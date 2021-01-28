#!/usr/bin/python
# coding: utf-8
"""

author: linxiao
date: 2021/1/23 18:07
"""

from colony import mysql
from colony import dbnode
import public 

import json


class dbmanager:

    __nodes = []

    def __get_deploy_settings(self):
        settings = json.loads(public.ReadFile("colony/deploy.conf"))
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

            master_host_settings['db_manager_user'] = db_manager_user
            master_host_settings['db_replication_user'] = db_replication_user
            
            secondary_host_settings['db_manager_user'] = db_manager_user
            secondary_host_settings['db_replication_user'] = db_replication_user

            node1 = dbnode()
            node1.master_priority = 1
            node1.deploy(master_host_settings)
            
            

    def create_db_user(self, username):
        """创建数据库用户"""
        pass


