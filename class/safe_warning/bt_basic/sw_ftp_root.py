#!/usr/bin/python
# coding: utf-8

import re, os, public

_title = '禁止root用户登录FTP'
_version = 1.0  # 版本
_ps = "禁止root用户登录FTP检查"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-3-15'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ftp_root.pl")
_tips = [
    "在【/www/server/pure-ftpd/etc/pure-ftpd.conf】配置文件中修改MinUID的值为100",
]
_help = ''
_remind = '此方案可以增强对FTP服务器的防护。配置后无法使用root用户登录ftp，谨慎使用。'


def check_run():
    if os.path.exists('/www/server/pure-ftpd/etc/pure-ftpd.conf'):
        try:
            info_data = public.ReadFile('/www/server/pure-ftpd/etc/pure-ftpd.conf')
            if info_data:
                tmp = re.search('\nMinUID\\s*([0-9]{1,4})', info_data)
                if tmp:
                    if int(tmp.group(1).strip()) < 100:
                        return False, '当前pure-ftpd未配置安全访问，在【pure-ftpd.conf】文件中修改/添加MinUID的值为100'
                    else:
                        return True, '无风险'
                else:
                    return False, '当前pure-ftpd未配置安全访问，在【pure-ftpd.conf】文件中修改/添加MinUID的值为100'
        except:
            return True, '无风险'
    return True, '无风险'
