#!/usr/bin/python
# coding: utf-8

import os, sys, public

_title = '检查nginx二进制文件是否被篡改'
_version = 1.0  # 版本
_ps = "检查nginx二进制文件是否被篡改"  # 描述
_level = 3  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-11-21'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_nginx_md5.pl")
_tips = [
    "在面板【软件商店】-【运行环境】重新安装Nginx",
    "寻求专业安全团队对服务器进行全面排查，清除后门"
]
_help = ''
_remind = '检测到/www/server/nginx/sbin/nginx执行文件被篡改，网站存在被入侵风险。'


def check_run():
    '''
        @name 开始检测
        @author lwh<2023-11-21>
        @return tuple (status<bool>,msg<string>)
    '''
    nginx_path = '/www/server/nginx/sbin/nginx'
    nginx_md5 = '/www/server/panel/data/nginx_md5.pl'
    if not os.path.exists(nginx_path):
        return True, '无风险'
    try:
        # new_md5 = public.ExecShell('md5sum {}'.format(nginx_path))[0].strip().split(" ")[0]
        new_md5 = public.FileMd5(nginx_path)
        if not new_md5:
            return True, '无风险'
        if os.path.exists(nginx_md5):
            old_md5 = public.ReadFile(nginx_md5).strip().split(" ")[0]
            if new_md5 != old_md5:
                return False, "检测到nginx文件被篡改（MD5：{}）".format(new_md5)
        return True, '无风险'
    except:
        return True, '无风险'
