import json
import os
import sys
import threading
import time
from datetime import datetime, timedelta
from importlib import import_module
from typing import Tuple, Union, Optional, List

import psutil

from .send_tool import WxAccountMsg
from .base_task import BaseTask, BaseTaskViewMsg
from .mods import PUSH_DATA_PATH, TaskTemplateConfig
from .util import read_file, write_file, get_config_value, GET_CLASS


class _ProcessInfo:

    def __init__(self):
        self.data = None
        self.last_time = 0

    def __call__(self) -> list:
        if self.data is not None and time.time() - self.last_time < 60:
            return self.data

        try:
            import PluginLoader
            get_obj = GET_CLASS()
            get_obj.sort = "status"
            p_info = PluginLoader.plugin_run("task_manager", "get_process_list", get_obj)
        except:
            return []

        if isinstance(p_info, dict) and "process_list" in p_info and isinstance(
                p_info["process_list"], list):
            self._process_info = p_info["process_list"]
            self.last_time = time.time()
            return self._process_info
        else:
            return []


get_process_info = _ProcessInfo()


def have_task_manager_plugin():
    """
    通过文件判断是否有进程管理器
    """
    return os.path.exists("/www/server/panel/plugin/task_manager/task_manager_push.py")


def load_task_manager_template():
    from .mods import load_task_template_by_config
    load_task_template_by_config([
        {
            "id": "60",
            "ver": "1",
            "used": True,
            "source": "task_manager_cpu",
            "title": "任务管理器CPU占用量告警",
            "load_cls": {
                "load_type": "path",
                "cls_path": "mod.base.push_mod.task_manager_push",
                "name": "TaskManagerCPUTask"
            },
            "template": {
                "field": [
                    {
                        "attr": "project",
                        "name": "进程名称",
                        "type": "select",
                        "items": {
                            "url": "plugin?action=a&name=task_manager&s=get_process_list_to_push"
                        }
                    },
                    {
                        "attr": "count",
                        "name": "占用率超过",
                        "type": "number",
                        "unit": "%",
                        "suffix": "后触发告警",
                        "default": 80,
                        "err_msg_prefix": "CUP占用率"
                    },
                    {
                        "attr": "interval",
                        "name": "间隔时间",
                        "type": "number",
                        "unit": "秒",
                        "suffix": "后再次监控检测条件",
                        "default": 600
                    }
                ],
                "sorted": [
                    [
                        "project"
                    ],
                    [
                        "count"
                    ],
                    [
                        "interval"
                    ]
                ],
            },
            "default": {
                "project": '',
                "count": 80,
                "interval": 600
            },
            "advanced_default": {
                "number_rule": {
                    "day_num": 3
                }
            },
            "send_type_list": [
                "wx_account",
                "dingding",
                "feishu",
                "mail",
                "weixin",
                "webhook"
            ],
            "unique": False,
            "tags": ["plugin"],
            "description": "定期检查指定进程的CPU占用量，如果超过设定值，则触发告警，避免过高的资源占用导致的服务异常。"
        },
        {
            "id": "61",
            "ver": "1",
            "used": True,
            "source": "task_manager_mem",
            "title": "任务管理器内存占用量告警",
            "load_cls": {
                "load_type": "path",
                "cls_path": "mod.base.push_mod.task_manager_push",
                "name": "TaskManagerMEMTask"
            },
            "template": {
                "field": [
                    {
                        "attr": "project",
                        "name": "进程名称",
                        "type": "select",
                        "items": {
                            "url": "plugin?action=a&name=task_manager&s=get_process_list_to_push"
                        }
                    },
                    {
                        "attr": "count",
                        "name": "占用量超过",
                        "type": "number",
                        "unit": "MB",
                        "suffix": "后触发告警",
                        "default": None,
                        "err_msg_prefix": "占用量"
                    },
                    {
                        "attr": "interval",
                        "name": "间隔时间",
                        "type": "number",
                        "unit": "秒",
                        "suffix": "后再次监控检测条件",
                        "default": 600
                    }
                ],
                "sorted": [
                    [
                        "project"
                    ],
                    [
                        "count"
                    ],
                    [
                        "interval"
                    ]
                ],
            },
            "default": {
                "project": '',
                "count": 80,
                "interval": 600
            },
            "advanced_default": {
                "number_rule": {
                    "day_num": 3
                }
            },
            "send_type_list": [
                "wx_account",
                "dingding",
                "feishu",
                "mail",
                "weixin",
                "webhook"
            ],
            "unique": False,
            "tags":["plugin"],
            "description": "定期检查指定进程的内存占用量，如果超过设定值，则触发告警，避免过高的资源占用导致的服务异常。"
        },
        {
            "id": "62",
            "ver": "1",
            "used": True,
            "source": "task_manager_process",
            "title": "任务管理器进程开销告警",
            "load_cls": {
                "load_type": "path",
                "cls_path": "mod.base.push_mod.task_manager_push",
                "name": "TaskManagerProcessTask"
            },
            "template": {
                "field": [
                    {
                        "attr": "project",
                        "name": "进程名称",
                        "type": "select",
                        "items": {
                            "url": "plugin?action=a&name=task_manager&s=get_process_list_to_push"
                        }
                    },
                    {
                        "attr": "count",
                        "name": "进程数超过",
                        "type": "number",
                        "unit": "个",
                        "suffix": "后触发告警",
                        "default": 20,
                        "err_msg_prefix": "进程数"
                    },
                    {
                        "attr": "interval",
                        "name": "间隔时间",
                        "type": "number",
                        "unit": "秒",
                        "suffix": "后再次监控检测条件",
                        "default": 600
                    }
                ],
                "sorted": [
                    [
                        "project"
                    ],
                    [
                        "count"
                    ],
                    [
                        "interval"
                    ]
                ],
            },
            "default": {
                "project": '',
                "count": 80,
                "interval": 600
            },
            "advanced_default": {
                "number_rule": {
                    "day_num": 3
                }
            },
            "send_type_list": [
                "wx_account",
                "dingding",
                "feishu",
                "mail",
                "weixin",
                "webhook"
            ],
            "unique": False,
            "tags": ["plugin"],
            "description": "定期检查指定进程的子进程数，如果超过设定值，则触发告警，避免过高的资源占用导致的服务异常。"
        }
    ])


