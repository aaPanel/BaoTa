import os
import re
from typing import Tuple

import public
from .base import BaseProjectCommon


class LimitNet(BaseProjectCommon):

    def get_limit_net(self, get):
        if public.get_webserver() != 'nginx':
            return public.returnMsg(False, 'SITE_NETLIMIT_ERR')
        try:
            site_id = int(get.site_id)
        except (AttributeError, TypeError, ValueError):
            return public.returnMsg(False, "参数错误")

        if self.config_prefix is None:
            return public.returnMsg(False, "不支持的网站类型")

        # 取配置文件
        site_name = public.M('sites').where("id=?", (site_id,)).getField('name')
        filename = "{}/vhost/nginx/{}{}.conf".format(self.setup_path, self.config_prefix, site_name)
        conf = public.readFile(filename)
        if not isinstance(conf, str):
            return public.returnMsg(False, "配置文件读取错误")

        # 站点总并发
        data = {
            'perserver': 0,
            'perip': 0,
            'limit_rate': 0,
        }

        rep_per_server = re.compile(r"(?P<prefix>.*)limit_conn +perserver +(?P<target>\d+) *; *", re.M)
        tmp_res = rep_per_server.search(conf)
        if tmp_res is not None and tmp_res.group("prefix").find("#") == -1:  # 有且不是注释
            data['perserver'] = int(tmp_res.group("target"))

        # IP并发限制
        rep_per_ip = re.compile(r"(?P<prefix>.*)limit_conn +perip +(?P<target>\d+) *; *", re.M)
        tmp_res = rep_per_ip.search(conf)
        if tmp_res is not None and tmp_res.group("prefix").find("#") == -1:  # 有且不是注释
            data['perip'] = int(tmp_res.group("target"))

        # 请求并发限制
        rep_limit_rate = re.compile(r"(?P<prefix>.*)limit_rate +(?P<target>\d+)\w+ *; *", re.M)
        tmp_res = rep_limit_rate.search(conf)
        if tmp_res is not None and tmp_res.group("prefix").find("#") == -1:  # 有且不是注释
            data['limit_rate'] = int(tmp_res.group("target"))

        self._show_limit_net(data)
        return data

    @staticmethod
    def _show_limit_net(data):
        values = [
            [300, 25, 512],
            [200, 10, 1024],
            [50, 3, 2048],
            [500, 10, 2048],
            [400, 15, 1024],
            [60, 10, 512],
            [150, 4, 1024],
        ]
        for i, c in enumerate(values):
            if data["perserver"] == c[0] and data["perip"] == c[1] and data["limit_rate"] == c[2]:
                data["value"] = i + 1
                break
        else:
            data["value"] = 0

    @staticmethod
    def _set_nginx_conf_limit() -> Tuple[bool, str]:
        # 设置共享内存
        nginx_conf_file = "/www/server/nginx/conf/nginx.conf"
        if not os.path.exists(nginx_conf_file):
            return False, "nginx配置文件丢失"
        nginx_conf = public.readFile(nginx_conf_file)
        rep_perip = re.compile(r"\s+limit_conn_zone +\$binary_remote_addr +zone=perip:10m;", re.M)
        rep_per_server = re.compile(r"\s+limit_conn_zone +\$server_name +zone=perserver:10m;", re.M)
        perip_res = rep_perip.search(nginx_conf)
        per_serve_res = rep_per_server.search(nginx_conf)
        if perip_res and per_serve_res:
            return True, ""
        elif perip_res or per_serve_res:
            tmp_res = perip_res or per_serve_res
            new_conf = nginx_conf[:tmp_res.start()] + (
                "\n\t\tlimit_conn_zone $binary_remote_addr zone=perip:10m;"
                "\n\t\tlimit_conn_zone $server_name zone=perserver:10m;"
            ) + nginx_conf[tmp_res.end():]
        else:
            # 通过检查第一个server的位置
            rep_first_server = re.compile(r"http\s*\{(.*\n)*\s*server\s*\{")
            tmp_res = rep_first_server.search(nginx_conf)
            if tmp_res:
                old_http_conf = tmp_res.group()
                # 在第一个server项前添加
                server_idx = old_http_conf.rfind("server")
                new_http_conf = old_http_conf[:server_idx] + (
                    "\n\t\tlimit_conn_zone $binary_remote_addr zone=perip:10m;"
                    "\n\t\tlimit_conn_zone $server_name zone=perserver:10m;\n"
                ) + old_http_conf[server_idx:]
                new_conf = rep_first_server.sub(new_http_conf, nginx_conf, 1)
            else:
                # 在没有配置其他server项目时，通过检查include server项目检查
                # 通检查 include /www/server/panel/vhost/nginx/*.conf; 位置
                rep_include = re.compile(r"http\s*\{(.*\n)*\s*include +/www/server/panel/vhost/nginx/\*\.conf;")
                tmp_res = rep_include.search(nginx_conf)
                if not tmp_res:
                    return False, "全局配置缓存配置失败"
                old_http_conf = tmp_res.group()

                include_idx = old_http_conf.rfind("include ")
                new_http_conf = old_http_conf[:include_idx] + (
                    "\n\t\tlimit_conn_zone $binary_remote_addr zone=perip:10m;"
                    "\n\t\tlimit_conn_zone $server_name zone=perserver:10m;\n"
                ) + old_http_conf[include_idx:]
                new_conf = rep_first_server.sub(new_http_conf, nginx_conf, 1)

        public.writeFile(nginx_conf_file, new_conf)
        if public.checkWebConfig() is not True:  # 检测失败，无法添加
            public.writeFile(nginx_conf_file, nginx_conf)
            return False, "全局配置缓存配置失败"
        return True, ""

    # 设置流量限制
    def set_limit_net(self, get):
        if public.get_webserver() != 'nginx':
            return public.returnMsg(False, 'SITE_NETLIMIT_ERR')
        try:
            site_id = int(get.site_id)
            per_server = int(get.perserver)
            perip = int(get.perip)
            limit_rate = int(get.limit_rate)
        except (AttributeError, TypeError, ValueError):
            return public.returnMsg(False, "参数错误")

        if per_server < 1 or perip < 1 or limit_rate < 1:
            return public.returnMsg(False, '并发限制，IP限制，流量限制必需大于0')

        # 取配置文件
        site_info = public.M('sites').where("id=?", (site_id,)).find()
        if not isinstance(site_info, dict):
            return public.returnMsg(False, "站点信息查询错误")
        else:
            site_name = site_info["name"]
        filename = "{}/vhost/nginx/{}{}.conf".format(self.setup_path, self.config_prefix, site_name)
        site_conf: str = public.readFile(filename)
        if not isinstance(site_conf, str):
            return public.returnMsg(False, "配置文件读取错误")

        flag, msg = self._set_nginx_conf_limit()
        if not flag:
            return public.returnMsg(False, msg)

        per_server_str = '    limit_conn perserver {};'.format(per_server)
        perip_str = '    limit_conn perip {};'.format(perip)
        limit_rate_str = '    limit_rate {}k;'.format(limit_rate)

        # 请求并发限制
        new_conf = site_conf
        ssl_end_res = re.search(r"#error_page 404/404.html;[^\n]*\n", new_conf)
        if ssl_end_res is None:
            return public.returnMsg(False, "未定位到SSL的相关配置，添加失败")
        ssl_end_idx = ssl_end_res.end()
        rep_limit_rate = re.compile(r"(.*)limit_rate +(\d+)\w+ *; *", re.M)
        tmp_res = rep_limit_rate.search(new_conf)
        if tmp_res is not None :
            new_conf = rep_limit_rate.sub(limit_rate_str, new_conf)
        else:
            new_conf = new_conf[:ssl_end_idx] + limit_rate_str + "\n" + new_conf[ssl_end_idx:]

        # IP并发限制
        rep_per_ip = re.compile(r"(.*)limit_conn +perip +(\d+) *; *", re.M)
        tmp_res = rep_per_ip.search(new_conf)
        if tmp_res is not None:
            new_conf = rep_per_ip.sub(perip_str, new_conf)
        else:
            new_conf = new_conf[:ssl_end_idx] + perip_str + "\n" + new_conf[ssl_end_idx:]

        rep_per_server = re.compile(r"(.*)limit_conn +perserver +(\d+) *; *", re.M)
        tmp_res = rep_per_server.search(site_conf)
        if tmp_res is not None:
            new_conf = rep_per_server.sub(per_server_str, new_conf)
        else:
            new_conf = new_conf[:ssl_end_idx] + per_server_str + "\n" + new_conf[ssl_end_idx:]

        public.writeFile(filename, new_conf)
        is_error = public.checkWebConfig()
        if is_error is not True:
            public.writeFile(filename, site_conf)
            return public.returnMsg(False, 'ERROR:<br><a style="color:red;">' + is_error.replace("\n", '<br>') + '</a>')

        public.serviceReload()
        public.WriteLog('TYPE_SITE', 'SITE_NETLIMIT_OPEN_SUCCESS', (site_name,))
        return public.returnMsg(True, 'SET_SUCCESS')

    # 关闭流量限制
    def close_limit_net(self, get):
        if public.get_webserver() != 'nginx':
            return public.returnMsg(False, 'SITE_NETLIMIT_ERR')
        if self.config_prefix is None:
            return public.returnMsg(False, "不支持的网站类型")
        try:
            site_id = int(get.site_id)
        except (AttributeError, TypeError, ValueError):
            return public.returnMsg(False, "参数错误")

        # 取回配置文件
        site_info = public.M('sites').where("id=?", (site_id,)).find()
        if not isinstance(site_info, dict):
            return public.returnMsg(False, "站点信息查询错误")
        else:
            site_name = site_info["name"]
        filename = "{}/vhost/nginx/{}{}.conf".format(self.setup_path, self.config_prefix, site_name)
        site_conf = public.readFile(filename)
        if not isinstance(site_conf, str):
            return public.returnMsg(False, "配置文件读取错误")

        # 清理总并发
        rep_limit_rate = re.compile(r"(.*)limit_rate +(\d+)\w+ *; *\n?", re.M)
        rep_per_ip = re.compile(r"(.*)limit_conn +perip +(\d+) *; *\n?", re.M)
        rep_per_server = re.compile(r"(.*)limit_conn +perserver +(\d+) *; *\n?", re.M)

        new_conf = site_conf
        new_conf = rep_limit_rate.sub("", new_conf, 1)
        new_conf = rep_per_ip.sub("", new_conf, 1)
        new_conf = rep_per_server.sub("", new_conf, 1)

        public.writeFile(filename, new_conf)
        is_error = public.checkWebConfig()
        if is_error is not True:
            public.writeFile(filename, site_conf)
            return public.returnMsg(False, 'ERROR:<br><a style="color:red;">' + is_error.replace("\n", '<br>') + '</a>')
        public.serviceReload()
        public.WriteLog('TYPE_SITE', 'SITE_NETLIMIT_CLOSE_SUCCESS', (site_name,))
        return public.returnMsg(True, 'SITE_NETLIMIT_CLOSE_SUCCESS')
