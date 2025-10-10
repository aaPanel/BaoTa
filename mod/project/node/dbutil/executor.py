import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Tuple, Any, Union, Type, Generic, TypeVar, TextIO
import sqlite3
import json

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public
import db

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")


@dataclass
class Script:
    """对应scripts表"""
    name: str
    script_type: str
    content: str
    id: Optional[int] = None
    description: Optional[str] = None
    group_id: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @staticmethod
    def check(data: Dict[str, Any]) -> str:
        if "script_type" not in data or not data["script_type"]:
            return "脚本类型不能为空"
        if not data["script_type"] in ["python", "shell"]:
            return "脚本类型错误, 请选择python或shell"
        if "content" not in data or not data["content"]:
            return "脚本内容不能为空"
        if "name" not in data or not data["name"]:
            return "脚本名称不能为空"
        return ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Script':
        """从字典创建Script实例"""
        return cls(
            id=int(data['id']) if data.get('id', None) else None,
            name=str(data['name']),
            script_type=str(data['script_type']),
            content=str(data['content']),
            description=str(data['description']) if data.get('description', None) else None,
            group_id=int(data['group_id']) if data.get('group_id', None) else 0,
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at', None) else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at', None) else None
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'script_type': self.script_type,
            'content': self.content,
            'description': self.description,
            'group_id': self.group_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class ScriptGroup:
    """对应script_groups表"""
    name: str
    id: Optional[int] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    @staticmethod
    def check(data: Dict[str, Any]) -> str:
        if "name" not in data or not data["name"]:
            return "脚本分组名称不能为空"
        return ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScriptGroup':
        """从字典创建ScriptGroup实例"""
        return cls(
            id=int(data['id']) if data.get('id', None) else None,
            name=str(data['name']),
            description=str(data['description']) if data.get('description', None) else None,
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at', None) else None
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class ExecutorTask:
    """对应executor_tasks表"""
    script_id: int
    script_content: str
    script_type: str
    server_ids: str = ""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    _elogs: Optional[List["ExecutorLog"]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutorTask':
        """从字典创建ExecutorTask实例"""
        return cls(
            id=int(data['id']) if data.get('id', None) else None,
            script_id=int(data['script_id']),
            script_content=str(data['script_content']),
            script_type=str(data['script_type']),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at', None) else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at', None) else None
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'script_id': self.script_id,
            'server_ids': self.server_ids,
            'script_content': self.script_content,
            'script_type': self.script_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @property
    def elogs(self) -> List["ExecutorLog"]:
        if self._elogs is None:
            return []
        return self._elogs

    @elogs.setter
    def elogs(self, elogs: List["ExecutorLog"]):
        self._elogs = elogs


_EXECUTOR_LOG_DIR = public.get_panel_path() + "/logs/executor_log/"
try:
    if not os.path.exists(_EXECUTOR_LOG_DIR):
        os.makedirs(_EXECUTOR_LOG_DIR)
except:
    pass


@dataclass
class ExecutorLog:
    """对应executor_logs表"""
    executor_task_id: int
    server_id: int
    ssh_host: str
    id: Optional[int] = None
    status: int = 0  # 0:运行中 1:成功 2:失败 3:异常
    log_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    _log_fp: Optional[TextIO] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutorLog':
        """从字典创建ExecutorLog实例"""
        return cls(
            id=int(data['id']) if data.get('id', None) else None,
            executor_task_id=int(data['executor_task_id']),
            server_id=int(data['server_id']),
            ssh_host=str(data['ssh_host']),
            status=int(data['status']) if data.get('status', 0) else 0,
            log_name=str(data['log_name']) if data.get('log_name', None) else None,
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at', None) else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at', None) else None
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'executor_task_id': self.executor_task_id,
            'server_id': self.server_id,
            'ssh_host': self.ssh_host,
            'status': self.status,
            'log_name': self.log_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @property
    def log_file(self):
        return os.path.join(_EXECUTOR_LOG_DIR, self.log_name)

    @property
    def log_fp(self):
        if self._log_fp is None:
            self._log_fp = open(self.log_file, "w+")
        return self._log_fp

    def create_log(self):
        public.writeFile(self.log_file, "")

    def remove_log(self):
        if os.path.exists(self.log_file):
            os.remove(self.log_file)

    def get_log(self):
        return public.readFile(self.log_file)

    def write_log(self, log_data: str, is_end_log=False):
        self.log_fp.write(log_data)
        self.log_fp.flush()
        if is_end_log:
            self.log_fp.close()
            self._log_fp = None


_TableType = TypeVar("_TableType", bound=Union[Script, ScriptGroup, ExecutorTask, ExecutorLog])


class _Table(Generic[_TableType]):
    """数据库表"""
    table_name: str = ""
    data_cls: Type[_TableType]

    def __init__(self, db_obj: db.Sql):
        self._db = db_obj

    # 当仅传递一个数据时，返回插入数的 id或错误信息; 当传递多个数据时，返回插入的行数或错误信息
    def create(self,
               data: Union[_TableType, List[_TableType]]) -> Union[int, str]:
        """创建数据"""
        if not isinstance(data, list):
            data = [data]

        if not len(data):
            raise ValueError("数据不能为空")
        if not isinstance(data[0], self.data_cls):
            raise ValueError("数据类型错误")

        now = datetime.now().isoformat()

        def fileter_data(item):
            item_dict = item.to_dict()
            if "id" in item_dict:
                item_dict.pop("id")
            if "created_at" in item_dict and item_dict["created_at"] is None:
                item_dict["created_at"] = now
            if "updated_at" in item_dict and item_dict["updated_at"] is None:
                item_dict["updated_at"] = now
            return item_dict

        data_list = list(map(fileter_data, data))
        if len(data_list) == 1:
            try:
                res = self._db.table(self.table_name).insert(data_list[0])
                if isinstance(res, int):
                    return res
                return str(res)
            except Exception as e:
                return str(e)
        try:
            res = self._db.table(self.table_name).batch_insert(data_list)
            if isinstance(res, (int, bool)):
                return len(data)
            return str(res)
        except Exception as e:
            return str(e)

    def update(self, data: _TableType) -> str:
        """更新数据"""
        if not isinstance(data, self.data_cls):
            raise ValueError("数据类型错误")
        data_dict = data.to_dict()
        data_dict.pop('created_at', None)
        if "updated_at" in data_dict:
            data_dict["updated_at"] = datetime.now().isoformat()
        if "id" not in data_dict:
            raise ValueError("数据id不能为空")
        try:
            self._db.table(self.table_name).where("id=?", (data_dict["id"],)).update(data_dict)
        except Exception as e:
            return str(e)
        return ""

    def get_byid(self, data_id: int) -> Optional[_TableType]:
        """根据id获取数据"""
        try:
            result = self._db.table(self.table_name).where("id=?", (data_id,)).find()
        except Exception as e:
            return None
        if not result:
            return None
        return self.data_cls.from_dict(result)

    def delete(self, data_id: Union[int, List[int]]):
        """删除数据"""
        if isinstance(data_id, list):
            data_id = [int(item) for item in data_id]
        elif isinstance(data_id, int):
            data_id = [int(data_id)]
        else:
            return "数据id类型错误"
        try:
            self._db.table(self.table_name).where(
                "id in ({})".format(",".join(["?"] * len(data_id))), (*data_id,)
            ).delete()
            return ""
        except Exception as e:
            return str(e)

    def query(self, *args) -> List[_TableType]:
        """查询数据"""
        try:
            result = self._db.table(self.table_name).where(*args).select()
        except Exception as e:
            return []
        if not result:
            return []
        return [self.data_cls.from_dict(item) for item in result]

    def query_page(self, *args, page_num: int = 1, limit: int = 10) -> List[_TableType]:
        """查询数据, 支持分页"""
        try:
            offset = limit * (page_num - 1)
            result = self._db.table(self.table_name).where(*args).limit(limit, offset).order("id DESC").select()
        except Exception as e:
            public.print_error()
            return []
        if not result:
            return []
        return [self.data_cls.from_dict(item) for item in result]

    def count(self, *args) -> int:
        """查询数据数量"""
        try:
            result = self._db.table(self.table_name).where(*args).count()
        except Exception as e:
            return 0
        return result

    def find(self, *args) -> Optional[_TableType]:
        """查询单条数据"""
        try:
            result = self._db.table(self.table_name).where(*args).find()
        except Exception as e:
            return None
        if not result:
            return None
        return self.data_cls.from_dict(result)


class _ScriptTable(_Table[Script]):
    """脚本表"""
    table_name = "scripts"
    data_cls = Script

    def set_group_id(self, group_id: int, *where_args) -> str:
        """设置脚本组"""
        try:
            self._db.table(self.table_name).where(where_args).update({"group_id": group_id})
        except Exception as e:
            return str(e)
        return ""


class _ScriptGroupTable(_Table[ScriptGroup]):
    """脚本组表"""
    table_name = "script_groups"
    data_cls = ScriptGroup
    default_group = ScriptGroup(
        id=0,
        name="默认",
        description="默认分组，未设置时使用该分组",
        created_at=datetime.now(),
    )

    def all_group(self) -> List[ScriptGroup]:
        """获取所有脚本组"""
        try:
            result = self._db.table(self.table_name).select()
        except Exception as e:
            return []
        if not result:
            return []
        return [self.default_group] + [self.data_cls.from_dict(item) for item in result]


class _ExecutorTaskTable(_Table[ExecutorTask]):
    """执行任务表"""
    table_name = "executor_tasks"
    data_cls = ExecutorTask

    def query_tasks(self,
                    page=1, size=10, node_id: int = None, script_type: str = None, search: str = None
                    ) -> Tuple[int, List[ExecutorTask]]:
        """查询任务"""
        where_args, parms = [], []
        if script_type and script_type != "all":
            where_args.append("script_type=?")
            parms.append(script_type)
        if search:
            search_str = "script_content like ?"
            parms.append("%{}%".format(search))

            stable = _ScriptTable(self._db)
            data = stable.query("name like ? or description like ?", ("%{}%".format(search), "%{}%".format(search)))
            if data:
                search_str += " or script_id in ({})".format(",".join(["?"] * len(data)))
                where_args.append("(" + search_str + ")")
                parms.append(tuple([item.id for item in data]))
            else:
                where_args.append(search_str)

        if node_id:
            where_args.append("server_ids like ?")
            parms.append("%|{}%".format(node_id))


        public.print_log("查询条件: {}".format(" AND ".join(where_args)), parms)
        count = self.count(
            " AND ".join(where_args),
            (*parms, )
        )

        return count, self.query_page(
            " AND ".join(where_args),
            (*parms, ),
            page_num=page,
            limit=size
        )


class _ExecutorLogTable(_Table[ExecutorLog]):
    """执行日志表"""
    table_name = "executor_logs"
    data_cls = ExecutorLog


class ExecutorDB:
    _DB_FILE = public.get_panel_path() + "/data/db/executor.db"
    _DB_INIT_FILE = os.path.dirname(__file__) + "/executor.sql"

    def __init__(self):
        sql = db.Sql()
        sql._Sql__DB_FILE = self._DB_FILE
        self.db = sql
        self.Script = _ScriptTable(self.db)
        self.ScriptGroup = _ScriptGroupTable(self.db)
        self.ExecutorTask = _ExecutorTaskTable(self.db)
        self.ExecutorLog = _ExecutorLogTable(self.db)

    def init_db(self):
        sql_data = public.readFile(self._DB_INIT_FILE)
        if not os.path.exists(self._DB_FILE) or os.path.getsize(self._DB_FILE) == 0:
            public.writeFile(self._DB_FILE, "")
            import sqlite3
            conn = sqlite3.connect(self._DB_FILE)
            cursor = conn.cursor()
            cursor.executescript(sql_data)
            conn.commit()
            conn.close()

    def close(self):
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_trackback):
        self.close()
