#!/usr/bin/python
# coding: utf-8

import os, public

_title = '检查是否存在危险远程访问文件'
_version = 1.0  # 版本
_ps = "检查是否存在危险远程访问文件hosts.equiv、.rhosts、.netrc"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-09'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_risk_file.pl")
_tips = [
    "删除在家目录下的.rhosts和.netrc文件以及删除根目录下的hosts.equiv文件",
    "按照提示找到风险文件并删除"
]
_help = ''
_remind = '此方案去除了所有存在风险的文件，防止被黑客利用入侵服务器。删除文件前可以先对文件进行备份，防止出现影响网站运行的情况。'


def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    result_list = []
    root_dir = "/home"
    cfile = ['hosts.equiv', '.rhosts', '.netrc']
    for item in os.listdir(root_dir):
        item_path = os.path.join(root_dir, item)
        if os.path.isdir(item_path):
            for item2 in os.listdir(item_path):
                if item2 in cfile:
                    result_list.append(os.path.join(root_dir, item2))
        else:
            if item in cfile:
                result_list.append(os.path.join(root_dir, item))
    # for cf in cfile:
    #     file = public.ExecShell('find /home -maxdepth 2 -name {}'.format(cf))
    #     if file[0]:
    #         result_list = result_list+file[0].split('\n')
    # result = '、'.join(reform_list(result_list))
    result = '、'.join(result_list)
    if result:
        return False, '存在高风险文件，尽快删除以下文件\"{}\"'.format(result)
    else:
        return True, '无风险'


# def reform_list(check_list):
#     """处理列表里的空字符串"""
#     return [i for i in check_list if (i is not None) and (str(i).strip() != '')]
