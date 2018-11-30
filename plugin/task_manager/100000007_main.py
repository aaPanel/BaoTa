#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 x3
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   宝塔任务管理器
#+--------------------------------------------------------------------
import sys
sys.path.append('class/');
import psutil,pwd,json,os,time,public,operator

class task_manager_main:
    Pids = None;
    __cpu_time = None;
    new_info = {};
    old_info = {};
    new_net_info = {};
    old_net_info = {};
    old_path = '/tmp/bt_task_old.json';
    old_net_path = '/tmp/bt_network_old.json'
    panel_pid = None
    task_pid = None
    
    def get_network_list(self,get):
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
        networkList = sorted(networkList, key=lambda x : x['status'], reverse=True);
        data = {}
        data['list'] = networkList
        data['state'] = self.get_network()
        return data;
    
    
    def get_network(self):
        #try:
        self.get_net_old();
        networkIo = psutil.net_io_counters()[:4]
        self.new_net_info['upTotal'] = networkIo[0]
        self.new_net_info['downTotal'] = networkIo[1]
        self.new_net_info['upPackets'] = networkIo[2]
        self.new_net_info['downPackets'] = networkIo[3]
        self.new_net_info['time'] = time.time()
        
        if not self.old_net_info: self.old_net_info = {}
        if not 'upTotal' in self.old_net_info:
            time.sleep(0.1);
            networkIo = psutil.net_io_counters()[:4]
            self.old_net_info['upTotal'] = networkIo[0]
            self.old_net_info['downTotal'] = networkIo[1]
            self.old_net_info['upPackets'] = networkIo[2]
            self.old_net_info['downPackets'] = networkIo[3]
            self.old_net_info['time'] = time.time()
            
        s = self.new_net_info['time'] - self.old_net_info['time'];
        networkInfo = {}
        networkInfo['upTotal']   = networkIo[0]
        networkInfo['downTotal'] = networkIo[1]
        networkInfo['up']        = round((float(networkIo[0]) - self.old_net_info['upTotal']) / s,2)
        networkInfo['down']      = round((float(networkIo[1]) - self.old_net_info['downTotal']) / s,2)
        networkInfo['downPackets'] =networkIo[3]
        networkInfo['upPackets']   =networkIo[2]
        networkInfo['downPackets_s'] = int((networkIo[3] - self.old_net_info['downPackets']) / s)
        networkInfo['upPackets_s']   = int((networkIo[2] - self.old_net_info['upPackets']) / s)
        public.writeFile(self.old_net_path,json.dumps(self.new_net_info))
        return networkInfo
        #except:
            #return None
    
    def get_user_list(self,get):
        tmpList = public.readFile('/etc/passwd').split("\n");
        userList = [];
        self.groupList = self.get_group_list(get);
        for ul in tmpList:
            tmp = ul.split(':');
            if len(tmp) < 6: continue;
            userInfo = {}
            userInfo['username'] = tmp[0];
            userInfo['uid'] = tmp[2];
            userInfo['gid'] = tmp[3];
            userInfo['group'] = self.get_group_name(tmp[3]);
            userInfo['ps'] = self.get_user_ps(tmp[0],tmp[4]);
            userInfo['home'] = tmp[5];
            userInfo['login_shell'] = tmp[6];
            userList.append(userInfo);
        return userList;
    
    def get_user_ps(self,name,ps):
        userPs = {'www':'宝塔面板','root':'超级管理员','mysql':'用于运行MySQL的用户','mongo':'用于运行MongoDB的用户',
                  'git':'git用户','mail':'mail','nginx':'第三方nginx用户','postfix':'postfix邮局用户','lp':'打印服务帐号',
                  'daemon':'控制后台进程的系统帐号','nobody':'匿名帐户','bin':'管理大部分命令的帐号','adm':'管理某些管理文件的帐号','smtp':'smtp邮件'}
        if name in userPs: return userPs[name];
        if not ps: return name;
        return ps;
    
    def remove_user(self,get):
        users = ['www','root','mysql','shutdown','postfix','smmsp','sshd','systemd-network','systemd-bus-proxy','avahi-autoipd','mail','sync','lp','adm','bin','mailnull','ntp','daemon','sys'];
        if get.user in users: return public.returnMsg(False,'不能删除系统和环境关键用户!');
        r = public.ExecShell("userdel " + get.user);
        if r[1].find('process') != -1:
            try:
                pid = r[1].split()[-1]
                p = psutil.Process(int(pid))
                pname = p.name();
                p.kill()
                public.ExecShell("pkill -9 " + pname)
                r = public.ExecShell("userdel " + get.user);
            except:pass
        if r[1].find('userdel:') != -1: return public.returnMsg(False,r[1]); 
        return public.returnMsg(True,'删除成功!');
    
    def get_group_name(self,gid):
        for g in self.groupList:
            if g['gid'] == gid: return g['group'];
        return '';
    
    def get_group_list(self,get):
        tmpList = public.readFile('/etc/group').split("\n");
        groupList = []
        for gl in tmpList:
            tmp = gl.split(':');
            if len(tmp) < 3: continue;
            groupInfo = {}
            groupInfo['group'] = tmp[0];
            groupInfo['gid'] = tmp[2];
            groupList.append(groupInfo);
        return groupList; 
    
    def get_service_list(self,get):
        init_d = '/etc/init.d/'
        serviceList = []
        for sname in os.listdir(init_d):
            if str(oct(os.stat(init_d + sname).st_mode)[-3:]) == '644': continue;
            serviceInfo = {}
            runlevels = self.get_runlevel(sname)
            serviceInfo['name'] = sname
            serviceInfo['runlevel_0'] = runlevels[0]
            serviceInfo['runlevel_1'] = runlevels[1]
            serviceInfo['runlevel_2'] = runlevels[2]
            serviceInfo['runlevel_3'] = runlevels[3]
            serviceInfo['runlevel_4'] = runlevels[4]
            serviceInfo['runlevel_5'] = runlevels[5]
            serviceInfo['runlevel_6'] = runlevels[6]
            serviceInfo['ps'] = self.get_run_ps(sname)
            serviceList.append(serviceInfo)
        
        data = {}
        data['runlevel'] = public.ExecShell('runlevel')[0].split()[1]
        data['serviceList'] = sorted(serviceList, key=lambda x : x['name'], reverse=False);
        data['serviceList'] = self.get_systemctl_list(data['serviceList'],data['runlevel']);
        return data
    
    def get_systemctl_list(self,serviceList,runlevel):
        systemctl_user_path = '/usr/lib/systemd/system/'
        systemctl_run_path = '/etc/systemd/system/multi-user.target.wants/'
        if not os.path.exists(systemctl_user_path) or not os.path.exists(systemctl_run_path): return serviceList;
        r = '.service'
        for d in os.listdir(systemctl_user_path):
            if d.find(r) == -1: continue;
            if not self.cont_systemctl(d): continue;
            isrun = '<span style="color:red;" title="点击开启">关闭</span>'
            serviceInfo = {}
            serviceInfo['name'] = d.replace(r,'')
            serviceInfo['runlevel_0'] = isrun
            serviceInfo['runlevel_1'] = isrun
            serviceInfo['runlevel_2'] = isrun
            serviceInfo['runlevel_3'] = isrun
            serviceInfo['runlevel_4'] = isrun
            serviceInfo['runlevel_5'] = isrun
            serviceInfo['runlevel_6'] = isrun
            if os.path.exists(systemctl_run_path + d): 
                isrun = '<span style="color:green;" title="点击关闭">开启</span>'
                serviceInfo['runlevel_' + runlevel] = isrun;
                serviceInfo['runlevel_3'] = isrun;
                serviceInfo['runlevel_5'] = isrun;
                
            serviceInfo['ps'] = self.get_run_ps(serviceInfo['name'])
            serviceList.append(serviceInfo)
        #serviceList = sorted(serviceList, key=lambda x : x['name'], reverse=False);
        return serviceList
    
    def cont_systemctl(self,name):
        conts = ['systemd','rhel','plymouth','rc-','@','init','ipr','dbus','-local']
        for c in conts:
            if name.find(c) != -1: return False
        return True
    
    def set_runlevel_state(self,get):
        if get.runlevel == '0' or get.runlevel == '6': return public.returnMsg(False,'为安全考虑,不能通过面板直接修改此运行级别');
        systemctl_user_path = '/usr/lib/systemd/system/'
        systemctl_run_path = '/etc/systemd/system/multi-user.target.wants/'
        if os.path.exists(systemctl_user_path + get.serviceName + '.service'): 
            runlevel = public.ExecShell('runlevel')[0].split()[1]
            if get.runlevel != runlevel: return public.returnMsg(False,'Systemctl托管的服务不能设置非当前运行级别的状态');
            action = 'enable';
            if os.path.exists(systemctl_run_path + get.serviceName + '.service'): action = 'disable';
            public.ExecShell('systemctl ' + action + ' ' + get.serviceName + '.service');
            return public.returnMsg(True,'设置成功!');
            
        rc_d = '/etc/rc' + get.runlevel + '.d/';
        import shutil;
        for d in os.listdir(rc_d):
            if d[3:] != get.serviceName: continue;
            sfile = rc_d + d;
            c = 'S';
            if d[:1] == 'S': c = 'K';
            dfile = rc_d + c + d[1:];
            shutil.move(sfile, dfile);
            return public.returnMsg(True,'设置成功!');
        return public.returnMsg(False,'设置失败!');
    
    def get_runlevel(self,name):
        rc_d = '/etc/'
        runlevels = []
        for i in range(7):
            isrun = '<span style="color:red;" title="点击开启">关闭</span>'
            for d in os.listdir(rc_d + 'rc' + str(i) + '.d'):
                if d[3:] == name:
                    if d[:1] == 'S': isrun = '<span style="color:green;" title="点击关闭">开启</span>'
            runlevels.append(isrun)
        return runlevels
    
    def remove_service(self,get):
        if get.serviceName == 'bt': return public.returnMsg(False,'不能通过面板结束宝塔面板服务!');
        systemctl_user_path = '/usr/lib/systemd/system/'
        if os.path.exists(systemctl_user_path + get.serviceName + '.service'):  return public.returnMsg(False,'Systemctl托管的服务不能通过面板删除');
        public.ExecShell('service ' + get.serviceName + ' stop');
        if os.path.exists('/usr/sbin/update-rc.d'):
            public.ExecShell('update-rc.d '+get.serviceName+' remove');
        elif os.path.exists('/usr/sbin/chkconfig'):
            public.ExecShell('chkconfig --del ' + get.serviceName);
        else:
            public.ExecShell("rm -f /etc/rc0.d/*" + get.serviceName);
            public.ExecShell("rm -f /etc/rc1.d/*" + get.serviceName);
            public.ExecShell("rm -f /etc/rc2.d/*" + get.serviceName);
            public.ExecShell("rm -f /etc/rc3.d/*" + get.serviceName);
            public.ExecShell("rm -f /etc/rc4.d/*" + get.serviceName);
            public.ExecShell("rm -f /etc/rc5.d/*" + get.serviceName);
            public.ExecShell("rm -f /etc/rc6.d/*" + get.serviceName);
        filename = '/etc/init.d/' + get.serviceName;
        if os.path.exists(filename): os.remove(filename);
        return public.returnMsg(True,'删除成功!');
    
    def kill_process(self,get):
        pid = int(get.pid)
        if pid < 30: return public.returnMsg(False,'不能结束系统关键进程!');
        if not pid in psutil.pids(): return public.returnMsg(False,'指定进程不存在!');
        if not 'killall' in get:
            p = psutil.Process(pid)
            if self.is_panel_process(pid): return public.returnMsg(False,'不能结束面板服务进程');
            p.kill()
            return public.returnMsg(True,'进程已结束');
        return self.kill_process_all(pid)
    
    def kill_process_all(self,pid):
        if pid < 30: return public.returnMsg(True,'已结束此进程树!');
        if self.is_panel_process(pid): return public.returnMsg(False,'不能结束面板服务进程');
        try:
            if not pid in psutil.pids(): public.returnMsg(True,'已结束此进程树!');
            p = psutil.Process(pid)
            ppid = p.ppid()
            name = p.name()
            p.kill()
            public.ExecShell('pkill -9 ' + name);
            if name.find('php-') != -1:
                public.ExecShell("rm -f /tmp/php-cgi-*.sock");
            elif name.find('mysql') != -1:
                public.ExecShell("rm -f /tmp/mysql.sock");
            elif name.find('nginx') != -1:
                public.ExecShell("rm -f /tmp/mysql.sock");
            self.kill_process_lower(pid)
            if ppid: return self.kill_process_all(ppid);
        except:pass
        return public.returnMsg(True,'已结束此进程树!');
    
    def kill_process_lower(self,pid):
        pids = psutil.pids();
        for lpid in pids:
            if lpid < 30: continue;
            if self.is_panel_process(lpid): continue;
            p = psutil.Process(lpid);
            ppid = p.ppid()
            if ppid == pid:
                p.kill()
                return self.kill_process_lower(lpid)
        return True;
    
    def is_panel_process(self,pid):
        if not self.panel_pid:
            self.panel_pid = int(public.ExecShell("ps aux | grep 'python main.py'|head -n1|awk '{print $2}'")[0])
        if pid == self.panel_pid: return True
        if not self.task_pid:
            self.task_pid = int(public.ExecShell("ps aux | grep 'python task.py'|head -n1|awk '{print $2}'")[0])
        if pid == self.task_pid: return True
        return False;
    
    def pkill_session(self,get):
        public.ExecShell("pkill -kill -t " + get.pts);
        return public.returnMsg(True,'已强行结束会话['+get.pts+']');
    
    def get_run_list(self,get):
        runFile = ['/etc/rc.local','/etc/profile','/etc/inittab','/etc/rc.sysinit'];
        runList = []
        for rfile in runFile:
            if not os.path.exists(rfile): continue;
            bodyR = self.clear_comments(public.readFile(rfile))
            if not bodyR: continue
            stat = os.stat(rfile)
            accept = str(oct(stat.st_mode)[-3:]);
            if accept == '644': continue
            tmp = {}
            tmp['name'] = rfile
            tmp['srcfile'] = rfile
            tmp['size'] = os.path.getsize(rfile)
            tmp['access'] = accept
            tmp['ps'] = self.get_run_ps(rfile)
            #tmp['body'] = bodyR
            runList.append(tmp)
        
        runlevel = public.ExecShell('runlevel')[0].split()[1]
        runPath = ['/etc/init.d','/etc/rc' + runlevel + '.d'];
        tmpAll = []
        islevel = False;
        for rpath in runPath:
            if not os.path.exists(rpath): continue;
            if runPath[1] == rpath: islevel = True;
            for f in os.listdir(rpath):
                if f[:1] != 'S': continue;
                filename = rpath + '/' + f;
                if not os.path.exists(filename): continue;
                if os.path.isdir(filename): continue;
                if os.path.islink(filename):
                    flink = os.readlink(filename).replace('../','/etc/');
                    if not os.path.exists(flink): continue;
                    filename = flink;
                tmp = {};
                tmp['name'] = f;
                if islevel: tmp['name'] = f[3:];
                if tmp['name'] in tmpAll: continue;
                stat = os.stat(filename);
                accept = str(oct(stat.st_mode)[-3:]);
                if accept == '644': continue;
                tmp['srcfile'] = filename;
                tmp['access'] = accept;
                tmp['size'] = os.path.getsize(filename);
                tmp['ps'] = self.get_run_ps(tmp['name']);
                runList.append(tmp);
                tmpAll.append(tmp['name']);
        data = {}
        data['run_list'] = runList
        data['run_level'] = runlevel;
        return data;
    
    def get_run_ps(self,name):
        runPs = {'netconsole':'网络控制台日志','network':'网络服务','jexec':'JAVA','tomcat8':'Apache Tomcat','tomcat7':'Apache Tomcat','mariadb':'Mariadb',
                 'tomcat9':'Apache Tomcat','tomcat':'Apache Tomcat','memcached':'Memcached缓存器','php-fpm-53':'PHP-5.3','php-fpm-52':'PHP-5.2',
                 'php-fpm-54':'PHP-5.4','php-fpm-55':'PHP-5.5','php-fpm-56':'PHP-5.6','php-fpm-70':'PHP-7.0','php-fpm-71':'PHP-7.1',
                 'php-fpm-72':'PHP-7.2','rsync_inotify':'rsync实时同步','pure-ftpd':'FTP服务','mongodb':'MongoDB','nginx':'Web服务器(Nginx)',
                 'httpd':'Web服务器(Apache)','bt':'宝塔面板','mysqld':'MySQL数据库','rsynd':'rsync主服务','php-fpm':'PHP服务','systemd':'系统核心服务',
                 '/etc/rc.local':'用户自定义启动脚本','/etc/profile':'全局用户环境变量','/etc/inittab':'用于自定义系统运行级别','/etc/rc.sysinit':'系统初始化时调用的脚本',
                 'sshd':'SSH服务','crond':'计划任务服务','udev-post':'设备管理系统','auditd':'审核守护进程','rsyslog':'rsyslog服务','sendmail':'邮件发送服务','blk-availability':'lvm2相关',
                 'local':'用户自定义启动脚本','netfs':'网络文件系统','lvm2-monitor':'lvm2相关','xensystem':'xen云平台相关','iptables':'iptables防火墙','ip6tables':'iptables防火墙 for IPv6','firewalld':'firewall防火墙'}
        if name in runPs: return runPs[name]
        return name;
    
    def clear_comments(self,body):
        bodyTmp = body.split("\n");
        bodyR = ""
        for tmp in bodyTmp:
            if tmp.startswith('#'): continue;
            if tmp.strip() == '': continue;
            bodyR += tmp;
        return bodyR
    
    def get_file_body(self,get):
        get.path = get.path.encode('utf-8');
        if not os.path.exists(get.path): return public.returnMsg(False,'FILE_NOT_EXISTS')
        if os.path.getsize(get.path) > 2097152: return public.returnMsg(False,'不能在线获取大于2MB的文件内容!');
        return self.clear_comments(public.readFile(get.path))
    
    def get_cron_list(self,get):
        filename = self.get_cron_file();
        tmpList = public.readFile(filename).split("\n");
        cronList = []
        for c in tmpList:
            c = c.strip();
            if c.startswith('#'): continue;
            tmp = c.split(' ')
            if len(tmp) < 6: continue;
            cronInfo = {}
            cronInfo['cycle'] = self.decode_cron_cycle(tmp)
            if not cronInfo['cycle']: continue
            ctmp = self.decode_cron_connand(tmp)
            cronInfo['command'] = c
            cronInfo['ps'] = ctmp[1]
            cronInfo['exe'] = ctmp[2]
            cronInfo['test'] = ctmp[0]
            cronList.append(cronInfo)
        return cronList
    
    def remove_cron(self,get):
        index = int(get.index);
        cronList = self.get_cron_list(get);
        if index > len(cronList) + 1: return public.returnMsg(False,'指定任务不存在!');
        toCron = []
        for i in range(len(cronList)):
            if i == index: continue
            toCron.append(cronList[i]['command']);
        cronStr = "\n".join(toCron) + "\n\n"
        filename = self.get_cron_file();
        public.writeFile(filename,cronStr);
        public.ExecShell("chmod 600 " + filename);
        self.CrondReload();
        return public.returnMsg(True,'删除成功!');
    
    def CrondReload(self):
        if os.path.exists('/etc/init.d/crond'): 
            public.ExecShell('/etc/init.d/crond reload')
        elif os.path.exists('/etc/init.d/cron'):
            public.ExecShell('service cron restart')
        else:
            public.ExecShell("systemctl reload crond")
            
    def decode_cron_connand(self,tmp):
        command = ''
        for i in range(len(tmp)):
            if i < 5: continue;
            command += tmp[i] + ' '
        ps = '未知任务'
        if command.find('/www/server/cron') != -1: 
            ps = '通过宝塔面板添加的计划任务';
        elif command.find('.acme.sh') != -1: 
            ps = '基于acme.sh的Let\'s Encrypt证书续签任务';
        elif command.find('certbot-auto renew') != -1:
            ps = '基于certbot的Let\'s Encrypt证书续签任务';
        
        tmpScript = command.split('>')[0].strip()
        filename = tmpScript.replace('"','').split()[0]
        #if not os.path.exists(filename): filename = '';
        return command.strip(),ps,filename;
    
    def decode_cron_cycle(self,tmp):
        if tmp[4] != '*':
            cycle = '每周' + self.toWeek(int(tmp[4])) + '的' + tmp[1] + '时' + tmp[0] + '分';
        elif tmp[2] != '*':
            if tmp[2].find('*') == -1:
                cycle = '每月的' + tmp[2] + '日,' + tmp[1] + '时' + tmp[0] + '分';
            else:
                cycle = '每隔' + tmp[2].split('/')[1] + '天' + tmp[1] + '时' + tmp[0] + '分';
        elif tmp[1] != '*':
            if tmp[1].find('*') == -1:
                cycle = '每天的' + tmp[1] + '时' + tmp[0] + '分';
            else:
                cycle = '每隔' + tmp[1].split('/')[1] + '小时'+ tmp[0] + '分钟';
        elif tmp[0] != '*':
            if tmp[0].find('*') == -1:
                cycle = '每小时的第' + tmp[0] + '分钟';
            else:
                cycle = '每隔' + tmp[0].split('/')[1] + '分钟';
        else: return None
        return cycle
            
            
    def toWeek(self,num):
        if num > 6: return '';
        wheres={
                0   :   public.getMsg('CRONTAB_SUNDAY'),
                1   :   public.getMsg('CRONTAB_MONDAY'),
                2   :   public.getMsg('CRONTAB_TUESDAY'),
                3   :   public.getMsg('CRONTAB_WEDNESDAY'),
                4   :   public.getMsg('CRONTAB_THURSDAY'),
                5   :   public.getMsg('CRONTAB_FRIDAY'),
                6   :   public.getMsg('CRONTAB_SATURDAY')
                }
        
        return wheres[num]
    
    def get_cron_file(self):
        filename = '/var/spool/cron/crontabs/root'
        if os.path.exists(filename): return filename
        return '/var/spool/cron/root';
    
    def get_exp_user(self,get):
        exp = {}
        exp['bash_profile'] = self.clear_comments(public.readFile('/root/.bash_profile'))
        exp['bash_logout'] = self.clear_comments(public.readFile('/root/.bash_logout'))
        return exp;
    
    def get_who(self,get):
        whoTmp = public.ExecShell('who')[0]
        tmpList = whoTmp.split("\n")
        whoList = []
        for w in tmpList:
            tmp = w.split()
            if len(tmp) < 5: continue;
            whoInfo = {}
            whoInfo['user'] = tmp[0]
            whoInfo['pts'] = tmp[1]
            whoInfo['date'] = tmp[2] + ' ' + tmp[3]
            whoInfo['ip'] = tmp[4].replace('(','').replace(')','')
            if len(tmp) > 5:
                whoInfo['date'] = tmp[2] + ' ' + tmp[3] + ' ' + tmp[4]
                whoInfo['ip'] = tmp[5].replace('(','').replace(')','')
            whoList.append(whoInfo)
        return whoList;
            
    def get_process_list(self,get):
        self.Pids = psutil.pids();
        processList = []
        if type(self.new_info) != dict: self.new_info = {}
        self.new_info['cpu_time'] = self.get_cpu_time();
        self.new_info['time'] = time.time();
        
        if not 'sortx' in get: get.sortx = 'cpu_percent';
        info = {}
        info['activity'] = 0;
        info['cpu'] = 0.00;
        info['mem'] = 0;
        info['disk'] = 0;
        status_ps = {'sleeping':'睡眠','running':'活动'}
        for pid in self.Pids:
            tmp = {}
            try:
                p = psutil.Process(pid);
            except:continue;
            with p.oneshot():
                p_mem = p.memory_full_info()
                if p_mem.uss + p_mem.rss + p_mem.pss + p_mem.data == 0: continue;
                pio = p.io_counters()
                p_cpus= p.cpu_times()
                p_state = p.status()
                if p_state == 'running': info['activity'] += 1;
                if p_state in status_ps: p_state = status_ps[p_state];
                tmp['exe'] = p.exe();
                tmp['name'] = p.name();                             
                tmp['pid'] = pid;                                   
                tmp['ppid'] = p.ppid()                              
                tmp['create_time'] = int(p.create_time())          
                tmp['status'] = p_state;                         
                tmp['user'] = p.username();                         
                tmp['memory_used'] = p_mem.uss                      
                tmp['cpu_percent'] = self.get_cpu_percent(str(pid),p_cpus,self.new_info['cpu_time']);
                tmp['io_write_bytes'] = pio.write_bytes;            
                tmp['io_read_bytes'] = pio.read_bytes;              
                tmp['io_write_speed'] = self.get_io_write(str(pid),pio.write_bytes)            
                tmp['io_read_speed'] = self.get_io_read(str(pid),pio.read_bytes)               
                tmp['connects'] = self.get_connects(pid)            
                tmp['threads'] = p.num_threads()                   
                tmp['ps'] = self.get_process_ps(tmp['name'],pid)       
                if tmp['cpu_percent'] > 100: tmp['cpu_percent'] = 0.1;
                info['cpu'] += tmp['cpu_percent'];
                info['disk'] += tmp['io_write_speed'] + tmp['io_read_speed'];
            processList.append(tmp);
            del(p)
            del(tmp)
        public.writeFile(self.old_path,json.dumps(self.new_info));
        res = True
        if get.sortx == 'status': res = False
        processList = sorted(processList, key=lambda x : x[get.sortx], reverse=res);
        info['load_average'] = self.get_load_average();
        data = {}
        data['process_list'] = processList;
        info['cpu'] = round(info['cpu'],2);
        info['mem'] = self.get_mem_info();
        data['info'] = info;
        return data
    
    def get_mem_info(self,get=None):
        mem = psutil.virtual_memory()
        memInfo = {'memTotal':mem.total,'memFree':mem.free,'memBuffers':mem.buffers,'memCached':mem.cached}
        memInfo['memRealUsed'] = memInfo['memTotal'] - memInfo['memFree'] - memInfo['memBuffers'] - memInfo['memCached']
        return memInfo['memRealUsed']
    
    def get_process_ps(self,name,pid):
        processPs = {'mysqld':'MySQL服务','php-fpm':'PHP子进程','php-cgi':'PHP-CGI进程',
                     'nginx':'Nginx服务','httpd':'Apache服务','sshd':'SSH服务','pure-ftpd':'FTP服务',
                     'sftp-server':'SFTP服务','mysqld_safe':'MySQL服务','firewalld':'防火墙服务',
                     'NetworkManager':'网络管理服务','svlogd':'日志守护进程','memcached':'Memcached缓存器'}
        if name in processPs: return processPs[name];
        if name == 'python':
            if self.is_panel_process(pid): return '宝塔面板';
        return name;
    
    
    def get_load_average(self):
        b = public.ExecShell("uptime")[0].replace(',','');
        c = b.split();
        data = {};
        data['1'] = float(c[-3]);
        data['5'] = float(c[-2]);
        data['15'] = float(c[-1]);
        return data;
    
    
    def get_process_info(self,get):
        pid = int(get.pid)
        p = psutil.Process(pid);
        processInfo = {}
        p_mem = self.object_to_dict(p.memory_full_info())
        pio = p.io_counters()
        p_cpus= p.cpu_times()
        processInfo['exe'] = p.exe();
        processInfo['name'] = p.name();                             
        processInfo['pid'] = pid;                                  
        processInfo['ppid'] = p.ppid()                              
        processInfo['pname'] = 'sys';
        if processInfo['ppid'] != 0: processInfo['pname'] = psutil.Process(processInfo['ppid']).name()  
        processInfo['comline'] = p.cmdline()                       
        processInfo['create_time'] = int(p.create_time())          
        processInfo['open_files'] = self.list_to_dict(p.open_files())       
        processInfo['status'] = p.status();                       
        processInfo['user'] = p.username();                         
        processInfo['memory_full'] = p_mem                          
        processInfo['io_write_bytes'] = pio.write_bytes;           
        processInfo['io_read_bytes'] = pio.read_bytes;              
        processInfo['connects'] = self.get_connects(pid)           
        processInfo['threads'] = p.num_threads()                    
        processInfo['ps'] = self.get_process_ps(processInfo['name'],pid)       
            
        return processInfo
    
    
    def get_connects(self,pid):
        connects = 0;
        try:
            if pid == 1: return connects
            tp = '/proc/' + str(pid) + '/fd/';
            if not os.path.exists(tp): return connects;
            for d in os.listdir(tp):
                fname = tp + d
                if os.path.islink(fname):
                    l = os.readlink(fname)
                    if l.find('socket:') != -1: connects += 1
        except:pass
        return connects;
    
    
    def get_io_write(self,pid,io_write):
        self.get_old();
        disk_io_write = 0
        if not self.old_info: self.old_info = {}
        if not pid in self.old_info:
            self.new_info[pid]['io_write'] = io_write;
            return disk_io_write;
        if not 'time' in self.old_info: self.old_info['time'] = self.new_info['time']
        io_end = (io_write - self.old_info[pid]['io_write'])
        if io_end > 0:
            disk_io_write = io_end / (time.time() - self.old_info['time']);
        self.new_info[pid]['io_write'] = io_write;
        if disk_io_write > 0: return int(disk_io_write)
        return 0
    
    
    def get_io_read(self,pid,io_read):
        self.get_old();
        disk_io_read = 0
        if not self.old_info: self.old_info = {}
        if not pid in self.old_info:
            self.new_info[pid]['io_read'] = io_read;
            return disk_io_read;
        if not 'time' in self.old_info: self.old_info['time'] = self.new_info['time']
        io_end = (io_read - self.old_info[pid]['io_read'])
        if io_end > 0:
            disk_io_read = io_end / (time.time() - self.old_info['time']);
        self.new_info[pid]['io_read'] = io_read;
        if disk_io_read > 0: return int(disk_io_read)
        return 0
    
    
    def get_cpu_percent(self,pid,cpu_times,cpu_time):
        self.get_old();
        percent = 0.00;
        process_cpu_time = self.get_process_cpu_time(cpu_times);
        if not self.old_info: self.old_info = {}
        if not pid in self.old_info:
            self.new_info[pid] = {}
            self.new_info[pid]['cpu_time'] = process_cpu_time;
            return percent;
        percent = round(100.00 * (process_cpu_time - self.old_info[pid]['cpu_time']) / (cpu_time - self.old_info['cpu_time']),2)
        self.new_info[pid] = {}
        self.new_info[pid]['cpu_time'] = process_cpu_time;
        if percent > 0: return percent;
        return 0.00;
    
    def get_old(self):
        if self.old_info: return True;
        if not os.path.exists(self.old_path): return False
        data = public.readFile(self.old_path)
        if not data: return False
        data = json.loads(data);
        if not data: return False
        self.old_info = data
        del(data)
        return True
    
    def get_net_old(self):
        if self.old_net_info: return True;
        if not os.path.exists(self.old_net_path): return False
        data = public.readFile(self.old_net_path)
        if not data: return False
        data = json.loads(data);
        if not data: return False
        self.old_net_info = data
        del(data)
        return True
    
    def get_process_cpu_time(self,cpu_times):
        cpu_time = 0.00;
        for s in cpu_times: cpu_time += s;
        return cpu_time;
        
    
    def get_cpu_time(self):
        if self.__cpu_time: return self.__cpu_time;
        self.__cpu_time = 0.00;
        s = psutil.cpu_times()
        self.__cpu_time = s.user + s.system + s.nice + s.idle
        return self.__cpu_time;
    
    
    def to_size(self,size):
        d = ('b','KB','MB','GB','TB');
        s = d[0];
        for b in d:
            if size < 1024: return size,b;
            size = size / 1024;
            s = b;
        return size,b;
        
    def GoToProcess(self,name):
        ps = ['sftp-server','login','nm-dispatcher','irqbalance','qmgr','wpa_supplicant','lvmetad','auditd','master','dbus-daemon',
              'tapdisk','sshd','init','ksoftirqd','kworker','kmpathd','kmpath_handlerd','python','kdmflush','bioset','crond','kthreadd',
              'migration','rcu_sched','kjournald','iptables','systemd','network','dhclient','systemd-journald','NetworkManager','systemd-logind',
              'systemd-udevd','polkitd','tuned','rsyslogd']
        return  name in ps
    
    
    def object_to_dict(self,obj):
        result = {}
        for name in dir(obj):
            value = getattr(obj, name)
            if not name.startswith('__') and not callable(value) and not name.startswith('_'): result[name] = value
        return result
    
    
    def list_to_dict(self,data):
        result = []
        for s in data:
            result.append(self.object_to_dict(s))
        return result;
    
