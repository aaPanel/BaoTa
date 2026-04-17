#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: lwh
# -------------------------------------------------------------------
# Time: 2023-11-22
# -------------------------------------------------------------------
# SSH 登录超时时间
# -------------------------------------------------------------------

import re, public, os

_title = 'SSH 登录超时配置检测'
_version = 1.0  # 版本
_ps = "SSH 登录超时配置检测"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-8-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ssh_login_grace.pl")
_tips = [
    "在【/etc/ssh/sshd_config】文件中设置【LoginGraceTime】为60",
]

_help = ''
_remind = '将LoginGraceTime参数设置为一个较小的数字将最大限度地降低对SSH服务器成功进行暴力破解的风险。它还将限制并发的未经身份验证的连接数量。'


def check_run():
    '''
        @name SSH 登录超时配置检测
        @author lwh<2023-11-22>
        @return tuple (status<bool>,msg<string>)
    '''
    path = '/etc/ssh/sshd_config'
    if not os.path.exists(path):
        return True, '无风险'
    try:
        conf = public.ReadFile(path)
        if not conf:
            return True, '无风险'
        # 匹配非注释行的 LoginGraceTime 配置及值
        matches = re.findall(r'^\s*(?!#)\s*LoginGraceTime\s+(\S+)', conf, re.M)
        if not matches:
            return False, '未启用SSH登录超时配置'
        # 获取最后一个有效配置值
        val = matches[-1].split('#')[0].strip().strip('"').strip("'")
        if not val.isdigit():
            return True, '无风险'
        # CIS 标准：LoginGraceTime 应 ≤ 60
        if int(val) > 60:
            return False, f'LoginGraceTime={val}秒，建议设置为60秒或更小'
        return True, '无风险'
    except:
        return True, '无风险'
