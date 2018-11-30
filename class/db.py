#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------

import sqlite3
import os

class Sql():
    #------------------------------
    # 数据库操作类 For sqlite3
    #------------------------------
    __DB_FILE    = None            # 数据库文件
    __DB_CONN    = None            # 数据库连接对象
    __DB_TABLE   = ""              # 被操作的表名称
    __OPT_WHERE  = ""              # where条件
    __OPT_LIMIT  = ""              # limit条件
    __OPT_ORDER  = ""              # order条件
    __OPT_FIELD  = "*"             # field条件
    __OPT_PARAM  = ()              # where值
    
    def __init__(self):
        self.__DB_FILE = 'data/default.db'
    
    def __GetConn(self): 
        #取数据库对象
        try:
            if self.__DB_CONN == None:
                self.__DB_CONN = sqlite3.connect(self.__DB_FILE)
        except Exception as ex:
            return "error: " + str(ex)
            
    def dbfile(self,name):
        self.__DB_FILE = 'data/' + name + '.db'
        return self
    
    def table(self,table):
        #设置表名
        self.__DB_TABLE = table
        return self
    
    
    def where(self,where,param):
        #WHERE条件
        if where:
            self.__OPT_WHERE = " WHERE " + where
            self.__OPT_PARAM = param
        return self
    
    
    def order(self,order):
        #ORDER条件
        if len(order):
            self.__OPT_ORDER = " ORDER BY "+order
        return self
    
    
    def limit(self,limit):
        #LIMIT条件
        if len(limit):
            self.__OPT_LIMIT = " LIMIT "+limit
        return self
    
    
    def field(self,field):
        #FIELD条件
        if len(field):
            self.__OPT_FIELD = field
        return self
    
    
    def select(self):
        #查询数据集
        self.__GetConn()
        try:
            sql = "SELECT " + self.__OPT_FIELD + " FROM " + self.__DB_TABLE + self.__OPT_WHERE + self.__OPT_ORDER + self.__OPT_LIMIT
            result = self.__DB_CONN.execute(sql,self.__OPT_PARAM)
            data = result.fetchall()
            #构造字曲系列
            if self.__OPT_FIELD != "*":
                field = self.__OPT_FIELD.split(',')
                tmp = []
                for row in data:
                    i=0
                    tmp1 = {}
                    for key in field:
                        tmp1[key] = row[i]
                        i += 1
                    tmp.append(tmp1)
                    del(tmp1)
                data = tmp
                del(tmp)
            else:
                #将元组转换成列表
                tmp = list(map(list,data))
                data = tmp
                del(tmp)
            self.__close()
            return data
        except Exception as ex:
            return "error: " + str(ex)
    
    
    def getField(self,keyName):
        #取回指定字段
        result = self.field(keyName).select();
        if len(result) == 1:
            return result[0][keyName]
        return result
    
    
    def setField(self,keyName,keyValue):
        #更新指定字段
        return self.save(keyName,(keyValue,))
        
    
    def find(self):
        #取一行数据
        result = self.limit("1").select()
        if len(result) == 1:
            return result[0]
        return result
    
    
    def count(self):
        #取行数
        key="COUNT(*)"
        data = self.field(key).select()
        try:
            return int(data[0][key])
        except:
            return 0
    
    
    def add(self,keys,param):
        #插入数据
        self.__GetConn()
        self.__DB_CONN.text_factory = str
        try:
            values=""
            for key in keys.split(','):
                values += "?,"
            values = values[0:len(values)-1];
            sql = "INSERT INTO "+self.__DB_TABLE+"("+keys+") "+"VALUES("+values+")"
            result = self.__DB_CONN.execute(sql,param)
            id = result.lastrowid
            self.__close()
            self.__DB_CONN.commit()
            return id
        except Exception as ex:
            return "error: " + str(ex)
    
    def addAll(self,keys,param):
        #插入数据
        self.__GetConn()
        self.__DB_CONN.text_factory = str
        try:
            values=""
            for key in keys.split(','):
                values += "?,"
            values = values[0:len(values)-1]
            sql = "INSERT INTO "+self.__DB_TABLE+"("+keys+") "+"VALUES("+values+")"
            result = self.__DB_CONN.execute(sql,param)
            return True
        except Exception as ex:
            return "error: " + str(ex)
        
    def commit(self):
        self.__close()
        self.__DB_CONN.commit()
    
    
    def save(self,keys,param):
        #更新数据
        self.__GetConn()
        self.__DB_CONN.text_factory = str
        try:
            opt = ""
            for key in keys.split(','):
                opt += key + "=?,"
            opt = opt[0:len(opt)-1]
            sql = "UPDATE " + self.__DB_TABLE + " SET " + opt+self.__OPT_WHERE
            
            import public
            public.writeFile('/tmp/test.pl',sql)
                        
            #处理拼接WHERE与UPDATE参数
            tmp = list(param)
            for arg in self.__OPT_PARAM:
                tmp.append(arg)
            self.__OPT_PARAM = tuple(tmp)
            result = self.__DB_CONN.execute(sql,self.__OPT_PARAM)
            self.__close()
            self.__DB_CONN.commit()
            return result.rowcount
        except Exception as ex:
            return "error: " + str(ex)
    
    def delete(self,id=None):
        #删除数据
        self.__GetConn()
        try:
            if id:
                self.__OPT_WHERE = " WHERE id=?"
                self.__OPT_PARAM = (id,)
            sql = "DELETE FROM " + self.__DB_TABLE + self.__OPT_WHERE
            result = self.__DB_CONN.execute(sql,self.__OPT_PARAM)
            self.__close()
            self.__DB_CONN.commit()
            return result.rowcount
        except Exception as ex:
            return "error: " + str(ex)
        
    
    def execute(self,sql,param):
        #执行SQL语句返回受影响行
        self.__GetConn()
        try:
            result = self.__DB_CONN.execute(sql,param)
            self.__DB_CONN.commit()
            return result.rowcount
        except Exception as ex:
            return "error: " + str(ex)
    
    
    def query(self,sql,param):
        #执行SQL语句返回数据集
        self.__GetConn()
        try:
            result = self.__DB_CONN.execute(sql,param)
            #将元组转换成列表
            data = list(map(list,result))
            return data
        except Exception as ex:
            return "error: " + str(ex)
        
    def create(self,name):
        #创建数据表
        self.__GetConn()
        import public
        script = public.readFile('data/' + name + '.sql')
        result = self.__DB_CONN.executescript(script)
        self.__DB_CONN.commit()
        return result.rowcount
        
    def fofile(self,filename):
        #执行脚本
        self.__GetConn()
        import public
        script = public.readFile(filename)
        result = self.__DB_CONN.executescript(script)
        self.__DB_CONN.commit()
        return result.rowcount
        
    def __close(self):
        #清理条件属性
        self.__OPT_WHERE = ""
        self.__OPT_FIELD = "*"
        self.__OPT_ORDER = ""
        self.__OPT_LIMIT = ""
        self.__OPT_PARAM = ()
    
    def close(self):
        #释放资源
        try:
            self.__DB_CONN.close()
            self.__DB_CONN = None
        except:
            pass
        
