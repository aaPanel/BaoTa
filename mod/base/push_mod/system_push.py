
import json
import os
import sys
import threading
import time
from datetime import datetime, timedelta
from importlib import import_module
from typing import Tuple, Union, Optional, List, Dict

import psutil

from .send_tool import WxAccountMsg
from .base_task import BaseTask, BaseTaskViewMsg
from .mods import PUSH_DATA_PATH
from .util import read_file, write_file, get_config_value, ExecShell


from .system import WAIT_TASK_LIST

try:
    if "/www/server/panel/class" not in sys.path:
        sys.path.insert(0, "/www/server/panel/class")
    from panel_msg.collector import SitePushMsgCollect, SystemPushMsgCollect
except ImportError:
    SitePushMsgCollect = None
    SystemPushMsgCollect = None


def _get_panel_name() -> str:
    data = get_config_value("title")  # 若获得别名，则使用别名
    if data == "":
        data = "宝塔面板"
    return data


class _NextThing:
    SERVICES = (
        ("nginx", "nginx"),
        ("httpd", "apache"),
        ("mysqld", "mysql"),
        ("redis", "redis"),
        ("memcached", "memcached"),
    )

    @staticmethod
    def execute_next_data(next_data: List[str]):
        """
        执行后置操作，例如重启服务。
        :param next_data: 包含需要执行的服务列表，例如 ["nginx", "mysql"]
        :return: 执行结果信息
        """
        res = []
        for service_name in next_data:
            if service_name.startswith("php"):
                base_path = "/www/server/php"
                if not os.path.exists(base_path):
                    return None
                for p in os.listdir(base_path):
                    if p != service_name.replace("php", ""):
                        continue
                    init_file = os.path.join("/etc/init.d", "php-fpm-{}".format(p))
                    if not os.path.isfile(init_file):
                        continue
                    ExecShell("{} start".format(init_file))
                    res.append(1)

            elif service_name == 'mysql':
                init_file = os.path.join("/etc/init.d", "mysqld")
                ExecShell("{} start".format(init_file))
                res.append(1)
            elif service_name == 'apache':
                init_file = os.path.join("/etc/init.d", "httpd")
                ExecShell("{} start".format(init_file))
                res.append(1)
            else:
                # 通用服务重启
                init_file = os.path.join("/etc/init.d", service_name)
                ExecShell("{} start".format(init_file))
                res.append(1)
        if len(res) == len(next_data):
            return ", 重启任务已执行"
        return ", 重启任务执行失败"

    @classmethod
    def get_available_services(cls) -> List[Dict]:
        res_list = []
        for service_file, service_name in cls.SERVICES:
            if os.path.exists('/etc/init.d/{}'.format(service_file)):
                res_list.append({
                    "title": "重启{}服务".format(service_name),
                    "value": service_name
                })

        php_path = "/www/server/php"
        if os.path.exists(php_path):
            for k in os.listdir(php_path):
                if k.isnumeric():
                    res_list.append({
                        "title": "重启php" + k,
                        "value": "php" + k
                    })
        return res_list


