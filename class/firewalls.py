#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 x3
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http:#bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------
import sys,os,public,re,firewalld,time
class firewalls:
    __isFirewalld = False
    __isUfw = False
    __Obj = None
    
    def __init__(self):
        if os.path.exists('/usr/sbin/firewalld'): self.__isFirewalld = True
        if os.path.exists('/usr/sbin/ufw'): self.__isUfw = True
        if self.__isFirewalld:
            try:
                self.__Obj = firewalld.firewalld()
                self.GetList()
            except:
                pass
        
    
    #获取服务端列表
    def GetList(self):
        try:
            data = {}
            data['ports'] = self.__Obj.GetAcceptPortList()
            addtime = time.strftime('%Y-%m-%d %X',time.localtime())
            for i in range(len(data['ports'])):
                tmp = self.CheckDbExists(data['ports'][i]['port'])
                if not tmp: public.M('firewall').add('port,ps,addtime',(data['ports'][i]['port'],'',addtime))
                          
            data['iplist'] = self.__Obj.GetDropAddressList()
            for i in range(len(data['iplist'])):
                try:
                    tmp = self.CheckDbExists(data['iplist'][i]['address'])
                    if not tmp: public.M('firewall').add('port,ps,addtime',(data['iplist'][i]['address'],'',addtime))
                except:
                    pass
        except:
            pass
    
    #检查数据库是否存在
    def CheckDbExists(self,port):
        data = public.M('firewall').field('id,port,ps,addtime').select()
        for dt in data:
            if dt['port'] == port: return dt
        return False
        
    #重载防火墙配置
    def FirewallReload(self):
        if self.__isUfw:
            public.ExecShell('/usr/sbin/ufw reload')
            return
        if self.__isFirewalld:
            public.ExecShell('firewall-cmd --reload')
        else:
            public.ExecShell('/etc/init.d/iptables save')
            public.ExecShell('/etc/init.d/iptables restart')

    #取防火墙状态
    def CheckFirewallStatus(self):
        if self.__isUfw:
            return 1

        if self.__isFirewalld:
            res = public.ExecShell("systemctl status firewalld")[0]
            if res.find('active (running)') != -1: return 1
            if res.find('disabled') != -1: return -1
            if res.find('inactive (dead)') != -1: return 0
        else:
            return 1
        
    #添加屏蔽IP
    def AddDropAddress(self,get):
        import time
        import re
        ip_format = get.port.split('/')[0]
        if not public.check_ip(ip_format): return public.returnMsg(False,'FIREWALL_IP_FORMAT')
        if ip_format in  ['0.0.0.0','127.0.0.0',"::1"]: return public.returnMsg(False,'请不要花样作死!')
        address = get.port
        if public.M('firewall').where("port=?",(address,)).count() > 0: return public.returnMsg(False,'FIREWALL_IP_EXISTS')
        if self.__isUfw:
            public.ExecShell('ufw insert 1 deny from ' + address + ' to any')
        else:
            if self.__isFirewalld:
                #self.__Obj.AddDropAddress(address)
                if public.is_ipv6(ip_format):
                    public.ExecShell('firewall-cmd --permanent --add-rich-rule=\'rule family=ipv6 source address="'+ address +'" drop\'')
                else:
                    public.ExecShell('firewall-cmd --permanent --add-rich-rule=\'rule family=ipv4 source address="'+ address +'" drop\'')
            else:
                if public.is_ipv6(ip_format): return public.returnMsg(False,'FIREWALL_IP_FORMAT')
                public.ExecShell('iptables -I INPUT -s '+address+' -j DROP')
        
        public.WriteLog("TYPE_FIREWALL", 'FIREWALL_DROP_IP',(address,))
        addtime = time.strftime('%Y-%m-%d %X',time.localtime())
        public.M('firewall').add('port,ps,addtime',(address,get.ps,addtime))
        self.FirewallReload()
        return public.returnMsg(True,'ADD_SUCCESS')
    
    
    #删除IP屏蔽
    def DelDropAddress(self,get):
        address = get.port
        id = get.id
        ip_format = get.port.split('/')[0]
        if self.__isUfw:
            public.ExecShell('ufw delete deny from ' + address + ' to any')
        else:
            if self.__isFirewalld:
                #self.__Obj.DelDropAddress(address)
                if public.is_ipv6(ip_format):
                    public.ExecShell('firewall-cmd --permanent --remove-rich-rule=\'rule family=ipv6 source address="'+ address +'" drop\'')
                else:
                    public.ExecShell('firewall-cmd --permanent --remove-rich-rule=\'rule family=ipv4 source address="'+ address +'" drop\'')
            else:
                public.ExecShell('iptables -D INPUT -s '+address+' -j DROP')
        
        public.WriteLog("TYPE_FIREWALL",'FIREWALL_ACCEPT_IP',(address,))
        public.M('firewall').where("id=?",(id,)).delete()
        
        self.FirewallReload()
        return public.returnMsg(True,'DEL_SUCCESS')
    
    
    #添加放行端口
    def AddAcceptPort(self,get):
        import re
        src_port = get.port
        get.port = get.port.replace('-',':')
        rep = r"^\d{1,5}(:\d{1,5})?$"
        if not re.search(rep,get.port):
            return public.returnMsg(False,'PORT_CHECK_RANGE')

        import time
        port = get.port
        ps = get.ps
        is_exists = public.M('firewall').where("port=? or port=?",(port,src_port)).count()
        if is_exists: return public.returnMsg(False,'端口已经放行过了!')
        notudps = ['80','443','8888','888','39000:40000','21','22']
        if self.__isUfw:
            public.ExecShell('ufw allow ' + port + '/tcp')
            if not port in notudps: public.ExecShell('ufw allow ' + port + '/udp')
        else:
            if self.__isFirewalld:
                #self.__Obj.AddAcceptPort(port)
                port = port.replace(':','-')
                public.ExecShell('firewall-cmd --permanent --zone=public --add-port='+port+'/tcp')
                if not port in notudps: public.ExecShell('firewall-cmd --permanent --zone=public --add-port='+port+'/udp')
            else:
                public.ExecShell('iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport '+port+' -j ACCEPT')
                if not port in notudps: public.ExecShell('iptables -I INPUT -p tcp -m state --state NEW -m udp --dport '+port+' -j ACCEPT')
        public.WriteLog("TYPE_FIREWALL", 'FIREWALL_ACCEPT_PORT',(port,))
        addtime = time.strftime('%Y-%m-%d %X',time.localtime())
        if not is_exists: public.M('firewall').add('port,ps,addtime',(port,ps,addtime))
        self.FirewallReload()
        return public.returnMsg(True,'ADD_SUCCESS')


    #添加放行端口
    def AddAcceptPortAll(self,port,ps):
        import re
        port = port.replace('-',':')
        rep = r"^\d{1,5}(:\d{1,5})?$"
        if not re.search(rep,port):
            return False
        if self.__isUfw:
            public.ExecShell('ufw allow ' + port + '/tcp')
            public.ExecShell('ufw allow ' + port + '/udp')
        else:
            if self.__isFirewalld:
                port = port.replace(':','-')
                public.ExecShell('firewall-cmd --permanent --zone=public --add-port='+port+'/tcp')
                public.ExecShell('firewall-cmd --permanent --zone=public --add-port='+port+'/udp')
            else:
                public.ExecShell('iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport '+port+' -j ACCEPT')
                public.ExecShell('iptables -I INPUT -p tcp -m state --state NEW -m udp --dport '+port+' -j ACCEPT')
        return True
    
    #删除放行端口
    def DelAcceptPort(self,get):
        port = get.port
        id = get.id
        try:
            if(port == public.GetHost(True) or port == public.readFile('data/port.pl').strip()): return public.returnMsg(False,'FIREWALL_PORT_PANEL')
            if self.__isUfw:
                public.ExecShell('ufw delete allow ' + port + '/tcp')
                public.ExecShell('ufw delete allow ' + port + '/udp')
            else:
                if self.__isFirewalld:
                    #self.__Obj.DelAcceptPort(port)
                    public.ExecShell('firewall-cmd --permanent --zone=public --remove-port='+port+'/tcp')
                    public.ExecShell('firewall-cmd --permanent --zone=public --remove-port='+port+'/udp')
                else:
                    public.ExecShell('iptables -D INPUT -p tcp -m state --state NEW -m tcp --dport '+port+' -j ACCEPT')
                    public.ExecShell('iptables -D INPUT -p tcp -m state --state NEW -m udp --dport '+port+' -j ACCEPT')
            public.WriteLog("TYPE_FIREWALL", 'FIREWALL_DROP_PORT',(port,))
            public.M('firewall').where("id=?",(id,)).delete()
            
            self.FirewallReload()
            return public.returnMsg(True,'DEL_SUCCESS')
        except:
            return public.returnMsg(False,'DEL_ERROR')
    
    #设置远程端口状态
    def SetSshStatus(self,get):
        version = public.readFile('/etc/redhat-release')
        if int(get['status'])==1:
            msg = public.getMsg('FIREWALL_SSH_STOP')
            act = 'stop'
        else:
            msg = public.getMsg('FIREWALL_SSH_START')
            act = 'start'
        
        if not os.path.exists('/etc/redhat-release'):
            public.ExecShell('service ssh ' + act)
        elif version.find(' 7.') != -1 or version.find(' 8.') != -1 or version.find('Fedora') != -1:
            public.ExecShell("systemctl "+act+" sshd.service")
        else:
            public.ExecShell("/etc/init.d/sshd "+act)
        
        public.WriteLog("TYPE_FIREWALL", msg)
        return public.returnMsg(True,'SUCCESS')

        
    
    
    #设置ping
    def SetPing(self,get):
        if get.status == '1':
            get.status = '0'
        else:
            get.status = '1'
        filename = '/etc/sysctl.conf'
        conf = public.readFile(filename)
        if conf.find('net.ipv4.icmp_echo') != -1:
            rep = r"net\.ipv4\.icmp_echo.*"
            conf = re.sub(rep,'net.ipv4.icmp_echo_ignore_all='+get.status,conf)
        else:
            conf += "\nnet.ipv4.icmp_echo_ignore_all="+get.status
            
        
        public.writeFile(filename,conf)
        public.ExecShell('sysctl -p')
        return public.returnMsg(True,'SUCCESS') 
        
    
    
    #改远程端口
    def SetSshPort(self,get):
        port = get.port
        if int(port) < 22 or int(port) > 65535: return public.returnMsg(False,'FIREWALL_SSH_PORT_ERR')
        ports = ['21','25','80','443','8080','888','8888']
        if port in ports: return public.returnMsg(False,'请不要使用常用程序的默认端口!')
        file = '/etc/ssh/sshd_config'
        conf = public.readFile(file)
        
        rep = r"#*Port\s+([0-9]+)\s*\n"
        conf = re.sub(rep, "Port "+port+"\n", conf)
        public.writeFile(file,conf)
        
        if self.__isFirewalld:
            public.ExecShell('firewall-cmd --permanent --zone=public --add-port='+port+'/tcp')
            public.ExecShell('setenforce 0')
            public.ExecShell('sed -i "s#SELINUX=enforcing#SELINUX=disabled#" /etc/selinux/config')
            public.ExecShell("systemctl restart sshd.service")
        elif self.__isUfw:
            public.ExecShell('ufw allow ' + port + '/tcp')
            public.ExecShell("service ssh restart")
        else:
            public.ExecShell('iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport '+port+' -j ACCEPT')
            public.ExecShell("/etc/init.d/sshd restart")
        
        self.FirewallReload()
        public.M('firewall').where("ps=? or ps=? or port=?",('SSH远程管理服务','SSH远程服务',port)).delete()
        public.M('firewall').add('port,ps,addtime',(port,'SSH远程服务',time.strftime('%Y-%m-%d %X',time.localtime())))
        public.WriteLog("TYPE_FIREWALL", "FIREWALL_SSH_PORT",(port,))
        return public.returnMsg(True,'EDIT_SUCCESS') 
    
    #取SSH信息
    def GetSshInfo(self,get):
        file = '/etc/ssh/sshd_config'
        conf = public.readFile(file)
        if not conf: conf = ''
        rep = r"#*Port\s+([0-9]+)\s*\n"
        tmp1 = re.search(rep,conf)
        port = '22'
        if tmp1:
            port = tmp1.groups(0)[0]
        import system
        panelsys = system.system()
        
        version = panelsys.GetSystemVersion()
        if os.path.exists('/usr/bin/apt-get'):
            if os.path.exists('/etc/init.d/sshd'):
                status = public.ExecShell("service sshd status | grep -P '(dead|stop)'|grep -v grep")
            else:
                status = public.ExecShell("service ssh status | grep -P '(dead|stop)'|grep -v grep")
        else:
            if version.find(' 7.') != -1 or version.find(' 8.') != -1 or version.find('Fedora') != -1:
                status = public.ExecShell("systemctl status sshd.service | grep 'dead'|grep -v grep")
            else:
                status = public.ExecShell("/etc/init.d/sshd status | grep -e 'stopped' -e '已停'|grep -v grep")
            
#       return status;
        if len(status[0]) > 3:
            status = False
        else:
            status = True
        isPing = True
        try:
            file = '/etc/sysctl.conf'
            conf = public.readFile(file)
            rep = r"#*net\.ipv4\.icmp_echo_ignore_all\s*=\s*([0-9]+)"
            tmp = re.search(rep,conf).groups(0)[0]
            if tmp == '1': isPing = False
        except:
            isPing = True
        
        data = {}
        data['port'] = port
        data['status'] = status
        data['ping'] = isPing
        return data
        
    