# coding: utf-8
# -------------------------------------------------------------------
# MySQL Binlog增量备份系统 - 清理管理模块
# -------------------------------------------------------------------
# Author: miku <miku@bt.cn>
# -------------------------------------------------------------------

import json
import os
import sys
import time
import datetime
import threading
from typing import Dict, List, Any, Optional

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

if '/www/server/panel' not in sys.path:
    sys.path.insert(0, '/www/server/panel')

import public

class CleanupManager:
    def __init__(self, backup_manager, config_manager):
        self.backup_manager = backup_manager
        self.config_manager = config_manager
        self.base_path = '/www/backup/mysql_binlog_backup'
        self.log_file = os.path.join(self.base_path, 'cleanup.log')
        self.lock = threading.Lock()
        
        # 确保日志目录存在
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path, exist_ok=True)

    def cleanup_database_backups(self, database_name: str, keep_days: int) -> Dict[str, Any]:
        """清理指定数据库的备份文件"""
        try:
            self._write_log(f"开始清理数据库 {database_name} 的备份，保留 {keep_days} 天")
            
            # 获取所有备份并按时间排序
            all_backups = self.backup_manager.get_backup_files_list(database_name)
            if not all_backups:
                msg = f"数据库 {database_name} 没有备份文件"
                self._write_log(msg)
                return {"status": True, "msg": msg, "deleted_count": 0, "size_freed": 0}
            
            all_backups.sort(key=lambda x: x['backup_time'])
            
            # 计算保留截止时间
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=keep_days)
            cutoff_date_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')
            
            self._write_log(f"保留截止时间: {cutoff_date_str}")
            
            # 分析备份结构
            analysis = self._analyze_backup_structure(all_backups, cutoff_date_str)
            
            # 确保备份链完整性
            if not analysis['full_backups']:
                msg = f"数据库 {database_name} 没有全量备份，跳过清理"
                self._write_log(msg, 'warning')
                return {"status": True, "msg": msg, "deleted_count": 0, "size_freed": 0}
            
            # 确定可以删除的备份
            can_delete = self._determine_deletable_backups(analysis)
            
            # 执行删除
            result = self._execute_cleanup(can_delete, database_name)
            
            self._write_log(f"数据库 {database_name} 清理完成: {result['msg']}")
            
            return result
            
        except Exception as e:
            error_msg = f"清理数据库 {database_name} 备份失败: {str(e)}"
            self._write_log(error_msg, 'error')
            return {"status": False, "msg": error_msg, "deleted_count": 0, "size_freed": 0}

    def cleanup_all_backups(self, override_keep_days: Optional[int] = None) -> Dict[str, Any]:
        """清理所有数据库的备份"""
        try:
            self._write_log("开始清理所有数据库的备份")
            
            all_tasks = self.config_manager.get_backup_task_list()
            if not all_tasks:
                msg = "没有找到备份任务"
                self._write_log(msg, 'warning')
                return {"status": True, "msg": msg, "total_deleted": 0, "total_size_freed": 0, "databases": []}
            
            total_deleted = 0
            total_size_freed = 0
            cleanup_results = []
            
            for task in all_tasks:
                db_name = task['database_name']
                keep_days = override_keep_days or task.get('keep_days', 30)
                
                result = self.cleanup_database_backups(db_name, keep_days)
                if result['status']:
                    total_deleted += result['deleted_count']
                    total_size_freed += result['size_freed']
                    cleanup_results.append({
                        'database': db_name,
                        'keep_days': keep_days,
                        'deleted_count': result['deleted_count'],
                        'size_freed': result['size_freed'],
                        'formatted_size_freed': self._format_size(result['size_freed'])
                    })
                else:
                    self._write_log(f"清理数据库 {db_name} 失败: {result['msg']}", 'error')
            
            summary = {
                'total_deleted': total_deleted,
                'total_size_freed': total_size_freed,
                'formatted_size_freed': self._format_size(total_size_freed),
                'databases': cleanup_results
            }
            
            msg = f"所有数据库清理完成，共删除 {total_deleted} 个备份，释放 {summary['formatted_size_freed']} 空间"
            self._write_log(msg)
            
            return {"status": True, "msg": msg, "data": summary}
            
        except Exception as e:
            error_msg = f"清理所有备份失败: {str(e)}"
            self._write_log(error_msg, 'error')
            return {"status": False, "msg": error_msg}

    def _analyze_backup_structure(self, all_backups: List[Dict], cutoff_date_str: str) -> Dict[str, Any]:
        """分析备份结构"""
        analysis = {
            'recent_backups': [],     # 最近N天的备份（全部保留）
            'old_backups': [],        # 超过N天的备份（需要智能判断）
            'full_backups': [],       # 所有全量备份
            'incremental_backups': [] # 所有增量备份
        }
        
        for backup in all_backups:
            # 按时间分类
            if backup['backup_time'] >= cutoff_date_str:
                analysis['recent_backups'].append(backup)
            else:
                analysis['old_backups'].append(backup)
            
            # 按类型分类
            if backup['backup_type'] == 'full':
                analysis['full_backups'].append(backup)
            else:
                analysis['incremental_backups'].append(backup)
        
        # 按时间排序
        analysis['full_backups'].sort(key=lambda x: x['backup_time'])
        analysis['incremental_backups'].sort(key=lambda x: x['backup_time'])
        
        return analysis

    def _determine_deletable_backups(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """确定可以删除的备份（智能策略）"""
        can_delete = []
        
        # 找到最新的全量备份
        latest_full_backup = max(analysis['full_backups'], key=lambda x: x['backup_time'])
        
        self._write_log(f"最新全量备份: {latest_full_backup['backup_id']} ({latest_full_backup['backup_time']})")
        
        # 处理旧的备份
        for backup in analysis['old_backups']:
            if backup['backup_type'] == 'incremental':
                # 增量备份：如果有更新的全量备份，可以删除
                if backup['backup_time'] < latest_full_backup['backup_time']:
                    can_delete.append(backup)
                    self._write_log(f"可删除增量备份: {backup['backup_id']} (有更新的全量备份)")
                else:
                    self._write_log(f"保留增量备份: {backup['backup_id']} (依赖最新全量备份)")
            
            elif backup['backup_type'] == 'full':
                # 全量备份：如果不是最新的，可以删除
                if backup['backup_id'] != latest_full_backup['backup_id']:
                    can_delete.append(backup)
                    self._write_log(f"可删除旧全量备份: {backup['backup_id']}")
                    
                    # 找到依赖此全量备份的增量备份
                    dependent_incrementals = self._find_dependent_incrementals(
                        backup, analysis['incremental_backups'], analysis['full_backups']
                    )
                    can_delete.extend(dependent_incrementals)
                    
                    for dep in dependent_incrementals:
                        self._write_log(f"可删除依赖增量备份: {dep['backup_id']} (依赖已删除的全量备份)")
                else:
                    self._write_log(f"保留最新全量备份: {backup['backup_id']}")
        
        return can_delete

    def _find_dependent_incrementals(self, full_backup: Dict, all_incrementals: List[Dict], 
                                   all_full_backups: List[Dict]) -> List[Dict[str, Any]]:
        """找到依赖指定全量备份的增量备份"""
        dependent = []
        full_backup_time = full_backup['backup_time']
        
        # 找到下一个全量备份的时间
        next_full_time = None
        for backup in all_full_backups:
            if backup['backup_time'] > full_backup_time:
                if not next_full_time or backup['backup_time'] < next_full_time:
                    next_full_time = backup['backup_time']
        
        # 找到在此时间范围内的增量备份
        for backup in all_incrementals:
            backup_time = backup['backup_time']
            if backup_time > full_backup_time:
                if not next_full_time or backup_time < next_full_time:
                    dependent.append(backup)
        
        return dependent

    def _execute_cleanup(self, can_delete: List[Dict], database_name: str) -> Dict[str, Any]:
        """执行实际的删除操作"""
        deleted_count = 0
        total_size_freed = 0
        failed_deletes = []
        
        for backup in can_delete:
            try:
                result = self.backup_manager.delete_backup_file(backup['backup_id'])
                if result['status']:
                    deleted_count += 1
                    total_size_freed += backup['file_size']
                    self._write_log(f"已删除备份: {backup['backup_id']} ({self._format_size(backup['file_size'])})")
                else:
                    failed_deletes.append(backup['backup_id'])
                    self._write_log(f"删除失败: {backup['backup_id']} - {result['msg']}", 'error')
            except Exception as e:
                failed_deletes.append(backup['backup_id'])
                self._write_log(f"删除异常: {backup['backup_id']} - {str(e)}", 'error')
        
        msg = f"数据库 {database_name} 清理完成，删除 {deleted_count} 个备份，释放 {self._format_size(total_size_freed)} 空间"
        if failed_deletes:
            msg += f"，{len(failed_deletes)} 个备份删除失败"
        
        return {
            "status": True,
            "msg": msg,
            "deleted_count": deleted_count,
            "size_freed": total_size_freed,
            "failed_deletes": failed_deletes
        }

    def get_cleanup_preview(self, database_name: str, keep_days: int) -> Dict[str, Any]:
        """预览清理效果（不实际删除）"""
        try:
            # 获取所有备份
            all_backups = self.backup_manager.get_backup_files_list(database_name)
            if not all_backups:
                return {"status": True, "msg": "没有备份文件", "preview": {"will_delete": [], "will_keep": []}}
            
            all_backups.sort(key=lambda x: x['backup_time'])
            
            # 计算保留截止时间
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=keep_days)
            cutoff_date_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')
            
            # 分析备份结构
            analysis = self._analyze_backup_structure(all_backups, cutoff_date_str)
            
            if not analysis['full_backups']:
                return {"status": True, "msg": "没有全量备份", "preview": {"will_delete": [], "will_keep": all_backups}}
            
            # 确定可以删除的备份
            can_delete = self._determine_deletable_backups(analysis)
            will_keep = [b for b in all_backups if b not in can_delete]
            
            # 统计信息
            delete_size = sum(b['file_size'] for b in can_delete)
            keep_size = sum(b['file_size'] for b in will_keep)
            
            preview = {
                "will_delete": [{
                    "backup_id": b['backup_id'],
                    "backup_type": b['backup_type'],
                    "backup_time": b['backup_time'],
                    "file_size": b['file_size'],
                    "formatted_size": self._format_size(b['file_size'])
                } for b in can_delete],
                "will_keep": [{
                    "backup_id": b['backup_id'],
                    "backup_type": b['backup_type'],
                    "backup_time": b['backup_time'],
                    "file_size": b['file_size'],
                    "formatted_size": self._format_size(b['file_size'])
                } for b in will_keep],
                "summary": {
                    "total_backups": len(all_backups),
                    "will_delete_count": len(can_delete),
                    "will_keep_count": len(will_keep),
                    "delete_size": delete_size,
                    "keep_size": keep_size,
                    "formatted_delete_size": self._format_size(delete_size),
                    "formatted_keep_size": self._format_size(keep_size),
                    "cutoff_date": cutoff_date_str
                }
            }
            
            return {"status": True, "msg": "预览生成成功", "preview": preview}
            
        except Exception as e:
            return {"status": False, "msg": f"生成预览失败: {str(e)}"}

    def get_cleanup_logs(self, limit: int = 100) -> List[str]:
        """获取清理日志"""
        try:
            if not os.path.exists(self.log_file):
                return []
            
            logs = []
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 返回最新的日志
            for line in reversed(lines[-limit:]):
                line = line.strip()
                if line:
                    logs.append(line)
            
            return logs
            
        except Exception as e:
            return [f"获取清理日志失败: {str(e)}"]

    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.2f} {size_names[i]}"

    def _write_log(self, message: str, level: str = 'info'):
        """写入清理日志"""
        try:
            with self.lock:
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                log_message = f"[{timestamp}] [{level.upper()}] {message}\n"
                
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(log_message)
                
                # 同时输出到控制台
                print(log_message.strip())
                
        except Exception as e:
            print(f"写入清理日志失败: {e}")

if __name__ == '__main__':
    # 测试代码
    print("CleanupManager 清理管理模块已创建") 