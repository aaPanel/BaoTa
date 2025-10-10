# coding: utf-8
#  + -------------------------------------------------------------------
# | 宝塔Linux面板
#  + -------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http:#bt.cn) All rights reserved.
#  + -------------------------------------------------------------------
# | Author: baozi <baozi@bt.cn>
#  + -------------------------------------------------------------------
import json
import os
import re
import time
from ipaddress import IPv4Address, AddressValueError
from typing import Tuple, Optional, Dict, Any, Union, List, Callable
from itertools import groupby

import public


class BaseLogSource:

    @classmethod
    def new(cls, data) -> Union["BaseLogSource", str]:
        raise NotImplementedError("未实现")

    def title(self) -> str:
        raise NotImplementedError("未实现")

    def to_conf(self) -> dict:
        raise NotImplementedError("未实现")

    def __eq__(self, other):
        raise NotImplementedError("未实现")


class BaseLogServer(object):

    @property
    def config(self):
        raise NotImplementedError("未实现")

    @config.setter
    def config(self, value):
        raise NotImplementedError("未实现")

    def collect_log(self, source: BaseLogSource) -> Tuple[bool, str]:
        raise NotImplementedError("未实现")

    def un_collect_log(self, source: BaseLogSource) -> Tuple[bool, str]:
        raise NotImplementedError("未实现")

    def begin_set(self, source_class) -> Tuple[bool, str]:
        raise NotImplementedError("未实现")

    def end_set(self, source_class) -> Tuple[bool, str]:
        raise NotImplementedError("未实现")

    def check_exist(self, mgr: "LogServerManager") -> bool:
        raise NotImplementedError("未实现")

    @classmethod
    def new(cls, data: Any) -> "BaseLogServer":
        raise NotImplementedError("未实现")


class SiteLogSource(BaseLogSource):
    _VHOST_PATH = "{}/vhost".format(public.get_panel_path())

    def __init__(self, site_name):
        self.site_name = site_name
        site_info = public.M("sites").where("name=?", (site_name,)).find()
        if not isinstance(site_info, dict):
            raise ValueError("站点:{}数据查询错误".format(site_name))

        self.project_type: Optional[str] = site_info["project_type"].lower()
        self.site_path = site_info["path"]
        self.webserver_type = public.get_webserver()

    def title(self) -> str:
        return self.site_name

    def to_conf(self) -> dict:
        return {
            "source_type": "site",
            "site_name": self.site_name
        }

    def __eq__(self, other):
        if isinstance(other, SiteLogSource):
            if other.site_name == self.site_name:
                return True
        return False

    @classmethod
    def new(cls, data: Union[dict, str]) -> Union["BaseLogSource", str]:
        if isinstance(data, str):
            site_name = data
        elif isinstance(data, dict):
            site_name = data.get("site_name", "")
        else:
            site_name = ""
        if site_name == "":
            return "网站名称错误"
        site_info = public.M("sites").where("name=?", (site_name,)).find()
        if not isinstance(site_info, dict):
            return "站点:{}数据查询错误".format(site_name)
        return cls(site_name)

    def nginx_config(self) -> Optional[Dict[str, str]]:
        prefix = "" if self.project_type == "php" else (self.project_type + "_")
        nginx_conf_file = os.path.join(self._VHOST_PATH, "nginx", "{}{}.conf".format(prefix, self.site_name))
        if not os.path.isfile(nginx_conf_file):
            return None
        config_data = public.readFile(nginx_conf_file)
        if not isinstance(config_data, str):
            return None
        return {
            "path": nginx_conf_file,
            "data": config_data,
        }

    def apache_config(self) -> Optional[Dict[str, str]]:
        prefix = "" if self.project_type == "php" else (self.project_type + "_")
        apache_conf_file = os.path.join(self._VHOST_PATH, "apache", "{}{}.conf".format(prefix, self.site_name))
        if not os.path.isfile(apache_conf_file):
            return None
        config_data = public.readFile(apache_conf_file)
        if not isinstance(config_data, str):
            return None
        return {
            "path": apache_conf_file,
            "data": config_data,
        }

    def web_server_conf(self) -> Optional[Dict[str, str]]:
        if self.webserver_type == "nginx":
            return self.nginx_config()
        else:
            return self.apache_config()

    def nginx_log_files(self) -> Optional[Dict[str, str]]:
        pass

    def apache_log_files(self) -> Optional[Dict[str, str]]:
        pass


