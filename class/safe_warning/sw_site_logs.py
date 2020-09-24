#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# 网站日志检测
# -------------------------------------------------------------------


import os,sys,re,public

_title = '网站日志检测'
_version = 1.0                              # 版本
_ps = "检测所有网站日志保存周期是否合规"          # 描述
_level = 2                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-04'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_site_logs.pl")
_tips = [
    "在【计划任务】页面将指定网站或全部网站的日志切割设置每天1次，保存180份以上",
    "提示：根据网络安全法第二十一条规定，网络日志应留存不少于六个月"
    ]

_help = ''


def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-03>
        @return tuple (status<bool>,msg<string>)        
    '''

    if public.M('crontab').where('sType=? AND sName=? AND save>=?',('logs','ALL',180)).count():
        return True,'无风险'

    log_list = public.M('crontab').where('sType=? AND save<?',('logs',180)).field('sName').select()

    not_logs = []
    for ml in log_list:
        if ml['sName'] in not_logs: continue
        not_logs.append(ml['sName'])

    #如果有设置切割所有网站日志,且设置不合规
    if 'ALL' in not_logs:
        log_list = public.M('crontab').where('sType=? AND save>=?',('logs',180)).field('sName').select()
        ok_logs = []
        for ml in log_list:
            if ml['sName'] in ok_logs: continue
            ok_logs.append(ml['sName'])

        not_logs = []
        site_list = public.M('sites').field('name').select()
        for s in site_list:
            if s['name'] in ok_logs: continue
            if s['name'] in not_logs: continue
            not_logs.append(s['name'])

    if not_logs:
        return False ,'以下网站日志保存周期不合规: <br />' + ('<br />'.join(not_logs))
    
    return True,'无风险'
    

