#!/bin/python
#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <2879625666@qq.com>
# +-------------------------------------------------------------------

#------------------------------
# 计划任务
#------------------------------

import sys
import os
from json import dumps,loads
from psutil import Process,pids,cpu_count,cpu_percent,net_io_counters,disk_io_counters,virtual_memory
sys.path.insert(0,"/www/server/panel/class/")
import db
import public
import time
import panelTask
import setPanelLets
global pre,timeoutCount,logPath,isTask,oldEdate,isCheck
pre = 0
timeoutCount = 0
isCheck = 0
oldEdate = None
logPath = '/tmp/panelExec.log'
isTask = '/tmp/panelTask.pl'

class MyBad():
    _msg = None
    def __init__(self,msg):
        self._msg = msg
    def __repr__(self):
        return self._msg
        

def ExecShell(cmdstring, cwd=None, timeout=None, shell=True):
    try:
        global logPath
        import shlex
        import datetime
        import subprocess
        import time
        sub = subprocess.Popen(cmdstring+' &> '+logPath, cwd=cwd, stdin=subprocess.PIPE,shell=shell,bufsize=4096)
        
        while sub.poll() is None:
            time.sleep(0.1)
                
        return sub.returncode
    except:
        return None

#下载文件
def DownloadFile(url,filename):
    try:
        import urllib,socket
        socket.setdefaulttimeout(10)
        urllib.urlretrieve(url,filename=filename ,reporthook= DownloadHook)
        public.ExecShell('chown www.www ' + filename)
        WriteLogs('done')
    except:
        WriteLogs('done')
        


#下载文件进度回调  
def DownloadHook(count, blockSize, totalSize):
    global pre
    used = count * blockSize
    pre1 = int((100.0 * used / totalSize))
    if pre == pre1:
        return
    speed = {'total':totalSize,'used':used,'pre':pre}
    WriteLogs(dumps(speed))
    pre = pre1

#写输出日志
def WriteLogs(logMsg):
    try:
        global logPath
        fp = open(logPath,'w+')
        fp.write(logMsg)
        fp.close()
    except:
        pass

#任务队列 
def startTask():
    global isTask
    try:
        while True:
            try:
                if os.path.exists(isTask):
                    sql = db.Sql()
                    sql.table('tasks').where("status=?",('-1',)).setField('status','0')
                    taskArr = sql.table('tasks').where("status=?",('0',)).field('id,type,execstr').order("id asc").select()
                    for value in taskArr:
                        start = int(time.time())
                        if not sql.table('tasks').where("id=?",(value['id'],)).count(): continue
                        sql.table('tasks').where("id=?",(value['id'],)).save('status,start',('-1',start))
                        if value['type'] == 'download':
                            argv = value['execstr'].split('|bt|')
                            DownloadFile(argv[0],argv[1])
                        elif value['type'] == 'execshell':
                            ExecShell(value['execstr'])
                        end = int(time.time())
                        sql.table('tasks').where("id=?",(value['id'],)).save('status,end',('1',end))
                        if(sql.table('tasks').where("status=?",('0')).count() < 1): 
                            ExecShell('rm -f ' + isTask)
            except:
                pass
            siteEdate()
            time.sleep(2)
    except:
        time.sleep(60)
        startTask()
        
#网站到期处理
def siteEdate():
    global oldEdate
    try:
        if not oldEdate: oldEdate = public.readFile('data/edate.pl')
        if not oldEdate: oldEdate = '0000-00-00'
        mEdate = time.strftime('%Y-%m-%d',time.localtime())
        if oldEdate == mEdate: return False
        edateSites = public.M('sites').where('edate>? AND edate<? AND (status=? OR status=?)',('0000-00-00',mEdate,1,u'正在运行')).field('id,name').select()
        import panelSite
        siteObject = panelSite.panelSite()
        for site in edateSites:
            get = MyBad('')
            get.id = site['id']
            get.name = site['name']
            siteObject.SiteStop(get)
        oldEdate = mEdate
        public.writeFile('data/edate.pl',mEdate)
    except:
         pass