class SysLogSource(BaseLogSource):

    def __init__(self):
        self._rsyslog_conf_file = "/etc/rsyslog.conf"

    def rsyslog_conf(self) -> Optional[Dict[str, str]]:
        if os.path.isfile(self._rsyslog_conf_file):
            conf_data = public.readFile(self._rsyslog_conf_file)
            if isinstance(conf_data, str):
                return {
                    "path": self._rsyslog_conf_file,
                    "data": conf_data,
                }
        return None

    @classmethod
    def new(cls, data) -> Union["BaseLogSource", str]:
        return cls()

    def title(self) -> str:
        return "系统日志"

    def to_conf(self) -> dict:
        return {
            "source_type": "syslog"
        }

    def __eq__(self, other):
        return isinstance(other, SysLogSource)


class BTLogServer(BaseLogServer):
    _NGINX_LOG_FORMAT = """
log_format btlogjson escape=json '{'
    '"server_addr": "$server_addr",'
    '"server_port": $server_port,'
    '"host":"$http_host",'
    '"x_forwarded_for":"$http_x_forwarded_for",'
    '"remote_addr":"$remote_addr",'
    '"remote_port":$remote_port,'
    '"protocol":"$server_protocol",'
    '"req_length":$request_length,'
    '"method":"$request_method",'
    '"uri":"$request_uri",'
    '"status":$status,'
    '"sent_bytes":$body_bytes_sent,'
    '"referer":"$http_referer",'
    '"user_agent":"$http_user_agent",'
    '"upstream_addr":"$upstream_addr",'
    '"upstream_status":"$upstream_status",'
    '"upstream_response_time":"$upstream_response_time",'
    '"take_time":$request_time,'
    '"from_data":"$request_body"'
'}';
"""
    _APACHE_LOG_FORMAT = r"""
LogFormat "%h|%{c}a|%{remote}p|%A|%p|%V|%H|%>s|%{ms}T|%{Content-Length}i|%B|%m|\"%U\"|\"%q\"|\"%{X-Forwarded-For}i\"|\"%{Referer}i\"|\"%{User-Agent}i\"" btlog
"""
    _NGINX_LOG_ACCESS = """access_log syslog:server={ip}:{port},nohostname,tag=nginx__{name}__access btlogjson;"""
    _NGINX_LOG_ERROR = """error_log syslog:server={ip}:{port},nohostname,tag=nginx__{name}__error;"""
    _APACHE_LOG_ACCESS = """CustomLog "|/usr/bin/logger -P {port} -d -n {ip} -S 8192 -t 'apache__{name}__access'" btlog"""
    _APACHE_LOG_ERROR = """ErrorLog "|/usr/bin/logger -P {port} -d -n {ip} -S 8192 -t 'apache__{name}__error'" """
    _SYS_LOG = """
# 发送到堡塔日志服务系统
*.* @{ip}:{port}
"""

    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port
        self._conf: Optional[dict] = None
        self._end_set_flag = False

    @staticmethod
    def _check_conf(ip: Optional[str] = None, port: Optional[int] = None) -> Tuple[bool, str]:
        if ip is not None:
            try:
                IPv4Address(ip)
            except AddressValueError:
                return False, "ip地址解析错误"

        if port is not None:
            if isinstance(port, str):
                try:
                    port = int(port)
                except ValueError:
                    return False, "端口解析错误"
            if not 1 < port < 65535:
                return False, "端口解析错误"
        return True, ""

    @property
    def config(self) -> dict:
        if self._conf is not None:
            return self._conf
        self._conf = {
            "ip": self.ip,
            "port": self.port
        }
        return self._conf

    def check_exist(self, mgr: "LogServerManager") -> bool:
        for server_conf in mgr.config.get("servers", []):
            if "ip" in server_conf and "port" in server_conf:
                if server_conf["ip"] == self.ip and server_conf["port"] == self.port:
                    return True
        return False

    @config.setter
    def config(self, value: dict):
        if not isinstance(value, dict):
            return
        if "ip" in value:
            ip = value["ip"].strip()
            flag, _ = self._check_conf(ip=ip)
            if flag:
                self.ip = ip
        if "port" in value:
            port = value["port"].strip()
            flag, _ = self._check_conf(port=port)
            if flag:
                self.port = port

    @staticmethod
    def _test_env() -> bool:
        out, _ = public.ExecShell("bash {}/script/btlogserver_check.sh".format(public.get_panel_path()))
        if "successful" in out:
            return True
        return False

    def begin_set(self, source_class) -> Tuple[bool, str]:
        if source_class is SiteLogSource:
            if public.checkWebConfig() is not True:
                return False, "{}的配置文件存在异常，无法启动，请先排除异常，再进行设置".format(public.get_webserver())

        self._end_set_flag = False  # 开始设置时，标识改为FALSE
        return True, ""

    def end_set(self, source_class: BaseLogSource):
        # 根据标识决定是否重启服务
        if source_class is SiteLogSource and self._end_set_flag:
            public.serviceReload()
        elif source_class is SysLogSource and self._end_set_flag:
            public.ExecShell("systemctl restart rsyslog")

    def collect_log(self, source: BaseLogSource) -> Tuple[bool, str]:
        if not self._test_env():
            return False, "环境检查出错，系统中没有rsyslog日志服务且无法安装成功，不能发送日志"
        if isinstance(source, SiteLogSource):
            return self._collect_site(source)
        elif isinstance(source, SysLogSource):
            return self._collect_sys_log(source)
        return False, "不支持的日志来源"

    def _collect_site(self, source: SiteLogSource) -> Tuple[bool, str]:
        flag, msg = self._collect_nginx_site(source)
        if flag is False and source.webserver_type == "nginx":
            return False, msg
        flag, msg = self._collect_apache_site(source)
        if flag is False and source.webserver_type == "apache":
            return False, msg
        return True, msg

    def _collect_sys_log(self, source: SysLogSource) -> Tuple[bool, str]:
        syslog_conf = source.rsyslog_conf()
        if syslog_conf is None:
            return False, "系统日志配置文件丢失"
        rep_log = re.compile(r"\s*\*\.\* +@" + r"\.".join(self.ip.split(".")) + ":" + str(self.port))
        res = rep_log.search(syslog_conf["data"])
        if res is not None:
            return True, "设置成功"

        new_conf = syslog_conf["data"] + self._SYS_LOG.format(ip=self.ip, port=self.port)
        public.writeFile(syslog_conf["path"], new_conf)
        self._end_set_flag = True  # 设置成功，标识改为True，重启服务
        return True, "设置成功"

    @classmethod
    def _set_nginx_log_format(cls, source: SiteLogSource) -> Tuple[bool, str]:
        # 添加log format
        nginx_conf_file = "/www/server/nginx/conf/nginx.conf"
        if not os.path.exists(nginx_conf_file):
            return False, "nginx配置文件丢失"
        nginx_conf = public.readFile(nginx_conf_file)
        rep_format = re.compile(r"log_format +btlogjson +escape=json")
        if rep_format.search(nginx_conf):
            return True, ""

        # 通过检查第一个server的位置
        rep_first_server = re.compile(r"http\s*\{(.*\n)*\s*server\s*\{")
        tmp_res = rep_first_server.search(nginx_conf)
        if tmp_res:
            old_http_conf = tmp_res.group()
            # 在第一个server项前添加
            server_idx = old_http_conf.rfind("server")
            new_http_conf = old_http_conf[:server_idx] + cls._NGINX_LOG_FORMAT + old_http_conf[server_idx:]
            new_nginx_conf = rep_first_server.sub(new_http_conf, nginx_conf, 1)

            public.writeFile(nginx_conf_file, new_nginx_conf)
        else:
            # 在没有配置其他server项目时，通过检查include server项目检查
            # 通检查 include /www/server/panel/vhost/nginx/*.conf; 位置
            rep_include = re.compile(r"http\s*\{(.*\n)*\s*include +/www/server/panel/vhost/nginx/\*\.conf;")
            tmp_res = rep_include.search(nginx_conf)
            if not tmp_res:
                return False, "日志格式化方式配置失败"
            old_http_conf = tmp_res.group()

            include_idx = old_http_conf.rfind("include ")
            new_http_conf = old_http_conf[:include_idx] + cls._NGINX_LOG_FORMAT + old_http_conf[include_idx:]
            new_nginx_conf = rep_first_server.sub(new_http_conf, nginx_conf, 1)
            public.writeFile(nginx_conf_file, new_nginx_conf)

        if source.webserver_type == "nginx" and public.checkWebConfig() is not True:  # 检测失败，无法添加
            public.writeFile(nginx_conf_file, nginx_conf)
            return False, "日志格式化方式配置失败"
        return True, ""

    def _collect_nginx_site(self, source: SiteLogSource) -> Tuple[bool, str]:
        flag, msg = self._set_nginx_log_format(source)
        if not flag:
            return False, msg
        site_nginx_conf = source.nginx_config()
        if site_nginx_conf is None:
            return False, "站点nginx配置文件丢失"

        rep_log = re.compile(r"access_log +syslog:.*btlogjson\s*;\s*error_log +syslog:.*__error;\s*")
        if rep_log.search(site_nginx_conf["data"]):
            return True, "配置成功"

        trans: Callable[[str], str] = lambda x: "_".join(x.split("."))

        last_idx = site_nginx_conf["data"].rfind("}")
        site_new_conf = "{}\n{}\n{}\n{}".format(
            site_nginx_conf["data"][:last_idx],
            self._NGINX_LOG_ACCESS.format(ip=self.ip, port=self.port, name=trans(source.site_name)),
            self._NGINX_LOG_ERROR.format(ip=self.ip, port=self.port, name=trans(source.site_name)),
            site_nginx_conf["data"][last_idx:],
        )
        public.writeFile(site_nginx_conf["path"], site_new_conf)
        if source.webserver_type == "nginx" and public.checkWebConfig() is not True:
            public.writeFile(site_nginx_conf["path"], site_nginx_conf["data"])
            return False, "配置失败"

        self._end_set_flag = True  # 设置成功，标识改为True，重启服务
        return True, ""

    @classmethod
    def _set_apache_log_format(cls, source: SiteLogSource) -> Tuple[bool, str]:
        # 添加log format
        apache_conf_file = "/www/server/apache/conf/httpd.conf"
        if not os.path.exists(apache_conf_file):
            return False, "apache配置文件丢失"
        apache_conf = public.readFile(apache_conf_file)
        rep_format = re.compile(r'\s*LogFormat +"(.*\|).*" +btlog')
        if rep_format.search(apache_conf):
            return True, ""

        # 通过检查主配置文件中if log_config_module 的位置
        rep_first_server = re.compile(r"\s*<IfModule +log_config_module>\s*\n")
        tmp_res = rep_first_server.search(apache_conf)
        if not tmp_res:
            return False, "日志格式化方式配置失败,未找到配置添加位置"

        end_idx = tmp_res.end()
        # 在第一个server项前添加
        new_conf = apache_conf[:end_idx] + cls._APACHE_LOG_FORMAT + apache_conf[end_idx:]
        public.writeFile(apache_conf_file, new_conf)

        if source.webserver_type == "apache" and public.checkWebConfig() is not True:  # 检测失败，无法添加
            # public.print_log(public.checkWebConfig())
            # public.print_log(new_conf)
            public.writeFile(apache_conf_file, apache_conf)
            return False, "日志格式化方式配置失败"
        return True, ""

    def _collect_apache_site(self, source: SiteLogSource) -> Tuple[bool, str]:
        flag, msg = self._set_apache_log_format(source)
        if not flag:
            return False, msg
        site_apache_conf = source.apache_config()
        if site_apache_conf is None:
            return False, "站点apache配置文件丢失"

        rep_log = re.compile(r'''CustomLog +"\|/usr/bin/logger.*\n\s*ErrorLog +"\|/usr/bin/logger.*__error'"''')
        if rep_log.search(site_apache_conf["data"]):
            return True, "配置成功"

        last_start = 0
        rep_virtual_host = re.compile(r"\s*</VirtualHost>")
        new_conf_list = []
        change = False
        site_conf = site_apache_conf["data"]
        for tmp_res in rep_virtual_host.finditer(site_conf):
            idx = tmp_res.start()
            change = True
            new_conf_list.append(site_conf[last_start:idx])
            new_conf_list.append(
                "\n" + self._APACHE_LOG_ACCESS.format(ip=self.ip, port=self.port, name=source.site_name)
            )
            new_conf_list.append(
                "\n" + self._APACHE_LOG_ERROR.format(ip=self.ip, port=self.port, name=source.site_name)
            )
            last_start = idx
        if not change:
            return False, "apache配置文件错误"
        new_conf_list.append(site_conf[last_start:])

        public.writeFile(site_apache_conf["path"], "".join(new_conf_list))
        if source.webserver_type == "apache" and public.checkWebConfig() is not True:
            # public.print_log(public.checkWebConfig())
            public.writeFile(site_apache_conf["path"], site_apache_conf["data"])
            return False, "配置失败"

        self._end_set_flag = True  # 设置成功，标识改为True，重启服务
        return True, ""

    def un_collect_log(self, source: BaseLogSource) -> Tuple[bool, str]:
        if isinstance(source, SiteLogSource):
            return self._un_collect_site(source)
        elif isinstance(source, SysLogSource):
            return self._un_collect_sys_log(source)
        return False, "不支持的日志来源"

    def _un_collect_site(self, source: SiteLogSource) -> Tuple[bool, str]:
        flag, msg = self._un_collect_nginx_log(source)
        if flag is False and source.webserver_type == "nginx":
            return False, msg
        flag, msg = self._un_collect_apache_log(source)
        if flag is False and source.webserver_type == "apache":
            return False, msg
        return True, msg

    def _un_collect_sys_log(self, source: SysLogSource) -> Tuple[bool, str]:
        syslog_conf = source.rsyslog_conf()
        if syslog_conf is None:
            return False, "系统日志配置文件丢失"
        rep_log = re.compile(r"(?P<a># +(.*)\n)?\s*\*\.\* +@" + r"\.".join(self.ip.split(".")) + ":" + str(self.port))
        res = rep_log.search(syslog_conf["data"])
        if res is None:
            return True, "设置成功"

        new_conf = rep_log.sub("\n", syslog_conf["data"], 1)
        public.writeFile(syslog_conf["path"], new_conf)
        self._end_set_flag = True  # 设置成功，标识改为True，重启服务
        return True, "设置成功"

    def _un_collect_nginx_log(self, source: SiteLogSource) -> Tuple[bool, str]:
        site_nginx_conf = source.nginx_config()
        if site_nginx_conf is None:
            return False, "站点nginx配置文件丢失"

        rep_log = re.compile(r"access_log +syslog:.*btlogjson\s*;\s*error_log +syslog:.*__error;\s*")
        if not rep_log.search(site_nginx_conf["data"]):
            return True, "配置移除成功"
        new_conf = rep_log.sub("", site_nginx_conf["data"], 1)
        public.writeFile(site_nginx_conf["path"], new_conf)
        if source.webserver_type == "nginx" and public.checkWebConfig() is not True:
            public.writeFile(site_nginx_conf["path"], site_nginx_conf["data"])
            return False, "配置失败"
        self._end_set_flag = True  # 设置成功，标识改为True，重启服务
        return True, ""

    def _un_collect_apache_log(self, source: SiteLogSource) -> Tuple[bool, str]:
        site_apache_conf = source.apache_config()
        if site_apache_conf is None:
            return False, "站点apache配置文件丢失"

        rep_log = re.compile(r'''CustomLog +"\|/usr/bin/logger.*\n\s*ErrorLog +"\|/usr/bin/logger.*__error'"\s*''')
        if not rep_log.search(site_apache_conf["data"]):
            return True, "配置移除成功"
        new_conf = rep_log.sub("", site_apache_conf["data"])
        public.writeFile(site_apache_conf["path"], new_conf)
        if source.webserver_type == "apache" and public.checkWebConfig() is not True:
            public.writeFile(site_apache_conf["path"], site_apache_conf["data"])
            return False, "配置失败"

        self._end_set_flag = True  # 设置成功，标识改为True，重启服务
        return True, ""

    @classmethod
    def new(cls, data: dict) -> Union["BaseLogServer", str]:
        if not isinstance(data, dict):
            return "配置信息格式错误"
        if "ip" not in data or "port" not in data:
            return "配置信息缺少ip或port"
        data["ip"] = data["ip"].strip()
        if isinstance(data["port"], str):
            try:
                data["port"] = int(data["port"].strip())
            except ValueError:
                data["port"] = -1

        if not isinstance(data["port"], int):
            return "端口信息错误"

        flag, msg = cls._check_conf(ip=data["ip"], port=data["port"])
        if not flag:
            return msg
        return cls(ip=data["ip"], port=data["port"])


