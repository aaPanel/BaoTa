 #coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------
from BTPanel import session,request
import public,os,json,time,apache,psutil
class ajax:

    def GetApacheStatus(self,get):
        a = apache.apache()
        return a.GetApacheStatus()
  
    def GetProcessCpuPercent(self,i,process_cpu):
        try:
            pp = psutil.Process(i)
            if pp.name() not in process_cpu.keys():
                process_cpu[pp.name()] = float(pp.cpu_percent(interval=0.1))
            process_cpu[pp.name()] += float(pp.cpu_percent(interval=0.1))
        except:
            pass
    def GetNginxStatus(self,get):
        try:
            if not os.path.exists('/www/server/nginx/sbin/nginx'): return public.returnMsg(False,'未安装nginx')
            process_cpu = {}
            worker = int(public.ExecShell("ps aux|grep nginx|grep 'worker process'|wc -l")[0])-1
            workermen = int(public.ExecShell("ps aux|grep nginx|grep 'worker process'|awk '{memsum+=$6};END {print memsum}'")[0]) / 1024
            for proc in psutil.process_iter():
                if proc.name() == "nginx":
                    self.GetProcessCpuPercent(proc.pid,process_cpu)
            time.sleep(0.1)
            #取Nginx负载状态
            self.CheckStatusConf()
            result = public.httpGet('http://127.0.0.1/nginx_status')
            tmp = result.split()
            data = {}
            if "request_time" in tmp:
                data['accepts']  = tmp[8]
                data['handled']  = tmp[9]
                data['requests'] = tmp[10]
                data['Reading']  = tmp[13]
                data['Writing']  = tmp[15]
                data['Waiting']  = tmp[17]
            else:
                data['accepts'] = tmp[9]
                data['handled'] = tmp[7]
                data['requests'] = tmp[8]
                data['Reading'] = tmp[11]
                data['Writing'] = tmp[13]
                data['Waiting'] = tmp[15]
            data['active'] = tmp[2]
            data['worker'] = worker
            data['workercpu'] = round(float(process_cpu["nginx"]),2)
            data['workermen'] = "%s%s" % (int(workermen), "MB")
            return data
        except Exception as ex: 
            public.WriteLog('信息获取',"Nginx负载状态获取失败: %s" % ex)
            return public.returnMsg(False,'数据获取失败!')
    
    def GetPHPStatus(self,get):
        #取指定PHP版本的负载状态
        try:
            version = get.version
            uri = "/phpfpm_"+version+"_status?json"
            result = public.request_php(version,uri,'')
            tmp = json.loads(result)
            fTime = time.localtime(int(tmp['start time']))
            tmp['start time'] = time.strftime('%Y-%m-%d %H:%M:%S',fTime)
            return tmp
        except Exception as ex:
            public.WriteLog('信息获取',"PHP负载状态获取失败: {}".format(public.get_error_info()))
            return public.returnMsg(False,'负载状态获取失败!')
        
    def CheckStatusConf(self):
        if public.get_webserver() != 'nginx': return
        filename = session['setupPath'] + '/panel/vhost/nginx/phpfpm_status.conf'
        if os.path.exists(filename):
            if public.ReadFile(filename).find('nginx_status')!=-1: return
        
        conf = '''server {
    listen 80;
    server_name 127.0.0.1;
    allow 127.0.0.1;
    location /nginx_status {
        stub_status on;
        access_log off;
    }
}'''

        public.writeFile(filename,conf)
        public.serviceReload()
    
    
    def GetTaskCount(self,get):
        #取任务数量
        return public.M('tasks').where("status!=?",('1',)).count()
    
    def GetSoftList(self,get):
        #取软件列表
        import json,os
        tmp = public.readFile('data/softList.conf')
        data = json.loads(tmp)
        tasks = public.M('tasks').where("status!=?",('1',)).field('status,name').select()
        for i in range(len(data)):
            data[i]['check'] = public.GetConfigValue('root_path')+'/'+data[i]['check']
            for n in range(len(data[i]['versions'])):
                #处理任务标记
                isTask = '1'
                for task in tasks:
                    tmp = public.getStrBetween('[',']',task['name'])
                    if not tmp:continue
                    tmp1 = tmp.split('-')
                    if data[i]['name'] == 'PHP': 
                        if tmp1[0].lower() == data[i]['name'].lower() and tmp1[1] == data[i]['versions'][n]['version']: isTask = task['status'];
                    else:
                        if tmp1[0].lower() == data[i]['name'].lower(): isTask = task['status']
                
                #检查安装状态
                if data[i]['name'] == 'PHP': 
                    data[i]['versions'][n]['task'] = isTask
                    checkFile = data[i]['check'].replace('VERSION',data[i]['versions'][n]['version'].replace('.',''))
                else:
                    data[i]['task'] = isTask
                    version = public.readFile(public.GetConfigValue('root_path')+'/server/'+data[i]['name'].lower()+'/version.pl')
                    if not version:continue
                    if version.find(data[i]['versions'][n]['version']) == -1:continue
                    checkFile = data[i]['check']
                data[i]['versions'][n]['status'] = os.path.exists(checkFile)
        return data
    
    
    def GetLibList(self,get):
        #取插件列表
        import json,os
        tmp = public.readFile('data/libList.conf')
        data = json.loads(tmp)
        for i in range(len(data)):
            data[i]['status'] = self.CheckLibInstall(data[i]['check'])
            data[i]['optstr'] = self.GetLibOpt(data[i]['status'], data[i]['opt'])
        return data
    
    def CheckLibInstall(self,checks):
        for cFile in checks:
            if os.path.exists(cFile): return '已安装'
        return '未安装'
    
    #取插件操作选项
    def GetLibOpt(self,status,libName):
        optStr = ''
        if status == '未安装':
            optStr = '<a class="link" href="javascript:InstallLib(\''+libName+'\');">安装</a>'
        else:
            libConfig = '配置'
            if(libName == 'beta'): libConfig = '内测资料'
                                  
            optStr = '<a class="link" href="javascript:SetLibConfig(\''+libName+'\');">'+libConfig+'</a> | <a class="link" href="javascript:UninstallLib(\''+libName+'\');">卸载</a>'
        return optStr
    
    #取插件AS
    def GetQiniuAS(self,get):
        filename = public.GetConfigValue('setup_path') + '/panel/data/'+get.name+'As.conf'
        if not os.path.exists(filename): public.writeFile(filename,'')
        data = {}
        data['AS'] = public.readFile(filename).split('|')
        data['info'] = self.GetLibInfo(get.name)
        if len(data['AS']) < 3:
            data['AS'] = ['','','','']
        return data


    #设置插件AS
    def SetQiniuAS(self,get):
        info = self.GetLibInfo(get.name)
        filename = public.GetConfigValue('setup_path') + '/panel/data/'+get.name+'As.conf'
        conf = get.access_key.strip() + '|' + get.secret_key.strip() + '|' + get.bucket_name.strip() + '|' + get.bucket_domain.strip()
        public.writeFile(filename,conf)
        public.ExecShell("chmod 600 " + filename)
        result = public.ExecShell(public.get_python_bin() + " " + public.GetConfigValue('setup_path') + "/panel/script/backup_"+get.name+".py list")
        
        if result[0].find("ERROR:") == -1: 
            public.WriteLog("插件管理", "设置插件["+info['name']+"]AS!")
            return public.returnMsg(True, '设置成功!')
        return public.returnMsg(False, 'ERROR: 无法连接到'+info['name']+'服务器,请检查[AK/SK/存储空间]设置是否正确!')
    
    #设置内测
    def SetBeta(self,get):
        data = {}
        data['username'] = get.bbs_name
        data['qq'] = get.qq
        data['email'] = get.email
        result = public.httpPost(public.GetConfigValue('home') + '/Api/LinuxBeta',data);
        import json;
        data = json.loads(result)
        if data['status']:
            public.writeFile('data/beta.pl',get.bbs_name + '|' + get.qq + '|' + get.email);
        return data
    #取内测资格状态
    def GetBetaStatus(self,get):
        try:
            return public.readFile('data/beta.pl').strip()
        except:
            return 'False'
               

    #获取指定插件信息
    def GetLibInfo(self,name):
        import json
        tmp = public.readFile('data/libList.conf')
        data = json.loads(tmp)
        for lib in data:
            if name == lib['opt']: return lib
        return False

    #获取文件列表
    def GetQiniuFileList(self,get):
        try:
            import json             
            result = public.ExecShell(public.get_python_bin() + " " + public.GetConfigValue('setup_path') + "/panel/script/backup_"+get.name+".py list")
            return json.loads(result[0])
        except:
            return public.returnMsg(False, '获取列表失败,请检查[AK/SK/存储空间]设是否正确!');

    
    
    #取网络连接列表
    def GetNetWorkList(self,get):
        import psutil
        netstats = psutil.net_connections()
        networkList = []
        for netstat in netstats:
            tmp = {}
            if netstat.type == 1:
                tmp['type'] = 'tcp'
            else:
                tmp['type'] = 'udp'
            tmp['family']   = netstat.family
            tmp['laddr']    = netstat.laddr
            tmp['raddr']    = netstat.raddr
            tmp['status']   = netstat.status
            p = psutil.Process(netstat.pid)
            tmp['process']  = p.name()
            tmp['pid']      = netstat.pid
            networkList.append(tmp)
            del(p)
            del(tmp)
        networkList = sorted(networkList, key=lambda x : x['status'], reverse=True)
        return networkList
    
    #取进程列表
    def GetProcessList(self,get):
        import psutil,pwd
        Pids = psutil.pids()
        
        processList = []
        for pid in Pids:
            try:
                tmp = {}
                p = psutil.Process(pid)
                if p.exe() == "": continue
                
                tmp['name'] = p.name();                             #进程名称
                if self.GoToProcess(tmp['name']): continue
                
                
                tmp['pid'] = pid;                                   #进程标识
                tmp['status'] = p.status();                         #进程状态
                tmp['user'] = p.username();                         #执行用户
                cputimes = p.cpu_times()
                tmp['cpu_percent'] = p.cpu_percent(0.1)
                tmp['cpu_times'] = cputimes.user                             #进程占用的CPU时间
                tmp['memory_percent'] = round(p.memory_percent(),3)          #进程占用的内存比例
                pio = p.io_counters()
                tmp['io_write_bytes'] = pio.write_bytes             #进程总共写入字节数
                tmp['io_read_bytes'] = pio.read_bytes               #进程总共读取字节数
                tmp['threads'] = p.num_threads()                    #进程总线程数
                
                processList.append(tmp)
                del(p)
                del(tmp)
            except:
                continue
        import operator
        processList = sorted(processList, key=lambda x : x['memory_percent'], reverse=True)
        processList = sorted(processList, key=lambda x : x['cpu_times'], reverse=True)
        return processList
    
    #结束指定进程
    def KillProcess(self,get):
        #return public.returnMsg(False,'演示服务器，禁止此操作!');
        import psutil
        p = psutil.Process(int(get.pid))
        name = p.name()
        if name == 'python': return public.returnMsg(False,'KILL_PROCESS_ERR')
        
        p.kill()
        public.WriteLog('TYPE_PROCESS','KILL_PROCESS',(get.pid,name))
        return public.returnMsg(True,'KILL_PROCESS',(get.pid,name))
    
    def GoToProcess(self,name):
        ps = ['sftp-server','login','nm-dispatcher','irqbalance','qmgr','wpa_supplicant','lvmetad','auditd','master','dbus-daemon','tapdisk','sshd','init','ksoftirqd','kworker','kmpathd','kmpath_handlerd','python','kdmflush','bioset','crond','kthreadd','migration','rcu_sched','kjournald','iptables','systemd','network','dhclient','systemd-journald','NetworkManager','systemd-logind','systemd-udevd','polkitd','tuned','rsyslogd']
        
        for key in ps:
            if key == name: return True
        
        return False
        
    
    def GetNetWorkIo(self,get):
        #取指定时间段的网络Io
        data =  public.M('network').dbfile('system').where("addtime>=? AND addtime<=?",(get.start,get.end)).field('id,up,down,total_up,total_down,down_packets,up_packets,addtime').order('id asc').select()
        return self.ToAddtime(data)
    
    def GetDiskIo(self,get):
        #取指定时间段的磁盘Io
        data = public.M('diskio').dbfile('system').where("addtime>=? AND addtime<=?",(get.start,get.end)).field('id,read_count,write_count,read_bytes,write_bytes,read_time,write_time,addtime').order('id asc').select()
        return self.ToAddtime(data)
    def GetCpuIo(self,get):
        #取指定时间段的CpuIo
        data = public.M('cpuio').dbfile('system').where("addtime>=? AND addtime<=?",(get.start,get.end)).field('id,pro,mem,addtime').order('id asc').select()
        return self.ToAddtime(data,True)
    
    def get_load_average(self,get):
        data = public.M('load_average').dbfile('system').where("addtime>=? AND addtime<=?",(get.start,get.end)).field('id,pro,one,five,fifteen,addtime').order('id asc').select()
        return self.ToAddtime(data)
    
    
    def ToAddtime(self,data,tomem = False):
        import time
        #格式化addtime列
        
        if tomem:
            import psutil
            mPre = (psutil.virtual_memory().total / 1024 / 1024) / 100
        length = len(data)
        he = 1
        if length > 100: he = 1
        if length > 1000: he = 3
        if length > 10000: he = 15
        if he == 1:
            for i in range(length):
                data[i]['addtime'] = time.strftime('%m/%d %H:%M',time.localtime(float(data[i]['addtime'])))
                if tomem and data[i]['mem'] > 100: data[i]['mem'] = data[i]['mem'] / mPre
            
            return data
        else:
            count = 0
            tmp = []
            for value in data:
                if count < he: 
                    count += 1
                    continue
                value['addtime'] = time.strftime('%m/%d %H:%M',time.localtime(float(value['addtime'])))
                if tomem and value['mem'] > 100: value['mem'] = value['mem'] / mPre
                tmp.append(value)
                count = 0
            return tmp
        
    def GetInstalleds(self,softlist):
        softs = ''
        for soft in softlist['data']:
            try:
                for v in soft['versions']:
                    if v['status']: softs += soft['name'] + '-' + v['version'] + '|'
            except:
                pass
        return softs


    
    #获取SSH爆破次数
    def get_ssh_intrusion(self):
        fp = open('/var/log/secure','rb')
        l = fp.readline()
        intrusion_total = 0
        while l:
            if l.find('Failed password for root') != -1:  intrusion_total += 1
            l = fp.readline()
        fp.close()
        return intrusion_total

    #申请内测版
    def apple_beta(self,get):
        try:
            userInfo = json.loads(public.ReadFile('data/userInfo.json'))
            p_data = {}
            p_data['uid'] = userInfo['uid']
            p_data['access_key'] = userInfo['access_key']
            p_data['username'] = userInfo['username']
            result = public.HttpPost(public.GetConfigValue('home') + '/api/panel/apple_beta',p_data,5)
            try:
                return json.loads(result)
            except: return public.returnMsg(False,'AJAX_CONN_ERR')
        except: return public.returnMsg(False,'AJAX_USER_BINDING_ERR')

    def to_not_beta(self,get):
        try:
            userInfo = json.loads(public.ReadFile('data/userInfo.json'))
            p_data = {}
            p_data['uid'] = userInfo['uid']
            p_data['access_key'] = userInfo['access_key']
            p_data['username'] = userInfo['username']
            result = public.HttpPost(public.GetConfigValue('home') + '/api/panel/to_not_beta',p_data,5)
            try:
                return json.loads(result)
            except: return public.returnMsg(False,'AJAX_CONN_ERR')
        except: return public.returnMsg(False,'AJAX_USER_BINDING_ERR')

    def to_beta(self):
        try:
            userInfo = json.loads(public.ReadFile('data/userInfo.json'))
            p_data = {}
            p_data['uid'] = userInfo['uid']
            p_data['access_key'] = userInfo['access_key']
            p_data['username'] = userInfo['username']
            public.HttpPost(public.GetConfigValue('home') + '/api/panel/to_beta',p_data,5)
        except: pass

    def get_uid(self):
        try:
            userInfo = json.loads(public.ReadFile('data/userInfo.json'))
            return userInfo['uid']
        except: return 0

    #获取最新的5条测试版更新日志
    def get_beta_logs(self,get):
        try:
            data = json.loads(public.HttpGet(public.GetConfigValue('home') + '/api/panel/get_beta_logs'))
            return data
        except:
            return public.returnMsg(False,'AJAX_CONN_ERR')

    def get_other_info(self):
        other = {}
        other['ds'] = []
        ds = public.M('domain').field('name').select()
        for d in ds:
            other['ds'].append(d['name'])
        return ','.join(other['ds'])

    

    
    def UpdatePanel(self,get):
        try:
            if not public.IsRestart(): return public.returnMsg(False,'EXEC_ERR_TASK')
            import json
            if int(session['config']['status']) == 0:
                public.HttpGet(public.GetConfigValue('home')+'/Api/SetupCount?type=Linux')
                public.M('config').where("id=?",('1',)).setField('status',1)
            
            #取回远程版本信息
            if 'updateInfo' in session and hasattr(get,'check') == False:
                updateInfo = session['updateInfo']
            else:
                logs = public.get_debug_log()
                import psutil,system,sys
                mem = psutil.virtual_memory()
                import panelPlugin
                mplugin = panelPlugin.panelPlugin()

                mplugin.ROWS = 10000
                panelsys = system.system()
                data = {}
                data['ds'] = '' #self.get_other_info()
                data['sites'] = str(public.M('sites').count())
                data['ftps'] = str(public.M('ftps').count())
                data['databases'] = str(public.M('databases').count())
                data['system'] = panelsys.GetSystemVersion() + '|' + str(mem.total / 1024 / 1024) + 'MB|' + str(public.getCpuType()) + '*' + str(psutil.cpu_count()) + '|' + str(public.get_webserver()) + '|' +session['version']
                data['system'] += '||'+self.GetInstalleds(mplugin.getPluginList(None))
                data['logs'] = logs
                data['client'] = request.headers.get('User-Agent')
                data['oem'] = ''
                data['intrusion'] = 0
                data['uid'] = self.get_uid()
                #msg = public.getMsg('PANEL_UPDATE_MSG');
                data['o'] = ''
                filename = '/www/server/panel/data/o.pl'
                if os.path.exists(filename): data['o'] = str(public.readFile(filename))
                sUrl = public.GetConfigValue('home') + '/api/panel/updateLinux'
                updateInfo = json.loads(public.httpPost(sUrl,data))
                if not updateInfo: return public.returnMsg(False,"CONNECT_ERR")
                #updateInfo['msg'] = msg;
                session['updateInfo'] = updateInfo
                
            #检查是否需要升级
            if updateInfo['is_beta'] == 1:
                if updateInfo['beta']['version'] ==session['version']: return public.returnMsg(False,updateInfo)
            else:
                if updateInfo['version'] ==session['version']: return public.returnMsg(False,updateInfo)
            
            
            #是否执行升级程序 
            if(updateInfo['force'] == True or hasattr(get,'toUpdate') == True or os.path.exists('data/autoUpdate.pl') == True):
                if updateInfo['is_beta'] == 1: updateInfo['version'] = updateInfo['beta']['version']
                setupPath = public.GetConfigValue('setup_path')
                uptype = 'update'
                httpUrl = public.get_url()
                if httpUrl: updateInfo['downUrl'] =  httpUrl + '/install/' + uptype + '/LinuxPanel-' + updateInfo['version'] + '.zip'
                public.downloadFile(updateInfo['downUrl'],'panel.zip')
                if os.path.getsize('panel.zip') < 1048576: return public.returnMsg(False,"PANEL_UPDATE_ERR_DOWN")
                public.ExecShell('unzip -o panel.zip -d ' + setupPath + '/')
                import compileall
                if os.path.exists('/www/server/panel/runserver.py'): public.ExecShell('rm -f /www/server/panel/*.pyc')
                if os.path.exists('/www/server/panel/class/common.py'): public.ExecShell('rm -f /www/server/panel/class/*.pyc')
                
                if os.path.exists('panel.zip'):os.remove("panel.zip")
                session['version'] = updateInfo['version']
                if 'getCloudPlugin' in session: del(session['getCloudPlugin'])
                if updateInfo['is_beta'] == 1: self.to_beta()
                public.ExecShell("/etc/init.d/bt start")
                public.writeFile('data/restart.pl','True')
                return public.returnMsg(True,'PANEL_UPDATE',(updateInfo['version'],))
            
            #输出新版本信息
            data = {
                'status' : True,
                'version': updateInfo['version'],
                'updateMsg' : updateInfo['updateMsg']
            }
            
            public.ExecShell('rm -rf /www/server/phpinfo/*')
            return public.returnMsg(True,updateInfo)
        except Exception as ex:
            return public.get_error_info()
            return public.returnMsg(False,"CONNECT_ERR")
         
    #检查是否安装任何
    def CheckInstalled(self,get):
        checks = ['nginx','apache','php','pure-ftpd','mysql']
        import os
        for name in checks:
            filename = public.GetConfigValue('root_path') + "/server/" + name
            if os.path.exists(filename): return True
        return False
    
    
    #取已安装软件列表
    def GetInstalled(self,get):
        import system
        data = system.system().GetConcifInfo()
        return data
    
    #取PHP配置
    def GetPHPConfig(self,get):
        import re,json
        filename = public.GetConfigValue('setup_path') + '/php/' + get.version + '/etc/php.ini'
        if public.get_webserver() == 'openlitespeed':
            filename = '/usr/local/lsws/lsphp{}/etc/php/{}.{}/litespeed/php.ini'.format(get.version,get.version[0],get.version[1])
            if os.path.exists('/etc/redhat-release'):
                filename = '/usr/local/lsws/lsphp' + get.version + '/etc/php.ini'
        if not os.path.exists(filename): return public.returnMsg(False,'PHP_NOT_EXISTS')
        phpini = public.readFile(filename)
        data = {}
        rep = "disable_functions\s*=\s{0,1}(.*)\n"
        tmp = re.search(rep,phpini).groups()
        data['disable_functions'] = tmp[0]
        
        rep = "upload_max_filesize\s*=\s*([0-9]+)(M|m|K|k)"
        tmp = re.search(rep,phpini).groups()
        data['max'] = tmp[0]
        
        rep = u"\n;*\s*cgi\.fix_pathinfo\s*=\s*([0-9]+)\s*\n"
        tmp = re.search(rep,phpini).groups()
        if tmp[0] == '0':
            data['pathinfo'] = False
        else:
            data['pathinfo'] = True
        self.getCloudPHPExt(get)
        phplib = json.loads(public.readFile('data/phplib.conf'))
        libs = []
        tasks = public.M('tasks').where("status!=?",('1',)).field('status,name').select()
        phpini_ols = None
        for lib in phplib:
            lib['task'] = '1'
            for task in tasks:
                tmp = public.getStrBetween('[',']',task['name'])
                if not tmp:continue
                tmp1 = tmp.split('-')
                if tmp1[0].lower() == lib['name'].lower():
                    lib['task'] = task['status']
                    lib['phpversions'] = []
                    lib['phpversions'].append(tmp1[1])
            if public.get_webserver() == 'openlitespeed':
                lib['status'] = False
                get.php_version = "{}.{}".format(get.version[0],get.version[1])
                if not phpini_ols:
                    phpini_ols = self.php_info(get)['phpinfo']['modules'].lower()
                    phpini_ols = phpini_ols.split()
                for i in phpini_ols:
                    if lib['check'][:-3].lower() == i :
                        lib['status'] = True
                        break
                    if "ioncube" in lib['check'][:-3].lower() and "ioncube" == i:
                        lib['status'] = True
                        break
            else:
                if phpini.find(lib['check']) == -1:
                    lib['status'] = False
                else:
                    lib['status'] = True
                
            libs.append(lib)
        
        data['libs'] = libs
        return data
        
    #获取PHP扩展
    def getCloudPHPExt(self,get):
        import json
        try:
            if 'php_ext' in session: return True
            if not session.get('download_url'): session['download_url'] = 'http://download.bt.cn'
            download_url = session['download_url'] + '/install/lib/phplib.json'
            tstr = public.httpGet(download_url)
            data = json.loads(tstr)
            if not data: return False
            public.writeFile('data/phplib.conf',json.dumps(data))
            session['php_ext'] = True
            return True
        except:
            return False

    #取PHPINFO信息
    def GetPHPInfo(self,get):
        if public.get_webserver() == "openlitespeed":
            shell_str = "/usr/local/lsws/lsphp{}/bin/php -i".format(get.version)
            return public.ExecShell(shell_str)[0]
        sPath = '/www/server/phpinfo'
        if os.path.exists(sPath):
            public.ExecShell("rm -rf " + sPath)
        p_file = '/dev/shm/phpinfo.php'
        public.writeFile(p_file,'<?php phpinfo(); ?>')
        phpinfo = public.request_php(get.version,'/phpinfo.php','/dev/shm')
        if os.path.exists(p_file): os.remove(p_file)
        return phpinfo.decode()

    #清理日志
    def delClose(self,get):
        if not 'uid' in session: session['uid'] = 1
        if session['uid'] != 1: return public.returnMsg(False,'没有权限!')
        if 'tmp_login_id' in session:
            return public.returnMsg(False,'没有权限!')

        public.M('logs').where('id>?',(0,)).delete()
        public.WriteLog('TYPE_CONFIG','LOG_CLOSE')
        return public.returnMsg(True,'LOG_CLOSE')

    def __get_webserver_conffile(self):
        webserver = public.get_webserver()
        if webserver == 'nginx':
            filename = public.GetConfigValue('setup_path') + '/nginx/conf/nginx.conf'
        elif webserver == 'openlitespeed':
            filename = public.GetConfigValue('setup_path') + "/panel/vhost/openlitespeed/detail/phpmyadmin.conf"
        else:
            filename = public.GetConfigValue('setup_path') + '/apache/conf/extra/httpd-vhosts.conf'
        
        return filename

    # 获取phpmyadmin ssl配置
    def get_phpmyadmin_conf(self):
        if public.get_webserver() == "nginx":
            conf_file = "/www/server/panel/vhost/nginx/phpmyadmin.conf"
            rep = r"listen\s*(\d+)"
        else:
            conf_file = "/www/server/panel/vhost/apache/phpmyadmin.conf"
            rep = r"Listen\s*(\d+)"
        return {"conf_file":conf_file,"rep":rep}

    # 设置phpmyadmin路径
    def set_phpmyadmin_session(self):
        import re
        conf_file = self.get_phpmyadmin_conf()
        conf = public.readFile(conf_file["conf_file"])
        rep = conf_file["rep"]
        if conf:
            port = re.search(rep,conf).group(1)
            if session['phpmyadminDir']:
                path = session['phpmyadminDir'].split("/")[-1]
                ip = public.GetHost()
                session['phpmyadminDir'] = "https://{}:{}/{}".format(ip, port, path)

    # 获取phpmyadmin ssl状态
    def get_phpmyadmin_ssl(self,get):
        import re
        conf_file = self.get_phpmyadmin_conf()
        conf = public.readFile(conf_file["conf_file"])
        rep = conf_file["rep"]
        if conf:
            port = re.search(rep, conf).group(1)
            return {"status":True,"port":port}
        return {"status":False,"port":""}

    # 修改php ssl端口
    def change_phpmyadmin_ssl_port(self,get):
        if public.get_webserver() == "openlitespeed":
            return public.returnMsg(False, 'OpenLiteSpeed 目前尚不支持该操作')
        import re
        try:
            port = int(get.port)
            if 1 > port > 65535:
                return public.returnMsg(False, '端口范围不正确')
        except:
            return public.returnMsg(False, '端口格式不正确')
        for i in ["nginx","apache"]:
            file = "/www/server/panel/vhost/{}/phpmyadmin.conf".format(i)
            conf = public.readFile(file)
            if not conf:
                return public.returnMsg(False,"没有找到{}配置文件，请尝试关闭ssl端口设置后再打开".format(i))
            rulePort = ['80', '443', '21', '20', '8080', '8081', '8089', '11211', '6379']
            if get.port in rulePort:
                return public.returnMsg(False, 'AJAX_PHPMYADMIN_PORT_ERR')
            if i == "nginx":
                if not os.path.exists("/www/server/panel/vhost/apache/phpmyadmin.conf"):
                    return public.returnMsg(False, "没有找到 apache phpmyadmin ssl 配置文件，请尝试关闭ssl端口设置后再打开")
                rep = r"listen\s*([0-9]+)\s*.*;"
                oldPort = re.search(rep, conf)
                if not oldPort:
                    return public.returnMsg(False, '没有检测到 nginx phpmyadmin监听的端口，请确认是否手动修改过文件')
                oldPort = oldPort.groups()[0]
                conf = re.sub(rep, 'listen ' + get.port + ' ssl;', conf)
            else:
                rep = r"Listen\s*([0-9]+)\s*\n"
                oldPort = re.search(rep, conf)
                if not oldPort:
                    return public.returnMsg(False, '没有检测到 apache phpmyadmin监听的端口，请确认是否手动修改过文件')
                oldPort = oldPort.groups()[0]
                conf = re.sub(rep, "Listen " + get.port + "\n", conf, 1)
                rep = r"VirtualHost\s*\*:[0-9]+"
                conf = re.sub(rep, "VirtualHost *:" + get.port, conf, 1)
            if oldPort == get.port: return public.returnMsg(False, 'SOFT_PHPVERSION_ERR_PORT')
            public.writeFile(file, conf)
            public.serviceReload()
            if i=="apache":
                import firewalls
                get.ps = public.getMsg('SOFT_PHPVERSION_PS')
                fw = firewalls.firewalls()
                fw.AddAcceptPort(get)
                public.serviceReload()
                public.WriteLog('TYPE_SOFT', 'SOFT_PHPMYADMIN_PORT', (get.port,))
                get.id = public.M('firewall').where('port=?', (oldPort,)).getField('id')
                get.port = oldPort
                fw.DelAcceptPort(get)
        return public.returnMsg(True, 'SET_PORT_SUCCESS')

    # 设置phpmyadmin ssl
    def set_phpmyadmin_ssl(self,get):
        if public.get_webserver() == "openlitespeed":
            return public.returnMsg(False, 'OpenLiteSpeed 目前尚不支持该操作')
        if not os.path.exists("/www/server/panel/ssl/certificate.pem"):
            return public.returnMsg(False,'面板证书不存在，请申请面板证书后再试')
        if get.v == "1":
        # nginx配置文件
            ssl_conf = """server
    {
        listen 887 ssl;
        server_name phpmyadmin;
        index index.html index.htm index.php;
        root  /www/server/phpmyadmin;
        #SSL-START SSL相关配置，请勿删除或修改下一行带注释的404规则
        #error_page 404/404.html;
        ssl_certificate    /www/server/panel/ssl/certificate.pem;
        ssl_certificate_key    /www/server/panel/ssl/privateKey.pem;
        ssl_protocols TLSv1 TLSv1.1 TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:HIGH:!aNULL:!MD5:!RC4:!DHE;
        ssl_prefer_server_ciphers on;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;
        error_page 497  https://$host$request_uri;
        #SSL-END
        include enable-php.conf;
        location ~ .*\.(gif|jpg|jpeg|png|bmp|swf)$
        {
            expires      30d;
        }
        location ~ .*\.(js|css)?$
        {
            expires      12h;
        }
        location ~ /\.
        {
            deny all;
        }
        access_log  /www/wwwlogs/access.log;
    }"""
            public.writeFile("/www/server/panel/vhost/nginx/phpmyadmin.conf",ssl_conf)
            import panelPlugin
            get.sName = "phpmyadmin"
            v = panelPlugin.panelPlugin().get_soft_find(get)
            public.writeFile("/tmp/2",str(v["ext"]["phpversion"]))
            # apache配置
            ssl_conf = '''Listen 887
<VirtualHost *:887>
    ServerAdmin webmaster@example.com
    DocumentRoot "/www/server/phpmyadmin"
    ServerName 0b842aa5.phpmyadmin
    ServerAlias phpmyadmin.com
    #ErrorLog "/www/wwwlogs/BT_default_error.log"
    #CustomLog "/www/wwwlogs/BT_default_access.log" combined
    
    #SSL
    SSLEngine On
    SSLCertificateFile /www/server/panel/ssl/certificate.pem
    SSLCertificateKeyFile /www/server/panel/ssl/privateKey.pem
    SSLCipherSuite EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH
    SSLProtocol All -SSLv2 -SSLv3
    SSLHonorCipherOrder On
    
    #PHP
    <FilesMatch \.php$>
           SetHandler "proxy:{}"
    </FilesMatch>
    
    #DENY FILES
    <Files ~ (\.user.ini|\.htaccess|\.git|\.svn|\.project|LICENSE|README.md)$>
      Order allow,deny
      Deny from all
    </Files>
    
    #PATH
    <Directory "/www/wwwroot/bt.youbadbad.cn/">
       SetOutputFilter DEFLATE
       Options FollowSymLinks
       AllowOverride All
       Require all granted
       DirectoryIndex index.php index.html index.htm default.php default.html default.htm
    </Directory>
</VirtualHost>'''.format(public.get_php_proxy(v["ext"]["phpversion"],'apache'))
            public.writeFile("/www/server/panel/vhost/apache/phpmyadmin.conf", ssl_conf)
        else:
            if os.path.exists("/www/server/panel/vhost/nginx/phpmyadmin.conf"):
                os.remove("/www/server/panel/vhost/nginx/phpmyadmin.conf")
            if os.path.exists("/www/server/panel/vhost/apache/phpmyadmin.conf"):
                os.remove("/www/server/panel/vhost/apache/phpmyadmin.conf")
            public.serviceReload()
            return public.returnMsg(True, '关闭成功')
        public.serviceReload()
        return public.returnMsg(True,'开启成功，请手动放行phpmyadmin ssl端口')


    #设置PHPMyAdmin
    def setPHPMyAdmin(self,get):
        import re
        #try:
        filename = self.__get_webserver_conffile()
        conf = public.readFile(filename)
        if not conf: return public.returnMsg(False,'ERROR')
        if hasattr(get,'port'):
            mainPort = public.readFile('data/port.pl').strip()
            rulePort = ['80','443','21','20','8080','8081','8089','11211','6379']
            oldPort = "888"
            if get.port in rulePort:
                return public.returnMsg(False,'AJAX_PHPMYADMIN_PORT_ERR')
            if public.get_webserver() == 'nginx':
                rep = r"listen\s+([0-9]+)\s*;"
                oldPort = re.search(rep,conf).groups()[0]
                conf = re.sub(rep,'listen ' + get.port + ';\n',conf)
            elif public.get_webserver() == 'apache':
                rep = r"Listen\s+([0-9]+)\s*\n"
                oldPort = re.search(rep,conf).groups()[0]
                conf = re.sub(rep,"Listen " + get.port + "\n",conf,1)
                rep = r"VirtualHost\s+\*:[0-9]+"
                conf = re.sub(rep,"VirtualHost *:" + get.port,conf,1)
            else:
                filename = '/www/server/panel/vhost/openlitespeed/listen/888.conf'
                conf = public.readFile(filename)
                reg = r"address\s+\*:(\d+)"
                tmp = re.search(reg,conf)
                if tmp:
                    oldPort = tmp.groups(1)
                conf = re.sub(reg,"address *:{}".format(get.port),conf)
            if oldPort == get.port: return public.returnMsg(False,'SOFT_PHPVERSION_ERR_PORT')
            
            public.writeFile(filename,conf)
            import firewalls
            get.ps = public.getMsg('SOFT_PHPVERSION_PS')
            fw = firewalls.firewalls()
            fw.AddAcceptPort(get)
            public.serviceReload()
            public.WriteLog('TYPE_SOFT','SOFT_PHPMYADMIN_PORT',(get.port,))
            get.id = public.M('firewall').where('port=?',(oldPort,)).getField('id')
            get.port = oldPort
            fw.DelAcceptPort(get)
            return public.returnMsg(True,'SET_PORT_SUCCESS')
        
        if hasattr(get,'phpversion'):
            if public.get_webserver() == 'nginx':
                filename = public.GetConfigValue('setup_path') + '/nginx/conf/enable-php.conf'
                conf = public.readFile(filename)
                rep = r"(unix:/tmp/php-cgi.*\.sock|127.0.0.1:\d+)"
                conf = re.sub(rep,public.get_php_proxy(get.phpversion,'nginx'),conf,1)
            elif public.get_webserver() == 'apache':
                rep = r"(unix:/tmp/php-cgi.*\.sock\|fcgi://localhost|fcgi://127.0.0.1:\d+)"
                conf = re.sub(rep,public.get_php_proxy(get.phpversion,'apache'),conf,1)
            else:
                reg = r'/usr/local/lsws/lsphp\d+/bin/lsphp'
                conf = re.sub(reg,'/usr/local/lsws/lsphp{}/bin/lsphp'.format(get.phpversion),conf)
            public.writeFile(filename,conf)
            public.serviceReload()
            public.WriteLog('TYPE_SOFT','SOFT_PHPMYADMIN_PHP',(get.phpversion,))
            return public.returnMsg(True,'SOFT_PHPVERSION_SET')
        
        if hasattr(get,'password'):
            import panelSite
            if(get.password == 'close'):
                return panelSite.panelSite().CloseHasPwd(get)
            else:
                return panelSite.panelSite().SetHasPwd(get)
        
        if hasattr(get,'status'):
            if conf.find(public.GetConfigValue('setup_path') + '/stop') != -1:
                conf = conf.replace(public.GetConfigValue('setup_path') + '/stop',public.GetConfigValue('setup_path') + '/phpmyadmin')
                msg = public.getMsg('START')
            else:
                conf = conf.replace(public.GetConfigValue('setup_path') + '/phpmyadmin',public.GetConfigValue('setup_path') + '/stop')
                msg = public.getMsg('STOP')
            
            public.writeFile(filename,conf)
            public.serviceReload()
            public.WriteLog('TYPE_SOFT','SOFT_PHPMYADMIN_STATUS',(msg,))
            return public.returnMsg(True,'SOFT_PHPMYADMIN_STATUS',(msg,))
        #except:
            #return public.returnMsg(False,'ERROR');
            
    def ToPunycode(self,get):
        import re
        get.domain = get.domain.encode('utf8')
        tmp = get.domain.split('.')
        newdomain = ''
        for dkey in tmp:
                #匹配非ascii字符
                match = re.search(u"[\x80-\xff]+",dkey)
                if not match:
                        newdomain += dkey + '.'
                else:
                        newdomain += 'xn--' + dkey.decode('utf-8').encode('punycode') + '.'

        return newdomain[0:-1]
    
    #保存PHP排序
    def phpSort(self,get):
        if public.writeFile('/www/server/php/sort.pl',get.ssort): return public.returnMsg(True,'SUCCESS')
        return public.returnMsg(False,'ERROR')
    
    #获取广告代码
    def GetAd(self,get):
        try:
            return public.HttpGet(public.GetConfigValue('home') + '/Api/GetAD?name='+get.name + '&soc=' + get.soc)
        except:
            return ''
        
    #获取进度
    def GetSpeed(self,get):
        return public.getSpeed()
    
    #检查登陆状态
    def CheckLogin(self,get):
        return True
    
    #获取警告标识
    def GetWarning(self,get):
        warningFile = 'data/warning.json'
        if not os.path.exists(warningFile): return public.returnMsg(False,'AJAX_WARNING_ERR')
        import json,time;
        wlist = json.loads(public.readFile(warningFile))
        wlist['time'] = int(time.time())
        return wlist
    
    #设置警告标识
    def SetWarning(self,get):
        wlist = self.GetWarning(get)
        id = int(get.id)
        import time,json;
        for i in xrange(len(wlist['data'])):
            if wlist['data'][i]['id'] == id:
                wlist['data'][i]['ignore_count'] += 1
                wlist['data'][i]['ignore_time'] = int(time.time())
        
        warningFile = 'data/warning.json'
        public.writeFile(warningFile,json.dumps(wlist))
        return public.returnMsg(True,'SET_SUCCESS')
    
    #获取memcached状态
    def GetMemcachedStatus(self,get):
        import telnetlib,re;
        conf = public.readFile('/etc/init.d/memcached')
        result = {}
        result['bind'] = re.search('IP=(.+)',conf).groups()[0]
        result['port'] = int(re.search('PORT=(\d+)',conf).groups()[0])
        result['maxconn'] = int(re.search('MAXCONN=(\d+)',conf).groups()[0])
        result['cachesize'] = int(re.search('CACHESIZE=(\d+)',conf).groups()[0])
        tn = telnetlib.Telnet(result['bind'],result['port'])
        tn.write(b"stats\n")
        tn.write(b"quit\n")
        data = tn.read_all()
        if type(data) == bytes: data = data.decode('utf-8')
        data = data.replace('STAT','').replace('END','').split("\n")
        res = ['cmd_get','get_hits','get_misses','limit_maxbytes','curr_items','bytes','evictions','limit_maxbytes','bytes_written','bytes_read','curr_connections'];
        for d in data:
            if len(d)<3: continue
            t = d.split()
            if not t[0] in res: continue
            result[t[0]] = int(t[1])
        result['hit'] = 1
        if result['get_hits'] > 0 and result['cmd_get'] > 0:
            result['hit'] = float(result['get_hits']) / float(result['cmd_get']) * 100

        return result
    
    #设置memcached缓存大小
    def SetMemcachedCache(self,get):
        import re
        confFile = '/etc/init.d/memcached'
        conf = public.readFile(confFile)
        conf = re.sub('IP=.+','IP='+get.ip,conf)
        conf = re.sub('PORT=\d+','PORT='+get.port,conf)
        conf = re.sub('MAXCONN=\d+','MAXCONN='+get.maxconn,conf)
        conf = re.sub('CACHESIZE=\d+','CACHESIZE='+get.cachesize,conf)
        public.writeFile(confFile,conf)
        public.ExecShell(confFile + ' reload')
        return public.returnMsg(True,'SET_SUCCESS')
    
    #取redis状态
    def GetRedisStatus(self,get):
        import re
        c = public.readFile('/www/server/redis/redis.conf')
        port = re.findall('\n\s*port\s+(\d+)',c)[0]
        password = re.findall('\n\s*requirepass\s+(.+)',c)
        if password: 
            password = ' -a ' + password[0]
        else:
            password = ''
        data = public.ExecShell('/www/server/redis/src/redis-cli -p ' + port + password + ' info')[0];
        res = [
               'tcp_port',
               'uptime_in_days',    #已运行天数
               'connected_clients', #连接的客户端数量
               'used_memory',       #Redis已分配的内存总量
               'used_memory_rss',   #Redis占用的系统内存总量
               'used_memory_peak',  #Redis所用内存的高峰值
               'mem_fragmentation_ratio',   #内存碎片比率
               'total_connections_received',#运行以来连接过的客户端的总数量
               'total_commands_processed',  #运行以来执行过的命令的总数量
               'instantaneous_ops_per_sec', #服务器每秒钟执行的命令数量
               'keyspace_hits',             #查找数据库键成功的次数
               'keyspace_misses',           #查找数据库键失败的次数
               'latest_fork_usec'           #最近一次 fork() 操作耗费的毫秒数
               ]
        data = data.split("\n")
        result = {}
        for d in data:
            if len(d)<3: continue
            t = d.strip().split(':')
            if not t[0] in res: continue
            result[t[0]] = t[1]
        return result
    
    #取PHP-FPM日志
    def GetFpmLogs(self,get):
        import re
        fpm_path = '/www/server/php/' + get.version + '/etc/php-fpm.conf'
        if not os.path.exists(fpm_path): return public.returnMsg(False,'AJAX_LOG_FILR_NOT_EXISTS')
        fpm_conf = public.readFile(fpm_path)
        log_tmp = re.findall(r"error_log\s*=\s*(.+)",fpm_conf)
        if not log_tmp: return public.returnMsg(False,'AJAX_LOG_FILR_NOT_EXISTS')
        log_file = log_tmp[0].strip()
        if log_file.find('var/log') == 0:
            log_file = '/www/server/php/' +get.version + '/'+ log_file
        return public.returnMsg(True,public.GetNumLines(log_file,1000))
    
    #取PHP慢日志
    def GetFpmSlowLogs(self,get):
        import re
        fpm_path = '/www/server/php/' + get.version + '/etc/php-fpm.conf'
        if not os.path.exists(fpm_path): return public.returnMsg(False,'AJAX_LOG_FILR_NOT_EXISTS')
        fpm_conf = public.readFile(fpm_path)
        log_tmp = re.findall(r"slowlog\s*=\s*(.+)",fpm_conf)
        if not log_tmp: return public.returnMsg(False,'AJAX_LOG_FILR_NOT_EXISTS')
        log_file = log_tmp[0].strip()
        if log_file.find('var/log') == 0:
            log_file = '/www/server/php/' +get.version + '/'+ log_file
        return public.returnMsg(True,public.GetNumLines(log_file,1000))
    
    #取指定日志
    def GetOpeLogs(self,get):
        if not os.path.exists(get.path): return public.returnMsg(False,'AJAX_LOG_FILR_NOT_EXISTS')
        return public.returnMsg(True,public.GetNumLines(get.path,1000))
    
    #检查用户绑定是否正确
    def check_user_auth(self,get):
        m_key = 'check_user_auth'
        if m_key in session: return session[m_key]
        u_path = 'data/userInfo.json'
        try:
            userInfo = json.loads(public.ReadFile(u_path))
        except: 
            if os.path.exists(u_path): os.remove(u_path)
            return public.returnMsg(False,'宝塔帐户绑定已失效，请在[设置]页面重新绑定!')
        pdata = {'access_key':userInfo['access_key'],'secret_key':userInfo['secret_key']}
        result = public.HttpPost(public.GetConfigValue('home') + '/api/panel/check_auth_key',pdata,3)
        if result == '0': 
            if os.path.exists(u_path): os.remove(u_path)
            return public.returnMsg(False,'宝塔帐户绑定已失效，请在[设置]页面重新绑定!')
        if result == '1':
            session[m_key] = public.returnMsg(True,'绑定有效!')
            return session[m_key]
        return public.returnMsg(True,result)


    #PHP探针
    def php_info(self,args):
        php_version = args.php_version.replace('.','')
        php_path = '/www/server/php/'
        if public.get_webserver() == 'openlitespeed':
            php_path = '/usr/local/lsws/lsphp'
        php_bin = php_path + php_version + '/bin/php'
        php_ini = php_path + php_version + '/etc/php.ini'
        if not os.path.exists('/etc/redhat-release'):
            php_ini = php_path + php_version + '/etc/php/'+args.php_version+'/litespeed/php.ini'
        tmp = public.ExecShell(php_bin + ' /www/server/panel/class/php_info.php')[0]
        result = json.loads(tmp)
        result['phpinfo'] = {}
        result['phpinfo']['php_version'] = result['php_version']
        result['phpinfo']['php_path'] = php_path
        result['phpinfo']['php_bin'] = php_bin
        result['phpinfo']['php_ini'] = php_ini
        result['phpinfo']['modules'] = ' '.join(result['modules'])
        result['phpinfo']['ini'] = result['ini']
        result['phpinfo']['keys'] = { "1cache": "缓存器", "2crypt": "加密解密库", "0db": "数据库驱动", "4network": "网络通信库", "5io_string": "文件和字符串处理库", "3photo":"图片处理库","6other":"其它第三方库"}
        del(result['php_version'])
        del(result['modules'])
        del(result['ini'])
        return result

    #取指定行
    def get_lines(self,args):
        if not os.path.exists(args.filename): return public.returnMsg(False,'指定日志文件不存在!')
        s_body = public.ExecShell("tail -n {} {}".format(args.num,args.filename))[0]
        return public.returnMsg(True,s_body)
        
        