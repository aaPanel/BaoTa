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
# Memcached安全检测
# -------------------------------------------------------------------

import os,sys,re,public

_title = 'Memcached安全'
_version = 1.0                              # 版本
_ps = "检测当前Memcached是否安全"             # 描述
_level = 2                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-04'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_memcached_port.pl")
_tips = [
    "若非必要，请勿将Memcached的bindIP配置为0.0.0.0",
    "若bindIP为0.0.0.0的情况下，请务必通过【系统防火墙】或【安全组】设置访问IP限制"
    ]
_help = ''

def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-03>
        @return tuple (status<bool>,msg<string>)
    '''

    p_file = '/etc/init.d/memcached'
    p_body = public.readFile(p_file)
    if not p_body: return True,'无风险'

    tmp = re.findall(r"^\s*IP=(0\.0\.0\.0)",p_body,re.M)
    if not tmp: return True,'无风险'
    
    tmp = re.findall(r"^\s*PORT=(\d+)",p_body,re.M)

    result = public.check_port_stat(int(tmp[0]),public.GetClientIp())
    if result == 0:
        return True,'无风险'
    
    return False,'当前Memcached端口：{}, 允许任意客户端访问，这可能导致数据泄露'.format(tmp[0])
    
