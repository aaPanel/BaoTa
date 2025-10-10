# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2017 宝塔软件(http:#bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: sww <sww@bt.cn>
# -------------------------------------------------------------------
# php异步项目部署模块
# ------------------------------
import traceback
import re, os, sys, json, time, hashlib
import shutil

if '/www/server/panel/' not in sys.path:
    sys.path.insert(0, '/www/server/panel/')
from mod.base.web_conf import IpRestrict, remove_sites_service_config
from mod.base.process.process import RealProcess
from mod.base.process.server import RealServer
from mod.base.database_tool import add_database
from mod.base.web_conf import NginxDomainTool, check_domain
from mod.base.web_conf.dir_tool import DirTool
from mod.base.web_conf.proxy import Proxy
from mod.base.backup_tool import VersionTool
from mod.base.web_conf.referer import Referer
from mod.base.web_conf.redirect import Redirect
from mod.base.process.server import syssafe_admin

if '/www/server/panel/class/' not in sys.path:
    sys.path.insert(0, '/www/server/panel/class/')
import public
import tarfile
import psutil

try:
    import zipfile
except:
    public.ExecShell("btpip install zipfile")
    import zipfile
try:
    import gzip
except:
    public.ExecShell("btpip install indexed-gzip")
    import gzip
try:
    import bz2
except:
    public.ExecShell("btpip install bz2file")
    import bz2


