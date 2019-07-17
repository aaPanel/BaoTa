#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------
import system,psutil,time,public,db,os,sys,json,py_compile,re
os.chdir('/www/server/panel')
sm = system.system();
taskConfig = json.loads(public.ReadFile('config/task.json'))

oldEdate = None

from BTPanel import cache

def control_init():
    sql = db.Sql().dbfile('system')
    csql = '''CREATE TABLE IF NOT EXISTS `load_average` (
`id` INTEGER PRIMARY KEY AUTOINCREMENT,
`pro` REAL,
`one` REAL,
`five` REAL,
`fifteen` REAL,
`addtime` INTEGER
)'''
    sql.execute(csql,())
    public.M('sites').execute("alter TABLE sites add edate integer DEFAULT '0000-00-00'",());
    public.M('sites').execute("alter TABLE sites add type_id integer DEFAULT 0",());

    sql = db.Sql()
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
    except:pass
    public.writeFile('/var/bt_setupPath.conf','/www')
    public.ExecShell(c)

    p_file = 'class/plugin2.so'
    if os.path.exists(p_file): public.ExecShell("rm -f class/*.so")
    public.ExecShell("chmod -R  600 /www/server/panel/data")
    public.ExecShell("chmod -R  600 /www/server/panel/config")
    public.ExecShell("chmod -R  700 /www/server/cron")
    public.ExecShell("chmod -R  600 /www/server/cron/*.log")
    public.ExecShell("chown -R root:root /www/server/panel/data")
    public.ExecShell("chown -R root:root /www/server/panel/config")
    disable_putenv('putenv')
    clean_session()
    set_crond()

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


#监控任务
def control_task():
    
    global sm,taskConfig
    if not taskConfig['control']['open']: return False
    day = taskConfig['control']['day'];
    if day < 1: 

        return False

    sql = db.Sql().dbfile('system')

    #取当前CPU Io
    cpuUsed = sm.get_cpu_percent()
    memUsed = get_mem_used()

    #取当前网络Io
    networkInfo = sm.GetNetWork(False)
            
    #取磁盘Io
    if os.path.exists('/proc/diskstats'):
        diskInfo = sm.get_io_info()

    
    addtime = int(time.time())
    deltime = addtime - (day * 86400)
            
    data = (cpuUsed,memUsed,addtime)
    sql.table('cpuio').add('pro,mem,addtime',data)
    sql.table('cpuio').where("addtime<?",(deltime,)).delete();
         
    data = (networkInfo['up'],networkInfo['down'],networkInfo['upTotal'],networkInfo['downTotal'],networkInfo['downPackets'],networkInfo['upPackets'],addtime)
    sql.table('network').add('up,down,total_up,total_down,down_packets,up_packets,addtime',data)
    sql.table('network').where("addtime<?",(deltime,)).delete();

    if os.path.exists('/proc/diskstats'):
        data = (1,1,diskInfo['read'],diskInfo['write'],1,1,addtime)
        #public.writeFile('/tmp/1.txt',str((time.time(),data)) + "\n",'a+')
        sql.table('diskio').add('read_count,write_count,read_bytes,write_bytes,read_time,write_time,addtime',data)
        sql.table('diskio').where("addtime<?",(deltime,)).delete();
                    
    #LoadAverage
    load_average = sm.GetLoadAverage(None)
    lpro = round((load_average['one'] / load_average['max']) * 100,2)
    if lpro > 100: lpro = 100;
    sql.table('load_average').add('pro,one,five,fifteen,addtime',(lpro,load_average['one'],load_average['five'],load_average['fifteen'],addtime))

    

#取内存使用率
def get_mem_used():
    mem = psutil.virtual_memory()
    memInfo = {'memTotal':mem.total/1024/1024,'memFree':mem.free/1024/1024,'memBuffers':mem.buffers/1024/1024,'memCached':mem.cached/1024/1024}
    tmp = memInfo['memTotal'] - memInfo['memFree'] - memInfo['memBuffers'] - memInfo['memCached']
    tmp1 = memInfo['memTotal'] / 100
    return int(tmp / tmp1)


#软件安装任务
def install_task():
    if cache.get('install_task'): return True
    if cache.get('install_exists'): return True
    sql = db.Sql()
    sql.table('tasks').where("status=?",('-1',)).setField('status','0')
    taskArr = sql.table('tasks').where("status=?",('0',)).field('id,type,execstr').order("id asc").select();
    cache.set('install_exists',True)
    cache.delete('install_task')
    logPath = '/tmp/panelExec.log'
    for value in taskArr:
        start = int(time.time());
        if not sql.table('tasks').where("id=?",(value['id'],)).count(): continue;
        sql.table('tasks').where("id=?",(value['id'],)).save('status,start',('-1',start))
        if value['type'] == 'download':
            import downloadFile
            argv = value['execstr'].split('|bt|')
            downloadFile.downloadFile().DownloadFile(argv[0],argv[1])
        elif value['type'] == 'execshell':
           os.system(value['execstr'] + " > " + logPath + " 2>&1")
        end = int(time.time())
        sql.table('tasks').where("id=?",(value['id'],)).save('status,end',('1',end))
    cache.delete('install_exists')

