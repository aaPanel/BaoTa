#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: baozi <baozi@bt.cn>
#-------------------------------------------------------------------
# 告警
#------------------------------
import os
import json
from importlib import import_module

from panelModel.base import panelBase
import public


class main(panelBase):

    def __init__(self):
        pass

    def get_list(self, args):
        """
        @name 获取推送列表
        """
        path = '{}/class/push/scripts/'.format(public.get_panel_path())
        if not os.path.exists(path):
            return []

        data = []
        for fname in os.listdir(path):
            if fname.find('.json') == -1: continue
            try:
                item = json.loads(public.readFile('{}/{}'.format(path,fname)))

                data.append(item)
            except json.JSONDecodeError:
                pass
        return data

    @staticmethod
    def get_msg_configs(get=None):
        import config

        data = config.config().get_msg_configs(None)

        web_hook = public.init_msg("web_hook")
        if web_hook is False:
            return data
        data["web_hook"] = {
            "name": "web_hook",
            "title": "WEB HOOK",
            "version": "1.0",
            "date": "2023-10-30",
            "help": "https://www.bt.cn/bbs/thread-121791-1-1.html",
            "ps": "宝塔自定义API信息通道，用于接收面板消息推送",
            "setup": True,
            "info": web_hook.get_version_info(),
            "data": web_hook.get_config()
        }

        return data

    @staticmethod
    def set_webhook_config(get):
        web_hook = import_module('.web_hook_msg', package="msg")
        web_hook_obj = getattr(web_hook, "web_hook_msg", None)()
        return web_hook_obj.set_config(get)

    @staticmethod
    def set_webhook_status(get):
        name = None
        if "name" in get:
            name = get.name.strip()
            if name == '':
                name = None

        status = getattr(get, "status", None)
        if status is None:
            return public.returnMsg(False, '没有状态参数')

        if status in ('true', True, 1, "1"):
            status = True
        else:
            status = False

        web_hook = import_module('.web_hook_msg', package="msg")
        web_hook_obj = getattr(web_hook, "web_hook_msg", None)()
        web_hook_obj.set_status(status, name)
        return public.returnMsg(True, '操作成功')

    @staticmethod
    def remove_hook(get):
        name = None
        if "name" in get:
            name = get.name.strip()
            if name == '':
                name = None

        web_hook = import_module('.web_hook_msg', package="msg")
        web_hook_obj = getattr(web_hook, "web_hook_msg", None)()
        web_hook_obj.del_hook_by_name(name)

        return public.returnMsg(True, '操作成功')
    
    @staticmethod
    def unbind_wx_account(get):
        wx_account = import_module('.wx_account_msg', package="msg")
        wx_account_obj = getattr(wx_account, "wx_account_msg", None)()
        return wx_account_obj.unbind()
    
    @staticmethod
    def system_push_next(get):
        system_push = import_module(".system_push", package="push")
        system_push_obj = getattr(system_push, "system_push", None)()

        data_list, _ = getattr(system_push_obj, "_get_can_next", None)()
        return data_list
