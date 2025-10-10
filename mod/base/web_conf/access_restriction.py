# 访问限制, 目前不兼容之前版本的访问限制
# nginx 使用 if 和 正则实现，保障与反向代理、重定向的兼容性
# apache 实现方案未变
import os
import re
import json
import shutil
from typing import Optional, Union, List, Dict
from itertools import chain
from .util import webserver, check_server_config, write_file, read_file, DB, service_reload, get_log_path, pre_re_key
from mod.base import json_response


class _ConfigObject:
    _config_file_path = ""
    panel_path = "/www/server/panel"

    def __init__(self):
        self._config: Optional[dict] = None

    @property
    def config(self) -> Dict[str, dict]:
        if self._config is None:
            try:
                self._config = json.loads(read_file(self._config_file_path))
            except (json.JSONDecodeError, TypeError, ValueError):
                self._config = {}
        return self._config

    def save_config(self):
        if self._config:
            write_file(self._config_file_path, json.dumps(self._config))


class ServerConfig:
    _vhost_path = "/www/server/panel/vhost"

    def __init__(self, config_prefix: str):
        self.config_prefix: str = config_prefix

    @staticmethod
    def crypt_password(password) -> str:
        import crypt
        return crypt.crypt(password,password)


# nginx配置文件相关操作
class _NginxAccessConf(ServerConfig):

    # 添加 include 导入配置项
    def set_nginx_access_include(self, site_name) -> Optional[str]:
        ng_file = "{}/nginx/{}{}.conf".format(self._vhost_path, self.config_prefix, site_name)
        ng_conf = read_file(ng_file)
        if not ng_conf:
            return "配置文件丢失"
        access_dir = "{}/nginx/access/{}".format(self._vhost_path, site_name)
        if not os.path.isdir(os.path.dirname(access_dir)):
            os.makedirs(os.path.dirname(access_dir))

        if not os.path.isdir(access_dir):
            os.makedirs(access_dir)

        include_conf = (
            "    #引用访问限制规则，注释后配置的访问限制将无效\n"
            "    include /www/server/panel/vhost/nginx/access/%s/*.conf;\n"
        ) % site_name

        rep_include = re.compile(r"\s*include.*/access/.*/\*\.conf\s*;", re.M)
        if rep_include.search(ng_conf):
            return
        # 添加 引入
        rep_list = [
            (re.compile(r"#SSL-END"), False),  # 匹配Referer配置, 加其下
            (re.compile(r"(\s*#.*)?\s*include\s+.*/redirect/.*\.conf;"), True),  # 重定向
            (re.compile(r"(\s*#.*)?\s*include\s+.*/ip-restrict/.*\.conf;"), True),  # Ip黑白名单
        ]

        # 使用正则匹配确定插入位置 use_start 在前面插入还是后面插入
        def set_by_rep_idx(tmp_rep: re.Pattern, use_start: bool) -> bool:
            tmp_res = tmp_rep.search(ng_conf)
            if not tmp_res:
                return False
            if use_start:
                new_conf = ng_conf[:tmp_res.start()] + include_conf + tmp_res.group() + ng_conf[tmp_res.end():]
            else:
                new_conf = ng_conf[:tmp_res.start()] + tmp_res.group() + include_conf + ng_conf[tmp_res.end():]

            write_file(ng_file, new_conf)
            if webserver() == "nginx" and check_server_config() is not None:
                write_file(ng_file, ng_conf)
                return False
            return True
        for r, s in rep_list:
            if set_by_rep_idx(r, s):
                break
        else:
            return "无法在配置文件中定位到需要添加的项目"

    # 写入配置文件
    def set_nginx_access_by_conf(self, site_name: str, configs: Dict[str, List[Dict[str, str]]]) -> Optional[str]:
        """  configs 示例结构
        configs = {
            "auth_dir": [
                {
                    "name": "aaa",
                    "dir_path": "/",
                    "auth_file": "/www/server/pass/www.cache.com/aaa.pass",
                    "username":"aaaa",
                    "password":"aaaa",
                }
            ],
            "file_deny": [
                {
                    "name": "bbb",
                    "dir_path": "/",
                    "suffix": ["png", "jpg"]
                }
            ]
        }
        """

        path_map = {}
        for c in chain(configs.get("auth_dir", []), configs.get("file_deny", [])):
            if c["dir_path"] not in path_map:
                path_map[c["dir_path"]] = {"path": c["dir_path"]}
            path_map[c["dir_path"]].update(c)

        path_list = list(path_map.values())
        path_list.sort(key=lambda x: len(x["path"].split("/")), reverse=True)
        conf_template = r"""location ~ "^%s.*$"  {
    auth_basic "Authorization";
    auth_basic_user_file %s;
%s
}
"""
        suffix_template = '{tmp_pre}if ( $uri ~ "\.({suffix})$" ) {{\n{tmp_pre}    return 404;\n{tmp_pre}}}'
        suffix_template2 = 'if ( $uri ~ "^{path}.*\.({suffix})$" ) {{\n    return 404;\n}}\n'
        tmp_conf_list = []
        for i in path_list:
            if "auth_file" in i and "suffix" in i:
                tmp_pre = "    "
                tmp_conf = conf_template % (
                    i["path"], i["auth_file"], suffix_template.format(tmp_pre=tmp_pre, suffix="|".join(i["suffix"]))
                )
                write_file(i["auth_file"], "{}:{}".format(i["username"], self.crypt_password(i["password"])))

            elif "auth_file" in i:
                tmp_conf = conf_template % (i["path"], i["auth_file"], "")
                write_file(i["auth_file"], "{}:{}".format(i["username"], self.crypt_password(i["password"])))
            else:
                tmp_conf = suffix_template2.format(path=i["path"], suffix="|".join(i["suffix"]))

            tmp_conf_list.append(tmp_conf)

        config_data = "\n".join(tmp_conf_list)
        config_file = "{}/nginx/access/{}/{}{}.conf".format(self._vhost_path, site_name, self.config_prefix, site_name)
        old_config = read_file(config_file)
        write_file(config_file, config_data)
        if webserver() == "nginx" and check_server_config() is not None:
            if isinstance(old_config, str):
                write_file(config_file, old_config)
            else:
                write_file(config_file, "")
            return "配置失败"