#网站到期处理
def site_end_task():
    global oldEdate
    if not oldEdate: oldEdate = public.readFile('data/edate.pl')
    if not oldEdate: oldEdate = '0000-00-00'
    mEdate = time.strftime('%Y-%m-%d',time.localtime())
    if oldEdate == mEdate: return False
    edateSites = public.M('sites').where('edate>? AND edate<? AND (status=? OR status=?)',('0000-00-00',mEdate,1,u'正在运行')).field('id,name').select()
    import panelSite,common
    siteObject = panelSite.panelSite()
    for site in edateSites:
        get = common.dict_obj()
        get.id = site['id']
        get.name = site['name']
        siteObject.SiteStop(get)
    oldEdate = mEdate
    public.writeFile('data/edate.pl',mEdate)



#PHP守护
def php_safe_task():
    if not os.path.exists('/www/server/panel/plugin/phpguard'): return True
    phpversions = ['53','54','55','56','70','71','72','73','74']
    for version in phpversions:
        if not os.path.exists('/etc/init.d/php-fpm-'+version): continue;
        if check_php_version(version): continue;
        if start_php_version(version):
            public.WriteLog('PHP守护程序','检测到PHP-' + version + '处理异常,已自动修复!')
            
#处理指定PHP版本   
def start_php_version(version):
    fpm = '/etc/init.d/php-fpm-'+version
    if not os.path.exists(fpm): return False;
        
    #尝试重载服务
    os.system(fpm + ' reload');
    if check_php_version(version): return True;
        
    #尝试重启服务
    cgi = '/tmp/php-cgi-'+version
    pid = '/www/server/php'+version+'/php-fpm.pid';
    os.system('pkill -9 php-fpm-'+version)
    time.sleep(0.5);
    if not os.path.exists(cgi): os.remove(cgi)
    if not os.path.exists(pid): os.remove(pid)
    os.system(fpm + ' start');
    if check_php_version(version): return True;
        
    #检查是否正确启动
    if os.path.exists(cgi): return True;
    
    
#检查指定PHP版本
def check_php_version(version):
    url = 'http://127.0.0.1/phpfpm_'+version+'_status';
    result = public.httpGet(url);
    #检查nginx
    if result.find('Bad Gateway') != -1: return False;
    #检查Apache
    if result.find('Service Unavailable') != -1: return False;
    if result.find('Not Found') != -1: check_phpinfo();
        
    #检查Web服务是否启动
    if result.find('Connection refused') != -1: 
        global isTask
        if os.path.exists(isTask): 
            isStatus = public.readFile(isTask);
            if isStatus == 'True': return True;
        filename = '/etc/init.d/nginx';
        if os.path.exists(filename): os.system(filename + ' start');
        filename = '/etc/init.d/httpd';
        if os.path.exists(filename): os.system(filename + ' start');
    return True;


#检测PHPINFO配置
def check_phpinfo():
    php_versions = ['53','54','55','56','70','71','72','73','74'];
    setupPath = '/www/server';
    path = setupPath +'/panel/vhost/nginx/phpinfo.conf';
    if not os.path.exists(path):
        opt = "";
        for version in php_versions:
            opt += "\n\tlocation /"+version+" {\n\t\tinclude enable-php-"+version+".conf;\n\t}";
        
        phpinfoBody = '''server
{
    listen 80;
    server_name 127.0.0.2;
    allow 127.0.0.1;
    index phpinfo.php index.html index.php;
    root  /www/server/phpinfo;
%s   
}''' % (opt,);
        public.writeFile(path,phpinfoBody);
    
    
    path = setupPath + '/panel/vhost/apache/phpinfo.conf';
    if not os.path.exists(path):
        opt = "";
        for version in php_versions:
            opt += """\n<Location /%s>
    SetHandler "proxy:unix:/tmp/php-cgi-%s.sock|fcgi://localhost"
</Location>""" % (version,version);
            
        phpinfoBody = '''
<VirtualHost *:80>
DocumentRoot "/www/server/phpinfo"
ServerAdmin phpinfo
ServerName 127.0.0.2
%s
<Directory "/www/server/phpinfo">
    SetOutputFilter DEFLATE
    Options FollowSymLinks
    AllowOverride All
    Order allow,deny
    Allow from all
    DirectoryIndex index.php index.html index.htm default.php default.html default.htm
</Directory>
</VirtualHost>
''' % (opt,);
        public.writeFile(path,phpinfoBody);



class JobsConfig:
    JOBS = []
    SCHEDULER_API_ENABLED = True
    def __init__(self):
        global taskConfig
        self.JOBS = taskConfig['JOBS']
