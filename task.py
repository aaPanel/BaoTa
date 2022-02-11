#!/bin/python
#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------

# ------------------------------
# 计划任务
# ------------------------------

import sys
import os
import logging
from json import dumps, loads
from psutil import Process, pids, cpu_count, cpu_percent, net_io_counters, disk_io_counters, virtual_memory
os.environ['BT_TASK'] = '1'
sys.path.insert(0, "/www/server/panel/class/")
import time
import public
import db
global pre, timeoutCount, logPath, isTask, oldEdate, isCheck
pre = 0
timeoutCount = 0
isCheck = 0
oldEdate = None
logPath = '/tmp/panelExec.log'
isTask = '/tmp/panelTask.pl'
python_bin = None

def get_python_bin():
    global python_bin
    if python_bin: return python_bin
    bin_file = '/www/server/panel/pyenv/bin/python'
    bin_file2 = '/usr/bin/python'
    if os.path.exists(bin_file):
        python_bin = bin_file
        return bin_file
    python_bin = bin_file2
    return bin_file2
def WriteFile(filename,s_body,mode='w+'):
    """
    写入文件内容
    @filename 文件名
    @s_body 欲写入的内容
    return bool 若文件不存在则尝试自动创建
    """
    try:
        fp = open(filename, mode)
        fp.write(s_body)
        fp.close()
        return True
    except:
        try:
            fp = open(filename, mode,encoding="utf-8")
            fp.write(s_body)
            fp.close()
            return True
        except:
            return False

def ReadFile(filename, mode='r'):
    """
    读取文件内容
    @filename 文件名
    return string(bin) 若文件不存在，则返回None
    """
    if not os.path.exists(filename):
        return False
    f_body = None
    with open(filename, mode) as fp:
        f_body = fp.read()
    return f_body

# 下载文件
def DownloadFile(url, filename):
    try:
        import urllib
        import socket
        socket.setdefaulttimeout(10)
        urllib.urlretrieve(url, filename=filename, reporthook=DownloadHook)
        os.system('chown www.www ' + filename)
        WriteLogs('done')
    except:
        WriteLogs('done')


# 下载文件进度回调
def DownloadHook(count, blockSize, totalSize):
    global pre
    used = count * blockSize
    pre1 = int((100.0 * used / totalSize))
    if pre == pre1:
        return
    speed = {'total': totalSize, 'used': used, 'pre': pre}
    WriteLogs(dumps(speed))
    pre = pre1

# 写输出日志
def WriteLogs(logMsg):
    try:
        global logPath
        with open(logPath, 'w+') as fp:
            fp.write(logMsg)
            fp.close()
    except:
        pass


def ExecShell(cmdstring, cwd=None, timeout=None, shell=True):
    try:
        global logPath
        import shlex
        import datetime
        import subprocess
        import time
        sub = subprocess.Popen(cmdstring+' &> '+logPath, cwd=cwd,
                               stdin=subprocess.PIPE, shell=shell, bufsize=4096)

        while sub.poll() is None:
            time.sleep(0.1)

        return sub.returncode
    except:
        return None


# 任务队列
def startTask():
    global isTask,logPath
    try:
        while True:
            try:
                if os.path.exists(isTask):
                    with db.Sql() as sql:
                        sql.table('tasks').where(
                            "status=?", ('-1',)).setField('status', '0')
                        taskArr = sql.table('tasks').where("status=?", ('0',)).field(
                            'id,type,execstr').order("id asc").select()
                        for value in taskArr:
                            start = int(time.time())
                            if not sql.table('tasks').where("id=?", (value['id'],)).count():
                                continue
                            sql.table('tasks').where("id=?", (value['id'],)).save(
                                'status,start', ('-1', start))
                            if value['type'] == 'download':
                                argv = value['execstr'].split('|bt|')
                                DownloadFile(argv[0], argv[1])
                            elif value['type'] == 'execshell':
                                ExecShell(value['execstr'])
                            end = int(time.time())
                            sql.table('tasks').where("id=?", (value['id'],)).save(
                                'status,end', ('1', end))
                            if(sql.table('tasks').where("status=?", ('0')).count() < 1):
                                if os.path.exists(isTask):
                                    os.remove(isTask)
                                #ExecShell('rm -f ' + isTask)
                        sql.close()
                        taskArr = None
            except:
                pass
            siteEdate()
            time.sleep(2)
    except Exception as ex:
        logging.info(ex)
        time.sleep(60)
        startTask()