def GetLoadAverage():
    c = os.getloadavg()
    data = {}
    data['one'] = float(c[0])
    data['five'] = float(c[1])
    data['fifteen'] = float(c[2])
    data['max'] = cpu_count() * 2
    data['limit'] = data['max']
    data['safe'] = data['max'] * 0.75
    return data
         

#系统监控任务
def systemTask():
    try:
        filename = 'data/control.conf'
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
        count = 0
        reloadNum=0
        network_up = network_down = diskio_1 = diskio_2 = networkInfo = cpuInfo = diskInfo = None
        while True:
            if not os.path.exists(filename):
                time.sleep(10)
                continue
            
            day = 30
            try:
                day = int(public.readFile(filename))
                if day < 1:
                    time.sleep(10)
                    continue
            except:
                day  = 30
            
            
            tmp = {}
            #取当前CPU Io     
            tmp['used'] = cpu_percent(interval=1)
            
            if not cpuInfo:
                tmp['mem'] = GetMemUsed()
                cpuInfo = tmp 
            
            if cpuInfo['used'] < tmp['used']:
                tmp['mem'] = GetMemUsed()
                cpuInfo = tmp 
            
            
            
            #取当前网络Io
            networkIo = net_io_counters()[:4]
            if not network_up:
                network_up   =  networkIo[0]
                network_down =  networkIo[1]
            tmp = {}
            tmp['upTotal']      = networkIo[0]
            tmp['downTotal']    = networkIo[1]
            tmp['up']           = round(float((networkIo[0] - network_up) / 1024),2)
            tmp['down']         = round(float((networkIo[1] - network_down) / 1024),2)
            tmp['downPackets']  = networkIo[3]
            tmp['upPackets']    = networkIo[2]
            
            network_up   =  networkIo[0]
            network_down =  networkIo[1]
            
            if not networkInfo: networkInfo = tmp
            if (tmp['up'] + tmp['down']) > (networkInfo['up'] + networkInfo['down']): networkInfo = tmp
            
            #取磁盘Io
            disk_ios = True
            try:
                if os.path.exists('/proc/diskstats'):
                    diskio_2 = disk_io_counters()
                    if not diskio_1: diskio_1 = diskio_2
                    tmp = {}
                    tmp['read_count']   = diskio_2.read_count - diskio_1.read_count
                    tmp['write_count']  = diskio_2.write_count - diskio_1.write_count
                    tmp['read_bytes']   = diskio_2.read_bytes - diskio_1.read_bytes
                    tmp['write_bytes']  = diskio_2.write_bytes - diskio_1.write_bytes
                    tmp['read_time']    = diskio_2.read_time - diskio_1.read_time
                    tmp['write_time']   = diskio_2.write_time - diskio_1.write_time
                
                    if not diskInfo: 
                        diskInfo = tmp
                    else:
                        diskInfo['read_count']   += tmp['read_count']
                        diskInfo['write_count']  += tmp['write_count']
                        diskInfo['read_bytes']   += tmp['read_bytes']
                        diskInfo['write_bytes']  += tmp['write_bytes']
                        diskInfo['read_time']    += tmp['read_time']
                        diskInfo['write_time']   += tmp['write_time']
                
                    diskio_1 = diskio_2
            except:disk_ios = False

            
            #print diskInfo
            
            if count >= 12:
                try:
                    sql.close()
                    sql = db.Sql().dbfile('system')
                    addtime = int(time.time())
                    deltime = addtime - (day * 86400)
                    
                    data = (cpuInfo['used'],cpuInfo['mem'],addtime)
                    sql.table('cpuio').add('pro,mem,addtime',data)
                    sql.table('cpuio').where("addtime<?",(deltime,)).delete()
                    
                    data = (networkInfo['up'] / 5,networkInfo['down'] / 5,networkInfo['upTotal'],networkInfo['downTotal'],networkInfo['downPackets'],networkInfo['upPackets'],addtime)
                    sql.table('network').add('up,down,total_up,total_down,down_packets,up_packets,addtime',data)
                    sql.table('network').where("addtime<?",(deltime,)).delete()
                    if os.path.exists('/proc/diskstats') and disk_ios:
                        data = (diskInfo['read_count'],diskInfo['write_count'],diskInfo['read_bytes'],diskInfo['write_bytes'],diskInfo['read_time'],diskInfo['write_time'],addtime)
                        sql.table('diskio').add('read_count,write_count,read_bytes,write_bytes,read_time,write_time,addtime',data)
                        sql.table('diskio').where("addtime<?",(deltime,)).delete()
                    
                    #LoadAverage
                    load_average = GetLoadAverage()
                    lpro = round((load_average['one'] / load_average['max']) * 100,2)
                    if lpro > 100: lpro = 100
                    sql.table('load_average').add('pro,one,five,fifteen,addtime',(lpro,load_average['one'],load_average['five'],load_average['fifteen'],addtime))
                    
                    lpro = None
                    load_average = None
                    cpuInfo = None
                    networkInfo = None
                    diskInfo = None
                    count = 0
                    reloadNum += 1
                    if reloadNum > 1440:
                        reloadNum = 0
                except Exception as ex:
                    print(str(ex))
            del(tmp)
            
            time.sleep(5)
            count +=1
    except:
        time.sleep(30)
        systemTask()
            

