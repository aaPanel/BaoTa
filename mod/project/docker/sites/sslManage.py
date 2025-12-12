# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------
# ------------------------------
# docker模型 - docker runtime 业务类
# ------------------------------
import os
import re
import sys
import json
import shutil
import datetime
import binascii
import fcntl
import time
import base64
import uuid
import hashlib

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
if not 'class/' in sys.path:
    sys.path.insert(0, 'class/')
import http_requests as requests

import public
import ssl_info
try:
    import OpenSSL
except:
    public.ExecShell("btpip install pyopenssl")
    import OpenSSL

from btdockerModel import dk_public as dp
from mod.project.docker.sites.base import Sites

# 写日志
def write_log(log_str, mode="ab+"):
    if __name__ == "__main__":
        return
    _log_file = 'logs/letsencrypt.log'
    f = open(_log_file, mode)
    log_str += "\n"
    f.write(log_str.encode('utf-8'))
    f.close()
    return True


class SslManage(Sites):
    nginx_conf_bak = '/tmp/backup_nginx.conf'

    def __init__(self):
        super().__init__()
        self.setupPath = public.get_setup_path()
        self._is_nginx_http3 = None
        self.is_ipv6 = os.path.exists(self.setupPath + '/panel/data/ipv6.pl')
        if os.path.exists(self.nginx_conf_bak): os.remove(self.nginx_conf_bak)

    def _get_ap_static_security(self, ap_conf):
        if not ap_conf: return ''
        ap_static_security = re.search('#SECURITY-START(.|\n)*#SECURITY-END', ap_conf)
        if ap_static_security:
            return ap_static_security.group()
        return ''

    # 获取TLS1.3标记
    def get_tls13(self):
        nginx_bin = '/www/server/nginx/sbin/nginx'
        nginx_v = public.ExecShell(nginx_bin + ' -V 2>&1')[0]
        nginx_v_re = re.findall("nginx/(\d\.\d+).+OpenSSL\s+(\d\.\d+)", nginx_v, re.DOTALL)
        if nginx_v_re:
            if nginx_v_re[0][0] in ['1.8', '1.9', '1.7', '1.6', '1.5', '1.4']:
                return ''
            if float(nginx_v_re[0][0]) >= 1.15 and float(nginx_v_re[0][-1]) >= 1.1:
                return ' TLSv1.3'
        else:
            _v = re.search('nginx/1\.1(5|6|7|8|9).\d', nginx_v)
            if not _v:
                _v = re.search('nginx/1\.2\d\.\d', nginx_v)
            openssl_v = public.ExecShell(nginx_bin + ' -V 2>&1|grep OpenSSL')[0].find('OpenSSL 1.1.') != -1
            if _v and openssl_v:
                return ' TLSv1.3'
        return ''

    @staticmethod
    def get_tls_protocol(tls1_3: str = "TLSv1.3", is_apache=False):
        """获取使用的协议
        @author baozi <202-04-18>
        @param:
        @return
        """
        protocols = {
            "TLSv1": False,
            "TLSv1.1": True,
            "TLSv1.2": True,
            "TLSv1.3": False,
        }
        file_path = public.get_panel_path() + "/data/ssl_protocol.json"
        if os.path.exists(file_path):
            data = public.readFile(file_path)
            if data is not False:
                protocols = json.loads(data)
                if protocols["TLSv1.3"] and tls1_3 == "":
                    protocols["TLSv1.3"] = False
                if is_apache is False:
                    return " ".join([p for p, v in protocols.items() if v is True])
                else:
                    return " ".join(["-" + p for p, v in protocols.items() if v is False])
        else:
            if tls1_3 != "":
                protocols["TLSv1.3"] = True
            if is_apache is False:
                return " ".join([p for p, v in protocols.items() if v is True])
            else:
                return " ".join(["-" + p for p, v in protocols.items() if v is False])

    def analyze_ssl(self, csr):
        issuer_dic = {}
        try:
            from cryptography import x509
            from cryptography.hazmat.backends import default_backend
            cert = x509.load_pem_x509_certificate(csr.encode("utf-8"), default_backend())
            issuer = cert.issuer
            for i in issuer:
                issuer_dic[i.oid._name] = i.value
        except:
            pass
        return issuer_dic

    def is_nginx_http3(self):
        if getattr(self, "_is_nginx_http3", None) is None:
            _is_nginx_http3 = public.ExecShell("nginx -V 2>&1| grep 'http_v3_module'")[0] != ''
            setattr(self, "_is_nginx_http3", _is_nginx_http3)
        return self._is_nginx_http3

    # 2024/11/8 10:31 给指定网站设置SSL
    def set_ssl_to_site(self, get):
        '''
            @name 给指定网站设置SSL
        '''
        # 解析证书
        get.key = get.key.strip()
        get.csr = get.csr.strip()

        issuer = self.analyze_ssl(get.csr)
        if issuer.get("organizationName") == "Let's Encrypt":
            get.csr += "\n"

        siteName = get.siteName
        path = '/www/server/panel/vhost/cert/' + siteName
        csrpath = path + "/fullchain.pem"
        keypath = path + "/privkey.pem"

        if (get.key.find('KEY') == -1): return public.returnResult(False, 'SITE_SSL_ERR_PRIVATE')
        if (get.csr.find('CERTIFICATE') == -1): return public.returnResult(False, 'SITE_SSL_ERR_CERT')
        public.writeFile('/tmp/cert.pl', get.csr)
        if not public.CheckCert('/tmp/cert.pl'): return public.returnResult(False, '证书错误,请粘贴正确的PEM格式证书!')
        backup_cert = '/tmp/backup_cert_' + siteName

        import shutil
        if os.path.exists(backup_cert): shutil.rmtree(backup_cert)
        if os.path.exists(path): shutil.move(path, backup_cert)
        if os.path.exists(path): shutil.rmtree(path)

        public.ExecShell('mkdir -p ' + path)
        public.writeFile(keypath, get.key)
        public.writeFile(csrpath, get.csr)

        # 写入配置文件
        result = self.SetSSLConf(get)
        if not result['status']: return result
        isError = public.checkWebConfig()

        if (type(isError) == str):
            if os.path.exists(path):
                shutil.rmtree(path)
            if os.path.exists(backup_cert):
                shutil.move(backup_cert, path)
            return public.returnResult(False, 'ERROR: <br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')
        public.serviceReload()

        if os.path.exists(path + '/partnerOrderId'): os.remove(path + '/partnerOrderId')
        if os.path.exists(path + '/certOrderId'): os.remove(path + '/certOrderId')
        p_file = '/etc/letsencrypt/live/' + get.siteName
        if os.path.exists(p_file): shutil.rmtree(p_file)
        public.WriteLog('TYPE_SITE', 'SITE_SSL_SAVE_SUCCESS')

        # 清理备份证书
        if os.path.exists(backup_cert): shutil.rmtree(backup_cert)
        return public.returnResult(True, '证书已保存!')

    def save_cert(self, get):
        # try:
        import panelSSL
        ss = panelSSL.panelSSL()
        get.keyPath = '/www/server/panel/vhost/cert/' + get.siteName + '/privkey.pem'
        get.certPath = '/www/server/panel/vhost/cert/' + get.siteName + '/fullchain.pem'
        return ss.SaveCert(get)

    # 添加SSL配置
    def SetSSLConf(self, get):
        """
        @name 兼容批量设置
        @auther hezhihong
        """
        siteName = get.siteName
        if not 'first_domain' in get: get.first_domain = siteName
        if 'isBatch' in get and siteName != get.first_domain: get.first_domain = siteName

        # Nginx配置
        file = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'

        # Node项目
        if not os.path.exists(file):  file = self.setupPath + '/panel/vhost/nginx/node_' + siteName + '.conf'
        if not os.path.exists(file):  file = self.setupPath + '/panel/vhost/nginx/java_' + siteName + '.conf'
        if not os.path.exists(file):  file = self.setupPath + '/panel/vhost/nginx/go_' + siteName + '.conf'
        if not os.path.exists(file):  file = self.setupPath + '/panel/vhost/nginx/other_' + siteName + '.conf'
        if not os.path.exists(file):  file = self.setupPath + '/panel/vhost/nginx/python_' + siteName + '.conf'
        if not os.path.exists(file):  file = self.setupPath + '/panel/vhost/nginx/net_' + siteName + '.conf'
        if not os.path.exists(file):  file = self.setupPath + '/panel/vhost/nginx/html_' + siteName + '.conf'
        ng_file = file
        ng_conf = public.readFile(file)
        have_nginx_conf = ng_conf is not False

        # 是否为子目录设置SSL
        # if hasattr(get,'binding'):
        #    allconf = conf;
        #    conf = re.search("#BINDING-"+get.binding+"-START(.|\n)*#BINDING-"+get.binding+"-END",conf).group()

        if ng_conf:
            if ng_conf.find('ssl_certificate') == -1:
                http3_header = '''\n    add_header Alt-Svc 'quic=":443"; h3=":443"; h3-29=":443"; h3-27=":443";h3-25=":443"; h3-T050=":443"; h3-Q050=":443";h3-Q049=":443";h3-Q048=":443"; h3-Q046=":443"; h3-Q043=":443"';'''
                if not self.is_nginx_http3():
                    http3_header = ""
                sslStr = """#error_page 404/404.html;
    ssl_certificate    /www/server/panel/vhost/cert/%s/fullchain.pem;
    ssl_certificate_key    /www/server/panel/vhost/cert/%s/privkey.pem;
    ssl_protocols %s;
    ssl_ciphers EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_tickets on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    add_header Strict-Transport-Security "max-age=31536000";%s
    error_page 497  https://$host$request_uri;
""" % (get.first_domain, get.first_domain, self.get_tls_protocol(self.get_tls13(), is_apache=False), http3_header)
                if (ng_conf.find('ssl_certificate') != -1):
                    if 'isBatch' not in get:
                        public.serviceReload()
                        return public.returnResult(True, 'SITE_SSL_OPEN_SUCCESS')
                    else:
                        return True

                if ng_conf.find('#error_page 404/404.html;') == -1:
                    return public.returnResult(False, "站点配置文件中未找到标识信息【#error_page 404/404.html;】，"
                                                   "无法确定SSL配置添加位置，请尝试手动添加标识或恢复配置文件")

                ng_conf = ng_conf.replace('#error_page 404/404.html;', sslStr)
                conf = re.sub(r"\s+\#SSL\-END", "\n\t\t#SSL-END", ng_conf)

                # 添加端口
                rep = "listen.*[\s:]+(\d+).*;"
                tmp = re.findall(rep, ng_conf)
                if not public.inArray(tmp, '443'):
                    listen_re = re.search(rep, ng_conf)
                    if not listen_re:
                        ng_conf = re.sub(r"server\s*{\s*", "server\n{\n\t\tlisten 80;\n\t\t", ng_conf)
                        listen_re = re.search(rep, ng_conf)
                    listen = listen_re.group()
                    nginx_ver = public.nginx_version()
                    default_site = ''
                    if ng_conf.find('default_server') != -1:
                        default_site = ' default_server'

                    listen_add_str = []
                    if nginx_ver:
                        port_str = ["443"]
                        if self.is_ipv6:
                            port_str.append("[::]:443")
                        use_http2_on = False
                        for p in port_str:
                            listen_add_str.append("\n    listen {} ssl".format(p))
                            if nginx_ver < [1, 9, 5]:
                                listen_add_str.append(default_site + ";")
                            elif [1, 9, 5] <= nginx_ver < [1, 25, 1]:
                                listen_add_str.append(" http2 " + default_site + ";")
                            else:  # >= [1, 25, 1]
                                listen_add_str.append(default_site + ";")
                                use_http2_on = True

                            if self.is_nginx_http3():
                                listen_add_str.append("\n    listen {} quic;".format(p))
                        if use_http2_on:
                            listen_add_str.append("\n    http2 on;")

                    else:
                        listen_add_str.append("\n    listen 443 ssl " + default_site + ";")
                    listen_add_str_data = "".join(listen_add_str)
                    ng_conf = ng_conf.replace(listen, listen + listen_add_str_data)

        if ng_conf:  # 因为未查明原因，Apache配置过程中会删除掉nginx备份文件（估计是重复调用了本类中的init操作导致的）
            shutil.copyfile(ng_file, self.nginx_conf_bak)
            public.writeFile(ng_file, ng_conf)

        http2https_pl = "{}/data/http2https.pl".format(public.get_panel_path())
        if os.path.exists(http2https_pl):
            self.CloseToHttps(public.to_dict_obj({'siteName': siteName}), without_reload=True)
            # 尝试设置 http2https，并暂时重启，等到后续测试配置后，在重启
            self.HttpToHttps(public.to_dict_obj({'siteName': siteName}), without_reload=True)

        isError = public.checkWebConfig()
        if (isError != True):
            if os.path.exists(self.nginx_conf_bak): shutil.copyfile(self.nginx_conf_bak, ng_file)
            public.ExecShell("rm -f /tmp/backup_*.conf")
            return public.returnResult(False,
                                    '证书错误: <br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')

        sql = public.M('firewall')
        import firewalls
        get.port = '443'
        get.ps = 'HTTPS'
        if 'isBatch' not in get: firewalls.firewalls().AddAcceptPort(get)
        if 'isBatch' not in get: public.serviceReload()
        self.save_cert(get)
        public.WriteLog('TYPE_SITE', 'SITE_SSL_OPEN_SUCCESS', (siteName,))
        result = public.returnResult(True, 'SSL开启成功!')
        result['csr'] = public.readFile('/www/server/panel/vhost/cert/' + get.siteName + '/fullchain.pem')
        result['key'] = public.readFile('/www/server/panel/vhost/cert/' + get.siteName + '/privkey.pem')
        if 'isBatch' not in get:
            return result
        else:
            return public.returnResult()

    # 清理SSL配置
    def CloseSSLConf(self, get):
        siteName = get.siteName
        file = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        conf = public.readFile(file)
        if conf:
            rep = "\n\s*#HTTP_TO_HTTPS_START(.|\n){1,300}#HTTP_TO_HTTPS_END"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_certificate\s+.+;\s+ssl_certificate_key\s+.+;"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_protocols\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_ciphers\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_prefer_server_ciphers\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_session_cache\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_session_timeout\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_ecdh_curve\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_session_tickets\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_stapling\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_stapling_verify\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+add_header\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+add_header\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl\s+on;"
            conf = re.sub(rep, '', conf)
            rep = "\s+error_page\s497.+;"
            conf = re.sub(rep, '', conf)
            rep = "\s+if.+server_port.+\n.+\n\s+\s*}"
            conf = re.sub(rep, '', conf)
            rep = "\s+listen\s+443.*;"
            conf = re.sub(rep, '', conf)
            rep = "\s+listen\s+\[::\]:443.*;"
            conf = re.sub(rep, '', conf)
            rep = "\s+http2\s+on;"
            conf = re.sub(rep, '', conf)
            public.writeFile(file, conf)

        public.WriteLog('TYPE_SITE', 'SITE_SSL_CLOSE_SUCCESS', (siteName,))
        public.serviceReload()
        return public.returnResult(True, 'SSL已关闭!')

    #部署指定商业证书
    def set_cert(self,get):
        if not hasattr(get,'siteName'):
                return public.returnResult(False,'缺少参数siteName')
        siteName = get.siteName
        from panelSSL import panelSSL
        ssl_obj = panelSSL()
        certInfo = ssl_obj.get_order_find(get)
        path = '/www/server/panel/vhost/cert/' + siteName
        if not os.path.exists(path):
            public.ExecShell('mkdir -p ' + path)
        csrpath = path+"/fullchain.pem"
        keypath = path+"/privkey.pem"
        pidpath = path+"/certOrderId"

        other_file = path + '/partnerOrderId'
        if os.path.exists(other_file): os.remove(other_file)
        other_file = path + '/README'
        if os.path.exists(other_file): os.remove(other_file)

        public.writeFile(keypath,certInfo['privateKey'])
        public.writeFile(csrpath,certInfo['certificate']+"\n"+certInfo['caCertificate'])
        public.writeFile(pidpath,get.oid)
        self.SetSSLConf(get)
        public.serviceReload()
        get.csr = certInfo['certificate']+"\n"+certInfo['caCertificate']
        ssl_obj.set_exclude_hash(get)
        return public.returnResult(True,'设置成功')

    def SetBatchCertToSite(self,get):
        """
        @name 批量部署证书
        @auther hezhihong
        """
        ssl_list=[]
        if not hasattr(get,'BatchInfo') or not get.BatchInfo:return public.returnMsg(False,'参数错误')
        else:
            ssl_list=json.loads(get.BatchInfo)
        if isinstance(ssl_list, list):
            total_num = len(ssl_list)
            resultinfo = {"total":total_num,"success": 0, "faild": 0,"successList":[],"faildList":[]}
            successList = []
            faildList=[]
            successnum=0
            failnum=0
            for Info in ssl_list:
                set_result={}
                set_result['status']=True
                get.certName =set_result['certName']= Info['certName']
                get.siteName =set_result['siteName']= str(Info['siteName'])  # 站点名称必定为字符串
                get.isBatch=True
                if "ssl_hash" in Info:
                    get.ssl_hash=Info['ssl_hash']
                result=self.SetCertToSite(get)
                if not result or (isinstance(result, dict) and not result['status']):
                    set_result['status']=False
                    failnum+=1
                    set_result["error_msg"] = ''
                    if isinstance(result, dict) and 'msg' in result:
                        set_result["error_msg"] = result['msg']
                    faildList.append(set_result)
                else:
                    successnum+=1
                    successList.append(set_result)
                public.writeSpeed('setssl', successnum+failnum, total_num)
            import firewalls
            get.port = '443'
            get.ps = 'HTTPS'
            firewalls.firewalls().AddAcceptPort(get)
            public.serviceReload()
            resultinfo['success']=successnum
            resultinfo['faild']= failnum
            resultinfo['successList']=  successList
            resultinfo['faildList']=  faildList

            if hasattr(get, "set_https_mode") and get.set_https_mode.strip() in (True, 1, "1", "true"):
                import panelSite
                sites_obj = panelSite.panelSite()
                if not sites_obj.get_https_mode():
                    sites_obj.set_https_mode()

        else:return public.returnMsg(False,'参数类型错误')
        return resultinfo

    #读取证书
    def GetCert(self,get):
        if "ssl_hash" in get:
            from ssl_manage import SSLManger
            return SSLManger.get_cert_for_deploy(get.ssl_hash.strip())
        vpath = os.path.join('/www/server/panel/vhost/ssl' , get.certName.replace("*.",''))
        if not os.path.exists(vpath): return public.returnMsg(False,'证书不存在!')
        data = {}
        data['privkey'] = public.readFile(vpath + '/privkey.pem')
        data['fullchain'] = public.readFile(vpath + '/fullchain.pem')
        return data

    #部署证书夹证书
    def SetCertToSite(self,get):
        """
        @name 兼容批量部署
        @auther hezhihong
        """

        try:
            result = self.GetCert(get)
            if not 'privkey' in result: return result
            siteName = get.siteName
            path = '/www/server/panel/vhost/cert/' + siteName
            if not os.path.exists(path):
                public.ExecShell('mkdir -p ' + path)
            csrpath = path+"/fullchain.pem"
            keypath = path+"/privkey.pem"

            #清理旧的证书链
            public.ExecShell('rm -f ' + keypath)
            public.ExecShell('rm -f ' + csrpath)
            public.ExecShell('rm -rf ' + path + '-00*')
            public.ExecShell('rm -rf /etc/letsencrypt/archive/' + get.siteName)
            public.ExecShell('rm -rf /etc/letsencrypt/archive/' + get.siteName + '-00*')
            public.ExecShell('rm -f /etc/letsencrypt/renewal/'+ get.siteName + '.conf')
            public.ExecShell('rm -f /etc/letsencrypt/renewal/'+ get.siteName + '-00*.conf')
            public.ExecShell('rm -f ' + path + '/README')
            if os.path.exists(path + '/certOrderId'): os.remove(path + '/certOrderId')

            public.writeFile(keypath,result['privkey'])
            public.writeFile(csrpath,result['fullchain'])
            return self.SetSSLConf(get)
        except Exception as ex:
            if 'isBatch' in get:return False
            return public.returnMsg(False,'SET_ERROR,' + public.get_error_info())

    # HttpToHttps
    def HttpToHttps(self, get, without_reload=False):
        siteName = get.siteName
        # Nginx配置
        file = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        conf = public.readFile(file)
        if conf:
            if conf.find('ssl_certificate') == -1: return public.returnMsg(False, '当前未开启SSL')
            to = """#error_page 404/404.html;
    #HTTP_TO_HTTPS_START
    set $isRedcert 1;
    if ($server_port != 443) {
        set $isRedcert 2;
    }
    if ( $uri ~ /\.well-known/ ) {
        set $isRedcert 1;
    }
    if ($isRedcert != 1) {
        rewrite ^(/.*)$ https://$host$1 permanent;
    }
    #HTTP_TO_HTTPS_END"""
            conf = conf.replace('#error_page 404/404.html;', to)
            public.writeFile(file, conf)
        if not without_reload:
            public.serviceReload()
        return public.returnMsg(True, 'SET_SUCCESS')

    # CloseToHttps
    def CloseToHttps(self, get, without_reload=False):
        siteName = get.siteName
        file = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        conf = public.readFile(file)
        if conf:
            rep = "\n\s*#HTTP_TO_HTTPS_START(.|\n){1,300}#HTTP_TO_HTTPS_END"
            conf = re.sub(rep, '', conf)
            rep = "\s+if.+server_port.+\n.+\n\s+\s*}"
            conf = re.sub(rep, '', conf)
            public.writeFile(file, conf)
        if not without_reload:
            public.serviceReload()
        return public.returnMsg(True, 'SET_SUCCESS')


