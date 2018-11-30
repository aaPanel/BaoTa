#!/usr/bin/python
# coding: utf-8
# -----------------------------
# 宝塔Linux面板网站备份工具 - TXCOS
# Author: 1249648969@qq.com
# -----------------------------
import sys, os
if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
os.chdir('/www/server/panel')
sys.path.append("class/")
import public, db, time,re,json
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client


# 腾讯云oss 的类
class txcos_main:
    __oss = None
    __bucket_path = None
    __error_count = 0
    __secret_id = 'None'
    __secret_key = 'None'
    __region = 'None'
    __Bucket = 'None'
    __error_msg = "ERROR: 无法连接腾讯云COS !"
    __setupPath = '/www/server/panel/plugin/txcos'
    '''
     __oss         : COS 客户端的对象
    __bucket_path ： COS 的路径 例如：/   /data
    __error_count : 错误次数
    __secret_id  ： 腾讯云COS 的secret_id 
    __secret_key : 腾讯云COS 的secret_key
    __region     : 腾讯云COS 的地区
    __Bucket     : COS 的Bucket
    __error_msg  ： 错误次数
    __error_msg   ： 错误信息
    '''

    def __init__(self):
        self.__conn()

    def set_cos(self):
        cfile = 'plugin/txcos/config.conf'
        fp = open(cfile, 'r')
        keys = fp.read().split('|')
        self.__secret_id = keys[0]
        self.__secret_key = keys[1]
        self.__region = keys[2]
        self.__Bucket = keys[3]
        self.__bucket_path = self.get_path(keys[4])
        try:
            config = CosConfig(Region=self.__region, SecretId=self.__secret_id, SecretKey=self.__secret_key, Token=None,Scheme='http')
            self.__oss = CosS3Client(config)
        except:
            if self.__oss == None:
                self.__conn()
            return json.dumps(self.__error_msg)


    def __conn(self):
        cfile = 'plugin/txcos/config.conf'
        if not os.path.exists(cfile): cfile = 'data/txcos.conf';
        if not os.path.exists(cfile): public.writeFile(cfile, '');
        fp = open(cfile, 'r')
        if not fp:
            print('ERROR: 请检查atxcos.conf文件中是否有腾讯云secret_id相关信息!')
        keys = fp.read().split('|')
        if len(keys) < 4:
            keys = ['', '', '', '', '/']
        if len(keys) < 5: keys.append('/');

        self.__secret_id = keys[0]
        self.__secret_key = keys[1]
        self.__region = keys[2]
        self.__Bucket = keys[3]
        self.__bucket_path = self.get_path(keys[4])
        try:
            config = CosConfig(Region=self.__region, SecretId=self.__secret_id, SecretKey=self.__secret_key, Token=None,Scheme='http')
            self.__oss = CosS3Client(config)
        except:
            if self.__oss==None:return json.dumps(self.__error_msg)

    def GetConfig(self, get):
        path = self.__setupPath + '/config.conf'
        if not os.path.exists(path):
            if os.path.exists('conf/atxcos.conf'): public.writeFile(path, public.readFile('conf/atxcos.conf'));
        if not os.path.exists(path): return ['', '', '', '', '/'];
        conf = public.readFile(path)
        if not conf: return ['', '', '', '', '/']
        result = conf.split('|')
        if len(result) < 5: result.append('/');
        return result

    def SetConfig(self, get):
        path = self.__setupPath + '/config.conf'
        conf = get.secret_id + '|' + get.secret_key + '|' + get.region + '|' + get.Bucket + '|' + get.bucket_path
        public.writeFile(path, conf)
        return public.returnMsg(True, '设置成功!')

    # 上传文件
    def upload_file(self, filename):
        if not self.__oss:
            self.set_cos()
            if self.__oss:
                return False
        try:
            # 断点续传
            key = filename.split('/')[-1]
            print(key)
            key = self.__bucket_path + key
            print(key)
            # 短点续传
            response = self.__oss.upload_file(
                Bucket=self.__Bucket,
                Key=key,
                MAXThread=10,
                PartSize=5,
                LocalFilePath=filename)
        except:
            time.sleep(1)
            self.__error_count += 1
            if self.__error_count < 2:  # 重试2次
                self.sync_date()
                self.upload_file(filename)
            print(self.__error_msg)
            return None

    def create_dir(self, get):
        if not self.__oss:
            self.set_cos()
            if self.__oss:
                return False
        path = self.get_path(get.path + get.dirname)
        filename = '/tmp/dirname.pl'
        public.writeFile(filename, '')
        response = self.__oss.put_object(
            Bucket=self.__Bucket,
            Body=b'',
            Key=path,
        )
        os.remove(filename)
        return public.returnMsg(True, '创建成功!')

    def get_list(self, get):
        if not self.__oss:
            self.set_cos()
            if self.__oss:
                return False
        try:
            data = []
            dir_list = []
            path = self.get_path(get.path)
            if 'Contents'  in self.__oss.list_objects(Bucket=self.__Bucket, MaxKeys=100, Delimiter='/', Prefix=path):
                for b in self.__oss.list_objects(Bucket=self.__Bucket, MaxKeys=100, Delimiter='/', Prefix=path)['Contents']:
                    tmp = {}
                    b['Key'] = b['Key'].replace(path, '')
                    if not b['Key']: continue
                    tmp['name'] = b['Key']
                    tmp['size'] = b['Size']
                    tmp['type'] = b['StorageClass']
                    tmp['download'] = self.download_file(path + b['Key'])
                    tmp['time'] = b['LastModified']
                    data.append(tmp)
            else:
                pass
            if 'CommonPrefixes' in self.__oss.list_objects(Bucket=self.__Bucket, MaxKeys=100, Delimiter='/', Prefix=path):
                for i in self.__oss.list_objects(Bucket=self.__Bucket, MaxKeys=100, Delimiter='/', Prefix=path)['CommonPrefixes']:
                    if not i['Prefix']: continue
                    dir_dir=i['Prefix'].split('/')[-2]+'/'
                    dir_list.append(dir_dir)
            else:
                pass
            mlist = {}
            mlist['path'] = get.path
            mlist['list'] = data
            mlist['dir'] = dir_list
            return mlist
        except:
            mlist = {}
            if self.__oss:
                mlist['status']=True
            else:
                mlist['status']=False
            mlist['path'] = get.path
            mlist['list'] = data
            mlist['dir'] = dir_list
            return mlist

    def sync_date(self):
        public.ExecShell("ntpdate 0.asia.pool.ntp.org")

    def download_file(self, filename, Expired=300):
        if not self.__oss:
            self.set_cos()
            if self.__oss:
                return False
        try:
            response = self.__oss.get_presigned_download_url(
                Bucket=self.__Bucket,
                Key=filename
            )
            response = re.findall('([^?]*)?.*', response)[0]
            return response
        except:
            print(self.__error_msg)
            return None

    def get_path(self, path):
        if path == '/': path = '';
        if path[:1] == '/':
            path = path[1:]
            if path[-1:] != '/': path += '/';
        return path

    def delete_file(self, filename):
        if not self.__oss:
            self.set_cos()
            if self.__oss:
                return False
        try:
            response = self.__oss.delete_object(
                Bucket=self.__Bucket,
                Key=filename
            )
            return response
        except Exception as ex:
            self.__error_count += 1
            if self.__error_count < 2:
                self.sync_date()
                self.delete_file(filename)
            print(self.__error_msg)
            return None

    # 删除文件
    def remove_file(self, get):
        if not self.__oss:
            self.set_cos()
            if self.__oss:
                return False
        path = self.get_path(get.path)
        filename = path + get.filename
        self.delete_file(filename)
        return public.returnMsg(True, '删除文件成功!')

    # 备份网站
    def backupSite(self, name, count):
        # self.set_cos()
        # self.__conn();
        if not self.__oss:
            self.set_cos()
            if self.__oss:
                return False
        sql = db.Sql();
        path = sql.table('sites').where('name=?', (name,)).getField('path');
        startTime = time.time();
        if not path:
            endDate = time.strftime('%Y/%m/%d %X', time.localtime())
            log = "网站[" + name + "]不存在!"
            print("★[" + endDate + "] " + log)
            print("----------------------------------------------------------------------------")
            return;

        backup_path = sql.table('config').where("id=?", (1,)).getField('backup_path') + '/site';
        if not os.path.exists(backup_path): public.ExecShell("mkdir -p " + backup_path);

        filename = backup_path + "/Web_" + name + "_" + time.strftime('%Y%m%d_%H%M%S', time.localtime()) + '.tar.gz'
        public.ExecShell("cd " + os.path.dirname(path) + " && tar zcvf '" + filename + "' '" + os.path.basename(
            path) + "' > /dev/null")
        endDate = time.strftime('%Y/%m/%d %X', time.localtime())

        time.sleep(1)
        if not os.path.exists(filename):
            log = "网站[" + name + "]备份失败!"
            print("★[" + endDate + "] " + log)
            print("----------------------------------------------------------------------------")
            return;

        if self.__bucket_path != '': self.__bucket_path += name + '/';

        # 上传文件
        self.upload_file(filename);

        outTime = time.time() - startTime
        pid = sql.table('sites').where('name=?', (name,)).getField('id');
        sql.table('backup').add('type,name,pid,filename,addtime,size',
                                ('0', os.path.basename(filename), pid, 'alioss', endDate, os.path.getsize(filename)))
        log = "网站[" + name + "]已成功备份到腾讯云COS,用时[" + str(round(outTime, 2)) + "]秒";
        public.WriteLog('计划任务', log)
        print("★[" + endDate + "] " + log)
        print("|---保留最新的[" + count + "]份备份")
        print("|---文件名:" + os.path.basename(filename))

        # 清理本地文件
        public.ExecShell("rm -f " + filename)

        # 清理多余备份
        backups = sql.table('backup').where('type=? and pid=?', ('0', pid)).field('id,name,filename').select();

        num = len(backups) - int(count)
        if num > 0:
            for backup in backups:
                if os.path.exists(backup['filename']):
                    public.ExecShell("rm -f " + backup['filename']);
                self.delete_file(self.__bucket_path + backup['name']);
                sql.table('backup').where('id=?', (backup['id'],)).delete();
                num -= 1;
                print("|---已清理过期备份文件：" + backup['name'])
                if num < 1: break;
        return None
    # 备份数据库

    def backupDatabase(self, name, count):
        if not self.__oss:
            self.set_cos()
            if self.__oss:
                return False
        sql = db.Sql();
        path = sql.table('databases').where('name=?', (name,)).getField('path');
        startTime = time.time();
        if not path:
            endDate = time.strftime('%Y/%m/%d %X', time.localtime())
            log = "数据库[" + name + "]不存在!"
            print("★[" + endDate + "] " + log)
            print("----------------------------------------------------------------------------")
            return;

        backup_path = sql.table('config').where("id=?", (1,)).getField('backup_path') + '/database';
        if not os.path.exists(backup_path): public.ExecShell("mkdir -p " + backup_path);

        filename = backup_path + "/Db_" + name + "_" + time.strftime('%Y%m%d_%H%M%S', time.localtime()) + ".sql.gz"

        import re
        mysql_root = sql.table('config').where("id=?", (1,)).getField('mysql_root')
        mycnf = public.readFile('/etc/my.cnf');
        rep = "\[mysqldump\]\nuser=root"
        sea = "[mysqldump]\n"
        subStr = sea + "user=root\npassword=" + mysql_root + "\n";
        mycnf = mycnf.replace(sea, subStr)
        if len(mycnf) > 100:
            public.writeFile('/etc/my.cnf', mycnf);

        public.ExecShell(
            "/www/server/mysql/bin/mysqldump --opt --default-character-set=utf8 " + name + " | gzip > " + filename)

        if not os.path.exists(filename):
            endDate = time.strftime('%Y/%m/%d %X', time.localtime())
            log = "数据库[" + name + "]备份失败!"
            print("★[" + endDate + "] " + log)
            print("----------------------------------------------------------------------------")
            return;

        mycnf = public.readFile('/etc/my.cnf');
        mycnf = mycnf.replace(subStr, sea)
        if len(mycnf) > 100:
            public.writeFile('/etc/my.cnf', mycnf);

        # 上传
        if self.__bucket_path != '': self.__bucket_path += 'database/' + name + '/';
        self.upload_file(filename);

        endDate = time.strftime('%Y/%m/%d %X', time.localtime())
        outTime = time.time() - startTime
        pid = sql.table('databases').where('name=?', (name,)).getField('id');

        sql.table('backup').add('type,name,pid,filename,addtime,size',
                                (1, os.path.basename(filename), pid, 'alioss', endDate, os.path.getsize(filename)))
        log = "数据库[" + name + "]已成功备份到腾讯云COS,用时[" + str(round(outTime, 2)) + "]秒";
        public.WriteLog('计划任务', log)
        print("★[" + endDate + "] " + log)
        print("|---保留最新的[" + count + "]份备份")
        print("|---文件名:" + os.path.basename(filename))

        # 清理本地文件
        public.ExecShell("rm -f " + filename)

        # 清理多余备份
        backups = sql.table('backup').where('type=? and pid=?', ('1', pid)).field('id,name,filename').select();

        num = len(backups) - int(count)
        if num > 0:
            for backup in backups:
                if os.path.exists(backup['filename']):
                    public.ExecShell("rm -f " + backup['filename']);

                self.delete_file(self.__bucket_path + backup['name']);
                sql.table('backup').where('id=?', (backup['id'],)).delete();
                num -= 1;
                print("|---已清理过期备份文件：" + backup['name'])
                if num < 1: break;
        return None

        # 备份指定目录
    def backupPath(self, path, count):
        if not self.__oss:
            self.set_cos()
            if self.__oss:
                return False
        sql = db.Sql();
        startTime = time.time();
        if path[-1:] == '/': path = path[:-1]
        name = os.path.basename(path)
        backup_path = sql.table('config').where("id=?", (1,)).getField('backup_path') + '/path';
        if not os.path.exists(backup_path): os.makedirs(backup_path);
        filename = backup_path + "/Path_" + name + "_" + time.strftime('%Y%m%d_%H%M%S', time.localtime()) + '.tar.gz'
        os.system(
            "cd " + os.path.dirname(path) + " && tar zcvf '" + filename + "' '" + os.path.basename(path) + "' > /dev/null")

        endDate = time.strftime('%Y/%m/%d %X', time.localtime())
        if not os.path.exists(filename):
            log = u"目录[" + path + "]备份失败"
            print(u"★[" + endDate + "] " + log)
            print(u"----------------------------------------------------------------------------")
            return;

        # 上传文件
        if self.__bucket_path != '': self.__bucket_path += 'path/' + name + '/';
        self.upload_file(filename);
        outTime = time.time() - startTime
        sql.table('backup').add('type,name,pid,filename,addtime,size',
                                ('2', path, '0', filename, endDate, os.path.getsize(filename)))
        log = u"目录[" + path + "]备份成功,用时[" + str(round(outTime, 2)) + "]秒";
        public.WriteLog(u'计划任务', log)
        print(u"★[" + endDate + "] " + log)
        print(u"|---保留最新的[" + count + u"]份备份")
        print(u"|---文件名:" + filename)

        # 清理多余备份
        backups = sql.table('backup').where('type=? and pid=?', ('2', 0)).field('id,filename').select();

        # 清理本地文件
        if os.path.exists(filename): os.remove(filename)
        num = len(backups) - int(count)
        if num > 0:
            for backup in backups:
                if os.path.exists(backup['filename']): os.remove(backup['filename'])
                self.delete_file(self.__bucket_path + backup['filename']);
                sql.table('backup').where('id=?', (backup['id'],)).delete();
                num -= 1;
                print(u"|---已清理过期备份文件：" + backup['filename'])
                if num < 1: break;


    def backupSiteAll(self, save):
        if not self.__oss:
            self.set_cos()
            if self.__oss:
                return False
        self.__conn()
        sites = public.M('sites').field('name').select()
        for site in sites:
            self.backupSite(site['name'], save)


    def backupDatabaseAll(self, save):
        if not self.__oss:
            self.set_cos()
            if self.__oss:
                return False
        self.__conn()
        databases = public.M('databases').field('name').select()
        for database in databases:
            self.backupDatabase(database['name'], save)

    def set_cos(self):
        cfile = 'plugin/txcos/config.conf'
        fp = open(cfile, 'r')
        keys = fp.read().split('|')
        self.__secret_id = keys[0]
        self.__secret_key = keys[1]
        self.__region = keys[2]
        self.__Bucket = keys[3]
        self.__bucket_path = self.get_path(keys[4])
        try:
            config = CosConfig(Region=self.__region, SecretId=self.__secret_id, SecretKey=self.__secret_key, Token=None,Scheme='http', Timeout=1)
            self.__oss = CosS3Client(config)
        except:
            if self.__oss == None:
                time.sleep(1)
                self.__conn()
            return json.dumps(self.__error_msg)

    def get_lib(self):
        import json
        list={
            "name":"腾讯云COS",
            "type":"计划任务",
            "ps":"将网站或数据库打包备份到腾讯云COS对象存储空间,, <a class='link' href='https://portal.qiniu.com/signup?code=3liz7nbopjd5e' target='_blank'>点击申请</a>",
            "status":'false',
            "opt":"txcos",
            "module":"qcloud_cos",
            "script":"txcos",
            "help":"https://www.bt.cn/bbs/thread-17442-1-1.html",
            "SecretId":"SecretId|请输入SecretId|腾讯云COS的SecretId",
            "SecretKey":"SecretKey|请输入SecretKey|腾讯云COS  SecretKey",
            "region":"存储地区|请输入对象存储地区|例如 ap-chengdu",
            "Bucket":"存储名称|请输入绑定的存储名称",
            "check":["/usr/lib/python2.6/site-packages/qcloud_cos/cos_auth.py","/usr/lib/python2.7/site-packages/qcloud_cos/cos_auth.py"]
        }
        lib='/www/server/panel/data/libList.conf'
        lib_dic = json.loads(public.readFile(lib))
        for i in lib_dic:
            if list['name'] in i['name']:
                return True
            else:
                pass
        lib_dic.append(list)
        public.writeFile(lib, json.dumps(lib_dic))
        return lib_dic



if __name__ == "__main__":
    import json

    data = None
    q = txcos_main()
    type = sys.argv[1]
    if type == 'site':
        if sys.argv[2] == 'ALL':
            #q.set_cos()
            q.backupSiteAll(sys.argv[3])
        else:
            #q.set_cos()
            q.backupSite(sys.argv[2], sys.argv[3])
        exit()
    elif type == 'database':
        if sys.argv[2] == 'ALL':
            #q.set_cos()
            q.backupDatabaseAll(sys.argv[3])
        else:
            #q.set_cos()
            q.backupDatabase(sys.argv[2], sys.argv[3])
        exit()
    elif type == 'path':
        #q.set_cos()
        q.backupPath(sys.argv[2], sys.argv[3])
    elif type == 'upload':
        #q.set_cos()
        data = q.upload_file(sys.argv[2])
    elif type == 'download':
        data = q.download_file(sys.argv[2])
    elif type == 'get':
        data = q.get_files(sys.argv[2])
    elif type == 'list':
        #q.set_cos()
        data = q.get_list()
    elif type == 'delete_file':
        data = q.delete_file(sys.argv[2])
    elif type == 'lib':
        data = q.get_lib()
    else:
        data = 'ERROR: 参数不正确!'
    print(json.dumps(data))