#!/usr/bin/python
#coding: utf-8
#-----------------------------
# 宝塔Linux面板网站备份工具 - 七牛
#-----------------------------
import sys,os
if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
os.chdir('/www/server/panel');
sys.path.append("class/")
import public,db,time

from qiniu import Auth
import qiniu.config



class qiniu_main:
    __qiniu = None
    __bucket_name = None
    __bucket_domain = None
    __error_msg = "ERROR: 无法连接到七牛云服务器，请检查[AK/SK/存储空间]设置是否正确!"
    __setupPath = 'plugin/qiniu'
    def __conn(self):
        if self.__qiniu: return;
        #获取七牛秘钥
        cfile = 'plugin/qiniu/config.conf';
        if not os.path.exists(cfile): cfile = 'data/qiniuAs.conf';
        fp = open(cfile,'r');
        if not fp:
            print('ERROR: 请检查qiniuAs.conf文件中是否有七牛Key相关信息!');
            return None
        keys = fp.read().split('|');
        if len(keys) < 4:
            print('ERROR: 请检查qiniuAs.conf文件中的七牛Key信息是否完整!');
            return None
        
        self.__bucket_name     = keys[2].strip();
        self.__bucket_domain     = keys[3].strip();
        
        #构建鉴权对象
        self.__qiniu = Auth(keys[0], keys[1]);
        
    def GetConfig(self,get):
        path = self.__setupPath + '/config.conf';
        if not os.path.exists(path):
            if os.path.exists('conf/qiniuAs.conf'): public.writeFile(path,public.readFile('conf/qiniuAs.conf'));
        if not os.path.exists(path): return False;
        conf = public.readFile(path);
        return conf.split('|');
    
    def SetConfig(self,get):
        path = self.__setupPath + '/config.conf';
        conf = get.access_key.strip() + '|' + get.secret_key.strip() +'|' + get.bucket_name.strip() + '|' + get.bucket_domain.strip();
        public.writeFile(path,conf);
        return public.returnMsg(True,'设置成功!');
        
        
    #上传文件
    def upload_file(self,filename):
        self.__conn();
        try:
            from qiniu import put_file, etag, urlsafe_base64_encode
            key = filename.split('/')[-1];
            token = self.__qiniu.upload_token(self.__bucket_name, key, 3600*2)
            result = put_file(token, key, filename)
            return result[0]
        except:
            print(self.__error_msg)
            return None
    
    #取回文件信息
    def get_files(self,filename):
        self.__conn();
        try:
            from qiniu import BucketManager
            bucket = BucketManager(self.__qiniu)
            result = bucket.stat(self.__bucket_name, filename)
            return result[0]
        except:
            print(self.__error_msg)
            return None

    def GetList(self,get):
        return self.get_list();
    
    #取回文件列表
    def get_list(self,path = '/'):
        self.__conn();
        try:
            if path == '/': path = ''
            from qiniu import BucketManager
            bucket = BucketManager(self.__qiniu)
            result = bucket.list(self.__bucket_name,path,None,1000,None)
            if not len(result[0]['items']): return [{"mimeType": "application/test", "fsize": 0, "hash": "", "key": "没有文件", "putTime": 14845314157209192}];
            return result[0]['items']
        except:
            print(self.__error_msg)
            return False
    
    #下载文件
    def download_file(self,filename):
        self.__conn();
        try:
            base_url = 'http://%s/%s' % (self.__bucket_domain, filename)
            private_url = self.__qiniu.private_download_url(base_url, expires=3600)
            return private_url.strip()
        except:
            print(self.__error_msg)
            return False

    #删除文件
    def DeleteFile(self,get):
        return self.delete_file(get.filename)

    #删除文件
    def delete_file(self,filename):
        self.__conn();
        try:
            from qiniu import BucketManager
            bucket = BucketManager(self.__qiniu)
            res,info = bucket.delete(self.__bucket_name, filename)
            if res == {}: return public.returnMsg(True,'删除成功')
            return public.returnMsg(False,'删除失败')
        except:
            print(self.__error_msg)
            return False
        
    #备份网站
    def backupSite(self,name,count):
        self.__conn();
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
        
        filename= backup_path + "/Web_" + name + "_" + time.strftime('%Y%m%d_%H%M%S',time.localtime()) + '.tar.gz'
        public.ExecShell("cd " + os.path.dirname(path) + " && tar zcvf '" + filename + "' '" + os.path.basename(path) + "' > /dev/null")
        endDate = time.strftime('%Y/%m/%d %X',time.localtime())
        
        if not os.path.exists(filename):
            log = "网站["+name+"]备份失败!"
            print("★["+endDate+"] "+log)
            print("----------------------------------------------------------------------------")
            return;
        
        #上传到七牛
        self.upload_file(filename);
        
        outTime = time.time() - startTime
        pid = sql.table('sites').where('name=?',(name,)).getField('id');
        sql.table('backup').add('type,name,pid,filename,addtime,size',('0',os.path.basename(filename),pid,'qiniu',endDate,os.path.getsize(filename)))
        log = "网站["+name+"]已成功备份到七牛云,用时["+str(round(outTime,2))+"]秒";
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
                self.delete_file(backup['name']);
                sql.table('backup').where('id=?',(backup['id'],)).delete();
                num -= 1;
                print("|---已清理过期备份文件：" + backup['name'])
                if num < 1: break;
        return None
    
    #备份数据库
    def backupDatabase(self,name,count):
        self.__conn();
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
        
        filename = backup_path + "/Db_" + name + "_" + time.strftime('%Y%m%d_%H%M%S',time.localtime())+".sql.gz"
        
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
        
        #上传到七牛
        self.upload_file(filename);
        
        endDate = time.strftime('%Y/%m/%d %X',time.localtime())
        outTime = time.time() - startTime
        pid = sql.table('databases').where('name=?',(name,)).getField('id');
        
        sql.table('backup').add('type,name,pid,filename,addtime,size',(1,os.path.basename(filename),pid,'qiniu',endDate,os.path.getsize(filename)))
        log = "数据库["+name+"]已成功备份到七牛云,用时["+str(round(outTime,2))+"]秒";
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
                    
                self.delete_file(backup['name']);
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
        print(filename)
        os.system("cd " + os.path.dirname(path) + " && tar zcvf '" + filename + "' '" + os.path.basename(path) + "' > /dev/null")
                
        endDate = time.strftime('%Y/%m/%d %X',time.localtime())
        if not os.path.exists(filename):
            log = u"目录["+path+"]备份失败"
            print(u"★["+endDate+"] "+log)
            print(u"----------------------------------------------------------------------------")
            return;
        
        #上传文件
        self.upload_file(filename);
        outTime = time.time() - startTime
        sql.table('backup').add('type,name,pid,filename,addtime,size',('2',path,'0',filename,endDate,os.path.getsize(filename)))
        log = u"目录["+path+"]备份成功,用时["+str(round(outTime,2))+"]秒";
        public.WriteLog(u'计划任务',log)
        print(u"★["+endDate+"] " + log)
        print(u"|---保留最新的["+count+u"]份备份")
        print(u"|---文件名:"+filename)
        
        #清理多余备份     
        backups = sql.table('backup').where('type=? and pid=?',('2',0)).field('id,filename').select();
        
        #清理本地文件
        if os.path.exists(filename): os.remove(filename)

        num = len(backups) - int(count)
        if  num > 0:
            for backup in backups:
                if os.path.exists(backup['filename']): os.remove(backup['filename'])
                self.delete_file(backup['filename']);
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
    
    
if __name__ == "__main__":
    import json
    data = None
    q = qiniu_main();
    type = sys.argv[1];
    if type == 'site':
        if sys.argv[2] == 'ALL':
             q.backupSiteAll( sys.argv[3])
        else:
            q.backupSite(sys.argv[2], sys.argv[3])
        exit()
    elif type == 'database':
        if sys.argv[2] == 'ALL':
            q.backupDatabaseAll(sys.argv[3])
        else:
            q.backupDatabase(sys.argv[2], sys.argv[3])
        exit()
    elif type == 'path':
        q.backupPath(sys.argv[2],sys.argv[3])
    elif type == 'upload':
        data = q.upload_file(sys.argv[2]);
    elif type == 'download':
        data = q.download_file(sys.argv[2]);
    elif type == 'get':
        data = q.get_files(sys.argv[2]);
    elif type == 'list':
        data = q.get_list();
    elif type == 'delete_file':
        data = q.delete_file(sys.argv[2]);
    else:
        data = 'ERROR: 参数不正确!';
    
    print(json.dumps(data))