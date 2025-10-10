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
import requests
import socket
import shlex


if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

if '/www/server/panel' not in sys.path:
    sys.path.insert(0, '/www/server/panel')

import public
from mod.project.backup_restore.base_util import BaseUtil
from mod.project.backup_restore.data_manager import DataManager
from mod.project.backup_restore.config_manager import ConfigManager
from mod.project.backup_restore.backup_manager import BackupManager
from mod.project.backup_restore.restore_manager import RestoreManager
from mod.project.backup_restore.ssh_manager import BtInstallManager

class main(DataManager,BaseUtil,ConfigManager):
    def __init__(self):
        self.base_path = '/www/backup/backup_restore'
        self.bakcup_task_json = self.base_path + '/backup_task.json'
        self.backup_pl_file = self.base_path + '/backup.pl'
        self.restore_pl_file = self.base_path + '/restore.pl'
        self.migrate_task_json = self.base_path + '/migration_task.json'
        self.migrate_pl_file = self.base_path + '/migrate.pl'
        self.migrate_success_pl= self.base_path + '/migrate_success.pl'
        self.migrage_save_data_conf = self.base_path + '/migrate_save_data_conf.json'

    def return_data(self,status:bool,msg=None,error_msg=None,data=None):
        return {
            "status": status,
            "msg": msg,
            "error_msg": error_msg,
            "data": data
        }

    def get_test(self,get=None):
        return self.get_file_size("/root")
        return self.return_data(True, "测试成功", None, None)
    
    def add_backup(self,get):
        web_check=BaseUtil().web_config_check()
        if web_check['status'] == False:
            return self.return_data(False, "{}".format(web_check['msg']), "{}".format(web_check['msg']), None)
        
        backup_config = []
        if os.path.exists(self.bakcup_task_json):
            backup_config=json.loads(public.ReadFile(self.bakcup_task_json))

        backup_now=False
        if not hasattr(get, "timestamp"):
            get_time=""
        else:
            try:
                get_time=int(get.timestamp)
            except:
                get_time=get.timestamp

        local_timestamp=int(time.time())
        if get_time == "" or get_time == "0" or get_time == 0:
            backup_timestamp=local_timestamp
            get_time=local_timestamp
            backup_now=True
        else:
            backup_timestamp=get_time
        if not hasattr(get, "backup_name"):
            return self.return_data(False,"参数错误,缺少backup_name","参数错误,缺少backup_name")
        
        if not hasattr(get, "data_list"):
            backup_data = []
            backup_data.extend(["soft","site","database","wp_tools","ftp","crontab","vmail","ssh","firewall","node","plugin"])
        else:
            backup_data = get.data_list
            backup_data=json.loads(backup_data)

        
        if not hasattr(get, "database_id"):
            database_id = []
        else:
            database_id = get.database_id


        if not hasattr(get, "site_id"):
            site_id = []
        else:
            site_id = get.site_id
    
        backup_conf = {}

        backup_conf['backup_name'] = get.backup_name
        backup_conf['timestamp'] = get_time
        backup_conf['create_time'] = datetime.datetime.fromtimestamp(int(local_timestamp)).strftime('%Y-%m-%d %H:%M:%S')
        backup_conf['backup_time'] = datetime.datetime.fromtimestamp(int(backup_timestamp)).strftime('%Y-%m-%d %H:%M:%S')
        backup_conf['storage_type'] = get.storage_type
        backup_conf['auto_exit'] = int(get.auto_exit)
        backup_conf['backup_status'] = 0
        backup_conf['restore_status'] = 0
        backup_conf['backup_path'] = self.base_path + "/" + str(get_time) + "_backup"
        backup_conf['backup_file'] = ""
        backup_conf['backup_file_sha256'] = ""
        backup_conf['backup_file_size'] = ""
        backup_conf['backup_count'] = {}
        backup_conf['backup_count']['success'] = None
        backup_conf['backup_count']['failed'] = None
        backup_conf['total_time']=None
        backup_conf['done_time']=None
        backup_conf['database_id'] = database_id
        backup_conf['site_id'] = site_id
        backup_conf['backup_data'] = backup_data
        
        backup_config.append(backup_conf) 
        public.WriteFile(self.bakcup_task_json,json.dumps(backup_config))

        if backup_now:
            public.ExecShell("nohup btpython /www/server/panel/mod/project/backup_restore/backup_manager.py backup_data {} > /dev/null 2>&1 &".format(int(get_time)))
        else:
            local_time = time.localtime(int(get_time))
            at_time_str = time.strftime("%Y%m%d%H%M", local_time)
            exec_command="echo 'nohup btpython /www/server/panel/mod/project/backup_restore/backup_manager.py backup_data {} > /dev/null 2>&1 &'|at -t {}".format(int(get_time),at_time_str)
            public.ExecShell(exec_command)
        public.set_module_logs('backup_restore', 'add_backup', 1)
        return self.return_data(True,"添加成功","添加成功")
        
    def get_backup_list(self,get=None):
        if not os.path.exists(self.base_path):
            public.ExecShell("mkdir -p {}".format(self.base_path))
        backup_config = []
        backup_config = BackupManager().get_local_backup()
        backup_config = sorted(backup_config, key=lambda x: int(x["timestamp"]), reverse=True)
        # if os.path.exists(self.bakcup_task_json):
        #     backup_config=json.loads(public.ReadFile(self.bakcup_task_json))
        return self.return_data(True,"获取成功",None,backup_config)

    def del_backup(self,get):
        if not hasattr(get, "timestamp"):
            return self.return_data(False,"参数错误","参数错误")
        
        backup_config = []
        if os.path.exists(self.bakcup_task_json):
            backup_config=json.loads(public.ReadFile(self.bakcup_task_json))
        
        for backup_conf in backup_config:
            if backup_conf['timestamp'] == int(get.timestamp):
                backup_file=backup_conf['backup_file']
                if os.path.exists(backup_file):
                    public.ExecShell("rm -rf {}".format(backup_file))
                backup_config.remove(backup_conf)
                public.WriteFile(self.bakcup_task_json,json.dumps(backup_config))
                return self.return_data(True,"删除成功","删除成功")
        
        backup_file_list=os.listdir(self.base_path)
        for backup_file in backup_file_list:
            if backup_file.endswith(".tar.gz"):
                if str(get.timestamp) in backup_file:
                    if os.path.exists(os.path.join(self.base_path,backup_file)):
                        public.ExecShell("rm -rf {}".format(os.path.join(self.base_path,backup_file)))
                    return self.return_data(True,"删除成功","删除成功")
                    
        return self.return_data(False,"删除失败","删除失败")
     
    def get_data_total(self,get=None):
        server_data=self.get_data_list()
        return self.return_data(True,"获取成功","",server_data)

    def get_progress(self,get=None):
        type=get.type
        if type == "backup":
            progress_data = BackupManager().get_backup_progress()
        elif type == "restore":
            progress_data = RestoreManager().get_restore_progress()
        if progress_data['status'] == True:
            return self.return_data(True,"获取成功","",progress_data['msg'])
        else:
            return self.return_data(False,"异常","",progress_data['msg'])
        
    def get_details(self,get=None):
        timestamp=get.timestamp
        type=get.type
        if type == "backup":
            return BackupManager().get_backup_details(timestamp)
        elif type == "restore":
            return RestoreManager().get_restore_details(timestamp)
    
    def get_exec_logs(self,get=None):
        timestamp=get.timestamp
        type=get.type
        if type == "backup":
            exec_logs=BackupManager().get_backup_log(timestamp)
        elif type == "restore":
            exec_logs=RestoreManager().get_restore_log(timestamp)
        return self.return_data(True,"获取成功","",exec_logs)

    def get_susses_msg(self,get=None):
        return ConfigManager.get_backup_susses_msg(get)

    def task_stop(self,get=None):
        timestamp=get.timestamp

        backup_task_pid=public.ExecShell("ps -ef|grep 'backup_manager.py'|grep -v grep|awk '{print $2}'")[0].replace("\n","")
        if backup_task_pid:
            public.ExecShell("kill {}".format(backup_task_pid))

        restore_task_pid=public.ExecShell("ps -ef|grep 'restore_manager.py'|grep -v grep|awk '{print $2}'")[0].replace("\n","")
        if restore_task_pid:
            public.ExecShell("kill {}".format(restore_task_pid))


        if os.path.exists(self.backup_pl_file):
            public.ExecShell("rm -f {}".format(self.backup_pl_file))

        if os.path.exists(self.restore_pl_file):
            public.ExecShell("rm -f {}".format(self.restore_pl_file))

        try:
            task_json_data=json.loads(public.ReadFile(self.bakcup_task_json))
            for item in task_json_data:
                if 'backup_status' in item and item['backup_status'] == 1:
                    item['backup_status']=0
                if 'restore_status' in item and item['restore_status'] == 1:
                    item['restore_status']=0
            public.WriteFile(self.bakcup_task_json,json.dumps(task_json_data))
        except:
            pass

        if os.path.exists("/www/server/panel/data/migration.pl"):
            public.ExecShell("rm -f /www/server/panel/data/migration.pl")
        return self.return_data(True, "终止任务成功", None, None)
    
    def get_backup_detail(self,get=None):
        timestamp=get.timestamp
        data = BackupManager().get_backup_file_msg(timestamp)
        return self.return_data(True,"获取成功","",data)

    def exec_backup(self,get=None):
        if not hasattr(get, "timestamp"):
            return self.return_data(False,"参数错误","参数错误")
        timestamp=get.timestamp
        public.ExecShell("nohup btpython /www/server/panel/mod/project/backup_restore/backup_manager.py backup_data {} > /dev/null 2>&1 &".format(int(timestamp)))
        return self.return_data(True,"执行成功","执行成功")
    
    def add_restore(self,get=None):
        if not hasattr(get, "timestamp"):
            return self.return_data(False,"参数错误","参数错误")
        timestamp=get.timestamp
        public.ExecShell("nohup btpython /www/server/panel/mod/project/backup_restore/restore_manager.py restore_data {} > /dev/null 2>&1 &".format(int(timestamp)))
        public.set_module_logs('backup_restore', 'add_restore', 1)
        return self.return_data(True,"添加还原任务成功","","")
    
    def ssh_auth_check(self, get):
        web_check=BaseUtil().web_config_check()
        if web_check['status'] == False:
            return self.return_data(False, "{}".format(web_check['msg']), "{}".format(web_check['msg']), None)
        """验证SSH连接信息是否正常"""
        if not hasattr(get, "server_ip") or not get.server_ip:
            return self.return_data(False, "参数错误，缺少server_ip", "参数错误，缺少server_ip")
        
        port = 22
        if hasattr(get, "ssh_port") and get.ssh_port:
            port = int(get.ssh_port)


        if not hasattr(get, "ssh_user") or not get.ssh_user:
            return self.return_data(False, "参数错误，缺少ssh_user", "参数错误，缺少ssh_user")

        if not hasattr(get, "auth_type") or not get.auth_type:
            return self.return_data(False, "参数错误，缺少auth_type", "参数错误，缺少auth_type")
        

        ssh_client=self.ssh_net_client_test(get.server_ip,port)
        if not ssh_client:
            return self.return_data(False, "SSH连接测试失败,请检查IP端口填写是否正确", "SSH连接测试失败,请检查IP端口填写是否正确")
        
        password = None
        key_file = None
        # 至少需要提供密码或密钥文件之一
        if hasattr(get, "password") and get.password:
            password = get.password
        else:
            return self.return_data(False, "参数错误，需要提供password", "参数错误，需要提供password")
        

        if get.auth_type == "password":
            key_file = None
        elif get.auth_type == "key":
            key_file = "/www/backup/backup_restore/key_file"
            public.WriteFile(key_file,get.password)
            public.ExecShell("chmod 600 {}".format(key_file))
        else:
            return self.return_data(False, "参数错误，auth_type错误", "参数错误，auth_type错误")
        
        # 创建SSH管理器实例并验证连接
        manager = BtInstallManager(
            host=get.server_ip,
            port=port,
            username=get.ssh_user,
            password=password,
            key_file=key_file
        )
        
        result = manager.verify_ssh_connection()
        
        if result["status"]:
            return self.return_data(True, "SSH连接验证成功", None, None)
        else:
            return self.return_data(False, "SSH连接验证失败", result["msg"], None)

    def add_migrate_task(self,get=None):
        self.stop_migrate()
        
        if os.path.exists("/www/backup/backup_restore/migration.log"):
            public.ExecShell("rm -f /www/backup/backup_restore/migration.log")

        server_ip=get.server_ip
        ssh_port=get.ssh_port
        ssh_user=get.ssh_user
        auth_type=get.auth_type
        password=get.password

        if auth_type == "key":
            key_file="/www/backup/backup_restore/key_file"
            public.WriteFile(key_file,password)
            public.ExecShell("chmod 600 {}".format(key_file))



        if not hasattr(get, "backup_data"):
            backup_data = []
            backup_data.extend(["soft","site","database","wp_tools","ftp","crontab","vmail","ssh","firewall","node","plugin"])
        else:
            backup_data = get.backup_data
            backup_data=json.loads(backup_data)

        
        if not hasattr(get, "database_id"):
            database_id = '["ALL"]'
        else:
            database_id = get.database_id


        if not hasattr(get, "site_id"):
            site_id = '["ALL"]'
        else:
            site_id = get.site_id

        save_data_conf={
            "backup_data":backup_data,
            "database_id":database_id,
            "site_id":site_id
        }
        public.WriteFile(self.migrage_save_data_conf,json.dumps(save_data_conf))


        timestamp=int(time.time())
        migrate_conf = {}
        migrate_conf['server_ip'] = server_ip
        migrate_conf['ssh_port'] = ssh_port
        migrate_conf['ssh_user'] = ssh_user
        migrate_conf['auth_type'] = auth_type
        migrate_conf['password'] = password
        migrate_conf['timestamp'] = timestamp
        migrate_conf['run_type'] = "INIT"
        migrate_conf['run_status'] = 1
        migrate_conf['step'] = 1
        migrate_conf['migrate_progress'] = 5
        migrate_conf['migrate_msg'] = "迁移任务初始化中"
        migrate_conf['task_info'] = None
        public.WriteFile(self.migrate_task_json,json.dumps(migrate_conf))

        if auth_type == "password":
            escaped_password = shlex.quote(password)
            public.ExecShell("nohup btpython /www/server/panel/mod/project/backup_restore/ssh_manager.py --action migrate -H {server_ip} -P {ssh_port} -u {ssh_user} -p {escaped_password} --task-name '我的迁移任务' > /dev/null 2>&1 &".format(server_ip=server_ip,ssh_port=ssh_port,ssh_user=ssh_user,escaped_password=escaped_password))
        elif auth_type == "key":
            public.ExecShell("nohup btpython /www/server/panel/mod/project/backup_restore/ssh_manager.py --action migrate -H {server_ip} -P {ssh_port} -u {ssh_user} --key-file {key_file} --task-name '我的迁移任务' > /dev/null 2>&1 &".format(server_ip=server_ip,ssh_port=ssh_port,ssh_user=ssh_user,key_file=key_file))
        public.set_module_logs('backup_restore', 'add_migrate_task', 1)
        return self.return_data(True, "添加迁移任务成功", None, None)

    def get_migrate_status(self,get=None):
        result={}
        if os.path.exists(self.migrate_task_json):
            result['task_status'] = True
            migrate_config = json.loads(public.ReadFile(self.migrate_task_json))
            result['server_ip'] = migrate_config['server_ip']
            result['timestamp'] = migrate_config['timestamp']
        else:
            result['task_status'] = False

        return self.return_data(True, "获取成功", None, result)
    
    def stop_migrate(self,get=None):
        migrate_pid=public.ExecShell("ps -ef|grep 'ssh_manager.py'|grep -v grep|awk '{print $2}'")[0].replace("\n","")
        if migrate_pid:
            public.ExecShell("kill {}".format(migrate_pid))
        public.ExecShell("rm -f /www/backup/backup_restore/migrate_backup.pl")
        public.ExecShell("rm -f /www/backup/backup_restore/migration.pl")
        public.ExecShell("rm -f /www/backup/backup_restore/migrate_backup_success.pl")
        if os.path.exists(self.migrate_task_json):
            public.ExecShell("rm -f {}".format(self.migrate_task_json))
            return self.return_data(True, "终止任务成功", None, None)
        else:
            return self.return_data(False, "当前没有迁移任务", None, None)

    def get_migrate_progress(self,get=None):
        if os.path.exists(self.migrate_task_json):
            migrate_config = json.loads(public.ReadFile(self.migrate_task_json))
            migrate_config['migrate_log'] = public.ReadFile('/www/backup/backup_restore/migration.log')
            if migrate_config['run_type'] == "PANEL_INSTALL":
                migrate_config['migrate_log'] = public.ReadFile('/www/backup/backup_restore/migration.log')
            if migrate_config['run_type'] == "LOCAL_BACKUP":
                if os.path.exists('/www/backup/backup_restore/backup.log'):
                    backup_log_data = public.ReadFile('/www/backup/backup_restore/backup.log')
                else:
                    backup_log_data = "正在启动备份任务..."
                migration_log_data = public.ReadFile('/www/backup/backup_restore/migration.log')
                migrate_config['migrate_log'] = migration_log_data + "\n" + backup_log_data
            if migrate_config ['run_status'] == 2:
                if migrate_config['run_type'] == "COMPLETED":
                    migrate_config['migrate_progress'] = 100
                    migrate_config['migrate_msg'] = "宝塔面板安装完成！"
                    migrate_config['panel_addr'] = migrate_config['task_info']['panel_info']['panel_url']
                    migrate_config['panel_user'] = migrate_config['task_info']['panel_info']['username']
                    migrate_config['panel_password'] = migrate_config['task_info']['panel_info']['password']
                    migrate_config['migrate_err_msg'] = None
                else:
                    migrate_config ['run_status'] = 1
                
            else:
                migrate_config['migrate_err_msg'] = migrate_config['migrate_msg']
                run_name="迁移任务"
                err_info=[]
                if migrate_config['run_type'] == "PANEL_INSTALL":
                    run_name="宝塔面板安装"
                elif migrate_config['run_type'] == "LOCAL_BACKUP":
                    run_name="本地备份"
                elif migrate_config['run_type'] == "UPLOAD_FILE":
                    run_name="文件上传"
                elif migrate_config['run_type'] == "REMOTE":
                    run_name="还原任务"
                err_info_result= {
                    "name": run_name,
                    "type": "环境",
                    "msg":  migrate_config['migrate_msg']
                }
                err_info.append(err_info_result)
                migrate_config['err_info'] = err_info

            return self.return_data(True, "获取成功", None, migrate_config)

            result={}
        else:
            return self.return_data(False, "当前没有迁移任务", None, None)
        
    def get_history_migrate_list(self,get=None):
        history_migrate = []
        if os.path.exists(self.base_path):
            for item in os.listdir(self.base_path):
                item_path = os.path.join(self.base_path, item)
                if os.path.isdir(item_path) and re.match(r'^(\d+)_migration$', item):
                    timestamp = re.match(r'^(\d+)_migration$', item).group(1)
                    if os.path.exists(os.path.join(item_path,"status.json")):
                        status_data = json.loads(public.ReadFile(os.path.join(item_path,"status.json")))
                        migrate_ip = status_data['server_ip']
                    else:
                        migrate_ip = None
                    migrate_data = {
                        "timestamp": int(timestamp),
                        "migrate_time": int(timestamp),
                        "migrate_path": item_path,
                        "migrate_ip": migrate_ip
                    }
                    history_migrate.append(migrate_data)
        return history_migrate
    
    def get_history_migrate_log(self,get=None):
        timestamp=get.timestamp
        history_migrate_log = self.base_path + "/" + str(timestamp) + "_migration/migration.log"
        if os.path.exists(history_migrate_log):
            return self.return_data(True, "获取成功", None, public.ReadFile(history_migrate_log))
        else:
            return self.return_data(False, "迁移日志不存在", None, None)

    def get_history_migrate_info(self,get=None):
        timestamp=get.timestamp
        history_migrate_info = self.base_path + "/" + str(timestamp) + "_migration/status.json"
        if os.path.exists(history_migrate_info):
            return self.return_data(True, "获取成功", None, json.loads(public.ReadFile(history_migrate_info)))
        else:
            return self.return_data(False, "迁移日志不存在", None, None)

    # def get_backup_log(self,get=None):
    #     if not hasattr(get, "timestamp"):
    #         return self.return_data(False,"参数错误","参数错误")
    #     timestamp=get.timestamp
    #     return self.return_data(True,"获取成功","",BackupManager().get_backup_log(timestamp))

    def ssh_net_client_test(self,server_ip,ssh_port):
        try:
            # 使用requests库测试SSH连接，设置3秒超时
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((server_ip, int(ssh_port)))
            sock.close()
            
            if result == 0:
                return True
            else:
                return False
        except Exception as e:
            return False
        
    def del_migrate_tips(self,get=None):
        if os.path.exists("/www/server/panel/data/migration.pl"):
            public.ExecShell("rm -f /www/server/panel/data/migration.pl")
        return public.returnMsg(True, "删除迁移提醒成功")
    
    def del_history_migrate(self,get=None):
        timestamp=get.timestamp
        if os.path.exists(self.base_path + "/" + str(timestamp) + "_migration"):
            public.ExecShell("rm -rf {}".format(self.base_path + "/" + str(timestamp) + "_migration"))
            return public.returnMsg(True, "删除迁移历史成功")
        else:
            return public.returnMsg(False, "迁移历史不存在")   
        
if __name__ == '__main__':
    # 获取命令行参数
    if len(sys.argv) < 2:
        print("Usage: btpython backup_manager.py <method> <timestamp>")
        sys.exit(1)
    method_name = sys.argv[1]  # 方法名  p
    timestamp = sys.argv[2]
    com_manager = main()  # 实例化对象
    if hasattr(com_manager, method_name):  # 检查方法是否存在
        method = getattr(com_manager, method_name)  # 获取方法
        method(timestamp)  # 调用方法
    else:
        print(f"Error: 方法 '{method_name}' 不存在")