# 网站到期处理


def siteEdate():
    global oldEdate
    try:
        if not oldEdate:
            oldEdate = ReadFile('/www/server/panel/data/edate.pl')
        if not oldEdate:
            oldEdate = '0000-00-00'
        mEdate = time.strftime('%Y-%m-%d', time.localtime())
        if oldEdate == mEdate:
            return False
        os.system(get_python_bin() +
                  " /www/server/panel/script/site_task.py > /dev/null")
    except Exception as ex:
        logging.info(ex)
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


# 系统监控任务
def systemTask():
    try:
        filename = 'data/control.conf'
        with db.Sql() as sql:
            sql = sql.dbfile('system')
            csql = '''CREATE TABLE IF NOT EXISTS `load_average` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `pro` REAL,
  `one` REAL,
  `five` REAL,
  `fifteen` REAL,
  `addtime` INTEGER
)'''
            sql.execute(csql, ())
            sql.close()

        count = 0
        reloadNum = 0
        disk_wr = 0
        diskio_1 = diskio_2 = networkInfo = cpuInfo = diskInfo = None
        network_up = {}
        network_down = {}
        process_object = process_task()
        try:
            from panelDaily import panelDaily
            panelDaily().check_databases()
        except Exception as e:
            logging.info(e)

        while True:
            if not os.path.exists(filename):
                time.sleep(10)
                continue

            day = 30
            try:
                day = int(ReadFile(filename))
                if day < 1:
                    time.sleep(10)
                    continue
            except:
                day = 30

            tmp = {}
            # 取当前CPU Io
            tmp['used'] = cpu_percent(interval=1)

            if not cpuInfo:
                tmp['mem'] = GetMemUsed()
                cpuInfo = tmp

            if cpuInfo['used'] < tmp['used']:
                tmp['mem'] = GetMemUsed()
                cpuInfo = tmp

            # 取当前网络Io
            networkIo_list = net_io_counters(pernic=True)
            tmp = {}
            tmp['upTotal'] = 0
            tmp['downTotal'] = 0
            tmp['up'] = 0
            tmp['down'] = 0
            tmp['downPackets'] = {}
            tmp['upPackets'] = {}

            for k in networkIo_list.keys():
                networkIo = networkIo_list[k][:4]
                if not k in network_up.keys():
                    network_up[k] = networkIo[0]
                    network_down[k] = networkIo[1]

                tmp['upTotal'] += networkIo[0]
                tmp['downTotal'] += networkIo[1]
                tmp['downPackets'][k] = round(
                    float((networkIo[1] - network_down[k]) / 1024)/5, 2)
                tmp['upPackets'][k] = round(
                    float((networkIo[0] - network_up[k]) / 1024)/5, 2)
                tmp['up'] += tmp['upPackets'][k]
                tmp['down'] += tmp['downPackets'][k]

                network_up[k] = networkIo[0]
                network_down[k] = networkIo[1]

            if not networkInfo:
                networkInfo = tmp
            if (tmp['up'] + tmp['down']) > (networkInfo['up'] + networkInfo['down']):
                networkInfo = tmp

            # 取磁盘Io
            disk_ios = True
            try:
                if os.path.exists('/proc/diskstats'):
                    diskio_2 = disk_io_counters()

                    if not diskio_1:
                        diskio_1 = diskio_2
                    tmp = {}
                    tmp['read_count'] = int((diskio_2.read_count - diskio_1.read_count) / 5)
                    tmp['write_count'] = int((diskio_2.write_count - diskio_1.write_count) / 5)
                    tmp['read_bytes'] = int((diskio_2.read_bytes - diskio_1.read_bytes) / 5)
                    tmp['write_bytes'] = int((diskio_2.write_bytes -  diskio_1.write_bytes) / 5)
                    tmp['read_time'] = int((diskio_2.read_time - diskio_1.read_time) / 5)
                    tmp['write_time'] = int((diskio_2.write_time - diskio_1.write_time) / 5)

                    if not diskInfo:
                        diskInfo = tmp
                    
                    if (tmp['read_bytes'] + tmp['write_bytes']) > (diskInfo['read_bytes'] + diskInfo['write_bytes']):
                        diskInfo['read_count'] = tmp['read_count']
                        diskInfo['write_count'] = tmp['write_count']
                        diskInfo['read_bytes'] = tmp['read_bytes']
                        diskInfo['write_bytes'] = tmp['write_bytes']
                        diskInfo['read_time'] = tmp['read_time']
                        diskInfo['write_time'] = tmp['write_time']

                    # logging.info(['read: ',tmp['read_bytes'] / 1024 / 1024,'write: ',tmp['write_bytes'] / 1024 / 1024])
                    diskio_1 = diskio_2
            except:
                logging.info(public.get_error_info())
                disk_ios = False

            if count >= 12:
                try:
                    sql = db.Sql().dbfile('system')
                    addtime = int(time.time())
                    deltime = addtime - (day * 86400)

                    data = (cpuInfo['used'], cpuInfo['mem'], addtime)
                    sql.table('cpuio').add('pro,mem,addtime', data)
                    sql.table('cpuio').where("addtime<?", (deltime,)).delete()
                    data = (networkInfo['up'], networkInfo['down'], networkInfo['upTotal'], networkInfo['downTotal'], dumps(networkInfo['downPackets']), dumps(networkInfo['upPackets']), addtime)
                    sql.table('network').add('up,down,total_up,total_down,down_packets,up_packets,addtime', data)
                    sql.table('network').where("addtime<?", (deltime,)).delete()
                    # logging.info(diskInfo)
                    if os.path.exists('/proc/diskstats') and disk_ios:
                        data = (diskInfo['read_count'], diskInfo['write_count'], diskInfo['read_bytes'],diskInfo['write_bytes'], diskInfo['read_time'], diskInfo['write_time'], addtime)
                        sql.table('diskio').add('read_count,write_count,read_bytes,write_bytes,read_time,write_time,addtime', data)
                        sql.table('diskio').where("addtime<?", (deltime,)).delete()

                    # LoadAverage
                    load_average = GetLoadAverage()
                    lpro = round(
                        (load_average['one'] / load_average['max']) * 100, 2)
                    if lpro > 100:
                        lpro = 100
                    sql.table('load_average').add('pro,one,five,fifteen,addtime', (lpro, load_average['one'], load_average['five'], load_average['fifteen'], addtime))
                    sql.table('load_average').where("addtime<?", (deltime,)).delete()
                    sql.table('process_high_percent').where("addtime<?", (deltime,)).delete()
                    sql.table('process_tops').where("addtime<?", (deltime,)).delete()
                    sql.close()
                    
                    lpro = None
                    load_average = None
                    cpuInfo = None
                    networkInfo = None
                    diskInfo = None
                    data = None
                    count = 0
                    reloadNum += 1
                    if reloadNum > 1440:
                        reloadNum = 0
                    process_object.get_monitor_list()
                    
                    # 日报数据收集
                    if os.path.exists("/www/server/panel/data/start_daily.pl"):
                        try:
                            from panelDaily import panelDaily
                            pd = panelDaily()
                            t_now = time.localtime()
                            yesterday  = time.localtime(time.mktime((
                                t_now.tm_year, t_now.tm_mon, t_now.tm_mday-1, 
                                0,0,0,0,0,0
                            )))
                            yes_time_key = pd.get_time_key(yesterday)
                            con = ReadFile("/www/server/panel/data/store_app_usage.pl")
                            # logging.info(str(con))
                            store = False
                            if con:
                                if con != str(yes_time_key):
                                    store = True
                            else:
                                store = True
    
                            if store:
                                date_str = str(yes_time_key)
                                daily_data = pd.get_daily_data_local(date_str)
                                if "status" in daily_data.keys():
                                    if daily_data["status"]:
                                        score = daily_data["score"]
                                        if public.M("system").dbfile("system").table("daily").where("time_key=?", (yes_time_key,)).count() == 0:
                                            public.M("system").dbfile("system").table("daily").add("time_key,evaluate,addtime", (yes_time_key, score, time.time()))
                                        pd.store_app_usage(yes_time_key)
                                        WriteFile("/www/server/panel/data/store_app_usage.pl", str(yes_time_key), "w")
                                    # logging.info("更新应用存储信息:"+str(yes_time_key))
                                    pd.check_server()
                        except Exception as e:
                            logging.info("存储应用空间信息错误:"+str(e)) 
                except Exception as ex:
                    logging.info(str(ex))
            del(tmp)
            time.sleep(5)
            count += 1
    except Exception as ex:
        logging.info(ex)
        time.sleep(30)
        systemTask()


