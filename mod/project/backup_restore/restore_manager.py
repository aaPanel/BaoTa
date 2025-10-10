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

class RestoreManager(SiteModule,DatabaseModule,FtpModule,DataManager,BaseUtil,ConfigManager):
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
        self.restore_log_file = self.base_path + '/restore.log'
        self.restore_pl_file = self.base_path + '/restore.pl'
        self.restore_success_file = self.base_path + '/restore_success.pl'
        self.migrate_backup_info_path = '/www/backup/backup_restore/migrate_backup_info.json'
    
    def restore_data(self,timestamp):
        if os.path.exists(self.restore_log_file):
            public.ExecShell("rm -f {}".format(self.restore_log_file))

        if os.path.exists(self.restore_pl_file):
            print("当前已有还原进程再运行！")
            return public.returnMsg(False, "当前已有还原进程再运行！")

        public.WriteFile(self.restore_pl_file,timestamp)

        backup_file=str(timestamp) + "_backup.tar.gz"
        file_names = os.listdir(self.base_path)
        for file in file_names:
            if backup_file in file:
                backup_file=file

        if os.path.exists(self.migrate_backup_info_path):
            backup_list=[]
            if os.path.exists(self.bakcup_task_json):
                backup_list = json.loads(public.ReadFile(self.bakcup_task_json))
            migrate_backup_info=json.loads(public.ReadFile(self.migrate_backup_info_path))
            backup_list.append(migrate_backup_info)
            public.ExecShell("rm -f {}".format(self.migrate_backup_info_path))
            public.WriteFile(self.bakcup_task_json,json.dumps(backup_list))
            time.sleep(1)


        backup_conf=self.get_backup_conf(timestamp)
        backup_conf['restore_status']=1
        self.save_backup_conf(timestamp,backup_conf)

        self.print_log("==================================","restore")
        self.print_log("开始解压数据包","restore")
        if not os.path.exists(self.base_path + "/{timestamp}_backup".format(timestamp=timestamp)):
            public.ExecShell("cd {}/ && tar -xvf {}".format(self.base_path,backup_file))
        restore_data_path=self.base_path + "/{timestamp}_backup".format(timestamp=timestamp)

        public.ExecShell("\cp -rpa {}/backup.json {}/restore.json".format(restore_data_path,restore_data_path))
        restore_info=self.get_restore_data_list(timestamp)
        restore_info['restore_status']=1
        self.update_restore_data_list(timestamp, restore_info)

        backup_conf=self.get_backup_conf(timestamp)
        try:
            backup_data_list=backup_conf['backup_data']
        except:
            backup_data_list=["soft","site","database","ftp","crontab","ssh","firewall","vmail","node","plugin"]

        start_time=int(time.time())


        self.print_log("开始还原数据","restore")

        try:
            PanelConfigModule().restore_panel_config_data(timestamp)
        except:
            pass

        if "soft" in backup_data_list:
            try:
                SoftModule().restore_env(timestamp)
            except:
                pass
        if "site" in backup_data_list:
            try:
                self.restore_site_data(timestamp)
            except:
                pass
        if "ftp" in backup_data_list:
            try:
                self.restore_ftp_data(timestamp)
            except:
                pass
        if "database" in backup_data_list:
            try:
                self.restore_database_data(timestamp)
            except:
                pass
        if "crontab" in backup_data_list:
            try:
                CrontabModule().restore_crontab_data(timestamp)
            except:
                pass
        if "ssh" in backup_data_list:
            try:
                SshModule().restore_ssh_data(timestamp)
            except:
                pass
        if "firewall" in backup_data_list:
            try:
                FirewallModule().restore_firewall_data(timestamp)
            except:
                pass
        if "vmail" in backup_data_list:
            try:
                MailModule().restore_vmail_data(timestamp)
            except:
                pass
        if "node" in backup_data_list:
            try:
                NodeModule().restore_node_data(timestamp)
            except:
                pass
        if "plugin" in backup_data_list:
            try:
                PluginModule().restore_plugin_data(timestamp)
            except:
                pass
        end_time=int(time.time())
        done_time=datetime.datetime.fromtimestamp(int(end_time)).strftime('%Y-%m-%d %H:%M:%S')
        total_time=end_time - start_time


        backup_conf=self.get_backup_conf(timestamp)
        backup_conf['restore_status']=2
        backup_conf['restore_done_time']=done_time
        backup_conf['restore_total_time']=total_time
        self.save_backup_conf(timestamp,backup_conf)

        restore_info['restore_status']=2
        restore_info['restore_done_time']=done_time
        restore_info['restore_total_time']=total_time
        self.update_restore_data_list(timestamp, restore_info)

        self.print_log("==================================","restore")
        self.print_log("数据还原完成","restore")

        public.WriteFile(self.restore_success_file,timestamp)
        public.ExecShell("rm -f {}".format(self.restore_pl_file))
        if not os.path.exists(self.history_log_path):
            public.ExecShell("mkdir -p {}".format(self.history_log_path))
        if not os.path.exists(self.history_info_path):
            public.ExecShell("mkdir -p {}".format(self.history_info_path))

        hitory_log_file=self.history_log_path + '/' + str(timestamp) + '_restore.log'
        history_info_file=self.history_info_path + '/' + str(timestamp) + '_restore.info'
        public.WriteFile(hitory_log_file,public.ReadFile("/www/backup/backup_restore/restore.log".format(timestamp)))
        public.WriteFile(history_info_file,public.ReadFile("/www/backup/backup_restore/{}_backup/restore.json".format(timestamp)))
        if os.path.exists("/www/server/panel/data/migration.pl"):
            public.ExecShell("rm -f /www/server/panel/data/migration.pl")

        #删除备份数据
        time.sleep(1)
        public.ExecShell("rm -rf /www/backup/backup_restore/{}_backup".format(timestamp))

        #重启面板
        public.ExecShell("/etc/init.d/bt restart")

    
    def get_restore_log(self,timestamp):
        restore_log_file = self.base_path + '/restore.log'
        history_log_file=self.history_log_path + '/' + str(timestamp) + '_restore.log'
        if os.path.exists(self.restore_pl_file):
            restore_timestamp=int(public.ReadFile(self.restore_pl_file))
            if int(restore_timestamp) == int(timestamp):
                return public.ReadFile(restore_log_file)
        if os.path.exists(history_log_file):
            return public.ReadFile(history_log_file)
        else:
            return None
            return public.ReadFile(restore_log_file)

    def get_restore_progress(self, get=None):
        """
        获取还原进度信息
        @param get: object 包含请求参数
        @return: dict 还原进度信息
        """
        # 设置相关文件路径
        restore_pl_file = self.base_path + '/restore.pl'
        restore_log_file = self.base_path + '/restore.log'
        restore_success_file = self.base_path + '/restore_success.pl'
        
        # 创建处理已完成备份的函数，减少代码重复
        def create_completed_result(restore_timestamp):
            if not restore_timestamp:
                return public.ReturnMsg(False, "还原完成但无法获取还原时间戳")
            
            if not os.path.exists(self.bakcup_task_json):
                return public.ReturnMsg(False, "还原配置文件不存在")
                
            restore_configs = json.loads(public.ReadFile(self.bakcup_task_json))
            success_data = next((item for item in restore_configs if str(item.get('timestamp')) == str(restore_timestamp)), {})
            
            return {
                "task_type": "restore",
                "task_status": 2,
                "backup_data": None,
                "backup_name": None,
                "data_backup_status": 2,
                "progress": 100,
                "msg": None,
                'task_msg': None,
                'exec_log': public.ReadFile(restore_log_file) if os.path.exists(restore_log_file) else "",
                'timestamp': restore_timestamp,
                'backup_file_info': success_data
            }
        
        # 检查备份是否已完成
        if os.path.exists(restore_success_file):
            success_time = int(os.path.getctime(restore_success_file))
            local_time = int(time.time()) 
            # 如果success文件创建时间在10秒内，说明备份刚刚完成
            if success_time + 10 > local_time:
                try:
                    restore_timestamp = public.ReadFile(restore_success_file).strip()
                    return public.ReturnMsg(True,create_completed_result(restore_timestamp))
                except Exception as e:
                    public.ExecShell("rm -f {}".format(restore_success_file))
                    return public.ReturnMsg(False, f"获取还原完成信息出错: {str(e)}")
            else:
                # 超过10秒，删除success文件
                public.ExecShell("rm -f {}".format(restore_success_file))
        
        # 检查是否有备份进程运行
        timestamp = ""
        try:
            # 检查备份进程锁文件
            if os.path.exists(restore_pl_file):
                timestamp = public.ReadFile(restore_pl_file).strip()
                if not timestamp:
                    return public.ReturnMsg(False, "还原进程正在运行，但无法获取还原时间戳")
            else:
                # 等待2秒，可能是还原刚刚完成
                time.sleep(2)
                if os.path.exists(restore_success_file):
                    success_time = int(os.path.getctime(restore_success_file))
                    local_time = int(time.time()) 
                    if success_time + 10 > local_time:
                        restore_timestamp = public.ReadFile(restore_success_file).strip()
                        return public.ReturnMsg(True,create_completed_result(restore_timestamp))
                
                # 再次检查是否有备份进程
                if os.path.exists(restore_success_file):
                    timestamp = public.ReadFile(restore_success_file).strip()
                    if not timestamp:
                        return public.ReturnMsg(False, "还原进程正在运行，但无法获取还原时间戳")
                else:
                    return public.ReturnMsg(False, "当前未找到还原任务，请在还原列表中查看是否还原完成")
            
            # 读取备份配置文件
            restore_json_path = f"{self.base_path}/{timestamp}_backup/restore.json"
            if not os.path.exists(restore_json_path):
                return public.ReturnMsg(False, f"还原配置文件不存在: {restore_json_path}")
            
            conf_data = json.loads(public.ReadFile(restore_json_path))
        except Exception as e:
            return public.ReturnMsg(False, f"获取还原进度信息出错: {str(e)}")
        
        # 读取备份日志
        restore_log_data = public.ReadFile(restore_log_file) if os.path.exists(restore_log_file) else ""
        
        # 定义备份类型及其处理逻辑
        restore_types = [
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
                'type': 'ssh',
                'data_key': 'ssh',
                'display_name': '终端数据',
                'progress': 75
            },
            {
                'type': 'firewall',
                'data_key': 'firewall',
                'display_name': '防火墙规则',
                'progress': 90
            }
        ]
        
        # 检查软件环境状态
        if "data_list" in conf_data and "soft" in conf_data["data_list"]:
            soft_data = conf_data["data_list"]["soft"]
            if "status" in soft_data and soft_data["status"].get("status") == 1:
                name = soft_data["status"].get("name", "未知软件")
                version = soft_data["status"].get("version", "未知版本")
                return public.ReturnMsg(True, {
                    "task_type": "restore",
                    "task_status": 1,
                    "data_type": "soft",
                    "name": name,
                    "data_backup_status": 1,
                    "progress": 20,
                    "msg": soft_data["status"].get("err_msg"),
                    'task_msg': f"当前正在还原运行环境 {name}-{version}",
                    'exec_log': restore_log_data,
                    'timestamp': timestamp
                })
        
        # 检查各类型备份进度
        for restore_type in restore_types:
            items = conf_data.get("data_list", {}).get(restore_type['data_key'], [])
            for item in items:
                try:
                    if item.get("restore_status") == 2:
                        continue

                    name = item.get("name", f"未知{restore_type['display_name']}")
                    return public.ReturnMsg(True,{
                        "task_type": "restore",
                        "task_status": 1,
                        "data_type": restore_type['type'],
                        "name": name,
                        "data_backup_status": item.get("status", 0),
                        "progress": restore_type['progress'],
                        "msg": item.get("msg"),
                        'task_msg': f"当前正在还原{restore_type['display_name']} {name}",
                        'exec_log': restore_log_data,
                        'timestamp': timestamp
                    })
                except:
                    #name = item.get("name", f"{restore_type['display_name']}")
                    return public.ReturnMsg(True,{
                        "task_type": "restore",
                        "task_status": 1,
                        "data_type": "服务器配置",
                        "name": "服务器配置",
                        "data_backup_status": 2,
                        "progress": 90,
                        "msg": None,
                        'task_msg': f"当前正在还原服务器各项配置",
                        'exec_log': restore_log_data,
                        'timestamp': timestamp
                    })

        
        # 检查数据打包进度
        try:
            restore_status = conf_data.get('restore_status')
            if restore_status == 1:
                return public.ReturnMsg(True,{
                        "task_type": "restore",
                        "task_status": 1,
                        "data_type": "tar",
                        "name": "数据解压",
                        "data_backup_status": 1,
                        "progress": 10,
                        'task_msg': "当前正在解压数据包",
                        'exec_log': restore_log_data,
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
                'backup_msg': "正在准备还原数据",
                'backup_log': restore_log_data,
                'timestamp': timestamp
            }
        
        return public.ReturnMsg(False, "当前未找到正在进行的还原任务，请在还原列表中查看是否还原完成")
    

    def get_restore_details(self, timestamp):
        history_info_file = self.history_info_path + '/' + str(timestamp) + '_restore.info'
        if not os.path.exists(history_info_file):
            #get_info=self.get_backup_file_msg(timestamp)
            #if not get_info:
            return {
                "status": False,
                "msg": "获取详情失败",
                "error_msg": "还原信息文件不存在",
                "data": {}
            }
        # try:
        backup_info = json.loads(public.ReadFile(history_info_file))
        backup_task_info=self.get_backup_conf(timestamp)

        backup_info['backup_file_size']=backup_task_info['backup_file_size']
        backup_info['backup_file_sha256']=backup_task_info['backup_file_sha256']
        backup_info['create_time']=backup_task_info['create_time']
        backup_info['backup_time']=backup_task_info['backup_time']
        backup_info['backup_file']=backup_task_info['backup_file']
        backup_info['backup_path']=backup_task_info['backup_path']
        backup_info['restore_done_time']=backup_task_info['restore_done_time']
        backup_info['restore_total_time']=backup_task_info['restore_total_time']
        

        # 提取基本信息
        result = {
            "status": True,
            "msg": "获取详情成功",
            "error_msg": "",
            "data": {
                "type": "restore",
                "done_time": backup_info.get("restore_done_time", ""),
                "total_time": backup_info.get("restore_total_time", 0),
                "backup_file": backup_info.get("backup_file", ""),
                "backup_file_size": backup_info.get("backup_file_size", "0"),
                "backup_file_sha256": backup_info.get("backup_file_sha256", ""),
                "disk_use": 4786525184,
                "disk_free": BaseUtil.get_free_space(self)['free_space'],
                "data_status": {
                    "env_list": [],
                    "site_list": [],
                    "database_list": [],
                    "ftp_list": [],
                    "crontab_list": {},
                    "ssh_list": {},
                    "firewall_list": {},
                    "vmail_list": [],
                    "btnode_list": [],
                    "plugin_list": []
                }
            }
        }
        
        # 处理软件列表
        if "soft" in backup_info['data_list']:
            soft_data = backup_info["data_list"]["soft"]
            
            # 处理Web服务器
            if "web_server" in soft_data and soft_data["web_server"]:
                result["data"]["data_status"]["env_list"].append({
                    "name": soft_data["web_server"].get("name", ""),
                    "version": soft_data["web_server"].get("version", ""),
                    "size": 0,  # 需要从其他地方获取
                    "status": 2,
                    "err_msg": None
                })
            
            # 处理PHP版本
            if "php_server" in soft_data and soft_data["php_server"]:
                for php in soft_data["php_server"]:
                    result["data"]["data_status"]["env_list"].append({
                        "name": php.get("name", ""),
                        "version": php.get("version", ""),
                        "size": 0,  # 需要从其他地方获取
                        "status": 2,
                        "err_msg": None
                    })
            
            # 处理MySQL服务器
            if "mysql_server" in soft_data and soft_data["mysql_server"]:
                result["data"]["data_status"]["env_list"].append({
                    "name": soft_data["mysql_server"].get("type", "mysql"),
                    "version": soft_data["mysql_server"].get("version", ""),
                    "size": 0,  # 需要从其他地方获取
                    "status": 2,
                    "err_msg": None
                })
            
            # 处理Redis服务器
            if "redis_server" in soft_data and soft_data["redis_server"]:
                result["data"]["data_status"]["env_list"].append({
                    "name": "redis",
                    "version": soft_data["redis_server"],
                    "size": 0,  # 需要从其他地方获取
                    "status": 2,
                    "err_msg": None
                })
            
            # 处理MongoDB服务器
            if "mongodb_server" in soft_data and soft_data["mongodb_server"]:
                result["data"]["data_status"]["env_list"].append({
                    "name": "mongodb",
                    "version": soft_data["mongodb_server"],
                    "size": 0,  # 需要从其他地方获取
                    "status": 2,
                    "err_msg": None
                })
            
            # 处理PostgreSQL服务器
            if "pgsql_server" in soft_data and soft_data["pgsql_server"]:
                result["data"]["data_status"]["env_list"].append({
                    "name": "pgsql",
                    "version": soft_data["pgsql_server"],
                    "size": 0,  # 需要从其他地方获取
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
        print("Usage: btpython restore_manager.py <method> <timestamp>")
        sys.exit(1)
    method_name = sys.argv[1]  # 方法名
    timestamp = sys.argv[2]    # IP地址     
    restore_manager = RestoreManager()  # 实例化对象
    if hasattr(restore_manager, method_name):  # 检查方法是否存在
        method = getattr(restore_manager, method_name)  # 获取方法
        method(timestamp)  # 调用方法
    else:
        print(f"Error: 方法 '{method_name}' 不存在")