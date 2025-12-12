# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------
# ------------------------------
# 反向代理模型
# ------------------------------
import re
import sys
import json
import os

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

os.chdir("/www/server/panel")
import public

from mod.base import pynginx
from mod.base.pynginx.extension import ServerTools, ConfigTools, ConfigFinder
from typing import Optional, Tuple, Callable, Type, Any


class main():

    def __init__(self):
        self._proxy_path = '/www/server/proxy_project'
        self._proxy_config_path = self._proxy_path + '/sites'
        self._site_proxy_conf_path = ""
        if not os.path.exists(self._proxy_config_path):
            public.ExecShell('mkdir -p {}'.format(self._proxy_config_path))
            public.ExecShell('chown -R www:www {}'.format(self._proxy_config_path))
            public.ExecShell('chmod -R 755 {}'.format(self._proxy_config_path))

        self._init_proxy_conf = {
            "site_name": "",
            "domain_list": [],
            "primary_port": "",
            "site_port": [],
            "https_port": "443",
            "ipv4_port_conf": "listen {listen_port};",
            "ipv6_port_conf": "listen [::]:{listen_port};",
            "port_conf": "listen {listen_port};{listen_ipv6}",
            "ipv4_ssl_port_conf": "{ipv4_port_conf}\n    listen {https_port} ssl http2 ;",
            "ipv6_ssl_port_conf": "{ipv6_port_conf}\n    listen [::]:{https_port} ssl http2 ;",
            "ipv4_http3_ssl_port_conf": "{ipv4_port_conf}\n    listen {https_port} quic;\n    listen {https_port} ssl;",
            "ipv6_http3_ssl_port_conf": "{ipv6_port_conf}\n    listen [::]:{https_port} quic;\n    listen [::]:{https_port} ssl ;",
            "site_path": "",
            "ssl_info": {
                "ssl_status": False,
                "ssl_default_conf": "#error_page 404/404.html;",
                "ssl_conf": '#error_page 404/404.html;\n    ssl_certificate    /www/server/panel/vhost/cert/{site_name}/fullchain.pem;\n    ssl_certificate_key    /www/server/panel/vhost/cert/{site_name}/privkey.pem;\n    ssl_protocols TLSv1.1 TLSv1.2 TLSv1.3;\n    ssl_ciphers EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5;\n    ssl_prefer_server_ciphers on;\n    ssl_session_cache shared:SSL:10m;\n    ssl_session_timeout 10m;\n    add_header Strict-Transport-Security "max-age=31536000";\n    error_page 497  https://$host$request_uri;',
                "force_ssl_conf": '#error_page 404/404.html;{force_conf}\n    ssl_certificate    /www/server/panel/vhost/cert/{site_name}/fullchain.pem;\n    ssl_certificate_key    /www/server/panel/vhost/cert/{site_name}/privkey.pem;\n    ssl_protocols TLSv1.1 TLSv1.2 TLSv1.3;\n    ssl_ciphers EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5;\n    ssl_prefer_server_ciphers on;\n    ssl_session_cache shared:SSL:10m;\n    ssl_session_timeout 10m;\n    add_header Strict-Transport-Security "max-age=31536000";\n    error_page 497  https://$host$request_uri;',
                "force_https": False,
                "force_conf": "    #HTTP_TO_HTTPS_START\n    set $isRedcert 1;\n    if ($server_port != 443) {\n        set $isRedcert 2;\n    }\n    if ( $uri ~ /\.well-known/ ) {\n        set $isRedcert 1;\n    }\n    if ($isRedcert != 1) {\n        rewrite ^(/.*)$ https://$host$1 permanent;\n    }\n    #HTTP_TO_HTTPS_END",
            },
            "err_age_404": "",
            "err_age_502": "",
            "ip_limit": {
                "ip_black": [],
                "ip_white": [],
            },
            "basic_auth": [],
            "proxy_cache": {
                "cache_status": False,
                "cache_zone": "",
                "static_cache": "",
                "expires": "1d",
                "cache_conf": "",
            },
            "gzip": {
                "gzip_status": False,
                "gzip_min_length": "1k",
                "gzip_comp_level": "6",
                "gzip_types": "text/plain application/javascript application/x-javascript text/javascript text/css application/xml application/json image/jpeg image/gif image/png font/ttf font/otf image/svg+xml application/xml+rss text/x-js",
                "gzip_conf": "gzip on;\n     gzip_min_length 10k;\n     gzip_buffers 4 16k;\n     gzip_http_version 1.1;\n     gzip_comp_level 2;\n     gzip_types text/plain application/javascript application/x-javascript text/javascript text/css application/xml;\n     gzip_vary on;\n     gzip_proxied expired no-cache no-store private auth;\n     gzip_disable \"MSIE [1-6]\.\";",
            },
            "subs_filter": False,
            "sub_filter": {
                "sub_filter_str": [],
            },
            "websocket": {
                "websocket_status": True,
                "websocket_conf": "proxy_http_version 1.1;\n      proxy_set_header Upgrade $http_upgrade;\n      proxy_set_header Connection $connection_upgrade;",
            },
            "security": {
                "security_status": False,
                "static_resource": "jpg|jpeg|gif|png|js|css",
                "return_resource": "404",
                "http_status": False,
                "domains": "",
                "security_conf": "    #SECURITY-START 防盗链配置"
                                 "\n    location ~ .*\.({static_resource})$"
                                 "\n    {{\n        expires      {expires};"
                                 "\n        access_log /dev/null;"
                                 "\n        valid_referers {domains};"
                                 "\n        if ($invalid_referer){{"
                                 "\n           return {return_resource};"
                                 "\n        }}"
                                 "\n    }}\n    #SECURITY-END",
            },
            "redirect": {
                "redirect_status": False,
                "redirect_conf": "    #引用重定向规则，注释后配置的重定向代理将无效\n    include /www/server/panel/vhost/nginx/redirect/{site_name}/*.conf;",
            },
            "proxy_log": {
                "log_type": "default",
                "server_port": "",
                "log_path": "",
                "log_conf": "\naccess_log  {log_path}/{site_name}.log;\n    error_log  {log_path}/{site_name}.error.log;",
            },
            "default_cache": "proxy_cache_path /www/wwwroot/{site_name}/proxy_cache_dir levels=1:2 keys_zone={cache_name}_cache:20m inactive=1d max_size=5g;",
            "default_describe": "# 如果反代网站访问异常且这里已经配置了内容，请优先排查此处的配置是否正确\n",
            "http_block": "",
            "server_block": "",
            "remark": "",
            "proxy_info": [],
        }
        self._template_conf = '''{http_block}
server {{
    {port_conf}
    server_name {domains};
    index index.php index.html index.htm default.php default.htm default.html;
    root {site_path};
    include /www/server/panel/vhost/nginx/extension/{site_name}/*.conf;
    
    #CERT-APPLY-CHECK--START
    # 用于SSL证书申请时的文件验证相关配置 -- 请勿删除
    include /www/server/panel/vhost/nginx/well-known/{site_name}.conf;
    #CERT-APPLY-CHECK--END

    #SSL-START {ssl_start_msg}
    {ssl_info}
    #SSL-END
    #REDIRECT START
    {redirect_conf}
    #REDIRECT END

    #ERROR-PAGE-START  {err_page_msg}
    {err_age_404}
    {err_age_502}
    #ERROR-PAGE-END

    #PHP-INFO-START  PHP引用配置，可以注释或修改
    {security_conf}
    include enable-php-00.conf;
    #PHP-INFO-END

    #IP-RESTRICT-START 限制访问ip的配置，IP黑白名单
    {ip_limit_conf}
    #IP-RESTRICT-END

    #BASICAUTH START
    {auth_conf}
    #BASICAUTH END

    #SUB_FILTER START
    {sub_filter}
    #SUB_FILTER END

    #GZIP START
    {gzip_conf}
    #GZIP END

    #GLOBAL-CACHE START
    {proxy_cache}
    #GLOBAL-CACHE END

    #WEBSOCKET-SUPPORT START
    {websocket_support}
    #WEBSOCKET-SUPPORT END

    #PROXY-CONF-START
    {proxy_conf}
    #PROXY-CONF-END

    #SERVER-BLOCK START
    {server_block}
    #SERVER-BLOCK END

    #禁止访问的文件或目录
    location ~ ^/(\.user.ini|\.htaccess|\.git|\.env|\.svn|\.project|LICENSE|README.md)
    {{
        return 404;
    }}

    #一键申请SSL证书验证目录相关设置
    location /.well-known{{
        allow all;
    }}

    #禁止在证书验证目录放入敏感文件
    if ( $uri ~ "^/\.well-known/.*\.(php|jsp|py|js|css|lua|ts|go|zip|tar\.gz|rar|7z|sql|bak)$" ) {{
        return 403;
    }}

    #LOG START
    {server_log}
    {monitor_conf}
    #LOG END
}}'''
        self._template_proxy_conf = '''location ^~ {proxy_path} {{
      {ip_limit}
      {basic_auth}
      proxy_pass {proxy_pass};
      proxy_set_header Host {proxy_host};
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Real-Port $remote_port;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto $scheme;
      proxy_set_header X-Forwarded-Host $host;
      proxy_set_header X-Forwarded-Port $server_port;
      proxy_set_header REMOTE-HOST $remote_addr;
      {SNI}
      {timeout_conf}
      {websocket_support}
      {custom_conf}
      {proxy_cache}
      {gzip}
      {sub_filter}
      {server_log}
    }}'''

    # 仅在创建时使用 构造默认配置
    def structure_proxy_conf(self, get):
        '''
            @name
            @author wzz <2024/4/19 下午4:29>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        sni_conf = ""
        if get.proxy_pass.startswith("https://"):
            sni_conf = "proxy_ssl_server_name on;"
        get.proxy_conf = self._template_proxy_conf.format(
            ip_limit="",
            gzip="",
            proxy_cache="",
            sub_filter="",
            server_log="",
            basic_auth="",
            proxy_pass=get.proxy_pass,
            proxy_host=get.proxy_host,
            proxy_path=get.proxy_path,
            SNI=sni_conf,
            custom_conf="",
            timeout_conf=get.proxy_timeout,
            websocket_support=self._init_proxy_conf["websocket"]["websocket_conf"],
        )

        get.proxy_info = {
            "proxy_type": get.proxy_type,
            "proxy_path": get.proxy_path,
            "proxy_pass": get.proxy_pass,
            "proxy_host": get.proxy_host,
            "ip_limit": {
                "ip_black": [],
                "ip_white": [],
            },
            "basic_auth": {},
            "proxy_cache": {
                "cache_status": False,
                "cache_zone": get.site_name.replace(".", "_") + "_cache",
                "static_cache": "",
                "expires": "1d",
                "cache_suffix": "css,js,jpe,jpeg,gif,png,webp,woff,eot,ttf,svg,ico,css.map,js.map",
                "cache_conf": "",
            },
            "gzip": {
                "gzip_status": False,
                "gzip_min_length": "1k",
                "gzip_comp_level": "6",
                "gzip_types": "text/plain application/javascript application/x-javascript text/javascript text/css application/xml application/json image/jpeg image/gif image/png font/ttf font/otf image/svg+xml application/xml+rss text/x-js",
                "gzip_conf": "gzip on;\n     gzip_min_length 10k;\n     gzip_buffers 4 16k;\n     gzip_http_version 1.1;\n     gzip_comp_level 2;\n     gzip_types text/plain application/javascript application/x-javascript text/javascript text/css application/xml;\n     gzip_vary on;\n     gzip_proxied expired no-cache no-store private auth;\n     gzip_disable \"MSIE [1-6]\.\";",
            },
            "sub_filter": {
                "sub_filter_str": [],
            },
            "websocket": {
                "websocket_status": True,
                "websocket_conf": "proxy_http_version 1.1;\n      proxy_set_header Upgrade $http_upgrade;\n      proxy_set_header Connection $connection_upgrade;",
            },
            "proxy_log": {
                "log_type": "off",
                "log_conf": get.server_log,
            },
            "timeout": {
                "proxy_connect_timeout": "60",
                "proxy_send_timeout": "600",
                "proxy_read_timeout": "600",
                "timeout_conf": "proxy_connect_timeout 60s;\n      proxy_send_timeout 600s;\n      proxy_read_timeout 600s;",
            },
            "custom_conf": "",
            "proxy_conf": get.proxy_conf,
            "remark": "",
            "template_proxy_conf": self._template_proxy_conf,
        }

    # 2024/4/18 上午10:53 构造反向代理的配置文件, 仅在创建时使用
    def structure_nginx(self, get):
        '''
            @name 构造反向代理的配置文件
            @author wzz <2024/4/18 上午10:54>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.err_age_404 = get.get("err_age_404", "#error_page 404 /404.html;")
        get.err_age_502 = get.get("err_age_502", "#error_page 502 /502.html;")
        get.proxy_info = get.get("proxy_info", "")

        get.server_log = self._init_proxy_conf["proxy_log"]["log_conf"].format(
            log_path=public.get_logs_path(),
            site_name=get.site_name
        )
        if get.site_port != "80":
            get.server_log = self._init_proxy_conf["proxy_log"]["log_conf"].format(
                log_path=public.get_logs_path(),
                site_name="{}_{}".format(get.site_name, get.site_port)
            )

        get.remark = get.get("remark", "")
        get.server_block = get.get("server_block", "")
        get.websocket_status = get.get("websocket_status", True)
        get.proxy_timeout = "proxy_connect_timeout 60s;\n      proxy_send_timeout 600s;\n      proxy_read_timeout 600s;"
        self.structure_proxy_conf(get)
        is_subs = public.ExecShell("nginx -V 2>&1|grep 'ngx_http_substitutions_filter' -o")[0]

        self._init_proxy_conf["subs_filter"] = True if is_subs != "" else False
        self._init_proxy_conf["site_name"] = get.main_domain
        self._init_proxy_conf["domain_list"] = get.domain_list
        self._init_proxy_conf["site_port"] = get.port_list
        self._init_proxy_conf["site_path"] = get.site_path
        self._init_proxy_conf["err_age_404"] = get.err_age_404
        self._init_proxy_conf["err_age_502"] = get.err_age_502
        self._init_proxy_conf["proxy_log"]["log_conf"] = get.server_log
        self._init_proxy_conf["remark"] = get.remark
        self._init_proxy_conf["http_block"] = ""
        self._init_proxy_conf["proxy_info"].append(get.proxy_info)
        self._init_proxy_conf["proxy_cache"]["cache_zone"] = get.site_name.replace(".",
                                                                                   "_") + "_cache" if get.site_port == "80" else "{}_{}_cache".format(
            get.site_name.replace(".", "_"), get.site_port)
        self._init_proxy_conf["primary_port"] = get.site_port

    # 2024/4/18 上午10:35 写入Nginx配置文件 仅在创建时使用
    def write_nginx_conf(self, get):
        '''
            @name 写入Nginx配置文件
            @author wzz <2024/4/18 上午10:36>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        # 这里可能会报错
        self.structure_nginx(get)

        if len(get.port_list) > 1:
            ipv4_port_conf = ""
            ipv6_port_conf = ""
            for p in get.port_list:
                ipv4_port_conf += self._init_proxy_conf["ipv4_port_conf"].format(listen_port=p) + "\n    "
                ipv6_port_conf += self._init_proxy_conf["ipv6_port_conf"].format(listen_port=p) + "\n    "
        else:
            ipv4_port_conf = self._init_proxy_conf["ipv4_port_conf"].format(listen_port=get.port_list[0])
            ipv6_port_conf = self._init_proxy_conf["ipv6_port_conf"].format(listen_port=get.port_list[0])
        port_conf = ipv4_port_conf + "\n" + ipv6_port_conf

        # 2024/6/4 下午4:20 兼容新版监控报表的配置
        monitor_conf = ""
        if os.path.exists("/www/server/panel/plugin/monitor/monitor_main.py"):
            monitor_conf = '''#Monitor-Config-Start 网站监控报表日志发送配置
    access_log syslog:server=unix:/tmp/bt-monitor.sock,nohostname,tag={pid}__access monitor;
    error_log syslog:server=unix:/tmp/bt-monitor.sock,nohostname,tag={pid}__error;
    #Monitor-Config-End'''.format(pid=get.pid)

        conf = self._template_conf.format(
            http_block=get.http_block,
            server_block="",
            port_conf=port_conf,
            ssl_start_msg=public.getMsg('NGINX_CONF_MSG1'),
            err_page_msg=public.getMsg('NGINX_CONF_MSG2'),
            php_info_start=public.getMsg('NGINX_CONF_MSG3'),
            rewrite_start_msg=public.getMsg('NGINX_CONF_MSG4'),
            log_path=public.get_logs_path(),
            domains=' '.join(get.domain_list) if len(get.domain_list) > 1 else get.site_name,
            site_name=get.site_name,
            ssl_info="#error_page 404/404.html;",
            err_age_404=get.err_age_404,
            err_age_502=get.err_age_502,
            ip_limit_conf="",
            auth_conf="",
            sub_filter="",
            gzip_conf="",
            redirect_conf="",
            security_conf="",
            proxy_conf=get.proxy_conf,
            server_log=get.server_log,
            site_path=get.site_path,
            proxy_cache="",
            websocket_support=self._init_proxy_conf["websocket"]["websocket_conf"],
            monitor_conf=monitor_conf,
        )

        # 写配置文件
        well_known_path = "{}/vhost/nginx/well-known".format(public.get_panel_path())
        if not os.path.exists(well_known_path):
            os.makedirs(well_known_path, 0o600)
        if not os.path.exists("/www/server/panel/vhost/nginx/extension/{}/".format(get.main_domain)):
            os.makedirs("/www/server/panel/vhost/nginx/extension/{}/".format(get.main_domain), 0o600)
        public.writeFile("{}/{}.conf".format(well_known_path, get.main_domain), "")

        get.filename = public.get_setup_path() + '/panel/vhost/nginx/' + get.main_domain + '.conf'

        return public.writeFile(get.filename, conf)

    # 2024/4/25 上午11:11 检查nginx是否支持http3
    def check_http3_support(self):
        '''
            @name 检查nginx是否支持http3
            @author wzz <2024/4/25 上午11:13>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        return public.ExecShell("nginx -V 2>&1| grep 'http_v3_module' -o")[0]

    # 2024/4/18 上午9:26 创建反向代理
    def create(self, get):
        '''
            @name 创建反向代理
            @author wzz <2024/4/18 上午9:27>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        # 2024/4/18 上午9:41 前置处理开始
        from mod.base.web_conf import util
        webserver = util.webserver()
        if webserver != "nginx" or webserver is None:
            return public.returnResult(status=False, msg="仅支持Nginx，请安装Nginx后再使用！")

        from panelSite import panelSite
        site_obj = panelSite()
        site_obj.check_default()

        wc_err = public.checkWebConfig()
        if not wc_err is True:
            return public.returnResult(
                status=False,
                msg='ERROR: 检测到配置文件有错误,请先排除后再操作<br><br><a style="color:red;">' +
                    wc_err.replace("\n", '<br>') + '</a>'
            )

        # 2024/4/18 上午9:45 参数处理
        get.domains = get.get("domains", "")
        get.proxy_path = get.get("proxy_path", "/")
        get.proxy_pass = get.get("proxy_pass", "")
        get.proxy_host = get.get("proxy_host", "$http_host")
        get.remark = get.get("remark", "")
        get.proxy_type = get.get("proxy_type", "http")

        # 2024/4/18 上午9:45 参数校验
        if not get.domains:
            return public.returnResult(status=False, msg="域名不能为空，至少输入一个域名！")
        if not get.proxy_pass:
            return public.returnResult(status=False, msg="代理目标不能为空！")
        if get.remark != "":
            get.remark = public.xssencode2(get.remark)
        if get.proxy_type == "unix":
            if not get.proxy_pass.startswith("/"):
                return public.returnResult(status=False, msg="unix文件路径必须以/开头，如/tmp/flask_app.sock！")
            if not get.proxy_pass.endswith(".sock"):
                return public.returnResult(status=False, msg="unix文件必须以.sock结尾，如/tmp/flask_app.sock！")
            if not os.path.exists(get.proxy_pass):
                return public.returnResult(status=False, msg="代理目标不存在！")
            get.proxy_pass = "http://unix:{}".format(get.proxy_pass)
        elif get.proxy_type == "http":
            if not get.proxy_pass.startswith("http://") and not get.proxy_pass.startswith("https://"):
                return public.returnResult(status=False, msg="代理目标必须以http://或https://开头！")

        # 2024/4/18 上午9:45 创建反向代理
        get.domain_list = get.domains.split("\n")
        get.site_name = util.to_puny_code(get.domain_list[0].strip().split(":")[0]).strip().lower()
        public.check_domain_cloud(get.site_name)
        if get.site_name.find('*') != -1: return public.returnResult(False, '主域名不能为泛解析')
        get.site_path = "/www/wwwroot/" + get.site_name
        get.site_port = get.domain_list[0].strip().split(":")[1] if ":" in get.domain_list[0] else "80"
        get.port_list = [get.site_port]
        if not public.checkPort(get.site_port):
            return public.returnResult(status=False, msg='端口【{}】不合法！'.format(get.site_port))

        if len(get.domain_list) > 1:
            for domain in get.domain_list[1:]:
                if not ":" in domain.strip():
                    continue

                d_port = domain.strip().split(":")[1]
                if not public.checkPort(d_port):
                    return public.returnResult(status=False, msg='端口【{}】不合法！'.format(d_port))

                if not d_port in get.port_list:
                    get.port_list.append(d_port)

        if get.site_port != "80":
            get.site_path = "/www/wwwroot/{}_{}".format(get.site_name, get.site_port)
            cache_name = "{}_{}".format(get.site_name.replace(".", "_"), get.site_port)
            self._site_path = "{}/{}_{}".format(self._proxy_config_path, get.site_name, get.site_port)
            get.main_domain = self.json_name = "{}_{}".format(get.site_name, get.site_port)
        else:
            get.site_path = "/www/wwwroot/" + get.site_name
            cache_name = get.site_name.replace(".", "_")
            self._site_path = self._proxy_config_path + '/' + get.site_name
            get.main_domain = self.json_name = get.site_name

        # 2024/4/18 上午10:06 检查域名是否存在
        opid = public.M('domain').where("name=? and port=?", (get.site_name, int(get.site_port))).getField('pid')
        if opid:
            if public.M('sites').where('id=?', (opid,)).count():
                return public.returnResult(status=False, msg='网站【{}】已存在，请勿重复添加！'.format(get.site_name))
            public.M('domain').where('pid=?', (opid,)).delete()

        if public.M('binding').where('domain=?', (get.site_name,)).count():
            return public.returnResult(status=False, msg='网站【{}】已存在，请勿重复添加！'.format(get.site_name))

        # 2024/4/18 上午10:06 检查网站是否存在
        sql = public.M('sites')
        if sql.where("name=?", (get.main_domain,)).count():
            return public.returnResult(status=False, msg='网站【{}】已存在，请勿重复添加！'.format(get.main_domain))

        # 2024/4/18 上午10:21 添加端口到系统防火墙
        from firewallModel.comModel import main as comModel
        firewall_com = comModel()
        get.port = get.site_port
        firewall_com.set_port_rule(get)

        # 2024/4/18 上午9:41 前置处理结束

        # 2024/4/18 上午10:46 写入网站配置文件
        get.http_block = "proxy_cache_path {site_path}/proxy_cache_dir levels=1:2 keys_zone={cache_name}_cache:20m inactive=1d max_size=5g;".format(
            site_path=get.site_path,
            cache_name=cache_name
        )

        if not os.path.exists(self._site_path):
            public.ExecShell('mkdir -p {}'.format(self._site_path))
            public.ExecShell('chown -R www:www {}'.format(self._site_path))
            public.ExecShell('chmod -R 755 {}'.format(self._site_path))

        if not os.path.exists(get.site_path):
            public.ExecShell('mkdir -p {}'.format(get.site_path))
            public.ExecShell('chown -R www:www {}'.format(get.site_path))
            public.ExecShell('chmod -R 755 {}'.format(get.site_path))

        if not os.path.exists(get.site_path + "/proxy_cache_dir"):
            public.ExecShell('mkdir -p {}'.format(get.site_path + "/proxy_cache_dir"))
            public.ExecShell('chown -R www:www {}'.format(get.site_path + "/proxy_cache_dir"))
            public.ExecShell('chmod -R 755 {}'.format(get.site_path + "/proxy_cache_dir"))

        if not os.path.exists(get.site_path + "/proxy_cache_dir"):
            return public.returnResult(status=False,
                                       msg="创建缓存目录失败，请尝试手动创建{}是否成功，如果不成功请联系宝塔运维".format(
                                           get.site_path + "/proxy_cache_dir"))

        self._site_proxy_conf_path = '{}/{}.json'.format(self._site_path, self.json_name)

        # 2024/4/18 上午10:22 写入数据库
        pdata = {
            'name': get.main_domain,
            'path': get.site_path,
            'ps': get.remark,
            'status': 1,
            'type_id': 0,
            'project_type': 'proxy',
            'project_config': json.dumps(self._init_proxy_conf),
            'addtime': public.getDate()
        }

        get.pid = public.M('sites').insert(pdata)
        # 2024/6/4 下午4:30 写nginx配置文件
        self.write_nginx_conf(get)

        for domain in get.domain_list:
            public.M('domain').insert({
                'name': domain if ":" not in domain else domain.split(":")[0],
                'pid': str(get.pid),
                'port': '80' if ":" not in domain else domain.split(":")[1],
                'addtime': public.getDate()
            })

        public.writeFile(self._site_proxy_conf_path, json.dumps(self._init_proxy_conf))
        wc_err = public.checkWebConfig()
        if not wc_err is True:
            public.ExecShell("rm -f {}".format(self._site_proxy_conf_path))
            public.ExecShell("rm -rf {}".format(get.filename))
            public.M('sites').where('id=?', (get.pid,)).delete()
            public.M('domain').where('pid=?', (get.pid,)).delete()
            return public.returnResult(
                status=False,
                msg='ERROR: 检测到配置文件有错误,请先排除后再操作<br><br><a style="color:red;">' +
                    wc_err.replace("\n", '<br>') + '</a>'
            )
        if type(wc_err) != bool and "test failed" in wc_err:
            public.ExecShell("rm -f {}".format(self._site_proxy_conf_path))
            public.ExecShell("rm -rf {}".format(get.filename))
            public.M('sites').where('id=?', (get.pid,)).delete()
            public.M('domain').where('pid=?', (get.pid,)).delete()
            return public.returnResult(
                status=False,
                msg='ERROR: 检测到配置文件有错误,请先排除后再操作<br><br><a style="color:red;">' +
                    wc_err.replace("\n", '<br>') + '</a>'
            )

        public.WriteLog('TYPE_SITE', 'SITE_ADD_SUCCESS', (get.site_name,))
        public.set_module_logs('site_proxy', 'create', 1)
        public.serviceReload()
        return public.returnResult(msg="反向代理项目添加成功！")

    def read_json_conf(self, get):
        '''
            @name
            @author wzz <2024/4/18 下午9:53>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        conf_path = "{path}/{site_name}/{site_name}.json".format(
            path=self._proxy_config_path,
            site_name=get.site_name
        )
        try:
            proxy_json_conf = json.loads(public.readFile(conf_path))
        except Exception as e:
            proxy_json_conf = {}

        return proxy_json_conf

    # 2024/4/18 下午9:58 设置全局日志
    def set_global_log(self, get):
        '''
            @name
            @author wzz <2024/4/18 下午9:58>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.log_type = get.get("log_type", "default")
        if not get.log_type in ["default", "file", "rsyslog", "off"]:
            return public.returnResult(status=False, msg="日志类型错误，请传入default/file/rsyslog/off！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        get.proxy_json_conf["proxy_log"]["log_type"] = get.log_type

        if get.log_type == "file":
            get.log_path = get.get("log_path", "")
            if get.log_path == "":
                return public.returnResult(status=False, msg="日志路径不能为空！")
            if not get.log_path.startswith("/"):
                return public.returnResult(status=False, msg="日志路径必须以/开头！")

            get.proxy_json_conf["proxy_log"]["log_path"] = get.log_path
            get.proxy_json_conf["proxy_log"]["log_conf"] = self._init_proxy_conf["proxy_log"]["log_conf"].format(
                log_path=get.log_path,
                site_name=get.site_name
            )
        elif get.log_type == "rsyslog":
            get.log_path = get.get("log_path", "")
            if get.log_path == "":
                return public.returnResult(status=False, msg="日志路径不能为空！")
            site_name = get.site_name.replace(".", "_")
            get.proxy_json_conf["proxy_log"]["log_conf"] = (
                "\n    access_log syslog:server={server_host},nohostname,tag=nginx_{site_name}_access;"
                "\n    error_log syslog:server={server_host},nohostname,tag=nginx_{site_name}_error;"
                .format(
                    server_host=get.log_path,
                    site_name=site_name
                ))
            get.proxy_json_conf["proxy_log"]["rsyslog_host"] = get.log_path
        elif get.log_type == "off":
            get.proxy_json_conf["proxy_log"]["log_conf"] = "\n    access_log off;\n    error_log off;"
        else:
            get.proxy_json_conf["proxy_log"]["log_conf"] = "    " + self._init_proxy_conf["proxy_log"][
                "log_conf"].format(
                log_path=public.get_logs_path(),
                site_name=get.site_name
            )

        update_result = self.update_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        # public.serviceReload()

        return public.returnResult(msg="设置成功！")

    # 2024/4/18 下午10:21 设置basic_auth
    def set_dir_auth(self, get):
        '''
            @name 设置basic_auth
            @param  auth_type: add/edit
                    auth_path: /api
                    username: admin
                    password: admin
            @return:
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.name = get.get("name", "")
        if get.name == "":
            return public.returnResult(status=False, msg="name不能为空！")

        get.auth_path = get.get("auth_path", "")
        if get.auth_path == "":
            return public.returnResult(status=False, msg="auth_path不能为空！")
        if not get.auth_path.startswith("/"):
            return public.returnResult(status=False, msg="auth_path必须以/开头！")

        get.username = get.get("username", "")
        get.password = get.get("password", "")
        if get.username == "" or get.password == "":
            return public.returnResult(status=False, msg="用户名和密码不能为空！")

        if len(get.password) > 8:
            return public.returnResult(status=False, msg="密码不能超过8位，超过的部分无法验证！")

        get.password = public.hasPwd(get.password)

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        # if len(get.proxy_json_conf["basic_auth"]) == 0:
        #     return public.returnResult(status=False, msg="【{}】不存在http认证中，请先添加！".format(get.auth_path))

        auth_file = "/www/server/pass/{site_name}/{name}.htpasswd".format(site_name=get.site_name, name=get.name)
        if not os.path.exists("/www/server/pass"):
            public.ExecShell("mkdir -p /www/server/pass")
        if not os.path.exists("/www/server/pass/{}".format(get.site_name)):
            public.ExecShell("mkdir -p /www/server/pass/{}".format(get.site_name))
        public.writeFile(auth_file, "{}:{}".format(get.username, get.password))

        for i in range(len(get.proxy_json_conf["basic_auth"])):
            if get.proxy_json_conf["basic_auth"][i]["auth_path"] == get.auth_path:
                if get.proxy_json_conf["basic_auth"][i]["auth_name"] == get.name:
                    get.proxy_json_conf["basic_auth"][i]["username"] = get.username
                    get.proxy_json_conf["basic_auth"][i]["password"] = get.password
                    break
        else:
            get.proxy_json_conf["basic_auth"].append({
                "auth_status": True,
                "auth_path": get.auth_path,
                "auth_name": get.name,
                "username": get.username,
                "password": public.hasPwd(get.password),
                "auth_file": auth_file,
            })

        self._site_proxy_conf_path = "{path}/{site_name}/{site_name}.json".format(
            path=self._proxy_config_path,
            site_name=get.site_name
        )
        public.writeFile(self._site_proxy_conf_path, json.dumps(get.proxy_json_conf))

        # public.serviceReload()

        return public.returnResult(msg="设置成功！")

    # 2024/4/22 下午4:17 添加指定网站的basic_auth
    def add_dir_auth(self, get):
        '''
            @name 添加指定网站的basic_auth
            @author wzz <2024/4/22 下午4:17>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.auth_path = get.get("auth_path", "")
        if get.auth_path == "":
            return public.returnResult(status=False, msg="auth_path不能为空！")
        if not get.auth_path.startswith("/"):
            return public.returnResult(status=False, msg="auth_path必须以/开头！")

        get.name = get.get("name", "")
        if get.name == "":
            return public.returnResult(status=False, msg="name不能为空！")

        get.username = get.get("username", "")
        if get.username == "":
            return public.returnResult(status=False, msg="username不能为空！")

        get.password = get.get("password", "")
        if get.password == "":
            return public.returnResult(status=False, msg="password不能为空！")
        if len(get.password) > 8:
            return public.returnResult(status=False, msg="密码不能超过8位，超过的部分无法验证！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        auth_file = "/www/server/pass/{site_name}/{name}.htpasswd".format(site_name=get.site_name, name=get.name)

        auth_conf = {
            "auth_status": True,
            "auth_path": get.auth_path,
            "auth_name": get.name,
            "username": get.username,
            "password": public.hasPwd(get.password),
            "auth_file": auth_file,
        }

        if len(get.proxy_json_conf["basic_auth"]) != 0:
            for i in range(len(get.proxy_json_conf["basic_auth"])):
                if get.proxy_json_conf["basic_auth"][i]["auth_path"] == get.auth_path:
                    return public.returnResult(status=False,
                                               msg="【{}】已存在http认证中，无法重复添加！".format(get.auth_path))

        if not os.path.exists("/www/server/pass"):
            public.ExecShell("mkdir -p /www/server/pass")
        if not os.path.exists("/www/server/pass/{}".format(get.site_name)):
            public.ExecShell("mkdir -p /www/server/pass/{}".format(get.site_name))
        public.writeFile(auth_file, "{}:{}".format(get.username, public.hasPwd(get.password)))

        get.proxy_json_conf["basic_auth"].append(auth_conf)

        update_result = self.update_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])

        return public.returnResult(msg="添加成功！")

    # 2024/4/23 上午9:34 删除指定网站的basic_auth
    def del_dir_auth(self, get):
        '''
            @name 删除指定网站的basic_auth
            @author wzz <2024/4/23 上午9:35>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.auth_path = get.get("auth_path", "")
        if get.auth_path == "":
            return public.returnResult(status=False, msg="auth_path不能为空！")

        get.name = get.get("name", "")
        if get.name == "":
            return public.returnResult(status=False, msg="name不能为空！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        auth_file = "/www/server/pass/{site_name}/{name}.htpasswd".format(site_name=get.site_name, name=get.name)

        panel_port = public.readFile('/www/server/panel/data/port.pl')
        proxy_list = self.get_proxy_list(get)
        if proxy_list["data"][0]["proxy_pass"] == "https://127.0.0.1:{}".format(
                panel_port.strip()) and get.auth_path.strip() == "/":
            return public.returnResult(False, "【{}】是面板的反代，不能删除【/】的http认证！".format(get.site_name))

        if len(get.proxy_json_conf["basic_auth"]) != 0:
            for i in range(len(get.proxy_json_conf["basic_auth"])):
                if get.proxy_json_conf["basic_auth"][i]["auth_path"] == get.auth_path:
                    if get.proxy_json_conf["basic_auth"][i]["auth_name"] == get.name:
                        get.proxy_json_conf["basic_auth"].pop(i)
                        break

        public.ExecShell("rm -f {}".format(auth_file))

        update_result = self.update_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])

        return public.returnResult(msg="删除成功！")

    # 2024/4/18 下午10:26 设置全局gzip
    def set_global_gzip(self, get):
        '''
            @name 设置全局gzip
            @param get:
            @return:
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.gzip_status = get.get("gzip_status/d", 999)
        if get.gzip_status == 999:
            return public.returnResult(status=False, msg="gzip_status不能为空，请传number 1或0！")
        get.gzip_min_length = get.get("gzip_min_length", "10k")
        get.gzip_comp_level = get.get("gzip_comp_level", "6")
        if get.gzip_min_length[0] == "0" or get.gzip_min_length.startswith("-"):
            return public.returnResult(status=False, msg="gzip_min_length参数不合法，请输入大于0的数字！")
        if get.gzip_comp_level == "0" or get.gzip_comp_level.startswith("-"):
            return public.returnResult(status=False, msg="gzip_comp_level参数不合法，请输入大于0的数字！")
        get.gzip_types = get.get(
            "gzip_types",
            "text/plain application/javascript application/x-javascript text/javascript text/css application/xml application/json image/jpeg image/gif image/png font/ttf font/otf image/svg+xml application/xml+rss text/x-js"
        )

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        get.proxy_json_conf["gzip"]["gzip_status"] = True if get.gzip_status == 1 else False
        if get.proxy_json_conf["gzip"]["gzip_status"]:
            get.proxy_json_conf["gzip"]["gzip_status"] = True
            get.proxy_json_conf["gzip"]["gzip_min_length"] = get.gzip_min_length
            get.proxy_json_conf["gzip"]["gzip_comp_level"] = get.gzip_comp_level
            get.proxy_json_conf["gzip"]["gzip_types"] = get.gzip_types
            get.gzip_conf = ("gzip on;"
                             "\n    gzip_min_length {gzip_min_length};"
                             "\n    gzip_buffers 4 16k;"
                             "\n    gzip_http_version 1.1;"
                             "\n    gzip_comp_level {gzip_comp_level};"
                             "\n    gzip_types {gzip_types};"
                             "\n    gzip_vary on;"
                             "\n    gzip_proxied expired no-cache no-store private auth;"
                             "\n    gzip_disable \"MSIE [1-6]\.\";").format(
                gzip_min_length=get.gzip_min_length,
                gzip_comp_level=get.gzip_comp_level,
                gzip_types=get.gzip_types
            )
            get.proxy_json_conf["gzip"]["gzip_conf"] = get.gzip_conf
        else:
            get.proxy_json_conf["gzip"]["gzip_conf"] = ""

        update_result = self.update_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])

        return public.returnResult(msg="设置成功！")

    # 2024/4/18 下午10:27 设置全局缓存
    def set_global_cache(self, get):
        '''
            @name 设置全局缓存
            @param get:
            @return:
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.cache_status = get.get("cache_status/d", 999)
        if get.cache_status == 999:
            return public.returnResult(status=False, msg="cache_status不能为空，请传number 1或0！")

        get.expires = get.get("expires", "1d")
        if get.expires[0] == "0" or get.expires.startswith("-"):
            return public.returnResult(status=False, msg="expires参数不合法，请输入大于0的数字！")
        expires = "expires {}".format(get.expires)

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        static_cache = ("\n    location ~ .*\\.(css|js|jpe?g|gif|png|webp|woff|eot|ttf|svg|ico|css\.map|js\.map)$"
                        "\n    {{"
                        "\n        {expires};"
                        "\n        error_log /dev/null;"
                        "\n        access_log /dev/null;"
                        "\n    }}").format(
            expires=expires,
        )

        cache_conf = ("\n    proxy_cache {cache_zone};"
                      "\n    proxy_cache_key $host$uri$is_args$args;"
                      "\n    proxy_ignore_headers Set-Cookie Cache-Control expires X-Accel-Expires;"
                      "\n    proxy_cache_valid 200 304 301 302 {expires};"
                      "\n    proxy_cache_valid 404 1m;"
                      "{static_cache}").format(
            cache_zone=get.proxy_json_conf["proxy_cache"]["cache_zone"],
            expires=get.expires,
            static_cache=get.proxy_json_conf["proxy_cache"]["static_cache"] if get.proxy_json_conf["proxy_cache"][
                                                                                   "static_cache"] != "" else static_cache
        )

        get.proxy_json_conf["proxy_cache"]["cache_status"] = True if get.cache_status == 1 else False
        if get.proxy_json_conf["proxy_cache"]["cache_status"]:
            get.proxy_json_conf["proxy_cache"]["cache_status"] = True
            get.proxy_json_conf["proxy_cache"]["expires"] = get.expires
            get.proxy_json_conf["proxy_cache"]["cache_conf"] = cache_conf
        else:
            get.proxy_json_conf["proxy_cache"]["cache_status"] = False
            get.proxy_json_conf["proxy_cache"]["cache_conf"] = static_cache

        update_result = self.update_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])

        return public.returnResult(msg="设置成功！")

    # 2024/4/18 下午10:43 设置全局websocket支持
    def set_global_websocket(self, get):
        '''
            @name
            @author wzz <2024/4/19 下午2:37>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.websocket_status = get.get("websocket_status/d", 999)
        if get.websocket_status == 999:
            return public.returnResult(status=False, msg="websocket_status不能为空，请传number 1或0！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        if get.websocket_status == 1:
            get.proxy_json_conf["websocket"]["websocket_status"] = True
        else:
            get.proxy_json_conf["websocket"]["websocket_status"] = False

        update_result = self.update_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])

        return public.returnResult(msg="设置成功！")

    # 2024/4/19 下午2:54 设置备注
    def set_remak(self, get):
        '''
            @name 设置备注
            @param get:
            @return:
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.id = get.get("id", "")
        if get.id == "":
            return public.returnResult(status=False, msg="id不能为空！")

        get.remark = get.get("remark", "")
        get.table = "sites"
        get.ps = get.remark

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        from data import data
        data_obj = data()
        result = data_obj.setPs(get)
        if not result["status"]:
            public.returnResult(status=False, msg=result["msg"])

        get.proxy_json_conf["remark"] = get.remark
        self._site_proxy_conf_path = "{path}/{site_name}/{site_name}.json".format(
            path=self._proxy_config_path,
            site_name=get.site_name
        )
        public.writeFile(self._site_proxy_conf_path, json.dumps(get.proxy_json_conf))

        return public.returnResult(msg=result["msg"])

    # 2024/4/19 下午2:59 添加反向代理
    def add_proxy(self, get):
        '''
            @name
            @author wzz <2024/4/19 下午3:00>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_path = get.get("proxy_path", "")
        if get.proxy_path == "":
            return public.returnResult(status=False, msg="proxy_path不能为空！")

        get.proxy_pass = get.get("proxy_pass", "")
        if get.proxy_pass == "":
            return public.returnResult(status=False, msg="proxy_pass不能为空！")

        get.proxy_host = get.get("proxy_host", "$http_host")
        get.proxy_type = get.get("proxy_type", "http")
        get.remark = get.get("remark", "")
        get.proxy_timeout = "proxy_connect_timeout 60s;\n      proxy_send_timeout 600s;\n      proxy_read_timeout 600s;"

        if get.remark != "":
            get.remark = public.xssencode2(get.remark)
        if get.proxy_type == "unix":
            if not get.proxy_pass.startswith("/"):
                return public.returnResult(status=False, msg="unix文件路径必须以/开头，如/tmp/flask_app.sock！")
            if not get.proxy_pass.endswith(".sock"):
                return public.returnResult(status=False, msg="unix文件必须以.sock结尾，如/tmp/flask_app.sock！")
            if not os.path.exists(get.proxy_pass):
                return public.returnResult(status=False, msg="代理目标不存在！")

            get.proxy_pass = "http://unix:{}".format(get.proxy_pass)
        elif get.proxy_type == "http":
            if not get.proxy_pass.startswith("http://") and not get.proxy_pass.startswith("https://"):
                return public.returnResult(status=False, msg="代理目标必须以http://或https://开头！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        # 2024/4/19 下午3:45 检测是否已经存在proxy_path,有的话就返回错误
        for proxy_info in get.proxy_json_conf["proxy_info"]:
            if proxy_info["proxy_path"] == get.proxy_path:
                return public.returnResult(status=False,
                                           msg="【{}】已存在反向代理中，无法重复添加！".format(get.proxy_path))

        if len(get.proxy_json_conf["basic_auth"]) != 0:
            for i in range(len(get.proxy_json_conf["basic_auth"])):
                if get.proxy_json_conf["basic_auth"][i]["auth_path"] == get.proxy_path:
                    return public.returnResult(status=False, msg="【{}】已存在basicauth中，请先删除再添加反向代理！".format(
                        get.proxy_path))

        sni_conf = ""
        if get.proxy_pass.startswith("https://"):
            sni_conf = "proxy_ssl_server_name on;"
        get.proxy_conf = self._template_proxy_conf.format(
            ip_limit="",
            gzip="",
            proxy_cache="",
            sub_filter="",
            server_log="",
            basic_auth="",
            proxy_pass=get.proxy_pass,
            proxy_host=get.proxy_host,
            proxy_path=get.proxy_path,
            SNI=sni_conf,
            custom_conf="",
            timeout_conf=get.proxy_timeout,
            websocket_support=get.proxy_json_conf["websocket"]["websocket_conf"],
        )

        get.proxy_json_conf["proxy_info"].append({
            "proxy_type": get.proxy_type,
            "proxy_path": get.proxy_path,
            "proxy_pass": get.proxy_pass,
            "proxy_host": get.proxy_host,
            "ip_limit": {
                "ip_black": [],
                "ip_white": [],
            },
            "basic_auth": {},
            "proxy_cache": {
                "cache_status": False,
                "cache_zone": "",
                "static_cache": "",
                "expires": "1d",
                "cache_conf": "",
            },
            "gzip": {
                "gzip_status": False,
                "gzip_min_length": "10k",
                "gzip_comp_level": "6",
                "gzip_types": "text/plain application/javascript application/x-javascript text/javascript text/css application/xml application/json image/jpeg image/gif image/png font/ttf font/otf image/svg+xml application/xml+rss text/x-js",
                "gzip_conf": "gzip on;\n     gzip_min_length 10k;\n     gzip_buffers 4 16k;\n     gzip_http_version 1.1;\n     gzip_comp_level 2;\n     gzip_types text/plain application/javascript application/x-javascript text/javascript text/css application/xml;\n     gzip_vary on;\n     gzip_proxied expired no-cache no-store private auth;\n     gzip_disable \"MSIE [1-6]\.\";",
            },
            "sub_filter": {
                "sub_filter_str": [],
            },
            "websocket": {
                "websocket_status": True,
                "websocket_conf": "proxy_http_version 1.1;\n      proxy_set_header Upgrade $http_upgrade;\n      proxy_set_header Connection $connection_upgrade;",
            },
            "proxy_log": {
                "log_type": "off",
                "log_conf": "",
            },
            "timeout": {
                "proxy_connect_timeout": "60",
                "proxy_send_timeout": "600",
                "proxy_read_timeout": "600",
                "timeout_conf": "proxy_connect_timeout 60s;\n      proxy_send_timeout 600s;\n      proxy_read_timeout 600s;",
            },
            "custom_conf": "",
            "proxy_conf": get.proxy_conf,
            "remark": get.remark,
            "template_proxy_conf": self._template_proxy_conf,
        })

        update_result = self.update_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])

        public.set_module_logs('site_proxy', 'add_proxy', 1)
        return public.returnResult(msg="添加成功！")

    # 2024/4/19 下午9:45 删除指定站点
    def delete(self, get):
        '''
            @name
            @author wzz <2024/4/19 下午9:45>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        get.id = get.get("id", "")
        get.remove_path = get.get("remove_path/d", 0)
        if get.id == "":
            return public.returnResult(status=False, msg="id不能为空！")

        get.reload = get.get("reload/d", 1)

        if public.M('sites').where('id=?', (get.id,)).count() < 1:
            return public.returnResult(status=False, msg='指定站点不存在！')

        site_file = public.get_setup_path() + '/panel/vhost/nginx/' + get.site_name + '.conf'
        if os.path.exists(site_file):
            public.ExecShell('rm -f {}'.format(site_file))
        redirect_dir = public.get_setup_path() + '/panel/vhost/nginx/redirect/' + get.site_name
        if os.path.exists(redirect_dir):
            public.ExecShell('rm -rf {}'.format(redirect_dir))

        logs_file = public.get_logs_path() + '/{}*'.format(get.site_name)
        public.ExecShell('rm -f {}'.format(logs_file))

        self._site_proxy_conf_path = "{path}/{site_name}".format(
            path=self._proxy_config_path,
            site_name=get.site_name
        )
        public.ExecShell('rm -rf {}'.format(self._site_proxy_conf_path))

        if get.remove_path == 1:
            public.ExecShell('rm -rf /www/wwwroot/{}'.format(get.site_name))

        if get.reload == 1:
            public.serviceReload()

        # 从数据库删除
        public.M('sites').where("id=?", (get.id,)).delete()
        public.M('domain').where("pid=?", (get.id,)).delete()
        public.WriteLog('TYPE_SITE', "SITE_DEL_SUCCESS", (get.site_name,))
        if os.path.exists("/www/server/panel/vhost/nginx/extension/{}/".format(get.site_name)):
            import shutil
            shutil.rmtree("/www/server/panel/vhost/nginx/extension/{}/".format(get.site_name))

        return public.returnResult(msg="反向代理项目删除成功！")

    # 2024/5/28 上午9:50 批量删除站点
    def batch_delete(self, get):
        '''
            @name 批量删除站点
            @author wzz <2024/5/28 上午9:51>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_list = get.get("site_list", [])
        get.remove_path = get.get("remove_path/d", 0)
        get.reload = get.get("reload/d", 0)

        try:
            site_list = json.loads(get.site_list)
        except:
            return public.returnResult(False, "请传入需要删除的网站列表!")

        acc_list = []
        for site in site_list:
            args = public.dict_obj()
            args.site_name = site["site_name"]
            args.remove_path = get.remove_path
            args.reload = get.reload
            args.id = site["id"]
            de_result = self.delete(args)
            if not de_result["status"]:
                acc_list.append({"site_name": site["site_name"], "status": False})
                continue

            acc_list.append({"site_name": site["site_name"], "status": True})

        public.serviceReload()

        return public.returnResult(True, msg="批量删除站点成功！", data=acc_list)

    # 2024/4/26 下午4:57 获取证书的部署状态
    def get_site_ssl_info(self, siteName):
        '''
            @name 获取证书的部署状态
            @author wzz <2024/4/26 下午4:58>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            import time
            import re
            s_file = 'vhost/nginx/{}.conf'.format(siteName)
            is_apache = False
            if not os.path.exists(s_file):
                s_file = 'vhost/apache/{}.conf'.format(siteName)
                is_apache = True

            if not os.path.exists(s_file):
                return -1

            s_conf = public.readFile(s_file)
            if not s_conf: return -1
            ssl_file = None
            if is_apache:
                if s_conf.find('SSLCertificateFile') == -1:
                    return -1
                s_tmp = re.findall(r"SSLCertificateFile\s+(.+\.pem)", s_conf)
                if not s_tmp: return -1
                ssl_file = s_tmp[0]
            else:
                if s_conf.find('ssl_certificate') == -1:
                    return -1
                s_tmp = re.findall(r"ssl_certificate\s+(.+\.pem);", s_conf)
                if not s_tmp: return -1
                ssl_file = s_tmp[0]
            ssl_info = public.get_cert_data(ssl_file)
            if not ssl_info: return -1
            ssl_info['endtime'] = int(
                int(time.mktime(time.strptime(ssl_info['notAfter'], "%Y-%m-%d")) - time.time()) / 86400)
            return ssl_info
        except:
            return -1

    # 2024/4/19 下午10:05 获取所有project_type为proxy的站点，需要做分页配置，按照添加时间排序
    def get_list(self, get):
        '''
            @name 获取所有project_type为proxy的站点，需要做分页配置，按照添加时间排序
            @param get:
            @return:
        '''
        get.p = get.get("p/d", 1)
        get.limit = get.get("limit/d", 10)
        get.search = get.get("search", "")

        where = "project_type=?"
        if get.search != "":
            where += " and name like ?"
            param = ("proxy", "%{}%".format(get.search))
        else:
            param = ("proxy",)

        import db
        sql = db.Sql()
        count = sql.table('sites').where(where, param).count()

        import page
        page = page.Page()
        data = {}
        info = {}
        info['count'] = count
        info['row'] = get.limit

        info['p'] = 1
        if hasattr(get, 'p'):
            info['p'] = int(get['p'])
            if info['p'] < 1: info['p'] = 1

        try:
            from flask import request
            info['uri'] = public.url_encode(request.full_path)
        except:
            info['uri'] = ''
        info['return_js'] = ''
        data['where'] = where
        data['page'] = page.GetPage(info)

        sql.table('sites').where(where, param)
        sql.field('id,name,path,status,ps,addtime,edate,rname').order('id desc')
        sql.limit(str(page.SHIFT) + ',' + str(page.ROW))
        data['data'] = sql.select()

        btwaf_path = '/www/server/btwaf'

        try:
            config = json.loads(public.readFile(os.path.join(btwaf_path, 'config.json')))
        except:
            config = {}

        try:
            waf_res = json.loads(public.readFile(os.path.join(btwaf_path, "site.json")))
        except:
            waf_res = {}

        for site in data['data']:
            get.site_name = site["name"]
            project_config = self.read_json_conf(get)
            site["healthy"] = 1
            site["waf"] = {}
            if not project_config:
                site["healthy"] = 0
                site["conf_path"] = ""
                site["ssl"] = -1
                site["proxy_pass"] = ""
                continue

            site["conf_path"] = public.get_setup_path() + '/panel/vhost/nginx/' + get.site_name + '.conf'
            site["ssl"] = self.get_site_ssl_info(get.site_name)
            site["proxy_pass"] = "--" if not project_config["proxy_info"] else project_config["proxy_info"][0]["proxy_pass"]

            if not config:
                site["waf"] = {"status": False}

            if "open" in config:
                if not config["open"]:
                    site["waf"] = {"status": False}
                    continue

            if waf_res:
                for waf in waf_res:
                    if waf != site["name"]: continue
                    if "open" in waf_res[waf]:
                        site["waf"] = {"status": waf_res[waf]["open"]}
                        break

        return public.returnResult(data=data)

    # 2024/4/19 下午11:46 给指定网站添加域名
    def add_domain(self, get):
        '''
            @name
            @author wzz <2024/4/19 下午11:46>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")
        get.id = get.get("id", "")
        if get.id == "":
            return public.returnResult(status=False, msg="id不能为空！")
        get.domains = get.get("domains", "")
        if get.domains == "":
            return public.returnResult(status=False, msg="domains不能为空！")
        if "," in get.domains:
            return public.returnResult(status=False, msg="域名不能包含逗号！")

        get.domain_list = get.domains.strip().replace(' ', '').split("\n")
        public.check_domain_cloud(get.domain_list[0])
        get.domain = ",".join(get.domain_list)
        get.webname = get.site_name
        port_list = []
        for domain in get.domain_list:
            if not ":" in domain.strip():
                continue

            d_port = domain.strip().split(":")[1]
            if not public.checkPort(d_port):
                return public.returnResult(status=False, msg='域名【{}】的端口号不合法！'.format(domain))

            port_list.append(d_port)

        # 2024/4/20 上午12:02 更新json文件
        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        get.proxy_json_conf["domain_list"].extend(get.domain_list)
        get.proxy_json_conf["site_port"].extend(port_list)

        self._site_proxy_conf_path = "{path}/{site_name}/{site_name}.json".format(
            path=self._proxy_config_path,
            site_name=get.site_name
        )
        public.writeFile(self._site_proxy_conf_path, json.dumps(get.proxy_json_conf))

        from panelSite import panelSite
        result = panelSite().AddDomain(get)
        return public.returnResult(status=True, data=result["domains"])

    # 2024/4/20 上午12:07 删除指定网站的某个域名
    def del_domain(self, get):
        '''
            @name
            @author wzz <2024/4/20 上午12:07>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.id = get.get("id", "")
        if get.id == "":
            return public.returnResult(status=False, msg="id不能为空！")
        get.port = get.get("port", "")
        if get.port == "":
            return public.returnResult(status=False, msg="port不能为空！")
        get.domain = get.get("domain", "").split(":")[0]
        if get.domain == "":
            return public.returnResult(status=False, msg="domain不能为空！")
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.webname = get.site_name
        site_info = public.M("sites").where("name=?", (get.site_name,)).find()
        if not site_info:
            return public.returnResult(status=False, msg="网站不存在！")

        # 2024/4/20 上午12:02 更新json文件
        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        if len(get.proxy_json_conf["domain_list"]) == 1:
            return public.returnResult(status=False, msg="至少保留一个域名！")

        while get.domain in get.proxy_json_conf["domain_list"]:
            get.proxy_json_conf["domain_list"].remove(get.domain)
        if get.port in get.proxy_json_conf["site_port"] and len(get.proxy_json_conf["site_port"]) != 1:
            while get.port in get.proxy_json_conf["site_port"]:
                get.proxy_json_conf["site_port"].remove(get.port)

        self._site_proxy_conf_path = "{path}/{site_name}/{site_name}.json".format(
            path=self._proxy_config_path,
            site_name=get.site_name
        )
        public.writeFile(self._site_proxy_conf_path, json.dumps(get.proxy_json_conf))

        from panelSite import panelSite
        if ":" in get.domain:
            domain, port = get.domain.split(":")
            get.port = port
            get.domain = domain
        get.id = site_info["id"]
        result = panelSite().DelDomain(get)
        return public.returnResult(status=result["status"], msg=result["msg"])

    # 2024/4/20 上午12:20 批量删除指定网站域名
    def batch_del_domain(self, get):
        '''
            @name 批量删除指定网站域名
            @param get:
            @return:
        '''
        get.id = get.get("id", "")
        if get.id == "":
            return public.returnResult(status=False, msg="id不能为空！")
        get.domains = get.get("domains", "")
        if get.domains == "":
            return public.returnResult(status=False, msg="domains不能为空！")
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.webname = get.site_name

        # 2024/4/20 上午12:02 更新json文件
        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        # if len(get.proxy_json_conf["domain_list"]) == 1:
        #     return public.returnResult(status=False, msg="至少保留一个域名！")

        get.domain_list = get.domains.strip().replace(' ', '').split("\n")

        # if len(get.domain_list) == len(get.proxy_json_conf["domain_list"]):
        #     return public.returnResult(status=False, msg="至少保留一个域名！")

        for domain in get.domain_list:
            while domain in get.proxy_json_conf["domain_list"]:
                get.proxy_json_conf["domain_list"].remove(domain)

            if ":" in domain:
                port = domain.split(":")[1]
                if len(get.proxy_json_conf["site_port"]) == 1:
                    continue

                while port in get.proxy_json_conf["site_port"]:
                    get.proxy_json_conf["site_port"].remove(port)

        self._site_proxy_conf_path = "{path}/{site_name}/{site_name}.json".format(
            path=self._proxy_config_path,
            site_name=get.site_name
        )
        public.writeFile(self._site_proxy_conf_path, json.dumps(get.proxy_json_conf))

        from panelSite import panelSite
        res_domains = []
        for domain in get.domain_list:
            get.domain = domain
            get.port = "80"
            if ":" in domain:
                get.port = domain.split(":")[1]
            result = panelSite().DelDomain(get)
            res_domains.append({"name": domain, "status": result["status"], "msg": result["msg"]})

        public.serviceReload()
        return public.returnResult(status=True, data=res_domains)

    # 2024/4/20 上午9:17 获取域名列表和https端口
    def get_domain_list(self, get):
        '''
            @name 获取域名列表和https端口
            @param get:
            @return:
        '''
        get.id = get.get("id", "")
        if get.id == "":
            return public.returnResult(status=False, msg="id不能为空！")
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.siteName = get.webname = get.site_name
        get.table = "domain"
        get.list = True
        get.search = get.id

        # 2024/4/20 上午12:02 更新json文件
        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        result_data = {}
        import data
        dataObject = data.data()
        result_data["domain_list"] = dataObject.getData(get)
        if get.proxy_json_conf["ssl_info"]["ssl_status"]:
            if not "https_port" in get.proxy_json_conf or get.proxy_json_conf["https_port"] == "":
                get.proxy_json_conf["https_port"] = "443"
            result_data["https_port"] = get.proxy_json_conf["https_port"]
        else:
            result_data["https_port"] = "未开启HTTPS"

            # 2024/4/20 上午9:21 domain_list里面没有的域名健康状态显示为0
        for domain in result_data["domain_list"]:
            domain["healthy"] = 1
            if domain["name"] not in get.proxy_json_conf["domain_list"]:
                domain["healthy"] = 0

        return public.returnResult(data=result_data)

    # 2024/4/20 下午2:22 获取配置文件
    def get_config(self, get):
        '''
            @name
            @author wzz <2024/4/20 下午2:22>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        site_conf = public.readFile(public.get_setup_path() + '/panel/vhost/nginx/' + get.site_name + '.conf')
        ssl_conf = get.proxy_json_conf["ssl_info"]["ssl_conf"].format(
            site_name=get.site_name,
        )
        if get.proxy_json_conf["ssl_info"]["force_https"]:
            ssl_conf = get.proxy_json_conf["ssl_info"]["force_ssl_conf"].format(
                site_name=get.site_name,
                force_conf=get.proxy_json_conf["ssl_info"]["force_ssl_conf"],
            )

        if "如果反代网站访问异常且这里已经配置了内容，请优先排查此处的配置是否正确" in get.proxy_json_conf["http_block"]:
            http_block = get.proxy_json_conf["http_block"]
        else:
            http_block = '''# 可设置server|upstream|map等所有http字段，如：
# server {{
#     listen 10086;
#     server_name ...
# }}
# upstream stream_ser {{
#     server back_test.com;
#     server ...
# }}
{default_describe}
{http_block}'''.format(
                default_describe=self._init_proxy_conf["default_describe"],
                http_block=get.proxy_json_conf["http_block"],
            )

        if "如果反代网站访问异常且这里已经配置了内容，请优先排查此处的配置是否正确" in get.proxy_json_conf[
            "server_block"]:
            server_block = get.proxy_json_conf["server_block"]
        else:
            server_block = '''# 可设置server|location等所有server字段，如：
# location /web {{
#     try_files $uri $uri/ /index.php$is_args$args;
# }}
# error_page 404 /diy_404.html;
{default_describe}
{server_block}'''.format(
                default_describe=self._init_proxy_conf["default_describe"],
                server_block=get.proxy_json_conf["server_block"],
            )

        data = {
            "site_conf": site_conf if not site_conf is False else "",
            "http_block": http_block,
            "server_block": server_block,
            "ssl_conf": ssl_conf,
        }

        return public.returnResult(data=data)

    # 2024/4/20 下午2:38 保存配置文件
    def save_config(self, get):
        '''
            @name 保存配置文件
            @param get:
            @return:
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.conf_type = get.get("conf_type", "")
        if get.conf_type == "":
            return public.returnResult(status=False, msg="conf_type不能为空！")

        get.body = get.get("body", "")
        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        if get.conf_type == "http_block":
            get.proxy_json_conf["http_block"] = get.body
        else:
            get.proxy_json_conf["server_block"] = get.body

        update_result = self.update_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="保存成功！")

    # 2024/4/20 下午3:11 根据proxy_json_conf，填入self._template_conf，然后生成nginx配置，保存到指定网站的conf文件中
    def generate_config(self, get):
        """
            @name 根据proxy_json_conf，填入self._template_conf，然后生成nginx配置，保存到指定网站的conf文件中
            @param get:
            @return:
        """
        # 2024/4/20 下午3:36 构造ip黑白名单
        ip_black = ""
        ip_white = ""
        for ip in get.proxy_json_conf["ip_limit"]["ip_black"]:
            ip_black += ("deny {};\n    ").format(ip)
        for ip in get.proxy_json_conf["ip_limit"]["ip_white"]:
            ip_white += ("allow {};\n    ").format(ip)

        if ip_white != "":
            ip_white += "deny all;"
        ip_limit_conf = ip_black + "\n    " + ip_white

        proxy_conf = ""
        ignore_path = []
        if len(get.proxy_json_conf["proxy_info"]) != 0:
            for info in get.proxy_json_conf["proxy_info"]:
                proxy_auth_conf = ""
                if info["basic_auth"]:
                    proxy_auth_conf = ("auth_basic \"Authorization\";"
                                       "\n      auth_basic_user_file {auth_file};").format(
                        auth_path=info["basic_auth"]["auth_path"],
                        auth_file=info["basic_auth"]["auth_file"],
                    )

                if len(get.proxy_json_conf["basic_auth"]) != 0:
                    for auth in get.proxy_json_conf["basic_auth"]:
                        if info["proxy_path"] == auth["auth_path"]:
                            ignore_path.append(auth["auth_path"])
                            proxy_auth_conf = ("auth_basic \"Authorization\";"
                                               "\n      auth_basic_user_file {auth_file};").format(
                                auth_path=auth["auth_path"],
                                auth_file=auth["auth_file"],
                            )
                            break

                p_ip_black = ""
                p_ip_white = ""
                for ip in info["ip_limit"]["ip_black"]:
                    p_ip_black += ("deny {};\n    ").format(ip)
                for ip in info["ip_limit"]["ip_white"]:
                    p_ip_white += ("allow {};\n    ").format(ip)

                if p_ip_white != "":
                    p_ip_white += "deny all;"
                p_ip_limit_conf = p_ip_black + "\n    " + p_ip_white

                if p_ip_black == "" and p_ip_white == "":
                    p_ip_limit_conf = ""

                p_gzip_conf = ""
                if info["gzip"]["gzip_status"]:
                    p_gzip_conf = info["gzip"]["gzip_conf"]

                p_sub_filter = ""
                if len(info["sub_filter"]["sub_filter_str"]) != 0:
                    p_sub_filter = 'proxy_set_header Accept-Encoding \"\";'
                    if not "subs_filter" in get.proxy_json_conf:
                        get.proxy_json_conf["subs_filter"] = \
                            public.ExecShell("nginx -V 2>&1|grep 'ngx_http_substitutions_filter' -o")[0] != ""

                    if not get.proxy_json_conf["subs_filter"]:
                        for filter in info["sub_filter"]["sub_filter_str"]:
                            p_sub_filter += "\n      sub_filter {oldstr} {newstr};".format(
                                oldstr=filter["oldstr"] if filter["oldstr"] != "" else "\"\"",
                                newstr=filter["newstr"] if filter["newstr"] != "" else "\"\"",
                            )

                        p_sub_filter += "\n      sub_filter_once off;"
                    else:
                        for filter in info["sub_filter"]["sub_filter_str"]:
                            p_sub_filter += "\n     subs_filter {oldstr} {newstr} {sub_type};".format(
                                oldstr=filter["oldstr"] if filter["oldstr"] != "" else "\"\"",
                                newstr=filter["newstr"] if filter["newstr"] != "" else "\"\"",
                                sub_type=filter["sub_type"] if "sub_type" in filter and filter[
                                    "sub_type"] != "" else "\"\"",
                            )

                p_websocket_support = ""
                if info["websocket"]["websocket_status"]:
                    p_websocket_support = info["websocket"]["websocket_conf"]

                timeout_conf = ("proxy_connect_timeout {proxy_connect_timeout};"
                                "\n    proxy_send_timeout {proxy_send_timeout};"
                                "\n    proxy_read_timeout {proxy_read_timeout};").format(
                    proxy_connect_timeout=info["timeout"]["proxy_connect_timeout"].replace("s", "") + "s",
                    proxy_send_timeout=info["timeout"]["proxy_send_timeout"].replace("s", "") + "s",
                    proxy_read_timeout=info["timeout"]["proxy_read_timeout"].replace("s", "") + "s",
                )

                sni_conf = ""
                if info["proxy_pass"].startswith("https://"):
                    sni_conf = "proxy_ssl_server_name on;"

                tmp_conf = info["template_proxy_conf"].format(
                    basic_auth=proxy_auth_conf,
                    ip_limit=p_ip_limit_conf,
                    gzip=p_gzip_conf,
                    sub_filter=p_sub_filter,
                    proxy_cache=info["proxy_cache"]["cache_conf"],
                    server_log="",
                    proxy_pass=info["proxy_pass"],
                    proxy_host=info["proxy_host"],
                    proxy_path=info["proxy_path"],
                    custom_conf=info["custom_conf"],
                    timeout_conf=timeout_conf,
                    websocket_support=p_websocket_support,
                    SNI=sni_conf,
                )
                info["proxy_conf"] = tmp_conf
                proxy_conf += tmp_conf + "\n    "

        # 2024/4/20 下午3:37 构造basicauth
        auth_conf = ""
        if len(get.proxy_json_conf["basic_auth"]) != 0:
            for auth in get.proxy_json_conf["basic_auth"]:
                if auth["auth_path"] not in ignore_path:
                    tmp_conf = ("location ^~ {auth_path} {{"
                                "\n    auth_basic \"Authorization\";"
                                "\n    auth_basic_user_file {auth_file};"
                                "\n    }}").format(auth_path=auth["auth_path"], auth_file=auth["auth_file"])
                    auth_conf += tmp_conf + "\n    "

        websocket_support = ""
        if get.proxy_json_conf["websocket"]["websocket_status"]:
            websocket_support = get.proxy_json_conf["websocket"]["websocket_conf"]

        gzip_conf = ""
        if get.proxy_json_conf["gzip"]["gzip_status"]:
            gzip_conf = get.proxy_json_conf["gzip"]["gzip_conf"]

        ssl_conf = "#error_page 404/404.html;"
        # listen_port = " ".join(get.proxy_json_conf["site_port"])
        # listen_ipv6 = "\n    listen [::]:{};".format(" ".join(get.proxy_json_conf["site_port"]))
        # port_conf = get.proxy_json_conf["port_conf"].format(
        #     listen_port=listen_port,
        #     listen_ipv6=listen_ipv6,
        # )
        if not "https_port" in get.proxy_json_conf or get.proxy_json_conf["https_port"] == "":
            get.proxy_json_conf["https_port"] = "443"
        if not "ipv4_port_conf" in get.proxy_json_conf:
            get.proxy_json_conf["ipv4_port_conf"] = "listen {listen_port};"
        if not "ipv6_port_conf" in get.proxy_json_conf:
            get.proxy_json_conf["ipv6_port_conf"] = "listen [::]:{listen_port};"
        if not "ipv4_http3_ssl_port_conf" in get.proxy_json_conf:
            get.proxy_json_conf[
                "ipv4_http3_ssl_port_conf"] = "{ipv4_port_conf}\n    listen {https_port} quic;\n    listen {https_port} ssl;"
        if not "ipv6_http3_ssl_port_conf" in get.proxy_json_conf:
            get.proxy_json_conf[
                "ipv6_http3_ssl_port_conf"] = "{ipv6_port_conf}\n    listen [::]:{https_port} quic;\n    listen [::]:{https_port} ssl ;"
        if not "ipv4_ssl_port_conf" in get.proxy_json_conf:
            get.proxy_json_conf["ipv4_ssl_port_conf"] = "{ipv4_port_conf}\n    listen {https_port} ssl http2 ;"
        if not "ipv6_ssl_port_conf" in get.proxy_json_conf:
            get.proxy_json_conf["ipv6_ssl_port_conf"] = "{ipv6_port_conf}\n    listen [::]:{https_port} ssl http2 ;"

        ipv4_port_conf = ""
        ipv6_port_conf = ""
        for p in get.proxy_json_conf["site_port"]:
            ipv4_port_conf += get.proxy_json_conf["ipv4_port_conf"].format(
                listen_port=p,
            ) + "\n    "
            ipv6_port_conf += get.proxy_json_conf["ipv6_port_conf"].format(
                listen_port=p,
            ) + "\n    "
        if get.proxy_json_conf["ssl_info"]["ssl_status"]:
            if public.ExecShell("nginx -V 2>&1| grep 'http_v3_module' -o")[0] != "":
                ipv4_http3_ssl_port_conf = get.proxy_json_conf["ipv4_http3_ssl_port_conf"].format(
                    ipv4_port_conf=ipv4_port_conf,
                    https_port=get.proxy_json_conf["https_port"],
                ) + "\n    "
                ipv6_http3_ssl_port_conf = get.proxy_json_conf["ipv6_http3_ssl_port_conf"].format(
                    ipv6_port_conf=ipv6_port_conf,
                    https_port=get.proxy_json_conf["https_port"],
                ) + "\n    "
                port_conf = ipv4_http3_ssl_port_conf + ipv6_http3_ssl_port_conf + "\n    http2 on;"
            else:
                ipv4_ssl_port_conf = get.proxy_json_conf["ipv4_ssl_port_conf"].format(
                    ipv4_port_conf=ipv4_port_conf,
                    https_port=get.proxy_json_conf["https_port"],
                ) + "\n    "
                ipv6_ssl_port_conf = get.proxy_json_conf["ipv6_ssl_port_conf"].format(
                    ipv6_port_conf=ipv6_port_conf,
                    https_port=get.proxy_json_conf["https_port"],
                ) + "\n    "
                port_conf = ipv4_ssl_port_conf + ipv6_ssl_port_conf
            ssl_conf = get.proxy_json_conf["ssl_info"]["ssl_conf"].format(site_name=get.site_name)
            if get.proxy_json_conf["ssl_info"]["force_https"]:
                ssl_conf = get.proxy_json_conf["ssl_info"]["force_ssl_conf"].format(
                    site_name=get.site_name,
                    force_conf=get.proxy_json_conf["ssl_info"]["force_conf"]
                )
        else:
            port_conf = ipv4_port_conf + "\n" + ipv6_port_conf

        redirect_conf = ""
        if get.proxy_json_conf["redirect"]["redirect_status"]:
            redirect_conf = get.proxy_json_conf["redirect"]["redirect_conf"].format(site_name=get.site_name)

        security_conf = ""
        if get.proxy_json_conf["security"]["security_status"]:
            domains = get.proxy_json_conf["security"]["domains"] if not get.proxy_json_conf["security"][
                "http_status"] else "none blocked " + get.proxy_json_conf["security"]["domains"]
            security_conf = get.proxy_json_conf["security"]["security_conf"].format(
                static_resource=get.proxy_json_conf["security"]["static_resource"],
                expires="30d",
                domains=domains.replace(",", " "),
                return_resource=get.proxy_json_conf["security"]["return_resource"],
            )

        default_cache = get.proxy_json_conf["default_cache"].format(
            site_name=get.site_name,
            cache_name=get.site_name.replace(".", "_")
        )
        get.http_block = default_cache + "\n" + get.proxy_json_conf["http_block"]

        # 2024/6/4 下午4:20 兼容新版监控报表的配置
        monitor_conf = ""
        if (os.path.exists("/www/server/panel/plugin/monitor/monitor_main.py") and
                os.path.exists("/www/server/monitor/config/sites.json")):
            try:
                sites_data = json.loads(public.readFile("/www/server/monitor/config/sites.json"))

                if sites_data[get.site_name]["open"]:
                    id = public.M('sites').where("name=?", (get.site_name,)).getField('id')
                    monitor_conf = '''#Monitor-Config-Start 网站监控报表日志发送配置
    access_log syslog:server=unix:/tmp/bt-monitor.sock,nohostname,tag={sid}__access monitor;
    error_log syslog:server=unix:/tmp/bt-monitor.sock,nohostname,tag={sid}__error;
    #Monitor-Config-End'''.format(sid=id)
            except:
                pass
        if not os.path.exists("/www/server/panel/vhost/nginx/extension/{}/".format(get.site_name)):
            os.makedirs("/www/server/panel/vhost/nginx/extension/{}/".format(get.site_name), 0o600)
        get.site_conf = self._template_conf.format(
            http_block=get.http_block,
            server_block=get.proxy_json_conf["server_block"],
            port_conf=port_conf,
            ssl_start_msg=public.getMsg('NGINX_CONF_MSG1'),
            err_page_msg=public.getMsg('NGINX_CONF_MSG2'),
            php_info_start=public.getMsg('NGINX_CONF_MSG3'),
            rewrite_start_msg=public.getMsg('NGINX_CONF_MSG4'),
            domains=' '.join(get.proxy_json_conf["domain_list"]) if len(
                get.proxy_json_conf["domain_list"]) > 1 else get.site_name,
            site_name=get.site_name,
            ssl_info=ssl_conf,
            err_age_404=get.proxy_json_conf["err_age_404"],
            err_age_502=get.proxy_json_conf["err_age_502"],
            ip_limit_conf=ip_limit_conf,
            auth_conf=auth_conf,
            sub_filter="",
            gzip_conf=gzip_conf,
            security_conf=security_conf,
            redirect_conf=redirect_conf,
            proxy_conf=proxy_conf,
            proxy_cache=get.proxy_json_conf["proxy_cache"]["cache_conf"],
            server_log=get.proxy_json_conf["proxy_log"]["log_conf"],
            site_path=get.proxy_json_conf["site_path"],
            websocket_support=websocket_support,
            monitor_conf=monitor_conf,
        )

    # 2024/4/21 下午10:46 设置商业ssl证书
    def set_cert(self, get):
        '''
            @name
            @author wzz <2024/4/21 下午10:46>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.oid = get.get("oid", "")
        if get.oid == "":
            return public.returnResult(status=False, msg="oid不能为空！")

        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.siteName = get.site_name

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        from panelSSL import panelSSL
        ssl_obj = panelSSL()
        set_result = ssl_obj.set_cert(get)
        if set_result["status"] == False:
            return set_result

        get.proxy_json_conf["ssl_info"]["ssl_status"] = True
        get.proxy_json_conf["https_port"] = "443"

        self._site_proxy_conf_path = "{path}/{site_name}/{site_name}.json".format(
            path=self._proxy_config_path,
            site_name=get.site_name
        )
        public.writeFile(self._site_proxy_conf_path, json.dumps(get.proxy_json_conf))

        return set_result

    # 2024/4/21 下午11:03 关闭SSl证书
    def close_ssl(self, get):
        '''
            @name
            @author wzz <2024/4/21 下午11:04>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.siteName = get.site_name

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        from panelSite import panelSite
        result = panelSite().CloseSSLConf(get)
        if not result["status"]:
            return result

        get.proxy_json_conf["ssl_info"]["ssl_status"] = False
        get.proxy_json_conf["https_port"] = "443"

        self._site_proxy_conf_path = "{path}/{site_name}/{site_name}.json".format(
            path=self._proxy_config_path,
            site_name=get.site_name
        )
        public.writeFile(self._site_proxy_conf_path, json.dumps(get.proxy_json_conf))

        return result

    # 2024/4/21 下午11:10 保存指定网站的SSL证书
    def set_ssl(self, get):
        '''
            @name 保存指定网站的SSL证书
            @author wzz <2024/4/21 下午11:12>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.key = get.get("key", "")
        if get.key == "":
            return public.returnResult(status=False, msg="key不能为空！")

        get.csr = get.get("csr", "")
        if get.csr == "":
            return public.returnResult(status=False, msg="csr不能为空！")

        get.siteName = get.site_name
        get.type = -1

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        from panelSite import panelSite
        result = panelSite().SetSSL(get)
        if not result["status"]:
            # return public.returnResult(status=False, msg=result["msg"])
            return result

        get.proxy_json_conf["ssl_info"]["ssl_status"] = True
        get.proxy_json_conf["https_port"] = "443"

        self._site_proxy_conf_path = "{path}/{site_name}/{site_name}.json".format(
            path=self._proxy_config_path,
            site_name=get.site_name
        )
        public.writeFile(self._site_proxy_conf_path, json.dumps(get.proxy_json_conf))

        return result

    # 2024/4/21 下午11:29 部署测试证书
    def set_test_cert(self, get):
        '''
            @name
            @author wzz <2024/4/21 下午11:30>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.partnerOrderId = get.get("partnerOrderId", "")
        if get.partnerOrderId == "":
            return public.returnResult(status=False, msg="partnerOrderId不能为空！")

        get.siteName = get.site_name

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        from panelSSL import panelSSL
        ssl_obj = panelSSL()
        set_result = ssl_obj.GetSSLInfo(get)
        if set_result["status"] == False:
            return set_result

        get.proxy_json_conf["ssl_info"]["ssl_status"] = True
        get.proxy_json_conf["https_port"] = "443"

        self._site_proxy_conf_path = "{path}/{site_name}/{site_name}.json".format(
            path=self._proxy_config_path,
            site_name=get.site_name
        )
        public.writeFile(self._site_proxy_conf_path, json.dumps(get.proxy_json_conf))

        return set_result

    # 2024/4/21 下午11:33 申请let' encrypt证书
    def apply_cert_api(self, get):
        '''
            @name
            @author wzz <2024/4/21 下午11:34>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.domains = get.get("domains", "")
        if get.domains == "":
            return public.returnResult(status=False, msg="domains不能为空！")

        get.auth_type = get.get("auth_type", "")
        if get.auth_type == "":
            return public.returnResult(status=False, msg="auth_type不能为空！")

        get.auth_to = get.get("auth_to", "")
        if get.auth_to == "":
            return public.returnResult(status=False, msg="auth_to不能为空！")

        get.auto_wildcard = get.get("auto_wildcard", "")
        if get.auto_wildcard == "":
            return public.returnResult(status=False, msg="auto_wildcard不能为空！")

        get.id = get.get("id", "")
        if get.id == "":
            return public.returnResult(status=False, msg="id不能为空！")

        get.siteName = get.site_name

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        from acme_v2 import acme_v2
        acme = acme_v2()
        result = acme.apply_cert_api(get)
        if not result["status"]:
            return result

        get.proxy_json_conf["ssl_info"]["ssl_status"] = True
        get.proxy_json_conf["https_port"] = "443"

        self._site_proxy_conf_path = "{path}/{site_name}/{site_name}.json".format(
            path=self._proxy_config_path,
            site_name=get.site_name
        )
        public.writeFile(self._site_proxy_conf_path, json.dumps(get.proxy_json_conf))

        return result

    # 2024/4/21 下午11:36 验证let' encrypt dns
    def apply_dns_auth(self, get):
        '''
            @name
            @author wzz <2024/4/21 下午11:36>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.index = get.get("index", "")
        if get.index == "":
            return public.returnResult(status=False, msg="index不能为空！")

        from acme_v2 import acme_v2
        acme = acme_v2()
        return acme.apply_dns_auth(get)

    # 2024/4/21 下午11:44 设置证书夹里面的证书
    def SetBatchCertToSite(self, get):
        '''
            @name
            @author wzz <2024/4/21 下午11:44>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.BatchInfo = get.get("BatchInfo", "")
        if get.BatchInfo == "":
            return public.returnResult(status=False, msg="BatchInfo不能为空！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        from panelSSL import panelSSL
        ssl_obj = panelSSL()
        set_result = ssl_obj.SetBatchCertToSite(get)
        if not "successList" in set_result:
            return set_result

        for re in set_result["successList"]:
            if re["status"] and re["siteName"] == get.site_name:
                get.proxy_json_conf["ssl_info"]["ssl_status"] = True
                break

        self._site_proxy_conf_path = "{path}/{site_name}/{site_name}.json".format(
            path=self._proxy_config_path,
            site_name=get.site_name
        )
        public.writeFile(self._site_proxy_conf_path, json.dumps(get.proxy_json_conf))

        return set_result

    # 2024/4/22 上午9:43 设置强制https
    def set_force_https(self, get):
        '''
            @name 设置强制https
            @param get:
                    site_name: 网站名
                    force_https: 1/0
            @return:
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.force_https = get.get("force_https/d", 999)
        if get.force_https == 999:
            return public.returnResult(status=False, msg="force_https不能为空！")

        get.siteName = get.site_name

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        get.proxy_json_conf["ssl_info"]["force_https"] = True if get.force_https == 1 else False

        from panelSite import panelSite
        if get.force_https == 1:
            result = panelSite().HttpToHttps(get)
        else:
            result = panelSite().CloseToHttps(get)

        if not result["status"]:
            return result

        self._site_proxy_conf_path = "{path}/{site_name}/{site_name}.json".format(
            path=self._proxy_config_path,
            site_name=get.site_name
        )
        public.writeFile(self._site_proxy_conf_path, json.dumps(get.proxy_json_conf))

        return result

    # 2024/4/22 上午10:27 创建重定向
    def CreateRedirect(self, get):
        '''
            @name
            @author wzz <2024/4/22 上午10:27>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.domainorpath = get.get("domainorpath", "")
        if get.domainorpath == "":
            return public.returnResult(status=False, msg="domainorpath不能为空！")

        get.redirecttype = get.get("redirecttype", "")
        if get.redirecttype == "":
            return public.returnResult(status=False, msg="redirecttype不能为空！")

        get.redirectpath = get.get("redirectpath", "")
        if get.domainorpath == "path" and get.redirectpath == "":
            return public.returnResult(status=False, msg="redirectpath不能为空！")

        get.tourl = get.get("tourl", "")
        if get.tourl == "":
            return public.returnResult(status=False, msg="tourl不能为空！")

        get.redirectdomain = get.get("redirectdomain", "")
        if get.domainorpath == "domain" and get.redirectdomain == "":
            return public.returnResult(status=False, msg="redirectdomain不能为空！")

        get.redirectname = get.get("redirectname", "")
        if get.redirectname == "":
            return public.returnResult(status=False, msg="redirectname不能为空！")

        get.sitename = get.site_name
        get.type = 1
        get.holdpath = 1

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        get.proxy_json_conf["redirect"]["redirect_status"] = True

        from panelRedirect import panelRedirect
        result = panelRedirect().CreateRedirect(get)

        self._site_proxy_conf_path = "{path}/{site_name}/{site_name}.json".format(
            path=self._proxy_config_path,
            site_name=get.site_name
        )
        public.writeFile(self._site_proxy_conf_path, json.dumps(get.proxy_json_conf))

        return result

    # 2024/4/22 上午10:45 删除指定网站的某个重定向规则
    def DeleteRedirect(self, get):
        '''
            @name 删除指定网站的某个重定向规则
            @author wzz <2024/4/22 上午10:45>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.redirectname = get.get("redirectname", "")
        if get.redirectname == "":
            return public.returnResult(status=False, msg="redirectname不能为空！")

        get.sitename = get.site_name

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        from panelRedirect import panelRedirect
        redirect_list = panelRedirect().GetRedirectList(get)
        if len(redirect_list) == 0:
            get.proxy_json_conf["redirect"]["redirect_status"] = False
            self._site_proxy_conf_path = "{path}/{site_name}/{site_name}.json".format(
                path=self._proxy_config_path,
                site_name=get.site_name
            )
            public.writeFile(self._site_proxy_conf_path, json.dumps(get.proxy_json_conf))

        return panelRedirect().DeleteRedirect(get)

    # 2024/4/23 上午10:38 编辑指定网站的某个重定向规则
    def ModifyRedirect(self, get):
        '''
            @name 编辑指定网站的某个重定向规则
            @author wzz <2024/4/23 上午10:38>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.domainorpath = get.get("domainorpath", "")
        if get.domainorpath == "":
            return public.returnResult(status=False, msg="domainorpath不能为空！")

        get.redirecttype = get.get("redirecttype", "")
        if get.redirecttype == "":
            return public.returnResult(status=False, msg="redirecttype不能为空！")

        get.redirectpath = get.get("redirectpath", "")
        if get.domainorpath == "path" and get.redirectpath == "":
            return public.returnResult(status=False, msg="redirectpath不能为空！")

        get.tourl = get.get("tourl", "")
        if get.tourl == "":
            return public.returnResult(status=False, msg="tourl不能为空！")

        get.redirectdomain = get.get("redirectdomain", "")
        if get.domainorpath == "domain" and get.redirectdomain == "":
            return public.returnResult(status=False, msg="redirectdomain不能为空！")

        get.redirectname = get.get("redirectname", "")
        if get.redirectname == "":
            return public.returnResult(status=False, msg="redirectname不能为空！")

        get.sitename = get.site_name
        get.type = get.get("type/d", 1)
        get.holdpath = get.get("holdpath/d", 1)

        from panelRedirect import panelRedirect

        return panelRedirect().ModifyRedirect(get)

    # 2024/4/26 下午3:32 获取指定网站指定重定向规则的信息
    def GetRedirectFile(self, get):
        '''
            @name 获取指定网站指定重定向规则的信息
            @author wzz <2024/4/26 下午3:32>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.path = get.get("path", "")
        if get.path == "":
            return public.returnResult(status=False, msg="path不能为空！")

        if not os.path.exists(get.path):
            return public.returnResult(status=False, msg="重定向已停止或配置文件目录不存在！")

        import files
        f = files.files()
        return f.GetFileBody(get)

    # 2024/4/22 上午11:12 设置防盗链
    def SetSecurity(self, get):
        '''
            @name 设置防盗链
            @author wzz <2024/4/22 上午11:12>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.fix = get.get("fix", "")
        if get.fix == "":
            return public.returnResult(status=False, msg="fix不能为空！")

        get.domains = get.get("domains", "")
        if get.domains == "":
            return public.returnResult(status=False, msg="domains不能为空！")

        get.return_rule = get.get("return_rule", "")
        if get.return_rule == "":
            return public.returnResult(status=False, msg="return_rule不能为空！")

        get.http_status = get.get("http_status", "")
        if get.http_status == "":
            return public.returnResult(status=False, msg="http_status不能为空！")

        get.status = get.get("status", "")
        if get.status == "":
            return public.returnResult(status=False, msg="status不能为空！")

        get.id = get.get("id", "")
        if get.id == "":
            return public.returnResult(status=False, msg="id不能为空！")

        get.name = get.site_name

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        get.proxy_json_conf["security"]["security_status"] = True if get.status == "true" else False
        get.proxy_json_conf["security"]["static_resource"] = get.fix
        get.proxy_json_conf["security"]["domains"] = get.domains
        get.proxy_json_conf["security"]["return_resource"] = get.return_rule
        get.proxy_json_conf["security"]["http_status"] = True if get.http_status else False

        from mod.base.web_conf.referer import Referer
        result = Referer("").set_referer_security(get)
        if not result["status"]:
            return result

        self._site_proxy_conf_path = "{path}/{site_name}/{site_name}.json".format(
            path=self._proxy_config_path,
            site_name=get.site_name
        )
        public.writeFile(self._site_proxy_conf_path, json.dumps(get.proxy_json_conf))

        return result

    # 2024/4/23 下午3:07 添加全局IP黑白名单
    def add_ip_limit(self, get):
        '''
            @name 添加全局IP黑白名单
            @author wzz <2024/4/23 下午3:08>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.ip_type = get.get("ip_type", "black")
        if get.ip_type not in ["black", "white"]:
            return public.returnResult(status=False, msg="ip_type参数错误，必须传black或white！")

        get.ips = get.get("ips", "")
        if get.ips == "":
            return public.returnResult(status=False, msg="ips不能为空，请输入IP，一行一个！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        get.ips = get.ips.split("\n")
        for ip in get.ips:
            if ip not in get.proxy_json_conf["ip_limit"]["ip_{}".format(get.ip_type)]:
                get.proxy_json_conf["ip_limit"]["ip_{}".format(get.ip_type)].append(ip)

        update_result = self.update_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])

        return public.returnResult(msg="设置成功！")

    # 2024/4/23 下午3:12 删除全局IP黑白名单
    def del_ip_limit(self, get):
        '''
            @name 删除全局IP黑白名单
            @author wzz <2024/4/23 下午3:12>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.ip_type = get.get("ip_type", "black")
        if get.ip_type not in ["black", "white"]:
            return public.returnResult(status=False, msg="ip_type参数错误，必须传black或white！")

        get.ip = get.get("ip", "")
        if get.ip == "":
            return public.returnResult(status=False, msg="ip不能为空，请输入IP！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        if get.ip in get.proxy_json_conf["ip_limit"]["ip_{}".format(get.ip_type)]:
            get.proxy_json_conf["ip_limit"]["ip_{}".format(get.ip_type)].remove(get.ip)

        update_result = self.update_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])

        return public.returnResult(msg="删除成功！")

    # 2024/4/23 下午3:13 批量删除全局IP黑白名单
    def batch_del_ip_limit(self, get):
        '''
            @name 批量删除全局IP黑白名单
            @author wzz <2024/4/23 下午3:14>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.ip_type = get.get("ip_type", "black")
        if get.ip_type not in ["black", "white", "all"]:
            return public.returnResult(status=False, msg="ip_type参数错误，必须传black或white！")

        get.ips = get.get("ips", "")
        if get.ips == "":
            return public.returnResult(status=False, msg="ips不能为空，请输入IP，一行一个！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        get.ips = get.ips.split("\n")
        for ip in get.ips:
            if get.ip_type == "all":
                if ip in get.proxy_json_conf["ip_limit"]["ip_black"]:
                    get.proxy_json_conf["ip_limit"]["ip_black"].remove(ip)
                if ip in get.proxy_json_conf["ip_limit"]["ip_white"]:
                    get.proxy_json_conf["ip_limit"]["ip_white"].remove(ip)
            else:
                if ip in get.proxy_json_conf["ip_limit"]["ip_{}".format(get.ip_type)]:
                    get.proxy_json_conf["ip_limit"]["ip_{}".format(get.ip_type)].remove(ip)

        update_result = self.update_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])

        return public.returnResult(msg="删除成功！")

    # 2024/4/22 下午9:01 获取指定网站的方向代理列表
    def get_proxy_list(self, get):
        '''
            @name
            @author wzz <2024/4/22 下午9:02>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_path = get.get("proxy_path", "")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        if len(get.proxy_json_conf["proxy_info"]) == 0:
            return public.returnResult(status=False, msg="没有代理信息！")

        subs_filter = get.proxy_json_conf["subs_filter"] if "subs_filter" in get.proxy_json_conf else \
            public.ExecShell("nginx -V 2>&1|grep 'ngx_http_substitutions_filter' -o")[0] != ""

        if get.proxy_path != "":
            for info in get.proxy_json_conf["proxy_info"]:
                if info["proxy_path"] == get.proxy_path:
                    info["global_websocket"] = get.proxy_json_conf["websocket"]["websocket_status"]
                    info["subs_filter"] = subs_filter
                    if "http://unix:" in info["proxy_pass"]:
                        info["proxy_pass"] = info["proxy_pass"].replace("http://unix:", "")

                    # 为配置中的代理url增加默认防盗链配置
                    default_conf = {
                        "name": get.site_name,
                        "fix": "jpg,jpeg,gif,png,js,css",
                        "domains": "",
                        "status": False,
                        "return_rule": "404",
                        "http_status": False,
                    }
                    if "security_referer" not in info or info["security_referer"]["status"] is False:
                        info["security_referer"] = default_conf
                        default_conf["domains"] = ",".join(self._get_site_domains(get.site_name))

                    return public.returnResult(data=info)
            else:
                return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

        return public.returnResult(data=get.proxy_json_conf["proxy_info"])

    # 2024/4/23 上午11:16 获取指定网站的所有配置信息
    def get_global_conf(self, get):
        '''
            @name 获取指定网站的所有配置信息
            @author wzz <2024/4/23 上午11:16>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        return public.returnResult(data=get.proxy_json_conf)

    @staticmethod
    def _get_site_domains(site_name: str):
        site_info = public.M("sites").where("name=?", (site_name,)).field('id').find()
        if not isinstance(site_info, dict):
            return []
        domains_info = public.M("domain").where("pid=?", (site_info["id"],)).field('name').select()
        if not isinstance(domains_info, list):
            return []
        return map(lambda x: x["name"], domains_info)

    # 2024/4/22 下午9:04 设置指定网站指定URL的反向代理
    def set_url_proxy(self, get):
        '''
            @name
            @author wzz <2024/4/22 下午9:04>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_path = get.get("proxy_path", "")
        if get.proxy_path == "":
            return public.returnResult(status=False, msg="proxy_path不能为空！")

        get.proxy_host = get.get("proxy_host", "")
        if get.proxy_host == "":
            return public.returnResult(status=False, msg="proxy_host不能为空！")

        get.proxy_pass = get.get("proxy_pass", "")
        if get.proxy_pass == "":
            return public.returnResult(status=False, msg="proxy_pass不能为空！")

        get.proxy_type = get.get("proxy_type", "")
        if get.proxy_type == "":
            return public.returnResult(status=False, msg="proxy_type不能为空！")

        get.proxy_connect_timeout = get.get("proxy_connect_timeout", "60s")
        get.proxy_send_timeout = get.get("proxy_send_timeout", "600s")
        get.proxy_read_timeout = get.get("proxy_read_timeout", "600s")

        get.remark = get.get("remark", "")
        if get.remark != "":
            get.remark = public.xssencode2(get.remark)

        if get.proxy_type == "unix":
            if not get.proxy_pass.startswith("http://unix:"):
                if not get.proxy_pass.startswith("/"):
                    return public.returnResult(status=False,
                                               msg="unix文件路径必须以/或http://unix:开头，如/tmp/flask_app.sock！")
                if not get.proxy_pass.endswith(".sock"):
                    return public.returnResult(status=False, msg="unix文件必须以.sock结尾，如/tmp/flask_app.sock！")
                if not os.path.exists(get.proxy_pass):
                    return public.returnResult(status=False, msg="代理目标不存在！")
                get.proxy_pass = "http://unix:" + get.proxy_pass
        elif get.proxy_type == "http":
            if not get.proxy_pass.startswith("http://") and not get.proxy_pass.startswith("https://"):
                return public.returnResult(status=False, msg="代理目标必须以http://或https://开头！")

        get.websocket = get.get("websocket/d", 1)

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        if get.proxy_json_conf["websocket"]["websocket_status"] and get.websocket != 1:
            return public.returnResult(status=False, msg="全局websocket为开启状态，不允许单独关闭此URL的websocket支持！")

        for info in get.proxy_json_conf["proxy_info"]:
            if info["proxy_path"] == get.proxy_path:
                info["proxy_host"] = get.proxy_host
                info["proxy_pass"] = get.proxy_pass
                info["proxy_type"] = get.proxy_type
                info["timeout"]["proxy_connect_timeout"] = get.proxy_connect_timeout.replace("s", "")
                info["timeout"]["proxy_send_timeout"] = get.proxy_send_timeout.replace("s", "")
                info["timeout"]["proxy_read_timeout"] = get.proxy_read_timeout.replace("s", "")
                info["websocket"]["websocket_status"] = True if get.websocket == 1 else False
                info["remark"] = get.remark
                break
        else:
            return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

        update_result = self.update_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])

        return public.returnResult(msg="设置成功！")

    # 2024/4/22 下午9:34 删除指定网站指定URL的反向代理
    def del_url_proxy(self, get):
        '''
            @name 删除指定网站指定URL的反向代理
            @param get:
            @return:
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_path = get.get("proxy_path", "")
        if get.proxy_path == "":
            return public.returnResult(status=False, msg="proxy_path不能为空！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        for info in get.proxy_json_conf["proxy_info"]:
            if info["proxy_path"] == get.proxy_path:
                get.proxy_json_conf["proxy_info"].remove(info)
                break
        else:
            return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

        update_result = self.update_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])

        return public.returnResult(msg="删除成功！")

    # 2024/4/22 下午9:36 设置指定网站指定URL反向代理的备注
    def set_url_remark(self, get):
        '''
            @name 设置指定网站指定URL反向代理的备注
            @param get:
            @return:
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_path = get.get("proxy_path", "")
        if get.proxy_path == "":
            return public.returnResult(status=False, msg="proxy_path不能为空！")

        get.remark = get.get("remark", "")
        if get.remark != "":
            get.remark = public.xssencode2(get.remark)

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        for info in get.proxy_json_conf["proxy_info"]:
            if info["proxy_path"] == get.proxy_path:
                info["remark"] = get.remark
                break
        else:
            return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

        update_result = self.update_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])

        return public.returnResult(msg="设置成功！")

    # 2024/4/22 下午9:40 添加指定网站指定URL的内容替换
    def add_sub_filter(self, get):
        '''
            @name 添加指定网站指定URL的内容替换
            @param get:
            @return:
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_path = get.get("proxy_path", "")
        if get.proxy_path == "":
            return public.returnResult(status=False, msg="proxy_path不能为空！")

        get.oldstr = get.get("oldstr", "")
        get.newstr = get.get("newstr", "")

        if get.oldstr == "" and get.newstr == "":
            return public.returnResult(status=False, msg="oldstr和newstr不能同时为空！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        get.sub_type = get.get("sub_type", "g")
        if get.sub_type == "":
            get.sub_type = "g"
        import re
        if not re.match(r'^[ior]+$|^g(?!.*o)|^o(?!.*g)$', get.sub_type):
            return public.returnResult(status=False,
                                       msg="get.sub_type 只能包含 'g'、'i'、'o' 或 'r' 中的字母组合，并且 'g' 和 'o' 不能同时存在！")

        is_subs = public.ExecShell("nginx -V 2>&1|grep 'ngx_http_substitutions_filter' -o")[0]
        if not is_subs and re.search(u'[\u4e00-\u9fa5]', get.oldstr + get.newstr):
            return public.returnResult(status=False,
                                       msg="您输入的内容包含中文，检测到当前nginx版本不支持，请尝试重新安装nginx 1.20以上的版本后重试！")

        if get.sub_type != "g" and not is_subs:
            return public.returnResult(status=False,
                                       msg="检测到当前nginx版本仅支持默认替换类型，请尝试重新安装nginx 1.20以上的版本后重试！")

        if not "g" in get.sub_type and not "o" in get.sub_type:
            get.sub_type = "g" + get.sub_type

        for info in get.proxy_json_conf["proxy_info"]:
            if info["proxy_path"] == get.proxy_path:
                for sub in info["sub_filter"]["sub_filter_str"]:
                    if get.oldstr == sub["oldstr"]:
                        return public.returnResult(status=False,
                                                   msg="替换前内容：【{}】的配置信息已存在，请勿重复添加！".format(
                                                       get.oldstr))
                info["sub_filter"]["sub_filter_str"].append(
                    {
                        "sub_type": get.sub_type,
                        "oldstr": get.oldstr,
                        "newstr": get.newstr
                    }
                )
                break
        else:
            return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

        update_result = self.update_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])

        return public.returnResult(msg="设置成功！")

    # 2024/4/22 下午10:00 删除指定网站指定URL的内容替换
    def del_sub_filter(self, get):
        '''
            @name 删除指定网站指定URL的内容替换
            @param get:
            @return:
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_path = get.get("proxy_path", "")
        if get.proxy_path == "":
            return public.returnResult(status=False, msg="proxy_path不能为空！")

        get.oldstr = get.get("oldstr", "")
        get.newstr = get.get("newstr", "")

        if get.oldstr == "" and get.newstr == "":
            return public.returnResult(status=False, msg="oldstr和newstr不能同时为空！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        for info in get.proxy_json_conf["proxy_info"]:
            if info["proxy_path"] == get.proxy_path:
                for sub in info["sub_filter"]["sub_filter_str"]:
                    if get.oldstr == sub["oldstr"]:
                        info["sub_filter"]["sub_filter_str"].remove(sub)
                        break
                else:
                    return public.returnResult(status=False, msg="未找到替换前内容：【{}】的配置信息！".format(get.oldstr))
                break
        else:
            return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

        update_result = self.update_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])

        return public.returnResult(msg="删除成功！")

    # 2024/4/22 下午10:03 设置指定网站指定URL的内容压缩
    def set_url_gzip(self, get):
        '''
            @name 设置指定网站指定URL的内容压缩
            @param get:
            @return:
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_path = get.get("proxy_path", "")
        if get.proxy_path == "":
            return public.returnResult(status=False, msg="proxy_path不能为空！")

        get.gzip_status = get.get("gzip_status/d", 999)
        if get.gzip_status == 999:
            return public.returnResult(status=False, msg="gzip_status不能为空，请传number 1或0！")
        get.gzip_min_length = get.get("gzip_min_length", "10k")
        get.gzip_comp_level = get.get("gzip_comp_level", "6")
        if get.gzip_min_length[0] == "0" or get.gzip_min_length.startswith("-"):
            return public.returnResult(status=False, msg="gzip_min_length参数不合法，请输入大于0的数字！")
        if get.gzip_comp_level == "0" or get.gzip_comp_level.startswith("-"):
            return public.returnResult(status=False, msg="gzip_comp_level参数不合法，请输入大于0的数字！")
        get.gzip_types = get.get(
            "gzip_types",
            "text/plain application/javascript application/x-javascript text/javascript text/css application/xml application/json image/jpeg image/gif image/png font/ttf font/otf image/svg+xml application/xml+rss text/x-js"
        )

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        for info in get.proxy_json_conf["proxy_info"]:
            if info["proxy_path"] == get.proxy_path:
                info["gzip"]["gzip_status"] = True if get.gzip_status == 1 else False
                if get.gzip_status == 1:
                    info["gzip"]["gzip_types"] = get.gzip_types
                    info["gzip"]["gzip_min_length"] = get.gzip_min_length
                    info["gzip"]["gzip_comp_level"] = get.gzip_comp_level
                    info["gzip"]["gzip_conf"] = ("gzip on;"
                                                 "\n      gzip_min_length {gzip_min_length};"
                                                 "\n      gzip_buffers 4 16k;"
                                                 "\n      gzip_http_version 1.1;"
                                                 "\n      gzip_comp_level {gzip_comp_level};"
                                                 "\n      gzip_types {gzip_types};"
                                                 "\n      gzip_vary on;"
                                                 "\n      gzip_proxied expired no-cache no-store private auth;"
                                                 "\n      gzip_disable \"MSIE [1-6]\.\";").format(
                        gzip_min_length=get.gzip_min_length,
                        gzip_comp_level=get.gzip_comp_level,
                        gzip_types=get.gzip_types,
                    )
                else:
                    info["gzip"]["gzip_conf"] = ""
                break
        else:
            return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

        update_result = self.update_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])

        return public.returnResult(msg="设置成功！")

    # 2024/4/22 下午10:15 添加指定网站指定URL的IP黑白名单
    def add_url_ip_limit(self, get):
        '''
            @name 添加指定网站指定URL的IP黑白名单
            @author wzz <2024/4/22 下午10:16>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_path = get.get("proxy_path", "")
        if get.proxy_path == "":
            return public.returnResult(status=False, msg="proxy_path不能为空！")

        get.ip_type = get.get("ip_type", "black")
        if get.ip_type not in ["black", "white"]:
            return public.returnResult(status=False, msg="ip_type参数错误，必须传black或white！")

        get.ips = get.get("ips", "")
        if get.ips == "":
            return public.returnResult(status=False, msg="ips不能为空，请输入IP，一行一个！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        get.ips = get.ips.split("\n")
        for info in get.proxy_json_conf["proxy_info"]:
            if info["proxy_path"] == get.proxy_path:
                for ip in get.ips:
                    if get.ip_type == "black":
                        if not ip in info["ip_limit"]["ip_black"]:
                            info["ip_limit"]["ip_black"].append(ip)
                    else:
                        if not ip in info["ip_limit"]["ip_white"]:
                            info["ip_limit"]["ip_white"].append(ip)
                break
        else:
            return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

        update_result = self.update_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])

        return public.returnResult(msg="设置成功！")

    # 2024/4/22 下午10:21 删除指定网站指定URL的IP黑白名单
    def del_url_ip_limit(self, get):
        '''
            @name 删除指定网站指定URL的IP黑白名单
            @param get:
            @return:
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_path = get.get("proxy_path", "")
        if get.proxy_path == "":
            return public.returnResult(status=False, msg="proxy_path不能为空！")

        get.ip_type = get.get("ip_type", "black")
        if get.ip_type not in ["black", "white"]:
            return public.returnResult(status=False, msg="ip_type参数错误，必须传black或white！")

        get.ip = get.get("ip", "")
        if get.ip == "":
            return public.returnResult(status=False, msg="ip不能为空，请输入IP！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        for info in get.proxy_json_conf["proxy_info"]:
            if info["proxy_path"] == get.proxy_path:
                if get.ip in info["ip_limit"]["ip_{ip_type}".format(ip_type=get.ip_type)]:
                    info["ip_limit"]["ip_{ip_type}".format(ip_type=get.ip_type)].remove(get.ip)
                break
        else:
            return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

        update_result = self.update_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])

        return public.returnResult(msg="设置成功！")

    # 2024/4/24 上午11:21 批量删除指定网站指定URL的IP黑白名单
    def batch_del_url_ip_limit(self, get):
        '''
            @name 批量删除指定网站指定URL的IP黑白名单
            @author wzz <2024/4/24 上午11:22>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.ip_type = get.get("ip_type", "black")
        if get.ip_type not in ["black", "white", "all"]:
            return public.returnResult(status=False, msg="ip_type参数错误，必须传black或white！")

        get.ips = get.get("ips", "")
        if get.ips == "":
            return public.returnResult(status=False, msg="ips不能为空，请输入IP，一行一个！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        for info in get.proxy_json_conf["proxy_info"]:
            if info["proxy_path"] == get.proxy_path:
                get.ips = get.ips.split("\n")
                if get.ip_type == "all":
                    for ip in get.ips:
                        if ip in info["ip_limit"]["ip_black"]:
                            info["ip_limit"]["ip_black"].remove(ip)
                        if ip in info["ip_limit"]["ip_white"]:
                            info["ip_limit"]["ip_white"].remove(ip)
                else:
                    for ip in get.ips:
                        if ip in info["ip_limit"]["ip_{ip_type}".format(ip_type=get.ip_type)]:
                            info["ip_limit"]["ip_{ip_type}".format(ip_type=get.ip_type)].remove(ip)
                break
        else:
            return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

        update_result = self.update_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])

        return public.returnResult(msg="删除成功！")

    # 2024/4/22 下午8:14 设置指定网站指定URL的缓存
    def set_url_cache(self, get):
        '''
            @name 设置指定网站指定URL的缓存
            @param get:
            @return:
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.cache_status = get.get("cache_status/d", 999)
        if get.cache_status == 999:
            return public.returnResult(status=False, msg="cache_status不能为空，请传number 1或0！")

        get.expires = get.get("expires", "1d")
        if get.expires[0] == "0" or get.expires.startswith("-"):
            return public.returnResult(status=False, msg="expires参数不合法，请输入大于0的数字！")

        get.cache_suffix = get.get("cache_suffix/s", "")
        if get.cache_suffix == "" and get.cache_status == 1:
            return public.returnResult(status=False, msg="cache_suffix不能为空，请输入后缀！")
        cache_suffix_list = []
        for suffix in get.cache_suffix.split(","):
            tmp_suffix = re.sub(r"\s", "", suffix)
            if not tmp_suffix:
                continue
            cache_suffix_list.append(tmp_suffix)

        if not cache_suffix_list and get.cache_status == 1:
            return public.returnResult(status=False, msg="cache_suffix参数错误，请输入有效后缀！")

        if not cache_suffix_list:
            cache_suffix_list = ["css", "js", "jpg", "jpeg", "png", "webp", "woff", "eot", "ttf", "svg", "ico", "css.map", "js.map"]

        get.cache_suffix = ",".join(cache_suffix_list)
        expires = "expires {}".format(get.expires)

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        static_cache = ("\n    location ~ .*\\.(css|js|jpe?g|gif|png|webp|woff|eot|ttf|svg|ico|css\.map|js\.map)$"
                        "\n    {{"
                        "\n        {expires};"
                        "\n        error_log /dev/null;"
                        "\n        access_log /dev/null;"
                        "\n    }}").format(
            expires=expires,
        )

        for info in get.proxy_json_conf["proxy_info"]:
            if info["proxy_path"] == get.proxy_path:
                info["proxy_cache"]["cache_status"] = True if get.cache_status == 1 else False
                info["proxy_cache"]["expires"] = get.expires
                info["proxy_cache"]["cache_suffix"] = get.cache_suffix
                if get.cache_status == 1:
                    info["proxy_cache"]["cache_conf"] = ("\n    proxy_cache {cache_zone};"
                                                         "\n    proxy_cache_key $host$uri$is_args$args;"
                                                         "\n    proxy_ignore_headers Set-Cookie Cache-Control expires X-Accel-Expires;"
                                                         "\n    proxy_cache_valid 200 304 301 302 {expires};"
                                                         "\n    proxy_cache_valid 404 1m;"
                                                         "{static_cache}").format(
                        cache_zone=get.proxy_json_conf["proxy_cache"]["cache_zone"],
                        expires=get.expires,
                        static_cache=static_cache,
                    )
                else:
                    info["proxy_cache"]["cache_conf"] = ""
                break
        else:
            return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

        update_result = self.update_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])

        return public.returnResult(msg="设置成功！")

    # 2024/4/24 上午9:57 设置指定网站指定URL的自定义配置
    def set_url_custom_conf(self, get):
        '''
            @name 设置指定网站指定URL的自定义配置
            @author wzz <2024/4/24 上午9:58>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_path = get.get("proxy_path", "")
        if get.proxy_path == "":
            return public.returnResult(status=False, msg="proxy_path不能为空！")

        get.custom_conf = get.get("custom_conf", "")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        for info in get.proxy_json_conf["proxy_info"]:
            if info["proxy_path"] == get.proxy_path:
                info["custom_conf"] = get.custom_conf
                break
        else:
            return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

        update_result = self.update_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])

        return public.returnResult(msg="设置成功！")

    @staticmethod
    def nginx_get_log_file(nginx_config: str, is_error_log: bool = False):
        import re
        if is_error_log:
            re_data = re.findall(r"error_log +(/(\S+/?)+) ?(.*?);", nginx_config)
        else:
            re_data = re.findall(r"access_log +(/(\S+/?)+) ?(.*?);", nginx_config)
        if re_data is None:
            return None
        for i in re_data:
            file_path = i[0].strip(";")
            if file_path != "/dev/null":
                return file_path
        return None

    def xsssec(self, text):
        replace_list = {
            "<": "＜",
            ">": "＞",
            "'": "＇",
            '"': "＂",
        }
        for k, v in replace_list.items():
            text = text.replace(k, v)
        return public.xssencode2(text)

    # 2024/4/24 下午5:39 获取指定网站的网站日志
    def GetSiteLogs(self, get):
        '''
            @name 获取指定网站的网站日志
            @author wzz <2024/4/24 下午5:39>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.type = get.get("type", "access")
        log_name = get.site_name
        if get.type != "access":
            log_name = get.site_name + ".error"

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        if get.proxy_json_conf["proxy_log"]["log_type"] == "default":
            log_file = public.get_logs_path() + "/" + log_name + '.log'
        elif get.proxy_json_conf["proxy_log"]["log_type"] == "file":
            log_file = get.proxy_json_conf["proxy_log"]["log_path"] + "/" + log_name + '.log'
        else:
            return public.returnResult(data={"msg": "", "size": 0})

        if os.path.exists(log_file):
            return public.returnResult(
                data={
                    "msg": self.xsssec(public.GetNumLines(log_file, 1000)),
                    "size": public.to_size(os.path.getsize(log_file))
                }
            )

        return public.returnResult(data={"msg": "", "size": 0})

    # 2024/4/25 上午10:51 清理指定网站的反向代理缓存
    def clear_cache(self, get):
        '''
            @name 清理指定网站的反向代理缓存
            @author wzz <2024/4/25 上午10:51>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        cache_dir = "/www/wwwroot/{site_name}/proxy_cache_dir".format(site_name=get.site_name)
        if os.path.exists(cache_dir):
            public.ExecShell("rm -rf {cache_dir}/*".format(cache_dir=cache_dir))

            public.serviceReload()
            return public.returnResult(msg="清理成功！")

        return public.returnResult(msg="清理失败，缓存目录不存在！")

    # 2024/4/25 下午9:24 设置指定网站的https端口
    def set_https_port(self, get):
        '''
            @name 设置指定网站的https端口
            @author wzz <2024/4/25 下午9:24>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.https_port = get.get("https_port", "443")
        if not public.checkPort(get.https_port) and get.https_port != "443":
            return public.returnResult(status=False, msg="https端口【{}】不合法！".format(get.https_port))

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        get.proxy_json_conf["https_port"] = get.https_port

        update_result = self.update_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])

        return public.returnResult(msg="设置成功！")

    # 2024/4/23 下午2:12 保存并重新生成新的nginx配置文件
    def update_conf(self, get):
        '''
            @name
            @author wzz <2024/4/23 下午2:13>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.conf_file = public.get_setup_path() + '/panel/vhost/nginx/' + get.site_name + '.conf'
        self.generate_config(get)
        get.data = get.site_conf
        get.encoding = "utf-8"
        get.path = get.conf_file

        import files
        f = files.files()
        save_result = f.SaveFileBody(get)
        if save_result["status"] == False:
            return public.returnResult(status=False, msg=save_result["msg"])

        self._site_proxy_conf_path = "{path}/{site_name}/{site_name}.json".format(
            path=self._proxy_config_path,
            site_name=get.site_name
        )
        public.writeFile(self._site_proxy_conf_path, json.dumps(get.proxy_json_conf))

        return public.returnResult(msg="保存成功！")


def _warp_check_nginx_conf(f):
    def inner(*args, **kwargs):
        check_ret = public.checkWebConfig()
        if not check_ret is True:
            return public.returnResult(
                status=False,
                msg='ERROR: 检测到配置文件有错误,请先排除后再操作<br><br><a style="color:red;">' +
                    check_ret.replace("\n", '<br>') + '</a>'
            )
        return f(*args, **kwargs)

    return inner



# 2025/7/23 使用pynginx 重写用于支持用户自定义所有配置情况，兼容旧版本
# 需处理的是后续操作，与创建相关的操作可以继续使用旧版本，不用处理
class ProxyProjectV2(main):

    def __init__(self):
        super().__init__()
        self._backup_path = self._proxy_path + "/backup"

    # 覆盖旧版更新配置的功能实现，阻止其功能
    def update_conf(self, get):
        return public.returnResult(status=True, msg="")

    @staticmethod
    def _parser_config(get) -> Tuple[Optional[pynginx.Config], str]:
        conf_file = public.get_setup_path() + '/panel/vhost/nginx/' + get.site_name + '.conf'
        if not os.path.exists(conf_file):
            return None, ""
        try:
            data = public.readFile(conf_file)
            if not data:
                return None, ""
            pync = pynginx.parse_string(data)
            pync.file_path = conf_file
            return pync, data
        except Exception as e:
            public.print_log(public.get_error_info())
            return None, ""

    def _warp_do_func(self, get, func: Callable[[ServerTools], Any]):
        pync, old_conf = self._parser_config(get)
        if pync is None:
            return public.returnResult(status=False, msg="配置文件解析失败！")

        ctool = ConfigTools(pync)
        stool = ctool.get_mian_server()
        if stool is None:
            return public.returnResult(status=False, msg="配置文件解析失败！")
        # 实际执行添加操作
        res = func(stool)
        if isinstance(res, dict):
            return res
        # 执行结束生成配置文件
        new_conf = ctool.to_string()
        public.writeFile(pync.file_path, new_conf)
        ret_nginx = public.checkWebConfig()
        if ret_nginx is not True:
            public.writeFile(pync.file_path, old_conf)
            return public.returnResult(status=False, msg="保存配置文件失败！无法添加配置")

        _site_proxy_conf_path = "{path}/{site_name}/{site_name}.json".format(
            path=self._proxy_config_path,
            site_name=get.site_name
        )
        public.writeFile(_site_proxy_conf_path, json.dumps(get.proxy_json_conf))
        public.serviceReload()
        return public.returnResult(msg="设置成功！")

    @_warp_check_nginx_conf
    def set_global_log(self, get):
        res = super().set_global_log(get)  # 旧版功能用于数据检查
        if res["status"] is False:
            return res

        def func(stool: ServerTools):
            if get.log_type == "file":
                access_log = "{}/{}.log".format(get.log_path, get.site_name)
                error_log = "{}/{}.error.log".format(get.log_path, get.site_name)
                stool.set_log_path(access_log, error_log)

            elif get.log_type == "rsyslog":
                site_name = get.site_name.replace(".", "_")
                access_log = "syslog:server={},nohostname,tag=nginx_{}_access".format(get.log_path, site_name)
                error_log = "syslog:server={},nohostname,tag=nginx_{}_error".format(get.log_path, site_name)
                stool.set_log_path(access_log, error_log)

            elif get.log_type == "off":
                stool.set_log_path("off", "off")
            else:
                access_log = "{}/{}.log".format(public.get_logs_path(), get.site_name)
                error_log = "{}/{}.error.log".format(public.get_logs_path(), get.site_name)
                stool.set_log_path(access_log, error_log)

        return self._warp_do_func(get, func)

    @_warp_check_nginx_conf
    def add_dir_auth(self, get):
        res = super().set_dir_auth(get)  # 旧版功能用于数据检查
        if res["status"] is False:
            return res

        def func(stool: ServerTools):
            auth_data = None
            for a in get.proxy_json_conf["basic_auth"]:
                if a["auth_path"] == get.auth_path:
                    auth_data = a
                    break
            stool.add_basic_auth(get.auth_path, auth_data["auth_file"])

        return self._warp_do_func(get, func)

    set_dir_auth = add_dir_auth

    @_warp_check_nginx_conf
    def del_dir_auth(self, get):
        res = super().del_dir_auth(get)
        if res["status"] is False:
            return res

        return self._warp_do_func(get, lambda stool: stool.remove_basic_auth(get.auth_path))

    @_warp_check_nginx_conf
    def set_global_gzip(self, get):
        res = super().set_global_gzip(get)
        if res["status"] is False:
            return res

        return self._warp_do_func(
            get, lambda stool: stool.set_gzip(
                bool(get.gzip_status), get.gzip_comp_level, get.gzip_min_length, get.gzip_types.split()
            )
        )

    # 该功能理论上不支持， 我们已经视使用了 ^~ / 匹配过后端，同级的所有正则匹配，都不会生效，故此配置从未生效
    # 针对代理的缓存配置只能在内部生效
    # PS: 该功能是废弃的功能，请勿使用
    @_warp_check_nginx_conf
    def set_global_cache(self, get):
        res = super().set_global_cache(get)
        if res["status"] is False:
            return res
        return self._warp_do_func(
            get, lambda stool: stool.set_server_proxy_cache(
                bool(get.cache_status),
                get.proxy_json_conf["proxy_cache"]["cache_zone"],
                get.expires
            )
        )

    @_warp_check_nginx_conf
    def set_global_websocket(self, get):
        res = super().set_global_websocket(get)

        if res["status"] is False:
            return res

        return self._warp_do_func(get, lambda stool: stool.set_websocket_support(bool(get.websocket_status)))

    @_warp_check_nginx_conf
    def add_proxy(self, get):
        res = super().add_proxy(get)
        if res["status"] is False:
            return res

        return self._set_proxy(get)

    def _set_proxy(self, get):

        def func(stool: ServerTools):
            connect_timeout = get.get("proxy_connect_timeout", "60s")
            send_timeout = get.get("proxy_send_timeout", "600s")
            read_timeout = get.get("proxy_read_timeout", "600s")
            ltool = stool.get_location(get.proxy_path, create=False)  # 尝试不创建，任意匹配规则均可只管路由一致的
            if ltool is None:  # 无法匹配路由的时候，尝试创建，且匹配规则为 ^~
                ltool = stool.get_location(get.proxy_path, "^~", create=True, comment="# 代理路由")
            ltool.add_proxy(get.proxy_pass, get.proxy_host, get.proxy_pass.startswith("https://"))
            ltool.set_proxy_timeout(connect_timeout, send_timeout, read_timeout)
            ltool.set_websocket_support(get.proxy_json_conf["websocket"]["websocket_status"])

        return self._warp_do_func(get, func)


    @_warp_check_nginx_conf
    def set_url_proxy(self, get):
        res = super().set_url_proxy(get)
        if res["status"] is False:
            return res

        return self._set_proxy(get)

    @_warp_check_nginx_conf
    def del_url_proxy(self, get):
        res = super().del_url_proxy(get)
        if res["status"] is False:
            return res

        def func(stool: ServerTools):
            stool.remove_location(get.proxy_path)

        return self._warp_do_func(get, func)

    @_warp_check_nginx_conf
    def add_ip_limit(self, get):
        res = super().add_ip_limit(get)
        if res["status"] is False:
            return res

        return self._set_ip_limit(get)

    def _set_ip_limit(self, get):
        def func(stool: ServerTools):
            stool.set_ip_restrict(
                get.proxy_json_conf["ip_limit"]["ip_black"],
                get.proxy_json_conf["ip_limit"]["ip_white"],
            )

        return self._warp_do_func(get, func)

    @_warp_check_nginx_conf
    def del_ip_limit(self, get):
        res = super().del_ip_limit(get)
        if res["status"] is False:
            return res

        return self._set_ip_limit(get)

    @_warp_check_nginx_conf
    def batch_del_ip_limit(self, get):
        res = super().batch_del_ip_limit(get)

        if res["status"] is False:
            return res

        return self._set_ip_limit(get)

    @_warp_check_nginx_conf
    def add_sub_filter(self, get):
        res = super().add_sub_filter(get)
        if res["status"] is False:
            return res
        return self._set_sub_filter(get)

    def _set_sub_filter(self, get):
        def func(stool: ServerTools):
            ltool = stool.get_location(get.proxy_path, create=False)
            if ltool is None:
                return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

            sub_filter_list = []
            if not "subs_filter" in get.proxy_json_conf:
                get.proxy_json_conf["subs_filter"] = \
                    public.ExecShell("nginx -V 2>&1|grep 'ngx_http_substitutions_filter' -o")[0] != ""

            for info in get.proxy_json_conf["proxy_info"]:
                if info["proxy_path"] != get.proxy_path:
                    continue
                for sub in info["sub_filter"]["sub_filter_str"]:
                    sub_filter_list.append((sub["oldstr"], sub["newstr"], sub["sub_type"]))

            ltool.set_sub_filter(sub_filter_list, bool(get.proxy_json_conf["subs_filter"]))

        return self._warp_do_func(get, func)

    @_warp_check_nginx_conf
    def del_sub_filter(self, get):
        res = super().del_sub_filter(get)

        if res["status"] is False:
            return res

        return self._set_sub_filter(get)

    @_warp_check_nginx_conf
    def set_url_gzip(self, get):
        res = super().set_url_gzip(get)
        if res["status"] is False:
            return res

        def func(stool: ServerTools):
            ltool = stool.get_location(get.proxy_path, create=False)
            if ltool is None:
                return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

            ltool.set_gzip(bool(get.gzip_status), get.gzip_comp_level, get.gzip_min_length, get.gzip_types.split())

        return self._warp_do_func(get, func)

    def _set_url_ip_limit(self, get):
        def func(stool: ServerTools):
            ltool = stool.get_location(get.proxy_path, create=False)
            if ltool is None:
                return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

            ip_limit = None
            for info in get.proxy_json_conf["proxy_info"]:
                if info["proxy_path"] == get.proxy_path:
                    ip_limit = info["ip_limit"]
                    break
            ltool.set_ip_restrict(ip_limit["ip_black"], ip_limit["ip_white"])

        return self._warp_do_func(get, func)

    @_warp_check_nginx_conf
    def add_url_ip_limit(self, get):
        res = super().add_url_ip_limit(get)
        if res["status"] is False:
            return res

        return self._set_url_ip_limit(get)

    @_warp_check_nginx_conf
    def del_url_ip_limit(self, get):
        res = super().del_url_ip_limit(get)
        if res["status"] is False:
            return res
        return self._set_url_ip_limit(get)

    @_warp_check_nginx_conf
    def batch_del_url_ip_limit(self, get):
        res = super().batch_del_url_ip_limit(get)
        if res["status"] is False:
            return res
        return self._set_url_ip_limit(get)

    @_warp_check_nginx_conf
    def set_url_cache(self, get):
        res = super().set_url_cache(get)
        if res["status"] is False:
            return res

        def func(stool: ServerTools):
            ltool = stool.get_location(get.proxy_path, create=False)
            if ltool is None:
                return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

            ltool.set_proxy_cache(
                bool(get.cache_status),
                get.proxy_json_conf["proxy_cache"]["cache_zone"],
                get.expires,
                get.cache_suffix,
            )

        return self._warp_do_func(get, func)

    @_warp_check_nginx_conf
    def set_https_port(self, get):
        res = super().set_https_port(get)

        if res["status"] is False:
            return res

        def func(stool: ServerTools):
            http_v3 = bool(public.ExecShell("nginx -V 2>&1| grep 'http_v3_module' -o")[0])
            nginx_ver = public.ExecShell("nginx -V 2>&1| nginx -version 2>&1 | cut -d'/' -f2")[0]
            nginx_ver_list = list(map(lambda x: int(x) if x.isdecimal() else 0, nginx_ver.split('.')[:3]))
            is_ipv6 = os.path.exists(public.get_panel_path() + '/data/ipv6.pl')
            stool.set_ssl_port(
                get.https_port,
                is_http3=http_v3,
                is_ipv6=is_ipv6,
                is_http2on=nginx_ver_list > [1, 25, 0] # 从 1.25.1 开始可用 http2 on; 命令
            )

        return self._warp_do_func(get, func)

    def save_nginx_config(self, get):
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.data = get.get("conf_data", "")
        if get.data == "":
            return public.returnResult(status=False, msg="data不能为空！")

        get.encoding = "utf-8"
        get.path = public.get_setup_path() + '/panel/vhost/nginx/' + get.site_name + '.conf'
        public.print_log(get.path)

        import files
        f = files.files()
        save_result = f.SaveFileBody(get)
        if save_result["status"] is False:
            return public.returnResult(status=False, msg=save_result["msg"])

        get.proxy_json_conf = self.read_json_conf(get)

        pyconf, _ = self._parser_config(get)
        cf = ConfigFinder(pyconf)
        self._update_proxy_config(old_conf=get.proxy_json_conf, new_conf=cf.export_proxy_config())
        self._site_proxy_conf_path = "{path}/{site_name}/{site_name}.json".format(
            path=self._proxy_config_path,
            site_name=get.site_name
        )
        public.writeFile(self._site_proxy_conf_path, json.dumps(get.proxy_json_conf))
        return public.returnResult(True, "保存成功")

    @staticmethod
    def _update_proxy_config(new_conf: dict, old_conf: dict):
        for key in ("site_port", "https_port", "ip_limit", "proxy_cache", "gzip", "websocket", "proxy_log"):
            if isinstance(new_conf[key], dict):
                old_conf[key].update(**new_conf[key])
            else:
                old_conf[key] = new_conf[key]

        old_basic_auth = {i["auth_path"]: i for i in old_conf["basic_auth"]}
        keys = []
        for basic_auth in new_conf["basic_auth"]:
            if basic_auth["auth_path"] in old_basic_auth:
                old_basic_auth[basic_auth["auth_path"]].update(**basic_auth)
            else:
                old_basic_auth[basic_auth["auth_path"]] = basic_auth
            keys.append(basic_auth["auth_path"])

        old_conf["basic_auth"] = [old_basic_auth[i] for i in keys]

        old_proxy_info= {i["proxy_path"]: i for i in old_conf["proxy_info"]}
        keys = []
        for proxy_info in new_conf["proxy_info"]:
            if proxy_info["proxy_path"] in old_proxy_info:
                old_proxy_info[proxy_info["proxy_path"]].update(**proxy_info)
            else:
                old_proxy_info[proxy_info["proxy_path"]] = proxy_info
            if "remark" not in old_proxy_info[proxy_info["proxy_path"]]:
                old_proxy_info[proxy_info["proxy_path"]]["remark"] = ""
            keys.append(proxy_info["proxy_path"])

        old_conf["proxy_info"] = [old_proxy_info[key] for key in keys]


    def re_history(self, get):
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        history = get.get("history", "")
        if history == "":
            return public.returnResult(status=False, msg="history不能为空！")

        path = public.get_setup_path() + '/panel/vhost/nginx/' + get.site_name + '.conf'

        save_path = ('/www/backup/file_history/' + path).replace('//', '/')
        history_file = save_path + '/' + history
        if not os.path.exists(history_file):
            return public.returnResult(status=False, msg="历史版本文件不存在！")
        data = public.readFile(history_file)
        get.conf_data = data
        return self.save_nginx_config(get)

    @_warp_check_nginx_conf
    def set_referer_conf(self, get):
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_path = get.get("proxy_path", "")
        if get.proxy_path == "":
            return public.returnResult(status=False, msg="proxy_path不能为空！")

        rconf = {}
        try:
            rconf["status"] = "true" if not hasattr(get, "status") else get.status.strip()
            rconf["http_status"] = "false" if not hasattr(get, "http_status") else get.http_status.strip()
            rconf["name"] = get.site_name.strip()
            rconf["fix"] = get.fix.strip()
            rconf["domains"] = get.domains.strip()
            rconf["return_rule"] = get.return_rule.strip()
        except AttributeError:
            return public.returnResult(False, "参数错误")
        error_str = ""
        if rconf["status"] not in ("true", "false") and rconf["http_status"] not in ("true", "false"):
            error_str = "状态参数只能使用【true,false】"
        else:
            rconf["status"] = rconf["status"] == "true"
            rconf["http_status"] = rconf["http_status"] == "true"
        if rconf["return_rule"] not in ('404', '403', '200', '301', '302', '401') and rconf["return_rule"][0] != "/":
            error_str = "响应资源应使用URI路径或HTTP状态码，如：/test.png 或 404"
        if len(rconf["domains"]) < 3:
            error_str =  "防盗链域名不能为空"
        if len(rconf["fix"]) < 2:
            error_str =  'URL后缀不能为空!'

        if error_str:
            return public.returnResult(False, error_str)

        rconf["domains"] = [i.strip() for i in rconf["domains"].split(",") if i.strip() != ""]
        rconf["fix"] = [i.strip() for i in rconf["fix"].split(",") if i.strip() != ""]

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        for info in get.proxy_json_conf["proxy_info"]:
            if info["proxy_path"] == get.proxy_path:
                info["security_referer"] = rconf
                break
        else:
            return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

        def func(stool: ServerTools):
            ltool = stool.get_location(get.proxy_path, create=False)
            if ltool is None:
                return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

            ltool.set_security_referer(
                status=rconf["status"],
                suffix_list=rconf["fix"],
                domain_list=rconf["domains"],
                return_rule=rconf["return_rule"],
                allow_empty= rconf["http_status"]
            )
            rconf["domains"] = ",".join(rconf["domains"])
            rconf["fix"] = ",".join(rconf["fix"])

        return self._warp_do_func(get, func)



main = ProxyProjectV2
