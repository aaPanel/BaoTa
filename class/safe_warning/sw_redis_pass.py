#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# Redis 密码检测
# -------------------------------------------------------------------

import os,sys,re,public

_title = 'Redis 密码检测'
_version = 1.0                              # 版本
_ps = "检测当前Redis密码是否安全"                 # 描述
_level = 3                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-08-10'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_redis_pass.pl")
_tips = [
    "1.Redis 密码太过于简单"
    "2.请及时修改密码"
    ]
_help = ''
_remind = '此方案通过加强数据库登录密码强度，降低服务器被入侵的风险。'


def check_run():
    try:
        p_file = '/www/server/redis/redis.conf'
        p_body = public.readFile(p_file)
        if not p_body: return True, '无风险'

        tmp = re.findall(r"^\s*requirepass\s+(.+)", p_body, re.M)
        if not tmp: return True, '无风险'

        redis_pass = tmp[0].strip()
        pass_info=public.ReadFile("/www/server/panel/config/weak_pass.txt")
        if not pass_info: return True, '无风险'
        pass_list = pass_info.split('\n')
        for i in pass_list:
            if i==redis_pass:
                return False, '当前Redis密码【%s】为弱密码，请修改密码'%redis_pass
        return True, '无风险'
    except:
        return True, '无风险'
