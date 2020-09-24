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
# MySQL端口安全检测
# -------------------------------------------------------------------

import os,sys,re,public

_title = 'MySQL端口安全'
_version = 1.0                              # 版本
_ps = "检测当前服务器的MySQL端口是否安全"      # 描述
_level = 2                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-03'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_mysql_port.pl")
_tips = [
    "若非必要，在【安全】页面将MySQL端口的放行删除",
    "通过【系统防火墙】插件修改MySQL端口的放行为限定IP，以增强安全性",
    "使用【Fail2ban防爆破】插件对MySQL服务进行保护"
    ]
_help = ''

def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-03>
        @return tuple (status<bool>,msg<string>)

        @example   
            status, msg = check_run()
            if status:
                print('OK')
            else:
                print('Warning: {}'.format(msg))
        
    '''
    mycnf_file = '/etc/my.cnf'
    if not os.path.exists(mycnf_file):
        return True,'未安装MySQL'
    mycnf = public.readFile(mycnf_file)
    port_tmp = re.findall(r"port\s*=\s*(\d+)",mycnf)
    if not port_tmp:
        return True,'未安装MySQL'
    if not public.ExecShell("lsof -i :{}".format(port_tmp[0]))[0]:
        return True,'未启动MySQL'
    result = public.check_port_stat(int(port_tmp[0]),public.GetClientIp())
    if result == 0:
        return True,'无风险'

    return False,'当前MySQL端口: {}，可被任意服务器访问，这可能导致MySQL被暴力破解，存在安全隐患'.format(port_tmp[0])
    
