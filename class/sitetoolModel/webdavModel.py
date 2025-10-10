# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2017 宝塔软件(http:#bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: baozi <baozi@bt.cn>
# -------------------------------------------------------------------
# webdav 管理器
# ------------------------------
import json
import os.path
import re
import shutil
import sys
from typing import Dict, Optional, List, Tuple

os.chdir("/www/server/panel")
if "class/" not in sys.path:
    sys.path.insert(0, "class/")

import public


def is_ipv6() -> bool:
    return os.path.exists('/www/server/panel/data/ipv6.pl')


class WebDav:
    _WEBDAV_PATH = "{}/vhost/nginx/webdav".format(public.get_panel_path())
    _WEBDAV_DIR_AUTH_PATH = "{}/vhost/nginx/webdav/dir_auth/".format(public.get_panel_path())
    _WEBDAV_AUTH_PASS_PATH = "/www/server/pass/webdav_auth"
    _TEMPLATE = """server
{{
    listen {listen_port};{listen_ipv6}
    server_name {domain};

    location / {{
        # DIRECTORY-AUTH-START 身份认证相关配置，请勿删除
        include /www/server/panel/vhost/nginx/webdav/dir_auth/{site_name}.conf;
        # DIRECTORY-AUTH-END
        root {site_path}; #注意修改成自己的目录
        client_max_body_size {client_max_body_size}M; #大文件支持
        autoindex on;
        dav_methods PUT DELETE MKCOL COPY MOVE;
        # 需要 nginx-dav-ext-module 才有下面的选项
        dav_ext_methods PROPFIND OPTIONS LOCK UNLOCK;
        create_full_put_path  on;
    }}
    
    access_log  /www/wwwlogs/webdav/{site_name}.log;
    error_log  /www/wwwlogs/webdav/{site_name}.error.log;
}}
"""

    def __init__(self, site_name: str, site_path: str, domain: str, port: str, status: bool,
                 auth: Optional[Dict],client_max_body_size:int = 50):
        self.domain = domain
        self.site_name = site_name
        self.site_path = site_path
        self.port = port
        self.auth = auth
        self.status = status
        self.client_max_body_size=client_max_body_size
        # auths: Dict[str, str] = {
        #     "name": "aaa",
        #     "path": "/",
        #     "auth_name": "aaaa",
        #     "auth_value": "pass"
        # }

    def set_config(self) -> bool:
        listen_ipv6 = ''
        if is_ipv6():
            listen_ipv6 = "\n    listen [::]:%s;" % self.port
        new_config = self._TEMPLATE.format(
            listen_port=self.port,
            listen_ipv6=listen_ipv6,
            domain=self.domain,
            site_name=self.site_name,
            site_path=self.site_path,
            client_max_body_size=self.client_max_body_size
        )
        webdav_dir_auth_path = "{}/{}.conf".format(self._WEBDAV_DIR_AUTH_PATH, self.site_name)
        if not os.path.exists(self._WEBDAV_DIR_AUTH_PATH):
            os.makedirs(self._WEBDAV_DIR_AUTH_PATH, 0o600)
        webdav_conf_path = "{}/{}.conf".format(self._WEBDAV_PATH, self.site_name)
        if not os.path.isfile(webdav_dir_auth_path):
            public.writeFile(webdav_dir_auth_path, "")

        webdav_log_path = "/www/wwwlogs/webdav"
        if not os.path.exists(webdav_log_path):
            os.makedirs(webdav_log_path, 0o700)
            public.ExecShell("chown www:www {}".format(webdav_log_path))

        public.writeFile(webdav_conf_path, new_config)
        if public.checkWebConfig() is not True:
            os.remove(webdav_conf_path)
            return False

        public.serviceReload()
        return True

    def remove(self):
        auth_pass_file = "{}/{}.pass".format(self._WEBDAV_AUTH_PASS_PATH, self.site_name)
        dir_auth_file = "{}/{}.conf".format(self._WEBDAV_DIR_AUTH_PATH, self.site_name)
        webdav_conf_file = "{}/{}.conf".format(self._WEBDAV_PATH, self.site_name)
        if os.path.exists(auth_pass_file):
            os.remove(auth_pass_file)

        if os.path.exists(dir_auth_file):
            os.remove(dir_auth_file)

        if os.path.exists(webdav_conf_file):
            os.remove(webdav_conf_file)
            public.serviceReload()

    def close(self):
        webdav_conf_file = "{}/{}.conf".format(self._WEBDAV_PATH, self.site_name)
        if os.path.exists(webdav_conf_file):
            os.remove(webdav_conf_file)
            public.serviceReload()
        self.status = False

    def open(self) -> bool:
        if not self.set_config():
            return False
        self.status = True
        return True

    def set_auth(self, auth_name: str, auth_value: str) -> Tuple[bool, str]:
        if not auth_name or not auth_value:
            return False, "验证名称或密码不能为空"
        # 允许的字符：字母（大小写）、数字、常见符号
        if not re.match(r'^[A-Za-z0-9!@#$%^&*\-_]+$', auth_value):
            return False, "密码中只能包含字母（大小写）、数字、英文的常见符号（如 !, @, #, $, %, ^, &, *, -, _）。"
        self.auth = {
            "auth_name": auth_name,
            "auth_value": auth_value
        }

        self._set_auth()
        return True, "添加成功"

    def remove_auth(self) -> Tuple[bool, str]:

        self.auth = None

        auth_pass_file = "{}/{}.pass".format(self._WEBDAV_AUTH_PASS_PATH, self.site_name)
        dir_auth_file = "{}/{}.conf".format(self._WEBDAV_DIR_AUTH_PATH, self.site_name)

        if os.path.exists(auth_pass_file):
            os.remove(auth_pass_file)
        public.writeFile(dir_auth_file, "")

        return True, "删除成功"

    def to_conf(self):
        return {
            "domain": self.domain,
            "site_name": self.site_name,
            "site_path": self.site_path,
            "port": self.port,
            "status": self.status,
            "auth": self.auth,
            "client_max_body_size": self.client_max_body_size  
        }

    def _set_auth(self):
        auth_pass_file = "{}/{}.pass".format(self._WEBDAV_AUTH_PASS_PATH, self.site_name)
        if not os.path.exists(self._WEBDAV_AUTH_PASS_PATH):
            os.makedirs(self._WEBDAV_AUTH_PASS_PATH, 0o755)
        dir_auth_path = "{}/{}".format(self._WEBDAV_DIR_AUTH_PATH, self.site_name)
        if not os.path.exists(dir_auth_path):
            os.makedirs(dir_auth_path, 0o755)

        auth_conf = """
#AUTH_START
auth_basic "Authorization";
auth_basic_user_file /www/server/pass/webdav_auth/{site_name}.pass;
#AUTH_END
""".format(
            site_name=self.site_name,
        )
        pass_str = "{}:{}".format(self.auth["auth_name"], public.hasPwd(self.auth["auth_value"]))
        public.writeFile(auth_pass_file, pass_str)
        public.writeFile("{}/{}.conf".format(self._WEBDAV_DIR_AUTH_PATH, self.site_name), auth_conf)