class _ApacheAccessConf(ServerConfig):
    
    def set_apache_access_include(self, site_name) -> Optional[str]:
        ap_file = "{}/apache/{}{}.conf".format(self._vhost_path, self.config_prefix, site_name)
        ap_conf = read_file(ap_file)
        if not ap_conf:
            return "配置文件丢失"
        access_dir = "{}/apache/access/{}".format(self._vhost_path, site_name)
        if not os.path.isdir(os.path.dirname(access_dir)):
            os.makedirs(os.path.dirname(access_dir))

        if not os.path.isdir(access_dir):
            os.makedirs(access_dir)

        pass_dir = "/www/server/pass/" + site_name
        if not os.path.isdir(os.path.dirname(pass_dir)):
            os.makedirs(os.path.dirname(pass_dir))

        if not os.path.isdir(pass_dir):
            os.makedirs(pass_dir)

        include_conf = (
            "\n    #引用访问限制规则，注释后配置的访问限制将无效\n"
            "    IncludeOptional /www/server/panel/vhost/apache/access/%s/*.conf\n"
        ) % site_name

        rep_include = re.compile(r"\s*IncludeOptional.*/access/.*/\*\.conf", re.M)
        if rep_include.search(ap_conf):
            return
        # 添加 引入
        rep_vhost_r = re.compile(r"</VirtualHost>")
        new_conf = rep_vhost_r.sub(include_conf + "</VirtualHost>", ap_conf)
        if not rep_include.search(new_conf):
            return "配置添加失败"

        write_file(ap_file, new_conf)
        if webserver() == "nginx" and check_server_config() is not None:
            write_file(ap_file, ap_conf)
            return "配置添加失败"

    def set_apache_access_by_conf(self, site_name: str, configs: Dict[str, List[Dict[str, str]]]) -> Optional[str]:
        """  configs 示例结构
        configs = {
            "auth_dir": [
                {
                    "name": "aaa",
                    "dir_path": "/",
                    "auth_file": "/www/server/pass/www.cache.com/aaa.pass",
                    "username":"aaaa",
                    "password":"aaaa",
                }
            ],
            "file_deny": [
                {
                    "name": "bbb",
                    "dir_path": "/",
                    "suffix": ["png", "jpg"]
                }
            ]
        }
        """
        site_path = DB("sites").where("name=?", (site_name, )).find()["path"]
        names = []
        old_configs = []
        access_dir = "{}/apache/access/{}".format(self._vhost_path, site_name)
        for i in os.listdir(access_dir):
            if not os.path.isfile(os.path.join(access_dir, i)):
                continue
            old_configs.append((i, read_file(os.path.join(access_dir, i))))

        for c in chain(configs.get("auth_dir", []), configs.get("file_deny", [])):
            if "suffix" in c:
                self._set_apache_file_deny(c, site_name)
                names.append("deny_{}.conf".format(c["name"]))
            else:
                self._set_apache_auth_dir(c, site_name, site_path)
                names.append("auth_{}.conf".format(c["name"]))

        for i in os.listdir(access_dir):
            if i not in names:
                os.remove(os.path.join(access_dir, i))

        if webserver() == "apache" and check_server_config() is not None:
            for i in os.listdir(access_dir):
                os.remove(os.path.join(access_dir, i))
            for n, data in old_configs:  # 还原之前的配置文件
                write_file(os.path.join(access_dir, n), data)
            return "配置保存失败"

    def _set_apache_file_deny(self, data: dict, site_name: str):
        conf = '''
#BEGIN_DENY_{n}
    <Directory ~ "{d}.*\.({s})$">
      Order allow,deny
      Deny from all
    </Directory>
#END_DENY_{n}
'''.format(n=data["name"], d=data["dir_path"], s="|".join(data["suffix"]))
        access_file = "{}/apache/access/{}/deny_{}.conf".format(self._vhost_path, site_name, data["name"])
        write_file(access_file, conf)

    def _set_apache_auth_dir(self, data: dict, site_path: str, site_name: str):
        conf = '''
<Directory "{site_path}{site_dir}">
    #AUTH_START
    AuthType basic
    AuthName "Authorization "
    AuthUserFile {auth_file}
    Require user {username}
    #AUTH_END
    SetOutputFilter DEFLATE
    Options FollowSymLinks
    AllowOverride All
    #Require all granted
        DirectoryIndex index.php index.html index.htm default.php default.html default.htm
</Directory>'''.format(site_path=site_path, site_dir=data["dir_path"], auth_file=data["auth_file"],
                       username=data["username"], site_name=site_name)
        write_file(data["auth_file"], "{}:{}".format(data["username"], self.crypt_password(data["password"])))
        access_file = "{}/apache/access/{}/auth_{}.conf".format(self._vhost_path, site_path, data["name"])
        write_file(access_file, conf)


