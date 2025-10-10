import json
import os
import re
import time
from datetime import datetime, timedelta
from typing import Tuple, Union, Optional, Iterator

from .send_tool import WxAccountMsg
from .base_task import BaseTask, BaseTaskViewMsg
from .mods import TaskTemplateConfig, SenderConfig
from .util import read_file, write_file


def rsync_ver_is_38() -> Optional[bool]:
    """
    检查rsync的版本是否为3.8。
    该函数不接受任何参数。
    返回值：
    - None: 如果无法确定rsync的版本或文件不存在。
    - bool: 如果版本确定为3.8，则返回True；否则返回False。
    """
    push_file = "/www/server/panel/plugin/rsync/rsync_push.py"
    if not os.path.exists(push_file):
        return None
    ver_info_file = "/www/server/panel/plugin/rsync/info.json"
    if not os.path.exists(ver_info_file):
        return None
    try:
        info = json.loads(read_file(ver_info_file))
    except (json.JSONDecodeError, TypeError):
        return None
    ver = info["versions"]
    ver_tuples = [int(i) for i in ver.split(".")]
    if len(ver_tuples) < 3:
        ver_tuples.extend([0] * (3 - len(ver_tuples)))
    if ver_tuples[0] < 3:
        return None
    if ver_tuples[1] <= 8 and ver_tuples[0] == 3:
        return True

    return False


class Rsync38Task(BaseTask):

    def __init__(self):
        super().__init__()
        self.source_name = "rsync_push"
        self.template_name = "文件同步告警"
        self.title = "文件同步告警"

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        if "interval" not in task_data or not isinstance(task_data["interval"], int):
            task_data["interval"] = 600
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return "rsync_push"

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        has_err = self._check(task_data.get("interval", 600))
        if not has_err:
            return None

        return {
            "msg_list": [
                ">通知类型：文件同步告警",
                ">告警内容：<font color=#ff0000>文件同步执行中出错了，请及时关注文件同步情况并处理。</font> ",
            ]
        }

    @staticmethod
    def _check(interval: int) -> bool:
        if not isinstance(interval, int):
            return False
        start_time = datetime.now() - timedelta(seconds=interval * 1.2)
        log_file = "{}/plugin/rsync/lsyncd.log".format("/www/server/panel")
        if not os.path.exists(log_file):
            return False
        return LogChecker(log_file=log_file, start_time=start_time)()

    def check_time_rule(self, time_rule: dict) -> Union[dict, str]:
        if "send_interval" not in time_rule or not isinstance(time_rule["interval"], int):
            time_rule["send_interval"] = 3 * 60
        if time_rule["send_interval"] < 60:
            time_rule["send_interval"] = 60
        return time_rule

    def filter_template(self, template: dict) -> Optional[dict]:
        res = rsync_ver_is_38()
        if res is None:
            return None
        if res:
            return template
        else:
            return None

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return '', {}

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "文件同步告警"
        msg.msg = "同步执行出错了，请及时关注同步情况"
        return msg

    def task_config_create_hook(self, task: dict) -> Optional[str]:
        return self.task_config_update_hook(task)

    def task_config_update_hook(self, task: dict) -> Optional[str]:
        old_file = "/www/server/panel/class/push/push.json"
        try:
            data = json.loads(read_file(old_file))
        except:
            data = {}

        sc = SenderConfig()
        module = set()
        for i in task.get("sender", []):
            tmp = sc.get_by_id(i)
            if tmp and tmp["sender_type"] != "webhook":
                module.add(tmp["sender_type"])
            if tmp and tmp["sender_type"] == "webhook":
                module.add(tmp["data"].get("title", "webhook"))

        old_id_list = list(data.get("rsync_push", {}).keys())
        old_id = old_id_list[0] if len(old_id_list) > 0 else str(int(time.time()))

        data["rsync_push"] = {
            old_id: {
                "key": "",
                "type": "",
                "cycle": 1,
                "count": 1,
                "interval": task.get("interval", 600),
                "module": ",".join(module),
                "push_count": task.get("number_rule", {}).get("day_num", 3),
                "title": "文件同步告警",
                "status": task["status"],
                "project": "rsync_all"
            }
        }
        write_file(old_file, json.dumps(data))
        return

    def task_config_remove_hook(self, task: dict) -> None:
        old_file = "/www/server/panel/class/push/push.json"
        try:
            data = json.loads(read_file(old_file))
        except:
            data = {}
        data["rsync_push"] = {}
        write_file(old_file, json.dumps(data))
        return


