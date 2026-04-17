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
# 检测风险用户
# -------------------------------------------------------------------


import os,sys,re,public

_title = '检测风险用户'
_version = 1.0                              # 版本
_ps = "检测系统用户列表中是否存在风险用户"      # 描述
_level = 0                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-05'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_login_user.pl")
_tips = [
    "如果这些用户不是服务器管理员添加的，则可能系统已被入侵，应尽快处理"
    ]

_help = ''


def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-04>
        @return tuple (status<bool>,msg<string>)
    '''

    u_list = get_ulist()

    try_users = []
    for u_info in u_list:
        if u_info['user'] == 'root': continue
        if u_info['pass'] == '*': continue
        if u_info['uid'] == 0:
            try_users.append(u_info['user'] + ' > 未知的管理员用户 [高危]')

        if u_info['login'] in ['/bin/bash','/bin/sh']:
            try_users.append(u_info['user'] + ' > 可登录的用户 [中危]')

    if try_users:
        return False, '以下用户存在安全风险: <br />' + ('<br />'.join(try_users))

    return True,'无风险'



#获取用户列表
def get_ulist():
    u_data = public.readFile('/etc/passwd')
    u_list = []
    for i in u_data.split("\n"):
        u_tmp = i.split(':')
        if len(u_tmp) < 3: continue
        u_info = {}
        u_info['user'],u_info['pass'],u_info['uid'],u_info['gid'],u_info['user_msg'],u_info['home'],u_info['login'] = u_tmp
        u_list.append(u_info)
    return u_list