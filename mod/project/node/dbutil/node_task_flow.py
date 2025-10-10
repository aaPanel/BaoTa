import copy
import os
import sys
import time
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Tuple, Any, Union, Type, Generic, TypeVar, TextIO
import sqlite3

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public
import db

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")


def random_name() -> str:
    return uuid.uuid4().hex[::4]


@dataclass
class Script:
    """对应scripts表"""
    name: str
    script_type: str
    content: str
    id: Optional[int] = None
    description: Optional[str] = None
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
            created_at=datetime.fromtimestamp(data['created_at']) if data.get('created_at', None) else None,
            updated_at=datetime.fromtimestamp(data['updated_at']) if data.get('updated_at', None) else None
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'script_type': self.script_type,
            'content': self.content,
            'description': self.description,
            'created_at': self.created_at.timestamp() if self.created_at else None,
            'updated_at': self.updated_at.timestamp() if self.updated_at else None
        }


@dataclass
class Flow:
    server_ids: str  # 存储服务器ID列表，原始TEXT类型
    step_count: int
    strategy: Dict[str, Any]  # JSON字段，存储策略
    status: str  # 状态 waiting, running, complete, error
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    _steps: Optional[List[Union["CommandTask", "TransferTask"]]] = None

    @staticmethod
    def check(data: Dict[str, Any]) -> str:
        if "strategy" not in data:
            data["strategy"] = {}
        else:
            strategy = data["strategy"]
            if isinstance(strategy, str):
                try:
                    strategy = json.loads(strategy)
                except json.JSONDecodeError:
                    return "策略字段格式错误"
            if not isinstance(strategy, dict):
                return "策略字段格式错误"
        return ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Flow':
        return cls(
            id=int(data['id']) if data.get('id') is not None else None,
            server_ids=str(data['server_ids']),
            step_count=int(data['step_count']),
            strategy=data['strategy'] if data.get('strategy') else {},
            status=str(data['status']),
            created_at=datetime.fromtimestamp(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromtimestamp(data['updated_at']) if data.get('updated_at') else None
        )

    def to_dict(self) -> Dict[str, Any]:
        now = int(time.time())
        return {
            'id': self.id,
            'server_ids': self.server_ids,
            'step_count': self.step_count,
            'strategy': self.strategy,
            'status': self.status,
            'created_at': int(self.created_at.timestamp()) if self.created_at else now,
            'updated_at': int(self.updated_at.timestamp()) if self.updated_at else now
        }

    @property
    def steps(self) -> List[Union["CommandTask", "TransferTask"]]:
        if self._steps is None:
            raise RuntimeError("请先设置steps内容")
        return self._steps

    @steps.setter
    def steps(self, steps: List[Union["CommandTask", "TransferTask"]]) -> None:
        self._steps = steps


@dataclass
class CommandTask:
    flow_id: int
    step_index: int
    script_id: int
    script_content: str
    script_type: str
    status: int = 0  # 0: 等待中, 1: 进行中, 2: 成功, 3: 失败
    name: str = ""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    _elogs: Optional[List["CommandLog"]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommandTask':
        return cls(
            id=int(data['id']) if data.get('id') is not None else None,
            name=str(data.get('name', '')),
            flow_id=int(data['flow_id']),
            step_index=int(data['step_index']),
            script_id=int(data['script_id']),
            script_content=str(data['script_content']),
            script_type=str(data['script_type']),
            status=int(data.get('status', 0)),
            created_at=datetime.fromtimestamp(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromtimestamp(data['updated_at']) if data.get('updated_at') else None
        )

    def to_dict(self) -> Dict[str, Any]:
        now = int(time.time())
        return {
            'id': self.id,
            'flow_id': self.flow_id,
            'name': self.name,
            'step_index': self.step_index,
            'script_id': self.script_id,
            'script_content': self.script_content,
            'script_type': self.script_type,
            'status': self.status,
            'created_at': int(self.created_at.timestamp()) if self.created_at else now,
            'updated_at': int(self.updated_at.timestamp()) if self.updated_at else now
        }

    def to_show_data(self) -> Dict[str, Any]:
        tmp = self.to_dict()
        tmp["task_type"] = "command"
        return tmp

    @property
    def elogs(self) -> List["CommandLog"]:
        if self._elogs is None:
            return []
        return self._elogs

    @elogs.setter
    def elogs(self, elogs: List["CommandLog"]):
        self._elogs = elogs


_EXECUTOR_LOG_DIR = public.get_panel_path() + "/logs/executor_log/"
try:
    if not os.path.exists(_EXECUTOR_LOG_DIR):
        os.makedirs(_EXECUTOR_LOG_DIR)
except:
    pass


@dataclass
class CommandLog:
    command_task_id: int
    server_id: int
    ssh_host: str
    id: Optional[int] = None
    status: int = 0  # 0: 等待, 1: 运作中, 2: 成功, 3: 失败, 4: 异常
    log_name: Optional[str] = None
    _log_fp: Optional[TextIO] = None
    _log_idx: int = -1

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommandLog':
        return cls(
            id=int(data['id']) if data.get('id') is not None else None,
            command_task_id=int(data['command_task_id']),
            server_id=int(data['server_id']),
            ssh_host=str(data['ssh_host']),
            status=int(data['status']) if data.get('status') is not None else 0,
            log_name=str(data['log_name']) if data.get('log_name') is not None else None,
        )

    def to_dict(self) -> Dict[str, Any]:
        now = int(time.time())
        return {
            'id': self.id,
            'command_task_id': self.command_task_id,
            'server_id': self.server_id,
            'ssh_host': self.ssh_host,
            'status': self.status,
            'log_name': self.log_name
        }

    def to_show_data(self, only_error=True):
        tmp = self.to_dict()
        if self.status in (3, 4):
            tmp["message"] = self.get_log()
        else:
            tmp["message"] = "" if only_error else self.get_log()

        if self._log_idx > -1:
            tmp["log_idx"] = self.log_idx

        return tmp

    @property
    def log_file(self):
        return os.path.join(_EXECUTOR_LOG_DIR, self.log_name)

    @property
    def log_fp(self):
        if self._log_fp is None:
            self._log_fp = open(self.log_file, "w+")
        return self._log_fp

    @property
    def log_idx(self):
        return self._log_idx

    @log_idx.setter
    def log_idx(self, log_idx: int):
        self._log_idx = log_idx

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


@dataclass
class TransferTask:
    flow_id: int
    step_index: int
    src_node: Dict[str, Any]
    src_node_task_id: int
    dst_nodes: List[Dict[str, Any]]
    name: str = ""
    message: str = ""
    path_list: List[Dict[str, Any]] = field(default_factory=lambda: [])
    status: int = 0  # 0: 等待中, 1: 进行中, 2: 成功, 3: 失败
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TransferTask':
        return cls(
            id=int(data['id']) if data.get('id') is not None else None,
            flow_id=int(data['flow_id']),
            name=str(data.get('name', '')),
            message=str(data.get('message', '')),
            step_index=int(data['step_index']),
            src_node=data['src_node'] if data.get('src_node') else {},
            src_node_task_id=int(data['src_node_task_id']),
            dst_nodes=data['dst_nodes'] if data.get('dst_nodes') else {},
            path_list=data['path_list'] if data.get('path_list') else [],
            status=int(data['status']) if data.get('status') is not None else 0,
            created_at=datetime.fromtimestamp(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromtimestamp(data['updated_at']) if data.get('updated_at') else None
        )

    def to_dict(self) -> Dict[str, Any]:
        now = int(time.time())
        return {
            'id': self.id,
            'flow_id': self.flow_id,
            'step_index': self.step_index,
            'name': self.name,
            'src_node': copy.deepcopy(self.src_node),
            'src_node_task_id': self.src_node_task_id,
            'dst_nodes': copy.deepcopy(self.dst_nodes),
            'path_list': self.path_list,
            'status': self.status,
            'message': self.message,
            'created_at': int(self.created_at.timestamp()) if self.created_at else now,
            'updated_at': int(self.updated_at.timestamp()) if self.updated_at else now
        }

    def to_show_data(self):
        tmp = self.to_dict()
        for key in ("api_key", "app_key", "ssh_conf"):
            if key in tmp["src_node"]:
                tmp["src_node"].pop(key)
            for node in tmp["dst_nodes"]:
                if key in node:
                    node.pop(key)
        tmp["task_type"] = "file"
        return tmp


@dataclass
class TransferFile:
    flow_id: int
    transfer_task_id: int
    src_file: str
    dst_file: str
    file_size: int
    is_dir: int = 0  # 0: 文件, 1: 目录
    id: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TransferFile':
        return cls(
            id=int(data['id']) if data.get('id') is not None else None,
            flow_id=int(data['flow_id']),
            transfer_task_id=int(data['transfer_task_id']),
            src_file=str(data['src_file']),
            dst_file=str(data['dst_file']),
            file_size=int(data['file_size']),
            is_dir=int(data['is_dir']) if data.get('is_dir') is not None else 0
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'flow_id': self.flow_id,
            'transfer_task_id': self.transfer_task_id,
            'src_file': self.src_file,
            'dst_file': self.dst_file,
            'file_size': self.file_size,
            'is_dir': self.is_dir
        }


@dataclass
class TransferLog:
    flow_id: int
    transfer_task_id: int
    transfer_file_id: int
    dst_node_idx: int
    status: int = 0  # 0: 等待中, 1: 进行中, 2: 成功, 3: 失败, 4: 跳过
    progress: int = 0
    message: str = ""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    _tf: Optional[TransferFile] = None
    _log_idx: int = -1

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TransferLog':
        return cls(
            id=int(data['id']) if data.get('id') is not None else None,
            flow_id=int(data['flow_id']),
            transfer_task_id=int(data['transfer_task_id']),
            transfer_file_id=int(data['transfer_file_id']),
            dst_node_idx=int(data['dst_node_idx']),
            status=int(data['status']) if data.get('status') is not None else 0,
            progress=int(data['progress']) if data.get('progress') is not None else 0,
            message=str(data['message']) if data.get('message') is not None else "",
            created_at=datetime.fromtimestamp(data['created_at']) if data.get('created_at') else None,
            started_at=datetime.fromtimestamp(data['started_at']) if data.get('started_at') else None,
            completed_at=datetime.fromtimestamp(data['completed_at']) if data.get('completed_at') else None
        )

    def to_dict(self) -> Dict[str, Any]:
        now = int(time.time())
        return {
            'id': self.id,
            'flow_id': self.flow_id,
            'transfer_task_id': self.transfer_task_id,
            'transfer_file_id': self.transfer_file_id,
            'dst_node_idx': self.dst_node_idx,
            'status': self.status,
            'progress': self.progress,
            'message': self.message,
            'created_at': int(self.created_at.timestamp()) if self.created_at else now,
            'started_at': int(self.started_at.timestamp()) if self.started_at else None,
            'completed_at': int(self.completed_at.timestamp()) if self.completed_at else None
        }

    @property
    def tf(self) -> TransferFile:
        if not self._tf:
            raise RuntimeError("tf is not set")
        return self._tf

    @tf.setter
    def tf(self, v: TransferFile):
        self._tf = v

    def to_show_data(self) -> Dict[str, Any]:
        ret = self.to_dict()
        if self._tf:
            ret.update(self._tf.to_dict())
        if self._log_idx > -1:
            ret["log_idx"] = self.log_idx
        return ret

    @property
    def log_idx(self):
        return self._log_idx

    @log_idx.setter
    def log_idx(self, log_idx: int):
        self._log_idx = log_idx


_TableType = TypeVar(
    "_TableType",
    bound=Union[Script, Flow, CommandTask, CommandLog, TransferTask, TransferFile, TransferLog]
)


class _Table(Generic[_TableType]):
    """数据库表"""
    table_name: str = ""
    data_cls: Type[_TableType]
    json_field_names: Tuple[str, ...] = tuple()

    def __init__(self, db_obj: db.Sql):
        self._db = db_obj

    def _deserialize(self, row: dict):
        for k, v in row.items():
            if k in self.json_field_names and isinstance(v, str):
                row[k] = json.loads(v)
        return self.data_cls.from_dict(row)

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

        now = int(time.time())

        def fileter_data(item):
            item_dict = item.to_dict()
            if "id" in item_dict:
                item_dict.pop("id")
            if "created_at" in item_dict and item_dict["created_at"] is None:
                item_dict["created_at"] = now
            if "updated_at" in item_dict and item_dict["updated_at"] is None:
                item_dict["updated_at"] = now
            for fj_n in self.json_field_names:
                if fj_n in item_dict and item_dict[fj_n] is not None and not isinstance(item_dict[fj_n], str):
                    item_dict[fj_n] = json.dumps(item_dict[fj_n])
            return item_dict

        data_list = list(map(fileter_data, data))
        if len(data_list) == 1:
            try:
                public.print_log(data_list)
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
            data_dict["updated_at"] = datetime.now().timestamp()
        if "id" not in data_dict:
            raise ValueError("数据id不能为空")
        for fj_n in self.json_field_names:
            if fj_n in data_dict and data_dict[fj_n] is not None and not isinstance(data_dict[fj_n], str):
                data_dict[fj_n] = json.dumps(data_dict[fj_n])
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
        return self._deserialize(result)

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
            if args:
                result = self._db.table(self.table_name).where(*args).select()
            else:
                result = self._db.table(self.table_name).select()
        except Exception as e:
            return []
        if not result:
            return []
        return [self._deserialize(item) for item in result]

    def query_page(self, *args, page_num: int = 1, limit: int = 10) -> List[_TableType]:
        """查询数据, 支持分页"""
        try:
            offset = limit * (page_num - 1)
            if not args:
                ret = self._db.table(self.table_name).limit(limit, offset).order("id DESC").select()
            else:
                ret = self._db.table(self.table_name).where(*args).limit(limit, offset).order("id DESC").select()
        except Exception as e:
            public.print_error()
            return []
        if not ret:
            return []
        return [self._deserialize(item) for item in ret]

    def count(self, *args) -> int:
        """查询数据数量"""
        try:
            if args:
                result = self._db.table(self.table_name).where(*args).count()
            else:
                result = self._db.table(self.table_name).count()
        except Exception as e:
            return 0
        return result

    def find(self, *args, order_by: str = None) -> Optional[_TableType]:
        """查询单条数据"""
        try:
            if order_by:
                result = self._db.table(self.table_name).where(*args).order(order_by).find()
            else:
                result = self._db.table(self.table_name).where(*args).find()
        except Exception as e:
            return None
        if not result:
            return None
        return self._deserialize(result)

    def bath_update(self, data: List[_TableType], update_fields: List[str]) -> Union[str, int]:
        """批量更新数据"""
        if not data or not update_fields:
            return "参数错误"
        parms = []
        real_update_fields = list(update_fields).copy()
        real_update_fields.append("id")
        for d in data:
            rows = []
            for f_name in real_update_fields:
                tmp = getattr(d, f_name)
                if isinstance(tmp, (list, dict)):
                    tmp = json.dumps(tmp)
                elif isinstance(tmp, (datetime, date)):
                    tmp = tmp.timestamp()
                rows.append(tmp)
            parms.append(tuple(rows))

        sql_str = "UPDATE {} SET {} WHERE id = ?".format(
            self.table_name,
            ",".join(["{}=?".format(f_name) for f_name in update_fields])
        )

        res = self._db.executemany(sql_str, parms)
        if isinstance(res, int):
            return res
        return str(res)

    def delete_where(self, where_str: str, parms: List[Any]) -> str:
        try:
            self._db.table(self.table_name).where(where_str, parms).delete()
            return ""
        except Exception as e:
            return str(e)


class _ScriptTable(_Table[Script]):
    """脚本表"""
    table_name = "scripts"
    data_cls = Script


class _FlowTable(_Table[Flow]):
    """任务流表"""
    table_name = "flows"
    data_cls = Flow
    json_field_names = ("strategy",)

    def last(self, order_by: str = "id DESC") -> Optional[Flow]:
        try:
            result = self._db.table(self.table_name).order(order_by).find()
            if not result:
                return None
        except Exception as e:
            return None
        return self._deserialize(result)


class _CommandTaskTable(_Table[CommandTask]):
    """命令任务表"""
    table_name = "command_tasks"
    data_cls = CommandTask

    def query_tasks(self,
                    page=1, size=10, script_type: str = None, search: str = None
                    ) -> Tuple[int, List[CommandTask]]:
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

        public.print_log("查询条件: {}".format(" AND ".join(where_args)), parms)
        count = self.count(
            " AND ".join(where_args),
            (*parms,)
        )

        return count, self.query_page(
            " AND ".join(where_args),
            (*parms,),
            page_num=page,
            limit=size
        )


class _CommandLogTable(_Table[CommandLog]):
    """命令日志表"""
    table_name = "command_logs"
    data_cls = CommandLog


class _TransferTaskTable(_Table[TransferTask]):
    """文件传输任务表"""
    table_name = "transfer_tasks"
    data_cls = TransferTask
    json_field_names = ("src_node", "dst_nodes", "path_list")


class _TransferFileTable(_Table[TransferFile]):
    """文件传输文件表"""
    table_name = "transfer_files"
    data_cls = TransferFile


class _TransferLogTable(_Table[TransferLog]):
    """文件传输日志表"""
    table_name = "transfer_logs"
    data_cls = TransferLog


class TaskFlowsDB(object):
    _DB_FILE = public.get_panel_path() + "/data/db/node_task_flow.db"
    _DB_INIT_FILE = os.path.dirname(__file__) + "/node_task_flow.sql"

    def __init__(self):
        sql = db.Sql()
        sql._Sql__DB_FILE = self._DB_FILE
        self.db = sql
        self.Script = _ScriptTable(self.db)
        self.Flow = _FlowTable(self.db)
        self.CommandTask = _CommandTaskTable(self.db)
        self.CommandLog = _CommandLogTable(self.db)
        self.TransferTask = _TransferTaskTable(self.db)
        self.TransferFile = _TransferFileTable(self.db)
        self.TransferLog = _TransferLogTable(self.db)

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

    def create_flow(
            self, used_nodes: List[Dict], target_nodes: List[Dict],
            strategy: dict, flow_data: List[dict]) -> Tuple[Optional[Flow], str]:
        """创建任务流"""
        f = Flow(
            server_ids="|{}|".format("|".join([str(item["id"]) for item in target_nodes])),
            step_count=len(flow_data),
            strategy=strategy,
            status="waiting"
        )
        f.id = self.Flow.create(f)
        if not isinstance(f.id, int):
            return None, "创建任务失败:{}".format(f.id)
        step_index = 1
        steps = []

        def clear():
            self.Flow.delete(f.id)
            for step in steps:
                if isinstance(step, CommandTask):
                    self.CommandTask.delete(step.id)
                elif isinstance(step, TransferTask):
                    self.TransferTask.delete(step.id)

        for task_data in flow_data:
            if task_data["task_type"] == "command":
                cmd_task, msg = self.create_cmd_task(f.id, step_index, task_data, target_nodes)
                if not cmd_task:
                    clear()
                    return None, msg
                steps.append(cmd_task)
            elif task_data["task_type"] == "file":
                transfer_task, msg = self.create_transfer_task(f.id, step_index, task_data, target_nodes, used_nodes)
                if not transfer_task:
                    clear()
                    return None, msg
                steps.append(transfer_task)
            step_index += 1

        return f, ""

    def create_cmd_task(self,
                        flow_id: int, step_index: int, task_data: dict,
                        nodes: List[Dict]) -> Tuple[Optional[CommandTask], str]:

        script_id = task_data.get('script_id', 0)
        script_content = task_data.get('script_content', "").strip()
        script_type = task_data.get('script_type', "").strip()
        name = task_data.get('name', random_name())
        if script_id:
            s = self.Script.get_byid(script_id)
            if not s:
                return None, "脚本不存在"
            script_content = s.content
            script_type = s.script_type
        elif script_content:
            if not script_type in ("python", "shell"):
                return None, "脚本类型错误"
        else:
            return None, "未选择脚本"

        cmd_task = CommandTask(
            flow_id=flow_id,
            step_index=step_index,
            script_id=script_id,
            name=name,
            script_content=script_content,
            script_type=script_type,
        )
        task_id = self.CommandTask.create(cmd_task)
        if not isinstance(task_id, int):
            return None, str(task_id)
        cmd_task.id = task_id
        time_now = time.time()
        md5_str = public.md5(script_content)[::2]
        cmd_logs = [
            CommandLog(
                command_task_id=task_id,
                server_id=node["id"],
                ssh_host=node["ssh_conf"]["host"],
                log_name="{}_{}_{}.log".format(md5_str, time_now, node['remarks'])
            )
            for node in nodes
        ]
        res = self.CommandLog.create(cmd_logs)
        if not isinstance(res, int):
            self.CommandTask.delete(task_id)
            return None, str(res)
        cmd_task.elogs = cmd_logs
        return cmd_task, ""

    def create_transfer_task(
            self, flow_id: int, step_index: int, task_data: dict,
            nodes: List[Dict], used_nodes: List[Dict]) -> Tuple[Optional[TransferTask], str]:

        src_node_id = task_data.get('src_node_id', 0)
        for node in used_nodes:
            if node["id"] == src_node_id:
                src_node = node
                break
        else:
            return None, "源节点不存在"

        path_list = task_data.get('path_list', [])
        for p in path_list:
            if "path" not in p or "dst_path" not in p or "is_dir" not in p:
                return None, "文件分发规则错误"
        if not path_list:
            return None, "请选择文件"

        dst_nodes = [
            {
                "name": node["remarks"], "address": node["address"],
                "api_key": node["api_key"], "app_key": node["app_key"],
                "ssh_conf": node["ssh_conf"], "lpver": node["lpver"]
            }
            for node in nodes if node["id"] != src_node_id
        ]

        tt = TransferTask(
            name=task_data.get('name', random_name()),
            flow_id=flow_id,
            step_index=step_index,
            src_node={"name": "local"},
            src_node_task_id=0,
            dst_nodes=dst_nodes,
            path_list=task_data.get('path_list', []),
        )

        if not (src_node["app_key"] == "local" and src_node["api_key"] == "local"):
            from mod.project.node.nodeutil import ServerNode
            srv = ServerNode(src_node["address"], src_node["api_key"], src_node["app_key"])
            res = srv.node_create_transfer_task(tt.to_dict())
            if "task_id" in res.get("data", {}):
                tt.src_node_task_id = res["data"]["task_id"]
                tt.src_node = {
                    "name": src_node["remarks"], "address": src_node["address"],
                    "api_key": src_node["api_key"], "app_key": src_node["app_key"],
                    "lpver": src_node["lpver"]
                }

        task_id = self.TransferTask.create(tt)
        if not isinstance(task_id, int):
            return None, str(task_id)

        tt.id = task_id
        return tt, ""

    def history_transferfile_task(self, file_id: int, only_error: bool = True) -> Dict:
        if only_error:
            log_list= self.TransferLog.query("transfer_task_id = ? and status = ?", (file_id, 3))
            files_id_list = [i.transfer_file_id for i in log_list]
            files = self.TransferFile.query("transfer_task_id = ? and id in ({})".format(
                ",".join([str(i) for i in files_id_list])
            ), (file_id,))
            fils_map = {i.id: i for i in files}
            error_num = len(log_list)
        else:
            log_list = self.TransferLog.query("transfer_task_id = ?", (file_id,))
            files = self.TransferFile.query("transfer_task_id = ?", (file_id,))
            print( log_list,  files, flush=True)
            fils_map = {i.id: i for i in files}
            error_num = len([i for i in log_list if i.status == 3])
        for i in log_list:
            i.tf = fils_map[i.transfer_file_id]

        count = self.TransferLog.count("transfer_task_id = ?", (file_id,))
        running_count = self.TransferLog.count("transfer_task_id = ? and status in (0,1)", (file_id,))
        return {
            "task_type": "file",
            "task_id": file_id,
            "count": count,
            "complete": count - error_num - running_count,
            "error": error_num,
            "data": [i.to_show_data() for i in log_list],
        }

    def history_command_task(self, cmd_id: int, only_error: bool = True) -> Dict:
        if only_error:
            log_list = self.CommandLog.query("command_task_id = ? and status = ?", (cmd_id, 3))
            error_num = len(log_list)
        else:
            log_list = self.CommandLog.query("command_task_id = ?", (cmd_id,))
            error_num = len([i for i in log_list if i.status == 3])
        count = self.CommandLog.count("command_task_id = ?", (cmd_id,))
        running_count = self.TransferLog.count("transfer_task_id = ? and status in (0,1)", (cmd_id,))
        return {
            "task_type": "command",
            "task_id": cmd_id,
            "count": count,
            "complete": count - error_num - running_count,
            "error": error_num,
            "data": [i.to_show_data(only_error=only_error) for i in log_list],
        }

    def history_flow_task(self, flow: Union[int, Flow]) -> Dict:
        if isinstance(flow, int):
            flow = self.Flow.get_byid(flow)
        steps: List[Union[CommandTask, TransferTask]] = [
            *self.CommandTask.query("flow_id = ?", (flow.id,)),
            *self.TransferTask.query("flow_id = ?", (flow.id,))
        ]

        for step in steps:
            if step.status == 1:
                now_idx = step.step_index
                break
        else:
            now_idx = len(steps)
        steps.sort(key=lambda x: x.step_index, reverse=False)

        flow.steps = steps
        flow_data = flow.to_dict()
        flow_data["steps"] = [i.to_show_data() for i in steps]
        flow_data["now_idx"] = now_idx
        return flow_data