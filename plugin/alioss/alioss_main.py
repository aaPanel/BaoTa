#!/usr/bin/python
#coding: utf-8
#-----------------------------
# 宝塔Linux面板网站备份工具 - ALIOSS
#-----------------------------
import sys,os
if sys.version_info[0] ==2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
os.chdir('/www/server/panel');
sys.path.append("class/")
import public,db,time,oss2

class alioss_main:
    __oss = None
    __bucket_name = None
    __bucket_domain = None
    __bucket_path = None
    __error_count = 0
    __error_msg = "ERROR: 无法连接到阿里云OSS服务器，请检查[AccessKeyId/AccessKeySecret/Endpoint]设置是否正确!"
    __setupPath = 'plugin/alioss'
    
    def __init__(self):
        self.__conn();
    
    def __conn(self):
        if self.__oss: return;
        #获取阿里云秘钥
        cfile = 'plugin/alioss/config.conf';
        if not os.path.exists(cfile): cfile = 'data/aliossAs.conf';
        if not os.path.exists(cfile): public.writeFile(cfile,'');
        fp = open(cfile,'r');
        if not fp:
            print('ERROR: 请检查aliossAs.conf文件中是否有阿里云AccessKey相关信息!');

        keys = fp.read().split('|');
        if len(keys) < 4:
            keys = ['','','','','']
        if len(keys) < 5: keys.append('/');
        
        self.__bucket_name     = keys[2];
        if keys[3].find(keys[2]) != -1: keys[3] = keys[3].replace(keys[2]+'.','');
        self.__bucket_domain     = keys[3];
        self.__bucket_path = self.get_path(keys[4] + '/bt_backup/');
        if self.__bucket_path[:1] == '/': self.__bucket_path = self.__bucket_path[1:]
        
        #构建鉴权对象
        self.__oss = oss2.Auth(keys[0], keys[1]);
        
    def GetConfig(self,get):
        path = self.__setupPath + '/config.conf';
        if not os.path.exists(path):
            if os.path.exists('conf/aliossAs.conf'): public.writeFile(path,public.readFile('conf/aliossAs.conf'));
        if not os.path.exists(path): return ['','','','','/'];
        conf = public.readFile(path);
        if not conf: return ['','','','','/']
        result = conf.split('|');
        if len(result) < 5: result.append('/');
        return result;
    
    def SetConfig(self,get):
        path = self.__setupPath + '/config.conf';
        conf = get.access_key + '|' + get.secret_key +'|' + get.bucket_name + '|' + get.bucket_domain + '|' + get.bucket_path;
        public.writeFile(path,conf);
        return public.returnMsg(True,'设置成功!');
        
    #上传文件
    def upload_file(self,filename):
        #连接OSS服务器
        self.__conn();
        try:
            #保存的文件名
            key = filename.split('/')[-1];
            key = self.__bucket_path + key;
            
            #获取存储对象
            bucket = oss2.Bucket(self.__oss,self.__bucket_domain,self.__bucket_name)
            
            #使用断点续传
            oss2.defaults.connection_pool_size = 4;
            result = oss2.resumable_upload(bucket, key, filename,
                store=oss2.ResumableStore(root='/tmp'), #进度保存目录
                multipart_threshold=1024*1024 * 2,
                part_size=1024*1024,   #分片大小
                num_threads=1);       #线程数
            return result.status
        except Exception as ex:
            if ex.status == 403:
                time.sleep(5);
                self.__error_count += 1;
                if self.__error_count < 2: #重试2次
                    self.sync_date();
                    self.upload_file(filename); 
                
            print(self.__error_msg)
            return None
        
    #创建目录
    def create_dir(self,get):
        self.__conn();
        path = self.get_path(get.path + get.dirname);
        filename = '/tmp/dirname.pl';
        public.writeFile(filename,'');
        bucket = oss2.Bucket(self.__oss,self.__bucket_domain,self.__bucket_name)
        result = bucket.put_object_from_file(path, filename)
        os.remove(filename);
        return public.returnMsg(True,'创建成功!');
    
    #取回文件列表
    def get_list(self,get):
        self.__conn();
        #try:
        from itertools import islice
        bucket = oss2.Bucket(self.__oss,self.__bucket_domain,self.__bucket_name)
        result = oss2.ObjectIterator(bucket);
        data = [];
        path = self.get_path(get.path);
        '''key, last_modified, etag, type, size, storage_class'''
        for b in islice(oss2.ObjectIterator(bucket,delimiter = '/',prefix = path),1000):
            b.key = b.key.replace(path,'');
            if not b.key: continue;
            tmp = {}
            tmp['name'] = b.key
            tmp['size'] = b.size
            tmp['type'] = b.type
            tmp['download'] = self.download_file(path + b.key,False);
            tmp['time'] = b.last_modified
            data.append(tmp)
        mlist = {}
        mlist['path'] = get.path;
        mlist['list'] = data;
        return mlist;
        #except Exception as ex:
            #if ex.status == 403: 
            #    self.__error_count += 1;
             #   if self.__error_count < 2:
            #        self.sync_date();
            #        self.get_list(get);
            #print(self.__error_msg)
            #return public.returnMsg(False,str(ex))
    
    def sync_date(self):
        import config
        config.config().syncDate(None)
    
    #下载文件
    def download_file(self,filename,m=True):
        self.__conn();
        if m: 
            import re
            m_type = 'site'
            if filename[:2] == 'Db': m_type = 'database'
            m_name = re.search('Db_(.+)_20\d+_\d+\.',filename).groups()[0]
            filename = self.__bucket_path + m_type + '/' + m_name + '/' + filename
        try:
            bucket = oss2.Bucket(self.__oss,self.__bucket_domain,self.__bucket_name)
            private_url = bucket.sign_url('GET', filename, 3600)
            return private_url
        except:
            print(self.__error_msg)
            return None
    
    #取目录路径
    def get_path(self,path):
        if path == '/': path = '';
        if path[:1] == '/': 
            path = path[1:];
            if path[-1:] != '/': path += '/';
        if path == '/': path = ''
        return path.replace('//','/');

    #删除文件
    def delete_file(self,filename):
        self.__conn();
        try:
            bucket = oss2.Bucket(self.__oss,self.__bucket_domain,self.__bucket_name)
            result = bucket.delete_object(filename)
            return result.status
        except Exception as ex:
            if ex.status == 403: 
                self.__error_count += 1;
                if self.__error_count < 2: 
                    self.sync_date();
                    self.delete_file(filename);
                
            print(self.__error_msg)
            return None
    
    #删除文件
    def remove_file(self,get):
        path = self.get_path(get.path);
        filename = path + get.filename;
        self.delete_file(filename);
        return public.returnMsg(True,'删除文件成功!');
        
        
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
        
        if self.__bucket_path != '': self.__bucket_path += 'site/' + name + '/';
        
        #上传文件
        self.upload_file(filename);
        
        outTime = time.time() - startTime
        pid = sql.table('sites').where('name=?',(name,)).getField('id');
        sql.table('backup').add('type,name,pid,filename,addtime,size',('0',os.path.basename(filename),pid,'alioss',endDate,os.path.getsize(filename)))
        log = "网站["+name+"]已成功备份到阿里云OSS,用时["+str(round(outTime,2))+"]秒";
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
                self.delete_file(self.__bucket_path + backup['name']);
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
        
        #上传
        if self.__bucket_path != '': self.__bucket_path += 'database/' + name + '/';
        self.upload_file(filename);
        
        endDate = time.strftime('%Y/%m/%d %X',time.localtime())
        outTime = time.time() - startTime
        pid = sql.table('databases').where('name=?',(name,)).getField('id');
        
        sql.table('backup').add('type,name,pid,filename,addtime,size',(1,os.path.basename(filename),pid,'alioss',endDate,os.path.getsize(filename)))
        log = "数据库["+name+"]已成功备份到阿里云OSS,用时["+str(round(outTime,2))+"]秒";
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
                    
                self.delete_file(self.__bucket_path + backup['name']);
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
        if self.__bucket_path != '': self.__bucket_path += 'path/' + name + '/';
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
                self.delete_file(self.__bucket_path + backup['filename']);
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
    q = alioss_main();
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