#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2017 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: 黄文良 <287962566@qq.com>
#-------------------------------------------------------------------

#------------------------------
# 数据库管理类
#------------------------------
import public,db,re,time,os,sys,panelMysql
from BTPanel import session
import datatool
class database(datatool.datatools):
    
    #添加数据库
    def AddDatabase(self,get):
        try:
            data_name = get['name'].strip()
            if self.CheckRecycleBin(data_name): return public.returnMsg(False,'数据库['+data_name+']已在回收站，请从回收站恢复!');
            if len(data_name) > 16: return public.returnMsg(False, 'DATABASE_NAME_LEN')
            reg = "^[\w\.-]+$"
            if not re.match(reg, data_name): return public.returnMsg(False,'DATABASE_NAME_ERR_T')
            if not hasattr(get,'db_user'): get.db_user = data_name;
            username = get.db_user.strip();
            checks = ['root','mysql','test','sys','panel_logs']
            if username in checks or len(username) < 1: return public.returnMsg(False,'数据库用户名不合法!');
            if data_name in checks or len(data_name) < 1: return public.returnMsg(False,'数据库名称不合法!');
            data_pwd = get['password']
            if len(data_pwd)<1:
                data_pwd = public.md5(time.time())[0:8]
            
            sql = public.M('databases')
            if sql.where("name=? or username=?",(data_name,username)).count(): return public.returnMsg(False,'DATABASE_NAME_EXISTS')
            address = get['address'].strip()
            user = '是'
            password = data_pwd
            
            codeing = get['codeing']
            
            wheres={
                    'utf8'      :   'utf8_general_ci',
                    'utf8mb4'   :   'utf8mb4_general_ci',
                    'gbk'       :   'gbk_chinese_ci',
                    'big5'      :   'big5_chinese_ci'
                    }
            codeStr=wheres[codeing]
            #添加MYSQL
            mysql_obj = panelMysql.panelMysql()
            result = mysql_obj.execute("create database `" + data_name + "` DEFAULT CHARACTER SET " + codeing + " COLLATE " + codeStr)
            isError = self.IsSqlError(result)
            if  isError != None: return isError
            mysql_obj.execute("drop user '" + username + "'@'localhost'")
            for a in address.split(','):
                mysql_obj.execute("drop user '" + username + "'@'" + a + "'")

            self.__CreateUsers(data_name,username,password,address)
            
            if get['ps'] == '': get['ps']=public.getMsg('INPUT_PS');
            addTime = time.strftime('%Y-%m-%d %X',time.localtime())
            
            pid = 0
            if hasattr(get,'pid'): pid = get.pid
            #添加入SQLITE
            sql.add('pid,name,username,password,accept,ps,addtime',(pid,data_name,username,password,address,get['ps'],addTime))
            public.WriteLog("TYPE_DATABASE", 'DATABASE_ADD_SUCCESS',(data_name,))
            return public.returnMsg(True,'ADD_SUCCESS')
        except Exception as ex:
            public.WriteLog("TYPE_DATABASE",'DATABASE_ADD_ERR', (data_name,str(ex)))
            return public.returnMsg(False,'ADD_ERROR')


    #创建用户
    def __CreateUsers(self,dbname,username,password,address):
        mysql_obj = panelMysql.panelMysql()
        mysql_obj.execute("CREATE USER `%s`@`localhost` IDENTIFIED BY '%s'" % (username,password))
        mysql_obj.execute("grant all privileges on %s.* to `%s`@`localhost`" % (dbname,username))
        for a in address.split(','):
            mysql_obj.execute("CREATE USER `%s`@`%s` IDENTIFIED BY '%s'" % (username,a,password))
            mysql_obj.execute("grant all privileges on %s.* to `%s`@`%s`" % (dbname,username,a))
        mysql_obj.execute("flush privileges")
        
    #检查是否在回收站
    def CheckRecycleBin(self,name):
        try:
            for n in os.listdir('/www/Recycle_bin'):
                if n.find('BTDB_'+name+'_t_') != -1: return True;
            return False;
        except:
            return False;
    
    #检测数据库执行错误
    def IsSqlError(self,mysqlMsg):
        mysqlMsg=str(mysqlMsg)
        if "MySQLdb" in mysqlMsg: return public.returnMsg(False,'DATABASE_ERR_MYSQLDB')
        if "2002," in mysqlMsg or '2003,' in mysqlMsg: return public.returnMsg(False,'DATABASE_ERR_CONNECT')
        if "using password:" in mysqlMsg: return public.returnMsg(False,'DATABASE_ERR_PASS')
        if "Connection refused" in mysqlMsg: return public.returnMsg(False,'DATABASE_ERR_CONNECT')
        if "1133" in mysqlMsg: return public.returnMsg(False,'DATABASE_ERR_NOT_EXISTS')
        return None
    
    #删除数据库
    def DeleteDatabase(self,get):
        try:
            id=get['id']
            name = get['name']
            if os.path.exists('data/recycle_bin_db.pl'): return self.DeleteToRecycleBin(name);
            
            find = public.M('databases').where("id=?",(id,)).field('id,pid,name,username,password,accept,ps,addtime').find();
            accept = find['accept'];
            username = find['username'];
            #删除MYSQL
            result = panelMysql.panelMysql().execute("drop database `" + name + "`")
            isError=self.IsSqlError(result)
            if  isError != None: return isError
            users = panelMysql.panelMysql().query("select Host from mysql.user where User='" + username + "' AND Host!='localhost'")
            panelMysql.panelMysql().execute("drop user '" + username + "'@'localhost'")
            for us in users:
                panelMysql.panelMysql().execute("drop user '" + username + "'@'" + us[0] + "'")
            panelMysql.panelMysql().execute("flush privileges")
            #删除SQLITE
            public.M('databases').where("id=?",(id,)).delete()
            public.WriteLog("TYPE_DATABASE", 'DATABASE_DEL_SUCCESS',(name,))
            return public.returnMsg(True, 'DEL_SUCCESS')
        except Exception as ex:
            public.WriteLog("TYPE_DATABASE",'DATABASE_DEL_ERR',(get.name , str(ex)))
            return public.returnMsg(False,'DEL_ERROR')
    
    #删除数据库到回收站  
    def DeleteToRecycleBin(self,name):
        import json
        data = public.M('databases').where("name=?",(name,)).field('id,pid,name,username,password,accept,ps,addtime').find();
        username = data['username'];
        panelMysql.panelMysql().execute("drop user '" + username + "'@'localhost'");
        users = panelMysql.panelMysql().query("select Host from mysql.user where User='" + username + "' AND Host!='localhost'")
        for us in users:
            panelMysql.panelMysql().execute("drop user '" + username + "'@'" + us[0] + "'")
        panelMysql.panelMysql().execute("flush privileges");
        rPath = '/www/Recycle_bin/';
        public.writeFile(rPath + 'BTDB_' + name +'_t_' + str(time.time()),json.dumps(data));
        public.M('databases').where("name=?",(name,)).delete();
        public.WriteLog("TYPE_DATABASE", 'DATABASE_DEL_SUCCESS',(name,));
        return public.returnMsg(True,'RECYCLE_BIN_DB');
    
    #永久删除数据库
    def DeleteTo(self,filename):
        import json
        data = json.loads(public.readFile(filename))
        if public.M('databases').where("name=?",( data['name'],)).count():
            os.remove(filename);
            return public.returnMsg(True,'DEL_SUCCESS');
        result = panelMysql.panelMysql().execute("drop database `" + data['name'] + "`")
        isError=self.IsSqlError(result)
        if  isError != None: return isError
        panelMysql.panelMysql().execute("drop user '" + data['username'] + "'@'localhost'")
        users = panelMysql.panelMysql().query("select Host from mysql.user where User='" + data['username'] + "' AND Host!='localhost'")
        for us in users:
            panelMysql.panelMysql().execute("drop user '" + data['username'] + "'@'" + us[0] + "'")
        panelMysql.panelMysql().execute("flush privileges")
        os.remove(filename);
        public.WriteLog("TYPE_DATABASE", 'DATABASE_DEL_SUCCESS',(data['name'],))
        return public.returnMsg(True,'DEL_SUCCESS');
    
    #恢复数据库
    def RecycleDB(self,filename):
        import json
        data = json.loads(public.readFile(filename))
        if public.M('databases').where("name=?",( data['name'],)).count():
            os.remove(filename);
            return public.returnMsg(True,'RECYCLEDB');

        self.__CreateUsers(data['name'],data['username'],data['password'],data['accept'])
        #result = panelMysql.panelMysql().execute("grant all privileges on `" + data['name'] + "`.* to '" + data['username'] + "'@'localhost' identified by '" + data['password'] + "'")
        #isError=self.IsSqlError(result)
        #if isError != None: return isError
        #panelMysql.panelMysql().execute("grant all privileges on `" + data['name'] + "`.* to '" + data['username'] + "'@'" + data['accept'] + "' identified by '" + data['password'] + "'")
        #panelMysql.panelMysql().execute("flush privileges")
        
        public.M('databases').add('id,pid,name,username,password,accept,ps,addtime',(data['id'],data['pid'],data['name'],data['username'],data['password'],data['accept'],data['ps'],data['addtime']))
        os.remove(filename);
        return public.returnMsg(True,"RECYCLEDB");
    
    #设置ROOT密码
    def SetupPassword(self,get):
        password = get['password'].strip()
        try:
            rep = "^[\w@\.]+$"
            if not re.match(rep, password): return public.returnMsg(False, 'DATABASE_NAME_ERR_T')
            mysql_root = public.M('config').where("id=?",(1,)).getField('mysql_root')
            #修改MYSQL
            mysql_obj = panelMysql.panelMysql()
            result = mysql_obj.query("show databases")
            isError=self.IsSqlError(result)
            is_modify = True
            if  isError != None: 
                #尝试使用新密码
                public.M('config').where("id=?",(1,)).setField('mysql_root',password)
                result = mysql_obj.query("show databases")
                isError=self.IsSqlError(result)
                if  isError != None: 
                    os.system("cd /www/server/panel && python tools.py root \"" + password + "\"")
                    is_modify = False
            if is_modify:
                m_version = public.readFile(public.GetConfigValue('setup_path') + '/mysql/version.pl')
                
                if m_version.find('5.7') == 0  or m_version.find('8.0') == 0:
                    panelMysql.panelMysql().execute("UPDATE mysql.user SET authentication_string='' WHERE user='root'")
                    panelMysql.panelMysql().execute("ALTER USER 'root'@'localhost' IDENTIFIED BY '%s'" % password)
                    panelMysql.panelMysql().execute("ALTER USER 'root'@'127.0.0.1' IDENTIFIED BY '%s'" % password)
                else:
                    result = mysql_obj.execute("update mysql.user set Password=password('" + password + "') where User='root'")
                mysql_obj.execute("flush privileges")

            msg = public.getMsg('DATABASE_ROOT_SUCCESS');
            #修改SQLITE
            public.M('config').where("id=?",(1,)).setField('mysql_root',password)  
            public.WriteLog("TYPE_DATABASE", "DATABASE_ROOT_SUCCESS")
            session['config']['mysql_root']=password
            return public.returnMsg(True,msg)
        except Exception as ex:
            return public.returnMsg(False,'EDIT_ERROR' + str(ex));
    
    #修改用户密码
    def ResDatabasePassword(self,get):
        try:
            newpassword = get['password']
            username = get['name']
            id = get['id']
            name = public.M('databases').where('id=?',(id,)).getField('name');
            
            rep = "^[\w@\.]+$"
            if len(re.search(rep, newpassword).groups()) > 0: return public.returnMsg(False, 'DATABASE_NAME_ERR_T')
            
            #修改MYSQL
            mysql_obj = panelMysql.panelMysql()
            m_version = public.readFile(public.GetConfigValue('setup_path') + '/mysql/version.pl')
            if m_version.find('5.7') == 0  or m_version.find('8.0') == 0:
                accept = self.map_to_list(panelMysql.panelMysql().query("select Host from mysql.user where User='" + name + "' AND Host!='localhost'"));
                mysql_obj.execute("update mysql.user set authentication_string='' where User='" + username + "'")
                result = mysql_obj.execute("ALTER USER `%s`@`localhost` IDENTIFIED BY '%s'" % (username,newpassword))
                for my_host in accept:
                    mysql_obj.execute("ALTER USER `%s`@`%s` IDENTIFIED BY '%s'" % (username,my_host[0],newpassword))
            else:
                result = mysql_obj.execute("update mysql.user set Password=password('" + newpassword + "') where User='" + username + "'")
            
            isError=self.IsSqlError(result)
            if  isError != None: return isError

            mysql_obj.execute("flush privileges")
            #if result==False: return public.returnMsg(False,'DATABASE_PASS_ERR_NOT_EXISTS')
            #修改SQLITE
            if int(id) > 0:
                public.M('databases').where("id=?",(id,)).setField('password',newpassword)
            else:
                public.M('config').where("id=?",(id,)).setField('mysql_root',newpassword)
                session['config']['mysql_root'] = newpassword
            
            public.WriteLog("TYPE_DATABASE",'DATABASE_PASS_SUCCESS',(name,))
            return public.returnMsg(True,'DATABASE_PASS_SUCCESS',(name,))
        except Exception as ex:
            import traceback
            public.WriteLog("TYPE_DATABASE", 'DATABASE_PASS_ERROR',(name,traceback.format_exc(limit=True).replace('\n','<br>')))
            return public.returnMsg(False,'DATABASE_PASS_ERROR',(name,))    
    
    #备份
    def ToBackup(self,get):
        #try:
        result = panelMysql.panelMysql().execute("show databases")
        isError=self.IsSqlError(result)
        if isError: return isError
        id = get['id']
        name = public.M('databases').where("id=?",(id,)).getField('name')
        root = public.M('config').where('id=?',(1,)).getField('mysql_root');
        if not os.path.exists(session['config']['backup_path'] + '/database'): os.system('mkdir -p ' + session['config']['backup_path'] + '/database');
        self.mypass(True, root);
        
        fileName = name + '_' + time.strftime('%Y%m%d_%H%M%S',time.localtime()) + '.sql.gz'
        backupName = session['config']['backup_path'] + '/database/' + fileName
        public.ExecShell("/www/server/mysql/bin/mysqldump --force --opt \"" + name + "\" | gzip > " + backupName)
        if not os.path.exists(backupName): return public.returnMsg(False,'BACKUP_ERROR');
        
        self.mypass(False, root);
        
        sql = public.M('backup')
        addTime = time.strftime('%Y-%m-%d %X',time.localtime())
        sql.add('type,name,pid,filename,size,addtime',(1,fileName,id,backupName,0,addTime))
        public.WriteLog("TYPE_DATABASE", "DATABASE_BACKUP_SUCCESS",(name,))
        return public.returnMsg(True, 'BACKUP_SUCCESS')
        #except Exception as ex:
            #public.WriteLog("数据库管理", "备份数据库[" + name + "]失败 => "  +  str(ex))
            #return public.returnMsg(False,'备份失败!')
    
    #删除备份文件
    def DelBackup(self,get):
        try:
            id = get.id
            where = "id=?"
            filename = public.M('backup').where(where,(id,)).getField('filename')
            if os.path.exists(filename): os.remove(filename)
            name=''
            if filename == 'qiniu':
                name = public.M('backup').where(where,(id,)).getField('name');
                public.ExecShell("python "+public.GetConfigValue('setup_path') + '/panel/script/backup_qiniu.py delete_file ' + name)
            
            public.M('backup').where(where,(id,)).delete()
            public.WriteLog("TYPE_DATABASE", 'DATABASE_BACKUP_DEL_SUCCESS',(name,filename))
            return public.returnMsg(True, 'DEL_SUCCESS');
        except Exception as ex:
            public.WriteLog("TYPE_DATABASE", 'DATABASE_BACKUP_DEL_ERR',(name,filename,str(ex)))
            return public.returnMsg(False,'DEL_ERROR')
    
    #导入
    def InputSql(self,get):
        #try:
        result = panelMysql.panelMysql().execute("show databases")
        isError=self.IsSqlError(result)
        if isError: return isError
        name = get['name']
        file = get['file']
        root = public.M('config').where('id=?',(1,)).getField('mysql_root');
        tmp = file.split('.')
        exts = ['sql','gz','zip']
        ext = tmp[len(tmp) -1]
        if ext not in exts:
            return public.returnMsg(False, 'DATABASE_INPUT_ERR_FORMAT')
            
        isgzip = False
        if ext != 'sql':
            tmp = file.split('/')
            tmpFile = tmp[len(tmp)-1]
            tmpFile = tmpFile.replace('.sql.' + ext, '.sql')
            tmpFile = tmpFile.replace('.' + ext, '.sql')
            tmpFile = tmpFile.replace('tar.', '')
            backupPath = session['config']['backup_path'] + '/database'
                
            if ext == 'zip':
                public.ExecShell("cd "  +  backupPath  +  " && unzip " +  file)
            else:
                public.ExecShell("cd "  +  backupPath  +  " && tar zxf " +  file)
                if not os.path.exists(backupPath  +  "/"  +  tmpFile): 
                    public.ExecShell("cd "  +  backupPath  +  " && gunzip -q " +  file)
                    isgizp = True
                 
            if not os.path.exists(backupPath + '/' + tmpFile) or tmpFile == '': return public.returnMsg(False, 'FILE_NOT_EXISTS',(tmpFile,))
            self.mypass(True, root);
            public.ExecShell(public.GetConfigValue('setup_path') + "/mysql/bin/mysql -uroot -p" + root + " --force \"" + name + "\" < " + backupPath + '/' +tmpFile)
            self.mypass(False, root);
            if isgizp:
                os.system('cd ' +backupPath+ ' && gzip ' + file.split('/')[-1][:-3]);
            else:
                os.system("rm -f " +  backupPath + '/' +tmpFile)
        else:
            self.mypass(True, root);
            public.ExecShell(public.GetConfigValue('setup_path') + "/mysql/bin/mysql -uroot -p" + root + " --force \"" + name + "\" < " +  file)
            self.mypass(False, root);
                
            
        public.WriteLog("TYPE_DATABASE", 'DATABASE_INPUT_SUCCESS',(name,))
        return public.returnMsg(True, 'DATABASE_INPUT_SUCCESS');
        #except Exception as ex:
            #public.WriteLog("TYPE_DATABASE", 'DATABASE_INPUT_ERR',(name,str(ex)))
            #return public.returnMsg(False,'DATABASE_INPUT_ERR')
    
    #同步数据库到服务器
    def SyncToDatabases(self,get):
        result = panelMysql.panelMysql().execute("show databases")
        isError=self.IsSqlError(result)
        if isError: return isError
        type = int(get['type'])
        n = 0
        sql = public.M('databases')
        if type == 0:
            data = sql.field('id,name,username,password,accept').select()
            for value in data:
                result = self.ToDataBase(value)
                if result == 1: n +=1
        else:
            import json
            data = json.loads(get.ids)
            for value in data:
                find = sql.where("id=?",(value,)).field('id,name,username,password,accept').find()   
                result = self.ToDataBase(find)
                if result == 1: n +=1
        
        return public.returnMsg(True,'DATABASE_SYNC_SUCCESS',(str(n),))
    
    #配置
    def mypass(self,act,root):
        os.system("sed -i '/user=root/d' /etc/my.cnf")
        os.system("sed -i '/password=/d' /etc/my.cnf")
        if act:
            mycnf = public.readFile('/etc/my.cnf');
            rep = "\[mysqldump\]\nuser=root"
            sea = "[mysqldump]\n"
            subStr = sea + "user=root\npassword=\"" + root + "\"\n";
            mycnf = mycnf.replace(sea,subStr)
            if len(mycnf) > 100: public.writeFile('/etc/my.cnf',mycnf);
    
    #添加到服务器
    def ToDataBase(self,find):
        #if find['username'] == 'bt_default': return 0
        if len(find['password']) < 3 :
            find['username'] = find['name']
            find['password'] = public.md5(str(time.time()) + find['name'])[0:10]
            public.M('databases').where("id=?",(find['id'],)).save('password,username',(find['password'],find['username']))
        
        result = panelMysql.panelMysql().execute("create database `" + find['name'] + "`")
        if "using password:" in str(result): return -1
        if "Connection refused" in str(result): return -1
       
        password = find['password']
        #if find['password']!="" and len(find['password']) > 20:
            #password = find['password']
        
        self.__CreateUsers(find['name'],find['username'],password,find['accept'])
        #panelMysql.panelMysql().execute("drop user '" + find['username'] + "'@'localhost'")
        #panelMysql.panelMysql().execute("drop user '" + find['username'] + "'@'" + find['accept'] + "'")
        #panelMysql.panelMysql().execute("grant all privileges on " + find['name'] + ".* to '" + find['username'] + "'@'localhost' identified by '" + password + "'")
        #panelMysql.panelMysql().execute("grant all privileges on " + find['name'] + ".* to '" + find['username'] + "'@'" + find['accept'] + "' identified by '" + password + "'")
        #panelMysql.panelMysql().execute("flush privileges")
        return 1
    
    
    #从服务器获取数据库
    def SyncGetDatabases(self,get):
        data = panelMysql.panelMysql().query("show databases")
        isError = self.IsSqlError(data)
        if isError != None: return isError
        users = panelMysql.panelMysql().query("select User,Host from mysql.user where User!='root' AND Host!='localhost' AND Host!=''")
        if type(users) == str: return public.returnMsg(False,users)
        sql = public.M('databases')
        nameArr = ['information_schema','performance_schema','mysql','sys']
        n = 0
        for  value in data:
            b = False
            for key in nameArr:
                if value[0] == key:
                    b = True 
                    break
            if b:continue
            if sql.where("name=?",(value[0],)).count(): continue
            host = '127.0.0.1'
            for user in users:
                if value[0] == user[0]:
                    host = user[1]
                    break
                
            ps = public.getMsg('INPUT_PS')
            if value[0] == 'test':
                    ps = public.getMsg('DATABASE_TEST')
            addTime = time.strftime('%Y-%m-%d %X',time.localtime())
            if sql.table('databases').add('name,username,password,accept,ps,addtime',(value[0],value[0],'',host,ps,addTime)): n +=1
        
        return public.returnMsg(True,'DATABASE_GET_SUCCESS',(str(n),))
    
    
    #获取数据库权限
    def GetDatabaseAccess(self,get):
        name = get['name']
        users = panelMysql.panelMysql().query("select Host from mysql.user where User='" + name + "' AND Host!='localhost'")
        isError = self.IsSqlError(users)
        if isError != None: return isError
        users = self.map_to_list(users)

        if len(users)<1:
            return public.returnMsg(True,"127.0.0.1")
        
        accs = []
        for c in users:
            accs.append(c[0]);
        userStr = ','.join(accs);
        return public.returnMsg(True,userStr)
    
    #设置数据库权限
    def SetDatabaseAccess(self,get):
        #try:
        name = get['name']
        db_name = public.M('databases').where('username=?',(name,)).getField('name');
        access = get['access']
        password = public.M('databases').where("username=?",(name,)).getField('password')
        users = panelMysql.panelMysql().query("select Host from mysql.user where User='" + name + "' AND Host!='localhost'")
        for us in users:
            panelMysql.panelMysql().execute("drop user '" + name + "'@'" + us[0] + "'")

        self.__CreateUsers(db_name,name,password,access)

        #for a in access.split(','):
        #    panelMysql.panelMysql().execute("grant all privileges on " + db_name + ".* to '" + name + "'@'" + a + "' identified by '" + password + "'")
        #panelMysql.panelMysql().execute("flush privileges")
        return public.returnMsg(True, 'SET_SUCCESS')
        #except Exception as ex:
            #public.WriteLog("TYPE_DATABASE",'DATABASE_ACCESS_ERR',(name ,str(ex)))
            #return public.returnMsg(False,'SET_ERROR')
        
    
    #获取数据库配置信息
    def GetMySQLInfo(self,get):
        data = {}
        try:
            public.CheckMyCnf();
            myfile = '/etc/my.cnf';
            mycnf = public.readFile(myfile);
            rep = "datadir\s*=\s*(.+)\n"
            data['datadir'] = re.search(rep,mycnf).groups()[0];
            rep = "port\s*=\s*([0-9]+)\s*\n"
            data['port'] = re.search(rep,mycnf).groups()[0];
        except:
            data['datadir'] = '/www/server/data';
            data['port'] = '3306';
        return data;
    
    #修改数据库目录
    def SetDataDir(self,get):
        if get.datadir[-1] == '/': get.datadir = get.datadir[0:-1];
        if not os.path.exists(get.datadir): os.system('mkdir -p ' + get.datadir);
        mysqlInfo = self.GetMySQLInfo(get);
        if mysqlInfo['datadir'] == get.datadir: return public.returnMsg(False,'DATABASE_MOVE_RE');
        
        os.system('/etc/init.d/mysqld stop');
        os.system('\cp -a -r ' + mysqlInfo['datadir'] + '/* ' + get.datadir + '/');
        os.system('chown -R mysql.mysql ' + get.datadir);
        os.system('chmod -R 755 ' + get.datadir);
        os.system('rm -f ' + get.datadir + '/*.pid');
        os.system('rm -f ' + get.datadir + '/*.err');
        
        public.CheckMyCnf();
        myfile = '/etc/my.cnf';
        mycnf = public.readFile(myfile);
        public.writeFile('/etc/my_backup.cnf',mycnf);
        mycnf = mycnf.replace(mysqlInfo['datadir'],get.datadir);
        public.writeFile(myfile,mycnf);
        os.system('/etc/init.d/mysqld start');
        result = public.ExecShell('ps aux|grep mysqld|grep -v grep');
        if len(result[0]) > 10:
            public.writeFile('data/datadir.pl',get.datadir);
            return public.returnMsg(True,'DATABASE_MOVE_SUCCESS');
        else:
            os.system('pkill -9 mysqld');
            public.writeFile(myfile,public.readFile('/etc/my_backup.cnf'));
            os.system('/etc/init.d/mysqld start');
            return public.returnMsg(False,'DATABASE_MOVE_ERR');
    
    #修改数据库端口
    def SetMySQLPort(self,get):
        myfile = '/etc/my.cnf';
        mycnf = public.readFile(myfile);
        rep = "port\s*=\s*([0-9]+)\s*\n"
        mycnf = re.sub(rep,'port = ' + get.port + '\n',mycnf);
        public.writeFile(myfile,mycnf);
        os.system('/etc/init.d/mysqld restart');
        return public.returnMsg(True,'EDIT_SUCCESS');
    
    #获取错误日志
    def GetErrorLog(self,get):
        path = self.GetMySQLInfo(get)['datadir'];
        filename = '';
        for n in os.listdir(path):
            if len(n) < 5: continue;
            if n[-3:] == 'err': 
                filename = path + '/' + n;
                break;
        if not os.path.exists(filename): return public.returnMsg(False,'FILE_NOT_EXISTS');
        if hasattr(get,'close'): 
            public.writeFile(filename,'')
            return public.returnMsg(True,'LOG_CLOSE');
        return public.GetNumLines(filename,1000);
    
    #二进制日志开关
    def BinLog(self,get):
        myfile = '/etc/my.cnf';
        mycnf = public.readFile(myfile);
        if mycnf.find('#log-bin=mysql-bin') != -1:
            if hasattr(get,'status'): return public.returnMsg(False,'0');
            mycnf = mycnf.replace('#log-bin=mysql-bin','log-bin=mysql-bin')
            mycnf = mycnf.replace('#binlog_format=mixed','binlog_format=mixed')
            os.system('sync')
            os.system('/etc/init.d/mysqld restart');
        else:
            path = self.GetMySQLInfo(get)['datadir'];
            if hasattr(get,'status'): 
                dsize = 0;
                for n in os.listdir(path):
                    if len(n) < 9: continue;
                    if n[0:9] == 'mysql-bin':
                        dsize += os.path.getsize(path + '/' + n);
                return public.returnMsg(True,dsize);
            
            mycnf = mycnf.replace('log-bin=mysql-bin','#log-bin=mysql-bin')
            mycnf = mycnf.replace('binlog_format=mixed','#binlog_format=mixed')
            os.system('sync')
            os.system('/etc/init.d/mysqld restart');
            os.system('rm -f ' + path + '/mysql-bin.*')
        
        public.writeFile(myfile,mycnf);
        return public.returnMsg(True,'SUCCESS');
    
    #获取MySQL配置状态
    def GetDbStatus(self,get):
        result = {};
        data = self.map_to_list( panelMysql.panelMysql().query('show variables'));
        gets = ['table_open_cache','thread_cache_size','query_cache_type','key_buffer_size','query_cache_size','tmp_table_size','max_heap_table_size','innodb_buffer_pool_size','innodb_additional_mem_pool_size','innodb_log_buffer_size','max_connections','sort_buffer_size','read_buffer_size','read_rnd_buffer_size','join_buffer_size','thread_stack','binlog_cache_size'];
        result['mem'] = {}
        for d in data:
            for g in gets:
                if d[0] == g: result['mem'][g] = d[1];
        if 'query_cache_type' in result['mem']:
            if result['mem']['query_cache_type'] != 'ON': result['mem']['query_cache_size'] = '0';
        return result;
    
    #设置MySQL配置参数
    def SetDbConf(self,get):
        gets = ['key_buffer_size','query_cache_size','tmp_table_size','max_heap_table_size','innodb_buffer_pool_size','innodb_log_buffer_size','max_connections','query_cache_type','table_open_cache','thread_cache_size','sort_buffer_size','read_buffer_size','read_rnd_buffer_size','join_buffer_size','thread_stack','binlog_cache_size'];
        emptys = ['max_connections','query_cache_type','thread_cache_size','table_open_cache']
        mycnf = public.readFile('/etc/my.cnf');
        n = 0;
        m_version = public.readFile('/www/server/mysql/version.pl')
        if not m_version: m_version = '';
        for g in gets:
            if m_version.find('8.') == 0 and g in ['query_cache_type','query_cache_size']: continue;
            s = 'M';
            if n > 5: s = 'K';
            if g in emptys: s = '';
            rep = '\s*'+g+'\s*=\s*\d+(M|K|k|m|G)?\n';
            c = g+' = ' + get[g] + s +'\n'
            if mycnf.find(g) != -1:
                mycnf = re.sub(rep,'\n'+c,mycnf,1);
            else:
                mycnf = mycnf.replace('[mysqld]\n','[mysqld]\n' +c)
            n+=1;
        public.writeFile('/etc/my.cnf',mycnf);
        return public.returnMsg(True,'SET_SUCCESS');
    
    #获取MySQL运行状态
    def GetRunStatus(self,get):
        import time;
        result = {}
        data = panelMysql.panelMysql().query('show global status');
        gets = ['Max_used_connections','Com_commit','Com_rollback','Questions','Innodb_buffer_pool_reads','Innodb_buffer_pool_read_requests','Key_reads','Key_read_requests','Key_writes','Key_write_requests','Qcache_hits','Qcache_inserts','Bytes_received','Bytes_sent','Aborted_clients','Aborted_connects','Created_tmp_disk_tables','Created_tmp_tables','Innodb_buffer_pool_pages_dirty','Opened_files','Open_tables','Opened_tables','Select_full_join','Select_range_check','Sort_merge_passes','Table_locks_waited','Threads_cached','Threads_connected','Threads_created','Threads_running','Connections','Uptime']
        try:
            if data[0] == 1045:
                return public.returnMsg(False,'MySQL密码错误!')
        except:pass
        for d in data:
            for g in gets:
                if d[0] == g: result[g] = d[1];
        result['Run'] = int(time.time()) - int(result['Uptime'])
        tmp = panelMysql.panelMysql().query('show master status');
        try:
            result['File'] = tmp[0][0];
            result['Position'] = tmp[0][1];
        except:
            result['File'] = 'OFF';
            result['Position'] = 'OFF';
        return result;
    
    #取慢日志
    def GetSlowLogs(self,get):
        path = '/www/server/data/mysql-slow.log';
        if not os.path.exists(path): return public.returnMsg(False,'日志文件不存在!');
        return public.returnMsg(True,public.GetNumLines(path,1000));
    

    # 获取当前数据库信息
    def GetInfo(self,get):
        info=self.GetdataInfo(get)
        return info
        if info:
            return info
        else:
            return public.returnMsg(False,"获取数据库失败!")
    
    #修复表信息
    def ReTable(self,get):
        info=self.RepairTable(get)

        if info:
            return public.returnMsg(True,"修复完成!")
        else:
            return public.returnMsg(False,"修复失败!")
    
    # 优化表
    def OpTable(self,get):
        info=self.OptimizeTable(get)
        if info:
            return public.returnMsg(True,"优化成功!")
        else:
            return public.returnMsg(False,"优化失败或者已经优化过了")

    #更改表引擎
    def AlTable(self,get):
        info=self.AlterTable(get)
        if info:
            return public.returnMsg(True,"更改成功")
        else:
            return public.returnMsg(False,"更改失败")