#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# sqlite模型
#------------------------------
import os,sys,re,json,shutil,psutil,time
from databaseModel.base import databaseBase
import public,db

try:
    from BTPanel import session
except :pass

class main(databaseBase):

    db_file = '{}/data/db_model.json'.format(public.get_panel_path())

    def get_list(self,args):
        """
        @name 获取数据库列表
        @param args['path'] 数据库文件路径
        @return list
        """
        result = []
        data = self.get_database_list()
        for sfile in data:
            info = {}

            info['name'] = os.path.basename(sfile)
            if 'name' in data[sfile]:
                info['name'] = data[sfile]['name']

            info['path'] = sfile
            if os.path.exists(sfile):
                info['size'] = os.path.getsize(sfile)
                info['st_time'] = int(os.path.getmtime(sfile))
                info['backup_count'] = 0
                try:
                    get = public.dict_obj()
                    get.path = sfile
                    nlist = self.get_backup_list(get)
                    info['backup_count'] = len(nlist)
                except:pass

                result.append(info)

        return result

    def AddDatabase(self,args):

        try:
            """
            @name 添加数据库
            @param args['name'] 数据库名称
            @param args['path'] 数据库路径
            @return bool
            """
            name = None
            path = args.path
            if not os.path.exists(path):
                return public.returnMsg(False,'数据库路径错误.')
            if 'name' in args:
                name = args.name
                name = name.replace(' ','')

            info = self.get_db_info(path)
            if not info:
                return public.returnMsg(False,'数据库文件错误,不是有效的sqlite数据库文件.')

            if not name:
                name = os.path.basename(path)

            data = self.get_database_list()
            if path in data:
                return public.returnMsg(False,'数据库已存在.')

            data[path] = {'name':name}
            public.writeFile(self.db_file,json.dumps(data))
            return public.returnMsg(True,'添加成功.')
        except Exception as e:
            return public.returnMsg(False,'添加失败.'+str(e))

    def DeleteDatabase(self,args):
        """
        @name 删除数据库
        @param args['path'] 数据库路径
        @return bool
        """
        path = args.path
        if not os.path.exists(path):
            return public.returnMsg(False,'数据库不存在.')

        data = self.get_database_list()
        if not path in data:
            return public.returnMsg(False,'数据库不存在.')

        del data[path]
        public.writeFile(self.db_file,json.dumps(data))
        return public.returnMsg(True,'删除成功.')


    def ToBackup(self,args):
        """
        @name 备份数据库
        @param args['path'] 数据库路径
        @return bool
        """
        path = args.path
        if not os.path.exists(path):
            return public.returnMsg(False,'数据库不存在.')

        data = self.get_database_list()
        if not path in data:
            return public.returnMsg(False,'数据库不存在.')

        fileName =  '{}_{}'.format(time.strftime('%Y%m%d_%H%M%S',time.localtime()),os.path.basename(path))
        backup_path = '{}/database/sqlite/{}'.format(session['config']['backup_path'],public.md5(path))
        if not os.path.exists(backup_path):
            os.makedirs(backup_path)

        backup_file = '{}/{}'.format(backup_path,fileName)
        shutil.copy(path,backup_file)
        if os.path.exists(backup_file):
            return public.returnMsg(True,'备份成功.')
        return public.returnMsg(False,'备份失败.')


    def DelBackup(self,args):
        """
        @删除备份文件
        """
        file = args.file
        if os.path.exists(file): os.remove(file)

        return public.returnMsg(True, 'DEL_SUCCESS');

    def get_backup_list(self,get):
        """
        @获取备份文件列表
        """
        nlist = []
        search = ''
        path = get.path

        if hasattr(get,'search'):
            search = get['search'].strip().lower()

        path  = session['config']['backup_path'] + '/database/sqlite/' + public.md5(path)
        if not os.path.exists(path): os.makedirs(path)
        for name in os.listdir(path):
            if search:
                if name.lower().find(search) == -1: continue;

            arrs = name.split('_')

            filepath = '{}/{}'.format(path,name).replace('//','/')
            stat = os.stat(filepath)

            item = {}
            item['name'] = name
            item['filepath'] = filepath
            item['size'] = stat.st_size
            item['mtime'] = int(stat.st_mtime)

            nlist.append(item)
        return nlist

    def get_table_list(self,args):
        """
        @name 获取数据库表列表
        @param args['path'] 数据库路径
        @return list
        """

        path = args.path
        if not os.path.exists(path):
            return public.returnMsg(False,'数据库不存在.')

        data = self.get_database_list()
        if not path in data:
            return public.returnMsg(False,'数据库不存在.')

        db = self.get_db_info(path)
        if not db:
            return public.returnMsg(False,'数据库文件错误.')

        result = []
        sql = db['sql']
        tables = sql.query('select `name` from sqlite_master where type="table"')
        for table in tables:
            info = {}
            info['name'] = table[0]
            if info['name'] in ['sqlite_sequence']:
                continue
            info['count'] = sql.table(info['name']).count() #获取表记录数
            result.append(info) #添加到结果列表
        return result

    def get_table_info(self,args):
        """
        @name 获取表信息
        @param args['path'] 数据库路径
        @param args['table'] 表名
        @return list
        """

        path = args.path
        table = args.table
        if not os.path.exists(path):
            return public.returnMsg(False,'数据库不存在.')

        data = self.get_database_list()
        if not path in data:
            return public.returnMsg(False,'数据库不存在.')

        db = self.get_db_info(path)
        if not db:
            return public.returnMsg(False,'数据库文件错误.')

        sql = db['sql'].table(table) #获取表对象
        order = ""
        if hasattr(args,'order'):
            order = args.order

        where = '1=1'
        limit = 10
        if hasattr(args,'limit'):
            limit = int(args.limit)

        if hasattr(args,'search') and args.search:

            w_list = []
            slist = sql.query('PRAGMA table_info({})'.format(table))
            for val in slist:
                w_list.append("`{}` like '%{}%'".format(val[1],args.search))
            where = ' or '.join(w_list)

        import page
        #实例化分页类
        page = page.Page()

        info = {}
        info['count'] = sql.where(where,()).count()
        info['row']   = limit
        info['uri']   = args
        info['p'] = 1
        if hasattr(args,'p'):
            info['p'] = int(args['p'])

        info['return_js'] = ''
        if hasattr(args,'tojs'):
            info['return_js']   = args.tojs

        data['where'] = where
        data['page'] = page.GetPage(info,'1,2,3,4,5,8')    #获取分页数据
        data['data'] = sql.where(where,()).order(order).limit(str(page.SHIFT)+','+str(page.ROW)).select()      #取出数据
        for item in data['data']:
            for key in item:
                if isinstance(item[key], (bytes,bytearray)):
                    item[key] = str(item[key])
        return data


    def update_table_info(self,args):
        """
        @name 更新表信息
        @param args['path'] 数据库路径
        @param args['table'] 表名
        @param args['where_data'] 修改前数据
        @param args['new_data'] 修改后数据
        @return bool
        """

        path = args.path
        table = args.table
        where_data = args.where_data
        new_data = args.new_data

        if not os.path.exists(path):
            return public.returnMsg(False,'数据库不存在.')

        data = self.get_database_list()
        if not path in data:
            return public.returnMsg(False,'数据库不存在.')

        db = self.get_db_info(path)
        if not db:
            return public.returnMsg(False,'数据库文件错误.')

        sql = db['sql'].table(table)
        where = self.__get_where(where_data,sql,table)

        if sql.where(where,()).count() <= 0:
            return public.returnMsg(False,'更新失败，数据不存在.')

        res = sql.where(where,()).update(new_data)
        if not res:
            return public.returnMsg(False,'更新失败.')

        return public.returnMsg(True,'更新成功.')



    def create_table(self,args):
        """
        @name 创建表
        """
        path = args.path
        if not os.path.exists(path):
            return public.returnMsg(False,'数据库不存在.')

        data = self.get_database_list()
        if not path in data:
            return public.returnMsg(False,'数据库不存在.')

        table = args.table
        sql_shell = args.sql_shell
        db = self.get_db_info(path)
        if not db:
            return public.returnMsg(False,'数据库文件错误.')

        sql = db['sql']
        tables = sql.query('select `name` from sqlite_master where type="table"')
        if table in tables:
            return public.returnMsg(False,'数据表已存在.')

        result = sql.execute(sql_shell)
        tables = sql.query('select `name` from sqlite_master where type="table"')
        if table in tables:
            return public.returnMsg(True,'创建成功.')
        else:
            return public.returnMsg(False,'创建失败,error:{}'.format(result))

    def execute_sql(self,args):
        """
        @name 执行SQL语句
        @param args['path'] 数据库路径
        @param args['sql_shell'] SQL语句
        @return bool
        """

        path = args.path
        if not os.path.exists(path):
            return public.returnMsg(False,'数据库不存在.')

        data = self.get_database_list()
        if not path in data:
            return public.returnMsg(False,'数据库不存在.')

        sql_shell = args.sql_shell
        db = self.get_db_info(path)
        if not db:
            return public.returnMsg(False,'数据库文件错误.')
        sql = db['sql']
        result = sql.execute(sql_shell)

        if result.find('error') != -1:
            return public.returnMsg(True,'执行成功,受影响行数{}.'.format(result))

        return public.returnMsg(False,'执行失败,{}'.format(result))

    def query_sql(self,args):
        """
        @name 查询sql
        @param args['path'] 数据库路径
        @param args['sql_shell'] sql语句
        """
        path = args.path
        if not os.path.exists(path):
            return public.returnMsg(False,'数据库不存在.')

        data = self.get_database_list()
        if not path in data:
            return public.returnMsg(False,'数据库不存在.')

        sql_shell = args.sql_shell
        db = self.get_db_info(path)
        if not db:
            return public.returnMsg(False,'数据库文件错误.')
        sql = db['sql']
        res = sql.query(sql_shell)

        result = {}
        if type(res) == list:
            result['status'] = True
            result['list'] = res

        else:
            result['status'] = False
            result['msg'] = res
        return result



    def create_table_data(self,args):
        """
        @name 添加数据
        @param args['path'] 数据库路径
        @param args['table'] 表名
        @param args['new_data'] 数据
        """

        path = args.path
        table = args.table
        new_data = args.new_data

        if not os.path.exists(path):
            return public.returnMsg(False,'数据库不存在.')

        data = self.get_database_list()
        if not path in data:
            return public.returnMsg(False,'数据库不存在.')

        db = self.get_db_info(path)
        if not db:
            return public.returnMsg(False,'数据库文件错误.')

        sql = db['sql'].table(table)

        new_data = self.__format_table_info(sql,table,new_data) #格式化数据
        keys,param = self.__format_pdata(new_data)
        res = sql.add(keys,param)
        if not res:
            return public.returnMsg(False,'添加数据失败，{}.'.format(res)) #添加失败，返回错误信息

        return public.returnMsg(True,'添加数据成功.')

    def delete_table_data(self,args):
        """
        @name 删除数据
        @param args['path'] 数据库路径
        @param args['table'] 表名
        @param args['where_data'] 删除数据
        """

        path = args.path
        table = args.table
        where_data = args.where_data

        if not os.path.exists(path):
            return public.returnMsg(False,'数据库不存在.')

        data = self.get_database_list()
        if not path in data:
            return public.returnMsg(False,'数据库不存在.')

        db = self.get_db_info(path)
        if not db:
            return public.returnMsg(False,'数据库文件错误.')

        sql = db['sql'].table(table)
        where = self.__get_where(where_data,sql,table)

        count = sql.where(where,()).count() #获取数据条数
        sql.where(where,()).delete() #删除数据
        if count == 0:
            return public.returnMsg(False,'删除数据失败，数据不存在.')

        return public.returnMsg(True,'删除成功，共删除数据 {} 条.'.format(count)) #返回成功信息

    def get_keys_bytable(self,args):
        """
        @name 获取表字段
        @param args['path'] 数据库路径
        @param args['table'] 表名
        @return list
        """

        path = args.path
        table = args.table

        if not os.path.exists(path):
            return public.returnMsg(False,'数据库不存在.')

        data = self.get_database_list()
        if not path in data:
            return public.returnMsg(False,'数据库不存在.')

        db = self.get_db_info(path)
        if not db:
            return public.returnMsg(False,'数据库文件错误.')

        result = []
        sql = db['sql'].table(table)
        slist = sql.query('PRAGMA table_info({})'.format(table))

        if not slist:
            return public.returnMsg(False, '无法获取表信息或表不存在。')

        for val in slist:
            if len(val) >= 6:  
                result.append({'name': val[1], 'type': val[2].lower(), 'pk': val[5]})
            else:
                print("数据格式不符合预期，表可能不含有足够的字段信息。")
                continue

        return result
    

    def __get_table_pk(self,sql,table):
        """
        @name 获取表主键
        @param sql sql对象
        @return array
        """
        res = []
        slist = sql.query('PRAGMA table_info({})'.format(table))

        for val in slist:

            if val[5] == 1:
                res.append(val[1])
        return res

    def __get_where(self,where_data,sql,table = None):
        """
        @name 获取where条件
        """
        res = []
        pks = self.__get_table_pk(sql,table)
        if len(pks) > 0:
            for pk in pks:
                if pk in where_data:
                    if type(where_data[pk]) == int:
                        res.append(" `{}` = {}".format(pk,where_data[pk]))
                    else:
                        res.append("`{}` = '{}'".format(pk,where_data[pk]))
        else:
            for key in where_data:
                if type(where_data[key]) == int:

                    res.append(" {}={} ".format(key,where_data[key]))
                else:
                    res.append(" {}='{}' ".format(key,where_data[key]))
        if len(res) == 0:
            return ' 1 = 1'
        return ' and '.join(res)


    def __format_table_info(self,sql,talbe,data):
        """
        @name 添加时删除自增字段
        @param sql 表对象
        @param data 数据
        @return dict
        """
        slist = sql.query('PRAGMA table_info({})'.format(talbe)) #获取表结构
        for val in slist:
            if val[5]:
                del data[val[1]] #删除自增字段
        return data


    def get_database_list(self):
        """
        @name 获取数据库列表
        """
        data = {}
        try:
            data = json.loads(public.readFile(self.db_file))
        except:pass
        return data


    #构造数据
    def __format_pdata(self,pdata):
        keys = pdata.keys()
        keys_str = ','.join(["`{}`".format(i) for i in keys])
        param = []
        for k in keys: param.append(pdata[k])
        return keys_str,tuple(param)

    def get_db_info(self,path):
        """
        @name 获取数据库信息
        @param path 数据库路径
        @return dict
        """
        result = False
        try:
            sql = db.Sql().set_dbfile(path)
            data = sql.query('select `name` from sqlite_master where type="table"')

            if type(data) == str:
                return False
            result = {}
            result['tab_count'] = len(data)
            result['size'] = os.path.getsize(path)
            result['sql'] = sql
            print(result)
        except:pass
        return result

