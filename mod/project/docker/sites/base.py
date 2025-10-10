# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------
# ------------------------------
# docker模型 - docker runtime 基类
# ------------------------------
import json
import os
import sys
import time
from datetime import datetime, timedelta

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public
from btdockerModel import dk_public as dp
from mod.project.docker.composeMod import main as composeMod


class Sites(composeMod):

    def __init__(self):
        super(Sites, self).__init__()
        self.project_path = '/www/dk_project'
        self.sites_config_path = self.project_path + '/sites'
        self.site_config_path = None
        self.site_conf_file = None
        self.default_index_body = '''<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>恭喜，站点创建成功！</title>
    <style>
        .container {
            width: 60%;
            margin: 10% auto 0;
            background-color: #f0f0f0;
            padding: 2% 5%;
            border-radius: 10px
        }

        ul {
            padding-left: 20px;
        }

            ul li {
                line-height: 2.3
            }

        a {
            color: #20a53a
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>恭喜, 站点创建成功！</h1>
        <h3>这是默认index.html，本页面由系统自动生成</h3>
        <ul>
            <li>本页面在FTP根目录下的index.html</li>
            <li>您可以修改、删除或覆盖本页面</li>
            <li>FTP相关信息，请到“面板系统后台 > FTP” 查看</li>
        </ul>
    </div>
</body>
</html>'''
        self.default_404_body = '''<html>
<style>
	.btlink {
	color: #20a53a;
	text-decoration: none;
}
</style>
<meta charset="UTF-8">
<html>
<head><title>404 Not Found</title></head>
<body>
<center><h1>404 Not Found</h1></center>
<hr>
<div style="text-align: center;font-size: 15px" >Power by <a class="btlink" href="https://www.bt.cn/?from=404" target="_blank">堡塔 (免费，高效和安全的托管控制面板)</a></div>
</body>
</html>'''
        self.default_stop_body = '''<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>抱歉，站点已暂停</title>
<style>
html,body,div,h1,*{margin:0;padding:0;}
body{
	background-color:#fefefe;
	color:#333
}
.box{
	width:580px;
	margin:0 auto;
}
h1{
	font-size:20px;
	text-align:center;
	background:url(data:image/png;base64,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) no-repeat top center;
	padding-top:160px;
	margin-top:30%;
	font-weight:normal;
}

</style>
</head>

<body>
<div class="box">
<h1>抱歉！该站点已经被管理员停止运行，请联系管理员了解详情！</h1>
<div style="text-align: center;font-size: 15px" >Power by <a class="btlink" href="https://www.bt.cn/?from=404" target="_blank">堡塔 (免费，高效和安全的托管控制面板)</a></div>
</div>
</body>
</html>
'''
        self.default_not_found_body = '''<html>
<head><title>404 Not Found</title></head>
<body>
<center><h1>404 Not Found</h1></center>
<hr><center>nginx</center>
</body>
</html>'''
        if not os.path.exists(self.sites_config_path):
            public.ExecShell('mkdir -p {}'.format(self.sites_config_path))
            public.ExecShell('chown -R www:www {}'.format(self.sites_config_path))
            public.ExecShell('chmod -R 755 {}'.format(self.sites_config_path))

        self.init_site_json = {
            "site_name": "",
            "domain_list": [],
            "primary_port": "",
            "site_port": [],
            "https_port": "443",
            "ipv4_port_conf": "listen {listen_port}{default_site};",
            "ipv6_status": False,
            "ipv6_port_conf": "listen [::]:{listen_port}{default_site};",
            "port_conf": "listen {listen_port};{listen_ipv6}",
            "ipv4_ssl_port_conf": "{ipv4_port_conf}\n    listen {https_port} ssl http2 {default_site};",
            "ipv6_ssl_port_conf": "{ipv6_port_conf}\n    listen [::]:{https_port} ssl http2 {default_site};",
            "ipv4_http3_ssl_port_conf": "{ipv4_port_conf}\n    listen {https_port} quic{default_site};\n    listen {https_port} ssl{default_site};",
            "ipv6_http3_ssl_port_conf": "{ipv6_port_conf}\n    listen [::]:{https_port} quic{default_site};\n    listen [::]:{https_port} ssl {default_site};",
            "site_path": "",
            "run_path": "/",
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
            "default_cache": "proxy_cache_path {site_config_path}/proxy_cache_dir levels=1:2 keys_zone={cache_name}_cache:20m inactive=1d max_size=5g;",
            "default_describe": "# 如果反代网站访问异常且这里已经配置了内容，请优先排查此处的配置是否正确\n",
            "http_block": "",
            "server_block": "",
            "remark": "",
            "enable_php_conf": "",
            "rewrite_conf": "",
            "index_conf": "index.php index.html index.htm default.php default.htm default.html",
            "redirect_conf_404": "",
            "stop_site": False,
            "stop_site_conf": "    location / {\n        try_files $uri /index.html;\n    }",
            "proxy_info": [],
            "classify": 0,
        }

        self._template_conf = '''{http_block}
server {{
    {port_conf}
    server_name {domains};
    index {index_conf};
    root {site_path}{run_path};
    {stop_site_conf}

    #CERT-APPLY-CHECK--START
    # 用于SSL证书申请时的文件验证相关配置 -- 请勿删除
    include /www/server/panel/vhost/nginx/well-known/{site_name}.conf;
    #CERT-APPLY-CHECK--END

    #SSL-START {ssl_start_msg}
    {ssl_info}
    #SSL-END
    #REDIRECT START
    {redirect_conf_404}
    {redirect_conf}
    #REDIRECT END

    #ERROR-PAGE-START  {err_page_msg}
    {err_age_404}
    {err_age_502}
    #ERROR-PAGE-END

    #PHP-INFO-START  PHP引用配置，可以注释或修改
    {security_conf}
    {enable_php_conf}
    #PHP-INFO-END
    
    #REWRITE-START URL重写规则引用,修改后将导致面板设置的伪静态规则失效
    {rewrite_conf}
    #REWRITE-END

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
      {PROXY_BUFFERING}
      {timeout_conf}
      {websocket_support}
      {custom_conf}
      {proxy_cache}
      {gzip}
      {sub_filter}
      {server_log}
    }}'''

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
            PROXY_BUFFERING="",
            custom_conf="",
            timeout_conf=get.proxy_timeout,
            websocket_support=self.init_site_json["websocket"]["websocket_conf"],
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
            "proxy_buffering": True,
        }

        # 2024/4/18 上午10:53 构造反向代理的配置文件

    def structure_nginx(self, get):
        '''
            @name 构造反向代理的配置文件
            @author wzz <2024/4/18 上午10:54>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if not os.path.exists(os.path.join(self.sites_config_path, "no_auto_create_404.pl")):
            get.err_age_404 = "error_page 404 /404.html;"
        else:
            get.err_age_404 = "#error_page 404 /404.html;"
        get.err_age_502 = get.get("err_age_502", "#error_page 502 /502.html;")
        get.proxy_info = get.get("proxy_info", "")

        get.server_log =self.init_site_json["proxy_log"]["log_conf"].format(
            log_path=public.get_logs_path(),
            site_name=get.site_name
        )
        if get.site_port != "80":
            get.server_log = self.init_site_json["proxy_log"]["log_conf"].format(
                log_path=public.get_logs_path(),
                site_name="{}_{}".format(get.site_name, get.site_port)
            )

        get.remark = get.get("remark", "")
        get.server_block = get.get("server_block", "")
        get.websocket_status = get.get("websocket_status", True)
        get.proxy_timeout = "proxy_connect_timeout 60s;\n      proxy_send_timeout 600s;\n      proxy_read_timeout 600s;"
        get.proxy_conf = ""
        if get.type != "php": self.structure_proxy_conf(get)
        is_subs = public.ExecShell("nginx -V 2>&1|grep 'ngx_http_substitutions_filter' -o")[0]

        self.init_site_json["subs_filter"] = True if is_subs != "" else False
        self.init_site_json["site_name"] = get.domain_name
        self.init_site_json["domain_list"] = get.domain_list
        self.init_site_json["site_port"] = get.port_list
        self.init_site_json["site_path"] = get.site_path
        self.init_site_json["err_age_404"] = get.err_age_404
        self.init_site_json["err_age_502"] = get.err_age_502
        self.init_site_json["proxy_log"]["log_conf"] = get.server_log
        self.init_site_json["remark"] = get.remark
        self.init_site_json["http_block"] = ""
        self.init_site_json["enable_php_conf"] = get.enable_php_conf
        self.init_site_json["proxy_info"] = [] if not get.proxy_info else [get.proxy_info]
        self.init_site_json["proxy_cache"]["cache_zone"] = get.site_name.replace(".", "_") + "_cache" if get.site_port == "80" else "{}_{}_cache".format(get.site_name.replace(".", "_"), get.site_port)
        self.init_site_json["primary_port"] = get.site_port
        self.init_site_json["type"] = get.type

        # 2024/4/18 上午10:35 写入Nginx配置文件

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
            for p in get.port_list:
                ipv4_port_conf += self.init_site_json["ipv4_port_conf"].format(listen_port=p, default_site="") + "\n    "
        else:
            ipv4_port_conf = self.init_site_json["ipv4_port_conf"].format(listen_port=get.port_list[0], default_site="")
        port_conf = ipv4_port_conf + "\n"

        # 2024/6/4 下午4:20 兼容新版监控报表的配置
        monitor_conf = ""
        if os.path.exists("/www/server/panel/plugin/monitor/monitor_main.py"):
            monitor_conf = '''#Monitor-Config-Start 网站监控报表日志发送配置
            access_log syslog:server=unix:/tmp/bt-monitor.sock,nohostname,tag=dp{pid}__access monitor;
            error_log syslog:server=unix:/tmp/bt-monitor.sock,nohostname,tag=dp{pid}__error;
            #Monitor-Config-End'''.format(pid=get.pid)

            import PluginLoader
            args = public.dict_obj()
            args.site_id = get.pid
            args.site_name = get.site_name
            PluginLoader.plugin_run("monitor", "init_docker_site_config", args)

        conf = self._template_conf.format(
            http_block=get.http_block,
            server_block="",
            port_conf=port_conf,
            index_conf=self.init_site_json["index_conf"],
            ssl_start_msg=public.getMsg('NGINX_CONF_MSG1'),
            err_page_msg=public.getMsg('NGINX_CONF_MSG2'),
            php_info_start=public.getMsg('NGINX_CONF_MSG3'),
            rewrite_start_msg=public.getMsg('NGINX_CONF_MSG4'),
            rewrite_conf="",
            redirect_conf_404="",
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
            enable_php_conf=get.enable_php_conf,
            proxy_conf=get.proxy_conf,
            server_log=get.server_log,
            site_path=get.site_path,
            run_path="",
            stop_site_conf="",
            proxy_cache="",
            websocket_support=self.init_site_json["websocket"]["websocket_conf"],
            monitor_conf=monitor_conf,
        )

        # 写配置文件
        well_known_path = "{}/vhost/nginx/well-known".format(public.get_panel_path())
        if not os.path.exists(well_known_path):
            os.makedirs(well_known_path, 0o600)
        public.writeFile("{}/{}.conf".format(well_known_path, get.domain_name), "")

        get.filename = public.get_setup_path() + '/panel/vhost/nginx/' + get.domain_name + '.conf'

        return public.writeFile(get.filename, conf)

    # 2024/7/29 下午2:39 创建必须目录
    def create_must_dir(self, get):
        '''
            @name
            @author wzz <2024/7/29 下午2:40>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if not os.path.exists(self.site_config_path):
            public.ExecShell('mkdir -p {}'.format(self.site_config_path))
            public.ExecShell('chown -R www:www {}'.format(self.site_config_path))
            public.ExecShell('chmod -R 755 {}'.format(self.site_config_path))

        if not os.path.exists(get.site_path):
            public.ExecShell('mkdir -p {}'.format(get.site_path))
            if get.type == "php":
                public.ExecShell("chown -R 1000:1000 {}".format(get.site_path))
            else:
                public.ExecShell('chown -R www:www {}'.format(get.site_path))
            public.ExecShell('chmod -R 755 {}'.format(get.site_path))

        public.ExecShell("chown -R www:www /www/dk_project/wwwroot")
        public.ExecShell("chmod -R 755 /www/dk_project/wwwroot")

        if not os.path.exists(self.site_config_path + "/proxy_cache_dir"):
            public.ExecShell('mkdir -p {}'.format(self.site_config_path + "/proxy_cache_dir"))
            public.ExecShell('chown -R www:www {}'.format(self.site_config_path + "/proxy_cache_dir"))
            public.ExecShell('chmod -R 755 {}'.format(self.site_config_path + "/proxy_cache_dir"))

    # 2024/7/29 上午11:46 创建完成后置检测
    def check_after_create(self, get):
        '''
            @name 创建完成后置检测
            @author wzz <2024/7/29 上午11:47>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        wc_err = public.checkWebConfig()
        if not wc_err:
            public.ExecShell("rm -f {}".format(self.site_conf_file))
            public.ExecShell("rm -rf {}".format(get.filename))
            dp.sql("docker_sites").where('id=?', (get.pid,)).delete()
            dp.sql("docker_domain").where('pid=?', (get.pid,)).delete()
            return public.returnResult(
                status=False,
                msg='ERROR: 检测到配置文件有错误,请先排除后再操作<br><br><a style="color:red;">' +
                    wc_err.replace("\n", '<br>') + '</a>'
            )
        if type(wc_err) != bool and "test failed" in wc_err:
            public.ExecShell("rm -f {}".format(self.site_conf_file))
            public.ExecShell("rm -rf {}".format(get.filename))
            dp.sql("docker_sites").where('id=?', (get.pid,)).delete()
            dp.sql("docker_domain").where('pid=?', (get.pid,)).delete()
            return public.returnResult(
                status=False,
                msg='ERROR: 检测到配置文件有错误,请先排除后再操作<br><br><a style="color:red;">' +
                    wc_err.replace("\n", '<br>') + '</a>'
            )

        return public.returnResult(True)

    # 2024/7/29 上午11:31 插入sites表
    def insert_sites(self, get):
        '''
            @name 插入sites或dk_sites表
            @author wzz <2024/7/29 上午11:32>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        addtime = public.getDate()
        pdata = {
            "name": get.domain_name,
            "path": get.site_path,
            "run_path": "/",
            "remark": get.remark,
            "type": get.type,
            "service_info": json.dumps(get.service_info),
            "addtime": addtime,
            "container_id": get.container_id,
        }
        get.pid = dp.sql("docker_sites").insert(pdata)
        if not get.pid:
            return public.returnResult(False, '添加失败，无法将数据插入到网站数据库中')

        for domain in get.domain_list:
            dp.sql("docker_domain").insert({
                "name": domain,
                "pid": get.pid,
                "port": "80" if ":" not in domain else domain.split(":")[1],
                "addtime": addtime,
            })

        return public.returnResult(True)

    def read_json_conf(self, get):
        '''
            @name
            @author wzz <2024/4/18 下午9:53>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        conf_path = "{path}/{site_name}/{site_name}.json".format(
            path=self.sites_config_path,
            site_name=get.site_name
        )
        try:
            proxy_json_conf = json.loads(public.readFile(conf_path))
        except Exception as e:
            proxy_json_conf = {}

        return proxy_json_conf

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
        if len(get.proxy_json_conf["proxy_info"]) != 0 and not get.proxy_json_conf["stop_site"]:
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
                    PROXY_BUFFERING="proxy_buffering off;" if "proxy_buffering" in info and info["proxy_buffering"] else "" and not info["proxy_buffering"],
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
        if not "ipv6_status" in get.proxy_json_conf:
            get.proxy_json_conf["ipv6_status"] = False

        ipv4_port_conf = ""
        ipv6_port_conf = ""
        default_site = public.readFile('/www/server/panel/data/defaultSite.pl')
        if not default_site:
            default_server = ""
        else:
            if default_site == get.site_name:
                default_server = " default_server"
            else:
                default_server = ""

        for p in get.proxy_json_conf["site_port"]:
            ipv4_port_conf += get.proxy_json_conf["ipv4_port_conf"].format(
                listen_port=p,
                default_site=default_server,
            ) + "\n    "
            if get.proxy_json_conf["ipv6_status"]:
                ipv6_port_conf += get.proxy_json_conf["ipv6_port_conf"].format(
                    listen_port=p,
                    default_site=default_server,
                ) + "\n    "

        if get.proxy_json_conf["ssl_info"]["ssl_status"]:
            if public.ExecShell("nginx -V 2>&1| grep 'http_v3_module' -o")[0] != "":
                ipv4_http3_ssl_port_conf = get.proxy_json_conf["ipv4_http3_ssl_port_conf"].format(
                    ipv4_port_conf=ipv4_port_conf,
                    https_port=get.proxy_json_conf["https_port"],
                    default_site=default_server,
                ) + "\n    "
                ipv6_http3_ssl_port_conf = ""
                if get.proxy_json_conf["ipv6_status"]:
                    ipv6_http3_ssl_port_conf = get.proxy_json_conf["ipv6_http3_ssl_port_conf"].format(
                        ipv6_port_conf=ipv6_port_conf,
                        https_port=get.proxy_json_conf["https_port"],
                        default_site=default_server,
                    ) + "\n    "
                port_conf = ipv4_http3_ssl_port_conf + ipv6_http3_ssl_port_conf + "\n    http2 on;"
            else:
                ipv4_ssl_port_conf = get.proxy_json_conf["ipv4_ssl_port_conf"].format(
                    ipv4_port_conf=ipv4_port_conf,
                    https_port=get.proxy_json_conf["https_port"],
                    default_site=default_server,
                ) + "\n    "
                ipv6_ssl_port_conf = ""
                if get.proxy_json_conf["ipv6_status"]:
                    ipv6_ssl_port_conf = get.proxy_json_conf["ipv6_ssl_port_conf"].format(
                        ipv6_port_conf=ipv6_port_conf,
                        https_port=get.proxy_json_conf["https_port"],
                        default_site=default_server,
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

        self.site_config_path = os.path.join(self.sites_config_path, get.site_name)
        if "/www/wwwroot/{site_name}" in get.proxy_json_conf["default_cache"]:
            get.proxy_json_conf["default_cache"] = self.init_site_json["default_cache"]
            if not os.path.exists(self.site_config_path + "/proxy_cache_dir"):
                public.ExecShell('mkdir -p {}'.format(self.site_config_path + "/proxy_cache_dir"))
                public.ExecShell('chown -R www:www {}'.format(self.site_config_path + "/proxy_cache_dir"))
                public.ExecShell('chmod -R 755 {}'.format(self.site_config_path + "/proxy_cache_dir"))

        default_cache = get.proxy_json_conf["default_cache"].format(
            site_config_path=self.site_config_path,
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
                    id = public.M('docker_domain').where("name=?", (get.site_name,)).getField('id')
                    if id:
                        monitor_conf = '''#Monitor-Config-Start 网站监控报表日志发送配置
        access_log syslog:server=unix:/tmp/bt-monitor.sock,nohostname,tag=dp{sid}__access {log_format};
        error_log syslog:server=unix:/tmp/bt-monitor.sock,nohostname,tag=dp{sid}__error;
        #Monitor-Config-End'''.format(sid=id, log_format=sites_data[get.site_name].get("log_format", "monitor"))
            except:
                pass

        if not "index_conf" in get.proxy_json_conf:
            get.proxy_json_conf["index_conf"] = self.init_site_json["index_conf"]
        if not "rewrite_conf" in get.proxy_json_conf:
            get.proxy_json_conf["rewrite_conf"] = ""
        if not "redirect_conf_404" in get.proxy_json_conf:
            get.proxy_json_conf["redirect_conf_404"] = ""
        if not "run_path" in get.proxy_json_conf:
            get.proxy_json_conf["run_path"] = ""
        if not "enable_php_conf" in get.proxy_json_conf:
            get.proxy_json_conf["enable_php_conf"] = False

        get.site_conf = self._template_conf.format(
            http_block=get.http_block,
            server_block=get.proxy_json_conf["server_block"],
            port_conf=port_conf,
            index_conf=get.proxy_json_conf["index_conf"],
            ssl_start_msg=public.getMsg('NGINX_CONF_MSG1'),
            err_page_msg=public.getMsg('NGINX_CONF_MSG2'),
            php_info_start=public.getMsg('NGINX_CONF_MSG3'),
            rewrite_start_msg=public.getMsg('NGINX_CONF_MSG4'),
            rewrite_conf=get.proxy_json_conf["rewrite_conf"],
            redirect_conf_404=get.proxy_json_conf["redirect_conf_404"],
            domains=' '.join(get.proxy_json_conf["domain_list"]) if len(get.proxy_json_conf["domain_list"]) > 1 else get.site_name,
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
            site_path=get.proxy_json_conf["site_path"] if not get.proxy_json_conf["stop_site"] else "{}/stop".format(self.sites_config_path),
            run_path=get.proxy_json_conf["run_path"] if get.proxy_json_conf["run_path"] != "/" else "",
            stop_site_conf=get.proxy_json_conf["stop_site_conf"] if get.proxy_json_conf["stop_site"] else "",
            websocket_support=websocket_support,
            monitor_conf=monitor_conf,
            enable_php_conf=get.proxy_json_conf["enable_php_conf"],
        )

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

    # 域名编码转换
    def ToPunycode(self, domain):
        try:
            # import OpenSSL
            import idna
        except:
            os.system("btpip install idna -I")
            import idna

        import re
        match = re.search(u"[^u\0000-u\001f]+", domain)
        if not match:
            return domain
        try:
            if domain.startswith("*."):
                return "*." + idna.encode(domain[2:]).decode("utf8")
            else:
                return idna.encode(domain).decode("utf8")
        except:
            return domain

    # 2024/4/23 下午2:12 保存并重新生成新的nginx配置文件
    def update_nginx_conf(self, get):
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
            path=self.sites_config_path,
            site_name=get.site_name
        )
        public.writeFile(self._site_proxy_conf_path, json.dumps(get.proxy_json_conf))

        return public.returnResult(msg="保存成功！")



