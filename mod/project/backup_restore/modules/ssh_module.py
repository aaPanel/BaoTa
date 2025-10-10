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


class SshModule(BaseUtil,ConfigManager):
    def __init__(self):
        self.base_path = '/www/backup/backup_restore'
        self.bakcup_task_json = self.base_path + '/backup_task.json'
        self.ssh_path="/www/server/panel/config/ssh_info"

    def backup_ssh_data(self,timestamp):
        self.print_log("====================================================","backup")
        self.print_log("开始备份终端数据","backup")

        ssh_backup_path=self.base_path + "/{timestamp}_backup/ssh".format(timestamp=timestamp)
        if not os.path.exists(ssh_backup_path):
            public.ExecShell('mkdir -p {}'.format(ssh_backup_path))
        print(self.ssh_path)
        public.ExecShell("\cp -rpa {} {}".format(self.ssh_path,ssh_backup_path))

        ssh_info={}
        ssh_info['status'] = 2
        ssh_info['msg'] = None


        # ssh_info['status'] = 3
        # ssh_info['msg'] = "导出ssh数据报错"
        ssh_info['ssh_info_path'] = ssh_backup_path
        backup_size=self.format_size(self.get_file_size(ssh_backup_path))
        self.print_log("备份终端数据完成 数据大小：{}".format(backup_size),'backup')

        data_list=self.get_backup_data_list(timestamp)
        data_list['data_list']['ssh']=ssh_info
        self.update_backup_data_list(timestamp, data_list)


    def restore_ssh_data(self,timestamp):
        self.print_log("==================================","restore")
        self.print_log("开始还原终端数据","restore")

        restore_data=self.get_restore_data_list(timestamp)
        ssh_data=restore_data['data_list']['ssh']
        ssh_info_path=ssh_data['ssh_info_path'] + "/ssh_info"

        restore_data['data_list']['ssh']['restore_status']=1
        self.update_restore_data_list(timestamp, restore_data)

        if not os.path.exists(ssh_info_path):
            self.print_log("还原失败，文件不存在","restore")
            return
        if not os.path.exists(self.ssh_path):
            public.ExecShell("mkdir -p {}".format(self.ssh_path))
        public.ExecShell("\cp -rpa {}/* {}".format(ssh_info_path,self.ssh_path))
        self.print_log("还原终端数据完成","restore")

        restore_data['data_list']['ssh']['restore_status']=2
        self.update_restore_data_list(timestamp, restore_data)


if __name__ == '__main__':
    # 获取命令行参数
    if len(sys.argv) < 2:
        print("Usage: btpython backup_manager.py <method> <timestamp>")
        sys.exit(1)
    method_name = sys.argv[1]  # 方法名  
    timestamp = sys.argv[2]
    ssh_manager = SshModule()  # 实例化对象
    if hasattr(ssh_manager, method_name):  # 检查方法是否存在
        method = getattr(ssh_manager, method_name)  # 获取方法
        method(timestamp)  # 调用方法
    else:
        print(f"Error: 方法 '{method_name}' 不存在")