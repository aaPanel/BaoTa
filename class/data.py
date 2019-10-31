#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http:#bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------
import sys
sys.path.append("class/")
import db,public,re
import json

class data:
    __ERROR_COUNT = 0
    '''
     * 设置备注信息
     * @param String _GET['tab'] 数据库表名
     * @param String _GET['id'] 条件ID
     * @return Bool 
    '''
    def setPs(self,get):
        id = get.id;
        if public.M(get.table).where("id=?",(id,)).setField('ps',get.ps):
            return public.returnMsg(True,'EDIT_SUCCESS');    
        return public.returnMsg(False,'EDIT_ERROR');
    
    #端口扫描
    def CheckPort(self,port):
        import socket
        localIP = '127.0.0.1';
        temp = {}
        temp['port'] = port;
        temp['local'] = True;
        try:
            s = socket.socket()
            s.settimeout(0.15)
            s.connect((localIP,port))
            s.close()
        except:
            temp['local'] = False;
        
        result = 0;
        if temp['local']: result +=2;
        return result;
    
    '''
     * 取数据列表
     * @param String _GET['tab'] 数据库表名
     * @param Int _GET['count'] 每页的数据行数
     * @param Int _GET['p'] 分页号  要取第几页数据
     * @return Json  page.分页数 , count.总行数   data.取回的数据
    '''
    def getData(self,get):
        try:
            table = get.table;
            data = self.GetSql(get);
            SQL = public.M(table);
        
            if table == 'backup':
                import os
                for i in range(len(data['data'])):
                    if data['data'][i]['size'] == 0:
                        if os.path.exists(data['data'][i]['filename']): data['data'][i]['size'] = os.path.getsize(data['data'][i]['filename'])
        
            elif table == 'sites' or table == 'databases':
                type = '0'
                if table == 'databases': type = '1'
                for i in range(len(data['data'])):
                    data['data'][i]['backup_count'] = SQL.table('backup').where("pid=? AND type=?",(data['data'][i]['id'],type)).count()
                if table == 'sites':
                    for i in range(len(data['data'])):
                        data['data'][i]['domain'] = SQL.table('domain').where("pid=?",(data['data'][i]['id'],)).count()
            elif table == 'firewall':
                for i in range(len(data['data'])):
                    if data['data'][i]['port'].find(':') != -1 or data['data'][i]['port'].find('.') != -1 or data['data'][i]['port'].find('-') != -1:
                        data['data'][i]['status'] = -1;
                    else:
                        data['data'][i]['status'] = self.CheckPort(int(data['data'][i]['port']));
                
            #返回
            return data;
        except:
            return public.get_error_info();
    
    '''
     * 取数据库行
     * @param String _GET['tab'] 数据库表名
     * @param Int _GET['id'] 索引ID
     * @return Json
    '''
    def getFind(self,get):
        tableName = get.table
        id = get.id
        field = self.GetField(get.table)
        SQL = public.M(tableName);
        where = "id=?";
        find = SQL.where(where,(id,)).field(field).find();
        return find;
    
    
    '''
     * 取字段值
     * @param String _GET['tab'] 数据库表名
     * @param String _GET['key'] 字段
     * @param String _GET['id'] 条件ID
     * @return String 
    '''
    def getKey(self,get):
        tableName = get.table;
        keyName = get.key;
        id = get.id;
        SQL = db.Sql().table(tableName);
        where = "id=?";
        retuls = SQL.where(where,(id,)).getField(keyName);
        return retuls;
    
        
        
    '''
     * 获取数据与分页
     * @param string table 表
     * @param string where 查询条件
     * @param int limit 每页行数
     * @param mixed result 定义分页数据结构
     * @return array
    '''
    def GetSql(self,get,result = '1,2,3,4,5,8'):
        #判断前端是否传入参数
        order = "id desc"
        if hasattr(get,'order'): 
            order = get.order
            
        limit = 20
        if hasattr(get,'limit'): 
            limit = int(get.limit)
        
        if hasattr(get,'result'): 
            result = get.result;
            
        SQL = db.Sql();
        data = {}
        #取查询条件
        where = ''
        if hasattr(get,'search'):
            if sys.version_info[0] == 2: get.search = get.search.encode('utf-8')
            where = self.GetWhere(get.table,get.search);
            if get.table == 'backup':
                where += " and type='" + get.type+"'";
            
            if get.table == 'sites' and get.search:
                pid = SQL.table('domain').where("name LIKE '%"+get.search+"%'",()).getField('pid');
                if pid: where = "id=" + str(pid);

        if get.table == 'sites' and hasattr(get,'type'):
            if get.type != '-1':
                type_where = "type_id=%s" % get.type
                if where == '': 
                    where = type_where
                else:
                    where += " and " + type_where
        
        field = self.GetField(get.table)
        #实例化数据库对象
        
        
        #是否直接返回所有列表
        if hasattr(get,'list'):
            data = SQL.table(get.table).where(where,()).field(field).order(order).select()
            return data
        
        #取总行数
        count = SQL.table(get.table).where(where,()).count();
        #get.uri = get
        #包含分页类
        import page
        #实例化分页类
        page = page.Page();
        
        info = {}
        info['count'] = count
        info['row']   = limit
        
        info['p'] = 1
        if hasattr(get,'p'):
            info['p']     = int(get['p'])
        info['uri']   = get
        info['return_js'] = ''
        if hasattr(get,'tojs'):
            info['return_js']   = get.tojs
        
        data['where'] = where;
        
        #获取分页数据
        data['page'] = page.GetPage(info,result)
        #取出数据
        data['data'] = SQL.table(get.table).where(where,()).order(order).field(field).limit(str(page.SHIFT)+','+str(page.ROW)).select()
        return data;
    
    #获取条件
    def GetWhere(self,tableName,search): 
        if not search: return ""

        if type(search) == bytes: search = search.encode('utf-8').strip()
        search = re.search(u"[\w\x80-\xff]+",search).group();
        wheres = {
            'sites'     :   "id='"+search+"' or name like '%"+search+"%' or status like '%"+search+"%' or ps like '%"+search+"%'",
            'ftps'      :   "id='"+search+"' or name like '%"+search+"%' or ps like '%"+search+"%'",
            'databases' :   "id='"+search+"' or name like '%"+search+"%' or ps like '%"+search+"%'",
            'logs'      :   "type like '%"+search+"%' or log like '%"+search+"%' or addtime like '%"+search+"%'",
            'backup'    :   "pid="+search+"",
            'users'     :   "id='"+search+"' or username='"+search+"'",
            'domain'    :   "pid='"+search+"' or name='"+search+"'",
            'tasks'     :   "status='"+search+"' or type='"+search+"'"
            }
        try:
            return wheres[tableName]
        except:
            return ''
        
    def GetField(self,tableName):
        fields = {
            'sites'     :   "id,name,path,status,ps,addtime,edate",
            'ftps'      :   "id,pid,name,password,status,ps,addtime,path",
            'databases' :   "id,pid,name,username,password,accept,ps,addtime",
            'logs'      :   "id,type,log,addtime",
            'backup'    :   "id,pid,name,filename,addtime,size",
            'users'     :   "id,username,phone,email,login_ip,login_time",
            'firewall'  :   "id,port,ps,addtime",
            'domain'    :   "id,pid,name,port,addtime",
            'tasks'     :   "id,name,type,status,addtime,start,end"
            }
        try:
            return fields[tableName]
        except:
            return ''
        
    
    
