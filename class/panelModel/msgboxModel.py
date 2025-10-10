# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: boazi <baozi@bt.cn>
# -------------------------------------------------------------------
# 消息盒子
# ------------------------------
import os
import time
import copy
import json
from datetime import datetime
from typing import Optional, List

import public
from panelModel.base import panelBase
from panel_msg.msg_file import message_mgr, Message


class main(panelBase):

    @staticmethod
    def get_msg_count(get):
        """获取未读信息数量，用于入口图标"""
        res = message_mgr.not_read_id
        return {
            "count": len(res),
            "not_read": len(res),
            "msgs_id": res
        }

    @staticmethod
    def get_not_read_list(get):
        """获取未读信息列表，不包含详情"""
        limit = - 1
        try:
            if hasattr(get, "limit"):
                limit = int(get.limit)
        except (ValueError, KeyError):
            return public.returnMsg(False, "参数错误")

        res = []
        limit = max(limit, -1)
        if limit == -1:
            for i in message_mgr.not_read_id:
                msg = Message.form_file(i)
                if msg:
                    res.append(msg.to_dict())
            return res
        else:
            # 取最新的id
            for i in message_mgr.not_read_id[::-1][:limit]:
                msg = Message.form_file(i)
                if msg:
                    res.append(msg.to_dict())

        return res

    @staticmethod
    def get_msg_list(get):
        """获取信息列表 """
        read = None
        try:
            page = int(get.page)
            size = int(get.size)
            is_read = get.is_read
            if "create_time_start" in get:
                create_time_start = int(get.create_time_start)
            else:
                create_time_start = None
            if "create_time_end" in get:
                create_time_end = int(get.create_time_end)
            else:
                create_time_end = None
        except (ValueError, KeyError, AttributeError):
            return public.returnMsg(False, "参数错误")

        if is_read == "read":
            read = True
        elif is_read == "not_read":
            read = False

        if page < 1:
            page = 1
        if size < 1:
            size = 20

        res = []
        count = 0
        msg_list = []
        for idx, i in enumerate(message_mgr.message_id_list()):
            count = idx + 1
            msg = Message.form_file(i)
            if not msg:
                continue
            msg_list.append(msg)

        msg_list.sort(key=lambda x: x.create_time, reverse=True)
        for msg in msg_list[(page-1) * size: page * size]:
            if msg.id not in message_mgr.not_read_id:
                msg.read = True
            if read is not None and msg.read != read:
                continue
            if create_time_start and create_time_end:
                if not create_time_start < msg.create_time < create_time_end:
                    continue

            res.append(msg.to_dict())

        return {
            "count": count,
            "msg_list": res
        }

    @staticmethod
    def get_msg_info(get):
        """获取信息详情"""
        try:
            msg_id = get.msg_id
        except (ValueError, KeyError):
            return public.returnMsg(False, "参数错误")
        msg = Message.form_file(msg_id)
        if msg is not None:
            if not msg.read:
                if msg_id in message_mgr.not_read_id:
                    message_mgr.not_read_id.remove(msg_id)
                    message_mgr.save_not_read_id()
            return msg.to_dict()
        return public.returnMsg(True, "信息丢失")

    @staticmethod
    def multi_read(get):
        """多选已读"""
        try:
            msgs_id = json.loads(get.msgs_id)
        except (ValueError, KeyError, json.JSONDecodeError):
            return public.returnMsg(False, "参数错误")
        for i in msgs_id:
            if i in message_mgr.not_read_id:
                message_mgr.not_read_id.remove(i)
            message_mgr.save_not_read_id()

            msg = Message.form_file(i)
            if msg:
                msg.read = False
                msg.save_to_file()

        return public.returnMsg(True, "操作成功")

    @staticmethod
    def multi_delete(get):
        """多选删除"""
        try:
            msgs_id = get.msgs_id
            msgs_id = json.loads(msgs_id)
        except (ValueError, KeyError, json.JSONDecodeError):
            return public.returnMsg(False, "参数错误")

        for i in msgs_id:
            if i in message_mgr.not_read_id:
                message_mgr.not_read_id.remove(i)
            message_mgr.save_not_read_id()
            msg = Message.form_file(i)
            if msg:
                msg.delete_from_file()

        return public.returnMsg(True, "操作成功")

    @staticmethod
    def read_all(get=None):
        """所有信息标为已读"""
        message_mgr.not_read_id.clear()
        message_mgr.save_not_read_id()
        return public.returnMsg(True, "操作成功")

    @staticmethod
    def delete_all(get=None):
        """所有信息删除"""
        MSG_PATH = "/www/server/panel/data/msg_box_data"
        for i in message_mgr.message_id_list():
            if os.path.exists("{}/{}".format(MSG_PATH, i)):
                os.remove("{}/{}".format(MSG_PATH, i))
        return public.returnMsg(True, "操作成功")

    @staticmethod
    def get_installed_msg(get=None):
        """获取在安装的软件的信息详情"""
        task = public.M('tasks').where("status!=?", ('1',)).field('id,status').order("id asc").find()
        if not task or isinstance(task, str):
            return public.returnMsg(False, "没有安装任务")
        task_id = task["id"]
        for i in message_mgr.message_id_list():
            msg = Message.form_file(i)
            if msg:
                if msg.sub["task_id"] == task_id:
                    return msg.to_dict()
        return public.returnMsg(False, "没有安装任务")

    @staticmethod
    def installed_msg_list(get=None):
        """获取任务队列中"""
        try:
            page = int(get.p.strip())
            pre_page = int(get.limit.strip())
        except (ValueError, KeyError, TypeError):
            return public.returnMsg(False, "参数错误")

        if page < 1:
            page = 1
        if pre_page < 1:
            pre_page = 10
        task_list = public.M('tasks').where("status = ? and type = ? ", ('1', "execshell")).order(
            "id desc").select()
        if isinstance(task_list, str):
            return public.returnMsg(False, "任务队列数据库损坏")

        count = len(task_list)
        target_list = task_list[(page - 1) * pre_page: page * pre_page + 1]
        msg_list = list(filter(None, [Message.form_file(i) for i in message_mgr.message_id_list()]))

        msg_map_by_task_id = {m.sub["task_id"]: m for m in msg_list}
        for t in target_list:
            if t["id"] in msg_map_by_task_id:
                t["msg_info"] = msg_map_by_task_id[t["id"]].to_dict()
            else:
                t["msg_info"] = None

        page_data = public.get_page(count, p=page, rows=pre_page)
        page_data["data"] = target_list

        return page_data


