#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------
import time,public,db,os,sys,json,re
os.chdir('/www/server/panel')

def control_init():
    dirPath = '/www/server/phpmyadmin/pma'
    if os.path.exists(dirPath):
        public.ExecShell("rm -rf {}".format(dirPath))
    
    dirPath = '/www/server/adminer'
    if os.path.exists(dirPath):
        public.ExecShell("rm -rf {}".format(dirPath))
    
    dirPath = '/www/server/panel/adminer'
    if os.path.exists(dirPath):
        public.ExecShell("rm -rf {}".format(dirPath))


    time.sleep(1)
    
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
        public.M('sites').execute("alter TABLE sites add edate integer DEFAULT '0000-00-00'",())
        public.M('sites').execute("alter TABLE sites add type_id integer DEFAULT 0",())

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

    public.M('users').where('email=? or email=?',('287962566@qq.com','amw_287962566@qq.com')).setField('email','test@message.com')

    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'users','%salt%')).count():
        public.M('users').execute("ALTER TABLE 'users' ADD 'salt' TEXT",())

    public.chdck_salt()



    filename = '/www/server/nginx/off'
    if os.path.exists(filename): os.remove(filename)
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
    public.ExecShell("chmod -R  600 /www/server/panel/data;chmod -R  600 /www/server/panel/config;chmod -R  700 /www/server/cron;chmod -R  600 /www/server/cron/*.log;chown -R root:root /www/server/panel/data;chown -R root:root /www/server/panel/config;chown -R root:root /www/server/phpmyadmin;chmod -R 755 /www/server/phpmyadmin")
    if os.path.exists("/www/server/mysql"):
        public.ExecShell("chown mysql:mysql /etc/my.cnf;chmod 600 /etc/my.cnf")
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
    #disable_putenv('putenv')
    #clean_session()
    #set_crond()
    test_ping()
    clean_max_log('/www/server/panel/plugin/rsync/lsyncd.log')
    clean_max_log('/var/log/rsyncd.log',1024*1024*10)
    clean_max_log('/root/.pm2/pm2.log',1024*1024*20)
    remove_tty1()
    clean_hook_log()
    run_new()
    clean_max_log('/www/server/cron',1024*1024*5,20)
    #check_firewall()
    check_dnsapi()
    clean_php_log()
    #update_py37()
    files_set_mode()
    set_pma_access()
    # public.set_open_basedir()
    clear_fastcgi_safe()
    
    



    
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
        ["/www/wwwlogs","","www",700,True],
        ["/www/enterprise_backup","","root",600,True],
        ["/www/server/cron","","root",700,True],
        ["/www/server/cron","/*.log","root",600,True],
        ["/www/server/stop","","root",755,True],
        ["/www/server/redis","","redis",700,True],
        ["/www/server/redis/redis.conf","","redis",600,False],
        ["/www/Recycle_bin","","root",600,True],
        ["/www/server/panel/class","","root",600,True],
        ["/www/server/panel/data","","root",600,True],
        ["/www/server/panel/plugin","","root",600,False],
        ["/www/server/panel/BTPanel","","root",600,True],
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
        ["/dev/shm/session.db","","root",600,False],
        ["/dev/shm/session_py3","","root",600,True],
        ["/dev/shm/session_py2","","root",600,True],
        ["/www/server/phpmyadmin","","root",755,True],
        ["/www/server/coll","","root",700,True]
    ]

    for m in m_paths:
        if not os.path.exists(m[0]): continue
        path = m[0] + m[1]
        public.ExecShell("chown {R} {U}:{U} {P}".format(P=path,U=m[2],R=rr[m[4]]))
        public.ExecShell("chmod {R} {M} {P}".format(P=path,M=m[3],R=rr[m[4]]))
        if m[1]:
            public.ExecShell("chown {U}:{U} {P}".format(P=m[0],U=m[2],R=rr[m[4]]))
            public.ExecShell("chmod {M} {P}".format(P=m[0],M=m[3],R=rr[m[4]]))

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
    pyenv='/www/server/panel/pyenv/bin/python'
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
        cmd_line = public.ExecShell('lsof -P -i:{}|grep LISTEN|grep -v grep'.format(int(port)))[0]
        if len(cmd_line) < 20: return False
        if cmd_line.find('BT-Panel') != -1: return False
        public.writeFile('/www/server/panel/data/restart.pl','True')
        public.writeFile(new_file,'True')
        return True
    except:
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
    for name in os.listdir(path):
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
        php_vs = ('52','53','54','55','56','70','71','72','73','74')
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