class LogServerManager(object):
    _CONFIG_FILE = "{}/data/logserver_config.json".format(public.get_panel_path())
    _SOURCE_MAP = {
        "site": SiteLogSource,
        "syslog": SysLogSource,
    }
    _LOG_SERVER_MAP: Dict[str, BaseLogServer] = {
        "bt_log_server": BTLogServer,
    }

    def __init__(self):
        self._config: Optional[Dict[str, List[dict]]] = None
        self.last_server = None

    @property
    def config(self) -> Dict[str, List[dict]]:
        if self._config is not None:
            return self._config
        default_conf = {}
        try:
            self._config = json.loads(public.readFile(self._CONFIG_FILE))
        except (json.JSONDecodeError, TypeError):
            pass
        if isinstance(self._config, dict):
            return self._config

        self._config = default_conf
        return self._config

    def save_conf(self):
        if self._config:
            public.writeFile(self._CONFIG_FILE, json.dumps(self._config))

    def add_logserver(self, server_type: str, data: dict) -> Tuple[bool, str]:
        if server_type not in self._LOG_SERVER_MAP:
            return False, "不支持的日志服务系统"

        try:
            s = self._LOG_SERVER_MAP[server_type].new(data)
        except:
            return False, "配置信息错误"
        else:
            if isinstance(s, str):
                return False, s
            if s.check_exist(self) is True:
                return False, "该配置已存在，请勿重新添加"

        data["id"] = str(int(time.time()))
        data["server_type"] = server_type
        if "servers" not in self.config:
            self.config["servers"] = []

        self.config["servers"].append(data)
        self.save_conf()
        self.last_server = data
        return True, "配置添加成功"

    def modify_logserver(self, server_id: str, data: dict) -> Tuple[bool, str]:
        server_conf = None
        for i in self.config.get("servers", []):
            if i["id"] == server_id:
                server_conf = i

        if not server_conf:
            return False, "未查询到该配置"

        if "id" in data:
            del data["id"]

        try:
            s = self._LOG_SERVER_MAP[server_conf["server_type"]].new(data)
        except:
            return False, "配置信息错误"
        else:
            if isinstance(s, str):
                return False, s

        server_conf.update(data)
        server = self._LOG_SERVER_MAP[server_conf["server_type"]].new(server_conf)
        if server_conf["id"] in self.config:
            # xiugai关于这个日志服务的配置
            s_list = self._build_source_by_conf(self.config.get(server_id, []))
            tmp = {}
            for k, v in groupby(s_list, key=lambda x: x.__class__):
                if k not in tmp:
                    tmp[k] = list(v)
                else:
                    tmp[k].extend(list(v))

            for k, v in tmp.items():
                f, _ = server.begin_set(k)
                if not f:
                    continue
                for i in v:
                    server.un_collect_log(i)
                    server.collect_log(i)
                server.end_set(k)
        self.save_conf()
        return True, "配置修改成功"

    def remove_logserver(self, server_id: str) -> Tuple[bool, str]:
        server_conf_idx = None
        server_conf = None
        for idx, i in enumerate(self.config.get("servers", [])):
            if i["id"] == server_id:
                server_conf = i
                server_conf_idx = idx

        if not server_conf:
            return False, "未查询到该配置"

        server = self._LOG_SERVER_MAP[server_conf["server_type"]].new(server_conf)
        if server_conf["id"] in self.config:
            # 移除关于这个日志服务的配置
            s_list = self._build_source_by_conf(self.config.get(server_id, []))
            tmp = {}
            for k, v in groupby(s_list, key=lambda x: x.__class__):
                if k not in tmp:
                    tmp[k] = list(v)
                else:
                    tmp[k].extend(list(v))

            for k, v in tmp.items():
                f, _ = server.begin_set(k)
                if not f:
                    continue
                for i in v:
                    server.un_collect_log(i)
                server.end_set(k)

            del self.config[server_conf["id"]]

        del self.config["servers"][server_conf_idx]
        self.save_conf()
        return True, "配置删除成功"

    def _get_server_by_id(self, server_id: str) -> Optional[dict]:
        server_conf = None
        for idx, i in enumerate(self.config.get("servers", [])):
            if i["id"] == server_id:
                server_conf = i
        return server_conf

    def _build_source_by_conf(self, data: Union[List[dict], dict]) -> List[BaseLogSource]:
        res = []
        if isinstance(data, dict):
            data = [data, ]
        for d in data:
            if "source_type" in d and d["source_type"] in self._SOURCE_MAP:
                try:
                    s = self._SOURCE_MAP[d["source_type"]].new(d)
                    if isinstance(s, BaseLogSource):
                        res.append(s)
                except:
                    pass
        return res

    def add_source(self, source_type: str, server_id: str, data: Union[List[Any], Any]):
        server_conf = self._get_server_by_id(server_id)
        if not server_conf:
            return public.returnMsg(False, "未查询到日志服务配置")

        if source_type not in self._SOURCE_MAP:
            return public.returnMsg(False, "不支持的日志来源类型")

        sources = []
        if isinstance(data, list):
            for i in data:
                source = self._SOURCE_MAP[source_type].new(i)
                if not isinstance(source, BaseLogSource):
                    return public.returnMsg(False, source)
                sources.append(source)
        else:
            source = self._SOURCE_MAP[source_type].new(data)
            if not isinstance(source, BaseLogSource):
                return public.returnMsg(False, source)
            sources.append(source)

        server = self._LOG_SERVER_MAP[server_conf["server_type"]].new(server_conf)

        flag, msg = server.begin_set(self._SOURCE_MAP[source_type])
        if not flag:
            return public.returnMsg(False, msg)
        res = []
        success_list = []
        for s in sources:
            flag, msg = server.collect_log(s)
            if not flag:
                res.append({
                    "title": s.title(),
                    "msg": msg,
                    "status": False
                })
            else:
                res.append({
                    "title": s.title(),
                    "msg": "设置成功",
                    "status": True
                })
                success_list.append(s)

        server.end_set(self._SOURCE_MAP[source_type])
        if server_conf["id"] not in self.config:
            self.config[server_conf["id"]] = []

        source_conf_list = self._build_source_by_conf(self.config.get(server_conf["id"]))
        for i in range(len(success_list) - 1, -1, -1):
            if success_list[i] in source_conf_list:
                del success_list[i]

        self.config[server_conf["id"]].extend([s.to_conf() for s in success_list])
        self.save_conf()
        return res

    def remove_source(self, source_type: str, server_id: str, data: Union[List[Any], Any]):
        server_conf = self._get_server_by_id(server_id)
        if not server_conf:
            return False, "未查询到日志服务配置"

        if source_type not in self._SOURCE_MAP:
            return False, "不支持的日志来源类型"

        sources = []
        if isinstance(data, list):
            for i in data:
                source = self._SOURCE_MAP[source_type].new(i)
                if not isinstance(source, BaseLogSource):
                    return False, source
                sources.append(source)
        else:
            source = self._SOURCE_MAP[source_type].new(data)
            if not isinstance(source, BaseLogSource):
                return False, source
            sources.append(source)

        server = self._LOG_SERVER_MAP[server_conf["server_type"]].new(server_conf)

        flag, msg = server.begin_set(self._SOURCE_MAP[source_type])
        if not flag:
            return False, msg
        res = []
        success_list = []
        for s in sources:
            flag, msg = server.un_collect_log(s)
            if not flag:
                res.append({
                    "title": s.title(),
                    "msg": msg,
                    "status": False
                })
            else:
                res.append({
                    "title": s.title(),
                    "msg": "设置成功",
                    "status": True
                })
                success_list.append(s)

        server.end_set(self._SOURCE_MAP[source_type])
        source_conf_list = self._build_source_by_conf(self.config.get(server_conf["id"]))
        for i in range(len(source_conf_list) - 1, -1, -1):
            if source_conf_list[i] in success_list:
                del source_conf_list[i]

        self.config[server_conf["id"]] = [i.to_conf() for i in source_conf_list]
        self.save_conf()
        return res

    def get_conf_list(self) -> List[dict]:
        res = []
        remove = []
        for k, v in self.config.items():
            if k == "servers":
                continue
            for idx, conf in enumerate(v):
                s = self._build_source_by_conf(conf)
                if s:
                    conf["server"] = self._get_server_by_id(k)
                    res.append(conf)
                else:
                    remove.append((k, idx))

        for k, idx in remove:
            del self.config[k][idx]
        if remove:
            self.save_conf()
        return res


