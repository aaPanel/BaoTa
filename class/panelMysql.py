#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------

import re,os,sys,public

class panelMysql:
    __DB_PASS = None
    __DB_USER = 'root'
    __DB_PORT = 3306
    __DB_HOST = 'localhost'
    __DB_CONN = None
    __DB_CUR  = None
    __DB_ERR  = None
    __DB_NET = None
    #连接MYSQL数据库
    def __Conn(self):
        if self.__DB_NET: return True
        try:
            socket = '/tmp/mysql.sock'
            try:
                if sys.version_info[0] != 2:
                    try:
                        import pymysql
                    except:
                        public.ExecShell("pip install pymysql")
                        import pymysql
                    pymysql.install_as_MySQLdb()
                import MySQLdb
                if sys.version_info[0] == 2:
                    reload(MySQLdb)
            except:
                try:
                    import pymysql
                    pymysql.install_as_MySQLdb()
                    import MySQLdb
                except Exception as e:
                    self.__DB_ERR = e
                    return False
            try:
                myconf = public.readFile('/etc/my.cnf')
                rep = r"port\s*=\s*([0-9]+)"
                self.__DB_PORT = int(re.search(rep,myconf).groups()[0])
            except:
                self.__DB_PORT = 3306
            self.__DB_PASS = public.M('config').where('id=?',(1,)).getField('mysql_root')
            
            try:
                self.__DB_CONN = MySQLdb.connect(host = self.__DB_HOST,user = self.__DB_USER,passwd = self.__DB_PASS,port = self.__DB_PORT,charset="utf8",connect_timeout=1,unix_socket=socket)
            except MySQLdb.Error as e:
                self.__DB_HOST = '127.0.0.1'
                self.__DB_CONN = MySQLdb.connect(host = self.__DB_HOST,user = self.__DB_USER,passwd = self.__DB_PASS,port = self.__DB_PORT,charset="utf8",connect_timeout=1,unix_socket=socket)
            self.__DB_CUR  = self.__DB_CONN.cursor()
            return True
        except MySQLdb.Error as e:
            self.__DB_ERR = e
            return False

    #连接远程数据库
    def connect_network(self,host,port,username,password):
        self.__DB_NET = True
        try:
            try:
                if sys.version_info[0] != 2:
                    try:
                        import pymysql
                    except:
                        public.ExecShell("pip install pymysql")
                        import pymysql
                    pymysql.install_as_MySQLdb()
                import MySQLdb
                if sys.version_info[0] == 2:
                    reload(MySQLdb)
            except:
                try:
                    import pymysql
                    pymysql.install_as_MySQLdb()
                    import MySQLdb
                except Exception as e:
                    self.__DB_ERR = e
                    return False
            self.__DB_CONN = MySQLdb.connect(host = host,user = username,passwd = password,port = port,charset="utf8",connect_timeout=10)
            self.__DB_CUR  = self.__DB_CONN.cursor()
        except MySQLdb.Error as e:
            self.__DB_ERR = e
            return False


          
    def execute(self,sql):
        #执行SQL语句返回受影响行
        if not self.__Conn(): return self.__DB_ERR
        try:
            result = self.__DB_CUR.execute(sql)
            self.__DB_CONN.commit()
            self.__Close()
            return result
        except Exception as ex:
            return ex
    
    
    def query(self,sql):
        #执行SQL语句返回数据集
        if not self.__Conn(): return self.__DB_ERR
        try:
            self.__DB_CUR.execute(sql)
            result = self.__DB_CUR.fetchall()
            #将元组转换成列表
            if sys.version_info[0] == 2:
                data = map(list,result)
            else:
                data = list(map(list,result))
            self.__Close()
            return data
        except Exception as ex:
            return ex
        
     
    #关闭连接        
    def __Close(self):
        self.__DB_CUR.close()
        self.__DB_CONN.close()