#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# 检查SSH密码失效时间
# -------------------------------------------------------------------
import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import os, sys, re, public

_title = '检查SSH密码修改最小间隔'
_version = 1.0  # 版本
_ps = "检查SSH密码修改最小间隔"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-08-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ssh_passmin.pl")
_tips = [
    "【/etc/login.defs】 PASS_MIN_DAYS 应设置为大于等于7",
    "PASS_MIN_DAYS 7   需同时执行命令设置root 密码失效时间   命令如下:  chage --mindays 7 root",
]
_help = ''
_remind = '此方案是设置SSH登录密码修改后，多少天之内无法再次修改。'


def check_run():
    try:
        p_file = '/etc/login.defs'
        p_body = public.readFile(p_file)
        if not p_body: return True, '无风险'
        tmp = re.findall("\nPASS_MIN_DAYS\s+(.+)", p_body, re.M)
        if not tmp: return True, '无风险'
        maxdays = tmp[0].strip()
        #7-14
        if int(maxdays) < 7:
            return False, '【%s】文件中把PASS_MIN_DAYS大于等于7' % p_file
        return True, '无风险'
    except:
        return True, '无风险'
