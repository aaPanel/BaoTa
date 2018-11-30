#!/usr/bin/python
#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------
#+--------------------------------------------------------------------
#|   宝塔系统加固程序
#+--------------------------------------------------------------------
import os,sys,json,time,re,psutil
from datetime import datetime
os.chdir('/www/server/panel')
sys.path.append('class/')
import public

class syssafe_main:
    __plugin_path = 'plugin/syssafe/'
    __state = {True:'开启',False:'关闭'}
    __name = u'系统加固'
    __deny = '/etc/hosts.deny'
    __allow = '/etc/hosts.allow'
    __months = {'Jan':'01','Feb':'02','Mar':'03','Apr':'04','May':'05','Jun':'06','Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'}
    __deny_list = None
    __config = None

    #检测关键目录是否可以被写入文件
    def check_sys_write(self):
        test_file = '/etc/init.d/bt_10000100.pl'
        public.writeFile(test_file,'True')
        if os.path.exists(test_file): 
            os.remove(test_file)
            return True
        return False

    #获取防护状态
    def get_safe_status(self,get):
        data = self.__read_config()
        if not data['open']: 
            if not self.check_sys_write(): 
                self.set_open(None,0)
                if not self.check_sys_write(): 
                    return public.returnMsg(False,'检测到第三方系统加固软件,无需再使用本插件!');
        result = []
        for s_name in data.keys():
            if type(data[s_name]) == bool: continue
            if not 'name' in data[s_name]: continue;

            tmp = {}
            tmp['key'] = s_name
            tmp['name'] = data[s_name]['name']
            tmp['open'] = data[s_name]['open']
            tmp['ps'] = data[s_name]['ps']
            result.append(tmp)

        safe_list = {}
        safe_list['open'] = data['open']
        safe_list['list'] = result
        return safe_list

    #设置防护状态
    def set_safe_status(self,get):
        data = self.__read_config()
        data[get.s_key]['open'] = not data[get.s_key]['open']
        self.__write_config(data)
        if type(data[get.s_key]) != bool:
            if 'paths' in data[get.s_key] and data['open']: self.__set_safe_state(data[get.s_key]['paths'],data[get.s_key]['open'])
        msg = u'已将[%s]状态设置为[%s]' % (data[get.s_key]['name'],self.__state[data[get.s_key]['open']])
        public.WriteLog(self.__name,msg)
        return public.returnMsg(True,msg)

    #设置系统加固开关
    def set_open(self,get,is_hit = -1):
        data = self.__read_config()
        if not data['open'] and is_hit == 1: return True
        if is_hit != -1:
            if is_hit == 0: 
                data['open'] = True
            else:
                data['open'] = False

        data['open'] = not data['open']
        service_msg = {True:'start',False:'stop'}
        if is_hit == -1: self.__write_config(data)
        for s_name in data.keys():
            if type(data[s_name]) == bool: continue;
            if not 'name' in data[s_name]: continue;
            if not 'paths' in data[s_name]: continue;
            if not data['open']: data[s_name]['open'] = False
            self.__set_safe_state(data[s_name]['paths'],data[s_name]['open'])
        msg = u'已[%s]宝塔系统加固功能' % self.__state[data['open']]
        public.WriteLog(self.__name,msg)
        s_exec = '/etc/init.d/bt_syssafe %s' % service_msg[data['open']]
        public.ExecShell(s_exec)
        return public.returnMsg(True,msg)

    #获取防护配置
    def get_safe_config(self,get):
        data = self.__read_config()
        data[get.s_key]['paths'] = self.__list_safe_state(data[get.s_key]['paths'])
        return data[get.s_key]
    
    #添加防护对象
    def add_safe_path(self,get):
        if not os.path.exists(get.path): return public.returnMsg(False,u'指定文件或目录不存在!')
        data = self.__read_config()

        for m_path in data[get.s_key]['paths']:
            if get.path == m_path['path']: return public.returnMsg(False,u'指定文件或目录已经添加过了!')

        path_info = {}
        path_info['path'] = get.path
        path_info['chattr'] = get.chattr
        path_info['s_mode'] = int(oct(os.stat(get.path).st_mode)[-3:],8)
        if get.d_mode:
            path_info['d_mode'] = int(get.d_mode,8)
        else:
            path_info['d_mode'] = path_info['s_mode']
        
        data[get.s_key]['paths'].insert(0,path_info)
        if 'paths' in data[get.s_key]: 
            public.ExecShell('chattr -%s %s' % (path_info['chattr'],path_info['path']))
            self.__set_safe_state([path_info],data[get.s_key]['open'])
        self.__write_config(data)
        msg = u'添加防护对象[%s]到[%s]' % (get.path,data[get.s_key]['name'])
        public.WriteLog(self.__name,msg)
        return public.returnMsg(True,msg)

    #删除防护对象
    def remove_safe_path(self,get):
        data = self.__read_config()
        is_exists = False
        for m_path in data[get.s_key]['paths']:
            if get.path == m_path['path']: 
                is_exists = True
                data[get.s_key]['paths'].remove(m_path)
                if os.path.exists(get.path):self.__set_safe_state([m_path],False)
                break;

        if not is_exists: return public.returnMsg(False,'指定保护对象不存在!')

        self.__write_config(data)
        msg = u'从[%s]删除保护对象[%s]' % (data[get.s_key]['name'],get.path)
        public.WriteLog(self.__name,msg)
        return public.returnMsg(True,msg)

    #添加进程白名单
    def add_process_white(self,get):
        data = self.__read_config()
        get.process_name = get.process_name.strip()
        if get.process_name in data['process']['process_white']: return public.returnMsg(False,'指定进程名已在白名单')
        data['process']['process_white'].insert(0,get.process_name)
        self.__write_config(data)
        msg = u'添加进程名[%s]到进程白名单' % get.process_name
        public.WriteLog(self.__name,msg)
        public.ExecShell('/etc/init.d/bt_syssafe restart')
        return public.returnMsg(True,msg)
    
    #删除进程白名单
    def remove_process_white(self,get):
        data = self.__read_config()
        get.process_name = get.process_name.strip()
        if not get.process_name in data['process']['process_white']: return public.returnMsg(False,'指定进程名不存在')
        data['process']['process_white'].remove(get.process_name)
        self.__write_config(data)
        msg = u'从进程白名单删除进程名[%s]' % get.process_name
        public.WriteLog(self.__name,msg)
        public.ExecShell('/etc/init.d/bt_syssafe restart')
        return public.returnMsg(True,msg)

    #添加进程关键词白名单
    def add_process_rule(self,get):
        data = self.__read_config()
        get.process_key = get.process_key.strip()
        if get.process_key in data['process']['process_rule']: return public.returnMsg(False,'指定关键词已在白名单')
        data['process']['process_rule'].insert(0,get.process_key)
        self.__write_config(data)
        msg = u'添加关键词[%s]到进程关键词白名单' % get.process_key
        public.WriteLog(self.__name,msg)
        return public.returnMsg(True,msg)

    #删除进程关键词白名单
    def remove_process_rule(self,get):
        data = self.__read_config()
        get.process_key = get.process_key.strip()
        if not get.process_key in data['process']['process_rule']: return public.returnMsg(False,'指定关键词不存在')
        data['process']['process_rule'].remove(get.process_key)
        self.__write_config(data)
        msg = u'从进程关键词白名单删除关键词[%s]' % get.process_key
        public.WriteLog(self.__name,msg)
        return public.returnMsg(True,msg)

    #取进程白名单列表
    def get_process_white(self,get):
        data = self.__read_config()
        return data['process']['process_white']

    #取进程关键词
    def get_process_rule(self,get):
        data = self.__read_config()
        return data['process']['process_white_rule']

    #取进程排除名单
    def get_process_exclude(self,get):
        data = self.__read_config()
        return data['process']['process_exclude']

    #取SSH加固策略
    def get_ssh_config(self,get):
        data = self.__read_config()
        return data['ssh']

    #保存SSH加固策略
    def save_ssh_config(self,get):
        get.cycle = int(get.cycle)
        get.limit = int(get.limit)
        get.limit_count = int(get.limit_count)
        if get.cycle > get.limit: return public.returnMsg(False,'封锁时间不能小于检测周期!');
        if get.cycle < 30 or get.cycle > 1800:  return public.returnMsg(False,'检测周期的值必需在30 - 1800秒之间!');
        if get.limit < 60: return public.returnMsg(False,'封锁时间不能小于60秒');
        if get.limit_count < 3 or get.limit_count > 100: return public.returnMsg(False,'检测阈值必需在3 - 100秒之间!');
        data = self.__read_config()
        data['ssh']['cycle'] = get.cycle
        data['ssh']['limit'] = get.limit
        data['ssh']['limit_count'] = get.limit_count
        self.__write_config(data)
        msg = u'修改SSH策略: 在[%s]秒内,登录错误[%s]次,封锁[%s]秒' % (data['ssh']['cycle'],data['ssh']['limit_count'],data['ssh']['limit'])
        public.WriteLog(self.__name,msg)
        public.ExecShell('/etc/init.d/bt_syssafe restart')
        return public.returnMsg(True,'配置已保存!')


    #获取SSH登录日志
    def get_ssh_login_logs(self,get):
        import page
        page = page.Page();
        count = public.M('logs').where('type=?',(u'SSH登录',)).count();
        limit = 12;
        info = {}
        info['count'] = count
        info['row']   = limit
        info['p'] = 1
        if hasattr(get,'p'):
            info['p']    = int(get['p'])
        info['uri']      = {}
        info['return_js'] = ''
        if hasattr(get,'tojs'):
            info['return_js']   = get.tojs
        data = {}
        data['page'] = page.GetPage(info,'1,2,3,4,5');
        data['data'] = public.M('logs').where('type=?',(u'SSH登录',)).order('id desc').limit(str(page.SHIFT)+','+str(page.ROW)).field('log,addtime').select();
        return data;

    #SSH日志分析任务
    def ssh_login_task(self,get = None):
        secure_logs =  public.GetNumLines('/var/log/secure',500).split('\n')
        total_time = '/dev/shm/ssh_total_time.pl'
        if not os.path.exists(total_time):  public.writeFile(total_time,str(int(time.time())))
        last_total_time = int(public.readFile(total_time))
        now_total_time = int(time.time())
        last_on_time = now_total_time - last_total_time
        self.__config = self.__read_config()
        my_config = self.__config['ssh']
        self.get_deny_list()
        is_modify = False
        for c_ip in self.__deny_list.keys():
            if self.__deny_list[c_ip] > now_total_time or self.__deny_list[c_ip] == 0: continue
            self.ip = c_ip
            self.remove_ssh_limit(None)
        ip_total = {}
        for log in secure_logs:
            if log.find('Failed password for invalid user') != -1:
                login_time = self.__to_date(re.search('^\w+\s+\d+\s+\d+:\d+:\d+',log).group())
                if now_total_time - login_time > my_config['cycle']: continue
                client_ip = re.search('(\d+\.)+\d+',log).group()
                if client_ip in self.__deny_list: continue
                if not client_ip in ip_total:ip_total[client_ip] = 0
                ip_total[client_ip] += 1
                if ip_total[client_ip] < my_config['limit_count']: continue
                self.__deny_list[client_ip] = now_total_time + my_config['limit']
                self.save_deay_list()
                self.ip = client_ip
                self.add_ssh_limit(None)
                public.WriteLog(u'SSH登录',u"[%s]在[%s]秒内连续[%s]次登录SSH失败,封锁[%s]秒" % (client_ip,my_config['cycle'], my_config['limit_count'], my_config['limit']))

            elif log.find('Accepted p') != -1:
                login_time = self.__to_date(re.search('^\w+\s+\d+\s+\d+:\d+:\d+',log).group())
                if login_time < last_total_time: continue;
                client_ip = re.search('(\d+\.)+\d+',log).group()
                login_user = re.findall("(\w+)\s+from",log)[0]
                public.WriteLog(u'SSH登录',u"用户[%s]成功登录服务器,用户IP:[%s],登录时间:[%s]" % (login_user,client_ip,time.strftime('%Y-%m-%d %X',time.localtime(login_time))))
        public.writeFile(total_time,str(int(time.time())))
        return 'success'

    #转换时间格式
    def __to_date(self,date_str):
        tmp = date_str.split(' ')
        
        s_date = str(datetime.now().year) + '-' + self.__months.get(tmp[0]) + '-' + tmp[1] + ' ' + tmp[2]
        time_array = time.strptime(s_date, "%Y-%m-%d %H:%M:%S")
        time_stamp = int(time.mktime(time_array))
        return time_stamp
    
    #添加SSH目标IP
    def add_ssh_limit(self,get):
        if get: 
            ip = get.ip;
        else:
            ip = self.ip;

        if ip in self.get_ssh_limit(): return public.returnMsg(True,'指定IP黑名单已存在!');
        denyConf = public.readFile(self.__deny).strip();
        while denyConf[-1:] == "\n" or denyConf[-1:] == " ": denyConf = denyConf[:-1];
        denyConf += "\nsshd:" + ip+":deny\n";
        public.writeFile(self.__deny,denyConf);
        if ip in self.get_ssh_limit(): 
            msg = u'添加IP[%s]到SSH-IP黑名单' % ip
            public.WriteLog(self.__name,msg)
            self.get_deny_list()
            if not ip in self.__deny_list: self.__deny_list[ip] = 0
            self.save_deay_list()
            return public.returnMsg(True,'添加成功!');
        return public.returnMsg(False,'添加失败!');
    
    #删除IP黑名单
    def remove_ssh_limit(self,get):
        if get: 
            ip = get.ip;
        else:
            ip = self.ip;
        
        if not self.__deny_list: self.get_deny_list()
        if ip in self.__deny_list: del(self.__deny_list[ip])
        self.save_deay_list()
        if not ip in self.get_ssh_limit(): return public.returnMsg(True,'指定IP黑名单不存在!');
        
        denyConf = public.readFile(self.__deny).strip();
        while denyConf[-1:] == "\n" or denyConf[-1:] == " ": denyConf = denyConf[:-1];
        denyConf = re.sub("\nsshd:"+ip+":deny\n?","\n",denyConf);
        public.writeFile(self.__deny,denyConf+"\n");
        
        msg = u'从SSH-IP黑名单中解封[%s]' % ip
        public.WriteLog(self.__name,msg)
        return public.returnMsg(True,'解封成功!');
    
    #获取当前SSH禁止IP
    def get_ssh_limit(self,get = None):
        denyConf = public.readFile(self.__deny);
        return re.findall("sshd:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):deny",denyConf);

    #获取deny信息
    def get_ssh_limit_info(self,get):
        self.get_deny_list()
        conf_list = self.get_ssh_limit(None)
        data= []
        for c_ip in conf_list:
            tmp = {}
            tmp['address'] = c_ip
            tmp['end'] = 0
            if c_ip in self.__deny_list: tmp['end'] = self.__deny_list[c_ip]
            data.append(tmp)
        return data

    #取deny_list
    def get_deny_list(self):
        deny_file = self.__plugin_path + 'deny.json'
        if not os.path.exists(deny_file): public.writeFile(deny_file,'{}')
        self.__deny_list = json.loads(public.readFile(self.__plugin_path + 'deny.json'))

    #存deny_list
    def save_deay_list(self):
        deny_file = self.__plugin_path + 'deny.json'
        public.writeFile(deny_file,json.dumps(self.__deny_list))

    #取操作日志
    def get_logs(self,get):
        import page
        page = page.Page();
        count = public.M('logs').where('type=? or type=?',(self.__name,u'SSH登录')).count();
        limit = 12;
        info = {}
        info['count'] = count
        info['row']   = limit
        info['p'] = 1
        if hasattr(get,'p'):
            info['p']    = int(get['p'])
        info['uri']      = {}
        info['return_js'] = ''
        if hasattr(get,'tojs'):
            info['return_js']   = get.tojs
        data = {}
        data['page'] = page.GetPage(info,'1,2,3,4,5');
        data['data'] = public.M('logs').where('type=? or type=?',(self.__name,u'SSH登录')).order('id desc').limit(str(page.SHIFT)+','+str(page.ROW)).field('log,addtime').select();
        return data;

    #锁定目录或文件
    def __lock_path(self,pathInfo):
        try:
            if not os.path.exists(pathInfo['path']): return False
            if pathInfo['d_mode']: os.chmod(pathInfo['path'],pathInfo['d_mode'])
            if pathInfo['chattr']: public.ExecShell('chattr +%s %s' % (pathInfo['chattr'],pathInfo['path']))
            return True
        except: return False
        

    #目录或文件解锁
    def __unlock_path(self,pathInfo):
        try:
            if not os.path.exists(pathInfo['path']): return False
            if pathInfo['chattr']: public.ExecShell('chattr -%s %s' % (pathInfo['chattr'],pathInfo['path']))
            if pathInfo['s_mode']: os.chmod(pathInfo['path'],pathInfo['s_mode'])
            return True
        except: return False

    #取文件或目录锁定状态
    def __get_path_state(self,path):
        if os.path.isfile(path):
            shell_cmd = "lsattr %s|awk '{print $1}'" % path
        else:
            shell_cmd = "lsattr %s |grep '%s$'|awk '{print $1}'" % (os.path.dirname(path),path)
        result = public.ExecShell(shell_cmd)[0]
        if result.find('-i-') != -1: return 'i'
        if result.find('-a-') != -1: return 'a'
        return False

    #遍历当前防护状态
    def __list_safe_state(self,paths):
        for i in range(len(paths)):
            mstate = self.__get_path_state(paths[i]['path'])
            paths[i]['state'] = mstate == paths[i]['chattr']
            paths[i]['s_mode'] = oct(paths[i]['s_mode'])
            paths[i]['d_mode'] = oct(paths[i]['d_mode'])
        return paths

    #设置指定项的锁定状态
    def __set_safe_state(self,paths,lock = True):
        for path_info in paths:
            if lock: 
                self.__lock_path(path_info)
            else:
                self.__unlock_path(path_info)
        return True


    #写配置文件
    def __write_config(self,data):
        public.writeFile(self.__plugin_path + 'config.json',json.dumps(data))
        return True

    #读配置文件
    def __read_config(self):
        return json.loads(public.readFile(self.__plugin_path + 'config.json'))



    __limit = 30;
    __vmsize = 1048576 * 100;
    __wlist = None
    __wslist = None
    __elist = None

    def check_main(self):
        pids = psutil.pids()
        for pid in pids:
            if pid < 1100: continue
            fname = '/proc/'+str(pid)+'/comm'
            if not os.path.exists(fname): continue
            name = public.readFile(fname).strip()
            if self.check_white(name): continue;
            try:
                p = psutil.Process(pid);
                percent = p.cpu_percent(interval = 0.1);
                vm = p.memory_info().vms
                if percent > self.__limit or vm > self.__vmsize:
                    if str(p.cmdline()).find('/www/server/cron') != -1: continue
                    if name.find('kworker') != -1: continue
                    p.kill();
                    public.WriteLog(self.__name,"已强制结束异常进程:[%s],PID:[%s],CPU:[%s]" % (name,pid,percent))
            except:continue



    #检查白名单
    def check_white(self,name):
        if not self.__elist: self.__elist = self.get_process_exclude(None)
        if not self.__wlist: self.__wlist = self.get_process_white(None)
        if not self.__wslist: self.__wslist = self.get_process_rule(None)

        if name in self.__elist: return True
        if name in self.__wlist: return True
        for key in self.__wslist:
            if name.find(key) != -1: return True
        return False

    #开始处理
    def start(self):
        import threading
        p = threading.Thread(target=self.ssh_task)
        p.setDaemon(True)
        p.start()
        self.process_task()

    #处理进程检测任务
    def process_task(self):
        time.sleep(600)
        if not self.__config: self.__config = self.__read_config()
        while True:
            if self.__config['process']['open']: self.check_main()
            time.sleep(3)

    #处理SSH日志分析任务
    def ssh_task(self):
        if not self.__config: self.__config = self.__read_config()
        while True:
            if self.__config['ssh']['open']: self.ssh_login_task()
            time.sleep(self.__config['ssh']['cycle'])



if __name__ == "__main__":
    c = syssafe_main();
    if len(sys.argv) == 1: 
        c.start();
    else:
        c.set_open(None,int(sys.argv[1]));



