#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 x3
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------
import psutil,time,os,public,re,sys
try:
    from BTPanel import session,cache
except:
    pass
class system:
    setupPath = None
    ssh = None
    shell = None
    
    def __init__(self):
        self.setupPath = public.GetConfigValue('setup_path')
    
    def GetConcifInfo(self,get=None):
        #取环境配置信息
        if not 'config' in session:
            session['config'] = public.M('config').where("id=?",('1',)).field('webserver,sites_path,backup_path,status,mysql_root').find()
        if not 'email' in session['config']:
            session['config']['email'] = public.M('users').where("id=?",('1',)).getField('email')
        data = {}
        data = session['config']
        data['webserver'] = public.get_webserver()
        #PHP版本
        phpVersions = ('52','53','54','55','56','70','71','72','73','74')
        
        data['php'] = []
        
        for version in phpVersions:
            tmp = {}
            tmp['setup'] = os.path.exists(self.setupPath + '/php/'+version+'/bin/php');
            if tmp['setup']:
                phpConfig = self.GetPHPConfig(version)
                tmp['version'] = version
                tmp['max'] = phpConfig['max']
                tmp['maxTime'] = phpConfig['maxTime']
                tmp['pathinfo'] = phpConfig['pathinfo']
                tmp['status'] = os.path.exists('/tmp/php-cgi-' + version + '.sock')
                data['php'].append(tmp)
            
        tmp = {}
        data['webserver'] = ''
        serviceName = 'nginx'
        tmp['setup'] = False
        phpversion = "54"
        phpport = '888'
        pstatus = False
        pauth = False
        if os.path.exists(self.setupPath+'/nginx'): 
            data['webserver'] = 'nginx'
            serviceName = 'nginx'
            tmp['setup'] = os.path.exists(self.setupPath +'/nginx/sbin/nginx')
            configFile = self.setupPath + '/nginx/conf/nginx.conf'
            try:
                if os.path.exists(configFile):
                    conf = public.readFile(configFile)
                    rep = "listen\s+([0-9]+)\s*;"
                    rtmp = re.search(rep,conf)
                    if rtmp:
                        phpport = rtmp.groups()[0]
                    
                    if conf.find('AUTH_START') != -1: pauth = True
                    if conf.find(self.setupPath + '/stop') == -1: pstatus = True
                    configFile = self.setupPath + '/nginx/conf/enable-php.conf'
                    conf = public.readFile(configFile)
                    rep = "php-cgi-([0-9]+)\.sock"
                    rtmp = re.search(rep,conf)
                    if rtmp:
                        phpversion = rtmp.groups()[0]
            except:
                pass
            
        elif os.path.exists(self.setupPath+'/apache'):
            data['webserver'] = 'apache'
            serviceName = 'httpd'
            tmp['setup'] = os.path.exists(self.setupPath +'/apache/bin/httpd')
            configFile = self.setupPath + '/apache/conf/extra/httpd-vhosts.conf'
            try:
                if os.path.exists(configFile):
                    conf = public.readFile(configFile)
                    rep = "php-cgi-([0-9]+)\.sock"
                    rtmp = re.search(rep,conf)
                    if rtmp:
                        phpversion = rtmp.groups()[0]
                    rep = "Listen\s+([0-9]+)\s*\n"
                    rtmp = re.search(rep,conf)
                    if rtmp:
                        phpport = rtmp.groups()[0]
                    if conf.find('AUTH_START') != -1: pauth = True
                    if conf.find(self.setupPath + '/stop') == -1: pstatus = True
            except:
                pass
        elif os.path.exists('/usr/local/lsws/bin/lswsctrl'):
            data['webserver'] = 'openlitespeed'
            serviceName = 'openlitespeed'
            tmp['setup'] = os.path.exists(self.setupPath +'/apache/bin/httpd')
            configFile = '/usr/local/lsws/bin/lswsctrl'
            try:
                if os.path.exists(configFile):
                    conf = public.readFile('/www/server/panel/vhost/openlitespeed/detail/phpmyadmin.conf')
                    rep = "/usr/local/lsws/lsphp(\d+)/bin/lsphp"
                    rtmp = re.search(rep,conf)
                    if rtmp:
                        phpversion = rtmp.groups()[0]
                    conf = public.readFile('/www/server/panel/vhost/openlitespeed/listen/888.conf')
                    rep = "address\s+\*\:(\d+)"
                    rtmp = re.search(rep,conf)
                    if rtmp:
                        phpport = rtmp.groups()[0]
                    if conf.find('AUTH_START') != -1: pauth = True
                    if conf.find(self.setupPath + '/stop') == -1: pstatus = True
            except:
                pass
                
                
        tmp['type'] = data['webserver']
        tmp['version'] = public.readFile(self.setupPath + '/'+data['webserver']+'/version.pl');
        tmp['status'] = False
        result = public.ExecShell('/etc/init.d/' + serviceName + ' status')
        if result[0].find('running') != -1: tmp['status'] = True
        data['web'] = tmp
        
        tmp = {}
        vfile = self.setupPath + '/phpmyadmin/version.pl';
        tmp['version'] = public.readFile(vfile);
        if tmp['version']: tmp['version'] = tmp['version'].strip()
        tmp['setup'] = os.path.exists(vfile);
        tmp['status'] = pstatus;
        tmp['phpversion'] = phpversion.strip();
        tmp['port'] = phpport;
        tmp['auth'] = pauth;
        data['phpmyadmin'] = tmp;
        
        tmp = {}
        tmp['setup'] = os.path.exists('/etc/init.d/tomcat');
        tmp['status'] = tmp['setup']
        #if public.ExecShell('ps -aux|grep tomcat|grep -v grep')[0] == "": tmp['status'] = False
        tmp['version'] = public.readFile(self.setupPath + '/tomcat/version.pl');
        data['tomcat'] = tmp;
        
        tmp = {}
        tmp['setup'] = os.path.exists(self.setupPath +'/mysql/bin/mysql');
        tmp['version'] = public.readFile(self.setupPath + '/mysql/version.pl');
        tmp['status'] = os.path.exists('/tmp/mysql.sock')
        data['mysql'] = tmp
        
        tmp = {}
        tmp['setup'] = os.path.exists(self.setupPath +'/redis/runtest');
        tmp['status'] = os.path.exists('/var/run/redis_6379.pid');
        data['redis'] = tmp;
        
        tmp = {}
        tmp['setup'] = os.path.exists('/usr/local/memcached/bin/memcached');
        tmp['status'] = os.path.exists('/var/run/memcached.pid');
        data['memcached'] = tmp;
        
        tmp = {}
        tmp['setup'] = os.path.exists(self.setupPath +'/pure-ftpd/bin/pure-pw');
        tmp['version'] = public.readFile(self.setupPath + '/pure-ftpd/version.pl');
        tmp['status'] = os.path.exists('/var/run/pure-ftpd.pid')
        data['pure-ftpd'] = tmp
        data['panel'] = self.GetPanelInfo()
        data['systemdate'] = public.ExecShell('date +"%Y-%m-%d %H:%M:%S %Z %z"')[0].strip();
        data['show_workorder'] = not os.path.exists('data/not_workorder.pl')
        return data
    
    def GetPanelInfo(self,get=None):
        #取面板配置
        address = public.GetLocalIp()
        try:
            port = public.GetHost(True)
        except:
            port = '8888';
        domain = ''
        if os.path.exists('data/domain.conf'):
           domain = public.readFile('data/domain.conf');
        
        autoUpdate = ''
        if os.path.exists('data/autoUpdate.pl'): autoUpdate = 'checked';
        limitip = ''
        if os.path.exists('data/limitip.conf'): limitip = public.readFile('data/limitip.conf');
        admin_path = '/'
        if os.path.exists('data/admin_path.pl'): admin_path = public.readFile('data/admin_path.pl').strip()
        
        templates = []
        #for template in os.listdir('BTPanel/templates/'):
        #    if os.path.isdir('templates/' + template): templates.append(template);
        template = public.GetConfigValue('template')
        
        check502 = '';
        if os.path.exists('data/502Task.pl'): check502 = 'checked';
        return {'port':port,'address':address,'domain':domain,'auto':autoUpdate,'502':check502,'limitip':limitip,'templates':templates,'template':template,'admin_path':admin_path}
    
    def GetPHPConfig(self,version):
        #取PHP配置
        file = self.setupPath + "/php/"+version+"/etc/php.ini"
        phpini = public.readFile(file)
        file = self.setupPath + "/php/"+version+"/etc/php-fpm.conf"
        phpfpm = public.readFile(file)
        data = {}
        try:
            rep = "upload_max_filesize\s*=\s*([0-9]+)M"
            tmp = re.search(rep,phpini).groups()
            data['max'] = tmp[0]
        except:
            data['max'] = '50'
        try:
            rep = "request_terminate_timeout\s*=\s*([0-9]+)\n"
            tmp = re.search(rep,phpfpm).groups()
            data['maxTime'] = tmp[0]
        except:
            data['maxTime'] = 0
        
        try:
            rep = r"\n;*\s*cgi\.fix_pathinfo\s*=\s*([0-9]+)\s*\n"
            tmp = re.search(rep,phpini).groups()
            
            if tmp[0] == '1':
                data['pathinfo'] = True
            else:
                data['pathinfo'] = False
        except:
            data['pathinfo'] = False
        
        return data

    
    def GetSystemTotal(self,get,interval = 1):
        #取系统统计信息
        data = self.GetMemInfo();
        cpu = self.GetCpuInfo(interval);
        data['cpuNum'] = cpu[1];
        data['cpuRealUsed'] = cpu[0];
        data['time'] = self.GetBootTime();
        data['system'] = self.GetSystemVersion();
        data['isuser'] = public.M('users').where('username=?',('admin',)).count();
        try:
            data['isport'] = public.GetHost(True) == '8888'
        except:data['isport'] = False

        data['version'] = session['version'];
        return data
    
    def GetLoadAverage(self,get):
        try:
            c = os.getloadavg()
        except:
            c = [0,0,0]
        data = {};
        data['one'] = float(c[0]);
        data['five'] = float(c[1]);
        data['fifteen'] = float(c[2]);
        data['max'] = psutil.cpu_count() * 2;
        data['limit'] = data['max'];
        data['safe'] = data['max'] * 0.75;
        return data;
    
    def GetAllInfo(self,get):
        data = {}
        data['load_average'] = self.GetLoadAverage(get)
        data['title'] = self.GetTitle()
        data['network'] = self.GetNetWorkApi(get)
        data['cpu'] = self.GetCpuInfo(1)
        data['time'] = self.GetBootTime()
        data['system'] = self.GetSystemVersion()
        data['mem'] = self.GetMemInfo()
        data['version'] = session['version']
        return data
    
    def GetTitle(self):
        return public.GetConfigValue('title')
    
    def GetSystemVersion(self):
        #取操作系统版本
        key = 'sys_version'
        version = cache.get(key)
        if version: return version
        import public
        version = public.readFile('/etc/redhat-release')
        if not version:
            version = public.readFile('/etc/issue').strip().split("\n")[0].replace('\\n','').replace('\l','').strip()
        else:
            version = version.replace('release ','').replace('Linux','').replace('(Core)','').strip()
        v_info = sys.version_info
        version = version + '(Py' + str(v_info.major) + '.' + str(v_info.minor) + '.' + str(v_info.micro) + ')'
        cache.set(key,version,600)
        return version
    
    def GetBootTime(self):
        #取系统启动时间
        key = 'sys_time'
        sys_time = cache.get(key)
        if sys_time: return sys_time
        import public,math
        conf = public.readFile('/proc/uptime').split()
        tStr = float(conf[0])
        min = tStr / 60
        hours = min / 60
        days = math.floor(hours / 24)
        hours = math.floor(hours - (days * 24))
        min = math.floor(min - (days * 60 * 24) - (hours * 60))
        sys_time = "{}天".format(int(days))
        cache.set(key,sys_time,1800)
        return sys_time
        #return public.getMsg('SYS_BOOT_TIME',(str(int(days)),str(int(hours)),str(int(min))))
    
    def GetCpuInfo(self,interval = 1):
        #取CPU信息
        cpuCount = psutil.cpu_count()
        cpuNum = psutil.cpu_count(logical=False)
        c_tmp = public.readFile('/proc/cpuinfo')
        d_tmp = re.findall("physical id.+",c_tmp)
        cpuW = len(set(d_tmp))
        import threading
        p = threading.Thread(target=self.get_cpu_percent_thead,args=(interval,))
        p.setDaemon(True)
        p.start()
        
        used = cache.get('cpu_used_all')
        if not used: used = self.get_cpu_percent_thead(interval)

        used_all = psutil.cpu_percent(percpu=True)
        cpu_name = public.getCpuType() + " * {}".format(cpuW)
        return used,cpuCount,used_all,cpu_name,cpuNum,cpuW

    def get_cpu_percent_thead(self,interval):
        used = psutil.cpu_percent(interval)
        cache.set('cpu_used_all',used,10)
        return used
        

    def get_cpu_percent(self):
        percent = 0.00
        old_cpu_time = cache.get('old_cpu_time')
        old_process_time = cache.get('old_process_time')
        if not old_cpu_time: 
            old_cpu_time = self.get_cpu_time()
            old_process_time = self.get_process_cpu_time()
            time.sleep(1)
        new_cpu_time = self.get_cpu_time()
        new_process_time = self.get_process_cpu_time()
        try:
            percent = round(100.00 * ((new_process_time - old_process_time) / (new_cpu_time - old_cpu_time)),2)
        except: percent = 0.00
        cache.set('old_cpu_time',new_cpu_time)
        cache.set('old_process_time',new_process_time)
        if percent > 100: percent = 100
        if percent > 0: return percent
        return 0.00

    def get_process_cpu_time(self):
        pids = psutil.pids()
        cpu_time = 0.00
        for pid in pids:
            try:
                cpu_times = psutil.Process(pid).cpu_times()
                for s in cpu_times: cpu_time += s
            except:continue
        return cpu_time

    def get_cpu_time(self):
        cpu_time = 0.00
        cpu_times = psutil.cpu_times()
        for s in cpu_times: cpu_time += s
        return cpu_time
    
    def GetMemInfo(self,get=None):
        #取内存信息
        mem = psutil.virtual_memory()
        memInfo = {'memTotal':int(mem.total/1024/1024),'memFree':int(mem.free/1024/1024),'memBuffers':int(mem.buffers/1024/1024),'memCached':int(mem.cached/1024/1024)}
        memInfo['memRealUsed'] = memInfo['memTotal'] - memInfo['memFree'] - memInfo['memBuffers'] - memInfo['memCached']
        return memInfo
    
    def GetDiskInfo(self,get=None):
        return self.GetDiskInfo2()
        #取磁盘分区信息
        diskIo = psutil.disk_partitions()
        diskInfo = []
        cuts = ['/mnt/cdrom','/boot','/boot/efi','/dev','/dev/shm','/run/lock','/run','/run/shm','/run/user']
        for disk in diskIo:
            if not cuts: continue
            tmp = {}
            tmp['path'] = disk[1]
            tmp['size'] = psutil.disk_usage(disk[1])
            diskInfo.append(tmp)
        return diskInfo
    
    def GetDiskInfo2(self):
        #取磁盘分区信息
        key = 'sys_disk'
        diskInfo = cache.get(key)
        if diskInfo: return diskInfo
        temp = public.ExecShell("df -hT -P|grep '/'|grep -v tmpfs|grep -v 'snap/core'|grep -v udev")[0]
        tempInodes = public.ExecShell("df -i -P|grep '/'|grep -v tmpfs|grep -v 'snap/core'|grep -v udev")[0]
        temp1 = temp.split('\n')
        tempInodes1 = tempInodes.split('\n')
        diskInfo = []
        n = 0
        cuts = ['/mnt/cdrom','/boot','/boot/efi','/dev','/dev/shm','/run/lock','/run','/run/shm','/run/user']
        for tmp in temp1:
            n += 1
            try:
                inodes = tempInodes1[n-1].split()
                disk = re.findall(r"^(.+)\s+([\w\.]+)\s+([\w\.]+)\s+([\w\.]+)\s+([\w\.]+)\s+([\d%]{2,4})\s+(/.{0,50})$",tmp.strip())
                if disk: disk = disk[0]
                if len(disk) < 6: continue
                if disk[2].find('M') != -1: continue
                if disk[2].find('K') != -1: continue
                if len(disk[6].split('/')) > 10: continue
                if disk[6] in cuts: continue
                if disk[6].find('docker') != -1: continue
                if disk[1].strip() in ['tmpfs']: continue
                arr = {}
                arr['filesystem'] = disk[0].strip()
                arr['type'] = disk[1].strip()
                arr['path'] = disk[6]
                tmp1 = [disk[2],disk[3],disk[4],disk[5]]
                arr['size'] = tmp1
                arr['inodes'] = [inodes[1],inodes[2],inodes[3],inodes[4]]
                diskInfo.append(arr)
            except Exception as ex: 
                public.WriteLog('信息获取',str(ex))
                continue
        cache.set(key,diskInfo,360)
        return diskInfo

    #清理系统垃圾
    def ClearSystem(self,get):
        count = total = 0
        tmp_total,tmp_count = self.ClearMail()
        count += tmp_count
        total += tmp_total
        tmp_total,tmp_count = self.ClearOther()
        count += tmp_count
        total += tmp_total
        return count,total
    
    #清理邮件日志
    def ClearMail(self):
        rpath = '/var/spool'
        total = count = 0
        import shutil
        con = ['cron','anacron','mail']
        for d in os.listdir(rpath):
            if d in con: continue
            dpath = rpath + '/' + d
            time.sleep(0.2)
            num = size = 0
            for n in os.listdir(dpath):
                filename = dpath + '/' + n
                fsize = os.path.getsize(filename)
                size += fsize
                if os.path.isdir(filename):
                    shutil.rmtree(filename)
                else:
                    os.remove(filename)
                print('\t\033[1;32m[OK]\033[0m')
                num += 1
            total += size
            count += num
        return total,count
    
    #清理其它
    def ClearOther(self):
        clearPath = [
                     {'path':'/www/server/panel','find':'testDisk_'},
                     {'path':'/www/wwwlogs','find':'log'},
                     {'path':'/tmp','find':'panelBoot.pl'},
                     {'path':'/www/server/panel/install','find':'.rpm'}
                     ]
        
        total = count = 0
        for c in clearPath:
            for d in os.listdir(c['path']):
                if d.find(c['find']) == -1: continue
                filename = c['path'] + '/' + d
                if os.path.isdir(filename): continue
                fsize = os.path.getsize(filename)
                total += fsize
                os.remove(filename)
                count += 1
        public.serviceReload()
        filename = '/www/server/nginx/off'
        if os.path.exists(filename): os.remove(filename)
        public.ExecShell('echo > /tmp/panelBoot.pl')
        return total,count
    
    def GetNetWork(self,get=None):
        cache_timeout = 86400
        otime = cache.get("otime")
        ntime = time.time()
        networkInfo = {}
        networkInfo['network'] = {}
        networkInfo['upTotal'] = 0
        networkInfo['downTotal'] = 0
        networkInfo['up'] = 0
        networkInfo['down'] = 0
        networkInfo['downPackets'] = 0
        networkInfo['upPackets'] = 0
        networkIo_list = psutil.net_io_counters(pernic = True)
        for net_key in networkIo_list.keys():
            networkIo = networkIo_list[net_key][:4]
            up_key = "{}_up".format(net_key)
            down_key = "{}_down".format(net_key)
            otime_key = "otime"

            if not otime:
                otime = time.time()
                
                cache.set(up_key,networkIo[0],cache_timeout)
                cache.set(down_key,networkIo[1],cache_timeout)
                cache.set(otime_key,otime ,cache_timeout)
                
            networkInfo['network'][net_key] = {}
            up = cache.get(up_key)
            down = cache.get(down_key)
            if not up:
                up = networkIo[0]
            if not down:
                down = networkIo[1] 
            networkInfo['network'][net_key]['upTotal']   = networkIo[0]
            networkInfo['network'][net_key]['downTotal'] = networkIo[1]
            networkInfo['network'][net_key]['up']        = round(float(networkIo[0] -  up) / 1024 / (ntime - otime),2)
            networkInfo['network'][net_key]['down']      = round(float(networkIo[1] - down) / 1024 / (ntime -  otime),2)
            networkInfo['network'][net_key]['downPackets'] =networkIo[3]
            networkInfo['network'][net_key]['upPackets']   =networkIo[2]

            networkInfo['upTotal'] += networkInfo['network'][net_key]['upTotal']
            networkInfo['downTotal'] += networkInfo['network'][net_key]['downTotal']
            networkInfo['up'] += networkInfo['network'][net_key]['up']
            networkInfo['down'] += networkInfo['network'][net_key]['down']
            networkInfo['downPackets'] += networkInfo['network'][net_key]['downPackets']
            networkInfo['upPackets'] += networkInfo['network'][net_key]['upPackets']

                            
            cache.set(up_key,networkIo[0],cache_timeout)
            cache.set(down_key,networkIo[1],cache_timeout)
            cache.set(otime_key, time.time(),cache_timeout)

        if get != False:
            networkInfo['cpu'] = self.GetCpuInfo(1)
            networkInfo['load'] = self.GetLoadAverage(get)
            networkInfo['mem'] = self.GetMemInfo(get)
            networkInfo['version'] = session['version']
            networkInfo['disk'] = self.GetDiskInfo2()

        networkInfo['title'] = self.GetTitle()
        networkInfo['time'] = self.GetBootTime()
        networkInfo['site_total'] = public.M('sites').count()
        networkInfo['ftp_total'] = public.M('ftps').count()
        networkInfo['database_total'] = public.M('databases').count()
        networkInfo['system'] = self.GetSystemVersion()
        networkInfo['installed'] = self.CheckInstalled()
        import panelSSL
        networkInfo['user_info'] = panelSSL.panelSSL().GetUserInfo(None)
        networkInfo['up'] = round(float(networkInfo['up']),2)
        networkInfo['down'] = round(float(networkInfo['down']),2)

        return networkInfo
        
    
    def GetNetWorkApi(self,get=None):
        return self.GetNetWork()

    #检查是否安装任何
    def CheckInstalled(self):
        checks = ['nginx','apache','php','pure-ftpd','mysql']
        import os
        for name in checks:
            filename = public.GetConfigValue('root_path') + "/server/" + name
            if os.path.exists(filename): return True
        return False
    
    def GetNetWorkOld(self):
        #取网络流量信息
        import time;
        pnet = public.readFile('/proc/net/dev')
        rep = '([^\s]+):[\s]{0,}(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)'
        pnetall = re.findall(rep,pnet)
        networkInfo = {}
        networkInfo['upTotal'] = networkInfo['downTotal'] = networkInfo['up'] = networkInfo['down'] = networkInfo['downPackets'] = networkInfo['upPackets'] = 0


        for pnetInfo in pnetall:
            if pnetInfo[0] == 'io': continue
            networkInfo['downTotal'] += int(pnetInfo[1])
            networkInfo['downPackets'] += int(pnetInfo[2])
            networkInfo['upTotal'] += int(pnetInfo[9])
            networkInfo['upPackets'] += int(pnetInfo[10])

        cache_timeout = 86400
        otime = cache.get("otime")
        if not otime:
            otime = time.time()
            cache.set('up',networkInfo['upTotal'],cache_timeout)
            cache.set('down',networkInfo['downTotal'],cache_timeout)
            cache.set('otime',otime ,cache_timeout)

        ntime = time.time()
        tmpDown = networkInfo['downTotal'] - cache.get("down")
        tmpUp = networkInfo['upTotal'] - cache.get("up")
        networkInfo['down'] = str(round(float(tmpDown) / 1024 / (ntime - otime),2))
        networkInfo['up']   = str(round(float(tmpUp) / 1024 / (ntime - otime),2))
        if networkInfo['down'] < 0: networkInfo['down'] = 0
        if networkInfo['up'] < 0: networkInfo['up'] = 0
        
        otime = time.time()
        cache.set('up',networkInfo['upTotal'],cache_timeout)
        cache.set('down',networkInfo['downTotal'],cache_timeout)
        cache.set('otime',ntime ,cache_timeout)

        networkInfo['cpu'] = self.GetCpuInfo()
        return networkInfo


    #取IO读写信息
    def get_io_info(self,get = None):
        io_disk = psutil.disk_io_counters()
        ioTotal = {}
        ioTotal['write'] = self.get_io_write(io_disk.write_bytes)
        ioTotal['read'] = self.get_io_read(io_disk.read_bytes)
        return ioTotal

    #取IO写
    def get_io_write(self,io_write):
        disk_io_write = 0
        old_io_write = cache.get('io_write')
        if not old_io_write:
            cache.set('io_write',io_write)
            return disk_io_write

        old_io_time = cache.get('io_time')
        new_io_time = time.time()
        if not old_io_time: old_io_time = new_io_time
        io_end = (io_write - old_io_write)
        time_end = (time.time() - old_io_time)
        if io_end > 0:
            if time_end < 1: time_end = 1
            disk_io_write = io_end / time_end
        cache.set('io_write',io_write)
        cache.set('io_time',new_io_time)
        if disk_io_write > 0: return int(disk_io_write)
        return 0

    #取IO读
    def get_io_read(self,io_read):
        disk_io_read = 0
        old_io_read = cache.get('io_read')
        if not old_io_read:
            cache.set('io_read',io_read)
            return disk_io_read
        old_io_time = cache.get('io_time')
        new_io_time = time.time()
        if not old_io_time: old_io_time = new_io_time
        io_end = (io_read - old_io_read)
        time_end = (time.time() - old_io_time)
        if io_end > 0:
            if time_end < 1: time_end = 1
            disk_io_read = io_end / time_end
        cache.set('io_read',io_read)
        if disk_io_read > 0: return int(disk_io_read)
        return 0

    #检查并修复MySQL目录权限
    def __check_mysql_path(self):
        try:
            #获取datadir路径
            mypath = '/etc/my.cnf'
            if not os.path.exists(mypath): return False
            public.set_mode(mypath,644)
            mycnf = public.readFile(mypath)
            tmp = re.findall('datadir\s*=\s*(.+)',mycnf)
            if not tmp: return False
            datadir = tmp[0]

            #可以被启动的权限
            accs = ['755','777']

            #处理data目录权限
            mode_info = public.get_mode_and_user(datadir)
            if not mode_info['mode'] in accs or mode_info['user'] != 'mysql':
                public.ExecShell('chmod 755 ' + datadir)
                public.ExecShell('chown -R mysql:mysql ' + datadir)
        
            #递归处理父目录权限
            datadir = os.path.dirname(datadir)
            while datadir != '/':
                if datadir == '/': break
                mode_info = public.get_mode_and_user(datadir)
                if not mode_info['mode'] in accs:
                    public.ExecShell('chmod 755 ' + datadir)
                datadir = os.path.dirname(datadir)
        except: pass
    
    def ServiceAdmin(self,get=None):
        #服务管理
        if get.name == 'mysqld': 
            public.CheckMyCnf()
            self.__check_mysql_path()
        if get.name.find('webserver') != -1:
            get.name = public.get_webserver()
        
        if get.name == 'phpmyadmin':
            import ajax
            get.status = 'True'
            ajax.ajax().setPHPMyAdmin(get)
            return public.returnMsg(True,'SYS_EXEC_SUCCESS')
            
        if get.name == 'openlitespeed':
            if get.type == 'stop':
                public.ExecShell('rm -f /tmp/lshttpd/*.sock* && /usr/local/lsws/bin/lswsctrl stop')
            elif get.type == 'start':
                public.ExecShell('rm -f /tmp/lshttpd/*.sock* && /usr/local/lsws/bin/lswsctrl start')
            else:
                public.ExecShell('rm -f /tmp/lshttpd/*.sock* && /usr/local/lsws/bin/lswsctrl restart')
            return public.returnMsg(True,'SYS_EXEC_SUCCESS')

        #检查httpd配置文件
        if get.name == 'apache' or get.name == 'httpd':
            get.name = 'httpd'
            if not os.path.exists(self.setupPath+'/apache/bin/apachectl'): return public.returnMsg(True,'SYS_NOT_INSTALL_APACHE')
            vhostPath = self.setupPath + '/panel/vhost/apache'
            if not os.path.exists(vhostPath):
                public.ExecShell('mkdir ' + vhostPath)
                public.ExecShell('/etc/init.d/httpd start')
            
            if get.type == 'start': 
                public.ExecShell('/etc/init.d/httpd stop')
                self.kill_port()
                
            result = public.ExecShell('ulimit -n 8192 ; ' + self.setupPath+'/apache/bin/apachectl -t')
            if result[1].find('Syntax OK') == -1:
                public.WriteLog("TYPE_SOFT",'SYS_EXEC_ERR', (str(result),))
                return public.returnMsg(False,'SYS_CONF_APACHE_ERR',(result[1].replace("\n",'<br>'),))
            
            if get.type == 'restart':
                public.ExecShell('pkill -9 httpd')
                public.ExecShell('/etc/init.d/httpd start')
                time.sleep(0.5)
            
        #检查nginx配置文件
        elif get.name == 'nginx':
            vhostPath = self.setupPath + '/panel/vhost/rewrite'
            if not os.path.exists(vhostPath): public.ExecShell('mkdir ' + vhostPath)
            vhostPath = self.setupPath + '/panel/vhost/nginx'
            if not os.path.exists(vhostPath):
                public.ExecShell('mkdir ' + vhostPath)
                public.ExecShell('/etc/init.d/nginx start')
            
            result = public.ExecShell('ulimit -n 8192 ; nginx -t -c '+self.setupPath+'/nginx/conf/nginx.conf')
            if result[1].find('perserver') != -1:
                limit = self.setupPath + '/nginx/conf/nginx.conf'
                nginxConf = public.readFile(limit)
                limitConf = "limit_conn_zone $binary_remote_addr zone=perip:10m;\n\t\tlimit_conn_zone $server_name zone=perserver:10m;"
                nginxConf = nginxConf.replace("#limit_conn_zone $binary_remote_addr zone=perip:10m;",limitConf)
                public.writeFile(limit,nginxConf)
                public.ExecShell('/etc/init.d/nginx start')
                return public.returnMsg(True,'SYS_CONF_NGINX_REP')
            
            if result[1].find('proxy') != -1:
                import panelSite
                panelSite.panelSite().CheckProxy(get)
                public.ExecShell('/etc/init.d/nginx start')
                return public.returnMsg(True,'SYS_CONF_NGINX_REP')
            
            #return result
            if result[1].find('successful') == -1:
                public.WriteLog("TYPE_SOFT",'SYS_EXEC_ERR', (str(result),))
                return public.returnMsg(False,'SYS_CONF_NGINX_ERR',(result[1].replace("\n",'<br>'),))

            if get.type == 'start': 
                self.kill_port()
                time.sleep(0.5)
        if get.name == 'redis':
            redis_init = '/etc/init.d/redis'
            if os.path.exists(redis_init):
                init_body = public.ReadFile(redis_init)
                if init_body.find('pkill -9 redis') == -1:
                    public.ExecShell("wget -O " + redis_init + " " + public.get_url() + '/init/redis.init')
                    public.ExecShell("chmod +x " + redis_init)
        
        #执行
        execStr = "/etc/init.d/"+get.name+" "+get.type
        if execStr == '/etc/init.d/pure-ftpd reload': execStr = self.setupPath+'/pure-ftpd/bin/pure-pw mkdb '+self.setupPath+'/pure-ftpd/etc/pureftpd.pdb'
        if execStr == '/etc/init.d/pure-ftpd start': public.ExecShell('pkill -9 pure-ftpd')
        if execStr == '/etc/init.d/tomcat reload': execStr = '/etc/init.d/tomcat stop && /etc/init.d/tomcat start'
        if execStr == '/etc/init.d/tomcat restart': execStr = '/etc/init.d/tomcat stop && /etc/init.d/tomcat start'
        
        if get.name != 'mysqld':
            result = public.ExecShell(execStr)
        else:
            public.ExecShell(execStr)
            result = []
            result.append('')
            result.append('')
        
        if result[1].find('nginx.pid') != -1:
            public.ExecShell('pkill -9 nginx && sleep 1')
            public.ExecShell('/etc/init.d/nginx start')
        if get.type != 'test':
            public.WriteLog("TYPE_SOFT", 'SYS_EXEC_SUCCESS',(execStr,))
        
        if len(result[1]) > 1 and get.name != 'pure-ftpd' and get.name != 'redis': return public.returnMsg(False, '<p>警告消息： <p>' + result[1].replace('\n','<br>'))
        return public.returnMsg(True,'SYS_EXEC_SUCCESS')
    
    def RestartServer(self,get):
        if not public.IsRestart(): return public.returnMsg(False,'EXEC_ERR_TASK')
        public.ExecShell("sync && init 6 &")
        return public.returnMsg(True,'SYS_REBOOT')

    def kill_port(self):
        public.ExecShell('pkill -9 httpd')
        public.ExecShell('pkill -9 nginx')
        public.ExecShell("kill -9 $(lsof -i :80|grep LISTEN|awk '{print $2}')")
        return True
    
    #释放内存
    def ReMemory(self,get):
        public.ExecShell('sync')
        scriptFile = 'script/rememory.sh'
        if not os.path.exists(scriptFile):
            public.downloadFile(public.GetConfigValue('home') + '/script/rememory.sh',scriptFile)
        public.ExecShell("/bin/bash " + self.setupPath + '/panel/' + scriptFile)
        return self.GetMemInfo()
    
    #重启面板     
    def ReWeb(self,get):
        #s = time.time()
        #if not self.shell: self.connect_ssh()
        #self.shell.send("nohup /etc/init.d/bt restart && sleep 1 && /etc/init.d/bt start > /dev/null &\n")
        #public.ExecShell("nohup sleep 2 && /etc/init.d/bt restart 2>&1 >/dev/null &")
        
        public.ExecShell("/etc/init.d/bt start")
        public.writeFile('data/restart.pl','True')
        return public.returnMsg(True,'面板已重启')

    def connect_ssh(self):
        import paramiko
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh.connect('127.0.0.1', public.GetSSHPort())
        except:
            if public.GetSSHStatus():
                try:
                    self.ssh.connect('localhost', public.GetSSHPort())
                except:
                    return False
            import firewalls,common
            fw = firewalls.firewalls()
            get = common.dict_obj()
            get.status = '0'
            fw.SetSshStatus(get)
            self.ssh.connect('127.0.0.1', public.GetSSHPort())
            get.status = '1'
            fw.SetSshStatus(get)
        self.shell = self.ssh.invoke_shell(term='xterm', width=100, height=29)
        self.shell.setblocking(0)
        return True
    
    #修复面板
    def RepPanel(self,get):
        public.writeFile('data/js_random.pl','1')
        public.ExecShell("wget -O update.sh " + public.get_url() + "/install/update6.sh && bash update.sh")
        self.ReWeb(None)
        return True
    
    #升级到专业版
    def UpdatePro(self,get):
        public.ExecShell("wget -O update.sh " + public.get_url() + "/install/update6.sh && bash update.sh")
        self.ReWeb(None)
        return True
        
        
        
        
        
        
