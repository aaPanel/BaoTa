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
_title = '面板未开启监控'
_version = 1.0  # 版本
_ps = "面板未开启监控"  # 描述
_level = 1  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-8-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_panel_control.pl")
_tips = [
    "在【监控】-【系统监控】中开启"
]
_help = ''
_remind = '开启服务器监控，可以记录服务器近期的运行情况，方便系统出现异常时的排查工作。'

def check_run():
    '''
        @name 面板未开启监控
        @time 2022-08-12
        @author lkq@bt.cn
    '''
    global _tips
    send_type = ""
    if os.path.exists("/www/server/panel/data/control.conf"):
        return True, '无风险'
    return False, _tips[0]



