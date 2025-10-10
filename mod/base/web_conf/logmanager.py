import os
import re
import json
import sys
from typing import Tuple, Optional, Union, List
from .util import webserver, check_server_config, write_file, read_file, DB, service_reload, get_log_path, pre_re_key
from mod.base import json_response


class _BaseLogFormat:
    panel_path = "/www/server/panel"

    def __init__(self):
        self._config_file = ""
        self._config: Optional[dict] = None
        self._format_dict = None
        self._log_format_dir = ''

    @property
    def config(self) -> dict:
        if self._config is None:
            try:
                self._config = json.loads(read_file(self._config_file))
            except (json.JSONDecodeError, TypeError, ValueError):
                self._config = {}
        return self._config

    def save_config(self):
        if self._config is not None:
            write_file(self._config_file, json.dumps(self._config))

    @property
    def log_format(self) -> dict:
        raise NotImplementedError()

    def check_config(self, name: str, keys: List[str], space_character=None) -> Optional[str]:
        if space_character and len(space_character) > 4:
            return "间隔符过长，请输入小于4位的间隔符"
        rep_name = re.compile(r"^\w+$")
        if rep_name.match(name) is None:
            return "名称只能包含数字、字母和下划线"
        if name in ("combined", "main"):
            return "请勿使用默认名称"
        error_key = []
        for k in keys:
            if k not in self.log_format:
                error_key.append(k)
        if error_key:
            return "无法识别以下日志关键字:【{}】".format(",".join(error_key))

    # 添加日志格式
    def add_log_format(self, name: str, keys: List[str], space_character=" ") -> Optional[str]:
        error_msg = self.check_config(name, keys, space_character)
        if error_msg:
            return error_msg
        if name in self.config:
            return "该名称的日志格式已存在"
        error_msg = self._set_to_config(name, keys, space_character, is_modify=False)
        if error_msg:
            return error_msg

        self.config[name] = {"keys": keys, "space_character": space_character, "sites": []}
        self.save_config()
        service_reload()
        return None

    # 修改日志格式
    def modify_log_format(self, name: str, keys: List[str], space_character=None) -> Optional[str]:
        error_msg = self.check_config(name, keys, space_character)
        if error_msg:
            return error_msg
        if name not in self.config:
            return "该名称的日志格式不存在"

        self.config[name]["keys"] = keys
        if space_character:
            self.config[name]["space_character"] = space_character
        else:
            space_character = self.config[name]["space_character"]

        error_msg = self._set_to_config(name, keys, space_character, is_modify=True)
        if error_msg:
            return error_msg
        self.save_config()
        service_reload()
        return None

    # 删除日志格式
    def remove_log_format(self, name: str) -> Optional[str]:
        if name not in self.config:
            return "该名称的日志格式不存在"
        if len(self.config[name].get("sites", [])) > 1:
            return "该日志格式在【{}】网站中正在使用，请先移除".format(",".join(self.config[name]["sites"]))
        self._remove_form_config(name)

        del self.config[name]
        self.save_config()
        service_reload()
        return None

    def _set_to_config(self, name: str, keys: List[str], space_character, is_modify=False) -> Optional[str]:
        raise NotImplementedError

    def _remove_form_config(self, name) -> None:
        conf_file = self._log_format_dir + "/{}_format.conf".format(name)
        if os.path.isfile(conf_file):
            os.remove(conf_file)

    # 在配置文件中设置日志格式， log_format_name传入空字符串时，设置会默认
    def set_site_log_format_in_config(self, site_name, log_format_name, conf_prefix, mutil=False) -> Optional[str]:
        """
        mutil 为True时，不会自动重载配置
        """
        raise NotImplementedError()

    # 设置日志格式
    def set_site_log_format(self, site_name, log_format_name, conf_prefix, mutil=False) -> Optional[str]:
        if log_format_name not in self.config and log_format_name != "":
            return "该名称的日志格式不存在"
        error_msg = self.set_site_log_format_in_config(site_name, log_format_name, conf_prefix, mutil=mutil)
        if error_msg is not None:
            return error_msg
        if "sites" not in self.config[log_format_name]:
            self.config[log_format_name]["sites"] = []
        for name, sub_conf in self.config.items():
            if name == log_format_name:
                sub_conf["sites"].append(site_name)  # 记录到配置文件中

            if site_name in sub_conf.get("sites", []):
                sub_conf["sites"].remove(site_name)   # 如果之前使用了其他的配置，则移除其他配置中的这个站点的关联

        self.save_config()


