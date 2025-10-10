#!/usr/bin/python
# coding: utf-8

import re, os, public
_title = '用户FTP访问安全配置'
_version = 1.0  # 版本
_ps = "用户FTP访问安全配置检查"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-3-15'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ftp_umask.pl")
_tips = [
    "在【/www/server/pure-ftpd/etc/pure-ftpd.conf】在配置文件中修改Umask的值为177:077",
]
_help = ''
_remind = '此方案可以增强对FTP服务器的防护，降低服务器被入侵的风险。'


def check_run():

    if os.path.exists('/www/server/pure-ftpd/etc/pure-ftpd.conf'):
        try:
            info_data = public.ReadFile('/www/server/pure-ftpd/etc/pure-ftpd.conf')
            if info_data:
                if re.search('.*Umask\s*177:077', info_data):
                    return True, '无风险'
                else:
                    return False, '当前pure-ftpd未配置安全访问，在【pure-ftpd.conf】文件中修改/添加Umask的值为177:077'
        except:
            return True, '无风险'
    return True, '无风险'
