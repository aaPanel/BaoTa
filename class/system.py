# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 x3
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang  <hwl@bt.cn>
# +-------------------------------------------------------------------
import psutil, time, os, public, re, sys,json

try:
    from BTPanel import session, cache, request
except:
    pass

from mod.base import json_response
from typing import Tuple


class system:
    setupPath = None
    ssh = None
    shell = None

    def __init__(self):
        self.setupPath = public.get_setup_path()

    def GetConcifInfo(self, get=None):
        # 取环境配置信息
        if not 'config' in session:
            session['config'] = public.M('config').where("id=?", ('1',)).field('webserver,sites_path,backup_path,status,mysql_root').find()
        if not 'email' in session['config']:
            session['config']['email'] = public.M('users').where("id=?", ('1',)).getField('email')
        data = {}
        data = session['config']
        data['webserver'] = public.get_webserver()
        # PHP版本
        phpVersions = public.get_php_versions()

        data['php'] = []

        for version in phpVersions:
            tmp = {}
            tmp['setup'] = os.path.exists(self.setupPath + '/php/' + version + '/bin/php')
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
        phpversion = "00"
        phpport = '888'
        pstatus = False
        pauth = False
        if os.path.exists(self.setupPath + '/nginx/version.pl'):
            data['webserver'] = 'nginx'
            serviceName = 'nginx'
            tmp['setup'] = os.path.exists(self.setupPath + '/nginx/sbin/nginx')
            configFile = self.setupPath + '/nginx/conf/nginx.conf'
            try:
                if os.path.exists(configFile):
                    conf = public.readFile(configFile)
                    rep = "listen\s+([0-9]+)\s*;"
                    rtmp = re.search(rep, conf)
                    if rtmp:
                        phpport = rtmp.groups()[0]

                    if conf.find('AUTH_START') != -1: pauth = True
                    if conf.find(self.setupPath + '/stop') == -1: pstatus = True
                    configFile = self.setupPath + '/nginx/conf/enable-php.conf'
                    conf = public.readFile(configFile)
                    rep = "php-cgi-([0-9]+)\.sock"
                    rtmp = re.search(rep, conf)
                    if rtmp:
                        phpversion = rtmp.groups()[0]
            except:
                pass

        elif os.path.exists(self.setupPath + '/apache'):
            data['webserver'] = 'apache'
            serviceName = 'httpd'
            tmp['setup'] = os.path.exists(self.setupPath + '/apache/bin/httpd')
            configFile = self.setupPath + '/apache/conf/extra/httpd-vhosts.conf'
            try:
                if os.path.exists(configFile):
                    conf = public.readFile(configFile)
                    rep = "php-cgi-([0-9]+)\.sock"
                    rtmp = re.search(rep, conf)
                    if rtmp:
                        phpversion = rtmp.groups()[0]
                    rep = "Listen\s+([0-9]+)\s*\n"
                    rtmp = re.search(rep, conf)
                    if rtmp:
                        phpport = rtmp.groups()[0]
                    if conf.find('AUTH_START') != -1: pauth = True
                    if conf.find(self.setupPath + '/stop') == -1: pstatus = True
            except:
                pass
        elif os.path.exists('/usr/local/lsws/bin/lswsctrl'):
            data['webserver'] = 'openlitespeed'
            serviceName = 'openlitespeed'
            tmp['setup'] = os.path.exists('/usr/local/lsws/bin/lswsctrl')
            configFile = '/usr/local/lsws/bin/lswsctrl'
            try:
                if os.path.exists(configFile):
                    conf = public.readFile('/www/server/panel/vhost/openlitespeed/detail/phpmyadmin.conf')
                    rep = "/usr/local/lsws/lsphp(\d+)/bin/lsphp"
                    rtmp = re.search(rep, conf)
                    if rtmp:
                        phpversion = rtmp.groups()[0]
                    conf = public.readFile('/www/server/panel/vhost/openlitespeed/listen/888.conf')
                    rep = "address\s+\*\:(\d+)"
                    rtmp = re.search(rep, conf)
                    if rtmp:
                        phpport = rtmp.groups()[0]
                    if conf.find('AUTH_START') != -1: pauth = True
                    if conf.find(self.setupPath + '/stop') == -1: pstatus = True
            except:
                pass

        tmp['type'] = public.get_webserver()
        tmp['version'] = public.xss_version(public.readFile(self.setupPath + '/' + tmp['type'] + '/version.pl'))
        tmp['status'] = False
        if serviceName == 'openlitespeed':
            result = public.ExecShell('systemctl status lswsctrl')
            if result[0].find('active (running)') != -1: tmp['status'] = True
        else:
            result = public.ExecShell('/etc/init.d/' + serviceName + ' status')
            if result[0].find('running') != -1: tmp['status'] = True
        data['web'] = tmp

        tmp = {}
        vfile = self.setupPath + '/phpmyadmin/version.pl'
        tmp['version'] = public.xss_version(public.readFile(vfile))
        if tmp['version']: tmp['version'] = tmp['version'].strip()
        tmp['setup'] = os.path.exists(vfile)
        tmp['status'] = pstatus
        tmp['phpversion'] = phpversion.strip()
        tmp['port'] = phpport
        tmp['auth'] = pauth
        data['phpmyadmin'] = tmp

        tmp = {}
        tmp['setup'] = os.path.exists('/etc/init.d/tomcat')
        tmp['status'] = tmp['setup']
        # if public.ExecShell('ps -aux|grep tomcat|grep -v grep')[0] == "": tmp['status'] = False
        tmp['version'] = public.xss_version(public.readFile(self.setupPath + '/tomcat/version.pl'))
        data['tomcat'] = tmp

        tmp = {}
        tmp['setup'] = os.path.exists(self.setupPath + '/mysql/bin/mysql')
        tmp['version'] = public.xss_version(public.readFile(self.setupPath + '/mysql/version.pl'))
        tmp['status'] = os.path.exists('/tmp/mysql.sock')
        data['mysql'] = tmp

        tmp = {}
        tmp['setup'] = os.path.exists(self.setupPath + '/redis/runtest')
        tmp['status'] = os.path.exists('/var/run/redis_6379.pid')
        data['redis'] = tmp

        tmp = {}
        tmp['setup'] = os.path.exists('/usr/local/memcached/bin/memcached')
        tmp['status'] = os.path.exists('/var/run/memcached.pid')
        data['memcached'] = tmp

        tmp = {}
        tmp['setup'] = os.path.exists(self.setupPath + '/pure-ftpd/bin/pure-pw')
        tmp['version'] = public.xss_version(public.readFile(self.setupPath + '/pure-ftpd/version.pl'))
        tmp['status'] = os.path.exists('/var/run/pure-ftpd.pid')
        data['pure-ftpd'] = tmp
        data['panel'] = self.GetPanelInfo()
        data['systemdate'] = public.ExecShell('date +"%Y-%m-%d %H:%M:%S %Z %z"')[0].strip();
        data['show_workorder'] = not os.path.exists('data/not_workorder.pl')
        data['show_panelai'] = not os.path.exists('data/not_panelai.pl')
        data['show_evaluate'] = not os.path.exists('data/not_evaluate.pl')
        
        return data

    def GetPanelInfo(self, get=None):
        # 取面板配置
        address = public.GetLocalIp()
        try:
            port = public.GetHost(True)
        except:
            port = '8888';
        domain = ''
        if os.path.exists('data/domain.conf'):
            domain = public.readFile('data/domain.conf');

        try:
            listen_port = public.readFile('data/port.pl')
            if int(listen_port) <= 0 : listen_port = '8888'
        except:
            listen_port = '8888'
        autoUpdate = ''
        if os.path.exists('data/autoUpdate.pl'): autoUpdate = 'checked';
        limitip = ''
        if os.path.exists('data/limitip.conf'): limitip = public.readFile('data/limitip.conf');
        admin_path = '/'
        if os.path.exists('data/admin_path.pl'): admin_path = public.readFile('data/admin_path.pl').strip()
        # 取面板访问限制地区
        limitarea = {"allow": [], "deny": []}
        if os.path.exists('data/limit_area.json'):
            try:
                limitarea = json.loads(public.readFile('data/limit_area.json'))
            except:
                limitarea = {"allow": [], "deny": []}
        limitarea_status = 'false'
        if os.path.exists('data/limit_area.pl'): limitarea_status = 'true'

        templates = []
        # for template in os.listdir('BTPanel/templates/'):
        #    if os.path.isdir('templates/' + template): templates.append(template);
        template = public.GetConfigValue('template')

        check502 = ''
        if os.path.exists('data/502Task.pl'): check502 = 'checked';
        return {'port': port,'listen_port':listen_port, 'address': address, 'domain': domain, 'auto': autoUpdate, '502': check502, 'limitip': limitip, 'limitarea_status': limitarea_status, 'limitarea': limitarea,
                'templates': templates, 'template': template, 'admin_path': admin_path}

    def GetPHPConfig(self, version):
        # 取PHP配置
        file = self.setupPath + "/php/" + version + "/etc/php.ini"
        phpini = public.readFile(file)
        file = self.setupPath + "/php/" + version + "/etc/php-fpm.conf"
        phpfpm = public.readFile(file)
        data = {}
        try:
            rep = "upload_max_filesize\s*=\s*([0-9]+)M"
            tmp = re.search(rep, phpini).groups()
            data['max'] = tmp[0]
        except:
            data['max'] = '50'
        try:
            rep = "request_terminate_timeout\s*=\s*([0-9]+)\n"
            tmp = re.search(rep, phpfpm).groups()
            data['maxTime'] = tmp[0]
        except:
            data['maxTime'] = 0

        try:
            rep = r"\n;*\s*cgi\.fix_pathinfo\s*=\s*([0-9]+)\s*\n"
            tmp = re.search(rep, phpini).groups()

            if tmp[0] == '1':
                data['pathinfo'] = True
            else:
                data['pathinfo'] = False
        except:
            data['pathinfo'] = False

        return data

    def GetSystemTotal(self, get, interval=1):
        # 取系统统计信息
        data = self.GetMemInfo()
        cpu = self.GetCpuInfo(interval)
        data['cpuNum'] = cpu[1]
        data['cpuRealUsed'] = cpu[0]
        data['time'] = self.GetBootTime()
        data['system'] = self.GetSystemVersion()
        data['isuser'] = public.M('users').where('username=?', ('admin',)).count()
        try:
            data['isport'] = public.GetHost(True) == '8888'
        except:
            data['isport'] = False

        data['version'] = session['version']
        return data

    def GetLoadAverage(self, get):
        try:
            c = os.getloadavg()
        except:
            c = [0, 0, 0]
        data = {}
        data['one'] = float(c[0])
        data['five'] = float(c[1])
        data['fifteen'] = float(c[2])
        data['max'] = psutil.cpu_count() * 2
        data['limit'] = data['max']
        data['safe'] = data['max'] * 0.75
        return data

    def GetAllInfo(self, get):
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
        return public.xss_version(public.GetConfigValue('title'))

    def GetSystemVersion(self):
        # 取操作系统版本
        key = 'sys_version'
        version = cache.get(key)
        if version: return version
        version = public.get_os_version()
        cache.set(key, version, 600)
        return version

    def GetBootTime(self):
        # 取系统启动时间
        key = 'sys_time'
        sys_time = cache.get(key)
        if sys_time: return sys_time
        import public, math
        conf = public.readFile('/proc/uptime').split()
        tStr = float(conf[0])
        min = tStr / 60
        hours = min / 60
        days = math.floor(hours / 24)
        hours = math.floor(hours - (days * 24))
        min = math.floor(min - (days * 60 * 24) - (hours * 60))

        sys_time = "{}天".format(int(days))
        if int(days) == 0:
            sys_time = "{}小时".format(int(hours))
            if int(hours) == 0:
                sys_time = "{}分钟".format(int(min))

        cache.set(key, sys_time, 300)
        return sys_time
        # return public.getMsg('SYS_BOOT_TIME',(str(int(days)),str(int(hours)),str(int(min))))

    def GetCpuInfo(self, interval=1):
        # 取CPU信息
        try:
            cpuCount = psutil.cpu_count()
            cpuNum = psutil.cpu_count(logical=False)
            c_tmp = public.readFile('/proc/cpuinfo')
            d_tmp = re.findall("physical id.+", c_tmp)
            cpuW = len(set(d_tmp))
            if cpuW == 0:
                cpuW = 1
            import threading
            p = threading.Thread(target=self.get_cpu_percent_thead, args=(interval,))
            # p.setDaemon(True)
            p.start()

            used = cache.get('cpu_used_all')
            if not used: used = self.get_cpu_percent_thead(interval)

            used_all = psutil.cpu_percent(percpu=True)
            cpu_name = public.getCpuType() + " * {}".format(cpuW)

            return used, cpuCount, used_all, cpu_name, cpuNum, cpuW
        except:
            return 0, 0, 0, 0, 0, 0

    def get_cpu_percent_thead(self, interval):
        used = psutil.cpu_percent(interval)
        cache.set('cpu_used_all', used, 10)
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
            percent = round(100.00 * ((new_process_time - old_process_time) / (new_cpu_time - old_cpu_time)), 2)
        except:
            percent = 0.00
        cache.set('old_cpu_time', new_cpu_time)
        cache.set('old_process_time', new_process_time)
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
            except:
                continue
        return cpu_time

    def get_cpu_time(self):
        cpu_time = 0.00
        cpu_times = psutil.cpu_times()
        for s in cpu_times: cpu_time += s
        return cpu_time

    def bytes_format(self, bytes_num, precision=2):
        """
        将bytes_num转成GB
        :param bytes_num: 字节数
        :return: 格式化后的字符串 xxx mb
        """
        suffixs = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']

        suffix = ""
        for i, suf in enumerate(suffixs):
            if bytes_num < 1024:
                suffix = suf
                break
            bytes_num /= 1024

        return ["{:.{precision}f}".format(bytes_num, precision=precision), suffix]

    def bytes_to_human_readable(self, bytes_num, precision=2):
        """
        将bytes_num转成GB
        :param bytes_num: 字节数
        :return: 格式化后的字符串 xxx mb
        """
        return self.bytes_format(bytes_num, precision)[0] + self.bytes_format(bytes_num, precision)[1]


    def GetMemInfo(self, get=None):
        # 取内存信息
        skey = 'memInfo'
        memInfo = cache.get(skey)
        if memInfo: return memInfo
        mem = psutil.virtual_memory()
        memInfo = {
            'memTotal': int(mem.total / 1024 / 1024),
            'memFree': int(mem.free / 1024 / 1024),
            'memBuffers': int(mem.buffers / 1024 / 1024),
            'memCached': int(mem.cached / 1024 / 1024),
            'memAvailable': int(mem.available / 1024 / 1024),
            'memShared': int(mem.shared / 1024 / 1024)
        }
        memInfo['memRealUsed'] = memInfo['memTotal'] - memInfo['memFree'] - memInfo['memBuffers'] - memInfo['memCached']
        memInfo['memNewTotalList'] = self.bytes_format(mem.total, 1)
        memNewTotal = ''.join(memInfo['memNewTotalList'])
        memInfo['memNewRealUsedList'] = self.bytes_format((memInfo['memTotal'] - memInfo['memFree'] - memInfo['memBuffers'] - memInfo['memCached']) * 1024 * 1024, 1)
        memNewRealUsed = ''.join(memInfo['memNewRealUsedList'])
        if memNewTotal[-2:] == memNewRealUsed[-2:]:
            memNewRealUsed = memNewRealUsed[:-2]
            if memNewRealUsed.endswith("0"):
                memNewRealUsed = memNewRealUsed[:-2]

        memInfo['memNewRealUsed'] = memNewRealUsed
        memInfo['memNewTotal'] = memNewTotal
        cache.set(skey, memInfo, 60)
        return memInfo

    def GetDiskInfo(self, get=None):
        # 取磁盘分区信息

        DISK_INFO_STATUS=False
        if os.path.exists("/etc/motd"):
            MOTD_MSG=public.ReadFile("/etc/motd")
            if "Alibaba" in MOTD_MSG or "Huawei Cloud" in MOTD_MSG:
                DISK_INFO_STATUS=True
        if os.path.exists("/etc/hostname"):
            HOSTNAME_MSG=public.ReadFile("/etc/hostname")
            TX_CLOUD=re.search(r'VM-[0-9]+-[0-9]+', HOSTNAME_MSG) is not None
            if TX_CLOUD:
                DISK_INFO_STATUS=True

        disk_info_dict = {}
        try:
            if DISK_INFO_STATUS:
                import subprocess
                result = subprocess.run(['lsblk', '-o', 'NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT','-p'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                output = result.stdout.decode('utf-8')

                lines = output.splitlines()
                headers = lines[0].split()
                current_main_part = None

                for line in lines[1:]:
                    columns = re.split(r'\s+', line.strip())
                    if len(columns) >= 3 and columns[2] in ['disk', 'part', 'lvm']:
                        entry = {headers[i]: columns[i] for i in range(len(columns))}
                        entry['NAME'] = re.sub(r'[├─└─]+', '', entry['NAME'])
                        if columns[2] == 'disk':
                            current_main_part = entry['NAME']
                        entry['main_part'] = current_main_part
                        disk_info_dict[entry['NAME']] = entry

                pdisk_info_dict = {}
                for line in lines[1:]:
                    columns = re.split(r'\s+', line.strip())
                    if len(columns) >= 3 and columns[2] in ['disk']:  # Check
                        entry = {headers[i]: columns[i] for i in range(len(columns))}
                        if columns[2] == 'disk':
                            current_main_part = entry['NAME']
                        entry['main_part'] = current_main_part
                    pdisk_info_dict[entry['NAME']] = entry
        except:
            pass

        try:
            diskIo = psutil.disk_partitions(True)
            diskInfo = []
            processed_devices = set()
            processed_mountpoints = set()

            cuts = ['/mnt/cdrom', '/boot', '/boot/efi', '/dev', '/dev/shm', '/run/lock', '/run', '/run/shm', '/run/user','/dev/zram']
            coutine_keys = ['docker','volume','overlay','/snap','/run/user','/dev/']
            coutine_types = ['ext2','ext3', 'ext4', 'xfs','btrfs','fat32','nfs','cifs','smb','iscsi']

            for disk in diskIo:
                if disk.mountpoint in cuts: continue
                if disk.mountpoint.startswith('/proc'): continue
                if disk.device in processed_devices and not disk.fstype.startswith("fuse"):
                    continue
                if disk.device.startswith("/dev/loop"):
                    continue
                if disk.mountpoint in processed_mountpoints:
                    continue
                # 根据文件系统类型过滤
                #if (disk.fstype.lower() not in coutine_types and 'fuse' not in disk.fstype.lower()) or disk.fstype.lower()=='fusectl': continue
                if disk.fstype.lower() not in coutine_types and disk.mountpoint != "/":
                    if (disk.fstype.lower() not in coutine_types and 'fuse' not in disk.fstype.lower()) or disk.fstype.lower() == 'fusectl': continue

                # 根据关键字过滤
                is_continue = False
                for key in coutine_keys:
                    if key == "overlay" and disk.mountpoint == "/": continue
                    if key in disk.mountpoint:
                        is_continue = True
                        break
                if is_continue: continue

                # 获取磁盘信息
                statvfs = os.statvfs(disk.mountpoint)

                # 计算容量使用信息
                disk_total = statvfs.f_frsize * statvfs.f_blocks
                disk_usage = (statvfs.f_frsize * statvfs.f_blocks) - (statvfs.f_frsize * statvfs.f_bfree)
                root_used = statvfs.f_frsize * statvfs.f_bfree - statvfs.f_frsize * statvfs.f_bavail
                disk_free = disk_total - disk_usage - root_used
                try:
                    disk_pre = disk_usage / (disk_total - root_used) * 100
                except:
                    disk_pre = 0

                # 获取inode信息
                inodes_used = statvfs.f_files - statvfs.f_ffree
                try:
                    inodes_pre = inodes_used / statvfs.f_files * 100
                except:
                    inodes_pre = 0
                tmp = {}
                tmp['byte_size'] = [disk_total, disk_usage, disk_free]
                tmp['path'] = disk.mountpoint.replace('/usr/local/lighthouse/softwares/btpanel', '/www')
                disk_total = self.to_size(disk_total)
                disk_usage = self.to_size(disk_usage)
                new_disk_usage = disk_usage
                if disk_total[-2:] == disk_usage[-2:]:
                    new_disk_usage = disk_usage[:-2]
                    if new_disk_usage.endswith("0"):
                        new_disk_usage = new_disk_usage[:-2]

                tmp['size'] = [disk_total, disk_usage, self.to_size(disk_free), "{:.2f}%".format(disk_pre), self.to_size(root_used), new_disk_usage.strip()]
                tmp['filesystem'] = disk.device
                tmp['type'] = disk.fstype
                tmp['inodes'] = [statvfs.f_files,inodes_used,statvfs.f_ffree,"{:.2f} %".format(inodes_pre)]

                if disk_info_dict:
                    main_part = disk_info_dict.get(disk.device, {}).get('main_part', None)
                    if main_part and main_part in disk_info_dict:
                        tmp['d_size'] = disk_info_dict[main_part]['SIZE']
                    else:
                        tmp['d_size'] = 'None'
                else:
                    tmp['d_size'] = 'None'

                diskInfo.append(tmp)
                processed_devices.add(disk.device)
                processed_mountpoints.add(disk.mountpoint)

            if disk_info_dict:
                existing_filesystems = {entry["filesystem"] for entry in diskInfo}
                mounted_main_parts = set()
                for fs in existing_filesystems:
                    if fs in disk_info_dict:
                        main_part = disk_info_dict[fs]["main_part"]
                        mounted_main_parts.add(main_part)

                unmounted_main_parts = set(disk_info_dict[device]["main_part"] for device in disk_info_dict if disk_info_dict[device]["main_part"] not in mounted_main_parts)
                unmounted_devices_info = [info for device, info in disk_info_dict.items() if info["main_part"] not in
                mounted_main_parts and info["TYPE"] == "disk"]

                new_device_info = []
                for device_info in unmounted_devices_info:
                    if device_info.get('MOUNTPOINT'):
                        continue
                    n_tmp = {}
                    n_tmp['path'] = "None"
                    n_tmp['size'] = device_info['SIZE']
                    n_tmp['type'] = device_info['TYPE']
                    n_tmp['filesystem'] = device_info['NAME']
                    if 'vda' in n_tmp['filesystem'] or 'sda' in n_tmp['filesystem'] or 'xvda' in n_tmp['filesystem']:
                        continue
                    if n_tmp['size'].endswith('M') or n_tmp['size'].endswith('B') or n_tmp['size'].endswith('K'):
                        continue
                    new_device_info.append(n_tmp)
                diskInfo.extend(new_device_info)

            return diskInfo
        except:
            print(public.get_error_info())
            # 如果出错则调用旧的获取磁盘信息方法
            return self.GetDiskInfo2()

    def GetDiskInfo2(self, human=True):

        # 取磁盘分区信息
        key = f'sys_disk_{human}'
        try:
            diskInfo = cache.get(key)
            if diskInfo: return diskInfo
        except:
            pass
        if human:
            temp = public.ExecShell("df -hT -P|grep '/'|grep -v tmpfs|grep -v 'snap/core'|grep -v udev")[0]
        else:
            temp = public.ExecShell("df -T -P|grep '/'|grep -v tmpfs|grep -v 'snap/core'|grep -v udev")[0]
        tempInodes = public.ExecShell("df -i -P|grep '/'|grep -v tmpfs|grep -v 'snap/core'|grep -v udev")[0]
        temp1 = temp.split('\n')
        tempInodes1 = tempInodes.split('\n')
        diskInfo = []
        n = 0
        cuts = ['/mnt/cdrom', '/boot', '/boot/efi', '/dev', '/dev/shm', '/run/lock', '/run', '/run/shm', '/run/user']
        for tmp in temp1:
            n += 1
            try:
                inodes = tempInodes1[n - 1].split()
                disk = re.findall(r"^(.+)\s+([\w\.]+)\s+([\w\.]+)\s+([\w\.]+)\s+([\w\.]+)\s+([\d%]{2,4})\s+(/.{0,100})$", tmp.strip().replace(',', '.'))
                if disk: disk = disk[0]
                if len(disk) < 6: continue
                # if disk[2].find('M') != -1: continue
                if disk[2].find('K') != -1: continue
                if len(disk[6].split('/')) > 10: continue
                if disk[6] in cuts: continue
                if str(disk[6]).startswith("/snap"): continue
                if disk[6].find('docker') != -1: continue
                if disk[1].strip() in ['tmpfs']: continue
                arr = {}
                arr['filesystem'] = disk[0].strip()
                arr['type'] = disk[1].strip()
                arr['path'] = disk[6].replace('/usr/local/lighthouse/softwares/btpanel', '/www')
                tmp1 = [disk[2], disk[3], disk[4], disk[5]]
                arr['size'] = tmp1
                arr['inodes'] = [inodes[1], inodes[2], inodes[3], inodes[4]]
                diskInfo.append(arr)
            except Exception as ex:
                public.WriteLog('信息获取', str(ex))
                continue
        cache.set(key, diskInfo, 10)
        return diskInfo

    # 获取磁盘IO开销数据
    def get_disk_iostat(self):
        iokey = 'iostat'
        diskio = cache.get(iokey)
        mtime = int(time.time())
        if not diskio:
            diskio = {}
            diskio['info'] = None
            diskio['time'] = mtime
        diskio_1 = diskio['info']
        stime = mtime - diskio['time']
        if not stime: stime = 1
        diskInfo = {}
        diskInfo['ALL'] = {}
        diskInfo['ALL']['read_count'] = 0
        diskInfo['ALL']['write_count'] = 0
        diskInfo['ALL']['read_bytes'] = 0
        diskInfo['ALL']['write_bytes'] = 0
        diskInfo['ALL']['read_time'] = 0
        diskInfo['ALL']['write_time'] = 0
        diskInfo['ALL']['read_merged_count'] = 0
        diskInfo['ALL']['write_merged_count'] = 0
        try:
            if os.path.exists('/proc/diskstats'):
                diskio_2 = psutil.disk_io_counters(perdisk=True)
                if not diskio_1:
                    diskio_1 = diskio_2
                for disk_name in diskio_2.keys():
                    diskInfo[disk_name] = {}
                    diskInfo[disk_name]['read_count'] = int((diskio_2[disk_name].read_count - diskio_1[disk_name].read_count) / stime)
                    diskInfo[disk_name]['write_count'] = int((diskio_2[disk_name].write_count - diskio_1[disk_name].write_count) / stime)
                    diskInfo[disk_name]['read_bytes'] = int((diskio_2[disk_name].read_bytes - diskio_1[disk_name].read_bytes) / stime)
                    diskInfo[disk_name]['write_bytes'] = int((diskio_2[disk_name].write_bytes - diskio_1[disk_name].write_bytes) / stime)
                    diskInfo[disk_name]['read_time'] = int((diskio_2[disk_name].read_time - diskio_1[disk_name].read_time) / stime)
                    diskInfo[disk_name]['write_time'] = int((diskio_2[disk_name].write_time - diskio_1[disk_name].write_time) / stime)
                    diskInfo[disk_name]['read_merged_count'] = int((diskio_2[disk_name].read_merged_count - diskio_1[disk_name].read_merged_count) / stime)
                    diskInfo[disk_name]['write_merged_count'] = int((diskio_2[disk_name].write_merged_count - diskio_1[disk_name].write_merged_count) / stime)

                    diskInfo['ALL']['read_count'] += diskInfo[disk_name]['read_count']
                    diskInfo['ALL']['write_count'] += diskInfo[disk_name]['write_count']
                    diskInfo['ALL']['read_bytes'] += diskInfo[disk_name]['read_bytes']
                    diskInfo['ALL']['write_bytes'] += diskInfo[disk_name]['write_bytes']
                    if diskInfo['ALL']['read_time'] < diskInfo[disk_name]['read_time']:
                        diskInfo['ALL']['read_time'] = diskInfo[disk_name]['read_time']
                    if diskInfo['ALL']['write_time'] < diskInfo[disk_name]['write_time']:
                        diskInfo['ALL']['write_time'] = diskInfo[disk_name]['write_time']
                    diskInfo['ALL']['read_merged_count'] += diskInfo[disk_name]['read_merged_count']
                    diskInfo['ALL']['write_merged_count'] += diskInfo[disk_name]['write_merged_count']

                cache.set(iokey, {'info': diskio_2, 'time': mtime})
        except:
            return diskInfo
        return diskInfo

    # 清理系统垃圾
    def ClearSystem(self, get):
        count = total = 0
        tmp_total, tmp_count = self.ClearMail()
        count += tmp_count
        total += tmp_total
        tmp_total, tmp_count = self.ClearOther()
        count += tmp_count
        total += tmp_total
        return count, total

    # 清理邮件日志
    def ClearMail(self):
        rpath = '/var/spool'
        total = count = 0
        import shutil
        con = ['cron', 'anacron', 'mail']
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
                num += 1
            total += size
            count += num
        return total, count

    # 清理其它
    def ClearOther(self):
        clearPath = [
            {'path': '/www/server/panel', 'find': 'testDisk_'},
            {'path': '/www/wwwlogs', 'find': 'log'},
            {'path': '/tmp', 'find': 'panelBoot.pl'},
            {'path': '/www/server/panel/install', 'find': '.rpm'}
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
        return total, count
    def set_rname(self, get):
        try:
            config_path = '/www/server/panel/data/set_disk_rname.json'
            if not 'path' in get: return public.returnMsg(False, 'INIT_ARGS_ERR')
            if not 'name' in get: return public.returnMsg(False, 'INIT_ARGS_ERR')
            if not os.path.exists(config_path): public.writeFile(config_path, '{}')
            config = json.loads(public.readFile(config_path))
            config[get.path] = get.name
            public.writeFile(config_path, json.dumps(config))
            return public.returnMsg(True, '设置成功！')
        except:
            return public.returnMsg(False, '设置失败！')

    def GetNetWork(self, get=None):
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
        try:
            networkIo_list = psutil.net_io_counters(pernic=True)
            for net_key in networkIo_list.keys():
                networkIo = networkIo_list[net_key][:4]
                up_key = "{}_up".format(net_key)
                down_key = "{}_down".format(net_key)
                otime_key = "otime"

                if not otime:
                    otime = time.time()

                    cache.set(up_key, networkIo[0], cache_timeout)
                    cache.set(down_key, networkIo[1], cache_timeout)
                    cache.set(otime_key, otime, cache_timeout)

                networkInfo['network'][net_key] = {}
                up = cache.get(up_key)
                down = cache.get(down_key)
                if not up:
                    up = networkIo[0]
                if not down:
                    down = networkIo[1]
                networkInfo['network'][net_key]['upTotal'] = networkIo[0]
                networkInfo['network'][net_key]['downTotal'] = networkIo[1]
                try:
                    networkInfo['network'][net_key]['up'] = round(float(networkIo[0] - up) / 1024 / (ntime - otime), 2)
                except:
                    networkInfo['network'][net_key]['up'] = 0
                try:
                    networkInfo['network'][net_key]['down'] = round(float(networkIo[1] - down) / 1024 / (ntime - otime), 2)
                except:
                    networkInfo['network'][net_key]['down'] = 0
                networkInfo['network'][net_key]['downPackets'] = networkIo[3]
                networkInfo['network'][net_key]['upPackets'] = networkIo[2]

                networkInfo['upTotal'] += networkInfo['network'][net_key]['upTotal']
                networkInfo['downTotal'] += networkInfo['network'][net_key]['downTotal']
                networkInfo['up'] += networkInfo['network'][net_key]['up']
                networkInfo['down'] += networkInfo['network'][net_key]['down']
                networkInfo['downPackets'] += networkInfo['network'][net_key]['downPackets']
                networkInfo['upPackets'] += networkInfo['network'][net_key]['upPackets']

                cache.set(up_key, networkIo[0], cache_timeout)
                cache.set(down_key, networkIo[1], cache_timeout)
                cache.set(otime_key, time.time(), cache_timeout)
        except:
            networkInfo['network'] = {}
            networkInfo['upTotal'] = 0
            networkInfo['downTotal'] = 0
            networkInfo['up'] = 0
            networkInfo['down'] = 0
            networkInfo['downPackets'] = 0
            networkInfo['upPackets'] = 0

        if get != False:
            networkInfo['cpu'] = self.GetCpuInfo(1)
            networkInfo['cpu_times'] = self.get_cpu_times()
            networkInfo['load'] = self.GetLoadAverage(get)
            networkInfo['mem'] = self.GetMemInfo(get)
            networkInfo['version'] = session['version']
            disk_list = []
            rname_config = {}
            if os.path.exists('/www/server/panel/data/set_disk_rname.json'):
                rname_config = json.loads(public.readFile('/www/server/panel/data/set_disk_rname.json'))
            for disk in self.GetDiskInfo():
                disk['rname'] = rname_config.get(disk['path'], disk['path'])
                disk_list.append(disk)
            networkInfo['disk'] = disk_list

        networkInfo['title'] = self.GetTitle()
        networkInfo['time'] = self.GetBootTime()
        networkInfo['site_total'] = public.M('sites').count()
        networkInfo['ftp_total'] = public.M('ftps').count()
        networkInfo['database_total'] = public.M('databases').count()
        networkInfo['system'] = self.GetSystemVersion()
        networkInfo['simple_system'] = networkInfo['system'].split(' ')[0] + ' ' + re.search('\d+', networkInfo['system']).group()
        networkInfo['installed'] = self.CheckInstalled()
        # import panelSSL
        # networkInfo['user_info'] = panelSSL.panelSSL().GetUserInfo(None)
        networkInfo['up'] = round(float(networkInfo['up']), 2)
        networkInfo['down'] = round(float(networkInfo['down']), 2)
        networkInfo['iostat'] = self.get_disk_iostat()

        try:
            system_comm=public.ReadFile('/proc/1/comm').strip("\n")
            if system_comm != 'systemd':
                networkInfo['docker_run'] = True
            else:
                networkInfo['docker_run'] = False
        except:
            networkInfo['docker_run'] = False


        return networkInfo

    def get_cpu_times(self):
        # skey = 'cpu_times'
        # data = cache.get(skey)
        # if data: return data
        # psutil.cpu_times_percent() 本来就有缓存，无需使用cache再次缓存
        try:
            data = {}
            cpu_times_p = psutil.cpu_times_percent()
            data['user'] = cpu_times_p.user
            data['nice'] = cpu_times_p.nice
            data['system'] = cpu_times_p.system
            data['idle'] = cpu_times_p.idle
            data['iowait'] = cpu_times_p.iowait
            data['irq'] = cpu_times_p.irq
            data['softirq'] = cpu_times_p.softirq
            data['steal'] = cpu_times_p.steal
            try:
                data['guest'] = cpu_times_p.guest
                data['guest_nice'] = cpu_times_p.guest_nice
            except:
                data['guest'] = 0
                data['guest_nice'] = 0
            data['总进程数'] = 0
            data['活动进程数'] = 0
            for pid in psutil.pids():
                try:
                    p = psutil.Process(pid)
                    if p.status() == 'running':
                        data['活动进程数'] += 1
                except:
                    continue
                data['总进程数'] += 1
            # cache.set(skey, data, 60)
        except:
            public.print_log(public.get_error_info())
            return None
        return data

    def GetNetWorkApi(self, get=None):
        return self.GetNetWork()

    # 检查是否安装任何
    def CheckInstalled(self):
        checks = ['nginx', 'apache', 'php', 'pure-ftpd', 'mysql']
        import os
        for name in checks:
            filename = public.get_panel_path() + "/server/" + name
            if os.path.exists(filename): return True
        return False

    # 字节单位转换
    def to_size(self, size, sub=False):
        if not size: return '0.00 b'
        size = float(size)
        d = ('b', 'KB', 'MB', 'GB', 'TB')
        s = d[0]
        for b in d:
            if sub:
                if size < 1024: return ("%.1f" % size)

            if size < 1024: return ("%.1f" % size) + ' ' + b
            size = size / 1024
            s = b
        return ("%.1f" % size) + ' ' + b

    def GetNetWorkOld(self):
        # 取网络流量信息
        import time;
        pnet = public.readFile('/proc/net/dev')
        rep = '([^\s]+):[\s]{0,}(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)'
        pnetall = re.findall(rep, pnet)
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
            cache.set('up', networkInfo['upTotal'], cache_timeout)
            cache.set('down', networkInfo['downTotal'], cache_timeout)
            cache.set('otime', otime, cache_timeout)

        ntime = time.time()
        tmpDown = networkInfo['downTotal'] - cache.get("down")
        tmpUp = networkInfo['upTotal'] - cache.get("up")
        networkInfo['down'] = str(round(float(tmpDown) / 1024 / (ntime - otime), 2))
        networkInfo['up'] = str(round(float(tmpUp) / 1024 / (ntime - otime), 2))
        if networkInfo['down'] < 0: networkInfo['down'] = 0
        if networkInfo['up'] < 0: networkInfo['up'] = 0

        otime = time.time()
        cache.set('up', networkInfo['upTotal'], cache_timeout)
        cache.set('down', networkInfo['downTotal'], cache_timeout)
        cache.set('otime', ntime, cache_timeout)

        networkInfo['cpu'] = self.GetCpuInfo()
        return networkInfo

    # 取IO读写信息
    def get_io_info(self, get=None):
        io_disk = psutil.disk_io_counters()
        ioTotal = {}
        ioTotal['write'] = self.get_io_write(io_disk.write_bytes)
        ioTotal['read'] = self.get_io_read(io_disk.read_bytes)
        return ioTotal

    # 取IO写
    def get_io_write(self, io_write):
        disk_io_write = 0
        old_io_write = cache.get('io_write')
        if not old_io_write:
            cache.set('io_write', io_write)
            return disk_io_write

        old_io_time = cache.get('io_time')
        new_io_time = time.time()
        if not old_io_time: old_io_time = new_io_time
        io_end = (io_write - old_io_write)
        time_end = (time.time() - old_io_time)
        if io_end > 0:
            if time_end < 1: time_end = 1
            disk_io_write = io_end / time_end
        cache.set('io_write', io_write)
        cache.set('io_time', new_io_time)
        if disk_io_write > 0: return int(disk_io_write)
        return 0

    # 取IO读
    def get_io_read(self, io_read):
        disk_io_read = 0
        old_io_read = cache.get('io_read')
        if not old_io_read:
            cache.set('io_read', io_read)
            return disk_io_read
        old_io_time = cache.get('io_time')
        new_io_time = time.time()
        if not old_io_time: old_io_time = new_io_time
        io_end = (io_read - old_io_read)
        time_end = (time.time() - old_io_time)
        if io_end > 0:
            if time_end < 1: time_end = 1
            disk_io_read = io_end / time_end
        cache.set('io_read', io_read)
        if disk_io_read > 0: return int(disk_io_read)
        return 0

    # 检查并修复MySQL目录权限
    def __check_mysql_path(self):
        try:
            # 获取datadir路径
            mypath = '/etc/my.cnf'
            if not os.path.exists(mypath): return False
            public.set_mode(mypath, 644)
            mycnf = public.readFile(mypath)
            tmp = re.findall('datadir\s*=\s*(.+)', mycnf)
            if not tmp: return False
            datadir = tmp[0]

            # 可以被启动的权限
            accs = ['755', '777']

            # 处理data目录权限
            mode_info = public.get_mode_and_user(datadir)
            if not mode_info['mode'] in accs or mode_info['user'] != 'mysql':
                public.ExecShell('chmod 755 ' + datadir)
                public.ExecShell('chown -R mysql:mysql ' + datadir)

            # 递归处理父目录权限
            datadir = os.path.dirname(datadir)
            while datadir != '/':
                if datadir == '/': break
                mode_info = public.get_mode_and_user(datadir)
                if not mode_info['mode'] in accs:
                    public.ExecShell('chmod 755 ' + datadir)
                datadir = os.path.dirname(datadir)
        except:
            pass

    def ServiceAdmin(self, get=None):
        # 服务管理
        if not "name" in get: return public.returnMsg(False, '请传入name参数')
        if not "type" in get: return public.returnMsg(False, '请传入type参数')
        if get.name == 'mysqld':
            if not os.path.exists('/www/server/mysql/sys_install.pl'):
                public.CheckMyCnf()
            self.__check_mysql_path()
        if get.name.find('webserver') != -1:
            get.name = public.get_webserver()

        if get.name == 'phpmyadmin':
            import ajax
            get.status = 'True'
            ajax.ajax().setPHPMyAdmin(get)
            return public.returnMsg(True, 'SYS_EXEC_SUCCESS')

        if get.name == 'openlitespeed':
            if get.type == 'stop':
                public.ExecShell('rm -f /tmp/lshttpd/*.sock* && /usr/local/lsws/bin/lswsctrl stop')
            elif get.type == 'start':
                public.ExecShell('rm -f /tmp/lshttpd/*.sock* && /usr/local/lsws/bin/lswsctrl start')
            else:
                public.ExecShell('rm -f /tmp/lshttpd/*.sock* && /usr/local/lsws/bin/lswsctrl restart')
            return public.returnMsg(True, 'SYS_EXEC_SUCCESS')

        # 检查httpd配置文件
        if get.name == 'apache' or get.name == 'httpd':
            if not os.path.exists("/etc/init.d/httpd"):
                return public.returnMsg(True, 'apache启动文件丢失，请尝试重装apache后再试！')

            get.name = 'httpd'
            if not os.path.exists(self.setupPath + '/apache/bin/apachectl'): return public.returnMsg(True, 'SYS_NOT_INSTALL_APACHE')
            vhostPath = self.setupPath + '/panel/vhost/apache'
            if not os.path.exists(vhostPath):
                public.ExecShell('mkdir ' + vhostPath)
                public.ExecShell('/etc/init.d/httpd start')

            if get.type == 'start':
                public.ExecShell('/etc/init.d/httpd stop')
                # self.kill_port()

            result = public.ExecShell('ulimit -n 8192 ; ' + self.setupPath + '/apache/bin/apachectl -t')
            if result[1].find('Syntax OK') == -1:
                public.WriteLog("TYPE_SOFT", 'SYS_EXEC_ERR', (str(result),))

                err = result[1]
                try:
                    version = public.ExecShell("{}/apache/bin/httpd -v".format(self.setupPath))
                    err = '{}\n{}'.format(version[1],result[1]).replace("\n", '<br>')
                except:pass
                return public.returnMsg(False, 'SYS_CONF_APACHE_ERR', (err,))

            if get.type == 'restart':
                public.ExecShell('pkill -9 httpd')
                public.ExecShell('/etc/init.d/httpd start')
                time.sleep(0.5)

        # 检查nginx配置文件
        elif get.name == 'nginx':

            if os.path.exists('/www/server/nginx/sys_install.pl'):
                systemd_list = self.GetSystemdList()
                for line in systemd_list:
                    if "nginx.service" in line:
                        execStr = "systemctl {} {}".format(get.type,line)
                        break
                if execStr == '':
                    if os.path.exists('/etc/init.d/nginx'):
                        execStr = "/etc/init.d/nginx {}".format(get.type)
                    else:
                        return public.returnMsg(True, '找不到系统nginx启动文件，请检查是否存在/etc/init.d/nginx或nginx.service')
                public.ExecShell(execStr)
                return public.returnMsg(True, 'SYS_EXEC_SUCCESS')


            if not os.path.exists("/etc/init.d/nginx"):
                return public.returnMsg(True, 'nginx启动文件丢失，请尝试重装nginx后再试！')

            vhostPath = self.setupPath + '/panel/vhost/rewrite'
            if not os.path.exists(vhostPath): public.ExecShell('mkdir ' + vhostPath)
            vhostPath = self.setupPath + '/panel/vhost/nginx'
            if not os.path.exists(vhostPath):
                public.ExecShell('mkdir ' + vhostPath)
                public.ExecShell('/etc/init.d/nginx start')

            if not public.checkWebConfig() is True:
                result = public.ExecShell('ulimit -n 8192 ; ' + self.setupPath + '/nginx/sbin/nginx -t -c ' + self.setupPath + '/nginx/conf/nginx.conf')
                if result[1].find('perserver') != -1:
                    limit = self.setupPath + '/nginx/conf/nginx.conf'
                    nginxConf = public.readFile(limit)
                    limitConf = "limit_conn_zone $binary_remote_addr zone=perip:10m;\n\t\tlimit_conn_zone $server_name zone=perserver:10m;"
                    nginxConf = nginxConf.replace("#limit_conn_zone $binary_remote_addr zone=perip:10m;", limitConf)
                    public.writeFile(limit, nginxConf)
                    public.ExecShell('/etc/init.d/nginx start')
                    return public.returnMsg(True, 'SYS_CONF_NGINX_REP')

                if result[1].find('proxy') != -1:
                    import panelSite
                    panelSite.panelSite().CheckProxy(get)
                    public.ExecShell('/etc/init.d/nginx start')
                    return public.returnMsg(True, 'SYS_CONF_NGINX_REP')

                # return result
                if result[1].find('successful') == -1:
                    public.WriteLog("TYPE_SOFT", 'SYS_EXEC_ERR', (str(result),))

                    err = result[1]
                    try:
                        version = public.ExecShell("{}/nginx/sbin/nginx -v".format(self.setupPath))
                        err = '{}\n{}'.format(version[1],result[1]).replace("\n", '<br>')
                    except:pass

                    return public.returnMsg(False, 'SYS_CONF_NGINX_ERR', (err,))

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

        # 执行
        execStr = "/etc/init.d/" + get.name + " " + get.type
        if get.name in ('redis',):
            execStr = "/etc/init.d/redis {}".format(get.type)
            if os.path.exists('/usr/lib/systemd/system/redis.service'):
                redis_service = public.ReadFile('/usr/lib/systemd/system/redis.service')
                if "/www/server/redis/" in redis_service:
                    execStr = "systemctl {} redis".format(get.type)
        if execStr == '/etc/init.d/pure-ftpd reload': execStr = self.setupPath + '/pure-ftpd/bin/pure-pw mkdb ' + self.setupPath + '/pure-ftpd/etc/pureftpd.pdb'
        if execStr == '/etc/init.d/pure-ftpd start': public.ExecShell('pkill -9 pure-ftpd')
        if execStr == '/etc/init.d/tomcat reload': execStr = '/etc/init.d/tomcat stop && /etc/init.d/tomcat start'
        if execStr == '/etc/init.d/tomcat restart': execStr = '/etc/init.d/tomcat stop && /etc/init.d/tomcat start'

        if get.name != 'mysqld':
            result = public.ExecShell(execStr)
        else:
            #系统mysql判断
            if os.path.exists('/www/server/mysql/sys_install.pl'):
                service_list=['mysql','mariadb','mysqld','mariadbd']
                systemd_list = self.GetSystemdList()
                for line in systemd_list:
                    for service in service_list:
                        if service + ".service" in line:
                            execStr = "systemctl {} {}".format(get.type,line)
                            break
                if execStr == '':
                    for service in service_list:
                        if os.path.exists('/etc/init.d/' + service):
                            execStr = "/etc/init.d/{} {}".format(service,get.type)
                            break
            public.ExecShell(execStr)
            result = []
            result.append('')
            result.append('')
            
        if result[1].find('nginx.pid') != -1:
            public.ExecShell('pkill -9 nginx && sleep 1')
            public.ExecShell('/etc/init.d/nginx start')
        if get.type != 'test':
            public.WriteLog("TYPE_SOFT", 'SYS_EXEC_SUCCESS', (execStr,))

        if get.type != 'stop':
            n = 0
            num = 5
            while not self.check_service_status(get.name):
                if get.name == 'nginx':
                    res = public.ExecShell('/etc/init.d/nginx status')
                    if res[1].find('already running') == -1:
                        public.ExecShell('/etc/init.d/nginx start')
                else:
                    public.ExecShell("systemctl {} {}".format(get.type,get.name))
                time.sleep(0.5)
                n += 1
                if n > num: break

            if not self.check_service_status(get.name):
                err = public.ExecShell(execStr)[1]
                if err is not None and len(err) >= 2:
                    err_id = err.split("\n")[-2].strip() if err.split("\n")[-1].strip() == "" else err.split("\n")[-1].strip()
                else:
                    err_id = str(err).strip()
                public.err_collect(err, 0, err_id)

                if len(result[1]) > 1 and get.name != 'pure-ftpd' and get.name != 'redis':
                    return public.returnMsg(False, '<p>启动失败： <p>' + result[1].replace('\n', '<br>'))
                else:
                    return public.returnMsg(False, '{}服务启动失败'.format(get.name))
        elif get.name in ['mysqld', 'mariadbd', 'redis', 'pure-ftpd', 'php-fpm', 'nginx', 'httpd', 'apache', 'memcached', 'mongodb']:
            # 等待进程停止运行
            n = 0
            num = 5
            while self.check_service_status(get.name):
                time.sleep(0.5)
                n += 1
                if n > num: break

            if get.name.find('php-fpm') != -1:
                _php_version = get.name.split('-')[-1]
                is_static, _ = public.ExecShell("grep \"pm = static\" /www/server/php/{}/etc/php-fpm.conf".format(_php_version))
                if is_static and get.type == "stop":
                    return public.returnMsg(True, 'SYS_EXEC_SUCCESS')

            if n > num:  # 超时
                return public.returnMsg(False, '服务停止失败!')
        return public.returnMsg(True, 'SYS_EXEC_SUCCESS')

    def check_service_status(self, name):
        '''
            @name 检查服务管理状态
            @author hwliang
            @param name<string> 服务名称
            @return bool
        '''
        if name in ['mysqld', 'mariadbd']:
            if os.path.exists('/www/server/mysql/sys_install.pl'):
                return self.GetProcessStatus('mysql')
            return public.is_mysql_process_exists()
        elif name == 'redis':
            return public.is_redis_process_exists()
        elif name == 'pure-ftpd':
            return public.is_pure_ftpd_process_exists()
        elif name.find('php-fpm') != -1:
            return public.is_php_fpm_process_exists(name)
        elif name == 'nginx':
            return public.is_nginx_process_exists()
        elif name in ['httpd', 'apache']:
            return public.is_httpd_process_exists()
        elif name == 'memcached':
            return public.is_memcached_process_exists()
        elif name == 'mongodb':
            return public.is_mongodb_process_exists()
        else:
            return True

    def RestartServer(self, get):
        if not public.IsRestart(): return public.returnMsg(False, 'EXEC_ERR_TASK')
        public.ExecShell("sync && init 6 &")
        return public.returnMsg(True, 'SYS_REBOOT')

    def kill_port(self):
        public.ExecShell('pkill -9 httpd')
        public.ExecShell('pkill -9 nginx')
        public.ExecShell("kill -9 $(lsof -i :80|grep LISTEN|awk '{print $2}')")
        return True

    # 释放内存
    def ReMemory(self, get):
        public.ExecShell('sync')
        scriptFile = 'script/rememory.sh'
        if not os.path.exists(scriptFile):
            public.downloadFile(public.GetConfigValue('home') + '/script/rememory.sh', scriptFile)
        public.ExecShell("/bin/bash " + self.setupPath + '/panel/' + scriptFile)
        return self.GetMemInfo()

    # 重启面板
    def ReWeb(self, get):
        import subprocess
        public.ExecShell("/etc/init.d/bt start")
        public.writeFile('data/restart.pl', 'True')
        # public.ExecShell("chmod +x /www/server/panel/script/set_fastest_pip_source.sh ")
        # # 执行脚本并获取输出
        # subprocess.check_output(["/www/server/panel/script/set_fastest_pip_source.sh"], shell=True)
        return public.returnMsg(True, '面板已重启')

    def ReloadWeb(self, get):
        """
        @name 重载面板,不重启task进程
        """
        public.ExecShell("/etc/init.d/bt reload")
        return public.returnMsg(True, '面板已重启')

    def reload_task(self, get):
        """
        @name 重载task进程
        """

        public.ExecShell("/www/server/panel/BT-Task")
        return public.returnMsg(True, '后台进程已重启完毕')

    """
    @name 线程里修复面板，减少等待时间
    """
    def _repair_panel(self,get):
        pfile = public.get_panel_path()
        log_file = '{}/data/repair.log'.format(pfile)
        nfile = '{}/script/local_fix.sh'.format(pfile)
        if not os.path.exists(nfile):
            os.system('btpython /www/server/panel/script/reload_check.py repair')
            public.ExecShell("wget --no-check-certificate -O update.sh " + public.get_url() + "/install/update6.sh && bash update.sh")
        else:
            public.ExecShell('bash {} 2>&1 > {}'.format(nfile,log_file))

        self.ReWeb(None)
        return True

    # 修复面板
    def RepPanel(self, get):
        public.ExecShell("chmod +x /www/server/panel/script/clean_crontab.sh")
        public.ExecShell("nohup /www/server/panel/script/clean_crontab.sh > /www/clean_crontab.txt 2>&1 &")
        public.writeFile('data/js_random.pl', '1')
        public.run_thread(self._repair_panel, (get,))
        return True

    @staticmethod
    def _normalize_version(version_str: str) -> Tuple[int, int, int]:
        try:
            tmp = version_str.split(".")
            if len(tmp) < 3:
                tmp += [0] * (3 - len(tmp))
            return int(tmp[0]), int(tmp[1]), int(tmp[2])
        except:
            return 0, 0, 0

    def upgrade_panel(self, get):
        """
        @name 更新面板(稳定版 lts)
        """
        get.check = get.get("check", True)
        import psutil, ajax
        disk = psutil.disk_usage(public.get_panel_path())
        if disk.free < 50 * 1024 * 1024:
            return public.returnMsg(True, '磁盘空间不足 [50 MB]，无法继续操作.')

        import json
        if int(session['config']['status']) == 0:
            public.HttpGet(
                public.GetConfigValue('home') +
                '/Api/SetupCount?type=Linux')
            public.M('config').where("id=?", ('1',)).setField('status', 1)

        # 取回远程版本信 息
        if 'updateInfo' in session and hasattr(get, 'check') == False:
            updateInfo = session['updateInfo']
        else:
            logs = public.get_debug_log()
            ajax_obj = ajax.ajax()
            mem = psutil.virtual_memory()
            import panelPlugin
            mplugin = panelPlugin.panelPlugin()

            mplugin.ROWS = 10000
            data = public.get_user_info()
            data['ds'] = ''  # self.get_other_info()
            data['sites'] = str(public.M('sites').count())
            data['ftps'] = str(public.M('ftps').count())
            data['databases'] = str(public.M('databases').count())
            data['system'] = self.GetSystemVersion() + '|' + str(mem.total / 1024 / 1024) + 'MB|' + str(public.getCpuType()) + '*' + str(psutil.cpu_count()) + '|' + str(public.get_webserver()) + '|' + session['version']
            data['system'] += '||' + ajax_obj.GetInstalleds(mplugin.getPluginList(None))
            data['logs'] = logs
            data['client'] = request.headers.get('User-Agent')
            data['oem'] = ''
            data['intrusion'] = 0
            data['uid'] = ajax_obj.get_uid()
            # msg = public.getMsg('PANEL_UPDATE_MSG');
            data['o'] = public.get_oem_name()
            sUrl = public.GetConfigValue('home') + '/api/panel/get_panel_version_v3'
            try:
                updateInfo = json.loads(public.httpPost(sUrl, data))
            except:
                return public.returnMsg(False, "CONNECT_ERR")

            if not updateInfo:
                return public.returnMsg(False, "CONNECT_ERR")

            session['updateInfo'] = updateInfo

        # 输出忽略的版本
        updateInfo['ignore'] = []
        no_path = '{}/data/no_update.pl'.format(public.get_panel_path())
        if os.path.exists(no_path):
            try:
                updateInfo['ignore'] = json.loads(public.readFile(no_path))
            except:
                pass

        if not updateInfo:
            return public.returnMsg(False, '无法连接【宝塔官网】，请检查网络原因.')

        if not 'force' in get:
            data = {'local': {}, 'cloud': {}, 'upgrade': 0}
            local_panel_ver = '{}'.format(public.version())
            data['local']['version'] = local_panel_ver
            update_time = public.readFile("{}/config/update_time.pl".format(public.get_panel_path()))
            if not update_time:
                update_time = os.path.getmtime('{}/class/common.py'.format(public.get_panel_path()))

            lockfile_path = os.path.join(public.get_panel_path(), ".upgrade_py313.lock")
            env_update_running = os.path.exists(lockfile_path)
            data['local']['update_time'] = int(update_time)
            data['local']['has_env_py313'] = self._has_py313() and not env_update_running
            data['local']['need_env_check'] = False # 默认为不需要环境检查
            data['local']['plugins_check'] = [] # 默认为不需要插件检查
            data['local']['env_update_running'] = env_update_running
            data['local']['uptime'] = time.strftime('%Y/%m/%d', time.localtime(data['local']['update_time']))
            data['cloud'] = updateInfo

            # 2024/12/24 09:30
            # data['upgrade'] = 0 不需要更新面板，已经是最新的正式版
            # data['upgrade'] = 1 显示小红点，建议更新到推荐的正式版
            # data['upgrade'] = 2 不显示小红点，可以更新到最新的正式版
            # 例子：
            # 例如当前版本是9.2.0，官方推荐安装的正式版版本是9.3.0，那么upgrade=1，此时显示更新小红点，建议更新到9.3.0，不会显示9.4.0的更新提示
            # 例如当前版本是9.3.0，官方最新发布的正式版版本是9.4.0，那么upgrade=2，此时不显示更新小红点，不会显示9.4.0的更新提示，但是点击更新按钮可以获取到9.4.0的更新提示，点击即可更新
            # 例如当前版本已经是9.4.0，官方最新发布的正式版版本是9.4.0，那么upgrade=0，此时不显示更新小红点，点击更新按钮也不会有更新提示，显示当前为最新版正式版
            # 当local比cloud版本高时，upgrade=0
            try:
                c_version = self._normalize_version(data['cloud']['OfficialVersion']['version'])
                if 'OfficialVersionLatest' in data['cloud'] and data['cloud']['OfficialVersionLatest']:
                    lc_version = self._normalize_version(data['cloud']['OfficialVersionLatest']['version'])
                else:
                    lc_version = self._normalize_version(data['local']['version'])
                l_version = self._normalize_version(data['local']['version'])
                if lc_version > l_version:
                    data['upgrade'] = 2
                elif c_version > l_version:
                    data['upgrade'] = 1
                else:
                    data['upgrade'] = 0
            except:
                data['upgrade'] = 1

            down_url = 'http://download.bt.cn/install/update/LinuxPanel-{}.pl'.format(data['local']['version'])
            if os.path.exists("/tmp/LinuxPanel-{}.pl".format(data['local']['version'])):
                os.remove("/tmp/LinuxPanel-{}.pl".format(data['local']['version']))
            public.downloadFile(down_url, "/tmp/LinuxPanel-{}.pl".format(data['local']['version']))
            try:
                pl_info = json.loads(public.readFile("/tmp/LinuxPanel-{}.pl".format(data['local']['version'])))
                if int(pl_info['update_time']) > int(data['local']['update_time']):
                    data['cloud']['hash'] = pl_info['hash']
                    data['cloud']['update_time'] = pl_info['update_time']
                    data['cloud']['version'] = data['local']['version']
            except:
                data['upgrade'] = 0

            target_v = {}
            if data['upgrade'] == 1:
                target_v = data['cloud'].get('OfficialVersion', {})
            elif data['upgrade'] == 2:
                target_v = data['cloud'].get('OfficialVersionLatest', {})

            plugin_restrictions = target_v.get("plugin_restrictions", {})
            if isinstance(plugin_restrictions, dict):
                py_check = plugin_restrictions.get("python", "3.7") == '3.13'
                if py_check:
                    data['local']['need_env_check'] = True
                    data['local']['plugins_check'] = self._get_plugin_for_py313()

            return data
        else:
            get.version = get.get("version", None)
            if get.version is None:
                return public.returnMsg(False, '版本号不能为空')

            update_time_file = "{}/config/update_time.pl".format(public.get_panel_path())
            if os.path.exists(update_time_file):
                os.remove(update_time_file)
            try:
                pl_info = json.loads(public.readFile("/tmp/LinuxPanel-{}.pl".format(public.version())))
                public.writeFile(update_time_file, str(pl_info['update_time']))
            except:
                pass

            logPath = '/tmp/upgrade_panel.log'
            public.writeFile(logPath, "")
            shell = 'nohup {} -u {}/script/upgrade_panel_optimized.py upgrade_panel {} &>{} &'.format(public.get_python_bin(), public.get_panel_path(), get.version, logPath)
            public.ExecShell(shell)

            return public.returnMsg(True, '面板更新任务已启动，请稍后查看修复结果')


    def repair_panel(self, get):
        """
        @name 修复面板(稳定版 lts)
        """
        disk = psutil.disk_usage(public.get_panel_path())
        if disk.free < 50 * 1024 * 1024:
            return public.returnMsg(True, '磁盘空间不足 [50 MB]，无法继续操作.')

        # 2024/12/10 11:55 处理修复面板异常的进程
        pids = psutil.pids()
        for pid in pids:
            try:
                p = psutil.Process(pid)
                if "python3" in p.name():
                    if "repair_panel" in p.cmdline()[-1]:
                        public.ExecShell("kill -9 {}".format(pid))
            except:
                pass

        if not 'force' in get:
            data = {'local':{},'cloud':{}, 'upgrade':0}
            data['local']['version'] = '{}'.format(public.version())
            update_time = public.readFile("{}/config/update_time.pl".format(public.get_panel_path()))
            if not update_time:
                update_time = os.path.getmtime('{}/class/common.py'.format(public.get_panel_path()))

            data['local']['update_time'] = int(update_time)
            try:
                down_url = 'http://download.bt.cn/install/update/LinuxPanel-{}.pl'.format(data['local']['version'])
                if os.path.exists("/tmp/LinuxPanel-{}.pl".format(data['local']['version'])):
                    os.remove("/tmp/LinuxPanel-{}.pl".format(data['local']['version']))
                public.downloadFile(down_url, "/tmp/LinuxPanel-{}.pl".format(data['local']['version']))
                try:
                    pl_info = json.loads(public.readFile("/tmp/LinuxPanel-{}.pl".format(data['local']['version'])))
                    if int(pl_info['update_time']) > int(data['local']['update_time']):
                        data['upgrade'] = 1
                        data['cloud'] = {}
                        data['cloud']['hash'] = pl_info['hash']
                        data['cloud']['update_time'] = pl_info['update_time']
                        data['cloud']['version'] = data['local']['version']
                except:
                    data['upgrade'] = 0
            except:
                data['upgrade'] = 1

            return data
        else:
            update_time_file = "{}/config/update_time.pl".format(public.get_panel_path())
            if os.path.exists(update_time_file):
                os.remove(update_time_file)
            try:
                pl_info = json.loads(public.readFile("/tmp/LinuxPanel-{}.pl".format(public.version())))
                public.writeFile(update_time_file, str(pl_info['update_time']))
            except:
                pass

            logPath = '/tmp/upgrade_panel.log'
            public.writeFile(logPath, "")
            shell = 'nohup {} -u {}/script/upgrade_panel_optimized.py repair_panel {} &>{} &'.format(public.get_python_bin(), public.get_panel_path(), public.version(), logPath)
            public.ExecShell(shell)

            return public.returnMsg(True, '面板修复任务已启动，请稍后查看修复结果')

    # 升级到专业版
    def UpdatePro(self, get):
        public.ExecShell("wget --no-check-certificate -O update.sh " + public.get_url() + "/install/update6.sh && bash update.sh")
        self.ReWeb(None)
        return True

    def get_upgrade_log(self,get):
        """
        @name 获取更新日志
        """
        logPath = '/tmp/upgrade_panel.log'
        if not os.path.exists(logPath):
            return public.returnMsg(True, '')

        logs = public.GetNumLines(logPath, 1000)
        try:
            # 适配旧版的日志
            return json.loads(logs)
        except:
            pass

        if logs.find('Success：面板更新成功') != -1:
            return {
                'status': True,
                'msg': "面板更新成功",
                'data': public.GetNumLines(logPath, 100)
            }

        return public.returnMsg(True, logs)

    @staticmethod
    def _has_py313() -> bool:
        import subprocess
        code = "import sys, urllib3, _sqlite3; print('%d.%d' % (sys.version_info.major, sys.version_info.minor))"
        now_env = os.path.join(public.get_panel_path(), "pyenv/bin/python3")
        pre_env = os.path.join(public.get_panel_path(), "pyenv313/bin/python3")
        for env in (now_env, pre_env):
            if not os.path.exists(env):
                continue
            try:
                ver = subprocess.check_output([env, "-c", code], text=True)
                if ver.strip() == "3.13":
                    return True
            except:
                pass
        return False

    def upgrade_env(self, get):
        """
        @name 升级环境
        """
        if self._has_py313():
            return json_response(status=True, msg='当前环境已升级为Python3.13')

        lockfile_path = os.path.join(public.get_panel_path(), ".upgrade_py313.lock")
        if os.path.exists(lockfile_path):
            return json_response(status=False, msg='当前环境正在升级中，请勿重复操作')
        else:
            log_path = os.path.join(public.get_panel_path(), "logs/upgrade_py313.log")
            if os.path.isfile(log_path):  # 删除之前的日志信息
                public.writeFile(log_path, "")

        sh = "cd {} \n nohup {} -u script/upgrade_py313.py prepare-env > /dev/null 2>&1 &".format(
            public.get_panel_path(), public.get_python_bin()
        )
        public.ExecShell(sh)
        return json_response(status=True, msg='环境升级任务已启动...')

    @staticmethod
    def upgrade_env_log(get):
        """
        @name 获取环境升级日志
        """

        lockfile_path = os.path.join(public.get_panel_path(), ".upgrade_py313.lock")
        env_update_running = os.path.exists(lockfile_path)

        log_path = os.path.join(public.get_panel_path(), "logs/upgrade_py313.log")
        if not os.path.exists(log_path):
            return json_response(status=True, msg="暂无日志信息", data={
                "env_update_running": env_update_running,
                "log": ""
            })

        logs = public.GetNumLines(log_path, 1000)
        msg = "获取成功"
        if not env_update_running:
            msg = "环境升级已结束"
        return json_response(status=True, msg=msg, data={
            "env_update_running": env_update_running,
            "log": logs
        })


    def _get_plugin_for_py313(self):
        config_file = os.path.join(public.get_panel_path(), "data/py313_plugins.json")
        m_time = 0
        if os.path.exists(config_file):
            m_time = os.path.getmtime(config_file)

        if m_time < time.time() - 3600:
            public.downloadFile('{}/install/update/py313_plugins.json'.format(public.get_url()), config_file)

        try:
            data = json.loads(public.readFile(config_file))
        except:
            data = []

        plugins = []
        plugin_path = os.path.join(public.get_panel_path(), "plugin")
        for i in data:
            if_file = os.path.join(plugin_path, i["name"], "info.json")
            if not os.path.exists(if_file):
                continue
            try:
                info = json.loads(public.readFile(if_file))
                lv = self._normalize_version(info.get("versions", "99.99"))
                nv = self._normalize_version(i.get("version", "0.0"))
                if lv < nv:
                    i["local_version"] = info["versions"]
                    plugins.append(i)
            except:
                continue
        plugins.sort(key=lambda x: x["level"])
        return  plugins
    
    def GetSystemdList(self,get=None):
        """
        @name 获取系统服务列表
        """
        try:
            result = public.ExecShell("systemctl list-units --type=service --all")[0].split("\n")
            return result
        except:
            return []

    def GetProcessStatus(self,sName):
        sys_server_list=["nginx","mysql","mysqld","php-fpm","mariadbd","mariadb"]
        if sName in sys_server_list:
            pids = []
            for proc in psutil.process_iter():
                if sName == 'mysql':
                    if proc.name() == 'mysqld' or proc.name() == 'mariadbd':
                        pids.append(proc.pid)
                else:
                    if proc.name() == sName:
                        pids.append(proc.pid)
            if len(pids) > 0:
                return True
            else:
                return False
        return False
