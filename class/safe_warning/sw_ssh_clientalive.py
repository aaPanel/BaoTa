#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: lkq <lkq@bt.cn>
# -------------------------------------------------------------------
# Time: 2022-08-10
# -------------------------------------------------------------------
# SSH 空闲超时时间检测
# -------------------------------------------------------------------
import re,public,os


_title = 'SSH 空闲超时时间检测'
_version = 1.0                              # 版本
_ps = "SSH 空闲超时时间检测"          # 描述
_level = 2                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-8-10'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ssh_clientalive.pl")
_tips = [
    "在【/etc/ssh/sshd_config】文件中设置【ClientAliveInterval】设置为600到900之间",
    "提示：SSH空闲超时时间建议为：600-900"
    ]

_help = ''
_remind = '此方案可以增强SSH服务的安全性，修复后连接SSH长时间无操作会自动退出，防止被他人利用。'


def check_run():
    '''
        @name SSH 空闲超时检测
        @time 2022-08-10
        @author lkq<2020-08-10>
        @return tuple (status<bool>,msg<string>)
    '''
    if os.path.exists('/etc/ssh/sshd_config'):
        try:
            info_data=public.ReadFile('/etc/ssh/sshd_config')
            if info_data:
                if re.search('ClientAliveInterval\s+\d+',info_data):
                    clientalive=re.findall('ClientAliveInterval\s+\d+',info_data)[0]
                    #clientalive 需要大于600 小于900
                    if int(clientalive.split(' ')[1]) >= 600 and int(clientalive.split(' ')[1]) <= 900:
                        return True,'无风险'
                    else:
                        return False,'当前SSH空闲超时时间为：'+clientalive.split(' ')[1]+'，请设置为600-900'
                else:
                    return True,'无风险'
        except:
            return True,'无风险'
    return True,'无风险'

def repaired():
    '''
        @name 修复ssh最大连接数
        @author lkq<2022-08-10>
        @return tuple (status<bool>,msg<string>)
    '''
    # 暂时不处理
    pass
