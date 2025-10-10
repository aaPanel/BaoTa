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
import json
import os
from typing import List
from mod.base import json_response

from mod.base.push_mod import PushManager, TaskConfig, TaskRecordConfig, TaskTemplateConfig, PushSystem, SenderConfig
from mod.base.push_mod import update_mod_push_system, UPDATE_MOD_PUSH_FILE, load_task_template_by_file, \
    UPDATE_VERSION_FILE, update_mod_push_system2
from mod.base.msg import update_mod_push_msg
from mod.base.push_mod.rsync_push import load_rsync_template
from mod.base.push_mod.task_manager_push import load_task_manager_template
from mod.base.push_mod.load_push import load_load_template
from mod.base.push_mod.util import ExecShell, debug_log
from mod.base.push_mod.web_log_push import load_web_log_template


def update_mod():
    try:
        with open(UPDATE_VERSION_FILE, 'r') as f:
            if f.read() == "11.0a":
                pl = False
            else:
                pl = True
    except:
        pl = True

    if pl:
        print("========================rewrite=====================")
        load_task_template_by_file("/www/server/panel/mod/base/push_mod/site_push_template.json")
        load_task_template_by_file("/www/server/panel/mod/base/push_mod/system_push_template.json")
        load_task_template_by_file("/www/server/panel/mod/base/push_mod/database_push_template.json")
        load_task_template_by_file("/www/server/panel/mod/base/push_mod/ssl_push_template.json")
        load_task_template_by_file("/www/server/panel/mod/base/push_mod/ftp_push_template.json")
        load_task_template_by_file("/www/server/panel/mod/base/push_mod/safe_mod_push_template.json")
        load_task_template_by_file("/www/server/panel/mod/base/push_mod/monitor_push_template.json")
        load_task_template_by_file("/www/server/panel/mod/base/push_mod/mod_node_push_template.json")
        load_rsync_template()
        load_task_manager_template()
        load_load_template()
        load_web_log_template()
        update_mod_push_system2()
        with open(UPDATE_VERSION_FILE, "w") as f:
            f.write("11.0a")
            # debug_log(">>>>>>> update_mod_push_system <<<<<<<<")

    if not os.path.exists(UPDATE_MOD_PUSH_FILE):
        update_mod_push_msg()
        update_mod_push_system()

    check_mod_push_file = "/www/server/panel/data/mod_push_data/check_mod_push_file.pl"
    if not os.path.exists(check_mod_push_file):
        ExecShell('nohup btpython /www/server/panel/script/migrate_push_tasks.py > /dev/null 2>&1 &')

try:
    update_mod()
except:
    pass
del update_mod


class main(PushManager):

    def get_task_list(self, get=None):
        sf = kf = None
        template_ids = None
        if get:
            sf = get.get("status/s", "").lower()
            if sf and sf in ("true", "1"):
                sf = True
            elif sf and sf in ("false", "0"):
                sf = False
            else:
                sf = None

            kf = get.get("keyword/s", "").lower()
            try:
                template_ids = [str(i) for i in json.loads(get.get("template_ids/s", "[]"))]
            except:
                template_ids = None

        res = self._get_task_list(status=sf, keyword=kf, template_id=template_ids)
        return json_response(status=True, data=res)

    def _get_task_list(self, status: bool=None, keyword: str=None, template_id: List[str] = None):
        res = TaskConfig().config
        # 按创建时间排序
        res.sort(key=lambda x: x["create_time"], reverse=True)
        can_call_template_ids = TaskTemplateConfig.can_call_template_ids()
        res = [task for task in res if task["template_id"] in can_call_template_ids]

        # 根据状态过滤任务
        if status is not None:
            res = [task for task in res if bool(task["status"]) == status]

        if template_id is not None and isinstance(template_id, list) and len(template_id) > 0:
            res = [task for task in res if task["template_id"] in template_id]

        for i in res:
            i['view_msg'] = self.get_view_msg_format(i)

        # 根据关键词过滤任务
        if keyword is not None and keyword:
            filtered_res = []
            for task in res:
                task_match = False
                if keyword in task["view_msg"].lower() or keyword in task["title"].lower():
                    task_match = True
                else:
                    sc = SenderConfig()
                    # 通道类型映射，包含模糊匹配规则
                    channel_map = {
                        "wx_account": "微信公众号",
                        "mail": "邮箱",
                        "webhook": "自定义通道",
                        "feishu": "飞书",
                        "dingding": "钉钉",
                        "weixin": "企业微信",
                        "sms": "短信"
                    }

                    for sender_id in task["sender"]:
                        sender = sc.get_by_id(sender_id)
                        if not sender:
                            continue
                        sender_title = sender.get("data", {}).get("title", "").lower()
                        sender_type = sender.get("sender_type", "")
                        sender_type_name = channel_map.get(sender_type, "")
                        if keyword in sender_title or keyword in sender_type or keyword in sender_type_name:
                            task_match = True
                            break

                if task_match:
                    filtered_res.append(task)

            res = filtered_res

        return res

    @staticmethod
    def get_task_record(get):
        page = 1
        size = 10
        try:
            if hasattr(get, "page"):
                page = int(get.page.strip())
            if hasattr(get, "size"):
                size = int(get.size.strip())
            task_id = get.task_id.strip()
        except (AttributeError, ValueError, TypeError):
            return json_response(status=False, msg="参数错误")

        t = TaskRecordConfig(task_id)
        t.config.sort(key=lambda x: x["create_time"])
        page = max(page, 1)
        size = max(size, 1)
        count = len(t.config)
        data = t.config[(page - 1) * size: page * size]
        return json_response(status=True, data={
            "count": count,
            "list": data,
        })

    def clear_task_record(self, get):
        try:
            task_id = get.task_id.strip()
        except (AttributeError, ValueError, TypeError):
            return json_response(status=False, msg="参数错误")
        self.clear_task_record_by_task_id(task_id)

        return json_response(status=True, msg="清除成功")

    @staticmethod
    def remove_task_records(get):
        try:
            task_id = get.task_id.strip()
            record_ids = set(json.loads(get.record_ids.strip()))
        except (AttributeError, ValueError, TypeError):
            return json_response(status=False, msg="参数错误")
        task_records = TaskRecordConfig(task_id)
        for i in range(len(task_records.config) - 1, -1, -1):
            if task_records.config[i]["id"] in record_ids:
                del task_records.config[i]

        task_records.save_config()
        return json_response(status=True, msg="清除成功")

    @staticmethod
    def get_task_template_list(get=None):
        res = []
        p_sys = PushSystem()
        tags = set()
        for i in TaskTemplateConfig().config:
            if not i['used']:
                continue
            to = p_sys.get_task_object(i["id"], i["load_cls"])
            if not to:
                continue
            t = to.filter_template(i["template"])
            if not t:
                continue
            i["template"] = t
            tags.update(set(t.get("tags", [])))
            res.append(i)

        return json_response(status=True, data=res)

    @classmethod
    def get_view_msg_format(cls, task: dict) -> str:
        return TaskTemplateConfig.task_view_msg_format(task)

    def monitor_push_list(self, get):
        res = self._get_task_list(template_id=["130", "131", "132"])
        site_name = get.get("site_name/s", "")
        if site_name:
            res = [i for i in res if site_name == i["task_data"]["site"]]
        return json_response(status=True, data=res)
