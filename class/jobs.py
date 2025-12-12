#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------
import time,public,db,os,sys,json,re,shutil
os.chdir('/www/server/panel')
today_time = str(time.time())
run_time_file = '/www/server/panel/jobs_run_time.pl'

def control_init():
    public.chdck_salt()
    rep_websocket_conf()
    rep_nginx_conf()
    rep_conf_db_data()
    acme_crond_reinit()
    check_default_ssl_conf()
    rep_php_enable()
    remove_tty1()
    run_new()
    set_nginx_extension()
    set_apache_extension()
    setup_site_total()
    check_cryptography_pyopenssl_version()
    check_docker_version()
    clear_fastcgi_safe()
    check_enable_php()
    rm_apache_cgi_test()
    ping_test()
    sync_default_msg_channel()
    update_python_project_env()
    if not os.path.exists('/www/server/panel/data/check_ssl_cron.pl'): check_ssl_cron()

    try:
        if os.path.exists(run_time_file):
            if time.time() - os.path.getmtime(run_time_file) < 86400: return
    except:
        pass

    try:
        #重启后反代配置是否正确
        from panelModel.panel_reverse_generationModel import main as prg
        prg().check_panel_site()
    except:
        pass

    clean_node_log()
    update_pubsuffix_dat()
    set_pma_access()
    clear_other_files()
    sql_pacth()
    #disable_putenv('putenv')
    #clean_session()
    #set_crond()
    clean_max_log("/www/server/panel/logs/ipfilter.log",1024*1024*10)
    clean_max_log('/www/server/panel/plugin/rsync/lsyncd.log')
    clean_max_log('/var/log/rsyncd.log',1024*1024*10)
    clean_max_log('/root/.pm2/pm2.log',1024*1024*20)
    clean_max_log('/usr/local/usranalyse/logs/send/bt_security.json', 1024*1024*100)
    clean_hook_log()
    clean_max_log('/www/server/cron',1024*1024*5,20)
    clean_max_log("/www/server/panel/plugin/webhook/script",1024*1024*1)
    # #check_firewall()
    check_dnsapi()
    clean_php_log()
    files_set_mode()
    # # public.set_open_basedir()
    update_py37()
    run_script()
    set_php_cli_env()
    # sync_node_list()
    check_default_curl_file()
    null_html()
    remove_other()
    deb_bashrc()
    upgrade_gevent()
    upgrade_polkit()
    # # hide_docker()
    rep_pyenv_link()
    panel_create_chunk()
    check_brotli()
    vacuum_db()
    public.writeFile(run_time_file, today_time)


def acme_crond_reinit():
    '''
        @name 修复acme定时任务
        @return void
    '''
    try:
        lets_config_file = os.path.join(public.get_panel_path(),'config/letsencrypt_v2.json')
        if not os.path.exists(lets_config_file): return
        import acme_v2
        acme_v2.acme_v2().set_crond()
    except:
        pass


def check_ssl_cron():
    # 检车Let's Encrypt证书续签任务的python路径是否正确
    echo_id = public.M('crontab').where('name=?',("续签Let's Encrypt证书",)).getField('echo')
    if not echo_id: return
    crontab_path = '/www/server/cron/{}'.format(echo_id)
    if not os.path.exists(crontab_path): return
    public.ExecShell("sed -i 's#/usr/bin/python#/www/server/panel/pyenv/bin/python3#g' {}".format(crontab_path))
    conf = public.readFile(crontab_path)
    if '/www/server/panel/pyenv/bin/python3' in conf:
        cmd = public.M('crontab').where('name=?',("续签Let's Encrypt证书",)).getField('sBody')
        cmd = cmd.replace('/usr/bin/python','/www/server/panel/pyenv/bin/python3')
        public.M('crontab').where('name=?',("续签Let's Encrypt证书",)).setField('sBody',cmd)
        public.ExecShell("systemctl restart crond")
        public.writeFile('/www/server/panel/data/check_ssl_cron.pl','True')
    
def rep_nginx_conf():
    '''
        @name 修复nginx配置文件
        @return void
    '''
    os.system("{} {}/script/nginx_conf_rep.py".format(public.get_python_bin(),public.get_panel_path()))

    filename = '{}/vhost/nginx/speed.conf'.format(public.get_panel_path())
    if os.path.exists(filename):
        f = open(filename,'r')
        conf_lines = f.readlines()
        f.close()
        n = 0
        for line in conf_lines:
            if line.find('lua_shared_dict site_cache') != -1:
                n+=1
        if n > 1:
            src_file = '{}/plugin/site_speed/speed.conf'.format(public.get_panel_path())
            if os.path.exists(src_file):
                shutil.copyfile(src_file,filename)
                public.ExecShell('/etc/init.d/nginx reload')
                print("修复:",filename)

def vacuum_db():
    '''
        @name 优化数据库
        @return void
    '''
    os.chdir('/www/server/panel')
    db_list = [
        {"file":"data/db/task.db","max_size":1024*1024*10},
    ]

    for db_info in db_list:
        try:
            if not os.path.exists(db_info['file']): continue
            db_size = os.path.getsize(db_info['file'])
            if db_size < db_info['max_size']: continue
            conn = db.sqlite3.connect(db_info['file'])
            if not conn: continue
            conn.execute('VACUUM',())
            conn.close()
        except:
            pass


def check_cryptography_pyopenssl_version():
    out1, error1 = public.ExecShell('/www/server/panel/pyenv/bin/python -c "import cryptography; print(cryptography.__version__.split(\'.\')[0])"') # type: str, str
    out2, error2 = public.ExecShell('/www/server/panel/pyenv/bin/python -c "import OpenSSL.crypto, OpenSSL; print(OpenSSL.__version__.split(\'.\')[0])"')

    need_reinstall = False
    if not out1 or not out1.strip().isdecimal() or int(out1) < 38:
        need_reinstall=True
    if error2.find("Traceback") != -1:
        need_reinstall=True
    elif not out2 or not out2.strip().isdecimal() or int(out2) < 24:
        need_reinstall=True

    if need_reinstall:
        from glob import glob
        from itertools import chain
        public.ExecShell("btpip uninstall pyopenssl -y")
        public.ExecShell("btpip uninstall pyopenssl -y")
        try:
            for i in chain(
                glob("/www/server/panel/pyenv/lib/python3.*/site-packages/pyopenssl*"),
                glob("/www/server/panel/pyenv/lib/python3.*/site-packages/OpenSSL"),
            ):
                if os.path.exists(i):
                    shutil.rmtree(i)
        except Exception as e:
            print(e)

        public.ExecShell("btpip uninstall cryptography -y")
        public.ExecShell("btpip uninstall cryptography -y")
        try:
            for i in chain(
                glob("/www/server/panel/pyenv/lib/python3.*/site-packages/cryptography"),
                glob("/www/server/panel/pyenv/lib/python3.*/site-packages/cryptography*"),
            ):
                if os.path.exists(i):
                    shutil.rmtree(i)
        except Exception as e:
            print(e)
        public.ExecShell("{panel_path}/pyenv/bin/python {panel_path}/script/pip_conf_selector.py --auto".format(
            panel_path=public.get_panel_path()
        ))
        public.ExecShell("btpip install pyopenssl cryptography")


