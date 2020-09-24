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
# 检测网站是否开启防跨站
# -------------------------------------------------------------------


import os,sys,re,public

_title = '网站防跨站检测'
_version = 1.0                              # 版本
_ps = "检测所有网站是否开启防跨站"              # 描述
_level = 1                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-05'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_site_spath.pl")
_tips = [
    "在【网站】页面，【设置】 - 【网站目录】中开启【防跨站攻击(open_basedir)】功能"
    ]

_help = ''


def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-05>
        @return tuple (status<bool>,msg<string>)
    '''
    not_uini = []
    site_list = public.M('sites').where('status=?',(1,)).field('name,path').select()
    for s in site_list:
        path = get_site_run_path(s['name'],s['path'])
        user_ini = path + '/.user.ini'
        if os.path.exists(user_ini): continue
        not_uini.append(s['name'])
    if not_uini:
        return False,'以下网站未开启防跨站功能：<br />' + ('<br />'.join(not_uini))
    return True,'无风险'



webserver_type = None
setupPath = '/www/server'
def get_site_run_path(siteName,sitePath):
    '''
        @name 获取网站运行目录
        @author hwliang<2020-08-05>
        @param siteName(string) 网站名称
        @param sitePath(string) 网站根目录
        @return string
    '''
    global webserver_type,setupPath
    if not webserver_type:
        webserver_type = public.get_webserver()
    path = None
    if webserver_type == 'nginx':
        filename = setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        if os.path.exists(filename):
            conf = public.readFile(filename)
            rep = r'\s*root\s+(.+);'
            tmp1 = re.search(rep,conf)
            if tmp1: path = tmp1.groups()[0]

    elif webserver_type == 'apache':
        filename = setupPath + '/panel/vhost/apache/' + siteName + '.conf'
        if os.path.exists(filename):
            conf = public.readFile(filename)
            rep = r'\s*DocumentRoot\s*"(.+)"\s*\n'
            tmp1 = re.search(rep,conf)
            if tmp1: path = tmp1.groups()[0]
    else:
        filename = setupPath + '/panel/vhost/openlitespeed/' + siteName + '.conf'
        if os.path.exists(filename):
            conf = public.readFile(filename)
            rep = r"vhRoot\s*(.*)"
            path = re.search(rep,conf)
            if not path:
                path = None
            else:
                path = path.groups()[0]

    if not path:
        path = sitePath

    return path