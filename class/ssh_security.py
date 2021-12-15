#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2017 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: 梁凯强 <1249648969@qq.com>
#-------------------------------------------------------------------
# SSH 安全类
#------------------------------
import public,os,re,send_mail,json
from datetime import datetime

class ssh_security:
    __SSH_CONFIG='/etc/ssh/sshd_config'
    __ip_data = None
    __ClIENT_IP='/www/server/panel/data/host_login_ip.json'
    __REPAIR={"1":{"id":1,"type":"file","harm":"高","repaired":"1","level":"3","name":"确保SSH MaxAuthTries 设置为3-6之间","file":"/etc/ssh/sshd_config","Suggestions":"加固建议   在/etc/ssh/sshd_config 中取消MaxAuthTries注释符号#, 设置最大密码尝试失败次数3-6 建议为4","repair":"MaxAuthTries 4","rule":[{"re":"\nMaxAuthTries\\s*(\\d+)","check":{"type":"number","max":7,"min":3}}],"repair_loophole":[{"re":"\n?#?MaxAuthTries\\s*(\\d+)","check":"\nMaxAuthTries 4"}]},"2":{"id":2,"repaired":"1","type":"file","harm":"高","level":"3","name":"SSHD 强制使用V2安全协议","file":"/etc/ssh/sshd_config","Suggestions":"加固建议   在/etc/ssh/sshd_config 文件按如相下设置参数","repair":"Protocol 2","rule":[{"re":"\nProtocol\\s*(\\d+)","check":{"type":"number","max":3,"min":1}}],"repair_loophole":[{"re":"\n?#?Protocol\\s*(\\d+)","check":"\nProtocol 2"}]},"3":{"id":3,"repaired":"1","type":"file","harm":"高","level":"3","name":"设置SSH空闲超时退出时间","file":"/etc/ssh/sshd_config","Suggestions":"加固建议   在/etc/ssh/sshd_config 将ClientAliveInterval设置为300到900，即5-15分钟，将ClientAliveCountMax设置为0-3","repair":"ClientAliveInterval 600  ClientAliveCountMax 2","rule":[{"re":"\nClientAliveInterval\\s*(\\d+)","check":{"type":"number","max":900,"min":300}}],"repair_loophole":[{"re":"\n?#?ClientAliveInterval\\s*(\\d+)","check":"\nClientAliveInterval 600"}]},"4":{"id":4,"repaired":"1","type":"file","harm":"高","level":"3","name":"确保SSH LogLevel 设置为INFO","file":"/etc/ssh/sshd_config","Suggestions":"加固建议   在/etc/ssh/sshd_config 文件以按如下方式设置参数（取消注释）","repair":"LogLevel INFO","rule":[{"re":"\nLogLevel\\s*(\\w+)","check":{"type":"string","value":["INFO"]}}],"repair_loophole":[{"re":"\n?#?LogLevel\\s*(\\w+)","check":"\nLogLevel INFO"}]},"5":{"id":5,"repaired":"1","type":"file","harm":"高","level":"3","name":"禁止SSH空密码用户登陆","file":"/etc/ssh/sshd_config","Suggestions":"加固建议  在/etc/ssh/sshd_config 将PermitEmptyPasswords配置为no","repair":"PermitEmptyPasswords no","rule":[{"re":"\nPermitEmptyPasswords\\s*(\\w+)","check":{"type":"string","value":["no"]}}],"repair_loophole":[{"re":"\n?#?PermitEmptyPasswords\\s*(\\w+)","check":"\nPermitEmptyPasswords no"}]},"6":{"id":6,"repaired":"1","type":"file","name":"SSH使用默认端口22","harm":"高","level":"3","file":"/etc/ssh/sshd_config","Suggestions":"加固建议   在/etc/ssh/sshd_config 将Port 设置为6000到65535随意一个, 例如","repair":"Port 60151","rule":[{"re":"Port\\s*(\\d+)","check":{"type":"number","max":65535,"min":22}}],"repair_loophole":[{"re":"\n?#?Port\\s*(\\d+)","check":"\nPort 65531"}]}}

    def __init__(self):
        if not os.path.exists(self.__ClIENT_IP):
            public.WriteFile(self.__ClIENT_IP,json.dumps([]))
        self.__mail=send_mail.send_mail()
        self.__mail_config=self.__mail.get_settings()
        try:
            self.__ip_data = json.loads(public.ReadFile(self.__ClIENT_IP))
        except:
            self.__ip_data=[]


    def return_python(self):
        if os.path.exists('/www/server/panel/pyenv/bin/python'):return '/www/server/panel/pyenv/bin/python'
        if os.path.exists('/usr/bin/python'):return '/usr/bin/python'
        if os.path.exists('/usr/bin/python3'):return '/usr/bin/python3'
        return 'python'

    def return_bashrc(self):
        if os.path.exists('/root/.bashrc'):return '/root/.bashrc'
        if os.path.exists('/etc/bashrc'):return '/etc/bashrc'
        if os.path.exists('/etc/bash.bashrc'):return '/etc/bash.bashrc'
        fd = open('/root/.bashrc', mode="w", encoding="utf-8")
        fd.close()
        return '/root/.bashrc'


    def check_files(self):
        try:
            json.loads(public.ReadFile(self.__ClIENT_IP))
        except:
            public.WriteFile(self.__ClIENT_IP, json.dumps([]))

    def get_ssh_port(self):
        conf = public.readFile(self.__SSH_CONFIG)
        if not conf: conf = ''
        rep = "#*Port\s+([0-9]+)\s*\n"
        tmp1 = re.search(rep,conf)
        port = '22'
        if tmp1:
            port = tmp1.groups(0)[0]
        return port

    # 主判断函数
    def check_san_baseline(self, base_json):
        if base_json['type'] == 'file':
            if 'check_file' in base_json:
                if not os.path.exists(base_json['check_file']):
                    return False
            else:
                if os.path.exists(base_json['file']):
                    ret = public.ReadFile(base_json['file'])
                    for i in base_json['rule']:
                        valuse = re.findall(i['re'], ret)
                        print(valuse)
                        if i['check']['type'] == 'number':
                            if not valuse: return False
                            if not valuse[0]: return False
                            valuse = int(valuse[0])
                            if valuse > i['check']['min'] and valuse < i['check']['max']:
                                return True
                            else:
                                return False
                        elif i['check']['type'] == 'string':
                            if not valuse: return False
                            if not valuse[0]: return False
                            valuse = valuse[0]
                            print(valuse)
                            if valuse in i['check']['value']:
                                return True
                            else:
                                return False
                return True

    def san_ssh_security(self,get):
        data={"num":100,"result":[]}
        result = []
        ret = self.check_san_baseline(self.__REPAIR['1'])
        if not ret: result.append(self.__REPAIR['1'])
        ret = self.check_san_baseline(self.__REPAIR['2'])
        if not ret: result.append(self.__REPAIR['2'])
        ret = self.check_san_baseline(self.__REPAIR['3'])
        if not ret: result.append(self.__REPAIR['3'])
        ret = self.check_san_baseline(self.__REPAIR['4'])
        if not ret: result.append(self.__REPAIR['4'])
        ret = self.check_san_baseline(self.__REPAIR['5'])
        if not ret: result.append(self.__REPAIR['5'])
        ret = self.check_san_baseline(self.__REPAIR['6'])
        if not ret: result.append(self.__REPAIR['6'])
        data["result"]=result
        if len(result)>=1:
            data['num']=data['num']-(len(result)*10)
        return data

    ################## SSH 登陆报警设置 ####################################
    def send_mail_data(self,title,body,type='mail'):
        if type=='mail':
            if self.__mail_config['user_mail']['user_name']:
                if len(self.__mail_config['user_mail']['mail_list'])>=1:
                    for i in self.__mail_config['user_mail']['mail_list']:
                        self.__mail.qq_smtp_send(i, title, body)
        elif type=='dingding':
            if self.__mail_config['dingding']['dingding']:
                self.__mail.dingding_send(title+body)
        return True

    #检测非UID为0的账户
    def check_user(self):
        data=public.ExecShell('''cat /etc/passwd | awk -F: '($3 == 0) { print $1 }'|grep -v '^root$'  ''')
        data=data[0]
        if re.search("\w+",data):
            self.send_mail_data(public.GetLocalIp()+'服务器存在后门用户',public.GetLocalIp()+'服务器存在后门用户'+data+'检查/etc/passwd文件')
            return True
        else:
            return False

    #记录root 的登陆日志

    #返回登陆IP
    def return_ip(self,get):
        self.check_files()
        return public.returnMsg(True, self.__ip_data)

    #添加IP白名单
    def add_return_ip(self, get):
        self.check_files()
        if get.ip.strip() in self.__ip_data:
            return public.returnMsg(False, "已经存在")
        else:
            self.__ip_data.append(get.ip.strip())
            public.writeFile(self.__ClIENT_IP, json.dumps(self.__ip_data))
            return public.returnMsg(True, "添加成功")

    def del_return_ip(self, get):
        self.check_files()
        if get.ip.strip() in self.__ip_data:
            self.__ip_data.remove(get.ip.strip())
            public.writeFile(self.__ClIENT_IP, json.dumps(self.__ip_data))
            return public.returnMsg(True, "删除成功")
        else:
            return public.returnMsg(False, "不存在")

    #取登陆的前50个条记录
    def login_last(self):
        self.check_files()
        data=public.ExecShell('last -n 50')
        data=re.findall("(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)",data[0])
        if data>=1:
            data2=list(set(data))
            for i in data2:
                if not i in self.__ip_data:
                    self.__ip_data.append(i)
            public.writeFile(self.__ClIENT_IP, json.dumps(self.__ip_data))
        return self.__ip_data

    #获取ROOT当前登陆的IP
    def get_ip(self):
        data = public.ExecShell(''' who am i |awk ' {print $5 }' ''')
        data = re.findall("(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)",data[0])
        return data

    def get_logs(self, args):
        if 'p' in args: p = int(args.p)
        rows = 10
        if 'rows' in args: rows = int(args.rows)
        count = public.M('logs').where('type=?', ('SSH安全',)).count()
        data = public.get_page(count, int(args.p), int(rows))
        data['data'] = public.M('logs').where('type=?', ('SSH安全',)).limit(data['shift'] + ',' + data['row']).order(
            'addtime desc').select()
        return data

    def get_server_ip(self):
        if os.path.exists('/www/server/panel/data/iplist.txt'):
            data=public.ReadFile('/www/server/panel/data/iplist.txt')
            return data.strip()
        else:return '127.0.0.1'


    #登陆的情况下
    def login(self):
        self.check_files()
        if not self.__mail_config['user_mail']['user_name']:return False
        self.check_user()
        self.__ip_data = json.loads(public.ReadFile(self.__ClIENT_IP))
        ip=self.get_ip()
        if len(ip[0])==0:return False
        try:
            import time
            mDate = time.strftime('%Y-%m-%d %X', time.localtime())
            if ip[0] in self.__ip_data:
                if public.M('logs').where('type=? addtime', ('SSH安全',mDate,)).count():return False
                public.WriteLog('SSH安全', self.get_server_ip() + '服务器登陆登陆IP为' + ip[0] + '登陆用户为root')
                return False
            else:
                if public.M('logs').where('type=? addtime', ('SSH安全', mDate,)).count(): return False
                self.send_mail_data(self.get_server_ip()+'服务器异常登陆',public.GetLocalIp()+'服务器存在异常登陆登陆IP为'+ip[0]+'登陆用户为root')
                public.WriteLog('SSH安全',public.GetLocalIp()+'服务器存在异常登陆登陆IP为'+ip[0]+'登陆用户为root')
                return True
        except:
            pass

    #开启监控
    def start_jian(self,get):
        data=public.ReadFile(self.return_bashrc())
        if not re.search(self.return_python()+' /www/server/panel/class/ssh_security.py',data):
            public.WriteFile(self.return_bashrc(),data.strip()+'\n'+self.return_python()+ ' /www/server/panel/class/ssh_security.py login\n')
            return public.returnMsg(True, '开启成功')
        return public.returnMsg(False, '开启失败')

    #关闭监控
    def stop_jian(self,get):
        data = public.ReadFile(self.return_bashrc())
        if re.search(self.return_python()+' /www/server/panel/class/ssh_security.py', data):
            public.WriteFile(self.return_bashrc(),data.replace(self.return_python()+' /www/server/panel/class/ssh_security.py login',''))
            if os.path.exists('/etc/bashrc'):
                data22=public.ReadFile('/etc/bashrc')
                if re.search('python /www/server/panel/class/ssh_security.py', data):
                    public.WriteFile(self.return_bashrc(),data.replace('python /www/server/panel/class/ssh_security.py login',''))
            return public.returnMsg(True, '关闭成功')
        else:
            return public.returnMsg(True, '关闭成功')

    #监控状态
    def get_jian(self,get):
        data = public.ReadFile(self.return_bashrc())
        if re.search('/www/server/panel/class/ssh_security.py login', data):
            return public.returnMsg(True, '1')
        else:
            return public.returnMsg(False, '1')

    def set_password(self, get):
        '''
        开启密码登陆
        get: 无需传递参数
        '''
        ssh_password = '\n#?PasswordAuthentication\s\w+'
        file = public.readFile(self.__SSH_CONFIG)
        if len(re.findall(ssh_password, file)) == 0:
            file_result = file + '\nPasswordAuthentication yes'
        else:
            file_result = re.sub(ssh_password, '\nPasswordAuthentication yes', file)
        self.wirte(self.__SSH_CONFIG, file_result)
        self.restart_ssh()
        return public.returnMsg(True, '开启成功')

    def set_sshkey(self, get):
        '''
        设置ssh 的key
        参数 ssh=rsa&type=yes
        '''
        type_list = ['rsa', 'dsa']
        ssh_type = ['yes', 'no']
        ssh = get.ssh
        if not ssh in ssh_type: return public.returnMsg(False, 'ssh选项失败')
        type = get.type
        if not type in type_list: return public.returnMsg(False, '加密方式错误')
        file = ['/root/.ssh/id_rsa.pub', '/root/.ssh/id_rsa', '/root/.ssh/authorized_keys']
        for i in file:
            if os.path.exists(i):
                os.remove(i)
        os.system("ssh-keygen -t %s -P '' -f ~/.ssh/id_rsa |echo y" % type)
        if os.path.exists(file[0]):
            public.ExecShell('cat %s >%s && chmod 600 %s' % (file[0], file[-1], file[-1]))
            rec = '\n#?RSAAuthentication\s\w+'
            rec2 = '\n#?PubkeyAuthentication\s\w+'
            file = public.readFile(self.__SSH_CONFIG)
            if len(re.findall(rec, file)) == 0: file = file + '\nRSAAuthentication yes'
            if len(re.findall(rec2, file)) == 0: file = file + '\nPubkeyAuthentication yes'
            file_ssh = re.sub(rec, '\nRSAAuthentication yes', file)
            file_result = re.sub(rec2, '\nPubkeyAuthentication yes', file_ssh)
            if ssh == 'no':
                ssh_password = '\n#?PasswordAuthentication\s\w+'
                if len(re.findall(ssh_password, file_result)) == 0:
                    file_result = file_result + '\nPasswordAuthentication no'
                else:
                    file_result = re.sub(ssh_password, '\nPasswordAuthentication no', file_result)
            self.wirte(self.__SSH_CONFIG, file_result)
            self.restart_ssh()
            return public.returnMsg(True, '开启成功')
        else:
            return public.returnMsg(False, '开启失败')

        # 取SSH信息

    def GetSshInfo(self):
        port = public.get_ssh_port()

        pid_file = '/run/sshd.pid'
        if os.path.exists(pid_file):
            pid = int(public.readFile(pid_file))
            status = public.pid_exists(pid)
        else:
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
        return status


    def stop_key(self, get):
        '''
        关闭key
        无需参数传递
        '''
        is_ssh_status=self.GetSshInfo()
        if is_ssh_status:
            file = ['/root/.ssh/id_rsa.pub', '/root/.ssh/id_rsa', '/root/.ssh/authorized_keys']
            rec = '\n#?RSAAuthentication\s\w+'
            rec2 = '\n#?PubkeyAuthentication\s\w+'
            file = public.readFile(self.__SSH_CONFIG)
            file_ssh = re.sub(rec, '\nRSAAuthentication no', file)
            file_result = re.sub(rec2, '\nPubkeyAuthentication no', file_ssh)
            self.wirte(self.__SSH_CONFIG, file_result)
            self.set_password(get)
            self.restart_ssh()
            return public.returnMsg(True, '关闭成功')
        else:
            file = ['/root/.ssh/id_rsa.pub', '/root/.ssh/id_rsa', '/root/.ssh/authorized_keys']
            rec = '\n#?RSAAuthentication\s\w+'
            rec2 = '\n#?PubkeyAuthentication\s\w+'
            file = public.readFile(self.__SSH_CONFIG)
            file_ssh = re.sub(rec, '\nRSAAuthentication no', file)
            file_result = re.sub(rec2, '\nPubkeyAuthentication no', file_ssh)
            self.wirte(self.__SSH_CONFIG, file_result)
            #self.set_password(get)
            return public.returnMsg(True, '关闭成功')


    def get_config(self, get):
        '''
        获取配置文件
        无参数传递
        '''
        result = {}
        file = public.readFile(self.__SSH_CONFIG)
        rec = '\n#?RSAAuthentication\s\w+'
        pubkey = '\n#?PubkeyAuthentication\s\w+'
        ssh_password = '\nPasswordAuthentication\s\w+'
        #是否运行root登录
        root_is_login='\n#?PermitRootLogin\s\w+'

        ret = re.findall(ssh_password, file)
        if not ret:
            result['password'] = 'no'
        else:
            if ret[-1].split()[-1] == 'yes':
                result['password'] = 'yes'
            else:
                result['password'] = 'no'
        pubkey = re.findall(pubkey, file)
        if not pubkey:
            result['pubkey'] = 'no'
        else:
            if pubkey[-1].split()[-1] == 'no':
                result['pubkey'] = 'no'
            else:
                result['pubkey'] = 'yes'
        rsa_auth = re.findall(rec, file)
        if not rsa_auth:
            result['rsa_auth'] = 'no'
        else:
            if rsa_auth[-1].split()[-1] == 'no':
                result['rsa_auth'] = 'no'
            else:
                result['rsa_auth'] = 'yes'

        is_root=re.findall(root_is_login, file)
        if not is_root:
            result['root_is_login'] = 'no'
        else:
            if is_root[-1].split()[-1] == 'no':
                result['root_is_login'] = 'no'
            else:
                result['root_is_login'] = 'yes'
        return result


    def set_root(self, get):
        '''
        开启密码登陆
        get: 无需传递参数
        '''
        ssh_password = '\nPermitRootLogin\s\w+'
        file = public.readFile(self.__SSH_CONFIG)
        if len(re.findall(ssh_password, file)) == 0:
            file_result = file + '\nPermitRootLogin yes'
        else:
            file_result = re.sub(ssh_password, '\nPermitRootLogin yes', file)
        self.wirte(self.__SSH_CONFIG, file_result)
        self.restart_ssh()
        return public.returnMsg(True, '开启成功')

    def stop_root(self, get):
        '''
        开启密码登陆
        get: 无需传递参数
        '''
        ssh_password = '\nPermitRootLogin\s\w+'
        file = public.readFile(self.__SSH_CONFIG)
        if len(re.findall(ssh_password, file)) == 0:
            file_result = file + '\nPermitRootLogin no'
        else:
            file_result = re.sub(ssh_password, '\nPermitRootLogin no', file)
        self.wirte(self.__SSH_CONFIG, file_result)
        self.restart_ssh()
        return public.returnMsg(True, '关闭成功')

    def stop_password(self, get):
        '''
        关闭密码访问
        无参数传递
        '''
        file = public.readFile(self.__SSH_CONFIG)
        ssh_password = '\n#?PasswordAuthentication\s\w+'
        file_result = re.sub(ssh_password, '\nPasswordAuthentication no', file)
        self.wirte(self.__SSH_CONFIG, file_result)
        self.restart_ssh()
        return public.returnMsg(True, '关闭成功')

    def get_key(self, get):
        '''
        获取key 无参数传递
        '''
        file = '/root/.ssh/id_rsa'
        if not os.path.exists(file): return public.returnMsg(True, '')
        ret = public.readFile(file)
        return public.returnMsg(True, ret)

    def wirte(self, file, ret):
        result = public.writeFile(file, ret)
        return result

    def restart_ssh(self):
        '''
        重启ssh 无参数传递
        '''
        version = public.readFile('/etc/redhat-release')
        act = 'restart'
        if not os.path.exists('/etc/redhat-release'):
            public.ExecShell('service ssh ' + act)
        elif version.find(' 7.') != -1 or version.find(' 8.') != -1:
            public.ExecShell("systemctl " + act + " sshd.service")
        else:
            public.ExecShell("/etc/init.d/sshd " + act)
    #检查是否设置了钉钉
    def check_dingding(self, get):
        '''
        检查是否设置了钉钉
        '''
        #检查文件是否存在
        if not os.path.exists('/www/server/panel/data/dingding.json'):return False
        dingding_config=public.ReadFile('/www/server/panel/data/dingding.json')
        if not dingding_config:return False
        #解析json
        try:
            dingding=json.loads(dingding_config)
            if dingding['dingding_url']:
                return True
        except:
            return False

    #开启SSH双因子认证
    def start_auth_method(self, get):
        '''
        开启SSH双因子认证
        '''
        #检查是否设置了钉钉
        #if not self.check_dingding(get): return public.returnMsg(False, '钉钉未设置')
        import ssh_authentication
        ssh_class=ssh_authentication.ssh_authentication()
        return  ssh_class.start_ssh_authentication_two_factors()

    #关闭SSH双因子认证
    def stop_auth_method(self, get):
        '''
        关闭SSH双因子认证
        '''
        #检查是否设置了钉钉
        #if not self.check_dingding(get): return public.returnMsg(False, '钉钉未设置')
        import ssh_authentication
        ssh_class=ssh_authentication.ssh_authentication()
        return ssh_class.close_ssh_authentication_two_factors()

    #获取SSH双因子认证状态
    def get_auth_method(self, get):
        '''
        获取SSH双因子认证状态
        '''
        #检查是否设置了钉钉
        #if not self.check_dingding(get): return public.returnMsg(False, '钉钉未设置')
        import ssh_authentication
        ssh_class=ssh_authentication.ssh_authentication()
        return ssh_class.check_ssh_authentication_two_factors()

    #判断so文件是否存在
    def check_so_file(self, get):
        '''
        判断so文件是否存在
        '''
        import ssh_authentication
        ssh_class=ssh_authentication.ssh_authentication()
        return ssh_class.is_check_so()

    #下载so文件
    def get_so_file(self, get):
        '''
        下载so文件
        '''
        import ssh_authentication
        ssh_class=ssh_authentication.ssh_authentication()
        return ssh_class.download_so()

    #获取pin
    def get_pin(self, get):
        '''
        获取pin
        '''
        import ssh_authentication
        ssh_class=ssh_authentication.ssh_authentication()
        return public.returnMsg(True, ssh_class.get_pin())

if __name__ == '__main__':
    import sys
    type = sys.argv[1]
    if type=='login':
        try:
            aa = ssh_security()
            aa.login()
        except:pass
    else:
        pass