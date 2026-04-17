#!/usr/bin/python
#coding: utf-8

import os, re, public


_title = '是否使用加密的远程管理ssh'
_version = 1.0  # 版本
_ps = "检测是否使用安全的套接字层加密传输信息，避免被侦听敏感信息"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-09'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ssh_v2.pl")
_tips = [
    "在【/etc/ssh/sshd_config】文件中添加或修改Protocol 2",
    "随后执行命令systemctl restart sshd重启进程",
]
_help = ''
_remind = '此方案可以增强对SSH通信的保护，避免敏感数据泄露。'


def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    cfile = '/etc/ssh/sshd_config'
    conf = public.readFile(cfile)
    rep = r"\nProtocol 2"
    tmp = re.search(rep, conf)
    if tmp:
        return True, '无风险'
    else:
        return False, '未使用安全套接字加密远程管理ssh'
