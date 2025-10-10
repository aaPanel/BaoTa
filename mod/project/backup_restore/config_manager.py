# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: miku <wzz@bt.cn>
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

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

if '/www/server/panel' not in sys.path:
    sys.path.insert(0, '/www/server/panel')

import public


class ConfigManager:
    def __init__(self):
        self.base_path = '/www/backup/backup_restore'
        self.bakcup_task_json = self.base_path + '/backup_task.json'

    def get_backup_conf(self,timestamp):
        if not os.path.exists(self.bakcup_task_json):
            return None
        task_json_data=json.loads(public.ReadFile(self.bakcup_task_json))
        data = [item for item in task_json_data if str(item['timestamp']) == timestamp]
        if not data:
            return None
        return data[0]

    def save_backup_conf(self,timestamp,data):
        if not os.path.exists(self.bakcup_task_json):
            return None
        task_json_data=json.loads(public.ReadFile(self.bakcup_task_json))
        for item in task_json_data:
            if str(item['timestamp']) == timestamp:
                item.update(data)
                break
        public.WriteFile(self.bakcup_task_json,json.dumps(task_json_data))

    def get_backup_data_list(self,timestamp):
        data_list_json=self.base_path + '/{timestamp}_backup/backup.json'.format(timestamp=timestamp)
        if not os.path.exists(data_list_json):
            return None
        data_list_data=json.loads(public.ReadFile(data_list_json))
        return data_list_data
    

    def update_backup_data_list(self,timestamp,data_list):
        data_list_json=self.base_path + '/{timestamp}_backup/backup.json'.format(timestamp=timestamp)
        try:
            # 读取现有配置
            if os.path.exists(data_list_json):
                current_data = json.loads(public.ReadFile(data_list_json))
                # 更新数据
                current_data.update(data_list)
                data_list = current_data
                
            # 写入更新后的配置
            public.WriteFile(data_list_json, json.dumps(data_list))
            return True
        except Exception as e:
            print(f"更新备份配置失败: {str(e)}")
            return False
        

    def get_restore_data_list(self,timestamp):
        data_list_json=self.base_path + '/{timestamp}_backup/restore.json'.format(timestamp=timestamp)
        if not os.path.exists(data_list_json):
            return None
        data_list_data=json.loads(public.ReadFile(data_list_json))
        return data_list_data
    
    def update_restore_data_list(self,timestamp,data_list):
        data_list_json=self.base_path + '/{timestamp}_backup/restore.json'.format(timestamp=timestamp)
            # 读取现有配置
        try:
            # 读取现有配置
            if os.path.exists(data_list_json):
                current_data = json.loads(public.ReadFile(data_list_json))
                # 更新数据
                current_data.update(data_list)
                data_list = current_data
                
            # 写入更新后的配置
            public.WriteFile(data_list_json, json.dumps(data_list))
            return True
        except Exception as e:
            print(f"更新备份配置失败: {str(e)}")
            return False


if __name__ == '__main__':
    # 获取命令行参数
    if len(sys.argv) < 3:
        print("Usage: btpython config_manager.py <method> <timestamp>")
        sys.exit(1)
    method_name = sys.argv[1]  # 方法名
    timestamp = sys.argv[2]    # IP地址
    config = ConfigManager()  # 实例化对象
    if hasattr(config, method_name):  # 检查方法是否存在
        method = getattr(config, method_name)  # 获取方法
        method(timestamp)  # 调用方法
    else:
        print(f"Error: 方法 '{method_name}' 不存在")

    
    