#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http:#bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------
import sys,os,re,time
if not 'class/' in sys.path:
    sys.path.insert(0,'class/')
import db,public,panelMysql
import json

class data:
    __ERROR_COUNT = 0
    DB_MySQL = None
    web_server = None
    setupPath = '/www/server'
    '''
     * 设置备注信息
     * @param String _GET['tab'] 数据库表名
     * @param String _GET['id'] 条件ID
     * @return Bool 
    '''
    def setPs(self,get):
        id = get.id
        if public.M(get.table).where("id=?",(id,)).setField('ps',get.ps):
            return public.returnMsg(True,'EDIT_SUCCESS');    
        return public.returnMsg(False,'EDIT_ERROR')
    
    #端口扫描
    def CheckPort(self,port):
        import socket
        localIP = '127.0.0.1'
        temp = {}
        temp['port'] = port
        temp['local'] = True
        try:
            s = socket.socket()
            s.settimeout(0.15)
            s.connect((localIP,port))
            s.close()
        except:
            temp['local'] = False
        
        result = 0
        if temp['local']: result +=2
        return result
    
    # 转换时间
    def strf_date(self, sdate):
        return time.strftime('%Y-%m-%d', time.strptime(sdate, '%Y%m%d%H%M%S'))

    def get_cert_end(self,pem_file):
        try:
            import OpenSSL
            result = {}
            x509 = OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM, public.readFile(pem_file))
            # 取产品名称
            issuer = x509.get_issuer()
            result['issuer'] = ''
            if hasattr(issuer, 'CN'):
                result['issuer'] = issuer.CN
            if not result['issuer']:
                is_key = [b'0', '0']
                issue_comp = issuer.get_components()
                if len(issue_comp) == 1:
                    is_key = [b'CN', 'CN']
                for iss in issue_comp:
                    if iss[0] in is_key:
                        result['issuer'] = iss[1].decode()
                        break
            # 取到期时间
            result['notAfter'] = self.strf_date(
                bytes.decode(x509.get_notAfter())[:-1])
            # 取申请时间
            result['notBefore'] = self.strf_date(
                bytes.decode(x509.get_notBefore())[:-1])
            # 取可选名称
            result['dns'] = []
            for i in range(x509.get_extension_count()):
                s_name = x509.get_extension(i)
                if s_name.get_short_name() in [b'subjectAltName', 'subjectAltName']:
                    s_dns = str(s_name).split(',')
                    for d in s_dns:
                        result['dns'].append(d.split(':')[1])
            subject = x509.get_subject().get_components()
            # 取主要认证名称
            if len(subject) == 1:
                result['subject'] = subject[0][1].decode()
            else:
                result['subject'] = result['dns'][0]
            return result
        except:
            return public.get_cert_data(pem_file)


    def get_site_ssl_info(self,siteName):
        try:
            s_file = 'vhost/nginx/{}.conf'.format(siteName)
            is_apache = False
            if not os.path.exists(s_file):
                s_file = 'vhost/apache/{}.conf'.format(siteName)
                is_apache = True

            if not os.path.exists(s_file):
                return -1
            
            s_conf = public.readFile(s_file)
            if not s_conf: return -1
            ssl_file = None
            if is_apache:
                if s_conf.find('SSLCertificateFile') == -1:
                    return -1
                s_tmp = re.findall(r"SSLCertificateFile\s+(.+\.pem)",s_conf)
                if not s_tmp: return -1
                ssl_file = s_tmp[0]
            else:
                if s_conf.find('ssl_certificate') == -1:
                    return -1
                s_tmp = re.findall(r"ssl_certificate\s+(.+\.pem);",s_conf)
                if not s_tmp: return -1
                ssl_file = s_tmp[0]
            ssl_info = self.get_cert_end(ssl_file)
            if not ssl_info: return -1
            ssl_info['endtime'] = int(int(time.mktime(time.strptime(ssl_info['notAfter'], "%Y-%m-%d")) - time.time()) / 86400)
            return ssl_info
        except: return -1
        #return "{}:{}".format(ssl_info['issuer'],ssl_info['notAfter'])
        

    def get_php_version(self,siteName):
        try:
            
            if not self.web_server:
                self.web_server = public.get_webserver()

            conf = public.readFile(self.setupPath + '/panel/vhost/'+self.web_server+'/'+siteName+'.conf')
            if self.web_server == 'openlitespeed':
                conf = public.readFile(
                    self.setupPath + '/panel/vhost/' + self.web_server + '/detail/' + siteName + '.conf')
            if self.web_server == 'nginx':
                rep = r"enable-php-([0-9]{2,3})\.conf"
            elif self.web_server == 'apache':
                rep = r"php-cgi-([0-9]{2,3})\.sock"
            else:
                rep = r"path\s*/usr/local/lsws/lsphp(\d+)/bin/lsphp"
            tmp = re.search(rep,conf).groups()
            if tmp[0] == '00':
                return '静态'
            
            return tmp[0][0] + '.' + tmp[0][1]
        except:
            return '静态'

    def map_to_list(self,map_obj):
        try:
            if type(map_obj) != list and type(map_obj) != str: map_obj = list(map_obj)
            return map_obj
        except: return []

    def get_database_size(self,databaseName):
        try:
            if not self.DB_MySQL:self.DB_MySQL = panelMysql.panelMysql()
            db_size = self.map_to_list(self.DB_MySQL.query("select sum(DATA_LENGTH)+sum(INDEX_LENGTH) from information_schema.tables  where table_schema='{}'".format(databaseName)))[0][0]
            if not db_size: return 0
            return int(db_size)
        except:
            return 0
        
    
    '''
     * 取数据列表
     * @param String _GET['tab'] 数据库表名
     * @param Int _GET['count'] 每页的数据行数
     * @param Int _GET['p'] 分页号  要取第几页数据
     * @return Json  page.分页数 , count.总行数   data.取回的数据
    '''
    def getData(self,get):
        try:
            table = get.table
            data = self.GetSql(get)
            SQL = public.M(table)
        
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
                        data['data'][i]['ssl'] = self.get_site_ssl_info(data['data'][i]['name'])
                        data['data'][i]['php_version'] = self.get_php_version(data['data'][i]['name'])
            elif table == 'firewall':
                for i in range(len(data['data'])):
                    if data['data'][i]['port'].find(':') != -1 or data['data'][i]['port'].find('.') != -1 or data['data'][i]['port'].find('-') != -1:
                        data['data'][i]['status'] = -1
                    else:
                        data['data'][i]['status'] = self.CheckPort(int(data['data'][i]['port']))
                
            #返回
            return data
        except:
            return public.get_error_info()
    
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
        SQL = public.M(tableName)
        where = "id=?"
        find = SQL.where(where,(id,)).field(field).find()
        return find
    
    
    '''
     * 取字段值
     * @param String _GET['tab'] 数据库表名
     * @param String _GET['key'] 字段
     * @param String _GET['id'] 条件ID
     * @return String 
    '''
    def getKey(self,get):
        tableName = get.table
        keyName = get.key
        id = get.id
        SQL = db.Sql().table(tableName)
        where = "id=?"
        retuls = SQL.where(where,(id,)).getField(keyName)
        return retuls
        
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
            result = get.result
            
        SQL = db.Sql()
        data = {}
        #取查询条件
        where = ''
        if hasattr(get,'search'):
            if sys.version_info[0] == 2: get.search = get.search.encode('utf-8')
            where = self.GetWhere(get.table,get.search)
            if get.table == 'backup':
                where += " and type='" + get.type+"'"
            
            if get.table == 'sites' and get.search:
                pid = SQL.table('domain').where("name LIKE '%"+get.search+"%'",()).getField('pid')
                if pid: 
                    if where: 
                        where += " or id=" + str(pid)
                    else:
                        where += "id=" + str(pid)

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
        count = SQL.table(get.table).where(where,()).count()
        #get.uri = get
        #包含分页类
        import page
        #实例化分页类
        page = page.Page()
        
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
        
        data['where'] = where
        
        #获取分页数据
        data['page'] = page.GetPage(info,result)
        #取出数据
        data['data'] = SQL.table(get.table).where(where,()).order(order).field(field).limit(str(page.SHIFT)+','+str(page.ROW)).select()
        return data
    
    #获取条件
    def GetWhere(self,tableName,search): 
        if not search: return ""

        if type(search) == bytes: search = search.encode('utf-8').strip()
        try:
            search = re.search(r"[\w\x80-\xff\.]+",search).group()
        except:
            return ''
        wheres = {
            'sites'     :   "id='"+search+"' or name like '%"+search+"%' or status like '%"+search+"%' or ps like '%"+search+"%'",
            'ftps'      :   "id='"+search+"' or name like '%"+search+"%' or ps like '%"+search+"%'",
            'databases' :   "id='"+search+"' or name like '%"+search+"%' or ps like '%"+search+"%'",
            'logs'      :   "uid='"+search+"' or username='"+search+"' or type like '%"+search+"%' or log like '%"+search+"%' or addtime like '%"+search+"%'",
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
            'logs'      :   "id,uid,username,type,log,addtime",
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
        
    
    
