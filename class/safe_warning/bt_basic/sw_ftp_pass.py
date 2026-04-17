#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: linxiao
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# FTP弱口令检测
# -------------------------------------------------------------------
# import sys, os
# os.chdir('/www/server/panel')
# sys.path.append("class/")
import os,public

_title = 'FTP服务弱口令检测'
_version = 2.0  # 版本
_ps = "检测已启用的FTP服务弱口令"  # 描述
_level = 3  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-08-12'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ftp_pass.pl")
_tips = [
    "请到【FTP】页面修改FTP密码",
    "注意：请不要使用过于简单的帐号密码，以免造成安全隐患",
    "推荐使用高安全强度的密码：分别包含数字、大小写、特殊字符混合，且长度不少于7位。",
    "使用【Fail2ban防爆破】插件对FTP服务进行保护"
]

_help = ''
_remind = '此方案可以加强对FTP服务器的防护，防止入侵者通过爆破入侵FTP服务器。'


def check_run():
    """检测FTP弱口令
        @author linxiao<2020-9-19>
        @return (bool, msg)
    """

    pass_info = public.ReadFile("/www/server/panel/config/weak_pass.txt")
    if not pass_info: return True, '无风险'
    pass_list = pass_info.split('\n')
    data = public.M("ftps").select()
    ret = ""
    for i in data:
        if i['password'] in pass_list:
            ret += "FTP用户：" + i['name'] + "存在弱口密码：" + short_passwd(i['password']) + "<br/>"
    if ret:
        # print(ret)
        return False, ret
    else:
        return True, '无风险'


def short_passwd(text):
    """
    @name 密码脱敏
    @author lwh
    """
    text_len = len(text)
    if text_len > 4:
        return text[:2] + "**" + text[text_len-2:]
    else:
        if 1 < text_len <= 4:
            return text[:1] + "****" + text[text_len-1]
        else:
            return "******"
