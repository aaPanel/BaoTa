# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: miku <miku@bt.cn>
# -------------------------------------------------------------------
import json
import os
import sys
import time
import sys
import concurrent.futures
import threading
import hashlib
import datetime
import re

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

if '/www/server/panel' not in sys.path:
    sys.path.insert(0, '/www/server/panel')

import public
from mod.project.backup_restore.base_util import BaseUtil
#from mod.project.backup_restore.data_manager import DataManager
from mod.project.backup_restore.config_manager import ConfigManager


class FirewallModule(BaseUtil,ConfigManager):
    def __init__(self):
        self.base_path = '/www/backup/backup_restore'
        self.bakcup_task_json = self.base_path + '/backup_task.json'

    def backup_firewall_data(self,timestamp):
        self.print_log("====================================================","backup")
        self.print_log("开始备份防火墙数据","backup")
        from firewallModel.comModel import main as firewall_com
        from safeModel.firewallModel import main as safe_firewall_main
        backup_path=self.base_path + "/{timestamp}_backup/firewall".format(timestamp=timestamp)
        if not os.path.exists(backup_path):
            public.ExecShell('mkdir -p {}'.format(backup_path))
        
        port_data_path = firewall_com().export_rules(public.to_dict_obj({"rule": 'port', 'chain': 'ALL'}))['msg']
        print(port_data_path)
        ip_data_path = firewall_com().export_rules(public.to_dict_obj({"rule": 'ip', 'chain': 'ALL'}))['msg']
        print(ip_data_path)
        forward_data_path = firewall_com().export_rules(public.to_dict_obj({"rule": 'forward'}))['msg']
        print(forward_data_path)
        country_data_path = safe_firewall_main().export_rules(public.to_dict_obj({'rule_name': 'country_rule'}))['msg']
        print(country_data_path)
        
        firewall_info = {
            "status": 2,
            "err_msg": None
        }
        
        for data_path in [port_data_path, ip_data_path, forward_data_path, country_data_path]:
            if "json" in data_path:
                public.ExecShell('\cp -rpa {} {}'.format(data_path, backup_path))
                file_name = data_path.split("/")[-1]
                if "port_rule" in file_name:
                    self.print_log("防火墙端口规则 ✓",'backup')
                    firewall_info["port_data_path"] = backup_path + "/" + file_name
                elif "ip_rules" in file_name:
                    self.print_log("防火墙IP规则 ✓",'backup')
                    firewall_info["ip_data_path"] = backup_path + "/" + file_name
                elif "port_forward" in file_name:
                    self.print_log("防火墙转发规则 ✓",'backup')
                    firewall_info["forward_data_path"] = backup_path + "/" + file_name
                elif "country" in file_name:
                    self.print_log("防火墙地区规则 ✓",'backup')
                    firewall_info["country_data_path"] = backup_path + "/" + file_name

        print(firewall_info)
        # 将防火墙信息写入备份配置文件
        data_list=self.get_backup_data_list(timestamp)
        data_list['data_list']['firewall']=firewall_info
        self.update_backup_data_list(timestamp, data_list) 
        
        self.print_log("防火墙数据备份完成","backup")
        #return firewall_info

    def init_firewall_data(self):
        self.print_log("开始初始化防火墙数据","restore")
        if not os.path.exists('/etc/systemd/system/BT-FirewallServices.service'):
            panel_path = public.get_panel_path()
            exec_shell = '('
            if not os.path.exists('/usr/sbin/ipset'):
                exec_shell = exec_shell + '{} install ipset -y;'.format(public.get_sys_install_bin())
            exec_shell = exec_shell + 'sh {panel_path}/script/init_firewall.sh;btpython -u {panel_path}/script/upgrade_firewall.py )'.format(panel_path=panel_path)
            public.ExecShell(exec_shell)
            return {'status': True, 'msg': '已安装.'}
        elif public.ExecShell("iptables -C INPUT -j IN_BT")[1] != '':         #丢失iptable链 需要重新创建
            exec_shell = 'sh {}/script/init_firewall.sh'.format(public.get_panel_path())
            public.ExecShell(exec_shell)
            return {'status': True, 'msg': '已安装.'}
        else:
            return {'status': True, 'msg': '已安装.'}

    def restore_firewall_data(self,timestamp):
        from firewallModel.comModel import main as firewall_com
        from safeModel.firewallModel import main as safe_firewall_main
        self.print_log("====================================================","restore")
        self.print_log("开始还原防火墙数据","restore")
        firewall_status=self.init_firewall_data()
        remote_data=self.get_restore_data_list(timestamp)
        
        firewall_data=remote_data['data_list']['firewall']
        port_rule_file = firewall_data.get('port_data_path')
        if port_rule_file:
            if os.path.exists(port_rule_file):
                self.print_log("开始还原防火墙端口规则","restore")
                result=firewall_com().import_rules(public.to_dict_obj({"rule": 'port', 'file': port_rule_file}))
                if result['status'] == True:
                    self.print_log("防火墙端口规则还原成功","restore")
                else:
                    self.print_log("防火墙端口规则还原失败","restore")
        ip_rule_file = firewall_data.get('ip_data_path')
        if ip_rule_file:
            if os.path.exists(ip_rule_file):
                self.print_log("开始还原防火墙IP规则","restore")
                result=firewall_com().import_rules(public.to_dict_obj({"rule": 'ip', 'file': ip_rule_file}))
                if result['status'] == True:
                    self.print_log("防火墙IP规则还原成功","restore")
                else:
                    self.print_log("防火墙IP规则还原失败","restore")
            
        forward_rule_file = firewall_data.get('forward_data_path')
        if forward_rule_file:
            if os.path.exists(forward_rule_file):
                self.print_log("开始还原防火墙转发规则","restore")
                result=firewall_com().import_rules(public.to_dict_obj({"rule": 'forward', 'file': forward_rule_file}))
                if result['status'] == True:
                    self.print_log("防火墙转发规则还原成功","restore")
                else:
                    self.print_log("防火墙转发规则还原失败","restore")

        country_rule_file = firewall_data.get('country_data_path')
        if country_rule_file:
            if os.path.exists(country_rule_file):
                self.print_log("开始还原防火墙地区规则","restore")
                public.ExecShell('\cp -rpa {}  /www/server/panel/data/firewall'.format(country_rule_file))
                country_rule_file_last_path=country_rule_file.split("/")[-1]
                result=safe_firewall_main().import_rules(public.to_dict_obj({'rule_name': 'country_rule', 'file_name': country_rule_file_last_path}))
                if result['status'] == True:
                    self.print_log("防火墙地区规则还原成功","restore")
                else:
                    self.print_log("防火墙地区规则还原失败","restore")

        # 重启防火墙
        self.print_log("开始重启防火墙","restore")
        firewall_com().set_status(public.to_dict_obj({'status': 1}))
        self.print_log("重启防火墙完成","restore")
        remote_data['data_list']['firewall']['status']=2
        self.update_restore_data_list(timestamp, remote_data)
        
if __name__ == '__main__':
    # 获取命令行参数
    if len(sys.argv) < 2:
        print("Usage: btpython backup_manager.py <method> <timestamp>")
        sys.exit(1)
    method_name = sys.argv[1]  # 方法名  
    timestamp = sys.argv[2]
    firewall_manager = FirewallModule()  # 实例化对象
    if hasattr(firewall_manager, method_name):  # 检查方法是否存在
        method = getattr(firewall_manager, method_name)  # 获取方法
        method(timestamp)  # 调用方法
    else:
        print(f"Error: 方法 '{method_name}' 不存在")