#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# 数据库定时备份检测
# -------------------------------------------------------------------


import os, sys, re, public

_title = '数据库定时备份检测'
_version = 1.0  # 版本
_ps = "检测所有数据库是否设置定期备份"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-04'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_database_backup.pl")
_tips = [
    "在【计划任务】页面将未设置备份的数据库设置定期备份，或设置备份所有数据库",
    "提示：未设置数据库定期备份的情况下，一但发生意外导致数据丢失，无处恢复，损失巨大",
]

_help = ''


def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-03>
        @return tuple (status<bool>,msg<string>)
    '''

    if os.path.exists('/www/server/panel/plugin/enterprise_backup'):
        return True, '无风险'

    if public.M('crontab').where('sType=? AND sName=?',
                                 ('database', 'ALL')).count():
        return True, '无风险'

    db_list = public.M('databases').field('name').select()

    not_backups = []
    sql = public.M('crontab')
    for db in db_list:
        if sql.where('sType=? AND sName=?', ('database', db['name'])).count():
            continue
        not_backups.append(db['name'])

    if not_backups:
        return False, '以下数据库未设置定期备份: <br />' + ('<br />'.join(not_backups))
    return True, '无风险'