class _NgLog(_BaseLogFormat):

    @property
    def log_format(self) -> dict:
        if self._format_dict is None:
            self._format_dict = {
                "server_addr": {
                    "name": "服务器地址",
                    "key": "$server_addr",
                },
                "server_port": {
                    "name": "服务器端口",
                    "key": "$server_port",
                },
                "host": {
                    "name": "域名",
                    "key": "$http_host",
                },
                "remote_addr": {
                    "name": "客户端地址",
                    "key": "$server_addr",
                },
                "remote_port": {
                    "name": "客户端端口",
                    "key": "$server_addr",
                },
                "protocol": {
                    "name": "服务器协议",
                    "key": "$server_protocol",
                },
                "req_length": {
                    "name": "请求长度",
                    "key": "$request_length",
                },
                "method": {
                    "name": "请求方法",
                    "key": "$request_method",
                },
                "uri": {
                    "name": "请求uri",
                    "key": "$request_uri",
                },
                "status": {
                    "name": "状态码",
                    "key": "$status",
                },
                "sent_bytes": {
                    "name": "发送字节数",
                    "key": "$body_bytes_sent",
                },
                "referer": {
                    "name": "来源地址",
                    "key": "$http_referer",
                },
                "user_agent": {
                    "name": "用户代理(User-Agent)",
                    "key": "$http_user_agent",
                },
                "take_time": {
                    "name": "请求用时",
                    "key": "$request_time",
                },
            }
        return self._format_dict

    def __init__(self):
        super().__init__()
        self._config_file = "{}/data/ng_log_format.json".format(self.panel_path)
        self._log_format_dir = "{}/vhost/nginx/log_format".format(self.panel_path)

    def _set_log_format_include(self) -> Optional[str]:
        config_file = "/www/server/nginx/conf/nginx.conf"
        config_data = read_file(config_file)
        if not config_data:
            return "配置文件丢失无法操作"
        if not os.path.isdir(self._log_format_dir):
            os.makedirs(self._log_format_dir)
        rep_include = re.compile(r"include\s+/www/server/panel/vhost/nginx/log_format/\*\.conf\s*;")
        if rep_include.search(config_data):
            return

        rep_http = re.compile(r"\s*http\s*\{[^\n]*\n")
        res = rep_http.search(config_data)
        if not res:
            return "主配置文件中缺少http配置项，无法添加"
        include_str = "include {}/*.conf;\n".format(self._log_format_dir)
        new_conf = config_data[:res.end()] + include_str + config_data[res.end():]
        write_file(config_file, new_conf)

    def _set_to_config(self, name: str, keys: List[str], space_character, is_modify=False) -> Optional[str]:
        error_msg = self._set_log_format_include()
        if error_msg:
            return error_msg
        conf_file = self._log_format_dir + "/{}_format.conf".format(name)
        write_file(conf_file, (
            "log_format {} '{}';".format(name, space_character.join(map(lambda x: self.log_format[x]["key"], keys)))
        ))

    def set_site_log_format_in_config(self, site_name, log_format_name, conf_prefix, mutil=False) -> Optional[str]:
        """
        mutil 为True时，不会自动重载配置
        """
        config_file = "{}/vhost/nginx/{}{}.conf".format(self.panel_path, conf_prefix, site_name)
        config_data = read_file(config_file)
        if not config_data:
            return "配置文件丢失无法操作"

        start_idx, end_idx = self.get_first_server_log_idx(config_data)
        if start_idx:
            rep_access_log = re.compile(r"\s*access_log\s+(?P<path>[^;\s]*)(\s+(?P<name>\w+))?;")
            res = rep_access_log.search(config_data[start_idx: end_idx])
            if res.group("name") == log_format_name:
                return
            new_access_log = "\n    access_log {} {};".format(res.group("path"), log_format_name)
            new_conf = config_data[:start_idx] + new_access_log + config_data[end_idx:]
        else:
            last_server_idx = config_data.rfind("}")  # server 范围内最后一个}的位置
            if last_server_idx == -1:
                return "配置文件格式错误无法操作"
            log_path = "{}/{}.log".format(get_log_path(), site_name)
            new_access_log = "\n    access_log {} {};\n".format(log_path, log_format_name)
            new_conf = config_data[:last_server_idx] + new_access_log + config_data[last_server_idx:]
        write_file(config_file, new_conf)
        if webserver() == "nginx" and check_server_config() is not None:
            write_file(config_file, config_data)
            return "配置修改失败"
        if webserver() == "nginx" and not mutil:
            service_reload()

    # 获取配置文件中server等级的第一个access_log的位置
    @staticmethod
    def get_first_server_log_idx(config_data) -> Tuple[Optional[int], Optional[int]]:
        rep_server = re.compile(r"\s*server\s*\{")
        res = rep_server.search(config_data)
        if res is None:
            return None, None
        rep_log = re.compile(r"\s*access_log\s+(?P<path>[^;\s]*)(\s+(?P<name>\w+))?;", re.M)
        s_idx = res.end()
        l_n = 1
        length = len(config_data)
        while l_n > 0:
            next_l = config_data[s_idx:].find("{")
            next_r = config_data[s_idx:].find("}")
            if next_l == -1 and next_r == -1:  # 都没有了跳过
                return None, None
            if next_r == -1 and next_l != -1:  # 还剩 { 但是没有 } ,跳过
                return None, None
            if next_l == -1:
                next_l = length
            if next_l < next_r:
                if l_n == 1:
                    res = rep_log.search(config_data[s_idx: s_idx + next_l])
                    if res:
                        return s_idx + res.start(), s_idx + res.end()
                l_n += 1
            else:
                l_n -= 1
                if l_n == 0:
                    res = rep_log.search(config_data[s_idx: s_idx + next_l])
                    if res:
                        return s_idx + res.start(), s_idx + res.end()
            s_idx += min(next_l, next_r) + 1
        return None, None

    # 设置站点的日志路径
    def set_site_log_path(self, site_name, site_log_path, conf_prefix, mutil=False) -> Optional[str]:
        if not os.path.isdir(site_log_path):
            return "不是一个存在的文件夹路径"

        if site_log_path[-1] == "/":
            site_log_path = site_log_path[:-1]

        # nginx
        nginx_config_path = '/www/server/panel/vhost/nginx/{}{}.conf'.format(conf_prefix, site_name)
        nginx_config = read_file(nginx_config_path)
        if not nginx_config:
            return "网站配置文件丢失，无法配置"

        # nginx
        old_log_file = self.nginx_get_log_file_path(nginx_config, site_name, is_error_log=False)
        old_error_log_file = self.nginx_get_log_file_path(nginx_config, site_name, is_error_log=True)

        if old_log_file and old_error_log_file:
            new_nginx_conf = nginx_config
            log_file_rep = re.compile(r"access_log +" + pre_re_key(old_log_file))
            error_log_file_rep = re.compile(r"error_log +" + pre_re_key(old_error_log_file))
            if log_file_rep.search(nginx_config):
                new_nginx_conf = log_file_rep.sub("access_log {}/{}.log".format(site_log_path, site_name),
                                                  new_nginx_conf, 1)

            if error_log_file_rep.search(nginx_config):
                new_nginx_conf = error_log_file_rep.sub("error_log {}/{}.error.log".format(site_log_path, site_name),
                                                        new_nginx_conf, 1)

            write_file(nginx_config_path, new_nginx_conf)
            if webserver() == "nginx" and check_server_config() is not None:
                write_file(nginx_config_path, nginx_config)
                return "配置修改失败"
            if webserver() == "nginx" and not mutil:
                service_reload()

        else:
            return "未找到日志配置，无法操作"

    @staticmethod
    def nginx_get_log_file_path(nginx_config: str, site_name: str, is_error_log: bool = False):
        log_file = None
        if is_error_log:
            re_data = re.findall(r"error_log +(/(\S+/?)+) ?(.*?);", nginx_config)
        else:
            re_data = re.findall(r"access_log +(/(\S+/?)+) ?(.*?);", nginx_config)
        if re_data is None:
            log_file = None
        else:
            for i in re_data:
                file_path = i[0].strip(";")
                if file_path != "/dev/null" and not file_path.endswith("purge_cache.log"):
                    if os.path.isdir(os.path.dirname(file_path)):
                        log_file = file_path
                        break

        logsPath = '/www/wwwlogs/'
        if log_file is None:
            if is_error_log:
                log_file = logsPath + site_name + '.log'
            else:
                log_file = logsPath + site_name + '.error.log'
            if not os.path.isfile(log_file):
                log_file = None

        return log_file

    def get_site_log_path(self, site_name, conf_prefix) -> Union[str, dict]:
        config_path = '/www/server/panel/vhost/nginx/{}{}.conf'.format(conf_prefix, site_name)
        config = read_file(config_path)
        if not config:
            return "站点配置文件丢失"
        log_file = self.nginx_get_log_file_path(config, site_name, is_error_log=False)
        error_log_file = self.nginx_get_log_file_path(config, site_name, is_error_log=False)
        if not (error_log_file and log_file):
            return "获取失败"
        return {
            "log_file": log_file,
            "error_log_file": error_log_file,
        }

    def close_access_log(self, site_name, conf_prefix) -> Optional[str]:
        nginx_config_path = '/www/server/panel/vhost/nginx/{}{}.conf'.format(conf_prefix, site_name)
        nginx_config = read_file(nginx_config_path)
        if not nginx_config:
            return "网站配置文件丢失，无法配置"

        start_idx, end_idx = self.get_first_server_log_idx(nginx_config)
        if not start_idx:
            return None
        new_conf = nginx_config

        while start_idx is not None:
            new_conf = new_conf[:start_idx] + '# ' + new_conf[start_idx:]
            start_idx, end_idx = self.get_first_server_log_idx(new_conf)

        write_file(nginx_config_path, new_conf)
        if webserver() == "nginx" and check_server_config() is not None:
            write_file(nginx_config_path, nginx_config)
            return "配置修改失败"

        return None

    # 未完成
    def open_access_log(self, site_name, conf_prefix) -> Optional[str]:
        nginx_config_path = '/www/server/panel/vhost/nginx/{}{}.conf'.format(conf_prefix, site_name)
        nginx_config = read_file(nginx_config_path)
        if not nginx_config:
            return "网站配置文件丢失，无法配置"

        new_conf = nginx_config.replace("#")

        write_file(nginx_config_path, new_conf)
        if webserver() == "nginx" and check_server_config() is not None:
            write_file(nginx_config_path, nginx_config)
            return "配置修改失败"

        return None

    def access_log_is_open(self, site_name, conf_prefix) -> bool:
        nginx_config_path = '/www/server/panel/vhost/nginx/{}{}.conf'.format(conf_prefix, site_name)
        nginx_config = read_file(nginx_config_path)
        if not nginx_config:
            return False

        start_idx, end_idx = self.get_first_server_log_idx(nginx_config)
        return start_idx is not None


