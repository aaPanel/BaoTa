# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2017 宝塔软件(http:#bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: 1249648969@qq.com
# -------------------------------------------------------------------

# ------------------------------
# 数据库工具类
# ------------------------------
import sys, os
os.chdir("/www/server/panel")
if not 'class/' in sys.path:
    sys.path.insert(0,'class/')
import panelMysql
import re,json,public

class datatools:
    DB_MySQL = None
    # 字节单位转换
    def ToSize(self, size):
        ds = ['b', 'KB', 'MB', 'GB', 'TB']
        for d in ds:
            if size < 1024: return ('%.2f' % size) + d
            size = size / 1024
        return '0b';

    # 获取当前数据库信息
    def GetdataInfo(self,get):
        '''
        传递一个数据库名称即可 get.databases
        '''
        if not self.DB_MySQL:self.DB_MySQL = panelMysql.panelMysql()
        db_name=get.db_name

        if not db_name:return False
        ret = {}
        tables = self.map_to_list(self.DB_MySQL.query('show tables from `%s`' % db_name))
        if type(tables) == list:
            try:
                data = self.map_to_list(self.DB_MySQL.query("select sum(DATA_LENGTH)+sum(INDEX_LENGTH) from information_schema.tables  where table_schema='%s'" % db_name))[0][0]
            except:
                data=0

            if not data: data = 0
            ret['data_size'] = self.ToSize(data)
            ret['database'] = db_name

            ret3 = []
            for i in tables:
                if i == 1049: return public.returnMsg(False,'指定数据库不存在!')
                if type(i) == int: continue
                table = self.map_to_list(self.DB_MySQL.query("show table status from `%s` where name = '%s'" % (db_name, i[0])))
                if not table: continue
                try:
                    ret2 = {}
                    ret2['type']=table[0][1]
                    data_size = table[0][6]
                    ret2['rows_count'] = table[0][4]
                    ret2['collation'] = table[0][14]
                    ret2['data_size'] = self.ToSize(int(data_size))
                    ret2['table_name'] = i[0]
                    ret3.append(ret2)
                except: continue
            ret['tables'] = (ret3)
        return ret



    #修复表信息
    def RepairTable(self,get):
        
        '''
        POST:
        db_name=web
        tables=['web1','web2']
        '''
        db_name = get.db_name
        tables = json.loads(get.tables)
        if not db_name or not tables: return False
        if not self.DB_MySQL:self.DB_MySQL = panelMysql.panelMysql()
        mysql_table = self.map_to_list(self.DB_MySQL.query('show tables from `%s`' % db_name))
        ret=[]
        if type(mysql_table)==list:
            if len(mysql_table)>0:
                for i in mysql_table:
                    for i2 in tables:
                        if i2==i[0]:
                            ret.append(i2)
                if len(ret)>0:
                    for i in ret:
                        self.DB_MySQL.execute('REPAIR TABLE `%s`.`%s`'%(db_name,i))
                    return True 
        return False



    #map to list
    def map_to_list(self,map_obj):
        try:
            if type(map_obj) != list and type(map_obj) != str: map_obj = list(map_obj)
            return map_obj
        except: return []


    # 优化表
    def OptimizeTable(self,get):
        '''
        POST:
        db_name=web
        tables=['web1','web2']
        '''
        if not self.DB_MySQL:self.DB_MySQL = panelMysql.panelMysql()
        db_name = get.db_name
        tables = json.loads(get.tables)
        if not db_name or not tables: return False
        mysql_table = self.map_to_list(self.DB_MySQL.query('show tables from `%s`' % db_name))
        ret=[]
        if type(mysql_table) == list:
            if len(mysql_table) > 0:
                for i in mysql_table:
                    for i2 in tables:
                        if i2 == i[0]:
                            ret.append(i2)
                if len(ret)>0:
                    for i in ret:
                        self.DB_MySQL.execute('OPTIMIZE table `%s`.`%s` ENGINE=MyISAM' % (db_name,i))
                    return True 
        return False

    # 更改表引擎
    def AlterTable(self,get):
        '''
        POST:
        db_name=web
        table_type=innodb
        tables=['web1','web2']
        '''
        if not self.DB_MySQL:self.DB_MySQL = panelMysql.panelMysql()
        db_name = get.db_name
        table_type = get.table_type
        tables = json.loads(get.tables)

        if not db_name or not tables: return False
        
        mysql_table = self.map_to_list(self.DB_MySQL.query('show tables from `%s`' % db_name))
        ret=[]
        if type(mysql_table)==list:
            if len(mysql_table)>0:
                for i in mysql_table:
                    for i2 in tables:
                        if i2==i[0]:
                            ret.append(i2)
                if len(ret)>0:
                    for i in ret:
                        self.DB_MySQL.execute('alter table `%s`.`%s` ENGINE=`%s`' % (db_name,i,table_type))
                    return True
        return False


    #检查表
    def CheckTable(self,database,tables,*args,**kwargs):
        pass
