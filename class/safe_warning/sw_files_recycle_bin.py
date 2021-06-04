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
# 检测是否开启文件回收站
# -------------------------------------------------------------------


import os,sys,re,public

_title = '文件回收站检测'
_version = 1.0                              # 版本
_ps = "检测文件回收站是否开启"                # 描述
_level = 2                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-05'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_files_recycle_bin.pl")
_tips = [
    "在【文件】页面，【回收站】 - 中开启【文件回收站】功能"
    ]

_help = ''


def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-05>
        @return tuple (status<bool>,msg<string>)
    '''
    if not os.path.exists('/www/server/panel/data/recycle_bin.pl'):
        return False,'当前未开启【文件回收站】功能，存在文件被误删的情况下无法找回的风险'
    return True,'无风险'
