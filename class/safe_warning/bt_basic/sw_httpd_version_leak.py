#!/usr/bin/python
# coding: utf-8


import re, os, public
_title = 'Apache 版本泄露'
_version = 1.0  # 版本
_ps = "Apache 版本泄露检查"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-14'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_httpd_version_leak.pl")
_tips = [
    "在【httpd.conf】文件中添加ServerSignature Off以及ServerTokens Prod",
]
_help = ''
_remind = '此方案可以增强对服务器的防护，降低网站被入侵的风险。'


def check_run():
    '''
        @name
        @author
        @return tuple (status<bool>,msg<string>)
    '''

    if os.path.exists('/www/server/apache/conf/httpd.conf'):
        try:
            info_data = public.ReadFile('/www/server/apache/conf/httpd.conf')
            if info_data:
                if not re.search('ServerSignature', info_data) and not re.search('ServerTokens',
                                                                                 info_data):
                    return True, '无风险'
                if re.search('ServerSignature Off', info_data) and re.search('ServerTokens Prod',
                                                                             info_data):
                    return True, '无风险'
                else:
                    return False, '当前Apache存在版本泄露问题，请在【httpd.conf】文件中添加ServerSignature Off以及ServerTokens Prod'
        except:
            return True, '无风险'
    return True, '无风险'
