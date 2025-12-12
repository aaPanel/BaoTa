# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2017 宝塔软件(http:#bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# -------------------------------------------------------------------

# ------------------------------
# 网站管理类
# ------------------------------
import io, re, public, os, sys, shutil, json, hashlib, socket, time
import traceback
import psutil
import ssl
import socket


try:
    # import OpenSSL
    import idna
except:
    # os.system("btpip install pyOpenSSL -I")
    os.system("btpip install idna -I")
    # import OpenSSL
    import idna
import base64

try:
    from BTPanel import session
    from BTPanel import cache
except:
    pass
from panelRedirect import panelRedirect
import site_dir_auth
# from panelModel.syncsiteModel import main as syncsite
from ssl_manage import SSLManger
from mod.base import json_response


class panelSite(panelRedirect):
    siteName = None  # 网站名称
    sitePath = None  # 根目录
    sitePort = None  # 端口
    phpVersion = None  # PHP版本
    setupPath = None  # 安装路径
    isWriteLogs = None  # 是否写日志
    nginx_conf_bak = '/tmp/backup_nginx.conf'
    apache_conf_bak = '/tmp/backup_apache.conf'
    is_ipv6 = False
    conf_dir = '{}/vhost/config'.format(public.get_panel_path())  # 防盗链配置

    def __init__(self):
        self.setupPath = public.get_setup_path()
        path = self.setupPath + '/panel/vhost/nginx'
        if not os.path.exists(path): public.ExecShell("mkdir -p " + path + " && chmod -R 644 " + path)
        path = self.setupPath + '/panel/vhost/apache'
        if not os.path.exists(path): public.ExecShell("mkdir -p " + path + " && chmod -R 644 " + path)
        path = self.setupPath + '/panel/vhost/rewrite'
        if not os.path.exists(path): public.ExecShell("mkdir -p " + path + " && chmod -R 644 " + path)
        path = self.setupPath + '/stop'
        if not os.path.exists(path + '/index.html'):
            public.ExecShell('mkdir -p ' + path)
            public.ExecShell('wget -O ' + path + '/index.html ' + public.get_url() + '/stop.html &')
        self.__proxyfile = '{}/data/proxyfile.json'.format(public.get_panel_path())
        self.OldConfigFile()
        if os.path.exists(self.nginx_conf_bak): os.remove(self.nginx_conf_bak)
        if os.path.exists(self.apache_conf_bak): os.remove(self.apache_conf_bak)
        self.is_ipv6 = os.path.exists(self.setupPath + '/panel/data/ipv6.pl')
        sys.setrecursionlimit(1000000)
        try:
            if not os.path.isdir(self.conf_dir):
                os.makedirs(self.conf_dir, 0o755)
        except PermissionError as e:
            public.WriteLog('信息获取', "{}失败: {}".format(self.conf_dir, str(e)))

        self.site_backup_log_path = "/www/backup/site_backup_log"

    # 默认配置文件
    def check_default(self):
        nginx = self.setupPath + '/panel/vhost/nginx'
        httpd = self.setupPath + '/panel/vhost/apache'
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
</VirtualHost>'''

        listen_ipv6 = ''
        if self.is_ipv6: listen_ipv6 = "\n    listen [::]:80;"
        nginx_default = '''server
{
    listen 80;%s
    server_name _;
    index index.html;
    root /www/server/nginx/html;
}''' % listen_ipv6
        if not os.path.exists(httpd + '/0.default.conf') and not os.path.exists(httpd + '/default.conf'): public.writeFile(httpd + '/0.default.conf', httpd_default)
        if not os.path.exists(nginx + '/0.default.conf') and not os.path.exists(nginx + '/default.conf'): public.writeFile(nginx + '/0.default.conf', nginx_default)

    # 添加apache端口
    def apacheAddPort(self, port):
        port = str(port)
        filename = self.setupPath + '/apache/conf/extra/httpd-ssl.conf'
        if os.path.exists(filename):
            ssl_conf = public.readFile(filename)
            if ssl_conf:
                if ssl_conf.find('Listen 443') != -1:
                    ssl_conf = ssl_conf.replace('Listen 443', '')
                    public.writeFile(filename, ssl_conf)

        filename = self.setupPath + '/apache/conf/httpd.conf'
        if not os.path.exists(filename): return
        allConf = public.readFile(filename)
        rep = r"Listen\s+([0-9]+)\n"
        tmp = re.findall(rep, allConf)
        if not tmp: return False
        for key in tmp:
            if key == port: return False

        listen = "\nListen " + tmp[0] + "\n"
        listen_ipv6 = ''
        # if self.is_ipv6: listen_ipv6 = "\nListen [::]:" + port
        allConf = allConf.replace(listen, listen + "Listen " + port + listen_ipv6 + "\n")
        public.writeFile(filename, allConf)
        return True

    # 添加到apache
    def apacheAdd(self):
        import time
        listen = ''
        if self.sitePort != '80': self.apacheAddPort(self.sitePort)
        acc = public.md5(str(time.time()))[0:8]
        try:
            httpdVersion = public.readFile(self.setupPath + '/apache/version.pl').strip()
        except:
            httpdVersion = ""
        if httpdVersion == '2.2':
            vName = ''
            if self.sitePort != '80' and self.sitePort != '443':
                vName = "NameVirtualHost  *:" + self.sitePort + "\n"
            phpConfig = ""
            apaOpt = "Order allow,deny\n\t\tAllow from all"
        else:
            vName = ""
            phpConfig = '''
    #PHP
    <FilesMatch \\.php$>
            SetHandler "proxy:%s"
    </FilesMatch>
    ''' % (public.get_php_proxy(self.phpVersion, 'apache'),)
            apaOpt = 'Require all granted'

        conf = '''%s<VirtualHost *:%s>
    ServerAdmin webmaster@example.com
    DocumentRoot "%s"
    ServerName %s.%s
    ServerAlias %s
    IncludeOptional /www/server/panel/vhost/apache/extension/%s/*.conf
    #errorDocument 404 /404.html
    ErrorLog "%s-error_log"
    CustomLog "%s-access_log" combined

    #DENY FILES
     <Files ~ (\.user.ini|\.htaccess|\.git|\.env|\.svn|\.project|LICENSE|README.md)$>
       Order allow,deny
       Deny from all
    </Files>
    %s
    #PATH
    <Directory "%s">
        SetOutputFilter DEFLATE
        Options FollowSymLinks
        AllowOverride All
        %s
        DirectoryIndex index.php index.html index.htm default.php default.html default.htm
    </Directory>
</VirtualHost>''' % (
            vName, self.sitePort, self.sitePath, acc, self.siteName, self.siteName, self.siteName,
            public.GetConfigValue('logs_path') + '/' + self.siteName,
            public.GetConfigValue('logs_path') + '/' + self.siteName,
            phpConfig, self.sitePath, apaOpt)

        ext_path = "/www/server/panel/vhost/apache/extension/%s/" % self.siteName
        if not os.path.exists(ext_path):
            os.makedirs(ext_path)

        htaccess = self.sitePath + '/.htaccess'
        if not os.path.exists(htaccess): public.writeFile(htaccess, ' ')
        public.ExecShell('chmod -R 755 ' + htaccess)
        public.ExecShell('chown -R www:www ' + htaccess)

        filename = self.setupPath + '/panel/vhost/apache/' + self.siteName + '.conf'
        public.writeFile(filename, conf)
        return True

    def set_404_config(self, get):
        try:
            status = get.status
            # filename = get.filename  # 从前端获取filename参数
            # if not filename.endswith('.html'):
            #     return public.returnMsg(False, "修改失败，文件名必须以.html结尾")
            config = self.get_404_config(get)
            # 更新配置
            config['status'] = status
            # config['filename'] = filename  # 将filename保存到配置中
            # 写回配置文件
            with open('/www/server/panel/class/404_settings.json', 'w') as f:
                json.dump(config, f)
            return public.returnMsg(True, "修改成功！")
        except Exception as e:
            return public.returnMsg(False, "修改失败" + str(e))


    def get_404_config(self,get):
        try:
            with open('/www/server/panel/class/404_settings.json', 'r') as f:
                settings = json.load(f)
        except FileNotFoundError:
            # 如果文件不存在，那么创建一个新的文件，并保存默认的设置
            # settings = {'status': "0", 'filename': "404.html"}
            settings = {'status': "1"}
        with open('/www/server/panel/class/404_settings.json', 'w') as f:
            json.dump(settings, f)
        status = settings.get('status', "1")
        # filename = settings.get('filename', "404.html")
        return {'status': status}  # 返回一个字典

    # 添加到nginx
    def nginxAdd(self):
        # config = self.get_404_config()
        # enable_error_page = config.get('status',"0")
        # error_page_line = 'error_page 404 /404.html;'

        # if enable_error_page=="0":
        #   error_page_line = '#error_page 404 /404.html;'
        # else:
        #   error_page_line = 'error_page 404 /404.html;'

        if not os.path.exists('/www/server/panel/class/404_settings.json'):
            public.writeFile('/www/server/panel/class/404_settings.json',json.dumps({}))

        template = None
        use_template = public.readFile("{}/data/use_nginx_template.pl".format(public.get_panel_path()))
        if isinstance(use_template, str):
            template_file = "{}/data/nginx_template/{}".format(public.get_panel_path(), use_template)
            if os.path.isfile(template_file):
                template = public.readFile(template_file)


        with open('/www/server/panel/class/404_settings.json', 'r') as f:
            settings = json.load(f)
        status = settings.get('status', "1")
        filename = settings.get('filename', "404.html")
        error_page_line = 'error_page 404 /' + filename + ';'

        if status == "0":
            error_page_line = '#' + error_page_line
        else:
            error_page_line = 'error_page 404 /' + filename + ';'

        listen_ipv6 = ''
        if self.is_ipv6: listen_ipv6 = "\n    listen [::]:%s;" % self.sitePort

        conf = '''server
{{
    listen {listen_port};{listen_ipv6}
    server_name {site_name};
    index index.php index.html index.htm default.php default.htm default.html;
    root {site_path};
    #CERT-APPLY-CHECK--START
    # 用于SSL证书申请时的文件验证相关配置 -- 请勿删除
    include /www/server/panel/vhost/nginx/well-known/{site_name}.conf;
    #CERT-APPLY-CHECK--END
    include /www/server/panel/vhost/nginx/extension/{site_name}/*.conf;
    
    #SSL-START {ssl_start_msg}
    #error_page 404/404.html;
    #SSL-END

    #ERROR-PAGE-START  {err_page_msg}
    {error_page_line}
    #error_page 502 /502.html;
    #ERROR-PAGE-END

    #PHP-INFO-START  {php_info_start}
    include enable-php-{php_version}.conf;
    #PHP-INFO-END

    #REWRITE-START {rewrite_start_msg}
    include {setup_path}/panel/vhost/rewrite/{site_name}.conf;
    #REWRITE-END

    #禁止访问的文件或目录
    location ~ ^/(\.user.ini|\.htaccess|\.git|\.env|\.svn|\.project|LICENSE|README.md)
    {{
        return 404;
    }}

    #一键申请SSL证书验证目录相关设置
    location ~ \.well-known{{
        allow all;
    }}

    #禁止在证书验证目录放入敏感文件
    if ( $uri ~ "^/\.well-known/.*\.(php|jsp|py|js|css|lua|ts|go|zip|tar\.gz|rar|7z|sql|bak)$" ) {{
        return 403;
    }}

    location ~ .*\\.(gif|jpg|jpeg|png|bmp|swf)$
    {{
        expires      30d;
        error_log /dev/null;
        access_log /dev/null;
    }}

    location ~ .*\\.(js|css)?$
    {{
        expires      12h;
        error_log /dev/null;
        access_log /dev/null;
    }}
    access_log  {log_path}/{site_name}.log;
    error_log  {log_path}/{site_name}.error.log;
}}'''.format(
            listen_port=self.sitePort,
            listen_ipv6=listen_ipv6,
            site_path=self.sitePath,
            ssl_start_msg=public.getMsg('NGINX_CONF_MSG1'),
            err_page_msg=public.getMsg('NGINX_CONF_MSG2'),
            php_info_start=public.getMsg('NGINX_CONF_MSG3'),
            php_version=self.phpVersion,
            setup_path=self.setupPath,
            rewrite_start_msg=public.getMsg('NGINX_CONF_MSG4'),
            log_path=self.get_sites_log_path(),
            site_name=self.siteName,
            error_page_line=error_page_line
        )

        template_conf = None
        if isinstance(template, str):
            try:
                template_conf = template.format(
                    listen_port=self.sitePort,
                    listen_ipv6=listen_ipv6,
                    site_path=self.sitePath,
                    ssl_start_msg=public.getMsg('NGINX_CONF_MSG1'),
                    err_page_msg=public.getMsg('NGINX_CONF_MSG2'),
                    php_info_start=public.getMsg('NGINX_CONF_MSG3'),
                    php_version=self.phpVersion,
                    setup_path=self.setupPath,
                    rewrite_start_msg=public.getMsg('NGINX_CONF_MSG4'),
                    log_path=self.get_sites_log_path(),
                    site_name=self.siteName,
                    error_page_line=error_page_line
                )
            except:
                template_conf = None

        # 写配置文件
        if not os.path.exists("/www/server/panel/vhost/nginx/well-known"):
            os.makedirs("/www/server/panel/vhost/nginx/well-known", 0o600)
        public.writeFile("/www/server/panel/vhost/nginx/well-known/{}.conf".format(self.siteName), "")
        if not os.path.exists("/www/server/panel/vhost/nginx/extension/{}/".format(self.siteName)):
            os.makedirs("/www/server/panel/vhost/nginx/extension/{}/".format(self.siteName), 0o600)
        filename = self.setupPath + '/panel/vhost/nginx/' + self.siteName + '.conf'
        if template_conf is not None:
            if not public.writeFile(filename, template_conf):
                return False
        else:
            if not public.writeFile(filename, conf):
                return False

        # 生成伪静态文件
        urlrewritePath = self.setupPath + '/panel/vhost/rewrite'
        urlrewriteFile = urlrewritePath + '/' + self.siteName + '.conf'
        if not os.path.exists(urlrewritePath): os.makedirs(urlrewritePath)
        open(urlrewriteFile, 'w+').close()
        if not os.path.exists(urlrewritePath):
            public.writeFile(urlrewritePath, '')
        if not os.path.exists(urlrewriteFile):
            # 如果rewrite文件创建失败，撤回网站主配置文件
            if os.path.exists(filename):
                os.remove(filename)
            return False

        return True


    # 重新生成nginx配置文件
    def rep_site_config(self, get):
        self.siteName = get.siteName
        siteInfo = public.M('sites').where('name=?', (self.siteName,)).field('id,path,port').find()
        siteInfo['domains'] = public.M('domains').where('pid=?', (siteInfo['id'],)).field('name,port').select()
        siteInfo['binding'] = public.M('binding').where('pid=?', (siteInfo['id'],)).field('domain,path').select()

    # openlitespeed
    def openlitespeed_add_site(self, get, init_args=None):
        # 写主配置httpd_config.conf
        # 操作默认监听配置
        if not self.sitePath:
            return public.returnMsg(False, "Not specify parameter [sitePath]")
        if init_args:
            self.siteName = init_args['sitename']
            self.phpVersion = init_args['phpv']
            self.sitePath = init_args['rundir']
        conf_dir = self.setupPath + '/panel/vhost/openlitespeed/'
        if not os.path.exists(conf_dir):
            os.makedirs(conf_dir)
        file = conf_dir + self.siteName + '.conf'

        v_h = """
#VHOST_TYPE BT_SITENAME START
virtualhost BT_SITENAME {
vhRoot BT_RUN_PATH
configFile /www/server/panel/vhost/openlitespeed/detail/BT_SITENAME.conf
allowSymbolLink 1
enableScript 1
restrained 1
setUIDMode 0
}
#VHOST_TYPE BT_SITENAME END
"""
        self.old_name = self.siteName
        if hasattr(get, "dirName"):
            self.siteName = self.siteName + "_" + get.dirName
            # sub_dir = self.sitePath + "/" + get.dirName
            v_h = v_h.replace("VHOST_TYPE", "SUBDIR")
            v_h = v_h.replace("BT_SITENAME", self.siteName)
            v_h = v_h.replace("BT_RUN_PATH", self.sitePath)
            # extp_name = self.siteName + "_" + get.dirName
        else:
            self.openlitespeed_domain(get)
            v_h = v_h.replace("VHOST_TYPE", "VHOST")
            v_h = v_h.replace("BT_SITENAME", self.siteName)
            v_h = v_h.replace("BT_RUN_PATH", self.sitePath)
            # extp_name = self.siteName
        public.writeFile(file, v_h, "a+")
        # 写vhost
        conf = '''docRoot                   $VH_ROOT
vhDomain                  $VH_NAME
adminEmails               example@example.com
enableGzip                1
enableIpGeo               1

index  {
  useServer               0
  indexFiles index.php,index.html
}

errorlog /www/wwwlogs/$VH_NAME_ols.error_log {
  useServer               0
  logLevel                ERROR
  rollingSize             10M
}

accesslog /www/wwwlogs/$VH_NAME_ols.access_log {
  useServer               0
  logFormat               '%{X-Forwarded-For}i %h %l %u %t "%r" %>s %b "%{Referer}i" "%{User-Agent}i"'
  logHeaders              5
  rollingSize             10M
  keepDays                10  compressArchive         1
}

scripthandler  {
  add                     lsapi:BT_EXTP_NAME php
}

extprocessor BTSITENAME {
  type                    lsapi
  address                 UDS://tmp/lshttpd/BT_EXTP_NAME.sock
  maxConns                20
  env                     LSAPI_CHILDREN=20
  initTimeout             600
  retryTimeout            0
  persistConn             1
  pcKeepAliveTimeout      1
  respBuffer              0
  autoStart               1
  path                    /usr/local/lsws/lsphpBTPHPV/bin/lsphp
  extUser                 www
  extGroup                www
  memSoftLimit            2047M
  memHardLimit            2047M
  procSoftLimit           400
  procHardLimit           500
}

phpIniOverride  {
php_admin_value open_basedir "/tmp/:BT_RUN_PATH"
}

expires {
    enableExpires           1
    expiresByType           image/*=A43200,text/css=A43200,application/x-javascript=A43200,application/javascript=A43200,font/*=A43200,application/x-font-ttf=A43200
}

rewrite  {
  enable                  1
  autoLoadHtaccess        1
  include /www/server/panel/vhost/openlitespeed/proxy/BTSITENAME/urlrewrite/*.conf
  include /www/server/panel/vhost/apache/redirect/BTSITENAME/*.conf
  include /www/server/panel/vhost/openlitespeed/redirect/BTSITENAME/*.conf
}
include /www/server/panel/vhost/openlitespeed/proxy/BTSITENAME/*.conf
'''
        open_base_path = self.sitePath
        if self.sitePath[-1] != '/':
            open_base_path = self.sitePath + '/'
        conf = conf.replace('BT_RUN_PATH', open_base_path)
        conf = conf.replace('BT_EXTP_NAME', self.siteName)
        conf = conf.replace('BTPHPV', self.phpVersion)
        conf = conf.replace('BTSITENAME', self.siteName)

        # 写配置文件
        conf_dir = self.setupPath + '/panel/vhost/openlitespeed/detail/'
        if not os.path.exists(conf_dir):
            os.makedirs(conf_dir)
        file = conf_dir + self.siteName + '.conf'
        # if hasattr(get,"dirName"):
        #     file = conf_dir + self.siteName +'_'+get.dirName+ '.conf'
        public.writeFile(file, conf)

        # 生成伪静态文件
        # urlrewritePath = self.setupPath + '/panel/vhost/rewrite'
        # urlrewriteFile = urlrewritePath + '/' + self.old_name + '.conf'
        # if not os.path.exists(urlrewritePath): os.makedirs(urlrewritePath)
        # open(urlrewriteFile, 'w+').close()
        return True

    # 上传CSV文件
    # def upload_csv(self, get):
    #     import files
    #     f = files.files()
    #     get.f_path = '/tmp/multiple_website.csv'
    #     result = f.upload(get)
    #     return result

    # 处理CSV内容
    def __process_cvs(self, key):
        import csv
        with open('/tmp/multiple_website.csv') as f:
            f_csv = csv.reader(f)
            # result = [i for i in f_csv]
            return [dict(zip(key, i)) for i in [i for i in f_csv if "FTP" not in i]]

    # 批量创建网站
    def __create_website_mulitiple(self, websites_info, site_path, get):
        create_successfully = {}
        create_failed = {}
        for data in websites_info:
            if not data:
                continue
            try:
                domains = data['website'].split(',')
                website_name = domains[0].split(':')[0]
                data['port'] = '80' if len(domains[0].split(':')) < 2 else domains[0].split(':')[1]
                get.webname = json.dumps({"domain": website_name, "domainlist": domains[1:], "count": 0})
                get.path = data['path'] if 'path' in data and data['path'] != '0' and data['path'] != '1' else site_path + '/' + website_name
                get.version = data['version'] if 'version' in data and data['version'] != '0' else '00'
                get.ftp = 'true' if 'ftp' in data and data['ftp'] == '1' else False
                get.sql = 'true' if 'sql' in data and data['sql'] == '1' else False
                get.port = data['port'] if 'port' in data else '80'
                get.codeing = 'utf8'
                get.type = 'PHP'
                get.type_id = '0'
                get.ps = ''
                create_other = {}
                create_other['db_status'] = False
                create_other['ftp_status'] = False
                if get.sql == 'true':
                    create_other['db_pass'] = get.datapassword = public.gen_password(16)
                    create_other['db_user'] = get.datauser = website_name.replace('.', '_').replace("-", "_")[:16]
                    create_other['db_status'] = True
                if get.ftp == 'true':
                    create_other['ftp_pass'] = get.ftp_password = public.gen_password(16)
                    create_other['ftp_user'] = get.ftp_username = website_name.replace('.', '_')
                    create_other['ftp_status'] = True
                result = self.AddSite(get, multiple=1)
                if 'status' in result:
                    create_failed[domains[0]] = result['msg']
                    continue
                create_successfully[domains[0]] = create_other
            except:
                create_failed[domains[0]] = '创建出错了，请再试一次'
        return {'status': True, 'msg': '创建网站 [ {} ] 成功'.format(','.join(create_successfully)), 'error': create_failed,
                'success': create_successfully}

    # 批量创建网站
    def create_website_multiple(self, get):
        '''
            @name 批量创建网站
            @author zhwen<2020-11-26>
            @param create_type txt/csv  txt格式为 “网站名|网站路径|是否创建FTP|是否创建数据库|PHP版本” 每个网站一行
                                                 "aaa.com:88,bbb.com|/www/wwwserver/aaa.com/或1|1/0|1/0|0/73"
                                        csv格式为 “网站名|网站端口|网站路径|PHP版本|是否创建数据库|是否创建FTP”
            @param websites_content     "[[aaa.com|80|/www/wwwserver/aaa.com/|1|1|73]...."
        '''
        key = ['website', 'path', 'ftp', 'sql', 'version']
        site_path = public.M('config').getField('sites_path')
        if get.create_type == 'txt':
            websites_info = [dict(zip(key, i)) for i in [i.strip().split('|') for i in json.loads(get.websites_content)]]
        else:
            websites_info = self.__process_cvs(key)
        res = self.__create_website_mulitiple(websites_info, site_path, get)
        public.serviceReload()
        return res

    def add_task(self, get):
        try:
            self.config_path = '/www/server/panel/data/syncsite.json'
            if not hasattr(get, 'site_id') or not hasattr(get, 'git_addr') or not hasattr(get, 'cycle'):
                return public.returnMsg(False, '参数错误!')
            if not os.path.exists(self.config_path):
                public.writeFile(self.config_path, '{}')
            conf_data = json.loads(public.readFile(self.config_path))
            path = public.M('sites').where('id=?', (get.site_id,)).getField('path')
            if not path:
                return public.returnMsg(False, '站点不存在!')
            branch = ''
            if hasattr(get, 'branch') and get.branch:
                branch = '-b {}'.format(get.branch)
            exec = 'rm -rf {}/git_bt && mkdir -p {}/git_bt && git clone {} {} {}/git_bt/ && cp -rf {}/git_bt/* {} && rm -rf {}/git_bt'.format(path, path, branch, get.git_addr, path, path, path, path)
            conf_data[str(get.site_id)] = {'exec': exec, 'cycle': get.cycle, 'last_time': 0, 'git_addr': get.git_addr, 'branch': get.branch}
            public.writeFile(self.config_path, json.dumps(conf_data))
            return public.returnMsg(True, '添加成功!')
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            return public.returnMsg(False, '添加失败!')
    # 添加站点
    def AddSite(self, get, multiple=None):
        res_msg = self.check_webserver(use2render=False)  # 检查是否有web服务
        if res_msg:
            return public.returnMsg(False, res_msg)
        self.check_default()
        isError = public.checkWebConfig()
        if isError != True:
            return public.returnMsg(False, 'ERROR: 检测到配置文件有错误,请先排除后再操作<br><br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')

        import json, files
        public.set_module_logs("php", 'add_site')
        get.path = self.__get_site_format_path(get.path)
        if ' ' in get.path or '\n' in get.path: return public.returnMsg(False, '目录中不能包含空格或换行符，请重新选择！')
        if (not os.path.isdir(get.path)) and os.path.exists(get.path):return public.returnMsg(False, '选中的必须是一个目录而不是一个文件')

        if not public.check_site_path(get.path):
            a, c = public.get_sys_path()
            return public.returnMsg(False, '请不要将网站根目录设置到以下关键目录中: <br>{}'.format("<br>".join(a + c)))
        try:
            siteMenu = json.loads(get.webname)
        except:
            return public.returnMsg(False, 'webname参数格式不正确，应该是可被解析的JSON字符串')
        self.siteName = self.ToPunycode(siteMenu['domain'].strip().split(':')[0]).strip().lower()
        self.sitePath = self.ToPunycodePath(self.GetPath(get.path.replace(' ', ''))).strip()
        self.sitePort = get.port.strip().replace(' ', '')

        if self.sitePort == "": get.port = "80"
        if not public.checkPort(self.sitePort):
            return public.returnMsg(False, 'SITE_ADD_ERR_PORT')
        for domain in siteMenu['domainlist']:
            if not len(domain.split(':')) == 2:
                continue
            if not public.checkPort(domain.split(':')[1].strip()):
                return public.returnMsg(False, 'SITE_ADD_ERR_PORT')

        if hasattr(get, 'version'):
            self.phpVersion = get.version.replace(' ', '')
        else:
            self.phpVersion = '00'

        if not self.phpVersion: self.phpVersion = '00'

        php_version = self.GetPHPVersion(get)
        is_phpv = False
        for php_v in php_version:
            if self.phpVersion == php_v['version']:
                is_phpv = True
                break
        if not is_phpv: return public.returnMsg(False, '指定PHP版本不存在!')

        main_domain = None
        # if siteMenu['count']:
        #    domain            = get.domain.replace(' ','')
        # 表单验证
        if not self.__check_site_path(self.sitePath): return public.returnMsg(False, 'PATH_ERROR')
        if len(self.phpVersion) < 2: return public.returnMsg(False, 'SITE_ADD_ERR_PHPEMPTY')
        reg = r"^([\w\-\*]{1,100}\.){1,24}([\w\-]{1,24}|[\w\-]{1,24}\.[\w\-]{1,24})$"
        if not re.match(reg, self.siteName): return public.returnMsg(False, 'SITE_ADD_ERR_DOMAIN')
        if self.siteName.find('*') != -1: return public.returnMsg(False, 'SITE_ADD_ERR_DOMAIN_TOW')
        if self.sitePath[-1] == '.': return public.returnMsg(False, '网站目录结尾不可以是 "."')

        if not main_domain:
            main_domain = self.siteName

        opid = public.M('domain').where("name=? and port=?", (main_domain, int(self.sitePort))).getField('pid')

        if opid:
            if public.M('sites').where('id=?', (opid,)).count():
                return public.returnMsg(False, 'SITE_ADD_ERR_DOMAIN_EXISTS')
            public.M('domain').where('pid=?', (opid,)).delete()

        if public.M('binding').where('domain=?', (self.siteName,)).count():
            return public.returnMsg(False, 'SITE_ADD_ERR_DOMAIN_EXISTS')

        # 是否重复
        sql = public.M('sites')
        if sql.where("name=?", (self.siteName,)).count():
            if public.is_ipv4(self.siteName):
                self.siteName = self.siteName + "_" + str(self.sitePort)
            else:
                return public.returnMsg(False, 'SITE_ADD_ERR_EXISTS')

        create_conf = self.create_default_conf()
        # 创建根目录
        if not os.path.exists(self.sitePath):
            try:
                os.makedirs(self.sitePath)
            except Exception as ex:
                return public.returnMsg(False, '创建根目录失败, %s' % ex)
            public.ExecShell('chmod -R 755 ' + self.sitePath)
            public.ExecShell('chown -R www:www ' + self.sitePath)

        # 创建basedir
        self.DelUserInI(self.sitePath)
        userIni = self.sitePath + '/.user.ini'
        if not os.path.exists(userIni):
            public.writeFile(userIni, 'open_basedir=' + self.sitePath + '/:/tmp/')
            public.ExecShell('chmod 644 ' + userIni)
            public.ExecShell('chown root:root ' + userIni)
            public.ExecShell('chattr +i ' + userIni)

        ngx_open_basedir_path = self.setupPath + '/panel/vhost/open_basedir/nginx'
        if not os.path.exists(ngx_open_basedir_path):
            os.makedirs(ngx_open_basedir_path, 384)
        ngx_open_basedir_file = ngx_open_basedir_path + '/{}.conf'.format(self.siteName)
        ngx_open_basedir_body = '''set $bt_safe_dir "open_basedir";
set $bt_safe_open "{}/:/tmp/";'''.format(self.sitePath)
        public.writeFile(ngx_open_basedir_file, ngx_open_basedir_body)

        # 创建默认文档
        index = self.sitePath + '/index.html'
        if not os.path.exists(index) and create_conf["page_index"]:
            public.writeFile(index, public.readFile('data/defaultDoc.html'))
            public.ExecShell('chmod -R 755 ' + index)
            public.ExecShell('chown -R www:www ' + index)

        # 创建默认404页
        doc404 = self.sitePath + '/404.html'
        path_404 = '{}/data/404.html'.format(public.get_panel_path())
        domestic_ip_file = '{}/data/domestic_ip.pl'.format(public.get_panel_path())
        is_domestic = os.path.exists(domestic_ip_file)
        if is_domestic:
            cn_404 = '{}/config/examples/404_cn.html'.format(public.get_panel_path())
            public.WriteFile(path_404, public.ReadFile(cn_404))
            if os.path.exists(domestic_ip_file): os.remove(domestic_ip_file)

        if create_conf["page_404"]:
            default_404_page_content = '''
<html>
<head><title>404 Not Found</title></head>
<body>
<center><h1>404 Not Found</h1></center>
<hr><center>nginx</center>
</body>
</html>
                '''
            if not os.path.exists(doc404):
                if os.path.exists(path_404):
                    data_404_body = public.ReadFile(path_404)
                    if not data_404_body: data_404_body = default_404_page_content
                else:
                    data_404_body = default_404_page_content

                public.WriteFile(doc404, data_404_body)
                public.ExecShell('chmod -R 755 ' + doc404)
                public.ExecShell('chown -R www:www ' + doc404)

        # 写入配置
        result = self.nginxAdd()
        if not result: return public.returnMsg(False, 'SITE_ADD_ERR_WRITE')
        result = self.apacheAdd()
        if not result: return public.returnMsg(False, 'SITE_ADD_ERR_WRITE')
        result = self.openlitespeed_add_site(get)
        # 检查处理结果
        if not result: return public.returnMsg(False, 'SITE_ADD_ERR_WRITE')

        ps = public.xssencode2(get.ps)
        # 添加放行端口
        if self.sitePort != '80':
            import firewalls
            get.port = self.sitePort
            get.ps = self.siteName
            firewalls.firewalls().AddAcceptPort(get)
        else:  # 检查80端口是否放行， 并放行
            self.test_80_port()

        if not hasattr(get, 'type_id'): get.type_id = 0
        if not hasattr(get, 'project_type'): get.project_type = 'PHP'
        public.check_domain_cloud(self.siteName)
        # 写入数据库
        get.pid = public.M('sites').add('name,path,status,ps,type_id,addtime,project_type', (self.siteName, self.sitePath, '1', ps, get.type_id, public.getDate(), get.project_type))

        # 添加更多域名
        for domain in siteMenu['domainlist']:
            get.domain = domain
            get.webname = self.siteName
            get.id = str(get.pid)
            self.AddDomain(get, multiple)

        public.M('domain').add('pid,name,port,addtime', (get.pid, main_domain, self.sitePort, public.getDate()))

        data = {}
        data['siteStatus'] = True
        data['siteId'] = get.pid

        # 添加FTP
        data['ftpStatus'] = False
        if get.ftp == 'true':
            import ftp
            result = ftp.ftp().AddUser(get)
            if result['status']:
                data['ftpStatus'] = True
                data['ftpUser'] = get.ftp_username
                data['ftpPass'] = get.ftp_password

        # 添加数据库
        data['databaseStatus'] = False
        if get.sql == 'true' or get.sql == 'MySQL':
            import database
            if len(get.datauser) > 16: get.datauser = get.datauser[:16]
            get.name = get.datauser
            get.db_user = get.datauser
            get.password = get.datapassword
            get.address = '127.0.0.1'
            result = database.database().AddDatabase(get)
            data['databaseUser'] = get.datauser
            data['databasePass'] = get.datapassword
            if result['status']:
                data['databaseStatus'] = True
                data['databaseName'] = get.datauser

        # 检查是否需要设置Git仓库
        data['gitStatus'] = False
        if getattr(get, 'git', 'false').lower() == 'true' and hasattr(get, 'git_addr'):
            get['site_id'] = get.pid  # 使用新添加站点的ID
            get['git_addr'] = get.git_addr
            get['cycle'] = getattr(get, 'cycle', '1')
            git_result = self.add_task(get)
            if git_result['status']:
                data['gitStatus'] = True

        if not multiple:
            public.serviceReload()
        public.WriteLog('TYPE_SITE', 'SITE_ADD_SUCCESS', (self.siteName,))
        if create_conf["log_split"]:
            self.site_crontab_log(self.siteName)
        self._set_web_path_mod(self.sitePath)
        return data

    def __get_site_format_path(self, path):
        path = path.replace('//', '/')
        if path[-1:] == '/':
            path = path[:-1]
        return path

    def __check_site_path(self, path):
        path = self.__get_site_format_path(path)
        other_path = public.M('config').where("id=?", ('1',)).field('sites_path,backup_path').find()
        if path == other_path['sites_path'] or path == other_path['backup_path']: return False
        return True

    def delete_website_multiple(self, get):
        '''
            @name 批量删除网站
            @author zhwen<2020-11-17>
            @param sites_id "1,2"
            @param ftp 0/1
            @param database 0/1
            @param  path 0/1
        '''
        sites_id = get.sites_id.split(',')
        del_successfully = []
        del_failed = {}
        for site_id in sites_id:
            get.id = site_id
            get.webname = public.M('sites').where("id=?", (site_id,)).getField('name')
            if not get.webname:
                continue
            try:
                self.DeleteSite(get, multiple=1)
                del_successfully.append(get.webname)
            except:
                del_failed[get.webname] = '删除时出错了，请再试一次'
                pass
        public.serviceReload()
        return {'status': True, 'msg': '删除网站 [ {} ] 成功'.format(','.join(del_successfully)), 'error': del_failed,
                'success': del_successfully}

    # 删除站点
    def DeleteSite(self, get, multiple=None):
        proxyconf = self.__read_config(self.__proxyfile)
        id = get.id
        if public.M('sites').where('id=?', (id,)).count() < 1: return public.returnMsg(False, '指定站点不存在!')
        siteName = get.webname
        get.siteName = siteName
        self.CloseTomcat(get)
        # 删除反向代理
        for i in range(len(proxyconf) - 1, -1, -1):
            if proxyconf[i]["sitename"] == siteName:
                del proxyconf[i]
        self.__write_config(self.__proxyfile, proxyconf)

        m_path = self.setupPath + '/panel/vhost/nginx/proxy/' + siteName
        if os.path.exists(m_path): public.ExecShell("rm -rf %s" % m_path)

        m_path = self.setupPath + '/panel/vhost/apache/proxy/' + siteName
        if os.path.exists(m_path): public.ExecShell("rm -rf %s" % m_path)

        # 删除目录保护
        _dir_aith_file = "%s/panel/data/site_dir_auth.json" % self.setupPath
        _dir_aith_conf = public.readFile(_dir_aith_file)
        if _dir_aith_conf:
            try:
                _dir_aith_conf = json.loads(_dir_aith_conf)
                if siteName in _dir_aith_conf:
                    del (_dir_aith_conf[siteName])
            except:
                pass
        self.__write_config(_dir_aith_file, _dir_aith_conf)

        dir_aith_path = self.setupPath + '/panel/vhost/nginx/dir_auth/' + siteName
        if os.path.exists(dir_aith_path): public.ExecShell("rm -rf %s" % dir_aith_path)

        dir_aith_path = self.setupPath + '/panel/vhost/apache/dir_auth/' + siteName
        if os.path.exists(dir_aith_path): public.ExecShell("rm -rf %s" % dir_aith_path)

        # 删除重定向
        __redirectfile = "%s/panel/data/redirect.conf" % self.setupPath
        redirectconf = self.__read_config(__redirectfile)
        for i in range(len(redirectconf) - 1, -1, -1):
            if redirectconf[i]["sitename"] == siteName:
                del redirectconf[i]
        self.__write_config(__redirectfile, redirectconf)
        m_path = self.setupPath + '/panel/vhost/nginx/redirect/' + siteName
        if os.path.exists(m_path): public.ExecShell("rm -rf %s" % m_path)
        m_path = self.setupPath + '/panel/vhost/apache/redirect/' + siteName
        if os.path.exists(m_path): public.ExecShell("rm -rf %s" % m_path)

        # 删除配置文件
        confPath = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        if os.path.exists(confPath): os.remove(confPath)

        confPath = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
        if os.path.exists(confPath): os.remove(confPath)
        open_basedir_file = self.setupPath + '/panel/vhost/open_basedir/nginx/' + siteName + '.conf'
        if os.path.exists(open_basedir_file): os.remove(open_basedir_file)

        # 删除openlitespeed配置
        vhost_file = "/www/server/panel/vhost/openlitespeed/{}.conf".format(siteName)
        if os.path.exists(vhost_file):
            public.ExecShell('rm -f {}*'.format(vhost_file))
        vhost_detail_file = "/www/server/panel/vhost/openlitespeed/detail/{}.conf".format(siteName)
        if os.path.exists(vhost_detail_file):
            public.ExecShell('rm -f {}*'.format(vhost_detail_file))
        vhost_ssl_file = "/www/server/panel/vhost/openlitespeed/detail/ssl/{}.conf".format(siteName)
        if os.path.exists(vhost_ssl_file):
            public.ExecShell('rm -f {}*'.format(vhost_ssl_file))
        vhost_sub_file = "/www/server/panel/vhost/openlitespeed/detail/{}_sub.conf".format(siteName)
        if os.path.exists(vhost_sub_file):
            public.ExecShell('rm -f {}*'.format(vhost_sub_file))

        vhost_redirect_file = "/www/server/panel/vhost/openlitespeed/redirect/{}".format(siteName)
        if os.path.exists(vhost_redirect_file):
            public.ExecShell('rm -rf {}*'.format(vhost_redirect_file))
        vhost_proxy_file = "/www/server/panel/vhost/openlitespeed/proxy/{}".format(siteName)
        if os.path.exists(vhost_proxy_file):
            public.ExecShell('rm -rf {}*'.format(vhost_proxy_file))

        # 删除openlitespeed监听配置
        self._del_ols_listen_conf(siteName)

        # 删除伪静态文件
        # filename = confPath+'/rewrite/'+siteName+'.conf'
        filename = '/www/server/panel/vhost/rewrite/' + siteName + '.conf'
        if os.path.exists(filename):
            os.remove(filename)
            public.ExecShell("rm -f " + confPath + '/rewrite/' + siteName + "_*")

        # 删除日志文件
        filename = public.GetConfigValue('logs_path') + '/' + siteName + '*'
        public.ExecShell("rm -f " + filename)

        # 删除证书
        # crtPath = '/etc/letsencrypt/live/'+siteName
        # if os.path.exists(crtPath):
        #    import shutil
        #    shutil.rmtree(crtPath)

        from mod.base.web_conf import remove_sites_service_config
        remove_sites_service_config(siteName, "")

        # 删除日志
        public.ExecShell("rm -f " + public.GetConfigValue('logs_path') + '/' + siteName + "-*")

        # 删除备份
        # public.ExecShell("rm -f "+session['config']['backup_path']+'/site/'+siteName+'_*')

        # 删除根目录
        if 'path' in get:
            if get.path in ('1', 1, True):
                import files
                get.path = self.__get_site_format_path(public.M('sites').where("id=?", (id,)).getField('path'))
                if self.__check_site_path(get.path):
                    if public.M('sites').where("path=?", (get.path,)).count() < 2:
                        files.files().DeleteDir(get)
                get.path = '1'

        # 重载配置
        if not multiple:
            public.serviceReload()

        # 从数据库删除
        public.M('sites').where("id=?", (id,)).delete()
        public.M('binding').where("pid=?", (id,)).delete()
        public.M('domain').where("pid=?", (id,)).delete()
        public.WriteLog('TYPE_SITE', "SITE_DEL_SUCCESS", (siteName,))

        # 是否删除关联数据库
        if hasattr(get, 'database'):
            if get.database in ('1', 1, True):
                find = public.M('databases').where("pid=?", (id,)).field('id,name').find()
                if find:
                    import database
                    get.name = find['name']
                    get.id = find['id']
                    database.database().DeleteDatabase(get)

        # 是否删除关联FTP
        if hasattr(get, 'ftp'):
            if get.ftp in ('1', 1, True):
                find = public.M('ftps').where("pid=?", (id,)).field('id,name').find()
                if find:
                    import ftp
                    get.username = find['name']
                    get.id = find['id']
                    ftp.ftp().DeleteUser(get)

        return public.returnMsg(True, 'SITE_DEL_SUCCESS')

    def _del_ols_listen_conf(self, sitename):
        conf_dir = '/www/server/panel/vhost/openlitespeed/listen/'
        if not os.path.exists(conf_dir):
            return False
        for i in os.listdir(conf_dir):
            file_name = conf_dir + i
            if os.path.isdir(file_name):
                continue
            conf = public.readFile(file_name)
            if not conf:
                continue
            map_rep = 'map\s+{}.*'.format(sitename)
            conf = re.sub(map_rep, '', conf)
            if "map" not in conf:
                public.ExecShell('rm -f {}*'.format(file_name))
                continue
            public.writeFile(file_name, conf)

    # 域名编码转换
    def ToPunycode(self, domain):
        import re
        match = re.search(u"[^u\0000-u\001f]+", domain)
        if not match:
            return domain
        try:
            if domain.startswith("*."):
                return "*." + idna.encode(domain[2:]).decode("utf8")
            else:
                return idna.encode(domain).decode("utf8")
        except:
            return domain

    # 中文路径处理
    def ToPunycodePath(self, path):
        if sys.version_info[0] == 2: path = path.encode('utf-8')
        if os.path.exists(path): return path
        import re
        match = re.search(u"[\x80-\xff]+", path)
        if not match: match = re.search(u"[\u4e00-\u9fa5]+", path)
        if not match: return path
        npath = ''
        for ph in path.split('/'):
            npath += '/' + self.ToPunycode(ph)
        return npath.replace('//', '/')

    def export_domains(self, args):
        '''
            @name 导出域名列表
            @author hwliang<2020-10-27>
            @param args<dict_obj>{
                siteName: string<网站名称>
            }
            @return string
        '''

        pid = public.M('sites').where('name=?', args.siteName).getField('id')
        domains = public.M('domain').where('pid=?', pid).field('name,port').select()
        text_data = []
        for domain in domains:
            text_data.append("{}:{}".format(domain['name'], domain['port']))
        data = "\n".join(text_data)
        return public.send_file(data, '{}_domains'.format(args.siteName))

    def import_domains(self, args):
        '''
            @name 导入域名
            @author hwliang<2020-10-27>
            @param args<dict_obj>{
                siteName: string<网站名称>
                domains: string<域名列表> 每行一个 格式： 域名:端口
            }
            @return string
        '''

        domains_tmp = args.domains.split("\n")
        get = public.dict_obj()
        get.webname = args.siteName
        get.id = public.M('sites').where('name=?', args.siteName).getField('id')
        domains = []
        for domain in domains_tmp:
            if public.M('domain').where('name=?', domain.split(':')[0]).count():
                continue
            domains.append(domain)

        get.domain = ','.join(domains)
        return self.AddDomain(get)

    # 添加域名
    def AddDomain(self, get, multiple=None):
        if not hasattr(get, "webname"):
            return public.returnMsg(False, '网站选择错误')
        get.webname = str(get.webname)

        # 检查配置文件
        isError = public.checkWebConfig()
        if isError != True:
            return public.returnMsg(False, 'ERROR: 检测到配置文件有错误,请先排除后再操作<br><br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')

        if not 'domain' in get: return public.returnMsg(False, '请填写域名!')
        if len(get.domain) < 3: return public.returnMsg(False, 'SITE_ADD_DOMAIN_ERR_EMPTY')
        domains = get.domain.strip().replace(' ', '').split(',')

        res_domains = []
        for domain in domains:
            if domain == "": continue
            domain = domain.strip().split(':')
            get.domain = self.ToPunycode(domain[0]).lower()
            get.port = '80'
            # 判断通配符域名格式
            if get.domain.find('*') != -1 and not get.domain.startswith('*.'):
                res_domains.append({"name": get.domain, "status": False, "msg": '域名格式不正确'})
                continue

            # 判断域名格式
            reg = "^([\w\-\*]{1,100}\.){1,24}([\w\-]{1,24}|[\w\-]{1,24}\.[\w\-]{1,24})$"
            if not re.match(reg, get.domain):
                res_domains.append({"name": get.domain, "status": False, "msg": '域名格式不正确'})
                continue

            # 获取自定义端口
            if len(domain) == 2:
                get.port = domain[1]
            if get.port == "": get.port = "80"

            # 判断端口是否合法
            if not re.match("^\d+$", get.port):
                res_domains.append({"name": get.domain, "status": False, "msg": '端口不合法，应该为数字'})
                continue
            not_used_ports = ('21', '25', '443', '888', '8888', '8443')
            if get.port in not_used_ports:
                res_domains.append({"name": get.domain, "status": False, "msg": '端口不合法，请勿使用常用端口，例如：ssh的22端口等'})
                continue
            intport = int(get.port)
            if intport < 1 or intport > 65535:
                res_domains.append({"name": get.domain, "status": False, "msg": '端口范围不合法'})
                continue
            # if not public.checkPort(get.port):
            #     res_domains.append({"name": get.domain, "status": False, "msg": '端口范围不合法'})
            #     continue
            # 检查域名是否存在
            sql = public.M('domain')
            opid = sql.where("name=? AND port=?", (get.domain, get.port)).getField('pid')
            if opid:
                siteName = public.M('sites').where('id=?', (opid,)).getField('name')
                if siteName:
                    res_domains.append({"name": get.domain, "status": False, "msg": '指定域名[{}]已被网站[{}]绑定过了'.format(get.domain, siteName)})
                    continue
                sql.where('pid=?', (opid,)).delete()

            # 检查是否被子目录绑定
            opid = public.M('binding').where('domain=?', (get.domain,)).getField('pid')
            if opid:
                siteName = public.M('sites').where('id=?', (opid,)).getField('name')
                res_domains.append({"name": get.domain, "status": False, "msg": '指定域名[{}]已被被网站[{}]的子目录绑定过了!'.format(get.domain, siteName)})
                continue

            # 写配置文件
            res = self.NginxDomain(get)
            if public.GetWebServer() == "nginx" and res is None:
                return public.returnMsg(False, 'nginx配置文件错误，请先检查配置文件')

            try:
                self.ApacheDomain(get)
                self.openlitespeed_domain(get)
                if self._check_ols_ssl(get.webname):
                    get.port = '443'
                    self.openlitespeed_domain(get)
                    get.port = '80'
            except:
                pass

            # 检查实际端口
            if len(domain) == 2: get.port = domain[1]

            # 添加放行端口
            if get.port != '80':
                import firewalls
                get.ps = get.domain
                firewalls.firewalls().AddAcceptPort(get)

            # 重载webserver服务
            if not multiple:
                public.serviceReload()
            full_domain = get.domain
            if not get.port in ['80', '443']: full_domain += ':' + get.port
            public.check_domain_cloud(full_domain)
            public.WriteLog('TYPE_SITE', 'DOMAIN_ADD_SUCCESS', (get.webname, get.domain))
            public.M('domain').add('pid,name,port,addtime', (get.id, get.domain, get.port, public.getDate()))
            res_domains.append({"name": get.domain, "status": True, "msg": '添加成功'})

        return self._ckeck_add_domain(get.webname, res_domains)

    # 判断ols_ssl是否已经设置
    def _check_ols_ssl(self, webname):
        conf = public.readFile('/www/server/panel/vhost/openlitespeed/listen/443.conf')
        if conf and webname in conf:
            return True
        return False

    # 添加openlitespeed 80端口监听
    def openlitespeed_set_80_domain(self, get, conf):
        rep = 'map\s+{}.*'.format(get.webname)
        domains = get.webname.strip().split(',')
        if conf:
            map_tmp = re.search(rep, conf)
            if map_tmp:
                map_tmp = map_tmp.group()
                domains = map_tmp.strip().split(',')
                if not public.inArray(domains, get.domain):
                    new_map = '{},{}'.format(conf, get.domain)
                    conf = re.sub(rep, new_map, conf)
            else:
                map_tmp = '\tmap\t{d} {d}\n'.format(d=domains[0])
                listen_rep = "secure\s*0"
                conf = re.sub(listen_rep, "secure 0\n" + map_tmp, conf)
            return conf

        else:
            rep_default = 'listener\s+Default\{(\n|[\s\w\*\:\#\.\,])*'
            tmp = re.search(rep_default, conf)
            # domains = get.webname.strip().split(',')
            if tmp:
                tmp = tmp.group()
                new_map = '\tmap\t{d} {d}\n'.format(d=domains[0])
                tmp += new_map
                conf = re.sub(rep_default, tmp, conf)
        return conf

    # openlitespeed写域名配置
    def openlitespeed_domain(self, get):
        listen_dir = '/www/server/panel/vhost/openlitespeed/listen/'
        if not os.path.exists(listen_dir):
            os.makedirs(listen_dir)
        listen_file = listen_dir + get.port + ".conf"
        listen_conf = public.readFile(listen_file)
        try:
            get.webname = json.loads(get.webname)
            get.domain = get.webname['domain'].replace('\r', '')
            get.webname = get.domain + "," + ",".join(get.webname["domainlist"])
            if get.webname[-1] == ',':
                get.webname = get.webname[:-1]
        except:
            pass

        if listen_conf:
            # 添加域名
            rep = 'map\s+{}.*'.format(get.webname)
            map_tmp = re.search(rep, listen_conf)
            if map_tmp:
                map_tmp = map_tmp.group()
                domains = map_tmp.strip().split(',')
                if not public.inArray(domains, get.domain):
                    new_map = '{},{}'.format(map_tmp, get.domain)
                    listen_conf = re.sub(rep, new_map, listen_conf)
            else:
                domains = get.webname.strip().split(',')
                map_tmp = '\tmap\t{d} {d}'.format(d=domains[0])
                listen_rep = "secure\s*0"
                listen_conf = re.sub(listen_rep, "secure 0\n" + map_tmp, listen_conf)
        else:
            listen_conf = """
listener Default%s{
    address *:%s
    secure 0
    map %s %s
}
""" % (get.port, get.port, get.webname, get.domain)
        # 保存配置文件
        public.writeFile(listen_file, listen_conf)
        return True

    # Nginx写域名配置
    def NginxDomain(self, get):
        file = self.setupPath + '/panel/vhost/nginx/' + str(get.webname) + '.conf'
        conf = public.readFile(file)
        if not isinstance(conf, str):
            return None
        rep_server_name = re.compile(r"\s*server_name\s*(.*);[^\n]*\n", re.M)
        rep_port = re.compile(r"\s*listen\s+[\[\]:]*(?P<port>[0-9]+).*;[^\n]*\n", re.M)

        if not (rep_server_name.search(conf) and rep_port.search(conf)):
            return None

        # 添加域名
        rep = r"server_name\s*(.*);"
        tmp = re.search(rep, conf).group()
        domains = tmp.replace(';', '').strip().split(' ')
        if not public.inArray(domains, get.domain):
            newServerName = tmp.replace(';', ' ' + get.domain + ';')
            conf = conf.replace(tmp, newServerName)

        # 添加端口
        rep = r"listen\s+[\[\]\:]*([0-9]+).*;"
        tmp = re.findall(rep, conf)
        if not public.inArray(tmp, get.port):
            listen = re.search(rep, conf).group()
            listen_ipv6 = ''
            if self.is_ipv6: listen_ipv6 = "\n\t\tlisten [::]:" + get.port + ';'
            conf = conf.replace(listen, listen + "\n\t\tlisten " + get.port + ';' + listen_ipv6)
        # 保存配置文件
        public.writeFile(file, conf)
        return True

    # Apache写域名配置
    def ApacheDomain(self, get):
        file = self.setupPath + '/panel/vhost/apache/' + get.webname + '.conf'
        conf = public.readFile(file)
        if not conf: return

        port = get.port
        siteName = get.webname
        newDomain = get.domain
        find = public.M('sites').where("id=?", (get.id,)).field('id,name,path').find()
        sitePath = find['path']
        siteIndex = 'index.php index.html index.htm default.php default.html default.htm'

        # 添加域名
        if conf.find('<VirtualHost *:' + port + '>') != -1:
            repV = r"<VirtualHost\s+\*\:" + port + ">(.|\n)*</VirtualHost>"
            domainV = re.search(repV, conf).group()
            rep = r"ServerAlias\s*(.*)\n"
            tmp = re.search(rep, domainV).group(0)
            domains = tmp.strip().split(' ')
            if not public.inArray(domains, newDomain):
                rs = tmp.replace("\n", "")
                newServerName = rs + ' ' + newDomain + "\n"
                myconf = domainV.replace(tmp, newServerName)
                conf = re.sub(repV, myconf, conf)
            if conf.find('<VirtualHost *:443>') != -1:
                repV = r"<VirtualHost\s+\*\:443>(.|\n)*</VirtualHost>"
                domainV = re.search(repV, conf).group()
                rep = r"ServerAlias\s*(.*)\n"
                tmp = re.search(rep, domainV).group(0)
                domains = tmp.strip().split(' ')
                if not public.inArray(domains, newDomain):
                    rs = tmp.replace("\n", "")
                    newServerName = rs + ' ' + newDomain + "\n"
                    myconf = domainV.replace(tmp, newServerName)
                    conf = re.sub(repV, myconf, conf)
        else:
            try:
                httpdVersion = public.readFile(self.setupPath + '/apache/version.pl').strip()
            except:
                httpdVersion = ""
            if httpdVersion == '2.2':
                vName = ''
                if self.sitePort != '80' and self.sitePort != '443':
                    vName = "NameVirtualHost  *:" + port + "\n"
                phpConfig = ""
                apaOpt = "Order allow,deny\n\t\tAllow from all"
            else:
                vName = ""
                # rep = "php-cgi-([0-9]{2,3})\.sock"
                # version = re.search(rep,conf).groups()[0]
                version = public.get_php_version_conf(conf)
                if len(version) < 2: return public.returnMsg(False, 'PHP_GET_ERR')
                phpConfig = '''
    #PHP
    <FilesMatch \\.php$>
            SetHandler "proxy:%s"
    </FilesMatch>
    ''' % (public.get_php_proxy(version, 'apache'),)
                apaOpt = 'Require all granted'

            newconf = '''<VirtualHost *:%s>
    ServerAdmin webmaster@example.com
    DocumentRoot "%s"
    ServerName %s.%s
    ServerAlias %s
    IncludeOptional /www/server/panel/vhost/apache/extension/%s/*.conf
    #errorDocument 404 /404.html
    ErrorLog "%s-error_log"
    CustomLog "%s-access_log" combined
    %s

    #DENY FILES
     <Files ~ (\.user.ini|\.htaccess|\.git|\.env|\.svn|\.project|LICENSE|README.md)$>
       Order allow,deny
       Deny from all
    </Files>

    #PATH
    <Directory "%s">
        SetOutputFilter DEFLATE
        Options FollowSymLinks
        AllowOverride All
        %s
        DirectoryIndex %s
    </Directory>
</VirtualHost>''' % (
                port, sitePath, siteName, port, newDomain, siteName,
                public.GetConfigValue('logs_path') + '/' + siteName,
                public.GetConfigValue('logs_path') + '/' + siteName, phpConfig, sitePath, apaOpt,
                siteIndex)
            conf += "\n\n" + newconf
            ext_path = "/www/server/panel/vhost/apache/extension/%s/" % self.siteName
            if not os.path.isdir(ext_path):
                os.makedirs(ext_path)

        # 添加端口
        if port != '80' and port != '888': self.apacheAddPort(port)

        # 保存配置文件
        public.writeFile(file, conf)
        return True

    def delete_domain_multiple(self, get):
        '''
            @name 批量删除网站
            @author zhwen<2020-11-17>
            @param id "1"
            @param domains_id 1,2,3
        '''
        domains_id = get.domains_id.split(',')
        get.webname = public.M('sites').where("id=?", (get.id,)).getField('name')
        del_successfully = []
        del_failed = {}
        for domain_id in domains_id:
            get.domain = public.M('domain').where("id=? and pid=?", (domain_id, get.id)).getField('name')
            get.port = str(public.M('domain').where("id=? and pid=?", (domain_id, get.id)).getField('port'))
            if not get.webname:
                continue
            if not get.domain:
                continue
            try:
                result = self.DelDomain(get, multiple=1)
                tmp = get.domain + ':' + get.port
                if not result['status']:
                    del_failed[tmp] = result['msg']
                    continue
                del_successfully.append(tmp)
            except:
                tmp = get.domain + ':' + get.port
                del_failed[tmp] = '删除时错误了，请再试一次'
                pass
        public.serviceReload()
        return {'status': True, 'msg': '删除域名 [ {} ] 成功'.format(','.join(del_successfully)), 'error': del_failed,
                'success': del_successfully}

    # 删除域名
    def DelDomain(self, get, multiple=None):
        if not 'id' in get: return public.returnMsg(False, '请选择域名')
        if not 'port' in get: return public.returnMsg(False, '请选择端口')
        sql = public.M('domain')
        id = get['id']
        port = get.port
        find = sql.where("pid=? AND name=? AND port=?", (get.id, get.domain, get.port)).field('id,name').find()
        if not find:
            return public.returnMsg(False, "未查询到指定域名，无法删除")
        domains = public.M('domain').where("pid=?", (id,)).field("id,name,port").select()
        if len(domains) == 1:
            return public.returnMsg(False, 'SITE_DEL_DOMAIN_ERR_ONLY')

        other_domains = [i for i in domains if i["id"] != find["id"]]

        # nginx
        file = self.setupPath + '/panel/vhost/nginx/' + get['webname'] + '.conf'
        conf = public.readFile(file)
        if conf:
            # 删除域名
            has_server_name = False
            rep = r"server_name\s+(.+);?"
            tmp = re.search(rep, conf)
            if tmp:
                has_server_name = True
                tmp_data = tmp.group()
                # newServerName = tmp.replace(' ' + get['domain'] + ';', ';')
                # newServerName = newServerName.replace(' ' + get['domain'] + ' ', ' ')
                newServerName = "server_name " + " ".join(set([i["name"] for i in other_domains])) + ";"
                conf = conf.replace(tmp_data, newServerName)

            # 删除端口
            rep = r"listen.*[\s:]+(\d+).*;"
            tmp = re.findall(rep, conf)
            port_count = public.M('domain').where('pid=? AND port=?', (get.id, get.port)).count()
            if public.inArray(tmp, port) == True and port_count < 2:
                rep = r"\n*\s+listen.*[\s:]+" + port + r"\s*;"
                conf = re.sub(rep, '', conf)
            if not has_server_name:
                last = None
                for i in re.finditer(r"\n*\s+listen.*[\s:]+(\d+)\s*;", conf):
                    last = i
                if last:
                    s_name = "\n    server_name " + " ".join(set([i["name"] for i in other_domains])) + ";"
                    conf = conf[:last.end()] + s_name + conf[last.end():]

            # 保存配置
            public.writeFile(file, conf.strip())

        # apache
        file = self.setupPath + '/panel/vhost/apache/' + get['webname'] + '.conf'
        conf = public.readFile(file)
        if conf:
            # 删除域名
            try:
                rep = r"\n*<VirtualHost \*\:" + port + ">(.|\n){500,1500}</VirtualHost>"
                tmp = re.search(rep, conf).group()

                rep1 = "ServerAlias\s+(.+)\n"
                tmp1 = re.findall(rep1, tmp)
                tmp2 = tmp1[0].split(' ')
                if len(tmp2) < 2:
                    conf = re.sub(rep, '', conf)
                    rep = "NameVirtualHost.+\:" + port + "\n"
                    conf = re.sub(rep, '', conf)
                else:
                    newServerName = tmp.replace(' ' + get['domain'] + "\n", "\n")
                    newServerName = newServerName.replace(' ' + get['domain'] + ' ', ' ')
                    conf = conf.replace(tmp, newServerName)
                # 保存配置
                public.writeFile(file, conf.strip())
            except:
                pass

        # openlitespeed
        self._del_ols_domain(get)

        public.M('domain').where("id=?", (find['id'],)).delete()
        public.WriteLog('TYPE_SITE', 'DOMAIN_DEL_SUCCESS', (get.webname, get.domain))
        if not multiple:
            public.serviceReload()
        return public.returnMsg(True, 'DEL_SUCCESS')

    # openlitespeed删除域名
    def _del_ols_domain(self, get):
        conf_dir = '/www/server/panel/vhost/openlitespeed/listen/'
        if not os.path.exists(conf_dir):
            return False
        for i in os.listdir(conf_dir):
            file_name = conf_dir + i
            if os.path.isdir(file_name):
                continue
            conf = public.readFile(file_name)
            map_rep = 'map\s+{}\s+(.*)'.format(get.webname)
            domains = re.search(map_rep, conf)
            if domains:
                domains = domains.group(1).split(',')
                if get.domain in domains:
                    domains.remove(get.domain)
                if len(domains) == 0:
                    os.remove(file_name)
                    continue
                else:
                    domains = ",".join(domains)
                    map_c = "map\t{} ".format(get.webname) + domains
                    conf = re.sub(map_rep, map_c, conf)
            public.writeFile(file_name, conf)

    # 检查域名是否解析
    def CheckDomainPing(self, get):
        try:
            epass = public.GetRandomString(32)
            spath = get.path + '/.well-known/pki-validation'
            if not os.path.exists(spath): public.ExecShell("mkdir -p '" + spath + "'")
            public.writeFile(spath + '/fileauth.txt', epass)
            result = public.httpGet('http://' + get.domain.replace('*.', '') + '/.well-known/pki-validation/fileauth.txt')
            if result == epass: return True
            return False
        except:
            return False

    def analyze_ssl(self, csr):
        issuer_dic = {}
        try:
            from cryptography import x509
            from cryptography.hazmat.backends import default_backend
            cert = x509.load_pem_x509_certificate(csr.encode("utf-8"), default_backend())
            issuer = cert.issuer
            for i in issuer:
                issuer_dic[i.oid._name] = i.value
        except:
            pass
        return issuer_dic

    # 保存第三方证书
    def SetSSL(self, get):
        import ssl_info
        ssl_info = ssl_info.ssl_info()

        get.key = get.key.strip()
        get.csr = get.csr.strip()

        issuer = self.analyze_ssl(get.csr)
        if issuer.get("organizationName") == "Let's Encrypt":
            get.csr += "\n"

        siteName = get.siteName
        path = '/www/server/panel/vhost/cert/' + siteName
        csrpath = path + "/fullchain.pem"
        keypath = path + "/privkey.pem"

        if (get.key.find('KEY') == -1): return public.returnMsg(False, 'SITE_SSL_ERR_PRIVATE')
        if (get.csr.find('CERTIFICATE') == -1): return public.returnMsg(False, 'SITE_SSL_ERR_CERT')
        public.writeFile('/tmp/cert.pl', get.csr)
        if not public.CheckCert('/tmp/cert.pl'): return public.returnMsg(False, '证书错误,请粘贴正确的PEM格式证书!')
        # 验证证书和密钥是否匹配格式是否为pem
        check_flag, check_msg = ssl_info.verify_certificate_and_key_match(get.key, get.csr)
        if not check_flag: return public.returnMsg(False, check_msg)
        # 验证证书链是否完整
        check_chain_flag, check_chain_msg = ssl_info.verify_certificate_chain(get.csr)
        if not check_chain_flag: return public.returnMsg(False, check_chain_msg)
        backup_cert = '/tmp/backup_cert_' + siteName

        import shutil
        if os.path.exists(backup_cert): shutil.rmtree(backup_cert)
        if os.path.exists(path): shutil.move(path, backup_cert)
        if os.path.exists(path): shutil.rmtree(path)

        public.ExecShell('mkdir -p ' + path)
        public.writeFile(keypath, get.key)
        public.writeFile(csrpath, get.csr)

        # 写入配置文件
        result = self.SetSSLConf(get)
        if not result['status']: return result
        isError = public.checkWebConfig()

        if (type(isError) == str):
            if os.path.exists(path):
                shutil.rmtree(path)
            if os.path.exists(backup_cert):
                shutil.move(backup_cert, path)
            return public.returnMsg(False, 'ERROR: <br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')
        public.serviceReload()

        if os.path.exists(path + '/partnerOrderId'): os.remove(path + '/partnerOrderId')
        if os.path.exists(path + '/certOrderId'): os.remove(path + '/certOrderId')
        p_file = '/etc/letsencrypt/live/' + get.siteName
        if os.path.exists(p_file): shutil.rmtree(p_file)
        public.WriteLog('TYPE_SITE', 'SITE_SSL_SAVE_SUCCESS')

        # 清理备份证书
        if os.path.exists(backup_cert): shutil.rmtree(backup_cert)
        return public.returnMsg(True, 'SITE_SSL_SUCCESS')

    # 获取运行目录
    def GetRunPath(self, get):
        if not hasattr(get, 'id'):
            if hasattr(get, 'siteName'):
                get.id = public.M('sites').where('name=?', (get.siteName,)).getField('id')
            else:
                get.id = public.M('sites').where('path=?', (get.path,)).getField('id')
        if not get.id: return False
        if type(get.id) == list: get.id = get.id[0]['id']
        result = self.GetSiteRunPath(get)
        if 'runPath' in result:
            return result['runPath']
        return False

    # 创建Let's Encrypt免费证书
    def CreateLet(self, get):

        domains = json.loads(get.domains)
        if not len(domains):
            return public.returnMsg(False, '请选择域名')

        file_auth = True
        if hasattr(get, 'dnsapi'):
            file_auth = False

        if not hasattr(get, 'dnssleep'):
            get.dnssleep = 10

        email = public.M('users').getField('email')
        if hasattr(get, 'email'):
            if get.email.find('@') == -1:
                get.email = email
            else:
                get.email = get.email.strip()
                public.M('users').where('id=?', (1,)).setField('email', get.email)
        else:
            get.email = email

        for domain in domains:
            if public.checkIp(domain): continue
            if domain.find('*.') >= 0 and file_auth:
                return public.returnMsg(False, '泛域名不能使用【文件验证】的方式申请证书!')

        if file_auth:
            get.sitename = get.siteName
            if self.GetRedirectList(get): return public.returnMsg(False, 'SITE_SSL_ERR_301')
            if self.GetProxyList(get): return public.returnMsg(False, '已开启反向代理的站点无法申请SSL!')
            data = self.get_site_info(get.siteName)
            get.id = data['id']
            runPath = self.GetRunPath(get)
            if runPath != '/':
                if runPath[:1] != '/': runPath = '/' + runPath
            else:
                runPath = ''
            get.site_dir = data['path'] + runPath

        else:
            dns_api_list = self.GetDnsApi(get)
            get.dns_param = None
            for dns in dns_api_list:
                if dns['name'] == get.dnsapi:
                    param = []
                    if not dns['data']: continue
                    for val in dns['data']:
                        param.append(val['value'])
                    get.dns_param = '|'.join(param)
            n_list = ['dns', 'dns_bt']
            if not get.dnsapi in n_list:
                if len(get.dns_param) < 16: return public.returnMsg(False, '请先设置【%s】的API接口参数.' % get.dnsapi)
            if get.dnsapi == 'dns_bt':
                if not os.path.exists('plugin/dns/dns_main.py'):
                    return public.returnMsg(False, '请先到软件商店安装【云解析】，并完成域名NS绑定.')

        self.check_ssl_pack()

        try:
            import panelLets
            public.mod_reload(panelLets)
        except Exception as ex:
            if str(ex).find('No module named requests') != -1:
                public.ExecShell("pip install requests &")
                return public.returnMsg(False, '缺少requests组件，请尝试修复面板!')
            return public.returnMsg(False, str(ex))

        lets = panelLets.panelLets()
        result = lets.apple_lest_cert(get)
        if result['status'] and not 'code' in result:
            get.onkey = 1
            path = '/www/server/panel/cert/' + get.siteName
            if os.path.exists(path + '/certOrderId'): os.remove(path + '/certOrderId')
            result = self.SetSSLConf(get)
        return result

    def get_site_info(self, siteName):
        data = public.M("sites").where('name=?', siteName).field('id,path,name').find()
        return data

    # 检测依赖库
    def check_ssl_pack(self):
        try:
            import requests
        except:
            public.ExecShell('pip install requests')
        try:
            import OpenSSL
        except:
            public.ExecShell('pip install pyopenssl')

    # 判断DNS-API是否设置
    def Check_DnsApi(self, dnsapi):
        dnsapis = self.GetDnsApi(None)
        for dapi in dnsapis:
            if dapi['name'] == dnsapi:
                if not dapi['data']: return True
                for d in dapi['data']:
                    if d['key'] == '': return False
        return True

    # 获取DNS-API列表
    def GetDnsApi(self, get):
        api_path = './config/dns_api.json'
        api_init = './config/dns_api_init.json'
        import shutil, json
        try:
            apis = json.loads(public.ReadFile(api_path))
        except:
            os.remove(api_path)
            shutil.copyfile(api_init, api_path)
            apis = json.loads(public.ReadFile(api_path))

        path = '/root/.acme.sh'
        if not os.path.exists(path + '/account.conf'): path = "/.acme.sh"
        account = public.readFile(path + '/account.conf')
        if not account: account = ''
        is_write = False
        for i in range(len(apis)):
            if not apis[i]['data']: continue
            for j in range(len(apis[i]['data'])):
                if apis[i]['data'][j]['value']: continue
                match = re.search(apis[i]['data'][j]['key'] + "\s*=\s*'(.+)'", account)
                if match: apis[i]['data'][j]['value'] = match.groups()[0]
                if apis[i]['data'][j]['value']: is_write = True
        if is_write: public.writeFile('./config/dns_api.json', json.dumps(apis))
        result = []
        for i in apis:
            if i['name'] == 'Dns_com': continue
            result.insert(0, i)
        return result

        # api_path = './config/dns_api.json'
        # api_init = './config/dns_api_init_v2.json'
        # apis = json.loads(public.ReadFile(api_init))

        # from panelDnsapi import DnsMager

        # m = DnsMager()
        # result = []
        # for data in apis:
        #     if data["name"] == "dns":
        #         result.append(data)
        #         continue
        #     if data["name"] in m.CLS_MAP:
        #         conf_list = m.config.get(data["name"], None)
        #         tmp = []
        #         if conf_list:
        #             for conf in conf_list:
        #                 tmp_dict = {
        #                     "ps": conf.pop("ps", ""),
        #                     "domains": conf.pop("domains", []),
        #                     "id": conf.pop("id")
        #                 }
        #                 for table in data["add_table"]:
        #                     if table["fields"][0] in conf:
        #                         tmp_dict["conf"] = [{"name": f, "value": conf.get(f, "")} for f in table["fields"]]
        #                 if "conf" in tmp_dict:
        #                     tmp.append(tmp_dict)
        #         data["data"] = tmp
        #         result.append(data)

        # return result

    @staticmethod
    def add_dns_api(get):
        try:
            dns_type = get.dns_type.strip()
            ps = get.ps.strip()
            conf_data = json.loads(get.pdata.strip())
            domains = json.loads(get.domains.strip())
            force_domain = None
            if "force_domain" in get:
                force_domain = get.force_domain.strip()
        except (json.JSONDecodeError, AttributeError, KeyError):
            return public.returnMsg(False, "参数错误")
        from panelDnsapi import DnsMager

        res = DnsMager().add_conf(dns_type, conf_data, ps, domains, force_domain)
        return public.returnMsg(*res)

    @staticmethod
    def set_dns_api(get):
        try:
            dns_type = get.dns_type.strip()
            api_id = get.api_id.strip()
            ps = None
            conf_data = None
            domains = None
            force_domain = None
            if "ps" in get:
                ps = get.ps.strip()
            if "force_domain" in get:
                force_domain = get.force_domain.strip()
            if "pdata" in get:
                conf_data = json.loads(get.pdata.strip())
            if "domains" in get:
                domains = json.loads(get.domains.strip())
        except (json.JSONDecodeError, AttributeError, KeyError):
            return public.returnMsg(False, "参数错误")
        try:
            from panelDnsapi import DnsMager
            res = DnsMager().modify_conf(api_id, dns_type, conf_data, ps, domains, force_domain)
            return public.returnMsg(*res)
        except:
            public.print_log(public.get_error_info())

    @staticmethod
    def remove_dns_api(get):
        try:
            dns_type = get.dns_type.strip()
            api_id = get.api_id.strip()
        except (json.JSONDecodeError, AttributeError, KeyError):
            return public.returnMsg(False, "参数错误")
        from panelDnsapi import DnsMager
        res = DnsMager().remove_conf(api_id, dns_type)
        return public.returnMsg(*res)

    @staticmethod
    def test_domains_api(get):
        try:
            domains = json.loads(get.domains.strip())
        except (json.JSONDecodeError, AttributeError, KeyError):
            return public.returnMsg(False, "参数错误")
        try:
            from panelDnsapi import DnsMager
            return DnsMager().test_domains_api(domains)
        except:
            public.print_log(public.get_error_info())

    # 设置DNS-API
    def SetDnsApi(self, get):
        pdata = json.loads(get.pdata)
        apis = json.loads(public.ReadFile('./config/dns_api.json'))
        is_write = False
        for key in pdata.keys():
            for i in range(len(apis)):
                if not apis[i]['data']: continue
                for j in range(len(apis[i]['data'])):
                    if apis[i]['data'][j]['key'] != key: continue
                    apis[i]['data'][j]['value'] = pdata[key]
                    is_write = True

        if is_write: public.writeFile('./config/dns_api.json', json.dumps(apis))
        return public.returnMsg(True, "设置成功!")

    # 获取站点所有域名
    def GetSiteDomains(self, get):
        data = {}

        n_list = []
        from sslModel import dataModel
        get.site_id = get.id
        dns_data = dataModel.main().get_domain_dns_config(get)
        for domain in dns_data:
            tmp = {'id': domain['domain_id'], 'name': domain['name'], 'binding': False, 'apply_ssl': 1, 'dns_status': domain['status'], 'root_domain_id': domain['domain_id']}
            if public.checkIp(domain['name']): tmp['apply_ssl'] = 0
            n_list.append(tmp)

        # binding = public.M('binding').where('pid=?', (get.id,)).field('domain,id').select()
        # for b in binding:
        #     tmp = {'id': b['id'], 'name': b['domain'],'binding':True, 'apply_ssl': 1}
        #     if public.checkIp(b['domain']):  tmp['apply_ssl'] = 0
        #
        #     n_list.append(tmp)
        n_list = sorted(n_list, key=lambda x: x['apply_ssl'], reverse=True)
        data['domains'] = n_list
        data['email'] = public.M('users').where('id=?', (1,)).getField('email')
        if data['email'] == public.en_hexb('4d6a67334f5459794e545932514846784c6d4e7662513d3d'): data['email'] = ''
        return data
    def GetFormatSSLResult(self, result):
        try:
            import re
            rep = "\s*Domain:.+\n\s+Type:.+\n\s+Detail:.+"
            tmps = re.findall(rep, result)

            statusList = []
            for tmp in tmps:
                arr = tmp.strip().split('\n')
                status = {}
                for ar in arr:
                    tmp1 = ar.strip().split(':')
                    status[tmp1[0].strip()] = tmp1[1].strip()
                    if len(tmp1) > 2:
                        status[tmp1[0].strip()] = tmp1[1].strip() + ':' + tmp1[2]
                statusList.append(status)
            return statusList
        except:
            return None

    # 获取TLS1.3标记
    def get_tls13(self):
        nginx_bin = '/www/server/nginx/sbin/nginx'
        nginx_v = public.ExecShell(nginx_bin + ' -V 2>&1')[0]
        nginx_v_re = re.findall("nginx/(\d\.\d+).+OpenSSL\s+(\d\.\d+)", nginx_v, re.DOTALL)
        if nginx_v_re:
            if nginx_v_re[0][0] in ['1.8', '1.9', '1.7', '1.6', '1.5', '1.4']:
                return ''
            if float(nginx_v_re[0][0]) >= 1.15 and float(nginx_v_re[0][-1]) >= 1.1:
                return ' TLSv1.3'
        else:
            _v = re.search('nginx/1\.1(5|6|7|8|9).\d', nginx_v)
            if not _v:
                _v = re.search('nginx/1\.2\d\.\d', nginx_v)
            openssl_v = public.ExecShell(nginx_bin + ' -V 2>&1|grep OpenSSL')[0].find('OpenSSL 1.1.') != -1
            if _v and openssl_v:
                return ' TLSv1.3'
        return ''

    # 获取apache反向代理
    def get_apache_proxy(self, conf):
        rep = "\n*#引用反向代理规则，注释后配置的反向代理将无效\n+\s+IncludeOptiona.*"
        proxy = re.search(rep, conf)
        if proxy:
            return proxy.group()
        return ""

    def _get_site_domains(self, sitename):
        site_id = public.M('sites').where('name=?', (sitename,)).field('id').find()
        domains = public.M('domain').where('pid=?', (site_id['id'],)).field('name').select()
        domains = [d['name'] for d in domains]
        return domains

    # 设置OLS ssl
    def set_ols_ssl(self, get, siteName):
        listen_conf = self.setupPath + '/panel/vhost/openlitespeed/listen/443.conf'
        conf = public.readFile(listen_conf)
        ssl_conf = """
        vhssl {
          keyFile                 /www/server/panel/vhost/cert/BTDOMAIN/privkey.pem
          certFile                /www/server/panel/vhost/cert/BTDOMAIN/fullchain.pem
          certChain               1
          sslProtocol             24
          ciphers                 EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH:ECDHE-RSA-AES128-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA128:DHE-RSA-AES128-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES128-GCM-SHA128:ECDHE-RSA-AES128-SHA384:ECDHE-RSA-AES128-SHA128:ECDHE-RSA-AES128-SHA:ECDHE-RSA-AES128-SHA:DHE-RSA-AES128-SHA128:DHE-RSA-AES128-SHA128:DHE-RSA-AES128-SHA:DHE-RSA-AES128-SHA:ECDHE-RSA-DES-CBC3-SHA:EDH-RSA-DES-CBC3-SHA:AES128-GCM-SHA384:AES128-GCM-SHA128:AES128-SHA128:AES128-SHA128:AES128-SHA:AES128-SHA:DES-CBC3-SHA:HIGH:!aNULL:!eNULL:!EXPORT:!DES:!MD5:!PSK:!RC4
          enableECDHE             1
          renegProtection         1
          sslSessionCache         1
          enableSpdy              15
          enableStapling           1
          ocspRespMaxAge           86400
        }
        """
        ssl_dir = self.setupPath + '/panel/vhost/openlitespeed/detail/ssl/'
        if not os.path.exists(ssl_dir):
            os.makedirs(ssl_dir)
        ssl_file = ssl_dir + '{}.conf'.format(siteName)
        if not os.path.exists(ssl_file):
            ssl_conf = ssl_conf.replace('BTDOMAIN', siteName)
            public.writeFile(ssl_file, ssl_conf, "a+")
        include_ssl = '\ninclude {}'.format(ssl_file)
        detail_file = self.setupPath + '/panel/vhost/openlitespeed/detail/{}.conf'.format(siteName)
        public.writeFile(detail_file, include_ssl, 'a+')
        if not conf:
            conf = """
listener SSL443 {
  map                     BTSITENAME BTDOMAIN
  address                 *:443
  secure                  1
  keyFile                 /www/server/panel/vhost/cert/BTSITENAME/privkey.pem
  certFile                /www/server/panel/vhost/cert/BTSITENAME/fullchain.pem
  certChain               1
  sslProtocol             24
  ciphers                 EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH:ECDHE-RSA-AES128-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA128:DHE-RSA-AES128-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES128-GCM-SHA128:ECDHE-RSA-AES128-SHA384:ECDHE-RSA-AES128-SHA128:ECDHE-RSA-AES128-SHA:ECDHE-RSA-AES128-SHA:DHE-RSA-AES128-SHA128:DHE-RSA-AES128-SHA128:DHE-RSA-AES128-SHA:DHE-RSA-AES128-SHA:ECDHE-RSA-DES-CBC3-SHA:EDH-RSA-DES-CBC3-SHA:AES128-GCM-SHA384:AES128-GCM-SHA128:AES128-SHA128:AES128-SHA128:AES128-SHA:AES128-SHA:DES-CBC3-SHA:HIGH:!aNULL:!eNULL:!EXPORT:!DES:!MD5:!PSK:!RC4
  enableECDHE             1
  renegProtection         1
  sslSessionCache         1
  enableSpdy              15
  enableStapling           1
  ocspRespMaxAge           86400
}
"""

        else:
            rep = 'listener\s*SSL443\s*{'
            map = '\n  map {s} {s}'.format(s=siteName)
            conf = re.sub(rep, 'listener SSL443 {' + map, conf)
        domain = ",".join(self._get_site_domains(siteName))
        conf = conf.replace('BTSITENAME', siteName).replace('BTDOMAIN', domain)
        public.writeFile(listen_conf, conf)

    def _get_ap_static_security(self, ap_conf):
        if not ap_conf: return ''
        ap_static_security = re.search('#SECURITY-START(.|\n)*#SECURITY-END', ap_conf)
        if ap_static_security:
            return ap_static_security.group()
        return ''

    # 添加SSL配置
    def SetSSLConf(self, get):
        """
        @name 兼容批量设置
        @auther hezhihong
        """
        siteName = get.siteName
        if not 'first_domain' in get: get.first_domain = siteName
        if 'isBatch' in get and siteName != get.first_domain: get.first_domain = siteName

        # Nginx配置
        file = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'

        # Node项目
        if not os.path.exists(file):  file = self.setupPath + '/panel/vhost/nginx/node_' + siteName + '.conf'
        if not os.path.exists(file):  file = self.setupPath + '/panel/vhost/nginx/java_' + siteName + '.conf'
        if not os.path.exists(file):  file = self.setupPath + '/panel/vhost/nginx/go_' + siteName + '.conf'
        if not os.path.exists(file):  file = self.setupPath + '/panel/vhost/nginx/other_' + siteName + '.conf'
        if not os.path.exists(file):  file = self.setupPath + '/panel/vhost/nginx/python_' + siteName + '.conf'
        if not os.path.exists(file):  file = self.setupPath + '/panel/vhost/nginx/net_' + siteName + '.conf'
        if not os.path.exists(file):  file = self.setupPath + '/panel/vhost/nginx/html_' + siteName + '.conf'
        ng_file = file
        ng_conf = public.readFile(file)
        have_nginx_conf = ng_conf is not False

        # 是否为子目录设置SSL
        # if hasattr(get,'binding'):
        #    allconf = conf;
        #    conf = re.search("#BINDING-"+get.binding+"-START(.|\n)*#BINDING-"+get.binding+"-END",conf).group()

        if ng_conf:
            if ng_conf.find('ssl_certificate') == -1:
                http3_header = '''\n    add_header Alt-Svc 'quic=":443"; h3=":443"; h3-29=":443"; h3-27=":443";h3-25=":443"; h3-T050=":443"; h3-Q050=":443";h3-Q049=":443";h3-Q048=":443"; h3-Q046=":443"; h3-Q043=":443"';'''
                if not self.is_nginx_http3():
                    http3_header = ""
                sslStr = """#error_page 404/404.html;
    ssl_certificate    /www/server/panel/vhost/cert/%s/fullchain.pem;
    ssl_certificate_key    /www/server/panel/vhost/cert/%s/privkey.pem;
    ssl_protocols %s;
    ssl_ciphers EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_tickets on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    add_header Strict-Transport-Security "max-age=31536000";%s
    error_page 497  https://$host$request_uri;
""" % (get.first_domain, get.first_domain, self.get_tls_protocol(self.get_tls13(), is_apache=False), http3_header)
                if (ng_conf.find('ssl_certificate') != -1):
                    if 'isBatch' not in get:
                        public.serviceReload()
                        return public.returnMsg(True, 'SITE_SSL_OPEN_SUCCESS')
                    else:
                        return True

                if ng_conf.find('#error_page 404/404.html;') == -1:
                    return public.returnMsg(False, "站点配置文件中未找到标识信息【#error_page 404/404.html;】，"
                                                   "无法确定SSL配置添加位置，请尝试手动添加标识或恢复配置文件")

                ng_conf = ng_conf.replace('#error_page 404/404.html;', sslStr)
                conf = re.sub(r"\s+\#SSL\-END", "\n\t\t#SSL-END", ng_conf)

                # 添加端口
                rep = "listen.*[\s:]+(\d+).*;"
                tmp = re.findall(rep, ng_conf)
                if not public.inArray(tmp, '443'):
                    listen_re = re.search(rep, ng_conf)
                    if not listen_re:
                        ng_conf = re.sub(r"server\s*{\s*", "server\n{\n\t\tlisten 80;\n\t\t", ng_conf)
                        listen_re = re.search(rep, ng_conf)
                    listen = listen_re.group()
                    nginx_ver = public.nginx_version()
                    default_site = ''
                    if ng_conf.find('default_server') != -1:
                        default_site = ' default_server'

                    listen_add_str = []
                    if nginx_ver:
                        port_str = ["443"]
                        if self.is_ipv6:
                            port_str.append("[::]:443")
                        use_http2_on = False
                        for p in port_str:
                            listen_add_str.append("\n    listen {} ssl".format(p))
                            if nginx_ver < [1, 9, 5]:
                                listen_add_str.append(default_site + ";")
                            elif [1, 9, 5] <= nginx_ver < [1, 25, 1]:
                                listen_add_str.append(" http2 " + default_site + ";")
                            else:  # >= [1, 25, 1]
                                listen_add_str.append(default_site + ";")
                                use_http2_on = True

                            if self.is_nginx_http3():
                                listen_add_str.append("\n    listen {} quic;".format(p))
                        if use_http2_on:
                            listen_add_str.append("\n    http2 on;")

                    else:
                        listen_add_str.append("\n    listen 443 ssl " + default_site + ";")
                    listen_add_str_data = "".join(listen_add_str)
                    ng_conf = ng_conf.replace(listen, listen + listen_add_str_data)

        # Apache配置
        file = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
        other_project = ""
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/apache/node_' + siteName + '.conf'
            other_project = "node"

        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/apache/java_' + siteName + '.conf'
            other_project = "java"

        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/apache/go_' + siteName + '.conf'
            other_project = "go"

        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/apache/other_' + siteName + '.conf'
            other_project = "other"

        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/apache/python_' + siteName + '.conf'
            other_project = "python"

        if not os.path.exists(file):
            other_project = "net"
            file = self.setupPath + '/panel/vhost/apache/net_' + siteName + '.conf'

        if not os.path.exists(file):
            other_project = "html"
            file = self.setupPath + '/panel/vhost/apache/html_' + siteName + '.conf'

        ap_conf = public.readFile(file)
        have_apache_conf = ap_conf is not False
        ap_static_security = self._get_ap_static_security(ap_conf)
        if ap_conf:
            ap_proxy = self.get_apache_proxy(ap_conf)
            if ap_conf.find('SSLCertificateFile') == -1 and ap_conf.find('VirtualHost') != -1:
                find = public.M('sites').where("name=?", (siteName,)).field('id,path').find()
                tmp = public.M('domain').where('pid=?', (find['id'],)).field('name').select()
                domains = ''
                for key in tmp:
                    domains += key['name'] + ' '
                path = (find['path'] + '/' + self.GetRunPath(get)).replace('//', '/')
                index = 'index.php index.html index.htm default.php default.html default.htm'

                try:
                    httpdVersion = public.readFile(self.setupPath + '/apache/version.pl').strip()
                except:
                    httpdVersion = ""
                if httpdVersion == '2.2':
                    vName = ""
                    phpConfig = ""
                    apaOpt = "Order allow,deny\n\t\tAllow from all"
                else:
                    vName = ""
                    # rep = r"php-cgi-([0-9]{2,3})\.sock"
                    # version = re.search(rep, conf).groups()[0]
                    version = public.get_php_version_conf(ap_conf)
                    if len(version) < 2:
                        if 'isBatch' not in get:
                            return public.returnMsg(False, 'PHP_GET_ERR')
                        else:
                            return False
                    phpConfig = '''
    #PHP
    <FilesMatch \\.php$>
            SetHandler "proxy:%s"
    </FilesMatch>
    ''' % (public.get_php_proxy(version, 'apache'),)
                    apaOpt = 'Require all granted'

                sslStr = '''%s<VirtualHost *:443>
    ServerAdmin webmaster@example.com
    DocumentRoot "%s"
    ServerName SSL.%s
    ServerAlias %s
    #errorDocument 404 /404.html
    ErrorLog "%s-error_log"
    CustomLog "%s-access_log" combined
    %s
    #SSL
    SSLEngine On
    SSLCertificateFile /www/server/panel/vhost/cert/%s/fullchain.pem
    SSLCertificateKeyFile /www/server/panel/vhost/cert/%s/privkey.pem
    SSLCipherSuite EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5:ALL:!ADH:!EXPORT56:RC4+RSA:+HIGH:+MEDIUM:+LOW:+SSLv2:+EXP:+eNULL
    SSLProtocol All -SSLv2 -SSLv3 %s
    SSLHonorCipherOrder On
    %s
    %s

    #DENY FILES
     <Files ~ (\.user.ini|\.htaccess|\.git|\.env|\.svn|\.project|LICENSE|README.md)$>
       Order allow,deny
       Deny from all
    </Files>

    #PATH
    <Directory "%s">
        SetOutputFilter DEFLATE
        Options FollowSymLinks
        AllowOverride All
        %s
        DirectoryIndex %s
    </Directory>
</VirtualHost>''' % (vName, path, siteName, domains, public.GetConfigValue('logs_path') + '/' + siteName,
                     public.GetConfigValue('logs_path') + '/' + siteName, ap_proxy,
                     get.first_domain, get.first_domain, self.get_tls_protocol(is_apache=True),
                     ap_static_security, phpConfig, path, apaOpt, index)
                ap_conf = ap_conf + "\n" + sslStr
                self.apacheAddPort('443')
                shutil.copyfile(file, self.apache_conf_bak)
                public.writeFile(file, ap_conf)
                if other_project == "node":  # 兼容Nodejs项目
                    from projectModel.nodejsModel import main
                    m = main()
                    project_find = m.get_project_find(siteName)
                    m.set_apache_config(project_find)
                if other_project == "java":  # 兼容Java项目
                    try:
                        from mod.project.java.java_web_conf import JavaApacheTool
                        from mod.project.java.projectMod import main
                        JavaApacheTool().set_apache_config_for_ssl(main().get_project_find(siteName))
                    except:
                        from projectModel.javaModel import main
                        m = main()
                        project_find = m.get_project_find(siteName)
                        m.set_apache_config(project_find)
                if other_project == "go":  # 兼容Go项目
                    from projectModel.goModel import main
                    m = main()
                    project_find = m.get_project_find(siteName)
                    m.set_apache_config(project_find)
                if other_project == "other":  # 兼容其他项目
                    from projectModel.otherModel import main
                    m = main()
                    project_find = m.get_project_find(siteName)
                    m.set_apache_config(project_find)
                if other_project == "python":  # 兼容python项目
                    from projectModel.pythonModel import main
                    m = main()
                    project_find = m.get_project_find(siteName)
                    m.set_apache_config(project_find)
                if other_project == "net":
                    from projectModel.netModel import main
                    m = main()
                    project_find = m.get_project_find(siteName)
                    m.set_apache_config(project_find)

                if other_project == "html":
                    from projectModel.htmlModel import main
                    m = main()
                    project_find = m.get_project_find(siteName)
                    m.set_apache_config(project_find)

        if not have_nginx_conf and not have_apache_conf:
            return public.returnMsg(False, '没有服务器配置文件，请检查是否开启了外网映射！')

        if ng_conf:  # 因为未查明原因，Apache配置过程中会删除掉nginx备份文件（估计是重复调用了本类中的init操作导致的）
            shutil.copyfile(ng_file, self.nginx_conf_bak)
            public.writeFile(ng_file, ng_conf)
        # OLS
        self.set_ols_ssl(get, siteName)
        http2https_pl = "{}/data/http2https.pl".format(public.get_panel_path())
        if os.path.exists(http2https_pl):
            self.CloseToHttps(public.to_dict_obj({'siteName': siteName}), without_reload=True)
            # 尝试设置 http2https，并暂时重启，等到后续测试配置后，在重启
            self.HttpToHttps(public.to_dict_obj({'siteName': siteName}), without_reload=True)
        isError = public.checkWebConfig()
        if (isError != True):
            if os.path.exists(self.nginx_conf_bak): shutil.copyfile(self.nginx_conf_bak, ng_file)
            if os.path.exists(self.apache_conf_bak): shutil.copyfile(self.apache_conf_bak, file)
            public.ExecShell("rm -f /tmp/backup_*.conf")
            return public.returnMsg(False, '证书错误: <br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')

        sql = public.M('firewall')
        import firewalls
        get.port = '443'
        get.ps = 'HTTPS'
        if 'isBatch' not in get: firewalls.firewalls().AddAcceptPort(get)
        if 'isBatch' not in get: public.serviceReload()
        self.save_cert(get)
        public.WriteLog('TYPE_SITE', 'SITE_SSL_OPEN_SUCCESS', (siteName,))
        result = public.returnMsg(True, 'SITE_SSL_OPEN_SUCCESS')
        result['csr'] = public.readFile('/www/server/panel/vhost/cert/' + get.siteName + '/fullchain.pem')
        result['key'] = public.readFile('/www/server/panel/vhost/cert/' + get.siteName + '/privkey.pem')
        if 'isBatch' not in get:
            return result
        else:
            return True

    def save_cert(self, get):
        # try:
        import panelSSL
        ss = panelSSL.panelSSL()
        get.keyPath = '/www/server/panel/vhost/cert/' + get.siteName + '/privkey.pem'
        get.certPath = '/www/server/panel/vhost/cert/' + get.siteName + '/fullchain.pem'
        return ss.SaveCert(get)
        return True
        # except:
        # return False;

    # HttpToHttps
    def HttpToHttps(self, get, without_reload=False):
        siteName = get.siteName
        # Nginx配置
        file = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/node_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/java_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/go_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/other_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/python_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/net_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/html_' + siteName + '.conf'
        conf = public.readFile(file)
        if conf:
            if conf.find('ssl_certificate') == -1: return public.returnMsg(False, '当前未开启SSL')
            to = """#error_page 404/404.html;
    #HTTP_TO_HTTPS_START
    set $isRedcert 1;
    if ($server_port != 443) {
        set $isRedcert 2;
    }
    if ( $uri ~ /\.well-known/ ) {
        set $isRedcert 1;
    }
    if ($isRedcert != 1) {
        rewrite ^(/.*)$ https://$host$1 permanent;
    }
    #HTTP_TO_HTTPS_END"""
            conf = conf.replace('#error_page 404/404.html;', to)
            public.writeFile(file, conf)

        file = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/apache/node_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/python_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/net_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/html' + siteName + '.conf'
        conf = public.readFile(file)
        if conf:
            httpTohttos = '''combined
    #HTTP_TO_HTTPS_START
    <IfModule mod_rewrite.c>
        RewriteEngine on
        RewriteCond %{SERVER_PORT} !^443$
        RewriteRule (.*) https://%{SERVER_NAME}$1 [L,R=301]
    </IfModule>
    #HTTP_TO_HTTPS_END'''
            conf = re.sub('combined', httpTohttos, conf, 1)
            public.writeFile(file, conf)
        # OLS
        conf_dir = '{}/panel/vhost/openlitespeed/redirect/{}/'.format(self.setupPath, siteName)
        if not os.path.exists(conf_dir):
            os.makedirs(conf_dir)
        file = conf_dir + 'force_https.conf'
        ols_force_https = '''
#HTTP_TO_HTTPS_START
<IfModule mod_rewrite.c>
    RewriteEngine on
    RewriteCond %{SERVER_PORT} !^443$
    RewriteRule (.*) https://%{SERVER_NAME}$1 [L,R=301]
</IfModule>
#HTTP_TO_HTTPS_END'''
        public.writeFile(file, ols_force_https)
        if not without_reload:
            public.serviceReload()
        return public.returnMsg(True, 'SET_SUCCESS')

    # CloseToHttps
    def CloseToHttps(self, get, without_reload=False):
        siteName = get.siteName
        file = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/node_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/java_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/go_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/other_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/python_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/net_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/html_' + siteName + '.conf'
        conf = public.readFile(file)
        if conf:
            rep = "\n\s*#HTTP_TO_HTTPS_START(.|\n){1,900}#HTTP_TO_HTTPS_END"
            conf = re.sub(rep, '', conf)
            rep = "\s+if.+server_port.+\n.+\n\s+\s*}"
            conf = re.sub(rep, '', conf)
            public.writeFile(file, conf)

        file = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/apache/python_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/apache/net_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/apache/html_' + siteName + '.conf'

        conf = public.readFile(file)
        if conf:
            rep = "\n\s*#HTTP_TO_HTTPS_START(.|\n){1,300}#HTTP_TO_HTTPS_END"
            conf = re.sub(rep, '', conf)
            public.writeFile(file, conf)
        # OLS
        file = '{}/panel/vhost/openlitespeed/redirect/{}/force_https.conf'.format(self.setupPath, siteName)
        if os.path.exists(file):
            public.ExecShell('rm -f {}*'.format(file))
        if not without_reload:
            public.serviceReload()
        return public.returnMsg(True, 'SET_SUCCESS')

    # 是否跳转到https
    def IsToHttps(self, siteName):
        file = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/node_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/java_' + siteName + '.conf'

        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/go_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/other_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/python_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/net_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/html_' + siteName + '.conf'
        conf = public.readFile(file)
        if conf:
            if conf.find('HTTP_TO_HTTPS_START') != -1: return True
            if conf.find('$server_port !~ 443') != -1: return True
            if conf.find('$server_port != 443') != -1: return True
            if conf.find('set $isRedcert 1;') != -1: return True
        return False

    # 清理SSL配置
    def CloseSSLConf(self, get):
        siteName = get.siteName

        file = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/node_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/java_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/go_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/other_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/python_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/net_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/html_' + siteName + '.conf'
        conf = public.readFile(file)
        if conf:
            rep = "\n\s*#HTTP_TO_HTTPS_START(.|\n){1,900}#HTTP_TO_HTTPS_END"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_certificate\s+.+;\s+ssl_certificate_key\s+.+;"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_protocols\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_ciphers\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_prefer_server_ciphers\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_session_cache\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_session_timeout\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_ecdh_curve\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_session_tickets\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_stapling\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl_stapling_verify\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+add_header\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+add_header\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\s+ssl\s+on;"
            conf = re.sub(rep, '', conf)
            rep = "\s+error_page\s497.+;"
            conf = re.sub(rep, '', conf)
            rep = "\s+if.+server_port.+\n.+\n\s+\s*}"
            conf = re.sub(rep, '', conf)
            rep = "\s+listen\s+443.*;"
            conf = re.sub(rep, '', conf)
            rep = "\s+listen\s+\[::\]:443.*;"
            conf = re.sub(rep, '', conf)
            rep = "\s+http2\s+on;"
            conf = re.sub(rep, '', conf)
            public.writeFile(file, conf)

        file = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/apache/node_' + siteName + '.conf'

        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/apache/java_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/apache/go_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/apache/other_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/apache/python_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/apache/net_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/apache/html_' + siteName + '.conf'
        conf = public.readFile(file)
        if conf:
            rep = "\n<VirtualHost \*\:443>(.|\n)*<\/VirtualHost>"
            conf = re.sub(rep, '', conf)
            rep = "\n\s*#HTTP_TO_HTTPS_START(.|\n){1,250}#HTTP_TO_HTTPS_END"
            conf = re.sub(rep, '', conf)
            rep = "NameVirtualHost  *:443\n"
            conf = conf.replace(rep, '')
            public.writeFile(file, conf)

        # OLS
        ssl_file = self.setupPath + '/panel/vhost/openlitespeed/detail/ssl/{}.conf'.format(siteName)
        detail_file = self.setupPath + '/panel/vhost/openlitespeed/detail/' + siteName + '.conf'
        force_https = self.setupPath + '/panel/vhost/openlitespeed/redirect/' + siteName
        if os.path.exists('{}/force_https.conf'.format(force_https)):
            string = 'rm -f {}/force_https.conf*'.format(force_https)
            public.ExecShell(string)
        detail_conf = public.readFile(detail_file)
        if detail_conf:
            detail_conf = detail_conf.replace('\ninclude ' + ssl_file, '')
            public.writeFile(detail_file, detail_conf)
        if os.path.exists(ssl_file):
            public.ExecShell('rm -f {}*'.format(ssl_file))

        self._del_ols_443_domain(siteName)
        partnerOrderId = '/www/server/panel/vhost/cert/' + siteName + '/partnerOrderId'
        if os.path.exists(partnerOrderId): public.ExecShell('rm -f ' + partnerOrderId)
        p_file = '/etc/letsencrypt/live/' + siteName + '/partnerOrderId'
        if os.path.exists(p_file): public.ExecShell('rm -f ' + p_file)

        public.WriteLog('TYPE_SITE', 'SITE_SSL_CLOSE_SUCCESS', (siteName,))
        public.serviceReload()
        return public.returnMsg(True, 'SITE_SSL_CLOSE_SUCCESS')

    def _del_ols_443_domain(self, sitename):
        file = "/www/server/panel/vhost/openlitespeed/listen/443.conf"
        conf = public.readFile(file)
        if conf:
            rep = '\n\s*map\s*{}'.format(sitename)
            conf = re.sub(rep, '', conf)
            if not "map " in conf:
                public.ExecShell('rm -f {}*'.format(file))
                return
            public.writeFile(file, conf)

    # 取SSL状态
    def GetSSL(self, get):
        if not hasattr(get, "siteName"):
            return public.returnMsg(False, '未指定网站!')
        get.siteName = str(get.siteName)

        siteName = get.siteName
        path = os.path.join('/www/server/panel/vhost/cert/', siteName)
        if not os.path.isfile(os.path.join(path, "fullchain.pem")) and not os.path.isfile(os.path.join(path, "privkey.pem")):
            path = os.path.join('/etc/letsencrypt/live/', siteName)
        type = 0
        if os.path.exists(path + '/README'):  type = 1
        if os.path.exists(path + '/partnerOrderId'):  type = 2
        if os.path.exists(path + '/certOrderId'):  type = 3
        csrpath = path + "/fullchain.pem"  # 生成证书路径
        keypath = path + "/privkey.pem"  # 密钥文件路径
        key = public.readFile(keypath)
        csr = public.readFile(csrpath)



        file = self.setupPath + '/panel/vhost/' + public.get_webserver() + '/' + siteName + '.conf'

        # 是否为node项目
        if not os.path.exists(file): file = self.setupPath + '/panel/vhost/' + public.get_webserver() + '/node_' + siteName + '.conf'

        if not os.path.exists(file): file = self.setupPath + '/panel/vhost/' + public.get_webserver() + '/java_' + siteName + '.conf'

        if not os.path.exists(file): file = self.setupPath + '/panel/vhost/' + public.get_webserver() + '/go_' + siteName + '.conf'

        if not os.path.exists(file): file = self.setupPath + '/panel/vhost/' + public.get_webserver() + '/other_' + siteName + '.conf'

        if not os.path.exists(file): file = self.setupPath + '/panel/vhost/' + public.get_webserver() + '/python_' + siteName + '.conf'

        if not os.path.exists(file): file = self.setupPath + '/panel/vhost/' + public.get_webserver() + '/net_' + siteName + '.conf'
        if not os.path.exists(
            file): file = self.setupPath + '/panel/vhost/' + public.get_webserver() + '/html_' + siteName + '.conf'

        if public.get_webserver() == "openlitespeed":
            file = self.setupPath + '/panel/vhost/' + public.get_webserver() + '/detail/' + siteName + '.conf'
        conf = public.readFile(file)
        if not conf: return public.returnMsg(False, '指定网站配置文件不存在!')

        if public.get_webserver() == 'nginx':
            keyText = 'ssl_certificate'
        elif public.get_webserver() == 'apache':
            keyText = 'SSLCertificateFile'
        else:
            keyText = 'openlitespeed/detail/ssl'

        status = True
        if (conf.find(keyText) == -1):
            status = False
            type = -1

        toHttps = self.IsToHttps(siteName)
        id = public.M('sites').where("name=?", (siteName,)).getField('id')
        domains = public.M('domain').where("pid=?", (id,)).field('name').select()
        cert_data = {}
        if csr:
            get.certPath = csrpath
            import panelSSL
            cert_data = panelSSL.panelSSL().GetCertName(get)
            if not cert_data:
                cert_data = {
                    'certificate': 0
                }

        if os.path.isfile(csrpath) and os.path.isfile(keypath):
            if key and csr:
                cert_hash = SSLManger().ssl_hash(certificate=csr, ignore_errors=True)
                if cert_hash is None:
                    cert_data["id"], cert_data["ps"] = 0, ''
                else:
                    cert_data["id"], cert_data["ps"] = SSLManger().get_cert_info_by_hash(cert_hash)
                    # 调用save_by_file方法保存证书信息
                    if cert_data["id"] == -1:
                        try:
                            save_result = SSLManger().save_by_file(csrpath, keypath)
                            cert_data["id"], cert_data["ps"] = SSLManger().get_cert_info_by_hash(cert_hash)
                        except:
                            cert_data["id"], cert_data["ps"] = 0, ''

        email = public.M('users').where('id=?', (1,)).getField('email')
        if email == public.en_hexb('4d6a67334f5459794e545932514846784c6d4e7662513d3d'): email = ''
        index = ''
        auth_type = 'http'
        if status == True:
            if type != 1:
                import acme_v2
                acme = acme_v2.acme_v2()
                index = acme.check_order_exists(csrpath)
                if index:
                    if index.find('/') == -1:
                        auth_type = acme._config['orders'][index]['auth_type']
                    type = 1
            else:
                crontab_file = 'vhost/cert/crontab.json'
                tmp = public.readFile(crontab_file)
                if tmp:
                    crontab_config = json.loads(tmp)
                    if siteName in crontab_config:
                        if 'dnsapi' in crontab_config[siteName]:
                            auth_type = 'dns'

            if os.path.exists(path + '/certOrderId'):  type = 3
        oid = -1
        if type == 3:
            oid = int(public.readFile(path + '/certOrderId'))
        tls_versions = self.get_ssl_protocol(get)
        # 作者 muluo
        # return {'status': status,'oid':oid, 'domain': domains, 'key': key, 'csr': csr, 'type': type, 'httpTohttps': toHttps,'cert_data':cert_data,'email':email,"index":index,'auth_type':auth_type}
        res = {'status': status, 'oid': oid, 'domain': domains, 'key': key, 'csr': csr, 'type': type, 'httpTohttps': toHttps, 'cert_data': cert_data, 'email': email, "index": index,
               'auth_type': auth_type, 'tls_versions': tls_versions}
        
        res['push'] = self.get_ssl_push_status(None, siteName, 'ssl',status)
        if os.path.exists("{}/data/ignore_https_mode/{}".format(public.get_panel_path(), siteName)):
            res["https_mode"] = True
            # 当前未开启HTTPS防窜站
        else:
            res["https_mode"] = self.get_https_mode(None)
        return res

    def set_site_ignore_https_mode(self, get):
        """
        设置网站忽略https防窜站
        :param get:
        :return:
        """
        if "siteName" not in get or not get.siteName:
            return public.returnMsg(False, '未指定网站!')
        siteName = get.siteName
        try:
            ignore_https_mode_path = "{}/data/ignore_https_mode/".format(public.get_panel_path())
            if not os.path.exists(ignore_https_mode_path):
                os.makedirs(ignore_https_mode_path)
            ignore_https_mode_path = os.path.join(ignore_https_mode_path, siteName)
            if public.writeFile(ignore_https_mode_path, "ignore"):
                return public.returnMsg(True, '设置成功!')
            else:
                return public.returnMsg(True, '设置失败!')
        except:
            public.print_log(public.get_error_info())
            return public.returnMsg(False, '设置失败，请检查权限!')

    def get_view_title_content(self, get):
        """
        获取推广横幅内容
        :param get:
        :return:
        """
        try:
            import panelPlugin
            panelPlugin = panelPlugin.panelPlugin()
            content = panelPlugin.get_cloud_list()["remarks"]["domain_panle"]
        except:
            content = ''
        if content:
            status = os.path.exists("{}/data/view_domain_title_status.pl".format(public.get_panel_path()))
        else:
            status = True

        return public.returnMsg(status, content)

    def set_ignore_view_domain_title(self, get):
        """
        设置忽略域名推广横幅
        :param get:
        :return:
        """
        try:
            ignore_view_domain_title_path = "{}/data/view_domain_title_status.pl".format(public.get_panel_path())
            if not os.path.exists(ignore_view_domain_title_path):
                public.writeFile(ignore_view_domain_title_path, "ignore")
            return public.returnMsg(True, '设置成功!')
        except:
            public.print_log(public.get_error_info())
            return public.returnMsg(False, '设置失败，请检查权限!')

    def get_ssl_push_status(self, get, siteName=None, stype=None,ssl_status=None):
        if get:
            siteName = get.siteName
        result = {'status': False}
        task_data={}
        selected_data = {
                'task_data': {},
                'title':"",
                'sender': "",
                'status':bool(0),
                'id':""
            } 
        task={}
        
        try:
            try:
                data = json.loads(public.readFile('{}/data/mod_push_data/task.json'.format(public.get_panel_path())))
            except:
                return result
            for i in data:
                if i['source'] =='site_ssl':
                    task_data = i.get('task_data', {})
                    # print(task_data)
                    project = task_data.get('project')
                    if project == siteName:
                        task=i
                        break
                    if project =="all" :
                        task=i
        except Exception as e:
            return result
 
        # if ssl_status:
        if task.get('id'):
            selected_data = {
                'task_data': task.get('task_data', {}),
                'title': task.get('title', ''),
                'sender': task.get('sender', []),
                'status':task.get('status'),
                'id':task.get('id', "")
            }
            # else:
            #     selected_data['status']=bool(0)
        return selected_data
    
    def get_site_push_status(self, get, siteName=None, stype=None):
        """
        @获取网站ssl告警通知状态
        @param get:
        @param siteName 网站名称
        @param stype 类型 ssl
        """
        import panelPush
        if get:
            siteName = get.siteName
            stype = get.stype

        result = {}
        result['status'] = False
        try:
            data = {}
            try:
                data = json.loads(public.readFile('{}/class/push/push.json'.format(public.get_panel_path())))
            except:
                pass

            if not 'site_push' in data:
                return result

            ssl_data = data['site_push']
            for key in ssl_data.keys():
                if ssl_data[key]['type'] != stype:
                    continue

                project = ssl_data[key]['project']
                if project in [siteName, 'all']:
                    ssl_data[key]['id'] = key
                    ssl_data[key]['s_module'] = 'site_push'

                    if project == siteName:
                        result = ssl_data[key]
                        break

                    if project == 'all':
                        result = ssl_data[key]
        except:
            pass

        p_obj = panelPush.panelPush()
        return p_obj.get_push_user(result)

    def query_sites_data_by_ids(self, sites_id):

        """
        根据ID查询网站数据。
        """
        sites_data = []
        for site_id in sites_id.split(','):
            find = public.M('sites').where("id=?", (site_id,)).find()
            if find:
                sites_data.append(find)
        return sites_data

    def format_status(self,status):
        """
        格式化状态字段，1代表运行，0代表停止。
        """
        return "运行" if status == "1" else "停止"

    def format_ssl_endtime(self,days):
        """
        格式化SSL证书的过期时间。
        """
        if days is None:
            return '未部署'
        return '剩余{}天'.format(days)

    def format_php_version(self,version):
        """
        将PHP版本从数字格式（如"82"）转换为点分格式（如"8.2"），
        特殊处理"0.0"为"静态"。
        """
        if version == "00":
            return "静态"
        if len(version) == 2:  # 假设所有PHP版本都是两位数
            return "{}.{}".format(version[0], version[1])
        return version

    def format_expiry_date(self,date):
        """
        处理到期日期的特殊值"0000-00-00"为"永久"。
        """
        if date == "0000-00-00":
            return "永久"
        return date


    def export_sites_to_csv(self, get):
        import csv
        import os
        import time

        try:
            sites_data = self.query_sites_data_by_ids(get.sites_id)
            # save_path = get.save_path
            csv_file_name = get.csv_file_name

            fieldnames_cn_to_en = {
                '网站名': 'name',
                '状态': 'status',
                # '添加时间': 'addtime',
                '根目录': 'path',
                '到期日期': 'edate',
                '项目类型': 'project_type',
                '备注': 'ps',
                'SSL证书过期时间': 'ssl_endtime',
                'PHP版本': 'php_version'
            }

            with open(csv_file_name, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=list(fieldnames_cn_to_en.keys()))
                writer.writeheader()
                for site in sites_data:
                    get.siteName = site['name']

                    ssl_endtime = self.get_ssl_cert_endtime(get)
                    php_info = self.GetSitePHPVersion(get)
                    php_version = self.format_php_version(php_info['phpversion']) if 'phpversion' in php_info else ''

                    row = {cn: site[en] for cn, en in fieldnames_cn_to_en.items() if en in site}
                    row['状态'] = self.format_status(site['status'])
                    row['SSL证书过期时间'] = self.format_ssl_endtime(ssl_endtime)
                    row['PHP版本'] = php_version
                    row['到期日期'] = self.format_expiry_date(site['edate'])

                    writer.writerow(row)

            return {'status': True, 'msg': '数据已成功导出到 {}'.format(csv_file_name)}
        except Exception as e:
            return {'status': False, 'msg': str(e)}

    def get_ssl_cert_endtime(self, get):
        get = type('obj', (object,), {'siteName': get.siteName})
        ssl_info = self.GetSSL(get)

        # 检查是否成功获取到SSL信息，并且cert_data字段存在
        if ssl_info['status'] and 'cert_data' in ssl_info and 'endtime' in ssl_info['cert_data']:
            return ssl_info['cert_data']['endtime']
        else:
            return None  # 没有找到endtime，返回None表示没有部署SSL证书或没有过期时间

    def set_site_status_multiple(self, get):
        '''
            @name 批量设置网站状态
            @author zhwen<2020-11-17>
            @param sites_id "1,2"
            @param status 0/1
        '''
        sites_id = get.sites_id.split(',')
        sites_name = []
        errors = {}
        day_time = time.time()
        for site_id in sites_id:
            get.id = site_id
            find = public.M('sites').where("id=?", (site_id,)).find()
            get.name = find['name']

            if get.status == '1':
                if find['edate'] != '0000-00-00' and public.to_date("%Y-%m-%d", find['edate']) < day_time:
                    errors[get.name] = "失败,已到期"
                    continue
            sites_name.append(get.name)
            if get.status == '1':
                self.SiteStart(get, multiple=1)
            else:
                self.SiteStop(get, multiple=1)
        public.serviceReload()
        if get.status == '1':
            return {'status': True, 'msg': '开启网站 [ {} ] 成功'.format(','.join(sites_name)), 'error': errors, 'success': sites_name}
        else:
            return {'status': True, 'msg': '停止网站 [ {} ] 成功'.format(','.join(sites_name)), 'error': errors, 'success': sites_name}

    # 启动站点
    def SiteStart(self, get, multiple=None):
        try:
            id = int(get.id)
        except:
            return public.returnMsg(False, '参数错误!')
        Path = self.setupPath + '/stop'
        location_stop = '''
    location / {
        try_files $uri /index.html;
    }
'''
        site_info = public.M('sites').where("id=?", (id,)).find()
        sitePath = site_info['path']
        if not sitePath:
            return public.returnMsg(False, '未找到网站目录!')
        try:
            p_cnf = json.loads(site_info['project_config'])
            if "php_run_path" in p_cnf:
                sitePath += p_cnf["php_run_path"]
        except:
            pass

        self.update_stop_field(get.id)

        # 定义 apache, nginx 和 openlitespeed 文件夹
        folders = ["apache", "nginx"]

        for folder in folders:
            self.move_file(folder, get.name)
            # self.move_file(get.name)

        # nginx
        file = self.setupPath + '/panel/vhost/nginx/' + get.name + '.conf'
        conf = public.readFile(file)
        if conf:
            conf = conf.replace(Path, sitePath)
            conf = conf.replace(location_stop, "")
            conf = re.sub(r'\s*rewrite\s+.*bt-stop\\\.html.*\s+/bt-stop.html\s+last;\s*location\s*=\s*/bt-stop.html\s*{[^}]+}[^\n]*\n', "", conf)
            conf = conf.replace("#include", "include")
            public.writeFile(file, conf)
        # apache
        file = self.setupPath + '/panel/vhost/apache/' + get.name + '.conf'
        conf = public.readFile(file)
        if conf:
            conf = conf.replace(Path, sitePath)
            conf = conf.replace("#IncludeOptional", "IncludeOptional")
            public.writeFile(file, conf)

        # OLS
        file = self.setupPath + '/panel/vhost/openlitespeed/' + get.name + '.conf'
        conf = public.readFile(file)
        if conf:
            rep = 'vhRoot\s*{}'.format(Path)
            new_content = 'vhRoot {}'.format(sitePath)
            conf = re.sub(rep, new_content, conf)
            public.writeFile(file, conf)

        public.M('sites').where("id=?", (id,)).setField('status', '1')
        if not multiple:
            public.serviceReload()
        public.WriteLog('TYPE_SITE', 'SITE_START_SUCCESS', (get.name,))
        return public.returnMsg(True, 'SITE_START_SUCCESS')

    def update_stop_field(self, site_id):

            # 如果'stop'字段存在，则将其值设为空
            try:
                public.M('sites').where("id=?", (site_id,)).setField('stop', '')
            except Exception as e:
                print(e)


    # 移动文件的函数
    def move_file(self, folder, name):
        # 定义源和目标文件夹
        source_dir = "/www/php_site/vhost"
        target_dir = self.setupPath + '/panel/vhost'

        # 检查源文件是否存在
        source_file = os.path.join(source_dir, folder, name + ".conf")
        if os.path.isfile(source_file):
            # 检查目标文件夹是否存在，如果不存在则创建
            target_folder = os.path.join(target_dir, folder)
            os.makedirs(target_folder, exist_ok=True)

            # 移动文件
            target_file = os.path.join(target_folder, name + ".conf")
            if not os.path.isfile(target_file):  # 检查目标文件是否已经存在
                shutil.move(source_file, target_file)
                # print(f"{source_file} 已移动到 {target_file}")
            else:
                # print(f"{target_file} 已存在，无需移动")
                pass
        public.ServiceReload()

    def _process_has_run_dir(self, website_name, website_path, stop_path):
        '''
            @name 当网站存在允许目录时停止网站需要做处理
            @author zhwen<2020-11-17>
            @param site_id 1
            @param names test,baohu
        '''
        conf = public.readFile(self.setupPath + '/panel/vhost/nginx/' + website_name + '.conf')
        if not conf:
            return False
        try:
            really_path = re.search('root\s+(.*);', conf).group(1)
            tmp = stop_path + '/' + really_path.replace(website_path + '/', '')
            public.ExecShell('mkdir {t} && ln -s {s}/index.html {t}/index.html'.format(t=tmp, s=stop_path))
        except:
            pass

    # 停止站点
    def SiteStop(self, get, multiple=None):
        path = self.setupPath + '/stop'
        id = get.id
        site_info = public.M('sites').where("id=?", (id,)).find()
        site_status = site_info['status']
        if str(site_status) != '1':
            return public.returnMsg(True, 'SITE_STOP_SUCCESS')
        if not os.path.exists(path) or not os.path.isfile(path + '/index.html'):
            os.makedirs(path)
            # ? 疑似无效代码
            public.downloadFile('http://{}/stop.html'.format(public.get_url()), path + '/index.html')

        bt_stop = path + '/bt-stop.html'
        if not os.path.exists(bt_stop):
            os.symlink(path + '/index.html', bt_stop)
        if not os.path.islink(bt_stop):
            os.unlink(bt_stop)
            os.symlink(path + '/index.html', bt_stop)

        binding = public.M('binding').where('pid=?', (id,)).field('id,pid,domain,path,port,addtime').select()
        for b in binding:
            bpath = path + '/' + b['path']
            if not os.path.exists(bpath):
                public.ExecShell('mkdir -p ' + bpath)
                public.ExecShell('ln -sf ' + path + '/index.html ' + bpath + '/index.html')

        sitePath = public.M('sites').where("id=?", (id,)).getField('path')
        r_path = self.GetRunPath(get)
        if isinstance(r_path, str):
            if r_path != '/':
                sitePath += r_path
                try:
                    project_config = json.loads(site_info.get("project_config"))
                except:
                    project_config = {}
                project_config["php_run_path"] = r_path
                public.M('sites').where("id=?", (id,)).setField('project_config', json.dumps(project_config))

        self._process_has_run_dir(get.name, sitePath, path)
        # nginx
        file = self.setupPath + '/panel/vhost/nginx/' + get.name + '.conf'
        conf = public.readFile(file)
        if conf:
            src_path = 'root ' + sitePath
            dst_path = 'root ' + path
            dst_path = dst_path + ''';

    rewrite ^/(?!bt-stop\.html$).* /bt-stop.html last;
    location = /bt-stop.html {
        root /www/server/stop;
        internal;
    }
'''
            if conf.find(src_path) != -1:
                conf = conf.replace(src_path + ";", dst_path)
            else:
                conf = conf.replace(sitePath + ";", path)
            conf = conf.replace("include", "#include")
            public.writeFile(file, conf)

        # apache
        file = self.setupPath + '/panel/vhost/apache/' + get.name + '.conf'
        conf = public.readFile(file)
        if conf:
            conf = conf.replace(sitePath, path)
            conf = conf.replace("IncludeOptional", "#IncludeOptional")
            public.writeFile(file, conf)
        # OLS
        file = self.setupPath + '/panel/vhost/openlitespeed/' + get.name + '.conf'
        conf = public.readFile(file)
        if conf:
            rep = 'vhRoot\s*{}'.format(sitePath)
            new_content = 'vhRoot {}'.format(path)
            conf = re.sub(rep, new_content, conf)
            public.writeFile(file, conf)

        public.M('sites').where("id=?", (id,)).setField('status', '0')
        if not multiple:
            public.serviceReload()
        public.WriteLog('TYPE_SITE', 'SITE_STOP_SUCCESS', (get.name,))
        return public.returnMsg(True, 'SITE_STOP_SUCCESS')

    # 取流量限制值
    def GetLimitNet(self, get):
        if not hasattr(get, 'id'):
            return public.returnMsg(False, "参数错误")
        id = get.id

        # 取回配置文件
        siteName = public.M('sites').where("id=?", (id,)).getField('name')
        if not siteName:
            return public.returnMsg(False, "未查询到对应的网站信息")
        filename = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'

        # 站点总并发
        data = {}
        conf = public.readFile(filename)
        try:
            rep = "\s+limit_conn\s+perserver\s+([0-9]+);"
            tmp = re.search(rep, conf).groups()
            data['perserver'] = int(tmp[0])

            # IP并发限制
            rep = "\s+limit_conn\s+perip\s+([0-9]+);"
            tmp = re.search(rep, conf).groups()
            data['perip'] = int(tmp[0])

            # 请求并发限制
            rep = "\s+limit_rate\s+([0-9]+)\w+;"
            tmp = re.search(rep, conf).groups()
            data['limit_rate'] = int(tmp[0])
        except:
            data['perserver'] = 0
            data['perip'] = 0
            data['limit_rate'] = 0

        self._show_limit_net(data)
        return data

    def _show_limit_net(self, data):
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

    # 设置流量限制
    def SetLimitNet(self, get):
        if (public.get_webserver() != 'nginx'): return public.returnMsg(False, 'SITE_NETLIMIT_ERR')

        id = get.id
        if int(get.perserver) < 1 or int(get.perip) < 1 or int(get.perip) < 1:
            return public.returnMsg(False, '并发限制，IP限制，流量限制必需大于0')
        perserver = 'limit_conn perserver ' + get.perserver + ';'
        perip = 'limit_conn perip ' + get.perip + ';'
        limit_rate = 'limit_rate ' + get.limit_rate + 'k;'

        # 取回配置文件
        siteName = public.M('sites').where("id=?", (id,)).getField('name')
        filename = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        conf = public.readFile(filename)
        if not conf:
            return public.returnMsg(False, '网站配置文件不存在!')

        # 设置共享内存
        oldLimit = self.setupPath + '/panel/vhost/nginx/limit.conf'
        if (os.path.exists(oldLimit)): os.remove(oldLimit)
        limit = self.setupPath + '/nginx/conf/nginx.conf'
        nginxConf = public.readFile(limit)
        limitConf = "limit_conn_zone $binary_remote_addr zone=perip:10m;\n\t\tlimit_conn_zone $server_name zone=perserver:10m;"
        nginxConf = nginxConf.replace("#limit_conn_zone $binary_remote_addr zone=perip:10m;", limitConf)
        public.writeFile(limit, nginxConf)

        if (conf.find('limit_conn perserver') != -1):
            # 替换总并发
            rep = "limit_conn\s+perserver\s+([0-9]+);"
            conf = re.sub(rep, perserver, conf)

            # 替换IP并发限制
            rep = "limit_conn\s+perip\s+([0-9]+);"
            conf = re.sub(rep, perip, conf)

            # 替换请求流量限制
            rep = "limit_rate\s+([0-9]+)\w+;"
            conf = re.sub(rep, limit_rate, conf)
        else:
            conf = conf.replace('#error_page 404/404.html;', "#error_page 404/404.html;\n    " + perserver + "\n    " + perip + "\n    " + limit_rate)

        import shutil
        shutil.copyfile(filename, self.nginx_conf_bak)
        public.writeFile(filename, conf)
        isError = public.checkWebConfig()
        if (isError != True):
            if os.path.exists(self.nginx_conf_bak): shutil.copyfile(self.nginx_conf_bak, filename)
            return public.returnMsg(False, 'ERROR: <br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')

        public.serviceReload()
        public.WriteLog('TYPE_SITE', 'SITE_NETLIMIT_OPEN_SUCCESS', (siteName,))
        return public.returnMsg(True, 'SET_SUCCESS')

    # 关闭流量限制
    def CloseLimitNet(self, get):
        id = get.id
        # 取回配置文件
        siteName = public.M('sites').where("id=?", (id,)).getField('name')
        filename = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        conf = public.readFile(filename)
        # 清理总并发
        rep = "\s+limit_conn\s+perserver\s+([0-9]+);"
        conf = re.sub(rep, '', conf)

        # 清理IP并发限制
        rep = "\s+limit_conn\s+perip\s+([0-9]+);"
        conf = re.sub(rep, '', conf)

        # 清理请求流量限制
        rep = "\s+limit_rate\s+([0-9]+)\w+;"
        conf = re.sub(rep, '', conf)
        public.writeFile(filename, conf)
        public.serviceReload()
        public.WriteLog('TYPE_SITE', 'SITE_NETLIMIT_CLOSE_SUCCESS', (siteName,))
        return public.returnMsg(True, 'SITE_NETLIMIT_CLOSE_SUCCESS')

    # 取301配置状态
    def Get301Status(self, get):
        siteName = get.siteName
        result = {}
        domains = ''
        site_data = public.M('sites').where("name=?", (siteName,)).find()
        if not site_data:
            result['domain'] = ''
            result['src'] = ""
            result['status'] = False
            result['url'] = "http://"
            return result
        if site_data["project_type"].lower() in ("php", "proxy"):
            prefix = ""
        else:
            prefix = site_data["project_type"].lower() + "_"

        tmp = public.M('domain').where("pid=?", (id,)).field('name').select()
        # node = public.M('sites').where('id=? and project_type=?', (id, 'Node')).count()
        # python = public.M('sites').where('id=? and project_type=?', (id, 'Python')).count()
        # net = public.M('sites').where('id=? and project_type=?', (id, 'net')).count()
        # if node:
        #     prefix = 'node_'
        # elif python:
        #     prefix = 'python_'
        # elif net:
        #     prefix = 'net_'
        # else:
        #     prefix = ''
        for key in tmp:
            domains += key['name'] + ','
        try:
            if (public.get_webserver() == 'nginx'):
                conf = public.readFile(self.setupPath + '/panel/vhost/nginx/' + prefix + siteName + '.conf')
                if conf.find('301-START') == -1:
                    result['domain'] = domains[:-1]
                    result['src'] = ""
                    result['status'] = False
                    result['url'] = "http://"
                    return result
                rep = "return\s+301\s+((http|https)\://.+);"
                arr = re.search(rep, conf).groups()[0]
                rep = "'\^(([\w-]+\.)+[\w-]+)'"
                tmp = re.search(rep, conf)
                src = ''
                if tmp: src = tmp.groups()[0]
            elif public.get_webserver() == 'apache':
                conf = public.readFile(self.setupPath + '/panel/vhost/apache/' + prefix + siteName + '.conf')
                if conf.find('301-START') == -1:
                    result['domain'] = domains[:-1]
                    result['src'] = ""
                    result['status'] = False
                    result['url'] = "http://"
                    return result
                rep = "RewriteRule\s+.+\s+((http|https)\://.+)\s+\["
                arr = re.search(rep, conf).groups()[0]
                rep = "\^((\w+\.)+\w+)\s+\[NC"
                tmp = re.search(rep, conf)
                src = ''
                if tmp: src = tmp.groups()[0]
            else:
                conf = public.readFile(self.setupPath + '/panel/vhost/openlitespeed/redirect/{s}/{s}.conf'.format(s=siteName))
                if not conf:
                    result['domain'] = domains[:-1]
                    result['src'] = ""
                    result['status'] = False
                    result['url'] = "http://"
                    return result
                rep = "RewriteRule\s+.+\s+((http|https)\://.+)\s+\["
                arr = re.search(rep, conf).groups()[0]
                rep = "\^((\w+\.)+\w+)\s+\[NC"
                tmp = re.search(rep, conf)
                src = ''
                if tmp: src = tmp.groups()[0]
        except:
            src = ''
            arr = 'http://'

        result['domain'] = domains[:-1]
        result['src'] = src.replace("'", '')
        result['status'] = True
        if (len(arr) < 3): result['status'] = False
        result['url'] = arr

        return result

    # 设置301配置
    def Set301Status(self, get):
        siteName = get.siteName
        srcDomain = get.srcDomain
        toDomain = get.toDomain
        type = get.type
        rep = "(http|https)\://.+"
        if not re.match(rep, toDomain):    return public.returnMsg(False, 'Url地址不正确!')

        # nginx
        filename = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        mconf = public.readFile(filename)
        if mconf == False: return public.returnMsg(False, '指定配置文件不存在!')
        if mconf:
            if (srcDomain == 'all'):
                conf301 = "\t#301-START\n\t\treturn 301 " + toDomain + "$request_uri;\n\t#301-END"
            else:
                conf301 = "\t#301-START\n\t\tif ($host ~ '^" + srcDomain + "'){\n\t\t\treturn 301 " + toDomain + "$request_uri;\n\t\t}\n\t#301-END"
            if type == '1':
                mconf = mconf.replace("#error_page 404/404.html;", "#error_page 404/404.html;\n" + conf301)
            else:
                rep = "\s+#301-START(.|\n){1,300}#301-END"
                mconf = re.sub(rep, '', mconf)

            public.writeFile(filename, mconf)

        # apache
        filename = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
        mconf = public.readFile(filename)
        if mconf:
            if type == '1':
                if (srcDomain == 'all'):
                    conf301 = "\n\t#301-START\n\t<IfModule mod_rewrite.c>\n\t\tRewriteEngine on\n\t\tRewriteRule ^(.*)$ " + toDomain + "$1 [L,R=301]\n\t</IfModule>\n\t#301-END\n"
                else:
                    conf301 = "\n\t#301-START\n\t<IfModule mod_rewrite.c>\n\t\tRewriteEngine on\n\t\tRewriteCond %{HTTP_HOST} ^" + srcDomain + " [NC]\n\t\tRewriteRule ^(.*) " + toDomain + "$1 [L,R=301]\n\t</IfModule>\n\t#301-END\n"
                rep = "combined"
                mconf = mconf.replace(rep, rep + "\n\t" + conf301)
            else:
                rep = "\n\s+#301-START(.|\n){1,300}#301-END\n*"
                mconf = re.sub(rep, '\n\n', mconf, 1)
                mconf = re.sub(rep, '\n\n', mconf, 1)

            public.writeFile(filename, mconf)

        # OLS
        conf_dir = self.setupPath + '/panel/vhost/openlitespeed/redirect/{}/'.format(siteName)
        if not os.path.exists(conf_dir):
            os.makedirs(conf_dir)
        file = conf_dir + siteName + '.conf'
        if type == '1':
            if (srcDomain == 'all'):
                conf301 = "#301-START\nRewriteEngine on\nRewriteRule ^(.*)$ " + toDomain + "$1 [L,R=301]#301-END\n"
            else:
                conf301 = "#301-START\nRewriteEngine on\nRewriteCond %{HTTP_HOST} ^" + srcDomain + " [NC]\nRewriteRule ^(.*) " + toDomain + "$1 [L,R=301]\n#301-END\n"
            public.writeFile(file, conf301)
        else:
            public.ExecShell('rm -f {}*'.format(file))

        isError = public.checkWebConfig()
        if (isError != True):
            return public.returnMsg(False, 'ERROR: <br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')

        public.serviceReload()
        return public.returnMsg(True, 'SUCCESS')

    # 取子目录绑定
    def GetDirBinding(self, get):
        if not hasattr(get, "id"):
            return public.returnMsg(False, "参数错误!")
        path = public.M('sites').where('id=?', (get.id,)).getField('path')
        if isinstance(path, list):
            return public.returnMsg(False, "未查询到网站信息!")
        if not os.path.exists(path):
            checks = ['/', '/usr', '/etc']
            if path in checks:
                data = {}
                data['dirs'] = []
                data['binding'] = []
                return data
            public.ExecShell('mkdir -p ' + path)
            public.ExecShell('chmod 755 ' + path)
            public.ExecShell('chown www:www ' + path)
            get.path = path
            self.SetDirUserINI(get)
            siteName = public.M('sites').where('id=?', (get.id,)).getField('name')
            public.WriteLog('网站管理', '站点[' + siteName + '],根目录[' + path + ']不存在,已重新创建!')

        # 取运行目录
        run_path = self.GetRunPath(get)
        if run_path: path += run_path

        # 遍历目录
        # if os.path.exists(path) and os.path.isdir(path):
        #     def get_sub_path(sub_path_name, num):
        #         if num == 0:
        #             return
        #         for filename in os.listdir(sub_path_name):
        #             try:
        #                 if sys.version_info[0] == 2:
        #                     filename = filename.encode('utf-8')
        #                 else:
        #                     filename.encode('utf-8')
        #                 filePath = sub_path_name + '/' + filename
        #                 if os.path.islink(filePath):
        #                     continue
        #                 if os.path.isdir(filePath):
        #                     dirnames.append(filePath[len(path) + 1:])
        #                     get_sub_path(filePath, num - 1)
        #             except:
        #                 pass

            # get_sub_path(path, 1)
        # 优化目录的获取速度
        dirnames = []
        if os.path.exists(path):
            dirnames = [entry.name for entry in os.scandir(path) if entry.is_dir() and not entry.is_symlink()]
        data = {}
        data['run_path'] = run_path  # 运行目录
        data['dirs'] = dirnames
        data['binding'] = public.M('binding').where('pid=?', (get.id,)).field('id,pid,domain,path,port,addtime').select()

        # 标记子目录是否存在
        for dname in data['binding']:
            _path = os.path.join(path, dname['path'].lstrip("/"))
            if not os.path.exists(_path):
                _path = _path.replace(run_path, '')
                if not os.path.exists(_path):
                    dname['path'] += '<a style="color:red;"> >> 错误: 目录不存在</a>'
                else:
                    dname['path'] = '../' + dname['path']
        return data

    # 添加子目录绑定
    def AddDirBinding(self, get):
        import shutil
        id = get.id
        tmp = get.domain.split(':')
        domain = tmp[0].lower()
        # 中文域名转码
        domain = public.en_punycode(domain)
        port = '80'
        version = ''
        if len(tmp) > 1: port = tmp[1]
        if not hasattr(get, 'dirName'): public.returnMsg(False, 'DIR_EMPTY')
        dirName = get.dirName

        reg = "^([\w\-\*]{1,100}\.){1,4}([\w\-]{1,100}|[\w\-]{1,100}\.[\w\-]{1,100})$"
        if not re.match(reg, domain): return public.returnMsg(False, 'SITE_ADD_ERR_DOMAIN')

        siteInfo = public.M('sites').where("id=?", (id,)).field('id,path,name').find()
        # 实际运行目录
        root_path = siteInfo['path']
        run_path = self.GetRunPath(get)
        if run_path: root_path += run_path

        webdir = root_path + '/' + dirName
        webdir = webdir.replace('//', '/').strip()
        if not os.path.exists(webdir):  # 如果在运行目录找不到指定子目录，尝试到根目录查找
            root_path = siteInfo['path']
            webdir = root_path + '/' + dirName
            webdir = webdir.replace('//', '/').strip()

        sql = public.M('binding')
        if sql.where("domain=?", (domain,)).count() > 0: return public.returnMsg(False, 'SITE_ADD_ERR_DOMAIN_EXISTS')
        if public.M('domain').where("name=?", (domain,)).count() > 0: return public.returnMsg(False, 'SITE_ADD_ERR_DOMAIN_EXISTS')

        filename = self.setupPath + '/panel/vhost/nginx/' + siteInfo['name'] + '.conf'
        nginx_conf_file = filename
        conf = public.readFile(filename)
        if conf:
            listen_ipv6 = ''
            if self.is_ipv6: listen_ipv6 = "\n    listen [::]:%s;" % port
            rep = "enable-php-(\w{2,5})\.conf"
            tmp = re.search(rep, conf).groups()
            version = tmp[0]
            bindingConf = '''
#BINDING-%s-START
server
{
    listen %s;%s
    server_name %s;
    index index.php index.html index.htm default.php default.htm default.html;
    root %s;

    include enable-php-%s.conf;
    include %s/panel/vhost/rewrite/%s.conf;
    #禁止访问的文件或目录
    location ~ ^/(\.user.ini|\.htaccess|\.git|\.env|\.svn|\.project|LICENSE|README.md)
    {
        return 404;
    }

    #一键申请SSL证书验证目录相关设置
    location ~ \.well-known{
        allow all;
    }

    location ~ .*\\.(gif|jpg|jpeg|png|bmp|swf)$
    {
        expires      30d;
        error_log /dev/null;
        access_log /dev/null;
    }
    location ~ .*\\.(js|css)?$
    {
        expires      12h;
        error_log /dev/null;
        access_log /dev/null;
    }
    access_log %s.log;
    error_log  %s.error.log;
}
#BINDING-%s-END''' % (domain, port, listen_ipv6, domain, webdir, version, self.setupPath, siteInfo['name'], public.GetConfigValue('logs_path') + '/' + siteInfo['name'],
                      public.GetConfigValue('logs_path') + '/' + siteInfo['name'], domain)

            conf += bindingConf
            shutil.copyfile(filename, self.nginx_conf_bak)
            public.writeFile(filename, conf)

        filename = self.setupPath + '/panel/vhost/apache/' + siteInfo['name'] + '.conf'
        conf = public.readFile(filename)
        if conf:
            try:
                try:
                    httpdVersion = public.readFile(self.setupPath + '/apache/version.pl').strip()
                except:
                    httpdVersion = ""
                if httpdVersion == '2.2':
                    phpConfig = ""
                    apaOpt = "Order allow,deny\n\t\tAllow from all"
                else:
                    # rep = "php-cgi-([0-9]{2,3})\.sock"
                    # tmp = re.search(rep,conf).groups()
                    # version = tmp[0]
                    version = public.get_php_version_conf(conf)
                    phpConfig = '''
    #PHP
    <FilesMatch \\.php>
        SetHandler "proxy:%s"
    </FilesMatch>
    ''' % (public.get_php_proxy(version, 'apache'),)
                    apaOpt = 'Require all granted'

                bindingConf = '''
\n#BINDING-%s-START
<VirtualHost *:%s>
    ServerAdmin webmaster@example.com
    DocumentRoot "%s"
    ServerAlias %s
    #errorDocument 404 /404.html
    ErrorLog "%s-error_log"
    CustomLog "%s-access_log" combined
    %s

    #DENY FILES
     <Files ~ (\.user.ini|\.htaccess|\.git|\.env|\.svn|\.project|LICENSE|README.md)$>
       Order allow,deny
       Deny from all
    </Files>

    #PATH
    <Directory "%s">
        SetOutputFilter DEFLATE
        Options FollowSymLinks
        AllowOverride All
        %s
        DirectoryIndex index.php index.html index.htm default.php default.html default.htm
    </Directory>
</VirtualHost>
#BINDING-%s-END''' % (domain, port, webdir, domain, public.GetConfigValue('logs_path') + '/' + siteInfo['name'], public.GetConfigValue('logs_path') + '/' + siteInfo['name'], phpConfig, webdir, apaOpt,
                      domain)

                conf += bindingConf
                shutil.copyfile(filename, self.apache_conf_bak)
                public.writeFile(filename, conf)
            except:
                pass
        get.webname = siteInfo['name']
        get.port = port
        self.phpVersion = version
        self.siteName = siteInfo['name']
        self.sitePath = webdir
        listen_file = self.setupPath + "/panel/vhost/openlitespeed/listen/80.conf"
        listen_conf = public.readFile(listen_file)
        if listen_conf:
            rep = 'secure\s*0'
            map = '\tmap {}_{} {}'.format(siteInfo['name'], dirName, domain)
            listen_conf = re.sub(rep, 'secure 0\n' + map, listen_conf)
            public.writeFile(listen_file, listen_conf)
        self.openlitespeed_add_site(get)

        # 检查配置是否有误
        isError = public.checkWebConfig()
        if isError != True:
            if os.path.exists(self.nginx_conf_bak): shutil.copyfile(self.nginx_conf_bak, nginx_conf_file)
            if os.path.exists(self.apache_conf_bak): shutil.copyfile(self.apache_conf_bak, filename)
            return public.returnMsg(False, 'ERROR: <br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')

        public.M('binding').add('pid,domain,port,path,addtime', (id, domain, port, dirName, public.getDate()))
        public.serviceReload()
        public.WriteLog('TYPE_SITE', 'SITE_BINDING_ADD_SUCCESS', (siteInfo['name'], dirName, domain))
        return public.returnMsg(True, 'ADD_SUCCESS')

    def delete_dir_bind_multiple(self, get):
        '''
            @name 批量删除网站
            @author zhwen<2020-11-17>
            @param bind_ids 1,2,3
        '''
        bind_ids = get.bind_ids.split(',')
        del_successfully = []
        del_failed = {}
        for bind_id in bind_ids:
            get.id = bind_id
            domain = public.M('binding').where("id=?", (get.id,)).getField('domain')
            if not domain:
                continue
            try:
                self.DelDirBinding(get, multiple=1)
                del_successfully.append(domain)
            except:
                del_failed[domain] = '删除时错误了，请再试一次'
                pass
        public.serviceReload()
        return {'status': True, 'msg': '删除 [ {} ] 子目录绑定成功'.format(','.join(del_successfully)), 'error': del_failed,
                'success': del_successfully}

    # 删除子目录绑定
    def DelDirBinding(self, get, multiple=None):
        id = get.id
        binding = public.M('binding').where("id=?", (id,)).field('id,pid,domain,path').find()
        siteName = public.M('sites').where("id=?", (binding['pid'],)).getField('name')

        # 防正则关键字转译
        b_path_prevent = public.prevent_re_key(binding['path'])
        b_domain_prevent = public.prevent_re_key(binding['domain'])
        site_name_prevent = public.prevent_re_key(siteName)

        # nginx
        filename = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        conf = public.readFile(filename)
        if conf:
            rep = "\s*.+BINDING-" + b_domain_prevent + "-START(.|\n)+BINDING-" + b_domain_prevent + "-END"
            conf = re.sub(rep, '', conf)
            public.writeFile(filename, conf)

        # apache
        filename = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
        conf = public.readFile(filename)
        if conf:
            rep = "\s*.+BINDING-" + b_domain_prevent + "-START(.|\n)+BINDING-" + b_domain_prevent + "-END"
            conf = re.sub(rep, '', conf)
            public.writeFile(filename, conf)

        # openlitespeed
        filename = self.setupPath + '/panel/vhost/openlitespeed/' + siteName + '.conf'
        conf = public.readFile(filename)
        rep = "#SUBDIR\s*{s}_{d}\s*START(\n|.)+#SUBDIR\s*{s}_{d}\s*END".format(s=site_name_prevent, d=b_path_prevent)
        if conf:
            conf = re.sub(rep, '', conf)
            public.writeFile(filename, conf)
        # 删除域名，前端需要传域名
        get.webname = siteName
        get.domain = binding['domain']
        self._del_ols_domain(get)

        # 清理子域名监听文件
        listen_file = self.setupPath + "/panel/vhost/openlitespeed/listen/80.conf"
        listen_conf = public.readFile(listen_file)
        if listen_conf:
            map_reg = '\s*map\s*{}_{}.*'.format(site_name_prevent, b_path_prevent)
            listen_conf = re.sub(map_reg, '', listen_conf)
            public.writeFile(listen_file, listen_conf)
        # 清理detail文件
        detail_file = "{}/panel/vhost/openlitespeed/detail/{}_{}.conf".format(self.setupPath, siteName, binding['path'])
        public.ExecShell("rm -f {}*".format(detail_file))

        # 从数据库删除绑定
        public.M('binding').where("id=?", (id,)).delete()

        # 如果没有其它域名绑定同一子目录，则删除该子目录的伪静态规则
        if not public.M('binding').where("path=? AND pid=?", (binding['path'], binding['pid'])).count():
            filename = self.setupPath + '/panel/vhost/rewrite/' + siteName + '_' + binding['path'] + '.conf'
            if os.path.exists(filename): public.ExecShell('rm -rf %s' % filename)
        # 是否需要重载服务
        if not multiple:
            public.serviceReload()
        public.WriteLog('TYPE_SITE', 'SITE_BINDING_DEL_SUCCESS', (siteName, binding['path']))
        return public.returnMsg(True, 'DEL_SUCCESS')

    # 取子目录Rewrite
    def GetDirRewrite(self, get):
        id = get.id
        find = public.M('binding').where("id=?", (id,)).field('id,pid,domain,path').find()
        site = public.M('sites').where("id=?", (find['pid'],)).field('id,name,path').find()

        if (public.get_webserver() != 'nginx'):
            filename = site['path'] + '/' + find['path'] + '/.htaccess'
        else:
            filename = self.setupPath + '/panel/vhost/rewrite/' + site['name'] + '_' + find['path'].replace('/', '_') + '.conf'

        if hasattr(get, 'add'):
            public.writeFile(filename, '')
            if public.get_webserver() == 'nginx':
                file = self.setupPath + '/panel/vhost/nginx/' + site['name'] + '.conf'
                conf = public.readFile(file)
                domain = find['domain']
                rep = "\n#BINDING-" + domain + "-START(.|\n)+BINDING-" + domain + "-END"
                tmp = re.search(rep, conf).group()
                dirConf = tmp.replace('rewrite/' + site['name'] + '.conf;', 'rewrite/' + site['name'] + '_' + find['path'].replace('/', '_') + '.conf;')
                conf = conf.replace(tmp, dirConf)
                public.writeFile(file, conf)
        data = {}
        data['status'] = False
        if os.path.exists(filename):
            data['status'] = True
            data['data'] = public.readFile(filename)
            data['rlist'] = ['0.当前']
            webserver = public.get_webserver()
            if webserver == "openlitespeed":
                webserver = "apache"
            for ds in os.listdir('rewrite/' + webserver):
                if ds == 'list.txt': continue
                if '0.当前' in ds: continue
                data['rlist'].append(ds[0:len(ds) - 5])
            data['filename'] = filename
        return data

    # 取默认文档
    def GetIndex(self, get):
        if not hasattr(get, "id"):
            return public.returnMsg(False, '查询参数错误')
        id = get.id
        Name = public.M('sites').where("id=?", (id,)).getField('name')
        if not isinstance(Name, str):
            return public.returnMsg(False, '获取失败,未查询到网站信息')
        try:
            file = self.setupPath + '/panel/vhost/' + public.get_webserver() + '/' + Name + '.conf'
            if public.get_webserver() == 'openlitespeed':
                file = self.setupPath + '/panel/vhost/' + public.get_webserver() + '/detail/' + Name + '.conf'
        except TypeError:
            return public.returnMsg(False, '获取失败,配置文件中不存在默认文档')
        conf = public.readFile(file)
        if conf == False: return public.returnMsg(False, '指定网站配置文件不存在!')
        if public.get_webserver() == 'nginx':
            rep = "\s+index\s+(.+);"
        elif public.get_webserver() == 'apache':
            rep = "DirectoryIndex\s+(.+)\n"
        else:
            rep = "indexFiles\s+(.+)\n"
        if re.search(rep, conf):
            tmp = re.search(rep, conf).groups()
            if public.get_webserver() == 'openlitespeed':
                return tmp[0]
            return tmp[0].replace(' ', ',')
        return public.returnMsg(False, '获取失败,配置文件中不存在默认文档')

    # 设置默认文档
    def SetIndex(self, get):
        id = get.id
        Index = get.Index.replace(' ', '')
        Index = Index.replace(',,', ',').strip()
        if not Index: return public.returnMsg(False, "默认文档不能为空")
        if Index.find('.') == -1: return public.returnMsg(False, 'SITE_INDEX_ERR_FORMAT')
        if len(Index) < 3: return public.returnMsg(False, 'SITE_INDEX_ERR_EMPTY')

        Name = public.M('sites').where("id=?", (id,)).getField('name')
        # 准备指令
        Index_L = Index.replace(",", " ")

        # nginx
        file = self.setupPath + '/panel/vhost/nginx/' + Name + '.conf'
        conf = public.readFile(file)
        if conf:
            rep = "\s+index\s+.+;"
            conf = re.sub(rep, "\n\tindex " + Index_L + ";", conf)
            public.writeFile(file, conf)

        # apache
        file = self.setupPath + '/panel/vhost/apache/' + Name + '.conf'
        conf = public.readFile(file)
        if conf:
            rep = "DirectoryIndex\s+.+\n"
            conf = re.sub(rep, 'DirectoryIndex ' + Index_L + "\n", conf)
            public.writeFile(file, conf)

        # openlitespeed
        file = self.setupPath + '/panel/vhost/openlitespeed/detail/' + Name + '.conf'
        conf = public.readFile(file)
        if conf:
            rep = "indexFiles\s+.+\n"
            Index = Index.split(',')
            Index = [i for i in Index if i]
            Index = ",".join(Index)
            conf = re.sub(rep, 'indexFiles ' + Index + "\n", conf)
            public.writeFile(file, conf)

        public.serviceReload()
        public.WriteLog('TYPE_SITE', 'SITE_INDEX_SUCCESS', (Name, Index_L))
        return public.returnMsg(True, 'SET_SUCCESS')

    # 修改物理路径
    def SetPath(self, get):
        id = get.id
        Path = self.GetPath(get.path)
        if ' ' in Path or "\n" in Path: return public.returnMsg(False, '目录中不能包含空格或换行符，请重新选择！')
        if Path == "" or id == '0': return public.returnMsg(False, "DIR_EMPTY")

        if not self.__check_site_path(Path): return public.returnMsg(False, "PATH_ERROR")
        if not public.check_site_path(Path):
            a, c = public.get_sys_path()
            return public.returnMsg(False, '请不要将网站根目录设置到以下关键目录中: <br>{}'.format("<br>".join(a + c)))

        if not os.path.exists(Path):
            return public.returnMsg(False, '指定的网站根目录不存在，无法设置，请检查输入信息.')

        SiteFind = public.M("sites").where("id=?", (id,)).field('path,name').find()
        if SiteFind["path"] == Path: return public.returnMsg(False, "SITE_PATH_ERR_RE")
        Name = SiteFind['name']
        file = self.setupPath + '/panel/vhost/nginx/' + Name + '.conf'
        conf = public.readFile(file)
        if conf:
            conf = conf.replace(SiteFind['path'], Path)
            public.writeFile(file, conf)

        file = self.setupPath + '/panel/vhost/apache/' + Name + '.conf'
        conf = public.readFile(file)
        if conf:
            rep = "DocumentRoot\s+.+\n"
            conf = re.sub(rep, 'DocumentRoot "' + Path + '"\n', conf)
            rep = "<Directory\s+.+\n"
            conf = re.sub(rep, '<Directory "' + Path + "\">\n", conf)
            public.writeFile(file, conf)

        # OLS
        file = self.setupPath + '/panel/vhost/openlitespeed/' + Name + '.conf'
        conf = public.readFile(file)
        if conf:
            reg = 'vhRoot.*'
            conf = re.sub(reg, 'vhRoot ' + Path, conf)
            public.writeFile(file, conf)

        public.M("sites").where("id=?", (id,)).setField('path', Path)
        public.WriteLog('TYPE_SITE', 'SITE_PATH_SUCCESS', (Name,))
        self.CheckRunPathExists(id)

        # 创建basedir
        userIni = Path + '/.user.ini'
        if os.path.exists(userIni): public.ExecShell("chattr -i " + userIni)
        public.writeFile(userIni, 'open_basedir=' + Path + '/:/tmp/')
        public.ExecShell('chmod 644 ' + userIni)
        public.ExecShell('chown root:root ' + userIni)
        public.ExecShell('chattr +i ' + userIni)
        public.set_site_open_basedir_nginx(Name)
        public.serviceReload()

        return public.returnMsg(True, "SET_SUCCESS")

    def CheckRunPathExists(self, site_id):
        '''
            @name 检查站点运行目录是否存在
            @author hwliang
            @param site_id int 站点ID
            @return bool
        '''

        site_info = public.M('sites').where('id=?', (site_id,)).field('name,path').find()
        if not site_info: return False
        args = public.dict_obj()
        args.id = site_id
        run_path = self.GetRunPath(args)
        site_run_path = site_info['path'] + '/' + run_path
        if os.path.exists(site_run_path): return True
        args.runPath = '/'
        self.SetSiteRunPath(args)
        public.WriteLog('TYPE_SITE', '因修改网站[{}]根目录，检测到原指定的运行目录[.{}]不存在，已自动将运行目录切换为[./]'.format(site_info['name'], run_path))
        return False

    # 取当前可用PHP版本
    def GetPHPVersion(self, get):
        all = getattr(get, 'all', 0)
        phpVersions = public.get_php_versions()
        phpVersions.insert(0, 'other')
        phpVersions.insert(0, '00')
        httpdVersion = ""
        filename = self.setupPath + '/apache/version.pl'
        if os.path.exists(filename): httpdVersion = public.readFile(filename).strip()

        if httpdVersion == '2.2': phpVersions = ('00', '52', '53', '54')
        if httpdVersion == '2.4':
            if '52' in phpVersions: phpVersions.remove('52')
        if os.path.exists('/www/server/nginx/sbin/nginx'):
            cfile = '/www/server/nginx/conf/enable-php-00.conf'
            if not os.path.exists(cfile): public.writeFile(cfile, '')

        s_type = getattr(get, 's_type', 0)
        data = []
        for val in phpVersions:
            if '9' in val: continue
            tmp = {}
            checkPath = self.setupPath + '/php/' + val + '/bin/php'
            if val in ['00', 'other']: checkPath = '/etc/init.d/bt'
            if httpdVersion == '2.2': checkPath = self.setupPath + '/php/' + val + '/libphp5.so'
            if os.path.exists(checkPath):
                tmp['version'] = val
                tmp['name'] = 'PHP-' + val
                if val == '00':
                    tmp['name'] = '纯静态'

                if val == 'other':
                    if s_type:
                        tmp['name'] = '自定义'
                    else:
                        continue
                tmp['status'] = True
                data.append(tmp)
            else:
                if all:
                    tmp['version'] = val
                    tmp['name'] = 'PHP-' + val
                    tmp['status'] = False
                    data.append(tmp)
        data = sorted(data, key=lambda x: x['status'],reverse=True)
        return data

    # 取指定站点的PHP版本
    def GetSitePHPVersion(self, get):
        try:
            siteName = get.siteName
            data = {}
            data['phpversion'] = public.get_site_php_version(siteName)
            conf = public.readFile(self.setupPath + '/panel/vhost/' + public.get_webserver() + '/' + siteName + '.conf')
            data['tomcat'] = conf.find('#TOMCAT-START')
            data['tomcatversion'] = public.readFile(self.setupPath + '/tomcat/version.pl')
            data['nodejsversion'] = public.readFile(self.setupPath + '/node.js/version.pl')
            data['php_other'] = ''
            if data['phpversion'] == 'other':
                other_file = '/www/server/panel/vhost/other_php/{}/enable-php-other.conf'.format(siteName)
                if os.path.exists(other_file):
                    conf = public.readFile(other_file)
                    data['php_other'] = re.findall(r"fastcgi_pass\s+(.+);", conf)[0]
            return data
        except:
            return public.returnMsg(False, 'SITE_PHPVERSION_ERR_A22,{}'.format(public.get_error_info()))

    def set_site_php_version_multiple(self, get):
        '''
            @name 批量设置PHP版本
            @author zhwen<2020-11-17>
            @param sites_id "1,2"
            @param version 52...74
        '''
        sites_id = get.sites_id.split(',')
        set_phpv_successfully = []
        set_phpv_failed = {}
        for site_id in sites_id:
            get.id = site_id
            get.siteName = public.M('sites').where("id=?", (site_id,)).getField('name')
            if not get.siteName:
                continue
            try:
                result = self.SetPHPVersion(get, multiple=1)
                if not result['status']:
                    set_phpv_failed[get.siteName] = result['msg']
                    continue
                set_phpv_successfully.append(get.siteName)
            except:
                set_phpv_failed[get.siteName] = '设置时错误了，请再试一次'
                pass
        public.serviceReload()
        return {'status': True, 'msg': '设置网站 [ {} ] PHP版本成功'.format(','.join(set_phpv_successfully)), 'error': set_phpv_failed,
                'success': set_phpv_successfully}

    # 设置指定站点的PHP版本
    def SetPHPVersion(self, get, multiple=None):
        if not hasattr(get, 'siteName'): return public.returnMsg(False, '网站名不可为空！')
        if not hasattr(get, 'version'): return public.returnMsg(False, 'php版本不可为空！')
        siteName = get.siteName
        version = get.version
        if version == 'other' and not public.get_webserver() in ['nginx', 'tengine']:
            return public.returnMsg(False, '自定义PHP配置只支持Nginx')
        try:
            # nginx
            file = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
            conf = public.readFile(file)
            if conf:
                other_path = '/www/server/panel/vhost/other_php/{}'.format(siteName)
                if not os.path.exists(other_path): os.makedirs(other_path)
                other_rep = "{}/enable-php-other.conf".format(other_path)

                if version == 'other':
                    dst = other_rep
                    get.other = get.other.strip()

                    if not get.other:
                        return public.returnMsg(False, '自定义版本时PHP连接配置不能为空!')

                    if not re.match(r"^(\d+\.\d+\.\d+\.\d+:\d+|unix:[\w/\.-]+)$", get.other):
                        return public.returnMsg(False, 'PHP连接配置格式不正确，请参考示例!')

                    other_tmp = get.other.split(':')
                    if other_tmp[0] == 'unix':
                        if not os.path.exists(other_tmp[1]):
                            return public.returnMsg(False, '指定unix套接字[{}]不存在，请核实!'.format(other_tmp[1]))
                    else:
                        if not public.check_tcp(other_tmp[0], int(other_tmp[1])):
                            return public.returnMsg(False, '无法连接[{}],请排查本机是否可连接目标服务器'.format(get.other))

                    other_conf = '''location ~ [^/]\.php(/|$)
{{
    try_files $uri =404;
    fastcgi_pass  {};
    fastcgi_index index.php;
    include fastcgi.conf;
    include pathinfo.conf;
}}'''.format(get.other)
                    public.writeFile(other_rep, other_conf)
                    conf = conf.replace(other_rep, dst)
                    rep = "include\s+enable-php-(\w{2,5})\.conf"
                    tmp = re.search(rep, conf)
                    if tmp: conf = conf.replace(tmp.group(), 'include ' + dst)
                elif re.search(r"enable-php-\d+-wpfastcgi.conf", conf):
                    dst = 'enable-php-{}-wpfastcgi.conf'.format(version)
                    conf = conf.replace(other_rep, dst)
                    rep = r"enable-php-\d+-wpfastcgi.conf"
                    tmp = re.search(rep, conf)
                    if tmp: conf = conf.replace(tmp.group(), dst)
                    self._create_wp_fastcgi_cache_conf(version)
                else:
                    dst = 'enable-php-' + version + '.conf'
                    conf = conf.replace(other_rep, dst)
                    rep = "enable-php-(\w{2,5})\.conf"
                    tmp = re.search(rep, conf)
                    if tmp: conf = conf.replace(tmp.group(), dst)

                public.writeFile(file, conf)
                try:
                    import site_dir_auth
                    site_dir_auth_module = site_dir_auth.SiteDirAuth()
                    auth_list = site_dir_auth_module.get_dir_auth(get)
                    if auth_list:
                        for i in auth_list[siteName]:
                            auth_name = i['name']
                            auth_file = "{setup_path}/panel/vhost/nginx/dir_auth/{site_name}/{auth_name}.conf".format(
                                setup_path=self.setupPath, site_name=siteName, auth_name=auth_name)
                            if os.path.exists(auth_file):
                                site_dir_auth_module.change_dir_auth_file_nginx_phpver(siteName, version, auth_name)
                except:
                    pass

            # apache
            file = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
            conf = public.readFile(file)
            if conf and version != 'other':
                rep = "(unix:/tmp/php-cgi-(\w{2,5})\.sock\|fcgi://localhost|fcgi://127.0.0.1:\d+)"
                tmp = re.search(rep, conf).group()
                conf = conf.replace(tmp, public.get_php_proxy(version, 'apache'))
                public.writeFile(file, conf)
            # OLS
            if version != 'other':
                file = self.setupPath + '/panel/vhost/openlitespeed/detail/' + siteName + '.conf'
                conf = public.readFile(file)
                if conf:
                    rep = 'lsphp\d+'
                    tmp = re.search(rep, conf)
                    if tmp:
                        conf = conf.replace(tmp.group(), 'lsphp' + version)
                        public.writeFile(file, conf)
            if not multiple:
                public.serviceReload()
            public.WriteLog("TYPE_SITE", "SITE_PHPVERSION_SUCCESS", (siteName, version))
            return public.returnMsg(True, 'SITE_PHPVERSION_SUCCESS', (siteName, version))
        except:
            return public.get_error_info()
            return public.returnMsg(False, '设置失败，没有在网站配置文件中找到enable-php-xx相关配置项!')

    @staticmethod
    def _create_wp_fastcgi_cache_conf(php_v: str):
        from wptoolkitModel.wp_toolkit.core import wpfastcgi_cache
        wpfastcgi_cache().set_fastcgi_php_conf(php_v)

    # 是否开启目录防御
    def GetDirUserINI(self, get):
        path = get.path + self.GetRunPath(get)
        if not path: return public.returnMsg(False, '获取目录失败')
        id = get.id
        get.name = public.M('sites').where("id=?", (id,)).getField('name')
        if not isinstance(get.name, str):
            return public.returnMsg(False, '获取站点信息失败')
        data = {}
        if os.path.exists("/www/server/panel/data/syncsite.json"):
            data['sync_git'] = True if get.id in json.loads(public.readFile("/www/server/panel/data/syncsite.json")) else False
        else:
            data['sync_git'] = False
        data['logs'] = self.GetLogsStatus(get)
        data['userini'] = False
        user_ini_file = path + '/.user.ini'
        try:
            user_ini_conf = public.readFile(user_ini_file)
        except OSError:
            user_ini_conf = {}
        if user_ini_conf and "open_basedir" in user_ini_conf:
            data['userini'] = True
        data['runPath'] = self.GetSiteRunPath(get)
        data['pass'] = self.GetHasPwd(get)
        return data

    # 清除多余user.ini
    def DelUserInI(self, path, up=0):
        useriniPath = path + '/.user.ini'
        if os.path.exists(useriniPath):
            public.ExecShell('chattr -i ' + useriniPath)
            try:
                os.remove(useriniPath)
            except:
                pass

        for p1 in os.listdir(path):
            try:
                npath = path + '/' + p1
                if not os.path.isdir(npath): continue
                useriniPath = npath + '/.user.ini'
                if os.path.exists(useriniPath):
                    public.ExecShell('chattr -i ' + useriniPath)
                    os.remove(useriniPath)
                if up < 3: self.DelUserInI(npath, up + 1)
            except:
                continue
        return True

    # 设置目录防御
    def SetDirUserINI(self, get):
        path = get.path
        runPath = self.GetRunPath(get)
        if not runPath: return public.returnMsg(False, "运行目录获取失败")
        filename = path + runPath + '/.user.ini'
        siteName = public.M('sites').where('path=?', (get.path,)).getField('name')
        conf = public.readFile(filename)
        try:
            self._set_ols_open_basedir(get)
            if os.path.exists(filename): public.ExecShell("chattr -i " + filename)
            if conf and "open_basedir" in conf:
                rep = "\n*open_basedir.*"
                conf = re.sub(rep, "", conf)
                if not conf:
                    os.remove(filename)
                else:
                    public.writeFile(filename, conf)
                    if os.path.exists(filename): public.ExecShell("chattr +i " + filename)
                public.set_site_open_basedir_nginx(siteName)
                return public.returnMsg(True, 'SITE_BASEDIR_CLOSE_SUCCESS')

            if conf and "session.save_path" in conf:
                rep = "session.save_path\s*=\s*(.*)"
                s_path = re.search(rep, conf).groups(1)[0]
                public.writeFile(filename, conf + '\nopen_basedir={}/:/tmp/:{}'.format(path, s_path))
            else:
                public.writeFile(filename, 'open_basedir={}/:/tmp/'.format(path))
            if os.path.exists(filename): public.ExecShell("chattr +i " + filename)
            if not os.path.exists(filename): return public.returnMsg(False, '.user.ini文件不存在,设置防跨站失败,请关闭防篡改或其他安全软件后再试!')
            public.set_site_open_basedir_nginx(siteName)
            public.serviceReload()
            return public.returnMsg(True, 'SITE_BASEDIR_OPEN_SUCCESS')
        except Exception as e:
            if os.path.exists(filename): public.ExecShell("chattr +i " + filename)
            if "Operation not permitted" in str(e):
                return public.returnMsg(False, "{}\t权限拒绝,设置防跨站失败,请关闭防篡改或其他安全软件后再试!".format(str(e)))
            return public.returnMsg(False, str(e))

    def _set_ols_open_basedir(self, get):
        # 设置ols
        try:
            sitename = public.M('sites').where("id=?", (get.id,)).getField('name')
            # sitename = path.split('/')[-1]
            f = "/www/server/panel/vhost/openlitespeed/detail/{}.conf".format(sitename)
            c = public.readFile(f)
            if not c: return False
            if f:
                rep = '\nphp_admin_value\s*open_basedir.*'
                result = re.search(rep, c)
                s = 'on'
                if not result:
                    s = 'off'
                    rep = '\n#php_admin_value\s*open_basedir.*'
                    result = re.search(rep, c)
                result = result.group()
                if s == 'on':
                    c = re.sub(rep, '\n#' + result[1:], c)
                else:
                    result = result.replace('#', '')
                    c = re.sub(rep, result, c)
                public.writeFile(f, c)
        except:
            pass

    # 读配置
    def __read_config(self, path):
        if not os.path.exists(path):
            public.writeFile(path, '[]')
        upBody = public.readFile(path)
        if not upBody: upBody = '[]'
        return json.loads(upBody)

        # 写配置

    def __write_config(self, path, data):
        return public.writeFile(path, json.dumps(data))

        # 取某个站点某条反向代理详情

    def GetProxyDetals(self, get):
        proxyUrl = self.__read_config(self.__proxyfile)
        sitename = get.sitename
        proxyname = get.proxyname
        for i in proxyUrl:
            if i["proxyname"] == proxyname and i["sitename"] == sitename:
                return i

    # 取某个站点反向代理列表
    def GetProxyList(self, get):
        n = 0
        for w in ["nginx", "apache"]:
            conf_path = "%s/panel/vhost/%s/%s.conf" % (self.setupPath, w, get.sitename)
            old_conf = ""
            if os.path.exists(conf_path):
                old_conf = public.readFile(conf_path)
            rep = "(#PROXY-START(\n|.)+#PROXY-END)"
            url_rep = "proxy_pass (.*);|ProxyPass\s/\s(.*)|Host\s(.*);"
            host_rep = "Host\s(.*);"
            if re.search(rep, old_conf):
                # 构造代理配置
                if w == "nginx":
                    get.todomain = str(re.search(host_rep, old_conf).group(1))
                    get.proxysite = str(re.search(url_rep, old_conf).group(1))
                else:
                    get.todomain = ""
                    get.proxysite = str(re.search(url_rep, old_conf).group(2))
                get.proxyname = "旧代理"
                get.type = 1
                get.proxydir = "/"
                get.advanced = 0
                get.cachetime = 1
                get.cache = 0
                get.subfilter = "[{\"sub1\":\"\",\"sub2\":\"\"},{\"sub1\":\"\",\"sub2\":\"\"},{\"sub1\":\"\",\"sub2\":\"\"}]"

                # proxyname_md5 = self.__calc_md5(get.proxyname)
                # 备份并替换老虚拟主机配置文件
                public.ExecShell("cp %s %s_bak" % (conf_path, conf_path))
                conf = re.sub(rep, "", old_conf)
                public.writeFile(conf_path, conf)
                if n == 0:
                    self.CreateProxy(get)
                n += 1
                # 写入代理配置
                # proxypath = "%s/panel/vhost/%s/proxy/%s/%s_%s.conf" % (
                # self.setupPath, w, get.sitename, proxyname_md5, get.sitename)
                # proxycontent = str(re.search(rep, old_conf).group(1))
                # public.writeFile(proxypath, proxycontent)
            if n == "1":
                public.serviceReload()
        proxyUrl = self.__read_config(self.__proxyfile)
        sitename = get.sitename
        proxylist = []
        for i in proxyUrl:
            if i["sitename"] == sitename:
                proxylist.append(i)
        return proxylist

    def del_proxy_multiple(self, get):
        '''
            @name 批量网站到期时间
            @author zhwen<2020-11-20>
            @param site_id 1
            @param proxynames ces,aaa
        '''
        proxynames = get.proxynames.split(',')
        del_successfully = []
        del_failed = {}
        get.sitename = public.M('sites').where("id=?", (get.site_id,)).getField('name')
        for proxyname in proxynames:
            if not proxyname:
                continue
            get.proxyname = proxyname
            try:
                resule = self.RemoveProxy(get, multiple=1)
                if not resule['status']:
                    del_failed[proxyname] = resule['msg']
                del_successfully.append(proxyname)
            except:
                del_failed[proxyname] = '删除时错误，请再试一次'
                pass
        return {'status': True, 'msg': '删除反向代理 [ {} ] 成功'.format(','.join(del_successfully)), 'error': del_failed,
                'success': del_successfully}

    # 删除反向代理
    def RemoveProxy(self, get, multiple=None):
        conf = self.__read_config(self.__proxyfile)
        sitename = get.sitename
        proxyname = get.proxyname
        for i in range(len(conf)):
            c_sitename = conf[i]["sitename"]
            c_proxyname = conf[i]["proxyname"]
            if c_sitename == sitename and c_proxyname == proxyname:
                proxyname_md5 = self.__calc_md5(c_proxyname)
                for w in ["apache", "nginx", "openlitespeed"]:
                    p = "{sp}/panel/vhost/{w}/proxy/{s}/{m}_{s}.conf*".format(sp=self.setupPath, w=w, s=c_sitename, m=proxyname_md5)

                    public.ExecShell('rm -f {}'.format(p))
                p = "{sp}/panel/vhost/openlitespeed/proxy/{s}/urlrewrite/{m}_{s}.conf*".format(sp=self.setupPath, m=proxyname_md5, s=get.sitename)
                public.ExecShell('rm -f {}'.format(p))
                del conf[i]
                self.__write_config(self.__proxyfile, conf)
                self.SetNginx(get)
                self.SetApache(get.sitename)
                if not multiple:
                    public.serviceReload()
                return public.returnMsg(True, '删除成功')

    # 检查代理是否存在
    def __check_even(self, get, action=""):
        conf_data = self.__read_config(self.__proxyfile)
        for i in conf_data:
            if i["sitename"] == get.sitename:
                if action == "create":
                    if i["proxydir"] == get.proxydir or i["proxyname"] == get.proxyname:
                        return i
                else:
                    if i["proxyname"] != get.proxyname and i["proxydir"] == get.proxydir:
                        return i

    # 检测全局代理和目录代理是否同时存在
    def __check_proxy_even(self, get, action=""):
        conf_data = self.__read_config(self.__proxyfile)
        n = 0
        if action == "":
            for i in conf_data:
                if i["sitename"] == get.sitename:
                    n += 1
            if n == 1:
                return
        for i in conf_data:
            if i["sitename"] == get.sitename:
                if i["advanced"] != int(get.advanced):
                    return i

    # 计算proxyname md5
    def __calc_md5(self, proxyname):
        md5 = hashlib.md5()
        md5.update(proxyname.encode('utf-8'))
        return md5.hexdigest()

    # 检测URL是否可以访问
    def __CheckUrl(self, get):
        sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sk.settimeout(5)
        rep = "(https?)://([\w\.\-]+):?([\d]+)?"
        h = re.search(rep, get.proxysite).group(1)
        d = re.search(rep, get.proxysite).group(2)
        try:
            p = re.search(rep, get.proxysite).group(3)
        except:
            p = ""
        try:
            if p:
                sk.connect((d, int(p)))
            else:
                if h == "http":
                    sk.connect((d, 80))
                else:
                    sk.connect((d, 443))
        except:
            return public.returnMsg(False, "目标URL无法访问")

    # 基本设置检查
    def __CheckStart(self, get, action=""):
        isError = public.checkWebConfig()
        if isinstance(isError, str):
            if isError.find('/proxy/') == -1:  # 如果是反向代理配置文件本身的错误，跳过
                return public.returnMsg(False, '配置文件出错请先排查配置')
        if action == "create":
            if sys.version_info.major < 3:
                if len(get.proxyname) < 3 or len(get.proxyname) > 40:
                    return public.returnMsg(False, '名称必须大于3小于40个字符串')
            else:
                if len(get.proxyname.encode("utf-8")) < 3 or len(get.proxyname.encode("utf-8")) > 40:
                    return public.returnMsg(False, '名称必须大于3小于40个字符串')
        if self.__check_even(get, action):
            return public.returnMsg(False, '指定反向代理名称或代理文件夹已存在')
        # 判断代理，只能有全局代理或目录代理
        if self.__check_proxy_even(get, action):
            return public.returnMsg(False, '不能同时设置目录代理和全局代理')
        # 判断cachetime类型
        if not bool(get.cachetime):
            return public.returnMsg(False, "缓存时间不能为空")
        if get.cachetime:
            try:
                int(get.cachetime)
            except:
                return public.returnMsg(False, "缓存时间不能为空")

        rep = "http(s)?\:\/\/"
        # repd = "http(s)?\:\/\/([a-zA-Z0-9][-a-zA-Z0-9]{0,62}\.)+([a-zA-Z0-9][a-zA-Z0-9]{0,62})+.?"
        tod = "[a-zA-Z]+$"
        repte = "[\?\=\[\]\)\(\*\&\^\%\$\#\@\!\~\`{\}\>\<\,\',\";]+"
        # 检测代理目录格式
        if re.search(repte, get.proxydir):
            return public.returnMsg(False, "代理目录不能有以下特殊符号 ?,=,[,],),(,*,&,^,%,$,#,@,!,~,`,{,},>,<,\,',\";]")
        # 检测发送域名格式
        if get.todomain:
            if re.search("[\}\{\#\;\"\']+", get.todomain):
                return public.returnMsg(False, '发送域名格式错误:' + get.todomain + '<br>不能存在以下特殊字符【 }  { # ; \" \' 】 ')
        if public.get_webserver() != 'openlitespeed' and not get.todomain:
            get.todomain = "$host"

        # 检测目标URL格式
        if not re.match(rep, get.proxysite):
            return public.returnMsg(False, '域名格式错误 ' + get.proxysite)
        if re.search(repte, get.proxysite):
            return public.returnMsg(False, "目标URL不能有以下特殊符号 ?,=,[,],),(,*,&,^,%,$,#,@,!,~,`,{,},>,<,\,',\"]")
        # 检测目标url是否可用
        # if re.match(repd, get.proxysite):
        #     if self.__CheckUrl(get):
        #         return public.returnMsg(False, "目标URL无法访问")
        subfilter = json.loads(get.subfilter)
        # 检测替换内容
        if subfilter:
            for s in subfilter:
                if not s["sub1"]:
                    if s["sub2"]:
                        return public.returnMsg(False, '请输入被替换的内容')
                elif s["sub1"] == s["sub2"]:
                    return public.returnMsg(False, '替换内容与被替换内容不能一致')

    # 设置Nginx配置
    def SetNginx(self, get):
        ng_proxyfile = "%s/panel/vhost/nginx/proxy/%s/*.conf" % (self.setupPath, get.sitename)
        ng_file = self.setupPath + "/panel/vhost/nginx/" + get.sitename + ".conf"
        p_conf = self.__read_config(self.__proxyfile)
        cureCache = ''

        if public.get_webserver() == 'nginx':
            shutil.copyfile(ng_file, '/tmp/ng_file_bk.conf')

        # if os.path.exists('/www/server/nginx/src/ngx_cache_purge'):
        cureCache += '''
    location ~ /purge(/.*) {
        proxy_cache_purge cache_one $host$1$is_args$args;
        #access_log  /www/wwwlogs/%s_purge_cache.log;
    }''' % (get.sitename)
        if os.path.exists(ng_file):
            self.CheckProxy(get)
            ng_conf = public.readFile(ng_file)
            if not p_conf:
                # rep = "#清理缓存规则[\w\s\~\/\(\)\.\*\{\}\;\$\n\#]+.{1,66}[\s\w\/\*\.\;]+include enable-php-"
                rep = "#清理缓存规则[\w\s\~\/\(\)\.\*\{\}\;\$\n\#]+.*\n.*"
                # ng_conf = re.sub(rep, 'include enable-php-', ng_conf)
                ng_conf = re.sub(rep, '', ng_conf)
                oldconf = '''location ~ .*\\.(gif|jpg|jpeg|png|bmp|swf)$
    {
        expires      30d;
        error_log /dev/null;
        access_log /dev/null;
    }
    location ~ .*\\.(js|css)?$
    {
        expires      12h;
        error_log /dev/null;
        access_log /dev/null;
    }'''
                if "(gif|jpg|jpeg|png|bmp|swf)$" not in ng_conf:
                    ng_conf = re.sub('access_log\s*/www', oldconf + "\n\taccess_log  /www", ng_conf)
                public.writeFile(ng_file, ng_conf)
                return
            sitenamelist = []
            for i in p_conf:
                sitenamelist.append(i["sitename"])

            if get.sitename in sitenamelist:
                rep = "include.*\/proxy\/.*\*.conf;"
                if not re.search(rep, ng_conf):
                    # rep = "location.+\(gif[\w\|\$\(\)\n\{\}\s\;\/\~\.\*\\\\\?]+access_log\s+/"
                    # 移除静态文件location，原有的正则表达式卡太死
                    patt = 'location[\s~\.\*\\\\]+\((gif|js).+?\s+\}'  # 非贪婪匹配
                    rep_compile = re.compile(patt,re.S)
                    if rep_compile:
                        ng_conf = rep_compile.sub('',ng_conf)
                    ng_conf = ng_conf.replace("include enable-php-",
                                              "#清理缓存规则\n" + cureCache + "\n\t#引用反向代理规则，注释后配置的反向代理将无效\n\t" + "include " + ng_proxyfile + ";\n\n\tinclude enable-php-")
                    public.writeFile(ng_file, ng_conf)

            else:
                # rep = "#清理缓存规则[\w\s\~\/\(\)\.\*\{\}\;\$\n\#]+.{1,66}[\s\w\/\*\.\;]+include enable-php-"
                rep = "#清理缓存规则[\w\s\~\/\(\)\.\*\{\}\;\$\n\#]+.*\n.*"
                # ng_conf = re.sub(rep,'include enable-php-',ng_conf)
                ng_conf = re.sub(rep, '', ng_conf)
                oldconf = '''location ~ .*\\.(gif|jpg|jpeg|png|bmp|swf)$
    {
        expires      30d;
        error_log /dev/null;
        access_log /dev/null;
    }
    location ~ .*\\.(js|css)?$
    {
        expires      12h;
        error_log /dev/null;
        access_log /dev/null;
    }'''
                if "(gif|jpg|jpeg|png|bmp|swf)$" not in ng_conf:
                    ng_conf = re.sub('access_log\s*/www', oldconf + "\n\taccess_log  /www", ng_conf)
                public.writeFile(ng_file, ng_conf)

    # 设置apache配置
    def SetApache(self, sitename):
        ap_proxyfile = "%s/panel/vhost/apache/proxy/%s/*.conf" % (self.setupPath, sitename)
        ap_file = self.setupPath + "/panel/vhost/apache/" + sitename + ".conf"
        p_conf = public.readFile(self.__proxyfile)

        if public.get_webserver() == 'apache':
            shutil.copyfile(ap_file, '/tmp/ap_file_bk.conf')

        if os.path.exists(ap_file):
            ap_conf = public.readFile(ap_file)
            if p_conf == "[]":
                rep = "\n*#引用反向代理规则，注释后配置的反向代理将无效\n+\s+IncludeOptiona[\s\w\/\.\*]+"
                ap_conf = re.sub(rep, '', ap_conf)
                public.writeFile(ap_file, ap_conf)
                return
            if sitename in p_conf:
                rep = "combined(\n|.)+IncludeOptional.*\/proxy\/.*conf"
                rep1 = "combined"
                if not re.search(rep, ap_conf):
                    ap_conf = ap_conf.replace(rep1, rep1 + "\n\t#引用反向代理规则，注释后配置的反向代理将无效\n\t" + "\n\tIncludeOptional " + ap_proxyfile)
                    public.writeFile(ap_file, ap_conf)
            else:
                # rep = "\n*#引用反向代理(\n|.)+IncludeOptional.*\/proxy\/.*conf"
                rep = "\n*#引用反向代理规则，注释后配置的反向代理将无效\n+\s+IncludeOptiona[\s\w\/\.\*]+"
                ap_conf = re.sub(rep, '', ap_conf)
                public.writeFile(ap_file, ap_conf)

    # 设置OLS
    def _set_ols_proxy(self, get):
        # 添加反代配置
        proxyname_md5 = self.__calc_md5(get.proxyname)
        dir_path = "%s/panel/vhost/openlitespeed/proxy/%s/" % (self.setupPath, get.sitename)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        file_path = "{}{}_{}.conf".format(dir_path, proxyname_md5, get.sitename)
        reverse_proxy_conf = """
extprocessor %s {
  type                    proxy
  address                 %s
  maxConns                1000
  pcKeepAliveTimeout      600
  initTimeout             600
  retryTimeout            0
  respBuffer              0
}
""" % (get.proxyname, get.proxysite)
        public.writeFile(file_path, reverse_proxy_conf)
        # 添加urlrewrite
        dir_path = "%s/panel/vhost/openlitespeed/proxy/%s/urlrewrite/" % (self.setupPath, get.sitename)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        file_path = "{}{}_{}.conf".format(dir_path, proxyname_md5, get.sitename)
        reverse_urlrewrite_conf = """
RewriteRule ^%s(.*)$ http://%s/$1 [P,E=Proxy-Host:%s]
""" % (get.proxydir, get.proxyname, get.todomain)
        public.writeFile(file_path, reverse_urlrewrite_conf)

    # 检查伪静态、主配置文件是否有location冲突
    def CheckLocation(self, get):
        # 伪静态文件路径
        rewriteconfpath = "%s/panel/vhost/rewrite/%s.conf" % (self.setupPath, get.sitename)
        # 主配置文件路径
        nginxconfpath = "%s/nginx/conf/nginx.conf" % (self.setupPath)
        # vhost文件
        vhostpath = "%s/panel/vhost/nginx/%s.conf" % (self.setupPath, get.sitename)

        rep = "location\s+/[\n\s]+{"

        for i in [rewriteconfpath, nginxconfpath, vhostpath]:
            conf = public.readFile(i)
            if not isinstance(conf, str):
                continue
            if re.findall(rep, conf):
                return public.returnMsg(False, '伪静态/nginx主配置/vhost/文件已经存在全局反向代理')

    # 创建反向代理
    def CreateProxy(self, get):
        try:
            nocheck = get.nocheck
        except:
            nocheck = ""
        if not get.get('proxysite', None):
            return public.returnMsg(False, '目标URL不能为空')
        if not nocheck:
            if self.__CheckStart(get, "create"):
                return self.__CheckStart(get, "create")
        if public.get_webserver() == 'nginx':
            if self.CheckLocation(get):
                return self.CheckLocation(get)
        if not get.proxysite.split('//')[-1]:
            return public.returnMsg(False, '目标URL不能为[http://或https://],请填写完整URL，如：https://www.bt.cn')
        proxyUrl = self.__read_config(self.__proxyfile)
        proxyUrl.append({
            "proxyname": get.proxyname,
            "sitename": get.sitename,
            "proxydir": get.proxydir,
            "proxysite": get.proxysite,
            "todomain": get.todomain,
            "type": int(get.type),
            "cache": int(get.cache),
            "subfilter": json.loads(get.subfilter),
            "advanced": int(get.advanced),
            "cachetime": int(get.cachetime)
        })
        self.__write_config(self.__proxyfile, proxyUrl)
        self.SetNginx(get)
        self.SetApache(get.sitename)
        self._set_ols_proxy(get)
        status = self.SetProxy(get)
        if not status["status"]:
            return status
        if get.proxydir == '/':
            get.version = '00'
            get.siteName = get.sitename
            self.SetPHPVersion(get)
        public.serviceReload()
        return public.returnMsg(True, '添加成功')

    # 取代理配置文件
    def GetProxyFile(self, get):
        import files
        conf = self.__read_config(self.__proxyfile)
        sitename = get.sitename
        proxyname = get.proxyname
        proxyname_md5 = self.__calc_md5(proxyname)
        get.path = "%s/panel/vhost/%s/proxy/%s/%s_%s.conf" % (self.setupPath, get.webserver, sitename, proxyname_md5, sitename)
        for i in conf:
            if proxyname == i["proxyname"] and sitename == i["sitename"] and i["type"] != 1:
                return public.returnMsg(False, '代理已暂停')
        f = files.files()
        return f.GetFileBody(get), get.path

    # 保存代理配置文件
    def SaveProxyFile(self, get):
        import files
        f = files.files()
        return f.SaveFileBody(get)
        #	return public.returnMsg(True, '保存成功')

    # 检查是否存在#Set Nginx Cache
    def check_annotate(self, data):
        rep = "\n\s*#Set\s*Nginx\s*Cache"
        if re.search(rep, data):
            return True

    def old_proxy_conf(self, conf, ng_conf_file, get):
        rep = 'location\s*\~\*.*gif\|png\|jpg\|css\|js\|woff\|woff2\)\$'
        if not re.search(rep, conf):
            return conf
        self.RemoveProxy(get)
        self.CreateProxy(get)
        return public.readFile(ng_conf_file)

    # 修改反向代理
    def ModifyProxy(self, get):
        if not get.get('proxysite', None):
            return public.returnMsg(False, '目标URL不能为空')
        proxyname_md5 = self.__calc_md5(get.proxyname)
        ap_conf_file = "{p}/panel/vhost/apache/proxy/{s}/{n}_{s}.conf".format(
            p=self.setupPath, s=get.sitename, n=proxyname_md5)
        ng_conf_file = "{p}/panel/vhost/nginx/proxy/{s}/{n}_{s}.conf".format(
            p=self.setupPath, s=get.sitename, n=proxyname_md5)
        ols_conf_file = "{p}/panel/vhost/openlitespeed/proxy/{s}/urlrewrite/{n}_{s}.conf".format(
            p=self.setupPath, s=get.sitename, n=proxyname_md5)
        if self.__CheckStart(get):
            return self.__CheckStart(get)
        conf = self.__read_config(self.__proxyfile)
        random_string = public.GetRandomString(8)

        for i in range(len(conf)):
            if conf[i]["proxyname"] == get.proxyname and conf[i]["sitename"] == get.sitename:
                if int(get.type) != 1:
                    if not os.path.exists(ng_conf_file):
                        return public.returnMsg(False, "请先开启反向代理后再编辑！")
                    public.ExecShell("mv {f} {f}_bak".format(f=ap_conf_file))
                    public.ExecShell("mv {f} {f}_bak".format(f=ng_conf_file))
                    public.ExecShell("mv {f} {f}_bak".format(f=ols_conf_file))
                    conf[i]["type"] = int(get.type)
                    self.__write_config(self.__proxyfile, conf)
                    public.serviceReload()
                    return public.returnMsg(True, '修改成功')
                else:
                    if os.path.exists(ap_conf_file + "_bak"):
                        public.ExecShell("mv {f}_bak {f}".format(f=ap_conf_file))
                        public.ExecShell("mv {f}_bak {f}".format(f=ng_conf_file))
                        public.ExecShell("mv {f}_bak {f}".format(f=ols_conf_file))
                    ng_conf = public.readFile(ng_conf_file)
                    if not ng_conf:
                        return public.returnMsg(False, '配置文件读取错误')
                    ng_conf = self.old_proxy_conf(ng_conf, ng_conf_file, get)
                    # 修改nginx配置
                    # 如果代理URL后缀带有URI则删除URI，正则匹配不支持proxypass处带有uri
                    php_pass_proxy = get.proxysite
                    if get.proxysite[-1] == '/' or get.proxysite.count('/') > 2 or '?' in get.proxysite:
                        php_pass_proxy = re.search('(https?\:\/\/[\w\.]+)', get.proxysite).group(0)
                    # ng_conf = re.sub("location\s+%s" % conf[i]["proxydir"],"location "+get.proxydir,ng_conf)
                    ng_conf = re.sub("location\s+[\^\~]*\s?%s" % conf[i]["proxydir"], "location ^~ " + get.proxydir, ng_conf)
                    ng_conf = re.sub("proxy_pass\s+%s" % conf[i]["proxysite"], "proxy_pass " + get.proxysite, ng_conf)
                    ng_conf = re.sub("location\s+\~\*\s+\\\.\(php.*\n\{\s*proxy_pass\s+%s.*" % (php_pass_proxy),
                                     "location ~* \.(php|jsp|cgi|asp|aspx)$\n{\n\tproxy_pass %s;" % php_pass_proxy, ng_conf)
                    ng_conf = re.sub("location\s+\~\*\s+\\\.\(gif.*\n\{\s*proxy_pass\s+%s.*" % (php_pass_proxy),
                                     "location ~* \.(gif|png|jpg|css|js|woff|woff2)$\n{\n\tproxy_pass %s;" % php_pass_proxy, ng_conf)

                    backslash = ""
                    if "Host $host" in ng_conf:
                        backslash = "\\"

                    ng_conf = re.sub(r"\sHost\s+%s" % public.prevent_re_key(conf[i]["todomain"]), " Host " + get.todomain, ng_conf)
                    cache_rep = r"proxy_cache_valid\s+200\s+304\s+301\s+302\s+\d+m;((\n|.)+expires\s+\d+m;)*"
                    if int(get.cache) == 1:
                        if re.search(cache_rep, ng_conf):
                            expires_rep = "\{\n\s+expires\s+12h;"
                            ng_conf = re.sub(expires_rep, "{", ng_conf)
                            ng_conf = re.sub(cache_rep, "proxy_cache_valid 200 304 301 302 {0}m;".format(get.cachetime), ng_conf)
                        else:
                            #                         ng_cache = """
                            # proxy_ignore_headers Set-Cookie Cache-Control expires;
                            # proxy_cache cache_one;
                            # proxy_cache_key $host$uri$is_args$args;
                            # proxy_cache_valid 200 304 301 302 %sm;""" % (get.cachetime)
                            ng_cache = """
    if ( $uri ~* "\.(gif|png|jpg|css|js|woff|woff2)$" )
    {
        expires 1m;
    }
    proxy_ignore_headers Set-Cookie Cache-Control expires;
    proxy_cache cache_one;
    proxy_cache_key $host$uri$is_args$args;
    proxy_cache_valid 200 304 301 302 %sm;""" % (get.cachetime)
                            if self.check_annotate(ng_conf):
                                cache_rep = '\n\s*#Set\s*Nginx\s*Cache(.|\n)*no-cache;\s*\n*\s*\}'
                                ng_conf = re.sub(cache_rep, '\n\t\t#Set Nginx Cache\n' + ng_cache, ng_conf)
                            else:
                                # cache_rep = '#proxy_set_header\s+Connection\s+"upgrade";'
                                cache_rep = r"proxy_set_header\s+REMOTE-HOST\s+\$remote_addr;"
                                ng_conf = re.sub(cache_rep, "\n\t\tproxy_set_header REMOTE-HOST $remote_addr;\n\t\t#Set Nginx Cache" + ng_cache,
                                                 ng_conf)
                    else:
                        no_cache = """
    #Set Nginx Cache
    set $static_file%s 0;
    if ( $uri ~* "\.(gif|png|jpg|css|js|woff|woff2)$" )
    {
        set $static_file%s 1;
        expires 1m;
    }
    if ( $static_file%s = 0 )
    {
        add_header Cache-Control no-cache;
    }
}
#PROXY-END/""" % (random_string, random_string, random_string)
                        if self.check_annotate(ng_conf):
                            rep = r'\n\s*#Set\s*Nginx\s*Cache(.|\n)*'
                            # ng_conf = re.sub(rep,
                            #                  "\n\t#Set Nginx Cache\n\tproxy_ignore_headers Set-Cookie Cache-Control expires;\n\tadd_header Cache-Control no-cache;",
                            #                  ng_conf)
                            ng_conf = re.sub(rep, no_cache, ng_conf)
                        else:
                            rep = r"\s+proxy_cache\s+cache_one.*[\n\s\w\_\";\$]+m;"
                            # ng_conf = re.sub(rep,
                            #                  r"\n\t#Set Nginx Cache\n\tproxy_ignore_headers Set-Cookie Cache-Control expires;\n\tadd_header Cache-Control no-cache;",
                            #                  ng_conf)
                            ng_conf = re.sub(rep, no_cache, ng_conf)

                    sub_rep = "sub_filter"
                    subfilter = json.loads(get.subfilter)
                    if str(conf[i]["subfilter"]) != str(subfilter) or ng_conf.find('sub_filter_once') == -1:
                        if re.search(sub_rep, ng_conf):
                            sub_rep = "\s+proxy_set_header\s+Accept-Encoding(.|\n)+off;"
                            ng_conf = re.sub(sub_rep, "", ng_conf)

                        # 构造替换字符串
                        ng_subdata = ''
                        ng_sub_filter = '''
    proxy_set_header Accept-Encoding "";%s
    sub_filter_once off;'''
                        if subfilter:
                            for s in subfilter:
                                if not s["sub1"]:
                                    continue
                                if '"' in s["sub1"]:
                                    s["sub1"] = s["sub1"].replace('"', '\\"')
                                if '"' in s["sub2"]:
                                    s["sub2"] = s["sub2"].replace('"', '\\"')
                                ng_subdata += '\n\t\tsub_filter "%s" "%s";' % (s["sub1"], s["sub2"])
                        if ng_subdata:
                            ng_sub_filter = ng_sub_filter % (ng_subdata)
                        else:
                            ng_sub_filter = ''
                        sub_rep = '#Set\s+Nginx\s+Cache'
                        ng_conf = re.sub(sub_rep, '#Set Nginx Cache\n' + ng_sub_filter, ng_conf)

                    # 修改apache配置
                    ap_conf = public.readFile(ap_conf_file)
                    ap_conf = re.sub("ProxyPass\s+%s\s+%s" % (conf[i]["proxydir"], conf[i]["proxysite"]), "ProxyPass %s %s" % (get.proxydir, get.proxysite), ap_conf)
                    ap_conf = re.sub("ProxyPassReverse\s+%s\s+%s" % (conf[i]["proxydir"], conf[i]["proxysite"]),
                                     "ProxyPassReverse %s %s" % (get.proxydir, get.proxysite), ap_conf)
                    # 修改OLS配置
                    p = "{p}/panel/vhost/openlitespeed/proxy/{s}/{n}_{s}.conf".format(p=self.setupPath, n=proxyname_md5, s=get.sitename)
                    c = public.readFile(p)
                    if c:
                        rep = 'address\s+(.*)'
                        new_proxysite = 'address\t{}'.format(get.proxysite)
                        c = re.sub(rep, new_proxysite, c)
                        public.writeFile(p, c)

                    # p = "{p}/panel/vhost/openlitespeed/proxy/{s}/urlrewrite/{n}_{s}.conf".format(p=self.setupPath,n=proxyname_md5,s=get.sitename)
                    c = public.readFile(ols_conf_file)
                    if c:
                        rep = 'RewriteRule\s*\^{}\(\.\*\)\$\s+http://{}/\$1\s*\[P,E=Proxy-Host:{}\]'.format(conf[i]["proxydir"], get.proxyname, conf[i]["todomain"])
                        new_content = 'RewriteRule ^{}(.*)$ http://{}/$1 [P,E=Proxy-Host:{}]'.format(get.proxydir, get.proxyname, get.todomain)
                        c = re.sub(rep, new_content, c)
                        public.writeFile(ols_conf_file, c)

                    conf[i]["proxydir"] = get.proxydir
                    conf[i]["proxysite"] = get.proxysite
                    conf[i]["todomain"] = get.todomain
                    conf[i]["type"] = int(get.type)
                    conf[i]["cache"] = int(get.cache)
                    conf[i]["subfilter"] = json.loads(get.subfilter)
                    conf[i]["advanced"] = int(get.advanced)
                    conf[i]["cachetime"] = int(get.cachetime)

                    public.writeFile(ng_conf_file, ng_conf)
                    public.writeFile(ap_conf_file, ap_conf)
                    self.__write_config(self.__proxyfile, conf)
                    self.SetNginx(get)
                    self.SetApache(get.sitename)
                    # self.SetProxy(get)

                    # if int(get.type) != 1:
                    #     public.ExecShell("mv %s %s_bak" % (ap_conf_file, ap_conf_file))
                    #     public.ExecShell("mv %s %s_bak" % (ng_conf_file, ng_conf_file))
                    public.serviceReload()
                    return public.returnMsg(True, '修改成功')

        # 设置反向代理

    def SetProxy(self, get):
        sitename = get.sitename  # 站点名称
        advanced = int(get.advanced)
        type = int(get.type)
        cache = int(get.cache)
        cachetime = int(get.cachetime)
        proxysite = get.proxysite
        proxydir = get.proxydir
        ng_file = self.setupPath + "/panel/vhost/nginx/" + sitename + ".conf"
        ap_file = self.setupPath + "/panel/vhost/apache/" + sitename + ".conf"
        p_conf = self.__read_config(self.__proxyfile)
        random_string = public.GetRandomString(8)

        # websocket前置map
        map_file = self.setupPath + "/panel/vhost/nginx/0.websocket.conf"
        if not os.path.exists(map_file):
            map_body = '''map $http_upgrade $connection_upgrade {
    default upgrade;
    ''  close;
}
'''
            public.writeFile(map_file, map_body)

        # 配置Nginx
        # 构造清理缓存连接

        # 构造缓存配置
        ng_cache = """
    if ( $uri ~* "\.(gif|png|jpg|css|js|woff|woff2)$" )
    {
    	expires 1m;
    }
    proxy_ignore_headers Set-Cookie Cache-Control expires;
    proxy_cache cache_one;
    proxy_cache_key $host$uri$is_args$args;
    proxy_cache_valid 200 304 301 302 %sm;""" % (cachetime)
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
        # rep = "(https?://[\w\.]+)"
        # proxysite1 = re.search(rep,get.proxysite).group(1)
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
        ng_proxy_cache = ''
        proxyname_md5 = self.__calc_md5(get.proxyname)
        ng_proxyfile = "%s/panel/vhost/nginx/proxy/%s/%s_%s.conf" % (self.setupPath, sitename, proxyname_md5, sitename)
        ng_proxydir = "%s/panel/vhost/nginx/proxy/%s" % (self.setupPath, sitename)
        if not os.path.exists(ng_proxydir):
            public.ExecShell("mkdir -p %s" % ng_proxydir)

        # 构造替换字符串
        ng_subdata = ''
        ng_sub_filter = '''
    proxy_set_header Accept-Encoding "";%s
    sub_filter_once off;'''
        if get.subfilter:
            for s in json.loads(get.subfilter):
                if not s["sub1"]:
                    continue
                if '"' in s["sub1"]:
                    s["sub1"] = s["sub1"].replace('"', '\\"')
                if '"' in s["sub2"]:
                    s["sub2"] = s["sub2"].replace('"', '\\"')
                ng_subdata += '\n\tsub_filter "%s" "%s";' % (s["sub1"], s["sub2"])
        if ng_subdata:
            ng_sub_filter = ng_sub_filter % (ng_subdata)
        else:
            ng_sub_filter = ''
        # 构造反向代理
        # 如果代理URL后缀带有URI则删除URI，正则匹配不支持proxypass处带有uri
        # php_pass_proxy = get.proxysite
        # if get.proxysite[-1] == '/' or get.proxysite.count('/') > 2 or '?' in get.proxysite:
        #     php_pass_proxy = re.search('(https?\:\/\/[\w\.]+)', get.proxysite).group(0)
        if advanced == 1:
            if proxydir[-1] != '/':
                proxydir = '{}/'.format(proxydir)
            if proxysite[-1] != '/':
                proxysite = '{}/'.format(proxysite)
            if type == 1 and cache == 1:
                ng_proxy_cache += ng_proxy % (
                    proxydir, proxydir, proxysite, get.todomain, ng_sub_filter, ng_cache, get.proxydir)
            if type == 1 and cache == 0:
                ng_proxy_cache += ng_proxy % (
                    get.proxydir, get.proxydir, proxysite, get.todomain, ng_sub_filter, no_cache, get.proxydir)
        else:
            if type == 1 and cache == 1:
                ng_proxy_cache += ng_proxy % (
                    get.proxydir, get.proxydir, get.proxysite, get.todomain, ng_sub_filter, ng_cache, get.proxydir)
            if type == 1 and cache == 0:
                ng_proxy_cache += ng_proxy % (
                    get.proxydir, get.proxydir, get.proxysite, get.todomain, ng_sub_filter, no_cache, get.proxydir)
        public.writeFile(ng_proxyfile, ng_proxy_cache)

        # APACHE
        # 反向代理文件
        ap_proxyfile = "%s/panel/vhost/apache/proxy/%s/%s_%s.conf" % (self.setupPath, get.sitename, proxyname_md5, get.sitename)
        ap_proxydir = "%s/panel/vhost/apache/proxy/%s" % (self.setupPath, get.sitename)
        if not os.path.exists(ap_proxydir):
            public.ExecShell("mkdir -p %s" % ap_proxydir)
        ap_proxy = ''
        if type == 1:
            ap_proxy += '''#PROXY-START%s
<IfModule mod_proxy.c>
    ProxyRequests Off
    SSLProxyEngine on
    ProxyPass %s %s/
    ProxyPassReverse %s %s/
    </IfModule>
#PROXY-END%s''' % (get.proxydir, get.proxydir, get.proxysite, get.proxydir,
                   get.proxysite, get.proxydir)
        public.writeFile(ap_proxyfile, ap_proxy)
        isError = public.checkWebConfig()
        if (isError != True):
            if public.get_webserver() == "nginx":
                shutil.copyfile('/tmp/ng_file_bk.conf', ng_file)
                rep_upstream = re.compile(r'host not found in upstream "(?P<upstream>\S+)" in')
                err_upstream_list = []
                for tmp in rep_upstream.finditer(isError):
                    err_upstream_list.append(tmp.group("upstream"))
                if err_upstream_list:
                    isError = "nginx无法解析以下后端服务器: 【{}】\n".format(",".join(err_upstream_list)) + isError
            else:
                shutil.copyfile('/tmp/ap_file_bk.conf', ap_file)
            for i in range(len(p_conf) - 1, -1, -1):
                if get.sitename == p_conf[i]["sitename"] and p_conf[i]["proxyname"]:
                    del p_conf[i]
            self.RemoveProxy(get)
            return public.returnMsg(False, 'ERROR: %s<br><a style="color:red;">' % public.GetMsg("CONFIG_ERROR") + isError.replace("\n",
                                                                                                                                   '<br>') + '</a>')
        return public.returnMsg(True, 'SUCCESS')

    # 开启缓存
    def ProxyCache(self, get):
        if public.get_webserver() != 'nginx': return public.returnMsg(False, 'WAF_NOT_NGINX')
        file = self.setupPath + "/panel/vhost/nginx/" + get.siteName + ".conf"
        conf = public.readFile(file)
        if conf.find('proxy_pass') == -1: return public.returnMsg(False, 'SET_ERROR')
        if conf.find('#proxy_cache') != -1:
            conf = conf.replace('#proxy_cache', 'proxy_cache')
            conf = conf.replace('#expires 12h', 'expires 12h')
        else:
            conf = conf.replace('proxy_cache', '#proxy_cache')
            conf = conf.replace('expires 12h', '#expires 12h')

        public.writeFile(file, conf)
        public.serviceReload()
        return public.returnMsg(True, 'SET_SUCCESS')

    # 检查反向代理配置
    def CheckProxy(self, get):
        if public.get_webserver() != 'nginx': return True
        file = self.setupPath + "/nginx/conf/proxy.conf"
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
    proxy_cache cache_one;''' % (self.setupPath, self.setupPath)
            public.writeFile(file, conf)

        file = self.setupPath + "/nginx/conf/nginx.conf"
        conf = public.readFile(file)
        if (conf.find('include proxy.conf;') == -1):
            rep = "include\s+mime.types;"
            conf = re.sub(rep, "include mime.types;\n\tinclude proxy.conf;", conf)
            public.writeFile(file, conf)

    def get_project_find(self, project_name):
        '''
            @name 获取指定项目配置
            @author hwliang<2021-08-09>
            @param project_name<string> 项目名称
            @return dict
        '''
        project_info = public.M('sites').where('project_type=? AND name=?', ('Java', project_name)).find()
        if not project_info: return False
        project_info['project_config'] = json.loads(project_info['project_config'])
        return project_info

    # 取伪静态规则应用列表
    def GetRewriteList(self, get):
        if get.siteName.find('node_') == 0:
            get.siteName = get.siteName.replace('node_', '')
        if get.siteName.find('java_') == 0:
            get.siteName = get.siteName.replace('java_', '')
        if get.siteName.find('python_') == 0:
            get.siteName = get.siteName.replace('python_', '')
        if get.siteName.find('go_') == 0:
            get.siteName = get.siteName.replace('go_', '')
        if get.siteName.find('other_') == 0:
            get.siteName = get.siteName.replace('other_', '')
        if get.siteName.find('net_') == 0:
            get.siteName = get.siteName.replace('net_', '')
        if get.siteName.find('html_') == 0:
            get.siteName = get.siteName.replace('html_', '')
        rewriteList = {}
        ws = public.get_webserver()
        if ws == "openlitespeed":
            ws = "apache"
        if ws == 'apache':
            Java_data = self.get_project_find(get.siteName)
            if not Java_data:
                get.id = public.M('sites').where("name=?", (get.siteName,)).getField('id')
                runPath = self.GetSiteRunPath(get)
                if runPath['runPath'].find('/www/server/stop') != -1:
                    runPath['runPath'] = runPath['runPath'].replace('/www/server/stop', '')
                if public.M('sites').where("name=? AND project_type IN (?,?)  ", (get.siteName, "Go", "Other")).find():  # go和other的path是运行文件
                    rewriteList['sitePath'] = public.M('sites').where("name=?", (get.siteName,)).getField('path').rsplit("/", 1)[0] + runPath['runPath']
                else:
                    rewriteList['sitePath'] = public.M('sites').where("name=?", (get.siteName,)).getField('path') + runPath['runPath']
            if Java_data:
                if Java_data['project_config']['java_type'] == 'springboot':
                    if "static_path" in Java_data['project_config'] and Java_data['project_config']['static_path']:
                        rewriteList['sitePath'] = Java_data['project_config']['static_path']
                    else:
                        rewriteList['sitePath'] = Java_data['project_config']['jar_path']
                else:
                    get.id = public.M('sites').where("name=?", (get.siteName,)).getField('id')
                    runPath = self.GetSiteRunPath(get)
                    if runPath['runPath'].find('/www/server/stop') != -1:
                        runPath['runPath'] = runPath['runPath'].replace('/www/server/stop', '')
                    rewriteList['sitePath'] = public.M('sites').where("name=?", (get.siteName,)).getField('path') + runPath['runPath']
        rewriteList['rewrite'] = []
        rewriteList['rewrite'].append('0.' + public.getMsg('SITE_REWRITE_NOW'))
        for ds in os.listdir('rewrite/' + ws):
            if ds == 'list.txt': continue
            if '0.当前' in ds: continue
            rewriteList['rewrite'].append(ds[0:len(ds) - 5])
        rewriteList['rewrite'] = sorted(rewriteList['rewrite'])
        rewriteList['default_list'] = [
  "0.当前",
  "EduSoho",
  "EmpireCMS",
  "ShopWind",
  "crmeb",
  "dabr",
  "dbshop",
  "dedecms",
  "default",
  "discuz",
  "discuzx",
  "discuzx2",
  "discuzx3",
  "drupal",
  "ecshop",
  "emlog",
  "laravel5",
  "maccms",
  "mvc",
  "niushop",
  "pbootcms",
  "phpcms",
  "phpwind",
  "sablog",
  "seacms",
  "shopex",
  "thinkphp",
  "typecho",
  "typecho2",
  "wordpress",
  "wp2",
  "zblog"
]
        return rewriteList


    def DelRewriteTel(self, get):
        name = get.name.strip()
        default_list = [
  "0.当前",
  "EduSoho",
  "EmpireCMS",
  "ShopWind",
  "crmeb",
  "dabr",
  "dbshop",
  "dedecms",
  "default",
  "discuz",
  "discuzx",
  "discuzx2",
  "discuzx3",
  "drupal",
  "ecshop",
  "emlog",
  "laravel5",
  "maccms",
  "mvc",
  "niushop",
  "pbootcms",
  "phpcms",
  "phpwind",
  "sablog",
  "seacms",
  "shopex",
  "thinkphp",
  "typecho",
  "typecho2",
  "wordpress",
  "wp2",
  "zblog"
]
        if name in default_list:
            return public.returnMsg(False, '默认模板不可删除！')
        ws = public.get_webserver()
        if ws == "openlitespeed":
            ws = "apache"
        file_path = os.path.join('/www/server/panel/rewrite/', ws, name + '.conf')
        if os.path.exists(file_path):
            public.ExecShell('rm -rf {}'.format(file_path))
        else:
            return public.returnMsg(False, '指定模板文件不存在！')
        return public.returnMsg(True, '删除成功！')

    # 保存伪静态模板
    def SetRewriteTel(self, get):
        if not hasattr(get, "name") or not get.name.strip():
            return public.returnMsg(False, '参数错误')
        ws = public.get_webserver()
        if ws == "openlitespeed":
            ws = "apache"
        if sys.version_info[0] == 2: get.name = get.name.encode('utf-8')
        filename = 'rewrite/' + ws + '/' + get.name + '.conf'
        public.writeFile(filename, get.data)
        return public.returnMsg(True, 'SITE_REWRITE_SAVE')

    # 打包
    def ToBackup(self, get):
        if not hasattr(get, "id"):
            return public.returnMsg(False, "参数错误")
        backstage = False
        if hasattr(get, "backstage") and get.backstage == '1':
            backstage =True

        id = get.id
        find = public.M('sites').where("id=?", (id,)).field('name,path,id').find()
        # 前置磁盘检测
        backupPath = session['config']['backup_path'] + '/site'
        try:
            inode = os.statvfs(backupPath)
            if inode.f_files > 0 and inode.f_favail < 2:
                return public.returnMsg(False, '检测到磁盘Inode已耗尽，请登录SSH手动清理磁盘后重试!')
            disk = psutil.disk_usage(backupPath)
            if disk.free < public.get_dir_used(find['path']):
                return public.returnMsg(False, '检测到磁盘空间不足,请登录SSH手动清理磁盘后重试!')
        except:
            pass
        if not find:
            return public.returnMsg(False, "未找到对应网站")
        import time
        # fileName = find['name'] + '_' + time.strftime('%Y%m%d_%H%M%S', time.localtime()) + '.zip'
        fileName = find['name'] + '_' + time.strftime('%Y%m%d_%H%M%S', time.localtime()) + '.tar.gz'
        
        zipName = os.path.join(backupPath, find["name"], fileName)
        if not os.path.exists(os.path.dirname(zipName)):
            os.makedirs(os.path.dirname(zipName))

        if not os.path.exists(self.site_backup_log_path):
            public.ExecShell("mkdir -p {}".format(self.site_backup_log_path))
        tmps = '{}/site_backup_{}.log'.format(self.site_backup_log_path,id)

        execStr = "cd '" + find['path'] + "' && tar -zcvf '" + zipName + "' --exclude=.user.ini   ./ > " + tmps + " 2>&1"
        # execStr = "cd '" + find['path'] + "' && tar -zcvf '" + zipName + "' ./ > " + tmps + " 2>&1"
        # execStr = "cd '" + find['path'] + "' && zip '" + zipName + "' -x .user.ini -r ./ > " + tmps + " 2>&1"
        if backstage:
            if not os.path.exists('/bin/sh'):
                if os.path.exists('/bin/bash'):
                    try:
                        os.symlink('/bin/bash', '/bin/sh')
                    except:
                        pass
            import subprocess
            process = subprocess.Popen([execStr], shell=True, start_new_session=True)
            pid = process.pid
            public.writeFile('{}.pl'.format(zipName), str(pid))
        else:
            public.ExecShell(execStr)
        sql = public.M('backup').add('type,name,pid,filename,size,addtime', (0, fileName, find['id'], zipName, 0, public.getDate()))
        public.WriteLog('TYPE_SITE', 'SITE_BACKUP_SUCCESS', (find['name'],))
        if backstage:
            return public.returnMsg(True, '备份任务添加成功！')
        return public.returnMsg(True, 'BACKUP_SUCCESS')

    # 删除备份文件
    def DelBackup(self, get):
        id = get.id
        where = "id=?"
        backup_info = public.M('backup').where(where, (id,)).find()
        if not backup_info:
            return public.returnMsg(True, "未查询到备份文件")
        filename = backup_info['filename']
        if os.path.exists(filename): os.remove(filename)
        name = ''
        if filename == 'qiniu':
            name = backup_info['name']
            public.ExecShell(public.get_python_bin() + " " + self.setupPath + '/panel/script/backup_qiniu.py delete_file ' + name)

        pid = backup_info['pid']
        site_name = public.M('sites').where('id=?', (pid,)).getField('name')

        public.WriteLog('TYPE_SITE', 'SITE_BACKUP_DEL_SUCCESS', (site_name, filename))
        public.M('backup').where(where, (id,)).delete()
        return public.returnMsg(True, 'DEL_SUCCESS')

    # 旧版本配置文件处理
    def OldConfigFile(self):
        # 检查是否需要处理
        moveTo = 'data/moveTo.pl'
        if os.path.exists(moveTo): return

        # 处理Nginx配置文件
        filename = self.setupPath + "/nginx/conf/nginx.conf"
        if os.path.exists(filename):
            conf = public.readFile(filename)
            if conf.find('include vhost/*.conf;') != -1:
                conf = conf.replace('include vhost/*.conf;', 'include ' + self.setupPath + '/panel/vhost/nginx/*.conf;')
                public.writeFile(filename, conf)

        self.moveConf(self.setupPath + "/nginx/conf/vhost", self.setupPath + '/panel/vhost/nginx', 'rewrite', self.setupPath + '/panel/vhost/rewrite')
        self.moveConf(self.setupPath + "/nginx/conf/rewrite", self.setupPath + '/panel/vhost/rewrite')

        # 处理Apache配置文件
        filename = self.setupPath + "/apache/conf/httpd.conf"
        if os.path.exists(filename):
            conf = public.readFile(filename)
            if conf.find('IncludeOptional conf/vhost/*.conf') != -1:
                conf = conf.replace('IncludeOptional conf/vhost/*.conf', 'IncludeOptional ' + self.setupPath + '/panel/vhost/apache/*.conf')
                public.writeFile(filename, conf)

        self.moveConf(self.setupPath + "/apache/conf/vhost", self.setupPath + '/panel/vhost/apache')

        # 标记处理记录
        public.writeFile(moveTo, 'True')
        public.serviceReload()

    # 移动旧版本配置文件
    def moveConf(self, Path, toPath, Replace=None, ReplaceTo=None):
        if not os.path.exists(Path): return
        import shutil

        letPath = '/etc/letsencrypt/live'
        nginxPath = self.setupPath + '/nginx/conf/key'
        apachePath = self.setupPath + '/apache/conf/key'
        for filename in os.listdir(Path):
            # 准备配置文件
            name = filename[0:len(filename) - 5]
            filename = Path + '/' + filename
            if os.path.isdir(filename): continue
            conf = public.readFile(filename)

            # 替换关键词
            if Replace: conf = conf.replace(Replace, ReplaceTo)
            ReplaceTo = letPath + name
            Replace = 'conf/key/' + name
            if conf.find(Replace) != -1: conf = conf.replace(Replace, ReplaceTo)
            Replace = 'key/' + name
            if conf.find(Replace) != -1: conf = conf.replace(Replace, ReplaceTo)
            public.writeFile(filename, conf)

            # 提取配置信息
            if conf.find('server_name') != -1:
                self.formatNginxConf(filename)
            elif conf.find('<Directory') != -1:
                # self.formatApacheConf(filename)
                pass

            # 移动文件
            shutil.move(filename, toPath + '/' + name + '.conf')

            # 转移证书
            self.moveKey(nginxPath + '/' + name, letPath + '/' + name)
            self.moveKey(apachePath + '/' + name, letPath + '/' + name)

        # 删除多余目录
        shutil.rmtree(Path)
        # 重载服务
        public.serviceReload()

    # 从Nginx配置文件获取站点信息
    def formatNginxConf(self, filename):

        # 准备基础信息
        name = os.path.basename(filename[0:len(filename) - 5])
        if name.find('.') == -1: return
        conf = public.readFile(filename)
        # 取域名
        rep = "server_name\s+(.+);"
        tmp = re.search(rep, conf)
        if not tmp: return
        domains = tmp.groups()[0].split(' ')

        # 取根目录
        rep = "root\s+(.+);"
        tmp = re.search(rep, conf)
        if not tmp: return
        path = tmp.groups()[0]

        # 提交到数据库
        self.toSiteDatabase(name, domains, path)

    # 从Apache配置文件获取站点信息
    def formatApacheConf(self, filename):
        # 准备基础信息
        name = os.path.basename(filename[0:len(filename) - 5])
        if name.find('.') == -1: return
        conf = public.readFile(filename)

        # 取域名
        rep = "ServerAlias\s+(.+)\n"
        tmp = re.search(rep, conf)
        if not tmp: return
        domains = tmp.groups()[0].split(' ')

        # 取根目录
        rep = u"DocumentRoot\s+\"(.+)\"\n"
        tmp = re.search(rep, conf)
        if not tmp: return
        path = tmp.groups()[0]

        # 提交到数据库
        self.toSiteDatabase(name, domains, path)

    # 添加到数据库
    def toSiteDatabase(self, name, domains, path):
        if public.M('sites').where('name=?', (name,)).count() > 0: return
        public.M('sites').add('name,path,status,ps,addtime', (name, path, '1', '请输入备注', public.getDate()))
        pid = public.M('sites').where("name=?", (name,)).getField('id')
        for domain in domains:
            public.M('domain').add('pid,name,port,addtime', (pid, domain, '80', public.getDate()))

    # 移动旧版本证书
    def moveKey(self, srcPath, dstPath):
        if not os.path.exists(srcPath): return
        import shutil
        os.makedirs(dstPath)
        srcKey = srcPath + '/key.key'
        srcCsr = srcPath + '/csr.key'
        if os.path.exists(srcKey): shutil.move(srcKey, dstPath + '/privkey.pem')
        if os.path.exists(srcCsr): shutil.move(srcCsr, dstPath + '/fullchain.pem')

    # 路径处理
    def GetPath(self, path):
        if path[-1] == '/':
            return path[0:-1]
        return path

    # 日志开关
    def logsOpen(self, get):
        site_id = get.get('id') or get.get('site_id')
        if site_id is not None:
            get.name = public.M('sites').where("id=?", (site_id,)).getField('name')
        # APACHE
        filename = public.GetConfigValue('setup_path') + '/panel/vhost/apache/' + get.name + '.conf'
        if os.path.exists(filename):
            conf = public.readFile(filename)
            if conf.find('#ErrorLog') != -1:
                conf = conf.replace("#ErrorLog", "ErrorLog").replace('#CustomLog', 'CustomLog')
            else:
                conf = conf.replace("ErrorLog", "#ErrorLog").replace('CustomLog', '#CustomLog')
            public.writeFile(filename, conf)

        # NGINX
        filename = public.GetConfigValue('setup_path') + '/panel/vhost/nginx/' + get.name + '.conf'
        if os.path.exists(filename):
            conf = public.readFile(filename)
            rep = public.GetConfigValue('logs_path') + "/" + get.name + ".log"
            if conf.find(rep) != -1:
                conf = conf.replace(rep, "/dev/null")
            else:
                conf = conf.replace('access_log  /dev/null', 'access_log  ' + rep)
            public.writeFile(filename, conf)

        # OLS
        filename = public.GetConfigValue('setup_path') + '/panel/vhost/openlitespeed/detail/' + get.name + '.conf'
        conf = public.readFile(filename)
        if conf:
            rep = "\nerrorlog(.|\n)*compressArchive\s*1\s*\n}"
            tmp_res = re.search(rep, conf)
            s = 'on'
            if not tmp_res:
                s = 'off'
                rep = "\n#errorlog(.|\n)*compressArchive\s*1\s*\n#}"
                tmp_res = re.search(rep, conf)
            if tmp_res:
                tmp = tmp_res.group()
                result = ''
                if s == 'on':
                    for l in tmp.strip().splitlines():
                        result += "\n#" + l
                else:
                    for l in tmp.splitlines():
                        result += "\n" + l[1:]
                conf = re.sub(rep, "\n" + result.strip(), conf)
                public.writeFile(filename, conf)

        public.serviceReload()
        return public.returnMsg(True, 'SUCCESS')

    # 取日志状态
    def GetLogsStatus(self, get):
        filename = public.GetConfigValue(
            'setup_path') + '/panel/vhost/' + public.get_webserver() + '/' + get.name + '.conf'
        if public.get_webserver() == 'openlitespeed':
            filename = public.GetConfigValue(
                'setup_path') + '/panel/vhost/' + public.get_webserver() + '/detail/' + get.name + '.conf'
        conf = public.readFile(filename)
        if not conf: return True
        if conf.find('#ErrorLog') != -1: return False
        if conf.find("access_log  /dev/null") != -1: return False
        if re.search('\n#accesslog', conf):
            return False
        return True

    # 取目录加密状态
    def GetHasPwd(self, get):
        if not hasattr(get, 'siteName'):
            get.siteName = public.M('sites').where('id=?', (get.id,)).getField('name')
            get.configFile = self.setupPath + '/panel/vhost/nginx/' + get.siteName + '.conf'
        conf = public.readFile(get.configFile)
        if type(conf) == bool: return False
        if conf.find('#AUTH_START') != -1: return True
        return False

    # 设置目录加密
    def SetHasPwd(self, get):
        if public.get_webserver() == 'openlitespeed':
            return public.returnMsg(False, '该功能暂时还不支持OpenLiteSpeed')
        if len(get.username.strip()) < 3 or len(get.password.strip()) < 3: return public.returnMsg(False, '用户名或密码不能小于3位！')

        if len(get.password.strip()) > 8:
            return public.returnMsg(False, '密码不能大于8位，超过8位的部分无法验证！')

        if not hasattr(get, 'siteName'):
            get.siteName = public.M('sites').where('id=?', (get.id,)).getField('name')

        self.CloseHasPwd(get)
        filename = public.GetConfigValue('setup_path') + '/pass/' + get.siteName + '.pass'
        try:
            passconf = get.username + ':' + public.hasPwd(get.password)
        except:
            return public.returnMsg(False, "加密密码错误，前两位请不要使用特殊符号！")

        if get.siteName == 'phpmyadmin':
            get.configFile = self.setupPath + '/nginx/conf/nginx.conf'
            if os.path.exists(self.setupPath + '/panel/vhost/nginx/phpmyadmin.conf'):
                get.configFile = self.setupPath + '/panel/vhost/nginx/phpmyadmin.conf'
        else:
            get.configFile = self.setupPath + '/panel/vhost/nginx/' + get.siteName + '.conf'

        # 处理Nginx配置
        conf = public.readFile(get.configFile)
        if conf:
            rep = '#error_page   404   /404.html;'
            if conf.find(rep) == -1: rep = '#error_page 404/404.html;'
            data = '''
    #AUTH_START
    auth_basic "Authorization";
    auth_basic_user_file %s;
    #AUTH_END''' % (filename,)
            conf = conf.replace(rep, rep + data)
            public.writeFile(get.configFile, conf)

        if get.siteName == 'phpmyadmin':
            get.configFile = self.setupPath + '/apache/conf/extra/httpd-vhosts.conf'
            if os.path.exists(self.setupPath + '/panel/vhost/apache/phpmyadmin.conf'):
                get.configFile = self.setupPath + '/panel/vhost/apache/phpmyadmin.conf'
        else:
            get.configFile = self.setupPath + '/panel/vhost/apache/' + get.siteName + '.conf'

        conf = public.readFile(get.configFile)
        if conf:
            # 处理Apache配置
            rep = 'SetOutputFilter'
            if conf.find(rep) != -1:
                data = '''#AUTH_START
        AuthType basic
        AuthName "Authorization "
        AuthUserFile %s
        Require user %s
        #AUTH_END
        ''' % (filename, get.username)
                conf = conf.replace(rep, data + rep)
                conf = conf.replace(' Require all granted', " #Require all granted")
                public.writeFile(get.configFile, conf)

        # 写密码配置
        passDir = public.GetConfigValue('setup_path') + '/pass'
        if not os.path.exists(passDir): public.ExecShell('mkdir -p ' + passDir)
        public.writeFile(filename, passconf)
        public.serviceReload()
        public.WriteLog("TYPE_SITE", "SITE_AUTH_OPEN_SUCCESS", (get.siteName,))
        return public.returnMsg(True, 'SET_SUCCESS')

    # 取消目录加密
    def CloseHasPwd(self, get):
        if not hasattr(get, 'siteName'):
            get.siteName = public.M('sites').where('id=?', (get.id,)).getField('name')

        if get.siteName == 'phpmyadmin':
            get.configFile = self.setupPath + '/nginx/conf/nginx.conf'
            if os.path.exists('/www/server/panel/vhost/nginx/phpmyadmin.conf'):
                conf = public.readFile('/www/server/panel/vhost/nginx/phpmyadmin.conf')
                rep = "\n\s*#AUTH_START(.|\n){1,200}#AUTH_END"
                conf = re.sub(rep, '', conf)
                public.writeFile('/www/server/panel/vhost/nginx/phpmyadmin.conf', conf)
        else:
            get.configFile = self.setupPath + '/panel/vhost/nginx/' + get.siteName + '.conf'

        if os.path.exists(get.configFile):
            conf = public.readFile(get.configFile)
            rep = "\n\s*#AUTH_START(.|\n){1,200}#AUTH_END"
            conf = re.sub(rep, '', conf)
            public.writeFile(get.configFile, conf)

        if get.siteName == 'phpmyadmin':
            get.configFile = self.setupPath + '/apache/conf/extra/httpd-vhosts.conf'
        else:
            get.configFile = self.setupPath + '/panel/vhost/apache/' + get.siteName + '.conf'

        if os.path.exists(get.configFile):
            conf = public.readFile(get.configFile)
            rep = "\n\s*#AUTH_START(.|\n){1,200}#AUTH_END"
            conf = re.sub(rep, '', conf)
            conf = conf.replace(' #Require all granted', " Require all granted")
            public.writeFile(get.configFile, conf)
        public.serviceReload()
        public.WriteLog("TYPE_SITE", "SITE_AUTH_CLOSE_SUCCESS", (get.siteName,))
        return public.returnMsg(True, 'SET_SUCCESS')

    # 启用tomcat支持
    def SetTomcat(self, get):
        siteName = get.siteName
        name = siteName.replace('.', '_')

        rep = "^(\d{1,3}\.){3,3}\d{1,3}$"
        if re.match(rep, siteName): return public.returnMsg(False, 'TOMCAT_IP')

        # nginx
        filename = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        if os.path.exists(filename):
            conf = public.readFile(filename)
            if conf.find('#TOMCAT-START') != -1: return self.CloseTomcat(get)
            tomcatConf = '''#TOMCAT-START
    location /
    {
        proxy_pass "http://%s:8080";
        proxy_set_header Host %s;
        proxy_set_header X-Forwarded-For $remote_addr;
    }
    location ~ .*\.(gif|jpg|jpeg|bmp|png|ico|txt|js|css)$
    {
        expires      12h;
    }

    location ~ .*\.war$
    {
        return 404;
    }
    #TOMCAT-END
    ''' % (siteName, siteName)
            rep = 'include enable-php'
            conf = conf.replace(rep, tomcatConf + rep)
            public.writeFile(filename, conf)

        # apache
        filename = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
        if os.path.exists(filename):
            conf = public.readFile(filename)
            if conf.find('#TOMCAT-START') != -1: return self.CloseTomcat(get)
            tomcatConf = '''#TOMCAT-START
    <IfModule mod_proxy.c>
        ProxyRequests Off
        SSLProxyEngine on
        ProxyPass / http://%s:8080/
        ProxyPassReverse / http://%s:8080/
        RequestHeader unset Accept-Encoding
        ExtFilterDefine fixtext mode=output intype=text/html cmd="/bin/sed 's,:8080,,g'"
        SetOutputFilter fixtext
    </IfModule>
    #TOMCAT-END
    ''' % (siteName, siteName)

            rep = '#PATH'
            conf = conf.replace(rep, tomcatConf + rep)
            public.writeFile(filename, conf)
        path = public.M('sites').where("name=?", (siteName,)).getField('path')
        import tomcat
        tomcat.tomcat().AddVhost(path, siteName)
        public.serviceReload()
        public.ExecShell('/etc/init.d/tomcat stop')
        public.ExecShell('/etc/init.d/tomcat start')
        public.ExecShell('echo "127.0.0.1 ' + siteName + '" >> /etc/hosts')
        public.WriteLog('TYPE_SITE', 'SITE_TOMCAT_OPEN', (siteName,))
        return public.returnMsg(True, 'SITE_TOMCAT_OPEN')

    # 关闭tomcat支持
    def CloseTomcat(self, get):
        if not os.path.exists('/etc/init.d/tomcat'): return False
        siteName = get.siteName
        name = siteName.replace('.', '_')

        # nginx
        filename = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        if os.path.exists(filename):
            conf = public.readFile(filename)
            rep = "\s*#TOMCAT-START(.|\n)+#TOMCAT-END"
            conf = re.sub(rep, '', conf)
            public.writeFile(filename, conf)

        # apache
        filename = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
        if os.path.exists(filename):
            conf = public.readFile(filename)
            rep = "\s*#TOMCAT-START(.|\n)+#TOMCAT-END"
            conf = re.sub(rep, '', conf)
            public.writeFile(filename, conf)
        public.ExecShell('rm -rf ' + self.setupPath + '/panel/vhost/tomcat/' + name)
        try:
            import tomcat
            tomcat.tomcat().DelVhost(siteName)
        except:
            pass
        public.serviceReload()
        public.ExecShell('/etc/init.d/tomcat restart')
        public.ExecShell("sed -i '/" + siteName + "/d' /etc/hosts")
        public.WriteLog('TYPE_SITE', 'SITE_TOMCAT_CLOSE', (siteName,))
        return public.returnMsg(True, 'SITE_TOMCAT_CLOSE')

    # 取当站点前运行目录
    def GetSiteRunPath(self, get):
        siteName = public.M('sites').where('id=?', (get.id,)).getField('name')
        sitePath = public.M('sites').where('id=?', (get.id,)).getField('path')
        if not siteName or os.path.isfile(sitePath): return {"runPath": "/", 'dirs': []}
        path = sitePath
        if public.get_webserver() == 'nginx':
            filename = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
            if os.path.exists(filename):
                conf = public.readFile(filename)
                rep = '\s*root\s+(.+);'
                tmp1 = re.search(rep, conf)
                if tmp1: path = tmp1.groups()[0]
        elif public.get_webserver() == 'apache':
            filename = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
            if os.path.exists(filename):
                conf = public.readFile(filename)
                rep = '\s*DocumentRoot\s*"(.+)"\s*\n'
                tmp1 = re.search(rep, conf)
                if tmp1: path = tmp1.groups()[0]
        else:
            filename = self.setupPath + '/panel/vhost/openlitespeed/' + siteName + '.conf'
            if os.path.exists(filename):
                conf = public.readFile(filename)
                rep = "vhRoot\s*(.*)"
                path = re.search(rep, conf)
                if not path:
                    return public.returnMsg(False, "Get Site run path false")
                path = path.groups()[0]
        data = {}
        if sitePath == path:
            data['runPath'] = '/'
        else:
            data['runPath'] = path.replace(sitePath, '')

        dirnames = []
        dirnames.append('/')
        if not os.path.exists(sitePath):
            os.makedirs(sitePath)

        # def get_sub_path(sub_path_name, num):
        #     if num == 0:
        #         return
        #     for filename in os.listdir(sub_path_name):
        #         try:
        #             if sys.version_info[0] == 2:
        #                 filename = filename.encode('utf-8')
        #             else:
        #                 filename.encode('utf-8')
        #             filePath = sub_path_name + '/' + filename
        #             if os.path.islink(filePath):
        #                 continue
        #             if os.path.isdir(filePath):
        #                 dirnames.append(filePath[len(sitePath):])
        #                 get_sub_path(filePath, num-1)
        #         except:
        #             pass
        # get_sub_path(sitePath, 1)

        # 优化目录的获取速度
        dirnames = []
        if os.path.exists(sitePath):
            dirnames = ['/' + entry.name for entry in os.scandir(sitePath) if entry.is_dir(follow_symlinks=False) and not entry.is_symlink()]
        data['dirs'] = ['/'] + dirnames
        return data

    # 设置当前站点运行目录
    def SetSiteRunPath(self, get):
        siteName = public.M('sites').where('id=?', (get.id,)).getField('name')
        sitePath = public.M('sites').where('id=?', (get.id,)).getField('path')
        old_run_path = self.GetRunPath(get)
        # 处理Nginx
        filename = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        if os.path.exists(filename):
            conf = public.readFile(filename)
            if conf:
                rep = '\s*root\s+(.+);'
                tmp = re.search(rep, conf)
                if tmp:
                    path = tmp.groups()[0]
                    conf = conf.replace(path, sitePath + get.runPath)
                    public.writeFile(filename, conf)

        # 处理Apache
        filename = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
        if os.path.exists(filename):
            conf = public.readFile(filename)
            if conf:
                rep = '\s*DocumentRoot\s*"(.+)"\s*\n'
                tmp = re.search(rep, conf)
                if tmp:
                    path = tmp.groups()[0]
                    conf = conf.replace(path, sitePath + get.runPath)
                    public.writeFile(filename, conf)
        # 处理OLS
        self._set_ols_run_path(sitePath, get.runPath, siteName)
        # self.DelUserInI(sitePath)
        # get.path = sitePath;
        # self.SetDirUserINI(get)
        s_path = sitePath + old_run_path + "/.user.ini"
        d_path = sitePath + get.runPath + "/.user.ini"
        if s_path != d_path:
            public.ExecShell("chattr -i {}".format(s_path))
            public.ExecShell("mv {} {}".format(s_path, d_path))
            public.ExecShell("chattr +i {}".format(d_path))

        public.serviceReload()
        return public.returnMsg(True, 'SET_SUCCESS')

    def _set_ols_run_path(self, site_path, run_path, sitename):
        ols_conf_file = "{}/panel/vhost/openlitespeed/{}.conf".format(self.setupPath, sitename)
        ols_conf = public.readFile(ols_conf_file)
        if not ols_conf:
            return
        reg = '#VHOST\s*{s}\s*START(.|\n)+#VHOST\s*{s}\s*END'.format(s=sitename)
        tmp = re.search(reg, ols_conf)
        if not tmp:
            return
        reg = "vhRoot\s*(.*)"
        # tmp = re.search(reg,tmp.group())
        # if not tmp:
        #     return
        tmp = "vhRoot " + site_path + run_path
        ols_conf = re.sub(reg, tmp, ols_conf)
        public.writeFile(ols_conf_file, ols_conf)

    # 设置默认站点
    def SetDefaultSite(self, get):
        import time
        if public.GetWebServer() in ['openlitespeed']:
            return public.returnMsg(False, '暂时不支持OpenLiteSpeed设置默认站点')
        default_site_save = 'data/defaultSite.pl'
        # 清理旧的
        defaultSite = public.readFile(default_site_save)
        http2 = ''
        versionStr = public.readFile('/www/server/nginx/version.pl')
        if versionStr:
            if versionStr.find('1.8.1') == -1:
                http2 = ' http2'
        use_http2_on = public.is_change_nginx_http2()
        if use_http2_on:
            http2 = ''

        if defaultSite:
            path = self.setupPath + '/panel/vhost/nginx/' + defaultSite + '.conf'
            if os.path.exists(path):
                conf = public.readFile(path)
                rep = "listen\s+80.+;"
                conf = re.sub(rep, 'listen 80;', conf, 1)
                rep = "listen\s+\[::\]:80.+;"
                conf = re.sub(rep, 'listen [::]:80;', conf, 1)
                rep = "listen\s+443\s+ssl.+;"
                conf = re.sub(rep, 'listen 443 ssl' + http2 + ';', conf, 1)
                rep = "listen\s+443\s+quic.+;"
                conf = re.sub(rep, 'listen 443 quic;', conf, 1)
                rep = "listen\s+\[::\]:443\s+ssl.+;"
                conf = re.sub(rep, 'listen [::]:443 ssl' + http2 + ';', conf, 1)
                rep = "listen\s+\[::\]:443\s+quic.+;"
                conf = re.sub(rep, 'listen [::]:443 quic;', conf, 1)

                if use_http2_on:
                    # 有ssl配置， 且没有http2
                    if conf.find('ssl_certificate') != -1:
                        if not re.search(r"http2\s+on;", conf):
                            rep_listen = re.compile(r"listen\s+[\[\]:]*(\d+).*\n", re.M)
                            res = rep_listen.search(conf)
                            if res:
                                conf = conf[:res.end()] + "    http2 on;\n" + conf[res.end():]
                    else:
                        # 没有ssl配置， 尝试清除http2
                        conf = re.sub(r"\s*http2\s+on;", "", conf)

                public.writeFile(path, conf)

            path = self.setupPath + '/apache/htdocs/.htaccess'
            if os.path.exists(path): os.remove(path)

        if get.name == '0':
            if os.path.exists(default_site_save): os.remove(default_site_save)
            public.serviceReload()
            return public.returnMsg(True, '设置成功!')

        # 处理新的
        path = self.setupPath + '/apache/htdocs'
        if os.path.exists(path):
            conf = '''<IfModule mod_rewrite.c>
  RewriteEngine on
  RewriteCond %{HTTP_HOST} !^127.0.0.1 [NC]
  RewriteRule (.*) http://%s/$1 [L]
</IfModule>'''
            conf = conf.replace("%s", get.name)
            if get.name == 'off': conf = ''
            public.writeFile(path + '/.htaccess', conf)

        path = self.setupPath + '/panel/vhost/nginx/' + get.name + '.conf'
        if os.path.exists(path):
            http3_v4 = ''
            http3_v6 = ''
            if self.is_nginx_http3():
                http3_v4 = "\n    listen 443 quic default_server;"
                http3_v6 = "\n    listen [::]:443 quic default_server;"

            conf = public.readFile(path)
            conf = re.sub(r"\s*listen\s+[\[:\]]*\d+\s+quic.*;", '', conf)
            rep = "listen\s+80\s*;"
            conf = re.sub(rep, 'listen 80 default_server;', conf, 1)
            rep = "listen\s+\[::\]:80\s*;"
            conf = re.sub(rep, 'listen [::]:80 default_server;', conf, 1)
            rep = "listen\s+443\s*ssl\s*\w*\s*;"
            conf = re.sub(rep, 'listen 443 ssl' + http2 + ' default_server;' + http3_v4, conf, 1)
            rep = "listen\s+\[::\]:443\s*ssl\s*\w*\s*;"
            conf = re.sub(rep, 'listen [::]:443 ssl' + http2 + ' default_server;' + http3_v6, conf, 1)
            if use_http2_on:
                # 有ssl配置， 且没有http2
                if conf.find('ssl_certificate') != -1:
                    if not re.search(r"http2\s+on;", conf):
                        rep_listen = re.compile(r"listen\s+[\[\]:]*(\d+).*\n", re.M)
                        res = rep_listen.search(conf)
                        if res:
                            conf = conf[:res.end()] + "    http2 on;\n" + conf[res.end():]
                else:
                    # 没有ssl配置， 尝试清除http2
                    conf = re.sub(r"\s*http2\s+on;", "", conf)

            public.writeFile(path, conf)

        path = self.setupPath + '/panel/vhost/nginx/default.conf'
        if os.path.exists(path): public.ExecShell('rm -f ' + path)
        public.writeFile(default_site_save, get.name)
        public.serviceReload()
        return public.returnMsg(True, 'SET_SUCCESS')

    # 取默认站点
    def GetDefaultSite(self, get):
        data = {}
        data['sites'] = public.M('sites').where('project_type=?', 'PHP').field('name').order('id desc').select()
        data['defaultSite'] = public.readFile('data/defaultSite.pl')
        return data

    # 扫描站点
    def CheckSafe(self, get):
        import db, time
        isTask = '/tmp/panelTask.pl'
        if os.path.exists(self.setupPath + '/panel/class/panelSafe.py'):
            import py_compile
            py_compile.compile(self.setupPath + '/panel/class/panelSafe.py')
        get.path = public.M('sites').where('id=?', (get.id,)).getField('path')
        execstr = "cd " + public.GetConfigValue('setup_path') + "/panel/class && " + public.get_python_bin() + " panelSafe.pyc " + get.path
        sql = db.Sql()
        public.Mpublic.M('tasks').add('id,name,type,status,addtime,execstr', (None, '扫描目录 [' + get.path + ']', 'execshell', '0', time.strftime('%Y-%m-%d %H:%M:%S'), execstr))
        public.writeFile(isTask, 'True')
        public.WriteLog('TYPE_SETUP', 'SITE_SCAN_ADD', (get.path,))
        return public.returnMsg(True, 'SITE_SCAN_ADD')

    # 获取结果信息
    def GetCheckSafe(self, get):
        get.path = public.M('sites').where('id=?', (get.id,)).getField('path')
        path = get.path + '/scan.pl'
        result = {}
        result['data'] = []
        result['phpini'] = []
        result['userini'] = result['sshd'] = True
        result['scan'] = False
        result['outime'] = result['count'] = result['error'] = 0
        if not os.path.exists(path): return result
        import json
        return json.loads(public.readFile(path))

    # 更新病毒库
    def UpdateRulelist(self, get):
        try:
            conf = public.httpGet(public.getUrl() + '/install/ruleList.conf')
            if conf:
                public.writeFile(self.setupPath + '/panel/data/ruleList.conf', conf)
                return public.returnMsg(True, 'UPDATE_SUCCESS')
            return public.returnMsg(False, 'CONNECT_ERR')
        except:
            return public.returnMsg(False, 'CONNECT_ERR')

    def set_site_etime_multiple(self, get):
        '''
            @name 批量网站到期时间
            @author zhwen<2020-11-17>
            @param sites_id "1,2"
            @param edate 2020-11-18
        '''
        try:
            sites_id = get.sites_id.split(',')
        except:
            return public.returnMsg(False, '参数错误')
        set_edate_successfully = []
        set_edate_failed = {}
        for site_id in sites_id:
            get.id = site_id
            site_name = public.M('sites').where("id=?", (site_id,)).getField('name')
            if not site_name:
                continue
            try:
                self.SetEdate(get)
                set_edate_successfully.append(site_name)
            except:
                set_edate_failed[site_name] = '设置时错误了，请再试一次'
                pass
        return {'status': True, 'msg': '设置网站 [ {} ] 到期时间成功'.format(','.join(set_edate_successfully)), 'error': set_edate_failed,
                'success': set_edate_successfully}

    # 设置到期时间
    def SetEdate(self, get):
        result = public.M('sites').where('id=?', (get.id,)).setField('edate', get.edate)
        siteName = public.M('sites').where('id=?', (get.id,)).getField('name')
        public.WriteLog('TYPE_SITE', 'SITE_EXPIRE_SUCCESS', (siteName, get.edate))
        return public.returnMsg(True, 'SITE_EXPIRE_SUCCESS')

    # 获取防盗链状态
    def GetSecurity(self, get):
        file = '/www/server/panel/vhost/nginx/' + get.name + '.conf'
        conf = public.readFile(file)
        data = {}
        if type(conf) == bool: return public.returnMsg(False, '读取配置文件失败!')
        if conf.find('SECURITY-START') != -1:
            rep = "#SECURITY-START(\n|.)+#SECURITY-END"
            tmp = re.search(rep, conf).group()
            content = re.search("\(.+\)\$", tmp)
            if content:
                data['fix'] = content.group().replace('(', '').replace(')$', '').replace('|', ',')
            else:
                data['fix'] = ''
            try:
                data['domains'] = ','.join(list(set(re.search("valid_referers\s+none\s+blocked\s+(.+);\n", tmp).groups()[0].split())))
            except:
                data['domains'] = ','.join(list(set(re.search("valid_referers\s+(.+);\n", tmp).groups()[0].split())))
            data['status'] = True
            data['http_status'] = tmp.find('none blocked') != -1
            try:
                data['return_rule'] = re.findall(r'(return|rewrite)\s+.*(\d{3}|(/.+)\s+(break|last));', conf)[0][1].replace('break', '').strip()
            except:
                data['return_rule'] = '404'
        else:
            conf_file = self.conf_dir + '/{}_door_chain.json'.format(get.name)
            try:
                data = json.loads(public.readFile(conf_file))
                data['status'] = data['status'] == "true"
            except:
                data = {}
                data['fix'] = 'jpg,jpeg,gif,png,js,css'
                domains = public.M('domain').where('pid=?', (get.id,)).field('name').select()
                tmp = []
                for domain in domains:
                    tmp.append(domain['name'])
                data['domains'] = ','.join(tmp)
                data['return_rule'] = '404'
                data['status'] = False
                data['http_status'] = False
        return data

    # 设置防盗链
    def SetSecurity(self, get):
        if len(get.fix) < 2: return public.returnMsg(False, 'URL后缀不能为空!')
        if len(get.domains) < 3: return public.returnMsg(False, '防盗链域名不能为空!')
        get.return_rule = get.return_rule.strip()
        if get.return_rule in ['404', '403', '200', '301', '302', '401', '201']:
            return_rule = 'return {}'.format(get.return_rule)
        else:
            if get.return_rule[0] != '/':
                return public.returnMsg(False, "响应资源应使用URI路径或HTTP状态码，如：/test.png 或 404")
            return_rule = 'rewrite /.* {} break'.format(get.return_rule)
        conf_file = self.conf_dir + '/{}_door_chain.json'.format(get.name)
        data = {
            "name": get.name,
            "fix": get.fix,
            "domains": get.domains,
            "status": get.status,
            "http_status": get.http_status,
            "return_rule": get.return_rule,
        }
        public.writeFile(conf_file, json.dumps(data))
        # nginx
        file = '/www/server/panel/vhost/nginx/' + get.name + '.conf'
        if os.path.exists(file):
            conf = public.readFile(file)
            if conf.find('SECURITY-START') != -1:
                # 先替换域名部分，防止域名过多导致替换失败
                rep = "\s+valid_referers.+"
                conf = re.sub(rep, '', conf)
                # 再替换配置部分
                rep = "\s+#SECURITY-START(\n|.){1,500}#SECURITY-END\n?"
                conf = re.sub(rep, '\n', conf)
            if get.status == 'false':
                public.WriteLog('网站管理', '站点[' + get.name + ']已关闭防盗链设置!')
                public.writeFile(file, conf)
            elif get.status == 'true':
                if conf.find('SECURITY-START') == -1:
                    return_rule = 'return 404'
                    if 'return_rule' in get:
                        get.return_rule = get.return_rule.strip()
                        if get.return_rule in ['404', '403', '200', '301', '302', '401', '201']:
                            return_rule = 'return {}'.format(get.return_rule)
                        else:
                            if get.return_rule[0] != '/':
                                return public.returnMsg(False, "响应资源应使用URI路径或HTTP状态码，如：/test.png 或 404")
                            return_rule = 'rewrite /.* {} break'.format(get.return_rule)
                    rconf = '''#SECURITY-START 防盗链配置
    location ~ .*\.(%s)$
    {
        expires      30d;
        access_log /dev/null;
        valid_referers %s;
        if ($invalid_referer){
           %s;
        }
    }
    #SECURITY-END
    include enable-php-''' % (
                        get.fix.strip().replace(',', '|'), get.domains.strip().replace(',', ' '), return_rule)
                    conf = re.sub("include\s+enable-php-", rconf, conf)
                    public.WriteLog('网站管理', '站点[' + get.name + ']已开启防盗链!')

                r_key = 'valid_referers none blocked'
                d_key = 'valid_referers'
                if get.http_status == 'true' and conf.find(r_key) == -1:
                    conf = conf.replace(d_key, r_key)
                elif get.http_status == 'false' and conf.find(r_key) != -1:
                    conf = conf.replace(r_key, d_key)
                public.writeFile(file, conf)

        # apache
        file = '/www/server/panel/vhost/apache/' + get.name + '.conf'
        if os.path.exists(file):
            conf = public.readFile(file)
            if conf.find('SECURITY-START') != -1:
                rep = "#SECURITY-START(\n|.){1,500}#SECURITY-END\n"
                conf = re.sub(rep, '', conf)
            if get.status == "false":
                public.writeFile(file, conf)
            elif get.status == 'true':
                if conf.find('SECURITY-START') == -1:
                    return_rule = '/404.html [R=404,NC,L]'
                    if 'return_rule' in get:
                        get.return_rule = get.return_rule.strip()
                        if get.return_rule in ['404', '403', '200', '301', '302', '401', '201']:
                            return_rule = '/{s}.html [R={s},NC,L]'.format(s=get.return_rule)
                        else:
                            if get.return_rule[0] != '/':
                                return public.returnMsg(False, "响应资源应使用URI路径或HTTP状态码，如：/test.png 或 404")
                            return_rule = '{}'.format(get.return_rule)

                    tmp = "    RewriteCond %{HTTP_REFERER} !{DOMAIN} [NC]"
                    tmps = []
                    for d in get.domains.split(','):
                        tmps.append(tmp.replace('{DOMAIN}', d))
                    domains = "\n".join(tmps)
                    rconf = "combined\n    #SECURITY-START 防盗链配置\n    RewriteEngine on\n" + domains + "\n    RewriteRule .(" + get.fix.strip().replace(
                        ',', '|') + ") " + return_rule + "\n    #SECURITY-END"
                    conf = conf.replace('combined', rconf)

                r_key = '#SECURITY-START 防盗链配置\n    RewriteEngine on\n    RewriteCond %{HTTP_REFERER} !^$ [NC]\n'
                d_key = '#SECURITY-START 防盗链配置\n    RewriteEngine on\n'
                if get.http_status == 'true' and conf.find(r_key) == -1:
                    conf = conf.replace(d_key, r_key)
                elif get.http_status == 'false' and conf.find(r_key) != -1:
                    if conf.find('SECURITY-START') == -1: return public.returnMsg(False, '请先开启防盗链!')
                    conf = conf.replace(r_key, d_key)
                public.writeFile(file, conf)
        # OLS
        cond_dir = '/www/server/panel/vhost/openlitespeed/prevent_hotlink/'
        if not os.path.exists(cond_dir):
            os.makedirs(cond_dir)
        file = cond_dir + get.name + '.conf'
        if get.http_status == 'true':
            conf = """
RewriteCond %{HTTP_REFERER} !^$
RewriteCond %{HTTP_REFERER} !BTDOMAIN_NAME [NC]
RewriteRule \.(BTPFILE)$    /404.html   [R,NC]
"""
            conf = conf.replace('BTDOMAIN_NAME', get.domains.replace(',', ' ')).replace('BTPFILE', get.fix.replace(',', '|'))
        else:
            conf = """
RewriteCond %{HTTP_REFERER} !BTDOMAIN_NAME [NC]
RewriteRule \.(BTPFILE)$    /404.html   [R,NC]
"""
            conf = conf.replace('BTDOMAIN_NAME', get.domains.replace(',', ' ')).replace('BTPFILE', get.fix.replace(',', '|'))
        public.writeFile(file, conf)
        if get.status == "false":
            if os.path.exists(file): os.remove(file)
        public.serviceReload()
        return public.returnMsg(True, 'SET_SUCCESS')

    # xss 防御
    def xsssec(self, text):
        replace_list = {
            "<": "＜",
            ">": "＞",
            "'": "＇",
            '"': "＂",
        }
        for k, v in replace_list.items():
            text = text.replace(k, v)
        return public.xssencode2(text)

    # 取网站日志
    def GetSiteLogs(self, get):
        logsPath = '/www/wwwlogs/'
        res = public.M('sites').where('name=?', (get.siteName,)).select()[0]['project_type'].lower()
        if res == 'php':
            res = ''
        else:
            res = res + '_'

        serverType = public.get_webserver()
        re_log_file = None
        if serverType == "nginx":
            config_path = '/www/server/panel/vhost/nginx/{}.conf'.format(res + get.siteName)
            config = public.readFile(config_path)
            re_log_file = self.nginx_get_log_file(config, is_error_log=False)
        elif serverType == 'apache':
            config_path = '/www/server/panel/vhost/apache/{}.conf'.format(res + get.siteName)
            config = public.readFile(config_path)
            if not config:
                print('|-正在处理网站:未检测到{}站点的日志'.format(get.siteName))
                return
            re_log_file = self.apache_get_log_file(config, is_error_log=False)

        if re_log_file is not None and os.path.exists(re_log_file):
            return public.returnMsg(True, self.xsssec(public.GetNumLines(re_log_file, 1000)))

        if serverType == "nginx":
            logPath = logsPath + get.siteName + '.log'
        elif serverType == 'apache':
            logPath = logsPath + get.siteName + '-access_log'
        else:
            logPath = logsPath + get.siteName + '_ols.access_log'
        if not os.path.exists(logPath):
            return public.returnMsg(False, '日志为空')
        return public.returnMsg(True, self.xsssec(public.GetNumLines(logPath, 1000)))

    # 取网站错误日志
    def get_site_errlog(self, get):
        serverType = public.get_webserver()
        logsPath = '/www/wwwlogs/'
        res = public.M('sites').where('name=?', (get.siteName,)).select()[0]['project_type'].lower()
        if res == 'php':
            res = ''
        else:
            res = res + '_'

        serverType = public.get_webserver()
        re_log_file = None
        if serverType == "nginx":
            config_path = '/www/server/panel/vhost/nginx/{}.conf'.format(res + get.siteName)
            config = public.readFile(config_path)
            if not config:
                return public.returnMsg(False, '配置文件丢失，无法读取到日志文件信息')
            re_log_file = self.nginx_get_log_file(config, is_error_log=True)
        elif serverType == 'apache':
            config_path = '/www/server/panel/vhost/apache/{}.conf'.format(res + get.siteName)
            config = public.readFile(config_path)
            if not config:
                print('|-正在处理网站:未检测到{}站点的日志'.format(get.siteName))
                return public.returnMsg(False, '配置文件丢失，无法读取到日志文件信息')
            re_log_file = self.apache_get_log_file(config, is_error_log=True)

        if re_log_file is not None and os.path.exists(re_log_file):
            return public.returnMsg(True, self.xsssec(public.GetNumLines(re_log_file, 1000)))

        if serverType == "nginx":
            logPath = logsPath + get.siteName + '.error.log'
        elif serverType == 'apache':
            logPath = logsPath + get.siteName + '-error_log'
        else:
            logPath = logsPath + get.siteName + '_ols.error_log'
        if not os.path.exists(logPath):
            return public.returnMsg(False, '日志为空')
        return public.returnMsg(True, self.xsssec(public.GetNumLines(logPath, 1000)))

    @staticmethod
    def nginx_get_log_file(nginx_config: str, is_error_log: bool = False):
        if is_error_log:
            re_data = re.findall(r"error_log +(/(\S+/?)+) ?(.*?);", nginx_config)
        else:
            re_data = re.findall(r"access_log +(/(\S+/?)+) ?(.*?);", nginx_config)
        if re_data is None:
            return None
        for i in re_data:
            file_path = i[0].strip(";")
            if file_path != "/dev/null":
                return file_path
        return None

    @staticmethod
    def apache_get_log_file(apache_config: str, is_error_log: bool = False):
        if is_error_log:
            re_data = re.findall(r'''ErrorLog +['"]?(/(\S+/?)+)['"]? ?(.*?)\n''', apache_config)
        else:
            re_data = re.findall(r'''CustomLog +['"]?(/(\S+/?)+)['"]? ?(.*?)\n''', apache_config)
        if re_data is None:
            return None
        for i in re_data:
            file_path = i[0].strip('"').strip("'")
            if file_path != "/dev/null":
                return file_path
        return None

    def check_and_add_stop_column(self):
            query_result = public.M('sites').field('stop').select()
            if "no such column: stop" in query_result:
                    try:
                        # alter_sql = "ALTER TABLE sites ADD COLUMN stop INTEGER DEFAULT 0"
                        # public.M('sites').execute(alter_sql, ())
                        public.M('sites').execute("ALTER TABLE 'sites' ADD 'stop' TEXT DEFAULT ''", ())
                    except Exception as e:
                        pass

    # 取网站分类
    def get_site_types(self, get):
        self.check_and_add_stop_column()
        search = get.search if "search" in get else None
        if search is not None and bool(search):
            like_str = "name LIKE '%{}%' ESCAPE '/'".format(self._sqlite_like_replace(search))
            data = public.M("site_types").where(like_str, ()).field("id,name").order("id asc").select()
        else:
            data = public.M("site_types").field("id,name").order("id asc").select()
        if isinstance(data, str) and data.startswith("error"):
            raise public.PanelError("查询数据库错误：" + data)
        data.insert(0, {"id": 0, "name": "默认分类"})
        data.insert(1, {"id": -2, "name": "已停止网站"})
        for i in data:
            i['name'] = public.xss_version(i['name'])
        return data

    @staticmethod
    def _sqlite_like_replace(data_str: str) -> str:
        key_list = ('/', '%', '(', ')', '[', ']', '&', '_')
        res = ''
        for c in data_str:
            if c in key_list:
                res += "/" + c
            elif c == "'":
                res += "''"
            else:
                res += c
        return res

    # 添加网站分类
    def add_site_type(self, get):
        get.name = get.name.strip()
        if not get.name: return public.returnMsg(False, "分类名称不能为空")
        if len(get.name) > 16: return public.returnMsg(False, "分类名称长度不能超过16位")
        type_sql = public.M('site_types')
        if type_sql.count() >= 30: return public.returnMsg(False, '最多添加30个分类!')
        if type_sql.where('name=?', (get.name,)).count() > 0: return public.returnMsg(False, "指定分类名称已存在!")
        type_sql.add("name", (public.xssencode2(get.name),))
        return public.returnMsg(True, '添加成功!')

    # 删除网站分类
    def remove_site_type(self, get):
        type_sql = public.M('site_types')
        if type_sql.where('id=?', (get.id,)).count() == 0: return public.returnMsg(False, "指定分类不存在!")
        type_sql.where('id=?', (get.id,)).delete()
        public.M("sites").where("type_id=?", (get.id,)).save("type_id", (0,))
        return public.returnMsg(True, "分类已删除!")

    # 修改网站分类名称
    def modify_site_type_name(self, get):
        get.name = get.name.strip()
        if not get.name: return public.returnMsg(False, "分类名称不能为空")
        if len(get.name) > 16: return public.returnMsg(False, "分类名称长度不能超过16位")
        type_sql = public.M('site_types')
        if type_sql.where('id=?', (get.id,)).count() == 0: return public.returnMsg(False, "指定分类不存在!")
        if type_sql.where('name=? AND id!=?', (get.name, get.id)).count() > 0: return public.returnMsg(False, "指定分类名称已存在!")
        type_sql.where('id=?', (get.id,)).setField('name', get.name)
        return public.returnMsg(True, "修改成功!")

    # 设置指定站点的分类
    def set_site_type(self, get):
        site_ids = json.loads(get.site_ids)
        site_sql = public.M("sites")
        for s_id in site_ids:
            site_sql.where("id=?", (s_id,)).setField("type_id", get.id)
        return public.returnMsg(True, "设置成功!")

    # 设置目录保护
    def set_dir_auth(self, get):
        sd = site_dir_auth.SiteDirAuth()
        return sd.set_dir_auth(get)

    def delete_dir_auth_multiple(self, get):
        '''
            @name 批量目录保护
            @author zhwen<2020-11-17>
            @param site_id 1
            @param names test,baohu
        '''
        names = get.names.split(',')
        del_successfully = []
        del_failed = {}
        for name in names:
            get.name = name
            get.id = get.site_id
            try:
                get.multiple = 1
                result = self.delete_dir_auth(get)
                if not result['status']:
                    del_failed[name] = result['msg']
                    continue
                del_successfully.append(name)
            except:
                del_failed[name] = '删除时错误了，请再试一次'
        public.serviceReload()
        return {'status': True, 'msg': '删除目录保护 [ {} ] 成功'.format(','.join(del_successfully)), 'error': del_failed,
                'success': del_successfully}

    # 删除目录保护
    def delete_dir_auth(self, get):
        sd = site_dir_auth.SiteDirAuth()
        return sd.delete_dir_auth(get)

    # 获取目录保护列表
    def get_dir_auth(self, get):
        sd = site_dir_auth.SiteDirAuth()
        return sd.get_dir_auth(get)

    # 修改目录保护密码
    def modify_dir_auth_pass(self, get):
        sd = site_dir_auth.SiteDirAuth()
        return sd.modify_dir_auth_pass(get)

    def _check_path_total(self, path, limit):
        """
        根据路径获取文件/目录大小
        @path 文件或者目录路径
        return int
        """

        if not os.path.exists(path): return 0;
        if not os.path.isdir(path): return os.path.getsize(path)
        size_total = 0
        for nf in os.walk(path):
            for f in nf[2]:
                filename = nf[0] + '/' + f
                if not os.path.exists(filename): continue;
                if os.path.islink(filename): continue;
                size_total += os.path.getsize(filename)
                if size_total >= limit: return limit
        return size_total

    def get_average_num(self, slist):
        """
        @获取平均值
        """
        count = len(slist)
        limit_size = 1 * 1024 * 1024
        if count <= 0: return limit_size
        print(slist)
        if len(slist) > 1:
            slist = sorted(slist)
            limit_size = int((slist[0] + slist[-1]) / 2 * 0.85)
        return limit_size

    def check_del_data(self, get):
        """
        @删除前置检测
        @ids = [1,2,3]
        """
        ids = json.loads(get['ids'])
        slist = {}
        result = []

        import database
        db_data = database.database().get_database_size(ids, True)
        limit_size = 50 * 1024 * 1024
        f_list_size = [];
        db_list_size = []
        for id in ids:
            data = public.M('sites').where("id=?", (id,)).field('id,name,path,addtime').find()
            if not data: continue

            addtime = public.to_date(times=data['addtime'])

            data['st_time'] = addtime
            data['limit'] = False
            data['backup_count'] = public.M('backup').where("pid=? AND type=?", (data['id'], '0')).count()
            f_size = self._check_path_total(data['path'], limit_size)
            data['total'] = f_size
            data['score'] = 0

            # 目录太小不计分
            if f_size > 0:
                f_list_size.append(f_size)

                # 10k 目录不参与排序
                if f_size > 10 * 1024: data['score'] = int(time.time() - addtime) + f_size

            if data['total'] >= limit_size: data['limit'] = True
            data['database'] = False
            find = public.M('databases').field('id,pid,name,ps,addtime').where('pid=?', (data['id'],)).find()
            if find:
                db_addtime = public.to_date(times=find['addtime'])

                data['database'] = db_data[find['name']]
                data['database']['st_time'] = db_addtime

                db_score = 0
                db_size = data['database']['total']

                if db_size > 0:
                    db_list_size.append(db_size)
                    if db_size > 50 * 1024: db_score += int(time.time() - db_addtime) + db_size

                data['score'] += db_score
            result.append(data)

        slist['data'] = sorted(result, key=lambda x: x['score'], reverse=True)
        slist['file_size'] = self.get_average_num(f_list_size)
        slist['db_size'] = self.get_average_num(db_list_size)
        return slist

    def get_https_mode(self, get=None):
        '''
            @name 获取https模式
            @author hwliang<2022-01-14>
            @return bool False.宽松模式 True.严格模式
        '''
        web_server = public.get_webserver()
        if web_server not in ['nginx', 'apache']:
            return False

        if web_server == 'nginx':
            default_conf_file = "{}/nginx/0.default.conf".format(public.get_vhost_path())
        else:
            default_conf_file = "{}/apache/0.default.conf".format(public.get_vhost_path())

        if not os.path.exists(default_conf_file): return False
        default_conf = public.readFile(default_conf_file)
        if not default_conf: return False

        if default_conf.find('DEFAULT SSL CONFI') != -1: return True
        return False

    def get_https_settings(self, get):
        http2https_pl = "{}/data/http2https.pl".format(public.get_panel_path())
        return json_response(status=True, msg="ok", data={
            "https_mode": self.get_https_mode(),
            "http2https": os.path.exists(http2https_pl),
        })

    @staticmethod
    def set_global_http2https(get):
        status = get.get("status/d", 0)
        http2https_pl = "{}/data/http2https.pl".format(public.get_panel_path())
        if status:
            public.writeFile(http2https_pl, "", "w")
        else:
            if os.path.exists(http2https_pl):
                os.remove(http2https_pl)
        return json_response(status=True, msg="设置成功")

    def write_ngx_default_conf_by_ssl(self):
        '''
            @name 写nginx默认配置文件（含SSL配置）
            @author hwliang<2022-01-14>
            @return bool
        '''
        http2 = ''
        versionStr = public.readFile('/www/server/nginx/version.pl')
        if versionStr:
            if versionStr.find('1.8.1') == -1:
                http2 = ' http2'
        default_conf_body = '''server
{{
    listen 80;
    listen 443 ssl{http2};
    server_name _;
    index index.html;
    root /www/server/nginx/html;

    # DEFAULT SSL CONFIG
    ssl_certificate    /www/server/panel/vhost/cert/0.default/fullchain.pem;
    ssl_certificate_key    /www/server/panel/vhost/cert/0.default/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    add_header Strict-Transport-Security "max-age=31536000";
}}'''.format(http2=http2)
        ngx_default_conf_file = "{}/nginx/0.default.conf".format(public.get_vhost_path())
        self.create_default_cert()
        return public.writeFile(ngx_default_conf_file, default_conf_body)

    def write_ngx_default_conf(self):
        '''
            @name 写nginx默认配置文件
            @author hwliang<2022-01-14>
            @return bool
        '''
        default_conf_body = '''server
{
    listen 80;
    server_name _;
    index index.html;
    root /www/server/nginx/html;
}'''
        ngx_default_conf_file = "{}/nginx/0.default.conf".format(public.get_vhost_path())
        return public.writeFile(ngx_default_conf_file, default_conf_body)

    def write_apa_default_conf_by_ssl(self):
        '''
            @name 写nginx默认配置文件（含SSL配置）
            @author hwliang<2022-01-14>
            @return bool
        '''
        default_conf_body = '''<VirtualHost *:80>
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
<VirtualHost *:443>
    ServerAdmin webmaster@example.com
    DocumentRoot "/www/server/apache/htdocs"
    ServerName ssl.default.com

    # DEFAULT SSL CONFIG
    SSLEngine On
    SSLCertificateFile /www/server/panel/vhost/cert/0.default/fullchain.pem
    SSLCertificateKeyFile /www/server/panel/vhost/cert/0.default/privkey.pem
    SSLCipherSuite EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5
    SSLProtocol All -SSLv2 -SSLv3 -TLSv1
    SSLHonorCipherOrder On

    <Directory "/www/server/apache/htdocs">
        SetOutputFilter DEFLATE
        Options FollowSymLinks
        AllowOverride All
        Order allow,deny
        Allow from all
        DirectoryIndex index.html
    </Directory>
</VirtualHost>'''
        apa_default_conf_file = "{}/apache/0.default.conf".format(public.get_vhost_path())
        self.create_default_cert()
        return public.writeFile(apa_default_conf_file, default_conf_body)

    def write_apa_default_conf(self):
        '''
            @name 写apache默认配置文件
            @author hwliang<2022-01-14>
            @return bool
        '''
        default_conf_body = '''<VirtualHost *:80>
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
</VirtualHost>'''
        apa_default_conf_file = "{}/apache/0.default.conf".format(public.get_vhost_path())
        return public.writeFile(apa_default_conf_file, default_conf_body)

    def set_https_mode(self, get=None):
        '''
            @name 设置https模式
            @author hwliang<2022-01-14>
            @return dict
        '''
        web_server = public.get_webserver()
        if web_server not in ['nginx', 'apache']:
            return public.returnMsg(False, '该功能只支持Nginx/Apache')

        ngx_default_conf_file = "{}/nginx/0.default.conf".format(public.get_vhost_path())
        apa_default_conf_file = "{}/apache/0.default.conf".format(public.get_vhost_path())
        ngx_default_conf = public.readFile(ngx_default_conf_file)
        apa_default_conf = public.readFile(apa_default_conf_file)
        status = False
        if ngx_default_conf:
            if ngx_default_conf.find('DEFAULT SSL CONFIG') != -1:
                status = False
                self.write_ngx_default_conf()
                self.write_apa_default_conf()
            else:
                status = True
                self.write_ngx_default_conf_by_ssl()
                self.write_apa_default_conf_by_ssl()
        else:
            status = True
            self.write_ngx_default_conf_by_ssl()
            self.write_apa_default_conf_by_ssl()

        public.serviceReload()
        status_msg = {True: '开启', False: '关闭'}
        msg = '已{}HTTPS严格模式'.format(status_msg[status])
        public.WriteLog('网站管理', msg)
        return public.returnMsg(True, msg)

    def create_default_cert(self):
        '''
            @name 创建默认SSL证书
            @author hwliang<2022-01-14>
            @return bool
        '''
        cert_pem = '/www/server/panel/vhost/cert/0.default/fullchain.pem'
        cert_key = '/www/server/panel/vhost/cert/0.default/privkey.pem'
        if os.path.exists(cert_pem) and os.path.exists(cert_key): return True
        cert_path = os.path.dirname(cert_pem)
        if not os.path.exists(cert_path): os.makedirs(cert_path)
        import OpenSSL
        key = OpenSSL.crypto.PKey()
        key.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)
        cert = OpenSSL.crypto.X509()
        cert.set_serial_number(0)
        # cert.get_subject().CN = ''
        cert.set_issuer(cert.get_subject())
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(86400 * 3650)
        cert.set_pubkey(key)
        cert.sign(key, 'md5')
        cert_ca = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
        private_key = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key)
        if len(cert_ca) > 100 and len(private_key) > 100:
            public.writeFile(cert_pem, cert_ca, 'wb+')
            public.writeFile(cert_key, private_key, 'wb+')
            return True
        return False

    def get_upload_ssl_list(self, get):
        """
        @获取上传证书列表
        @siteName string 网站名称
        """
        siteName = get['siteName']
        path = '{}/vhost/upload_ssl/{}'.format(public.get_panel_path(), siteName)
        if not os.path.exists(path): os.makedirs(path)

        res = []
        for filename in os.listdir(path):
            try:
                filename = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(filename)))
                res.append(filename)
            except:
                pass
        return res

    # 获取指定证书基本信息
    def get_cert_init(self, cert_data, ssl_info=None):
        """
        @获取指定证书基本信息
        @cert_data string 证书数据
        @ssl_info dict 证书信息
        """
        try:
            result = {}
            if ssl_info and ssl_info['ssl_type'] == 'pfx':
                x509 = self.__check_pfx_pwd(cert_data, ssl_info['pwd'])[0]
            else:
                # x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert_data)
                if "/www/server/panel/class" not in sys.path:
                    sys.path.insert(0, "/www/server/panel/class")
                import ssl_info
                return ssl_info.ssl_info().load_ssl_info_by_data(cert_data)

            # 取产品名称
            issuer = x509.get_issuer()
            result['issuer'] = ''
            if hasattr(issuer, 'CN'):
                result['issuer'] = issuer.CN
            if not result['issuer']:
                is_key = [b'0', '0']
                issue_comp = issuer.get_components()
                if len(issue_comp) == 1:
                    is_key = [b'CN', 'CN']
                for iss in issue_comp:
                    if iss[0] in is_key:
                        result['issuer'] = iss[1].decode()
                        break
            # 取到期时间
            result['notAfter'] = self.strf_date(
                bytes.decode(x509.get_notAfter())[:-1])
            # 取申请时间
            result['notBefore'] = self.strf_date(
                bytes.decode(x509.get_notBefore())[:-1])
            # 取可选名称
            result['dns'] = []
            for i in range(x509.get_extension_count()):
                s_name = x509.get_extension(i)
                if s_name.get_short_name() in [b'subjectAltName', 'subjectAltName']:
                    s_dns = str(s_name).split(',')
                    for d in s_dns:
                        result['dns'].append(d.split(':')[1])
            subject = x509.get_subject().get_components()

            # 取主要认证名称
            if len(subject) == 1:
                result['subject'] = subject[0][1].decode()
            else:
                if len(result['dns']) > 0:
                    result['subject'] = result['dns'][0]
                else:
                    result['subject'] = '';
            return result
        except:
            return False

    def strf_date(self, sdate):
        """
        @转换证书时间
        """
        return time.strftime('%Y-%m-%d', time.strptime(sdate, '%Y%m%d%H%M%S'))

    def check_ssl_endtime(self, data, ssl_info=None):
        """
        @检查证书是否有效(证书最高有效期不超过1年)
        @data string 证书数据
        @ssl_info dict 证书信息
        """
        info = self.get_cert_init(data, ssl_info)
        if info:
            end_time = time.mktime(time.strptime(info['notAfter'], "%Y-%m-%d"))
            start_time = time.mktime(time.strptime(info['notBefore'], "%Y-%m-%d"))

            days = int((end_time - start_time) / 86400)
            if days < 400:  # 1年有效期+1个月续签时间
                return data
        return False

    # 证书转为pkcs12
    def dump_pkcs12(self, key_pem=None, cert_pem=None, ca_pem=None, friendly_name=None):
        """
        @证书转为pkcs12
        @key_pem string 私钥数据
        @cert_pem string 证书数据
        @ca_pem string 可选的CA证书数据
        @friendly_name string 可选的证书名称
        """
        try:
            import OpenSSL
            p12 = OpenSSL.crypto.PKCS12()
            if cert_pem:
                x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert_pem.encode())
                p12.set_certificate(x509)
            if key_pem:
                p12.set_privatekey(OpenSSL.crypto.load_privatekey(
                    OpenSSL.crypto.FILETYPE_PEM, key_pem.encode()))
            if ca_pem:
                p12.set_ca_certificates((OpenSSL.crypto.load_certificate(
                    OpenSSL.crypto.FILETYPE_PEM, ca_pem.encode()),))
            if friendly_name:
                p12.set_friendlyname(friendly_name.encode())
            return p12.export()
        except:
            return None

    def download_cert(self, get):
        """
        @下载证书
        @get dict 请求参数
            siteName string 网站名称
            ssl_type string 证书类型
            key string 密钥
            pem string 证书数据
            pwd string 证书密码
        """
        pem = get['pem']
        siteName = get['siteName']
        ssl_type = get['ssl_type']

        rpath = '{}/temp/ssl/'.format(public.get_panel_path())
        if os.path.exists(rpath): shutil.rmtree(rpath)

        ca_list = []
        path = '{}/{}_{}'.format(rpath, siteName, int(time.time()))
        if ssl_type == 'pfx':
            import OpenSSL
            res = self.__check_pfx_pwd(base64.b64decode(pem), get['pwd'])
            p12 = res[1]
            x509 = res[0]
            get['pwd'] = res[2]
            print(get['pwd'])
            ca_list = []
            for x in p12.get_ca_certificates():
                ca_list.insert(0, OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, x).decode().strip())
            ca_cert = '\n'.join(ca_list)
            key = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, p12.get_privatekey()).decode().strip()
            domain_cert = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, x509).decode().strip()
        else:
            key = get['key']
            domain_cert = pem.split('-----END CERTIFICATE-----')[0] + "-----END CERTIFICATE-----\n"
            ca_cert = pem.replace(domain_cert, '')

            p12 = self.dump_pkcs12(key, '{}\n{}'.format(domain_cert.strip(), ca_cert), ca_cert)
            if p12 is None:
                import ssl_info
                p12 = ssl_info.ssl_info().dump_pkcs12_new(key, '{}\n{}'.format(domain_cert.strip(), ca_cert), ca_cert)

        for x in ['IIS', 'Apache', 'Nginx', '其他证书']:
            d_file = '{}/{}'.format(path, x)
            if not os.path.exists(d_file): os.makedirs(d_file)

            if x == 'IIS' and p12 is not None:
                public.writeFile2(d_file + '/fullchain.pfx', p12, 'wb+')
                public.writeFile(d_file + '/password.txt', get['pwd'])
            elif x == 'Apache':
                public.writeFile(d_file + '/privkey.key', key)
                public.writeFile(d_file + '/root_bundle.crt', ca_cert)
                public.writeFile(d_file + '/domain.crt', domain_cert)
            else:
                public.writeFile(d_file + '/privkey.key', key)
                public.writeFile(d_file + '/fullchain.pem', '{}\n{}'.format(domain_cert.strip(), ca_cert))

        flist = []
        public.get_file_list(path, flist)

        zfile = '{}/{}.zip'.format(rpath, os.path.basename(path))
        import zipfile
        f = zipfile.ZipFile(zfile, 'w', zipfile.ZIP_DEFLATED)
        for item in flist:
            s_path = item.replace(path, '')
            if s_path: f.write(item, s_path)
        f.close()

        return public.returnMsg(True, zfile);

    def check_ssl_info(self, get):
        """
        @解析证书信息
        @get dict 请求参数
            path string 上传文件路径
        """
        path = get['path']
        if not os.path.exists(path):
            return public.returnMsg(False, '查询失败，不存在的地址')

        info = {'root': '', 'cert': '', 'pem': '', 'key': ''}
        ssl_info = {'pwd': None, 'ssl_type': None}
        for filename in os.listdir(path):
            filepath = '{}/{}'.format(path, filename)
            ext = filename[-4:]
            if ext == '.pfx':
                ssl_info['ssl_type'] = 'pfx'

                f = open(filepath, 'rb')  # pfx为二进制文件
                info['pem'] = f.read()

            else:
                data = public.readFile(filepath)
                if filename.find('password') >= 0:  # 取pfx密码
                    ssl_info['pwd'] = re.search('([a-zA-Z0-9]+)', data).groups()[0]
                    continue

                if len(data) < 1024:
                    continue

                if data.find('PRIVATE KEY') >= 0:
                    info['key'] = data  # 取key

                if ext == '.pem':
                    if self.check_ssl_endtime(data):
                        info['pem'] = data
                else:
                    if data.find('BEGIN CERTIFICATE') >= 0:
                        if not info['root']:
                            info['root'] = data
                        else:
                            info['cert'] = data

        if ssl_info['ssl_type'] == 'pfx':
            info['pem'] = self.check_ssl_endtime(info['pem'], ssl_info)
            if info['pem']:
                info['pem'] = base64.b64encode(info['pem'])
                info['key'] = True
        else:
            if not info['pem']:
                # 确认ca证书和域名证书顺序
                info['pem'] = self.check_ssl_endtime(info['root'] + "\n" + info['cert'], ssl_info)
                if not info['pem']:
                    info['pem'] = self.check_ssl_endtime(info['cert'] + "\n" + info['root'], ssl_info)

        if info['key'] and info['pem']:
            return {'key': info['key'], 'pem': info['pem'], 'ssl_type': ssl_info['ssl_type'], 'pwd': ssl_info['pwd']}
        return False

    def __check_pfx_pwd(self, data, pwd):
        """
        @检测pfx证书密码
        @data string pfx证书内容
        @pwd string 密码
        """
        import OpenSSL
        try:
            p12 = OpenSSL.crypto.load_pkcs12(data, pwd)
            x509 = p12.get_certificate()
        except:
            pwd = re.search('([a-zA-Z0-9]+)', pwd).groups()[0]
            p12 = OpenSSL.crypto.load_pkcs12(data, pwd)
            x509 = p12.get_certificate()
        return [x509, p12, pwd]

    def _ckeck_add_domain(self, site_name, domains):
        ssl_data = self.GetSSL(type("get", tuple(), {"siteName": site_name})())
        if not ssl_data["status"] or not ssl_data.get("cert_data", {}).get("dns", None):
            return {"domains": domains}
        domain_rep = []
        for i in ssl_data["cert_data"]["dns"]:
            if i.startswith("*"):
                _rep = "^[^\.]+\." + i[2:].replace(".", "\.")
            else:
                _rep = "^" + i.replace(".", "\.")
            domain_rep.append(_rep)
        no_ssl = []
        for domain in domains:
            if not domain["status"]: continue
            for _rep in domain_rep:
                if re.search(_rep, domain["name"]):
                    break
            else:
                no_ssl.append(domain["name"])
        if no_ssl:
            return {
                "domains": domains,
                "not_ssl": no_ssl,
                "tip": "本站点已启用SSL证书,但本次添加的域名：{}，无法匹配当前证书，如有需求，请重新申请证书。".format(str(no_ssl))
            }
        return {"domains": domains}

    # —————————————————————
    #     批量伪静态      |
    # —————————————————————
    def GetRewriteLists(self, get):
        """批量获取伪静态地址
        @author baozi <202-04-18>
        @param:
            get  ( dict ):
        @return   :  请求参数
        """
        try:
            site_ids = json.loads(getattr(get, "site_ids", "[]"))
            site_type = getattr(get, "site_type", None)
            if not isinstance(site_type, str) and not isinstance(site_ids, list) and site_ids:
                return {"status": False, "msg": "参数错误！"}
        except:
            return {"status": False, "msg": "参数错误！"}
        ws = public.get_webserver()
        if ws == "openlitespeed":
            ws = "apache"
        rewrites = {"err_site": [], 'site_rewrites': [], "template_rewrites": []}
        for _id in site_ids:
            site = public.M('sites').where("id=?", (_id,)).field("id,name,path,project_config").find()
            if not site:
                rewrites["err_site"].append({"id": _id, "msg": "未查询到站点信息"})
                continue
            # 目前只支持PHP站点，后期添加其他站点时，可以再此处添加判断：
            #
            #
            if ws == "nginx":
                rewrite_file = public.get_panel_path() + '/vhost/rewrite/' + site["name"] + '.conf'
                if not os.path.exists(rewrite_file):
                    if not os.path.exists(os.path.dirname(rewrite_file)):
                        os.makedirs(os.path.dirname(rewrite_file))
                    open(rewrite_file, 'w+').close()
                    # rewrites["err_site"].append({"id": _id, "name": site["name"], "msg":"站点伪静态文件丢失"})
                rewrites["site_rewrites"].append({"id": _id, "name": site["name"], "file": rewrite_file})
                continue
            _path = site["path"]
            if site_type.lower() == "java":
                site["project_config"] = json.loads(site["project_config"])
                if site['project_config']['java_type'] == 'springboot':
                    if site['project_config']['static_path']:
                        _path = site['project_config']['static_path']
                    else:
                        _path = site['project_config']['jar_path']
            if site_type.lower() in ("go", "other"):
                _path = _path.rsplit("/", 1)[0]
            runPath = self.GetSiteRunPath(type("get", (object,), {"id": site["id"]})())
            if runPath['runPath'].find('/www/server/stop') != -1:
                runPath['runPath'] = runPath['runPath'].replace('/www/server/stop', '')

            rewrite_file = _path + runPath['runPath'] + ".htaccess"
            rewrite_file = rewrite_file.replace("//", "/")
            if not os.path.exists(rewrite_file):
                open(rewrite_file, 'w+').close()
                # rewrites["err_site"].append({"id": _id, "name": site["name"], "msg":"站点伪静态文件丢失"})
            rewrites["site_rewrites"].append({"id": _id, "name": site["name"], "file": rewrite_file})

        for ds in sorted(os.listdir('rewrite/' + ws)):
            # public.print_log(ds)
            if ds == 'list.txt': continue
            if '0.当前' in ds: continue
            _file = "{}/rewrite/{}/{}".format(public.get_panel_path(), ws, ds)
            rewrites['template_rewrites'].append({"name": ds[0:len(ds) - 5], "file": _file})

        return rewrites

    def SetRewriteLists(self, get):
        """批量设置伪静态文件
        @author baozi <202-04-18>
        @param:
            get  ( dict ): 请求参数
        @return   :
        """
        from typing import Dict, List
        from files import files
        try:
            sites: List[Dict] = json.loads(getattr(get, "sites", "[]"))
            rewrite_data = getattr(get, "rewrite_data", "")
            if not isinstance(rewrite_data, str) and not isinstance(sites, list) and sites:
                return {"status": False, "msg": "参数错误！"}
        except:
            return {"status": False, "msg": "参数错误！"}
        if rewrite_data == 'undefined':
            return public.returnMsg(False, '错误的文件内容,请重新保存!')

        res_list = []
        webserver = public.get_webserver()
        for site in sites:
            _site = public.M('sites').where("id=?", (site["id"],)).field("id,name,path,project_config").find()
            site["status"] = False
            if not _site:
                site["msg"] = "未查询到站点信息"
                res_list.append(site)
                continue
            path = site["file"]
            if not os.path.exists(path):
                site["msg"] = "站点伪静态文件丢失"
                res_list.append(site)
                continue
            if path.find('/rewrite/null/') != -1:
                path = path.replace("/rewrite/null/", "/rewrite/{}/".format(webserver))
            if path.find('/vhost/null/') != -1:
                path = path.replace("/vhost/null/", "/vhost/{}/".format(webserver))

            try:
                public.ExecShell('\\cp -a ' + path + ' /tmp/backup.conf')

                try:
                    rewrite_data = rewrite_data.encode('utf-8', errors='ignore').decode("utf-8")
                    fp = open(path, 'w+', encoding='utf-8')
                except:
                    fp = open(path, 'w+')
                rewrite_data = files().crlf_to_lf(rewrite_data, path)
                fp.write(rewrite_data)
                fp.close()

                isError = public.checkWebConfig()
                if isError != True:
                    public.ExecShell('\\cp -a /tmp/backup.conf ' + path)
                    site["msg"] = 'ERROR:<br><font style="color:red;">' + isError.replace("\n", '<br>') + '</font>'
                    res_list.append(site)
                    continue
                public.WriteLog('TYPE_FILE', 'FILE_SAVE_SUCCESS', (path,))
                site["status"] = True
                site["msg"] = "修改成功"
                res_list.append(site)
            except Exception as ex:
                site["status"] = False
                site["msg"] = "ERROR:<br>" + str(ex).replace("\n", '<br>')
                res_list.append(site)

        public.serviceReload()

        return res_list

    @staticmethod
    def check_webserver(use2render=False):
        setup_path = public.GetConfigValue('setup_path')
        ng_path = setup_path + '/nginx/sbin/nginx'
        ap_path = setup_path + '/apache/bin/apachectl'
        op_path = '/usr/local/lsws/bin/lswsctrl'
        not_server = False
        if not os.path.exists(ng_path) and not os.path.exists(ap_path) and not os.path.exists(op_path):
            not_server = True
        if not not_server:
            return
        tasks = public.M('tasks').where("status!=? AND type!=?", ('1', 'download')).field('id,name').select()
        for task in tasks:
            name = task["name"].lower()
            if name.find("openlitespeed") != -1:
                return "正在安装OpenLiteSpeed服务，请等待安装完成后再操作"
            if name.find("nginx") != -1:
                return "正在安装Nginx服务，请等待安装完成后再操作"
            if name.lower().find("apache") != -1:
                return "正在安装Apache服务，请等待安装完成后再操作"
        if use2render:
            return None

        return "未安装任意Web服务，请安装Nginx或Apache后再操作"

    @staticmethod
    def webserverprep(get=None):
        tasks = public.M('tasks').where("status!=? AND type!=?", ('1', 'download')).field('id,name').select()
        for task in tasks:
            name = task["name"].lower()
            if name.find("openlitespeed") != -1:
                return public.returnMsg(False, "正在安装OpenLiteSpeed服务")
            if name.find("nginx") != -1:
                return public.returnMsg(False, "正在安装Nginx服务")
            if name.lower().find("apache") != -1:
                return public.returnMsg(False, "正在安装Apache服务")

        return public.returnMsg(True, "")

    @staticmethod
    def check_total_install_info(get):
        """
        获取监控报表安装信息
        @param get:
        @return:
        """
        return_dict = {"total_status": True, "nginx_status": True, "buy_status": True}
        try:
            total_version = json.loads(public.ReadFile('/www/server/panel/plugin/total/info.json'))['versions']
        except:
            total_version = '0.0.0'
        total_version = float(str(total_version)[0:3])
        if total_version < 7.6:
            return_dict["total_status"] = False

        try:
            nginx_version = float(public.readFile("/www/server/nginx/version.pl")[0:4])
        except:
            nginx_version = 0

        if nginx_version < 1.18:
            return_dict["nginx_status"] = False

        try:
            import PluginLoader
            data = PluginLoader.plugin_run('total', 'index', get)
            if isinstance(data, dict):
                if 'status' in data and data['status'] == False and 'msg' in data:
                    return_dict["buy_status"] = False
                    if isinstance(data['msg'], str):
                        if data['msg'].find('加载失败') != -1 or data['msg'].find('Traceback ') == 0:
                            raise public.PanelError(data['msg'])
            else:
                return_dict["buy_status"] = False
        except Exception as ex:
            if str(ex).find('未购买') != -1:
                return_dict["buy_status"] = False

        return return_dict

    # 网站 --》 php项目 --》 流量限制 --》 流量限额
    @staticmethod
    def create_flow_rule(get):
        """
        @name: 创建流量限制规则
        @return:
        """
        import PluginLoader
        get.model_index = 'panel'

        return PluginLoader.module_run("total", "create_flow_rule", get)

    @staticmethod
    def get_generated_flow_info(get):
        """
        @name: 显示流量信息
        @return:
        """
        import PluginLoader
        get.model_index = 'panel'

        return PluginLoader.module_run("total", "get_generated_flow_info", get)

    @staticmethod
    def get_limit_config(get):
        """
        @name: 获取流量限制配置
        @return:
        """
        import PluginLoader
        get.model_index = 'panel'

        return PluginLoader.module_run("total", "get_limit_config", get)

    @staticmethod
    def remove_flow_rule(get):
        """
        @name: 删除流量限制配置
        @return:
        """
        import PluginLoader
        get.model_index = 'panel'

        return PluginLoader.module_run("total", "remove_flow_rule", get)

    @staticmethod
    def modify_flow_rule(get):
        """
        @name: 修改流量限制配置
        @return:
        """
        import PluginLoader
        get.model_index = 'panel'

        return PluginLoader.module_run("total", "modify_flow_rule", get)

    @staticmethod
    def set_limit_status(get):
        """
        @name: 修改流量限制配置
        @return:
        """
        import PluginLoader
        get.model_index = 'panel'

        return PluginLoader.module_run("total", "set_limit_status", get)

    # —————————————————————
    #     协议版本选择    |
    # —————————————————————
    @staticmethod
    def set_ssl_protocol(get):
        """ 设置全局TLS版本
        @author baozi <202-04-18>
        @param:
        @return
        """
        protocols = {
            "TLSv1": False,
            "TLSv1.1": False,
            "TLSv1.2": False,
            "TLSv1.3": False,
        }
        if "use_protocols" in get:
            use_protocols = getattr(get, "use_protocols", [])
            if isinstance(use_protocols, list):
                for protocol in use_protocols:
                    if protocol in protocols:
                        protocols[protocol] = True
            elif isinstance(use_protocols, str):
                for protocol in use_protocols.split(","):
                    if protocol in protocols:
                        protocols[protocol] = True
            else:
                protocols["TLSv1.1"] = True
                protocols["TLSv1.2"] = True
                protocols["TLSv1.3"] = True

        else:
            protocols["TLSv1.1"] = True
            protocols["TLSv1.2"] = True
            protocols["TLSv1.3"] = True

        # public.print_log(protocols)
        public.WriteFile(public.get_panel_path() + "/data/ssl_protocol.json", json.dumps(protocols))
        return public.returnMsg(True, 'SET_SUCCESS')

    @staticmethod
    def get_tls_protocol(tls1_3: str = "TLSv1.3", is_apache=False):
        """获取使用的协议
        @author baozi <202-04-18>
        @param:
        @return
        """
        protocols = {
            "TLSv1": False,
            "TLSv1.1": True,
            "TLSv1.2": True,
            "TLSv1.3": True,
        }
        file_path = public.get_panel_path() + "/data/ssl_protocol.json"
        if os.path.exists(file_path):
            data = public.readFile(file_path)
            if data is not False:
                protocols = json.loads(data)
                if protocols["TLSv1.3"] and tls1_3 == "":
                    protocols["TLSv1.3"] = False
                if is_apache is False:
                    return " ".join([p for p, v in protocols.items() if v is True])
                else:
                    return " ".join(["-" + p for p, v in protocols.items() if v is False])
        else:
            if tls1_3 != "":
                protocols["TLSv1.3"] = True
            if is_apache is False:
                return " ".join([p for p, v in protocols.items() if v is True])
            else:
                return " ".join(["-" + p for p, v in protocols.items() if v is False])

    @staticmethod
    def get_ssl_protocol(get):
        """ 获取全局TLS版本
        @author baozi <202-04-18>
        @param:
        @return
        """
        protocols = {
            "TLSv1": False,
            "TLSv1.1": True,
            "TLSv1.2": True,
            "TLSv1.3": True,
        }
        file_path = public.get_panel_path() + "/data/ssl_protocol.json"
        if os.path.exists(file_path):
            data = public.readFile(file_path)
            if data is not False:
                protocols = json.loads(data)
                return protocols

        return protocols

    @staticmethod
    def get_sites_ftp(get):
        """快速获取网站ftp"""
        siteName = getattr(get, "siteName", None)
        site_id = getattr(get, "site_id", None)
        if siteName is None and site_id is None:
            return public.returnMsg(False, "参数错误")

        site_sql = public.M("sites")
        if site_id is not None:
            site_sql = site_sql.where("id = ? and project_type in ('PHP','WP2')", (site_id))
        elif siteName is not None:
            site_sql = site_sql.where("name = ? and project_type  in ('PHP','WP2')", (siteName.strip()))
        res = site_sql.find()
        if isinstance(res, str) and res.startswith("error"):
            return public.returnMsg(False, "数据库损坏")

        if not res:
            return public.returnMsg(False, "没有该网站")

        ftps = public.M("ftps").where("pid = ? or path = ?", (res["id"],res['path'])).find()
        if isinstance(ftps, str) and ftps.startswith("error"):
            return public.returnMsg(False, "数据库损坏")

        if not ftps:
            return {
                "status": True,
                "msg": "没有对应站点的ftp信息",
                "info": None,
            }
        return {
            "status": True,
            "info": ftps
        }

    @staticmethod
    def set_sites_ftp(get):
        """快速设置网站ftp"""
        siteName = getattr(get, "siteName", None)
        site_id = getattr(get, "site_id", None)
        if siteName is None and site_id is None:
            return public.returnMsg(False, "参数错误")

        ftp_id = getattr(get, "ftp_id", None)
        ftp_status = getattr(get, "ftp_status", None)
        ftp_name = getattr(get, "ftp_name", None)
        ftp_pwd = getattr(get, "ftp_pwd", None)
        if ftp_name is None or ftp_pwd is None:
            return public.returnMsg(False, "参数错误")

        site_sql = public.M("sites")
        if site_id is not None:
            site_sql = site_sql.where("id = ? and project_type in ('PHP','WP2')", (int(site_id)))
        elif siteName is not None:
            site_sql = site_sql.where("name = ? and project_type in ('PHP','WP2')", (siteName.strip()))
        res = site_sql.find()
        if isinstance(res, str) and res.startswith("error"):
            return public.returnMsg(False, "数据库损坏")

        if not res:
            return public.returnMsg(False, "没有该网站")

        def warp_result(ftp_res, site_ftp_id=None, site_ftp_name=None, site_ftp_pwd=None):
            if ftp_res["status"] is False:
                return ftp_res
            if site_ftp_id is not None:
                ftp_info = public.M("ftps").where("id = ? ", (site_ftp_id,)).find()
                ftp_res["info"] = ftp_info
                return ftp_res
            if site_ftp_name is not None and site_ftp_pwd is not None:
                ftp_info = public.M("ftps").where("name = ? ", (site_ftp_name,)).find()
                ftp_res["info"] = ftp_info
                return ftp_res
            return ftp_res

        ftp_get_obj = public.dict_obj()
        # ftp 创建
        import ftp
        if ftp_id is None or ftp_id in [0, "0"]:
            ftp_get_obj.ftp_username = ftp_name
            ftp_get_obj.ftp_password = ftp_pwd
            ftp_get_obj.path = res["path"]
            ftp_get_obj.pid = res["id"]
            ftp_get_obj.ps = res["name"]
            result = ftp.ftp().AddUser(ftp_get_obj)
            return warp_result(result, site_ftp_name=ftp_name, site_ftp_pwd=ftp_pwd)

        if ftp_status is not None:
            # ftp_get_obj.id = ftp_id
            # ftp_get_obj.status = "0" if ftp_status in ("0", 0, "false", False) else "1"
            # ftp_get_obj.username = ftp_name
            # result = ftp.ftp().SetStatus(ftp_get_obj)
            # return warp_result(result, site_ftp_id=ftp_id)
            del_get_obj = public.dict_obj()
            del_get_obj.id = ftp_id
            del_get_obj.username = ftp_name
            result = ftp.ftp().DeleteUser(del_get_obj)
            return result

        old_ftp_info = public.M("ftps").where("id = ? ", (ftp_id,)).find()
        if not old_ftp_info or isinstance(old_ftp_info, str):
            return public.returnMsg(False, "修改错误")

        if old_ftp_info["name"] == ftp_name:  # ftp用户名不变就只修改密码
            ftp_get_obj.ftp_username = ftp_name
            ftp_get_obj.new_password = ftp_pwd
            ftp_get_obj.id = ftp_id

            result = ftp.ftp().SetUserPassword(ftp_get_obj)
            return warp_result(result, site_ftp_id=ftp_id)
        else:  # ftp用户名变了就删除重建
            ftp_get_obj.ftp_username = ftp_name
            ftp_get_obj.ftp_password = ftp_pwd
            ftp_get_obj.path = res["path"]
            ftp_get_obj.pid = res["id"]
            ftp_get_obj.ps = res["name"]
            result = ftp.ftp().AddUser(ftp_get_obj)
            if result["status"] is False:
                return public.returnMsg(False, result["msg"])

            # 删除旧的ftp
            del_get_obj = public.dict_obj()
            del_get_obj.id = old_ftp_info["id"]
            del_get_obj.username = old_ftp_info["name"]
            ftp.ftp().DeleteUser(del_get_obj)
            return warp_result(result, site_ftp_name=ftp_name, site_ftp_pwd=ftp_pwd)

    @staticmethod
    def site_crontab_log(site_name):
        if public.M("crontab").where("sName =? and sType = ?", ("ALL", "logs")).find():
            return True

        import crontab
        crontabs = crontab.crontab()
        args = {
            "name": "切割日志[{}]".format(site_name),
            "type": 'day',
            "where1": '',
            "hour": 0,
            "minute": 1,
            "sName": site_name,
            "sType": 'logs',
            "notice": '',
            "notice_channel": '',
            "save": 180,
            "save_local": '1',
            "backupTo": '',
            "sBody": '',
            "urladdress": ''
        }
        res = crontabs.AddCrontab(args)
        if res and "id" in res.keys():
            return True
        return False

    def create_default_conf(self, get=None):
        status = {
            "page_404": True,
            "page_index": True,
            "log_split": False,
        }
        tip_file_path = public.get_panel_path() + "/data/php_create_default_conf.json"
        if os.path.exists(tip_file_path):
            data = public.readFile(tip_file_path)
            if data is not False:
                try:
                    status = json.loads(data)
                except:
                    pass

        cdn_ip_conf_file = "{}/vhost/nginx/real_cdn_ip.conf".format(public.get_panel_path())
        if not os.path.exists(cdn_ip_conf_file):
            cdn_ip = False
            status['cdn_recursive'] = False
            nginx_path = public.GetConfigValue('setup_path') + '/nginx/conf/nginx.conf'
            config = public.readFile(nginx_path)
            if config:
                if 'real_ip_header' in config and 'set_real_ip_from' in config:
                    cdn_ip = True
            if public.get_webserver() == 'nginx':
                status['cdn_ip'] = cdn_ip
        else:
            cdn_ip_conf = public.readFile(cdn_ip_conf_file)
            if cdn_ip_conf:
                status['cdn_ip'] = True
                status['cdn_recursive'] = True if 'real_ip_recursive' in cdn_ip_conf else False
            else:
                status['cdn_ip'] = False
                status['cdn_recursive'] = False
        status['log_path'] = self.get_sites_log_path()
        return status

    # def open_cdn_ip(self, get):
    #     public.print_log(get.__dict__)
    #     if not hasattr(get,'cdn_ip'):
    #         return public.returnMsg(False, '参数错误')
    #     if get.cdn_ip in ['true', True]:
    #         nginx_path = public.GetConfigValue('setup_path') + '/nginx/conf/nginx.conf'
    #         config = public.readFile(nginx_path)
    #         if not config:
    #             return public.returnMsg(False, '未找到配置文件')
    #         con = "     real_ip_header X-Forwarded-For;\n     set_real_ip_from 0.0.0.0/0;"
    #         if 'real_ip_header' in config and 'set_real_ip_from' in config:
    #             return public.returnMsg(False, '已开启CDN IP解析')
    #         tmplet = r'http\s*{'
    #         tmp = re.search(tmplet, config)
    #         if not tmp:
    #             return public.returnMsg(False, '未找到配置文件')
    #         now_config = config[:tmp.end()] + '\n' + con + '\n' + config[tmp.end():]
    #         public.writeFile(nginx_path, now_config)
    #         public.serviceReload()
    #         return public.returnMsg(True, '开启成功，请检查网站访问是否正常！')
    #     else:
    #         nginx_path = public.GetConfigValue('setup_path') + '/nginx/conf/nginx.conf'
    #         public.ExecShell("sed -i '/real_ip_header/d' " + nginx_path)
    #         public.ExecShell("sed -i '/set_real_ip_from/d' " + nginx_path)
    #         public.serviceReload()
    #         return public.returnMsg(True, '关闭成功')

    def open_cdn_ip(self, get):
        if public.get_webserver() != 'nginx':
            return public.returnMsg(False, '仅nginx服务器支持此功能')
        if public.checkWebConfig() is not True:
            return public.returnMsg(False, '仅nginx配置文件有误，请先修复后再试！')

        status = get.get("cdn_ip", False)
        recursive = get.get("cdn_recursive", False)
        white_ips = get.get("white_ips", "")
        white_ip_list = []
        if white_ips:
            import ipaddress
            for ip in white_ips.split(","):
                try:
                    ipaddress.ip_address(ip)
                    white_ip_list.append(ip)
                except:
                    try:
                        ipaddress.ip_network(ip)
                        white_ip_list.append(ip)
                    except:
                        continue
        white_ip_list = ["0.0.0.0/0", "::/0"] if not white_ip_list else white_ip_list
        header_cdn = get.get("header_cdn/s", "X-Forwarded-For").strip()
        if re.search(r"\s+", header_cdn):
            return public.returnMsg(False, "请求头不能含有空格")

        cdn_ip_conf_file = "{}/vhost/nginx/real_cdn_ip.conf".format(public.get_panel_path())
        if not os.path.isfile(cdn_ip_conf_file):
            public.writeFile(cdn_ip_conf_file, '')
            nginx_conf_file = public.GetConfigValue('setup_path') + '/nginx/conf/nginx.conf'
            config = public.readFile(nginx_conf_file)
            if not config:
                return public.returnMsg(False, '未找到配置文件')

            data_list = []
            for line in config.split('\n'):
                if 'real_ip_header' in line or 'set_real_ip_from' in line:
                    continue
                data_list.append(line)
            public.writeFile(nginx_conf_file, '\n'.join(data_list))
            if public.checkWebConfig() is not True:
                return public.returnMsg(False, '配置文件有误，请检查！')
            else:
                public.serviceReload()

        if status in ('true', True):
            real_ip_from = ""
            for white_ip in white_ip_list:
                real_ip_from += "set_real_ip_from {};\n".format(white_ip)
            public.WriteFile(cdn_ip_conf_file, """
{}real_ip_header {};{}
""".format(real_ip_from, header_cdn, "" if recursive not in ['true', True] else "\nreal_ip_recursive on;"))
            public.serviceReload()

        else:
            public.writeFile(cdn_ip_conf_file, '')
            public.serviceReload()

        return public.returnMsg(True, '设置成功')

    @staticmethod
    def set_create_default_conf(get):
        status = {
            "page_404": True,
            "page_index": True,
            "log_split": False,
        }
        tip_file_path = public.get_panel_path() + "/data/php_create_default_conf.json"
        page_404_status = getattr(get, "page_404", None)
        if page_404_status is not None:
            status["page_404"] = True if page_404_status in [True, "true", 1, "1"] else False

        page_index_status = getattr(get, "page_index", None)
        if page_index_status is not None:
            status["page_index"] = True if page_index_status in [True, "true", 1, "1"] else False

        log_split_status = getattr(get, "log_split", None)
        if log_split_status is not None:
            status["log_split"] = True if log_split_status in [True, "true", 1, "1"] else False

        public.writeFile(tip_file_path, json.dumps(status))
        return public.returnMsg(True, "修改成功")

    def site_rname(self, get):
        try:
            if not (hasattr(get, "id") and hasattr(get, "rname")):
                return public.returnMsg(False, "参数错误")
            id = get.id
            rname = get.rname
            data = public.M('sites').where("id=?", (id,)).select()
            if not data:
                return public.returnMsg(False, "站点不存在")
            data = data[0]
            name = data['rname'] if 'rname' in data.keys() and data.get('rname', '') else data['name']
            if 'rname' not in data.keys():
                public.M('sites').execute("ALTER TABLE 'sites' ADD 'rname' text DEFAULT ''", ())
            public.M('sites').where('id=?', data['id']).update({'rname': rname})
            return public.returnMsg(True, '网站【{}】改名为：【{}】'.format(name, rname))
        except:
            return public.returnMsg(False, traceback.format_exc())

    def get_Scan(self, get):
        try:
            import PluginLoader
            res = self.startScan(get)
            return res
        except:
            print(traceback.format_exc())
            pass
        return {}

    def startScan(self, get):
        '''
        @name 开始扫描
        @author lkq<2022-3-30>
        @param get
        '''
        self.__cachekey = public.Md5('vulnerability_scanning' + time.strftime('%Y-%m-%d'))
        self.__config_file = '/www/server/panel/config/vulnerability_scanning.json'
        result22 = []
        time_info = int(time.time())
        webInfo = self.getWebInfo(None)
        if type(webInfo) == str:
            cache.set("scaing_info", result22, 1600)
            cache.set("scaing_info_time", time_info, 1600)
            result = {"info": result22, "time": time_info, }
            return result
        config = self.get_config()
        for web in webInfo:
            for cms in config:
                data = cms
                if 'cms_name' in web:
                    if web['cms_name'] != cms['cms_name']:
                        if not web['cms_name'] in cms['cms_list']: continue
                if self.getCmsType(web, data):
                    if not 'cms' in web:
                        web['cms'] = []
                        web['cms'].append(cms)
                    else:
                        web['cms'].append(cms)
                else:
                    if not 'cms' in web:
                        web['cms'] = []
            if not 'is_vufix' in web:
                web['is_vufix'] = False
        for i in webInfo:
            if i['is_vufix']:
                result22.append(i)
        cache.set("scaing_info", result22, 1600)
        cache.set("scaing_info_time", time_info, 1600)
        result = {"info": [], "time": time_info}
        loophole_num = sum([len(i['cms']) for i in result22])
        result['loophole_num'] = loophole_num
        result['site_num'] = len(webInfo)
        return result

    def getWebInfo(self, get):
        '''
        @name 获取网站的信息
        @author lkq<2022-3-30>
        @param get
        '''
        return public.M('sites').where('project_type=?', ('PHP')).select()

    def get_config(self):
        '''
        @name 获取配置文件
        @author lkq<2022-3-23>
        @return
        '''
        result = [
            {"cms_list": [], "dangerous": "2", "cms_name": "迅睿CMS",
             "ps": "迅睿CMS 版本过低",
             "name": "迅睿CMS 版本过低",
             "determine": ["dayrui/My/Config/Version.php"],
             "version": {"type": "file", "file": "dayrui/My/Config/Version.php",
                         "regular": "version.+'(\d+.\d+.\d+)'", "regular_len": 0,
                         "vul_version": "3.2.0~4.5.4", "ver_type": "range"},
             "repair_file": {"type": "file",
                             "file": [{"file": "dayrui/My/Config/Version.php",
                                       "regular": ''' if (preg_match('/(php|jsp|asp|exe|sh|cmd|vb|vbs|phtml)/i', $value)) {'''}]},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "pbootcms",
             "ps": "pbootcms 3.0.0~3.0.4 存在多个高危漏洞CNVD-2020-48981,CNVD-2020-48677,CNVD-2020-48469,CNVD-2020-57593,CNVD-2020-56006,CNVD-2021-00794,CNVD-2021-30081,CNVD-2021-30113,CNVD-2021-32163",
             "name": "pbootcms 2.0.0~2.0.8 存在多个高危漏洞CNVD-2020-48981,CNVD-2020-48677,CNVD-2020-48469,CNVD-2020-57593,CNVD-2020-56006,CNVD-2021-00794,CNVD-2021-30081,CNVD-2021-30113,CNVD-2021-32163",
             "determine": ["apps/common/version.php", "core/basic/Config.php",
                           "apps/admin/view/default/js/mylayui.js",
                           "apps/api/controller/ContentController.php"],
             "version": {"type": "file", "file": "apps/common/version.php",
                         "regular": "app_version.+'(\d+.\d+.\d+)'", "regular_len": 0,
                         "vul_version": "3.0.0~3.0.4", "ver_type": "range"},
             "repair_file": {"type": "file",
                             "file": [{"file": "apps/admin/controller/system/ConfigController.php",
                                       "regular": ''' if (preg_match('/(php|jsp|asp|exe|sh|cmd|vb|vbs|phtml)/i', $value)) {'''}]},
             }
            , {"cms_list": [], "dangerous": "3", "cms_name": "pbootcms",
               "ps": "pbootcms 2.0.0~2.0.8 存在多个高危漏洞CNVD-2020-04104,CNVD-2020-13536,CNVD-2020-24744,CNVD-2020-32198,CNVD-2020-32180,CNVD-2020-32177,CNVD-2020-31495,CNVD-2019-43060",
               "name": "pbootcms 2.0.0~2.0.8 存在多个高危漏洞CNVD-2020-04104,CNVD-2020-13536,CNVD-2020-24744,CNVD-2020-32198,CNVD-2020-32180,CNVD-2020-32177,CNVD-2020-31495,CNVD-2019-43060",
               "determine": ["apps/common/version.php", "core/basic/Config.php",
                             "apps/admin/view/default/js/mylayui.js",
                             "apps/api/controller/ContentController.php"],
               "version": {"type": "file", "file": "apps/common/version.php",
                           "regular": "app_version.+'(\d+.\d+.\d+)'", "regular_len": 0,
                           "vul_version": "2.0.0~2.0.8", "ver_type": "range"},
               "repair_file": {"type": "file",
                               "file": [{"file": "apps/home/controller/ParserController.php",
                                         "regular": ''' if (preg_match('/(\$_GET\[)|(\$_POST\[)|(\$_REQUEST\[)|(\$_COOKIE\[)|(\$_SESSION\[)|(file_put_contents)|(file_get_contents)|(fwrite)|(phpinfo)|(base64)|(`)|(shell_exec)|(eval)|(assert)|(system)|(exec)|(passthru)|(print_r)|(urldecode)|(chr)|(include)|(request)|(__FILE__)|(__DIR__)|(copy)/i', $matches[1][$i]))'''}]},
               }
            ,
            {"cms_list": [], "dangerous": "3", "cms_name": "pbootcms",
             "ps": "pbootcms 1.3.0~1.3.8 存在多个高危漏洞CNVD-2018-26355,CNVD-2018-24253,CNVD-2018-26938,CNVD-2019-14855,CNVD-2019-27743,CNVD-2020-23841",
             "name": "pbootcms 1.3.0~1.3.8 存在多个高危漏洞CNVD-2018-26355,CNVD-2018-24253,CNVD-2018-26938,CNVD-2019-14855,CNVD-2019-27743,CNVD-2020-23841",
             "determine": ["apps/common/version.php", "core/basic/Config.php",
                           "apps/admin/view/default/js/mylayui.js",
                           "apps/api/controller/ContentController.php"],
             "version": {"type": "file", "file": "apps/common/version.php",
                         "regular": "app_version.+'(\d+.\d+.\d+)'", "regular_len": 0,
                         "vul_version": "1.3.0~1.3.8", "ver_type": "range"},
             "repair_file": {"type": "file",
                             "file": [{"file": "apps/admin/controller/system/ConfigController.php",
                                       "regular": '''$config = preg_replace('/(\'' . $key . '\'([\s]+)?=>([\s]+)?)[\w\'\"\s,]+,/', '${1}\'' . $value . '\',', $config);'''}]},
             }
            , {"cms_list": [], "dangerous": "3", "cms_name": "pbootcms",
               "ps": "pbootcms 1.2.0~1.2.2 存在多个高危漏洞CNVD-2018-21503,CNVD-2018-19945,CNVD-2018-22854,CNVD-2018-22142,CNVD-2018-26780,CNVD-2018-24845",
               "name": "pbootcms 1.0.1~1.2.2 存在多个高危漏洞CNVD-2018-21503,CNVD-2018-19945,CNVD-2018-22854,CNVD-2018-22142,CNVD-2018-26780,CNVD-2018-24845",
               "determine": ["apps/common/version.php", "core/basic/Config.php",
                             "apps/admin/view/default/js/mylayui.js",
                             "apps/api/controller/ContentController.php"],
               "version": {"type": "file", "file": "apps/common/version.php",
                           "regular": "app_version.+'(\d+.\d+.\d+)'", "regular_len": 0,
                           "vul_version": ["1.2.0", "1.2.1", "1.2.2"], "ver_type": "list"},
               "repair_file": {"type": "file",
                               "file": [{"file": "apps/admin/controller/system/DatabaseController.php",
                                         "regular": '''if ($value && ! preg_match('/(^|[\s]+)(drop|truncate|set)[\s]+/i', $value)) {'''}]},
               },
            {"cms_list": [], "dangerous": "3", "cms_name": "pbootcms",
             "ps": "pbootcms 1.1.9 存在SQL注入漏洞CNVD-2018-18069",
             "name": "pbootcms 1.1.9 存在SQL注入漏洞CNVD-2018-18069",
             "determine": ["apps/common/version.php", "core/basic/Config.php",
                           "apps/admin/view/default/js/mylayui.js",
                           "apps/api/controller/ContentController.php"],
             "version": {"type": "file", "file": "apps/common/version.php",
                         "regular": "app_version.+'(\d+.\d+.\d+)'", "regular_len": 0,
                         "vul_version": ["1.1.9"], "ver_type": "list"},
             "repair_file": {"type": "file",
                             "file": [{"file": "core/function/handle.php",
                                       "regular": '''if (Config::get('url_type') == 2 && strrpos($indexfile, 'index.php') !== false)'''}]},
             },
            {"cms_list": [], "dangerous": "4", "cms_name": "pbootcms",
             "ps": "pbootcms 1.1.6~1.1.8 存在前台代码执行漏洞、存在多个SQL注入漏洞 CNVD-2018-17412,CNVD-2018-17741,CNVD-2018-17747,CNVD-2018-17750,CNVD-2018-17751,CNVD-2018-17752,CNVD-2018-17753,CNVD-2018-17754",
             "name": "pbootcms 1.1.6~1.1.8  存在前台代码执行漏洞、存在多个SQL注入漏洞 CNVD-2018-17412,CNVD-2018-17741,CNVD-2018-17747,CNVD-2018-17750,CNVD-2018-17751,CNVD-2018-17752,CNVD-2018-17753,CNVD-2018-17754",
             "determine": ["apps/common/version.php", "core/basic/Config.php",
                           "apps/admin/view/default/js/mylayui.js",
                           "apps/api/controller/ContentController.php"],
             "version": {"type": "file", "file": "apps/common/version.php",
                         "regular": "app_version.+'(\d+.\d+.\d+)'", "regular_len": 0,
                         "vul_version": ["1.1.6", "1.1.7", "1.1.8"], "ver_type": "list"},
             "repair_file": {"type": "file",
                             "file": [{"file": "core/function/handle.php",
                                       "regular": '''if (is_array($string)) { // 数组处理
                foreach ($string as $key => $value) {
                    $string[$key] = decode_slashes($value);
                }'''}]},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "pbootcms",
             "ps": "pbootcms 1.1.4 存在SQL注入漏洞CNVD-2018-13335,CNVD-2018-13336",
             "name": "pbootcms 1.1.4 存在SQL注入漏洞CNVD-2018-13335,CNVD-2018-13336",
             "determine": ["apps/common/version.php", "core/basic/Config.php",
                           "apps/admin/view/default/js/mylayui.js",
                           "apps/api/controller/ContentController.php"],
             "version": {"type": "file", "file": "apps/common/version.php",
                         "regular": "app_version.+'(\d+.\d+.\d+)'", "regular_len": 0,
                         "vul_version": ["1.1.4"], "ver_type": "list"},
             "repair_file": {"type": "file",
                             "file": [{"file": "core/extend/ueditor/php/controller.php",
                                       "regular": '''if (! ini_get('session.auto_start') && ! isset($_SESSION)'''}]},
             }
            , {"cms_list": [], "dangerous": "3", "cms_name": "maccms10",
               "ps": "maccms10 <=2022.1000.3025 存在ssrf漏洞、存在XSS漏洞",
               "name": "maccms10 <=2022.1000.3025 存在ssrf漏洞、存在XSS漏洞",
               "determine": ["application/extra/version.php", "application/api/controller/Wechat.php",
                             "thinkphp/library/think/Route.php",
                             "application/admin/controller/Upload.php"],
               "version": {"type": "file", "file": "application/extra/version.php",
                           "regular": "code.+'(\d+.\d+.\d+)'", "regular_len": 0,
                           "vul_version": ["2022.1000.3025", "2022.1000.3005", "2022.1000.3024", "2022.1000.3020",
                                           "2022.1000.3023",
                                           "2022.1000.3002", "2022.1000.1099", "2021.1000.1081"], "ver_type": "list"},
               "repair_file": {"type": "file",
                               "file": [{"file": "application/common/model/Actor.php",
                                         "regular": '''$data[$filter_field] = mac_filter_xss($data[$filter_field]);'''}]},
               }
            ,
            {"cms_list": [], "dangerous": "3", "cms_name": "maccms10",
             "ps": "maccms10 <=2022.1000.3024 存在前台任意用户登陆、后台会话验证绕过、后台任意文件写入、任意文件删除漏洞",
             "name": "maccms10 <=2022.1000.3024 存在前台任意用户登陆、后台会话验证绕过、后台任意文件写入、任意文件删除漏洞",
             "determine": ["application/extra/version.php", "application/api/controller/Wechat.php",
                           "thinkphp/library/think/Route.php",
                           "application/admin/controller/Upload.php"],
             "version": {"type": "file", "file": "application/extra/version.php",
                         "regular": "code.+'(\d+.\d+.\d+)'", "regular_len": 0,
                         "vul_version": ["2022.1000.3005", "2022.1000.3024", "2022.1000.3020", "2022.1000.3023",
                                         "2022.1000.3002", "2022.1000.1099", "2021.1000.1081"], "ver_type": "list"},
             "repair_file": {"type": "file",
                             "file": [{"file": "application/common/model/Annex.php",
                                       "regular": '''if (stripos($v['annex_file'], '../') !== false)'''}]},
             }
            , {"cms_list": [], "dangerous": "3", "cms_name": "eyoucms",
               "ps": "eyoucms 1.5.5~1.5.7 存在多个安全漏洞",
               "name": "eyoucms 1.5.1~1.5.4 存在多个安全漏洞",
               "determine": ["data/conf/version.txt", "application/api/controller/Uploadify.php",
                             "application/extra/extra_cache_key.php",
                             "application/admin/controller/Uploadify.php"],
               "version": {"type": "file", "file": "data/conf/version.txt",
                           "regular": "(\d+.\d+.\d+)", "regular_len": 0,
                           "vul_version": "1.5.5~1.5.7", "ver_type": "range"},
               "repair_file": {"type": "file",
                               "file": [{"file": "application/common.php",
                                         "regular": '''$login_errnum_key = 'adminlogin_'.md5('login_errnum_'.$admin_info['user_name']);'''}]},
               }
            ,
            {"cms_list": [], "dangerous": "4", "cms_name": "eyoucms",
             "ps": "eyoucms 1.5.1~1.5.4 存在多个高危安全漏洞,CNVD-2021-82431,CNVD-2021-82429,CNVD-2021-72772,CNVD-2021-51838,CNVD-2021-51836,CNVD-2021-41520,CNVD-2021-24745,,CNVD-2021-26007,CNVD-2021-26099,CNVD-2021-41520",
             "name": "eyoucms 1.5.1~1.5.4 存在多个高危安全漏洞,CNVD-2021-82431,CNVD-2021-82429,CNVD-2021-72772,CNVD-2021-51838,CNVD-2021-51836,CNVD-2021-41520,CNVD-2021-24745,,CNVD-2021-26007,CNVD-2021-26099,CNVD-2021-41520",
             "determine": ["data/conf/version.txt", "application/api/controller/Uploadify.php",
                           "application/extra/extra_cache_key.php",
                           "application/admin/controller/Uploadify.php"],
             "version": {"type": "file", "file": "data/conf/version.txt",
                         "regular": "(\d+.\d+.\d+)", "regular_len": 0,
                         "vul_version": "1.5.1~1.5.4", "ver_type": "range"},
             "repair_file": {"type": "file",
                             "file": [{"file": "application/common.php",
                                       "regular": '''$citysite_db->where(['domain'=>$s_arr[0]])->cache(true, EYOUCMS_CACHE_TIME, 'citysite')->count()'''}]},
             },
            {"cms_list": [], "dangerous": "4", "cms_name": "eyoucms",
             "ps": "eyoucms 1.4.7 存在多个高危安全漏洞,CNVD-2020-46317,CNVD-2020-49065,CNVD-2020-44394,CNVD-2020-44392,CNVD-2020-44391,CNVD-2020-47671,CNVD-2020-50721",
             "name": "eyoucms 1.4.7 存在多个高危安全漏洞,CNVD-2020-46317,CNVD-2020-49065,CNVD-2020-44394,CNVD-2020-44392,CNVD-2020-44391,CNVD-2020-47671,CNVD-2020-50721",
             "determine": ["data/conf/version.txt", "application/api/controller/Uploadify.php",
                           "application/extra/extra_cache_key.php",
                           "application/admin/controller/Uploadify.php"],
             "version": {"type": "file", "file": "data/conf/version.txt",
                         "regular": "(\d+.\d+.\d+)", "regular_len": 0,
                         "vul_version": "1.4.7~1.4.7", "ver_type": "range"},
             "repair_file": {"type": "file",
                             "file": [{"file": "application/common.php",
                                       "regular": '''function GetTagIndexRanking($limit = 5, $field = 'id, tag')'''}]},
             },
            {"cms_list": [], "dangerous": "4", "cms_name": "eyoucms",
             "ps": "eyoucms 1.4.6 存在多个高危安全漏洞,CNVD-2020-44116,CNVD-2020-32622,CNVD-2020-28132,CNVD-2020-28083,CNVD-2020-28064,CNVD-2020-33104",
             "name": "eyoucms 1.4.6 存在多个高危安全漏洞,CNVD-2020-44116,CNVD-2020-32622,CNVD-2020-28132,CNVD-2020-28083,CNVD-2020-28064,CNVD-2020-33104",
             "determine": ["data/conf/version.txt", "application/api/controller/Uploadify.php",
                           "application/extra/extra_cache_key.php",
                           "application/admin/controller/Uploadify.php"],
             "version": {"type": "file", "file": "data/conf/version.txt",
                         "regular": "(\d+.\d+.\d+)", "regular_len": 0,
                         "vul_version": "1.4.6~1.4.6", "ver_type": "range"},
             "repair_file": {"type": "file",
                             "file": [{"file": "application/common.php",
                                       "regular": '''preg_replace('#^(/[/\w]+)?(/uploads/|/public/static/)#i'''}]},
             }
            , {"cms_list": [], "dangerous": "4", "cms_name": "eyoucms",
               "ps": "eyoucms 1.3.9~1.4.4 存在多个安全漏洞CNVD-2020-02271,CNVD-2020-02824,CNVD-2020-18735,CNVD-2020-18677,CNVD-2020-23229,CNVD-2020-23805,CNVD-2020-23820",
               "name": "eyoucms 1.3.9~1.4.4 存在多个安全漏洞CNVD-2020-02271,CNVD-2020-02824,CNVD-2020-18735,CNVD-2020-18677,CNVD-2020-23229,CNVD-2020-23805,CNVD-2020-23820",
               "determine": ["data/conf/version.txt", "application/api/controller/Uploadify.php",
                             "application/extra/extra_cache_key.php",
                             "application/admin/controller/Uploadify.php"],
               "version": {"type": "file", "file": "data/conf/version.txt",
                           "regular": "(\d+.\d+.\d+)", "regular_len": 0,
                           "vul_version": "1.3.9~1.4.4", "ver_type": "range"},
               "repair_file": {"type": "file",
                               "file": [{"file": "application/common.php",
                                         "regular": '''$TimingTaskRow = model('Weapp')->getWeappList('TimingTask');'''}]},
               },
            {"cms_list": [], "dangerous": "4", "cms_name": "eyoucms", "ps": "eyoucms 1.4.1 存在命令执行漏洞",
             "name": "eyoucms 1.4.1 存在命令执行漏洞",
             "determine": ["data/conf/version.txt", "application/api/controller/Uploadify.php",
                           "application/extra/extra_cache_key.php",
                           "application/admin/controller/Uploadify.php"],
             "version": {"type": "file", "file": "data/conf/version.txt",
                         "regular": "(\d+.\d+.\d+)", "regular_len": 0,
                         "vul_version": "1.4.1~1.4.1", "ver_type": "range"},
             "repair_file": {"type": "file",
                             "file": [{"file": "application/route.php",
                                       "regular": '''$weapp_route_file = 'plugins/route.php';'''}]},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "eyoucms", "ps": "eyoucms<=1.3.8 存在SQL注入、存在插件上传漏洞",
             "name": "eyoucms<=1.3.8 存在SQL注入、存在插件上传漏洞",
             "determine": ["data/conf/version.txt", "application/api/controller/Uploadify.php",
                           "application/extra/extra_cache_key.php",
                           "application/admin/controller/Uploadify.php"],
             "version": {"type": "file", "file": "data/conf/version.txt",
                         "regular": "(\d+.\d+.\d+)", "regular_len": 0,
                         "vul_version": "1.0.0~1.3.8", "ver_type": "range"},
             "repair_file": {"type": "file",
                             "file": [{"file": "core/library/think/template/taglib/Eyou.php",
                                       "regular": '''$notypeid  = !empty($tag['notypeid']) ? $tag['notypeid'] : '';'''}]},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "eyoucms", "ps": "eyoucms<=1.3.4 存在后台文件上传漏洞",
             "name": "eyoucms<=1.3.4 存在后台文件上传漏洞",
             "determine": ["data/conf/version.txt", "application/api/controller/Uploadify.php",
                           "application/extra/extra_cache_key.php",
                           "application/admin/controller/Uploadify.php"],
             "version": {"type": "file", "file": "data/conf/version.txt",
                         "regular": "(\d+.\d+.\d+)", "regular_len": 0,
                         "vul_version": "1.0.0~1.3.4", "ver_type": "range"},
             "repair_file": {"type": "file",
                             "file": [{"file": "application/common.php",
                                       "regular": '''include_once EXTEND_PATH."function.php";'''}]},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "eyoucms", "ps": "eyoucms 1.0 存在任意文件上传漏洞",
             "name": "eyoucms 1.0 存在任意文件上传漏洞",
             "determine": ["data/conf/version.txt", "application/api/controller/Uploadify.php",
                           "application/extra/extra_cache_key.php",
                           "application/admin/controller/Uploadify.php"],
             "version": {"type": "file", "file": "data/conf/version.txt",
                         "regular": "(\d+.\d+.\d+)", "regular_len": 0,
                         "vul_version": "1.0.0~1.1.0", "ver_type": "range"},
             "repair_file": {"type": "file",
                             "file": [{"file": "application/api/controller/Uploadify.php",
                                       "regular": '''目前没用到这个api接口'''}]},
             },
            {"cms_list": [], "dangerous": "2", "cms_name": "海洋CMS", "ps": "海洋CMS 版本过低",
             "name": "海洋CMS 版本过低",
             "determine": ["data/admin/ver.txt", "include/common.php", "include/main.class.php",
                           "detail/index.php"],
             "version": {"type": "file", "file": "data/admin/ver.txt",
                         "regular": "(\d+.\d+?|\d+)", "regular_len": 0,
                         "vul_version": ["6.28", "6.54", "7.2", "8.4", "8.5", "8.6", "8.7", "8.8", "8.9", "9", "9.1",
                                         "9.2", "9.3", "9.4", "9.5", "9.6", "9.7", "9.8", "9.9", "9.91", "9.92", "9.93",
                                         "9.94", "9.96", "9.97", "9.98", "9.99", "10", "10.1", "10.2", "10.3", "10.4",
                                         "10.5", "10.6", "10.7", "10.8", "10.9", "11", "11.1", "11.2", "11.3", "11.4",
                                         "11.5"], "ver_type": "list"},
             "repair_file": {"type": "version", "file": []},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "海洋CMS", "ps": "海洋CMS <=9.95存在前台RCE",
             "name": "海洋CMS <=9.95存在前台RCE",
             "determine": ["data/admin/ver.txt", "include/common.php", "include/main.class.php",
                           "detail/index.php"],
             "version": {"type": "file", "file": "data/admin/ver.txt",
                         "regular": "(\d+.\d+?|\d+)", "regular_len": 0,
                         "vul_version": ["6.28", "6.54", "7.2", "8.4", "8.5", "8.6", "8.7", "8.8", "8.9", "9", "9.1",
                                         "9.2", "9.3", "9.4", "9.5", "9.6", "9.7", "9.8", "9.9", "9.91", "9.92", "9.93",
                                         "9.94"], "ver_type": "list"},
             "repair_file": {"type": "file",
                             "file": [{"file": "include/common.php",
                                       "regular": ''''$jpurl='//'.$_SERVER['SERVER_NAME']'''}]},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "ThinkCMF", "ps": "ThinkCMF CVE-2019-6713漏洞",
             "name": "ThinkCMF CVE-2019-6713",
             "determine": ["public/index.php", "app/admin/hooks.php", "app/admin/controller/NavMenuController.php",
                           "simplewind/cmf/hooks.php"],
             "version": {"type": "file", "file": "public/index.php",
                         "regular": "THINKCMF_VERSION.+'(\d+.\d+.\d+)'", "regular_len": 0,
                         "vul_version": ["5.0.190111", "5.0.181231", "5.0.181212", "5.0.180901", "5.0.180626",
                                         "5.0.180525", "5.0.180508"], "ver_type": "list"},
             "repair_file": {"type": "file",
                             "file": [{"file": "app/admin/validate/RouteValidate.php",
                                       "regular": '''protected function checkUrl($value, $rule, $data)'''}]},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "ThinkCMF", "ps": "ThinkCMF templateFile远程代码执行漏洞",
             "name": "ThinkCMF templateFile远程代码执行漏洞",
             "determine": ["simplewind/Core/ThinkPHP.php", "index.php",
                           "data/conf/db.php", "application/Admin/Controller/NavcatController.class.php",
                           "application/Comment/Controller/WidgetController.class.php"],
             "version": {"type": "file", "file": "index.php",
                         "regular": "THINKCMF_VERSION.+(\d+.\d+.\d+)'", "regular_len": 0,
                         "vul_version": "1.6.0~2.2.2", "ver_type": "range"},
             "repair_file": {"type": "file",
                             "file": [{"file": "application/Comment/Controller/WidgetController.class.php",
                                       "regular": '''protected function display('''}]},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "zfaka", "ps": "zfaka存在SQL注入漏洞", "name": "zfaka存在SQL注入漏洞",
             "determine": ["application/init.php", "application/function/F_Network.php",
                           "application/controllers/Error.php", "application/modules/Admin/controllers/Profiles.php"],
             "version": {"type": "file", "file": "application/init.php",
                         "regular": "VERSION.+'(\d+.\d+.\d+)'", "regular_len": 0,
                         "vul_version": "1.0.0~1.4.4", "ver_type": "range"},
             "repair_file": {"type": "file", "file": [{"file": "application/function/F_Network.php",
                                                       "regular": '''if(filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_IPV4'''}]},
             }
            ,
            {"cms_list": [], "dangerous": "3", "cms_name": "dedecms", "ps": "dedecms 20210719安全更新",
             "name": "dedecms 20210719安全更新",
             "determine": ["data/admin/ver.txt", "data/common.inc.php",
                           "dede/shops_operations_userinfo.php", "member/edit_space_info.php"],
             "version": {"type": "file", "file": "data/admin/ver.txt",
                         "regular": "(\d+)", "regular_len": 0,
                         "vul_version": ["20180109"], "ver_type": "list"},
             "repair_file": {"type": "file", "file": [{"file": "include/dedemodule.class.php",
                                                       "regular": '''if(preg_match("#[^a-z]+(eval|assert)[\s]*[(]#i"'''}]},
             }
            ,
            {"cms_list": [], "dangerous": "3", "cms_name": "dedecms", "ps": "dedecms 20220125安全更新",
             "name": "dedecms 20220125安全更新",
             "determine": ["data/admin/ver.txt", "data/common.inc.php",
                           "dede/shops_operations_userinfo.php", "member/edit_space_info.php"],
             "version": {"type": "file", "file": "data/admin/ver.txt",
                         "regular": "(\d+)", "regular_len": 0,
                         "vul_version": ["20180109", "20220325", "20210201", "20210806"], "ver_type": "list"},
             "repair_file": {"type": "file", "file": [{"file": "include/downmix.inc.php",
                                                       "regular": '''上海卓卓网络科技有限公司'''}]},
             }
            ,
            {"cms_list": [], "dangerous": "3", "cms_name": "dedecms", "ps": "dedecms 20220218安全更新",
             "name": "dedecms 20220218安全更新",
             "determine": ["data/admin/ver.txt", "data/common.inc.php",
                           "dede/shops_operations_userinfo.php", "member/edit_space_info.php"],
             "version": {"type": "file", "file": "data/admin/ver.txt",
                         "regular": "(\d+)", "regular_len": 0,
                         "vul_version": ["20180109", "20220325", "20210201", "20210806"], "ver_type": "list"},
             "repair_file": {"type": "file", "file": [{"file": "dede/file_manage_control.php",
                                                       "regular": '''phpinfo,eval,assert,exec,passthru,shell_exec,system,proc_open,popen'''}]},
             }
            , {"cms_list": [], "dangerous": "3", "cms_name": "dedecms", "ps": "dedecms 20220310安全更新",
               "name": "dedecms 20220310安全更新",
               "determine": ["data/admin/ver.txt", "data/common.inc.php",
                             "dede/shops_operations_userinfo.php", "member/edit_space_info.php"],
               "version": {"type": "file", "file": "data/admin/ver.txt",
                           "regular": "(\d+)", "regular_len": 0,
                           "vul_version": ["20180109", "20220325", "20210201", "20210806"], "ver_type": "list"},
               "repair_file": {"type": "file", "file": [{"file": "dede/file_manage_control.php",
                                                         "regular": '''phpinfo,eval,assert,exec,passthru,shell_exec,system,proc_open,popen'''}]},
               },
            {"cms_list": [], "dangerous": "3", "cms_name": "dedecms", "ps": "dedecms 20220325安全更新",
             "name": "dedecms 20220325安全更新",
             "determine": ["data/admin/ver.txt", "data/common.inc.php",
                           "dede/shops_operations_userinfo.php", "member/edit_space_info.php"],
             "version": {"type": "file", "file": "data/admin/ver.txt",
                         "regular": "(\d+)", "regular_len": 0,
                         "vul_version": ["20180109", "20220325", "20210201", "20210806"], "ver_type": "list"},
             "repair_file": {"type": "file", "file": [{"file": "plus/mytag_js.php",
                                                       "regular": '''phpinfo,eval,assert,exec,passthru,shell_exec,system,proc_open,popen'''}]},
             },
            {"cms_list": [], "dangerous": "2", "cms_name": "dedecms", "ps": "dedecms 已开启会员注册功能",
             "name": "dedecms 已开启会员注册功能",
             "determine": ["data/admin/ver.txt", "data/common.inc.php",
                           "dede/shops_operations_userinfo.php", "member/edit_space_info.php"],
             "version": {"type": "file", "file": "data/admin/ver.txt",
                         "regular": "(\d+)", "regular_len": 0,
                         "vul_version": ["20180109", "20220325", "20210201", "20210806"], "ver_type": "list"},
             "repair_file": {"type": "phpshell", "file": [{"file": "member/get_user_cfg_mb_open.php",
                                                           "phptext": '''<?php require_once(dirname(__FILE__).'/../include/common.inc.php');echo 'start'.$cfg_mb_open.'end';?>''',
                                                           "regular": '''start(\w)end''', "reulst_type": "str",
                                                           "result": "startYend"}]},
             }
            , {"cms_list": [], "dangerous": "3", "cms_name": "MetInfo", "ps": "MetInfo 7.5.0存在SQL注入漏洞",
               "name": "MetInfo7.5.0存在SQL注入漏洞",
               "determine": ["cache/config/config_metinfo.php", "app/system/entrance.php",
                             "app/system/databack/admin/index.class.php", "cache/config/app_config_metinfo.php"],
               "version": {"type": "file", "file": "cache/config/config_metinfo.php",
                           "regular": "value.+'(\d+.\d+.\d+)'", "vul_version": "7.5.0~7.5.0", "ver_type": "range"},
               "repair_file": {"type": "version", "file": []},
               },
            {"cms_list": [], "dangerous": "3", "cms_name": "MetInfo", "ps": "MetInfo 7.3.0存在SQL注入漏洞、XSS漏洞",
             "name": "MetInfo 7.3.0存在SQL注入漏洞、XSS漏洞",
             "determine": ["app/system/entrance.php", "app/system/admin/admin/index.class.php",
                           "app/system/admin/admin/templates/admin_add.php"],
             "version": {"type": "file", "file": "app/system/entrance.php",
                         "regular": "SYS_VER.+'(\d+.\d+.\d+)'", "vul_version": "7.3.0~7.3.0", "ver_type": "range"},
             "repair_file": {"type": "version", "file": []},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "MetInfo", "ps": "MetInfo 7.2.0存在SQL注入漏洞、XSS漏洞",
             "name": "MetInfo 7.2.0存在SQL注入漏洞、XSS漏洞",
             "determine": ["app/system/entrance.php", "app/system/admin/admin/index.class.php",
                           "app/system/admin/admin/templates/admin_add.php"],
             "version": {"type": "file", "file": "app/system/entrance.php",
                         "regular": "SYS_VER.+'(\d+.\d+.\d+)'", "vul_version": "7.2.0~7.2.0", "ver_type": "range"},
             "repair_file": {"type": "version", "file": []},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "MetInfo", "ps": "MetInfo 7.1.0存在文件上传漏洞、SQL注入漏洞、XSS漏洞",
             "name": "MetInfo 7.1.0存在文件上传漏洞、SQL注入漏洞、XSS漏洞",
             "determine": ["app/system/entrance.php", "app/system/admin/admin/index.class.php",
                           "app/system/admin/admin/templates/admin_add.php"],
             "version": {"type": "file", "file": "app/system/entrance.php",
                         "regular": "SYS_VER.+'(\d+.\d+.\d+)'", "vul_version": "7.1.0~7.1.0", "ver_type": "range"},
             "repair_file": {"type": "version", "file": []},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "MetInfo", "ps": "MetInfo 7.0.0 存在SQL注入漏洞",
             "name": "MetInfo7.0.0存在SQL注入漏洞",
             "determine": ["app/system/entrance.php", "app/system/admin/admin/index.class.php",
                           "app/system/admin/admin/templates/admin_add.php"],
             "version": {"type": "file", "file": "app/system/entrance.php",
                         "regular": "SYS_VER.+'(\d+.\d+.\d+)'", "vul_version": "7.0.0~7.0.0", "ver_type": "range"},
             "repair_file": {"type": "version", "file": []},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "MetInfo", "ps": "MetInfo 6.1.2存在SQL注入漏洞",
             "name": "MetInfo 6.1.2存在SQL注入漏洞",
             "determine": ["app/system/entrance.php", "app/system/admin/admin/templates/admin_add.php"],
             "version": {"type": "file", "file": "app/system/entrance.php",
                         "regular": "SYS_VER.+'(\d+.\d+.\d+)'", "vul_version": "6.1.2~6.1.2", "ver_type": "range"},
             "repair_file": {"type": "version", "file": []},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "MetInfo", "ps": "MetInfo 6.1.1 存在已知后台权限可以获取webshell漏洞",
             "name": "MetInfo 6.1.1 存在已知后台权限可以获取webshell漏洞",
             "determine": ["app/system/entrance.php", "app/system/admin/admin/templates/admin_add.php"],
             "version": {"type": "file", "file": "app/system/entrance.php",
                         "regular": "SYS_VER.+'(\d+.\d+.\d+)'", "vul_version": "6.1.1~6.1.1", "ver_type": "range"},
             "repair_file": {"type": "version", "file": []},
             },
            {"cms_list": [], "dangerous": "2", "cms_name": "emlog", "ps": "emlog版本太低建议升级到Pro版本",
             "name": "emlog版本太低建议升级到Pro版本",
             "determine": ["include/lib/option.php", "admin/views/template_install.php",
                           "include/lib/checkcode.php", "include/controller/author_controller.php"],
             "version": {"type": "file", "file": "include/lib/option.php",
                         "regular": "EMLOG_VERSION.+'(\d+.\d+.\d+)'", "vul_version": "5.3.1~6.0.0",
                         "ver_type": "range"},
             "repair_file": {"type": "version", "file": []},
             },
            {"cms_list": [], "dangerous": "1", "cms_name": "帝国CMS", "ps": "EmpireCMs7.0后台XSS漏洞",
             "name": "EmpireCMs7.0后台XSS漏洞",
             "determine": ["e/class/EmpireCMS_version.php", "e/search/index.php",
                           "e/member/EditInfo/index.php", "e/ViewImg/index.html"],
             "version": {"type": "file", "file": "e/class/EmpireCMS_version.php",
                         "regular": "EmpireCMS_VERSION.+'(\d+.\d+)'", "vul_version": "7.0~7.0", "ver_type": "range"},
             "repair_file": {"type": "version", "file": []},
             },
            {"cms_list": [], "dangerous": "2", "cms_name": "帝国CMS", "ps": "EmpireCMs6.0~7.5 后台代码执行",
             "name": "EmpireCMs6.0~7.5 后台代码执行",
             "determine": ["e/class/EmpireCMS_version.php", "e/search/index.php",
                           "e/member/EditInfo/index.php", "e/ViewImg/index.html"],
             "version": {"type": "file", "file": "e/class/EmpireCMS_version.php",
                         "regular": "EmpireCMS_VERSION.+'(\d+.\d+)'", "vul_version": "6.0~7.5", "ver_type": "range"},
             "repair_file": {"type": "version", "file": []},
             },
            {"cms_list": [], "dangerous": "2", "cms_name": "帝国CMS", "ps": "EmpireCMs6.0~7.5 后台导入模型代码执行",
             "name": "EmpireCMs6.0~7.5 后台导入模型代码执行",
             "determine": ["e/class/EmpireCMS_version.php", "e/search/index.php",
                           "e/member/EditInfo/index.php", "e/ViewImg/index.html"],
             "version": {"type": "file", "file": "e/class/EmpireCMS_version.php",
                         "regular": "EmpireCMS_VERSION.+'(\d+.\d+)'", "vul_version": "6.0~7.5", "ver_type": "range"},
             "repair_file": {"type": "version", "file": []},
             },
            {"cms_list": [], "dangerous": "2", "cms_name": "discuz", "ps": "Discuz utility组件对外访问",
             "name": "Discuz utility组件对外访问",
             "determine": ["uc_client/client.php", "uc_server/lib/uccode.class.php",
                           "uc_server/model/version.php", "source/discuz_version.php"],
             "version": {"type": "single_file", "file": "utility/convert/index.php",
                         "regular": "DISCUZ_RELEASE.+'(\d+)'", "regular_len": 0,
                         "vul_version": ["1"], "ver_type": "list"},
             "repair_file": {"type": "single_file", "file": [{"file": "utility/convert/index.php",
                                                              "regular": '''$source = getgpc('source') ? getgpc('source') : getgpc('s');'''}]},
             },
            {"cms_list": [], "dangerous": "2", "cms_name": "discuz", "ps": "Discuz邮件认证入口CSRF以及时间限制可绕过漏洞",
             "name": "Discuz邮件认证入口CSRF以及时间限制可绕过漏洞",
             "determine": ["uc_client/client.php", "uc_server/lib/uccode.class.php",
                           "uc_server/model/version.php", "source/discuz_version.php"],
             "version": {"type": "file", "file": "source/discuz_version.php",
                         "regular": "DISCUZ_RELEASE.+'(\d+)'", "regular_len": 0,
                         "vul_version": ["20210816",
                                         "20210630", "20210520", "20210320", "20210119", "20200818", "20191201",
                                         "20190917"], "ver_type": "list"},
             "repair_file": {"type": "file", "file": [{"file": "source/admincp/admincp_setting.php",
                                                       "regular": '''showsetting('setting_permissions_mailinterval', 'settingnew[mailinterval]', $setting['mailinterval'], 'text');'''}]},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "discuz", "ps": "Discuz 报错注入SQL", "name": "Discuz 报错注入SQL",
             "determine": ["uc_client/client.php", "uc_server/lib/uccode.class.php",
                           "uc_server/model/version.php", "source/discuz_version.php"],
             "version": {"type": "file", "file": "source/discuz_version.php",
                         "regular": "DISCUZ_RELEASE.+'(\d+)'", "regular_len": 0,
                         "vul_version": ["20211124", "20211022", "20210926", "20210917", "20210816",
                                         "20210630", "20210520", "20210320", "20210119", "20200818", "20191201",
                                         "20190917"], "ver_type": "list"},
             "repair_file": {"type": "file", "file": [
                 {"file": "api/uc.php",
                  "regular": '''if($len > 22 || $len < 3 || preg_match("/\s+|^c:\\con\\con|[%,\*\"\s\<\>\&\(\)']/is", $get['newusername']))'''}]},
             }
            , {"cms_list": [], "dangerous": "3", "cms_name": "discuz", "ps": "Discuz备份恢复功能执行任意SQL漏洞",
               "name": "Discuz备份恢复功能执行任意SQL漏洞",
               "determine": ["uc_client/client.php", "uc_server/lib/uccode.class.php", "uc_server/model/version.php",
                             "source/discuz_version.php"],
               "version": {"type": "file", "file": "source/discuz_version.php", "regular": "DISCUZ_RELEASE.+'(\d+)'",
                           "regular_len": 0,
                           "vul_version": ["20211231", "20211124", "20211022", "20210926", "20210917", "20210816",
                                           "20210630", "20210520", "20210320", "20210119", "20200818", "20191201",
                                           "20190917"], "ver_type": "list"},
               "repair_file": {"type": "file", "file": [
                   {"file": "api/db/dbbak.php",
                    "regular": '''if(!preg_match('/^backup_(\d+)_\w+$/', $get['sqlpath']) || !preg_match('/^\d+_\w+\-(\d+).sql$/', $get['dumpfile']))'''}]},
               },
            {"cms_list": ["maccms10"], "dangerous": "4", "cms_name": "Thinkphp", "ps": "thinkphp5.0.X漏洞",
             "name": "Thinkphp5.X代码执行",
             "determine": ["thinkphp/base.php", "thinkphp/library/think/App.php", "thinkphp/library/think/Request.php"],
             "version": {"type": "file", "file": "thinkphp/base.php", "regular": "THINK_VERSION.+(\d+.\d+.\d+)",
                         "vul_version": "5.0.0~5.0.24", "ver_type": "range"},
             "repair_file": {"type": "file", "file": [
                 {"file": "thinkphp/library/think/App.php", "regular": '''(!preg_match('/^[A-Za-z](\w|\.)*$/'''},
                 {"file": "thinkphp/library/think/Request.php",
                  "regular": '''if (in_array($method, ['GET', 'POST', 'DELETE', 'PUT', 'PATCH']))'''}]},
             },
            {"cms_list": ["maccms10"], "dangerous": "3", "cms_name": "Thinkphp", "ps": "Thinkphp5.0.15 SQL注入漏洞",
             "name": "Thinkphp5.0.15 SQL注入漏洞",
             "determine": ["thinkphp/base.php", "thinkphp/library/think/App.php",
                           "thinkphp/library/think/Request.php"],
             "version": {"type": "file", "file": "thinkphp/base.php", "regular": "THINK_VERSION.+(\d+.\d+.\d+)",
                         "vul_version": "5.0.13~5.0.15", "ver_type": "range"},
             "repair_file": {"type": "file", "file": [
                 {"file": "thinkphp/library/think/db/Builder.php",
                  "regular": '''if ($key == $val[1]) {
                                $result[$item] = $this->parseKey($val[1]) . '+' . floatval($val[2]);
                            }'''}]},
             },
            {"cms_list": ["maccms10"], "dangerous": "3", "cms_name": "Thinkphp", "ps": "Thinkphp5.0.10 SQL注入漏洞",
             "name": "Thinkphp5.0.10 SQL注入漏洞",
             "determine": ["thinkphp/base.php", "thinkphp/library/think/App.php",
                           "thinkphp/library/think/Request.php"],
             "version": {"type": "file", "file": "thinkphp/base.php", "regular": "THINK_VERSION.+(\d+.\d+.\d+)",
                         "vul_version": "5.0.10~5.0.10", "ver_type": "range"},
             "repair_file": {"type": "file", "file": [
                 {"file": "thinkphp/library/think/Request.php",
                  "regular": '''preg_match('/^(EXP|NEQ|GT|EGT|LT|ELT|OR|XOR|LIKE|NOTLIKE|NOT LIKE|NOT BETWEEN|NOTBETWEEN|BETWEEN|NOTIN|NOT IN|IN)$/i'''}]},
             },
            {"cms_list": ["maccms10"], "dangerous": "3", "cms_name": "Thinkphp",
             "ps": "Thinkphp5.0.0 到 Thinkphp5.0.21 SQL注入漏洞", "name": "Thinkphp5.0.21 SQL注入漏洞",
             "determine": ["thinkphp/base.php", "thinkphp/library/think/App.php",
                           "thinkphp/library/think/Request.php"],
             "version": {"type": "file", "file": "thinkphp/base.php", "regular": "THINK_VERSION.+(\d+.\d+.\d+)",
                         "vul_version": "5.0.0~5.0.21", "ver_type": "range"},
             "repair_file": {"type": "file", "file": [
                 {"file": "thinkphp/library/think/db/builder/Mysql.php",
                  "regular": '''if ($strict && !preg_match('/^[\w\.\*]+$/', $key))'''}]},
             },
            {"cms_list": ["maccms10"], "dangerous": "3", "cms_name": "Thinkphp", "ps": "Thinkphp5.0.18文件包含漏洞",
             "name": "Thinkphp5.0.18文件包含漏洞",
             "determine": ["thinkphp/base.php", "thinkphp/library/think/App.php",
                           "thinkphp/library/think/Request.php"],
             "version": {"type": "file", "file": "thinkphp/base.php", "regular": "THINK_VERSION.+(\d+.\d+.\d+)",
                         "vul_version": "5.0.0~5.0.18", "ver_type": "range"},
             "repair_file": {"type": "file", "file": [
                 {"file": "thinkphp/library/think/template/driver/File.php",
                  "regular": '''$this->cacheFile = $cacheFile;'''}]},
             },
            {"cms_list": ["maccms10"], "dangerous": "4", "cms_name": "Thinkphp", "ps": "Thinkphp5.0.10远程代码执行",
             "name": "Thinkphp5.0.10远程代码执行",
             "determine": ["thinkphp/base.php", "thinkphp/library/think/App.php",
                           "thinkphp/library/think/Request.php"],
             "version": {"type": "file", "file": "thinkphp/base.php", "regular": "THINK_VERSION.+(\d+.\d+.\d+)",
                         "vul_version": "5.0.0~5.0.10", "ver_type": "range"},
             "repair_file": {"type": "file", "file": [
                 {"file": "thinkphp/library/think/App.php",
                  "regular": '''$data   = "<?php\n//" . sprintf('%012d', $expire) . "\n exit();?>;'''}]},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "Wordpress", "ps": "CVE-2022–21661 Wordpress SQL注入",
             "name": "CVE-2022–21661 Wordpress SQL注入",
             "determine": ["wp-includes/version.php", "wp-settings.php", "wp-comments-post.php",
                           "wp-includes/class-wp-hook.php"],
             "version": {"type": "file", "file": "wp-includes/version.php", "regular": "wp_version.+(\d+.\d+.\d+)",
                         "vul_version": "4.1.0~5.8.2", "ver_type": "range"},
             "repair_file": {"type": "file", "file": [{"file": "wp-includes/class-wp-tax-query.php",
                                                       "regular": '''if ( 'slug' === $query['field'] || 'name' === $query['field'] )'''}]}}
        ]
        return result

    def getCmsType(self, webinfo, cmsinfo):
        '''
        @name 确定CMS类型
        @author lkq<2022-3-30>
        @param webinfo   网站信息
        @param cmsinfo   CMS信息
        '''

        for i in cmsinfo['determine']:
            path = webinfo['path'] + '/' + i
            if not os.path.exists(path):
                return False

        # 获取cms 的版本
        if 'cms_name' in webinfo:
            if webinfo['cms_name'] != cmsinfo['cms_name']:
                if not cmsinfo['cms_name'] in cmsinfo['cms_list']: return False

        version = self.getCmsVersion(webinfo, cmsinfo)
        if not version: return False
        webinfo['version_info'] = version
        # 判断是否在漏洞版本中
        if not self.getVersionInfo(version, cmsinfo['version']): return False
        webinfo['cms_name'] = cmsinfo['cms_name']
        # 判断该网站是否修复了
        is_vufix = self.getCmsVersionVulFix(webinfo, cmsinfo)
        if not is_vufix: return False
        webinfo['is_vufix'] = True
        return True

    def getCmsVersion(self, webinfo, cmsinfo):
        '''
        @name 获取CMS版本号
        @author lkq<2022-3-30>
        @param get
        '''

        version = cmsinfo["version"]
        if 'regular_len' in version:
            info = version['regular_len']
        else:
            info = 0
        if version['type'] == 'file':
            path = webinfo['path'] + '/' + version['file']
            # public.print_log(path)
            if os.path.exists(path):
                path_info = public.ReadFile(path)
                if path_info and re.search(version['regular'], path_info):
                    if not 'cms_name' in webinfo:
                        webinfo['cms_name'] = cmsinfo['cms_name']
                    return re.findall(version['regular'], path_info)[info]
        elif version['type'] == 'single_file':
            return "1"
        elif version["type"] == 'is_file':
            path = webinfo['path'] + '/' + version['file']
            if os.path.exists(path):
                return "1"
        return False

    def getVersionInfo(self, version, versionlist):
        '''
        @name 判断当前版本在不在受影响的版本列表中
        @author lkq<2022-3-30>
        @param version 版本号
        @param versionlist 版本号列表
        '''
        if versionlist['ver_type'] == 'range':
            try:
                versionlist = versionlist['vul_version']
                start, end = versionlist.split('~')
                if version.split('.')[0] >= start.split('.')[0] and version.split('.')[0] <= end.split('.')[0]:
                    start = ''.join(start.split('.'))
                    end = ''.join(end.split('.'))
                    version = ''.join(version.split('.'))
                    if version >= start and version <= end:
                        return True
                return False
            except:
                return False
        elif versionlist['ver_type'] == 'list':
            if version in versionlist['vul_version']:
                return True
            return False

    def getCmsVersionVulFix(self, webinfo, cmsinfo):
        '''
        @name 判断漏洞是否修复
        @author lkq<2022-3-30>
        @param get
        '''
        repair_file = cmsinfo['repair_file']
        if repair_file['type'] == 'file':
            for i in repair_file['file']:
                path = webinfo['path'] + '/' + i['file']
                if os.path.exists(path):
                    path_info = public.ReadFile(path)
                    if not i['regular'] in path_info:
                        return True
        elif repair_file['type'] == 'single_file':
            for i in repair_file['file']:
                path = webinfo['path'] + '/' + i['file']
                if os.path.exists(path):
                    path_info = public.ReadFile(path)
                    if i['regular'] in path_info:
                        return True
        elif repair_file['type'] == 'version':
            return True
        elif repair_file['type'] == 'is_file':
            for i in repair_file['file']:
                path = webinfo['path'] + '/' + i['file']
                if os.path.exists(path):
                    return True
        elif repair_file['type'] == 'phpshell':
            for i in repair_file['file']:
                try:
                    path = webinfo['path'] + '/' + i['file']
                    public.WriteFile(path, i['phptext'])
                    dir_name = os.path.dirname(path)
                    getname = os.path.basename(path)
                    data = public.ExecShell("cd %s && php %s" % (dir_name, getname))
                    if len(data) <= 0: return False
                    if i['result'] in data[0]:
                        os.remove(path)
                        return True
                    else:
                        os.remove(path)
                except:
                    continue
        return False

    def list(self, get):
        '''
        @name 获取缓存的历史记录
        @return webinfo
        '''
        import traceback
        try:
            # return {"info": [], "time": 0, 'loophole_num': 0, 'site_num': 0}
            if not cache.get("scaing_info") or not cache.get("scaing_info_time"):
                return {"info": [], "time": 0, 'loophole_num': 0, 'site_num': 0}
            result = {"info": cache.get("scaing_info"), "time": cache.get("scaing_info_time")}
            loophole_num = sum([len(i['cms']) for i in result['info']])
            result['info'] = []
            result['loophole_num'] = loophole_num
            result['site_num'] = len(self.getWebInfo(None))
            return result
        except:
            print(traceback.format_exc())

    def get_cron_scanin_info(self, get):
        if "/www/server/panel" not in sys.path:
            sys.path.insert(0, '/www/server/panel')

        from mod.base.push_mod import TaskConfig
        res = TaskConfig().get_by_keyword("vulnerability_scanning", "vulnerability_scanning")
        if not res:
            return {"cycle": 1, "channel": "", "status": 0}
        else:
            return {
                "cycle": res['task_data']["cycle"],
                "channel": ",".join(res['sender']),
                "status": int(res['status'])
            }

    def set_cron_scanin_info(self, get):
        """设置漏洞扫描定时任务
        @param get: 请求参数对象
        @return: dict 设置结果
        """
        # status = bool(get.get("status/d", 0))
        # channel = get.get("channel/s", "")
        # day = get.get("day/d", 0)
        # if "/www/server/panel" not in sys.path:
        #     sys.path.insert(0, '/www/server/panel')

        # from mod.base.push_mod.safe_mod_push import VulnerabilityScanningTask

        # res = VulnerabilityScanningTask.set_push_task(status, day, channel.split(","))
        # if not res:
        #     return public.returnMsg(True, '设置成功')
        # else:
        #     return public.returnMsg(False, res)
        # 优化健壮性
        try:
            # 参数处理部分
            try:
                status = bool(int(get.get("status", 0)))
            except (ValueError, TypeError):
                status = False
                
            channel = get.get("channel", "")
            if not isinstance(channel, str):
                channel = str(channel)
                
            try:
                # 先尝试转换为浮点数，再向下取整
                day_float = float(get.get("day", 0))
                day = int(day_float)  # 浮点数向下取整
            except (ValueError, TypeError):
                day = 1
                
            # 确保参数在有效范围内
            if day < 0:
                day = 1
                

            try:
                from mod.base.push_mod.safe_mod_push import VulnerabilityScanningTask
                
                # 处理channel参数
                if isinstance(channel, str):
                    channel_list = channel.split(",") if channel else []
                elif isinstance(channel, list):
                    channel_list = channel
                else:
                    channel_list = []
                    
                # 设置推送任务
                res = VulnerabilityScanningTask.set_push_task(status, day, channel_list)
                if not res:
                    return public.returnMsg(True, '设置成功')
                else:
                    return public.returnMsg(False, res)
            except ImportError:
                return public.returnMsg(False, "未找到相关模块，请确认系统完整性")
            except Exception as e:
                return public.returnMsg(False, "设置任务时出错: {}".format(str(e)))
                
        except Exception as e:
            # 捕获所有可能的异常，确保API不会崩溃
            return public.returnMsg(False, '设置失败: {}'.format(str(e)))

    def get_crond_find(self, get):
        id = int(get.id)
        data = public.M('crontab').where('id=?', (id,)).find()
        return data

    def multiple_basedir(self, get):
        try:
            site_ids = json.loads(getattr(get, "site_ids", "[]"))
            if not isinstance(site_ids, list) and site_ids:
                return {"status": False, "msg": "参数错误！"}
            stat = get.stat == "open"
        except:
            return {"status": False, "msg": "参数错误！"}

        sites_info = public.M("sites").where(
            "project_type=? AND id IN ({})".format(','.join(["?"]*len(site_ids))), ("PHP", *site_ids)
        ).field("id,path").select()

        res = {
            "errors": [],
            "succeed": [],
        }
        for site in sites_info:
            get_obj = public.dict_obj()
            get_obj.path = site["path"]
            get_obj.id = site["id"]
            run_path = self.GetRunPath(get_obj)
            if not run_path:
                res["errors"].append(public.returnMsg(False, "运行目录获取失败"))
            filename = (site["path"] + run_path + '/.user.ini').replace("//", "/")
            if stat is False:  # 关闭
                if os.path.exists(filename):
                    new_get = public.dict_obj()
                    new_get.path = site["path"]
                    tmp = self.SetDirUserINI(new_get)
                    tmp["id"] = site["id"]
                    if tmp["status"] is False:
                        res["errors"].append(tmp)
                    else:
                        res["succeed"].append(tmp)
                else:
                    res["succeed"].append({
                        "status": True,
                        "msg": "防跨站文件不存在，跳过关闭",
                        "id": site["id"],
                    })
            else:
                if not os.path.exists(filename):
                    new_get = public.dict_obj()
                    new_get.path = site["path"]
                    tmp = self.SetDirUserINI(new_get)
                    tmp["id"] = site["id"]
                    if tmp["status"] is False:
                        res["errors"].append(tmp)
                    else:
                        res["succeed"].append(tmp)
                else:
                    res["succeed"].append({"id": site["id"], "status": True, "msg": "防跨站文件存在，跳过操作开启"})
        return res

    def multiple_limit_net(self, get):
        try:
            site_ids = json.loads(getattr(get, "site_ids", "[]"))
            if not isinstance(site_ids, list) and site_ids:
                return {"status": False, "msg": "参数错误！"}
            perserver = get.perserver
            perip = get.perip
            limit_rate = get.limit_rate
            close_limit_net = get.close_limit_net
        except:
            return {"status": False, "msg": "参数错误！"}

        sites_info = public.M("sites").where(
            "project_type=? AND id IN ({})".format(','.join(["?"]*len(site_ids))), ("PHP", *site_ids)
        ).field("id,path").select()

        res = {
            "errors": [],
            "succeed": [],
        }
        if close_limit_net in ("true", "1", 1, True):
            for site in sites_info:
                get_obj = public.dict_obj()
                get_obj.id = site["id"]
                tmp = self.CloseLimitNet(get_obj)
                tmp["id"] = site["id"]
                if tmp["status"] is False:
                    res["errors"].append(tmp)
                else:
                    res["succeed"].append(tmp)
            return res

        for site in sites_info:
            get_obj = public.dict_obj()
            get_obj.id = site["id"]
            get_obj.perserver = perserver
            get_obj.perip = perip
            get_obj.limit_rate = limit_rate
            tmp = self.SetLimitNet(get_obj)
            tmp["id"] = site["id"]
            if tmp["status"] is False:
                res["errors"].append(tmp)
            else:
                res["succeed"].append(tmp)

        return res

    def multiple_referer(self, get):
        try:
            site_ids = json.loads(getattr(get, "site_ids", "[]"))
            if not isinstance(site_ids, list) and site_ids:
                return {"status": False, "msg": "参数错误！"}
            fix = get.fix
            domains = get.domains
            status = get.status
            return_rule = get.return_rule
            http_status = get.http_status
        except:
            return {"status": False, "msg": "参数错误！"}

        sites_info = public.M("sites").where(
            "project_type=? AND id IN ({})".format(','.join(["?"]*len(site_ids))), ("PHP", *site_ids)
        ).field("id,name").select()

        if len(domains) < 3:
            domains = ""

        sites_domains = {s["id"]: domains for s in sites_info}
        domains_info = public.M("domain").where(
            "pid IN ({})".format(','.join(["?"]*len(sites_domains))), list(sites_domains.keys())
        ).field("pid,name").select()

        for domain in domains_info:
            sites_domains[domain["pid"]] += ',' + domain["name"]

        # public.print_log(domains_info)

        res = {
            "errors": [],
            "succeed": [],
        }
        for site in sites_info:
            get_obj = public.dict_obj()
            get_obj.id = site["id"]
            get_obj.name = site["name"]
            get_obj.fix = fix
            get_obj.domains = sites_domains[site["id"]].strip(",")
            get_obj.status = status
            get_obj.return_rule = return_rule
            get_obj.http_status = http_status
            tmp = self.SetSecurity(get_obj)
            tmp["id"] = site["id"]
            if tmp["status"] is False:
                res["errors"].append(tmp)
            else:
                res["succeed"].append(tmp)

        return res

    def check_ssl(self, get, port=443):
        try:
            context = ssl.create_default_context()
            hostname = get.hostname
            with socket.create_connection((hostname, port)) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    print(ssock.version())
                    return public.returnMsg(True, f"验证到网站 {hostname}已部署ssl证书!", "")
        except Exception as e:
            error_message = str(e)
            error_translation = {
                "Name or service not known": "这可能是由于以下原因：输入的域名不存在或拼写错误;DNS 服务器无法解析域名；你的网络连接有问题。",
                f"[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostname mismatch, certificate is not valid for '{hostname}'. (_ssl.c:1091)":"证书中的主机名与你尝试连接的主机名不匹配。",
                "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate":"你可能正在尝试连接到的服务器的 SSL 证书无法被信任的证书颁发机构验证。"}
            for error in error_translation:
                if error in error_message:
                    error_message = error_translation[error]
                    break
            return public.returnMsg(False, error_message)

    def is_nginx_http3(self):
        if getattr(self, "_is_nginx_http3", None) is None:
            _is_nginx_http3 = public.ExecShell("nginx -V 2>&1| grep 'http_v3_module'")[0] != ''
            setattr(self, "_is_nginx_http3", _is_nginx_http3)
        return self._is_nginx_http3

    @staticmethod
    def set_security_headers(get):
        try:
            s_info = json.loads(get.security_info.strip())
            site_name = get.site_name.strip()
        except (json.JSONDecodeError, AttributeError):
            return public.returnMsg(False, "参数错误")

        config_file = '{}/vhost/nginx/{}.conf'.format(public.get_panel_path(), site_name)
        conf = public.readFile(config_file)
        if not conf:
            return public.returnMsg(False, "nginx配置文件不存在")

        has_rep = re.compile("#SECURITY-HEADERS-START\n(.*\n){4,10}\s*#SECURITY-HEADERS-END")

        new_security_config = [
            "#SECURITY-HEADERS-START",
            (
                    ("" if s_info.get("x_xss_protection", False) else "# ") +
                    'add_header X-XSS-Protection   "1; mode=block" always;'
            ),
            (
                    ("" if s_info.get("x_content_type_options", False) else "# ") +
                    'add_header X-Content-Type-Options   "nosniff" always;'
            ),
            (
                    ("" if s_info.get("referrer_policy", False) else "# ") +
                    'add_header Referrer-Policy    "no-referrer-when-downgrade" always;'
            ),
            (
                    ("" if s_info.get("content_security_policy", False) else "# ") +
                    '''add_header Content-Security-Policy   "default-src 'self' http: https: ws: wss: data: blob: 'unsafe-inline'; frame-ancestors 'self';" always;'''
            ),
            (
                    ("" if s_info.get("permissions_policy", False) else "# ") +
                    'add_header Permissions-Policy        "interest-cohort=()" always;'
            ),
            "#SECURITY-HEADERS-END"
        ]

        new_security_config_str = "\n".join(["    " + i for i in new_security_config])
        if has_rep.search(conf):
            new_conf = has_rep.sub(new_security_config_str.lstrip(), conf, 1)
        else:
            ssl_rep = re.compile(r"#SSL-END.*\n")
            if not ssl_rep.search(conf):
                return public.returnMsg(False, "无法定位到添加的位置，请注意配置文件")
            new_conf = ssl_rep.sub("#SSL-END\n\n" + new_security_config_str, conf, 1)

        public.writeFile(config_file, new_conf)
        if not public.checkWebConfig() is True:
            public.writeFile(config_file, conf)
            return public.returnMsg(False, "设置失败")

        public.serviceReload()
        return public.returnMsg(True, "设置成功")

    @staticmethod
    def get_security_headers(get):
        try:
            site_name = get.site_name.strip()
        except (json.JSONDecodeError, AttributeError):
            return public.returnMsg(False, "参数错误")

        config_file = '{}/vhost/nginx/{}.conf'.format(public.get_panel_path(), site_name)
        conf = public.readFile(config_file)
        if not conf:
            return public.returnMsg(False, "nginx配置文件不存在")

        has_rep = re.compile("#SECURITY-HEADERS-START\n(.*\n){4,10}\s*#SECURITY-HEADERS-END")
        res = {
            "x_xss_protection": False,   # 阻止浏览器上下文中执行恶意JavaScript代码
            "x_content_type_options": False,  # 阻止浏览器的内容嗅探
            "referrer_policy": False,  # 让浏览器跳转时不携带referrer
            "content_security_policy": False,  # 让浏览器加载内容时只加载自己网站的内容
            "permissions_policy": False,  # 防止浏览器进行用户行为跟踪
        }
        if not has_rep.search(conf):
            return res

        res_rep_list = {
            "x_xss_protection": re.compile(r"(?P<target># *)?add_header +X-XSS-Protection"),
            "x_content_type_options": re.compile(r"(?P<target># *)?add_header +X-Content-Type-Options"),
            "referrer_policy": re.compile(r"(?P<target># *)?add_header +Referrer-Policy"),
            "content_security_policy": re.compile(r"(?P<target># *)?add_header +Content-Security-Policy"),
            "permissions_policy": re.compile(r"(?P<target># *)?add_header +Permissions-Policy"),
        }
        for k, rep in res_rep_list.items():
            tmp = rep.search(conf)
            if tmp is not None and not tmp.group("target"):
                res[k] = True

        return res

    def set_sites_log_path(self, get):
        try:
            log_path: str = get.log_path.strip()
        except AttributeError:
            return public.returnMsg(False, "参数错误")

        if not os.path.isdir(log_path):
            return public.returnMsg(False, "不是一个存在的文件夹路径")
        if log_path[-1] == "/":
            log_path = log_path[:-1]
        public.writeFile("{}/data/sites_log_path.pl".format(public.get_panel_path()), log_path)

        try:
            res = self.move_logs(get, log_path)
            if res is not None:
                return res
        except:
            public.print_log(public.get_error_info())

        return public.returnMsg(True, "设置成功")

    @staticmethod
    def get_sites_log_path(get=None):
        log_path = public.readFile("{}/data/sites_log_path.pl".format(public.get_panel_path()))
        if isinstance(log_path, str) and os.path.isdir(log_path):
            return log_path
        return public.GetConfigValue('logs_path')

    @staticmethod
    def move_logs(get, log_path: str):
        change_sites = False
        mv_log = False
        try:
            if "change_sites" in get:
                change_sites_str = get.change_sites.strip()
                if change_sites_str in ("yes", "1", "true"):
                    change_sites = True
            if "mv_log" in get:
                mv_log_str = get.mv_log.strip()
                if mv_log_str in ("yes", "1", "true"):
                    mv_log = True
        except:
            pass

        if not change_sites:
            return None

        all_site = public.M("sites").where("project_type=?", ("PHP", )).field("name").select()
        if not isinstance(all_site, list):
            return None

        from logsModel.siteModel import main as log_tool

        logchange = log_tool()

        res = []
        for item in all_site:
            get_obj = public.dict_obj()
            get_obj.log_path = log_path
            get_obj.site_name = item["name"]
            get_obj.mv_log = mv_log
            tmp = logchange.change_site_log_path(get_obj, is_multi=True)
            tmp.update(site_name=item["name"])

            res.append(tmp)
        public.serviceReload()
        return res

    @staticmethod
    def set_dns_domains(get):
        try:
            domains = json.loads(get.domains.strip())
        except AttributeError:
            return public.returnMsg(False, "参数错误")
        domains = [d.split(":")[0] for d in domains]

        server_ip = public.get_server_ip()
        if not isinstance(domains, list) and isinstance(server_ip, str):
            return public.returnMsg(False, "无法添加Dns解析记录，可能是您的ip无法获取")
        res = []
        success = []
        from panelDnsapi import DnsMager

        for domain in domains:
            try:
                dns_obj = DnsMager().get_dns_obj_by_domain(domain)
                dns_obj.add_record_for_creat_site(domain, server_ip)
                success.append(domain)
            except Exception as e:
                res.append({'domain': domain, "error": str(e)})

        res_data = public.returnMsg(True, "")
        res_data["err_list"] = res
        res_data["success_list"] = success
        return res_data

    @staticmethod
    def test_80_port():
        from safeModel.firewallModel import main

        firewall = main()
        rules = firewall.get_sys_firewall_rules()
        for r in rules:
            if r["types"] == "accept" and r["ports"] == "80" and r["protocol"].find("tcp") != -1:
                return
        new_get = public.dict_obj()
        new_get.protocol = "tcp"
        new_get.ports = "80"
        new_get.choose = "all"
        new_get.address = ""
        new_get.domain = ""
        new_get.types = "accept"
        new_get.brief = ""
        new_get.source = ""
        firewall.create_rules(new_get)

    def set_restart_task(self,get):
        import sys
        sys.path.append("..")  # 添加上一级目录到系统路径
        import crontab
        p = crontab.crontab()
        try:
            p = crontab.crontab()
            task_name = '[勿删]Apache守护进程'
            status = get.status
            if public.M('crontab').where('name=?', (task_name,)).count() == 0:
                task = {
                    "name": task_name,
                    "type": "minute-n",
                    "where1": "5",
                    "hour": "1",
                    "minute": "5",
                    "week": "1",
                    "sType": "toShell",
                    "sName": "",
                    "backupTo": "",
                    "save": "",
                    "sBody": "btpython /www/server/panel/script/restart_apache.py ",
                    "urladdress": "",
                    "status": "0",
                    "notice":0,
                }
                res=p.AddCrontab(task)
                if res['status']:
                  return public.returnMsg(True,"设置成功！")
                else:
                  return public.returnMsg(False, res['msg'])
            else:

                return self.set_status(get)
        except Exception as e:
            return public.returnMsg(False, "设置失败" + str(e))
    def set_status(self,get):
        import sys
        sys.path.append("..")  # 添加上一级目录到系统路径
        import crontab
        p = crontab.crontab()
        task_name = '[勿删]Apache守护进程'
        data={"id":public.M('crontab').where("name=?", (task_name,)).getField('id')}
        return p.set_cron_status(public.to_dict_obj(data))

    def get_restart_task(self,get):

        try:

            task_name = '[勿删]Apache守护进程'
            # if public.M('crontab').where('name=?', (task_name,)).count() == 0:
            #     task = {
            #         "name": task_name,
            #         "type": "minute-n",
            #         "where1": "5",
            #         "hour": "1",
            #         "minute": "5",
            #         "week": "1",
            #         "sType": "toShell",
            #         "sName": "",
            #         "backupTo": "",
            #         "save": "",
            #         "sBody": "btpython /www/server/panel/script/restart_apache.py ",
            #         "urladdress": "",
            #         "status": "0",
            #         "notice":0,
            #     }
            #     p.AddCrontab(task)
            #     public.M('crontab').where('name=?', (task_name,)).setField('status', 0)
            crontab_data_list = public.M('crontab').where('name=?', (task_name,)).select()
            if crontab_data_list:
                crontab_data = crontab_data_list[0]
            else:
                crontab_data={"status":0}
            return public.returnMsg(True, crontab_data)
        except Exception as e:
            return public.returnMsg(False, "获取失败" + str(e))

    def get_domains(self, get):
        try:
            if not hasattr(get, "pids"):
                return []
            pids = json.loads(get.pids)
            res = public.M('domain').select()
            res = [i['name'] for i in res if i['pid'] in pids]
            return res
        except:
            return []

    # dns一键解析
    def set_site_dns(self, get):
        from sslModel import dataModel
        dataModel = dataModel.main()
        domains = get.domains.strip().split(',')
        sever_ip = public.get_server_ip()
        data = []
        for domain in domains:
            try:
                dataModel.add_dns_value_by_domain(domain, sever_ip, "A")
                data.append({"domain": domain, "status": True, "msg": "设置成功"})
            except Exception as e:
                data.append({"domain": domain, "status": False, "msg": str(e)})
        return data

    # 遍历目录下的所有文件和目录， 设置文件的权限为644， 目录的权限为755
    @staticmethod
    def _set_web_path_mod(path: str):
        import pwd
        try:
            pwd_user = pwd.getpwnam("www")
        except:
            return
        if not os.path.isdir(path):
            return
        for root, dirs, files in os.walk(path):
            for file in files:
                try:
                    os.chmod(os.path.join(root, file), 0o644)
                    os.chown(os.path.join(root, file), pwd_user.pw_uid, pwd_user.pw_gid)
                except:
                    pass
            for tmp_dir in dirs:
                try:
                    os.chmod(os.path.join(root, tmp_dir), 0o755)
                    os.chown(os.path.join(root, tmp_dir), pwd_user.pw_uid, pwd_user.pw_gid)
                except:
                    pass

    @staticmethod
    def get_cdn_ip_settings(args):
        status = {}
        cdn_ip_conf_file = "{}/vhost/nginx/real_cdn_ip.conf".format(public.get_panel_path())
        if not os.path.exists(cdn_ip_conf_file):
            cdn_ip = False
            status['cdn_recursive'] = False
            status['white_ips'] = "0.0.0.0/0,::/0"
            nginx_path = public.GetConfigValue('setup_path') + '/nginx/conf/nginx.conf'
            config = public.readFile(nginx_path)
            if config:
                if 'real_ip_header' in config and 'set_real_ip_from' in config:
                    cdn_ip = True
            if public.get_webserver() == 'nginx':
                status['cdn_ip'] = cdn_ip
            status["header_cdn"] = "X-Forwarded-For"
        else:
            status['cdn_ip'] = False
            status['cdn_recursive'] = False
            status["header_cdn"] = "X-Forwarded-For"
            status['white_ips'] = "0.0.0.0/0,::/0"
            cdn_ip_conf = public.readFile(cdn_ip_conf_file)
            if cdn_ip_conf:
                status['cdn_ip'] = True
                white_ips = ""
                for line in cdn_ip_conf.split('\n'):
                    dat = line.strip().strip(";")
                    if dat.startswith("set_real_ip_from"):
                        white_ips += dat.split()[1] + ","
                    elif dat.startswith("real_ip_header"):
                        status["header_cdn"] = dat.split()[1]
                    elif dat.startswith("real_ip_recursive"):
                        status['cdn_recursive'] = True
                if white_ips:
                    status['white_ips'] = white_ips.strip(",")
        return  status

    def set_free_total_status(self, get):
        site_id = get.get("site_id/s", "")
        site_status = bool(get.get("status/d", 1))
        set_type = "site"
        if site_id == "global":
            set_type = "global"
        else:
            try:
                site_id = int(site_id)
            except:
                return public.returnMsg(False, "参数错误")
        from mod.base.free_site_total import SiteTotalConfig
        if set_type == "site":
            stc = SiteTotalConfig()
            res = stc.one_site_status(site_id, site_status)
            if res:
                return public.returnMsg(False,
                                        "设置失败，可能无法更新收集服务导致的，请检查网络状态是否可以正常访问到bt.cn")
            return public.returnMsg(True, "设置成功")
        else:
            stc = SiteTotalConfig()
            stc.stop_always(not site_status)
            return public.returnMsg(True, "设置成功")

    def get_free_total_status(self, get):
        from mod.base.free_site_total import SiteTotalConfig
        stc = SiteTotalConfig()
        site_id = get.get("site_id/s", "")
        if site_id != "global":
            try:
                site_id = int(site_id)
            except:
                return public.returnMsg(False, "参数错误")
        conf = stc.get_status()
        if site_id != "global":
            status = True
            for site in conf["sites"]:
                if site["site_id"] == site_id:
                    status = site["is_open"]
        else:
            status = conf["is_open"]
        return {"status": True, "data": {"status": status}, "msg": "获取成功", "code":200}

