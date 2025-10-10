# coding: utf-8
# -------------------------------------------------------------------
# MySQL Binlog增量备份系统 - 配置管理模块
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

class AdvancedScheduleCalculator:
    """高级调度计算器"""
    
    def __init__(self):
        pass
    
    def calculate_next_full_backup(self, schedule_config: Dict[str, Any], last_execution: str = None) -> str:
        """计算下次全量备份时间"""
        schedule_type = schedule_config.get('type', 'hours')
        
        if schedule_type == 'daily':
            return self._calculate_daily(schedule_config)
        elif schedule_type == 'weekly':
            return self._calculate_weekly(schedule_config)
        elif schedule_type == 'interval':
            return self._calculate_interval(schedule_config, last_execution)
        elif schedule_type == 'hours':
            return self._calculate_hours(schedule_config)
        else:
            # 默认使用小时模式
            return self._calculate_hours(schedule_config)
    
    def _calculate_daily(self, config: Dict[str, Any]) -> str:
        """每天固定时间执行"""
        target_time = config.get('time')
        if not target_time:
            raise ValueError("daily模式缺少 time 配置")
        
        now = datetime.datetime.now()
        today = now.date()
        
        # 解析目标时间
        time_parts = target_time.split(':')
        target_hour = int(time_parts[0])
        target_minute = int(time_parts[1])
        target_second = int(time_parts[2]) if len(time_parts) > 2 else 0
        
        # 今天的目标时间
        target_datetime = datetime.datetime.combine(
            today, 
            datetime.time(target_hour, target_minute, target_second)
        )
        
        # 如果今天的目标时间已过，计算明天的时间
        if now >= target_datetime:
            target_datetime += datetime.timedelta(days=1)
        
        return target_datetime.strftime('%Y-%m-%d %H:%M:%S')
    
    def _calculate_weekly(self, config: Dict[str, Any]) -> str:
        """每周固定时间执行"""
        target_weekday = config.get('weekday')
        target_time = config.get('time')
        
        if target_weekday is None:
            raise ValueError("weekly模式缺少 weekday 配置")
        if not target_time:
            raise ValueError("weekly模式缺少 time 配置")
        
        now = datetime.datetime.now()
        
        # 解析目标时间
        time_parts = target_time.split(':')
        target_hour = int(time_parts[0])
        target_minute = int(time_parts[1])
        target_second = int(time_parts[2]) if len(time_parts) > 2 else 0
        
        # 计算距离目标星期几还有多少天
        current_weekday = now.weekday()
        # Python的weekday(): 0=周一, 6=周日
        # 我们的配置: 0=周日, 1=周一...6=周六
        # 转换: 我们的周日(0) = Python的周日(6)
        python_target_weekday = 6 if target_weekday == 0 else target_weekday - 1
        
        days_ahead = python_target_weekday - current_weekday
        if days_ahead < 0:  # 这周的目标日已过
            days_ahead += 7
        elif days_ahead == 0:  # 今天就是目标日
            target_today = now.replace(hour=target_hour, minute=target_minute, second=target_second, microsecond=0)
            if now >= target_today:  # 今天的目标时间已过
                days_ahead = 7
        
        target_date = now.date() + datetime.timedelta(days=days_ahead)
        target_datetime = datetime.datetime.combine(
            target_date,
            datetime.time(target_hour, target_minute, target_second)
        )
        
        return target_datetime.strftime('%Y-%m-%d %H:%M:%S')
    
    def _calculate_interval(self, config: Dict[str, Any], last_execution: str = None) -> str:
        """固定间隔天数执行"""
        interval_days = config.get('interval_days')
        target_time = config.get('time')
        start_date = config.get('start_date')
        
        if not interval_days:
            raise ValueError("interval模式缺少 interval_days 配置")
        if not target_time:
            raise ValueError("interval模式缺少 time 配置")
        
        # 解析目标时间
        time_parts = target_time.split(':')
        target_hour = int(time_parts[0])
        target_minute = int(time_parts[1])
        target_second = int(time_parts[2]) if len(time_parts) > 2 else 0
        
        if last_execution:
            # 基于上次执行时间计算
            last_date = datetime.datetime.strptime(last_execution, '%Y-%m-%d %H:%M:%S').date()
            next_date = last_date + datetime.timedelta(days=interval_days)
        elif start_date:
            # 基于起始日期计算
            start = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
            now = datetime.datetime.now()
            
            #如果时间大于未来 直接用未来时间
            if start > now.date():
                next_date = start
            else:
                days_passed = (now.date() - start).days
                intervals_passed = days_passed // interval_days
                next_date = start + datetime.timedelta(days=(intervals_passed + 1) * interval_days)
        else:
            next_date = datetime.datetime.now().date() + datetime.timedelta(days=interval_days)
        
        target_datetime = datetime.datetime.combine(
            next_date,
            datetime.time(target_hour, target_minute, target_second)
        )
        
        return target_datetime.strftime('%Y-%m-%d %H:%M:%S')
    
    def _calculate_hours(self, config: Dict[str, Any]) -> str:
        """小时间隔执行"""
        interval_hours = config.get('interval_hours')
        if not interval_hours:
            raise ValueError("hours模式缺少 interval_hours 配置")
        
        now = datetime.datetime.now()
        next_time = now + datetime.timedelta(hours=interval_hours)
        return next_time.strftime('%Y-%m-%d %H:%M:%S')
    
    def parse_schedule_from_request(self, get_obj) -> Dict[str, Any]:
        """从请求对象解析调度配置"""
        if not hasattr(get_obj, 'schedule_type'):
            raise ValueError("缺少调度类型 schedule_type")
        
        schedule = {
            "type": get_obj.schedule_type
        }
        
        if get_obj.schedule_type == 'daily':
            if not hasattr(get_obj, 'schedule_time'):
                raise ValueError("daily模式需要提供 schedule_time 参数")
            schedule["time"] = get_obj.schedule_time
            
        elif get_obj.schedule_type == 'weekly':
            if not hasattr(get_obj, 'schedule_time'):
                raise ValueError("weekly模式需要提供 schedule_time 参数")
            if not hasattr(get_obj, 'weekday'):
                raise ValueError("weekly模式需要提供 weekday 参数")
            schedule["time"] = get_obj.schedule_time
            schedule["weekday"] = int(get_obj.weekday)
            
        elif get_obj.schedule_type == 'interval':
            if not hasattr(get_obj, 'schedule_time'):
                raise ValueError("interval模式需要提供 schedule_time 参数")
            if not hasattr(get_obj, 'interval_days'):
                raise ValueError("interval模式需要提供 interval_days 参数")
            schedule["time"] = get_obj.schedule_time
            schedule["interval_days"] = int(get_obj.interval_days)
            schedule["start_date"] = getattr(get_obj, 'start_date', None)
            
        elif get_obj.schedule_type == 'hours':
            if not hasattr(get_obj, 'interval_hours'):
                raise ValueError("hours模式需要提供 interval_hours 参数")
            schedule["interval_hours"] = int(get_obj.interval_hours)
        else:
            raise ValueError(f"不支持的调度类型: {get_obj.schedule_type}")
        
        return schedule

