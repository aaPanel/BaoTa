#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: lwh <lwh@bt.cn>
# -------------------------------------------------------------------
# Time: 2023-08-05
# -------------------------------------------------------------------
# PHP未关闭错误提示
# -------------------------------------------------------------------


import sys, os

os.chdir('/www/server/panel')
sys.path.append("class/")

import public, re, os

_title = 'PHP报错误信息提示'
_version = 1.0  # 版本
_ps = "检测PHP是否关闭错误提示"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-8-5'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_php_display_errors.pl")
_tips = [
    "根据风险描述，在【软件商店】-【运行环境】找到对应版本的PHP插件，在【配置修改】页面，将display_errors设置为关闭并保存"
]

_help = ''
_remind = 'PHP错误提示可能会泄露网站程序的敏感信息；此方案通过关闭【display_errors】选项，防止网站信息泄露。'
_type = 'web'


def check_run():
    path = "/www/server/php"
    # 检查PHP目录是否存在
    if not os.path.exists(path):
        return True, '无风险'  # PHP未安装

    # 获取目录下的文件夹
    dirs = os.listdir(path)
    result = []
    for dir in dirs:
        # 动态检测是否为有效的PHP版本目录（检查php.ini是否存在）
        file_path = os.path.join(path, dir, "etc", "php.ini")
        if os.path.exists(file_path):
            try:
                php_ini = public.readFile(file_path)
                if not php_ini:
                    continue
                # 使用改进的正则表达式，支持多种值格式
                rep = r"\ndisplay_errors\s*=\s*(\S+)"
                if re.search(rep, php_ini):
                    status = re.findall(rep, php_ini)[0].strip().lower()
                    # 检测是否为开启状态（支持 On/on/1/yes/true）
                    if status in ['on', '1', 'yes', 'true']:
                        result.append(dir)
            except Exception as e:
                # 记录错误但继续检测其他版本
                public.print_log("检测 PHP {} display_errors 失败: {}".format(dir, e))
                continue
    if result:
        ret = "未关闭错误信息提示的PHP版本有：{}".format('、'.join(result))
        return False, ret
    else:
        return True, "无风险"
