# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: miku <miku@bt.cn>
# -------------------------------------------------------------------
import json
import os
import sys
import time
import concurrent.futures
import threading
import hashlib
import datetime
import re

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

if '/www/server/panel' not in sys.path:
    sys.path.insert(0, '/www/server/panel')


import public
from mod.project.backup_restore.base_util import BaseUtil
from mod.project.backup_restore.data_manager import DataManager
from mod.project.backup_restore.config_manager import ConfigManager


class PanelConfigModule(DataManager,BaseUtil,ConfigManager):
    def __init__(self):
        self.base_path = '/www/backup/backup_restore'
        self.bakcup_task_json = self.base_path + '/backup_task.json'
        self.panel_asset_config = '/www/server/panel/data/panel_asset.json'
        self.panel_path = '/www/server/panel'
        self.panel_run_path = self.panel_path + '/BTPanel'
        self.panel_static_temp_path = self.panel_run_path + '/static/temp'
        self.mail_config = self.panel_path + '/data/stmp_mail.json'
        self.push_data= self.panel_path + '/data/mod_push_data'

    def backup_panel_config_data(self,timestamp):
        self.print_log("==================================","backup")
        self.print_log("开始备份面板设置数据","backup")

        backup_path = self.base_path + "/{timestamp}_backup/panel_config".format(timestamp=timestamp)
        if not os.path.exists(backup_path):
            public.ExecShell('mkdir -p {}'.format(backup_path))

        #备份面板UI设置
        if os.path.exists(self.panel_asset_config):
            public.ExecShell("\cp -rpa {} {}".format(self.panel_asset_config,backup_path))
            asset_config_data=json.loads(public.ReadFile(self.panel_asset_config))
            try:
                asset_items = ['favicon', 'login_bg_images', 'main_bg_images', 'menu_logo']
                for img_item in asset_items:
                    if asset_config_data.get(img_item) and asset_config_data[img_item] != "":
                        public.ExecShell("\cp -rpa {}/{} {}".format(self.panel_run_path, asset_config_data[img_item], backup_path))
            except:
                pass

        #备份面板邮件配置
        if os.path.exists(self.mail_config):
            public.ExecShell("\cp -rpa {} {}".format(self.mail_config,backup_path))

        #备份面板告警配置
        if os.path.exists(self.push_data):
            public.ExecShell("\cp -rpa {} {}".format(self.push_data,backup_path))

        #备份面板标题
        if os.path.exists(self.panel_path + "/data/title.pl"):
            public.ExecShell("\cp -rpa {} {}".format(self.panel_path + "/data/title.pl",backup_path))
        
        #备份面板debug状态
        if os.path.exists(self.panel_path + "/data/debug.pl"):
            public.ExecShell("\cp -rpa {} {}".format(self.panel_path + "/data/debug.pl",backup_path))

        #备份面板离线模式
        if os.path.exists(self.panel_path + "/data/not_network.pl"):
            public.ExecShell("\cp -rpa {} {}".format(self.panel_path + "/data/not_network.pl",backup_path))

        #备份面板菜单
        if os.path.exists(self.panel_path + "/config/menu.json"):
            public.ExecShell("\cp -rpa {} {}".format(self.panel_path + "/config/menu.json",backup_path))

        #备份常用登录地区
        if os.path.exists(self.panel_path + "/data/panel_login_area.json"):
            public.ExecShell("\cp -rpa {} {}".format(self.panel_path + "/data/panel_login_area.json",backup_path))

        #备份登录白名单
        if os.path.exists(self.panel_path + "/data/send_login_white.json"):
            public.ExecShell("\cp -rpa {} {}".format(self.panel_path + "/data/send_login_white.json",backup_path))

        #备份登录限制
        if os.path.exists(self.panel_path + "/data/limit_area.json"):
            public.ExecShell("\cp -rpa {} {}".format(self.panel_path + "/data/limit_area.json",backup_path))

        #备份备忘录
        if os.path.exists(self.panel_path + "/data/memo.txt"):
            public.ExecShell("\cp -rpa {} {}".format(self.panel_path + "/data/memo.txt",backup_path))

        #备份UA限制
        if os.path.exists(self.panel_path + "/class/limitua.json"):
            public.ExecShell("\cp -rpa {} {}".format(self.panel_path + "/class/limitua.json",backup_path))

        #备份域名
        if os.path.exists(self.panel_path + "/data/domain.conf"):
            public.ExecShell("\cp -rpa {} {}".format(self.panel_path + "/data/domain.conf",backup_path))

        self.print_log("面板设置数据备份完成","backup")
        return True
    
    def restore_panel_config_data(self,timestamp):
        self.print_log("==================================","restore")
        self.print_log("开始恢复面板设置数据","restore")

        backup_path = self.base_path + "/{timestamp}_backup/panel_config".format(timestamp=timestamp)
        if not os.path.exists(backup_path):
            self.print_log("面板设置备份文件不存在","restore")

        backup_path = self.base_path + "/{timestamp}_backup/panel_config".format(timestamp=timestamp)

        #还原面板UI设置
        if os.path.exists(backup_path + "/panel_asset.json"):
            public.ExecShell("mkdir -p {}".format(self.panel_static_temp_path))
            asset_config_data=json.loads(public.ReadFile(backup_path + "/panel_asset.json"))
            try:
                asset_items = ['favicon', 'login_bg_images', 'main_bg_images', 'menu_logo']
                for img_item in asset_items:
                    if asset_config_data.get(img_item) and asset_config_data[img_item] != "":
                        img_base_path = os.path.basename(asset_config_data[img_item])
                        cmd = "\cp -rpa {} {}".format(backup_path + "/" + img_base_path,self.panel_static_temp_path)
                        public.ExecShell(cmd)
                public.ExecShell("\cp -rpa {} {}".format(backup_path + "/panel_asset.json",self.panel_asset_config))
            except:
                pass

        #还原面板邮件配置
        if os.path.exists(backup_path + "/stmp_mail.json"):
            public.ExecShell("\cp -rpa {} {}".format(backup_path + "/stmp_mail.json",self.mail_config))

        #还原面板告警配置
        if os.path.exists(backup_path + "/mod_push_data"):
            if os.path.exists(self.push_data):
                public.ExecShell("\cp -rpa {}/* {}".format(backup_path + "/mod_push_data",self.push_data))
            else:
                public.ExecShell("mkdir -p {}".format(self.push_data))
                public.ExecShell("\cp -rpa {}/* {}".format(backup_path + "/mod_push_data",self.push_data))

        #还原面板标题
        if os.path.exists(backup_path + "/title.pl"):
            public.ExecShell("\cp -rpa {} {}".format(backup_path + "/title.pl",self.panel_path + "/data/title.pl"))

        #还原面板debug状态
        if os.path.exists(backup_path + "/debug.pl"):
            public.ExecShell("\cp -rpa {} {}".format(backup_path + "/debug.pl",self.panel_path + "/data/debug.pl"))

        #还原面板离线模式
        if os.path.exists(backup_path + "/not_network.pl"):
            public.ExecShell("\cp -rpa {} {}".format(backup_path + "/not_network.pl",self.panel_path + "/data/not_network.pl"))

        #还原面板菜单
        if os.path.exists(backup_path + "/menu.json"):
            public.ExecShell("\cp -rpa {} {}".format(backup_path + "/menu.json",self.panel_path + "/config/menu.json"))

        #还原常用登录地区
        if os.path.exists(backup_path + "/panel_login_area.json"):
            public.ExecShell("\cp -rpa {} {}".format(backup_path + "/panel_login_area.json",self.panel_path + "/data/panel_login_area.json"))

        #还原登录白名单
        if os.path.exists(backup_path + "/send_login_white.json"):
            public.ExecShell("\cp -rpa {} {}".format(backup_path + "/send_login_white.json",self.panel_path + "/data/send_login_white.json"))

        #还原登录限制
        if os.path.exists(backup_path + "/limit_area.json"):
            public.ExecShell("\cp -rpa {} {}".format(backup_path + "/limit_area.json",self.panel_path + "/data/limit_area.json"))

        #还原备忘录
        if os.path.exists(backup_path + "/memo.txt"):
            public.ExecShell("\cp -rpa {} {}".format(backup_path + "/memo.txt",self.panel_path + "/data/memo.txt"))

        #还原UA限制
        if os.path.exists(backup_path + "/limitua.json"):
            public.ExecShell("\cp -rpa {} {}".format(backup_path + "/limitua.json",self.panel_path + "/class/limitua.json"))

        #还原域名
        if os.path.exists(backup_path + "/domain.conf"):
            public.ExecShell("\cp -rpa {} {}".format(backup_path + "/domain.conf",self.panel_path + "/data/domain.conf"))
        

if __name__ == '__main__':
    # 获取命令行参数
    if len(sys.argv) < 3:
        print("Usage: btpython backup_manager.py <method> <timestamp>")
        sys.exit(1)
    method_name = sys.argv[1]  # 方法名
    timestamp = sys.argv[2]    # IP地址     
    panel_config_module = PanelConfigModule()  # 实例化对象
    if hasattr(panel_config_module, method_name):  # 检查方法是否存在
        method = getattr(panel_config_module, method_name)  # 获取方法
        method(timestamp)  # 调用方法
    else:
        print(f"Error: 方法 '{method_name}' 不存在")