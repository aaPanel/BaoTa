import json
import os
import sys
import time
from typing import Optional, List, Union, Dict, Any
from uuid import uuid4
from .msg_db import Message as OldMessage

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
import public

MSG_PATH = "/www/server/panel/data/msg_box_data"
UPDATE_TIP = "{}/update.pl".format(MSG_PATH)


if not os.path.exists(MSG_PATH):
    os.makedirs(MSG_PATH, 0o600)


class Message:

    def __init__(self):
        self.id: Optional[str] = None
        self.title: str = ""
        self.read: bool = False
        self.msg_types: List[str] = []
        self.source: List[str] = []
        self.level: str = "info"
        self.create_time: int = 0
        self.read_time: int = 0
        self.sub_type = "soft_install"
        self.sub: Dict[str, Any] = {}

    def msg_filename(self):
        return "{}/{}".format(MSG_PATH, self.id)

    def json(self) -> str:
        return json.dumps(self.to_dict())

    def to_dict(self) -> dict:
        res = {
            "id": self.id,
            "title": self.title,
            "read": self.read,
            "msg_types": self.msg_types,
            "source": self.source,
            "level": self.level,
            "create_time": self.create_time,
            "read_time": self.read_time,
            "sub_type": "soft_install",
            "sub": self.sub,
        }
        return res

    @classmethod
    def form_file(cls, msg_id: str) -> Optional["Message"]:
        filename = "{}/{}".format(MSG_PATH, msg_id)
        if not os.path.exists(filename):
            return None
        try:
            data = json.loads(public.ReadFile(filename))
        except:
            os.remove(filename)
            return None
        if not isinstance(data, dict):
            os.remove(filename)
            return None
        return cls.form_dict(data)

    @classmethod
    def form_dict(cls, data: dict) -> "Message":
        msg = cls()
        msg.id = data.get("id", None)
        msg.title = data.get("title", "")
        msg.read = data.get("read", False)
        msg.msg_types = data.get("msg_types", [])
        msg.source = data.get("source", [])
        msg.level = data.get("level", "unknown")
        msg.create_time = data.get("create_time", 0)
        msg.read_time = data.get("read_time", 0)
        msg.sub_type = "soft_install"
        msg.sub = data.get("sub", {})

        return msg

    @staticmethod
    def new_id() -> str:
        return uuid4().hex[::2]

    def save_to_file(self) -> str:
        """
        保存信息到文件
        """
        if self.id is None:
            self.id = self.new_id()
            public.WriteFile(self.msg_filename(), self.json())
        else:
            public.WriteFile(self.msg_filename(), self.json())

        return self.id

    def delete_from_file(self):
        """
        删除信息
        """
        if "file_name" in self.sub:
            if os.path.exists(self.sub["file_name"]) and not self.sub["file_name"].startswith("/tmp"):
                os.remove(self.sub["file_name"])
        if os.path.exists(self.msg_filename()):
            os.remove(self.msg_filename())

    @classmethod
    def new(cls, title: str = '',
            source: List[str] = None,
            sub_msg: dict = None,
            level: str = "info") -> "Message":
        """
        新建一条信息：
        title：信息标题
        msg_types：信息类型
        sub_msg: 信息详情
            包含一个特殊key： self_type, 表明详细信息的类型
        """

        if title == "":
            raise ValueError("标题不能为空")
        if sub_msg is None:
            raise ValueError("详细信息不能为空")
        msg = cls()
        msg.title = title
        msg.sub_type = sub_msg.pop("self_type")
        msg.sub = sub_msg
        msg.msg_types = ["软件安装", "软件安装"]
        msg.source = source
        msg.level = level
        msg.create_time = int(time.time())

        return msg


class MsgMgr:

    def __init__(self):
        self._not_read_file = "{}/not_read.tip".format(MSG_PATH)
        if not os.path.exists(self._not_read_file):
            public.WriteFile(self._not_read_file, '[]')
        self._not_read_id: List[str] = []
        self.last_change_time: int = 0
        self._update_msg()

    @property
    def not_read_id(self) -> List:
        if not os.path.exists(self._not_read_file):
            self._not_read_id = []
            return self._not_read_id

        mtime = os.stat(self._not_read_file).st_mtime
        if int(mtime) == self.last_change_time:
            return self._not_read_id

        try:
            data = json.loads(public.ReadFile(self._not_read_file))
            if not isinstance(data, list):
                raise ValueError
            else:
                self._not_read_id = data
        except:
            public.WriteFile(self._not_read_file, '[]')
            self._not_read_id = []

        self.last_change_time = os.stat(self._not_read_file).st_mtime
        return self._not_read_id

    def save_not_read_id(self):
        public.WriteFile(self._not_read_file, json.dumps(self._not_read_id))
        self.last_change_time = os.stat(self._not_read_file).st_mtime

    def collect_message(self,
                        title: str = '',
                        source: List[str] = None,
                        sub_msg: dict = None
                        ) -> Union[Message, str]:

        msg = Message.new(title, source, sub_msg)
        msg.save_to_file()
        self.not_read_id.append(msg.id)
        self.save_not_read_id()
        return msg

    @staticmethod
    def message_id_list():
        return [i for i in os.listdir(MSG_PATH) if i not in ("not_read.tip", "update.pl")]

    def _update_msg(self):
        """更新到新版存储方式"""
        if os.path.exists(UPDATE_TIP) or not os.path.exists("/www/server/panel/data/msg_box.db"):
            return
        try:
            msg_list: List[OldMessage] = OldMessage.query_by_sub_args(sub_name="soft_install", order_by="msg.id desc")
            msg_list = msg_list[:200]
            for i in msg_list:
                msg = Message.form_dict(i.to_dict())
                msg.id = Message.new_id()
                msg.save_to_file()
                if not msg.read:
                    self.not_read_id.append(msg.id)
            self.save_not_read_id()
        except:
            public.print_log(public.get_error_info())
            pass
        public.WriteFile(UPDATE_TIP, '')

    @staticmethod
    def clear_overdue_msg():
        """清理过期信息"""
        pass

    @staticmethod
    def get_by_task_id(task_id: int) -> Optional[Message]:
        for i in message_mgr.message_id_list():
            msg = Message.form_file(i)
            if msg:
                if msg.sub["task_id"] == task_id:
                    return msg
        return None


message_mgr = MsgMgr()