class WebDavManager:
    _CONF_FILE = "{}/data/nginx_webdav.conf".format(public.get_panel_path())
    _WEBDAV_PATH = "{}/vhost/nginx/webdav".format(public.get_panel_path())
    _WEBDAV_DIR_AUTH_PATH = "{}/vhost/nginx/webdav/dir_auth/".format(public.get_panel_path())

    def __init__(self):
        self._config = None

    @property
    def config(self) -> Dict:
        if self._config is not None:
            return self._config
        default_config = dict()
        try:
            self._config = json.loads(public.readFile(self._CONF_FILE))
        except (json.JSONDecodeError, TypeError):
            pass
        if isinstance(self._config, dict):
            return self._config
        self._config = default_config
        return self._config

    def save_config(self):
        public.writeFile(self._CONF_FILE, json.dumps(self.config))

    # 检查webdav的引入是否在主配置文件中
    @classmethod
    def check_webdav_conf(cls):
        if not os.path.isdir(cls._WEBDAV_PATH):
            os.makedirs(cls._WEBDAV_PATH, 0o600)
        webdav_log_path = "/www/wwwlogs/webdav"
        if not os.path.exists(webdav_log_path):
            os.makedirs(webdav_log_path, 0o700)
            public.ExecShell("chown www:www {}".format(webdav_log_path))
        nginx_conf_path = "/www/server/nginx/conf/nginx.conf"
        nginx_conf = public.readFile(nginx_conf_path)
        if not isinstance(nginx_conf, str):
            raise ValueError("Nginx主配置文件丢失，无法操作")
        if nginx_conf.find("/www/server/panel/vhost/nginx/webdav/*.conf;") == -1:
            rep = re.compile("include +/www/server/panel/vhost/nginx/\*\.conf;\n")
            sun_conf_str = (
                "include /www/server/panel/vhost/nginx/*.conf;\n"
                "include /www/server/panel/vhost/nginx/webdav/*.conf;\n"
            )
            new_conf = rep.sub(sun_conf_str, nginx_conf, 1)
            public.writeFile(nginx_conf_path, new_conf)
            if public.checkWebConfig() is not True:
                public.writeFile(nginx_conf_path, nginx_conf)
                raise ValueError("配置文件存在错误，无法操作")
        return None

    # 检查用户的nginx是否存在dav模块
    @staticmethod
    def check_webdav_model():
        out, _ = public.ExecShell("nginx -V 2>&1 | grep 'nginx-dav-ext-module'")
        if out == "":
            raise ValueError("当前的nginx未编译WebDav模块，请重新安装")

        return None

    @staticmethod
    def check_domain(domain: str, port: str) -> bool:
        try:
            int_port = int(port)
            if int_port < 1 or int_port > 65535:
                return False
        except ValueError:
            return False

        return public.is_domain(domain)

    @staticmethod
    def check_domain_exists(domain: str, port: str) -> bool:
        res = public.M('domain').where("name=? and port=?", (domain, int(port))).select()
        if isinstance(res, str):
            return False
        if isinstance(res, list) and len(res) > 0:
            return True
        return False

    def get_web_dav(self, site_name) -> Optional[WebDav]:
        if site_name not in self.config:
            return None
        info = self.config[site_name]
        return WebDav(
            site_name=info["site_name"],
            site_path=info["site_path"],
            domain=info["domain"],
            port=info["port"],
            auth=info.get("auth", None),
            status=info["status"],
            client_max_body_size=info.get("client_max_body_size", 50),
        )

    def _check_env(self) -> Tuple[bool, str]:
        try:
            self.check_webdav_model()
            self.check_webdav_conf()
        except ValueError as e:
            return False, str(e)
        return True, ""

    def add_web_dav(self, site_id, domain: str, port: str,client_max_body_size:int=50) -> Tuple[bool, str]:
        site_info = public.M("sites").where('id=?', (site_id,)).field('id,path,name').find()
        if isinstance(site_info, str):
            return False, "网站查询错误"

        flag, err = self._check_env()
        if not flag:
            return False, err

        if not isinstance(site_info, dict):
            return False, "没有该网站"

        if not self.check_domain(domain, port):
            return False, "域名错误"

        if not self.check_domain(domain, port):
            return False, "域名错误"

        if self.check_domain_exists(domain, port):
            return False, "域名已存在"

        webdav = WebDav(
            site_name=site_info["name"],
            site_path=site_info["path"],
            domain=domain,
            port=port,
            auth=None,
            status=True,
            client_max_body_size=client_max_body_size
        )

        flag = webdav.set_config()
        if not flag:
            return False, "添加失败"

        self.config[webdav.site_name] = webdav.to_conf()
        self.save_config()
        
        return True, "添加成功"

    def remove_web_dav(self, site_name) -> Tuple[bool, str]:
        webdav = self.get_web_dav(site_name)
        if webdav:
            webdav.remove()
            del self.config[site_name]
            self.save_config()
        return True, "删除成功"

    def set_web_dav(self, site_name, option) -> Tuple[bool, str]:
        webdav = self.get_web_dav(site_name)
        if webdav:
            if option in ("close", "closed", "0"):
                webdav.close()
                self.config[site_name] = webdav.to_conf()
                self.save_config()
                return True, "关闭成功"
            else:
                if not webdav.open():
                    return False, "开启失败"
                else:
                    self.config[site_name] = webdav.to_conf()
                    self.save_config()
                    return True, "开启成功"
        else:
            return False, "没有指定的WebDav配置"


