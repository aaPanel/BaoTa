import json
import os
import time
from typing import Tuple, Union, Optional

from .mods import PUSH_DATA_PATH, TaskTemplateConfig, TaskConfig
from .send_tool import WxAccountMsg
from .base_task import BaseTask, BaseTaskViewMsg
from .util import read_file, DB, GET_CLASS, write_file


class NginxLoadTask(BaseTask):
    def __init__(self):
        super().__init__()
        self.source_name = "nginx_load_push"
        self.template_name = "负载均衡告警"
        self._tip_counter = None

    @property
    def tip_counter(self) -> dict:
        if self._tip_counter is not None:
            return self._tip_counter
        tip_counter = '{}/load_balance_push.json'.format(PUSH_DATA_PATH)
        if os.path.exists(tip_counter):
            try:
                self._tip_counter = json.loads(read_file(tip_counter))
            except json.JSONDecodeError:
                self._tip_counter = {}
        else:
            self._tip_counter = {}
        return self._tip_counter

    def save_tip_counter(self):
        tip_counter = '{}/load_balance_push.json'.format(PUSH_DATA_PATH)
        write_file(tip_counter, json.dumps(self.tip_counter))

    def get_title(self, task_data: dict) -> str:
        if task_data["project"] == "all":
            return "负载节点异常告警"
        return "负载节点[{}]异常告警".format(task_data["project"])

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        all_upstream_name = DB("upstream").field("name").select()
        if isinstance(all_upstream_name, str) and all_upstream_name.startswith("error"):
            return '没有负载均衡配置，无法设置告警'
        all_upstream_name = [i["name"] for i in all_upstream_name]
        if not bool(all_upstream_name):
            return '没有负载均衡配置，无法设置告警'
        if task_data["project"] not in all_upstream_name and task_data["project"] != "all":
            return '没有该负载均衡配置，无法设置告警'

        cycle = []
        for i in task_data["cycle"].split("|"):
            if bool(i) and i.isdecimal():
                code = int(i)
                if 100 <= code < 600:
                    cycle.append(str(code))
        if not bool(cycle):
            return '没有指定任何错误码，无法设置告警'

        task_data["cycle"] = "|".join(cycle)
        task_data["interval"] = 300
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return task_data["project"]

    def _check_func(self, upstream_name: str, codes: str, interval:int) -> list:
        import PluginLoader
        get_obj = GET_CLASS()
        get_obj.upstream_name = upstream_name
        # 调用外部插件检查负载均衡的健康状况
        upstreams = PluginLoader.plugin_run("load_balance", "get_check_upstream", get_obj)
        access_codes = [int(i) for i in codes.split("|") if bool(i.strip())]
        res_list = []
        for upstream in upstreams:
            # 检查每个节点，返回有问题的节点信息
            res = upstream.check_nodes(access_codes, return_nodes=True)
            for ping_url in res:
                if ping_url in self.tip_counter:
                    self.tip_counter[ping_url].append(int(time.time()))
                    idx = 0
                    for i in self.tip_counter[ping_url]:
                        # 清理超过4分钟的记录
                        if time.time() - i > interval * 4:
                            idx += 1
                    self.tip_counter[ping_url] = self.tip_counter[ping_url][idx:]
                    print("self.tip_counter[ping_url]",self.tip_counter[ping_url])
                    # 如果一个节点连续三次出现在告警列表中，则视为需要告警
                    if len(self.tip_counter[ping_url]) >= 3:
                        res_list.append(ping_url)
                        self.tip_counter[ping_url] = []
                else:
                    self.tip_counter[ping_url] = [int(time.time()), ]
        self.save_tip_counter()
        return res_list

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        err_nodes = self._check_func(task_data["project"], task_data["cycle"], task_data.get("interval", 300))
        if not err_nodes:
            return None
        pj = "负载均衡:【{}】".format(task_data["project"]) if task_data["project"] != "all" else "负载均衡"
        nodes = '、'.join(err_nodes)
        self.title = self.get_title(task_data)
        return {
            "msg_list": [
                ">通知类型：负载均衡告警",
                ">告警内容：<font color=#ff0000>{}配置下的节点【{}】出现访问错误，请及时关注节点情况并处理。</font> ".format(
                    pj, nodes),
            ],
            "pj": pj,
            "nodes": nodes
        }

    def filter_template(self, template: dict) -> Optional[dict]:
        if not os.path.exists("/www/server/panel/plugin/load_balance/load_balance_main.py"):
            return None
        all_upstream = DB("upstream").field("name").select()
        if isinstance(all_upstream, str) and all_upstream.startswith("error"):
            return None
        all_upstream_name = [i["name"] for i in all_upstream]
        if not all_upstream_name:
            return None
        for name in all_upstream_name:
            template["field"][0]["items"].append({
                "title": name,
                "value": name
            })
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return '', {}

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "负载均衡告警"
        msg.msg = "负载均衡出现节点异常，请登录面板查看"
        return msg

    def task_config_create_hook(self, task: dict) -> None:
        old_config_file = "/www/server/panel/class/push/push.json"
        try:
            old_config = json.loads(read_file(old_config_file))
        except:
            return
        if "load_balance_push" not in old_config:
            old_config["load_balance_push"] = {}
        old_data = {
            "push_count": task["number_rule"].get("day_num", 2),
            "cycle": task["task_data"].get("cycle", "200|301|302|403|404"),
            "interval": task["task_data"].get("interval", 600),
            "title": task["title"],
            "status": task['status'],
            "module": ",".join(task["sender"])
        }
        for k, v in old_config["load_balance_push"].items():
            if v["project"] == task["task_data"]["project"]:
                v.update(old_data)
        else:
            old_data["project"] = task["task_data"]["project"]
            old_config["load_balance_push"][int(time.time())] = old_data

        write_file(old_config_file, json.dumps(old_config))

    def task_config_update_hook(self, task: dict) -> None:
        return self.task_config_create_hook(task)

    def task_config_remove_hook(self, task: dict) -> None:
        old_config_file = "/www/server/panel/class/push/push.json"
        try:
            old_config = json.loads(read_file(old_config_file))
        except:
            return
        if "load_balance_push" not in old_config:
            old_config["load_balance_push"] = {}
        old_config["load_balance_push"] = {
            k: v for k, v in old_config["load_balance_push"].items()
            if v["project"] != task["task_data"]["project"]
        }

        write_file(old_config_file, json.dumps(old_config))


