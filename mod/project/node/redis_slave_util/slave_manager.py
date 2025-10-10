# -*- coding: utf-8 -*-
"""
Redis 从库管理器
负责从节点的连接检查、状态管理、操作控制等
"""

import json
import os
import sys
import time

if '/www/server/panel/class' not in sys.path:
    sys.path.insert(0, '/www/server/panel/class')
if '/www/server/panel' not in sys.path:
    sys.path.insert(0, '/www/server/panel')

import public
from mod.project.node.redis_slave_util.bt_api import BtApi
from .redis_manager import RedisManager
from .config_manager import ConfigManager


class SlaveManager:
    """Redis 从库管理器"""
    
    def __init__(self):
        # 不在初始化时创建 BtApi 实例，而是在需要时动态创建
        self.redis_manager = RedisManager()
        self.config_manager = ConfigManager()
    
    def _get_bt_api(self, panel_addr, panel_key):
        """获取 BtApi 实例"""
        return BtApi(panel_addr, panel_key)
    
    # ==================== 从库检查 ====================
    def check_slave(self, panel_addr, panel_key, master_ip, slave_ip):
        """检查从库连接和配置"""
        try:
            bt_api = self._get_bt_api(panel_addr, panel_key)
            
            # 检查API连接 - 使用面板信息接口
            api_result = bt_api.get_slave_panel_info()
            
            if not api_result.get("status"):
                return public.returnMsg(False, f"无法连接到从库面板: {api_result.get('msg', 'Unknown error')}")
            
            # 检查Redis版本
            version_result = bt_api.slave_execute_command("redis-cli --version")
            
            if not version_result.get("status"):
                return public.returnMsg(False, "从库Redis版本检查失败")
            
            version_output = version_result.get("msg", "")
            if "redis-cli" not in version_output:
                return public.returnMsg(False, "从库未安装Redis或版本不兼容")
            
            # 检查Redis服务状态
            status_result = bt_api.slave_execute_command("ps aux | grep redis-server | grep -v grep")
            
            if not status_result.get("status") or not status_result.get("msg"):
                return public.returnMsg(False, "从库Redis服务未运行")
            
            return public.returnMsg(True, "从库检查通过")
            
        except Exception as e:
            error_msg = "检查从库失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return public.returnMsg(False, error_msg)
    
    def check_slave_redis_status(self, slave_node_id):
        """检查从库Redis运行状态"""
        try:
            return self.redis_manager.check_redis_service(slave_node_id)
                
        except Exception as e:
            error_msg = "检查从库Redis状态失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return {"status": False, "msg": error_msg}
    
    # ==================== 从库状态管理 ====================
    def get_slave_replication_status(self, slave_node_id, password=None):
        """获取从库复制状态"""
        try:
            repl_info_result = self.redis_manager.get_replication_info(slave_node_id, password)
            if not repl_info_result.get("status"):
                return {"status": False, "msg": repl_info_result.get("msg")}
            
            repl_data = repl_info_result["data"]
            role = repl_data.get("role", "unknown")
            
            
            if role != "slave":
                return {
                    "status": False,
                    "msg": "该节点不是从库",
                    "data": {"role": role}
                }
            
            # 解析从库状态
            master_link_status = repl_data.get("master_link_status", "down")
            master_last_io_seconds_ago = repl_data.get("master_last_io_seconds_ago", -1)
            master_sync_in_progress = repl_data.get("master_sync_in_progress", 0)
            slave_repl_offset = repl_data.get("slave_repl_offset", 0)
            
            # 计算延迟
            lag = master_last_io_seconds_ago if master_last_io_seconds_ago >= 0 else None
            
            status_data = {
                "role": role,
                "master_link_status": master_link_status,
                "is_online": master_link_status == "up",
                "lag": lag,
                "sync_in_progress": master_sync_in_progress == 1,
                "repl_offset": slave_repl_offset,
                "master_host": repl_data.get("master_host", ""),
                "master_port": repl_data.get("master_port", 0),
                "last_io_seconds": master_last_io_seconds_ago
            }
            
            return {
                "status": True,
                "data": status_data
            }
            
        except Exception as e:
            error_msg = "获取从库复制状态失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return {"status": False, "msg": error_msg}
    
    def stop_slave_replication(self, slave_node_id):
        """停止从库复制"""
        try:
            # 获取复制组信息
            group_config = self.config_manager.get_group_by_slave(slave_node_id)
            if not group_config:
                return public.returnMsg(False, "未找到从库所属的复制组")
            
            password = group_config.get("redis_password")
            
            # 停止复制
            result = self.redis_manager.stop_replication(slave_node_id, password)
            if result.get("status"):
                self.config_manager.write_group_log(
                    group_config["group_id"],
                    f"从库 {slave_node_id} 复制已停止"
                )
                return public.returnMsg(True, "停止复制成功")
            else:
                return result
                
        except Exception as e:
            error_msg = "停止从库复制失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return public.returnMsg(False, error_msg)
    
    def reconnect_slave(self, group_id, slave_node_id):
        """重连从库"""
        try:
            # 获取复制组配置
            group_config = self.config_manager.get_group_config(group_id)
            if not group_config:
                return public.returnMsg(False, "未找到复制组配置")
            
            master_ip = group_config["master_ip"]
            master_port = group_config["master_port"]
            password = group_config["redis_password"]
            
            # 重新配置从库
            result = self.redis_manager.configure_slave(
                slave_node_id, master_ip, master_port, password
            )
            
            if result.get("status"):
                self.config_manager.write_group_log(
                    group_id,
                    f"从库 {slave_node_id} 重连成功"
                )
                return public.returnMsg(True, "重连成功")
            else:
                self.config_manager.write_group_log(
                    group_id,
                    f"从库 {slave_node_id} 重连失败: {result.get('msg')}",
                    "ERROR"
                )
                return result
                
        except Exception as e:
            error_msg = "重连从库失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return public.returnMsg(False, error_msg)
    
    def remove_slave(self, group_id, slave_node_id):
        """移除从库"""
        try:
            # 获取复制组配置
            group_config = self.config_manager.get_group_config(group_id)
            if not group_config:
                return public.returnMsg(False, "未找到复制组配置")
            
            password = group_config["redis_password"]
            
            # 停止从库复制
            stop_result = self.redis_manager.stop_replication(slave_node_id, password)
            if not stop_result.get("status"):
                public.WriteLog("TYPE_REDIS", f"停止从库复制失败，但继续移除: {stop_result.get('msg')}")
            
            # 从配置中移除从库
            remove_result = self.config_manager.remove_slave_from_group(group_id, slave_node_id)
            if remove_result:
                self.config_manager.write_group_log(
                    group_id,
                    f"从库 {slave_node_id} 已从复制组中移除"
                )
                return public.returnMsg(True, "移除从库成功")
            else:
                return public.returnMsg(False, "移除从库失败")
                
        except Exception as e:
            error_msg = "移除从库失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return public.returnMsg(False, error_msg)
    
    # ==================== 从库信息获取 ====================
    def get_slave_detail_info(self, slave_node_id):
        """获取从库详细信息"""
        try:
            # 获取复制组配置
            group_config = self.config_manager.get_group_by_slave(slave_node_id)
            password = group_config.get("redis_password") if group_config else None
            
            # 获取节点基础信息
            node_data = public.M("node").where("id = ?", (slave_node_id,)).find()
            if not node_data:
                return {"status": False, "msg": "未找到节点信息"}
            
            server_ip = node_data.get("server_ip", "")
            if ":" in server_ip:
                host, port = server_ip.split(":", 1)
            else:
                host = server_ip
                port = "6379"
            
            # 获取Redis基础信息
            server_info_result = self.redis_manager.get_server_info(slave_node_id, password)
            memory_info_result = self.redis_manager.get_memory_usage(slave_node_id, password)
            performance_info_result = self.redis_manager.get_performance_stats(slave_node_id, password)
            connection_info_result = self.redis_manager.get_connection_info(slave_node_id, password)
            replication_status_result = self.get_slave_replication_status(slave_node_id, password)
            
            # 构建详细信息
            detail_info = {
                "node_id": slave_node_id,
                "server_ip": f"{host}:{port}",
                "host": host,
                "port": port,
                "node_name": node_data.get("name", ""),
                "status": "online" if replication_status_result.get("status") else "offline"
            }
            
            # 添加服务器信息
            if server_info_result.get("status"):
                detail_info.update(server_info_result["data"])
            
            # 添加内存信息
            if memory_info_result.get("status"):
                detail_info["memory"] = memory_info_result["data"]
            
            # 添加性能信息
            if performance_info_result.get("status"):
                detail_info["performance"] = performance_info_result["data"]
            
            # 添加连接信息
            if connection_info_result.get("status"):
                detail_info["connections"] = connection_info_result["data"]
            
            # 添加复制状态
            if replication_status_result.get("status"):
                detail_info["replication"] = replication_status_result["data"]
                
                # 计算健康度评分
                health_score = self.calculate_slave_health_score(replication_status_result["data"])
                detail_info["health_score"] = health_score
            else:
                detail_info["replication"] = {"error": replication_status_result.get("msg")}
                detail_info["health_score"] = 0
            
            return {
                "status": True,
                "data": detail_info
            }
            
        except Exception as e:
            error_msg = "获取从库详细信息失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return {"status": False, "msg": error_msg}
    
    def calculate_slave_health_score(self, replication_data):
        """计算从库健康度评分（0-100）"""
        try:
            score = 0
            
            # 1. 连接状态 (40分)
            if replication_data.get("is_online", False):
                score += 40
            
            # 2. 延迟情况 (30分)
            lag = replication_data.get("lag")
            if lag is not None:
                if lag <= 1:
                    score += 30
                elif lag <= 5:
                    score += 20
                elif lag <= 10:
                    score += 10
                # 延迟超过10秒不加分
            
            # 3. 同步状态 (20分)
            if not replication_data.get("sync_in_progress", False):
                score += 20
            
            # 4. 复制偏移量 (10分)
            repl_offset = replication_data.get("repl_offset", 0)
            if repl_offset > 0:
                score += 10
            
            return min(score, 100)
            
        except Exception:
            return 0
    
    # ==================== 批量操作 ====================
    def batch_check_slaves(self, slave_node_ids, password=None):
        """批量检查从库状态"""
        try:
            results = {}
            
            for slave_node_id in slave_node_ids:
                try:
                    # 检查Redis服务状态
                    redis_status = self.check_slave_redis_status(slave_node_id)
                    
                    # 获取复制状态
                    repl_status = self.get_slave_replication_status(slave_node_id, password)
                    
                    results[slave_node_id] = {
                        "redis_status": redis_status,
                        "replication_status": repl_status,
                        "last_check_time": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                except Exception as e:
                    results[slave_node_id] = {
                        "redis_status": {"status": False, "msg": str(e)},
                        "replication_status": {"status": False, "msg": str(e)},
                        "last_check_time": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
            
            return {
                "status": True,
                "data": results
            }
            
        except Exception as e:
            error_msg = "批量检查从库失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return {"status": False, "msg": error_msg}
    
    def batch_reconnect_slaves(self, group_id, slave_node_ids):
        """批量重连从库"""
        try:
            results = {}
            
            for slave_node_id in slave_node_ids:
                try:
                    result = self.reconnect_slave(group_id, slave_node_id)
                    results[slave_node_id] = result
                except Exception as e:
                    results[slave_node_id] = public.returnMsg(False, str(e))
            
            return {
                "status": True,
                "data": results
            }
            
        except Exception as e:
            error_msg = "批量重连从库失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return {"status": False, "msg": error_msg}
    
    # ==================== 从库操作记录 ====================
    def log_slave_operation(self, group_id, slave_node_id, operation, result, details=None):
        """记录从库操作日志"""
        try:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            status = "成功" if result.get("status") else "失败"
            message = f"[{timestamp}] 从库 {slave_node_id} {operation} {status}"
            
            if not result.get("status"):
                message += f": {result.get('msg', '')}"
            
            if details:
                message += f" - {details}"
            
            self.config_manager.write_group_log(group_id, message)
            return True
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", f"记录从库操作日志失败: {str(e)}")
            return False 