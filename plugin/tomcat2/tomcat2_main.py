#!/usr/bin/python
# coding: utf-8
# -----------------------------
# 宝塔Linux面板 tomcat 管理器
# Author: <1249648969@qq.com>
'''
//      ┏┛ ┻━━━━━┛ ┻┓
//      ┃　　　━　　　┃
//      ┃　┳┛　  ┗┳　┃
//      ┃　　　-　　　┃
//      ┗━┓　　　┏━━━┛   你瞅啥，瞅你咋地！
//        ┃　　　┗━━━━━━━━━┓
//        ┗━┓ ┓ ┏━━━┳ ┓ ┏━┛
//          ┗━┻━┛   ┗━┻━┛
'''
import sys, os
if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
os.chdir('/www/server/panel')
sys.path.append("class/")
import public,re,psutil,files,json,firewalls
from xml.etree.ElementTree import ElementTree, Element
class file: path = encoding =''
class mobj: port = ps = ''
class liang:version=''

class tomcat2_main(object):
    __tomcat7='/www/server/tomcat7'
    __tomcat8 = '/www/server/tomcat8'
    __tomcat9 = '/www/server/tomcat9'
    __tomcat7_config='/etc/init.d/tomcat7'
    __tomcat8_config = '/etc/init.d/tomcat8'
    __tomcat9_config = '/etc/init.d/tomcat9'
    __tomcat7_server='/www/server/tomcat7/conf/server.xml'
    __tomcat8_server = '/www/server/tomcat8/conf/server.xml'
    __tomcat9_server = '/www/server/tomcat9/conf/server.xml'
    __jdk_7='/usr/java/jdk1.7.0_80'
    __jdk_8='/usr/java/jdk1.8.0_121'
    __jdk_11='/usr/java/jdk-11.0.2'
    __jdk_8_191='/usr/java/jdk1.8.0_191-amd64'
    __tomcat7_log='/www/server/tomcat7/logs/catalina-daemon.out'
    __tomcat8_log = '/www/server/tomcat8/logs/catalina-daemon.out'
    __tomcat9_log = '/www/server/tomcat9/logs/catalina-daemon.out'
    __tomcat7_jkd='/www/server/tomcat7/bin/daemon.sh'
    __tomcat8_jkd = '/www/server/tomcat8/bin/daemon.sh'
    __tomcat9_jkd = '/www/server/tomcat9/bin/daemon.sh'
    __files=''
    __TREE = None
    __ENGINE = None
    __ROOT = None
    __version_dict={}
    __CONF_FILE=''
    __user_config='/www/server/panel/plugin/tomcat/user.json'
    __CONNECTROR = ''

    def __init__(self):
        if not self.__files:files.files()
        self.SetPort()
    #开启端口
    def SetPort(self):
        import firewalls
        fs = firewalls.firewalls()
        get = mobj()
        for i in range(8080,8083):
            get.port = str(i)
            get.ps = 'tomcat外部端口'
            fs.AddAcceptPort(get)
        return True

    # 安装接口
    def InstallTomcat(self,get):
        version=get.version.strip()
        type=get.type.strip()
        version_list=["7","8","9"]
        jdk8_path = '/usr/java/jdk1.8.0_121'
        jdk7_path = '/usr/java/jdk1.7.0_80'
        if version=='tomcat7':version="7"
        if version == 'tomcat8': version = "8"
        if version == 'tomcat9': version = "9"
        if version in version_list:
            if type=='install':
                if version == "8" or version == "9":
                    if not os.path.exists(jdk8_path):
                        public.downloadFile("http://download.bt.cn/install/src/jdk-8u121-linux-x64.rpm",
                                            "/tmp/java-jdk.rpm")
                else:
                    if not os.path.exists(jdk7_path):
                        public.downloadFile(
                            "http://download.bt.cn/install/src/jdk-7u80-linux-x64.rpm",
                            "/tmp/java-jdk.rpm")
                if os.path.exists("/tmp/tomcat2.sh"):
                    public.ExecShell("cd /tmp && rm -rf /tmp/tomcat2.sh && wget -O tomcat2.sh %s/install/0/tomcat2.sh && bash -x  tomcat2.sh install %s >>/tmp/tomcat.json"%(str(public.get_url()),str(version)))
                    #public.ExecShell("cd /tmp && bash -x  tomcat2.sh install %s >>/tmp/tomcat.json"%(str(version)))

                else:
                    public.ExecShell(
                        "cd /tmp && wget -O tomcat2.sh %s/install/0/tomcat2.sh && bash -x  tomcat2.sh install %s >>/tmp/tomcat.json" %(str(public.get_url()),str(version)))
                return public.returnMsg(True, "安装成功")
            elif type=='uninstall':
                if os.path.exists("/tmp/tomcat2.sh"):
                    public.ExecShell("cd /tmp && rm -rf /tmp/tomcat2.sh && wget -O tomcat2.sh %s/install/0/tomcat2.sh && bash -x  tomcat2.sh uninstall %s >>/tmp/tomcat.json" %(str(public.get_url()),str(version)))
                    #public.ExecShell("cd /tmp &&  bash -x  tomcat2.sh uninstall %s >>/tmp/tomcat.json" % (str(version)))
                else:
                    public.ExecShell(
                        "cd /tmp && wget -O tomcat2.sh %s/install/0/tomcat2.sh && bash -x  tomcat2.sh uninstall %s >>/tmp/tomcat.json" %(str(public.get_url()),str(version)))
                return public.returnMsg(True, "卸载成功")
            else:
                return public.returnMsg(False, "类型错误")
        else:
            return public.returnMsg(False, "类型错误")

    #查看安装日志
    def GetSetLog(self,get):
        log_path='/tmp/tomcat.json'
        if os.path.exists(log_path):
            ret=self.GetLog(log_path)
            if ret:
                return public.returnMsg(True, ret)
            else:
                return public.returnMsg(True, "日志为空")
        else:
            return public.returnMsg(True, "日志为空")

    # xml 初始化
    def Xml_init(self,path):
        try:
            self.__CONF_FILE = str(path)
            self.__TREE = ElementTree()
            self.__TREE.parse(self.__CONF_FILE)
            self.__ROOT = self.__TREE.getroot()
            self.__ENGINE = self.__TREE.findall('Service/Engine')[0]
            self.__CONNECTROR = self.__TREE.findall('Service/Connector')
            return True
        except:
            return False

    # 返回安装的tomcat 版本 服务状态 和JDK 版本
    def  TomcatVersion(self,get):
        ret={}
        if os.path.exists(self.__tomcat7) and os.path.exists(self.__tomcat7_config):
            # 取服务状态
            # JDK 版本
            list=self.GetServerJdk(version='tomcat7')
            if list:
                ret['tomcat7']=list
                get=liang()
                get.version='7'
                if not self.Initialization(get.version):
                    ret['tomcat7']['port'] = False
                else:
                    port=self.GetPort()
                    ret['tomcat7']['port'] = port
        else:
            ret['tomcat7']=False

        if os.path.exists(self.__tomcat8) and os.path.exists(self.__tomcat8_config):
            list=self.GetServerJdk(version='tomcat8')
            if list:
                ret['tomcat8'] = list
                get=liang()
                get.version='8'
                if not self.Initialization(get.version):
                    ret['tomcat9']['port'] = False
                else:
                    port = self.GetPort()
                    ret['tomcat8']['port'] = port
        else:
            ret['tomcat8'] = False


        if os.path.exists(self.__tomcat9) and os.path.exists(self.__tomcat9_server):
            list=self.GetServerJdk(version='tomcat9')
            if list:
                ret['tomcat9'] = list
                get=liang()
                get.version='9'
                if not self.Initialization(get.version):
                    ret['tomcat9']['port'] = False
                else:
                    port = self.GetPort()
                    ret['tomcat9']['port'] = port

            else:ret['tomcat9']=False
        else:
            ret['tomcat9'] = False


        return public.returnMsg(True, ret)

    #取jdk和服务状态
    def GetServerJdk(self,version):
        ret={}
        jdk_version = self.GetJdk(version)
        server = self.GetServer(version)
        if jdk_version:
            ret['jdk_version']=jdk_version
            if server:
                ret['status']=True
            else:
                ret['status'] = False
            return ret
        else:
            return False

    # 取JDK 版本
    def GetJdk(self,version):
        path='/www/server/%s/bin/daemon.sh'%version
        if os.path.exists(path):
            ret=public.ReadFile(path)
            rec="\nJAVA_HOME=.+"
            if re.search(rec,ret):
                jdk=re.search(rec, ret).group(0).split('/')[-1]
                return jdk
            else:
                return False
        else:
            return False

    # 取服务状态
    def GetServer(self,version):
        pid_path='/www/server/%s/logs/catalina-daemon.pid'%version
        if os.path.exists(pid_path):
            pid= int(public.ReadFile(pid_path).strip())
            try:
                ret = psutil.Process(pid)
                return True
            except:
                return False
        else:
            return False

    #服务管理
    def StartTomcat(self,get):
        version=get.version.strip()
        type=get.type.strip()
        #判断服务是否正常
        execStr = '/etc/init.d/%s stop && /etc/init.d/%s start'%(version,version)
        start='/etc/init.d/%s start'%(version)
        stop='/etc/init.d/%s stop'%(version)
        if type=='start':
            ret=self.GetServer(version)
            if not ret:
                pid_path = '/www/server/%s/logs/catalina-daemon.pid' % version
                if os.path.exists(pid_path):
                    os.remove(pid_path)
                public.ExecShell(start)
            return public.returnMsg(True, '%s启动成功'%version)
        elif type=='stop':
            public.ExecShell(stop)
            if self.GetServer(version):
                public.ExecShell(stop)
            return public.returnMsg(True, '%s关闭成功' % version)
        elif type=='reload':
            public.ExecShell(execStr)
            ret = self.GetServer(version)
            if not ret:
                public.ExecShell(execStr)
            return public.returnMsg(True, '%s重载成功' % version)
        else:
            return public.returnMsg(False, '类型错误')

    #网站配置文件
    def GetConfig(self,get):
        ret={}
        if not self.__files: files.files()
        if os.path.exists(self.__tomcat7_server):
            tomcat7_file=self.GetFile(self.__tomcat7_server)
            if tomcat7_file:
                ret['tomcat7']=tomcat7_file
            else:
                ret['tomcat7']=False
        else:
            ret['tomcat7']=False
        if os.path.exists(self.__tomcat8_server):
            tomcat8_file=self.GetFile(self.__tomcat8_server)
            if tomcat8_file:
                ret['tomcat8']=tomcat8_file
            else:
                ret['tomcat8']=False
        else:
            ret['tomcat8']=False
        if os.path.exists(self.__tomcat9_server):
            tomcat9_file=self.GetFile(self.__tomcat9_server)
            if tomcat9_file:
                ret['tomcat9']=tomcat9_file
            else:
                ret['tomcat9']=False
        else:
            ret['tomcat9']=False
        return  public.returnMsg(True,ret)

    #查看文件函数
    def GetFile(self,path):
        if os.path.exists(path):
            get = file()
            get.path = path
            files2=files.files()
            _file = files2.GetFileBody(get)
            return _file
        else:
            return False

    #保存文件函数
    def WriteFile(self,get):
        '''
        三个参数：
        data
        path
        encoding
        :param get:
        :return:
        '''
        files2 = files.files()
        _file = files2.SaveFileBody(get)
        return _file

    # 日志
    def GetOpeLogs(self,get):
        ret={}
        if os.path.exists(self.__tomcat7_log):
            retc=self.GetLog(self.__tomcat7_log)
            if  retc:
                ret['tomcat7']=retc
            else:
                ret['tomcat7']=False
        else:
            ret['tomcat7'] = False
        if os.path.exists(self.__tomcat8_log):
            retc=self.GetLog(self.__tomcat8_log)
            if  retc:
                ret['tomcat8']=retc
            else:
                ret['tomcat8']=False
        else:
            ret['tomcat8'] = False
        if os.path.exists(self.__tomcat9_log):
            retc=self.GetLog(self.__tomcat9_log)
            if  retc:
                ret['tomcat9']=retc
            else:
                ret['tomcat9']=False
        else:
            ret['tomcat9'] = False
        return public.returnMsg(True,ret)

    # Log 取100行操作
    def GetLog(self,path):
        if not os.path.exists(path): return False
        return  public.GetNumLines(path, 3000)

    # 更换JDK 版本
    def SetJdk(self,get):
        version=get.version.strip()
        jdk_version=get.jdk_version.strip()
        if version=='7':
            #判断是否存在
            if os.path.exists(self.__tomcat7_config) and os.path.exists(self.__tomcat7_server) and os.path.exists(self.__tomcat7) and os.path.exists(self.__tomcat7_jkd):
                ret=self.PassJDk(self.__tomcat7_jkd,jdk_version)
                if ret:
                    return public.returnMsg(True, '更换成功')
                else:
                    return public.returnMsg(False, '更换失败')
            else:
                return public.returnMsg(False, "tomcat%s 环境有问题，请检查一下是否正常"%version)
        elif version=='8':
            if os.path.exists(self.__tomcat8_config) and os.path.exists(self.__tomcat8_server) and os.path.exists(
                    self.__tomcat8) and os.path.exists(self.__tomcat8_jkd):
                ret=self.PassJDk(self.__tomcat8_jkd, jdk_version)
                if ret:
                    return public.returnMsg(True,'更换成功')
                else:
                    return public.returnMsg(False, '更换失败')
            else:
                return public.returnMsg(False, "tomcat%s 环境有问题，请检查一下是否正常" % version)
        elif version=='9':
            if os.path.exists(self.__tomcat9_config) and os.path.exists(self.__tomcat9_server) and os.path.exists(
                    self.__tomcat9) and os.path.exists(self.__tomcat9_jkd):
                ret=self.PassJDk(self.__tomcat9_jkd, jdk_version)
                if ret:
                    return public.returnMsg(True,'更换成功')
                else:
                    return public.returnMsg(False, '更换失败')
            else:
                return public.returnMsg(False, "tomcat%s 环境有问题，请检查一下是否正常" % version)

    def PassJDk(self,path,jdk_version):
        if not os.path.exists(jdk_version):return public.returnMsg(False,"此JDK未安装")
        jdk_file=public.ReadFile(path)
        rec = '\nJAVA_HOME=.*'
        if re.search(rec, jdk_file):
            ret=re.sub('\nJAVA_HOME=.*','\nJAVA_HOME=%s'%jdk_version,jdk_file)
            public.WriteFile(jdk_file,ret)
            return True
        else:
            return False

    # 本地做一个本地hosts
    def SetHosts(self,domain):
        ret=public.ReadFile('/etc/hosts')
        import re
        rec='%s'%domain
        if re.search(rec,ret):
            pass
        else:
            public.ExecShell('echo "127.0.0.1 ' + domain + '" >> /etc/hosts')

    # 更新domain
    def PullHost(self,domain,domain2):
        ret = public.ReadFile('/etc/hosts')
        import re
        rec = '%s' % domain
        if re.search(rec, ret):
            re.sub(domain,domain2,ret)
            public.WriteFile('/etc/hosts',ret)
        else:
            public.ExecShell('echo "127.0.0.1 ' + domain + '" >> /etc/hosts')



    # 创建项目
    def AddProject(self, get):
    # 保存之后重载配置
        domain = get.domain.strip()
        if not self.is_domain(domain.strip()): return public.returnMsg(False, "请输入正确的域名")
        path = get.path.strip()
        version = get.version.strip()
        if not os.path.exists(path): os.makedirs(path)
        if not self.Initialization(get.version): return public.returnMsg(False, "配置文件错误请。或者服务未安装")
        ret = self.AddVhost(path=path, domain=domain)

        if ret:
            self.SetHosts(domain)
            self.RestarTomcat(version)
            return public.returnMsg(True, "添加成功")
        else:
            return public.returnMsg(False, "已经存在")

    def RestarTomcat(self,version):
        if version=='7':version='tomcat7'
        if version == '8': version = 'tomcat8'
        if version == '9': version = 'tomcat9'
        execStr = '/etc/init.d/%s stop && /etc/init.d/%s start' % (version, version)
        public.ExecShell(execStr)

    #查看项目列表
    def GetSite(self,get):
        ret={}
        if os.path.exists(self.__tomcat7_server):
            ret2=self.Xml_init(self.__tomcat7_server)
            if ret2:
                ret['tomcat7']=self.GetVhosts()
                version=self.GetVersion('7')
                if not version:version=='7.0.76'
                ret['tomcat7'].append(version)
            else:
                ret['tomcat7'] =False
        if os.path.exists(self.__tomcat8_server):
            ret2=self.Xml_init(self.__tomcat8_server)
            if ret2:
                ret['tomcat8'] = self.GetVhosts()
                version=self.GetVersion('8')
                if not version:version=='8.5.12'
                ret['tomcat8'].append(version)
            else:
                ret['tomcat8'] = False
        if os.path.exists(self.__tomcat9_server):
            ret2=self.Xml_init(self.__tomcat9_server)
            if ret2:
                ret['tomcat9'] = self.GetVhosts()
                version=self.GetVersion('9')
                if not version:version=='9.0.0'
                ret['tomcat9'].append(version)
            else:
                ret['tomcat9']=False
        return public.returnMsg(True,ret)

    # 查看版本号
    def GetVersion(self,version):
        tomcat_version='tomcat'+version
        path='/www/server/%s/version.pl'%tomcat_version
        if os.path.exists(path):
            ret=public.ReadFile(path)
            return ret.strip()
        else:return False


    def DelProject(self, get):
        version = get.version.strip()
        domain = get.domain.strip()
        if not self.is_domain(domain.strip()): return public.returnMsg(False, "请输入正确的域名")
        if not self.Initialization(get.version): return public.returnMsg(False, "配置文件错误请检查配置文件")
        ret = self.DelVhost(domain)
        if ret:
            self.RestarTomcat(version)
            return public.returnMsg(True, '删除成功')
        return public.returnMsg(False, '不存在')

    #
    def ReplacePath(self, get):
        version = get.version.strip()
        domain = get.domain.strip()
        path = get.path.strip()
        if not self.is_domain(domain): return public.returnMsg(False, "请输入正确的域名")
        if not self.Initialization(get.version): return public.returnMsg(False, "配置文件错误请检查配置文件")
        ret = self.SetPath(domain, path)
        if ret:
            self.RestarTomcat(version)
            return public.returnMsg(True, '更改成功')
        else:
            return public.returnMsg(True, '更改失败,目录不存在')


    # 添加二级目录
    def AddSitePath(self,get):
        version = get.version.strip()
        domain = get.domain.strip()
        if not self.is_domain(domain.strip()): return public.returnMsg(False, "请输入正确的域名")
        path = get.path.strip()
        name=get.name2.strip()
        if not os.path.exists(path): os.makedirs(path)
        if not self.Initialization(get.version): return public.returnMsg(False, "配置文件错误请检查配置文件")
        ret = self.AddPath(domain, path, name)
        if ret:
            self.RestarTomcat(version)
            return public.returnMsg(True, '添加成功')
        else:
            return public.returnMsg(False, '已经存在')

    def DelSitePath(self, get):
        version = get.version.strip()
        domain = get.domain.strip()
        path = get.path.strip()
        if not self.is_domain(domain.strip()): return public.returnMsg(False, "请输入正确的域名")
        if not self.Initialization(get.version): return public.returnMsg(False, "配置文件错误请检查配置文件")
        ret = self.DelPath(domain, path)
        self.RestarTomcat(version)
        return public.returnMsg(True, '删除成功')

    def Reloadable2(self,get):
        version = get.version.strip()
        domain = get.domain.strip()
        if not self.is_domain(domain.strip()): return public.returnMsg(False, "请输入正确的域名")
        reloadable=int(get.reloadable)
        if not self.Initialization(get.version): return public.returnMsg(False, "配置文件错误请检查配置文件")
        ret = self.SetVhost(domain=domain, reloadable=reloadable)
        self.RestarTomcat(version)
        return public.returnMsg(True, '更改成功!')

    def GetReloadable(self,get):
        if not self.is_domain(get.domain.strip()): return public.returnMsg(False, "请输入正确的域名")
        if not self.Initialization(get.version): return public.returnMsg(False, "配置文件错误请检查配置文件")
        ret = self.GetdomainVhost(get.domain)
        if ret:return public.returnMsg(True, ret)
        return public.returnMsg(False, '获取失败')


    # 初始化xml 进行配置
    def Initialization(self,version):
        if version=='7' or version=='tomcat7':
            if self.Xml_init(self.__tomcat7_server):return True
            else:return False
        elif version=='8' or version=='tomcat8':
            if self.Xml_init(self.__tomcat8_server):return True
            else:return False
        elif version=='9' or version=='tomcat9':
            if self.Xml_init(self.__tomcat9_server):return True
            else:return False
        else:return False

    # 映射
    def Mapping(self,get):
        if not self.Initialization(get.version):return public.returnMsg(False, "配置文件错误请检查配置文件")
        domain=get.domain.strip()
        version=get.version.strip()
        if not self.ChekcDomain(domain):return public.returnMsg(False,"tomcat中未存在此域名")
        sql = public.M('sites')
        if sql.where("name=?", (domain,)).count(): return public.returnMsg(False, 'SITE_ADD_ERR_EXISTS');
        ret={"domain":domain,"domainlist":[],"count":0}
        get.webname=json.dumps(ret)
        get.port = "80"
        get.ftp = 'false'
        get.sql = 'false'
        get.version = '00'
        get.ps = 'tomcat[' + version + ']的映射站点'
        get.path = public.M('config').where("id=?", ('1',)).getField('sites_path') + '/' + domain
        result=self.create_site(get)
        if 'status' in result: return result
        import panelSite
        s = panelSite.panelSite()
        get.sitename = domain
        get.proxyname = 'tomcat'
        get.proxysite = 'http://' + domain +':' +str(self.GetPort())
        get.todomain = domain
        get.proxydir = '/'
        get.type = 1
        get.cache = 0
        get.cachetime = 1
        get.advanced = 0
        get.subfilter = "[{\"sub1\":\"\",\"sub2\":\"\"},{\"sub1\":\"\",\"sub2\":\"\"},{\"sub1\":\"\",\"sub2\":\"\"}]"
        result = s.CreateProxy(get)
        if result['status']:
            public.WriteLog('tomcat'+str(get.version), '添加映射[' + str(domain) + ']' + '成功')
        else:
            public.WriteLog('tomcat'+str(get.version), '添加映射[' + str(domain) + ']' + '失败')
        os.system('chown www:www %s'%public.M('config').where("id=?", ('1',)).getField('sites_path') + '/' + domain)
        return public.returnMsg(True, '添加成功!')

    # 作为标识ID
    def GetRandomString(self,length):
        from random import Random
        strings = ''
        chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
        chrlen = len(chars) - 1
        random = Random()
        for i in range(length):
            strings += chars[random.randint(0, chrlen)]
        return strings

    def create_site(self, get):
            import panelSite
            s = panelSite.panelSite()
            result = s.AddSite(get)
            if 'status' in result: return result;
            result['id'] = public.M('sites').where('name=?', (get.domain,)).getField('id')
            self.set_ssl_check(get.domain)
            return result

        # 设置SSL验证目录过滤
    def set_ssl_check(self, siteName):
            rewriteConf = '''#一键申请SSL证书验证目录相关设置
    location ~ \.well-known{
        allow all;
    }'''
            public.writeFile('vhost/rewrite/' + siteName + '.conf', rewriteConf)

    # 更改域名
    def RenameDomain(self,get):
        if not self.Initialization(get.version): return public.returnMsg(False, "配置文件错误请检查配置文件")
        domain=get.domain.strip()
        appbase=get.appbase.strip()
        domain2=get.domain2.strip()
        if not self.is_domain(domain2.strip()): return public.returnMsg(False, "请输入正确的域名")
        mapping=get.mapping.strip()
        import time
        # 解决时效问题
        time.sleep(0.1)
        domain_file=self.GetServerDomain()

        if  len(domain_file)>=1:
            for i in domain_file:
                # 主域名
                if i.has_key('domain_main'):
                    if i['domain_main']==domain and i['appBase']==appbase:
                        sql = public.M('sites')
                        self.GetDomainPath2(domain, domain2)
                        self.RestarTomcat(get.version)
                        if mapping == '1':
                            if sql.where("name=?", (domain,)).count(): return public.returnMsg(False,'域名已经映射或者已经存在,请删除之后再更换')
                            get.domain = domain2
                            self.PullHost(domain, domain2)
                            ret = self.Mapping(get)
                            return ret
                        else:
                            self.PullHost(domain,domain2)
                            return public.returnMsg(True, '更换成功!')
                else:
                    # 其他域名
                    if i.has_key('domain'):
                        if i['domain'] == domain and i['appBase'] == appbase:
                            sql = public.M('sites')
                            self.GetDomainPath2(domain, domain2)
                            self.RestarTomcat(get.version)
                            if mapping == '1':
                                if sql.where("name=?", (domain,)).count(): return public.returnMsg(False,'域名已经映射或者已经存在,请删除之后再更换')

                                get.domain = domain2
                                ret = self.Mapping(get)
                                self.PullHost(domain, domain2)
                                return ret
                            else:
                                self.PullHost(domain, domain2)
                                return public.returnMsg(True, '更换成功!')
        return public.returnMsg(False, '获取域名列表失败!')

    def GetProxy(self,get):
        import panelSite
        try:
            s = panelSite.panelSite()
            ret=s.GetProxyList(get)
            #return str(type(ret))
            if type(ret)==list:
                return public.returnMsg(True, 'ok')
            else:
                return public.returnMsg(False, 'false')
        except:
            return public.returnMsg(False, 'false')

    # 更改端口
    def SetTomcatPort(self,get):
        port=get.port.strip()
        version=get.version.strip()

        if self.IsOpen(port):return public.returnMsg(False, '端口已经被占用!')
        if not self.Initialization(get.version): return public.returnMsg(False, "配置文件错误请检查配置文件")
        ret=self.TomcatSetPort(port=port)
        if ret:
            self.RestarTomcat(get.version)
            fs = firewalls.firewalls()
            get = mobj()
            get.port = port
            get.ps = 'tomcat外部端口'
            fs.AddAcceptPort(get)
            return public.returnMsg(True, '更改成功!')
        else:public.returnMsg(False, '更改失败')


    #查看端口
    def GetTomcatPort(self,get):
        if not self.Initialization(get.version): return public.returnMsg(False, "配置文件错误请检查配置文件")
        ret = self.GetPort()
        return public.returnMsg(True,ret)

    #查看二级目录
    def GeterPath(self,get):
        if not self.Initialization(get.version): return public.returnMsg(False, "配置文件错误请检查配置文件")
        ret = self.GetDomain(get.domain)
        if not ret: return public.returnMsg(True, ret)
        return public.returnMsg(True,ret)



    ##################################XML 操作部分#########################
    # 获取虚拟主机列表
    def GetVhosts(self):
        Hosts = self.__ENGINE.getchildren()
        data = []
        for host in Hosts:
            if host.tag != 'Host': continue;
            tmp = host.attrib
            ch = host.getchildren()
            tmp['item'] = {}
            for c in ch:
                tmp['item'][c.tag] = c.attrib
            data.append(tmp)
        return data

    # 添加虚拟主机
    def AddVhost(self, path, domain):
        if not os.path.exists(path): os.makedirs(path)
        if self.GetVhost(domain): return 111
        attr = {"appBase": path, "autoDeploy": "true", "name": domain, "unpackWARs": "true",
                "xmlNamespaceAware": "false", "xmlValidation": "false"}
        Host = Element("Host", attr)
        attr = {"docBase": path, "path": "", "reloadable": "true", "crossContext": "true", }
        Context = Element("Context", attr)
        Host.append(Context)
        self.__ENGINE.append(Host)
        self.Save()

        return True

    # 删除虚拟主机
    def DelVhost(self, domain):
        if domain=='localhost':return False
        host = self.GetVhost(domain)
        if not host: return False
        self.__ENGINE.remove(host)
        self.Save()
        return True

    # 获取指定虚拟主机
    def GetVhost(self, domain):
        Hosts = self.__ENGINE.getchildren()
        for host in Hosts:
            if host.tag != 'Host': continue;
            if host.attrib['name'] == domain:
                return host
        return None

    # 修改根目录
    def SetPath(self, domain, path):
        if not os.path.exists(path): public.ExecShell('mkdir -p %s'%path)
        host = self.GetVhost(domain)
        if not host: return False
        if host.attrib['appBase']=='webapps':return False
        host.attrib['appBase'] = path
        host.getchildren()[0].attrib['docBase'] = path
        self.Save()
        return True

    # 添加二级目录
    def AddPath(self, domain, name, path):
        #if self.ChekcDomain(domain):return False
        if self.CheckPath(domain, name): return False
        if not os.path.exists(path): os.makedirs(path)
        ret = self.GetVhost(domain)
        attr = {"docBase": path, "path": name, "reloadable": "true", }
        Context = Element("Context", attr)
        ret.append(Context)
        self.Save()
        return True

    # 判断是否存在这个二级目录
    def CheckPath(self, domain, path):
        ret = self.GetVhost(domain)
        for i in ret:
           if i.attrib.has_key('path'):
               if i.attrib['path'] == path:
                   return True
        else:
            return False

    # 删除二级目录
    def DelPath(self, domain, path):
        ret = self.GetVhost(domain)
        if not ret:return False
        for i in ret:
            if i.attrib.has_key('path'):
                if i.attrib['path'] == path:
                    ret.remove(i)
        self.Save()
        return True

    # 获取当前配置文件的端口


    # 修改虚拟主机属性
    def SetVhost2(self, domain, key, value):
        host = self.GetVhost(domain)
        if not host: return False
        host.attrib[key] = value
        self.Save()
        return True

    # 修改虚拟主机属性
    def SetVhost(self, domain,reloadable):
        Hosts = self.GetVhost(domain)
        if not Hosts:return False
        if reloadable:
            for i in Hosts:
                if i.attrib.has_key('reloadable'):
                    i.attrib['reloadable'] ="true"
        else:
            for i in Hosts:
                if i.attrib.has_key('reloadable'):
                    i.attrib['reloadable'] ="false"
        self.Save()
        return True

    # 查看 reloadable 信息
    def GetdomainVhost(self, domain):
        Hosts = self.GetVhost(domain)
        if not Hosts: return False

        for i in Hosts:
            if i.attrib.has_key('reloadable'):
                if i.attrib['reloadable'] =="true":
                    return True
                else:return False
        else:return False



    #获取端口号
    def GetPort(self):
        for i in self.__CONNECTROR:
            if i.attrib.has_key('protocol') and i.attrib.has_key('port'):
                if i.attrib['protocol']=='HTTP/1.1':
                    return int(i.attrib['port'])
        else:
            return int(8080)

    # 判断域名是否存在
    def ChekcDomain(self, domain):
        ret = self.GetVhosts()
        for i in ret:
            if i.has_key('name'):
                if i['name'] == domain:
                    return True
        else:
            return False

    def is_domain(self, domain):
        import re
        domain_regex = re.compile(
            r'(?:[A-Z0-9_](?:[A-Z0-9-_]{0,247}[A-Z0-9])?\.)+(?:[A-Z]{2,6}|[A-Z0-9-]{2,}(?<!-))\Z',
            re.IGNORECASE)
        return True if domain_regex.match(domain) else False

    # 整理配置文件格式
    def format(self, em, level=0):
        i = "\n" + level * "  "
        if len(em):
            if not em.text or not em.text.strip():
                em.text = i + "  "
            for e in em:
                self.format(e, level + 1)
            if not e.tail or not e.tail.strip():
                e.tail = i
        if level and (not em.tail or not em.tail.strip()):
            em.tail = i

    #给根节点加项目地址路径
    def AddLocalHost(self,name,path,domain='localhost'):
        ret=self.GetVhost(domain)
        if not  ret: return False
        for i in ret:
           if  i.attrib.has_key('path'):
               if i.attrib['path'] == name:
                   return False
        attr = {"docBase": path, "path": name, "reloadable": "true", }
        Context = Element("Context", attr)
        ret.append(Context)
        self.Save()
        return True

    # 取主域名
    def GetMainDomain(self):
        ret=self.GetVhosts()
        for i in ret:
            if i['item'].has_key('Valve'):
                return str(i['name'])
        else:
            return str('localhost')

    # 获取域名的appBase 信息
    def GetDomainPath(self,doamin):
        ret = self.GetVhosts()
        for i in ret:
            if i['name']==doamin:
                return str(i['appBase'])
        return False

    # 获取域名和路径信息
    def GetServerDomain(self):
        ret = []
        ret2 = self.GetVhosts()
        for i in ret2:
            rec = {}
            if i['item'].has_key('Valve'):
                rec['domain_main'] = i['name']
                rec['appBase'] = i['appBase']
                ret.append(rec)
            else:
                rec['appBase'] = i['appBase']
                rec['domain'] = i['name']
                ret.append(rec)
        return ret

    # 更新域名信息
    def GetDomainPath2(self,doamin,doamin2):
        self.__TREE.parse(self.__CONF_FILE)
        self.__ENGINE = self.__TREE.findall('Service/Engine')[0]
        Hosts = self.__ENGINE.getchildren()
        for host in Hosts:
            if host.tag != 'Host': continue;
            if host.attrib['name']==doamin:
                host.attrib['name']=doamin2
        self.Save()
        return True

    # 判断端口是否被占用
    def IsOpen(self, port):
        ip = '0.0.0.0'
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((ip, int(port)))
            s.shutdown(2)
            return True
        except:
            return False

    #更换端口
    def TomcatSetPort(self,port):
        for i in self.__CONNECTROR:
            if i.attrib.has_key('protocol') and i.attrib.has_key('port'):
                if i.attrib['protocol'] == 'HTTP/1.1':
                    i.attrib['port']=port
        self.Save()
        if self.GetPort()==int(port):return True
        else:return False


    # 查看二级目录
    def GetDomain(self,domain):
        ret=self.GetVhost(domain)
        resulet=[]
        if not ret: return False
        try:
            for i in ret:
                if i.attrib['path']:
                    resulet.append(i.attrib)
        except:
            return resulet
        return resulet

   # 保存配置
    def Save(self):
        self.format(self.__ROOT)
        self.__TREE.write(self.__CONF_FILE, 'utf-8')

if __name__ == '__main__':
    print(111)
    tom = tomcat2_main()
    tom.Xml_init('/www/server/tomcat9/conf/server.xml')
    print(tom.AddVhost(domain='www.aa2222.com', path='/tomcat/aa'))