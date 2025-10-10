# -*- coding: utf-8 -*-
"""
Redis 主从复制模块 - 前端接口层
负责处理前端请求，调用具体的业务逻辑实现
"""

import json
import os
import sys
import time
import socket
# 添加路径
if '/www/server/panel/class' not in sys.path:
    sys.path.insert(0, '/www/server/panel/class')
if '/www/server/panel' not in sys.path:
    sys.path.insert(0, '/www/server/panel')

import public
from mod.project.node.redis_slave_util.config_manager import ConfigManager
from mod.project.node.redis_slave_util.redis_manager import RedisManager
from mod.project.node.redis_slave_util.slave_manager import SlaveManager
from mod.project.node.redis_slave_util.sync_service import SyncService
from mod.project.node.redis_slave_util.monitor_service import MonitorService



class main:
    """Redis 主从复制主模块"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.redis_manager = RedisManager()
        self.slave_manager = SlaveManager()
        self.sync_service = SyncService()
        self.monitor_service = MonitorService()

    # ==================== 版本和检查相关 ====================
    def get_redis_version(self, get=None):
        """获取Redis版本"""
        version = self.redis_manager.get_redis_version()
        if not version:
            return public.returnMsg(False, "此功能仅支持Redis-3.2以上版本使用！")
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

    def check_redis_port(self, server_ip=None, port=6379):
        """检查Redis端口是否开放"""
        try:
            # 将端口转换为整数
            if isinstance(port, str):
                port = int(port)
            
            # 创建socket连接
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)  # 设置3秒超时
            
            # 尝试连接
            result = sock.connect_ex((server_ip, port))
            sock.close()
            
            # connect_ex返回0表示连接成功
            if result == 0:
                return True
            else:
                return False
                
        except Exception as e:
            return False

    # ==================== 主从复制组管理 ====================
    def replication_group_list(self, get=None):
        """获取主从复制组列表（带分页和搜索功能）"""
        try:
            # 1. 检查Redis版本
            version_check = self.redis_manager.get_redis_version()
            if not version_check:
                return public.returnMsg(False, "此功能仅支持Redis-3.2以上版本使用！")
            
            # 2. 获取并验证分页参数
            search = getattr(get, 'search', '').strip() if get else ''
            p = int(getattr(get, 'p', 1)) if get and hasattr(get, 'p') else 1
            limit = int(getattr(get, 'limit', 20)) if get and hasattr(get, 'limit') else 20
            
            # 参数验证
            if p < 1:
                p = 1
            if limit < 1 or limit > 100:
                limit = 20
            
            # 3. 获取所有复制组列表
            all_data = self.config_manager.get_all_replication_groups()
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
            
            # 4. 丰富数据 - 添加监控信息
            enriched_data = []
            for group in all_data:
                group_info = self.enrich_group_data(group)
                enriched_data.append(group_info)
            
            # 5. 搜索过滤
            filtered_data = enriched_data
            if search:
                filtered_data = []
                for item in enriched_data:
                    # 支持按复制组名称、主库地址搜索
                    if (search.lower() in item.get('group_name', '').lower() or 
                        search.lower() in item.get('master_server_ip', '').lower()):
                        filtered_data.append(item)
            
            # 6. 计算分页参数
            total_count = len(filtered_data)
            total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0
            offset = (p - 1) * limit
            
            # 7. 获取当前页数据
            current_page_data = filtered_data[offset:offset + limit]
            
            # 8. 构建分页信息
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
            
            # 9. 返回结果
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
            error_msg = "获取主从复制组列表失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return {
                "status": False,
                "msg": error_msg,
                "data": [],
                "page": {},
                "search": "",
                "total": 0
            }

    def enrich_group_data(self, group):
        """丰富复制组数据，添加监控信息"""
        try:
            # 获取主节点监控数据
            master_info = self.monitor_service.get_master_status(group['master_node_id'])
            
            # 获取从节点状态
            slave_count = len(group.get('slave_nodes', []))
            normal_slaves = 0
            total_lag = 0
            lag_count = 0
            
            for slave_node_id in group.get('slave_nodes', []):
                slave_status = self.monitor_service.get_slave_status(slave_node_id)
                if slave_status.get('is_online', False):
                    normal_slaves += 1
                    if slave_status.get('lag') is not None:
                        total_lag += slave_status['lag']
                        lag_count += 1
            
            # 计算平均延迟
            avg_lag = round(total_lag / lag_count, 2) if lag_count > 0 else 0
            
            return {
                'group_id': group['group_id'],
                'group_name': group['group_name'],
                'master_server_ip': "{}:{}".format(group['master_ip'], group['master_port']),
                'memory_usage': master_info.get('memory_usage_percent', 0),
                'qps': master_info.get('qps', 0),
                'connections': master_info.get('connections', 0),
                'slave_count': slave_count,
                'normal_slaves': normal_slaves,
                'avg_lag': avg_lag,
                'created_time': group.get('created_time', ''),
                'status': 'normal' if normal_slaves == slave_count else 'warning',
                'task_id': group.get('task_id', '')
            }
        except Exception as e:
            public.WriteLog("TYPE_REDIS", "丰富复制组数据失败: {}".format(str(e)))
            return group

    # ==================== 创建主从复制组 ====================
    def create_replication_group(self, get):
        """创建主从复制组"""
        required_params = ['group_name', 'master_node_id', 'slave_node_ids','master_ip','redis_password']
        for param in required_params:
            if not hasattr(get, param):
                return public.returnMsg(False, "缺少参数！ {}".format(param))

        # 验证参数
        group_name = get.group_name.strip()
        if not group_name:
            return public.returnMsg(False, "主从名称不能为空！")
        
        # 检查名称是否已存在
        if self.config_manager.group_name_exists(group_name):
            return public.returnMsg(False, "主从复制组名称已存在！")
        
        # 获取节点信息
        master_node = public.M("node").where("id = ?", (get.master_node_id,)).find()
        if not master_node:
            return public.returnMsg(False, "未找到主节点信息")
        
        
        slave_node_ids = json.loads(get.slave_node_ids) if isinstance(get.slave_node_ids, str) else get.slave_node_ids
        slave_nodes = []
        for slave_id in slave_node_ids:
            slave_node = public.M("node").where("id = ?", (slave_id,)).find()
            if not slave_node:
                return public.returnMsg(False, "未找到从节点信息: {}".format(slave_id))
            slave_nodes.append(slave_node)

        # 验证主从IP不能相同
        #master_ip = master_node.get("server_ip")
        master_ip = get.master_ip
        for slave_node in slave_nodes:
            slave_ip = slave_node.get("server_ip")
            if master_ip == slave_ip:
                return public.returnMsg(False, "主库和从库不能是同一个IP!")
            # if slave_ip == "127.0.0.1":
            #     return public.returnMsg(False, "从库不能是127.0.0.1!")
            
        if master_ip == "127.0.0.1":
            return public.returnMsg(False, "主库不能是127.0.0.1!")
        
        
        # 检查密码强度
        if len(get.redis_password) < 8:
            return public.returnMsg(False, "Redis密码长度不能少于8位!")
        
        ip_list = [master_ip]
        for slave_node in slave_nodes:
            ip_list.append(slave_node.get("server_ip"))
        for ip in ip_list:
            if not self.check_redis_port(ip):
                return public.returnMsg(False, "连接{} redis失败，请指定ip放行6379端口，并设置redis外网访问权限(注意设置密码)".format(ip))


        # 创建配置目录
        if not os.path.exists("/www/server/panel/config/redis_slave_info"):
            public.ExecShell("mkdir -p /www/server/panel/config/redis_slave_info")
        # 启动创建工作流
        return self.sync_service.create_replication_group(
            group_name, master_node, slave_nodes, get.redis_password,master_ip
        )

    def get_creation_status(self, get):
        """获取创建状态"""
        if not hasattr(get, 'task_id'):
            return public.returnMsg(False, "缺少参数！ task_id")
        

        return self.sync_service.get_creation_status(get.task_id)

    def get_group_creation_status(self, get):
        """通过复制组ID获取创建状态"""
        if not hasattr(get, 'group_id'):
            return public.returnMsg(False, "缺少参数！ group_id")
        
        try:
            # 通过group_id获取task_id
            task_id = self.config_manager.get_group_task_id(get.group_id)
            if not task_id:
                return public.returnMsg(False, "未找到该复制组的创建任务ID")
            
            # 获取任务状态
            return self.sync_service.get_creation_status(task_id)
            
        except Exception as e:
            error_msg = "获取复制组创建状态失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return public.returnMsg(False, error_msg)

    # ==================== 复制组详细管理 ====================
    def get_group_detail(self, get):
        """获取复制组详细信息"""
        if not hasattr(get, 'group_id'):
            return public.returnMsg(False, "缺少参数！ group_id")
        
        try:
            group_config = self.config_manager.get_group_config(get.group_id)
            if not group_config:
                return public.returnMsg(False, "未找到复制组配置")
            
            # 获取主节点详细信息
            master_detail = self.monitor_service.get_master_detail_info(group_config['master_node_id'])
            
            # 获取从节点详细信息列表
            slave_details = []
            for slave_node_id in group_config.get('slave_nodes', []):
                slave_detail = self.monitor_service.get_slave_detail_info(slave_node_id)
                slave_details.append(slave_detail)
            
            result = {
                "status": True,
                "msg": "success",
                "data": {
                    "group_info": group_config,
                    "master_detail": master_detail,
                    "slave_details": slave_details
                }
            }
            return result
            
        except Exception as e:
            error_msg = "获取复制组详细信息失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return public.returnMsg(False, error_msg)

    # ==================== 从库管理 ====================
    def get_slave_status(self, get):
        """获取从库状态"""
        if not hasattr(get, 'slave_node_id'):
            return public.returnMsg(False, "缺少参数！ slave_node_id")
        
        return self.monitor_service.get_slave_status(get.slave_node_id)

    def reconnect_slave(self, get):
        """重连从库"""
        required_params = ['group_id', 'slave_node_id']
        for param in required_params:
            if not hasattr(get, param):
                return public.returnMsg(False, "缺少参数！ {}".format(param))
        
        return self.slave_manager.reconnect_slave(get.group_id, get.slave_node_id)

    def remove_slave(self, get):
        """移除从库"""
        required_params = ['group_id', 'slave_node_id']
        for param in required_params:
            if not hasattr(get, param):
                return public.returnMsg(False, "缺少参数！ {}".format(param))
        
        return self.slave_manager.remove_slave(get.group_id, get.slave_node_id)

    def add_slave_to_group(self, get):
        """向复制组添加新的从节点"""
        required_params = ['group_id', 'new_slave_node_id']
        for param in required_params:
            if not hasattr(get, param):
                return public.returnMsg(False, "缺少参数！ {}".format(param))
        
        return self.sync_service.add_slave_to_existing_group(get.group_id, get.new_slave_node_id)

    # ==================== 复制组操作 ====================
    def delete_replication_group(self, get):
        """删除主从复制组"""
        if not hasattr(get, 'group_id'):
            return public.returnMsg(False, "缺少参数！ group_id")

        group_id = get.group_id
        group_config = self.config_manager.get_group_config(group_id)
        if not group_config:
            return public.returnMsg(False, "未找到复制组配置信息")

        try:
            cleanup_errors = []
            
            # 记录开始删除
            self.config_manager.write_group_log(group_id, "开始删除主从复制组", "INFO")
            
            # 1. 停止所有从库复制并清理配置
            slave_nodes = group_config.get('slave_nodes', [])
            for slave_node_id in slave_nodes:
                try:
                    # 停止从库复制
                    stop_result = self.slave_manager.stop_slave_replication(slave_node_id)
                    if not stop_result.get("status"):
                        cleanup_errors.append(f"停止从库 {slave_node_id} 复制失败: {stop_result.get('msg')}")
                    
                    # 清理从节点Redis配置（移除replicaof等配置）
                    clean_result = self.redis_manager.stop_replication(slave_node_id)
                    if not clean_result.get("status"):
                        cleanup_errors.append(f"清理从库 {slave_node_id} 配置失败: {clean_result.get('msg')}")
                    else:
                        self.config_manager.write_group_log(group_id, f"从库 {slave_node_id} 配置已清理", "INFO")
                        
                except Exception as e:
                    cleanup_errors.append(f"处理从库 {slave_node_id} 异常: {str(e)}")
            
            # 2. 清理主库复制相关配置
            master_node_id = group_config.get('master_node_id')
            if master_node_id:
                try:
                    # 清理主库复制用户和配置
                    master_cleanup = self.redis_manager.cleanup_replication_users(master_node_id)
                    if not master_cleanup:
                        cleanup_errors.append(f"清理主库 {master_node_id} 配置失败")
                    else:
                        self.config_manager.write_group_log(group_id, f"主库 {master_node_id} 配置已清理", "INFO")
                except Exception as e:
                    cleanup_errors.append(f"清理主库 {master_node_id} 异常: {str(e)}")
            
            # 3. 删除配置文件和日志文件
            self.config_manager.write_group_log(group_id, "删除配置文件和日志", "INFO")
            
            # 先获取日志内容用于记录错误
            if cleanup_errors:
                for error in cleanup_errors:
                    self.config_manager.write_group_log(group_id, f"清理错误: {error}", "WARNING")
            
            # 删除配置和日志文件
            remove_result = self.config_manager.remove_group_config(group_id)
            if not remove_result:
                return public.returnMsg(False, "删除配置文件失败")
            
            # 构建返回消息
            if cleanup_errors:
                error_summary = "; ".join(cleanup_errors[:3])  # 只显示前3个错误
                if len(cleanup_errors) > 3:
                    error_summary += f" 等共{len(cleanup_errors)}个错误"
                return public.returnMsg(True, f"删除成功，但存在清理问题: {error_summary}")
            else:
                return public.returnMsg(True, "删除成功！")
            
        except Exception as e:
            error_msg = "删除复制组失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            
            # 即使出现异常也尝试删除配置文件
            try:
                self.config_manager.remove_group_config(group_id)
            except:
                pass
                
            return public.returnMsg(False, error_msg)

    # ==================== 监控相关 ====================
    def get_monitor_data(self, get=None):
        """获取监控数据"""
        try:
            return self.monitor_service.get_all_monitor_data()
        except Exception as e:
            error_msg = "获取监控数据失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return public.returnMsg(False, error_msg)

    def get_alert_info(self, get=None):
        """获取告警信息"""
        try:
            alert_data = []
            
            # 获取所有复制组
            all_groups = self.config_manager.get_all_replication_groups()
            
            for group in all_groups:
                # 检查主节点告警
                master_alerts = self.monitor_service.check_master_alerts(group['master_node_id'])
                if master_alerts:
                    for alert in master_alerts:
                        if alert.get("type") == "master_offline":
                            alert_data.append(alert)
                
                # 检查从节点告警
                for slave_node_id in group.get('slave_nodes', []):
                    slave_alerts = self.monitor_service.check_slave_alerts(slave_node_id)
                    if slave_alerts:
                        for alert in slave_alerts:
                            if alert.get("type") == "slave_offline":
                                alert_data.append(alert)

            return {
                "status": True,
                "msg": "success",
                "data": alert_data,
                "count": len(alert_data)
            }
            
        except Exception as e:
            error_msg = "获取告警信息失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return public.returnMsg(False, error_msg)

    # ==================== 工具方法 ====================
    def generate_redis_password(self, get=None):
        """生成Redis密码"""
        import random
        import string
        
        # 生成16位强密码，包含字母、数字和特殊字符
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(random.choice(chars) for _ in range(16))
        
        return public.returnMsg(True, password)

    def validate_redis_connection(self, get):
        """验证Redis连接"""
        required_params = ['node_id', 'password']
        for param in required_params:
            if not hasattr(get, param):
                return public.returnMsg(False, "缺少参数！ {}".format(param))
        
        return self.redis_manager.test_connection(get.node_id, get.password)

    def get_available_nodes(self, get=None):
        """获取可用的Redis节点列表"""
        #_REPO_DIR="/www/server/panel/data/mod_node_status_cache/"
        try:
            nodes = public.M("node").select()
            available_nodes = []
            
            # 获取所有复制组信息，用于检测节点是否已在复制组中
            all_groups = self.config_manager.get_all_replication_groups()
            
            # 构建节点到复制组的映射关系
            node_group_map = {}
            for group in all_groups:
                # 主节点
                master_id = group.get('master_node_id')
                if master_id:
                    node_group_map[master_id] = {
                        'group_id': group['group_id'],
                        'group_name': group['group_name'],
                        'role': 'master'
                    }
                
                # 从节点
                for slave_id in group.get('slave_nodes', []):
                    node_group_map[slave_id] = {
                        'group_id': group['group_id'],
                        'group_name': group['group_name'],
                        'role': 'slave'
                    }
            
            for node in nodes:
                try:
                    # if node.get("api_key") != "local":
                    #     if not os.path.exists(_REPO_DIR+"server_{}.json".format(node.get("id"))):
                    #         continue
                    # if not self.bt_api_client_test(node.get("id")):
                    #     continue

                    # 检查节点是否安装了Redis并获取版本信息
                    redis_version = self.redis_manager.get_redis_version_by_node(node['id'])
                    
                    if redis_version:  # 只有检测到Redis版本的节点才添加到列表
                        # 检查Redis服务状态
                        service_status = self.redis_manager.check_redis_service(node['id'])
                        node_status = 'online' if service_status.get('status', False) else 'offline'
                        
                        # 检查节点是否在复制组中
                        is_in_replication_group = node['id'] in node_group_map
                        group_info = node_group_map.get(node['id'], None)
                        

                        server_ip = node.get('server_ip', '')
                        if server_ip == "127.0.0.1":
                            server_ip = public.GetLocalIp()
                            
                        node_info = {
                            'id': node['id'],
                            'name': node.get('remarks', ''),
                            'server_ip': server_ip,
                            'status': node_status,
                            'redis_version': redis_version,
                            'type': 'standalone',  # Redis类型，默认为单机
                            'is_in_replication_group': is_in_replication_group,
                            'group_info': group_info  # 如果在复制组中，包含复制组信息；否则为None
                        }
                        available_nodes.append(node_info)
                        
                except Exception as e:
                    # 如果检测某个节点失败，记录日志但继续处理其他节点
                    public.WriteLog("TYPE_REDIS", f"检测节点 {node.get('id')} Redis状态失败: {str(e)}")
                    continue
            
            return {
                "status": True,
                "msg": "success",
                "data": available_nodes
            }
            
        except Exception as e:
            error_msg = "获取可用节点失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return public.returnMsg(False, error_msg)

    # ==================== 后台任务方法 ====================
    def auto_monitor_task(self):
        """自动监控任务（后台任务调用）"""
        return self.monitor_service.auto_monitor_task()

    def health_check_task(self):
        """健康检查任务（后台任务调用）"""
        return self.monitor_service.health_check_task() 
    
