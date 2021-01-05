#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# ACME v2客户端
# -------------------------------------------------------------------
import re
import fcntl
import datetime
import binascii
import hashlib
import base64
import json
import copy
import time
import os
import sys
os.chdir('/www/server/panel')
if not 'class/' in sys.path:
    sys.path.insert(0,'class/')
import http_requests as requests
requests.DEFAULT_TYPE = 'curl'
import public

try:
    import OpenSSL
except:
    public.ExecShell("pip install pyopenssl")
    import OpenSSL
try:
    import dns.resolver
except:
    public.ExecShell("pip install dnspython")
    import dns.resolver

class acme_v2:
    _url = None
    _apis = None
    _config = {}
    _dns_domains = []
    _bits = 2048
    _acme_timeout = 30
    _dns_class = None
    _user_agent = "BTPanel"
    _replay_nonce = None
    _verify = False
    _digest = "sha256"
    _max_check_num = 5
    _wait_time = 5
    _mod_index = {True: "Staging", False: "Production"}
    _debug = False
    _auto_wildcard = False
    _dnsapi_file = 'config/dns_api.json'
    _save_path = 'vhost/letsencrypt'
    _conf_file = 'config/letsencrypt.json'

    def __init__(self):
        if self._debug:
            self._url = 'https://acme-staging-v02.api.letsencrypt.org/directory'
        else:
            self._url = 'https://acme-v02.api.letsencrypt.org/directory'
        self._config = self.read_config()

    # 取接口目录
    def get_apis(self):
        if not self._apis:
            # 尝试从配置文件中获取
            api_index = self._mod_index[self._debug]
            if not 'apis' in self._config:
                self._config['apis'] = {}
            if api_index in self._config['apis']:
                if 'expires' in self._config['apis'][api_index] and 'directory' in self._config['apis'][api_index]:
                    if time.time() < self._config['apis'][api_index]['expires']:
                        self._apis = self._config['apis'][api_index]['directory']
                        return self._apis

            # 尝试从云端获取
            res = requests.get(self._url)
            if not res.status_code in [200, 201]:
                result = res.json()
                if "type" in result:
                    if result['type'] == 'urn:acme:error:serverInternal':
                        raise Exception('服务因维护而关闭或发生内部错误，查看 <a href="https://letsencrypt.status.io/" target="_blank" class="btlink">https://letsencrypt.status.io/</a> 了解更多详细信息。')
                raise Exception(res.content)
            s_body = res.json()
            self._apis = {}
            self._apis['newAccount'] = s_body['newAccount']
            self._apis['newNonce'] = s_body['newNonce']
            self._apis['newOrder'] = s_body['newOrder']
            self._apis['revokeCert'] = s_body['revokeCert']
            self._apis['keyChange'] = s_body['keyChange']

            # 保存到配置文件
            self._config['apis'][api_index] = {}
            self._config['apis'][api_index]['directory'] = self._apis
            self._config['apis'][api_index]['expires'] = time.time() + \
                86400  # 24小时后过期
            self.save_config()
        return self._apis

    # 获取帐户信息
    def get_account_info(self, args):
        try:
            if not 'account' in self._config:
                return {}
            k = self._mod_index[self._debug]
            if not k in self._config['account']:
                self.get_apis()
                self.get_kid()
            account = self._config['account'][k]
            account['email'] = self._config['email']
            self.set_crond()
            return account
        except Exception as ex:
            return public.returnMsg(False,str(ex))

    # 设置帐户信息
    def set_account_info(self, args):
        if not 'account' in self._config:
            return public.returnMsg(False, '指定帐户不存在')
        account = json.loads(args.account)
        if 'email' in account:
            self._config['email'] = account['email']
            del(account['email'])
        self._config['account'][self._mod_index[self._debug]] = account
        self.save_config()
        return public.returnMsg(True, '帐户设置成功!')

    # 获取订单列表
    def get_orders(self, args):
        if not 'orders' in self._config:
            return []
        s_orders = []
        for index in self._config['orders'].keys():
            tmp_order = self._config['orders'][index]
            tmp_order['index'] = index
            s_orders.append(tmp_order)
        return s_orders

    # 删除订单
    def remove_order(self, args):
        if not 'orders' in self._config:
            return public.returnMsg(False, '指定订单不存在!')
        if not args.index in self._config['orders']:
            return public.returnMsg(False, '指定订单不存在!')
        del(self._config['orders'][args.index])
        self.save_config()
        return public.returnMsg(True, '订单删除成功!')

    # 取指定订单数据
    def get_order_find(self, args):
        if not 'orders' in self._config:
            return public.returnMsg(False, '指定订单不存在!')
        if not args.index in self._config['orders']:
            return public.returnMsg(False, '指定订单不存在!')
        result = self._config['orders'][args.index]
        result['cert'] = self.get_cert_info(args.index)
        return result

    # 获取证书信息
    def get_cert_info(self, index):
        cert = {}
        path = self._config['orders'][index]['save_path']
        if not os.path.exists(path):
            self.download_cert(index)
        cert['private_key'] = public.readFile(path + "/privkey.pem")
        cert['fullchain'] = public.readFile(path + "/fullchain.pem")
        return cert

    # 更新证书压缩包
    def update_zip(self, args):
        path = self._config['orders'][args.index]['save_path']
        if not os.path.exists(path):  # 尝试重新下载证书
            self.download_cert(args.index)
        if not os.path.exists(path):
            return public.returnMsg(False, '证书读取失败，目录不存在!')
        import panelTask
        bt_task = panelTask.bt_task()
        zip_file = path+'/cert.zip'
        result = bt_task._zip(path, '.', path+'/cert.zip', '/dev/null', 'zip')
        if not os.path.exists(zip_file):
            return result
        return public.returnMsg(True, zip_file)

    # 吊销证书
    def revoke_order(self, index):
        if type(index) != str:
            index = index.index
        if not index in self._config['orders']:
            raise Exception("指定订单不存在!")
        cert_path = self._config['orders'][index]['save_path']
        if not os.path.exists(cert_path):
            raise Exception("指定订单没有找到可用的证书!")
        cert = self.dump_der(cert_path)
        if not cert:
            raise Exception("证书读取失败!")
        payload = {
            "certificate": self.calculate_safe_base64(cert),
            "reason": 4
        }
        res = self.acme_request(self._apis['revokeCert'], payload)
        if res.status_code in [200, 201]:
            if os.path.exists(cert_path):
                public.ExecShell("rm -rf {}".format(cert_path))
            del(self._config['orders'][index])
            self.save_config()
            return public.returnMsg(True, "证书吊销成功!")
        return res.json()

    # 取根域名和记录值
    def extract_zone(self, domain_name):
        top_domain_list = ['.ac.cn', '.ah.cn', '.bj.cn', '.com.cn', '.cq.cn', '.fj.cn', '.gd.cn','.gov.cn', '.gs.cn',
                           '.gx.cn', '.gz.cn', '.ha.cn', '.hb.cn', '.he.cn','.hi.cn', '.hk.cn', '.hl.cn', '.hn.cn',
                           '.jl.cn', '.js.cn', '.jx.cn','.ln.cn', '.mo.cn', '.net.cn', '.nm.cn', '.nx.cn', '.org.cn',
                           '.my.id','.com.ac','.com.ad','.com.ae','.com.af','.com.ag','.com.ai','.com.al','.com.am',
                           '.com.an','.com.ao','.com.aq','.com.ar','.com.as','.com.as','.com.at','.com.au','.com.aw',
                           '.com.az','.com.ba','.com.bb','.com.bd','.com.be','.com.bf','.com.bg','.com.bh','.com.bi',
                           '.com.bj','.com.bm','.com.bn','.com.bo','.com.br','.com.bs','.com.bt','.com.bv','.com.bw',
                           '.com.by','.com.bz','.com.ca','.com.ca','.com.cc','.com.cd','.com.cf','.com.cg','.com.ch',
                           '.com.ci','.com.ck','.com.cl','.com.cm','.com.cn','.com.co','.com.cq','.com.cr','.com.cu',
                           '.com.cv','.com.cx','.com.cy','.com.cz','.com.de','.com.dj','.com.dk','.com.dm','.com.do',
                           '.com.dz','.com.ec','.com.ee','.com.eg','.com.eh','.com.es','.com.et','.com.eu','.com.ev',
                           '.com.fi','.com.fj','.com.fk','.com.fm','.com.fo','.com.fr','.com.ga','.com.gb','.com.gd',
                           '.com.ge','.com.gf','.com.gh','.com.gi','.com.gl','.com.gm','.com.gn','.com.gp','.com.gr',
                           '.com.gt','.com.gu','.com.gw','.com.gy','.com.hm','.com.hn','.com.hr','.com.ht','.com.hu',
                           '.com.id','.com.id','.com.ie','.com.il','.com.il','.com.in','.com.io','.com.iq','.com.ir',
                           '.com.is','.com.it','.com.jm','.com.jo','.com.jp','.com.ke','.com.kg','.com.kh','.com.ki',
                           '.com.km','.com.kn','.com.kp','.com.kr','.com.kw','.com.ky','.com.kz','.com.la','.com.lb',
                           '.com.lc','.com.li','.com.lk','.com.lr','.com.ls','.com.lt','.com.lu','.com.lv','.com.ly',
                           '.com.ma','.com.mc','.com.md','.com.me','.com.mg','.com.mh','.com.ml','.com.mm','.com.mn',
                           '.com.mo','.com.mp','.com.mq','.com.mr','.com.ms','.com.mt','.com.mv','.com.mw','.com.mx',
                           '.com.my','.com.mz','.com.na','.com.nc','.com.ne','.com.nf','.com.ng','.com.ni','.com.nl',
                           '.com.no','.com.np','.com.nr','.com.nr','.com.nt','.com.nu','.com.nz','.com.om','.com.pa',
                           '.com.pe','.com.pf','.com.pg','.com.ph','.com.pk','.com.pl','.com.pm','.com.pn','.com.pr',
                           '.com.pt','.com.pw','.com.py','.com.qa','.com.re','.com.ro','.com.rs','.com.ru','.com.rw',
                           '.com.sa','.com.sb','.com.sc','.com.sd','.com.se','.com.sg','.com.sh','.com.si','.com.sj',
                           '.com.sk','.com.sl','.com.sm','.com.sn','.com.so','.com.sr','.com.st','.com.su','.com.sy',
                           '.com.sz','.com.tc','.com.td','.com.tf','.com.tg','.com.th','.com.tj','.com.tk','.com.tl',
                           '.com.tm','.com.tn','.com.to','.com.tp','.com.tr','.com.tt','.com.tv','.com.tw','.com.tz',
                           '.com.ua','.com.ug','.com.uk','.com.uk','.com.us','.com.uy','.com.uz','.com.va','.com.vc',
                           '.com.ve','.com.vg','.com.vn','.com.vu','.com.wf','.com.ws','.com.ye','.com.za','.com.zm',
                           '.com.zw']
        old_domain_name = domain_name
        top_domain = "."+".".join(domain_name.rsplit('.')[-2:])
        new_top_domain = "." + top_domain.replace(".", "")
        is_tow_top = False
        if top_domain in top_domain_list:
            is_tow_top = True
            domain_name = domain_name[:-len(top_domain)] + new_top_domain

        if domain_name.count(".") > 1:
            zone, middle, last = domain_name.rsplit(".", 2)
            if is_tow_top:
                last = top_domain[1:]
            root = ".".join([middle, last])
        else:
            zone = ""
            root = old_domain_name
        return root, zone

    # 自动构造通配符
    def auto_wildcard(self, domains):
        if not domains:
            return domains
        domain_list = []
        for domain in domains:
            rootDoamin = self.extract_zone(domain)[0]
            if not rootDoamin in domain_list:
                domain_list.append(rootDoamin)
            if not "*." + rootDoamin in domain_list:
                domain_list.append("*." + rootDoamin)
        return domain_list

    # 构造域名列表
    def format_domains(self, domains):
        if type(domains) != list:
            return []
        # 是否自动构造通配符
        if self._auto_wildcard:
            domains = self.auto_wildcard(domains)
        wildcard = []
        tmp_domains = []
        for domain in domains:
            domain = domain.strip()
            if domain in tmp_domains:
                continue
            # 将通配符域名转为验证正则表达式
            f_index = domain.find("*.")
            if f_index not in [-1, 0]:
                continue
            if f_index == 0:
                wildcard.append(domain.replace(
                    "*", r"^[\w-]+").replace(".", r"\."))
            # 添加到申请列表
            tmp_domains.append(domain)

        # 处理通配符包含
        apply_domains = tmp_domains[:]
        for domain in tmp_domains:
            for w in wildcard:
                if re.match(w, domain):
                    apply_domains.pop(domain)

        return apply_domains

    # 创建订单
    def create_order(self, domains, auth_type, auth_to, index=None):
        domains = self.format_domains(domains)
        if not domains:
            raise Exception("至少需要有一个域名")
        # 构造标识
        identifiers = []
        for domain_name in domains:
            identifiers.append({"type": 'dns', "value": domain_name})
        payload = {"identifiers": identifiers}

        # 请求创建订单
        res = self.acme_request(self._apis['newOrder'], payload)
        if not res.status_code in [201]:  # 如果创建失败
            e_body = res.json()
            if 'type' in e_body:
                # 如果随机数失效
                if e_body['type'].find('error:badNonce') != -1:
                    self.get_nonce(force=True)
                    res = self.acme_request(self._apis['newOrder'], payload)

                # 如果帐户失效
                if e_body['detail'].find('KeyID header contained an invalid account URL') != -1:
                    k = self._mod_index[self._debug]
                    del(self._config['account'][k])
                    self.get_kid()
                    self.get_nonce(force=True)
                    res = self.acme_request(self._apis['newOrder'], payload)
            if not res.status_code in [201]:
                a_auth = res.json()
                
                ret_title = self.get_error(str(a_auth))
                raise StopIteration(
                        "{0} >>>> {1}".format(
                            ret_title,
                            json.dumps(a_auth)
                        )
                    )

        # 返回验证地址和验证
        s_json = res.json()
        s_json['auth_type'] = auth_type
        s_json['domains'] = domains
        s_json['auth_to'] = auth_to
        index = self.save_order(s_json, index)
        return index

    # 获取验证信息
    def get_auths(self, index):
        if not index in self._config['orders']:
            raise Exception('指定订单不存在!')

        # 检查是否已经获取过授权信息
        if 'auths' in self._config['orders'][index]:
            # 检查授权信息是否过期
            if time.time() < self._config['orders'][index]['auths'][0]['expires']:
                return self._config['orders'][index]['auths']
        
        #清理旧验证
        self.claer_auth_file(index)
        
        auths = []
        for auth_url in self._config['orders'][index]['authorizations']:
            res = self.acme_request(auth_url, "")
            if res.status_code not in [200, 201]:
                raise Exception("获取授权失败: {}".format(res.json()))

            s_body = res.json()
            if 'status' in s_body:
                if s_body['status'] in ['invalid']:
                    raise Exception("无效订单，此订单当前为验证失败状态!")
                if s_body['status'] in ['valid']:  # 跳过无需验证的域名
                    continue

            s_body['expires'] = self.utc_to_time(s_body['expires'])
            identifier_auth = self.get_identifier_auth(index, auth_url, s_body)
            if not identifier_auth:
                raise Exception("验证信息构造失败!{}")

            acme_keyauthorization, auth_value = self.get_keyauthorization(
                identifier_auth['token'])
            identifier_auth['acme_keyauthorization'] = acme_keyauthorization
            identifier_auth['auth_value'] = auth_value
            identifier_auth['expires'] = s_body['expires']
            identifier_auth['auth_to'] = self._config['orders'][index]['auth_to']
            identifier_auth['type'] = self._config['orders'][index]['auth_type']
            # 设置验证信息
            self.set_auth_info(identifier_auth)
            auths.append(identifier_auth)
        self._config['orders'][index]['auths'] = auths
        self.save_config()
        return auths

    # 更新随机数
    def update_replay_nonce(self, res):
        replay_nonce = res.headers.get('Replay-Nonce')
        if replay_nonce:
            self._replay_nonce = replay_nonce

    # 设置验证信息
    def set_auth_info(self, identifier_auth):
        
        #从云端验证
        if not self.cloud_check_domain(identifier_auth['domain']):
            self.err = "云端验证失败!"
        
        # 是否手动验证DNS
        if identifier_auth['auth_to'] == 'dns':
            return None

        # 是否文件验证
        if identifier_auth['type'] in ['http', 'tls']:
            self.write_auth_file(
                identifier_auth['auth_to'], identifier_auth['token'], identifier_auth['acme_keyauthorization'])
        else:
            # dnsapi验证
            self.create_dns_record(
                identifier_auth['auth_to'], identifier_auth['domain'], identifier_auth['auth_value'])
                
    #从云端验证域名是否可访问
    def cloud_check_domain(self,domain):
        try:
            result = requests.post('https://www.bt.cn/api/panel/check_domain',{"domain":domain}).json()
            return result['status']
        except: return False
        

    #清理验证文件
    def claer_auth_file(self,index):
        if not self._config['orders'][index]['auth_type'] in ['http','tls']: 
            return True
        acme_path = '{}/.well-known/acme-challenge'.format(self._config['orders'][index]['auth_to'])
        write_log("|-验证目录：{}".format(acme_path))
        if os.path.exists(acme_path):
            public.ExecShell("rm -f {}/*".format(acme_path))
        
        acme_path = '/www/server/stop/.well-known/acme-challenge'
        if os.path.exists(acme_path):
            public.ExecShell("rm -f {}/*".format(acme_path))
        

    # 写验证文件
    def write_auth_file(self, auth_to, token, acme_keyauthorization):
        try:
            acme_path = '{}/.well-known/acme-challenge'.format(auth_to)
            if not os.path.exists(acme_path):
                os.makedirs(acme_path)
                public.set_own(acme_path, 'www')
            wellknown_path = '{}/{}'.format(acme_path, token)
            public.writeFile(wellknown_path, acme_keyauthorization)
            public.set_own(wellknown_path, 'www')
            
            acme_path = '/www/server/stop/.well-known/acme-challenge'
            if not os.path.exists(acme_path):
                os.makedirs(acme_path)
                public.set_own(acme_path, 'www')
            wellknown_path = '{}/{}'.format(acme_path,token)
            public.writeFile(wellknown_path,acme_keyauthorization)
            public.set_own(wellknown_path, 'www')
            return True
        except:
            err = public.get_error_info()
            print(err)
            raise Exception("写入验证文件失败: {}".format(err))

    # 解析域名
    def create_dns_record(self, auth_to, domain, dns_value):
        # 如果为手动解析
        if auth_to == 'dns' or auth_to.find('|') == -1:
            return None
        if not self._dns_class:
            import panelDnsapi
            dns_name, key, secret = self.get_dnsapi(auth_to)
            self._dns_class = getattr(panelDnsapi, dns_name)(key, secret)
        self._dns_class.create_dns_record(public.de_punycode(domain), dns_value)
        self._dns_domains.append({"domain": domain, "dns_value": dns_value})

    # 解析DNSAPI信息
    def get_dnsapi(self, auth_to):
        tmp = auth_to.split('|')
        dns_name = tmp[0]
        key = "None"
        secret = "None"
        if len(tmp) < 3:
            try:
                dnsapi_config = json.loads(public.readFile(self._dnsapi_file))
                for dc in dnsapi_config:
                    if dc['name'] != dns_name:
                        continue
                    if not dc['data']:
                        continue
                    key = dc['data'][0]['value']
                    secret = dc['data'][1]['value']
            except:
                raise Exception("没有找到有效的DNSAPI密钥信息")
        else:
            key = tmp[1]
            secret = tmp[2]
        return dns_name, key, secret

    # 删除域名解析
    def remove_dns_record(self):
        if not self._dns_class:
            return None
        for dns_info in self._dns_domains:
            try:
                self._dns_class.delete_dns_record(
                    public.de_punycode(dns_info['domain']), dns_info['dns_value'])
            except:
                pass
    # 验证域名
    def auth_domain(self, index):
        if not index in self._config['orders']:
            raise Exception('指定订单不存在!')

        # 开始验证
        for auth in self._config['orders'][index]['auths']:
            res = self.check_auth_status(auth['url'])  # 检查是否需要验证
            if res.json()['status'] == 'pending':
                if auth['type'] == 'dns':  # 尝试提前验证dns解析
                    self.check_dns(
                        "_acme-challenge.{}".format(
                            auth['domain'].replace('*.', '')),
                        auth['auth_value'],
                        "TXT"
                    )
                self.respond_to_challenge(auth)

        # 检查验证结果
        for i in range(len(self._config['orders'][index]['auths'])):
            self.check_auth_status(self._config['orders'][index]['auths'][i]['url'], [
                                   'valid', 'invalid'])
            self._config['orders'][index]['status'] = 'valid'

    # 检查验证状态
    def check_auth_status(self, url, desired_status=None):
        desired_status = desired_status or ["pending", "valid", "invalid"]
        number_of_checks = 0
        while True:
            if desired_status == ['valid', 'invalid']:
                write_log("|-第{}次查询验证结果..".format(number_of_checks + 1))
                time.sleep(self._wait_time)
            check_authorization_status_response = self.acme_request(url, "")
            a_auth = check_authorization_status_response.json()
            authorization_status = a_auth["status"]
            number_of_checks += 1
            if authorization_status in desired_status:
                if authorization_status == "invalid":
                    write_log("|-验证失败!")
                    try:
                        if 'error' in a_auth['challenges'][0]:
                            ret_title = a_auth['challenges'][0]['error']['detail']
                        elif 'error' in a_auth['challenges'][1]:
                            ret_title = a_auth['challenges'][1]['error']['detail']
                        elif 'error' in a_auth['challenges'][2]:
                            ret_title = a_auth['challenges'][2]['error']['detail']
                        else:
                            ret_title = str(a_auth)
                        ret_title = self.get_error(ret_title)
                    except:
                        ret_title = str(a_auth)
                    raise StopIteration(
                        "{0} >>>> {1}".format(
                            ret_title,
                            json.dumps(a_auth)
                        )
                    )
                break

            if number_of_checks == self._max_check_num:
                raise StopIteration(
                    "错误：已尝试验证{0}次. 最大验证次数为{1}. 验证时间间隔为{2}秒.".format(
                        number_of_checks,
                        self._max_check_num,
                        self._wait_time
                    )
                )
        if desired_status == ['valid', 'invalid']:
            write_log("|-验证成功!")
        return check_authorization_status_response

    # 格式化错误输出
    def get_error(self, error):
        if error.find("Max checks allowed") >= 0:
            return "CA无法验证您的域名，请检查域名解析是否正确，或等待5-10分钟后重试."
        elif error.find("Max retries exceeded with") >= 0 or error.find('status_code=0 ') != -1:
            return "CA服务器连接超时，请稍候重试."
        elif error.find("The domain name belongs") >= 0:
            return "域名不属于此DNS服务商，请确保域名填写正确."
        elif error.find('login token ID is invalid') >= 0:
            return 'DNS服务器连接失败，请检查密钥是否正确.'
        elif error.find('Error getting validation data') != -1:
            return '数据验证失败，CA无法从验证连接中获到正确的验证码.'
        elif "too many certificates already issued for exact set of domains" in error:
            return '签发失败,该域名%s超出了每周的重复签发次数限制!' % re.findall("exact set of domains: (.+):", error)
        elif "Error creating new account :: too many registrations for this IP" in error:
            return '签发失败,当前服务器IP已达到每3小时最多创建10个帐户的限制.'
        elif "DNS problem: NXDOMAIN looking up A for" in error:
            return '验证失败,没有解析域名,或解析未生效!'
        elif "Invalid response from" in error:
            return '验证失败,域名解析错误或验证URL无法被访问!'
        elif error.find('TLS Web Server Authentication') != -1:
            return "连接CA服务器失败，请稍候重试."
        elif error.find('Name does not end in a public suffix') != -1:
            return "不支持的域名%s，请检查域名是否正确!" % re.findall("Cannot issue for \"(.+)\":", error)
        elif error.find('No valid IP addresses found for') != -1:
            return "域名%s没有找到解析记录，请检查域名是否解析生效!" % re.findall("No valid IP addresses found for (.+)", error)
        elif error.find('No TXT record found at') != -1:
            return "没有在域名%s中找到有效的TXT解析记录,请检查是否正确解析TXT记录,如果是DNSAPI方式申请的,请10分钟后重试!" % re.findall("No TXT record found at (.+)", error)
        elif error.find('Incorrect TXT record') != -1:
            return "在%s上发现错误的TXT记录:%s,请检查TXT解析是否正确,如果是DNSAPI方式申请的,请10分钟后重试!" % (re.findall("found at (.+)", error), re.findall("Incorrect TXT record \"(.+)\"", error))
        elif error.find('Domain not under you or your user') != -1:
            return "这个dnspod账户下面不存在这个域名，添加解析失败!"
        elif error.find('SERVFAIL looking up TXT for') != -1:
            return "没有在域名%s中找到有效的TXT解析记录,请检查是否正确解析TXT记录,如果是DNSAPI方式申请的,请10分钟后重试!" % re.findall("looking up TXT for (.+)", error)
        elif error.find('Timeout during connect') != -1:
            return "连接超时,CA服务器无法访问您的网站!"
        elif error.find("DNS problem: SERVFAIL looking up CAA for") != -1:
            return "域名%s当前被要求验证CAA记录，请手动解析CAA记录，或1小时后重新尝试申请!" % re.findall("looking up CAA for (.+)", error)
        elif error.find("Read timed out.") != -1:
            return "验证超时,请检查域名是否正确解析，若已正确解析，可能服务器与Let'sEncrypt连接异常，请稍候再重试!"
        elif error.find('Cannot issue for') != -1:
            return "无法为{}颁发证书，不能直接用域名后缀申请通配符证书!".format(re.findall(r'for\s+"(.+)"',error))
        elif error.find('too many failed authorizations recently'):
            return '该帐户1小时内失败的订单次数超过5次，请等待1小时再重试!'
        elif error.find("Error creating new order") != -1:
            return "订单创建失败，请稍候重试!"
        elif error.find("Too Many Requests") != -1:
            return "1小时内超过5次验证失败，暂时禁止申请，请稍候重试!"
        elif error.find('HTTP Error 400: Bad Request') != -1:
            return "CA服务器拒绝访问，请稍候重试!"
        elif error.find('Temporary failure in name resolution') != -1:
            return '服务器DNS故障，无法解析域名，请使用Linux工具箱检查dns配置'
        elif error.find('Too Many Requests') != -1:
            return '该域名请求申请次数过多，请3小时后重试'
        else:
            return error

    # 发送验证请求
    def respond_to_challenge(self, auth):
        payload = {"keyAuthorization": "{0}".format(
            auth['acme_keyauthorization'])}
        respond_to_challenge_response = self.acme_request(
            auth['dns_challenge_url'], payload)
        return respond_to_challenge_response

    # 发送CSR
    def send_csr(self, index):
        csr = self.create_csr(index)
        payload = {"csr": self.calculate_safe_base64(csr)}
        send_csr_response = self.acme_request(
            url=self._config['orders'][index]['finalize'], payload=payload)
        if send_csr_response.status_code not in [200, 201]:
            raise ValueError(
                "错误： 发送CSR: 响应状态{status_code} 响应值:{response}".format(
                    status_code=send_csr_response.status_code,
                    response=send_csr_response.json(),
                )
            )
        send_csr_response_json = send_csr_response.json()
        certificate_url = send_csr_response_json["certificate"]
        self._config['orders'][index]['certificate_url'] = certificate_url
        self.save_config()
        return certificate_url

    # 获取证书到期时间
    def get_cert_timeout(self, cret_data):
        try:
            x509 = OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM, cret_data)
            cert_timeout = bytes.decode(x509.get_notAfter())[:-1]
            return int(time.mktime(time.strptime(cert_timeout, '%Y%m%d%H%M%S')))
        except:
            return int(time.time() + (86400 * 90))

    # 下载证书
    def download_cert(self, index):
        res = self.acme_request(
            self._config['orders'][index]['certificate_url'], "")
        if res.status_code not in [200, 201]:
            raise Exception("下载证书失败: {}".format(res.json()))

        pem_certificate = res.content
        if type(pem_certificate) == bytes:
            pem_certificate = pem_certificate.decode('utf-8')
        cert = self.split_ca_data(pem_certificate)
        cert['cert_timeout'] = self.get_cert_timeout(cert['cert'])
        cert['private_key'] = self._config['orders'][index]['private_key']
        cert['domains'] = self._config['orders'][index]['domains']
        del(self._config['orders'][index]['private_key'])
        del(self._config['orders'][index]['auths'])
        del(self._config['orders'][index]['expires'])
        del(self._config['orders'][index]['authorizations'])
        del(self._config['orders'][index]['finalize'])
        del(self._config['orders'][index]['identifiers'])
        if 'cert' in self._config['orders'][index]:
            del(self._config['orders'][index]['cert'])
        self._config['orders'][index]['status'] = 'valid'
        self._config['orders'][index]['cert_timeout'] = cert['cert_timeout']
        domain_name = self._config['orders'][index]['domains'][0]
        self._config['orders'][index]['save_path'] = '{}/{}'.format(
            self._save_path, domain_name)
        cert['save_path'] = self._config['orders'][index]['save_path']
        self.save_config()
        self.save_cert(cert, index)
        return cert

    # 保存证书到文件
    def save_cert(self, cert, index):
        try:
            domain_name = self._config['orders'][index]['domains'][0]
            path = self._config['orders'][index]['save_path']
            if not os.path.exists(path):
                os.makedirs(path, 384)

            # 存储证书
            key_file = path + "/privkey.pem"
            pem_file = path + "/fullchain.pem"
            public.writeFile(key_file, cert['private_key'])
            public.writeFile(pem_file, cert['cert'] + cert['root'])
            public.writeFile(path + "/cert.csr", cert['cert'])
            public.writeFile(path + "/root_cert.csr", cert['root'])

            # 转为IIS证书
            pfx_buffer = self.dump_pkcs12(
                cert['private_key'], cert['cert'] + cert['root'], cert['root'], domain_name)
            public.writeFile(path + "/fullchain.pfx", pfx_buffer, 'wb+')

            ps = '''文件说明：
privkey.pem     证书私钥
fullchain.pem   包含证书链的PEM格式证书(nginx/apache)
root_cert.csr   根证书
cert.csr        域名证书
fullchain.pfx   用于IIS的证书格式

如何在宝塔面板使用：
privkey.pem         粘贴到密钥输入框
fullchain.pem       粘贴到证书输入框
'''
            public.writeFile(path+'/说明.txt', ps)
            self.sub_all_cert(key_file, pem_file)
        except:
            write_log(public.get_error_info())

    # 替换服务器上的同域名同品牌证书
    def sub_all_cert(self, key_file, pem_file):
        cert_init = self.get_cert_init(pem_file)  # 获取新证书的基本信息
        paths = ['vhost/cert', 'vhost/ssl']
        for path in paths:
            if not os.path.exists(path):
                continue
            for p_name in os.listdir(path):
                to_path = path + '/' + p_name
                to_pem_file = to_path + '/fullchain.pem'
                to_key_file = to_path + '/privkey.pem'
                to_info = to_path + '/info.json'
                # 判断目标证书是否存在
                if not os.path.exists(to_pem_file):
                    continue
                # 获取目标证书的基本信息
                to_cert_init = self.get_cert_init(to_pem_file)
                # 判断证书品牌是否一致
                if to_cert_init['issuer'] != cert_init['issuer'] and to_cert_init['issuer'].find("Let's Encrypt") == -1:
                    continue
                # 判断目标证书的到期时间是否较早
                if to_cert_init['notAfter'] > cert_init['notAfter']:
                    continue
                # 判断认识名称是否一致
                if len(to_cert_init['dns']) != len(cert_init['dns']):
                    continue
                is_copy = True
                for domain in to_cert_init['dns']:
                    if not domain in cert_init['dns']:
                        is_copy = False
                if not is_copy:
                    continue

                # 替换新的证书文件和基本信息
                public.writeFile(
                    to_pem_file, public.readFile(pem_file, 'rb'), 'wb')
                public.writeFile(
                    to_key_file, public.readFile(key_file, 'rb'), 'wb')
                public.writeFile(to_info, json.dumps(cert_init))
                write_log(
                    "|-检测到{}下的证书与本次申请的证书重叠，且到期时间较早，已替换为新证书!".format(to_path))
        # 重载web服务
        public.serviceReload()

    # 检查指定证书是否在订单列表
    def check_order_exists(self, pem_file):
        try:
            cert_init = self.get_cert_init(pem_file)
            if not cert_init: return None
            for index in self._config['orders'].keys():
                if not 'save_path' in self._config['orders'][index]:
                    continue
                for domain in self._config['orders'][index]['domains']:
                    if domain in cert_init['dns']:
                        return index
            if cert_init['issuer'].find("Let's Encrypt") != -1:
                return pem_file
            return None
        except: return None

    # 取证书基本信息API
    def get_cert_init_api(self, args):
        if not os.path.exists(args.pem_file):
            args.pem_file = 'vhost/cert/{}/fullchain.pem'.format(args.siteName)
            if not os.path.exists(args.pem_file):
                return public.returnMsg(False, '指定证书文件不存在!')
        cert_init = self.get_cert_init(args.pem_file)
        if not cert_init:
            return public.returnMsg(False, '证书信息获取失败!')
        cert_init['dnsapi'] = json.loads(public.readFile(self._dnsapi_file))
        return cert_init

    # 获取指定证书基本信息
    def get_cert_init(self, pem_file):
        if not os.path.exists(pem_file):
            return None
        try:
            result = {}
            x509 = OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM, public.readFile(pem_file))
            # 取产品名称
            issuer = x509.get_issuer()
            result['issuer'] = ''
            if hasattr(issuer, 'CN'):
                result['issuer'] = issuer.CN
            if not result['issuer']:
                is_key = [b'0', '0']
                issue_comp = issuer.get_components()
                if len(issue_comp) == 1:
                    is_key = [b'CN', 'CN']
                for iss in issue_comp:
                    if iss[0] in is_key:
                        result['issuer'] = iss[1].decode()
                        break
            # 取到期时间
            result['notAfter'] = self.strf_date(
                bytes.decode(x509.get_notAfter())[:-1])
            # 取申请时间
            result['notBefore'] = self.strf_date(
                bytes.decode(x509.get_notBefore())[:-1])
            # 取可选名称
            result['dns'] = []
            for i in range(x509.get_extension_count()):
                s_name = x509.get_extension(i)
                if s_name.get_short_name() in [b'subjectAltName', 'subjectAltName']:
                    s_dns = str(s_name).split(',')
                    for d in s_dns:
                        result['dns'].append(d.split(':')[1])
            subject = x509.get_subject().get_components()
            # 取主要认证名称
            if len(subject) == 1:
                result['subject'] = subject[0][1].decode()
            else:
                result['subject'] = result['dns'][0]
            return result
        except: return None

    # 转换时间
    def strf_date(self, sdate):
        return time.strftime('%Y-%m-%d', time.strptime(sdate, '%Y%m%d%H%M%S'))

    # 证书转为DER
    def dump_der(self, cert_path):
        cert = OpenSSL.crypto.load_certificate(
            OpenSSL.crypto.FILETYPE_PEM, public.readFile(cert_path+'/cert.csr'))
        return OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_ASN1, cert)

    # 证书转为pkcs12
    def dump_pkcs12(self, key_pem=None, cert_pem=None, ca_pem=None, friendly_name=None):
        p12 = OpenSSL.crypto.PKCS12()
        if cert_pem:
            p12.set_certificate(OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM, cert_pem.encode()))
        if key_pem:
            p12.set_privatekey(OpenSSL.crypto.load_privatekey(
                OpenSSL.crypto.FILETYPE_PEM, key_pem.encode()))
        if ca_pem:
            p12.set_ca_certificates((OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM, ca_pem.encode()),))
        if friendly_name:
            p12.set_friendlyname(friendly_name.encode())
        return p12.export()

    # 拆分根证书
    def split_ca_data(self, cert):
        datas = cert.split('-----END CERTIFICATE-----')
        return {"cert": datas[0] + "-----END CERTIFICATE-----\n", "root": datas[1] + '-----END CERTIFICATE-----\n'}

    # 构造可选名称
    def get_alt_names(self, index):
        domain_name = self._config['orders'][index]['domains'][0]
        domain_alt_names = []
        if len(self._config['orders'][index]['domains']) > 1:
            domain_alt_names = self._config['orders'][index]['domains'][1:]
        return domain_name, domain_alt_names

    # 检查DNS记录
    def check_dns(self, domain, value, s_type='TXT'):
        write_log("|-尝试本地验证DNS记录,域名: {} , 类型: {} 记录值: {}".format(domain, s_type, value))
        time.sleep(10)
        n = 0
        while n < 20:
            n += 1
            try:
                import dns.resolver
                ns = dns.resolver.query(domain, s_type)
                for j in ns.response.answer:
                    for i in j.items:
                        txt_value = i.to_text().replace('"', '').strip()
                        write_log("|-第 {} 次验证值: {}".format(n, txt_value))
                        if txt_value == value:
                            write_log("|-本地验证成功!")
                            return True
            except:
                try:
                    import dns.resolver
                except:
                    return False
            time.sleep(3)
        write_log("|-本地验证失败!")
        return True

    # 创建CSR
    def create_csr(self, index):
        if 'csr' in self._config['orders'][index]:
            return self._config['orders']['csr']
        domain_name, domain_alt_names = self.get_alt_names(index)
        X509Req = OpenSSL.crypto.X509Req()
        X509Req.get_subject().CN = domain_name
        if domain_alt_names:
            SAN = "DNS:{0}, ".format(domain_name).encode("utf8") + ", ".join(
                "DNS:" + i for i in domain_alt_names
            ).encode("utf8")
        else:
            SAN = "DNS:{0}".format(domain_name).encode("utf8")

        X509Req.add_extensions(
            [
                OpenSSL.crypto.X509Extension(
                    "subjectAltName".encode("utf8"), critical=False, value=SAN
                )
            ]
        )
        pk = OpenSSL.crypto.load_privatekey(
            OpenSSL.crypto.FILETYPE_PEM, self.create_certificate_key(
                index).encode()
        )
        X509Req.set_pubkey(pk)
        X509Req.set_version(2)
        X509Req.sign(pk, self._digest)
        return OpenSSL.crypto.dump_certificate_request(OpenSSL.crypto.FILETYPE_ASN1, X509Req)

    # 构造域名验证头和验证值
    def get_keyauthorization(self, token):
        acme_header_jwk_json = json.dumps(
            self.get_acme_header("GET_THUMBPRINT")["jwk"], sort_keys=True, separators=(",", ":")
        )
        acme_thumbprint = self.calculate_safe_base64(
            hashlib.sha256(acme_header_jwk_json.encode("utf8")).digest()
        )
        acme_keyauthorization = "{0}.{1}".format(token, acme_thumbprint)
        base64_of_acme_keyauthorization = self.calculate_safe_base64(
            hashlib.sha256(acme_keyauthorization.encode("utf8")).digest()
        )

        return acme_keyauthorization, base64_of_acme_keyauthorization

    # 构造验证信息
    def get_identifier_auth(self, index, url, auth_info):
        s_type = self.get_auth_type(index)
        write_log("|-验证类型：{}".format(s_type))
        domain = auth_info['identifier']['value']
        wildcard = False
        # 处理通配符
        if 'wildcard' in auth_info:
            wildcard = auth_info['wildcard']
        if wildcard:
            domain = "*." + domain

        for auth in auth_info['challenges']:
            if auth['type'] != s_type:
                continue
            identifier_auth = {
                "domain": domain,
                "url": url,
                "wildcard": wildcard,
                "token": auth['token'],
                "dns_challenge_url": auth['url'],
            }
            return identifier_auth
        return None

    # 获取域名验证方式
    def get_auth_type(self, index):
        if not index in self._config['orders']:
            raise Exception('指定订单不存在!')
        s_type = 'http-01'
        if 'auth_type' in self._config['orders'][index]:
            if self._config['orders'][index]['auth_type'] == 'dns':
                s_type = 'dns-01'
            elif self._config['orders'][index]['auth_type'] == 'tls':
                s_type = 'tls-alpn-01'
            else:
                s_type = 'http-01'
        return s_type

    # 保存订单
    def save_order(self, order_object, index):
        if not 'orders' in self._config:
            self._config['orders'] = {}
        renew = False
        if not index:
            index = public.md5(json.dumps(order_object['identifiers']))
        else:
            renew = True
            order_object['certificate_url'] = self._config['orders'][index]['certificate_url']
            order_object['save_path'] = self._config['orders'][index]['save_path']

        order_object['expires'] = self.utc_to_time(order_object['expires'])
        self._config['orders'][index] = order_object
        self._config['orders'][index]['index'] = index
        if not renew:
            self._config['orders'][index]['create_time'] = int(time.time())
            self._config['orders'][index]['renew_time'] = 0
        self.save_config()
        return index

    # UTC时间转时间戳
    def utc_to_time(self, utc_string):
        try:
            utc_string = utc_string.split('.')[0]
            utc_date = datetime.datetime.strptime(
                utc_string, "%Y-%m-%dT%H:%M:%S")
            # 按北京时间返回
            return int(time.mktime(utc_date.timetuple())) + (3600 * 8)
        except:
            return int(time.time() + 86400 * 7)

    # 获取kid
    def get_kid(self, force=False):
        #如果配置文件中不存在kid或force = True时则重新注册新的acme帐户
        if not 'account' in self._config:
            self._config['account'] = {}
        k = self._mod_index[self._debug]
        if not k in self._config['account']:
            self._config['account'][k] = {}

        if not 'kid' in self._config['account'][k]:
            self._config['account'][k]['kid'] = self.register()
            self.save_config()
            time.sleep(3)
            self._config = self.read_config()
        return self._config['account'][k]['kid']

    # 注册acme帐户
    def register(self, existing=False):
        if not 'email' in self._config:
            self._config['email'] = 'demo@bt.cn'
        if existing:
            payload = {"onlyReturnExisting": True}
        elif self._config['email']:
            payload = {
                "termsOfServiceAgreed": True,
                "contact": ["mailto:{0}".format(self._config['email'])],
            }
        else:
            payload = {"termsOfServiceAgreed": True}

        res = self.acme_request(url=self._apis['newAccount'], payload=payload)

        if res.status_code not in [201, 200, 409]:
            raise Exception("注册ACME帐户失败: {}".format(res.json()))
        kid = res.headers["Location"]
        return kid

    # 请求到ACME接口
    def acme_request(self, url, payload):
        headers = {"User-Agent": self._user_agent}
        payload = self.stringfy_items(payload)

        if payload == "":
            payload64 = payload
        else:
            payload64 = self.calculate_safe_base64(json.dumps(payload))
        protected = self.get_acme_header(url)
        protected64 = self.calculate_safe_base64(json.dumps(protected))
        signature = self.sign_message(
            message="{0}.{1}".format(protected64, payload64))  # bytes
        signature64 = self.calculate_safe_base64(signature)  # str
        data = json.dumps(
            {"protected": protected64, "payload": payload64,
                "signature": signature64}
        )
        headers.update({"Content-Type": "application/jose+json"})
        response = requests.post(
            url, data=data.encode("utf8"), timeout=self._acme_timeout, headers=headers, verify=self._verify
        )
        # 更新随机数
        self.update_replay_nonce(response)
        return response

    # 计算signature
    def sign_message(self, message):
        pk = OpenSSL.crypto.load_privatekey(
            OpenSSL.crypto.FILETYPE_PEM, self.get_account_key().encode())
        return OpenSSL.crypto.sign(pk, message.encode("utf8"), self._digest)

    # 系列化payload
    def stringfy_items(self, payload):
        if isinstance(payload, str):
            return payload

        for k, v in payload.items():
            if isinstance(k, bytes):
                k = k.decode("utf-8")
            if isinstance(v, bytes):
                v = v.decode("utf-8")
            payload[k] = v
        return payload

    # 获取随机数
    def get_nonce(self, force=False):
        # 如果没有保存上一次的随机数或force=True时则重新获取新的随机数
        if not self._replay_nonce or force:
            headers = {"User-Agent": self._user_agent}
            response = requests.get(
                self._apis['newNonce'],
                timeout=self._acme_timeout,
                headers=headers,
                verify=self._verify
            )
            self._replay_nonce = response.headers["Replay-Nonce"]
        return self._replay_nonce

    # 获请ACME请求头
    def get_acme_header(self, url):
        header = {"alg": "RS256", "nonce": self.get_nonce(), "url": url}
        if url in [self._apis['newAccount'], 'GET_THUMBPRINT']:
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import serialization
            private_key = serialization.load_pem_private_key(
                self.get_account_key().encode(),
                password=None,
                backend=default_backend(),
            )
            public_key_public_numbers = private_key.public_key().public_numbers()

            exponent = "{0:x}".format(public_key_public_numbers.e)
            exponent = "0{0}".format(exponent) if len(
                exponent) % 2 else exponent
            modulus = "{0:x}".format(public_key_public_numbers.n)
            jwk = {
                "kty": "RSA",
                "e": self.calculate_safe_base64(binascii.unhexlify(exponent)),
                "n": self.calculate_safe_base64(binascii.unhexlify(modulus)),
            }
            header["jwk"] = jwk
        else:
            header["kid"] = self.get_kid()
        return header

    # 转为无填充的Base64
    def calculate_safe_base64(self, un_encoded_data):
        if sys.version_info[0] == 3:
            if isinstance(un_encoded_data, str):
                un_encoded_data = un_encoded_data.encode("utf8")
        r = base64.urlsafe_b64encode(un_encoded_data).rstrip(b"=")
        return r.decode("utf8")

    # 获用户取密钥对
    def get_account_key(self):
        if not 'account' in self._config:
            self._config['account'] = {}
        k = self._mod_index[self._debug]
        if not k in self._config['account']:
            self._config['account'][k] = {}

        if not 'key' in self._config['account'][k]:
            self._config['account'][k]['key'] = self.create_key()
            if type(self._config['account'][k]['key']) == bytes: 
                self._config['account'][k]['key'] = self._config['account'][k]['key'].decode()
            self.save_config()
        return self._config['account'][k]['key']

    # 获取证书密钥对
    def create_certificate_key(self, index):
        # 判断是否已经创建private_key
        if 'private_key' in self._config['orders'][index]:
            return self._config['orders'][index]['private_key']
        # 创建新的私钥
        private_key = self.create_key()
        if type(private_key) == bytes:
            private_key = private_key.decode()
        # 保存私钥到订单配置文件
        self._config['orders'][index]['private_key'] = private_key
        self.save_config()
        return private_key

    # 创建Key
    def create_key(self, key_type=OpenSSL.crypto.TYPE_RSA):
        key = OpenSSL.crypto.PKey()
        key.generate_key(key_type, self._bits)
        private_key = OpenSSL.crypto.dump_privatekey(
            OpenSSL.crypto.FILETYPE_PEM, key)
        return private_key

    # 写配置文件
    def save_config(self):
        fp = open(self._conf_file, 'w+')
        fcntl.flock(fp, fcntl.LOCK_EX)  # 加锁
        fp.write(json.dumps(self._config))
        fcntl.flock(fp, fcntl.LOCK_UN)  # 解锁
        fp.close()
        return True

    # 读配置文件
    def read_config(self):
        if not os.path.exists(self._conf_file):
            self._config['orders'] = {}
            self._config['account'] = {}
            self._config['apis'] = {}
            self._config['email'] = public.M('config').where('id=?',(1,)).getField('email')
            if self._config['email'] in ['287962566@qq.com']:
                self._config['email'] = None
            self.save_config()
            return self._config
        tmp_config = public.readFile(self._conf_file)
        if not tmp_config:
            return self._config
        try:
            self._config = json.loads(tmp_config)
        except:
            self.save_config()
            return self._config
        return self._config

    # 申请证书
    def apply_cert(self, domains, auth_type='dns', auth_to='Dns_com|None|None', **args):
        write_log("", "wb+")
        try:
            self.get_apis()
            index = None
            if 'index' in args:
                index = args['index']
            if not index:  # 判断是否只想验证域名
                write_log("|-正在创建订单..")
                index = self.create_order(domains, auth_type, auth_to)
                write_log("|-正在获取验证信息..")
                self.get_auths(index)
                if auth_to == 'dns' and len(self._config['orders'][index]['auths']) > 0:
                    return self._config['orders'][index]
            write_log("|-正在验证域名..")
            self.auth_domain(index)
            self.remove_dns_record()
            write_log("|-正在发送CSR..")
            self.send_csr(index)
            write_log("|-正在下载证书..")
            cert = self.download_cert(index)
            cert['status'] = True
            cert['msg'] = '申请成功!'
            write_log("|-申请成功，正在部署到站点..")
            return cert
        except Exception as ex:
            self.remove_dns_record()
            ex = str(ex)
            if ex.find(">>>>") != -1:
                msg = ex.split(">>>>")
                msg[1] = json.loads(msg[1])
            else:
                msg = ex
                write_log(public.get_error_info())
            return public.returnMsg(False, msg)

    # 申请证书 - api
    def apply_cert_api(self, args):
        # 是否为指定站点
        if re.match(r"^\d+$", args.auth_to):
            import panelSite
            path = public.M('sites').where('id=?',(args.id,)).getField('path')
            args.auth_to = path + '/' + panelSite.panelSite().GetRunPath(args)
            args.auth_to = args.auth_to.replace("//","/")
            if args.auth_to[-1] == '/':
                args.auth_to = args.auth_to[:-1]

            if not os.path.exists(args.auth_to):
                return public.returnMsg(False, '无效的站点目录，请检查指定站点是否存在!')
            
        check_result = self.check_auth_env(args)
        if check_result: return check_result
        
        if args.auto_wildcard == '1':
            self._auto_wildcard = True
        return self.apply_cert(json.loads(args.domains), args.auth_type, args.auth_to)

    #检查认证环境
    def check_auth_env(self,args):
        for domain in json.loads(args.domains):
            if public.checkIp(domain): continue
            if domain.find('*.') >=0 and args.auth_type in ['http','tls']:
                raise public.returnMsg(False, '泛域名不能使用【文件验证】的方式申请证书!')
        import panelSite
        s = panelSite.panelSite()
        if args.auth_type in ['http','tls']:
            try:
                if not 'siteName' in args:
                    args.siteName = public.M('sites').where('id=?',(args.id,)).getField('name')
                args.sitename = args.siteName
                data = s.GetRedirectList(args)
                # 检查重定向是否开启
                if type(data) == list: 
                    for x in data:
                        if x['type']: return public.returnMsg(False, 'SITE_SSL_ERR_301')
                data = s.GetProxyList(args)
                # 检查反向代理是否开启
                if type(data) == list:                    
                    for x in data:
                        if x['type']: return public.returnMsg(False,'已开启反向代理的站点无法申请SSL!')
                # 检查旧重定向是否开启
                data = s.Get301Status(args)
                if data['status']:
                    return public.returnMsg(False,'网站已经开启重定向，请关闭后再申请!')
                #判断是否强制HTTPS
                if s.IsToHttps(args.siteName):
                    return public.returnMsg(False, '配置强制HTTPS后无法使用【文件验证】的方式申请证书!')
            except:
                return False
        else:          
            if args.auth_to.find('Dns_com') != -1:
                if not os.path.exists('plugin/dns/dns_main.py'):
                    return public.returnMsg(False, '请先到软件商店安装【云解析】，并完成域名NS绑定.')
        
        

            
        return False

    # DNS手动验证
    def apply_dns_auth(self, args):
        return self.apply_cert([], auth_type='dns', auth_to='dns', index=args.index)


    #创建计划任务
    def set_crond(self):
        try:
            echo = public.md5(public.md5('renew_lets_ssl_bt'))
            cron_id = public.M('crontab').where('echo=?',(echo,)).getField('id')

            import crontab
            args_obj = public.dict_obj()
            if not cron_id:
                cronPath = public.GetConfigValue('setup_path') + '/cron/' + echo
                shell = '{} /www/server/panel/class/acme_v2.py --renew=1'.format(sys.executable)
                public.writeFile(cronPath,shell)
                args_obj.id = public.M('crontab').add('name,type,where1,where_hour,where_minute,echo,addtime,status,save,backupTo,sType,sName,sBody,urladdress',("续签Let's Encrypt证书",'day','','0','10',echo,time.strftime('%Y-%m-%d %X',time.localtime()),0,'','localhost','toShell','',shell,''))
                crontab.crontab().set_cron_status(args_obj)
            else:
                cron_path = public.get_cron_path()
                if os.path.exists(cron_path):
                    cron_s = public.readFile(cron_path)
                    if cron_s.find(echo) == -1:
                        public.M('crontab').where('echo=?',(echo,)).setField('status',0)
                        args_obj.id = cron_id
                        crontab.crontab().set_cron_status(args_obj)
        except:pass

    # 续签证书
    def renew_cert(self, index):
        write_log("", "wb+")
        try:
            order_index = []
            if index:
                if type(index) != str:
                    index = index.index
                if not index in self._config['orders']:
                    raise Exception("指定订单号不存在，无法续签!")
                order_index.append(index)
            else:
                s_time = time.time() + (30 * 86400)
                for i in self._config['orders'].keys():
                    if not 'save_path' in self._config['orders'][i]:
                        continue
                    if 'cert' in self._config['orders'][i]:
                        self._config['orders'][i]['cert_timeout'] = self._config['orders'][i]['cert']['cert_timeout']
                    if not 'cert_timeout' in self._config['orders'][i]:
                        self._config['orders'][i]['cert_timeout'] = int(time.time())
                    if self._config['orders'][i]['cert_timeout'] > s_time or self._config['orders'][i]['auth_to'] == 'dns':
                        continue

                    #已删除的网站直接跳过续签
                    if self._config['orders'][i]['auth_to'].find('|') == -1 and self._config['orders'][i]['auth_to'].find('/') != -1:
                        if not os.path.exists(self._config['orders'][i]['auth_to']):
                            continue
                    order_index.append(i)

            if not order_index:
                write_log("|-没有找到30天内到期的SSL证书!")
                return
            write_log("|-共需要续签 {} 张证书".format(len(order_index)))
            n = 0
            self.get_apis()
            cert = None
            for index in order_index:
                n += 1
                write_log("|-正在续签第 {} 张，域名: {}..".format(n,
                                                        self._config['orders'][index]['domains']))
                write_log("|-正在创建订单..")
                try:
                    index = self.create_order(
                        self._config['orders'][index]['domains'],
                        self._config['orders'][index]['auth_type'],
                        self._config['orders'][index]['auth_to'],
                        index
                    )
                
                    write_log("|-正在获取验证信息..")
                    self.get_auths(index)
                    write_log("|-正在验证域名..")
                    self.auth_domain(index)
                    write_log("|-正在发送CSR..")
                    self.remove_dns_record()
                    self.send_csr(index)
                    write_log("|-正在下载证书..")
                    cert = self.download_cert(index)
                    self._config['orders'][index]['renew_time'] = int(time.time())
                    self.save_config()
                    cert['status'] = True
                    cert['msg'] = '续签成功!'
                    write_log("|-续签成功!")
                except Exception as e:
                    write_log("|-" + str(e).split('>>>>')[0])
                write_log("-" * 70)
            return cert
        except Exception as ex:
            self.remove_dns_record()
            ex = str(ex)
            if ex.find(">>>>") != -1:
                msg = ex.split(">>>>")
                msg[1] = json.loads(msg[1])
            else:
                msg = ex
                write_log(public.get_error_info())
            return public.returnMsg(False, msg)


