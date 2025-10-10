#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Nginx配置目录
NGINX_CONF_DIR = "/www/server/panel/vhost/nginx"

# 数据库配置
DB_PATH = "load_balancer.db"

# 日志配置
LOG_FILE = "load_balancer.log"
LOG_LEVEL = "INFO"

# 日志格式定义
LOG_FORMAT = '''$time_local\t$remote_addr\t$request_method\t$upstream_addr\t$upstream_response_time\t$body_bytes_sent\t$bytes_sent\t$status\t$request_uri'''

# 负载均衡方法
LOAD_BALANCE_METHODS = {
    "sticky_cookie": "基于Cookie的会话保持",
    "ip_hash": "基于IP的会话保持",
    "least_conn": "最少连接数",
    "round_robin": "轮询"
}

# 默认配置
DEFAULT_CONFIG = {
    "http": {
        "port": 80,
        "load_balance_method": "sticky_cookie",
        "cookie_expires": "1h",
        "cookie_domain": ".example.com",
        "cookie_path": "/",
        "proxy_next_upstream": "error timeout http_500 http_502 http_503 http_504",
        "proxy_next_upstream_tries": 3,
        "proxy_next_upstream_timeout": 10
    },
    "tcp": {
        "proxy_connect_timeout": "1s",
        "proxy_timeout": "3s"
    }
}

# 节点检查配置
NODE_CHECK = {
    "timeout": 5,  # 连接超时时间（秒）
    "retry_times": 3,  # 重试次数
    "retry_interval": 1  # 重试间隔（秒）
} 