# coding: utf-8
# -------------------------------------------------------------------
# MySQL Binlog增量备份系统
# -------------------------------------------------------------------
# Author: miku <miku@bt.cn>
# -------------------------------------------------------------------
import json
import os
import sys
import time
import datetime
import re

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

if '/www/server/panel' not in sys.path:
    sys.path.insert(0, '/www/server/panel')

import public
import panelMysql
import db_mysql
import database
from mod.project.mysql_binlog_backup.config_manager import ConfigManager
from mod.project.mysql_binlog_backup.backup_manager import BackupManager
from mod.project.mysql_binlog_backup.restore_manager import RestoreManager
from mod.project.mysql_binlog_backup.cleanup_manager import CleanupManager

class main:
    def __init__(self):
        self.base_path = '/www/backup/mysql_binlog_backup'
        self.config_manager = ConfigManager()
        self.backup_manager = BackupManager()
        self.restore_manager = RestoreManager()
        self.cleanup_manager = CleanupManager(self.backup_manager, self.config_manager)
    
        self._init_db_connections()

        # 确保基础目录存在
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path, exist_ok=True)
    
    def _init_db_connections(self):
        """初始化数据库连接"""
        self.mysql_obj = db_mysql.panelMysql()

    def return_data(self, status: bool, msg=None, data=None):
        """统一返回数据格式"""
        return {
            "status": status,
            "msg": msg,
            "data": data
        }
    
    def _id_get_database_name(self, get):
        if not hasattr(get, 'id') or not get.id:
            return self.return_data(False, "缺少ID")
        db_info = public.M('databases').where('id=? AND type=?', (get.id, 'MySQL')).find()
        if not db_info:
            return self.return_data(False, "MySQL数据库ID {} 不存在".format(get.id))
        try:
            if db_info['db_type'] != 0:
                return self.return_data(False, "只支持本地本机数据库，不支持docker或远程数据库！")
        except:
            return self.return_data(False, "只支持本地本机数据库，不支持docker或远程数据库！")
        return db_info['name']

    def add_binlog_backup_task(self, get):
        """添加binlog备份任务"""
        try:
            # 参数验证
            if not hasattr(get, 'id') or not get.id:
                return self.return_data(False, "缺少数据库ID")
                
            if not hasattr(get, 'schedule_type') or not get.schedule_type:
                return self.return_data(False, "缺少调度类型")
                
            if not hasattr(get, 'incremental_backup_interval') or not get.incremental_backup_interval:
                return self.return_data(False, "缺少增量备份间隔(分钟)")

            # 获取保留天数参数，默认30天
            keep_days = int(getattr(get, 'keep_days', 30))
            if keep_days < 1:
                return self.return_data(False, "保留天数必须大于0")

            # 通过ID获取数据库名称
            database_name = self._id_get_database_name(get)
            if isinstance(database_name, dict):  # 返回的是错误信息
                return database_name

            # 检查binlog是否开启
            if not self.backup_manager.check_binlog_enabled():
                return self.return_data(False, "请先开启MySQL的binlog功能")

            try:
                incremental_backup_interval=int(get.incremental_backup_interval)
            except:
                return self.return_data(False, "增量备份间隔请设置为合理的数值")

            # 验证调度配置
            schedule_calculator = self.config_manager.schedule_calculator
            try:
                schedule_config = schedule_calculator.parse_schedule_from_request(get)
            except Exception as e:
                return self.return_data(False, str(e))

            # 创建备份任务配置
            task_config = {
                'database_name': database_name,
                'full_backup_schedule': schedule_config,
                'incremental_backup_interval': incremental_backup_interval,
                'keep_days': keep_days,
                'enabled': True,
                'create_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'last_full_backup': None,
                'last_incremental_backup': None,
                'next_full_backup': None,
                'next_incremental_backup': None
            }

            # 保存配置
            result = self.config_manager.save_backup_task_config(task_config)
            if result['status']:
                # 添加到计划任务
                self._add_cron_task()
                public.set_module_logs('mysql_binlog_backup', 'add_binlog_backup_task', 1)
                return self.return_data(True, "添加备份任务成功", result['data'])
            else:
                return self.return_data(False, result['msg'])
                
        except Exception as e:
            return self.return_data(False, str(e))

    def get_schedule_options(self, get=None):
        """获取支持的调度选项"""
        try:
            options = {
                "schedule_types": [
                    {
                        "value": "hours",
                        "label": "每N小时",
                        "description": "传统的小时间隔模式",
                        "params": ["interval_hours"]
                    },
                    {
                        "value": "daily",
                        "label": "每天固定时间",
                        "description": "每天在指定时间执行",
                        "params": ["time"]
                    },
                    {
                        "value": "weekly",
                        "label": "每周固定时间",
                        "description": "每周指定天的指定时间执行",
                        "params": ["time", "weekday"]
                    },
                    {
                        "value": "interval",
                        "label": "自定义间隔",
                        "description": "每隔N天的指定时间执行",
                        "params": ["time", "interval_days", "start_date"]
                    }
                ],
                "weekdays": [
                    {"value": 0, "label": "周日"},
                    {"value": 1, "label": "周一"},
                    {"value": 2, "label": "周二"},
                    {"value": 3, "label": "周三"},
                    {"value": 4, "label": "周四"},
                    {"value": 5, "label": "周五"},
                    {"value": 6, "label": "周六"}
                ],
                "examples": {
                    "daily": {
                        "description": "每天凌晨1:30执行",
                        "config": {
                            "schedule_type": "daily",
                            "schedule_time": "01:30:00"
                        }
                    },
                    "weekly": {
                        "description": "每周日凌晨1:30执行",
                        "config": {
                            "schedule_type": "weekly",
                            "schedule_time": "01:30:00",
                            "weekday": 0
                        }
                    },
                    "interval": {
                        "description": "每3天的凌晨1:01执行",
                        "config": {
                            "schedule_type": "interval",
                            "schedule_time": "01:01:00",
                            "interval_days": 3,
                            "start_date": "2025-07-08"
                        }
                    },
                    "hours": {
                        "description": "每24小时执行",
                        "config": {
                            "schedule_type": "hours",
                            "interval_hours": 24
                        }
                    }
                }
            }
            return self.return_data(True, "获取调度选项成功", options)
            
        except Exception as e:
            return self.return_data(False, str(e))

    def get_backup_task_list(self, get):
        """获取备份任务配置"""
        try:
            if not hasattr(get, 'id') or not get.id:
                return self.return_data(False, "缺少数据库ID")

            # 通过ID获取数据库名称
            database_name = self._id_get_database_name(get)
            if isinstance(database_name, dict):  # 返回的是错误信息
                return database_name

            # 获取指定数据库的备份任务
            task = self.config_manager.get_backup_task_config(database_name)
            space_free = self.backup_manager.disk_free_check()
            if task:
                if not space_free:
                    task['space_free'] = False
                else:
                    task['space_free'] = True

                if task['last_incremental_backup'] == None and task['last_full_backup'] != None:
                    task['last_exec_time'] = task['last_full_backup']
                elif task['last_incremental_backup'] != None and task['last_full_backup'] != None:
                    try:
                        incremental_time = datetime.datetime.strptime(task['last_incremental_backup'], '%Y-%m-%d %H:%M:%S')
                        full_backup_time = datetime.datetime.strptime(task['last_full_backup'], '%Y-%m-%d %H:%M:%S')
                        
                        if incremental_time > full_backup_time:
                            task['last_exec_time'] = task['last_incremental_backup']
                        else:
                            task['last_exec_time'] = task['last_full_backup']
                    except (ValueError, TypeError) as e:
                        task['last_exec_time'] = task['last_full_backup']
                else:
                    task['last_exec_time'] = None

                task['next_exec_time'] = task['next_full_backup']

                incremental_time = datetime.datetime.strptime(task['next_incremental_backup'], '%Y-%m-%d %H:%M:%S')
                full_backup_time = datetime.datetime.strptime(task['next_full_backup'], '%Y-%m-%d %H:%M:%S')
                if incremental_time > full_backup_time:
                    task['next_exec_time'] = task['next_incremental_backup']
                else:
                    task['next_exec_time'] = task['last_full_backup']

                return self.return_data(True, "获取成功", task)
            else:
                if not space_free:
                    data = {
                        "enabled": False,
                        "space_free": False
                    }
                else:
                    data = {
                        "enabled": False,
                        "space_free": True
                    }
                return self.return_data(True, "获取成功", data)
            
        except Exception as e:
            return self.return_data(False, str(e))

    def get_all_backup_tasks(self, get=None):
        """获取所有备份任务列表"""
        try:
            tasks = self.config_manager.get_backup_task_list()
            return self.return_data(True, "获取成功", tasks)
            
        except Exception as e:
            return self.return_data(False, str(e))

    def get_backup_files_list(self, get):
        """获取备份文件列表（支持分页、日期筛选、类型筛选）"""
        try:
            # 获取参数
            database_name = None
            if hasattr(get, 'id') and get.id:
                database_name = self._id_get_database_name(get)
                if isinstance(database_name, dict):  # 返回的是错误信息
                    return database_name
            
            backup_type = getattr(get, 'backup_type', 'all')  # all, full, incremental
            date = getattr(get, 'date', None)  # 指定日期 YYYY-MM-DD
            page = int(getattr(get, 'page', 1))
            limit = int(getattr(get, 'limit', 20))
            
            # 参数验证
            if page < 1:
                page = 1
            if limit < 1 or limit > 100:
                limit = 20
                
            # 获取备份文件列表
            result = self.backup_manager.get_backup_files_list_with_filter(
                database_name=database_name,
                backup_type=backup_type,
                date=date,
                page=page,
                limit=limit
            )
            
            return self.return_data(True, "获取成功", result)
            
        except Exception as e:
            return self.return_data(False, str(e))

    def update_backup_task_config(self, get):
        """更新备份任务配置"""
        try:
            if not hasattr(get, 'id') or not get.id:
                return self.return_data(False, "缺少数据库ID")

            # 通过ID获取数据库名称
            database_name = self._id_get_database_name(get)
            if isinstance(database_name, dict):  # 返回的是错误信息
                return database_name

            update_data = {}
            if hasattr(get, 'full_backup_interval'):
                update_data['full_backup_interval'] = int(get.full_backup_interval)
            if hasattr(get, 'incremental_backup_interval'):
                update_data['incremental_backup_interval'] = int(get.incremental_backup_interval)
            if hasattr(get, 'keep_days'):
                keep_days = int(get.keep_days)
                if keep_days < 1:
                    return self.return_data(False, "保留天数必须大于0")
                update_data['keep_days'] = keep_days
            if hasattr(get, 'enabled'):
                update_data['enabled'] = bool(get.enabled)

            result = self.config_manager.update_backup_task_config(database_name, update_data)
            if result['status']:
                return self.return_data(True, "更新配置成功")
            else:
                return self.return_data(False, result['msg'])
                
        except Exception as e:
            return self.return_data(False, str(e))

    def set_backup_task_status(self, get):
        """设置备份任务状态（启用/禁用）"""
        try:
            if not hasattr(get, 'id') or not get.id:
                return self.return_data(False, "缺少数据库ID")
                
            if not hasattr(get, 'enabled'):
                return self.return_data(False, "缺少状态参数(enabled)")

            # 通过ID获取数据库名称
            database_name = self._id_get_database_name(get)
            if isinstance(database_name, dict):  # 返回的是错误信息
                return database_name

            # 检查任务是否存在
            task_config = self.config_manager.get_backup_task_config(database_name)
            if not task_config:
                return self.return_data(False, "数据库 {} 的备份任务不存在".format(database_name))

            # 转换状态参数
            enabled = False
            if str(get.enabled).lower() in ['true', '1', 'yes', 'on']:
                enabled = True
            elif str(get.enabled).lower() in ['false', '0', 'no', 'off']:
                enabled = False
            else:
                return self.return_data(False, "状态参数无效，请使用 true/false 或 1/0")

            # 更新状态
            update_data = {'enabled': enabled}
            result = self.config_manager.update_backup_task_config(database_name, update_data)
            
            if result['status']:
                status_text = "启用" if enabled else "禁用"
                # 记录日志
                public.set_module_logs('mysql_binlog_backup', 'set_backup_task_status', 1)
                
                return self.return_data(True, "备份任务已{}".format(status_text), {
                    'database_name': database_name,
                    'enabled': enabled,
                    'status_text': status_text
                })
            else:
                return self.return_data(False, result['msg'])
                
        except Exception as e:
            return self.return_data(False, str(e))

    def del_binlog_backup_task(self, get):
        """删除binlog备份任务"""
        try:
            if not hasattr(get, 'id') or not get.id:
                return self.return_data(False, "缺少数据库ID")

            # 通过ID获取数据库名称
            database_name = self._id_get_database_name(get)
            if isinstance(database_name, dict):  # 返回的是错误信息
                return database_name

            # 删除配置
            result = self.config_manager.delete_backup_task_config(database_name)
            if result['status']:
                # 如果没有其他任务，移除计划任务
                remaining_tasks = self.config_manager.get_backup_task_list()
                if not remaining_tasks:
                    self._remove_cron_task()
                
                public.set_module_logs('mysql_binlog_backup', 'del_binlog_backup_task', 1)
                return self.return_data(True, "设置成功！")
            else:
                return self.return_data(False, result['msg'])
                
        except Exception as e:
            return self.return_data(False, str(e))

    def get_backup_logs(self, get):
        """查看备份任务日志"""
        try:
            database_name = None
            if hasattr(get, 'id') and get.id:
                database_name = self._id_get_database_name(get)
                if isinstance(database_name, dict):  # 返回的是错误信息
                    return database_name
            
            log_type = getattr(get, 'log_type', 'all')  # all, full, incremental
            limit = getattr(get, 'limit', 100)
            
            logs = self.backup_manager.get_backup_logs(database_name, log_type, limit)
            return self.return_data(True, "获取日志成功", logs)
            
        except Exception as e:
            return self.return_data(False, str(e))

    def delete_backup_file(self, get):
        """删除备份文件"""
        try:
            if not hasattr(get, 'backup_id') or not get.backup_id:
                return self.return_data(False, "缺少备份ID")

            result = self.backup_manager.delete_backup_file(get.backup_id)
            if result['status']:
                return self.return_data(True, "删除备份文件成功")
            else:
                return self.return_data(False, result['msg'])
                
        except Exception as e:
            return self.return_data(False, str(e))

    def restore_binlog_data(self, get):
        """还原备份数据"""
        try:
            if not hasattr(get, 'id') or not get.id:
                return self.return_data(False, "缺少数据库ID")
                
            if not hasattr(get, 'restore_time') or not get.restore_time:
                return self.return_data(False, "缺少还原时间点")

            # 通过ID获取数据库名称
            database_name = self._id_get_database_name(get)
            if isinstance(database_name, dict):  # 返回的是错误信息
                return database_name

            # 启动还原任务
            result = self.restore_manager.start_restore_task(database_name, get.restore_time)
            if result['status']:
                public.set_module_logs('mysql_binlog_backup', 'restore_binlog_data', 1)
                return self.return_data(True, "还原任务已启动", result['data'])
            else:
                return self.return_data(False, result['msg'])
                
        except Exception as e:
            return self.return_data(False, str(e))

    def get_restore_progress(self, get):
        """获取还原进度"""
        try:
            task_id = getattr(get, 'task_id', None)
            progress = self.restore_manager.get_restore_progress(task_id)
            return self.return_data(True, "获取进度成功", progress)
            
        except Exception as e:
            return self.return_data(False, str(e))

    def get_backup_status(self, get=None):
        """获取备份状态"""
        try:
            status = self.backup_manager.get_backup_status()
            return self.return_data(True, "获取状态成功", status)
            
        except Exception as e:
            return self.return_data(False, str(e))
        
    def get_db_info(self, get=None):
        if not hasattr(get, 'id') or not get.id:
            return self.return_data(False, "缺少数据库ID")
        db_name = self._id_get_database_name(get)
        if isinstance(db_name, dict):  # 返回的是错误信息
            return db_name
        
        db_size = 0
        try:
            table_list = self.mysql_obj.query("show tables from `{}`".format(db_name))
            db_size=self.mysql_obj.query("SELECT SUM(data_length + index_length) AS db_size_bytes FROM information_schema.tables WHERE table_schema = '{}'".format(db_name))
            db_size=int(db_size[0][0])
        except:
            db_size = public.ExecShell("du -sb /www/server/data/{}".format(db_name))[0].split("\t")[0]
            if int(db_size) < 100:
                db_size=0
        
        try:
            table_count=len(table_list)
        except:
            return self.return_data(False, "获取数据库信息失败，请检查mysql是否正常启动/root密码是否正确后再进行增量备份设置")
        
        log_bin_status=self.mysql_obj.query("SHOW VARIABLES LIKE 'log_bin'")
        if log_bin_status[0][1].find("ON") != -1:
            log_bin_status=True
        else:
            log_bin_status=False

        if log_bin_status == False:
            return self.return_data(False, "二进制日志已关闭，请开启二进制日志后再设置增量备份！")

        data={
            "db_size": db_size,
            "table_count": table_count
        }
        
        return self.return_data(True, "获取数据库信息成功", data)
    
    def cleanup_all_backups(self, get=None):
        if not hasattr(get, 'id') or not get.id:
            return self.return_data(False, "缺少数据库ID")
        
        database_name = self._id_get_database_name(get)
        if isinstance(database_name, dict):  # 返回的是错误信息
            return database_name
        
        """清理所有备份文件"""
        try:
            result = self.backup_manager.cleanup_all_backups(database_name)
            if result['status']:
                return self.return_data(True, result['msg'])
            else:
                return self.return_data(False, result['msg'])
        except:
            return self.return_data(False, "清理失败")

    def cleanup_old_backups(self, get):
        """清理旧备份文件"""
        try:
            # 可以指定数据库ID，如果不指定则清理所有数据库
            database_name = None
            if hasattr(get, 'id') and get.id:
                database_name = self._id_get_database_name(get)
                if isinstance(database_name, dict):  # 返回的是错误信息
                    return database_name
            
            # 获取保留天数，优先使用传入参数
            keep_days = None
            if hasattr(get, 'keep_days') and get.keep_days:
                keep_days = int(get.keep_days)
                if keep_days < 1:
                    return self.return_data(False, "保留天数必须大于0")
            
            # 如果指定了数据库，清理单个数据库
            if database_name:
                # 获取该数据库的备份任务配置中的保留天数
                if not keep_days:
                    task_config = self.config_manager.get_backup_task_config(database_name)
                    if task_config and 'keep_days' in task_config:
                        keep_days = task_config['keep_days']
                    else:
                        keep_days = 30  # 默认值
                
                result = self.cleanup_manager.cleanup_database_backups(database_name, keep_days)
                if result['status']:
                    return self.return_data(True, result['msg'], result)
                else:
                    return self.return_data(False, result['msg'])
            else:
                # 清理所有数据库的备份
                result = self.cleanup_manager.cleanup_all_backups(keep_days)
                if result['status']:
                    return self.return_data(True, result['msg'], result.get('data', {}))
                else:
                    return self.return_data(False, result['msg'])
            
        except Exception as e:
            return self.return_data(False, str(e))

    def get_cleanup_preview(self, get):
        """预览清理效果（不实际删除）"""
        try:
            if not hasattr(get, 'id') or not get.id:
                return self.return_data(False, "缺少数据库ID")

            # 通过ID获取数据库名称
            database_name = self._id_get_database_name(get)
            if isinstance(database_name, dict):  # 返回的是错误信息
                return database_name

            # 获取保留天数
            keep_days = int(getattr(get, 'keep_days', 30))
            if keep_days < 1:
                return self.return_data(False, "保留天数必须大于0")

            result = self.cleanup_manager.get_cleanup_preview(database_name, keep_days)
            if result['status']:
                return self.return_data(True, result['msg'], result.get('preview', {}))
            else:
                return self.return_data(False, result['msg'])

        except Exception as e:
            return self.return_data(False, str(e))

    def get_cleanup_logs(self, get=None):
        """获取清理日志"""
        try:
            limit = int(getattr(get, 'limit', 100)) if get else 100
            logs = self.cleanup_manager.get_cleanup_logs(limit)
            return self.return_data(True, "获取清理日志成功", logs)
            
        except Exception as e:
            return self.return_data(False, str(e))

    def _add_cron_task(self):
        """添加计划任务"""
        import crontab
        try:
            # 每分钟执行一次备份检查
            cmd = "btpython {}/task_scheduler.py".format(os.path.dirname(__file__))
            
            # 检查是否已存在计划任务
            cron_list = public.M('crontab').where('name=?', ('[勿删]MySQL 增量备份任务',)).select()
            if not cron_list:
                pdata = {
                    'name': '[勿删]MySQL 增量备份任务',
                    'sBody': cmd,
                    'sType': 'toShell',
                    'sName': '',
                    'backupTo': '',
                    'save': '',
                    'urladdress': '',
                    'save_local': 0,
                    'notice': 0,
                    'notice_channel': '',
                    'datab_name': '',
                    'tables_name': '',
                    'flock': 1,
                    'version': '',
                    'user': '',
                    'stop_site': 0,
                    'type': 'minute-n',
                    'week': 1,
                    'hour': 1,
                    'minute': 1,
                    'where1': 1,
                    'timeSet': 1,
                    'timeType': "sday",
                }
                bt_syssafe_stop=False
                if os.path.exists("/etc/init.d/bt_syssafe"):
                    bt_syssafe_status = public.ExecShell("/etc/init.d/bt_syssafe status")
                    if bt_syssafe_status[0].find("already running") != -1:
                        public.ExecShell("/etc/init.d/bt_syssafe stop")
                        bt_syssafe_stop=True
                        time.sleep(1)

                crontab.crontab().AddCrontab(pdata)

                if bt_syssafe_stop:
                    public.ExecShell("/etc/init.d/bt_syssafe start")
                    time.sleep(1)
        except Exception as e:
            print("添加计划任务失败: {}".format(e))

    def _remove_cron_task(self):
        """移除计划任务"""
        try:
            public.M('crontab').where('echo=?', ('mysql_binlog_backup',)).delete()
        except Exception as e:
            print("移除计划任务失败: {}".format(e))
