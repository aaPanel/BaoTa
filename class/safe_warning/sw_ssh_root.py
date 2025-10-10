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
# 检查SSH root是否可以登录
# -------------------------------------------------------------------
import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import os, sys, re, public

_title = '检查SSH root是否可以登录'
_version = 1.0  # 版本
_ps = "检查SSH root是否可以登录"  # 描述
_level = 0  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-08-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ssh_root.pl")
_tips = [
    "【/etc/ssh/sshd_config】 添加PermitRootLogin no参数",
    "PermitRootLogin no",
]
_help = ''
_remind = '此方案修复之后，无法使用root用户进行SSH远程登录'



def check_run():
    #ssh 检查root 登录
    if os.path.exists('/etc/ssh/sshd_config'):
        try:
            info_data = public.ReadFile('/etc/ssh/sshd_config')
            if info_data:
                if re.search('PermitRootLogin\s+no', info_data):
                    return True, '无风险'
                else:
                    return True, '无风险'
                    return False, '当前/etc/ssh/sshd_config 中的参数【PermitRootLogin】配置为：yes，请设置为no'
        except:
            return True, '无风险'
    return True, '无风险'