def rep_php_enable():
    '''
        @name 修复PHP引用文件
        @return void
    '''

    # 是否为nginx环境
    nginx_conf_path = '{}/nginx/conf'.format(public.get_setup_path())
    if not os.path.exists(nginx_conf_path): return

    # 默认配置
    default_conf = '''    location ~ [^/]\.php(/|$)
    {
        try_files $uri =404;
        fastcgi_pass  unix:/tmp/php-cgi-[PHP_VERSION].sock;
        fastcgi_index index.php;
        include fastcgi.conf;
        include pathinfo.conf;
    }'''

    # 获取PHP版本
    php_versions = public.get_php_versions()
    rep_file_list = []
    for php_version in php_versions:
        if isinstance(php_version,int): php_version = str(php_version)

        # 检查是否已经存在配置文件
        enable_file = '{}/enable-php-{}.conf'.format(nginx_conf_path,php_version)
        if os.path.exists(enable_file):
            conf_body = public.readFile(enable_file)
            # 如果配置文件中包含fastcgi_pass则跳过
            if conf_body.find('fastcgi_pass') != -1: continue

        # 生成配置文件
        rep_file_list.append(enable_file)
        conf_body = default_conf.replace('[PHP_VERSION]',php_version)
        public.writeFile(enable_file,conf_body)

    # 检查配置文件是否正确
    setupPath = public.get_setup_path()
    result = public.ExecShell('ulimit -n 8192 ; ' + setupPath + '/nginx/sbin/nginx -t -c ' + setupPath + '/nginx/conf/nginx.conf')
    if 'successful' not in result[1]:
        # 配置文件错误则删除刚刚生成的文件
        for enable_file in rep_file_list:
            if os.path.exists(enable_file): os.remove(enable_file)

def rep_conf_db_data():
    '''
        @name 修复confg.db的第一条数据
         部分情况下config表中的第一条数据会丢失
        @return void
    '''
    try:
        res = public.M("config").where("id=?", (1,)).find()
        if not isinstance(res, dict):  # 未查到id为1的数据
            pdata = {
                "id": 1,
                "webserver": public.GetWebServer(),
                "backup_path": "/www/backup",
                "sites_path": "/www/wwwroot",
                "status": 0,
                "mysql_root": "root"
            }
            public.M("config").insert(pdata)
    except:
        pass

def rep_websocket_conf():
    '''
        @name 修复websocket配置文件
        @return void
    '''

    conf = '''map $http_upgrade $connection_upgrade {
    default upgrade;
    ''  close;
}'''

    conf_file = '{}/vhost/nginx/0.websocket.conf'.format(public.get_panel_path())
    if os.path.exists(conf_file):
        conf_body = public.readFile(conf_file)
        if conf_body.find('map $http_upgrade $connection_upgrade') != -1: return

    public.writeFile(conf_file,conf)
    setupPath = public.get_setup_path()
    result = public.ExecShell('ulimit -n 8192 ; ' + setupPath + '/nginx/sbin/nginx -t -c ' + setupPath + '/nginx/conf/nginx.conf')
    if 'connection_upgrade' in result[1]:
        if os.path.exists(conf_file): os.remove(conf_file)

def check_default_ssl_conf():
    '''
        @name 检查默认SSL配置是否存在
        @return void
    '''
    ngx_default_conf_file = "{}/nginx/0.default.conf".format(public.get_vhost_path())
    if not os.path.exists(ngx_default_conf_file): return

    conf = public.readFile(ngx_default_conf_file)
    if not conf: return

    if conf.find('ssl_certificate') == -1:
        return

    old_index = 'listen 443 ssl;'
    index_of = 'listen 443 ssl http2;'
    versionStr = public.readFile('/www/server/nginx/version.pl')
    if versionStr:
        if versionStr.find('1.8.1') != -1:
            return

    if conf.find(index_of) != -1:
        return

    conf = conf.replace(old_index,index_of)
    public.writeFile(ngx_default_conf_file,conf)

def check_brotli():
    '''
        @name 安装brotli模块(如果没有安装的话)
        @return void
    '''
    # 未开启面板SSL则不安装
    if not os.path.exists('/www/server/panel/data/ssl.pl'): return
    try:
        import brotli
    except ImportError:
        tip_file = '/tmp/brotil_install.pl'
        if os.path.exists(tip_file):
            # 10分钟内安装过brotli则不再尝试安装
            if time.time() - os.stat(tip_file).st_mtime < 600:
                return
        os.system("nohup {} -m pip install brotli &> {} &".format(public.get_python_bin(),tip_file))

def rm_apache_cgi_test():
    '''
        @name 删除apache测试cgi文件
        @author hwliang
        @return void
    '''
    test_cgi_file = '/www/server/apache/cgi-bin/test-cgi'
    if os.path.exists(test_cgi_file):
        os.remove(test_cgi_file)

def rep_pyenv_link():
    '''
        @name 修复pyenv环境软链
        @author hwliang
        @return void
    '''
    pyenv_bin = '/www/server/panel/pyenv/bin/python3'
    btpython_bin = '/usr/bin/btpython'
    pip_bin = '/www/server/panel/pyenv/bin/pip3'
    btpip_bin = '/usr/bin/btpip'

    # 检查btpython软链接
    if not os.path.exists(pyenv_bin): return
    if not os.path.exists(btpython_bin):
        public.ExecShell("ln -sf {} {}".format(pyenv_bin,btpython_bin))

    # 检查btpip软链接
    if not os.path.exists(pip_bin): return
    if not os.path.exists(btpip_bin):
        public.ExecShell("ln -sf {} {}".format(pip_bin,btpip_bin))


def hide_docker():
    '''
        @name 隐藏docker菜单
        @author hwliang
        @return void
    '''
    tip_file = '{}/data/hide_docker.pl'.format(public.get_panel_path())
    if os.path.exists(tip_file): return

    # 正在使用docker-compose的用户不隐藏
    docker_compose = "/usr/bin/docker-compose"
    if os.path.exists(docker_compose): return

    # 获取隐藏菜单配置
    menu_key = 'memuDocker'
    hide_menu_json = public.read_config('hide_menu')
    if not isinstance(hide_menu_json,list):
        hide_menu_json = []
    if menu_key in hide_menu_json: return

    # 保存隐藏菜单配置
    hide_menu_json.append(menu_key)
    public.save_config('hide_menu',hide_menu_json)
    public.writeFile(tip_file,'True')





def upgrade_polkit():
    '''
        @name 修复polkit提权漏洞(CVE-2021-4034)
        @author hwliang
        @return void
    '''
    upgrade_log_file = '{}/logs/upgrade_polkit.log'.format(public.get_panel_path())
    tip_file = '{}/data/upgrade_polkit.pl'.format(public.get_panel_path())
    if os.path.exists(tip_file): return
    os.system("nohup {} {}/script/polkit_upgrade.py &> {}".format(public.get_python_bin(),public.get_panel_path(),upgrade_log_file))

def clear_other_conf():
    path = '/www/server/panel/vhost/nginx'
    if not os.path.exists(path):
        return
    is_reload = False
    for fname in os.listdir(path):
        if fname.split('.')[-1] != 'conf':
            continue
        filename = os.path.join(path,fname)
        conf_body = public.readFile(filename)
        if not conf_body: continue
        if conf_body.find('body_filter_by_lua_block') != -1 and conf_body.find('</head') and conf_body.find('<scrip'):
            is_reload = True
            os.remove(filename)
            bak_file = filename + '.bak'
            if os.path.exists(bak_file): os.remove(bak_file)

    nginx_conf = '/www/server/nginx/conf/nginx.conf'
    nginx_conf_body = public.readFile(nginx_conf)
    if not nginx_conf_body: return
    keyword = "injectjs_filter"
    if nginx_conf_body.find(keyword) != -1:
        is_reload = True
        public.ExecShell("sed -i '/{}/d' {}".format(keyword,nginx_conf))

    if is_reload:
        public.ExecShell("/etc/init.d/nginx reload")
        public.ExecShell("/etc/init.d/nginx start")



