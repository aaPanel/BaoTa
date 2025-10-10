# -*- coding: utf-8 -*-
"""
MySQL 主从复制配置管理模块
负责配置信息的读取、保存、验证等操作
"""

import os
import json
import time
import re
from typing import Union, Dict, List, Any
import public


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self.base_path="/www/server/panel/config/mysql_slave_info"
        self.master_slave_info_path = os.path.join(self.base_path, "master_slave_info.json")
        self.old_config_json = os.path.join(self.base_path, "config.json.0")
        self.master_slave_log_path = os.path.join(self.base_path, "log")
        
    def get_slave_config(self, slave_ip: str) -> Union[Dict[str, Any], None]:
        """获取指定从库的配置信息
        Args:
            slave_ip: 从库IP
        Returns:
            dict: 从库配置信息
            None: 未找到配置或出错
        """
        try:
            if not os.path.exists(self.master_slave_info_path):
                return None
                
            master_slave_info = json.loads(public.ReadFile(self.master_slave_info_path))
            for info in master_slave_info:
                if info.get("slave_ip") == slave_ip:
                    return info
            return None
        except:
            return None

    def save_slave_config(self, slave_ip: str, new_info: Dict[str, Any]) -> bool:
        """保存从库配置信息
        Args:
            slave_ip: 从库IP
            new_info: 新的配置信息
        Returns:
            bool: 保存是否成功
        """
        try:
            print(new_info)
            if not os.path.exists(self.master_slave_info_path):
                return False
                
            master_slave_info = json.loads(public.ReadFile(self.master_slave_info_path))
            for i, info in enumerate(master_slave_info):
                if info.get("slave_ip") == slave_ip:
                    master_slave_info[i] = new_info
                    public.WriteFile(self.master_slave_info_path, json.dumps(master_slave_info))
                    print(master_slave_info)
                    return True
            return False
        except:
            return False

    def update_slave_status(self, slave_ip: str, step: int, step_index: int, status: str, msg: str) -> bool:
        """更新从库同步状态"""
        info = self.get_slave_config(slave_ip)
        if not info:
            return False
            
        info["data"]["step"] = step
        info["data"]["steps"][step_index] = {
            "name": info["data"]["steps"][step_index]["name"],
            "status": status,
            "msg": msg
        }
        return self.save_slave_config(slave_ip, info)

    def add_slave_config(self, config_data: Dict[str, Any]) -> bool:
        """添加新的从库配置"""
        try:
            if os.path.exists(self.master_slave_info_path):
                master_slave_info = json.loads(public.ReadFile(self.master_slave_info_path))
            else:
                master_slave_info = []
            
            master_slave_info.append(config_data)
            public.WriteFile(self.master_slave_info_path, json.dumps(master_slave_info))
            return True
        except:
            return False

    def remove_slave_config(self, slave_ip: str) -> bool:
        """删除从库配置"""
        try:
            if not os.path.exists(self.master_slave_info_path):
                return False
                
            master_slave_info = json.loads(public.ReadFile(self.master_slave_info_path))
            master_slave_info = [item for item in master_slave_info if item.get("slave_ip") != slave_ip]
            public.WriteFile(self.master_slave_info_path, json.dumps(master_slave_info))
            return True
        except:
            return False

    def get_all_slave_configs(self) -> List[Dict[str, Any]]:
        """获取所有从库配置"""
        try:
            if not os.path.exists(self.master_slave_info_path):
                return []
            return json.loads(public.ReadFile(self.master_slave_info_path))
        except:
            return []

    def print_log(self, slave_ip: str, log_msg: str):
        """打印日志"""
        if not os.path.exists(self.master_slave_log_path):
            public.ExecShell("mkdir -p {path}".format(path=self.master_slave_log_path))
        
        time_str = time.strftime('%Y-%m-%d %H:%M:%S')
        log_path = self.master_slave_log_path + "/{slave_ip}.log".format(slave_ip=slave_ip)
        log = "[{}] {}".format(time_str, log_msg)
        public.writeFile(log_path, log + "\n", 'a+')

    @staticmethod
    def get_server_id_from_ip(ip_address: str) -> int:
        """根据IP地址生成唯一的MySQL server-id"""
        try:
            ip_parts = ip_address.split('.')
            if len(ip_parts) != 4:
                return int(time.time()) % 4294967295
            
            ip_num = (int(ip_parts[0]) * 256**3 + 
                     int(ip_parts[1]) * 256**2 + 
                     int(ip_parts[2]) * 256 + 
                     int(ip_parts[3]))
            
            server_id = (ip_num % 4294967294) + 1
            return server_id
        except:
            return int(time.time()) % 4294967295
    def create_default_steps(self, sync_type: str = "auto") -> List[Dict[str, str]]:
        """创建默认的同步步骤"""
        base_steps = [
            {
                'name': '主数据库配置',
                'status': 'wait',
                'msg': '等待配置主数据库'
            },
            {
                'name': '备份数据库',
                'status': 'wait',
                'msg': '等待备份数据库'
            },
            {
                'name': '导入数据',
                'status': 'wait',
                'msg': '等待数据导入从库'
            },
            {
                'name': '从库配置',
                'status': 'wait',
                'msg': '等待配置从库'
            },
            {
                'name': '完成同步',
                'status': 'wait',
                'msg': '等待完成'
            }
        ]
        
        if sync_type == "auto":
            # 在"备份数据库"后插入"上传数据"步骤
            upload_step = {
                'name': '上传数据',
                'status': 'wait',
                'msg': '等待上传数据'
            }
            return base_steps[:2] + [upload_step] + base_steps[2:]
        else:
            return base_steps 