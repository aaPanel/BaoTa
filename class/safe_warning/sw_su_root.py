#!/usr/bin/python
# coding: utf-8

import os, re, public


_title = '检查是否禁用wheel组外的用户su为root'
_version = 1.0  # 版本
_ps = "检查是否使用PAM认证模块禁止wheel组之外的用户su为root"  # 描述
_level = 1  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2024-02-23'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_su_root.pl")
_tips = [
    "在文件【/etc/pam.d/su】中添加auth required pam_wheel.so",
    "如需配置用户可以切换为root，则将用户加入wheel组，使用命令添加wheel组【addgroup wheel】，再执行命令【gpasswd -a [用户] wheel】",
]
_help = ''
_remind = '此方案通过禁止低权限用户切换到root用户，增强对服务器权限的保护。修复前需要确保业务没有切换root的需求，否则忽略此风险项。'


def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    cfile = '/etc/pam.d/su'
    if not os.path.exists(cfile):
        return True, '无风险'
    conf = public.readFile(cfile)
    rep1 = '\n\s*auth\s*sufficient\s*pam_rootok.so'
    tmp1 = re.search(rep1, conf)
    if tmp1:
        rep2 = '\n\s*auth\s*required\s*pam_wheel.so'
        tmp2 = re.search(rep2, conf)
        if tmp2:
            return True, '无风险'
        else:
            return False, '未禁用wheel组外的用户su切换为root用户'
    return False, '未禁用wheel组外的用户su切换为root用户'
