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
# SSH安全检测
# -------------------------------------------------------------------


import os,sys,re,public,json

_title = 'SSH端口安全'
_version = 1.0                              # 版本
_ps = "检测当前服务器的SSH端口是否安全"      # 描述
_level = 1                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-08-18'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ssh_port.pl")
_tips = [
    "在【安全】页面修改SSH端口，并考虑在【SSH安全管理】中关闭【SSH密码登录】，开启【SSH密钥登录】",
    "若不需要SSH连接服务，建议在【安全】页面关闭SSH服务",
    "通过【系统防火墙】插件或在【安全组】修改SSH端口的放行为限定IP，以增强安全性",
    "使用【Fail2ban防爆破】插件对SSH服务进行保护"
    ]

_help = ''
_remind = '此方案通过修改SSH登录的默认端口，降低被爆破的风险。注意修复之后，需要同步修改相关业务登录SSH的端口。'


def check_run():
    '''
        @name 开始检测
        @author hwliang<2022-08-18>
        @return tuple (status<bool>,msg<string>)

        @example
            status, msg = check_run()
            if status:
                print('OK')
            else:
                print('Warning: {}'.format(msg))

    '''
    port = public.get_sshd_port()

    version = public.readFile('/etc/redhat-release')
    if not version:
        version = public.readFile('/etc/issue').strip().split("\n")[0].replace('\\n','').replace('\l','').strip()
    else:
        version = version.replace('release ','').replace('Linux','').replace('(Core)','').strip()

    status = public.get_sshd_status()

    fail2ban_file = '/www/server/panel/plugin/fail2ban/config.json'
    if os.path.exists(fail2ban_file):
        try:
            fail2ban_config = json.loads(public.readFile(fail2ban_file))
            if 'sshd' in fail2ban_config.keys():
                if fail2ban_config['sshd']['act'] == 'true':
                    return True,'已开启Fail2ban防爆破'
        except: pass

    if not status:
        return True,'未开启SSH服务'
    if port != '22':
        return True,'已修改默认SSH端口'

    result = public.check_port_stat(int(port),public.GetLocalIp())
    if result == 0:
        return True,'无风险'

    return False,'默认SSH端口({})未修改，且未做访问IP限定配置，有SSH暴破风险'.format(port)

