#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2017 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: 黄文良 <287962566@qq.com>
#-------------------------------------------------------------------

#------------------------------
# 网站管理类
#------------------------------
import io,re,public,os,sys,shutil,json,hashlib,socket,time
from BTPanel import session
from panelRedirect import  panelRedirect
class panelSite(panelRedirect):
    siteName = None #网站名称
    sitePath = None #根目录
    sitePort = None #端口
    phpVersion = None #PHP版本
    setupPath = None #安装路径
    isWriteLogs = None #是否写日志
    nginx_conf_bak = '/tmp/backup_nginx.conf'
    apache_conf_bak = '/tmp/backup_apache.conf'
    is_ipv6 = False

    def __init__(self):
        self.setupPath = '/www/server';
        path = self.setupPath + '/panel/vhost/nginx'
        if not os.path.exists(path): public.ExecShell("mkdir -p " + path + " && chmod -R 644 " + path);
        path = self.setupPath + '/panel/vhost/apache'
        if not os.path.exists(path): public.ExecShell("mkdir -p " + path + " && chmod -R 644 " + path);
        path = self.setupPath + '/panel/vhost/rewrite'
        if not os.path.exists(path): public.ExecShell("mkdir -p " + path + " && chmod -R 644 " + path);
        path = self.setupPath + '/stop';
        if not os.path.exists(path + '/index.html'):
            os.system('mkdir -p ' + path);
            os.system('wget -O ' + path + '/index.html '+public.get_url()+'/stop.html &');
        self.__proxyfile = '/www/server/panel/data/proxyfile.json'
        self.OldConfigFile();
        if os.path.exists(self.nginx_conf_bak): os.remove(self.nginx_conf_bak)
        if os.path.exists(self.apache_conf_bak): os.remove(self.apache_conf_bak)
        self.is_ipv6 = os.path.exists(self.setupPath + '/panel/data/ipv6.pl')

    #默认配置文件
    def check_default(self):
        nginx = self.setupPath + '/panel/vhost/nginx'
        httpd = self.setupPath + '/panel/vhost/apache'
        httpd_default = '''<VirtualHost *:80>
    ServerAdmin webmaster@example.com
    DocumentRoot "/www/server/apache/htdocs"
    ServerName bt.default.com
    <Directory "/www/server/apache/htdocs">
        SetOutputFilter DEFLATE
        Options FollowSymLinks
        AllowOverride All
        Order allow,deny
        Allow from all
        DirectoryIndex index.html
    </Directory>
</VirtualHost>'''
        
        listen_ipv6 = ''
        if self.is_ipv6: listen_ipv6 = "\n    listen [::]:80;"
        nginx_default = '''server
{
    listen 80;%s
    server_name _;
    index index.html;
    root /www/server/nginx/html;
}''' % listen_ipv6 
        if not os.path.exists(httpd + '/0.default.conf') and not os.path.exists(httpd + '/default.conf'): public.writeFile(httpd + '/0.default.conf',httpd_default)
        if not os.path.exists(nginx + '/0.default.conf') and not os.path.exists(nginx + '/default.conf'): public.writeFile(nginx + '/0.default.conf',nginx_default)
    
    #添加apache端口
    def apacheAddPort(self,port):
        filename = self.setupPath+'/apache/conf/extra/httpd-ssl.conf';
        if os.path.exists(filename):
            ssl_conf = public.readFile(filename)
            if ssl_conf:
                if ssl_conf.find('Listen 443') != -1: 
                    ssl_conf = ssl_conf.replace('Listen 443','')
                    public.writeFile(filename,ssl_conf)

        filename = self.setupPath+'/apache/conf/httpd.conf';
        if not os.path.exists(filename): return;
        allConf = public.readFile(filename);
        rep = "Listen\s+([0-9]+)\n";
        tmp = re.findall(rep,allConf);
        if not tmp: return False;
        for key in tmp:
            if key == port: return False
        
        listen = "\nListen "+tmp[0]
        listen_ipv6 = ''
        #if self.is_ipv6: listen_ipv6 = "\nListen [::]:" + port
        allConf = allConf.replace(listen,listen + "\nListen " + port + listen_ipv6)
        public.writeFile(filename, allConf)
        return True
    
    #添加到apache
    def apacheAdd(self):
        import time
        listen = '';
        if self.sitePort != '80': self.apacheAddPort(self.sitePort);
        acc = public.md5(str(time.time()))[0:8];
        try:
            httpdVersion = public.readFile(self.setupPath+'/apache/version.pl').strip();
        except:
            httpdVersion = "";
        if httpdVersion == '2.2':
            vName = '';
            if self.sitePort != '80' and self.sitePort != '443':
                vName = "NameVirtualHost  *:"+self.sitePort+"\n";
            phpConfig = "";
            apaOpt = "Order allow,deny\n\t\tAllow from all";
        else:
            vName = "";
            phpConfig ='''
    #PHP
    <FilesMatch \\.php$>
            SetHandler "proxy:unix:/tmp/php-cgi-%s.sock|fcgi://localhost"
    </FilesMatch>
    ''' % (self.phpVersion,)
            apaOpt = 'Require all granted';
        
        conf='''%s<VirtualHost *:%s>
    ServerAdmin webmaster@example.com
    DocumentRoot "%s"
    ServerName %s.%s
    ServerAlias %s
    #errorDocument 404 /404.html
    ErrorLog "%s-error_log"
    CustomLog "%s-access_log" combined
    
    #DENY FILES
     <Files ~ (\.user.ini|\.htaccess|\.git|\.svn|\.project|LICENSE|README.md)$>
       Order allow,deny
       Deny from all
    </Files>
    %s
    #PATH
    <Directory "%s">
        SetOutputFilter DEFLATE
        Options FollowSymLinks
        AllowOverride All
        %s
        DirectoryIndex index.php index.html index.htm default.php default.html default.htm
    </Directory>
</VirtualHost>''' % (vName,self.sitePort,self.sitePath,acc,self.siteName,self.siteName,public.GetConfigValue('logs_path')+'/'+self.siteName,public.GetConfigValue('logs_path')+'/'+self.siteName,phpConfig,self.sitePath,apaOpt)
    
        htaccess = self.sitePath+'/.htaccess'
        if not os.path.exists(htaccess): public.writeFile(htaccess, ' ');
        public.ExecShell('chmod -R 755 ' + htaccess);
        public.ExecShell('chown -R www:www ' + htaccess);

        filename = self.setupPath+'/panel/vhost/apache/'+self.siteName+'.conf'
        public.writeFile(filename,conf)
        return True
    
    #添加到nginx
    def nginxAdd(self):
        listen_ipv6 = ''
        if self.is_ipv6: listen_ipv6 = "\n    listen [::]:%s;" % self.sitePort

        conf='''server
{
    listen %s;%s
    server_name %s;
    index index.php index.html index.htm default.php default.htm default.html;
    root %s;
    
    #SSL-START %s
    #error_page 404/404.html;
    #SSL-END
    
    #ERROR-PAGE-START  %s
    #error_page 404 /404.html;
    #error_page 502 /502.html;
    #ERROR-PAGE-END
    
    #PHP-INFO-START  %s
    include enable-php-%s.conf;
    #PHP-INFO-END
    
    #REWRITE-START %s
    include %s/panel/vhost/rewrite/%s.conf;
    #REWRITE-END
    
    #禁止访问的文件或目录
    location ~ ^/(\.user.ini|\.htaccess|\.git|\.svn|\.project|LICENSE|README.md)
    {
        return 404;
    }
    
    #一键申请SSL证书验证目录相关设置
    location ~ \.well-known{
        allow all;
    }
    
    location ~ .*\\.(gif|jpg|jpeg|png|bmp|swf)$
    {
        expires      30d;
        error_log off;
        access_log /dev/null;
    }
    
    location ~ .*\\.(js|css)?$
    {
        expires      12h;
        error_log off;
        access_log /dev/null; 
    }
    access_log  %s.log;
    error_log  %s.error.log;
}''' % (self.sitePort,listen_ipv6,self.siteName,self.sitePath,public.getMsg('NGINX_CONF_MSG1'),public.getMsg('NGINX_CONF_MSG2'),public.getMsg('NGINX_CONF_MSG3'),self.phpVersion,public.getMsg('NGINX_CONF_MSG4'),self.setupPath,self.siteName,public.GetConfigValue('logs_path')+'/'+self.siteName,public.GetConfigValue('logs_path')+'/'+self.siteName)
        
        #写配置文件
        filename = self.setupPath+'/panel/vhost/nginx/'+self.siteName+'.conf'
        public.writeFile(filename,conf);
        
        #生成伪静态文件
        urlrewritePath = self.setupPath+'/panel/vhost/rewrite';
        urlrewriteFile = urlrewritePath+'/'+self.siteName+'.conf';
        if not os.path.exists(urlrewritePath): os.makedirs(urlrewritePath);
        open(urlrewriteFile,'w+').close();
        return True;
    
     
    #添加站点
    def AddSite(self,get):
        self.check_default()
        isError = public.checkWebConfig()
        if isError != True:
            return public.returnMsg(False,'ERROR: 检测到配置文件有错误,请先排除后再操作<br><br><a style="color:red;">'+isError.replace("\n",'<br>')+'</a>');
        
        import json,files

        get.path = self.__get_site_format_path(get.path)
        siteMenu = json.loads(get.webname)
        self.siteName     = self.ToPunycode(siteMenu['domain'].strip().split(':')[0]).strip().lower();
        self.sitePath     = self.ToPunycodePath(self.GetPath(get.path.replace(' ','')));
        self.sitePort     = get.port.strip().replace(' ','');

        if self.sitePort == "": get.port = "80";
        if not public.checkPort(self.sitePort): return public.returnMsg(False,'SITE_ADD_ERR_PORT');
        
        if hasattr(get,'version'):
            self.phpVersion   = get.version.replace(' ','');
        else:
            self.phpVersion   = '00';

        if not self.phpVersion: self.phpVersion = '00';

        php_version = self.GetPHPVersion(get)
        is_phpv = False
        for php_v in php_version:
            if self.phpVersion == php_v['version']: 
                is_phpv = True
                break
        if not is_phpv: return public.returnMsg(False,'指定PHP版本不存在!')
        
        domain = None
        #if siteMenu['count']:
        #    domain            = get.domain.replace(' ','')
        #表单验证
        if not files.files().CheckDir(self.sitePath) or not self.__check_site_path(self.sitePath): return public.returnMsg(False,'PATH_ERROR');
        if len(self.phpVersion) < 2: return public.returnMsg(False,'SITE_ADD_ERR_PHPEMPTY');
        reg = "^([\w\-\*]{1,100}\.){1,4}([\w\-]{1,24}|[\w\-]{1,24}\.[\w\-]{1,24})$";
        if not re.match(reg, self.siteName): return public.returnMsg(False,'SITE_ADD_ERR_DOMAIN');
        if self.siteName.find('*') != -1: return public.returnMsg(False,'SITE_ADD_ERR_DOMAIN_TOW');
        
        if not domain: domain = self.siteName;
    
        
        #是否重复
        sql = public.M('sites');
        if sql.where("name=?",(self.siteName,)).count(): return public.returnMsg(False,'SITE_ADD_ERR_EXISTS');
        opid = public.M('domain').where("name=?",(self.siteName,)).getField('pid');
        
        if opid:
            if public.M('sites').where('id=?',(opid,)).count():
                return public.returnMsg(False,'SITE_ADD_ERR_DOMAIN_EXISTS');
            public.M('domain').where('pid=?',(opid,)).delete();

        if public.M('binding').where('domain=?',(self.siteName,)).count():
            return public.returnMsg(False,'SITE_ADD_ERR_DOMAIN_EXISTS');
        
        #创建根目录
        if not os.path.exists(self.sitePath): 
            os.makedirs(self.sitePath)
            public.ExecShell('chmod -R 755 ' + self.sitePath);
            public.ExecShell('chown -R www:www ' + self.sitePath);
        
        #创建basedir
        self.DelUserInI(self.sitePath);
        userIni = self.sitePath+'/.user.ini';
        if not os.path.exists(userIni):
            public.writeFile(userIni, 'open_basedir='+self.sitePath+'/:/tmp/:/proc/');
            public.ExecShell('chmod 644 ' + userIni);
            public.ExecShell('chown root:root ' + userIni);
            public.ExecShell('chattr +i '+userIni);
        
        #创建默认文档
        index = self.sitePath+'/index.html'
        if not os.path.exists(index):
            public.writeFile(index, public.readFile('data/defaultDoc.html'))
            public.ExecShell('chmod -R 755 ' + index);
            public.ExecShell('chown -R www:www ' + index);
        
        #创建自定义404页
        doc404 = self.sitePath+'/404.html'
        if not os.path.exists(doc404):
            public.writeFile(doc404, public.readFile('data/404.html'));
            public.ExecShell('chmod -R 755 ' + doc404);
            public.ExecShell('chown -R www:www ' + doc404);
        
        #写入配置
        result = self.nginxAdd()
        result = self.apacheAdd()
        
        #检查处理结果
        if not result: return public.returnMsg(False,'SITE_ADD_ERR_WRITE');
        
        ps = get.ps
        #添加放行端口
        if self.sitePort != '80':
            import firewalls
            get.port = self.sitePort
            get.ps = self.siteName;
            firewalls.firewalls().AddAcceptPort(get);

        if not hasattr(get,'type_id'): get.type_id = 0
        
        #写入数据库
        get.pid = sql.table('sites').add('name,path,status,ps,type_id,addtime',(self.siteName,self.sitePath,'1',ps,get.type_id,public.getDate()))
        
        #添加更多域名
        for domain in siteMenu['domainlist']:
            get.domain = domain
            get.webname = self.siteName
            get.id = str(get.pid)
            self.AddDomain(get)
        
        sql.table('domain').add('pid,name,port,addtime',(get.pid,self.siteName,self.sitePort,public.getDate()))
        
        data = {}
        data['siteStatus'] = True
        data['siteId'] = get.pid
            
        #添加FTP
        data['ftpStatus'] = False
        if get.ftp == 'true':
            import ftp
            get.ps = self.siteName
            result = ftp.ftp().AddUser(get)
            if result['status']: 
                data['ftpStatus'] = True
                data['ftpUser'] = get.ftp_username
                data['ftpPass'] = get.ftp_password
        
        #添加数据库
        data['databaseStatus'] = False
        if get.sql == 'true' or get.sql == 'MySQL':
            import database
            if len(get.datauser) > 16: get.datauser = get.datauser[:16]
            get.name = get.datauser
            get.db_user = get.datauser
            get.password = get.datapassword
            get.address = '127.0.0.1'
            get.ps = self.siteName
            result = database.database().AddDatabase(get)
            if result['status']: 
                data['databaseStatus'] = True
                data['databaseUser'] = get.datauser
                data['databasePass'] = get.datapassword
        public.serviceReload()
        public.WriteLog('TYPE_SITE','SITE_ADD_SUCCESS',(self.siteName,))
        return data

    def __get_site_format_path(self,path):
        path = path.replace('//','/');
        if path[-1:] == '/':
            path = path[:-1]
        return path

    def __check_site_path(self,path):
        path = self.__get_site_format_path(path)
        other_path = public.M('config').where("id=?",('1',)).field('sites_path,backup_path').find();
        if path == other_path['sites_path'] or path == other_path['backup_path']: return False
        return True
    
    #删除站点
    def DeleteSite(self,get):
        proxyconf = self.__read_config(self.__proxyfile)
        id = get.id;
        if public.M('sites').where('id=?',(id,)).count() < 1: return public.returnMsg(False,'指定站点不存在!')
        siteName = get.webname;
        get.siteName = siteName
        self.CloseTomcat(get);
        # 删除反向代理
        for i in range(len(proxyconf)-1,-1,-1):
            if proxyconf[i]["sitename"] == siteName:
                del proxyconf[i]
        self.__write_config(self.__proxyfile,proxyconf)

        m_path = self.setupPath+'/panel/vhost/nginx/proxy/'+siteName
        if os.path.exists(m_path): public.ExecShell("rm -rf %s" % m_path)

        m_path = self.setupPath+'/panel/vhost/apache/proxy/'+siteName
        if os.path.exists(m_path): public.ExecShell("rm -rf %s" % m_path)

        #删除重定向
        __redirectfile = "%s/panel/data/redirect.conf" % self.setupPath
        redirectconf = self.__read_config(__redirectfile)
        for i in range(len(redirectconf)-1,-1,-1):
            if redirectconf[i]["sitename"] == siteName:
                del redirectconf[i]
        self.__write_config(__redirectfile,redirectconf)
        m_path = self.setupPath+'/panel/vhost/nginx/redirect/'+siteName

        if os.path.exists(m_path): public.ExecShell("rm -rf %s" % m_path)

        m_path = self.setupPath+'/panel/vhost/apache/redirect/'+siteName
        if os.path.exists(m_path): public.ExecShell("rm -rf %s" % m_path)
        #删除配置文件
        confPath = self.setupPath+'/panel/vhost/nginx/'+siteName+'.conf'
        if os.path.exists(confPath): os.remove(confPath)
        
        confPath = self.setupPath+'/panel/vhost/apache/' + siteName + '.conf';
        if os.path.exists(confPath): os.remove(confPath)
        
        #删除伪静态文件
        filename = confPath+'/rewrite/'+siteName+'.conf'
        if os.path.exists(filename): 
            os.remove(filename)
            public.ExecShell("rm -f " + confPath + '/rewrite/' + siteName + "_*")
        
        #删除日志文件
        filename = public.GetConfigValue('logs_path')+'/'+siteName+'*'
        public.ExecShell("rm -f " + filename)
        
        
        #删除证书
        #crtPath = '/etc/letsencrypt/live/'+siteName
        #if os.path.exists(crtPath):
        #    import shutil
        #    shutil.rmtree(crtPath)
        
        #删除日志
        public.ExecShell("rm -f " + public.GetConfigValue('logs_path') + '/' + siteName + "-*")
        
        #删除备份
        public.ExecShell("rm -f "+session['config']['backup_path']+'/site/'+siteName+'_*')
        
        #删除根目录
        if 'path' in get:
            if get.path == '1':
                import files
                get.path = self.__get_site_format_path(public.M('sites').where("id=?",(id,)).getField('path'));
                if self.__check_site_path(get.path): files.files().DeleteDir(get)
        
        #重载配置
        public.serviceReload();
        
        #从数据库删除
        public.M('sites').where("id=?",(id,)).delete();
        public.M('binding').where("pid=?",(id,)).delete();
        public.M('domain').where("pid=?",(id,)).delete();
        public.WriteLog('TYPE_SITE', "SITE_DEL_SUCCESS",(siteName,));
        
        #是否删除关联数据库
        if hasattr(get,'database'):
            if get.database == '1':
                find = public.M('databases').where("pid=?",(id,)).field('id,name').find()
                if find:
                    import database
                    get.name = find['name']
                    get.id = find['id']
                    database.database().DeleteDatabase(get)
        
        #是否删除关联FTP
        if hasattr(get,'ftp'):
            if get.ftp == '1':
                find = public.M('ftps').where("pid=?",(id,)).field('id,name').find()
                if find:
                    import ftp
                    get.username = find['name']
                    get.id = find['id']
                    ftp.ftp().DeleteUser(get)
            
        return public.returnMsg(True,'SITE_DEL_SUCCESS')
    
    #域名编码转换
    def ToPunycode(self,domain):
        import re;
        if sys.version_info[0] == 2: domain = domain.encode('utf8');
        tmp = domain.split('.');
        newdomain = '';
        for dkey in tmp:
                #匹配非ascii字符
                match = re.search(u"[\x80-\xff]+",dkey);
                if not match: match = re.search(u"[\u4e00-\u9fa5]+",dkey);
                if not match:
                    newdomain += dkey + '.';
                else:
                    if sys.version_info[0] == 2:
                        newdomain += 'xn--' + dkey.decode('utf-8').encode('punycode') + '.'
                    else:
                        newdomain += 'xn--' + dkey.encode('punycode').decode('utf-8') + '.'
        return newdomain[0:-1];
    
    #中文路径处理
    def ToPunycodePath(self,path):
        if sys.version_info[0] == 2: path = path.encode('utf-8');
        if os.path.exists(path): return path;
        import re;
        match = re.search(u"[\x80-\xff]+",path);
        if not match: match = re.search(u"[\u4e00-\u9fa5]+",path);
        if not match: return path;
        npath = '';
        for ph in path.split('/'):
            npath += '/' + self.ToPunycode(ph);
        return npath.replace('//','/')
        
    #添加域名
    def AddDomain(self,get):
        #检查配置文件
        isError = public.checkWebConfig()
        if isError != True:
            return public.returnMsg(False,'ERROR: 检测到配置文件有错误,请先排除后再操作<br><br><a style="color:red;">'+isError.replace("\n",'<br>')+'</a>');
        
        if len(get.domain) < 3: return public.returnMsg(False,'SITE_ADD_DOMAIN_ERR_EMPTY');
        domains = get.domain.replace(' ','').split(',')
        
        for domain in domains:
            if domain == "": continue;
            domain = domain.strip().split(':')
            get.domain = self.ToPunycode(domain[0]).lower()
            get.port = '80'
            
            reg = "^([\w\-\*]{1,100}\.){1,4}([\w\-]{1,24}|[\w\-]{1,24}\.[\w\-]{1,24})$";
            if not re.match(reg, get.domain): return public.returnMsg(False,'SITE_ADD_DOMAIN_ERR_FORMAT');
            
            if len(domain) == 2: get.port = domain[1];
            if get.port == "": get.port = "80";
            
            if not public.checkPort(get.port): return public.returnMsg(False,'SITE_ADD_DOMAIN_ERR_POER');
            #检查域名是否存在
            sql = public.M('domain');
            opid = sql.where("name=? AND (port=? OR pid=?)",(get.domain,get.port,get.id)).getField('pid');
            if opid:
                if public.M('sites').where('id=?',(opid,)).count():
                    return public.returnMsg(False,'SITE_ADD_DOMAIN_ERR_EXISTS');
                sql.where('pid=?',(opid,)).delete();

            if public.M('binding').where('domain=?',(get.domain,)).count():
                return public.returnMsg(False,'SITE_ADD_ERR_DOMAIN_EXISTS');

                
            
            #写配置文件
            self.NginxDomain(get)
            try:
                self.ApacheDomain(get)
            except:
                pass;
                        
            
            #添加放行端口
            if get.port != '80':
                import firewalls
                get.ps = get.domain;
                firewalls.firewalls().AddAcceptPort(get);
            
            public.serviceReload();
            public.WriteLog('TYPE_SITE', 'DOMAIN_ADD_SUCCESS',(get.webname,get.domain));
            sql.table('domain').add('pid,name,port,addtime',(get.id,get.domain,get.port,public.getDate()));

        return public.returnMsg(True,'SITE_ADD_DOMAIN');
    
    #Nginx写域名配置
    def NginxDomain(self,get):
        file = self.setupPath + '/panel/vhost/nginx/'+get.webname+'.conf';
        conf = public.readFile(file);
        if not conf: return;
        
        #添加域名
        rep = "server_name\s*(.*);";
        tmp = re.search(rep,conf).group()
        domains = tmp.replace(';','').strip().split(' ')
        if not public.inArray(domains,get.domain):
            newServerName = tmp.replace(';',' ' + get.domain + ';')
            conf = conf.replace(tmp,newServerName)
        
        #添加端口
        rep = "listen\s+([0-9]+)\s*[default_server]*\s*;";
        tmp = re.findall(rep,conf);
        if not public.inArray(tmp,get.port):
            listen = re.search(rep,conf).group()
            listen_ipv6 = ''
            if self.is_ipv6: listen_ipv6 = "\n\tlisten [::]:"+get.port+';'
            conf = conf.replace(listen,listen + "\n\tlisten "+get.port+';' + listen_ipv6)
        #保存配置文件
        public.writeFile(file,conf)
        return True
    
    #Apache写域名配置
    def ApacheDomain(self,get):
        file = self.setupPath + '/panel/vhost/apache/'+get.webname+'.conf';
        conf = public.readFile(file);
        if not conf: return;
        
        port = get.port;
        siteName = get.webname;
        newDomain = get.domain
        find = public.M('sites').where("id=?",(get.id,)).field('id,name,path').find();
        sitePath = find['path'];
        siteIndex = 'index.php index.html index.htm default.php default.html default.htm'
            
        #添加域名
        if conf.find('<VirtualHost *:'+port+'>') != -1:
            repV = "<VirtualHost\s+\*\:"+port+">(.|\n)*</VirtualHost>";
            domainV = re.search(repV,conf).group()
            rep = "ServerAlias\s*(.*)\n";
            tmp = re.search(rep,domainV).group(0)
            domains = tmp.strip().split(' ')
            if not public.inArray(domains,newDomain):
                rs = tmp.replace("\n","")
                newServerName = rs+' '+newDomain+"\n";
                myconf = domainV.replace(tmp,newServerName);
                conf = re.sub(repV, myconf, conf);
            if conf.find('<VirtualHost *:443>') != -1:
                repV = "<VirtualHost\s+\*\:443>(.|\n)*</VirtualHost>";
                domainV = re.search(repV,conf).group()
                rep = "ServerAlias\s*(.*)\n";
                tmp = re.search(rep,domainV).group(0)
                domains = tmp.strip().split(' ')
                if not public.inArray(domains,newDomain):
                    rs = tmp.replace("\n","")
                    newServerName = rs+' '+newDomain+"\n";
                    myconf = domainV.replace(tmp,newServerName);
                    conf = re.sub(repV, myconf, conf);
        else:
            try:
                httpdVersion = public.readFile(self.setupPath+'/apache/version.pl').strip();
            except:
                httpdVersion = "";
            if httpdVersion == '2.2':
                vName = '';
                if self.sitePort != '80' and self.sitePort != '443':
                    vName = "NameVirtualHost  *:"+port+"\n";
                phpConfig = "";
                apaOpt = "Order allow,deny\n\t\tAllow from all";
            else:
                vName = "";
                rep = "php-cgi-([0-9]{2,3})\.sock";
                version = re.search(rep,conf).groups()[0]
                if len(version) < 2: return public.returnMsg(False,'PHP_GET_ERR')
                phpConfig ='''
    #PHP
    <FilesMatch \\.php$>
            SetHandler "proxy:unix:/tmp/php-cgi-%s.sock|fcgi://localhost"
    </FilesMatch>
    ''' % (version,);
                apaOpt = 'Require all granted';
            
            newconf='''<VirtualHost *:%s>
    ServerAdmin webmaster@example.com
    DocumentRoot "%s"
    ServerName %s.%s
    ServerAlias %s
    #errorDocument 404 /404.html
    ErrorLog "%s-error_log"
    CustomLog "%s-access_log" combined
    %s
    
    #DENY FILES
     <Files ~ (\.user.ini|\.htaccess|\.git|\.svn|\.project|LICENSE|README.md)$>
       Order allow,deny
       Deny from all
    </Files>
    
    #PATH
    <Directory "%s">
        SetOutputFilter DEFLATE
        Options FollowSymLinks
        AllowOverride All
        %s
        DirectoryIndex %s
    </Directory>
</VirtualHost>''' % (port,sitePath,siteName,port,newDomain,public.GetConfigValue('logs_path')+'/'+siteName,public.GetConfigValue('logs_path')+'/'+siteName,phpConfig,sitePath,apaOpt,siteIndex)
            conf += "\n\n"+newconf;
        
        #添加端口
        if port != '80' and port != '888': self.apacheAddPort(port)
        
        #保存配置文件
        public.writeFile(file,conf)
        return True
    
    #删除域名
    def DelDomain(self,get):
        sql = public.M('domain');
        id=get['id'];
        port = get.port;
        find = sql.where("pid=? AND name=?",(get.id,get.domain)).field('id,name').find();
        domain_count = sql.table('domain').where("pid=?",(id,)).count();
        if domain_count == 1: return public.returnMsg(False,'SITE_DEL_DOMAIN_ERR_ONLY');
        
        #nginx
        file = self.setupPath+'/panel/vhost/nginx/'+get['webname']+'.conf';
        conf = public.readFile(file);
        if conf:
            #删除域名
            rep = "server_name\s+(.+);";
            tmp = re.search(rep,conf).group()
            newServerName = tmp.replace(' '+get['domain']+';',';');
            newServerName = newServerName.replace(' '+get['domain']+' ',' ');
            conf = conf.replace(tmp,newServerName);
            
            #删除端口
            rep = "listen\s+([0-9]+);";
            tmp = re.findall(rep,conf);
            port_count = sql.table('domain').where('pid=? AND port=?',(get.id,get.port)).count()
            if public.inArray(tmp,port) == True and  port_count < 2:
                rep = "\n*\s+listen\s+"+port+";";
                conf = re.sub(rep,'',conf);
                rep = "\n*\s+listen\s+\[::\]:"+port+";";
                conf = re.sub(rep,'',conf);
            #保存配置
            public.writeFile(file,conf)
        
        #apache
        file = self.setupPath+'/panel/vhost/apache/'+get['webname']+'.conf';
        conf = public.readFile(file);
        if conf:
            #删除域名
            try:
                rep = "\n*<VirtualHost \*\:" + port + ">(.|\n)*</VirtualHost>";
                tmp = re.search(rep, conf).group()
                
                rep1 = "ServerAlias\s+(.+)\n";
                tmp1 = re.findall(rep1,tmp);
                tmp2 = tmp1[0].split(' ')
                if len(tmp2) < 2:
                    conf = re.sub(rep,'',conf);
                    rep = "NameVirtualHost.+\:" + port + "\n";
                    conf = re.sub(rep,'',conf);
                else:
                    newServerName = tmp.replace(' '+get['domain']+"\n","\n");
                    newServerName = newServerName.replace(' '+get['domain']+' ',' ');
                    conf = conf.replace(tmp,newServerName);
            
                #保存配置
                public.writeFile(file,conf)
            except:
                pass;
        
        sql.table('domain').where("id=?",(find['id'],)).delete();
        public.WriteLog('TYPE_SITE', 'DOMAIN_DEL_SUCCESS',(get.webname,get.domain));
        public.serviceReload();
        return public.returnMsg(True,'DEL_SUCCESS');
    
    #检查域名是否解析
    def CheckDomainPing(self,get):
        try:
            epass = public.GetRandomString(32);
            spath = get.path + '/.well-known/pki-validation';
            if not os.path.exists(spath): os.system("mkdir -p '" + spath + "'");
            public.writeFile(spath + '/fileauth.txt',epass);
            result = public.httpGet('http://' + get.domain.replace('*.','') + '/.well-known/pki-validation/fileauth.txt');
            if result == epass: return True
            return False
        except:
            return False
    
    # 保存第三方证书
    def SetSSL(self, get):
        siteName = get.siteName;
        path = '/www/server/panel/vhost/cert/' + siteName;
        csrpath = path + "/fullchain.pem"
        keypath = path + "/privkey.pem"

        if (get.key.find('KEY') == -1): return public.returnMsg(False, 'SITE_SSL_ERR_PRIVATE');
        if (get.csr.find('CERTIFICATE') == -1): return public.returnMsg(False, 'SITE_SSL_ERR_CERT');
        public.writeFile('/tmp/cert.pl', get.csr);
        if not public.CheckCert('/tmp/cert.pl'): return public.returnMsg(False, '证书错误,请粘贴正确的PEM格式证书!');
        backup_cert = '/tmp/backup_cert_' + siteName
        
        import shutil
        if os.path.exists(backup_cert): shutil.rmtree(backup_cert)
        if os.path.exists(path): shutil.move(path,backup_cert)
        if os.path.exists(path): shutil.rmtree(path)

        public.ExecShell('mkdir -p ' + path)
        public.writeFile(keypath, get.key);
        public.writeFile(csrpath, get.csr);

        # 写入配置文件
        result = self.SetSSLConf(get);
        if not result['status']: return result;
        isError = public.checkWebConfig();

        if (type(isError) == str):
            if os.path.exists(path): shutil.rmtree(backup_cert)
            shutil.move(backup_cert,path)
            return public.returnMsg(False, 'ERROR: <br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>');
        public.serviceReload();

        if os.path.exists(path + '/partnerOrderId'): os.remove(path + '/partnerOrderId')
        p_file = '/etc/letsencrypt/live/' + get.siteName
        if os.path.exists(p_file): shutil.rmtree(p_file)
        public.WriteLog('TYPE_SITE', 'SITE_SSL_SAVE_SUCCESS')

        #清理备份证书
        if os.path.exists(backup_cert): shutil.rmtree(backup_cert)
        return public.returnMsg(True, 'SITE_SSL_SUCCESS')
        
    #获取运行目录
    def GetRunPath(self,get):
        if not hasattr(get,'id'):
            if hasattr(get,'siteName'):
                get.id = public.M('sites').where('name=?',(get.siteName,)).getField('id');
            else:
                get.id = public.M('sites').where('path=?',(get.path,)).getField('id');
        if not get.id: return False;
        if type(get.id) == list: get.id = get.id[0]['id'];
        result = self.GetSiteRunPath(get);
        return result['runPath'];


    # 创建Let's Encrypt免费证书
    def CreateLet(self,get):

        domains = json.loads(get.domains)
        if not len(domains): 
            return public.returnMsg(False, '请选择域名');

        file_auth =  True
        if hasattr(get, 'dnsapi'): 
            file_auth = False
        
        if not hasattr(get, 'dnssleep'): 
            get.dnssleep = 10

        email = public.M('users').getField('email');
        if hasattr(get, 'email'):
            if get.email.find('@') == -1: 
                get.email = email
            else:
                get.email = get.email.strip()
                public.M('users').where('id=?',(1,)).setField('email',get.email);
        else:
            get.email = email
              
        for domain in domains:
            if public.checkIp(domain): continue;
            if domain.find('*.') >=0 and file_auth:
                return public.returnMsg(False, '泛域名不能使用【文件验证】的方式申请证书!');

        if file_auth:
            get.sitename = get.siteName
            if self.GetRedirectList(get): return public.returnMsg(False, 'SITE_SSL_ERR_301');
            if self.GetProxyList(get): return public.returnMsg(False,'已开启反向代理的站点无法申请SSL!');
            data = self.get_site_info(get.siteName)
            get.site_dir = data['path']
        else:          
            dns_api_list = self.GetDnsApi(get)
            get.dns_param = None
            for dns in dns_api_list:                
                if dns['name'] == get.dnsapi:        
                    param = [];
                    if not dns['data']: continue 
                    for val in dns['data']:
                        param.append(val['value'])
                    get.dns_param  = '|'.join(param)
            n_list = ['dns' , 'dns_bt']
            if not get.dnsapi in n_list:
                if len(get.dns_param) < 16: return public.returnMsg(False, '请先设置【%s】的API接口参数.' % get.dnsapi);
            if get.dnsapi == 'dns_bt':
                if not os.path.exists('plugin/dns/dns_main.py'):
                    return public.returnMsg(False, '请先到软件商店安装【云解析】，并完成域名NS绑定.');

        self.check_ssl_pack()
        import panelLets
        lets = panelLets.panelLets()
        result = lets.apple_lest_cert(get)
        if result['status'] and not 'code' in result:       
            get.onkey = 1;
            result = self.SetSSLConf(get)
        return result

    def get_site_info(self,siteName):
        data = public.M("sites").where('name=?',siteName).field('path,name').find()
        return data


    #检测依赖库
    def check_ssl_pack(self):
        try:
            import requests
        except:
            os.system('pip install requests')
        try:
            import OpenSSL
        except:
            os.system('pip install pyopenssl')


    #判断DNS-API是否设置
    def Check_DnsApi(self,dnsapi):
        dnsapis = self.GetDnsApi(None)
        for dapi in dnsapis:
            if dapi['name'] == dnsapi:
                if not dapi['data']: return True
                for d in dapi['data']:
                    if d['key'] == '': return False
        return True
    
    #获取DNS-API列表
    def GetDnsApi(self,get):
        apis = json.loads(public.ReadFile('./config/dns_api.json'))
        path = '/root/.acme.sh'
        if not os.path.exists(path + '/account.conf'): path = "/.acme.sh"
        account = public.readFile(path + '/account.conf')
        if not account: account = ''
        is_write = False
        for i in range(len(apis)):
            if not apis[i]['data']: continue
            for j in range(len(apis[i]['data'])):
                if apis[i]['data'][j]['value']: continue
                match = re.search(apis[i]['data'][j]['key'] + "\s*=\s*'(.+)'",account)
                if match: apis[i]['data'][j]['value'] = match.groups()[0]
                if apis[i]['data'][j]['value']: is_write = True
        if is_write: public.writeFile('./config/dns_api.json',json.dumps(apis))
        result = []
        for i in apis: result.insert(0,i)
        return result

    #设置DNS-API
    def SetDnsApi(self,get):
        pdata = json.loads(get.pdata)
        apis = json.loads(public.ReadFile('./config/dns_api.json'))
        is_write = False
        for key in pdata.keys():
            for i in range(len(apis)):
                if not apis[i]['data']: continue
                for j in range(len(apis[i]['data'])):
                    if apis[i]['data'][j]['key'] != key: continue
                    apis[i]['data'][j]['value'] = pdata[key]
                    is_write = True

        if is_write: public.writeFile('./config/dns_api.json',json.dumps(apis))
        return public.returnMsg(True,"设置成功!")
    
        
    #获取站点所有域名
    def GetSiteDomains(self,get):
        data = {}
        domains = public.M('domain').where('pid=?',(get.id,)).field('name,id').select()
        binding = public.M('binding').where('pid=?',(get.id,)).field('domain,id').select()
        if type(binding) == str: return binding
        for b in binding:
            tmp = {}
            tmp['name'] = b['domain']
            tmp['id'] = b['id']
            tmp['binding'] = True
            domains.append(tmp)
        data['domains'] = domains
        data['email'] = public.M('users').where('id=?',(1,)).getField('email')
        if data['email'] == '287962566@qq.com': data['email'] = ''
        return data
    
    def GetFormatSSLResult(self,result):
        try:
            import re
            rep = "\s*Domain:.+\n\s+Type:.+\n\s+Detail:.+"
            tmps = re.findall(rep,result)
        
            statusList = [];
            for tmp in tmps:
                arr = tmp.strip().split('\n')
                status={}
                for ar in arr:
                    tmp1 = ar.strip().split(':')
                    status[tmp1[0].strip()] = tmp1[1].strip()
                    if len(tmp1) > 2:
                        status[tmp1[0].strip()] = tmp1[1].strip() + ':' + tmp1[2]
                statusList.append(status)
            return statusList
        except:
            return None;

    #获取TLS1.3标记
    def get_tls13(self):
        nginx_bin = '/www/server/nginx/sbin/nginx'
        nginx_v = public.ExecShell(nginx_bin + ' -V 2>&1|grep version:')[0]
        nginx_v = re.search('nginx/1\.1(5|6|7|8|9).\d',nginx_v)
        openssl_v = public.ExecShell(nginx_bin + ' -V 2>&1|grep OpenSSL')[0].find('OpenSSL 1.1.') != -1
        if nginx_v and openssl_v:
            return ' TLSv1.3'
        return ''
  
    # 获取apache反向代理
    def get_apache_proxy(self,conf):
        rep = "\n*#引用反向代理规则，注释后配置的反向代理将无效\n+\s+IncludeOptiona[\s\w\/\.\*]+"
        proxy = re.search(rep,conf)
        if proxy:
            return proxy.group()
        return ""
  
    # 添加SSL配置
    def SetSSLConf(self, get):
        siteName = get.siteName
        if not 'first_domain' in get: get.first_domain = siteName

        # Nginx配置
        file = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf';
        ng_file = file
        conf = public.readFile(file);

        # 是否为子目录设置SSL
        # if hasattr(get,'binding'):
        #    allconf = conf;
        #    conf = re.search("#BINDING-"+get.binding+"-START(.|\n)*#BINDING-"+get.binding+"-END",conf).group();

        if conf:
            if conf.find('ssl_certificate') == -1:
                sslStr = """#error_page 404/404.html;
    ssl_certificate    /www/server/panel/vhost/cert/%s/fullchain.pem;
    ssl_certificate_key    /www/server/panel/vhost/cert/%s/privkey.pem;
    ssl_protocols TLSv1 TLSv1.1 TLSv1.2%s;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:HIGH:!aNULL:!MD5:!RC4:!DHE;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    error_page 497  https://$host$request_uri;
""" % (get.first_domain, get.first_domain,self.get_tls13());
                if (conf.find('ssl_certificate') != -1):
                    return public.returnMsg(True, 'SITE_SSL_OPEN_SUCCESS');

                conf = conf.replace('#error_page 404/404.html;', sslStr);
                # 添加端口
                rep = "listen\s+([0-9]+)\s*[default_server]*;";
                tmp = re.findall(rep, conf);
                if not public.inArray(tmp, '443'):
                    listen = re.search(rep,conf).group()
                    versionStr = public.readFile('/www/server/nginx/version.pl');
                    http2 = ''
                    if versionStr:
                        if versionStr.find('1.8.1') == -1: http2 = ' http2';
                    default_site = '';
                    if conf.find('default_server') != -1: default_site = ' default_server'

                    listen_ipv6 = ';'
                    if self.is_ipv6: listen_ipv6 = ";\n\tlisten [::]:443 ssl"+http2+default_site+";"
                    conf = conf.replace(listen,listen + "\n\tlisten 443 ssl"+http2 + default_site + listen_ipv6)
                shutil.copyfile(file, self.nginx_conf_bak)
                public.writeFile(file, conf)

        # Apache配置
        file = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf';
        conf = public.readFile(file);
        if conf:
            ap_proxy = self.get_apache_proxy(conf)
            if conf.find('SSLCertificateFile') == -1:
                find = public.M('sites').where("name=?", (siteName,)).field('id,path').find()
                tmp = public.M('domain').where('pid=?', (find['id'],)).field('name').select()
                domains = ''
                for key in tmp:
                    domains += key['name'] + ' '
                path = (find['path'] + '/' + self.GetRunPath(get)).replace('//', '/');
                index = 'index.php index.html index.htm default.php default.html default.htm'

                try:
                    httpdVersion = public.readFile(self.setupPath + '/apache/version.pl').strip()
                except:
                    httpdVersion = "";
                if httpdVersion == '2.2':
                    vName = "";
                    phpConfig = "";
                    apaOpt = "Order allow,deny\n\t\tAllow from all";
                else:
                    vName = "";
                    rep = "php-cgi-([0-9]{2,3})\.sock";
                    version = re.search(rep, conf).groups()[0];
                    if len(version) < 2: return public.returnMsg(False, 'PHP_GET_ERR')
                    phpConfig = '''
    #PHP
    <FilesMatch \\.php$>
            SetHandler "proxy:unix:/tmp/php-cgi-%s.sock|fcgi://localhost"
    </FilesMatch>
    ''' % (version,);
                    apaOpt = 'Require all granted';

                sslStr = '''%s<VirtualHost *:443>
    ServerAdmin webmasterexample.com
    DocumentRoot "%s"
    ServerName SSL.%s
    ServerAlias %s
    #errorDocument 404 /404.html
    ErrorLog "%s-error_log"
    CustomLog "%s-access_log" combined
    %s
    #SSL
    SSLEngine On
    SSLCertificateFile /www/server/panel/vhost/cert/%s/fullchain.pem
    SSLCertificateKeyFile /www/server/panel/vhost/cert/%s/privkey.pem
    SSLCipherSuite EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH
    SSLProtocol All -SSLv2 -SSLv3
    SSLHonorCipherOrder On
    %s

    #DENY FILES
     <Files ~ (\.user.ini|\.htaccess|\.git|\.svn|\.project|LICENSE|README.md)$>
       Order allow,deny
       Deny from all
    </Files>

    #PATH
    <Directory "%s">
        SetOutputFilter DEFLATE
        Options FollowSymLinks
        AllowOverride All
        %s
        DirectoryIndex %s
    </Directory>
</VirtualHost>''' % (vName, path, siteName, domains, public.GetConfigValue('logs_path') + '/' + siteName, public.GetConfigValue('logs_path') + '/' + siteName ,ap_proxy ,get.first_domain, get.first_domain, phpConfig, path, apaOpt, index)

                conf = conf + "\n" + sslStr;
                self.apacheAddPort('443');
                shutil.copyfile(file, self.apache_conf_bak)
                public.writeFile(file, conf)

        isError = public.checkWebConfig();
        if (isError != True):
            if os.path.exists(self.nginx_conf_bak): shutil.copyfile(self.nginx_conf_bak, ng_file)
            if os.path.exists(self.apache_conf_bak): shutil.copyfile(self.apache_conf_bak, file)
            public.ExecShell("rm -f /tmp/backup_*.conf")
            return public.returnMsg(False, '证书错误: <br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>');

        sql = public.M('firewall');
        import firewalls
        get.port = '443'
        get.ps = 'HTTPS'
        firewalls.firewalls().AddAcceptPort(get)
        public.serviceReload();
        self.save_cert(get);
        public.WriteLog('TYPE_SITE', 'SITE_SSL_OPEN_SUCCESS', (siteName,));
        result = public.returnMsg(True, 'SITE_SSL_OPEN_SUCCESS');
        result['csr'] = public.readFile('/www/server/panel/vhost/cert/' + get.siteName + '/fullchain.pem');
        result['key'] = public.readFile( '/www/server/panel/vhost/cert/' + get.siteName + '/privkey.pem');
        return result

    def save_cert(self, get):
        # try:
        import panelSSL;
        ss = panelSSL.panelSSL();
        get.keyPath = '/www/server/panel/vhost/cert/' + get.siteName + '/privkey.pem';
        get.certPath = '/www/server/panel/vhost/cert/' + get.siteName + '/fullchain.pem';
        return ss.SaveCert(get);
        return True;
        # except:
        # return False;
    
    #HttpToHttps
    def HttpToHttps(self,get):
        siteName = get.siteName;
        #Nginx配置
        file = self.setupPath + '/panel/vhost/nginx/'+siteName+'.conf';
        conf = public.readFile(file);
        if conf:
            if conf.find('ssl_certificate') == -1: return public.returnMsg(False,'当前未开启SSL');
            to = """#error_page 404/404.html;
    #HTTP_TO_HTTPS_START
    if ($server_port !~ 443){
        rewrite ^(/.*)$ https://$host$1 permanent;
    }
    #HTTP_TO_HTTPS_END"""
            conf = conf.replace('#error_page 404/404.html;',to);
            public.writeFile(file,conf);
        
        file = self.setupPath + '/panel/vhost/apache/'+siteName+'.conf';
        conf = public.readFile(file);
        if conf:
            httpTohttos = '''combined
    #HTTP_TO_HTTPS_START
    <IfModule mod_rewrite.c>
        RewriteEngine on
        RewriteCond %{SERVER_PORT} !^443$
        RewriteRule (.*) https://%{SERVER_NAME}$1 [L,R=301]
    </IfModule>
    #HTTP_TO_HTTPS_END'''
            conf = re.sub('combined',httpTohttos,conf,1);
            public.writeFile(file,conf);
        public.serviceReload();
        return public.returnMsg(True,'SET_SUCCESS');
    
    #CloseToHttps
    def CloseToHttps(self,get):
        siteName = get.siteName;
        file = self.setupPath + '/panel/vhost/nginx/'+siteName+'.conf';
        conf = public.readFile(file);
        if conf:
            rep = "\n\s*#HTTP_TO_HTTPS_START(.|\n){1,300}#HTTP_TO_HTTPS_END";
            conf = re.sub(rep,'',conf);
            rep = "\s+if.+server_port.+\n.+\n\s+\s*}";
            conf = re.sub(rep,'',conf);
            public.writeFile(file,conf);
        
        file = self.setupPath + '/panel/vhost/apache/'+siteName+'.conf';
        conf = public.readFile(file);
        if conf:
            rep = "\n\s*#HTTP_TO_HTTPS_START(.|\n){1,300}#HTTP_TO_HTTPS_END";
            conf = re.sub(rep,'',conf);
            public.writeFile(file,conf);
        public.serviceReload();
        return public.returnMsg(True,'SET_SUCCESS');
    
    #是否跳转到https
    def IsToHttps(self,siteName):
        file = self.setupPath + '/panel/vhost/nginx/'+siteName+'.conf';
        conf = public.readFile(file);
        if conf:
            if conf.find('HTTP_TO_HTTPS_START') != -1: return True;
            if conf.find('$server_port !~ 443') != -1: return True;
        return False;
        
    # 清理SSL配置
    def CloseSSLConf(self, get):
        siteName = get.siteName

        file = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf';
        conf = public.readFile(file);
        if conf:
            rep = "\n\s*#HTTP_TO_HTTPS_START(.|\n){1,300}#HTTP_TO_HTTPS_END";
            conf = re.sub(rep, '', conf);
            rep = "\s+ssl_certificate\s+.+;\s+ssl_certificate_key\s+.+;";
            conf = re.sub(rep, '', conf);
            rep = "\s+ssl_protocols\s+.+;\n";
            conf = re.sub(rep, '', conf);
            rep = "\s+ssl_ciphers\s+.+;\n";
            conf = re.sub(rep, '', conf);
            rep = "\s+ssl_prefer_server_ciphers\s+.+;\n";
            conf = re.sub(rep, '', conf);
            rep = "\s+ssl_session_cache\s+.+;\n";
            conf = re.sub(rep, '', conf);
            rep = "\s+ssl_session_timeout\s+.+;\n";
            conf = re.sub(rep, '', conf);
            rep = "\s+ssl_ecdh_curve\s+.+;\n";
            conf = re.sub(rep, '', conf);
            rep = "\s+ssl_session_tickets\s+.+;\n";
            conf = re.sub(rep, '', conf);
            rep = "\s+ssl_stapling\s+.+;\n";
            conf = re.sub(rep, '', conf);
            rep = "\s+ssl_stapling_verify\s+.+;\n";
            conf = re.sub(rep, '', conf);
            rep = "\s+add_header\s+.+;\n";
            conf = re.sub(rep, '', conf);
            rep = "\s+add_header\s+.+;\n";
            conf = re.sub(rep, '', conf);
            rep = "\s+ssl\s+on;";
            conf = re.sub(rep, '', conf);
            rep = "\s+error_page\s497.+;";
            conf = re.sub(rep, '', conf);
            rep = "\s+if.+server_port.+\n.+\n\s+\s*}";
            conf = re.sub(rep, '', conf);
            rep = "\s+listen\s+443.*;";
            conf = re.sub(rep, '', conf);
            rep = "\s+listen\s+\[::\]:443.*;";
            conf = re.sub(rep, '', conf);
            public.writeFile(file, conf)

        file = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf';
        conf = public.readFile(file);
        if conf:
            rep = "\n<VirtualHost \*\:443>(.|\n)*<\/VirtualHost>";
            conf = re.sub(rep, '', conf);
            rep = "\n\s*#HTTP_TO_HTTPS_START(.|\n){1,250}#HTTP_TO_HTTPS_END";
            conf = re.sub(rep, '', conf);
            rep = "NameVirtualHost  *:443\n";
            conf = conf.replace(rep, '');
            public.writeFile(file, conf)

        partnerOrderId = '/www/server/panel/vhost/cert/' + siteName + '/partnerOrderId';
        if os.path.exists(partnerOrderId): public.ExecShell('rm -f ' + partnerOrderId);
        p_file = '/etc/letsencrypt/live/' + siteName + '/partnerOrderId'
        if os.path.exists(p_file): os.system('rm -f ' + p_file);

        public.WriteLog('TYPE_SITE', 'SITE_SSL_CLOSE_SUCCESS', (siteName,));
        public.serviceReload();
        return public.returnMsg(True, 'SITE_SSL_CLOSE_SUCCESS');

    # 取SSL状态
    def GetSSL(self, get):
        siteName = get.siteName
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
        if (conf.find(keyText) == -1):
            status = False
            type = -1

        toHttps = self.IsToHttps(siteName);
        id = public.M('sites').where("name=?", (siteName,)).getField('id');
        domains = public.M('domain').where("pid=?", (id,)).field('name').select();
        cert_data= {}
        if csr:
            get.certPath = csrpath
            import panelSSL
            cert_data = panelSSL.panelSSL().GetCertName(get)

        email = public.M('users').where('id=?',(1,)).getField('email')
        if email == '287962566@qq.com': email = ''
        return {'status': status, 'domain': domains, 'key': key, 'csr': csr, 'type': type, 'httpTohttps': toHttps,'cert_data':cert_data,'email':email}
    
    
    #启动站点
    def SiteStart(self,get):
        id = get.id
        Path = self.setupPath + '/stop';
        sitePath = public.M('sites').where("id=?",(id,)).getField('path');
        
        #nginx
        file = self.setupPath + '/panel/vhost/nginx/'+get.name+'.conf';
        conf = public.readFile(file);
        if conf:
            conf = conf.replace(Path, sitePath);
            public.writeFile(file,conf)
        #apaceh
        file = self.setupPath + '/panel/vhost/apache/'+get.name+'.conf';
        conf = public.readFile(file);
        if conf:
            conf = conf.replace(Path, sitePath);
            public.writeFile(file,conf)
        
        public.M('sites').where("id=?",(id,)).setField('status','1');
        public.serviceReload();
        public.WriteLog('TYPE_SITE','SITE_START_SUCCESS',(get.name,))
        return public.returnMsg(True,'SITE_START_SUCCESS')
    
    
    #停止站点
    def SiteStop(self,get):
        path = self.setupPath + '/stop';
        id = get.id
        if not os.path.exists(path):
            os.makedirs(path)
            public.downloadFile('http://download.bt.cn/stop.html',path + '/index.html');
        
        binding = public.M('binding').where('pid=?',(id,)).field('id,pid,domain,path,port,addtime').select();
        for b in binding:
            bpath = path + '/' + b['path'];
            if not os.path.exists(bpath): 
                public.ExecShell('mkdir -p ' + bpath);
                public.ExecShell('ln -sf ' + path + '/index.html ' + bpath + '/index.html');
        
        sitePath = public.M('sites').where("id=?",(id,)).getField('path');
        
        #nginx
        file = self.setupPath + '/panel/vhost/nginx/'+get.name+'.conf';
        conf = public.readFile(file);
        if conf:
            conf = conf.replace(sitePath,path);
            public.writeFile(file,conf)
        
        #apache
        file = self.setupPath + '/panel/vhost/apache/'+get.name+'.conf';
        conf = public.readFile(file);
        if conf:
            conf = conf.replace(sitePath,path);
            public.writeFile(file,conf)
        public.M('sites').where("id=?",(id,)).setField('status','0');
        public.serviceReload();
        public.WriteLog('TYPE_SITE','SITE_STOP_SUCCESS',(get.name,))
        return public.returnMsg(True,'SITE_STOP_SUCCESS')

    
    #取流量限制值
    def GetLimitNet(self,get):
        id = get.id
        
        #取回配置文件
        siteName = public.M('sites').where("id=?",(id,)).getField('name');
        filename = self.setupPath + '/panel/vhost/nginx/'+siteName+'.conf';
        
        #站点总并发
        data = {}
        conf = public.readFile(filename);
        try:
            rep = "\s+limit_conn\s+perserver\s+([0-9]+);";
            tmp = re.search(rep, conf).groups()
            data['perserver'] = int(tmp[0]);
            
            #IP并发限制
            rep = "\s+limit_conn\s+perip\s+([0-9]+);";
            tmp = re.search(rep, conf).groups()
            data['perip'] = int(tmp[0]);
            
            #请求并发限制
            rep = "\s+limit_rate\s+([0-9]+)\w+;";
            tmp = re.search(rep, conf).groups()
            data['limit_rate'] = int(tmp[0]);
        except:
            data['perserver'] = 0
            data['perip'] = 0
            data['limit_rate'] = 0
        
        return data;
    
    
    #设置流量限制
    def SetLimitNet(self,get):
        if(public.get_webserver() != 'nginx'): return public.returnMsg(False, 'SITE_NETLIMIT_ERR');
        
        id = get.id;
        perserver = 'limit_conn perserver ' + get.perserver + ';';
        perip = 'limit_conn perip ' + get.perip + ';';
        limit_rate = 'limit_rate ' + get.limit_rate + 'k;';
        
        #取回配置文件
        siteName = public.M('sites').where("id=?",(id,)).getField('name');
        filename = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf';
        conf = public.readFile(filename);
        
        #设置共享内存
        oldLimit = self.setupPath + '/panel/vhost/nginx/limit.conf';
        if(os.path.exists(oldLimit)): os.remove(oldLimit);
        limit = self.setupPath + '/nginx/conf/nginx.conf';
        nginxConf = public.readFile(limit);
        limitConf = "limit_conn_zone $binary_remote_addr zone=perip:10m;\n\t\tlimit_conn_zone $server_name zone=perserver:10m;";
        nginxConf = nginxConf.replace("#limit_conn_zone $binary_remote_addr zone=perip:10m;",limitConf);
        public.writeFile(limit,nginxConf)
        
        if(conf.find('limit_conn perserver') != -1):
            #替换总并发
            rep = "limit_conn\s+perserver\s+([0-9]+);";
            conf = re.sub(rep,perserver,conf);
            
            #替换IP并发限制
            rep = "limit_conn\s+perip\s+([0-9]+);";
            conf = re.sub(rep,perip,conf);
            
            #替换请求流量限制
            rep = "limit_rate\s+([0-9]+)\w+;";
            conf = re.sub(rep,limit_rate,conf);
        else:
            conf = conf.replace('#error_page 404/404.html;',"#error_page 404/404.html;\n    " + perserver + "\n    " + perip + "\n    " + limit_rate);
        
        
        import shutil
        shutil.copyfile(filename, self.nginx_conf_bak)
        public.writeFile(filename,conf)
        isError = public.checkWebConfig();
        if(isError != True):
            if os.path.exists(self.nginx_conf_bak): shutil.copyfile(self.nginx_conf_bak,filename)
            return public.returnMsg(False,'ERROR: <br><a style="color:red;">'+isError.replace("\n",'<br>')+'</a>');
        
        public.serviceReload();
        public.WriteLog('TYPE_SITE','SITE_NETLIMIT_OPEN_SUCCESS',(siteName,))
        return public.returnMsg(True, 'SET_SUCCESS');
    
    
    #关闭流量限制
    def CloseLimitNet(self,get):
        id = get.id
        #取回配置文件
        siteName = public.M('sites').where("id=?",(id,)).getField('name');
        filename = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf';
        conf = public.readFile(filename);
        #清理总并发
        rep = "\s+limit_conn\s+perserver\s+([0-9]+);";
        conf = re.sub(rep,'',conf);
        
        #清理IP并发限制
        rep = "\s+limit_conn\s+perip\s+([0-9]+);";
        conf = re.sub(rep,'',conf);
        
        #清理请求流量限制
        rep = "\s+limit_rate\s+([0-9]+)\w+;";
        conf = re.sub(rep,'',conf);
        public.writeFile(filename,conf)
        public.serviceReload();
        public.WriteLog('TYPE_SITE','SITE_NETLIMIT_CLOSE_SUCCESS',(siteName,))
        return public.returnMsg(True, 'SITE_NETLIMIT_CLOSE_SUCCESS');
    
    #取301配置状态
    def Get301Status(self,get):
        siteName = get.siteName
        result = {}
        domains = ''
        id = public.M('sites').where("name=?",(siteName,)).getField('id')
        tmp = public.M('domain').where("pid=?",(id,)).field('name').select()
        for key in tmp:
            domains += key['name'] + ','
        try:
            if(public.get_webserver() == 'nginx'):
                conf = public.readFile(self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf');
                if conf.find('301-START') == -1:
                    result['domain'] = domains[:-1]
                    result['src'] = "";
                    result['status'] = False
                    result['url'] = "http://";
                    return result;
                rep = "return\s+301\s+((http|https)\://.+);";
                arr = re.search(rep, conf).groups()[0];
                rep = "'\^(([\w-]+\.)+[\w-]+)'";
                tmp = re.search(rep, conf);
                src = ''
                if tmp : src = tmp.groups()[0]
            else:
                conf = public.readFile(self.setupPath + '/panel/vhost/apache/' + siteName + '.conf');
                if conf.find('301-START') == -1:
                    result['domain'] = domains[:-1]
                    result['src'] = "";
                    result['status'] = False
                    result['url'] = "http://";
                    return result;
                rep = "RewriteRule\s+.+\s+((http|https)\://.+)\s+\[";
                arr = re.search(rep, conf).groups()[0];
                rep = "\^((\w+\.)+\w+)\s+\[NC";
                tmp = re.search(rep, conf);
                src = ''
                if tmp : src = tmp.groups()[0]
        except:
            src = ''
            arr = 'http://'
            
        result['domain'] = domains[:-1]
        result['src'] = src.replace("'", '');
        result['status'] = True
        if(len(arr) < 3): result['status'] = False
        result['url'] = arr;
        
        return result
    
    
    #设置301配置
    def Set301Status(self,get):
        siteName = get.siteName
        srcDomain = get.srcDomain
        toDomain = get.toDomain
        type = get.type
        rep = "(http|https)\://.+";
        if not re.match(rep, toDomain):    return public.returnMsg(False,'Url地址不正确!');
        
        
        #nginx
        filename = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf';
        mconf = public.readFile(filename);
        if mconf:
            if(srcDomain == 'all'):
                conf301 = "\t#301-START\n\t\treturn 301 "+toDomain+"$request_uri;\n\t#301-END";
            else:
                conf301 = "\t#301-START\n\t\tif ($host ~ '^"+srcDomain+"'){\n\t\t\treturn 301 "+toDomain+"$request_uri;\n\t\t}\n\t#301-END";
            if type == '1': 
                mconf = mconf.replace("#error_page 404/404.html;","#error_page 404/404.html;\n"+conf301)
            else:
                rep = "\s+#301-START(.|\n){1,300}#301-END";
                mconf = re.sub(rep, '', mconf);
            
            public.writeFile(filename,mconf)
        
        
        #apache
        filename = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf';
        mconf = public.readFile(filename);
        if type == '1': 
            if(srcDomain == 'all'):
                conf301 = "\n\t#301-START\n\t<IfModule mod_rewrite.c>\n\t\tRewriteEngine on\n\t\tRewriteRule ^(.*)$ "+toDomain+"$1 [L,R=301]\n\t</IfModule>\n\t#301-END\n";
            else:
                conf301 = "\n\t#301-START\n\t<IfModule mod_rewrite.c>\n\t\tRewriteEngine on\n\t\tRewriteCond %{HTTP_HOST} ^"+srcDomain+" [NC]\n\t\tRewriteRule ^(.*) "+toDomain+"$1 [L,R=301]\n\t</IfModule>\n\t#301-END\n";
            rep = "combined"
            mconf = mconf.replace(rep,rep + "\n\t" + conf301);
        else:
            rep = "\n\s+#301-START(.|\n){1,300}#301-END\n*";
            mconf = re.sub(rep, '\n\n', mconf,1);
            mconf = re.sub(rep, '\n\n', mconf,1);
        
        public.writeFile(filename,mconf)
        
        
        isError = public.checkWebConfig();
        if(isError != True):
            return public.returnMsg(False,'ERROR: <br><a style="color:red;">'+isError.replace("\n",'<br>')+'</a>');
        
        public.serviceReload();
        return public.returnMsg(True,'SUCCESS');
    
    #取子目录绑定
    def GetDirBinding(self,get):
        path = public.M('sites').where('id=?',(get.id,)).getField('path')
        if not os.path.exists(path): 
            checks = ['/','/usr','/etc']
            if path in checks: 
                data = {}
                data['dirs'] = []
                data['binding'] = []
                return data;
            os.system('mkdir -p ' + path);
            os.system('chmod 755 ' + path);
            os.system('chown www:www ' + path);
            siteName = public.M('sites').where('id=?',(get.id,)).getField('name')
            public.WriteLog('网站管理','站点['+siteName+'],根目录['+path+']不存在,已重新创建!');
        dirnames = []
        for filename in os.listdir(path):
            try:
                filePath = path + '/' + filename
                if os.path.islink(filePath): continue
                if os.path.isdir(filePath):
                    dirnames.append(filename)
            except:
                pass
        
        data = {}
        data['dirs'] = dirnames
        data['binding'] = public.M('binding').where('pid=?',(get.id,)).field('id,pid,domain,path,port,addtime').select()
        return data
    
    #添加子目录绑定
    def AddDirBinding(self,get):
        import shutil
        id = get.id
        tmp = get.domain.split(':')
        domain = tmp[0].lower();
        port = '80'
        if len(tmp) > 1: port = tmp[1];
        if not hasattr(get,'dirName'): public.returnMsg(False, 'DIR_EMPTY');
        dirName = get.dirName; 
        
        reg = "^([\w\-\*]{1,100}\.){1,4}(\w{1,10}|\w{1,10}\.\w{1,10})$";
        if not re.match(reg, domain): return public.returnMsg(False,'SITE_ADD_ERR_DOMAIN');
        
        siteInfo = public.M('sites').where("id=?",(id,)).field('id,path,name').find();
        webdir = siteInfo['path'] + '/' + dirName;
        sql = public.M('binding');
        if sql.where("domain=?",(domain,)).count() > 0: return public.returnMsg(False, 'SITE_ADD_ERR_DOMAIN_EXISTS');
        if public.M('domain').where("name=?",(domain,)).count() > 0: return public.returnMsg(False, 'SITE_ADD_ERR_DOMAIN_EXISTS');
        
        filename = self.setupPath + '/panel/vhost/nginx/' + siteInfo['name'] + '.conf';
        nginx_conf_file = filename
        conf = public.readFile(filename);
        if conf:
            listen_ipv6 = ''
            if self.is_ipv6: listen_ipv6 = "\n    listen [::]:%s;" % port
            rep = "enable-php-([0-9]{2,3})\.conf";
            tmp = re.search(rep,conf).groups()
            version = tmp[0];
            bindingConf ='''
#BINDING-%s-START
server
{
    listen %s;%s
    server_name %s;
    index index.php index.html index.htm default.php default.htm default.html;
    root %s;
    
    include enable-php-%s.conf;
    include %s/panel/vhost/rewrite/%s.conf;
    #禁止访问的文件或目录
    location ~ ^/(\.user.ini|\.htaccess|\.git|\.svn|\.project|LICENSE|README.md)
    {
        return 404;
    }
    
    #一键申请SSL证书验证目录相关设置
    location ~ \.well-known{
        allow all;
    }
    
    location ~ .*\\.(gif|jpg|jpeg|png|bmp|swf)$
    {
        expires      30d;
        error_log off;
        access_log /dev/null; 
    }
    location ~ .*\\.(js|css)?$
    {
        expires      12h;
        error_log off;
        access_log /dev/null; 
    }
    access_log %s.log;
    error_log  %s.error.log;
}
#BINDING-%s-END''' % (domain,port,listen_ipv6,domain,webdir,version,self.setupPath,siteInfo['name'],public.GetConfigValue('logs_path')+'/'+siteInfo['name'],public.GetConfigValue('logs_path')+'/'+siteInfo['name'],domain)
            
            conf += bindingConf
            shutil.copyfile(filename, self.nginx_conf_bak)
            public.writeFile(filename,conf)
            
            
            
        filename = self.setupPath + '/panel/vhost/apache/' + siteInfo['name'] + '.conf';
        conf = public.readFile(filename);
        if conf:
            try:
                try:
                    httpdVersion = public.readFile(self.setupPath+'/apache/version.pl').strip();
                except:
                    httpdVersion = "";
                if httpdVersion == '2.2':
                    phpConfig = "";
                    apaOpt = "Order allow,deny\n\t\tAllow from all";
                else:
                    rep = "php-cgi-([0-9]{2,3})\.sock";
                    tmp = re.search(rep,conf).groups()
                    version = tmp[0];
                    phpConfig ='''
    #PHP     
    <FilesMatch \\.php>
        SetHandler "proxy:unix:/tmp/php-cgi-%s.sock|fcgi://localhost"
    </FilesMatch>
    ''' % (version,)
                    apaOpt = 'Require all granted';
            
                bindingConf ='''
\n#BINDING-%s-START
<VirtualHost *:%s>
    ServerAdmin webmaster@example.com
    DocumentRoot "%s"
    ServerName %s
    #errorDocument 404 /404.html
    ErrorLog "%s-error_log"
    CustomLog "%s-access_log" combined
    %s
    
    #DENY FILES
     <Files ~ (\.user.ini|\.htaccess|\.git|\.svn|\.project|LICENSE|README.md)$>
       Order allow,deny
       Deny from all
    </Files>
    
    #PATH
    <Directory "%s">
        SetOutputFilter DEFLATE
        Options FollowSymLinks
        AllowOverride All
        %s
        DirectoryIndex index.php index.html index.htm default.php default.html default.htm
    </Directory>
</VirtualHost>
#BINDING-%s-END''' % (domain,port,webdir,domain,public.GetConfigValue('logs_path')+'/'+siteInfo['name'],public.GetConfigValue('logs_path')+'/'+siteInfo['name'],phpConfig,webdir,apaOpt,domain)
                
                conf += bindingConf;
                shutil.copyfile(filename, self.apache_conf_bak)
                public.writeFile(filename,conf)
            except:
                pass
        
        #检查配置是否有误
        isError = public.checkWebConfig()
        if isError != True:
            if os.path.exists(self.nginx_conf_bak): shutil.copyfile(self.nginx_conf_bak,nginx_conf_file)
            if os.path.exists(self.apache_conf_bak): shutil.copyfile(self.apache_conf_bak,filename)
            return public.returnMsg(False,'ERROR: <br><a style="color:red;">'+isError.replace("\n",'<br>')+'</a>');
            
        public.M('binding').add('pid,domain,port,path,addtime',(id,domain,port,dirName,public.getDate()));
        public.serviceReload();
        public.WriteLog('TYPE_SITE', 'SITE_BINDING_ADD_SUCCESS',(siteInfo['name'],dirName,domain));
        return public.returnMsg(True, 'ADD_SUCCESS');
    
    #删除子目录绑定
    def DelDirBinding(self,get):
        id = get.id
        binding = public.M('binding').where("id=?",(id,)).field('id,pid,domain,path').find();
        siteName = public.M('sites').where("id=?",(binding['pid'],)).getField('name');
        
        #nginx
        filename = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf';
        conf = public.readFile(filename);
        if conf:
            rep = "\s*.+BINDING-" + binding['domain'] + "-START(.|\n)+BINDING-" + binding['domain'] + "-END";
            conf = re.sub(rep, '', conf);
            public.writeFile(filename,conf)
        
        #apache
        filename = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf';
        conf = public.readFile(filename);
        if conf:
            rep = "\s*.+BINDING-" + binding['domain'] + "-START(.|\n)+BINDING-" + binding['domain'] + "-END";
            conf = re.sub(rep, '', conf);
            public.writeFile(filename,conf)
        
        public.M('binding').where("id=?",(id,)).delete();
        filename = self.setupPath + '/panel/vhost/rewrite/' + siteName + '_' + binding['path'] + '.conf';
        if os.path.exists(filename): os.remove(filename)
        public.serviceReload();
        public.WriteLog('TYPE_SITE', 'SITE_BINDING_DEL_SUCCESS',(siteName,binding['path']));
        return public.returnMsg(True,'DEL_SUCCESS')
    
    #取默认文档
    #取子目录Rewrite
    def GetDirRewrite(self,get):
        id = get.id;
        find = public.M('binding').where("id=?",(id,)).field('id,pid,domain,path').find();
        site = public.M('sites').where("id=?",(find['pid'],)).field('id,name,path').find();
        
        if(public.get_webserver() == 'apache'):
            filename = site['path']+'/'+find['path']+'/.htaccess';
        else:
            filename = self.setupPath + '/panel/vhost/rewrite/'+site['name']+'_'+find['path']+'.conf';
        
        if hasattr(get,'add'):
            public.writeFile(filename,'')
            if public.get_webserver() == 'nginx':
                file = self.setupPath + '/panel/vhost/nginx/'+site['name']+'.conf';
                conf = public.readFile(file);
                domain = find['domain'];
                rep = "\n#BINDING-"+domain+"-START(.|\n)+BINDING-"+domain+"-END";
                tmp = re.search(rep, conf).group();
                dirConf = tmp.replace('rewrite/'+site['name']+'.conf;', 'rewrite/'+site['name']+'_'+find['path']+'.conf;');
                conf = conf.replace(tmp, dirConf);
                public.writeFile(file,conf)
        data = {}
        data['status'] = False;
        if os.path.exists(filename):
            data['status'] = True;
            data['data'] = public.readFile(filename);
            data['rlist'] = []
            for ds in os.listdir('rewrite/' + public.get_webserver()):
                if ds == 'list.txt': continue;
                data['rlist'].append(ds[0:len(ds)-5]);
            data['filename'] = filename;
        return data
    
    #取默认文档
    def GetIndex(self,get):
        id = get.id;
        Name = public.M('sites').where("id=?",(id,)).getField('name');
        file = self.setupPath + '/panel/vhost/'+public.get_webserver()+'/' + Name + '.conf';
        conf = public.readFile(file)
        if public.get_webserver() == 'nginx':
            rep = "\s+index\s+(.+);";
        else:
            rep = "DirectoryIndex\s+(.+)\n";
            
        tmp = re.search(rep,conf).groups()
        return tmp[0].replace(' ',',')
    
    #设置默认文档
    def SetIndex(self,get):
        id = get.id;
        if get.Index.find('.') == -1: return public.returnMsg(False,  'SITE_INDEX_ERR_FORMAT')
        
        Index = get.Index.replace(' ', '')
        Index = get.Index.replace(',,', ',')
        
        if len(Index) < 3: return public.returnMsg(False,  'SITE_INDEX_ERR_EMPTY')
        
        
        Name = public.M('sites').where("id=?",(id,)).getField('name');
        #准备指令
        Index_L = Index.replace(",", " ");
        
        #nginx
        file = self.setupPath + '/panel/vhost/nginx/' + Name + '.conf';
        conf = public.readFile(file);
        if conf:
            rep = "\s+index\s+.+;";
            conf = re.sub(rep,"\n\tindex " + Index_L + ";",conf);
            public.writeFile(file,conf);
        
        #apache
        file = self.setupPath + '/panel/vhost/apache/' + Name + '.conf';
        conf = public.readFile(file);
        if conf:
            rep = "DirectoryIndex\s+.+\n";
            conf = re.sub(rep,'DirectoryIndex ' + Index_L + "\n",conf);
            public.writeFile(file,conf);
        
        public.serviceReload();
        public.WriteLog('TYPE_SITE', 'SITE_INDEX_SUCCESS',(Name,Index_L));
        return public.returnMsg(True,  'SET_SUCCESS')
    
    #修改物理路径
    def SetPath(self,get):
        id = get.id
        Path = self.GetPath(get.path);
        if Path == "" or id == '0': return public.returnMsg(False,  "DIR_EMPTY");
        
        import files
        if not files.files().CheckDir(Path) or not self.__check_site_path(Path): return public.returnMsg(False,  "PATH_ERROR");
        
        SiteFind = public.M("sites").where("id=?",(id,)).field('path,name').find();
        if SiteFind["path"] == Path: return public.returnMsg(False,  "SITE_PATH_ERR_RE");
        Name = SiteFind['name'];
        file = self.setupPath + '/panel/vhost/nginx/' + Name + '.conf';
        conf = public.readFile(file);
        if conf:
            conf = conf.replace(SiteFind['path'],Path );
            public.writeFile(file,conf);
        
        file = self.setupPath + '/panel/vhost/apache/' + Name + '.conf';
        conf = public.readFile(file);
        if conf:
            rep = "DocumentRoot\s+.+\n";
            conf = re.sub(rep,'DocumentRoot "' + Path + '"\n',conf);
            rep = "<Directory\s+.+\n";
            conf = re.sub(rep,'<Directory "' + Path + "\">\n",conf);
            public.writeFile(file,conf);
        
        #创建basedir
        userIni = Path + '/.user.ini'
        if os.path.exists(userIni): public.ExecShell("chattr -i "+userIni);
        public.writeFile(userIni, 'open_basedir='+Path+'/:/tmp/:/proc/')
        public.ExecShell('chmod 644 ' + userIni)
        public.ExecShell('chown root:root ' + userIni)
        public.ExecShell('chattr +i '+userIni)
        
        public.serviceReload();
        public.M("sites").where("id=?",(id,)).setField('path',Path);
        public.WriteLog('TYPE_SITE', 'SITE_PATH_SUCCESS',(Name,));
        return public.returnMsg(True,  "SET_SUCCESS");
    
    #取当前可用PHP版本
    def GetPHPVersion(self,get):
        phpVersions = ('00','52','53','54','55','56','70','71','72','73','74')
        httpdVersion = "";
        filename = self.setupPath+'/apache/version.pl';
        if os.path.exists(filename): httpdVersion = public.readFile(filename).strip()
        
        if httpdVersion == '2.2': phpVersions = ('00','52','53','54')
        if httpdVersion == '2.4': phpVersions = ('00','53','54','55','56','70','71','72','73','74')
        if os.path.exists('/www/server/nginx/sbin/nginx'):
            cfile = '/www/server/nginx/conf/enable-php-00.conf'
            if not os.path.exists(cfile): public.writeFile(cfile,'');
        
        data = []
        for val in phpVersions:
            tmp = {}
            checkPath = self.setupPath+'/php/'+val+'/bin/php';
            if val == '00': checkPath = '/etc/init.d/bt';
            if httpdVersion == '2.2': checkPath = self.setupPath+'/php/'+val+'/libphp5.so';
            if os.path.exists(checkPath):
                tmp['version'] = val;
                tmp['name'] = 'PHP-'+val;
                if val == '00': tmp['name'] = '纯静态';
                data.append(tmp)
        return data
    
    
    #取指定站点的PHP版本
    def GetSitePHPVersion(self,get):
        try:
            siteName = get.siteName;
            conf = public.readFile(self.setupPath + '/panel/vhost/'+public.get_webserver()+'/'+siteName+'.conf');
            if public.get_webserver() == 'nginx':
                rep = "enable-php-([0-9]{2,3})\.conf"
            else:
                rep = "php-cgi-([0-9]{2,3})\.sock";
            tmp = re.search(rep,conf).groups()
            data = {}
            data['phpversion'] = tmp[0];
            data['tomcat'] = conf.find('#TOMCAT-START');
            data['tomcatversion'] = public.readFile(self.setupPath + '/tomcat/version.pl');
            data['nodejs'] = conf.find('#NODE.JS-START');
            data['nodejsversion'] = public.readFile(self.setupPath + '/node.js/version.pl');
            return data;
        except:
            return public.returnMsg(False,'SITE_PHPVERSION_ERR_A22');
    
    #设置指定站点的PHP版本
    def SetPHPVersion(self,get):
        siteName = get.siteName
        version = get.version
        
        #nginx
        file = self.setupPath + '/panel/vhost/nginx/'+siteName+'.conf';
        conf = public.readFile(file);
        if conf:
            rep = "enable-php-([0-9]{2,3})\.conf";
            tmp = re.search(rep,conf).group()
            conf = conf.replace(tmp,'enable-php-'+version+'.conf');
            public.writeFile(file,conf)
        
        #apache
        file = self.setupPath + '/panel/vhost/apache/'+siteName+'.conf';
        conf = public.readFile(file);
        if conf:
            rep = "php-cgi-([0-9]{2,3})\.sock";
            tmp = re.search(rep,conf).group()
            conf = conf.replace(tmp,'php-cgi-'+version+'.sock');
            public.writeFile(file,conf)
        
        public.serviceReload();
        public.WriteLog("TYPE_SITE", "SITE_PHPVERSION_SUCCESS",(siteName,version));
        return public.returnMsg(True,'SITE_PHPVERSION_SUCCESS',(siteName,version));

    
    #是否开启目录防御
    def GetDirUserINI(self,get):
        path = get.path + self.GetRunPath(get);
        id = get.id;
        get.name = public.M('sites').where("id=?",(id,)).getField('name');
        data = {}
        data['logs'] = self.GetLogsStatus(get);
        data['userini'] = False;
        if os.path.exists(path+'/.user.ini'):
            data['userini'] = True;
        data['runPath'] = self.GetSiteRunPath(get);
        data['pass'] = self.GetHasPwd(get);
        return data;
    
    #清除多余user.ini
    def DelUserInI(self,path,up = 0):
        useriniPath = path + '/.user.ini'
        if os.path.exists(useriniPath):
            public.ExecShell('chattr -i ' + useriniPath);
            os.remove(useriniPath)

        for p1 in os.listdir(path):
            try:
                npath = path + '/' + p1;
                if not os.path.isdir(npath): continue
                useriniPath = npath + '/.user.ini';
                if os.path.exists(useriniPath): 
                    public.ExecShell('chattr -i ' + useriniPath);
                    os.remove(useriniPath)
                if up < 3: self.DelUserInI(npath, up + 1);
            except: continue
        return True;
            
            
    #设置目录防御
    def SetDirUserINI(self,get):
        path = get.path
        runPath = self.GetRunPath(get)
        filename = path+runPath+'/.user.ini';
        if os.path.exists(filename):
            public.ExecShell("chattr -i "+filename);
            os.remove(filename)
            return public.returnMsg(True, 'SITE_BASEDIR_CLOSE_SUCCESS');

        if len(runPath) > 1: 
            self.DelUserInI(path + runPath);
        else:
            self.DelUserInI(path);
        
        public.writeFile(filename, 'open_basedir='+path+'/:/tmp/:/proc/');
        public.ExecShell("chattr +i "+filename);
        
        return public.returnMsg(True,'SITE_BASEDIR_OPEN_SUCCESS');



       # 读配置
    def __read_config(self, path):
        if not os.path.exists(path):
            public.writeFile(path, '[]')
        upBody = public.readFile(path)
        if not upBody: upBody = '[]'
        return json.loads(upBody)

        # 写配置
    def __write_config(self, path, data):
        return public.writeFile(path, json.dumps(data))

        # 取某个站点某条反向代理详情
    def GetProxyDetals(self, get):
        proxyUrl = self.__read_config(self.__proxyfile)
        sitename = get.sitename
        proxyname = get.proxyname
        for i in proxyUrl:
            if i["proxyname"] == proxyname and i["sitename"] == sitename:
                return i

    # 取某个站点反向代理列表
    def GetProxyList(self, get):
        n = 0
        for w in ["nginx", "apache"]:
            conf_path = "%s/panel/vhost/%s/%s.conf" % (self.setupPath, w, get.sitename)
            old_conf = public.readFile(conf_path)
            rep = "(#PROXY-START(\n|.)+#PROXY-END)"
            url_rep = "proxy_pass (.*);|ProxyPass\s/\s(.*)|Host\s(.*);"
            host_rep = "Host\s(.*);"
            if re.search(rep, old_conf):
                # 构造代理配置
                if w == "nginx":
                    get.todomain = str(re.search(host_rep, old_conf).group(1))
                    get.proxysite = str(re.search(url_rep, old_conf).group(1))
                else:
                    get.todomain = ""
                    get.proxysite = str(re.search(url_rep, old_conf).group(2))
                get.proxyname = "旧代理"
                get.type = 1
                get.proxydir = "/"
                get.advanced = 0
                get.cachetime = 1
                get.cache = 0
                get.subfilter = "[{\"sub1\":\"\",\"sub2\":\"\"},{\"sub1\":\"\",\"sub2\":\"\"},{\"sub1\":\"\",\"sub2\":\"\"}]"

                #proxyname_md5 = self.__calc_md5(get.proxyname)
                # 备份并替换老虚拟主机配置文件
                os.system("cp %s %s_bak" % (conf_path, conf_path))
                conf = re.sub(rep, "", old_conf)
                public.writeFile(conf_path, conf)
                if n == 0:
                    self.CreateProxy(get)
                n += 1
                # 写入代理配置
                #proxypath = "%s/panel/vhost/%s/proxy/%s/%s_%s.conf" % (
                #self.setupPath, w, get.sitename, proxyname_md5, get.sitename)
                # proxycontent = str(re.search(rep, old_conf).group(1))
                # public.writeFile(proxypath, proxycontent)
            if n == "1":
                public.serviceReload()
        proxyUrl = self.__read_config(self.__proxyfile)
        sitename = get.sitename
        proxylist = []
        for i in proxyUrl:
            if i["sitename"] == sitename:
                proxylist.append(i)
        return proxylist


    # 删除反向代理
    def RemoveProxy(self, get):
        proxyUrl = self.__read_config(self.__proxyfile)
        sitename = get.sitename
        proxyname = get.proxyname
        for i in range(len(proxyUrl)):
            if proxyUrl[i]["sitename"] == sitename and proxyUrl[i]["proxyname"] == proxyname:
                proxyname_md5 = self.__calc_md5(proxyUrl[i]["proxyname"])
                os.system("rm -f %s/panel/vhost/nginx/proxy/%s/%s_%s.conf" % (self.setupPath,proxyUrl[i]["sitename"],proxyname_md5,proxyUrl[i]["sitename"]))
                os.system("rm -f %s/panel/vhost/apache/proxy/%s/%s_%s.conf" % (self.setupPath,proxyUrl[i]["sitename"],proxyname_md5, proxyUrl[i]["sitename"]))
                del proxyUrl[i]
                self.__write_config(self.__proxyfile,proxyUrl)
                self.SetNginx(get)
                self.SetApache(get.sitename)
                public.serviceReload()
                return public.returnMsg(True, '删除成功')


    # 检查代理是否存在
    def __check_even(self,get,action=""):
        conf_data = self.__read_config(self.__proxyfile)
        for i in conf_data:
            if i["sitename"] == get.sitename:
                if action == "create":
                    if  i["proxydir"] == get.proxydir or i["proxyname"] == get.proxyname:
                        return i
                else:
                    if i["proxyname"] != get.proxyname and i["proxydir"] == get.proxydir:
                        return i

    # 检测全局代理和目录代理是否同时存在
    def __check_proxy_even(self,get,action=""):
        conf_data = self.__read_config(self.__proxyfile)
        n = 0
        if action == "":
            for i in conf_data:
                if i["sitename"] == get.sitename:
                    n += 1
            if n == 1:
                return
        for i in conf_data:
            if i["sitename"] == get.sitename:
                if i["advanced"] != int(get.advanced):
                    return i
    # 计算proxyname md5
    def __calc_md5(self,proxyname):
        md5 = hashlib.md5()
        md5.update(proxyname.encode('utf-8'))
        return md5.hexdigest()

    # 检测URL是否可以访问
    def __CheckUrl(self, get):
        sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sk.settimeout(5)
        rep = "(https?)://([\w\.\-]+):?([\d]+)?"
        h = re.search(rep, get.proxysite).group(1)
        d = re.search(rep, get.proxysite).group(2)
        try:
            p = re.search(rep, get.proxysite).group(3)
        except:
            p = ""
        print(d, p)
        try:
            if p:
                sk.connect((d, int(p)))
                print (p)
            else:
                if h == "http":
                    sk.connect((d, 80))
                    print(80)
                else:
                    sk.connect((d, 443))
                    print(443)
        except:
            print("目标URL无法访问")
            return public.returnMsg(False, "目标URL无法访问")

    # 基本设置检查
    def __CheckStart(self,get,action=""):
        isError = public.checkWebConfig()
        if (isError != True):
            return public.returnMsg(False, '配置文件出错请先排查配置')
        if action == "create":
            if sys.version_info.major < 3:
                if len(get.proxyname) < 3 or len(get.proxyname) > 15:
                    print("名称必须大于3小于15个字符串")
                    return public.returnMsg(False, '名称必须大于3小于15个字符串')
            else:
                if len(get.proxyname.encode("utf-8")) < 3 or len(get.proxyname.encode("utf-8")) > 15:
                    print("名称必须大于3小于15个字符串")
                    return public.returnMsg(False, '名称必须大于3小于15个字符串')
        if self.__check_even(get,action):
            print("指定反向代理名称或代理文件夹已存在")
            return public.returnMsg(False, '指定反向代理名称或代理文件夹已存在')
        # 判断代理，只能有全局代理或目录代理
        if self.__check_proxy_even(get,action):
            print('不能同时设置目录代理和全局代理')
            return public.returnMsg(False, '不能同时设置目录代理和全局代理')
        #判断cachetime类型
        if get.cachetime:
            try:
                int(get.cachetime)
            except:
                return public.returnMsg(False, "请输入数字")

        rep = "http(s)?\:\/\/"
        repd = "http(s)?\:\/\/([a-zA-Z0-9][-a-zA-Z0-9]{0,62}\.)+([a-zA-Z0-9][a-zA-Z0-9]{0,62})+.?"
        tod = "[a-zA-Z]+$"
        repte = "[\?\=\[\]\)\(\*\&\^\%\$\#\@\!\~\`{\}\>\<\,\',\"]+"
        # 检测代理目录格式
        if re.search(repte,get.proxydir):
            print("代理目录不能有以下特殊符号 ?,=,[,],),(,*,&,^,%,$,#,@,!,~,`,{,},>,<,\,',\"]")
            return public.returnMsg(False, "代理目录不能有以下特殊符号 ?,=,[,],),(,*,&,^,%,$,#,@,!,~,`,{,},>,<,\,',\"]")
        # 检测发送域名格式
        if get.todomain:
            if not re.search(tod,get.todomain):
                return public.returnMsg(False, '发送域名格式错误 ' + get.todomain)
        else:
            get.todomain = "$host"

        # 检测目标URL格式
        if not re.match(rep, get.proxysite):
            return public.returnMsg(False, '域名格式错误 ' + get.proxysite)
        if re.search(repte,get.proxysite):
            print("目标URL不能有以下特殊符号 ?,=,[,],),(,*,&,^,%,$,#,@,!,~,`,{,},>,<,\,',\"]")
            return public.returnMsg(False, "目标URL不能有以下特殊符号 ?,=,[,],),(,*,&,^,%,$,#,@,!,~,`,{,},>,<,\,',\"]" )
        # 检测目标url是否可用
        # if re.match(repd, get.proxysite):
        #     if self.__CheckUrl(get):
        #         return public.returnMsg(False, "目标URL无法访问")
        subfilter = json.loads(get.subfilter)
        # 检测替换内容
        if subfilter:
            for s in subfilter:
                if not s["sub1"]:
                    if s["sub2"]:
                        print("请输入被替换的内容")
                        return public.returnMsg(False, '请输入被替换的内容')
                elif s["sub1"] == s["sub2"]:
                    print("替换内容与被替换内容不能一致")
                    return public.returnMsg(False, '替换内容与被替换内容不能一致')
    # 设置Nginx配置
    def SetNginx(self,get):
        ng_proxyfile = "%s/panel/vhost/nginx/proxy/%s/*.conf" % (self.setupPath,get.sitename)
        ng_file = self.setupPath + "/panel/vhost/nginx/" + get.sitename + ".conf"
        p_conf = self.__read_config(self.__proxyfile)
        cureCache = ''

        if public.get_webserver() == 'nginx':
            shutil.copyfile(ng_file, '/tmp/ng_file_bk.conf')

        #if os.path.exists('/www/server/nginx/src/ngx_cache_purge'):
        cureCache += '''
    location ~ /purge(/.*) {
        proxy_cache_purge cache_one $host$1$is_args$args;
        #access_log  /www/wwwlogs/%s_purge_cache.log;
    }''' % (get.sitename)
        if os.path.exists(ng_file):
            self.CheckProxy(get)
            ng_conf = public.readFile(ng_file)
            if not p_conf:
                rep = "#清理缓存规则[\w\s\~\/\(\)\.\*\{\}\;\$\n\#]+.{66,66}\n+[\s\w\/\*\.\;]+include enable-php-"
                ng_conf = re.sub(rep, 'include enable-php-', ng_conf)
                oldconf = '''location ~ .*\\.(gif|jpg|jpeg|png|bmp|swf)$
    {
        expires      30d;
        error_log off;
        access_log /dev/null;
    }
    location ~ .*\\.(js|css)?$
    {
        expires      12h;
        error_log off;
        access_log /dev/null;
    }'''
                ng_conf = ng_conf.replace('access_log', oldconf + "\n\taccess_log")
                public.writeFile(ng_file, ng_conf)
                return
            sitenamelist = []
            for i in p_conf:
                sitenamelist.append(i["sitename"])

            if get.sitename in sitenamelist:
                rep = "include.*\/proxy\/.*\*.conf;"
                if not re.search(rep,ng_conf):
                    rep = "location.+\(gif[\w\|\$\(\)\n\{\}\s\;\/\~\.\*\\\\\?]+access_log\s+/"
                    ng_conf = re.sub(rep, 'access_log  /', ng_conf)
                    ng_conf = ng_conf.replace("include enable-php-","#清理缓存规则\n" +cureCache +"\n\t#引用反向代理规则，注释后配置的反向代理将无效\n\t" + "include " + ng_proxyfile + ";\n\n\tinclude enable-php-")
                    public.writeFile(ng_file,ng_conf)

            else:
                rep =  "#清理缓存规则[\w\s\~\/\(\)\.\*\{\}\;\$\n\#]+.{66,66}\n+[\s\w\/\*\.\;]+include enable-php-"
                ng_conf = re.sub(rep,'include enable-php-',ng_conf)
                oldconf = '''location ~ .*\\.(gif|jpg|jpeg|png|bmp|swf)$
    {
        expires      30d;
        error_log off;
        access_log /dev/null;
    }
    location ~ .*\\.(js|css)?$
    {
        expires      12h;
        error_log off;
        access_log /dev/null;
    }'''
                ng_conf = ng_conf.replace('access_log', oldconf + "\n\taccess_log")
                public.writeFile(ng_file, ng_conf)

    # 设置apache配置
    def SetApache(self,sitename):
        ap_proxyfile = "%s/panel/vhost/apache/proxy/%s/*.conf" % (self.setupPath,sitename)
        ap_file = self.setupPath + "/panel/vhost/apache/" + sitename + ".conf"
        p_conf = public.readFile(self.__proxyfile)

        if public.get_webserver() == 'apache':
            shutil.copyfile(ap_file, '/tmp/ap_file_bk.conf')

        if os.path.exists(ap_file):
            ap_conf = public.readFile(ap_file)
            if p_conf == "[]":
                rep = "\n*#引用反向代理规则，注释后配置的反向代理将无效\n+\s+IncludeOptiona[\s\w\/\.\*]+"
                ap_conf = re.sub(rep, '', ap_conf)
                public.writeFile(ap_file, ap_conf)
                return
            if sitename in p_conf:
                rep = "combined(\n|.)+IncludeOptional.*\/proxy\/.*conf"
                rep1 = "combined"
                if not re.search(rep,ap_conf):
                    ap_conf = ap_conf.replace(rep1, rep1 + "\n\t#引用反向代理规则，注释后配置的反向代理将无效\n\t" + "\n\tIncludeOptional " + ap_proxyfile)
                    public.writeFile(ap_file,ap_conf)
            else:
                # rep = "\n*#引用反向代理(\n|.)+IncludeOptional.*\/proxy\/.*conf"
                rep = "\n*#引用反向代理规则，注释后配置的反向代理将无效\n+\s+IncludeOptiona[\s\w\/\.\*]+"
                ap_conf = re.sub(rep,'', ap_conf)
                public.writeFile(ap_file, ap_conf)

    # 检查伪静态、主配置文件是否有location冲突
    def CheckLocation(self,get):
        #伪静态文件路径
        rewriteconfpath = "%s/panel/vhost/rewrite/%s.conf" % (self.setupPath,get.sitename)
        # 主配置文件路径
        nginxconfpath = "%s/nginx/conf/nginx.conf" % (self.setupPath)													 
        # vhost文件
        vhostpath = "%s/panel/vhost/nginx/%s.conf" % (self.setupPath,get.sitename)

        rep = "location\s+/[\n\s]+{"

        for i in [rewriteconfpath,nginxconfpath,vhostpath]:
            conf = public.readFile(i)
            if re.findall(rep,conf):
                return public.returnMsg(False, '伪静态/nginx主配置/vhost/文件已经存在全局反向代理')

    # 创建反向代理
    def CreateProxy(self, get):
        try:
            nocheck = get.nocheck
        except:
            nocheck = ""
        if not nocheck:
            if self.__CheckStart(get,"create"):
                return self.__CheckStart(get,"create")
        if public.get_webserver() == 'nginx':
            if self.CheckLocation(get):
                return self.CheckLocation(get)

        proxyUrl = self.__read_config(self.__proxyfile)
        proxyUrl.append({
            "proxyname": get.proxyname,
            "sitename": get.sitename,
            "proxydir": get.proxydir,
            "proxysite": get.proxysite,
            "todomain": get.todomain,
            "type": int(get.type),
            "cache": int(get.cache),
            "subfilter": json.loads(get.subfilter),
            "advanced": int(get.advanced),
            "cachetime": int(get.cachetime)
        })
        self.__write_config(self.__proxyfile, proxyUrl)
        self.SetNginx(get)
        self.SetApache(get.sitename)
        self.SetProxy(get)
            # return public.returnMsg(False, '配置冲突')
        get.version = '00'
        get.siteName = get.sitename
        self.SetPHPVersion(get)
        public.serviceReload()
        print("添加成功")
        return public.returnMsg(True, '添加成功')

    # 取代理配置文件
    def GetProxyFile(self,get):
        import files
        conf = self.__read_config(self.__proxyfile)
        sitename = get.sitename
        proxyname = get.proxyname
        proxyname_md5 = self.__calc_md5(proxyname)
        get.path = "%s/panel/vhost/%s/proxy/%s/%s_%s.conf" % (self.setupPath, get.webserver, sitename,proxyname_md5,sitename)
        for i in conf:
            if proxyname == i["proxyname"] and sitename == i["sitename"] and i["type"] != 1:
                return public.returnMsg(False, '代理已暂停')
        f = files.files()
        return f.GetFileBody(get),get.path

    # 保存代理配置文件
    def SaveProxyFile(self,get):
        import files
        f = files.files()
        return f.SaveFileBody(get)
        #	return public.returnMsg(True, '保存成功')                                                                 


    # 修改反向代理
    def ModifyProxy(self, get):
        proxyname_md5 = self.__calc_md5(get.proxyname)
        ap_conf_file = "%s/panel/vhost/apache/proxy/%s/%s_%s.conf" % (
        self.setupPath, get.sitename, proxyname_md5, get.sitename)
        ng_conf_file = "%s/panel/vhost/nginx/proxy/%s/%s_%s.conf" % (
        self.setupPath, get.sitename, proxyname_md5, get.sitename)
        if self.__CheckStart(get):
            return self.__CheckStart(get)
        proxyUrl = self.__read_config(self.__proxyfile)
        for i in range(len(proxyUrl)):
            if proxyUrl[i]["proxyname"] == get.proxyname and proxyUrl[i]["sitename"] == get.sitename:
                if int(get.type) != 1:
                    os.system("mv %s %s_bak" % (ap_conf_file, ap_conf_file))
                    os.system("mv %s %s_bak" % (ng_conf_file, ng_conf_file))
                    proxyUrl[i]["type"] = int(get.type)
                    self.__write_config(self.__proxyfile, proxyUrl)
                    public.serviceReload()
                    return public.returnMsg(True, '修改成功')
                else:
                    if os.path.exists(ap_conf_file+"_bak"):
                        os.system("mv %s_bak %s" % (ap_conf_file, ap_conf_file))
                        os.system("mv %s_bak %s" % (ng_conf_file, ng_conf_file))
                    ng_conf = public.readFile(ng_conf_file)
                    # 修改nginx配置
                    ng_conf = re.sub("location\s+%s" % proxyUrl[i]["proxydir"],"location "+get.proxydir,ng_conf)
                    ng_conf = re.sub("proxy_pass\s+%s" % proxyUrl[i]["proxysite"],"proxy_pass "+get.proxysite,ng_conf)
                    ng_conf = re.sub("\sHost\s+%s" % proxyUrl[i]["todomain"]," Host "+get.todomain,ng_conf)
                    cache_rep = "proxy_cache_valid\s+200\s+304\s+301\s+302\s+"
                    if int(get.cache) == 1:
                        if re.search(cache_rep,ng_conf):
                            ng_conf = re.sub(cache_rep+"%sm;" % proxyUrl[i]["cachetime"], "proxy_cache_valid 200 304 301 302 %sm;" % get.cachetime, ng_conf)
                        else:
                            ng_cache = """
    proxy_cache cache_one;
    proxy_cache_key $host$uri$is_args$args;
    proxy_cache_valid 200 304 301 302 %sm;""" % (get.cachetime)
                            cache_rep = '#proxy_set_header\s+Connection\s+"upgrade";'
                            ng_conf = re.sub(cache_rep,'#proxy_set_header Connection "upgrade";\n'+ng_cache,ng_conf)
                    else:
                        rep = '\s+proxy_cache\s+cache_one.*[\n\s\w\_\";\$]+m;'
                        ng_conf = re.sub(rep, "", ng_conf)

                    sub_rep = "sub_filter"
                    subfilter = json.loads(get.subfilter)
                    if str(proxyUrl[i]["subfilter"]) != str(subfilter):
                        if re.search(sub_rep, ng_conf):
                            sub_rep = "\s+proxy_set_header\s+Accept-Encoding.*[\n\s\w\_\";]+off;"
                            ng_conf = re.sub(sub_rep,"",ng_conf)

                        # 构造替换字符串
                        ng_subdata = ''
                        ng_sub_filter = '''
    proxy_set_header Accept-Encoding "";%s
    sub_filter_once off;'''
                        if subfilter:
                            for s in subfilter:
                                if s["sub1"]:
                                    ng_subdata += '\n\tsub_filter "%s" "%s";' % (s["sub1"], s["sub2"])
                        if ng_subdata:
                            ng_sub_filter = ng_sub_filter % (ng_subdata)
                        else:
                            ng_sub_filter = ''
                        sub_rep = '#proxy_set_header\s+Connection\s+"upgrade";'
                        ng_conf = re.sub(sub_rep,'#proxy_set_header Connection "upgrade";\n'+ng_sub_filter,ng_conf)

                    # 修改apache配置
                    ap_conf = public.readFile(ap_conf_file)
                    ap_conf = re.sub("ProxyPass\s+%s\s+%s" % (proxyUrl[i]["proxydir"], proxyUrl[i]["proxysite"]),"ProxyPass %s %s" % (get.proxydir,get.proxysite), ap_conf)
                    ap_conf = re.sub("ProxyPassReverse\s+%s\s+%s" % (proxyUrl[i]["proxydir"], proxyUrl[i]["proxysite"]),
                                     "ProxyPassReverse %s %s" % (get.proxydir, get.proxysite), ap_conf)
                    proxyUrl[i]["proxydir"] = get.proxydir
                    proxyUrl[i]["proxysite"] = get.proxysite
                    proxyUrl[i]["todomain"] = get.todomain
                    proxyUrl[i]["type"] = int(get.type)
                    proxyUrl[i]["cache"] = int(get.cache)
                    proxyUrl[i]["subfilter"] = json.loads(get.subfilter)
                    proxyUrl[i]["advanced"] = int(get.advanced)
                    proxyUrl[i]["cachetime"] = int(get.cachetime)

                    public.writeFile(ng_conf_file,ng_conf)
                    public.writeFile(ap_conf_file,ap_conf)
                    self.__write_config(self.__proxyfile, proxyUrl)
                    self.SetNginx(get)
                    self.SetApache(get.sitename)
                    # self.SetProxy(get)


                    # if int(get.type) != 1:
                    #     os.system("mv %s %s_bak" % (ap_conf_file, ap_conf_file))
                    #     os.system("mv %s %s_bak" % (ng_conf_file, ng_conf_file))
                    public.serviceReload()
                    print("修改成功")
                    return public.returnMsg(True, '修改成功')






        # 设置反向代理
    def SetProxy(self,get):
        sitename = get.sitename  # 站点名称
        advanced = int(get.advanced)
        type = int(get.type)
        cache = int(get.cache)
        cachetime = int(get.cachetime)
        ng_file = self.setupPath + "/panel/vhost/nginx/" + sitename + ".conf"
        ap_file = self.setupPath + "/panel/vhost/apache/" + sitename + ".conf"
        p_conf = self.__read_config(self.__proxyfile)
        # 配置Nginx
        # 构造清理缓存连接


        # 构造缓存配置
        ng_cache = """
    proxy_cache cache_one;
    proxy_cache_key $host$uri$is_args$args;
    proxy_cache_valid 200 304 301 302 %sm;""" % (cachetime)
        rep = "(https?://[\w\.]+)"
        # proxysite1 = re.search(rep,get.proxysite).group(1)
        ng_proxy = '''
#PROXY-START%s
location %s
{
    expires 12h;
    if ($request_uri ~* "(php|jsp|cgi|asp|aspx)")
    {
         expires 0;
    }
    proxy_pass %s;
    proxy_set_header Host %s;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header REMOTE-HOST $remote_addr;
    
    %s
    #proxy_connect_timeout 30s;
    #proxy_read_timeout 86400s;
    #proxy_send_timeout 30s;
    #proxy_http_version 1.1;
    #proxy_set_header Upgrade $http_upgrade;
    #proxy_set_header Connection "upgrade";

    add_header X-Cache $upstream_cache_status;
    %s
    %s
}

#PROXY-END%s'''
        ng_proxy_cache = ''
        proxyname_md5 = self.__calc_md5(get.proxyname)
        ng_proxyfile = "%s/panel/vhost/nginx/proxy/%s/%s_%s.conf" % (self.setupPath,sitename,proxyname_md5, sitename)
        ng_proxydir = "%s/panel/vhost/nginx/proxy/%s" % (self.setupPath, sitename)
        if not os.path.exists(ng_proxydir):
            os.system("mkdir -p %s" % ng_proxydir)


        # 构造替换字符串
        ng_subdata = ''
        ng_sub_filter = '''
    proxy_set_header Accept-Encoding "";%s
    sub_filter_once off;'''
        if get.subfilter:
            for s in json.loads(get.subfilter):
                if s["sub1"]:
                    ng_subdata += '\n\tsub_filter "%s" "%s";' % (s["sub1"], s["sub2"])
        if ng_subdata:
            ng_sub_filter = ng_sub_filter % (ng_subdata)
        else:
            ng_sub_filter = ''
        # 构造反向代理
        if advanced == 1:
            if type == 1 and cache == 1:
                ng_proxy_cache += ng_proxy % (
                    get.proxydir, get.proxydir,get.proxysite, get.todomain, "#持久化连接相关配置" ,ng_sub_filter, ng_cache ,get.proxydir)
            if type == 1 and cache == 0:
                ng_proxy_cache += ng_proxy % (
                    get.proxydir, get.proxydir, get.proxysite, get.todomain, "#持久化连接相关配置" ,ng_sub_filter,'' ,get.proxydir)
        else:
            if type == 1 and cache == 1:
                ng_proxy_cache += ng_proxy % (
                    get.proxydir, get.proxydir, get.proxysite, get.todomain, "#持久化连接相关配置" ,ng_sub_filter, ng_cache, get.proxydir)
            if type == 1 and cache == 0:
                ng_proxy_cache += ng_proxy % (
                    get.proxydir, get.proxydir, get.proxysite, get.todomain, "#持久化连接相关配置" ,ng_sub_filter, '', get.proxydir)
        public.writeFile(ng_proxyfile, ng_proxy_cache)


        # APACHE
        # 反向代理文件
        ap_proxyfile = "%s/panel/vhost/apache/proxy/%s/%s_%s.conf" % (self.setupPath,get.sitename,proxyname_md5,get.sitename)
        ap_proxydir = "%s/panel/vhost/apache/proxy/%s" % (self.setupPath,get.sitename)
        if not os.path.exists(ap_proxydir):
            os.system("mkdir -p %s" % ap_proxydir)
        ap_proxy = ''
        if type == 1:
            ap_proxy += '''#PROXY-START%s
<IfModule mod_proxy.c>
    ProxyRequests Off
    SSLProxyEngine on
    ProxyPass %s %s/
    ProxyPassReverse %s %s/
    </IfModule>
#PROXY-END%s''' % (get.proxydir, get.proxydir, get.proxysite, get.proxydir,
                            get.proxysite, get.proxydir)
        public.writeFile(ap_proxyfile,ap_proxy)
        isError = public.checkWebConfig()
        if (isError != True):
            if public.get_webserver() == "nginx":
                shutil.copyfile('/tmp/ng_file_bk.conf', ng_file)
            else:
                shutil.copyfile('/tmp/ap_file_bk.conf', ap_file)
            for i in range(len(p_conf)-1,-1,-1):
                if get.sitename == p_conf[i]["sitename"] and p_conf[i]["proxyname"]:
                    del p_conf[i]
            return public.returnMsg(False, 'ERROR: %s<br><a style="color:red;">' % public.GetMsg("CONFIG_ERROR") + isError.replace("\n",
                                                                                                          '<br>') + '</a>')
        return public.returnMsg(True, 'SUCCESS')          
    
    
    #开启缓存
    def ProxyCache(self,get):
        if public.get_webserver() != 'nginx': return public.returnMsg(False,'WAF_NOT_NGINX');
        file = self.setupPath + "/panel/vhost/nginx/"+get.siteName+".conf";
        conf = public.readFile(file);
        if conf.find('proxy_pass') == -1: return public.returnMsg(False,'SET_ERROR');
        if conf.find('#proxy_cache') != -1:
            conf = conf.replace('#proxy_cache','proxy_cache');
            conf = conf.replace('#expires 12h','expires 12h');
        else:
            conf = conf.replace('proxy_cache','#proxy_cache');
            conf = conf.replace('expires 12h','#expires 12h');
        
        public.writeFile(file,conf);
        public.serviceReload();
        return public.returnMsg(True,'SET_SUCCESS');
    
    
    #检查反向代理配置
    def CheckProxy(self,get):
        if public.get_webserver() != 'nginx': return True;
        file = self.setupPath + "/nginx/conf/proxy.conf";
        if not os.path.exists(file):
            conf='''proxy_temp_path %s/nginx/proxy_temp_dir;
    proxy_cache_path %s/nginx/proxy_cache_dir levels=1:2 keys_zone=cache_one:10m inactive=1d max_size=5g;
    client_body_buffer_size 512k;
    proxy_connect_timeout 60;
    proxy_read_timeout 60;
    proxy_send_timeout 60;
    proxy_buffer_size 32k;
    proxy_buffers 4 64k;
    proxy_busy_buffers_size 128k;
    proxy_temp_file_write_size 128k;
    proxy_next_upstream error timeout invalid_header http_500 http_503 http_404;
    proxy_cache cache_one;''' % (self.setupPath,self.setupPath)
            public.writeFile(file,conf)
        
        
        file = self.setupPath + "/nginx/conf/nginx.conf";
        conf = public.readFile(file);
        if(conf.find('include proxy.conf;') == -1):
            rep = "include\s+mime.types;";
            conf = re.sub(rep, "include mime.types;\n\tinclude proxy.conf;", conf);
            public.writeFile(file,conf)
        
    
    #取伪静态规则应用列表
    def GetRewriteList(self,get):
        rewriteList = {}
        if public.get_webserver() == 'apache': 
            get.id = public.M('sites').where("name=?",(get.siteName,)).getField('id');
            runPath = self.GetSiteRunPath(get);
            rewriteList['sitePath'] = public.M('sites').where("name=?",(get.siteName,)).getField('path') + runPath['runPath'];
            
        rewriteList['rewrite'] = []
        rewriteList['rewrite'].append('0.'+public.getMsg('SITE_REWRITE_NOW'))
        for ds in os.listdir('rewrite/' + public.get_webserver()):
            if ds == 'list.txt': continue;
            rewriteList['rewrite'].append(ds[0:len(ds)-5]);
        rewriteList['rewrite'] = sorted(rewriteList['rewrite']);
        return rewriteList
    
    #保存伪静态模板
    def SetRewriteTel(self,get):
        get.name = get.name.encode('utf-8');
        filename = 'rewrite/' + public.get_webserver() + '/' + get.name + '.conf';
        public.writeFile(filename,get.data);
        return public.returnMsg(True, 'SITE_REWRITE_SAVE');
    
    #打包
    def ToBackup(self,get):
        id = get.id;
        find = public.M('sites').where("id=?",(id,)).field('name,path,id').find();
        import time
        fileName = find['name']+'_'+time.strftime('%Y%m%d_%H%M%S',time.localtime())+'.zip';
        backupPath = session['config']['backup_path'] + '/site'
        zipName = backupPath + '/'+fileName;
        if not (os.path.exists(backupPath)): os.makedirs(backupPath)
        tmps = '/tmp/panelExec.log'
        execStr = "cd '" + find['path'] + "' && zip '" + zipName + "' -x .user.ini -r ./ > " + tmps + " 2>&1"
        public.ExecShell(execStr)
        sql = public.M('backup').add('type,name,pid,filename,size,addtime',(0,fileName,find['id'],zipName,0,public.getDate()));
        public.WriteLog('TYPE_SITE', 'SITE_BACKUP_SUCCESS',(find['name'],));
        return public.returnMsg(True, 'BACKUP_SUCCESS');
    
    
    #删除备份文件
    def DelBackup(self,get):
        id = get.id
        where = "id=?";
        filename = public.M('backup').where(where,(id,)).getField('filename');
        if os.path.exists(filename): os.remove(filename)
        name = '';
        if filename == 'qiniu':
            name = public.M('backup').where(where,(id,)).getField('name');
            public.ExecShell("python "+self.setupPath + '/panel/script/backup_qiniu.py delete_file ' + name)
        
        public.WriteLog('TYPE_SITE', 'SITE_BACKUP_DEL_SUCCESS',(name,filename));
        public.M('backup').where(where,(id,)).delete();
        return public.returnMsg(True, 'DEL_SUCCESS');
    
    #旧版本配置文件处理
    def OldConfigFile(self):
        #检查是否需要处理
        moveTo = 'data/moveTo.pl';
        if os.path.exists(moveTo): return;
        
        #处理Nginx配置文件
        filename = self.setupPath + "/nginx/conf/nginx.conf"
        if os.path.exists(filename):
            conf = public.readFile(filename);
            if conf.find('include vhost/*.conf;') != -1:
                conf = conf.replace('include vhost/*.conf;','include ' + self.setupPath + '/panel/vhost/nginx/*.conf;');
                public.writeFile(filename,conf);
        
        self.moveConf(self.setupPath + "/nginx/conf/vhost", self.setupPath + '/panel/vhost/nginx','rewrite',self.setupPath+'/panel/vhost/rewrite');
        self.moveConf(self.setupPath + "/nginx/conf/rewrite", self.setupPath + '/panel/vhost/rewrite');
        
        
        
        #处理Apache配置文件
        filename = self.setupPath + "/apache/conf/httpd.conf"
        if os.path.exists(filename):
            conf = public.readFile(filename);
            if conf.find('IncludeOptional conf/vhost/*.conf') != -1:
                conf = conf.replace('IncludeOptional conf/vhost/*.conf','IncludeOptional ' + self.setupPath + '/panel/vhost/apache/*.conf');
                public.writeFile(filename,conf);
        
        self.moveConf(self.setupPath + "/apache/conf/vhost", self.setupPath + '/panel/vhost/apache');
        
        #标记处理记录
        public.writeFile(moveTo,'True');
        public.serviceReload();
        
    #移动旧版本配置文件
    def moveConf(self,Path,toPath,Replace=None,ReplaceTo=None):
        if not os.path.exists(Path): return;
        import shutil
        
        letPath = '/etc/letsencrypt/live';
        nginxPath = self.setupPath + '/nginx/conf/key'
        apachePath = self.setupPath + '/apache/conf/key'
        for filename in os.listdir(Path):
            #准备配置文件
            name = filename[0:len(filename) - 5];
            filename = Path + '/' + filename;
            conf = public.readFile(filename);
            
            #替换关键词
            if Replace: conf = conf.replace(Replace,ReplaceTo);
            ReplaceTo = letPath + name;
            Replace = 'conf/key/' + name;
            if conf.find(Replace) != -1: conf = conf.replace(Replace,ReplaceTo);
            Replace = 'key/' + name;
            if conf.find(Replace) != -1: conf = conf.replace(Replace,ReplaceTo);
            public.writeFile(filename,conf);
            
            #提取配置信息
            if conf.find('server_name') != -1:
                self.formatNginxConf(filename);
            elif conf.find('<Directory') != -1:
                #self.formatApacheConf(filename)
                pass;
            
            #移动文件
            shutil.move(filename, toPath + '/' + name + '.conf');
            
            #转移证书
            self.moveKey(nginxPath + '/' + name, letPath + '/' + name)
            self.moveKey(apachePath + '/' + name, letPath + '/' + name)
        
        #删除多余目录
        shutil.rmtree(Path);
        #重载服务
        public.serviceReload();
        
    #从Nginx配置文件获取站点信息
    def formatNginxConf(self,filename):
        
        #准备基础信息
        name = os.path.basename(filename[0:len(filename) - 5]);
        if name.find('.') == -1: return;
        conf = public.readFile(filename);
        #取域名
        rep = "server_name\s+(.+);"
        tmp = re.search(rep,conf);
        if not tmp: return;
        domains = tmp.groups()[0].split(' ');
        
        #取根目录
        rep = "root\s+(.+);"
        tmp = re.search(rep,conf);
        if not tmp: return;
        path = tmp.groups()[0];
        
        #提交到数据库
        self.toSiteDatabase(name, domains, path);
    
    #从Apache配置文件获取站点信息
    def formatApacheConf(self,filename):
        #准备基础信息
        name = os.path.basename(filename[0:len(filename) - 5]);
        if name.find('.') == -1: return;
        conf = public.readFile(filename);
        
        #取域名
        rep = "ServerAlias\s+(.+)\n"
        tmp = re.search(rep,conf);
        if not tmp: return;
        domains = tmp.groups()[0].split(' ');
        
        #取根目录
        rep = u"DocumentRoot\s+\"(.+)\"\n"
        tmp = re.search(rep,conf);
        if not tmp: return;
        path = tmp.groups()[0];
        
        #提交到数据库
        self.toSiteDatabase(name, domains, path);
    
    #添加到数据库
    def toSiteDatabase(self,name,domains,path):
        if public.M('sites').where('name=?',(name,)).count() > 0: return;
        public.M('sites').add('name,path,status,ps,addtime',(name,path,'1','请输入备注',public.getDate()));
        pid = public.M('sites').where("name=?",(name,)).getField('id');
        for domain in domains:
            public.M('domain').add('pid,name,port,addtime',(pid,domain,'80',public.getDate()))
    
    #移动旧版本证书
    def moveKey(self,srcPath,dstPath):
        if not os.path.exists(srcPath): return;
        import shutil
        os.makedirs(dstPath);
        srcKey = srcPath + '/key.key';
        srcCsr = srcPath + '/csr.key';
        if os.path.exists(srcKey): shutil.move(srcKey,dstPath + '/privkey.pem');
        if os.path.exists(srcCsr): shutil.move(srcCsr,dstPath + '/fullchain.pem');
    
    #路径处理
    def GetPath(self,path):
        if path[-1] == '/':
            return path[0:-1];
        return path;
    
    #日志开关
    def logsOpen(self,get):
        get.name = public.M('sites').where("id=?",(get.id,)).getField('name');
        # APACHE
        filename = public.GetConfigValue('setup_path') + '/panel/vhost/apache/' + get.name + '.conf';
        if os.path.exists(filename):
            conf = public.readFile(filename);
            if conf.find('#ErrorLog') != -1:
                conf = conf.replace("#ErrorLog","ErrorLog").replace('#CustomLog','CustomLog');
            else:
                conf = conf.replace("ErrorLog","#ErrorLog").replace('CustomLog','#CustomLog');
            public.writeFile(filename,conf);
        
        #NGINX
        filename = public.GetConfigValue('setup_path') + '/panel/vhost/nginx/' + get.name + '.conf';
        if os.path.exists(filename):
            conf = public.readFile(filename);
            rep = public.GetConfigValue('logs_path') + "/"+get.name+".log";
            if conf.find(rep) != -1:
                conf = conf.replace(rep,"/dev/null");
            else:
                conf = conf.replace('access_log  /dev/null','access_log  ' + rep);
            public.writeFile(filename,conf);
        
        public.serviceReload();
        return public.returnMsg(True, 'SUCCESS');
    
    #取日志状态
    def GetLogsStatus(self,get):
        filename = public.GetConfigValue('setup_path') + '/panel/vhost/'+public.get_webserver()+'/' + get.name + '.conf';
        conf = public.readFile(filename);
        if conf.find('#ErrorLog') != -1: return False;
        if conf.find("access_log  /dev/null") != -1: return False;
        return True;
    
    #取目录加密状态
    def GetHasPwd(self,get):
        if not hasattr(get,'siteName'):
            get.siteName = public.M('sites').where('id=?',(get.id,)).getField('name');
            get.configFile = self.setupPath + '/panel/vhost/nginx/' + get.siteName + '.conf';
        conf = public.readFile(get.configFile);
        if conf.find('#AUTH_START') != -1: return True;
        return False;
            
    #设置目录加密
    def SetHasPwd(self,get):
        if len(get.username.strip()) == 0 or len(get.password.strip()) == 0: return public.returnMsg(False,'用户名或密码不能为空!')

        if not hasattr(get,'siteName'): 
            get.siteName = public.M('sites').where('id=?',(get.id,)).getField('name');
            
        self.CloseHasPwd(get);
        filename = public.GetConfigValue('setup_path') + '/pass/' + get.siteName + '.pass';
        passconf = get.username + ':' + public.hasPwd(get.password);
        
        if get.siteName == 'phpmyadmin': 
            get.configFile = self.setupPath + '/nginx/conf/nginx.conf';
        else:
            get.configFile = self.setupPath + '/panel/vhost/nginx/' + get.siteName + '.conf';
            
        #处理Nginx配置
        conf = public.readFile(get.configFile);
        if conf:
            rep = '#error_page   404   /404.html;';
            if conf.find(rep) == -1: rep = '#error_page 404/404.html;';
            data = '''
    #AUTH_START
    auth_basic "Authorization";
    auth_basic_user_file %s;
    #AUTH_END''' % (filename,)
            conf = conf.replace(rep,rep + data);
            public.writeFile(get.configFile,conf);
        
        
        if get.siteName == 'phpmyadmin': 
            get.configFile = self.setupPath + '/apache/conf/extra/httpd-vhosts.conf';
        else:
            get.configFile = self.setupPath + '/panel/vhost/apache/' + get.siteName + '.conf';
            
        conf = public.readFile(get.configFile);
        if conf:
            #处理Apache配置
            rep = 'SetOutputFilter'
            if conf.find(rep) != -1:
                data = '''#AUTH_START
        AuthType basic
        AuthName "Authorization "
        AuthUserFile %s
        Require user %s
        #AUTH_END
        ''' % (filename,get.username)
                conf = conf.replace(rep,data + rep);
                conf = conf.replace(' Require all granted'," #Require all granted");
                public.writeFile(get.configFile,conf);
          
        #写密码配置  
        passDir = public.GetConfigValue('setup_path') + '/pass';
        if not os.path.exists(passDir): public.ExecShell('mkdir -p ' + passDir)
        public.writeFile(filename,passconf);
        public.serviceReload();
        public.WriteLog("TYPE_SITE","SITE_AUTH_OPEN_SUCCESS",(get.siteName,));
        return public.returnMsg(True,'SET_SUCCESS');
        
    #取消目录加密
    def CloseHasPwd(self,get):
        if not hasattr(get,'siteName'): 
            get.siteName = public.M('sites').where('id=?',(get.id,)).getField('name');
            
        if get.siteName == 'phpmyadmin': 
            get.configFile = self.setupPath + '/nginx/conf/nginx.conf';
        else:
            get.configFile = self.setupPath + '/panel/vhost/nginx/' + get.siteName + '.conf';
        
        if os.path.exists(get.configFile):
            conf = public.readFile(get.configFile);
            rep = "\n\s*#AUTH_START(.|\n){1,200}#AUTH_END";
            conf = re.sub(rep,'',conf);
            public.writeFile(get.configFile,conf);
            
        if get.siteName == 'phpmyadmin': 
            get.configFile = self.setupPath + '/apache/conf/extra/httpd-vhosts.conf';
        else:
            get.configFile = self.setupPath + '/panel/vhost/apache/' + get.siteName + '.conf';
        
        if os.path.exists(get.configFile):
            conf = public.readFile(get.configFile);
            rep = "\n\s*#AUTH_START(.|\n){1,200}#AUTH_END";
            conf = re.sub(rep,'',conf);
            conf = conf.replace(' #Require all granted'," Require all granted");
            public.writeFile(get.configFile,conf);
        public.serviceReload();
        public.WriteLog("TYPE_SITE","SITE_AUTH_CLOSE_SUCCESS",(get.siteName,));
        return public.returnMsg(True,'SET_SUCCESS');
    
    #启用tomcat支持
    def SetTomcat(self,get):
        siteName = get.siteName;
        name = siteName.replace('.','_');
        
        rep = "^(\d{1,3}\.){3,3}\d{1,3}$";
        if re.match(rep,siteName): return public.returnMsg(False,'TOMCAT_IP');
        
        #nginx
        filename = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf';
        if os.path.exists(filename):
            conf = public.readFile(filename);
            if conf.find('#TOMCAT-START') != -1: return self.CloseTomcat(get);
            tomcatConf = '''#TOMCAT-START
    location /
    {
        proxy_pass "http://%s:8080";
        proxy_set_header Host %s;
        proxy_set_header X-Forwarded-For $remote_addr;
    }
    location ~ .*\.(gif|jpg|jpeg|bmp|png|ico|txt|js|css)$
    {
        expires      12h;
    }
    
    location ~ .*\.war$
    {
        return 404;
    }
    #TOMCAT-END
    ''' % (siteName,siteName)
            rep = 'include enable-php';
            conf = conf.replace(rep,tomcatConf + rep);
            public.writeFile(filename,conf);
        
        #apache
        filename = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf';
        if os.path.exists(filename):
            conf = public.readFile(filename);
            if conf.find('#TOMCAT-START') != -1: return self.CloseTomcat(get);
            tomcatConf = '''#TOMCAT-START
    <IfModule mod_proxy.c>
        ProxyRequests Off
        SSLProxyEngine on
        ProxyPass / http://%s:8080/
        ProxyPassReverse / http://%s:8080/
        RequestHeader unset Accept-Encoding
        ExtFilterDefine fixtext mode=output intype=text/html cmd="/bin/sed 's,:8080,,g'"
        SetOutputFilter fixtext
    </IfModule>
    #TOMCAT-END
    ''' % (siteName,siteName)
            
            rep = '#PATH';
            conf = conf.replace(rep,tomcatConf + rep);
            public.writeFile(filename,conf);
        path = public.M('sites').where("name=?",(siteName,)).getField('path');
        import tomcat
        tomcat.tomcat().AddVhost(path,siteName);
        public.serviceReload();
        public.ExecShell('/etc/init.d/tomcat stop');
        public.ExecShell('/etc/init.d/tomcat start');
        public.ExecShell('echo "127.0.0.1 '+siteName + '" >> /etc/hosts');
        public.WriteLog('TYPE_SITE','SITE_TOMCAT_OPEN',(siteName,))
        return public.returnMsg(True,'SITE_TOMCAT_OPEN');
    
    #关闭tomcat支持
    def CloseTomcat(self,get):
        if not os.path.exists('/etc/init.d/tomcat'): return False;
        siteName = get.siteName;
        name = siteName.replace('.','_');
        
        #nginx
        filename = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf';
        if os.path.exists(filename):
            conf = public.readFile(filename);
            rep = "\s*#TOMCAT-START(.|\n)+#TOMCAT-END"
            conf = re.sub(rep,'',conf);
            public.writeFile(filename,conf);
        
        #apache
        filename = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf';
        if os.path.exists(filename):
            conf = public.readFile(filename);
            rep = "\s*#TOMCAT-START(.|\n)+#TOMCAT-END"
            conf = re.sub(rep,'',conf);
            public.writeFile(filename,conf);
        public.ExecShell('rm -rf ' + self.setupPath + '/panel/vhost/tomcat/' + name);
        try:
            import tomcat
            tomcat.tomcat().DelVhost(siteName);
        except:
            pass
        public.serviceReload();
        public.ExecShell('/etc/init.d/tomcat restart');
        public.ExecShell("sed -i '/"+siteName+"/d' /etc/hosts");
        public.WriteLog('TYPE_SITE','SITE_TOMCAT_CLOSE',(siteName,));
        return public.returnMsg(True,'SITE_TOMCAT_CLOSE');
    
    #取当站点前运行目录
    def GetSiteRunPath(self,get):
        siteName = public.M('sites').where('id=?',(get.id,)).getField('name');
        sitePath = public.M('sites').where('id=?',(get.id,)).getField('path');
        path = sitePath;
        if public.get_webserver() == 'nginx':
            filename = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
            if os.path.exists(filename):
                conf = public.readFile(filename)
                rep = '\s*root\s*(.+);'
                path = re.search(rep,conf).groups()[0];
        else:
            filename = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
            if os.path.exists(filename):
                conf = public.readFile(filename)
                rep = '\s*DocumentRoot\s*"(.+)"\s*\n'
                path = re.search(rep,conf).groups()[0];
        
        data = {}
        if sitePath == path: 
            data['runPath'] = '/';
        else:
            data['runPath'] = path.replace(sitePath,'');
        
        dirnames = []
        dirnames.append('/');
        if not os.path.exists(sitePath): os.makedirs(sitePath)
        for filename in os.listdir(sitePath):
            try:
                filePath = sitePath + '/' + filename
                if os.path.islink(filePath): continue
                if os.path.isdir(filePath):
                    dirnames.append('/' + filename)
            except:
                pass
        
        data['dirs'] = dirnames;
        return data;
    
    #设置当前站点运行目录
    def SetSiteRunPath(self,get):
        siteName = public.M('sites').where('id=?',(get.id,)).getField('name');
        sitePath = public.M('sites').where('id=?',(get.id,)).getField('path');
        
        #处理Nginx
        filename = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        if os.path.exists(filename):
            conf = public.readFile(filename)
            rep = '\s*root\s*(.+);'
            path = re.search(rep,conf).groups()[0];
            conf = conf.replace(path,sitePath + get.runPath);
            public.writeFile(filename,conf);
            
        #处理Apache
        filename = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
        if os.path.exists(filename):
            conf = public.readFile(filename)
            rep = '\s*DocumentRoot\s*"(.+)"\s*\n'
            path = re.search(rep,conf).groups()[0];
            conf = conf.replace(path,sitePath + get.runPath);
            public.writeFile(filename,conf);

        self.DelUserInI(sitePath);
        get.path = sitePath;
        self.SetDirUserINI(get);
        
        public.serviceReload();
        return public.returnMsg(True,'SET_SUCCESS');
    
    #设置默认站点
    def SetDefaultSite(self,get):
        import time;

        default_site_save = 'data/defaultSite.pl'
        #清理旧的
        defaultSite = public.readFile(default_site_save);
        http2 = ''
        versionStr = public.readFile('/www/server/nginx/version.pl');
        if versionStr:
            if versionStr.find('1.8.1') == -1: http2 = ' http2';
        if defaultSite:
            path = self.setupPath + '/panel/vhost/nginx/' + defaultSite + '.conf';
            if os.path.exists(path):
                conf = public.readFile(path);
                rep = "listen\s+80.+;"
                conf = re.sub(rep,'listen 80;',conf,1);
                rep = "listen\s+\[::\]:80.+;"
                conf = re.sub(rep,'listen [::]:80;',conf,1);
                rep = "listen\s+443.+;"
                conf = re.sub(rep,'listen 443 ssl'+http2+';',conf,1);
                rep = "listen\s+\[::\]:443.+;"
                conf = re.sub(rep,'listen [::]:443 ssl'+http2+';',conf,1);
                public.writeFile(path,conf);
        
            path = self.setupPath + '/apache/htdocs/.htaccess'
            if os.path.exists(path): os.remove(path)

        if get.name == '0': 
            os.remove(default_site_save)
            return public.returnMsg(True,'设置成功!')

        #处理新的
        path = self.setupPath + '/apache/htdocs';
        if os.path.exists(path):
            conf = '''<IfModule mod_rewrite.c>
  RewriteEngine on
  RewriteCond %{HTTP_HOST} !^127.0.0.1 [NC] 
  RewriteRule (.*) http://%s/$1 [L]
</IfModule>'''
            conf = conf.replace("%s",get.name)
            if get.name == 'off': conf = '';
            public.writeFile(path + '/.htaccess',conf);
            
        
        path = self.setupPath + '/panel/vhost/nginx/' + get.name + '.conf';
        if os.path.exists(path):
            conf = public.readFile(path);
            rep = "listen\s+80\s*;"
            conf = re.sub(rep,'listen 80 default_server;',conf,1);
            rep = "listen\s+\[::\]:80\s*;"
            conf = re.sub(rep,'listen [::]:80 default_server;',conf,1);
            rep = "listen\s+443\s*ssl\s*\w*\s*;"
            conf = re.sub(rep,'listen 443 ssl'+http2+' default_server;',conf,1);
            rep = "listen\s+\[::\]:443\s*ssl\s*\w*\s*;"
            conf = re.sub(rep,'listen [::]:443 ssl'+http2+' default_server;',conf,1);
            public.writeFile(path,conf);
        
        path = self.setupPath + '/panel/vhost/nginx/default.conf';
        if os.path.exists(path): public.ExecShell('rm -f ' + path);
        public.writeFile(default_site_save,get.name);
        public.serviceReload();
        return public.returnMsg(True,'SET_SUCCESS');
    
    #取默认站点
    def GetDefaultSite(self,get):
        data = {}
        data['sites'] = public.M('sites').field('name').order('id desc').select();
        data['defaultSite'] = public.readFile('data/defaultSite.pl');
        return data;
    
    #扫描站点
    def CheckSafe(self,get):
        import db,time
        isTask = '/tmp/panelTask.pl'
        if os.path.exists(self.setupPath + '/panel/class/panelSafe.py'):
            import py_compile
            py_compile.compile(self.setupPath + '/panel/class/panelSafe.py');
        get.path = public.M('sites').where('id=?',(get.id,)).getField('path');
        execstr = "cd " + public.GetConfigValue('setup_path') + "/panel/class && python panelSafe.pyc " + get.path;
        sql = db.Sql()
        sql.table('tasks').add('id,name,type,status,addtime,execstr',(None,'扫描目录 ['+get.path+']','execshell','0',time.strftime('%Y-%m-%d %H:%M:%S'),execstr))
        public.writeFile(isTask,'True')
        public.WriteLog('TYPE_SETUP','SITE_SCAN_ADD',(get.path,));
        return public.returnMsg(True,'SITE_SCAN_ADD');
    
    #获取结果信息
    def GetCheckSafe(self,get):
        get.path = public.M('sites').where('id=?',(get.id,)).getField('path');
        path = get.path + '/scan.pl'
        result = {};
        result['data'] = []
        result['phpini'] = []
        result['userini'] = result['sshd'] = True;
        result['scan'] = False
        result['outime'] = result['count'] = result['error'] = 0
        if not os.path.exists(path): return result;
        import json
        return json.loads(public.readFile(path));
        
    #更新病毒库
    def UpdateRulelist(self,get):
        try:
            conf = public.httpGet(public.getUrl()+'/install/ruleList.conf')
            if conf:
                public.writeFile(self.setupPath + '/panel/data/ruleList.conf',conf);
                return public.returnMsg(True,'UPDATE_SUCCESS');
            return public.returnMsg(False,'CONNECT_ERR');
        except:
            return public.returnMsg(False,'CONNECT_ERR');
    
    #设置到期时间
    def SetEdate(self,get):
        result = public.M('sites').where('id=?',(get.id,)).setField('edate',get.edate);
        siteName = public.M('sites').where('id=?',(get.id,)).getField('name');
        public.WriteLog('TYPE_SITE','SITE_EXPIRE_SUCCESS',(siteName,get.edate));
        return public.returnMsg(True,'SITE_EXPIRE_SUCCESS');
    
    #获取防盗链状态
    def GetSecurity(self,get):
        file = '/www/server/panel/vhost/nginx/' + get.name + '.conf';
        conf = public.readFile(file);
        data = {}
        if conf.find('SECURITY-START') != -1:
            rep = "#SECURITY-START(\n|.){1,500}#SECURITY-END";
            tmp = re.search(rep,conf).group()
            data['fix'] = re.search("\(.+\)\$",tmp).group().replace('(','').replace(')$','').replace('|',',');
            data['domains'] = ','.join(re.search("valid_referers\s+none\s+blocked\s+(.+);\n",tmp).groups()[0].split());
            data['status'] = True;
        else:
            data['fix'] = 'jpg,jpeg,gif,png,js,css';
            domains = public.M('domain').where('pid=?',(get.id,)).field('name').select();
            tmp = [];
            for domain in domains:
                tmp.append(domain['name']);
            data['domains'] = ','.join(tmp);
            data['status'] = False
        return data;
    
    #设置防盗链
    def SetSecurity(self,get):
        if len(get.fix) < 2: return public.returnMsg(False,'URL后缀不能为空!');
        file = '/www/server/panel/vhost/nginx/' + get.name + '.conf';
        if os.path.exists(file):
            conf = public.readFile(file);
            if conf.find('SECURITY-START') != -1:
                rep = "\s{0,4}#SECURITY-START(\n|.){1,500}#SECURITY-END\n?";
                conf = re.sub(rep,'',conf);
                public.WriteLog('网站管理','站点['+get.name+']已关闭防盗链设置!');
            else:
                rconf = '''#SECURITY-START 防盗链配置
    location ~ .*\.(%s)$
    {
        expires      30d;
        access_log /dev/null;
        valid_referers none blocked %s;
        if ($invalid_referer){
           return 404;
        }
    }
    #SECURITY-END
    include enable-php-''' % (get.fix.strip().replace(',','|'),get.domains.strip().replace(',',' '))
                conf = re.sub("include\s+enable-php-",rconf,conf);
                public.WriteLog('网站管理','站点['+get.name+']已开启防盗链!');
            public.writeFile(file,conf);
        file = '/www/server/panel/vhost/apache/' + get.name + '.conf';
        if os.path.exists(file):
            conf = public.readFile(file);
            if conf.find('SECURITY-START') != -1:
                rep = "#SECURITY-START(\n|.){1,500}#SECURITY-END\n";
                conf = re.sub(rep,'',conf);
            else:
                tmp = "    RewriteCond %{HTTP_REFERER} !{DOMAIN} [NC]";
                tmps = [];
                for d in get.domains.split(','):
                    tmps.append(tmp.replace('{DOMAIN}',d));
                domains = "\n".join(tmps);
                rconf = "combined\n    #SECURITY-START 防盗链配置\n    RewriteEngine on\n    RewriteCond %{HTTP_REFERER} !^$ [NC]\n" + domains + "\n    RewriteRule .("+get.fix.strip().replace(',','|')+") /404.html [R=404,NC,L]\n    #SECURITY-END"
                conf = conf.replace('combined',rconf)
            public.writeFile(file,conf);
        public.serviceReload();
        return public.returnMsg(True,'SET_SUCCESS');
    
    #取网站日志
    def GetSiteLogs(self,get):
        serverType = public.get_webserver();
        logPath = '/www/wwwlogs/' + get.siteName + '.log';
        if serverType != 'nginx': logPath = '/www/wwwlogs/' + get.siteName + '-access_log';
        if not os.path.exists(logPath): return public.returnMsg(False,'日志为空');
        return public.returnMsg(True,public.GetNumLines(logPath,1000));


    #取网站分类
    def get_site_types(self,get):
        data = public.M("site_types").field("id,name").order("id asc").select()
        data.insert(0,{"id":0,"name":"默认分类"})
        return data

    #添加网站分类
    def add_site_type(self,get):
        get.name = get.name.strip()
        if not get.name: return public.returnMsg(False,"分类名称不能为空")
        if len(get.name) > 18: return public.returnMsg(False,"分类名称长度不能超过6个汉字或18位字母")
        type_sql = public.M('site_types')
        if type_sql.count() >= 10: return public.returnMsg(False,'最多添加10个分类!')
        if type_sql.where('name=?',(get.name,)).count()>0: return public.returnMsg(False,"指定分类名称已存在!")
        type_sql.add("name",(get.name,))
        return public.returnMsg(True,'添加成功!')

    #删除网站分类
    def remove_site_type(self,get):
        type_sql = public.M('site_types')
        if type_sql.where('id=?',(get.id,)).count()==0: return public.returnMsg(False,"指定分类不存在!")
        type_sql.where('id=?',(get.id,)).delete()
        public.M("sites").where("type_id=?",(get.id,)).save("type_id",(0,))
        return public.returnMsg(True,"分类已删除!")

    #修改网站分类名称
    def modify_site_type_name(self,get):
        get.name = get.name.strip()
        if not get.name: return public.returnMsg(False,"分类名称不能为空")
        if len(get.name) > 18: return public.returnMsg(False,"分类名称长度不能超过6个汉字或18位字母")
        type_sql = public.M('site_types')
        if type_sql.where('id=?',(get.id,)).count()==0: return public.returnMsg(False,"指定分类不存在!")
        type_sql.where('id=?',(get.id,)).setField('name',get.name)
        return public.returnMsg(True,"修改成功!")

    #设置指定站点的分类
    def set_site_type(self,get):
        site_ids = json.loads(get.site_ids)
        site_sql = public.M("sites")
        for s_id in site_ids:
            site_sql.where("id=?",(s_id,)).setField("type_id",get.id)
        return public.returnMsg(True,"设置成功!")
