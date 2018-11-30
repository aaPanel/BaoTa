#!/usr/bin/python
#coding: utf-8
#-----------------------------
# 宝塔Linux面板网站备份工具 - 又拍云
#-----------------------------
import sys,os
if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
os.chdir('/www/server/panel');
sys.path.append("class/")
import public,db,time,json,upyun

class upyun_main:
    __PATH = 'plugin/upyun/'
    __UP = None;
    __NAME = None;
    __USER = None;
    __PASS = None;
    __DOMAIN = None;
    
    #初始化
    def __init__(self):
        if not self.__UP:
            try:
                data = json.loads(public.readFile(self.__PATH+'conf.pl'));
                self.__DOMAIN = data['domain'];
                self.__NAME = data['service'];
                self.__USER = data['username'];
                self.__PASS = data['password'];
                self.__UP = upyun.UpYun(self.__NAME, self.__USER, self.__PASS);
                self.CheckHook();
            except:
                self.__UP = None;
                pass;
    
    #检查是否写入钩子
    def CheckHook(self):
        try:
            libFile = 'data/libList.conf';
            mlist = json.loads(public.readFile(libFile));
            for lt in mlist:
                if lt['opt'] == 'upyun': return True;
            
            data = {'name':'又拍云存储','opt':'upyun','module':'upyun'}
            mlist.append(data);
            public.writeFile(libFile,json.dumps(mlist));
            return True
        except:
            return False;
    
    #获取签名
    def GetSgin(self,get):
        from upyun.modules.exception import UpYunClientException
        from upyun.modules.sign import make_policy, make_signature
        from upyun.modules.httpipe import cur_dt
        dt = cur_dt();
        
        policy = make_policy({
            'bucket': self.__NAME,
            'expiration': int(time.time()) + 600,
            'save-key': get.filename,
            'date': dt
        });
        
        signature = make_signature(
            username=self.__USER,
            password=public.md5(self.__PASS),
            method='POST',
            uri='/' + self.__NAME,
            date=dt,
            policy=policy
        );
        
        return policy,signature,self.__NAME
    
    #设置Token
    def SetToken(self,get):
        data = {
                'domain':get.domain,
                'service':get.service,
                'username':get.username,
                'password':get.password
                }
        public.writeFile(self.__PATH + 'conf.pl',json.dumps(data));
        try:
            self.__UP = upyun.UpYun(get.service, get.username, get.password);
            get.path = '/';
            if not self.GetList(get): return public.returnMsg(False,'API资料校验失败，请核实!');
            return public.returnMsg(True,'设置成功!');
        except:
            return public.returnMsg(False,'API资料校验失败，请核实!');
        

        
    #获取列表
    def GetList(self,get):
        try:
            data = {}
            data['list'] = self.__UP.getlist(get.path, order='asc', begin='');
            data['usage'] = self.__UP.usage();
            data['domain'] = self.__DOMAIN;
            return data;
        except:
            return False;
    
    #上传文件
    def UploadFile(self,get):
        try:
            from upyun import FileStore
            if not os.path.exists(get.filename): public.returnMsg(False,'文件不存在!');
            filename = os.path.basename(get.filename)
            with open(get.filename, 'rb') as f:
                res = self.__UP.put(get.path + '/' + filename, f, checksum=True, need_resume=True, store=FileStore())
            return res;
        except:
            return public.returnMsg(False,'连接服务器失败!');
    
    #删除文件
    def DeleteFile(self,get):
        try:
            res = self.__UP.delete(get.filename);
            return public.returnMsg(True,'删除成功!');
        except:
            return public.returnMsg(False,'不能删除非空目录!');
        
    #获取服务使用情况
    def UsAge(self,get):
        try:
            data = json.loads(public.readFile(self.__PATH+'conf.pl'));
            try:
                data['usage'] = self.__UP.usage();
            except:
                data['usage'] = 0;
            return data;
        except:
            return False;
    
    #创建目录
    def CreateDir(self,get):
        try:
            self.__UP.mkdir(get.path);
            return public.returnMsg(True,'创建成功');
        except:
            return public.returnMsg(False,'连接服务器失败!');

    #下载文件
    def download_file(self,filename):
        if filename.find('/') == -1:
            b_info = public.M('backup').where('filename=?',(filename,)).field('pid,type').find()
            type_list = {'0':'site','1':'database','2':'path'}
            name = public.M(type_list[b_info['type']]+'s').where('id=?',(b_info['pid'],)).getField('name')
            filename = self.__PATH + '/' + type_list[b_info['type']] + '/' + name + '/' + filename
            
        return 'http://' + self.__DOMAIN + filename
        
    
    #备份网站
    def backupSite(self,name,count):
        sql = db.Sql();
        path = sql.table('sites').where('name=?',(name,)).getField('path');
        startTime = time.time();
        if not path:
            endDate = time.strftime('%Y/%m/%d %X',time.localtime())
            log = "网站["+name+"]不存在!"
            print("★["+endDate+"] "+log)
            print("----------------------------------------------------------------------------")
            return;
        
        backup_path = sql.table('config').where("id=?",(1,)).getField('backup_path') + '/site';
        if not os.path.exists(backup_path): public.ExecShell("mkdir -p " + backup_path);
        
        filename= backup_path + "/Web_" + name + "_" + time.strftime('%Y%m%d_%H%M%S',time.localtime()) + '_' + public.GetRandomString(8)+'.tar.gz'
        public.ExecShell("cd " + os.path.dirname(path) + " && tar zcvf '" + filename + "' '" + os.path.basename(path) + "' > /dev/null")
        endDate = time.strftime('%Y/%m/%d %X',time.localtime())
        
        if not os.path.exists(filename):
            log = "网站["+name+"]备份失败!"
            print("★["+endDate+"] "+log)
            print("----------------------------------------------------------------------------")
            return;
        
        #上传文件
        get = getObject();
        get.filename = filename;
        get.path = '/bt_backup/sites/' + name
        self.UploadFile(get);
        
        outTime = time.time() - startTime
        pid = sql.table('sites').where('name=?',(name,)).getField('id');
        download =  get.path + '/' + os.path.basename(filename)
        sql.table('backup').add('type,name,pid,filename,addtime,size',('0',download,pid,'upyun',endDate,os.path.getsize(filename)))
        log = "网站["+name+"]已成功备份到又拍云存储,用时["+str(round(outTime,2))+"]秒";
        public.WriteLog('计划任务',log)
        print("★["+endDate+"] " + log)
        print("|---保留最新的["+count+"]份备份")
        print("|---文件名:"+os.path.basename(filename))
        
        #清理本地文件
        public.ExecShell("rm -f " + filename)
        
        #清理多余备份
        backups = sql.table('backup').where('type=? and pid=?',('0',pid)).field('id,name,filename').select();
        
        num = len(backups) - int(count)
        if  num > 0:
            for backup in backups:
                if os.path.exists(backup['filename']):
                    public.ExecShell("rm -f " + backup['filename']);
                get.filename = '/bt_backup/sites/' + name +'/' + backup['name']
                self.DeleteFile(get);
                sql.table('backup').where('id=?',(backup['id'],)).delete();
                num -= 1;
                print("|---已清理过期备份文件：" + backup['name'])
                if num < 1: break;
        return None
    
    #备份数据库
    def backupDatabase(self,name,count):
        sql = db.Sql();
        path = sql.table('databases').where('name=?',(name,)).getField('path');
        startTime = time.time();
        if not path:
            endDate = time.strftime('%Y/%m/%d %X',time.localtime())
            log = "数据库["+name+"]不存在!"
            print("★["+endDate+"] "+log)
            print("----------------------------------------------------------------------------")
            return;
        
        
        backup_path = sql.table('config').where("id=?",(1,)).getField('backup_path') + '/database';
        if not os.path.exists(backup_path): public.ExecShell("mkdir -p " + backup_path);
        
        filename = backup_path + "/Db_" + name + "_" + time.strftime('%Y%m%d_%H%M%S',time.localtime())+'_'+public.GetRandomString(8)+".sql.gz"
        
        import re
        mysql_root = sql.table('config').where("id=?",(1,)).getField('mysql_root')
        mycnf = public.readFile('/etc/my.cnf');
        rep = "\[mysqldump\]\nuser=root"
        sea = "[mysqldump]\n"
        subStr = sea + "user=root\npassword=" + mysql_root+"\n";
        mycnf = mycnf.replace(sea,subStr)
        if len(mycnf) > 100:
            public.writeFile('/etc/my.cnf',mycnf);
        
        public.ExecShell("/www/server/mysql/bin/mysqldump --opt --default-character-set=utf8 " + name + " | gzip > " + filename)
        
        if not os.path.exists(filename):
            endDate = time.strftime('%Y/%m/%d %X',time.localtime())
            log = "数据库["+name+"]备份失败!"
            print("★["+endDate+"] "+log)
            print("----------------------------------------------------------------------------")
            return;

        mycnf = public.readFile('/etc/my.cnf');
        mycnf = mycnf.replace(subStr,sea)
        if len(mycnf) > 100:
            public.writeFile('/etc/my.cnf',mycnf);
        
        #上传
        get = getObject();
        get.filename = filename;
        get.path = '/bt_backup/database/' + name
        self.UploadFile(get);
        
        endDate = time.strftime('%Y/%m/%d %X',time.localtime())
        outTime = time.time() - startTime
        pid = sql.table('databases').where('name=?',(name,)).getField('id');
        download = get.path + '/' + os.path.basename(filename)
        sql.table('backup').add('type,name,pid,filename,addtime,size',(1,download,pid,'upyun',endDate,os.path.getsize(filename)))
        log = "数据库["+name+"]已成功备份到又拍云存储,用时["+str(round(outTime,2))+"]秒";
        public.WriteLog('计划任务',log)
        print("★["+endDate+"] " + log)
        print("|---保留最新的["+count+"]份备份")
        print("|---文件名:"+os.path.basename(filename))
        
        #清理本地文件
        public.ExecShell("rm -f " + filename)
        
        #清理多余备份     
        backups = sql.table('backup').where('type=? and pid=?',('1',pid)).field('id,name,filename').select();
        
        num = len(backups) - int(count)
        if  num > 0:
            for backup in backups:
                if os.path.exists(backup['filename']):
                    public.ExecShell("rm -f " + backup['filename']);
                get.filename = '/bt_backup/database/' + name +'/' + backup['name']
                self.DeleteFile(get);
                sql.table('backup').where('id=?',(backup['id'],)).delete();
                num -= 1;
                print("|---已清理过期备份文件：" + backup['name'])
                if num < 1: break;
        return None

    #备份指定目录
    def backupPath(self,path,count):
        sql = db.Sql();
        startTime = time.time();
        name = os.path.basename(path)
        backup_path = sql.table('config').where("id=?",(1,)).getField('backup_path') + '/path';
        if not os.path.exists(backup_path): os.makedirs(backup_path);
        filename= backup_path + "/Path_" + name + "_" + time.strftime('%Y%m%d_%H%M%S',time.localtime()) + '.tar.gz'
        os.system("cd " + os.path.dirname(path) + " && tar zcvf '" + filename + "' '" + os.path.basename(path) + "' > /dev/null")
        
        get = getObject();
        get.filename = filename;
        get.path = '/bt_backup/path/' + name
        self.UploadFile(get);

        endDate = time.strftime('%Y/%m/%d %X',time.localtime())
        if not os.path.exists(filename):
            log = u"目录["+path+"]备份失败"
            print(u"★["+endDate+"] "+log)
            print(u"----------------------------------------------------------------------------")
            return;
        
        outTime = time.time() - startTime
        download = get.path + '/' + os.path.basename(filename)
        sql.table('backup').add('type,name,pid,filename,addtime,size',('2',download,path,'upyun',endDate,os.path.getsize(filename)))
        log = u"目录["+path+"]备份成功,用时["+str(round(outTime,2))+"]秒";
        public.WriteLog(u'计划任务',log)
        print(u"★["+endDate+"] " + log)
        print(u"|---保留最新的["+count+u"]份备份")
        print(u"|---文件名:"+filename)
        
        #清理多余备份     
        backups = sql.table('backup').where('type=?',('2',)).field('id,filename').select();
        
        #清理本地备份
        if os.path.exists(filename): os.remove(filename)

        num = len(backups) - int(count)
        if  num > 0:
            for backup in backups:
                if os.path.exists(backup['filename']): os.remove(backup['filename'])
                get.filename = '/bt_backup/path/' + name +'/' + backup['name']
                self.DeleteFile(get);
                sql.table('backup').where('id=?',(backup['id'],)).delete();
                num -= 1;
                print(u"|---已清理过期备份文件：" + backup['filename'])
                if num < 1: break;
        
    
    def backupSiteAll(self,save):
        sites = public.M('sites').field('name').select()
        for site in sites:
            self.backupSite(site['name'],save)
        

    def backupDatabaseAll(self,save):
        databases = public.M('databases').field('name').select()
        for database in databases:
            self.backupDatabase(database['name'],save)

class getObject: pass;
    
if __name__ == "__main__":
    import json
    data = None
    q = upyun_main();
    type = sys.argv[1];
    if type == 'site':
        if sys.argv[2] == 'ALL':
             q.backupSiteAll( sys.argv[3])
        else:
            q.backupSite(sys.argv[2], sys.argv[3])
        exit()
    elif type == 'database':
        if sys.argv[2] == 'ALL':
            data = q.backupDatabaseAll(sys.argv[3])
        else:
            data = q.backupDatabase(sys.argv[2], sys.argv[3])
        exit()
    elif type == 'path':
        data = q.backupPath(sys.argv[2],sys.argv[3])
    else:
        data = 'ERROR: 参数不正确!';
    print(json.dumps(data))