def echo_err(msg):
    write_log("\033[31m=" * 65)
    write_log("|-错误：{}\033[0m".format(msg))
    exit()

# 写日志
def write_log(log_str, mode="ab+"):
    if __name__ == "__main__":
        print(log_str)
        return
    _log_file = 'logs/letsencrypt.log'
    f = open(_log_file, mode)
    log_str += "\n"
    f.write(log_str.encode('utf-8'))
    f.close()
    return True


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(usage="必要的参数：--domain 域名列表，多个以逗号隔开!")
    p.add_argument('--domain', default=None,
                   help="请指定要申请证书的域名", dest="domains")
    p.add_argument('--type', default=None, help="请指定验证类型", dest="auth_type")
    p.add_argument('--path', default=None, help="请指定网站根目录", dest="path")
    p.add_argument('--dnsapi', default=None, help="请指定DNSAPI", dest="dnsapi")
    p.add_argument('--dns_key', default=None, help="请指定DNSAPI的key", dest="key")
    p.add_argument('--dns_secret', default=None,
                   help="请指定DNSAPI的secret", dest="secret")
    p.add_argument('--index', default=None, help="指定订单索引", dest="index")
    p.add_argument('--renew', default=None, help="续签证书", dest="renew")
    p.add_argument('--revoke', default=None, help="吊销证书", dest="revoke")
    args = p.parse_args()
    cert = None
    if args.revoke:
        if not args.index:
            echo_err("请在--index参数中传入要被吊销的订单索引")
        p = acme_v2()
        result = p.revoke_order(args.index)
        write_log(result)
        exit()

    if args.renew:
        p = acme_v2()
        p.renew_cert(args.index)
    else:
        try:
            if not args.index:
                if not args.domains:
                    echo_err("请在--domain参数中指定要申请证书的域名，多个以逗号(,)隔开")
                if not args.auth_type in ['http', 'tls', 'dns']:
                    echo_err("请在--type参数中指定正确的验证类型，支持dns和http")
                auth_to = ''
                if args.auth_type in ['http', 'tls']:
                    if not args.path:
                        echo_err("请在--path参数中指定网站根目录!")
                    if not os.path.exists(args.path):
                        echo_err("指定网站根目录不存在，请检查：{}".format(args.path))
                    auth_to = args.path
                else:
                    if args.dnsapi == '0':
                        auth_to = 'dns'
                    else:
                        if not args.key:
                            echo_err("使用dnsapi申请时请在--dns_key参数中指定dnsapi的key!")
                        if not args.secret:
                            echo_err(
                                "使用dnsapi申请时请在--dns_secret参数中指定dnsapi的secret!")
                        auth_to = "{}|{}|{}".format(
                            args.dnsapi, args.key, args.secret)

                domains = args.domains.strip().split(',')
                p = acme_v2()
                cert = p.apply_cert(
                    domains, auth_type=args.auth_type, auth_to=auth_to)
                if args.dnsapi == '0':
                    acme_txt = '_acme-challenge.'
                    acme_caa = '1 issue letsencrypt.org'
                    write_log("=" * 65)
                    write_log("\033[32m|-手动订单提交成功，请按以下提示解析DNS记录: \033[0m")
                    write_log("=" * 65)
                    write_log("|-订单索引: {}".format(cert['index']))
                    write_log(
                        "|-重试命令: ./acme_v2.py --index=\"{}\"".format(cert['index']))
                    write_log(
                        "|-共需要解析 \033[36m{}\033[0m 个域名记录。".format(len(cert['auths'])))
                    for i in range(len(cert['auths'])):
                        write_log('-' * 70)
                        write_log(
                            "|-第 \033[36m{}\033[0m 个域名为：{} ， 请解析以下信息：".format(i+1, cert['auths'][i]['domain']))
                        write_log("|-记录类型: TXT 记录名: \033[41m{}\033[0m  记录值: \033[41m{}\033[0m [必需]".format(
                            acme_txt + cert['auths'][i]['domain'].replace('*.', ''), cert['auths'][i]['auth_value']))
                        write_log("|-记录类型: CAA 记录名: \033[41m{}\033[0m 记录值: \033[41m{}\033[0m [可选]".format(
                            cert['auths'][i]['domain'].replace('*.', ''), acme_caa))
                    write_log('-' * 70)
                    input_data = ""
                    while input_data not in ['y', 'Y', 'n', 'N']:
                        input_msg = "请在完成解析后等待2-3分钟后输入Y按回车以继续验证域名: "
                        if sys.version_info[0] == 2:
                            input_data = raw_input(input_msg)
                        else:
                            input_data = input(input_msg)
                    if input_data in ['n', 'N']:
                        write_log("=" * 65)
                        write_log("|-用户放弃申请，退出程序!")
                        exit()
                    cert = p.apply_cert(
                        [], auth_type=args.auth_type, auth_to='dns', index=cert['index'])
            else:
                # 重新验证
                p = acme_v2()
                cert = p.apply_cert([], auth_type='dns',
                                    auth_to='dns', index=args.index)
        except Exception as ex:
            write_log("|-{}".format(public.get_error_info()))
            exit()
    if not cert:
        exit()
    write_log("=" * 65)
    write_log("|-证书获取成功!")
    write_log("=" * 65)
    write_log("证书到期时间: {}".format(
        public.format_date(times=cert['cert_timeout'])))
    write_log("证书已保存在: {}/".format(cert['save_path']))
