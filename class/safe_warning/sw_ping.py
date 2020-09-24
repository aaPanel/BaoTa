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
_version = 1.0                              # 版本
_ps = "检测是否禁止ICMP协议访问服务器(禁Ping)"              # 描述
_level = 1                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-05'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ping.pl")
_tips = [
    "在【安全】页面中开启【禁Ping】功能",
    "注意：开启后无法通过ping通服务器IP或域名，请根据实际需求设置"
    ]

_help = ''


def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-05>
        @return tuple (status<bool>,msg<string>)
    '''
    
    cfile = '/etc/sysctl.conf'
    conf = public.readFile(cfile)
    rep = r"#*net\.ipv4\.icmp_echo_ignore_all\s*=\s*([0-9]+)"
    tmp = re.search(rep,conf)
    if tmp:
        if tmp.groups(0)[0] == '1':
            return True,'无风险'

    return False,'当前未开启【禁Ping】功能，存在服务器被ICMP攻击或被扫的风险'
