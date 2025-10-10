# -*- coding: utf-8 -*-
"""
MySQL 主从复制同步服务模块
负责主从同步的核心业务逻辑
"""

import os
from typing import Dict, Any, List
from urllib.parse import urlparse
import sys

if '/www/server/panel/class' not in sys.path:
    sys.path.insert(0, '/www/server/panel/class')
if '/www/server/panel' not in sys.path:
    sys.path.insert(0, '/www/server/panel')

import public
try:
    from .config_manager import ConfigManager
    from .mysql_manager import MySQLManager
    from .slave_manager import SlaveManager
    from .bt_api import BtApi
    from .firewall_manager import FirewallManager
except:
    from config_manager import ConfigManager
    from mysql_manager import MySQLManager
    from slave_manager import SlaveManager
    from bt_api import BtApi
    from firewall_manager import FirewallManager



class SyncService:
    """同步服务"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.mysql_manager = MySQLManager()
        self.slave_manager = SlaveManager()
        self.firewall_manager = FirewallManager()

    def add_slave_server(self, panel_addr: str, panel_key: str, master_ip: str, 
                        slave_ip: str, db_name: str, err_code: str, sync_type: str) -> Dict[str, Any]:
        """添加主从配置"""
        # 检查是否已存在
        check_master_info = self.config_manager.get_slave_config(slave_ip)
        if check_master_info:
            return public.returnMsg(False, "已添加有主从复制信息，请勿重复添加！")

        # 验证面板地址
        parsed_url = urlparse(panel_addr.strip())
        if parsed_url.scheme not in ('http', 'https') or not parsed_url.netloc :
            return public.returnMsg(False, "请输入正确的面板地址！ 如：http://1.1.1.1:8888/ http://www.bt.cn:8888/")

        panel_addr = "{}://{}/".format(parsed_url.scheme, parsed_url.netloc)

        # 构建配置信息
        server_id = ConfigManager.get_server_id_from_ip(slave_ip)
        info_data = {
            "panel_addr": panel_addr,
            "panel_key": panel_key,
            "master_ip": master_ip,
            "slave_ip": slave_ip,
            "db_name": db_name,
            "err_code": err_code,
            "sync_type": sync_type,
            "server_id": server_id,
            "io_status": None,
            "sql_status": None,
            "config_status": "wait",
            "run_status": "stop",
            "data": {
                "step": 1,
                "progress": {},
                "steps": self.config_manager.create_default_steps(sync_type),
                "logs": []
            }
        }

        # 保存配置
        self.config_manager.add_slave_config(info_data)

        # 启动同步进程
        if sync_type == "auto":
            public.ExecShell("nohup btpython /www/server/panel/mod/project/node/mysql_slave_util/start_sync.py auto_sync_data {} > /dev/null 2>&1 &".format(slave_ip))
        elif sync_type == "manual":
            public.ExecShell("nohup btpython /www/server/panel/mod/project/node/mysql_slave_util/start_sync.py manual_sync_data {} > /dev/null 2>&1 &".format(slave_ip))
            
        return public.returnMsg(True, "添加成功")
    
    def get_panel_key(self, slave_ip: str) -> str:
        """获取面板密钥"""
        info = self.config_manager.get_slave_config(slave_ip)
        if not info:
            return False
        return info.get("panel_key")

    def auto_sync_data(self, slave_ip: str) -> bool:
        """自动同步数据"""
        info = self.config_manager.get_slave_config(slave_ip)
        if not info:
            return False

        panel_addr = info.get("panel_addr") if str(info.get("panel_addr")).endswith("/") else info.get("panel_addr") + "/"
        panel_key = info.get("panel_key")
        bt_api_obj = BtApi(panel_addr, panel_key)
        slave_panel_info = bt_api_obj.get_config()
        slave_root = slave_panel_info['mysql_root']

        # 设置为运行状态
        info["config_status"] = "running"
        self.config_manager.save_slave_config(slave_ip, info)

        # 清空日志
        sync_log_path = self.config_manager.master_slave_log_path + "/" + slave_ip + ".log"
        if os.path.exists(sync_log_path):
            public.WriteFile(sync_log_path, "")

        try:
            # 1. 防火墙配置
            print("1. 防火墙配置")
            self.firewall_manager.allow_master_firewall_port(slave_ip)
            
            # 2. 配置主库
            print("2. 配置主库")
            self.config_master(slave_ip)
            
            # 3. 备份数据
            print("3. 备份数据")
            self.backup_master_data(slave_ip)
            
            # 4. 创建从库数据库
            print("4. 创建从库数据库")
            self._create_slave_databases(info, bt_api_obj)
            
            # 5. 上传数据
            print("5. 上传数据")
            self._upload_data_to_slave(slave_ip, info, bt_api_obj)
            
            # 6. 导入数据
            print("6. 导入数据")
            self._import_data_to_slave(slave_ip, info, bt_api_obj, slave_root)
            
            # 7. 配置从库
            print("7. 配置从库")
            self._config_slave_final(slave_ip)
            
            # 8. 启动同步
            print("8. 启动同步")
            self._start_slave_sync(slave_ip)

            return True
        except Exception as e:
            self.config_manager.print_log(slave_ip, f"自动同步失败: {str(e)}")
            info["config_status"] = "error"
            self.config_manager.save_slave_config(slave_ip, info)
            return False

    def manual_sync_data(self, slave_ip: str) -> bool:
        """手动同步数据"""
        info = self.config_manager.get_slave_config(slave_ip)
        if not info:
            return False

        panel_addr = info.get("panel_addr") if str(info.get("panel_addr")).endswith("/") else info.get("panel_addr") + "/"
        panel_key = info.get("panel_key")
        bt_api_obj = BtApi(panel_addr, panel_key)
        slave_panel_info = bt_api_obj.get_config()

        # 设置为运行状态
        info["config_status"] = "running"
        self.config_manager.save_slave_config(slave_ip, info)

        # 清空日志
        sync_log_path = self.config_manager.master_slave_log_path + "/" + slave_ip + ".log"
        if os.path.exists(sync_log_path):
            public.WriteFile(sync_log_path, "")

        try:
            # 1. 防火墙配置
            self.firewall_manager.allow_master_firewall_port(slave_ip)
            
            # 2. 配置主库
            self.config_master(slave_ip)
            
            # 3. 备份数据
            self.backup_master_data(slave_ip)
            
            # 4. 创建从库数据库
            self._create_slave_databases(info, bt_api_obj)
            
            # 5. 等待手动导入数据
            self.config_manager.update_slave_status(
                slave_ip=slave_ip, step=2, step_index=2, 
                status="running", msg="从库数据库已创建好，等待手动将数据导入从库...."
            )

            return True
        except Exception as e:
            self.config_manager.print_log(slave_ip, f"手动同步配置失败: {str(e)}")
            info["config_status"] = "error"
            self.config_manager.save_slave_config(slave_ip, info)
            return False

    def config_master(self, slave_ip: str) -> bool:
        """配置主库"""
        self.config_manager.print_log(slave_ip, "开始配置主库")
        self.config_manager.update_slave_status(
            slave_ip=slave_ip, step=0, step_index=0, 
            status="running", msg="配置主数据库中......"
        )

        # MySQL配置
        result = self.mysql_manager.config_master(slave_ip)
        if not result.get("status"):
            self.config_manager.update_slave_status(
                slave_ip=slave_ip, step=0, step_index=0, 
                status="error", msg=result.get("msg")
            )
            return False

        # 创建从库用户
        user_result = self.mysql_manager.create_slave_user(slave_ip)
        if not user_result.get("status"):
            self.config_manager.update_slave_status(
                slave_ip=slave_ip, step=0, step_index=0, 
                status="error", msg="创建从库用户失败"
            )
            return False

        # 保存用户信息
        info = self.config_manager.get_slave_config(slave_ip)
        info["master_user"] = user_result["user"]
        info["master_password"] = user_result["password"]
        self.config_manager.save_slave_config(slave_ip, info)

        self.config_manager.update_slave_status(
            slave_ip=slave_ip, step=0, step_index=0, 
            status="done", msg="配置主数据库成功"
        )
        self.config_manager.print_log(slave_ip, "MySQL主库配置成功")
        return True

    def backup_master_data(self, slave_ip: str) -> bool:
        """备份主库数据"""
        info = self.config_manager.get_slave_config(slave_ip)
        if not info:
            return False

        self.config_manager.print_log(slave_ip, "开始备份主库数据")
        self.config_manager.update_slave_status(
            slave_ip=slave_ip, step=1, step_index=1, 
            status="running", msg="备份数据库中......"
        )

        db_name_list = info.get("db_name").split(",")
        backup_result = self.mysql_manager.backup_master_data(db_name_list)
        if not backup_result.get("status"):
            self.config_manager.update_slave_status(
                slave_ip=slave_ip, step=1, step_index=1, 
                status="error", msg="备份数据库失败"
            )
            return False

        # 保存备份信息
        info["data"]["master_data_sql"] = backup_result["backup_file"]
        info["data"]["mysql_info"] = backup_result["db_info"]
        info["data"]["sql_file_sha256"] = backup_result["file_sha256"]
        info["data"]["sql_file_size"] = backup_result["file_size"]
        self.config_manager.save_slave_config(slave_ip, info)

        self.config_manager.update_slave_status(
            slave_ip=slave_ip, step=1, step_index=1, 
            status="done", msg="备份数据库完成"
        )
        self.config_manager.print_log(slave_ip, "备份数据库完成")
        return True

    def sync_slave_config(self, slave_ip: str) -> Dict[str, Any]:
        """手动同步从库配置"""
        info = self.config_manager.get_slave_config(slave_ip)
        if not info:
            return public.returnMsg(False, "未找到同步信息，可能未开始配置，请删除重建主从")

        try:
            self.config_manager.update_slave_status(
                slave_ip=slave_ip, step=2, step_index=2, 
                status="done", msg="数据导入完成"
            )
            
            self._config_slave_final(slave_ip)
            self._start_slave_sync(slave_ip)

            return public.returnMsg(True, "同步成功")
        except Exception as e:
            return public.returnMsg(False, f"同步失败: {str(e)}")

    def _create_slave_databases(self, info: Dict[str, Any], bt_api_obj: BtApi):
        """创建从库数据库"""
        try:
            # 重新获取最新的配置信息，确保包含数据库信息
            slave_ip = info.get("slave_ip")
            if slave_ip:
                latest_info = self.config_manager.get_slave_config(slave_ip)
                if latest_info and "mysql_info" in latest_info.get("data", {}):
                    for db in latest_info["data"]["mysql_info"]:
                        bt_api_obj.create_database(db['name'], db['password'])
        except Exception as e:
            print(f"创建从库数据库异常: {e}")
            pass

    def _upload_data_to_slave(self, slave_ip: str, info: Dict[str, Any], bt_api_obj: BtApi):
        """上传数据到从库"""
        # 重新获取最新的配置信息，确保包含备份数据
        latest_info = self.config_manager.get_slave_config(slave_ip)
        if not latest_info:
            raise Exception("未找到从库配置信息")
            
        self.config_manager.update_slave_status(
            slave_ip=slave_ip, step=2, step_index=2, 
            status="running", msg="上传数据至从库......"
        )
        print("最新配置信息:", latest_info["data"])
        self.config_manager.print_log(slave_ip, "开始上传数据至从库")
        print("上传数据至从库......")
        
        # 检查备份文件信息是否存在
        if "master_data_sql" not in latest_info["data"]:
            raise Exception("备份文件信息不存在，请检查备份步骤")
            
        try:
            upload_file_result = bt_api_obj.upload_file(latest_info["data"]["master_data_sql"])
        except Exception as e:
            print("上传异常:", e)
            upload_file_result = False
        print("上传结果:", upload_file_result)
        
        if upload_file_result != True:
            self.config_manager.update_slave_status(
                slave_ip=slave_ip, step=2, step_index=2, 
                status="error", msg="上传文件失败，请尝试删除从库重新配置，或采用手动方式同步"
            )
            raise Exception("上传文件失败")

        self.config_manager.print_log(slave_ip, "上传数据完成")
        self.config_manager.update_slave_status(
            slave_ip=slave_ip, step=2, step_index=2, 
            status="done", msg="上传数据完成"
        )

    def _import_data_to_slave(self, slave_ip: str, info: Dict[str, Any], bt_api_obj: BtApi, slave_root: str):
        """导入数据到从库"""
        # 重新获取最新的配置信息，确保包含备份数据
        latest_info = self.config_manager.get_slave_config(slave_ip)
        if not latest_info:
            raise Exception("未找到从库配置信息")
            
        self.config_manager.print_log(slave_ip, "开始导入数据至从库")
        self.config_manager.update_slave_status(
            slave_ip=slave_ip, step=3, step_index=3, 
            status="running", msg="导入数据至从库......"
        )

        export_sql_file = latest_info["data"]["master_data_sql"]
        import_shell = "/www/server/mysql/bin/mysql -uroot -p{slave_root} --force < {export_sql_file}".format(
            slave_root=slave_root, export_sql_file=export_sql_file)
        
        bt_api_obj.slave_execute_command(import_shell)

        self.config_manager.print_log(slave_ip, "导入数据完成")
        self.config_manager.update_slave_status(
            slave_ip=slave_ip, step=3, step_index=3, 
            status="done", msg="导入数据完成"
        )

    def _config_slave_final(self, slave_ip: str):
        """最终配置从库"""
        step_index = 3 if self.config_manager.get_slave_config(slave_ip).get("sync_type") == "manual" else 4
        
        self.config_manager.update_slave_status(
            slave_ip=slave_ip, step=step_index + 1, step_index=step_index, 
            status="running", msg="配置从库数据库......"
        )
        
        self.slave_manager.config_slave(slave_ip)
        
        self.config_manager.update_slave_status(
            slave_ip=slave_ip, step=step_index + 1, step_index=step_index, 
            status="done", msg="从库配置成功"
        )

    def _start_slave_sync(self, slave_ip: str):
        """启动从库同步"""
        step_index = 4 if self.config_manager.get_slave_config(slave_ip).get("sync_type") == "manual" else 5
        
        start_sql = "start slave;"
        self.slave_manager.exec_shell_sql(slave_ip, start_sql)
        
        self.config_manager.update_slave_status(
            slave_ip=slave_ip, step=step_index, step_index=step_index, 
            status="done", msg="同步完成"
        )
        
        info = self.config_manager.get_slave_config(slave_ip)
        info["config_status"] = "done"
        info["run_status"] = "start"
        self.config_manager.save_slave_config(slave_ip, info)

if __name__ == '__main__':
    # 获取命令行参数
    if len(sys.argv) < 3:
        print("Usage: btpython sync_service.py <method> <ip_address>")
        sys.exit(1)
    method_name = sys.argv[1]  # 方法名
    ip_address = sys.argv[2]    # IP地址
    replicate = SyncService()  # 实例化对象
    if hasattr(replicate, method_name):  # 检查方法是否存在
        method = getattr(replicate, method_name)  # 获取方法
        method(ip_address)  # 调用方法
    else:
        print(f"Error: 方法 '{method_name}' 不存在")
