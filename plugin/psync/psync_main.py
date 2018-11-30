#!/usr/bin/python
# coding: utf-8
# -----------------------------
# 宝塔Linux面板备份/同步工具
# -----------------------------
# Author:1249648969@qq.com
import sys, os

reload(sys)
sys.setdefaultencoding('utf-8')
os.chdir('/www/server/panel')
sys.path.append("class/")
import public, db, time, json, system, re

class mobj: port = ps = ''


class psync_main:
    __setupPath = '/www/server/panel/plugin/psync'
    __backupPath = '/www/server/panel/plugin/psync/backup'
    __configuration_file = '/etc/rsyncd.conf'
    __torsync_passwd = '/www/server/panel/plugin/psync/liang.db'
    __rsync_passwd = '/www/server/panel/plugin/psync/password'
    __rsync_pid = '/var/run/rsyncd.pid'
    __wwwroot = '/www/wwwroot'
    __to_rsync_pass = '/www/server/panel/plugin/psync/to_rsync_passwd'
    __toToken = None
    timeoutCount = 0
    __port = 22
    pre = 0
    oldTime = 0
    logPath = '/www/server/panel/plugin/psync/pre.json'

    def __check_dst_port(self, ip, port, timeout=3):
        import socket
        ok = True
        try:
            s = socket.socket()
            s.settimeout(timeout)
            s.connect((ip, port))
            s.close()
        except:
            ok = False
        return ok
    # 设置备份信息
    def SetConfig(self, get):
        data = {}
        data['status'] = False
        data['log'] = {}
        data['site'] = []
        data['database'] = []
        data['ftp'] = []

        data['log']['status'] = True
        data['log']['to'] = True
        if get.log == '1':
            data['log']['status'] = True
            data['log']['to'] = False

        msite = json.loads(get.site)
        if len(msite) > 0:
            sites = public.M('sites').field('id,name,path,status,ps,addtime').select()
            for site in sites:
                if not site['name'] in msite: continue
                site['domains'] = public.M('domain').where('pid=?', (site['id'],)).field('name,port,addtime').select()
                site['binding'] = public.M('binding').where('pid=?', (site['id'],)).field('domain,path,addtime').select()
                site['to'] = False
                data['site'].append(site)

        mdata = json.loads(get.database)
        if len(mdata) > 0:
            databases = public.M('databases').field('name,username,password,accept,ps,addtime').select()
            for database in databases:
                if not database['name'] in mdata: continue
                database['to'] = False
                data['database'].append(database)

        mftp = json.loads(get.ftp)
        if len(mftp) > 0:
            ftps = public.M('ftps').field('pid,name,password,path,status,ps,addtime').select()
            for ftp in ftps:
                if not ftp['name'] in mftp: continue
                ftp['to'] = False
                data['ftp'].append(ftp)
        public.writeFile(self.__setupPath + '/relist.json', json.dumps(data))

        toToken = {}
        toToken['url'] = get.tourl
        toToken['token'] = get.totoken
        public.writeFile(self.__setupPath + '/toToken.json', json.dumps(toToken))
        os.system("cd " + self.__setupPath + ' && python psync_main.py action &')
        isTask = '/tmp/panelTask.pl'
        public.writeFile(isTask, 'True')
        os.system("cd " + self.__setupPath + ' && python psync_main.py start &')
        public.WriteLog('一键迁移', '添加数据迁移任务成功!')
        return data


    def start(self):
        self.WriteLogs('启动sshd')
        relist = self.__setupPath + '/toToken.json'
        toToken = json.loads(public.readFile(relist))
        result = public.httpGet(
            toToken['url'] + '/pluginApi?token=' + toToken['token'] + '&action=a&name=psync&s=start_sshd')
        return True
        # 启动sshd 服务

    def start_sshd(self, get):
            self.WriteLogs('启动ssh')
            os.system('pkill -9 rsync')
            os.system('rm -rf /var/run/rsyncd.pid && rm -rf /var/run/rsyncd.lock ')
            os.system('/etc/init.d/rsynd stop')

            if os.path.exists(self.__setupPath+ '/port.json'):
                version = public.readFile('/etc/redhat-release')
                act = 'restart'
                if not os.path.exists('/etc/redhat-release'):
                    public.ExecShell('service ssh ' + act)
                elif version.find(' 7.') != -1:
                    public.ExecShell("systemctl " + act + " sshd.service")
                else:
                    public.ExecShell("/etc/init.d/sshd " + act)
                self.WriteLogs('开始ssh')
                os.system('rm -rf %s'%self.__setupPath+ '/port.json')
                try:
                    if int(public.ExecShell('netstat -nltp |grep sshd | awk \'{print $4}\' | grep 22  |wc -l')[0].split()[0]) ==0:
                        version = public.readFile('/etc/redhat-release')
                        act = 'restart'
                        if not os.path.exists('/etc/redhat-release'):
                            public.ExecShell('service ssh ' + act)
                        elif version.find(' 7.') != -1:
                            public.ExecShell("systemctl " + act + " sshd.service")
                        else:
                            public.ExecShell("/etc/init.d/sshd " + act)
                        self.WriteLogs('开始ssh')
                        os.system('rm -rf %s' % self.__setupPath + '/port.json')
                        return True
                    else:
                        version = public.readFile('/etc/redhat-release')
                        act = 'restart'
                        if not os.path.exists('/etc/redhat-release'):
                            public.ExecShell('service ssh ' + act)
                        elif version.find(' 7.') != -1:
                            public.ExecShell("systemctl " + act + " sshd.service")
                        else:
                            public.ExecShell("/etc/init.d/sshd " + act)
                        self.WriteLogs('开始ssh')
                        os.system('rm -rf %s' % self.__setupPath + '/port.json')
                except:
                    version = public.readFile('/etc/redhat-release')
                    act = 'restart'
                    if not os.path.exists('/etc/redhat-release'):
                        public.ExecShell('service ssh ' + act)
                    elif version.find(' 7.') != -1:
                        public.ExecShell("systemctl " + act + " sshd.service")
                    else:
                        public.ExecShell("/etc/init.d/sshd " + act)
                    self.WriteLogs('开始ssh')
                    os.system('rm -rf %s' % self.__setupPath + '/port.json')
                    return True
            else:
                version = public.readFile('/etc/redhat-release')
                act = 'restart'
                if not os.path.exists('/etc/redhat-release'):
                    public.ExecShell('service ssh ' + act)
                elif version.find(' 7.') != -1:
                    public.ExecShell("systemctl " + act + " sshd.service")
                else:
                    public.ExecShell("/etc/init.d/sshd " + act)
                self.WriteLogs('开始ssh')
                os.system('rm -rf %s' % self.__setupPath + '/port.json')

    # 设置远程备份信息
    def SetToConfig(self, get):
        import web
        data = {}
        toToken = self.GetToToken()
        data['token'] = toToken['token']
        data['site'] = get.site
        data['database'] = get.database
        data['ftp'] = get.ftp
        data['log'] = '0'
        get.settoken = 'True'
        data['totoken'] = self.GetToken(get)['token']
        data['tourl'] = web.ctx.protocol + '://' + web.ctx.host
        result = json.loads(public.httpPost(toToken['url'] + '/pluginApi?action=a&name=psync&s=SetConfig', data))
        relist = self.__setupPath + '/relist.json'
        public.writeFile(relist, json.dumps(result))
        import firewalls
        fs = firewalls.firewalls()
        get = mobj()
        get.port = '443'
        get.ps = 'HTTPS'
        fs.AddAcceptPort(get)
        return result

    # 设置备份信息
    def SetConfig_token(self, get):
        self.WriteLogs('设置备份信息')
        data = {}
        data['status'] = False
        data['log'] = {}
        data['site'] = []
        data['database'] = []
        data['ftp'] = []

        data['log']['status'] = True
        data['log']['to'] = True
        if get.log == '1':
            data['log']['status'] = True
            data['log']['to'] = False
        toToken = {}
        toToken['url'] = get.tourl
        toToken['token'] = get.totoken
        self.WriteLogs('写入配置文件')
        public.writeFile(self.__rsync_passwd, get.rsync_pass)
        public.writeFile(self.__setupPath + '/toToken.json', json.dumps(toToken))
        return data

    # 设置远程备份信息 加入随机密码
    def set_token(self, get):
        import web
        data = {}
        toToken = self.GetToToken()
        data['token'] = toToken['token']
        data['site'] = 'cc.com'
        data['database'] = 'ccc'
        data['ftp'] = 'cc.com'
        data['log'] = '0'
        get.settoken = 'True'
        data['totoken'] = self.GetToken(get)['token']
        data['tourl'] = web.ctx.protocol + '://' + web.ctx.host
        import random
        import string
        ran_str = ''.join(random.sample(string.ascii_letters + string.digits, 32))
        rsync_db = public.readFile(self.__torsync_passwd).split(':')
        rsync_db.pop(1)
        rsync_db.append(ran_str)
        db_file = open(self.__torsync_passwd, 'w')
        db_file.write((rsync_db[0] + ':' + rsync_db[1]))
        self.WriteLogs('密码为%s' % ran_str)
        data['rsync_pass'] = ran_str
        result = json.loads(public.httpPost(toToken['url'] + '/pluginApi?action=a&name=psync&s=SetConfig_token', data))
        relist = self.__setupPath + '/relist.json'
        return result

    # 253
    def get_to_rsync_port(self, get):
        os.system('wget -O /www/server/panel/plugin/psync/rsyncd.conf '+public.get_url()+'/install/plugin/psync/rsyncd.conf -T 5')
        relist = self.__setupPath + '/toToken.json'
        toToken = json.loads(public.readFile(relist))
        if not os.path.exists(relist): return public.returnMsg(False, '获取IP失败!')
        relist=self.__setupPath+'/rsyncd.conf'
        if os.path.exists(relist):
            os.system('unalias cp')
            os.system('cp -a -r /www/server/panel/plugin/psync/rsyncd.conf  /etc/rsyncd.conf')
            self.WriteLogs('设置完毕')
        else:
            os.system('wget -O /www/server/panel/plugin/psync/rsyncd.conf '+public.get_url()+'/install/plugin/psync/rsyncd.conf -T 5')
            os.system('unalias cp')
            os.system('cp -a -r /www/server/panel/plugin/psync/rsyncd.conf  /etc/rsyncd.conf')
            self.WriteLogs('设置完毕')
        self.WriteLogs('正在启动')
        os.system('pkill -9 ssh')
        os.system('pkill -9 sshd')
        os.system('/etc/init.d/ssh stop')
        public.ExecShell("/etc/init.d/sshd stop")
        public.ExecShell("systemctl stop sshd.service")
        try:
            if int(public.ExecShell('netstat -ntltp|grep sshd|grep 22 | awk -F : \'{print $4}\' |grep 22')[0].split()[0])==22:
                version = public.readFile('/etc/redhat-release')
                act = 'stop'
                if not os.path.exists('/etc/redhat-release'):
                    public.ExecShell('service ssh ' + act)
                elif version.find(' 7.') != -1:
                    public.ExecShell("systemctl " + act + " sshd.service")
                else:
                    public.ExecShell("/etc/init.d/ssh " + act)
                    public.ExecShell("/etc/init.d/sshd " + act)
                data={'port':'22'}
                public.writeFile(self.__setupPath + '/port.json', json.dumps(data))
                self.WriteLogs('22端口已经关闭')
        except:
            pass
        os.system('pkill -9 rsync')
        os.system('rm -rf /var/run/rsyncd.pid && rm -rf /var/run/rsyncd.lock ')
        os.system('/etc/init.d/rsynd start')
        self.WriteLogs('启动成功')
        if not self.__rsync_pid:
            os.system('pkill -9 rsync')
            os.system('rm -rf /var/run/rsyncd.pid && rm -rf /var/run/rsyncd.lock')
            os.system('/etc/init.d/rsynd start')
        ret = self.set_token(get=get)
        self.WriteLogs('%s' % ret)
        result = public.httpGet(
            toToken['url'] + '/pluginApi?token=' + toToken['token'] + '&action=a&name=psync&s=get_rsync_port')
        self.WriteLogs('检查完毕！！%s' % result)
        return result

    # 检查迁出服务器是否开启873端口这个需要在 199
    def get_rsync_port(self, get):
        # 迁移节点验证端口
        relist = self.__setupPath + '/toToken.json'
        if not os.path.exists(relist): return public.returnMsg(False, '获取IP失败!')
        self.WriteLogs('获取ip文件成功')
        ip_list = json.loads(public.readFile(relist))
        url = ip_list['url']
        self.WriteLogs('获取url%s' % url)
        ip=ip_list['url'].split(':')[1].replace('//','')
        self.WriteLogs('验证IP如下%s' % ip)
        check_port = self.__check_dst_port(ip, self.__port)
        return check_port

    def clear(self, get):
        if hasattr(get, 'clear'):
            os.system('/etc/init.d/rsynd stop')
            os.system('rm -rf /var/run/rsyncd.pid && rm -rf /var/run/rsyncd.lock ')
            os.system('/etc/init.d/rsynd start')
            toToken = self.GetToToken()
            data = {}
            data['token'] = toToken['token']
            result = public.httpPost(toToken['url'] + '/pluginApi?action=a&name=psync&s=SetConfig', data)
            return public.returnMsg(True, '关闭成功!')

    def clear_to_rsync(self, get):
        os.system('pkill -9 rsync')
        os.system('rm -rf /var/run/rsyncd.pid && rm -rf /var/run/rsyncd.lock ')
        os.system('/etc/init.d/rsynd start ')
        return True

    def get_rsync_chekc(self, get):
        if os.path.exists(self.__rsync_pid):
            return public.returnMsg(True, '正在运行中')
        else:
            return public.returnMsg(False, '未开启!')

    # 检查服务状态
    def get_rsync(self, get):
        if hasattr(get, 'close'):
            os.system('/etc/init.d/rsynd stop')
            os.system('rm -rf /var/run/rsyncd.pid && rm -rf /var/run/rsyncd.lock ')
            return public.returnMsg(True, '关闭成功!')
        if hasattr(get, 'setup'):
            os.system('/etc/init.d/rsynd stop')
            os.system('pkill -9 rsync')
            os.system('rm -rf /var/run/rsyncd.pid && rm -rf /var/run/rsyncd.lock ')
            os.system('/etc/init.d/rsynd start')
            return public.returnMsg(True, '启动成功!')
            # 取列表

    def GetList(self, get):
        listFile = self.__setupPath + '/relist.json'
        if not os.path.exists(listFile): return public.returnMsg(False, '当前没有迁移任务!')
        return json.loads(public.readFile(listFile))

    # 获取Token
    def GetToken(self, get):
        tempFile = 'data/tempToken.json'
        if hasattr(get, 'settoken'): self.SetToken(get)
        if not os.path.exists(tempFile): return public.returnMsg(False, '未开启')
        token = json.loads(public.readFile(tempFile))
        if time.time() > token['timeout']: return public.returnMsg(False, '已过期')
        return token

    # 生成Token
    def SetToken(self, get):
        tempFile = 'data/tempToken.json'
        tempToken = {}
        if hasattr(get, 'close'):
            os.system('rm -f ' + tempFile)
            return public.returnMsg(True, '关闭成功!')

        if hasattr(get, 'timeout'):
            tempToken = json.loads(public.readFile(tempFile))
        else:
            tempToken['token'] = public.GetRandomString(32)

        tempToken['timeout'] = time.time() + (86400 * 7)
        public.writeFile(tempFile, json.dumps(tempToken))
        return public.returnMsg(True, '开启成功!')

    # 检测远程服务器环境
    def CheckToServer(self, get):
        try:
            if get.token == 'undefined':
                toToken = self.GetToToken()
                get.url = toToken['url']
                get.token = toToken['token']
            data = {}
            data['token'] = get.token
            result = json.loads(public.httpPost(get.url + '/pluginApi?action=a&name=psync&s=CheckServer', data))
            toToken = {}
            toToken['url'] = get.url
            toToken['token'] = get.token
            public.writeFile(self.__setupPath + '/toToken.json', json.dumps(toToken))
            data['local'] = self.CheckServer(get)
            data['to'] = result
            return data
        except:
            return public.returnMsg(False, '连接服务器失败，请检查面板地址和密钥是否正确!')

    # 设置当前进度
    def SetSpeed(self, get):
        aTask = {}
        aTask['name'] = get.tname
        aTask['count'] = get.tcount
        aTask['done'] = get.tdone
        actionTask = self.__setupPath + '/actionTask.json'
        public.writeFile(actionTask, json.dumps(aTask))
        return True

    # 设置远程进度
    def SetSpeedTo(self, aTask):
        toToken = self.GetToToken()
        result = public.httpGet(
            toToken['url'] + '/pluginApi?token=' + toToken['token'] + '&action=a&name=psync&s=SetSpeed&tname=' + aTask['name'] + '&tcount=' + str(aTask['count']) + '&tdone=' + str(aTask['done']))
        return True

    # 检查是否重复
    def CheckRe(self, get):
        self.SetSpeed(get)
        result = public.M(get.type).where('name=?', (get.pname,)).count()
        if result > 0:
            type = 'database'
            if get.type == 'sites':
                type = 'site'
            elif get.type == 'ftps':
                type = 'ftp'
            return self.SetValue(type, get.pname, True)
        return result

    # 检查远程服务器是否重复
    def CheckReTo(self, type, name, aTask):
        toToken = self.GetToToken()
        result = public.httpGet(toToken['url'] + '/pluginApi?token=' + toToken['token'] + '&action=a&name=psync&s=CheckRe&type=' + type + '&pname=' + name + '&tname=' + aTask['name'] + '&tcount=' + str(aTask['count']) + '&tdone=' + str(aTask['done']))
        if result != '0':
            type = 'database'
            if type == 'sites':
                type = 'site'
            elif type == 'ftps':
                type = 'ftp'
            self.SetValue(type, name, True)
            return False
        return True

    # 写入状态
    def SetValue(self, type, name, status):
        relist = self.__setupPath + '/relist.json'
        relistData = json.loads(public.readFile(relist))
        for i in range(len(relistData[type])):
            if relistData[type][i]['name'] == name:
                relistData[type][i]['to'] = status
                break

        public.writeFile(relist, json.dumps(relistData))
        return True

    # 检测本机环境
    def CheckServer(self, get):
        import firewalls
        fs = firewalls.firewalls()
        get = mobj()
        get.port = '873'
        get.ps = 'rsync'

        fs.AddAcceptPort(get)
        serverInfo = {}
        # 获取Web服务器
        serverInfo['webserver'] = 'apache'
        if os.path.exists('/www/server/nginx/sbin/nginx'): serverInfo['webserver'] = 'nginx'

        # 获取PHP版本
        serverInfo['php'] = []
        phpversions = ['52', '53', '54', '55', '56', '70', '71']
        phpPath = '/www/server/php/'
        for pv in phpversions:
            if not os.path.exists(phpPath + pv + '/bin/php'): continue
            serverInfo['php'].append(pv)

        # 获取MySQL
        serverInfo['mysql'] = False
        if os.path.exists('/www/server/mysql/bin/mysql'): serverInfo['mysql'] = True

        # 获取FTP
        serverInfo['ftp'] = False
        if os.path.exists('/www/server/pure-ftpd/bin/pure-pw'): serverInfo['ftp'] = True

        # 获取网站列表
        serverInfo['siteList'] = public.M('sites').field('id,name,ps').select()
        # 获取FTP列表
        serverInfo['ftpList'] = public.M('ftps').field('id,name,ps').select()
        # 获取数据库列表
        serverInfo['dataList'] = public.M('databases').field('id,name,ps').select()

        # 获取磁盘空间
        import psutil
        try:
            diskInfo = psutil.disk_usage('/www')
        except:
            diskInfo = psutil.disk_usage('/')
        serverInfo['disk'] = diskInfo[2]
        return serverInfo

    # 获取目标面板Token
    def GetToToken(self, get=None):
        if not self.__toToken:
            toToken = self.__setupPath + '/toToken.json'
            if os.path.exists(toToken):
                self.__toToken = json.loads(public.readFile(toToken))
            else:
                return {'url': '', 'token': ''}
        return self.__toToken

    # 获取迁移状态
    def GetToStatus(self, get):
        actionTask = self.__setupPath + '/actionTask.json'
        if not os.path.exists(actionTask): return public.returnMsg(False, '当前没有迁移任务!')
        aTask = json.loads(public.readFile(actionTask))
        if aTask['name'] == '迁移完成':
            relist = self.__setupPath + '/relist.json'
            relistData = json.loads(public.readFile(relist))
            return relistData
        else:
            try:
                if os.path.exists(self.logPath): aTask['speed'] = json.loads(public.readFile(self.logPath))
            except:
                pass
            return aTask

    # 确认迁移状态
    def SetRe(self, get):
        actionTask = self.__setupPath + '/actionTask.json'
        relist = self.__setupPath + '/relist.json'
        os.system('rm -f ' + actionTask)
        os.system('rm -f ' + relist)
        return public.returnMsg(True, '已确认!')

 # 检测本机的东西
    def Check_info(self, get):
        serverInfo = {}
        serverInfo['siteList'] = public.M('sites').field('name').select()
        serverInfo['ftpList'] = public.M('ftps').field('name').select()
        serverInfo['dataList'] = public.M('databases').field('name').select()
        return serverInfo

    def check_type(self,filename,type):
        self.WriteLogs('filename%s'%filename)
        relist = self.__setupPath + '/toToken.json'
        data = json.loads(public.readFile(relist))
        aaaa=data['url'] + '/pluginApi?action=a&name=psync&s=Check_info&'+'token='+data['token']
        self.WriteLogs(aaaa)
        chekc_data =public.httpGet(aaaa)
        self.WriteLogs(chekc_data)
        chekc_data=json.loads(chekc_data)
        if chekc_data:
            self.WriteLogs('你好')
            self.WriteLogs('data%s'%chekc_data)
            if type=='site':
                if len(chekc_data['siteList'])>1:
                    for i in chekc_data['siteList']:
                        if filename==i['name']:
                            self.WriteLogs('存在')
                            return True
                        else:
                            return False
            elif type=='database':
                if len(chekc_data['dataList'])>1:
                    for i in chekc_data['dataList']:
                        if filename==i['name']:
                            self.WriteLogs('存在')
                            return True
                        else:
                            return False
            elif type=='ftp':
                if len(chekc_data['ftpList'])>1:
                    for i in chekc_data['ftpList']:
                        if filename==i['name']:
                            self.WriteLogs('存在')
                            return True
                        else:
                            return False
            else:
                return False
        else:
            return False
            self.WriteLogs('错误')

    # 开始迁移
    def StartBackup(self):

        self.WriteLogs('开始迁移')
        listFile = self.__setupPath + '/relist.json'
        actionTask = self.__setupPath + '/actionTask.json'
        taskList = self.GetList(None)

        self.WriteLogs('迁移站点')
        aTask = {}
        aTask['name'] = '站点'
        aTask['count'] = len(taskList['site']) + len(taskList['database']) + len(taskList['ftp']) + 1
        aTask['done'] = 0
        # 迁移网站
        for i in range(len(taskList['site'])):
            self.WriteLogs('正在迁移网站!%s' % aTask['name'])
            aTask['done'] += 1
            aTask['name'] = '站点[' + taskList['site'][i]['name'] + ']'
            public.writeFile(actionTask, json.dumps(aTask))
            msite = taskList['site'][i]
            if msite['to']: continue
            if not self.CheckReTo('sites', taskList['site'][i]['name'], aTask): continue
            public.WriteLog('一键迁移', '正在迁移' + aTask['name'] + '[' + taskList['site'][i]['name'] + ']')
            self.WriteLogs('正在迁移网站!%s' % aTask['name'])
            # 返回的是网站目录  /www/wwwroot/good.o2oxy.cn
            filename = self.BackupSite(msite['name'], msite['path'])
            print ('正在迁移网站[' + msite['name'] + '] ... ')
            ret=self.check_type(filename,'site')
            if ret:
                self.WriteLogs('已经存在')
                taskList['site'][i]['to'] = False
                continue
            else:
                print (self.rsyn_upload(filename, 'site', msite['name'], aTask))
                public.WriteLog('一键迁移', aTask['name'] + '[' + taskList['site'][i]['name'] + ']迁移完成')
                self.WriteLogs('正在迁移网站!完成%s' % aTask['name'])
                taskList['site'][i]['to'] = True
        public.writeFile(listFile, json.dumps(taskList))

        # 迁移数据库
        aTask['name'] = '数据库'

        for i in range(len(taskList['database'])):
            aTask['done'] += 1
            aTask['name'] = '数据库[' + taskList['database'][i]['name'] + ']'
            public.writeFile(actionTask, json.dumps(aTask))
            mdata = taskList['database'][i]
            if mdata['to']: continue
            if not self.CheckReTo('databases', taskList['database'][i]['name'], aTask): continue
            public.WriteLog('一键迁移', '正在迁移' + aTask['name'] + '[' + taskList['database'][i]['name'] + ']')

            self.WriteLogs('正在迁移数据库!%s' % aTask['name'])
            # 这个filename 返回的是一个路径
            if mdata['name'] == 'test': continue
            filename = self.BackupDatabase(mdata['name'], mdata['username'], mdata['password'])
            print ('正在迁移数据库[' + mdata['name'] + '] ... ')
            ret=self.check_type(filename,'database')
            if ret:
                taskList['database'][i]['to'] = False
                continue
            else:
                print (self.rsyn_upload(filename, 'database', mdata['name'], aTask))
                public.WriteLog('一键迁移', aTask['name'] + '[' + taskList['database'][i]['name'] + ']迁移完成')
                self.WriteLogs('正在迁移数据库!完成%s' % aTask['name'])
                taskList['database'][i]['to'] = True
        public.writeFile(listFile, json.dumps(taskList))

        # 迁移FTP
        aTask['name'] = 'FTP'
        for i in range(len(taskList['ftp'])):
            aTask['done'] += 1
            aTask['name'] = 'FTP[' + taskList['ftp'][i]['name'] + ']'
            public.writeFile(actionTask, json.dumps(aTask))
            if taskList['ftp'][i]['to']: continue
            if not self.CheckReTo('ftps', taskList['ftp'][i]['name'], aTask): continue
            print ('正在迁移FTP ... ')
            public.WriteLog('一键迁移', '正在迁移' + aTask['name'] + '[' + taskList['ftp'][i]['name'] + ']')
            self.WriteLogs('正在迁FTP!%s' % aTask['name'])
            # /www/server/panel/plugin/psync/backup/ftp.json
            filename = self.__setupPath + '/backup/ftp.json'
            public.writeFile(filename, taskList['ftp'][i]['name'])
            ret=self.check_type(filename,'ftp')
            if ret:
                taskList['ftp'][i]['to'] = False
                continue
            else:
                print (self.rsyn_upload(filename, 'ftp', '', aTask))
                public.WriteLog('一键迁移', aTask['name'] + '[' + taskList['ftp'][i]['name'] + ']迁移完成')
                self.WriteLogs('正在迁FTP!完成%s' % aTask['name'])
                taskList['ftp'][i]['to'] = True
        public.writeFile(listFile, json.dumps(taskList))

        # 迁移操作日志+FTP帐户
        aTask['name'] = '操作日志'
        self.SetSpeedTo(aTask)
        public.writeFile(actionTask, json.dumps(aTask))

        filename = '111'
        print ('正在迁移操作日志 ... ')
        public.WriteLog('一键迁移', '正在迁移操作日志...')
        self.WriteLogs('一键迁移正在迁移操作日志...')
        print (self.rsyn_upload(filename, 'log', '', aTask))
        taskList['log']['to'] = True
        public.WriteLog('一键迁移', '操作日志迁移完成!')
        self.WriteLogs('一键迁移操作日志迁移完成!')
        aTask['name'] = '迁移完成'
        aTask['count'] = 0
        aTask['done'] = 0
        self.SetSpeedTo(aTask)
        public.writeFile(actionTask, json.dumps(aTask))
        taskList['status'] = True
        public.writeFile(listFile, json.dumps(taskList))
        os.system('rm -rf ' + self.__backupPath + '/*')


    def rsyn_upload(self, filename, type, name, aTask):
        if type=='log':
            result = self.UploadTo(filename, type, name, aTask)
            return result
        self.WriteLogs('%s-%s-%s-%s' % (filename, type, name, aTask))
        self.WriteLogs('123456')
        aTask1 = {}
        aTask1['name'] = aTask['name']
        aTask1['count'] = str(aTask['count'])
        aTask1['done'] = str(aTask['done'])
        self.WriteLogs('%s%s%s' % (aTask1['name'], str(aTask1['count']), str(aTask1['done'])))
        actionTask = self.__setupPath + '/actionTask.json'
        self.WriteLogs('写入OK')
        public.writeFile(actionTask, json.dumps(aTask1))
        self.WriteLogs('发送%s' % filename)
        ret = self.to_rsync(filename, type, name)
        self.WriteLogs('发送成功%s' % filename)
        result = self.UploadTo(filename, type, name, aTask)
        return result

    def to_rsync(self, filename, type, name):
        self.WriteLogs('正在发送2222%s--%s' % (type, name))
        relist = self.__setupPath + '/toToken.json'
        if not os.path.exists(relist): return public.returnMsg(False, '获取IP失败!')
        self.WriteLogs('获取ip文件成功')
        ip_list = json.loads(public.readFile(relist))
        url = ip_list['url']
        self.WriteLogs('获取url%s' % url)
        ip=ip_list['url'].split(':')[1].replace('//','')
        print ('客户端IP为%s' % ip)
        print ('正在发送%s--%s' % (type, name))
        self.WriteLogs('IP:%s' % ip)
        os.system('chown root.root ' + self.__rsync_passwd)
        self.WriteLogs('/usr/bin/rsync --port=%s  -avzp -P %s liang@%s::9fc81642102bf60d/ --password-file=%s' % (self.__port, filename, ip, self.__rsync_passwd))
        os.system( '/usr/bin/rsync --port=%s -avzp -P %s liang@%s::9fc81642102bf60d/ --password-file=%s >>/root/rsync.log' % (self.__port, filename, ip, self.__rsync_passwd))
        self.WriteLogs('/usr/bin/rsync --port=%s  -avzp -P %s liang@%s::9fc81642102bf60d/ --password-file=%s' % (
        self.__port, filename, ip, self.__rsync_passwd))
        if type == 'database':
            os.system('rm -rf %s' % filename)
        return True

    def Recovery_data(self, get):
        self.WriteLogs('已经收到文件')
        relist = self.__setupPath + '/relist.json'
        if not os.path.exists(relist): return public.returnMsg(False, '非法数据!')
        aTask = {}
        aTask['name'] = get.tname
        aTask['count'] = get.tcount
        aTask['done'] = get.tdone
        actionTask = self.__setupPath + '/actionTask.json'
        public.writeFile(actionTask, json.dumps(aTask))
        filename = self.__wwwroot + '/' + get.fname
        if get.stype == 'site':  result = self.ReSiteFile(filename, get.sname)
        if get.stype == 'database':  result = self.ReDataFile(filename, get.sname)
        if get.stype == 'ftp': result = self.RePanelFtp(filename)
        if get.stype == 'log': result = self.RePanelLog(filename)

        return result

    def UploadTo(self, filename, type, name, aTask):
        toToken = self.GetToToken()
        self.WriteLogs('正在用rsync发送文件%s' % filename)
        toUrl = toToken['url'] + '/pluginApi?action=a&name=psync&s=Recovery_data'
        os.system('curl -k -m 86400 --form "token=' + toToken['token'] + '" --form "sname=' + name + '" --form "stype=' + type + '" --form "fname=' + os.path.basename(filename) + '" --form "tname=' + aTask['name'] + '" --form "tcount=' + str( aTask['count']) + '" --form "tdone=' + str(aTask['done']) + '" "' + toUrl + '"')
        return True

    def RePanelFtp(self, filename):
        if not os.path.exists(filename): return False
        name = public.readFile(filename).strip()
        relist = self.__setupPath + '/relist.json'
        relistData = json.loads(public.readFile(relist))
        for i in range(len(relistData['ftp'])):
            if relistData['ftp'][i]['name'] == name:
                ftpInfo = relistData['ftp'][i]
                if public.M('ftps').where('name=?', (ftpInfo['name'],)).count(): continue
                if not os.path.exists(ftpInfo['path']):
                    os.system('mkdir -p ' + ftpInfo['path'])
                    os.system('chown www.www ' + ftpInfo['path'])
                    os.system('chmod 755 ' + ftpInfo['path'])
                public.ExecShell('/www/server/pure-ftpd/bin/pure-pw useradd ' + ftpInfo['name'] + ' -u www -d ' + ftpInfo['path'] + '<<EOF \n' + ftpInfo['password'] + '\n' + ftpInfo['password'] + '\nEOF')
                public.ExecShell('/www/server/pure-ftpd/bin/pure-pw mkdb /www/server/pure-ftpd/etc/pureftpd.pdb')
                public.M('ftps').add('name,password,path,status,ps,addtime', (
                ftpInfo['name'], ftpInfo['password'], ftpInfo['path'], ftpInfo['status'], ftpInfo['ps'],
                ftpInfo['addtime']))
                relistData['ftp'][i]['to'] = True
                public.writeFile(relist, json.dumps(relistData))
                os.system('rm -rf %s' % filename)
                public.WriteLog('FTP文件已经备份成功', 'hao l ')
                self.WriteLogs('FTP文件已经备份成功')
                return True
        return False

    # 备份日志
    def BackupLog(self, isLog=None):
        print ('正在备份操作日志...')
        data = []
        if not isLog:
            data = public.M('logs').field('type,log,addtime').select()
        #
        backupLog = self.__backupPath + '/log.json'
        public.writeFile(backupLog, json.dumps(data))
        print ('备份完成，共' + str(len(data)) + '条日志!')
        return backupLog

    # 备份站点
    def BackupSite(self, name, path):
        bt_conf = path + '/bt_conf'
        os.system('mkdir -p ' + bt_conf + '/ssl')

        # 备份Nginx配置文件
        nginxConf = bt_conf + '/nginx.conf'
        panelNginxConf = '/www/server/panel/vhost/nginx/' + name + '.conf'
        if os.path.exists(panelNginxConf):
            conf = public.readFile(panelNginxConf).replace(' default_server', '')
            public.writeFile(nginxConf, conf)

        # 备份Nginx伪静态文件
        nginxRewrite = bt_conf + '/rewrite.conf'
        panelNginxRewrite = '/www/server/panel/vhost/rewrite/' + name + '.conf'
        if os.path.exists(panelNginxRewrite):
            conf = public.readFile(panelNginxRewrite)
            public.writeFile(nginxRewrite, conf)

        # 备份子目录伪静态规则
        try:
            panelRewritePath = '/www/server/panel/vhost/rewrite'
            rs = os.listdir(panelRewritePath)
            for r in rs:
                if r.find(name + '_') == -1: continue
                nginxRewrite = bt_conf + '/rewrite_' + r.split('_')[1]
                conf = public.readFile(panelRewritePath + '/' + r)
                public.writeFile(nginxRewrite, conf)
        except:
            pass

        # 备份apache配置文件
        httpdConf = bt_conf + '/apache.conf'
        panelHttpdConf = '/www/server/panel/vhost/apache/' + name + '.conf'
        if os.path.exists(panelHttpdConf):
            conf = public.readFile(panelHttpdConf)
            public.writeFile(httpdConf, conf)

        # 备份证书文件
        sslSrcPath = bt_conf + '/ssl/'
        sslDstPath = '/etc/letsencrypt/live/' + name + '/'
        sslFiles = ['privkey.pem', 'fullchain.pem', 'partnerOrderId', 'README']
        for sslFile in sslFiles:
            if os.path.exists(sslDstPath + sslFile):
                conf = public.readFile(sslDstPath + sslFile)
                public.writeFile(sslSrcPath + sslFile, conf)
        # return self.BackupPath(path)
        return path

    # 写输出日志
    def WriteLogs(self, logMsg):
        if os.path.exists(self.logPath):
            os.system('touch %s' % self.logPath)
        fp = open(self.logPath, 'a+')
        fp.write(logMsg + '\n')
        fp.close()

    # 恢复面板日志
    # /www/wwwroot/log.json
    def RePanelLog(self, filename):
        relist = self.__setupPath + '/relist.json'
        relistData = json.loads(public.readFile(relist))
        relistData['status'] = True
        relistData['log']['to'] = True
        public.writeFile(relist, json.dumps(relistData))
        return True

    # 恢复数据库文件
    def ReDataFile(self, filename, name):
        relist = self.__setupPath + '/relist.json'
        relistData = json.loads(public.readFile(relist))
        for i in range(len(relistData['database'])):
            if relistData['database'][i]['name'] == name:
                data = relistData['database'][i]
                if not self.RePanelDataBase(data): return False
                if not self.InputDatabase(data['name'], data['password'], filename): return False
                relistData['database'][i]['to'] = True
                public.writeFile(relist, json.dumps(relistData))
                return True
        return False

        # 恢复数据库面板数据

    def RePanelDataBase(self, mdata):
        if public.M('databases').where('name=?', (mdata['name'],)).count(): return False

        # 添加MYSQL
        import panelMysql
        result = panelMysql.panelMysql().execute("create database `" + mdata['name'] + "`")
        panelMysql.panelMysql().execute("drop user '" + mdata['name'] + "'@'localhost'")
        panelMysql.panelMysql().execute("drop user '" + mdata['name'] + "'@'" + mdata['accept'] + "'")
        panelMysql.panelMysql().execute( "grant all privileges on `" + mdata['name'] + "`.* to '" + mdata['name'] + "'@'localhost' identified by '" +mdata['password'] + "'")
        panelMysql.panelMysql().execute("grant all privileges on `" + mdata['name'] + "`.* to '" + mdata['name'] + "'@'" + mdata['accept'] + "' identified by '" + mdata['password'] + "'")
        panelMysql.panelMysql().execute("flush privileges")
        pid = public.M('databases').add('name,username,password,accept,ps,addtime', (mdata['name'], mdata['username'], mdata['password'], mdata['accept'], mdata['ps'], mdata['addtime']))
        if not pid: return False
        return True

    # 恢复站点文件
    def ReSiteFile(self, filename, name):
        relist = self.__setupPath + '/relist.json'
        relistData = json.loads(public.readFile(relist))

        for i in range(len(relistData['site'])):
            if relistData['site'][i]['name'] == name:
                msite = relistData['site'][i]
                if not self.RePanelSite(msite): return False
                # if not self.ComerPath(msite['path'], filename): return False

                # 恢复nginx配置文件
                nginxConf = msite['path'] + '/bt_conf/nginx.conf'
                panelNginxConf = '/www/server/panel/vhost/nginx/' + msite['name'] + '.conf'
                if os.path.exists(nginxConf):
                    conf = public.readFile(nginxConf)
                    public.writeFile(panelNginxConf, conf)

                # 恢复nginx伪静态文件
                nginxRewrite = msite['path'] + '/bt_conf/rewrite.conf'
                panelNginxRewrite = '/www/server/panel/vhost/rewrite/' + msite['name'] + '.conf'
                if os.path.exists(nginxRewrite):
                    conf = public.readFile(nginxRewrite)
                    public.writeFile(panelNginxRewrite, conf)

                # 恢复子目录伪静态规则
                try:
                    backupRewrite = msite['path'] + '/bt_conf'
                    rs = os.listdir(backupRewrite)
                    for r in rs:
                        if r.find('rewrite_') == -1: continue
                        nginxRewrite = '/www/server/panel/vhost/rewrite/' + name + '_' + r.split('_')[1]
                        conf = public.readFile(backupRewrite + '/' + r)
                        public.writeFile(nginxRewrite, conf)
                except:
                    pass

                # 恢复apache配置文件
                httpdConf = msite['path'] + '/bt_conf/apache.conf'
                panelHttpdConf = '/www/server/panel/vhost/apache/' + msite['name'] + '.conf'
                if os.path.exists(httpdConf):
                    conf = public.readFile(httpdConf)
                    public.writeFile(panelHttpdConf, conf)

                # 恢复证书文件
                sslSrcPath = msite['path'] + '/bt_conf/ssl/'
                sslDstPath = '/etc/letsencrypt/live/' + msite['name'] + '/'
                os.system('mkdir -p ' + sslDstPath)
                sslFiles = ['privkey.pem', 'fullchain.pem', 'partnerOrderId', 'README']
                for sslFile in sslFiles:
                    if os.path.exists(sslSrcPath + sslFile):
                        conf = public.readFile(sslSrcPath + sslFile)
                        public.writeFile(sslDstPath + sslFile, conf)

                # 清理临时文件
                os.system('rm -rf ' + msite['path'] + '/bt_conf')
                if os.path.exists(msite['path'] + '/.user.ini'): os.system('chattr +i ' + msite['path'] + '/.user.ini')
                relistData['site'][i]['to'] = True
                public.writeFile(relist, json.dumps(relistData))
                public.serviceReload()
                return True
        return False

    # 恢复站点面板数据
    def RePanelSite(self, msite):
        if public.M('sites').where('name=?', (msite['name'],)).count(): return False

        pid = public.M('sites').add('name,path,status,ps,addtime',
                                    (msite['name'], msite['path'], msite['status'], msite['ps'], msite['addtime']))
        if not pid: return False
        sql = public.M('domain')
        for domain in msite['domains']:
            sql.table('domain').add('pid,name,port,addtime', (pid, domain['name'], domain['port'], domain['addtime']))

        for binding in msite['binding']:
            sql.table('binding').add('pid,domain,port,path,addtime',
                                     (pid, binding['domain'], '80', binding['path'], binding['addtime']))
        return True

    # 解压到目录
    def ComerPath(self, path, comerfile):
        if not os.path.exists(comerfile): return False
        if not os.path.exists(path): os.system('mkdir -p ' + path)
        os.system('tar -zxvf ' + comerfile + ' -C ' + path + '/')
        return True

    # 打包目录
    def BackupPath(self, path):
        print ('正在压缩目录： [' + path + '] ...')
        if not os.path.exists(self.__backupPath):
            os.system('mkdir -p ' + self.__backupPath)
            os.system('chmod -R 600 ' + self.__backupPath)
        dfile = self.__backupPath + '/' + 'path_' + str(time.time()) + '.tar.gz'
        os.system("cd '" + path + "' && tar -zcvf '" + dfile + "' * .user.ini .htaccess")
        os.system('rm -rf ' + path + '/bt_conf')
        if not os.path.exists(dfile): return False
        return dfile

    # 导出数据库
    def BackupDatabase(self, name, username, password):
        print ('正在导出数据库： [' + name + '] ...')
        backupPath = self.__wwwroot
        if not os.path.exists(backupPath):
            os.system('mkdir -p ' + backupPath)
            os.system('chmod -R 600 ' + backupPath)
        backupName = backupPath + '/db_' + name + '_' + str(time.time()) + '.sql.gz'
        os.system(
            "/www/server/mysql/bin/mysqldump -u" + username + " -p" + password + " " + name + " | gzip > " + backupName)
        if not os.path.exists(backupName): return False
        return backupName

    # 导入数据库
    def InputDatabase(self, name, password, sqlgz):
        if not os.path.exists(sqlgz): return False
        os.system("gunzip -f < " + sqlgz + "|/www/server/mysql/bin/mysql -u" + name + " -p" + password + " " + name)
        time.sleep(1)
        os.system('rm -rf %s' % (sqlgz))
        return True


if __name__ == "__main__":
    p = psync_main()
    p.StartBackup()
    import json
    type = sys.argv[1]
    if type == 'start':
        p.start()
    else:
        p.StartBackup()