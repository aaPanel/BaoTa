# -*- coding: utf-8 -*-
"""
Redis 主从复制配置管理器
负责管理主从复制组的配置信息
"""

import json
import os
import time
import uuid
import sys

if '/www/server/panel/class' not in sys.path:
    sys.path.insert(0, '/www/server/panel/class')
if '/www/server/panel' not in sys.path:
    sys.path.insert(0, '/www/server/panel')

import public


class ConfigManager:
    """Redis 主从复制配置管理"""
    
    def __init__(self):
        self.config_base_path = "/www/server/panel/config/redis_slave_info"
        self.groups_config_path = os.path.join(self.config_base_path, "groups")
        self.log_path = os.path.join(self.config_base_path, "log")
        self.init_directories()
    
    def init_directories(self):
        """初始化必要的目录"""
        for path in [self.config_base_path, self.groups_config_path, self.log_path]:
            if not os.path.exists(path):
                os.makedirs(path, mode=0o755)
    
    # ==================== 复制组配置管理 ====================
    def create_group_config(self, group_name, master_node, slave_nodes, password, master_ip, task_id=None):
        """创建新的复制组配置"""
        try:
            group_id = str(uuid.uuid4())
            
            # 使用传入的master_ip，如果没有则从server_ip解析
            if master_ip:
                master_ip_to_use = master_ip
                master_port = "6379"  # 默认端口
            else:
                # 解析主节点地址（兼容性处理）
                master_server_ip = master_node.get("server_ip", "")
                if ":" in master_server_ip:
                    master_ip_to_use, master_port = master_server_ip.split(":", 1)
                else:
                    master_ip_to_use = master_server_ip
                    master_port = "6379"  # 默认Redis端口
            
            # 准备从节点信息
            slave_node_ids = [node.get("id") for node in slave_nodes]
            
            config = {
                "group_id": group_id,
                "group_name": group_name,
                "master_node_id": master_node.get("id"),
                "master_ip": master_ip_to_use,
                "master_port": master_port,
                "master_address": master_node.get("server_ip", ""),  # 保留原始地址
                "slave_nodes": slave_node_ids,
                "redis_password": password,  # 注意：实际应用中应该加密存储
                "task_id": task_id,  # 添加创建任务ID
                "created_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "creating",
                "config_version": "1.0"
            }
            
            # 保存配置
            config_file = os.path.join(self.groups_config_path, "{}.json".format(group_id))
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            return group_id
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", "创建复制组配置失败: {}".format(str(e)))
            return None
    
    def get_group_config(self, group_id):
        """获取复制组配置"""
        try:
            config_file = os.path.join(self.groups_config_path, "{}.json".format(group_id))
            if not os.path.exists(config_file):
                return None
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            return config
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", "获取复制组配置失败: {}".format(str(e)))
            return None
    
    def update_group_config(self, group_id, updates):
        """更新复制组配置"""
        try:
            config = self.get_group_config(group_id)
            if not config:
                return False
            
            # 更新配置
            config.update(updates)
            config["updated_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 保存配置
            config_file = os.path.join(self.groups_config_path, "{}.json".format(group_id))
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", "更新复制组配置失败: {}".format(str(e)))
            return False
    
    def remove_group_config(self, group_id):
        """删除复制组配置"""
        try:
            # 删除复制组配置文件
            config_file = os.path.join(self.groups_config_path, "{}.json".format(group_id))
            if os.path.exists(config_file):
                os.remove(config_file)
                public.WriteLog("TYPE_REDIS", f"已删除复制组配置文件: {config_file}")
            
            # 删除相关日志文件
            log_file = os.path.join(self.log_path, "{}.log".format(group_id))
            if os.path.exists(log_file):
                os.remove(log_file)
                public.WriteLog("TYPE_REDIS", f"已删除复制组日志文件: {log_file}")
            
            # 删除相关任务文件
            tasks_dir = os.path.join(self.config_base_path, "tasks")
            if os.path.exists(tasks_dir):
                for task_file in os.listdir(tasks_dir):
                    if task_file.endswith('.json'):
                        task_path = os.path.join(tasks_dir, task_file)
                        try:
                            with open(task_path, 'r', encoding='utf-8') as f:
                                task_data = json.load(f)
                            
                            # 如果任务属于这个复制组，则删除
                            if task_data.get('group_id') == group_id:
                                os.remove(task_path)
                                public.WriteLog("TYPE_REDIS", f"已删除任务文件: {task_path}")
                        except Exception as e:
                            public.WriteLog("TYPE_REDIS", f"处理任务文件失败 {task_path}: {str(e)}")
            
            return True
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", "删除复制组配置失败: {}".format(str(e)))
            return False
    
    def get_all_replication_groups(self):
        """获取所有复制组配置"""
        try:
            groups = []
            
            if not os.path.exists(self.groups_config_path):
                return groups
            
            for filename in os.listdir(self.groups_config_path):
                if filename.endswith('.json'):
                    group_id = filename[:-5]  # 移除.json后缀
                    config = self.get_group_config(group_id)
                    if config:
                        groups.append(config)
            
            # 按创建时间倒序排列
            groups.sort(key=lambda x: x.get('created_time', ''), reverse=True)
            return groups
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", "获取所有复制组失败: {}".format(str(e)))
            return []
    
    def group_name_exists(self, group_name):
        """检查复制组名称是否已存在"""
        try:
            all_groups = self.get_all_replication_groups()
            for group in all_groups:
                if group.get('group_name') == group_name:
                    return True
            return False
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", "检查复制组名称失败: {}".format(str(e)))
            return False
    
    def get_group_task_id(self, group_id):
        """通过复制组ID获取创建任务ID"""
        try:
            config = self.get_group_config(group_id)
            if config:
                return config.get('task_id')
            return None
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", "获取复制组任务ID失败: {}".format(str(e)))
            return None
    
    def get_group_by_task_id(self, task_id):
        """通过任务ID获取复制组配置"""
        try:
            all_groups = self.get_all_replication_groups()
            for group in all_groups:
                if group.get('task_id') == task_id:
                    return group
            return None
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", "通过任务ID获取复制组失败: {}".format(str(e)))
            return None
    
    # ==================== 从节点配置管理 ====================
    def add_slave_to_group(self, group_id, slave_node_id):
        """向复制组添加从节点"""
        try:
            config = self.get_group_config(group_id)
            if not config:
                return False
            
            slave_nodes = config.get('slave_nodes', [])
            if slave_node_id not in slave_nodes:
                slave_nodes.append(slave_node_id)
                return self.update_group_config(group_id, {'slave_nodes': slave_nodes})
            
            return True
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", "添加从节点失败: {}".format(str(e)))
            return False
    
    def remove_slave_from_group(self, group_id, slave_node_id):
        """从复制组移除从节点"""
        try:
            config = self.get_group_config(group_id)
            if not config:
                return False
            
            slave_nodes = config.get('slave_nodes', [])
            if slave_node_id in slave_nodes:
                slave_nodes.remove(slave_node_id)
                return self.update_group_config(group_id, {'slave_nodes': slave_nodes})
            
            return True
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", "移除从节点失败: {}".format(str(e)))
            return False
    
    def get_group_by_slave(self, slave_node_id):
        """根据从节点ID获取所属的复制组"""
        try:
            all_groups = self.get_all_replication_groups()
            for group in all_groups:
                if slave_node_id in group.get('slave_nodes', []):
                    return group
            return None
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", "根据从节点获取复制组失败: {}".format(str(e)))
            return None
    
    # ==================== 日志管理 ====================
    def write_group_log(self, group_id, message, level="INFO"):
        """写入复制组日志"""
        try:
            log_file = os.path.join(self.log_path, "{}.log".format(group_id))
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_entry = "[{}] [{}] {}\n".format(timestamp, level, message)
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            
            return True
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", "写入复制组日志失败: {}".format(str(e)))
            return False
    
    def get_group_log(self, group_id, lines=100):
        """获取复制组日志"""
        try:
            log_file = os.path.join(self.log_path, "{}.log".format(group_id))
            if not os.path.exists(log_file):
                return ""
            
            # 读取最后N行
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
            
            if lines > 0:
                return ''.join(all_lines[-lines:])
            else:
                return ''.join(all_lines)
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", "获取复制组日志失败: {}".format(str(e)))
            return ""
    
    def clear_group_log(self, group_id):
        """清空复制组日志"""
        try:
            log_file = os.path.join(self.log_path, "{}.log".format(group_id))
            if os.path.exists(log_file):
                open(log_file, 'w').close()
            return True
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", "清空复制组日志失败: {}".format(str(e)))
            return False
    
    # ==================== 任务状态管理 ====================
    def create_task_status(self, task_id, task_type, group_id):
        """创建任务状态记录"""
        try:
            task_file = os.path.join(self.config_base_path, "tasks", "{}.json".format(task_id))
            task_dir = os.path.dirname(task_file)
            
            if not os.path.exists(task_dir):
                os.makedirs(task_dir, mode=0o755)
            
            task_status = {
                "task_id": task_id,
                "task_type": task_type,
                "group_id": group_id,
                "status": "running",
                "progress": 0,
                "message": "任务开始执行",
                "created_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "steps": []
            }
            
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(task_status, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", "创建任务状态失败: {}".format(str(e)))
            return False
    
    def update_task_status(self, task_id, updates):
        """更新任务状态"""
        try:
            task_file = os.path.join(self.config_base_path, "tasks", "{}.json".format(task_id))
            if not os.path.exists(task_file):
                return False
            
            with open(task_file, 'r', encoding='utf-8') as f:
                task_status = json.load(f)
            
            task_status.update(updates)
            task_status["updated_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
            
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(task_status, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", "更新任务状态失败: {}".format(str(e)))
            return False
    
    def get_task_status(self, task_id):
        """获取任务状态"""
        try:
            task_file = os.path.join(self.config_base_path, "tasks", "{}.json".format(task_id))
            if not os.path.exists(task_file):
                return None
            
            with open(task_file, 'r', encoding='utf-8') as f:
                task_status = json.load(f)
            
            return task_status
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", "获取任务状态失败: {}".format(str(e)))
            return None 