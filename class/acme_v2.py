#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn> a
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# ACME v2客户端
# -------------------------------------------------------------------
import warnings
warnings.filterwarnings("ignore", message=r".*doesn't\s+match\s+a\s+supported\s+version", module="requests")
import re
import fcntl
import datetime
import binascii
import hashlib
import base64
import json
import shutil
import time
import os
import sys
import uuid

os.chdir('/www/server/panel')
if not 'class/' in sys.path:
    sys.path.insert(0,'class/')
import http_requests as requests
# requests.DEFAULT_TYPE = 'curl'
import public

try:
    import OpenSSL
except:
    public.ExecShell("btpip install pyopenssl")
    import OpenSSL
try:
    import dns.resolver
except:
    public.ExecShell("btpip install dnspython")
    import dns.resolver

import ssl_info
####
# auth to 格式说明
# 旧版 auth to 格式：
# 文件验证：/www/server/xxxx/xxxx
# DNS->手动：dns  DNS->api: CloudFlareDns|XXXXXXXX|XXXXXXXXX
#
# 新版 auth to 格式：
# DNS->手动：dns DNS->api: dns#@api

class acme_v2:
    _url = None
    _apis = None
    _config = {}
    _dns_domains = []
    _bits = 2048
    _acme_timeout = 30
    _dns_class = None
    _user_agent = "BaoTa/1.0 (+https://www.bt.cn)"
    _replay_nonce = None
    _verify = False
    _digest = "sha256"
    _max_check_num = 15
    _wait_time = 5
    _mod_index = {True: "Staging", False: "Production"}
    _debug = False
    _auto_wildcard = False
    _dnsapi_file = 'config/dns_api.json'
    _save_path = 'vhost/letsencrypt'
    _conf_file = 'config/letsencrypt.json'
    _conf_file_v2 = 'config/letsencrypt_v2.json'
    _request_type = 'curl'

    def __init__(self):
        if not os.path.exists(self._conf_file_v2) and os.path.exists(self._conf_file):
            shutil.copyfile(self._conf_file, self._conf_file_v2)
        if self._debug:
            self._url = 'https://acme-staging-v02.api.letsencrypt.org/directory'
        else:
            self._url = 'https://acme-v02.api.letsencrypt.org/directory'
        self._config = self.read_config()
        self._nginx_cache_file_auth = {}
        self._can_use_lua = None
        self._well_known_check_cache = {}

    def can_use_lua_module(self):
        if self._can_use_lua is None:
            # 查询lua_module 不为空
            self._can_use_lua = public.ExecShell("nginx -V 2>&1 |grep lua_nginx_module")[0].strip() != ''
        return self._can_use_lua

    # 返回是否能通过lua 做了文件验证处理， 如果返回True，则表示可以处理了验证文件， 不再走之前的 if 验证方式
    def can_use_lua_for_site(self, site_name: str, site_type: str):
        if self._can_use_lua is None:
            # 查询lua_module 不为空
            self._can_use_lua = public.ExecShell("nginx -V 2>&1 |grep lua_nginx_module")[0].strip() != ''

        if not self._can_use_lua:
            return False

        if site_type.lower() in ("php", "proxy", "wp2"):
            prefix = ""
        else:
            prefix = site_type.lower() + "_"

        ng_file = "{}/nginx/{}{}.conf".format(public.get_vhost_path(), prefix, site_name)
        ng_data = public.readFile(ng_file)
        if not ng_data:
            return False

        rep_well_known = re.compile(
            r"(#.*\n)?\s*include\s+/www/server/panel/vhost/nginx/well-known/.*\.conf;.*\n(#.*\n)?"
            r"(.*\n)*?\s*#error_page 404/404\.html;"
        )   # 匹配一下引入的外部配置文件，同时保证这个配置在SSL配置之前， 这样避免路由匹配问题

        if rep_well_known.search(ng_data):
            lua_file = "{}/nginx/well-known/{}.conf".format(public.get_vhost_path(), site_name)
            lua_data = public.readFile(lua_file)
            if not lua_data or "set_by_lua_block $well_known" not in lua_data:
                return False
            else:
                return True
        else:
            return False

    # 返回是否能通过if 判断方式做了文件验证处理， 如果返回True，则表示可以
    @staticmethod
    def can_use_if_for_file_check(site_name: str, site_type: str):
        if site_type.lower() in ("php", "proxy", "wp2"):
            prefix = ""
        else:
            prefix = site_type.lower() + "_"

        # if 方式的文件验证必须是可重载的情况
        if public.checkWebConfig() is not True:
            return False

        ng_file = "{}/nginx/{}{}.conf".format(public.get_vhost_path(), prefix, site_name)
        ng_data = public.readFile(ng_file)
        if not ng_data:
            return False

        rep_well_known = re.compile(
            r"(#.*\n)?\s*include\s+/www/server/panel/vhost/nginx/well-known/.*\.conf;.*\n(#.*\n)?"
            r"(.*\n)*?\s*#error_page 404/404\.html;"
        )   # 匹配一下引入的外部配置文件，同时保证这个配置在SSL配置之前， 这样避免路由匹配问题

        if rep_well_known.search(ng_data):
            return True
        else:
            return False

    # 返回配置文件是否支持使用普通的文件验证
    @staticmethod
    def can_use_base_file_check(site_name: str, site_type: str):
        if site_type.lower() in ("php", "proxy", "wp2"):
            prefix = ""
        else:
            prefix = site_type.lower() + "_"

        webserver = public.get_webserver()
        if webserver == "nginx":
            ng_file = "{}/nginx/{}{}.conf".format(public.get_vhost_path(), prefix, site_name)
            ng_data = public.readFile(ng_file)
            if not ng_data:
                return False
            rep_well_known = re.compile(r"location\s+([=~^]*\s*)?/?\\?\.well-known/?\s*{")
            if rep_well_known.search(ng_data):
                return True
            else:
                return False
        elif webserver == "apache" and prefix:  # PHP 不用检查
            ap_file = "{}/apache/{}{}.conf".format(public.get_vhost_path(), prefix, site_name)
            ap_data = public.readFile(ap_file)
            if not ap_data:
                return False
            rep_well_known_list = [
                re.compile(r"<IfModule\s+alias_module>\s+Alias\s+/\.well-known/\s+\S+\s+</IfModule>"),
                re.compile(r"\s*ProxyPass\s+/\.well-known/\s+!", re.M),
            ]
            for rep_well_known in rep_well_known_list:
                if rep_well_known.search(ap_data):
                    return True
            return False
        return True

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
            res = requests.get(self._url,s_type=self._request_type)
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
        return public.split_domain_sld(domain_name)
        # top_domain_list = public.readFile('{}/config/domain_root.txt'.format(public.get_panel_path()))
        # if top_domain_list:
        #     top_domain_list = top_domain_list.strip().split('\n')
        # else:
        #     top_domain_list = []
        # old_domain_name = domain_name
        # top_domain = "."+".".join(domain_name.rsplit('.')[-2:])
        # new_top_domain = "." + top_domain.replace(".", "")
        # is_tow_top = False
        # if top_domain in top_domain_list:
        #     is_tow_top = True
        #     domain_name = domain_name[:-len(top_domain)] + new_top_domain
        #
        # if domain_name.count(".") > 1:
        #     zone, middle, last = domain_name.rsplit(".", 2)
        #     if is_tow_top:
        #         last = top_domain[1:]
        #     root = ".".join([middle, last])
        # else:
        #     zone = ""
        #     root = old_domain_name
        # return root, zone

    # 自动构造通配符
    def auto_wildcard(self, domains):
        if not domains:
            return domains
        domain_list = []
        for domain in domains:
            root, zone = self.extract_zone(domain)
            tmp_list = zone.rsplit(".", 1)
            if len(tmp_list) == 1:
                if root not in domain_list:
                    domain_list.append(root)
                if not "*." + root in domain_list:
                    domain_list.append("*." + root)
            else:
                new_root = "{}.{}".format(tmp_list[1], root)
                if new_root not in domain_list:
                    domain_list.append(new_root)
                if not "*." + new_root in domain_list:
                    domain_list.append("*." + new_root)
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
                    apply_domains.remove(domain)

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
        if not res.status_code in [201,200]:  # 如果创建失败
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
            if not res.status_code in [201,200]:
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

    def get_site_run_path_byid(self,site_id):
        '''
            @name 通过site_id获取网站运行目录
            @author hwliang
            @param site_id<int> 网站标识
            @return None or string
        '''
        if public.M('sites').where('id=? and project_type=?', (site_id, 'PHP')).count()>=1:
            site_path = public.M('sites').where('id=?',site_id).getField('path')
            if not site_path: return None
            if not os.path.exists(site_path): return None
            args = public.dict_obj()
            args.id = site_id
            import panelSite
            run_path = panelSite.panelSite().GetRunPath(args)
            if run_path in ['/']: run_path = ''
            if run_path:
                if run_path[0] == '/': run_path = run_path[1:]
            site_run_path = os.path.join(site_path,run_path)
            if not os.path.exists(site_run_path): return site_path
            return site_run_path
        else:
            find = public.M('sites').where('id=?',site_id).find()
            if not find:
                return False
            count = public.M('sites').where(
                'id=? and project_type in (?,?,?,?)',
                (site_id, 'Java', 'Go', 'Other', "Python")
            ).count()
            if count:
                try:
                    project_info = json.loads(find['project_config'])
                    if 'ssl_path' not in project_info:
                        ssl_path = '/www/wwwroot/java_node_ssl'
                    else:
                        ssl_path = project_info['ssl_path']
                    if not os.path.exists(ssl_path):
                        os.makedirs(ssl_path)
                    return ssl_path
                except:
                    return False
            else:
                import panelSite
                auth_to = find['path'] + '/' + panelSite.panelSite().GetRunPath(public.to_dict_obj({"id": site_id}))
                auth_to = auth_to.replace("//", "/")
                if auth_to[-1] == '/':
                    auth_to = auth_to[:-1]
                if not os.path.exists(auth_to):
                    return False
                return auth_to


    def get_site_run_path(self,domains):
        '''
            @name 通过域名列表获取网站运行目录
            @author hwliang
            @param domains<list> 域名列表
            @return None or string
        '''
        site_id = 0
        for domain in domains:
            site_id = public.M('domain').where("name=?",domain).getField('pid')
            if site_id: break

        if not site_id: return None
        return self.get_site_run_path_byid(site_id)

    # 获取验证信息
    def get_auths(self, index):
        if not index in self._config['orders']:
            raise Exception('指定订单不存在!')

        # 检查是否已经获取过授权信息
        if 'auths' in self._config['orders'][index]:
            # 检查授权信息是否过期
            if time.time() < self._config['orders'][index]['auths'][0]['expires']:
                return self._config['orders'][index]['auths']
        if self._config['orders'][index]['auth_type'] != 'dns':
            site_run_path = self.get_site_run_path(self._config['orders'][index]['domains'])
            if site_run_path: self._config['orders'][index]['auth_to'] = site_run_path

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
            self.set_auth_info(identifier_auth, index=index)
            auths.append(identifier_auth)
        self._config['orders'][index]['auths'] = auths
        self.save_config()
        if not self.check_config(index, "auths", auths):
            self.save_config()
        return auths

    # 更新随机数
    def update_replay_nonce(self, res):
        replay_nonce = res.headers.get('Replay-Nonce')
        if replay_nonce:
            self._replay_nonce = replay_nonce

    # 设置验证信息
    def set_auth_info(self, identifier_auth, index=None):

        #从云端验证
        if not self.cloud_check_domain(identifier_auth['domain']):
            self.err = "云端验证失败!"

        # 是否手动验证DNS
        if identifier_auth['auth_to'] == 'dns':
            return None

        # 是否文件验证
        if identifier_auth['type'] in ['http', 'tls']:
            self.write_auth_file(
                identifier_auth['auth_to'], identifier_auth['token'], identifier_auth['acme_keyauthorization'], index)
        else:
            # dnsapi验证
            self.create_dns_record(
                identifier_auth['auth_to'], identifier_auth['domain'], identifier_auth['auth_value'])

    #从云端验证域名是否可访问
    def cloud_check_domain(self,domain):
        try:
            result = requests.post('https://www.bt.cn/api/panel/check_domain',{"domain":domain,"ssl":1},s_type=self._request_type).json()
            return result['status']
        except: return False


    #清理验证文件
    def claer_auth_file(self,index):
        if not self._config['orders'][index]['auth_type'] in ['http','tls']:
            return True
        acme_path = '{}/.well-known/acme-challenge'.format(self._config['orders'][index]['auth_to'])
        acme_path = acme_path.replace("//",'/')
        write_log("|-验证目录：{}".format(acme_path))
        if os.path.exists(acme_path):
            public.ExecShell("rm -f {}/*".format(acme_path))

        acme_path = '/www/server/stop/.well-known/acme-challenge'
        if os.path.exists(acme_path):
            public.ExecShell("rm -f {}/*".format(acme_path))

    def change_well_known_mod(self, path_dir: str):
        path_dir = path_dir.rstrip("/")
        if not os.path.isdir(path_dir):
            return False
        if path_dir in self._well_known_check_cache:
            return True
        else:
            self._well_known_check_cache[path_dir] = True
        import stat

        try:
            import pwd
            uid_data = pwd.getpwnam("www")
            uid = uid_data.pw_uid
            gid = uid_data.pw_gid
        except:
            return

        # 逐级给最低访问权限
        while path_dir != "/":
            path_dir_stat = os.stat(path_dir)
            if path_dir_stat.st_uid == 0 and uid != 0:
                old_mod = stat.S_IMODE(path_dir_stat.st_mode)
                if not old_mod & (1 << 3):
                    os.chmod(path_dir, old_mod + (1 << 3))  # chmod g+x
            if path_dir_stat.st_uid == uid:
                old_mod = stat.S_IMODE(path_dir_stat.st_mode)
                if not old_mod & (1 << 6):
                    os.chmod(path_dir, old_mod + (1 << 6))  # chmod u+x
            elif path_dir_stat.st_gid == gid:
                old_mod = stat.S_IMODE(path_dir_stat.st_mode)
                if not old_mod & (1 << 3):
                    os.chmod(path_dir, old_mod + (1 << 6))  # chmod g+x
            elif path_dir_stat.st_uid != uid or path_dir_stat.st_gid != gid:
                old_mod = stat.S_IMODE(path_dir_stat.st_mode)
                if not old_mod & 1:
                    os.chmod(path_dir, old_mod+1)   # chmod o+x
            path_dir = os.path.dirname(path_dir)

    # 写验证文件
    def write_auth_file(self, auth_to, token, acme_keyauthorization, index):
        if public.get_webserver() == "nginx":
            # 如果是nginx尝试使用配置文件进行验证
            self.write_ngin_authx_file(auth_to, token, acme_keyauthorization, index)

        # 尝试写文件进行验证
        try:
            acme_path = '{}/.well-known/acme-challenge'.format(auth_to)
            acme_path = acme_path.replace("//",'/')
            if not os.path.exists(acme_path):
                os.makedirs(acme_path)
                public.set_own(acme_path, 'www')
            self.change_well_known_mod(acme_path)
            wellknown_path = '{}/{}'.format(acme_path, token)
            public.writeFile(wellknown_path, acme_keyauthorization)
            public.set_own(wellknown_path, 'www')

            acme_path = '/www/server/stop/.well-known/acme-challenge'
            if not os.path.exists(acme_path):
                os.makedirs(acme_path)
                public.set_own(acme_path, 'www')
            self.change_well_known_mod(acme_path)
            wellknown_path = '{}/{}'.format(acme_path,token)
            public.writeFile(wellknown_path,acme_keyauthorization)
            public.set_own(wellknown_path, 'www')
            return True
        except:
            err = public.get_error_info()
            print(err)
            raise Exception("写入验证文件失败: {}".format(err))

    def write_ngin_authx_file(self, auth_to, token, acme_keyauthorization, index):
        site_name, project_type = self.get_site_name_by_domains(self._config["orders"][index]["domains"])
        if site_name is None:
            return

        if self.can_use_lua_for_site(site_name, project_type):
            return

        if project_type.lower() in ("php", "proxy"):
            nginx_conf_path = "{}/vhost/nginx/{}.conf".format(public.get_panel_path(), site_name)
        else:
            nginx_conf_path = "{}/vhost/nginx/{}_{}.conf".format(public.get_panel_path(), project_type.lower(), site_name)
        nginx_conf = public.readFile(nginx_conf_path)
        if nginx_conf is False:
            return

        file_check_config_path = "/www/server/panel/vhost/nginx/well-known/{}.conf".format(site_name)
        if not os.path.exists("/www/server/panel/vhost/nginx/well-known"):
            os.makedirs("/www/server/panel/vhost/nginx/well-known", 0o755)

        # 如果主配置中，没有引用则尝试添加，添加失败就跳出
        if not re.search(r"\s*include\s+/www/server/panel/vhost/nginx/well-known/.*\.conf;", nginx_conf, re.M):
            ssl_line = re.search(r"(#.*\n\s*)?#error_page 404/404\.html;", nginx_conf)
            if ssl_line is None:
                return
            default_cert_apply_check = (
                "#CERT-APPLY-CHECK--START\n"
                "    # 用于SSL证书申请时的文件验证相关配置 -- 请勿删除\n"
                "    include /www/server/panel/vhost/nginx/well-known/{}.conf;\n"
                "    #CERT-APPLY-CHECK--END\n    "
            ).format(site_name)
            if not os.path.exists(file_check_config_path):
                public.writeFile(file_check_config_path, "")

            new_conf = nginx_conf.replace(ssl_line.group(), default_cert_apply_check + ssl_line.group(), 1)
            public.writeFile(nginx_conf_path, new_conf)
            isError = public.checkWebConfig()
            if isError is not True:
                public.writeFile(nginx_conf_path, nginx_conf)
                return

        # 如果主配置有引用， 不再检测位置关系，因为不能保证用户的自定义配置的优先级， 直接进行文件验证的 lua 方式和 if 方式的尝试
        if self.can_use_lua_module():
            self.write_lua_file_for_site(file_check_config_path)
            return

        # 开始尝试if 验证方式
        if auth_to not in self._nginx_cache_file_auth:
            self._nginx_cache_file_auth[auth_to] = []

        self._nginx_cache_file_auth[auth_to].append((token, acme_keyauthorization))

        tmp_data = []
        for token, acme_key in self._nginx_cache_file_auth[auth_to]:
            tmp_data.append((
                'if ($request_uri ~ "^/\.well-known/acme-challenge/{}.*"){{\n'
                '    return 200 "{}";\n'
                '}}\n'
            ).format(token, acme_key))

        public.writeFile(file_check_config_path, "\n".join(tmp_data))
        isError = public.checkWebConfig()
        if isError is True:
            public.serviceReload()
        else:
            public.writeFile(file_check_config_path, "")

    @staticmethod
    def write_lua_file_for_site(file_check_config_path: str):
        old_data = public.readFile(file_check_config_path)
        if isinstance(old_data, str) and "set_by_lua_block $well_known" in old_data:
            return

        lua_file_data = """
set $well_known '';
if ( $uri ~ "^/.well-known/" ) {
  set_by_lua_block $well_known { 
    -- 获取路径
    local m,err = ngx.re.match(ngx.var.uri,"/.well-known/(.*)","isjo")
    -- 如果路径匹配
    if m then
      -- 拼接文件路径
      local filename = ngx.var.document_root .. m[0]
      -- 判断文件路径中是否合法
      if not ngx.re.find(m[1],"\\\\./","isjo") then
        -- 判断文件是否存在
        local is_exists = io.open(filename, "r")
        if not is_exists then
            -- Java项目?
            filename = "/www/wwwroot/java_node_ssl" ..  m[0]
        end
        -- 释放
        if is_exists then is_exists:close() end
        -- 读取文件
        local fp = io.open(filename,'r')
        if fp then
          local file_body = fp:read("*a")
          fp:close()
          if file_body then
            ngx.header['content-type'] = 'text/plain'
            return file_body
          end
        end
      end
    end
    return ""
  }
}

if ( $well_known != "" ) {
  return 200 $well_known;
}
"""
        public.writeFile(file_check_config_path, lua_file_data)
        isError = public.checkWebConfig()
        if isError is True:
            public.serviceReload()
        else:
            public.writeFile(file_check_config_path, old_data)

    # 解析域名 新的 前端修改完用这个
    # def create_dns_record(self, auth_to, domain, dns_value):
    #     # 如果为手动解析
    #     if auth_to == 'dns':
    #         return None
    #
    #     from panelDnsapi import DnsMager
    #
    #     self._dns_class = DnsMager().get_dns_obj_by_domain(domain)
    #     self._dns_class.create_dns_record(public.de_punycode(domain), dns_value)
    #     self._dns_domains.append({"domain": domain, "dns_value": dns_value})

    # 解析域名
    def create_dns_record(self, auth_to, domain, dns_value):
        # 如果为手动解析
        if auth_to == 'dns':
            return None

        if auth_to.find('|') != -1:
            import panelDnsapi
            dns_name, key, secret = self.get_dnsapi(auth_to)
            self._dns_class = getattr(panelDnsapi, dns_name)(key, secret)
            self._dns_class.create_dns_record(public.de_punycode(domain), dns_value)
        # else:
        #     from panelDnsapi import DnsMager
        #     self._dns_class = DnsMager().get_dns_obj_by_domain(domain)
        # self._dns_class.create_dns_record(public.de_punycode(domain), dns_value)
        # self._dns_domains.append({"domain": domain, "dns_value": dns_value})
        else:
            from sslModel import dataModel
            dataModel.main().add_dns_value_by_domain(domain, dns_value, is_let_txt=True)
        self._dns_domains.append({"domain": domain, "dns_value": dns_value})
        return

    # 解析域名
    # def create_dns_record(self, auth_to, domain, dns_value):
    #     # 如果为手动解析
    #     if auth_to == 'dns' or auth_to.find('|') == -1:
    #         return None
    #
    #     import panelDnsapi
    #     dns_name, key, secret = self.get_dnsapi(auth_to)
    #     self._dns_class = getattr(panelDnsapi, dns_name)(key, secret)
    #     self._dns_class.create_dns_record(public.de_punycode(domain), dns_value)
    #     self._dns_domains.append({"domain": domain, "dns_value": dns_value})
    #     return

    # 解析DNSAPI信息  # 不再使用的
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
        if not self._dns_domains:
            return None
        for dns_info in self._dns_domains:
            try:
                if self._dns_class:
                    self._dns_class.delete_dns_record(
                        public.de_punycode(dns_info['domain']), dns_info['dns_value'])
                else:
                    from sslModel import dataModel
                    dataModel.main().del_dns_value_by_domain(dns_info['domain'], is_let_txt=True)
            except Exception as e:
                pass

    # 验证域名
    def auth_domain(self, index):
        self._config['orders'][index]['auth_tag'] = True
        self.save_config()
        if index not in self._config['orders']:
            raise Exception('指定订单不存在!')

        if "auths" not in self._config['orders'][index]:
            raise Exception('订单验证信息丢失，请尝试重新申请!')

        # 开始验证
        for auth in self._config['orders'][index]['auths']:
            res = self.check_auth_status(auth['url'])  # 检查是否需要验证
            if res.json()['status'] == 'invalid':
                raise Exception('域名验证失败，请尝试重新申请!')
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

    def auth_domain_api(self, get):
        """
        验证单个域名
        """
        index = get.index
        domain = get.domain
        self.get_apis()

        write_log("|-正在验证域名：{}".format(domain))
        if index not in self._config['orders']:
            return public.returnMsg(False, '指定订单不存在!')
        order = self._config['orders'][index]
        if "auths" not in order:
            return public.returnMsg(False, '订单验证信息丢失，请尝试重新申请!')

        for auth in order['auths']:
            if auth.get("status") == "invalid":
                return public.returnMsg(False, "域名验证失败，请尝试重新申请！")
            if domain and auth['domain'] != domain:
                continue
            try:
                res = self.check_auth_status(auth['url'])  # 检查是否需要验证
                if res.json()['status'] == 'pending':
                    self.respond_to_challenge(auth)
                    _return = self.check_auth_status(auth['url'], ['valid', 'invalid']).json()
                    auth['status'] = _return['status']
                    return auth
                auth['status'] = res.json()['status']
                write_log("|-验证成功!")
                return auth
            except StopIteration as e:
                auth['status'] = 'invalid'
                ex = str(e)
                if ex.find(">>>>") != -1:
                    msg = ex.split(">>>>")
                    msg[1] = json.loads(msg[1])
                else:
                    msg = ex
                    write_log(public.get_error_info())
                auth['error'] = msg
                return public.returnMsg(False, msg)
            finally:
                self.save_config()
                if "pending" not in [i.get("status", "pending") for i in order['auths']]:
                    return self.apply_dns_auth(get)
        write_log("|-没有在订单中找到此域名：{}".format(domain))
        return public.returnMsg(False, "没有在订单中找到此域名：{}".format(domain))

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
            if not isinstance(a_auth, dict):
                write_log(a_auth)
                continue
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
        write_log("error_result: " + str(error))
        if error.find("Max checks allowed") >= 0:
            return "CA无法验证您的域名，请检查域名解析是否正确，或等待5-10分钟后重试."
        elif error.find("Max retries exceeded with") >= 0 or error.find('status_code=0 ') != -1:
            return "CA服务器连接超时，请稍候重试."
        elif error.find("The domain name belongs") >= 0:
            return "域名不属于此DNS服务商，请确保域名填写正确."
        elif error.find("domains in the last 168 hours") != -1 and error.find("Error creating new order") != -1:
            return "签发失败,该域名%s的根域名超出了每周的最大签发次数限制!" % re.findall("hours:\s+(.+?),", error)
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
        elif error.find("The ACME server can not issue a certificate for an IP address") != -1:
            return "不能使用IP地址申请证书!"
        elif error.find('Cannot issue for') != -1:
            return "无法为{}颁发证书，不能直接用域名后缀申请通配符证书!".format(re.findall(r'for\s+"(.+)"',error))
        elif error.find('too many failed authorizations recently') != -1:
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
        elif error.find('Only domain names are supported') != -1:
            return "Let's Encrypt仅支持使用域名申请证书"
        elif error.find('DNSSEC: DNSKEY Missing') != -1:
            return "CA无法找到或获取用于验证DNSSEC签名的DNSKEY记录"
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
            if send_csr_response.status_code == 0:
                raise ValueError("错误：提示Connection reset by peer,可能请求过程被意外拦截，如果只有此域名无法申请，则该域名可能存在异常!")
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

        info = ssl_info.ssl_info().load_ssl_info_by_data(cret_data)
        if not info:
            return int(time.time() + (86400 * 90))

        try:
            return public.to_date(times=info['notAfter'])
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
            from ssl_manage import SSLManger
            SSLManger().save_by_data(cert['cert'] + cert['root'], cert['private_key'])

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

            self.set_exclude_hash(index, cert['cert'] + cert['root'])

            # 转为IIS证书
            try:
                pfx_buffer = self.dump_pkcs12(
                    cert['private_key'], cert['cert'] + cert['root'], cert['root'], domain_name)
            except:
                pfx_buffer = ssl_info.ssl_info().dump_pkcs12_new(
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

    def set_exclude_hash(self, order, exclude_hash):
        try:
            path = '{}/data/exclude_hash.json'.format(public.get_panel_path())

            try:
                data = json.loads(public.readFile(path))
            except:
                data = self.get_exclude_hash(public.to_dict_obj({}))
            if "exclude_hash_let" not in data:
                data["exclude_hash_let"] = {}
            data['exclude_hash_let'].update({order: self._hash(certificate=exclude_hash)})
            public.writeFile(path, json.dumps(data))
        except:
            pass

    def get_exclude_hash(self, get):
        path = '{}/data/exclude_hash.json'.format(public.get_panel_path())

        import panelSSL
        exclude_data = panelSSL.panelSSL().get_exclude_hash(get)
        if exclude_data.get('version_let') == '1':
            return exclude_data
        if "exclude_hash_let" not in exclude_data:
            exclude_data["exclude_hash_let"] = {}

        data = self.read_config()
        try:
            self.get_apis()
        except:
            return exclude_data

        for order in data.get('orders', {}).values():
            if order['status'] != "valid" or not order.get("certificate_url"):
                continue
            try:
                res = self.acme_request(
                    order['certificate_url'], "")
                if res.status_code not in [200, 201]:
                    continue
                pem_certificate = res.content
                if type(pem_certificate) == bytes:
                    pem_certificate = pem_certificate.decode('utf-8')
                cert = self.split_ca_data(pem_certificate)
                exclude_data["exclude_hash_let"].update({order['index']: self._hash(certificate=cert['cert'] + cert['root'])})
            except:
                pass
        exclude_data['version_let'] = '1'
        public.writeFile(path, json.dumps(exclude_data))
        return exclude_data

    def _hash(self, cert_filename: str = None, certificate: str = None, ignore_errors: bool = False):
        if cert_filename is not None and os.path.isfile(cert_filename):
            certificate = public.readFile(cert_filename)

        if not isinstance(certificate, str) or not certificate.startswith("-----BEGIN"):
            if ignore_errors:
                return None
            raise ValueError("证书格式错误")

        md5_obj = hashlib.md5()
        md5_obj.update(certificate.encode("utf-8"))
        return md5_obj.hexdigest()


    # 通过域名获取网站名称
    def get_site_name_by_domains(self,domains):
        sql = public.M('domain')
        site_sql = public.M('sites')
        siteName, project_type = None, None
        for domain in domains:
            pid = sql.where('name=?',domain).getField('pid')
            if pid:
                site_data = site_sql.where('id=?', pid).field('name,project_type').find()
                siteName, project_type = site_data["name"], site_data["project_type"]
                break
        return siteName, project_type

    # 替换服务器上的同域名同品牌证书
    def sub_all_cert(self, key_file, pem_file):
        cert_init = self.get_cert_init(pem_file)  # 获取新证书的基本信息
        paths = ['/www/server/panel/vhost/cert', '/www/server/panel/vhost/ssl','/www/server/panel']
        is_panel = False
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
                    if not p_name in ['ssl']: continue
                    to_pem_file = to_path + '/certificate.pem'
                    to_key_file = to_path + '/privateKey.pem'
                    if not os.path.exists(to_pem_file):
                        continue
                # 获取目标证书的基本信息
                to_cert_init = self.get_cert_init(to_pem_file)
                # 判断证书品牌是否一致
                try:
                    if to_cert_init['issuer'] != cert_init['issuer'] and to_cert_init['issuer'].find("Let's Encrypt") == -1 and to_cert_init.get('issuer_O', '') != "Let's Encrypt":
                        continue
                except: continue
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
                if path == paths[-1]: is_panel = True

        # 重载web服务
        public.serviceReload()
        # if is_panel: public.restart_panel()

    # 检查指定证书是否在订单列表
    def check_order_exists(self, pem_file):
        try:
            cert_init = self.get_cert_init(pem_file)
            if not cert_init:
                return None
            if not (cert_init['issuer'].find("Let's Encrypt") != -1 or cert_init['issuer'] in ('R3', 'R10', 'R11') or cert_init.get('issuer_O', '') == "Let's Encrypt"):
                return None
            for index in self._config['orders'].keys():
                if not 'save_path' in self._config['orders'][index]:
                    continue
                for domain in self._config['orders'][index]['domains']:
                    if domain in cert_init['dns']:
                        return index
            return pem_file
        except:
            return None

    # 取证书基本信息API
    def get_cert_init_api(self, args):
        if not os.path.exists(args.pem_file):
            args.pem_file = 'vhost/cert/{}/fullchain.pem'.format(args.siteName)
            if not os.path.exists(args.pem_file):
                return public.returnMsg(False, '指定证书文件不存在!')
        cert_init = self.get_cert_init(args.pem_file)
        if not cert_init:
            return public.returnMsg(False, '证书信息获取失败!')
        try:
            cert_init['dnsapi'] = json.loads(public.readFile(self._dnsapi_file))
        except:
            cert_init['dnsapi'] = []
        return cert_init

    # 获取指定证书基本信息
    def get_cert_init(self, pem_file):
        return ssl_info.ssl_info().load_ssl_info(pem_file)

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
    def split_ca_data(self,cert):
        sp_key = '-----END CERTIFICATE-----\n'
        datas = cert.split(sp_key)
        return {"cert": datas[0] + sp_key, "root": sp_key.join(datas[1:])}

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
        try:
            X509Req.set_version(2)
        except ValueError as e:  # pyOpenSSL 新版本需要必须设置版本为0
            X509Req.set_version(0)
        X509Req.sign(pk, self._digest)
        return OpenSSL.crypto.dump_certificate_request(OpenSSL.crypto.FILETYPE_ASN1, X509Req)

    def create_csr_new(self, index):
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives import serialization
        # 如果已经生成了 CSR，直接返回
        if 'csr' in self._config['orders'][index]:
            return self._config['orders'][index]['csr']

        # 获取域名和备用域名
        domain_name, domain_alt_names = self.get_alt_names(index)

        # 生成私钥
        pk = self.create_certificate_key(index).encode()
        private_key = serialization.load_pem_private_key(pk, password=None)

        # 构建 CSR
        csr_builder = x509.CertificateSigningRequestBuilder().subject_name(
            x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, domain_name),
            ])
        )

        # 添加 subjectAltName 扩展
        if domain_alt_names:
            alt_names = [x509.DNSName(domain_name)] + [x509.DNSName(alt) for alt in domain_alt_names]
        else:
            alt_names = [x509.DNSName(domain_name)]

        csr_builder = csr_builder.add_extension(
            x509.SubjectAlternativeName(alt_names),
            critical=False
        )

        # 签署 CSR
        csr = csr_builder.sign(private_key, hashes.SHA256())

        # 返回 CSR (ASN1 格式)
        return csr.public_bytes(serialization.Encoding.DER)

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
            # index = public.md5(json.dumps(order_object['identifiers']))
            index = public.md5(str(uuid.uuid4()))
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
            url, data=data.encode("utf8"), timeout=self._acme_timeout, headers=headers, verify=self._verify,s_type=self._request_type
        )
        # 更新随机数
        self.update_replay_nonce(response)
        return response

    # 计算signature
    def sign_message(self, message):
        try:
            pk = OpenSSL.crypto.load_privatekey(
                OpenSSL.crypto.FILETYPE_PEM, self.get_account_key().encode())
            return OpenSSL.crypto.sign(pk, message.encode("utf8"), self._digest)
        except:
            return self.sign_message_new(message)

    def sign_message_new(self, message):
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding

        import ssl_info
        pk = ssl_info.ssl_info().analysis_private_key(self.get_account_key())
        return pk.sign(message.encode("utf8"), padding.PKCS1v15(), hashes.SHA256())

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
                verify=self._verify,
                s_type=self._request_type
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
            try:
                self._config['account'][k]['key'] = self.create_key()
            except:
                self._config['account'][k]['key'] = self.create_key_new()
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
        try:
            private_key = self.create_key()
        except:
            private_key = self.create_key_new()
        if type(private_key) == bytes:
            private_key = private_key.decode()
        # 保存私钥到订单配置文件
        self._config['orders'][index]['private_key'] = private_key
        self.save_config()
        return private_key

    # 创建Key
    def create_key(self, key_type=None):
        if key_type not in [OpenSSL.crypto.TYPE_RSA, OpenSSL.crypto.TYPE_DSA, OpenSSL.crypto.TYPE_EC]:
            key_type = OpenSSL.crypto.TYPE_RSA
        key = OpenSSL.crypto.PKey()
        key.generate_key(key_type, self._bits)
        private_key = OpenSSL.crypto.dump_privatekey(
            OpenSSL.crypto.FILETYPE_PEM, key)
        return private_key

    def create_key_new(self, key_type='RSA'):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa, ec, ed25519

        if key_type == 'RSA':
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=self._bits
            )
        elif key_type == 'EC':
            private_key = ec.generate_private_key(ec.SECP256R1())
        elif key_type == 'ED25519':
            private_key = ed25519.Ed25519PrivateKey.generate()
        else:
            raise ValueError(f"Unsupported key type: {key_type}")

        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        return private_key_pem

    # 写配置文件
    def save_config(self):
        fp = open(self._conf_file_v2, 'w+')
        fcntl.flock(fp, fcntl.LOCK_EX)  # 加锁
        fp.write(json.dumps(self._config))
        fcntl.flock(fp, fcntl.LOCK_UN)  # 解锁
        fp.close()
        return True

    # 读配置文件
    def read_config(self):
        if not os.path.exists(self._conf_file_v2):
            self._config['orders'] = {}
            self._config['account'] = {}
            self._config['apis'] = {}
            self._config['email'] = public.M('config').where('id=?',(1,)).getField('email')
            if self._config['email'] in [public.en_hexb('4d6a67334f5459794e545932514846784c6d4e7662513d3d')]:
                self._config['email'] = None
            self.save_config()
            return self._config
        tmp_config = public.readFile(self._conf_file_v2)
        if not tmp_config:
            return self._config
        try:
            self._config = json.loads(tmp_config)
        except:
            self.save_config()
            return self._config
        return self._config

    def check_config(self, index, key, value) -> bool:
        tmp_config = public.readFile(self._conf_file_v2)
        if not tmp_config:
            return False
        try:
            config_data = json.loads(tmp_config)
        except:
            return False

        if index not in config_data.get("orders", {}):
            return False

        if key not in config_data['orders'][index]:
            return False
        if config_data['orders'][index][key] == value:
            return True
        else:
            return False

    # 申请证书
    def apply_cert(self, domains, auth_type='dns', auth_to='Dns_com|None|None', **args):
        index = ''
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
                    auth_domains = [i["domain"].replace("*.", "") for i in self._config['orders'][index]['auths']]
                    if len(auth_domains) != len(set(auth_domains)):
                        self._config['orders'][index]["error"] = True
                        self._config['orders'][index]["error_msg"] = "检测到解析记录存在冲突，请分别验证以下域名"
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
            _res = {"status": False, "msg": msg, "index": index}
            return _res

    # 申请证书 - api
    def apply_cert_api(self, args):
        """
        @name 申请证书
        @param domains: list 域名列表
        @param auth_type: str 认证方式
        @param auth_to: str 认证路径
        @param auto_wildcard: str 是否自动组合泛域名
        """
        if not 'id' in args:
            return public.returnMsg(False,'网站id不能为空!')

        if 'auto_wildcard' in args and args.auto_wildcard == '1':
            self._auto_wildcard = True

        find = public.M('sites').where('id=?', (args.id,)).find()
        if not find:
            return public.returnMsg(False, "网站丢失，无法继续申请证书")

        if args.auth_type in ['http', 'tls']:
            if find["status"] != "1":
                return public.returnMsg(False, "当前网站未开启不能使用文件验证")
            if not self.can_use_base_file_check(find["name"], find["project_type"]):
                webserver: str = public.get_webserver()
                msg = "当前项目的服务（{}）配置文件被修改不支持文件验证，请选择其他方式或还原配置文件".format(webserver.title())
                if webserver != 'nginx':
                    return public.returnMsg(False, msg)
                # nginx 检测其他两种方案的可行性
                if not self.can_use_lua_for_site(find["name"], find["project_type"]) and \
                        not self.can_use_if_for_file_check(find["name"], find["project_type"]):

                    return public.returnMsg(False, msg)

        # 是否为指定站点
        count = public.M('sites').where(
            'id=? and project_type in (?,?,?,?)',
            (args.id, 'Java', 'Go', 'Other', "Python")
        ).count()
        if count:
            try:
                project_info = json.loads(find['project_config'])
                if 'ssl_path' not in project_info:
                    ssl_path = '/www/wwwroot/java_node_ssl'
                else:
                    ssl_path = project_info['ssl_path']
                if not os.path.exists(ssl_path):
                    os.makedirs(ssl_path)

                args.auth_to = ssl_path
            except:
                return public.returnMsg(False, '当前项目配置文件存在问题,请重新建立')
        else:
            if re.match(r"^\d+$", args.auth_to):
                import panelSite
                args.auth_to = find['path'] + '/' + panelSite.panelSite().GetRunPath(args)
                args.auth_to = args.auth_to.replace("//", "/")
                if args.auth_to[-1] == '/':
                    args.auth_to = args.auth_to[:-1]

                if not os.path.exists(args.auth_to):
                    return public.returnMsg(False, '无效的站点目录，请检查指定站点是否存在!')

            #检查认证环境
            if args.auth_type in ['http', 'tls']:
                check_result = self.check_auth_env(args)
                if check_result:
                    return check_result

        return self.apply_cert(json.loads(args.domains), args.auth_type, args.auth_to)

    # 检查认证环境
    def check_auth_env(self,args):
        for domain in json.loads(args.domains):
            if public.checkIp(domain): continue
            if domain.find('*.') != -1 and args.auth_type in ['http','tls']:
                return public.returnMsg(False, '泛域名不能使用【文件验证】的方式申请证书!')

        data = public.M('sites').where('id=?', (args.id,)).find()
        if not data:
            return public.returnMsg(False, "网站丢失，无法继续申请证书")
        else:
            args.siteName = data['name']
            site_type = data["project_type"]

        use_nginx_conf_to_auth = False
        if args.auth_type in ['http', 'tls'] and public.get_webserver() == "nginx":  # nginx 在lua验证和可重启的
            if self.can_use_lua_for_site(args.siteName, site_type):
                use_nginx_conf_to_auth = True
            else:
                if self.can_use_if_for_file_check(args.siteName, site_type):
                    use_nginx_conf_to_auth = True

        import panelSite
        s = panelSite.panelSite()
        if args.auth_type in ['http', 'tls'] and use_nginx_conf_to_auth is False:
            try:
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
        if not hasattr(args, "index") or not args.index:
            return public.returnMsg(False, "参数信息不完整，没有索引参数【index】")
        return self.apply_cert([], auth_type='dns', auth_to='dns', index=args.index)


    #创建计划任务
    def set_crond(self):
        try:
            echo = public.md5(public.md5('renew_lets_ssl_bt'))
            find = public.M('crontab').where('echo=?',(echo,)).find()
            cron_id = find['id'] if find else None

            import crontab
            import random
            args_obj = public.dict_obj()
            if not cron_id:
                cronPath = public.GetConfigValue('setup_path') + '/cron/' + echo
                shell = '{} -u /www/server/panel/class/acme_v2.py --renew_v2=1'.format(sys.executable)
                public.writeFile(cronPath,shell)

                # 使用随机时间
                hour = random.randint(0, 23)
                minute = random.randint(1, 59)
                args_obj.id = public.M('crontab').add('name,type,where1,where_hour,where_minute,echo,addtime,status,save,backupTo,sType,sName,sBody,urladdress',("续签Let's Encrypt证书",'day','',hour,minute,echo,time.strftime('%Y-%m-%d %X',time.localtime()),0,'','localhost','toShell','',shell,''))
                crontab.crontab().set_cron_status(args_obj)
            else:
                # 检查任务如果是0点10分执行，改为随机时间
                if find['where_hour'] == 0 and find['where_minute'] == 10:
                    print('修改任务时间')
                    # 使用随机时间
                    hour = random.randint(0, 23)
                    minute = random.randint(1, 59)
                    public.M('crontab').where('id=?',(cron_id,)).save('where_hour,where_minute,status',(hour,minute,0))

                    # 停用任务
                    args_obj.id = cron_id
                    crontab.crontab().set_cron_status(args_obj)

                    # 启用任务
                    public.M('crontab').where('id=?',(cron_id,)).setField('status',1)
                    crontab.crontab().set_cron_status(args_obj)

                cron_path = public.get_cron_path()
                if os.path.exists(cron_path):
                    cron_s = public.readFile(cron_path)
                    if cron_s.find(echo) == -1:
                        public.M('crontab').where('id=?',(cron_id,)).setField('status',0)
                        args_obj.id = cron_id
                        crontab.crontab().set_cron_status(args_obj)
        except:pass


    # 获取当前正在使用此证书的网站目录
    def get_ssl_used_site(self, index):
        hash_dic = self.get_exclude_hash(public.dict_obj())
        if not hash_dic: return False
        ssl_hash = hash_dic.get("exclude_hash_let", {}).get(index, '')
        if not ssl_hash: return False

        cert_paths = 'vhost/cert'
        import panelSite
        args = public.dict_obj()
        args.siteName = ''
        for c_name in os.listdir(cert_paths):
            skey_file = '{}/{}/fullchain.pem'.format(cert_paths,c_name)
            try:
                skey = self._hash(cert_filename=skey_file)
            except:
                continue
            if not skey: continue
            if skey == ssl_hash:
                args.siteName = c_name
                site_info = public.M('sites').where('name=?', c_name).find()
                if not site_info or isinstance(site_info, str):
                    return False
                if site_info["project_type"] not in ("PHP", "proxy"):
                    if not os.path.isdir(site_info["path"]):
                        return os.path.dirname(site_info["path"])
                    else:
                        return site_info["path"]

                run_path = panelSite.panelSite().GetRunPath(args)
                if not run_path:
                    continue
                sitePath = public.M('sites').where('name=?',c_name).getField('path')
                if not sitePath:
                    continue
                to_path = "{}/{}".format(sitePath,run_path)
                to_path = to_path.replace("//", "/")
                return to_path
        return False

    def get_index(self,domains):
        '''
            @name 获取标识
            @author hwliang<2022-02-10>
            @param domains<list> 域名列表
            @return string
        '''
        identifiers = []
        for domain_name in domains:
            identifiers.append({"type": 'dns', "value": domain_name})
        return public.md5(json.dumps(identifiers))


    # 续签同品牌其它证书
    def renew_cert_other(self):
        '''
            @name 续签同品牌其它证书
            @author hwliang<2022-02-10>
            @return void
        '''
        cert_path = "{}/vhost/cert".format(public.get_panel_path())
        if not os.path.exists(cert_path): return
        new_time = time.time() + (86400 * 30)
        n=0
        if not 'orders' in self._config: self._config['orders'] = {}
        import panelSite
        siteObj = panelSite.panelSite()
        args = public.dict_obj()
        for siteName in os.listdir(cert_path):
            try:
                cert_file = '{}/{}/fullchain.pem'.format(cert_path,siteName)
                if not os.path.exists(cert_file): continue # 无证书文件
                siteInfo = public.M('sites').where('name=?',siteName).find()
                if not siteInfo: continue # 无网站信息
                cert_init = self.get_cert_init(cert_file)
                if not cert_init: continue # 无法获取证书
                end_time = time.mktime(time.strptime(cert_init['notAfter'],'%Y-%m-%d'))
                if end_time > new_time: continue # 未到期
                try:
                    if not cert_init['issuer'] in ['R3',"Let's Encrypt"] and cert_init['issuer'].find("Let's Encrypt") == -1 and cert_init.get('issuer_O', "") != "Let's Encrypt":
                        continue # 非同品牌证书
                except: continue

                if isinstance(cert_init['dns'],str): cert_init['dns'] = [cert_init['dns']]
                index = self.get_index(cert_init['dns'])
                if index in self._config['orders'].keys(): continue # 已在订单列表

                n+=1
                write_log("|-正在续签第 {} 张其它证书，域名: {}..".format(n,cert_init['subject']))
                write_log("|-正在创建订单..")
                args.id = siteInfo['id']
                runPath = siteObj.GetRunPath(args)
                if runPath and not runPath in ['/']:
                    path = siteInfo['path'] + '/' + runPath
                else:
                    path = siteInfo['path']

                self.renew_cert_to(cert_init['dns'],'http',path.replace('//','/'))
            except:
                write_log("|-[{}]续签失败".format(siteName))

    # 关闭强制https
    def close_httptohttps(self,siteName):
        try:

            if not siteName: siteName
            import panelSite
            site_obj = panelSite.panelSite()
            if not site_obj.IsToHttps(siteName):
                return False
            get = public.dict_obj()
            get.siteName = siteName
            site_obj.CloseToHttps(get)
            return True
        except:
            return False

    # 恢复强制https
    def rep_httptohttps(self,siteName):
        try:
            if not siteName: return False
            import panelSite
            site_obj = panelSite.panelSite()
            if not site_obj.IsToHttps(siteName):
                get = public.dict_obj()
                get.siteName = siteName
                site_obj.HttpToHttps(get)
            return True
        except:
            return False


    def renew_cert_to(self,domains,auth_type,auth_to,index = None):
        siteName = None
        cert = {}
        if os.path.exists(auth_to):
            if public.M('sites').where('path=?',auth_to).count() == 1:
                site_id = public.M('sites').where('path=?',auth_to).getField('id')
                siteName = public.M('sites').where('path=?',auth_to).getField('name')
                r_status = public.M('sites').where('path=?',auth_to).getField('status')
                if r_status != '1':
                    write_log("|- 该证书使用了【文件验证】方式,但网站【{}】未启动，只能跳过续签。".format(siteName))
                    return public.returnMsg(False, "该证书使用了【文件验证】方式,但网站【{}】未启动，只能跳过续签。".format(siteName))
                import panelSite
                siteObj = panelSite.panelSite()
                args = public.dict_obj()
                args.id = site_id
                runPath = siteObj.GetRunPath(args)
                if runPath and not runPath in ['/']:
                    path = auth_to + '/' + runPath
                    if os.path.exists(path): auth_to = path.replace('//','/')

            else:
                siteName, _ = self.get_site_name_by_domains(domains)

            isError = public.checkWebConfig()
            if isError is not True and public.get_webserver() == "nginx":
                write_log("|- 该证书使用了【文件验证】方式,但目前无法重载nginx服务器配置文件，只能跳过续签。")
                write_log("|- 配置文件报错信息如下：")
                write_log(isError)

        is_rep = self.close_httptohttps(siteName)
        try:
            index = self.create_order(
                domains,
                auth_type,
                auth_to.replace('//','/'),
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

            # 清理失败重试记录
            self._config['orders'][index]['retry_count'] = 0
            self._config['orders'][index]['next_retry_time'] = 0

            # 保存证书配置
            self.save_config()
            cert['status'] = True
            cert['msg'] = '续签成功!'
            write_log("|-续签成功!")
        except Exception as e:

            if str(e).find('请稍候重试') == -1: # 受其它证书影响和连接CA失败的的不记录重试次数
                if index:
                    # 设置下次重试时间
                    self._config['orders'][index]['next_retry_time'] = int(time.time() + (86400 * 2))
                    # 记录重试次数
                    if not 'retry_count' in self._config['orders'][index].keys():
                        self._config['orders'][index]['retry_count'] = 1
                    self._config['orders'][index]['retry_count'] += 1
                    # 保存证书配置
                    self.save_config()
            e = str(e)
            if e.find(">>>>") != -1:
                msg = e.split(">>>>")[0]
                err = json.loads(e.split(">>>>")[1])
            else:
                msg = e
                err = {}
            write_log("|-" + msg)
            return {"status": False, "msg": msg, "err": err}
        finally:
            if is_rep: self.rep_httptohttps(siteName)
        write_log("-" * 70)
        return cert

    def set_auto_renew_status(self, index, status, error_msg=''):
        """
        @name 设置自动续签状态
        @param index:
        @param status:
        @param error_msg:
        @return:
        """
        path = "{}/config/letsencrypt_auto_renew.json".format(public.get_panel_path())
        try:
            data = json.loads(public.readFile(path))
            data[index] = {"status": status, "error_msg": error_msg}
        except:
            data = {index: {"status": status, "error_msg": error_msg}}
        public.writeFile(path, json.dumps(data))


    # 续签证书
    def renew_cert(self, index, cycle=None):
        write_log("", "wb+")
        set_status = False
        index_info = None
        try:
            order_index = []
            if index:
                set_status = True
                if type(index) != str:
                    index = index.index
                if not index in self._config['orders']:
                    write_log("|-指定订单号不存在，无法续签!")
                    self.set_auto_renew_status(index, -1, "指定订单号不存在，无法续签!")
                    raise Exception("指定订单号不存在，无法续签!")
                if cycle:
                    s_time = time.time() + (int(cycle) * 86400)
                    if self._config['orders'][index]['cert_timeout'] > s_time:
                        self.set_auto_renew_status(index, 0, "|-过期时间大于{}天，跳过续签!".format(cycle))
                        write_log("|-过期时间大于{}天，跳过续签!".format(cycle))
                        return
                order_index.append(index)
            else:
                s_time = time.time() + (30 * 86400)
                if not 'orders' in self._config: self._config['orders'] = {}
                for i in self._config['orders'].keys():
                    if not 'save_path' in self._config['orders'][i]:
                        continue
                    if 'cert' in self._config['orders'][i]:
                        self._config['orders'][i]['cert_timeout'] = self._config['orders'][i]['cert']['cert_timeout']
                    if not 'cert_timeout' in self._config['orders'][i]:
                        self._config['orders'][i]['cert_timeout'] = int(time.time())
                    if self._config['orders'][i]['cert_timeout'] > s_time:
                        continue

                    # 已删除的网站直接跳过续签
                    # is_file_check = (self._config['orders'][i]['auth_to'].find('|') == -1 or
                    #                  not self._config['orders'][i]['auth_to'].startswith("dns")
                    #                 ) and self._config['orders'][i]['auth_to'].find('/') != -1
                    # if is_file_check:
                        # if not os.path.exists(self._config['orders'][i]['auth_to']):
                        # ^^^^^^^^^^——————————这个不能判断网站已被删除的情况下，文件夹未删除时的问题
                    # _auth_to = self.get_ssl_used_site(self._config['orders'][i]['save_path'])
                    _auth_to = self.get_ssl_used_site(i)
                    if not _auth_to:
                        continue

                    # 域名不存在？
                    for domain in self._config['orders'][i]['domains']:
                        if domain.find('*') != -1:
                            break
                        if not public.M('domain').where("name=?",(domain,)).count() and not public.M('binding').where("domain=?",domain).count():
                            _auth_to = None
                            write_log("|-跳过被删除的域名: {}".format(self._config['orders'][i]['domains']))
                    if not _auth_to: continue
                    self._config['orders'][i]['auth_to'] = _auth_to

                    # 是否到了允许重试的时间
                    if 'next_retry_time' in self._config['orders'][i]:
                        timeout = self._config['orders'][i]['next_retry_time'] - int(time.time())
                        if timeout > 0:
                            write_log('|-本次跳过域名:{}，因第上次续签失败，还需要等待{}小时后再重试'.format(self._config['orders'][i]['domains'],int(timeout / 60 / 60)))
                            continue

                    # # 是否到了最大重试次数
                    # if 'retry_count' in self._config['orders'][i]:
                    #     if self._config['orders'][i]['retry_count'] >= 5:
                    #         write_log('|-本次跳过域名:{}，因连续5次续签失败，不再续签此证书(可尝试手动续签此证书，成功后错误次数将被重置)'.format(self._config['orders'][i]['domains']))
                    #         continue

                    # 加入到续签订单
                    order_index.append(i)
            if not order_index:
                write_log("|-没有找到30天内到期的SSL证书，正在尝试去寻找其它可续签证书!")
                self.get_apis()
                self.renew_cert_other()
                write_log("|-所有任务已处理完成!")
                return
            write_log("|-共需要续签 {} 张证书".format(len(order_index)))
            n = 0
            self.get_apis()
            cert = None
            for index in order_index:
                n += 1
                domains = _test_domains(self._config['orders'][index]['domains'], self._config['orders'][index]['auth_to'],self._config['orders'][index]['auth_type'])
                if len(domains) == 0:
                    write_log("|-第 {} 张证书下的域名全部未使用(这些域名是:[{}])，已跳过。".format(n, ",".join(self._config['orders'][index]['domains'])))
                    err_msg = "域名全部未使用，已跳过。"
                    if set_status:
                        self.set_auto_renew_status(index, -1, err_msg)
                    continue
                else:
                    index_info = self._config['orders'][index]
                    self._config['orders'][index]['domains'] = domains
                    write_log("|-正在续签第 {} 张，域名: {}..".format(n,self._config['orders'][index]['domains']))
                    write_log("|-正在创建订单..")
                    cert = self.renew_cert_to(self._config['orders'][index]['domains'],self._config['orders'][index]['auth_type'],self._config['orders'][index]['auth_to'],index)
                    err_msg = "续签失败!"
            if not cert:
                return public.returnMsg(False, err_msg)
            if cert.get('status') is False and set_status:
                self.set_auto_renew_status(index, -1, cert.get('msg'))
                self._config['orders'][index] = index_info
                self.save_config()
            if (cert.get('status') is None or cert.get('status') is True) and set_status:
                self.set_auto_renew_status(index, 1, "续签成功!")
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
            if set_status:
                self.set_auto_renew_status(index, -1, msg)
            if index_info:
                self._config['orders'][index] = index_info
                self.save_config()
            return public.returnMsg(False, msg)

    def renew_cert_v2(self, index, cycle):
        if index:
            hash_list = [index]
        else:
            # 获取所有网站证书
            from sslModel import certModel
            certModel = certModel.main()
            use_cert_list = certModel.get_cert_to_site(True)
            hash_list = use_cert_list.keys()
        s = 0
        from sslModel import base
        dns_data = base.sslBase().get_dns_data(None)
        for ssl_hash in hash_list:
            s += 1
            write_log("|-正在续签第 {} 张证书，共 {} 张..".format(s, len(hash_list)))
            cert_data = public.M('ssl_info').where('hash=?', ssl_hash).find()
            if not cert_data:
                write_log("|-【{}】没有找到指定证书信息，无法续签!".format(ssl_hash))
                continue
            # 借用ps字段，记录证书续签状态
            if cert_data['ps'] == "renewed":
                write_log("|-【{}】证书已续签，无需续签!".format(ssl_hash))
                continue
            try:
                cert_info = json.loads(cert_data['info'])
            except:
                write_log(public.get_error_info())
                write_log("|-【{}】证书信息格式错误，无法续签，请尝试手动续签!".format(ssl_hash))
                continue
            if cert_info.get('issuer') not in ("R3", "R8", "R11", "R10", "R5") and cert_info.get('issuer_O') != "Let's Encrypt":
                write_log("|-【{}】不是Let's Encrypt证书，无法续签!".format(ssl_hash))
                continue
            # 计算 30 天后的日期
            if cycle:
                cycle = int(cycle)
                # 计算 30 天后的日期
                future_date = (datetime.datetime.now().date() + datetime.timedelta(days=cycle)).strftime('%Y-%m-%d')
                if future_date < cert_info['notAfter']:
                    write_log("|-【{}】到期时间大于{}天，无需续签!".format(ssl_hash, cycle))
                    continue
            else:
                try:
                    notBefore = datetime.datetime.strptime(cert_info['notBefore'][:10], "%Y-%m-%d").timestamp()
                    notAfter = datetime.datetime.strptime(cert_info['notAfter'][:10], "%Y-%m-%d").timestamp()
                except Exception as e:
                    write_log("|-【{}】证书时间格式错误，无法续签，请尝试手动续签!".format(ssl_hash))
                    write_log(public.get_error_info())
                    continue
                total_time = notAfter - notBefore
                if total_time >= 90 * 86400:
                    renew_time = notAfter - (30 * 86400)
                else:
                    renew_time = notAfter - (total_time / 3)

                if renew_time > time.time():
                    write_log("|-【{}】未到续签时间，下次续签：{}".format(ssl_hash, time.strftime('%Y-%m-%d', time.localtime(renew_time))))
                    continue
            # 判断是否有泛域名
            wildcard = False
            if "*" in ",".join(cert_info['dns']):
                write_log("|-【{}】存在泛域名，只能用dns验证方式续签!".format(ssl_hash))
                wildcard = True
            # 判断是否绑定了dns-api
            auth_domains = []
            for i in cert_info['dns']:
                root_domain, _, _ = base.sslBase().extract_zone(i)
                root_domain_info = public.M('ssl_domains').where("domain=?", root_domain).find()
                if not root_domain_info or root_domain_info.get("dns_id") not in dns_data.keys():
                    write_log("|-根域名【{}】未绑定dns-api，跳过域名: {}!".format(root_domain, i))
                    continue
                auth_domains.append(i)
            if not auth_domains:
                write_log("|-【{}】域名全部未绑定dns-api，无法使用dns验证续签!".format(ssl_hash))
                dns_auth = False
                if wildcard:
                    continue
            else:
                dns_auth = True
            if set(auth_domains) == set(cert_info['dns']):
                write_log("|-【{}】全部域名已绑定dns-api，正在尝试使用dns验证续签!".format(ssl_hash))
                self.get_apis()
                cert = self.renew_cert_to(auth_domains, "dns", "dns-api")
                if cert.get('status') is False:
                    continue
                public.M('ssl_info').where('hash=?', ssl_hash).update({"ps": "renewed"})
                continue
            else:
                http_auth = False
                write_log("|-【{}】正在检测文件验证是否可用".format(ssl_hash))
                sites = {}
                for domain in cert_info['dns']:
                    domain_info = public.M('domain').where("name=?", domain).find()
                    if not domain_info:
                        write_log("|-域名【{}】不存在，跳过!".format(domain))
                        continue
                    if not sites.get(domain_info["pid"]):
                        sites[domain_info["pid"]] = [domain]
                    else:
                        sites[domain_info["pid"]].append(domain)
                if not sites:
                    write_log("|-【{}】没有找到可用的文件验证站点，请尝试手动续签!".format(ssl_hash))
                # 暂时不做多网站文件验证
                if len(sites.keys()) > 1:
                    write_log("|-【{}】检测到验证域名分散在多个站点，暂时不支持多个站点文件验证!".format(ssl_hash))
                for site_id, domains in sites.items():
                    site_info = public.M('sites').where("id=?", site_id).find()
                    if not site_info:
                        write_log("|-站点【{}】不存在，跳过!".format(site_id))
                        break
                    if set(domains) == set(cert_info['dns']) or len(domains) > len(auth_domains):
                        http_auth = True
                        break
            if http_auth:
                write_log("|-【{}】正在尝试使用文件验证续签!".format(ssl_hash))
                self.get_apis()
                cert = self.renew_cert_to(domains, "http", site_info['path'])
                if cert.get('status') is False:
                    continue
                public.M('ssl_info').where('hash=?', ssl_hash).update({"ps": "renewed"})
                continue
            elif dns_auth:
                write_log("|-【{}】正在尝试使用dns验证续签!".format(ssl_hash))
                self.get_apis()
                cert = self.renew_cert_to(auth_domains, "dns", "dns-api")
                if cert.get('status') is False:
                    continue
                public.M('ssl_info').where('hash=?', ssl_hash).update({"ps": "renewed"})
                continue
            else:
                write_log("|-【{}】没有找到可用的验证方式，请尝试手动续签!".format(ssl_hash))
                continue
        return

    def get_order_list(self, get):
        """
        获取订单列表
        """
        self.get_exclude_hash(get)
        data = self.read_config()
        if not data.get('orders'):
            return []

        del_list = []
        _return = []

        orders = list(data['orders'].values())
        for i in range(len(orders) - 1, -1, -1):
            if orders[i]['status'] == "valid" and (not orders[i].get("save_path") or not orders[i].get("cert_timeout")):
                del_list.append(orders[i]['index'])
                del orders[i]
                continue
            if orders[i]['status'] == "valid":
                orders[i]['expires'] = orders[i]['cert_timeout']
            if orders[i]['status'] == "ready":
                orders[i]['status'] = "pending"
            try:
                end_time = int(
                    (orders[i]['expires'] - datetime.datetime.today().timestamp()) / (60 * 60 * 24)
                )
            except Exception as e:
                end_time = 90
            orders[i]['endDay'] = end_time
        try:
            arg = public.to_dict_obj({"index": ",".join(del_list), "d": "1"})
            self.delete_order(arg)
        except:
            pass
        return orders

    def get_order_detail(self, get):
        """
        订单详情
        """
        order_index = get.index
        orders = self.read_config()

        data = orders["orders"].get(order_index)

        if not data:
            return public.returnMsg(False, "没有找到此订单信息")
        if not data.get('auths'):
            if not data.get('authorizations'):
                return public.ReturnMsg(False, "订单验证信息丢失，请尝试重新申请!")
            try:
                self.get_apis()
                data['auths'] = []
                for auth_url in data['authorizations']:
                    res = self.acme_request(auth_url, "")
                    if res.status_code not in [200, 201]:
                        return public.ReturnMsg(False, "订单验证信息丢失，请尝试重新申请!")
                    s_body = res.json()
                    identifier_auth = self.get_identifier_auth(order_index, auth_url, s_body)
                    acme_keyauthorization, auth_value = self.get_keyauthorization(
                        identifier_auth['token'])
                    identifier_auth['acme_keyauthorization'] = acme_keyauthorization
                    identifier_auth['auth_value'] = auth_value
                    identifier_auth['expires'] = s_body['expires']
                    identifier_auth['auth_to'] = self._config['orders'][order_index]['auth_to']
                    identifier_auth['type'] = self._config['orders'][order_index]['auth_type']
                    data['auths'].append(identifier_auth)
                self.save_config()
            except:
                return public.ReturnMsg(False, "订单验证信息丢失，请尝试重新申请!")

        endtime = ((data.get('expires', 0) or 0) - datetime.datetime.today().timestamp()) / (60 * 60 * 24)
        if endtime <= 0:
            return public.ReturnMsg(False, "订单已过期，请重新申请!")

        _return = {"auths": []}
        if data['auth_type'] == 'dns':
            auth_domains = [i["domain"].replace("*.", "") for i in data['auths']]
            if len(auth_domains) != len(set(auth_domains)):
                _return["error"] = True
                _return["error_msg"] = "检测到解析记录存在冲突，请分别验证以下域名"

            for auth in data['auths']:
                domain = auth['domain']
                domains = auth['domain'].split('.')
                if domains[0] == '*':
                    domain = ".".join(domains[1:])
                _return["auths"].append({
                    "domain": auth['domain'],
                    "status": auth.get('status', "pending"),
                    "data": [{
                        "domain": "_acme-challenge.{}".format(domain),
                        "auth_value": auth["auth_value"],
                        "type": "TXT",
                        "must": "是"
                    }, {
                        "domain": domain,
                        "auth_value": '0 issue "letsencrypt.org"',
                        "type": "CAA",
                        "must": "否"
                    }]
                })
            return _return
        else:
            for auth in data['auths']:
                domain = auth['domain']
                _return["auths"].append({
                    "domain": domain,
                    "data": [{
                        "domain": auth['domain'],
                        "file_path": "{}.well-known/acme-challenge/{}".format(auth['auth_to'], auth['token']),
                        "content": auth['acme_keyauthorization'],
                        "must": "是"
                    }]
                })
            return _return

    def validate_domain(self, get):
        order_index = get.index

        data = self.read_config()
        data = data["orders"].get(order_index)

        if not data:
            return public.returnMsg(False, "没有找到此订单信息")
        if not data.get('auths'):
            return public.ReturnMsg(False, "订单验证信息丢失，请尝试重新申请!")
        endtime = ((data.get('expires', 0) or 0) - datetime.datetime.today().timestamp()) / (60 * 60 * 24)
        if endtime <= 0:
            return public.ReturnMsg(False, "订单已过期，请重新申请!")
        # for auth in data['auths']:
        #     self.set_auth_info(auth, order_index)
        return self.apply_cert([], "dns", "dns", index=order_index)

    def delete_order(self, get):
        return self._delete_order(get)["finish_list"][0]

    def _delete_order(self, get):
        from sslModel import certModel
        certModel = certModel.main()
        if ('index' not in get or not get.index) and ('ssl_hash' not in get or not get.ssl_hash):
            return {'status': False, 'msg': "缺少必填参数", 'finish_list': []}
        # 强制删除已经部署的证书
        force = False
        if hasattr(get, 'force'):
            force = get.force
        local = True if 'local' not in get else get.local
        cloud = True if 'cloud' not in get else get.cloud

        path = '{}/data/exclude_hash.json'.format(public.get_panel_path())
        exclude_data = self.get_exclude_hash(get)

        # 组合删除数据
        del_data = []
        if 'index' in get and get.index:
            index_list = get.index.split(',')
            for index in index_list:
                ssl_hash = exclude_data.get("exclude_hash_let", {}).get(index)
                del_data.append({"index": index, "ssl_hash": ssl_hash})
        if 'ssl_hash' in get and get.ssl_hash:
            ssl_hash_list = get.ssl_hash.split(',')
            for ssl_hash in ssl_hash_list:
                append_data = {"index": "", "ssl_hash": ssl_hash}
                for index, value in exclude_data.get("exclude_hash_let", {}).items():
                    if value == ssl_hash:
                        append_data["index"] = index
                        break
                del_data.append(append_data)

        data = self.read_config()
        finish_list = []
        for d in del_data:
            finish = {"name": "let's Encrypt", "status": True, "msg": "删除成功"}
            local_err = ""
            order_err = ""
            # 删除本地证书
            if d['ssl_hash']:
                try:
                    certModel.remove_cert(ssl_hash=d['ssl_hash'], local=local, cloud=cloud, force=force)
                except Exception as e:
                    local_err = str(e)
            # 删除订单
            if d['index'] and d['index'] in data['orders'] and local:
                try:
                    if d['index'] in exclude_data["exclude_hash_let"]:
                        del exclude_data["exclude_hash_let"][d['index']]
                    del data['orders'][d['index']]
                except Exception as e:
                    order_err = str(e)
            if local_err:
                finish["status"] = False
                finish["msg"] = "本地证书删除失败: {}".format(local_err)
            if order_err:
                finish["status"] = False
                if finish["msg"] == "删除成功":
                    finish["msg"] = "订单删除失败: {}".format(order_err)
                else:
                    finish["msg"] += "；订单删除失败: {}".format(order_err)

            finish_list.append(finish)

        public.writeFile(path, json.dumps(exclude_data))
        public.writeFile(self._conf_file_v2, json.dumps(data))
        if 'd' in get:
            return data
        return {'status': True, 'msg': "删除成功", 'finish_list': finish_list}

    def download_cert_to_local(self, get):
        index = get.index

        orders = self.read_config()
        order = orders['orders'].get(index)
        if not order:
            return public.returnMsg(False, "下载失败，未找到此订单")

        exclude_data = self.get_exclude_hash(get)

        ssl_hash = exclude_data.get("exclude_hash_let", {}).get(index)
        if not ssl_hash:
            return public.returnMsg(False, "订单未完成或订单信息有误，下载失败")
        from sslModel import certModel
        return certModel.main().download_cert(public.to_dict_obj({"ssl_hash": ssl_hash}))

    def SetCertToSite(self,get):
        import panelSSL
        exclude_data = self.get_exclude_hash(get)
        ssl_hash = exclude_data['exclude_hash_let'].get(get.index)
        if not ssl_hash:
            return public.returnMsg(False, "未找到此证书")
        get.ssl_hash = ssl_hash
        return panelSSL.panelSSL().SetCertToSite(get)



def _test_domains(domains, auth_to, auth_type):
    # 检查站点域名变更情况， 若有删除域名，则在续签时，删除已经不使用的域名，再执行续签任务
    # 是dns验证的跳过
    if auth_to.find("|") != -1 or auth_to.startswith("dns#@"):
        return domains
    # 是泛域名的跳过
    for domain in domains:
        if domain.find("*.") != -1:
            return domains
    sql = public.M('domain')
    site_sql = public.M('sites')
    for domain in domains:
        pid = sql.where('name=?', domain).getField('pid')
        if pid and site_sql.where('id=?',pid).find():
            site_domains = [i["name"] for i in sql.where('pid=?',(pid,)).field("name").select()]
            break
    else:
        site_id = site_sql.where('path=?', auth_to).getField('id')
        if bool(site_id) and str(site_id).isdigit():
            site_domains = [i["name"] for i in sql.where('pid=?',(site_id,)).field("name").select()]
        else:
            # 全都查询不到，认为这个站点已经被删除
            return []

    del_domains = list(set(domains) - set(site_domains))
    for i in del_domains:
        domains.remove(i)
    return domains


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

# todo：兼容控制台，目前不兼容
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
    p.add_argument('--renew_v2', default=None, help="续签证书v2", dest="renew_v2")
    p.add_argument('--revoke', default=None, help="吊销证书", dest="revoke")
    p.add_argument('--cycle', default=None, help="到期时间小于等于时续签", dest="cycle")
    args = p.parse_args()
    cert = None
    if args.revoke:
        if not args.index:
            echo_err("请在--index参数中传入要被吊销的订单索引")
        p = acme_v2()
        result = p.revoke_order(args.index)
        write_log(result)
        exit()

    if args.renew_v2:
        sys.path.append(public.get_panel_path())
        p = acme_v2()
        if args.cycle:
            try:
                int(args.cycle)
            except:
                args.cycle = None
        p.renew_cert_v2(args.index, args.cycle)
        exit()

    if args.renew:
        sys.path.append(public.get_panel_path())
        p = acme_v2()
        if args.cycle:
            try:
                int(args.cycle)
            except:
                args.cycle = None
        p.renew_cert(args.index, args.cycle)
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
