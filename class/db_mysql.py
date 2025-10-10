# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------

import re
import sys
import os

import public
try:
    import pymysql
except ImportError:
    public.ExecShell("btpip install pymysql")
    try:
        import pymysql
    except ImportError:
        pass


class panelMysql:

    DB_ERROR = None
    def __init__(self):
        self.__CONN_KWARGS = {
            "host": "localhost",
            "port": 3306,
            "user": "root",
            "password": None,
            "connect_timeout": 5,
            "read_timeout": 60,
            "write_timeout": 60,
            "unix_socket": None,
        }
        self.__DB_PREFIX = ''
        self.__DB_CONN = None
        self.__DB_CUR = None
        self.__DB_ERR = None
        self.__DB_TABLE = ""  # 被操作的表名称
        self.__OPT_WHERE = ""  # where条件
        self.__OPT_LIMIT = ""  # limit条件
        self.__OPT_ORDER = ""  # order条件
        self.__OPT_FIELD = "*"  # field条件
        self.__OPT_PARAM = ()  # where值
        self._USER = None
        self._ex = None


    def set_name(self, name):
        self.__DB_NAME = str(name)
        return self

    def set_prefix(self, prefix):
        self.__DB_PREFIX = prefix
        return self

    def set_host(self, host, port, name, user, password, prefix='', **kwargs):
        self.__CONN_KWARGS["host"] = host
        self.__CONN_KWARGS["port"] = int(port)
        self.__CONN_KWARGS["user"] = str(user)
        self.__CONN_KWARGS["password"] = str(password)
        self.__CONN_KWARGS.update(kwargs)

        self.__DB_PREFIX = prefix
        if not self.__GetConn():
            return False
        return self

    # 连接MYSQL数据库
    def __GetConn(self):
        if self.__CONN_KWARGS["host"] == "localhost":
            myconf = public.readFile("/etc/my.cnf")
            if myconf:
                socket_re = re.search(r"\nsocket\s*=\s*([^\n]+)", myconf)
                if socket_re:
                    self.__CONN_KWARGS["unix_socket"] = socket_re.group(1)
                elif os.path.exists("/tmp/mysql.sock"):
                    self.__CONN_KWARGS["unix_socket"] = "/tmp/mysql.sock"
            elif os.path.exists("/tmp/mysql.sock"):
                self.__CONN_KWARGS["unix_socket"] = "/tmp/mysql.sock"

            if myconf:
                port_re = re.search(r"\nport\s*=\s*([0-9]+)", myconf)
                if port_re:
                    self.__CONN_KWARGS["port"] = int(port_re.group(1))
                else:
                    self.__CONN_KWARGS["port"] == "3306"
            else:
                self.__CONN_KWARGS["port"] == "3306"

            if self.__CONN_KWARGS["password"] is None:
                self.__CONN_KWARGS["password"] = public.M("config").where("id=?",(1,)).getField("mysql_root")

            password_str = str(self.__CONN_KWARGS["password"])
            if any(ord(char) > 255 for char in password_str):
                encoded_password =self.__CONN_KWARGS["password"].encode('utf-8')
                self.__CONN_KWARGS["password"]=encoded_password

        try:
            self.__DB_CONN = pymysql.connect(**self.__CONN_KWARGS)
            self.__DB_CUR = self.__DB_CONN.cursor()
            return True
        # except pymysql.err.OperationalError as err:
        except Exception as err:
            self.__DB_ERR = err
            self._ex = err
            if self.__CONN_KWARGS["user"] == "root" and str(self.__CONN_KWARGS["host"]).lower() == "localhost":
                exec_sql = "/usr/bin/mysql --user=root --password='{password}' --default-character-set=utf8 -e 'SET sql_notes = 0;{sql}'"
                if str(err).find("Access denied for user 'root'@'::1'") != -1 or str(err).find("Host '::1' is not allowed to connect") != -1:
                    sql = "drop user `root`@`::1`;'"
                    public.ExecShell(exec_sql.format(password=self.__CONN_KWARGS["password"], sql=sql), env={"MYSQL_PWD": self.__CONN_KWARGS["password"]})
                    sql = "create user `root`@`::1` identified by \"{root_password}\";'".format(root_password=self.__CONN_KWARGS["password"])
                    public.ExecShell(exec_sql.format(password=self.__CONN_KWARGS["password"], sql=sql), env={"MYSQL_PWD": self.__CONN_KWARGS["password"]})
                    sql = "grant all privileges on *.* to `root`@`::1`;'"
                    public.ExecShell(exec_sql.format(password=self.__CONN_KWARGS["password"], sql=sql), env={"MYSQL_PWD": self.__CONN_KWARGS["password"]})
                    sql = "flush privileges;'"
                    public.ExecShell(exec_sql.format(password=self.__CONN_KWARGS["password"], sql=sql), env={"MYSQL_PWD": self.__CONN_KWARGS["password"]})
                elif str(err).find("Access denied for user 'root'@'127.0.0.1'") != -1 or str(err).find("Host '127.0.0.1' is not allowed to connect") != -1:
                    sql = "drop user `root`@`127.0.0.1`;'"
                    public.ExecShell(exec_sql.format(password=self.__CONN_KWARGS["password"], sql=sql), env={"MYSQL_PWD": self.__CONN_KWARGS["password"]})
                    sql = "create user `root`@`127.0.0.1` identified by \"{root_password}\";'".format(root_password=self.__CONN_KWARGS["password"])
                    public.ExecShell(exec_sql.format(password=self.__CONN_KWARGS["password"], sql=sql), env={"MYSQL_PWD": self.__CONN_KWARGS["password"]})
                    sql = "grant all privileges on *.* to `root`@`127.0.0.1`;'"
                    public.ExecShell(exec_sql.format(password=self.__CONN_KWARGS["password"], sql=sql), env={"MYSQL_PWD": self.__CONN_KWARGS["password"]})
                    sql = "flush privileges;'"
                    public.ExecShell(exec_sql.format(password=self.__CONN_KWARGS["password"], sql=sql), env={"MYSQL_PWD": self.__CONN_KWARGS["password"]})

                try:
                    self.__DB_CONN = pymysql.connect(**self.__CONN_KWARGS)
                    self.__DB_CUR = self.__DB_CONN.cursor()
                    return True
                except Exception as err:
                    self.__DB_ERR = err
                    self._ex = err


        try:
            try:
                if sys.version_info[0] != 2:
                    pymysql.install_as_MySQLdb()
                import MySQLdb
                if sys.version_info[0] == 2:
                    reload(MySQLdb)
            except:
                try:
                    pymysql.install_as_MySQLdb()
                    import MySQLdb
                except Exception as err:
                    self.__DB_ERR = err
                    self._ex = err
                    return False
            if self.__CONN_KWARGS["host"] == "localhost":
                self.__DB_CONN = MySQLdb.connect(host=self.__CONN_KWARGS["host"], port=self.__CONN_KWARGS["port"], user=self.__CONN_KWARGS["user"], passwd=str(self.__CONN_KWARGS["password"]), charset="utf8", connect_timeout=self.__CONN_KWARGS["connect_timeout"], unix_socket=self.__CONN_KWARGS["unix_socket"])
            else:
                self.__DB_CONN = MySQLdb.connect(host=self.__CONN_KWARGS["host"], port=self.__CONN_KWARGS["port"], user=self.__CONN_KWARGS["user"], passwd=str(self.__CONN_KWARGS["password"]), charset="utf8", connect_timeout=self.__CONN_KWARGS["connect_timeout"])
            self.__DB_CUR = self.__DB_CONN.cursor()
            return True
        except MySQLdb.Error as err:
            # pass
            self.__DB_ERR = err
            self._ex = err
        self.DB_ERROR = self._ex
        public.WriteLog("数据库管理", "数据库连接失败:{}".format(self._ex))
        return False

    def table(self, table):
        # 设置表名
        self.__DB_TABLE = self.__DB_PREFIX + table
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
        limit = str(limit)
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
        if not self.__DB_CUR: return self.__DB_ERR
        try:
            self.__get_columns()
            sql = "SELECT " + self.__OPT_FIELD + " FROM " + self.__DB_TABLE + self.__OPT_WHERE + self.__OPT_ORDER + self.__OPT_LIMIT
            self.__DB_CUR.execute(sql, self.__OPT_PARAM)
            data = self.__DB_CUR.fetchall()
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
            self._ex = ex
            return ex

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
            self._ex = ex
            return ex

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
        keys_tmp = []
        for k in keys:
            keys_tmp.append("`{}`".format(k))
        keys_str = ','.join(keys_tmp)

        param = []
        for k in keys:
            # if pdata[k] == None: pdata[k] = ''
            param.append(pdata[k])
        return keys_str, tuple(param)

    def addAll(self, keys, param):
        # 插入数据
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
            self._ex = ex
            return ex

    def commit(self):
        self.__close()
        self.__DB_CONN.commit()

    def save(self, keys, param):
        # 更新数据
        self.__GetConn()
        self.__DB_CONN.text_factory = str
        try:
            opt = ""
            for key in keys.split(','):
                opt += key + "=%s,"
            opt = opt[0:len(opt) - 1]
            sql = "UPDATE " + self.__DB_TABLE + " SET " + opt + self.__OPT_WHERE

            # 处理拼接WHERE与UPDATE参数
            if param:
                tmp = list(self.__to_tuple(param))
                for arg in self.__OPT_PARAM:
                    tmp.append(arg)
                self.__OPT_PARAM = tuple(tmp)
                self.__DB_CUR.execute(sql, self.__OPT_PARAM)
            else:
                self.__DB_CUR.execute(sql)
            self.__close()
            self.__DB_CONN.commit()
            return self.__DB_CUR.rowcount
        except Exception as ex:
            self._ex = ex
            return ex

    def delete(self, id=None):
        # 删除数据
        self.__GetConn()
        try:
            if id:
                self.__OPT_WHERE = " WHERE id=%s"
                self.__OPT_PARAM = (id,)
            sql = "DELETE FROM " + self.__DB_TABLE + self.__OPT_WHERE
            self.__DB_CUR.execute(sql, self.__OPT_PARAM)
            self.__close()
            self.__DB_CONN.commit()
            return self.__DB_CUR.rowcount
        except Exception as ex:
            return "error: " + str(ex)

    def execute(self, sql, param=()):
        # 执行SQL语句返回受影响行
        if not self.__GetConn(): return self.__DB_ERR
        try:
            if param:
                self.__OPT_PARAM = list(self.__to_tuple(param))
                result = self.__DB_CUR.execute(sql, self.__OPT_PARAM)
            else:
                result = self.__DB_CUR.execute(sql)
            self.__DB_CONN.commit()
            self.__close()
            return result
        except Exception as ex:
            self._ex = ex
            return ex

    def query(self, sql, is_close=True, param=()):
        # 执行SQL语句返回数据集
        if not self.__GetConn(): return self.__DB_ERR
        try:
            if param:
                self.__OPT_PARAM = list(self.__to_tuple(param))
                self.__DB_CUR.execute(sql, self.__OPT_PARAM)
            else:
                self.__DB_CUR.execute(sql)
            result = self.__DB_CUR.fetchall()
            # 将元组转换成列表
            data = list(map(list, result))
            if is_close: self.__Close()
            return data
        except Exception as ex:
            self._ex = ex
            return ex

    # 关闭连接
    def __Close(self):
        self.__DB_CUR.close()
        self.__DB_CONN.close()

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
            self.__DB_CUR.close()
            self.__DB_CUR.close()
        except:
            pass
