# -*- coding: utf-8 -*-
"""
Redis 监控服务
负责获取监控数据、状态跟踪、告警检测等
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
from .config_manager import ConfigManager
from .redis_manager import RedisManager
from .slave_manager import SlaveManager


class MonitorService:
    """Redis 监控服务"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.redis_manager = RedisManager()
        self.slave_manager = SlaveManager()
        
        # 告警阈值配置
        self.alert_thresholds = {
            "memory_usage_critical": 80,  # 内存使用率临界值
            "memory_usage_warning": 70,   # 内存使用率警告值
            "lag_critical": 10,           # 延迟临界值（秒）
            "lag_warning": 5,             # 延迟警告值（秒）
            "connection_ratio_warning": 80, # 连接数比例警告值
            "hit_rate_warning": 80        # 命中率警告值
        }
    
    # ==================== 主节点监控 ====================
    def get_master_status(self, master_node_id):
        """获取主节点状态"""
        try:
            # 获取复制组配置
            group_config = None
            all_groups = self.config_manager.get_all_replication_groups()
            for group in all_groups:
                if group.get("master_node_id") == master_node_id:
                    group_config = group
                    break
            
            if not group_config:
                return {"status": "error", "msg": "未找到相关复制组"}
            
            password = group_config.get("redis_password")
            
            # 获取节点基础信息
            node_data = public.M("node").where("id = ?", (master_node_id,)).find()
            if not node_data:
                return {"status": "error", "msg": "未找到节点信息"}
            
            server_ip = node_data.get("server_ip", "")
            
            # 获取各项监控数据
            memory_result = self.redis_manager.get_memory_usage(master_node_id, password)
            performance_result = self.redis_manager.get_performance_stats(master_node_id, password)
            connection_result = self.redis_manager.get_connection_info(master_node_id, password)
            
            status_data = {
                "node_id": master_node_id,
                "server_ip": server_ip,
                "memory_usage_percent": 0,
                "qps": 0,
                "connections": 0,
                "status": "offline"
            }
            
            # 内存信息
            if memory_result.get("status"):
                memory_data = memory_result["data"]
                status_data["memory_usage_percent"] = memory_data.get("usage_percent", 0)
                status_data["memory_used"] = memory_data.get("used_memory_human", "0B")
                status_data["status"] = "online"
            
            # 性能信息
            if performance_result.get("status"):
                perf_data = performance_result["data"]
                status_data["qps"] = perf_data.get("qps", 0)
                status_data["hit_rate"] = perf_data.get("hit_rate", 0)
            
            # 连接信息
            if connection_result.get("status"):
                conn_data = connection_result["data"]
                status_data["connections"] = conn_data.get("connected_clients", 0)
                status_data["max_connections"] = conn_data.get("max_clients", 0)
            
            return status_data
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", f"获取主节点状态失败: {str(e)}")
            return {"status": "error", "msg": str(e)}
    
    def get_master_detail_info(self, master_node_id):
        """获取主节点详细信息"""
        try:
            # 获取复制组配置
            group_config = None
            all_groups = self.config_manager.get_all_replication_groups()
            for group in all_groups:
                if group.get("master_node_id") == master_node_id:
                    group_config = group
                    break
            
            if not group_config:
                return {"status": False, "msg": "未找到相关复制组"}
            
            password = group_config.get("redis_password")
            
            # 获取节点基础信息
            node_data = public.M("node").where("id = ?", (master_node_id,)).find()
            if not node_data:
                return {"status": False, "msg": "未找到节点信息"}
            
            server_ip = node_data.get("server_ip", "")
            if ":" in server_ip:
                host, port = server_ip.split(":", 1)
            else:
                host = server_ip
                port = "6379"
            
            # 获取详细监控数据
            server_info_result = self.redis_manager.get_server_info(master_node_id, password)
            memory_info_result = self.redis_manager.get_memory_usage(master_node_id, password)
            performance_info_result = self.redis_manager.get_performance_stats(master_node_id, password)
            connection_info_result = self.redis_manager.get_connection_info(master_node_id, password)
            replication_info_result = self.redis_manager.get_replication_info(master_node_id, password)
            
            # 构建详细信息
            detail_info = {
                "node_id": master_node_id,
                "server_ip": server_ip,
                "address": f"{host}:{port}",
                "host": host,
                "port": port,
                "node_name": node_data.get("name", ""),
                "role": "master",
                "status": "online" if server_info_result.get("status") else "offline"
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
            
            # 添加复制信息
            if replication_info_result.get("status"):
                detail_info["replication"] = replication_info_result["data"]
                
                # 计算从节点连接数
                repl_data = replication_info_result["data"]
                connected_slaves = repl_data.get("connected_slaves", 0)
                detail_info["connected_slaves"] = connected_slaves
            
            return {
                "status": True,
                "data": detail_info
            }
            
        except Exception as e:
            error_msg = "获取主节点详细信息失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return {"status": False, "msg": error_msg}
    
    # ==================== 从节点监控 ====================
    def get_slave_status(self, slave_node_id):
        """获取从节点状态"""
        try:
            # 获取复制组配置
            group_config = self.config_manager.get_group_by_slave(slave_node_id)
            if not group_config:
                return {"status": "error", "msg": "未找到相关复制组"}
            
            password = group_config.get("redis_password")
            
            # 获取节点基础信息
            node_data = public.M("node").where("id = ?", (slave_node_id,)).find()
            if not node_data:
                return {"status": "error", "msg": "未找到节点信息"}
            
            server_ip = node_data.get("server_ip", "")
            
            # 获取从节点复制状态
            repl_status_result = self.slave_manager.get_slave_replication_status(slave_node_id, password)
            
            status_data = {
                "node_id": slave_node_id,
                "server_ip": server_ip,
                "is_online": False,
                "lag": None,
                "memory_usage_percent": 0,
                "qps": 0,
                "connections": 0,
                "health_score": 0
            }
            
            if repl_status_result.get("status"):
                repl_data = repl_status_result["data"]
                status_data["is_online"] = repl_data.get("is_online", False)
                status_data["lag"] = repl_data.get("lag")
                status_data["repl_offset"] = repl_data.get("repl_offset", 0)
                
                # 计算健康度评分
                status_data["health_score"] = self.slave_manager.calculate_slave_health_score(repl_data)
            
            # 获取其他监控数据
            memory_result = self.redis_manager.get_memory_usage(slave_node_id, password)
            if memory_result.get("status"):
                status_data["memory_usage_percent"] = memory_result["data"].get("usage_percent", 0)
            
            performance_result = self.redis_manager.get_performance_stats(slave_node_id, password)
            if performance_result.get("status"):
                status_data["qps"] = performance_result["data"].get("qps", 0)
            
            connection_result = self.redis_manager.get_connection_info(slave_node_id, password)
            if connection_result.get("status"):
                status_data["connections"] = connection_result["data"].get("connected_clients", 0)
            
            return status_data
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", f"获取从节点状态失败: {str(e)}")
            return {"status": "error", "msg": str(e)}
    
    def get_slave_detail_info(self, slave_node_id):
        """获取从节点详细信息"""
        return self.slave_manager.get_slave_detail_info(slave_node_id)
    
    # ==================== 监控数据聚合 ====================
    def get_all_monitor_data(self):
        """获取所有监控数据"""
        try:
            monitor_data = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "groups": []
            }
            
            # 获取所有复制组
            all_groups = self.config_manager.get_all_replication_groups()
            
            for group in all_groups:
                group_data = {
                    "group_id": group["group_id"],
                    "group_name": group["group_name"],
                    "master": {},
                    "slaves": []
                }
                
                # 获取主节点监控数据
                master_status = self.get_master_status(group["master_node_id"])
                group_data["master"] = master_status
                
                # 获取从节点监控数据
                for slave_node_id in group.get("slave_nodes", []):
                    slave_status = self.get_slave_status(slave_node_id)
                    group_data["slaves"].append(slave_status)
                
                monitor_data["groups"].append(group_data)
            
            return {
                "status": True,
                "data": monitor_data
            }
            
        except Exception as e:
            error_msg = "获取监控数据失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return {"status": False, "msg": error_msg}
    
    # ==================== 告警检测 ====================
    def check_master_alerts(self, master_node_id):
        """检查主节点告警"""
        try:
            alerts = []
            master_status = self.get_master_status(master_node_id)
            
            # 获取节点基础信息
            node_data = public.M("node").where("id = ?", (master_node_id,)).find()
            server_ip = node_data.get("server_ip", "") if node_data else ""
            
            if master_status.get("status") == "offline":
                alerts.append({
                    "level": "critical",
                    "type": "master_offline",
                    "node_id": master_node_id,
                    "server_ip": server_ip,
                    "message": "主节点离线",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                })
                return alerts
            
            # 内存使用率告警
            memory_usage = master_status.get("memory_usage_percent", 0)
            if memory_usage >= self.alert_thresholds["memory_usage_critical"]:
                alerts.append({
                    "level": "critical",
                    "type": "memory_usage",
                    "node_id": master_node_id,
                    "server_ip": server_ip,
                    "message": f"主节点内存使用率过高: {memory_usage}%",
                    "value": memory_usage,
                    "threshold": self.alert_thresholds["memory_usage_critical"],
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                })
            elif memory_usage >= self.alert_thresholds["memory_usage_warning"]:
                alerts.append({
                    "level": "warning",
                    "type": "memory_usage",
                    "node_id": master_node_id,
                    "server_ip": server_ip,
                    "message": f"主节点内存使用率较高: {memory_usage}%",
                    "value": memory_usage,
                    "threshold": self.alert_thresholds["memory_usage_warning"],
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                })
            
            # 连接数告警
            connections = master_status.get("connections", 0)
            max_connections = master_status.get("max_connections", 0)
            if max_connections > 0:
                connection_ratio = (connections / max_connections) * 100
                if connection_ratio >= self.alert_thresholds["connection_ratio_warning"]:
                    alerts.append({
                        "level": "warning",
                        "type": "connection_usage",
                        "node_id": master_node_id,
                        "server_ip": server_ip,
                        "message": f"主节点连接数过高: {connections}/{max_connections} ({connection_ratio:.1f}%)",
                        "value": connection_ratio,
                        "threshold": self.alert_thresholds["connection_ratio_warning"],
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
            
            # 命中率告警
            hit_rate = master_status.get("hit_rate", 100)
            if hit_rate < self.alert_thresholds["hit_rate_warning"]:
                alerts.append({
                    "level": "warning",
                    "type": "hit_rate",
                    "node_id": master_node_id,
                    "server_ip": server_ip,
                    "message": f"主节点缓存命中率过低: {hit_rate}%",
                    "value": hit_rate,
                    "threshold": self.alert_thresholds["hit_rate_warning"],
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                })
            
            return alerts
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", f"检查主节点告警失败: {str(e)}")
            return []
    
    def check_slave_alerts(self, slave_node_id):
        """检查从节点告警"""
        try:
            alerts = []
            slave_status = self.get_slave_status(slave_node_id)
            
            # 获取节点基础信息
            node_data = public.M("node").where("id = ?", (slave_node_id,)).find()
            server_ip = node_data.get("server_ip", "") if node_data else ""
            
            # 从节点离线告警
            if not slave_status.get("is_online", False):
                alerts.append({
                    "level": "critical",
                    "type": "slave_offline",
                    "node_id": slave_node_id,
                    "server_ip": server_ip,
                    "message": "从节点离线或复制中断",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                })
                return alerts
            
            # 延迟告警
            lag = slave_status.get("lag")
            if lag is not None:
                if lag >= self.alert_thresholds["lag_critical"]:
                    alerts.append({
                        "level": "critical",
                        "type": "replication_lag",
                        "node_id": slave_node_id,
                        "server_ip": server_ip,
                        "message": f"从节点复制延迟过高: {lag}秒",
                        "value": lag,
                        "threshold": self.alert_thresholds["lag_critical"],
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                elif lag >= self.alert_thresholds["lag_warning"]:
                    alerts.append({
                        "level": "warning",
                        "type": "replication_lag",
                        "node_id": slave_node_id,
                        "server_ip": server_ip,
                        "message": f"从节点复制延迟较高: {lag}秒",
                        "value": lag,
                        "threshold": self.alert_thresholds["lag_warning"],
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
            
            # 健康度告警
            health_score = slave_status.get("health_score", 0)
            if health_score < 60:
                alerts.append({
                    "level": "warning",
                    "type": "health_score",
                    "node_id": slave_node_id,
                    "server_ip": server_ip,
                    "message": f"从节点健康度较低: {health_score}分",
                    "value": health_score,
                    "threshold": 60,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                })
            
            return alerts
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", f"检查从节点告警失败: {str(e)}")
            return []
    
    # ==================== 后台监控任务 ====================
    def auto_monitor_task(self):
        """自动监控任务"""
        try:
            # 获取所有复制组
            all_groups = self.config_manager.get_all_replication_groups()
            
            for group in all_groups:
                group_id = group["group_id"]
                
                try:
                    # 检查主节点
                    master_alerts = self.check_master_alerts(group["master_node_id"])
                    for alert in master_alerts:
                        self.config_manager.write_group_log(
                            group_id,
                            f"[{alert['level'].upper()}] {alert['message']}",
                            "WARNING" if alert['level'] == "warning" else "ERROR"
                        )
                    
                    # 检查从节点
                    for slave_node_id in group.get("slave_nodes", []):
                        slave_alerts = self.check_slave_alerts(slave_node_id)
                        for alert in slave_alerts:
                            self.config_manager.write_group_log(
                                group_id,
                                f"[{alert['level'].upper()}] {alert['message']}",
                                "WARNING" if alert['level'] == "warning" else "ERROR"
                            )
                
                except Exception as e:
                    self.config_manager.write_group_log(
                        group_id,
                        f"监控检查异常: {str(e)}",
                        "ERROR"
                    )
            
            return True
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", f"自动监控任务失败: {str(e)}")
            return False
    
    def health_check_task(self):
        """健康检查任务"""
        try:
            # 获取所有复制组
            all_groups = self.config_manager.get_all_replication_groups()
            
            for group in all_groups:
                group_id = group["group_id"]
                password = group.get("redis_password")
                
                try:
                    # 检查主节点服务状态
                    master_node_id = group["master_node_id"]
                    master_service_check = self.redis_manager.check_redis_service(master_node_id)
                    if not master_service_check.get("status"):
                        self.config_manager.write_group_log(
                            group_id,
                            f"主节点Redis服务检查异常: {master_service_check.get('msg')}",
                            "ERROR"
                        )
                    
                    # 检查从节点服务状态和复制状态
                    for slave_node_id in group.get("slave_nodes", []):
                        try:
                            # 检查Redis服务状态
                            slave_service_check = self.redis_manager.check_redis_service(slave_node_id)
                            if not slave_service_check.get("status"):
                                self.config_manager.write_group_log(
                                    group_id,
                                    f"从节点 {slave_node_id} Redis服务异常: {slave_service_check.get('msg')}",
                                    "ERROR"
                                )
                                continue
                            
                            # 检查复制状态
                            repl_status = self.slave_manager.get_slave_replication_status(slave_node_id, password)
                            if repl_status.get("status"):
                                repl_data = repl_status["data"]
                                if not repl_data.get("is_online", False):
                                    self.config_manager.write_group_log(
                                        group_id,
                                        f"从节点 {slave_node_id} 复制状态异常",
                                        "WARNING"
                                    )
                            else:
                                self.config_manager.write_group_log(
                                    group_id,
                                    f"从节点 {slave_node_id} 复制状态检查失败: {repl_status.get('msg')}",
                                    "ERROR"
                                )
                        except Exception as e:
                            self.config_manager.write_group_log(
                                group_id,
                                f"从节点 {slave_node_id} 健康检查异常: {str(e)}",
                                "ERROR"
                            )
                
                except Exception as e:
                    self.config_manager.write_group_log(
                        group_id,
                        f"健康检查异常: {str(e)}",
                        "ERROR"
                    )
            
            return True
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", f"健康检查任务失败: {str(e)}")
            return False
    
    # ==================== 工具方法 ====================
    def update_alert_thresholds(self, thresholds):
        """更新告警阈值"""
        try:
            self.alert_thresholds.update(thresholds)
            return True
        except Exception as e:
            public.WriteLog("TYPE_REDIS", f"更新告警阈值失败: {str(e)}")
            return False
    
    def get_alert_thresholds(self):
        """获取告警阈值配置"""
        return self.alert_thresholds.copy()
    
    def calculate_group_health_score(self, group_id):
        """计算复制组整体健康度"""
        try:
            group_config = self.config_manager.get_group_config(group_id)
            if not group_config:
                return 0
            
            total_score = 0
            node_count = 0
            
            # 主节点健康度 (权重 40%)
            master_status = self.get_master_status(group_config["master_node_id"])
            if master_status.get("status") == "online":
                master_score = 100
                # 根据内存使用率调整分数
                memory_usage = master_status.get("memory_usage_percent", 0)
                if memory_usage > 80:
                    master_score -= 30
                elif memory_usage > 70:
                    master_score -= 15
                
                total_score += master_score * 0.4
            
            # 从节点健康度 (权重 60%)
            slave_nodes = group_config.get("slave_nodes", [])
            if slave_nodes:
                slave_total_score = 0
                for slave_node_id in slave_nodes:
                    slave_status = self.get_slave_status(slave_node_id)
                    slave_score = slave_status.get("health_score", 0)
                    slave_total_score += slave_score
                    node_count += 1
                
                if node_count > 0:
                    avg_slave_score = slave_total_score / node_count
                    total_score += avg_slave_score * 0.6
            else:
                # 没有从节点时，主节点健康度占100%
                total_score = total_score / 0.4 if total_score > 0 else 0
            
            return min(round(total_score), 100)
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", f"计算复制组健康度失败: {str(e)}")
            return 0 