# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: baozi <baozi@bt.cn>
# -------------------------------------------------------------------
# 项目监听重启模块
# ------------------------------
# 功能: 监听指定项目的文件，当文件发生变化时，调用服务重启
# 1.配置
#     conf = {
#         "project_type": "java",
#         "project_id": 14,
#         "project_name": "project_name",
#         "watch_path": "/www/wwwroot/java_p/xxx.jar",
#     }
# 对文件的处理方式：
#     1. 比对size
#     2. 比对mtime
# 对文件夹的处理方式：Todo：视情况后续开发
#     1.暂不支持
# Todo: 目前只支持java springboot项目
# 服务运行逻辑
# BT-Task 做轮询
#     1.1 加载配置文件
#     1.2 获取状态并比对
#     1.3 根据比对结果处理重启服务
#     1.4.尝试重载配置文件

import threading
import json
import os.path
import time
import sys
from importlib import import_module
from typing import Optional, Dict, Any, Tuple


os.chdir("/www/server/panel")
if "class/" not in sys.path:
    sys.path.insert(0, "class/")

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

import public


class WatchConfig:
    _CONF_FILE = "{}/data/watch_project.json".format(public.get_panel_path())

    def __init__(self):
        self._config: Optional[dict] = None
        self._conf_time: Optional[int] = None

    @property
    def config(self) -> dict:
        if self._config is not None:
            return self._config
        data = {}
        if not os.path.isfile(self._CONF_FILE):
            self._config = data
            self.save_conf()
            return self._config
        try:
            data = json.loads(public.readFile(self._CONF_FILE))
            if isinstance(data, dict):
                self._config = data
                self._conf_time = int(os.path.getmtime(self._CONF_FILE))  # 正确读出配置时保存时间戳
            else:
                self._config = {}
        except (json.JSONDecodeError, TypeError):
            self._config = {}

        if self._conf_time is None:
            self.save_conf()
        return self._config

    def save_conf(self):
        if self._config is not None:
            public.writeFile(self._CONF_FILE, json.dumps(self._config))
            self._conf_time = int(os.path.getmtime(self._CONF_FILE))

    def reload(self) -> bool:
        if not os.path.exists(self._CONF_FILE):
            self._config = {}
            self.save_conf()
            return True

        now_mtime = int(os.path.getmtime(self._CONF_FILE))
        if now_mtime == self._conf_time:
            return False
        else:
            self._config = None
            return True


class Task:
    WAIT_TIME = 20

    def __init__(self):
        self.watch_conf = WatchConfig()
        self._mod_cache: Dict[str, Any] = {}
        self._status_cache = {}
        self._sub_thread_cache = {}

    def get_mod_obj(self, project_type: str) -> Any:
        if project_type in self._mod_cache:
            return self._mod_cache[project_type]

        try:
            if project_type == "java" and os.path.exists("/www/server/panel/mod/project/java/projectMod.py"):
                main_module = import_module("mod.project.java.projectMod")
            else:
                if not project_type.endswith("Model"):
                    project_type += "Model"
                main_module = import_module(".{}".format(project_type), package="projectModel")
        except ImportError:
            print(public.get_error_info())
            # public.print_log(public.get_error_info())
            return None

        main_class = getattr(main_module, "main", None)
        if not callable(main_class):
            return None

        self._mod_cache[project_type] = main_class()
        return self._mod_cache[project_type]

    def need_restart(self, project_type: str, project_id: int) -> bool:
        model_main_obj = self.get_mod_obj(project_type)
        if not model_main_obj:
            return False
        stop_by_user = getattr(model_main_obj, "is_stop_by_user")(project_id)
        if stop_by_user:
            return False
        return True

    def get_status_by_name(self, project_name: str) -> Tuple[int, float]:
        conf = self.watch_conf.config[project_name]
        file = conf['watch_path']
        if not os.path.exists(file):
            return 0, 0
        return os.path.getsize(file), int(os.path.getmtime(file))

    def check_status(self, project_name: str) -> bool:
        if project_name not in self._status_cache:
            self._status_cache[project_name] = self.get_status_by_name(project_name)
            return False

        now_status = self.get_status_by_name(project_name)
        if self._status_cache[project_name] == now_status:
            return False
        else:
            self._status_cache[project_name] = now_status
            return True

    def restart_with_threading(self, project_type, project_name):
        try:
            model_main_obj = self.get_mod_obj(project_type)
            get_obj = public.dict_obj()
            get_obj.project_name = project_name
            getattr(model_main_obj, "restart_project")(get_obj)
        except:
            # print(public.get_error_info())
            public.print_log(public.get_error_info())

    def _run(self):
        while True:
            # print(self.watch_conf.config)
            # print(self.watch_conf._conf_time)
            # print(self._status_cache)
            for p_name, p_conf in self.watch_conf.config.items():
                p_type = p_conf["project_type"]
                if self.need_restart(p_type, p_conf["project_id"]):
                    if self.check_status(p_name):
                        if p_name in self._sub_thread_cache:
                            self._sub_thread_cache[p_name].join()
                        restart_task = threading.Thread(target=self.restart_with_threading, args=(p_type, p_name))
                        restart_task.start()
                        self._sub_thread_cache[p_name] = restart_task

            # public.print_log("---------WAIT--------------")
            for i in range(int(self.WAIT_TIME / 5)):
                time.sleep(5)
                if self.watch_conf.reload():
                    print("配置文件发生变化，重载配置")
                    # public.print_log("配置文件发生变化，重载配置")
                    # public.print_log(self.watch_conf.config)
                    break

    def run(self):
        try:
            self._run()
        except KeyboardInterrupt:
            return
        except:
            public.print_log(public.get_error_info())
            # print(self.watch_conf.config)
            self.watch_conf = WatchConfig()
            self.run()