class _ApLog(_BaseLogFormat):

    def set_site_log_format_in_config(self, site_name, log_format_name, conf_prefix, mutil=False) -> Optional[str]:
        if log_format_name == "":
            log_format_name = "combined"
        config_file = "{}/vhost/apache/{}{}.conf".format(self.panel_path, conf_prefix, site_name)
        config_data = read_file(config_file)
        if not config_data:
            return "配置文件丢失无法操作"

        custom_log_rep = re.compile(r'''\s*CustomLog\s+['"](?P<path>.*)['"](\s+(?P<name>.*))?''', re.M)
        new_custom_log = '\n    CustomLog "{}" %s\n' % log_format_name
        new_conf_list = []
        idx = 0
        for tmp_res in custom_log_rep.finditer(config_data):
            new_conf_list.append(config_data[idx:tmp_res.start()])
            new_conf_list.append(new_custom_log.format(tmp_res.group("path")))
            idx = tmp_res.end()
        new_conf_list.append(config_data[idx:])
        new_conf = "".join(new_conf_list)

        write_file(config_file, new_conf)
        if webserver() == "apache" and check_server_config() is not None:
            write_file(config_file, config_data)
            return "配置修改失败"
        if webserver() == "apache" and not mutil:
            service_reload()

    # 设置站点的日志路径
    def set_site_log_path(self, site_name, site_log_path, conf_prefix, mutil=False) -> Optional[str]:
        if not os.path.isdir(site_log_path):
            return "不是一个存在的文件夹路径"

        if site_log_path[-1] == "/":
            site_log_path = site_log_path[:-1]

        # apache
        apache_config_path = '/www/server/panel/vhost/apache/{}{}.conf'.format(conf_prefix, site_name)
        apache_config = read_file(apache_config_path)
        if not apache_config:
            return "网站配置文件丢失，无法配置"

        # apache
        old_log_file = self.apache_get_log_file_path(apache_config, site_name, is_error_log=False)
        old_error_log_file = self.apache_get_log_file_path(apache_config, site_name, is_error_log=True)

        if old_log_file and old_error_log_file:
            new_apache_conf = apache_config
            log_file_rep = re.compile(r'''CustomLog +['"]?''' + pre_re_key(old_log_file) + '''['"]?''')
            error_log_file_rep = re.compile(r'''ErrorLog +['"]?''' + pre_re_key(old_error_log_file) + '''['"]?''')
            if log_file_rep.search(apache_config):
                new_apache_conf = log_file_rep.sub('CustomLog "{}/{}-access_log"'.format(site_log_path, site_name),
                                                   new_apache_conf)

            if error_log_file_rep.search(apache_config):
                new_apache_conf = error_log_file_rep.sub('ErrorLog "{}/{}.-error_log"'.format(site_log_path, site_name),
                                                         new_apache_conf)
            write_file(apache_config_path, new_apache_conf)
            print(new_apache_conf)
            if webserver() == "apache" and check_server_config() is not None:
                write_file(apache_config_path, apache_config)
                return "配置修改失败"
            if webserver() == "apache" and not mutil:
                service_reload()
        else:
            return "未找到日志配置，无法操作"

    @staticmethod
    def apache_get_log_file_path(apache_config: str, site_name: str, is_error_log: bool = False):
        log_file = None
        if is_error_log:
            re_data = re.findall(r'''ErrorLog +['"]?(/(\S+/?)+)['"]? ?(.*?)\n''', apache_config)
        else:
            re_data = re.findall(r'''CustomLog +['"]?(/(\S+/?)+)['"]? ?(.*?)\n''', apache_config)
        if re_data is None:
            log_file = None
        else:
            for i in re_data:
                file_path = i[0].strip('"').strip("'")
                if file_path != "/dev/null":
                    if os.path.isdir(os.path.dirname(file_path)):
                        log_file = file_path
                        break

        logsPath = '/www/wwwlogs/'
        if log_file is None:
            if is_error_log:
                log_file = logsPath + site_name + '-access_log'
            else:
                log_file = logsPath + site_name + '-error_log'
            if not os.path.isfile(log_file):
                log_file = None

        return log_file

    @staticmethod
    def close_access_log(site_name, conf_prefix) -> Optional[str]:
        apache_config_path = '/www/server/panel/vhost/apache/{}{}.conf'.format(conf_prefix, site_name)
        apache_config = read_file(apache_config_path)
        if not apache_config:
            return "网站配置文件丢失，无法配置"
        custom_log_rep = re.compile(r'''CustomLog +['"]?(/(\S+/?)+)['"]?(\s*.*)?''', re.M)
        new_conf_list = []
        idx = 0
        for tmp_res in custom_log_rep.finditer(apache_config):
            new_conf_list.append(apache_config[idx:tmp_res.start()])
            new_conf_list.append("# " + tmp_res.group())
            idx = tmp_res.end()
        new_conf_list.append(apache_config[idx:])
        new_conf = "".join(new_conf_list)
        write_file(apache_config_path, new_conf)
        if webserver() == "apache" and check_server_config() is not None:
            write_file(apache_config_path, apache_config)
            return "配置修改失败"
        return None

    @staticmethod
    def open_access_log(site_name, conf_prefix) -> Optional[str]:
        apache_config_path = '/www/server/panel/vhost/apache/{}{}.conf'.format(conf_prefix, site_name)
        apache_config = read_file(apache_config_path)
        if not apache_config:
            return "网站配置文件丢失，无法配置"
        new_conf = apache_config.replace("#CustomLog", "CustomLog")
        write_file(apache_config_path, new_conf)
        if webserver() == "apache" and check_server_config() is not None:
            write_file(apache_config_path, apache_config)
            return "配置修改失败"
        return None

    @staticmethod
    def access_log_is_open(site_name, conf_prefix) -> bool:
        apache_config_path = '/www/server/panel/vhost/apache/{}{}.conf'.format(conf_prefix, site_name)
        apache_config = read_file(apache_config_path)
        if not apache_config:
            return False
        if apache_config.find("#CustomLog") != -1:
            return False
        return True


    def get_site_log_path(self, site_name, conf_prefix) -> Union[str, dict]:
        config_path = '/www/server/panel/vhost/apache/{}{}.conf'.format(conf_prefix, site_name)
        config = read_file(config_path)
        if not config:
            return "站点配置文件丢失"
        log_file = self.apache_get_log_file_path(config, site_name, is_error_log=False)
        error_log_file = self.apache_get_log_file_path(config, site_name, is_error_log=False)
        if not (error_log_file and log_file):
            return "获取失败"
        return {
            "log_file": log_file,
            "error_log_file": error_log_file,
        }

    @property
    def log_format(self) -> dict:
        if self._format_dict is None:
            self._format_dict = {
                "server_addr": {
                    "name": "服务器地址",
                    "key": "%A",
                },
                "server_port": {
                    "name": "服务器端口",
                    "key": "%p",
                },
                "host": {
                    "name": "域名",
                    "key": "%V",
                },
                "remote_addr": {
                    "name": "客户端地址",
                    "key": "%{c}a",
                },
                "remote_port": {
                    "name": "客户端端口",
                    "key": "%{remote}p",
                },
                "protocol": {
                    "name": "服务器协议",
                    "key": "%H",
                },
                "method": {
                    "name": "请求方法",
                    "key": "%m",
                },
                "uri": {
                    "name": "请求uri",
                    "key": r"\"%U\"",
                },
                "status": {
                    "name": "状态码",
                    "key": "%>s",
                },
                "sent_bytes": {
                    "name": "发送字节数",
                    "key": "%B",
                },
                "referer": {
                    "name": "来源地址",
                    "key": r"\"%{Referer}i\"",
                },
                "user_agent": {
                    "name": "用户代理(User-Agent)",
                    "key": r"\"%{User-Agent}i\"",
                },
                "take_time": {
                    "name": "请求用时",
                    "key": "%{ms}T",
                },
            }
        return self._format_dict

    def __init__(self):
        super().__init__()
        self._config_file = "{}/data/ap_log_format.json".format(self.panel_path)
        self._log_format_dir = "{}/vhost/apache/log_format".format(self.panel_path)

    def _set_log_format_include(self) -> Optional[str]:
        config_file = "/www/server/apache/conf/httpd.conf"
        config_data = read_file(config_file)
        if not config_data:
            return "配置文件丢失无法操作"
        if not os.path.isdir(self._log_format_dir):
            os.makedirs(self._log_format_dir)
        rep_include = re.compile(r"IncludeOptional\s+/www/server/panel/vhost/apache/log_format/\*\.conf")
        if rep_include.search(config_data):
            return
        new_conf = config_data + """
<IfModule log_config_module>
    IncludeOptional /www/server/panel/vhost/apache/log_format/*.conf
</IfModule>
"""
        write_file(config_file, new_conf)

    def _set_to_config(self, name: str, keys: List[str], space_character, is_modify=False) -> Optional[str]:
        error_msg = self._set_log_format_include()
        if error_msg:
            return error_msg
        conf_file = self._log_format_dir + "/{}_format.conf".format(name)
        write_file(conf_file, (
            'LogFormat "{}" {}'.format(space_character.join(map(lambda x: self.log_format[x]["key"], keys)), name)
        ))