#取内存使用率
def GetMemUsed():
    try:
        mem = virtual_memory()
        memInfo = {'memTotal':mem.total/1024/1024,'memFree':mem.free/1024/1024,'memBuffers':mem.buffers/1024/1024,'memCached':mem.cached/1024/1024}
        tmp = memInfo['memTotal'] - memInfo['memFree'] - memInfo['memBuffers'] - memInfo['memCached']
        tmp1 = memInfo['memTotal'] / 100
        return (tmp / tmp1)
    except:
        return 1

#检查502错误 
def check502():
    try:
        phpversions = ['53','54','55','56','70','71','72','73','74']
        for version in phpversions:
            php_path = '/www/server/php/' + version + '/sbin/php-fpm'
            if not os.path.exists(php_path): continue
            if checkPHPVersion(version): continue
            if startPHPVersion(version):
                public.WriteLog('PHP守护程序','检测到PHP-' + version + '处理异常,已自动修复!')
    except:
        pass
            
#处理指定PHP版本   
def startPHPVersion(version):
    try:
        fpm = '/etc/init.d/php-fpm-'+version
        php_path = '/www/server/php/' + version + '/sbin/php-fpm'
        if not os.path.exists(php_path): 
            if os.path.exists(fpm): os.remove(fpm)
            return False
        
        #尝试重载服务
        public.ExecShell(fpm + ' reload')
        if checkPHPVersion(version): return True
        
        #尝试重启服务
        cgi = '/tmp/php-cgi-'+version + '.sock'
        pid = '/www/server/php/'+version+'/var/run/php-fpm.pid'
        public.ExecShell('pkill -9 php-fpm-'+version)
        time.sleep(0.5)
        if not os.path.exists(cgi): public.ExecShell('rm -f ' + cgi)
        if not os.path.exists(pid): public.ExecShell('rm -f ' + pid)
        public.ExecShell(fpm + ' start')
        if checkPHPVersion(version): return True
        
        #检查是否正确启动
        if os.path.exists(cgi): return True
    except:
        return True
    
    
#检查指定PHP版本
def checkPHPVersion(version):
    try:
        url = 'http://127.0.0.1/phpfpm_'+version+'_status'
        result = HttpGet(url)
        #检查nginx
        if result.find('Bad Gateway') != -1: return False
        #检查Apache
        if result.find('Service Unavailable') != -1: return False
        if result.find('Not Found') != -1: CheckPHPINFO()
        
        #检查Web服务是否启动
        if result.find('Connection refused') != -1: 
            global isTask
            if os.path.exists(isTask): 
                isStatus = public.readFile(isTask)
                if isStatus == 'True': return True
            filename = '/etc/init.d/nginx'
            if os.path.exists(filename): public.ExecShell(filename + ' start')
            filename = '/etc/init.d/httpd'
            if os.path.exists(filename): public.ExecShell(filename + ' start')
            
        return True
    except:
        return True


