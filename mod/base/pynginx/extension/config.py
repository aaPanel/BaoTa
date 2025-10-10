import os.path
import re
from itertools import product
from typing import Tuple, Any

from .server import ServerTools
from .. import *


class ConfigTools:

    def __init__(self, conf: Config):
        self._conf = conf

    def get_mian_server(self) -> Optional[ServerTools]:
        mian_server = self._get_mian_server()
        if mian_server is None:
            return None
        return ServerTools(mian_server)

    def _get_mian_server(self) -> Optional[Server]:
        http_block = self._conf.find_directives("http")
        if len(http_block) == 0:
            servers: List[Server] = [trans_(d, Server) for d in self._conf.directives if type(d) is Server]
            if len(servers) == 0:
                return None

            servers.sort(key=lambda x: 0 if not x.get_block() else len(x.get_block().get_directives()), reverse=True)
            return servers[0]
        else:
            http_dir = trans_(http_block[0], Http)
            servers: List[Server] = [trans_(d, Server) for d in http_dir.servers]
            if not servers:
                return None
            servers.sort(key=lambda x: 0 if not x.get_block() else len(x.get_block().get_directives()), reverse=True)
            return servers[0]

    def to_string(self):
        return dump_config(self._conf)


# 用于访问用户修改后的配置数据， 提取并更新到配置文件中
class ConfigFinder(ConfigTools):
    _domain_regexp = re.compile(r"^([\w\-*]{1,100}\.){1,24}([\w\-]{1,24}|[\w\-]{1,24}\.[\w\-]{1,24})$")

    def __init__(self, conf: Config):
        super().__init__(conf)
        self._server = self._get_mian_server()
        if self._server is None:
            raise ValueError("No server found")

    def find_domain(self) -> List[str]:
        tmp = self._server.top_find_directives("server_name")
        if len(tmp) == 0:
            return []

        res = []

        for i in trans_(tmp[0], Directive).parameters:
            name, port = i, ""
            if ":" in i:
                name, port = i.rsplit(":", 1)
            if not self._domain_regexp.match(name):
                continue
            if name.find('*') != -1 and name.find('*.') == -1:
                continue

            res.append(name if port == "" else name + ":" + port)

        return res

    def find_ports(self) -> Tuple[List[str], str]:
        site_port = set()
        https_port = "443"
        for d in self._server.top_find_directives("listen"):
            p = d.get_parameters()[0]
            port = None
            if p.isdecimal():
                port = p
            elif ":" in p:
                port = p.rsplit(":", 1)[1]

            if any((p in ("ssl", "quic") for p in d.get_parameters()[1:])):
                if port and port != "443":
                    https_port = port
            else:
                if port:
                    site_port.add(port)
        return list(site_port), https_port

    def find_ip_restrict(self) -> Tuple[List[str], List[str]]:
        allow = []
        deny = []
        for d in self._server.top_find_directives("allow"):
            if d.get_parameters()[0] == "all":
                continue
            allow.append(d.get_parameters()[0])

        for d in self._server.top_find_directives("deny"):
            if d.get_parameters()[0] == "all":
                continue
            deny.append(d.get_parameters()[0])

        return allow, deny

    def find_http_auth(self) -> List[Dict[str, str]]:
        locations = [trans_(l, Location) for l in self._server.top_find_directives("location")]
        if not locations:
            return []

        res = []
        for l in locations:
            if not l:
                continue
            d = l.top_find_directives("auth_basic_user_file")
            if not d:
                continue

            file = "" if not d[0].get_parameters() else d[0].get_parameters()[0]
            if not file:
                continue
            name = os.path.basename(file)
            if name.endswith(".htpasswd"):
                name = name[:-9]
            res.append({
                "auth_status": True,
                "auth_path": l.match,
                "auth_name": name,
                "username": "",
                "password": "",
                "auth_file": file,
            })
        return res

    def find_gzip(self) -> dict:
        gzip_status = self._server.top_find_directives_with_param("gzip", "on")
        gzip_level_dirs = self._server.top_find_directives("gzip_comp_level")
        gzip_types_dirs = self._server.top_find_directives("gzip_types")
        gzip_min_length_dirs = self._server.top_find_directives("gzip_min_length")

        if gzip_level_dirs:
            gzip_level = "6" if not gzip_level_dirs[0].get_parameters() else gzip_level_dirs[0].get_parameters()[0]
        else:
            gzip_level = "6"

        if gzip_types_dirs:
            gzip_types = gzip_types_dirs[0].get_parameters()
        else:
            gzip_types = [
                "text/plain", "text/css", "text/xml", "text/javascript", "application/x-javascript",
                "application/json", "application/xml", "application/xml+rss", "application/vnd.ms-fontobject",
                "application/x-font-ttf", "application/x-font-opentype", "application/x-font-truetype",
            ]
        if gzip_min_length_dirs:
            gzip_min_length = "1k" if not gzip_min_length_dirs[0].get_parameters() else \
                gzip_min_length_dirs[0].get_parameters()[0]
        else:
            gzip_min_length = "1k"

        return {
            "gzip_status": bool(gzip_status),
            "gzip_min_length": gzip_min_length,
            "gzip_comp_level": gzip_level,
            "gzip_types": " ".join(gzip_types)
        }

    def find_server_proxy_cache(self) -> Tuple[bool, str, str]:
        proxy_cache = self._server.top_find_directives("proxy_cache")
        if not proxy_cache:
            return False, "", ""
        proxy_cache = trans_(proxy_cache[0], Directive)
        if proxy_cache.parameters:
            cache_zone = proxy_cache.parameters[0]
        else:
            return False, "", ""
        proxy_cache_valid_dirs = self._server.top_find_directives("proxy_cache_valid")
        timeout = "1d"
        for d in proxy_cache_valid_dirs:
            t = d.get_parameters()[-1]
            if set(d.get_parameters()[:-1]) != {"404"}:
                timeout = t

        return bool(proxy_cache), cache_zone, timeout

    def find_websocket_support(self) -> bool:
        """查找server块是否支持websocket"""
        return bool(
            self._server.top_find_directives_with_param("proxy_set_header", "Upgrade") and
            self._server.top_find_directives_with_param("proxy_set_header", "Connection")
        )

    def find_log_path(self, uninclude: List[str] = ("bt-monitor.sock",)) -> dict:
        access_logs = [
            i for i in self._server.block.directives
            if i.get_name() == "access_log" and not any(unp in p for unp, p in product(uninclude, i.get_parameters()))
        ]
        if not access_logs:
            return {
                "log_type": "default",
                "log_path": "",
                "rsyslog_host": ""
            }
        access_log = trans_(access_logs[0], Directive)
        if len(access_log.parameters) < 1:
            return {
                "log_type": "default",
                "log_path": "",
                "rsyslog_host": ""
            }
        log_path_str = access_log.parameters[0]
        log_path = ""
        rsyslog_host = ""
        if "syslog" in log_path_str:
            log_type = "rsyslog"
            res = re.search(r"syslog:server=(?P<host>[^,]*)", log_path_str)
            if res:
                rsyslog_host = res.group("host")
        elif log_path_str == "off":
            log_type = "off"
        else:
            log_type = "file"
            log_path = os.path.dirname(log_path_str)
            if log_path == "/www/wwwlogs":
                log_type = "default"

        return {
            "log_type": log_type,
            "log_path": log_path,
            "rsyslog_host": rsyslog_host
        }

    def find_proxy(self) -> List[Dict]:
        locations = [trans_(l, Location) for l in self._server.top_find_directives("location")]
        if not locations:
            return []
        res = []
        for loc in locations:
            _lf = _LocationFinder(loc)
            proxy_data = _lf.find_proxy()
            if not proxy_data:
                continue
            ip_white, ip_black = _lf.find_ip_restrict()
            proxy_data["ip_limit"] = {
                "ip_black": ip_black,
                "ip_white": ip_white,
            }
            p_status, cache_zone, expires = _lf.find_proxy_cache()
            if p_status:
                proxy_data["proxy_cache"] = {
                    "cache_status": p_status,
                    "cache_zone": cache_zone,
                    "expires": expires,
                }
            else:
                proxy_data["proxy_cache"] = {"cache_status": p_status, }
            proxy_data["gzip"] = _lf.find_gzip()
            proxy_data["sub_filter"] = {
                "sub_filter_str": _lf.find_sub_filter(),
            }
            proxy_data["websocket"] = {"websocket_status": _lf.find_websocket_support()}
            connect, send, read = _lf.find_timeout()
            proxy_data["timeout"] = {
                "proxy_connect_timeout": connect,
                "proxy_send_timeout": send,
                "proxy_read_timeout": read,
            }
            proxy_data["security_referer"] = _lf.find_referer_conf()
            res.append(proxy_data)
        return res

    def export_proxy_config(self) -> Dict:
        domain_list = self.find_domain()
        site_port, https_port = self.find_ports()
        ip_white, ip_black = self.find_ip_restrict()
        ip_limit = {"ip_black": ip_black, "ip_white": ip_white}
        basic_auth = self.find_http_auth()
        p_status, cache_zone, expires = self.find_server_proxy_cache()
        if p_status:
            proxy_cache = {
                "cache_status": p_status,
                "cache_zone": cache_zone,
                "expires": expires,
            }
        else:
            proxy_cache = {
                "cache_status": p_status
            }
        gzip = self.find_gzip()
        websocket = {
            "websocket_status": self.find_websocket_support(),
        }
        proxy_log = self.find_log_path()
        return {
            "domain_list": domain_list,
            "site_port": site_port,
            "https_port": https_port,
            "ip_limit": ip_limit,
            "basic_auth": basic_auth,
            "proxy_cache": proxy_cache,
            "gzip": gzip,
            "websocket": websocket,
            "proxy_log": proxy_log,
            "proxy_info": self.find_proxy(),
        }


