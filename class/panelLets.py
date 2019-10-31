#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 曹觉心 <314866873@qq.com>
# +-------------------------------------------------------------------
import os,sys,json,time,re
setup_path = '/www/server/panel'
os.chdir(setup_path)
sys.path.append("class/")
import requests,sewer,public
from OpenSSL import crypto
try:
    requests.packages.urllib3.disable_warnings()
except:pass
if __name__ != '__main__':
    import BTPanel
try:
    import dns.resolver
except:
    os.system("pip install dnspython")
    try:
        import dns.resolver
    except:
        pass

class panelLets:
    let_url = "https://acme-v02.api.letsencrypt.org/directory"
    #let_url = "https://acme-staging-v02.api.letsencrypt.org/directory"

    setupPath = None #安装路径  
    server_type = None
    
    #构造方法
    def __init__(self):
        self.setupPath = public.GetConfigValue('setup_path')
        self.server_type = public.get_webserver()

    
    #拆分根证书
    def split_ca_data(self,cert):
        datas = cert.split('-----END CERTIFICATE-----')
        return {"cert":datas[0] + "-----END CERTIFICATE-----\n","ca_data":datas[1] + '-----END CERTIFICATE-----\n' }

    #证书转为pkcs12
    def dump_pkcs12(self,key_pem=None,cert_pem = None, ca_pem=None, friendly_name=None):
        p12 = crypto.PKCS12()
        if cert_pem:
            ret = p12.set_certificate(crypto.load_certificate(crypto.FILETYPE_PEM, cert_pem.encode()))
            assert ret is None
        if key_pem:
            ret = p12.set_privatekey(crypto.load_privatekey(crypto.FILETYPE_PEM, key_pem.encode()))
            assert ret is None
        if ca_pem:
            ret = p12.set_ca_certificates((crypto.load_certificate(crypto.FILETYPE_PEM, ca_pem.encode()),) )
        if friendly_name:
            ret = p12.set_friendlyname(friendly_name.encode())
        return p12

    def extract_zone(self,domain_name):
        domain_name = domain_name.lstrip("*.")
        top_domain_list = ['.ac.cn', '.ah.cn', '.bj.cn', '.com.cn', '.cq.cn', '.fj.cn', '.gd.cn', 
                            '.gov.cn', '.gs.cn', '.gx.cn', '.gz.cn', '.ha.cn', '.hb.cn', '.he.cn', 
                            '.hi.cn', '.hk.cn', '.hl.cn', '.hn.cn', '.jl.cn', '.js.cn', '.jx.cn', 
                            '.ln.cn', '.mo.cn', '.net.cn', '.nm.cn', '.nx.cn', '.org.cn']
        old_domain_name = domain_name
        m_count = domain_name.count(".")
        top_domain = "."+".".join(domain_name.rsplit('.')[-2:])
        new_top_domain = "." + top_domain.replace(".","")
        is_tow_top = False
        if top_domain in top_domain_list:
            is_tow_top = True
            domain_name = domain_name[:-len(top_domain)] + new_top_domain

        if domain_name.count(".") > 1:
            zone, middle, last = domain_name.rsplit(".", 2)        
            acme_txt = "_acme-challenge.%s" % zone
            if is_tow_top: last = top_domain[1:]
            root = ".".join([middle, last])
        else:
            zone = ""
            root = old_domain_name
            acme_txt = "_acme-challenge"
        return root, zone, acme_txt

    #获取根域名
    def get_root_domain(self,domain_name):
        d_root,tow_name,acme_txt = self.extract_zone(domain_name)
        return d_root
    
    #获取acmename
    def get_acme_name(self,domain_name):
        d_root,tow_name,acme_txt = self.extract_zone(domain_name)
        return acme_txt + '.' + d_root

    #格式化错误输出
    def get_error(self,error):
        if error.find("Max checks allowed") >= 0 :
            return "CA无法验证您的域名，请检查域名解析是否正确，或等待5-10分钟后重试."
        elif error.find("Max retries exceeded with") >= 0:
            return "CA服务器连接超时，请稍候重试."
        elif error.find("The domain name belongs") >= 0:
            return "域名不属于此DNS服务商，请确保域名填写正确."
        elif error.find('login token ID is invalid') >=0:
            return 'DNS服务器连接失败，请检查密钥是否正确.'
        elif "too many certificates already issued for exact set of domains" in error:
            return '签发失败,该域名%s超出了每周的重复签发次数限制!' % re.findall("exact set of domains: (.+):",error)
        elif "Error creating new account :: too many registrations for this IP" in error:
            return '签发失败,当前服务器IP已达到每3小时最多创建10个帐户的限制.'
        elif "DNS problem: NXDOMAIN looking up A for" in error:
            return '验证失败,没有解析域名,或解析未生效!'
        elif "Invalid response from" in error:
            return '验证失败,域名解析错误或验证URL无法被访问!'
        elif error.find('TLS Web Server Authentication') != -1:
            public.restart_panel()
            return "连接CA服务器失败，请稍候重试."
        elif error.find('Name does not end in a public suffix') !=-1:
            return "不支持的域名%s，请检查域名是否正确!" % re.findall("Cannot issue for \"(.+)\":",error)
        elif error.find('No valid IP addresses found for') != -1:
            return "域名%s没有找到解析记录，请检查域名是否解析生效!" % re.findall("No valid IP addresses found for (.+)",error)
        elif error.find('No TXT record found at') != -1:
            return "没有在域名%s中找到有效的TXT解析记录,请检查是否正确解析TXT记录,如果是DNSAPI方式申请的,请10分钟后重试!" % re.findall("No TXT record found at (.+)",error)
        elif error.find('Incorrect TXT record') != -1:
            return "在%s上发现错误的TXT记录:%s,请检查TXT解析是否正确,如果是DNSAPI方式申请的,请10分钟后重试!" % (re.findall("found at (.+)",error),re.findall("Incorrect TXT record \"(.+)\"",error))
        elif error.find('Domain not under you or your user') != -1:
            return "这个dnspod账户下面不存在这个域名，添加解析失败!"
        elif error.find('SERVFAIL looking up TXT for') != -1:
            return "没有在域名%s中找到有效的TXT解析记录,请检查是否正确解析TXT记录,如果是DNSAPI方式申请的,请10分钟后重试!" % re.findall("looking up TXT for (.+)",error)
        elif error.find('Timeout during connect') != -1:
            return "连接超时,CA服务器无法访问您的网站!"
        elif error.find("DNS problem: SERVFAIL looking up CAA for") != -1:
            return "域名%s当前被要求验证CAA记录，请手动解析CAA记录，或1小时后重新尝试申请!" % re.findall("looking up CAA for (.+)",error)
        elif error.find("Read timed out.") != -1:
            return "验证超时,请检查域名是否正确解析，若已正确解析，可能服务器与Let'sEncrypt连接异常，请稍候再重试!"
        elif error.find("Error creating new order") != -1:
            return "订单创建失败，请稍候重试!"
        else:
            return error;

    #获取DNS服务器
    def get_dns_class(self,data):
        if data['dnsapi'] == 'dns_ali':
            import panelDnsapi
            public.mod_reload(panelDnsapi)
            dns_class = panelDnsapi.AliyunDns(key = data['dns_param'][0], secret = data['dns_param'][1])
            return dns_class
        elif data['dnsapi'] == 'dns_dp':
            dns_class = sewer.DNSPodDns(DNSPOD_ID = data['dns_param'][0] ,DNSPOD_API_KEY = data['dns_param'][1])
            return dns_class
        elif data['dnsapi'] == 'dns_cx':   
            import panelDnsapi
            public.mod_reload(panelDnsapi)
            dns_class = panelDnsapi.CloudxnsDns(key = data['dns_param'][0] ,secret =data['dns_param'][1])
            result = dns_class.get_domain_list()
            if result['code'] == 1:                
                return dns_class
        elif data['dnsapi'] == 'dns_bt':
            import panelDnsapi
            public.mod_reload(panelDnsapi)
            dns_class = panelDnsapi.Dns_com()
            return dns_class
        return False

    #续签证书
    def renew_lest_cert(self,data):  
        #续签网站
        path = self.setupPath + '/panel/vhost/cert/'+ data['siteName'];
        if not os.path.exists(path):  return public.returnMsg(False, '续签失败,证书目录不存在.') 

        account_path = path + "/account_key.key"
        if not os.path.exists(account_path): return public.returnMsg(False, '续签失败,缺少account_key.') 

        #续签
        data['account_key'] = public.readFile(account_path)

        if not 'first_domain' in data:  data['first_domain'] = data['domains'][0]

        if 'dnsapi' in data:                
            certificate = self.crate_let_by_dns(data)
        else:            
            certificate = self.crate_let_by_file(data)       

        if not certificate['status']: return public.returnMsg(False, certificate['msg'])
                 
        #存储证书
        public.writeFile(path + "/privkey.pem",certificate['key'])
        public.writeFile(path + "/fullchain.pem",certificate['cert'] + certificate['ca_data'])
        public.writeFile(path + "/account_key.key", certificate['account_key']) #续签KEY

        #转为IIS证书
        p12 = self.dump_pkcs12(certificate['key'], certificate['cert'] + certificate['ca_data'],certificate['ca_data'],data['first_domain'])
        pfx_buffer = p12.export()
        public.writeFile(path + "/fullchain.pfx",pfx_buffer,'wb+')
         
        return public.returnMsg(True, '[%s]证书续签成功.' % data['siteName'])



    #申请证书
    def apple_lest_cert(self,get):
   
        data = {}        
        data['siteName'] = get.siteName
        data['domains'] = json.loads(get.domains)
        data['email'] = get.email
        data['dnssleep'] = get.dnssleep
             
        if len(data['domains']) <=0 : return public.returnMsg(False, '申请域名列表不能为空.')
        
        data['first_domain'] = data['domains'][0]       
     
        path = self.setupPath + '/panel/vhost/cert/'+ data['siteName'];
        if not os.path.exists(path): os.makedirs(path)

        # 检查是否自定义证书
        partnerOrderId = path + '/partnerOrderId';
        if os.path.exists(partnerOrderId): os.remove(partnerOrderId)
        #清理续签key
        re_key = path + '/account_key.key';
        if os.path.exists(re_key): os.remove(re_key)

        re_password = path + '/password';
        if os.path.exists(re_password): os.remove(re_password)
        
        data['account_key'] = None   
        if hasattr(get, 'dnsapi'): 
            if not 'app_root' in get: get.app_root = '0'
            data['app_root'] = get.app_root   
            domain_list = data['domains']
            if data['app_root'] == '1':
                domain_list = []
                data['first_domain'] = self.get_root_domain(data['first_domain'])
                for domain in data['domains']:
                    rootDoamin = self.get_root_domain(domain)
                    if not rootDoamin in domain_list: domain_list.append(rootDoamin)
                    if not "*." + rootDoamin in domain_list: domain_list.append("*." + rootDoamin)
                data['domains'] = domain_list
            if get.dnsapi == 'dns':
                domain_path = path + '/domain_txt_dns_value.json'
                if hasattr(get, 'renew'): #验证
                    data['renew'] = True
                    dns = json.loads(public.readFile(domain_path))
                    data['dns'] = dns
                    certificate = self.crate_let_by_oper(data)
                else:
                    #手动解析提前返回
                    result = self.crate_let_by_oper(data)
                    if 'status' in result and not result['status']:  return result
                    result['status'] = True
                    public.writeFile(domain_path, json.dumps(result)) 
                    result['msg'] = '获取成功,请手动解析域名'
                    result['code'] = 2;
                    return result
            elif get.dnsapi == 'dns_bt':
                data['dnsapi'] = get.dnsapi
                certificate = self.crate_let_by_dns(data)
            else:
                data['dnsapi'] = get.dnsapi
                data['dns_param'] = get.dns_param.split('|')
                certificate = self.crate_let_by_dns(data)
        else:
            #文件验证
            data['site_dir'] = get.site_dir;     
            certificate = self.crate_let_by_file(data)       

        if not certificate['status']: return public.returnMsg(False, certificate['msg'])
        
        #保存续签
        cpath = self.setupPath + '/panel/vhost/cert/crontab.json'
        config = {}
        if os.path.exists(cpath):
            try:
                config = json.loads(public.readFile(cpath))
            except:pass

        config[data['siteName']] = data
        public.writeFile(cpath,json.dumps(config))
        public.set_mode(cpath,600)

        #存储证书
        public.writeFile(path + "/privkey.pem",certificate['key'])
        public.writeFile(path + "/fullchain.pem",certificate['cert'] + certificate['ca_data'])
        public.writeFile(path + "/account_key.key",certificate['account_key']) #续签KEY

        #转为IIS证书
        p12 = self.dump_pkcs12(certificate['key'], certificate['cert'] + certificate['ca_data'],certificate['ca_data'],data['first_domain'])
        pfx_buffer = p12.export()
        public.writeFile(path + "/fullchain.pfx",pfx_buffer,'wb+')        
        public.writeFile(path + "/README","let") 
        
        #计划任务续签
        self.set_crond()
        return public.returnMsg(True, '申请成功.')

    #创建计划任务
    def set_crond(self):
        try:
            echo = public.md5(public.md5('renew_lets_ssl_bt'))
            cron_id = public.M('crontab').where('echo=?',(echo,)).getField('id')

            import crontab
            args_obj = public.dict_obj()
            if not cron_id:
                cronPath = public.GetConfigValue('setup_path') + '/cron/' + echo
                shell = 'python %s/panel/class/panelLets.py renew_lets_ssl ' % (self.setupPath)
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

    #手动解析
    def crate_let_by_oper(self,data):
        result = {}
        result['status'] = False
        try:
            if not data['email']: data['email'] = public.M('users').getField('email')

            #手动解析记录值
            if not 'renew' in data:
                BTPanel.dns_client = sewer.Client(domain_name = data['first_domain'],dns_class = None,account_key = data['account_key'],domain_alt_names = data['domains'],contact_email = str(data['email']) ,ACME_AUTH_STATUS_WAIT_PERIOD = 15,ACME_AUTH_STATUS_MAX_CHECKS = 5,ACME_REQUEST_TIMEOUT = 20,ACME_DIRECTORY_URL = self.let_url)
                domain_dns_value = "placeholder"
                dns_names_to_delete = []

                BTPanel.dns_client.acme_register()
                authorizations, finalize_url = BTPanel.dns_client.apply_for_cert_issuance()
                responders = []
                for url in authorizations:
                    identifier_auth = BTPanel.dns_client.get_identifier_authorization(url)
                    authorization_url = identifier_auth["url"]
                    dns_name = identifier_auth["domain"]
                    dns_token = identifier_auth["dns_token"]
                    dns_challenge_url = identifier_auth["dns_challenge_url"]

                    acme_keyauthorization, domain_dns_value = BTPanel.dns_client.get_keyauthorization(dns_token)
                 
                    acme_name = self.get_acme_name(dns_name)
                    dns_names_to_delete.append({"dns_name": public.de_punycode(dns_name),"acme_name":acme_name, "domain_dns_value": domain_dns_value})
                    responders.append(
                        {
                            "authorization_url": authorization_url,
                            "acme_keyauthorization": acme_keyauthorization,
                            "dns_challenge_url": dns_challenge_url,
                        }
                    )
            
                dns = {}
                dns['dns_names'] = dns_names_to_delete
                dns['responders'] = responders
                dns['finalize_url'] = finalize_url
                return dns
            else:
                responders = data['dns']['responders']
                dns_names_to_delete = data['dns']['dns_names']
                finalize_url = data['dns']['finalize_url']
                for i in responders:  
                    auth_status_response = BTPanel.dns_client.check_authorization_status(i["authorization_url"])
                    if auth_status_response.json()["status"] == "pending":
                        BTPanel.dns_client.respond_to_challenge(i["acme_keyauthorization"], i["dns_challenge_url"])

                for i in responders:
                    BTPanel.dns_client.check_authorization_status(i["authorization_url"], ["valid","invalid"])

                certificate_url = BTPanel.dns_client.send_csr(finalize_url)
                certificate = BTPanel.dns_client.download_certificate(certificate_url)

                if certificate:
                    certificate = self.split_ca_data(certificate)
                    result['cert'] = certificate['cert']
                    result['ca_data'] = certificate['ca_data']
                    result['key'] = BTPanel.dns_client.certificate_key
                    result['account_key'] = BTPanel.dns_client.account_key
                    result['status'] = True
                    BTPanel.dns_client = None
                else:
                    result['msg'] = '证书获取失败，请稍后重试.'

        except Exception as e:
            res = str(e).split('>>>>')
            err = False
            try:
                err = json.loads(res[1])
            except: err = False
            result['msg'] =  [self.get_error(res[0]),err]

        return result

    #dns验证
    def crate_let_by_dns(self,data):
        dns_class = self.get_dns_class(data)
        if not dns_class: 
            return public.returnMsg(False, 'DNS连接失败，请检查密钥是否正确.')
     
        result = {}
        result['status'] = False
        try:
            log_level = "INFO"
            if data['account_key']: log_level = 'ERROR'
            if not data['email']: data['email'] = public.M('users').getField('email')
            client = sewer.Client(domain_name = data['first_domain'],domain_alt_names = data['domains'],account_key = data['account_key'],contact_email = str(data['email']),LOG_LEVEL = log_level,ACME_AUTH_STATUS_WAIT_PERIOD = 15,ACME_AUTH_STATUS_MAX_CHECKS = 5,ACME_REQUEST_TIMEOUT = 20, dns_class = dns_class,ACME_DIRECTORY_URL = self.let_url)
            domain_dns_value = "placeholder"
            dns_names_to_delete = []
            try:
                client.acme_register()
                authorizations, finalize_url = client.apply_for_cert_issuance()
                
                responders = []
                for url in authorizations:
                    identifier_auth = client.get_identifier_authorization(url)
                    authorization_url = identifier_auth["url"]
                    dns_name = identifier_auth["domain"]
                    dns_token = identifier_auth["dns_token"]
                    dns_challenge_url = identifier_auth["dns_challenge_url"]
                    acme_keyauthorization, domain_dns_value = client.get_keyauthorization(dns_token)
                    dns_class.create_dns_record(public.de_punycode(dns_name), domain_dns_value)
                    self.check_dns(self.get_acme_name(dns_name),domain_dns_value)
                    dns_names_to_delete.append({"dns_name": public.de_punycode(dns_name), "domain_dns_value": domain_dns_value})
                    responders.append({"authorization_url": authorization_url, "acme_keyauthorization": acme_keyauthorization,"dns_challenge_url": dns_challenge_url} )

                try:
                    for i in responders:
                        auth_status_response = client.check_authorization_status(i["authorization_url"])
                        r_data = auth_status_response.json()
                        if r_data["status"] == "pending":
                            client.respond_to_challenge(i["acme_keyauthorization"], i["dns_challenge_url"])

                    for i in responders: client.check_authorization_status(i["authorization_url"], ["valid","invalid"])
                except:
                    for i in responders:
                        auth_status_response = client.check_authorization_status(i["authorization_url"])
                        r_data = auth_status_response.json()
                        if r_data["status"] == "pending":
                            client.respond_to_challenge(i["acme_keyauthorization"], i["dns_challenge_url"])
                    for i in responders: client.check_authorization_status(i["authorization_url"], ["valid","invalid"])

                certificate_url = client.send_csr(finalize_url)
                certificate = client.download_certificate(certificate_url)
                if certificate:
                    certificate = self.split_ca_data(certificate)
                    result['cert'] = certificate['cert']
                    result['ca_data'] = certificate['ca_data']
                    result['key'] = client.certificate_key
                    result['account_key'] = client.account_key
                    result['status'] = True

            except Exception as e:
                raise e
            finally:   
                try:
                    for i in dns_names_to_delete: dns_class.delete_dns_record(i["dns_name"], i["domain_dns_value"])
                except :
                    pass

        except Exception as e:  
            try:
                for i in dns_names_to_delete: dns_class.delete_dns_record(i["dns_name"], i["domain_dns_value"])
            except:pass
            res = str(e).split('>>>>')
            err = False
            try:
                err = json.loads(res[1])
            except: err = False
            result['msg'] =  [self.get_error(res[0]),err]
        return result

    #文件验证
    def crate_let_by_file(self,data):
        result = {}
        result['status'] = False
        result['clecks'] = []
        try:
            log_level = "INFO"
            if data['account_key']: log_level = 'ERROR'
            if not data['email']: data['email'] = public.M('users').getField('email')
            client = sewer.Client(domain_name = data['first_domain'],dns_class = None,account_key = data['account_key'],domain_alt_names = data['domains'],contact_email = str(data['email']),LOG_LEVEL = log_level,ACME_AUTH_STATUS_WAIT_PERIOD = 15,ACME_AUTH_STATUS_MAX_CHECKS = 5,ACME_REQUEST_TIMEOUT = 20,ACME_DIRECTORY_URL = self.let_url)
            
            client.acme_register()
            authorizations, finalize_url = client.apply_for_cert_issuance()
            responders = []
            sucess_domains = []
            for url in authorizations:
                identifier_auth = self.get_identifier_authorization(client,url)
             
                authorization_url = identifier_auth["url"]
                http_name = identifier_auth["domain"]
                http_token = identifier_auth["http_token"]
                http_challenge_url = identifier_auth["http_challenge_url"]

                acme_keyauthorization, domain_http_value = client.get_keyauthorization(http_token)   
                acme_dir = '%s/.well-known/acme-challenge' % (data['site_dir']);
                if not os.path.exists(acme_dir): os.makedirs(acme_dir)
               
                #写入token
                wellknown_path = acme_dir + '/' + http_token               
                public.writeFile(wellknown_path,acme_keyauthorization)
                wellknown_url = "http://{0}/.well-known/acme-challenge/{1}".format(http_name, http_token)
                
                result['clecks'].append({'wellknown_url':wellknown_url,'http_token':http_token});
                is_check = False
                n = 0
                while n < 5:
                    print("wait_check_authorization_status")
                    try:                       
                        retkey = public.httpGet(wellknown_url,20)
                        if retkey == acme_keyauthorization:
                            is_check = True
                            break;
                    except :
                        pass
                    n += 1;
                    time.sleep(1)
                sucess_domains.append(http_name) 
                responders.append({"authorization_url": authorization_url, "acme_keyauthorization": acme_keyauthorization,"http_challenge_url": http_challenge_url})

            if len(sucess_domains) > 0: 
                #验证
                for i in responders:
                    auth_status_response = client.check_authorization_status(i["authorization_url"])
                    if auth_status_response.json()["status"] == "pending":
                        client.respond_to_challenge(i["acme_keyauthorization"], i["http_challenge_url"]).json()

                for i in responders:
                    client.check_authorization_status(i["authorization_url"], ["valid","invalid"])

                certificate_url = client.send_csr(finalize_url)
                certificate = client.download_certificate(certificate_url)
               
                if certificate:
                    certificate = self.split_ca_data(certificate)
                    result['cert'] = certificate['cert']
                    result['ca_data'] = certificate['ca_data']
                    result['key'] = client.certificate_key
                    result['account_key'] = client.account_key
                    result['status'] = True
                else:
                    result['msg'] = '证书获取失败，请稍后重试.'
            else:
                result['msg'] = "签发失败,我们无法验证您的域名:<p>1、检查域名是否绑定到对应站点</p><p>2、检查域名是否正确解析到本服务器,或解析还未完全生效</p><p>3、如果您的站点设置了反向代理,或使用了CDN,请先将其关闭</p><p>4、如果您的站点设置了301重定向,请先将其关闭</p><p>5、如果以上检查都确认没有问题，请尝试更换DNS服务商</p>'"
        except Exception as e:
            res = str(e).split('>>>>')
            err = False
            try:
                err = json.loads(res[1])
            except: err = False
            result['msg'] =  [self.get_error(res[0]),err]
        return result

    
    def get_identifier_authorization(self,client, url):
        
        headers = {"User-Agent": client.User_Agent}
        get_identifier_authorization_response = requests.get(url, timeout = client.ACME_REQUEST_TIMEOUT, headers=headers,verify=False)
       
        if get_identifier_authorization_response.status_code not in [200, 201]:
            raise ValueError("Error getting identifier authorization: status_code={status_code}".format(status_code=get_identifier_authorization_response.status_code ) )
        res = get_identifier_authorization_response.json()
        domain = res["identifier"]["value"]
        wildcard = res.get("wildcard")
        if wildcard:
            domain = "*." + domain

        for i in res["challenges"]:
            if i["type"] == "http-01":
                http_challenge = i
        http_token = http_challenge["token"]
        http_challenge_url = http_challenge["url"]
        identifier_auth = {
            "domain": domain,
            "url": url,
            "wildcard": wildcard,
            "http_token": http_token,
            "http_challenge_url": http_challenge_url,
        }
        return identifier_auth

    #检查DNS记录
    def check_dns(self,domain,value,type='TXT'):
        time.sleep(5)
        n = 0
        while n < 10:
            try:
                import dns.resolver
                ns = dns.resolver.query(domain,type)
                for j in ns.response.answer:
                    for i in j.items:
                        txt_value = i.to_text().replace('"','').strip()
                        if txt_value == value: 
                            print("验证成功：%s" % txt_value)
                            return True
            except:
                try:
                    import dns.resolver
                except:
                    return False
            n+=1
            time.sleep(5)
        return True
    
    #获取证书哈希
    def get_cert_data(self,path):
        try:
            if path[-4:] == '.pfx':   
                f = open(path,'rb') 
                pfx_buffer = f.read() 
                p12 = crypto.load_pkcs12(pfx_buffer,'')
                x509 = p12.get_certificate()
            else:
                cret_data = public.readFile(path)
                x509 = crypto.load_certificate(crypto.FILETYPE_PEM, cret_data)
            
            buffs = x509.digest('sha1')
            hash =  bytes.decode(buffs).replace(':','')
            data = {}
            data['hash'] = hash
            data['timeout'] = bytes.decode(x509.get_notAfter())[:-1]
            return data
        except :
            return False      


    #获取快过期的证书
    def get_renew_lets_bytimeout(self,cron_list):
        tday = 30
        path = self.setupPath + '/panel/vhost/cert'      
        nlist = {}
        new_list = {}
        for siteName in cron_list:   
            spath =  path + '/' + siteName
            #验证是否存在续签KEY
            if os.path.exists(spath + '/account_key.key'):
                if public.M('sites').where("name=?",(siteName,)).count():        
                    new_list[siteName] = cron_list[siteName]
                    data = self.get_cert_data(self.setupPath + '/panel/vhost/cert/' + siteName + '/fullchain.pem')                                     
                    timeout = int(time.mktime(time.strptime(data['timeout'],'%Y%m%d%H%M%S')))
                    eday = (timeout - int(time.time())) / 86400                
                    if eday < 30:                                     
                        nlist[siteName] = cron_list[siteName]
        #清理过期配置
        public.writeFile(self.setupPath + '/panel/vhost/cert/crontab.json',json.dumps(new_list))
        return nlist

    #===================================== 计划任务续订证书 =====================================#
    #续订
    def renew_lets_ssl(self):        
        cpath = self.setupPath + '/panel/vhost/cert/crontab.json'
        if not os.path.exists(cpath):  
            print("|-当前没有可以续订的证书. " );        
        else:
            old_list = json.loads(public.ReadFile(cpath))    
            print('=======================================================================')
            print('|-%s 共计[%s]续签证书任务.' % (time.strftime('%Y-%m-%d %X',time.localtime()),len(old_list)))                        
            cron_list = self.get_renew_lets_bytimeout(old_list)

            tlist = []
            for siteName in old_list:                 
                if not siteName in cron_list: tlist.append(siteName)
            print('|-[%s]未到期或网站未使用Let\'s Encrypt证书.' % (','.join(tlist)))
            print('|-%s 等待续签[%s].' % (time.strftime('%Y-%m-%d %X',time.localtime()),len(cron_list)))
            
            sucess_list  = []
            err_list = []
            for siteName in cron_list:
                data = cron_list[siteName]
                ret = self.renew_lest_cert(data)
                if ret['status']:
                    sucess_list.append(siteName)
                else:
                    err_list.append({"siteName":siteName,"msg":ret['msg']})
            print("|-任务执行完毕，共需续订[%s]，续订成功[%s]，续订失败[%s]. " % (len(cron_list),len(sucess_list),len(err_list)));        
            if len(sucess_list) > 0:       
                print("|-续订成功：%s" % (','.join(sucess_list)))
            if len(err_list) > 0:       
                print("|-续订失败：")
                for x in err_list:
                    print("    %s ->> %s" % (x['siteName'],x['msg']))

            print('=======================================================================')
            print(" ");

if __name__ == "__main__":
    if len(sys.argv) > 1:
        type = sys.argv[1]
        if type == 'renew_lets_ssl':
            panelLets().renew_lets_ssl()
