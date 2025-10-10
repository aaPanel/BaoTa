# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2020 宝塔软件(https://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: baozi <baozi@bt.cn>
# | Author: baozi
# +-------------------------------------------------------------------
from typing import List, Dict, Tuple

import public, panelPush

try:
    from BTPanel import cache
except:
    from cachelib import SimpleCache
    cache = SimpleCache()


class metaclass(type):
    def __new__(cls, name, *args, **kwargs):
        push_cls = super().__new__(cls, name, *args, **kwargs)
        if name == "base_push":
            return push_cls
        else:
            push_cls.all_push_model.append(push_cls)
        return push_cls


class base_push(metaclass=metaclass):
    all_push_model = []

    # 版本信息 目前无作用
    def get_version_info(self, get=None):
        raise NotImplementedError

    # 格式化返回执行周期， 目前无作用
    def get_push_cycle(self, data: dict):
        return data

    # 获取模块推送参数
    def get_module_config(self, get: public.dict_obj):
        raise NotImplementedError

    # 获取模块配置项
    def get_push_config(self, get: public.dict_obj):
        # 其实就是配置信息，没有也会从全局配置文件push.json中读取
        raise NotImplementedError

    # 写入推送配置文件
    def set_push_config(self, get: public.dict_obj):
        raise NotImplementedError

    # 删除推送配置
    def del_push_config(self, get: public.dict_obj):
        # 从配置中删除信息，并做一些您想做的事，如记日志
        raise NotImplementedError

    # 无意义？？？
    def get_total(self):
        return True

    # 检查并获取推送消息，返回空时，不做推送, 传入的data是配置项
    def get_push_data(self, data, total):
        # data 内容
        # index :  时间戳 time.time()
        # 消息 以类型为key， 以内容为value， 内容中包含title 和msg
        # push_keys： 列表，发送了信息的推送任务的id，用来验证推送任务次数（） 意义不大
        raise NotImplementedError

    # 返回这个告警类型可以设置的任务模板，返回形式为列表套用字典
    def get_task_template(self) -> Tuple[str, List[Dict]]:
        # 返回这个告警类型可以设置的任务模板，返回形式为列表套用字典
        raise NotImplementedError

    # 返回到前端信息的钩子, 默认为返回传入信息（即：当前设置的任务的信息）
    def get_view_msg(self, task_id: str, task_data: dict) -> dict:
        return task_data


class WxAccountMsgBase:

    @classmethod
    def new_msg(cls):
        return cls()

    def set_ip_address(self, server_ip, local_ip):
        pass

    def to_send_data(self):
        return "", {}


class WxAccountMsg(WxAccountMsgBase):
    def __init__(self):
        self.ip_address: str = ""
        self.thing_type: str = ""
        self.msg: str = ""
        self.next_msg: str = ""

    def set_ip_address(self, server_ip, local_ip):
        self.ip_address = "{}({})".format(server_ip, local_ip)
        if len(self.ip_address) > 32:
            self.ip_address = self.ip_address[:29] + "..."

    def to_send_data(self):
        res = {
            "first": {},
            "keyword1": {
                "value": self.ip_address,
            },
            "keyword2": {
                "value": self.thing_type,
            },
            "keyword3": {
                "value": self.msg,
            }
        }

        if self.next_msg != "":
            res["keyword4"] = {"value": self.next_msg}

        return "", res


class WxAccountLoginMsg(WxAccountMsgBase):
    tid = "RJNG8dBZ5Tb9EK6j6gOlcAgGs2Fjn5Fb07vZIsYg1P4"

    def __init__(self):
        self.login_name: str = ""
        self.login_ip: str = ""
        self.login_type: str = ""
        self.address: str = ""
        self._server_name: str = ""
        self._server_ip = ""

    def set_ip_address(self, server_ip, local_ip: str):
        if local_ip != "127.0.0.1" and local_ip.startswith("192.168"):
            self._server_ip = local_ip
        else:
            self._server_ip = server_ip
        if self._server_name == "":
            self._server_name = "服务器IP{}".format(server_ip)

    def _get_server_name(self):
        data = public.GetConfigValue("title")  # 若获得别名，则使用别名
        if data == "宝塔Linux面板":
            self._server_name = "宝塔面板({})".format(".".join(self._server_ip.split(".")[2:]))
        elif data != "":
            self._server_name = data

    def to_send_data(self):
        self._get_server_name()
        if self.address.startswith(">归属地："):
            self.address = self.address[5:]
        if self.address == "":
            self.address = "未知的归属地"

        if not public.is_ipv4(self.login_ip):
            self.login_ip = "ipv6-can not show"
            
        res = {
            "thing10": {
                "value": self._server_name,
            },
            "character_string9": {
                "value": self.login_ip,
            },
            "thing7": {
                "value": self.login_type,
            },
            "thing11": {
                "value": self.address,
            },
            "thing2": {
                "value": self.login_name,
            }
        }
        return self.tid, res
