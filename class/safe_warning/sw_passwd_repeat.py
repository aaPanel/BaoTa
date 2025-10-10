#!/usr/bin/python
#coding: utf-8

import os, re, public


_title = '检查密码重复使用次数限制'
_version = 1.0  # 版本
_ps = "检测是否限制密码重复使用次数"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_passwd_repeat.pl")
_tips = [
    "配置文件备份cp -p /etc/pam.d/system-auth /etc/pam.d/system-auth.bak",
    "在【/etc/pam.d/system-auth】文件【password sufficient】后面添加或修改remember=3"
]
_help = ''
_remind = '此方案通过限制登录密码重复使用次数，加强服务器访问控制保护。'

def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    try:
        cfile = '/etc/pam.d/system-auth'
        conf = public.readFile(cfile)
        rep1 = r"password(\s*)sufficient(\s*)pam_unix.so"
        if re.search(rep1, conf):
            rep = "password\s*sufficient\s*pam_unix.so.*remember\s*=\s*[1-9]+"
            tmp = re.search(rep, conf)
            if tmp:
                return True, '无风险'
            else:
                return False, '未限制密码重复使用次数'
    except:
        return True, '无风险'
    return True, '无风险'

