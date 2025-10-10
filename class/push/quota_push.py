# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Windows面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2020 宝塔软件(https://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: baozi <1191604998@qq.com>
# +-------------------------------------------------------------------

import sys
import os
import re
import json
import time
import datetime
import psutil
import threading

class_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# /www/server/panel/class
bt_panel_path = os.path.dirname(class_path)
sys.path.insert(0, class_path)
sys.path.insert(0, bt_panel_path)
import public
import panelPush
from push.base_push import base_push, WxAccountMsg
from panelMysql import panelMysql


class quota_push(base_push):
    __push_conf = os.path.join(public.get_panel_path(), "class/push/push.json")

    def __init__(self):
        self.__push = panelPush.panelPush()


    def get_version_info(self, get=None):
        data = {
            'ps': '宝塔系统告警',
            'version': '1.0',
            'date': '2023-07-16',
            'author': '宝塔',
            'help': 'http://www.bt.cn/bbs'
        }
        return data

    # 格式化返回执行周期， 目前无作用
    def get_push_cycle(self, data: dict):
        return data

    # 获取模块推送参数
    def get_module_config(self, get: public.dict_obj):
        data = []
        item = self.__push.format_push_data(
            push=["mail", 'dingding', 'weixin', "feishu", "wx_account"],
            project='system', type='')
        item['cycle'] = 30
        item['title'] = '磁盘容量限额'
        data.append(item)
        return data

    # 获取模块配置项
    def get_push_config(self, get: public.dict_obj):
        task_id = get.id
        push_list = self.__push._get_conf()

        if task_id not in push_list["quota_push"]:
            res_data = public.returnMsg(False, '未找到指定配置.')
            res_data['code'] = 100
            return res_data
        result = push_list["quota_push"][task_id]
        return result

    @staticmethod
    def clear_push_count(task_id):
        """清除推送次数"""
        task_data_cache.set("tip_" + task_id, [])
        task_data_cache.save_cache()

    # 写入推送配置文件
    def set_push_config(self, get: public.dict_obj):
        return self.__push._get_conf()

    # 删除推送配置
    def del_push_config(self, get: public.dict_obj):
        # 从配置中删除信息，并做一些您想做的事，如记日志
        task_id = get.id
        data = self.__push._get_conf()
        if str(task_id).strip() in data["quota_push"]:
            del data["quota_push"][task_id]
        public.writeFile(self.__push_conf, json.dumps(data))
        return public.returnMsg(True, '删除成功.')

    def get_total(self):
        return True

    def can_view_task(self, data) -> bool:
        return False

    # 检查并获取推送消息，返回空时，不做推送, 传入的data是配置项
    def get_push_data(self, data, total):
        # data 内容
        # index :  时间戳 time.time()
        # 消息 以类型为key， 以内容为value， 内容中包含title 和msg
        # push_keys： 列表，发送了信息的推送任务的id，用来验证推送任务次数（） 意义不大
        tip_list = task_data_cache.get("tip_{}".format(data["id"]))
        if tip_list is None:
            tip_list = []
        today = datetime.date.today()
        try:
            for i in range(len(tip_list)-1, -1, -1):
                tip_time = datetime.datetime.fromtimestamp(float(tip_list[i]))
                if tip_time.date() < today:
                    del tip_list[i]
        except ValueError:
            tip_list = []

        if 0 < data["push_count"] <= len(tip_list):
            return None

        result = {'index': datetime.datetime.now().timestamp(), 'push_keys': []}
        try:
            import PluginLoader
            quota_info = PluginLoader.module_run('quota', 'quota_check', int(data["id"]))
        except:
            quota_info = None

        type_msg_dict = {
            "database": "数据库",
            "site": "网站目录",
            "ftp": "FTP 目录",
        }

        if quota_info is not None and quota_info.get("status") is None:
            for m_module in data['module'].split(','):
                type_msg = type_msg_dict.get(data["type"])
                if m_module == 'wx_account':
                    result[m_module] = ToWechatAccountMsg.quota(type_msg, quota_info["db_name"], quota_info["used"])
                else:
                    quota_path = quota_info["path"]
                    if quota_info["quota_type"] == "database":
                        quota_path = quota_info["db_name"]
                    s_list = [
                        ">通知类型：{}容量限额告警".format(type_msg),
                        ">告警内容：{} {} 磁盘使用量 {}MB 已超过 {}MB".format(type_msg, quota_path, round(quota_info["used"] / 1024 / 1024, 2), quota_info["quota_push"]["size"])
                    ]
                    sdata = public.get_push_info("磁盘容量占用告警", s_list)
                    result[m_module] = sdata

            tip_list.append(result["index"])
            task_data_cache.set("tip_{}".format(data["id"]), tip_list)
        return result

    # 返回到前端信息的钩子, 默认为返回传入信息（即：当前设置的任务的信息）
    @staticmethod
    def get_view_msg(task_id, task_data):
        task_data["tid"] = view_msg.get_tid(task_data)
        task_data["view_msg"] = view_msg.get_msg_by_type(task_data)
        return task_data

    @staticmethod
    def _get_bak_task_template():
        return []


class TaskDataCache(object):
    """记录告警检测的平均数据"""
    _FILE = "{}/data/push/tips/quota_data.json".format(public.get_panel_path())

    def __init__(self):
        if not os.path.exists(self._FILE):
            self._data = {}
            if not os.path.exists(os.path.dirname(self._FILE)):
                os.makedirs(os.path.dirname(self._FILE), 0o600)
            self._file_fp = open(self._FILE, mode='w+', encoding='utf-8')
        else:
            try:
                self._file_fp = open(self._FILE, mode='r+', encoding='utf-8')
                self._data = json.load(self._file_fp)
                if not isinstance(self._data, dict):
                    self._data = {}
            except (json.JSONDecodeError, ValueError):
                self._data = {}
                self._file_fp = open(self._FILE, mode='w+', encoding='utf-8')

    def __del__(self):
        self.save_cache()
        self._file_fp.close()

    def save_cache(self):
        self._file_fp.seek(0, 0)
        self._file_fp.truncate()
        json.dump(self._data, self._file_fp)
        self._file_fp.flush()

    def get(self, key):
        return self._data.get(key, None)

    def set(self, key, value):
        self._data[key] = value


task_data_cache = TaskDataCache()


class ViewMsgFormat(object):
    _FORMAT = {
        "database": (
            lambda x: "<span>MySQL 数据库 {} 磁盘占用超过 {}MB 触发</span>".format(x.get("db_name"),x.get("size"))
        ),
        "site": (
            lambda x: "<span>网站目录 {} 磁盘占用超过 {}MB 触发</span>".format(x.get("path"), x.get("size"))
        ),
        "ftp": (
            lambda x: "<span>ftp目录 {} 磁盘占用超过 {}MB 触发</span>".format(x.get("path"), x.get("size"))
        ),
    }

    _TID = {
        "database": "quota_push@0",
        "site": "quota_push@1",
        "ftp": "quota_push@2",
    }

    def get_msg_by_type(self, data):
        return self._FORMAT[data["type"]](data)

    def get_tid(self, data):
        return self._TID[data["type"]]


view_msg = ViewMsgFormat()


class ToWechatAccountMsg:
    @staticmethod
    def quota(type_msg: str, db_name: str, size: int):
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "{} 容量限额告警".format(type_msg)
        msg.msg = "{} {} 磁盘占用超过 {}MB".format(type_msg, db_name, str(size))
        msg.next_msg = "请登录面板，查看主机情况"
        return msg


