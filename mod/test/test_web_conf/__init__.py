import os
import sys
from unittest import TestCase

SITE_NAME_CASE = "aaa.test.com"
SITE_PATH = "/www/wwwroot/aaa.test.com"
SUB_SITE_PATH = SITE_PATH + "/test_run"
if not os.path.exists(SUB_SITE_PATH):
    os.makedirs(SUB_SITE_PATH)
VHOST_PATH = "/www/server/panel/vhost"
PREFIX = ""
NGINX_CONFIG_FILE = "{}/nginx/{}{}.conf".format(VHOST_PATH, PREFIX, SITE_NAME_CASE)
APACHE_CONFIG_FILE = "{}/apache/{}{}.conf".format(VHOST_PATH, PREFIX, SITE_NAME_CASE)
NGINX_CONFIG_CASE = """server
{
    listen 80;
    server_name aaa.test.com;
    index index.php index.html index.htm default.php default.html default.htm;
    root /www/wwwroot/aaa.test.com;
    #CERT-APPLY-CHECK--START
    # 用于SSL证书申请时的文件验证相关配置 -- 请勿删除
    include /www/server/panel/vhost/nginx/well-known/aaa.test.com.conf;
    #CERT-APPLY-CHECK--END

    #SSL-START SSL相关配置，请勿删除或修改下一行带注释的404规则
    #error_page 404/404.html;
    #SSL-END

    #ERROR-PAGE-START  错误页配置，可以注释、删除或修改
    #error_page 404 /404.html;
    #error_page 502 /502.html;
    #ERROR-PAGE-END

    #PHP-INFO-START  PHP引用配置，可以注释或修改
    include enable-php-00.conf;
    #PHP-INFO-END

    #REWRITE-START URL重写规则引用,修改后将导致面板设置的伪静态规则失效
    include /www/server/panel/vhost/rewrite/aaa.test.com.conf;
    #REWRITE-END

    #禁止访问的文件或目录
    location ~ ^/(\.user.ini|\.htaccess|\.git|\.env|\.svn|\.project|LICENSE|README.md)
    {
        return 404;
    }

    #一键申请SSL证书验证目录相关设置
    location ~ \.well-known{
        allow all;
    }

    #禁止在证书验证目录放入敏感文件
    if ( $uri ~ "^/\.well-known/.*\.(php|jsp|py|js|css|lua|ts|go|zip|tar\.gz|rar|7z|sql|bak)$" ) {
        return 403;
    }

    location ~ .*\.(gif|jpg|jpeg|png|bmp|swf)$
    {
        expires      30d;
        error_log /dev/null;
        access_log /dev/null;
    }

    location ~ .*\.(js|css)?$
    {
        expires      12h;
        error_log /dev/null;
        access_log /dev/null;
    }
    access_log /www/wwwlogs/aaa.test.com.log;
    error_log  /www/wwwlogs/aaa.test.com.error.log;
}"""

# access_log /www/wwwlogs/aaa.test.com.log;

APACHE_CONFIG_CASE = """<VirtualHost *:80>
    ServerAdmin webmaster@example.com
    DocumentRoot "/www/wwwroot/aaa.test.com"
    ServerName 630e5c70.aaa.test.com
    ServerAlias aaa.test.com
    #errorDocument 404 /404.html
    ErrorLog "/www/wwwlogs/aaa.test.com-error_log"
    CustomLog "/www/wwwlogs/aaa.test.com-access_log" combined

    #DENY FILES
     <Files ~ (\.user.ini|\.htaccess|\.git|\.env|\.svn|\.project|LICENSE|README.md)$>
       Order allow,deny
       Deny from all
    </Files>
    
    #PHP
    <FilesMatch \.php$>
            SetHandler "proxy:unix:/tmp/php-cgi-00.sock|fcgi://localhost"
    </FilesMatch>
    
    #PATH
    <Directory "/www/wwwroot/aaa.test.com">
        SetOutputFilter DEFLATE
        Options FollowSymLinks
        AllowOverride All
        Require all granted
        DirectoryIndex index.php index.html index.htm default.php default.html default.htm
    </Directory>
</VirtualHost>"""

APACHE_PATH = "/www/server/apache"
NGINX_PATH = "/www/server/nginx"


class WebBaseTestcase(TestCase):

    def __init__(self):
        super(WebBaseTestcase, self).__init__()
        if not os.path.isfile(NGINX_CONFIG_FILE):
            with open(NGINX_CONFIG_FILE, "w+") as f:
                f.write(NGINX_CONFIG_CASE)

        if not os.path.isfile(APACHE_CONFIG_FILE):
            with open(APACHE_CONFIG_FILE, "w+") as f:
                f.write(APACHE_CONFIG_CASE)

        self.site_name = SITE_NAME_CASE

    @staticmethod
    def reset_site_config():
        with open(NGINX_CONFIG_FILE, "w+") as f:
            f.write(NGINX_CONFIG_CASE)

        with open(APACHE_CONFIG_FILE, "w+") as f:
            f.write(APACHE_CONFIG_CASE)

    @staticmethod
    def change_env_to_apache():
        if "/www/server/panel/class" not in sys.path:
            sys.path.insert(0, "/www/server/panel/class")

        import public

        if os.path.exists(NGINX_PATH):
            public.ExecShell("/etc/init.d/nginx stop")
            os.rename(NGINX_PATH, NGINX_PATH+"_back")

        if os.path.exists(APACHE_PATH + "_back"):
            os.rename(APACHE_PATH + "_back", APACHE_PATH)

    @staticmethod
    def change_env_to_nginx():
        if "/www/server/panel/class" not in sys.path:
            sys.path.insert(0, "/www/server/panel/class")

        import public

        if os.path.exists(APACHE_PATH):
            public.ExecShell("/etc/init.d/httpd stop")
            os.rename(APACHE_PATH, APACHE_PATH + "_back")

        if os.path.exists(NGINX_PATH + "_back"):
            os.rename(NGINX_PATH + "_back", NGINX_PATH)

    def check_web_server_config(self):
        if "/www/server/panel/class" not in sys.path:
            sys.path.insert(0, "/www/server/panel/class")

        import public

        # nginx
        ng_error = ""
        if os.path.exists(NGINX_PATH):
            shell_str = "ulimit -n 8192; {np}/sbin/nginx -t -c {np}/conf/nginx.conf".format(np=NGINX_PATH)
            ng_result = public.ExecShell(shell_str)
            if ng_result[1].find("successful") == -1:
                ng_error = ng_result[1]

        # apache
        ap_error = ""
        if os.path.exists(APACHE_PATH):
            shell_str = "ulimit -n 8192; {ap}/bin/apachectl -t".format(ap=APACHE_PATH)
            ap_result = public.ExecShell(shell_str)
            if ap_result[1].find("Syntax OK") == -1:
                ap_error = ap_result[1]

        if ng_error:
            print(ng_error)

        if ap_error:
            print(ap_error)

        if ng_error or ap_error:
            self.fail("Failed to execute")
