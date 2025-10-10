import os
import re
import json
from typing import Optional, Union, List, Dict, Any
from mod.base.web_conf.util import check_server_config, write_file, read_file, service_reload
from mod.base import json_response
from urllib3.util import Url, parse_url

import public


class RealServerProxy:
    panel_path = "/www/server/panel"
    default_headers = (
        "Host", "X-Real-IP", "X-Forwarded-For", "REMOTE-HOST", "X-Host", "X-Scheme", "Upgrade", "Connection"
    )

    def __init__(self, project_data: dict):
        self.config_prefix: str = "java_"

        site_name = project_data["name"]
        self.project_id = project_data["id"]
        self.project_config = project_data["project_config"]

        self._config: Optional[List[dict]] = None
        self._ng_file: str = "{}/vhost/nginx/{}{}.conf".format(self.panel_path, self.config_prefix, site_name)
        self._ap_file: str = "{}/vhost/apache/{}{}.conf".format(self.panel_path, self.config_prefix, site_name)
        self.site_name = site_name
        self.ws_type = public.get_webserver()

    @staticmethod
    def new_id() -> str:
        from uuid import uuid4
        return uuid4().hex[::3]

    @property
    def config(self) -> List[dict]:
        if self._config is None:
            if "proxy_info" in self.project_config:
                self._config = self.project_config["proxy_info"]
            else:
                self._config = []

        return self._config

    def save_config(self):
        if self._config is not None:
            self.project_config["proxy_info"] = self._config
            public.M("sites").where("id=?", (self.project_id,)).update(
                {"project_config": json.dumps(self.project_config)}
            )

    # 检查代理是否存在
    def _check_even(self, proxy_conf: dict, is_modify) -> Optional[str]:
        if is_modify is True:
            for i in self.config:
                if i["proxy_dir"] == proxy_conf["proxy_dir"] and i["proxy_id"] != proxy_conf["proxy_id"]:
                    return '指定反向代理名称或代理文件夹已存在'
                if i["proxy_port"] == proxy_conf["proxy_port"] and i["proxy_id"] != proxy_conf["proxy_id"]:
                    return '指定反向代理端口已存在对应的代理'
        else:
            for i in self.config:
                if i["proxy_port"] == proxy_conf["proxy_port"]:
                    return '指定反向代理端口已存在对应的代理'

    def check_args(self, get, is_modify=False) -> Union[str, dict]:
        err_msg = check_server_config()
        if isinstance(err_msg, str):
            return 'WEB服务器配置配置文件错误ERROR:<br><font style="color:red;">' + \
                err_msg.replace("\n", '<br>') + '</font>'
        data = {
            "proxy_dir": "/",
            "status": 1,
            "proxy_id": self.new_id(),
            "rewrite": {
                "status": False,
                "src_path": "",
                "target_path": "",
            },
            "add_headers": [],
        }
        try:
            data["site_name"] = get.site_name.strip()
            if "proxy_dir" in get:
                data["proxy_dir"] = get.proxy_dir.strip()
            if "proxy_id" in get:
                data["proxy_id"] = get.proxy_id.strip()
            data["proxy_port"] = int(get.proxy_port)
            data["status"] = int(get.status.strip())
            if hasattr(get, "rewrite"):
                data["rewrite"] = get.rewrite
                if isinstance(get.rewrite, str):
                    data["rewrite"] = json.loads(get.rewrite)

            if hasattr(get, "add_headers"):
                data["add_headers"] = get.add_headers
                if isinstance(get.add_headers, str):
                    data["add_headers"] = json.loads(get.add_headers)
        except:
            public.print_log(public.get_error_info())
            return "参数错误"

        if not 1 < data["proxy_port"] < 65536:
            return '代理端口范围错误'

        if not data["proxy_dir"].endswith("/"):
            data["proxy_dir"] += "/"

        evn_msg = self._check_even(data, is_modify)
        if isinstance(evn_msg, str):
            return evn_msg

        rep_re_key = re.compile(r'''[?=\[\])(*&^%$#@!~`{}><,'"\\]+''')
        special = r'''?，=，[，]，)，(，*，&，^，%，$，#，@，!，~，`，{，}，>，<，\，'，"'''
        # 检测代理目录格式
        if rep_re_key.search(data["proxy_dir"]):
            return "代理路由不能有以下特殊符号" + special

        if not isinstance(data["rewrite"], dict):
            return "路由重写配置错误"
        if "status" not in data["rewrite"] or not data["rewrite"]["status"]:
            data["rewrite"] = {
                "status": False,
                "src_path": "",
                "target_path": "",
            }
        else:
            if not ("src_path" in data["rewrite"] and "target_path" in data["rewrite"]):
                return "路由重写参数配置错误"
            if not isinstance(data["rewrite"]["src_path"], str) or not isinstance(data["rewrite"]["target_path"], str):
                return "路由重写参数配置错误"
            if rep_re_key.search(data["rewrite"]["src_path"]):
                return "路由重写匹配路由不能有以下特殊符号" + special
            if rep_re_key.search(data["rewrite"]["target_path"]):
                return "路由重写目标路由不能有以下特殊符号" + special

        if not isinstance(data["add_headers"], list):
            return "自定义代理头配置错误"
        else:
            rep_blank_space = re.compile(r"\s+")
            for h in data["add_headers"]:
                if "k" not in h or "v" not in h:
                    return "自定义代理头配置错误"
                if not isinstance(h["k"], str) or not isinstance(h["v"], str):
                    return "自定义代理头配置错误"
                if rep_blank_space.search(h["k"]) or rep_blank_space.search(h["v"]):
                    return "代理头配置中不能包含有空格"
                if h["k"] in self.default_headers:
                    return '代理头配置中不能包含有默认头【{}】'.format(h["k"])

        return data

    def check_location(self, proxy_dir: str) -> Optional[str]:
        # 伪静态文件路径
        rewrite_conf_path = "%s/vhost/rewrite/%s%s.conf" % (self.panel_path, self.config_prefix, self.site_name)

        rep_location = re.compile(r"s*location\s+(\^~\s*)?%s\s*{" % proxy_dir)

        for i in [rewrite_conf_path, self._ng_file]:
            conf = read_file(i)
            if isinstance(conf, str) and rep_location.search(conf):
                return '伪静态/站点主配置文件已经存路径【{}】的配置'.format(proxy_dir)

    @staticmethod
    def _set_nginx_proxy_base():
        file = "/www/server/nginx/conf/proxy.conf"
        setup_path = "/www/server"
        if not os.path.exists(file):
            conf = '''proxy_temp_path %s/nginx/proxy_temp_dir;
proxy_cache_path %s/nginx/proxy_cache_dir levels=1:2 keys_zone=cache_one:10m inactive=1d max_size=5g;
client_body_buffer_size 512k;
proxy_connect_timeout 60;
proxy_read_timeout 60;
proxy_send_timeout 60;
proxy_buffer_size 32k;
proxy_buffers 4 64k;
proxy_busy_buffers_size 128k;
proxy_temp_file_write_size 128k;
proxy_next_upstream error timeout invalid_header http_500 http_503 http_404;
proxy_cache cache_one;''' % (setup_path, setup_path)
            write_file(file, conf)

        conf = read_file(file)
        if conf and conf.find('include proxy.conf;') == -1:
            conf = re.sub(r"include\s+mime\.types;", "include mime.types;\n\tinclude proxy.conf;", conf)
            write_file(file, conf)

        # websocket前置map
        map_file = "/www/server/panel/vhost/nginx/0.websocket.conf"
        if not os.path.exists(map_file):
            write_file(map_file, '''
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''  close;
}''')

    @staticmethod
    def build_proxy_conf(proxy_data: dict) -> str:
        ng_proxy = '''
    #PROXY-START{proxy_dir}
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
    #PROXY-END{proxy_dir}
'''

        rewrite = ""
        if "rewrite" in proxy_data and proxy_data["rewrite"].get("status", False):
            rewrite = proxy_data["rewrite"]
            src_path = rewrite["src_path"]
            if not src_path.endswith("/"):
                src_path += "/"
            target_path = rewrite["target_path"]
            if target_path.endswith("/"):
                target_path = target_path[:-1]
            if src_path == "/":
                rewrite = "\n        rewrite ^{}$ {} break;".format(src_path, target_path)
            else:
                rewrite = "\n        rewrite ^{}(.*)$ {}/$1 break;".format(src_path, target_path)

        add_headers = ""
        if "add_headers" in proxy_data:
            header_tmp = "        proxy_set_header {} {};"
            add_headers_list = [header_tmp.format(h["k"], h["v"]) for h in proxy_data["add_headers"] if
                                "k" in h and "v" in h]
            add_headers = "\n".join(add_headers_list)
            if add_headers:
                add_headers = "\n" + add_headers

        # 构造替换字符串
        proxy_dir = proxy_data["proxy_dir"]
        proxy_site = "http://127.0.0.1:{}".format(proxy_data["proxy_port"])

        proxy = ng_proxy.format(
            proxy_dir=proxy_dir,
            proxy_url=proxy_site,
            rewrite=rewrite,
            add_headers=add_headers,
        )

        return proxy

    def add_nginx_proxy(self, proxy_data: dict) -> Optional[str]:
        ng_conf = read_file(self._ng_file)
        if not ng_conf:
            return "Nginx配置文件不存在"

        proxy_str = self.build_proxy_conf(proxy_data)

        # 添加配置信息到配置文件中
        rep_list = [
            (re.compile(r"\s*#PROXY-LOCAl-END.*", re.M), True),  # 添加到反向代理结尾的上面
            (re.compile(r"\s*#ROXY-END.*", re.M), False),  # 添加到其他的反向代理的下面
            (re.compile(r"\s*#\s*HTTP反向代理相关配置结束\s*<<<.*", re.M), False),  # 添加到其他的反向代理的下面
            (re.compile(r"\s*include\s*/www/server/panel/vhost/rewrite/.*(\s*#.*)?"), False),
            # 添加到伪静态的下面
            # (re.compile(r"(#.*)?\s*location\s+/\.well-known/\s*{"), True),  # 添加到location /.well-known/上面
        ]

        # 使用正则匹配确定插入位置
        def set_by_rep_idx(tmp_rep: re.Pattern, use_start: bool) -> bool:
            tmp_res = tmp_rep.search(ng_conf)
            if not tmp_res:
                return False
            if use_start:
                new_conf = ng_conf[:tmp_res.start()] + proxy_str + tmp_res.group() + ng_conf[tmp_res.end():]
            else:
                new_conf = ng_conf[:tmp_res.start()] + tmp_res.group() + proxy_str + ng_conf[tmp_res.end():]

            write_file(self._ng_file, new_conf)
            if self.ws_type == "nginx" and check_server_config() is not None:
                write_file(self._ng_file, ng_conf)
                return False
            return True

        for r, s in rep_list:
            if set_by_rep_idx(r, s):
                break
        else:
            return "无法在配置文件中定位到需要添加的项目"

    def _unset_nginx_proxy(self, proxy_data) -> Optional[str]:
        ng_conf = read_file(self._ng_file)
        if not isinstance(ng_conf, str):
            return "配置文件不存在"

        proxy_dir = proxy_data["proxy_dir"]
        rep_start_end = re.compile(r"\s*#PROXY-START%s(.|\n)*?#PROXY-END%s[^\n]*" % (proxy_dir, proxy_dir))
        if rep_start_end.search(ng_conf):
            new_ng_conf = rep_start_end.sub("", ng_conf)
            write_file(self._ng_file, new_ng_conf)
            if self.ws_type == "nginx":
                err_msg = check_server_config()
                if isinstance(err_msg, str):
                    write_file(self._ng_file, ng_conf)
                    return err_msg
            else:
                return

        rep_location = re.compile(r"(\s*#.*?)\s*location\s+(\^~\s*)?%s\s*{" % proxy_dir)
        res = rep_location.search(ng_conf)
        if res:
            end_idx = self.find_nginx_block_end(ng_conf, res.end() + 1)
            if not end_idx:
                return

            block = ng_conf[res.start(): end_idx]
            if block.find("proxy_pass") == -1:  # 如果这块内不包含proxy_pass 则跳过
                return

            # 异除下一个注释行
            res_end = re.search(r"\s*#PROXY-END.*", ng_conf[end_idx + 1:])
            if res_end:
                end_idx += res_end.end()

            new_ng_conf = ng_conf[:res.start()] + ng_conf[end_idx + 1:]
            write_file(self._ng_file, new_ng_conf)
            if self.ws_type == "nginx":
                err_msg = check_server_config()
                if isinstance(err_msg, str):
                    write_file(self._ng_file, ng_conf)
                    return err_msg

    @staticmethod
    def find_nginx_block_end(data: str, start_idx: int) -> Optional[int]:
        if len(data) < start_idx + 1:
            return None

        level = 1
        line_start = 0
        for i in range(start_idx + 1, len(data)):
            if data[i] == '\n':
                line_start = i + 1
            if data[i] == '{' and line_start and data[line_start: i].find("#") == -1:  # 没有注释的下一个{
                level += 1
            elif data[i] == '}' and line_start and data[line_start: i].find("#") == -1:  # 没有注释的下一个}
                level -= 1
            if level == 0:
                return i

        return None

    @staticmethod
    def build_apache_conf(proxy_data: dict) -> str:
        return '''
    #PROXY-START{proxy_dir}
    <IfModule mod_proxy.c>
        ProxyRequests Off
        SSLProxyEngine on
        ProxyPass {proxy_dir} {url}/
        ProxyPassReverse {proxy_dir} {url}/
        RequestHeader set Host "%{{Host}}e"
        RequestHeader set X-Real-IP "%{{REMOTE_ADDR}}e"
        RequestHeader set X-Forwarded-For "%{{X-Forwarded-For}}e"
        RequestHeader setifempty X-Forwarded-For "%{{REMOTE_ADDR}}e"
    </IfModule>
    #PROXY-END{proxy_dir}
'''.format(proxy_dir=proxy_data["proxy_dir"], url="http://127.0.0.1:{}".format(proxy_data["proxy_port"]))

    def add_apache_proxy(self, proxy_data: dict) -> Optional[str]:
        ap_conf = read_file(self._ap_file)
        if not ap_conf:
            return "Apache配置文件不存在"

        proxy_str = self.build_apache_conf(proxy_data)

        # 添加配置信息到配置文件中
        rep_list = [
            (re.compile(r"#ROXY-END[^\n]*\n"), False),  # 添加到其他的反向代理的下面
            (re.compile(r"#\s*HTTP反向代理相关配置结束\s*<<<[^\n]*\n"), False),  # 添加到其他的反向代理的下面
            (
                re.compile(r"\s*(#SSL[^\n]*)?\s*<IfModule\s*alias_module>[^\n]*\s*.*/.well-known/[^\n]*\s*</IfModule>"),
                True  # 添加到location /.well-known/上面
            ),
            (re.compile(r"\s*</VirtualHost>[^\n]*\n?"), True),
        ]

        # 使用正则匹配确定插入位置
        def set_by_rep_idx(tmp_rep: re.Pattern, use_start: bool) -> bool:
            new_conf_list = []
            change_flag = False
            start_idx = 0
            for tmp in tmp_rep.finditer(ap_conf):
                change_flag = True
                new_conf_list.append(ap_conf[start_idx:tmp.start()])
                start_idx = tmp.end()
                if use_start:
                    new_conf_list.append(proxy_str)
                    new_conf_list.append(tmp.group())
                else:
                    new_conf_list.append(tmp.group())
                    new_conf_list.append(proxy_str)

            if not change_flag:
                return False

            new_conf_list.append(ap_conf[start_idx:])
            write_file(self._ap_file, "".join(new_conf_list))
            if self.ws_type == "apache" and check_server_config() is not None:
                write_file(self._ap_file, ap_conf)
                return False
            return True

        for r, s in rep_list:
            if set_by_rep_idx(r, s):
                break
        else:
            return "无法在配置文件中定位到需要添加的项目"

    def remove_apache_proxy(self, proxy_data) -> Optional[str]:
        ap_conf = read_file(self._ap_file)
        if not isinstance(ap_conf, str):
            return "配置文件不存在"

        proxy_dir = proxy_data["proxy_dir"]
        rep_start_end = re.compile(r"\s*#PROXY-START%s(.|\n)*?#PROXY-END%s[^\n]*" % (proxy_dir, proxy_dir))
        if rep_start_end.search(ap_conf):
            new_ap_conf = rep_start_end.sub("", ap_conf)
            write_file(self._ap_file, new_ap_conf)
            if self.ws_type == "apache":
                err_msg = check_server_config()
                if isinstance(err_msg, str):
                    write_file(self._ap_file, ap_conf)
                    return err_msg
            else:
                return

        rep_if_mod = re.compile(
            r"(\s*#.*)?\s*<IfModule mod_proxy\.c>\s*(.*\n){3,5}\s*"
            r"ProxyPass\s+%s\s+\S+/\s*(.*\n){1,2}\s*</IfModule>(\s*#.*)?" % proxy_dir)

        res = rep_if_mod.search(ap_conf)
        if res:
            new_ap_conf = rep_if_mod.sub("", ap_conf)
            write_file(self._ap_file, new_ap_conf)
            if self.ws_type == "apache":
                err_msg = check_server_config()
                if isinstance(err_msg, str):
                    write_file(self._ap_file, ap_conf)
                    return err_msg

    def create_proxy(self, proxy_data: dict) -> Optional[str]:
        for i in self.config:
            if i["proxy_dir"] == proxy_data["proxy_dir"]:
                proxy_data["proxy_id"] = i["proxy_id"]
                return self.modify_proxy(proxy_data)

        if self.ws_type == "nginx":
            err_msg = self.check_location(proxy_data["proxy_dir"])
            if err_msg:
                return json_response(False, err_msg)

        self._set_nginx_proxy_base()
        error_msg = self.add_nginx_proxy(proxy_data)
        if self.ws_type == "nginx" and error_msg:
            return error_msg
        error_msg = self.add_apache_proxy(proxy_data)
        if self.ws_type == "apache" and error_msg:
            return error_msg
        self.config.append(proxy_data)
        self.save_config()
        service_reload()

    def modify_proxy(self, proxy_data: dict) -> Optional[str]:
        idx = None
        for index, i in enumerate(self.config):
            if i["proxy_id"] == proxy_data["proxy_id"] and i["site_name"] == proxy_data["site_name"]:
                idx = index
                break

        if idx is None:
            return "未找到该id的反向代理配置"

        if proxy_data["proxy_dir"] != self.config[idx]["proxy_dir"] and self.ws_type == "nginx":
            err_msg = self.check_location(proxy_data["proxy_dir"])
            if err_msg:
                return json_response(False, err_msg)

        self._set_nginx_proxy_base()
        error_msg = self._unset_nginx_proxy(self.config[idx])
        if self.ws_type == "nginx" and error_msg:
            return error_msg

        error_msg = self.remove_apache_proxy(self.config[idx])
        if self.ws_type == "apache" and error_msg:
            return error_msg

        error_msg = self.add_nginx_proxy(proxy_data)
        if self.ws_type == "nginx" and error_msg:
            return error_msg

        error_msg = self.add_apache_proxy(proxy_data)
        if self.ws_type == "apache" and error_msg:
            return error_msg

        self.config[idx] = proxy_data
        self.save_config()
        service_reload()

    def remove_proxy(self, site_name, proxy_id, multiple=False) -> Optional[str]:
        idx = None
        for index, i in enumerate(self.config):
            if i["proxy_id"] == proxy_id and i["site_name"] == site_name:
                idx = index

        if idx is None:
            return "未找到该名称的反向代理配置"

        err_msg = self._unset_nginx_proxy(self.config[idx])
        if err_msg and self.ws_type == "nginx":
            return err_msg

        error_msg = self.remove_apache_proxy(self.config[idx])
        if self.ws_type == "apache" and error_msg:
            return error_msg

        del self.config[idx]
        self.save_config()
        if not multiple:
            service_reload()

    def get_proxy_list_by_nginx(self) -> List[Dict[str, Any]]:
        ng_conf = read_file(self._ng_file)
        if not isinstance(ng_conf, str):
            return []

        rep_location = re.compile(r"\s*location\s+([=*~^]*\s+)?(?P<path>\S+)\s*{")
        proxy_location_path_info = {}
        for tmp in rep_location.finditer(ng_conf):
            end_idx = self.find_nginx_block_end(ng_conf, tmp.end() + 1)
            if end_idx and ng_conf[tmp.start(): end_idx].find("proxy_pass") != -1:
                p = tmp.group("path")
                if not p.endswith("/"):
                    p += "/"
                proxy_location_path_info[p] = (tmp.start(), end_idx)

        res_pass = re.compile(r"proxy_pass\s+(?P<pass>\S+)\s*;", re.M)
        remove_list = []
        local_host = ("127.0.0.1", "localhost", "0.0.0.0")
        for i in self.config:
            if i["proxy_dir"] in proxy_location_path_info:
                start_idx, end_idx = proxy_location_path_info[i["proxy_dir"]]
                block = ng_conf[start_idx: end_idx]
                res_pass_res = res_pass.search(block)
                if res_pass_res:
                    url = parse_url(res_pass_res.group("pass"))
                    if isinstance(url, Url) and url.hostname in local_host and url.port == i["proxy_port"]:
                        i["status"] = True
                        proxy_location_path_info.pop(i["proxy_dir"])
                        continue

            remove_list.append(i)

        need_save = False
        for i in remove_list:
            self.config.remove(i)
            need_save = True

        for path, (start_idx, end_idx) in proxy_location_path_info.items():
            block = ng_conf[start_idx: end_idx]
            res_pass_res = res_pass.search(block)
            if res_pass_res:
                url = parse_url(res_pass_res.group("pass"))
                if isinstance(url, Url) and url.hostname in ("127.0.0.1", "localhost", "0.0.0.0"):
                    self.config.insert(0, {
                        "proxy_id": self.new_id(),
                        "site_name": self.site_name,
                        "proxy_dir": "/",
                        "proxy_port": url.port,
                        "status": 1,
                        "rewrite": {
                            "status": False,
                            "src_path": "",
                            "target_path": "",
                        },
                        "add_headers": [],
                    })
                need_save = True
        if need_save:
            self.save_config()

        return self.config

    def get_proxy_list_by_apache(self) -> List[Dict[str, Any]]:
        ap_conf = read_file(self._ap_file)
        if not isinstance(ap_conf, str):
            return []

        rep_proxy_pass = r"ProxyPass\s+%s\s+\S+/"
        mian_location_use = False
        for i in self.config:
            if i["proxy_dir"] == "/":
                mian_location_use = True
            rep_l = re.search(rep_proxy_pass % i["proxy_dir"], ap_conf, re.M)
            if rep_l:
                i["status"] = 1
            else:
                i["status"] = 0

        if not mian_location_use:
            res_l = re.search(
                r"\s*<IfModule mod_proxy\.c>\s*(.*\n){3,5}\s*"
                r"ProxyPass\s+/\s+(?P<pass>\S+)/\s*(.*\n){1,2}\s*</IfModule>", ap_conf)

            if not res_l:
                return self.config

            url = parse_url(res_l.group("pass"))
            if isinstance(url, Url) and url.hostname in ("127.0.0.1", "localhost", "0.0.0.0"):
                self.config.insert(0, {
                    "proxy_id": self.new_id(),
                    "site_name": self.site_name,
                    "proxy_dir": "/",
                    "proxy_port": url.port,
                    "status": 1,
                    "rewrite": {
                        "status": False,
                        "src_path": "",
                        "target_path": "",
                    },
                    "add_headers": [],
                })
                self.save_config()

        return self.config

    def get_proxy_list(self) -> List[Dict[str, Any]]:
        if self.ws_type == "nginx":
            return self.get_proxy_list_by_nginx()
        else:
            return self.get_proxy_list_by_apache()


