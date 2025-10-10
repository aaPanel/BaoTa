import os
import re
import json
import shutil
import sys
import traceback
from hashlib import md5
from typing import Tuple, Optional, Union, List, Dict, Any
from .util import webserver, check_server_config, write_file, read_file, DB, service_reload, get_log_path, pre_re_key
from mod.base import json_response


class RealProxy:
    panel_path = "/www/server/panel"
    _proxy_conf_file = "{}/data/mod_proxy_file.conf".format(panel_path)

    def __init__(self, config_prefix: str):
        self.config_prefix: str = config_prefix
        self._config: Optional[List[dict]] = None

    # {
    #     "proxyname": "yyy",
    #     "sitename": "www.12345test.com",
    #     "proxydir": "/",
    #     "proxysite": "http://www.baidu.com",
    #     "todomain": "www.baidu.com",
    #     "type": 0,
    #     "cache": 0,
    #     "subfilter": [
    #         {"sub1": "", "sub2": ""},
    #         {"sub1": "", "sub2": ""},
    #         {"sub1": "", "sub2": ""}],
    #     "advanced": 1,
    #     "cachetime": 1
    # }

    @property
    def config(self) -> List[dict]:
        if self._config is None:
            try:
                self._config = json.loads(read_file(self._proxy_conf_file))
            except (json.JSONDecodeError, TypeError, ValueError):
                self._config = []
        return self._config

    def save_config(self):
        if self._config is not None:
            write_file(self._proxy_conf_file, json.dumps(self._config))

    # 检查代理是否存在
    def _check_even(self, proxy_conf: dict, is_modify) -> bool:
        for i in self.config:
            if i["sitename"] == proxy_conf["sitename"]:
                if is_modify is False:
                    if i["proxydir"] == proxy_conf["proxydir"] or i["proxyname"] == proxy_conf["proxyname"]:
                        return True
                else:
                    if i["proxyname"] != proxy_conf["proxyname"] and i["proxydir"] == proxy_conf["proxydir"]:
                        return True

    # 检测全局代理和目录代理是否同时存在
    def _check_proxy_even(self, proxy_conf: dict, is_modify) -> bool:
        n = 0
        if is_modify:
            for i in self.config:
                if i["sitename"] == proxy_conf["sitename"]:
                    n += 1
            if n == 1:
                return False
        for i in self.config:
            if i["sitename"] == proxy_conf["sitename"]:
                if i["advanced"] != proxy_conf["advanced"]:
                    return True
        return False

    def check_args(self, get, is_modify=False) -> Union[str, dict]:
        if check_server_config():
            return '配置文件出错请先排查配置'
        data = {
            "advanced": 0,
            "proxydir": "",
            "cache": 0,
            "cachetime": 1,
            "type": 0,
            "todomain": "$host",
        }
        try:
            data["proxyname"] = get.proxyname.strip()
            data["sitename"] = get.sitename.strip()
            if "proxydir" in get:
                data["proxydir"] = get.proxydir.strip()
            data["proxysite"] = get.proxysite.strip()
            if "todomain" in get:
                data["todomain"] = get.todomain.strip()
            data["type"] = int(get.type.strip())
            data["cache"] = int(get.cache.strip())
            data["subfilter"] = json.loads(get.subfilter.strip())
            data["advanced"] = int(get.advanced.strip())
            data["cachetime"] = int(get.cachetime.strip())
        except:
            return "参数错误"

        if is_modify is False:
            if len(data["proxyname"]) < 3 or len(data["proxyname"]) > 40:
                return '名称必须大于3小于40个字符串'

        if self._check_even(data, is_modify):
            return '指定反向代理名称或代理文件夹已存在'
        # 判断代理，只能有全局代理或目录代理
        if self._check_proxy_even(data, is_modify):
            return '不能同时设置目录代理和全局代理'
        # 判断cachetime类型
        if data["cachetime"] < 1:
            return "缓存时间不能为空"

        rep = "http(s)?\:\/\/"
        rep_re_key = re.compile(r'''[?=\[\])(*&^%$#@!~`{}><,'"\\]+''')
        # 检测代理目录格式
        if rep_re_key.search(data["proxydir"]):
            return "代理目录不能有以下特殊符号 ?,=,[,],),(,*,&,^,%,$,#,@,!,~,`,{,},>,<,\,',\"]"
        # 检测发送域名格式
        if get.todomain:
            if re.search("[}{#;\"\']+", data["todomain"]):
                return '发送域名格式错误:' + data["todomain"] + '<br>不能存在以下特殊字符【 }  { # ; \" \' 】 '
        if webserver() != 'openlitespeed' and not get.todomain:
            data["todomain"] = "$host"

        # 检测目标URL格式
        if not re.match(rep, data["proxysite"]):
            return '域名格式错误 ' + data["proxysite"]
        if rep_re_key.search(data["proxysite"]):
            return "目标URL不能有以下特殊符号 ?,=,[,],),(,*,&,^,%,$,#,@,!,~,`,{,},>,<,\,',\"]"

        if not data["proxysite"].split('//')[-1]:
            return '目标URL不能为[http://或https://],请填写完整URL，如：https://www.bt.cn'

        for s in data["subfilter"]:
            if not s["sub1"]:
                continue
            if not s["sub1"] and s["sub2"]:
                return '请输入被替换的内容'
            elif s["sub1"] == s["sub2"]:
                return '替换内容与被替换内容不能一致'
        return data

    def check_location(self, site_name, proxy_dir: str) -> Optional[str]:
        # 伪静态文件路径
        rewrite_conf_path = "%s/vhost/rewrite/%s%s.conf" % (self.panel_path, self.config_prefix, site_name)
        # vhost文件
        vhost_path = "%s/vhost/nginx/%s%s.conf" % (self.panel_path, self.config_prefix, site_name)

        rep_location = re.compile(r"location\s+(\^~\s*)?%s\s*{" % proxy_dir)

        for i in [rewrite_conf_path, vhost_path]:
            conf = read_file(i)
            if isinstance(conf, str) and rep_location.search(conf):
                return '伪静态/站点主配置文件已经存在全局反向代理'

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
            rep = "include\s+mime.types;"
            conf = re.sub(rep, "include mime.types;\n\tinclude proxy.conf;", conf)
            write_file(file, conf)

    def set_nginx_proxy_include(self, site_name) -> Optional[str]:
        self._set_nginx_proxy_base()
        ng_file = "{}/vhost/nginx/{}{}.conf".format(self.panel_path, self.config_prefix, site_name)
        ng_conf = read_file(ng_file)
        if not ng_conf:
            return "配置文件丢失"
        cure_cache = '''location ~ /purge(/.*) {
        proxy_cache_purge cache_one $host$1$is_args$args;
        #access_log  /www/wwwlogs/%s_purge_cache.log;
    }''' % site_name

        proxy_dir = "{}/vhost/nginx/proxy/{}".format(self.panel_path, site_name)
        if not os.path.isdir(os.path.dirname(proxy_dir)):
            os.makedirs(os.path.dirname(proxy_dir))

        if not os.path.isdir(proxy_dir):
            os.makedirs(proxy_dir)

        include_conf = (
            "\n    #清理缓存规则\n"
            "    %s\n"
            "    #引用反向代理规则，注释后配置的反向代理将无效\n"
            "    include /www/server/panel/vhost/nginx/proxy/%s/*.conf;\n"
        ) % (cure_cache, site_name)

        rep_include = re.compile(r"\s*include.*/proxy/.*/\*\.conf\s*;", re.M)
        if rep_include.search(ng_conf):
            return
        # 添加 引入
        rep_list = [
            (re.compile(r"\s*include\s+.*/rewrite/.*\.conf;(\s*#REWRITE-END)?"), False),  # 先匹配伪静态，有伪静态就加到伪静态下
            (re.compile(r"#PHP-INFO-END"), False),  # 匹配PHP配置, 加到php配置下
            (re.compile(r"\sinclude +.*/ip-restrict/.*\*\.conf;", re.M), False),  # 匹配IP配置, 加其下
            (re.compile(r"#SECURITY-END"), False),  # 匹配Referer配置, 加其下
        ]

        # 使用正则匹配确定插入位置
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

        now_ng_conf = read_file(ng_file)
        # 清理文件缓存
        rep_location = re.compile(r"location\s+~\s+\.\*\\\.[^{]*{(\s*(expires|error_log|access_log).*;){3}\s*}\s*")

        new__ng_conf = rep_location.sub("", now_ng_conf)
        write_file(ng_file, new__ng_conf)
        if webserver() == "nginx" and check_server_config() is not None:
            write_file(ng_file, now_ng_conf)

    def un_set_nginx_proxy_include(self, site_name) -> Optional[str]:
        ng_file = "{}/vhost/nginx/{}{}.conf".format(self.panel_path, self.config_prefix, site_name)
        ng_conf = read_file(ng_file)
        if not ng_conf:
            return "配置文件丢失"
        rep_list = [
            re.compile(r"\s*#清理缓存规则\n"),
            re.compile(r"\s*location\s+~\s+/purge[^{]*{[^}]*}\s*"),
            re.compile(r"(#[^#\n]*\n)?\s*include.*/proxy/.*/\*\.conf\s*;[^\n]*\n"),
        ]
        new_conf = ng_conf
        for rep in rep_list:
            new_conf = rep.sub("", new_conf, 1)

        write_file(ng_file, new_conf)
        if webserver() == "nginx" and check_server_config() is not None:
            write_file(ng_file, ng_conf)
            return "配置移除失败"

    def set_apache_proxy_include(self, site_name):
        ap_file = "{}/vhost/apache/{}{}.conf".format(self.panel_path, self.config_prefix, site_name)
        ap_conf = read_file(ap_file)
        if not ap_conf:
            return "配置文件丢失"
        proxy_dir = "{}/vhost/apache/proxy/{}".format(self.panel_path, site_name)

        if not os.path.isdir(os.path.dirname(proxy_dir)):
            os.makedirs(os.path.dirname(proxy_dir))
        if not os.path.isdir(proxy_dir):
            os.makedirs(proxy_dir)

        include_conf = (
            "    #引用反向代理规则，注释后配置的反向代理将无效\n"
            "    IncludeOptional /www/server/panel/vhost/apache/proxy/%s/*.conf\n"
        ) % site_name

        rep_include = re.compile(r"\s*IncludeOptional.*/proxy/.*/\*\.conf\s*;", re.M)
        if rep_include.search(ap_conf):
            return

        # 添加 引入
        rep_list = [
            (re.compile(r"<FilesMatch \\\.php\$>(.|\n)*?</FilesMatch>[^\n]*\n"), False),  # 匹配PHP配置, 加到php配置下
            (re.compile(r"CustomLog[^\n]*\n"), False),  # 匹配Referer配置, 加其下
        ]

        # 使用正则匹配确定插入位置
        def set_by_rep_idx(rep: re.Pattern, use_start: bool) -> bool:
            new_conf_list = []
            last_idx = 0
            for tmp in rep.finditer(ap_conf):
                new_conf_list.append(ap_conf[last_idx:tmp.start()])
                if use_start:
                    new_conf_list.append(include_conf)
                    new_conf_list.append(tmp.group())
                else:
                    new_conf_list.append(tmp.group())
                    new_conf_list.append(include_conf)
                last_idx = tmp.end()
            if last_idx == 0:
                return False

            new_conf_list.append(ap_conf[last_idx:])

            new_conf = "".join(new_conf_list)
            write_file(ap_file, new_conf)
            if webserver() == "apache" and check_server_config() is not None:
                write_file(ap_file, ap_conf)
                return False
            return True

        for r, s in rep_list:
            if set_by_rep_idx(r, s):
                break
        else:
            return "无法在配置文件中定位到需要添加的项目"

    def un_set_apache_proxy_include(self, site_name) -> Optional[str]:
        ng_file = "{}/vhost/apache/{}{}.conf".format(self.panel_path, self.config_prefix, site_name)
        ap_conf = read_file(ng_file)
        if not ap_conf:
            return "配置文件丢失"
        rep_include = re.compile(r"(#.*\n)?\s*IncludeOptiona.*/proxy/.*/\*\.conf\s*[^\n]\n")

        new_conf = rep_include.sub("", ap_conf)

        write_file(ng_file, new_conf)
        if webserver() == "apache" and check_server_config() is not None:
            write_file(ng_file, ap_conf)
            return "配置移除失败"

    def set_nginx_proxy(self, proxy_data: dict) -> Optional[str]:
        proxy_name_md5 = self._calc_proxy_name_md5(proxy_data["proxyname"])
        ng_proxy_file = "%s/vhost/nginx/proxy/%s/%s_%s.conf" % (
            self.panel_path, proxy_data["sitename"], proxy_name_md5,  proxy_data["sitename"])
        if proxy_data["type"] == 0:
            if os.path.isfile(ng_proxy_file):
                os.remove(ng_proxy_file)
                return

        random_string = self._random_string()

        # websocket前置map
        map_file = "{}/vhost/nginx/0.websocket.conf".format(self.panel_path)
        if not os.path.exists(map_file):
            write_file(map_file, '''
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''  close;
}''')
        # 构造缓存配置
        ng_cache = """
    if ( $uri ~* "\.(gif|png|jpg|css|js|woff|woff2)$" )
    {
        expires 1m;
    }
    proxy_ignore_headers Set-Cookie Cache-Control expires;
    proxy_cache cache_one;
    proxy_cache_key $host$uri$is_args$args;
    proxy_cache_valid 200 304 301 302 %sm;""" % proxy_data["cachetime"]
        no_cache = """
    set $static_file%s 0;
    if ( $uri ~* "\.(gif|png|jpg|css|js|woff|woff2)$" )
    {
        set $static_file%s 1;
        expires 1m;
        }
    if ( $static_file%s = 0 )
    {
    add_header Cache-Control no-cache;
    }""" % (random_string, random_string, random_string)

        ng_proxy = '''
#PROXY-START%s

location ^~ %s
{
    proxy_pass %s;
    proxy_set_header Host %s;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header REMOTE-HOST $remote_addr;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
    proxy_http_version 1.1;
    # proxy_hide_header Upgrade;

    add_header X-Cache $upstream_cache_status;

    #Set Nginx Cache
    %s
    %s
}

#PROXY-END%s'''

        # 构造替换字符串
        ng_sub_data_list = []
        for s in proxy_data["subfilter"]:
            if not s["sub1"]:
                continue
            if '"' in s["sub1"]:
                s["sub1"] = s["sub1"].replace('"', '\\"')
            if '"' in s["sub2"]:
                s["sub2"] = s["sub2"].replace('"', '\\"')
            ng_sub_data_list.append('    sub_filter "%s" "%s";' % (s["sub1"], s["sub2"]))
        if ng_sub_data_list:
            ng_sub_filter = '''
    proxy_set_header Accept-Encoding "";
    %s
    sub_filter_once off;''' % "\n".join(ng_sub_data_list)
        else:
            ng_sub_filter = ''

        if proxy_data["proxydir"][-1] != '/':
            proxy_dir = proxy_data["proxydir"] + "/"
        else:
            proxy_dir = proxy_data["proxydir"]

        if proxy_data["proxysite"][-1] != '/':
            proxy_site = proxy_data["proxysite"] + "/"
        else:
            proxy_site = proxy_data["proxysite"]

        # 构造反向代理
        if proxy_data["cache"] == 1:
            ng_proxy_cache = ng_proxy % (
                proxy_dir, proxy_dir, proxy_site, proxy_data["todomain"], ng_sub_filter, ng_cache, proxy_dir)
        else:
            ng_proxy_cache = ng_proxy % (
                proxy_dir, proxy_dir, proxy_site, proxy_data["todomain"], ng_sub_filter, no_cache, proxy_dir)

        write_file(ng_proxy_file, ng_proxy_cache)
        if webserver() == "nginx" and check_server_config() is not None:
            import public
            public.print_log(check_server_config())
            os.remove(ng_proxy_file)
            return "配置添加失败"

    def set_apache_proxy(self, proxy_data: dict):
        proxy_name_md5 = self._calc_proxy_name_md5(proxy_data["proxyname"])
        ap_proxy_file = "%s/vhost/apache/proxy/%s/%s_%s.conf" % (
            self.panel_path, proxy_data["sitename"], proxy_name_md5,  proxy_data["sitename"])
        if proxy_data["type"] == 0:
            if os.path.isfile(ap_proxy_file):
                os.remove(ap_proxy_file)
                return

        ap_proxy = '''#PROXY-START%s
<IfModule mod_proxy.c>
    ProxyRequests Off
    SSLProxyEngine on
    ProxyPass %s %s/
    ProxyPassReverse %s %s/
</IfModule>
#PROXY-END%s''' % (proxy_data["proxydir"], proxy_data["proxydir"], proxy_data["proxysite"],
                   proxy_data["proxydir"],proxy_data["proxysite"], proxy_data["proxydir"])
        write_file(ap_proxy_file, ap_proxy)

    @staticmethod
    def _random_string() -> str:
        from uuid import uuid4
        return "bt" + uuid4().hex[:6]

    @staticmethod
    def _calc_proxy_name_md5(data: str) -> str:
        m = md5()
        m.update(data.encode("utf-8"))
        return m.hexdigest()

    def create_proxy(self, get) -> Optional[str]:
        proxy_data = self.check_args(get, is_modify=False)
        if isinstance(proxy_data, str):
            return proxy_data
        if webserver() == "nginx":
            error_msg = self.check_location(proxy_data["sitename"], proxy_data["proxydir"])
            if error_msg:
                return error_msg

        error_msg = self.set_nginx_proxy_include(proxy_data["sitename"])
        if webserver() == "nginx" and error_msg:
            return error_msg
        error_msg = self.set_apache_proxy_include(proxy_data["sitename"])
        if webserver() == "apache" and error_msg:
            return error_msg
        error_msg = self.set_nginx_proxy(proxy_data)
        if webserver() == "nginx" and error_msg:
            return error_msg
        self.set_apache_proxy(proxy_data)
        self.config.append(proxy_data)
        self.save_config()
        service_reload()

    def modify_proxy(self, get) -> Optional[str]:
        proxy_data = self.check_args(get, is_modify=True)
        if isinstance(proxy_data, str):
            return proxy_data
        idx = None

        for index, i in enumerate(self.config):
            if i["proxyname"] == proxy_data["proxyname"] and i["sitename"] == proxy_data["sitename"]:
                idx = index
                break
        if idx is None:
            return "未找到该名称的反向代理配置"

        if webserver() == "nginx" and proxy_data["proxydir"] != self.config[idx]["proxydir"]:
            error_msg = self.check_location(proxy_data["sitename"], proxy_data["proxydir"])
            if error_msg:
                return error_msg

        error_msg = self.set_nginx_proxy_include(proxy_data["sitename"])
        if webserver() == "nginx" and error_msg:
            return error_msg
        error_msg = self.set_apache_proxy_include(proxy_data["sitename"])
        if webserver() == "apache" and error_msg:
            return error_msg
        error_msg = self.set_nginx_proxy(proxy_data)
        if webserver() == "nginx" and error_msg:
            return error_msg
        self.set_apache_proxy(proxy_data)
        self.config[idx] = proxy_data
        self.save_config()
        service_reload()

    def remove_proxy(self, site_name, proxy_name, multiple=False) -> Optional[str]:
        idx = None
        site_other = False
        for index, i in enumerate(self.config):
            if i["proxyname"] == proxy_name and i["sitename"] == site_name:
                idx = index
            if i["sitename"] == site_name and i["proxyname"] != proxy_name:
                site_other = True

        if idx is None:
            return "未找到该名称的反向代理配置"

        proxy_name_md5 = self._calc_proxy_name_md5(proxy_name)
        ng_proxy_file = "%s/vhost/nginx/proxy/%s/%s_%s.conf" % (
            self.panel_path, site_name, proxy_name_md5, site_name)
        ap_proxy_file = "%s/vhost/apache/proxy/%s/%s_%s.conf" % (
            self.panel_path, site_name, proxy_name_md5, site_name)
        if os.path.isfile(ap_proxy_file):
            os.remove(ap_proxy_file)

        if os.path.isfile(ng_proxy_file):
            os.remove(ng_proxy_file)
        del self.config[idx]
        self.save_config()
        if not site_other:
            self.un_set_apache_proxy_include(site_name)
            self.un_set_nginx_proxy_include(site_name)
        if not multiple:
            service_reload()

    def get_proxy_list(self, get) -> Union[str, List[Dict[str, Any]]]:
        try:
            site_name = get.sitename.strip()
        except (AttributeError, ValueError, TypeError):
            return "参数错误"
        proxy_list = []
        web_server = webserver()
        for conf in self.config:
            if conf["sitename"] != site_name:
                continue
            md5_name = self._calc_proxy_name_md5(conf['proxyname'])
            conf["proxy_conf_file"] = "%s/vhost/%s/proxy/%s/%s_%s.conf" % (
                self.panel_path, web_server, site_name, md5_name, site_name)
            proxy_list.append(conf)
        return proxy_list

    def remove_site_proxy_info(self, site_name):
        idx_list = []
        for index, i in enumerate(self.config):
            if i["sitename"] == site_name:
                idx_list.append(index)

        for idx in idx_list[::-1]:
            del self.config[idx]

        self.save_config()

        ng_proxy_dir = "%s/vhost/nginx/proxy/%s" % (self.panel_path, site_name)
        ap_proxy_dir = "%s/vhost/apache/proxy/%s" % (self.panel_path, site_name)

        if os.path.isdir(ng_proxy_dir):
            shutil.rmtree(ng_proxy_dir)

        if os.path.isdir(ap_proxy_dir):
            shutil.rmtree(ap_proxy_dir)


class Proxy(object):

    def __init__(self, config_prefix=""):
        self.config_prefix = config_prefix
        self._p = RealProxy(self.config_prefix)

    def create_proxy(self, get):
        msg = self._p.create_proxy(get)
        if msg:
            return json_response(status=False, msg=msg)
        return json_response(status=True, msg="添加成功")

    def modify_proxy(self, get):
        msg = self._p.modify_proxy(get)
        if msg:
            return json_response(status=False, msg=msg)
        return json_response(status=True, msg="修改成功")

    def remove_proxy(self, get):
        try:
            site_name = get.sitename.strip()
            proxy_name = get.proxyname.strip()
        except:
            return json_response(status=False, msg="参数错误")
        msg = self._p.remove_proxy(site_name, proxy_name)
        if msg:
            return json_response(status=False, msg=msg)
        return json_response(status=True, msg="删除成功")

    def get_proxy_list(self, get):
        data = self._p.get_proxy_list(get)
        if isinstance(data, str):
            return json_response(status=False, msg=data)
        else:
            return json_response(status=True, data=data)