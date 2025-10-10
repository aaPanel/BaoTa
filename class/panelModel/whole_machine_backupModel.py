# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: sww <sww@bt.cn>
# -------------------------------------------------------------------

# 备份
# ------------------------------
import datetime
import json
import os
import time
import sys
import concurrent.futures
import threading
import hashlib

if '/www/server/panel/class' not in sys.path:
    sys.path.insert(0, '/www/server/panel/class')
if '/www/server/panel' not in sys.path:
    sys.path.insert(0, '/www/server/panel')
import public
import panelMysql
import db_mysql
import database
import psutil
import ajax
from firewallModel.comModel import main as firewall_main
from safeModel.firewallModel import main as safe_firewall_main
from CloudStoraUpload import CloudStoraUpload  # 引入云存储上传模块


class main:
    sys_config = public.M('config').where("id=1", ()).find()
    setting_path='{}/data/whole_machine_backup_settings.json'.format(public.get_panel_path()) 
    if os.path.exists(setting_path):
        sys_backup_path = json.loads(public.ReadFile(setting_path))['sys_backup_path']
    else:
        sys_backup_path = '/www/backup/'
        if sys_config and sys_config.get('backup_path'):
            sys_backup_path = sys_config.get('backup_path')
            sys_backup_path = sys_backup_path if sys_backup_path.endswith('/') else sys_backup_path + '/'
    backup_path = '{}whole_machine_backup/'.format(sys_backup_path)
    backup_log_path = '{}log/'.format(backup_path)
    all_backup_config_path = os.path.join(public.get_panel_path(), 'config/whole_machine_backup.json')
    time_str = public.format_date()
    lock = None
    executor = None
    functions = []
    backup_config = {}
    reduction_config = {}
    backup_save_config = backup_path + '{}/backup.json'
    id_config = None
    backup_record = None
    reduction_log_path = None
    backup_task_data = None
    logs_file = '{}whole_machine_backup.log'.format(backup_path)
    status = None
    error_num = 0
    access_num = 0

    def __init__(self):
        if not os.path.exists(self.backup_path):
            public.ExecShell("mkdir -p {}".format(self.backup_path))
            public.ExecShell("chmod -R 755 {}".format(self.backup_path))
            public.ExecShell("chown -R www:www {}".format(self.backup_path))
        if not os.path.exists(self.all_backup_config_path):
            public.writeFile(self.all_backup_config_path, json.dumps({}))
        self.config = json.loads(public.readFile(self.all_backup_config_path))

    def print_log(self, log: str):
        time_str = time.strftime('%Y-%m-%d %H:%M:%S')
        log = "{} $$ {}".format(time_str, log)
        public.writeFile(self.logs_file, log + "\n", 'a+')

    def write_config(self, id, conf):
        self.config[id] = conf
        public.writeFile(self.all_backup_config_path, json.dumps(self.config))

    def get_md5(self, path):
        try:
            if os.path.exists(path) and os.path.isfile(path):
                return public.FileMd5(path)
            return False
        except:
            return False

    # ======================================================================
    #     交互层级
    # ======================================================================

    # 获取恢复对比列表

    # 获取备份任务列表
    def get_task_list(self, get=None):
        try:
            if not hasattr(get, 'page') or get.page == '':
                get.page = 1
            if not hasattr(get, 'limit') or get.limit == '':
                get.limit = 10
            get.page, get.limit = int(get.page), int(get.limit)
            result = []
            ids = ['log']
            for k, v in self.config.items():
                info = {'id': k}
                ids.append(k)
                info.update(v)
                info['backup_path'] = info['backup_path'] + '.tar.gz'
                result.append(info)
            for i in os.listdir(self.backup_path):
                if os.path.isdir(os.path.join(self.backup_path, i)) and i not in ids:
                    public.ExecShell('rm -rf {}'.format(os.path.join(self.backup_path, i)))
            result = sorted(result, key=lambda x: x['addtime'], reverse=True)
            # 做分页处理
            data = public.get_page(len(result), get.page, get.limit)
            data['data'] = result[get.page * get.limit - get.limit:get.page * get.limit]
            return public.returnMsg(True, data)
        except:
            self.print_log(public.get_error_info())
            return public.returnMsg(False, '获取任务列表失败！')

    # 获取任务信息
    def get_task_info(self, get):
        if not hasattr(get, 'id'):
            return public.returnMsg(False, '参数错误,缺少参数id！')
        if get.id not in self.config:
            return public.returnMsg(False, '任务不存在！')
        task_config_path = self.config[get.id]["task_config"]
        try:
            task_config = json.loads(public.readFile(task_config_path))
            if isinstance(task_config['backup_config'], str):
                task_config['backup_config'] = json.loads(task_config['backup_config'])
            if isinstance(task_config['reduction_config'], str):
                task_config['reduction_config'] = json.loads(task_config['reduction_config'])
        except:
            return public.returnMsg(False, '任务配置文件读取失败！')
        return public.returnMsg(True, task_config)

    # 删除任务
    def del_task(self, get):
        if not hasattr(get, 'id'):
            return public.returnMsg(False, '参数错误,缺少参数id！')
        if get.id not in self.config:
            return public.returnMsg(False, '任务不存在！')
        if "task_id" in self.config[get.id]:
            count = public.M('tasks').where("id=? nd status!='1'", (self.config[get.id]["task_id"],)).count()
            if count:
                return public.returnMsg(False, '任务正在执行中，请等待执行结束后再删除！')
        del self.config[get.id]
        public.ExecShell("rm -rf {}*".format(os.path.join(self.backup_path, get.id)))
        public.ExecShell("rm -rf {}".format(os.path.join(self.backup_log_path, get.id + "_backup.log")))
        public.ExecShell("rm -rf {}".format(os.path.join(self.backup_log_path, get.id + "_reduction.log")))
        public.writeFile(self.all_backup_config_path, json.dumps(self.config))
        return public.returnMsg(True, '删除成功！')

    # 获取备份日志
    def get_backup_log(self, get):
        if not hasattr(get, 'id'):
            return public.returnMsg(False, '参数错误,缺少参数id！')
        if get.id not in self.config:
            return public.returnMsg(False, '任务不存在,请刷新后重试！！')
        backup_log_path = self.config[get.id]["backup_log_path"]
        if not os.path.exists(backup_log_path):
            return public.returnMsg(False, '未检测到日志！')
        log = public.readFile(backup_log_path)
        if log:
            try:
                log = json.loads(log)
                return public.returnMsg(True, log)
            except:
                pass
        return public.returnMsg(False, "日志格式话出错！")

    # 获取还原日志
    def get_reduction_log(self, get):
        if not hasattr(get, 'id'):
            return public.returnMsg(False, '参数错误,缺少参数id！')
        if get.id not in self.config:
            return public.returnMsg(False, '任务不存在,请刷新后重试！')
        reduction_log_path = self.config[get.id]["reduction_log_path"]
        if not os.path.exists(reduction_log_path):
            return public.returnMsg(False, '未检测到日志！')
        log = public.readFile(reduction_log_path)
        if log:
            try:
                log = json.loads(log)
                return public.returnMsg(True, log)
            except:
                pass
        return public.returnMsg(False, "日志格式话出错！")

    # 获取备份数据列表
    def get_data_list(self, get):
        """
        获取备份数据列表
        :param get:
        """
        result = {}
        # 环境备份列表
        result["env_list"] = self.get_env_list()
        # 数据备份列表
        result["data_list"] = {}
        result["data_list"]["site_list"] = self.get_site_list()
        result["data_list"]["sql_list"] = self.get_sql_list()
        result["data_list"]["ftp_list"] = self.get_ftp_list()
        result["data_list"]["terminal_list"] = self.get_terminal_list()
        result["data_list"]["crontab_list"] = self.get_crontab_list()
        result["data_list"]['safety'] = {
            "port_list": [{"name": "端口规则", "status": 1, "backup_status": 0, "reduction_status": 0}],
            "ip_list": [{"name": "IP规则", "status": 1, "backup_status": 0, "reduction_status": 0}],
            "port_redirect": [{"name": "端口转发", "status": 1, "backup_status": 0, "reduction_status": 0}],
            "area_list": [{"name": "地区规则", "status": 1, "backup_status": 0, "reduction_status": 0}],
            "ssh_config": [{"name": "ssh配置", "status": 1, "backup_status": 0, "reduction_status": 0}],
            'words': [{"name": "违规词检测-关键词", "status": 1, "backup_status": 0, "reduction_status": 0}],
        }
        # 配置备份列表
        # result["config_list"] = self.get_config_list()
        return result

    def get_site_list(self):
        """
        获取站点列表
        :return:    dict
        """
        # result = {'php': [], 'proxy': [], 'java': [], 'node': [], 'go': [], 'python': [], 'net': [], 'html': [], 'other': []}
        result = {'php': [], 'proxy': []}
        # now_list = ['php', 'proxy']
        data = public.M('sites').field('name,project_type,id,ps').select()
        if isinstance(data, str):
            return {}
        for i in data:
            if i['project_type'].lower() not in result.keys():
                continue
            result[i['project_type'].lower()].append({"name": i['name'], "status": 1, "backup_status": 0, "reduction_status": 0, "id": i['id'], 'ps': i['ps']})
        cont = [i for i, j in result.items() if not j]
        [result.pop(i) for i in cont]
        return result

    def get_sql_list(self):
        """
        获取数据库列表
        :return:    dict
        """
        result = {}
        data = public.M('databases').field('name,type,id').select()
        result['mysql'] = []
        if isinstance(data, str):
            return {}
        for i in data:
            if i['type'].lower() not in result:
                continue
            if i['type'].lower() in ['mysql']:
                result[i['type'].lower()].append({"name": i['name'], "status": 1, "backup_status": 0, "reduction_status": 0, "id": i['id']})
            # else:
            #     result[i['type'].lower()].append({"name": i['name'], "status": 3, "backup_status": 0, "reduction_status": 0, "id": i['id']})
        # result['redis'] = [{"name": "redis", "status": 3, "backup_status": 0, "reduction_status": 0}]
        # result['sqlite'] = []
        # db_file_path = '{}/data/db_model.json'.format(public.get_panel_path())
        # if os.path.exists(db_file_path):
        #     db_data = json.loads(public.readFile(db_file_path))
        #     for i in db_data:
        #         result['sqlite'].append({"name": os.path.basename(i), "status": 3, "backup_status": 0, "reduction_status": 0})
        return result

    def get_ftp_list(self):
        """
        获取ftp列表
        :return:    list
        """
        result = []
        data = public.M('ftps').field('name,id').select()
        if isinstance(data, str):
            return []
        for i in data:
            result.append({"name": i['name'], "status": 1, "backup_status": 0, "reduction_status": 0, "id": i['id']})
        return result

    def get_env_list(self):
        result = {}
        # 获取web服务状态
        web_type = public.get_webserver()
        if web_type == 'nginx':
            web_setup = os.path.exists('/www/server/nginx')
            web_version = public.readFile('/www/server/nginx/version.pl').strip() if web_setup else ""
        elif web_type == 'apache':
            web_setup = os.path.exists('/www/server/apache')
            web_version = public.readFile('/www/server/apache/version.pl').strip() if web_setup else ""
        else:
            web_setup = False
            web_version = ""
        result[web_type] = [{"setup": web_setup, "name": web_version, "status": 1 if web_setup else 0, "backup_status": 0, "reduction_status": 0}]

        # 获取数据库版本,及安装状态
        mysql_path = "/www/server/mysql"
        mysql_setup = os.path.exists(mysql_path)
        mysql_version = public.readFile(mysql_path + "/version.pl").strip() if mysql_setup else ""
        result['mysql'] = [{"setup": mysql_setup, "name": mysql_version, "status": 1 if mysql_setup else 0, "backup_status": 0, "reduction_status": 0, "primitive_data": "0"}]

        # 获取 ftp 服务状态
        ftp_path = "/www/server/pure-ftpd"
        ftp_setup = os.path.exists(ftp_path)
        ftp_version = public.readFile(ftp_path + "/version.pl").strip() if ftp_setup else ""
        result['ftp'] = [{"setup": ftp_setup, "name": ftp_version, "status": 1 if ftp_setup else 0, "backup_status": 0, "reduction_status": 0}]

        # 获取php版本
        php_path = "/www/server/php"
        php_list = ['52', '53', '54', '55', '56', '70', '71', '72', '73', '74', '80', '81', '82', '83']
        for i in php_list:
            if 'php' not in result:
                result['php'] = []
            try:
                int(i)
                result['php'].append({"name": i, "status": 1 if os.path.exists('/www/server/php/{}/bin'.format(i)) else 0, "backup_status": 0, "reduction_status": 0,
                                      'setup': os.path.exists('/www/server/php/{}/bin'.format(i))})
            except:
                pass
        # mongo_path = "/www/server/mongodb"
        # mongo_setup = os.path.exists(mongo_path)
        # mongo_version = public.readFile(mongo_path + "/version.pl").strip() if mongo_setup else ""
        # result['mongo'] = [{"setup": mongo_setup, "name": mongo_version, "status": 3, "backup_status": 0, "reduction_status": 0}]
        #
        # redis_path = "/www/server/redis"
        # redis_setup = os.path.exists(redis_path)
        # redis_version = public.readFile(redis_path + "/version.pl").strip() if redis_setup else ""
        # result['redis'] = [{"setup": redis_setup, "name": redis_version, "status": 3, "backup_status": 0, "reduction_status": 0}]
        #
        # pgsql_path = "/www/server/pgsql"
        # pgsql_setup = os.path.exists(pgsql_path)
        # pgsql_version = public.readFile(pgsql_path + "/data/PG_VERSION").strip() if pgsql_setup else ""
        # result['pgsql'] = [{"setup": pgsql_setup, "name": pgsql_version, "status": 3, "backup_status": 0, "reduction_status": 0}]
        # result['python'] = [{"setup": False, "name": '', "status": 3, "backup_status": 0, "reduction_status": 0}]
        # result['java'] = [{"setup": False, "name": '', "status": 3, "backup_status": 0, "reduction_status": 0}]
        # result['node'] = [{"setup": False, "name": '', "status": 3, "backup_status": 0, "reduction_status": 0}]
        # result['.net'] = [{"setup": False, "name": '', "status": 3, "backup_status": 0, "reduction_status": 0}]
        # result['tomcat'] = [{"setup": False, "name": '', "status": 3, "backup_status": 0, "reduction_status": 0}]

        return result

    def get_config_list(self):
        result = {"alarm": [{"name": "面板告警", "status": 3, "backup_status": 0, "reduction_status": 0}], }
        return result

    def get_terminal_list(self):
        result = []
        result.append({"name": "服务器列表", "status": 1, "backup_status": 0, "reduction_status": 0})
        result.append({"name": "常用命令", "status": 1, "backup_status": 0, "reduction_status": 0})
        return result

    def get_crontab_list(self):
        result = []
        result.append({"name": "计划任务列表", "status": 1, "backup_status": 0, "reduction_status": 0})
        return result

    # ======================================================================
    #     创建任务
    # ======================================================================

    def create_task(self, get):
        """
        创建备份任务
        :param get:
        type: 1:备份 2还原
        id: 还原配置id
        conf: 备份配置信息
        :return:
        """
        if not hasattr(get, 'type'):
            return public.returnMsg(False, '参数错误,缺少参数type！')
        if not hasattr(get, 'id') and get.type == '2' and not hasattr(get, 'reduction_config'):
            return public.returnMsg(False, '参数错误,缺少参数reduction_config或id！')
        if get.type == '1' and not hasattr(get, 'backup_config'):
            return public.returnMsg(False, '参数错误,缺少参数backup_config！')
        if not hasattr(get, "backup_type") or get.backup_type == "":
            get.backup_type = "整机备份"
        if not hasattr(get, "next_exec_time") or get.next_exec_time == "":
            get.next_exec_time = "0"
        # get.storage_type="ftp"
        # 设置存储类型，默认为 "local"
        storage_type = get.storage_type if hasattr(get, 'storage_type') else 'local'
        if get.type == '2' and storage_type !='local':
           return public.returnMsg(False, '暂时不还原云存储文件！')

        try:
            # 根据任务类型设置任务名称
            if get.type == '1':
                name = "备份任务"
            else:
                name = "还原任务"

            # 检查是否存在重复任务（同名任务且未完成）
            task_data = public.M('tasks').where("name = ? AND status != ?", ("{}".format(name), "1")).find()
            if task_data:
                return public.returnMsg(False, '已有重复的任务了，请上一个备份任务执行完成后再进行添加新的备份任务！')

            # 初始化任务参数
            get.type = get.type if hasattr(get, 'type') else '1'
            get.backup_sql_time = int(get.backup_sql_time) if hasattr(get, 'backup_sql_time') else 0

            if int(get.type) == 1:  # 备份任务
                if get.next_exec_time not in [0, '0']:
                    exec_time=datetime.datetime.fromtimestamp(int(get.next_exec_time)).strftime("%Y-%m-%d %H:%M:%S")
                else:
                    exec_time="暂未执行"
                # 确保 backup_config 为 JSON 格式
                get.backup_config = get.backup_config if isinstance(get.backup_config, str) else json.dumps(get.backup_config)

                # 生成唯一任务 ID
                get.id = public.GetRandomString(16)

                # 设置任务相关文件路径
                task_config_path = os.path.join(self.backup_path, get.id, "task_config.json")
                reduction_task_config_path = os.path.join(self.backup_path, get.id + "_reduction.json")
                storage_backup_path=""
                if storage_type !='local':
                    name="{}.tar.gz".format(get.id)
                    cloud_name=get.storage_type
                    import CloudStoraUpload
                    c = CloudStoraUpload.CloudStoraUpload()
                    c.run(cloud_name)
                    url = ''
                    backup_path = c.obj.backup_path
                    storage_backup_path = os.path.join(backup_path, "whole_machine_backup",name)

                
                # 定义任务配置
                conf = {
                    "backup_sql_time": get.backup_sql_time,
                    "addtime": time.strftime('%Y-%m-%d %H:%M:%S'),
                    "backup_path": os.path.join(self.backup_path, get.id),
                    "backup_log_path": os.path.join(self.backup_log_path, get.id + "_backup.log"),
                    "reduction_log_path": os.path.join(self.backup_log_path, get.id + "_reduction.log"),
                    "status": 0,  # -1 备份中 0 等待备份 1 备份完成 2 备份失败 3 还原中 4 还原完成 5 还原失败
                    "task_config": task_config_path,
                    "reduction_task_config_path": reduction_task_config_path,
                    "exec_time": exec_time,
                    "backup_type": get.backup_type,
                    "name": get.get('name', get.backup_type),
                    "storage_type":storage_type,
                    "storage_backup_path":storage_backup_path
                }
                # 创建备份任务目录
                if not os.path.exists(os.path.join(self.backup_path, get.id)):
                    public.ExecShell("mkdir -p {}".format(os.path.join(self.backup_path, get.id)))

                # 写入任务配置文件
                task_config = {
                    "backup_config": get.backup_config,
                    "reduction_config": {}
                }
                public.writeFile(task_config_path, json.dumps(task_config))

                # 将任务配置写入全局配置
                self.write_config(get.id, conf)

                # 如果设置了定时执行时间，加入定时任务
                if get.next_exec_time not in [0, '0']:
                    data = {
                        "name": 'whole_machine_backup',
                        "title": '面板数据备份',
                        "type": "1",
                        "time": str(int(get.next_exec_time) + 10),
                        "fun": 'create_queue',
                        "args": {"id": get.id, "type": 1},
                        "model_index": "panel"
                    }
                    public.set_tasks_run(data)
                else:
                    # 立即加入任务队列
                    self.create_queue(public.to_dict_obj({"id": get.id, "type": 1}))

            elif int(get.type) == 2:  # 还原任务
                # 检查还原任务是否存在
                if get.id not in self.config:
                    return public.returnMsg(False, '还原配置不存在,请刷新后重试！')

                # 设置还原任务配置路径
                reduction_task_config_path = os.path.join(self.backup_path, get.id + "_reduction.json")

                # 写入还原配置文件
                reduction_config = get.reduction_config
                task_config = {"reduction_config": reduction_config}
                public.writeFile(reduction_task_config_path, json.dumps(task_config))

                # 加入还原任务队列
                self.create_queue(public.to_dict_obj({"id": get.id, "type": 2}))

            return public.returnMsg(True, '添加成功！')

        except:
            # 捕获异常，记录错误日志并返回失败消息
            self.print_log(public.get_error_info())
            return public.returnMsg(False, '添加任务报错了！')

    def check_plugins(self, get):
        import PluginLoader
        """
        检查指定目录下是否存在某些插件目录，并判断对应存储是否安装

        :param plugin_path: 插件目录的路径，例如 "/www/server/panel/plugin"
        :return: 一个字典，包含每个插件的安装状态
        """
        import os

        plugin_path = "{}/plugin".format(public.get_panel_path())
        # 定义需要检查的插件
        plugins = ["alioss", "txcos", "ftp", "qiniu","webdav"]

        # 初始化结果字典
        result = {}

        # 检查插件目录
        for plugin in plugins:
            plugin_dir = os.path.join(plugin_path, plugin)

            # 初始化插件信息
            result[plugin] = {
                "install": os.path.exists(plugin_dir),  # 插件目录是否存在
                "config": False                         # 默认 config 为 False
            }

            # 检查配置状态
            if result[plugin]["install"]:
                try:
                    
                    get.path = "/"
                    if plugin == "webdav":
                        res = PluginLoader.plugin_run(plugin, "list_files", get)
                        if not "status" in res:
                            print(res)
                            result[plugin]["config"] = True
                    else:
                        res = PluginLoader.plugin_run(plugin, "get_list", get)
                        if "list" in res and "list":
                            result[plugin]["config"] = True
                    # if not "status" in res:
                    #     print(res)
                    #     result[plugin]["config"] = True
                except Exception as e:
                    
                    result[plugin]["config"] = False

        return public.returnMsg(True, result)

    def delete_account(self, get):
        storage_type=get.storage_type
        panel_path=public.get_panel_path()
        plugin_path = "{}/plugin".format(panel_path)
        config_path = os.path.join(plugin_path, storage_type,"config.conf")
        aes_status_path = os.path.join(plugin_path, storage_type,"aes_status")
        data_path=os.path.join("{}/data".format(panel_path),"{}AS.conf".format(storage_type))
        # # 检查 aes_status 文件内容
        # if os.path.exists(config_path):
        public.ExecShell("rm -rf {}".format(config_path))
        public.ExecShell("rm -rf {}".format(aes_status_path))
        public.ExecShell("rm -rf {}".format(data_path))
        return public.returnMsg(True, "删除账号成功！")


    def backup_download(self, get):
        if not hasattr(get, 'backup_path') or not hasattr(get, 'storage_type'):
            return public.returnMsg(False, '请传入backup_path!')
        # 调用 check_plugins 检查云存储插件状态
        plugin_status = self.check_plugins(get)["msg"]
        storage_type = get.storage_type       
        if storage_type not in ["alioss", "txcos", "ftp", "qiniu", "webdav","local"]:
            return public.returnMsg(False, "不支持该插件：{}".format(storage_type))
        if storage_type in plugin_status:
            if not plugin_status[storage_type]["install"]:
                return public.returnMsg(False, "请先安装{}存储插件！".format(storage_type))
            if not plugin_status[storage_type]["config"]:
                return public.returnMsg(False, "{}存储插件未配置，请先配置！".format(storage_type))

        backup_path=get.backup_path
        if get.storage_type=="webdav" or get.storage_type=="local" or get.storage_type=="ftp":
            if get.storage_type=="webdav":
                import sys
                if '/www/server/panel/plugin/webdav' not in sys.path:
                    sys.path.insert(0, '/www/server/panel/plugin/webdav')
                try:
                    from webdav_main import webdav_main as webdav
                    # get.object_name =os.path.join(webdav().default_backup_path , "whole_machine_backup", os.path.basename(backup_path))
                    # self.client.download_file(from_path=download_path, to_path=local_path)
                    download_path=os.path.join(webdav().default_backup_path , "whole_machine_backup",os.path.basename(backup_path))
                    local_path = os.path.join("/tmp", os.path.basename(backup_path))
                    webdav().client.download_file(from_path=download_path, to_path=local_path)
                    path=local_path
                except Exception as e:
                    if "could not be found in the server" in str(e):
                        return public.returnMsg(False, '在云存储中未发现该文件!')
                    return public.returnMsg(False, '请先安装webdav存储插件！')
            elif get.storage_type=="ftp":
                import sys
                if '/www/server/panel/plugin/ftp' not in sys.path:
                    sys.path.insert(0, '/www/server/panel/plugin/ftp')
                try:
                    from ftp_main import ftp_main as ftp
                    # get.object_name =os.path.join(webdav().default_backup_path , "whole_machine_backup", os.path.basename(backup_path))
                    # self.client.download_file(from_path=download_path, to_path=local_path)
                    ftp_backup_path=ftp().get_config(get)['backup_path']
                    download_path=os.path.join(ftp_backup_path , "whole_machine_backup",os.path.basename(backup_path))
                    local_path = os.path.join("/tmp", os.path.basename(backup_path))
                    ftp().client.generate_download_url(download_path)
                    path=local_path
                except:
                    import traceback
                    print(traceback.format_exc())
                    return public.returnMsg(False, '请先安装ftp存储插件！')
            else:
                path = get.backup_path
            if os.path.exists(path):
                return {'status': True, 'is_loacl': True, 'path': path}
            return public.returnMsg(False, '文件不存在！')
        else:
            name=os.path.basename(backup_path)
            cloud_name=get.storage_type
            import CloudStoraUpload
            c = CloudStoraUpload.CloudStoraUpload()
            c.run(cloud_name)
            url = ''
            backup_path = c.obj.backup_path
            path = os.path.join(backup_path, "whole_machine_backup")
            data = c.obj.get_list(path)
            for i in data['list']:
                print(i)
                if i['name'] == name:
                    url = i['download']
            if url == '':
                return public.returnMsg(False, '在云存储中未发现该文件!')
            return {'status': True, 'is_loacl': False, 'path': url}

    
    def get_sys_backup_path_config(self,get=None):
        setting_path='{}/data/whole_machine_backup_settings.json'.format(public.get_panel_path())
        try:
            with open(setting_path, 'r') as f:
                settings = json.load(f)
        except:
            settings = {'sys_backup_path': self.sys_backup_path}
            with open(setting_path, 'w') as f:
                json.dump(settings, f) 
        sys_backup_path = settings.get('sys_backup_path', self.sys_backup_path)
        return public.returnMsg(True,sys_backup_path)

    def set_sys_backup_path_config(self, get):
        setting_path='{}/data/whole_machine_backup_settings.json'.format(public.get_panel_path())
        sys_backup_path = get.sys_backup_path if get.sys_backup_path.endswith('/') else get.sys_backup_path + '/'
        # 检查是否是有效目录路径
        if not os.path.isabs(sys_backup_path):
            return public.returnMsg(False, "请输入正确的目录路径!")
        settings = {
            'sys_backup_path': sys_backup_path
        }
        with open(setting_path, 'w') as f:
            json.dump(settings, f)
        return public.returnMsg(True, "设置成功！") 


    # ======================================================================
    #     开始备份
    # ======================================================================
    # 开始入口
    def backup(self, id):
        """
        备份
        :param id:
        :return:
        """
        try:
            if not isinstance(id, str):
                id = id['id']
            # self.lock = threading.Lock()
            # self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
            if id not in self.config.keys():
                return public.returnMsg(False, '任务不存在！')
            self.backup_save_config = self.backup_save_config.format(id)
            self.backup_log_path = self.config[id]["backup_log_path"]
            conf = self.config[id]
            conf["status"] = -1
            self.status = 1
            conf["exec_time"] = time.strftime('%Y-%m-%d %H:%M:%S')
            self.write_config(id, conf)
            backup_path = self.backup_path
            self.backup_path = conf["backup_path"]  # 别用backup_path
            if not os.path.exists(self.backup_path):
                public.ExecShell('mkdir -p {}'.format(os.path.basename(self.backup_path)))
            if not os.path.exists(os.path.join(self.backup_path, "backup")):
                public.ExecShell('mkdir -p {}'.format(os.path.join(self.backup_path, "backup")))
            if not os.path.exists(os.path.dirname(self.backup_log_path)):
                public.ExecShell('mkdir -p {}'.format(os.path.dirname(self.backup_log_path)))
            # 获取备份配置
            self.backup_config = json.loads(public.readFile(conf["task_config"]))["backup_config"]
            self.backup_config = json.loads(self.backup_config)
            if not os.path.exists(self.backup_log_path):
                public.writeFile(self.backup_log_path, json.dumps(self.backup_config))
            else:
                try:
                    self.backup_config = json.loads(public.readFile(self.backup_log_path))
                except:
                    pass
            # 创建备份目录
            # 备份环境
            self.backup_env(self.backup_config)
            # 备份数据
            self.backup_data(self.backup_config)
            # 备份配置 暂时不做....
            # self.backup_panel_config(self.backup_config)
            # 备份完成 将备份文件压缩
            conf["status"] = self.status
            conf['error_num'] = self.error_num
            conf['access_num'] = self.access_num
            conf_path = os.path.join(conf['backup_path'], id)
            public.writeFile(conf_path, json.dumps({id: conf}))
            public.ExecShell('cp {} {}'.format(self.backup_log_path, conf['backup_path']))
            public.ExecShell('cp {} {}'.format(os.path.join(conf['backup_path'], 'backup.json'), os.path.join(backup_path, id + '_backup.json')))
            # public.ExecShell('tar -zcvf {}.tar.gz -C {} .'.format(self.backup_path, self.backup_path))
            # 压缩备份文件
            
            self.print_log(self.backup_path)
            tar_gz_filename ="{}.tar.gz".format(self.backup_path)
            public.ExecShell(f'tar -zcvf {tar_gz_filename} -C {self.backup_path} .')
            self.print_log(f"->>>压缩备份文件完成：{tar_gz_filename}")
            
            # 判断是否需要上传到云存储
            storage_type = conf.get("storage_type", "local")
            cloud_backup_path = tar_gz_filename  # 初始备份路径为本地路径
            
            if storage_type != "local" and os.path.exists(tar_gz_filename):
                _cloud_name = {
                    "tianyiyun": "天翼云cos",
                    "webdav": "webdav存储",
                    "minio": "minio存储",
                    "dogecloud": "多吉云COS",
                }
                print(333333333333333)
                if storage_type in ["tianyiyun","webdav","minio","dogecloud"]:
                    cloud_name_cn = _cloud_name.get(storage_type, storage_type)  # 获取云存储的中文名
                    from CloudStoraUpload import CloudStoraUpload
                    _cloud_new = CloudStoraUpload()
                    _cloud = _cloud_new.run(storage_type)
                    if _cloud is False:
                        return False
                    self.print_log("->>>正在上传文件{}到{}，请稍候...".format(tar_gz_filename,cloud_name_cn))
                    try:
                        backup_path = _cloud_new.backup_path
                        if not backup_path.endswith('/'):
                            backup_path += '/'
                        upload_path = os.path.join(backup_path, "whole_machine_backup", os.path.basename(tar_gz_filename))
                        self.print_log(tar_gz_filename)
                        self.print_log(upload_path)
                        if _cloud.upload_file(tar_gz_filename, upload_path):
                            self.print_log(f"->>>文件已成功上传到云存储：{cloud_name_cn}")
                            public.ExecShell('rm -rf {}'.format(tar_gz_filename))
                            self.print_log('删除本地文件{}'.format(tar_gz_filename))
                            # cloud_backup_path = upload_path + '|' + storage_type + '|' + os.path.basename(tar_gz_filename)  # 更新为云存储路径
                        else:
                            self.print_log(f"->>>上传到{cloud_name_cn}失败")
                    except Exception as e:
                        self.print_log(f"->>>上传到{cloud_name_cn}时发生错误: {str(e)}")
                else:
                    print(storage_type)
                    from CloudStoraUpload import CloudStoraUpload
                    _cloud = CloudStoraUpload()
                    _cloud.run(storage_type)
                    cloud_name_cn = _cloud.obj._title
                    if not _cloud.obj:
                        return False
                    self.print_log("->>>正在上传文件{}到{}，请稍候...".format(tar_gz_filename,cloud_name_cn))
                    try:
                        backup_path = _cloud.obj.backup_path
                        if not backup_path.endswith('/'):
                            backup_path += '/'
                        upload_path = os.path.join(backup_path, "whole_machine_backup", os.path.basename(tar_gz_filename))
                        print(upload_path)
                        print((tar_gz_filename))
                        if _cloud.cloud_upload_file(tar_gz_filename, upload_path):
                            self.print_log(f"->>>已成功上传到{cloud_name_cn}")
                            public.ExecShell('rm -rf {}'.format(tar_gz_filename))
                            self.print_log('删除本地文件{}'.format(tar_gz_filename))
                            # cloud_backup_path = upload_path + '|' + storage_type + '|' + os.path.basename(tar_gz_filename)  # 更新为云存储路径
                        else:
                            self.print_log(f"->>>上传到{cloud_name_cn}失败")
                    except Exception as e:
                        self.print_log(f"->>>上传到{cloud_name_cn}时发生错误: {str(e)}")
                
            # return public.returnMsg(False, '备份失败！')

            public.ExecShell('rm -rf {}'.format(self.backup_path))
            self.write_config(id, conf)
            return public.returnMsg(True, '备份完成！')
        except:
            print(public.get_error_info())
            return public.returnMsg(False, '备份失败！')
        

    # 修改备份状态
    def change_backup_status1(self, block, name="", son_name="", status_name="", status=0, sec_name='', ):
        # 通过线程锁来修改self变量并写入文件中
        pass

    def change_backup_status(self, block, name="", son_name="", status_name="", status=0, sec_name='', msg=''):
        if status == 2:
            self.status = 2
            self.error_num += 1
        if status == 1:
            self.access_num += 1
        if sec_name != '':
            for i in range(len(self.backup_config[block][name][son_name])):
                if self.backup_config[block][name][son_name][i]['name'] == sec_name:
                    self.backup_config[block][name][son_name][i][status_name] = status
                    if status_name == 'backup_status':
                        if status == 1:
                            self.backup_config[block][name][son_name][i]['status'] = 1
                        else:
                            self.backup_config[block][name][son_name][i]['status'] = 0
                    if msg != "":
                        self.backup_config[block][name][son_name][i]['msg'] = msg
        elif son_name != "":
            for i in range(len(self.backup_config[block][name])):
                if self.backup_config[block][name][i]['name'] == son_name:
                    self.backup_config[block][name][i][status_name] = status
                    if status_name == 'backup_status':
                        if status == 1:
                            self.backup_config[block][name][i]['status'] = 1
                        else:
                            self.backup_config[block][name][i]['status'] = 0
                    if msg != "":
                        self.backup_config[block][name][i]['msg'] = msg
        else:
            self.backup_config[block][status_name] = status
            if status_name == 'backup_status':
                if status == 1:
                    self.backup_config[block]['status'] = 1
                else:
                    self.backup_config[block]['status'] = 0
            if msg != "":
                self.backup_config[block]['msg'] = msg
        public.writeFile(self.backup_log_path, json.dumps(self.backup_config))

    def generate_md5(self, input_string):
        # 创建一个 hashlib.md5 对象
        md5_hash = hashlib.md5()

        # 将输入的字符串编码为字节，并更新 MD5 对象
        md5_hash.update(input_string.encode())

        # 获取生成的 MD5 值的十六进制表示
        md5_hex = md5_hash.hexdigest()

        return md5_hex

    # 复制一个文件或者目录到备份目录中
    def copy_file(self, path):
        if not os.path.exists(path):
            return False
        md5_name = self.generate_md5(path)
        save_path = os.path.join(self.backup_path, "backup", md5_name)
        if os.path.exists(save_path):
            return save_path
        if os.path.isdir(path):
            public.ExecShell('tar -zcvf {} -C {} .'.format(save_path, path))
        if os.path.isfile(path):
            public.ExecShell('tar -zcvf {} -C {} {}'.format(save_path, os.path.dirname(path), os.path.basename(path)))
        time.sleep(0.01)
        if os.path.exists(save_path):
            return save_path
        else:
            return False

    def write_id_config(self, block, name="", son_name="", config={}, sec_name=''):
        if self.id_config is None:
            if not os.path.exists(self.backup_save_config):
                public.writeFile(self.backup_save_config, json.dumps({}))
            print(self.backup_save_config)
            self.id_config = json.loads(public.readFile(self.backup_save_config))
        if sec_name != "":
            if block not in self.id_config:
                self.id_config[block] = {}
            if name not in self.id_config[block]:
                self.id_config[block][name] = {}
            if son_name not in self.id_config[block][name]:
                self.id_config[block][name][son_name] = {}
            self.id_config[block][name][son_name][sec_name] = config
        elif son_name != "":
            if block not in self.id_config:
                self.id_config[block] = {}
            if name not in self.id_config[block]:
                self.id_config[block][name] = {}
            self.id_config[block][name][son_name] = config
        elif name != "":
            if block not in self.id_config:
                self.id_config[block] = {}
            self.id_config[block][name] = config
        else:
            self.id_config[block] = config
        public.writeFile(self.backup_save_config, json.dumps(self.id_config))

    def uncopy_file(self, path, to_path, isfile=True, md5=False, unbak=False):
        if not os.path.exists(path) and isfile:
            return False
        if os.path.exists(to_path):
            if not unbak:
                if os.path.exists(to_path + '_bak'):
                    public.ExecShell('rm -rf {}'.format(to_path + '_bak'))
                public.ExecShell('mv {} {}'.format(to_path, to_path + '_bak'))

            public.ExecShell('rm -rf {}'.format(to_path))
        if isfile:
            public.ExecShell('tar -zxvf {} -C {} --overwrite'.format(path, os.path.dirname(to_path)))
        else:
            if not isfile:
                public.ExecShell('mkdir -p {}'.format(to_path))
            public.ExecShell('tar -zxvf {} -C {} --overwrite'.format(path, to_path))
        time.sleep(0.01)
        if os.path.exists(to_path):
            if md5 and isfile:
                if md5 == self.get_md5(to_path):
                    self.print_log('文件MD5比对成功')
                    return True
                else:
                    self.print_log('文件md5比对失败')
                    return False
            return True
        else:
            res, i_flag = self.check_copy_error(to_path)
            if res:
                if isfile:
                    public.ExecShell('tar -zxvf {} -C {} --overwrite'.format(path, to_path))
                else:
                    public.ExecShell('tar -zxvf {} -C {} --overwrite'.format(path, os.path.basename(to_path)))
            time.sleep(0.01)
            if i_flag:
                public.ExecShell('chattr +i {}'.format(to_path))
            if os.path.exists(to_path):
                if md5 and isfile:
                    if md5 == self.get_md5(to_path):
                        self.print_log('文件MD5比对成功')
                        return True
                    else:
                        self.print_log('文件md5比对失败')
                        return False
                return True
            return False

    def check_copy_error(self, path):
        # 检查 / 目录是否满
        i_flag = False
        disk_status = psutil.disk_usage('/')
        if disk_status.used / disk_status.total >= 0.99:
            self.print_log('磁盘空间不足')
            return False, i_flag
        if not os.path.exists(path):
            # 尝试创建目录
            public.ExecShell('mkdir -p {}'.format(path))
            time.sleep(0.01)
            if os.path.exists(path):
                return True, i_flag
        # 检查目录是否有 权限写入
        if not os.access(path, os.W_OK):
            self.print_log('文件无法写入，尝试修复')
            public.ExecShell('chmod 777 {}'.format(path))
            public.ExecShell('chattr -i {}'.format(path))
            if not os.access(path, os.W_OK):
                self.print_log('文件无法写入，无法修复')
                return False, i_flag
            else:
                i_flag = True, i_flag
                self.print_log('文件修复成功')
                return True, i_flag
        return False, i_flag
    # 222222222222
    
    # ======================================================================
    #     备份环境
    # ======================================================================

    def backup_env(self, conf):
        env_conf = conf["env_list"]
        connect = {
            "php": self.backup_php,
            "mysql": self.backup_mysql,
            "mongo": self.backup_mongo,
            "redis": self.backup_redis,
            "pgsql": self.backup_pgsql,
            "nginx": self.backup_nginx,
            "apache": self.backup_apache,
            "ftp": self.backup_ftp,
        }
        for k, v in env_conf.items():
            if not isinstance(v, list):
                continue
            for i in v:
                if i['status'] in [1, -1, 2]:
                    connect[k](i)
                else:
                    if i['name'] and i["status"] != 3:
                        self.change_backup_status("env_list", k, i["name"], "backup_status", 4, msg="未备份".format(i["name"]))

    def backup_php(self, conf):
        try:
            self.change_backup_status("env_list", "php", conf["name"], "backup_status", -1, msg="开始备份php{}环境".format(conf["name"]))
            php_verison = conf["name"]
            flag = 1
            self.print_log("->>>开始获取php{}扩展列表".format(php_verison))
            res = public.ExecShell("/www/server/php/{}/bin/php -m".format(php_verison))[0]
            php_development = res.split("\n")
            # 去待 【】和空行
            if len(php_development) > 1:
                php_development = php_development[1:]
                php_development = [i.strip() for i in php_development if i.strip() and '[' not in i]
            else:
                php_development = []
            # 尝试获取swoole的版本
            if 'swoole' in php_development:
                res = public.ExecShell("/www/server/php/{}/bin/php --ri swoole | grep Version | awk '{{print $3}}'".format(php_verison))[0]
                try:
                    index = php_development.index('swoole')
                    php_development[index] = 'swoole{}'.format(res.strip()[0] if res.strip()[0] in ['4', '5'] else res.strip()[0])
                except:
                    pass
            # self.print_log(php_development)
            self.print_log("获取php{}扩展列表完成".format(php_verison))

            # 备份配置文件
            self.print_log("开始备份php{}配置文件".format(php_verison))
            php_ini = "/www/server/php/{}/etc/php.ini".format(php_verison)
            res = self.copy_file(php_ini)
            if not res:
                self.print_log("备份php{}配置文件失败".format(php_verison))
                self.change_backup_status("env_list", "php", conf["name"], "backup_status", 2, msg="备份php{}配置文件失败".format(php_verison))
                flag = 2
            php_ini_md5 = self.get_md5(php_ini)
            php_ini_name = res
            php_fpm_path = "/www/server/php/{}/etc/php-fpm.conf".format(php_verison)
            res = self.copy_file(php_fpm_path)
            if not res:
                self.print_log("备份php{}配置文件失败".format(php_verison))
                self.change_backup_status("env_list", "php", conf["name"], "backup_status", 2, msg="备份php{}配置文件失败".format(php_verison))
                flag = 2
            php_fpm_md5 = self.get_md5(php_fpm_path)
            php_fpm_name = res
            # 写入备份配置文件
            self.print_log("备份php{}配置文件完成".format(php_verison))
            words_path = "/www/server/panel/config/thesaurus.json"
            wrods_data = None
            words_data_md5 = None
            if os.path.exists(words_path):
                wrods_data = self.copy_file(words_path)
                words_data_md5 = self.get_md5(words_path)
            self.print_log("备份php{}关键词完成".format(php_verison))
            config = {
                "php_development": php_development,
                "php_ini": php_ini_name,
                "php_fpm": php_fpm_name,
                "wrods_data": wrods_data,
                "php_ini_md5": php_ini_md5,
                "php_fpm_md5": php_fpm_md5,
                "words_data_md5": words_data_md5,
            }
            self.write_id_config("env_list", "php", conf["name"], config)
            self.change_backup_status("env_list", "php", conf["name"], "backup_status", flag, msg="备份php{}完成".format(php_verison))
            self.print_log("->>>备份php{}完成".format(php_verison))
        except:
            self.print_log("备份php{}出错".format(php_verison))
            self.print_log(public.get_error_info())
            self.change_backup_status("env_list", "php", conf["name"], "backup_status", 2, msg="备份php{}出错，程序出错".format(php_verison))

    def backup_mysql(self, conf):
        try:
            self.print_log("->>>开始备份mysql")
            flag = 1
            mysql_data = None
            mysql_conf = None
            mysql_version = None
            if not conf['setup']:
                self.print_log("mysql未安装")
                self.change_backup_status("env_list", "mysql", conf["name"], "backup_status", 2, msg="mysql未安装")
                flag = 2
            else:
                self.print_log("开始备份mysql{}版本".format(conf["name"]))
                mysql_version = conf["name"]
                self.print_log("开始备份mysql{}配置文件".format(mysql_version))
                mysql_conf = "/etc/my.cnf"
                res = self.copy_file(mysql_conf)
                if not res:
                    self.print_log("备份mysql{}配置文件失败".format(mysql_version))
                    flag = 2
                else:
                    mysql_conf = res
                if int(conf.get("primitive_data", 0)) == 1:
                    self.print_log("开始备份mysql{}数据文件".format(mysql_version))
                    mysql_data = public.get_mysql_info()['datadir']
                    res = self.copy_file(mysql_data)
                    if not res:
                        self.print_log("备份mysql{}数据文件失败".format(mysql_version))
                        flag = 2
                    else:
                        mysql_data = res
            version = mysql_version
            mysql_conf_md5 = self.get_md5("/etc/my.cnf")
            config = {
                "version": version,
                "mysql_conf": mysql_conf,
                "mysql_data": mysql_data,
                "mysql_conf_md5": mysql_conf_md5,
            }
            self.write_id_config("env_list", "mysql", config=config)
            self.change_backup_status("env_list", "mysql", son_name=conf["name"], status_name="backup_status", status=flag, msg="备份mysql完成")
            self.print_log("->>>备份mysql完成")
        except:
            self.print_log("备份mysql出错")
            self.print_log(public.get_error_info())
            self.change_backup_status("env_list", "mysql", conf["name"], "backup_status", 2, msg="备份mysql出错，程序出错")

    def backup_mongo(self, conf):
        try:
            self.print_log("->>> 开始备份mongo")
            flag = 1
            mongo_conf = None
            mongo_version = None
            mongo_conf_md5 = None
            if not conf['setup']:
                self.print_log("mongo未安装")
                self.change_backup_status("env_list", "mongo", conf["name"], "backup_status", 2, msg="mongo未安装")
                flag = 2
            else:
                self.print_log("备份mongo{}版本".format(conf["name"]))
                mongo_version = conf["name"]
                self.print_log("备份mongo{}配置文件".format(mongo_version))
                mongo_conf = "/www/server/mongodb/config.conf"
                mongo_conf_md5 = self.get_md5(mongo_conf)
                res = self.copy_file(mongo_conf)
                if not res:
                    self.print_log("备份mongo{}配置文件失败".format(mongo_version))
                    flag = 2
                else:
                    mongo_conf = res
            version = mongo_version
            mongo_conf = mongo_conf
            config = {
                "version": version,
                "mongo_conf": mongo_conf,
                "mongo_conf_md5": mongo_conf_md5,
            }
            self.write_id_config("env_list", "mongo", config=config)
            self.change_backup_status("env_list", "mongo", conf['name'], status_name="backup_status", status=flag, msg="备份mongo完成")
            self.print_log("->>>备份mongo完成")
        except:
            self.print_log("备份mongo出错")
            self.print_log(public.get_error_info())
            self.change_backup_status("env_list", "mongo", conf["name"], "backup_status", 2, msg="备份mongo出错，程序出错")

    def backup_redis(self, conf):
        try:
            self.print_log("->>> 开始备份redis")
            flag = 1
            redis_conf = None
            redis_version = None
            if not conf['setup']:
                self.print_log("redis未安装")
                self.change_backup_status("env_list", "redis", conf['name'], status_name="backup_status", status=2, msg="redis未安装")
                flag = 2
            else:
                self.print_log("备份redis{}版本".format(conf["name"]))
                redis_version = conf["name"]
                self.print_log("备份redis{}配置文件".format(redis_version))
                redis_conf = "/www/server/redis/redis.conf"
                res = self.copy_file(redis_conf)
                if not res:
                    self.print_log("备份redis{}配置文件失败".format(redis_version))
                    flag = 2
                else:
                    redis_conf = res
            version = redis_version
            redis_conf = redis_conf
            redis_conf_md5 = self.get_md5(redis_conf)
            config = {
                "version": version,
                "redis_conf": redis_conf,
                "redis_conf_md5": redis_conf_md5,
            }
            self.write_id_config("env_list", "redis", config=config)
            self.change_backup_status("env_list", "redis", conf['name'], status_name="backup_status", status=flag, msg="备份redis完成")
            self.print_log("->>>备份redis完成")
        except:
            self.print_log("备份redis出错")
            print(public.get_error_info())
            self.change_backup_status("env_list", "redis", conf['name'], status_name="backup_status", status=2, msg="备份redis出错，程序出错")

    def backup_pgsql(self, conf):
        try:
            self.print_log("->>> 开始备份pgsql")
            flag = 1
            pgsql_conf = None
            pgsql_version = None
            client_conf = None
            if not conf['setup']:
                self.print_log("pgsql未安装")
                self.change_backup_status("env_list", "pgsql", conf["name"], "backup_status", 2, msg="pgsql未安装")
                flag = 2
            else:
                self.print_log("备份pgsql{}版本".format(conf["name"]))
                pgsql_version = conf["name"]
                self.print_log("备份pgsql{}配置文件".format(pgsql_version))
                pgsql_conf = "/www/server/pgsql/data/postgresql.conf"
                res = self.copy_file(pgsql_conf)
                if not res:
                    self.print_log("备份pgsql{}主配置文件失败".format(pgsql_version))
                    flag = 2
                else:
                    pgsql_conf = res
                self.print_log("备份pgsql{}客户端配置文件".format(pgsql_version))
                client_conf_path = "/www/server/pgsql/data/pg_hba.conf"
                res = self.copy_file(client_conf_path)
                if not res:
                    self.print_log("备份pgsql{}客户端配置文件失败".format(pgsql_version))
                    flag = 2
                else:
                    client_conf = res
            version = pgsql_version
            pgsql_conf = pgsql_conf
            client_conf = client_conf
            pgsql_conf_md5 = self.get_md5(pgsql_conf)
            client_conf_md5 = self.get_md5(client_conf)
            config = {
                "version": version,
                "pgsql_conf": pgsql_conf,
                "client_conf": client_conf,
                "pgsql_conf_md5": pgsql_conf_md5,
                "client_conf_md5": client_conf_md5,
            }
            self.write_id_config("env_list", "pgsql", config=config)
            self.change_backup_status("env_list", "pgsql", conf['name'], status_name="backup_status", status=flag, msg="备份pgsql完成")
            self.print_log("->>>备份pgsql完成")
        except:
            self.print_log("备份pgsql出错")
            self.print_log(public.get_error_info())
            self.change_backup_status("env_list", "pgsql", conf['name'], status_name="backup_status", status=2, msg="备份pgsql出错，程序出错")

    def backup_nginx(self, conf):
        try:
            self.print_log("->>> 开始备份nginx")
            flag = 1
            nginx_conf = None
            nginx_version = None
            nginx_file = None
            nginx_cmd = None
            nginx_systemd = None
            self.change_backup_status("env_list", "nginx", conf['name'], status_name="backup_status", status=-1, msg="开始备份nginx")
            if not conf['setup']:
                self.print_log("nginx未安装")
                self.change_backup_status("env_list", "nginx", status_name="backup_status", status=2, msg="nginx未安装")
                flag = 2
            else:
                self.print_log("开始备份nginx{}版本".format(conf["name"]))
                nginx_version = conf["name"]
                self.print_log("开始备份nginx{}配置文件".format(nginx_version))
                nginx_conf_path = "/www/server/nginx/conf/nginx.conf"
                res = self.copy_file(nginx_conf_path)
                if not res:
                    self.print_log("备份nginx{}配置文件失败".format(nginx_version))
                    flag = 2
                else:
                    nginx_conf = res
                self.print_log("开始备份nginx{}文件".format(nginx_version))
                nginx_file_path = "/www/server/nginx"
                res = self.copy_file(nginx_file_path)
                if not res:
                    self.print_log("备份nginx{}文件失败".format(nginx_version))
                    flag = 2
                else:
                    nginx_file = res
                self.print_log("开始备份nginx{}启动脚本".format(nginx_version))
                nginx_cmd_path = "/etc/init.d/nginx"
                res = self.copy_file(nginx_cmd_path)
                if not res:
                    self.print_log("备份nginx{}启动脚本失败".format(nginx_version))
                    flag = 2
                else:
                    nginx_cmd = res
                self.print_log("开始备份nginx{}systemd服务脚本".format(nginx_version))
                nginx_systemd_path = "/lib/systemd/system/nginx.service"
                if os.path.exists(nginx_systemd_path):
                    res = self.copy_file(nginx_systemd_path)
                    if not res:
                        self.print_log("备份nginx{}systemd服务脚本失败".format(nginx_version))
                        flag = 2
                    else:
                        nginx_systemd = res
                nginx_conf_md5 = self.get_md5(nginx_conf_path)
                nginx_file_md5 = self.get_md5(nginx_file_path)
                nginx_cmd_md5 = self.get_md5(nginx_cmd_path)
                nginx_systemd_md5 = self.get_md5(nginx_systemd_path)
            config = {
                "nginx_conf": nginx_conf,
                "nginx_file": nginx_file,
                "nginx_cmd": nginx_cmd,
                "nginx_systemd": nginx_systemd,
                "version": nginx_version,
                "nginx_conf_md5": nginx_conf_md5,
                "nginx_file_md5": nginx_file_md5,
                "nginx_cmd_md5": nginx_cmd_md5,
                "nginx_systemd_md5": nginx_systemd_md5,
            }
            self.write_id_config("env_list", "nginx", config=config)
            self.change_backup_status("env_list", "nginx", conf['name'], status_name="backup_status", status=flag, msg="备份nginx完成")
        except:
            self.print_log("备份nginx出错")
            self.print_log(public.get_error_info())
            self.change_backup_status("env_list", "nginx", conf['name'], status_name="backup_status", status=2, msg="备份nginx出错，程序出错")

    def backup_apache(self, conf):
        try:
            self.print_log("->>> 开始备份apache")
            self.change_backup_status("env_list", "apache", conf['name'], status_name="backup_status", status=-1, msg="开始备份apache")
            flag = 1
            apache_conf = None
            apache_version = None
            self.print_log("开始备份apache{}版本".format(conf["name"]))
            version = apache_version
            self.print_log("开始备份apache{}配置文件".format(version))
            apache_conf_path = "/www/server/apache/conf/"
            res = self.copy_file(apache_conf_path)
            if not res:
                self.print_log("备份apache{}配置文件失败".format(version))
                flag = 2
            else:
                apache_conf = res
            apache_conf_md5 = self.get_md5(apache_conf_path)
            config = {
                "version": version,
                "apache_conf": apache_conf,
                "apache_conf_md5": apache_conf_md5,
            }
            self.write_id_config("env_list", "apache", config=config)
            self.change_backup_status("env_list", "apache", conf['name'], status_name="backup_status", status=flag, msg="备份apache完成")
        except:
            self.print_log("备份apache出错")
            self.print_log(public.get_error_info())
            self.change_backup_status("env_list", "apache", conf['name'], status_name="backup_status", status=2, msg="备份apache出错，程序出错")

    def backup_ftp(self, conf):
        try:
            self.print_log("->>> 开始备份ftp")
            self.change_backup_status("env_list", "ftp", conf['name'], status_name="backup_status", status=-1, msg="开始备份ftp")
            flag = 1
            version = conf["name"]
            ftp_conf = None
            log_status = None
            if not conf['setup']:
                self.print_log("ftp未安装")
                self.change_backup_status("env_list", "ftp", conf["name"], "backup_status", 2, msg="ftp未安装")
                flag = 2
            else:
                self.print_log("开始备份ftp{}配置文件".format(version))
                ftp_conf_path = "/www/server/pure-ftpd/etc/pure-ftpd.conf"
                res = self.copy_file(ftp_conf_path)
                if not res:
                    self.print_log("备份ftp{}配置文件失败".format(version))
                    flag = 2
                else:
                    ftp_conf = res
                self.print_log("开始备份ftp{}日志状态".format(version))
                rsyslog_path = "/etc/rsyslog.conf"
                cofig = public.readFile(rsyslog_path)
                if "ftp.*" in cofig:
                    log_status = 1
                else:
                    log_status = 0
            ftp_conf_md5 = self.get_md5(ftp_conf_path)
            config = {
                "version": version,
                "ftp_conf": ftp_conf,
                "log_status": log_status,
                "ftp_conf_md5": ftp_conf_md5,
            }
            self.write_id_config("env_list", "ftp", config=config)
            self.change_backup_status("env_list", "ftp", conf['name'], status_name="backup_status", status=flag, msg="备份ftp完成")
            self.print_log("->>>备份ftp完成")
        except:
            self.print_log("备份ftp出错")
            self.print_log(public.get_error_info())
            self.change_backup_status("env_list", "ftp", conf['name'], status_name="backup_status", status=2, msg="备份ftp出错，程序出错")

        # ======================================================================
        #     备份数据
        # ======================================================================

    def backup_data(self, conf):
        data_conf = conf["data_list"]
        connect = {
            "php": self.backup_php_data,
            "java": self.backup_java_data,
            "node": self.backup_node_data,
            "python": self.backup_python_data,
            "other": self.backup_other_data,
            "net": self.backup_net_data,
            "proxy": self.backup_proxy_data,
            "html": self.backup_html_data,
            "mysql": self.backup_mysql_data,
            "mongodb": self.backup_mongodb_data,
            "redis": self.backup_redis_data,
            "pgsql": self.backup_pgsql_data,
            "ftp_list": self.backup_ftp_data,
            "terminal_list": self.backup_terminal_data,
            "crontab_list": self.backup_crontab_data,
            "port_list": self.backup_port_data,
            "ip_list": self.backup_ip_data,
            "port_redirect": self.backup_port_redirect_data,
            "area_list": self.backup_area_data,
            "ssh_config": self.ssh_config_data,
            "words": self.backup_words_data,
            "sqlite": self.backup_sqlite_data,
        }
        for k, v in data_conf.items():
            if k in ['site_list', 'sql_list', 'config_list', "safety"]:
                for type, dates in v.items():
                    if type not in connect.keys():
                        continue
                    for data in dates:
                        if data['status'] in [1, -1, 2]:
                            connect[type.lower()](data)
                        else:
                            if data['name'] and data["status"] != 3:
                                self.change_backup_status("data_list", k, type, "backup_status", 4, data["name"], msg="未备份".format(data["name"]))
            elif k in ['ftp_list']:
                for i in v:
                    if i['status'] in [1, -1, 2]:
                        connect[k](i)
                    else:
                        if i['name'] and i["status"] != 3:
                            self.change_backup_status("data_list", k, i["name"], "backup_status", 4, msg="未备份".format(i["name"]))
            else:
                for j in v:
                    if j['status'] in [1, -1, 2]:
                        connect[k](j)
                    else:
                        if j['name'] and j["status"] != 3:
                            self.change_backup_status("data_list", k, j["name"], "backup_status", 4, msg="未备份".format(j["name"]))

    def backup_php_data(self, conf):
        try:
            self.print_log("->>>开始备份PHP站点:{}".format(conf["name"]))
            self.change_backup_status("data_list", "site_list", 'php', "backup_status", -1, conf["name"], msg="开始备份")
            # 获取网站信息
            sid = conf["id"]
            site_info = public.M('sites').where("id=?", (sid,)).find()
            is_phpmod = False
            if 'project_config' in site_info.keys():
                project_config = json.loads(site_info['project_config'])
                if 'type' in project_config.keys() and project_config['type'].lower() == 'phpmod':
                    is_phpmod = True
            site_file = None
            domains = None
            database_info = None
            redirect_list = []
            redirect_nginx_data = None
            redirect_apache_data = None
            proxy_nginx_data = None
            proxy_apache_data = None
            proxy_list = []
            nginx_config = None
            apache_config = None
            dir_auth_json = None
            dir_auth_file = None
            ssl_info = None
            if not site_info:
                self.print_log("{} 获取站点信息失败".format(conf["name"]))
                self.change_backup_status("data_list", "site_list", 'php', "backup_status", 2, conf["name"], msg="获取站点信息失败")
            else:
                # 备份网站域名
                domains = public.M('domain').where("pid=?", (sid,)).select()
                if not domains or isinstance(domains, str):
                    self.print_log("{} 获取站点域名失败".format(conf["name"]))
                    self.change_backup_status("data_list", "site_list", 'php', "backup_status", 2, conf["name"], msg="获取站点域名失败")

                # 备份站点文件
                site_file_path = site_info["path"]
                if os.path.exists(site_file_path):
                    site_file = self.copy_file(site_file_path)

                # 备份数据库
                database_info = public.M("databases").where("pid = ?", (sid,)).find()
                if not database_info:
                    database_info = None
                    self.print_log("未查找到相关的数据库信息，跳过备份数据库")
                elif isinstance(database_info, str):
                    database_info = None
                    self.print_log("查找数据库信息失败，跳过备份数据库")
                if database_info is not None:
                    self.backup_mysql_data(database_info)
                # 备份ftp
                ftp_info = public.M("ftps").where("pid = ?", (sid,)).find()
                if not ftp_info:
                    ftp_info = None
                    self.print_log("未查找到相关的ftp信息，跳过备份ftp")
                elif isinstance(ftp_info, str):
                    ftp_info = None
                    self.print_log("查找ftp信息失败，跳过备份ftp")
                if ftp_info is not None:
                    self.backup_ftp_data(ftp_info)
                __redirectfile = "/www/server/panel/data/redirect.conf"
                try:
                    redirectconf = json.loads(public.readFile(__redirectfile))
                except:
                    redirectconf = {}
                for i in redirectconf:
                    if i["sitename"] == conf["name"]:
                        redirect_list.append(i)
                redirect_nginx_data_path = '/www/server/panel/vhost/nginx/redirect/{}'.format(conf["name"])
                redirect_nginx_data = self.copy_file(redirect_nginx_data_path)
                redirect_apache_data_path = '/www/server/panel/vhost/apache/redirect/{}'.format(conf["name"])
                redirect_apache_data = self.copy_file(redirect_apache_data_path)
                if not is_phpmod:
                    __proxyfile = '{}/data/proxyfile.json'.format(public.get_panel_path())

                else:
                    __proxyfile = "{}/data/mod_proxy_file.conf".format(public.get_panel_path())
                try:
                    proxyUrl = json.loads(public.readFile(__proxyfile))
                except:
                    proxyUrl = {}
                for i in proxyUrl:
                    if i["sitename"] == conf["name"]:
                        proxy_list.append(i)
                proxy_nginx_data_path = '/www/server/panel/vhost/nginx/proxy/{}'.format(conf["name"])
                proxy_nginx_data = self.copy_file(proxy_nginx_data_path)
                proxy_apache_data_path = '/www/server/panel/vhost/apache/proxy/{}'.format(conf["name"])
                proxy_apache_data = self.copy_file(proxy_apache_data_path)

                import panelSite
                # 备份网站目录
                site_run_path = panelSite.panelSite().GetDirUserINI(public.to_dict_obj({'path': site_info['path'], 'id': site_info['id']}))
                import config
                # 备份ssl配置
                ssl_path = "/www/server/panel/vhost/cert/{}".format(site_info["name"])
                if os.path.exists(ssl_path):
                    ssl_info = self.copy_file(ssl_path)

                # 备份web配置文件
                nginx_config_path = "/www/server/panel/vhost/nginx/{}.conf".format(site_info["name"])
                apache_config_path = "/www/server/panel/vhost/apache/{}.conf".format(site_info["name"])
                if os.path.exists(nginx_config_path):
                    nginx_config = self.copy_file(nginx_config_path)
                if os.path.exists(apache_config_path):
                    apache_config = self.copy_file(apache_config_path)

                # 备份目录限制
                dir_auth_json_path = "/www/server/panel/data/site_dir_auth.json"
                if os.path.exists(dir_auth_json_path):
                    dir_auth_json = self.copy_file(dir_auth_json_path)
                dir_auth_file_path = "/www/server/panel/vhost/nginx/dir_auth/{}".format(site_info["name"])
                if os.path.exists(dir_auth_file_path):
                    dir_auth_file = self.copy_file(dir_auth_file_path)

                banding = public.M('binding').where('pid=?', (site_info['id'],)).field('id,pid,domain,path,port,addtime').select()

                site_file_md5 = self.get_md5(site_file_path)
                nginx_config_md5 = self.get_md5(nginx_config_path)
                apache_config_md5 = self.get_md5(apache_config_path)
                dir_auth_json_md5 = self.get_md5(dir_auth_json_path)
                dir_auth_file_md5 = self.get_md5(dir_auth_file_path)

                # 备份伪静态数据
                pseudo_static_data_path = "/www/server/panel/vhost/rewrite/{}.conf".format(site_info["name"])
                pseudo_static_data_md5 = self.get_md5(pseudo_static_data_path)
                pseudo_static_data = self.copy_file(pseudo_static_data_path)

                php_version = panelSite.panelSite().GetSitePHPVersion(public.to_dict_obj({'siteName': site_info['name']}))['phpversion']
                site_info["php_version"] = php_version
                config = {
                    "site_file": site_file,
                    "domains": domains,
                    "database_info": database_info,
                    "redirect_list": redirect_list,
                    "proxy_list": proxy_list,
                    "site_run_path": site_run_path,
                    "ssl_info": ssl_info,
                    "nginx_config": nginx_config,
                    "apache_config": apache_config,
                    "dir_auth_file": dir_auth_file,
                    "dir_auth_json": dir_auth_json,
                    "banding": banding,
                    "site_file_md5": site_file_md5,
                    "nginx_config_md5": nginx_config_md5,
                    "apache_config_md5": apache_config_md5,
                    "dir_auth_json_md5": dir_auth_json_md5,
                    "dir_auth_file_md5": dir_auth_file_md5,
                    "site_info": site_info,
                    "ftp_info": ftp_info,
                    "pseudo_static_data": pseudo_static_data,
                    "pseudo_static_data_md5": pseudo_static_data_md5,
                    "redirect_nginx_data": redirect_nginx_data,
                    "redirect_apache_data": redirect_apache_data,
                    "proxy_nginx_data": proxy_nginx_data,
                    "proxy_apache_data": proxy_apache_data,
                }
                self.print_log(config)
                self.write_id_config("data_list", "site_list", "php", config=config, sec_name=conf["name"])
                self.change_backup_status("data_list", "site_list", 'php', "backup_status", 1, conf["name"], msg="备份PHP站点:{}完成".format(conf["name"]))
            self.print_log("->>>备份PHP站点:{}完成".format(conf["name"]))
        except:
            self.change_backup_status("data_list", "site_list", 'php', "backup_status", 2, conf["name"], msg="备份PHP站点:{}出错，程序出错".format(conf["name"]))
            self.print_log("备份PHP站点:{}出错".format(conf["name"]))
            self.print_log(public.get_error_info())

    def backup_java_data(self, conf):
        self.print_log("->>>备份Java站点:{},跳过".format(conf["name"]))
        self.change_backup_status("data_list", "site_list", 'java', "backup_status", 2, conf["name"])
        return
        self.print_log("->>>开始备份Java站点:{}".format(conf["name"]))
        self.print_log(conf)
        self.print_log("->>>备份Java站点:{}完成".format(conf["name"]))

    def backup_node_data(self, conf):
        self.print_log("->>>备份Node站点:{}跳过".format(conf["name"]))
        self.change_backup_status("data_list", "site_list", 'node', "backup_status", 2, conf["name"], msg="备份Node站点:{}跳过".format(conf["name"]))
        return
        self.print_log("->>>开始备份Node站点:{}".format(conf["name"]))
        self.print_log(conf)
        self.print_log("->>>备份Node站点:{}完成".format(conf["name"]))

    def backup_python_data(self, conf):
        self.print_log("->>>备份Python站点:{}跳过".format(conf["name"]))
        self.change_backup_status("data_list", "site_list", 'python', "backup_status", 2, conf["name"], msg="备份Python站点:{}跳过".format(conf["name"]))
        return
        self.print_log("->>>开始备份Python站点:{}".format(conf["name"]))
        self.print_log(conf)
        self.print_log("->>>备份Python站点:{}完成".format(conf["name"]))

    def backup_other_data(self, conf):
        self.print_log("->>>备份其他站点:{}跳过".format(conf["name"]))
        self.change_backup_status("data_list", "site_list", 'other', "backup_status", 2, conf["name"], msg="备份其他站点:{}跳过".format(conf["name"]))
        return
        self.print_log("->>>开始备份其他站点:{}".format(conf["name"]))
        self.print_log(conf)
        self.print_log("->>>备份其他站点:{}完成".format(conf["name"]))

    def backup_net_data(self, conf):
        self.print_log("->>>备份.NET站点:{}跳过".format(conf["name"]))
        self.change_backup_status("data_list", "site_list", 'net', "backup_status", 2, conf["name"], msg="备份.NET站点:{}跳过".format(conf["name"]))
        return
        self.print_log("->>>开始备份.NET站点:{}".format(conf["name"]))
        self.print_log(conf)
        self.print_log("->>>备份.NET站点:{}完成".format(conf["name"]))

    def backup_proxy_data(self, conf):
        self.print_log("->>>开始备份代理站点:{}".format(conf["name"]))
        nginx_config = None
        apache_config = None
        site_info = None
        site_info = public.M('sites').where("name=?", (conf["name"],)).select()
        self.print_log("数据库信息备份成功")
        proxy_config_path = "/www/server/proxy_project/sites/{}".format(conf["name"])
        if not os.path.exists(proxy_config_path):
            self.print_log("代理站点:{},配置文件不存在，备份失败".format(conf["name"]))
            self.change_backup_status("data_list", "site_list", 'proxy', "backup_status", 2, conf["name"], msg="代理站点:{},配置文件不存在，备份失败".format(conf["name"]))
            return
        proxy_config = self.copy_file(proxy_config_path)
        self.print_log("代理站点:{}配置文件备份成功".format(conf["name"]))
        nginx_config_path = "/www/server/panel/vhost/nginx/{}.conf".format(conf["name"])
        if os.path.exists(nginx_config_path):
            nginx_config = self.copy_file(nginx_config_path)
        apache_config_path = "/www/server/panel/vhost/apache/{}.conf".format(conf["name"])
        if os.path.exists(apache_config_path):
            apache_config = self.copy_file(apache_config_path)
        self.print_log("代理站点:{}web配置文件备份成功".format(conf["name"]))

        proxy_config_md5 = self.get_md5(proxy_config_path)
        nginx_config_md5 = self.get_md5(nginx_config_path)
        apache_config_md5 = self.get_md5(apache_config_path)

        config = {
            "proxy_config": proxy_config,
            "nginx_config": nginx_config,
            "apache_config": apache_config,
            "site_info": site_info,
            "proxy_config_md5": proxy_config_md5,
            "nginx_config_md5": nginx_config_md5,
            "apache_config_md5": apache_config_md5,
        }
        self.write_id_config("data_list", "site_list", "proxy", config=config, sec_name=conf["name"])
        self.change_backup_status("data_list", "site_list", 'proxy', "backup_status", 1, conf["name"], msg="备份代理站点:{}完成".format(conf["name"]))
        self.print_log("->>>备份代理站点:{}完成".format(conf["name"]))

    def backup_html_data(self, conf):
        self.print_log("->>>备份静态站点:{}跳过".format(conf["name"]))
        self.change_backup_status("data_list", "site_list", 'html', "backup_status", 2, conf["name"], msg="备份静态站点:{}跳过".format(conf["name"]))
        return
        self.print_log("->>>开始备份静态站点:{}".format(conf["name"]))
        self.print_log(conf)
        self.print_log("->>>备份静态站点:{}完成".format(conf["name"]))

    # 检查mysql的备份文件是否正常
    def check_mysql_files(self, sql_path, sql_name):
        if not os.path.exists(sql_path):
            self.print_log("备份mysql数据库:{}失败，备份文件不存在！".format(sql_name))
            return False
        if os.path.isdir(sql_path):
            self.print_log("备份mysql数据库:{}失败，备份文件为目录！".format(sql_name))
            return False
        # 获取sql文件数据库大小
        sql_size = os.path.getsize(sql_path)
        if sql_size > 10 * 1024 * 1024:
            self.print_log("备份mysql数据库:{}，备份文件大于10M,跳过数据校验！".format(sql_name))
            return True
        # 验证备份是否正常结束
        data = public.GetNumLines(sql_path, 3)
        if data.find("Dump completed on") == -1:
            self.print_log("备份mysql数据库:{}失败，备份非正常结束！".format(sql_name))
            return False
        # 验证所有表是否都在sql文件中
        # 获取数据库的所有表名称
        table_list = database.database().GetInfo(public.to_dict_obj({'db_name': sql_name}))
        table_list = [i['table_name'] for i in table_list["tables"]]
        if not table_list:
            self.print_log("备份mysql数据库:{}数据校验成功，数据库无表".format(sql_name))
            return True

        self.print_log(table_list)
        res = public.ExecShell("grep -o -F -e {} {}".format(" -e ".join(table_list), sql_path))[0]
        # 去重和去空
        res = list(set(res.split("\n")))
        res = [i.strip() for i in res if i.strip()]
        if len(res) != len(table_list):
            self.print_log("备份mysql数据库:{}失败，备份文件不完整！".format(sql_name))
            return False
        self.print_log("备份mysql数据库:{}数据校验成功".format(sql_name))
        return True

    def backup_mysql_data(self, conf):
        try:
            self.print_log("->>>开始备份mysql数据库:{}".format(conf["name"]))
            self.print_log(conf)
            sql_data_md5 = None
            self.change_backup_status("data_list", "sql_list", 'mysql', "backup_status", -1, conf["name"], msg="开始备份mysql数据库:{}".format(conf["name"]))
            mysql_info = public.M("databases").where("name=?", (conf['name'],)).find()
            if not mysql_info or isinstance(mysql_info, str):
                self.print_log("获取mysql数据库信息失败")
                self.change_backup_status("data_list", "sql_list", 'mysql', "backup_status", 2, conf["name"], msg="获取mysql数据库信息失败")
                return
            # 远程数据库只备份信息
            if mysql_info["db_type"] == 2:
                config = {
                    "mysql_info": mysql_info,
                    "cloud_server": public.M('database_servers').where('id=?', (mysql_info['sid'])).select()
                }
                if not config["cloud_server"]:
                    self.print_log("获取远程数据库信息失败")
                    self.change_backup_status("data_list", "sql_list", 'mysql', "backup_status", 2, conf["name"], msg="获取远程数据库信息失败")
                    return
                else:
                    config["cloud_server"] = config["cloud_server"][0]
                self.write_id_config("data_list", "sql_list", "mysql", config=config, sec_name=conf["name"])
                self.change_backup_status("data_list", "sql_list", 'mysql', "backup_status", 1, conf["name"])
                self.print_log("->>>备份mysql数据库:{}完成,远程数据库".format(conf["name"]))
                return
            self.print_log("32")
            sql_path = '/tmp/{}.sql'.format(conf["name"])
            md5_name = self.generate_md5(sql_path)
            save_path = os.path.join(self.backup_path, "backup", md5_name)
            sql_data = save_path
            if not os.path.exists(save_path):
                if not os.path.exists(self.backup_path):
                    self.print_log("333333333332")
                    os.makedirs(self.backup_path)
                _MYSQLDUMP_BIN = public.get_mysqldump_bin()
                db_password = public.M("config").where("id=?", (1,)).getField("mysql_root")
                self.print_log("33333333333333333333332")
                try:
                    db_port = int(panelMysql.panelMysql().query("show global variables like 'port'")[0][1])
                except:
                    db_port = 3306
                mysql_obj = db_mysql.panelMysql()
                flag = mysql_obj.set_host('localhost', db_port, None, 'root', db_password)
                if flag is False:
                    self.print_log("连接mysql数据库失败")
                    self.change_backup_status("data_list", "sql_list", 'mysql', "backup_status", 2, conf["name"], msg="连接mysql数据库失败")
                    return
                # 开始备份数据库
                resp = public.ExecShell("{} --help | grep set-gtid-purged >> /tmp/backup_sql.log".format(_MYSQLDUMP_BIN))[0]
                set_gtid_purged = ''
                if resp.find("--set-gtid-purged") != -1:
                    set_gtid_purged = "--set-gtid-purged=OFF"
                shell = "'{mysqldump_bin}' {set_gtid_purged} --opt --skip-lock-tables --single-transaction --routines --events --skip-triggers --default-character-set='{db_charset}' --force " \
                        "--host='{db_host}' --port={db_port} --user='{db_user}' --password='{db_password}' '{db_name}' > {sql_path}".format(
                    mysqldump_bin=_MYSQLDUMP_BIN,
                    set_gtid_purged=set_gtid_purged,
                    db_charset='utf8mb4',
                    db_host='localhost',
                    db_port=db_port,
                    db_user='root',
                    db_password=db_password,
                    db_name=conf["name"],
                    sql_path=sql_path
                )
                public.ExecShell(shell)
                if not self.check_mysql_files(sql_path, conf["name"]):
                    self.print_log("3333333333333333333333333333333")
                    self.change_backup_status("data_list", "sql_list", 'mysql', "backup_status", 2, conf["name"], msg="备份mysql数据库:{}失败".format(conf["name"]))
                    self.print_log("333333333333333333333333333333333333333333333333333")
                    return
                time.sleep(0.1)
                if os.path.exists(sql_path):
                    # 转移文件
                    sql_data_md5 = self.get_md5(sql_path)
                    sql_data = self.copy_file(sql_path)
                    self.print_log("备份mysql数据库:{}数据打包成功！".format(conf["name"]))
                    public.ExecShell('rm -rf {}'.format(sql_path))

            # 备份数据库的权限
            sql_power = database.database().GetDatabaseAccess(public.to_dict_obj({'name': conf["name"]}))['msg']
            sql_info = database.database().GetInfo(public.to_dict_obj({'db_name': conf["name"]}))
            mysql_version = public.readFile('/www/server/mysql/version.pl')
            config = {
                "sql_data": sql_data,
                "mysql_info": mysql_info,
                "sql_power": sql_power,
                "sql_info": sql_info,
                "mysql_version": mysql_version,
                "sql_data_md5": sql_data_md5,
            }
            self.print_log(config)
            self.print_log("3333333333333333333")
            self.write_id_config("data_list", "sql_list", "mysql", config=config, sec_name=conf["name"])
            self.change_backup_status("data_list", "sql_list", 'mysql', "backup_status", 1, conf["name"], msg="备份mysql数据库:{}完成".format(conf["name"]))
            self.print_log("->>>备份mysql数据库:{}完成".format(conf["name"]))
        except:
            print(public.get_error_info())

    def backup_mongodb_data(self, conf):
        self.print_log("->>>开始备份mongo数据库:{}".format(conf["name"]))
        mongo_info = public.M("databases").where("name=? AND LOWER(type)=LOWER('mongodb')", (conf['name'],)).find()
        if not mongo_info or isinstance(mongo_info, str):
            self.print_log("获取mongo数据库信息失败")
            self.change_backup_status("data_list", "sql_list", 'mongodb', "backup_status", 2, conf["name"], msg="获取mongo数据库信息失败")
            return
        # 远程数据库只备份信息
        if mongo_info["db_type"] == 2:
            config = {
                "mongo_info": mongo_info,
                "cloud_server": public.M('database_servers').where('db_type=?', ('mongodb')).select()
            }
            self.write_id_config("data_list", "sql_list", "mongodb", config=config, sec_name=conf["name"])
            self.change_backup_status("data_list", "sql_list", 'mongodb', "backup_status", 1, conf["name"], msg="备份mongo数据库:{}完成".format(conf["name"]))
            return

        # 备份数据库
        mongo_path = '/tmp/{}'.format(conf["name"])
        md5_name = self.generate_md5(mongo_path)
        save_path = os.path.join(self.backup_path, "backup", md5_name)
        mongo_data = save_path
        mongo_data_md5 = None
        if not os.path.exists(save_path):
            _MONGODBDUMP_BIN = os.path.join(public.get_setup_path(), "mongodb/bin/mongodump")
            _MONGOEXPORT_BIN = os.path.join(public.get_setup_path(), "mongodb/bin/mongoexport")
            db_password = mongo_info["password"]
            from databaseModel.mongodbModel import panelMongoDB
            if mongo_info["db_type"] == 0:
                if panelMongoDB().get_config_options("security", "authorization", "disabled") == "enabled":
                    if not db_password:
                        return public.returnMsg(False, "数据库密码为空！请先设置数据库密码！")
                else:
                    db_password = None
                db_port = panelMongoDB.get_config_options("net", "port", 27017)
            db_host = "127.0.0.1"
            db_user = mongo_info["username"]
            mongodump_shell = "'{mongodump_bin}' --host='{db_host}' --port={db_port} --db='{db_name}' --out='{out}'".format(
                mongodump_bin=_MONGODBDUMP_BIN,
                db_host=db_host,
                db_port=int(db_port),
                db_name=conf["name"],
                out=mongo_path,
            )
            if db_password:  # 本地未开启安全认证
                mongodump_shell += " --username='{db_user}' --password={db_password}".format(db_user=db_user, db_password=public.shell_quote(str(db_password)))

            public.ExecShell('{}'.format(mongodump_shell))
            time.sleep(0.1)
            if os.path.exists(mongo_path):
                self.print_log("备份mongo数据库:{}完成".format(conf["name"]))
                # 转移文件
                mongo_data = self.copy_file(mongo_path)
                mongo_data_md5 = self.get_md5(mongo_path)
                public.ExecShell('rm -rf {}'.format(mongo_path))
        from databaseModel.mongodbModel import main
        sql_power = main().GetDatabaseAccess(public.to_dict_obj({'user_name': mongo_info["username"]}))['data']
        config = {
            "mongo_data": mongo_data,
            "mongo_info": mongo_info,
            "sql_power": sql_power,
            "mongo_data_md5": mongo_data_md5
        }
        self.print_log(config)
        self.write_id_config("data_list", "sql_list", "mongodb", config=config, sec_name=conf["name"])
        self.change_backup_status("data_list", "sql_list", 'mongodb', "backup_status", 1, conf["name"], msg="备份mongo数据库:{}完成".format(conf["name"]))
        self.print_log("->>>备份mongo数据库:{}完成".format(conf["name"]))

    def backup_redis_data(self, conf):
        self.print_log("->>>开始备份redis数据库:{}".format(conf["name"]))
        from databaseModel.redisModel import panelRedisDB
        redis_db = panelRedisDB().set_host(decode_responses=False)
        status, redis_obj = redis_db.connect(0)
        if status is False:
            self.print_log("连接redis数据库失败")
            self.change_backup_status("data_list", "sql_list", 'redis', "backup_status", 2, conf["name"], msg="连接redis数据库失败")
            return
        redis_obj.bgsave()

        # 等待后台保存操作完成
        while True:
            # 获取持久化信息
            progress_info = redis_obj.info("persistence")
            bgsave_in_progress = int(progress_info.get("rdb_bgsave_in_progress", 0))
            if bgsave_in_progress == 0:
                break
            time.sleep(1)  # 等待1秒后再次检查
        dump_path = os.path.join(redis_obj.config_get("dir")["dir"], redis_obj.config_get("dbfilename")["dbfilename"])
        if not os.path.exists(dump_path):
            self.print_log("备份redis数据库:{}失败".format(conf["name"]))
            self.change_backup_status("data_list", "sql_list", 'redis', "backup_status", 2, conf["name"], msg="备份redis数据库:{}失败".format(conf["name"]))
            return
        redis_data = self.copy_file(dump_path)
        redis_data_md5 = self.get_md5(dump_path)
        public.ExecShell('rm -rf {}'.format(dump_path))
        config = {
            "redis_data": redis_data,
            "redis_info": conf,
            "redis_data_md5": redis_data_md5
        }
        self.print_log(config)
        self.write_id_config("data_list", "sql_list", "redis", config=config, sec_name=conf["name"])
        self.change_backup_status("data_list", "sql_list", 'redis', "backup_status", 1, conf["name"], msg="备份redis数据库:{}完成".format(conf["name"]))
        self.print_log("->>>备份redis数据库:{}完成".format(conf["name"]))

    def backup_pgsql_data(self, conf):
        self.print_log("->>>开始备份pgsql数据库:{}".format(conf["name"]))
        pgsql_info = public.M("databases").where("name=? AND LOWER(type)=LOWER('pgsql')", (conf['name'],)).find()
        self.print_log(pgsql_info)
        pgsql_data = None
        if not pgsql_info or isinstance(pgsql_info, str):
            self.print_log("获取pgsql数据库信息失败")
            self.change_backup_status("data_list", "sql_list", 'pgsql', "backup_status", 2, conf["name"], msg="获取pgsql数据库信息失败")
            return
        # 远程数据库只备份信息
        if pgsql_info["db_type"] == 2:
            config = {
                "pgsql_info": pgsql_info,
                "cloud_server": public.M('database_servers').where('db_type=?', ('pgsql')).select()
            }
            self.write_id_config("data_list", "sql_list", "pgsql", config=config, sec_name=conf["name"])
            self.change_backup_status("data_list", "sql_list", 'pgsql', "backup_status", 1, conf["name"], msg="备份pgsql数据库:{}完成".format(conf["name"]))
            self.print_log("->>>备份pgsql数据库:{}完成".format(conf["name"]))
            return

        # 备份数据库
        db_name = pgsql_info["name"]
        pgsql_data_md5 = None
        db_user = "postgres"
        db_host = "127.0.0.1"
        from databaseModel.pgsqlModel import panelPgsql
        db_port = panelPgsql().get_config_options("port", int, 5432)
        t_path = os.path.join(public.get_panel_path(), "data/postgresAS.json")
        if not os.path.isfile(t_path):
            self.change_backup_status("data_list", "sql_list", 'pgsql', "backup_status", 2, conf["name"], msg="获取数据库密码失败")
            self.print_log("获取数据库密码失败")
        db_password = ""
        if os.path.exists(t_path):
            try:
                db_password = json.loads(public.readFile(t_path)).get("password", "")
            except:
                db_password = ""
        if not db_password:
            self.change_backup_status("data_list", "sql_list", 'pgsql', "backup_status", 2, conf["name"], msg="获取数据库密码失败")
            self.print_log("获取数据库密码失败")
            return

        pgsql_obj = panelPgsql().set_host(host=db_host, port=db_port, database=None, user=db_user, password=db_password)
        status, err_msg = pgsql_obj.connect()
        if status is False:
            self.change_backup_status("data_list", "sql_list", 'pgsql', "backup_status", 2, conf["name"], msg="连接数据库失败[{}:{}]".format(db_host, db_port))
            self.print_log("连接数据库失败[{}:{}]".format(db_host, db_port))
            return
        _PGDUMP_BIN = os.path.join(public.get_setup_path(), "pgsql/bin/pg_dump")
        backup_path = '/tmp/{}.sql'.format(db_name)
        md5_name = self.generate_md5(backup_path)
        pgsql_data = os.path.join(self.backup_path, "backup", md5_name)
        if not os.path.exists(backup_path):
            shell = "'{pgdump_bin}' --host='{db_host}' --port={db_port} --username='{db_user}' --dbname='{db_name}' --clean > {backup_path}".format(
                pgdump_bin=_PGDUMP_BIN,
                db_host=db_host,
                db_port=int(db_port),
                db_user=db_user,
                db_name=db_name,
                backup_path=backup_path
            )
            public.ExecShell(shell)
            time.sleep(0.1)
            if os.path.exists(backup_path):
                self.print_log("备份pgsql数据库:{}完成".format(conf["name"]))
                # 转移文件
                pgsql_data = self.copy_file(backup_path)
                pgsql_data_md5 = self.get_md5(backup_path)
                public.ExecShell('rm -rf {}'.format(backup_path))
        config = {
            "pgsql_data": pgsql_data,
            "pgsql_info": pgsql_info,
            "pgsql_data_md5": pgsql_data_md5
        }
        self.print_log(config)
        self.write_id_config("data_list", "sql_list", "pgsql", config=config, sec_name=conf["name"])
        self.change_backup_status("data_list", "sql_list", 'pgsql', "backup_status", 1, conf["name"], msg="备份pgsql数据库:{}完成".format(conf["name"]))
        self.print_log("->>>备份pgsql数据库:{}完成".format(conf["name"]))

    def backup_sqlServer_data(self, conf):
        self.print_log("->>>开始备份sqlServer数据库:{}".format(conf["name"]))
        sql_info = public.M("databases").where("name=? AND LOWER(type)=LOWER('sqlserver')", (conf['name'],)).find()
        if not sql_info or isinstance(sql_info, str):
            self.print_log("获取sqlServer数据库信息失败")
            self.change_backup_status("data_list", "sql_list", 'sqlserver', "backup_status", 2, conf["name"], msg="获取sqlServer数据库信息失败")
            return
        # 远程数据库只备份信息
        config = {
            "sql_info": sql_info,
            "cloud_server": public.M('database_servers').where('db_type=?', ('sqlserver')).select()
        }
        self.write_id_config("data_list", "sql_list", "sqlserver", config=config, sec_name=conf["name"])
        self.change_backup_status("data_list", "sql_list", 'sqlserver', "backup_status", 1, conf["name"], msg="备份sqlServer数据库:{}完成".format(conf["name"]))
        self.print_log("->>>备份sqlServer数据库:{}完成".format(conf["name"]))
        return

    def backup_ftp_data(self, conf):
        self.print_log("->>>开始备份ftp:{}".format(conf["name"]))
        self.print_log(conf)
        ftp_info = public.M("ftps").where("id=?", (conf["id"],)).find()
        if not ftp_info or isinstance(ftp_info, str):
            self.print_log("获取ftp信息失败")
            self.change_backup_status("data_list", "ftp_list", "ftp", "backup_status", 2, conf["name"], msg="获取ftp信息失败")
            return
        ftp_data = None
        if os.path.exists(ftp_info["path"]):
            ftp_data = self.copy_file(ftp_info["path"])
        ftp_data_md5 = self.get_md5(ftp_info["path"])
        config = {
            "ftp_data": ftp_data,
            "ftp_info": ftp_info,
            "ftp_data_md5": ftp_data_md5
        }
        self.print_log(config)
        self.write_id_config("data_list", "ftp_list", conf["name"], config=config)
        self.change_backup_status("data_list", "ftp_list", conf['name'], "backup_status", 1, msg="备份ftp:{}完成".format(conf["name"]))
        self.print_log("->>>备份ftp:{}完成".format(conf["name"]))

    def backup_terminal_data(self, conf):
        self.print_log("->>>开始备份服务器列表,常用命令")
        self.print_log(conf)
        terminal_data = None
        terminal_data_path = '/www/server/panel/config/ssh_info'
        if os.path.exists(terminal_data_path):
            terminal_data = self.copy_file(terminal_data_path)
        terminal_data_md5 = self.get_md5(terminal_data_path)
        config = {
            "terminal_data": terminal_data,
            "terminal_data_md5": terminal_data_md5,
        }
        self.write_id_config("data_list", "terminal_list", "服务器列表", config=config)
        self.write_id_config("data_list", "terminal_list", "常用命令", config=config)
        self.change_backup_status("data_list", "terminal_list", "服务器列表", "backup_status", 1, msg="备份服务器列表完成")
        self.change_backup_status("data_list", "terminal_list", "常用命令", "backup_status", 1, msg="备份常用命令完成")
        self.print_log("->>>备份服务器列表,常用命令完成")

    def backup_crontab_data(self, conf):
        self.print_log("->>>开始备份计划任务:{}".format(conf["name"]))
        crontab_list = public.M("crontab").select()
        self.write_id_config("data_list", "crontab_list", "crontab", config=crontab_list)
        self.change_backup_status("data_list", "crontab_list", "计划任务列表", "backup_status", 1, msg="备份计划任务完成")
        self.print_log("->>>备份计划任务:{}完成".format(conf["name"]))

    def backup_port_data(self, conf):
        self.print_log("->>>开始备份端口:{}".format(conf["name"]))
        self.print_log(conf)
        from firewallModel.comModel import main as com
        port_data = None
        port_data_md5 = None
        try:
            port_data_path = com().export_rules(public.to_dict_obj({"data": {'rule_name': 'port_rule'}}))['msg']
            port_data = self.copy_file(port_data_path)
            port_data_md5 = self.get_md5(port_data_path)
        except:
            self.change_backup_status("data_list", "safety", "port_list", "backup_status", 2, conf["name"], msg="备份端口:{}出错,程序出错".format(conf["name"]))
            self.print_log("备份端口:{}出错".format(conf["name"]))
            return
        config = {
            "port_data": port_data,
            "port_data_md5": port_data_md5,
            "port_data_path": port_data_path
        }
        self.print_log(config)
        self.write_id_config("data_list", "safety", "port_list", config=config, sec_name=conf["name"])
        self.change_backup_status("data_list", "safety", "port_list", "backup_status", 1, conf["name"], msg="备份端口:{}完成".format(conf["name"]))
        self.print_log("->>>备份端口:{}完成".format(conf["name"]))

    def backup_ip_data(self, conf):
        self.print_log("->>>开始备份IP:{}".format(conf["name"]))
        from firewallModel.comModel import main as com
        ip_data = None
        ip_data_md5 = None
        try:
            ip_list_path = com().export_rules(public.to_dict_obj({"rule": 'ip', 'chain': 'ALL'}))['msg']
            ip_data = self.copy_file(ip_list_path)
            ip_data_md5 = self.get_md5(ip_list_path)
        except:
            self.change_backup_status("data_list", "safety", "ip_list", "backup_status", 2, conf["name"], msg="备份IP:{}出错，程序出错".format(conf["name"]))
            print(public.get_error_info())
            self.print_log("备份IP:{}出错".format(conf["name"]))
            return
        config = {
            "ip_data": ip_data,
            "ip_data_md5": ip_data_md5,
            "ip_list_path": ip_list_path
        }
        self.write_id_config("data_list", "safety", "ip_list", config=config, sec_name=conf["name"])
        self.change_backup_status("data_list", "safety", "ip_list", "backup_status", 1, conf["name"], msg="备份IP:{}完成".format(conf["name"]))
        self.print_log(config)
        self.print_log("->>>备份IP:{}完成".format(conf["name"]))

    def backup_port_redirect_data(self, conf):
        self.print_log("->>>开始备份端口转发:{}".format(conf["name"]))
        from firewallModel.comModel import main as com
        forward = None
        forward_md5 = None
        try:
            forward_path = com().export_rules(public.to_dict_obj({"rule": 'forward'}))['msg']
            forward = self.copy_file(forward_path)
            forward_md5 = self.get_md5(forward_path)
        except:
            self.change_backup_status("data_list", "safety", "ip_list", "port_redirect", 2, conf["name"], msg="备份IP:{}出错，程序出错".format(conf["name"]))
            print(public.get_error_info())
            self.print_log("备份IP:{}出错".format(conf["name"]))
            return
        config = {
            "forward": forward,
            "forward_md5": forward_md5,
            "forward_path": forward_path
        }
        self.write_id_config("data_list", "safety", "port_redirect", config=config, sec_name=conf["name"])
        self.change_backup_status("data_list", "safety", "port_redirect", "backup_status", 1, conf["name"], msg="备份端口转发:{}完成".format(conf["name"]))
        self.print_log(config)
        self.print_log("->>>备份端口转发:{}完成".format(conf["name"]))

    def backup_area_data(self, conf):
        self.print_log("->>>开始备份区域:{}".format(conf["name"]))
        area_data = None
        area_data_md5 = None
        try:
            area_data_path = safe_firewall_main().export_rules(public.to_dict_obj({'rule_name': 'country_rule'}))['msg']
            area_data = self.copy_file(area_data_path)
            area_data_md5 = self.get_md5(area_data_path)
        except:
            self.change_backup_status("data_list", "safety", "area_list", "backup_status", 2, conf["name"], msg="备份区域:{}出错，程序出错".format(conf["name"]))
            self.print_log("备份区域:{}出错".format(conf["name"]))
            return
        config = {
            "area_data": area_data,
            "area_data_md5": area_data_md5,
            "area_data_path": area_data_path
        }
        self.write_id_config("data_list", "safety", "area_list", config=config, sec_name=conf["name"])
        self.change_backup_status("data_list", "safety", "area_list", "backup_status", 1, conf["name"], msg="备份区域:{}完成".format(conf["name"]))
        self.print_log("->>>备份区域:{}完成".format(conf["name"]))

    def ssh_config_data(self, conf):
        self.print_log("->>>开始备份SSH配置:{}".format(conf["name"]))
        ssh_data = None
        ssh_data_md5 = None
        ssh_config_path = '/etc/ssh/sshd_config'
        if os.path.exists(ssh_config_path):
            ssh_data = self.copy_file(ssh_config_path)
            ssh_data_md5 = self.get_md5(ssh_config_path)
        else:
            self.print_log("未找到SSH配置文件")
            self.change_backup_status("data_list", "safety", "ssh_config", "backup_status", 2, conf["name"], msg="未找到SSH配置文件")
            return
        config = {
            "ssh_data": ssh_data,
            "ssh_data_md5": ssh_data_md5
        }
        self.write_id_config("data_list", "safety", "ssh_config", config=config, sec_name=conf["name"])
        self.change_backup_status("data_list", "safety", "ssh_config", "backup_status", 1, conf["name"], msg="备份SSH配置:{}完成".format(conf["name"]))
        self.print_log(config)
        self.print_log("->>>备份SSH配置:{}完成".format(conf["name"]))

    def backup_words_data(self, conf):
        self.print_log("->>>开始备份关键词:{}".format(conf["name"]))
        words_path = "/www/server/panel/config/thesaurus.json"
        wrods_data = None
        wrod_data_md5 = None
        if os.path.exists(words_path):
            wrods_data = self.copy_file(words_path)
            wrod_data_md5 = self.get_md5(words_path)
        config = {
            "wrods_data": wrods_data,
            "wrod_data_md5": wrod_data_md5
        }
        self.write_id_config("data_list", "safety", "words", config=config, sec_name=conf["name"])
        self.change_backup_status("data_list", "safety", "words", "backup_status", 1, conf["name"], msg="备份关键词:{}完成".format(conf["name"]))
        self.print_log(config)
        self.print_log("->>>备份关键词:{}完成".format(conf["name"]))

    def backup_sqlite_data(self, conf):
        self.print_log("->>>开始备份sqlite:{}".format(conf["name"]))
        sqlite_path = conf["name"]
        sqlite_data = None
        sqlite_data_md5 = None
        if os.path.exists(sqlite_path):
            sqlite_data = self.copy_file(sqlite_path)
            sqlite_data_md5 = self.get_md5(sqlite_path)
        config = {
            "sqlite_data": sqlite_data,
            "sqlite_info": conf["name"],
            "sqlite_data_md5": sqlite_data_md5
        }
        self.write_id_config("data_list", "sql_list", "sqlite", config=config, sec_name=conf["name"])
        self.change_backup_status("data_list", "sql_list", "sqlite", "backup_status", 1, conf["name"], msg="备份sqlite:{}完成".format(conf["name"]))
        self.print_log(config)
        self.print_log("->>>备份sqlite:{}完成".format(conf["name"]))

    # ======================================================================
    #     恢复数据
    # ======================================================================

    # 获取备份记录
    def get_backup_record(self, id):
        """
        获取备份记录
        :param id:
        :return:
        """
        if id not in self.config:
            return public.returnMsg(False, '任务不存在！')
        if self.backup_record is None:
            backup_log_path = self.config[id]["backup_log_path"]
            res = json.loads(public.readFile(backup_log_path))
            self.backup_record = res

    # 恢复入口函数
    def reduction(self, id):
        """
        还原
        :param id:
        :return:
        """
        if not isinstance(id, str):
            id = id["id"]
        conf = self.config[id]
        self.get_backup_record(id)
        reduction = json.loads(public.readFile(conf["reduction_task_config_path"]))["reduction_config"]
        if not reduction:
            self.print_log("还原信息不存在")
            return public.returnMsg(False, '还原配置不存在')
        if isinstance(reduction, str):
            reduction = json.loads(reduction)
        self.reduction_config = reduction
        self.reduction_log_path = conf["reduction_log_path"]
        # 取备份中存储的数据
        try:
            backup_data_path = os.path.join(self.backup_path, id + "_backup.json")
            self.backup_task_data = json.loads(public.readFile(backup_data_path))
        except:
            pass
        if not self.backup_task_data:
            self.print_log("备份信息检查失败，恢复失败")
            return public.returnMsg(False, '备份信息检查失败，恢复失败')

        conf["status"] = 3
        self.status = 4
        conf["start_time"] = time.strftime('%Y-%m-%d %X')
        self.write_config(id, conf)

        # 开始解压备份文件
        try:
            if not os.path.exists(conf['backup_path'] + '.tar.gz'):
                self.print_log("备份文件不存在")
                return public.returnMsg(False, '备份文件不存在')
            public.ExecShell('mkdir -p {}'.format(conf['backup_path']))
            public.ExecShell('tar -xzf {} -C {}'.format(conf['backup_path'] + '.tar.gz', conf['backup_path']))
        except:
            pass
        # 还原环境
        self.reduction_env(self.reduction_config)
        # 还原数据
        self.reduction_data(self.reduction_config)
        # 还原配置
        # self.reduction_panel_config(self.reduction_config)
        conf["status"] = self.status
        conf['access_num'] = self.access_num
        conf['error_num'] = self.error_num
        self.write_config(id, conf)
        return public.returnMsg(True, '还原结束')

    # 写恢复进度日志
    def change_reduction_status(self, block, name="", son_name="", status_name="", status=0, sec_name='', msg=''):
        if status == 2:
            self.status = 5
            self.error_num += 1
        if status == 1:
            self.access_num += 1
        if sec_name != '':
            for i in range(len(self.reduction_config[block][name][son_name])):
                if self.reduction_config[block][name][son_name][i]['name'] == sec_name:
                    self.reduction_config[block][name][son_name][i][status_name] = status
                    if msg != '':
                        self.reduction_config[block][name][son_name][i]['msg'] = msg
        elif son_name != "":
            for i in range(len(self.reduction_config[block][name])):
                if self.reduction_config[block][name][i]['name'] == son_name:
                    self.reduction_config[block][name][i][status_name] = status
                    if msg != '':
                        self.reduction_config[block][name][i]['msg'] = msg
        elif name != "":
            self.reduction_config[block][name][status_name] = status
            if msg != '':
                self.reduction_config[block][name]['msg'] = msg
        else:
            self.reduction_config[block][status_name] = status
            if msg != '':
                self.reduction_config[block]['msg'] = msg
        public.writeFile(self.reduction_log_path, json.dumps(self.reduction_config))

    def reduction_env(self, conf):
        env_conf = conf["env_list"]
        connect = {
            "php": self.reduction_php,
            "mysql": self.reduction_mysql,
            "mongo": self.reduction_mongo,
            "redis": self.reduction_redis,
            "pgsql": self.reduction_pgsql,
            "nginx": self.reduction_nginx,
            "apache": self.reduction_apache,
            "ftp": self.reduction_ftp,
        }
        for k, v in env_conf.items():
            for i in v:
                if i['status'] == 1:
                    # 取备份的信息
                    try:
                        connect[k](i)
                    except:
                        print(public.get_error_info())
                        self.change_reduction_status("env_list", k, i["name"], "reduction_status", 2, msg="{}{}还原失败，程序出错".format(k, i["name"]))
                else:
                    if i['status'] != 3 and i['name']:
                        self.change_reduction_status("env_list", k, i["name"], "reduction_status", 4, msg="{}{}未备份".format(k, i["name"]))

    # 检测进程是否存在
    def cehck_pid_status(self, pid):
        try:
            ps = psutil.Process(int(pid))
            return True
        except:
            return False

    def reduction_php(self, conf):
        self.print_log("->>>开始还原PHP环境:{}".format(conf["name"]))
        self.change_reduction_status("env_list", "php", conf["name"], "reduction_status", -1, msg='开始还原php{}环境'.format(conf["name"]))
        pid_file = '/www/server/php/{}/var/run/php-fpm.pid'.format(conf["name"])
        if conf["name"] == '52':
            pid_file = '/www/server/php/{}/logs/php-fpm.pid'.format(conf["name"])
        php_backup_config = [j for i, j in self.backup_task_data['env_list']["php"].items() if i == conf["name"]]
        if not php_backup_config or isinstance(php_backup_config, str):
            self.print_log("获取php{}备份信息失败".format(conf["name"]))
            self.change_reduction_status("env_list", "php", conf["name"], "reduction_status", 2, msg="获取php{}备份信息失败".format(conf["name"]))
            return
        php_backup_config = php_backup_config[0]
        # 开始检测当前php是否安装
        php_path = '/www/server/php/{}'.format(conf["name"])
        if not os.path.exists(php_path):
            self.print_log("php{}未安装,开始安装".format(conf["name"]))
            # 安装指定的php版本
            public.ExecShell('cd /www/server/panel/install && /bin/bash install_soft.sh 1 install php {}.{} &>> {}'.format(conf["name"][0], conf["name"][1], self.logs_file))
            self.print_log('php{}安装完成,检测安装状态中.....'.format(conf["name"]))
            pid = public.readFile(pid_file)
            if not self.cehck_pid_status(pid):
                public.ExecShell('/etc/init.d/php-fpm-{} start'.format(conf["name"]))
                time.sleep(0.1)
                pid = public.readFile(pid_file)
                if not self.cehck_pid_status(pid):
                    self.print_log('php{}安装失败'.format(conf["name"]))
                    self.change_reduction_status("env_list", "php", conf["name"], "reduction_status", 2, msg="php{}安装失败".format(conf["name"]))
                    public.ExecShell("rm -rf /www/server/php/{}".format(conf["name"]))
                    return
            self.print_log('php{}安装完成'.format(conf["name"]))
        else:
            self.print_log('php{}已安装'.format(conf["name"]))
        self.print_log('状态检测中.....')
        pid = public.readFile(pid_file)
        if not self.cehck_pid_status(pid):
            self.print_log('php{}未启动，正在启动中......'.format(conf["name"]))
            public.ExecShell('/etc/init.d/php-fpm-{} start'.format(conf["name"]))
            time.sleep(0.1)
            pid = public.readFile(pid_file)
            self.print_log(pid)
            if not self.cehck_pid_status(pid):
                self.print_log('php{}启动失败'.format(conf["name"]))
                self.change_reduction_status("env_list", "php", conf["name"], "reduction_status", 2, msg="php{}启动失败".format(conf["name"]))
                return
        self.print_log('php{}已启动'.format(conf["name"]))

        # 开始安装拓展
        so_path = "/www/server/php/{}/lib/php/extensions/".format(conf["name"])
        if os.path.exists(so_path) and len(os.listdir(so_path)) > 0:
            so_path = os.path.join(so_path, os.listdir(so_path)[0])
            development_list = php_backup_config["php_development"]
        else:
            development_list = []
        now_development_list = ajax.ajax().GetPHPConfig(public.to_dict_obj({"version": conf["name"]}))['libs']
        now_development_list = {i['name']: i for i in now_development_list}
        install_err = []
        for development in development_list:
            development = development.lower()
            if development.lower() in now_development_list.keys() and now_development_list[development.lower()]["status"] != True and conf["name"] in now_development_list[development.lower()][
                "versions"] and not os.path.exists(os.path.join(so_path, "{}.so".format(development))):
                self.print_log("开始安装php{}拓展:{}".format(conf["name"], development))
                public.ExecShell(
                    'wget -O {sh_name}.sh https://download.bt.cn/install/1/{sh_name}.sh && sh {sh_name}.sh install {php_version} $>> {log}'.format(sh_name=development.lower(),
                                                                                                                                                   php_version=conf["name"],
                                                                                                                                                   log=self.logs_file))
                # 检测是否安装成功
                if 'swoole' in development:
                    development = 'swoole'
                res = public.ExecShell('/www/server/php/{}/bin/php -m'.format(conf["name"]))
                if development in res[0].lower() and "{}.so".format(development) in os.listdir(so_path):
                    self.print_log("php{}拓展:{}安装成功".format(conf["name"], development))
                else:
                    self.print_log("php{}拓展:{}安装失败".format(conf["name"], development))
                    install_err.append(development)
        # 安装失败的重新安装
        for development in install_err:
            development = development.lower()
            self.print_log("开始安装php{}拓展:{}".format(conf["name"], development))
            public.ExecShell(
                'wget -O {sh_name}.sh https://download.bt.cn/install/1/{sh_name}.sh && sh {sh_name}.sh install {php_version} $>> {log}'.format(sh_name=development.lower(), php_version=conf["name"],
                                                                                                                                               log=self.logs_file))
            # 检测是否安装成功
            if 'swoole' in development:
                development = 'swoole'
            res = public.ExecShell('/www/server/php/{}/bin/php -m'.format(conf["name"]))
            try:
                if development in res[0].lower() or "{}.so".format(development) in os.listdir(so_path):
                    self.print_log("php{}拓展:{}安装成功".format(conf["name"], development))
                else:
                    self.print_log("php{}拓展:{}安装失败".format(conf["name"], development))
            except:
                pass
        # 开始还原php配置文件
        php_ini_path = '/www/server/php/{}/etc/php.ini'.format(conf["name"])
        php_fpm_path = '/www/server/php/{}/etc/php-fpm.conf'.format(conf["name"])
        php_ini_res = self.uncopy_file(php_backup_config["php_ini"], php_ini_path, isfile=True)
        php_fpm_res = self.uncopy_file(php_backup_config["php_fpm"], php_fpm_path, isfile=True)
        if not php_ini_res or not php_fpm_res:
            self.print_log("还原php{}配置文件失败".format(conf["name"]))
            self.change_reduction_status("env_list", "php", conf["name"], "reduction_status", 2, msg="还原php{}配置文件失败".format(conf["name"]))
            return
        # 安全防护拓展 移除
        if not os.path.exists(so_path) or 'security_notice.so' not in os.listdir(so_path):
            public.ExecShell("sed -i '/security_notice/ s/.*/ /' {}".format(php_ini_path))
            public.ExecShell("sed -i '/security.notice/ s/.*/ /' {}".format(php_fpm_path))
        self.print_log("还原php{}配置文件完成".format(conf["name"]))
        # 重载php
        public.ExecShell('/etc/init.d/php-fpm-{} reload'.format(conf["name"]))
        self.print_log("->>>还原PHP环境:{}完成".format(conf["name"]))
        self.change_reduction_status("env_list", "php", conf["name"], "reduction_status", 1, msg="还原php{}配置文件完成".format(conf["name"]))

    def reduction_mysql(self, conf):
        self.print_log("->>>开始还原mysql环境:{}".format(conf["name"]))
        self.print_log(conf)
        backup_mysql_conf = self.backup_task_data['env_list']['mysql']
        self.change_reduction_status("env_list", "mysql", conf['name'], status_name="reduction_status", status=-1, msg="开始还原mysql{}环境".format(conf["name"]))
        self.print_log(backup_mysql_conf)
        # 检测mysql是否安装和版本是否相同
        mysql_path = '/www/server/mysql/version.pl'
        if not os.path.exists(mysql_path):
            self.print_log("mysql未安装,开始安装mysql{}".format(backup_mysql_conf["version"]))
            public.ExecShell('mkdir -p /www/server/mysql')
            version = backup_mysql_conf["version"]
            if version.count('.') > 1:
                version = version.split('.')[:2]
                version = '.'.join(version)
            public.ExecShell("/bin/bash /www/server/panel/install/install_soft.sh 1 install mysql {} &>> {}".format(version, self.logs_file))
        mysql_version = public.readFile('/www/server/mysql/version.pl')
        if not mysql_version:
            self.print_log("mysql读取版本异常，请手动检查")
            self.change_reduction_status("env_list", "mysql", conf['name'], status_name="reduction_status", status=2, msg="mysql读取版本异常，请手动检查")
        else:
            mysql_version = mysql_version.strip()
        if mysql_version != conf["name"]:
            self.print_log("mysql版本不一致,请手动操作将mysql版本升级到{}版本".format(conf["name"]))
            self.change_reduction_status("env_list", "mysql", conf['name'], status_name="reduction_status", status=2, msg="mysql版本不一致,请手动操作将mysql版本升级到{}版本".format(conf["name"]))
            return
        else:
            self.print_log("mysql版本一致")
        # 恢复配置文件
        self.print_log('开始恢复mysql配置文件')
        config_path = '/etc/my.cnf'
        res = self.uncopy_file(backup_mysql_conf["mysql_conf"], config_path, isfile=True, md5=backup_mysql_conf["mysql_conf_md5"])
        if not res:
            self.change_reduction_status("env_list", "mysql", conf['name'], status_name="reduction_status", status=2, msg="还原mysql{}配置文件失败".format(conf["name"]))
        self.print_log("->>>还原mysql环境:{}完成".format(conf["name"]))
        self.change_reduction_status("env_list", "mysql", conf['name'], status_name="reduction_status", status=1, msg="还原mysql{}完成".format(conf["name"]))

    def reduction_mongo(self, conf):
        self.print_log("->>>开始还原mongo环境:{}".format(conf["name"]))
        self.print_log(conf)
        self.print_log("->>>还原mongo环境:{}完成".format(conf["name"]))

    def reduction_redis(self, conf):
        self.print_log("->>>开始还原redis环境:{}".format(conf["name"]))
        self.print_log(conf)
        self.print_log("->>>还原redis环境:{}完成".format(conf["name"]))

    def reduction_pgsql(self, conf):
        self.print_log("->>>开始还原pgsql环境:{}".format(conf["name"]))
        self.print_log(conf)
        self.print_log("->>>还原pgsql环境:{}完成".format(conf["name"]))

    def reduction_nginx(self, conf):
        self.print_log("->>>开始还原nginx环境:{}".format(conf["name"]))
        # self.print_log(conf)
        # self.print_log(self.backup_task_data['env_list']['nginx'])
        self.change_reduction_status("env_list", "nginx", conf['name'], status_name="reduction_status", status=-1, msg="开始还原nginx环境")
        nginx_path = '/www/server/nginx'
        # 关闭nginx 服务
        if os.path.exists(nginx_path):
            public.ExecShell("/etc/init.d/nginx stop")
            self.print_log('关闭nginx服务')
        self.print_log("开始恢复nginx")
        flag = 1
        # 恢复nginx文件
        res = self.uncopy_file(self.backup_task_data['env_list']['nginx']["nginx_file"], "/www/server/nginx/", unbak=True)
        if not res:
            flag = 0
        # 还原nginx启动文件
        if self.backup_task_data['env_list']['nginx']["nginx_cmd"]:
            res = self.uncopy_file(self.backup_task_data['env_list']['nginx']["nginx_cmd"], "/etc/init.d/nginx", isfile=True, md5=self.backup_task_data['env_list']['nginx']["nginx_cmd_md5"])
            if not res:
                flag = 0
        if self.backup_task_data['env_list']['nginx']["nginx_systemd"]:
            res = self.uncopy_file(self.backup_task_data['env_list']['nginx']["nginx_systemd"], "/lib/systemd/system/nginx.service", isfile=True,
                                   md5=self.backup_task_data['env_list']['nginx']["nginx_systemd_md5"])
            if not res:
                flag = 0
        if not flag:
            # 还原之前的版本
            if os.path.exists("/www/server/nginx_bak"):
                public.ExecShell("rm -rf /www/server/nginx")
                public.ExecShell("mv /www/server/nginx_bak /www/server/nginx")
            if os.path.exists("/etc/init.d/nginx_bak"):
                public.ExecShell("rm -rf /etc/init.d/nginx")
                public.ExecShell("mv /etc/init.d/nginx_bak /etc/init.d/nginx")
            if os.path.exists("/lib/systemd/system/nginx.service_bak"):
                public.ExecShell("rm -rf /lib/systemd/system/nginx.service")
                public.ExecShell("mv /lib/systemd/system/nginx.service_bak /lib/systemd/system/nginx.service")
            self.change_reduction_status("env_list", "nginx", conf['name'], status_name="reduction_status", status=2, msg="还原nginx失败")
            public.ExecShell('/etc/init.d/nginx start')
            self.print_log("还原nginx失败")
            return
        # 启动nginx
        public.ExecShell("/etc/init.d/nginx start")
        self.change_reduction_status("env_list", "nginx", conf['name'], status_name="reduction_status", status=1, msg="还原nginx完成")
        self.print_log("->>>还原nginx环境:{}完成".format(conf["name"]))

    def reduction_apache(self, conf):
        self.print_log("->>>开始还原apache环境:{}".format(conf["name"]))
        self.print_log(conf)
        self.change_reduction_status("env_list", "apache", conf['name'], status_name="reduction_status", status=-1, msg="开始还原apache{}环境".format(conf["name"]))
        self.print_log(self.backup_task_data['env_list']['apache'])
        apache_path = '/www/server/apache/version.pl'
        if not os.path.exists(apache_path):
            # 安装apache
            public.ExecShell('mkdir -p /www/server/apache')
            version = self.backup_task_data['env_list']['apache']["version"]
            if version.count('.') > 1:
                version = version.split('.')[:2]
                version = '.'.join(version)
            public.ExecShell("/bin/bash /www/server/panel/install/install_soft.sh 1 install apache {} &>> {}".format(version, self.logs_file))
        apache_version = public.readFile('/www/server/apache/version.pl')
        if not apache_version:
            self.print_log("apache读取版本异常，请手动检查")
            self.change_reduction_status("env_list", "apache", conf['name'], status_name="reduction_status", status=2, msg="apache读取版本异常，请手动检查")
        else:
            apache_version = apache_version.strip()
        if apache_version != conf["name"]:
            public.ExecShell('rm -rf /www/server/apache')
            self.print_log('apache版本不一致，升级apache到{}版本'.format(conf["name"]))
            version = conf["name"]
            if version.count('.') > 1:
                version = version.split('.')[:2]
                version = '.'.join(version)
            public.ExecShell("/bin/bash /www/server/panel/install/install_soft.sh 1 install apache {} &>> {}".format(version, self.logs_file))
        # 恢复配置文件
        res = self.uncopy_file(self.backup_task_data['env_list']['apache']["apache_conf"], "/www/server/apache/", isfile=True, md5=self.backup_task_data['env_list']['apache']["apache_conf_md5"])
        if not res:
            self.change_reduction_status("env_list", "apache", conf['name'], status_name="reduction_status", status=2, msg="还原apache{}配置文件失败".format(conf["name"]))
        self.print_log("->>>还原apache环境:{}完成".format(conf["name"]))

    def reduction_ftp(self, conf):
        self.print_log("->>>开始还原ftp环境:{}".format(conf["name"]))
        self.print_log(conf)
        self.change_reduction_status("env_list", "ftp", conf['name'], status_name="reduction_status", status=-1, msg="开始还原ftp{}环境".format(conf["name"]))
        self.print_log(self.backup_task_data['env_list']['ftp'])
        # 检测ftp是否安装
        ftp_path = '/www/server/pure-ftpd'
        if not os.path.exists(ftp_path):
            # 安装ftp
            version = self.backup_task_data['env_list']['ftp']["version"]
            public.ExecShell("/bin/bash /www/server/panel/install/install_soft.sh 1 install pure-ftpd {}&>> {}".format(version, self.logs_file))
        # 恢复配置文件
        self.print_log('开始恢复ftp配置文件')
        res = self.uncopy_file(self.backup_task_data['env_list']['ftp']["ftp_conf"], "/www/server/pure-ftpd/etc/pure-ftpd.conf", md5=self.backup_task_data['env_list']['ftp']["ftp_conf_md5"])
        if not res:
            self.change_reduction_status("env_list", "ftp", conf['name'], status_name="reduction_status", status=2, msg="还原ftp{}配置文件失败".format(conf["name"]))
            # 恢复配置文件
            public.ExecShell('rm -rf /www/server/pure-ftpd')
            public.ExecShell('mv /www/server/pure-ftpd/etc/pure-ftpd.conf_bak /www/server/pure-ftpd/etc/pure-ftpd.conf')
        # 检查日志开启状态
        self.print_log('开始检查ftp日志开启状态')
        rsyslog_path = "/etc/rsyslog.conf"
        cofig = public.readFile(rsyslog_path)
        if "ftp.*" in cofig:
            log_status = 1
        else:
            log_status = 0
        if self.backup_task_data['env_list']['ftp']["log_status"] != log_status:
            if self.backup_task_data['env_list']['ftp']["log_status"]:
                public.ExecShell("sed -i '/ftp\.\*/d' {}".format(rsyslog_path))
            else:
                public.ExecShell("echo 'ftp.*    /var/log/pureftpd.log' >> {}".format(rsyslog_path))
            public.ExecShell('/etc/init.d/rsyslog restart')
        self.print_log('ftp日志开启状态恢复完成')
        self.change_reduction_status("env_list", "ftp", conf['name'], status_name="reduction_status", status=1, msg="还原ftp{}完成".format(conf["name"]))
        self.print_log("->>>还原ftp环境:{}完成".format(conf["name"]))

    def reduction_data(self, conf):
        data_conf = conf["data_list"]
        connect = {
            "php": self.reduction_php_data,
            "java": self.reduction_java_data,
            "node": self.reduction_node_data,
            "python": self.reduction_python_data,
            "other": self.reduction_other_data,
            "net": self.reduction_net_data,
            "proxy": self.reduction_proxy_data,
            "html": self.reduction_html_data,
            "mysql": self.reduction_mysql_data,
            "mongodb": self.reduction_mongodb_data,
            "redis": self.reduction_redis_data,
            "pgsql": self.reduction_pgsql_data,
            "ftp_list": self.reduction_ftp_data,
            "terminal_list": self.reduction_terminal_data,
            "crontab_list": self.reduction_crontab_data,
            "port_list": self.reduction_port_data,
            "ip_list": self.reduction_ip_data,
            "port_redirect": self.reduction_port_redirect_data,
            "area_list": self.reduction_area_data,
            "ssh_config": self.reduction_ssh_config_data,
            "words": self.reduction_words_data,
            "sqlite": self.reduction_sqlite_data,
        }
        for k, v in data_conf.items():
            if k in ['site_list', 'sql_list', 'config_list', "safety"]:
                for type, dates in v.items():
                    if type not in connect.keys():
                        pass
                    for data in dates:
                        if int(data['status']) in [1, -1, 2] and data['backup_status'] == 1:
                            try:
                                connect[type.lower()](data)
                            except:
                                print(public.get_error_info())
                                self.change_reduction_status("data_list", k, type, "reduction_status", 2, data["name"], msg="{}还原失败，程序出错".format(data["name"]))
                        else:
                            self.change_reduction_status("data_list", k, type, "reduction_status", 4, data["name"], msg="{}备份状态异常".format(data["name"]))
            elif k in ['ftp_list']:
                for i in v:
                    if i['status'] in [1, -1, 2] and i['backup_status'] == 1:
                        try:
                            connect[k](i)
                        except:
                            print(public.get_error_info())
                            self.change_reduction_status("data_list", "ftp_list", i["name"], "reduction_status", 2, msg="{}还原失败，程序出错".format(i["name"]))
                    else:
                        self.change_reduction_status("data_list", "ftp_list", i["name"], "reduction_status", 4, msg="{}备份状态异常".format(i["name"]))
            else:
                for j in v:
                    if j['status'] in [1, -1, 2] and j['backup_status'] == 1:
                        try:
                            connect[k](j)
                        except:
                            print(public.get_error_info())
                            self.change_reduction_status("data_list", k, j["name"], "reduction_status", 2, msg="{}还原失败，程序出错".format(j["name"]))
                    else:
                        if j['status'] != 3 and j['name']:
                            self.change_reduction_status("data_list", k, j["name"], "reduction_status", 4, msg="{}备份状态异常".format(j["name"]))

    def reduction_php_data(self, conf):
        self.print_log(")->>>开始还原PHP数据:{}".format(conf["name"]))
        backup_conf_config = self.backup_task_data.get('data_list', {}).get('site_list', {}).get('php', {}).get(conf['name'], {})
        self.change_reduction_status("data_list", "site_list", "php", "reduction_status", -1, conf["name"], msg="开始还原php{}数据".format(conf["name"]))
        if not backup_conf_config:
            self.print_log("获取php{}备份信息失败".format(conf["name"]))
            self.change_reduction_status("data_list", "site_list", "php", "reduction_status", 2, conf["name"], msg="获取php{}备份信息失败".format(conf["name"]))
            return
        # 查看当前网站配置
        now_site_config = public.M('sites').where('name=?', (conf['name'],)).select()
        site_info = backup_conf_config["site_info"]
        # php动态项目特殊处理：
        import panelSite
        from mod.project.php.php_asyncMod import main as php_asyncMod
        is_phpmod = False
        if 'project_config' in site_info.keys():
            site_info['project_config'] = json.loads(site_info['project_config'])
            if 'type' in site_info['project_config'].keys() and site_info['project_config']['type'].lower() == 'phpmod':
                is_phpmod = True
        if now_site_config and isinstance(now_site_config, list):
            # 同步网站的sql配置
            now_site_config = now_site_config[0]
            site_info['ps'] = now_site_config['ps']
            site_info['id'] = now_site_config['id']
            site_info.pop('index')
            if isinstance(site_info.get('project_config', ''), dict):
                site_info['project_config'] = json.dumps(site_info['project_config'])
            site_info.pop('php_version')
            public.M('sites').where('name=? and id=?', (site_info["name"], now_site_config["id"])).update(site_info)
        else:
            if not is_phpmod:
                args = public.dict_obj()
                args.path = site_info['path']
                args.ftp = False
                args.type = 'PHP'
                args.type_id = site_info['type_id']
                args.ps = site_info['ps']
                args.port = '80'
                args.version = site_info['php_version']
                args.need_index = 0
                args.need_404 = 0
                args.sql = False
                args.codeing = 'utf8mb4'
                args.webname = json.dumps({"domain": site_info['name'], "domainlist": [], "count": 0})
                panelSite.panelSite().AddSite(args)
            else:
                args = public.dict_obj()
                args.site_path = site_info['path']
                args.project_cmd = site_info['project_config']['start_cmd']
                args.install_dependence = '0'
                args.php_version = site_info['project_config']['php_version']
                args.sql = False
                args.project_ps = site_info['ps']
                args.project_port = ''
                args.open_proxy = '0'
                args.project_proxy_path = ''
                args.run_user = site_info['project_config']['run_user']
                args.composer_version = ''
                args.webname = json.dumps({"domain": site_info['name'], "domainlist": [], "count": 0})
                php_asyncMod().create_project(args)

        self.print_log('面板网站存储信息同步完成')

        # 恢复网站文件
        site_path = site_info['path']
        res = self.uncopy_file(backup_conf_config["site_file"], site_path, isfile=False, unbak=True)
        if not res:
            self.change_reduction_status("data_list", "site_list", "php", "reduction_status", 2, conf["name"], msg="还原php{}网站文件失败".format(conf["name"]))
            self.print_log("还原php{}网站文件失败".format(conf["name"]))
            return

        # 同步网站域名
        site_id = public.M('sites').where('name=?', (conf['name'],)).getField('id')
        domains = backup_conf_config["domains"]
        if domains and isinstance(domains, list):
            domains = {i["name"]: i for i in domains}
        sql = public.M('domain')
        now_domains = sql.where('pid=?', (site_id,)).select()
        if now_domains and isinstance(now_domains, list):
            now_domains = {i["name"]: i for i in now_domains}
        else:
            now_domains = {}

        print(domains)
        print(now_domains)
        # 删除多余的域名
        del_domains = [i for i in now_domains.keys() if i not in domains.keys()]
        if del_domains:
            public.M('domain').where('name in (?)', (','.join(del_domains))).delete()
            self.print_log('删除多余的域名成功：{}'.format(','.join(del_domains)))
        # 修改域名信息
        for domain, value in domains.items():
            if domain not in now_domains.keys():
                self.print_log('添加域名：{}'.format(domain))
                value.pop('id')
                value['pid'] = site_id
                public.M('domain').insert(value)
            else:
                domains[domain].pop('id')
                value['pid'] = site_id
                public.M('domain').where('name=?', (domain,)).update(value)

        self.print_log("php{}网站域名恢复完成".format(conf["name"]))

        # 恢复网站nginx和apache配置文件
        self.print_log('开始恢复php{}网站nginx和apache配置文件'.format(conf["name"]))
        nginx_conf_path = '/www/server/panel/vhost/nginx/{}.conf'.format(conf["name"])
        apache_conf_path = '/www/server/panel/vhost/apache/{}.conf'.format(conf["name"])
        if backup_conf_config['nginx_config'] and os.path.exists(backup_conf_config['nginx_config']):
            res = self.uncopy_file(backup_conf_config["nginx_config"], nginx_conf_path, isfile=True, md5=backup_conf_config["nginx_config_md5"])
            if not res:
                self.change_reduction_status("data_list", "site_list", "php", "reduction_status", 2, conf["name"], msg="还原php{}nginx配置文件失败".format(conf["name"]))
                self.print_log("还原php{}nginx配置文件失败".format(conf["name"]))
                return
        if backup_conf_config['apache_config'] and os.path.exists(backup_conf_config['apache_config']):
            res = self.uncopy_file(backup_conf_config["apache_config"], apache_conf_path, isfile=True, md5=backup_conf_config["apache_config_md5"])
            if not res:
                self.change_reduction_status("data_list", "site_list", "php", "reduction_status", 2, conf["name"], msg="还原php{}apache配置文件失败".format(conf["name"]))
                self.print_log("还原php{}apache配置文件失败".format(conf["name"]))
                return
        self.print_log("php{}网站nginx和apache配置文件恢复完成".format(conf["name"]))

        # 恢复网站重定向
        self.print_log('开始恢复php{}网站重定向'.format(conf["name"]))
        redirect_list = backup_conf_config["redirect_list"]
        __redirectfile = "/www/server/panel/data/redirect.conf"
        redirectconf = json.loads(public.readFile(__redirectfile))
        red_name = {j['sitename']: i for i, j in enumerate(redirectconf)}
        for i in redirect_list:
            if i["sitename"] not in red_name.keys():
                redirectconf.append(i)
            elif i['sitename'] in red_name.keys():
                redirectconf[red_name[i['sitename']]] = i
        public.writeFile(__redirectfile, json.dumps(redirectconf))
        res_nginx = self.uncopy_file(backup_conf_config["redirect_nginx_data"], '/www/server/panel/vhost/nginx/redirect/{}'.format(conf["name"]), isfile=False)
        res_apache = self.uncopy_file(backup_conf_config["redirect_apache_data"], '/www/server/panel/vhost/apache/redirect/{}'.format(conf["name"]), isfile=False)
        if res_nginx and res_apache:
            self.print_log("恢复重定向成功")
        else:
            self.print_log("恢复重定向失败")
            self.change_reduction_status("data_list", "site_list", "php", "reduction_status", 2, conf["name"], msg="恢复重定向失败")
        # 删除多余得重定向
        old_list = [i['redirectname'] for i in redirect_list]
        now_redirect_list = [i['redirectname'] for i in redirectconf if i['sitename'] == conf["name"]]
        for redirect in now_redirect_list:
            if redirect not in old_list:
                if is_phpmod:
                    res = php_asyncMod().remove_project_redirect(public.to_dict_obj({"sitename": conf["name"], "redirectname": redirect}))
                else:
                    res = panelSite.panelSite().DeleteRedirect(public.to_dict_obj({"siteName": conf["name"], "redirectName": redirect}))
                if res['status']:
                    self.print_log("删除多余重定向：{}成功".format(redirect))
                else:
                    self.print_log("删除多余重定向：{}失败".format(redirect))
                    self.change_reduction_status("data_list", "site_list", "php", "reduction_status", 2, conf["name"], msg="删除多余重定向：{}失败".format(redirect))
        self.print_log("php{}网站重定向恢复完成".format(conf["name"]))

        # 恢复反向代理
        self.print_log('开始恢复php{}网站反向代理'.format(conf["name"]))
        proxy_list = backup_conf_config["proxy_list"]
        if not is_phpmod:
            __proxyfile = '{}/data/proxyfile.json'.format(public.get_panel_path())

        else:
            __proxyfile = "{}/data/mod_proxy_file.conf".format(public.get_panel_path())
        try:
            proxyUrl = json.loads(public.readFile(__proxyfile))
        except:
            proxyUrl = {}
        proxy_name = {j['sitename']: i for i, j in enumerate(proxyUrl)}
        for i in proxy_list:
            if i["sitename"] not in proxy_name.keys():
                proxyUrl.append(i)
            elif i['sitename'] in proxy_name.keys():
                proxyUrl[proxy_name[i['sitename']]] = i

        public.writeFile(__proxyfile, json.dumps(proxyUrl))
        res_n = self.uncopy_file(backup_conf_config["proxy_nginx_data"], '/www/server/panel/vhost/nginx/proxy/{}'.format(conf["name"]), isfile=False)
        res_a = self.uncopy_file(backup_conf_config["proxy_apache_data"], '/www/server/panel/vhost/apache/proxy/{}'.format(conf["name"]), isfile=False)
        if not res_n or not res_a:
            self.change_reduction_status("data_list", "site_list", "php", "reduction_status", 2, conf["name"], msg="恢复nginx反向代理失败")
            self.print_log("恢复反向代理失败")

        # 删除多余的反向代理
        old_list = [i['proxyname'] for i in proxy_list]
        proxy_name = [i for i in proxyUrl if i['sitename'] == conf["name"]]
        for proxy in proxy_name:
            if proxy['proxyname'] not in old_list:
                if is_phpmod:
                    res = php_asyncMod().remove_proxy(public.to_dict_obj({"sitename": conf["name"], "proxyname": proxy['proxyname']}))
                else:
                    res = panelSite.panelSite().DeleteProxy(public.to_dict_obj({"siteName": conf["name"], "proxyName": proxy['proxyname']}))
                if not res['status']:
                    self.print_log("删除多余反向代理：{}失败".format(proxy['proxyname']))
                    self.change_reduction_status("data_list", "site_list", "php", "reduction_status", 2, conf["name"], msg="删除多余反向代理：{}失败".format(proxy['proxyname']))
                    return
                self.print_log("删除多余反向代理：{}成功".format(proxy['proxyname']))

        self.print_log("php{}网站反向代理恢复完成".format(conf["name"]))

        # 开始恢复ssl证书
        self.print_log('开始恢复php{}网站ssl证书'.format(conf["name"]))
        if backup_conf_config["ssl_info"]:
            ssl_path = '/www/server/panel/vhost/cert/{}'.format(conf["name"])
            res = self.uncopy_file(backup_conf_config["ssl_info"], ssl_path, isfile=False)
            if not res:
                self.change_reduction_status("data_list", "site_list", "php", "reduction_status", 2, conf["name"], msg="还原php{}ssl证书失败".format(conf["name"]))
                self.print_log("还原php{}ssl证书失败".format(conf["name"]))
                return
            self.print_log("php{}网站ssl证书恢复完成".format(conf["name"]))
        else:
            self.print_log("php{}网站无ssl证书".format(conf["name"]))

        # 开始恢复目录加密访问
        self.print_log('开始恢复php{}网站目录加密访问'.format(conf["name"]))
        if backup_conf_config["dir_auth_json"]:
            dir_auth_path = '/tmp/{}'.format(conf["name"])
            self.uncopy_file(backup_conf_config["dir_auth_json"], dir_auth_path, unbak=True)
            if os.path.exists(dir_auth_path):
                res = public.readFile(dir_auth_path)
                if res:
                    res = json.loads(res)
                    data = res.get(conf["name"], [])
                    if data:
                        config_path = '/www/server/panel/data/site_dir_auth.json'
                        if os.path.exists(config_path):
                            res = public.readFile(config_path)
                            if res:
                                res = json.loads(res)
                            else:
                                res = {}
                            res[conf["name"]] = data
                            public.writeFile(config_path, json.dumps(res))
                        else:
                            conf = {conf["name"]: data}
                            public.writeFile(config_path, json.dumps(conf))
        if backup_conf_config["dir_auth_file"]:
            res = self.uncopy_file(backup_conf_config["dir_auth_file"], '/www/server/panel/vhost/nginx/dir_auth/{}'.format(conf["name"]), isfile=False)
            if not res:
                self.change_reduction_status("data_list", "site_list", "php", "reduction_status", 2, conf["name"], msg="还原php{}目录加密访问失败".format(conf["name"]))
                self.print_log("还原php{}目录加密访问失败".format(conf["name"]))
                return
        self.print_log("php{}网站目录加密访问恢复完成".format(conf["name"]))

        # 开始恢复子目录域名绑定
        if backup_conf_config["banding"]:
            if is_phpmod:
                pass
            else:
                self.print_log('开始恢复php{}网站子目录域名绑定'.format(conf["name"]))
                res = panelSite.panelSite().GetDirBinding(public.to_dict_obj({"id": site_id}))
                banding_list = res["binding"]
                banding_list = {i["domain"]: i for i in banding_list}
                old_list = {i["domain"]: i for i in backup_conf_config["banding"]}
                for k, v in old_list.items():
                    if k not in banding_list.keys():
                        res = panelSite.panelSite().AddDirBinding(public.to_dict_obj({"id": site_id, "domain": v["domain"], "dirName": v["path"]}))
                        if not res["status"]:
                            self.print_log("恢复子目录域名绑定：{}失败".format(k))
                            self.change_reduction_status("data_list", "site_list", "php", "reduction_status", 2, conf["name"], msg="恢复子目录域名绑定：{}失败".format(k))
                            return
                        self.print_log("恢复子目录域名绑定：{}成功".format(k))
                for k, v in banding_list.items():
                    if k not in old_list.keys():
                        res = panelSite.panelSite().DelDirBinding(public.to_dict_obj({"id": v['id']}))
                        if not res["status"]:
                            self.print_log("删除多余子目录域名绑定：{}失败".format(k))
                            self.change_reduction_status("data_list", "site_list", "php", "reduction_status", 2, conf["name"], msg="删除多余子目录域名绑定：{}失败".format(k))
                            return
                        self.print_log("删除多余子目录域名绑定：{}成功".format(k))
        # 开始恢复伪静态
        if backup_conf_config["pseudo_static_data"]:
            self.print_log('开始恢复php{}网站伪静态'.format(conf["name"]))
            res = self.uncopy_file(backup_conf_config["pseudo_static_data"], '/www/server/panel/vhost/rewrite/{}.conf'.format(conf["name"]), isfile=True,
                                   md5=backup_conf_config["pseudo_static_data_md5"])
            if not res:
                self.change_reduction_status("data_list", "site_list", "php", "reduction_status", 2, conf["name"], msg="还原php{}伪静态失败".format(conf["name"]))
                self.print_log("还原php{}伪静态失败".format(conf["name"]))
                return
            self.print_log("php{}网站伪静态恢复完成".format(conf["name"]))
        # 还原网站相关数据库
        self.print_log('开始还原php{}网站相关数据库'.format(conf["name"]))
        if backup_conf_config["database_info"]:
            self.reduction_mysql_data(backup_conf_config['database_info'])

        if backup_conf_config["ftp_info"]:
            self.reduction_ftp_data(backup_conf_config["ftp_info"])
        self.print_log('php{}网站相关数据库恢复完成'.format(conf["name"]))

        self.print_log("->>>还原PHP数据:{}完成".format(conf["name"]))
        self.change_reduction_status("data_list", "site_list", "php", "reduction_status", 1, conf["name"], msg="还原成功！")

    def reduction_java_data(self, conf):
        self.print_log("->>>开始还原java数据:{}".format(conf["name"]))
        self.print_log(conf)
        self.print_log("->>>还原java数据:{}完成".format(conf["name"]))

    def reduction_node_data(self, conf):
        self.print_log("->>>开始还原node数据:{}".format(conf["name"]))
        self.print_log(conf)
        self.print_log("->>>还原node数据:{}完成".format(conf["name"]))

    def reduction_python_data(self, conf):
        self.print_log("->>>开始还原python数据:{}".format(conf["name"]))
        self.print_log(conf)
        self.print_log("->>>还原python数据:{}完成".format(conf["name"]))

    def reduction_other_data(self, conf):
        self.print_log("->>>开始还原other数据:{}".format(conf["name"]))
        self.print_log(conf)
        self.print_log("->>>还原other数据:{}完成".format(conf["name"]))

    def reduction_net_data(self, conf):
        self.print_log("->>>开始还原net数据:{}".format(conf["name"]))
        self.print_log(conf)
        self.print_log("->>>还原net数据:{}完成".format(conf["name"]))

    def reduction_proxy_data(self, conf):
        self.print_log("->>>开始还原proxy数据:{}".format(conf["name"]))
        self.change_reduction_status("data_list", "site_list", "proxy", "reduction_status", -1, conf["name"], msg="开始还原proxy{}数据".format(conf["name"]))
        proxy_config_path = "/www/server/proxy_project/sites/{}".format(conf["name"])
        nginx_config_path = "/www/server/panel/vhost/nginx/{}.conf".format(conf["name"])
        apache_config_path = "/www/server/panel/vhost/apache/{}.conf".format(conf["name"])
        # 恢复面板存储得网站信息
        self.print_log('开始恢复数据库存储信息proxy:{}'.format(conf["name"]))
        site_info = self.backup_task_data['data_list']['site_list']['proxy'].get(conf["name"], {})
        if not site_info:
            self.print_log("获取proxy{}备份信息失败".format(conf["name"]))
            self.change_reduction_status("data_list", "site_list", "proxy", "reduction_status", 2, conf["name"], msg="获取proxy{}备份信息失败")
            return
        site_db_info = site_info["site_info"][0]
        now_site_info = public.M('sites').where('name=?', (conf["name"],)).select()
        if now_site_info and not isinstance(now_site_info, str):
            now_site_info = now_site_info[0]
            site_db_info.pop('id')
            now_site_info.update(site_db_info)
            now_site_info.pop('index')
            public.M('sites').where('name=? and project_type="proxy"', (conf["name"],)).update(now_site_info)
        else:
            proxy_cache_dir = "/www/wwwroot/{}/proxy_cache_dir".format(conf["name"])
            if not os.path.exists(proxy_cache_dir):
                public.ExecShell('mkdir -p {}'.format(proxy_cache_dir))
                if os.path.exists(proxy_cache_dir):
                    public.ExecShell('chown -R www:www {}'.format(proxy_cache_dir))
                    public.ExecShell('chmod -R 755 {}'.format(proxy_cache_dir))
                    self.print_log('创建proxy{}缓存目录成功'.format(conf["name"]))
                else:
                    self.print_log('创建proxy{}缓存目录失败'.format(conf["name"]))
                    self.change_reduction_status("data_list", "site_list", "proxy", "reduction_status", 2, conf["name"], msg="创建proxy{}缓存目录失败{}".format(conf["name"], proxy_cache_dir))
                    return
            site_db_info.pop('id')
            site_db_info['project_type'] = 'proxy'
            site_db_info.pop('index')
            public.M('sites').insert(site_db_info)
        self.print_log('面板网站存储信息同步完成')
        # 还原网站配置文件
        self.print_log('开始恢复proxy{}网站配置文件'.format(conf["name"]))
        res = self.uncopy_file(site_info["proxy_config"], proxy_config_path, isfile=True, md5=site_info["proxy_config_md5"])
        if not res:
            self.print_log('还原proxy{}配置文件失败'.format(conf["name"]))
            self.change_reduction_status("data_list", "site_list", "proxy", "reduction_status", 2, conf["name"], msg="还原proxy{}配置文件失败".format(conf["name"]))
            return
        self.print_log('proxy{}网站配置文件恢复完成'.format(conf["name"]))

        # 恢复nginx和apache配置文件
        self.print_log('开始恢复proxy{}网站nginx和apache配置文件'.format(conf["name"]))
        if site_info['nginx_config'] and os.path.exists(site_info['nginx_config']):
            res = self.uncopy_file(site_info["nginx_config"], nginx_config_path, isfile=True, md5=site_info["nginx_config_md5"])
            if not res:
                self.change_reduction_status("data_list", "site_list", "proxy", "reduction_status", 2, conf["name"], msg="还原proxy{}nginx配置文件失败".format(conf["name"]))
                self.print_log("还原proxy{}nginx配置文件失败".format(conf["name"]))
                return
        if site_info['apache_config'] and os.path.exists(site_info['apache_config']):
            res = self.uncopy_file(site_info["apache_config"], apache_config_path, isfile=True, md5=site_info["apache_config_md5"])
            if not res:
                self.change_reduction_status("data_list", "site_list", "proxy", "reduction_status", 2, conf["name"], msg="还原proxy{}apache配置文件失败".format(conf["name"]))
                self.print_log("还原proxy{}apache配置文件失败".format(conf["name"]))
                return
        self.print_log('proxy{}网站nginx和apache配置文件恢复完成'.format(conf["name"]))
        self.print_log("->>>还原proxy数据:{}完成".format(conf["name"]))
        self.change_reduction_status("data_list", "site_list", "proxy", "reduction_status", 1, conf["name"], msg="还原成功！")

    def reduction_html_data(self, conf):
        self.print_log("->>>开始还原html数据:{}".format(conf["name"]))
        self.print_log(conf)
        self.print_log("->>>还原html数据:{}完成".format(conf["name"]))

    def reduction_mysql_data(self, conf):
        self.print_log("->>>开始还原mysql数据:{}".format(conf["name"]))
        bakup_config = self.backup_task_data['data_list']['sql_list']['mysql'].get(conf['name'], {})
        self.change_reduction_status("data_list", "sql_list", "mysql", "reduction_status", -1, conf["name"], msg="开始还原mysql{}数据".format(conf["name"]))
        if not bakup_config:
            self.print_log("获取mysql{}备份信息失败".format(conf["name"]))
            self.change_reduction_status("data_list", "sql_list", "mysql", "reduction_status", 2, conf["name"], msg="获取mysql{}备份信息失败".format(conf["name"]))
            return

        if int(bakup_config['mysql_info']['db_type']) == 2:
            # 开始恢复远程数据库配置
            self.print_log('开始还原mysql{}远程数据库配置'.format(conf["name"]))
            cloud_server = bakup_config['cloud_server']
            now_cloud_server = public.M('database_servers').where('id=?', (bakup_config['mysql_info']['sid'])).select()
            if not now_cloud_server:
                public.M('database_servers').insert(cloud_server)
            else:
                cloud_server.pop('id')
                public.M('database_servers').where('id=?', (bakup_config['mysql_info']['sid'])).update(cloud_server)
            now_db_info = public.M('databases').where('name=?', (conf["name"],)).select()
            if now_db_info:
                public.M('databases').where('name=?', (conf["name"],)).delete()
            db_info = bakup_config['mysql_info']
            db_info.pop('id')
            public.M('databases').insert(db_info)
            self.print_log('mysql{}远程数据库配置恢复完成'.format(conf["name"]))
            self.change_reduction_status("data_list", "sql_list", "mysql", "reduction_status", 1, conf["name"], msg="还原mysql{}数据库成功".format(conf["name"]))
            return

            # 恢复数据库配置
        self.print_log('开始恢复mysql{}数据库配置'.format(conf["name"]))
        now_db_info = public.M('databases').where('name=?', (conf["name"],)).select()
        if now_db_info and not isinstance(now_db_info, str):
            now_db_info = now_db_info[0]
            now_db_info['conn_config'] = bakup_config['mysql_info']['conn_config']
            now_db_info['sid'] = bakup_config['mysql_info']['sid']
            public.M('databases').where('name=?', (conf["name"],)).update(now_db_info)
        else:
            # 创建数据库
            args = public.dict_obj()
            args.name = bakup_config['mysql_info']['name']
            args.db_user = bakup_config['mysql_info']['username']
            args.password = bakup_config['mysql_info']['password']
            args.dataAccess = "127.0.0.1"
            args.address = "127.0.0.1"
            args.codeing = 'utf8mb4'
            args.dtype = 'MYSQL'
            args.ps = bakup_config['mysql_info']['ps']
            args.sid = bakup_config['mysql_info']['sid']
            args.list_ip = '0.0.0.0/0'
            args.host = ''
            res = database.database().AddDatabase(args)
            if not res['status']:
                self.print_log("创建mysql{}数据库失败".format(conf["name"]))
                self.change_reduction_status("data_list", "sql_list", "mysql", "reduction_status", 2, conf["name"], msg="创建mysql{}数据库失败,{}".format(conf["name"], res['msg']))
                return
        self.print_log('mysql{}数据库配置恢复完成'.format(conf["name"]))

        # 开始恢复数据库权限
        self.print_log('开始还原mysql{}数据库权限'.format(conf["name"]))
        access = bakup_config["sql_power"]
        args = public.dict_obj()
        args.name = conf["name"]
        args.dataAccess = access
        args.address = ''
        args.access = access
        res = database.database().SetDatabaseAccess(args)
        # 恢复数据记录
        if not res['status']:
            self.change_reduction_status("data_list", "sql_list", "mysql", "reduction_status", 2, conf["name"], msg="还原mysql{}数据库权限失败".format(conf["name"]))
            self.print_log("还原mysql{}数据库权限失败".format(conf["name"]))
            return
        self.print_log('mysql{}数据库权限恢复完成'.format(conf["name"]))

        # 开始恢复数据库数据
        self.print_log('开始还原mysql{}数据库数据'.format(conf["name"]))

        res = self.uncopy_file(bakup_config["sql_data"], '/tmp/{}.sql'.format(conf["name"]), isfile=True, unbak=True)
        if not res:
            self.change_reduction_status("data_list", "sql_list", "mysql", "reduction_status", 2, conf["name"], msg="还原mysql{}数据库数据解压失败".format(conf["name"]))
            self.print_log("还原mysql{}数据库数据解压失败".format(conf["name"]))
        _MYSQL_BIN = public.get_mysql_bin()
        db_charset = public.get_database_character(conf['name'])
        db_password = public.M("config").where("id=?", (1,)).getField("mysql_root")
        if not db_password:
            return public.returnMsg(False, "数据库密码为空！请先设置数据库密码！")
        try:
            db_port = int(panelMysql.panelMysql().query("show global variables like 'port'")[0][1])
        except:
            db_port = 3306
        db_host = "localhost"
        db_user = "root"
        shell = "'{mysql_bin}' --force --default-character-set='{db_charset}' --host='{db_host}' --port={db_port} --user='{db_user}' --password='{password}' '{db_name}'".format(
            mysql_bin=_MYSQL_BIN,
            db_charset=db_charset,
            db_host=db_host,
            db_port=db_port,
            db_user=db_user,
            password=db_password,
            db_name=conf["name"],
        )
        public.ExecShell("{}  < {} &>> {}".format(shell, '/tmp/{}.sql'.format(conf["name"]), self.logs_file))
        # 数据检查
        now_sql_info = database.database().GetInfo(public.to_dict_obj({'db_name': conf["name"]}))
        if now_sql_info['data_size'] != bakup_config["sql_info"]['data_size']:
            self.change_reduction_status("data_list", "sql_list", "mysql", "reduction_status", 2, conf["name"], msg="还原mysql{}数据库数据失败".format(conf["name"]))
            self.print_log("还原mysql{}数据库数据失败".format(conf["name"]))
            return
        self.print_log('mysql{}数据库数据大小校验完成{}'.format(conf["name"], now_sql_info['data_size']))
        self.print_log('mysql{}数据库数据恢复完成'.format(conf["name"]))

        self.print_log("->>>还原mysql数据库:{}完成".format(conf["name"]))
        self.change_reduction_status("data_list", "sql_list", "mysql", "reduction_status", 1, conf["name"], msg="还原mysql{}数据库成功".format(conf["name"]))

    def reduction_mongodb_data(self, conf):
        self.print_log("->>>开始还原mongodb数据:{}".format(conf["name"]))
        self.print_log(conf)
        self.print_log("->>>还原mongodb数据:{}完成".format(conf["name"]))

    def reduction_redis_data(self, conf):
        self.print_log("->>>开始还原redis数据:{}".format(conf["name"]))
        self.print_log(conf)
        self.print_log("->>>还原redis数据:{}完成".format(conf["name"]))

    def reduction_pgsql_data(self, conf):
        self.print_log("->>>开始还原pgsql数据:{}".format(conf["name"]))
        self.print_log(conf)
        self.print_log("->>>还原pgsql数据:{}完成".format(conf["name"]))

    def reduction_ftp_data(self, conf):
        self.print_log("->>>开始还原ftp数据:{}".format(conf["name"]))
        self.change_reduction_status("data_list", "ftp_list", conf["name"], "reduction_status", -1, msg="开始还原ftp{}数据".format(conf["name"]))
        ftp_info = self.backup_task_data['data_list']['ftp_list'].get(conf['name'], {})
        if not ftp_info:
            self.print_log("获取ftp{}备份信息失败".format(conf["name"]))
            self.change_reduction_status("data_list", "ftp_list", conf["name"], "reduction_status", 2, msg="获取ftp{}备份信息失败".format(conf["name"]))
            return
        self.print_log('开始恢复ftp{}用户'.format(conf["name"]))
        import ftp
        now_ftp_info = public.M('ftps').where('name=?', (conf["name"],)).select()
        if now_ftp_info and not isinstance(now_ftp_info, str):
            now_ftp_info = now_ftp_info[0]
            if 'id' in ftp_info.keys(): ftp_info['ftp_info'].pop('id')
            now_ftp_info.update(ftp_info['ftp_info'])
            public.M('ftps').where('name=?', (conf["name"],)).update(now_ftp_info)
            args = public.dict_obj()
            args.id = now_ftp_info['id']
            args.ftp_username = ftp_info['ftp_info']["name"]
            args.new_password = ftp_info['ftp_info']["password"]
            args.path = ftp_info['ftp_info']["path"]
            res = ftp.ftp().SetUser(args)
            if not res['status']:
                self.print_log("修改ftp{}用户失败".format(conf["name"]))
                self.change_reduction_status("data_list", "ftp_list", conf["name"], "reduction_status", 2, msg="修改ftp{}用户失败".format(conf["name"]))
                return
            self.print_log('修改ftp{}用户成功'.format(conf["name"]))
        else:
            args = public.dict_obj()
            args.ftp_username = ftp_info['ftp_info']["name"]
            args.ftp_password = ftp_info['ftp_info']["password"]
            args.path = ftp_info['ftp_info']["path"]
            args.ps = ftp_info['ftp_info']["ps"]
            res = ftp.ftp().AddUser(args)
            if not res['status']:
                self.print_log("创建ftp{}用户失败".format(conf["name"]))
                self.change_reduction_status("data_list", "ftp_list", conf["name"], "reduction_status", 2, msg="创建ftp{}用户失败".format(conf["name"]))
                return
            self.print_log('创建ftp{}用户成功'.format(conf["name"]))
        self.print_log('ftp{}用户恢复完成'.format(conf["name"]))
        # 开始恢复ftp数据
        self.print_log('开始还原ftp{}数据'.format(conf["name"]))
        res = self.uncopy_file(ftp_info["ftp_data"], ftp_info['ftp_info']["path"], isfile=False, unbak=True)
        if not res:
            self.change_reduction_status("data_list", "ftp_list", conf["name"], "reduction_status", 2, msg="还原ftp{}数据失败".format(conf["name"]))
            self.print_log("还原ftp{}数据失败".format(conf["name"]))
        self.print_log('ftp{}数据恢复完成'.format(conf["name"]))
        self.print_log("->>>还原ftp:{}完成".format(conf["name"]))
        self.change_reduction_status("data_list", "ftp_list", conf["name"], "reduction_status", 1, msg="还原ftp{}成功".format(conf["name"]))

    def reduction_terminal_data(self, conf):
        self.print_log("->>>开始还原terminal数据")
        self.print_log(conf)
        backup_conf = self.backup_task_data['data_list']['terminal_list'][conf['name']]
        terminal = "/www/server/panel/config/ssh_info"
        self.print_log('开始还原terminal数据')
        res = self.uncopy_file(backup_conf["terminal_data"], terminal, isfile=False)
        if not res:
            self.change_reduction_status("data_list", "terminal_list", conf["name"], "reduction_status", 2, msg="还原{}数据失败".format(conf["name"]))
            self.print_log("还原terminal数据失败")
            public.ExecShell('rm -rf {}'.format(terminal))
            public.ExecShell('mv {}_bak {} -f'.format(terminal, terminal))
            return
        self.print_log("->>>还原terminal数据完成")
        self.change_reduction_status("data_list", "terminal_list", conf["name"], "reduction_status", 1, msg="还原{}数据成功".format(conf["name"]))

    def reduction_crontab_data(self, conf):
        self.print_log("->>>开始还原crontab数据:{}".format(conf["name"]))
        self.print_log(conf)
        self.change_reduction_status("data_list", "crontab_list", conf["name"], "reduction_status", -1, msg="开始还原计划任务{}数据".format(conf["name"]))
        backup_conf = self.backup_task_data['data_list']['crontab_list']
        cron_list = public.M('crontab').select()
        cron_list = [i['name'] for i in cron_list]
        # 开始恢复计划任务
        successful_imports = 0
        failed_tasks = []
        import crontab
        for task in backup_conf['crontab']:
            if task['name'] not in cron_list:
                # 使用正确的字段和逻辑来创建新的任务字典
                new_task = {
                    "name": task['name'],
                    "type": task['type'],
                    "where1": task['where1'],
                    "hour": task['where_hour'],
                    "minute": task['where_minute'],
                    "status": task['status'],
                    "save": task['save'],
                    "backupTo": task['backupTo'],
                    "sType": task['sType'],
                    "sBody": task['sBody'],
                    "sName": task['sName'],
                    "urladdress": task['urladdress'],
                    "save_local": task['save_local'],
                    "notice": task['notice'],
                    "notice_channel": task['notice_channel'],
                    "db_type": task['db_type'],
                    "split_type": task['split_type'],
                    "split_value": task['split_value'],
                    "keyword": task['keyword'],
                    "post_param": task['post_param'],
                    "flock": task['flock'],
                    "time_set": task['time_set'],
                    "backup_mode": task['backup_mode'],
                    "db_backup_path": task['db_backup_path'],
                    "time_type": task['time_type'],
                    "special_time": task['special_time'],
                    "user_agent": task['user_agent'],
                    "version": task['version'],
                    "table_list": task['table_list'],
                    "result": task['result'],
                    "log_cut_path": task['log_cut_path'],
                    "rname": task['rname'],
                    "type_id": task['type_id'],
                    "second": task.get('second', ''),
                }

                result = crontab.crontab().AddCrontab(new_task)
                if result.get('status', False):
                    successful_imports += 1
                else:
                    failed_tasks.append(task['name'])
            else:
                self.print_log("计划任务{}已存在".format(task['name']))

        if failed_tasks:
            self.print_log("以下任务导入失败:{}".format(failed_tasks))
            self.change_reduction_status("data_list", "crontab_list", conf["name"], "reduction_status", 2, msg="以下任务导入失败:{}".format(failed_tasks))
        self.print_log("->>>还原计划任务数据:{}完成".format(conf["name"]))
        self.change_reduction_status("data_list", "crontab_list", conf["name"], "reduction_status", 1, msg="还原计划任务{}成功".format(conf["name"]))

    def reduction_port_data(self, conf):
        self.print_log("->>>开始还原端口数据:{}".format(conf["name"]))
        self.print_log(conf)
        self.change_reduction_status("data_list", "safety", "port_list", "reduction_status", -1, conf["name"], msg="开始还原端口{}数据".format(conf["name"]))
        # 开始恢复端口规则
        backup_conf = self.backup_task_data['data_list']['safety']['port_list']['端口规则']
        self.print_log(backup_conf)
        self.print_log('开始解压端口数据')
        res = self.uncopy_file(backup_conf["port_data"], backup_conf['port_data_path'], md5=backup_conf['port_data_md5'])
        if not res:
            self.change_reduction_status("data_list", "safety", "port_list", "reduction_status", 2, conf["name"], msg="解压端口数据失败")
            self.print_log("解压端口数据失败")
            return
        res = firewall_main().import_rules(public.to_dict_obj({"rule": "port", "file": backup_conf['port_data_path']}))
        if not res['status']:
            self.change_reduction_status("data_list", "safety", "port_list", "reduction_status", 2, conf["name"], msg="还原端口数据失败" + res['msg'])
            self.print_log("还原端口数据失败" + res['msg'])
            return
        self.print_log("->>>还原端口数据:{}完成".format(conf["name"]))
        self.change_reduction_status("data_list", "safety", "port_list", "reduction_status", 1, conf["name"], msg="还原端口数据成功")

    def reduction_port_redirect_data(self, conf):
        self.print_log("->>>开始还原端口转发数据:{}".format(conf["name"]))
        self.change_reduction_status("data_list", "safety", "port_redirect", "reduction_status", -1, conf["name"], msg="开始还原端口转发{}数据".format(conf["name"]))
        self.print_log(conf)
        backup_conf = self.backup_task_data['data_list']['safety']['port_redirect']['端口转发']
        if not backup_conf:
            self.print_log("获取port_redirect{}备份信息失败".format(conf["name"]))
            self.change_reduction_status("data_list", "safety", "port_redirect", "reduction_status", 2, conf["name"], msg="获取端口转发{}备份信息失败".format(conf["name"]))
            return
        self.print_log('开始解压port_redirect数据')
        res = self.uncopy_file(backup_conf["forward"], backup_conf['forward_path'], md5=backup_conf['forward_md5'])
        if not res:
            self.change_reduction_status("data_list", "safety", "port_redirect", "reduction_status", 2, conf["name"], msg="解压端口转发数据失败")
            self.print_log("解压端口转发数据失败")
            return

        res = firewall_main().import_rules(public.to_dict_obj({"rule": "port_redirect", "file": backup_conf['forward_path']}))
        if not res['status']:
            self.change_reduction_status("data_list", "safety", "port_redirect", "reduction_status", 2, conf["name"], msg="还原端口转发数据失败" + res['msg'])
            self.print_log("还原port_redirect数据失败" + res['msg'])
            return
        self.change_reduction_status("data_list", "safety", "port_redirect", "reduction_status", 1, conf["name"], msg="还原端口转发数据成功")
        self.print_log("->>>还原端口转发数据:{}完成".format(conf["name"]))

    def reduction_area_data(self, conf):
        self.print_log("->>>开始还原地区限制数据:{}".format(conf["name"]))
        self.change_reduction_status("data_list", "safety", "area_list", "reduction_status", -1, conf["name"], msg="开始还原地区限制{}数据".format(conf["name"]))
        backup_conf = self.backup_task_data['data_list']['safety']['area_list'][conf['name']]
        area_data_path = "/www/server/panel/data/firewall/country.json"
        if not backup_conf:
            self.print_log("获取地区限制{}备份信息失败".format(conf["name"]))
            self.change_reduction_status("data_list", "safety", "area_list", "reduction_status", 2, conf["name"], msg="获取area{}备份信息失败".format(conf["name"]))
            return
        # 开始恢复区域封禁
        self.print_log('开始解压地区限制数据')
        res = self.uncopy_file(backup_conf["area_data"], area_data_path, md5=backup_conf['area_data_md5'])
        if not res:
            self.change_reduction_status("data_list", "safety", "area_list", "reduction_status", 2, conf["name"], msg="解压地区限制数据失败")
            self.print_log("解压地区限制数据失败")
            return

        res = safe_firewall_main().import_rules(public.to_dict_obj({"rule_name": "country_rule", "file_name": "country.json"}))
        if not res['status']:
            self.change_reduction_status("data_list", "safety", "area_list", "reduction_status", 2, conf["name"], msg="还原地区限制数据失败" + res['msg'])
            self.print_log("还原area数据失败" + res['msg'])
            return

        self.change_reduction_status("data_list", "safety", "area_list", "reduction_status", 1, conf["name"], msg="还原地区限制数据成功")
        self.print_log("->>>还原地区限制数据:{}完成".format(conf["name"]))

    def reduction_ip_data(self, conf):
        self.print_log("->>>开始还原ip数据:{}".format(conf["name"]))
        self.print_log(conf)
        self.change_reduction_status("data_list", "safety", "ip_list", "reduction_status", -1, conf["name"], msg="开始还原ip{}数据".format(conf["name"]))
        backup_conf = self.backup_task_data['data_list']['safety']['ip_list'][conf['name']]
        if not backup_conf:
            self.print_log("获取ip{}备份信息失败".format(conf["name"]))
            self.change_reduction_status("data_list", "safety", "ip_list", "reduction_status", 2, conf["name"], msg="获取ip{}备份信息失败".format(conf["name"]))
            return

        # 开始恢复IP封禁
        self.print_log('开始解压ip数据')
        res = self.uncopy_file(backup_conf["ip_data"], backup_conf['ip_list_path'], md5=backup_conf['ip_data_md5'])
        if not res:
            self.change_reduction_status("data_list", "safety", "ip_list", "reduction_status", 2, conf["name"], msg="解压ip数据失败")
            self.print_log("解压ip数据失败")
            return

        res = firewall_main().import_rules(public.to_dict_obj({"rule": "ip", "file": backup_conf['ip_list_path']}))
        if not res['status']:
            self.change_reduction_status("data_list", "safety", "ip_list", "reduction_status", 2, conf["name"], msg="还原ip数据失败" + res['msg'])
            self.print_log("还原ip数据失败" + res['msg'])
            return

        self.change_reduction_status("data_list", "safety", "ip_list", "reduction_status", 1, conf["name"], msg="还原ip数据成功")
        self.print_log("->>>还原ip数据:{}完成".format(conf["name"]))

    def reduction_words_data(self, conf):
        self.print_log("->>>开始还原words数据:{}".format(conf["name"]))
        self.print_log(conf)
        self.change_reduction_status("data_list", "safety", "words", "reduction_status", -1, conf["name"], msg="开始还原违规关键词{}数据".format(conf["name"]))
        backup_conf = self.backup_task_data['data_list']['safety']['words'][conf['name']]
        self.print_log(backup_conf)
        # 开始恢复敏感词
        self.print_log('开始解压words数据')
        words_path = "/www/server/panel/config/thesaurus.json"
        res = self.uncopy_file(backup_conf["wrods_data"], words_path, md5=backup_conf['wrod_data_md5'])
        if not res:
            self.change_reduction_status("data_list", "safety", "words", "reduction_status", 2, conf["name"], msg="还原违规关键词数据失败")
            self.print_log("解压words数据失败")
            return
        self.change_reduction_status("data_list", "safety", "words", "reduction_status", 1, conf["name"], msg="还原违规关键词数据")
        self.print_log("->>>还原违规关键词数据:{}完成".format(conf["name"]))

    def reduction_sqlite_data(self, conf):
        self.print_log("->>>开始还原sqlite数据:{}".format(conf["name"]))
        self.print_log(conf)
        self.print_log("->>>还原sqlite数据:{}完成".format(conf["name"]))

    def reduction_ssh_config_data(self, conf):
        self.print_log("->>>开始还原ssh数据:{}".format(conf["name"]))
        self.print_log(conf)
        self.change_reduction_status("data_list", "safety", "ssh_config", "reduction_status", -1, conf["name"], msg="开始还原ssh{}数据".format(conf["name"]))
        backup_conf = self.backup_task_data['data_list']['safety']['ssh_config'][conf['name']]
        self.print_log(backup_conf)
        ssh_config_path = '/etc/ssh/sshd_config'
        self.print_log('开始解压ssh数据')
        res = self.uncopy_file(backup_conf["ssh_data"], ssh_config_path, md5=backup_conf['ssh_data_md5'])
        if not res:
            self.change_reduction_status("data_list", "safety", "ssh_config", "reduction_status", 2, conf["name"], msg="还原ssh数据失败")
            self.print_log("还原ssh_config数据失败")
            return

        public.ExecShell('systemctl restart sshd')
        self.print_log("->>>还原ssfig数据:{}完成".format(conf["name"]))
        self.change_reduction_status("data_list", "safety", "ssh_config", "reduction_status", 1, conf["name"], msg="还原ssh数据成功")

    def create_queue(self, get):
        """
        创建任务队列（用于执行备份或还原任务）

        :param get: 包含任务 ID 和任务类型的对象
            - id (str): 任务的唯一标识符
            - type (str): 任务类型，1 表示备份，2 表示还原
        """
        # 获取任务 ID 和类型
        id = get.id
        type = get.type
        print(type)
        # 根据任务类型设置任务名称
        name = '备份任务' if type == 1 else '还原任务'
        print(name)
        # 导入任务管理模块
        import panelTask
        print("btpython /www/server/panel/class/panelModel/whole_machine_backupModel.py {} {} &> {}".format(id, type, self.logs_file ))
        # 使用任务管理模块创建任务，执行命令通过 `btpython` 调用对应脚本
        panelTask.bt_task().create_task(
            name,  # 任务名称
            0,     # 任务类型（0 表示普通任务）
            "btpython /www/server/panel/class/panelModel/whole_machine_backupModel.py {} {} &> {}".format(
                id,   # 任务 ID
                type, # 任务类型
                self.logs_file  # 日志文件路径
            )
        )

        # 记录日志，表示任务创建成功
        self.print_log("创建{}成功".format(name))


    def input(self, get):
        # 文件名清理：去掉干扰字符 (如 "(1)")
        original_file_name = get.f_name
        clean_file_name = original_file_name
        if '(' in original_file_name and ')' in original_file_name:
            clean_file_name = original_file_name.split('(')[0].strip() + ".tar.gz"

        # file_name = '/www/backup/whole_machine_backup/{}'.format(get.f_name)
        file_name = self.backup_path + clean_file_name 
        if not os.path.exists(self.backup_path):
            os.makedirs(self.backup_path)
        if clean_file_name in self.config:
            return public.returnMsg(False, '已存在相同的任务，请先删除后再导入！')
        from files import files
        fileObj = files()
        get.f_path = self.backup_path
        ff = fileObj.upload(get)
        if isinstance(ff, int):
            return ff
        if not ff['status']:
            return ff
        # 解压出全局配置文件
        print(public.ExecShell('cd {} && tar -zxvf {} ./{} '.format(self.backup_path,  clean_file_name, clean_file_name.rstrip('.tar.gz'))))
        print(clean_file_name)
        all_config_path = os.path.join(self.backup_path, clean_file_name.rstrip('.tar.gz'))
        print(all_config_path)
        time.sleep(0.2)
        if not os.path.exists(all_config_path):
            return public.returnMsg(False, '未找到配置文件！')
        try:
            res=json.loads(public.readFile(all_config_path))
            res[clean_file_name.rstrip('.tar.gz')]['status'] = 1
            self.config.update(res)
        except Exception as e:
            print(e)
            return public.returnMsg(False, '配置文件解析失败！')
        public.ExecShell('rm -rf {}'.format(all_config_path))

        # 取出备份记录
        if os.path.exists('{}backup.json'.format(self.backup_path)):
            public.ExecShell('rm -rf {}backup.json'.format(self.backup_path))
        public.ExecShell('cd {} && tar -zxvf {} ./backup.json'.format(self.backup_path, file_name))
        time.sleep(0.1)
        public.ExecShell('mv {}backup.json  {}_backup.json'.format(self.backup_path, self.backup_path+clean_file_name.rstrip('.tar.gz')))
        # 取出备份日志
        if not os.path.exists(self.backup_log_path):
            public.ExecShell('mkdir -p {}'.format(self.backup_log_path))
        public.ExecShell('cd {} && tar -zxvf {} ./{}_backup.log'.format(self.backup_log_path, file_name,clean_file_name.rstrip('.tar.gz')))
        public.writeFile(self.all_backup_config_path, json.dumps(self.config))
        return public.returnMsg(True, '导入成功！')

def cp_config():
    config_path = os.path.join(public.get_panel_path(), 'config/whole_machine_backup.json')
    if not os.path.exists(config_path):
        public.ExecShell("cp /www/backup/whole_machine_backup/whole_machine_backup.json {}".format(config_path))
cp_config()
del cp_config

if __name__ == '__main__':
    id = sys.argv[1]
    type = sys.argv[2]
    main = main()
    if type == '1':
        print('1')
        main.backup(id)
    elif type == '2':
        main.reduction(id)
    elif type == '3':
        main.check_mysql_files(sys.argv[3], sys.argv[4])
    else:
        print('参数错误！')
        sys.exit(1)
