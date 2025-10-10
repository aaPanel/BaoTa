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
import sys
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
#from mod.project.backup_restore.data_manager import DataManager
from mod.project.backup_restore.config_manager import ConfigManager


def get_plugin_object():
    import PluginLoader
    from panelPlugin import panelPlugin

    p = panelPlugin()
    soft_list = PluginLoader.get_plugin_list(0)
    setattr(p, "_panelPlugin__plugin_s_list", panelPlugin.set_coexist(None, soft_list["list"]))
    return p


class PluginModule(BaseUtil,ConfigManager):
    def __init__(self):
        self.base_path = '/www/backup/backup_restore'
        self.bakcup_task_json = self.base_path + '/backup_task.json'
        self.plugin_path = '/www/server/panel/plugin'

    def backup_plugin_data(self,timestamp):
        self.print_log("====================================================","backup")
        self.print_log("开始备份插件数据","backup")

        backup_path=self.base_path + "/{timestamp}_backup/plugin".format(timestamp=timestamp)
        if not os.path.exists(backup_path):
            public.ExecShell('mkdir -p {}'.format(backup_path))
    
        plugin_info = {}
        btwaf_path=os.path.join(self.plugin_path,"btwaf")
        monitor_path=os.path.join(self.plugin_path,"monitor")   
        tamper_core_path=os.path.join(self.plugin_path,"tamper_core")
        syssafe_path=os.path.join(self.plugin_path,"syssafe")

        if os.path.exists(btwaf_path):
            result=self.backup_btwaf_data(timestamp)
            plugin_info['btwaf']=result
        if os.path.exists(monitor_path):
            result=self.backup_monitor_data(timestamp)
            plugin_info['monitor']=result
        if os.path.exists(tamper_core_path):
            result=self.backup_tamper_core_data(timestamp)
            plugin_info['tamper_core']=result
        if os.path.exists(syssafe_path):
            result=self.backup_syssafe_data(timestamp)
            plugin_info['syssafe']=result
        data_list=self.get_backup_data_list(timestamp)
        data_list['data_list']['plugin']=plugin_info
        self.update_backup_data_list(timestamp, data_list)

        
    def backup_btwaf_data(self,timestamp):
        backup_path=self.base_path + "/{timestamp}_backup/plugin/btwaf".format(timestamp=timestamp)
        if not os.path.exists(backup_path):
            public.ExecShell('mkdir -p {}'.format(backup_path))

        try:
            btwaf_info_json=json.loads(public.ReadFile(os.path.join(self.plugin_path,"btwaf","info.json")))
            result={
                "status": 2,
                "err_msg": None,
                "version": btwaf_info_json['versions'],
                "size": self.get_file_size(os.path.join(self.plugin_path,"btwaf"))
            }
        
            public.ExecShell("\cp -rpa /www/server/btwaf/config.json {backup_path}/config.json".format(backup_path=backup_path))
            public.ExecShell("\cp -rpa /www/server/btwaf/site.json {backup_path}/site.json".format(backup_path=backup_path))
            public.ExecShell("\cp -rpa /www/server/btwaf/rule {backup_path}/rule".format(backup_path=backup_path))
            backup_size=self.format_size(self.get_file_size(backup_path))
            self.print_log("nginx防火墙  ✓ ({})".format(backup_size),'backup')
            return result
        except:
            return None
 

    def backup_monitor_data(self,timestamp):
        backup_path=self.base_path + "/{timestamp}_backup/plugin/monitor".format(timestamp=timestamp)
        if not os.path.exists(backup_path):
            public.ExecShell('mkdir -p {}'.format(backup_path))

        try:
            monitor_info_json=json.loads(public.ReadFile(os.path.join(self.plugin_path,"monitor","info.json")))
            result={
                "status": 2,
                "err_msg": None,
                "version": monitor_info_json['versions'],
                "size": self.get_file_size(os.path.join(self.plugin_path,"monitor"))
            }
            if os.path.exists("/www/server/panel/plugin/monitor/site_robots.json"):
                public.ExecShell("\cp -rpa /www/server/panel/plugin/monitor/site_robots.json {backup_path}/site_robots.json".format(backup_path=backup_path))
            if os.path.exists("/www/server/panel/plugin/monitor/site_sitemap_info.json"):
                public.ExecShell("\cp -rpa /www/server/panel/plugin/monitor/site_sitemap_info.json {backup_path}/site_sitemap_info.json".format(backup_path=backup_path))
            if os.path.exists("/www/server/panel/plugin/monitor/spider_api.config"):
                public.ExecShell("\cp -rpa /www/server/panel/plugin/monitor/spider_api.config {backup_path}/spider_api.config".format(backup_path=backup_path))
            if os.path.exists("/www/server/panel/plugin/monitor/baidu_user.config"):
                public.ExecShell("\cp -rpa /www/server/panel/plugin/monitor/baidu_user.config {backup_path}/baidu_user.config".format(backup_path=backup_path))
            if os.path.exists("/www/server/panel/plugin/monitor/360_user.config"):
                public.ExecShell("\cp -rpa /www/server/panel/plugin/monitor/360_user.config {backup_path}/360_user.config".format(backup_path=backup_path))
            public.ExecShell("\cp -rpa /www/server/monitor/config  {backup_path}/config".format(backup_path=backup_path))
            backup_size=self.format_size(self.get_file_size(backup_path))
            self.print_log("网站监控报表  ✓ ({})".format(backup_size),'backup')
            return result
        except:
            return None

    def backup_tamper_core_data(self,timestamp):
        backup_path=self.base_path + "/{timestamp}_backup/plugin/tamper_core".format(timestamp=timestamp)
        if not os.path.exists(backup_path):
            public.ExecShell('mkdir -p {}'.format(backup_path))

        try:
            tamper_core_info_json=json.loads(public.ReadFile(os.path.join(self.plugin_path,"tamper_core","info.json")))
            result={
                "status": 2,
                "err_msg": None,
                "version": tamper_core_info_json['versions'],
                "size": self.get_file_size(os.path.join(self.plugin_path,"tamper_core"))
            }
            public.ExecShell("\cp -rpa /www/server/panel/plugin/tamper_core/tamper_push_template.json {backup_path}/tamper_push_template.json".format(backup_path=backup_path))
            public.ExecShell("\cp -rpa /www/server/panel/plugin/tamper_core/rule.json {backup_path}/rule.json".format(backup_path=backup_path))
            public.ExecShell("\cp -rpa /www/server/tamper/config_ps.json {backup_path}/config_ps.json".format(backup_path=backup_path))
            public.ExecShell("\cp -rpa /www/server/tamper/tamper.conf {backup_path}/tamper.conf".format(backup_path=backup_path))
            backup_size=self.format_size(self.get_file_size(backup_path))
            self.print_log("企业防篡改  ✓ ({})".format(backup_size),'backup')
            return result
        except:
            return None
    
    
    def backup_syssafe_data(self,timestamp):
        backup_path=self.base_path + "/{timestamp}_backup/plugin/syssafe".format(timestamp=timestamp)
        if not os.path.exists(backup_path):
            public.ExecShell('mkdir -p {}'.format(backup_path))

        try:
            syssafe_info_json=json.loads(public.ReadFile(os.path.join(self.plugin_path,"syssafe","info.json")))
            result={
                "status": 2,
                "err_msg": None,
                "version": syssafe_info_json['versions'],
                "size": self.get_file_size(os.path.join(self.plugin_path,"syssafe"))
            }
            public.ExecShell("\cp -rpa /www/server/panel/plugin/syssafe/config.json {backup_path}/config.json".format(backup_path=backup_path))
            public.ExecShell("\cp -rpa /www/server/panel/plugin/syssafe/sys_process.json {backup_path}/sys_process.json".format(backup_path=backup_path))
            public.ExecShell("\cp -rpa /www/server/panel/plugin/syssafe/config {backup_path}/".format(backup_path=backup_path))
            backup_size=self.format_size(self.get_file_size(backup_path))
            self.print_log("系统加固  ✓ ({})".format(backup_size),'backup')
            return result
        except:
            return None
        
    def restore_plugin_data(self,timestamp):
        self.print_log("====================================================","restore")
        self.print_log("开始恢复插件数据","restore")
        self.print_log("如迁移机器未绑定宝塔用户并升级为专业版或企业版，将会出现插件还原失败等情况", "restore")
        
        restore_path=self.base_path + "/{timestamp}_restore/plugin".format(timestamp=timestamp)
        
        restore_data=self.get_restore_data_list(timestamp)
        plugin_info=restore_data['data_list']['plugin']

        if 'btwaf' in plugin_info and plugin_info['btwaf']:
            log_str="开始安装nginx防火墙"
            self.print_log(log_str,"restore")
            restore_data['data_list']['plugin']['btwaf']['restore_status']=1
            self.update_restore_data_list(timestamp,restore_data)
            plugin_version=plugin_info['btwaf']['version']
            install_result=self.install_plugin('btwaf',plugin_version)
            if install_result['status'] == True:
                new_log_str="nginx防火墙 ✓"
                self.replace_log(log_str,new_log_str,"restore")
                log_str="开始还原nginx防火墙数据"
                self.print_log(log_str,"restore")
                self.restore_btwaf_data(timestamp)
                restore_data['data_list']['plugin']['btwaf']['restore_status']=2
                self.update_restore_data_list(timestamp,restore_data)
                new_log_str="nginx防火墙数据 ✓"
                self.replace_log(log_str,new_log_str,"restore")
            else:
                restore_data['data_list']['plugin']['btwaf']['restore_status']=3
                restore_data['data_list']['plugin']['btwaf']['err_msg']=install_result['msg']
                self.update_restore_data_list(timestamp,restore_data)
                new_log_str="nginx防火墙 ✗"
                self.replace_log(log_str,new_log_str,"restore")
        if 'monitor' in plugin_info and plugin_info['monitor']:
            log_str="开始安装网站监控报表"
            self.print_log(log_str,"restore")
            restore_data['data_list']['plugin']['monitor']['restore_status']=1
            self.update_restore_data_list(timestamp,restore_data)
            plugin_version=plugin_info['monitor']['version']
            install_result=self.install_plugin('monitor',plugin_version)
            if install_result['status'] == True:
                new_log_str="网站监控报表 ✓"
                self.replace_log(log_str,new_log_str,"restore")
                log_str="开始还原网站监控报表数据"
                self.print_log(log_str,"restore")
                self.restore_monitor_data(timestamp)
                restore_data['data_list']['plugin']['monitor']['restore_status']=2
                self.update_restore_data_list(timestamp,restore_data)
                new_log_str="网站监控报表数据 ✓"
                self.replace_log(log_str,new_log_str,"restore")
            else:
                restore_data['data_list']['plugin']['monitor']['restore_status']=3
                restore_data['data_list']['plugin']['monitor']['err_msg']=install_result['msg']
                self.update_restore_data_list(timestamp,restore_data)
                new_log_str="网站监控报表 ✗"
                self.replace_log(log_str,new_log_str,"restore")
        if 'tamper_core' in plugin_info and plugin_info['tamper_core']:
            log_str="开始安装企业防篡改"
            self.print_log(log_str,"restore")
            restore_data['data_list']['plugin']['tamper_core']['restore_status']=1
            self.update_restore_data_list(timestamp,restore_data)
            plugin_version=plugin_info['tamper_core']['version']
            install_result=self.install_plugin('tamper_core',plugin_version)
            if install_result['status'] == True:
                public.ExecShell("/etc/init.d/bt-tamper stop")
                new_log_str="企业防篡改 ✓"
                self.replace_log(log_str,new_log_str,"restore")
                log_str="开始还原企业防篡改数据"
                self.print_log(log_str,"restore")
                self.restore_tamper_core_data(timestamp)
                restore_data['data_list']['plugin']['tamper_core']['restore_status']=2
                self.update_restore_data_list(timestamp,restore_data)
                new_log_str="企业防篡改数据 ✓"
                self.replace_log(log_str,new_log_str,"restore")
            else:
                restore_data['data_list']['plugin']['tamper_core']['restore_status']=3
                restore_data['data_list']['plugin']['tamper_core']['err_msg']=install_result['msg']
                self.update_restore_data_list(timestamp,restore_data)
                new_log_str="企业防篡改 ✗"
                self.replace_log(log_str,new_log_str,"restore")
        if 'syssafe' in plugin_info and plugin_info['syssafe']:
            log_str="开始安装系统加固"
            self.print_log(log_str,"restore")
            restore_data['data_list']['plugin']['syssafe']['restore_status']=1
            self.update_restore_data_list(timestamp,restore_data)
            plugin_version=plugin_info['syssafe']['version']
            install_result=self.install_plugin('syssafe',plugin_version)
            if install_result['status'] == True:
                public.ExecShell("/etc/init.d/bt_syssafe stop")
                new_log_str="系统加固 ✓"
                self.replace_log(log_str,new_log_str,"restore")
                log_str="开始还原系统加固数据"
                self.print_log(log_str,"restore")
                self.restore_syssafe_data(timestamp)
                restore_data['data_list']['plugin']['syssafe']['restore_status']=2
                self.update_restore_data_list(timestamp,restore_data)
                new_log_str="系统加固数据 ✓"
                self.replace_log(log_str,new_log_str,"restore")
            else:
                restore_data['data_list']['plugin']['syssafe']['restore_status']=3
                restore_data['data_list']['plugin']['syssafe']['err_msg']=install_result['msg']
                self.update_restore_data_list(timestamp,restore_data)
                new_log_str="系统加固 ✗"
                self.replace_log(log_str,new_log_str,"restore")
        self.print_log("插件数据还原完成","restore")
        
    def restore_btwaf_data(self,timestamp):
        restore_path=self.base_path + "/{timestamp}_backup/plugin/btwaf".format(timestamp=timestamp)
        plugin_path="/www/server/btwaf"
        if  os.path.exists(restore_path) and os.path.exists(plugin_path):
            public.ExecShell("\cp -rpa {restore_path}/config.json /www/server/btwaf/config.json".format(restore_path=restore_path))
            public.ExecShell("\cp -rpa {restore_path}/site.json /www/server/btwaf/site.json".format(restore_path=restore_path))
            public.ExecShell("\cp -rpa {restore_path}/rule/* /www/server/btwaf/rule".format(restore_path=restore_path))

    def restore_monitor_data(self,timestamp):
        restore_path=self.base_path + "/{timestamp}_backup/plugin/monitor".format(timestamp=timestamp)
        plugin_path="/www/server/panel/plugin/monitor/"
        if  os.path.exists(restore_path) and os.path.exists(plugin_path):
            public.ExecShell("\cp -rpa {restore_path}/site_robots.json /www/server/panel/plugin/monitor/site_robots.json".format(restore_path=restore_path))
            public.ExecShell("\cp -rpa {restore_path}/site_sitemap_info.json /www/server/panel/plugin/monitor/site_sitemap_info.json".format(restore_path=restore_path))
            public.ExecShell("\cp -rpa {restore_path}/spider_api.config /www/server/panel/plugin/monitor/spider_api.config".format(restore_path=restore_path))
            public.ExecShell("\cp -rpa {restore_path}/baidu_user.config /www/server/panel/plugin/monitor/baidu_user.config".format(restore_path=restore_path))
            public.ExecShell("\cp -rpa {restore_path}/360_user.config /www/server/panel/plugin/monitor/360_user.config".format(restore_path=restore_path))
            public.ExecShell("\cp -rpa {restore_path}/config/* /www/server/monitor/config".format(restore_path=restore_path))

    def restore_tamper_core_data(self,timestamp):
        restore_path=self.base_path + "/{timestamp}_backup/plugin/tamper_core".format(timestamp=timestamp)
        plugin_path="/www/server/panel/plugin/tamper_core/"
        if  os.path.exists(restore_path) and os.path.exists(plugin_path):
            public.ExecShell("\cp -rpa {restore_path}/tamper_push_template.json /www/server/panel/plugin/tamper_core/tamper_push_template.json".format(restore_path=restore_path))
            public.ExecShell("\cp -rpa {restore_path}/rule.json /www/server/panel/plugin/tamper_core/rule.json".format(restore_path=restore_path))
            public.ExecShell("\cp -rpa {restore_path}/config_ps.json /www/server/tamper/config_ps.json".format(restore_path=restore_path))
            public.ExecShell("\cp -rpa {restore_path}/tamper.conf /www/server/tamper/tamper.conf".format(restore_path=restore_path))
            public.ExecShell("/etc/init.d/bt-tamper stop")

    def restore_syssafe_data(self,timestamp):
        restore_path=self.base_path + "/{timestamp}_backup/plugin/syssafe".format(timestamp=timestamp)
        plugin_path="/www/server/panel/plugin/syssafe/"
        if  os.path.exists(restore_path) and os.path.exists(plugin_path):
            public.ExecShell("\cp -rpa {restore_path}/config.json /www/server/panel/plugin/syssafe/config.json".format(restore_path=restore_path))
            public.ExecShell("\cp -rpa {restore_path}/sys_process.json /www/server/panel/plugin/syssafe/sys_process.json".format(restore_path=restore_path))
            public.ExecShell("\cp -rpa {restore_path}/config/* /www/server/panel/plugin/syssafe/config".format(restore_path=restore_path))
            public.ExecShell("/etc/init.d/bt_syssafe stop")

        
    def install_plugin(self,sName,plugin_version):
        # import PluginLoader
        # import panelPlugin
        # plugin = panelPlugin.panelPlugin()
        try:
            plugin = get_plugin_object()
            sName=sName
            version_parts = plugin_version.split(".", 1)
            sVersion = version_parts[0]
            sMin_version = version_parts[1] if len(version_parts) > 1 else ""
            get = public.dict_obj()
            get.sName = sName
            get.version = sVersion
            get.min_version = sMin_version
            info = plugin.install_plugin(get)
            
            args = public.dict_obj()
            args.tmp_path = info['tmp_path']
            args.plugin_name = sName
            args.install_opt = info['install_opt']
            info = plugin.input_package(args)
            return info
        except:
            return {
                'status': False,
                'msg': '安装失败'
            }
    
if __name__ == '__main__':
    # 获取命令行参数
    if len(sys.argv) < 2:
        print("Usage: btpython backup_manager.py <method> <timestamp>")
        sys.exit(1)
    method_name = sys.argv[1]  # 方法名  
    timestamp = sys.argv[2]
    plugin_manager = PluginModule()  # 实例化对象
    if hasattr(plugin_manager, method_name):  # 检查方法是否存在
        method = getattr(plugin_manager, method_name)  # 获取方法
        method(timestamp)  # 调用方法
    else:
        print(f"Error: 方法 '{method_name}' 不存在")