class RealLogMgr:

    def __init__(self, conf_prefix: str = ""):
        self.conf_prefix = conf_prefix
        if webserver() == "nginx":
            self._log_format_tool = _NgLog()
        else:
            self._log_format_tool = _ApLog()

    @staticmethod
    def remove_site_log_format_info(site_name: str):
        for logtool in (_NgLog(), _ApLog()):
            for _, conf in logtool.config.items():
                if site_name in conf.get("sites", []):
                    conf["sites"].remove(site_name)
            logtool.save_config()

    def log_format_data(self, site_name: str):
        log_format_data = None
        for name, data in self._log_format_tool.config.items():
            if site_name in data.get("sites", []):
                log_format_data = data
                log_format_data.update(name=name)
        return {
            "log_format": log_format_data,
            "rule": self._log_format_tool.log_format,
            "all_log_format":  self._log_format_tool.config
        }

    def add_log_format(self, name: str, keys: List[str], space_character=" ") -> Optional[str]:
        return self._log_format_tool.add_log_format(name, keys, space_character)

    def modify_log_format(self, name: str, keys: List[str], space_character=None) -> Optional[str]:
        return self._log_format_tool.modify_log_format(name, keys, space_character)

    def remove_log_format(self, name: str) -> Optional[str]:
        return self._log_format_tool.remove_log_format(name)

    # log_format_name 为空字符串时表示恢复成默认的日志格式
    def set_site_log_format(self, site_name, log_format_name, mutil=False) -> Optional[str]:
        return self._log_format_tool.set_site_log_format(site_name, log_format_name, self.conf_prefix, mutil)

    def set_site_log_path(self, site_name, site_log_path, mutil=False) -> Optional[str]:
        return self._log_format_tool.set_site_log_path(site_name, site_log_path, self.conf_prefix, mutil)

    def get_site_log_path(self, site_name) -> Union[str, dict]:
        return self._log_format_tool.get_site_log_path(site_name, self.conf_prefix)

    @staticmethod
    def site_crontab_log(site_name: str, hour: int, minute: int, save: int) -> bool:
        if DB("crontab").where("sName =? and sType = ?", ("ALL", "logs")).find():
            return True

        if "/www/server/panel/class" not in sys.path:
            sys.path.insert(0, "/www/server/panel/class")
        import crontab
        crontabs = crontab.crontab()
        args = {
            "name": "切割日志[{}]".format(site_name),
            "type": 'day',
            "where1": '',
            "hour": hour,
            "minute": minute,
            "sName": site_name,
            "sType": 'logs',
            "notice": '',
            "notice_channel": '',
            "save": save,
            "save_local": '1',
            "backupTo": '',
            "sBody": '',
            "urladdress": ''
        }
        res = crontabs.AddCrontab(args)
        if res and "id" in res.keys():
            return True
        return False


