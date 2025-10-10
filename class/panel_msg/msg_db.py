import json
import os
import shutil
import types
import fcntl
from importlib import import_module
from typing import Optional, List, Union, Tuple
from datetime import datetime

import public

_ALLOWED_SUB_TYPES = []  # 允许的信息详情类型

_LEVEL_TO_INT = {
    "unknown": 0,
    "info": 1,
    "warning": 2,
    "error": 3
}


def _level_to_int(level: str) -> int:
    if level in _LEVEL_TO_INT:
        return _LEVEL_TO_INT[level]
    return 0


def _int_to_level(level_int: int) -> str:
    if level_int == 0:
        return "unknown"
    elif level_int == 1:
        return "info"
    elif level_int == 2:
        return "warning"
    return "error"


def load_module():
    # 加载所有可用的子信息类型，并执行建立数据库的函数
    for file in os.listdir(os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__))), "initd")):
        if file.endswith(".py"):
            try:
                m = import_module(".initd.{}".format(file[:-3]), package='panel_msg')
            except ImportError:
                continue

            if not hasattr(m, "ALLOWED_TYPE") or not isinstance(m.ALLOWED_TYPE, str):
                continue

            if not hasattr(m, "init_db") or not callable(m.init_db):
                continue

            if m.ALLOWED_TYPE not in _ALLOWED_SUB_TYPES:
                _ALLOWED_SUB_TYPES.append(m.ALLOWED_TYPE)
                m.init_db()


def init():
    pass
    # _init_msg_db()
    # load_module()


def lock_msg_db():
    with open("/www/server/panel/data/msg_box.db", mode="rb") as msg_fd:
        fcntl.flock(msg_fd.fileno(), fcntl.LOCK_EX)


def unlock_msg_db():
    with open("/www/server/panel/data/msg_box.db", mode="rb") as msg_fd:
        fcntl.flock(msg_fd.fileno(), fcntl.LOCK_UN)


def msg_db_locker(func):
    def inner_func(*args, **kwargs):
        lock_msg_db()
        res = func(*args, **kwargs)
        unlock_msg_db()
        return res

    return inner_func


def _init_msg_db():
    from db import Sql
    
    db = Sql()
    db.dbfile("msg_box")
    create_msg_sql = (
        "CREATE TABLE IF NOT EXISTS 'msg' ("
        "'id' INTEGER PRIMARY KEY AUTOINCREMENT, "
        "'sub_id' INTEGER NOT NULL DEFAULT 0, "
        "'sub_type' TEXT NOT NULL DEFAULT '', "
        "'title' TEXT NOT NULL DEFAULT '', "
        "'read' INTEGER NOT NULL DEFAULT 0, "
        "'msg_types' TEXT NOT NULL DEFAULT '[]', "
        "'source' TEXT NOT NULL DEFAULT '[]', "
        "'level' INTEGER NOT NULL DEFAULT 0, "
        "'read_time' INTEGER NOT NULL DEFAULT 0, "
        "'create_time' INTEGER NOT NULL DEFAULT (strftime('%s'))"
        ");"
    )
    res = db.execute(create_msg_sql)
    if isinstance(res, str) and res.startswith("error"):
        public.WriteLog("消息盒子", "建表msg失败: " + res)
        return
    res = db.execute("pragma journal_mode=wal")
    # public.print_log(res)


# 代替 db.py 中， 离谱的两个query函数
def msg_db_query_func(self, sql, param=()):
    # 执行SQL语句返回数据集
    self._Sql__GetConn()
    try:
        return self._Sql__DB_CONN.execute(sql, self._Sql__to_tuple(param))
    except Exception as ex:
        return "error: " + str(ex)


def get_msg_db():
    from db import Sql

    db = Sql()
    db.dbfile("msg_box")
    setattr(db, "query", types.MethodType(msg_db_query_func, db))
    return db


def msg_table():
    return get_msg_db().table("msg")


def get_msg_table(name: str):
    return get_msg_db().table(name)


