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

_title = '是否开启软链接保护'
_version = 1.0  # 版本
_ps = "是否开启软链接保护"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-11-21'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_protected_symlinks.pl")
_tips = [
    "操作如下：sysctl -w fs.protected_symlinks=1",
]
_help = ''
_remind = '通过启用此内核参数，仅当在粘性全局可写目录之外时，或者当目录所有者匹配符号链接的所有者时，才允许跟踪符号链接。禁止此类符号链接有助于缓解基于特权程序访问的不安全文件系统的漏洞。'


def check_run():
    try:
        if os.path.exists("/proc/sys/fs/protected_symlinks"):
            protected_symlinks = public.ReadFile("/proc/sys/fs/protected_symlinks")
            if int(protected_symlinks) != 1:
                return False, '未开启软链接保护'
            else:
                return True, "无风险"
    except:
        return True, "无风险"
    return True, "无风险"
