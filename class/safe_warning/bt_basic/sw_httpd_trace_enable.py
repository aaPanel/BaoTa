#!/usr/bin/python
# coding: utf-8


import re, os, public
_title = 'Apache TRACE请求检查'
_version = 1.0  # 版本
_ps = "Apache TRACE请求检查"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-11-21'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_httpd_trace_enable.pl")
_tips = [
    "在【httpd.conf】文件中设置TraceEnable off，并重启Apache服务",
    "或者使用一键修复处理安全风险"
]
_help = ''
_remind = 'TRACE请求一般用于测试HTTP协议，攻击者可能会利用TRACE请求结合其他漏洞进行跨站脚本攻击，获取敏感信息，建议修复。'


def check_run():
    '''
        @name
        @author lwh<2023-11-22>
        @return tuple (status<bool>,msg<string>)
    '''

    if os.path.exists('/www/server/apache/conf/httpd.conf'):
        try:
            info_data = public.ReadFile('/www/server/apache/conf/httpd.conf')
            if info_data:
                if not re.search('TraceEnable off', info_data):
                    return False, '当前Apache未关闭TRACE请求，请在【httpd.conf】文件中设置TraceEnable off'
        except:
            return True, '无风险'
    return True, '无风险'