def clear_other_files():
    dirPath = '/www/server/phpmyadmin/pma'
    if os.path.exists(dirPath):
        public.ExecShell("rm -rf {}".format(dirPath))
    dirPath = '/www/server/nginx/waf'
    if os.path.exists(dirPath):
        public.ExecShell("rm -rf {}".format(dirPath))
        public.ExecShell("/etc/init.d/nginx reload")
        public.ExecShell("/etc/init.d/nginx start")

    dirPath = '/www/server/adminer'
    if os.path.exists(dirPath):
        public.ExecShell("rm -rf {}".format(dirPath))

    dirPath = '/www/server/panel/adminer'
    if os.path.exists(dirPath):
        public.ExecShell("rm -rf {}".format(dirPath))

    filename = '/www/server/nginx/off'
    if os.path.exists(filename): os.remove(filename)
    clear_other_conf()

    c = public.to_string([99, 104, 97, 116, 116, 114, 32, 45, 105, 32, 47, 119, 119, 119, 47,
                          115, 101, 114, 118, 101, 114, 47, 112, 97, 110, 101, 108, 47, 99,
                          108, 97, 115, 115, 47, 42])
    try:
        init_file = '/etc/init.d/bt'
        src_file = '/www/server/panel/init.sh'
        md51 = public.md5(init_file)
        md52 = public.md5(src_file)
        if md51 != md52:
            import shutil
            shutil.copyfile(src_file,init_file)
            if os.path.getsize(init_file) < 10:
                public.ExecShell("chattr -i " + init_file)
                public.ExecShell("\cp -arf %s %s" % (src_file,init_file))
                public.ExecShell("chmod +x %s" % init_file)
    except:pass
    public.writeFile('/var/bt_setupPath.conf','/www')
    public.ExecShell(c)
    p_file = 'class/plugin2.so'
    if os.path.exists(p_file): public.ExecShell("rm -f class/*.so")
    # public.ExecShell("chmod -R  600 /www/server/panel/data;chmod -R  600 /www/server/panel/config;chmod -R  700 /www/server/cron;chmod -R  600 /www/server/cron/*.log;chown -R root:root /www/server/panel/data;chown -R root:root /www/server/panel/config;chown -R root:root /www/server/phpmyadmin;chmod -R 755 /www/server/phpmyadmin")
    if os.path.exists("/www/server/mysql"):
        public.ExecShell("chown mysql:mysql /etc/my.cnf;chmod 600 /etc/my.cnf")
    public.ExecShell("rm -rf /www/server/panel/temp/*")
    stop_path = '/www/server/stop'
    if not os.path.exists(stop_path):
        os.makedirs(stop_path)
    public.ExecShell("chown -R root:root {path};chmod -R 755 {path}".format(path=stop_path))
    public.ExecShell('chmod 755 /www;chmod 755 /www/server')
    if os.path.exists('/www/server/phpmyadmin/pma'):
        public.ExecShell("rm -rf /www/server/phpmyadmin/pma")
    if os.path.exists("/www/server/adminer"):
        public.ExecShell("rm -rf /www/server/adminer")
    if os.path.exists("/www/server/panel/adminer"):
        public.ExecShell("rm -rf /www/server/panel/adminer")
    if os.path.exists('/dev/shm/session.db'):
        os.remove('/dev/shm/session.db')

    # 删除静态文件缓存
    compress_cache_path = "{}/temp/compress_caches".format(public.get_panel_path())
    if os.path.exists(compress_cache_path):
        public.ExecShell("rm -rf {}".format(compress_cache_path))

    node_service_bin = '/usr/bin/nodejs-service'
    node_service_src = '/www/server/panel/script/nodejs-service.py'
    if os.path.exists(node_service_src): public.ExecShell("chmod 700 " + node_service_src)
    if not os.path.exists(node_service_bin):
        if os.path.exists(node_service_src):
            public.ExecShell("ln -sf {} {}".format(node_service_src,node_service_bin))

    # 修复wordpress专版伪静态文件不存在导致的nginx配置错误
    o_file = os.path.join(public.get_panel_path(),'data/o.pl')
    if os.path.exists(o_file): 
        res = public.ReadFile(o_file)
        # 只针对tencent环境
        if res and res == 'tencent':
            wordpress_rewrite = '''location / {
    try_files $uri $uri/ /index.php?$args;
}'''
            wordpress_local_rewrite_file = os.path.join(public.get_panel_path(),'vhost/rewrite/wordpress.local.conf')
            if not os.path.exists(wordpress_local_rewrite_file):
                public.writeFile(wordpress_local_rewrite_file,wordpress_rewrite)
            else:
                conf = os.path.getsize(wordpress_local_rewrite_file)
                if conf < 10:
                    public.writeFile(wordpress_local_rewrite_file,wordpress_rewrite)

    # 修复urllib3版本过高导致的requests模块无法使用问题
    try:
        import urllib3
        if urllib3.__version__ >= '2.0.0':
            public.ExecShell("nohup {python_bin} -m pip uninstall urllib3 && {python_bin} -m pip install urllib3==1.25.11 -i https://pypi.tuna.tsinghua.edu.cn/simple/ &>/dev/null &".format(python_bin=public.get_python_bin()))
    except:
        public.ExecShell("nohup {} -m pip install urllib3==1.25.11 -i https://pypi.tuna.tsinghua.edu.cn/simple/ &>/dev/null &".format(public.get_python_bin()))


