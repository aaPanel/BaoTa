#!/usr/bin/python
# coding: utf-8

import re, os, public

_title = '禁止匿名登录FTP'
_version = 1.0  # 版本
_ps = "禁止匿名登录FTP检测"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-3-15'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ftp_login.pl")
_tips = [
    "在【/www/server/pure-ftpd/etc/pure-ftpd.conf】配置文件中修改NoAnonymous的值为yes",
]
_help = ''
_remind = '此方案可以增强FTP服务器防护，防止非法入侵服务器。配置后无法使用Anonymous登录FTP服务器。'


def check_run():

    if os.path.exists('/www/server/pure-ftpd/etc/pure-ftpd.conf'):
        try:
            info_data = public.ReadFile('/www/server/pure-ftpd/etc/pure-ftpd.conf')
            if info_data:
                if re.search('\n\s*NoAnonymous\s*yes', info_data):
                    return True, '无风险'
                else:
                    return False, '当前pure-ftpd未禁用匿名登录，在【pure-ftpd.conf】文件中修改/添加NoAnonymous的值为yes'
        except:
            return True, '无风险'
    return True, '无风险'
