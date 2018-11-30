#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 x3
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2017 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <2879625666@qq.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   宝塔gitlab插件
#+--------------------------------------------------------------------

import public,json,os,time;
class obj: id=0;
class gitlab_main:
    __setupPath = 'plugin/gitlab';
    __panelPath = '/www/server/panel';
    
    #获取服务状态
    def GetStatus(self,get):
        try:
            data = {}
            data['status'] = True;
            data['port'] = self.GetPort(get)
            data['url'] = 'http://' + public.GetLocalIp() + ':' + data['port'];
            data['msg'] = '获取成功!'
            tmp = public.ExecShell('/usr/bin/gitlab-ctl status')[0].replace(':','').replace(')','').split('\n');
            if len(tmp) < 5: return public.returnMsg(False,'未安装');
            
            data['list'] = []
            for t in tmp:
                t = t.split();
                if len(t) < 3: continue
                m = {}
                m['status'] = False
                if t[0] == 'run': m['status'] = True;
                m['name'] = t[1];
                m['pid'] = t[3]
                data['list'].append(m)
            return data;
        except:
            return public.returnMsg(False,'未找到相关配置，gitlab可能已损坏!');
        
    
    #服务控制
    def ServiceAdmin(self,get):
        if get.status == 'stop':
            os.system('/usr/bin/gitlab-ctl stop');
            msg='GitLab服务已停止'
        elif get.status == 'start':
            os.system('/usr/bin/gitlab-ctl start');
            msg='GitLab服务已启动,请等待1分钟后再访问GitLab'
        elif get.status == 'restart':
            os.system('/usr/bin/gitlab-ctl restart');
            msg='GitLab服务已重启成功,请等待1分钟后再访问GitLab'
        
        public.WriteLog('GitLab',msg);
        return public.returnMsg(True,msg);
    
    
    #获取端口
    def GetPort(self,get):
        #检查配置文件是否存在
        configFile = '/var/opt/gitlab/nginx/conf/gitlab-http.conf';
        if not os.path.exists(configFile): return public.returnMsg(False,'未找到相关配置，gitlab可能已损坏!');
        conf = public.readFile(configFile);
        
        #获取当前端口
        import re;
        rep = "listen\s+\*:(\d+);"
        return re.search(rep,conf).groups()[0];
    
    #修改端口
    def SetPort(self,get):
        try:
            #检查端口合法性
            checkPorts = ['80','8888','888','8098','8080','8081','8090','22','21','443','8443','20']
            if get.port in checkPorts: return public.returnMsg(False,'不能使用[' + get.port+']作为gitlab端口!');
            
            #检查配置文件是否存在
            configFile = '/var/opt/gitlab/nginx/conf/gitlab-http.conf';
            if not os.path.exists(configFile): return public.returnMsg(False,'未找到相关配置，gitlab可能已损坏!');
            conf = public.readFile(configFile);
            
            #取旧端口
            import re;
            rep = "listen\s+\*:(\d+);"
            oldport =  re.search(rep,conf).groups()[0];
            if oldport == get.port: return public.returnMsg(True,'修改成功!');
            
            #修改端口配置
            conf = conf.replace(':' + oldport,':' + get.port);
            public.writeFile(configFile,conf);
            os.system('/usr/bin/gitlab-ctl restart');
            
            #从防火墙放行新端口
            import firewalls
            get.ps = 'GitLab端口';
            fw = firewalls.firewalls()
            fw.AddAcceptPort(get)
            
            #从防火墙删除旧端口
            msg = '端口成功修改为['+get.port+'],请等待1分钟后再访问GitLab!';
            get.id = public.M('firewall').where('port=?',(oldport,)).getField('id');
            if not get.id: get.id = 0;
            get.port = oldport
            fw.DelAcceptPort(get);
            
            public.WriteLog('GitLab',msg);
            return public.returnMsg(True,msg);
        except Exception as ex:
            msg='端口修改失败!<br>错误信息：<br>' + str(ex)
            public.WriteLog('GitLab',msg);
            return public.returnMsg(True,msg);
        
        
    def GetSSHKey(self,get):
        path = '/root/.ssh/id_rsa.pub';
        if not os.path.exists(path): os.system('ssh-keygen -t rsa -C "GitLab-SSHKey" -f /root/.ssh/id_rsa -q -N ""')
        
        if get.setkey == '1':
            os.system('rm -rf /root/.ssh/id_rsa*')
            os.system('ssh-keygen -t rsa -C "GitLab-SSHKey" -f /root/.ssh/id_rsa -q -N ""')
            public.WriteLog('GitLab','已重新生成SSHKey');
            
        sshKey = public.readFile(path);
        return sshKey;
        
        
        