def sql_pacth():
    sql = db.Sql().dbfile('system')
    if not sql.table('sqlite_master').where('type=? AND name=?', ('table', 'load_average')).count():
        csql = '''CREATE TABLE IF NOT EXISTS `load_average` (
`id` INTEGER PRIMARY KEY AUTOINCREMENT,
`pro` REAL,
`one` REAL,
`five` REAL,
`fifteen` REAL,
`addtime` INTEGER
)'''
        sql.execute(csql,())
    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'sites','%type_id%')).count():
        public.M('sites').execute("alter TABLE sites add type_id integer DEFAULT 0",())

    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'database_servers','%db_type%')).count():
        public.M('databases').execute("alter TABLE database_servers add db_type REAL DEFAULT 'mysql'",())

    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'sites','%edate%')).count():
        public.M('sites').execute("alter TABLE sites add edate integer DEFAULT '0000-00-00'",())

    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'sites','%project_type%')).count():
        public.M('sites').execute("alter TABLE sites add project_type STRING DEFAULT 'PHP'",())

    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'sites','%project_config%')).count():
        public.M('sites').execute("alter TABLE sites add project_config STRING DEFAULT '{}'",())

    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'backup','%ps%')).count():
        public.M('backup').execute("alter TABLE backup add ps STRING DEFAULT '无'",())

    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'databases','%db_type%')).count():
        public.M('databases').execute("alter TABLE databases add db_type integer DEFAULT '0'",())

    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'databases','%conn_config%')).count():
        public.M('databases').execute("alter TABLE databases add conn_config STRING DEFAULT '{}'",())

    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'databases','%sid%')).count():
        public.M('databases').execute("alter TABLE databases add sid integer DEFAULT 0",())

    ndb = public.M('databases').order("id desc").field('id,pid,name,username,password,accept,ps,addtime,type').select()
    if type(ndb) == str: public.M('databases').execute("alter TABLE databases add type TEXT DEFAULT MySQL",())

    # 计划任务表处理
    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'crontab','%status%')).count():
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'status' INTEGER DEFAULT 1",())
    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'crontab','%save%')).count():
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'save' INTEGER DEFAULT 3",())
    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'crontab','%backupTo%')).count():
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'backupTo' TEXT DEFAULT off",())
    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'crontab','%sName%')).count():
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sName' TEXT",())
    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'crontab','%sBody%')).count():
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sBody' TEXT",())
    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'crontab','%sType%')).count():
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sType' TEXT",())
    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'crontab','%urladdress%')).count():
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'urladdress' TEXT",())
    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'crontab','%save_local%')).count():
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'save_local' INTEGER DEFAULT 0",())
    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'crontab','%notice%')).count():
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'notice' INTEGER DEFAULT 0",())
    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'crontab','%notice_channel%')).count():
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'notice_channel' TEXT DEFAULT ''",())

    sql = db.Sql()
    if not sql.table('sqlite_master').where('type=? AND name=?', ('table', 'site_types')).count():
        csql = '''CREATE TABLE IF NOT EXISTS `site_types` (
`id` INTEGER PRIMARY KEY AUTOINCREMENT,
`name` REAL,
`ps` REAL
)'''

        sql.execute(csql,())

    if not sql.table('sqlite_master').where('type=? AND name=?', ('table', 'download_token')).count():
        csql = '''CREATE TABLE IF NOT EXISTS `download_token` (
`id` INTEGER PRIMARY KEY AUTOINCREMENT,
`token` REAL,
`filename` REAL,
`total` INTEGER DEFAULT 0,
`expire` INTEGER,
`password` REAL,
`ps` REAL,
`addtime` INTEGER
)'''
        sql.execute(csql,())


    if not sql.table('sqlite_master').where('type=? AND name=?', ('table', 'messages')).count():
        csql = '''CREATE TABLE IF NOT EXISTS `messages` (
`id` INTEGER PRIMARY KEY AUTOINCREMENT,
`level` TEXT,
`msg` TEXT,
`state` INTEGER DEFAULT 0,
`expire` INTEGER,
`addtime` INTEGER
)'''
        sql.execute(csql,())

    if not sql.table('sqlite_master').where('type=? AND name=?', ('table', 'temp_login')).count():
        csql = '''CREATE TABLE IF NOT EXISTS `temp_login` (
`id` INTEGER PRIMARY KEY AUTOINCREMENT,
`token` REAL,
`salt` REAL,
`state` INTEGER,
`login_time` INTEGER,
`login_addr` REAL,
`logout_time` INTEGER,
`expire` INTEGER,
`addtime` INTEGER
)'''
        sql.execute(csql,())

    if not sql.table('sqlite_master').where('type=? AND name=?', ('table', 'database_servers')).count():
        csql = '''CREATE TABLE IF NOT EXISTS `database_servers` (
`id` INTEGER PRIMARY KEY AUTOINCREMENT,
`db_host` REAL,
`db_port` REAL,
`db_user` INTEGER,
`db_password` INTEGER,
`ps` REAL,
`addtime` INTEGER
)'''
        sql.execute(csql,())

    if not sql.table('sqlite_master').where('type=? AND name=?', ('table', 'security')).count():
        csql = '''CREATE TABLE IF NOT EXISTS `security` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `type` TEXT,
    `log` TEXT,
    `addtime` INTEGER DEFAULT 0
    )'''
        sql.execute(csql, ())


    test_ping()
    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'logs','%username%')).count():
        public.M('logs').execute("alter TABLE logs add uid integer DEFAULT '1'",())
        public.M('logs').execute("alter TABLE logs add username TEXT DEFAULT 'system'",())

    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'crontab','%status%')).count():
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'status' INTEGER DEFAULT 1",())
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'save' INTEGER DEFAULT 3",())
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'backupTo' TEXT DEFAULT off",())
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sName' TEXT",())
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sBody' TEXT",())
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sType' TEXT",())
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'urladdress' TEXT",())

    public.M('users').where('email=? or email=?',(public.en_hexb('4d6a67334f5459794e545932514846784c6d4e7662513d3d'),public.en_hexb('59573133587a49344e7a6b324d6a55324e6b42786353356a6232303d'))).setField('email','test@message.com')

    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'users','%salt%')).count():
        public.M('users').execute("ALTER TABLE 'users' ADD 'salt' TEXT",())


    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'messages','%retry_num%')).count():
        public.M('messages').execute("alter TABLE messages add send integer DEFAULT 0",())
        public.M('messages').execute("alter TABLE messages add retry_num integer DEFAULT 0",())


def upgrade_gevent():
    '''
        @name 升级gevent
        @author hwliang
        @return void
    '''
    tip_file = '{}/data/upgrade_gevent.lock'.format(public.get_panel_path())
    upgrade_script_file = '{}/script/upgrade_gevent.sh'.format(public.get_panel_path())
    if os.path.exists(upgrade_script_file) and not os.path.exists(tip_file):
        public.writeFile(tip_file,'1')
        os.system("bash {}".format(upgrade_script_file))
        if os.path.exists(tip_file): os.remove(tip_file)


def deb_bashrc():
    '''
        @name 针对debian/ubuntu未调用bashrc导致的问题
        @author hwliang
        @return void
    '''
    bashrc = '/root/.bashrc'
    bash_profile = '/root/.bash_profile'
    apt_get = '/usr/bin/apt-get'
    if not os.path.exists(apt_get): return
    if not os.path.exists(bashrc): return
    if not os.path.exists(bash_profile): return

    profile_body = public.readFile(bash_profile)
    if not isinstance(profile_body,str): return
    if profile_body.find('.bashrc') == -1:
        public.writeFile(bash_profile,'source ~/.bashrc\n' + profile_body.strip() + "\n")



def remove_other():
    rm_files = [
        "class/pluginAuth.so",
        "class/pluginAuth.cpython-310-x86_64-linux-gnu.so",
        "class/pluginAuth.cpython-310-aarch64-linux-gnu.so",
        "class/pluginAuth.cpython-37m-i386-linux-gnu.so",
        "class/pluginAuth.cpython-37m-loongarch64-linux-gnu.so",
        "class/pluginAuth.cpython-37m-aarch64-linux-gnu.so",
        "class/pluginAuth.cpython-37m-x86_64-linux-gnu.so",
        "class/pluginAuth.cpython-37m.so",
        "class/libAuth.loongarch64.so",
        "class/libAuth.x86.so",
        "class/libAuth.x86-64.so",
        "class/libAuth.glibc-2.14.x86_64.so",
        "class/libAuth.aarch64.so",
        "script/check_files.py"
    ]

    for f in rm_files:
        if os.path.exists(f):
            os.remove(f)



def null_html():
    null_files = ['/www/server/nginx/html/index.html','/www/server/apache/htdocs/index.html','/www/server/panel/data/404.html']
    null_new_body='''<html>
<head><title>404 Not Found</title></head>
<body>
<center><h1>404 Not Found</h1></center>
<hr><center>nginx</center>
</body>
</html>'''
    for null_file in null_files:
        if not os.path.exists(null_file): continue

        null_body = public.readFile(null_file)
        if not null_body: continue
        if null_body.find('没有找到站点') != -1 or null_body.find('您请求的文件不存在') != -1:
            public.writeFile(null_file,null_new_body)


def check_default_curl_file():
    default_file = '{}/data/default_curl.pl'.format(public.get_panel_path())
    if os.path.exists(default_file):
        default_curl_body = public.readFile(default_file)
        if default_curl_body:
            public.WriteFile(default_file,default_curl_body.strip())

def sync_node_list():
    import config
    config.config().sync_cloud_node_list()

