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
# Mysql 弱口令检测
# -------------------------------------------------------------------

import  public, os
_title = '面板登录告警是否开启'
_version = 1.0  # 版本
_ps = "面板登录告警是否开启"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-8-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_panel_swing.pl")
_tips = [
    "在【面板设置】-【通知设置】-【面板登录告警】中开启"
]
_help = ''
_remind = '此方案可以加强面板防护，及时发现非法入侵面板行为。'

def check_run():
    '''
        @name 面板登录告警是否开启
        @time 2022-08-12
        @author lkq@bt.cn
    '''
    send_type = ""
    tip_files = ['panel_login_send.pl','login_send_type.pl','login_send_mail.pl','login_send_dingding.pl']
    for fname in tip_files:
        filename = 'data/' + fname
        if os.path.exists(filename):
            return True, '无风险'
    return False, '在【面板设置】-【通知设置】-【面板登录告警】中开启'



