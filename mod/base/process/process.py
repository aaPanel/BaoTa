# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: sww <sww@bt.cn>
# -------------------------------------------------------------------
import json
import os
# ------------------------------
# 进程模型
# ------------------------------
import sys
import time
import traceback

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

os.chdir("/www/server/panel")
import public
import psutil
from typing import Any

try:
    from BTPanel import cache
except:
    import cachelib

    cache = cachelib.SimpleCache()


class RealProcess:
    process_path = '/proc'
    ps = json.loads(public.readFile('/www/server/panel/mod/base/process/process_ps.json'))
    __isUfw = False
    __isFirewalld = False
    old_info = {}
    new_info = {}
    old_path = '/tmp/bt_task_old1.json'
    __cpu_time = None
    __process_net_list = {}
    last_net_process = None
    last_net_process_time = 0
    old_net_path = '/tmp/bt_network_old1.json'
    old_net_info = {}
    new_net_info = {}

    def __init__(self):
        if os.path.exists('/usr/sbin/firewalld'): self.__isFirewalld = True
        if os.path.exists('/usr/sbin/ufw'): self.__isUfw = True

    def object_to_dict(self, obj):
        result = {}
        for name in dir(obj):
            value = getattr(obj, name)
            if not name.startswith('__') and not callable(value) and not name.startswith('_'): result[name] = value
        return result

    def get_computers_use(self):
        result = {}
        cpu_usage = psutil.cpu_percent(interval=1, percpu=True)
        result['cpu'] = round(sum(cpu_usage) / len(cpu_usage), 2)
        memory = psutil.virtual_memory()
        print(memory.total)
        result['memory_usage'] = memory.percent
        disk = psutil.disk_usage('/')
        result['disk_usage'] = round(((disk.used / disk.total) * 100), 0)
        network_io = psutil.net_io_counters()
        result['network_io_bytes_sent'] = network_io.bytes_sent
        result['network_io_bytes_recv'] = network_io.bytes_recv

        return result

    # ------------------------------ 获取进程列表 start ------------------------------
    def get_process_list(self):
        """
        获取进程列表
        :return:
        """
        try:
            process_list = []
            if type(self.new_info) != dict: self.new_info = {}
            self.new_info['cpu_time'] = self.get_cpu_time()
            self.new_info['time'] = time.time()
            self.get_process_net_list()
            for proc in psutil.process_iter(
                    ['pid', 'ppid', 'name', 'username', 'create_time', 'memory_info', 'io_counters', 'num_threads', 'create_time', 'connections', 'open_files', 'status', 'cmdline']):
                try:
                    proc_info = proc.as_dict(
                        attrs=['pid', 'ppid', 'name', 'username', 'create_time', 'memory_info', 'io_counters', 'num_threads', 'create_time', 'connections', 'open_files', 'status',
                               'cmdline'])
                    p_cpus = proc.cpu_times()
                    process_list.append({
                        'pid': proc_info['pid'],
                        'ppid': proc_info['ppid'],
                        'name': proc_info['name'],
                        'username': proc_info['username'],
                        'cpu_percent': self.get_cpu_percent(str(proc_info['pid']), p_cpus, self.new_info['cpu_time']),
                        'running_time': time.time() - proc_info['create_time'],
                        'memory_info': proc_info['memory_info'],
                        'io_info': proc_info['io_counters'],
                        'num_threads': proc_info['num_threads'],
                        'create_time': proc_info['create_time'],
                        'connections_info': proc_info['connections'],
                        'open_files': proc_info['open_files'],
                        'ps': self.get_process_ps(proc.name())['data'],
                        'status': proc_info['status'],
                        'cmdline': proc_info['cmdline'],
                        'net_info': self.get_process_network(proc_info['pid'])
                    })
                    cache.set(self.old_path, self.new_info, 600)
                except:
                    pass
            return public.returnResult(code=1, msg='success', status=True, data=process_list)
        except Exception as e:
            return public.returnResult(code=0, msg='获取进程列表失败' + str(e), status=False)

    # ------------------------------ 获取进程列表 end ------------------------------

    # ------------------------------ 获取进程信息 start ------------------------------

    @staticmethod
    def _format_connections(connects):
        result = []
        for i in connects:
            r_addr = i.raddr
            if not i.raddr:
                r_addr = ('', 0)
            l_addr = i.laddr
            if not i.laddr:
                l_addr = ('', 0)
            result.append({
                "fd": i.fd,
                "family": i.family,
                "local_addr": l_addr[0],
                "local_port": l_addr[1],
                "client_addr": r_addr[0],
                "client_rport": r_addr[1],
                "status": i.status
            })
        return result

    @staticmethod
    def get_connects(pid: str):
        '''
            @name 获取进程连接信息
            @author hwliang<2021-08-09>
            @param pid<int>
            @return dict
        '''
        connects = 0
        try:
            if pid == 1:
                return connects
            tp = '/proc/' + str(pid) + '/fd/'
            if not os.path.exists(tp):
                return connects
            for d in os.listdir(tp):
                f_name = tp + d
                if os.path.islink(f_name):
                    l = os.readlink(f_name)
                    if l.find('socket:') != -1:
                        connects += 1
        except:
            pass
        return connects

    def get_process_info_by_pid(self, pid: int) -> dict:
        """
        获取进程信息
        :param pid:
        :return:
        """
        try:
            status_ps = {'sleeping': '睡眠', 'running': '活动'}
            process = psutil.Process(int(pid))
            if type(self.new_info) != dict: self.new_info = {}
            self.new_info['cpu_time'] = self.get_cpu_time()
            self.new_info['time'] = time.time()
            self.get_process_net_list()
            p_cpus = process.cpu_times()
            # 获取连接信息
            connections = process.connections()
            p_mem = process.memory_full_info()
            io_info = process.io_counters()
            info = {
                'pid': process.pid,
                'ppid': process.ppid(),
                'name': process.name(),
                'threads': process.num_threads(),
                'user': process.username(),
                'username': process.username(),
                'cpu_percent': self.get_cpu_percent(process.pid, p_cpus, self.new_info['cpu_time']),
                'memory_info': self.object_to_dict(p_mem),
                'memory_used': p_mem.uss,
                'io_info': self.object_to_dict(io_info),
                "io_write_bytes": io_info.write_bytes,
                "io_read_bytes": io_info.read_bytes,
                'connections': self._format_connections(connections),
                "connects": self.get_connects(str(process.pid)),
                'status': status_ps[process.status()] if process.status() in status_ps else process.status(),
                'create_time': process.create_time(),
                'running_time': process.cpu_times().user + process.cpu_times().system,
                'cmdline': process.cmdline(),
                'open_files': [self.object_to_dict(i) for i in process.open_files()],
                'ps': self.get_process_ps(process.name())['data'],
                'net_info': self.get_process_network(process.pid),
                "exe": ' '.join(process.cmdline()),
            }
            cache.set(self.old_path, self.new_info, 600)
            return public.returnResult(code=1, msg='success', status=True, data=info)
        except Exception as e:
            return public.returnResult(code=0, msg='获取进程信息失败' + str(e), status=False)

    # 通过name获取进程信息
    def get_process_info_by_name(self, name: str) -> dict:
        """
        通过name获取进程信息
        :param name:
        :return:
        """
        try:
            pids = [i.pid for i in psutil.process_iter(['pid', 'name', 'cmdline']) if i.name() == name]
            infos = []
            for pid in pids:
                try:
                    info = self.get_process_info_by_pid(pid)
                    if info['status']:
                        infos.append(info['data'])
                except:
                    pass
            return public.returnResult(code=1, msg='success', status=True, data=infos)
        except Exception as e:
            return public.returnResult(code=0, msg='获取进程信息失败' + str(e), status=False)

    # 通过启动命令获取进程信息
    def get_process_info_by_exec(self, cli: str) -> dict:
        """
        通过启动命令获取进程信息
        :param cli:启动命令
        :return:
        """

        try:
            pids = [i.pid for i in psutil.process_iter(['pid', 'cmdline']) if cli in ' '.join(i.cmdline())]
            infos = []
            for pid in pids:
                try:
                    info = self.get_process_info_by_pid(pid)
                    if info['status']:
                        infos.append(info['data'])
                except:
                    pass
            return public.returnResult(code=1, msg='success', status=True, data=infos)
        except Exception as e:
            return public.returnResult(code=0, msg='获取进程信息失败' + str(e), status=False)

    def get_process_info_by_port(self, port: int) -> dict:
        """
        通过端口获取进程信息
        :param port:
        :return:
        """
        try:
            infos = []
            for i in psutil.process_iter(['pid', 'connections']):
                for conn in i.connections():
                    try:
                        if conn.laddr.port == int(port):
                            info = self.get_process_info_by_pid(i.pid)
                            if info['status']:
                                infos.append(info['data'])
                    except:
                        pass
            return public.returnResult(code=1, msg='success', status=True, data=infos)
        except Exception as e:
            return public.returnResult(code=0, msg='获取进程信息失败' + str(e), status=False)

    def get_process_info_by_ip(self, ip: str) -> dict:
        """
        通过远程ip获取进程信息
        :param ip:
        :return:
        """
        infos = []
        try:
            for i in psutil.process_iter(['pid', 'connections']):
                for conn in i.connections():
                    try:
                        if conn.raddr:
                            if conn.raddr.ip == ip:
                                info = self.get_process_info_by_pid(i.pid)['data']
                                if info:
                                    infos.append(info)
                    except:
                        pass
            return public.returnResult(code=1, msg='success', status=True, data=infos)
        except:
            return public.returnResult(code=0, msg='获取进程信息失败', status=False, data=infos)

    def get_process_info_by_openfile(self, file_path: str) -> dict:
        """
        通过打开文件获取进程信息
        :param file_path:
        :return:
        """
        infos = []
        try:
            for i in psutil.process_iter(['pid', 'open_files']):
                try:
                    for file in i.open_files():
                        if file.path == file_path:
                            info = self.get_process_info_by_pid(i.pid)['data']
                            if info:
                                infos.append(info)
                except:
                    pass
            return public.returnResult(code=1, msg='success', status=True, data=infos)
        except:
            return public.returnResult(code=0, msg='获取进程信息失败', status=False, data=infos)

    # ------------------------------ 获取进程信息 end ------------------------------

    # ------------------------------ 获取进程ps start ------------------------------

    def get_process_ps(self, name: str) -> dict:
        """
        获取进程ps
        :param name:
        :return:
        """

        return public.returnResult(code=1, msg='success', status=True, data=self.ps.get(name, '未知进程'))

    # ------------------------------ 获取进程ps end ------------------------------

    # ------------------------------ 获取进程树 start ------------------------------

    def get_process_tree(self, pid: int) -> dict:
        """
        获取进程树
        :param pid:
        :return:
        """
        try:
            pid = int(pid)
            process = psutil.Process(pid)
            process_tree = process.children(recursive=True)
            infos = []
            info = self.get_process_info_by_pid(pid)
            if info['status']:
                infos.append(info['data'])

            for prc in process_tree:
                info = self.get_process_info_by_pid(prc.pid)
                if info['status']:
                    infos.append(info['data'])
            return public.returnResult(code=1, msg='success', status=True, data=infos)
        except Exception as e:
            return public.returnResult(code=0, msg='获取进程树失败' + str(e), status=False)

    # ------------------------------ 获取进程树 end ------------------------------

    # ------------------------------ 结束进程 start ------------------------------
    # 结束进程pid
    def kill_pid(self, pid: int) -> dict:
        """
        通过关闭进程
        :param pid:
        :return:
        """
        try:
            os.kill(pid, 9)
            return public.returnResult(code=1, msg='success', status=True, data='')
        except Exception as e:
            public.ExecShell('kill -9 ' + str(pid))
            return public.returnResult(code=1, msg='结束进程失败' + str(e), status=True)

    # 结束进程名
    def kill_name(self, name: str) -> dict:
        """
        通过name关闭进程
        :param name:
        :return:
        """
        try:
            os.system('killall ' + name)
            return public.returnResult(code=1, msg='success', status=True, data='')
        except Exception as e:
            return public.returnResult(code=0, msg='结束进程失败' + str(e), status=False)

    # 结束进程树
    def kill_tree(self, pid: int) -> dict:
        """
        通过关闭进程树
        :param pid:
        :return:
        """
        try:
            p = psutil.Process(pid)
            p.kill()
            for i in p.children(recursive=True):
                i.kill()
            return public.returnResult(code=1, msg='success', status=True, data='')
        except Exception as e:
            public.ExecShell('kill -9 ' + str(pid))
            return public.returnResult(code=1, msg='success', status=True)

    # 结束所有进程  pid,进程名，进程树
    def kill_proc_all(self, pid: int) -> dict:
        """
        结束所有进程
        :return:
        """
        try:
            proc = psutil.Process(pid)
            name = proc.name()
            self.kill_pid(pid)
            self.kill_name(name)
            self.kill_tree(pid)
            return public.returnResult(code=1, msg='success', status=True, data='')
        except Exception as e:
            return public.returnResult(code=0, msg='结束进程失败' + str(e), status=False)

    def kill_port(self, port: str) -> dict:
        """
        结束端口进程
        :param port:
        :return:
        """
        for process in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                for conn in process.connections():
                    if conn.laddr.port == int(port):
                        self.kill_pid(process.pid)
            except:
                pass
        return public.returnResult(code=1, msg='success', status=True, data='')

    # ------------------------------ 结束进程 end ------------------------------

    # ------------------------------ 拉黑ip start ------------------------------
    def add_black_ip(self, ips: list, ) -> dict:
        """
        拉黑ip
        :param ip:
        :return:
        """
        try:
            if not public.get_firewall_status() == 1: return public.returnMsg(False, '当前系统防火墙未开启')
            if [ip for ip in ips if ip in ['0.0.0.0', '127.0.0.0', "::1"]]: return {'status': False, 'msg': '禁止拉黑本机ip', 'data': ''}
            for ip in ips:
                if not public.check_ip(ip): continue
                if public.M('firewall_ip').where("port=?", (ip,)).count() > 0: continue
                if self.__isUfw:
                    if public.is_ipv6(ip):
                        public.ExecShell('ufw deny from ' + ip + ' to any')
                    else:
                        public.ExecShell('ufw insert 1 deny from ' + ip + ' to any')
                else:
                    if self.__isFirewalld:
                        if public.is_ipv6(ip):
                            public.ExecShell('firewall-cmd --permanent --add-rich-rule=\'rule family=ipv6 source address="' + ip + '" drop\'')
                        else:
                            public.ExecShell('firewall-cmd --permanent --add-rich-rule=\'rule family=ipv4 source address="' + ip + '" drop\'')
                    else:
                        if public.is_ipv6(ip): return public.returnMsg(False, 'FIREWALL_IP_FORMAT')
                        public.ExecShell('iptables -I INPUT -s ' + ip + ' -j DROP')
                addtime = time.strftime('%Y-%m-%d %X', time.localtime())
                public.M('firewall_ip').add('address,addtime,types', (ip, addtime, 'drop'))
            self.firewall_reload()
            return public.returnResult(code=1, msg='success', status=True, data='')
        except Exception as e:
            return public.returnResult(code=0, msg='拉黑失败' + str(e), status=False)

    # ------------------------------ 拉黑ip end ------------------------------

    # ------------------------------ 取消拉黑ip start ------------------------------
    # 删除IP屏蔽
    def del_black_ip(self, ips: list) -> dict:
        try:
            if not public.get_firewall_status() == 1: return public.returnMsg(False, '当前系统防火墙未开启')
            for ip in ips:
                if not public.check_ip(ip): continue
                if self.__isUfw:
                    public.ExecShell('ufw delete deny from ' + ip + ' to any')
                else:
                    if self.__isFirewalld:
                        if public.is_ipv6(ip):
                            public.ExecShell('firewall-cmd --permanent --remove-rich-rule=\'rule family=ipv6 source address="' + ip + '" drop\'')
                        else:
                            public.ExecShell('firewall-cmd --permanent --remove-rich-rule=\'rule family=ipv4 source address="' + ip + '" drop\'')
                    else:
                        public.ExecShell('iptables -D INPUT -s ' + ip + ' -j DROP')

                public.WriteLog("TYPE_FIREWALL", 'FIREWALL_ACCEPT_IP', (ip,))
                public.M('firewall_ip').where("address=?", (ip,)).delete()

            self.firewall_reload()
            return public.returnResult(code=1, msg='success', status=True)
        except Exception as e:
            return public.returnResult(code=0, msg='删除失败' + str(e), status=False)

    # 重载防火墙配置
    def firewall_reload(self):
        try:
            if self.__isUfw:
                public.ExecShell('/usr/sbin/ufw reload &')
                return public.returnResult(code=1, msg='success', status=True)
            if self.__isFirewalld:
                public.ExecShell('firewall-cmd --reload &')
            else:
                public.ExecShell('/etc/init.d/iptables save &')
                public.ExecShell('/etc/init.d/iptables restart &')
            return public.returnResult(code=1, msg='success', status=True)
        except:
            return public.returnResult(code=0, msg='重载防火墙失败', status=False)

    # ------------------------------ 取消拉黑ip end ------------------------------

    # ------------------------------ 获取进程cpu start ------------------------------

    # 获取cpu使用率
    def get_cpu_percent(self, pid, cpu_times, cpu_time):
        self.get_old()
        percent = 0.00
        process_cpu_time = self.get_process_cpu_time(cpu_times)
        if not self.old_info: self.old_info = {}
        if not pid in self.old_info:
            self.new_info[pid] = {}
            self.new_info[pid]['cpu_time'] = process_cpu_time
            return percent
        try:
            percent = round(
                100.00 * (process_cpu_time - self.old_info[pid]['cpu_time']) / (cpu_time - self.old_info['cpu_time']), 2)
        except:
            return 0
        self.new_info[pid] = {}
        self.new_info[pid]['cpu_time'] = process_cpu_time
        if percent > 0: return percent
        return 0.00

    def get_process_cpu_time(self, cpu_times):
        cpu_time = 0.00
        for s in cpu_times: cpu_time += s
        return cpu_time

    def get_old(self):
        if self.old_info: return True
        data = cache.get(self.old_path)
        if not data: return False
        self.old_info = data
        del (data)
        return True

    def get_cpu_time(self):
        if self.__cpu_time: return self.__cpu_time
        self.__cpu_time = 0.00
        s = psutil.cpu_times()
        self.__cpu_time = s.user + s.system + s.nice + s.idle
        return self.__cpu_time

    # ------------------------------ 获取进程cpu end ------------------------------

    # ------------------------------ 获取进程net start ------------------------------

    def get_process_network(self, pid):
        '''
            @name 获取进程网络流量
            @author hwliang<2021-09-13>
            @param pid<int> 进程ID
            @return tuple
        '''
        if not self.__process_net_list:
            self.get_process_net_list()
        if not self.last_net_process_time: return 0, 0, 0, 0
        if not pid in self.__process_net_list: return 0, 0, 0, 0

        if not pid in self.last_net_process:
            return self.__process_net_list[pid]['up'], self.__process_net_list[pid]['up_package'], \
                self.__process_net_list[pid]['down'], self.__process_net_list[pid]['down_package']

        up = int((self.__process_net_list[pid]['up'] - self.last_net_process[pid]['up']) / (
                time.time() - self.last_net_process_time))
        down = int((self.__process_net_list[pid]['down'] - self.last_net_process[pid]['down']) / (
                time.time() - self.last_net_process_time))
        up_package = int((self.__process_net_list[pid]['up_package'] - self.last_net_process[pid]['up_package']) / (
                time.time() - self.last_net_process_time))
        down_package = int(
            (self.__process_net_list[pid]['down_package'] - self.last_net_process[pid]['down_package']) / (
                    time.time() - self.last_net_process_time))
        return up, up_package, down, down_package

    def get_process_net_list(self):
        w_file = '/dev/shm/bt_net_process'
        if not os.path.exists(w_file): return
        self.last_net_process = cache.get('net_process')
        self.last_net_process_time = cache.get('last_net_process')
        net_process_body = public.readFile(w_file)
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
            self.__process_net_list[tmp['pid']] = tmp
        cache.set('net_process', self.__process_net_list, 600)
        cache.set('last_net_process', time.time(), 600)

    def get_network(self):
        try:
            self.get_net_old()
            networkIo = psutil.net_io_counters()[:4]
            self.new_net_info['upTotal'] = networkIo[0]
            self.new_net_info['downTotal'] = networkIo[1]
            self.new_net_info['upPackets'] = networkIo[2]
            self.new_net_info['downPackets'] = networkIo[3]
            self.new_net_info['time'] = time.time()

            if not self.old_net_info: self.old_net_info = {}
            if not 'upTotal' in self.old_net_info:
                time.sleep(0.1)
                networkIo = psutil.net_io_counters()[:4]
                self.old_net_info['upTotal'] = networkIo[0]
                self.old_net_info['downTotal'] = networkIo[1]
                self.old_net_info['upPackets'] = networkIo[2]
                self.old_net_info['downPackets'] = networkIo[3]
                self.old_net_info['time'] = time.time()

            s = self.new_net_info['time'] - self.old_net_info['time']
            networkInfo = {}
            networkInfo['upTotal'] = networkIo[0]
            networkInfo['downTotal'] = networkIo[1]
            networkInfo['up'] = round((float(networkIo[0]) - self.old_net_info['upTotal']) / s, 2)
            networkInfo['down'] = round((float(networkIo[1]) - self.old_net_info['downTotal']) / s, 2)
            networkInfo['downPackets'] = networkIo[3]
            networkInfo['upPackets'] = networkIo[2]
            networkInfo['downPackets_s'] = int((networkIo[3] - self.old_net_info['downPackets']) / s)
            networkInfo['upPackets_s'] = int((networkIo[2] - self.old_net_info['upPackets']) / s)
            cache.set(self.old_net_path, self.new_net_info, 600)
            return networkInfo
        except:
            return None

    def get_net_old(self):
        if self.old_net_info: return True
        data = cache.get(self.old_net_path)
        if not data: return False
        if not data: return False
        self.old_net_info = data
        del (data)
        return True

    # ------------------------------ 获取进程net end ------------------------------

    # ------------------------------ 获取启动项列表 start ------------------------------
    def get_run_list(self, search: str = ''):
        runFile = ['/etc/rc.local', '/etc/profile', '/etc/inittab', '/etc/rc.sysinit']
        runList = []
        for rfile in runFile:
            if not os.path.exists(rfile): continue
            bodyR = self.clear_comments(public.readFile(rfile))
            if not bodyR: continue
            stat = os.stat(rfile)
            accept = str(oct(stat.st_mode)[-3:])
            if accept == '644': continue
            tmp = {}
            tmp['name'] = rfile
            tmp['srcfile'] = rfile
            tmp['size'] = os.path.getsize(rfile)
            tmp['access'] = accept
            tmp['ps'] = self.get_run_ps(rfile)
            runList.append(tmp)
        runlevel = self.get_my_runlevel()
        runPath = ['/etc/init.d', '/etc/rc' + runlevel + '.d']
        tmpAll = []
        islevel = False
        for rpath in runPath:
            if not os.path.exists(rpath): continue
            if runPath[1] == rpath: islevel = True
            for f in os.listdir(rpath):
                if f[:1] != 'S': continue
                filename = rpath + '/' + f
                if not os.path.exists(filename): continue
                if os.path.isdir(filename): continue
                if os.path.islink(filename):
                    flink = os.readlink(filename).replace('../', '/etc/')
                    if not os.path.exists(flink): continue
                    filename = flink
                tmp = {}
                tmp['name'] = f
                if islevel: tmp['name'] = f[3:]
                if tmp['name'] in tmpAll: continue
                stat = os.stat(filename)
                accept = str(oct(stat.st_mode)[-3:])
                if accept == '644': continue
                tmp['srcfile'] = filename
                tmp['access'] = accept
                tmp['size'] = os.path.getsize(filename)
                tmp['ps'] = self.get_run_ps(tmp['name'])
                runList.append(tmp)
                tmpAll.append(tmp['name'])
        data = {}
        data['run_list'] = runList
        data['run_level'] = runlevel
        if search:
            data['run_list'] = self.search_run(data['run_list'], search)
        return public.returnResult(code=1, msg='success', status=True, data=data)

    # 启动项查询
    def search_run(self, data, search):
        try:
            ldata = []
            for i in data:
                if search in i['name'] or search in i['srcfile'] or search in i['ps']:
                    ldata.append(i)
            return ldata
        except:
            return data

    # 清除注释
    def clear_comments(self, body):
        bodyTmp = body.split("\n")
        bodyR = ""
        for tmp in bodyTmp:
            if tmp.startswith('#'): continue
            if tmp.strip() == '': continue
            bodyR += tmp
        return bodyR

    # 服务注释
    def get_run_ps(self, name):
        runPs = {'netconsole': '网络控制台日志', 'network': '网络服务', 'jexec': 'JAVA', 'tomcat8': 'Apache Tomcat',
                 'tomcat7': 'Apache Tomcat', 'mariadb': 'Mariadb',
                 'tomcat9': 'Apache Tomcat', 'tomcat': 'Apache Tomcat', 'memcached': 'Memcached缓存器',
                 'php-fpm-53': 'PHP-5.3', 'php-fpm-52': 'PHP-5.2',
                 'php-fpm-54': 'PHP-5.4', 'php-fpm-55': 'PHP-5.5', 'php-fpm-56': 'PHP-5.6', 'php-fpm-70': 'PHP-7.0',
                 'php-fpm-71': 'PHP-7.1',
                 'php-fpm-72': 'PHP-7.2', 'rsync_inotify': 'rsync实时同步', 'pure-ftpd': 'FTP服务',
                 'mongodb': 'MongoDB', 'nginx': 'Web服务器(Nginx)',
                 'httpd': 'Web服务器(Apache)', 'bt': '宝塔面板', 'mysqld': 'MySQL数据库', 'rsynd': 'rsync主服务',
                 'php-fpm': 'PHP服务', 'systemd': '系统核心服务',
                 '/etc/rc.local': '用户自定义启动脚本', '/etc/profile': '全局用户环境变量',
                 '/etc/inittab': '用于自定义系统运行级别', '/etc/rc.sysinit': '系统初始化时调用的脚本',
                 'sshd': 'SSH服务', 'crond': '计划任务服务', 'udev-post': '设备管理系统', 'auditd': '审核守护进程',
                 'rsyslog': 'rsyslog服务', 'sendmail': '邮件发送服务', 'blk-availability': 'lvm2相关',
                 'local': '用户自定义启动脚本', 'netfs': '网络文件系统', 'lvm2-monitor': 'lvm2相关',
                 'xensystem': 'xen云平台相关', 'iptables': 'iptables防火墙', 'ip6tables': 'iptables防火墙 for IPv6',
                 'firewalld': 'firewall防火墙'}
        if name in runPs: return runPs[name]
        return name

    # 获取当前运行级别
    def get_my_runlevel(self):
        try:
            runlevel = public.ExecShell('runlevel')[0].split()[1]
        except:
            runlevel_dict = {"multi-user.target": '3', 'rescue.target': '1', 'poweroff.target': '0',
                             'graphical.target': '5', "reboot.target": '6'}
            r_tmp = public.ExecShell('systemctl get-default')[0].strip()
            if r_tmp in runlevel_dict:
                runlevel = runlevel_dict[r_tmp]
            else:
                runlevel = '3'
        return runlevel

    # ------------------------------ 获取启动项列表 end ------------------------------