class main(IpRestrict, RealProcess, Proxy, Redirect):  # 继承并使用同ip黑白名单限制  SSLManager ssl继承证书管理
    _phpa_path = '/www/server/phpa_project'  #
    _phpa_logs = '{}/logs'.format(_phpa_path)
    setupPath = public.get_setup_path()
    is_ipv6 = os.path.exists(setupPath + '/panel/data/ipv6.pl')
    siteName = None
    sitePath = None
    sitePort = None
    phpVersion = None
    pids = None
    _log_name = '项目管理'
    _php_logs_path = "/www/wwwlogs/php_async"
    __proxyfile = '{}/data/proxyfile.json'.format(public.get_panel_path())
    group_file = "/www/server/panel/data/phpa_project_groups.json"
    
    def __init__(self):
        IpRestrict.__init__(self)
        Proxy.__init__(self)
        RealProcess.__init__(self)
        Redirect.__init__(self)
        if not os.path.exists(self.group_file): public.writeFile(self.group_file, '{}')
    
    def create_project(self, get):
        try:
            public.set_module_logs('phpmod', 'create_phpmod', 1)
            if not hasattr(get, 'webname'):
                return public.returnResult(False, '请输入域名！')
            if not hasattr(get, 'site_path'):
                return public.returnResult(False, '请输入项目路径！')
            if not os.path.exists(get.site_path): public.ExecShell('mkdir -p {}'.format(get.site_path))
            if not hasattr(get, 'project_proxy_path') and hasattr(get, 'open_proxy') and int(get.open_proxy) == 1:
                return public.returnResult(False, '设置反向代理！')
            if not hasattr(get, 'project_port') or get.project_port == '':
                get.project_port = 0
            if not hasattr(get, 'php_version'):
                return public.returnResult(False, '请选择PHP版本！')
            if not hasattr(get, 'project_cmd'):
                return public.returnResult(False, '请输入启动命令！')
            if not hasattr(get, 'is_power_on'):
                get.is_power_on = 1
            if not hasattr(get, 'project_ps'):
                get.project_ps = ''
            if not hasattr(get, 'sql'):
                get.sql = ""
            if not hasattr(get, 'run_user'):
                get.run_user = 'www'
            if not hasattr(get, 'composer_version'):
                get.composer_version = '2.7.3'
            if not os.path.exists('/www/server/phpa_project/logs'):
                public.ExecShell('mkdir -p /www/server/phpa_project/logs')
            public.set_module_logs('php_async', 'create_project', )
            public.ExecShell('chmod -R 777 /www/server/phpa_project/logs')
            # 设置项目目录权限
            public.ExecShell("chown -R {}:{} {}".format(get.run_user.strip(), get.run_user.strip(), get.site_path))
            public.ExecShell("chmod -R 755 {}".format(get.site_path))
            webname = json.loads(get.webname)
            # 域名重复性检查
            domains = [webname['domain']] + webname['domainlist']
            for domain in domains:
                if public.M('sites').where('name=?', (domain.split(':')[0].strip(),)).count():
                    return public.returnResult(False, '指定域名已存在: {}'.format(domain))
            
            # 域名存在检查
            get.project_cmd = get.project_cmd.strip()
            
            # 创建项目
            if public.M('sites').where('name=?', (webname['domain'].split(':')[0].strip(),)).count():
                return public.returnResult(False, '指定项目已存在: {}'.format(webname))
            
            self.siteName = self.ToPunycode(webname['domain'].split(':')[0].strip())
            self.sitePath = self.ToPunycodePath(get.site_path)
            self.sitePort = 80 if ':' not in webname['domain'] else webname['domain'].split(':')[1].strip()
            self.phpVersion = get.php_version
            # 添加nginx网站配置文件
            self.nginxAdd()
            # 添加多余的域名
            domainlist = []
            for domain in domains:
                domainname = domain.split(':')[0].strip()
                domainport = '80' if ':' not in domain else domain.split(':')[1].strip()
                domainlist.append((domainname, domainport))
            if len(domainlist) > 1:
                NginxDomainTool().nginx_set_domain(self.siteName, *domainlist)
                # 创建默认文档
            if not os.path.exists('{}/index.ttml'.format(self.sitePath)):
                connect = """
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>恭喜，异步项目创建成功！</title>
    <style>
        .container {
            width: 60%;
            margin: 10% auto 0;
            background-color: #f0f0f0;
            padding: 2% 5%;
            border-radius: 10px
        }

        ul {
            padding-left: 20px;
        }

            ul li {
                line-height: 2.3
            }

        a {
            color: #20a53a
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>恭喜，异步项目创建成功！</h1>
        <h3>这是默认index.html，本页面由系统自动生成</h3>
        <ul>
            <li>本页面在项目目录下的index.html</li>
            <li>您可以修改、删除或覆盖本页面</li>
            <li>您可以将web目录修改为您的前端文件所在目录</li>
            <li>您也可以将后端直接反代到此域名</li>
        </ul>
    </div>
</body>
                    """
                public.writeFile('{}/index.html'.format(self.sitePath), connect)
            # 添加反向代理
            if hasattr(get, 'open_proxy') and int(get.open_proxy) == 1:
                args = {
                    "proxyname": self.siteName,
                    "sitename": self.siteName,
                    "proxydir": get.project_proxy_path,
                    "proxysite": "http://127.0.0.1:{}".format(get.project_port),
                    "todomain": "$host",
                    "type": "1",
                    "cache": "1",
                    "subfilter": '[{"sub1":"","sub2":""},{"sub1":"","sub2":""},{"sub1":"","sub2":""}]',
                    "advanced": "1",
                    "cachetime": "1",
                }
                
                self.create_proxy(public.to_dict_obj(args))
            # 修改启动命令
            start_cmd = get.project_cmd
            if 'php' == get.project_cmd[:3]:
                get.project_cmd = '/www/server/php/{}/bin/php -c {}/php-cli.ini {}'.format(get.php_version, get.site_path, get.project_cmd[3:])
            else:
                get.project_cmd = '/www/server/php/{}/bin/php -c {}/php-cli.ini {}'.format(get.php_version, get.site_path, get.project_cmd)
            is_fork = 0
            if ' -d' in get.project_cmd:
                is_fork = 1
            # 创建服务 并设置开机启动
            realserver = RealServer()
            
            realserver.create_daemon(self.siteName, '', get.project_cmd, get.site_path, '',get.run_user.strip(), get.is_power_on, logs_file=os.path.join(self._phpa_logs, self.siteName + '.log'),
                                     is_fork=is_fork,fork_time_out=0.2)
            # 安装依赖
            dependence = 0
            if hasattr(get, 'install_dependence') and get.install_dependence == "1":
                public.run_thread(self.install_dependence, (self.siteName, get.php_version, get.site_path, get.composer_version))
                dependence = 1
            else:
                public.ExecShell('cp /www/server/php/{}/etc/php-cli.ini {}/'.format(get.php_version, get.site_path))
                public.ExecShell("sed -i '/disable_functions/d' {}".format(os.path.join(get.site_path, 'php-cli.ini')))
                public.ExecShell("chown root:root {}".format(os.path.join(get.site_path, 'php-cli.ini')))
                public.ExecShell("chomd 644 {}".format(os.path.join(get.site_path, 'php-cli.ini')))
            # 写入数据库
            pdata = {
                'name': self.siteName,
                'path': get.site_path,
                'ps': get.project_ps,
                'status': 1,
                'type_id': 0,
                'project_type': 'PHP',
                'project_config': json.dumps(
                    {
                        'ssl_path': '/www/wwwroot/phpa_ssl',
                        'sitename': self.siteName,
                        'domains': [webname['domain']] + webname['domainlist'],
                        'project_path': get.site_path,
                        'project_cmd': get.project_cmd,
                        'is_power_on': get.is_power_on,
                        'port': int(get.project_port),
                        'log_path': self._log_name,
                        'php_version': get.php_version,
                        'dependence': dependence,
                        'start_cmd': start_cmd,
                        'project_port': get.project_port,
                        'type': 'PHPMOD',
                        'run_user': get.run_user.strip(),
                    }
                ),
                'addtime': public.getDate()
            }
            pid = public.M('sites').insert(pdata)
            for domain in domains:
                domain_arr = domain.split(':')
                if len(domain_arr) == 1:
                    domain_arr.append(80)
                domain_arr[0] = self.ToPunycode(domain_arr[0].strip())
                public.M('domain').add('pid,name,port,addtime', (pid, domain_arr[0], domain_arr[1], public.getDate()))
            
            # 检查是否创建数据库
            if get.sql == "MYSQL":
                if not (hasattr(get, 'sql_user') or hasattr(get, 'sql_pwd') or hasattr(get, 'sql_codeing')):
                    return public.returnResult(False, '请填写数据库信息')
                mysql_data = {
                    "server_id": 0,
                    "database_name": get.sql_user,
                    "db_user": get.sql_user,
                    "password": get.sql_pwd,
                    "dataAccess": "ip",
                    "address": "127.0.0.1",
                    "codeing": get.sql_codeing,
                    "ps": get.project_ps,
                    "listen_ip": "0.0.0.0/0",
                    "host": "",
                    "pid": pid,
                }
                add_database(db_type="mysql", data=mysql_data)
            
            # self.modify_project_run_state(public.to_dict_obj({'sitename': self.siteName, 'project_action': 'start'}))
            # 写日志
            public.WriteLog(self._log_name, '添加PHP动态项目{}'.format(webname))
            return {'status': True, 'msg': '添加成功！','databaseUser': get.sql_user, 'databasePass': get.sql_pwd,'databaseStatus': True}
        except:
            return public.returnResult(False, str(traceback.format_exc()))
    
    def re_install_dependence(self, get):
        if not hasattr(get, 'id'):
            return public.returnResult(False, '参数缺失：ids！')
        project_config = public.M('sites').where('id=?', (get.id,)).select()[0]
        project_config = json.loads(project_config['project_config'])
        if os.path.exists('/tmp/php_mod_{}.pl'.format(project_config['name'])) and int(project_config['dependence']) == 1:
            pid = public.readFile('/tmp/php_mod_{}.pl'.format(project_config['name']))
            try:
                import psutil
                p = psutil.Process(int(pid))
                if p.name() == 'BT-Panel' or p.name() == 'btpython':
                    return public.returnResult(False, '正在安装中请稍后重试！')
            except:
                pass
        public.run_thread(self.install_dependence, (project_config['name'], project_config['php_version'], project_config['path']))
        return public.returnResult(True, '正在安装依赖！')
    
    def check_install(self, get):
        if not hasattr(get, 'name'):
            return public.returnResult(False, '参数缺失：name！')
        if not hasattr(get, 'php_version'):
            return public.returnResult(False, '参数缺失：php_version！')
        if get.name == 'swoole':
            res = public.ExecShell("/www/server/php/{}/bin/php --ri {}|grep Version|awk '{{print $3}}'".format(get.php_version, get.name))
            if res[0] != '':
                return public.returnResult(True, res[0].strip())
            return public.returnResult(False, '未安装！请前往PHP-安装扩展中安装{}！'.format(get.name))
        if get.name == 'fileinfo':
            res = public.ExecShell("/www/server/php/{}/bin/php --ri {}".format(get.php_version, get.name))
            if res[0] != '' and 'fileinfo' in res[0] and 'enabled' in res[0]:
                return public.returnResult(True, '已安装！')
            return public.returnResult(False, '未安装！请前往PHP-安装扩展中安装{}！'.format(get.name))
    
    def print_log(self, path, log):
        public.writeFile(path, log, 'a+')
    
    def check_auto_install(self, get):
        if not hasattr(get, 'path'):
            return public.returnResult(False, '参数缺失：path！')
        if not os.path.exists("{}/composer.json".format(get.path)):
            return False
        if not os.path.exists('{}/composer.lock'.format(get.path)) or not os.path.exists('{}/vendor'.format(get.path)):
            return True
        return False
    
    def get_swoole_correspondence_php(self, get):
        if not hasattr(get, 'swoole_version') and get.swoole_version.strip() in ['2', '4', '5']:
            return public.returnResult(False, '参数缺失：swoole_version！')
        swoole_version = get.swoole_version.strip()
        php_correspondence = {
            '2': ['52', '53', '54', '55', '70', '71', '72'],
            '4': ['72', '73', '74', '80', '81', '82'],
            '5': ['80', '81', '82', '83'],
        }
        php_list = php_correspondence[swoole_version]
        result = []
        for php in php_list:
            setup_status = os.path.exists('/www/server/php/{}/bin/php'.format(php))
            c_ini = '/www/server/php/{}/etc/php.ini'.format(php)
            res, err_str = public.ExecShell("/www/server/php/{}/bin/php -c {} --ri swoole|grep Version|awk '{{print $3}}'".format(php, c_ini))
            swoole_status = True if res != '' else False
            swoole_version = res.strip()
            result.append({
                'php_version': php,
                'setup_status': setup_status,
                'swoole_status': swoole_status,
                'swoole_version': swoole_version,
                'setup_swoole_isactive': True if swoole_version != '' and swoole_version[0] == get.swoole_version else False
            })
        return public.returnResult(True, data=result, msg='获取成功！')
    
    @syssafe_admin
    def install_composer(self, composer_version, logs_path):
        composer_name = '/usr/bin/composer{}'.format(('_' + composer_version.replace('.', '_')) if composer_version != '' else '')
        if not os.path.exists(composer_name) and composer_version != '':
            url = public.get_url() + '/src/compose/composer_{}'.format(composer_version.replace('.', '_'))
            public.ExecShell('wget -O {} {} &> {}'.format(composer_name, url, logs_path))
            if os.path.exists(composer_name):
                public.ExecShell('chmod +x {}'.format(composer_name))
                public.ExecShell('echo "{}" >> {}'.format('composer{}下载成功！'.format(composer_version), logs_path))
    
    def install_dependence(self, webname, php_version, site_path, composer_version='2.7.3'):
        logs_path = '/tmp/{}_install_dependence.log'.format(webname)
        
        # 检查锁和所文件
        if os.path.exists('{}/composer.lock'.format(site_path)):
            if os.path.exists('{}/vendor'.format(site_path)):
                public.ExecShell('echo "{}" >> {}'.format('composer.lock和vendor目录存在，不需要安装依赖！', logs_path))
                try:
                    project_list = public.M('sites').where('project_type=? and name=?', ('PHP', webname)).field('project_config').select()[0]
                    project_config = json.loads(project_list['project_config'])
                    project_config['dependence'] = 0
                    public.M('sites').where('project_type=? and name=?', ('PHP', webname)).setField('project_config', json.dumps(project_config))
                except:
                    pass
                if not os.path.exists('/www/server/phpa_project/logs'):
                    public.ExecShell('mkdir -p /www/server/phpa_project/logs')
                public.ExecShell('chmod -R 755 /www/server/phpa_project/logs')
                RealServer().daemon_admin(str(webname), 'start')
                return
            else:
                public.ExecShell('echo "{}" >> {}'.format('composer.lock存在，但vendor目录不存在，开始安装依赖！', logs_path))
        else:
            public.ExecShell('echo "{}" > {}'.format('composer.lock不存在，开始安装依赖！', logs_path))
        self.install_composer(composer_version, logs_path)
        public.writeFile('/tmp/php_mod_{}.pl'.format(webname), str(os.getpid()))
        public.ExecShell('cp /www/server/php/{}/etc/php-cli.ini {}/'.format(php_version, site_path))
        public.ExecShell("sed -i '/disable_functions/d' {}".format(os.path.join(site_path, 'php-cli.ini')))
        # 尝试安装composer中的依赖
        self.print_log(logs_path, '开始安装composer依赖！\n')

        composer_env = os.environ.copy()
        if "HOME" not in composer_env and "COMPOSER_HOME" not in composer_env:
            composer_env["HOME"] = "/root" if not os.path.exists("/home/www") else "/home/www"
        public.ExecShell(
            'cd {} && export COMPOSER_ALLOW_SUPERUSER=1 && '
            '/www/server/php/{}/bin/php -c {} /usr/bin/composer{} install --no-interaction &>> {}'.format(
                site_path, php_version, os.path.join(site_path, 'php-cli.ini'),
                '_' + composer_version.replace('.','_') if composer_version != '' else '', logs_path),
            env=composer_env)

        # 查看安装依赖报错
        logs = public.readFile(logs_path)
        if "No composer.lock file present. Updating dependencies to latest instead of installing from lock file" in logs and not os.path.exists('{}/composer.lock'.format(site_path)):
            self.print_log(logs_path, '\ncomposer.lock文件不存在,安装依赖时需要使用此文件,请前往项目官网下载composer.lock文件放入{}目录后前往<compsoer页面>重新安装依赖！'.format(site_path))
        public.ExecShell('cp /www/server/php/{}/etc/php-cli.ini {} >> {}'.format(php_version, site_path, logs_path))
        public.ExecShell("sed -i '/disable_functions/d' {}".format(os.path.join(site_path, 'php-cli.ini')))
        public.ExecShell("chown root:root {}".format(os.path.join(site_path, 'php-cli.ini')))
        public.ExecShell("chomd 644 {}".format(os.path.join(site_path, 'php-cli.ini')))
        self.print_log(logs_path, '安装依赖结束！')
        try:
            project_list = public.M('sites').where('project_type=? and name=?', ('PHP', webname)).field('project_config').select()[0]
            project_config = json.loads(project_list['project_config'])
            project_config['dependence'] = 0
            public.M('sites').where('project_type=? and name=?', ('PHP', webname)).setField('project_config', json.dumps(project_config))
        except:
            pass
        if not os.path.exists('/www/server/phpa_project/logs'):
            public.ExecShell('mkdir -p /www/server/phpa_project/logs')
        public.ExecShell('chmod -R 755 /www/server/phpa_project/logs')
        self.modify_project_run_state(public.to_dict_obj({'sitename': webname, 'project_action': 'start'}))
    
    def check_development_setup(self, php_version, name):
        try:
            # /ajax?action=GetPHPConfig
            import ajax
            a = ajax.ajax()
            get = public.to_dict_obj({})
            get.version = php_version
            res = a.GetPHPConfig(get)
            for i in res['libs']:
                if i['name'] == name and i['status'] == True:
                    return True
            return False
        except:
            return False
    
    # 域名编码转换
    def ToPunycode(self, domain):
        import re
        if sys.version_info[0] == 2: domain = domain.encode('utf8')
        tmp = domain.split('.')
        newdomain = ''
        for dkey in tmp:
            if dkey == '*': continue
            # 匹配非ascii字符
            match = re.search(u"[\x80-\xff]+", dkey)
            if not match: match = re.search(u"[\u4e00-\u9fa5]+", dkey)
            if not match:
                newdomain += dkey + '.'
            else:
                if sys.version_info[0] == 2:
                    newdomain += 'xn--' + dkey.decode('utf-8').encode('punycode') + '.'
                else:
                    newdomain += 'xn--' + dkey.encode('punycode').decode('utf-8') + '.'
        if tmp[0] == '*': newdomain = "*." + newdomain
        return newdomain[0:-1]
    
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
    
    # 添加到nginx
    def nginxAdd(self):
        if not os.path.exists('/www/server/panel/class/404_settings.json'):
            public.writeFile('/www/server/panel/class/404_settings.json', json.dumps({}))
        
        template = None
        use_template = public.readFile("{}/data/use_nginx_template.pl".format(public.get_panel_path()))
        if isinstance(use_template, str):
            template_file = "{}/data/nginx_template/{}".format(public.get_panel_path(), use_template)
            if os.path.isfile(template_file):
                template = public.readFile(template_file)
        
        with open('/www/server/panel/class/404_settings.json', 'r') as f:
            settings = json.load(f)
        status = settings.get('status', "0")
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
        filename = self.setupPath + '/panel/vhost/nginx/' + self.siteName + '.conf'
        if template_conf is not None:
            public.writeFile(filename, template_conf)
        else:
            public.writeFile(filename, conf)
        
        # 生成伪静态文件
        urlrewritePath = self.setupPath + '/panel/vhost/rewrite'
        urlrewriteFile = urlrewritePath + '/' + self.siteName + '.conf'
        if not os.path.exists(urlrewritePath): os.makedirs(urlrewritePath)
        open(urlrewriteFile, 'w+').close()
        if not os.path.exists(urlrewritePath):
            public.writeFile(urlrewritePath, '')
        
        return True
    
    # 删除站点
    def DeleteSite(self, get, multiple=None):
        try:
            proxyconf = [] if not os.path.exists(self.__proxyfile) else json.loads(public.readFile(self.__proxyfile))
            id = get.id
            if public.M('sites').where('id=?', (id,)).count() < 1: return public.returnResult(False, '指定站点不存在!')
            siteName = get.webname
            get.siteName = siteName
            # 删除反向代理
            for i in range(len(proxyconf) - 1, -1, -1):
                if proxyconf[i]["sitename"] == siteName:
                    del proxyconf[i]
            public.writeFile(self.__proxyfile, json.dumps(proxyconf))
            m_path = self.setupPath + '/panel/vhost/nginx/proxy/' + siteName
            if os.path.exists(m_path): public.ExecShell("rm -rf %s" % m_path)
            
            # 删除目录保护
            _dir_aith_file = "%s/panel/data/site_dir_auth.json" % self.setupPath
            _dir_aith_conf = public.readFile(_dir_aith_file)
            # 删除保护目录
            if _dir_aith_conf:
                try:
                    _dir_aith_conf = json.loads(_dir_aith_conf)
                    if siteName in _dir_aith_conf:
                        del (_dir_aith_conf[siteName])
                except:
                    pass
            public.writeFile(_dir_aith_file, _dir_aith_conf)
            dir_aith_path = self.setupPath + '/panel/vhost/nginx/dir_auth/' + siteName
            if os.path.exists(dir_aith_path): public.ExecShell("rm -rf %s" % dir_aith_path)
            
            # 删除重定向
            __redirectfile = "%s/panel/data/redirect.conf" % self.setupPath
            redirectconf = [] if not os.path.exists(__redirectfile) else json.loads(public.readFile(__redirectfile))
            for i in range(len(redirectconf) - 1, -1, -1):
                if redirectconf[i]["sitename"] == siteName:
                    del redirectconf[i]
            public.writeFile(__redirectfile, json.dumps(redirectconf))
            m_path = self.setupPath + '/panel/vhost/nginx/redirect/' + siteName
            if os.path.exists(m_path): public.ExecShell("rm -rf %s" % m_path)
            
            # 删除配置文件
            confPath = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
            if os.path.exists(confPath): os.remove(confPath)
            
            # 删除伪静态文件
            filename = '/www/server/panel/vhost/rewrite/' + siteName + '.conf'
            if os.path.exists(filename):
                os.remove(filename)
                public.ExecShell("rm -f " + confPath + '/rewrite/' + siteName + "_*")
            
            # 删除日志文件
            filename = public.GetConfigValue('logs_path') + '/' + siteName + '*'
            public.ExecShell("rm -f " + filename)
            
            # 重载服务
            public.serviceReload()
            
            # 从数据库删除
            public.M('sites').where("id=?", (id,)).delete()
            public.M('binding').where("pid=?", (id,)).delete()
            public.M('domain').where("pid=?", (id,)).delete()
            public.WriteLog('TYPE_SITE', "SITE_DEL_SUCCESS", (siteName,))
            
            # 是否删除关联数据库
            if hasattr(get, 'database'):
                if get.database == '1':
                    find = public.M('databases').where("pid=?", (id,)).field('id,name').find()
                    if find:
                        import database
                        get.name = find['name']
                        get.id = find['id']
                        database.database().DeleteDatabase(get)
            
            # 是否删除关联FTP
            if hasattr(get, 'ftp'):
                if get.ftp == '1':
                    find = public.M('ftps').where("pid=?", (id,)).field('id,name').find()
                    if find:
                        import ftp
                        get.username = find['name']
                        get.id = find['id']
                        ftp.ftp().DeleteUser(get)
            try:
                # 删除项目
                Redirect().remove_redirect_by_project_name(siteName)
            except:
                pass
            RealServer().del_daemon(siteName)
            remove_sites_service_config(siteName)
            return public.returnResult(True, '删除成功')
        except:
            return public.returnResult(False, traceback.format_exc())
    
    def get_sites_log_path(get=None):
        log_path = public.readFile("{}/data/sites_log_path.pl".format(public.get_panel_path()))
        if isinstance(log_path, str) and os.path.isdir(log_path):
            return log_path
        return public.GetConfigValue('logs_path')
    
    # 检查端口是否被占用
    def check_port_is_used(self, port, sock=False):
        '''
            @name 检查端口是否被占用
            @author sww
            @param port: int<端口>
            @return bool
        '''
        if not isinstance(port, int): port = int(port)
        if port == 0: return False
        project_list = public.M('sites').where('status=? AND project_type=?', (1, 'PHP')).field(
            'name,path,project_config').select()
        for project_find in project_list:
            project_config = json.loads(project_find['project_config'])
            if not 'port' in project_config: continue
            try:
                if int(project_config['port']) == port:
                    return True
            except:
                continue
        if sock: return False
        return public.check_tcp('127.0.0.1', port)
    
    # 获取项目列表
    def get_project_list(self, get):
        '''
            @name 获取项目列表
            @author sww
            @param get<dict_obj>{
                sitename: string<项目名称>
            }
            @return dict
        '''
        try:
            if not 'p' in get:  get.p = 1
            if not 'limit' in get: get.limit = 20
            if not 'callback' in get: get.callback = ''
            if not 'order' in get: get.order = 'id desc'
            type_id = None
            if "type_id" in get:
                try:
                    type_id = int(get.type_id)
                except:
                    type_id = None
            
            if 'search' in get:
                get.sitename = get.search.strip()
                search = "%{}%".format(get.sitename)
                if type_id is None:
                    count = public.M('sites').where('project_type=? AND (name LIKE ? OR ps LIKE ?)', ('PHP', search, search)).count()
                    data = public.get_page(count, int(get.p), int(get.limit), get.callback)
                    data['data'] = public.M('sites').where('project_type=? AND (name LIKE ? OR ps LIKE ?)', ('PHP', search, search)).limit(data['shift'] + ',' + data['row']).order(get.order).select()
                else:
                    count = public.M('sites').where('project_type=? AND (name LIKE ? OR ps LIKE ?) AND type_id = ?',
                                                    ('PHP', search, search, type_id)).count()
                    data = public.get_page(count, int(get.p), int(get.limit), get.callback)
                    data['data'] = public.M('sites').where('project_type=? AND (name LIKE ? OR ps LIKE ?) AND type_id = ?', ('PHP', search, search, type_id)).limit(
                        data['shift'] + ',' + data['row']).order(get.order).select()
            else:
                if type_id is None:
                    count = public.M('sites').where('project_type=?', 'PHP').count()
                    data = public.get_page(count, int(get.p), int(get.limit), get.callback)
                    data['data'] = public.M('sites').where('project_type=?', 'PHP').limit(data['shift'] + ',' + data['row']).order(get.order).select()
                else:
                    count = public.M('sites').where('project_type=? AND type_id = ?', ('PHP', type_id)).count()
                    data = public.get_page(count, int(get.p), int(get.limit), get.callback)
                    data['data'] = public.M('sites').where('project_type=? AND type_id = ?', ('PHP', type_id)).limit(data['shift'] + ',' + data['row']).order(get.order).select()
            
            for i in range(len(data['data'])):
                data['data'][i] = self.get_project_stat(data['data'][i])
                logs_path = '/tmp/{}_install_dependence.log'.format(data['data'][i]['name'])
                if not os.path.exists(logs_path) or int(os.path.getmtime(logs_path)) - int(time.time()) > 20:
                    data['data'][i]['dependence'] = 0
            return public.returnResult(True, data=data)
        except:
            return public.returnResult(False, '获取项目列表失败')
    
    # 获取项目状态信息
    def get_project_stat(self, project_info):
        '''
            @name 获取项目状态信息
            @author sww
            @param project_info<dict> 项目信息
            @return list
        '''
        project_info['project_config'] = json.loads(project_info['project_config'])
        # project_info['project_config']['bind_extranet'] = int(project_info['project_config']['bind_extranet'])
        # project_info['run'] = self.get_project_run_state(sitename=project_info['name'])
        # project_info['load_info'] = self.get_project_load_info(sitename=project_info['name'])
        project_info['run'] = RealServer().daemon_status(project_info['name'])['status']
        project_info['ssl'] = self.get_ssl_end_date(sitename=project_info['name'])
        project_info['listen'] = []
        project_info['listen_ok'] = True
        # if project_info['load_info']:
        #     for pid in project_info['load_info'].keys():
        #         if not 'connections' in project_info['load_info'][pid]:
        #             project_info['load_info'][pid]['connections'] = []
        #         if 'connections' in project_info['load_info'][pid]:
        #             for conn in project_info['load_info'][pid]['connections']:
        #                 if not conn['status'] == 'LISTEN': continue
        #                 if not conn['local_port'] in project_info['listen']:
        #                     project_info['listen'].append(conn['local_port'])
        #     if project_info['listen']:
        #         project_info['listen_ok'] = project_info['project_config']['port'] in project_info['listen']
        return project_info
    
    # 获取指定项目的域名列表
    def project_get_domain(self, get):
        '''
            @name 获取指定项目的域名列表
            @author sww
            @param get<dict_obj>{
                sitename: string<项目名称>
            }
            @return dict
        '''
        try:
            project_id = public.M('sites').where('name=?', (get.sitename,)).getField('id')
            domains = public.M('domain').where('pid=?', (project_id,)).order('id desc').select()
            # project_find = self.get_project_find(get.sitename)
            # if len(domains) != len(project_find['project_config']['domains']):
            #     public.M('domain').where('pid=?', (project_id,)).delete()
            #     if not project_find: return []
            #     for d in project_find['project_config']['domains']:
            #         domain = {}
            #         arr = d.split(':')
            #         if len(arr) < 2: arr.append(80)
            #         domain['name'] = arr[0]
            #         domain['port'] = int(arr[1])
            #         domain['pid'] = project_id
            #         domain['addtime'] = public.getDate()
            #         public.M('domain').insert(domain)
            #     if project_find['project_config']['domains']:
            #         domains = public.M('domain').where('pid=?', (project_id,)).select()
            return public.returnResult(True, data=domains)
        except:
            return public.returnResult(False, traceback.format_exc())
    
    # 获取指定项目配置
    def get_project_find(self, sitename):
        '''
            @name 获取指定项目配置
            @author sww
            @param sitename<string> 项目名称
            @return dict
        '''
        project_info = public.M('sites').where('project_type=? AND name=?', ('PHP', sitename)).find()
        if not project_info: return False
        project_info['project_config'] = json.loads(project_info['project_config'])
        if 'run_user' not in project_info['project_config'].keys():
            project_info['run_user'] = 'www'
        return project_info
    
    # 获取项目SSL信息
    def get_ssl_end_date(self, sitename):
        '''
            @name 获取SSL信息
            @author sww
            @param sitename <string> 项目名称
            @return dict
        '''
        import data
        return data.data().get_site_ssl_info(sitename)
    
    # 删除指定项目中的域名
    def project_remove_domain(self, get):
        '''
            @name 为指定项目删除域名
            @author sww
            @param get<dict_obj>{
                sitename: string<项目名称>
                domain: string<域名>
            }
            @return dict
        '''
        try:
            project_find = self.get_project_find(get.sitename)
            if not project_find:
                return public.returnResult(False, '指定项目不存在')
            result = []
            domain_id_list = json.loads(get.domain)
            remove_list = []
            project_id = public.M('sites').where('name=?', (get.sitename,)).getField('id')
            for domain_id in domain_id_list:
                domain_info = public.M('domain').where('id=?', (domain_id,)).find()
                if not domain_info:
                    return public.returnResult(False, '指定域名不存在')

                if public.M('domain').where('pid=?', (project_id,)).count() == 1:
                    result.append({'domain_id': domain_id, 'name': domain_info["name"], 'msg': "项目中至少需要一个域名", "status": False})
                    continue
                remove_list.append(domain_info["name"])
                public.M('domain').where('id=?', (domain_id,)).delete()
                public.WriteLog(self._log_name, '从项目：{}，删除域名{}'.format(get.sitename, str(remove_list)))
                result.append({'domain_id': domain_id, 'name': domain_info["name"], 'msg': "删除成功", "status": True})
            domain_list = public.M('domain').where('pid=?', (project_id,)).select()
            domain_list = [(domain['name'], str(domain['port'])) for domain in domain_list]
            NginxDomainTool().nginx_set_domain(get.sitename, *domain_list)
            return public.returnResult(True, data=result)
        except:
            return public.returnResult(False, traceback.format_exc())
    
    # 为指定项目添加域名
    def project_add_domain(self, get):
        '''
            @name 为指定项目添加域名
            @author sww
            @param get<dict_obj>{
                sitename: string<项目名称>
                domains: list<域名列表>
            }
            @return dict
        '''
        try:
            project_find = self.get_project_find(get.sitename)
            if not project_find:
                return public.returnResult(False, '指定项目不存在')
            project_id = project_find['id']
            domains = get.domains
            if not isinstance(domains, list):
                domains = json.loads(domains)
            flag = False
            res_domains = []
            for domain in domains:
                domain = domain.strip()
                if not domain: continue
                if not self.check_domain(domain.split(':')[0]):
                    res_domains.append({"name": domain, "status": False, "msg": '域名格式错误'})
                    continue
                domain_arr = domain.split(':')
                domain_arr[0] = self.ToPunycode(domain_arr[0])
                if domain_arr[0] is False:
                    res_domains.append({"name": domain, "status": False, "msg": '域名格式错误'})
                    continue
                if len(domain_arr) == 1:
                    domain_arr.append("")
                if domain_arr[1] == "":
                    domain_arr[1] = 80
                    domain += ':80'
                try:
                    if not (0 < int(domain_arr[1]) < 65535):
                        res_domains.append({"name": domain, "status": False, "msg": '域名格式错误'})
                        continue
                except ValueError:
                    res_domains.append({"name": domain, "status": False, "msg": '域名格式错误'})
                    continue
                if not public.M('domain').where('name=?', (domain_arr[0],)).count():
                    public.M('domain').add('name,pid,port,addtime',
                                           (domain_arr[0], project_id, domain_arr[1], public.getDate()))
                    if not domain in project_find['project_config']['domains']:
                        project_find['project_config']['domains'].append(domain)
                    public.WriteLog(self._log_name, '成功添加域名{}到项目{}'.format(domain, get.sitename))
                    res_domains.append({"name": domain_arr[0], "status": True, "msg": '添加成功'})
                    flag = True
                else:
                    public.WriteLog(self._log_name, '添加域名错误，域名{}已存在'.format(domain))
                    res_domains.append({"name": domain_arr[0], "status": False, "msg": '添加失败，域名{}已存在'.format(domain)})
            if flag:
                public.M('sites').where('id=?', (project_id,)).save('project_config', json.dumps(project_find['project_config']))
                domain_list = public.M('domain').where('pid=?', (project_id)).select()
                domain_list = [(domain['name'], str(domain['port'])) for domain in domain_list]
                NginxDomainTool().nginx_set_domain(get.sitename, *domain_list)
            return self._ckeck_add_domain(get.sitename, res_domains)
        except:
            return public.returnResult(False, traceback.format_exc())
    
    def _ckeck_add_domain(self, site_name, domains):
        from panelSite import panelSite
        ssl_data = panelSite().GetSSL(type("get", tuple(), {"siteName": site_name})())
        if not ssl_data["status"]: return public.returnResult(True, data={"domains": domains}, msg="添加成功")
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
            return public.returnResult(True, data={
                "domains": domains,
                "not_ssl": no_ssl,
                "tip": "本站点已启用SSL证书,但本次添加的域名：{}，无法匹配当前证书，如有需求，请重新申请证书。".format(str(no_ssl))
            }, msg="添加成功")
        return public.returnResult(True, data={"domains": domains}, msg="添加成功")
    
    # 获取项目状态
    def get_project_run_state(self, get):
        '''
            @name 获取项目运行状态信息
            @param sitename<string> 项目名称
            @return dict
        '''
        try:
            sitename = get.sitename.strip()
            result = {}
            project_info = self.get_project_find(sitename)
            res = RealServer().daemon_status(sitename)
            result['status'] = res['status']
            result['sitename'] = sitename
            result['is_power_on'] = int(project_info["project_config"]['is_power_on'])
            result['project_path'] = project_info['path']  # type : str
            result['project_cmd'] = project_info["project_config"].get('start_cmd', '')
            result['project_port'] = project_info['project_config']['port']
            if result['project_path'][-1] != "/":
                result['project_path'] += "/"
            result['site_run_path'] = DirTool().get_site_run_path(sitename).replace(result['project_path'].rstrip("/"), "")
            if not result['site_run_path']:
                result['site_run_path'] = "/"
            result['php_version'] = project_info['project_config']['php_version']
            result['run_user'] = project_info['project_config'].get('run_user', 'www')
            result['ps'] = project_info['ps']
            result['pid'] = RealServer().get_daemon_pid(sitename)["data"]
            if result['pid'] in [0, '0', ''] and result['status']:
                res = public.ExecShell("""ps -aux |grep "{}"|grep -v "grep"|awk '{{print $2}}'""".format(result['project_cmd']))[0]
                res = res.strip().split("\n")
                if res and len(res) >= 1:
                    res.sort()
                    result['pid'] = res[0]
            result['Listen'] = []
            if result['pid']:
                children = RealProcess().get_process_tree(result['pid'])["data"]
                for chi in children:
                    for i in chi.get("connections", []):
                        port = i.get("local_port", '')
                        addr = i.get("local_addr", '')
                        status = i.get("status", 'dasd')
                        if addr == '0.0.0.0':
                            addr = public.GetLocalIp()
                        if port and addr and status.lower() == 'listen':
                            result['Listen'].append((addr, port))
            result['Listen'] = list(set(result['Listen']))
            
            return public.returnResult(True, data=result)
        except:
            public.print_log(traceback.format_exc())
            return public.returnResult(False, '获取项目状态失败')
    
    def domain_to_puny_code(self, domain: str) -> str:
        new_domain = ''
        for dkey in domain.split('.'):
            if dkey == '*' or dkey == "":
                continue
            # 匹配非ascii字符
            match = re.search(u"[\x80-\xff]+", dkey)
            if not match:
                match = re.search(u"[\u4e00-\u9fa5]+", dkey)
            if not match:
                new_domain += dkey + '.'
            else:
                new_domain += 'xn--' + dkey.encode('punycode').decode('utf-8') + '.'
        if domain.startswith('*.'):
            new_domain = "*." + new_domain
        return new_domain[:-1]
    
    def check_domain(self, domain: str):
        domain = self.domain_to_puny_code(domain)
        # 判断通配符域名格式
        if domain.find('*') != -1 and domain.find('*.') == -1:
            return None
        
        # 判断域名格式
        rep_domain = re.compile(r"^([\w\-*]{1,100}\.){1,24}([\w\-]{1,24}|[\w\-]{1,24}\.[\w\-]{1,24})$")
        if not rep_domain.match(domain):
            return None
        return domain
    
    # 修改项目运行状态
    def modify_project_run_state(self, get):
        sitename = get.sitename
        project_action = get.project_action
        logs_path = "/www/server/phpa_project/logs"
        if not os.path.exists(logs_path):
            public.ExecShell('mkdir -p {}'.format(logs_path))
        public.ExecShell('chmod 777 -R {}'.format(logs_path))
        if project_action in ['start', 'restart']:
            self.async_dependence_config(sitename)
        res = RealServer().daemon_admin(sitename, project_action)
        if res['status'] and project_action in ['start', 'restart']:
            public.M('sites').where('name=? and project_type=?', (sitename, 'PHP')).setField('status', 1)
        elif res['status'] or project_action == 'stop':
            public.M('sites').where('name=? and project_type=?', (sitename, 'PHP')).setField('status', 0)
        if project_action in ['start', 'restart']:
            # num = 0
            # for i in range(20):
            #
            #     if conn['status']:num += 1
            #     if num >3:
            #         return public.returnResult(False, '启动失败')
            time.sleep(0.1)
            conn = RealServer().daemon_status(sitename)
            if not conn['status']:
                return public.returnResult(False, '启动失败')
            else:
                return public.returnResult(True, '启动成功')
            
        
        # if project_action in ['start', 'restart']:
        #     site_info = self.get_project_find(sitename)
        #     for i in range(20):
        #         time.sleep(0.1)
        #         conn = public.ExecShell('systemctl status {}'.format(sitename))
        #         public.print_log(conn)
        #         if 'deactivating' in conn[0]:
        #             # 开启forking模式
        #             sys_conf = '/usr/lib/systemd/system/{}.service'.format(sitename)
        #             sys_conf = public.readFile(sys_conf)
        #             public.print_log(sys_conf)
        #             if 'Type=forking' not in sys_conf:
        #                 sys_conf = sys_conf.replace('Type=simple', 'Type=forking')
        #                 public.writeFile('/usr/lib/systemd/system/{}.service'.format(sitename), sys_conf)
        #             public.ExecShell('systemctl daemon-reload')
        #             public.ExecShell('systemctl restart {}'.format(sitename))
        #
        #         pid = RealServer().get_daemon_pid(sitename)["data"]
        #         if pid in [0, '0', '']:
        #             res = public.ExecShell("""ps -aux |grep "{}"|grep -v "grep"|awk '{{print $2}}'""".format(site_info['project_config']['project_cmd']))[0]
        #             res = res.strip().split("\n")
        #             if res and len(res) >= 1:
        #                 res.sort()
        #                 pid = res[0]
        #         if pid not in [0, '0', '']:
        #             pids = psutil.Process(int(pid)).children(recursive=True)
        #             pids = [str(i.pid) for i in pids]
        #             pids.append(str(pid))
        #             if pid not in [0, '0']:
        #                 res = public.ExecShell('lsof -i |grep -E "{}" |grep LISTEN'.format('|'.join(pids)))
        #                 if res[0]:
        #                     return public.returnResult(True, '启动成功')
        #     return public.returnResult(False, '启动失败')
        return public.returnResult(True, '关闭成功')
    
    def async_dependence_config(self, sitename):
        """
        增加安装依赖的配置文件
        """
        try:
            config = self.get_project_find(sitename)
            # public.ExecShell("chown -R {}:{} {}".format(config['project_config'].run_user.strip(), config['project_config'].run_user.strip(), get.site_path))
            # public.ExecShell("chmod -R 755 {}".format(config['path']))
            php_version = config['project_config']['php_version']
            php_ini_path = os.path.join(config['path'], 'php-cli.ini')
            public.ExecShell('cp /www/server/php/{}/etc/php-cli.ini {}'.format(php_version, config['path']))
            public.ExecShell('chown root:root {}'.format(php_ini_path))
            public.ExecShell('chmod 644 {}'.format(php_ini_path))
            public.ExecShell("sed -i '/disable_functions/d' {}".format(php_ini_path))
            public.writeFile(php_ini_path, php_cli_ini)
        
        except:
            pass
    
    # 修改项目网站运行目录
    def modify_project_path(self, get):
        if not hasattr(get, 'new_run_path_sub'):
            return public.returnResult(False, '新的运行目录不能为空')
        new_run_path_sub = get.new_run_path_sub
        sitename = get.sitename.strip()
        project_info = self.get_project_find(sitename)
        DirTool().modify_site_run_path(sitename, project_info['path'], new_run_path_sub)
        return public.returnResult(True, '修改成功')
    
    def modify_project(self, get):
        try:
            if not hasattr(get, 'sitename'):
                return public.returnResult(False, '项目名称不能为空')
            if not hasattr(get, 'project_cmd'):
                return public.returnResult(False, 'project_cmd不能为空')
            if not hasattr(get, 'project_path'):
                return public.returnResult(False, 'project_path不能为空')
            if not hasattr(get, 'site_run_path'):
                return public.returnResult(False, 'site_run_path不能为空')
            if not hasattr(get, 'run_user'):
                get.run_user = 'www'
            
            public.ExecShell('chown -R {}:{} {}'.format(get.run_user, get.run_user, get.project_path))
            public.ExecShell('chmod 755 {}'.format(get.project_path))
            config = self.get_project_find(get.sitename)
            start_cmd = get.project_cmd
            if 'php' == get.project_cmd[:3]:
                get.project_cmd = '/www/server/php/{}/bin/php -c {}/php-cli.ini {}'.format(get.php_version, get.project_path, get.project_cmd[3:])
            else:
                get.project_cmd = '/www/server/php/{}/bin/php -c {}/php-cli.ini {}'.format(get.php_version, get.project_path, get.project_cmd)
            if config['project_config'].get('start_cmd') != start_cmd:
                config['project_config']['start_cmd'] = start_cmd
            if config['path'] != get.project_path:
                if not os.path.exists(get.project_path):
                    return public.returnResult(False, '项目目录不存在')
                config['path'] = get.project_path
                config['project_config']['project_path'] = get.project_path
            
            # get.site_run_path = os.path.join(config['path'], get.site_run_path.lstrip("/"))
            config['project_config']['site_run_path'] = get.site_run_path.rstrip('/')
            get.new_run_path_sub = config['project_config']['site_run_path']
            self.modify_project_path(get)
            if config['project_config']['php_version'] != get.php_version:
                config['project_config']['php_version'] = get.php_version
                public.ExecShell('cp /www/server/php/{}/etc/php-cli.ini {}'.format(get.php_version, config['path']))
                public.ExecShell('chown root:root {}'.format(os.path.join(config['path'], 'php-cli.ini')))
                public.ExecShell('chmod 644 {}'.format(os.path.join(config['path'], 'php-cli.ini')))
                public.ExecShell("sed -i '/disable_functions/d' {}".format(os.path.join(config['path'], 'php-cli.ini')))
            if config['project_config']['project_cmd'] != get.project_cmd or config['project_config']['is_power_on'] != get.get('is_power_on', 1) or config['project_config'][
                'run_user'] != get.run_user:
                config['project_config']['is_power_on'] = get.get('is_power_on', 1)
                config['project_config']['project_cmd'] = get.project_cmd
                config['project_config']['run_user'] = get.run_user
                systemd_conf = '/usr/lib/systemd/system/{}.service'.format(get.sitename)
                conf = public.readFile(systemd_conf)
                is_fork = 0
                if conf:
                    if 'Type=forking' in conf:
                        is_fork = 1
                realserver = RealServer()
                realserver.create_daemon(get.sitename, '', get.project_cmd, get.project_path, user=config['project_config'].get('run_user', 'www'), is_power_on=get.is_power_on,
                                         logs_file=os.path.join(self._phpa_logs, get.sitename + '.log'), is_fork=is_fork)
            if config['ps'] != get.get('ps', '') and get.get('ps', ''):
                public.M('sites').where('name=?  and project_type=?', (get.sitename, 'PHP')).setField('ps', get.get('ps', ''))
            config['project_config']['port'] = get.get('project_port', 0)
            public.M('sites').where('name=? and project_type=?', (get.sitename, 'PHP')).setField('project_config', json.dumps(config['project_config']))
            return public.returnResult(True, '修改成功')
        except:
            return public.returnResult(False, traceback.format_exc())
    
    def get_project_log(self, get):
        log_file = self._phpa_logs + '/' + get.sitename + '.log'
        if not os.path.exists(log_file):
            return public.returnResult(status=True, msg='暂无项目日志')
        return public.returnResult(True, msg=public.GetNumLines(log_file, 1000))
    
    def get_access_log(self, get):
        from logsModel.siteModel import main as siteModel
        get.sitename = get.siteName.strip()
        sitelog = siteModel()
        return public.returnResult(True, data=sitelog.get_site_access_logs(get)['msg'])
    
    def get_error_log(self, get):
        from logsModel.siteModel import main as siteModel
        get.sitename = get.siteName.strip()
        sitelog = siteModel()
        return public.returnResult(True, data=sitelog.get_site_error_logs(get)['msg'])
    
    def get_config_file(self, get):
        result = {}
        site_name = get.sitename
        conf = self.get_project_find(site_name)
        result['nginx配置文件'] = self.setupPath + '/panel/vhost/nginx/' + site_name + '.conf'
        result['php-cli配置文件'] = os.path.join(conf['path'], 'php-cli.ini')
        env_path = os.path.join(conf['path'], '.env')
        if os.path.exists(env_path):
            result['.env配置文件'] = env_path
        result['伪静态配置文件'] = "/www/server/panel/vhost/rewrite/{}.conf".format(site_name)
        composer_path = os.path.join(conf['path'], 'composer.json')
        if os.path.exists(composer_path):
            result['composer配置文件'] = composer_path
        return public.returnResult(True, data=result)
    
    # 上传版本
    def upload_version(self, get):
        """
        上传压缩包并存储为版本
        """
        if not hasattr(get, 'sitename'):
            return public.returnResult(False, '项目名称不能为空')
        if not hasattr(get, 'version'):
            return public.returnResult(False, '版本号不能为空')
        if not hasattr(get, 'ps'):
            get.ps = ''
        try:
            upload_files = os.path.join("/tmp", get.f_name)
            from files import files
            fileObj = files()
            ff = fileObj.upload(get)
            if type(ff) == int:
                return ff
            if not ff['status']:
                return public.returnResult(False, ff['msg'])
            output_dir = str(os.path.join('/tmp', public.GetRandomString(16)))
            os.makedirs(output_dir, 777)
            if not self.extract_archive(upload_files, output_dir)[0]:
                return public.returnResult(False, '解压失败,仅支持zip,tar.gz,tar,bz2,gz,xz格式的压缩包')
            if len(os.listdir(output_dir)) == 1:
                output_dir = str(os.path.join(output_dir, os.listdir(output_dir)[0]))
            versiontool = VersionTool()
            res = versiontool.publish_by_src_path(get.sitename, output_dir, get.version, get.ps, sync=True)
            public.ExecShell('rm -rf {}'.format(output_dir))
            public.ExecShell('rm -rf {}'.format(upload_files))
            if res is None:
                return public.returnResult(True, '添加成功')
            return public.returnResult(False, '添加失败' + res)
        except:
            return public.returnResult(False, traceback.format_exc())
    
    def extract_archive(self, file_path, output_dir):
        name = os.path.basename(file_path)
        if name.endswith('.tar.gz'):
            with tarfile.open(file_path, 'r:gz') as tar:
                tar.extractall(output_dir)
        elif name.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(output_dir)
        elif name.endswith('.gz'):
            with gzip.open(file_path, 'rb') as f_in, open(os.path.join(output_dir, name[:-3]), 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        elif name.endswith('.tar'):
            with tarfile.open(file_path, 'r') as tar:
                tar.extractall(output_dir)
        elif name.endswith('.bz2'):
            with open(file_path, 'rb') as f_in, open(os.path.join(output_dir, name[:-4]), 'wb') as f_out:
                with bz2.BZ2File(f_in) as bz:
                    shutil.copyfileobj(bz, f_out)
        # elif name.endswith('.xz'):
        #     with lzma.open(file_path, 'rb') as f_in, open(os.path.join(output_dir, name[:-3]), 'wb') as f_out:
        #         shutil.copyfileobj(f_in, f_out)
        else:
            return False, '文件格式错误.'
        
        return True, '解压成功'
    
    # 获取列表
    def get_version_list(self, get):
        if not hasattr(get, 'sitename'):
            return public.returnResult(False, '项目名称不能为空')
        versiontool = VersionTool()
        return public.returnResult(True, data=versiontool.version_list(get.sitename))
    
    # 删除版本
    def remove_version(self, get):
        if not hasattr(get, 'sitename'):
            return public.returnResult(False, '项目名称不能为空')
        if not hasattr(get, 'version'):
            return public.returnResult(False, '版本号不能为空')
        versiontool = VersionTool()
        if versiontool.remove(get.sitename, get.version) is None:
            return public.returnResult(True, '删除成功')
        return public.returnResult(False, '删除失败')
    
    # 恢复版本
    def recover_version(self, get):
        try:
            if not hasattr(get, 'sitename'):
                return public.returnResult(False, '项目名称不能为空')
            if not hasattr(get, 'version'):
                return publihuoc.returnResult(False, '版本号不能为空')
            conf = self.get_project_find(get.sitename)
            versiontool = VersionTool()
            res = versiontool.recover(get.sitename, get.version, conf['path'], DirTool().get_site_run_path(get.sitename))
            if res is not True:
                return public.returnResult(False, res)
            return public.returnResult(True, '恢复成功')
        except:
            return public.returnResult(False, traceback.format_exc())
    
    def now_file_backup(self, get):
        try:
            if not hasattr(get, 'sitename'):
                return public.returnResult(False, '项目名称不能为空')
            if not hasattr(get, 'version'):
                return public.returnResult(False, '版本号不能为空')
            if not hasattr(get, 'ps'):
                get.ps = ''
            config = self.get_project_find(get.sitename)
            path = config['path']
            versiontool = VersionTool()
            res = versiontool.publish_by_src_path(get.sitename, path, get.version, get.ps, sync=True)
            if res is None:
                return public.returnResult(True, '添加成功')
            return public.returnResult(False, '添加失败' + res)
        except:
            return public.returnResult(False, traceback.format_exc())
    
    def set_version_ps(self, get):
        if not hasattr(get, 'sitename'):
            return public.returnResult(False, '项目名称不能为空')
        if not hasattr(get, 'version'):
            return public.returnResult(False, '版本号不能为空')
        if not hasattr(get, 'ps'):
            get.ps = ''
        versiontool = VersionTool()
        versiontool.set_ps(get.sitename, get.version, get.ps)
        return public.returnResult(True, '设置成功')
    
    def get_setup_log(self, get):
        log_file = "/tmp/{}_install_dependence.log".format(get.sitename)
        if not os.path.exists(log_file):
            return public.returnResult(True, data='暂无项目日志')
        return public.returnResult(True, data=public.GetNumLines(log_file, 1000))
    
    def add_crontab(self, get):
        try:
            if not hasattr(get, 'sitename'):
                return public.returnResult(False, '项目名称不能为空')
            if not hasattr(get, 'cron_name'):
                return public.returnResult(False, '定时任务名称不能为空')
            if not hasattr(get, 'sBody'):
                return public.returnResult(False, '定时任务内容不能为空')
            args = {
                "name": get.cron_name,
                "type": get.type,
                "where1": get.where1,
                "hour": get.hour,
                "minute": get.minute,
                "week": get.week,
                "sType": "toShell",
                "sName": "",
                "backupTo": "localhost",
                "save": get.sitename,
                "sBody": get.sBody,
                "urladdress": "",
                "flock": get.flock
            }
            import crontab
            res = crontab.crontab().AddCrontab(public.to_dict_obj(args))
            if res['status']:
                return public.returnResult(True, msg='添加成功!')
            return public.returnResult(False, res['msg'])
        except:
            return public.returnResult(False, traceback.format_exc())
    
    def get_crontab_list(self, get):
        try:
            if not hasattr(get, 'sitename'):
                return public.returnResult(False, '项目名称不能为空')
            cront = public.M('crontab').where('save=?', (get.sitename,)).select()
            
            data = []
            for i in range(len(cront)):
                tmp = cront[i]
                
                if cront[i]['type'] == "day":
                    tmp['type_zh'] = public.getMsg('CRONTAB_TODAY')
                    tmp['cycle'] = public.getMsg('CRONTAB_TODAY_CYCLE',
                                                 (str(cront[i]['where_hour']), str(cront[i]['where_minute'])))
                elif cront[i]['type'] == "day-n":
                    tmp['type_zh'] = public.getMsg('CRONTAB_N_TODAY', (str(cront[i]['where1']),))
                    tmp['cycle'] = public.getMsg('CRONTAB_N_TODAY_CYCLE', (
                        str(cront[i]['where1']), str(cront[i]['where_hour']), str(cront[i]['where_minute'])))
                elif cront[i]['type'] == "hour":
                    tmp['type_zh'] = public.getMsg('CRONTAB_HOUR')
                    tmp['cycle'] = public.getMsg('CRONTAB_HOUR_CYCLE', (str(cront[i]['where_minute']),))
                elif cront[i]['type'] == "hour-n":
                    tmp['type_zh'] = public.getMsg('CRONTAB_N_HOUR', (str(cront[i]['where1']),))
                    tmp['cycle'] = public.getMsg('CRONTAB_N_HOUR_CYCLE',
                                                 (str(cront[i]['where1']), str(cront[i]['where_minute'])))
                elif cront[i]['type'] == "minute-n":
                    tmp['type_zh'] = public.getMsg('CRONTAB_N_MINUTE', (str(cront[i]['where1']),))
                    tmp['cycle'] = public.getMsg('CRONTAB_N_MINUTE_CYCLE', (str(cront[i]['where1']),))
                elif cront[i]['type'] == "week":
                    tmp['type_zh'] = public.getMsg('CRONTAB_WEEK')
                    if not cront[i]['where1']: cront[i]['where1'] = '0'
                    tmp['cycle'] = public.getMsg('CRONTAB_WEEK_CYCLE', (
                        self.toWeek(int(cront[i]['where1'])), str(cront[i]['where_hour']),
                        str(cront[i]['where_minute'])))
                elif cront[i]['type'] == "month":
                    tmp['type_zh'] = public.getMsg('CRONTAB_MONTH')
                    tmp['cycle'] = public.getMsg('CRONTAB_MONTH_CYCLE', (
                        str(cront[i]['where1']), str(cront[i]['where_hour']), str(cront[i]['where_minute'])))
                
                log_file = '/www/server/cron/{}.log'.format(tmp['echo'])
                if os.path.exists(log_file):
                    tmp['addtime'] = self.get_last_exec_time(log_file)
                data.append(tmp)
            
            for i in data:
                if i['backup_mode'] == "1":
                    i['backup_mode'] = 1
                else:
                    i['backup_mode'] = 0
                if i['db_backup_path'] == "":
                    i['db_backup_path'] = "/www/backup"
                
                if not i.get('rname', ''):
                    i['rname'] = i['name']
                if i['time_type'] == 'sweek':
                    i['type'] = 'sweek'
                    week_str = self.toweek(i['time_set'])
                    if week_str:  # 检查week_str是否为空
                        i['type_zh'] = week_str
                        i['cycle'] = "每" + week_str + i['special_time'] + "执行"
                
                elif i['time_type'] == 'sday':
                    i['type'] = 'sweek'
                    i['type_zh'] = i['special_time']
                    i['cycle'] = "每天" + i['special_time'] + "执行"
                
                elif i['time_type'] == 'smonth':
                    i['type'] = 'sweek'
                    i['type_zh'] = i['special_time']
                    i['cycle'] = "每月" + i['time_set'] + "号" + i['special_time'] + "执行"
                if i['sType'] == 'site_restart':
                    i['cycle'] = "每天" + i['special_time'] + "执行"
            return public.returnResult(True, data=data)
        except:
            return public.returnResult(False, traceback.format_exc())
    
    # 转换大写星期
    def toWeek(self, num):
        wheres = {
            0: public.getMsg('CRONTAB_SUNDAY'),
            1: public.getMsg('CRONTAB_MONDAY'),
            2: public.getMsg('CRONTAB_TUESDAY'),
            3: public.getMsg('CRONTAB_WEDNESDAY'),
            4: public.getMsg('CRONTAB_THURSDAY'),
            5: public.getMsg('CRONTAB_FRIDAY'),
            6: public.getMsg('CRONTAB_SATURDAY')
        }
        try:
            return wheres[num]
        except:
            return ''
    
    def get_last_exec_time(self, log_file):
        '''
            @name 获取上次执行时间
            @author hwliang
            @param log_file<string> 日志文件路径
            @return format_date
        '''
        exec_date = ''
        try:
            log_body = public.GetNumLines(log_file, 20)
            if log_body:
                log_arr = log_body.split('\n')
                date_list = []
                for i in log_arr:
                    if i.find('★') != -1 and i.find('[') != -1 and i.find(']') != -1:
                        date_list.append(i)
                if date_list:
                    exec_date = date_list[-1].split(']')[0].split('[')[1]
        except:
            pass
        
        finally:
            if not exec_date:
                exec_date = public.format_date(times=int(os.path.getmtime(log_file)))
        return exec_date
    
    def start_task(self, get):
        try:
            if not hasattr(get, 'id'):
                return public.returnResult(False, 'ID不能为空')
            import crontab
            res = crontab.crontab().StartTask(get)
            if res['status']:
                return public.returnResult(True, '启动成功')
            return public.returnResult(False, res['msg'])
        except:
            return public.returnResult(False, traceback.format_exc())
    
    def modify_crontab_status(self, get):
        try:
            if not hasattr(get, 'id'):
                return public.returnResult(False, 'ID不能为空')
            if hasattr(get, 'status'):
                cronInfo = public.M('crontab').where('id=?', (get.id,)).select()[0]
                if int(cronInfo['status']) == int(get.status):
                    return public.returnResult(True, '修改成功')
            get.if_stop = False
            import crontab
            res = crontab.crontab().set_cron_status(get)
            if res['status']:
                return public.returnResult(True, '修改成功')
            return public.returnResult(False, res['msg'])
        except:
            return public.returnResult(False, traceback.format_exc())
    
    def remove_crontab(self, get):
        try:
            if not hasattr(get, 'id'):
                return public.returnResult(False, 'ID不能为空')
            import crontab
            res = crontab.crontab().DelCrontab(get)
            if res['status']:
                return public.returnResult(True, '删除成功')
            return public.returnResult(False, res['msg'])
        except:
            return public.returnResult(False, traceback.format_exc())
    
    def modify_crontab(self, get):
        try:
            if not hasattr(get, 'id'):
                return public.returnResult(False, 'ID不能为空')
            self.remove_crontab(get)
            res = self.add_crontab(get)
            res['msg'] = res['msg'].replace('添加', '修改')
            return res
        except:
            return public.returnResult(False, traceback.format_exc())
    
    def get_crontab_log(self, get):
        try:
            if not hasattr(get, 'id'):
                return public.returnResult(False, 'ID不能为空')
            import crontab
            res = crontab.crontab().GetLogs(get)
            return public.returnResult(True, res['msg'])
        except:
            return public.returnResult(False, traceback.format_exc())
    
    def clearn_logs(self, get):
        try:
            if not hasattr(get, 'id'):
                return public.returnResult(False, '项目名称不能为空')
            import crontab
            crontab.crontab().DelLogs(get)
            return public.returnResult(True, '清空成功')
        except:
            return public.returnResult(False, traceback.format_exc())
    
    def get_group_file(self):
        config = json.loads(public.readFile(self.group_file))
        return config
    
    def get_group_list(self, get):
        try:
            config = self.get_group_file()
            result = []
            for i, j in config.items():
                tmp = []
                for k in j['project_list']:
                    con = self.get_project_run_state(public.to_dict_obj({'sitename': k}))['data']
                    if con:
                        tmp.append(con)
                    else:
                        self.group_remove_project(public.to_dict_obj({'group_name': i, 'sitename': k}))
                j['project_list'] = tmp
                j['name'] = i
                result.append(j)
            
            for i in result:
                for j in i['project_list']:
                    if not j:
                        print(j)
                        continue
                    if not j['status']:
                        i['status'] = 0
                        break
                if len(i['project_list']) == 0:
                    i['status'] = 0
            return public.returnResult(True, data=result)
        except:
            return public.returnResult(False, traceback.format_exc())
    
    def set_order(self, get):
        project_list = get.project_list.strip(',').split(',')
        group_name = get.group_name
        config = self.get_group_file()
        if group_name not in config:
            return public.returnResult(False, '组名不存在')
        config[group_name]['project_list'] = project_list
        public.writeFile(self.group_file, json.dumps(config))
        return public.returnResult(True, '设置成功')
    
    def create_group(self, get):
        try:
            if not hasattr(get, 'group_name'):
                return public.returnResult(False, '组名不能为空')
            config = self.get_group_file()
            if get.group_name in config:
                return public.returnResult(False, '组名已存在')
            config[get.group_name] = {'interval': get.get('interval', 30), 'project_list': [], 'status': 0}
            public.writeFile(self.group_file, json.dumps(config))
            return public.returnResult(True, '添加成功')
        except:
            return public.returnResult(False, traceback.format_exc())
    
    def remove_group(self, get):
        if not hasattr(get, 'group_name'):
            return public.returnResult(False, '组名不能为空')
        config = self.get_group_file()
        if get.group_name not in config:
            return public.returnResult(False, '组名不存在')
        del config[get.group_name]
        public.writeFile(self.group_file, json.dumps(config))
        return public.returnResult(True, '删除成功')
    
    def group_add_project(self, get):
        try:
            if not hasattr(get, 'group_name'):
                return public.returnResult(False, '组名不能为空')
            if not hasattr(get, 'sitename'):
                return public.returnResult(False, '项目名不能为空')
            config = self.get_group_file()
            if get.group_name not in config:
                return public.returnResult(False, '组名不存在')
            if get.sitename not in config[get.group_name]['project_list']:
                config[get.group_name]['project_list'].append(get.sitename)
            flag = 1
            for i in config[get.group_name]['project_list']:
                if not self.get_project_run_state(public.to_dict_obj({'sitename': i}))['status']:
                    flag = 0
                    break
            if flag:
                config[get.group_name]['status'] = 1
            public.writeFile(self.group_file, json.dumps(config))
            return public.returnResult(True, '添加成功')
        except:
            return public.returnResult(False, traceback.format_exc())
    
    def group_remove_project(self, get):
        try:
            if not hasattr(get, 'group_name'):
                return public.returnResult(False, '组名不能为空')
            if not hasattr(get, 'sitename'):
                return public.returnResult(False, '项目名不能为空')
            config = self.get_group_file()
            if get.group_name not in config:
                return public.returnResult(False, '组名不存在')
            if get.sitename not in config[get.group_name]['project_list']:
                return public.returnResult(False, '项目不存在')
            config[get.group_name]['project_list'].remove(get.sitename)
            flag = 1
            for i in config[get.group_name]['project_list']:
                if not self.get_project_run_state(public.to_dict_obj({'sitename': i}))['status']:
                    flag = 0
                    break
            if flag:
                config[get.group_name]['status'] = 1
            else:
                config[get.group_name]['status'] = 0
            public.writeFile(self.group_file, json.dumps(config))
            return public.returnResult(True, '删除成功')
        except:
            return public.returnResult(False, traceback.format_exc())
    
    def set_group_interval(self, get):
        if not hasattr(get, 'group_name'):
            return public.returnResult(False, '组名不能为空')
        if not hasattr(get, 'interval'):
            return public.returnResult(False, '间隔时间不能为空')
        config = self.get_group_file()
        if get.group_name not in config:
            return public.returnResult(False, '组名不存在')
        config[get.group_name]['interval'] = get.interval
        public.writeFile(self.group_file, json.dumps(config))
        return public.returnResult(True, '设置成功')
    
    def set_group_status(self, get):
        if not hasattr(get, 'group_name'):
            return public.returnResult(False, '组名不能为空')
        if not hasattr(get, 'status'):
            return public.returnResult(False, '状态不能为空')
        config = self.get_group_file()
        if get.group_name not in config:
            return public.returnResult(False, '组名不存在')
        if get.status == 'stop':
            public.run_thread(self.stop_groups, (get.group_name,))
            return public.returnResult(True, '开始停止项目')
        if get.status == 'start':
            public.run_thread(self.start_groups, (get.group_name,))
            return public.returnResult(True, '开始启动项目')
        return public.returnResult(True, '设置成功')
    
    def stop_groups(self, group):
        config = self.get_group_file()
        if group not in config:
            return public.returnResult(False, '组名不存在')
        config[group]['status'] = 0
        for i in config[group]['project_list']:
            self.modify_project_run_state(public.to_dict_obj({'sitename': i, 'project_action': 'stop'}))
        public.writeFile(self.group_file, json.dumps(config))
    
    def start_groups(self, group):
        config = self.get_group_file()
        self.stop_groups(group)
        if group not in config:
            return public.returnResult(False, '组名不存在')
        for i in config[group]['project_list']:
            self.modify_project_run_state(public.to_dict_obj({'sitename': i, 'project_action': 'start'}))
            if config[group]['project_list'].index(i) == len(config[group]['project_list']) - 1:
                continue
            time.sleep(int(config[group]['interval']))
        flag = 1
        for i in config[group]['project_list']:
            if not self.get_project_run_state(public.to_dict_obj({'sitename': i}))['status']:
                flag = 0
                break
        if flag:
            config[group]['status'] = 1
        else:
            config[group]['status'] = 0
        public.writeFile(self.group_file, json.dumps(config))
    
    # 取代理配置文件
    def get_proxy_file(self, get):
        try:
            import files
            conf = [] if not os.path.exists(self.__proxyfile) else json.loads(public.readFile(self.__proxyfile))
            get.webserver = public.GetWebServer()
            sitename = get.sitename
            proxyname = get.proxyname
            proxyname_md5 = self.__calc_md5(proxyname)
            get.path = "%s/panel/vhost/%s/proxy/%s/%s_%s.conf" % (self.setupPath, get.webserver, sitename, proxyname_md5, sitename)
            for i in conf:
                if proxyname == i["proxyname"] and sitename == i["sitename"] and i["type"] != 1:
                    return public.returnResult(False, '代理已暂停')
            f = files.files()
            return public.returnResult(True, data=(f.GetFileBody(get), get.path))
        except:
            return public.returnResult(False, traceback.format_exc())
    
    # 计算proxyname md5
    def __calc_md5(self, proxyname):
        md5 = hashlib.md5()
        md5.update(proxyname.encode('utf-8'))
        return md5.hexdigest()
    
    # 保存重定向配置文件
    def save_proxy_file(self, get):
        import files
        f = files.files()
        get.data = get.config
        return f.SaveFileBody(get)
    
    def set_cron_status_all(self, get):
        import crontab
        return crontab.crontab().set_cron_status_all(get)
    
    def get_index_conf(self, get):
        if not hasattr(get, 'id'):
            return public.returnResult(False, msg='请输入id')
        sitename = public.M('sites').where('id=?', (get.id,)).getField('name')
        if not sitename:
            return public.returnResult(False, msg='项目不存在')
        res = DirTool().get_index_conf(sitename)
        if str(res) == str:
            return public.returnResult(False, msg='获取失败' + res)
        else:
            return public.returnResult(True, data=res)
    
    def set_index_conf(self, get):
        if not hasattr(get, 'id'):
            return public.returnResult(False, msg='请输入id')
        if not hasattr(get, 'Index'):
            return public.returnResult(False, msg='配置不能为空')
        try:
            sitename = public.M('sites').where('id=?', (get.id,)).getField('name')
            index = get.Index
            if type(get.Index) == str:
                index = get.Index.split(',')
            DirTool().set_index_conf(sitename, file_list=index)
            return public.returnResult(True, msg='设置成功')
        except:
            return public.returnResult(False, msg='设置失败')
    
    def get_referer_security(self, get):
        if not hasattr(get, 'id'):
            return public.returnResult(False, msg='请输入id')
        sitename = public.M('sites').where('id=?', (get.id,)).getField('name')
        if not sitename:
            return public.returnResult(False, msg='项目不存在')
        get.site_name = sitename
        return Referer('').get_referer_security(get)
    
    def set_referer_security(self, get):
        return Referer('').set_referer_security(get)
    
    def get_system_user_list(self, get=None):
        """
        默认只返回uid>= 1000 的用户 和 root
        get中包含 sys_user 返回 uid>= 100 的用户 和 root
        get中包含 all_user 返回所有的用户
        """
        sys_user = False
        all_user = False
        if get is not None:
            if hasattr(get, "sys_user"):
                sys_user = True
            if hasattr(get, "all_user"):
                all_user = True
        
        user_set = set()
        try:
            import pwd
            for tmp_uer in pwd.getpwall():
                if tmp_uer.pw_uid == 0:
                    user_set.add(tmp_uer.pw_name)
                elif tmp_uer.pw_uid >= 1000:
                    user_set.add(tmp_uer.pw_name)
                elif sys_user and tmp_uer.pw_uid >= 100:
                    user_set.add(tmp_uer.pw_name)
                elif all_user:
                    user_set.add(tmp_uer.pw_name)
        except Exception:
            pass
        return list(user_set)


if __name__ == "__main__":
    m = main()
    m.install_dependence("555.com", "82", "/xiaopacai/laravel11.5.0/", composer_version="2.7.3")
