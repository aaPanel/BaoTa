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
# 用户缺省权限检查
# -------------------------------------------------------------------
# import sys, os
# os.chdir('/www/server/panel')
# sys.path.append("class/")
import os, sys, re, public

_title = '/etc/profile用户缺省权限检查'
_version = 1.0  # 版本
_ps = "/etc/profile用户缺省权限检查"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-08-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_umask.pl")
_tips = [
    "【/etc/profile】 文件中所设置的umask为002,不符合要求，建议设置为027",
    "操作如下：修改 umask 为027",
]
_help = ''
_remind = '此方案可以加强用户权限的控制，避免用户权限过高。'


def check_run():
      # 判断是否存在/etc/profile文件
    if os.path.exists("/etc/profile"):
        # 读取文件内容
        profile = public.ReadFile("/etc/profile")
        # 判断是否存在umask设置
        if re.search("umask 0",profile):
            # 判断是否设置为027
            if re.search("umask 027",profile):
                return True,"无风险"
            else:
                return True,"无风险"
                # return False,"未设置umask为027"
        else:
            return True,"无风险"