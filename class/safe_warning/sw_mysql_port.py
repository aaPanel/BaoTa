#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# Maintainer:hezhihong <bt_ahong@qq.com>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# MySQL端口安全检测
# -------------------------------------------------------------------

import os, re, public, json, psutil

_title = 'MySQL端口安全'
_version = 1.1  # 版本
_ps = "检测当前服务器的MySQL端口是否安全"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-08-18'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_mysql_port.pl")
_tips = [
    "若非必要，在【安全】页面将MySQL端口的放行删除",
    "通过【系统防火墙】插件修改MySQL端口的放行为限定IP，以增强安全性",
    "使用【Fail2ban防爆破】插件对MySQL服务进行保护"
]
_help = ''
_remind = '此方案加强的对MySQL数据库的防护，降低服务器被窃取数据的风险。修复之前要根据业务需求开放可访问IP，确保网站运行正常。'


def check_run():
    '''
        @name 开始检测
        @author hwliang<2022-08-18>
        @return tuple (status<bool>,msg<string>)

        @example
            status, msg = check_run()
            if status:
                print('OK')
            else:
                print('Warning: {}'.format(msg))

    '''
    import time
    s_time = time.time()
    mysql_port = ""
    datadir = public.get_datadir()
    if not datadir:
        return True, '无风险'
    pid_file = "{}/{}.pid".format(datadir, public.get_hostname())
    # 从pid文件中获取MySQL进程ID
    if os.path.exists(pid_file):
        try:
            pid = int(public.readFile(pid_file))
            status = public.pid_exists(pid)
            if not status: return True, '无风险'
            process = psutil.Process(pid)
            con = process.connections()
            for c in con:
                if c.status == psutil.CONN_LISTEN:
                    mysql_port = str(c.laddr.port)
        except:
            return True, '无风险'
    else:
        return True, '无风险'
    # 检查防火墙规则
    if mysql_port:
        try:
            # sql = public.M('firewall_new')
            # if sql.where("ports = ? and address = ?", (mysql_port, "")).count() == 0:
            #     public.print_log("|===========开始扫描MySQL端口44444")
            #     return True, '无风险'
            pass
        except Exception as e:
            return True, '无风险'
    else:
        return True, '未查询到Mysql端口'
    # mycnf_file = '/etc/my.cnf'
    # if not os.path.exists(mycnf_file):
    #     return True,'未安装MySQL'
    # mycnf = public.readFile(mycnf_file)
    # port_tmp = re.findall(r"port\s*=\s*(\d+)",mycnf)
    # if not port_tmp:
    #     return True,'未安装MySQL'
    # if not public.is_mysql_process_exists():
    #     return True,'未启动MySQL'
    #
    # # result = public.check_port_stat(int(port_tmp[0]),public.GetLocalIp())
    # # 兼容socket能连通但实际端口不通情况
    # import socket
    # temp = {'port': port_tmp[0], 'local': True}
    # result = 0
    # try:
    #     s = socket.socket()
    #     s.settimeout(0.15)
    #     s.connect(("127.0.0.1", mysql_port))
    #     s.close()
    #     result += 2
    # except:
    #     temp['local'] = False
    #
    # if result != 0:
    #     public.print_log("旧：{}".format(time.time() - s_time))
    #     if os.path.exists('/usr/sbin/firewalld'):
    #         res=public.readFile("/etc/firewalld/zones/public.xml")
    #         if res and res.find('"{}"'.format(port_tmp[0]) == -1):
    #             public.print_log("走掉了")
    #             return True,'无风险'
    #     elif os.path.exists('/usr/sbin/ufw'):
    #         rule_file = '/etc/ufw/user.rules'
    #         if os.path.exists(rule_file):
    #             res=public.readFile(rule_file)
    #             if res and res.find('input -p tcp --dport {} -j ACCEPT'.format(port_tmp[0])) == -1:
    #                 return True,'无风险'
    #         else:
    #             res=public.ExecShell('ufw status verbose|grep {}'.format(port_tmp[0]))
    #             check_str=' '+port_tmp[0]+'/'
    #             if res[0].find(check_str) == -1:
    #                 return True,'无风险'
    #     elif os.path.exists('/usr/sbin/iptables'):
    #             res=public.ExecShell("iptables --list-rules|grep -v '\-s '|grep {}".format(port_tmp[0]))[0]
    #             if res and res.find('-p tcp -m state --state NEW -m tcp --dport {} -j ACCEPT'.format(port_tmp[0])) == -1:
    #                 return True,'无风险'
    #
    # else:return True,'无风险'
    # 新增fail2ban配置检测
    fail2ban_file = '/www/server/panel/plugin/fail2ban/config.json'
    if os.path.exists(fail2ban_file):
        try:
            fail2ban_config = json.loads(public.readFile(fail2ban_file))
            if 'mysql' in fail2ban_config.keys():
                if fail2ban_config['mysql']['act'] == 'true':
                    # public.print_log("不对")
                    return True, '已开启Fail2ban防爆破'
        except:
            pass

    return False, '当前MySQL端口: {}，可被任意服务器访问，这可能导致MySQL被暴力破解，存在安全隐患'.format(mysql_port)