class PanelSysDiskTask(BaseTask):

    def __init__(self):
        super().__init__()
        self.source_name = "system_disk"
        self.template_name = "首页磁盘告警"

        self.wx_msg = ""

    def get_title(self, task_data: dict) -> str:
        return "挂载目录【{}】的磁盘余量告警".format(task_data["project"])

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        if task_data["project"] not in [i[0] for i in self._get_disk_name()]:
            return "指定的磁盘不存在"
        if not (isinstance(task_data['cycle'], int) and task_data['cycle'] in (1, 2)):
            return "类型参数错误"
        if not (isinstance(task_data['count'], int) and task_data['count'] >= 1):
            return "阈值参数错误"
        if task_data['cycle'] == 2 and task_data['count'] >= 100:
            return "阈值参数错误, 设置的检查范围不正确"
        task_data['interval'] = 600
        return task_data

    @staticmethod
    def _get_disk_name() -> list:
        """获取硬盘挂载点"""
        if "/www/server/panel" not in sys.path:
            sys.path.insert(0, "/www/server/panel")

        system_modul = import_module('.system', package="class")
        system = getattr(system_modul, "system")

        disk_info = system.GetDiskInfo2(None, human=False)

        return [(d.get("path"), d.get("size")[0]) for d in disk_info]

    @staticmethod
    def _get_disk_info() -> list:
        """获取硬盘挂载点"""
        if "/www/server/panel" not in sys.path:
            sys.path.insert(0, "/www/server/panel")

        system_modul = import_module('.system', package="class")
        system = getattr(system_modul, "system")

        disk_info = system.GetDiskInfo2(None, human=False)

        return disk_info

    def get_keyword(self, task_data: dict) -> str:
        return task_data["project"]

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        self.title = self.get_title(task_data)
        disk_info = self._get_disk_info()
        unsafe_disk_list = []

        for d in disk_info:
            if task_data["project"] != d["path"]:
                continue
            free = int(d["size"][2]) / 1048576
            proportion = int(d["size"][3] if d["size"][3][-1] != "%" else d["size"][3][:-1])

            if task_data["cycle"] == 1 and free < task_data["count"]:
                unsafe_disk_list.append(
                    "挂载在【{}】上的磁盘剩余容量为{}G，小于告警值{}G.".format(
                        d["path"], round(free, 2), task_data["count"])
                )
                self.wx_msg = "剩余容量小于{}G".format(task_data["count"])

            elif task_data["cycle"] == 2 and proportion > task_data["count"]:
                unsafe_disk_list.append(
                    "挂载在【{}】上的磁盘已使用容量为{}%，大于告警值{}%.".format(
                        d["path"], round(proportion, 2), task_data["count"])
                )
                self.wx_msg = "占用量大于{}%".format(task_data["count"])

        if len(unsafe_disk_list) == 0:
            return None

        return {
            "msg_list": [
                ">通知类型：磁盘余量告警",
                ">告警内容:\n" + "\n".join(unsafe_disk_list)
            ]
        }

    def filter_template(self, template: dict) -> Optional[dict]:
        for (path, total_size) in self._get_disk_name():
            template["field"][0]["items"].append({
                "title": "【{}】的磁盘".format(path),
                "value": path,
                "count_default": round((int(total_size) * 0.2) / 1024 / 1024, 1)
            })
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return 'machine_exception|磁盘余量告警', {
            'name': _get_panel_name(),
            'type': "磁盘空间不足",
        }

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "宝塔首页磁盘告警"
        if len(self.wx_msg) > 20:
            self.wx_msg = self.wx_msg[:17] + "..."
        msg.msg = self.wx_msg
        return msg


class PanelSysCPUTask(BaseTask, _NextThing):

    def __init__(self):
        super().__init__()
        self.source_name = "system_cpu"
        self.template_name = "首页CPU告警"
        self.title = "首页CPU告警"

        self.cpu_count = 0
        self.next_thing_msg = ""

        self._tip_file = "{}/system_cpu.tip".format(PUSH_DATA_PATH)
        self._tip_data: Optional[List[Tuple[float, float]]] = None

    @property
    def cache_list(self) -> List[Tuple[float, float]]:
        if self._tip_data is not None:
            return self._tip_data
        try:
            self._tip_data = json.loads(read_file(self._tip_file))
        except:
            self._tip_data = []
        return self._tip_data

    def save_cache_list(self):
        write_file(self._tip_file, json.dumps(self.cache_list))

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        if not (isinstance(task_data['cycle'], int) and task_data['cycle'] >= 1):
            return "时间参数错误"
        if not (isinstance(task_data['count'], int) and task_data['count'] >= 1):
            return "阈值参数错误，至少为1%"
        available_services = self.get_available_services()
        valid_services = {service["value"] for service in available_services}
        if "next_data" in task_data:
            for service in task_data["next_data"]:
                if service not in valid_services:
                    return "所选择的服务 {} 不存在".format(service)
        task_data['interval'] = 60
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return "system_cpu"

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        expiration = datetime.now() - timedelta(seconds=task_data["cycle"] * 60 + 10)
        for i in range(len(self.cache_list) - 1, -1, -1):
            data_time, _ = self.cache_list[i]
            if datetime.fromtimestamp(data_time) < expiration:
                del self.cache_list[i]

        # 记录下次的
        def thread_get_cpu_data():
            self.cache_list.append((time.time(), psutil.cpu_percent(10)))
            # print(self.cache_list)
            self.save_cache_list()

        thread_active = threading.Thread(target=thread_get_cpu_data, args=())
        thread_active.start()
        WAIT_TASK_LIST.append(thread_active)

        if len(self.cache_list) < task_data["cycle"]:  # 小于指定次数不推送
            return None

        if len(self.cache_list) > 0:
            avg_data = sum(i[1] for i in self.cache_list) / len(self.cache_list)
        else:
            avg_data = 0

        if avg_data < task_data["count"]:
            return None
        else:
            self.cache_list.clear()
        self.cpu_count = round(avg_data, 2)
        # 检查是否有后置操作
        next_msg = ""
        if "next_data" in task_data and task_data["next_data"]:
            next_msg = self.execute_next_data(task_data["next_data"])
            self.next_thing_msg = next_msg.lstrip(", ") + ",详情请登录面板"

        s_list = [
            ">通知类型：CPU高占用告警",
            ">告警内容：最近{}分钟内机器CPU平均占用率为{}%，高于告警值{}%{}".format(
                task_data["cycle"], round(avg_data, 2), task_data["count"], next_msg),
        ]

        return {
            "msg_list": s_list,
        }

    def filter_template(self, template):
        available_services = self.get_available_services()
        for field in template["field"]:
            if field["attr"] == "next_data":
                field["items"] = available_services
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return 'machine_exception|CPU高占用告警', {
            'name': _get_panel_name(),
            'type': "CPU高占用",
        }

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "宝塔首页cpu告警"
        msg.msg = "主机CPU占用超过：{}%".format(self.cpu_count)
        msg.next_msg = "请登录面板，查看主机情况" if not self.next_thing_msg else self.next_thing_msg
        return msg


