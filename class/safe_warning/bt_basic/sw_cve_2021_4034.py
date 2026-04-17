#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: lkq <lkq@bt.cn>
# -------------------------------------------------------------------
# Time: 2022-08-10
# -------------------------------------------------------------------
# CVE-2021-4034 polkit pkexec 本地提权漏洞检测
# -------------------------------------------------------------------
# import sys, os
# os.chdir('/www/server/panel')
# sys.path.append("class/")
import json
import public, os, stat
_title = 'CVE-2021-4034 polkit pkexec 本地提权漏洞检测'
_version = 1.0  # 版本
_ps = "CVE-2021-4034 polkit pkexec 本地提权漏洞检测"  # 描述
_level = 3  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-08-04'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_cve_2021_4034.pl")
_tips = [
    "更新polkit 组件,CentOS可通过执行命令【yum update polkit】升级修复"
]
_help = ''
_remind = '升级软件版本存在风险，强烈建议服务器先做快照备份，以防操作失败能及时恢复！'


def check_run():
    '''
        @name CVE-2021-4034 polkit pkexec 本地提权漏洞检测
        @time 2022-08-12
        @author lkq@bt.cn
    '''
    if not os.path.exists('/usr/bin/pkexec'):
        return True, '无风险'
    st = os.stat('/usr/bin/pkexec')
    setuid, setgid = bool(st.st_mode & stat.S_ISUID), bool(st.st_mode & stat.S_ISGID)
    if not setuid: return True, '无风险'
    redhat_file = '/etc/redhat-release'
    if os.path.exists(redhat_file):
        version = ""
        # 从漏洞扫描获取版本缓存
        product_json = "/www/server/panel/data/warning/product_version.json"
        if os.path.exists(product_json):
            try:
                product = json.loads(public.ReadFile(product_json))
                if "polkit" in product:
                    version = product["polkit"]
            except Exception as e:
                version = ""
                # public.print_log("报错了：{}".format(e))
        data=public.ReadFile(redhat_file)
        if not version:
            version = get_polkit_version()
        if not version: return True, '无风险'
        if not data:return True, '无风险'
        if data.find('CentOS Linux release 7.') != -1:
            # polkit=public.ExecShell("rpm -q polkit-0.*")
            # polkit_list = polkit[0].strip()
            if version.find('polkit-0') == -1:return True, '无风险'
            p = version.split(".")
            if len(p)<2:return True, '无风险'
            if p[1] == '112-26':return True,'无风险'
            p2=p[1].split("-")
            if int(p2[1]) <26:
                return False, '请更新polkit'
            return True,'无风险'
        #CentOS 8.0
        elif data.find('CentOS Linux release 8.0') == 0:
            polkit = public.ExecShell("rpm -q polkit-0.*")
            if version.find('polkit-0') == -1: return True, '无风险'
            # Centos 7
            p = version.split(".")
            if len(p) < 2: return True, '无风险'
            if p[1] == '115-13': return True, '无风险'
            p2 = p[1].split("-")
            if int(p2[1]) < 13:
                return False, 'centos8已停止维护，请先升级系统至8stream，再更新polkit'
            return True, '无风险'
        elif data.find("CentOS Linux release 8.2") == 0:
            if version.find('polkit-0') == -1: return True, '无风险'
            # Centos 7
            p = version.split(".")
            if len(p) < 2: return True, '无风险'
            if p[1] == '115-11': return True, '无风险'
            p2 = p[1].split("-")
            if int(p2[1]) < 11:
                return False, 'centos8已停止维护，请先升级系统至8stream，再更新polkit'
            return True, '无风险'
        elif data.find("CentOS Linux release 8.5") == 0:
            if version.find('polkit-0.115-12') ==0:
                return False, 'centos8已停止维护，请先升级系统至8stream，再更新polkit'
            return True, '无风险'
    return True, '无风险'


def get_polkit_version():
    """
    @name 获取polkit版本(centos)
    @author lwh<2024-02-28>
    @return bool, string
    """
    polkit = public.ExecShell("rpm -q polkit-0.*")
    if not polkit[0]: return False
    return polkit.strip()

