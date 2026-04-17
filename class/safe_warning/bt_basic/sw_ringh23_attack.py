#!/usr/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: wpl <2026-03-04>
# +-------------------------------------------------------------------

# RingH23攻击套件检测
# +-------------------------------------------------------------------

import os
import sys
import re
import glob

_title = '检测服务器是否被RingH23攻击套件感染'
_version = 1.0
_ps = '检测/var/adm/目录、ld.so.preload、udev规则等RingH23攻击特征'
_level = 3
_date = '2026-03-04'
_ignore = os.path.exists('/www/server/panel/data/warning/ignore/sw_ringh23_attack.pl')
_tips = [
    '使用 export RING04H={uuid} 禁用Rootkit隐藏功能',
    '删除 /etc/ld.so.preload 中的恶意模块路径/var/adm/',
    '删除 /var/adm/{uuid} 目录下的所有文件',
    '删除 /etc/udev/rules.d/99-{uuid}.rules 规则文件'
]

# 帮助信息
_help = ''

# 修复提醒
_remind = 'RingH23攻击套件可能导致网站被植入恶意代码'


def check_run():
    '''
        @name RingH23攻击套件检测
        @return tuple (status<bool>,msg<string>)
    '''
    risk_items = []

    # ==== 检测点1: 检查 /var/adm/ 目录 ====
    if os.path.exists('/var/adm/'):
        try:
            for item in os.listdir('/var/adm/'):
                # 匹配UUID格式: 32位16进制 或 带横线的标准UUID
                if re.match(r'^[a-f0-9]{32}$', item) or \
                   re.match(r'^[a-f0-9-]{36}$', item):
                    risk_items.append('/var/adm/{}'.format(item))
        except:
            pass

    # ==== 检测点2: 检查 ld.so.preload ====
    preload_file = '/etc/ld.so.preload'
    if os.path.exists(preload_file):
        try:
            with open(preload_file, 'r') as f:
                content = f.read().strip()
                if content and ('libutilkeybd.so' in content or '/var/adm/' in content):
                    risk_items.append('异常预加载模块: {}'.format(content))
        except:
            pass

    # ==== 检测点3: 检查 udev 规则 ====
    udev_path = '/etc/udev/rules.d'
    if os.path.exists(udev_path):
        try:
            for f in glob.glob('{}/99-*.rules'.format(udev_path)):
                risk_items.append('异常udev规则: {}'.format(f))
        except:
            pass

    # ==== 返回结果 ====
    if risk_items:
        msg = '检测到RingH23攻击特征:<br/>' + '<br/>'.join(risk_items)
        return False, msg

    return True, '未检测到RingH23攻击特征'