class LogMgr:

    def __init__(self, conf_prefix: str = ""):
        self.conf_prefix = conf_prefix
        self._real_log_mgr = RealLogMgr(self.conf_prefix)

    def log_format_data(self, get):
        try:
            site_name = get.site_name.strip()
        except (AttributeError, json.JSONDecodeError, TypeError, ValueError):
            return json_response(status=False, msg="参数类型错误")
        data = self._real_log_mgr.log_format_data(site_name)
        return json_response(status=True, data=data)

    def add_log_format(self, get):
        try:
            space_character = " "
            format_name = get.format_name.strip()
            keys = json.loads(get.keys.strip())
            if "space_character" in get:
                space_character = get.space_character
        except (AttributeError, json.JSONDecodeError, TypeError, ValueError):
            return json_response(status=False, msg="参数类型错误")

        msg = self._real_log_mgr.add_log_format(format_name, keys, space_character)
        if isinstance(msg, str):
            return json_response(status=False, msg=msg)
        return json_response(status=True, msg="添加成功")

    def modify_log_format(self, get):
        try:
            space_character = None
            format_name = get.format_name.strip()
            keys = json.loads(get.keys.strip())
            if "space_character" in get:
                space_character = get.space_character
        except (AttributeError, json.JSONDecodeError, TypeError, ValueError):
            return json_response(status=False, msg="参数类型错误")

        msg = self._real_log_mgr.modify_log_format(format_name, keys, space_character)
        if isinstance(msg, str):
            return json_response(status=False, msg=msg)
        return json_response(status=True, msg="修改成功")

    def remove_log_format(self, get):
        try:
            format_name = get.format_name.strip()
        except (AttributeError, json.JSONDecodeError, TypeError, ValueError):
            return json_response(status=False, msg="参数类型错误")

        msg = self._real_log_mgr.remove_log_format(format_name)
        if isinstance(msg, str):
            return json_response(status=False, msg=msg)
        return json_response(status=True, msg="删除成功")

    def set_site_log_format(self, get):
        try:
            format_name = get.format_name.strip()
            site_name = get.site_name.strip()
        except (AttributeError, json.JSONDecodeError, TypeError, ValueError):
            return json_response(status=False, msg="参数类型错误")

        msg = self._real_log_mgr.set_site_log_format(site_name, log_format_name=format_name)
        if isinstance(msg, str):
            return json_response(status=False, msg=msg)
        return json_response(status=True, msg="添加成功")

    def set_site_log_path(self, get):
        try:
            log_path = get.log_path.strip()
            site_name = get.site_name.strip()
        except (AttributeError, json.JSONDecodeError, TypeError, ValueError):
            return json_response(status=False, msg="参数类型错误")

        msg = self._real_log_mgr.set_site_log_path(site_name, site_log_path=log_path)
        if isinstance(msg, str):
            return json_response(status=False, msg=msg)
        return json_response(status=True, msg="修改路径成功")

    def get_site_log_path(self, get):
        try:
            site_name = get.site_name.strip()
        except (AttributeError, json.JSONDecodeError, TypeError, ValueError):
            return json_response(status=False, msg="参数类型错误")

        msg = self._real_log_mgr.get_site_log_path(site_name)
        if isinstance(msg, str):
            return json_response(status=False, msg=msg)
        return json_response(status=True, data=msg)

    def site_crontab_log(self, get):
        try:
            site_name = get.site_name.strip()
            hour = int(get.hour.strip())
            minute = int(get.minute.strip())
            save = int(get.save.strip())
        except (AttributeError, json.JSONDecodeError, TypeError, ValueError):
            return json_response(status=False, msg="参数类型错误")

        msg = self._real_log_mgr.site_crontab_log(site_name, hour=hour, minute=minute, save=save)
        if isinstance(msg, str):
            return json_response(status=False, msg=msg)
        return json_response(status=True, data=msg)
