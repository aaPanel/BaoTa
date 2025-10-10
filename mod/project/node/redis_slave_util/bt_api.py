# -*- coding: utf-8 -*-
"""
宝塔API通信模块 - Redis版本
负责与从库面板的API通信
"""
import base64
import json
import time
import hashlib
import os
from dataclasses import dataclass
from typing import Dict, Any, Union, Optional
import public

@dataclass
class APPKey:
    origin: str
    request_token: str
    app_key: str
    app_token: str

    @classmethod
    def parser(cls, app_key: str) -> Optional["APPKey"]:
        try:
            data = base64.b64decode(app_key).decode("utf-8")
            origin, request_token, app_key, app_token = data.split("|")
            origin_arr = origin.split(":")
            if len(origin_arr) > 3:
                origin = ":".join(origin_arr[:3])
            return cls(origin, request_token, app_key, app_token)
        except:
            return None


class BtApi:
    """宝塔API客户端 - Redis版本"""

    def __init__(self, panel_addr: str, panel_key: str):
        self.BT_PANEL = panel_addr if str(panel_addr).endswith("/") else panel_addr + "/"
        self.BT_KEY = panel_key

        self.APP = None
        app = APPKey.parser(panel_key)
        if app:
            self.APP = app
            self.BT_PANEL = app.origin.rstrip("/") + "/"

        import requests
        self._REQUESTS = None
        if not self._REQUESTS:
            self._REQUESTS = requests.session()

    def get_key_data(self) -> Dict[str, Any]:
        now = int(time.time())
        if self.APP:
            md5_panel_key = hashlib.md5(self.APP.request_token.encode()).hexdigest()
            request_token = hashlib.md5("{}{}".format(now, md5_panel_key).encode()).hexdigest()
            return {
                "client_bind_token": self.APP.app_token,
                "form_data": public.aes_encrypt("{}", self.APP.app_key), # ? 骗骗自己式加密
                "request_token": request_token,
                "request_time": str(now),
            }
        else:
            md5_panel_key = hashlib.md5(self.BT_KEY.encode()).hexdigest()
            request_token = hashlib.md5("{}{}".format(now, md5_panel_key).encode()).hexdigest()
            return {
                "request_token": request_token,
                "request_time": str(now),
            }

    def http_post_cookie(self, url: str, pdata: Dict[str, Any], timeout: int = 1800) -> str:
        """请求从库"""
        try:
            res = self._REQUESTS.post(url, params=self.get_key_data(), data=pdata, timeout=timeout, verify=False)
            if self.APP:
                return public.aes_decrypt(res.text, self.APP.app_key)
            else:
                return res.text
        except Exception as ex:
            ex = str(ex)
            if ex.find("Max retries exceeded with") != -1:
                return public.returnJson(False, "连接服务器失败!")
            if ex.find("Read timed out") != -1 or ex.find("Connection aborted") != -1:
                return public.returnJson(False, "连接超时!")
            return public.returnJson(False, "连接服务器失败!")

    def get_config(self) -> Dict[str, Any]:
        """请求从库获取配置接口"""
        try:
            info_url = self.BT_PANEL + "config?action=get_config"
            info_data = self.get_key_data()
            result = self.http_post_cookie(info_url, info_data, 5)
            return json.loads(result)
        except:
            return public.returnMsg(False, "请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {localhost} 是否加入从库API接口的IP白名单".format(localhost=public.GetLocalIp()))

    def get_slave_panel_info(self) -> Dict[str, Any]:
        """获取从库面板信息"""
        try:
            info_url = self.BT_PANEL + "system?action=GetConcifInfo"
            info_data = self.get_key_data()
            result = self.http_post_cookie(info_url, info_data, 5)
            return json.loads(result)
        except:
            return public.returnMsg(False, "请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {localhost} 是否加入从库API接口的IP白名单".format(localhost=public.GetLocalIp()))

    def slave_execute_command(self, shell: str, path: str = "/tmp") -> Dict[str, Any]:
        """从库执行 shell"""
        url = self.BT_PANEL + "/files?action=ExecShell"
        pdata = self.get_key_data()
        pdata["shell"] = shell
        pdata["path"] = path
        self.http_post_cookie(url, pdata)

        get_time = 3  # 超时间
        resp = self.get_execute_msg()
        start_time = int(time.time()) + get_time
        while resp["status"] is False and not resp["msg"] and int(time.time()) < start_time:
            resp = self.get_execute_msg()
            if resp["msg"]:
                break
            time.sleep(0.5)
        return resp

    def get_execute_msg(self) -> Dict[str, Any]:
        """获取 shell 执行结果"""
        try:
            url = self.BT_PANEL + "/files?action=GetExecShellMsg"
            pdata = self.get_key_data()
            result = self.http_post_cookie(url, pdata)
            return json.loads(result)
        except:
            return public.returnMsg(False, "请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {localhost} 是否加入从库API接口的IP白名单".format(localhost=public.GetLocalIp()))

    def get_slave_file(self, path: str = None) -> Dict[str, Any]:
        """获取从库文件内容"""
        try:
            url = self.BT_PANEL + "/files?action=GetFileBody"
            pdata = self.get_key_data()
            pdata["path"] = "/etc/redis.conf"
            if path:
                pdata["path"] = path
            result = self.http_post_cookie(url, pdata)
            return json.loads(result)
        except:
            return public.returnMsg(False, "请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {localhost} 是否加入从库API接口的IP白名单".format(localhost=public.GetLocalIp()))

    def save_slave_conf(self, content: str, path: str = None) -> Dict[str, Any]:
        """保存从库文件"""
        try:
            url = self.BT_PANEL + "/files?action=SaveFileBody"
            pdata = self.get_key_data()
            pdata["path"] = "/etc/redis.conf"
            if path:
                pdata["path"] = path
            pdata["encoding"] = "utf-8"
            pdata["data"] = content
            result = self.http_post_cookie(url, pdata)
            return json.loads(result)
        except:
            return public.returnMsg(False, "请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {localhost} 是否加入从库API接口的IP白名单".format(localhost=public.GetLocalIp()))

    def upload_file(self, export_path: str) -> Union[bool, str]:
        """上传文件"""
        pdata = self.get_key_data()
        pdata["f_name"] = os.path.basename(export_path)
        pdata["f_path"] = os.path.dirname(export_path)
        pdata["f_size"] = os.path.getsize(export_path)
        pdata["f_start"] = 0
        f = open(export_path, "rb")
        return self._send_file(pdata, f)

    def _send_file(self, pdata: Dict[str, Any], f) -> Union[bool, str]:
        """发送文件"""
        success_num = 0  # 连续发送成功次数
        upload_buff_size = 1024 * 1024 * 2  # 上传大小
        max_buff_size = int(1024 * 1024 * 8)  # 最大分片大小
        min_buff_size = int(1024 * 32)  # 最小分片大小
        err_num = 0  # 连接错误计数
        max_err_num = 5  # 最大连接错误重试次数
        up_buff_num = 5  # 调整分片的触发次数
        timeout = 30  # 每次发送分片的超时时间
        split_num = 0
        split_done = 0

        while True:
            max_buff = int(pdata["f_size"] - pdata["f_start"])
            if max_buff < upload_buff_size: 
                upload_buff_size = max_buff  # 判断是否到文件尾
            files = {"blob": f.read(upload_buff_size)}
            try:
                res = self._REQUESTS.post(self.BT_PANEL + "/files?action=upload", data=pdata, files=files, timeout=timeout, verify=False)
                success_num += 1
                err_num = 0
                # 连续5次分片发送成功的情况下尝试调整分片大小, 以提升上传效率
                if success_num > up_buff_num and upload_buff_size < max_buff_size:
                    upload_buff_size = int(upload_buff_size * 2)
                    success_num = up_buff_num - 3  # 如再顺利发送3次则继续提升分片大小
                    if upload_buff_size > max_buff_size: 
                        upload_buff_size = max_buff_size
            except Exception as err:
                err = str(err)
                if err.find("Read timed out") != -1 or err.find("Connection aborted") != -1:
                    if upload_buff_size > min_buff_size:
                        # 发生超时的时候尝试调整分片大小, 以确保网络情况不好的时候能继续上传
                        upload_buff_size = int(upload_buff_size / 2)
                        if upload_buff_size < min_buff_size: 
                            upload_buff_size = min_buff_size
                        success_num = 0
                    continue
                # 如果连接超时
                if err.find("Max retries exceeded with") != -1 and err_num <= max_err_num:
                    err_num += 1
                    time.sleep(0.5)
                    continue
                return "上传失败"
            if self.APP:
                result = json.loads(public.aes_decrypt(res.text, self.APP.app_key))
            else:
                result = res.json()
            if isinstance(result, int):
                if result == split_done:
                    split_num += 1
                else:
                    split_num = 0
                split_done = result
                if split_num > 10 or result > pdata["f_size"]:
                    return "上传失败！"
                pdata["f_start"] = result  # 设置断点
            else:
                if result["status"] is True:
                    return True
                return result["msg"]
        return True

    def control_redis_service(self, action_type: str = "restart") -> str:
        """控制从库Redis服务"""
        try:
            url = self.BT_PANEL + "/system?action=ServiceAdmin"
            p_data = self.get_key_data()
            p_data["name"] = "redis"
            p_data["type"] = action_type
            result = self.http_post_cookie(url, p_data)
            return result
        except:
            return public.returnMsg(False, "请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {localhost} 是否加入从库API接口的IP白名单".format(localhost=public.GetLocalIp()))

    def get_redis_info(self) -> Dict[str, Any]:
        """获取Redis信息"""
        try:
            url = self.BT_PANEL + "/ajax?action=GetSoftList"
            p_data = self.get_key_data()
            p_data["type"] = "redis"
            result = self.http_post_cookie(url, p_data)
            return json.loads(result)
        except:
            return public.returnMsg(False, "请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {localhost} 是否加入从库API接口的IP白名单".format(localhost=public.GetLocalIp()))

    def get_redis_status(self) -> Dict[str, Any]:
        """获取Redis运行状态"""
        try:
            url = self.BT_PANEL + "/redis?action=GetRedisStatus"
            p_data = self.get_key_data()
            result = self.http_post_cookie(url, p_data)
            return json.loads(result)
        except:
            return public.returnMsg(False, "请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {localhost} 是否加入从库API接口的IP白名单".format(localhost=public.GetLocalIp()))

    def execute_redis_command(self, command: str) -> Dict[str, Any]:
        """执行Redis命令"""
        try:
            url = self.BT_PANEL + "/redis?action=redis_exec"
            p_data = self.get_key_data()
            p_data["command"] = command
            result = self.http_post_cookie(url, p_data)
            return json.loads(result)
        except:
            return public.returnMsg(False, "请求从库错误！<br/>1.请检查密钥是否正确<br/>2.请检查 {localhost} 是否加入从库API接口的IP白名单".format(localhost=public.GetLocalIp())) 