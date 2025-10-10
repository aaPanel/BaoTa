#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: lwh
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# 开启软链接保护
# -------------------------------------------------------------------
# import sys, os
# os.chdir('/www/server/panel')
# sys.path.append("class/")
import os, sys, re, public

_title = '是否限制核心转储'
_version = 1.0  # 版本
_ps = "是否限制核心转储"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-11-22'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_suid_dumpable.pl")
_tips = [
    "操作如下：sysctl -w fs.suid_dumpable=0",
]
_help = ''
_remind = 'setuid程序的核心转储更有可能包含敏感数据，限制任何setuid程序写入核心文件的能力可以降低敏感数据泄露的风险。'


def check_run():
    try:
        if os.path.exists("/proc/sys/fs/suid_dumpable"):
            suid_dumpable = public.ReadFile("/proc/sys/fs/suid_dumpable")
            if int(suid_dumpable) != 0:
                return False, '未对核心转储做限制，可能会出现信息泄露的情况。'
            else:
                return True, "无风险"
    except:
        return True, "无风险"
    return True, "无风险"
