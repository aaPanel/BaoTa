#!/usr/bin/env python3
# coding: utf-8
# -------------------------------------------------------------------
# MySQL Binlog增量备份系统 - 任务调度脚本
# -------------------------------------------------------------------
# Author: miku <miku@bt.cn>
# -------------------------------------------------------------------

import json
import os
import sys
import time
import datetime
import threading

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

if '/www/server/panel' not in sys.path:
    sys.path.insert(0, '/www/server/panel')

import public
from mod.project.mysql_binlog_backup.config_manager import ConfigManager
from mod.project.mysql_binlog_backup.backup_manager import BackupManager

class TaskScheduler:
    def __init__(self):
        self.base_path = '/www/backup/mysql_binlog_backup'
        self.lock_file = os.path.join(self.base_path, 'scheduler.lock')
        self.log_file = os.path.join(self.base_path, 'scheduler.log')
        
        self.config_manager = ConfigManager()
        self.backup_manager = BackupManager()
        
        # 确保目录存在
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path, exist_ok=True)

    def run(self):
        """主执行函数"""
        try:
            # 检查是否已有调度器在运行
            if self._is_running():
                self._write_log("调度器已在运行中，跳过本次执行")
                return
            
            # 创建锁文件
            self._create_lock()
            
            try:
                self._write_log("开始执行备份任务检查")
                
                # 检查binlog是否可用
                if not self.backup_manager.check_binlog_enabled():
                    self._write_log("MySQL binlog未开启，跳过备份任务", 'warning')
                    return
                
                # 获取待执行的任务
                pending_tasks = self.config_manager.get_pending_tasks()
                
                if not pending_tasks:
                    self._write_log("没有待执行的备份任务")
                    return
                
                self._write_log(f"发现 {len(pending_tasks)} 个待执行的备份任务")
                
                # 执行待执行的任务
                for task in pending_tasks:
                    self._execute_backup_task(task)
                
                self._write_log("备份任务检查完成")
                
            finally:
                # 删除锁文件
                self._remove_lock()
                
        except Exception as e:
            self._write_log(f"执行备份任务检查时发生错误: {str(e)}", 'error')
            self._remove_lock()

    def _execute_backup_task(self, task: dict):
        """执行单个备份任务"""
        try:
            database_name = task['database_name']
            backup_type = task['backup_type']
            config = task['config']
            
            db_data = public.M('databases').where("name=? AND sid=0 AND LOWER(type)=LOWER('mysql')", database_name).select()
            if not db_data:
                self._write_log(f"数据库 {database_name} 不存在，请检查是否已删除此数据，当前已跳过备份", 'warning')
                return
                
            self._write_log(f"开始执行 {database_name} 的 {backup_type} 备份")
            
            # 设置任务运行状态
            self.config_manager.set_task_running_status(database_name, True)
            
            try:
                if backup_type == 'full':
                    result = self._execute_full_backup(database_name, config)
                elif backup_type == 'incremental':
                    result = self._execute_incremental_backup(database_name, config)
                else:
                    result = {"status": False, "msg": f"未知的备份类型: {backup_type}"}
                
                if result['status']:
                    # 更新配置中的执行时间
                    self.config_manager.update_backup_execution_time(database_name, backup_type)
                    self._write_log(f"{database_name} 的 {backup_type} 备份执行成功")
                else:
                    self._write_log(f"{database_name} 的 {backup_type} 备份执行失败: {result['msg']}", 'error')
                    
            finally:
                # 取消任务运行状态
                self.config_manager.set_task_running_status(database_name, False)
                
        except Exception as e:
            error_msg = f"执行备份任务失败: {str(e)}"
            self._write_log(error_msg, 'error')
            # 确保取消运行状态
            try:
                self.config_manager.set_task_running_status(database_name, False)
            except:
                pass

    def _execute_full_backup(self, database_name: str, config: dict) -> dict:
        """执行全量备份"""
        try:
            self._write_log(f"执行 {database_name} 的全量备份")
            
            # 调用备份管理器执行全量备份
            result = self.backup_manager.mysqldump_full_backup(database_name)
            
            if result['status']:
                backup_info = result['data']
                file_size = self.backup_manager._format_size(backup_info['file_size'])
                self._write_log(f"{database_name} 全量备份完成，文件大小: {file_size}")
            
            return result
            
        except Exception as e:
            return {"status": False, "msg": f"全量备份异常: {str(e)}"}

    def _execute_incremental_backup(self, database_name: str, config: dict) -> dict:
        """执行增量备份"""
        try:
            self._write_log(f"执行 {database_name} 的增量备份")
            
            # 调用备份管理器执行增量备份
            result = self.backup_manager.binlog_incremental_backup(database_name)
            
            if result['status']:
                backup_info = result['data']
                file_size = self.backup_manager._format_size(backup_info['file_size'])
                self._write_log(f"{database_name} 增量备份完成，文件大小: {file_size}")
            
            return result
            
        except Exception as e:
            return {"status": False, "msg": f"增量备份异常: {str(e)}"}

    def _is_running(self) -> bool:
        """检查调度器是否正在运行"""
        if not os.path.exists(self.lock_file):
            return False
        
        try:
            # 检查锁文件的创建时间，如果超过5分钟则认为是僵尸锁
            lock_time = os.path.getmtime(self.lock_file)
            current_time = time.time()
            
            # 如果锁文件超过5分钟，删除它
            if current_time - lock_time > 300:  # 5分钟
                self._write_log("发现僵尸锁文件，删除它", 'warning')
                os.remove(self.lock_file)
                return False
            
            # 读取锁文件中的PID
            with open(self.lock_file, 'r') as f:
                pid = f.read().strip()
            
            # 检查进程是否还在运行
            if pid.isdigit():
                try:
                    os.kill(int(pid), 0)  # 不发送信号，只检查进程是否存在
                    return True
                except OSError:
                    # 进程不存在，删除锁文件
                    os.remove(self.lock_file)
                    return False
            
            return True
            
        except Exception as e:
            self._write_log(f"检查锁文件状态失败: {e}", 'warning')
            return False

    def _create_lock(self):
        """创建锁文件"""
        try:
            with open(self.lock_file, 'w') as f:
                f.write(str(os.getpid()))
        except Exception as e:
            self._write_log(f"创建锁文件失败: {e}", 'error')

    def _remove_lock(self):
        """删除锁文件"""
        try:
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)
        except Exception as e:
            self._write_log(f"删除锁文件失败: {e}", 'error')

    def _write_log(self, message: str, level: str = 'info'):
        """写入日志"""
        try:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_message = f"[{timestamp}] [SCHEDULER] [{level.upper()}] {message}\n"
            
            # 写入日志文件
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_message)
            
            # 同时输出到控制台
            print(log_message.strip())
            
            # 保持日志文件大小合理，只保留最近1000行
            self._rotate_log_file()
            
        except Exception as e:
            print(f"写入调度器日志失败: {e}")

    def _rotate_log_file(self):
        """轮转日志文件"""
        try:
            if not os.path.exists(self.log_file):
                return
            
            # 检查文件大小，如果超过10MB则进行轮转
            file_size = os.path.getsize(self.log_file)
            if file_size > 10 * 1024 * 1024:  # 10MB
                
                # 读取最后1000行
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                if len(lines) > 1000:
                    # 保留最后1000行
                    with open(self.log_file, 'w', encoding='utf-8') as f:
                        f.writelines(lines[-1000:])
                    
                    self._write_log("日志文件已轮转，保留最近1000行记录")
                    
        except Exception as e:
            print(f"轮转日志文件失败: {e}")

