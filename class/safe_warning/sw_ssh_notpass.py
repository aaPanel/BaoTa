#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: lkq <lkq@bt.cn>
# -------------------------------------------------------------------
# Time: 2022-08-10
# -------------------------------------------------------------------
# 禁止SSH空密码登录
# -------------------------------------------------------------------
import re,public,os


_title = '禁止SSH空密码登录'
_version = 1.0                              # 版本
_ps = "禁止SSH空密码登录"          # 描述
_level = 3                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-8-10'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ssh_notpasswd.pl")
_tips = [
    "在【/etc/ssh/sshd_config】文件中设置【PermitEmptyPasswords】将配置为no",
    "提示：【PermitEmptyPasswords】将配置为no"
    ]

_help = ''
_remind = '此方案防止服务器使用空密码登录。注意修复后服务器无法使用空密码登录，确保相关的业务访问同步配置登录密码。'


def check_run():
    '''
        @name 检测禁止SSH空密码登录
        @author lkq<2020-08-10>
        @return tuple (status<bool>,msg<string>)
    '''

    if os.path.exists('/etc/ssh/sshd_config'):
        try:
            info_data = public.ReadFile('/etc/ssh/sshd_config')
            if info_data:
                if re.search('\nPermitEmptyPasswords\\s*yes', info_data):
                    return False, '当前【PermitEmptyPasswords】配置为：yes，请设置为no'
                else:
                    return True, '无风险'
        except:
            return True, '无风险'
    return True, '无风险'