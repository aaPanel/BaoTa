# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2020 宝塔软件(http://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: baozi <baozi@bt.cn>
# | 消息通道HOOK模块
# +-------------------------------------------------------------------

import copy
import requests
from typing import Optional, Union
from urllib3.util import parse_url

from .util import write_push_log, get_test_msg
import json

# config = {
#     "name": "default",
#     "url": "https://www.bt.cn",
#     "query": {
#         "aaa": "111"
#     },
#     "header": {
#         "AAA": "BBBB",
#     },
#     "body_type": ["json", "form_data", "null"],
#     "custom_parameter": {
#         "rrr": "qqqq"
#     },
#     "method": ["GET", "POST", "PUT", "PATCH"],
#     "ssl_verify": [True, False]
# }
# #
# # 1.自动解析Query参数，拼接并展示给用户  # 可不做
# # 2.自定义Header头 # 必做
# # 3.Body中的内容是: type:str="首页磁盘告警", time:int=168955427, data:str="xxxxxx"  # ？
# # 4.自定义参数: key=value 添加在Body中  # 可不做
# # 5.请求类型自定义 # 必做
# # 以上内容需要让用户可测试--!


class WebHookMsg(object):
    DEFAULT_HEADERS = {
        "User-Agent": "BT-Panel",
    }

    def __init__(self, hook_data: dict):
        self.id = hook_data["id"]
        self.config = copy.deepcopy(hook_data["data"])

    def send_msg(self, msg: str, title:str, push_type:str) -> Optional[str]:
        the_url = parse_url(self.config['url'])

        ssl_verify = self.config.get("ssl_verify", None)
        if ssl_verify is None:
            ssl_verify = the_url.scheme == "https"
        else:
            ssl_verify = bool(int(ssl_verify))  # 转换为布尔值

        custom_parameter = self.config.get("custom_parameter", {})
        if not isinstance(custom_parameter, dict):
            custom_parameter = {}  # 如果 custom_parameter 不是字典，则设置为空字典

        real_data = self._build_real_data(msg, title, push_type, custom_parameter)

        headers = self.DEFAULT_HEADERS.copy()
        for k, v in self.config.get("headers", {}).items():
            if not isinstance(v, str):
                v = str(v)
            headers[k] = v

        data = None
        json_data = None
        if self.config["body_type"] == "json":
            json_data = real_data
        elif self.config["body_type"] == "form_data":
            data = real_data

        status = False
        error = None
        timeout = 10
        if data:
            for k, v in data.items():
                if isinstance(v, str):
                    continue
                else:
                    data[k]=json.dumps(v)   

        for i in range(3):
            try:
                if json_data is not None:
                    res = requests.request(
                        method=self.config["method"],
                        url=str(the_url),
                        json=json_data,
                        headers=headers,
                        timeout=timeout,
                        verify=ssl_verify,
                    )
                else:
                    res = requests.request(
                        method=self.config["method"],
                        url=str(the_url),
                        data=data,
                        headers=headers,
                        timeout=timeout,
                        verify=ssl_verify,
                    )

                if res.status_code == 200:
                    status = True
                    error = None
                    break
                else:
                    status = False
                    error = res.text or "请求错误，返回状态码为：{}".format(res.status_code)
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                timeout += 5
                error = "请求超时，请检查网络连接"
                continue
            except requests.exceptions.RequestException as e:
                error = str(e)
                break

        write_push_log("Web Hook", status, title)
        return error if error else status

    @staticmethod
    def _build_real_data(msg: str, title:str, push_type:str, custom_parameter: dict):
        default_data = {
            "title": title,
            "msg": msg,
            "type": push_type,
        }
        _build_by_replace = False

        def _replace(tmp_data: Union[str, list, dict,]):
            nonlocal _build_by_replace
            if isinstance(tmp_data, str):
                if "$1" in tmp_data:
                    _build_by_replace = True
                    tmp_data = tmp_data.replace("$1", json.dumps(default_data, ensure_ascii=False))
                if "$msg" in tmp_data:
                    _build_by_replace = True
                    tmp_data = tmp_data.replace("$msg", msg)
                if "$title" in tmp_data:
                    _build_by_replace = True
                    tmp_data = tmp_data.replace("$title", title)
                if "$type" in tmp_data:
                    _build_by_replace = True
                    tmp_data = tmp_data.replace("$type", push_type)
                return tmp_data
            elif isinstance(tmp_data, list):
                new_data = []
                for i in tmp_data:
                    new_data.append(_replace(i))
                return new_data
            elif isinstance(tmp_data, dict):
                new_data = {}
                for k, v in tmp_data.items():
                    new_data[k] = _replace(v)
                return new_data
            else:
                return tmp_data

        real_data = _replace(custom_parameter)
        if _build_by_replace:
            return real_data
        else:
            custom_parameter["title"] = title
            custom_parameter["msg"] = msg
            custom_parameter["type"] = push_type
            return custom_parameter

    @classmethod
    def check_args(cls, args) -> Union[str, dict]:
        """配置hook"""
        try:
            title = args['title']
            url = args["url"]
            query = args.get("query", {})
            headers = args.get("headers", {})
            body_type = args.get("body_type", "json")
            custom_parameter = args.get("custom_parameter", {})
            method = args.get("method", "POST")
            ssl_verify = args.get("ssl_verify", None)  # null Ture
        except (ValueError, KeyError):
            return "参数错误"

        the_url = parse_url(url)
        if the_url.scheme is None or the_url.host is None:
            return"url解析错误，这可能不是一个合法的url"

        for i in (query, headers, custom_parameter):
            if not isinstance(i, dict):
                return "参数格式错误"

        if body_type not in ('json', 'form_data', 'null'):
            return "body_type必须为json,form_data或者null"

        if method not in ('GET', 'POST', 'PUT', 'PATCH'):
            return "发送方式选择错误"

        if ssl_verify not in (True, False, None):
            return "是否验证ssl选项错误"

        title = title.strip()
        if title == "":
            return"名称不能为空"

        data = {
            "title": title,
            "url": url,
            "query": query,
            "headers": headers,
            "body_type": body_type,
            "custom_parameter": custom_parameter,
            "method": method,
            "ssl_verify": ssl_verify,
            "status": True
        }

        test_obj = cls({"data": data, "id": None})
        test_msg = {
            "msg_list": ['>配置状态：成功\n\n']
        }

        test_task = get_test_msg("消息通道配置提醒")

        res = test_obj.send_msg(
            test_task.to_web_hook_msg(test_msg, test_task.the_push_public_data()),
            "消息通道配置提醒",
            "消息通道配置提醒"
        )
        if res is True:
            return data

        return res

    def test_send_msg(self) -> Optional[str]:
        test_msg = {
            "msg_list": ['>配置状态：<font color=#20a53a>成功</font>\n\n']
        }
        test_task = get_test_msg("消息通道配置提醒")
        res = self.send_msg(
            test_task.to_web_hook_msg(test_msg, test_task.the_push_public_data()),
            "消息通道配置提醒",
            "消息通道配置提醒"
        )
        if res is None:
            return None
        return res