class RealAccessRestriction(_ConfigObject, _ApacheAccessConf, _NginxAccessConf):
    _config_file_path = "/www/server/panel/data/site_access.json"

    def __init__(self, config_prefix: str):
        super(RealAccessRestriction, self).__init__()
        super(_ApacheAccessConf, self).__init__(config_prefix)

    # 把配置信息更新到服务配置文件中
    def _refresh_web_server_conf(self, site_name: str, site_access_conf: dict, web_server=None) -> Optional[str]:
        if web_server is None:
            web_server = webserver()
        error_msg = self.set_apache_access_by_conf(site_name, site_access_conf)
        if web_server == "apache" and error_msg is not None:
            return error_msg
        error_msg = self.set_nginx_access_by_conf(site_name, site_access_conf)
        if web_server == "nginx" and error_msg is not None:
            return error_msg

    # 添加include配置到对应站点的配置文件中
    def _set_web_server_conf_include(self, site_name, web_server=None) -> Optional[str]:
        if web_server is None:
            web_server = webserver()
        error_msg = self.set_apache_access_include(site_name)
        if web_server == "apache" and error_msg is not None:
            return error_msg
        error_msg = self.set_nginx_access_include(site_name)
        if web_server == "nginx" and error_msg is not None:
            return error_msg

    def check_auth_dir_args(self, get, is_modify=False) -> Union[str, dict]:
        values = {}
        try:
            values["site_name"] = get.site_name.strip()
            values["dir_path"] = get.dir_path.strip()
        except AttributeError:
            return "参数错误"

        if hasattr(get, "password"):
            password = get.password.strip()
            if len(password) < 3:
                return '密码不能少于3位'
            elif len(password) > 8:
                return '密码有效位数不能大于8位'
            if re.search(r'\s', password):
                return '密码不能存在空格'
            values['password'] = password
        else:
            return '请输入密码!'

        if hasattr(get, "username"):
            username = get.username.strip()
            if len(username) < 3:
                return '账号不能少于3位'
            if re.search(r'\s', username):
                return '账号不能存在空格'
            values['username'] = username
        else:
            return '请输入用户!'

        if hasattr(get, "name"):
            name = get.name.strip()
            if len(name) < 3:
                return '名称不能少于3位'
            if re.search(r'\s', name):
                return '名称不能存在空格'
            if not re.search(r'^\w+$', name):
                return '名称格式错误,仅支持数字字母下划线，请参考格式：aaa_bbb'
            values['name'] = name
        else:
            return '请输入名称!'
        if not is_modify:
            data = self.config.get(values["site_name"], {}).get("auth_dir", [])
            for i in data:
                if i["dir_path"] == values["dir_path"]:
                    return "此路径已存在"
                if i["name"] == values["name"]:
                    return "此名称已存在"

        values["auth_file"] = "/www/server/pass/{}/{}.pass".format(values["site_name"], values["name"])
        return values

    def create_auth_dir(self, get) -> Optional[str]:
        conf = self.check_auth_dir_args(get, is_modify=False)
        if isinstance(conf, str):
            return conf

        web_server = webserver()
        error_msg = self._set_web_server_conf_include(conf["site_name"], web_server)
        if error_msg:
            return error_msg

        if conf["site_name"] not in self.config:
            self.config[conf["site_name"]] = {"auth_dir": [], "file_deny": []}
        self.config[conf["site_name"]]["auth_dir"].append(conf)

        error_msg = self._refresh_web_server_conf(conf["site_name"], self.config[conf["site_name"]], web_server)
        if error_msg:
            return error_msg
        self.save_config()
        service_reload()

    def modify_auth_dir(self, get) -> Optional[str]:
        conf = self.check_auth_dir_args(get, is_modify=True)
        if isinstance(conf, str):
            return conf

        data = self.config.get(conf["site_name"], {}).get("auth_dir", [])
        target_idx = None
        for idx, i in enumerate(data):
            if i["name"] == conf["name"]:
                target_idx = idx
                break
        if target_idx is None:
            return "没有指定的配置信息"
        web_server = webserver()
        error_msg = self._set_web_server_conf_include(conf["site_name"], web_server)
        if error_msg:
            return error_msg
        if conf["site_name"] not in self.config:
            self.config[conf["site_name"]] = {"auth_dir": [], "file_deny": []}

        self.config[conf["site_name"]]["auth_dir"][target_idx] = conf

        error_msg = self._refresh_web_server_conf(conf["site_name"], self.config[conf["site_name"]], web_server)
        if error_msg:
            return error_msg
        self.save_config()
        service_reload()

    def remove_auth_dir(self, site_name: str, name: str) -> Optional[str]:
        if site_name not in self.config:
            return "没有该网站的配置"

        target = None
        for idx, i in enumerate(self.config[site_name].get("auth_dir", [])):
            if i.get("name", None) == name:
                target = idx

        if target is None:
            return "没有该路径的配置"

        del self.config[site_name]["auth_dir"][target]
        web_server = webserver()
        error_msg = self._refresh_web_server_conf(site_name, self.config[site_name], web_server)
        if error_msg:
            return error_msg
        self.save_config()
        service_reload()
        return

    def check_file_deny_args(self, get, is_modify=False) -> Union[str, dict]:
        values = {}
        try:
            values["site_name"] = get.site_name.strip()
            values["name"] = get.name.strip()
            values["dir_path"] = get.dir_path.strip()
            values["suffix"] = list(filter(lambda x: bool(x.strip()), json.loads(get.suffix.strip())))
        except (AttributeError, json.JSONDecodeError, TypeError, ValueError):
            return "参数错误"

        if len(values["name"]) < 3:
            return '规则名最少需要输入3个字符串！'
        if not values["suffix"]:
            return '文件扩展名不可为空！'
        if not values["dir_path"]:
            return '目录不可为空！'

        if not is_modify:
            data = self.config.get(values["site_name"], {}).get("file_deny", [])
            for i in data:
                if i["dir_path"] == values["dir_path"]:
                    return "此路径已存在"
                if i["name"] == values["name"]:
                    return "此名称已存在"
        return values

    def create_file_deny(self, get) -> Optional[str]:
        conf = self.check_file_deny_args(get, is_modify=False)
        if isinstance(conf, str):
            return conf
        web_server = webserver()
        error_msg = self._set_web_server_conf_include(conf["site_name"], web_server)
        if error_msg:
            return error_msg
        if conf["site_name"] not in self.config:
            self.config[conf["site_name"]] = {"auth_dir": [], "file_deny": []}

        self.config[conf["site_name"]]["file_deny"].append(conf)
        error_msg = self._refresh_web_server_conf(conf["site_name"], self.config[conf["site_name"]], web_server)
        if error_msg:
            return error_msg
        self.save_config()
        service_reload()

    def modify_file_deny(self, get) -> Optional[str]:
        conf = self.check_file_deny_args(get, is_modify=True)
        if isinstance(conf, str):
            return conf

        data = self.config.get(conf["site_name"], {}).get("file_deny", [])
        target_idx = None
        for idx, i in enumerate(data):
            if i["name"] == conf["name"]:
                target_idx = idx
                break
        if target_idx is None:
            return "没有指定的配置信息"
        web_server = webserver()
        error_msg = self._set_web_server_conf_include(conf["site_name"], web_server)
        if error_msg:
            return error_msg
        if conf["site_name"] not in self.config:
            self.config[conf["site_name"]] = {"auth_dir": [], "file_deny": []}

        self.config[conf["site_name"]]["file_deny"][target_idx] = conf

        error_msg = self._refresh_web_server_conf(conf["site_name"], self.config[conf["site_name"]], web_server)
        if error_msg:
            return error_msg
        self.save_config()
        service_reload()

    def remove_file_deny(self, site_name: str, name: str) -> Optional[str]:
        if site_name not in self.config:
            return "没有该网站的配置"

        target = None
        for idx, i in enumerate(self.config[site_name].get("file_deny", [])):
            if i.get("name", None) == name:
                target = idx

        if target is None:
            return "没有该路径的配置"

        del self.config[site_name]["file_deny"][target]
        web_server = webserver()
        error_msg = self._refresh_web_server_conf(site_name, self.config[site_name], web_server)
        if error_msg:
            return error_msg
        self.save_config()
        service_reload()
        return

    def site_access_restriction_info(self, site_name: str) -> dict:
        if site_name not in self.config:
            return {"auth_dir": [], "file_deny": []}
        else:
            return self.config[site_name]

    def remove_site_access_restriction_info(self, site_name):
        if site_name in self.config:
            del self.config["site_name"]
            self.save_config()
        ng_access_dir = "{}/nginx/access/{}".format(self._vhost_path, site_name)
        ap_access_dir = "{}/apache/access/{}".format(self._vhost_path, site_name)
        if os.path.isdir(ng_access_dir):
            shutil.rmtree(ng_access_dir)

        if os.path.isdir(ap_access_dir):
            shutil.rmtree(ap_access_dir)


