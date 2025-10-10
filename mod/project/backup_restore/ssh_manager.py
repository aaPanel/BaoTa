#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 通过SSH连接新服务器，安装宝塔面板并进行备份还原

import paramiko
import os
import time
import sys
import json
import re
import argparse
import logging
import socket
import datetime

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

if '/www/server/panel' not in sys.path:
    sys.path.insert(0, '/www/server/panel')

import public

try:
    from paramiko import SSHClient, AutoAddPolicy
    from paramiko.sftp_client import SFTPClient
except:
    public.ExecShell("btpip install paramiko")
    try:
        from paramiko import SSHClient, AutoAddPolicy
        from paramiko.sftp_client import SFTPClient
    except:
        pass

# 添加迁移进度跟踪相关的变量和工具函数
BACKUP_RESTORE_PATH = "/www/backup/backup_restore"
MIGRATION_TASK_JSON = '/www/backup/backup_restore/migration_task.json'
MIGRATION_LOG_FILE = '/www/backup/backup_restore/migration.log'
MIGRATION_PL_FILE = '/www/backup/backup_restore/migration.pl'
MIGRATION_SUCCESS_FILE = '/www/backup/backup_restore/migration_success.pl'

# 迁移状态码
MIGRATION_STATUS = {
    'PENDING': 0,      # 等待中
    'RUNNING': 1,      # 运行中
    'COMPLETED': 2,    # 已完成
    'FAILED': 3,       # 失败
}

# 迁移阶段
MIGRATION_STAGES = {
    'INIT': {
        'code': 'init',
        'display': '初始化',
        'progress': 5,
    },
    'PANEL_INSTALL': {
        'code': 'panel_install',
        'display': '面板安装',
        'progress': 20,
    },
    'LOCAL_BACKUP': {
        'code': 'local_backup',
        'display': '本地备份',
        'progress': 40,
    },
    'FILE_UPLOAD': {
        'code': 'file_upload',
        'display': '文件上传',
        'progress': 70,
    },
    'RESTORE': {
        'code': 'restore',
        'display': '数据还原',
        'progress': 90,
    },
    'COMPLETED': {
        'code': 'completed',
        'display': '迁移完成',
        'progress': 100,
    }
}

def write_migration_log(message, task_id=None, log_type='INFO'):
    """写入迁移日志"""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    log_message = f"[{timestamp}] [{log_type}] {message}\n"
    
    # 确保目录存在
    log_dir = os.path.dirname(MIGRATION_LOG_FILE)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    # 写入主日志文件
    with open(MIGRATION_LOG_FILE, 'a+') as f:
        f.write(log_message)
    
    # 如果指定了任务ID，同时写入任务特定的日志文件
    if task_id:
        task_log_file = f"/www/backup/backup_restore/{task_id}_migration/migration.log"
        task_log_dir = os.path.dirname(task_log_file)
        if not os.path.exists(task_log_dir):
            os.makedirs(task_log_dir)
        with open(task_log_file, 'a+') as f:
            f.write(log_message)
    
    return log_message.strip()

def update_migration_status(task_id, stage, status=MIGRATION_STATUS['RUNNING'], message=None, details=None):
    """更新迁移任务状态"""
    # 确保目录存在
    task_dir = f"/www/backup/backup_restore/{task_id}_migration"
    if not os.path.exists(task_dir):
        os.makedirs(task_dir)
    
    # 任务状态文件路径
    task_status_file = f"{task_dir}/status.json"
    
    # 读取当前状态（如果存在）
    current_status = {}
    if os.path.exists(task_status_file):
        try:
            with open(task_status_file, 'r') as f:
                current_status = json.load(f)
        except Exception as e:
            write_migration_log(f"读取任务状态失败: {e}", task_id, 'ERROR')
    
    # 更新状态为新格式
    current_time = time.strftime('%Y-%m-%d %H:%M:%S')
    if 'start_time' not in current_status:
        current_status['start_time'] = current_time
    
    current_status['task_id'] = task_id
    current_status['last_update'] = current_time
    current_status['server_ip'] = current_status.get('server_ip', '')
    current_status['run_type'] = stage
    current_status['run_status'] = status
    current_status['step'] = list(MIGRATION_STAGES.keys()).index(stage) + 1 if stage in MIGRATION_STAGES else 1
    current_status['migrate_progress'] = MIGRATION_STAGES.get(stage, {}).get('progress', 0)
    current_status['migrate_msg'] = message if message else MIGRATION_STAGES.get(stage, {}).get('display', stage)
    
    if details:
        if 'task_info' not in current_status:
            current_status['task_info'] = {}
        current_status['task_info'].update(details)
    
    # 如果任务完成，记录完成时间
    if status == MIGRATION_STATUS['COMPLETED']:
        current_status['end_time'] = current_time
        if 'start_time' in current_status:
            start_time = time.strptime(current_status['start_time'], '%Y-%m-%d %H:%M:%S')
            end_time = time.strptime(current_time, '%Y-%m-%d %H:%M:%S')
            total_seconds = time.mktime(end_time) - time.mktime(start_time)
            current_status['total_time'] = total_seconds
    
    # 保存状态
    try:
        with open(task_status_file, 'w') as f:
            json.dump(current_status, f, ensure_ascii=False, indent=2)
    except Exception as e:
        write_migration_log(f"保存任务状态失败: {e}", task_id, 'ERROR')
    
    # 同时更新全局任务记录
    update_global_migration_tasks(task_id, current_status)
    
    return current_status

def update_global_migration_tasks(task_id, task_status):
    """更新全局迁移任务记录 - 唯一任务运行模式"""
    # 在唯一任务运行模式下，我们只保存最新的任务
    try:
        task_dir = os.path.dirname(MIGRATION_TASK_JSON)
        if not os.path.exists(task_dir):
            os.makedirs(task_dir)
        # 直接写入当前任务作为全局任务
        with open(MIGRATION_TASK_JSON, 'w') as f:
            json.dump(task_status, f, ensure_ascii=False, indent=2)
    except Exception as e:
        write_migration_log(f"保存全局任务记录失败: {e}", task_id, 'ERROR')

def get_migration_status(task_id=None):
    """获取迁移任务进度
    
    Args:
        task_id: 指定任务ID，如果为空则返回最新任务状态
        
    Returns:
        任务状态信息
    """
    # 如果没有指定task_id，则从migration_task.json获取当前运行的任务
    if not task_id:
        if os.path.exists(MIGRATION_PL_FILE):
            try:
                with open(MIGRATION_PL_FILE, 'r') as f:
                    task_id = f.read().strip()
            except:
                return {"status": False, "msg": "无法读取当前运行的任务ID"}
                
        # 如果没有获取到任务ID，则直接读取全局任务文件
        if not task_id and os.path.exists(MIGRATION_TASK_JSON):
            try:
                with open(MIGRATION_TASK_JSON, 'r') as f:
                    task_data = json.load(f)
                    return {"status": True, "msg": "获取任务状态成功", "data": task_data}
            except Exception as e:
                return {"status": False, "msg": f"读取任务状态失败: {e}"}
        
        if not task_id:
            return {"status": False, "msg": "没有正在运行的任务"}
    
    # 获取指定任务的状态
    task_status_file = f"/www/backup/backup_restore/{task_id}_migration/status.json"
    if os.path.exists(task_status_file):
        try:
            with open(task_status_file, 'r') as f:
                task_data = json.load(f)
                return {"status": True, "msg": "获取任务状态成功", "data": task_data}
        except Exception as e:
            return {"status": False, "msg": f"读取任务状态失败: {e}"}
    else:
        return {"status": False, "msg": f"任务 {task_id} 不存在"}

