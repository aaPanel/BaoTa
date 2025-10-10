#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: lkq <lkq@bt.cn>
# -------------------------------------------------------------------
# Time: 2022-08-10
# -------------------------------------------------------------------
# SSH过期提前警告天数
# -------------------------------------------------------------------



# import sys, os
# os.chdir('/www/server/panel')
# sys.path.append("class/")
import re,public,os




_title = 'SSH过期提前警告天数'
_version = 1.0                              # 版本
_ps = "SSH过期提前警告天数"          # 描述
_level = 2                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-8-10'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ssh_passwarn.pl")
_tips = [
    "在【/etc/login.defs】 PASS_WARN_AGE 大于等于7",
    "提示：PASS_WARN_AGE 30   同时执行命令使root用户设置生效 chage --warndays 7 root",
    ]

_help = ''
_remind = '此方案是设置密码过期前多少天会告警提醒，防止忘记修改影响服务器内的进程执行。注意此提醒只有在登录服务器后才会提醒，建议在面板的告警通知处设置告警方式。'


def check_run():
    '''
        @name SSH过期提前警告天数
        @time 2022-08-10
        @author lkq<2020-08-10>
        @return tuple (status<bool>,msg<string>)
    '''
    if os.path.exists('/etc/login.defs'):
        try:
            info_data=public.ReadFile('/etc/login.defs')
            if info_data:
                if re.search('PASS_WARN_AGE\s+\d+',info_data):

                    passwarnage=re.findall('PASS_WARN_AGE\s+(\d+)',info_data)[0]
                    #passwarnage 需要大于7 小于14
                    if int(passwarnage) >= 7:
                        return True,'无风险'
                    else:
                        return False,'当前PASS_WARN_AGE为：'+passwarnage+'，请设置为大于等于7'
                else:
                    return True,'无风险'
        except:
            return True,'无风险'
    return True,'无风险'
