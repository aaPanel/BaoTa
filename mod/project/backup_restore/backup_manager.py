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
import re

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

if '/www/server/panel' not in sys.path:
    sys.path.insert(0, '/www/server/panel')

import public
from mod.project.backup_restore.base_util import BaseUtil
from mod.project.backup_restore.data_manager import DataManager
from mod.project.backup_restore.config_manager import ConfigManager
# from .modules.base_module import BaseModule
from mod.project.backup_restore.modules.site_module import SiteModule
from mod.project.backup_restore.modules.database_module import DatabaseModule
from mod.project.backup_restore.modules.soft_module import SoftModule
from mod.project.backup_restore.modules.ftp_module import FtpModule
from mod.project.backup_restore.modules.crontab_module import CrontabModule
from mod.project.backup_restore.modules.ssh_module import SshModule
from mod.project.backup_restore.modules.firewall_module import FirewallModule
from mod.project.backup_restore.modules.plugin_module import PluginModule
from mod.project.backup_restore.modules.mail_module import MailModule
from mod.project.backup_restore.modules.node_module import NodeModule
from mod.project.backup_restore.modules.panelconfig_module import PanelConfigModule
# from .modules.database_module import DatabaseModule
# from .modules.ftp_module import FTPModule
# from .modules.terminal_module import TerminalModule
# from .modules.firewall_module import FirewallModule
# from .utils import print_log, get_file_sha256

