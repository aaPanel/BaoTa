#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# 开启地址空间布局随机化
# -------------------------------------------------------------------
# import sys, os
# os.chdir('/www/server/panel')
# sys.path.append("class/")
import os, sys, re, public

_title = '开启地址空间布局随机化'
_version = 1.0  # 版本
_ps = "开启地址空间布局随机化"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-08-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_kernel_space.pl")
_tips = [
    "【/proc/sys/kernel/randomize_va_space】 值为2：",
    "操作如下：sysctl -w kernel.randomize_va_space=2",
]
_help = ''
_remind = '此方案可以降低入侵者利用缓冲区溢出攻击服务器的风险，加强对服务器的防护。'

def check_run():
       try:
           if os.path.exists("/proc/sys/kernel/randomize_va_space"):
               randomize_va_space=public.ReadFile("/proc/sys/kernel/randomize_va_space")
               if int(randomize_va_space)!=2:
                   return False, '未开启地址空间布局随机化'
               else:
                   return True,"无风险"
       except:
           return True, "无风险"