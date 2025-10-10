#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------
import json
import os
import sys
import sqlite3
import re
from typing import List, Optional

os.chdir("/www/server/panel")
if not "class/" in sys.path:
    sys.path.insert(0,"class/")

import public

class Sql():
    #------------------------------
    # 数据库操作类 For sqlite3
    #------------------------------
    __LOCK = "/dev/shm/sqlite_lock.pl"
    __READ_ONLY_TIPS = "/dev/shm/sqlite_read_only.pl"
    __LAST_KEY = "BT-0x:"
    __ENCRYPT_KEYS = ["password","salt","email","mysql_root","db_password"]
    __DEFAULT_DB_PATH = os.path.join(public.get_panel_path(), "data/db/default.db")

    __DATABASES_PATH = os.path.join(public.get_panel_path(), "config/databases.json")
    ERR_INFO = None

    def __init__(self):
        self.__DB_FILE = None  # 数据库文件
        self.__DB_CONN: Optional[sqlite3.Connection] = None  # 数据库连接对象
        self.__DB_TABLE = ""  # 被操作的表名称
        self.__OPT_WHERE = ""  # where条件
        self.__OPT_LIMIT = ""  # limit条件
        self.__OPT_ORDER = ""  # order条件
        self.__OPT_FIELD = "*"  # field条件
        self.__OPT_PARAM = ()  # where值
        self.__DB_NAME = "" # 数据库名称

        self.__TB_INFO = {} # 表信息
        self.__TEMP_PATH = None
        self.__READ_ONLY = False

    def __enter__(self):
        return self

    def __exit__(self,exc_type,exc_value,exc_trackback):
        self.close()

    def __memory_user_db(self):
        '''
            @name 加载数据库到内存
            @return None
        '''
        if not self.__DB_FILE:
            return False

        if os.path.getsize(self.__DB_FILE) > 1024 * 1024 * 2:
            # 数据库文件大于2M，不加载到内存
            return False


        # 读取用户数据库文件
        src_f = open(self.__DB_FILE, 'rb')
        src_data = src_f.read()
        src_f.close()

        # 创建临时目录到内存盘
        import tempfile
        tempfile.tempdir = '/dev/shm'
        self.__TEMP_PATH = tempfile.TemporaryDirectory()
        temp_file = os.path.join(self.__TEMP_PATH.name, '{}.db'.format(public.md5(self.__DB_FILE)))

        # 写入到临时文件
        dst_f = open(temp_file, 'wb')
        dst_f.write(src_data)
        dst_f.close()

        # 将临时文件路径赋值给数据库文件，并标记为只读
        self.__DB_FILE = temp_file
        self.__READ_ONLY = True
        public.writeFile(self.__READ_ONLY_TIPS, '1')
        return True


    def __clear_memory_user_db(self):
        '''
            @name 清理内存数据库
            @return None
        '''
        if not self.__TEMP_PATH:
            return

        # 释放临时目录，取消只读标记
        self.__TEMP_PATH.cleanup()
        self.__TEMP_PATH = None
        self.__READ_ONLY = False
        if os.path.exists(self.__READ_ONLY_TIPS):
            os.remove(self.__READ_ONLY_TIPS)

    def __get_db_path(self):
        if self.__DB_FILE is not None:
            return

        if self.__DB_NAME:
            # 有指定数据库名称的情况
            databases_dict = json.loads(public.readFile(self.__DATABASES_PATH))
            for db_name, tb_dict in databases_dict.items():
                if self.__DB_NAME in tb_dict:
                    self.__DB_FILE = os.path.join(public.get_panel_path(), "data/db", db_name)
                    self.__TB_INFO = tb_dict[self.__DB_NAME]
                    return
        else:
            # 未指定数据库名称的情况
            if not self.__DB_TABLE:
                self.__DB_FILE = self.__DEFAULT_DB_PATH
                return
            try:
                databases_dict = json.loads(public.readFile(self.__DATABASES_PATH))
                for db_name, tb_dict in databases_dict.items():
                    if self.__DB_TABLE in tb_dict:
                        self.__DB_FILE = os.path.join(public.get_panel_path(), "data/db", db_name)
                        self.__TB_INFO = tb_dict[self.__DB_TABLE]
                        return
            except Exception as err:
                pass

        # 使用默认数据库
        self.__DB_FILE = self.__DEFAULT_DB_PATH
        return


    def __GetConn(self):
        #取数据库对象
        self.__get_db_path()
        try:
            if self.__DB_CONN == None:
                if os.path.exists(self.__DB_FILE) and os.path.getsize(self.__DB_FILE) == 0:
                    os.remove(self.__DB_FILE)
                self.__DB_CONN = sqlite3.connect(self.__DB_FILE)
                self.__DB_CONN.text_factory = lambda x: str(x, 'utf-8', 'ignore')

                # 处理因磁盘空间不足或没权限导致用户表无法打开的问题
                try:
                    self.__DB_CONN.execute("SELECT name FROM sqlite_master LIMIT 1")
                except Exception as ex:
                    str_ex = str(ex)
                    if "unable to open database file" in str_ex:
                        # 加载用户数据库到内存盘，并标记为只读
                        if self.__memory_user_db():

                            # 重新连接数据库
                            self.__DB_CONN = sqlite3.connect(self.__DB_FILE)
                            self.__DB_CONN.text_factory = str
                        else:
                            disk_status,err_msg = public.check_disk_status()
                            raise public.PanelError("打开数据库失败[{}]: {}".format(disk_status,err_msg))

            if "sql" in self.__TB_INFO and self.__TB_INFO.get("sql"):
                result = self.__DB_CONN.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?;", (self.__DB_TABLE,))
                if list(map(list,result))[0][0] == 0:
                    self.__DB_CONN.execute(self.__TB_INFO["sql"])
        except Exception as ex:
            return "error: " + str(ex)

    def set_dbfile(self,path):
        self.__DB_FILE = path
        return self

    def connect(self):
        #连接数据库
        self.__GetConn()
        return self

    def dbfile(self,name: str):
        if not name.endswith(".db"): # 兼容老的
            name += ".db"
        #设置数据库文件
        self.__DB_FILE = os.path.join(public.get_panel_path(), "data", name)
        return self

    def table(self,table):
        #设置表名
        self.__DB_TABLE = table
        return self

    def db(self,name):
        # 设置数据库名称，用于判断数据库文件
        self.__DB_NAME = name
        return self

    def where(self,where,param):
        #WHERE条件
        if where:
            self.__OPT_WHERE = " WHERE " + where
            self.__OPT_PARAM = self.__to_tuple(param)
        return self

    def __to_tuple(self,param):
        #将参数转换为tuple
        if type(param) != tuple:
            if type(param) == list:
                param = tuple(param)
            else:
                param = (param,)
        return param


    def order(self,order):
        #ORDER条件
        if len(order):
            self.__OPT_ORDER = " ORDER BY "+order
        return self


    def limit(self,limit,offset = 0):
        #LIMIT条件

        if limit and not offset:
            self.__OPT_LIMIT = " LIMIT {}".format(limit)
        elif limit and offset:
            self.__OPT_LIMIT = " LIMIT {},{}".format(offset,limit)
        return self


    def field(self,field):
        #FIELD条件
        if len(field):
            self.__OPT_FIELD = field
        return self

    def query(self, sql, param=(), transfer_list=True):
        self.ERR_INFO = None
        # 执行SQL语句返回数据集
        self.__GetConn()
        try:
            result = self.__DB_CONN.execute(sql, self.__to_tuple(param))
            # self.log("result:" + str(result))
            if transfer_list:
                # 将元组转换成列表
                data = list(map(list, result))
            else:
                data = result
            return data
        except Exception as ex:
            self.ERR_INFO = str(ex)
            return "error: " + str(ex)
    def query(self,sql,param = ()):
        self.ERR_INFO = None
        #执行SQL语句返回数据集
        self.__GetConn()
        try:
            result = self.__DB_CONN.execute(sql,self.__to_tuple(param))

            #将元组转换成列表
            data = list(map(list,result))

            return data
        except Exception as ex:
            self.ERR_INFO = str(ex)
            try:
                if 'unable to open database file' in str(ex):
                    self.clear_files()

                    result = self.__DB_CONN.execute(sql,self.__to_tuple(param))
                    data = list(map(list,result))
                    return data
            except:pass
            return "error: " + str(ex)


    def select(self,num=0):

        self.ERR_INFO = None
        #查询数据集
        self.__GetConn()
        try:
            self.__get_columns()

            sql = "SELECT " + self.__OPT_FIELD + " FROM " + self.__DB_TABLE + self.__OPT_WHERE + self.__OPT_ORDER + self.__OPT_LIMIT
            result = self.__DB_CONN.execute(sql,self.__OPT_PARAM)
            data = result.fetchall()
            #构造字典系列
            if self.__OPT_FIELD != "*":
                fields = self.__format_field(self.__OPT_FIELD.split(','))
                tmp = []
                for row in data:
                    i=0
                    tmp1 = {}
                    for key in fields:
                        tmp1[key.strip('`')] = row[i]
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
            self._close()
            data = self.de_crypt(data)

            if self.__READ_ONLY:
                self.ERR_INFO = 'database is read only!'
            return data
        except Exception as ex:
            ex_str = str(ex)
            self.ERR_INFO = ex_str
            re_column = re.compile(r"no such column:\s+(?P<column>\S+)")
            res = re_column.search(ex_str)
            if res:
                column = res.group("column")
                if self.__TB_INFO:
                    for i in self.__TB_INFO.get("fields", []):
                        if isinstance(i, list) and len(i) == 6 and i[1] == column:
                            # 处理字符串类型默认值
                            if i[2].lower() in [ 'text', 'varchar'] and i[4] == "":
                                i[4] = "''"
                            res = self.execute("ALTER TABLE {} ADD {} {} DEFAULT {}".format(self.__DB_TABLE, column, i[2], i[4]))
                            # 如果添加字段成功，且重试次数<3次，则重新查询
                            if isinstance(res, int) and num < 3:
                                num +=1
                                return self.select(num)

            if "disk I/O error" in ex_str:
                return []

            # 处理firewall_new表的异常
            if ("malformed database schema" in ex_str or "file is encrypted or is not a database" in ex_str) and self.__DB_TABLE in ['firewall_new']:
                bak_file = "{}.{}".format(self.__DB_FILE, public.format_date("%Y%m%d_%H%M%S"))
                public.ExecShell("mv -f {} {}".format(self.__DB_FILE, bak_file))
                return []
            if 'client_info' in ex_str:
                # 用户很困扰 这是什么  暂时不记录这个日志 2024-4-7 client_info表一直不存在
                return []

            return []

    def get(self):
        self.__get_columns()
        return self.select()

    def __format_field(self,field):
        import re
        fields = []
        for key in field:
            s_as = re.search(r'\s+as\s+',key,flags=re.IGNORECASE)
            if s_as:
                as_tip = s_as.group()
                key = key.split(as_tip)[1]
            fields.append(key)
        return fields

    def __get_columns(self):
        if self.__OPT_FIELD == '*':
            tmp_cols = self.query('PRAGMA table_info('+self.__DB_TABLE+')',())
            cols = []
            for col in tmp_cols:
                if len(col) > 2: cols.append('`' + col[1] + '`')
            if len(cols) > 0: self.__OPT_FIELD = ','.join(cols)

    def getField(self,keyName):
        #取回指定字段
        try:
            result = self.limit("1").field(keyName).select()
            if len(result) != 0:
                return result[0][keyName]
            return result
        except: return None


    def setField(self,keyName,keyValue):
        #更新指定字段
        return self.save(keyName,(keyValue,))


    def find(self):
        #取一行数据
        try:
            self.ERR_INFO = None
            result = self.limit("1").select()
            if len(result) == 1:
                return result[0]
            return result
        except Exception as ex:
            self.ERR_INFO = str(ex)
            return None

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
        self.write_lock()
        self.clear_files()
        self.__GetConn()
        self.__DB_CONN.text_factory = str
        param = self.en_crypt(keys,param)
        try:
            values=""
            for key in keys.split(','):
                values += "?,"
            values = values[0:len(values)-1]
            sql = "INSERT INTO "+self.__DB_TABLE+"("+keys+") "+"VALUES("+values+")"
            result = self.__DB_CONN.execute(sql,self.__to_tuple(param))
            id = result.lastrowid
            self._close()
            self.__DB_CONN.commit()
            self.rm_lock()
            return id
        except Exception as ex:
            raise public.PanelError("数据库插入出错：" + "error: " + str(ex))
            # return "error: " + str(ex)

    #插入数据
    def insert(self,pdata):
        if not pdata: return False
        keys,param = self.__format_pdata(pdata)
        return self.add(keys,param)

    #更新数据
    def update(self,pdata):
        if not pdata: return False
        keys,param = self.__format_pdata(pdata)
        return self.save(keys,param)

    #构造数据
    def __format_pdata(self,pdata):
        keys = pdata.keys()
        # 对于字段是关键字的时候，需要加反引号， 但是涉及的地方都没有处理，无法预知是否存在问题， 9.6.0处理后需要反复测试
        keys_str = ','.join(["`{}`".format(i) for i in keys])
        param = []
        for k in keys: param.append(pdata[k])
        return keys_str,tuple(param)

    def addAll(self,keys,param):
        #插入数据
        self.write_lock()
        self.clear_files()
        self.__GetConn()
        self.__DB_CONN.text_factory = str
        param = self.en_crypt(keys,param)
        try:
            values=""
            for key in keys.split(','):
                values += "?,"
            values = values[0:len(values)-1]
            sql = "INSERT INTO "+self.__DB_TABLE+"("+keys+") "+"VALUES("+values+")"
            result = self.__DB_CONN.execute(sql,self.__to_tuple(param))
            self.rm_lock()
            return True
        except Exception as ex:
            return "error: " + str(ex)

    def commit(self):
        self._close()
        self.__DB_CONN.commit()

    def _encrypt(self,data):

        # 加密数据
        if not isinstance(data,str): return data
        if not data: return data
        if data.startswith(self.__LAST_KEY): return data
        import PluginLoader
        result = PluginLoader.db_encrypt(data)
        if result['status'] == True:
            return self.__LAST_KEY + result['msg']
        return data

    def _decrypt(self,data):

        # 解密数据
        if not isinstance(data,str): return data
        if not data: return data
        if data.startswith(self.__LAST_KEY):
            import PluginLoader
            res =  PluginLoader.db_decrypt(data[6:])['msg']
            return res
        return data


    def en_crypt(self,keys,param):
        # 加密指定字段
        try:
            if not param or not keys: return param
            if not str(self.__DB_FILE).startswith(os.path.join(public.get_panel_path(), "data")) and not self.__READ_ONLY: return param

            new_param = []
            keys_list = [i.strip("`") for i in keys.split(',')]
            if isinstance(param,str): param = [param]
            for i in range(len(keys_list)):
                key = keys_list[i]
                value = param[i]
                if key in self.__ENCRYPT_KEYS:
                    value = self._encrypt(value)
                new_param.append(value)
            return tuple(new_param)
        except:
            return param

    def de_crypt(self,data):
        # 解密字段
        try:
            if not data: return data
            if not str(self.__DB_FILE).startswith(os.path.join(public.get_panel_path(), "data")) and not self.__READ_ONLY: return data
            if isinstance(data,dict):
                for key in data.keys():
                    if not isinstance(data[key],str): continue
                    if data[key].startswith(self.__LAST_KEY):
                        data[key] = self._decrypt(data[key])
            elif isinstance(data,list):
                for i in range(len(data)):
                    for key in data[i].keys():
                        if not isinstance(data[i][key],str): continue
                        if data[i][key].startswith(self.__LAST_KEY):
                            data[i][key] = self._decrypt(data[i][key])
            elif isinstance(data,str):
                if data.startswith(self.__LAST_KEY):
                    data = self._decrypt(data)
            return data
        except:
            return data

    def is_read_only(self):
        '''
            @name 是否为只读状态
            @return bool
        '''
        if self.__READ_ONLY:
            self.rm_lock()
            self.close()
            raise public.PanelError("数据库保存出错：因磁盘空间不足，当前数据库为只读状态，无法更新数据，请通过文件释放一些磁盘空间后重试!")

    def save(self,keys,param):
        #更新数据
        self.write_lock()
        self.clear_files()
        self.__GetConn()
        self.is_read_only()
        self.__DB_CONN.text_factory = str
        param = self.en_crypt(keys,param)
        try:
            opt = ""
            for key in keys.split(','):
                opt += key + "=?,"
            opt = opt[0:len(opt)-1]
            sql = "UPDATE " + self.__DB_TABLE + " SET " + opt+self.__OPT_WHERE

            #处理拼接WHERE与UPDATE参数
            tmp = list(self.__to_tuple(param))
            for arg in self.__OPT_PARAM:
                tmp.append(arg)
            self.__OPT_PARAM = tuple(tmp)
            result = self.__DB_CONN.execute(sql,self.__OPT_PARAM)
            self._close()
            self.__DB_CONN.commit()
            self.rm_lock()
            return result.rowcount
        except Exception as ex:
            err = str(ex)
            if 'database or disk is full' in err:
                raise public.PanelError("数据库保存出错：磁盘空间不足，请通过[文件管理]释放一些磁盘空间后重试!")
            raise public.PanelError("数据库保存出错：" + "error: " + str(ex))
            # return "error: " + str(ex)

    def delete(self,id=None):
        #删除数据
        self.write_lock()
        self.clear_files()
        self.__GetConn()
        self.is_read_only()
        try:
            if id:
                self.__OPT_WHERE = " WHERE id=?"
                self.__OPT_PARAM = (id,)
            sql = "DELETE FROM " + self.__DB_TABLE + self.__OPT_WHERE
            result = self.__DB_CONN.execute(sql,self.__OPT_PARAM)
            self._close()
            self.__DB_CONN.commit()
            self.rm_lock()
            return result.rowcount
        except Exception as ex:
            return "error: " + str(ex)


    def execute(self,sql,param = ()):
        #执行SQL语句返回受影响行
        self.write_lock()
        self.clear_files()
        self.__GetConn()
        try:
            result = self.__DB_CONN.execute(sql,self.__to_tuple(param))
            self.__DB_CONN.commit()
            self.rm_lock()
            return result.rowcount
        except Exception as ex:
            return "error: " + str(ex)

    def executemany(self, sql, param: list):
        # 执行SQL语句返回受影响行
        self.write_lock()
        self.__GetConn()
        try:
            result = self.__DB_CONN.executemany(sql, param)
            self.__DB_CONN.commit()
            self.rm_lock()
            return result.rowcount
        except Exception as ex:
            return "error: " + str(ex)

    #是否有锁
    def is_lock(self):
        return
        # n = 0
        # while os.path.exists(self.__LOCK):
        #     n+=1
        #     if n > 100:
        #         self.rm_lock()
        #         break
        #     time.sleep(0.01)
    #写锁
    def write_lock(self):
        return
        # self.is_lock()
        # with open(self.__LOCK,'wb+') as f:
        #     f.close()



    #解锁
    def rm_lock(self):
        return
        # if os.path.exists(self.__LOCK):
        #     os.remove(self.__LOCK)


    def clear_files(self):
        """
        @name 清理空间
        """
        import psutil
        path = public.get_panel_path()

        res = psutil.disk_usage(path)
        limit = 512 * 1024
        if res.free > limit:
            return

        #清理安装日志
        log_path = '{}/logs/installed'.format(path)
        if os.path.exists(log_path):
            total = 0
            try:
                flist = []
                for f in os.listdir(log_path):
                    sfile = '{}/{}'.format(log_path, f)
                    if not os.path.isfile(sfile):
                        continue
                    flist.append(sfile)
                flist.sort(key=lambda x: os.path.getmtime(x), reverse=False)

                for f in flist:
                    total += os.path.getsize(f)
                    if total >= limit:
                        os.remove(f)
                        break
                    os.remove(f)
            except:pass
            if total:
                print('共释放：{}'.format(public.to_size(total)))



    def create(self,name):
        #创建数据表
        self.write_lock()
        self.clear_files()
        self.__GetConn()
        script = public.readFile('data/' + name + '.sql')
        result = self.__DB_CONN.executescript(script)
        self.__DB_CONN.commit()
        self.rm_lock()
        return result.rowcount

    def fofile(self,filename):
        #执行脚本
        self.write_lock()
        self.clear_files()
        self.__GetConn()
        script = public.readFile(filename)
        result = self.__DB_CONN.executescript(script)
        self.__DB_CONN.commit()
        self.rm_lock()
        return result.rowcount

    def _close(self):
        #清理条件属性
        self.__OPT_WHERE = ""
        self.__OPT_FIELD = "*"
        self.__OPT_ORDER = ""
        self.__OPT_LIMIT = ""
        self.__OPT_PARAM = ()

    def is_connect(self):
        #检查是否连接数据库
        if not self.__DB_CONN:
            return False
        return True


    def close(self):
        #释放资源
        try:
            self.__DB_CONN.close()
            self.__DB_CONN = None
            self.__clear_memory_user_db()
        except:
            pass

    def batch_add(self, keys: List[str], value_list: List[tuple]):
        # 批量插入数据
        self.clear_files()
        self.__GetConn()
        self.__DB_CONN.text_factory = str
        need_crypt = any(key in keys for key in self.__ENCRYPT_KEYS)
        keys_str = ",".join(["`{}`".format(key) for key in keys])
        for idx, param in enumerate(value_list):
            if len(param) != len(keys):
                raise public.PanelError("数据长度与字段长度不一致")
            if need_crypt:
                value_list[idx] = self.en_crypt(keys_str,param)
        try:
            values_temp=",".join(["?" for _ in range(len(keys))])
            sql = "INSERT INTO " + self.__DB_TABLE + "(" + keys_str + ") " + "VALUES(" + values_temp + ")"
            self.__DB_CONN.executemany(sql, value_list)
            self._close()
            self.__DB_CONN.commit()
            return True
        except Exception as ex:
            raise public.PanelError("数据库插入出错：" + "error: " + str(ex))
            # return "error: " + str(ex)

    def batch_insert(self, data_list:List[dict]):
        keys = list(data_list[0].keys())
        value_list = []
        try:
            for items in data_list:
                if not isinstance(items, dict):
                    raise public.PanelError("数据类型错误")
                value_list.append(tuple(items[key] for key in keys))
        except:
            raise public.PanelError("数据类型错误")
        return self.batch_add(keys, value_list)