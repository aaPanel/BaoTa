import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Tuple
import sqlite3
import json

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public
import db

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")


@dataclass
class FileTransferTask:
    task_id: Optional[int] = None
    source_node: dict = field(default_factory=lambda: {})
    target_node: dict = field(default_factory=lambda: {})
    source_path_list: list = field(default_factory=lambda: [])  # [{"path":"/www/wwwroot/aaaa", "is_dir":true}]
    target_path: str = ""
    task_action: str = ""  # upload/download
    status: str = "pending"  # pending/running/completed/failed
    default_mode: str = "cover"  # 默认处理模式  cover: 覆盖，ignore: 跳过，rename:重命名
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: str = ""
    target_task_id: int = 0
    is_source_node: bool = False
    is_target_node: bool = False

    @classmethod
    def from_dict(cls, row: dict) -> 'FileTransferTask':
        source_node = row.get("source_node", "{}")
        if isinstance(source_node, str):
            source_node = json.loads(source_node)
        elif isinstance(source_node, dict):
            source_node = source_node
        else:
            source_node = {}

        target_node = row.get("target_node", "{}")
        if isinstance(target_node, str):
            target_node = json.loads(target_node)
        elif isinstance(target_node, dict):
            target_node = target_node
        else:
            target_node = {}

        source_path_list = row.get("source_path_list", "[]")
        if isinstance(source_path_list, str):
            source_path_list = json.loads(source_path_list)
        elif isinstance(source_path_list, list):
            source_path_list = source_path_list
        else:
            source_path_list = []

        return cls(
            task_id=row.get("task_id", None),
            source_node=source_node,
            target_node=target_node,
            source_path_list=source_path_list,
            target_path=row.get("target_path", ""),
            task_action=row.get("task_action", ""),
            status=row.get("status", ""),
            default_mode=row.get("default_mode", "cover"),
            created_at=datetime.fromisoformat(row.get("created_at")) if row.get("created_at", "") else None,
            started_at=datetime.fromisoformat(row.get("started_at")) if row.get("started_at", "") else None,
            completed_at=datetime.fromisoformat(row.get("completed_at")) if row.get("completed_at", "") else None,
            created_by=row.get("created_by", ""),
            target_task_id=row.get("target_task_id", 0),
            is_source_node=row.get("is_source_node", False),
            is_target_node=row.get("is_target_node", False)
        )

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "source_node": self.source_node,
            "target_node": self.target_node,
            "source_path_list": self.source_path_list,
            "target_path": self.target_path,
            "task_action": self.task_action,
            "status": self.status,
            "default_mode": self.default_mode,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_by": self.created_by,
            "target_task_id": self.target_task_id,
            "is_source_node": self.is_source_node,
            "is_target_node": self.is_target_node
        }


