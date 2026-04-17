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
# SSH密码复杂度检查
# -------------------------------------------------------------------
import sys,os
os.chdir('/www/server/panel')
sys.path.append("class/")
import os,sys,re,public

_title = 'SSH密码长度度检查'
_version = 1.0                              # 版本
_ps = "SSH密码长度度检查"                      # 描述
_level = 2                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-08-10'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ssh_security.pl")
_tips = [
    "【/etc/security/pwquality.conf】 文件中把minlen(密码最小长度)设置为9-32位",
    "minlen=9",
    ]
_help = ''
_remind = '此方案会强制登录密码的最低长度，降低服务器被爆破的风险。'


def check_run():
   try:
        p_file = '/etc/security/pwquality.conf'
        p_body = public.readFile(p_file)
        if not p_body: return True, '无风险'
        # 使用负向前瞻过滤注释行，只匹配非注释行
        matches = re.findall(r'^\s*(?!#)\s*minlen\s*=\s*(\S+)', p_body, re.M)
        if not matches: return True, '无风险'
        # 取最后一个匹配的值（与修复方法保持一致）
        minlen_str = matches[-1].strip()
        # 转换为整数进行判断
        try:
            minlen = int(minlen_str)
        except ValueError:
            # 如果转换失败（例如包含非数字字符），跳过此配置
            return True, '无风险'
        if minlen < 9:
            return False, '【%s】文件中把minlen(密码最小长度)设置为9-32位'%p_file

        return True, '无风险'
   except Exception as e:
        return True, '无风险'
