# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------

import sqlite3
import os, time, sys

os.chdir('/www/server/panel')
if not 'class/' in sys.path:
    sys.path.insert(0, 'class/')
import public


class Sql():
    # ------------------------------
    # 数据库操作类 For sqlite3
    # ------------------------------
    __DB_FILE = None  # 数据库文件
    __DB_CONN = None  # 数据库连接对象
    __DB_TABLE = ""  # 被操作的表名称
    __OPT_WHERE = ""  # where条件
    __OPT_LIMIT = ""  # limit条件
    __OPT_ORDER = ""  # order条件
    __OPT_FIELD = "*"  # field条件
    __OPT_PARAM = ()  # where值


    def __init__(self, dbfile=None):
        if not os.path.exists("class/projectModel/content/"):
            os.makedirs("class/projectModel/content/")
        if not dbfile:
            self.__DB_FILE = 'class/projectModel/content/content.db'
            self.__LOCK = '/dev/shm/{}.pl'.format(self.__DB_FILE.replace('/', '_'))
        else:
            self.__DB_FILE ='class/projectModel/content/' + dbfile + '.db'
            self.__LOCK = '/dev/shm/{}.pl'.format(self.__DB_FILE.replace('/', '_'))
        if not os.path.exists(self.__DB_FILE):
            # 创建数据库
            conn = sqlite3.connect(self.__DB_FILE)
            conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_trackback):
        self.close()

    def __GetConn(self):
        # 取数据库对象
        try:
            if self.__DB_CONN == None:
                self.__DB_CONN = sqlite3.connect(self.__DB_FILE)
                self.__DB_CONN.text_factory = str
        except Exception as ex:
            return "error: " + str(ex)

    def dbfile(self, name):
        self.__DB_FILE = 'class/projectModel/content/' + name + '.db'
        return self

    def table(self, table):
        # 设置表名
        self.__DB_TABLE = table
        return self

    def where(self, where, param):
        # WHERE条件
        if where:
            self.__OPT_WHERE = " WHERE " + where
            self.__OPT_PARAM = self.__to_tuple(param)
        return self

    def __to_tuple(self, param):
        # 将参数转换为tuple
        if type(param) != tuple:
            if type(param) == list:
                param = tuple(param)
            else:
                param = (param,)
        return param

    def order(self, order):
        # ORDER条件
        if len(order):
            self.__OPT_ORDER = " ORDER BY " + order
        return self

    def limit(self, limit):
        # LIMIT条件
        if len(limit):
            self.__OPT_LIMIT = " LIMIT " + limit
        return self

    def field(self, field):
        # FIELD条件
        if len(field):
            self.__OPT_FIELD = field
        return self

    def select(self):
        # 查询数据集
        self.__GetConn()
        try:
            self.__get_columns()
            sql = "SELECT " + self.__OPT_FIELD + " FROM " + self.__DB_TABLE + self.__OPT_WHERE + self.__OPT_ORDER + self.__OPT_LIMIT
            result = self.__DB_CONN.execute(sql, self.__OPT_PARAM)
            data = result.fetchall()
            # 构造字典系列
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
                # 将元组转换成列表
                tmp = list(map(list, data))
                data = tmp
                del (tmp)
            self.__close()
            return data
        except Exception as ex:
            return "error: " + str(ex)

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
            tmp_cols = self.query('PRAGMA table_info(' + self.__DB_TABLE + ')', ())
            cols = []
            for col in tmp_cols:
                if len(col) > 2: cols.append('`' + col[1] + '`')
            if len(cols) > 0: self.__OPT_FIELD = ','.join(cols)

    def getField(self, keyName):
        # 取回指定字段
        try:
            result = self.field(keyName).select()
            if len(result) != 0:
                return result[0][keyName]
            return result
        except:
            return None

    def setField(self, keyName, keyValue):
        # 更新指定字段
        return self.save(keyName, (keyValue,))

    def find(self):
        # 取一行数据
        try:
            result = self.limit("1").select()
            if len(result) == 1:
                return result[0]
            return result
        except:
            return None

    def count(self):
        # 取行数
        key = "COUNT(*)"
        data = self.field(key).select()
        try:
            return int(data[0][key])
        except:
            return 0

    def add(self, keys, param):
        # 插入数据
        self.write_lock()
        self.__GetConn()
        self.__DB_CONN.text_factory = str
        try:
            values = ""
            for key in keys.split(','):
                values += "?,"
            values = values[0:len(values) - 1]
            sql = "INSERT INTO " + self.__DB_TABLE + "(" + keys + ") " + "VALUES(" + values + ")"
            result = self.__DB_CONN.execute(sql, self.__to_tuple(param))
            id = result.lastrowid
            self.__close()
            self.__DB_CONN.commit()
            self.rm_lock()
            return id
        except Exception as ex:
            return "error: " + str(ex)

    # 插入数据
    def insert(self, pdata):
        if not pdata: return False
        keys, param = self.__format_pdata(pdata)
        return self.add(keys, param)

    # 更新数据
    def update(self, pdata):
        if not pdata: return False
        keys, param = self.__format_pdata(pdata)
        return self.save(keys, param)

    # 构造数据
    def __format_pdata(self, pdata):
        keys = pdata.keys()
        keys_str = ','.join(keys)
        param = []
        for k in keys: param.append(pdata[k])
        return keys_str, tuple(param)

    def addAll(self, keys, param):
        # 插入数据
        self.write_lock()
        self.__GetConn()
        self.__DB_CONN.text_factory = str
        try:
            values = ""
            for key in keys.split(','):
                values += "?,"
            values = values[0:len(values) - 1]
            sql = "INSERT INTO " + self.__DB_TABLE + "(" + keys + ") " + "VALUES(" + values + ")"
            result = self.__DB_CONN.execute(sql, self.__to_tuple(param))
            self.rm_lock()
            return True
        except Exception as ex:
            return "error: " + str(ex)

    def commit(self):
        self.__close()
        self.__DB_CONN.commit()

    def save(self, keys, param):
        # 更新数据
        self.write_lock()
        self.__GetConn()
        self.__DB_CONN.text_factory = str
        try:
            opt = ""
            for key in keys.split(','):
                opt += key + "=?,"
            opt = opt[0:len(opt) - 1]
            sql = "UPDATE " + self.__DB_TABLE + " SET " + opt + self.__OPT_WHERE

            # 处理拼接WHERE与UPDATE参数
            tmp = list(self.__to_tuple(param))
            for arg in self.__OPT_PARAM:
                tmp.append(arg)
            self.__OPT_PARAM = tuple(tmp)
            result = self.__DB_CONN.execute(sql, self.__OPT_PARAM)
            self.__close()
            self.__DB_CONN.commit()
            self.rm_lock()
            return result.rowcount
        except Exception as ex:
            return "error: " + str(ex)

    def delete(self, id=None):
        # 删除数据
        self.write_lock()
        self.__GetConn()
        try:
            if id:
                self.__OPT_WHERE = " WHERE id=?"
                self.__OPT_PARAM = (id,)
            sql = "DELETE FROM " + self.__DB_TABLE + self.__OPT_WHERE
            result = self.__DB_CONN.execute(sql, self.__OPT_PARAM)
            self.__close()
            self.__DB_CONN.commit()
            self.rm_lock()
            return result.rowcount
        except Exception as ex:
            return "error: " + str(ex)

    def execute(self, sql, param=()):
        # 执行SQL语句返回受影响行
        self.write_lock()
        self.__GetConn()
        try:
            result = self.__DB_CONN.execute(sql, self.__to_tuple(param))
            self.__DB_CONN.commit()
            self.rm_lock()
            return result.rowcount
        except Exception as ex:
            return "error: " + str(ex)

    # 是否有锁
    def is_lock(self):
        n = 0
        while os.path.exists(self.__LOCK):
            n += 1
            if n > 100:
                self.rm_lock()
                break
            time.sleep(0.01)

    # 写锁
    def write_lock(self):
        self.is_lock()
        with open(self.__LOCK, 'wb+') as f:
            f.close()

    # 解锁
    def rm_lock(self):
        if os.path.exists(self.__LOCK):
            try:
                os.remove(self.__LOCK)
            except:
                pass

    def query(self, sql, param=()):
        # 执行SQL语句返回数据集
        self.__GetConn()
        try:
            result = self.__DB_CONN.execute(sql, self.__to_tuple(param))
            # 将元组转换成列表
            data = list(map(list, result))
            return data
        except Exception as ex:
            return "error: " + str(ex)

    def create(self, name):
        # 创建数据表
        self.write_lock()
        self.__GetConn()
        script = public.readFile('data/' + name + '.sql')
        result = self.__DB_CONN.executescript(script)
        self.__DB_CONN.commit()
        self.rm_lock()
        return result.rowcount

    def fofile(self, filename):
        # 执行脚本
        self.write_lock()
        self.__GetConn()
        script = public.readFile(filename)
        result = self.__DB_CONN.executescript(script)
        self.__DB_CONN.commit()
        self.rm_lock()
        return result.rowcount

    def __close(self):
        # 清理条件属性
        self.__OPT_WHERE = ""
        self.__OPT_FIELD = "*"
        self.__OPT_ORDER = ""
        self.__OPT_LIMIT = ""
        self.__OPT_PARAM = ()

    def close(self):
        # 释放资源
        try:
            self.__DB_CONN.close()
            self.__DB_CONN = None
        except:
            pass

