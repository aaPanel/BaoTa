from .pgsql import PgsqlTool
from .mongodb import MongodbTool
from .mysql import MysqlTool
from .sql_server import SQLServerTool

from typing import Optional

DB_TYPE = (
    "pgsql",
    "mongodb",
    "mysql",
    "sqlserver"
)


def add_database(db_type: str, data: dict) -> Optional[str]:
    """
    data: 中包含的有效参数为
    database_name：数据库名称
    server_id：数据库 id
    db_user：数据库用户名
    password：数据库用户的密码
    dataAccess ：链接限制方式 如：ip
    address：可允许使用的ip， 配合上一个参数使用
    codeing： 编码
    ps：备注
    listen_ip: pgsql 有效，可设置访问地址
    """
    if db_type not in DB_TYPE:
        return "错误的数据库类型"

    if db_type == "pgsql":
        tool = PgsqlTool()
    elif db_type == "mongodb":
        tool = MongodbTool()
    elif db_type == "mysql":
        tool = MysqlTool()
    else:
        tool = SQLServerTool()

    f, msg = tool.add_database(data.pop("server_id"), data.pop("database_name"), **data)
    if not f:
        return msg
    return None


__all__ = [
    "PgsqlTool",
    "MongodbTool",
    "MysqlTool",
    "SQLServerTool",
    "add_database",
]
