#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: lkq <lkq@bt.cn>
# -------------------------------------------------------------------
# Time: 2022-08-10
# -------------------------------------------------------------------
# SSH 最大连接数检测
# -------------------------------------------------------------------

import re, public, os

_title = 'SSH 最大连接数检测'
_version = 1.0  # 版本
_ps = "SSH 最大连接数检测"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-8-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ssh_maxauth.pl")
_tips = [
    "在【/etc/ssh/sshd_config】文件中设置【MaxAuthTries】为3-5",
    "提示：SSH最大连接数为：3-6，请设置为3-5"
]

_help = ''
_remind = '此方案通过减少SSH最大连接数量，降低服务器被入侵的风险。注意修复之前确认SSH需要支持同时连接的数量，防止影响正常业务运行。'


def check_run():
    '''
        @name 检测ssh最大连接数
        @author lkq<2020-08-10>
        @return tuple (status<bool>,msg<string>)
    '''

    if os.path.exists('/etc/ssh/sshd_config'):
        try:
            info_data = public.ReadFile('/etc/ssh/sshd_config')
            if info_data:
                if re.search('MaxAuthTries\s+\d+', info_data):
                    maxauth = re.findall('MaxAuthTries\s+\d+', info_data)[0]
                    # max 需要大于3 小于6
                    if int(maxauth.split(' ')[1]) >= 3 and int(maxauth.split(' ')[1]) <= 6:
                        return True, '无风险'
                    else:
                        return False, '当前SSH最大连接数为：' + maxauth.split(' ')[1] + '，请设置为3-5'
                else:
                    return True, '无风险'
        except:
            return True, '无风险'
    return True, '无风险'


def repaired():
    '''
        @name 修复ssh最大连接数
        @author lkq<2020-08-10>
        @return tuple (status<bool>,msg<string>)
    '''
    # 暂时不处理
    pass
