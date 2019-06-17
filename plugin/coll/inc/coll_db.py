#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------


#+--------------------------------------------------------------------
#|   微架构 - 数据库对象
#+--------------------------------------------------------------------
import os,sys
os.chdir('/www/server/panel')
sys.path.insert(0,'class/')
from db import Sql

class coll_db(Sql):
    __plugin_path = '/www/server/panel/plugin/coll'
    __conn_err = None
    def __init__(self):
        self.dbfile()

    #设置数据库文件路径
    def dbfile(self):
        db_file = self.__plugin_path + '/data.db'
        if os.path.exists(db_file):
            self._Sql__DB_FILE = db_file
        else:
            self.__conn_err = 'ERROR: Database file does not exist, ' + db_file

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
        keys_str = ','.join(keys)
        param = []
        for k in keys: param.append(pdata[k])
        return keys_str,tuple(param)

    #连接到数据库
    def conn(self,table):
        if self.__conn_err: 
            print(self.__conn_err)
            return self.__conn_err
        return self.table(table)

def M(table):
    d = coll_db()
    return d.conn(table)

#写日志 
def write_log(type,log):
    from BTPanel import session,time
    pdata = {}
    #如果没有登录
    if not 'coll_uid' in session:
        pdata['uid'] = 0
        pdata['username'] = 'system'
    else:
        pdata['uid'] = session['coll_uid']
        pdata['username'] = session['coll_username']

    pdata['type'] = type
    pdata['log'] = log
    pdata['addtime'] = int(time.time())
    M('logs').insert(pdata)
    return True