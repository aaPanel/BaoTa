# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2020 宝塔软件(http://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: baozi <baozi@bt.cn>
# | 消息通道HOOK模块
# +-------------------------------------------------------------------
import os
import sys
import json
import re
import copy
import requests
from typing import Optional, List, Dict, Any, Union
from urllib3.util import parse_url

panel_path = "/www/server/panel"
if os.getcwd() != panel_path:
    os.chdir(panel_path)
if panel_path + "/class/" not in sys.path:
    sys.path.insert(0, panel_path + "/class/")

import public


class HooKConfig(object):
    _CONFIG_FILE = '{}/data/hooks_msg.json'.format(panel_path)

    def __init__(self):
        self._config: Optional[List[Dict[str, Any]]] = None

    def __getitem__(self, item: str) -> Optional[Dict[str, Any]]:
        if self._config is None:
            self._read_config()
        for d in self._config:
            if d.get('name', '') == item:
                return d
        return None

    def __setitem__(self, key: str, value: Dict[str, Any]):
        if self._config is None:
            self._read_config()
        if not isinstance(key, str) or not isinstance(value, dict):
            raise ValueError('参数类型错误')

        for idx, d in enumerate(self._config):
            if d.get('name', '') == key:
                target_idx = idx
                break
        else:
            target_idx = -1

        value.update(name=key)
        if target_idx == -1:
            self._config.append(value)
        else:
            self._config[target_idx] = value

        self.save_to_file()

    def __delitem__(self, key):
        if self._config is None:
            self._read_config()

        target_idx = -1
        for i, d in enumerate(self._config):
            if d.get('name', '') == key:
                target_idx = i
                break
        if target_idx != -1:
            del self._config[target_idx]
            self.save_to_file()
        return None

    def _read_config(self):
        data = []
        if os.path.exists(self._CONFIG_FILE):
            js_data = public.readFile(self._CONFIG_FILE)
            if isinstance(js_data, str):
                try:
                    data = json.loads(js_data)
                except json.JSONDecodeError:
                    data = []
        self._config = data

    def to_view(self) -> list:
        if self._config is None:
            self._read_config()

        return copy.deepcopy(self._config)

    def save_to_file(self):
        if self._config is None:
            self._read_config()
        public.writeFile(self._CONFIG_FILE, json.dumps(self._config))

    @staticmethod
    def get_version_info():
        """
        获取版本信息
        """
        data = {
            'ps': '宝塔WEB HOOK消息通道，用于接收面板消息推送',
            'version': '1.0',
            'date': '2023-10-30',
            'author': '宝塔',
            'title': 'WEB HOOK',
            'help': 'https://www.bt.cn/bbs/thread-121791-1-1.html'
        }
        return data

    @classmethod
    def clear_config(cls):
        if os.path.exists(cls._CONFIG_FILE):
            os.remove(cls._CONFIG_FILE)

    def set_all(self, status: bool):
        if self._config is None:
            self._read_config()

        for v in self._config:
            v["status"] = status

        self.save_to_file()

    def all_hook_name(self):
        names = []

        for v in self._config:
            if v["status"] is True:
                names.append(v["name"])

        return names


_cfg = HooKConfig()

# default = {
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


class RealHook(object):
    DEFAULT_HEADERS = {
        "User-Agent": "BT-Panel",
    }

    def __init__(self, hook_name, name: str = None, config: dict = None):
        if name is not None and config is not None:
            self.name = hook_name
            self._config = copy.deepcopy(config)
            return

        if not hook_name:
            raise ValueError("hook_name 不能为空")
        if _cfg[hook_name] is None:
            raise ValueError("没有配置指定的HOOK")

        self.name = hook_name
        self._config = _cfg[hook_name]

    def send_msg(self, msg: str, title, push_type) -> Optional[str]:
        if self._config['status'] is False:
            return "该通道已关闭，不再发送"

        ssl_verify = self._config.get("ssl_verify", None)

        the_url = parse_url(self._config['url'])
        if ssl_verify is None:
            ssl_verify = the_url.scheme == "https"

        custom_parameter = self._config.get("custom_parameter", {})
        if not isinstance(custom_parameter, dict):
            custom_parameter = {}  # 如果 custom_parameter 不是字典，则设置为空字典

        real_data = self._build_real_data(msg, title, push_type, custom_parameter)

        data = None
        json_data = None
        headers = self.DEFAULT_HEADERS.copy()
        if self._config["body_type"] == "json":
            json_data = real_data
        elif self._config["body_type"] == "form_data":
            data = real_data

        for k, v in self._config.get("headers", {}).items():
            if not isinstance(v, str):
                v = str(v)
            headers[k] = v
        if data:
            for k, v in data.items():
                if isinstance(v, str):
                    continue
                else:
                    data[k]=json.dumps(v)
        timeout = 5
        for i in range(3):
            try:
                if json_data is not None:
                    res = requests.request(
                        method=self._config["method"],
                        url=str(the_url),
                        json=json_data,
                        headers=headers,
                        timeout=timeout,
                        verify=ssl_verify,
                    )
                else:
                    res = requests.request(
                        method=self._config["method"],
                        url=str(the_url),
                        data=data,
                        headers=headers,
                        timeout=timeout,
                        verify=ssl_verify,
                    )
                if res.status_code == 200:
                    return None
                else:
                    return res.text
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                timeout += 5
                continue
            except requests.exceptions.RequestException as e:
                return str(e)
            except:
                return "发送失败，疑似是系统环境因素导致"
        return None

    @staticmethod
    def _build_real_data(msg: str, title:str, push_type:str, custom_parameter: dict):
        default_data = {"title": title, "msg": msg, "type": push_type}
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


