#!/usr/bin/python
# coding: utf-8

import sys, os, public
_title = 'Docker关键性文件权限检查'
_version = 1.0  # 版本
_ps = "Docker关键性文件权限检查"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-14'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_docker_mod.pl")
_tips = [
    "在【文件】页面，对指定目录或文件设置正确的权限和所有者",
    "docker.service和docker.socket需要赋予【644】权限",
    "docker目录chmod /etc/docker 755"
]
_help = ''
_remind = '此方案加强了对Docker文件的保护，防止入侵者篡改Docker文件。'


def check_run():
    dir_list = [
        ['/usr/lib/systemd/system/docker.service', 644, 'root'],
        ['/usr/lib/systemd/system/docker.socket', 644, 'root'],
        ['/etc/docker', 755, 'root']
        ]

    not_mode_list = []
    for d in dir_list:
        if not os.path.exists(d[0]):
            continue
        u_mode = public.get_mode_and_user(d[0])
        if u_mode['user'] != d[2]:
            not_mode_list.append("{} 当前权限: {} : {} 安全权限: {} : {}".format(d[0],u_mode['mode'],u_mode['user'],d[1],d[2]))
        if int(u_mode['mode']) != d[1]:
            not_mode_list.append("{} 当前权限: {} : {} 安全权限: {} : {}".format(d[0],u_mode['mode'],u_mode['user'],d[1],d[2]))
    if not_mode_list:
        return False, '以下关键文件或目录权限错误:{}'.format('、'.join(not_mode_list))
    else:
        return True, "无风险"
