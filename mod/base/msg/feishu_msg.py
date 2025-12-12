#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2020 宝塔软件(http://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: lx
# | 消息通道飞书通知模块
# +-------------------------------------------------------------------

import re
import json
import requests
import traceback
import socket

import requests.packages.urllib3.util.connection as urllib3_cn
from requests.packages import urllib3
from typing import Optional, Union

from .util import write_push_log, get_test_msg, reset_allowed_gai_family

# 关闭警告
urllib3.disable_warnings()


class FeiShuMsg:

    def __init__(self, feishu_data):
        self.id = feishu_data["id"]
        self.config = feishu_data["data"]

    @classmethod
    def check_args(cls, args: dict) -> Union[dict, str]:
        if "url" not in args or "title" not in args:
            return "信息不完整"

        title = args["title"]
        if len(title) > 15:
            return '备注名称不能超过15个字符'

        if "user" in args and isinstance(args["user"], list):
            user = args["user"]
        else:
            user = []

        if "isAtAll" in args and isinstance(args["isAtAll"], bool):
            atall = args["isAtAll"]
        else:
            atall = True

        data = {
            "url": args["url"],
            "user": user,
            "title": title,
            "isAtAll": atall,
        }

        test_obj = cls({"data": data, "id": None})
        test_msg = {
            "msg_list": ['>配置状态：成功\n\n']
        }

        test_task = get_test_msg("消息通道配置提醒")

        res = test_obj.send_msg(
            test_task.to_feishu_msg(test_msg, test_task.the_push_public_data()),
            "消息通道配置提醒"
        )
        if res is True:
            return data

        return res

    def send_msg(self, msg: str, title: str) -> Optional[str]:
        """
        飞书发送信息
        @msg 消息正文
        """
        if not self.config:
            return '未正确配置飞书信息。'

        reg = '<font.+>(.+)</font>'
        tmp = re.search(reg, msg)
        if tmp:
            tmp = tmp.groups()[0]
            msg = re.sub(reg, tmp, msg)

        if "isAtAll" not in self.config and not self.config["user"]:
            self.config["isAtAll"] = True

        if self.config["isAtAll"]:
            msg += "<at user_id=\"all\">所有人</at>"

        user_list = []
        for user in self.config["user"]:
            user: str
            if user.count("|") == 1:
                user_id, user_name = user.split("|")
                user_list.append("<at user_id=\"{}\">{}</at>".format(user_id, user_name))
        msg += "".join(user_list)

        headers = {'Content-Type': 'application/json'}
        data = {
            "msg_type": "text",
            "content": {
                "text": msg
            }
        }
        status = False
        error = None
        try:
            def allowed_gai_family():
                family = socket.AF_INET
                return family

            urllib3_cn.allowed_gai_family = allowed_gai_family
            rdata = requests.post(
                url=self.config['url'],
                data=json.dumps(data),
                verify=False,
                headers=headers,
                timeout=10
            ).json()
            reset_allowed_gai_family()

            if "StatusCode" in rdata and rdata["StatusCode"] == 0:
                status = True
            else:
                error = rdata["StatusMessage"]
        except:
            error = traceback.format_exc()

        write_push_log("飞书", status, title)

        return error if error else status

    def test_send_msg(self) -> Optional[str]:
        test_msg = {
            "msg_list": ['>配置状态：<font color=#20a53a>成功</font>\n\n']
        }
        test_task = get_test_msg("消息通道配置提醒")
        res = self.send_msg(
            test_task.to_feishu_msg(test_msg, test_task.the_push_public_data()),
            "消息通道配置提醒"
        )
        if res is None:
            return None
        return res
