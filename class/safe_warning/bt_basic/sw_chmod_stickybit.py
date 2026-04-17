#!/usr/bin/python
# coding: utf-8

import os, sys, public
_title = '检查临时目录是否有粘滞位'
_version = 1.0  # 版本
_ps = "检查临时目录是否设置粘滞位权限"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-09'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_chmod_stickybit.pl")
_tips = [
    "使用chmod +t 【文件名】命令修改文件的权限",
]
_help = ''
_remind = '此方案可以防止系统用户误删服务器下的文件。'


def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    # result_list存放未配置粘滞位的目录名
    result_list = []
    tmp_path = ['/var/tmp', '/tmp']
    for tmp in tmp_path:
        file_stat = os.stat(tmp)
        if file_stat.st_mode & 0o1000:
            continue
        else:
            result_list.append(tmp)
    if len(result_list) > 0:
        return False, '以下目录未设置粘滞位权限：{}'.format('、'.join(result_list))
    else:
        return True, '无风险'
    # result_str = public.ExecShell('find {} -maxdepth 0 ! -perm /01000 -type d'.format(' '.join(tmp_path)))[0].strip()
    # public.print_log("粘滞位：{}".format(result_str))
    # if result_str:
    #     result = '、'.join(result_str.split('\n'))
    #     return False, '以下目录未设置粘滞位权限：{}'.format(result)
    # else:
    #     return True, '无风险'
