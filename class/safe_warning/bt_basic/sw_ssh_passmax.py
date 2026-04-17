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

_title = '检查SSH密码失效时间'
_version = 1.0  # 版本
_ps = "检查SSH密码失效时间"  # 描述
_level = 0  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-08-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ssh_passmax.pl")
_tips = [
    "【/etc/login.defs】 使用非密码登陆方式密钥对。请忽略此项, 在/etc/login.defs 中将PASS_MAX_DAYS 参数设置为90-180之间",
    "PASS_MAX_DAYS 90   需同时执行命令设置root密码到期时间   命令如下:  chage --maxdays 90 root",
]
_help = ''
_remind = '此方案通过设置root登录密码的有效期，降低被爆破的风险。注意修复方案会使root密码到期后失效，需要在到期之前修改密码，若修改不及时可能会影响部分业务运行。'


def check_run():
    try:
        p_file = '/etc/login.defs'
        p_body = public.readFile(p_file)
        if not p_body: return True, '无风险'
        tmp = re.findall("\nPASS_MAX_DAYS\s+(.+)", p_body, re.M)
        if not tmp: return True, '无风险'
        maxdays = tmp[0].strip()
        #60-180之间
        if int(maxdays) < 90 or int(maxdays) > 180:
            return False, '【%s】文件中把PASS_MAX_DAYS设置为90-180之间' % p_file
        return True, '无风险'
    except:
        return True, '无风险'

