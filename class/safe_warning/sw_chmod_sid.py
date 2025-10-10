#!/usr/bin/python
# coding: utf-8

import os, public

_title = '检查拥有suid和sgid权限的文件'
_version = 1.0  # 版本
_ps = "检查重要文件是否存在suid和sgid权限"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-09'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_chmod_sid.pl")
_tips = [
    "使用chmod u-s 【文件名】命令去除suid权限",
    "使用chmod g-s 【文件名】去除sgid权限"
]
_help = ''
_remind = '此方案去除了重要文件的特殊权限，可以防止入侵者利用这些文件进行权限提升。'


def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    exist_list = []
    suid_list = []
    sgid_list = []
    # 列出重要文件，先判断是否存在
    file_list = ['/usr/bin/chage', '/usr/bin/gpasswd', '/usr/bin/wall', '/usr/bin/chfn', '/usr/bin/chsh',
                 '/usr/bin/newgrp',
                 '/usr/bin/write', '/usr/sbin/usernetctl', '/bin/mount', '/bin/umount', '/bin/ping', '/sbin/netreport']
    for fl in file_list:
        if os.path.exists(fl):
            exist_list.append(fl)
    for el in exist_list:
        file_stat = os.stat(el)
        if file_stat.st_mode & 0o4000:
            suid_list.append(el)
        if file_stat.st_mode & 0o2000:
            sgid_list.append(el)
    if suid_list and sgid_list:
        return False, "存在suid特权的文件：{}<br>存在sgid特权的文件：{}".format('、'.join(suid_list), '、'.join(sgid_list))
    elif suid_list:
        return False, "以下文件存在suid特权：{}".format('、'.join(suid_list))
    elif sgid_list:

        return False, "以下文件存在sgid特权：{}".format('、'.join(sgid_list))
    else:
        return True, "无风险"
    # find命令-perm 判断是否有suid或guid，有则返回该文件名
    # result_str = public.ExecShell('find {} -type f -perm /04000 -o -perm /02000'.format(' '.join(exist_list)))[
    #     0].strip()
    # result = '、'.join(result_str.split('\n'))
    # if result:
    #     return False, '以下文件存在sid特权，chmod u-s或g-s去除sid位：\"{}\"'.format(result)
    # else:
    #     return True, '无风险'
