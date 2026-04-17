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
# 检测是否禁ping
# -------------------------------------------------------------------


import os,sys,re,public

_title = 'ICMP检测'
_version = 3.0
_ps = "检测是否禁止ICMP协议访问服务器(禁Ping)"
_level = 2
_date = '2025-01-15'
_ignore = os.path.exists("data/warning/ignore/sw_ping.pl")
_tips = [
    "在【安全】页面中开启【禁Ping】功能",
    "注意：开启后无法通过ping通服务器IP或域名，请根据实际需求设置"
    ]

_help = ''
_remind = '此方案可以降低服务器真实IP被发现的风险，增强服务器的安全性。'


def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-05>
        @return tuple (status<bool>,msg<string>)
    '''
    try:
        # 1. 优先检查运行时实际值（/proc/sys/net/ipv4/icmp_echo_ignore_all）
        try:
            runtime_file = '/proc/sys/net/ipv4/icmp_echo_ignore_all'
            runtime_value = public.readFile(runtime_file)
            if runtime_value and runtime_value.strip() == '1':
                # 运行时已禁用ping，无风险
                return True, '无风险'
        except:
            pass

        # 2. 运行时未禁用，检查配置文件（可能已配置但未生效）
        try:
            file = '/etc/sysctl.conf'
            conf = public.readFile(file)
            rep = r"#*net\.ipv4\.icmp_echo_ignore_all\s*=\s*([0-9]+)"
            tmp = re.search(rep, conf)
            if tmp:
                config_value = tmp.groups(0)[0]
                if config_value == '1':
                    # 配置了但未生效
                    return False, '已配置禁Ping但未生效，请执行：sysctl -p'
        except:
            pass

        # 3. 既未运行时禁用，也未配置
        return False, '当前未开启【禁Ping】功能，存在服务器被ICMP攻击或被扫的风险'
    except:
        return True, '无风险'
