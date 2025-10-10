# -*- coding: utf-8 -*-
"""
Redis 管理器
负责Redis连接、版本检查、基础操作等
"""

import json
import os
import sys
import time
import subprocess

if '/www/server/panel/class' not in sys.path:
    sys.path.insert(0, '/www/server/panel/class')
if '/www/server/panel' not in sys.path:
    sys.path.insert(0, '/www/server/panel')

import public
from mod.project.node.redis_slave_util.bt_api import BtApi


class RedisManager:
    """Redis 管理器"""
    
    def __init__(self):
        # 不在初始化时创建 BtApi 实例，而是在需要时动态创建
        self.redis_config_path = "/www/server/redis/redis.conf"  # 宝塔面板Redis配置文件路径
    
    def _get_bt_api(self, panel_addr, panel_key):
        """获取 BtApi 实例"""
        return BtApi(panel_addr, panel_key)
    
    def _is_local_node(self, node_data):
        """判断是否为本地节点"""
        server_ip = node_data.get("server_ip", "")
        # 提取IP地址（去除端口）
        ip = server_ip.split(":")[0] if ":" in server_ip else server_ip
        return ip == "127.0.0.1" or ip == "localhost"
    
    def _execute_command(self, node_data, command):
        """统一的命令执行方法"""
        try:
            if self._is_local_node(node_data):
                # 本机节点执行
                result = public.ExecShell(command)
                stdout, stderr = result[0], result[1]
                
                if stderr and stderr.strip():
                    return {"status": False, "msg": stderr.strip()}
                else:
                    return {"status": True, "msg": stdout.strip() if stdout else ""}
            else:
                # 远程节点通过API执行
                bt_api = self._get_bt_api(node_data.get("address"), node_data.get("api_key") or node_data.get("app_key"))
                return bt_api.slave_execute_command(command)
        except Exception as e:
            return {"status": False, "msg": str(e)}
    
    def _get_node_data(self, node_id):
        """获取节点数据"""
        try:
            if node_id is None:
                return None
            
            node_data = public.M("node").where("id = ?", (node_id,)).find()
            return node_data
        except Exception as e:
            public.WriteLog("TYPE_REDIS", f"获取节点数据失败: {str(e)}")
            return None
    
    def _modify_redis_config(self, node_data, config_changes):
        """修改Redis配置文件"""
        try:
            config_file = self.redis_config_path
            
            # 构建sed命令来修改配置
            commands = []
            
            for key, value in config_changes.items():
                if value is None:
                    # 删除配置项（匹配以key开头的行）
                    sed_cmd = f"sed -i '/^{key}\\s/d; /^#{key}\\s/d' {config_file}"
                    commands.append(sed_cmd)
                else:
                    # 先删除旧配置（包括注释的），再添加新配置
                    delete_cmd = f"sed -i '/^{key}\\s/d; /^#{key}\\s/d' {config_file}"
                    add_cmd = f"echo '{key} {value}' >> {config_file}"
                    commands.extend([delete_cmd, add_cmd])
            
            # 执行所有配置命令
            for cmd in commands:
                result = self._execute_command(node_data, cmd)
                if not result.get("status"):
                    return {"status": False, "msg": f"配置修改失败: {result.get('msg')}"}
            
            return {"status": True, "msg": "配置修改成功"}
            
        except Exception as e:
            return {"status": False, "msg": f"配置修改异常: {str(e)}"}
    
    def _restart_redis_service(self, node_data):
        """重启Redis服务"""
        try:
            # 尝试多种重启方式
            restart_commands = [
                "systemctl restart redis",
                "service redis restart", 
                "/etc/init.d/redis restart 2>&1"
            ]
            
            for cmd in restart_commands:
                result = self._execute_command(node_data, cmd)
                if result.get("status"):
                    # 等待服务启动
                    time.sleep(3)
                    # 检查服务状态
                    check_result = self._execute_command(node_data, "ps aux | grep redis-server | grep -v grep | wc -l")
                    if check_result.get("status") and int(check_result.get("msg", "0").strip()) > 0:
                        return {"status": True, "msg": "Redis服务重启成功"}
            
            return {"status": False, "msg": "Redis服务重启失败"}
            
        except Exception as e:
            return {"status": False, "msg": f"重启服务异常: {str(e)}"}
    
    # ==================== 版本检查 ====================
    def get_redis_version(self, node_id=None):
        """获取Redis版本"""
        try:
            if node_id:
                # 通过API获取指定节点的Redis版本
                node_data = public.M("node").where("id = ?", (node_id,)).find()
                if not node_data:
                    return None
                
                result = self._execute_command(node_data, "redis-cli --version")
                
                if result.get("status") and result.get("msg"):
                    version_output = result["msg"]
                    # 解析版本号，例如: redis-cli 6.2.6
                    if "redis-cli" in version_output:
                        parts = version_output.split()
                        if len(parts) >= 2:
                            version = parts[1]
                            # 检查版本是否满足要求 (>= 3.2)
                            if self.check_redis_version(version):
                                return version
                return None
            else:
                # 本地Redis版本检查
                result = public.ExecShell("redis-cli --version")[0]
                if "redis-cli" in result:
                    parts = result.split()
                    if len(parts) >= 2:
                        version = parts[1]
                        if self.check_redis_version(version):
                            return version
                return None
                
        except Exception as e:
            public.WriteLog("TYPE_REDIS", "获取Redis版本失败: {}".format(str(e)))
            return None
    
    def check_redis_version(self, version):
        """检查Redis版本是否满足要求 (>= 3.2)"""
        try:
            version_parts = version.split('.')
            major = int(version_parts[0])
            minor = int(version_parts[1]) if len(version_parts) > 1 else 0
            
            return major > 3 or (major == 3 and minor >= 2)
            
        except Exception:
            return False
    
    def get_redis_version_by_node(self, node_id):
        """通过节点ID获取Redis版本"""
        try:
            node_data = self._get_node_data(node_id)
            if not node_data:
                return None
            
            result = self._execute_command(node_data, "redis-cli --version")
            
            if result.get("status") and result.get("msg"):
                version_output = result["msg"]
                # 解析版本号，例如: redis-cli 6.2.6
                if "redis-cli" in version_output:
                    parts = version_output.split()
                    if len(parts) >= 2:
                        version = parts[1]
                        # 检查版本是否满足要求 (>= 3.2)
                        if self.check_redis_version(version):
                            return version
            return None
                
        except Exception as e:
            public.WriteLog("TYPE_REDIS", f"获取节点 {node_id} Redis版本失败: {str(e)}")
            return None
    
    def get_memory_info(self, node_id, password=None):
        """获取Redis内存信息"""
        try:
            # 获取内存相关信息
            memory_info = self.get_redis_info(node_id, "memory", password)
            
            if memory_info and memory_info.get("status"):
                info_data = memory_info["data"]
                
                used_memory = int(info_data.get("used_memory", 0))
                max_memory = int(info_data.get("maxmemory", 0))
                
                # 如果没有设置maxmemory，尝试获取系统内存
                if max_memory == 0:
                    # 获取系统内存信息
                    node_data = self._get_node_data(node_id)
                    if node_data:
                        sys_result = self._execute_command(node_data, "cat /proc/meminfo | grep MemTotal | awk '{print $2}'")
                        if sys_result.get("status"):
                            # MemTotal是KB，转换为字节
                            max_memory = int(sys_result.get("msg", "0").strip()) * 1024
                
                usage_percent = (used_memory / max_memory) if max_memory > 0 else 0
                used_memory_human = info_data.get("used_memory_human", "")
                
                return {
                    "status": True,
                    "data": {
                        "used_memory": used_memory,
                        "max_memory": max_memory,
                        "usage_percent": usage_percent,
                        "used_memory_human": used_memory_human
                    }
                }
            else:
                return {"status": False, "msg": "无法获取内存信息"}
                
        except Exception as e:
            error_msg = f"获取节点 {node_id} 内存信息失败: {str(e)}"
            public.WriteLog("TYPE_REDIS", error_msg)
            return {"status": False, "msg": error_msg}
    
    # ==================== 服务状态检查 ====================
    def check_redis_service(self, node_id):
        """检查Redis服务状态"""
        try:
            node_data = public.M("node").where("id = ?", (node_id,)).find()
            if not node_data:
                return {"status": False, "msg": "未找到节点信息"}
            
            # 检查Redis进程
            result = self._execute_command(node_data, "ps aux | grep redis-server | grep -v grep | wc -l")
            
            if result.get("status"):
                process_count = int(result.get("msg", "0").strip())
                if process_count > 0:
                    return {"status": True, "msg": "Redis服务正常运行"}
                else:
                    return {"status": False, "msg": "Redis服务未运行"}
            else:
                return {"status": False, "msg": "无法检查Redis服务状态"}
                
        except Exception as e:
            error_msg = "检查Redis服务状态失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return {"status": False, "msg": error_msg}
    
    # ==================== 主从复制配置 ====================
    def configure_master(self, node_id, password):
        """配置Redis主节点"""
        try:
            node_data = public.M("node").where("id = ?", (node_id,)).find()
            if not node_data:
                return public.returnMsg(False, "未找到节点信息")
            
            # 配置主节点参数
            config_changes = {
                "requirepass": password,
                "masterauth": password,
                "replica-read-only": "yes",
                "repl-diskless-sync": "yes",
                "bind": "0.0.0.0",  # 允许外部连接
                "protected-mode": "no"  # 关闭保护模式以允许远程连接
            }
            
            # 修改配置文件
            config_result = self._modify_redis_config(node_data, config_changes)
            if not config_result.get("status"):
                return public.returnMsg(False, f"修改主节点配置失败: {config_result.get('msg')}")
            
            # 重启Redis服务
            restart_result = self._restart_redis_service(node_data)
            if not restart_result.get("status"):
                return public.returnMsg(False, f"重启Redis服务失败: {restart_result.get('msg')}")
            
            return public.returnMsg(True, "主节点配置成功")
            
        except Exception as e:
            error_msg = "配置Redis主节点失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return public.returnMsg(False, error_msg)
    
    def configure_slave(self, slave_node_id, master_host, master_port, password):
        """配置Redis从节点"""
        try:
            node_data = public.M("node").where("id = ?", (slave_node_id,)).find()
            if not node_data:
                return public.returnMsg(False, "未找到从节点信息")
            
            # 配置从节点参数
            config_changes = {
                "requirepass": password,
                "masterauth": password,
                "replicaof": f"{master_host} {master_port}",
                "replica-read-only": "yes",
                "bind": "0.0.0.0",  # 允许外部连接（用于监控）
                "protected-mode": "no"
            }
            
            # 修改配置文件
            config_result = self._modify_redis_config(node_data, config_changes)
            if not config_result.get("status"):
                return public.returnMsg(False, f"修改从节点配置失败: {config_result.get('msg')}")
            
            # 重启Redis服务
            restart_result = self._restart_redis_service(node_data)
            if not restart_result.get("status"):
                return public.returnMsg(False, f"重启Redis服务失败: {restart_result.get('msg')}")
            
            return public.returnMsg(True, "从节点配置成功")
            
        except Exception as e:
            error_msg = "配置Redis从节点失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return public.returnMsg(False, error_msg)
    
    def stop_replication(self, slave_node_id, password=None):
        """停止从节点复制"""
        try:
            node_data = public.M("node").where("id = ?", (slave_node_id,)).find()
            if not node_data:
                return public.returnMsg(False, "未找到从节点信息")
            
            # 移除复制配置
            config_changes = {
                "replicaof": None  # 删除replicaof配置
            }
            
            # 修改配置文件
            config_result = self._modify_redis_config(node_data, config_changes)
            if not config_result.get("status"):
                return public.returnMsg(False, f"修改配置失败: {config_result.get('msg')}")
            
            # 重启Redis服务
            restart_result = self._restart_redis_service(node_data)
            if not restart_result.get("status"):
                return public.returnMsg(False, f"重启服务失败: {restart_result.get('msg')}")
            
            return public.returnMsg(True, "停止复制成功")
            
        except Exception as e:
            error_msg = "停止Redis复制失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return public.returnMsg(False, error_msg)
    
    # ==================== Redis命令执行 ====================
    def execute_redis_command(self, node_id, command, password=None):
        """执行Redis命令"""
        try:
            # 获取节点信息
            node_data = self._get_node_data(node_id)
            if not node_data:
                return {"status": False, "msg": "未找到节点信息"}
            
            # 解析服务器地址和端口
            server_ip = node_data.get("server_ip", "")
            if ":" in server_ip:
                host, port = server_ip.split(":", 1)
            else:
                host = server_ip
                port = "6379"
            
            # 根据是否为本地节点选择连接方式
            if self._is_local_node(node_data):
                # 本地节点使用127.0.0.1连接
                if password:
                    # 使用管道方式先认证再执行命令
                    full_cmd = f"echo -e 'AUTH {password}\\n{command}' | redis-cli -h 127.0.0.1 -p {port}"
                else:
                    full_cmd = f"redis-cli -h 127.0.0.1 -p {port} -c '{command}'"
            else:
                # 远程节点使用实际IP连接
                if password:
                    # 使用管道方式先认证再执行命令
                    full_cmd = f"echo -e 'AUTH {password}\\n{command}' | redis-cli -h {host} -p {port}"
                else:
                    full_cmd = f"redis-cli -h {host} -p {port} -c '{command}'"
            
            result = self._execute_command(node_data, full_cmd)
            
            if result.get("status"):
                return {
                    "status": True,
                    "data": result.get("msg", "").strip()
                }
            else:
                return {
                    "status": False,
                    "msg": result.get("msg", "命令执行失败")
                }
                
        except Exception as e:
            error_msg = "执行Redis命令失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return {"status": False, "msg": error_msg}
    
    # ==================== 信息获取 ====================
    def get_redis_info(self, node_id, section=None, password=None):
        """获取Redis信息"""
        try:
            command = "INFO"
            if section:
                command = f"INFO {section}"
            
            result = self.execute_redis_command(node_id, command, password)
            if result.get("status"):
                # 解析INFO命令输出
                info_data = self.parse_redis_info(result["data"])
                return {"status": True, "data": info_data}
            else:
                return result
                
        except Exception as e:
            error_msg = "获取Redis信息失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return {"status": False, "msg": error_msg}
    
    def parse_redis_info(self, info_output):
        """解析Redis INFO命令输出"""
        try:
            info_dict = {}
            current_section = "general"
            
            for line in info_output.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    if line.startswith('# '):
                        current_section = line[2:].lower()
                    continue
                
                if ':' in line:
                    key, value = line.split(':', 1)
                    # 尝试转换数值
                    try:
                        if '.' in value:
                            value = float(value)
                        elif value.isdigit():
                            value = int(value)
                    except ValueError:
                        pass
                    
                    if current_section not in info_dict:
                        info_dict[current_section] = {}
                    info_dict[current_section][key] = value
            
            return info_dict
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", "解析Redis信息失败: {}".format(str(e)))
            return {}
    
    # ==================== 监控数据获取 ====================
    def get_memory_usage(self, node_id, password=None):
        """获取内存使用情况"""
        try:
            info_result = self.get_redis_info(node_id, "memory", password)
            if not info_result.get("status"):
                return {"status": False, "msg": info_result.get("msg")}
            
            memory_info = info_result["data"].get("memory", {})
            used_memory = memory_info.get("used_memory", 0)
            max_memory = memory_info.get("maxmemory", 0)
            
            # 如果没有设置maxmemory，尝试获取系统内存
            if max_memory == 0:
                max_memory = memory_info.get("total_system_memory", 0)
            
            usage_percent = 0
            if max_memory > 0:
                usage_percent = round((used_memory / max_memory) * 100, 2)
            
            return {
                "status": True,
                "data": {
                    "used_memory": used_memory,
                    "max_memory": max_memory,
                    "usage_percent": usage_percent,
                    "used_memory_human": memory_info.get("used_memory_human", "0B")
                }
            }
            
        except Exception as e:
            error_msg = "获取内存使用情况失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return {"status": False, "msg": error_msg}
    
    def get_performance_stats(self, node_id, password=None):
        """获取性能统计"""
        try:
            info_result = self.get_redis_info(node_id, "stats", password)
            if not info_result.get("status"):
                return {"status": False, "msg": info_result.get("msg")}
            
            stats_info = info_result["data"].get("stats", {})
            
            return {
                "status": True,
                "data": {
                    "qps": stats_info.get("instantaneous_ops_per_sec", 0),
                    "total_commands": stats_info.get("total_commands_processed", 0),
                    "keyspace_hits": stats_info.get("keyspace_hits", 0),
                    "keyspace_misses": stats_info.get("keyspace_misses", 0),
                    "hit_rate": self.calculate_hit_rate(
                        stats_info.get("keyspace_hits", 0),
                        stats_info.get("keyspace_misses", 0)
                    )
                }
            }
            
        except Exception as e:
            error_msg = "获取性能统计失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return {"status": False, "msg": error_msg}
    
    def get_connection_info(self, node_id, password=None):
        """获取连接信息"""
        try:
            info_result = self.get_redis_info(node_id, "clients", password)
            if not info_result.get("status"):
                return {"status": False, "msg": info_result.get("msg")}
            
            clients_info = info_result["data"].get("clients", {})
            
            return {
                "status": True,
                "data": {
                    "connected_clients": clients_info.get("connected_clients", 0),
                    "max_clients": clients_info.get("maxclients", 0),
                    "total_connections": clients_info.get("total_connections_received", 0),
                    "rejected_connections": clients_info.get("rejected_connections", 0)
                }
            }
            
        except Exception as e:
            error_msg = "获取连接信息失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return {"status": False, "msg": error_msg}
    
    def get_replication_info(self, node_id, password=None):
        """获取复制信息"""
        try:
            info_result = self.get_redis_info(node_id, "replication", password)
            if not info_result.get("status"):
                return {"status": False, "msg": info_result.get("msg")}
            print(info_result)
            repl_info = info_result["data"].get("replication", {})
            
            return {
                "status": True,
                "data": repl_info
            }
            
        except Exception as e:
            error_msg = "获取复制信息失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return {"status": False, "msg": error_msg}
    
    # ==================== 工具方法 ====================
    def calculate_hit_rate(self, hits, misses):
        """计算缓存命中率"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)
    
    def cleanup_replication_users(self, master_node_id):
        """清理复制相关配置"""
        try:
            node_data = public.M("node").where("id = ?", (master_node_id,)).find()
            if not node_data:
                public.WriteLog("TYPE_REDIS", f"未找到主节点信息: {master_node_id}")
                return False
            
            # 清理主节点的复制相关配置
            config_changes = {
                "requirepass": None,  # 删除密码配置
                "masterauth": None,   # 删除主节点认证配置
                "bind": "127.0.0.1",  # 恢复默认绑定
                "protected-mode": "yes"  # 恢复保护模式
            }
            
            # 修改配置文件
            config_result = self._modify_redis_config(node_data, config_changes)
            if not config_result.get("status"):
                public.WriteLog("TYPE_REDIS", f"清理主节点配置失败: {config_result.get('msg')}")
                return False
            
            # 重启Redis服务使配置生效
            restart_result = self._restart_redis_service(node_data)
            if not restart_result.get("status"):
                public.WriteLog("TYPE_REDIS", f"重启主节点Redis服务失败: {restart_result.get('msg')}")
                return False
            
            return True
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", "清理复制配置失败: {}".format(str(e)))
            return False
    
    def get_server_info(self, node_id, password=None):
        """获取服务器基础信息"""
        try:
            info_result = self.get_redis_info(node_id, "server", password)
            if not info_result.get("status"):
                return {"status": False, "msg": info_result.get("msg")}
            
            server_info = info_result["data"].get("server", {})
            
            return {
                "status": True,
                "data": {
                    "redis_version": server_info.get("redis_version", ""),
                    "uptime_days": server_info.get("uptime_in_days", 0),
                    "tcp_port": server_info.get("tcp_port", 6379),
                    "process_id": server_info.get("process_id", 0)
                }
            }
            
        except Exception as e:
            error_msg = "获取服务器信息失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return {"status": False, "msg": error_msg} 