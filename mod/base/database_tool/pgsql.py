import os
import re

from typing import Optional, Dict, List, Union, Tuple

from .base import BaseDatabaseTool, pgsql
from .util import read_file, GET_CLASS


class PgsqlTool(BaseDatabaseTool):
    _type_name = "pgsql"

    def local_server_info(self) -> Optional[Dict]:
        bin_path = "/www/server/pgsql/bin/postgres"
        if not os.path.isfile(bin_path):
            return None

        conf_file = '/www/server/pgsql/data/postgresql.conf'
        conf = read_file(conf_file)
        default_port = 5432
        if not isinstance(conf, str):
            port = default_port
        else:
            rep_port = re.compile(r"\s*port\s*=\s*(?P<port>\d+)", re.M)
            port_res = rep_port.search(conf)
            if not port_res:
                port = default_port
            else:
                port = int(port_res.group("port"))

        return {
            'id': 0,
            'db_host': '127.0.0.1',
            'db_port': port,
            'db_user': 'root',
            'db_password': '',
            'ps': '本地服务器',
            'addtime': 0
        }

    # 添加一个数据库
    def add_database(self, server_id: int, database_name: str, **kwargs) -> Tuple[bool, str]:
        get_obj = GET_CLASS()
        get_obj.name = database_name
        get_obj.sid = server_id
        get_obj.ps = kwargs.get("ps", "")
        get_obj.db_user = kwargs.get("db_user", "")
        get_obj.password = kwargs.get("password", "")
        get_obj.listen_ip = kwargs.get("listen_ip", "")
        res = pgsql().AddDatabase(get_obj)
        if res["status"] is True:
            return True, "添加成功"
        else:
            return False, res['msg']
