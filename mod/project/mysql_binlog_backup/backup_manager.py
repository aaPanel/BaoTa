# coding: utf-8
# -------------------------------------------------------------------
# MySQL Binlog增量备份系统 - 备份管理模块
# -------------------------------------------------------------------
# Author: miku <miku@bt.cn>
# -------------------------------------------------------------------

import json
import os
import sys
import time
import datetime
import re
import shutil
import hashlib
import threading
from typing import Dict, List, Any, Optional

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

if '/www/server/panel' not in sys.path:
    sys.path.insert(0, '/www/server/panel')

import public
import panelMysql
import db_mysql

class BackupManager:
    def __init__(self):
        self.base_path = '/www/backup/mysql_binlog_backup'
        self.backup_path = os.path.join(self.base_path, 'backups')
        self.log_file = os.path.join(self.base_path, 'backup.log')
        self.lock = threading.Lock()
        
        # MySQL工具路径
        self._MYSQLDUMP_BIN = public.get_mysqldump_bin()
        self._MYSQL_BIN = public.get_mysql_bin()
        self._MYSQLBINLOG_BIN = '/www/server/mysql/bin/mysqlbinlog'
        
        # 确保备份目录存在
        if not os.path.exists(self.backup_path):
            os.makedirs(self.backup_path, exist_ok=True)

    def disk_free_check(self):
        try:
            total, used, free = shutil.disk_usage(self.base_path)
            
            # 1GB = 1024 * 1024 * 1024 字节
            min_free_space = 1024 * 1024 * 1024 # 1GB
            
            # free_gb = free / (1024 * 1024 * 1024)
            # total_gb = total / (1024 * 1024 * 1024)
            # used_gb = used / (1024 * 1024 * 1024)
            
            if free >= min_free_space:
                return True
            else:
                return False
                
        except Exception as e:
            return False

    def check_binlog_enabled(self) -> bool:
        """检查MySQL binlog是否开启"""
        try:
            mysql_obj = db_mysql.panelMysql()
            result = mysql_obj.query("SHOW VARIABLES LIKE 'log_bin'")
            if result and len(result) > 0:
                return result[0][1].lower() in ['on', '1', 'true']
            return False
        except Exception as e:
            self._write_log(f"检查binlog状态失败: {e}", 'error')
            return False

    def get_mysql_binlog_info(self) -> Dict[str, Any]:
        """获取MySQL binlog信息"""
        try:
            mysql_obj = db_mysql.panelMysql()
            
            # 获取当前binlog文件和位置
            status_result = mysql_obj.query("SHOW MASTER STATUS")
            if not status_result:
                return {"status": False, "msg": "无法获取binlog状态"}
            
            binlog_file = status_result[0][0]
            binlog_position = status_result[0][1]
            
            # 获取binlog文件列表
            binlog_list = mysql_obj.query("SHOW BINARY LOGS")
            
            # 获取binlog路径
            log_bin_result = mysql_obj.query("SHOW VARIABLES LIKE 'log_bin_basename'")
            if log_bin_result:
                log_bin_basename = log_bin_result[0][1]
                binlog_dir = os.path.dirname(log_bin_basename)
            else:
                binlog_dir = '/www/server/data'
            
            return {
                "status": True,
                "current_file": binlog_file,
                "current_position": binlog_position,
                "binlog_list": [item[0] for item in binlog_list] if binlog_list else [],
                "binlog_dir": binlog_dir
            }
            
        except Exception as e:
            return {"status": False, "msg": f"获取binlog信息失败: {str(e)}"}

    def mysqldump_full_backup(self, database_name: str) -> Dict[str, Any]:
        """执行MySQL全量备份"""
        try:
            self._write_log(f"开始执行数据库 {database_name} 的全量备份")
            
            # 获取数据库连接信息
            db_info = public.M('databases').where('name=? AND type=?', (database_name, 'MySQL')).find()
            if not db_info:
                return {"status": False, "msg": "数据库不存在"}
            
            # 获取MySQL连接参数
            try:
                db_port = int(panelMysql.panelMysql().query("show global variables like 'port'")[0][1])
            except:
                db_port = 3306
                
            db_password = public.M("config").where("id=?", (1,)).getField("mysql_root")
            db_charset = public.get_database_character(database_name)
            
            # 记录备份开始时间和binlog位置
            backup_start_time = datetime.datetime.now()
            binlog_info = self.get_mysql_binlog_info()
            if not binlog_info['status']:
                return {"status": False, "msg": "无法获取binlog信息"}
            
            # 创建备份目录 - 按日期分组存储
            date_str = backup_start_time.strftime('%Y-%m-%d')
            time_str = backup_start_time.strftime('%H%M%S')
            backup_folder = f"{time_str}_full"
            backup_dir = os.path.join(self.backup_path, database_name, date_str, backup_folder)
            os.makedirs(backup_dir, exist_ok=True)
            
            # 设置备份文件路径
            sql_file = os.path.join(backup_dir, f"{database_name}_full.sql")
            
            # 构建mysqldump命令
            set_gtid_purged = ""
            resp = public.ExecShell(f"{self._MYSQLDUMP_BIN} --help | grep set-gtid-purged")[0]
            if resp.find("--set-gtid-purged") != -1:
                set_gtid_purged = "--set-gtid-purged=OFF"
                
            shell = f"'{self._MYSQLDUMP_BIN}' {set_gtid_purged} --opt --single-transaction --routines --events " \
                   f"--master-data=2 --default-character-set='{db_charset}' --force " \
                   f"--host='localhost' --port={db_port} --user='root' --password='{db_password}' '{database_name}'"
            
            shell += f" > '{sql_file}'"
            
            # 执行备份
            result = public.ExecShell(shell, env={"MYSQL_PWD": db_password})
            
            if not os.path.exists(sql_file) or os.path.getsize(sql_file) == 0:
                return {"status": False, "msg": f"备份失败: {result[1]}"}
            
            # 计算文件哈希
            file_hash = self._calculate_file_hash(sql_file)
            file_size = os.path.getsize(sql_file)
            
            # 保存备份信息
            backup_info = {
                "backup_id": f"{database_name}_{date_str}_{time_str}_full",
                "database_name": database_name,
                "backup_type": "full",
                "backup_time": backup_start_time.strftime('%Y-%m-%d %H:%M:%S'),
                "backup_date": date_str,
                "backup_folder": backup_folder,
                "file_path": sql_file,
                "file_size": file_size,
                "file_hash": file_hash,
                "binlog_file": binlog_info['current_file'],
                "binlog_position": binlog_info['current_position'],
                "status": "completed"
            }
            
            # 保存备份信息到文件
            info_file = os.path.join(backup_dir, 'backup_info.json')
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, ensure_ascii=False, indent=2)
            
            self._write_log(f"数据库 {database_name} 全量备份完成，文件大小: {self._format_size(file_size)}")
            
            return {"status": True, "msg": "全量备份完成", "data": backup_info}
            
        except Exception as e:
            error_msg = f"全量备份失败: {str(e)}"
            self._write_log(error_msg, 'error')
            return {"status": False, "msg": error_msg}

    def binlog_incremental_backup(self, database_name: str, start_time: str = None) -> Dict[str, Any]:
        """执行binlog增量备份"""
        try:
            self._write_log(f"开始执行数据库 {database_name} 的增量备份")
            
            # 获取最后一次备份信息
            last_backup = self._get_last_backup_info(database_name)
            if not last_backup:
                return {"status": False, "msg": "没有找到全量备份，请先执行全量备份"}
            
            # 确定起始时间和binlog位置
            if start_time:
                start_datetime = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            else:
                # 使用最后一次备份的时间
                if last_backup['backup_type'] == 'full':
                    start_datetime = datetime.datetime.strptime(last_backup['backup_time'], '%Y-%m-%d %H:%M:%S')
                    start_binlog_file = last_backup.get('binlog_file')
                    start_binlog_position = last_backup.get('binlog_position')
                else:
                    # 如果最后一次是增量备份，从该备份的结束位置开始
                    start_datetime = datetime.datetime.strptime(last_backup['backup_time'], '%Y-%m-%d %H:%M:%S')
                    start_binlog_file = last_backup.get('end_binlog_file')
                    start_binlog_position = last_backup.get('end_binlog_position')
            
            # 获取当前binlog信息
            current_binlog_info = self.get_mysql_binlog_info()
            if not current_binlog_info['status']:
                return {"status": False, "msg": "无法获取当前binlog信息"}
            
            # 创建备份目录 - 按日期分组存储
            backup_start_time = datetime.datetime.now()
            date_str = backup_start_time.strftime('%Y-%m-%d')
            time_str = backup_start_time.strftime('%H%M%S')
            backup_folder = f"{time_str}_incremental"
            backup_dir = os.path.join(self.backup_path, database_name, date_str, backup_folder)
            os.makedirs(backup_dir, exist_ok=True)
            
            # 获取需要备份的binlog文件列表
            binlog_files = self._get_binlog_files_in_range(
                current_binlog_info['binlog_dir'],
                start_binlog_file if 'start_binlog_file' in locals() else None,
                current_binlog_info['current_file'],
                start_datetime,
                backup_start_time
            )
            
            if not binlog_files:
                return {"status": False, "msg": "没有找到需要备份的binlog文件"}
            
            # 导出binlog
            sql_file = os.path.join(backup_dir, f"{database_name}_incremental.sql")
            result = self._export_binlog_to_sql(binlog_files, sql_file, database_name, start_datetime, backup_start_time)
            
            if not result['status']:
                return result
            
            # 计算文件信息
            file_hash = self._calculate_file_hash(sql_file)
            file_size = os.path.getsize(sql_file)
            
            # 保存备份信息
            backup_info = {
                "backup_id": f"{database_name}_{date_str}_{time_str}_incremental",
                "database_name": database_name,
                "backup_type": "incremental",
                "backup_time": backup_start_time.strftime('%Y-%m-%d %H:%M:%S'),
                "backup_date": date_str,
                "backup_folder": backup_folder,
                "file_path": sql_file,
                "file_size": file_size,
                "file_hash": file_hash,
                "start_time": start_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                "end_time": backup_start_time.strftime('%Y-%m-%d %H:%M:%S'),
                "start_binlog_file": start_binlog_file if 'start_binlog_file' in locals() else binlog_files[0],
                "start_binlog_position": start_binlog_position if 'start_binlog_position' in locals() else 0,
                "end_binlog_file": current_binlog_info['current_file'],
                "end_binlog_position": current_binlog_info['current_position'],
                "binlog_files": binlog_files,
                "status": "completed"
            }
            
            # 保存备份信息到文件
            info_file = os.path.join(backup_dir, 'backup_info.json')
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, ensure_ascii=False, indent=2)
            
            self._write_log(f"数据库 {database_name} 增量备份完成，文件大小: {self._format_size(file_size)}")
            
            return {"status": True, "msg": "增量备份完成", "data": backup_info}
            
        except Exception as e:
            error_msg = f"增量备份失败: {str(e)}"
            self._write_log(error_msg, 'error')
            return {"status": False, "msg": error_msg}

    def _get_binlog_files_in_range(self, binlog_dir: str, start_file: str, end_file: str, 
                                   start_time: datetime.datetime, end_time: datetime.datetime) -> List[str]:
        """获取指定时间范围内的binlog文件"""
        try:
            binlog_info = self.get_mysql_binlog_info()
            if not binlog_info['status']:
                return []
            
            all_binlog_files = binlog_info['binlog_list']
            selected_files = []
            
            start_found = False
            for binlog_file in all_binlog_files:
                # 如果指定了起始文件，从该文件开始
                if start_file and binlog_file == start_file:
                    start_found = True
                
                # 如果没有指定起始文件，或者已经找到起始文件
                if not start_file or start_found:
                    selected_files.append(binlog_file)
                
                # 如果到达结束文件，停止
                if binlog_file == end_file:
                    break
            
            return selected_files
            
        except Exception as e:
            self._write_log(f"获取binlog文件列表失败: {e}", 'error')
            return []

    def _export_binlog_to_sql(self, binlog_files: List[str], output_file: str, database_name: str, 
                             start_time: datetime.datetime, end_time: datetime.datetime) -> Dict[str, Any]:
        """将binlog导出为SQL文件"""
        try:
            binlog_info = self.get_mysql_binlog_info()
            binlog_dir = binlog_info['binlog_dir']
            
            # 构建mysqlbinlog命令
            binlog_paths = [os.path.join(binlog_dir, f) for f in binlog_files]
            
            # 检查binlog文件是否存在
            for binlog_path in binlog_paths:
                if not os.path.exists(binlog_path):
                    return {"status": False, "msg": f"Binlog文件不存在: {binlog_path}"}
            
            # 构建时间过滤参数
            start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
            end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S')
            
            shell = f"'{self._MYSQLBINLOG_BIN}' --database='{database_name}' " \
                   f"--start-datetime='{start_time_str}' --stop-datetime='{end_time_str}' "
            
            shell += ' '.join(f"'{path}'" for path in binlog_paths)
            shell += f" > '{output_file}'"
            
            # 执行命令
            result = public.ExecShell(shell)
            public.WriteFile("/www/backup/mysql_binlog_backup/test.txt", shell)
            
            if not os.path.exists(output_file):
                return {"status": False, "msg": f"导出binlog失败: {result[1]}"}
            
            # 检查文件是否存在，即使为空也是正常的（可能该时间段没有数据变化）
            file_size = os.path.getsize(output_file)
            if file_size == 0:
                self._write_log(f"该时间段binlog为空，无数据变化（这是正常现象）")
                # 创建一个标记注释，表示这是一个空的但成功的增量备份
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"-- 增量备份时间段: {start_time.strftime('%Y-%m-%d %H:%M:%S')} 到 {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"-- 该时间段内数据库无变化，binlog为空\n")
                    f.write(f"-- 这是一次成功的增量备份\n")
            
            return {"status": True, "msg": "binlog导出成功"}
            
        except Exception as e:
            return {"status": False, "msg": f"导出binlog失败: {str(e)}"}

    def _get_last_backup_info(self, database_name: str) -> Optional[Dict[str, Any]]:
        """获取最后一次备份信息"""
        try:
            database_backup_dir = os.path.join(self.backup_path, database_name)
            if not os.path.exists(database_backup_dir):
                return None
            
            backup_infos = []
            
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
                            backup_infos.append(backup_info)
            
            if not backup_infos:
                return None
            
            # 按备份时间排序，获取最新的备份
            backup_infos.sort(key=lambda x: x['backup_time'], reverse=True)
            return backup_infos[0]
                
        except Exception as e:
            self._write_log(f"获取最后备份信息失败: {e}", 'error')
            return None

    def get_backup_files_list(self, database_name: str = None) -> List[Dict[str, Any]]:
        """获取备份文件列表"""
        try:
            backup_files = []
            
            if database_name:
                database_dirs = [database_name]
            else:
                database_dirs = [d for d in os.listdir(self.backup_path) 
                               if os.path.isdir(os.path.join(self.backup_path, d))]
            
            for db_name in database_dirs:
                db_backup_dir = os.path.join(self.backup_path, db_name)
                if not os.path.exists(db_backup_dir):
                    continue
                
                # 遍历日期目录
                for date_dir in os.listdir(db_backup_dir):
                    date_path = os.path.join(db_backup_dir, date_dir)
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
                                backup_info['formatted_size'] = self._format_size(backup_info['file_size'])
                                backup_files.append(backup_info)
            
            # 按备份时间排序
            backup_files.sort(key=lambda x: x['backup_time'], reverse=True)
            return backup_files
            
        except Exception as e:
            self._write_log(f"获取备份文件列表失败: {e}", 'error')
            return []

    def get_backup_files_list_with_filter(self, database_name: str = None, backup_type: str = 'all',
                                        date: str = None, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        """获取备份文件列表（支持筛选和分页）"""
        try:
            # 获取所有备份文件
            all_backup_files = self.get_backup_files_list(database_name)
            
            # 应用筛选条件
            filtered_files = []
            
            for backup_file in all_backup_files:
                # 备份类型筛选
                if backup_type != 'all':
                    if backup_type == 'full' and backup_file['backup_type'] != 'full':
                        continue
                    elif backup_type == 'incremental' and backup_file['backup_type'] != 'incremental':
                        continue
                
                # 日期筛选
                if date:
                    backup_date = backup_file['backup_time'][:10]  # 提取日期部分 YYYY-MM-DD
                    if backup_date != date:
                        continue
                
                filtered_files.append(backup_file)
            
            # 计算分页信息
            total = len(filtered_files)
            total_pages = (total + limit - 1) // limit if total > 0 else 0
            offset = (page - 1) * limit
            
            # 获取当前页数据
            page_files = filtered_files[offset:offset + limit]
            
            return {
                'list': page_files,
                'total': total,
                'page': page,
                'limit': limit,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
            
        except Exception as e:
            self._write_log(f"获取备份文件列表失败: {e}", 'error')
            return {
                'list': [],
                'total': 0,
                'page': page,
                'limit': limit,
                'total_pages': 0,
                'has_next': False,
                'has_prev': False
            }
            
    def cleanup_all_backups(self, database_name: str):
        public.ExecShell("rm -rf {}/{}/*".format(self.backup_path, database_name))
        return {"status": True, "msg": "清理成功"}

    def delete_backup_file(self, backup_id: str) -> Dict[str, Any]:
        """删除备份文件"""
        try:
            # 查找备份文件
            backup_info = self._find_backup_by_id(backup_id)
            if not backup_info:
                return {"status": False, "msg": "备份文件不存在"}
            
            # 删除备份目录
            backup_dir = os.path.dirname(backup_info['file_path'])
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
                #self._write_log(f"删除备份文件: {backup_id}")
                return {"status": True, "msg": "删除成功"}
            else:
                return {"status": False, "msg": "备份目录不存在"}
                
        except Exception as e:
            error_msg = f"删除备份文件失败: {str(e)}"
            self._write_log(error_msg, 'error')
            return {"status": False, "msg": error_msg}

    def _find_backup_by_id(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """根据备份ID查找备份信息"""
        backup_files = self.get_backup_files_list()
        for backup in backup_files:
            if backup['backup_id'] == backup_id:
                return backup
        return None

    def get_backup_logs(self, database_name: str = None, log_type: str = 'all', limit: int = 100) -> List[str]:
        """获取备份日志"""
        try:
            if not os.path.exists(self.log_file):
                return []
            
            logs = []
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 过滤日志
            for line in lines[-limit:]:
                line = line.strip()
                if not line:
                    continue
                
                # 如果指定了数据库名称，只返回相关日志
                if database_name and database_name not in line:
                    continue
                
                # 如果指定了日志类型，进行过滤
                if log_type != 'all':
                    if log_type == 'full' and '全量备份' not in line:
                        continue
                    elif log_type == 'incremental' and '增量备份' not in line:
                        continue
                
                logs.append(line)
            
            return logs
            
        except Exception as e:
            self._write_log(f"获取备份日志失败: {e}", 'error')
            return []

    def get_backup_status(self) -> Dict[str, Any]:
        """获取备份状态"""
        try:
            status = {
                "binlog_enabled": self.check_binlog_enabled(),
                "total_backups": 0,
                "databases": {},
                "disk_usage": self._get_backup_disk_usage()
            }
            
            # 统计备份信息
            backup_files = self.get_backup_files_list()
            status["total_backups"] = len(backup_files)
            
            for backup in backup_files:
                db_name = backup['database_name']
                if db_name not in status["databases"]:
                    status["databases"][db_name] = {
                        "full_backups": 0,
                        "incremental_backups": 0,
                        "total_size": 0,
                        "last_backup": None
                    }
                
                if backup['backup_type'] == 'full':
                    status["databases"][db_name]["full_backups"] += 1
                else:
                    status["databases"][db_name]["incremental_backups"] += 1
                
                status["databases"][db_name]["total_size"] += backup['file_size']
                
                if not status["databases"][db_name]["last_backup"] or \
                   backup['backup_time'] > status["databases"][db_name]["last_backup"]:
                    status["databases"][db_name]["last_backup"] = backup['backup_time']
            
            return status
            
        except Exception as e:
            self._write_log(f"获取备份状态失败: {e}", 'error')
            return {"error": str(e)}

    def _get_backup_disk_usage(self) -> Dict[str, Any]:
        """获取备份目录磁盘使用情况"""
        try:
            if not os.path.exists(self.backup_path):
                return {"total_size": 0, "formatted_size": "0 B"}
            
            total_size = 0
            for root, dirs, files in os.walk(self.backup_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
            
            return {
                "total_size": total_size,
                "formatted_size": self._format_size(total_size)
            }
            
        except Exception as e:
            return {"total_size": 0, "formatted_size": "0 B", "error": str(e)}

    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件SHA256哈希值"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            self._write_log(f"计算文件哈希失败: {e}", 'error')
            return ""

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
    backup_manager = BackupManager()
    
    # 测试检查binlog
    print("Binlog状态:", backup_manager.check_binlog_enabled())
    
    # 测试获取binlog信息
    binlog_info = backup_manager.get_mysql_binlog_info()
    print("Binlog信息:", binlog_info)
    
    # 如果有参数，执行对应的备份操作
    if len(sys.argv) > 2:
        method_name = sys.argv[1]
        database_name = sys.argv[2]
        
        if method_name == 'full_backup':
            result = backup_manager.mysqldump_full_backup(database_name)
            print("全量备份结果:", result)
        elif method_name == 'incremental_backup':
            result = backup_manager.binlog_incremental_backup(database_name)
            print("增量备份结果:", result) 