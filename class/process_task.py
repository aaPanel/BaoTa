#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------

#--------------------------------
# 进程监控模块
#--------------------------------
from psutil import cpu_count, pids, Process, cpu_times
from json import dumps
import os
import sys

os.chdir("/www/server/panel")
sys.path.insert(0, "class/")
import db
import time
import struct
import copy
import public
from cachelib import SimpleCache


class process_network_total:
    __pid_file = 'logs/process_network_total.pid'
    __inode_list = {}
    __net_process_list = {}
    __net_process_size = {}
    __last_stat = 0
    __last_write_time = 0
    __last_check_time = 0
    __tip_file = 'data/is_net_task.pl'
    __all_tip = 'data/control.conf'
    
    def install_pcap(self):
        '''
            @name 安装pcap模块依赖包
            @author hwliang
            @return void
        '''
        # 标记只安装一次
        tip_file= '{}/data/install_pcap.pl'.format(public.get_panel_path())
        if os.path.exists(tip_file): return

        if os.path.exists('/usr/bin/apt'):
            os.system("apt install libpcap-dev -y")
        elif os.path.exists('/usr/bin/dnf'):
            red_file = '/etc/redhat-release'
            if os.path.exists(red_file):
                f = open(red_file, 'r')
                red_body = f.read()
                f.close()
                if red_body.find('CentOS Linux release 8.') != -1:
                    rpm_file = '/root/libpcap-1.9.1.rpm'
                    down_url = "wget -O {} https://download.bt.cn/src/libpcap-devel-1.9.1-5.el8.x86_64.rpm --no-check-certificate -T 10".format(
                        rpm_file)
                    if os.path.exists(rpm_file):
                        os.system(down_url)
                        os.system("rpm -ivh {}".format(rpm_file))
                        if os.path.exists(rpm_file): os.remove(rpm_file)
                else:
                    os.system("dnf install libpcap-devel -y")
            else:
                os.system("dnf install libpcap-devel -y")
        elif os.path.exists('/usr/bin/yum'):
            os.system("yum install libpcap-devel -y")
        os.system("btpip install pypcap")
        # 写入标记文件
        public.writeFile(tip_file, 'True')

    def start(self):
        '''
            @name 启动进程网络监控
            @author hwliang<2021-09-13>
            @return void
        '''
        if not os.path.exists(self.__tip_file) or not os.path.exists(self.__all_tip):
            return
        try:
            import pcap
        except ImportError:
            try:
                self.install_pcap()
                import pcap
            except ImportError:
                print("pypcap module install failed.")
                return
        try:
            p = pcap.pcap()  # 监听所有网卡
            p.setfilter('tcp')  # 只监听TCP数据包
            for p_time, p_data in p:
                # 检查是否停止
                if p_time - self.__last_check_time > 10:
                    self.__last_check_time = p_time
                    if not os.path.exists(self.__tip_file) or not os.path.exists(self.__all_tip):
                        break

                # 处理数据包
                self.handle_packet(p_data)
        except:
            print(public.get_error_info())
            pass

    def handle_packet(self, pcap_data):
        '''
            @name 处理pcap数据包
            @author hwliang<2021-09-12>
            @param pcap_data<bytes> pcap数据包
            @return void
        '''
        # 获取IP协议头
        ip_header = pcap_data[14:34]
        # 解析src/dst地址
        src_ip = ip_header[12:16]
        dst_ip = ip_header[16:20]
        # 解析sport/dport端口
        src_port = pcap_data[34:36]
        dst_port = pcap_data[36:38]

        src = src_ip + b':' + src_port
        dst = dst_ip + b':' + dst_port
        # 计算数据包长度
        pack_size = len(pcap_data)
        # 统计进程流量
        self.total_net_process(dst, src, pack_size)

    def total_net_process(self, dst, src, pack_size):
        '''
            @name 统计进程流量
            @author hwliang<2021-09-13>
            @param dst<bytes> 目标地址
            @param src<bytes> 源地址
            @param pack_size<int> 数据包长度
            @return void
        '''
        self.get_tcp_stat()
        direction = None
        mtime = time.time()
        if dst in self.__net_process_list:
            pid = self.__net_process_list[dst]
            direction = 'down'
        elif src in self.__net_process_list:
            pid = self.__net_process_list[src]
            direction = 'up'
        else:
            if mtime - self.__last_stat > 3:
                self.__last_stat = mtime
                self.get_tcp_stat(True)
                if dst in self.__net_process_list:
                    pid = self.__net_process_list[dst]
                    direction = 'down'
                elif src in self.__net_process_list:
                    pid = self.__net_process_list[src]
                    direction = 'up'

        if not direction: return False
        if not pid: return False
        if not pid in self.__net_process_size:
            self.__net_process_size[pid] = {}
            self.__net_process_size[pid]['down'] = 0
            self.__net_process_size[pid]['up'] = 0
            self.__net_process_size[pid]['up_package'] = 0
            self.__net_process_size[pid]['down_package'] = 0

        self.__net_process_size[pid][direction] += pack_size
        self.__net_process_size[pid][direction + '_package'] += 1

        # 写入到文件
        if mtime - self.__last_write_time > 1:
            self.__last_write_time = mtime
            self.write_net_process()

    def write_net_process(self):
        '''
            @name 写入进程流量
            @author hwliang<2021-09-13>
            @return void
        '''
        w_file = '/dev/shm/bt_net_process'
        process_size = copy.deepcopy(self.__net_process_size)
        net_process = []
        for pid in process_size.keys():
            net_process.append(
                str(pid) + " " + str(process_size[pid]['down']) + " " +
                str(process_size[pid]['up']) + " " +
                str(process_size[pid]['down_package']) + " " +
                str(process_size[pid]['up_package']))

        f = open(w_file, 'w+', encoding='utf-8')
        f.write('\n'.join(net_process))
        f.close()

    def hex_to_ip(self, hex_ip):
        '''
            @name 将16进制的IP地址转换为字符串IP地址
            @author hwliang<2021-09-13>
            @param hex_ip<string> 16进制的IP地址:16进程端口
            @return tuple(ip<str>,port<int>) IP地址,端口
        '''
        hex_ip, hex_port = hex_ip.split(':')
        ip = '.'.join([
            str(int(hex_ip[i:i + 2], 16)) for i in range(0, len(hex_ip), 2)
        ][::-1])
        port = int(hex_port, 16)
        return ip, port

    def get_tcp_stat(self, force=False):
        '''
            @name 获取当前TCP连接状态表
            @author hwliang<2021-09-13>
            @param force<bool> 是否强制刷新
            @return dict
        '''
        if not force and self.__net_process_list:
            return self.__net_process_list
        self.__net_process_list = {}
        tcp_stat_file = '/proc/net/tcp'
        tcp_stat = open(tcp_stat_file, 'rb')
        tcp_stat_list = tcp_stat.read().decode('utf-8').split('\n')
        tcp_stat.close()
        tcp_stat_list = tcp_stat_list[1:]
        if force: self.get_process_inodes(force)
        for i in tcp_stat_list:
            tcp_tmp = i.split()
            if len(tcp_tmp) < 10: continue
            inode = tcp_tmp[9]
            if inode == '0': continue
            local_ip, local_port = self.hex_to_ip(tcp_tmp[1])
            if local_ip == '127.0.0.1': continue
            remote_ip, remote_port = self.hex_to_ip(tcp_tmp[2])
            if local_ip == remote_ip: continue
            if remote_ip == '0.0.0.0': continue

            pid = self.inode_to_pid(inode, force)
            if not pid: continue

            key = self.get_ip_pack(local_ip) + b':' + self.get_port_pack(
                local_port)
            self.__net_process_list[key] = pid
        return self.__net_process_list

    def get_port_pack(self, port):
        '''
            @name 将端口转换为字节流
            @author hwliang<2021-09-13>
            @param port<int> 端口
            @return bytes
        '''
        return struct.pack('H', int(port))[::-1]

    def get_ip_pack(self, ip):
        '''
            @name 将IP地址转换为字节流
            @author hwliang<2021-09-13>
            @param ip<str> IP地址
            @return bytes
        '''
        ip_arr = ip.split('.')
        ip_pack = b''
        for i in ip_arr:
            ip_pack += struct.pack('B', int(i))
        return ip_pack

    def inode_to_pid(self, inode, force=False):
        '''
            @name 将inode转换为进程ID
            @author hwliang<2021-09-13>
            @param inode<string> inode
            @param force<bool> 是否强制刷新
            @return int
        '''
        inode_list = self.get_process_inodes()
        if inode in inode_list:
            return inode_list[inode]
        return None

    def get_process_inodes(self, force=False):
        '''
            @name 获取进程inode列表
            @author hwliang<2021-09-13>
            @param force<bool> 是否强制刷新
            @return dict
        '''
        if not force and self.__inode_list: return self.__inode_list
        proc_path = '/proc'
        inode_list = {}
        for pid in os.listdir(proc_path):
            try:
                if not pid.isdigit(): continue
                inode_path = proc_path + '/' + pid + '/fd'
                for fd in os.listdir(inode_path):
                    try:
                        fd_file = inode_path + '/' + fd
                        fd_link = os.readlink(fd_file)
                        if fd_link.startswith('socket:['):
                            inode = fd_link[8:-1]
                            inode_list[inode] = pid
                    except:
                        continue
            except:
                continue
        self.__inode_list = inode_list
        return inode_list

    def get_process_name(self, pid):
        '''
            @name 获取进程名称
            @author hwliang<2021-09-13>
            @param pid<str> 进程ID
            @return str
        '''
        pid_path = '/proc/' + pid + '/comm'
        if not os.path.exists(pid_path): return ''
        pid_file = open(pid_path, 'rb')
        pid_name = pid_file.read().decode('utf-8').strip()
        pid_file.close()
        return pid_name

    def write_pid(self):
        '''
            @name 写入进程ID到PID文件
            @author hwliang<2021-09-13>
            @return void
        '''
        self_pid = os.getpid()
        pid_file = open(self.__pid_file, 'w')
        pid_file.write(str(self_pid))
        pid_file.close()

    def rm_pid_file(self):
        '''
            @name 删除进程pid文件
            @author hwliang<2021-09-13>
            @return void
        '''
        if os.path.exists(self.__pid_file):
            os.remove(self.__pid_file)