class main:

    @staticmethod
    def collect_list(get=None):
        return LogServerManager().get_conf_list()

    @staticmethod
    def server_list(get=None):
        return LogServerManager().config.get("servers", [])

    @staticmethod
    def add_logserver(get):
        try:
            source_type, source_list = None, None
            server_type = get.server_type.strip()
            server_data = json.loads(get.server_data.strip())
            if "source_type" in get:
                source_type = get.source_type.strip()
            if "source_list" in get:
                source_list = json.loads(get.source_list.strip())
        except (AttributeError, json.JSONDecodeError):
            return public.returnMsg(False, "参数错误")

        logserver_mgr = LogServerManager()
        flag, msg = logserver_mgr.add_logserver(
            server_type=server_type,
            data=server_data,
        )
        # if not flag:
        #     return public.returnMsg(False, msg)
        # if source_type and source_list:
        #     flag, msg = logserver_mgr.add_source(
        #         source_type=source_type,
        #         server_id=logserver_mgr.last_server["id"],
        #         data=source_list,
        #     )
        return public.returnMsg(flag, msg)

    @staticmethod
    def modify_logserver(get):
        try:
            server_id = get.server_id.strip()
            server_data = json.loads(get.server_data.strip())
        except (AttributeError, json.JSONDecodeError):
            return public.returnMsg(False, "参数错误")

        return public.returnMsg(*LogServerManager().modify_logserver(
            server_id=server_id,
            data=server_data,
        ))

    @staticmethod
    def remove_logserver(get):
        try:
            server_id = get.server_id.strip()
        except (AttributeError, json.JSONDecodeError):
            return public.returnMsg(False, "参数错误")

        return public.returnMsg(*LogServerManager().remove_logserver(
            server_id=server_id
        ))

    @staticmethod
    def add_source(get):
        try:
            server_id = get.server_id.strip()
            source_type = get.source_type.strip()
            source_list = json.loads(get.source_list.strip())
        except (AttributeError, json.JSONDecodeError):
            return public.returnMsg(False, "参数错误")

        return LogServerManager().add_source(
            source_type=source_type,
            server_id=server_id,
            data=source_list,
        )

    @staticmethod
    def remove_source(get):
        try:
            server_id = get.server_id.strip()
            source_type = get.source_type.strip()
            source_list = json.loads(get.source_list.strip())
        except (AttributeError, json.JSONDecodeError):
            return public.returnMsg(False, "参数错误")

        return LogServerManager().remove_source(
            source_type=source_type,
            server_id=server_id,
            data=source_list,
        )
