#!/usr/bin/python
# coding: utf-8

import os, sys, re, public


_title = '设置关键文件底层属性'
_version = 1.0  # 版本
_ps = "检查关键文件的底层属性是否配置"  # 描述
_level = 0  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_file_lock.pl")
_tips = [
    "给系统日志文件【/var/log/messages】添加只可追加属性chattr +a",
    "给关键文件【/etc/passwd /etc/shadow /etc/group /etc/gshadow】添加锁属性chattr +i"
]
_help = ''


def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    result_list = []
    result_str1 = public.ExecShell('lsattr -l /var/log/messages*')[0].strip()
    tmp_list1 = result_str1.split('\n')
    # 执行lsattr -l查看文件特殊属性，若存在特殊属性，则判断是否为“追加属性”，若为否，则加入到result_list，最终显示到面板中
    for tl1 in tmp_list1:
        if not "Append_Only" in tl1:
            log1 = re.search('.*?\s', tl1)
            result_list.append(log1.group().strip())
    result_str2 = public.ExecShell('lsattr -l /etc/passwd /etc/shadow /etc/group /etc/gshadow')[0].strip()
    tmp_list2 = result_str2.split('\n')
    # immutable判断是否为锁属性
    for tl2 in tmp_list2:
        if not "Immutable" in tl2:
            log2 = re.search('.*?\s', tl2)
            result_list.append(log2.group().strip())
    if result_list:
        return False, '以下文件未配置适当的底层属性：{}'.format('、'.join(result_list))
    else:
        return True, '无风险'