def set_php_cli_env():
    '''
        @name 设置php-cli环境变量
        @author hwliang<2021-09-07>
        @return void
    '''
    php_path = '/www/server/php'
    bashrc = '/root/.bashrc'
    if not os.path.exists(php_path): return
    if not os.path.exists(bashrc): return
    # 清理所有别名
    public.ExecShell('sed -i "/alias php/d" {}'.format(bashrc))
    bashrc_body = public.readFile(bashrc)
    if not bashrc_body: return

    # 设置默认环境变量版本别名
    env_php_bin = '/usr/bin/php'
    if os.path.exists(env_php_bin):
        if os.path.islink(env_php_bin):
            php_cli_ini = "/etc/php-cli.ini"
            if os.path.exists(php_cli_ini):
                bashrc_body += "alias php='php -c {}'\n".format(php_cli_ini)


    # 设置所有已安装的PHP版本环境变量和别名
    php_versions_list = public.get_php_versions()
    for php_version in php_versions_list:
        php_ini = "{}/{}/etc/php.ini".format(php_path,php_version)
        php_cli_ini = "{}/{}/etc/php-cli.ini".format(php_path,php_version)
        env_php_bin = "/usr/bin/php{}".format(php_version)
        php_bin = "{}/{}/bin/php".format(php_path,php_version)
        php_ize = '/usr/bin/php{}-phpize'.format(php_version)
        php_ize_src = "{}/{}/bin/phpize".format(php_path,php_version)
        php_fpm = '/usr/bin/php{}-php-fpm'.format(php_version)
        php_fpm_src = "{}/{}/sbin/php-fpm".format(php_path,php_version)
        php_pecl = '/usr/bin/php{}-pecl'.format(php_version)
        php_pecl_src = "{}/{}/bin/pecl".format(php_path,php_version)
        php_pear = '/usr/bin/php{}-pear'.format(php_version)
        php_pear_src = "{}/{}/bin/pear".format(php_path,php_version)
        php_composer = '/usr/bin/php{}-composer'.format(php_version)
        php_composer_src = "{}/{}/bin/composer".format(php_path,php_version)

        if os.path.exists(php_bin):
            # 设置每个版本的环境变量
            if not os.path.exists(env_php_bin): os.symlink(php_bin,env_php_bin)
            if not os.path.exists(php_ize) and os.path.exists(php_ize_src): os.symlink(php_ize_src,php_ize)
            if not os.path.exists(php_fpm) and os.path.exists(php_fpm_src): os.symlink(php_fpm_src,php_fpm)
            if not os.path.exists(php_pecl) and os.path.exists(php_pecl_src): os.symlink(php_pecl_src,php_pecl)
            if not os.path.exists(php_pear) and os.path.exists(php_pear_src): os.symlink(php_pear_src,php_pear)
            if not os.path.exists(php_composer) and os.path.exists(php_composer_src): os.symlink(php_composer_src,php_composer)

            public.ExecShell("\cp -f {} {}".format(php_ini,php_cli_ini)) # 每次复制新的php.ini到php-cli.ini
            public.ExecShell('sed -i "/disable_functions/d" {}'.format(php_cli_ini)) # 清理禁用函数
            bashrc_body += "alias php{}='php{} -c {}'\n".format(php_version,php_version,php_cli_ini) # 设置别名
        else:
            # 清理已卸载的环境变量
            if os.path.islink(env_php_bin): os.remove(env_php_bin)
            if os.path.islink(php_ize): os.remove(php_ize)
            if os.path.islink(php_fpm): os.remove(php_fpm)
            if os.path.islink(php_pecl): os.remove(php_pecl)
            if os.path.islink(php_pear): os.remove(php_pear)
            if os.path.islink(php_composer): os.remove(php_composer)

    public.writeFile(bashrc,bashrc_body)


def check_enable_php():
    '''
        @name 检查nginx下的php配置文件
    '''
    php_versions = public.get_php_versions()
    ngx_php_conf = public.get_setup_path() + '/nginx/conf/enable-php-00.conf'
    public.writeFile(ngx_php_conf,'')
    for php_v in php_versions:
        ngx_php_conf = public.get_setup_path() + '/nginx/conf/enable-php-{}.conf'.format(php_v)
        if os.path.exists(ngx_php_conf): continue
        enable_conf = '''
    location ~ [^/]\.php(/|$)
	{{
		try_files $uri =404;
		fastcgi_pass  unix:/tmp/php-cgi-{}.sock;
		fastcgi_index index.php;
		include fastcgi.conf;
		include pathinfo.conf;
	}}
    '''.format(php_v)
        public.writeFile(ngx_php_conf,enable_conf)



def write_run_script_log(_log,rn='\n'):
    _log_file = '/www/server/panel/logs/run_script.log'
    public.writeFile(_log_file,_log + rn,'a+')


def run_script():
    try:
        os.system("{} {}/script/run_script.py".format(public.get_python_bin(),public.get_panel_path()))
        run_tip = '/dev/shm/bt.pl'
        if os.path.exists(run_tip): return
        public.writeFile(run_tip,str(time.time()))
        uptime = float(public.readFile('/proc/uptime').split()[0])
        if uptime > 1800: return
        run_config ='/www/server/panel/data/run_config'
        script_logs = '/www/server/panel/logs/script_logs'
        if not os.path.exists(run_config):
            os.makedirs(run_config,384)
        if not os.path.exists(script_logs):
            os.makedirs(script_logs,384)

        for sname in os.listdir(run_config):
            script_conf_file = '{}/{}'.format(run_config,sname)
            if not os.path.exists(script_conf_file): continue
            script_info = json.loads(public.readFile(script_conf_file))
            exec_log_file = '{}/{}'.format(script_logs,sname)

            if not os.path.exists(script_info['script_file']) \
                or script_info['script_file'].find('/www/server/panel/plugin/') != 0 \
                    or not re.match('^\w+$',script_info['script_file']):
                os.remove(script_conf_file)
                if os.path.exists(exec_log_file): os.remove(exec_log_file)
                continue


            if script_info['script_type'] == 'python':
                _bin = public.get_python_bin()
            elif script_info['script_type'] == 'bash':
                _bin = '/usr/bin/bash'
                if not os.path.exists(_bin): _bin = 'bash'

            exec_script = 'nohup {} {} &> {} &'.format(_bin,script_info['script_file'],exec_log_file)
            public.ExecShell(exec_script)
            script_info['last_time'] = time.time()
            public.writeFile(script_conf_file,json.dumps(script_info))
    except:
        pass


def clear_fastcgi_safe():
    try:
        fastcgifile = '/www/server/nginx/conf/fastcgi.conf'
        if os.path.exists(fastcgifile):
            conf = public.readFile(fastcgifile)
            if conf.find('bt_safe_open') != -1:
                public.ExecShell('sed -i "/bt_safe_open/d" {}'.format(fastcgifile))
                public.ExecShell('/etc/init.d/nginx reload')
    except:
        pass

