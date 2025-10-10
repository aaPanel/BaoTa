import os
import re
import shutil
import sys
from typing import List, Optional, Union, Tuple

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public
from mod.base.web_conf.util import listen_ipv6, get_log_path, GET_CLASS, service_reload
from mod.base.web_conf import NginxDomainTool, ApacheDomainTool


class JavaNginxTool:
    def __init__(self):
        self._panel_path = "/www/server/panel"
        self._vhost_path = "{}/vhost".format(self._panel_path)
        self._nginx_bak_path = "/var/tmp/springboot/nginx_conf_backup"
        if not os.path.exists(self._nginx_bak_path):
            os.makedirs(self._nginx_bak_path, 0o600)

    def set_nginx_config(self, project_data: dict, domains: List[Tuple[str, Union[str, int]]],
                         use_ssl: bool = False, force_ssl=False):
        if use_ssl:
            use_http2_on = public.is_change_nginx_http2()
            use_http3 = public.is_nginx_http3()
        else:
            use_http2_on = False
            use_http3 = False

        project_config = project_data["project_config"]
        if project_config['java_type'] == "springboot":
            project_path = project_data["project_config"]["jar_path"]
        else:
            project_path = project_data["path"]
            if os.path.isfile(project_path):
                project_path = os.path.dirname(project_path)

        port_set = set()
        domain_set = set()
        use_ipv6 = listen_ipv6()
        listen_ports_list = []
        for d, p in domains:
            if str(p) == "443":  # 443 端口特殊处理
                continue
            if str(p) not in port_set:
                listen_ports_list.append("    listen {};".format(str(p)))
                if use_ipv6:
                    listen_ports_list.append("    listen [::]:{};".format(str(p)))

            port_set.add(str(p))
            domain_set.add(d)

        if use_ssl:
            if not use_http2_on:
                http2 = " http2"
            else:
                http2 = ""
                listen_ports_list.append("    http2 on;")

            listen_ports_list.append("    listen 443 ssl{};".format(http2))
            if use_ipv6:
                listen_ports_list.append("    listen [::]:443 ssl{};".format(http2))

            if use_http3:
                listen_ports_list.append("    listen 443 quic;")
                if use_ipv6:
                    listen_ports_list.append("    listen [::]:443 quic;")

        listen_ports = "\n".join(listen_ports_list).strip()

        static_conf = self._build_static_conf(project_config, project_path)
        proxy_conf = self._build_proxy_conf(project_config)
        ssl_conf = "#error_page 404/404.html;"
        if use_ssl:
            ssl_conf += "\n" + self._build_ssl_conf(project_config, use_http3=use_http3, force_ssl=force_ssl)

        nginx_template_file = "{}/template/nginx/java_mod_http.conf".format(self._vhost_path)
        nginx_conf_file = "{}/nginx/java_{}.conf".format(self._vhost_path, project_data["name"])

        nginx_template = public.ReadFile(nginx_template_file)
        if not isinstance(nginx_template, str):
            return "读取模版文件失败"

        nginx_conf = nginx_template.format(
            listen_ports=listen_ports,
            domains=" ".join(domain_set),
            site_path=project_path,
            site_name=project_data["name"],
            panel_path=self._panel_path,
            log_path=get_log_path(),
            ssl_conf=ssl_conf,
            static_conf=static_conf,
            proxy_conf=proxy_conf,
        )
        from mod.base.web_conf import ng_ext
        nginx_conf = ng_ext.set_extension_by_config(project_data["name"], nginx_conf)
        rewrite_file = "{}/rewrite/java_{}.conf".format(self._vhost_path, project_data["name"])
        if not os.path.exists(rewrite_file):
            public.writeFile(rewrite_file, '# 请将伪静态规则或自定义NGINX配置填写到此处\n')
        apply_check = "{}/nginx/well-known/{}.conf".format(self._vhost_path, project_data["name"])
        if not os.path.exists(os.path.dirname(apply_check)):
            os.makedirs(os.path.dirname(apply_check), 0o600)
        if not os.path.exists(apply_check):
            public.writeFile(apply_check, '')

        public.writeFile(nginx_conf_file, nginx_conf)
        return None

    @staticmethod
    def _build_proxy_conf(project_config: dict) -> str:
        if "proxy_info" not in project_config:
            return ""

        proxy_info = project_config["proxy_info"]
        proxy_conf_list = []
        if not proxy_info:
            return ""
        ng_proxy = '''    #PROXY-START{proxy_dir}
    location {proxy_dir} {{{rewrite}
        proxy_pass {proxy_url};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;{add_headers}
        proxy_set_header REMOTE-HOST $remote_addr;
        add_header X-Cache $upstream_cache_status;
        proxy_set_header X-Host $host:$server_port;
        proxy_set_header X-Scheme $scheme;
        proxy_connect_timeout 30s;
        proxy_read_timeout 86400s;
        proxy_send_timeout 30s;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }}
    #PROXY-END{proxy_dir}'''
        for i in proxy_info:
            if i.get("status", False):
                continue
            rewrite = ""
            if "rewrite" in i and i["rewrite"].get("status", False):
                rewrite = i["rewrite"]
                src_path = i["src_path"]
                if not src_path.endswith("/"):
                    src_path += "/"
                target_path = rewrite["target_path"]
                if target_path.endswith("/"):
                    target_path += target_path[:-1]

                rewrite = "\n        rewrite ^{}(.*)$ {}/$1 break;".format(src_path, target_path)

            add_headers = ""
            if "add_headers" in i:
                header_tmp = "        add_header {} {};"
                add_headers_list = [header_tmp.format(h["k"], h["v"]) for h in i["add_headers"] if
                                    "k" in h and "v" in h]
                add_headers = "\n".join(add_headers_list)
                if add_headers:
                    add_headers = "\n" + add_headers

            proxy_conf_list.append(ng_proxy.format(
                proxy_dir=i["proxy_dir"],
                rewrite=rewrite,
                add_headers=add_headers,
                proxy_url="http://127.0.0.1:{}".format(i["proxy_port"]),
            ))

        return ("\n".join(proxy_conf_list) + "\n").lstrip()

    @staticmethod
    def _build_static_conf(project_config: dict, default_path: str) -> str:
        if project_config['java_type'] == "springboot" and "static_info" in project_config:
            static_info = project_config["static_info"]
            if not static_info.get("status", False):
                return ""
            index_str = "index.html"
            index = static_info.get("index", "")
            if index:
                if isinstance(index, list):
                    index_str = " ".join(index)
                elif isinstance(index, str):
                    index_str = " ".join([i.strip() for i in index.split(",") if i.strip()])

            path = static_info.get("path")
            if not path:
                path = default_path
            try_file = ''
            if static_info.get("use_try_file", True):
                try_file = "         try_files $uri $uri/ /index.html;\n"
            static_conf = (
                              "location / {\n"
                              "         root %s;\n"
                              "         index %s;\n%s"
                              "    }"
                          ) % (path, index_str, try_file)

            return static_conf
        return ""

    def _build_ssl_conf(self, project_config: dict, use_http3=False, force_ssl=False) -> str:
        force_ssl_str = ""
        if force_ssl:
            force_ssl_str = '''
    #HTTP_TO_HTTPS_START
    if ($server_port !~ 443){
        rewrite ^(/.*)$ https://$host$1 permanent;
    }
    #HTTP_TO_HTTPS_END'''
        http3_header = ""
        if use_http3:
            http3_header = '''\n    add_header Alt-Svc 'quic=":443"; h3=":443"; h3-27=":443";h3-29=":443";h3-25=":443"; h3-T050=":443"; h3-Q050=":443";h3-Q049=":443";h3-Q048=":443"; h3-Q046=":443"; h3-Q043=":443"';'''

        return '''    ssl_certificate    {vhost_path}/cert/{project_name}/fullchain.pem;
    ssl_certificate_key    {vhost_path}/cert/{project_name}/privkey.pem;
    ssl_protocols TLSv1.1 TLSv1.2 TLSv1.3;
    ssl_ciphers EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    add_header Strict-Transport-Security "max-age=31536000";{http3_header}
    error_page 497  https://$host$request_uri;{force_ssl}'''.format(
            vhost_path=self._vhost_path,
            project_name=project_config["project_name"],
            http3_header=http3_header,
            force_ssl=force_ssl_str,
        )

    def open_nginx_config_file(self, project_data: dict, domains: List[Tuple[str, str]], ) -> Optional[str]:
        project_name = project_data["name"]
        back_path = "{}/{}".format(self._nginx_bak_path, project_name)
        target_file = "{}/nginx/java_{}.conf".format(self._vhost_path, project_name)
        if os.path.isfile(target_file):
            return

        if os.path.isfile(back_path):
            shutil.copyfile(back_path, target_file)
            if os.path.isfile(target_file):
                NginxDomainTool("java_").nginx_set_domain(project_name, *domains)
                error_msg = public.checkWebConfig()
                if not isinstance(error_msg, str):  # 没有报错时直接退出
                    service_reload()
                    return

        res = self.set_nginx_config(project_data, domains, use_ssl=False)
        if not res:
            service_reload()
        return res

    def close_nginx_config_file(self, project_data: dict) -> None:
        project_name = project_data["name"]
        back_path = "{}/{}".format(self._nginx_bak_path, project_name)
        target_file = "{}/nginx/java_{}.conf".format(self._vhost_path, project_name)
        if not os.path.isfile(target_file):
            return

        if os.path.isfile(back_path):
            os.remove(back_path)

        shutil.move(target_file, back_path)
        service_reload()

    def exists_nginx_ssl(self, project_name):
        """
           判断项目是否配置Nginx SSL配置
        """
        config_file = "{}/nginx/java_{}.conf".format(self._vhost_path, project_name)
        if not os.path.exists(config_file):
            return False, False

        config_body = public.readFile(config_file)
        if isinstance(config_body, str):
            return False, False

        is_ssl, is_force_ssl = False, False
        if config_body.find('ssl_certificate') != -1:
            is_ssl = True
        if config_body.find('HTTP_TO_HTTPS_START') != -1:
            is_force_ssl = True
        return is_ssl, is_force_ssl

    def set_static_path(self, project_data: dict) -> Optional[Union[bool, str]]:
        project_path = project_data["project_config"]["jar_path"]
        static_str = self._build_static_conf(project_data["project_config"], project_path)
        ng_file = "{}/nginx/java_{}.conf".format(self._vhost_path, project_data["name"])
        ng_conf = public.readFile(ng_file)
        if not isinstance(ng_conf, str):
            return "配置文件读取错误"

        static_conf = "#STATIC-START 静态资源相关配置\n    {}\n    #STATIC-END".format(static_str)
        rep_static = re.compile(r"#STATIC-START(.*\n){2,9}\s*#STATIC-END.*")
        res = rep_static.search(ng_conf)
        if res:
            new_ng_conf = ng_conf.replace(res.group(), static_conf)
            public.writeFile(ng_file, new_ng_conf)
            error_msg = public.checkWebConfig()
            if not isinstance(error_msg, str):  # 没有报错时直接退出
                service_reload()
                return None
            else:
                public.writeFile(ng_file, ng_conf)
                return 'WEB服务器配置配置文件错误ERROR:<br><font style="color:red;">' + \
                    error_msg.replace("\n", '<br>') + '</font>'

        # 添加配置信息到配置文件中
        rep_list = [
            (re.compile(r"\s*#PROXY-LOCAl-START.*", re.M), True),  # 添加到反向代理结尾的上面
            (re.compile(r"\s*#REWRITE-END.*", re.M), False),  # 添加到伪静态的下面
            (re.compile(r"\s*#SSL-END.*", re.M), False),  # 添加到SSL END的下面
        ]

        # 使用正则匹配确定插入位置
        def set_by_rep_idx(tmp_rep: re.Pattern, use_start: bool) -> bool:
            tmp_res = tmp_rep.search(ng_conf)
            if not tmp_res:
                return False
            if use_start:
                new_conf = ng_conf[:tmp_res.start()] + static_conf + tmp_res.group() + ng_conf[tmp_res.end():]
            else:
                new_conf = ng_conf[:tmp_res.start()] + tmp_res.group() + static_conf + ng_conf[tmp_res.end():]

            public.writeFile(ng_file, new_conf)
            if public.get_webserver() == "nginx" and isinstance(public.checkWebConfig(), str):
                public.writeFile(ng_file, ng_conf)
                return False
            return True

        for r, s in rep_list:
            if set_by_rep_idx(r, s):
                service_reload()
                return None
        else:
            return False


