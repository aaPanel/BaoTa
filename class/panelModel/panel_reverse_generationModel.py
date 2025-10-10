# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: sww <sww@bt.cn>
# -------------------------------------------------------------------
import traceback
import os
import json
import re

import public
from panelModel.base import panelBase

try:
    from BTPanel import g
except:
    pass

from typing import Optional, Dict

#
# class main(panelBase):
#     __port = public.get_panel_port()
#     __admin_path = ''
#     if os.path.exists('data/admin_path.pl'):
#         __admin_path = public.readFile('data/admin_path.pl').strip()[1:]
#     setupPath = '/www/server'
#     is_ipv6 = False
#     __http = 'https://' if os.path.exists("data/ssl.pl") else 'http://'
#
#     # 添加到apache
#     def apacheAdd(self):
#         conf = '''
# <VirtualHost *:80>
#     ServerAdmin webmaster@example.com
#     DocumentRoot "/www/wwwroot/panel_ssl"
#     ServerName dc219ee7.{domain}
#     ServerAlias {domain}
#     #PROXY-START/
#     <IfModule mod_proxy.c>
#         ProxyRequests Off
#         # 反向代理websocket请求
#         RewriteEngine On
#         RewriteCond %{{HTTP:Connection}} Upgrade [NC]
#         RewriteCond %{{HTTP:Upgrade}} websocket  [NC]
#         RewriteRule /(.*) ws://127.0.0.1:{port}/$1 [P]
#
#         SSLProxyEngine on
#         ProxyPass / http://127.0.0.1:{port}/
#         ProxyPassReverse / http://127.0.0.1:{port}/
#         </IfModule>
#     #PROXY-END/
# </VirtualHost>
#         '''.format(port=self.__port, domain=self.siteName)
#         filename = '/www/server/panel/vhost/apache/' + self.siteName + '.conf'
#         public.writeFile(filename, conf)
#
#     # 添加到nginx
#     def nginxAdd(self):
#         conf = '''
#         server
# {{
#     listen 80;
#     server_name {domain};
#     root /www/wwwroot/panel_ssl;
#
# #PROXY-START/
#
# location ^~ /
# {{
#     proxy_pass http://127.0.0.1:{port}/;
#     proxy_set_header Host $host;
#     proxy_set_header X-Real-IP $remote_addr;
#     proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#     proxy_set_header REMOTE-HOST $remote_addr;
#     proxy_set_header Upgrade $http_upgrade;
#     proxy_set_header Connection "upgrade";
#     proxy_http_version 1.1;
#     # proxy_hide_header Upgrade;
#     add_header X-Cache $upstream_cache_status;
#     #Set Nginx Cache
# }}
# #PROXY-END/
# }}
#     '''.format(port=self.__port, domain=self.siteName)
#         filename = '/www/server/panel/vhost/nginx/' + self.siteName + '.conf'
#         public.writeFile(filename, conf)
#
#     def AddSite(self, get):
#         public.set_module_logs('config', 'set_generation', 1)
#         try:
#             if not (os.path.exists('/etc/init.d/nginx') or os.path.exists(
#                     '/etc/init.d/httpd')): return public.returnMsg(False, '未检测到nginx或apache服务，设置失败!')
#             if not hasattr(get, 'domain'): return public.returnMsg(False, '参数错误!')
#             if (hasattr(get, 'certPem') and hasattr(get, 'privateKey') and get.certPem and get.privateKey):
#                 import ssl_info
#                 # 验证证书和密钥是否匹配格式是否为pem
#                 ssl_info = ssl_info.ssl_info()
#                 check_flag, check_msg = ssl_info.verify_certificate_and_key_match(get.privateKey, get.certPem)
#                 if not check_flag: return public.returnMsg(False, check_msg)
#                 # 验证证书链是否完整
#                 check_chain_flag, check_chain_msg = ssl_info.verify_certificate_chain(get.certPem)
#                 if not check_chain_flag: return public.returnMsg(False, check_chain_msg)
#             self.siteName = get.domain.strip()
#             if public.M('domain').where('name=?', (self.siteName,)).count():
#                 return public.returnMsg(False, '域名已存在!')
#             if os.path.exists('data/panel_generation.pl'):
#                 self.del_panel_generation()
#             self.apacheAdd()
#             self.nginxAdd()
#             public.serviceReload()
#             data = {}
#             data['domain'] = self.siteName
#             data['port'] = self.__port
#             data['addr'] = self.__http + self.siteName + '/' + self.__admin_path
#             data['is_ssl'] = False
#             public.writeFile('data/panel_generation.pl', json.dumps(data))
#             if (hasattr(get, 'certPem') and hasattr(get,
#                                                     'privateKey') and get.certPem and get.privateKey) or self.__http == 'https://':
#                 self.set_panel_ssl(get)
#             return public.returnMsg(True, '添加成功!访问地址：{}'.format(data['addr']))
#         except:
#             return traceback.format_exc()
#
#     def get_cert_info(self, get):
#         try:
#             if not hasattr(get, 'cert_name'): return public.returnMsg(False, '参数错误!')
#             cert_name = get.cert_name
#             if cert_name.startswith('*.'):
#                 cert_name = cert_name[2:]
#             if not os.path.exists('/www/server/panel/vhost/ssl/{}'.format(cert_name)):
#                 return public.returnMsg(False, '证书不存在!')
#             cert_data = {}
#             cert_data['cert_name'] = cert_name
#             cert_data['cert'] = public.readFile('/www/server/panel/vhost/ssl/{}/fullchain.pem'.format(cert_name))
#             cert_data['key'] = public.readFile('/www/server/panel/vhost/ssl/{}/privkey.pem'.format(cert_name))
#             cert_data['info'] = json.loads(
#                 public.readFile('/www/server/panel/vhost/ssl/{}/info.json'.format(cert_name)))
#             return cert_data
#         except:
#             return traceback.format_exc()
#
#     def get_panel_generation(self, get=None):
#         try:
#             data = {}
#             if os.path.exists('data/panel_generation.pl'):
#                 data['proxy_stats'] = True
#                 panel_generation = json.loads(public.readFile('data/panel_generation.pl'))
#                 data['domain'] = panel_generation['domain']
#                 data['addr'] = self.__http + panel_generation['domain'] + '/' + self.__admin_path
#                 data['cert'] = False
#                 data['key'] = False
#                 if os.path.exists("data/ssl.pl"):
#                     data['cert'] = public.readFile('/www/server/panel/ssl/certificate.pem')
#                     data['key'] = public.readFile('/www/server/panel/ssl/privateKey.pem')
#                 return data
#             else:
#                 return {
#                     'proxy_stats': False,
#                     'addr': '',
#                     'cert': False,
#                     'key': False,
#                 }
#         except:
#             return traceback.format_exc()
#
#     def del_panel_generation(self, get=None):
#         if not os.path.exists('data/panel_generation.pl'):
#             return public.returnMsg(False, '未开启面板代理!')
#         data = json.loads(public.readFile('data/panel_generation.pl'))
#         public.ExecShell('rm -rf /www/wwwroot/' + data['domain'])
#         public.ExecShell('rm -rf /www/server/panel/vhost/nginx/' + data['domain'] + '.conf')
#         public.ExecShell('rm -rf /www/server/panel/vhost/apache/' + data['domain'] + '.conf')
#         public.ExecShell("rm -f data/panel_generation.pl")
#         public.serviceReload()
#         return public.returnMsg(True, '关闭成功!')
#
#     def set_panel_generation_ssl(self, get=None):
#         """
#         @name 兼容批量设置
#         @auther hezhihong
#         """
#         if hasattr(get, 'domain'):
#             siteName = get.domain
#         else:
#             data = json.loads(public.readFile('/www/server/panel/data/panel_generation.pl'))
#             siteName = data['domain']
#         # Nginx配置
#         file = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
#         conf = '''
# server
# {{
#     listen 443;
#     server_name {domain};
#     root /www/wwwroot/panel_ssl;
#
# #PROXY-START/
#
# ssl_certificate    /www/server/panel/ssl/certificate.pem;
# ssl_certificate_key    /www/server/panel/ssl/privateKey.pem;
# ssl_ciphers EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5;
# ssl_prefer_server_ciphers on;
# ssl_session_cache shared:SSL:10m;
# ssl_session_timeout 10m;
# ssl_protocols TLSv1 TLSv1.1 TLSv1.2; #表示使用的TLS协议的类型。
# location ^~ /
# {{
#     proxy_pass https://127.0.0.1:{port}/;
#     proxy_set_header Host $host;
#     proxy_set_header X-Real-IP $remote_addr;
#     proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#     proxy_set_header REMOTE-HOST $remote_addr;
#     proxy_set_header Upgrade $http_upgrade;
#     proxy_set_header Connection $upgrade;
#     proxy_http_version 1.1;
#     # proxy_hide_header Upgrade;
#     add_header X-Cache $upstream_cache_status;
#     #Set Nginx Cache
# }}
# #PROXY-END/
# }}
#             '''.format(port=self.__port, domain=siteName)
#         public.writeFile(file, conf)
#
#         # Apache配置
#         file = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
#         conf = """
# <VirtualHost *:443>
# ServerAdmin webmaster@example.com
# DocumentRoot "/www/wwwroot/panel_ssl"
# ServerName dc219ee7.{domain}
# ServerAlias {domain}
# SSLProxyEngine on
# SSLProxyVerify none
# SSLProxyCheckPeerCN off
# SSLProxyCheckPeerName off
# SSLProxyCheckPeerExpire off
# SSLEngine on
# SSLCertificateFile          /www/server/panel/ssl/certificate.pem
# SSLCertificateKeyFile       /www/server/panel/ssl/privateKey.pem
# #PROXY-START/
# <IfModule mod_proxy.c>
# ProxyRequests Off
#     # 反向代理websocket请求
#     RewriteEngine On
#     RewriteCond %{{HTTP:Connection}} Upgrade [NC]
#     RewriteCond %{{HTTP:Upgrade}} websocket  [NC]
#     RewriteRule /(.*) ws://127.0.0.1:{port}/$1 [P]
#
#     SSLProxyEngine on
#     ProxyPass / https://127.0.0.1:{port}/
#     ProxyPassReverse / https://127.0.0.1:{port}/
# </IfModule>
# #PROXY-END/
# </VirtualHost>
#         """.format(port=self.__port, domain=siteName)
#         self.apacheAddPort(443)
#         public.writeFile(file, conf)
#         public.serviceReload()
#         data = {}
#         data['domain'] = siteName
#         data['port'] = self.__port
#         data['addr'] = self.__http + self.siteName + '/' + self.__admin_path
#         data['is_ssl'] = True
#         public.writeFile('data/panel_generation.pl', json.dumps(data))
#
#     def apacheAddPort(self, port):
#         port = str(port)
#         filename = self.setupPath + '/apache/conf/extra/httpd-ssl.conf'
#         if os.path.exists(filename):
#             ssl_conf = public.readFile(filename)
#             if ssl_conf:
#                 if ssl_conf.find('Listen 443') != -1:
#                     ssl_conf = ssl_conf.replace('Listen 443', '')
#                     public.writeFile(filename, ssl_conf)
#
#         filename = self.setupPath + '/apache/conf/httpd.conf'
#         if not os.path.exists(filename): return
#         allConf = public.readFile(filename)
#         rep = r"Listen\s+([0-9]+)\n"
#         tmp = re.findall(rep, allConf)
#         if not tmp: return False
#         for key in tmp:
#             if key == port: return False
#
#         listen = "\nListen " + tmp[0] + "\n"
#         listen_ipv6 = ''
#         # if self.is_ipv6: listen_ipv6 = "\nListen [::]:" + port
#         allConf = allConf.replace(listen, listen + "Listen " + port + listen_ipv6 + "\n")
#         public.writeFile(filename, allConf)
#         return True
#
#     def set_panel_ssl(self, get):
#         flag = 1
#         if not hasattr(get, 'certPem') or not get.certPem:
#             flag = 0
#             get.certPem = public.readFile('/www/server/panel/ssl/certificate.pem')
#         if not hasattr(get, 'privateKey') or not get.privateKey:
#             flag = 0
#             get.privateKey = public.readFile('/www/server/panel/ssl/privateKey.pem')
#         if flag:
#             result = self.SavePanelSSL(get)
#             if not result['status']: return result
#
#         sslConf = '/www/server/panel/data/ssl.pl'
#         public.writeFile(sslConf, 'True')
#         public.writeFile('data/reload.pl', 'True')
#         self.set_panel_generation_ssl(get)
#         return public.returnMsg(True, '证书已保存!')
#
#     def SavePanelSSL(self, get):
#         keyPath = 'ssl/privateKey.pem'
#         certPath = 'ssl/certificate.pem'
#         checkCert = '/tmp/cert.pl'
#         ssl_pl = 'data/ssl.pl'
#         if not 'certPem' in get: return public.returnMsg(False, '缺少certPem参数!')
#         if not 'privateKey' in get: return public.returnMsg(False, '缺少privateKey参数!')
#         public.writeFile(checkCert, get.certPem)
#         if not public.CheckCert(checkCert):
#             os.remove(checkCert)
#             return public.returnMsg(False, '证书错误,请检查!')
#         if get.privateKey:
#             public.writeFile(keyPath, get.privateKey)
#         if get.certPem:
#             public.writeFile(certPath, get.certPem)
#         public.writeFile('ssl/input.pl', 'True')
#         if os.path.exists(ssl_pl): public.writeFile('data/reload.pl', 'True')
#         return public.returnMsg(True, '证书已保存!')
#
#     def stop_panel_ssl(self, get):
#         sslConf = '/www/server/panel/data/ssl.pl'
#         if os.path.exists(sslConf) and not 'cert_type' in get:
#             if os.path.exists('/www/server/panel/data/ssl_verify_data.pl'):
#                 return public.returnMsg(False, '检测到当前面板已开启访问设备验证，请先关闭访问设备验证！')
#             public.ExecShell('rm -f ' + sslConf)
#             try:
#                 g.rm_ssl = True
#             except:
#                 pass
#             data = json.loads(public.readFile('data/panel_generation.pl'))
#             get.domain = data['domain']
#             self.AddSite(get)
#             return public.returnMsg(True, 'PANEL_SSL_CLOSE')
#
#     def check_panel_site(self, get=None):
#         if not os.path.exists('data/panel_generation.pl'):
#             return public.returnMsg(True, '未开启面板代理!')
#         data = json.loads(public.readFile('data/panel_generation.pl'))
#         get = public.to_dict_obj({
#             'domain': data['domain'],
#         })
#         if data['port'] != self.__port:
#             self.AddSite(get)
#         if data['is_ssl'] != (self.__http == 'https://'):
#             self.AddSite(get)
#         return public.returnMsg(True, '检查成功!')
#

