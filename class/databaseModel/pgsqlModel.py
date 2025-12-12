# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: hezhihong <bt_ahong@qq.com>
# -------------------------------------------------------------------

# ------------------------------
# postgresql模型
# ------------------------------
import os
import re
import json
import time
from typing import Tuple, Union

from databaseModel.base import databaseBase
import public

try:
    from BTPanel import session
except:
    pass
try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except:
    pass


class panelPgsql:
    _CONFIG_PATH = os.path.join(public.get_setup_path(), "pgsql/data/postgresql.conf")

    def __init__(self):
        self.check_package()

        self.__CONN_KWARGS = {
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": None,
            "database": None,
            "connect_timeout": 3,
        }
        self.__DB_CONN = None
        self.__DB_CUR = None

    # 检查python包是否存在
    @classmethod
    def check_package(cls):
        """
        @name检测依赖是否正常
        """
        try:
            import psycopg2
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        except:
            os.system('btpip install psycopg2-binary')
            try:
                import psycopg2
                from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            except:
                return False
        return True

    # 连接PGSQL数据库
    def connect(self) -> Tuple[bool, str]:
        if self.__CONN_KWARGS.get("password") is None:
            if self.__CONN_KWARGS["host"] in ["localhost", "127.0.0.1"] and os.path.exists("/www/server/pgsql/data"):
                self.__CONN_KWARGS["port"] = self.get_config_options("port", int, 5432)
                tmp_args = public.dict_obj()
                tmp_args.is_True = True
                self.__CONN_KWARGS["password"] = main().get_root_pwd(tmp_args)

        try:
            self.__DB_CONN = psycopg2.connect(**self.__CONN_KWARGS)
            self.__DB_CONN.autocommit = True
            self.__DB_CONN.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)  # <-- ADD THIS LINE

            self.__DB_CUR = self.__DB_CONN.cursor()
            return True, "正常"
        except:
            err_msg = public.get_error_info()
            return False, err_msg

    # 设置连接参数
    def set_host(self, *args, **kwargs):
        """
        设置连接参数
        """
        # args 兼容老版本，后续新增禁止使用 args
        if len(args) >= 5:
            kwargs["host"] = args[0]
            kwargs["port"] = args[1]
            kwargs["database"] = args[2]
            kwargs["user"] = args[3]
            kwargs["password"] = args[4]

        if kwargs.get("db_host") is not None:
            kwargs["host"] = kwargs.get("db_host")
        if kwargs.get("db_port") is not None:
            kwargs["port"] = kwargs.get("db_port")
        if kwargs.get("db_name") is not None:
            kwargs["database"] = kwargs.get("db_name")
        if kwargs.get("db_user") is not None:
            kwargs["user"] = kwargs.get("db_user")
        if kwargs.get("db_password") is not None:
            kwargs["password"] = kwargs.get("db_password")
        self.__CONN_KWARGS.update(kwargs)

        if not isinstance(self.__CONN_KWARGS["port"], int):
            self.__CONN_KWARGS["port"] = int(self.__CONN_KWARGS["port"])
        return self

    def execute(self, sql):
        # 执行SQL语句返回受影响行
        if self.__DB_CONN is None:
            status, err_msg = self.connect()
            if status is False:
                return err_msg
        if self.__DB_CONN.closed or self.__DB_CUR.closed:  # 判断是否关闭，关闭重新连接
            status, err_msg = self.connect()
            if status is False:
                return err_msg
        try:
            # print(sql)
            result = self.__DB_CUR.execute(sql)
            self.__DB_CONN.commit()
            self.__Close()
            return result
        except Exception as ex:

            return ex

    def query(self, sql):

        # 执行SQL语句返回数据集
        if self.__DB_CONN is None:
            status, err_msg = self.connect()
            if status is False:
                return err_msg
        if self.__DB_CONN.closed or self.__DB_CUR.closed:  # 判断是否关闭，关闭重新连接
            status, err_msg = self.connect()
            if status is False:
                return err_msg
        try:
            self.__DB_CUR.execute(sql)
            result = self.__DB_CUR.fetchall()

            data = list(map(list, result))
            self.__Close()
            return data
        except Exception as ex:
            return ex

    def use_database(self, database_name):
        """
        切换到指定数据库
        @param database_name: 数据库名称
        @return: Tuple[bool, str] (成功状态, 消息)
        """
        # 如果已经有连接，先关闭
        if self.__DB_CONN is not None and not self.__DB_CONN.closed:
            self.__Close()
        
        # 更新数据库名称
        self.__CONN_KWARGS["database"] = database_name
        
        # 重新连接
        return self.connect()

    # 关闭连接
    def __Close(self):
        self.__DB_CUR.close()
        self.__DB_CONN.close()

    # 获取未注释的配置文件参数
    @classmethod
    def get_config_options(cls, name: str, value_type: type, default=None):
        """
        获取未注释的配置文件参数
        name: 参数名称
        value_type: 参数类型
        """
        conf_data = public.readFile(cls._CONFIG_PATH)
        if not conf_data:
            public.ExecShell("/www/server/pgsql/data/postgresql.conf  /www/server/pgsql/data/postgresql.bak")
            public.ExecShell("wget -O /www/server/pgsql/data/postgresql.conf https://download.bt.cn/conf/postgresql.conf;chmod 600 /www/server/pgsql/data/postgresql.conf;chown postgres:postgres /www/server/pgsql/data/postgresql.conf")
            time.sleep(2)
            conf_data = public.readFile(cls._CONFIG_PATH)

        if conf_data is None or not isinstance(conf_data, str):
            # 文件不存在或读取出错时，设置conf_data为默认空字符串
            conf_data = ""
        elif not conf_data.endswith("\n"):
            conf_data += "\n"

        re_type_dict = {
            str: "([^\n]*)",
            int: "(\d+)",
            bool: "(on|off)",
        }
        re_str = re_type_dict.get(value_type, "([^\n]*)")

        conf_obj = re.search(r"\n{}\s*=\s*{}".format(name, re_str), conf_data)
        if conf_obj:
            value = conf_obj.group(1)
            value = value.strip()
            if value_type == bool:
                value = value == "on"
            else:
                value = value_type(value)
            return value

        if default is not None:
            if isinstance(default, value_type):
                return default
            elif value_type == bool:
                default = default == "on"
            else:
                default = value_type(default)
            return default
        return None


