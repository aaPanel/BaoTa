#!/usr/bin/python
# coding: utf-8

import os, sys, public

_title = '检查是否存在空密码用户'
_version = 1.0  # 版本
_ps = "检查是否存在空密码用户"  # 描述
_level = 3  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-11-21'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_empty_passwd_user.pl")
_tips = [
    "使用root登录服务器，给空密码用户设置密码",
    "若不清楚用户的用处可以执行命令【passwd -l (用户名)】暂时封锁用户",
    "解锁用户命令【passwd -fu (用户名)】"
]
_help = ''
_remind = '检测到存在空白密码的用户，可能是黑客保留的后门用户，若非业务需求建议设置密码。'


def check_run():
    '''
        @name 开始检测
        @author lwh<2023-11-21>
        @return tuple (status<bool>,msg<string>)
    '''
    user_list = []
    try:
        output, err = public.ExecShell('awk -F: \'NF && $2 == "" {print}\' /etc/shadow')
        if err == '' and output != '':
            output_list = output.strip().split('\n')
            for op in output_list:
                user_list.append(op.split(':')[0])
        if len(user_list) > 0:
            return False, '发现空密码用户【{}】'.format('、'.join(user_list))
    except:
        return True, '无风险'
    return True, '无风险'