class Rsync39Task(BaseTask):

    def __init__(self):
        super().__init__()
        self.source_name = "rsync_push"
        self.template_name = "文件同步告警"
        self.title = "文件同步告警"

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        if "interval" not in task_data or not isinstance(task_data["interval"], int):
            task_data["interval"] = 600
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return "rsync_push"

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        """
        不返回数据，以实时触发为主
        """
        return None

    def check_time_rule(self, time_rule: dict) -> Union[dict, str]:
        if "send_interval" not in time_rule or not isinstance(time_rule["send_interval"], int):
            time_rule["send_interval"] = 3 * 60
        if time_rule["send_interval"] < 60:
            time_rule["send_interval"] = 60
        return time_rule

    def filter_template(self, template: dict) -> Optional[dict]:
        res = rsync_ver_is_38()
        if res is None:
            return None
        if res is False:
            return template
        else:
            return None

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return '', {}

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        task_name = push_data.get("task_name", None)
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "文件同步告警"
        if task_name:
            msg.msg = "文件同步任务{}出错了".format(task_name)
        else:
            msg.msg = "同步执行出错了，请及时关注同步情况"
        return msg

    def task_config_create_hook(self, task: dict) -> Optional[str]:
        return self.task_config_update_hook(task)

    def task_config_update_hook(self, task: dict) -> Optional[str]:
        old_file = "/www/server/panel/class/push/push.json"
        try:
            data = json.loads(read_file(old_file))
        except:
            data = {}

        sc = SenderConfig()
        module = set()
        for i in task.get("sender", []):
            tmp = sc.get_by_id(i)
            if tmp and tmp["sender_type"] != "webhook":
                module.add(tmp["sender_type"])
            if tmp and tmp["sender_type"] == "webhook":
                module.add(tmp["data"].get("title", "webhook"))

        old_id_list = list(data.get("rsync_push", {}).keys())
        old_id = old_id_list[0] if len(old_id_list) > 0 else str(int(time.time()))

        data["rsync_push"] = {
            old_id: {
                "key": "",
                "type": "",
                "cycle": 1,
                "count": 1,
                "interval": task.get("interval", 600),
                "module": ",".join(module),
                "push_count": task.get("number_rule", {}).get("day_num", 3),
                "title": "文件同步告警",
                "status": task["status"],
                "project": "rsync_all"
            }
        }
        write_file(old_file, json.dumps(data))
        return

    def task_config_remove_hook(self, task: dict) -> None:
        old_file = "/www/server/panel/class/push/push.json"
        try:
            data = json.loads(read_file(old_file))
        except:
            data = {}
        data["rsync_push"] = {}
        write_file(old_file, json.dumps(data))
        return


class LogChecker:
    """
    排序查询并获取日志内容
    """
    rep_time = re.compile(r'(?P<target>(\w{3}\s+){2}(\d{1,2})\s+(\d{2}:?){3}\s+\d{4})')
    format_str = '%a %b %d %H:%M:%S %Y'
    err_datetime = datetime.fromtimestamp(0)
    err_list = ("error", "Error", "ERROR", "exitcode = 10", "failed")

    def __init__(self, log_file: str, start_time: datetime):
        self.log_file = log_file
        self.start_time = start_time
        self.is_over_time = None  # None:还没查到时间，未知， False: 可以继续网上查询， True:比较早的数据了，不再向上查询
        self.has_err = False  # 目前已查询的内容中是否有报错信息

    def _format_time(self, log_line) -> Optional[datetime]:
        try:
            date_str_res = self.rep_time.search(log_line)
            if date_str_res:
                time_str = date_str_res.group("target")
                return datetime.strptime(time_str, self.format_str)
        except Exception:
            return self.err_datetime
        return None

    # 返回日志内容
    def __call__(self):
        _buf = b""
        file_size, fp = os.stat(self.log_file).st_size - 1, open(self.log_file, mode="rb")
        fp.seek(-1, 2)
        while file_size:
            read_size = min(1024, file_size)
            fp.seek(-read_size, 1)
            buf: bytes = fp.read(read_size) + _buf
            fp.seek(-read_size, 1)
            if file_size > 1024:
                idx = buf.find(ord("\n"))
                _buf, buf = buf[:idx], buf[idx + 1:]
            for i in self._get_log_line_from_buf(buf):
                self._check(i)
                if self.is_over_time:
                    return self.has_err
            file_size -= read_size
        return False

    # 从缓冲中读取日志
    @staticmethod
    def _get_log_line_from_buf(buf: bytes) -> Iterator[str]:
        n, m = 0, 0
        buf_len = len(buf) - 1
        for i in range(buf_len, -1, -1):
            if buf[i] == ord("\n"):
                log_line = buf[buf_len + 1 - m: buf_len - n + 1].decode("utf-8")
                yield log_line
                n = m = m + 1
            else:
                m += 1
        yield buf[0: buf_len - n + 1].decode("utf-8")

    # 格式化并筛选查询条件
    def _check(self, log_line: str) -> None:
        # 筛选日期
        for err in self.err_list:
            if err in log_line:
                self.has_err = True

        ck_time = self._format_time(log_line)
        if ck_time:
            self.is_over_time = self.start_time > ck_time


def load_rsync_template():
    """
    加载rsync模板
    """
    from .mods import load_task_template_by_config
    load_task_template_by_config(
        [{
            "id": "40",
            "ver": "1",
            "used": True,
            "source": "rsync_push",
            "title": "文件同步告警",
            "load_cls": {
                "load_type": "path",
                "cls_path": "mod.base.push_mod.rsync_push",
                "name": "RsyncTask"
            },
            "template": {
                "field": [
                ],
                "sorted": [
                ]
            },
            "default": {
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
            "unique": True,
            "tags": ["plugin"],
            "description": "当文件同步工具执行同步任务出错时，发送告警通知，帮助管理员快速知晓文件同步情况"
        }]
    )


RsyncTask = Rsync39Task
if rsync_ver_is_38() is True:
    RsyncTask = Rsync38Task


def push_rsync_by_task_name(task_name: str):
    from .system import push_by_task_keyword

    push_data = {
        "task_name": task_name,
        "msg_list": [
            ">通知类型：文件同步告警",
            ">告警内容：<font color=#ff0000>文件同步任务{}在执行中出错了，请及时关注文件同步情况并处理。</font> ".format(
                task_name),
        ]
    }
    push_by_task_keyword("rsync_push", "rsync_push", push_data=push_data)


class ViewMsgFormat(BaseTaskViewMsg):

    def get_msg(self, task: dict) -> Optional[str]:
        if task["template_id"] == "40":
            return "<span>文件同步出现异常时，推送告警信息(每日推送{}次后不再推送)<span>".format(
                task.get("number_rule", {}).get("day_num"))
        return None


RsyncTask.VIEW_MSG = ViewMsgFormat