class PanelSysLoadTask(BaseTask, _NextThing):

    def __init__(self):
        super().__init__()
        self.source_name = "system_load"
        self.template_name = "首页负载告警"
        self.title = "首页负载告警"

        self.next_thing_msg = ""
        self.avg_data = 0

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        available_services = self.get_available_services()
        valid_services = {service["value"] for service in available_services}
        if "next_data" in task_data:
            for service in task_data["next_data"]:
                if service not in valid_services:
                    return "所选择的服务 {} 不存在".format(service)

        if not (isinstance(task_data['cycle'], int) and task_data['cycle'] >= 1):
            return "时间参数错误"
        if not (isinstance(task_data['count'], int) and task_data['count'] >= 1):
            return "阈值参数错误，至少为1%"
        task_data['interval'] = 60 * task_data['cycle']
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return "system_load"

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        now_load = os.getloadavg()
        cpu_count = psutil.cpu_count()
        now_load = [i / (cpu_count * 2) * 100 for i in now_load]
        need_push = False
        avg_data = 0
        if task_data["cycle"] == 15 and task_data["count"] < now_load[2]:
            avg_data = now_load[2]
            need_push = True
        elif task_data["cycle"] == 5 and task_data["count"] < now_load[1]:
            avg_data = now_load[1]
            need_push = True
        elif task_data["cycle"] == 1 and task_data["count"] < now_load[0]:
            avg_data = now_load[0]
            need_push = True

        if need_push is False:
            return None

        self.avg_data = avg_data

        # 检查是否有后置操作
        next_msg = ""
        if "next_data" in task_data and task_data["next_data"]:
            next_msg = self.execute_next_data(task_data["next_data"])
            self.next_thing_msg = next_msg.lstrip(", ") + ",详情请登录面板"

        return {
            "msg_list": [
                ">通知类型：负载超标告警",
                ">告警内容：最近{}分钟内机器平均负载率为{}%，高于{}%告警值{}".format(
                    task_data["cycle"], round(avg_data, 2), task_data["count"], next_msg
                ),
            ]
        }

    def filter_template(self, template):
        available_services = self.get_available_services()
        for field in template["field"]:
            if field["attr"] == "next_data":
                field["items"] = available_services
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return 'machine_exception|负载超标告警', {
            'name': _get_panel_name(),
            'type': "平均负载过高",
        }

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "宝塔首页负载告警"
        msg.msg = "主机负载超过：{}%".format(round(self.avg_data, 2))
        msg.next_msg = "请登录面板，查看主机情况" if not self.next_thing_msg else self.next_thing_msg
        return msg


