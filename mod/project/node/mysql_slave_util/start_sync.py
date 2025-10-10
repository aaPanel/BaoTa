#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MySQL 主从复制同步启动脚本
用于后台执行同步任务
"""

import sys
import os

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)  # 添加当前目录到路径

if '/www/server/panel/class' not in sys.path:
    sys.path.insert(0, '/www/server/panel/class')
if '/www/server/panel' not in sys.path:
    sys.path.insert(0, '/www/server/panel')

from sync_service import SyncService


def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("Usage: python start_sync.py <method> <slave_ip>")
        sys.exit(1)
    
    method_name = sys.argv[1]  # 方法名
    slave_ip = sys.argv[2]     # 从库IP
    
    sync_service = SyncService()
    
    if method_name == "auto_sync_data":
        result = sync_service.auto_sync_data(slave_ip)
        print(f"自动同步结果: {result}")
    elif method_name == "manual_sync_data":
        result = sync_service.manual_sync_data(slave_ip)
        print(f"手动同步结果: {result}")
    else:
        print(f"错误: 未知的方法 '{method_name}'")
        sys.exit(1)


if __name__ == '__main__':
    main() 