class PanelNginxProxy:
    _PROXY_MOD_DIR = "/www/server/proxy_project/sites"

    def __init__(self):
        from mod.project.proxy.comMod import main as Proxy
        self.proxy = Proxy()
        self._panel_url: Optional[str] = ""
        self.panel_port = public.get_panel_port()
        self._panel_site_data: Optional[dict] = None
        self.admin_path = '/'
        if os.path.exists('data/admin_path.pl'):
            self.admin_path = public.readFile('data/admin_path.pl').strip()
            if not self.admin_path:
                self.admin_path = '/'

    @staticmethod
    def get_panel_ssl() -> Dict:
        from config import config as PanelConf
        panel_conf = PanelConf()
        return panel_conf.GetPanelSSL(None)

    @property
    def panel_url(self):
        if not self._panel_url:
            schema = "https" if os.path.exists("data/ssl.pl") else "http"
            self._panel_url = "{schema}://127.0.0.1:{port}".format(schema=schema, port=self.panel_port)
        return self._panel_url

    # 通过当前代理的地址 127.0.0.1 和端口 panel_port 来确定面板代理的网站， 如果没有则返回None
    def get_proxy_site(self) -> Optional[dict]:
        if not os.path.isdir(self._PROXY_MOD_DIR):
            return None
        if self._panel_site_data:
            return self._panel_site_data

        from urllib.parse import urlparse
        target_name = ""
        for site_name in os.listdir(self._PROXY_MOD_DIR):
            conf_file = os.path.join(self._PROXY_MOD_DIR, site_name, site_name + ".json")
            try:
                data = json.loads(public.readFile(conf_file))
            except:
                continue

            for item in data.get("proxy_info", []):
                if item.get("proxy_path", "") != "/":
                    continue
                u = urlparse(item.get("proxy_pass", ""))
                if u.hostname == "127.0.0.1" and int(u.port if u.port else 80) == int(self.panel_port):
                    target_name = site_name
                    break

            if target_name:
                break

        if not target_name:
            return None

        res = public.M("sites").where("name =? and project_type= ? ", (target_name, "proxy")).find()
        if not isinstance(res, dict):
            return None
        self._panel_site_data = {
            "name": res["name"],
            "id": res["id"],
            "ssl": self.proxy.get_site_ssl_info(res["name"])
        }
        if self._panel_site_data["ssl"] != -1:
            self._panel_site_data["ssl"]["cert"] = public.readFile(
                os.path.join(public.get_vhost_path(), "cert", res["name"], "fullchain.pem")
            )
            self._panel_site_data["ssl"]["key"] = public.readFile(
                os.path.join(public.get_vhost_path(), "cert", res["name"], "privkey.pem")
            )
        return self._panel_site_data

    def create_proxy_site(self, domain: str) -> str:
        args = public.to_dict_obj({
            "proxy_pass": self.panel_url,
            "proxy_type": "http",
            "domains": domain,
            "proxy_host": "$http_host",
            "remark": "宝塔面板的反代[请误操作,修改可能会导致面板无法访问]"
        })

        create_result = self.proxy.create(args)
        if not create_result['status']:
            return create_result['msg']

        return ""

    def close_proxy_site(self) -> str:
        site = self.get_proxy_site()
        if not site:
            return "未找到面板代理网站"
        close_result = self.proxy.delete(public.to_dict_obj({
            "id": site["id"],
            "site_name": site["name"],
            "remove_path": 1,
        }))
        if not close_result['status']:
            return close_result['msg']
        return ""

    # 开启证书，如果没有传递证书则使用自签证书， 如果没有自签证书，尝试生成，如果传递证书则使用
    def open_site_ssl(self, private_key: str = "", certificate: str = "") -> str:
        site = self.get_proxy_site()
        if not site:
            return "未找到面板代理网站"

        if not private_key or not certificate:
            ssl_conf = self.get_panel_ssl()
            private_key = ssl_conf["privateKey"]
            certificate = ssl_conf["certPem"]

        if not private_key or not certificate:
            return "未找到证书"

        res = self.proxy.set_ssl(public.to_dict_obj({
            "site_name": site["name"],
            "key": private_key,
            "csr": certificate,
        }))
        if not res['status']:
            return res['msg']
        return ""

    def close_site_ssl(self) -> str:
        site = self.get_proxy_site()
        if not site:
            return "未找到面板代理网站"
        res = self.proxy.close_ssl(public.to_dict_obj({
            "site_name": site["name"],
        }))
        if not res['status']:
            return res['msg']
        return ""