class Process(object):
    process = RealProcess()

    # 获取进程列表
    def get_process_list(self):
        return self.process.get_process_list()

    # 获取进程信息->pid
    def get_process_info_by_pid(self, get: Any) -> dict:
        if not hasattr(get, 'pid'): return {'status': False, 'msg': '参数错误', 'data': {}}
        return self.process.get_process_info_by_pid(get.pid)

    # 通过name获取进程信息
    def get_process_info_by_name(self, get: Any) -> dict:
        if not hasattr(get, 'name'): return {'status': False, 'msg': '参数错误', 'data': {}}
        return self.process.get_process_info_by_name(get.name)

    def get_process_info_by_exec(self, get: Any) -> dict:
        if not hasattr(get, 'cli'): return {'status': False, 'msg': '参数错误', 'data': {}}
        return self.process.get_process_info_by_exec(get.cli)

    def get_process_info_by_port(self, get: Any) -> dict:
        if not hasattr(get, 'port'): return {'status': False, 'msg': '参数错误', 'data': {}}
        return self.process.get_process_info_by_port(get.port)

    def get_process_info_by_ip(self, get: Any) -> dict:
        if not hasattr(get, 'ip'): return {'status': False, 'msg': '参数错误', 'data': {}}
        return self.process.get_process_info_by_ip(get.ip)

    def get_process_info_by_openfile(self, get: Any) -> dict:
        if not hasattr(get, 'file_path'): return {'status': False, 'msg': '参数错误', 'data': {}}
        return self.process.get_process_info_by_openfile(get.file_path)

    # 获取进程树
    def get_process_tree(self, get: Any) -> dict:
        if not hasattr(get, 'pid'): return {'status': False, 'msg': '参数错误', 'data': {}}
        return self.process.get_process_tree(get.pid)

    # 结束进程pid
    def kill_pid(self, get: Any) -> dict:
        if not hasattr(get, 'pid'): return {'status': False, 'msg': '参数错误', 'data': {}}
        return self.process.kill_pid(get.pid)

    # 结束进程名
    def kill_name(self, get: Any) -> dict:
        if not hasattr(get, 'name'): return {'status': False, 'msg': '参数错误', 'data': {}}
        return self.process.kill_name(get.name)

    # 结束进程树
    def kill_tree(self, get: Any) -> dict:
        if not hasattr(get, 'pid'): return {'status': False, 'msg': '参数错误', 'data': {}}
        return self.process.kill_tree(get.pid)

    # 结束所有进程  pid,进程名，进程树
    def kill_proc_all(self, get: Any) -> dict:
        if not hasattr(get, 'pid'): return {'status': False, 'msg': '参数错误', 'data': {}}
        return self.process.kill_proc_all(get.pid)

    def kill_port(self, get: Any) -> dict:
        if not hasattr(get, 'port'): return {'status': False, 'msg': '参数错误', 'data': {}}
        return self.process.kill_port(get.port)

    def add_black_ip(self, get: Any) -> dict:
        if not hasattr(get, 'ips'): return {'status': False, 'msg': '参数错误', 'data': {}}
        return self.process.add_black_ip(get.ips)

    def del_black_ip(self, get: Any) -> dict:
        if not hasattr(get, 'ips'): return {'status': False, 'msg': '参数错误', 'data': {}}
        return self.process.del_black_ip(get.ips)

    def get_process_ps(self, get: Any) -> dict:
        if not hasattr(get, 'name'): return {'status': False, 'msg': '参数错误', 'data': {}}
        return self.process.get_process_ps(get.name)

    def get_run_list(self, get: Any) -> dict:
        if not hasattr(get, 'search'): return {'status': False, 'msg': '参数错误', 'data': {}}
        return self.process.get_run_list(get.search)


if __name__ == "__main__":
    p = RealProcess()
    print(p.get_computers_use())
    # print('========================')
    # print(p.get_process_list()['data'])
    # print('========================')
    # print(p.get_process_info_by_pid(1)['data'])
    # print('========================')
    # print(p.get_process_info_by_name('systemd'))
    # print('========================')
    # res = p.get_process_tree(1)
    # print(res['data'][1])
    # print('========================')
    # print(p.kill_pid(1))
    # print('========================')
    # print(p.kill_name('systemd'))
    # print('========================')
    # print(p.kill_tree(1))
    # print('========================')
    # print(p.kill_proc_all(1))
    # print('========================')
    # print(p.get_process_info_by_exec('nginx'))
    # print('========================')
    # print(p.get_process_info_by_port(8888))
    # print('========================')
    # print(p.get_process_ps('nginx'))
    # print('========================')
    # print(p.get_process_info_by_ip('192.168.168.66'))
    # print('========================')
    # print(p.add_black_ip(['1.1.1.1']))
    # print('========================')
    # print(p.del_black_ip(['1.1.1.1']))
    # print('========================')
