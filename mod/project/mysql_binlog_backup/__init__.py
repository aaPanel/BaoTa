# coding: utf-8
# -------------------------------------------------------------------
# MySQL Binlog增量备份系统
# -------------------------------------------------------------------
# Author: miku <miku@bt.cn>
# -------------------------------------------------------------------

"""
MySQL Binlog增量备份系统

这是一个专门用于MySQL数据库增量备份的系统，支持：
- 基于mysqldump的全量备份
- 基于binlog的增量备份
- 时间点恢复(Point-in-Time Recovery)
- 自动化备份调度
- 完整的备份管理功能

主要模块：
- comMod: API接口控制器
- config_manager: 配置管理
- backup_manager: 备份管理
- restore_manager: 还原管理  
- task_scheduler: 任务调度器
"""

__version__ = "1.0.0"
__author__ = "miku <miku@bt.cn>"
__description__ = "MySQL Binlog增量备份系统"

# 导出主要类
from .comMod import main as ComMod
from .config_manager import ConfigManager
from .backup_manager import BackupManager
from .restore_manager import RestoreManager
from .task_scheduler import TaskScheduler, ManualBackupRunner

__all__ = [
    'ComMod',
    'ConfigManager', 
    'BackupManager',
    'RestoreManager',
    'TaskScheduler',
    'ManualBackupRunner'
] 