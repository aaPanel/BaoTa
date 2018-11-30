#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 x3
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2017 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <2879625666@qq.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   自动部署网站
#+--------------------------------------------------------------------

import public,json,os,time,sys
from BTPanel import session
class obj: id=0;
class deployment_main:
    __setupPath = 'plugin/deployment';
    __panelPath = '/www/server/panel';
    logPath = 'plugin/deployment/speed.json'
    timeoutCount = 0;
    oldTime = 0;
    
    #获取列表
    def GetList(self,get):
        self.GetCloudList(get);
        jsonFile = self.__setupPath + '/list.json';
        if not os.path.exists(jsonFile): return public.returnMsg(False,'配置文件不存在!');
        data = {}
        data = json.loads(public.readFile(jsonFile));
            
        if not hasattr(get,'type'): 
            get.type = 0;
        else:
            get.type = int(get.type)
        if not hasattr(get,'search'): 
            search = None
            m = 0
        else:
            search = get.search.encode('utf-8').lower();
            m = 1
            
        tmp = [];
        for d in data:
            i=0;
            if get.type > 0:
                if get.type == d['type']: i+=1
            else:
                i+=1
            if search:
                if d['name'].lower().find(search) != -1: i+=1;
                if d['title'].lower().find(search) != -1: i+=1;
                if get.type > 0 and get.type != d['type']: i -= 1;
            if i>m:tmp.append(d);
            
        data = tmp;
        result = {}
        result['data'] = data;
        jsonFile = self.__setupPath + '/type.json';
        if not os.path.exists(jsonFile): self.GetCloudList(get);
        result['type'] = json.loads(public.readFile(jsonFile));
        return result;
    
    #获取插件列表
    def GetDepList(self,get):
        jsonFile = self.__setupPath + '/list.json';
        if not os.path.exists(jsonFile): return public.returnMsg(False,'配置文件不存在!');
        data = {}
        data = json.loads(public.readFile(jsonFile));
        return data;
        
    
    #从云端获取列表
    def GetCloudList(self,get):
        try:
            if not 'package' in session:
                downloadUrl = public.get_url() + '/install/plugin/deployment/package.json';
                tmp = json.loads(public.httpGet(downloadUrl));
                if not tmp: return public.returnMsg(False,'从云端获取失败!');
                jsonFile = self.__setupPath + '/list.json';
                public.writeFile(jsonFile,json.dumps(tmp));
                
                downloadUrl = public.get_url() + '/install/plugin/deployment/type.json';
                tmp = json.loads(public.httpGet(downloadUrl));
                if not tmp: return public.returnMsg(False,'从云端获取失败!');
                jsonFile = self.__setupPath + '/type.json';
                public.writeFile(jsonFile,json.dumps(tmp));
                
                session['package'] = True
                return public.returnMsg(True,'更新成功!');
            return public.returnMsg(True,'无需更新!');
        except:
            return public.returnMsg(False,'从云端获取失败!');
        
        
    
    #添加程序包
    def AddPackage(self,get):
        jsonFile = self.__setupPath + '/list.json';
        if not os.path.exists(jsonFile): return public.returnMsg(False,'配置文件不存在!');
        
        data = {}
        data = json.loads(public.readFile(jsonFile));
        for d in data:
            if d['name'] == get.dname: return public.returnMsg(False,'您要添加的程序标识已存在!');
            if d['title'] == get.title: return public.returnMsg(False,'您要添加的程序名称已存在!');
        
        if hasattr(get,'rewrite'): get.rewrite = True;
        
        pinfo = {}
        pinfo['name'] = get.dname;
        pinfo['title'] = get.title;
        pinfo['version'] = get.version;
        pinfo['md5'] = get.md5;
        pinfo['rewrite'] = get.rewrite;
        pinfo['php'] = get.php;
        pinfo['ps'] = get.ps;
        pinfo['shell'] = get.shell;
        pinfo['download'] = get.download;
        data.append(pinfo);
        public.writeFile(jsonFile,json.dumps(data));
        return public.returnMsg(True,'添加成功!');
    
    #删除程序包
    def DelPackage(self,get):
        jsonFile = self.__setupPath + '/list.json';
        if not os.path.exists(jsonFile): return public.returnMsg(False,'配置文件不存在!');
        
        data = {}
        data = json.loads(public.readFile(jsonFile));
        
        tmp = [];
        for d in data:
            if d['name'].find(get.dname) != -1: continue;
            tmp.append(d);
        
        data = tmp;
        public.writeFile(jsonFile,json.dumps(data));
        return public.returnMsg(True,'删除成功!');
    
    #下载文件
    def DownloadFile(self,url,filename):
        try:
            path = os.path.dirname(filename)
            if not os.path.exists(path): os.makedirs(path)
            import urllib,socket
            socket.setdefaulttimeout(10)
            self.pre = 0;
            self.oldTime = time.time();
            if sys.version_info[0] == 2:
                urllib.urlretrieve(url,filename=filename,reporthook= self.DownloadHook)
            else:
                urllib.request.urlretrieve(url,filename=filename,reporthook= self.DownloadHook)
            self.WriteLogs(json.dumps({'name':'下载文件','total':0,'used':0,'pre':0,'speed':0}));
        except:
            if self.timeoutCount > 5: return;
            self.timeoutCount += 1
            time.sleep(5)
            self.DownloadFile(url,filename)
            
    #下载文件进度回调  
    def DownloadHook(self,count, blockSize, totalSize):
        used = count * blockSize
        pre1 = int((100.0 * used / totalSize))
        if self.pre != pre1:
            dspeed = used / (time.time() - self.oldTime);
            speed = {'name':'下载文件','total':totalSize,'used':used,'pre':self.pre,'speed':dspeed}
            self.WriteLogs(json.dumps(speed))
            self.pre = pre1
    
    #写输出日志
    def WriteLogs(self,logMsg):
        fp = open(self.logPath,'w+');
        fp.write(logMsg)
        fp.close()
    
    #一键安装网站程序
    #param string name 程序名称
    #param string site_name 网站名称
    #param string php_version PHP版本
    def SetupPackage(self,get):
        name = get.dname
        site_name = get.site_name;
        php_version = get.php_version;
        #取基础信息
        find = public.M('sites').where('name=?',(site_name,)).field('id,path').find();
        path = find['path'];
        
        #获取包信息
        pinfo = self.GetPackageInfo(name);
        if not pinfo: return public.returnMsg(False,'指定软件包不存在!');
        
        #检查本地包
        self.WriteLogs(json.dumps({'name':'正在校验软件包...','total':0,'used':0,'pre':0,'speed':0}));
        packageZip = self.__setupPath + '/package/' + name + '.zip';
        isDownload = False;
        if os.path.exists(packageZip):
            md5str = self.GetFileMd5(packageZip);
            if md5str != pinfo['md5']: isDownload = True;
        else:
            isDownload = True;
            
        #下载文件
        
        if isDownload:
            self.WriteLogs(json.dumps({'name':'正在下载文件 ...','total':0,'used':0,'pre':0,'speed':0}));
            self.DownloadFile(pinfo['download'], packageZip);
        if not os.path.exists(packageZip): return public.returnMsg(False,'文件下载失败!');
        
        self.WriteLogs(json.dumps({'name':'正在解压软件包...','total':0,'used':0,'pre':0,'speed':0}));
        os.system('unzip -o '+packageZip+' -d ' + path + '/');
        
        #设置权限
        self.WriteLogs(json.dumps({'name':'设置权限','total':0,'used':0,'pre':0,'speed':0}));
        os.system('chmod -R 755 ' + path);
        os.system('chown -R www.www ' + path);
        if pinfo['chmod'] != "":
            access = pinfo['chmod'].split(',')
            for chm in access:
                tmp = chm.split('|');
                if len(tmp) != 2: continue;
                os.system('chmod -R ' + tmp[0] + ' ' + path + '/' + tmp[1]);
        
        #安装PHP扩展
        self.WriteLogs(json.dumps({'name':'安装必要的PHP扩展','total':0,'used':0,'pre':0,'speed':0}));
        if pinfo['ext'] != '':
            exts = pinfo['ext'].split(',');
            import files
            mfile = files.files();
            for ext in exts:
                if ext == 'pathinfo': 
                    import config
                    con = config.config();
                    get.version = php_version;
                    get.type = 'on';
                    con.setPathInfo(get);
                else:
                    get.name = ext
                    get.version = php_version
                    get.type = '1';
                    mfile.InstallSoft(get);
        
        
        #执行额外shell进行依赖安装
        self.WriteLogs(json.dumps({'name':'执行额外SHELL','total':0,'used':0,'pre':0,'speed':0}));
        if os.path.exists(path+'/install.sh'): 
            os.system('cd '+path+' && bash ' + 'install.sh');
            os.system('rm -f ' + path+'/install.sh')
            
        #是否执行Composer
        if os.path.exists(path + '/composer.json'):
            self.WriteLogs(json.dumps({'name':'执行Composer','total':0,'used':0,'pre':0,'speed':0}));
            if not os.path.exists(path + '/composer.lock'):
                execPHP = '/www/server/php/' + php_version +'/bin/php';
                if execPHP:
                    if public.get_url().find('125.88'):
                        os.system('cd ' +path+' && '+execPHP+' /usr/bin/composer config repo.packagist composer https://packagist.phpcomposer.com');
                    import panelSite;
                    phpini = '/www/server/php/' + php_version + '/etc/php.ini'
                    phpiniConf = public.readFile(phpini);
                    phpiniConf = phpiniConf.replace('proc_open,proc_get_status,','');
                    public.writeFile(phpini,phpiniConf);
                    os.system('nohup cd '+path+' && '+execPHP+' /usr/bin/composer install -vvv > /tmp/composer.log 2>&1 &');
        
        #写伪静态
        self.WriteLogs(json.dumps({'name':'设置伪静态','total':0,'used':0,'pre':0,'speed':0}));
        swfile = path + '/nginx.rewrite';
        if os.path.exists(swfile):
            rewriteConf = public.readFile(swfile);
            dwfile = self.__panelPath + '/vhost/rewrite/' + site_name + '.conf';
            public.writeFile(dwfile,rewriteConf);
        
        #删除伪静态文件
        public.ExecShell("rm -f " + path + '/*.rewrite')
        
        #删除多余文件
        rm_file = path + '/index.html'
        if os.path.exists(rm_file): 
            rm_file_body = public.readFile(rm_file)
            if rm_file_body.find('panel-heading') != -1: os.remove(rm_file)
        
        #设置运行目录
        self.WriteLogs(json.dumps({'name':'设置运行目录','total':0,'used':0,'pre':0,'speed':0}));
        if pinfo['run'] != '/':
            import panelSite;
            siteObj = panelSite.panelSite();
            mobj = obj();
            mobj.id = find['id'];
            mobj.runPath = pinfo['run'];
            siteObj.SetSiteRunPath(mobj);
            
        #导入数据
        self.WriteLogs(json.dumps({'name':'导入数据库','total':0,'used':0,'pre':0,'speed':0}));
        if os.path.exists(path+'/import.sql'):
            databaseInfo = public.M('databases').where('pid=?',(find['id'],)).field('username,password').find();
            if databaseInfo:
                os.system('/www/server/mysql/bin/mysql -u' + databaseInfo['username'] + ' -p' + databaseInfo['password'] + ' ' + databaseInfo['username'] + ' < ' + path + '/import.sql');
                os.system('rm -f ' + path + '/import.sql');
                siteConfigFile = path + '/' + pinfo['config'];
                if os.path.exists(siteConfigFile):
                    siteConfig = public.readFile(siteConfigFile)
                    siteConfig = siteConfig.replace('BT_DB_USERNAME',databaseInfo['username'])
                    siteConfig = siteConfig.replace('BT_DB_PASSWORD',databaseInfo['password'])
                    siteConfig = siteConfig.replace('BT_DB_NAME',databaseInfo['username'])
                    public.writeFile(siteConfigFile,siteConfig)
        
        public.serviceReload();
        self.depTotal(name);
        self.WriteLogs(json.dumps({'name':'准备部署','total':0,'used':0,'pre':0,'speed':0}));
        return public.returnMsg(True,pinfo);
    
    #提交安装统计
    def depTotal(self,name):
        try:
            import urllib2
            urllib2.urlopen("http://www.bt.cn/Api/depTotal?name=" + name, timeout = 3)
            return True
        except:
            return False;
    
    #获取进度
    def GetSpeed(self,get):
        try:
            if not os.path.exists(self.logPath): public.returnMsg(False,'当前没有部署任务!');
            return json.loads(public.readFile(self.logPath));
        except:
            return {'name':'准备部署','total':0,'used':0,'pre':0,'speed':0}
     
    #获取包信息
    def GetPackageInfo(self,name):
        data = self.GetDepList(None);
        if not data: return False;
        downUrl = public.get_url() + '/install/package';
        for info in data:
            if info['name'] == name:
                info['download'] = info['download'].replace('{Download}',downUrl);
                return info;
        return False;
    
    #检查指定包是否存在
    def CheckPackageExists(self,name):
        data = self.GetDepList(None);
        if not data: return False;
        for info in data:
            if info['name'] == name: return True;
        
        return False;
    
    #文件的MD5值
    def GetFileMd5(self,filename):
        if not os.path.isfile(filename): return False;
        import hashlib;
        myhash = hashlib.md5()
        f = open(filename,'rb')
        while True:
            b = f.read(8096)
            if not b :
                break
            myhash.update(b)
        f.close()
        return myhash.hexdigest();
    
    #获取站点标识
    def GetSiteId(self,get):
        return public.M('sites').where('name=?',(get.webname,)).getField('id');
    