# 取内存使用率
def GetMemUsed():
    try:
        mem = virtual_memory()
        memInfo = {'memTotal': mem.total/1024/1024, 'memFree': mem.free/1024/1024,
                   'memBuffers': mem.buffers/1024/1024, 'memCached': mem.cached/1024/1024}
        tmp = memInfo['memTotal'] - memInfo['memFree'] - \
            memInfo['memBuffers'] - memInfo['memCached']
        tmp1 = memInfo['memTotal'] / 100
        return (tmp / tmp1)
    except:
        return 1

# 检查502错误


def check502():
    try:
        phpversions = public.get_php_versions()
        for version in phpversions:
            if version in ['52','5.2']: continue
            php_path = '/www/server/php/' + version + '/sbin/php-fpm'
            if not os.path.exists(php_path):
                continue
            if checkPHPVersion(version):
                continue
            if startPHPVersion(version):
                public.WriteLog('PHP守护程序', '检测到PHP-' + version + '处理异常,已自动修复!', not_web=True)
    except Exception as ex:
        logging.info(ex)

# 处理指定PHP版本
def startPHPVersion(version):
    try:
        fpm = '/etc/init.d/php-fpm-'+version
        php_path = '/www/server/php/' + version + '/sbin/php-fpm'
        if not os.path.exists(php_path):
            if os.path.exists(fpm):
                os.remove(fpm)
            return False

        # 尝试重载服务
        os.system(fpm + ' start')
        os.system(fpm + ' reload')
        if checkPHPVersion(version):
            return True

        # 尝试重启服务
        cgi = '/tmp/php-cgi-'+version + '.sock'
        pid = '/www/server/php/'+version+'/var/run/php-fpm.pid'
        os.system('pkill -9 php-fpm-'+version)
        time.sleep(0.5)
        if os.path.exists(cgi):
            os.remove(cgi)
        if os.path.exists(pid):
            os.remove(pid)
        os.system(fpm + ' start')
        if checkPHPVersion(version):
            return True
        # 检查是否正确启动
        if os.path.exists(cgi):
            return True
        return False
    except Exception as ex:
        logging.info(ex)
        return True


