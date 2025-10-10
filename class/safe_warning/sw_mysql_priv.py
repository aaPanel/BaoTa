#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: linxiao
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# 数据库备份权限检测
# -------------------------------------------------------------------

import os, re, public, panelMysql

_title = '数据库备份权限检测'
_version = 1.0  # 版本
_ps = "检测MySQL root用户是否具备数据库备份权限"  # 描述
_level = 0  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-09-19'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_mysql_priv.pl")
_tips = [
    "登录Mysql执行【SHOW GRANTS FOR root;】查看root权限情况",
    "【GRANT ALL PRIVILEGES ON *.* TO 'root'@'localhost' WITH GRANT OPTION;】授予root用户所有权限/或是根据需求授予部分权限",
    "【FLUSH PRIVILEGES;】刷新MySQL用户权限，并再次查看root权限情况"
]

_help = ''
_remind = '此方案保障了root用户备份数据库的权限，确保数据库备份工作的进行。'


def check_run():
    """检测root用户是否具备数据库备份权限

        @author linxiao<2020-9-18>
        @return (bool, msg)
    """
    # 获取mysql配置
    mysql_port = _get_mysql_port()
    if not mysql_port:
        return True, '无风险'
    # mycnf_file = '/etc/my.cnf'
    # if not os.path.exists(mycnf_file):
    #     return True, '无风险'
    # mycnf = public.readFile(mycnf_file)
    # port_tmp = re.findall(r"port\s*=\s*(\d+)", mycnf)
    # if not port_tmp:
    #     return True, '无风险'

    # 检查mysql是否运行
    if not _is_mysql_running():
        return True, '无风险'
    # if not public.ExecShell("lsof -i :{}".format(port_tmp[0]))[0]:
    # return True, '无风险'

    # 检查备份权限
    base_backup_privs = ["Lock_tables_priv", "Select_priv"]
    select_sql = "Select {} FROM mysql.user WHERE user='root' and " \
                 "host=SUBSTRING_INDEX((select current_user()),'@', " \
                 "-1);".format(",".join(base_backup_privs))
    # 执行查询
    select_result = panelMysql.panelMysql().query(select_sql)
    if not select_result:
        return False, "root用户执行mysqldump备份的权限不足。"
    select_result = select_result[0]
    for priv in select_result:
        if priv.lower() != "y":
            return False, "root用户执行mysqldump备份的权限不足。"
    return True, '无风险'


def _is_mysql_running():
    """检查MySQL是否运行"""
    try:
        # 1. 首先通过进程检查（最快）
        if public.ExecShell("ps aux | grep mysqld | grep -v grep")[0]:
            return True

        # 2. 通过服务状态检查
        if public.ExecShell("systemctl status mysql")[0]:
            return True

        # 3. 如果上述方法都未确认，则检查端口
        config_files = [
            '/etc/my.cnf',
            '/etc/mysql/my.cnf',
            '/www/server/mysql/my.cnf'
        ]

        for conf_file in config_files:
            if os.path.exists(conf_file):
                mycnf = public.readFile(conf_file)
                if mycnf:
                    port_match = re.findall(r"port\s*=\s*(\d+)", mycnf)
                    if port_match and public.ExecShell("lsof -i :{}".format(port_match[0]))[0]:
                        return True

        return False

    except Exception as e:
        return False


def _get_mysql_port():
    """获取MySQL端口"""
    try:
        # 检查多个配置文件位置
        for conf_file in ['/etc/my.cnf', '/etc/mysql/my.cnf', '/www/server/mysql/my.cnf']:
            if os.path.exists(conf_file):
                mycnf = public.readFile(conf_file)
                if mycnf:
                    port_match = re.findall(r"port\s*=\s*(\d+)", mycnf)
                    if port_match:
                        return port_match[0]
        return None
    except Exception as e:
        return None