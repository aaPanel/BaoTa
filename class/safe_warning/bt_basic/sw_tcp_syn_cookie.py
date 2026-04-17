#!/usr/bin/python
#coding: utf-8

import os, re, sys, public


_title = 'TCP-SYNcookie保护检测'
_version = 1.0  # 版本
_ps = "检查是否开启TCP-SYNcookie保护缓解syn flood攻击"  # 描述
_level = 1  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-09'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_tcp_syn_cookie.pl")
_tips = [
    "在【/etc/sysctl.conf】文件中添加net.ipv4.tcp_syncookies=1",
    "然后执行命令sysctl -p生效配置",
]
_help = ''
_remind = '此方案可以缓解网络洪水攻击，增强服务器运行的稳定性。'


def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''

    cfile = '/etc/sysctl.conf'
    conf = public.readFile(cfile)
    rep = r"\nnet.ipv4.tcp_syncookies(\s*)=(\s*)1"
    tmp = re.search(rep, conf)
    if tmp:
        return True, '无风险'
    else:
        return False, '未开启TCP-SYNcookie保护'

