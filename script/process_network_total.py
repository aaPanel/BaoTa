#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang<hwl@bt.cn>
#-------------------------------------------------------------------

import sys
import time
import os
import struct

os.chdir('/www/server/panel')
if 'class/' in sys.path: sys.path.insert(0,"class/")
import copy
try:
    import pcap
except ImportError:
    if os.path.exists('/usr/bin/apt'):
        os.system("apt install libpcap-dev -y")
    elif os.path.exists('/usr/bin/dnf'):
        red_file = '/etc/redhat-release'
        if os.path.exists(red_file):
            f = open(red_file,'r')
            red_body = f.read()
            f.close()
            if red_body.find('CentOS Linux release 8.') != -1:
                rpm_file = '/root/libpcap-1.9.1.rpm'
                down_url = "wget -O {} https://repo.almalinux.org/almalinux/8/PowerTools/x86_64/os/Packages/libpcap-devel-1.9.1-5.el8.x86_64.rpm --no-check-certificate -T 10".format(rpm_file)
                print(down_url)
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
    try:
        import pcap
    except ImportError:
        print("pypcap module install failed.")
        sys.exit()

class process_network_total:
    __pid_file = 'logs/process_network_total.pid'
    __inode_list = {}
    __net_process_list = {}
    __net_process_size = {}
    __last_stat = 0
    __last_write_time = 0
    __end_time = 0

    def start(self,timeout = 0):
        '''
            @name 启动进程网络监控
            @author hwliang<2021-09-13>
            @param timeout<int> 结束时间(秒)，0表示持久运行，默认为0
            @return void
        '''        
        stime = time.time()
        self.__end_time = timeout + stime
        self.__last_stat = stime
        try:
            p = pcap.pcap() # 监听所有网卡
            p.setfilter('tcp') # 只监听TCP数据包
            for p_time,p_data in p:
                self.handle_packet(p_data)
                # 过期停止监听
                if timeout > 0:
                    if p_time > self.__end_time:
                        self.rm_pid_file()
                        break
        except:
            self.rm_pid_file()
        
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
        self.total_net_process(dst,src,pack_size)

    def total_net_process(self,dst,src,pack_size):
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
            net_process.append(str(pid) + " " + str(process_size[pid]['down']) + " " + str(process_size[pid]['up']) + " " + str(process_size[pid]['down_package']) + " " + str(process_size[pid]['up_package']))

        f = open(w_file,'w+',encoding='utf-8')
        f.write('\n'.join(net_process))
        f.close()

    def hex_to_ip(self, hex_ip):
        '''
            @name 将16进制的IP地址转换为字符串IP地址
            @author hwliang<2021-09-13>
            @param hex_ip<string> 16进制的IP地址:16进程端口
            @return tuple(ip<str>,port<int>) IP地址,端口
        '''
        hex_ip,hex_port = hex_ip.split(':')
        ip = '.'.join([str(int(hex_ip[i:i+2], 16)) for i in range(0, len(hex_ip), 2)][::-1])
        port = int(hex_port, 16)
        return ip,port

    def get_tcp_stat(self,force = False):
        '''
            @name 获取当前TCP连接状态表
            @author hwliang<2021-09-13>
            @param force<bool> 是否强制刷新
            @return dict
        '''
        if not force and self.__net_process_list: return self.__net_process_list
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
            local_ip,local_port = self.hex_to_ip(tcp_tmp[1])
            if local_ip == '127.0.0.1': continue
            remote_ip,remote_port = self.hex_to_ip(tcp_tmp[2])
            if local_ip == remote_ip: continue
            if remote_ip == '0.0.0.0': continue
            
            pid = self.inode_to_pid(inode,force)
            if not pid: continue 
            
            key = self.get_ip_pack(local_ip) + b':' + self.get_port_pack(local_port)
            self.__net_process_list[key] = pid
        return self.__net_process_list
            
    
    def get_port_pack(self,port):
        '''
            @name 将端口转换为字节流
            @author hwliang<2021-09-13>
            @param port<int> 端口
            @return bytes
        '''
        return struct.pack('H',int(port))[::-1]
    
    def get_ip_pack(self,ip):
        '''
            @name 将IP地址转换为字节流
            @author hwliang<2021-09-13>
            @param ip<str> IP地址
            @return bytes
        '''
        ip_arr = ip.split('.')
        ip_pack = b''
        for i in ip_arr:
            ip_pack += struct.pack('B',int(i))
        return ip_pack

    def inode_to_pid(self,inode,force = False):
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

    def get_process_inodes(self,force = False):
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

    def get_process_name(self,pid):
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
        pid_file = open(self.__pid_file,'w')
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

if __name__ == '__main__':
    if len(sys.argv) > 1:
        timeout = int(sys.argv[-1])
    else:
        timeout = 0
    p = process_network_total()
    p.write_pid()
    p.start(timeout)