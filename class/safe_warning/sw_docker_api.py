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
# Docker API 未授权访问
# -------------------------------------------------------------------
# import sys, os
# os.chdir('/www/server/panel')
# sys.path.append("class/")

import  public, os,requests
_title = 'Docker API 未授权访问'
_version = 1.0  # 版本
_ps = "Docker API 未授权访问"  # 描述
_level = 3  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-8-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_docker_api.pl")
_tips = [
    "在安全-系统防火墙将2375端口的来源设置为指定IP或域名",
    "若不为业务需要，建议关闭该api"
]
_help = ''
_remind = '此方案可以修复Docker的未授权访问漏洞，防止攻击者利用Docker入侵服务器。需要对API访问进行限制，确保不会影响原有的网站业务运行。'


#
def get_local_ip():
    '''获取内网IP'''
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        return ip
    finally:
        s.close()
    return '127.0.0.1'

def check_run():
    '''
        @name 面板登录告警是否开启
        @time 2022-08-12
        @author lkq@bt.cn
    '''
    try:
        if os.path.exists("/lib/systemd/system/docker.service"):
            data=public.ReadFile("/lib/systemd/system/docker.service")
            if not data:return  True, '无风险'
            if '-H tcp://' in data:
                datas=requests.get("http://{}:2375/info".format(get_local_ip()),timeout=1)
                datas.json()
                if 'KernelVersion' in  datas.text and 'RegistryConfig' in datas.text and 'DockerRootDir' in datas.text:
                    return False,"Docker API 存在未授权访问"
        return True, '无风险'
    except:return True,"无风险"