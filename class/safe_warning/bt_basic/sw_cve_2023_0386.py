#!/usr/bin/python
#coding: utf-8
import os
import public
import re

_title = 'CVE-2023-0386 Linux Kernel OverlayFS 权限提升漏洞漏洞检测'
_version = 1.0  # 版本
_ps = "CVE-2023-0386 Linux Kernel OverlayFS 权限提升漏洞漏洞检测"  # 描述
_level = 3  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-08-04'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_cve_2023_0386.pl")
_tips = [
    "根据提示检查内核版本是否低于指定版本【uname -r】",
    "若是CentOS 8 Stream，则执行【yum install kernel】命令升级内核版本，并重启服务器",
    "若是Ubuntu 22.04，则执行【apt install linux-image】查看可安装版本号，选择高于5.15.0-70的版本号，再次执行【apt install linux-image-版本号】，并重启服务器"
]
_help = ''
_remind = '上述升级内核的操作具有一定风险，强烈建议服务器先做快照备份，以防操作失败能及时恢复！'


# https://nvd.nist.gov/vuln/detail/CVE-2023-0386
def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    # centos8
    if os.path.exists('/etc/redhat-release'):
        ver = public.ReadFile('/etc/redhat-release')
        if ver.startswith('CentOS Stream release 8'):
            kernel = public.ExecShell('uname -r')[0].strip()
            result = re.search("^(\\d+.\\d+.\\d+-\\d+)", kernel)
            if result:
                result = result.group(1).split('.')
                result = result[:2] + result[2].split('-')
                if len(result) == 4:
                    if result[0] == '4' and result[1] == '18' and result[2] == '0':
                        if len(result[3]) <= 3:
                            fin = contrast(result[3], 425)
                            if not fin:
                                return False, '当前内核版本【{}】存在安全风险，请尽快升级至4.18.0-425及以上版本'.format(kernel)
    elif os.path.exists('/etc/issue'):
        ver = public.ReadFile('/etc/issue')
        if ver.startswith('Ubuntu 22.04'):
            kernel = public.ExecShell('uname -r')[0].strip()
            result = re.search("^(\\d+.\\d+.\\d+-\\d+)", kernel)
            if result:
                result = result.group(1).split('.')
                result = result[:2] + result[2].split('-')
                print(result)
                if len(result) == 4:
                    if result[0] == '5' and result[1] == '15' and result[2] == '0':
                        if len(result[3]) <= 3:
                            fin = contrast(result[3], 70)
                            if not fin:
                                return False, '当前内核版本【{}】存在安全风险，请尽快升级至5.15.0-70及以上版本'.format(kernel)
    return True, '当前内核版本无风险'


def contrast(a, b):
    if len(a) >= 3:
        if a[0].isdigit() and a[1].isdigit() and a[2].isdigit():
            if int(a[0:3]) >= int(b):
                return True
            else:
                return False
        elif a[0].isdigit() and a[1].isdigit():
            if int(a[0:2]) >= int(b):
                return True
            else:
                return False
        elif a[0].isdigit():
            if int(a[0]) >= int(b):
                return True
            else:
                return False
        else:
            return False
    elif len(a) == 2:
        if a[0].isdigit() and a[1].isdigit():
            if int(a[0:2]) >= int(b):
                return True
            else:
                return False
        elif a[0].isdigit():
            if int(a[0]) >= int(b):
                return True
            else:
                return False
        else:
            return False
    elif len(a) == 1:
        if a[0].isdigit():
            if int(a[0]) >= int(b):
                return True
            else:
                return False
        else:
            return False
    else:
        return False

