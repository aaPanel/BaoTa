# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: miku <miku@bt.cn>
# -------------------------------------------------------------------

import json
import os
import sys
import time
import sys
import concurrent.futures
import threading
import hashlib
import datetime
import re
import shutil
import random
import string
if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

if '/www/server/panel' not in sys.path:
    sys.path.insert(0, '/www/server/panel')

import panelMysql
import db_mysql
import database

import public
from mod.project.backup_restore.base_util import BaseUtil
from mod.project.backup_restore.data_manager import DataManager
from mod.project.backup_restore.config_manager import ConfigManager

class DatabaseModule(DataManager,BaseUtil,ConfigManager):
    _MYSQLDUMP_BIN = public.get_mysqldump_bin()
    _MYSQL_BIN = public.get_mysql_bin()

    def __init__(self):
        self.base_path = '/www/backup/backup_restore'
        self.bakcup_task_json = self.base_path + '/backup_task.json'

    def get_database_backup_conf(self,timestamp=None):
        mysql_data = public.M('databases').select()
        db_list = []
        for data in mysql_data:
            db_info = {}  
            db_info['name'] = data['name']
            db_info['type'] = data['type']
            db_info['id'] = data['id']
            db_info['sid'] = data['sid']
            db_info['ps'] = data['ps']
            db_info['username'] = data['username']
            db_info['password'] = data['password']
            db_info["data_type"] = "backup"
            db_info['accept'] = data['accept']
            db_info['status'] = 0
            db_info['msg'] = None
            db_info['database_record'] = data
            db_list.append(db_info)

        if os.path.exists("/www/server/redis/src/redis-server") and os.path.exists("/www/server/redis/version.pl"):
            db_info = self.get_redis_info()
            db_list.append(db_info)
        return db_list

    def get_redis_info(self):
        db_info = {}
        db_info['name'] = "redis"
        db_info['type'] = "redis"
        db_info['id'] = 0
        db_info['sid'] = 0
        db_info['ps'] = "redis"
        db_info['username'] = "redis"
        db_info['password'] = "redis"
        db_info['status'] = 0
        db_info['msg'] = None
        return db_info


    def get_remote_db_list(self,timestamp=None):
        import db
        sql = db.Sql()
        sql.table('database_servers')
        result = sql.select()
        if result:
            return {
                'status':True,
                'msg':result
            }
        else:
            return {
                'status':False,
                'msg':'远程数据库列表为空'
            }
    
    def resotre_remote_db_server(self,remote_db_list):
        try:
            for remote_db in remote_db_list:
                local_remote_db_info=public.M('database_servers').where('db_host=? AND db_port=?', (remote_db['db_host'], remote_db['db_port'])).select()
                if not local_remote_db_info:
                    pdata = {
                        'id': remote_db['id'],
                        'db_host': remote_db['db_host'],
                        'db_port': remote_db['db_port'],
                        'db_user': remote_db['db_user'],
                        'db_password': remote_db['db_password'],
                        'ps': remote_db['ps'],
                        'type': remote_db['type'],
                        'db_type': remote_db['db_type']
                }
                result = public.M("database_servers").insert(pdata)
                print(result)
        except:
            pass
    
    def restore_remote_database(self,db_data):
        database_record=db_data['database_record']
        local_db_info=public.M('databases').where('name=?', (db_data["name"],)).select()
        if not local_db_info:
            pdata={
                'pid': database_record['pid'],
                'name': database_record['name'],
                'username': database_record['username'],
                'password': database_record['password'],
                'accept': database_record['accept'],
                'ps': database_record['ps'], 
                'addtime': database_record['addtime'],
                'db_type': database_record['db_type'],
                'conn_config': database_record['conn_config'],
                'sid': database_record['sid'],
                'type': database_record['type'],
                'type_id': database_record['type_id']
            }
            result = public.M("databases").insert(pdata)
            print(result)
            
    def backup_redis_data(self,timestamp:int):
        """
        备份数据库
        """
        db_fidx = None
        db_fname="all_db"
            
        import databaseModel.redisModel as panelRedis
        redis_obj = panelRedis.panelRedisDB()
        if redis_obj.redis_conn(0) is False:
            return public.returnMsg(False, "redis 连接异常！")
            
        self._db_num = 16
        _REDIS_CONF = os.path.join(public.get_setup_path(), "redis/redis.conf")
        if os.path.exists(_REDIS_CONF):
            redis_conf = public.readFile(_REDIS_CONF)
            db_obj = re.search("\ndatabases\s+(\d+)", redis_conf)
            if db_obj:
                self._db_num = int(db_obj.group(1))

        if db_fidx:
            redis_obj.redis_conn(0).execute_command("SELECT",int(db_fidx))
            redis_obj.redis_conn(0).execute_command("SAVE")
        else:
            for db_idx in range(0, self._db_num):
                redis_obj.redis_conn(db_idx).save()

        redis_obj = redis_obj.redis_conn(0)
        src_path = os.path.join(redis_obj.config_get().get("dir", ""), "dump.rdb")
        if not os.path.exists(src_path):
            return public.returnMsg(False, 'BACKUP_ERROR')
        backup_path = "/www/backup/backup_restore/{timestamp}_backup/database/redis".format(timestamp=timestamp)
        if not os.path.exists(backup_path):
            public.ExecShell("mkdir -p {}".format(backup_path))
        file_name = "{db_fname}_{backup_time}_redis_data.rdb".format(db_fname=db_fname, backup_time=time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()))
        file_path = os.path.join(backup_path, file_name)
        print(file_path)
        print(src_path)
        shutil.copyfile(src_path, file_path)
        if not os.path.exists(file_path):
            return public.returnMsg(False, 'BACKUP_ERROR')

        return public.returnMsg(True, file_path)
    
    def backup_database_data(self,timestamp):
        data_list=self.get_backup_data_list(timestamp)
        if not data_list:
            return None
        self.print_log("==================================","backup")
        self.print_log("开始备份数据库数据",'backup')
        for db in data_list['data_list']['database']:
            self.print_log("开始备份{}数据库".format(db['name']),'backup')
            db['status'] = 1
            self.update_backup_data_list(timestamp, data_list)
            if db['sid'] == 0:
                backup_file = None
                backup_result=None
                db['sql_file_name'] = None
                db['size'] = None
                db['sql_sha256'] = None
                if db['type'] == 'MySQL':
                    backup_result = self.backup_mysql_data(db['name'],timestamp)
                elif db['type'] == 'MongoDB':
                    backup_result = self.backup_mongodb_data(db['name'],timestamp)
                elif db['type'] == 'pgsql':
                    backup_result = self.backup_pgsql_data(db['name'],timestamp)
                elif db['type'] == 'redis':
                    backup_result = self.backup_redis_data(timestamp)
                
                if backup_result:
                    if backup_result['status'] == True:
                        backup_file=backup_result['msg']
                        db['sql_file_name'] = backup_file
                        db['size'] = self.get_file_size(backup_file)
                        db['sql_sha256'] = self.get_file_sha256(backup_file)
                        db['status'] = 2
                        db['msg'] = None
                    elif backup_result['status'] == False:
                        db['status'] = 3
                        db['msg'] = backup_result['msg']
                else:
                    db['status'] = 2
                    db['msg'] = None
            else:
                db['status'] = 2
                db['msg'] = None

            self.update_backup_data_list(timestamp, data_list)
            self.print_log("{}数据库备份完成".format(db['name']),'backup')

        try:
            self.backup_sqlite_data(timestamp)
        except:
            pass

        get_remote_list_result=self.get_remote_db_list()
        if get_remote_list_result['status'] == True:
            data_list['data_list']['remote_db_list']=get_remote_list_result['msg'] 
            self.update_backup_data_list(timestamp, data_list)

    def backup_sqlite_data(self,timestamp):
        db_model_path="/www/server/panel/data/db_model.json"
        if os.path.exists(db_model_path):
            if not os.path.exists("/www/backup/backup_restore/{timestamp}_backup/database/db_model.json".format(timestamp=timestamp)):
                public.ExecShell("mkdir -p /www/backup/backup_restore/{timestamp}_backup/database".format(timestamp=timestamp))
            public.ExecShell("\cp -rpa {db_model_path} /www/backup/backup_restore/{timestamp}_backup/database/db_model.json".format(db_model_path=db_model_path,timestamp=timestamp))
            db_model_info=json.loads(public.readFile(db_model_path))

            db_list=[]
            for db_path, db_info in db_model_info.items():
                if os.path.exists(db_path):
                    backup_dir = "/www/backup/backup_restore/{timestamp}_backup/database/sqlite".format(timestamp=timestamp)
                    if not os.path.exists(backup_dir):
                        public.ExecShell("mkdir -p {backup_dir}".format(backup_dir=backup_dir))

                    random_suffix = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8))
                    new_db_name = db_info['name'] + '_' + random_suffix
                    db_list.append({
                        "db_path": db_path,
                        "db_name": db_info['name'],
                        "new_db_name": new_db_name
                    })
                    backup_file_path = "{backup_dir}/{db_name}".format(backup_dir=backup_dir, db_name=new_db_name)
                    public.ExecShell("\cp -rpa {db_path} {backup_file_path}".format(db_path=db_path, backup_file_path=backup_file_path))
            public.WriteFile("/www/backup/backup_restore/{timestamp}_backup/database/sqlite/db_list.json".format(timestamp=timestamp), json.dumps(db_list))
    
    def restore_sqlite_data(self,timestamp):
        self.print_log("==================================","restore")
        self.print_log("开始还原SQLite数据库列表", "restore")
        db_model_path="/www/server/panel/data/db_model.json"
        backup_db_model_path = "/www/backup/backup_restore/{timestamp}_backup/database/db_model.json".format(timestamp=timestamp)
        backup_sqlite_dir = "/www/backup/backup_restore/{timestamp}_backup/database/sqlite".format(timestamp=timestamp)
        backup_sqlite_info_path = "/www/backup/backup_restore/{timestamp}_backup/database/sqlite/db_list.json".format(timestamp=timestamp)

        print(backup_db_model_path)
        print(backup_sqlite_dir)
        if not os.path.exists(backup_db_model_path) or not os.path.exists(backup_sqlite_dir):
            self.print_log("SQLite数据量列表备份文件不存在，跳过还原", "restore")
            return True
        
        db_model_info = json.loads(public.readFile(backup_sqlite_info_path))
        
        for db_info in db_model_info:
            self.print_log("sqlite 还原记录1","restore")
            db_name = db_info['db_name']
            new_db_name = db_info['new_db_name']
            db_path=db_info['db_path']
            if os.path.exists(db_path):
                self.print_log("sqlite 还原记录2","restore")
                continue
            self.print_log("sqlite 还原记录3","restore")
            db_dir = os.path.dirname(db_path)
            if not os.path.exists(db_dir):
                public.ExecShell("mkdir -p {}".format(db_dir))

            self.print_log("sqlite 还原记录4","restore")
            public.ExecShell("\cp -rpa {backup_sqlite_dir}/{new_db_name} {db_path}".format(backup_sqlite_dir=backup_sqlite_dir, new_db_name=new_db_name, db_path=db_path))
            return
        self.print_log("sqlite 还原记录5","restore")
        cp_cmd = "\cp -rpa {backup_db_model_path} {db_model_path}".format(backup_db_model_path=backup_db_model_path, db_model_path=db_model_path)
        public.ExecShell(cp_cmd)
        self.print_log("sqlite 还原记录6{}","restore")
        self.print_log("SQLite数据库列表还原完成", "restore")
        return True

            
    def backup_mysql_data(self,db_name:str,timestamp:int):
        mysql_obj = db_mysql.panelMysql()
        try:
            db_port = int(panelMysql.panelMysql().query("show global variables like 'port'")[0][1])
        except:
            db_port = 3306

        db_charset = public.get_database_character(db_name)
        
        set_gtid_purged = ""
        resp = public.ExecShell("{} --help | grep set-gtid-purged".format(self._MYSQLDUMP_BIN))[0]
        if resp.find("--set-gtid-purged") != -1:
            set_gtid_purged = "--set-gtid-purged=OFF"
        db_user="root"
        db_password=public.M("config").where("id=?", (1,)).getField("mysql_root")
        db_host="localhost"

        backup_path="/www/backup/backup_restore/{timestamp}_backup/database/mysql".format(timestamp=timestamp)
        if not os.path.exists(backup_path):
            os.makedirs(backup_path, exist_ok=True)
        sql_file=backup_path+"/{}.sql".format(db_name)
        shell = "'{mysqldump_bin}' {set_gtid_purged} --opt --skip-lock-tables --single-transaction --routines --events --skip-triggers --default-character-set='{db_charset}' --force " \
                "--host='{db_host}' --port={db_port} --user='{db_user}' --password='{db_password}' '{db_name}'".format(
                mysqldump_bin=self._MYSQLDUMP_BIN,
                set_gtid_purged=set_gtid_purged,
                db_charset=db_charset,
                db_host=db_host,
                db_port=db_port,
                db_user=db_user,
                db_password=db_password,
                db_name=db_name,
        )
        shell += " > '{export_sql_file}' ".format(export_sql_file=sql_file)
        public.ExecShell(shell, env={"MYSQL_PWD": db_password})
        return {"status": True, "msg": sql_file}

    def backup_mongodb_data(self,db_name,timestamp:int):
        """
        备份 MongoDB 数据库(仅本地)
        
        Args:
            db_name (str): 数据库名称
            
        Returns:
            dict: 备份结果状态
        """

        import databaseModel.mongodbModel as panelMongoDB

        # 检查备份工具是否存在
        _MONGODBDUMP_BIN = "/www/server/mongodb/bin/mongodump"
        _MONGOEXPORT_BIN = "/www/server/mongodb/bin/mongoexport"
        
        if not os.path.exists(_MONGODBDUMP_BIN):
            print("缺少备份工具，请先通过软件管理安装MongoDB!")
            return {"status": False, "msg": "缺少备份工具，请先通过软件管理安装MongoDB!"}
            
        if not os.path.exists(_MONGOEXPORT_BIN):
            print("缺少备份工具，请先通过软件管理安装MongoDB!")
            return {"status": False, "msg": "缺少备份工具，请先通过软件管理安装MongoDB!"}
            
        # 查询数据库信息
        db_find = public.M("databases").where("name=? AND LOWER(type)=LOWER('mongodb')", (db_name,)).find()
        if not db_find:
            print(f"数据库不存在！{db_name}")
            return {"status": False, "msg": f"数据库不存在！{db_name}"}
            
        if not public.process_exists("mongod"):
            print("Mongodb服务还未开启！")
            return {"status": False, "msg": "Mongodb服务还未开启！"}
            
        # 设置基本备份参数
        db_user = db_find.get("username", "")
        db_password = db_find.get("password", "")
        file_type = "bson"  # 默认使用bson格式备份
        db_host = "127.0.0.1"
        db_port = panelMongoDB.panelMongoDB().get_config_options("net", "port", 27017)
        
        # 设置备份路径
        backup_path = f"/www/backup/backup_restore/{timestamp}_backup/database/mongodb"
        if not os.path.exists(backup_path):
            os.makedirs(backup_path, exist_ok=True)
            
        file_name = f"{db_name}_{file_type}_{time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())}_mongodb_data"
        export_dir = os.path.join(backup_path, file_name)
        
        # 构建备份命令
        mongodump_shell = f"'{_MONGODBDUMP_BIN}' --host='{db_host}' --port={int(db_port)} --db='{db_name}' --out='{export_dir}'"
        
        # 如果需要认证，添加用户名和密码
        if db_password:
            mongodump_shell += f" --username='{db_user}' --password='{db_password}'"
            
        # 执行备份命令
        public.ExecShell(mongodump_shell)
        
        # 检查备份是否成功
        if not os.path.exists(export_dir):
            print("数据库备份失败，导出目录不存在！")
            return {"status": False, "msg": "数据库备份失败，导出目录不存在！"}
            
        # 压缩备份文件
        backup_file = f"{export_dir}.zip"
        public.ExecShell(f"cd {backup_path} && zip -m {backup_file} -r {file_name}")
        
        if not os.path.exists(backup_file):
            public.ExecShell(f"rm -rf {export_dir}")
            print("备份压缩失败！")
            return {"status": False, "msg": "备份压缩失败！"}
            
        # 记录备份信息
        backup_size = os.path.getsize(backup_file)
        print(backup_file)
        return {"status": True, "msg": backup_file}
        if backup_size < 1:
            print("备份执行成功，备份文件小于1b，请检查备份完整性。")
            return {"status": True, "msg": "备份执行成功，备份文件小于1b，请检查备份完整性。"}
        else:
            print(f"MongoDB数据库 {db_name} 备份成功！")
            return {"status": True, "msg": "备份成功", "path": backup_file}



    def backup_pgsql_data(self,db_name:str,timestamp:int):
        """
        备份PostgreSQL数据库(仅本地)
        
        Args:
            db_name (str): 数据库名称
            timestamp (int): 时间戳，用于创建备份目录
            
        Returns:
            dict: 备份结果状态
        """
        # 检查备份工具是否存在
        _PGDUMP_BIN = "/www/server/pgsql/bin/pg_dump"
        
        if not os.path.exists(_PGDUMP_BIN):
            print("缺少备份工具，请先通过软件商店安装pgsql管理器!")
            return {"status": False, "msg": "缺少备份工具，请先通过软件商店安装pgsql管理器!"}
            
        # 查询数据库信息
        db_find = public.M("databases").where("name=? AND LOWER(type)=LOWER('pgsql')", (db_name,)).find()
        if not db_find:
            print(f"数据库不存在！{db_name}")
            return {"status": False, "msg": f"数据库不存在！{db_name}"}
            
        # 设置基本备份参数
        db_user = "postgres"
        db_host = "127.0.0.1"
        db_port = 5432
        
        # 获取PostgreSQL密码
        try:
            t_path = os.path.join(public.get_panel_path(), "data/postgresAS.json")
            if not os.path.isfile(t_path):
                print("请先设置管理员密码！")
                return {"status": False, "msg": "请先设置管理员密码！"}
                
            admin_info = json.loads(public.readFile(t_path))
            db_password = admin_info.get("password", "")
            if not db_password:
                print("数据库密码为空！请先设置数据库密码！")
                return {"status": False, "msg": "数据库密码为空！请先设置数据库密码！"}
        except Exception as e:
            print(f"获取PostgreSQL密码失败: {str(e)}")
            return {"status": False, "msg": f"获取PostgreSQL密码失败: {str(e)}"}
            
        # 设置备份路径
        backup_path = f"/www/backup/backup_restore/{timestamp}_backup/database/pgsql"
        if not os.path.exists(backup_path):
            os.makedirs(backup_path, exist_ok=True)
            
        # 构建备份文件名
        file_name = f"{db_name}_{time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())}_pgsql_data.sql.gz"
        backup_file = os.path.join(backup_path, file_name)
        
        # 构建备份命令
        shell = f"'{_PGDUMP_BIN}' --host='{db_host}' --port={int(db_port)} --username='{db_user}' --dbname='{db_name}' --clean | gzip > '{backup_file}'"
        
        # 执行备份命令
        public.ExecShell(shell, env={"PGPASSWORD": db_password})
        
        # 检查备份是否成功
        if not os.path.exists(backup_file):
            print("数据库备份失败，导出文件不存在！")
            return {"status": False, "msg": "数据库备份失败，导出文件不存在！"}
            
        # 记录备份信息
        backup_size = os.path.getsize(backup_file)
        
        # 写入日志
        public.WriteLog("TYPE_DATABASE", "DATABASE_BACKUP_SUCCESS", (db_name,))
        return {"status": True, "msg": backup_file}
        
        if backup_size < 2048:
            print("备份执行成功，备份文件小于2KB，请检查备份完整性。")
            return {"status": True, "msg": "备份执行成功，备份文件小于2KB，请检查备份完整性。"}
        else:
            print(f"PostgreSQL数据库 {db_name} 备份成功！")
            return {"status": True, "msg": "备份成功", "path": backup_file}
        
    
    def restore_database_data(self,timestamp):
        self.print_log("==================================","restore")
        self.print_log("开始还原数据库数据","restore")
        restore_data=self.get_restore_data_list(timestamp)
        database_data=restore_data['data_list']['database']
        for db_data in database_data:
            self.print_log("开始还原{}数据库".format(db_data['name']),"restore")
            db_data['restore_status']=1
            self.update_restore_data_list(timestamp, restore_data)
            if db_data['sid'] == 0:
                if db_data['type'] == 'MySQL':
                    self.restore_mysql_info(db_data)
                    self.input_mysql_sql(db_data)
                elif db_data['type'] == 'MongoDB':
                    self.restore_mongodb_info(db_data)
                    self.restore_mongodb_data(db_data)
                elif db_data['type'] == 'pgsql':
                    self.restore_pgsql_info(db_data)
                    self.restore_pgsql_data(db_data)
                elif db_data['type'] == 'redis':
                    self.restore_redis_data(db_data)
            else:
                self.restore_remote_database(db_data)
            db_data['restore_status']=2
            self.update_restore_data_list(timestamp, restore_data)
            self.print_log("{}数据库还原完成".format(db_data['name']),"restore")

        remote_db_list = restore_data['data_list'].get('remote_db_list')
        if remote_db_list is not None:
            self.print_log("开始还原远程数据库","restore")
            self.resotre_remote_db_server(restore_data['data_list']['remote_db_list'])
            self.print_log("远程数据库还原完成","restore")

        try:
            self.restore_sqlite_data(timestamp)
        except Exception as e:
            self.print_log("还原sqlite数据失败{}".format(e),"restore")

    def init_mysql_root(self,get=None):
        try:
            if not os.path.exists("/www/server/panel/data/remysql_root.pl"):
                args = public.dict_obj()
                args.table = "config"
                args.id = 1
                args.key = "mysql_root"
                import data
                data.data().getKey(args)
                public.ExecShell("echo 'True' > /www/server/panel/data/remysql_root.pl")
        except:
            pass
        
    def restore_mysql_info(self,db_data):
        try:
            self.init_mysql_root("get")
        except:
            pass
        mysql_obj = db_mysql.panelMysql()
        local_db_info=public.M('databases').where('name=?', (db_data["name"],)).select()
        if not local_db_info:
            args = public.dict_obj()
            args.name = db_data['name']
            args.db_user = db_data['username']
            args.password = db_data['password']
            args.dataAccess = "ip"
            args.address = db_data['accept']
            args.codeing = "utf8mb4"
            args.dtype = "MySQL"
            args.ps = db_data['ps']
            args.sid = "0"
            args.listen_ip = "0.0.0.0/0"
            res = database.database().AddDatabase(args)
            if res['status'] == False:
                print("创建失败啦！！！")
            else:
                print("创建成功啦！！！")
        pass

    def input_mysql_sql(self,db_data):
        db_host = "localhost"
        db_user = "root"
        try:
            db_port = int(panelMysql.panelMysql().query("show global variables like 'port'")[0][1])
        except:
            db_port = 3306

        db_password = public.M("config").where("id=?", (1,)).getField("mysql_root")
        db_name = db_data['name']
        db_charset = public.get_database_character(db_name)
        shell = "'{mysql_bin}' --force --default-character-set='{db_charset}' --host='{db_host}' --port={db_port} --user='{db_user}' --password='{password}' '{db_name}'".format(
        mysql_bin=self._MYSQL_BIN,
        db_charset=db_charset,
        db_host=db_host,
        db_port=db_port,
        db_user=db_user,
        password=db_password,
        db_name=db_name,
        )
        sql_path=db_data['sql_file_name']
        output, error=public.ExecShell("{shell} < '{path}'".format(shell=shell, path=sql_path), env={"MYSQL_PWD": db_password})
        print(output,error)

    def restore_mongodb_info(self,db_data):
        import databaseModel.mongodbModel as panelMongoDB
        local_db_info=public.M('databases').where('name=?', (db_data["name"],)).select()
        if not local_db_info:
            args = public.dict_obj()
            args.name = db_data['name']
            args.db_user =  db_data['username']
            args.password = db_data['password']
            args.dataAccess = db_data['accept']
            args.ps = db_data['ps']
            args.address = ""
            args.codeing = "utf8mb4"
            args.dtype = "MongoDb"
            args.sid = 0
            args.listen_ip = "0.0.0.0/0"
            args.host = ""
            res =  panelMongoDB.main().AddDatabase(args)
            if res['status'] == False:
                print("创建失败啦！！！")
            else:
                print("创建成功啦！！！")
        pass
        

    def restore_mongodb_data(self,db_data):
        # [TECH-DEBT] 调用面板接口导入，非原生
        # 风险：如面板导入异常，可能影响导入失败  
        # 责任人：@mikumiku 到期日：2025-4-30  
        import databaseModel.mongodbModel as panelMongoDB
        db_name = db_data['name']
        sql_path=sql_path=db_data['sql_file_name']
        args = public.dict_obj()
        args.file = sql_path
        args.name = db_name
        res = panelMongoDB.main().InputSql(args)
        if res['status'] == False:
            print("导入失败啦mongo！！！")
        else:
            print("导入成功啦mongo！！！")

    def restore_pgsql_info(self,db_data):
        import databaseModel.pgsqlModel as panelPgsql

        local_db_info=public.M('databases').where('name=?', (db_data["name"],)).select()
        if not local_db_info:
            args = public.dict_obj()
            args.name = db_data['name']
            args.db_user = db_data['username']
            args.password = db_data['password']
            args.ps = db_data['ps']
            args.sid = 0
            args.listen_ip = "0.0.0.0/0"
            args.host = ""
            res = panelPgsql.main().AddDatabase(args)
            if res['status'] == False:
                print("创建失败啦！！！")
            else:
                print("创建成功啦！！！")


    def restore_pgsql_root_pwd(self,pgsql_root_pwd):
        import databaseModel.pgsqlModel as panelPgsql
        args = public.dict_obj()
        args.password = pgsql_root_pwd
        panelPgsql.main().set_root_pwd(args)

    def restore_pgsql_data(self,db_data):
        """还原PostgreSQL数据库
        @param db_data: dict 数据库信息
        """
        try:
            import databaseModel.pgsqlModel as panelPgsql
            if not os.path.exists('/www/server/pgsql/bin/psql'):
                print("缺少恢复工具，请先通过软件管理安装pgsql!")
                return False

            db_name = db_data['name']
            sql_gz_file = db_data['sql_file_name']
            if os.path.exists(sql_gz_file):
                public.ExecShell("gunzip {sql_file}".format(sql_file=sql_gz_file))

            sql_file = sql_gz_file.replace(".gz", "")
            if not os.path.exists(sql_file):
                print("备份文件不存在！")
                return False

            # 获取本地PostgreSQL的配置信息
            t_path = os.path.join('/www/server/panel/data/postgresAS.json')
            if not os.path.isfile(t_path):
                characters = string.ascii_lowercase + string.digits
                pgsql_root_pwd = ''.join(random.choice(characters) for _ in range(16))
                self.restore_pgsql_root_pwd(pgsql_root_pwd)
                print("已设置随机管理员密码")

            db_port = panelPgsql.main().get_port(None)["data"]
            db_password = json.loads(public.readFile(t_path)).get("password", "")

            # 构建psql命令
            shell = "'/www/server/pgsql/bin/psql' --host='127.0.0.1' --port={} --username='postgres' --dbname='{}'".format(
                int(db_port),
                db_name
            )

            # 执行还原命令
            result = public.ExecShell("{} < '{}'".format(shell, sql_file), env={"PGPASSWORD": db_password})
            print(result)
            
            if "ERROR:" in result[0] or "ERROR:" in result[1]:
                print(f"还原数据库失败: {result}")
                return False

            print(f"数据库 {db_name} 还原成功!")
            return True

        except Exception as e:
            print(f"还原数据库失败: {str(e)}")
            return False


    def restore_redis_data(self,db_data):
        try:
            rdb_file=db_data['sql_file_name']
            if os.path.exists(rdb_file):
                if os.path.exists("/www/server/redis/dump.rdb"):
                    self.print_log("开始停止redis服务","restore")
                    public.ExecShell("/etc/init.d/redis stop")
                    time.sleep(1)
                    public.ExecShell("rm -f /www/server/redis/dump.rdb.bak")
                    public.ExecShell("mv /www/server/redis/dump.rdb /www/server/redis/dump.rdb.bak")
                    self.print_log("redis服务停止成功","restore")
                self.print_log("还原redis记录444","restore")
                public.ExecShell("\cp -pra {rdb_file} /www/server/redis/dump.rdb".format(rdb_file=rdb_file))
                public.ExecShell("chown -R redis:redis /www/server/redis")
                public.ExecShell("chmod 644 /www/server/redis/dump.rdb")
                time.sleep(1)
                self.print_log("还原redis记录123","restore")
                public.ExecShell("/etc/init.d/redis start")
        except Exception as e:
            self.print_log("还原redis有问题了{}".format(e),"restore")
            pass



if __name__ == '__main__':
    # 获取命令行参数
    if len(sys.argv) < 3:
        print("Usage: btpython backup_manager.py <method> <timestamp>")
        sys.exit(1)
    method_name = sys.argv[1]  # 方法名
    timestamp = sys.argv[2]    # IP地址     
    database_module = DatabaseModule()  # 实例化对象
    if hasattr(database_module, method_name):  # 检查方法是否存在
        method = getattr(database_module, method_name)  # 获取方法
        method(timestamp)  # 调用方法
    else:
        print(f"Error: 方法 '{method_name}' 不存在")