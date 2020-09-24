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
# 检测风险用户
# -------------------------------------------------------------------


import os,sys,re,public

_title = 'WAF防火墙检测'
_version = 1.0                              # 版本
_ps = "检测是否安装WAF防火墙"               # 描述
_level = 2                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-05'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_waf_install.pl")
_tips = [
    "建议安装WAF防火墙，如：宝塔Nginx防火墙、宝塔Apache防火墙、Nginx免费防火墙、云锁、安全狗、悬镜等",
    "注意：WAF防火墙只安装一款即可，安装过多的WAF防火墙可能导致您的网站异常，和增加不必要的服务器开销"
    ]

_help = ''


def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-04>
        @return tuple (status<bool>,msg<string>)
    '''

    web_list = [
        '/www/server/nginx/sbin/nginx',
        '/www/server/apache/bin/httpd',
        '/usr/local/lsws/bin'
        ]
    is_install_web = False
    for w in web_list:
        if os.path.exists(w):
            is_install_web = True
            break

    if not is_install_web:
        return True,'无风险'
    
    waf_list = [
        '/www/server/panel/plugin/btwaf/info.json',
        '/www/server/panel/plugin/btwaf_httpd/info.json',
        '/www/server/panel/plugin/free_waf/info.json',
        '/usr/local/yunsuo_agent/uninstall',
        '/etc/safedog',
        '/usr/share/xmirror/scripts/uninstall.sh'
        ]

    for waf in waf_list:
        if os.path.exists(waf):
            return True,'无风险'
        
    return True,'未安装WAF防火墙，服务器网站容易受到攻击，存在安全风险'

    