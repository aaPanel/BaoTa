#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2017 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   docker管理插件
#+--------------------------------------------------------------------
import sys,os
if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
os.chdir('/www/server/panel');
sys.path.append("class/")
import docker,public,json

class docker_main:
    __docker = None;
    
    #实例化SDK
    def __init__(self):
        if not self.__docker: self.__docker = docker.from_env();
    
    #取容器列表
    def GetConList(self,get):
        conList = [];
        for con in self.__docker.containers.list(all=True):
            tmp = con.attrs;
            tmp['Created'] = self.utc_to_local(tmp['Created'].split('.')[0]);
            conList.append(tmp);
        return conList;
    
    
    # UTCS时间转换为时间戳
    def utc_to_local(self,utc_time_str, utc_format='%Y-%m-%dT%H:%M:%S'):
        import pytz,datetime,time
        local_tz = pytz.timezone('Asia/Chongqing')
        local_format = "%Y-%m-%d %H:%M"
        utc_dt = datetime.datetime.strptime(utc_time_str, utc_format)
        local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
        time_str = local_dt.strftime(local_format)
        return int(time.mktime(time.strptime(time_str, local_format)))
    
    #创建容器
    def CreateCon(self,get):
        try:
            conObject = self.__docker.containers.run(
                                                image = get.image,
                                                mem_limit = get.mem_limit + 'M',
                                                ports = eval(get.ports.replace('[','(').replace(']',')')),
                                                auto_remove = False,
                                                command = ['/bin/bash','/etc/init.d/bt start','systemctl stop firewalld','systemctl disable firewalld','service stop iptables'],
                                                detach = True,
                                                stdin_open = True,
                                                tty=True,
                                                entrypoint = '/usr/sbin/init',
                                                privileged = True,
                                                volumes = json.loads(get.volumes),
                                                cpu_shares = int(get.cpu_shares)
                                                );
            if conObject:
                #conObject.exec_run('(echo "'+get.ps.strip()+'";sleep 0.1;echo "'+get.ps.strip()+'")|passwd root',privileged = True,stdin = True);
                self.AcceptPort(get);
                return public.returnMsg(True,'创建成功!');
            
            return public.returnMsg(False,'创建失败!');
        except docker.errors.APIError as ex:
            return public.returnMsg(False,'创建失败!' + str(ex));
    
    #放行端口
    def AcceptPort(self,get):
        import firewalls
        f = firewalls.firewalls()
        get.ps = 'docker容器的端口';
        for port in json.loads(get.accept):
            get.port = port;
            f.AddAcceptPort(get)
        return True;
        
    #判断端口是否被占用
    def IsPortExists(self,get):
        tmp = public.ExecShell("lsof -i -P|grep '" + get.port + "'");
        if tmp[0]: return True;
        tmp = public.ExecShell("lsof -i -P|grep '*:" + get.port.split(':')[1] + "'");
        if tmp[0]: return True;
        return False;
    
    #删除容器
    def RemoveCon(self,get):
        try:
            conFind = self.__docker.containers.get(get.Hostname);
            conFind.remove()
            return public.returnMsg(True,'删除成功!');
        except:
            return public.returnMsg(False,'删除失败,请先停止该容器!');
    
    #查找容器
    def GetConFind(self,get):
        find = self.__docker.containers.get(get.Hostname);
        if not find: return None;
        return find.attrs;
    
    #启动容器
    def RunCon(self,get):
        try:
            conFind = self.__docker.containers.get(get.Hostname);
            if not conFind: return public.returnMsg(False,'指定容器不存在!');
            conFind.start();
            conFind.exec_run('/etc/init.d/bt start');
            return public.returnMsg(True,'启动成功!');
        except docker.errors.APIError as ex:
            return public.returnMsg(False,'启动失败!' + str(ex));
    
    #停止容器
    def StopCon(self,get):
        try:
            conFind = self.__docker.containers.get(get.Hostname);
            if not conFind: return public.returnMsg(False,'指定容器不存在!');
            conFind.stop();
            return public.returnMsg(True,'停止成功!');
        except docker.errors.APIError as ex:
            return public.returnMsg(False,'停止失败!' + str(ex));
    
    #重启容器
    def RestartCon(self,get):
        try:
            conFind = self.__docker.containers.get(get.Hostname);
            if not conFind: return public.returnMsg(False,'指定容器不存在!');
            conFind.restart();
            return public.returnMsg(True,'重启成功!');
        except docker.errors.APIError as ex:
            return public.returnMsg(False,'重启成功!' + str(ex));
        
    #内存配额
    def MemLimit(self,get):
        pass
    
    #CPU配额
    def CpuLimit(self,get):
        pass
    
    #添加磁盘
    def AddDisk(self,get):
        pass
    
    #绑定磁盘
    def BindingDisk(self,get):
        pass
    
    #取创建依赖
    def GetCreateInfo(self,get):
        import psutil;
        data = {}
        data['images'] = self.GetImageList(None);
        data['memSize'] = psutil.virtual_memory().total / 1024 / 1024;
        data['iplist'] = self.GetIPList(None);
        return data;
    
    #取IP列表
    def GetIPList(self,get):
        ipConf = '/www/server/panel/plugin/docker/iplist.json';
        if not os.path.exists(ipConf): return [];
        iplist = json.loads(public.readFile(ipConf));
        return iplist;
    
    #添加IP
    def AddIP(self,get):
        ipConf = '/www/server/panel/plugin/docker/iplist.json';
        if not os.path.exists(ipConf): 
            iplist = [];
            public.writeFile(ipConf,json.dumps(iplist));
        
        iplist = json.loads(public.readFile(ipConf));
        ipInfo = {'address':get.address,'netmask':get.netmask,'gateway':get.gateway};
        iplist.append(ipInfo);
        public.writeFile(ipConf,json.dumps(iplist));
        return public.returnMsg(True,'添加成功!');
    
    #删除IP
    def DelIP(self,get):
        ipConf = '/www/server/panel/plugin/docker/iplist.json';
        if not os.path.exists(ipConf): return public.returnMsg(False,'指定IP不存在!');
        iplist = json.loads(public.readFile(ipConf));
        newList = [];
        for ipInfo in iplist:
            if ipInfo['address'] == get.address: continue;
            newList.append(ipInfo);
        public.writeFile(ipConf,json.dumps(newList));
        return public.returnMsg(True,'删除成功!');
        
    
    #生成快照
    def Snapshot(self,get):
        try:
            ConObject = self.GetConFind(get.Hostname);
            ConObject.commit(repository = get.imageName,tag = get.tag,message = get.message,author = get.author,changes = get.chenges);
            return public.returnMsg(True,'操作成功!');
        except docker.errors.APIError as ex:
            return public.returnMsg(False,'操作失败: ' + str(ex));
    
    #制作镜像
    def CommitCon(self,get):
        try:
            ConObject = self.GetConFind(get.Hostname);
            ConObject.commit(repository = get.imageName,tag = get.tag,message = get.message,author = get.author,changes = get.chenges);
            return public.returnMsg(True,'操作成功!');
        except docker.errors.APIError as ex:
            return public.returnMsg(False,'操作失败: ' + str(ex));
    
    #取镜像列表
    def GetImageList(self,get):
        imageList = [];
        for image in self.__docker.images.list():
            tmp_attrs = image.attrs;
            tmp_image = {}
            tmp_image['Id'] = tmp_attrs['Id'].split(':')[1][:12];
            tmp_image['RepoTags'] = tmp_attrs['RepoTags'][0];
            tmp_image['Size'] = tmp_attrs['Size'];
            tmp_image['Labels'] = tmp_attrs['Config']['Labels'];
            tmp_image['Comment'] = tmp_attrs['Comment'];
            imageList.append(tmp_image);
        return imageList;
    
    #删除镜像
    def RemoveImage(self,get):    
        try:
            conFind = self.__docker.images.remove(get.imageId);
            return public.returnMsg(True,'删除成功!');
        except docker.errors.APIError as ex:
            return public.returnMsg(False,'删除失败,该镜像当前正在被使用!' + str(ex));
        
    
    #
    
    
    #用户管理页面
    def UserAdmin(self,get):
        return public.readFile('/www/server/panel/plugin/docker/userdocker.html');
    
    #用户登陆
    def UserLogin(self,get):
        return public.readFile('/www/server/panel/plugin/docker/login-docker.html');