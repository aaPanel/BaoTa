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
# 开启地址空间布局随机化
# -------------------------------------------------------------------
# import sys, os
# os.chdir('/www/server/panel')
# sys.path.append("class/")
import os, sys, re, public

_title = '是否开启硬链接保护'
_version = 1.0  # 版本
_ps = "是否开启硬链接保护"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-11-21'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_protected_hardlinks.pl")
_tips = [
    "操作如下：sysctl -w fs.protected_hardlinks=1",
]
_help = ''
_remind = '通过启用此内核参数，用户不能再创建指向他们不拥有的文件的软链接或硬链接，可以减少特权程序访问不安全文件系统的漏洞，增强服务器安全防护。'


def check_run():
    try:
        if os.path.exists("/proc/sys/fs/protected_hardlinks"):
            protected_hardlinks = public.ReadFile("/proc/sys/fs/protected_hardlinks")
            if int(protected_hardlinks) != 1:
                return False, '未开启硬链接保护'
            else:
                return True, "无风险"
    except:
        return True, "无风险"
    return True, "无风险"
