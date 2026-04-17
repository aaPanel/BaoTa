import os
import sqlite3
import configparser
from typing import List, Dict


# 面板网站配置文件
def panel_configs() -> List[str]:
    vhost_dir = "/www/server/panel/vhost/nginx"

    panel_files = []
    ret = []
    for file in panel_files:
        file_path = "{}/{}".format(vhost_dir, file)
        if os.path.exists(file_path):
            ret.append(file_path)

    try:
        db_file = "/www/server/panel/data/db/site.db"
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name,project_type FROM sites")
            for row in cursor.fetchall():
                name, project_type = row[0], row[1].lower()
                config_prefix = project_type + "_"
                if project_type in ("php", "proxy", "wp2"):
                    config_prefix = ""
                file_path = "{}/{}{}.conf".format(vhost_dir, config_prefix, name)
                if os.path.exists(file_path):
                    ret.append(file_path)
    except Exception as e:
        print("Error:", e)

    try:
        db_file = "/www/server/panel/data/db/docker.db"
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM docker_sites")
            for row in cursor.fetchall():
                name = row[0]
                file_path = "{}/{}.conf".format(vhost_dir, name)
                if os.path.exists(file_path):
                    ret.append(file_path)
    except Exception as e:
        print("Error:", e)

    return ret

# 面板vhost http部分的共用配置文件
def panel_vhost_http_d_configs() -> List[str]:
    vhost_dir = "/www/server/panel/vhost/nginx"
    panel_files = [
        "0.btwaf_log_format.conf",
        "0.default.conf",
        "0.monitor_log_format.conf",
        "0.site_total_log_format.conf",
        "0.websocket.conf",
        "waf2monitor_data.conf",
        "load_balance_shared.conf",
        "tcp/load_balance_shared.conf",
        "speed.conf",
        "btwaf.conf",
        "0.fastcgi_cache.conf",
    ]
    ret = []
    for file in panel_files:
        file_path = os.path.join(vhost_dir, file)
        if os.path.isfile(file_path):
            ret.append(file_path)

    return ret

# nginx http部分共用配置文件
def panel_nginx_http_d_configs() -> List[str]:
    ret = []
    # proxy.conf
    proxy_file = "/www/server/nginx/conf/proxy.conf"
    if os.path.isfile(proxy_file):
        ret.append(proxy_file)

    return  ret

def panel_php_info_configs() -> Dict[str, str]:
    ret = {}
    php_dir = "/www/server/php"
    nginx_php_info_dir = "/www/server/nginx/conf"
    if not os.path.exists(php_dir):
        return ret

    for i in os.listdir(php_dir):
        php_ver = i
        php_fpm_ini = "{}/{}/etc/php-fpm.conf".format(php_dir, php_ver)
        if not os.path.exists(php_fpm_ini):
            continue
        nginx_php_info = "enable-php-{}.conf".format(php_ver)
        ini = configparser.ConfigParser()
        ini.read(php_fpm_ini, encoding="utf-8")
        sock_file = ini.get("www", "listen", fallback="")
        if sock_file and os.path.exists(sock_file):
            if not os.path.exists(os.path.join(nginx_php_info_dir, nginx_php_info)):
                os.makedirs(nginx_php_info_dir, 0o755, exist_ok=True)
                with open(os.path.join(nginx_php_info_dir, nginx_php_info), "w") as f:
                    f.write('''    location ~ [^/]\\.php(/|$)
    {{
        try_files $uri =404;
        fastcgi_pass  unix:/tmp/php-cgi-{}.sock;
        fastcgi_index index.php;
        include fastcgi.conf;
        include pathinfo.conf;
    }}
'''.format(php_ver))
            ret["unix:{}".format(sock_file)] = nginx_php_info

    return ret

