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
from psutil import Process, pids, cpu_count
os.environ['BT_TASK'] = '1'
sys.path.insert(0, "/www/server/panel/class/")
import time
import public
import db
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

# 写输出日志
def WriteLogs(logMsg):
    try:
        global logPath
        with open(logPath, 'w+') as fp:
            fp.write(logMsg)
            fp.close()
    except:
        pass


# 日报监控任务
def systemTask():
    process_object = process_task()
    while 1:
        time.sleep(60)
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
                        pd.check_server()
            except Exception as e:
                logging.info("存储应用空间信息错误:"+str(e)) 

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
            public.auto_backup_panel()
            check502()
            time.sleep(600)
    except Exception as ex:
        logging.info(ex)
        time.sleep(600)
        check502Task()


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

