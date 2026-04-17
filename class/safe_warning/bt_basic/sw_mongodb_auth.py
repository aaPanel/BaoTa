#!/usr/bin/python
#coding: utf-8

import os, re, public

_title = 'MongoDB是否开启安全认证'
_version = 1.0  # 版本
_ps = "检查MongoDB是否开启安全认证"  # 描述
_level = 3  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-09'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_mongodb_auth.pl")
_tips = [
    "在面板数据库MongoDB中打开安全认证开关",
]
_help = ''
_remind = '此方案可以加强对数据库的保护，防止黑客通过mongo数据库盗取数据。'


def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    cfile = '{}/mongodb/config.conf'.format(public.get_setup_path())
    if not os.path.exists(cfile):
        return True, '无风险，未安装mongodb'
    if not public.process_exists("mongod"):
        return True, '无风险，MongoDB服务还未开启！'
    conf = public.readFile(cfile)
    rep = "\n\s*authorization\s*:\s*enabled"
    tmp = re.search(rep, conf)
    if tmp:
        return True, '无风险'
    else:
        return False, '未开启MongoDB安全认证'

