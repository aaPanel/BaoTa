# -*- coding: utf-8 -*-
import os.path
import sys
from typing import Tuple, Optional

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public


class NginxUtils:
    _BIN = "/www/server/nginx/sbin/nginx"
    _NGINX_HOST = public.get_vhost_path() + "/nginx"
    _LOG_FORMAT = '''# 负载均衡日志格式
log_format load_balancer_detailed '$time_local,$remote_addr,$host,$request_method,"$request_uri",'
                                '"$upstream_addr","$upstream_response_time","$upstream_bytes_received",'
                                '"$upstream_status","$upstream_cache_status",'
                                '$request_time,$body_bytes_sent,$bytes_sent,$status,"$http_user_agent",'
                                '"$http_referer",$http_x_forwarded_for,$http_x_real_ip';
'''
    _TCP_LOG_FORMAT = '''# 负载均衡tcp日志格式   
log_format load_balancer_tcp_detailed '$time_local,$remote_addr,$protocol,$status,$bytes_sent,$bytes_received,'
                                      '$session_time,"$upstream_addr","$upstream_bytes_sent","$upstream_bytes_received",'
                                      '"$upstream_connect_time"';
'''

    @staticmethod
    def check_config() -> Tuple[bool, str]:
        """检查Nginx配置是否正确"""
        data = public.checkWebConfig()
        if data is True:
            return True, ''
        return False, data

    @staticmethod
    def reload_nginx():
        """重载Nginx配置"""
        return public.serviceReload()

    @classmethod
    def nginx_exists(cls) -> bool:
        return os.path.exists(cls._BIN)

    @classmethod
    def has_sticky_module(cls) -> bool:
        out, _ = public.ExecShell("{} -V 2>&1 | grep nginx-sticky-module".format(cls._BIN))
        return True if out else False

    @classmethod
    def set_load_balancer_log_format(cls):
        log_format_file = "{}/0.load_balancer_log_format.conf".format(cls._NGINX_HOST)
        if not os.path.exists(log_format_file):
            public.writeFile(log_format_file, cls._LOG_FORMAT)

    @classmethod
    def set_tcp_load_balancer_log_format(cls):
        log_format_file = "{}/tcp/0.load_balancer_log_format.conf".format(cls._NGINX_HOST)
        if not os.path.exists(log_format_file):
            public.writeFile(log_format_file, cls._TCP_LOG_FORMAT)
