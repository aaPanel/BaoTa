# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2020 宝塔软件(http://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: baozi
# | 消息通道 短信模块(新)
# +-------------------------------------------------------------------
import json
import os
import time
import traceback
from typing import Union, Optional
from mod.base.push_mod import SenderConfig
from .util import write_push_log, PANEL_PATH, write_file, read_file, public_http_post


class SMSMsg:
    API_URL = 'http://www.bt.cn/api/wmsg'
    USER_PATH = '{}/data/userInfo.json'.format(PANEL_PATH)

    # 构造方法
    def __init__(self, msm_data: dict):
        self.id = msm_data["id"]
        self.data = msm_data["data"]
        self.user_info = None
        try:
            self.user_info = json.loads(read_file(self.USER_PATH))
        except:
            self.user_info = None

        self._PDATA = {
            "access_key": "" if self.user_info is None else self.user_info["access_key"],
            "data": {}
        }

    def refresh_config(self, force=False):
        if "last_refresh_time" not in self.data:
            self.data["last_refresh_time"] = 0
        if self.data.get("last_refresh_time") + 60 * 60 * 24 < time.time() or force:  # 一天最多更新一次
            result = self._request('get_user_sms')
            if not isinstance(result, dict) or ("status" in result and not result["status"]):
                return {
                    "count": 0,
                    "total": 0
                }
            sc = SenderConfig()
            tmp = sc.get_by_id(self.id)
            if tmp is not None:
                result["last_refresh_time"] = time.time()
                tmp["data"] = result
                sc.save_config()
        else:
            result = self.data
        return result

    def send_msg(self, sm_type: str, sm_args: dict):
        """
        @发送短信
        @sm_type 预警类型, ssl_end|宝塔SSL到期提醒
        @sm_args 预警参数
        """
        if not self.user_info:
            return "未成功绑定官网账号，无法发送信息，请尝试重新绑定"
        tmp = sm_type.split('|')
        if "|" in sm_type and len(tmp) >= 2:
            s_type = tmp[0]
            title = tmp[1]
        else:
            s_type = sm_type
            title = '宝塔告警提醒'

        sm_args = self.canonical_data(sm_args)
        self._PDATA['data']['sm_type'] = s_type
        self._PDATA['data']['sm_args'] = sm_args
        result = self._request('send_msg')
        u_key = '{}****{}'.format(self.user_info['username'][:3], self.user_info['username'][-3:])
        if isinstance(result, str):
            write_push_log("短信", False, title, [u_key])
            return result

        if result['status']:
            write_push_log("短信", True, title, [u_key])
            return None
        else:
            write_push_log("短信", False, title, [u_key])
            return result.get("msg", "发送错误")

    @staticmethod
    def canonical_data(args):
        """规范数据内容"""
        if not isinstance(args, dict):
            return args
        new_args = {}
        for param, value in args.items():
            if type(value) != str:
                new_str = str(value)
            else:
                new_str = value.replace(".", "_").replace("+", "＋")
            new_args[param] = new_str
        return new_args

    def push_data(self, data):
        return self.send_msg(data['sm_type'], data['sm_args'])

    # 发送请求
    def _request(self, d_name: str) -> Union[dict, str]:
        pdata = {
            'access_key': self._PDATA['access_key'],
            'data': json.dumps(self._PDATA['data'])
        }
        try:
            result = public_http_post(self.API_URL + '/' + d_name, pdata)
            result = json.loads(result)
            return result
        except Exception:
            return traceback.format_exc()