class BackupManager(SiteModule,DatabaseModule,FtpModule,DataManager,BaseUtil,ConfigManager):
    def __init__(self):
    #    self._init_modules()
        self.base_path = '/www/backup/backup_restore'
        self.bakcup_task_json = self.base_path + '/backup_task.json'
        self.backup_log_file = self.base_path + '/backup.log'
        self.backup_pl_file = self.base_path + '/backup.pl'
        self.backup_success_file = self.base_path + '/success.pl'
        self.backup_save_config = self.base_path + '/backup_save_config.json'
        self.history_log_path = '/www/backup/backup_restore/history/log'
        self.history_info_path = '/www/backup/backup_restore/history/info'
        self.migrate_backup_info_path = '/www/backup/backup_restore/migrate_backup_info.json'
        self.backup_err_log_path = '/www/backup/backup_restore/backup_err.log'

    # def _init_modules(self):
    #     """初始化所有模块"""
    #     self.modules = {
    #         'site': SiteModule(self.config_manager),
    #         'database': DatabaseModule(self.config_manager),
    #         'ftp': FTPModule(self.config_manager),
    #         'terminal': TerminalModule(self.config_manager),
    #         'firewall': FirewallModule(self.config_manager)
    #     }
    
    def get_local_backup(self,get=None):
        backup_list=[]
        if os.path.exists(self.bakcup_task_json):
            backup_list=json.loads(public.ReadFile(self.bakcup_task_json))

        file_names = os.listdir(self.base_path)
        pattern = re.compile(r"\d{8}-\d{4}_\d+_backup\.tar\.gz")
        matched_files = [f for f in file_names if pattern.match(f)]
        for file in matched_files:
            if "upload.tmp" in file:
                continue
            file_timestamp = file.split('_')[1]
            matched = any(item["timestamp"] == int(file_timestamp) for item in backup_list)
            if not matched:
                done_time=datetime.datetime.fromtimestamp(int(file_timestamp)).strftime('%Y-%m-%d %H:%M:%S')
                file_size = public.ExecShell("du -sb /www/backup/backup_restore/{}".format(file))[0].split("\t")[0]
                file_conf={}
                file_conf['backup_name'] = str(file)
                file_conf['timestamp']=int(file_timestamp)
                file_conf['create_time'] = done_time
                file_conf['backup_time'] = done_time
                file_conf['backup_file'] = self.base_path + "/" + file
                file_conf['storage_type'] = "local"
                file_conf['auto_exit'] = 0
                file_conf['restore_status'] = 0
                file_conf['backup_status']  = 2
                file_conf['backup_path'] = self.base_path + "/" + file
                file_conf['done_time'] = done_time
                file_conf['backup_file_size'] = str(self.get_file_size(self.base_path + "/" + file))
                file_conf['backup_file_sha256'] = self.get_file_sha256(self.base_path + "/" + file)
                file_conf['backup_count'] = {}
                file_conf['backup_count']['success'] = None
                file_conf['backup_count']['failed'] = None
                file_conf['total_time']=None
                backup_list.append(file_conf)

        if os.path.exists(self.migrate_backup_info_path):
            migrate_backup_info=json.loads(public.ReadFile(self.migrate_backup_info_path))
            backup_list.append(migrate_backup_info)
            public.ExecShell("rm -f {}".format(self.migrate_backup_info_path))
                
        public.WriteFile(self.bakcup_task_json,json.dumps(backup_list))
        return backup_list
        #public.WriteFile(self.bakcup_task_json,json.dumps(backup_list))
        # for file_name in os.listdir(self.base_path):
        #     backup_file_path=self.base_path + "/" + file_name
        #     if backup_file_path.endswith(".tar.gz"):
        #         for backup_task in backup_list:
        #             if backup_task.get('backup_file') == backup_file_path:
        #                 continue
        #             else:
        #                 print(1)
        #                 stat_file = os.stat(backup_file_path)
        #                 file_data = {
        #                     "name": file_name,
        #                     "size": stat_file.st_size,
        #                     "timestamp": 123456789,
        #                     "backup_file": backup_file_path,
        #                     "backup_status": 2,
        #                     "backup_type": "local"
        #                 }
        #                 #backup_list.append(file_data)
        
        #print(backup_list)
        #return backup_list
    
    def get_backup_file_msg(self,timestamp):
        import tarfile
        backup_file=str(timestamp) + "_backup.tar.gz"
        print(backup_file)
        file_names = os.listdir(self.base_path)
        for file in file_names:
            if backup_file in file:
                backup_file=file
        path=self.base_path + "/" + backup_file
        path_data={}
        if not os.path.exists(path):
            return path_data
        try:
            with tarfile.open(path, 'r:gz') as tar:
                # 提前获取文件列表
                members = tar.getnames()
                # 提取备份 JSON 配置
                if '{}_backup/backup.json'.format(timestamp) in members:
                    json_file_name = '{}_backup/backup.json'.format(timestamp)
                    json_file = tar.extractfile(json_file_name)
                    json_content = json_file.read().decode('utf-8')
                    path_data['config'] = json.loads(json_content)

                # 提取备份日志文件
                if '{}_backup/backup.log'.format(timestamp) in members:
                    log_file_name = '{}_backup/backup.log'.format(timestamp)
                    log_file = tar.extractfile(log_file_name)
                    log_content = log_file.read().decode('utf-8')
                    path_data['log'] = log_content + path + "\n打包完成"
        except:
            return False
        
        # path_data['server_config']=self.get_server_config()
        # path_data['backup_path_size']=25256044
        # path_data['free_size'] = self.get_free_space()['free_space']


        self.history_log_path = '/www/backup/backup_restore/history/log'
        self.history_info_path = '/www/backup/backup_restore/history/info'
        if not os.path.exists(self.history_log_path):
            public.ExecShell("mkdir -p {}".format(self.history_log_path))
        if not os.path.exists(self.history_info_path):
            public.ExecShell("mkdir -p {}".format(self.history_info_path))
    
        try:
            public.WriteFile(self.history_log_path + "{}_backup.log".format(timestamp),path_data['log'])
        except: 
            pass
        try:
            public.WriteFile(self.history_info_path + "/{}_backup.info".format(timestamp),json.dumps(path_data['config']))
        except:
            return False
        
        try:
            backup_task_info=self.get_backup_conf(timestamp)
            hitory_info=json.loads(public.ReadFile(self.history_info_path + "/{}_backup.info".format(timestamp)))
            hitory_info['create_time']=backup_task_info['create_time']
            hitory_info['backup_time']=backup_task_info['backup_time']
            hitory_info['backup_file']=backup_task_info['backup_file']
            hitory_info['backup_path']=backup_task_info['backup_path']
            hitory_info['done_time']=backup_task_info['done_time']
            hitory_info['total_time']=backup_task_info['total_time']
            hitory_info['backup_file_size']=backup_task_info['backup_file_size']
            hitory_info['backup_file_sha256']=backup_task_info['backup_file_sha256']
            public.WriteFile(self.history_info_path + "/{}_backup.info".format(timestamp),json.dumps(hitory_info))
        except:
            pass

        #return path_data
        return True


    def add_backup_task(self,timestamp: int):
        backup_path=self.base_path + '/{timestamp}_backup/'.format(timestamp=timestamp)
        if not os.path.exists(backup_path):
            os.makedirs(backup_path)

        backup_conf=self.get_backup_conf(timestamp)
        if not backup_conf:
            print("备份配置文件不存在")
            return public.returnMsg(False, "备份配置文件不存在")
        backup_conf['data_list']={}
        backup_data_list=backup_conf['backup_data']
        if "soft" in backup_data_list:
            backup_conf['data_list']['soft']=SoftModule().get_soft_data(timestamp)
        else:
            backup_conf['data_list']['soft']={}

        backup_conf['data_list']['site']=self.get_site_backup_conf(timestamp)
        
        if "database" in backup_data_list:
            backup_conf['data_list']['database']=self.get_database_backup_conf(timestamp)
        else:
            backup_conf['data_list']['database']={}


        if "ftp" in backup_data_list:
            backup_conf['data_list']['ftp']=self.backup_ftp_data(timestamp)
        else:
            backup_conf['data_list']['ftp']={}
        backup_conf['backup_status']=1


        public.WriteFile(backup_path + 'backup.json',json.dumps(backup_conf))

    def backup_data(self,timestamp: int):
        if os.path.exists(self.backup_log_file):
            public.ExecShell("rm -f {}".format(self.backup_log_file))

        if os.path.exists(self.backup_pl_file):
            print("当前已有备份进程再运行！")
            return public.returnMsg(False, "当前已有备份进程再运行！")
        public.WriteFile(self.backup_pl_file,timestamp)

        backup_conf=self.get_backup_conf(timestamp)
        
        try:
            backup_data_list=backup_conf['backup_data']
        except:
            backup_data_list=[]
            backup_data_list.extend(["soft","site","database","wp_tools","ftp","crontab","vmail","ssh","firewall","node","plugin"])
            backup_conf['backup_data'] = backup_data_list
            backup_conf['database_id'] = '["ALL"]'
            backup_conf['site_id'] = '["ALL"]'
            self.save_backup_conf(timestamp,backup_conf)


        backup_conf['backup_status']=1
        self.save_backup_conf(timestamp,backup_conf)

        start_time=int(time.time())

        self.add_backup_task(timestamp)

        # 注释掉原来的代码
        # try:
        #     if "site" in backup_data_list:
        #         self.backup_site_data(timestamp)
        # except:
        #     pass
        # try:
        #     if "database" in backup_data_list:
        #         self.backup_database_data(timestamp)
        # except:
        #     pass
        # try:
        #     CrontabModule().backup_crontab_data(timestamp)
        # except:
        #     pass
        # try:
        #     SshModule().backup_ssh_data(timestamp)
        # except:
        #     pass
        # try:
        #     FirewallModule().backup_firewall_data(timestamp)
        # except:
        #     pass
        # try:
        #     MailModule().backup_vmail_data(timestamp)
        # except:
        #     pass
        # try:
        #     PluginModule().backup_plugin_data(timestamp)
        # except:
        #     pass
        # try:
        #     self.write_backup_data(timestamp)
        # except:
        #     pass


        # 新的循环实现
        for backup_type in backup_data_list:
            try:
                if backup_type == 'site':
                    print(1)
                    self.backup_site_data(timestamp)
                elif backup_type == 'database':
                    self.backup_database_data(timestamp)
                elif backup_type == 'crontab':
                    CrontabModule().backup_crontab_data(timestamp)
                elif backup_type == 'ssh':
                    SshModule().backup_ssh_data(timestamp)
                elif backup_type == 'firewall':
                    FirewallModule().backup_firewall_data(timestamp)
                elif backup_type == 'vmail':
                    MailModule().backup_vmail_data(timestamp)
                elif backup_type == 'plugin':
                    PluginModule().backup_plugin_data(timestamp)
                # elif backup_type == 'soft':
                #     self.backup_soft_data(timestamp)
                elif backup_type == 'wp_tools':
                    self.backup_wp_tools_data(timestamp)
                elif backup_type == 'ftp':
                    self.backup_ftp_data(timestamp)
                elif backup_type == 'node':
                    NodeModule().backup_node_data(timestamp)
            except Exception as e:
                public.WriteFile(self.backup_err_log_path,e)

        try:
            PanelConfigModule().backup_panel_config_data(timestamp)
        except:
            pass

        try:
            self.write_backup_data(timestamp)
        except:
            public.WriteFile(self.backup_err_log_path,e)



        end_time=int(time.time())
        done_time=datetime.datetime.fromtimestamp(int(end_time)).strftime('%Y-%m-%d %H:%M:%S')
        total_time=end_time - start_time

        backup_conf=self.get_backup_conf(timestamp)
        backup_conf['backup_status']=2
        backup_conf['done_time']=done_time
        backup_conf['total_time']=total_time
        
        self.save_backup_conf(timestamp,backup_conf)
        self.sync_backup_info(timestamp)

        public.WriteFile(self.backup_success_file,timestamp)
        public.ExecShell("rm -f {}".format(self.backup_pl_file))
        self.create_history_file(timestamp)

    def create_history_file(self,timestamp):
        if not os.path.exists(self.history_log_path):
            public.ExecShell("mkdir -p {}".format(self.history_log_path))
        if not os.path.exists(self.history_info_path):
            public.ExecShell("mkdir -p {}".format(self.history_info_path))

        hitory_log_file=self.history_log_path + '/' + str(timestamp) + '_backup.log'
        history_info_file=self.history_info_path + '/' + str(timestamp) + '_backup.info'
        public.WriteFile(hitory_log_file,public.ReadFile("/www/backup/backup_restore/backup.log".format(timestamp)))
        public.WriteFile(history_info_file,public.ReadFile("/www/backup/backup_restore/{}_backup/backup.json".format(timestamp)))

    def sync_backup_info(self,timestamp):
        backup_conf=self.get_backup_conf(timestamp)
        data_list=self.get_backup_data_list(timestamp)
        data_list['backup_status']=backup_conf['backup_status']
        data_list['backup_file']=backup_conf['backup_file']
        data_list['backup_file_sha256']=backup_conf['backup_file_sha256']
        data_list['backup_file_size']=backup_conf['backup_file_size']
        data_list['done_time']=backup_conf['done_time']
        data_list['total_time']=backup_conf['total_time']
        data_list['backup_count']=backup_conf['backup_count']
        self.update_backup_data_list(timestamp, data_list)

    def count_backup_status(self,data,status_code):
        return sum(
            1 for category in data.values()
            for item in category
            if isinstance(item, dict) and item.get('status') == status_code
        )
    
    def write_backup_data(self,timestamp):
        self.print_log("====================================================","backup")
        self.print_log("开始压缩打包所有数据","backup")
        from datetime import datetime
        # timestamp=get.timestamp
        backup_conf=self.get_backup_conf(timestamp)


        backup_log_path=self.base_path + str(timestamp) + "_backup/"
        public.ExecShell('\cp -rpa {} {}'.format(self.backup_log_file,backup_log_path))

        conf_data=json.loads((public.ReadFile("/www/backup/backup_restore/{}_backup/backup.json".format(timestamp))))
        status_2_count = self.count_backup_status(conf_data['data_list'], 2)
        status_3_count = self.count_backup_status(conf_data['data_list'], 3)

        dt_object = datetime.fromtimestamp(int(timestamp))
        file_time = dt_object.strftime('%Y%m%d-%H%M')
        tar_file_name = file_time + "_" + str(timestamp) + "_backup.tar.gz"
        conf_data['backup_status']=1
        public.WriteFile("/www/backup/backup_restore/{}_backup/backup.json".format(timestamp),json.dumps(conf_data))
        
        public.ExecShell("cd /www/backup/backup_restore && tar -czvf {} {}_backup".format(tar_file_name,timestamp))
        file_size = public.ExecShell("du -sb /www/backup/backup_restore/{}".format(tar_file_name))[0].split("\t")[0]

        time.sleep(1)
        #public.ExecShell("rm -rf /www/backup/backup_restore/{}_backup".format(timestamp))
        
        backup_conf["backup_status"] = 2
        backup_conf["backup_file"] = "/www/backup/backup_restore/" + tar_file_name
        backup_conf["backup_file_sha256"] = self.get_file_sha256("/www/backup/backup_restore/" + tar_file_name)
        backup_conf["backup_file_size"] = file_size
        backup_conf["backup_count"]={}
        backup_conf["backup_count"]['success'] = status_2_count
        backup_conf["backup_count"]['failed'] = status_3_count
        storage_type=backup_conf['storage_type']
        print(backup_conf)
        
        backup_size=self.format_size(int(file_size))
        self.print_log("压缩打包所有数据完成 数据大小：{}".format(backup_size),'backup')
        self.print_log("====================================================","backup")
        

        tar_file_name= "/www/backup/backup_restore/" + tar_file_name
        if storage_type != "local" and os.path.exists(tar_file_name):
            from CloudStoraUpload import CloudStoraUpload
            _cloud = CloudStoraUpload()
            _cloud.run(storage_type)
            cloud_name_cn = _cloud.obj._title
            if not _cloud.obj:
                return False
            self.print_log("正在上传备份文件到{}...".format(cloud_name_cn),"backup")
            try:
                backup_path = _cloud.obj.backup_path
                if not backup_path.endswith('/'):
                    backup_path += '/'
                upload_path = os.path.join(backup_path, "backup_restore", os.path.basename(tar_file_name))
                if _cloud.cloud_upload_file(tar_file_name, upload_path):
                    self.print_log(f"已成功上传到{cloud_name_cn}","backup")
            except Exception as e:
                self.print_log(f"上传到{cloud_name_cn}时发生错误: {str(e)}","backup")

        self.save_backup_conf(timestamp,backup_conf)


    def add_backup(self, timestamp: int) -> dict:
        """添加备份任务"""
        try:
            backup_config = self.config_manager.get_backup_config()
            timestamp = int(time.time())
        except:
            pass

    def test_get(self,get=None):
        result = self.get_backup_progress()
        print(result)

    def get_backup_progress(self, get=None):
        """
        获取备份进度信息
        @param get: object 包含请求参数
        @return: dict 备份进度信息
        """
        # 设置相关文件路径
        backup_pl_file = self.base_path + '/backup.pl'
        backup_log_file = self.base_path + '/backup.log'
        backup_success_file = self.base_path + '/success.pl'
        
        # 创建处理已完成备份的函数，减少代码重复
        def create_completed_result(backup_timestamp):
            if not backup_timestamp:
                return public.ReturnMsg(False, "备份完成但无法获取备份时间戳")
            
            if not os.path.exists(self.bakcup_task_json):
                return public.ReturnMsg(False, "备份配置文件不存在")
                
            backup_configs = json.loads(public.ReadFile(self.bakcup_task_json))
            success_data = next((item for item in backup_configs if str(item.get('timestamp')) == str(backup_timestamp)), {})
            err_info =[]
            # in_err={}
            # in_err['name']="php"
            # in_err['type']="环境"
            # in_err['msg']="缺少gd依赖库"
            # err_info.append(in_err)
            return {
                "task_type": "backup",
                "task_status": 2,
                "backup_data": None,
                "backup_name": None,
                "data_backup_status": 2,
                "progress": 100,
                "msg": None,
                'task_msg': None,
                'exec_log': public.ReadFile(backup_log_file) if os.path.exists(backup_log_file) else "",
                'timestamp': backup_timestamp,
                'backup_file_info': success_data,
                'err_info': err_info
            }
        
        # 检查备份是否已完成
        if os.path.exists(backup_success_file):
            success_time = int(os.path.getctime(backup_success_file))
            local_time = int(time.time()) 
            # 如果success文件创建时间在10秒内，说明备份刚刚完成
            if success_time + 10 > local_time:
                try:
                    backup_timestamp = public.ReadFile(backup_success_file).strip()
                    return public.ReturnMsg(True,create_completed_result(backup_timestamp))
                except Exception as e:
                    public.ExecShell("rm -f {}".format(backup_success_file))
                    return public.ReturnMsg(False, f"获取备份完成信息出错: {str(e)}")
            else:
                # 超过10秒，删除success文件
                public.ExecShell("rm -f {}".format(backup_success_file))
        
        # 检查是否有备份进程运行
        timestamp = ""
        try:
            # 检查备份进程锁文件
            if os.path.exists(backup_pl_file):
                timestamp = public.ReadFile(backup_pl_file).strip()
                if not timestamp:
                    return public.ReturnMsg(False, "备份进程正在运行，但无法获取备份时间戳")
            else:
                # 等待2秒，可能是备份刚刚完成
                time.sleep(2)
                if os.path.exists(backup_success_file):
                    success_time = int(os.path.getctime(backup_success_file))
                    local_time = int(time.time()) 
                    if success_time + 10 > local_time:
                        backup_timestamp = public.ReadFile(backup_success_file).strip()
                        return public.ReturnMsg(True,create_completed_result(backup_timestamp))
                
                # 再次检查是否有备份进程
                if os.path.exists(backup_pl_file):
                    timestamp = public.ReadFile(backup_pl_file).strip()
                    if not timestamp:
                        return public.ReturnMsg(False, "备份进程正在运行，但无法获取备份时间戳")
                else:
                    return public.ReturnMsg(False, "当前未找到备份任务，请在备份列表中查看是否备份完成")
            
            # 读取备份配置文件
            backup_json_path = f"{self.base_path}/{timestamp}_backup/backup.json"
            if not os.path.exists(backup_json_path):
                return public.ReturnMsg(False, f"备份配置文件不存在: {backup_json_path}")
            
            conf_data = json.loads(public.ReadFile(backup_json_path))
        except Exception as e:
            return public.ReturnMsg(False, f"获取备份进度信息出错: {str(e)}")
        
        # 读取备份日志
        backup_log_data = public.ReadFile(backup_log_file) if os.path.exists(backup_log_file) else ""
        
        # 定义备份类型及其处理逻辑
        backup_types = [
            {
                'type': 'site',
                'data_key': 'site',
                'display_name': '站点',
                'progress': 30
            },
            {
                'type': 'database',
                'data_key': 'database',
                'display_name': '数据库',
                'progress': 60
            },
            {
                'type': 'ftp',
                'data_key': 'ftp',
                'display_name': 'FTP用户',
                'progress': 70
            },
            {
                'type': 'terminal',
                'data_key': 'terminal',
                'display_name': '终端数据',
                'progress': 75
            },
            {
                'type': 'firewall',
                'data_key': 'firewall',
                'display_name': '防火墙规则',
                'progress': 80
            }
        ]
        
        # 检查各类型备份进度
        for backup_type in backup_types:
            items = conf_data.get("data_list", {}).get(backup_type['data_key'], [])
            for item in items:
                try:
                    if item.get("status") == 2:
                        continue
                        
                    name = item.get("name", f"未知{backup_type['display_name']}")
                    return public.ReturnMsg(True,{
                        "task_type": "backup",
                        "task_status": 1,
                        "data_type": backup_type['type'],
                        "name": name,
                        "data_backup_status": item.get("status", 0),
                        "progress": backup_type['progress'],
                        "msg": item.get("msg"),
                        'task_msg': f"当前正在备份{backup_type['display_name']} {name}",
                        'exec_log': backup_log_data,
                        'timestamp': timestamp
                    })
                except:
                     return public.ReturnMsg(True,{
                        "task_type": "backup",
                        "task_status": 1,
                        "data_type": "服务器配置",
                        "name": "服务器配置",
                        "data_backup_status": 1,
                        "progress": 80,
                        "msg": "正在备份服务器配置",
                        'task_msg': f"当前正在备份各项服务器配置",
                        'exec_log': backup_log_data,
                        'timestamp': timestamp
                    })
        
        # 检查数据打包进度
        try:
            backup_status = conf_data.get('backup_status')
            if backup_status == 1:
                return public.ReturnMsg(True,{
                        "task_type": "backup",
                        "task_status": 1,
                        "data_type": "tar",
                        "name": "数据打包",
                        "data_backup_status": 1,
                        "progress": 90,
                        'task_msg': "当前正在压缩数据包",
                        'exec_log': backup_log_data,
                        'timestamp': timestamp
                })
        except Exception:
            # 可能没有backup_status字段，继续处理
            pass
        
        # 如果没有发现进行中的任务，但有备份进程
        if timestamp:
            return {
                "backup_data": "unknown",
                "backup_name": "未知任务",
                "data_backup_status": 1,
                "progress": 10,
                'backup_msg': "正在准备备份数据",
                'backup_log': backup_log_data,
                'timestamp': timestamp
            }
        return public.ReturnMsg(False, "当前未找到正在进行的备份任务，请在备份列表中查看是否备份完成")
    
    
    def get_backup_details(self, timestamp):
        history_info_file = self.history_info_path + '/' + str(timestamp) + '_backup.info'
        if not os.path.exists(history_info_file):
            get_info=self.get_backup_file_msg(timestamp)
            if not get_info:
                return {
                    "status": False,
                    "msg": "获取详情失败",
                    "error_msg": "备份信息文件不存在",
                    "data": {}
                }
        # try:
        backup_info = json.loads(public.ReadFile(history_info_file))
        try:
            disk_use = int(backup_info.get("backup_file_size", 0)) * 2
        except:
            disk_use = backup_info.get("backup_file_size", 0)
        
        # 提取基本信息
        result = {
            "status": True,
            "msg": "获取详情成功",
            "error_msg": "",
            "data": {
                "type": "backup",
                "done_time": backup_info.get("done_time", ""),
                "total_time": backup_info.get("total_time", 0),
                "backup_file": backup_info.get("backup_file", ""),
                "backup_file_size": backup_info.get("backup_file_size", "0"),
                "backup_file_sha256": backup_info.get("backup_file_sha256", ""),
                "disk_use": disk_use,
                "disk_free": BaseUtil.get_free_space(self)['free_space'],
                "data_status": {
                    "env_list": [],
                    "site_list": [],
                    "database_list": [],
                    "ftp_list": [],
                    "crontab_list": {},
                    "ssh_list": {},
                    "firewall_list": {},
                    "plugin_list": [],
                    "vmail_list": [],
                    "btnode_list": [],
                    "soft_data": []
                }
            }
        }
        
        # 处理软件列表
        if "soft" in backup_info['data_list']:
            soft_data = backup_info["data_list"]["soft"]
            soft_list = []
            
            # 处理Web服务器
            if "web_server" in soft_data and soft_data["web_server"]:
                soft_list.append({
                    "name": soft_data["web_server"].get("name", ""),
                    "version": soft_data["web_server"].get("version", ""),
                    "size": soft_data["web_server"].get("size", 0)
                })
            
            # 处理PHP版本
            if "php_server" in soft_data and soft_data["php_server"]:
                for php in soft_data["php_server"]:
                    soft_list.append({
                        "name": php.get("name", ""),
                        "version": php.get("version", ""),
                        "size": php.get("size", 0)
                    })
            
            # 处理MySQL服务器
            if "mysql_server" in soft_data and soft_data["mysql_server"]:
                soft_list.append({
                    "name": soft_data["mysql_server"].get("type", "mysql"),
                    "version": soft_data["mysql_server"].get("version", ""),
                    "size": soft_data["mysql_server"].get("size", 0)
                })
            
            # 处理FTP服务器
            if "ftp_server" in soft_data and soft_data["ftp_server"]:
                soft_list.append({
                    "name": soft_data["ftp_server"].get("name", ""),
                    "version": soft_data["ftp_server"].get("version", ""),
                    "size": soft_data["ftp_server"].get("size", 0)
                })
            
            # 处理JDK列表
            if "jdk_list" in soft_data and soft_data["jdk_list"]:
                for jdk in soft_data["jdk_list"]:
                    soft_list.append({
                        "name": jdk.get("name", ""),
                        "version": jdk.get("version", ""),
                        "size": jdk.get("size", 0)
                    })
            
            # 处理Node列表
            if "node_list" in soft_data and soft_data["node_list"]:
                for node in soft_data["node_list"]:
                    soft_list.append({
                        "name": node.get("name", ""),
                        "version": node.get("version", ""),
                        "size": node.get("size", 0)
                    })
            
            # 处理Tomcat列表
            if "tomcat_list" in soft_data and soft_data["tomcat_list"]:
                for tomcat in soft_data["tomcat_list"]:
                    soft_list.append({
                        "name": tomcat.get("name", ""),
                        "version": tomcat.get("version", ""),
                        "size": tomcat.get("size", 0)
                    })
            
            # 处理Redis服务器
            if "redis_server" in soft_data and soft_data["redis_server"]:
                soft_list.append({
                    "name": soft_data["redis_server"].get("name", ""),
                    "version": soft_data["redis_server"].get("version", ""),
                    "size": soft_data["redis_server"].get("size", 0)
                })
            
            # 处理Memcached服务器
            if "memcached_server" in soft_data and soft_data["memcached_server"]:
                soft_list.append({
                    "name": soft_data["memcached_server"].get("name", ""),
                    "version": soft_data["memcached_server"].get("version", ""),
                    "size": soft_data["memcached_server"].get("size", 0)
                })
            
            # 处理MongoDB服务器
            if "mongodb_server" in soft_data and soft_data["mongodb_server"]:
                soft_list.append({
                    "name": soft_data["mongodb_server"].get("name", ""),
                    "version": soft_data["mongodb_server"].get("version", ""),
                    "size": soft_data["mongodb_server"].get("size", 0)
                })
            
            # 处理PostgreSQL服务器
            if "pgsql_server" in soft_data and soft_data["pgsql_server"]:
                soft_list.append({
                    "name": soft_data["pgsql_server"].get("name", ""),
                    "version": soft_data["pgsql_server"].get("version", ""),
                    "size": soft_data["pgsql_server"].get("size", 0)
                })
            
            # 处理phpMyAdmin
            if "phpmyadmin_version" in soft_data and soft_data["phpmyadmin_version"]:
                soft_list.append({
                    "name": soft_data["phpmyadmin_version"].get("name", ""),
                    "version": soft_data["phpmyadmin_version"].get("version", ""),
                    "size": soft_data["phpmyadmin_version"].get("size", 0)
                })
            
            # 添加到结果中
            result["data"]["data_status"]["soft_data"] = soft_list

            # 添加软件数据到环境列表
            for soft in soft_list:
                result["data"]["data_status"]["env_list"].append({
                    "name": soft.get("name", ""),
                    "version": soft.get("version", ""),
                    "size": soft.get("size", 0),
                    "status": 2,
                    "err_msg": None
                })
        
        # 处理网站列表
        if "data_list" in backup_info and "site" in backup_info["data_list"]:
            for site in backup_info["data_list"]["site"]:
                result["data"]["data_status"]["site_list"].append({
                    "name": site.get("name", ""),
                    "type": site.get("project_type", ""),
                    "size": site.get("size", 0),
                    "status": site.get("status", 0),
                    "err_msg": site.get("msg", None)
                })
        
        # 处理数据库列表
        if "data_list" in backup_info and "database" in backup_info["data_list"]:
            for db in backup_info["data_list"]["database"]:
                result["data"]["data_status"]["database_list"].append({
                    "name": db.get("name", ""),
                    "type": db.get("type", ""),
                    "size": db.get("size", 0),
                    "status": db.get("status", 0),
                    "err_msg": db.get("msg", None)
                })
        
        # 处理FTP列表
        if "data_list" in backup_info and "ftp" in backup_info["data_list"]:
            for ftp in backup_info["data_list"]["ftp"]:
                result["data"]["data_status"]["ftp_list"].append({
                    "name": ftp.get("name", ""),
                    "size": ftp.get("size", 0),
                    "status": ftp.get("status", 0),
                    "err_msg": ftp.get("msg", None)
                })
        
        # 处理计划任务
        if "data_list" in backup_info and "crontab" in backup_info["data_list"]:
            crontab_data = backup_info["data_list"]["crontab"]
            try:
                if crontab_data["crontab_json"]:
                    if os.path.exists(crontab_data["crontab_json"]):
                        crontab_data["crontab_json"] = json.loads(public.ReadFile(crontab_data["crontab_json"]))
                    crontab_list=[]
                    for crontab in crontab_data["crontab_json"]:
                        crontab_list.append({
                            "name": crontab.get("name", ""),
                            "size": crontab.get("id", 0),
                            "status": 2,
                            "err_msg": None
                        })
                    result["data"]["data_status"]["crontab_list"] = crontab_list
            except:
                result["data"]["data_status"]["crontab_list"] = {
                    "crontab_count": 0,
                    "crontab_size": 0,  
                    "status": 2,
                    "err_msg": None
                }
        
        # 处理SSH列表
        if "data_list" in backup_info and "ssh" in backup_info["data_list"]:
            ssh_data = backup_info["data_list"]["ssh"]
            result["data"]["data_status"]["ssh_list"] = {
                "ssh_size": ssh_data.get("ssh_size", 0),
                "command_size": ssh_data.get("command_size", 0),
                "status": 2,
                "err_msg": None
            }
        
        # 处理防火墙列表
        if "data_list" in backup_info and "firewall" in backup_info["data_list"]:
            firewall_data = backup_info["data_list"]["firewall"]
            result["data"]["data_status"]["firewall_list"] = {
                "port_size": firewall_data.get("firewall_forward", 0),
                "ip_rule_size": firewall_data.get("firewall_ip", 0),
                "status": 2,
                "err_msg": None
            }
        
        # 处理插件列表
        if "data_list" in backup_info and "plugin" in backup_info["data_list"]:
            plugin_data = backup_info["data_list"]["plugin"]
            # 检查插件数据格式
            if isinstance(plugin_data, dict):
                # 新格式：{"plugin_name": {"status": x, "err_msg": y}}
                for plugin_name, plugin_info in plugin_data.items():
                    display_name = self.get_plugin_display_name(plugin_name)
                    plugin_item = {
                        "name": display_name,
                        "display_name": display_name,
                        "size": plugin_info.get("size", 0),
                        "status": plugin_info.get("status", 2),
                        "err_msg": plugin_info.get("err_msg", None)
                    }
                    result["data"]["data_status"]["plugin_list"].append(plugin_item)
            else:
                # 旧格式：[{"name": x, "size": y}]
                for plugin in plugin_data:
                    plugin_name = plugin.get("name", "")
                    display_name = self.get_plugin_display_name(plugin_name)
                    result["data"]["data_status"]["plugin_list"].append({
                        "name": display_name,
                        "display_name": display_name,
                        "size": plugin.get("size", 0),
                        "status": 2,
                        "err_msg": None
                    })
        if "data_list" in backup_info and "vmail" in backup_info["data_list"]:
            vmail_data = backup_info["data_list"]["vmail"]
            
            result["data"]["data_status"]["vmail_list"].append({
                "name": "邮局数据",
                "vmail_size": vmail_data.get("size", 0),
                "status": 2,
                "err_msg": None
            })
            
        if "data_list" in backup_info and "node" in backup_info["data_list"]:
            node_data = backup_info["data_list"]["node"]["node_list"]
            for node in node_data:
                result["data"]["data_status"]["btnode_list"].append({
                    "name": node.get("name", ""),
                    "server_ip": node.get("server_ip", ""),
                    "status": 2,
                    "err_msg": None
                })
        return result
        # except Exception as e:
        #     return {
        #         "status": False,
        #         "msg": "获取详情失败",
        #         "error_msg": str(e),
        #         "data": {}
        #     }
        
    def get_backup_log(self,timestamp):
        backup_log_file = self.base_path + '/backup.log'
        history_log_file=self.history_log_path + '/' + str(timestamp) + '_backup.log'
        if os.path.exists(self.backup_pl_file):
            backup_timestamp=int(public.ReadFile(self.backup_pl_file))
            if int(backup_timestamp) == int(timestamp):
                return public.ReadFile(backup_log_file)
        if os.path.exists(history_log_file):
            return public.ReadFile(history_log_file)
        else:
            return None

    def get_plugin_display_name(self, plugin_name):
        """获取插件的显示名称"""
        plugin_display_names = {
            "btwaf": "nginx防火墙",
            "monitor": "网站监控报表",
            "tamper_core": "企业级防篡改",
            "syssafe": "系统加固"
        }
        return plugin_display_names.get(plugin_name, plugin_name)

if __name__ == '__main__':
    # 获取命令行参数
    if len(sys.argv) < 3:
        print("Usage: btpython backup_manager.py <method> <timestamp>")
        sys.exit(1)
    method_name = sys.argv[1]  # 方法名
    timestamp = sys.argv[2]    # IP地址     
    backup_manager = BackupManager()  # 实例化对象
    if hasattr(backup_manager, method_name):  # 检查方法是否存在
        method = getattr(backup_manager, method_name)  # 获取方法
        method(timestamp)  # 调用方法
    else:
        print(f"Error: 方法 '{method_name}' 不存在")