class web_hook_msg:
    _MODULE_NAME = "hook"

    def __init__(self, name: str = None):
        if name is None:
            self._real_hook = None
        elif _cfg[name] is None:
            self._real_hook = None
        else:
            self._real_hook = RealHook(name)

    @staticmethod
    def get_version_info(get=None):
        """
        获取版本信息
        """
        return _cfg.get_version_info()

    @staticmethod
    def get_config(get=None):
        """
        获取配置
        """
        return _cfg.to_view()

    @staticmethod
    def set_status(status: bool, name=None) -> None:
        if name is None:
            _cfg.set_all(status)
        else:
            if _cfg[name] is not None:
                _cfg[name]["status"] = status

    @staticmethod
    def del_hook_by_name(name: str) -> None:
        del _cfg[name]

    @staticmethod
    def set_config(get):
        """配置hook"""
        try:
            hook_data = get.hook_data
            if isinstance(hook_data, str):
                hook_data = json.loads(hook_data)
            else:
                return ValueError
            name = hook_data['name']
            url = hook_data["url"]
            query = hook_data.get("query", {})
            headers = hook_data.get("headers", {})
            body_type = hook_data.get("body_type", "json")
            custom_parameter = hook_data.get("custom_parameter", {})
            method = hook_data.get("method", "POST")
            ssl_verify = hook_data.get("ssl_verify", None)  # null Ture

            status = bool(hook_data.get("status", True))
        except (ValueError, KeyError, json.JSONDecodeError, AttributeError):
            return public.returnMsg(False, "参数错误")

        test_or_save = int(getattr(get, "test_or_save", "0"))

        try:
            the_url = parse_url(url)  
            if the_url.scheme is None or the_url.host is None:
                # 如果解析结果表明这不是一个有效的URL，则返回错误信息
                return public.returnMsg(False, "URL字段不是一个有效的URL")
        except:
            return public.returnMsg(False, "URL字段不是一个有效的URL")

        for i in (query, headers, custom_parameter):
            if not isinstance(i, dict):
                return public.returnMsg(False, "参数错误")

        if body_type not in ('json', 'form_data', 'null'):
            return public.returnMsg(False, "body_type必须为json,form_data或者null")

        if method not in ('GET', 'POST', 'PUT', 'PATCH'):
            return public.returnMsg(False, "发送方式选择错误")

        if ssl_verify not in (True, False, None):
            return public.returnMsg(False, "是否验证ssl选项错误")

        name = name.strip()
        if name == "":
            return public.returnMsg(False, "名称不能为空")

        if name in ("dingding", "feishu", "mail", "sms", "weixin", "wx_account", "web_hook"):
            return public.returnMsg(False, "不能使用包含歧义的名称")

        the_conf = {
            "url": url,
            "query": query,
            "headers": headers,
            "body_type": body_type,
            "custom_parameter": custom_parameter,
            "method": method,
            "ssl_verify": ssl_verify,
            "status": True
        }

        if test_or_save == 1:
            hook = RealHook(hook_name="", name=name, config=the_conf)
            res = hook.send_msg(
                msg="宝塔面板自定义HOOK通道-测试信息",
                title="测试信息",
                push_type="测试信息"
            )
            if res is None:
                return public.returnMsg(True, "测试信息发送成功")
            else:
                return public.returnMsg(False, "测试信息发送失败")
        else:
            the_conf['status'] = status
            _cfg[name] = the_conf

        return public.returnMsg(True, "配置保存成功")

    @staticmethod
    def get_send_msg(msg):
        """
        @name 处理md格式
        """
        title = None
        if msg.find("####") >= 0:
            try:
                title = re.search(r"####(.+)\n", msg).groups()[0]
            except KeyError:
                pass
            msg = msg.replace("\n\n", "<br>").strip()
        pass
        return msg, title

    def send_msg(self, msg, title: str = '宝塔面板消息推送', push_type: str = 'unknown'):
        """
        触发web_hook, 发送信息
        """
        if self._real_hook is None:
            public.returnMsg(False, "未指定对应的hook用于发送")

        error, success, total = 0, 0, 1
        msg, n_title = self.get_send_msg(msg)

        if n_title:
            title = n_title

        error_msg = self._real_hook.send_msg(msg, title, push_type)

        if error_msg is None:
            status_msg = '<span style="color:#20a53a;">成功</span>'
            success += 1
        else:
            status_msg = '<span style="color:red;">失败</span>'
            error += 1
        log = '标题：【{}】，通知方式：【Api-{}】，发送状态：{}'.format(title, self._real_hook.name, status_msg)
        public.WriteLog('告警通知', log)

        result = public.returnMsg(True, '发送完成，共发送【{}】条，成功【{}】，失败【{}】。'.format(total, success, error))
        result['error_msg'] = error_msg
        result['success'] = success
        result['error'] = error
        return result

    def push_data(self, data):
        if "hook_name" in data:
            self._real_hook = RealHook(data.get("hook_name"))
        if "push_type" in data:
            push_type = data.get("push_type")
            return self.send_msg(data['msg'], data['title'], push_type)
        return self.send_msg(data['msg'], data['title'])

    @staticmethod
    def uninstall():
        _cfg.clear_config()

    @staticmethod
    def get_all_hooks_name():
        return _cfg.all_hook_name()
