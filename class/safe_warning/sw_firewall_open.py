#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# 系统防火墙检测
# -------------------------------------------------------------------


import os,public,psutil
import re

_title = '系统防火墙检测'
_version = 1.0                              # 版本
_ps = "检测是否开启系统防火墙"               # 描述
_level = 2                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-08-18'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_firewall_open.pl")
_tips = [
    "在安全-系统防火墙中打开防火墙开关",
    "建议开启系统防火墙，以避免所有服务器端口暴露在互联网上，如服务器有【安全组】功能，请忽略此提示",
    "注意：开启系统防火墙需提前将需要开放的端口，特别是SSH和面板端口加入放行列表，否则可能导致服务器无法访问"
    ]

_help = ''
_remind = '此方案可以降低服务器暴露的风险面，增强对网站的防护。但是需要在端口规则处添加需要开放的端口，否则会导致网站无法访问。'


def check_run():
    '''
        @name 开始检测
        @author hwliang<2022-08-18>
        @return tuple (status<bool>,msg<string>)
    '''
    # if os.path.exists('/usr/sbin/firewalld') and os.path.exists('/usr/bin/yum'):
    #     res = public.ExecShell("ps -ef|grep firewalld|grep -v grep")[0]
    #     if res: return True,'无风险'
    #     res = public.ExecShell("systemctl is-active firewalld")[0]
    #     if res == "active": return True,'无风险'
    #     res = public.ExecShell("systemctl list-units | grep firewalld")[0]
    #     if res.find('active running') != -1: return True,'无风险'
    #     return False,'未开启系统防火墙，存在安全风险'
    # elif os.path.exists('/usr/sbin/ufw') and os.path.exists('/usr/bin/apt-get'):
    #     res = public.ExecShell("systemctl is-active ufw")[0]
    #     if res == "active": return True,'无风险'
    #     res = public.ExecShell("systemctl list-units | grep ufw")[0]
    #     if res.find('active running') != -1: return True,'无风险'
    #     res = public.ExecShell('/lib/ufw/ufw-init status')[0]
    #     if res.find("Firewall is not running") != -1: return False,'未开启系统防火墙，存在安全风险'
    #     res = public.ExecShell('ufw status verbose')[0]
    #     if res.find('inactive') != -1: return False,'未开启系统防火墙，存在安全风险'
    #     return True,'无风险'
    # else:
    #     res = public.ExecShell("/etc/init.d/iptables status")[0]
    #     if res.find('not running') != -1: return False,'未开启系统防火墙，存在安全风险'
    #     res = public.ExecShell("systemctl is-active iptables")[0]
    #     if res == "active": return True,'无风险'
    #     return True,'无风险'
    # import psutil
    if os.path.exists('/usr/sbin/firewalld'):
        for pid in psutil.pids():
            try:
                p = psutil.Process(pid)
                if '/usr/sbin/firewalld' in p.cmdline():
                    return True,'无风险'
            except:
                pass
        return False,'未开启系统防火墙，存在安全风险'
    elif os.path.exists('/usr/bin/firewalld'):
        for pid in psutil.pids():
            try:
                p = psutil.Process(pid)
                if '/usr/bin/firewalld' in p.cmdline():
                    return True, '无风险'
            except:
                pass
        return False, '未开启系统防火墙，存在安全风险'
    elif os.path.exists('/usr/sbin/ufw'):
        res = public.ExecShell("ufw status verbose|grep -E '(Status: active|激活)'")
        if res[0].strip():
            return True, '无风险'
        else:
            return False, '未开启系统防火墙，存在安全风险'
    elif os.path.exists('/sbin/ufw'):
        res = public.ExecShell("/sbin/ufw status |grep -E '(Status: active|激活)'")
        if res[0].strip():
            return True, '无风险'
        else:
            return False, '未开启系统防火墙，存在安全风险'
    elif os.path.exists('/usr/sbin/iptables'):
        res = public.ExecShell("service iptables status|grep 'Chain INPUT'")
        if res[0].strip():
            return True, '无风险'
        else:
            return False, '未开启系统防火墙，存在安全风险'
    return False, '未安装系统防火墙，存在安全风险'

    # firewall_files = {'/usr/sbin/firewalld': "pid", '/usr/bin/firewalld': "pid",
    #                   '/usr/sbin/ufw': "ufw status verbose|grep -E '(Status: active|激活)'",
    #                   '/sbin/ufw': "/sbin/ufw status |grep -E '(Status: active|激活)'",
    #                   '/usr/sbin/iptables': "service iptables status|grep 'Chain INPUT'"}
    # for f in firewall_files.keys():
    #     if not os.path.exists(f): continue
    #     _cmd = firewall_files[f]
    #     if _cmd != "pid":
    #         res = public.ExecShell(_cmd)
    #         if res[0].strip():
    #             return True,'无风险'
    #         else:
    #             return False,'未开启系统防火墙，存在安全风险'
    #     for pid in psutil.pids():
    #         try:
    #             p = psutil.Process(pid)
    #             if f in p.cmdline():
    #                 return True,'无风险'
    #         except:
    #             pass
    #     return False,'未开启系统防火墙，存在安全风险'
    # return False,'未安装系统防火墙，存在安全风险'
    # status = public.get_firewall_status()
    # if status == 1:
    #     return True,'无风险'
    # elif status == -1:
    #     return False,'未安装系统防火墙，存在安全风险'
    # else:
    #     return False,'未开启系统防火墙，存在安全风险'