class process_task:
    __pids = []
    __last_times = {}
    __last_dates = {}
    __write_last = {}
    __write_dates = {}
    __read_last = {}
    __read_dates = {}
    __cpu_count = cpu_count()
    __cache = SimpleCache(5000)
    last_net_process = {}
    last_net_process_time = 0
    __process_net_list = {}
    __process_object = {}
    __insert_time = 0
    __last_cpu_time = 0
    old_key = 'old_cpu_times'
    new_key = 'new_cpu_times'
    new_info = {}
    old_info = {}

    def __init__(self):

        tip_file = '{}/data/process_index.pl'.format(public.get_panel_path())
        #hezhihong 修复process_top_list表不存在不自动创建问题 20230203
        if not public.M('sqlite_master').dbfile('system').where(
                'type=? AND name=?', ('table', 'process_top_list')).count():
            public.ExecShell('rm -f {}'.format(tip_file))
        if not os.path.isfile(tip_file):
            _sql = db.Sql().dbfile('system')
            csql = '''CREATE TABLE IF NOT EXISTS `process_top_list` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `cpu_top` REAL,
  `memory_top` REAL,
  `disk_top` REAL,
  `net_top` REAL,
  `all_top` REAL,
  `addtime` INTEGER
)'''
            _sql.execute(csql, ())
            # _sql.execute(
            #     'CREATE INDEX `addtime` ON `process_top_list` (`addtime`)', ())
            _sql.close()
            public.writeFile(tip_file, 'True')

    def get_pids(self):
        '''
            @name 获取pid列表
            @author hwliang<2021-09-04>
            @return None
        '''
        self.__pids = pids()

    def get_cpu_time(self):
        s = cpu_times()
        return s.user + s.system + s.nice + s.idle

    def get_cpu_percent(self, pid, cpu_time_total, s_cpu_times):
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

        cpu_percent = round(
            100.00 * float(cpu_time_total - old_time) /
            (s_cpu_times - self.__last_cpu_time), 2)
        self.__last_times[pid] = cpu_time_total
        self.__last_dates[pid] = stime
        if cpu_percent > 100: cpu_percent = 99
        if cpu_percent < 0: cpu_percent = 0
        return cpu_percent

    def get_io_write(self, pid, io_write):
        disk_io_write = 0
        stime = time.time()
        if pid in self.__write_last:
            old_write = self.__write_last[pid]
        else:
            self.__write_last[pid] = io_write
            self.__write_dates[pid] = stime
            return disk_io_write

        io_end = (io_write - old_write)
        if io_end > 0:
            disk_io_write = int(io_end / (stime - self.__write_dates[pid]))

        self.__write_last[pid] = io_write
        self.__write_dates[pid] = stime
        if disk_io_write < 0: disk_io_write = 0
        return disk_io_write

    def get_io_read(self, pid, io_read):
        disk_io_read = 0
        stime = time.time()
        if pid in self.__read_last:
            old_read = self.__read_last[pid]
        else:
            self.__read_last[pid] = io_read
            self.__read_dates[pid] = stime
            return disk_io_read

        io_end = (io_read - old_read)
        if io_end > 0:
            disk_io_read = int(io_end / (stime - self.__read_dates[pid]))

        self.__read_last[pid] = io_read
        self.__read_dates[pid] = stime
        if disk_io_read < 0: disk_io_read = 0
        return disk_io_read

    def read_file(self, filename):
        f = open(filename, 'rb')
        result = f.read()
        f.close()
        return result.decode().replace("\u0000", " ").strip()

    def get_process_net_list(self):
        w_file = '/dev/shm/bt_net_process'
        if not os.path.exists(w_file): return
        self.last_net_process = self.__cache.get('net_process')
        self.last_net_process_time = self.__cache.get('last_net_process')
        net_process_body = self.read_file(w_file)
        if not net_process_body: return
        net_process = net_process_body.split('\n')
        for np in net_process:
            if not np: continue
            tmp = {}
            np_list = np.split()
            if len(np_list) < 5: continue
            tmp['pid'] = int(np_list[0])
            tmp['down'] = int(np_list[1])
            tmp['up'] = int(np_list[2])
            tmp['down_package'] = int(np_list[3])
            tmp['up_package'] = int(np_list[4])
            self.__process_net_list[str(tmp['pid'])] = tmp
        self.__cache.set('net_process', self.__process_net_list, 600)
        self.__cache.set('last_net_process', time.time(), 600)

    def get_process_network(self, pid):
        '''
            @name 获取进程网络流量
            @author hwliang<2021-09-13>
            @param pid<int> 进程ID
            @return tuple
        '''

        if not self.__process_net_list:
            self.get_process_net_list()
        if not self.last_net_process_time:
            return 0, 0, 0, 0
        if not pid in self.__process_net_list.keys():
            return 0, 0, 0, 0

        if not pid in self.last_net_process:
            return self.__process_net_list[pid]['up'], self.__process_net_list[
                pid]['up_package'], self.__process_net_list[pid][
                    'down'], self.__process_net_list[pid]['down_package']

        up = int((self.__process_net_list[pid]['up'] -
                  self.last_net_process[pid]['up']) /
                 (time.time() - self.last_net_process_time))
        down = int((self.__process_net_list[pid]['down'] -
                    self.last_net_process[pid]['down']) /
                   (time.time() - self.last_net_process_time))
        up_package = int((self.__process_net_list[pid]['up_package'] -
                          self.last_net_process[pid]['up_package']) /
                         (time.time() - self.last_net_process_time))
        down_package = int((self.__process_net_list[pid]['down_package'] -
                            self.last_net_process[pid]['down_package']) /
                           (time.time() - self.last_net_process_time))
        if up < 0: up = 0
        if down < 0: down = 0
        if up_package < 0: up_package = 0
        if down_package < 0: down_package = 0
        return up, up_package, down, down_package

    def get_process_username(self, pid):
        '''
            @name 获取进程用户名
            @param pid 进程id
            @return 用户名
        '''
        try:
            import pwd
            return pwd.getpwuid(os.stat('/proc/' + str(pid)).st_uid).pw_name
        except:
            return 'root'

    def get_monitor_list(self, stime=None):
        '''
            @name 获取监控列表
            @author hwliang<2021-09-04>
            @return list
        '''
        self.get_pids()
        process_info_list = []
        total_cpu_precent = 0.0
        my_pid = os.getpid()
        if type(self.new_info) != dict: self.new_info = {}
        all_cpu_time = self.get_cpu_time()
        self.new_info['time'] = time.time()

        for pid in self.__pids:
            try:
                # if pid < 100: continue
                if pid == my_pid: continue
                if not pid in self.__process_object.keys():
                    self.__process_object[pid] = Process(pid)
                try:
                    if self.__process_object[pid].status() == 'terminated':
                        self.__process_object[pid] = Process(pid).create_time
                except:
                    self.__process_object[pid] = Process(pid)
                p = self.__process_object[pid]

                process_info = {}
                process_info['cpu_percent'] = self.get_cpu_percent(
                    str(pid), sum(p.cpu_times()), all_cpu_time
                )  #self.get_cpu_percent(pid,int(sum(p.cpu_times())),self.new_info['cpu_time'])         # CPU使用率
                total_cpu_precent += process_info['cpu_percent']
                process_info['memory'] = p.memory_info().rss  # 内存占用
                if not process_info['memory']: continue

                io_counters = p.io_counters()
                process_info['disk_read'] = self.get_io_read(
                    pid, io_counters.read_bytes)  # 读取磁盘字节数
                process_info['disk_write'] = self.get_io_write(
                    pid, io_counters.write_bytes)  # 写入磁盘字节数
                process_info['disk_total'] = process_info[
                    'disk_read'] + process_info['disk_write']  # 磁盘总读写

                process_info['up'], process_info['up_package'], process_info[
                    'down'], process_info[
                        'down_package'] = self.get_process_network(str(pid))

                process_info['net_total'] = process_info['up'] + process_info[
                    'down']  # 网络总流量
                process_info['package_total'] = process_info[
                    'up_package'] + process_info['down_package']  # 网络总包数

                if not process_info['cpu_percent'] and not process_info[
                        'disk_total'] and not process_info['net_total']:
                    continue
                process_proc_comm = '/proc/{}/comm'.format(pid)
                process_proc_cmdline = '/proc/{}/cmdline'.format(pid)
                process_info['pid'] = pid
                process_info['name'] = self.read_file(process_proc_comm)
                process_info['cmdline'] = self.read_file(
                    process_proc_cmdline)  # 启动命令
                process_info['create_time'] = int(p.create_time())  # 创建时间
                process_info['connect_count'] = len(p.connections())  # 连接数
                process_info['username'] = self.get_process_username(
                    pid)  # 进程用户名
                process_info_list.append(process_info)
            except:
                continue

        self.__last_cpu_time = all_cpu_time
        self.__process_net_list.clear()
        self.insert_db(process_info_list, stime)
        # import public
        # for pp in sorted(process_info_list,key=lambda x:x['cpu_percent'],reverse=True):
        if total_cpu_precent > 100: total_cpu_precent = 100
        return total_cpu_precent

    def get_expire_time(self):
        '''
            @name 获取过期时间
            @return int
        '''
        filename = 'data/control.conf'
        _day = 30
        if os.path.exists(filename):
            try:
                conf = self.read_file(filename)
                if conf: _day = int(conf)
            except:
                pass
        return time.time() - _day * 86400

    def insert_db(self, process_info_list, _time):
        '''
            @name 插入数据库
            @param process_info_list list
            @return bool
        '''
        if not process_info_list: return
        all_top, cpu_top, disk_top, net_top, memory_top = self.get_top_list(
            process_info_list)

        with db.Sql().dbfile('system') as _sql:
            if not _time:
                _time = int(time.time())
            _sql.table('process_top_list').insert({
                'all_top':
                dumps(all_top),
                'cpu_top':
                dumps(cpu_top),
                'disk_top':
                dumps(disk_top),
                'net_top':
                dumps(net_top),
                'memory_top':
                dumps(memory_top),
                'addtime':
                _time
            })

            # 删除过期数据
            if not self.__insert_time: self.__insert_time = _time
            if _time - self.__insert_time > 3600:
                self.__insert_time = _time
                _sql.table('process_top_list').where('addtime<?', self.get_expire_time()).delete()
                
                # 释放一次磁盘空间
                system_vacuum_file = "{}/data/system_vacuum.pl".format(public.get_panel_path())
                do_vacuum = False
                if not os.path.exists(system_vacuum_file):
                    public.writeFile(system_vacuum_file, str(int(time.time())))
                    do_vacuum = True
                elif os.path.getmtime(system_vacuum_file) < time.time() - 86400 * 7:
                    public.writeFile(system_vacuum_file, str(int(time.time())))
                    do_vacuum = True
                if do_vacuum:
                    _sql.execute('VACUUM', ())

            _sql.close()

    def get_top_list(sekf, process_info_list):
        '''
            @name 排序
            @param process_info_list list
            @return list
        '''
        process_info_list = sorted(
            process_info_list,
            key=lambda x:
            [x['cpu_percent'], x['disk_total'], x['net_total'], x['memory']],
            reverse=True)
        top_num = 5
        all_top = []
        for p in process_info_list[:top_num]:
            _line = [
                p['cpu_percent'], p['disk_read'], p['disk_write'], p['memory'],
                p['up'], p['down'], p['pid'],
                public.xssencode2(p['name']),
                public.xssencode2(p['cmdline']),
                public.xssencode2(p['username']), p['create_time']
            ]
            all_top.append(_line)

        process_info_list = sorted(process_info_list,
                                   key=lambda x: x['cpu_percent'],
                                   reverse=True)
        cpu_top = []
        for p in process_info_list[:top_num]:
            if not p['cpu_percent']: continue
            _line = [
                p['cpu_percent'], p['pid'],
                public.xssencode2(p['name']),
                public.xssencode2(p['cmdline']),
                public.xssencode2(p['username']), p['create_time']
            ]
            cpu_top.append(_line)

        process_info_list = sorted(process_info_list,
                                   key=lambda x: x['disk_total'],
                                   reverse=True)
        disk_top = []
        for p in process_info_list[:top_num]:
            if not p['disk_total']: continue
            _line = [
                p['disk_total'], p['disk_read'], p['disk_write'], p['pid'],
                public.xssencode2(p['name']),
                public.xssencode2(p['cmdline']),
                public.xssencode2(p['username']), p['create_time']
            ]
            disk_top.append(_line)

        process_info_list = sorted(process_info_list,
                                   key=lambda x: x['net_total'],
                                   reverse=True)
        net_top = []
        for p in process_info_list[:top_num]:
            if not p['net_total']: continue
            _line = [
                p['net_total'], p['up'], p['down'], p['connect_count'],
                p['package_total'], p['pid'],
                public.xssencode2(p['name']),
                public.xssencode2(p['cmdline']),
                public.xssencode2(p['username']), p['create_time']
            ]
            net_top.append(_line)

        process_info_list = sorted(process_info_list,
                                   key=lambda x: x['memory'],
                                   reverse=True)
        memory_top = []
        for p in process_info_list[:top_num]:
            if not p['memory']: continue
            _line = [
                p['memory'], p['pid'],
                public.xssencode2(p['name']),
                public.xssencode2(p['cmdline']),
                public.xssencode2(p['username']), p['create_time']
            ]
            memory_top.append(_line)

        return all_top, cpu_top, disk_top, net_top, memory_top


if __name__ == '__main__':
    # net = process_network_total()
    # net.start()
    # threading.Thread(target = net.start,args=()).start()

    p = process_task()
    while True:
        p.get_monitor_list()
        time.sleep(1)
        print("-" * 50)
