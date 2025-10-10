import json
import os
import time
from typing import Tuple, Union, Optional, List

from .mods import PUSH_DATA_PATH
from .send_tool import WxAccountMsg
from .base_task import BaseTask, BaseTaskViewMsg
from .util import read_file, DB, write_file


class NodeHttpLoadTask(BaseTask):
    def __init__(self):
        super().__init__()
        self.source_name = "nodes_nginx_http_load_push"
        self.template_name = "节点管理-负载均衡"
        self._tip_counter = None

    @property
    def tip_counter(self) -> dict:
        if self._tip_counter is not None:
            return self._tip_counter
        tip_counter = '{}/node_load_balance_push.json'.format(PUSH_DATA_PATH)
        if os.path.exists(tip_counter):
            try:
                self._tip_counter = json.loads(read_file(tip_counter))
            except json.JSONDecodeError:
                self._tip_counter = {}
        else:
            self._tip_counter = {}
        return self._tip_counter

    @staticmethod
    def _get_load_name(load_id: int):
        data = DB("load_sites").where("load_id = ? and site_type=?", (load_id, "http")).find()
        if isinstance(data, dict):
            return data["ps"]
        return ""

    @staticmethod
    def _get_all_load() -> List[dict]:
        data = DB("load_sites").where("site_type=?", ("http",)).field("load_id,ps").select()
        if isinstance(data, list):
            return data
        return []

    def save_tip_counter(self):
        tip_counter = '{}/node_load_balance_push.json'.format(PUSH_DATA_PATH)
        write_file(tip_counter, json.dumps(self.tip_counter))

    def get_title(self, task_data: dict) -> str:
        if task_data["project"] == "all":
            return "节点管理-负载节点异常告警"
        return "节点管理-负载[{}]异常告警".format(self._get_load_name(task_data["project"]))

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        all_loads = self._get_all_load()
        all_load_id = [i["load_id"] for i in all_loads]
        if not bool(all_load_id):
            return '没有负载均衡配置，无法设置告警'
        if task_data["project"] not in all_load_id:
            return '没有该负载均衡配置，无法设置告警'

        codes = []
        for i in task_data["codes"].split(","):
            if bool(i) and i.isdecimal():
                code = int(i)
                if 100 <= code < 600:
                    codes.append(str(code))
        if not bool(codes):
            return '没有指定任何错误码，无法设置告警'

        task_data["codes"] = ",".join(codes)
        task_data["interval"] = 120
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return task_data["project"]

    def _check_func(self, load_id: int, codes: str, interval: int) -> list:
        from mod.project.node.loadutil.load_check import RequestChecker
        from mod.project.node.dbutil import HttpNode, NodeDB
        access_codes = [int(i) for i in codes.split(",") if bool(i.strip())]
        nodes, err = NodeDB().get_nodes(load_id, "http")
        if not nodes:
            return []
        res_list = []
        for node in nodes:
            # 检查每个节点，返回有问题的节点信息
            node, _ = HttpNode.bind(node)
            if not node:
                continue

            node_name = node.node_site_name + ":" + str(node.port)
            if not RequestChecker.check_http_node(node, access_codes):
                if node_name in self.tip_counter:
                    self.tip_counter[node_name].append(int(time.time()))
                    self.tip_counter[node_name] = list(filter(
                        lambda i: interval * 4 + i >= time.time(),
                        self.tip_counter[node_name]
                    ))

                    # 如果一个节点连续三次出现在告警列表中，则视为需要告警
                    if len(self.tip_counter[node_name]) >= 3:
                        res_list.append(node_name)
                        self.tip_counter[node_name] = []
                else:
                    self.tip_counter[node_name] = [int(time.time()), ]

        self.save_tip_counter()
        return res_list

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        err_nodes = self._check_func(task_data["project"], task_data["codes"], task_data.get("interval", 180))
        if not err_nodes:
            return None
        pj = "负载均衡:【{}】".format(self._get_load_name(task_data["project"]))
        nodes = '、'.join(err_nodes)
        self.title = self.get_title(task_data)
        return {
            "msg_list": [
                ">通知类型：节点管理-负载均衡告警",
                ">告警内容：<font color=#ff0000>{}配置下的节点【{}】出现访问错误，请及时关注节点情况并处理。</font> ".format(
                    pj, nodes),
            ],
            "pj": pj,
            "nodes": nodes
        }

    def filter_template(self, template: dict) -> Optional[dict]:
        all_loads = self._get_all_load()
        if not all_loads:
            return None
        for item in all_loads:
            template["field"][0]["items"].append({
                "title": item["ps"],
                "value": item["load_id"]
            })
        template["field"][0]["default"] = all_loads[0]["load_id"]
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return '', {}

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "节点管理-负载均衡告警"
        msg.msg = "节点管理-负载均衡出现节点异常，请登录面板查看"
        return msg