@dataclass
class FileTransfer:
    transfer_id: Optional[int] = None
    task_id: int = 0
    src_file: str = ""
    dst_file: str = ""
    file_size: int = 0
    is_dir: int = 0
    status: str = ""  # pending/running/completed/failed
    progress: int = 0
    message: str = ""
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, row: dict) -> 'FileTransfer':
        return cls(
            transfer_id=row.get("transfer_id", None),
            task_id=row.get("task_id", 0),
            src_file=row.get("src_file", ""),
            dst_file=row.get("dst_file", ""),
            file_size=row.get("file_size", 0),
            is_dir=row.get("is_dir", 0),
            status=row.get("status", ""),
            progress=row.get("progress", 0),
            message=row.get("message", ""),
            created_at=datetime.fromisoformat(row.get("created_at")) if row.get("created_at", "") else None,
            started_at=datetime.fromisoformat(row.get("started_at")) if row.get("started_at", "") else None,
            completed_at=datetime.fromisoformat(row.get("completed_at")) if row.get("completed_at", "") else None
        )

    def to_dict(self) -> dict:
        return {
            "transfer_id": self.transfer_id,
            "task_id": self.task_id,
            "src_file": self.src_file,
            "dst_file": self.dst_file,
            "file_size": self.file_size,
            "is_dir": self.is_dir,
            "status": self.status,
            "progress": self.progress,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


# SQLite 操作类
class FileTransferDB:
    _DB_FILE = public.get_panel_path() + "/data/db/node_file_transfer.db"
    _DB_INIT_FILE = os.path.dirname(__file__) + "/file_transfer.sql"

    def __init__(self):
        sql = db.Sql()
        sql._Sql__DB_FILE = self._DB_FILE
        self.db = sql

    def init_db(self):
        sql_data = public.readFile(self._DB_INIT_FILE)
        if not os.path.exists(self._DB_FILE) or os.path.getsize(self._DB_FILE) == 0:
            public.writeFile(self._DB_FILE, "")
            import sqlite3
            conn = sqlite3.connect(self._DB_FILE)
            c = conn.cursor()
            c.executescript(sql_data)
            conn.commit()
            conn.close()

    def close(self):
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_trackback):
        self.close()

    def __del__(self):
        self.close()

    def create_task(self, task: FileTransferTask) -> str:
        task_data = task.to_dict()
        task_data.pop('task_id', None)
        task_data.pop('created_at', None)
        task_data["source_node"] = json.dumps(task_data["source_node"])
        task_data["target_node"] = json.dumps(task_data["target_node"])
        task_data["source_path_list"] = json.dumps(task_data["source_path_list"])
        try:
            err = self.db.table("transfer_tasks").insert(task_data)
            if isinstance(err, str):
                return err
            elif isinstance(err, int):
                task.task_id = err
            return ""
        except Exception as e:
            return f"数据库操作错误: {str(e)}"

    def update_task(self, task: FileTransferTask) -> str:
        task_data = task.to_dict()
        task_data.pop('created_at', None)
        task_data["source_node"] = json.dumps(task_data["source_node"])
        task_data["target_node"] = json.dumps(task_data["target_node"])
        task_data["source_path_list"] = json.dumps(task_data["source_path_list"])
        if not task.task_id:
            return "task_id is required"
        try:
            err = self.db.table("transfer_tasks").where("task_id = ?", task.task_id).update(task_data)
            if isinstance(err, str):
                return err
            return ""
        except Exception as e:
            return f"数据库操作错误: {str(e)}"

    def get_task(self, task_id: int) -> Tuple[Optional[dict], str]:
        result = self.db.table("transfer_tasks").where("task_id = ?", task_id).find()
        if isinstance(result, str):
            return None, result
        if self.db.ERR_INFO:
            return None, self.db.ERR_INFO
        return result, ""

    def get_last_task(self) -> Tuple[Optional[dict], str]:
        result = self.db.table("transfer_tasks").order("task_id DESC").limit(1).find()
        if isinstance(result, str):
            return None, result
        if self.db.ERR_INFO:
            return None, self.db.ERR_INFO
        return result, ""

    def delete_task(self, task_id: int) -> str:
        result = self.db.table("transfer_tasks").where("task_id = ?", task_id).delete()
        if isinstance(result, str):
            return result
        return ""

    def get_all_tasks(self, offset: int = 0, limit: int = 100) -> List[dict]:
        results = self.db.table("transfer_tasks").limit(limit, offset).select()
        if isinstance(results, list):
            return results
        return []

    def count_tasks(self) -> int:
        return self.db.table("transfer_tasks").count()

    def create_file_transfer(self, transfer: FileTransfer) -> str:
        transfer_data = transfer.to_dict()
        transfer_data.pop('transfer_id', None)
        transfer_data.pop('created_at', None)
        try:
            err = self.db.table("file_transfers").insert(transfer_data)
            if isinstance(err, str):
                return err
            return ""
        except Exception as e:
            return f"数据库操作错误: {str(e)}"

    def update_file_transfer(self, transfer: FileTransfer) -> str:
        transfer_data = transfer.to_dict()
        if not transfer.transfer_id:
            return "transfer_id is required"
        try:
            err = self.db.table("file_transfers").where("transfer_id = ?", transfer.transfer_id).update(transfer_data)
            if isinstance(err, str):
                return err
            return ""
        except Exception as e:
            return f"数据库操作错误: {str(e)}"

    def get_file_transfer(self, transfer_id: int) -> Optional[dict]:
        result = self.db.table("file_transfers").where("transfer_id = ?", transfer_id).find()
        if isinstance(result, str):
            return None
        if self.db.ERR_INFO:
            return None
        return result

    def get_task_file_transfers(self, task_id: int) -> List[dict]:
        results = self.db.table("file_transfers").where("task_id = ?", task_id).select()
        if isinstance(results, list):
            return results
        return []

    def batch_create_file_transfers(self, transfers: List[FileTransfer]) -> str:
        """
        批量创建文件传输记录
        
        Args:
            transfers: FileTransfer 对象列表
            
        Returns:
            str: 错误信息，如果成功则返回空字符串
        """
        if not transfers:
            return ""

        try:
            # 准备批量插入的数据
            transfer_data_list = []
            for transfer in transfers:
                transfer_data = transfer.to_dict()
                transfer_data.pop('transfer_id', None)
                transfer_data['created_at'] = datetime.now().isoformat()
                transfer_data_list.append(transfer_data)

            # 执行批量插入
            err = self.db.table("file_transfers").batch_insert(transfer_data_list)
            if isinstance(err, str):
                return err
            return ""
        except Exception as e:
            return f"批量创建文件传输记录失败: {str(e)}"

    # 获取上一个任务所有文件传输状态
    def last_task_all_status(self) -> Tuple[Dict, str]:
        last_task, err = self.get_last_task()
        if err:
            return {}, err
        if not last_task:
            return {}, ""

        task = FileTransferTask.from_dict(last_task)
        file_list = self.get_task_file_transfers(task.task_id)
        return {
            "task": task.to_dict(),
            "file_list": file_list,
        }, ""