class ConfigManager:
    def __init__(self):
        self.base_path = '/www/backup/mysql_binlog_backup'
        self.config_file = os.path.join(self.base_path, 'backup_tasks.json')
        self.lock = threading.Lock()
        self.schedule_calculator = AdvancedScheduleCalculator()
        
        # 确保配置目录存在
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path, exist_ok=True)
            
        # 初始化配置文件
        if not os.path.exists(self.config_file):
            self._init_config_file()

    def _init_config_file(self):
        """初始化配置文件"""
        initial_config = {
            "version": "1.0",
            "create_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "tasks": {}
        }
        self._write_config(initial_config)

    def _read_config(self) -> Dict[str, Any]:
        """读取配置文件"""
        try:
            if os.path.exists(self.config_file):
                content = public.ReadFile(self.config_file)
                if content:
                    return json.loads(content)
            return self._get_default_config()
        except Exception as e:
            print(f"读取配置文件失败: {e}")
            return self._get_default_config()

    def _write_config(self, config: Dict[str, Any]) -> bool:
        """写入配置文件"""
        try:
            with self.lock:
                config['update_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                content = json.dumps(config, ensure_ascii=False, indent=2)
                public.WriteFile(self.config_file, content)
                return True
        except Exception as e:
            print(f"写入配置文件失败: {e}")
            return False

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "version": "1.0",
            "create_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "tasks": {}
        }

    def save_backup_task_config(self, task_config: Dict[str, Any]) -> Dict[str, Any]:
        """保存备份任务配置"""
        try:
            config = self._read_config()
            database_name = task_config['database_name']
            
            # 必须包含全量备份调度配置
            if 'full_backup_schedule' not in task_config:
                return {"status": False, "msg": "缺少全量备份调度配置 full_backup_schedule"}
            
            schedule_config = task_config['full_backup_schedule']
            
            # 计算下次全量备份时间
            next_full_backup = self.schedule_calculator.calculate_next_full_backup(schedule_config)
            task_config['next_full_backup'] = next_full_backup
            
            # 增量备份时间计算
            incremental_interval = task_config.get('incremental_backup_interval', 30)
            next_full_time = datetime.datetime.strptime(next_full_backup, '%Y-%m-%d %H:%M:%S')
            next_incremental_time = next_full_time + datetime.timedelta(minutes=incremental_interval)
            task_config['next_incremental_backup'] = next_incremental_time.strftime('%Y-%m-%d %H:%M:%S')
            
            task_config['task_id'] = f"{database_name}_{int(time.time())}"
            
            config['tasks'][database_name] = task_config
            
            if self._write_config(config):
                return {"status": True, "msg": "保存成功", "data": task_config}
            else:
                return {"status": False, "msg": "写入配置文件失败"}
                
        except Exception as e:
            return {"status": False, "msg": f"保存配置失败: {str(e)}"}

    def get_backup_task_list(self) -> List[Dict[str, Any]]:
        """获取备份任务列表"""
        try:
            config = self._read_config()
            tasks = list(config.get('tasks', {}).values())
            
            # 添加状态信息
            for task in tasks:
                task['status'] = self._get_task_status(task)
                
            return tasks
        except Exception as e:
            print(f"获取备份任务列表失败: {e}")
            return []

    def get_backup_task_config(self, database_name: str) -> Optional[Dict[str, Any]]:
        """获取指定数据库的备份任务配置"""
        try:
            config = self._read_config()
            return config.get('tasks', {}).get(database_name)
        except Exception as e:
            print(f"获取备份任务配置失败: {e}")
            return None

    def update_backup_task_config(self, database_name: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新备份任务配置"""
        try:
            config = self._read_config()
            
            if database_name not in config.get('tasks', {}):
                return {"status": False, "msg": "备份任务不存在"}
            
            task_config = config['tasks'][database_name]
            
            # 更新配置
            for key, value in update_data.items():
                if key in ['full_backup_interval', 'incremental_backup_interval', 'enabled']:
                    task_config[key] = value
            
            # 如果更新了间隔时间，重新计算下次执行时间
            if 'full_backup_interval' in update_data:
                now = datetime.datetime.now()
                task_config['next_full_backup'] = self._calculate_next_time(now, task_config['full_backup_interval'] * 60)
            
            if 'incremental_backup_interval' in update_data:
                now = datetime.datetime.now()
                task_config['next_incremental_backup'] = self._calculate_next_time(now, task_config['incremental_backup_interval'])
                
            config['tasks'][database_name] = task_config
            
            if self._write_config(config):
                return {"status": True, "msg": "更新成功", "data": task_config}
            else:
                return {"status": False, "msg": "写入配置文件失败"}
                
        except Exception as e:
            return {"status": False, "msg": f"更新配置失败: {str(e)}"}

    def update_backup_execution_time(self, database_name: str, backup_type: str, execution_time: str = None) -> bool:
        """更新备份执行时间"""
        try:
            config = self._read_config()
            
            if database_name not in config.get('tasks', {}):
                return False
                
            task_config = config['tasks'][database_name]
            
            if execution_time is None:
                execution_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if backup_type == 'full':
                task_config['last_full_backup'] = execution_time
                
                # 使用调度计算器计算下次全量备份时间
                schedule_config = task_config.get('full_backup_schedule')
                if not schedule_config:
                    return False  # 配置格式错误
                
                next_full_backup = self.schedule_calculator.calculate_next_full_backup(schedule_config, execution_time)
                task_config['next_full_backup'] = next_full_backup
                
                # 全量备份完成后，立即设置增量备份时间
                now = datetime.datetime.now()
                task_config['next_incremental_backup'] = self._calculate_next_time(now, task_config['incremental_backup_interval'])
                
            elif backup_type == 'incremental':
                task_config['last_incremental_backup'] = execution_time
                # 计算下次增量备份时间
                now = datetime.datetime.now()
                task_config['next_incremental_backup'] = self._calculate_next_time(now, task_config['incremental_backup_interval'])
            
            config['tasks'][database_name] = task_config
            return self._write_config(config)
            
        except Exception as e:
            print(f"更新备份执行时间失败: {e}")
            return False

    def delete_backup_task_config(self, database_name: str) -> Dict[str, Any]:
        """删除备份任务配置"""
        try:
            config = self._read_config()
            
            if database_name not in config.get('tasks', {}):
                return {"status": False, "msg": "备份任务不存在"}
            
            del config['tasks'][database_name]
            
            if self._write_config(config):
                return {"status": True, "msg": "删除成功"}
            else:
                return {"status": False, "msg": "写入配置文件失败"}
                
        except Exception as e:
            return {"status": False, "msg": f"删除配置失败: {str(e)}"}

    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """获取待执行的任务"""
        try:
            config = self._read_config()
            pending_tasks = []
            now = datetime.datetime.now()
            
            for database_name, task_config in config.get('tasks', {}).items():
                if not task_config.get('enabled', True):
                    continue
                    
                # 检查是否需要执行全量备份
                next_full = task_config.get('next_full_backup')
                if next_full and datetime.datetime.strptime(next_full, '%Y-%m-%d %H:%M:%S') <= now:
                    pending_tasks.append({
                        'database_name': database_name,
                        'backup_type': 'full',
                        'config': task_config
                    })
                
                # 检查是否需要执行增量备份
                next_incremental = task_config.get('next_incremental_backup')
                if next_incremental and datetime.datetime.strptime(next_incremental, '%Y-%m-%d %H:%M:%S') <= now:
                    # 确保有全量备份基础
                    if task_config.get('last_full_backup'):
                        pending_tasks.append({
                            'database_name': database_name,
                            'backup_type': 'incremental',
                            'config': task_config
                        })
            
            return pending_tasks
            
        except Exception as e:
            print(f"获取待执行任务失败: {e}")
            return []

    def _calculate_next_time(self, current_time: datetime.datetime, interval_minutes: int) -> str:
        """计算下次执行时间"""
        next_time = current_time + datetime.timedelta(minutes=interval_minutes)
        return next_time.strftime('%Y-%m-%d %H:%M:%S')

    def _get_task_status(self, task: Dict[str, Any]) -> str:
        """获取任务状态"""
        if not task.get('enabled', True):
            return 'disabled'
        
        now = datetime.datetime.now()
        
        # 检查是否有备份正在进行
        if task.get('backup_running', False):
            return 'running'
        
        # 检查下次执行时间
        next_full = task.get('next_full_backup')
        next_incremental = task.get('next_incremental_backup')
        
        if next_full and datetime.datetime.strptime(next_full, '%Y-%m-%d %H:%M:%S') <= now:
            return 'pending_full'
        elif next_incremental and datetime.datetime.strptime(next_incremental, '%Y-%m-%d %H:%M:%S') <= now:
            return 'pending_incremental'
        else:
            return 'waiting'

    def set_task_running_status(self, database_name: str, running: bool) -> bool:
        """设置任务运行状态"""
        try:
            config = self._read_config()
            
            if database_name in config.get('tasks', {}):
                config['tasks'][database_name]['backup_running'] = running
                return self._write_config(config)
            
            return False
        except Exception as e:
            print(f"设置任务运行状态失败: {e}")
            return False

if __name__ == '__main__':
    # 测试代码
    config_manager = ConfigManager()
    
    # 测试保存任务配置
    test_config = {
        'database_name': 'test_db',
        'full_backup_interval': 24,    # 24小时执行一次全量备份
        'incremental_backup_interval': 30,  # 30分钟执行一次增量备份
        'enabled': True,
        'create_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    result = config_manager.save_backup_task_config(test_config)
    print("保存配置结果:", result)
    
    # 测试获取任务列表
    tasks = config_manager.get_backup_task_list()
    print("任务列表:", tasks)
    
    # 测试获取待执行任务
    pending = config_manager.get_pending_tasks()
    print("待执行任务:", pending) 