class NodeTcpLoadTask(NodeHttpLoadTask):
    def __init__(self):
        super().__init__()
        self.source_name = "nodes_nginx_tcp_load_push"
        self.template_name = "节点管理-tcp负载均衡"
        self._tip_counter = None

    @property
    def tip_counter(self) -> dict:
        if self._tip_counter is not None:
            return self._tip_counter
        tip_counter = '{}/node_tcp_load_balance_push.json'.format(PUSH_DATA_PATH)
        if os.path.exists(tip_counter):
            try:
                self._tip_counter = json.loads(read_file(tip_counter))
            except json.JSONDecodeError:
                self._tip_counter = {}
        else:
            self._tip_counter = {}
        return self._tip_counter

    @staticmethod
    def _get_load_name(load_id: int):
        data = DB("load_sites").where("load_id = ? and site_type=?", (load_id, "tcp")).find()
        if isinstance(data, dict):
            return data["ps"]
        return ""

    @staticmethod
    def _get_all_load() -> List[dict]:
        data = DB("load_sites").where("site_type=? and tcp_config like ?", ("tcp", "%\"tcp\"%")).field(
            "load_id,ps").select()
        if isinstance(data, list):
            return data
        return []

    def save_tip_counter(self):
        tip_counter = '{}/node_tcp_load_balance_push.json'.format(PUSH_DATA_PATH)
        write_file(tip_counter, json.dumps(self.tip_counter))

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        all_loads = self._get_all_load()
        all_load_id = [i["load_id"] for i in all_loads]
        if not bool(all_load_id):
            return '没有负载均衡配置，无法设置告警'
        if task_data["project"] not in all_load_id:
            return '没有该负载均衡配置，无法设置告警'

        task_data["err_num"] = max(1, task_data.get("err_num", 1))
        task_data["interval"] = 120
        return task_data

    def _check_func(self, load_id: int, err_num: int, interval: int) -> list:
        from mod.project.node.loadutil.load_check import RequestChecker
        from mod.project.node.dbutil import TcpNode, NodeDB
        nodes, err = NodeDB().get_nodes(load_id, "tcp")
        if not nodes:
            return []
        res_list = []
        for node in nodes:
            # 检查每个节点，返回有问题的节点信息
            node, _ = TcpNode.bind(node)
            if not node:
                continue

            node_name = node.host + ":" + str(node.port)
            if not RequestChecker.check_tcp_node(node):
                if node_name in self.tip_counter:
                    self.tip_counter[node_name].append(int(time.time()))
                    self.tip_counter[node_name] = list(filter(
                        lambda i: interval * (err_num + 1) + i >= time.time(),
                        self.tip_counter[node_name]
                    ))

                    # 如果一个节点连续多次次出现在告警列表中，则视为需要告警
                    if len(self.tip_counter[node_name]) >= err_num:
                        res_list.append(node_name)
                        self.tip_counter[node_name] = []
                else:
                    self.tip_counter[node_name] = [int(time.time()), ]

        self.save_tip_counter()
        return res_list

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        err_nodes = self._check_func(task_data["project"], task_data["err_num"], task_data.get("interval", 180))
        if not err_nodes:
            return None
        pj = "tcp负载均衡:【{}】".format(self._get_load_name(task_data["project"]))
        nodes = '、'.join(err_nodes)
        self.title = self.get_title(task_data)
        return {
            "msg_list": [
                ">通知类型：节点管理-tcp负载均衡告警",
                ">告警内容：<font color=#ff0000>{}配置下的节点【{}】出现访问错误，请及时关注节点情况并处理。</font> ".format(
                    pj, nodes),
            ],
            "pj": pj,
            "nodes": nodes
        }

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return '', {}

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "节点管理-tcp负载均衡告警"
        msg.msg = "节点管理-tcp负载均衡出现节点异常"
        return msg