#设置文件权限
def files_set_mode():
    # 24小时内设置过权限则不再设置
    tips_file = '/tmp/last_files_set_mode.pl'
    if os.path.exists(tips_file):
        if time.time() - os.path.getmtime(tips_file) < 86400: return
    rr = {True:'-R',False:''}
    m_paths = [
        ["/www/server/total","/*.lua","root",755,False],
        ["/www/server/total","/*.json","root",755,False],
        ["/www/server/total/logs","","www",755,True],
        ["/www/server/total/total","","www",755,True],
        ["/www/server/speed","/*.lua","root",755,False],
        ["/www/server/speed/total","","www",755,True],
        ["/www/server/btwaf","/*.lua","root",755,False],
        ["/www/backup","","root",600,True],
        ["/www/panel-static","","root",755,True],
        ["/www/enterprise_backup","","root",600,True],
        ["/www/server/cron","","root",700,True],
        ["/www/server/cron","/*.log","root",600,True],
        ["/www/server/stop","","root",755,True],
        ["/www/server/redis","","redis",700,True],
        ["/www/server/redis/redis.conf","","redis",600,False],
        ["/www/server/panel/class","","root",600,True],
        ["/www/server/panel/data","","root",600,True],
        ["/www/server/panel/plugin","","root",600,False],
        ["/www/server/panel/BTPanel","","root",755,True],
        ["/www/server/panel/vhost","","root",600,True],
        ["/www/server/panel/rewrite","","root",600,True],
        ["/www/server/panel/config","","root",600,True],
        ["/www/server/panel/backup","","root",600,True],
        ["/www/server/panel/package","","root",600,True],
        ["/www/server/panel/script","","root",700,True],
        ["/www/server/panel/temp","","root",600,True],
        ["/www/server/panel/tmp","","root",600,True],
        ["/www/server/panel/ssl","","root",600,True],
        ["/www/server/panel/install","","root",600,True],
        ["/www/server/panel/logs","","root",600,True],
        ["/www/server/panel/BT-Panel","","root",700,False],
        ["/www/server/panel/BT-Task","","root",700,False],
        ["/www/server/panel","/*.py","root",600,False],
        ["/www/server/panel","","root",755,False],
        ["/www/server/panel/BTPanel/__init__.py","","root",600,False],
        ["/www/server/panel/BTPanel/templates","","root",600,True],
        ["/dev/shm/session.db","","root",600,False],
        ["/dev/shm/session_py3","","root",600,True],
        ["/dev/shm/session_py2","","root",600,True],
        ["/www/server/phpmyadmin","","root",755,True],
        ["/www/server/coll","","root",700,True],
        ["/www/server/panel/init.sh","","root",600,False],
        ["/www/server/panel/license.txt","","root",600,False],
        ["/www/server/panel/requirements.txt","","root",600,False],
        ["/www/server/panel/update.sh","","root",600,False],
        ["/www/server/panel/default.pl","","root",600,False],
        ["/www/server/panel/hooks","","root",600,True],
        ["/www/server/panel/cache","","root",600,True],
        ["/root","","root",550,False],
        ["/root/.ssh","","root",700,False],
        ["/root/.ssh/authorized_keys","","root",600,False],
        ["/root/.ssh/id_rsa.pub","","root",644,False],
        ["/root/.ssh/id_rsa","","root",600,False],
        ["/root/.ssh/known_hosts","","root",644,False]
    ]

    recycle_list = public.get_recycle_bin_list()
    for recycle_path in recycle_list:
        m_paths.append([recycle_path,'','root',600,False])

    for m in m_paths:
        if not os.path.exists(m[0]): continue
        path = m[0] + m[1]
        public.ExecShell("chown {R} {U}:{U} {P}".format(P=path,U=m[2],R=rr[m[4]]))
        public.ExecShell("chmod {R} {M} {P}".format(P=path,M=m[3],R=rr[m[4]]))
        if m[1]:
            public.ExecShell("chown {U}:{U} {P}".format(P=m[0],U=m[2],R=rr[m[4]]))
            public.ExecShell("chmod {M} {P}".format(P=m[0],M=m[3],R=rr[m[4]]))

    set_www_logs_mode()
    # 移除面板目录下所有文件的所属组、其它用户的写权限
    public.ExecShell("nohup chmod -R go-w /www/server/panel &")
    # 标记文件设置时间
    public.writeFile(tips_file,str(time.time()))


def set_www_logs_mode():
    public.ExecShell("chown {U}:{U} {P}".format(P="/www/wwwlogs", U="www"))
    public.ExecShell("chmod {M} {P}".format(M=701, P="/www/wwwlogs"))
    for path in os.listdir("/www/wwwlogs"):
        if path in ("go", "java", "other", "nodejs", "python"):
            for root, dirs, files in os.walk("/www/wwwlogs/" + path):
                public.ExecShell("chown {U}:{U} {P}".format(P=root, U="www"))
                public.ExecShell("chmod {M} {P}".format(P=root, M=701))
        else:
            public.ExecShell("chown -R {U}:{U} {P}".format(P="/www/wwwlogs/" + path, U="www"))
            public.ExecShell("chmod -R {M} {P}".format(P="/www/wwwlogs/" + path, M=700))


#获取PMA目录
def get_pma_path():
    pma_path = '/www/server/phpmyadmin'
    if not os.path.exists(pma_path): return False
    for filename in os.listdir(pma_path):
        filepath = pma_path + '/' + filename
        if os.path.isdir(filepath):
            if filename[0:10] == 'phpmyadmin':
                return str(filepath)
    return False


#处理phpmyadmin访问权限
def set_pma_access():
    try:
        pma_path = get_pma_path()
        if not pma_path: return False
        if not os.path.exists(pma_path): return False
        pma_tmp = pma_path + '/tmp'
        if not os.path.exists(pma_tmp):
            os.makedirs(pma_tmp)

        nginx_file = '/www/server/nginx/conf/nginx.conf'
        if os.path.exists(nginx_file):
            nginx_conf = public.readFile(nginx_file)
            if nginx_conf.find('/tmp/') == -1:
                r_conf = '''/www/server/phpmyadmin;
            location ~ /tmp/ {
                return 403;
            }'''

                nginx_conf = nginx_conf.replace('/www/server/phpmyadmin;',r_conf)
                public.writeFile(nginx_file,nginx_conf)
                public.serviceReload()

        apa_pma_tmp = pma_tmp + '/.htaccess'
        if not os.path.exists(apa_pma_tmp):
            r_conf = '''order allow,deny
    deny from all'''
            public.writeFile(apa_pma_tmp,r_conf)
            public.set_mode(apa_pma_tmp,755)
            public.set_own(apa_pma_tmp,'root')

        public.ExecShell("chmod -R 700 {}".format(pma_tmp))
        public.ExecShell("chown -R www:www {}".format(pma_tmp))
        return True
    except:
        return False





#尝试升级到独立环境
def update_py37():
    pyenv='/www/server/panel/pyenv/bin/python3'
    pyenv_exists='/www/server/panel/data/pyenv_exists.pl'
    if os.path.exists(pyenv) or os.path.exists(pyenv_exists): return False
    download_url = public.get_url()
    public.ExecShell("nohup curl {}/install/update_panel.sh|bash &>/tmp/panelUpdate.pl &".format(download_url))
    public.writeFile(pyenv_exists,'True')
    return True

def test_ping():
    _f = '/www/server/panel/data/ping_token.pl'
    if os.path.exists(_f): os.remove(_f)
    try:
        import panelPing
        panelPing.Test().create_token()
    except:
        pass

#检查dnsapi
def check_dnsapi():
    dnsapi_file = 'config/dns_api.json'
    tmp = public.readFile(dnsapi_file)
    if not tmp: return False
    dnsapi = json.loads(tmp)
    if tmp.find('CloudFlare') == -1:
        cloudflare = {
                        "ps": "使用CloudFlare的API接口自动解析申请SSL",
                        "title": "CloudFlare",
                        "data": [{
                            "value": "",
                            "key": "SAVED_CF_MAIL",
                            "name": "E-Mail"
                        }, {
                            "value": "",
                            "key": "SAVED_CF_KEY",
                            "name": "API Key"
                        }],
                        "help": "CloudFlare后台获取Global API Key",
                        "name": "CloudFlareDns"
                    }
        dnsapi.insert(0,cloudflare)
    check_names = {"dns_bt":"Dns_com","dns_dp":"DNSPodDns","dns_ali":"AliyunDns","dns_cx":"CloudxnsDns"}
    for i in range(len(dnsapi)):
        if dnsapi[i]['name'] in check_names:
            dnsapi[i]['name'] = check_names[dnsapi[i]['name']]

    public.writeFile(dnsapi_file,json.dumps(dnsapi))
    return True



#检测端口放行是否同步(仅firewalld)
def check_firewall():
    try:
        if not os.path.exists('/usr/sbin/firewalld'): return False
        data = public.M('firewall').field('port,ps').select()
        import firewalld,firewalls
        fs = firewalls.firewalls()
        accept_ports = firewalld.firewalld().GetAcceptPortList()

        port_list = []
        for port_info  in accept_ports:
            if port_info['port'] in port_list:
                continue
            port_list.append(port_info['port'])

        n = 0
        for p in data:
            if p['port'].find('.') != -1:
                continue
            if p['port'] in port_list:
                continue
            fs.AddAcceptPortAll(p['port'],p['ps'])
            n+=1
        #重载
        if n: fs.FirewallReload()
    except:
        pass