class main:

    def __init__(self):
        pass

    @staticmethod
    def project_is_watch(get):
        try:
            project_name = get.project_name.strip()
        except AttributeError:
            return public.returnMsg(False, "参数错误")

        conf = WatchConfig()
        if project_name in conf.config:
            return conf.config[project_name]
        else:
            return {}

    @staticmethod
    def add_project_watch(get):
        try:
            project_name = get.project_name.strip()
        except AttributeError:
            return public.returnMsg(False, "参数错误")

        site_info = public.M('sites').where("name = ?", (project_name, )).find()
        if isinstance(site_info, str) and site_info.startswith("error"):
            return public.returnMsg(False, "数据库查询错误:" + site_info)
        if not isinstance(site_info, dict):
            return public.returnMsg(False, "未查询到指定的网站")
        if site_info["project_type"] != "Java":
            return public.returnMsg(False, "目前只支持Java Springboot项目使用")

        project_config = json.loads(site_info["project_config"])
        if project_config['java_type'] != 'springboot':
            return public.returnMsg(False, "目前只支持Java Springboot项目使用")

        conf = WatchConfig()
        conf.config[project_name] = {
                "project_type": site_info["project_type"].lower(),
                "project_id": site_info["id"],
                "project_name": project_name,
                "watch_path": project_config["project_jar"]
            }
        conf.save_conf()
        return public.returnMsg(True, "添加成功")

    @staticmethod
    def del_project_watch(get):
        try:
            project_name = get.project_name.strip()
        except AttributeError:
            return public.returnMsg(False, "参数错误")

        conf = WatchConfig()
        if project_name in conf.config:
            del conf.config[project_name]
            conf.save_conf()

        return public.returnMsg(True, "删除成功")


def use_project_watch(project_name: str) -> bool:
    conf = WatchConfig()
    return project_name in conf.config


def add_project_watch(p_name: str, p_type: str, site_id: int, watch_path: str) -> None:
    conf = WatchConfig()
    conf.config[p_name] = {
        "project_type": p_type.lower(),
        "project_id": site_id,
        "project_name": p_name,
        "watch_path": watch_path
    }
    try:
        site_ids = public.M('sites').field("id").select()
        site_id_list = [i['id'] for i in site_ids]
        public.print_log(site_id_list)
        remove_list = []
        for k, v in conf.config.items():
            if v["project_id"] not in site_id_list:
                remove_list.append(k)
        for i in remove_list:
            del conf.config[i]
    except:
        pass
    conf.save_conf()


def del_project_watch(p_name: str) -> None:
    conf = WatchConfig()
    if p_name in conf.config:
        del conf.config[p_name]
        conf.save_conf()


if __name__ == '__main__':
    Task().run()