class main:

    @staticmethod
    def get_webdav_conf(get):
        try:
            site_name = get.site_name.strip()
        except AttributeError:
            return public.returnMsg(False, "参数错误")

        webdav = WebDavManager().get_web_dav(site_name)
        if not webdav:
            return {"need_create": True}

        data = webdav.to_conf()
        data["need_create"] = False
        return data

    @staticmethod
    def add_webdav(get):
        try:
            
            # 确保client_max_body_size存在并且可以转换为整数
            if not hasattr(get, 'client_max_body_size'):
                get.client_max_body_size = 50
            client_max_body_size = int(get.client_max_body_size)
            
            site_id = int(get.site_id.strip())
            tmp_domain = get.domain.strip()
        except (AttributeError, ValueError):
            return public.returnMsg(False, "参数错误")
        tmp = tmp_domain.split(":")
        if len(tmp) == 1 or tmp[1] == "":
            domain = tmp[0]
            port = "80"
        else:
            domain = tmp[0]
            port = tmp[1]

        return public.returnMsg(*WebDavManager().add_web_dav(site_id, domain, port,client_max_body_size))

    @staticmethod
    def set_webdav(get):
        try:
            site_name = get.site_name.strip()
            option = get.option.strip()
        except (AttributeError, ValueError):
            return public.returnMsg(False, "参数错误")

        return public.returnMsg(*WebDavManager().set_web_dav(site_name, option))

    @staticmethod
    def remove_webdav(get):
        try:
            site_name = get.site_name.strip()
        except (AttributeError, ValueError):
            return public.returnMsg(False, "参数错误")

        return public.returnMsg(*WebDavManager().remove_web_dav(site_name))

    @staticmethod
    def set_client_max_body_size(get):
        try:
            try:
                site_name = get.site_name.strip()
                client_max_body_size = int(get.client_max_body_size.strip())  # 获取上传大小限制
            
            except (AttributeError, ValueError):
                return public.returnMsg(False, "参数错误")


            manager = WebDavManager()
            webdav = manager.get_web_dav(site_name)
            if not webdav:
                return public.returnMsg(False, "没有指定的WebDav配置")
            webdav.client_max_body_size = client_max_body_size
            manager.config[site_name] = webdav.to_conf()
            manager.save_config()
            webdav.set_config()
            public.serviceReload()

            return public.returnMsg(True, "设置成功")
        except Exception as e:
            return public.returnMsg(False, str(e))
    @staticmethod
    def set_auth(get):
        try:
            site_name = get.site_name.strip()
            auth_name = get.auth_name.strip()
            auth_value = get.auth_value.strip()
        except (AttributeError, ValueError):
            return public.returnMsg(False, "参数错误")

        if len(auth_value) < 3:
            return public.returnMsg(False, '密码不能少于3位')
        if len(auth_value) > 8:
            return public.returnMsg(False, '密码不能大于8位，超过8位的部分无法验证。')
        if re.search('\s', auth_value):
            return public.returnMsg(False, '密码不能存在空格')

        manager = WebDavManager()
        webdav = manager.get_web_dav(site_name)
        if not webdav:
            return public.returnMsg(False, "没有指定的WebDav配置")
        flag, msg = webdav.set_auth(
            auth_name=auth_name,
            auth_value=auth_value,
        )
        if flag:
            manager.config[site_name] = webdav.to_conf()
            manager.save_config()
            public.serviceReload()

        return public.returnMsg(flag, msg)

    @staticmethod
    def remove_auth(get):
        try:
            site_name = get.site_name.strip()
        except (AttributeError, ValueError):
            return public.returnMsg(False, "参数错误")

        manager = WebDavManager()
        webdav = manager.get_web_dav(site_name)
        if not webdav:
            return public.returnMsg(False, "没有指定的WebDav配置")
        flag, msg = webdav.remove_auth()
        if flag:
            manager.config[site_name] = webdav.to_conf()
            manager.save_config()
            public.serviceReload()

        return public.returnMsg(flag, msg)