# 检查指定PHP版本
def checkPHPVersion(version):
    try:
        cgi_file = '/tmp/php-cgi-{}.sock'.format(version)
        if os.path.exists(cgi_file):
            init_file = '/etc/init.d/php-fpm-{}'.format(version)
            if os.path.exists(init_file):
                init_body = public.ReadFile(init_file)
                if not init_body: return True
            uri = "/phpfpm_"+version+"_status?json"
            result = public.request_php(version, uri, '')
            loads(result)
        return True
    except:
        logging.info("检测到PHP-{}无法访问".format(version))
        return False


# 502错误检查线程
def check502Task():
    try:
        while True:
            check502()
            sess_expire()
            time.sleep(600)
    except Exception as ex:
        logging.info(ex)
        time.sleep(600)
        check502Task()


# session过期处理
def sess_expire():
    try:
        sess_path = '/www/server/panel/data/session'
        if not os.path.exists(sess_path):
            return
        s_time = time.time()
        f_list = os.listdir(sess_path)
        f_num = len(f_list)
        for fname in f_list:
            filename = '/'.join((sess_path, fname))
            fstat = os.stat(filename)
            f_time = s_time - fstat.st_mtime
            if f_time > 3600:
                os.remove(filename)
                continue
            if fstat.st_size < 256 and len(fname) == 32:
                if f_time > 60 or f_num > 30:
                    os.remove(filename)
                    continue
        del(f_list)
    except Exception as ex:
        logging.info(str(ex))


# 检查面板证书是否有更新
def check_panel_ssl():
    try:
        while True:
            lets_info = ReadFile("/www/server/panel/ssl/lets.info")
            if not lets_info:
                time.sleep(3600)
                continue
            os.system(get_python_bin() + " /www/server/panel/script/panel_ssl_task.py > /dev/null")
            time.sleep(3600)
    except Exception as e:
        public.writeFile("/tmp/panelSSL.pl", str(e), "a+")

# 监控面板状态
def panel_status():
    time.sleep(1)
    panel_pid = get_panel_pid()
    while True:
        time.sleep(30)
        if not panel_pid:
            panel_pid = get_panel_pid()
        if not panel_pid:
            service_panel('start')

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


def update_panel():
    os.system("curl http://download.bt.cn/install/update6.sh|bash &")


def service_panel(action='reload'):
    if not os.path.exists('/www/server/panel/init.sh'):
        update_panel()
    else:
        os.system("bash /www/server/panel/init.sh {} &".format(action))

