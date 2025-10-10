
ALLOWED_TYPE = "push_msg"  # 允许的信息详情类型


def init_db():
    import public
    from db import Sql

    db = Sql()
    db.dbfile("msg_box")
    create_sql_str = (
        "CREATE TABLE IF NOT EXISTS 'push_msg' ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "pid INTEGER NOT NULL UNIQUE DEFAULT 0, "
        "push_type TEXT NOT NULL DEFAULT '', "
        "push_title TEXT NOT NULL DEFAULT '', "
        "data TEXT NOT NULL DEFAULT '{}'"
        ");"
    )
    res = db.execute(create_sql_str)
    if isinstance(res, str) and res.startswith("error"):
        public.WriteLog("消息盒子", "建表push_msg失败")
        return

    index_sql_str = "CREATE INDEX IF NOT EXISTS 'push_pid_index' ON 'push_msg' ('pid');"

    res = db.execute(index_sql_str)
    if isinstance(res, str) and res.startswith("error"):
        public.WriteLog("消息盒子", "为push_msg建立索引push_pid_index失败")
        return

