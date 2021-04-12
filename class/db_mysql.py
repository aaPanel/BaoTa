#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------
import re, os, sys, public, json
import pymysql


class mysql:
    __DB_PASS = ''
    __DB_USER = ''
    __DB_NAME = ''
    __DB_PORT = 3306
    __DB_HOST = 'localhost'
    __DB_PREFIX = ''
    __DB_CONN = None
    __DB_CUR = None
    __DB_ERR = None
    __DB_NET = None
    __DB_TABLE = ""  # 被操作的表名称
    __OPT_WHERE = ""  # where条件
    __OPT_LIMIT = ""  # limit条件
    __OPT_ORDER = ""  # order条件
    __OPT_FIELD = "*"  # field条件
    __OPT_PARAM = ()  # where值

    def __init__(self):
        pass

    def set_name(self, name):
        self.__DB_NAME = name
        return self

    def set_host(self, host, port, name, username, password, prefix=''):
        self.__DB_HOST = host
        self.__DB_PORT = port
        self.__DB_NAME = name
        self.__DB_USER = username
        self.__DB_PASS = password
        self.__DB_PREFIX = prefix
        return self

    #连接MYSQL数据库
    def __GetConn(self):
        if self.__DB_NET: return True
        try:
            self.__DB_CONN = pymysql.connect(host=self.__DB_HOST,
                                             port=self.__DB_PORT,
                                             user=self.__DB_USER,
                                             passwd=self.__DB_PASS)

            self.__DB_CUR = self.__DB_CONN.cursor()
            self.__DB_NET = True
            return True
        except pymysql.Error as e:
            self.__DB_ERR = e
            return False

    def table(self, table):
        #设置表名
        self.__DB_TABLE = self.__DB_PREFIX + table
        return self

    def where(self, where, param):
        #WHERE条件
        if where:
            self.__OPT_WHERE = " WHERE " + where
            self.__OPT_PARAM = self.__to_tuple(param)
        return self

    def __to_tuple(self, param):
        #将参数转换为tuple
        if type(param) != tuple:
            if type(param) == list:
                param = tuple(param)
            else:
                param = (param, )
        return param

    def order(self, order):
        #ORDER条件
        if len(order):
            self.__OPT_ORDER = " ORDER BY " + order
        return self

    def limit(self, limit):
        #LIMIT条件
        limit = str(limit)
        if len(limit):
            self.__OPT_LIMIT = " LIMIT " + limit
        return self

    def field(self, field):
        #FIELD条件
        if len(field):
            self.__OPT_FIELD = field
        return self

    def select(self):
        #查询数据集
        self.__GetConn()
        try:
            self.__get_columns()
            sql = "SELECT " + self.__OPT_FIELD + " FROM " + self.__DB_TABLE + self.__OPT_WHERE + self.__OPT_ORDER + self.__OPT_LIMIT
            self.__DB_CUR.execute(sql, self.__OPT_PARAM)
            data = self.__DB_CUR.fetchall()
            #构造字典系列
            if self.__OPT_FIELD != "*":
                fields = self.__format_field(self.__OPT_FIELD.split(','))
                tmp = []
                for row in data:
                    i = 0
                    tmp1 = {}
                    for key in fields:
                        tmp1[key.strip('`')] = row[i]
                        i += 1
                    tmp.append(tmp1)
                    del (tmp1)
                data = tmp
                del (tmp)
            else:
                #将元组转换成列表
                tmp = list(map(list, data))
                data = tmp
                del (tmp)
            self.__close()
            return data
        except Exception as ex:
            return public.get_error_info()

    def get(self):
        self.__get_columns()
        return self.select()

    def __format_field(self, field):
        import re
        fields = []
        for key in field:
            s_as = re.search(r'\s+as\s+', key, flags=re.IGNORECASE)
            if s_as:
                as_tip = s_as.group()
                key = key.split(as_tip)[1]
            fields.append(key)
        return fields

    def __get_columns(self):
        if self.__OPT_FIELD == '*':
            tmp_cols = self.query(
                "select COLUMN_NAME from information_schema.COLUMNS where table_name = '{}' and table_schema = '{}';"
                .format(self.__DB_TABLE, self.__DB_NAME), False)
            cols = []
            for col in tmp_cols:
                cols.append('`' + col[0] + '`')
            if len(cols) > 0: self.__OPT_FIELD = ','.join(cols)

    def getField(self, keyName):
        #取回指定字段
        try:
            result = self.field(keyName).select()
            if len(result) != 0:
                return result[0][keyName]
            return result
        except:
            return None

    def setField(self, keyName, keyValue):
        #更新指定字段
        return self.save(keyName, (keyValue, ))

    def find(self):
        #取一行数据
        try:
            result = self.limit("1").select()
            if len(result) == 1:
                return result[0]
            return result
        except:
            return None

    def count(self):
        #取行数
        key = "COUNT(*)"
        data = self.field(key).select()
        try:
            return int(data[0][key])
        except:
            return 0

    def add(self, keys, param):
        #插入数据
        self.__GetConn()
        self.__DB_CONN.text_factory = str
        try:
            values = ""
            for key in keys.split(','):
                values += "%s,"
            values = values[0:len(values) - 1]
            sql = "INSERT INTO " + self.__DB_TABLE + "(" + keys + ") " + "VALUES(" + values + ")"
            self.__DB_CUR.execute(sql, self.__to_tuple(param))
            id = self.__DB_CUR.lastrowid
            self.__close()
            self.__DB_CONN.commit()
            return id
        except Exception as ex:
            return "error: " + str(ex)

    #插入数据
    def insert(self, pdata):
        if not pdata: return False
        keys, param = self.__format_pdata(pdata)
        return self.add(keys, param)

    #更新数据
    def update(self, pdata):
        if not pdata: return False
        keys, param = self.__format_pdata(pdata)
        return self.save(keys, param)

    #构造数据
    def __format_pdata(self, pdata):
        keys = pdata.keys()
        keys_tmp = []
        for k in keys:
            keys_tmp.append("`{}`".format(k))
        keys_str = ','.join(keys_tmp)

        param = []
        for k in keys:
            #if pdata[k] == None: pdata[k] = ''
            param.append(pdata[k])
        return keys_str, tuple(param)

    def addAll(self, keys, param):
        #插入数据
        self.__GetConn()
        self.__DB_CONN.text_factory = str
        try:
            values = ""
            for key in keys.split(','):
                values += "%s,"
            values = values[0:len(values) - 1]
            sql = "INSERT INTO " + self.__DB_TABLE + "(" + keys + ") " + "VALUES(" + values + ")"
            result = self.__DB_CUR.execute(sql, self.__to_tuple(param))
            return True
        except Exception as ex:
            return "error: " + str(ex)

    def commit(self):
        self.__close()
        self.__DB_CONN.commit()

    def save(self, keys, param):
        #更新数据
        self.__GetConn()
        self.__DB_CONN.text_factory = str
        try:
            opt = ""
            for key in keys.split(','):
                opt += key + "=%s,"
            opt = opt[0:len(opt) - 1]
            sql = "UPDATE " + self.__DB_TABLE + " SET " + opt + self.__OPT_WHERE

            #处理拼接WHERE与UPDATE参数
            tmp = list(self.__to_tuple(param))
            for arg in self.__OPT_PARAM:
                tmp.append(arg)
            self.__OPT_PARAM = tuple(tmp)
            self.__DB_CUR.execute(sql, self.__OPT_PARAM)
            self.__close()
            self.__DB_CONN.commit()
            return self.__DB_CUR.rowcount
        except Exception as ex:
            return "error: " + str(ex)

    def delete(self, id=None):
        #删除数据
        self.__GetConn()
        try:
            if id:
                self.__OPT_WHERE = " WHERE id=%s"
                self.__OPT_PARAM = (id, )
            sql = "DELETE FROM " + self.__DB_TABLE + self.__OPT_WHERE
            self.__DB_CUR.execute(sql, self.__OPT_PARAM)
            self.__close()
            self.__DB_CONN.commit()
            return self.__DB_CUR.rowcount
        except Exception as ex:
            return "error: " + str(ex)

    def execute(self, sql, is_close=True):
        #执行SQL语句返回受影响行
        if not self.__GetConn(): return self.__DB_ERR
        try:
            result = self.__DB_CUR.execute(sql)
            self.__DB_CONN.commit()
            if is_close: self.__close()
            return result
        except Exception as ex:
            return ex

    def query(self, sql, is_close=True):
        #执行SQL语句返回数据集
        if not self.__GetConn(): return self.__DB_ERR
        try:
            self.__DB_CUR.execute(sql)
            result = self.__DB_CUR.fetchall()
            #将元组转换成列表
            data = list(map(list, result))
            if is_close: self.__Close()
            return data
        except Exception as ex:
            return ex

    #关闭连接
    def __Close(self):
        self.__DB_CUR.close()
        self.__DB_CONN.close()

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
            self.__DB_CUR.close()
            self.__DB_CUR.close()
        except:
            pass