#!/usr/bin/python
#coding: utf-8

import os, re, public

_title = '是否启用Docker日志审计检查'
_version = 1.0  # 版本
_ps = "是否启用Docker日志审计检查"  # 描述
_level = 0  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-13'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_audit_docker.pl")
_tips = [
    "在【/etc/audit/rules.d/audit.rules】文件中添加-w /usr/bin/docker -k docker",
    "重启auditd进程systemctl restart auditd"
]
_help = ''


def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    audit_path = '/etc/audit/audit.rules'
    if not os.path.exists(audit_path):
        return False, '有风险，未安装auditd审计工具'
    # auditctl -l命令列出当前auditd规则，匹配是否有对docker做审计记录
    result = public.ExecShell('auditctl -l')[0].strip()
    rep = '/usr/bin/docker'
    if re.search(rep, result):
        return True, '无风险'
    else:
        return False, '有风险，未开启docker审计日志'

