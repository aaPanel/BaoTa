#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------
import time,public,db,os,sys,json,re
os.chdir('/www/server/panel')
exec_tips = None
from BTPanel import cache

def control_init():
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
        public.M('sites').execute("alter TABLE sites add edate integer DEFAULT '0000-00-00'",());
        public.M('sites').execute("alter TABLE sites add type_id integer DEFAULT 0",());

    sql = db.Sql()
    if not sql.table('sqlite_master').where('type=? AND name=?', ('table', 'site_types')).count():
        csql = '''CREATE TABLE IF NOT EXISTS `site_types` (
`id` INTEGER PRIMARY KEY AUTOINCREMENT,
`name` REAL,
`ps` REAL
)'''

        sql.execute(csql,())

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
                os.system("chattr -i " + init_file)
                os.system("\cp -arf %s %s" % (src_file,init_file))
                os.system("chmod +x %s" % init_file)
    except:pass
    public.writeFile('/var/bt_setupPath.conf','/www')
    public.ExecShell(c)
    p_file = 'class/plugin2.so'
    if os.path.exists(p_file): public.ExecShell("rm -f class/*.so")
    public.ExecShell("chmod -R  600 /www/server/panel/data;chmod -R  600 /www/server/panel/config;chmod -R  700 /www/server/cron;chmod -R  600 /www/server/cron/*.log;chown -R root:root /www/server/panel/data;chown -R root:root /www/server/panel/config")
    #disable_putenv('putenv')
    clean_session()
    #set_crond()
    clean_max_log('/www/server/panel/plugin/rsync/lsyncd.log')
    remove_tty1()
    clean_hook_log()

#清理webhook日志
def clean_hook_log():
    path = '/www/server/panel/plugin/webhook/script'
    if not os.path.exists(path): return False
    for name in os.listdir(path):
        if name[-4:] != ".log": continue;
        clean_max_log(path+'/' + name,524288)

#清理PHP日志
def clean_php_log():
    path = '/www/server/panel/php'
    if not os.path.exists(path): return False
    for name in os.listdir(path):
        filename = path + '/var/log/php-fpm.log'
        if os.path.exists(filename): clean_max_log(filename)
        filename = path + '/var/log/slow.log'
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
            shell = 'python /www/server/panel/class/panelLets.py renew_lets_ssl'
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


