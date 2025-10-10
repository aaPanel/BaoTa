# -*- coding: utf-8 -*-
"""
Redis 主从同步服务
负责创建主从复制组、管理同步流程、处理工作流任务等
"""

import json
import os
import sys
import time
import uuid
import threading

if '/www/server/panel/class' not in sys.path:
    sys.path.insert(0, '/www/server/panel/class')
if '/www/server/panel' not in sys.path:
    sys.path.insert(0, '/www/server/panel')

import public
from .config_manager import ConfigManager
from .redis_manager import RedisManager
from .slave_manager import SlaveManager
from mod.project.node.nodeutil import ServerNode, LocalNode

class SyncService:
    """Redis 主从同步服务"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.redis_manager = RedisManager()
        self.slave_manager = SlaveManager()
    
    # ==================== 创建主从复制组 ====================
    def create_replication_group(self, group_name, master_node, slave_nodes, password, master_ip):
        """创建主从复制组 - 启动异步任务"""
        try:
            # 生成任务ID
            task_id = str(uuid.uuid4())
            
            # 创建复制组配置（传入task_id）
            group_id = self.config_manager.create_group_config(
                group_name, master_node, slave_nodes, password, master_ip, task_id
            )
            
            if not group_id:
                return public.returnMsg(False, "创建复制组配置失败")
            
            # 创建任务状态
            self.config_manager.create_task_status(task_id, "create_group", group_id)
            
            # 启动异步创建任务
            thread = threading.Thread(
                target=self._create_group_workflow,
                args=(task_id, group_id, master_node, slave_nodes, password, master_ip)
            )
            thread.daemon = True
            thread.start()
            
            return public.returnMsg(True, {
                "task_id": task_id,
                "group_id": group_id,
                "message": "创建任务已启动"
            })
            
        except Exception as e:
            error_msg = "启动创建任务失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return public.returnMsg(False, error_msg)
    
    def _create_group_workflow(self, task_id, group_id, master_node, slave_nodes, password, master_ip):
        """创建复制组工作流"""
        try:
            # 更新任务状态
            self.config_manager.update_task_status(task_id, {
                "status": "running",
                "progress": 10,
                "message": "开始创建主从复制组"
            })
            
            self.config_manager.write_group_log(group_id, "开始创建主从复制组", "INFO")

            #放行主从节点6379端口
            # for node in slave_nodes:
            #     srv = ServerNode.new_by_id(node.get("id"))
            #     flag, msg = srv.set_firewall_open(6379, "tcp",True)

            
            # 步骤1: 配置主Redis节点
            self._update_task_step(task_id, 1, "配置主Redis节点", "running")
            master_result = self._configure_master_node(group_id, master_node, password)
            
            if not master_result.get("status"):
                self._fail_task(task_id, f"配置主节点失败: {master_result.get('msg')}")
                return
            
            self._update_task_step(task_id, 1, "配置主Redis节点", "completed")
            self.config_manager.update_task_status(task_id, {
                "progress": 30,
                "message": "主节点配置完成"
            })
            
            # 步骤2: 配置从Redis节点
            self._update_task_step(task_id, 2, "配置从Redis节点", "running")
            slaves_result = self._configure_slave_nodes(group_id, master_ip, slave_nodes, password)
            
            if not slaves_result.get("status"):
                self._fail_task(task_id, f"配置从节点失败: {slaves_result.get('msg')}")
                return
            
            self._update_task_step(task_id, 2, "配置从Redis节点", "completed")
            self.config_manager.update_task_status(task_id, {
                "progress": 60,
                "message": "从节点配置完成"
            })
            
            # 步骤3: 验证复制状态
            self._update_task_step(task_id, 3, "验证复制状态", "running")
            verify_result = self._verify_replication_status(group_id, slave_nodes, password)
            
            if not verify_result.get("status"):
                self._fail_task(task_id, f"复制状态验证失败: {verify_result.get('msg')}")
                return
            
            self._update_task_step(task_id, 3, "验证复制状态", "completed")
            self.config_manager.update_task_status(task_id, {
                "progress": 85,
                "message": "复制状态验证完成"
            })
            
            # 步骤4: 主从配置配置完成
            self._update_task_step(task_id, 4, "主从配置配置完成", "running")
            # 这个步骤不需要做任何操作，直接标记为完成
            self._update_task_step(task_id, 4, "主从配置配置完成", "completed")
            self.config_manager.write_group_log(group_id, "主从配置配置完成", "INFO")
            
            # 完成任务
            self.config_manager.update_task_status(task_id, {
                "status": "completed",
                "progress": 100,
                "message": "主从复制组创建成功"
            })
            
            self.config_manager.update_group_config(group_id, {"status": "active"})
            self.config_manager.write_group_log(group_id, "主从复制组创建成功", "INFO")
            
        except Exception as e:
            error_msg = "创建工作流执行失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            self._fail_task(task_id, error_msg)
    
    def _configure_master_node(self, group_id, master_node, password):
        """配置主节点"""
        try:
            self.config_manager.write_group_log(
                group_id, 
                f"开始配置主节点: {master_node.get('server_ip')}"
            )
            
            # 检查Redis服务状态
            service_check = self.redis_manager.check_redis_service(master_node.get("id"))
            if not service_check.get("status"):
                return public.returnMsg(False, f"主节点Redis服务检查失败: {service_check.get('msg')}")
            
            # 配置主节点
            config_result = self.redis_manager.configure_master(master_node.get("id"), password)
            if not config_result.get("status"):
                return config_result
            
            self.config_manager.write_group_log(
                group_id, 
                f"主节点配置完成: {master_node.get('server_ip')}"
            )
            
            return public.returnMsg(True, "主节点配置成功")
            
        except Exception as e:
            error_msg = "配置主节点失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return public.returnMsg(False, error_msg)
    
    def _configure_slave_nodes(self, group_id, master_ip, slave_nodes, password):
        """配置从节点"""
        try:
            success_count = 0
            
            for slave_node in slave_nodes:
                try:
                    self.config_manager.write_group_log(
                        group_id, 
                        f"开始配置从节点: {slave_node.get('server_ip')}"
                    )
                    
                    # 检查从节点Redis服务状态
                    service_check = self.redis_manager.check_redis_service(slave_node.get("id"))
                    if not service_check.get("status"):
                        self.config_manager.write_group_log(
                            group_id, 
                            f"从节点Redis服务检查失败: {slave_node.get('server_ip')} - {service_check.get('msg')}",
                            "ERROR"
                        )
                        continue
                    
                    # 配置从节点
                    config_result = self.redis_manager.configure_slave(
                        slave_node.get("id"), master_ip, "6379", password
                    )
                    
                    if config_result.get("status"):
                        success_count += 1
                        self.config_manager.write_group_log(
                            group_id, 
                            f"从节点配置成功: {slave_node.get('server_ip')}"
                        )
                    else:
                        self.config_manager.write_group_log(
                            group_id, 
                            f"从节点配置失败: {slave_node.get('server_ip')} - {config_result.get('msg')}",
                            "ERROR"
                        )
                        
                except Exception as e:
                    self.config_manager.write_group_log(
                        group_id, 
                        f"从节点配置异常: {slave_node.get('server_ip')} - {str(e)}",
                        "ERROR"
                    )
            
            if success_count == 0:
                return public.returnMsg(False, "所有从节点配置失败")
            elif success_count < len(slave_nodes):
                return public.returnMsg(True, f"部分从节点配置成功 ({success_count}/{len(slave_nodes)})")
            else:
                return public.returnMsg(True, "所有从节点配置成功")
                
        except Exception as e:
            error_msg = "配置从节点失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return public.returnMsg(False, error_msg)
    
    def _verify_replication_status(self, group_id, slave_nodes, password):
        """验证复制状态"""
        try:
            self.config_manager.write_group_log(group_id, "开始验证复制状态")
            
            # 等待同步稳定
            time.sleep(5)
            
            success_count = 0
            
            for slave_node in slave_nodes:
                try:
                    # 获取从节点复制状态
                    status_result = self.slave_manager.get_slave_replication_status(
                        slave_node.get("id"), password
                    )
                    
                    if status_result.get("status"):
                        repl_data = status_result["data"]
                        if repl_data.get("is_online", False):
                            success_count += 1
                            self.config_manager.write_group_log(
                                group_id, 
                                f"从节点复制正常: {slave_node.get('server_ip')}"
                            )
                        else:
                            self.config_manager.write_group_log(
                                group_id, 
                                f"从节点复制异常: {slave_node.get('server_ip')} - 连接状态: {repl_data.get('master_link_status')}",
                                "WARNING"
                            )
                    else:
                        self.config_manager.write_group_log(
                            group_id, 
                            f"从节点状态检查失败: {slave_node.get('server_ip')} - {status_result.get('msg')}",
                            "ERROR"
                        )
                        
                except Exception as e:
                    self.config_manager.write_group_log(
                        group_id, 
                        f"从节点状态验证异常: {slave_node.get('server_ip')} - {str(e)}",
                        "ERROR"
                    )
            
            if success_count == 0:
                return public.returnMsg(False, "所有从节点复制状态异常")
            elif success_count < len(slave_nodes):
                return public.returnMsg(True, f"部分从节点复制正常 ({success_count}/{len(slave_nodes)})")
            else:
                return public.returnMsg(True, "所有从节点复制正常")
                
        except Exception as e:
            error_msg = "验证复制状态失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return public.returnMsg(False, error_msg)
    
    # ==================== 任务状态管理 ====================
    def _update_task_step(self, task_id, step_num, step_name, status):
        """更新任务步骤状态"""
        try:
            task_status = self.config_manager.get_task_status(task_id)
            if not task_status:
                return
            
            steps = task_status.get("steps", [])
            
            # 查找或创建步骤
            step_found = False
            for step in steps:
                if step.get("step") == step_num:
                    step["status"] = status
                    step["updated_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    if status == "completed":
                        step["completed_time"] = step["updated_time"]
                    step_found = True
                    break
            
            if not step_found:
                new_step = {
                    "step": step_num,
                    "name": step_name,
                    "status": status,
                    "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "updated_time": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                if status == "completed":
                    new_step["completed_time"] = new_step["updated_time"]
                steps.append(new_step)
            
            self.config_manager.update_task_status(task_id, {"steps": steps})
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", f"更新任务步骤失败: {str(e)}")
    
    def _fail_task(self, task_id, error_message):
        """标记任务失败"""
        try:
            self.config_manager.update_task_status(task_id, {
                "status": "failed",
                "progress": 0,
                "message": error_message,
                "error_time": time.strftime("%Y-%m-%d %H:%M:%S")
            })
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", f"标记任务失败异常: {str(e)}")
    
    def get_creation_status(self, task_id):
        """获取创建状态"""
        try:
            task_status = self.config_manager.get_task_status(task_id)
            if not task_status:
                return public.returnMsg(False, "未找到任务状态")
            
            # 如果任务关联的复制组存在，添加日志信息
            group_id = task_status.get("group_id")
            if group_id:
                logs = self.config_manager.get_group_log(group_id, 50)
                task_status["logs"] = logs
            
            return {
                "status": True,
                "msg": "success",
                "data": task_status
            }
            
        except Exception as e:
            error_msg = "获取创建状态失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return public.returnMsg(False, error_msg)
    
    # ==================== 同步配置管理 ====================
    def sync_slave_config(self, slave_node_id):
        """手动同步从库配置"""
        try:
            # 获取从库所属的复制组
            group_config = self.config_manager.get_group_by_slave(slave_node_id)
            if not group_config:
                return public.returnMsg(False, "未找到从库所属的复制组")
            
            master_ip = group_config["master_ip"]
            master_port = group_config["master_port"]
            password = group_config["redis_password"]
            
            # 重新配置从库
            result = self.redis_manager.configure_slave(
                slave_node_id, master_ip, master_port, password
            )
            
            if result.get("status"):
                self.config_manager.write_group_log(
                    group_config["group_id"],
                    f"从库 {slave_node_id} 配置同步成功"
                )
                return public.returnMsg(True, "同步配置成功")
            else:
                self.config_manager.write_group_log(
                    group_config["group_id"],
                    f"从库 {slave_node_id} 配置同步失败: {result.get('msg')}",
                    "ERROR"
                )
                return result
                
        except Exception as e:
            error_msg = "同步从库配置失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return public.returnMsg(False, error_msg)
    
    # ==================== 数据同步任务 ====================
    def auto_sync_data(self, group_id):
        """自动同步数据（后台任务调用）"""
        try:
            group_config = self.config_manager.get_group_config(group_id)
            if not group_config:
                return False
            
            password = group_config["redis_password"]
            slave_nodes = group_config.get("slave_nodes", [])
            
            # 检查所有从节点状态
            for slave_node_id in slave_nodes:
                try:
                    status_result = self.slave_manager.get_slave_replication_status(
                        slave_node_id, password
                    )
                    
                    if status_result.get("status"):
                        repl_data = status_result["data"]
                        if not repl_data.get("is_online", False):
                            # 尝试重连
                            self.slave_manager.reconnect_slave(group_id, slave_node_id)
                    else:
                        # 检查Redis服务状态
                        redis_status = self.slave_manager.check_slave_redis_status(slave_node_id)
                        if not redis_status.get("status"):
                            self.config_manager.write_group_log(
                                group_id,
                                f"从库 {slave_node_id} Redis服务异常: {redis_status.get('msg')}",
                                "ERROR"
                            )
                            
                except Exception as e:
                    self.config_manager.write_group_log(
                        group_id,
                        f"检查从库 {slave_node_id} 状态异常: {str(e)}",
                        "ERROR"
                    )
            
            return True
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", f"自动同步数据失败: {str(e)}")
            return False
    
    def manual_sync_data(self, group_id):
        """手动同步数据（后台任务调用）"""
        try:
            group_config = self.config_manager.get_group_config(group_id)
            if not group_config:
                return False
            
            password = group_config["redis_password"]
            slave_nodes = group_config.get("slave_nodes", [])
            master_node_id = group_config["master_node_id"]
            
            # 获取主节点复制信息
            master_repl_info = self.redis_manager.get_replication_info(master_node_id, password)
            if not master_repl_info.get("status"):
                self.config_manager.write_group_log(
                    group_id,
                    f"获取主节点复制信息失败: {master_repl_info.get('msg')}",
                    "ERROR"
                )
                return False
            
            # 强制重新同步所有从节点
            for slave_node_id in slave_nodes:
                try:
                    # 停止复制
                    self.redis_manager.stop_replication(slave_node_id, password)
                    time.sleep(1)
                    
                    # 重新启动复制
                    self.slave_manager.reconnect_slave(group_id, slave_node_id)
                    
                    self.config_manager.write_group_log(
                        group_id,
                        f"从库 {slave_node_id} 手动同步完成"
                    )
                    
                except Exception as e:
                    self.config_manager.write_group_log(
                        group_id,
                        f"从库 {slave_node_id} 手动同步失败: {str(e)}",
                        "ERROR"
                    )
            
            return True
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", f"手动同步数据失败: {str(e)}")
            return False
    
    # ==================== 工具方法 ====================
    def validate_group_config(self, group_name, master_node, slave_nodes, password):
        """验证复制组配置"""
        try:
            # 检查名称
            if not group_name or not group_name.strip():
                return public.returnMsg(False, "复制组名称不能为空")
            
            # 检查名称是否已存在
            if self.config_manager.group_name_exists(group_name):
                return public.returnMsg(False, "复制组名称已存在")
            
            # 检查密码强度
            if not password or len(password) < 8:
                return public.returnMsg(False, "密码长度不能少于8位")
            
            # 检查主从节点不能重复
            master_id = master_node.get("id")
            slave_ids = [node.get("id") for node in slave_nodes]
            
            if master_id in slave_ids:
                return public.returnMsg(False, "主节点不能同时作为从节点")
            
            # 检查从节点不能重复
            if len(slave_ids) != len(set(slave_ids)):
                return public.returnMsg(False, "从节点不能重复")
            
            return public.returnMsg(True, "配置验证通过")
            
        except Exception as e:
            error_msg = "验证复制组配置失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            return public.returnMsg(False, error_msg)
    
    # ==================== 追加从节点功能 ====================
    def add_slave_to_existing_group(self, group_id, new_slave_node_id):
        """向现有复制组添加新的从节点（同步执行）"""
        try:
            # 1. 获取复制组配置
            group_config = self.config_manager.get_group_config(group_id)
            if not group_config:
                return public.returnMsg(False, "未找到复制组配置")
            
            # 检查复制组状态
            if group_config.get("status") != "active":
                return public.returnMsg(False, "复制组状态异常，无法添加从节点,建议删除复制组后重新创建")
            
            # 2. 获取新从节点信息
            new_slave_node = public.M("node").where("id = ?", (new_slave_node_id,)).find()
            if not new_slave_node:
                return public.returnMsg(False, "未找到新从节点信息")
            
            # 3. 验证节点不能重复
            existing_slaves = group_config.get('slave_nodes', [])
            master_node_id = group_config.get('master_node_id')
            
            if new_slave_node_id in existing_slaves:
                return public.returnMsg(False, "该节点已是此复制组的从节点")
            
            if new_slave_node_id == master_node_id:
                return public.returnMsg(False, "不能将主节点添加为从节点")
            
            # 4. 验证IP不能与主节点相同
            master_ip = group_config.get('master_ip')
            slave_ip = new_slave_node.get('server_ip', '').split(':')[0]
            if master_ip == slave_ip:
                return public.returnMsg(False, "从节点IP不能与主节点IP相同")
            
            # 记录开始操作
            self.config_manager.write_group_log(
                group_id, 
                f"开始添加新从节点: {new_slave_node.get('server_ip')} (ID: {new_slave_node_id})", 
                "INFO"
            )
            
            # 5. 检查新从节点Redis服务状态
            service_check = self.redis_manager.check_redis_service(new_slave_node_id)
            if not service_check.get("status"):
                error_msg = f"新从节点Redis服务检查失败: {service_check.get('msg')}"
                self.config_manager.write_group_log(group_id, error_msg, "ERROR")
                return public.returnMsg(False, error_msg)
            
            # 6. 配置新从节点
            master_port = group_config.get('master_port', '6379')
            password = group_config.get('redis_password')
            
            config_result = self.redis_manager.configure_slave(
                new_slave_node_id, master_ip, master_port, password
            )
            
            if not config_result.get("status"):
                error_msg = f"配置新从节点失败: {config_result.get('msg')}"
                self.config_manager.write_group_log(group_id, error_msg, "ERROR")
                return public.returnMsg(False, error_msg)
            
            self.config_manager.write_group_log(
                group_id, 
                f"新从节点配置完成: {new_slave_node.get('server_ip')}", 
                "INFO"
            )
            
            # 7. 更新复制组配置
            add_result = self.config_manager.add_slave_to_group(group_id, new_slave_node_id)
            if not add_result:
                error_msg = "更新复制组配置失败"
                self.config_manager.write_group_log(group_id, error_msg, "ERROR")
                return public.returnMsg(False, error_msg)
            
            # 8. 等待复制稳定并验证状态
            import time
            time.sleep(3)
            
            status_result = self.slave_manager.get_slave_replication_status(new_slave_node_id, password)
            if status_result.get("status"):
                repl_data = status_result["data"]
                if repl_data.get("is_online", False):
                    self.config_manager.write_group_log(
                        group_id, 
                        f"新从节点复制状态正常: {new_slave_node.get('server_ip')}", 
                        "INFO"
                    )
                    return public.returnMsg(True, "新从节点添加成功")
                else:
                    warning_msg = f"新从节点已添加，但复制状态异常: 连接状态={repl_data.get('master_link_status', 'unknown')}"
                    self.config_manager.write_group_log(group_id, warning_msg, "WARNING")
                    return public.returnMsg(True, warning_msg)
            else:
                warning_msg = f"新从节点已添加，但无法验证复制状态: {status_result.get('msg')}"
                self.config_manager.write_group_log(group_id, warning_msg, "WARNING")
                return public.returnMsg(True, warning_msg)
                
        except Exception as e:
            error_msg = "添加新从节点失败: {}".format(str(e))
            public.WriteLog("TYPE_REDIS", error_msg)
            try:
                self.config_manager.write_group_log(group_id, error_msg, "ERROR")
            except:
                pass
            return public.returnMsg(False, error_msg) 