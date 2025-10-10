#!/usr/bin/python
#coding: utf-8

import sys,re,os,public

_title = '限制SSH登录后使用图形化界面检查'
_version = 1.0                              # 版本
_ps = "限制SSH登录后使用图形化界面检查"                      # 描述
_level = 0                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-14'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ssh_forward.pl")
_tips = [
    "在【/etc/ssh/sshd_config】中修改X11Forwarding为no",
    ]
_help = ''
_remind = '此方案可以加强SSH登录的安全性，加快SSH连接速度。注意修复方案会关闭X11图形界面转发，若需要使用该服务请不要配置。'

def check_run():
    conf = '/etc/ssh/sshd_config'
    if not os.path.exists(conf):
        return True, '无风险'
    result = public.ReadFile(conf)
    rep = '.*?X11Forwarding\s*?yes'
    tmp = re.search(rep, result)
    if tmp:
        if tmp.group()[0] == '#':
            return True, '无风险'
        else:
            return False, '未关闭SSH图形化转发'
    return True, '无风险'