class Acme_V2(Sites):
    _url = None
    _config = {}
    _auto_wildcard = False
    _apis = None
    _dns_class = None
    _mod_index = {True: "Staging", False: "Production"}
    _debug = False
    _conf_file_v2 = 'config/letsencrypt_v2.json'
    _request_type = 'curl'
    _user_agent = "BaoTa/1.0 (+https://www.bt.cn)"
    _replay_nonce = None
    _acme_timeout = 30
    _verify = False
    _dnsapi_file = 'config/dns_api.json'
    _dns_domains = []
    _wait_time = 5
    _max_check_num = 15
    _bits = 2048
    _digest = "sha256"
    _save_path = 'vhost/letsencrypt'

    def __init__(self):
        super().__init__()
        self._can_use_lua = None
        self._nginx_cache_file_auth = {}
        self._well_known_check_cache = {}
        if self._debug:
            self._url = 'https://acme-staging-v02.api.letsencrypt.org/directory'
        else:
            self._url = 'https://acme-v02.api.letsencrypt.org/directory'


    # 返回配置文件是否支持使用普通的文件验证
    @staticmethod
    def can_use_base_file_check(site_name: str, site_type: str):
        ng_file = "{}/nginx/{}.conf".format(public.get_vhost_path(), site_name)
        ng_data = public.readFile(ng_file)
        if not ng_data:
            return False
        rep_well_known = re.compile(r"location\s+([=~^]*\s*)?/?\\?\.well-known/?\s*{")
        if rep_well_known.search(ng_data):
            return True
        else:
            return False

    # 返回是否能通过lua 做了文件验证处理， 如果返回True，则表示可以处理了验证文件， 不再走之前的 if 验证方式
    def can_use_lua_for_site(self, site_name: str):
        if self._can_use_lua is None:
            # 查询lua_module 不为空
            self._can_use_lua = public.ExecShell("nginx -V 2>&1 |grep lua_nginx_module")[0].strip() != ''

        if not self._can_use_lua:
            return False

        ng_file = "{}/nginx/{}.conf".format(public.get_vhost_path(), site_name)
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
    def can_use_if_for_file_check(site_name: str):
        # if 方式的文件验证必须是可重载的情况
        if public.checkWebConfig() is not True:
            return False

        ng_file = "{}/nginx/{}.conf".format(public.get_vhost_path(), site_name)
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

    # 检查认证环境
    def check_auth_env(self,args):
        for domain in json.loads(args.domains):
            if public.checkIp(domain): continue
            if domain.find('*.') != -1 and args.auth_type in ['http','tls']:
                return public.returnMsg(False, '泛域名不能使用【文件验证】的方式申请证书!')

        data = public.M('docker_sites').where('id=?', (args.id,)).find()
        if not data:
            return public.returnMsg(False, "网站丢失，无法继续申请证书")
        else:
            args.siteName = data['name']

        use_nginx_conf_to_auth = False
        if args.auth_type in ['http', 'tls'] and public.get_webserver() == "nginx":  # nginx 在lua验证和可重启的
            if self.can_use_lua_for_site(args.siteName):
                use_nginx_conf_to_auth = True
            else:
                if self.can_use_if_for_file_check(args.siteName):
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

    # 写配置文件
    def save_ssl_config(self):
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
            self.save_ssl_config()
            return self._config
        tmp_config = public.readFile(self._conf_file_v2)
        if not tmp_config:
            return self._config
        try:
            self._config = json.loads(tmp_config)
        except:
            self.save_ssl_config()
            return self._config
        return self._config

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
            self.save_ssl_config()
        return self._apis

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

    # 转为无填充的Base64
    def calculate_safe_base64(self, un_encoded_data):
        if sys.version_info[0] == 3:
            if isinstance(un_encoded_data, str):
                un_encoded_data = un_encoded_data.encode("utf8")
        r = base64.urlsafe_b64encode(un_encoded_data).rstrip(b"=")
        return r.decode("utf8")

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

    # 创建Key
    def create_key(self, key_type=OpenSSL.crypto.TYPE_RSA):
        key = OpenSSL.crypto.PKey()
        key.generate_key(key_type, self._bits)
        private_key = OpenSSL.crypto.dump_privatekey(
            OpenSSL.crypto.FILETYPE_PEM, key)
        return private_key

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
            self.save_ssl_config()
        return self._config['account'][k]['key']

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
            self.save_ssl_config()
            time.sleep(3)
            self._config = self.read_config()
        return self._config['account'][k]['kid']

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

    # 计算signature
    def sign_message(self, message):
        pk = OpenSSL.crypto.load_privatekey(
            OpenSSL.crypto.FILETYPE_PEM, self.get_account_key().encode())
        return OpenSSL.crypto.sign(pk, message.encode("utf8"), self._digest)

    # 更新随机数
    def update_replay_nonce(self, res):
        replay_nonce = res.headers.get('Replay-Nonce')
        if replay_nonce:
            self._replay_nonce = replay_nonce

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
        import acme_v2
        signature = acme_v2.acme_v2().sign_message(
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
            return '签发失败,该域名%s超出了每周的重复签发次数限制!' % re.findall("exact set of domains: (.+):",
                                                                                 error)
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
            return "域名%s没有找到解析记录，请检查域名是否解析生效!" % re.findall(
                "No valid IP addresses found for (.+)", error)
        elif error.find('No TXT record found at') != -1:
            return "没有在域名%s中找到有效的TXT解析记录,请检查是否正确解析TXT记录,如果是DNSAPI方式申请的,请10分钟后重试!" % re.findall(
                "No TXT record found at (.+)", error)
        elif error.find('Incorrect TXT record') != -1:
            return "在%s上发现错误的TXT记录:%s,请检查TXT解析是否正确,如果是DNSAPI方式申请的,请10分钟后重试!" % (
            re.findall("found at (.+)", error), re.findall("Incorrect TXT record \"(.+)\"", error))
        elif error.find('Domain not under you or your user') != -1:
            return "这个dnspod账户下面不存在这个域名，添加解析失败!"
        elif error.find('SERVFAIL looking up TXT for') != -1:
            return "没有在域名%s中找到有效的TXT解析记录,请检查是否正确解析TXT记录,如果是DNSAPI方式申请的,请10分钟后重试!" % re.findall(
                "looking up TXT for (.+)", error)
        elif error.find('Timeout during connect') != -1:
            return "连接超时,CA服务器无法访问您的网站!"
        elif error.find("DNS problem: SERVFAIL looking up CAA for") != -1:
            return "域名%s当前被要求验证CAA记录，请手动解析CAA记录，或1小时后重新尝试申请!" % re.findall(
                "looking up CAA for (.+)", error)
        elif error.find("Read timed out.") != -1:
            return "验证超时,请检查域名是否正确解析，若已正确解析，可能服务器与Let'sEncrypt连接异常，请稍候再重试!"
        elif error.find("The ACME server can not issue a certificate for an IP address") != -1:
            return "不能使用IP地址申请证书!"
        elif error.find('Cannot issue for') != -1:
            return "无法为{}颁发证书，不能直接用域名后缀申请通配符证书!".format(re.findall(r'for\s+"(.+)"', error))
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
        self.save_ssl_config()
        return index

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
        find_result = dp.sql("docker_sites").where("id=?", (site_id,)).find()
        if not find_result: return None
        site_path = find_result['path']
        if not os.path.exists(site_path): return None
        run_path = find_result['run_path']
        if run_path in ['/']: run_path = ''
        if run_path:
            if run_path[0] == '/': run_path = run_path[1:]
        site_run_path = os.path.join(site_path, run_path)
        if not os.path.exists(site_run_path): return site_path
        return site_run_path

    def get_site_run_path(self,domains):
        '''
            @name 通过域名列表获取网站运行目录
            @author hwliang
            @param domains<list> 域名列表
            @return None or string
        '''
        site_id = 0
        for domain in domains:
            site_id = dp.sql("docker_domain").where("name=?", (domain,)).getField('pid')
            if site_id:
                break

        if not site_id: return None
        return self.get_site_run_path_byid(site_id)

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

    #从云端验证域名是否可访问
    def cloud_check_domain(self,domain):
        try:
            result = requests.post('https://www.bt.cn/api/panel/check_domain',{"domain":domain,"ssl":1},s_type=self._request_type).json()
            return result['status']
        except: return False

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

    def can_use_lua_module(self):
        if self._can_use_lua is None:
            # 查询lua_module 不为空
            self._can_use_lua = public.ExecShell("nginx -V 2>&1 |grep lua_nginx_module")[0].strip() != ''
        return self._can_use_lua

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
            raise Exception("写入验证文件失败: {}".format(err))

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

    def check_auths_config(self, index, key, value) -> bool:
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
        self.save_ssl_config()
        if not self.check_auths_config(index, "auths", auths):
            self.save_ssl_config()
        return auths

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

    # 发送验证请求
    def respond_to_challenge(self, auth):
        payload = {"keyAuthorization": "{0}".format(
            auth['acme_keyauthorization'])}
        respond_to_challenge_response = self.acme_request(
            auth['dns_challenge_url'], payload)
        return respond_to_challenge_response

    # 验证域名
    def auth_domain(self, index):
        if index not in self._config['orders']:
            raise Exception('指定订单不存在!')

        if "auths" not in self._config['orders'][index]:
            raise Exception('订单验证信息丢失，请尝试重新申请!')

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

    # 构造可选名称
    def get_alt_names(self, index):
        domain_name = self._config['orders'][index]['domains'][0]
        domain_alt_names = []
        if len(self._config['orders'][index]['domains']) > 1:
            domain_alt_names = self._config['orders'][index]['domains'][1:]
        return domain_name, domain_alt_names

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
        self.save_ssl_config()
        return private_key

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
        self.save_ssl_config()
        return certificate_url

    # 拆分根证书
    def split_ca_data(self,cert):
        sp_key = '-----END CERTIFICATE-----\n'
        datas = cert.split(sp_key)
        return {"cert": datas[0] + sp_key, "root": sp_key.join(datas[1:])}

    # 获取证书到期时间
    def get_cert_timeout(self, cret_data):

        info = ssl_info.ssl_info().load_ssl_info_by_data(cret_data)
        if not info:
            return int(time.time() + (86400 * 90))

        try:
            return public.to_date(times=info['notAfter'])
        except:
            return int(time.time() + (86400 * 90))

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

    # 获取指定证书基本信息
    def get_cert_init(self, pem_file):
        return ssl_info.ssl_info().load_ssl_info(pem_file)

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
            public.writeFile(path + '/说明.txt', ps)
            self.sub_all_cert(key_file, pem_file)
        except:
            write_log(public.get_error_info())

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
        self.save_ssl_config()
        self.save_cert(cert, index)
        return cert

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
                import traceback
                msg = traceback.format_exc()
                write_log(public.get_error_info())
            return public.returnMsg(False, msg)

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
            return public.returnMsg(False, '网站id不能为空!')

        if 'auto_wildcard' in args and args.auto_wildcard == '1':
            self._auto_wildcard = True

        find = public.M('docker_sites').where('id=?', (args.id,)).find()
        if not find:
            return public.returnMsg(False, "网站丢失，无法继续申请证书")

        if re.match(r"^\d+$", args.auth_to):
            import panelSite
            args.auth_to = find['path'] + '/' + panelSite.panelSite().GetRunPath(args)
            args.auth_to = args.auth_to.replace("//", "/")
            if args.auth_to[-1] == '/':
                args.auth_to = args.auth_to[:-1]

            if not os.path.exists(args.auth_to):
                return public.returnMsg(False, '无效的站点目录，请检查指定站点是否存在!')

        # 检查认证环境
        check_result = self.check_auth_env(args)
        if check_result: return check_result

        return self.apply_cert(json.loads(args.domains), args.auth_type, args.auth_to)

    # DNS手动验证
    def apply_dns_auth(self, args):
        if not hasattr(args, "index") or not args.index:
            return public.returnMsg(False, "参数信息不完整，没有索引参数【index】")
        return self.apply_cert([], auth_type='dns', auth_to='dns', index=args.index)