class ManualBackupRunner:
    """手动备份执行器"""
    
    def __init__(self):
        self.backup_manager = BackupManager()
        self.config_manager = ConfigManager()
    
    def run_manual_backup(self, database_name: str, backup_type: str):
        """手动执行备份"""
        try:
            print(f"开始手动执行 {database_name} 的 {backup_type} 备份")
            
            if backup_type == 'full':
                result = self.backup_manager.mysqldump_full_backup(database_name)
            elif backup_type == 'incremental':
                result = self.backup_manager.binlog_incremental_backup(database_name)
            else:
                result = {"status": False, "msg": f"未知的备份类型: {backup_type}"}
            
            if result['status']:
                print(f"{backup_type} 备份执行成功")
                if 'data' in result:
                    backup_info = result['data']
                    file_size = self.backup_manager._format_size(backup_info['file_size'])
                    print(f"备份文件大小: {file_size}")
                    print(f"备份文件路径: {backup_info['file_path']}")
            else:
                print(f"{backup_type} 备份执行失败: {result['msg']}")
            
            return result
            
        except Exception as e:
            error_msg = f"手动备份失败: {str(e)}"
            print(error_msg)
            return {"status": False, "msg": error_msg}

def main():
    """主函数"""
    if len(sys.argv) > 1:
        action = sys.argv[1]
        
        if action == 'manual' and len(sys.argv) >= 4:
            # 手动执行备份
            database_name = sys.argv[2]
            backup_type = sys.argv[3]
            
            runner = ManualBackupRunner()
            result = runner.run_manual_backup(database_name, backup_type)
            
            exit_code = 0 if result['status'] else 1
            sys.exit(exit_code)
            
        elif action == 'status':
            # 显示系统状态
            config_manager = ConfigManager()
            backup_manager = BackupManager()
            
            print("=== MySQL Binlog 备份系统状态 ===")
            print(f"Binlog状态: {'开启' if backup_manager.check_binlog_enabled() else '关闭'}")
            
            tasks = config_manager.get_backup_task_list()
            print(f"配置任务数: {len(tasks)}")
            
            backup_status = backup_manager.get_backup_status()
            print(f"总备份文件数: {backup_status.get('total_backups', 0)}")
            print(f"磁盘使用: {backup_status.get('disk_usage', {}).get('formatted_size', '0 B')}")
            
            if tasks:
                print("\n任务列表:")
                for task in tasks:
                    print(f"  - {task['database_name']}: {task['status']} "
                          f"(全量:{task['full_backup_interval']}h, 增量:{task['incremental_backup_interval']}min)")
            
        elif action == 'help':
            print("MySQL Binlog 备份系统 - 任务调度器")
            print("")
            print("用法:")
            print("  btpython task_scheduler.py              # 执行定时任务检查")
            print("  btpython task_scheduler.py manual <db_name> <full|incremental>  # 手动执行备份")
            print("  btpython task_scheduler.py status       # 显示系统状态")
            print("  btpython task_scheduler.py help         # 显示帮助信息")
            print("")
            print("示例:")
            print("  btpython task_scheduler.py manual mydb full")
            print("  btpython task_scheduler.py manual mydb incremental")
            
        else:
            print("未知操作，使用 'help' 查看帮助信息")
            sys.exit(1)
    else:
        # 默认执行定时任务检查
        scheduler = TaskScheduler()
        scheduler.run()

if __name__ == '__main__':
    main() 