class PanelSysMEMTask(BaseTask, _NextThing):

    def __init__(self):
        super().__init__()
        self.source_name = "system_mem"
        self.template_name = "首页内存告警"
        self.title = "首页内存告警"

        self.wx_data = 0
        self.next_thing_msg = ""

        self._tip_file = "{}/system_mem.tip".format(PUSH_DATA_PATH)
        self._tip_data: Optional[List[Tuple[float, float]]] = None

    @property
    def cache_list(self) -> List[Tuple[float, float]]:
        if self._tip_data is not None:
            return self._tip_data
        try:
            self._tip_data = json.loads(read_file(self._tip_file))
        except:
            self._tip_data = []
        return self._tip_data

    def save_cache_list(self):
        write_file(self._tip_file, json.dumps(self.cache_list))

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        if not (isinstance(task_data['cycle'], int) and task_data['cycle'] >= 1):
            return "次数参数错误"
        available_services = self.get_available_services()
        valid_services = {service["value"] for service in available_services}
        if "next_data" in task_data:
            for service in task_data["next_data"]:
                if service not in valid_services:
                    return "所选择的服务 {} 不存在".format(service)
        if not (isinstance(task_data['count'], int) and task_data['count'] >= 1):
            return "阈值参数错误，至少为1%"
        task_data['interval'] = task_data['cycle'] * 60
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return "system_mem"

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        mem = psutil.virtual_memory()
        real_used: float = (mem.total - mem.free - mem.buffers - mem.cached) / mem.total
        stime = datetime.now()
        expiration = stime - timedelta(seconds=task_data["cycle"] * 60 + 10)

        self.cache_list.append((stime.timestamp(), real_used))

        for i in range(len(self.cache_list) - 1, -1, -1):
            data_time, _ = self.cache_list[i]
            if datetime.fromtimestamp(data_time) < expiration:
                del self.cache_list[i]

        avg_data = sum(i[1] for i in self.cache_list) / len(self.cache_list)

        if avg_data * 100 < task_data["count"]:
            self.save_cache_list()
            return None
        else:
            self.cache_list.clear()
            self.save_cache_list()

        self.wx_data = round(avg_data * 100, 2)
        # 检查是否有后置操作
        next_msg = ""
        if "next_data" in task_data and task_data["next_data"]:
            next_msg = self.execute_next_data(task_data["next_data"])
            self.next_thing_msg = next_msg.lstrip(", ") + ",详情请登录面板"

        return {
            'msg_list': [
                ">通知类型：内存高占用告警",
                ">告警内容：最近{}分钟内机器内存平均占用率为{}%，高于告警值{}%{}".format(
                    task_data["cycle"], round(avg_data * 100, 2), task_data["count"], next_msg),
            ]
        }

    def filter_template(self, template):
        available_services = self.get_available_services()
        for field in template["field"]:
            if field["attr"] == "next_data":
                field["items"] = available_services
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return 'machine_exception|内存高占用告警', {
            'name': _get_panel_name(),
            'type': "内存高占用",
        }

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "宝塔首页内存告警"
        msg.msg = "主机内存占用超过：{}%".format(self.wx_data)
        msg.next_msg = "请登录面板，查看主机情况" if not self.next_thing_msg else self.next_thing_msg
        return msg


class ViewMsgFormat(BaseTaskViewMsg):
    _FORMAT = {
        "20": (
            lambda x: "<span>挂载在{}上的磁盘{}触发</span>".format(
                x.get("project"),
                "余量不足%.1fG" % round(x.get("count"), 1) if x.get("cycle") == 1 else "占用超过%d%%" % x.get("count"),
            )
        ),
        "21": (
            lambda x: "<span>{}分钟内平均CPU占用超过{}%触发{}</span>".format(
                x.get("cycle"), x.get("count"),
                "" if not x.get("next_data", None) else "，随后重启【{}】服务".format(",".join(x["next_data"]))
            )
        ),
        "22": (
            lambda x: "<span>{}分钟内平均负载超过{}%触发{}</span>".format(
                x.get("cycle"), x.get("count"),
                "" if not x.get("next_data", None) else "，随后重启【{}】服务".format(",".join(x["next_data"]))
            )
        ),
        "23": (
            lambda x: "<span>{}分钟内内存使用率超过{}%触发{}</span>".format(
                x.get("cycle"), x.get("count"),
                "" if not x.get("next_data", None) else "，随后重启【{}】服务".format(",".join(x["next_data"]))
            )
        )
    }

    def get_msg(self, task: dict) -> Optional[str]:
        if task["template_id"] in self._FORMAT:
            return self._FORMAT[task["template_id"]](task["task_data"])
        return None


PanelSysDiskTask.VIEW_MSG = PanelSysCPUTask.VIEW_MSG = PanelSysLoadTask.VIEW_MSG = PanelSysMEMTask.VIEW_MSG = ViewMsgFormat