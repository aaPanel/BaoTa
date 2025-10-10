# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2020 宝塔软件(http://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: baozi <baozi@bt.cn>
# | 消息通道微信公众号模块
# +-------------------------------------------------------------------

import os, sys
import time, base64

import re
import json
import requests
import traceback
import socket

import requests.packages.urllib3.util.connection as urllib3_cn
from requests.packages import urllib3
from typing import Optional, Union, List, Dict, Any

from .util import write_push_log, get_test_msg, read_file, public_http_post
from mod.base.push_mod import WxAccountMsg, SenderConfig
from mod.base import json_response

# 关闭警告
urllib3.disable_warnings()


class WeChatAccountMsg:
    USER_PATH = '/www/server/panel/data/userInfo.json'
    need_refresh_file = '/www/server/panel/data/mod_push_data/refresh_wechat_account.tip'
    refresh_time = '/www/server/panel/data/mod_push_data/refresh_wechat_account_time.pl'

    def __init__(self, *config_data):
        if len(config_data) == 0:
            self.config = None
        elif len(config_data) == 1:
            self.config = config_data[0]["data"]
        else:
            self.config = config_data[0]["data"]
            self.config["users"] = [i["data"]['id'] for i in config_data]
            self.config["users_nickname"] = [i["data"]['nickname'] for i in config_data]
        try:
            self.user_info = json.loads(read_file(self.USER_PATH))
        except:
            self.user_info = None

    @classmethod
    def get_user_info(cls) -> Optional[dict]:
        try:
            return json.loads(read_file(cls.USER_PATH))
        except:
            return None

    @classmethod
    def last_refresh(cls):
        tmp = read_file(cls.refresh_time)
        if not tmp:
            last_refresh_time = 0
        else:
            try:
                last_refresh_time = int(tmp)
            except:
                last_refresh_time = 0
        return last_refresh_time

    @staticmethod
    def get_local_ip() -> str:
        """获取内网IP"""
        import socket
        s = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            return ip
        except:
            pass
        finally:
            if s is not None:
                s.close()
        return '127.0.0.1'

    def send_msg(self, msg: WxAccountMsg) -> Optional[str]:
        if self.user_info is None:
            return '未获取到用户信息'

        msg.set_ip_address(self.user_info["address"], self.get_local_ip())
        template_id, msg_data = msg.to_send_data()
        url = "https://www.bt.cn/api/v2/user/wx_web/send_template_msg_v3"
        wx_account_ids = self.config["users"] if "users" in self.config else [self.config["id"], ]
        data = {
            "uid": self.user_info["uid"],
            "access_key": self.user_info["access_key"],
            "data": base64.b64encode(json.dumps(msg_data).encode('utf-8')).decode('utf-8'),
            "wx_account_ids": base64.b64encode(json.dumps(wx_account_ids).encode('utf-8')).decode('utf-8'),
        }
        if template_id != "":
            data["template_id"] = template_id

        status = False
        error = None
        user_name = self.config["users_nickname"] if "users_nickname" in self.config else [self.config["nickname"], ]
        try:

            resp = public_http_post(url, data)
            x = json.loads(resp)
            if x["success"]:
                status = True
            else:
                status = False
                error = x["res"]
        except:
            error = traceback.format_exc()

        write_push_log("微信公众号", status, msg.thing_type, user_name)

        return error if error else status

    @classmethod
    def refresh_config(cls, force: bool = False):
        if os.path.exists(cls.need_refresh_file):
            force = True
            os.remove(cls.need_refresh_file)
        if force or cls.last_refresh() + 60 * 10 < time.time():
            cls._get_by_web()

    @classmethod
    def _get_by_web(cls) -> Optional[List]:
        user_info = cls.get_user_info()
        # 检查 user_info 是否为 None
        if user_info is None:
            return None       
        url = "https://www.bt.cn/api/v2/user/wx_web/bound_wx_accounts"
        data = {
            "uid": user_info["uid"],
            "access_key": user_info["access_key"],
            "serverid": user_info["serverid"]
        }
        try:
            data = json.loads(public_http_post(url, data))
            if not data["success"]:
                return None
        except:
            return None

        cls._save_user_info(data["res"])
        return data["res"]

    @staticmethod
    def _save_user_info(user_config_list: List[Dict[str, Any]]):
        user_config_dict = {i["hex"]: i for i in user_config_list}

        remove_list = []
        sc = SenderConfig()
        for i in sc.config:
            if i['sender_type'] != "wx_account":
                continue
            if i['data'].get("hex", None) in user_config_dict:
                i['data'].update(user_config_dict[i['data']["hex"]])
                user_config_dict.pop(i['data']["hex"])
            else:
                remove_list.append(i)

        for r in remove_list:
            sc.config.remove(r)

        if user_config_dict:  # 还有多的
            for v in user_config_dict.values():
                v["title"] = v["nickname"]
                sc.config.append({
                    "id": sc.nwe_id(),
                    "used": True,
                    "sender_type": "wx_account",
                    "data": v
                })
        sc.save_config()

    @classmethod
    def unbind(cls, wx_account_uid: str):
        user_info = cls.get_user_info()
        if user_info is None:
            return json_response(status=True, msg='未获取到用户绑定的信息')
        url = "https://www.bt.cn/api/v2/user/wx_web/unbind_wx_accounts"
        data = {
            "uid": user_info["uid"],
            "access_key": user_info["access_key"],
            "serverid": user_info["serverid"],
            "ids":  str(wx_account_uid)
        }
        try:
            datas = json.loads(public_http_post(url, data))
            if datas["success"]:
                return json_response(status=True, data=datas, msg="解绑成功")
            else:
                return json_response(status=False, data=datas, msg=datas["res"])
        except:
            return json_response(status=True, msg="链接云端失败")

    @classmethod
    def get_auth_url(cls):
        user_info = cls.get_user_info()
        if user_info is None:
            return json_response(status=True, msg='未获取到用户绑定的信息')
        url = "https://www.bt.cn/api/v2/user/wx_web/get_auth_url"
        data = {
            "uid": user_info["uid"],
            "access_key": user_info["access_key"],
            "serverid": user_info["serverid"],
        }
        try:
            datas = json.loads(public_http_post(url, data))
            if datas["success"]:
                return json_response(status=True, data=datas)
            else:
                return json_response(status=False, data=datas, msg=datas["res"])
        except:
            return json_response(status=True, msg="链接云端失败")

    def test_send_msg(self) -> Optional[str]:
        test_msg = {
            "msg_list": ['>配置状态：<font color=#20a53a>成功</font>\n\n']
        }
        test_task = get_test_msg("消息通道配置提醒")
        res = self.send_msg(
            test_task.to_wx_account_msg(test_msg, test_task.the_push_public_data()),
        )
        if res is None:
            return None
        return res


