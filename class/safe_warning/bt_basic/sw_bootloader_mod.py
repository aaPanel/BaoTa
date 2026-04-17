#!/usr/bin/python
# coding: utf-8

import sys, os, public
_title = 'bootloader配置权限'
_version = 1.0  # 版本
_ps = "bootloader配置权限检查"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-15'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_bootloader_mod.pl")
_tips = [
    "根据风险描述提示的文件，对grub配置安全的权限",
    "若是grub2，则：chmod 600 /boot/grub2/grub.cfg、chown root /boot/grub2/grub.cfg",
    "若是grub，则：chmod 600 /boot/grub/grub.cfg、chown root /boot/grub/grub.cfg"
]
_help = ''
_remind = '此方案可以加强服务器grub界面的防护，进一步阻止外部入侵服务器。'

def check_run():
    dir_list = [
        ['/boot/grub2/grub.cfg', 600, 'root'],
        ['/boot/grub/grub.cfg', 600, 'root']
        ]
    # 存放没有配置权限的文件
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
