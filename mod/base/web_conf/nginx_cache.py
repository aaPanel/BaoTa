import json
import os
import re
from typing import Optional, List, Tuple, Dict, Any, Union
from .util import read_file, write_file, check_server_config, service_reload
from mod.base import pynginx
from mod.base.pynginx.extension import ServerTools

class NginxStaticCacheMgr:
    proxy_pass_pattern = re.compile(r"(?P<not_used>#[^\n]*)?proxy_pass\s+[^\n]*")
    proxy_import_pattern = re.compile(r"(?P<not_used>#[^\n]*)?include\s+\S+vhost/nginx/proxy/[^\s/]+/\*\.conf\s*;")

    def __init__(self, config_prefix: str = ""):
        self.config_prefix: str = config_prefix
        self.nginx_vhost_path = "/www/server/panel/vhost/nginx"

    def set_cache(self, site_name: str, old_suffix:List[str], new_suffix:List[str], time_out: str) -> Optional[str]:
        config_file = "{}/{}{}.conf".format(self.nginx_vhost_path, self.config_prefix, site_name)
        if not os.path.exists(config_file):
            return "网站配置文件不存在"

        conf_data = read_file(config_file)
        if not conf_data:
            return "网站配置文件为空"

        conf = pynginx.parse_file(config_file)
        server_list = conf.find_servers()
        for server in server_list:
            server_tools = ServerTools(server)
            res = server_tools.set_static_cache(old_suffix, new_suffix, time_out)
            if  res:
                return res

        new_conf = pynginx.dump_config(conf)
        write_file(config_file, new_conf)

        check_err = check_server_config()
        if check_err:
            write_file(config_file, conf_data)
            return "Nginx配置浏览器缓存失败：" + check_err
        else:
            service_reload()
            return None

    def read_cache(self, site_name: str) -> List[Dict]:
        config_file = "{}/{}{}.conf".format(self.nginx_vhost_path, self.config_prefix, site_name)
        if not os.path.exists(config_file):
            return []

        conf_data = read_file(config_file)
        if not conf_data:
            return []

        conf = pynginx.parse_file(config_file)
        server_list = conf.find_servers()
        if not server_list:
            return []
        server = server_list[0]
        static_pattern = re.compile(r'\.\*\\\.\((?P<suffix>[^)]+)\)\??\$')
        tmp_locations = server.top_find_directives_with_param("location", "~", static_pattern)
        return [
            {
                "suffix": static_pattern.search(loc.match).group("suffix").split("|"),
                "time_out": loc.top_find_directives("expires")[0].parameters[0]
            }
            for loc in tmp_locations if loc.top_find_directives("expires")
        ]


    def remove_cache(self, site_name: str, suffix: List[str]) -> Optional[str]:
        config_file = "{}/{}{}.conf".format(self.nginx_vhost_path, self.config_prefix, site_name)
        if not os.path.exists(config_file):
            return "网站配置文件不存在"

        conf_data = read_file(config_file)
        if not conf_data:
            return "网站配置文件为空"

        conf = pynginx.parse_file(config_file)
        server_list = conf.find_servers()
        for server in server_list:
            server_tools = ServerTools(server)
            server_tools.remove_static_cache(suffix)

        new_conf = pynginx.dump_config(conf)
        write_file(config_file, new_conf)

        check_err = check_server_config()
        if check_err:
            write_file(config_file, conf_data)
            return "Nginx配置浏览器缓存失败：" + check_err
        else:
            service_reload()
            return None

    def can_set_cache(self, site_name: str) -> str:
        config_file = "{}/{}{}.conf".format(self.nginx_vhost_path, self.config_prefix, site_name)
        if not os.path.exists(config_file):
            return "网站配置文件不存在"

        conf_data = read_file(config_file)
        if not conf_data:
            return "网站配置文件为空"

        proxy_pass = self.proxy_pass_pattern.search(conf_data)
        if proxy_pass and not proxy_pass.group("not_used"):
            return "已存在代理配置【{}】，可能导致冲突，请自行配置缓存信息".format(proxy_pass.group().strip())
        proxy_import = self.proxy_import_pattern.search(conf_data)
        if proxy_import and not proxy_import.group("not_used"):
            return "已使用反向代理配置【{}】，可能导致冲突，请自行配置缓存信息".format(proxy_import.group().strip())

        check_err = check_server_config()
        if check_err:
            return "Nginx配置文件错误，请先修复后在尝试：" + check_err
        return ""
