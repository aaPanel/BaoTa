import os
import re
from typing import Optional, List, Tuple, Dict, Any, Union
from .util import read_file, write_file, check_server_config, service_reload


class NginxGzipMgr:
    _gzip_pattern = re.compile(r'(\s*#GZIP.*\n)?(\s*gzip[ _].*\n)+(\s*#GZIP.*\n*)?')
    _read_pattern_map = {
        "min_length": (re.compile(r"gzip_min_length\s+(?P<target>\d+[km]?)\s*;"), "1k"),
        "comp_level": (re.compile(r"gzip_comp_level\s+(?P<target>[0-9])\s*;"), "6"),
        "gzip_types": (
            re.compile(r"gzip_types\s+(?P<target>.*)\s*;"),
            "text/plain application/javascript application/x-javascript text/javascript text/css application/xml application/json image/jpeg image/gif image/png font/ttf font/otf image/svg+xml application/xml+rss text/x-js"
        ),
    }

    def __init__(self, config_prefix: str = ""):
        self.config_prefix: str = config_prefix
        self.nginx_vhost_path = "/www/server/panel/vhost/nginx"

    @staticmethod
    def _get_server_level(server_config: str) -> List[List[Tuple[int, int]]]:
        rep_server = re.compile(r"\s*server\s*\{")
        res = rep_server.search(server_config)  # 从第一个server开始划分
        if not res:
            return []

        comments = [(i.start(), i.end()) for i in re.finditer(r"#.*", server_config)]
        in_comments = lambda x: any(l <= x < r for l, r in comments)

        level = 1
        level_1_data = []
        start = res.end()
        for i in range(res.end(), len(server_config)):
            if in_comments(i):
                continue
            if server_config[i] == '{':
                if level == 1:
                    level_1_data.append((start, i - 1))
                level += 1
                if level == 1:
                    start = i + 1
            elif server_config[i] == '}':
                if level == 1:
                    level_1_data.append((start, i - 1))
                level -= 1
                if level == 1:
                    start = i + 1

        if level != 0:
            return []
        # 划分多个server
        start_idx_list = []
        for srv in rep_server.finditer(server_config):  # 处理多个server的情况即子域名绑定
            start_idx_list.append(srv.end())

        if len(start_idx_list) == 1:
            return [level_1_data]
        else:
            res_list = []
            start_idx_list.append(-1)
            for l in level_1_data:
                if l[0] == start_idx_list[0]:
                    start_idx_list = start_idx_list[1:]
                    res_list.append([])
                res_list[-1].append(l)

            return res_list

    def set_gzip(self,
                 site_name: str,
                 comp_level: int = 6,
                 min_length: Tuple[int, str] = ("1", "k"),
                 gzip_types: List[str] = None) -> Optional[str]:
        config_file = "{}/{}{}.conf".format(self.nginx_vhost_path, self.config_prefix, site_name)
        if not os.path.exists(config_file):
            return "网站配置文件不存在"

        conf_data = read_file(config_file)
        if not conf_data:
            return "网站配置文件为空"

        check_err = check_server_config()
        if check_err:
            return "Nginx配置文件错误，请先修复后在尝试：" + check_err

        if not gzip_types:
            gzip_types = [
                "text/plain", "application/javascript", "application/x-javascript", "text/javascript", "text/css",
                "application/xml", "application/json", "image/jpeg", "image/gif", "image/png", "font/ttf", "font/otf",
                "image/svg+xml", "application/xml+rss", "text/x-js"
            ]

        gzip_config = """
    #GZIP START
    gzip on;
    gzip_min_length {};
    gzip_buffers 4 16k;
    gzip_http_version 1.1;
    gzip_comp_level {};
    gzip_types {};
    gzip_vary on;
    gzip_proxied expired no-cache no-store private auth;
    gzip_disable "MSIE [1-6]\\.";
    #GZIP END
""".format("{}{}".format(*min_length), comp_level, " ".join(gzip_types))

        new_conf = self._gzip_pattern.sub("\n", conf_data)
        server_level = self._get_server_level(new_conf)
        if len(server_level) > 0:
            for srv in server_level[::-1]:
                new_conf = new_conf[:srv[-1][0]] + gzip_config + new_conf[srv[-1][0]:]
        else:
            return "未查询到可用server配置块"

        write_file(config_file, new_conf)
        check_err = check_server_config()
        if check_err:
            write_file(config_file, conf_data)
            return "Nginx配置Gzip失败：" + check_err
        else:
            service_reload()
            return None

    def remove_gzip(self, site_name: str) -> Optional[str]:
        config_file = "{}/{}{}.conf".format(self.nginx_vhost_path, self.config_prefix, site_name)
        check_err = check_server_config()
        if check_err:
            return "Nginx配置文件错误，请先修复后在尝试：" + check_err

        conf_data = read_file(config_file)
        if not conf_data:
            return "网站配置文件为空"

        new_conf = self._gzip_pattern.sub("\n", conf_data)
        write_file(config_file, new_conf)
        check_err = check_server_config()
        if check_err:
            write_file(config_file, conf_data)
            return "Nginx配置Gzip失败：" + check_err
        else:
            service_reload()
            return None

    def read_gzip(self, site_name: str) -> Tuple[Dict[str, Any], Optional[str]]:
        config_file = "{}/{}{}.conf".format(self.nginx_vhost_path, self.config_prefix, site_name)
        conf_data = read_file(config_file)
        if not conf_data:
            return {}, "网站配置文件为空"
        gzip_config_ret = self._gzip_pattern.search(conf_data)
        if not gzip_config_ret:
            default_data: Dict[str, Any] = {
                key: default_str for key, (_, default_str) in self._read_pattern_map.items()
            }
            default_data["status"] = False
            return default_data, None

        gzip_config = gzip_config_ret.group()
        ret_dict: Dict[str, Any] = {}
        for key, (pattern, default_str) in self._read_pattern_map.items():
            res = pattern.search(gzip_config)
            if res:
                ret_dict[key] = res.group("target")
            else:
                ret_dict[key] = default_str

        ret_dict["status"] = True
        return ret_dict, None

    @staticmethod
    def check_gzip_args(get) -> Union[Dict[str, Any], str]:
        min_length: str = get.get("min_length/s", "")
        if not min_length or not re.match(r"[0-9]+[kKmM]?", min_length):
            return "请输入正确的最小压缩长度"
        args = {}
        if min_length[-1] in "kKmM":
            min_length_int = int(min_length[:-1])
            args["min_length"] = (min_length_int, min_length[-1].lower())
        else:
            min_length_int = int(min_length)
            args["min_length"] = (min_length_int, "")

        comp_level: int = get.get("comp_level/d", 6)
        if not 0 < comp_level < 10:
            return "请输入正确压缩等级"
        args["comp_level"] = comp_level

        gzip_types_str: str = get.get("gzip_types/s", "")
        gzip_types = gzip_types_str.split()
        if not gzip_types:
            return "请输入要压缩的文件类型"
        args["gzip_types"] = gzip_types
        return args
