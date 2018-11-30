#!/usr/bin/python
# coding: utf-8
# (=.= )~[.]=~~~
# 宝塔Linux面板环境备份/还原工具
# Author: 1249648969@qq.com
#
import sys, os
if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
os.chdir('/www/server/panel')
sys.path.append("class/")
import public, time, json, re,zipfile,firewalls,random,db

def M(table,type='system2'):
   import db
   sql = db.Sql()
   sql.dbfile(type)
   return sql.table(table);


class mobj: port = ps = path = type =''
class backup_main:
    __time_out = 'Panel_Bak_'+time.strftime('%Y%m%d_%H%M%S',time.localtime())
    __path = '/www/server/backup/panelBackup'
    __reduction_path = '/www/server/backup/ReduCtion'
    __Disposable_path = '/www/server/backup/Disposable'
    __backup_path = None

    # 初始化目录
    def __init__(self):

        if not os.path.exists(self.__path):
            os.system('mkdir -p ' + self.__path)

        self.__backup_path = '/%s/%s' % (self.__path, self.__time_out)
        if not self.__backup_path:
            if os.path.exists(self.__backup_path):
                os.system('mkdri -p %s' % self.__backup_path)

        if not os.path.exists(self.__reduction_path):
            os.system('mkdir -p ' + self.__reduction_path)

        if not os.path.exists(self.__Disposable_path):
            os.system('mkdir -p ' + self.__Disposable_path)

    # 构造system.db
    def M(table):
        sql = db.Sql()
        sql.dbfile('system2')
        return sql.table(table)

    # 字节单位转换
    def ToSize(self, size):
        ds = ['b', 'KB', 'MB', 'GB', 'TB']
        for d in ds:
            if int(size) < 1024: return "%.2f%s" % (size , d)
            size = size / 1024
        return '0b'

    # 备份日志
    def BackupLog(self, isLog=None):
        data = public.M('logs').field('type,log,addtime').select()
        if len(data) >= 1:
            backupLog = self.__backup_path + '/log.json'
            print(backupLog)
            os.system('mkdir -p  %s' % self.__backup_path)
            os.mknod(backupLog)
            public.writeFile(backupLog, json.dumps(data))
            print ('备份完成，共' + str(len(data)) + '条日志!')
            return backupLog

    # 网站信息
    def BackupSite(self):
        data = {}
        data['site'] = public.M('sites').field('id,name,path,status,ps,addtime').select()
        data['domain'] = public.M('domain').field('pid,name,port,addtime').select()
        if len(data) >= 1:
            backupLog = self.__backup_path + '/site.json'
            print(backupLog)
            os.system('mkdir -p  %s' % self.__backup_path)
            os.mknod(backupLog)
            public.writeFile(backupLog, json.dumps(data))
            print ('备份完成，共' + str(len(data)) + '条日志!')
            return data

    # 备份面板FTP
    def RePanelFtp(self):
        data = public.M('ftps').field('name,password,path,status,ps,addtime').select()
        if len(data) >= 1:
            backupLog = self.__backup_path + '/ftp.json'
            print(backupLog)
            os.system('mkdir -p  %s' % self.__backup_path)
            os.mknod(backupLog)
            public.writeFile(backupLog, json.dumps(data), 'w+')
            print ('备份完成，共' + str(len(data)) + '条日志!')
            return backupLog

    # 备份防火墙
    def RePanelFrewall(self):
        data = public.M('firewall').field('port,ps,addtime').select()
        if len(data) >= 1:
            backupLog = self.__backup_path + '/firewall.json'
            print(backupLog)
            os.system('touch %s' % backupLog)
            public.writeFile(backupLog, json.dumps(data))
            print ('备份完成，共' + str(len(data)) + '条日志!')
            return backupLog

    # 备份配置文件
    def BackupSiteConfig(self, name):
        print(name)
        bt_conf = self.__backup_path + '/' + name + '/bt_conf'
        os.system('mkdir -p ' + bt_conf + '/ssl')
        print("备份Nginx配置文件")
        # 备份Nginx配置文件
        nginxConf = bt_conf + '/nginx.conf'
        panelNginxConf = '/www/server/panel/vhost/nginx/' + name + '.conf'
        if os.path.exists(panelNginxConf):
            conf = public.readFile(panelNginxConf).replace(' default_server', '')
            public.writeFile(nginxConf, conf)

        # 备份Nginx伪静态文件
        nginxRewrite = bt_conf + '/rewrite.conf'
        panelNginxRewrite = '/www/server/panel/vhost/rewrite/' + name + '.conf'
        if os.path.exists(panelNginxRewrite):
            conf = public.readFile(panelNginxRewrite)
            public.writeFile(nginxRewrite, conf)

        # 备份子目录伪静态规则
        try:
            panelRewritePath = '/www/server/panel/vhost/rewrite'
            rs = os.listdir(panelRewritePath)
            for r in rs:
                if r.find(name + '_') == -1: continue
                nginxRewrite = bt_conf + '/rewrite_' + r.split('_')[1]
                conf = public.readFile(panelRewritePath + '/' + r)
                public.writeFile(nginxRewrite, conf)
        except:
            pass

        # 备份apache配置文件
        httpdConf = bt_conf + '/apache.conf'
        panelHttpdConf = '/www/server/panel/vhost/apache/' + name + '.conf'
        if os.path.exists(panelHttpdConf):
            conf = public.readFile(panelHttpdConf)
            public.writeFile(httpdConf, conf)

        # 备份证书文件
        sslSrcPath = bt_conf + '/ssl/'
        sslDstPath = '/etc/letsencrypt/live/' + name + '/'
        sslFiles = ['privkey.pem', 'fullchain.pem', 'partnerOrderId', 'README']
        for sslFile in sslFiles:
            if os.path.exists(sslDstPath + sslFile):
                conf = public.readFile(sslDstPath + sslFile)
                public.writeFile(sslSrcPath + sslFile, conf)
        return True

    # 备份监控日志功能
    def BackupSystem(self):
        db_path='/www/server/panel/data/'
        db_name=db_path+'system.db'
        if os.path.exists(db_name):
            public.ExecShell('cp -p %s %s'%(db_name,self.__backup_path))
            if os.path.exists(self.__backup_path + '/system.db'):
                return True

    # 备份环境入口
    def Backup_all(self,get):
        self.BackupLog()
        self.RePanelFtp()
        self.RePanelFrewall()
        self.BackupSystem()
        data = self.BackupSite()
        print(data)
        if data['site']:
            if len(data['site']) >=1:
                for i in data['site']:
                    print(i['name'])
                    self.BackupSiteConfig(i['name'])
        os.system('cd ' + self.__path + ' &&  zip -r %s.zip %s' % (self.__time_out, self.__backup_path))
        zip_path = self.__backup_path + '.zip'
        os.system('rm -rf %s' % self.__backup_path)
        return zip_path


    # 查看已经备份的文件
    def GetBuckup(self, get):
        clearPath = [{'path': '/www/server/backup/panelBackup', 'find': 'zip'}]
        total = count = 0
        ret = []
        for c in clearPath:
            if os.path.exists(c['path']):
                for d in os.listdir(c['path']):
                    print(c)
                    if d.find('zip') == -1: continue
                    filename = c['path'] + '/' + d
                    # print(filename)
                    fsize = os.path.getsize(filename)
                    ret_size = {}
                    ret_size['name'] = filename
                    time1 = os.path.getmtime(filename)
                    # c2 = time.localtime(time1)
                    ret_size['time'] = int(time1)
                    ret_size['filename'] = os.path.basename(filename)
                    ret_size['download'] = '/download?filename=' + filename
                    ret_size['size'] = self.ToSize(int(fsize))
                    ret.append(ret_size)

        ret = sorted(ret,key=lambda x:x['time'],reverse=True)
        return ret

    # 上传接口
    def UploadFile(self, get):
        return '/files?action=UploadFile&path=' + self.__Disposable_path + '&codeing=byte'

    # 解压文件
    def Decompression(self, get):
        clearPath = [{'path': self.__Disposable_path, 'find': 'zip'}]
        for c in clearPath:
            if os.path.exists(c['path']):
                for d in os.listdir(c['path']):
                    if d.find(c['find']) == -1: continue
                    filename = c['path'] + '/' + d
                    path = d.replace('.zip', '')
                    print(filename)
                    if os.path.exists(self.__reduction_path + '/backup/panelBackup/' + path):
                        public.ExecShell('rm -rf %s' % filename)
                        return public.returnMsg(True, "已经存在")
                    print(self.__reduction_path + '/backup/panelBackup/' + path)
                    f = zipfile.ZipFile(filename, 'r')
                    for file in f.namelist():
                        f.extract(file, self.__reduction_path)
                    backup_path = self.__reduction_path + '/backup/panelBackup/' + path
                    if os.path.exists(backup_path):
                        os.system('rm -rf %s/*' % self.__Disposable_path)
                        get = mobj()
                        get.path = str(path)
                        get.type = get.type
                        ret=self.ImportData(get)
                        return ret
                    else:
                        os.system('rm -rf %s/*' % self.__Disposable_path)
                        return public.returnMsg(False, "解压失败")
        os.system('rm -rf %s/*' % self.__Disposable_path)
        return public.returnMsg(False, "解压失败")

    def GetBackupSite(self, get):
        clearPath = [{'path': '/www/server/backup/ReduCtion/backup/panelBackup', 'find': 'zip'}]
        total = count = 0
        ret = []
        for c in clearPath:
            if os.path.exists(c['path']):
                for d in os.listdir(c['path']):
                    filename = c['path'] + '/' + d
                    print(filename)
                    fsize = os.path.getsize(filename)
                    ret_size = {}
                    ret_size['name'] = filename
                    time1 = os.path.getmtime(filename)
                    c2 = time.localtime(time1)
                    ret_size['time'] = int(time1)
                    ret_size['filename'] = os.path.basename(filename)
                    ret_size['download'] = '/download?filename=' + filename
                    ret_size['size'] = public.ExecShell('du -sh  %s' % filename)[0].split()[0]
                    ret.append(ret_size)
        ret = sorted(ret, key=lambda x: x['time'], reverse=True)
        return ret

    # 删除文件
    def DelFile(self, get):
        path = get.filename
        name_path = '/www/server/backup/panelBackup/' + path
        if os.path.exists(name_path):
            os.system('rm -rf %s' % name_path)
        return public.returnMsg(True, "删除成功")


    # 删除文件
    def DelFile2(self, get):
        path = get.filename
        name_path = '/www/server/backup/ReduCtion/backup/panelBackup/' + path
        if os.path.exists(name_path):
            os.system('rm -rf %s' % name_path)
        return public.returnMsg(True, "删除成功")

    # 从本地导入文件
    def LocalImport(self,get):
        # 本地参数加一个type=local
        path=get.path
        type=get.type
        path=self.__path+'/'+path
        if os.path.exists(path):
            os.system('cp -p %s %s' %(path,self.__Disposable_path))
            ret2=self.Decompression(get)
            if ret2:
                return ret2
        else:
            return public.returnMsg(False,'参数错误')

    # 导入入口
    def ImportData(self,get):
        path=get.path
        type=get.type
        path = '/www/server/backup/ReduCtion/backup/panelBackup/' + path
        if os.path.exists(path):
            log=self.RecoveryPanelLog(path)
            fire=self.RecoveryFirewalld(path)
            ftp=self.RecoveryFtp(path)
            site=self.RecoverySite(path)
            system=self.Recoverysystem(path)
            #os.system('rm -rf %s' % path)
            ret={'log':log,'firewalld':fire,'ftp':ftp,'site':site,'plugin':True,'system':system}
            if ret:
                if type!='local':
                    path='/www/server/backup/ReduCtion/backup/panelBackup/'
                    os.system('rm -rf %s'%path)
            return public.returnMsg(True, ret)
        else:
            return public.returnMsg(False, "导入失败")

    #恢复系统监控日志
    def Recoverysystem(self,path):
        log_path = path + '/system.db'
        # 零时的system.db
        temporary_log='/www/server/panel/data/system2.db'
        system_path='/www/server/panel/data/system.db'
        if os.path.exists(temporary_log):
            public.ExecShell('rm -rf %s'%temporary_log)
        public.ExecShell('cp -p %s %s' % (log_path, temporary_log))
        if os.path.exists(system_path):
            if os.path.getsize(temporary_log) <= 10000: return False
            if os.path.getsize(system_path)<=10000 and os.path.getsize(temporary_log) > 10000:
                public.ExecShell('rm -rf %s && mv %s %s '%(system_path,temporary_log,system_path))
                return True
            else:
                if os.path.exists(temporary_log):
                    sql="select * from cpuio order by id DESC limit 1;"
                    # 判断是是否是同机器
                    try:
                        ret=M('cpuio').query(sql,())
                        ret2=M('cpuio',type='system').where('id=?', (ret,)).select()
                        if ret[0][0][-1]==ret2[0][-1]:
                            return True
                        # 不是同机器
                        else:
                            # 当机器的时间点小于备份时
                            ret2 = M('cpuio',type='system').query(sql,())
                            if ret[0][0][-1] > ret2[0][-1]:
                                public.ExecShell('rm -rf %s && mv %s %s ' % (system_path, temporary_log, system_path))
                            else:
                                return True
                    except:
                        return True
    # 恢复日志
    def RecoveryPanelLog(self, path):
        log_path = path + '/log.json'
        if os.path.exists(log_path):
            print(log_path)
            log_data = json.loads(public.ReadFile(log_path))
            dbsql = public.M('logs')
            if len(log_data)>=1:
                for i in log_data:
                    dbsql.addAll('type,log,addtime', (i['type'], i['log'], i['addtime']))
                dbsql.commit()
                return True

    # 恢复防火墙配置
    def RecoveryFirewalld(self, path):
        log_path = path + '/firewall.json'
        ret=[]
        if os.path.exists(log_path):
            log_data = json.loads(public.ReadFile(log_path))
            if len(log_data) >= 1:
                for i in log_data:
                    ftpinfo = {}
                    if public.M('firewall').where('port=?', (i['port'],)).count():
                        ftpinfo['port'] = i['port']
                        ftpinfo['status'] = False
                        ret.append(ftpinfo)
                        continue
                    print('插入防火墙')
                    ftpinfo['port'] = i['port']
                    ftpinfo['status'] = True
                    ret.append(ftpinfo)
                    fs = firewalls.firewalls()
                    get = mobj()
                    get.port = str(i['port'])
                    get.ps = str(i['ps'])
                    fs.AddAcceptPort(get)
                    print(ret)
                return ret
        else:
            return False

    # 恢复FTP数据
    def RecoveryFtp(self, path):
        ret=[]
        log_path = path + '/ftp.json'
        print('恢复FTP')
        if os.path.exists(log_path):
            log_data = json.loads(public.ReadFile(log_path))
            if len(log_data)>=1:
                for i in log_data:
                    ftpinfo = {}
                    if public.M('ftps').where('name=?', (i['name'],)).count():
                        ftpinfo['ftp_name']=i['name']
                        ftpinfo['status']=False
                        ret.append(ftpinfo)
                        continue
                    ftpinfo['ftp_name'] = i['name']
                    ftpinfo['status'] = True
                    ret.append(ftpinfo)
                    public.M('ftps').add('status,ps,name,addtime,path,password',(i['status'], i['ps'], i['name'], i['addtime'], i['path'], i['password']))
                    public.ExecShell('/www/server/pure-ftpd/bin/pure-pw useradd ' \
                                     + i['name'] + ' -u www -d ' + i['path'] + \
                                     '<<EOF \n' + i['password'] + '\n' + i['password'] + '\nEOF')
                    public.ExecShell('/www/server/pure-ftpd/bin/pure-pw mkdb /www/server/pure-ftpd/etc/pureftpd.pdb')
                return ret
            else:
                return ret
        else:
            return False


    # 恢复网站和配置文件信息
    def RecoverySite(self, path):
        ret=[]
        site_path = path + '/site.json'
        if os.path.exists(site_path):
            site_data = json.loads(public.ReadFile(site_path))

            if len(site_data['site']) >= 1:
                for i in site_data['site']:
                    ftpinfo = {}
                    if public.M('sites').where('name=?', (i['name'],)).count():
                        ftpinfo['site_name'] = i['name']
                        ftpinfo['status'] = False
                        ret.append(ftpinfo)
                        continue
                    ftpinfo['site_name'] = i['name']
                    ftpinfo['status'] = True
                    ret.append(ftpinfo)
                    data = public.M('sites').add('name,path,status,ps,addtime',(i['name'], i['path'], i['status'], i['ps'], i['addtime']))
                    pid_data = public.M('sites').where('name=?', (i['name'],)).field('id').select()[0]['id']
                    for i2 in site_data['domain']:
                        if i['id'] == i2['pid']:
                            public.M('domain').add('pid,name,port,addtime',(pid_data, i2['name'], i2['port'], i2['addtime']))
                            self.RecoverySSl(path, i['name'])
                return ret
            else:
                return ret
        else:
            return False

    # 恢复站点伪静态SSl
    def RecoverySSl(self, path, site):
        print("恢复站点伪静态SSl")
        ssl_path = path + '/' + site
        nginxConf = ssl_path + '/bt_conf/nginx.conf'
        panelNginxConf = '/www/server/panel/vhost/nginx/' + site + '.conf'
        if os.path.exists(nginxConf):
            conf = public.readFile(nginxConf)
            public.writeFile(panelNginxConf, conf)
        # 恢复nginx伪静态文件
        nginxRewrite = ssl_path + '/bt_conf/rewrite.conf'
        panelNginxRewrite = '/www/server/panel/vhost/rewrite/' + site + '.conf'
        if os.path.exists(nginxRewrite):
            conf = public.readFile(nginxRewrite)
            public.writeFile(panelNginxRewrite, conf)
        # 恢复子目录伪静态规则
        try:
            backupRewrite = ssl_path + '/bt_conf'
            rs = os.listdir(backupRewrite)
            for r in rs:
                if r.find('rewrite_') == -1: continue
                nginxRewrite = '/www/server/panel/vhost/rewrite/' + site + '_' + r.split('_')[1]
                conf = public.readFile(backupRewrite + '/' + r)
                public.writeFile(nginxRewrite, conf)
        except:
            pass
        # 恢复apache配置文件
        httpdConf = path + '/bt_conf/apache.conf'
        panelHttpdConf = '/www/server/panel/vhost/apache/' + site + '.conf'
        if os.path.exists(httpdConf):
            conf = public.readFile(httpdConf)
            public.writeFile(panelHttpdConf, conf)

        # 恢复证书文件
        sslSrcPath = path + '/bt_conf/ssl/'
        sslDstPath = '/etc/letsencrypt/live/' + site + '/'
        os.system('mkdir -p ' + sslDstPath)
        sslFiles = ['privkey.pem', 'fullchain.pem', 'partnerOrderId', 'README']
        for sslFile in sslFiles:
            if os.path.exists(sslSrcPath + sslFile):
                conf = public.readFile(sslSrcPath + sslFile)
                public.writeFile(sslDstPath + sslFile, conf)
        public.serviceReload()
        return True
