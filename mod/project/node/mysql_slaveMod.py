# -*- coding: utf-8 -*-
"""
MySQL 主从复制模块 - 前端接口层
负责处理前端请求，调用具体的业务逻辑实现
"""

import json
import os
import sys
import time
# 添加路径
if '/www/server/panel/class' not in sys.path:
    sys.path.insert(0, '/www/server/panel/class')
if '/www/server/panel' not in sys.path:
    sys.path.insert(0, '/www/server/panel')

import public
from mod.project.node.mysql_slave_util.config_manager import ConfigManager
from mod.project.node.mysql_slave_util.mysql_manager import MySQLManager
from mod.project.node.mysql_slave_util.slave_manager import SlaveManager
from mod.project.node.mysql_slave_util.sync_service import SyncService
from mod.project.node.mysql_slave_util.firewall_manager import FirewallManager


class main:
    """MySQL 主从复制主模块"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.mysql_manager = MySQLManager()
        self.slave_manager = SlaveManager()
        self.sync_service = SyncService()
        self.firewall_manager = FirewallManager()

    # ==================== 版本和检查相关 ====================
    def get_mysql_version(self, get=None):
        """获取MySQL版本"""
        version = self.mysql_manager.get_mysql_version()
        if not version:
            return public.returnMsg(False, "此功能仅支持mysql-5.7以上版本使用！")
        return public.returnMsg(True, version)

    def check_slave(self, get):
        """检查从库连接和配置"""
        required_params = ['panel_addr', 'panel_key', 'master_ip', 'slave_ip']
        for param in required_params:
            if not hasattr(get, param):
                return public.returnMsg(False, "缺少参数！ {}".format(param))
        
        return self.slave_manager.check_slave(
            get.panel_addr, get.panel_key, get.master_ip, get.slave_ip
        )

    # ==================== 主库相关 ====================
    def database_list(self, get=None):
        """获取主库数据库列表（带分页和搜索功能）"""
        try:
            # 1. 检查MySQL版本
            version_check = self.mysql_manager.get_mysql_version()
            if not version_check:
                return public.returnMsg(False, "此功能仅支持mysql-5.7以上版本使用！")
            
            # 2. 获取并验证分页参数
            search = getattr(get, 'search', '').strip() if get else ''
            p = int(getattr(get, 'p', 1)) if get and hasattr(get, 'p') else 1
            limit = int(getattr(get, 'limit', 20)) if get and hasattr(get, 'limit') else 20
            
            # 参数验证
            if p < 1:
                p = 1
            if limit < 1 or limit > 100:
                limit = 20
            
            # 3. 获取所有数据库列表
            all_data = self.mysql_manager.database_list()
            if not all_data:
                return {
                    "status": True,
                    "msg": "success",
                    "data": [],
                    "page": {
                        "current_page": p,
                        "total_pages": 0,
                        "total_count": 0,
                        "per_page": limit,
                        "has_prev": False,
                        "has_next": False,
                        "start_item": 0,
                        "end_item": 0,
                        "showing": "显示第 0 到 0 项，共 0 项"
                    },
                    "search": search,
                    "total": 0
                }
            
            # 4. 搜索过滤
            filtered_data = all_data
            if search:
                filtered_data = []
                for item in all_data:
                    # 支持按数据库名称搜索（如果item是字符串）
                    if isinstance(item, str):
                        if search.lower() in item.lower():
                            filtered_data.append(item)
                    # 如果item是字典，支持多字段搜索
                    elif isinstance(item, dict):
                        search_fields = ['name', 'database', 'db_name', 'schema_name']
                        match_found = False
                        for field in search_fields:
                            if field in item and item[field] and search.lower() in str(item[field]).lower():
                                match_found = True
                                break
                        if match_found:
                            filtered_data.append(item)
                    else:
                        # 其他类型转换为字符串进行搜索
                        if search.lower() in str(item).lower():
                            filtered_data.append(item)
            
            # 5. 计算分页参数
            total_count = len(filtered_data)
            total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0
            offset = (p - 1) * limit
            
            # 6. 获取当前页数据
            current_page_data = filtered_data[offset:offset + limit]
            
            # 7. 构建分页信息
            start_item = offset + 1 if total_count > 0 else 0
            end_item = min(offset + limit, total_count)
            
            page_info = {
                "current_page": p,
                "total_pages": total_pages,
                "total_count": total_count,
                "per_page": limit,
                "has_prev": p > 1,
                "has_next": p < total_pages,
                "prev_page": p - 1 if p > 1 else None,
                "next_page": p + 1 if p < total_pages else None,
                "start_item": start_item,
                "end_item": end_item,
                "showing": "显示第 {} 到 {} 项，共 {} 项".format(start_item, end_item, total_count)
            }
            
            # 8. 返回结果
            result = {
                "status": True,
                "msg": "success",
                "data": current_page_data,
                "page": page_info,
                "search": search,
                "total": total_count
            }
            return result
            
        except Exception as e:
            import traceback
            error_msg = "获取数据库列表失败: {}".format(str(e))
            public.WriteLog("TYPE_DATABASE", error_msg)
            return {
                "status": False,
                "msg": error_msg,
                "data": [],
                "page": {},
                "search": "",
                "total": 0
            }

    def get_master_sql_list(self, get=None):
        """获取主库备份文件列表"""
        data = self.mysql_manager.get_master_sql_list()
        result = {
            "status": True,
            "msg": "success",
            "data": data
        }
        return result

    def del_master_sql(self, get):
        """删除主库备份文件"""
        if not hasattr(get, 'path'):
            return public.returnMsg(False, "缺少参数！ path")
        
        return self.mysql_manager.del_master_sql(get.path)

    # ==================== 从库管理 ====================
    def slave_list(self, get=None):
        """获取从库列表"""
        # 检查MySQL版本
        version_check = self.mysql_manager.get_mysql_version()
        if not version_check:
            return public.returnMsg(False, "此功能仅支持mysql-5.7以上版本使用！")

        # 检查旧版本兼容性
        try:
            old_config_json = "/www/server/panel/plugin/mysql_replicate/config.json.0"
            if os.path.exists(old_config_json):
                old_config_json = json.loads(public.ReadFile(old_config_json))
                slave_list = old_config_json.get("slave")
                master_list = old_config_json.get("master")
                if slave_list and len(slave_list) > 0 and master_list and len(master_list) > 0:
                    return public.returnMsg(False, "当前主从版本不支持旧版主从同步，如需还原旧版本请在终端执行以下命令还原(不影响当前主从配置) 命令：wget -O remysql_slave.sh https://download.bt.cn/tools/remysql_slave.sh && bash remysql_slave.sh")
        except:
            pass

        all_configs = self.config_manager.get_all_slave_configs()
        if not all_configs:
            return []
        
        search_ip=None
        if get and get.search:
            search_ip=get.search

        data  = []
        for item in all_configs:
            info = {
                "slave_ip": item["slave_ip"],
                "panel_addr": item["panel_addr"],
                "panel_key": item["panel_key"],
                "err_code": item["err_code"],
                "sync_type": item["sync_type"],
                "config_status": item["config_status"],
                "run_status": item["run_status"],
                "db_name": item["db_name"]
            }
            check_slave_result = self.slave_manager.check_slave(item.get("panel_addr"), item.get("panel_key"), item.get("master_ip"), item.get("slave_ip"))
            slave_ip = item.get("slave_ip")
            slave_ip = item.get("slave_ip")
            if item.get("config_status") == "done" and check_slave_result.get("status") is True:
                try:
                    slave_status = json.loads(self.slave_manager.get_slave_info(slave_ip))
                    io_status = slave_status.get("Slave_IO_Running")
                    sql_status = slave_status.get("Slave_SQL_Running")
                    if io_status and sql_status:
                        info["io_status"] = io_status
                        info["sql_status"] = sql_status
                        if io_status != "Yes" or sql_status != "Yes":
                            info["error_msg"] = {
                                "Last_IO_Error_Timestamp": slave_status.get("Last_IO_Error_Timestamp"),
                                "Last_IO_Errno": slave_status.get("Last_IO_Errno"),
                                "Last_IO_Error": slave_status.get("Last_IO_Error"),
                                "Last_SQL_Error_Timestamp": slave_status.get("Last_SQL_Error_Timestamp"),
                                "Last_SQL_Errno": slave_status.get("Last_SQL_Errno"),
                                "Last_SQL_Error": slave_status.get("Last_SQL_Error")
                            }
                except:
                    info["io_status"] = "None"
                    info["sql_status"] = "None"
            else:
                info["io_status"] = "api_error"
                info["sql_status"] = "api_error"

            api_status_result = self.slave_manager.get_slave_mysql_status(slave_ip)
            info["api_status"] = api_status_result.get("status")
            info["api_msg"] = api_status_result.get("msg")
            data.append(info)

        if search_ip:
            data = [item for item in data if search_ip in item["slave_ip"]]

        result = {
            "status": True,
            "msg": "success",
            "data": data
        }
        return result

    def add_slave_server(self, get):
        """添加主从配置"""
        required_params = ['node_id', 'db_name', 'err_code', 'sync_type', 'master_ip', 'slave_ip']
        #required_params = ['panel_addr', 'panel_key', 'db_name', 'err_code', 'sync_type', 'master_ip', 'slave_ip']
        for param in required_params:
            if not hasattr(get, param):
                return public.returnMsg(False, "缺少参数！ {}".format(param))

        node_id=get.node_id
        node_data = public.M("node").where("id = ?", (node_id,)).find()
        if not node_data:
            return public.returnMsg(False, "未找到节点信息")

        if get.master_ip == get.slave_ip:
            return public.returnMsg(False, "主库和从库不能是同一个IP!")

        public.set_module_logs("nodes_mysql_slave_9", "add_slave_server")
        if not os.path.exists("/www/server/panel/config/mysql_slave_info"):
            public.ExecShell("mkdir -p /www/server/panel/config/mysql_slave_info")

        panel_addr = node_data.get("address")
        panel_key = node_data.get("api_key") or node_data.get("app_key")

        
        ip_validation_result = self.validate_ip_network_type(get.master_ip, get.slave_ip)
        if not ip_validation_result.get("status"):
            return public.returnMsg(False, ip_validation_result.get("msg"))
        
        check_slave_result = self.slave_manager.check_slave(
            panel_addr, panel_key, get.master_ip, get.slave_ip
        )
        if check_slave_result.get("status") is False:
            return public.returnMsg(False, check_slave_result.get("msg"))
        
        if os.path.exists("/www/server/panel/config/mysql_slave_info/log/{}.log".format(get.master_ip)):
            public.ExecShell("rm -rf /www/server/panel/config/mysql_slave_info/log/{}.log".format(get.master_ip))
        
        default_err_code="1007,1050"
        if get.err_code == "":
            err_code=default_err_code
        else:
            err_code=get.err_code + "," + default_err_code

        return self.sync_service.add_slave_server(
            panel_addr, panel_key, get.master_ip, 
            get.slave_ip, get.db_name, err_code, get.sync_type
        )

    def del_slave_server(self, get):
        """删除从库服务器"""
        if not hasattr(get, 'slave_ip'):
            return public.returnMsg(False, "缺少参数！ slave_ip")

        slave_ip = get.slave_ip
        slave_info = self.config_manager.get_slave_config(slave_ip)
        if not slave_info:
            return public.returnMsg(False, "未找到从库配置信息")

        # 停止从库同步
        self.slave_manager.exec_shell_sql(slave_ip, "stop slave;")
        self.slave_manager.exec_shell_sql(slave_ip, "RESET SLAVE ALL;")

        # 删除MySQL用户
        master_user = slave_info.get("master_user")
        if master_user:
            self.mysql_manager.drop_slave_user(master_user, slave_ip)

        # 删除配置
        self.config_manager.remove_slave_config(slave_ip)

        return public.returnMsg(True, "删除成功！")

    def set_slave_status(self, get):
        """设置从库状态"""
        required_params = ['slave_ip', 'status']
        for param in required_params:
            if not hasattr(get, param):
                return public.returnMsg(False, "缺少参数！ {}".format(param))

        return self.slave_manager.set_slave_status(get.slave_ip, get.status)

    def get_slave_info(self, get):
        """获取从库信息（面板用）"""
        if not hasattr(get, 'slave_ip'):
            return public.returnMsg(False, "缺少参数！ slave_ip")

        return self.slave_manager.get_slave_info_dict(get.slave_ip)

    # ==================== 同步相关 ====================
    def sync_slave_config(self, get):
        """手动同步从库配置"""
        if not hasattr(get, 'slave_ip'):
            return public.returnMsg(False, "缺少参数！ slave_ip")

        return self.sync_service.sync_slave_config(get.slave_ip)

    def get_sync_status(self, get):
        """获取同步状态"""
        if not hasattr(get, 'slave_ip'):
            return public.returnMsg(False, "缺少参数！ slave_ip")

        slave_ip = get.slave_ip
        info = self.config_manager.get_slave_config(slave_ip)
        if not info:
            return public.returnMsg(False, "未找到同步信息，可能未开始配置，请删除重建主从")
        
        # 添加日志信息
        log_path = self.config_manager.master_slave_log_path + "/" + slave_ip + ".log"
        if os.path.exists(log_path):
            info["data"]["logs"] = public.ReadFile(log_path)
        else:
            info["data"]["logs"] = ""
        
        result = {
            "status": True,
            "msg": "success",
            "data": info
        }
        return result
    
    def get_slave_error_info(self, get):
        slave_data=self.slave_list(None)
        error_data=[]
        for item in slave_data["data"]:
            io_status = item.get("io_status")
            sql_status = item.get("sql_status")
            
            if not io_status or not sql_status:
                error_time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time())))
                data={
                    "slave_ip": item["slave_ip"],
                    "error_time": error_time,
                    "io_status": io_status,
                    "sql_status": sql_status,
                    "error_msg": "无法获取到从库状态，请检查从库mysql是否正常运行"
                }
                error_data.append(data)
            else:
                if io_status != "Yes" or sql_status != "Yes":
                    error_msg = item.get("error_msg", {})
                    if error_msg.get("Last_IO_Error_Timestamp"):
                        error_time = error_msg["Last_IO_Error_Timestamp"]
                    elif error_msg.get("Last_SQL_Error_Timestamp"):
                        error_time = error_msg["Last_SQL_Error_Timestamp"]
                    else:
                        error_time = ""
                    data={
                        "slave_ip": item["slave_ip"],
                        "error_time": error_time,
                        "io_status": io_status,
                        "sql_status": sql_status,
                        "error_msg": error_msg
                    }
                    error_data.append(data)
        return error_data


    # ==================== 兼容性方法 ====================
    def get_old_slave_list(self, get=None):
        """获取旧版从库列表（兼容性）"""
        # 这个方法主要用于兼容旧版本，可以根据需要实现
        return False

    def info_test(self, slave_ip):
        """测试信息（兼容性）"""
        info = self.config_manager.get_slave_config(slave_ip)
        if info:
            for step in info["data"]["steps"]:
                if step["name"] == "导入数据":  
                    step["name"] = "从库数据库已创建好，等待手动将数据导入从库...."
            self.config_manager.save_slave_config(slave_ip, info)

    # ==================== 后台任务方法 ====================
    def auto_sync_data(self, slave_ip):
        """自动同步数据（后台任务调用）"""
        return self.sync_service.auto_sync_data(slave_ip)

    def manual_sync_data(self, slave_ip):
        """手动同步数据（后台任务调用）"""
        return self.sync_service.manual_sync_data(slave_ip)

    def is_private_ip(self, ip_address):
        """
        判断IP地址是否为内网IP
        :param ip_address: IP地址字符串
        :return: True表示内网IP，False表示公网IP
        """
        import ipaddress
        try:
            ip = ipaddress.ip_address(ip_address)
            # 判断是否为私有地址
            return ip.is_private or ip.is_loopback or ip.is_link_local
        except ValueError:
            # IP地址格式不正确，返回False
            return False

    def validate_ip_network_type(self, master_ip, slave_ip):
        """
        验证主从IP是否为同一网络类型（都是内网或都是公网）
        :param master_ip: 主库IP
        :param slave_ip: 从库IP
        :return: dict 包含验证结果和消息
        """
        master_is_private = self.is_private_ip(master_ip)
        slave_is_private = self.is_private_ip(slave_ip)
        
        # 如果都是内网IP或都是公网IP，则通过验证
        if master_is_private == slave_is_private:
            network_type = "内网" if master_is_private else "公网"
            return {
                "status": True,
                "msg": "IP网络类型验证通过，主从库均为{}IP".format(network_type),
                "master_type": "内网" if master_is_private else "公网",
                "slave_type": "内网" if slave_is_private else "公网"
            }
        else:
            master_type = "内网" if master_is_private else "公网"
            slave_type = "内网" if slave_is_private else "公网"
            return {
                "status": False,
                "msg": "主从库IP网络类型不匹配！主库({})为{}IP，从库({})为{}IP。请使用相同网络类型的IP地址确保可连接。".format(
                    master_ip, master_type, slave_ip, slave_type
                ),
                "master_type": master_type,
                "slave_type": slave_type
            }
    