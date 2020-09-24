# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 1249648969@qq.com
# |   主控   备份
# +---------------------------------------
import sys, os
if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
os.chdir('/www/server/panel')
if not 'class/' in sys.path:
    sys.path.insert(0,'class/')
import time,hashlib,sys,os,json,requests,re,public,random,string,panelMysql,downloadFile
python_bin=public.get_python_bin()
class backup_bak:
    _chek_site_file='/tmp/chekc_site.json'
    _check_database = '/www/server/panel/data/check_database.json'
    _check_site = '/www/server/panel/data/check_site_data.json'
    _chekc_path='/www/server/panel/data/check_path_data.json'
    _down_path='/www/server/panel/data/download_path_data.json'
    _check_database_data=[]
    _check_site_data=[]
    _check_path_data=[]
    _down_path_data=[]
    #备份所有站点的进度
    _check_all_site = '/www/server/panel/data/check_site_data_all.json'
    _check_site_all_data=[]
    #备份所有数据库的进度
    _check_all_date = '/www/server/panel/data/check_date_data_all.json'
    _check_date_all_data=[]
    def __init__(self):
        if not os.path.exists(self._check_all_site):
            ret = []
            public.writeFile(self._check_all_site, json.dumps(ret))
        else:
            ret = public.ReadFile(self._check_all_site)
            self._check_site_all_data = json.loads(ret)

        if not os.path.exists(self._check_all_date):
            ret = []
            public.writeFile(self._check_all_date, json.dumps(ret))
        else:
            ret = public.ReadFile(self._check_all_date)
            self._check_date_all_data = json.loads(ret)
        if not os.path.exists('/www/backup/site_backup'):
            public.ExecShell('mkdir /www/backup/site_backup -p')
        if not os.path.exists('/www/backup/database_backup'):
            public.ExecShell('mkdir /www/backup/database_backup')
        if not os.path.exists(self._check_database):
            ret = []
            public.writeFile(self._check_database, json.dumps(ret))
        else:
            ret = public.ReadFile(self._check_database)
            self._check_database_data = json.loads(ret)
        if not os.path.exists(self._check_site):
            ret = []
            public.writeFile(self._check_site, json.dumps(ret))
        else:
            ret = public.ReadFile(self._check_site)
            self._check_site_data = json.loads(ret)
        if not os.path.exists(self._chekc_path):
            ret = []
            public.writeFile(self._chekc_path, json.dumps(ret))
        else:
            ret = public.ReadFile(self._chekc_path)
            self._check_path_data = json.loads(ret)

        #下载所需要的
        if not os.path.exists(self._down_path):
            ret = []
            public.writeFile(self._down_path, json.dumps(ret))
        else:
            ret = public.ReadFile(self._down_path)
            self._down_path_data = json.loads(ret)


    #判断是否在_check_database_data 中
    def check_database_data(self,data,ret):
        if len(data)==0:return False
        for i in data:
            if int(i['id']) == int(ret['id']):
                return True
        else:
            return False

    def check_database_data2(self,data,ret):
        if len(data)==0:return False
        for i in data:
            if i['id'] == ret['id']:
                return True
        else:
            return False

    #写入_database_data到里面去
    def set_database_data(self,ret):
        if len(self._check_database_data) == 0:
            self._check_database_data.append(ret)
        else:
            if self.check_database_data(self._check_database_data,ret):
                for i in self._check_database_data:
                    if int(i['id'])==int(ret['id']):
                        i['name'] = ret['name']
                        i['path']=ret['path']
                        i['status']=ret['status']
            else:
                self._check_database_data.append(ret)
        public.writeFile(self._check_database, json.dumps(self._check_database_data))
        return True

    #写入_site_data到里面去
    def set_site_data(self,ret):
        if len(self._check_site_data) == 0:
            self._check_site_data.append(ret)
        else:
            if self.check_database_data(self._check_site_data,ret):
                for i in self._check_site_data:
                    if int(i['id']) == int(ret['id']):
                        i['name'] = ret['name']
                        i['path']=ret['path']
                        i['status']=ret['status']
            else:
                self._check_site_data.append(ret)
        public.writeFile(self._check_site, json.dumps(self._check_site_data))
        return True

    #写入_site_data到里面去
    def set_path_data(self,ret):
        if len(self._check_path_data) == 0:
            self._check_path_data.append(ret)
        else:
            if self.check_database_data2(self._check_path_data,ret):
                for i in self._check_path_data:
                    if i['id']==ret['id']:
                        i['name'] = ret['name']
                        i['path']=ret['path']
                        i['status']=ret['status']
            else:
                self._check_path_data.append(ret)
        public.writeFile(self._chekc_path, json.dumps(self._check_path_data))
        return True

    # 显示所有网站信息
    def get_sites(self,get):
        data= public.M('sites').field('id,name,path,status,ps,addtime,edate').select()
        for i in data:
            data2=self.GetSSL(i['name'])
            i['ssl']=data2['status']
            if data2['status']:
                i['time'] = data2['cert_data']
            else:
                i['time'] =False
        return data


    def get_databases(self,get):
        data= public.M('databases').field('id,name,username,password,accept,ps,addtime').select()
        return data

    # 是否跳转到https
    def IsToHttps(self, siteName):
        file = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf';
        conf = public.readFile(file);
        if conf:
            if conf.find('HTTP_TO_HTTPS_START') != -1: return True;
            if conf.find('$server_port !~ 443') != -1: return True;
        return False;

    # 取SSL状态
    def GetSSL(self, siteName):
        self.setupPath = '/www/server'
        path = os.path.join('/www/server/panel/vhost/cert/', siteName)
        if not os.path.isfile(os.path.join(path, "fullchain.pem")) and not os.path.isfile(os.path.join(path, "privkey.pem")):
            path = os.path.join('/etc/letsencrypt/live/', siteName)
        type = 0;
        if os.path.exists(path + '/README'):  type = 1;
        if os.path.exists(path + '/partnerOrderId'):  type = 2;
        csrpath = path + "/fullchain.pem";  # 生成证书路径
        keypath = path + "/privkey.pem";  # 密钥文件路径
        key = public.readFile(keypath);
        csr = public.readFile(csrpath);
        file = self.setupPath + '/panel/vhost/' + public.get_webserver() + '/' + siteName + '.conf';
        conf = public.readFile(file);
        keyText = 'SSLCertificateFile'
        if public.get_webserver() == 'nginx': keyText = 'ssl_certificate';
        status = True
        if not conf or conf.find(keyText) == -1:
            status = False
            type = -1
        toHttps = self.IsToHttps(siteName)
        id = public.M('sites').where("name=?", (siteName,)).getField('id')
        domains = public.M('domain').where("pid=?", (id,)).field('name').select()
        cert_data= {}
        if csr:
            cert_data = self.GetCertName(csrpath)
        email = public.M('users').where('id=?',(1,)).getField('email')
        if email == '287962566@qq.com': email = ''
        return {'status': status, 'cert_data':cert_data}

    #转换时间
    def strfToTime(self,sdate):
        import time
        return time.strftime('%Y-%m-%d',time.strptime(sdate,'%b %d %H:%M:%S %Y %Z'))

    #获取证书名称
    def GetCertName(self,certPath):
        try:
            openssl = '/usr/local/openssl/bin/openssl';
            if not os.path.exists(openssl): openssl = 'openssl';
            result = public.ExecShell(openssl + " x509 -in "+certPath+" -noout -subject -enddate -startdate -issuer")
            tmp = result[0].split("\n");
            data = {}
            data['subject'] = tmp[0].split('=')[-1]
            data['notAfter'] = self.strfToTime(tmp[1].split('=')[1])
            data['notBefore'] = self.strfToTime(tmp[2].split('=')[1])
            if tmp[3].find('O=') == -1:
                data['issuer'] = tmp[3].split('CN=')[-1]
            else:
                data['issuer'] = tmp[3].split('O=')[-1].split(',')[0]
            if data['issuer'].find('/') != -1: data['issuer'] = data['issuer'].split('/')[0];
            result = public.ExecShell(openssl + " x509 -in "+certPath+" -noout -text|grep DNS")
            data['dns'] = result[0].replace('DNS:','').replace(' ','').strip().split(',');
            return data;
        except:
            print(public.get_error_info())
            return None;


    # 显示所有网站信息
    def get_sites_or_ssl(self,get):
        data= public.M('sites').field('id,name,path,status,ps,addtime,edate').select()
        for i in data:
            i['ssl']=self.GetSSL(i['name'])
        return data


    #backup_database
    def backup_database(self,get):
        if not public.M('databases').where("name=?",(get.name,)).count():return public.returnMsg(False,'数据库不存在')
        id=public.M('databases').where("name=?", (get.name,)).getField('id')
        if not id:return public.returnMsg(False,'数据库不存在')
        if os.path.exists(self._chek_site_file):
            return public.returnMsg(False, '这个时间段中存在有运行任务,建议更换计划任务的时间备份')
        public.ExecShell( python_bin + ' /www/server/panel/class/backup_bak.py database %s &'%id)
        return public.returnMsg(True,'OK')

    # backup_database
    def backup_site(self, get):
        if not public.M('sites').where("name=?", (get.name,)).count(): return public.returnMsg(False, "网站不存在")
        id = public.M('sites').where('name=?',(get.name,)).getField('id')
        if not id:return public.returnMsg(False, "网站不存在")

        #监测是否存在任务
        if os.path.exists(self._chek_site_file):
            return public.returnMsg(False, '这个时间段中存在有运行任务,建议更换计划任务的时间备份')


        public.ExecShell(python_bin+ ' /www/server/panel/class/backup_bak.py sites %s &' % id)
        return public.returnMsg(True, 'OK')

    # backup_path
    def backup_path_data(self, get):
        if not os.path.exists(get.path):return public.returnMsg(False, "目录不存在")
        public.ExecShell(python_bin+ ' /www/server/panel/class/backup_bak.py path %s &' % get.path)
        return public.returnMsg(True, 'OK')

    #检测数据库执行错误
    def IsSqlError(self,mysqlMsg):
        mysqlMsg=str(mysqlMsg)
        if "MySQLdb" in mysqlMsg: return False
        if "2002," in mysqlMsg or '2003,' in mysqlMsg: return False
        if "using password:" in mysqlMsg: return False
        if "Connection refused" in mysqlMsg: return False
        if "1133" in mysqlMsg: return False
        if "libmysqlclient" in mysqlMsg:return False

    #配置
    def mypass(self,act,root):
        public.ExecShell("sed -i '/user=root/d' /etc/my.cnf")
        public.ExecShell("sed -i '/password=/d' /etc/my.cnf")
        if act:
            mycnf = public.readFile('/etc/my.cnf');
            rep = "\[mysqldump\]\nuser=root"
            sea = "[mysqldump]\n"
            subStr = sea + "user=root\npassword=\"" + root + "\"\n";
            mycnf = mycnf.replace(sea,subStr)
            if len(mycnf) > 100: public.writeFile('/etc/my.cnf',mycnf);

    def backup_database2(self,id):
        if not public.M('databases').where("id=?", (id,)).count():
            ret = {}
            ret['id'] = id
            ret['name'] = False
            ret['status'] = False
            ret['path'] = False
            ret['chekc']=False
            self.set_site_data(ret)
            return public.returnMsg(False, '数据库不存在')
        id=int(id)
        # 添加到chekc_database 中
        ret={}
        ret['id']=id
        ret['name']=public.M('databases').where("id=?", (id,)).getField('name')
        ret['status']=False
        ret['path']=False
        ret['chekc'] = True
        self.set_database_data(ret)
        if not os.path.exists(self._chek_site_file): public.ExecShell('touch %s' % self._chek_site_file)
        path=self.backup_database_data(id)
        os.remove(self._chek_site_file)

        ret['status'] = True
        ret['path'] = path
        self.set_database_data(ret)

    def backup_path_data2(self,path):
        id=''.join(random.sample(string.ascii_letters + string.digits, 4))
        if not os.path.exists(path):
            ret = {}
            ret['id'] = id
            ret['name'] = False
            ret['status'] = False
            ret['path'] = False
            ret['chekc']=False
            self.set_path_data(ret)
            return public.returnMsg(False, "目录不存在")
        # 添加到chekc_database 中
        ret={}
        ret['id']=id
        ret['name']=path
        ret['status']=False
        ret['path']=False
        ret['chekc'] = True
        self.set_path_data(ret)
        path2=self.backup_path(path)
        ret['status'] = True
        ret['path'] = path2
        self.set_path_data(ret)
        return True

    def backup_site2(self,id):
        if not public.M('sites').where("id=?", (id,)).count():
            ret = {}
            ret['id'] = id
            ret['name'] = False
            ret['status'] = False
            ret['path'] = False
            ret['chekc']=False
            self.set_site_data(ret)
            return public.returnMsg(False, "网站不存在")
        id=int(id)
        # 添加到chekc_database 中
        ret={}
        ret['id']=id
        ret['name']=public.M('sites').where("id=?", (id,)).getField('name')
        ret['status']=False
        ret['path']=False
        ret['chekc'] = True
        self.set_site_data(ret)
        if not os.path.exists(self._chek_site_file): public.ExecShell('touch %s' % self._chek_site_file)
        path=self.backup_site_data(id)
        os.remove(self._chek_site_file)
        ret['status'] = True
        ret['path'] = path
        self.set_site_data(ret)
        return True

    #备份数据库
    def backup_database_data(self,id):
        result = panelMysql.panelMysql().execute("show databases")
        isError =self.IsSqlError(result)
        if isError: return isError
        name = public.M('databases').where("id=?", (id,)).getField('name')
        root = public.M('config').where('id=?', (1,)).getField('mysql_root')
        if not os.path.exists('/www/server/panel/BTPanel/static' + '/database'): public.ExecShell(
            'mkdir -p ' + '/www/server/panel/BTPanel/static' + '/database');
        self.mypass(True, root)
        path_id = ''.join(random.sample(string.ascii_letters + string.digits, 20))
        fileName = path_id+'DATA'+name + '_' + time.strftime('%Y%m%d_%H%M%S', time.localtime()) + '.sql.gz'
        backupName = '/www/server/panel/BTPanel/static'+ '/database/' + fileName
        public.ExecShell("/www/server/mysql/bin/mysqldump --default-character-set=" + public.get_database_character(
            name) + " --force --opt \"" + name + "\" | gzip > " + backupName)
        if not os.path.exists(backupName): return public.returnMsg(False, 'BACKUP_ERROR')
        self.mypass(False, root)
        sql = public.M('backup')
        addTime = time.strftime('%Y-%m-%d %X', time.localtime())
        sql.add('type,name,pid,filename,size,addtime', (1, fileName, id, backupName, 0, addTime))
        public.WriteLog("TYPE_DATABASE", "DATABASE_BACKUP_SUCCESS", (name,))
        return backupName

    #备份网站
    def backup_site_data(self,id):
        path_id = ''.join(random.sample(string.ascii_letters + string.digits, 20))
        find = public.M('sites').where("id=?",(id,)).field('name,path,id').find()
        import time
        fileName = path_id+'WEB'+find['name']+'_'+time.strftime('%Y%m%d_%H%M%S',time.localtime())+'.zip'
        backupPath = '/www/server/panel/BTPanel/static'+ '/site'
        zipName = backupPath + '/'+fileName
        if not (os.path.exists(backupPath)): os.makedirs(backupPath)
        tmps = '/tmp/panelExec.log'
        execStr = "cd '" + find['path'] + "' && zip '" + zipName + "' -x .user.ini -r ./ > " + tmps + " 2>&1"
        public.ExecShell(execStr)
        sql = public.M('backup').add('type,name,pid,filename,size,addtime',(0,fileName,find['id'],zipName,0,public.getDate()))
        public.WriteLog('TYPE_SITE', 'SITE_BACKUP_SUCCESS',(find['name'],))
        return zipName

    #备份目录
    def backup_path(self,path):
        import time
        path_id = ''.join(random.sample(string.ascii_letters + string.digits, 20))
        fileName =path_id+ path.replace('/','_')+'_'+time.strftime('%Y%m%d_%H%M%S',time.localtime())+'.zip'
        backupPath = '/www/server/panel/BTPanel/static'+ '/path'
        zipName = backupPath + '/'+fileName
        if not (os.path.exists(backupPath)): os.makedirs(backupPath)
        tmps = '/tmp/panelExec.log'
        execStr = "cd '" + path + "' && zip '" + zipName + "' -x .user.ini -r ./ > " + tmps + " 2>&1"
        public.ExecShell(execStr)
        public.WriteLog('文件管理	', '备份文件夹【%s】成功'%path)
        print(zipName)
        return zipName

    #查看数据备份进度
    def get_database_progress(self,get):
        id=get.id
        for i in self._check_database_data:
            if int(i['id'])==int(id):
                return public.returnMsg(True, i)
        else:
            return public.returnMsg(False,'False')

    #查看网站备份进度
    def get_site_progress(self,get):
        id=get.id
        for i in self._check_site_data:
            if int(i['id']) == int(id):
                return public.returnMsg(True, i)
        else:
            return public.returnMsg(False, 'False')

    #查看网站备份进度
    def get_path_progress(self,get):
        id=get.id
        for i in self._check_path_data:
            if i['id'] == id:
                return public.returnMsg(True, i)
        else:
            return public.returnMsg(False, 'False')

    ###########文件下载
    # 判断是否在_check_database_data 中
    def check_down_data(self, data, ret):
        if len(data) == 0: return False
        for i in data:
            if i['id'] == ret['id'] and i['type']==ret['type']:
                return True
        else:
            return False

    def set_down_data(self, ret):
        if len(self._down_path_data) == 0:
            self._down_path_data.append(ret)
        else:
            if self.check_database_data(self._down_path_data, ret):
                for i in self._down_path_data:
                    if i['id'] == ret['id'] and i['type']==ret['type']:
                        i['name'] = ret['name']
                        i['url']=ret['url']
                        i['filename']=ret['filename']
                        i['status'] = ret['status']
            else:
                self._down_path_data.append(ret)
        public.writeFile(self._down_path, json.dumps(self._down_path_data))
        return True

    #下载对方的备份文件
    def download_path(self,get):
        filename=get.filename
        ret = {}
        ret['type']=get.type
        ret['id']=get.id
        ret['name']=get.name
        ret['url']=get.url
        ret['filename']=filename
        ret['status']=False
        self.set_down_data(ret)
        print(python_bin+ ' /www/server/panel/class/backup_bak.py down  %s %s %s %s %s &'%(get.url,filename,get.type,get.id,get.name))
        public.ExecShell(python_bin+ ' /www/server/panel/class/backup_bak.py down  %s %s %s %s %s &'%(get.url,filename,get.type,get.id,get.name))
        return True

    def down2(self,url,filename,type,id,name):
        self.down(url,filename)
        ret={}
        ret['url'] = url
        ret['type']=type
        ret['id']=id
        ret['name']=name
        ret['filename'] = filename
        ret['status']=True
        self.set_down_data(ret)

    #测试下载
    def down(self,url,filename):
        print(url)
        print("下载到%s"%filename)
        down=downloadFile.downloadFile()
        ret=down.DownloadFile(url,filename)
        print('下载完成')
        return True

    #查看网站备份进度
    def get_down_progress(self,get):
        id=get.id
        type=get.type
        for i in self._down_path_data:
            if i['id'] == id and i['type']==type:
                return public.returnMsg(True, i)
        else:
            return public.returnMsg(False, 'False')

    # backup_database
    def backup_site_all(self, get):
        #监测是否存在任务
        if os.path.exists(self._chek_site_file):
            return public.returnMsg(False, '这个时间段中存在有运行任务,建议更换计划任务的时间备份')

        public.ExecShell(python_bin+ ' /www/server/panel/class/backup_bak.py sites_ALL 11 &')
        return public.returnMsg(True, 'OK')

    def set_backup_all(self):
        data = public.M('sites').field('id,name,path,status,ps,addtime,edate').select()
        site_list = []
        #进度格式 总数量 当前数量  和返回的结果
        jindu={}
        jindu['start_count']=len(data)
        jindu['end_count']=0
        jindu['resulit']=site_list
        public.writeFile(self._check_all_site, json.dumps(jindu))
        if not os.path.exists(self._chek_site_file): public.ExecShell('touch %s' % self._chek_site_file)
        for i in data:
            path = self.backup_site_data(i['id'])
            if path:
                resulit = {}
                resulit['id'] = i['id']
                resulit['path'] = path
                resulit['type'] = 'sites'
                resulit['name']=i['name']
                jindu['resulit'].append(resulit)
            jindu['end_count'] +=1
            print(jindu)
            public.writeFile(self._check_all_site, json.dumps(jindu))
        os.remove(self._chek_site_file)
        return site_list

    #查看网站备份进度
    def get_all_site_progress(self,get):
        return self._check_site_all_data

    # backup_database
    def backup_date_all(self, get):
        if os.path.exists(self._chek_site_file):
            return public.returnMsg(False, '这个时间段中存在有运行任务,建议更换计划任务的时间备份')
        public.ExecShell(python_bin+ ' /www/server/panel/class/backup_bak.py database_ALL 11 &')
        return public.returnMsg(True, 'OK')

    def backup_all_database(self):
        data = public.M('databases').field('id,name,username,password,accept,ps,addtime').select()
        site_list = []
        #进度格式 总数量 当前数量  和返回的结果
        jindu={}
        jindu['start_count']=len(data)
        jindu['end_count']=0
        jindu['resulit']=site_list
        public.writeFile(self._check_all_date, json.dumps(jindu))
        if not os.path.exists(self._chek_site_file): public.ExecShell('touch %s' % self._chek_site_file)
        for i in data:
            path = self.backup_database_data(i['id'])
            if path:
                resulit = {}
                resulit['id'] = i['id']
                resulit['path'] = path
                resulit['type'] = 'sites'
                resulit['name'] = i['name']
                jindu['resulit'].append(resulit)
            jindu['end_count'] +=1
            print(jindu)
            public.writeFile(self._check_all_date, json.dumps(jindu))
        os.remove(self._chek_site_file)
        return site_list

    #查看网站备份进度
    def get_all_date_progress(self,get):
        return self._check_date_all_data

if __name__ == '__main__':
    p = backup_bak()
    ret = sys.argv[1]
    type = sys.argv[2]
    if ret =='sites':
        p.backup_site2(type)
    elif ret=='sites_ALL':
        p.set_backup_all()
    elif ret=='database_ALL':
        p.backup_all_database()
    elif ret=='database':
        p.backup_database2(type)
    elif ret=='path':
        p.backup_path_data2(type)
    elif ret=='down':
        filename = sys.argv[3]
        down_type=sys.argv[4]
        down_id=sys.argv[5]
        down_name=sys.argv[6]
        p.down2(type,filename,down_type,down_id,down_name)