class Message:
    def __init__(self):
        self.id = None
        self.title: str = ""
        self.read: bool = False
        self.msg_types: List[str] = []
        self.source: List[str] = []
        self.level: str = "info"
        self.create_time: Optional[int] = None
        self.read_time: Optional[int] = None
        self._sub = None
        self._sub_type = None
        self._sub_id = None

    @property
    def sub(self) -> Optional[dict]:
        if self._sub is not None:
            return self._sub
        if self._sub_id is None or self._sub_type is None:
            return None
        with get_msg_table(self._sub_type) as table:
            sub_info = table.where("id = ?", (self._sub_id,)).find()
        if not sub_info:
            return None
        if isinstance(sub_info, str) and sub_info.startswith("error"):
            raise ValueError(sub_info)
        sub = dict()
        for k, v in sub_info.items():
            if k in ("id",):
                sub[k] = v
                continue
            if isinstance(v, str):
                try:
                    sub[k] = json.loads(v)
                except json.JSONDecodeError:
                    sub[k] = v
            else:
                sub[k] = v

        self._sub = sub
        return self._sub

    @sub.setter
    def sub(self, sub_data: dict):
        self._sub = sub_data
        if "id" in sub_data and sub_data["id"] is not None:
            self._sub_id = sub_data["id"]
        if "self_type" in sub_data and isinstance(sub_data["self_type"], str):
            self._sub_type = sub_data["self_type"]

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
            "sub_type": self._sub_type,
            "sub": self.sub,
        }
        if not isinstance(self.sub, dict):
            res["sub"] = {
                "msg": "详细信息丢失"
            }
        else:
            res["sub"]["self_type"] = self._sub_type
        return res

    @classmethod
    def form_dict(cls, data: dict) -> Optional["Message"]:
        msg = cls()
        msg.id = data.get("id", None)
        msg.title = data.get("title", "")
        msg.read = data.get("read", False)
        msg.msg_types = data.get("msg_types", [])
        msg.source = data.get("source", [])
        msg.level = data.get("level", "unknown")
        msg.create_time = data.get("create_time", None)
        msg.read_time = data.get("read_time", None)
        msg._sub_type = data.get("sub_type", None)
        msg._sub_id = data.get("sub_id", None)

        if msg._sub_type is None:
            raise ValueError("信息详情类型不能为空")

        # 特别字段检查
        if isinstance(msg.read, int):
            msg.read = True if msg.id != 0 else False
        if isinstance(msg.level, int):
            msg.level = _int_to_level(msg.level)

        if isinstance(msg.msg_types, str):
            try:
                msg.msg_types = json.loads(msg.msg_types)
            except json.JSONDecodeError:
                msg.msg_types = []

        if isinstance(msg.source, str):
            try:
                msg.source = json.loads(msg.source)
            except json.JSONDecodeError:
                msg.source = []

        return msg

    @msg_db_locker
    def save_to_db(self) -> int:
        """
        保存信息到数据库
        没有sub时，不保存
        """
        if self._sub_type not in _ALLOWED_SUB_TYPES:
            raise ValueError("详细类型错误，{}是不支持的类型".format(self._sub_type))
        # 先处理msg主体部分：
        if not isinstance(self.sub, dict):
            raise ValueError("详细信息丢失，无法保存信息")
        now = int(datetime.now().timestamp())
        the_sub_id = self._sub_id or self.sub.get("id", None)
        data = {
            "title": self.title,
            "msg_types": json.dumps(self.msg_types) if self.msg_types is not None else '[]',
            "source": json.dumps(self.source) if self.source is not None else '[]',
            "level": _level_to_int(self.level),
            "sub_type": self._sub_type if self._sub_type is not None else "unknown",
            "sub_id": 0 if not the_sub_id else the_sub_id
        }
        # create_time, read
        if self.id is None:
            data["read"] = 0
            data["read_time"] = 0
            data["create_time"] = now

            with msg_table() as table:
                res = table.insert(data)
            if isinstance(res, str) and res.startswith("error"):
                raise ValueError(res)

            self.id = res
        else:
            data["read"] = 0 if self.read is False else 1
            data["read_time"] = now if self.read and not self.read_time else self.read_time
            if data["read_time"] is None:
                data["read_time"] = 0
            with msg_table() as table:
                res = table.where("id = ?", (self.id,)).update(data)
            if isinstance(res, str) and res.startswith("error"):
                raise ValueError(res)

        # 处理详情部分:
        if not self._sub_id and isinstance(self.sub, dict):  # 有详情信息，但是详情详情还未保存
            sub_data = self.sub.copy()
            if "self_type" in sub_data:
                sub_data.pop("self_type")
            if "id" in sub_data:
                sub_data.pop("id")

            for k, v in sub_data.items():
                if isinstance(v, (list, tuple, dict)):
                    sub_data[k] = json.dumps(v)
            sub_data["pid"] = self.id
            with get_msg_table(self._sub_type) as table:
                res = table.insert(sub_data)
            if isinstance(res, str) and res.startswith("error"):
                raise ValueError(res)

            self.sub["id"] = res
            self._sub_id = res
            with msg_table() as table:
                res = table.where("id = ?", (self.id,)).update({"sub_id": self._sub_id})

        if isinstance(self._sub_id, int) and isinstance(self.sub, dict):  # 有详情信息，且需要更新数据
            sub_data = self.sub.copy()
            if "self_type" in sub_data:
                sub_data.pop("self_type")

            sub_data["pid"] = self.id
            sub_data.pop("id")
            for k, v in sub_data.items():
                if isinstance(v, (list, tuple, dict)):
                    sub_data[k] = json.dumps(v)
            with get_msg_table(self._sub_type) as table:
                res = table.where('id = ?', (self._sub_id,)).update(sub_data)
            if isinstance(res, str) and res.startswith("error"):
                raise ValueError(res)
            with msg_table() as table:
                res = table.where("id = ?", (self.id,)).update({"sub_id": self._sub_id})
            if isinstance(res, str) and res.startswith("error"):
                raise ValueError(res)

        return self.id

    @msg_db_locker
    def delete_from_db(self):
        with get_msg_table(self._sub_type) as table:
            table.delete(self._sub_id)
        if self._sub_type == "soft_install" and (isinstance(self.sub, dict) and "file_name" in self.sub):
            if os.path.exists(self.sub["file_name"]) and not self.sub["file_name"].startswith("/tmp"):
                os.remove(self.sub["file_name"])
        with msg_table() as table:
            res = table.delete(self.id)
        self.id = None
        self._sub_type = None

    @classmethod
    @msg_db_locker
    def multi_delete(cls, id_list: List[int]) -> Optional[str]:
        """
        批量删除，返回None表示没有问题，返回str表述错误信息
        """
        with msg_table() as table:
            msgs_info = table.where("id in ({})".format(",".join(["?"] * len(id_list))),
                                    id_list).field("id,sub_type,sub_id").select()
        if isinstance(msgs_info, str) and msgs_info.startswith("error"):
            return msgs_info

        for msg_info in msgs_info:
            with get_msg_table(msg_info["sub_type"]) as table:
                sub_msg = table.where("id = ?", (msg_info["sub_id"])).find()
                table.delete(msg_info["sub_id"])
            if msg_info["sub_type"] == "soft_install":
                if sub_msg and os.path.exists(sub_msg["file_name"]) and not sub_msg["file_name"].startswith("/tmp"):
                    os.remove(sub_msg["file_name"])

            with msg_table() as table:
                table.delete(msg_info["id"])

        return None

    def view(self) -> Union[str, dict]:
        return self._sub

    @classmethod
    @msg_db_locker
    def multi_read(cls, id_list: List[int]) -> Optional[str]:
        """
        批量标为已读，返回None表示没有问题，返回str表述错误信息
        """
        with msg_table() as table:
            msgs_info = table.where("id in ({})".format(",".join(["?"] * len(id_list))),
                                    id_list).field("id,read,read_time").select()

        if isinstance(msgs_info, str) and msgs_info.startswith("error"):
            return msgs_info

        now = datetime.now().timestamp()
        id_list = [m["id"] for m in msgs_info]
        up_data = {
            "read_time": now,
            "read": 1
        }
        with msg_table() as table:
            res = table.where("id in ({})".format(",".join(["?"] * len(msgs_info))), id_list).update(up_data)
        if isinstance(res, str) and res.startswith("error"):
            return res
        return None

    @classmethod
    @msg_db_locker
    def read_all(cls):
        """
        全部已读
        """
        now = datetime.now().timestamp()
        up_data = {
            "read_time": now,
            "read": 1
        }
        with msg_table() as table:
            res = table.update(up_data)
        if isinstance(res, str) and res.startswith("error"):
            return res
        return None

    @staticmethod
    @msg_db_locker
    def delete_all():
        with get_msg_db() as db:
            tables = db.query("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            if isinstance(tables, str) and tables.startswith("error"):
                return tables

            for table in tables:
                db.execute("DELETE FROM %s" % table[0])

        logs_dir = public.get_panel_path() + "/logs/installed"
        if os.path.exists(logs_dir):
            shutil.rmtree(logs_dir)

    @classmethod
    def new(cls, title: str = '',
            msg_types: List[str] = None,
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
        if "self_type" not in sub_msg:
            raise ValueError("详细信息的类型不能为空")
        if sub_msg["self_type"] not in _ALLOWED_SUB_TYPES:
            raise ValueError("详细信息的类型不是一个可用的类型")
        msg = cls()
        msg.title = title
        msg._sub_type = sub_msg.pop("self_type")
        msg.sub = sub_msg
        msg.msg_types = msg_types
        msg.source = source
        msg.level = level

        return msg

    @classmethod
    @msg_db_locker
    def find_by_id(cls, msg_id: int) -> Optional["Message"]:
        if not isinstance(msg_id, int):
            raise ValueError("id 必须是整数字段")

        with msg_table() as m_table:
            msg_info = m_table.where("id = ?", (msg_id,)).find()
        if isinstance(msg_info, str) and msg_info.startswith("error"):
            raise ValueError(msg_info)

        if not bool(msg_info):
            return None

        return cls.form_dict(msg_info)
    


    @classmethod
    def find_by_sub_args(cls,
                         sub_name: str,
                         sub_where: Tuple[str, Union[Tuple, List]],
                         limit: Union[Tuple[int, int], int] = None
                         ) -> Optional[List["Message"]]:
        """
        where 和 sub_where 的第一项写条件， 形如 `[sub_name].id = ?`
                            第二项写参数列表， 如 [1, "22"]
            完整示例：("[sub_name].id > ? and [sub_name].name like ?", [1, "22])
        """
        db_file = '/www/server/panel/data/msg_box.db'
        if not os.path.exists(db_file):
            _init_msg_db()
        if sub_name is None and sub_where is None:
            raise ValueError("没有参数，无法进行查询")
        query_str = (
            "SELECT msg.id FROM 'msg' LEFT JOIN '{}' "
            "WHERE {}.id = msg.sub_id AND msg.sub_type = '{}' "
            "AND ({})"
        ).format(sub_name, sub_name, sub_name, sub_where[0])
        args = list(sub_where[1])
        if limit is not None:
            if isinstance(limit, int) or len(limit) == 1:
                query_str += "LIMIT 0,?"
                args.append(limit[0] if isinstance(limit, (list, tuple)) else limit)
            else:
                query_str += "LIMIT ?,?"
                args += limit[::-1]
        lock_msg_db()
        with msg_table() as table:
            info = table.query(query_str, args)
            if isinstance(info, str):
                if info.find('malformed') != -1:
                    unlock_msg_db()
                    if os.path.exists(db_file):
                        public.ExecShell('rm -f ' + db_file)
                    _init_msg_db()
                    return []
                raise ValueError("数据库错误：" + info)
            target_ids = [i[0] for i in info]
        unlock_msg_db()

        if len(target_ids) == 0:
            return None

        return [cls.find_by_id(i) for i in target_ids]

    @classmethod
    @msg_db_locker
    def query_by_sub_args(cls,
                          sub_name: str,
                          sub_where: Tuple[str, Union[Tuple, List]] = None,
                          limit: Union[Tuple[int, int], int] = None,
                          order_by: str = None,
                          ) -> List["Message"]:
        """
        where 和 sub_where 的第一项写条件， 形如 `[sub_name].id = ?`
                            第二项写参数列表， 如 [1, "22"]
            完整示例：("[sub_name].id > ? and [sub_name].name like ?", [1, "22])
        """
        db_file = '/www/server/panel/data/msg_box.db'
        if not os.path.exists(db_file):
            _init_msg_db()
        if sub_name is None:
            raise ValueError("没有参数，无法进行查询")
        if sub_where is not None:
            query_str = (
                "SELECT * FROM 'msg' LEFT JOIN '{}' "
                "WHERE {}.id = msg.sub_id AND msg.sub_type = '{}' "
                "AND ({})"
            ).format(sub_name, sub_name, sub_name, sub_where[0])
            args = list(sub_where[1])
        else:
            query_str = (
                "SELECT * FROM 'msg' LEFT JOIN '{}' "
                "WHERE {}.id = msg.sub_id AND msg.sub_type = '{}'"
            ).format(sub_name, sub_name, sub_name)
            args = []

        if isinstance(order_by, str):
            query_str += " ORDER BY ?"
            args.append(order_by)

        if limit is not None:
            if isinstance(limit, (list, tuple)) and len(limit) == 2:
                query_str += " LIMIT ?,?"
                args += limit[::-1]
            else:
                query_str += " LIMIT 0,?"
                args.append(limit[0] if isinstance(limit, (list, tuple)) else limit)

        with msg_table() as table:
            result = table.query(query_str, args)
            if isinstance(result, str):
                if result.find('malformed') != -1:
                    unlock_msg_db()
                    if os.path.exists(db_file):
                        public.ExecShell('rm -f ' + db_file)
                    _init_msg_db()
                    return []
                raise ValueError("数据库错误：" + result)
            table_headers = [i[0] for i in result.description]
            msg_h, sub_h = table_headers[:10], table_headers[10:]
            res = []
            for i in result.fetchall():
                msg_data = dict(zip(msg_h, i[:10]))
                sub_data = dict(zip(sub_h, i[10:]))
                tmp_msg = cls.form_dict(msg_data)
                tmp_msg.sub = sub_data
                res.append(tmp_msg)

        return res


def collect_message(title: str = '',
                    msg_types: List[str] = None,
                    source: List[str] = None,
                    sub_msg: dict = None,
                    level: str = "info") -> Union["Message", str]:
    """
    储存一条信息：
    title：信息标题
    msg_types：信息类型
    sub_msg: 信息详情
        包含一个特殊key： self_type, 表明详细信息的类型

    返回：当操作失败时，返回操作失败的信息，成功时返回信息， type:Message
    """
    return ''
    # try:
    #     msg = Message.new(title, msg_types, source, sub_msg, level)
    #     msg.save_to_db()
    # except ValueError as e:
    #     return str(e)
    # return msg
