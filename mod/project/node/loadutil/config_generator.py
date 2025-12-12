#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import shutil
import sys
from typing import List, Dict

from .config import NGINX_CONF_DIR
from .nginx_utils import NginxUtils
from mod.project.node.dbutil import LoadSite, HttpNode, TcpNode, ServerNodeDB
from typing import Union

from ..nodeutil import ServerNode

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public


class NginxConfigGenerator:
    def __init__(self):
        self.nginx_conf_dir = NGINX_CONF_DIR
        self.nginx_tcp_conf_dir = os.path.join(self.nginx_conf_dir, "tcp")
        self.nginx_proxy_conf_dir = os.path.join(self.nginx_conf_dir, "proxy")

    def generate_http_config(self, load: LoadSite, nodes: List[HttpNode]) -> Dict[str, str]:
        """生成HTTP负载均衡配置"""
        # 生成upstream配置
        upstream_conf = self._generate_http_upstream_config(load, nodes)

        # 生成server配置
        server_conf = self._generate_server_config(load.site_name)

        # 生成proxy配置
        proxy_conf = self._generate_proxy_config(load, nodes)

        return {
            'upstream': upstream_conf,
            'server': server_conf,
            'proxy': proxy_conf
        }

    @staticmethod
    def _generate_http_upstream_config(load: LoadSite, nodes: List[HttpNode]) -> str:
        """生成upstream配置"""
        config = "upstream {} {{\n".format(load.name)

        # 添加负载均衡方法
        if load.http_config["http_alg"] == "sticky_cookie":
            config += "    sticky name=bt_load_srv_id expires=12h;\n"
        elif load.http_config["http_alg"] == "ip_hash":
            config += "    ip_hash;\n"
        elif load.http_config["http_alg"] == "least_conn":
            config += "    least_conn;\n"

        can_use_backup = not load.http_config["http_alg"] in ["hash", "ip_hash", "random", "sticky_cookie"]

        srv_db = ServerNodeDB()
        # 添加节点
        for node in nodes:
            server = "{}:{}".format(node.node_site_name, node.port)
            if srv_db.is_local_node(node.node_id):
                server = "127.0.0.1:" + str(node.port)
            elif load.site_name == node.node_site_name:
                server_ip = ServerNode.get_node_ip(node.node_id)
                if server_ip:
                    server = server_ip + ":" + str(node.port)
            backup_str = " backup" if node.node_status == "backup" and can_use_backup else ""
            backup_str = " down" if node.node_status == "down" else backup_str
            config += "    server {} weight={} max_fails={} fail_timeout={} {};\n".format(
                server, node.weight, node.max_fail,
                node.fail_timeout, backup_str,
            )
        config += "}\n"
        return config

    @staticmethod
    def _generate_server_config(site_name: str) -> str:
        """生成server配置"""
        site_ng_file = "/www/server/panel/vhost/nginx/{}.conf".format(site_name)
        ng_conf = public.readFile(site_ng_file)
        rep = re.compile(r"include.*/vhost/nginx/proxy/.*\*.conf;")
        if not rep.search(ng_conf):
            ng_proxy_file_str = "/www/server/panel/vhost/nginx/proxy/{}/*.conf;".format(site_name)
            replace_str = "\n\t#引用反向代理规则，注释后配置的反向代理将无效\n\tinclude {}\n\n\tinclude enable-php-".format(
                ng_proxy_file_str)
            ng_conf = ng_conf.replace("include enable-php-", replace_str)
        ng_conf = re.sub(r"location .{3,10}\((gif|js)\|[^{]*[^}]*}\n", "", ng_conf)
        return ng_conf

    @staticmethod
    def _generate_proxy_config(load: LoadSite, nodes: List[HttpNode]) -> str:
        """生成proxy配置"""
        is_https = False
        for node in nodes:
            if node.port in (443, 8443):
                is_https = True
                break

        if not os.path.exists("/www/wwwlogs/load_balancing/logs/" + load.site_name):
            os.makedirs("/www/wwwlogs/load_balancing/logs/" + load.site_name)

        proxy_cache = ""
        if load.http_config.get("proxy_cache_status", False):
            cache_suffix = load.http_config.get("cache_suffix", "")
            if cache_suffix:
                parameter = r".*\.(" + "|".join([re.escape(i) for i in cache_suffix.split(",")]) + ")$"
            else:
                parameter = None
            cache_time = load.http_config.get("cache_time", "1d")
            if not re.match(r"^[0-9]+([smhd])$", cache_time):
                cache_time = "1d"
            if parameter:
                proxy_cache = """
    add_header X-Cache $upstream_cache_status;
    location ~ {parameter} {{
        proxy_pass {is_https}://{name};
        proxy_cache cache_one;
        proxy_cache_key $host$uri$is_args$args;
        proxy_ignore_headers Set-Cookie Cache-Control expires X-Accel-Expires;
        proxy_cache_valid 200 304 301 302 {cache_time};
        proxy_cache_valid 404 {cache_time};
    }}
""".format(is_https="https" if is_https else "http",
           name=load.name,
           cache_time=cache_time,
           parameter=parameter)

        config = """location / {{
    proxy_pass {is_https}://{name};
    
    # 基本代理设置
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    # 禁用缓存
    proxy_cache off;
    # 错误处理
    proxy_next_upstream {next_upstream};{proxy_cache}
}}

# 使用详细日志格式
access_log /www/wwwlogs/load_balancing/logs/{site_name}/proxy_access.log load_balancer_detailed;
""".format(
            site_name=load.site_name,
            name=load.name,
            is_https="https" if is_https else "http",
            next_upstream=load.http_config["proxy_next_upstream"],
            proxy_cache=proxy_cache,
        )
        return config

    @staticmethod
    def generate_tcp_config(load: LoadSite, nodes: List[TcpNode]) -> str:
        """生成TCP配置"""
        tcp_upstream = ""
        for node in nodes:
            backup_str = " backup" if node.node_status == "backup" else ""
            backup_str = " down" if node.node_status == "down" else backup_str
            tcp_upstream += "    server {}:{} weight={} max_fails={} fail_timeout={}{};\n".format(
                node.host, node.port, node.weight, node.max_fail, node.fail_timeout, backup_str
            )
        os.makedirs("/www/wwwlogs/load_balancing/tcp_logs/" + load.name, exist_ok=True)
        tcp_config = load.tcp_config
        config = """upstream %s {
%s
}

server {
    listen %s:%d%s;
    proxy_connect_timeout %ds;
    proxy_timeout %ds;
    proxy_pass %s;
    access_log /www/wwwlogs/load_balancing/tcp_logs/%s/tcp_load.log load_balancer_tcp_detailed;
}
""" % (load.name, tcp_upstream, tcp_config["host"], tcp_config["port"], "" if tcp_config["type"] == "tcp" else " udp",
       tcp_config["proxy_connect_timeout"], tcp_config["proxy_timeout"], load.name, load.name)
        return config

    def save_configs(self, load: LoadSite, nodes: List[Union[TcpNode, HttpNode]]) -> str:
        """保存配置文件"""
        if load.site_type == "http":
            NginxUtils.set_load_balancer_log_format()
            # 保存upstream配置
            configs = self.generate_http_config(load, nodes)
            site_name = load.site_name
            upstream_back, server_back, proxy_back = "", "", ""
            upstream_path = os.path.join(self.nginx_conf_dir, "upstream_{}.conf".format(site_name))
            if os.path.exists(upstream_path):
                upstream_back = public.readFile(upstream_path)
            public.writeFile(upstream_path, configs['upstream'])

            # 保存server配置
            server_path = os.path.join(self.nginx_conf_dir, "{}.conf".format(site_name))
            if os.path.exists(server_path):
                server_back = public.readFile(server_path)
            public.writeFile(server_path, configs['server'])

            # 创建并保存proxy配置
            proxy_dir = os.path.join(self.nginx_proxy_conf_dir, site_name)
            os.makedirs(proxy_dir, exist_ok=True)
            proxy_path = os.path.join(proxy_dir, "load_proxy_{}.conf".format(site_name))
            if os.path.exists(proxy_path):
                proxy_back = public.readFile(proxy_path)
            public.writeFile(proxy_path, configs['proxy'])

            flag, err = NginxUtils.check_config()
            if not flag:
                public.writeFile(upstream_path, upstream_back)
                public.writeFile(server_path, server_back)
                public.writeFile(proxy_path, proxy_back)
                return err
            else:
                NginxUtils.reload_nginx()

        elif load.site_type == "tcp":
            NginxUtils.set_tcp_load_balancer_log_format()
            # 保存TCP配置
            tcp_dir = self.nginx_tcp_conf_dir
            os.makedirs(tcp_dir, exist_ok=True)

            site_name = load.name
            conf = self.generate_tcp_config(load, nodes)
            stream_back = ""
            stream_path = os.path.join(tcp_dir, "{}.conf".format(site_name))
            if os.path.exists(stream_path):
                stream_back = public.readFile(stream_path)
            public.writeFile(stream_path, conf)
            flag, err = NginxUtils.check_config()
            if not flag:
                public.writeFile(stream_path, stream_back)
                return err
            else:
                NginxUtils.reload_nginx()

    def set_http_proxy_next_upstream(self, site_name: str, proxy_next_upstream: str) -> str:
        proxy_path = os.path.join(self.nginx_proxy_conf_dir, site_name, "load_proxy_{}.conf".format(site_name))
        proxy_back = ""
        if os.path.exists(proxy_path):
            proxy_back = public.readFile(proxy_path)

        rep = re.compile(r'proxy_next_upstream\s+[^;]*;')
        proxy_conf = re.sub(rep, 'proxy_next_upstream {};'.format(proxy_next_upstream), proxy_back)
        if proxy_conf != proxy_back:
            public.writeFile(proxy_path, proxy_conf)
            flag, err = NginxUtils.check_config()
            if not flag:
                public.writeFile(proxy_path, proxy_back)
                return err
            else:
                NginxUtils.reload_nginx()
        return ""

    def set_http_proxy_cache(self, site_name: str, load: LoadSite, nodes: List[Union[TcpNode, HttpNode]]) -> str:
        proxy_path = os.path.join(self.nginx_proxy_conf_dir, site_name, "load_proxy_{}.conf".format(site_name))
        proxy_back = ""
        if os.path.exists(proxy_path):
            proxy_back = public.readFile(proxy_path)

        proxy_conf = self._generate_proxy_config(load, nodes)
        if proxy_conf != proxy_back:
            public.writeFile(proxy_path, proxy_conf)
            flag, err = NginxUtils.check_config()
            if not flag:
                public.writeFile(proxy_path, proxy_back)
                return err
            else:
                NginxUtils.reload_nginx()
        return ""


    def delete_node_conf(self, load: LoadSite, mutil=False):
        if load.site_type == "http":
            site_name = load.site_name
            upstream_path = os.path.join(self.nginx_conf_dir, "upstream_{}.conf".format(site_name))
            if os.path.exists(upstream_path):
                os.remove(upstream_path)
            proxy_path = os.path.join(self.nginx_proxy_conf_dir, site_name, "load_proxy_{}.conf".format(site_name))
            if os.path.exists(proxy_path):
                os.remove(proxy_path)

            log_dir = os.path.join("/www/wwwlogs/load_balancing/logs/", site_name)
            if os.path.exists(log_dir):
                shutil.rmtree(log_dir)

            log_cache_dir = os.path.join("/www/wwwlogs/load_balancing/cache/", site_name)
            if os.path.exists(log_cache_dir):
                shutil.rmtree(log_cache_dir)
        else:
            site_name = load.name
            tcp_conf = os.path.join(self.nginx_tcp_conf_dir, "{}.conf".format(site_name))
            if os.path.exists(tcp_conf):
                os.remove(tcp_conf)

            log_dir = os.path.join("/www/wwwlogs/load_balancing/tcp_logs/", site_name)
            if os.path.exists(log_dir):
                shutil.rmtree(log_dir)

            log_cache_dir = os.path.join("/www/wwwlogs/load_balancing/cache/", site_name)
            if os.path.exists(log_cache_dir):
                shutil.rmtree(log_cache_dir)
        if not mutil:
            NginxUtils.reload_nginx()