class AccessRestriction:

    def __init__(self, config_prefix: str = ""):
        self.config_prefix: str = config_prefix
        self._ar = RealAccessRestriction(config_prefix)

    def create_auth_dir(self, get):
        res = self._ar.create_auth_dir(get)
        if isinstance(res, str):
            return json_response(status=False, msg=res)
        return json_response(status=True, msg="添加成功")

    def modify_auth_dir(self, get):
        res = self._ar.modify_auth_dir(get)
        if isinstance(res, str):
            return json_response(status=False, msg=res)
        return json_response(status=True, msg="修改成功")

    def remove_auth_dir(self, get):
        try:
            site_name = get.site_name.strip()
            name = get.name.strip()
        except AttributeError:
            return json_response(status=False, msg="请求参数错误")
        res = self._ar.remove_auth_dir(site_name, name)
        if isinstance(res, str):
            return json_response(status=False, msg=res)
        return json_response(status=True, msg="删除成功")

    def create_file_deny(self, get):
        res = self._ar.create_file_deny(get)
        if isinstance(res, str):
            return json_response(status=False, msg=res)
        return json_response(status=True, msg="添加成功")

    def modify_file_deny(self, get):
        res = self._ar.modify_file_deny(get)
        if isinstance(res, str):
            return json_response(status=False, msg=res)
        return json_response(status=True, msg="修改成功")

    def remove_file_deny(self, get):
        try:
            site_name = get.site_name.strip()
            name = get.name.strip()
        except AttributeError:
            return json_response(status=False, msg="请求参数错误")
        res = self._ar.remove_file_deny(site_name, name)
        if isinstance(res, str):
            return json_response(status=False, msg=res)
        return json_response(status=True, msg="删除成功")

    def site_access_restriction_info(self, get):
        try:
            site_name = get.site_name.strip()
        except AttributeError:
            return json_response(status=False, msg="请求参数错误")
        data = self._ar.site_access_restriction_info(site_name)
        return json_response(status=True, data=data)
