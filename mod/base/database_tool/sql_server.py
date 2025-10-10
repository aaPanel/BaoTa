import os
import re

from typing import Optional, Dict, List, Union, Tuple

from .base import BaseDatabaseTool, sqlserver
from .util import read_file, GET_CLASS


class SQLServerTool(BaseDatabaseTool):
    _type_name = "sqlserver"

    def local_server_info(self) -> Optional[Dict]:
        return None

    # 添加一个数据库
    def add_database(self, server_id: int, database_name: str, **kwargs) -> Tuple[bool, str]:
        get_obj = GET_CLASS()
        get_obj.name = database_name
        get_obj.sid = server_id
        get_obj.ps = kwargs.get("ps", "")
        get_obj.db_user = kwargs.get("db_user", "")
        get_obj.password = kwargs.get("password", "")
        res = sqlserver().AddDatabase(get_obj)
        if res["status"] is True:
            return True, "添加成功"
        else:
            return False, res['msg']
