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
import shutil
if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

if '/www/server/panel' not in sys.path:
    sys.path.insert(0, '/www/server/panel')

import panelMysql
import db_mysql
import database

import public
from mod.project.backup_restore.base_util import BaseUtil
from mod.project.backup_restore.data_manager import DataManager
from mod.project.backup_restore.config_manager import ConfigManager

class FtpModule(DataManager,BaseUtil,ConfigManager):

    def __init__(self):
        self.base_path = '/www/backup/backup_restore'
        self.bakcup_task_json = self.base_path + '/backup_task.json'

    def backup_ftp_data(self,timestamp=None):
        self.print_log("==================================","backup")
        self.print_log("开始备份ftp账户信息","backup")
        ftp_data = public.M('ftps').field('name,id,password,path,ps').select()
        filtered_ftp = [id for id in ftp_data]
        for ftp in filtered_ftp:
            self.print_log("{}用户 ✓".format(ftp['name']),"backup")
            ftp['status'] = 2
            ftp['msg'] = None
        self.print_log("ftp账户信息备份完成","backup")
        return filtered_ftp
    
    def restore_ftp_data(self,timestamp=None):
        import ftp
        self.print_log("====================================================","restore")
        self.print_log("开始还原ftp账户配置","restore")
        restore_data=self.get_restore_data_list(timestamp)

        for ftp_data in restore_data['data_list']['ftp']:
            ftp_data['restore_status']=1
            self.update_restore_data_list(timestamp, restore_data)
            local_ftp_info=public.M('ftps').where('name=?', (ftp_data["name"],)).select()
            if not local_ftp_info:
                log_str="开始还原{}账户".format(ftp_data['name'])
                self.print_log(log_str,"restore")
                args = public.dict_obj()
                args.ftp_username = ftp_data['name']
                args.path = ftp_data['path']
                args.ftp_password = ftp_data['password']
                args.ps = ftp_data['ps']
                res = ftp.ftp().AddUser(args)
                if res['status'] == False:
                    print(ftp_data['name'])
                    ftp_data['restore_status'] = 3
                    print("创建失败啦！！！")
                else:
                    print("创建成功啦！！！")
                    new_log_str="{}账户 ✓".format(ftp_data['name'])
                    self.replace_log(log_str,new_log_str,"restore")
                    ftp_data['restore_status'] = 2
                self.update_restore_data_list(timestamp, restore_data)
            else:
                ftp_data['restore_status'] = 2
        self.print_log("ftp账户配置还原完成","restore")
           

if __name__ == '__main__':
    # 获取命令行参数
    if len(sys.argv) < 3:
        print("Usage: btpython backup_manager.py <method> <timestamp>")
        sys.exit(1)
    method_name = sys.argv[1]  # 方法名
    timestamp = sys.argv[2]    # IP地址     
    ftp_module = FtpModule()  # 实例化对象
    if hasattr(ftp_module, method_name):  # 检查方法是否存在
        method = getattr(ftp_module, method_name)  # 获取方法
        method(timestamp)  # 调用方法
    else:
        print(f"Error: 方法 '{method_name}' 不存在")