# 重启面板服务
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

# 取面板pid
def get_panel_pid():
    pid = ReadFile('/www/server/panel/logs/panel.pid')
    if pid:
        return int(pid)
    for pid in pids():
        try:
            p = Process(pid)
            n = p.cmdline()[-1]
            if n.find('runserver') != -1 or n.find('BT-Panel') != -1:
                return pid
        except:
            pass
    return None


def HttpGet(url, timeout=6, headers={}):
    if sys.version_info[0] == 2:
        try:
            import urllib2
            req = urllib2.Request(url, headers=headers)
            response = urllib2.urlopen(req, timeout=timeout,)
            return response.read()
        except Exception as ex:
            logging.info(str(ex))
            return str(ex)
    else:
        try:
            import urllib.request
            req = urllib.request.Request(url, headers=headers)
            response = urllib.request.urlopen(req, timeout=timeout)
            result = response.read()
            if type(result) == bytes:
                result = result.decode('utf-8')
            return result
        except Exception as ex:
            logging.info("URL: {}  => {}".format(url, ex))
            return str(ex)


# 定时任务去检测邮件信息
def send_mail_time():
    while True:
        try:
            os.system(get_python_bin() +" /www/server/panel/script/mail_task.py > /dev/null")
            time.sleep(180)
        except:
            time.sleep(360)
            send_mail_time()

#5个小时更新一次更新软件列表
def update_software_list():
    while True:
        try:
            import panelPlugin
            panelPlugin.panelPlugin().get_cloud_list_status(None)
            time.sleep(18000)
        except:
            time.sleep(1800)
            update_software_list()

# 检查面板文件完整性
def check_files_panel():
    python_bin = get_python_bin()
    while True:
        time.sleep(600)
        try:
            result = loads(
                os.popen('{} /www/server/panel/script/check_files.py'.format(python_bin)).read()
                )
        except:
            logging.info(public.get_error_info())
            continue
        if result in ['0']:
            continue

        if type(result) != list:
            continue
        class_path = '/www/server/panel/class/'
        for i in result:
            cf = class_path + i['name']
            if not os.path.exists(cf):
                continue
            if public.FileMd5(cf) == i['md5']:
                continue
            public.writeFile(cf, i['body'])
            os.system("bash /www/server/panel/init.sh reload &")


# 面板消息提醒
def check_panel_msg():
    python_bin = get_python_bin()
    while True:
        os.system('{} /www/server/panel/script/check_msg.py &'.format(python_bin))
        time.sleep(3600)


