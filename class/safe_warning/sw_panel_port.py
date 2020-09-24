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
# 面板端口检测
# -------------------------------------------------------------------

import os,sys,re,public

_title = '面板端口安全'
_version = 1.0                              # 版本
_ps = "检测当前面板端口是否安全"      # 描述
_level = 2                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-03'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_panel_port.pl")
_tips = [
    "请在【设置】页面修改默认面板端口",
    "注意：有【安全组】的服务器应在【安全组】中提前放行新端口，以防新端口无法打开"
    ]
_help = ''

def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-03>
        @return tuple (status<bool>,msg<string>)
    '''

    port_file = '/www/server/panel/data/port.pl'
    port = public.readFile(port_file)
    if not port: return True,'无安全风险'
    port = int(port)
    if port != 8888:
        return True,'无安全风险'
    return False,'面板端口为默认端口({}), 这可能造成不必要的安全风险'.format(port)
    
