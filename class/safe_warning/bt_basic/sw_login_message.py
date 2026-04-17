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
# 检测用户登录通知
# -------------------------------------------------------------------


import os,sys,re,public

_title = 'SSH用户登录通知'
_version = 1.0                              # 版本
_ps = "检测是否开启SSH用户登录通知"              # 描述
_level = 0                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-05'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_login_message.pl")
_tips = [
    "在【安全】页面，【SSH安全管理】 - 【登录报警】中开启【监控root用户登陆】功能"
    ]

_help = ''


def return_bashrc():
    if os.path.exists('/root/.bashrc'):return '/root/.bashrc'
    if os.path.exists('/etc/bashrc'):return '/etc/bashrc'
    if os.path.exists('/etc/bash.bashrc'):return '/etc/bash.bashrc'
    return '/root/.bashrc'

def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-04>
        @return tuple (status<bool>,msg<string>)
    '''

    data = public.ReadFile(return_bashrc())
    if not data: return True,'无风险'
    if re.search('ssh_security.py login', data):
        return True,'无风险'
    else:
        return False,'未配置SSH用户登录通知，无法在第一时间获知服务器是否被非法登录'