def create_migration_task(task_name, host, port=22, username='root', password=None, key_file=None, backup_file=None):
    """创建新的迁移任务"""
    task_id = str(int(time.time()))
    
    # 检查是否存在正在运行的任务
    if os.path.exists(MIGRATION_PL_FILE):
        try:
            with open(MIGRATION_PL_FILE, 'r') as f:
                running_task_id = f.read().strip()
            
            # 如果有运行中的任务，返回错误
            if running_task_id:
                error_msg = f"已有任务正在运行，任务ID: {running_task_id}"
                write_migration_log(error_msg)
                return {"status": False, "msg": error_msg}
        except:
            pass
    
    # 按照comMod.py中的格式创建任务数据
    print(host)
    task_data = {
        'task_id': task_id,
        'server_ip': host,
        'ssh_port': port,
        'ssh_user': username,
        'auth_type': 'password' if password else 'key',
        'password': password if password else '',
        'timestamp': int(time.time()),
        'run_type': 'INIT',
        'run_status': MIGRATION_STATUS['RUNNING'],
        'step': 1,
        'migrate_progress': MIGRATION_STAGES['INIT']['progress'],
        'migrate_msg': '迁移任务初始化中',
        'task_info': {
            'task_name': task_name,
            'backup_file': backup_file,
            'start_time': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    }
    
    # 创建任务目录
    task_dir = f"/www/backup/backup_restore/{task_id}_migration"
    if not os.path.exists(task_dir):
        os.makedirs(task_dir)
    
    # 保存任务状态
    with open(f"{task_dir}/status.json", 'w') as f:
        json.dump(task_data, f, ensure_ascii=False, indent=2)
    
    # 更新全局任务记录
    update_global_migration_tasks(task_id, task_data)
    
    # 创建进程锁文件
    with open(MIGRATION_PL_FILE, 'w') as f:
        f.write(task_id)
    
    write_migration_log(f"创建迁移任务: {task_name} -> {host}", task_id)
    
    return {"status": True, "msg": "迁移任务创建成功", "task_id": task_id}

class BtInstallManager:
    def __init__(self, host, port=22, username='root', password=None, key_file=None, 
                 backup_file=None, panel_port=8888, max_retries=3, retry_interval=5, task_id=None):
        """
        初始化SSH连接管理器
        
        Args:
            host: 远程服务器IP
            port: SSH端口，默认22
            username: SSH用户名，默认root
            password: SSH密码，与key_file二选一
            key_file: SSH密钥文件路径，与password二选一
            backup_file: 本地备份文件路径
            panel_port: 宝塔面板端口，默认8888
            max_retries: 最大重试次数，默认3次
            retry_interval: 重试间隔，默认5秒
            task_id: 迁移任务ID，用于跟踪进度
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_file = key_file
        self.backup_file = backup_file
        self.panel_port = panel_port
        self.ssh = None
        self.sftp = None
        self.remote_backup_path = '/www/backup/backup_restore'
        self.max_retries = max_retries
        self.retry_interval = retry_interval
        self.task_id = task_id  # 添加任务ID
        
    def connect(self):
        """建立SSH连接"""
        try:
            if self.task_id:
                write_migration_log(f"正在连接到服务器 {self.host}:{self.port}", self.task_id)
                
            self.ssh = SSHClient()
            self.ssh.set_missing_host_key_policy(AutoAddPolicy())
           
            
            if self.key_file:
                key = self._load_ssh_key(self.key_file)
                self.ssh.connect(self.host, self.port, self.username, pkey=key)
            else:
                self.ssh.connect(self.host, self.port, self.username, self.password)
                
            self.sftp = self.ssh.open_sftp()
            print(f"[+] 成功连接到服务器 {self.host}")
            
            if self.task_id:
                write_migration_log(f"成功连接到服务器 {self.host}", self.task_id)
                
            return True
        except paramiko.AuthenticationException:
            error_msg = f"认证失败: 用户名或密码错误"
            print(f"[!] {error_msg}")
            
            if self.task_id:
                write_migration_log(error_msg, self.task_id, 'ERROR')
                update_migration_status(self.task_id, 'INIT', MIGRATION_STATUS['FAILED'], message=error_msg)
                
            return {"status": False, "msg": error_msg}
        except paramiko.SSHException as e:
            error_msg = f"SSH连接异常: {e}"
            print(f"[!] {error_msg}")
            
            if self.task_id:
                write_migration_log(error_msg, self.task_id, 'ERROR')
                update_migration_status(self.task_id, 'INIT', MIGRATION_STATUS['FAILED'], message=error_msg)
                
            return {"status": False, "msg": error_msg}
        except socket.error as e:
            error_msg = f"网络连接错误: {e}"
            print(f"[!] {error_msg}")
            
            if self.task_id:
                write_migration_log(error_msg, self.task_id, 'ERROR')
                update_migration_status(self.task_id, 'INIT', MIGRATION_STATUS['FAILED'], message=error_msg)
                
            return {"status": False, "msg": error_msg}
        except Exception as e:
            error_msg = f"连接服务器失败: {e}"
            print(f"[!] {error_msg}")
            
            if self.task_id:
                write_migration_log(error_msg, self.task_id, 'ERROR')
                update_migration_status(self.task_id, 'INIT', MIGRATION_STATUS['FAILED'], message=error_msg)
                
            return {"status": False, "msg": error_msg}
    
    def _load_ssh_key(self, key_file, password=None):
        """根据密钥文件自动判断类型并加载"""
        # 读取文件内容
        with open(key_file, 'r') as f:
            content = f.read()
        
        # 尝试不同的密钥类型
        key = None
        errors = []
        
        # 判断明确标记的密钥类型
        if "BEGIN RSA PRIVATE KEY" in content:
            try:
                key = paramiko.RSAKey.from_private_key_file(key_file, password=password)
                if self.task_id:
                    write_migration_log(f"使用RSA类型密钥连接", self.task_id)
                return key
            except Exception as e:
                errors.append(f"RSA密钥加载失败: {str(e)}")
        
        elif "BEGIN DSA PRIVATE KEY" in content and hasattr(paramiko, "DSSKey"): # 兼容无DSSKey功能的paramiko版本
            try:
                key = paramiko.DSSKey.from_private_key_file(key_file, password=password)
                if self.task_id:
                    write_migration_log(f"使用DSA类型密钥连接", self.task_id)
                return key
            except Exception as e:
                errors.append(f"DSA密钥加载失败: {str(e)}")
        
        elif "BEGIN EC PRIVATE KEY" in content:
            try:
                key = paramiko.ECDSAKey.from_private_key_file(key_file, password=password)
                if self.task_id:
                    write_migration_log(f"使用ECDSA类型密钥连接", self.task_id)
                return key
            except Exception as e:
                errors.append(f"ECDSA密钥加载失败: {str(e)}")
        
        elif "BEGIN OPENSSH PRIVATE KEY" in content:
            # 对于OPENSSH格式，尝试所有可能的类型
            key_types = [
                (paramiko.Ed25519Key, "Ed25519"),
                (paramiko.RSAKey, "RSA"),
                (paramiko.ECDSAKey, "ECDSA"),
            ]
            if hasattr(paramiko, "DSSKey"): # 兼容无DSSKey功能的paramiko版本
                key_types.append((paramiko.DSSKey, "DSA"))

            for key_class, key_name in key_types:
                try:
                    key = key_class.from_private_key_file(key_file, password=password)
                    if self.task_id:
                        write_migration_log(f"使用{key_name}类型密钥连接", self.task_id)
                    return key
                except Exception as e:
                    errors.append(f"{key_name}密钥加载失败: {str(e)}")
        
        # 如果以上方法都失败，抛出异常
        error_msg = "无法识别或加载密钥，请检查密钥文件格式是否正确"
        if self.task_id:
            write_migration_log(error_msg, self.task_id)
        raise ValueError(error_msg)
    
    def reconnect(self):
        """重新连接SSH"""
        if self.ssh:
            try:
                self.ssh.close()
            except:
                pass
        if self.sftp:
            try:
                self.sftp.close()
            except:
                pass
            
        self.ssh = None
        self.sftp = None
        
        for attempt in range(self.max_retries):
            print(f"[*] 尝试重新连接服务器 (尝试 {attempt+1}/{self.max_retries})...")
            connection_result = self.connect()
            if isinstance(connection_result, dict):
                # 连接失败，返回错误信息
                if attempt == self.max_retries - 1:
                    return connection_result
            elif connection_result:
                return True
            time.sleep(self.retry_interval)
        
        print(f"[!] 重新连接服务器失败，已达到最大重试次数 ({self.max_retries})")
        return {"status": False, "msg": f"重新连接服务器失败，已达到最大重试次数 ({self.max_retries})"}
            
    def disconnect(self):
        """关闭SSH连接"""
        if self.sftp:
            self.sftp.close()
        if self.ssh:
            self.ssh.close()
        print(f"[+] 已断开与服务器 {self.host} 的连接")
    
    def exec_command(self, command, print_output=True, retry=True):
        """
        执行远程命令
        
        Args:
            command: 要执行的命令
            print_output: 是否打印输出
            retry: 连接断开时是否重试
            
        Returns:
            (stdout, stderr)
        """
        if not self.ssh:
            if retry:
                reconnect_result = self.reconnect()
                if isinstance(reconnect_result, dict):
                    return None, None
                return self.exec_command(command, print_output, False)  # 重连成功后再次尝试，但不再重试
            print("[!] SSH连接未建立")
            return None, None
            
        try:
            print(f"[*] 执行命令: {command}")
            stdin, stdout, stderr = self.ssh.exec_command(command)
            stdout_content = stdout.read().decode('utf-8')
            stderr_content = stderr.read().decode('utf-8')
            
            if print_output:
                if stdout_content:
                    print("[+] 输出:", stdout_content)
                if stderr_content:
                    print("[!] 错误:", stderr_content)
                    
            return stdout_content, stderr_content
        except (socket.error, paramiko.SSHException) as e:
            print(f"[!] 执行命令时SSH连接断开: {e}")
            if retry:
                reconnect_result = self.reconnect()
                if isinstance(reconnect_result, dict):
                    return None, None
                print("[*] 重新连接成功，重试命令...")
                return self.exec_command(command, print_output, False)  # 重连成功后再次尝试，但不再重试
            return None, None
    
    def check_os_type(self):
        """检测服务器操作系统类型"""
        print("[*] 检测服务器操作系统类型...")
        os_type = None
        
        stdout, _ = self.exec_command("cat /etc/os-release")
        if stdout is None:
            return None
            
        if "CentOS" in stdout:
            os_type = "centos"
        elif "Ubuntu" in stdout:
            os_type = "ubuntu"
        elif "Debian" in stdout:
            os_type = "debian"
        else:
            stdout, _ = self.exec_command("cat /etc/redhat-release", print_output=False)
            if stdout and ("CentOS" in stdout or "Red Hat" in stdout):
                os_type = "centos"
        
        if os_type:
            print(f"[+] 操作系统类型: {os_type}")
        else:
            print("[!] 无法确定操作系统类型")
            
        return os_type
    
    def install_bt_panel(self):
        """安装宝塔面板"""
        if self.task_id:
            update_migration_status(self.task_id, 'PANEL_INSTALL', message="开始安装宝塔面板")
            
        print("[*] 开始安装宝塔面板...")
        
        # 检查是否已安装宝塔面板
        # stdout, _ = self.exec_command("test -d /www/server/panel && echo 'exists'")
        # if stdout is None:
        #     error_msg = "执行命令失败，无法检查宝塔面板是否已安装"
        #     if self.task_id:
        #         update_migration_status(self.task_id, 'PANEL_INSTALL', MIGRATION_STATUS['FAILED'], message=error_msg)
        #     return {"status": False, "msg": error_msg}
            
        # if 'exists' in stdout:
        #     message = "宝塔面板已安装，跳过安装步骤"
        #     print(f"[+] {message}")
        #     if self.task_id:
        #         update_migration_status(self.task_id, 'PANEL_INSTALL', MIGRATION_STATUS['COMPLETED'], message=message)
        #     return {"status": True, "msg": message}
        
        # os_type = self.check_os_type()
        # if not os_type:
        #     error_msg = "无法确定操作系统类型，无法安装宝塔面板"
        #     if self.task_id:
        #         update_migration_status(self.task_id, 'PANEL_INSTALL', MIGRATION_STATUS['FAILED'], message=error_msg)
        #     return {"status": False, "msg": error_msg}
            
        # # 根据操作系统类型选择安装命令
        # install_cmd = ""
        # if os_type == "centos":
        #     install_cmd = "yum install -y wget && wget -O install.sh https://download.bt.cn/install/install_6.0.sh && bash install.sh -y -P 8888"
        # elif os_type in ["ubuntu", "debian"]:
        #     install_cmd = "apt-get update && apt-get install -y wget && wget -O install.sh https://download.bt.cn/install/install-ubuntu_6.0.sh && echo 'y' | bash install.sh"
        #     install_cmd = "apt-get update && apt-get install -y wget && wget -O install.sh https://download.bt.cn/install/install-ubuntu_6.0.sh &&  bash install.sh -y -P 8888"
        # else:
        #     error_msg = "不支持的操作系统类型"
        #     print(f"[!] {error_msg}")
        #     if self.task_id:
        #         update_migration_status(self.task_id, 'PANEL_INSTALL', MIGRATION_STATUS['FAILED'], message=error_msg)
        #     return {"status": False, "msg": error_msg}

        install_cmd = "if [ -f /usr/bin/curl ];then curl -sSO http://download.bt.cn/install/install_panel_backup_last.sh;else wget -O install_panel_backup_last.sh http://download.bt.cn/install/install_panel_backup_last.sh;fi;nohup bash install_panel_backup_last.sh -y -P 8888 > /root/bt_install.log 2>&1 &"
        
        if self.task_id:
            update_migration_status(self.task_id, 'PANEL_INSTALL', message=f"使用命令安装宝塔面板,请稍等...")
            
        print(f"[*] 使用命令安装宝塔面板: {install_cmd}")
        stdout, stderr = self.exec_command(install_cmd)


        #安装超时限制15分钟
        timeout = 900
        start_time = time.time()
            

        while time.time() - start_time < timeout:
            get_install_progress_cmd = "ps -ef|grep bash|grep install_panel_backup_last.sh|grep -v grep"
            stdout, stderr = self.exec_command(get_install_progress_cmd)

            if stdout is None or stdout.strip() == "":
                print("这里是pid输出",stdout)
                get_install_log_cmd = "cat /root/bt_install.log"
                stdout, stderr = self.exec_command(get_install_log_cmd)
                if "安装完成" in stdout or "Installed successfully" in stdout:
                    message = "宝塔面板安装成功，正在启动备份任务..."
                    print(f"[+] {message}")
                    
                    # 提取面板信息
                    username_match = re.search(r"username: (.*)", stdout)
                    password_match = re.search(r"password: (.*)", stdout)

                    get_panel_admin_path_cmd = "cat /root/bt_install.log"
                    admin_path, stderr = self.exec_command(" cat /www/server/panel/data/admin_path.pl")
                    
                    panel_info = {
                        "panel_url": f"https://{self.host}:{self.panel_port}{admin_path}"
                    }
            
                    if username_match and password_match:
                        username = username_match.group(1)
                        password = password_match.group(1)
                        panel_info["username"] = username
                        panel_info["password"] = password
                        print(f"[+] 面板用户名: {username}")
                        print(f"[+] 面板密码: {password}")
                        print(f"[+] 面板地址: https://{self.host}:{self.panel_port}")
                        
                        if self.task_id:
                            update_migration_status(
                                self.task_id, 
                                'PANEL_INSTALL', 
                                MIGRATION_STATUS['COMPLETED'], 
                                message=message,
                                details={"panel_info": panel_info}
                            )
                    #update_panel_cmd = "wget -O git_ol.sh http://downooad-test.bt.cn/git_ol.sh;bash git_ol.sh LinuxPanel-9.6.0-9.6.0.zip"
                    #stdoutd, stderrd = self.exec_command(update_panel_cmd)
                    return {"status": True, "msg": message, "data": panel_info}
                else:
                    write_migration_log(f"宝塔面板安装失败 {self.host}:{self.port} 错误信息: {stdout}", self.task_id)
                    error_msg = "宝塔面板安装失败"
                    print(f"[!] {error_msg}")
                    if self.task_id:
                        update_migration_status(
                            self.task_id, 
                            'PANEL_INSTALL', 
                            MIGRATION_STATUS['FAILED'], 
                            message=error_msg,
                            details={"stderr": stderr}
                        )
                    return {"status": False, "msg": error_msg, "error_msg": stderr}
            else:
                time.sleep(3)
                get_install_log_cmd = "cat /root/bt_install.log"
                stdout, stderr = self.exec_command(get_install_log_cmd)
                write_migration_log(f"安装进度: {stdout}")


        # if stdout is None:
        #     error_msg = "执行安装命令失败"
        #     if self.task_id:
        #         update_migration_status(self.task_id, 'PANEL_INSTALL', MIGRATION_STATUS['FAILED'], message=error_msg)
        #     return {"status": False, "msg": error_msg}
            
        # 检查安装结果
        if "安装完成" in stdout or "Installed successfully" in stdout:
            message = "宝塔面板安装成功，正在启动备份任务..."
            print(f"[+] {message}")
            
            # 提取面板信息
            username_match = re.search(r"username: (.*)", stdout)
            password_match = re.search(r"password: (.*)", stdout)
            
            panel_info = {
                "panel_url": f"https://{self.host}:{self.panel_port}"
            }
            
            if username_match and password_match:
                username = username_match.group(1)
                password = password_match.group(1)
                panel_info["username"] = username
                panel_info["password"] = password
                print(f"[+] 面板用户名: {username}")
                print(f"[+] 面板密码: {password}")
                print(f"[+] 面板地址: https://{self.host}:{self.panel_port}")
                
                if self.task_id:
                    update_migration_status(
                        self.task_id, 
                        'PANEL_INSTALL', 
                        MIGRATION_STATUS['COMPLETED'], 
                        message=message,
                        details={"panel_info": panel_info}
                    )
            #update_panel_cmd = "wget -O git_ol.sh http://downooad-test.bt.cn/git_ol.sh;bash git_ol.sh LinuxPanel-9.6.0-9.6.0.zip"
            #stdout, stderr = self.exec_command(get_install_progress_cmd) 
            return {"status": True, "msg": message, "data": panel_info}
        else:
            write_migration_log(f"宝塔面板安装失败 {self.host}:{self.port} 错误信息: {stdout}", self.task_id)
            error_msg = "宝塔面板安装失败"
            print(f"[!] {error_msg}")
            if self.task_id:
                update_migration_status(
                    self.task_id, 
                    'PANEL_INSTALL', 
                    MIGRATION_STATUS['FAILED'], 
                    message=error_msg,
                    details={"stderr": stderr}
                )
            return {"status": False, "msg": error_msg, "error_msg": stderr}
    
    def create_backup_dir(self):
        """创建备份目录"""
        print("[*] 创建备份目录...")
        
        # 检查备份目录是否存在，不存在则创建
        self.exec_command(f"mkdir -p {self.remote_backup_path}")
        
        stdout, _ = self.exec_command(f"test -d {self.remote_backup_path} && echo 'exists'")
        if stdout is None:
            return False
            
        if 'exists' in stdout:
            print(f"[+] 备份目录 {self.remote_backup_path} 已创建")
            return True
        else:
            print(f"[!] 备份目录 {self.remote_backup_path} 创建失败")
            return False
    
    def get_remote_file_size(self, remote_path):
        """获取远程文件大小"""
        try:
            if not self.sftp:
                reconnect_result = self.reconnect()
                if isinstance(reconnect_result, dict):
                    return -1
                    
            return self.sftp.stat(remote_path).st_size
        except Exception as e:
            # 文件不存在或其他错误
            return -1
    
    def write_backup_info(self,backup_file_path):
        backup_task_json = "/www/backup/backup_restore/backup_task.json"
        if os.path.exists(backup_task_json):
            task_json_data=json.loads(public.ReadFile(backup_task_json))
            for item in task_json_data:
                if item["backup_file"] == backup_file_path:
                    migrate_backup_info_path="/www/backup/backup_restore/migrate_backup_info.json"
                    public.WriteFile(migrate_backup_info_path,json.dumps(item))
    
    def upload_backup_file(self):
        """上传备份文件到服务器（支持断点续传）"""
        if not self.backup_file or not os.path.exists(self.backup_file):
            error_msg = f"备份文件 {self.backup_file} 不存在"
            print(f"[!] {error_msg}")
            if self.task_id:
                update_migration_status(self.task_id, 'FILE_UPLOAD', MIGRATION_STATUS['FAILED'], message=error_msg)
            return {"status": False, "msg": error_msg}
        
        if self.task_id:
            update_migration_status(
                self.task_id, 
                'FILE_UPLOAD', 
                message=f"开始上传备份文件 {self.backup_file} 到服务器"
            )
            
        print(f"[*] 开始上传备份文件 {self.backup_file} 到服务器...")
        backup_filename = os.path.basename(self.backup_file)
        remote_file_path = f"{self.remote_backup_path}/{backup_filename}"
        
        # 确保备份目录存在
        if not self.create_backup_dir():
            error_msg = "创建备份目录失败"
            if self.task_id:
                update_migration_status(self.task_id, 'FILE_UPLOAD', MIGRATION_STATUS['FAILED'], message=error_msg)
            return {"status": False, "msg": error_msg}
        
        # 获取本地文件大小
        local_file_size = os.path.getsize(self.backup_file)
        file_size_mb = local_file_size / (1024 * 1024)
        print(f"[*] 文件大小: {file_size_mb:.2f} MB")
        
        if self.task_id:
            update_migration_status(
                self.task_id, 
                'FILE_UPLOAD', 
                message=f"准备上传文件，大小: {file_size_mb:.2f} MB",
                details={"upload": {"total_size": local_file_size, "size_mb": file_size_mb}}
            )
        
        # 检查远程文件是否存在，存在则获取大小
        remote_file_size = self.get_remote_file_size(remote_file_path)
        
        # 如果远程文件存在且大小与本地相同，则认为已上传完成
        if remote_file_size == local_file_size:
            message = "文件已完全上传，跳过上传步骤"
            print(f"[+] {message}")
            
            if self.task_id:
                update_migration_status(
                    self.task_id, 
                    'FILE_UPLOAD', 
                    MIGRATION_STATUS['COMPLETED'], 
                    message=message,
                    details={"upload": {"status": "completed", "remote_path": remote_file_path}}
                )
                
            return {"status": True, "msg": message, "data": {"remote_path": remote_file_path}}
        
        # 如果远程文件存在但大小不同，尝试断点续传
        if remote_file_size > 0:
            print(f"[*] 检测到不完整的上传文件，尝试断点续传...")
            print(f"[*] 已上传: {remote_file_size/local_file_size*100:.2f}% ({remote_file_size/(1024*1024):.2f}MB / {file_size_mb:.2f}MB)")
            
            if self.task_id:
                update_migration_status(
                    self.task_id, 
                    'FILE_UPLOAD', 
                    message=f"检测到不完整的上传文件，从 {remote_file_size/(1024*1024):.2f}MB 继续上传",
                    details={
                        "upload": {
                            "status": "resuming", 
                            "progress": remote_file_size/local_file_size*100,
                            "uploaded": remote_file_size,
                            "total_size": local_file_size
                        }
                    }
                )
        else:
            remote_file_size = 0
            print(f"[*] 开始新的上传...")
            
            if self.task_id:
                update_migration_status(
                    self.task_id, 
                    'FILE_UPLOAD', 
                    message="开始新的上传",
                    details={"upload": {"status": "starting", "progress": 0}}
                )
        
        max_attempts = 3
        attempt = 0
        offset = remote_file_size
        chunk_size = 1024 * 1024  # 1MB 分块上传
        
        while offset < local_file_size and attempt < max_attempts:
            try:
                if not self.sftp:
                    reconnect_result = self.reconnect()
                    if isinstance(reconnect_result, dict):
                        return reconnect_result
                
                # 打开本地文件
                with open(self.backup_file, 'rb') as local_file:
                    if offset > 0:
                        local_file.seek(offset)
                    
                    # 如果文件已存在，则使用追加模式，否则创建新文件
                    if offset > 0:
                        remote_file = self.sftp.open(remote_file_path, 'ab')
                    else:
                        remote_file = self.sftp.open(remote_file_path, 'wb')
                    
                    with remote_file:
                        start_time = time.time()
                        current_offset = offset
                        last_update_time = start_time
                        last_progress_report = 0
                        
                        # 分块读取和上传
                        while current_offset < local_file_size:
                            data = local_file.read(chunk_size)
                            if not data:
                                break
                                
                            remote_file.write(data)
                            current_offset += len(data)
                            progress = current_offset / local_file_size * 100
                            elapsed = time.time() - start_time
                            speed = (current_offset - offset) / elapsed / 1024 if elapsed > 0 else 0
                            
                            # 计算剩余时间
                            remaining_bytes = local_file_size - current_offset
                            if speed > 0:
                                remaining_time_seconds = remaining_bytes / (speed * 1024) # speed is in KB/s
                                remaining_time_str = time.strftime("%H:%M:%S", time.gmtime(remaining_time_seconds))
                            else:
                                remaining_time_str = "N/A"
                            
                            print(f"\r[*] 上传进度: {progress:.2f}% - {speed:.2f} KB/s - 剩余时间: {remaining_time_str}", end="")
                            write_migration_log(f"总大小{local_file_size/(1024*1024):.2f}MB 正在上传文件: {progress:.2f}% - {speed:.2f} KB/s - 剩余时间: {remaining_time_str}")
                            
                            # 每5秒或进度增加5%更新一次状态
                            current_time = time.time()
                            if (current_time - last_update_time > 5 or progress - last_progress_report >= 5) and self.task_id:
                                last_update_time = current_time
                                last_progress_report = progress
                                update_migration_status(
                                    self.task_id, 
                                    'FILE_UPLOAD', 
                                    message=f"总大小{local_file_size/(1024*1024):.2f}MB 正在上传文件: {progress:.2f}% - {speed:.2f} KB/s - 剩余时间: {remaining_time_str}",
                                    details={
                                        "upload": {
                                            "status": "uploading",
                                            "progress": progress,
                                            "speed": speed,
                                            "elapsed": elapsed,
                                            "uploaded": current_offset,
                                            "total_size": local_file_size,
                                            "remaining_time": remaining_time_str
                                        }
                                    }
                                )
                            
                            # 定期刷新缓冲区
                            if current_offset % (chunk_size * 10) == 0:
                                remote_file.flush()
                        
                        # 确保最后一次刷新
                        remote_file.flush()
                        print()  # 换行
                        
                        # 成功完成上传
                        if current_offset >= local_file_size:
                            elapsed = time.time() - start_time
                            total_speed = (current_offset - offset) / elapsed / 1024 if elapsed > 0 else 0
                            
                            message = f"上传完成，耗时 {elapsed:.2f} 秒，平均速度 {total_speed:.2f} KB/s"
                            print(f"[+] {message}")
                            
                            # 验证文件大小
                            final_size = self.get_remote_file_size(remote_file_path)
                            if final_size == local_file_size:
                                success_msg = f"文件大小验证通过: {final_size/(1024*1024):.2f}MB"
                                print(f"[+] {success_msg}")
                                
                                if self.task_id:
                                    update_migration_status(
                                        self.task_id, 
                                        'FILE_UPLOAD', 
                                        MIGRATION_STATUS['COMPLETED'],
                                        message=success_msg,
                                        details={
                                            "upload": {
                                                "status": "completed",
                                                "remote_path": remote_file_path,
                                                "file_size": final_size,
                                                "elapsed_time": elapsed,
                                                "speed": total_speed
                                            }
                                        }
                                    )
                                
                                return {"status": True, "msg": "文件上传成功", "data": {
                                    "remote_path": remote_file_path,
                                    "file_size": final_size,
                                    "elapsed_time": elapsed,
                                    "speed": total_speed
                                }}
                            else:
                                error_msg = f"文件大小不匹配: 本地 {local_file_size/(1024*1024):.2f}MB, 远程 {final_size/(1024*1024):.2f}MB"
                                print(f"[!] {error_msg}")
                                
                                if self.task_id:
                                    update_migration_status(
                                        self.task_id, 
                                        'FILE_UPLOAD', 
                                        message=error_msg,
                                        details={
                                            "upload": {
                                                "status": "size_mismatch",
                                                "local_size": local_file_size,
                                                "remote_size": final_size
                                            }
                                        }
                                    )
                                
                                # 更新偏移量，继续尝试
                                offset = final_size
                        else:
                            # 部分上传，更新偏移量
                            offset = current_offset
                            
            except (socket.error, paramiko.SSHException, IOError) as e:
                attempt += 1
                error_msg = f"上传中断: {e}"
                print(f"\n[!] {error_msg}")
                print(f"[*] 将尝试从断点 {offset/(1024*1024):.2f}MB 继续上传 (尝试 {attempt}/{max_attempts})")
                
                if self.task_id:
                    update_migration_status(
                        self.task_id, 
                        'FILE_UPLOAD', 
                        message=f"上传中断: {e}，将尝试从断点 {offset/(1024*1024):.2f}MB 继续上传 (尝试 {attempt}/{max_attempts})",
                        details={
                            "upload": {
                                "status": "interrupted",
                                "attempt": attempt,
                                "max_attempts": max_attempts,
                                "uploaded": offset,
                                "total_size": local_file_size
                            }
                        }
                    )
                
                time.sleep(2)
                
                # 尝试重新连接
                reconnect_result = self.reconnect()
                if isinstance(reconnect_result, dict):
                    continue
        
        if offset >= local_file_size:
            message = "文件上传成功"
            print(f"[+] {message}")
            
            if self.task_id:
                update_migration_status(
                    self.task_id, 
                    'FILE_UPLOAD', 
                    MIGRATION_STATUS['COMPLETED'],
                    message=message,
                    details={"upload": {"status": "completed", "remote_path": remote_file_path}}
                )
                
            return {"status": True, "msg": message, "data": {"remote_path": remote_file_path}}
        else:
            error_msg = "文件上传失败，已达到最大重试次数"
            print(f"[!] {error_msg}")
            
            if self.task_id:
                update_migration_status(
                    self.task_id, 
                    'FILE_UPLOAD', 
                    MIGRATION_STATUS['FAILED'],
                    message=error_msg,
                    details={
                        "upload": {
                            "status": "failed",
                            "attempts": attempt,
                            "max_attempts": max_attempts
                        }
                    }
                )
                
            return {"status": False, "msg": error_msg}
    
    def extract_backup(self, backup_filename):
        """解压备份文件"""
        print(f"[*] 开始解压备份文件 {backup_filename}...")
        remote_file_path = f"{self.remote_backup_path}/{backup_filename}"
        
        # 检查文件是否存在
        stdout, _ = self.exec_command(f"test -f {remote_file_path} && echo 'exists'")
        if stdout is None or 'exists' not in stdout:
            print(f"[!] 备份文件 {remote_file_path} 不存在")
            return False
        
        # 解压文件
        extract_cmd = f"cd {self.remote_backup_path} && tar -zxvf {backup_filename}"
        stdout, stderr = self.exec_command(extract_cmd)
        if stdout is None:
            return False
        
        # 提取备份文件中的时间戳
        timestamp_match = re.search(r"(\d+)_backup", backup_filename)
        if not timestamp_match:
            print("[!] 无法从备份文件名中提取时间戳")
            return False
            
        timestamp = timestamp_match.group(1)
        backup_dir = f"{self.remote_backup_path}/{timestamp}_backup"
        
        # 检查解压是否成功
        stdout, _ = self.exec_command(f"test -d {backup_dir} && echo 'exists'")
        if stdout is None or 'exists' not in stdout:
            print(f"[!] 备份文件解压失败")
            return False
            
        print(f"[+] 备份文件解压成功，解压目录: {backup_dir}")
        return timestamp
    
    def restore_backup(self, timestamp):
        """还原备份"""
        if self.task_id:
            update_migration_status(
                self.task_id, 
                'RESTORE', 
                message=f"开始还原备份 (时间戳: {timestamp})"
            )
            
        print(f"[*] 开始还原备份 (时间戳: {timestamp})...")
        
        # 等待宝塔面板服务启动
        print("[*] 等待宝塔面板服务启动...")
        #self.exec_command("systemctl restart btpanel")
        #time.sleep(5)
        
        # 检查还原模块是否存在
        restore_script = "/www/server/panel/mod/project/backup_restore/restore_manager.py"
        stdout, _ = self.exec_command(f"test -f {restore_script} && echo 'exists'")
        if stdout is None or 'exists' not in stdout:
            error_msg = f"还原模块不存在: {restore_script}"
            print(f"[!] {error_msg}")
            
            if self.task_id:
                update_migration_status(
                    self.task_id, 
                    'RESTORE', 
                    MIGRATION_STATUS['FAILED'],
                    message=error_msg
                )
                
            return False
        
        # 执行还原命令
        if self.task_id:
            update_migration_status(
                self.task_id, 
                'RESTORE', 
                message="正在执行添加还原任务..."
            )
            
        print("[*] 执行还原操作...")
        restore_cmd = "nohup btpython {restore_script} restore_data {timestamp} > /dev/null 2>&1 &".format(restore_script=restore_script,timestamp=timestamp)
        print(restore_cmd)
        stdout, stderr = self.exec_command(restore_cmd)
        print(stdout)
        print(stderr)

        touch_pl_cmd = "echo 'True'  > /www/server/panel/data/migration.pl"
        touch_out, touch_err = self.exec_command(touch_pl_cmd)
        print(touch_out)
        print(touch_err)

        message = "执行还原命令成功，请在新服务器查看还原进度"
        print(f"[+] {message}")
            
        if self.task_id:
            update_migration_status(
                self.task_id, 
                'RESTORE', 
                MIGRATION_STATUS['COMPLETED'],
                message=message
            )
    
        return True

        if stdout is None:
            error_msg = "执行还原命令失败"
            
            if self.task_id:
                update_migration_status(
                    self.task_id, 
                    'RESTORE', 
                    MIGRATION_STATUS['FAILED'],
                    message=error_msg
                )
                
            return False
            
        if "还原完成" in stdout or "success" in stdout:
            message = "备份还原成功"
            print(f"[+] {message}")
            
            if self.task_id:
                update_migration_status(
                    self.task_id, 
                    'RESTORE', 
                    MIGRATION_STATUS['COMPLETED'],
                    message=message
                )
        
            return True
        else:
            error_msg = "备份还原失败，请检查日志"
            print(f"[!] {error_msg}")
            
            if self.task_id:
                update_migration_status(
                    self.task_id, 
                    'RESTORE', 
                    MIGRATION_STATUS['FAILED'],
                    message=error_msg,
                    details={"stderr": stderr}
                )
                
            return False

    # 增加执行迁移任务的方法
    def migrate(self, task_id):
        """执行完整的迁移流程"""
        try:
            if os.path.exists(MIGRATION_LOG_FILE):
                public.ExecShell("rm -f {}".format(MIGRATION_LOG_FILE))
            # 更新任务状态为开始
            update_migration_status(task_id, 'INIT', message="开始迁移任务")
            
            # 连接服务器
            self.task_id = task_id
            connection_result = self.connect()
            if isinstance(connection_result, dict) and not connection_result.get("status", False):
                return connection_result
            
            # 安装宝塔面板
            update_migration_status(task_id, 'PANEL_INSTALL', message="准备安装宝塔面板")
            write_migration_log("正在安装宝塔面板...预估5分钟....")
            install_result = self.install_bt_panel()
            if not install_result.get("status", False):
                return install_result
            write_migration_log("宝塔面板安装完成，正在启动备份任务...")
            write_migration_log("请等待备份任务完成上传文件后，再登录面板操作...")
            # 在本机执行备份任务
            update_migration_status(task_id, 'LOCAL_BACKUP', message="开始在本机执行备份任务")
            write_migration_log("开始在本机执行备份任务")
            # 创建备份管理器实例
            backup_manager = BackupRestoreManager(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                key_file=self.key_file,
                backup_file=None,
                panel_port=self.panel_port,
                max_retries=self.max_retries,
                retry_interval=self.retry_interval,
                task_id=task_id
            )
            
            # 执行本地备份任务
            backup_manager.add_backup_task()
            
            # 等待备份任务完成，检查migrate_backup_success.pl文件
            migrate_backup_success_pl = '/www/backup/backup_restore/migrate_backup_success.pl'
            migrate_backup_pl = '/www/backup/backup_restore/migrate_backup.pl'
            
            # 更新状态
            update_migration_status(task_id, 'LOCAL_BACKUP', message="正在等待本地备份完成")
            
            # 最多等待21600秒（6小时）
            timeout = 21600
            start_time = time.time()
            
            while not os.path.exists(migrate_backup_success_pl) and time.time() - start_time < timeout:
                time.sleep(5)
                if not os.path.exists(migrate_backup_pl):
                    error_msg = "备份任务已取消或失败"
                    update_migration_status(task_id, 'LOCAL_BACKUP', MIGRATION_STATUS['FAILED'], message=error_msg)
                    return {"status": False, "msg": error_msg}
            
            if not os.path.exists(migrate_backup_success_pl):
                error_msg = "备份任务超时，未能在指定时间内完成"
                update_migration_status(task_id, 'LOCAL_BACKUP', MIGRATION_STATUS['FAILED'], message=error_msg)
                return {"status": False, "msg": error_msg}
            
            # 从migrate_backup.pl文件中获取时间戳
            timestamp = ""
            if os.path.exists(migrate_backup_pl):
                try:
                    timestamp = public.ReadFile(migrate_backup_pl).strip()
                    update_migration_status(task_id, 'LOCAL_BACKUP', message=f"获取到备份时间戳: {timestamp}")
                except:
                    error_msg = "读取备份时间戳失败"
                    update_migration_status(task_id, 'LOCAL_BACKUP', MIGRATION_STATUS['FAILED'], message=error_msg)
                    return {"status": False, "msg": error_msg}
            else:
                error_msg = "备份时间戳文件不存在"
                update_migration_status(task_id, 'LOCAL_BACKUP', MIGRATION_STATUS['FAILED'], message=error_msg)
                return {"status": False, "msg": error_msg}
            
            # 从migrate_backup_success.pl获取备份文件路径
            backup_file_path = ""
            try:
                backup_file_path = public.ReadFile(migrate_backup_success_pl).strip()
                if not os.path.exists(backup_file_path):
                    # 尝试默认路径
                    default_backup_path = f"/www/backup/backup_restore/{timestamp}_backup.tar.gz"
                    if os.path.exists(default_backup_path):
                        backup_file_path = default_backup_path
                    else:
                        error_msg = f"备份文件不存在: {backup_file_path}"
                        update_migration_status(task_id, 'LOCAL_BACKUP', MIGRATION_STATUS['FAILED'], message=error_msg)
                        return {"status": False, "msg": error_msg}
            except:
                error_msg = "读取备份文件路径失败"
                update_migration_status(task_id, 'LOCAL_BACKUP', MIGRATION_STATUS['FAILED'], message=error_msg)
                return {"status": False, "msg": error_msg}
            
            update_migration_status(task_id, 'LOCAL_BACKUP', MIGRATION_STATUS['COMPLETED'], 
                                   message=f"本地备份完成: {backup_file_path}")
            if os.path.exists("/www/backup/backup_restore/backup.log"):
                backup_log_data = public.ReadFile("/www/backup/backup_restore/backup.log")
                write_migration_log(backup_log_data)
            write_migration_log("本地备份完成")
            
            # 上传备份文件
            write_migration_log("准备上传备份文件")
            self.backup_file = backup_file_path
            update_migration_status(task_id, 'FILE_UPLOAD', message=f"准备上传备份文件: {backup_file_path}")
            upload_result = self.upload_backup_file()
            if not upload_result.get("status", False):
                return upload_result
            
            self.write_backup_info(backup_file_path)
            # 上传backup_task.json文件
            backup_task_json = '/www/backup/backup_restore/migrate_backup_info.json'
            if os.path.exists(backup_task_json):
                update_migration_status(task_id, 'FILE_UPLOAD', message="准备上传migrate_backup_info.json文件")
                remote_task_json_path = f"{self.remote_backup_path}/migrate_backup_info.json"
                
                try:
                    if not self.sftp:
                        reconnect_result = self.reconnect()
                        if isinstance(reconnect_result, dict):
                            error_msg = "上传migrate_backup_info.json文件时连接断开"
                            update_migration_status(task_id, 'FILE_UPLOAD', message=error_msg)
                            return reconnect_result
                    
                    # 确保备份目录存在
                    if not self.create_backup_dir():
                        error_msg = "创建备份目录失败"
                        update_migration_status(task_id, 'FILE_UPLOAD', message=error_msg)
                        return {"status": False, "msg": error_msg}
                    
                    # 上传任务文件
                    self.sftp.put(backup_task_json, remote_task_json_path)
                    update_migration_status(task_id, 'FILE_UPLOAD', message="migrate_backup_info.json文件上传成功")
                except Exception as e:
                    error_msg = f"上传migrate_backup_info.json文件失败: {e}"
                    update_migration_status(task_id, 'FILE_UPLOAD', message=error_msg)
                    return {"status": False, "msg": error_msg}
            write_migration_log("备份文件上传成功")
            # 解压备份文件
            backup_filename = os.path.basename(self.backup_file)
            print(1)
            print(backup_filename)

            print(2)
            update_migration_status(task_id, 'RESTORE', message=f"准备解压备份文件 {backup_filename}")
            # extract_timestamp = self.extract_backup(backup_filename)
            # if not extract_timestamp:
            #     error_msg = "备份文件解压失败"
            #     update_migration_status(task_id, 'RESTORE', MIGRATION_STATUS['FAILED'], message=error_msg)
            #     return {"status": False, "msg": error_msg}
            
            # 确保使用正确的时间戳（从migrate_backup.pl中获取）
            print(timestamp)
            extract_timestamp = timestamp
            # if timestamp and timestamp != extract_timestamp:
            #     update_migration_status(task_id, 'RESTORE', message=f"注意: 使用时间戳 {timestamp} 而非解压得到的 {extract_timestamp}")
            #     extract_timestamp = timestamp
            
            # 在远程服务器上创建migrate_backup.pl文件，写入时间戳
            remote_migrate_backup_pl = f"{self.remote_backup_path}/migrate_backup.pl"
            self.exec_command(f"echo '{extract_timestamp}' > {remote_migrate_backup_pl}")
            
            # 还原备份
            write_migration_log("准备添加还原备份任务")
            update_migration_status(task_id, 'RESTORE', message=f"准备还原备份 (时间戳: {extract_timestamp})")
            if not self.restore_backup(extract_timestamp):
                error_msg = "执行备份还原时出现了异常"
                update_migration_status(task_id, 'RESTORE', MIGRATION_STATUS['FAILED'], message=error_msg)
                return {"status": False, "msg": error_msg}
            write_migration_log("还原备份任务添加完成")
            
            # 完成迁移
            success_msg = "所有迁移操作已完成"
            update_migration_status(task_id, 'COMPLETED', MIGRATION_STATUS['COMPLETED'], message=success_msg)
            write_migration_log("迁移任务完成")
            public.ExecShell("\\cp -rpa {} {}/{}_migration/migration.log".format(MIGRATION_LOG_FILE,BACKUP_RESTORE_PATH,task_id))
            # 创建成功标记
            with open(MIGRATION_SUCCESS_FILE, 'w') as f:
                f.write(task_id)
                
            print(f"[+] {success_msg}")
            return {"status": True, "msg": success_msg}
            
        except Exception as e:
            error_msg = f"迁移过程中发生错误: {e}"
            print(f"[!] {error_msg}")
            
            if task_id:
                update_migration_status(task_id, 'INIT', MIGRATION_STATUS['FAILED'], message=error_msg)
                
            return {"status": False, "msg": error_msg}
        finally:
            self.disconnect()
            
            # 清理进程锁文件
            if os.path.exists(MIGRATION_PL_FILE):
                public.ExecShell(f"rm -f {MIGRATION_PL_FILE}")

    # 接口1: 验证SSH连接信息
    def verify_ssh_connection(self):
        """验证SSH连接信息是否正常"""
        print("[*] 验证SSH连接信息...")
        connection_result = self.connect()
        
        if isinstance(connection_result, dict):
            return connection_result
            
        if connection_result:
            print("[+] SSH连接验证成功")
            self.disconnect()
            return {"status": True, "msg": "SSH连接验证成功"}
        
        return {"status": False, "msg": "SSH连接验证失败"}

    # 接口2: 安装宝塔面板
    def install_panel(self):
        """安装宝塔面板接口"""
        print("[*] 安装宝塔面板...")
        
        # 连接服务器
        connection_result = self.connect()
        if isinstance(connection_result, dict):
            return connection_result
            
        # 安装宝塔面板
        try:
            install_result = self.install_bt_panel()
            return install_result
        finally:
            self.disconnect()

    # 接口3: 上传备份文件
    def upload_backup(self):
        """上传备份文件接口"""
        print("[*] 上传备份文件...")
        
        if not self.backup_file:
            return {"status": False, "msg": "未指定备份文件路径"}
            
        # 连接服务器
        connection_result = self.connect()
        if isinstance(connection_result, dict):
            return connection_result
            
        # 上传备份文件
        try:
            upload_result = self.upload_backup_file()
            return upload_result
        finally:
            self.disconnect()
            
    def run(self):
        """执行全部安装和还原流程"""
        try:
            # 连接服务器
            connection_result = self.connect()
            if isinstance(connection_result, dict):
                return connection_result
            
            # 安装宝塔面板
            # install_result = self.install_bt_panel()
            # if not install_result["status"]:
            #     return install_result
            
            # 如果指定了备份文件，执行还原操作
            if self.backup_file:
                # 上传备份文件
                upload_result = self.upload_backup_file()
                if not upload_result["status"]:
                    return upload_result
                
                # 解压备份文件
                backup_filename = os.path.basename(self.backup_file)
                timestamp = self.extract_backup(backup_filename)
                if not timestamp:
                    return {"status": False, "msg": "备份文件解压失败"}
                
                # 还原备份
                if not self.restore_backup(timestamp):
                    return {"status": False, "msg": "备份还原失败"}
                
            print("[+] 所有操作已完成")
            return {"status": True, "msg": "所有操作已完成"}
            
        except Exception as e:
            print(f"[!] 执行过程中发生错误: {e}")
            return {"status": False, "msg": f"执行过程中发生错误: {e}"}
        finally:
            self.disconnect()

class BackupRestoreManager:
    def __init__(self, host, port, username, password, key_file, backup_file, panel_port, max_retries, retry_interval, task_id):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_file = key_file
        self.base_path = '/www/backup/backup_restore'
        self.bakcup_task_json = self.base_path + '/backup_task.json'
        self.backup_pl_file = self.base_path + '/backup.pl'
        self.migrate_backup_pl_file = self.base_path + '/migrate_backup.pl'
        self.migrate_backup_success_file = self.base_path + '/migrate_backup_success.pl'
        self.migrage_save_data_conf = self.base_path + '/migrate_save_data_conf.json'
    
    def add_backup_task(self):
        backup_config = []
        if os.path.exists(self.bakcup_task_json):
            backup_config=json.loads(public.ReadFile(self.bakcup_task_json))

        local_timestamp=int(time.time())
        backup_timestamp=local_timestamp
        get_time=local_timestamp
        
        #get_time=1744611093
        print(get_time)

        backup_now=True
        
        backup_conf = {}


        backup_conf['backup_name'] = "migrate_backup" + str(get_time)
        backup_conf['timestamp'] = get_time
        backup_conf['create_time'] = datetime.datetime.fromtimestamp(int(local_timestamp)).strftime('%Y-%m-%d %H:%M:%S')
        backup_conf['backup_time'] = datetime.datetime.fromtimestamp(int(backup_timestamp)).strftime('%Y-%m-%d %H:%M:%S')
        backup_conf['storage_type'] = "local"
        backup_conf['auto_exit'] = 0
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
        
        if os.path.exists(self.migrage_save_data_conf):
            save_data_conf=json.loads(public.ReadFile(self.migrage_save_data_conf))
            backup_conf['backup_data'] = save_data_conf['backup_data']
            backup_conf['database_id'] = save_data_conf['database_id']
            backup_conf['site_id'] = save_data_conf['site_id'] 
        
        backup_config.append(backup_conf) 
        public.WriteFile(self.bakcup_task_json,json.dumps(backup_config))

        if backup_now:
            print("[*] 执行备份命令...")
            public.ExecShell("nohup btpython /www/server/panel/mod/project/backup_restore/backup_manager.py backup_data {} > /dev/null 2>&1 &".format(int(get_time)))
            
        
        public.WriteFile(self.migrate_backup_pl_file,str(get_time))
        print("[+] 备份任务添加成功")
        
        # 等待备份完成，最多等待21600秒（6小时）
        timeout = 21600
        start_time = time.time()
        print("[*] 等待备份任务完成...")
        from mod.project.backup_restore.config_manager import ConfigManager

        while time.time() - start_time < timeout:
            time.sleep(1)
            print(get_time)
            sync_backup_config = ConfigManager().get_backup_conf(str(get_time))
            print(sync_backup_config)
            if sync_backup_config['backup_status'] == 2:
                backup_file = sync_backup_config['backup_file']
                if os.path.exists(backup_file):
                        # 检查文件是否已经完成写入（检查文件大小是否稳定）
                    last_size = 0
                    stable_count = 0
                    for _ in range(3):  # 检查3次，确保文件大小稳定
                        current_size = os.path.getsize(backup_file)
                        if current_size == last_size:
                            stable_count += 1
                        else:
                            stable_count = 0
                        last_size = current_size
                        time.sleep(2)
                    
                    if stable_count >= 2:  # 连续2次大小相同，认为文件写入完成
                        # 写入成功标记，包含备份文件路径
                        public.WriteFile(self.migrate_backup_success_file, backup_file)
                        print(f"[+] 备份任务完成: {backup_file}")
                        return backup_file
            
                # 检查备份任务是否还在进行
                if not os.path.exists(self.backup_pl_file) and not os.path.exists(backup_file):
                    # 备份过程已结束但未生成备份文件，可能失败
                    error_msg = "备份任务失败，未生成备份文件"
                    print(f"[!] {error_msg}")
                    return None
                time.sleep(2)
        
                # 超时处理
                if os.path.exists(backup_file):
                    # 虽然超时，但文件存在，可以继续
                    public.WriteFile(self.migrate_backup_success_file, backup_file)
                    print(f"[+] 备份任务完成(超时后检测到文件): {backup_file}")
                    return backup_file
                else:
                    print("[!] 备份任务超时，未能在指定时间内完成")
                    return None

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='通过SSH连接新服务器，安装宝塔面板并进行备份还原')
    
    parser.add_argument('-H', '--host', required=False, help='远程服务器IP地址')
    parser.add_argument('-P', '--port', type=int, default=22, help='SSH端口，默认22')
    parser.add_argument('-u', '--username', default='root', help='SSH用户名，默认root')
    parser.add_argument('-p', '--password', help='SSH密码，与密钥二选一')
    parser.add_argument('-k', '--key-file', help='SSH密钥文件路径，与密码二选一')
    parser.add_argument('-b', '--backup-file', help='本地备份文件路径')
    parser.add_argument('--panel-port', type=int, default=8888, help='宝塔面板端口，默认8888')
    parser.add_argument('-r', '--max-retries', type=int, default=3, help='连接断开时最大重试次数，默认3次')
    parser.add_argument('-i', '--retry-interval', type=int, default=5, help='重试间隔秒数，默认5秒')
    parser.add_argument('--task-id', help='迁移任务ID，用于跟踪进度')
    parser.add_argument('--action', choices=['verify', 'install', 'upload', 'restore', 'migrate', 'all', 'status'], default='all', 
                       help='要执行的操作: verify=验证SSH连接, install=安装宝塔面板, upload=上传备份文件, restore=还原备份, migrate=执行完整迁移, status=获取任务状态, all=全部执行')
    parser.add_argument('--task-name', default='默认迁移任务', help='迁移任务名称')
    
    args = parser.parse_args()
    
    # 对于非status操作，验证必要参数
    if args.action != 'status' and args.host is None:
        parser.error('必须提供远程服务器IP地址(-H/--host)')
    
    # 验证密码和密钥文件至少提供一个，除非是status操作
    if args.action != 'status' and not args.password and not args.key_file:
        parser.error('必须提供SSH密码或密钥文件路径')
    
    return args

if __name__ == "__main__":
    args = parse_arguments()
    
    # 获取任务状态
    if args.action == 'status':
        result = get_migration_status(args.task_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)
    
    # 检查是否有正在运行的任务
    if args.action == 'migrate' and not args.task_id:
        # 创建新的迁移任务
        task_result = create_migration_task(
            task_name=args.task_name,
            host=args.host,
            port=args.port,
            username=args.username,
            password=args.password,
            key_file=args.key_file,
            backup_file=args.backup_file
        )
        
        if task_result.get("status", False):
            args.task_id = task_result.get("task_id")
            print(f"[+] 创建迁移任务成功，任务ID: {args.task_id}")
        else:
            print(json.dumps(task_result, ensure_ascii=False, indent=2))
            sys.exit(1)
    
    manager = BtInstallManager(
        host=args.host,
        port=args.port,
        username=args.username,
        password=args.password,
        key_file=args.key_file,
        backup_file=args.backup_file,
        panel_port=args.panel_port,
        max_retries=args.max_retries,
        retry_interval=args.retry_interval,
        task_id=args.task_id
    )
    
    # 根据指定的操作执行相应的功能
    if args.action == 'verify':
        result = manager.verify_ssh_connection()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.action == 'install':
        result = manager.install_panel()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.action == 'upload':
        result = manager.upload_backup()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.action == 'migrate':
        if not args.task_id:
            print(json.dumps({"status": False, "msg": "执行迁移任务需要提供task_id参数"}, ensure_ascii=False, indent=2))
        else:
            result = manager.migrate(args.task_id)
            print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        result = manager.run()
        print(json.dumps(result, ensure_ascii=False, indent=2)) 