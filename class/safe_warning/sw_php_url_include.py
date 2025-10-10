#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: lwh
# -------------------------------------------------------------------
# Time: 2024-02-23
# -------------------------------------------------------------------
# PHP开启远程文件包含
# -------------------------------------------------------------------

# import sys,os
# os.chdir('/www/server/panel')
# sys.path.append("class/")
import re, public, os

_title = 'PHP启用远程文件包含'
_version = 1.0  # 版本
_ps = "PHP存在远程文件包含风险"  # 描述
_level = 3  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2024-02-23'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_php_url_include.pl")
_tips = [
    "在【php.ini】文件中设置【allow_url_include】配置为Off"
]

_help = ''
_remind = '此方案可以防止网站被黑客利用远程包含漏洞控制服务器'


def check_run():
    path = "/www/server/php"
    # 获取目录下的文件夹
    dirs = os.listdir(path)
    resulit = []
    for dir in dirs:
        if dir in ["52", "53", "54", "55", "56", "70", "71", "72", "73", "74", "80", "81"]:
            file_path = path + "/" + dir + "/etc/php.ini"
            if os.path.exists(file_path):
                # 获取文件内容
                try:
                    php_ini = public.readFile(file_path)
                    # 查找include
                    if re.search("\nallow_url_include\\s*=\\s*(\\w+)", php_ini):
                        include_php = re.search("\nallow_url_include\\s*=\\s*(\\w+)", php_ini).groups()[0]
                        if include_php.lower() == "off":
                            pass
                        else:
                            resulit.append(dir)
                except:
                    pass
    if len(resulit) > 0:
        return False, "存在远程包含风险的php版本如下：【" + ",".join(resulit) + "】，请在php.ini中设置allow_url_include为Off"
    else:
        return True, "无风险"
