# coding: utf-8
# +-------------------------------------------------------------------
# | version :1.0
# +-------------------------------------------------------------------
# | Author: 梁凯强 <1249648969@qq.com>
# +-------------------------------------------------------------------
# | SSH 双因子认证
# +--------------------------------------------------------------------
import public,re,os
import platform,time

class ssh_authentication:
    __SSH_CONFIG='/etc/ssh/sshd_config'
    __PAM_CONFIG='/etc/pam.d/sshd'
    __python_pam='/usr/pam_python_so'
    __config_pl='/www/server/panel/data/pam_btssh_authentication.pl'


    def __init__(self):
        '''检查pam_python目录是否存在'''
        if not os.path.exists(self.__python_pam):
            public.ExecShell("mkdir -p " + self.__python_pam)
            public.ExecShell("chmod 600 " + self.__python_pam)
        if not os.path.exists(self.__config_pl):
            public.ExecShell("echo  '%s' >>%s"%(public.GetRandomString(32),self.__config_pl))
            public.ExecShell("chmod 600 " + self.__config_pl)  

    def wirte(self, file, ret):
        result = public.writeFile(file, ret)
        return result
    
    #重启SSH
    def restart_ssh(self):
        act = 'restart'
        if os.path.exists('/etc/redhat-release'):
            version = public.readFile('/etc/redhat-release')
            if isinstance(version, str):
                if version.find(' 7.') != -1 or version.find(' 8.') != -1:
                    public.ExecShell("systemctl " + act + " sshd.service")
                else:
                    public.ExecShell("/etc/init.d/sshd " + act)
            else:
                public.ExecShell("/etc/init.d/sshd " + act)
        else:
            public.ExecShell("/etc/init.d/sshd " + act)
    
    #查找PAM目录
    def get_pam_dir(self):
        #Centos 系列
        if os.path.exists('/etc/redhat-release'):
            version = public.readFile('/etc/redhat-release')
            if isinstance(version, str):
                if version.find(' 7.') != -1:
                    return 'auth  requisite  %s/pam_btssh_authentication.so'%(self.__python_pam)
                elif version.find(' 8.') != -1:
                    return 'auth  requisite  %s/pam_btssh_authentication.so'%(self.__python_pam)
                else:
                    return False
        #Ubuntu
        elif os.path.exists('/etc/lsb-release'):
            version = public.readFile('/etc/lsb-release')
            if isinstance(version, str):
                if version.find('16.') != -1:
                    return 'auth  requisite  %s/pam_btssh_authentication.so'%(self.__python_pam)
                elif version.find('20.') != -1:
                    return 'auth  requisite  %s/pam_btssh_authentication.so'%(self.__python_pam)
                elif version.find('18.') != -1:
                    return 'auth  requisite  %s/pam_btssh_authentication.so'%(self.__python_pam)
                else:
                    return False
        #debian
        elif os.path.exists('/etc/debian_version'):
            version = public.readFile('/etc/debian_version')
            if isinstance(version, str):
                if version.find('9.') != -1:
                    return 'auth  requisite  %s/pam_btssh_authentication.so'%(self.__python_pam)
                elif version.find('10.') != -1:
                    return 'auth  requisite  %s/pam_btssh_authentication.so'%(self.__python_pam)
                else:
                    return False
        return False
        
    #判断PAMSO文件是否存在
    def isPamSoExists(self):
        check2=self.get_pam_dir()
        if not check2: return False
        check=check2.split()
        if len(check)<3: return False
        if os.path.exists(check[2]):
            #判断文件大小
            if os.path.getsize(check[2])<10240:
                self.install_pam_python(check)
                return self.isPamSoExists()
            return check2
        else:
            self.install_pam_python(check)
            return self.isPamSoExists()

    #安装pam_python
    def install_pam_python(self,check):
        so_path=check[2]
        so_name=check[2].split('/')[-1]
        public.ExecShell('/usr/local/curl/bin/curl -o %s http://download.bt.cn/btwaf_rule/pam_python_so/%s'%(so_path,so_name))
        public.ExecShell("chmod 600 " + so_path)
        return True
    
    #开启双因子认证
    def start_ssh_authentication(self):
        check=self.isPamSoExists()
        if not check:return False
        if os.path.exists(self.__PAM_CONFIG):
            auth_data=public.readFile(self.__PAM_CONFIG)
            if isinstance(auth_data, str):
                if auth_data.find("\n"+check) != -1:
                    return True
                else:
                    auth_data=auth_data+"\n"+check
                    public.writeFile(self.__PAM_CONFIG,auth_data)
                    return True
        return False
                
    #关闭双因子认证
    def stop_ssh_authentication(self):
        check=self.isPamSoExists()
        if not check:return False
        if os.path.exists(self.__PAM_CONFIG):
            auth_data=public.readFile(self.__PAM_CONFIG)
            if isinstance(auth_data, str):
                if auth_data.find("\n"+check) != -1:
                    auth_data=auth_data.replace("\n"+check,'')
                    public.writeFile(self.__PAM_CONFIG,auth_data)
                    return True
                else:
                    return False
        return False

    #检查是否开启双因子认证
    def check_ssh_authentication(self):
        check=self.isPamSoExists()
        if not check:return False
        if os.path.exists(self.__PAM_CONFIG):
            auth_data=public.readFile(self.__PAM_CONFIG)
            if isinstance(auth_data, str):
                if auth_data.find("\n"+check) != -1:
                    return True
                else:
                    return False
        return False


    #设置SSH应答模式
    def set_ssh_login_user(self):
        ssh_password = '\nChallengeResponseAuthentication\s\w+'
        file = public.readFile(self.__SSH_CONFIG)
        if isinstance(file, str):
            if len(re.findall(ssh_password, file)) == 0:
                file_result = file + '\nChallengeResponseAuthentication yes'
            else:
                file_result = re.sub(ssh_password, '\nChallengeResponseAuthentication yes', file)
            self.wirte(self.__SSH_CONFIG, file_result)
            self.restart_ssh()
        return public.returnMsg(True, '开启成功')

    #关闭SSH应答模式
    def close_ssh_login_user(self):
        file = public.readFile(self.__SSH_CONFIG)
        ssh_password = '\nChallengeResponseAuthentication\s\w+'
        if isinstance(file, str):
            file_result = re.sub(ssh_password, '\nChallengeResponseAuthentication no', file)
            self.wirte(self.__SSH_CONFIG, file_result)
            self.restart_ssh()
        return public.returnMsg(True, '关闭成功')

    #查看SSH应答模式
    def check_ssh_login_user(self):
        file = public.readFile(self.__SSH_CONFIG)
        ssh_password = '\nChallengeResponseAuthentication\s\w+'
        if isinstance(file, str):
            ret = re.findall(ssh_password, file)
            if not ret:
                return False
            else:
                if ret[-1].split()[-1] == 'yes':
                    return True
                else:
                    return False
        return False

    #关闭密码访问
    def stop_password(self):
        '''
        关闭密码访问
        无参数传递
        '''
        file = public.readFile(self.__SSH_CONFIG)
        if isinstance(file, str):
            if file.find('PasswordAuthentication') != -1:
                file_result = file.replace('\nPasswordAuthentication yes', '\nPasswordAuthentication no')
                self.wirte(self.__SSH_CONFIG, file_result)
                self.restart_ssh()
                return public.returnMsg(True, '关闭密码认证成功')
            else:   
                return public.returnMsg(False, '没有密码认证')
        return public.returnMsg(False, '没有密码认证')

    #开启密码登录
    def start_password(self):
        '''
        开启密码登陆
        get: 无需传递参数
        '''
        file = public.readFile(self.__SSH_CONFIG)
        if isinstance(file, str):
            if file.find('PasswordAuthentication') != -1:
                file_result = file.replace('\nPasswordAuthentication no', '\nPasswordAuthentication yes')
                self.wirte(self.__SSH_CONFIG, file_result)
                self.restart_ssh()
                return public.returnMsg(True, '开启密码认证成功')
            else:
                file_result = file + '\nPasswordAuthentication yes'
                self.wirte(self.__SSH_CONFIG, file_result)
                self.restart_ssh()
                return public.returnMsg(True, '开启密码认证成功')
        return public.returnMsg(False, '没有密码认证')

    #查看密码登录状态
    def check_password(self):
        '''
        查看密码登录状态
        无参数传递
        '''
        file = public.readFile(self.__SSH_CONFIG)
        ssh_password = '\nPasswordAuthentication\s\w+'
        if isinstance(file, str):
            ret = re.findall(ssh_password, file)
            if not ret:
                return False
            else:
                if ret[-1].split()[-1] == 'yes':
                    return True
                else:
                    return False
        return False


    #开启SSH 双因子认证
    def start_ssh_authentication_two_factors(self):
        if not self.get_pam_dir():return public.returnMsg(False,'不支持该系统')
        check=self.isPamSoExists()
        if not check:return 'False'
        if not self.check_ssh_login_user():
            self.set_ssh_login_user()
        if not self.check_ssh_authentication():
            self.start_ssh_authentication()
        #如果开启的话，就关闭密码认证
        # if self.check_password():
        #     self.stop_password()
        #检查是否开启双因子认证
        if  self.check_ssh_authentication() and self.check_ssh_login_user():
            return public.returnMsg(True,'开启成功')
        return public.returnMsg(True,'开启失败')

    
    #关闭SSH 双因子认证
    def close_ssh_authentication_two_factors(self):
        if not self.get_pam_dir():return public.returnMsg(False,'不支持该系统')
        check=self.isPamSoExists()
        if not check:return False
        if self.check_ssh_authentication():
            self.stop_ssh_authentication()
        #检查是否关闭双因子认证
        #如果是关闭的SSH，那么就开启
        # if not self.check_password():
        #     self.start_password()
        if not self.check_ssh_authentication():
            return public.returnMsg(True,'已关闭')
        if self.stop_ssh_authentication():
            return public.returnMsg(True,'已关闭')
        

    #检查是否开启双因子认证
    def check_ssh_authentication_two_factors(self):
        if not self.get_pam_dir():return public.returnMsg(False,'不支持该系统')
        check=self.isPamSoExists()
        if not check:return False
        if not self.check_ssh_login_user():
            return public.returnMsg(False,'未开启')
        if not self.check_ssh_authentication():
            return public.returnMsg(False,'未开启')
        return public.returnMsg(True,'已开启')
    
    def is_check_so(self):
        '''判断SO文件是否存在'''
        if not self.get_pam_dir():return public.returnMsg(False,'不支持该系统')
        config_data=self.get_pam_dir()
        if not config_data:return False
        config_data2=config_data.split()
        ret={}
        ret['so_path']=config_data2[2].split('/')[-1]
        if os.path.exists(config_data2[2]):
            ret['so_status']=True
        else:
            ret['so_status']=False
        return public.returnMsg(True,ret)

    def download_so(self):
        '''下载so文件'''
        if not self.get_pam_dir():return public.returnMsg(False,'不支持该系统')
        config_data=self.get_pam_dir()
        if not config_data:return False
        config_data=config_data.split()
        self.install_pam_python(config_data)
        #判断下载的文件大小
        if os.path.exists(config_data[2]) :
            if os.path.getsize(config_data[2])>10240:
                return public.returnMsg(True,"下载文件成功")
        return public.returnMsg(False,"下载失败")

        #获取Linux系统的主机名
    def get_pin(self):
        import platform,time
        data=platform.uname()
        tme_data=time.strftime('%Y-%m-%d%H:%M',time.localtime(time.time()))
        #获取秒
        tis_data=time.strftime('%S',time.localtime(time.time()))
        ip_list=public.ReadFile('/www/server/panel/data/pam_btssh_authentication.pl')
        ret={}
        if isinstance(ip_list,str):
            info=data[0]+data[1]+data[2]+tme_data+ip_list
            md5_info=public.Md5(info)
            ret['pin']=md5_info[:6]
            ret['time']=60-int(tis_data)
            return ret
        else:
            ret['pin']='error'
            ret['time']=60
            return ret