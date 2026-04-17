#!/usr/bin/python
#coding: utf-8

import os, re, public

_title = 'CVE-2022-2068 OpenSSL任意命令执行漏洞检测'
_version = 1.0  # 版本
_ps = "CVE-2022-2068 OpenSSL任意命令执行漏洞检测"  # 描述
_level = 0  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_cve_2022_2068.pl")
_tips = [
    "升级OpenSSL至最新版本或是安全版本",
    "1.0.2zf、1.1.1p、3.0.4及以上版本",
]
_help = ''


def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    # https://nvd.nist.gov/vuln/detail/CVE-2022-2068#range-8768393
    openssl = public.ExecShell("openssl version")[0].strip()
    openssl = openssl.split(' ')[1]
    openssl = openssl.split('.')
    if openssl[0] == '1':
        if openssl[1] == '0' and openssl[2][0] == '2':
            if len(openssl[2]) < 3:
                return False, '当前openssl版本存在安全风险，需更新到安全版本'
            elif not openssl[2][1].islower():
                return False, '当前openssl版本存在安全风险，需更新到安全版本'
            elif openssl[2][1] < 'z':
                return False, '当前openssl版本存在安全风险，需更新到安全版本'
            elif openssl[2][1] == 'z' and openssl[2][2] < 'f':
                return False, '当前openssl版本存在安全风险，需更新到安全版本'
            else:
                return True, '无风险'
        elif openssl[1] == '1' and openssl[2][0] == '1':
            if len(openssl[2]) < 2:
                return False, '当前openssl版本存在安全风险，需更新到安全版本'
            elif not openssl[2][1].islower():
                return False, '当前openssl版本存在安全风险，需更新到安全版本'
            elif openssl[2][1] < 'p':
                return False, '当前openssl版本存在安全风险，需更新到安全版本'
            else:
                return True, '无风险'
    elif openssl[0] == '3' and openssl[1] == '0':
        if openssl[2][0] < '4':
            return False, '当前openssl版本存在安全风险，需更新到安全版本'
        else:
            return True, '无风险'
    else:
        return True, '无风险'