def load_load_template():
    from .mods import load_task_template_by_config
    load_task_template_by_config(
        [{
            "id": "50",
            "ver": "1",
            "used": True,
            "source": "nginx_load_push",
            "title": "负载均衡",
            "load_cls": {
                "load_type": "path",
                "cls_path": "mod.base.push_mod.load_push",
                "name": "NginxLoadTask"
            },
            "template": {
                "field": [
                    {
                        "attr": "project",
                        "name": "负载名称",
                        "type": "select",
                        "default": "all",
                        "unit": "",
                        "suffix": (
                            "<i style='color: #999;font-style: initial;font-size: 12px;margin-right: 5px'>*</i>"
                            "<span style='color:#999'>选中的负载配置中，出现节点访问失败时，触发告警</span>"
                        ),
                        "items": [
                            {
                                "title": "所有已配置的负载",
                                "value": "all"
                            }
                        ]
                    },
                    {
                        "attr": "cycle",
                        "name": "成功的状态码",
                        "type": "textarea",
                        "unit": "",
                        "suffix": (
                            "<br><i style='color: #999;font-style: initial;font-size: 12px;margin-right: 5px'>*</i>"
                            "<span style='color:#999'>状态码以竖线分隔，如：200|301|302|403|404</span>"
                        ),
                        "width": "400px",
                        "style": {
                            'height': '70px',
                        },
                        "default": "200|301|302|403|404"
                    }
                ],
                "sorted": [
                    [
                        "project"
                    ],
                    [
                        "cycle"
                    ]
                ],
            },
            "default": {
                "project": "all",
                "cycle": "200|301|302|403|404"
            },
            "advanced_default": {
                "number_rule": {
                    "day_num": 3
                }
            },
            "send_type_list": [
                "wx_account",
                "dingding",
                "feishu",
                "mail",
                "weixin",
                "webhook"
            ],
            "unique": False,
            "tags": ["plugin"],
            "description": "每隔一段时间检查负载均衡插件中，设置的节点是否可以正常访问，当访问异常时发送告警通知"
        }]
    )


class ViewMsgFormat(BaseTaskViewMsg):

    def get_msg(self, task: dict) -> Optional[str]:
        if task["template_id"] == "50":
            return "<span>节点访问异常时，推送告警信息(每日推送{}次后不再推送)<span>".format(
                task.get("number_rule", {}).get("day_num"))
        return None


NginxLoadTask.VIEW_MSG = ViewMsgFormat