#!/usr/bin/python
#coding: utf-8

import os, re, public


_title = '检查账户认证失败次数限制'
_version = 1.0  # 版本
_ps = "检测是否限制账户认证失败的次数"  # 描述
_level = 0  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-20'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_login_fail_limit.pl")
_tips = [
    "在【/etc/pam.d/sshd】文件第二行添加或修改",
    "auth required pam_tally2.so onerr=fail deny=5 unlock_time=300 even_deny_root root_unlock_time=300"
]
_help = ''
_remind = '此方案可以降低服务器被爆破的风险。但务必要记住登录密码，防止登录失败过多导致账户被锁定5分钟。'


def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    cfile = '/etc/pam.d/sshd'
    if not os.path.exists(cfile):
        return True, '无风险'
    conf = public.readFile(cfile)
    rep = r".*auth(\s*)required(\s*)pam_tally[2]?\.so.*deny(\s*)=.*unlock_time(\s*)=.*even_deny_root.*root_unlock_time(\s*)="
    tmp = re.search(rep, conf)
    if tmp:
        if tmp.group()[0] == '#':
            return False, '未配置认证失败次数限制或配置不当'
        return True, '无风险'
    else:
        return False, '未配置认证失败次数限制或配置不当'

