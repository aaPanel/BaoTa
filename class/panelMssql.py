#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Windows面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 沐落 <cjx@bt.cn>
# +-------------------------------------------------------------------

import re,os,sys,public

class panelMssql:
    __DB_PASS = None
    __DB_USER = 'sa'
    __DB_PORT = 1433
    __DB_HOST = '127.0.0.1'
    __DB_CONN = None
    __DB_CUR  = None
    __DB_ERR  = None
    __DB_SERVER = 'MSSQLSERVER'

    __DB_CLOUD = 0 #远程数据库
    def __init__(self):
        self.__DB_CLOUD = 0


    def set_host(self,host,port,name,username,password,prefix = ''):
        self.__DB_HOST = host
        self.__DB_PORT = int(port)
        self.__DB_NAME = name
        if self.__DB_NAME: self.__DB_NAME = str(self.__DB_NAME)
        self.__DB_USER = str(username)
        self._USER = str(username)
        self.__DB_PASS = str(password)
        self.__DB_PREFIX = prefix
        self.__DB_CLOUD = 1
        return self

    def __Conn(self):
        """
        连接MSSQL数据库
        """
        try:
            import pymssql
        except :
            os.system("btpip install pymssql==2.1.4")
            import pymssql


        if not self.__DB_CLOUD:
            sa_path = 'data/sa.pl'
            if os.path.exists(sa_path): self.__DB_PASS = public.readFile(sa_path)
            self.__DB_PORT = 1433

        try:

            if self.__DB_CLOUD:
                try:
                    self.__DB_CONN = pymssql.connect(server = self.__DB_HOST, port= str(self.__DB_PORT),user=self.__DB_USER,password=self.__DB_PASS,database = None,login_timeout = 30,timeout = 0,autocommit = True)
                except:
                    self.__DB_ERR = '连接数据库失败!请检查远程数据库信息是否正确'
                    return False
            else:
                self.__DB_CONN = pymssql.connect(server = self.__DB_HOST, port= str(self.__DB_PORT),login_timeout = 30,timeout = 0,autocommit = True)
            self.__DB_CUR = self.__DB_CONN.cursor()  #将数据库连接信息，赋值给cur。
            self.__DB_CUR = self.__DB_CONN.cursor()  #将数据库连接信息，赋值给cur。
            if self.__DB_CUR:
                return True
            else:
                self.__DB_ERR = '连接数据库失败,请检查是否安装SQL Server'
                return False
        except Exception as ex:
            self.__DB_ERR = public.get_error_info()

        return False

    def execute(self,sql):

        #执行SQL语句返回受影响行
        if not self.__Conn(): return self.__DB_ERR
        try:
            result = self.__DB_CUR.execute(sql)

            self.__Close()
            return result;
        except Exception as ex:
            self.__DB_ERR = public.get_error_info()
            return self.__DB_ERR

    def query(self,sql):
        #执行SQL语句返回数据集
        if not self.__Conn(): return self.__DB_ERR
        try:
            self.__DB_CUR.execute(sql)
            result = self.__DB_CUR.fetchall()

            #print(result)
            #将元组转换成列表
            data = list(map(list,result))
            self.__Close()
            return data
        except Exception as ex:
            self.__DB_ERR = public.get_error_info()
            #public.WriteLog('SQL Server查询异常', self.__DB_ERR);
            return str(ex)


    #关闭连接
    def __Close(self):
        self.__DB_CUR.close()
        self.__DB_CONN.close()