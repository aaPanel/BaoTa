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


if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

if '/www/server/panel' not in sys.path:
    sys.path.insert(0, '/www/server/panel')

os.chdir("/www/server/panel")
import public


class BaseUtil:
    def __init__(self):
        self.base_path = '/www/backup/backup_restore'
        self.history_path = '/www/backup/backup_restore/history'
        self.nginx_bin_path = '/www/server/nginx/sbin/nginx'

    def print_log(self,log:str,type:str):
        time_str = time.strftime('%Y-%m-%d %H:%M:%S')
        log = "[{}] {}".format(time_str, log)
        log_file = self.base_path + '/{}.log'.format(type)
        public.writeFile(log_file, log + "\n", 'a+')
    
    def replace_log(self,old_str:str,new_str:str,type:str):
        log_file = self.base_path + '/{}.log'.format(type)
        log_data = public.ReadFile(log_file)
        if old_str in log_data:
            log_data = log_data.replace(old_str, new_str)
            public.WriteFile(log_file, log_data)

    def get_test(self,get=None):
        return public.returnMsg(True, "测试成功")
    
    
    def get_file_sha256(self, file_path):
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(4096)  # 先读取再判断
                if not chunk:
                    break
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def get_free_space(self):
        result={}
        path="/www"
        diskstat = os.statvfs(path)
        free_space = diskstat.f_bavail * diskstat.f_frsize 
        total_space = diskstat.f_blocks * diskstat.f_frsize  
        used_space = (diskstat.f_blocks - diskstat.f_bfree) * diskstat.f_frsize
        result['free_space'] = free_space
        return result
    
    def get_file_size(self,path: str) -> int:
        try:
            if os.path.isfile(path):
                return os.path.getsize(path)
            elif os.path.isdir(path):
                return int(public.ExecShell(f"du -sb {path}")[0].split("\t")[0])
            return 0
        except:
            return 0
        
    def format_size(self,size:int):
        if size < 1024:
            return f"{size}B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.2f}KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / 1024 / 1024:.2f}MB"
        elif size < 1024 * 1024 * 1024 * 1024:
            return f"{size / 1024 / 1024 / 1024:.2f}GB"
        else:
            return f"{size / 1024 / 1024 / 1024 / 1024:.2f}TB"
        
    def web_config_check(self):
        if os.path.exists(self.nginx_bin_path):
            nginx_conf_test=public.ExecShell("ulimit -n 8192 ;{} -t".format(self.nginx_bin_path))[1]
            if "successful" in nginx_conf_test:
                return {
                    "status": True,
                    "msg": None
                }
            else:
                return {
                    "status": False,
                    "msg": "Nginx 配置文件错误，清查！:{}".format(nginx_conf_test)
                }
        else:
            return {
                "status": True,
                "msg": None
            }
