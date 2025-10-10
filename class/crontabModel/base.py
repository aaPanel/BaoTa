#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
#-------------------------------------------------------------------
import os,sys,time,json
panelPath = '/www/server/panel'
os.chdir(panelPath)
if not panelPath + "/class/" in sys.path:
    sys.path.insert(0, panelPath + "/class/")
import public
import db
class crontabBase:
    dbfile = public.get_panel_path() + '/data/db/script.db'
    __columns = None
    def __init__(self) -> None:
        if not os.path.exists(self.dbfile):
            self.create_table()
        self.check_column()
        self.sync_scripts()
        self.sync_types() 

    def exists_column(self, sql_pbj,table,column):
        '''
            @name 判断列是否存在
            @author hwliang
            @param sql_pbj <object> 数据库对象
            @param table <str> 表名
            @param column <str> 列名
            @return <bool> True 存在，False 不存在
        '''
        if not self.__columns:
            self.__columns = sql_pbj.query('PRAGMA table_info('+table+')',())
        for col in self.__columns:
            if len(col) < 3: continue
            if col[1] == column: return True
        return False

    def check_column(self):
        '''
            @name 检查表结构是否完整，不完整则补充完整
            @autho hwliang
            @return void
        '''

        sql_obj = db.Sql().dbfile(self.dbfile)
        if not sql_obj: return
        if not self.exists_column(sql_obj,'scripts','is_args'):
            sql_obj.execute("ALTER TABLE 'scripts' ADD 'is_args' INTEGER DEFAULT 0",())
        if not self.exists_column(sql_obj,'scripts','args_title'):
            sql_obj.execute("ALTER TABLE 'scripts' ADD 'args_title' VARCHAR",())
        if not self.exists_column(sql_obj,'scripts','args_ps'):
            sql_obj.execute("ALTER TABLE 'scripts' ADD 'args_ps' VARCHAR",())
        if not self.exists_column(sql_obj,'operator_where','args'):
            sql_obj.execute("ALTER TABLE 'operator_where' ADD 'args' VARCHAR",())
        if not self.exists_column(sql_obj,'trigger','args'):
            sql_obj.execute("ALTER TABLE 'trigger' ADD 'args' VARCHAR",())
        if sql_obj.table('types').where('type_id=?',3).getField('name') != '告警通知':
            sql_obj.table('types').where('type_id=?',3).update({'name':'告警通知','title':'用于发送各种告警通知的脚本'})

        sql_obj.close()
    def sync_types(self):
        panel_path = public.get_panel_path()
        # 检查文件是否存在
        tfile = '{}/config/script_types.json'.format(panel_path)
        if not os.path.exists(tfile): return
        tbody = public.readFile(tfile)
        if not tbody: return

        # 检查内容是否变更
        last_sync_md5_file = '{}/data/last_sync_types_md5.pl'.format(panel_path)
        tmd5 = public.md5(tbody)
        if os.path.exists(last_sync_md5_file):
            last_sync_md5 = public.readFile(last_sync_md5_file)
            if last_sync_md5 == tmd5: return

        # 同步类型库
        try:
            type_list = json.loads(tbody)
            sql_obj = db.Sql().dbfile(self.dbfile)
            for type_item in type_list:
                type_info = sql_obj.table('types').where('type_id=?', (type_item['type_id'],)).find()
                if type_info:
                    # 更新类型信息
                    sql_obj.table('types').where('type_id=?', (type_item['type_id'],)).update(type_item)
                else:
                    sql_obj.table('types').insert(type_item)
            sql_obj.close()

            # 记录本次同步内容的MD5
            public.writeFile(last_sync_md5_file, tmd5)
        except:
            return
    def sync_scripts(self):
        '''
            @name 同步脚本库
            @autho hwliang
            @return void
        '''
        panel_path = public.get_panel_path()
        # 检查文件是否存在
        sfile = '{}/config/crontab.json'.format(panel_path)
        if not os.path.exists(sfile): return
        sbody = public.readFile(sfile)
        if not sbody: return

        # 检查内容是否变更
        last_sync_md5_file = '{}/data/last_sync_md5.pl'.format(panel_path)
        smd5 = public.md5(sbody)
        if os.path.exists(last_sync_md5_file):
            last_sync_md5 = public.readFile(last_sync_md5_file)
            if last_sync_md5 == smd5: return

        # 同步脚本库
        try:
            script_list = json.loads(sbody)
            sql_obj = db.Sql().dbfile(self.dbfile)
            for script in script_list:
                if 'script_id' in script.keys():
                    del(script['script_id'])
                script_info = sql_obj.table('scripts').where('name=?',(script['name'],)).find()
                if script_info:
                    # 更新脚本版本
                    if script_info['version'] == script['version']: continue
                    sql_obj.table('scripts').where('script_id=?',(script_info['script_id'],)).update(script)
                else:
                    sql_obj.table('scripts').insert(script)
            sql_obj.close()

            # 记录本次同步内容的MD5
            public.writeFile(last_sync_md5_file,smd5)
        except:
            return

    def create_table(self):
        '''
            @name 创建表结构
            @autho hwliang
            @return void
        '''
        sql_obj = db.Sql().dbfile(self.dbfile)
        if not sql_obj: return
        sql = '''
CREATE TABLE operator_where (
    where_id INTEGER PRIMARY KEY AUTOINCREMENT,
    trigger_id INTEGER,
    operator VARCHAR,
    op_value VARCHAR,
    args VARCHAR,
    run_script_id INTEGER,
    run_script TEXT,
    create_time INTEGER DEFAULT (0)
)
'''
        sql_obj.execute(sql,())
        sql_obj.execute('CREATE INDEX tid ON operator_where (trigger_id)',())

        sql = '''
CREATE TABLE scripts (
    script_id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_id INTEGER DEFAULT (0), is_baota INTEGER DEFAULT (0),
    name VARCHAR, status INTEGER DEFAULT (1),
    author VARCHAR, script TEXT,
    version VARCHAR,
    return_type VARCHAR DEFAULT string,
    is_args INTEGER DEFAULT (0),
    script_type INTEGER DEFAULT (0),
    ps VARCHAR,
    create_time INTEGER DEFAULT (0)
)
'''
        sql_obj.execute(sql,())
        sql_obj.execute('CREATE INDEX type_id ON scripts (type_id);',())
        sql_obj.execute('CREATE INDEX is_baota ON scripts (is_baota);',())
        sql_obj.execute('CREATE INDEX status ON scripts (status);',())

        sql = '''CREATE TABLE "trigger" (
    trigger_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR,
    status INTEGER DEFAULT (1),
    script_id INTEGER DEFAULT (0),
    script_body TEXT,
    cycle_type VARCHAR,
    cycle_where VARCHAR,
    cycle_hour INTEGER DEFAULT (0),
    cycle_minute INTEGER DEFAULT (0),
    ps VARCHAR,
    create_time INTEGER DEFAULT (0)
)
'''

        sql_obj.execute(sql,())
        sql_obj.execute('CREATE INDEX t_status ON "trigger" (status)',())

        sql = '''
CREATE TABLE types (
    type_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR, title VARCHAR
)
'''
        sql_obj.execute(sql,())
        sql_obj.execute("INSERT INTO types (type_id, name, title) VALUES (1, '服务管理', '用于管理服务状态的脚本，如检测服务状态、停止、重载、启动等')",())
        sql_obj.execute("INSERT INTO types (type_id, name, title) VALUES (2, '进程监控', '用于监控进程状态的脚本，如进程存活、开销等')",())
        sql_obj.execute("INSERT INTO types (type_id, name, title) VALUES (3, '告警通知', '用于发送各种告警通知的脚本')",())
        sql_obj.execute("INSERT INTO types (type_id, name, title) VALUES (4, '负载监控', '用于监控系统负载的脚本，如CPU、内存、网络等')",())
        sql_obj.execute("INSERT INTO types (type_id, name, title) VALUES (5, '网站监控', '用于监控网站状态的脚本，如指定URL地址访问状态、内容等')",())
        sql_obj.execute("INSERT INTO types (type_id, name, title) VALUES (6, '其它', '综合用途的脚本，如系统升级、面板升级、软件升级等')",())
        sql_obj.execute("INSERT INTO types (type_id, name, title) VALUES (7, '自定义', '用户自定义的脚本');",())

        sql = '''CREATE TABLE tasks (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    script_id INTEGER DEFAULT (0),
    trigger_id INTEGER DEFAULT (0),
    where_id INTEGER DEFAULT (0),
    status INTEGER DEFAULT (0),
    result_succ VARCHAR,
    result_err VARCHAR,
    start_time INTEGER DEFAULT (0),
    end_time INTEGER DEFAULT (0)
)
'''
        sql_obj.execute("CREATE INDEX sid ON tasks (script_id)",())
        sql_obj.execute("CREATE INDEX t_id ON tasks (trigger_id)",())
        sql_obj.execute("CREATE INDEX wid ON tasks (where_id)",())
        sql_obj.execute("CREATE INDEX stat ON tasks (status)",())
        sql_obj.execute(sql,())
        sql_obj.close()