class TaskManagerCPUTask(BaseTask):

    def __init__(self):
        super().__init__()
        self.source_name = "task_manager_cpu"
        self.template_name = "任务管理器CUP占用量告警"

    def get_title(self, task_data: dict) -> str:
        return "进程【{}】的CPU占用量告警".format(task_data["project"])

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        if "interval" not in task_data or not isinstance(task_data["interval"], int):
            task_data["interval"] = 600
        if task_data["interval"] < 60:
            task_data["interval"] = 60
        if "count" not in task_data or not isinstance(task_data["count"], int):
            return "设置的检查范围不正确"
        if not 1 <= task_data["count"] < 100:
            return "设置的检查范围不正确"
        if not task_data["project"]:
            return "请选择进程"
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return task_data["project"]

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        process_info = get_process_info()
        self.title = self.get_title(task_data)
        count = used = 0
        for p in process_info:
            if p["name"] == task_data['project']:
                used += p["cpu_percent"]
                count += 1 if "children" not in p else len(p["children"]) + 1

        if used <= task_data['count']:
            return None

        return {
            'msg_list':
                [
                    ">通知类型：任务管理器CPU占用量告警",
                    ">告警内容: 进程名称为【{}】的进程共有{}个，消耗的CPU资源占比为{}%，大于告警阈值{}%。".format(
                        task_data['project'], count, used, task_data['count']
                    )
                ],
            "project": task_data['project'],
            "count": int(task_data['count'])
        }

    def filter_template(self, template: dict) -> Optional[dict]:
        if not have_task_manager_plugin():
            return None
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return '', {}

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "任务管理器CPU占用量告警"
        if len(push_data["project"]) > 11:
            project = push_data["project"][:9] + ".."
        else:
            project = push_data["project"]

        msg.msg = "{}的CUP超过{}%".format(project, push_data["count"])
        return msg


