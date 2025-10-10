import json
import os
import re
from typing import Optional, Tuple
from .util import listen_ipv6, write_file, read_file, service_reload


def check_default():
    vhost_path = "/www/server/panel/vhost"
    nginx = vhost_path + '/nginx'
    httpd = vhost_path + '/apache'
    httpd_default = '''<VirtualHost *:80>
    ServerAdmin webmaster@example.com
    DocumentRoot "/www/server/apache/htdocs"
    ServerName bt.default.com
    <Directory "/www/server/apache/htdocs">
        SetOutputFilter DEFLATE
        Options FollowSymLinks
        AllowOverride All
        Order allow,deny
        Allow from all
        DirectoryIndex index.html
    </Directory>
</VirtualHost>
'''

    listen_ipv6_str = ''
    if listen_ipv6():
        listen_ipv6_str = "\n    listen [::]:80;"

    nginx_default = '''server
{
    listen 80;%s
    server_name _;
    index index.html;
    root /www/server/nginx/html;
}''' % listen_ipv6_str

    if not os.path.exists(httpd + '/0.default.conf') and not os.path.exists(httpd + '/default.conf'):
        write_file(httpd + '/0.default.conf', httpd_default)
    if not os.path.exists(nginx + '/0.default.conf') and not os.path.exists(nginx + '/default.conf'):
        write_file(nginx + '/0.default.conf', nginx_default)


def get_default_site() -> Tuple[Optional[str], Optional[str]]:
    panel_path = "/www/server/panel"

    old_ds_file = panel_path + "/data/defaultSite.pl"
    new_ds_file = panel_path + "/data/mod_default_site.pl"
    if os.path.exists(old_ds_file) and not os.path.exists(new_ds_file):
        write_file(new_ds_file, json.dumps({
            "name": read_file(old_ds_file).strip(),
            "prefix": ''
        }))

    res = read_file(new_ds_file)
    if not isinstance(res, str):
        return None, None
    data = json.loads(res)
    return data["name"], data["prefix"]


# site_name 传递None的时候，表示将默认站点设置给关闭
# prefix 表示配置文件前缀， 如 "net_", 默认为空字符串
# domain 站点的域名 如： "www.sss.com:8456"
def set_default_site(site_name: Optional[str], prefix="", domain: str = None) -> Optional[str]:
    # 清理旧的
    old_default_name, old_prefix = get_default_site()
    panel_path = "/www/server/panel"
    default_site_save = panel_path + '/data/mod_default_site.pl'
    if old_default_name:
        ng_conf_file = os.path.join(panel_path, "vhost/nginx/{}{}.conf".format(old_prefix, old_default_name))
        old_conf = read_file(ng_conf_file)
        if isinstance(old_conf, str):
            rep_listen_ds = re.compile(r"listen\s+.*default_server.*;")
            new_conf_list = []
            start_idx = 0
            for tmp_res in rep_listen_ds.finditer(old_conf):
                new_conf_list.append(old_conf[start_idx: tmp_res.start()])
                new_conf_list.append(tmp_res.group().replace("default_server", ""))
                start_idx = tmp_res.end()

            new_conf_list.append(old_conf[start_idx:])

            write_file(ng_conf_file, "".join(new_conf_list))

        path = '/www/server/apache/htdocs/.htaccess'
        if os.path.exists(path):
            os.remove(path)

    if site_name is None:
        write_file(default_site_save, json.dumps({
            "name": None,
            "prefix": None
        }))
        service_reload()
        return

    # 处理新的
    ap_path = '/www/server/apache/htdocs'
    if os.path.exists(ap_path):
        conf = '''<IfModule mod_rewrite.c>
  RewriteEngine on
  RewriteCond %{{HTTP_HOST}} !^127.0.0.1 [NC]
  RewriteRule (.*) http://{}/$1 [L]
</IfModule>'''.format(domain)

        write_file(ap_path + '/.htaccess', conf)

    ng_conf_file = os.path.join(panel_path, "vhost/nginx/{}{}.conf".format(prefix, site_name))
    ng_conf = read_file(ng_conf_file)
    if isinstance(ng_conf, str):
        rep_listen = re.compile(r"listen[^;]*;")
        new_conf_list = []

        start_idx = 0
        for tmp_res in rep_listen.finditer(ng_conf):
            new_conf_list.append(ng_conf[start_idx: tmp_res.start()])
            print(tmp_res.group())
            if tmp_res.group().find("default_server") == -1:
                new_conf_list.append(tmp_res.group()[:-1] + " default_server;")
            else:
                new_conf_list.append(tmp_res.group())
            start_idx = tmp_res.end()

        new_conf_list.append(ng_conf[start_idx:])

        write_file(ng_conf_file, "".join(new_conf_list))

    write_file(default_site_save, json.dumps({
        "name": site_name,
        "prefix": prefix
    }))

    service_reload()
    return