#检测PHPINFO配置
def CheckPHPINFO():
    php_versions = ['53','54','55','56','70','71','72','73','74']
    setupPath = '/www/server'
    path = setupPath +'/panel/vhost/nginx/phpinfo.conf'
    if not os.path.exists(path):
        opt = ""
        for version in php_versions:
            opt += "\n\tlocation /"+version+" {\n\t\tinclude enable-php-"+version+".conf;\n\t}"
        
        phpinfoBody = '''server
{
    listen 80;
    server_name 127.0.0.2;
    allow 127.0.0.1;
    index phpinfo.php index.html index.php;
    root  /www/server/phpinfo;
%s   
}''' % (opt,)
        public.writeFile(path,phpinfoBody)
    
    
    path = setupPath + '/panel/vhost/apache/phpinfo.conf'
    if not os.path.exists(path):
        opt = ""
        for version in php_versions:
            opt += """\n<Location /%s>
    SetHandler "proxy:unix:/tmp/php-cgi-%s.sock|fcgi://localhost"
</Location>""" % (version,version)
            
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
''' % (opt,)
        public.writeFile(path,phpinfoBody)

#502错误检查线程
def check502Task():
    try:
        while True:
            if os.path.exists('/www/server/panel/data/502Task.pl'): check502()
            time.sleep(600)
    except:
        time.sleep(600)
        check502Task()

# 检查面板证书是否有更新
def check_panel_ssl():
    try:
        while True:
            lets_info = public.readFile("/www/server/panel/ssl/lets.info")
            if lets_info:
                lets_info = loads(lets_info)
                cert_info_file = "/www/server/panel/vhost/ssl/" + lets_info["domain"] + "/info.json"
                cert_info = public.readFile(cert_info_file)
                if cert_info:
                    cert_info = loads(cert_info)
                    if setPanelLets.setPanelLets().copy_cert(cert_info):
                        strTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
                        public.writeFile("/tmp/panelSSL.pl","{} 面板证书更新成功".format(strTime))
            time.sleep(60)
    except:
        e = public.get_error_info()
        public.writeFile("/tmp/panelSSL.pl", str(e))

#监控面板状态
def panel_status():
    time.sleep(1)
    panel_path = '/www/server/panel'
    pool = 'http://'
    if os.path.exists(panel_path + '/data/ssl.pl'): pool = 'https://'
    port = '8888'
    if os.path.exists(panel_path + '/data/port.pl'): port = public.readFile(panel_path + '/data/port.pl').strip()
    panel_url = pool + '127.0.0.1:' + port + '/service_status'
    panel_pid = get_panel_pid()
    n = 0
    s = 0
    v = 0
    while True:
        time.sleep(5)
        check_session()
        if not panel_pid: panel_pid = get_panel_pid()
        if not panel_pid: service_panel('start')

        try:
            f = Process(panel_pid).cmdline()[-1]
            if f.find('runserver') == -1 and f.find('BT-Panel') == -1: 
                service_panel('start')
                time.sleep(3)
                panel_pid = get_panel_pid()
                continue
        except:
            service_panel('start')
            time.sleep(3)
            panel_pid = get_panel_pid()
            continue

        n += 1
        v += 1

        if v > 10:
            v = 0
            log_path = panel_path + '/logs/error.log'
            if os.path.exists(log_path):
                e_body = public.GetNumLines(log_path,10)
                if e_body:
                    if e_body.find('PyWSGIServer.do_close') != -1 or e_body.find('Expected GET method:')!=-1 or e_body.find('Invalid HTTP method:') != -1 or e_body.find('table session') != -1:
                        result = HttpGet(panel_url)
                        if result != 'True':
                            if e_body.find('table session') != -1:
                                sess_file = '/dev/shm/session.db'
                                if os.path.exists(sess_file): os.remove(sess_file)
                            public.ExecShell("bash /www/server/panel/init.sh reload &")
                            time.sleep(10)
                            result = HttpGet(panel_url)
                            if result == 'True':
                                public.WriteLog('守护程序','检查到面板服务异常,已自动恢复!')

        if n > 18000:
            n = 0
            result = HttpGet(panel_url)
            if result == 'True':
                time.sleep(10)
                continue
            update_panel()
            result = HttpGet(panel_url)
            if result == 'True':
                public.WriteLog('守护程序','检查到面板服务异常,已自动恢复!')
                time.sleep(10)
                continue


def update_panel():
    public.ExecShell("curl http://download.bt.cn/install/update6.sh|bash &")

def service_panel(action = 'reload'):
    if not os.path.exists('/www/server/panel/init.sh'):
        update_panel()
    else:
        public.ExecShell("bash /www/server/panel/init.sh {} &".format(action))


def check_session():
    try:
        session_file = '/dev/shm/session.db'
        if not os.path.exists(session_file): #如果session文件不存在
            return False
        s_size = os.path.getsize(session_file)
        if s_size < 1024 * 1024 * 2: return False
        if s_size > 1024 * 1024 * 10:
            #大于10MB
            if os.path.exists(session_file): os.remove(session_file)
            public.ExecShell("bash /www/server/panel/init.sh reload &")
        else:
            sql = db.Sql()
            sql._Sql__DB_FILE = session_file
            sql.table('session').where('expiry<?',(public.format_date())).delete()
            sql.table('session').execute('VACUUM',())
            sql.close()
        return True
    except:
        return False

#重启面板服务
def restart_panel_service():
    rtips = 'data/restart.pl'
    reload_tips = 'data/reload.pl'
    while True:
        if os.path.exists(rtips):
            os.remove(rtips)
            service_panel('restart')
        if os.path.exists(reload_tips):
            os.remove(reload_tips)
            service_panel('reload')
        time.sleep(1)

#取面板pid
def get_panel_pid():
    for pid in pids():
        try:
            p = Process(pid)
            n = p.cmdline()[-1]
            if n.find('runserver') != -1 or n.find('BT-Panel') != -1: return pid
        except: pass
    return None


def HttpGet(url,timeout = 6,headers = {}):
    if sys.version_info[0] == 2:
        try:
            import urllib2,ssl
            if sys.version_info[0] == 2:
                reload(urllib2)
                reload(ssl)
            try:
                ssl._create_default_https_context = ssl._create_unverified_context
            except:pass
            req = urllib2.Request(url, headers = headers)
            response = urllib2.urlopen(req,timeout = timeout,)
            return response.read()
        except Exception as ex:
            return str(ex)
    else:
        try:
            import urllib.request,ssl
            try:
                ssl._create_default_https_context = ssl._create_unverified_context
            except:pass
            req = urllib.request.Request(url,headers = headers)
            response = urllib.request.urlopen(req,timeout = timeout)
            result = response.read()
            if type(result) == bytes: result = result.decode('utf-8')
            return result
        except Exception as ex:
            return str(ex)

if __name__ == "__main__":
    main_pid = 'logs/task.pid'
    os.system("kill -9 $(cat {}) &> /dev/null".format(main_pid))
    pid = os.fork()
    if pid: sys.exit(0)
    
    os.umask(0)
    os.setsid()

    _pid = os.fork()
    if _pid:
        public.writeFile(main_pid,str(_pid))
        sys.exit(0)

    sys.stdout.flush()
    sys.stderr.flush()

    err_f = open('logs/task.log','a+')
    os.dup2(err_f.fileno(),sys.stderr.fileno())
    err_f.close()
    public.ExecShell('rm -rf /www/server/phpinfo/*')

    import threading
    t = threading.Thread(target=systemTask)
    t.setDaemon(True)
    t.start()
    
    p = threading.Thread(target=check502Task)
    p.setDaemon(True)
    p.start()

    pl = threading.Thread(target=panel_status)
    pl.setDaemon(True)
    pl.start()

    p = threading.Thread(target=restart_panel_service)
    p.setDaemon(True)
    p.start()
    
    p = threading.Thread(target=check_panel_ssl)
    p.setDaemon(True)
    p.start()

    task_obj = panelTask.bt_task()
    p = threading.Thread(target=task_obj.start_task)
    p.setDaemon(True)
    p.start()

    startTask()

