# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# -------------------------------------------------------------------

# ------------------------------
# sqlite模型
# ------------------------------
import os, re, json, time
from databaseModel.base import databaseBase
import public, panelMssql

try:
    from BTPanel import session
except:
    pass


class main(databaseBase):

    def get_list(self, args):
        """
        @获取数据库列表
        @sql_type = sqlserver
        """
        return self.get_base_list(args, sql_type='sqlserver')

    def get_mssql_obj_by_sid(self, sid=0, conn_config=None):
        """
        @取mssql数据库对像 By sid
        @sid 数据库分类，0：本地
        """
        if type(sid) == str:
            try:
                sid = int(sid)
            except:
                sid = 0

        if sid:
            if not conn_config: conn_config = public.M('database_servers').where("id=?", sid).find()
            db_obj = panelMssql.panelMssql()

            try:
                db_obj = db_obj.set_host(conn_config['db_host'], conn_config['db_port'], None, conn_config['db_user'], conn_config['db_password'])
            except Exception as e:
                raise public.PanelError(e)
        else:
            db_obj = panelMssql.panelMssql()
        return db_obj

    def get_mssql_obj(self, db_name):
        """
        @取mssql数据库对象
        @db_name 数据库名称
        """
        is_cloud_db = False
        if db_name:
            db_find = public.M('databases').where("name=? AND LOWER(type)=LOWER('SQLServer')", db_name).find()
            if db_find['sid']:
                return self.get_mssql_obj_by_sid(db_find['sid'])
            is_cloud_db = db_find['db_type'] in ['1', 1]

        if is_cloud_db:

            db_obj = panelMssql.panelMssql()
            conn_config = json.loads(db_find['conn_config'])
            try:
                db_obj = db_obj.set_host(conn_config['db_host'], conn_config['db_port'], conn_config['db_name'], conn_config['db_user'], conn_config['db_password'])
            except Exception as e:
                raise public.PanelError(e)
        else:
            db_obj = panelMssql.panelMssql()
        return db_obj

    def GetCloudServer(self, args):
        '''
            @name 获取远程服务器列表
            @author hwliang<2021-01-10>
            @return list
        '''
        return self.GetBaseCloudServer(args)

    def AddCloudServer(self, args):
        '''
        @添加远程数据库
        '''
        public.set_module_logs('sqlserver', 'addremoteserver', 1)
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

    def AddDatabase(self, args):
        """
        @添加数据库

        """
        dtype = "sqlserver"
        res = self.add_base_database(args, dtype)
        if not res['status']: return res

        data_name = res['data_name']
        username = res['username']
        password = res['data_pwd']

        if re.match("^\d+", data_name):
            return public.returnMsg(False, 'SQLServer数据库不能以数字开头!')

        reg_count = 0
        regs = ['[a-z]', '[A-Z]', '\W', '[0-9]']
        for x in regs:
            if re.search(x, password): reg_count += 1

        if len(password) < 8 or len(password) > 128 or reg_count < 3:
            return public.returnMsg(False, 'SQLServer密码复杂性策略不匹配，应为8-128位，并包含大写，小写，数字，特殊符号其中任何3项!')

        try:
            self.sid = int(args['sid'])
        except:
            self.sid = 0

        dtype = 'SQLServer'
        # 添加SQLServer
        mssql_obj = self.get_mssql_obj_by_sid(self.sid)
        result = mssql_obj.execute("CREATE DATABASE %s" % data_name)
        isError = self.IsSqlError(result)
        if isError != None: return isError

        mssql_obj.execute("DROP LOGIN %s" % username)

        # 添加用户
        self.__CreateUsers(data_name, username, password, '127.0.0.1')

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
        if self.sid: db_type = 2

        public.set_module_logs('linux_sqlserver', 'AddDatabase', 1)
        # 添加入SQLITE
        public.M('databases').add('pid,sid,db_type,name,username,password,accept,ps,addtime,type', (pid, self.sid, db_type, data_name, username, password, '127.0.0.1', args['ps'], addTime, dtype))
        public.WriteLog("TYPE_DATABASE", 'DATABASE_ADD_SUCCESS', (data_name,))
        return public.returnMsg(True, 'ADD_SUCCESS')

    def DeleteDatabase(self, args):
        """
        @删除数据库
        """

        id = args['id']
        find = public.M('databases').where("id=? AND LOWER(type)=LOWER('SQLServer')", (id,)).field('id,pid,name,username,password,type,accept,ps,addtime,sid,db_type').find()
        if not find: return public.returnMsg(False, '指定数据库不存在.')

        name = args['name']
        username = find['username']

        mssql_obj = self.get_mssql_obj_by_sid(find['sid'])
        mssql_obj.execute("ALTER DATABASE %s SET SINGLE_USER with ROLLBACK IMMEDIATE" % name)
        result = mssql_obj.execute("DROP DATABASE %s" % name)

        if self.get_database_size_by_id(find['sid']):
            isError = self.IsSqlError(result)
            if isError != None: return isError

        mssql_obj.execute("DROP LOGIN %s" % username)

        # 删除SQLITE
        public.M('databases').where("id=? AND LOWER(type)=LOWER('SQLServer')", (id,)).delete()
        public.WriteLog("TYPE_DATABASE", 'DATABASE_DEL_SUCCESS', (name,))
        return public.returnMsg(True, 'DEL_SUCCESS')

    def ToBackup(self, args):
        """
        @备份数据库 id 数据库id
        """
        id = args['id']
        find = public.M('databases').where("id=? AND LOWER(type)=LOWER('SQLServer')", (id,)).find()
        if not find: return public.returnMsg(False, '数据库不存在!')

        self.CheckBackupPath(args)

        fileName = f"{find['name']}_sqlserver_data_{time.strftime('%Y%m%d_%H%M%S', time.localtime())}.bak"
        backupName = session['config']['backup_path'] + '/database/sqlserver/' + fileName

        mssql_obj = self.get_mssql_obj_by_sid(find['sid'])

        if not int(find['sid']):
            ret = mssql_obj.execute("backup database %s To disk='%s'" % (find['name'], backupName))
            isError = self.IsSqlError(ret)
            if isError != None: return isError
        else:
            # 远程数据库
            return public.returnMsg(False, '操作失败，远程数据库无法备份.')

        if not os.path.exists(backupName):
            return public.returnMsg(False, 'BACKUP_ERROR')

        public.M('backup').add('type,name,pid,filename,size,addtime', (1, fileName, id, backupName, 0, time.strftime('%Y-%m-%d %X', time.localtime())))
        public.WriteLog("TYPE_DATABASE", "DATABASE_BACKUP_SUCCESS", (find['name'],))

        if os.path.getsize(backupName) < 2048:
            return public.returnMsg(True, '备份执行成功，备份文件小于2Kb，请检查备份完整性.')
        else:
            return public.returnMsg(True, 'BACKUP_SUCCESS')

    def DelBackup(self, args):
        """
        @删除备份文件
        """
        return self.delete_base_backup(args)

    # 导入
    def InputSql(self, get):

        name = get.name
        file = get.file

        find = public.M('databases').where("name=? AND LOWER(type)=LOWER('SQLServer')", (name,)).find()
        if not find: return public.returnMsg(False, '数据库不存在!')

        tmp = file.split('.')
        exts = ['sql', 'zip', 'bak']
        ext = tmp[len(tmp) - 1]
        if ext not in exts:
            return public.returnMsg(False, 'DATABASE_INPUT_ERR_FORMAT')

        backupPath = session['config']['backup_path'] + '/database'

        if ext == 'zip':
            try:
                fname = os.path.basename(file).replace('.zip', '')
                dst_path = backupPath + '/' + fname
                if not os.path.exists(dst_path): os.makedirs(dst_path)

                public.unzip(file, dst_path)
                for x in os.listdir(dst_path):
                    if x.find('bak') >= 0 or x.find('sql') >= 0:
                        file = dst_path + '/' + x
                        break
            except:
                return public.returnMsg(False, '导入失败，该文件不是有效的zip格式的文件。')

        mssql_obj = self.get_mssql_obj_by_sid(find['sid'])
        data = mssql_obj.query("use %s ;select filename from sysfiles" % find['name'])

        isError = self.IsSqlError(data)
        if isError != None: return isError
        if type(data) == str: return public.returnMsg(False, data)

        mssql_obj.execute("ALTER DATABASE %s SET OFFLINE WITH ROLLBACK IMMEDIATE" % (find['name']))
        mssql_obj.execute("use master;restore database %s from disk='%s' with replace, MOVE N'%s' TO N'%s',MOVE N'%s_Log'  TO N'%s' " % (find['name'], file, find['name'], data[0][0], find['name'], data[1][0]))
        mssql_obj.execute("ALTER DATABASE %s SET ONLINE" % (find['name']))

        public.WriteLog("TYPE_DATABASE", '导入数据库[{}]成功'.format(name))
        return public.returnMsg(True, 'DATABASE_INPUT_SUCCESS')

    # 同步数据库到服务器
    def SyncToDatabases(self, get):
        type = int(get['type'])
        n = 0
        sql = public.M('databases')
        if type == 0:
            data = sql.field('id,name,username,password,accept,type,sid,db_type').where('type=?', ('SQLServer',)).select()

            for value in data:
                if value['db_type'] in ['1', 1]:
                    continue  # 跳过远程数据库
                result = self.ToDataBase(value)
                if result == 1: n += 1
        else:
            import json
            data = json.loads(get.ids)
            for value in data:
                find = sql.where("id=? AND LOWER(type)=LOWER('SQLServer')", (value,)).field('id,name,username,password,sid,db_type,accept,type').find()
                result = self.ToDataBase(find)
                if result == 1: n += 1

        if n == 1:
            return public.returnMsg(True, '同步成功')
        elif n == 0:
            return public.returnMsg(False, '同步失败')

        return public.returnMsg(True, 'DATABASE_SYNC_SUCCESS', (str(n),))

    # 添加到服务器
    def ToDataBase(self, find):
        if find['username'] == 'bt_default': return 0
        if len(find['password']) < 3:
            find['username'] = find['name']
            find['password'] = public.md5(str(time.time()) + find['name'])[0:10]
            public.M('databases').where("id=? AND LOWER(type)=LOWER('SQLServer')", (find['id'],)).save('password,username', (find['password'], find['username']))

        self.sid = find['sid']
        mssql_obj = self.get_mssql_obj_by_sid(self.sid)
        result = mssql_obj.execute("CREATE DATABASE %s" % find['name'])
        isError = self.IsSqlError(result)
        if isError != None and not 'already exists' in result: return -1

        self.__CreateUsers(find['name'], find['username'], find['password'], '127.0.0.1')

        return 1

    # 从服务器获取数据库
    def SyncGetDatabases(self, get):

        n = 0
        s = 0
        db_type = 0
        self.sid = get.get('sid/d', 0)
        if self.sid: db_type = 2

        mssql_obj = self.get_mssql_obj_by_sid(self.sid)

        data = mssql_obj.query('SELECT name FROM MASTER.DBO.SYSDATABASES ORDER BY name')
        isError = self.IsSqlError(data)
        if isError != None: return isError
        if type(data) == str: return public.returnMsg(False, data)

        sql = public.M('databases')
        nameArr = ['information_schema', 'performance_schema', 'mysql', 'sys', 'master', 'model', 'msdb', 'tempdb', 'ReportServerTempDB', 'YueMiao', 'ReportServer']
        for item in data:
            dbname = item[0]
            if sql.where("name=? AND LOWER(type)=LOWER('SQLServer')", (dbname,)).count(): continue
            if not dbname in nameArr:
                if sql.table('databases').add('name,username,password,accept,ps,addtime,type,sid,db_type', (dbname, dbname, '', '', public.getMsg('INPUT_PS'), time.strftime('%Y-%m-%d %X', time.localtime()), 'SQLServer', self.sid, db_type)): n += 1

        return public.returnMsg(True, 'DATABASE_GET_SUCCESS', (str(n),))

    def ResDatabasePassword(self, args):
        """
        @修改用户密码
        """
        id = args['id']
        username = args['name'].strip()
        newpassword = public.trim(args['password'])

        try:
            if not newpassword:
                return public.returnMsg(False, '修改失败，数据库[' + username + ']密码不能为空.')
            if len(re.search("^[\w@\.]+$", newpassword).groups()) > 0:
                return public.returnMsg(False, '数据库密码不能为空或带有特殊字符')
        except:
            return public.returnMsg(False, '数据库密码不能为空或带有特殊字符')

        find = public.M('databases').where("id=? AND LOWER(type)=LOWER('SQLServer')", (id,)).field('id,pid,name,username,password,type,accept,ps,addtime,sid').find()
        if not find: return public.returnMsg(False, '修改失败，指定数据库不存在.')

        mssql_obj = self.get_mssql_obj_by_sid(find['sid'])
        mssql_obj.execute("EXEC sp_password NULL, '%s', '%s'" % (newpassword, username))

        # 修改SQLITE
        public.M('databases').where("id=? AND LOWER(type)=LOWER('SQLServer')", (id,)).setField('password', newpassword)

        public.WriteLog("TYPE_DATABASE", 'DATABASE_PASS_SUCCESS', (find['name'],))
        return public.returnMsg(True, 'DATABASE_PASS_SUCCESS', (find['name'],))

    def get_root_pwd(self, args):
        """
        @获取sa密码
        """
        mssql_obj = panelMssql.panelMssql()
        ret = mssql_obj.get_sql_name()
        if not ret: return public.returnMsg(False, 'SQL Server未安装或者未启动，请先安装或启动')

        sa_path = '{}/data/sa.pl'.format(public.get_panel_path())
        if os.path.exists(sa_path):
            password = public.readFile(sa_path)
            return public.returnMsg(True, password)
        return public.returnMsg(True, '')

    def set_root_pwd(self, args):
        """
        @设置sa密码
        """
        password = public.trim(args['password'])
        try:
            if not password:
                return public.returnMsg(False, '修改失败，数据库[' + username + ']密码不能为空.')
            if len(re.search("^[\w@\.]+$", password).groups()) > 0:
                return public.returnMsg(False, 'sa密码不能为空或带有特殊符号')
        except:
            return public.returnMsg(False, 'sa密码不能为空或带有特殊符号')

        mssql_obj = panelMssql.panelMssql()
        result = mssql_obj.execute("EXEC sp_password NULL, '%s', 'sa'" % password)

        isError = self.IsSqlError(result)
        if isError != None: return isError

        public.writeFile('data/sa.pl', password)
        session['config']['mssql_sa'] = password
        return public.returnMsg(True, '修改sa密码成功！')

    def get_database_size_by_id(self, args):
        """
        @获取数据库尺寸（批量删除验证）
        @args json/int 数据库id
        """
        total = 0
        db_id = args
        if not isinstance(args, int): db_id = args['db_id']

        try:
            name = public.M('databases').where("id=? AND LOWER(type)=LOWER('SQLServer')", db_id).getField('name')
            mssql_obj = self.get_mssql_obj(name)
            tables = mssql_obj.query("select name,size,type from sys.master_files where type=0 and name = '{}'".format(name))

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
    def __CreateUsers(self, data_name, username, password, address):
        """
        @创建数据库用户
        """
        mssql_obj = self.get_mssql_obj_by_sid(self.sid)
        mssql_obj.execute("use %s create login %s with password ='%s' , default_database = %s" % (data_name, username, password, data_name))
        mssql_obj.execute("use %s create user %s for login %s with default_schema=dbo" % (data_name, username, username))
        mssql_obj.execute("use %s exec sp_addrolemember 'db_owner','%s'" % (data_name, data_name))
        mssql_obj.execute("ALTER DATABASE %s SET MULTI_USER" % data_name)

    # 检测备份目录并赋值权限（MSSQL需要Authenticated Users）
    def CheckBackupPath(self, get):
        backupFile = session['config']['backup_path'] + '/database/sqlserver'
        if not os.path.exists(backupFile):
            os.makedirs(backupFile)
            get.filename = backupFile
            get.user = 'Authenticated Users'
            get.access = 2032127
            import files
            files.files().SetFileAccess(get)

    # 数据库状态检测
    def CheckDatabaseStatus(self, get):
        """
        数据库状态检测
        """
        if not hasattr(get, "sid"):
            return public.returnMsg(False, "缺少参数！sid")
        if not str(get.sid).isdigit():
            return public.returnMsg(False, "参数错误！sid")
        sid = int(get.sid)
        if sid != 0:
            conn_config = public.M("database_servers").where("id=? AND LOWER(db_type)=LOWER('sqlserver')", (sid,)).find()
            if not conn_config:
                return public.returnMsg(False, "远程数据库信息不存在！")
            conn_config["db_name"] = None
            sql_server_obj = panelMssql.panelMssql().set_host(conn_config['db_host'], conn_config['db_port'], conn_config.get("db_name"), conn_config['db_user'], conn_config['db_password'])
        else:
            sql_server_obj = panelMssql.panelMssql()
        data = sql_server_obj.query("SELECT name FROM MASTER.DBO.SYSDATABASES ORDER BY name")
        db_status = not isinstance(data, bool)
        return {"status": True, "msg": "正常" if db_status is True else "异常", "db_status": db_status}

    def check_cloud_database_status(self, conn_config):
        """
        @检测远程数据库是否连接
        @conn_config 远程数据库配置，包含host port pwd等信息
        """
        try:

            import panelMssql
            if not 'db_name' in conn_config: conn_config['db_name'] = None
            sql_obj = panelMssql.panelMssql().set_host(conn_config['db_host'], conn_config['db_port'], conn_config['db_name'], conn_config['db_user'], conn_config['db_password'])
            data = sql_obj.query("SELECT name FROM MASTER.DBO.SYSDATABASES ORDER BY name")

            isError = self.IsSqlError(data)
            if isError != None: return isError
            if type(data) == str:
                return public.returnMsg(False, data)

            if not conn_config['db_name']: return True
            for i in data:
                if i[0] == conn_config['db_name']:
                    return True
            return public.returnMsg(False, '指定数据库不存在!')
        except Exception as ex:
            return public.returnMsg(False, "远程数据库连接失败！{}".format(ex))
