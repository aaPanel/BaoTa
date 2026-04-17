#!/usr/bin/python
# coding: utf-8

import os, sys, public
import re

_title = '检查是否允许空密码sudo提权'
_version = 1.0  # 版本
_ps = "检查是否允许空密码sudo提权"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-11-21'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_sudoers_nopasswd.pl")
_tips = [
    "打开/etc/sudoers或是/etc/sudoers.d下的文件",
    "删除或注释【NOPASSWD】标记所在行",
    "或者使用一键修复处理安全风险"
]
_help = ''
_remind = '当sudo使用【NOPASSWD】标记时，允许用户使用sudo执行命令，而无需进行身份验证。这种不安全的配置可能导致黑客夺取服务器的高级权限。'


def check_run():
    '''
        @name 开始检测
        @author lwh<2023-11-21>
        @return tuple (status<bool>,msg<string>)
    '''
    risk_list = []
    sudo_file = "/etc/sudoers"
    sudo_dir = "/etc/sudoers.d/"
    if not os.path.exists(sudo_file):
        return True, '无风险'
    if detect_passwd(sudo_file):
        risk_list.append(sudo_file)
    if os.path.exists(sudo_dir):
        for path in os.listdir(sudo_dir):
            item_path = os.path.join(sudo_dir, path)
            if os.path.isfile(item_path):
                if detect_passwd(item_path):
                    risk_list.append(item_path)
    if len(risk_list) > 0:
        return False, '以下sudo文件存在NOPASSWD标记：<br/>{}'.format('<br/>'.join(risk_list))
    return True, '无风险'
    # risk_list = []
    # try:
    #     output, err = public.ExecShell('grep -P \'^(?!#).*[\s]+NOPASSWD[\s]*\:.*$\' {}'.format(sudo_file))
    #     if err == '' and output != '':
    #         risk_list.append(sudo_file)
    #     if os.path.exists(sudo_dir):
    #         import glob
    #         for filename in glob.glob(os.path.join(sudo_dir, '*')):
    #             output, err = public.ExecShell('grep -P \'^(?!#).*[\s]+NOPASSWD[\s]*\:.*$\' {}'.format(filename))
    #             if err == '' and output != '':
    #                 risk_list.append(filename)
    #     if len(risk_list)>0:
    #         return False, '以下sudo文件存在NOPASSWD标记：{}'.format('<br/>'.join(risk_list))
    # except:
    #     return True, '无风险'
    # return True, '无风险'


def detect_passwd(file):
    """
    @name 检查文件内容是否存在NOPASSWD
    @author lwh<2024-02-29>
    """
    data = public.ReadFile(file)
    for d in data.split("\n"):
        if d.startswith("#"):
            continue
        if re.search("\s+NOPASSWD:.*", d):
            return True
    return False