class main:

    def __init__(self):
        pass

    @staticmethod
    def get_panel_generation(get: public.dict_obj = None):
        p = PanelNginxProxy()
        site = p.get_proxy_site()
        if site:
            schema = "https" if site['ssl'] != -1 else "http"
            data = {
                'proxy_stats': True,
                'domain': site['name'],
                'addr': schema + "://" + site['name'] + p.admin_path,
                'use_ssl': site['ssl'] != -1,
                'cert': "" if site['ssl'] == -1 else site["ssl"]["cert"],
                'key': "" if site['ssl'] == -1 else site["ssl"]["key"]
            }
            if site['ssl'] == -1:
                ssl_conf = p.get_panel_ssl()
                data['cert'] = ssl_conf["certPem"]
                data['key'] = ssl_conf["privateKey"]

            return data

        else:
            ssl_conf = p.get_panel_ssl()
            return {
                'proxy_stats': False,
                'domain': '',
                'addr': '',
                'use_ssl': False,
                'cert': ssl_conf["certPem"],
                'key': ssl_conf["privateKey"],
            }

    @staticmethod
    def del_panel_generation(get: public.dict_obj = None):
        p = PanelNginxProxy()
        p.close_proxy_site()
        return public.returnMsg(True, '关闭成功')

    @staticmethod
    def set_panel_generation(get: public.dict_obj):
        if public.get_webserver() != "nginx":
            return public.returnMsg(False, '当前仅支持nginx环境')
        domain = get.get("domain", "")
        if not domain:
            return public.returnMsg(False, '请输入要绑定的域名')
        key = get.get("key", "")
        cert = get.get("cert", "")
        p = PanelNginxProxy()
        old_site = p.get_proxy_site()
        if old_site and old_site['name'] != domain:
            p.close_proxy_site()
            p = PanelNginxProxy()  # 防止缓存
            old_site = None

        if not old_site:
            err = p.create_proxy_site(domain)
            if err:
                return public.returnMsg(False, err)


        err = ""
        if key and cert:
            err = p.open_site_ssl(key, cert)

        if err:
            return public.returnMsg(False, err)
        return public.returnMsg(True, '设置成功')
