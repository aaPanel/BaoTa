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


class MailModule(BaseUtil,ConfigManager):
    def __init__(self):
        self.base_path = '/www/backup/backup_restore'
        self.bakcup_task_json = self.base_path + '/backup_task.json'
        self.vmail_data_path = '/www/vmail'

    def backup_vmail_data(self,timestamp):
        if not os.path.exists(self.vmail_data_path):
            return False
        
        data_list=self.get_backup_data_list(timestamp)
        if not data_list:
            return None

        backup_path = self.base_path + "/{timestamp}_backup/vmail".format(timestamp=timestamp)
        if not os.path.exists(backup_path):
            public.ExecShell('mkdir -p {}'.format(backup_path))

        self.print_log("====================================================","backup")
        self.print_log("开始备份邮局数据",'backup')

        maill_info={}
        maill_info['status'] = 1
        maill_info['msg'] = None
        maill_info['vmail_backup_name'] = None
        
        data_list['data_list']['vmail'] = maill_info
        self.update_backup_data_list(timestamp, data_list)

        vmail_backup_name = "vmail_{timestamp}.tar.gz".format(timestamp=timestamp)
        public.ExecShell("cd /www && tar -czvf {} vmail".format(vmail_backup_name))
        public.ExecShell("mv /www/{} {}".format(vmail_backup_name, backup_path))
        maill_info['vmail_backup_name'] = backup_path + "/" + vmail_backup_name
        maill_info['status'] = 2
        maill_info['msg'] = None
        maill_info['size'] = self.get_file_size(backup_path + "/" + vmail_backup_name)
        data_list['data_list']['vmail'] = maill_info
        self.update_backup_data_list(timestamp, data_list)
        backup_size=self.format_size(self.get_file_size(backup_path + "/" + vmail_backup_name))
        self.print_log("邮局数据备份完成 数据大小：{}".format(backup_size),'backup')

    def restore_vmail_data(self,timestamp):
        restore_data=self.get_restore_data_list(timestamp)
        if not restore_data:
            return None

        vmail_data=restore_data['data_list']['vmail']
        if not vmail_data:
            return None
        
        self.print_log("==================================","restore")
        self.print_log("开始还原邮局数据","restore")

        restore_data['data_list']['vmail']['restore_status']=1
        self.update_restore_data_list(timestamp, restore_data)

        vmail_backup_name = vmail_data['vmail_backup_name']
        if not os.path.exists(vmail_backup_name):
            self.print_log("还原失败，文件不存在","restore")
            return
        
        if os.path.exists(self.vmail_data_path):
            public.ExecShell("mv {} {}.bak".format(self.vmail_data_path,self.vmail_data_path))

        public.ExecShell("\cp -rpa {} /www/{}".format(vmail_backup_name,os.path.basename(self.vmail_data_path)))
        public.ExecShell("cd /www && tar -xzvf {}".format(os.path.basename(self.vmail_data_path)))

        restore_data['data_list']['vmail']['restore_status']=2
        self.update_restore_data_list(timestamp, restore_data)

        self.print_log("邮局数据还原完成","restore")
        
if __name__ == '__main__':
    # 获取命令行参数
    if len(sys.argv) < 3:
        print("Usage: btpython backup_manager.py <method> <timestamp>")
        sys.exit(1)
    method_name = sys.argv[1]  # 方法名
    timestamp = sys.argv[2]    # IP地址     
    mail_module = MailModule()  # 实例化对象
    if hasattr(mail_module, method_name):  # 检查方法是否存在
        method = getattr(mail_module, method_name)  # 获取方法
        method(timestamp)  # 调用方法
    else:
        print(f"Error: 方法 '{method_name}' 不存在")