#尝试启动新架构
def run_new():
    try:
        new_file = '/www/server/panel/data/new.pl'
        port_file = '/www/server/panel/data/port.pl'
        if os.path.exists(new_file): return False
        if not os.path.exists(port_file): return False
        port = public.readFile(port_file)
        if not port: return False

        # 2024/10/21 17:07 增加多一种方式检查是否已经启动，减少lsof调用的开销
        import psutil
        p_in = any("BT-Panel" in p.name() for p in psutil.process_iter(attrs=['name']))
        if p_in: return False

        cmd_line = public.ExecShell('lsof -P -i:{}|grep LISTEN|grep -v grep'.format(int(port)))[0]
        if len(cmd_line) < 20: return False
        if cmd_line.find('BT-Panel') != -1: return False
        public.writeFile('/www/server/panel/data/restart.pl','True')
        public.writeFile(new_file,'True')
        return True
    except:
        if os.path.exists("/www/server/panel/data/debug.pl"):
            import traceback
            public.print_log(traceback.format_exc())
        return False

#清理webhook日志
def clean_hook_log():
    path = '/www/server/panel/plugin/webhook/script'
    if not os.path.exists(path): return False
    for name in os.listdir(path):
        if name[-4:] != ".log": continue
        clean_max_log(path+'/' + name,524288)

#清理PHP日志
def clean_php_log():
    path = '/www/server/php'
    if not os.path.exists(path): return False
    php_list=public.get_php_versions()
    for name in os.listdir(path):
        if name not in php_list:continue
        filename = path +'/'+name + '/var/log/php-fpm.log'
        if os.path.exists(filename): clean_max_log(filename)
        filename = path +'/'+name + '/var/log/php-fpm-test.log'
        if os.path.exists(filename): clean_max_log(filename)
        filename =  path +'/'+name + '/var/log/slow.log'
        if os.path.exists(filename): clean_max_log(filename)

#清理大日志
def clean_max_log(log_file,max_size = 104857600,old_line = 100):
    if not os.path.exists(log_file): return False
    if os.path.getsize(log_file) > max_size:
        try:
            old_body = public.GetNumLines(log_file,old_line)
            public.writeFile(log_file,old_body)
        except:
            print(public.get_error_info())


def clean_node_log():
    # tcp/http/udp 负载日志
    import datetime
    today = datetime.date.today()
    log_name_regexp = re.compile(r"(proxy_access|tcp_load)\.log\.(?P<date>\d{4}-\d{2}-\d{2})\.csv")
    for i in ("logs", "tcp_logs"):
        log_dir = public.get_logs_path() + "/load_balancing/" + i
        if not os.path.isdir(log_dir):
            continue
        for name in os.listdir(log_dir):
            load_log_dir = log_dir + "/" + name
            if not os.path.isdir(load_log_dir):
                continue
            for f_name in os.listdir(load_log_dir):
                re_ret = log_name_regexp.search(f_name)
                log_file = load_log_dir + "/" + f_name
                if not re_ret or not os.path.isfile(log_file):
                    continue
                try:
                    the_date = datetime.date.fromisoformat(re_ret.group('date'))
                    if the_date + datetime.timedelta(days=7) < today:
                        os.remove(log_file)
                except:
                    pass

    # 文件互传日志
    task_list=public.M("transfer_tasks").where(
        "status in (?,?)", ("failed", "complete")
    ).order("task_id DESC").limit(1, 5).select()  # 只保留最近的5条数据, 从第6条开始的数据都删掉

    if task_list and isinstance(task_list, list) and "task_id" in task_list[0]:
        task_id = task_list[0]["task_id"]
        public.M("transfer_tasks").where("task_id <=?", (task_id, )).delete()
        public.M("file_transfers").where("task_id <=?", (task_id, )).delete()


#删除tty1
def remove_tty1():
    file_path = '/etc/systemd/system/getty@tty1.service'
    if not os.path.exists(file_path): return False
    if not os.path.islink(file_path): return False
    if os.readlink(file_path) != '/dev/null': return False
    try:
        os.remove(file_path)
    except:pass


#默认禁用指定PHP函数
def disable_putenv(fun_name):
    try:
        is_set_disable = '/www/server/panel/data/disable_%s' % fun_name
        if os.path.exists(is_set_disable): return True
        php_vs = public.get_php_versions()
        php_ini = "/www/server/php/{0}/etc/php.ini"
        rep = "disable_functions\s*=\s*.*"
        for pv in php_vs:
            php_ini_path = php_ini.format(pv)
            if not os.path.exists(php_ini_path): continue
            php_ini_body = public.readFile(php_ini_path)
            tmp = re.search(rep,php_ini_body)
            if not tmp: continue
            disable_functions = tmp.group()
            if disable_functions.find(fun_name) != -1: continue
            print(disable_functions)
            php_ini_body = php_ini_body.replace(disable_functions,disable_functions+',%s' % fun_name)
            php_ini_body.find(fun_name)
            public.writeFile(php_ini_path,php_ini_body)
            public.phpReload(pv)
        public.writeFile(is_set_disable,'True')
        return True
    except: return False


#创建计划任务
def set_crond():
    try:
        echo = public.md5(public.md5('renew_lets_ssl_bt'))
        cron_id = public.M('crontab').where('echo=?',(echo,)).getField('id')

        import crontab
        args_obj = public.dict_obj()
        if not cron_id:
            cronPath = public.GetConfigValue('setup_path') + '/cron/' + echo
            shell = public.get_python_bin() + ' /www/server/panel/class/panelLets.py renew_lets_ssl'
            public.writeFile(cronPath,shell)
            args_obj.id = public.M('crontab').add('name,type,where1,where_hour,where_minute,echo,addtime,status,save,backupTo,sType,sName,sBody,urladdress',("续签Let's Encrypt证书",'day','','0','10',echo,time.strftime('%Y-%m-%d %X',time.localtime()),0,'','localhost','toShell','',shell,''))
            crontab.crontab().set_cron_status(args_obj)
        else:
            cron_path = public.get_cron_path()
            if os.path.exists(cron_path):
                cron_s = public.readFile(cron_path)
                if cron_s.find(echo) == -1:
                    public.M('crontab').where('echo=?',(echo,)).setField('status',0)
                    args_obj.id = cron_id
                    crontab.crontab().set_cron_status(args_obj)
    except:
        print(public.get_error_info())


#清理多余的session文件
def clean_session():
    try:
        session_path = r'/dev/shm/session_py' + str(sys.version_info[0])
        if not os.path.exists(session_path): return False
        now_time = time.time()
        p_time = 86400
        old_state = False
        for fname in os.listdir(session_path):
            filename = os.path.join(session_path,fname)
            if not os.path.exists(filename): continue
            modify_time = os.path.getmtime(filename)
            if (now_time - modify_time) > p_time:
                old_state = True
                break
        if old_state: public.ExecShell("rm -f " + session_path + '/*')
        return True
    except:return False

# 面板磁盘预留空间
def panel_create_chunk():
    chunk_file = "/www/reserve_space.pl"
    if os.path.isfile(chunk_file):
        return

    temp = public.ExecShell("df -T -P|grep '/'|grep -v tmpfs|grep -v 'snap/core'|grep -v udev")[0]
    diskInfo = []
    n = 0
    cuts = ['/mnt/cdrom', '/boot', '/boot/efi', '/dev', '/dev/shm', '/run/lock', '/run', '/run/shm', '/run/user']
    for tmp in temp.split('\n'):
        n += 1
        try:
            disk = re.findall(r"^(.+)\s+([\w\.]+)\s+([\w\.]+)\s+([\w\.]+)\s+([\w\.]+)\s+([\d%]{2,4})\s+(/.{0,100})$",
                              tmp.strip().replace(',', '.'))
            if disk: disk = disk[0]
            if len(disk) < 6: continue
            # if disk[2].find('M') != -1: continue
            if disk[2].find('K') != -1: continue
            if len(disk[6].split('/')) > 10: continue
            if disk[6] in cuts: continue
            if str(disk[6]).startswith("/snap"): continue
            if disk[6].find('docker') != -1: continue
            if disk[1].strip() in ['tmpfs']: continue
            arr = {
                'filesystem': disk[0].strip(),
                'type': disk[1].strip(),
                'path': disk[6].replace('/usr/local/lighthouse/softwares/btpanel', '/www')
            }
            tmp1 = [disk[2], disk[3], disk[4], disk[5]]
            arr['size'] = tmp1
            diskInfo.append(arr)
        except Exception as ex:
            public.WriteLog('信息获取', str(ex))
            continue

    www_free_size = None
    root_free_size = None
    for d in diskInfo:
        if d["path"] in ("/www", "/www/"):
            www_free_size = d["size"][2]
        if d["path"] == "/":
            root_free_size = d["size"][2]

    if www_free_size is None:
        free_size = root_free_size
    else:
        free_size = www_free_size

    if free_size is None:
        return

    try:
        free_size = int(free_size)
    except:
        return

    use_size = free_size * 0.05  # 取可用空间的5%
    if use_size > 512*1024*1024:
        use_size = 512*1024*1024

    num = int(use_size / 1024)
    with open(chunk_file, 'wb') as f:
        for i in range(num):
            f.write(b'\0' * 1024)