class process_task:

    __pids = []
    __last_times = {}
    __last_dates = {}
    __cpu_count = cpu_count()
    __sql = None

    def __init__(self):
        self.__sql = db.Sql().dbfile('system')
        csql = '''CREATE TABLE IF NOT EXISTS `process_tops` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `process_list` REAL,
  `addtime` INTEGER
)'''
        self.__sql.execute(csql, ())
        csql = '''CREATE TABLE IF NOT EXISTS `process_high_percent` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` REAL,
  `pid`  REAL,
  `cmdline` REAL,
  `cpu_percent` FLOAT,
  `memory` FLOAT,
  `cpu_time_total` INTEGER,
  `addtime` INTEGER
)'''
        self.__sql.execute(csql, ())
        self.__sql.close()

    def get_pids(self):
        '''
            @name 获取pid列表
            @author hwliang<2021-09-04>
            @return None
        '''
        self.__pids = pids()

    def get_cpu_percent(self,pid,cpu_time_total):
        '''
            @name 获取pid的cpu占用率
            @author hwliang<2021-09-04>
            @param pid 进程id
            @param cpu_time_total 进程总cpu时间
            @return 占用cpu百分比
        '''
        stime = time.time()
        if pid in self.__last_times:
            old_time = self.__last_times[pid]
        else:
            self.__last_times[pid] = cpu_time_total
            self.__last_dates[pid] = stime
            return 0

        cpu_percent = round(100.00 * float(cpu_time_total - old_time) / (stime - self.__last_dates[pid]) / self.__cpu_count,2)
        return cpu_percent

    def read_file(self,filename):
        f = open(filename,'rb')
        result = f.read()
        f.close()
        return result.decode().replace("\u0000"," ").strip()

    def get_monitor_list(self):
        '''
            @name 获取监控列表
            @author hwliang<2021-09-04>
            @return list
        '''
        self.get_pids()
        monitor_list = {}
        cpu_src_limit = 30
        cpu_pre_limit = 80 / self.__cpu_count
        
        addtime = int(time.time())
        for pid in self.__pids:
            try:
                process_proc_comm = '/proc/{}/comm'.format(pid)
                process_proc_cmdline = '/proc/{}/cmdline'.format(pid)
                if pid < 100: continue
                p = Process(pid)

                cpu_times = p.cpu_times()
                cpu_time_total = int(sum(cpu_times))
                pname = self.read_file(process_proc_comm)
                cmdline = self.read_file(process_proc_cmdline)
                rss = p.memory_info().rss
                cpu_percent = self.get_cpu_percent(pid,cpu_time_total)
                pid = str(pid)
                ppid = str(p.ppid())
                if ppid in monitor_list:
                    monitor_list[ppid]['pid'].append(pid)
                    monitor_list[ppid]['cpu_time_total'] += cpu_time_total
                    monitor_list[ppid]['memory'] += rss
                    monitor_list[ppid]['cpu_percent'] += cpu_percent
                else:
                    if pname == 'php-fpm':
                        if cmdline.find('/www/server/php/') != -1:
                            pname += '(' + '.'.join(cmdline.split('/')[-3]) + ')'
                    elif pname in ['mysqld','mysqld_safe']:
                        pname = 'mysqld,mysql_safe(MySQL)'
                    elif pname in ['BT-Task','BT-Panel']:
                        continue
                    
                    monitor_list[pid] = {
                        'pid':[pid],
                        'name':pname,
                        'cmdline': cmdline,
                        'memory': rss, 
                        'cpu_time_total': cpu_time_total,
                        'cpu_percent': cpu_percent
                    }

            except:
                continue

        process_info_list = []
        cpu_high_list = []
        for i in monitor_list:
            pid_count = len(monitor_list[i]['pid'])
            monitor_list[i]['pid'] = ','.join(monitor_list[i]['pid'])
            process_info_list.append(monitor_list[i])

            # 记录CPU占用超过 cpu_pre_limit 的进程
            if pid_count > 1:
                if monitor_list[i]['cpu_percent'] >= cpu_src_limit:
                    cpu_high_list.append(monitor_list[i])
            else:
                if monitor_list[i]['cpu_percent'] >= cpu_pre_limit:
                    cpu_high_list.append(monitor_list[i])
            

        self.__sql = db.Sql().dbfile('system')        
        process_info_list = sorted(process_info_list,key=lambda x:x['cpu_time_total'],reverse=True)
        self.__sql.table('process_tops').insert({"process_list": dumps(process_info_list[:10]),'addtime':addtime})

        if cpu_high_list:
            for cpu_high in cpu_high_list:
                self.__sql.table('process_high_percent').addAll(
                    'pid,name,cmdline,memory,cpu_time_total,cpu_percent,addtime',
                    (
                        cpu_high['pid'],
                        cpu_high['name'],
                        cpu_high['cmdline'],
                        cpu_high['memory'],
                        cpu_high['cpu_time_total'],
                        cpu_high['cpu_percent'],
                        addtime
                    )
                )
            self.__sql.commit()

        self.__sql.close()



def main():
    main_pid = 'logs/task.pid'
    if os.path.exists(main_pid):
        os.system("kill -9 $(cat {}) &> /dev/null".format(main_pid))
    pid = os.fork()
    if pid:
        sys.exit(0)

    os.setsid()

    _pid = os.fork()
    if _pid:
        public.writeFile(main_pid, str(_pid))
        sys.exit(0)

    sys.stdout.flush()
    sys.stderr.flush()
    task_log_file = 'logs/task.log'

    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S', filename=task_log_file, filemode='a+')
    logging.info('服务已启动')

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
    
    p = threading.Thread(target=update_software_list)
    p.setDaemon(True)
    p.start()
    
    p = threading.Thread(target=send_mail_time)
    p.setDaemon(True)
    p.start()

    p = threading.Thread(target=check_files_panel)
    p.setDaemon(True)
    p.start()
    import panelTask
    task_obj = panelTask.bt_task()
    task_obj.not_web = True
    p = threading.Thread(target=task_obj.start_task)
    p.setDaemon(True)
    p.start()

    p = threading.Thread(target=check_panel_msg)
    p.setDaemon(True)
    p.start()

    startTask()


if __name__ == "__main__":
    main()
