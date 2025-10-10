# coding: utf-8
# -------------------------------------------------------------------
# MySQL Binlog增量备份系统 - 还原管理模块
# -------------------------------------------------------------------
# Author: miku <miku@bt.cn>
# -------------------------------------------------------------------

import json
import os
import sys
import time
import datetime
import threading
import uuid
from typing import Dict, List, Any, Optional

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

if '/www/server/panel' not in sys.path:
    sys.path.insert(0, '/www/server/panel')

import public
import panelMysql
import db_mysql

class RestoreManager:
    def __init__(self):
        self.base_path = '/www/backup/mysql_binlog_backup'
        self.backup_path = os.path.join(self.base_path, 'backups')
        self.restore_path = os.path.join(self.base_path, 'restore')
        self.log_file = os.path.join(self.base_path, 'restore.log')
        self.lock = threading.Lock()
        
        # MySQL工具路径
        self._MYSQL_BIN = public.get_mysql_bin()
        
        # 确保还原目录存在
        if not os.path.exists(self.restore_path):
            os.makedirs(self.restore_path, exist_ok=True)

    def start_restore_task(self, database_name: str, restore_time: str) -> Dict[str, Any]:
        """启动还原任务"""
        try:
            # 参数验证
            try:
                restore_datetime = datetime.datetime.strptime(restore_time, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return {"status": False, "msg": "时间格式错误，请使用 YYYY-MM-DD HH:MM:SS 格式"}
            
            # 检查数据库是否存在
            db_info = public.M('databases').where('name=? AND type=?', (database_name, 'MySQL')).find()
            if not db_info:
                return {"status": False, "msg": "数据库不存在"}
            
            # 生成任务ID
            task_id = str(uuid.uuid4())
            
            # 创建还原任务信息
            task_info = {
                "task_id": task_id,
                "database_name": database_name,
                "restore_time": restore_time,
                "start_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "status": "preparing",
                "progress": 0,
                "message": "准备还原任务",
                "backup_files": [],
                "error": None
            }
            
            # 保存任务信息
            task_file = os.path.join(self.restore_path, f"{task_id}.json")
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(task_info, f, ensure_ascii=False, indent=2)
            
            # 在后台启动还原进程
            import threading
            restore_thread = threading.Thread(
                target=self._execute_restore_task,
                args=(task_id, database_name, restore_datetime)
            )
            restore_thread.daemon = True
            restore_thread.start()
            
            self._write_log(f"启动数据库 {database_name} 还原任务，目标时间: {restore_time}")
            
            return {"status": True, "msg": "还原任务已启动", "data": {"task_id": task_id}}
            
        except Exception as e:
            error_msg = f"启动还原任务失败: {str(e)}"
            self._write_log(error_msg, 'error')
            return {"status": False, "msg": error_msg}

    def _execute_restore_task(self, task_id: str, database_name: str, restore_datetime: datetime.datetime):
        """执行还原任务"""
        try:
            self._update_task_status(task_id, "analyzing", 10, "分析备份文件")
            
            # 获取需要的备份文件
            backup_plan = self._create_restore_plan(database_name, restore_datetime)
            if not backup_plan['status']:
                self._update_task_status(task_id, "failed", 0, backup_plan['msg'], backup_plan['msg'])
                return
            
            self._update_task_status(task_id, "restoring", 20, "开始还原数据")
            
            # 执行还原计划
            result = self._execute_restore_plan(task_id, database_name, backup_plan['data'], restore_datetime)
            
            if result['status']:
                self._update_task_status(task_id, "completed", 100, "还原完成")
                self._write_log(f"数据库 {database_name} 还原完成")
            else:
                self._update_task_status(task_id, "failed", 0, "还原失败", result['msg'])
                self._write_log(f"数据库 {database_name} 还原失败: {result['msg']}", 'error')
                
        except Exception as e:
            error_msg = f"执行还原任务失败: {str(e)}"
            self._update_task_status(task_id, "failed", 0, "还原失败", error_msg)
            self._write_log(error_msg, 'error')

    def _create_restore_plan(self, database_name: str, restore_datetime: datetime.datetime) -> Dict[str, Any]:
        """创建还原计划"""
        try:
            # 获取所有备份文件
            backup_files = self._get_backup_files(database_name)
            if not backup_files:
                return {"status": False, "msg": "没有找到备份文件"}
            
            # 查找基础全量备份
            base_full_backup = None
            incremental_backups = []
            
            for backup in backup_files:
                backup_time = datetime.datetime.strptime(backup['backup_time'], '%Y-%m-%d %H:%M:%S')
                
                # 只考虑还原时间点之前的备份
                if backup_time <= restore_datetime:
                    if backup['backup_type'] == 'full':
                        # 寻找最近的全量备份
                        if not base_full_backup or backup_time > datetime.datetime.strptime(base_full_backup['backup_time'], '%Y-%m-%d %H:%M:%S'):
                            base_full_backup = backup
                    elif backup['backup_type'] == 'incremental':
                        incremental_backups.append(backup)
            
            if not base_full_backup:
                return {"status": False, "msg": "没有找到适合的全量备份"}
            
            # 筛选需要的增量备份
            base_time = datetime.datetime.strptime(base_full_backup['backup_time'], '%Y-%m-%d %H:%M:%S')
            needed_incremental = []
            
            for backup in incremental_backups:
                backup_time = datetime.datetime.strptime(backup['backup_time'], '%Y-%m-%d %H:%M:%S')
                # 选择在全量备份之后，还原时间点之前的增量备份
                if base_time < backup_time <= restore_datetime:
                    needed_incremental.append(backup)
            
            # 按时间排序增量备份
            needed_incremental.sort(key=lambda x: x['backup_time'])
            
            restore_plan = {
                "base_backup": base_full_backup,
                "incremental_backups": needed_incremental,
                "total_files": 1 + len(needed_incremental)
            }
            
            return {"status": True, "data": restore_plan}
            
        except Exception as e:
            return {"status": False, "msg": f"创建还原计划失败: {str(e)}"}

    def _execute_restore_plan(self, task_id: str, database_name: str, restore_plan: Dict[str, Any], 
                             restore_datetime: datetime.datetime) -> Dict[str, Any]:
        """执行还原计划"""
        try:
            # 备份当前数据库
            backup_result = self._backup_current_database(database_name)
            if not backup_result['status']:
                return {"status": False, "msg": f"备份当前数据库失败: {backup_result['msg']}"}
            
            progress_step = 70 / restore_plan['total_files']  # 70%的进度用于还原
            current_progress = 20
            
            # 还原全量备份
            self._update_task_status(task_id, "restoring", current_progress, "还原全量备份")
            
            result = self._restore_full_backup(database_name, restore_plan['base_backup'])
            if not result['status']:
                return {"status": False, "msg": f"还原全量备份失败: {result['msg']}"}
            
            current_progress += progress_step
            
            # 依次还原增量备份
            for i, incremental_backup in enumerate(restore_plan['incremental_backups']):
                message = f"还原增量备份 {i+1}/{len(restore_plan['incremental_backups'])}"
                self._update_task_status(task_id, "restoring", current_progress, message)
                
                result = self._restore_incremental_backup(database_name, incremental_backup, restore_datetime)
                if not result['status']:
                    return {"status": False, "msg": f"还原增量备份失败: {result['msg']}"}
                
                current_progress += progress_step
            
            self._update_task_status(task_id, "finalizing", 90, "完成还原")
            
            return {"status": True, "msg": "还原完成"}
            
        except Exception as e:
            return {"status": False, "msg": f"执行还原计划失败: {str(e)}"}

    def _backup_current_database(self, database_name: str) -> Dict[str, Any]:
        """备份当前数据库（还原前的安全备份）"""
        try:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = os.path.join(self.restore_path, f"pre_restore_{database_name}_{timestamp}")
            os.makedirs(backup_dir, exist_ok=True)
            
            # 获取MySQL连接参数
            try:
                db_port = int(panelMysql.panelMysql().query("show global variables like 'port'")[0][1])
            except:
                db_port = 3306
                
            db_password = public.M("config").where("id=?", (1,)).getField("mysql_root")
            db_charset = public.get_database_character(database_name)
            
            # 使用mysqldump备份
            sql_file = os.path.join(backup_dir, f"{database_name}_pre_restore.sql")
            mysqldump_bin = public.get_mysqldump_bin()
            
            shell = f"'{mysqldump_bin}' --opt --single-transaction --routines --events " \
                   f"--default-character-set='{db_charset}' --force " \
                   f"--host='localhost' --port={db_port} --user='root' --password='{db_password}' '{database_name}'"
            
            shell += f" > '{sql_file}'"
            
            result = public.ExecShell(shell, env={"MYSQL_PWD": db_password})
            
            if not os.path.exists(sql_file) or os.path.getsize(sql_file) == 0:
                return {"status": False, "msg": f"备份失败: {result[1]}"}
            
            self._write_log(f"已创建还原前备份: {sql_file}")
            return {"status": True, "data": {"backup_file": sql_file}}
            
        except Exception as e:
            return {"status": False, "msg": f"创建还原前备份失败: {str(e)}"}

    def _restore_full_backup(self, database_name: str, full_backup: Dict[str, Any]) -> Dict[str, Any]:
        """还原全量备份"""
        try:
            sql_file = full_backup['file_path']
            
            if not os.path.exists(sql_file):
                return {"status": False, "msg": f"备份文件不存在: {sql_file}"}
            
            # 获取MySQL连接参数
            try:
                db_port = int(panelMysql.panelMysql().query("show global variables like 'port'")[0][1])
            except:
                db_port = 3306
                
            db_password = public.M("config").where("id=?", (1,)).getField("mysql_root")
            db_charset = public.get_database_character(database_name)
            
            # 构建mysql导入命令
            shell = f"'{self._MYSQL_BIN}' --force --default-character-set='{db_charset}' " \
                   f"--host='localhost' --port={db_port} --user='root' --password='{db_password}' '{database_name}'"
            
            shell += f" < '{sql_file}'"
            
            # 执行导入
            result = public.ExecShell(shell, env={"MYSQL_PWD": db_password})
            
            if "error:" in result[0].lower() or "error:" in result[1].lower():
                return {"status": False, "msg": f"导入失败: {result[0]} {result[1]}"}
            
            self._write_log(f"全量备份还原完成: {sql_file}")
            return {"status": True, "msg": "全量备份还原完成"}
            
        except Exception as e:
            return {"status": False, "msg": f"还原全量备份失败: {str(e)}"}

    def _restore_incremental_backup(self, database_name: str, incremental_backup: Dict[str, Any], 
                                   stop_datetime: datetime.datetime) -> Dict[str, Any]:
        """还原增量备份"""
        try:
            sql_file = incremental_backup['file_path']
            
            if not os.path.exists(sql_file):
                return {"status": False, "msg": f"增量备份文件不存在: {sql_file}"}
            
            # 获取MySQL连接参数
            try:
                db_port = int(panelMysql.panelMysql().query("show global variables like 'port'")[0][1])
            except:
                db_port = 3306
                
            db_password = public.M("config").where("id=?", (1,)).getField("mysql_root")
            
            # 如果需要精确到时间点，重新生成binlog SQL
            backup_end_time = datetime.datetime.strptime(incremental_backup.get('end_time', incremental_backup['backup_time']), '%Y-%m-%d %H:%M:%S')
            
            if stop_datetime < backup_end_time:
                # 需要重新生成到指定时间点的binlog
                temp_sql_file = self._generate_point_in_time_sql(incremental_backup, stop_datetime)
                if temp_sql_file:
                    sql_file = temp_sql_file
                else:
                    return {"status": False, "msg": "生成时间点SQL失败"}
            
            # 构建mysql导入命令
            shell = f"'{self._MYSQL_BIN}' --force --host='localhost' --port={db_port} " \
                   f"--user='root' --password='{db_password}' '{database_name}'"
            
            shell += f" < '{sql_file}'"
            
            # 执行导入
            result = public.ExecShell(shell, env={"MYSQL_PWD": db_password})
            
            if "error:" in result[0].lower() or "error:" in result[1].lower():
                return {"status": False, "msg": f"导入增量备份失败: {result[0]} {result[1]}"}
            
            self._write_log(f"增量备份还原完成: {sql_file}")
            return {"status": True, "msg": "增量备份还原完成"}
            
        except Exception as e:
            return {"status": False, "msg": f"还原增量备份失败: {str(e)}"}

    def _generate_point_in_time_sql(self, incremental_backup: Dict[str, Any], 
                                   stop_datetime: datetime.datetime) -> Optional[str]:
        """生成指定时间点的binlog SQL"""
        try:
            # 从增量备份信息中获取binlog文件信息
            binlog_files = incremental_backup.get('binlog_files', [])
            if not binlog_files:
                return None
            
            # 获取binlog目录
            mysql_obj = db_mysql.panelMysql()
            log_bin_result = mysql_obj.query("SHOW VARIABLES LIKE 'log_bin_basename'")
            if log_bin_result:
                log_bin_basename = log_bin_result[0][1]
                binlog_dir = os.path.dirname(log_bin_basename)
            else:
                binlog_dir = '/www/server/data'
            
            # 生成临时SQL文件
            temp_sql_file = os.path.join(self.restore_path, f"temp_pit_{int(time.time())}.sql")
            
            # 构建mysqlbinlog命令
            mysqlbinlog_bin = '/usr/bin/mysqlbinlog'
            binlog_paths = [os.path.join(binlog_dir, f) for f in binlog_files]
            
            start_time_str = incremental_backup.get('start_time', incremental_backup['backup_time'])
            stop_time_str = stop_datetime.strftime('%Y-%m-%d %H:%M:%S')
            
            shell = f"'{mysqlbinlog_bin}' --database='{incremental_backup['database_name']}' " \
                   f"--start-datetime='{start_time_str}' --stop-datetime='{stop_time_str}' "
            
            shell += ' '.join(f"'{path}'" for path in binlog_paths)
            shell += f" > '{temp_sql_file}'"
            
            result = public.ExecShell(shell)
            
            if os.path.exists(temp_sql_file) and os.path.getsize(temp_sql_file) > 0:
                return temp_sql_file
            else:
                return None
                
        except Exception as e:
            self._write_log(f"生成时间点SQL失败: {e}", 'error')
            return None

    def _get_backup_files(self, database_name: str) -> List[Dict[str, Any]]:
        """获取数据库的所有备份文件"""
        try:
            backup_files = []
            database_backup_dir = os.path.join(self.backup_path, database_name)
            
            if not os.path.exists(database_backup_dir):
                return []
            
            # 遍历日期目录
            for date_dir in os.listdir(database_backup_dir):
                date_path = os.path.join(database_backup_dir, date_dir)
                if not os.path.isdir(date_path):
                    continue
                
                # 遍历该日期下的备份目录
                for backup_dir in os.listdir(date_path):
                    backup_path = os.path.join(date_path, backup_dir)
                    if not os.path.isdir(backup_path):
                        continue
                    
                    info_file = os.path.join(backup_path, 'backup_info.json')
                    if os.path.exists(info_file):
                        with open(info_file, 'r', encoding='utf-8') as f:
                            backup_info = json.load(f)
                            backup_files.append(backup_info)
            
            # 按备份时间排序
            backup_files.sort(key=lambda x: x['backup_time'])
            return backup_files
            
        except Exception as e:
            self._write_log(f"获取备份文件失败: {e}", 'error')
            return []

    def _update_task_status(self, task_id: str, status: str, progress: int, message: str, error: str = None):
        """更新任务状态"""
        try:
            task_file = os.path.join(self.restore_path, f"{task_id}.json")
            if os.path.exists(task_file):
                with open(task_file, 'r', encoding='utf-8') as f:
                    task_info = json.load(f)
                
                task_info['status'] = status
                task_info['progress'] = progress
                task_info['message'] = message
                task_info['update_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                if error:
                    task_info['error'] = error
                
                with open(task_file, 'w', encoding='utf-8') as f:
                    json.dump(task_info, f, ensure_ascii=False, indent=2)
                    
        except Exception as e:
            self._write_log(f"更新任务状态失败: {e}", 'error')

    def get_restore_progress(self, task_id: str = None) -> Dict[str, Any]:
        """获取还原进度"""
        try:
            if task_id:
                # 获取指定任务的进度
                task_file = os.path.join(self.restore_path, f"{task_id}.json")
                if os.path.exists(task_file):
                    with open(task_file, 'r', encoding='utf-8') as f:
                        info = json.load(f)
                        info['progress'] = int(info['progress'])
                        return info
                else:
                    return {"status": "not_found", "msg": "任务不存在"}
            else:
                # 获取所有任务的状态
                tasks = []
                if os.path.exists(self.restore_path):
                    for file in os.listdir(self.restore_path):
                        if file.endswith('.json'):
                            task_file = os.path.join(self.restore_path, file)
                            with open(task_file, 'r', encoding='utf-8') as f:
                                task_info = json.load(f)
                                tasks.append(task_info)
                
                # 按开始时间排序
                tasks.sort(key=lambda x: x.get('start_time', ''), reverse=True)
                return {"tasks": tasks}
                
        except Exception as e:
            return {"status": "error", "msg": f"获取还原进度失败: {str(e)}"}

    def _write_log(self, message: str, level: str = 'info'):
        """写入日志"""
        try:
            with self.lock:
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                log_message = f"[{timestamp}] [{level.upper()}] {message}\n"
                
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(log_message)
                
                # 同时输出到控制台
                print(log_message.strip())
                
        except Exception as e:
            print(f"写入日志失败: {e}")

if __name__ == '__main__':
    # 测试代码
    restore_manager = RestoreManager()
    
    if len(sys.argv) > 3:
        action = sys.argv[1]
        database_name = sys.argv[2]
        restore_time = sys.argv[3]
        
        if action == 'restore':
            result = restore_manager.start_restore_task(database_name, restore_time)
            print("还原结果:", result)
        elif action == 'progress' and len(sys.argv) > 4:
            task_id = sys.argv[4]
            progress = restore_manager.get_restore_progress(task_id)
            print("还原进度:", progress) 