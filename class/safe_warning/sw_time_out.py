#!/usr/bin/python
# coding: utf-8

import os, re, public


_title = '检查是否设置命令行界面超时退出'
_version = 1.0  # 版本
_ps = "检查是否设置无操作超时退出"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_time_out.pl")
_tips = [
    "在文件【/etc/profile】中添加tmout=300，等保要求不大于600秒",
    "执行命令source /etc/profile使配置生效",
]
_help = ''
_remind = '此方案会使服务器命令行超过一定时间未操作自动关闭，可以加强服务器安全性。'


def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    cfile = '/etc/profile'
    conf = public.readFile(cfile)
    rep = '(tmout|TMOUT)(\s*)=(\s*)([1-9][^0-9]|[1-9][0-9][^0-9]|[1-5][0-9][0-9][^0-9]|600[^0-9])'
    tmp = re.search(rep, conf)
    if tmp:
        return True, '无风险'
    else:
        return False, '未配置命令行超时退出'