class main(databaseBase, panelPgsql):
    _DB_BACKUP_DIR = os.path.join(public.M("config").where("id=?", (1,)).getField("backup_path"), "database")
    _PGSQL_BACKUP_DIR = os.path.join(_DB_BACKUP_DIR, "pgsql")
    _PGDUMP_BIN = os.path.join(public.get_setup_path(), "pgsql/bin/pg_dump")
    _PSQL_BIN = os.path.join(public.get_setup_path(), "pgsql/bin/psql")

    __ser_name = None
    __soft_path = '/www/server/pgsql'
    __setup_path = '/www/server/panel/'
    __dbuser_info_path = "{}plugin/pgsql_manager_dbuser_info.json".format(__setup_path)
    __plugin_path = "{}plugin/pgsql_manager/".format(__setup_path)

    def __init__(self):
        if not os.path.exists(self._PGSQL_BACKUP_DIR):
            os.makedirs(self._PGSQL_BACKUP_DIR,exist_ok=True)

        s_path = public.get_setup_path()
        v_info = public.readFile("{}/pgsql/version.pl".format(s_path))
        if v_info:
            ver = v_info.split('.')[0]
            self.__ser_name = 'postgresql-x64-{}'.format(ver)
            self.__soft_path = '{}/pgsql/{}'.format(s_path)

    # 获取配置项
    def get_options(self, get):
        data = {}
        options = ['port', 'listen_addresses']
        if not self.__soft_path: self.__soft_path = '{}/pgsql'.format(public.get_setup_path())
        conf = public.readFile('{}/data/postgresql.conf'.format(self.__soft_path))
        for opt in options:
            tmp = re.findall("\s+" + opt + "\s*=\s*(.+)#", conf)
            if not tmp: continue
            data[opt] = tmp[0].strip()
            if opt == 'listen_addresses':
                data[opt] = data[opt].replace('\'', '')
        data['password'] = self.get_root_pwd(None)['msg']
        return data

    def get_list(self,args):
        """
        @获取数据库列表
        @sql_type = pgsql
        """
        # 获取基础数据库列表
        base_list = self.get_base_list(args, sql_type = 'pgsql')

        # 检查文件是否存在
        if os.path.exists('/www/server/pgsql/data/pg_hba.conf'):
            # 读取 pg_hba.conf 文件
            with open('/www/server/pgsql/data/pg_hba.conf', 'r') as file:
                lines = file.readlines()

            # 遍历数据库列表
            for db in base_list['data']:
                # 遍历 pg_hba.conf 文件的每一行
                for line in lines:
                    # 如果这一行精确匹配数据库名
                    if re.search(r'\b' + db['name'] + r'\b', line):
                        # 提取访问权限
                        listen_ip = line.split()[-2]
                        # 更新数据库的访问权限
                        db.update({'listen_ip': listen_ip})
                        break
        return base_list

    def get_sql_obj_by_sid(self, sid: Union[int, str] = 0, conn_config=None):
        """
        @取pgsql数据库对像 By sid
        @sid 数据库分类，0：本地
        """
        if isinstance(sid, str):
            sid = int(sid)

        if sid:
            if not conn_config: conn_config = public.M('database_servers').where("id=? AND LOWER(db_type)=LOWER('pgsql')", sid).find()
            db_obj = panelPgsql()

            try:
                db_obj = db_obj.set_host(host=conn_config["db_host"], port=conn_config["db_port"], database=None, user=conn_config["db_user"], password=conn_config["db_password"])
            except Exception as e:
                raise public.PanelError(e)
        else:
            db_obj = panelPgsql()
        return db_obj

    def get_sql_obj(self, db_name):
        """
        @取pgsql数据库对象
        @db_name 数据库名称
        """
        is_cloud_db = False
        if db_name:
            db_find = public.M('databases').where("name=? AND LOWER(type)=LOWER('PgSql')", db_name).find()
            if db_find['sid']:
                return self.get_sql_obj_by_sid(db_find['sid'])
            is_cloud_db = db_find['db_type'] in ['1', 1]

        if is_cloud_db:

            db_obj = panelPgsql()
            conn_config = json.loads(db_find['conn_config'])
            try:
                db_obj = db_obj.set_host(host=conn_config["db_host"], port=conn_config["db_port"], database=conn_config["db_name"], user=conn_config["db_user"], password=conn_config["db_password"])
            except Exception as e:
                raise public.PanelError(e)
        else:
            db_obj = panelPgsql()
        return db_obj

    def GetCloudServer(self, args):
        '''
            @name 获取远程服务器列表
            @author hwliang<2021-01-10>
            @return list
        '''
        check_result = os.system('/www/server/pgsql/bin/psql --version')
        if check_result != 0 and not public.M('database_servers').where("LOWER(db_type)=LOWER('pgsql')", ()).count(): return []
        return self.GetBaseCloudServer(args)

    def AddCloudServer(self, args):
        '''
        @添加远程数据库
        '''
        return self.AddBaseCloudServer(args)

    def RemoveCloudServer(self, args):
        '''
        @删除远程数据库
        '''
        return self.RemoveBaseCloudServer(args)

    def ModifyCloudServer(self, args):
        '''
        @修改远程数据库
        '''
        return self.ModifyBaseCloudServer(args)

    def GetMainVersion(self,args):
        '''
        @获取主版本号
        '''
        if not os.path.exists('/www/server/pgsql/bin/psql'):
            return 0
        cli_version_result = public.ExecShell('/www/server/pgsql/bin/psql --version')
        try:
            major_version = int(cli_version_result[0].strip('\n').split(' ')[-1].split('.')[0])
        except:
            return 0
        return major_version

    def AddPluginDatabaseConf(self,database,username,password,listen_ip):
        """
        @添加插件数据库配置
        @database 数据库名称
        @username 用户名
        @password 密码
        @listen_ip 监听ip
        """

        dbuser_info_path = "/www/server/panel/plugin/pgsql_manager_dbuser_info.json"
        dbuser_info_str = public.ReadFile(dbuser_info_path)
        dbuser_info_list = []
        
        if dbuser_info_str:
            for line in dbuser_info_str.strip().split('\n'):
                if line.strip():
                    item = json.loads(line)
                    if item['database'] == database:
                        return public.returnMsg(False, '数据库已存在')
                    dbuser_info_list.append(item)
        
        dbuser_info_list.append({'database': database, 'username': username, 'password': password, 'listen_ip': listen_ip})
        
        jsonl_content = '\n'.join([json.dumps(item) for item in dbuser_info_list])
        public.WriteFile(dbuser_info_path, jsonl_content, mode='w')

    def DeletePluginDatabaseConf(self,database):
        """
        @删除插件数据库配置
        @database 数据库名称
        """
        dbuser_info_path = "/www/server/panel/plugin/pgsql_manager_dbuser_info.json"
        dbuser_info_str = public.ReadFile(dbuser_info_path)
        dbuser_info_list = []
        
        if dbuser_info_str:
            for line in dbuser_info_str.strip().split('\n'):
                if line.strip():
                    item = json.loads(line)
                    if item['database'] != database:
                        dbuser_info_list.append(item)
        
        if dbuser_info_list:
            jsonl_content = '\n'.join([json.dumps(item) for item in dbuser_info_list])
            public.WriteFile(dbuser_info_path, jsonl_content, mode='w')
        else:
            public.WriteFile(dbuser_info_path, '', mode='w')
    
    def AddDatabase(self, args):
        """
        @添加数据库
        """
        if not hasattr(args, "name"):
            return public.returnMsg(False, "缺少参数！name")
        if not hasattr(args, "sid"):
            return public.returnMsg(False, "缺少参数！sid")

        db_name = args.name
        sid = args.sid

        if re.search(r"\W", db_name):
            return public.returnMsg(False, "数据库名不能包含特殊字符，请重新设置")
        if not str(sid).isdigit():
            return public.returnMsg(False, "参数错误！sid")
        sid = int(sid)

        dtype = "pgsql"
        res = self.add_base_database(args, dtype)
        if not res['status']: return res

        data_name = res['data_name']
        username = res['username']
        password = res['data_pwd']
        listen_ip= args.listen_ip
        # 添加对 listen_ip 的格式检查
        if not re.match(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}\b", listen_ip):
            return public.returnMsg(False, "ip格式错误！")

        pgsql_obj = self.get_sql_obj_by_sid(sid)
        status, err_msg = pgsql_obj.connect()
        if status is False:
            return public.returnMsg(False, "连接数据库失败！")
        result = pgsql_obj.execute("""CREATE DATABASE "{}";""".format(data_name))
        isError = self.IsSqlError(result)
        if isError != None: return isError
        if str(result).find("permission denied to create database") != -1:
            return public.returnMsg(False, "创建数据库权限拒绝！")

        # 添加用户
        self.__CreateUsers(sid, data_name, username, password, '127.0.0.1')

        if not hasattr(args, 'ps'): args['ps'] = public.getMsg('INPUT_PS')
        addTime = time.strftime('%Y-%m-%d %X', time.localtime())

        pid = 0
        if hasattr(args, 'pid'): pid = args.pid

        if hasattr(args, 'contact'):
            site = public.M('sites').where("id=?", (args.contact,)).field('id,name').find()
            if site:
                pid = int(args.contact)
                args['ps'] = site['name']

        db_type = 0
        if sid: db_type = 2

        public.set_module_logs('pgsql', 'AddDatabase', 1)
        # 添加入SQLITE
        public.M('databases').add('pid,sid,db_type,name,username,password,accept,ps,addtime,type', (pid, sid, db_type, data_name, username, password, '127.0.0.1', args['ps'], addTime, dtype))
        public.WriteLog("TYPE_DATABASE", 'DATABASE_ADD_SUCCESS', (data_name,))
        # 添加访问权限
        config_file_path = self.get_data_directory(args)['data'] + "/pg_hba.conf"
        public.WriteFile(config_file_path.strip(), "\nhost    {}  {}    {}    md5".format(data_name, username, listen_ip), mode='a')
        public.ExecShell("/etc/init.d/pgsql reload")
        try:
            self.AddPluginDatabaseConf(data_name, username, password, listen_ip)
        except:
            pass
        return public.returnMsg(True, 'ADD_SUCCESS')

    def get_data_directory(self, args):  # 获取储存路径
        if os.path.isfile("/www/server/pgsql/data_directory"):
            data_directory = public.ReadFile("/www/server/pgsql/data_directory", mode='r')
        else:
            data_directory = "/www/server/pgsql/data"
        # 返回数据到前端
        return {'data': data_directory.strip(), "status": True}
    
    def processing_parameter(self, args):  # 处理前端传过来的参数
        if 'p' not in args: args.p = 1
        if 'rows' not in args: args.rows = 12
        if 'callback' not in args: args.callback = ''
        args.p = int(args.p)
        args.rows = int(args.rows)
        return args
        
    def modify_pgsql_listen_ip(self,args):  # 修改pgsql用户访问权限
        try:
            args = self.processing_parameter(args)  # 处理前端传过来的参数
            print(args)
            print(222)
            username =args.username
            print(username)
            listen_ip = args.listen_ip 
            database=args.data_name
            if not re.match(r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}/\d+", listen_ip.strip()):
                return {'data': "你输入的不合法，修改失败", "status": False}
            pgsql_conf_path = '/www/server/pgsql/data/postgresql.conf'  
            # pgsql_conf_path = os.path.join(self.get_data_directory(args)['data'], "postgresql.conf").strip()
            pgsql_conf = public.ReadFile(pgsql_conf_path)
            # pgsql_conf = re.sub(r"(#?\s*listen_addresses\s*=\s*)'.*'", r"\1'*'", pgsql_conf)
            pgsql_conf = re.sub(r"(#?\s*listen_addresses\s*=\s*)'.*'", r"listen_addresses = '*'", pgsql_conf)
            public.WriteFile(pgsql_conf_path, pgsql_conf)
            # dbuser_info_path = self.dbuser_info_path
            # dbuser_info_str = ''
            # if os.path.isfile(dbuser_info_path):
            #     with open(dbuser_info_path) as f:
            #         for i in f:
            #             if not i.strip(): continue
            #             item = json.loads(i)
            #             if item['username'] == username:
            #                 item['listen_ip'] = listen_ip
            #                 database = item['database']
            #                 dbuser_info_str += json.dumps(item) + '\n'
            #                 continue
            #             dbuser_info_str += i
            # public.WriteFile(dbuser_info_path, dbuser_info_str, mode='w')
            config_file_path = os.path.join(self.get_data_directory(args)['data'], "pg_hba.conf").strip()
            con_str = public.ReadFile(config_file_path).strip() + '\n'
            head_index = '# PostgreSQL Client Authentication Configuration File'
            tmp_1 = re.search(head_index + r"(\n|.)+" + head_index, con_str)
            if tmp_1:
                con_str = con_str.replace(tmp_1.group(), head_index)
            tmp = re.search(r"(host\s+"+database+r"\s+"+username+r"\s+[\d\./]+\s+\w+)", con_str)
            host_str = "host    {}   {}    {}    md5\n".format(database, username, listen_ip)
            if tmp:
                sub_str = tmp.group()
                con_str = con_str.replace(sub_str,host_str).strip()
            else:
                con_str = con_str.strip()
                con_str += "\n" + host_str
            public.WriteFile(config_file_path, con_str.replace('\n\nhost', '\nhost').strip() + '\n')
            public.ExecShell("/etc/init.d/pgsql reload")
            # 返回数据到前端
            return {"status": True,'msg': "修改pgsql用户访问权限成功", }
        except Exception as e:
            return public.returnMsg(False,str(e))

    def DeleteDatabase(self, get):
        """
        @删除数据库
        """
        id = get['id']
        find = public.M('databases').where("id=? AND LOWER(type)=LOWER('PgSql')", (id,)).field('id,pid,name,username,password,accept,ps,addtime,db_type,conn_config,sid,type').find()
        if not find: return public.returnMsg(False, '指定数据库不存在.')

        name = get['name']
        username = find['username']

        pgsql_obj = self.get_sql_obj_by_sid(find['sid'])
        status, err_msg = pgsql_obj.connect()
        if status is False:
            return public.returnMsg(False, "连接数据库失败！")

        # 查询当前数据是否被连接
        data_list = pgsql_obj.query("""SELECT * FROM pg_stat_activity WHERE datname = '{}';""".format(name))
        if data_list:
            return public.returnMsg(False, "删除失败！当前数据库正在连接中！")
        resp = pgsql_obj.execute("""DROP DATABASE "{}";""".format(name))
        if resp is not None:
            return public.returnMsg(False, "删除数据库失败！")
        pgsql_obj.execute("""DROP USER "{}";""".format(username))
        # 删除SQLITE
        public.M('databases').where("id=? AND LOWER(type)=LOWER('PgSql')", (id,)).delete()
        public.WriteLog("TYPE_DATABASE", 'DATABASE_DEL_SUCCESS', (name,))

        #删除配置文件中的数据库配置
        try:
            self.DeletePluginDatabaseConf(name)
        except:
            pass
        return public.returnMsg(True, 'DEL_SUCCESS')

    def ToBackup(self, args):
        """
        @备份数据库 id 数据库id
        """
        if not os.path.exists(self._PGDUMP_BIN):
            return public.returnMsg(False, '缺少备份工具，请先通过软件商店pgsql管理器!')

        if not hasattr(args, "id"):
            return public.returnMsg(False, "缺少参数！id")
        db_id = args.id
        table_list = getattr(args, "table_list", [])
        storage_type = getattr(args, "storage_type", "db")

        if storage_type not in ["db", "table"]:
            return public.returnMsg(False, "参数错误！storage_type")

        db_find = public.M('databases').where("id=? AND LOWER(type)=LOWER('pgsql')", (db_id,)).find()
        if not db_find: return public.returnMsg(False, '数据库不存在!')

        if not db_find["password"].strip():
            return public.returnMsg(False, '数据库密码为空，请先设置密码.')

        db_name = db_find["name"]

        db_user = "postgres"
        db_host = "127.0.0.1"
        if db_find["db_type"] == 0:
            db_port = panelPgsql.get_config_options("port", int, 5432)

            t_path = os.path.join(public.get_panel_path(), "data/postgresAS.json")
            if not os.path.isfile(t_path):
                return public.returnMsg(False, "请先设置管理员密码！")
            db_password = json.loads(public.readFile(t_path)).get("password", "")
            if not db_password:
                return public.returnMsg(False, "数据库密码为空！请先设置数据库密码！")
        elif db_find["db_type"] == 1:
            # 远程数据库
            conn_config = json.loads(db_find["conn_config"])
            db_host = conn_config["db_host"]
            db_port = conn_config["db_port"]
            db_user = conn_config["db_user"]
            db_password = conn_config["db_password"]
        elif db_find["db_type"] == 2:
            conn_config = public.M("database_servers").where("id=? AND LOWER(db_type)=LOWER('pgsql')", db_find["sid"]).find()
            db_host = conn_config["db_host"]
            db_port = conn_config["db_port"]
            db_user = conn_config["db_user"]
            db_password = conn_config["db_password"]
        else:
            return public.returnMsg(False, "未知的数据库类型")

        pgsql_obj = panelPgsql().set_host(host=db_host, port=db_port, database=None, user=db_user, password=db_password)
        status, err_msg = pgsql_obj.connect()
        if status is False:
            return public.returnMsg(False, "连接数据库[{}:{}]失败".format(db_host, int(db_port)))

        db_backup_dir = os.path.join(self._PGSQL_BACKUP_DIR, db_name)
        if not os.path.exists(db_backup_dir):
            os.makedirs(db_backup_dir)

        file_name = "{db_name}_{backup_time}_pgsql_data".format(db_name=db_name, backup_time=time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()))
        # backup_path = os.path.join(self._PGSQL_BACKUP_DIR, file_name)

        shell = "'{pgdump_bin}' --host='{db_host}' --port={db_port} --username='{db_user}' --dbname='{db_name}' --clean".format(
            pgdump_bin=self._PGDUMP_BIN,
            db_host=db_host,
            db_port=int(db_port),
            db_user=db_user,
            db_name=db_name,
        )

        backup_ps = "手动备份"
        if storage_type == "db":  # 导出单个文件
            file_name = file_name + ".sql.gz"
            backup_path = os.path.join(db_backup_dir, file_name)
            table_shell = ""
            if len(table_list) != 0:
                backup_ps += "-合并导出"
                table_shell = "--table='" + "' --table='".join(table_list) + "'"
            shell += " {table_shell} | gzip > '{backup_path}'".format(table_shell=table_shell, backup_path=backup_path)
            public.ExecShell(shell, env={"PGPASSWORD": db_password})
        else:  # 按表导出
            backup_ps += "-分表导出"
            export_dir = os.path.join(db_backup_dir, file_name)
            if not os.path.isdir(export_dir):
                os.makedirs(export_dir)

            for table_name in table_list:
                tb_backup_path = os.path.join(export_dir, "{table_name}.sql".format(table_name=table_name))
                tb_shell = shell + " --table='{table_name}' > '{tb_backup_path}'".format(table_name=table_name, tb_backup_path=tb_backup_path)
                public.ExecShell(tb_shell, env={"PGPASSWORD": db_password})
            backup_path = "{export_dir}.zip".format(export_dir=export_dir)
            public.ExecShell("cd '{backup_dir}' && zip -m '{backup_path}' -r '{file_name}'".format(backup_dir=db_backup_dir, backup_path=backup_path, file_name=file_name))
            if not os.path.exists(backup_path):
                public.ExecShell("rm -rf {}".format(export_dir))

        if not os.path.exists(backup_path):
            return public.returnMsg(False, '数据库备份失败，导出文件不存在!')

        addTime = time.strftime('%Y-%m-%d %X', time.localtime())
        backup_size = os.path.getsize(backup_path)
        public.M('backup').add('type,name,pid,filename,size,addtime,ps', (1, os.path.basename(backup_path), db_id, backup_path, backup_size, addTime, backup_ps))
        public.WriteLog("TYPE_DATABASE", "DATABASE_BACKUP_SUCCESS", (db_find['name'],))
        if backup_size < 2048:
            return public.returnMsg(True, '备份执行成功，备份文件小于2Kb，请检查备份完整性.')
        else:
            return public.returnMsg(True, 'BACKUP_SUCCESS')

    # 导入数据库备份
    def InputSql(self, get):
        """
        导入数据库备份
        """
        if not os.path.exists(self._PSQL_BIN):
            return public.returnMsg(False, "缺少恢复工具，请先通过软件管理安装pgsql!")

        if not hasattr(get, "name"):
            return public.returnMsg(False, "缺少参数！name")
        if not hasattr(get, "file"):
            return public.returnMsg(False, "缺少参数！file")

        db_name = get.name
        file = get.file
        if not os.path.exists(file): return public.returnMsg(False, "导入路径不存在!")
        if not os.path.isfile(file): return public.returnMsg(False, "仅支持导入压缩文件!")

        file_name = os.path.basename(file)
        ext_list = ["sql", "tar.gz", "gz", "zip"]
        ext_tmp = file_name.split(".")
        file_ext = ".".join(ext_tmp[1:])
        ext_temp = [ext.lower() for ext in ext_list if ext.lower() in file_ext]
        if len(ext_temp) == 0:
            return public.returnMsg(False, "请选择sql、tar.gz、gz、zip文件格式!")

        db_find = public.M('databases').where("name=? AND LOWER(type)=LOWER('PgSql')", (db_name,)).find()
        if not db_find: return public.returnMsg(False, '数据库不存在!')

        if not db_find["password"].strip():
            return public.returnMsg(False, '数据库密码为空，请先设置密码.')

        # 解压
        input_dir = os.path.join(self._PGSQL_BACKUP_DIR, db_name, "input_tmp_{}".format(int(time.time() * 1000_000)))

        is_zip = False
        if "zip" in file_ext:
            if not os.path.isdir(input_dir): os.makedirs(input_dir)
            public.ExecShell("unzip -o '{file}' -d '{input_dir}'".format(file=file, input_dir=input_dir))
            is_zip = True
        elif "tar.gz" in file_ext:
            if not os.path.isdir(input_dir): os.makedirs(input_dir)
            public.ExecShell("tar zxf '{file}' -C '{input_dir}'".format(file=file, input_dir=input_dir))
            is_zip = True
        elif "gz" in file_ext:
            if not os.path.isdir(input_dir): os.makedirs(input_dir)
            temp_file = os.path.join(input_dir, file_name)
            public.ExecShell("cp '{file}' '{temp_file}' && gunzip -q '{temp_file}'".format(file=file, temp_file=temp_file))
            is_zip = True

        input_path_list = []
        if is_zip is True:  # 遍历临时目录
            for name in os.listdir(input_dir):
                path = os.path.join(input_dir, name)
                if os.path.isfile(path) and str(path).endswith(".sql"):
                    input_path_list.append(path)
                elif os.path.isdir(path):
                    for t_name in os.listdir(path):
                        t_path = os.path.join(path, t_name)
                        if os.path.isfile(t_path) and str(t_path).endswith(".sql"):
                            input_path_list.append(t_path)
        else:
            input_path_list.append(file)

        db_name = db_find["name"]

        db_user = "postgres"
        db_host = "127.0.0.1"
        if db_find["db_type"] == 0:
            args_one = public.dict_obj()
            db_port = self.get_port(args_one)["data"]
            t_path = os.path.join(public.get_panel_path(), "data/postgresAS.json")
            if not os.path.isfile(t_path):
                return public.returnMsg(False, "请先设置管理员密码！")
            db_password = json.loads(public.readFile(t_path)).get("password", "")
        elif db_find["db_type"] == 1:
            # 远程数据库
            conn_config = json.loads(db_find["conn_config"])
            db_host = conn_config["db_host"]
            db_port = conn_config["db_port"]
            db_user = conn_config["db_user"]
            db_password = conn_config["db_password"]
        elif db_find["db_type"] == 2:
            conn_config = public.M("database_servers").where("id=? AND LOWER(db_type)=LOWER('pgsql')", db_find["sid"]).find()
            db_host = conn_config["db_host"]
            db_port = conn_config["db_port"]
            db_user = conn_config["db_user"]
            db_password = conn_config["db_password"]
        else:
            return public.returnMsg(False, "未知的数据库类型")

        shell = "'{psql_bin}' --host='{db_host}' --port={db_port} --username='{db_user}' --dbname='{db_name}'".format(
            psql_bin=self._PSQL_BIN,
            db_host=db_host,
            db_port=int(db_port),
            db_user=db_user,
            db_name=db_name,
        )
        for path in input_path_list:
            public.ExecShell("{shell} < '{path}'".format(shell=shell, path=path), env={"PGPASSWORD": db_password})
        # 清理导入临时目录
        if is_zip is True:
            public.ExecShell("rm -rf '{input_dir}'".format(input_dir=input_dir))
        public.WriteLog("TYPE_DATABASE", '导入数据库[{}]成功'.format(db_name))
        return public.returnMsg(True, 'DATABASE_INPUT_SUCCESS')

    # 获取备份文件
    def GetBackup(self, get):
        p = getattr(get, "p", 1)
        limit = getattr(get, "limit", 10)
        return_js = getattr(get, "return_js", "")
        search = getattr(get, "search", None)

        if not str(p).isdigit():
            return public.returnMsg(False, "参数错误！p")
        if not str(limit).isdigit():
            return public.returnMsg(False, "参数错误！limit")

        p = int(p)
        limit = int(limit)

        ext_list = ["sql", "tar.gz", "gz", "zip"]

        backup_list = []

        # 递归获取备份文件
        def get_dir_backup(backup_dir: str, backup_list: list, is_recursion: bool):
            for name in os.listdir(backup_dir):
                path = os.path.join(backup_dir, name)
                if os.path.isfile(path):
                    ext = name.split(".")[-1]
                    if ext.lower() not in ext_list: continue
                    if search is not None and search not in name: continue

                    stat_file = os.stat(path)
                    path_data = {
                        "name": name,
                        "path": path,
                        "size": stat_file.st_size,
                        "mtime": int(stat_file.st_mtime),
                        "ctime": int(stat_file.st_ctime),
                    }
                    backup_list.append(path_data)
                elif os.path.isdir(path) and is_recursion is True:
                    get_dir_backup(path, backup_list, is_recursion)

        get_dir_backup(self._PGSQL_BACKUP_DIR, backup_list, True)
        get_dir_backup(self._DB_BACKUP_DIR, backup_list, False)

        try:
            from flask import request
            uri = public.url_encode(request.full_path)
        except:
            uri = ''
        # 包含分页类
        import page
        # 实例化分页类
        page = page.Page()
        info = {
            "p": p,
            "count": len(backup_list),
            "row": limit,
            "return_js": return_js,
            "uri": uri,
        }
        page_info = page.GetPage(info)

        start_idx = (int(p) - 1) * limit
        end_idx = p * limit if p * limit < len(backup_list) else len(backup_list)
        backup_list.sort(key=lambda data: data["mtime"], reverse=True)
        backup_list = backup_list[start_idx:end_idx]
        return {"status": True, "msg": "OK", "data": backup_list, "page": page_info}

    def DelBackup(self, args):
        """
        @删除备份文件
        """
        return self.delete_base_backup(args)

    def get_port(self, args):  # 获取端口号
        str_shell = '''netstat -luntp|grep postgres|head -1|awk '{print $4}'|awk -F: '{print $NF}' '''
        try:
            port = public.ExecShell(str_shell)[0]
            if port.strip():
                return {'data': port.strip(), "status": True}
            else:
                return {'data': 5432, "status": False}
        except:
            return {'data': 5432, "status": False}

    def SyncToDatabases(self, get):
        """
        @name同步数据库到服务器
        """
        tmp_type = int(get['type'])
        n = 0
        sql = public.M('databases')
        if tmp_type == 0:
            # data = sql.field('id,name,username,password,accept,type,sid,db_type').where('type=?',('pgsql',)).select()
            data = sql.field('id,name,username,password,accept,type,sid,db_type').where("LOWER(type)=LOWER('PgSql')", ()).select()

            for value in data:
                if value['db_type'] in ['1', 1]:
                    continue  # 跳过远程数据库
                result = self.ToDataBase(value)
                if result == 1: n += 1
        else:
            import json
            data = json.loads(get.ids)
            for value in data:
                find = sql.where("id=?", (value,)).field('id,name,username,password,sid,db_type,accept,type').find()
                result = self.ToDataBase(find)
                if result == 1: n += 1
        if n == 1:
            return public.returnMsg(True, '同步成功')
        elif n == 0:
            return public.returnMsg(False, '同步失败')
        return public.returnMsg(True, 'DATABASE_SYNC_SUCCESS', (str(n),))

    def ToDataBase(self, find):
        """
        @name 添加到服务器
        """
        if find['username'] == 'bt_default': return 0
        if len(find['password']) < 3:
            find['username'] = find['name']
            find['password'] = public.md5(str(time.time()) + find['name'])[0:10]
            public.M('databases').where("id=? AND LOWER(type)=LOWER('PgSql')", (find['id'],)).save('password,username', (find['password'], find['username']))

        sid = find['sid']
        pgsql_obj = self.get_sql_obj_by_sid(sid)
        status, err_msg = pgsql_obj.connect()
        if status is False:
            return public.returnMsg(False, "连接数据库失败！")

        result = pgsql_obj.execute("""CREATE DATABASE "{}";""".format(find['name']))
        isError = self.IsSqlError(result)
        if isError != None and isError['status'] == False and isError['msg'] == '指定数据库已存在，请勿重复添加.': return 1

        self.__CreateUsers(sid, find['name'], find['username'], find['password'], '127.0.0.1')

        return 1

    def SyncGetDatabases(self, get):
        """
        @name 从服务器获取数据库
        @param sid 0为本地数据库 1为远程数据库
        """
        n = 0
        s = 0
        db_type = 0
        sid = get.get('sid/d', 0)
        if sid: db_type = 2

        pgsql_obj = self.get_sql_obj_by_sid(sid)
        status, err_msg = pgsql_obj.connect()
        if status is False:
            return public.returnMsg(False, "连接数据库失败！")

        data = pgsql_obj.query('SELECT datname FROM pg_database;')  # select * from pg_database order by datname
        isError = self.IsSqlError(data)
        if isError != None: return isError
        if type(data) == str: return public.returnMsg(False, data)

        sql = public.M('databases')
        nameArr = ['information_schema', 'postgres', 'template1', 'template0', 'performance_schema', 'mysql', 'sys', 'master', 'model', 'msdb', 'tempdb', 'ReportServerTempDB', 'YueMiao', 'ReportServer']
        for item in data:
            dbname = item[0]
            if dbname in nameArr: continue

            if sql.where("name=? AND LOWER(type)=LOWER('PgSql')", (dbname,)).count(): continue
            if public.M('databases').add('name,username,password,accept,ps,addtime,type,sid,db_type', (dbname, dbname, "", "", public.getMsg('INPUT_PS'), time.strftime('%Y-%m-%d %X', time.localtime()), 'PgSql', sid, db_type)): n += 1

        return public.returnMsg(True, 'DATABASE_GET_SUCCESS', (str(n),))

    def ResDatabasePassword(self, args):
        """
        @修改用户密码
        """
        id = args['id']
        username = args['name'].strip()
        newpassword = public.trim(args['password'])
        if not newpassword: return public.returnMsg(False, '修改失败，数据库密码不能为空.')

        find = public.M('databases').where("id=? AND LOWER(type)=LOWER('PgSql')", (id,)).field('id,pid,name,username,password,type,accept,ps,addtime,sid').find()
        if not find: return public.returnMsg(False, '修改失败，指定数据库不存在.')

        pgsql_obj = self.get_sql_obj_by_sid(find['sid'])
        status, err_msg = pgsql_obj.connect()
        if status is False:
            return public.returnMsg(False, "连接数据库失败！")

        data = pgsql_obj.query('SELECT rolname FROM pg_roles;')
        if username not in data:
            # 添加用户
            result = self.__CreateUsers(find['sid'], username, username, newpassword, "127.0.0.0.1")
        else:
            result = pgsql_obj.execute("""ALTER USER "{}" with password '{}';""".format(username, newpassword))
        isError = self.IsSqlError(result)
        if isError != None: return isError

        # 修改SQLITE
        public.M('databases').where("id=? AND LOWER(type)=LOWER('PgSql')", (id,)).setField('password', newpassword)

        public.WriteLog("TYPE_DATABASE", 'DATABASE_PASS_SUCCESS', (find['name'],))
        return public.returnMsg(True, 'DATABASE_PASS_SUCCESS', (find['name'],))

    def get_root_pwd(self, args):
        """
        @获取sa密码
        """
        # check_result = os.system('/www/server/pgsql/bin/psql1 --version')
        if not os.path.exists("/www/server/pgsql/bin/psql"): return public.returnMsg(False, '检测到PgSQL未安装或未启动，请先安装或启动')
        password = ''
        path = '{}/data/postgresAS.json'.format(public.get_panel_path())
        if os.path.isfile(path):
            try:
                password = json.loads(public.readFile(path))['password']
                # print('333333333')
                # print(password)
            except:
                pass
        if 'is_True' in args and args.is_True: return password
        return public.returnMsg(True, password)

    def set_root_pwd(self, args):
        """
        @设置sa密码
        """
        password = public.trim(args['password'])
        if len(password) < 8: return public.returnMsg(False, '密码输入错误，不能少于8位数.')
        check_result = os.system('/www/server/pgsql/bin/psql --version')
        if check_result != 0: return public.returnMsg(False, '检测到PgSQL未安装或未启动，请先安装或启动')
        pgsql_obj = self.get_sql_obj_by_sid('0')
        status, err_msg = pgsql_obj.connect()
        if status is False:
            return public.returnMsg(False, "连接数据库失败！")

        data = pgsql_obj.query('SELECT datname FROM pg_database;')
        isError = self.IsSqlError(data)
        if isError != None: return isError

        path = '{}/data/pg_hba.conf'.format(self.__soft_path)
        p_path = '{}/data/postgresAS.json'.format(public.get_panel_path())
        if not os.path.isfile(path): return public.returnMsg(False, '{}文件不存在，请检查安装是否完整！'.format(path))
        src_conf = public.readFile(path)
        add_conf = src_conf.replace('md5', 'trust')
        # public.writeFile(path,public.readFile(path).replace('md5','trust'))
        public.writeFile(path, add_conf)

        pg_obj = panelPgsql()
        pg_obj.execute("""ALTER USER "postgres" WITH PASSWORD '{}';""".format(password))
        data = {"username": "postgres", "password": ""}
        try:
            data = json.loads(public.readFile(p_path))
        except:
            pass
        data['password'] = password
        public.writeFile(p_path, json.dumps(data))
        public.writeFile(path, src_conf)
        return public.returnMsg(True, '管理员密码修改成功.')

    def get_info_by_db_id(self, db_id):
        """
        @获取数据库连接详情
        @db_id 数据库id
        """
        # print(db_id,'111111111111')
        find = public.M('databases').where("id=? AND LOWER(type)=LOWER('pgsql')", db_id).find()
        # return find
        if not find: return False
        # print(find)
        if find["db_type"] == 1:
            # 远程数据库
            conn_config = json.loads(find["conn_config"])
            db_host = conn_config["db_host"]
            db_port = conn_config["db_port"]
            db_user = conn_config["db_user"]
            db_password = conn_config["db_password"]
        elif find["db_type"] == 2:
            conn_config = public.M("database_servers").where("id=? AND LOWER(db_type)=LOWER('pgsql')", find["sid"]).find()
            db_host = conn_config["db_host"]
            db_port = conn_config["db_port"]
            db_user = conn_config["db_user"]
            db_password = conn_config["db_password"]
        else:  # 本地数据库
            db_host = '127.0.0.1'
            args_one = public.dict_obj()
            db_port = self.get_port(args_one)
            db_user = "postgres"
            t_path = os.path.join(public.get_panel_path(), "data/postgresAS.json")
            db_password = json.loads(public.readFile(t_path)).get("password", "")
        data = {
            'db_name': find["name"],
            'db_host': db_host,
            'db_port': int(db_port),
            'db_user': db_user,
            'db_password': db_password,
        }
        return data

    def get_database_size_by_id(self, args):
        """
        @获取数据库尺寸（批量删除验证）
        @args json/int 数据库id
        """
        total = 0
        db_id = args
        if not isinstance(args, int): db_id = args['db_id']

        try:
            name = public.M('databases').where("id=? AND LOWER(type)=LOWER('PgSql')", db_id).getField('name')
            sql_obj = self.get_sql_obj(name)
            tables = sql_obj.query("select name,size,type from sys.master_files where type=0 and name = '{}'".format(name))

            total = tables[0][1]
            if not total: total = 0
        except:
            pass

        return total

    def check_del_data(self, args):
        """
        @删除数据库前置检测
        """
        return self.check_base_del_data(args)

    # 本地创建数据库
    def __CreateUsers(self, sid, data_name, username, password, address):
        """
        @创建数据库用户

        """
        sql_obj = self.get_sql_obj_by_sid(sid)
        sql_obj.execute("""CREATE USER "{}" WITH PASSWORD '{}';""".format(username, password))
        sql_obj.execute("""GRANT ALL PRIVILEGES ON DATABASE "{}" TO "{}";""".format(data_name, username))
        sql_obj.execute("""CREATE SCHEMA AUTHORIZATION "{}";""".format(username))
        major_version = self.GetMainVersion(None)
        if major_version >= 15:
            sql_obj.execute("""GRANT USAGE, CREATE ON SCHEMA public TO "{}";""".format(username))
            status, err_msg = sql_obj.use_database(data_name)
            #sql_obj.execute("""GRANT USAGE, CREATE ON SCHEMA public TO "{}";""".format(username))
            sql_obj.execute("""GRANT USAGE, CREATE ON SCHEMA public TO "{}";""".format(username))
        
            # # 授予 public schema 中所有表的权限
            # sql_obj.execute("""GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "{}";""".format(username))
            
            # # 授予 public schema 中所有序列的权限
            # sql_obj.execute("""GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "{}";""".format(username))
            
            # # 授予 public schema 中所有函数的权限
            # sql_obj.execute("""GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO "{}";""".format(username))
            
            # # 设置未来创建的表的默认权限（重要！）
            # sql_obj.execute("""ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "{}";""".format(username))
            # sql_obj.execute("""ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "{}";""".format(username))
            # sql_obj.execute("""ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO "{}";""".format(username))

        return True

    # def __CreateUsers2(self, sid, data_name, username, password, address):
    #     """
    #     @创建数据库用户
    #     """
    #     sql_obj = self.get_sql_obj_by_sid(sid)
    #     sql_obj.execute("""CREATE USER "{}" WITH PASSWORD '{}';""".format(username, password))
    #     sql_obj.execute("""GRANT ALL PRIVILEGES ON DATABASE "{}" TO "{}";""".format(data_name, username))
    #     sql_obj.execute("""CREATE SCHEMA AUTHORIZATION "{}";""".format(username))
    #     major_version = self.GetMainVersion(None)
    #     if major_version >= 15:
    #         sql_obj.execute("""GRANT USAGE, CREATE ON SCHEMA public TO "{}";""".format(username))
    #         retrun 39
    #     return 1

    def __get_db_list(self, sql_obj):
        """
        获取pgsql数据库列表
        """
        data = []
        ret = sql_obj.query('SELECT datname FROM pg_database;')
        if type(ret) == list:
            for x in ret:
                data.append(x[0])
        return data

    def __new_password(self):
        """
        生成随机密码
        """
        import random
        import string
        # 生成随机密码
        password = "".join(random.sample(string.ascii_letters + string.digits, 16))
        return password

    def CheckDatabaseStatus(self, get):
        """
        数据库状态检测
        """
        if not hasattr(get, "sid"):
            return public.returnMsg(False, "缺少参数！sid")
        if not str(get.sid).isdigit():
            return public.returnMsg(False, "参数错误！sid")
        sid = int(get.sid)

        pgsql_obj = panelPgsql()
        if sid == 0:
            db_status, err_msg = pgsql_obj.connect()
        else:
            conn_config = public.M("database_servers").where("id=? AND LOWER(db_type)=LOWER('pgsql')", (sid,)).find()
            if not conn_config:
                db_status = False
                err_msg = "远程数据库信息不存在！"
            else:
                pgsql_obj.set_host(host=conn_config["db_host"], port=conn_config["db_port"], database=None, user=conn_config["db_user"], password=conn_config["db_password"])
                db_status, err_msg = pgsql_obj.connect()

        return {"status": True if db_status is True else False, "msg": "正常" if db_status is True else "异常", "db_status": db_status, "err_msg": err_msg}

    def check_cloud_database_status(self, conn_config):
        """
        @检测远程数据库是否连接
        @conn_config 远程数据库配置，包含host port pwd等信息
        旧方法，添加数据库时调用
        """
        try:
            if conn_config.get("db_name"): conn_config["db_name"] = None
            pgsql_obj = panelPgsql().set_host(host=conn_config['db_host'], port=conn_config['db_port'], database=None, user=conn_config['db_user'], password=conn_config['db_password'])

            status, err_msg = pgsql_obj.connect()
            if status is False:
                return {"status": False, "msg": "远程数据库连接失败!"}
            return status
        except:
            return public.returnMsg(False, "远程数据库连接失败！")

    # 获取当前数据库信息
    def GetInfo(self, get):
        db_name = get.db_name

        pgsql_obj = panelPgsql()
        db_find = public.M('databases').where("name=? AND LOWER(type)=LOWER('PgSql')", db_name).find()
        if not db_find:
            return public.returnMsg(False, '数据库不存在！')
        if db_find['sid']:
            db_find = public.M('database_servers').where("id=? AND LOWER(db_type)=LOWER('pgsql')", db_find['sid']).find()
        else:
            path = os.path.join(public.get_panel_path(), "data/postgresAS.json")
            if not os.path.isfile(path):
                return public.returnMsg(False, "请先设置管理员密码！")

            db_find = {
                "db_host": "127.0.0.1",
                "db_port": panelPgsql.get_config_options("port", int, 5432),
                "db_user": "postgres",
                "db_password": json.loads(public.readFile(path))['password'],
            }

        pgsql_obj.set_host(host=db_find['db_host'], port=db_find['db_port'], database=db_name, user=db_find['db_user'], password=db_find['db_password'])
        status, err_msg = pgsql_obj.connect()
        if status is False:
            return public.returnMsg(False, "连接数据库失败！")

        database_list = pgsql_obj.query(f"select datname from pg_database where datname='{db_name}';")
        database_list = [database[0] for database in database_list]
        if not database_list:
            return public.returnMsg(False, '数据库不存在！')

        collation = pgsql_obj.query(f"select pg_encoding_to_char(encoding) from pg_database where datname='{db_name}';")[0][0]
        result = {
            "database": db_name,
            "total_size": 0,
            "table_list": [],
        }

        temp_list = pgsql_obj.query("""
            select schemaname, tablename
            from pg_tables
            where schemaname NOT IN ('pg_catalog', 'information_schema');
        """)
        
        for table in temp_list:
            schema_name = table[0]
            table_name = table[1]
            full_table_name = f'"{schema_name}"."{table_name}"'  # 注意加引号防止大小写或特殊字符问题

            temp_data = pgsql_obj.query(f"select count(*) from {full_table_name};")
            if not isinstance(temp_data, list): continue
            if len(temp_data) == 0: continue
            rows_count = temp_data[0][0]

            data_size = pgsql_obj.query(f"""
                select pg_size_pretty(pg_table_size('{full_table_name}')) AS table_size,
                    pg_size_pretty(pg_indexes_size('{full_table_name}')) AS indexes_size,
                    pg_size_pretty(pg_total_relation_size('{full_table_name}')) AS total_size,
                    pg_total_relation_size('{full_table_name}') as total_size_2;
            """)
            if not isinstance(data_size, list): continue
            if len(data_size) == 0: continue

            table_size = data_size[0][0]
            indexes_size = data_size[0][1]
            total_size = data_size[0][2]
            total_size_2 = data_size[0][3]

            table_temp = {
                "schema": schema_name,
                "table_name": table_name,
                "rows_count": rows_count,
                "table_size": table_size,
                "indexes_size": indexes_size,
                "total_size": total_size,
            }

            result["total_size"] += total_size_2
            result["table_list"].append(table_temp)

        result["total_size"] = public.to_size(result["total_size"])
        return {"status": True, "msg": "ok", "data": result}


