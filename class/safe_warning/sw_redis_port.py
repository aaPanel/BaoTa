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
# Redis安全检测
# -------------------------------------------------------------------

import os,sys,re,public

_title = 'Redis安全检测'
_version = 1.0                              # 版本
_ps = "检测当前Redis是否安全"                 # 描述
_level = 3                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-04'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_redis_port.pl")
_tips = [
    "若非必要，请勿将Redis的bind配置为0.0.0.0",
    "若bind为0.0.0.0的情况下，请务必为Redis设置访问密码",
    "请勿使用过于简单的密码作为Redis访问密码",
    "推荐使用高安全强度的密码：分别包含数字、大小写、特殊字符混合，且长度不少于7位。",
    "Redis一但出现安全问题，这将大概率导致服务器被入侵，请务必认真处理"
    ]
_help = ''


def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-03>
        @return tuple (status<bool>,msg<string>)
    '''

    p_file = '/www/server/redis/redis.conf'
    p_body = public.readFile(p_file)
    if not p_body: return True,'无风险'

    tmp = re.findall(r"^\s*bind\s+(0\.0\.0\.0)",p_body,re.M)
    if not tmp: return True,'无风险'

    tmp = re.findall(r"^\s*requirepass\s+(.+)",p_body,re.M)
    if not tmp: return False,'Reids允许外网连接，但未设置Redis密码，极度危险，请立即处理'

    redis_pass = tmp[0].strip()
    if not is_strong_password(redis_pass):
        return False, 'Redis访问密码过于简单，存在安全隐患'
    
    return True,'无风险'


def is_strong_password(password):
    """判断密码复杂度是否安全

    非弱口令标准：长度大于等于7，分别包含数字、小写、大写、特殊字符。
    @password: 密码文本
    @return: True/False
    """

    if len(password) < 7:
        return False

    import re
    digit_reg = "[0-9]"  # 匹配数字 +1
    lower_case_letters_reg = "[a-z]"  # 匹配小写字母 +1
    upper_case_letters_reg = "[A-Z]"  # 匹配大写字母 +1
    special_characters_reg = r"((?=[\x21-\x7e]+)[^A-Za-z0-9])"  # 匹配特殊字符 +1

    regs = [digit_reg,
            lower_case_letters_reg,
            upper_case_letters_reg,
            special_characters_reg]

    grade = 0
    for reg in regs:
        if re.search(reg, password):
            grade += 1

    if grade == 4 or (grade >= 2 and len(password) >= 9):
        return True
    return False
