#!/usr/bin/python
# coding: utf-8

import sys, os, public
_title = '关闭非加密远程管理telnet'
_version = 1.0  # 版本
_ps = "关闭非加密远程管理telnet检查"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-15'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_telnet_server.pl")
_tips = [
    "尽可能使用加密远程管理sshd服务，关闭不安全的telnet服务",
    "systemctl stop telnet.socket停止telnet服务"
]
_help = ''
_remind = '此方案会关闭不安全的telnet服务，降低数据泄露的风险。若业务需求telnet，则忽略此风险项。'


def check_run():
    result = public.ExecShell('systemctl is-active telnet.socket')[0].strip()
    if 'active' == result:
        return False, 'telnet服务未关闭'
    else:
        return True, '无风险'