def ping_test():
    if os.system("ping -c 1 -w 1 100.100.100.200") == 0:
        server_store = "aliyun"
    elif os.system("ping -c 1 -w 1 metadata.tencentyun.com") == 0:
        server_store = "tencent"
    else:
        server_store = public.readFile("/www/server/panel/data/cloudthirdlogin.pl")
        if not server_store:
            server_store = "others"
    public.writeFile("/www/server/panel/data/server_store.pl", server_store)


def sync_default_msg_channel():
    if "/www/server/panel" not in sys.path:
        sys.path.append("/www/server/panel")

    try:
        from mod.base.msg import update_mod_push_msg
        os.remove("/www/server/panel/data/mod_push_data/update_sender.pl")
        update_mod_push_msg()
        # public.print_log("更新消息通道成功！")
    except:
        # public.print_log("更新消息通道失败！")
        pass

def update_python_project_env():
    """获取并更新python项目环境信息"""
    if "/www/server/panel" not in sys.path:
        sys.path.append("/www/server/panel")
    try:
        from mod.project.python.pyenv_tool import EnvironmentReporter
        EnvironmentReporter().init_report()
    except:
        public.print_error()
        pass


def update_pubsuffix_dat():
    try:
        from mod.base.pubsuffix import update_dat
        update_dat()
    except:
        public.print_error()


def check_docker_version():
    ver, error = public.ExecShell('/www/server/panel/pyenv/bin/python -c "import docker; print(docker.__version__.split(\'.\')[0])"')
    try:
        if error or int(ver) < 5:
            public.ExecShell('btpip install --upgrade docker')
    except:
        public.ExecShell('btpip install --upgrade docker')

def set_nginx_extension():
    tip_file = "{}/data/set_nginx_extension.pl".format(public.get_panel_path())
    if os.path.exists(tip_file):
        return
    if "/www/server/panel" not in sys.path:
        sys.path.insert(0, "/www/server/panel")

    if not os.path.exists("/www/server/nginx/sbin/nginx"):
        return

    if not public.get_webserver() == "nginx":
        return

    res = public.checkWebConfig()
    if res is not True:
        print("nginx配置文件异常，无法插入扩展配置！", flush=True)
        return
    try:
        from mod.base.web_conf import ng_ext

        sites = public.M('sites').field('id,name,project_type').select()
        change = False
        for site in sites:
            site_type = site['project_type']
            site_name = site['name']
            if site_type.lower() in ("php", "proxy", "wp2"):
                prefix = ""
            else:
                prefix = site_type.lower() + "_"

            ng_file = "{}/nginx/{}{}.conf".format(public.get_vhost_path(), prefix, site_name)
            ng_data = public.readFile(ng_file)
            if not ng_data:
                print(site_name, "没有配置文件: {}".format(ng_file))
                continue

            if ng_ext.has_extension(ng_data):
                print(site_name, "有扩展配置文件: {}".format(ng_file))
                continue

            ng_data_new = ng_ext.set_extension_by_config(site_name, ng_data)
            public.writeFile(ng_file, ng_data_new)
            if not public.checkWebConfig() is True:
                print("配置文件插入错误，已还原！\n", ng_data_new, public.checkWebConfig(), flush=True)
                public.writeFile(ng_file, ng_data)
            else:
                change=True
                print("插入配置成功：", site_name, flush=True)

        if change:
            public.ServiceReload()
            print("重启Nginx成功！", flush=True)

        public.writeFile(tip_file, "1")
        # setup_site_total()
    except:
        pass


def set_apache_extension():
    tip_file = "{}/data/set_apache_extension.pl".format(public.get_panel_path())
    if os.path.exists(tip_file):
        return
    if "/www/server/panel" not in sys.path:
        sys.path.insert(0, "/www/server/panel")

    print("开始设置Apache扩展配置...", flush=True)
    if not public.get_webserver() == "apache":
        return

    res = public.checkWebConfig()
    if res is not True:
        print("Apache配置文件异常，无法插入扩展配置！", flush=True)
        return

    try:
        from mod.base.web_conf import ap_ext

        sites = public.M('sites').field('id,name,project_type').select()
        change = False
        for site in sites:
            site_type = site['project_type']
            site_name = site['name']
            if site_type.lower() in ("php", "proxy", "wp2"):
                prefix = ""
            else:
                prefix = site_type.lower() + "_"

            ap_file = "{}/apache/{}{}.conf".format(public.get_vhost_path(), prefix, site_name)
            ap_data = public.readFile(ap_file)
            if not ap_data:
                print(site_name, "没有配置文件: {}".format(ap_file))
                continue

            if ap_ext.has_extension(ap_data):
                print(site_name, "有扩展配置文件: {}".format(ap_file))
                continue

            ng_data_new = ap_ext.set_extension_by_config(site_name, ap_data)
            public.writeFile(ap_file, ng_data_new)
            if not public.checkWebConfig() is True:
                print("配置文件插入错误，已还原！\n", ng_data_new, public.checkWebConfig(), flush=True)
                public.writeFile(ap_file, ap_data)
            else:
                change=True
                print("插入配置成功：", site_name, flush=True)

        if change:
            public.ServiceReload()
            print("重启Apache成功！", flush=True)

        public.writeFile(tip_file, "1")
        # setup_site_total()
    except:
        pass


def setup_site_total():
    from mod.base.free_site_total import SiteTotalService
    # s = SiteTotalService()
    # if not s.running():
    #     s.start()

    # 2025/11/17 修改free_site_total 安装逻辑， 使用一个记录文件，记录上次更新对应的面板更新时间，如果一致，则不更新，否则就更新
    if os.path.exists(SiteTotalService().stop_always_flags): # 存在则说明用户设置的是永久关闭
         return

    panel_path = public.get_panel_path()
    config_py = "{}/class/config.py".format(panel_path)
    last_install_file = "{}/data/free_site_total.pl".format(panel_path)
    config_content = public.readFile(config_py)
    match_ret = re.search(r'''version_number":\s*int\("(?P<upt>\d+)"\)''', config_content)
    update_time = -1
    if match_ret:
        try:
            update_time = int(match_ret.group("upt"))
        except:
            update_time = -1

    if not update_time:
        update_time = os.path.getmtime(config_py)

    last_install_time = 0
    if os.path.exists(last_install_file):
        try:
            last_install_time = int(public.readFile(last_install_file))
        except:
            pass

    if last_install_time == update_time:
        tmp_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_install_time))
        print("当前面板安装时间与free_site_total一致（{}），无需更新！".format(tmp_time), flush=True)
        return

    install_sh = "{} {}/script/free_total_update.py".format(public.get_python_bin(), panel_path)
    res = public.ExecShell(install_sh)
    print(res[0]+ res[1])
    print("free_site_total 安装成功！", flush=True)
    public.writeFile(last_install_file, str(update_time))


if __name__ == '__main__':
    stime = time.time()
    control_init()
    print("耗时：{:.2f}".format(time.time() - stime))


