#!/usr/bin/python
# coding: utf-8
# Date 2022/1/12

import sys,os

_title = '系统后门用户检测'
_version = 1.0  # 版本
_ps = "系统后门用户检测"  # 描述
_level = 3  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2021-01-12'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_system_user.pl")
_tips = [
    "在命令行中删除后门用户",
    "注意：如果存在后门用户说明你服务器已经被入侵"
]
_help = ''

def check_run():
    '''
        @name 开始检测
        @author lkq<2021-01-12>
        @return tuple (status<bool>,msg<string>)
    '''
    ret=[]
    cfile = '/etc/passwd'
    if os.path.exists(cfile):
        f=open(cfile,'r')
        for i in f:
            i=i.strip().split(":")
            if i[2]=='0' and i[3]=='0':
                if i[0]=='root':continue
                ret.append(i[0])
    if ret:
        return False, '存在后门用户%s'%''.join(ret)
    return True, '当前未发现存在后门用户'