class _LocationFinder:

    def __init__(self, l: Location):
        self._location = l

    def find_proxy(self) -> Optional[Dict]:
        proxy_pass_dirs = self._location.top_find_directives("proxy_pass")
        if not proxy_pass_dirs:
            return None

        host_dirs = self._location.top_find_directives_with_param("proxy_set_header", "Host")
        proxy_pass = proxy_pass_dirs[0].get_parameters()[0]
        return {
            "proxy_pass": proxy_pass,
            "proxy_host": host_dirs[0].parameters[1] if host_dirs else "$http_host",
            "proxy_type": "http" if proxy_pass.startswith("http") else "unix",
            "proxy_path": self._location.match,
        }

    def find_ip_restrict(self) -> Tuple[List[str], List[str]]:
        allow, deny = [], []
        for d in self._location.top_find_directives("allow"):
            if d.get_parameters()[0] == "all":
                continue
            allow.append(d.get_parameters()[0])

        for d in self._location.top_find_directives("deny"):
            if d.get_parameters()[0] == "all":
                continue
            deny.append(d.get_parameters()[0])

        return allow, deny

    def find_proxy_cache(self) -> Tuple[bool, str, str]:
        proxy_cache = self._location.top_find_directives("proxy_cache")
        if not proxy_cache:
            return False, "", ""
        proxy_cache = trans_(proxy_cache[0], Directive)
        if proxy_cache.parameters:
            cache_zone = proxy_cache.parameters[0]
        else:
            return False, "", ""
        proxy_cache_valid_dirs = self._location.top_find_directives("proxy_cache_valid")
        timeout = "1d"
        for d in proxy_cache_valid_dirs:
            t = d.get_parameters()[-1]
            if set(d.get_parameters()[:-1]) != {"404"}:
                timeout = t

        return bool(proxy_cache), cache_zone, timeout

    def find_gzip(self) -> dict:
        gzip_status = self._location.top_find_directives_with_param("gzip", "on")
        gzip_level_dirs = self._location.top_find_directives("gzip_comp_level")
        gzip_types_dirs = self._location.top_find_directives("gzip_types")
        gzip_min_length_dirs = self._location.top_find_directives("gzip_min_length")

        if gzip_level_dirs:
            gzip_level = "6" if not gzip_level_dirs[0].get_parameters() else gzip_level_dirs[0].get_parameters()[0]
        else:
            gzip_level = "6"

        if gzip_types_dirs:
            gzip_types = gzip_types_dirs[0].get_parameters()
        else:
            gzip_types = [
                "text/plain", "text/css", "text/xml", "text/javascript", "application/x-javascript",
                "application/json", "application/xml", "application/xml+rss", "application/vnd.ms-fontobject",
                "application/x-font-ttf", "application/x-font-opentype", "application/x-font-truetype",
            ]
        if gzip_min_length_dirs:
            gzip_min_length = "1k" if not gzip_min_length_dirs[0].get_parameters() else \
                gzip_min_length_dirs[0].get_parameters()[0]
        else:
            gzip_min_length = "1k"

        return {
            "gzip_status": bool(gzip_status),
            "gzip_min_length": gzip_min_length,
            "gzip_comp_level": gzip_level,
            "gzip_types": " ".join(gzip_types)
        }

    def find_websocket_support(self) -> bool:
        """查找server块是否支持websocket"""
        return bool(
            self._location.top_find_directives_with_param("proxy_set_header", "Upgrade") and
            self._location.top_find_directives_with_param("proxy_set_header", "Connection")
        )

    def find_sub_filter(self) -> List[Dict[str, str]]:
        res = []
        for d in self._location.get_block().get_directives():
            if d.get_name() == "sub_filter":
                res.append({
                    "oldstr": d.get_parameters()[0].strip('"'),
                    "newstr": d.get_parameters()[1].strip('"'),
                    "sub_type": ""
                })
            elif d.get_name() == "subs_filter":
                res.append({
                    "oldstr": d.get_parameters()[0].strip('"'),
                    "newstr": d.get_parameters()[1].strip('"'),
                    "sub_type": d.get_parameters()[2].strip('"'),
                })
        return res

    def find_timeout(self) -> Tuple[str, str, str]:
        res = ["60", "600", "600"]
        dirs = ("proxy_connect_timeout", "proxy_send_timeout", "proxy_read_timeout")
        for d in self._location.block.get_directives():
            if d.get_name() in dirs:
                res[dirs.index(d.get_name())] = d.get_parameters()[0].strip("s")
        return res

    def find_referer_conf(self) -> Dict[str, Any]:
        loc: Optional[Location] = None
        locs = self._location.top_find_directives_with_param("location", "~")
        if locs:
            for loc_if in locs:
                loc_obj = trans_(loc_if, Location)
                if not loc_obj:
                    continue
                if not loc_obj.match.startswith(r".*\.(") and not loc_obj.match.endswith(r")$"):
                    continue
                if loc_obj.top_find_directives("expires") and \
                        loc_obj.top_find_directives("valid_referers") and \
                        loc_obj.top_find_directives_like_param("if", "$invalid_referer"):
                    loc = loc_obj
                    break
        if not loc:
            return {"status": False}
        suffix_list = loc.match[5:-2].split("|")
        domain_list = []
        allow_empty = False
        for p in loc.top_find_directives("valid_referers")[0].get_parameters():
            if p in ("none", "blocked"):
                allow_empty = True
            else:
                domain_list.append(p)

        ifb = loc.top_find_directives_like_param("if", "$invalid_referer")[0].get_block()
        return_rule = ifb.find_directives("return")
        if return_rule:
            return_rule = return_rule[0].get_parameters()[0]
        else:
           for d in ifb.find_directives("rewrite"):
               if d.get_parameters() and d.get_parameters()[0] == "/.*":
                   return_rule = d.get_parameters()[1]
        return {
            "status": True,
            "fix": ",".join(suffix_list),
            "domains": ",".join(domain_list),
            "return_rule": return_rule,
            "http_status": allow_empty
        }




