# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: lkqiang<lkq@bt.cn>
# +-------------------------------------------------------------------
# +--------------------------------------------------------------------
# |   密码管理
# +--------------------------------------------------------------------
import sys, os
if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
os.chdir('/www/server/panel')
if not 'class/' in sys.path:
    sys.path.insert(0,'class/')
import re
import public,data,database,config

class password:
    def __init__(self):
        self.__data=data.data()
        self.__database=database.database()
        self.__config=config.config()

    #设置面板密码
    def set_panel_password(self,get):
        get.password1=get.password
        get.password2 = get.password
        data=self.__config.setPassword(get)
        return data

    #查看面板用户名
    def get_panel_username(self,get):
        data=public.M('users').where("id=?", (1,)).getField('username')
        if  data:
            return data
        else:
            return False

    # 设置root 密码
    def set_root_password(self,get):
        public.ExecShell("echo"+get.user+":"+get.password+"|chpasswd")
        return True

    #查看mysql_root密码
    def get_mysql_root(self,get):
        password = public.M('config').where("id=?",(1,)).getField('mysql_root')
        return public.returnMsg(True, password)

    #设置mysql_root 密码
    def set_mysql_password(self,get):
        if 'password' in  get:
            resutl=self.__database.SetupPassword(get)
            return resutl
        else:
            return public.returnMsg(False, 'password参数不能为空')


    # MySQL 的其他账户设置
    #获取其他mysql的信息
    def get_databses(self,get):
        data=public.M('databases').select()
        return public.returnMsg(True, data)

    # 修改MySQL 其他账户的密码
    def rem_mysql_pass(self,get):
        '''
        参数 三个
        id 数据库ID， name:数据库名称, password:数据库密码
        '''
        data=self.__database.ResDatabasePassword(get)
        return data

    # 修改其他Mysql 账户的权限
    def set_mysql_access(self,get):
        '''
        参数 三个
        name:数据库名称, dataAccess: 权限  access 权限
        '''
        data=self.__database.SetDatabaseAccess(get)
        return data


    ####################  SSH 的基础设置####################

    # 开启密码登陆
    def SetPassword(self, get):
        ssh_password = '\n#?PasswordAuthentication\s\w+'
        file = public.readFile('/etc/ssh/sshd_config')
        if len(re.findall(ssh_password, file)) == 0:
            file_result = file + '\nPasswordAuthentication yes'
        else:
            file_result = re.sub(ssh_password, '\nPasswordAuthentication yes', file)
        self.Wirte('/etc/ssh/sshd_config', file_result)
        self.RestartSsh()
        return public.returnMsg(True, '开启成功')

    # 设置ssh_key
    def SetSshKey(self, get):
        ''''''
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
        public.ExecShell("ssh-keygen -t %s -P '' -f ~/.ssh/id_rsa |echo y" % type)
        if os.path.exists(file[0]):
            public.ExecShell('cat %s >%s && chmod 600 %s' % (file[0], file[-1], file[-1]))
            rec = '\n#?RSAAuthentication\s\w+'
            rec2 = '\n#?PubkeyAuthentication\s\w+'
            file = public.readFile('/etc/ssh/sshd_config')
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
            self.Wirte('/etc/ssh/sshd_config', file_result)
            self.RestartSsh()
            return public.returnMsg(True, '开启成功')
        else:
            return public.returnMsg(False, '开启失败')


    # 关闭sshkey
    def StopKey(self, get):
        file = ['/root/.ssh/id_rsa.pub', '/root/.ssh/id_rsa', '/root/.ssh/authorized_keys']
        rec = '\n#?RSAAuthentication\s\w+'
        rec2 = '\n#?PubkeyAuthentication\s\w+'
        file = public.readFile('/etc/ssh/sshd_config')
        file_ssh = re.sub(rec, '\n#RSAAuthentication no', file)
        file_result = re.sub(rec2, '\n#PubkeyAuthentication no', file_ssh)
        self.Wirte('/etc/ssh/sshd_config', file_result)
        self.SetPassword(get)
        self.RestartSsh()
        return public.returnMsg(True, '关闭成功')
        # 读取配置文件 获取当前状态

    def GetConfig(self, get):
        result = {}
        file = public.readFile('/etc/ssh/sshd_config')
        rec = '\n#?RSAAuthentication\s\w+'
        pubkey = '\n#?PubkeyAuthentication\s\w+'
        ssh_password = '\nPasswordAuthentication\s\w+'
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
        return result

    # 关闭密码方式
    def StopPassword(self, get):
        file = public.readFile('/etc/ssh/sshd_config')
        ssh_password = '\n#?PasswordAuthentication\s\w+'
        file_result = re.sub(ssh_password, '\nPasswordAuthentication no', file)
        self.Wirte('/etc/ssh/sshd_config', file_result)
        self.RestartSsh()
        return public.returnMsg(True, '关闭成功')

    #显示key文件
    def GetKey(self, get):
        file = '/root/.ssh/id_rsa'
        if not os.path.exists(file): return public.returnMsg(True, '')
        ret = public.readFile(file)
        return public.returnMsg(True, ret)

    # 下载
    def Download(self, get):
        if os.path.exists('/root/.ssh/id_rsa'):
            ret = '/download?filename=/root/.ssh/id_rsa'
            return public.returnMsg(True, ret)

    # 写入配置文件
    def Wirte(self, file, ret):
        result = public.writeFile(file, ret)
        return result

    def RestartSsh(self):
        version = public.readFile('/etc/redhat-release')
        act = 'restart'
        if not os.path.exists('/etc/redhat-release'):
            public.ExecShell('service ssh ' + act)
        elif version.find(' 7.') != -1:
            public.ExecShell("systemctl " + act + " sshd.service")
        else:
            public.ExecShell("/etc/init.d/sshd " + act)