class NodeMysqlSlave(BaseTask):
    def __init__(self):
        super().__init__()
        self.source_name = "nodes_mysql_slave_err_push"
        self.template_name = "节点管理-Mysql主从异常告警"
        self._tip_counter = None

    def get_title(self, task_data: dict) -> str:
        return "节点管理-Mysql主从异常告警"

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        task_data["interval"] = 120
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return "nodes_mysql_slave_err_push"

    def _check_func(self) -> list:
        from mod.project.node.mysql_slaveMod import main as mysql_slave
        return mysql_slave().get_slave_error_info(get=None)

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        err_nodes = self._check_func()
        if not err_nodes:
            return None
        self.title = self.get_title(task_data)
        err_list = []
        wx_node_err = "{}主从中断，中断时间{}".format(err_nodes[0]["slave_ip"], err_nodes[0]["error_time"])
        for node in err_nodes:
            err_list.append("<font color=#ff0000>【{}】主从中断，中断时间【{}】;</font>".format(node["slave_ip"], node["error_time"]))
        err_list.append("详情请前往节点管理-主从同步查看具体报错信息")
        return {
            "msg_list": [
                ">通知类型：节点管理-Mysql主从告警",
                ">告警内容：",
                *err_list
            ],
            "node": wx_node_err
        }

    def filter_template(self, template: dict) -> Optional[dict]:
        return template

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "节点管理-Mysql主从告警"
        msg.msg = "节点管理-Mysql主从出现节点异常，请登录面板查看"
        return msg


class NodeRedisSlave(BaseTask):
    def __init__(self):
        super().__init__()
        self.source_name = "nodes_redis_slave_err_push"
        self.template_name = "节点管理-Redis主从异常告警"
        self._tip_counter = None

    def get_title(self, task_data: dict) -> str:
        return "节点管理-Redis主从异常告警"

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        task_data["interval"] = 120
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return "nodes_redis_slave_err_push"

    def _check_func(self) -> list:
        from mod.project.node.redis_slaveMod import main as redis_slave
        ret = redis_slave().get_alert_info(get=None)
        if "status" in ret and ret["status"] and "data" in ret and isinstance(ret["data"], list):
            return ret["data"]
        return []

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        err_nodes = self._check_func()
        if len(err_nodes) == 0:
            return None
        self.title = self.get_title(task_data)
        err_list = []
        wx_node_err = "{}主从中断，中断时间{}".format(err_nodes[0]["server_ip"], err_nodes[0]["timestamp"])
        for node in err_nodes:
            err_list.append("<font color=#ff0000>Redis主从服务器【{}】，异常：{}，时间：{};</font>".format(
                node["server_ip"], node["message"], node["timestamp"]))
        err_list.append("详情请前往节点管理-主从同步查看具体报错信息")
        return {
            "msg_list": [
                ">通知类型：节点管理-Redis主从异常告警",
                ">告警内容：",
                *err_list
            ],
            "node": wx_node_err
        }

    def filter_template(self, template: dict) -> Optional[dict]:
        return template

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "节点管理-Redis主从异常告警"
        msg.msg = "节点管理-Redis主从异常告警，请登录面板查看" if not push_data.get("node", None) else push_data["node"]
        return msg


class ViewMsgFormat(BaseTaskViewMsg):

    def get_msg(self, task: dict) -> Optional[str]:
        if task["template_id"] == "220":
            return "<span>负载节点测试路径访问状态码不为{}时，推送告警信息(每日推送{}次后不再推送)<span>".format(
                task.get("task_data", {}).get("codes", "").replace(",", "|"),
                task.get("number_rule", {}).get("day_num"))
        if task["template_id"] == "221":
            return "<span>负载节点连接异常时，推送告警信息(每日推送{}次后不再推送)<span>".format(
                task.get("number_rule", {}).get("day_num"))
        if task["template_id"] == "222":
            return "<span>任意Mysql主从配置异常时，推送告警信息(每日推送{}次后不再推送)<span>".format(
                task.get("number_rule", {}).get("day_num"))
        if task["template_id"] == "223":
            return "<span>任意Redis主从配置异常时，推送告警信息(每日推送{}次后不再推送)<span>".format(
                task.get("number_rule", {}).get("day_num"))
        return None


NodeMysqlSlave.VIEW_MSG = NodeHttpLoadTask.VIEW_MSG = NodeTcpLoadTask.VIEW_MSG = ViewMsgFormat
