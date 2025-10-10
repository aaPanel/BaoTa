#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# 检测关键目录权限是否正确
# -------------------------------------------------------------------


import os,sys,re,public

_title = '关键目录权限检测'
_version = 1.0                              # 版本
_ps = "检测关键目录权限是否正确"              # 描述
_level = 0                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-05'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_dir_mode.pl")
_tips = [
    "在【文件】页面，对指定目录或文件设置正确的权限和所有者",
    "注意1：通过【文件】页面设置目录权限时，请取消【应用到子目录】选项",
    "注意2：错误的文件权限，不但存在安全风险，还可能导致服务器上的一些软件无法正常工作"
    ]

_help = ''


def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-05>
        @return tuple (status<bool>,msg<string>)
    '''
    dir_list = [
        ['/usr',755,'root'],
        ['/usr/bin',555,'root'],
        ['/usr/sbin',555,'root'],
        ['/usr/lib',555,'root'],
        ['/usr/lib64',555,'root'],
        ['/usr/local',755,'root'],
        ['/etc',755,'root'],
        ['/etc/passwd',644,'root'],
        ['/etc/shadow',600,'root'],
        ['/etc/gshadow',600,'root'],
        ['/etc/cron.deny',600,'root'],
        ['/etc/anacrontab',600,'root'],
        ['/var',755,'root'],
        ['/var/spool',755,'root'],
        ['/var/spool/cron',700,'root'],
        ['/var/spool/cron/root',600,'root'],
        ['/var/spool/cron/crontabs/root',600,'root'],
        ['/www',755,'root'],
        ['/www/server',755,'root'],
        ['/www/wwwroot',755,'root'],
        ['/root',550,'root'],
        ['/mnt',755,'root'],
        ['/home',755,'root'],
        ['/dev',755,'root'],
        ['/opt',755,'root'],
        ['/sys',555,'root'],
        ['/run',755,'root'],
        ['/tmp',777,'root']
    ]

    not_mode_list = []
    # for d in dir_list:
    #     if not os.path.exists(d[0]): continue
    #     u_mode = public.get_mode_and_user(d[0])
    #     if u_mode['user'] != d[2]:
    #         not_mode_list.append("{} 当前权限: {} : {} 安全权限: {} : {}".format(d[0],u_mode['mode'],u_mode['user'],d[1],d[2]))
    #     if int(u_mode['mode']) != d[1]:
    #         not_mode_list.append("{} 当前权限: {} : {} 安全权限: {} : {}".format(d[0],u_mode['mode'],u_mode['user'],d[1],d[2]))

    # if not_mode_list:
    #     return False,'以下关键文件或目录权限错误: <br />' + ("<br />".join(not_mode_list))

    #如果是管理员账号，检查是否有root权限



    #检测



    return True,'无风险'
