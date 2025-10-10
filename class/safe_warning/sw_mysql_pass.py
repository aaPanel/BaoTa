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

import public, os
_title = 'Mysql 弱口令检测'
_version = 1.0  # 版本
_ps = "Mysql 弱口令检测"  # 描述
_level = 3  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-8-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_mysql_pass.pl")
_tips = [
    "在面板数据库-MySQL，修改存在弱口令数据库的密码"
]
_help = ''
_remind = '此方案增加数据库密码强度，降低被爆破成功的风险。'


def check_run():
    '''
        @name Mysql 弱口令检测
        @time 2022-08-12
        @author lkq@bt.cn
    '''
    if not os.path.exists("/www/server/panel/config/weak_pass.txt"):
        return True, '无风险'
    pass_info = public.ReadFile("/www/server/panel/config/weak_pass.txt")
    pass_list = pass_info.split('\n')
    data=public.M("databases").select()
    ret=""
    for i in data:
        if i['password'] in pass_list:
            ret+="数据库："+i['name']+" 存在弱口密码："+short_passwd(i['password'])+"<br/>"
    if ret:
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

