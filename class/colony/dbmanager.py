#!/usr/bin/python
# coding: utf-8
"""

author: linxiao
date: 2021/1/23 18:07
"""

from colony import mysql
from colony.dbnode import dbnode
import public 

import json


class dbmanager:

    __nodes = []

    def __get_deploy_settings(self):
        config = public.ReadFile("config/deploy.json")
        settings = json.loads(config)
        return settings


    def generate_node_config(self):
        """生成节点配置文件
        
        1. 初始化集群管理节点数据库管理用户名和密码(非root)
        2. 赋予必要的权限
        3. 将配置生成到文件
        """

    def deploy(self, get):
        """部署节点"""
        settings = self.__get_deploy_settings()
        replication_mode = settings["mode"].lower()
        if replication_mode == "master-master":
            # 主主复制初始化
            master_host_settings = settings["master"]
            secondary_host_settings = settings["secondary master"]

            db_manager_user = settings["db_manager_user"]
            db_replication_user = settings["db_replication_user"]
            db_reset_root = settings["db_reset_root"]

            master_host_settings['db_manager_user'] = db_manager_user
            master_host_settings['db_replication_user'] = db_replication_user
            master_host_settings['db_reset_root'] = db_reset_root
            
            secondary_host_settings['db_manager_user'] = db_manager_user
            secondary_host_settings['db_replication_user'] = db_replication_user
            secondary_host_settings['db_reset_root'] = db_reset_root

            node1 = dbnode()
            node1.master_priority = 1
            result = node1.deploy(master_host_settings)
            return result
            
           


