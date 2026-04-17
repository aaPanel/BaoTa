#!/usr/bin/python
# coding: utf-8

import os, pkg_resources

_title = 'pypi供应链投毒检测'
_version = 1.0  # 版本
_ps = "pypi供应链投毒检测"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2024-02-27'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_pip_poison.pl")
_tips = [
    "执行命令btpip uninstall 【检测出来的恶意包名】",
]
_help = ''
_remind = '此方案可以删除服务器存在风险的软件包，防止被黑客利用进行入侵。执行方案命令前，确保该恶意库名不是正常业务的依赖库，否则可能会影响网站运行。'


def check_run():
    installed_packages = pkg_resources.working_set
    installed_packages_list = ["%s" % (i.key,) for i in installed_packages]
    evil_list = ["istrib", "djanga", "easyinstall", "junkeldat", "libpeshka", "mumpy", "mybiubiubiu", "nmap",
                 "beautfulsoup", "openvc", "pythonkafka", "selemium", "virtualnv", "mateplotlib", "request",
                 "amazom-selenium", "pilloe", "randam", "arduino", "urllitelib", "urtelib32", "graphql32"]

    result_list = [evil for evil in evil_list if evil in installed_packages_list]

    if len(result_list) > 0:
        return False, 'btpip存在恶意包：<br>{}'.format('、'.join(result_list))
    else:
        return True, '无风险'
