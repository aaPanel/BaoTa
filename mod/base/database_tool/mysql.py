import os
import re

from typing import Optional, Dict, List, Union, Tuple

from .base import BaseDatabaseTool, panelMysql, database
from .util import read_file, write_file, DB, GET_CLASS


class MysqlTool(BaseDatabaseTool):
    _type_name = "mysql"

    def local_server_info(self) -> Optional[Dict]:
        bin_path = "/www/server/mysql/bin/mysql"
        if not os.path.isfile(bin_path):
            return None

        conf_file = '/etc/my.cnf'
        conf = read_file(conf_file)
        default_port = 3306
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

    # 检测服务是否可以链接
    # def server_status(self, server_id: int) -> Union[Dict, str]:
    #     """
    #     数据库状态检测
    #     """
    #     db_name = None
    #     if server_id != 0:
    #         conn_config = DB("database_servers").where("id=? AND LOWER(db_type)=LOWER('mysql')", (server_id,)).find()
    #         if not conn_config:
    #             return "远程数据库信息不存在！"
    #         conn_config["db_name"] = None
    #         db_user = conn_config["db_user"]
    #         root_password = conn_config["db_password"]
    #         db_host = conn_config["db_host"]
    #         db_port = conn_config["db_port"]
    #     else:
    #         db_user = "root"
    #         root_password = DB("config").where("id=?", (1,)).getField("mysql_root")
    #         db_host = "localhost"
    #         try:
    #             db_port = int(panelMysql().query("show global variables like 'port'")[0][1])
    #         except:
    #             db_port = 3306
    #     mysql_obj = panelMysql()
    #     flag = mysql_obj.set_host(db_host, db_port, db_name, db_user, root_password)
    #
    #     error = ''
    #     db_status = True
    #     if flag is False:
    #         db_status = False
    #         error = mysql_obj._ex
    #
    #     return {
    #         "status": True,
    #         'error': str(error),
    #         "msg": "正常" if db_status is True else "异常",
    #         "db_status": db_status
    #     }

    # 添加一个数据库
    def add_database(self, server_id: int, database_name: str, **kwargs) -> Tuple[bool, str]:
        get_obj = GET_CLASS()
        get_obj.name = database_name
        get_obj.sid = server_id
        get_obj.db_user = kwargs.get("db_user", "")
        get_obj.password = kwargs.get("password", "")
        get_obj.dataAccess = kwargs.get("dataAccess", "")
        get_obj.address = kwargs.get("address", "")
        get_obj.codeing = kwargs.get("codeing", "")
        get_obj.dtype = "MySQL"
        get_obj.ps = kwargs.get("ps", "")
        get_obj.host = kwargs.get("host", "")
        get_obj.pid = str(kwargs.get("pid", '0'))
        res = database().AddDatabase(get_obj)
        if res["status"] is True:
            return True, "添加成功"
        else:
            return False, res['msg']
