# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2017 宝塔软件(http:#bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: baozi <baozi@bt.cn>
# -------------------------------------------------------------------
# 新告警的所有数据库操作
# ------------------------------
import json
import os
import types
from typing import Any, Dict, Optional, List
from uuid import uuid4


from .base_task import BaseTask
from .tool import load_task_cls
from .util import Sqlite, write_log, read_file, write_file, debug_log


DB_INIT_ERROR = False

PANEL_PATH = "/www/server/panel"
PUSH_DATA_PATH = "{}/data/mod_push_data".format(PANEL_PATH)
UPDATE_VERSION_FILE = "{}/update_panel.pl".format(PUSH_DATA_PATH)
UPDATE_MOD_PUSH_FILE = "{}/update_mod.pl".format(PUSH_DATA_PATH)


class BaseConfig:
    config_file_path = ""

    def __init__(self):
        if not os.path.exists(PUSH_DATA_PATH):
            os.makedirs(PUSH_DATA_PATH)
        self._config: Optional[List[Dict[str, Any]]] = None

    @property
    def config(self) -> List[Dict[str, Any]]:
        if self._config is None:
            try:
                self._config = json.loads(read_file(self.config_file_path))
            except:
                self._config = []
        return self._config

    def save_config(self) -> None:
        write_file(self.config_file_path, json.dumps(self.config))

    @staticmethod
    def nwe_id() -> str:
        return uuid4().hex[::2]

    def get_by_id(self, target_id: str) -> Optional[Dict[str, Any]]:
        for i in self.config:
            if i.get("id", None) == target_id:
                return i


class TaskTemplateConfig(BaseConfig):
    TAGS_MAP = {
        "common": "常用",
        "site": "网站",
        "ssl": "SSL",
        "system": "系统",
        "soft": "软件",
        "plugin": "插件",
        "panel": "面板",
        "safe": "安全",
    }

    config_file_path = "{}/task_template.json".format(PUSH_DATA_PATH)

    _VIEW_MSG_CLASS = []
    _CAN_CALL_TEMPLATE = []
    _UPDATE_TIMESTAMP = 0
    _NOT_CHECKED = (  # 仅需要面板的告警不检查 后续添加需要更新
        "1", "2", "3", "4", "5", "6", "7", "8", "9",
        "10", "20", "21", "22", "23", "71",
        "101", "102", "110","121", "122", "123",
    )

    def __init__(self):
        super().__init__()

    @classmethod
    def _update_view_msg_class(cls, self):
        cls_list = set()
        can_call_template = []
        for i in self.config:
            if i["used"] is False:
                continue
            load_data = i.get("load_cls", {})
            task_cls = load_task_cls(load_data)
            if task_cls:
                cls_list.add(task_cls.VIEW_MSG)
                task: BaseTask = task_cls()
                if i["id"] in self._NOT_CHECKED:
                    continue
                if task.filter_template(i["template"]):
                    can_call_template.append(i["id"])

        cls._VIEW_MSG_CLASS = list(cls_list)
        cls._CAN_CALL_TEMPLATE = can_call_template + list(self._NOT_CHECKED)
        cls._UPDATE_TIMESTAMP = int(os.path.getmtime(cls.config_file_path))

    @classmethod
    def can_call_template_ids(cls) -> List[str]:
        cls._update_view_msg_class(cls())
        return cls._CAN_CALL_TEMPLATE


    @classmethod
    def task_view_msg_format(cls, task: dict) -> str:
        if cls._UPDATE_TIMESTAMP != int(os.path.getmtime(cls.config_file_path)):
            cls._update_view_msg_class(cls())
        for i in cls._VIEW_MSG_CLASS:
            res = i().get_msg(task)
            if res:
                return res
        return "<span>--</span>"


class TaskConfig(BaseConfig):
    config_file_path = "{}/task.json".format(PUSH_DATA_PATH)

    def get_by_keyword(self, source: str, keyword: str) -> Optional[Dict[str, Any]]:
        for i in self.config:
            if i.get("source", None) == source and i.get("keyword", None) == keyword:
                return i

    def get_by_source(self, source: str) -> List[Dict[str, Any]]:
        res = []
        for i in self.config:
            if i.get("source", None) == source:
                res.append(i)
        return res


class TaskRecordConfig(BaseConfig):
    config_file_path_fmt = "%s/task_record_{}.json" % PUSH_DATA_PATH

    def __init__(self, task_id: str):
        super().__init__()
        self.config_file_path = self.config_file_path_fmt.format(task_id)


class SenderConfig(BaseConfig):
    config_file_path = "{}/sender.json".format(PUSH_DATA_PATH)

    def __init__(self):
        super(SenderConfig, self).__init__()
        if not os.path.exists(self.config_file_path):
            write_file(self.config_file_path, json.dumps([{
                "id": self.nwe_id(),
                "used": True,
                "sender_type": "sms",
                "data": {},
                "original": True
            }]))

    def key_exists(self, sender_type: str, key: str, value: Any) -> bool:
        for i in self.config:
            if i.get("sender_type", None) == sender_type:
                if i.get("data", {}).get(key, None) == value:
                    return True
        return False


def _check_fields(template: dict) -> bool:
    if not isinstance(template, dict):
        return False

    fields = ("id", "ver", "used", "source", "title", "load_cls", "template", "default", "unique", "create_time")
    for field in fields:
        if field not in template:
            return False
    return True


def load_task_template_by_config(templates: List[Dict]) -> None:
    """
    通过 传入的配置信息 执行一次模板更新操作
    @param templates: 模板内容，为一个数据列表
    @return: 报错信息，如果返回None则表示执行成功
    """

    task_template_config = TaskTemplateConfig()
    add_list = []
    for template in templates:
        tmp = task_template_config.get_by_id(template['id'])
        if tmp is not None:
            tmp.update(template)
        else:
            add_list.append(template)

    task_template_config.config.extend(add_list)
    task_template_config.save_config()

    # with get_table('task_template') as table:
    #     for template in templates:
    #         if not _check_fields(template):
    #             continue
    #         res = table.where("id = ?", (template['id'])).field('ver').select()
    #         if isinstance(res, str):
    #             return "数据库损坏：" + res
    #         if not res:  # 没有就插入
    #             table.insert(template)
    #         else:
    #             # 版本不一致就更新版本
    #             if res['ver'] != template['ver']:
    #                 template.pop("id")
    #                 table.where("id = ?", (template['id'])).update(template)
    #


def load_task_template_by_file(template_file: str) -> Optional[str]:
    """
    执行一次模板更新操作
    @param template_file: 模板文件路径
    @return: 报错信息，如果返回None则表示执行成功
    """
    if not os.path.isfile(template_file):
        return "模板文件不存在，更新失败"

    if DB_INIT_ERROR:
        return "数据库初始化时报错，无法更新"

    res = read_file(template_file)
    if not isinstance(res, str):
        return "数据读取失败"

    try:
        templates = json.loads(res)
    except (json.JSONDecoder, TypeError, ValueError):
        return "仅支持JSON格式数据"

    if not isinstance(templates, list):
        return "数据格式错误，应当为一个列表"

    return load_task_template_by_config(templates)
