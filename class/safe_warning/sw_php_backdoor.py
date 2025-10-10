#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: lwh <lwh@bt.cn>
# -------------------------------------------------------------------
# Time: 2023-08-07
# -------------------------------------------------------------------
# PHP.ini挂马
# -------------------------------------------------------------------


import sys, os

os.chdir('/www/server/panel')
sys.path.append("class/")

import public, re, os

_title = 'PHP配置文件挂马检测'
_version = 1.0  # 版本
_ps = "检测PHP配置文件是否被挂马"  # 描述
_level = 3  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-8-7'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_php_backdoor.pl")
_tips = [
    "根据风险描述，在【软件商店】-【运行环境】找到对应版本的PHP插件",
    "在【配置文件】页面，找到auto_prepend_file或auto_append_file，删除后面的内容，保存并重启PHP"
]

_help = ''
_remind = '此方案可以删除php配置文件的恶意代码，并建议对服务器进行全面的木马扫描，清除后门文件，并修复网站漏洞。'
_type = 'web'


def check_run():
    path = "/www/server/php"
    # 获取目录下的文件夹
    dirs = os.listdir(path)
    result = {}
    for dir in dirs:
        if dir in ["52", "53", "54", "55", "56", "70", "71", "72", "73", "74", "80", "81"]:
            file_path = path + "/" + dir + "/etc/php.ini"
            if os.path.exists(file_path):
                # 获取文件内容
                try:
                    php_ini = public.readFile(file_path)
                    if re.search("\nauto_prepend_file\\s?=\\s?(.+)", php_ini):
                        prepend = re.findall("\nauto_prepend_file\\s?=\\s?(.+)", php_ini)
                        if "data:;base64" in prepend[0]:
                            result[dir] = ["auto_prepend_file"]
                    if re.search("\nauto_append_file\\s?=\\s?(.+)", php_ini):
                        append = re.findall("\nauto_append_file\\s?=\\s?(.+)", php_ini)
                        if "data:;base64" in append[0]:
                            if dir in result:
                                result[dir].append("auto_append_file")
                            else:
                                result[dir] = ["auto_append_file"]
                except:
                    pass
    if result:
        ret = ""
        for i in result:
            ret += "【PHP" + i + "】存在恶意代码的字段:" + ",".join(result[i]) + "<br/>"
        return False, ret
    else:
        return True, "无风险"