class TaskManagerMEMTask(BaseTask):
    def __init__(self):
        super().__init__()
        self.source_name = "task_manager_mem"
        self.template_name = "任务管理器内存占用量告警"

    def get_title(self, task_data: dict) -> str:
        return "进程【{}】的内存占用量告警".format(task_data["project"])

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        if not task_data["project"]:
            return "请选择进程"
        if "interval" not in task_data or not isinstance(task_data["interval"], int):
            task_data["interval"] = 600
        task_data["interval"] = max(60, task_data["interval"])
        if "count" not in task_data or not isinstance(task_data["count"], int):
            return "设置的检查范围不正确"
        if task_data["count"] < 1:
            return "设置的检查范围不正确"
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return task_data["project"]

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        process_info = get_process_info()
        self.title = self.get_title(task_data)

        used = count = 0
        for p in process_info:
            if p["name"] == task_data['project']:
                used += p["memory_used"]
                count += 1 if "children" not in p else len(p["children"]) + 1

        if used <= task_data['count'] * 1024 * 1024:
            return None
        return {
            'msg_list': [
                ">通知类型：任务管理器内存占用量告警",
                ">告警内容: 进程名称为【{}】的进程共有{}个，消耗的内存资源为{}MB，大于告警阈值{}MB。".format(
                    task_data['project'], count, int(used / 1024 / 1024), task_data['count']
                )
            ],
            "project": task_data['project']
        }

    def filter_template(self, template: dict) -> Optional[dict]:
        if not have_task_manager_plugin():
            return None
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return '', {}

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        if len(push_data["project"]) > 11:
            project = push_data["project"][:9] + ".."
        else:
            project = push_data["project"]
        msg.thing_type = "任务管理器内存占用量告警"
        msg.msg = "{}的内存超过告警数值".format(project)
        return msg


class TaskManagerProcessTask(BaseTask):
    def __init__(self):
        super().__init__()
        self.source_name = "task_manager_process"
        self.title = "任务管理器进程开销告警"

    def get_title(self, task_data: dict) -> str:
        return "进程【{}】的子进程开销告警".format(task_data["project"])

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        if not task_data["project"]:
            return "请选择进程"
        if "interval" not in task_data or not isinstance(task_data["interval"], int):
            task_data["interval"] = 600
        task_data["interval"] = max(60, task_data["interval"])
        if "count" not in task_data or not isinstance(task_data["count"], int):
            return "设置的检查范围不正确"
        if task_data["count"] < 1:
            return "设置的检查范围不正确"
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return task_data["project"]

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        process_info = get_process_info()
        count = 0
        for p in process_info:
            if p["name"] == task_data['project']:
                count += 1 if "children" not in p else len(p["children"]) + 1

        if count <= task_data['count']:
            return None

        return {
            'msg_list':
                [
                    ">通知类型：任务管理器进程开销告警",
                    ">告警内容: 进程名称为【{}】的进程共有{}个，大于告警阈值{}个。".format(
                        task_data['project'], count, task_data['count']
                    )
                ],
            "project": task_data['project'],
            "count": task_data['count'],
        }

    def filter_template(self, template: dict) -> Optional[dict]:
        if not have_task_manager_plugin():
            return None
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return '', {}

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "任务管理器进程开销告警"
        if len(push_data["project"]) > 11:
            project = push_data["project"][:9] + ".."
        else:
            project = push_data["project"]

        if push_data["count"] > 100:  # 节省字数
            push_data["count"] = "限制"

        msg.msg = "{}的子进程数超过{}".format(project, push_data["count"])
        return msg


class ViewMsgFormat(BaseTaskViewMsg):
    _FORMAT = {
        "60": (
            lambda x: "<span>进程：{}的CUP占用超过{}%触发</span>".format(
                x.get("project"), x.get("count")
            )
        ),
        "61": (
            lambda x: "<span>进程：{}的内存使用率超过{}MB后触发</span>".format(
                x.get("project"), x.get("count")
            )
        ),
        "62": (
            lambda x: "<span>进程：{}的子进程数量超过{}后触发</span>".format(
                x.get("project"), x.get("count")
            )
        ),
    }

    def get_msg(self, task: dict) -> Optional[str]:
        if task["template_id"] in self._FORMAT:
            return self._FORMAT[task["template_id"]](task["task_data"])
        return None


TaskManagerCPUTask.VIEW_MSG = TaskManagerMEMTask.VIEW_MSG = TaskManagerProcessTask.VIEW_MSG = ViewMsgFormat