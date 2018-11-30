#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 x3
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2017 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   宝塔安全登陆插件
#+--------------------------------------------------------------------
import sys;
sys.path.append('class/');
import public,json,os,time,binascii,urllib,re;
class safelogin_main:
    __PANEL_SSL = None;
    __PDATA = None;
    __APIURL = 'https://www.bt.cn/api/Auth';
    __UPATH = 'data/userInfo.json';
    __DENY = '/etc/hosts.deny';
    __ALLOW = '/etc/hosts.allow';
    __LIMIT_CONF = 'data/limitip.conf';
    __userInfo = None;
    def __init__(self):
        pdata = {}
        data = {}
        if os.path.exists(self.__UPATH):
            self.__userInfo = json.loads(public.readFile(self.__UPATH));
            if self.__userInfo:
                pdata['access_key'] = self.__userInfo['access_key'];
                data['secret_key'] = self.__userInfo['secret_key'];
        else:
            pdata['access_key'] = 'test';
            data['secret_key'] = '123456';
        pdata['data'] = data;
        self.__PDATA = pdata;
        
    #生成并发送Token
    def SendToken(self,get = None):
        return False;        
    
    #获取服务器密钥
    def GetServerToken(self,get):
        password = public.M('users').where('id=?',(1,)).getField('password');
        if password != public.md5(get.password): return public.returnMsg(False,'密码验证失败!');
        tokenFile = 'plugin/safelogin/token.pl';
        if not os.path.exists(tokenFile):
            tokenStr = public.GetRandomString(64);
            public.writeFile(tokenFile,tokenStr);
        else:
            tokenStr = public.readFile(tokenFile);
        public.ExecShell('chattr +i ' + tokenFile);
        return tokenStr.strip();
    
    #获取服务器信息
    def GetServerInfo(self,get):
        #self.SendToken();
        self.__init__();
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data']);
        result = json.loads(public.httpPost(self.__APIURL + '/GetServerInfo',self.__PDATA));
        result['data'] = self.En_Code(result['data']);
        return result;
        
    #获取Token
    def GetToken(self,get):
        data = {}
        data['username'] = get.username;
        data['password'] = public.md5(get.password);
        pdata = {}
        pdata['data'] = self.De_Code(data);
        result = json.loads(public.httpPost(self.__APIURL+'/GetToken',pdata));
        result['data'] = self.En_Code(result['data']);
        if result['data']: public.writeFile(self.__UPATH,json.dumps(result['data']));
        del(result['data']);
        return result;
        
    #获取节点列表
    def get_node_list(self,get):
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data']);
        result = json.loads(public.httpPost(self.__APIURL + '/GetNodeList',self.__PDATA));
        result['data'] = self.En_Code(result['data']);
        return result;
    
    #添加SSH许可IP
    def add_ssh_limit(self,get):
        ip = get.ip;
        denyConf = public.readFile(self.__DENY);
        if denyConf.find('sshd:ALL') == -1:
            while denyConf[-1:] == "\n" or denyConf[-1:] == " ": denyConf = denyConf[:-1];
            denyConf += "\nsshd:ALL\n";
            public.writeFile(self.__DENY,denyConf);
        if ip in self.get_ssh_limit(): return public.returnMsg(True,'指定IP白名单已存在!');
        
        allowConf = public.readFile(self.__ALLOW).strip();
        while allowConf[-1:] == "\n" or allowConf[-1:] == " ": allowConf = allowConf[:-1];
        allowConf += "\nsshd:" + ip+":allow\n";
        public.writeFile(self.__ALLOW,allowConf);
        
        if ip in self.get_ssh_limit(): return public.returnMsg(True,'添加成功!');
        return public.returnMsg(False,'添加失败!');
    
    #删除SSH许可IP
    def remove_ssh_limit(self,get):
        ip = get.ip;
        if not ip in self.get_ssh_limit(): return public.returnMsg(True,'指定白名单不存在!');
        allowConf = public.readFile(self.__ALLOW).strip();
        while allowConf[-1:] == "\n" or allowConf[-1:] == " ": allowConf = allowConf[:-1];
        allowConf = re.sub("\nsshd:"+ip+":allow\n?","\n",allowConf);
        public.writeFile(self.__ALLOW,allowConf+"\n");
        return public.returnMsg(True,'删除成功!');
    
    #获取当前SSH许可IP
    def get_ssh_limit(self,get = None):
        allowConf = public.readFile(self.__ALLOW);
        return re.findall("sshd:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):allow",allowConf);
    
    #获取登陆记录
    def get_login_log(self,get):
        return public.M('logs').where('type=?',(u'用户登录',)).field('log,addtime').select();
    
    #取当前面板登陆许可
    def get_panel_limit(self,get = None):
        conf = public.readFile(self.__LIMIT_CONF)
        if not conf: conf = '';
        limitIp = conf.split(',');
        if '' in limitIp: limitIp.remove('');
        return limitIp;
    
    #添加面板许可登陆IP
    def add_panel_limit(self,get):
        limitIp = self.get_panel_limit();
        if get.ip in limitIp: return public.returnMsg(True,'指定IP白名单已存在!');
        limitIp.append(get.ip);
        public.writeFile(self.__LIMIT_CONF,','.join(limitIp));
        return public.returnMsg(True,'添加成功!');
    
    #删除面板许可登陆IP
    def remove_panel_limit(self,get):
        limitIp = self.get_panel_limit();
        if not get.ip in limitIp: return public.returnMsg(True,'指定IP白名单不存在!');
        limitIp.remove(get.ip);
        public.writeFile(self.__LIMIT_CONF,','.join(limitIp));
        return public.returnMsg(True,'删除成功!');
    
    #清除SSH许可限制
    def close_ssh_limit(self,get):
        #清除白名单
        allowConf = public.readFile(self.__ALLOW);
        allowConf = re.sub("\n\s*sshd:\w{1,3}\.\w{1,3}\.\w{1,3}\.\w{1,3}:allow",'',allowConf);
        public.writeFile(self.__ALLOW,allowConf);
        
        #关闭限制
        denyConf = public.readFile(self.__DENY);
        denyConf = re.sub("sshd:ALL\s*","",denyConf);
        public.writeFile(self.__DENY,denyConf);
        return public.returnMsg(True,'清除成功!');
    
    #清除面板登陆许可
    def close_panel_limit(self,get):
        if os.path.exists(self.__LIMIT_CONF): os.remove(self.__LIMIT_CONF);
        return public.returnMsg(True,'已关闭IP限制!');
    
    #获取操作系统信息
    def get_system_info(self,get):
        import system;
        s = system.system();
        data = s.GetSystemTotal(get,0.1);
        data['disk'] = s.GetDiskInfo2();
        return data;
    
    #获取环境信息
    def get_service_info(self,get):
        import system;
        serviceInfo = system.system().GetConcifInfo(get);
        del(serviceInfo['mysql_root']);
        return serviceInfo;
    
    #获取用户绑定信息
    def get_user_info(self,get):
        return self.__userInfo;
    
    #设置用户绑定信息
    def set_user_info(self,get):
        data = {}
        data['username'] = get.username;
        data['password'] = public.md5(get.password);
        pdata = {}
        pdata['data'] = self.De_Code(data);
        result = json.loads(public.httpPost(self.__APIURL+'/GetToken',pdata));
        result['data'] = self.En_Code(result['data']);
        if result['data']: public.writeFile(self.__UPATH,json.dumps(result['data']));
        del(result['data']);
        return result;
    
    
    #获取SSH爆破次数
    def get_ssh_errorlogin(self,get):
        path = '/var/log/secure'
        if not os.path.exists(path): public.writeFile(path,'');
        fp = open(path,'r');
        l = fp.readline();
        data = {};
        data['intrusion'] = [];
        data['intrusion_total'] = 0;
        
        data['defense'] = [];
        data['defense_total'] = 0;
        
        data['success'] = [];
        data['success_total'] = 0;
        
        limit = 100;
        while l:
            if l.find('Failed password for root') != -1: 
                if len(data['intrusion']) > limit: del(data['intrusion'][0]);
                data['intrusion'].append(l);
                data['intrusion_total'] += 1;
            elif l.find('Accepted') != -1:
                if len(data['success']) > limit: del(data['success'][0]);
                data['success'].append(l);
                data['success_total'] += 1;
            elif l.find('refused') != -1:
                if len(data['defense']) > limit: del(data['defense'][0]);
                data['defense'].append(l);
                data['defense_total'] += 1;
            l = fp.readline();
            
        months = {'Jan':'01','Feb':'02','Mar':'03','Apr':'04','May':'05','Jun':'06','Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'}
        
        intrusion = [];
        for g in data['intrusion']:
            tmp = {}
            tmp1 = g.split();
            tmp['date'] = months[tmp1[0]] + '/' + tmp1[1] + ' ' + tmp1[2];
            tmp['user'] = tmp1[8];
            tmp['address'] = tmp1[10];
            intrusion.append(tmp);
            
        data['intrusion'] = intrusion;
        
        success = [];
        for g in data['success']:
            tmp = {}
            tmp1 = g.split();
            tmp['date'] = months[tmp1[0]] + '/' + tmp1[1] + ' ' + tmp1[2];
            tmp['user'] = tmp1[8];
            tmp['address'] = tmp1[10];
            success.append(tmp);
        data['success'] = success;
        
        defense = []
        for g in data['defense']:
            tmp = {}
            tmp1 = g.split();
            tmp['date'] = months[tmp1[0]] + '/' + tmp1[1] + ' ' + tmp1[2];
            tmp['user'] = '-';
            tmp['address'] = tmp1[8];
            defense.append(tmp);
        data['defense'] = defense;
        import firewalls;
        data['ssh'] = firewalls.firewalls().GetSshInfo(get);
        return data;
    
    #加密数据
    def De_Code(self,data):
        if sys.version_info[0] == 2:
            pdata = urllib.urlencode(data);
        else:
            pdata = urllib.parse.urlencode(data);
            if type(pdata) == str: pdata = pdata.encode('utf-8')
        return binascii.hexlify(pdata);

    
    #解密数据
    def En_Code(self,data):
        if sys.version_info[0] == 2:
            result = urllib.unquote(binascii.unhexlify(data));
        else:
            if type(data) == str: data = data.encode('utf-8')
            tmp = binascii.unhexlify(data)
            if type(tmp) != str: tmp = tmp.decode('utf-8')
            result = urllib.parse.unquote(tmp)

        if type(result) != str: result = result.decode('utf-8')
        return json.loads(result);

    