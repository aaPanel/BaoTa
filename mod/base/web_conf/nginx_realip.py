import os
import re
import json
import sys
import ipaddress
from typing import Tuple, Optional, Union, List, Dict, Any
from .util import webserver, check_server_config, write_file, read_file, service_reload
from mod.base import json_response

class NginxRealIP:

    def __init__(self):
        pass

    def set_real_ip(self, site_name:str, ip_header:str, allow_ip: List[str], recursive: bool = False) -> Optional[str]:
        if not webserver() == 'nginx':
            return "仅在nginx服务器可使用"
        res = check_server_config()
        if res:
            return "当前配置文件有误，请检查排出异常后重试，ERROR: %s".format(res)
        self._set_ext_real_ip_file(site_name, status=True, ip_header=ip_header, allow_ip=allow_ip, recursive=recursive)
        res = check_server_config()
        if res:
            self._set_ext_real_ip_file(site_name, status=False, ip_header="", allow_ip=[], recursive=False)
            return "配置失败：{}".format(res)
        else:
            service_reload()

    def close_real_ip(self, site_name:str):
        self._set_ext_real_ip_file(site_name, status=False, ip_header="", allow_ip=[], recursive=False)
        service_reload()
        return

    def get_real_ip(self, site_name:str) -> Dict[str, Any]:
        return self._read_ext_real_ip_file(site_name)

    def _set_ext_real_ip_file(self, site_name: str, status:bool, ip_header:str, allow_ip: List[str], recursive: bool = False):
        ext_file = "/www/server/panel/vhost/nginx/extension/{}/proxy_real_ip.conf".format(site_name)
        if not status:
            if os.path.exists(ext_file):
                os.remove(ext_file)
            return

        if not os.path.exists(os.path.dirname(ext_file)):
            os.makedirs(os.path.dirname(ext_file))
        real_ip_from = ""
        for ip in allow_ip:
            tmp_ip = self.formatted_ip(ip)
            if tmp_ip:
                real_ip_from += "    set_real_ip_from {};\n".format(ip)
        if not real_ip_from:
            real_ip_from = "set_real_ip_from 0.0.0.0/0;\nset_real_ip_from ::/0;\n"
        conf_data = "{}real_ip_header    {};\nreal_ip_recursive {};\n".format(
            real_ip_from, ip_header, "on" if recursive else "off"
        )
        write_file(ext_file, conf_data)

    @staticmethod
    def _read_ext_real_ip_file(site_name: str) -> Dict[str, Any]:
        ret = {
            "ip_header": "",
            "allow_ip": [],
            "recursive": False
        }
        ext_file = "/www/server/panel/vhost/nginx/extension/{}/proxy_real_ip.conf".format(site_name)
        if os.path.exists(ext_file):
            data = read_file(ext_file)
            if data:
                for line in data.split("\n"):
                    line = line.strip("; ")
                    if line.startswith("real_ip_header"):
                        ret["ip_header"] = line.split()[1]
                    elif line.startswith("set_real_ip_from"):
                        ret["allow_ip"].append(line.split()[1])
                    elif line.startswith("real_ip_recursive"):
                        ret["recursive"] = True if line.split()[1] == "on" else False
        return ret

    @staticmethod
    def formatted_ip(ip: str) -> str:
        try:
            ip = ipaddress.ip_address(ip)
            return ip.compressed
        except:
            try:
                ip = ipaddress.ip_network(ip)
                return ip.compressed
            except:
                pass
        return ""