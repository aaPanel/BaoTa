#!/usr/bin/python
# coding: utf-8

import os, re, public


_title = '检查别名配置'
_version = 1.0  # 版本
_ps = "检查ls和rm命令是否设置别名"  # 描述
_level = 1  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_alias_ls_rm.pl")
_tips = [
    "在文件【~/.bashrc】中添加或修改alias ls=\'ls -alh\'以及alias rm=\'rm -i\'",
    "执行【source ~/.bashrc】使配置生效",
]
_help = ''
_remind = '此方案可以让ls命令列出更详细的文件信息以及降低rm命令误删文件的风险，但可能会影响原来的操作习惯'


def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    # 存放配置不当的命令，分别用正则判断是否配置别名
    result_list = []
    cfile = '/root/.bashrc'
    if not os.path.exists(cfile):
        return True, '无风险'
    conf = public.readFile(cfile)
    # rep1 = 'alias(\s*)ls(\s*)=(\s*)[\'\"]ls(\s*)-.*[alh].*[alh].*[alh]'
    # tmp1 = re.search(rep1, conf)
    # if not tmp1:
    #     result_list.append('ls')
    rep2 = 'alias(\s*)rm(\s*)=(\s*)[\'\"]rm(\s*)-.*[i?].*'
    tmp2 = re.search(rep2, conf)
    if not tmp2:
        result_list.append('rm')
    if len(result_list) > 0:
        return False, '{}命令未配置别名或配置不当'.format('、'.join(result_list))
    else:
        return True, '无风险'
