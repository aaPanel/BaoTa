#!/usr/bin/python
#coding: utf-8

import os, public, re

_title = 'CVE-2019-5736容器逃逸漏洞检测'
_version = 1.0  # 版本
_ps = "检测CVE-2019-5736容器逃逸漏洞"  # 描述
_level = 0  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-27'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_cve_2019_5736.pl")
_tips = [
    "docker version查看docker版本是否小于18.09.2，runc版本小于1.0-rc6",
    "升级docker版本"
]
_help = ''
_remind = '黑客可通过此漏洞夺取服务器权限。'

# https://nvd.nist.gov/vuln/detail/CVE-2019-5736#match-7231264
def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    docker = public.ExecShell("docker version --format=\'{{ .Server.Version }}\'")[0].strip()
    if 'command not found' in docker or '未找到命令' in docker:
        return True, '无风险，未安装docker'
    if not re.search('\d+.\d+.\d+', docker):
        return True, '无风险'
    docker = docker.split('.')
    if len(docker[0]) < 2:
        return False, '有风险，当前docker版本存在安全风险，需升级到安全版本'
    elif int(docker[0]) < 18:
        return False, '有风险，当前docker版本存在安全风险，需升级到安全版本'
    elif int(docker[0]) == 18:
        if int(docker[1]) < 9:
            return False, '有风险，当前docker版本存在安全风险，需升级到安全版本'
        elif int(docker[1]) == 9:
            if int(docker[2][0]) < 2:
                return False, '有风险，当前docker版本存在安全风险，需升级到安全版本'
            else:
                return True, '无风险'
        else:
            return True, '无风险'
    else:
        return True, '无风险'