# class wx_account_msg:
#     __module_name = None
#     __default_pl = "{}/data/default_msg_channel.pl".format(panelPath)
#     conf_path = '{}/data/wx_account_msg.json'.format(panelPath)
#     user_info = None
#
#     def __init__(self):
#         try:
#             self.user_info = json.loads(public.ReadFile("{}/data/userInfo.json".format(public.get_panel_path())))
#         except:
#             self.user_info = None
#         self.__module_name = self.__class__.__name__.replace('_msg', '')
#
#     def get_version_info(self, get):
#         """
#         获取版本信息
#         """
#         data = {}
#         data['ps'] = '宝塔微信公众号，用于接收面板消息推送'
#         data['version'] = '1.0'
#         data['date'] = '2022-08-15'
#         data['author'] = '宝塔'
#         data['title'] = '微信公众号'
#         data['help'] = 'http://www.bt.cn'
#         return data
#
#     def get_local_ip(self):
#         '''获取内网IP'''
#         import socket
#         try:
#             s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#             s.connect(('8.8.8.8', 80))
#             ip = s.getsockname()[0]
#             return ip
#         finally:
#             s.close()
#         return '127.0.0.1'
#
#     def get_config(self, get):
#         """
#         微信公众号配置
#         """
#         if os.path.exists(self.conf_path):
#             # 60S内不重复加载
#             start_time = int(time.time())
#             if os.path.exists("data/wx_account_msg.lock"):
#                 lock_time = 0
#                 try:
#                     lock_time = int(public.ReadFile("data/wx_account_msg.lock"))
#                 except:
#                     pass
#                 # 大于60S重新加载
#                 if start_time - lock_time > 60:
#                     public.run_thread(self.get_web_info2)
#                     public.WriteFile("data/wx_account_msg.lock", str(start_time))
#             else:
#                 public.WriteFile("data/wx_account_msg.lock", str(start_time))
#                 public.run_thread(self.get_web_info2)
#             data = json.loads(public.ReadFile(self.conf_path))
#
#             if not 'list' in data: data['list'] = {}
#
#             title = '默认'
#             if 'res' in data and 'nickname' in data['res']: title = data['res']['nickname']
#
#             data['list']['default'] = {'title': title, 'data': ''}
#
#             data['default'] = self.__get_default_channel()
#             return data
#         else:
#             public.run_thread(self.get_web_info2)
#             return {"success": False, "res": "未获取到配置信息"}
#
#     def set_config(self, get):
#         """
#         @设置默认值
#         """
#         if 'default' in get and get['default']:
#             public.writeFile(self.__default_pl, self.__module_name)
#
#         return public.returnMsg(True, '设置成功')
#
#     def get_web_info(self, get):
#         if self.user_info is None: return public.returnMsg(False, '未获取到用户绑定的信息')
#         url = "https://www.bt.cn/api/v2/user/wx_web/info"
#         data = {
#             "uid": self.user_info["uid"],
#             "access_key": self.user_info["access_key"],
#             "serverid": self.user_info["serverid"]
#         }
#         try:
#
#             datas = json.loads(public.httpPost(url, data))
#
#             if datas["success"]:
#                 public.WriteFile(self.conf_path, json.dumps(datas))
#                 return public.returnMsg(True, datas)
#             else:
#                 public.WriteFile(self.conf_path, json.dumps(datas))
#                 return public.returnMsg(False, datas)
#         except:
#             public.WriteFile(self.conf_path, json.dumps({"success": False, "res": "链接云端失败,请检查网络"}))
#             return public.returnMsg(False, "链接云端失败,请检查网络")
#
#     def unbind(self):
#         if self.user_info is None:
#             return public.returnMsg(False, '未获取到用户绑定的信息')
#         url = "https://www.bt.cn/api/v2/user/wx_web/unbind"
#         data = {
#             "uid": self.user_info["uid"],
#             "access_key": self.user_info["access_key"],
#             "serverid": self.user_info["serverid"]
#         }
#         try:
#
#             datas = json.loads(public.httpPost(url, data))
#
#             if os.path.exists(self.conf_path):
#                 os.remove(self.conf_path)
#
#             if datas["success"]:
#                 return public.returnMsg(True, datas)
#             else:
#                 return public.returnMsg(False, datas)
#         except:
#             public.WriteFile(self.conf_path, json.dumps({"success": False, "res": "链接云端失败,请检查网络"}))
#             return public.returnMsg(False, "链接云端失败,请检查网络")
#
#     def get_web_info2(self):
#         if self.user_info is None:
#             return public.returnMsg(False, '未获取到用户绑定的信息')
#         url = "https://www.bt.cn/api/v2/user/wx_web/info"
#         data = {
#             "uid": self.user_info["uid"],
#             "access_key": self.user_info["access_key"],
#             "serverid": self.user_info["serverid"]
#         }
#         try:
#             datas = json.loads(public.httpPost(url, data))
#             if datas["success"]:
#                 public.WriteFile(self.conf_path, json.dumps(datas))
#                 return public.returnMsg(True, datas)
#             else:
#                 public.WriteFile(self.conf_path, json.dumps(datas))
#                 return public.returnMsg(False, datas)
#         except:
#             public.WriteFile(self.conf_path, json.dumps({"success": False, "res": "链接云端失败"}))
#             return public.returnMsg(False, "链接云端失败")
#
#     def get_send_msg(self, msg):
#         """
#         @name 处理md格式
#         """
#         try:
#             import re
#             title = '宝塔告警通知'
#             if msg.find("####") >= 0:
#                 try:
#                     title = re.search(r"####(.+)", msg).groups()[0]
#                 except:
#                     pass
#
#                 msg = msg.replace("####", ">").replace("\n\n", "\n").strip()
#                 s_list = msg.split('\n')
#
#                 if len(s_list) > 3:
#                     s_title = s_list[0].replace(" ", "")
#                     s_list = s_list[3:]
#                     s_list.insert(0, s_title)
#                     msg = '\n'.join(s_list)
#
#             s_list = []
#             for msg_info in msg.split('\n'):
#                 reg = '<font.+>(.+)</font>'
#                 tmp = re.search(reg, msg_info)
#                 if tmp:
#                     tmp = tmp.groups()[0]
#                     msg_info = re.sub(reg, tmp, msg_info)
#                 s_list.append(msg_info)
#             msg = '\n'.join(s_list)
#         except:
#             pass
#         return msg, title
#
#     def send_msg(self, msg):
#         """
#         微信发送信息
#         @msg 消息正文
#         """
#
#         if self.user_info is None:
#             return public.returnMsg(False, '未获取到用户信息')
#
#         if not isinstance(msg, str):
#             return self.send_msg_v2(msg)
#
#         msg, title = self.get_send_msg(msg)
#         url = "https://www.bt.cn/api/v2/user/wx_web/send_template_msg_v2"
#         datassss = {
#             "first": {
#                 "value": "堡塔主机告警",
#             },
#             "keyword1": {
#                 "value": "内网IP " + self.get_local_ip() + "\n外网IP " + self.user_info[
#                     "address"] + "  \n服务器别名 " + public.GetConfigValue("title"),
#             },
#             "keyword2": {
#                 "value": "堡塔主机告警",
#             },
#             "keyword3": {
#                 "value": msg,
#             },
#             "remark": {
#                 "value": "如有疑问，请联系宝塔客服",
#             },
#         }
#         data = {
#             "uid": self.user_info["uid"],
#             "access_key": self.user_info["access_key"],
#             "data": base64.b64encode(json.dumps(datassss).encode('utf-8')).decode('utf-8')
#         }
#
#         try:
#             res = {}
#             error, success = 0, 0
#
#             x = json.loads(public.httpPost(url, data))
#             conf = self.get_config(None)['list']
#
#             # 立即刷新剩余次数
#             public.run_thread(self.get_web_info2)
#
#             res[conf['default']['title']] = 0
#             if x['success']:
#                 res[conf['default']['title']] = 1
#                 success += 1
#             else:
#                 error += 1
#
#             try:
#                 public.write_push_log(self.__module_name, title, res)
#             except:
#                 pass
#
#             result = public.returnMsg(True, '发送完成,发送成功{},发送失败{}.'.format(success, error))
#             result['success'] = success
#             result['error'] = error
#             return result
#
#         except:
#             print(public.get_error_info())
#             return public.returnMsg(False, '微信消息发送失败。 --> {}'.format(public.get_error_info()))
#
#     def push_data(self, data):
#         if isinstance(data, dict):
#             return self.send_msg(data['msg'])
#         else:
#             return self.send_msg_v2(data)
#
#     def uninstall(self):
#         if os.path.exists(self.conf_path):
#             os.remove(self.conf_path)
#
#     def send_msg_v2(self, msg):
#         from push.base_push import WxAccountMsgBase, WxAccountMsg
#         if self.user_info is None:
#             return public.returnMsg(False, '未获取到用户信息')
#
#         if isinstance(msg, public.dict_obj):
#             msg = getattr(msg, "msg", "测试信息")
#             if len(msg) >= 20:
#                 return self.send_msg(msg)
#
#         if isinstance(msg, str):
#             the_msg = WxAccountMsg.new_msg()
#             the_msg.thing_type = msg
#             the_msg.msg = msg
#             msg = the_msg
#
#         if not isinstance(msg, WxAccountMsgBase):
#             return public.returnMsg(False, '消息类型错误')
#
#         msg.set_ip_address(self.user_info["address"], self.get_local_ip())
#
#         template_id, msg_data = msg.to_send_data()
#         url = "https://www.bt.cn/api/v2/user/wx_web/send_template_msg_v2"
#         data = {
#             "uid": self.user_info["uid"],
#             "access_key": self.user_info["access_key"],
#             "data": base64.b64encode(json.dumps(msg_data).encode('utf-8')).decode('utf-8'),
#         }
#         if template_id != "":
#             data["template_id"] = template_id
#
#         try:
#             error, success = 0, 0
#             resp = public.httpPost(url, data)
#             x = json.loads(resp)
#             conf = self.get_config(None)['list']
#
#             # 立即刷新剩余次数
#             public.run_thread(self.get_web_info2)
#
#             res = {
#                 conf['default']['title']: 0
#             }
#             if x['success']:
#                 res[conf['default']['title']] = 1
#                 success += 1
#             else:
#                 error += 1
#
#             try:
#                 public.write_push_log(self.__module_name, msg.thing_type, res)
#             except:
#                 pass
#             result = public.returnMsg(True, '发送完成,发送成功{},发送失败{}.'.format(success, error))
#             result['success'] = success
#             result['error'] = error
#             return result
#
#         except:
#             return public.returnMsg(False, '微信消息发送失败。 --> {}'.format(public.get_error_info()))
