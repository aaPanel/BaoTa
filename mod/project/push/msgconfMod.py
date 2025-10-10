# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2017 宝塔软件(http:#bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: baozi <baozi@bt.cn>
# -------------------------------------------------------------------
# 新告警通道管理模块
# ------------------------------
from mod.base.msg import SenderManager, WeChatAccountMsg, update_mod_push_msg
from mod.base.push_mod import SenderConfig
from mod.base import json_response

import public


# update_mod_push_msg()


class main(SenderManager):

    @staticmethod
    def wx_account_auth(get=None):
        return WeChatAccountMsg.get_auth_url()

    @staticmethod
    def unbind_wx_account(get):
        try:
            sender_id = get.sender_id.strip()
        except AttributeError:
            return json_response(status=False, msg="参数错误")

        conf = SenderConfig().get_by_id(sender_id)
        if not conf:
            return json_response(status=False, msg="未查询到对应绑定信息")

        res = WeChatAccountMsg.unbind(conf["data"]["id"])
        public.WriteFile(WeChatAccountMsg.need_refresh_file, "")
        return res

    def set_default_sender(self, get):
        try:

            try:
                sender_id = get.sender_id.strip()
                sender_type = get.sender_type.strip()
            except AttributeError:
                return json_response(status=False, msg="参数错误")

            sc = SenderConfig()
            change = False
            for conf in sc.config:
                if conf["sender_type"] == sender_type:
                    is_original = conf.get("original", False)
                    if conf["id"] == sender_id:
                        change = True
                        conf["original"] = True
                    else:
                        conf["original"] = False

            sc.save_config()
            if change:
                self.set_default_for_compatible(sc.get_by_id(sender_id))
            return json_response(status=True, msg="设置成功")
        except Exception as e:
            return json_response(status=False, msg=e)

