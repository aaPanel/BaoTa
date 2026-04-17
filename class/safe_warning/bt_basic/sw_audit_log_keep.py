#!/usr/bin/python
#coding: utf-8

import os, re, public


_title = '审核日志永久保存'
_version = 1.0  # 版本
_ps = "检查审核日志满了后是否自动删除"  # 描述
_level = 0  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-15'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_audit_log_keep.pl")
_tips = [
    "在【/etc/audit/auditd.conf】中max_log_file_action将ROTATE改为KEEP_LOGS",
    "重启auditd服务systemctl restart auditd"
]
_help = ''


def check_run():
    cfile = '/etc/audit/auditd.conf'
    if not os.path.exists(cfile):
        return False, '有风险，未安装auditd审计工具'
    result = public.ReadFile(cfile)
    # 默认是rotate，日志满了后循环日志，keep_logs会保留旧日志
    rep = 'max_log_file_action\s*=\s(.*)'
    tmp = re.search(rep, result)
    if tmp:
        if 'keep_logs'.lower() == tmp.group(1).lower():
            return True, '无风险'
    return False, '当前max_log_file_action值为{}，应当为KEEP_LOGS'.format(tmp.group(1))
