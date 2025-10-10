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


class NodeModule(BaseUtil,ConfigManager):
    def __init__(self):
        self.base_path = '/www/backup/backup_restore'
        self.bakcup_task_json = self.base_path + '/backup_task.json'
        self.node_data_path = '/www/server/panel/data/db/node.db'

    def backup_node_data(self,timestamp):
        if not os.path.exists(self.node_data_path):
            return False
        
        data_list=self.get_backup_data_list(timestamp)
        if not data_list:
            return None

        backup_path = self.base_path + "/{timestamp}_backup/node".format(timestamp=timestamp)
        if not os.path.exists(backup_path):
            public.ExecShell('mkdir -p {}'.format(backup_path))

        self.print_log("====================================================","backup")
        self.print_log("开始备份节点管理数据",'backup')

        node_info={}
        node_info['status'] = 1
        node_info['msg'] = None
        node_info['node_backup_name'] = None
        node_info['node_list'] = []

        node_list = public.M('node').field('id,address,remarks,server_ip').select()
        for i in node_list:
            node_info['node_list'].append({
                "name": i['remarks'],
                "server_ip": i['server_ip'],
            })
        
        data_list['data_list']['node'] = node_info
        self.update_backup_data_list(timestamp, data_list)

        node_backup_name = "node.db"
        public.ExecShell("\cp -rpa /www/server/panel/data/db/node.db {}".format(backup_path))
        node_info['node_backup_name'] = backup_path + "/" + node_backup_name
        node_info['status'] = 2
        node_info['msg'] = None
        node_info['size'] = self.get_file_size(backup_path + "/" + node_backup_name)
        data_list['data_list']['node'] = node_info
        self.update_backup_data_list(timestamp, data_list)
        backup_size=self.format_size(self.get_file_size(backup_path + "/" + node_backup_name))
        self.print_log("节点管理数据备份完成 数据大小：{}".format(backup_size),'backup')

    def restore_node_data(self,timestamp):
        restore_data=self.get_restore_data_list(timestamp)
        if not restore_data:
            return None

        node_data=restore_data['data_list']['node']
        if not node_data:
            return None
        
        self.print_log("==================================","restore")
        self.print_log("开始还原节点数据","restore")

        restore_data['data_list']['node']['restore_status']=1
        self.update_restore_data_list(timestamp, restore_data)

        node_backup_name = node_data['node_backup_name']
        if not os.path.exists(node_backup_name):
            self.print_log("还原失败，文件不存在","restore")
            return
        
        if os.path.exists(self.node_data_path):
            public.ExecShell("mv {} {}.bak".format(self.node_data_path,self.node_data_path))

        print(node_backup_name)
        print(self.node_data_path)
        public.ExecShell("\cp -rpa {} {}".format(node_backup_name,self.node_data_path))

        restore_data['data_list']['node']['restore_status']=2
        self.update_restore_data_list(timestamp, restore_data)

        self.print_log("节点数据还原完成","restore")
        
if __name__ == '__main__':
    # 获取命令行参数
    if len(sys.argv) < 3:
        print("Usage: btpython backup_manager.py <method> <timestamp>")
        sys.exit(1)
    method_name = sys.argv[1]  # 方法名
    timestamp = sys.argv[2]    # IP地址     
    node_module = NodeModule()  # 实例化对象
    if hasattr(node_module, method_name):  # 检查方法是否存在
        method = getattr(node_module, method_name)  # 获取方法
        method(timestamp)  # 调用方法
    else:
        print(f"Error: 方法 '{method_name}' 不存在")