class JavaApacheTool:
    def __init__(self):
        self._panel_path = "/www/server/panel"
        self._vhost_path = "{}/vhost".format(self._panel_path)
        self._apache_bak_path = "/var/tmp/springboot/httpd_conf_backup"
        if not os.path.exists(self._apache_bak_path):
            os.makedirs(self._apache_bak_path, 0o600)

    def set_apache_config_for_ssl(self, project_data):
        domains = public.M('domain').where('pid=?', (project_data["id"],)).select()
        domain_list = [(i["name"], i["port"]) for i in domains]
        return self.set_apache_config(project_data, domain_list, use_ssl=True)

    def set_apache_config(self, project_data: dict, domains: List[Tuple[str, Union[str, int]]],
                          use_ssl: bool = False, force_ssl: bool = False):
        name = project_data['name']
        port_set = set()
        domain_set = set()
        for d, p in domains:
            port_set.add(str(p))
            domain_set.add(d)

        domains_str = ' '.join(domain_set)
        project_config = project_data["project_config"]
        if project_config['java_type'] == "springboot":
            project_path = project_data["project_config"]["jar_path"]
        else:
            project_path = project_data["path"]
            if os.path.isfile(project_path):
                project_path = os.path.dirname(project_path)

        apache_template_file = "{}/template/apache/java_mod_http.conf".format(self._vhost_path)
        apache_conf_file = "{}/apache/java_{}.conf".format(self._vhost_path, name)

        apache_template = public.ReadFile(apache_template_file)
        if not isinstance(apache_template, str):
            return "读取模版文件失败"

        apache_conf_list = []
        proxy_conf = self._build_proxy_conf(project_config)
        for p in port_set:
            apache_conf_list.append(apache_template.format(
                site_path=project_path,
                server_name='{}.{}'.format(p, project_path),
                domains=domains_str,
                log_path=get_log_path(),
                server_admin='admin@{}'.format(name),
                port=p,
                ssl_config='',
                project_name=name,
                proxy_conf=proxy_conf,
            ))

        if use_ssl:
            ssl_config = '''SSLEngine On
    SSLCertificateFile {vhost_path}/cert/{project_name}/fullchain.pem
    SSLCertificateKeyFile {vhost_path}/cert/{project_name}/privkey.pem
    SSLCipherSuite EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5
    SSLProtocol All -SSLv2 -SSLv3 -TLSv1
    SSLHonorCipherOrder On'''.format(project_name=name, vhost_path=public.get_vhost_path())
            if force_ssl:
                ssl_config += '''
    #HTTP_TO_HTTPS_START
    <IfModule mod_rewrite.c>
        RewriteEngine on
        RewriteCond %{SERVER_PORT} !^443$
        RewriteRule (.*) https://%{SERVER_NAME}$1 [L,R=301]
    </IfModule>
    #HTTP_TO_HTTPS_END'''

            apache_conf_list.append(apache_template.format(
                site_path=project_path,
                server_name='{}.{}'.format("443", project_path),
                domains=domains_str,
                log_path=get_log_path(),
                server_admin='admin@{}'.format(name),
                port="443",
                ssl_config=ssl_config,
                project_name=name,
                proxy_conf=proxy_conf,
            ))

        apache_conf = '\n'.join(apache_conf_list)
        from mod.base.web_conf import ap_ext
        apache_conf = ap_ext.set_extension_by_config(name, apache_conf)
        public.writeFile(apache_conf_file, apache_conf)
        ApacheDomainTool.apache_add_ports(*port_set)
        return None

    @staticmethod
    def _build_proxy_conf(project_config: dict) -> str:
        if "proxy_info" not in project_config:
            return ""

        proxy_info = project_config["proxy_info"]
        proxy_conf_list = []
        if not proxy_info:
            return ""
        ap_proxy = '''    #PROXY-START{proxy_dir}
    <IfModule mod_proxy.c>
        ProxyRequests Off
        SSLProxyEngine on
        ProxyPass {proxy_dir} {proxy_url}/
        ProxyPassReverse {proxy_dir} {proxy_url}/
        RequestHeader set Host "%{Host}e"
        RequestHeader set X-Real-IP "%{REMOTE_ADDR}e"
        RequestHeader set X-Forwarded-For "%{X-Forwarded-For}e"
        RequestHeader setifempty X-Forwarded-For "%{REMOTE_ADDR}e"
    </IfModule>
    #PROXY-END{proxy_dir}'''

        for i in proxy_info:
            if i.get("status", False):
                continue

            proxy_conf_list.append(ap_proxy.format(
                proxy_dir=i["proxy_dir"],
                proxy_url="http://127.0.0.1:{}".format(i["proxy_port"]),
            ))

        return ("\n".join(proxy_conf_list) + "\n").lstrip()

    def open_apache_config_file(self, project_data: dict, domains: List[Tuple[str, str]]) -> Optional[str]:
        project_name = project_data["name"]
        back_path = "{}/{}".format(self._apache_bak_path, project_name)
        target_file = "{}/apache/java_{}.conf".format(self._vhost_path, project_name)
        if os.path.isfile(target_file):
            return

        if os.path.isfile(back_path):
            shutil.copyfile(back_path, target_file)
            if os.path.isfile(target_file):
                ApacheDomainTool("java_").apache_set_domain(project_name, *domains)
                error_msg = public.checkWebConfig()
                if not isinstance(error_msg, str):  # 没有报错时直接退出
                    service_reload()
                    return

        res = self.set_apache_config(
            project_data,
            domains=domains,
            use_ssl=False,
        )

        if not res:
            service_reload()
        return res

    def close_apache_config_file(self, project_data: dict) -> None:
        project_name = project_data["name"]
        back_path = "{}/{}".format(self._apache_bak_path, project_name)
        target_file = "{}/apache/java_{}.conf".format(self._vhost_path, project_name)
        if not os.path.isfile(target_file):
            return

        if os.path.isfile(back_path):
            os.remove(back_path)

        shutil.move(target_file, back_path)
        service_reload()

    def exists_apache_ssl(self, project_name) -> Tuple[bool, bool]:
        """
            判断项目是否配置Apache SSL配置
        """
        config_file = "{}/apache/java_{}.conf".format(self._vhost_path, project_name)
        if not os.path.exists(config_file):
            return False, False

        config_body = public.readFile(config_file)
        if not isinstance(config_body, str):
            return False, False

        is_ssl, is_force_ssl = False, False
        if config_body.find('SSLCertificateFile') != -1:
            is_ssl = True
        if config_body.find('HTTP_TO_HTTPS_START') != -1:
            is_force_ssl = True
        return is_ssl, is_force_ssl


