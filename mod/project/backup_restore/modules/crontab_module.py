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


class CrontabModule(BaseUtil,ConfigManager):
    def __init__(self):
        self.base_path = '/www/backup/backup_restore'
        self.bakcup_task_json = self.base_path + '/backup_task.json'

    def backup_crontab_data(self,timestamp):
        self.print_log("====================================================","backup")
        self.print_log("开始备份计划任务","backup")

        #backup_date=conf_data['backup_date']

        backup_path=self.base_path + "/{timestamp}_backup/crontab".format(timestamp=timestamp)
        if not os.path.exists(backup_path):
            public.ExecShell('mkdir -p {}'.format(backup_path))
        
        field = 'id,name,type,where1,where_hour,where_minute,echo,addtime,status,save,backupTo,sName,sBody,sType,urladdress,save_local,notice,notice_channel,db_type,split_type,split_value,type_id,rname,keyword,post_param,flock,time_set,backup_mode,db_backup_path,time_type,special_time,log_cut_path,user_agent,version,table_list,result,second,stop_site'
        crontab_data = public.M('crontab').order("id asc").field(field).select()
        for task in crontab_data:
            task['type_id'] = ""

        crontab_json_path="{}/crontab.json".format(backup_path)
        public.WriteFile(crontab_json_path,json.dumps(crontab_data))
        for item in crontab_data:
            self.print_log("计划任务 {} ✓".format(item['name']),"backup")

        crontab_info={}
        crontab_info['status'] = 2
        crontab_info['msg'] = None
        crontab_info['crontab_json'] = crontab_json_path
        crontab_info['file_sha256'] = self.get_file_sha256(crontab_json_path)
        self.print_log("备份计划任务完成",'backup')

        #conf_data['crontab'].append(crontab)
        # conf_data.append(crontab)
        data_list=self.get_backup_data_list(timestamp)
        data_list['data_list']['crontab']=crontab_info
        self.update_backup_data_list(timestamp, data_list)
        #return crontab_info
        #public.WriteFile("/www/backup/backup_restore/{}_backup/backup.json".format(timestamp),json.dumps(conf_data))

    def restore_crontab_data(self,timestamp):
        self.print_log("==================================","restore")
        self.print_log("开始还原计划任务","restore")

        restore_data=self.get_restore_data_list(timestamp)
        import crontab

        cron_list = public.M('crontab').select()
        cron_list = [i['name'] for i in cron_list]
        crontab_data_json=restore_data['data_list']['crontab']['crontab_json']
        restore_data['data_list']['crontab']['restore_status']=1
        self.update_restore_data_list(timestamp, restore_data)
        crontab_data=json.loads(public.ReadFile(crontab_data_json))
        for crontab_item in crontab_data:
            if crontab_item['name'] not in cron_list:
                new_crontab = {
                    "name": crontab_item['name'],
                    "type": crontab_item['type'],
                    "where1": crontab_item['where1'],
                    "hour": crontab_item['where_hour'],
                    "minute": crontab_item['where_minute'],
                    "status": crontab_item['status'],
                    "save": crontab_item['save'],
                    "backupTo": crontab_item['backupTo'],
                    "sType": crontab_item['sType'],
                    "sBody": crontab_item['sBody'],
                    "sName": crontab_item['sName'],
                    "urladdress": crontab_item['urladdress'],
                    "save_local": crontab_item['save_local'],
                    "notice": crontab_item['notice'],
                    "notice_channel": crontab_item['notice_channel'],
                    "db_type": crontab_item['db_type'],
                    "split_type": crontab_item['split_type'],
                    "split_value": crontab_item['split_value'],
                    "keyword": crontab_item['keyword'],
                    "post_param": crontab_item['post_param'],
                    "flock": crontab_item['flock'],
                    "time_set": crontab_item['time_set'],
                    "backup_mode": crontab_item['backup_mode'],
                    "db_backup_path": crontab_item['db_backup_path'],
                    "time_type": crontab_item['time_type'],
                    "special_time": crontab_item['special_time'],
                    "user_agent": crontab_item['user_agent'],
                    "version": crontab_item['version'],
                    "table_list": crontab_item['table_list'],
                    "result": crontab_item['result'],
                    "log_cut_path": crontab_item['log_cut_path'],
                    "rname": crontab_item['rname'],
                    "type_id": crontab_item['type_id'],
                    "second": crontab_item.get('second', ''),
                }
                result = crontab.crontab().AddCrontab(new_crontab)
                if result['status'] == False:
                    self.print_log("计划任务：{} 添加失败，原因{}，跳过".format(crontab_item['name'],result['msg']),"restore")
                else:
                    self.print_log("计划任务：{} 添加成功".format(crontab_item['name']),"restore")
            else:
                self.print_log("计划任务：{} 已存在，跳过".format(crontab_item['name']),"restore")

        self.print_log("还原计划任务完成","restore")
        restore_data['data_list']['crontab']['restore_status']=2
        self.update_restore_data_list(timestamp, restore_data)


if __name__ == '__main__':
    # 获取命令行参数
    if len(sys.argv) < 2:
        print("Usage: btpython backup_manager.py <method> <timestamp>")
        sys.exit(1)
    method_name = sys.argv[1]  # 方法名  
    timestamp = sys.argv[2]
    crontab_manager = CrontabModule()  # 实例化对象
    if hasattr(crontab_manager, method_name):  # 检查方法是否存在
        method = getattr(crontab_manager, method_name)  # 获取方法
        method(timestamp)  # 调用方法
    else:
        print(f"Error: 方法 '{method_name}' 不存在")