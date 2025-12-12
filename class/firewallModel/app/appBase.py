# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------

# ------------------------------
# 系统防火墙模型 - 底层基类
# ------------------------------

import sys
import subprocess
if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
import public


class Base(object):

    def __init__(self):
        pass

    # 2024/3/22 下午 3:18 通用返回
    def _result(self, status: bool, msg: str) -> dict:
        '''
            @name 通用返回
            @author wzz <2024/3/22 下午 3:19>
            @param status: True/False
                    msg: 提示信息
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        return {"status": status, "msg": msg}

    # 2024/3/22 下午 4:55 检查是否设置了net.ipv4.ip_forward = 1，没有则设置
    def check_ip_forward(self) -> dict:
        '''
            @name 检查是否设置了net.ipv4.ip_forward = 1，没有则设置
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        import os
        if os.path.exists("/etc/default/ufw"):
            #ufw需要开启转发
            if public.ExecShell("iptables -t nat -C POSTROUTING_BT -j MASQUERADE")[1] != '':
                public.ExecShell(""" grep -q 'DEFAULT_FORWARD_POLICY="DROP"' /etc/default/ufw && sed -i 's/DEFAULT_FORWARD_POLICY="DROP"/DEFAULT_FORWARD_POLICY="ACCEPT"/' /etc/default/ufw && ufw reload """)
                public.ExecShell("iptables -t nat -N POSTROUTING_BT; iptables -t nat -A POSTROUTING -j POSTROUTING_BT; iptables -t nat -A POSTROUTING_BT -j MASQUERADE")
        elif os.path.exists("/usr/sbin/firewalld"):
                if 'no' in public.ExecShell("firewall-cmd --query-masquerade")[0]:
                    public.ExecShell("firewall-cmd --permanent --add-masquerade;firewall-cmd --reload")
        stdout, stderr = public.ExecShell("sysctl net.ipv4.ip_forward")
        if "net.ipv4.ip_forward = 1" not in stdout:
            # 2024/3/22 下午 4:56 永久设置
            stdout, stderr = public.ExecShell("echo net.ipv4.ip_forward=1 >> /etc/sysctl.conf")
            if stderr:
                return self._result(False, "设置net.ipv4.ip_forward失败, err: {}".format(stderr))

            stdout, stderr = public.ExecShell("sysctl -p")
            if stderr:
                return self._result(False, "设置net.ipv4.ip_forward失败, err: {}".format(stderr))
            return self._result(True, "设置net.ipv4.ip_forward成功")
        return self._result(True, "net.ipv4.ip_forward已经设置")

    # 2024/3/18 上午 11:35 处理192.168.1.100-192.168.1.200这种ip范围
    # 返回192.168.1.100,192.168.1.101,192.168.1...,192.168.1.200列表
    def handle_ip_range(self, ip):
        '''
            @name 处理192.168.1.100-192.168.1.200这种ip范围的ip列表
            @author wzz <2024/3/19 下午 4:58>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        ip_range = ip.split("-")
        ip_start = ip_range[0]
        ip_end = ip_range[1]
        ip_start = ip_start.split(".")
        ip_end = ip_end.split(".")
        ip_start = [int(i) for i in ip_start]
        ip_end = [int(i) for i in ip_end]
        ip_list = []
        for i in range(ip_start[0], ip_end[0] + 1):
            for j in range(ip_start[1], ip_end[1] + 1):
                for k in range(ip_start[2], ip_end[2] + 1):
                    for l in range(ip_start[3], ip_end[3] + 1):
                        ip_list.append("{}.{}.{}.{}".format(i, j, k, l))
        return ip_list

    # 2024/11/22 15:19 处理70-79这种端口范围
    # 返回70,71,72,...79列表
    def handle_port_range(self, port):
        '''
            @name 处理70-79这种端口范围的端口列表
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        port_range = port.split("-")
        port_start = int(port_range[0])
        port_end = int(port_range[1])
        port_list = []
        for i in range(port_start, port_end + 1):
            port_list.append(i)
        return port_list

    def run_command(self, command):
        try:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return e.stdout, e.stderr
