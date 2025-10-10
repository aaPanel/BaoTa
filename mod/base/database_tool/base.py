import sys
from typing import List, Dict, Optional
from .util import DB


if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

from db_mysql import panelMysql
from database import database
from databaseModel.mongodbModel import main as mongodb
from databaseModel.pgsqlModel import main as pgsql
from databaseModel.sqlserverModel import main as sqlserver


class BaseDatabaseTool:
    _type_name = ""

    def local_server_info(self) -> Optional[Dict]:
        raise NotImplementedError()

    # 获取所有可以管理的服务器的信息
    def server_list(self) -> List[Dict]:
        data = DB('database_servers').where("LOWER(db_type)=LOWER('?')", (self._type_name, )).select()
        if not isinstance(data, list):
            data = []
        local_server = self.local_server_info()
        if local_server is not None:
            data.insert(0, local_server)
        return data

    # 添加一个数据库
    def add_database(self, server_id: int, database_name: str, **kwargs) -> List[Dict]:
        raise NotImplementedError()