class JavaWebConfig:

    def __init__(self):
        self._ng_conf_onj = JavaNginxTool()
        self._ap_conf_onj = JavaApacheTool()
        self.ws_type = public.get_webserver()

    def create_config(self, project_data: dict, domains: List[Tuple[str, Union[str, int]]],
                      use_ssl: bool = False, force_ssl=False):
        ng_res = self._ng_conf_onj.set_nginx_config(project_data, domains, use_ssl, force_ssl=force_ssl)
        ap_res = self._ap_conf_onj.set_apache_config(project_data, domains, use_ssl, force_ssl=force_ssl)
        if self.ws_type == "nginx" and ng_res:
            return ng_res
        elif self.ws_type == "apache" and ap_res:
            return ap_res
        service_reload()

    def _open_config_file(self, project_data: dict):
        domain_list = public.M('domain').where('pid=?', (project_data["id"],)).field("name,port").select()
        domains = [(i["name"], str(i["port"])) for i in domain_list]
        if not domains:
            return "域名不能为空"
        ng_res = self._ng_conf_onj.open_nginx_config_file(project_data, domains)
        ap_res = self._ap_conf_onj.open_apache_config_file(project_data, domains)
        if self.ws_type == "nginx" and ng_res:
            return ng_res
        elif self.ws_type == "apache" and ap_res:
            return ap_res

    def _close_apache_config_file(self, project_data: dict) -> None:
        self._ap_conf_onj.close_apache_config_file(project_data)
        self._ng_conf_onj.close_nginx_config_file(project_data)

    def _set_domain(self, project_data: dict, domains: List[Tuple[str, str]]) -> Optional[str]:
        ng_res = NginxDomainTool("java_").nginx_set_domain(project_data["name"], *domains)
        ap_res = ApacheDomainTool("java_").apache_set_domain(project_data["name"], *domains)
        if self.ws_type == "nginx" and ng_res:
            return ng_res
        elif self.ws_type == "apache" and ap_res:
            return ap_res

    def _get_ssl_status(self, project_name) -> Tuple[bool, bool]:
        if self.ws_type == "nginx":
            return self._ng_conf_onj.exists_nginx_ssl(project_name)
        elif self.ws_type == "apache":
            return self._ap_conf_onj.exists_apache_ssl(project_name)
        return False, False

    def _set_static_path(self, project_data: dict):
        if self.ws_type == "nginx":
            res = self._ng_conf_onj.set_static_path(project_data)
            if res is None:
                return None
            elif res is False:
                err_msg = public.checkWebConfig()
                if isinstance(err_msg, str):
                    return 'WEB服务器配置配置文件错误ERROR:<br><font style="color:red;">' + \
                        err_msg.replace("\n", '<br>') + '</font>'

                return self._open_config_file(project_data)
            else:
                return res
        return "只支持nginx设置静态路由"
