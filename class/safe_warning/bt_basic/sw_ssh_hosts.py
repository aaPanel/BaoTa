#!/usr/bin/python
#coding: utf-8

import os,sys,re,public


_title = 'ssh访问控制列表检查'
_version = 1.0  # 版本
_ps = "设置ssh登录白名单"  # 描述
_level = 0  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-09'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ssh_hosts.pl")
_tips = [
    "在【/etc/hosts.deny】添加ALL:ALL",
    "在【/etc/hosts.allow】添加sshd:【来访者IP地址】"
]
_help = ''
_remind = '此方案会阻挡除白名单以外的其余IP登录服务器，增强服务器的安全防护。注意此方案存在风险，修复之前一定要确保已添加可访问服务器的IP。'


def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    cfile = '/etc/hosts.deny'
    conf = public.ReadFile(cfile)
    if 'all:all' in conf or 'ALL:ALL' in conf:
        return True, '无风险'
    else:
        return False, '未设置ssh登录白名单'
