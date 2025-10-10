# -*- coding: utf-8 -*-
"""
Redis 主从复制后台任务
负责手动执行监控、健康检查、自动恢复等任务
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
from .sync_service import SyncService
from .monitor_service import MonitorService


class BackgroundTasks:
    """Redis 主从复制后台任务管理"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.redis_manager = RedisManager()
        self.slave_manager = SlaveManager()
        self.sync_service = SyncService()
        self.monitor_service = MonitorService()
    
    # ==================== 手动任务执行 ====================
    def manual_health_check(self):
        """手动执行健康检查"""
        try:
            public.WriteLog("TYPE_REDIS", "开始执行Redis健康检查任务")
            
            # 调用监控服务的健康检查
            result = self.monitor_service.health_check_task()
            
            if result:
                public.WriteLog("TYPE_REDIS", "Redis健康检查任务执行完成")
            else:
                public.WriteLog("TYPE_REDIS", "Redis健康检查任务执行失败")
            
            return result
                
        except Exception as e:
            public.WriteLog("TYPE_REDIS", f"健康检查任务异常: {str(e)}")
            return False
    
    def manual_monitor_check(self):
        """手动执行监控检查"""
        try:
            public.WriteLog("TYPE_REDIS", "开始执行Redis监控检查任务")
            
            # 调用监控服务的自动监控
            result = self.monitor_service.auto_monitor_task()
            
            if result:
                public.WriteLog("TYPE_REDIS", "Redis监控检查任务执行完成")
            else:
                public.WriteLog("TYPE_REDIS", "Redis监控检查任务执行失败")
            
            return result
                
        except Exception as e:
            public.WriteLog("TYPE_REDIS", f"监控检查任务异常: {str(e)}")
            return False
    
    def manual_sync_check(self):
        """手动执行同步检查"""
        try:
            public.WriteLog("TYPE_REDIS", "开始执行Redis自动同步任务")
            
            # 获取所有复制组
            all_groups = self.config_manager.get_all_replication_groups()
            
            success_count = 0
            total_count = len(all_groups)
            
            for group in all_groups:
                try:
                    group_id = group["group_id"]
                    result = self.sync_service.auto_sync_data(group_id)
                    
                    if result:
                        success_count += 1
                    else:
                        public.WriteLog("TYPE_REDIS", f"复制组 {group_id} 自动同步失败")
                        
                except Exception as e:
                    public.WriteLog("TYPE_REDIS", f"复制组 {group.get('group_id', 'unknown')} 自动同步异常: {str(e)}")
            
            public.WriteLog("TYPE_REDIS", f"Redis自动同步任务执行完成: {success_count}/{total_count} 成功")
            
            return success_count == total_count
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", f"自动同步任务异常: {str(e)}")
            return False
    
    def manual_log_cleanup(self):
        """手动执行日志清理"""
        try:
            public.WriteLog("TYPE_REDIS", "开始执行Redis日志清理任务")
            
            cleaned_count = 0
            
            # 获取所有复制组
            all_groups = self.config_manager.get_all_replication_groups()
            
            for group in all_groups:
                try:
                    group_id = group["group_id"]
                    
                    # 获取日志文件路径
                    log_file = os.path.join(self.config_manager.log_path, f"{group_id}.log")
                    
                    if os.path.exists(log_file):
                        # 获取文件大小
                        file_size = os.path.getsize(log_file)
                        
                        # 如果日志文件大于10MB，保留最后1000行
                        if file_size > 10 * 1024 * 1024:  # 10MB
                            try:
                                with open(log_file, 'r', encoding='utf-8') as f:
                                    lines = f.readlines()
                                
                                # 保留最后1000行
                                if len(lines) > 1000:
                                    with open(log_file, 'w', encoding='utf-8') as f:
                                        f.writelines(lines[-1000:])
                                    
                                    public.WriteLog("TYPE_REDIS", f"复制组 {group_id} 日志文件已清理")
                                    cleaned_count += 1
                            
                            except Exception as e:
                                public.WriteLog("TYPE_REDIS", f"清理复制组 {group_id} 日志失败: {str(e)}")
                
                except Exception as e:
                    public.WriteLog("TYPE_REDIS", f"处理复制组 {group.get('group_id', 'unknown')} 日志清理异常: {str(e)}")
            
            # 清理任务状态文件（保留最近30天）
            task_cleaned = self._cleanup_task_files()
            
            public.WriteLog("TYPE_REDIS", f"Redis日志清理任务执行完成: 清理了 {cleaned_count} 个日志文件，{task_cleaned} 个任务文件")
            
            return True
            
        except Exception as e:
            public.WriteLog("TYPE_REDIS", f"日志清理任务异常: {str(e)}")
            return False
    
    def _cleanup_task_files(self):
        """清理任务状态文件"""
        try:
            task_dir = os.path.join(self.config_manager.config_base_path, "tasks")
            if not os.path.exists(task_dir):
                return 0
            
            current_time = time.time()
            cleanup_threshold = 30 * 24 * 60 * 60  # 30天
            cleaned_count = 0
            
            for filename in os.listdir(task_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(task_dir, filename)
                    
                    try:
                        # 检查文件修改时间
                        file_mtime = os.path.getmtime(file_path)
                        
                        if current_time - file_mtime > cleanup_threshold:
                            os.remove(file_path)
                            cleaned_count += 1
                            
                    except Exception as e:
                        public.WriteLog("TYPE_REDIS", f"清理任务文件 {filename} 失败: {str(e)}")
            
            return cleaned_count
        
        except Exception as e:
            public.WriteLog("TYPE_REDIS", f"清理任务文件异常: {str(e)}")
            return 0


# 全局后台任务管理器实例
_background_tasks = None


def get_background_tasks():
    """获取后台任务管理器实例"""
    global _background_tasks
    if _background_tasks is None:
        _background_tasks = BackgroundTasks()
    return _background_tasks


# 兼容性保留，实际不启动定时任务
def start_background_tasks():
    """启动后台任务（已移除定时功能，仅创建实例）"""
    get_background_tasks()
    public.WriteLog("TYPE_REDIS", "Redis后台任务管理器已初始化（手动模式）")


def stop_background_tasks():
    """停止后台任务（已移除定时功能，无需操作）"""
    public.WriteLog("TYPE_REDIS", "Redis后台任务管理器已停止（手动模式）")


if __name__ == "__main__":
    # 用于测试或独立运行
    try:
        tasks = BackgroundTasks()
        
        print("Redis后台任务已启动，按 Ctrl+C 停止...")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("正在停止后台任务...")
        tasks.stop_background_tasks()
        print("后台任务已停止") 