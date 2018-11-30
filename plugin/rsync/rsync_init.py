 #coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2019 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------
import re, os, sys, time ,base64 ,json ,re ,public, db, crontab
sys.path.append("class/")
from panelAuth import panelAuth
from BTPanel import session

class plugin_rsync_init():
    __bin = '/usr/bin/rsync'
    rsyn_file = "/etc/rsyncd.conf"
    lsync_file = "/etc/lsyncd.conf"
    rsyn_path = 'plugin/rsync'
    
    def __init__(self):
        s_dir = self.rsyn_path + '/sclient';
        if not os.path.exists(s_dir): public.ExecShell("mkdir -p " + s_dir);
        s_dir = self.rsyn_path + '/secrets';
        if not os.path.exists(s_dir): public.ExecShell("mkdir -p " + s_dir);
        s_file = self.rsyn_path + '/lsyncd.log'
        if os.path.exists(s_file):
            if os.path.getsize(s_file) * 1024 * 1024 > 1024: public.writeFile(s_file,public.GetNumLines(s_file,2000))
      
    def get_logs(self,get):
        import page
        page = page.Page();
        count = public.M('logs').where('type=?',(u'数据同步工具',)).count();
        limit = 12;
        info = {}
        info['count'] = count
        info['row']   = limit
        info['p'] = 1
        if hasattr(get,'p'):
            info['p']    = int(get['p'])
        info['uri']      = get
        info['return_js'] = ''
        if hasattr(get,'tojs'):
            info['return_js']   = get.tojs
        data = {}
        
        data['page'] = page.GetPage(info,'1,2,3,4,5,8');
        data['data'] = public.M('logs').where('type=?',(u'数据同步工具',)).order('id desc').limit(str(page.SHIFT)+','+str(page.ROW)).field('log,addtime').select();
        return data;

    def get_rsync_conf(self,get):
        data = json.loads(public.readFile(self.rsyn_path + '/config.json'))
        return data
    
    def get_global_conf(self,get):
        data = self.get_rsync_conf(None);
        result = {}
        result['modules'] = data['modules']
        result['global'] = data['global']
        result['open'] = (len(public.ExecShell("/etc/init.d/rsynd status|grep 'already running'")[0]) > 1) | False
        return result;
    
    def modify_global_conf(self,get):
        data = self.get_rsync_conf(None);
        if 'port' in get: data['global']['port'] = int(get.port)
        if 'hosts_allow' in get: data['global']['hosts allow'] = " ".join(get.hosts_allow.split());
        if 'timeout' in get: data['global']['timeout'] = int(get.timeout);
        if 'max_connections' in get: data['global']['max connections'] = int(get.max_connections)
        if 'dont_compress' in get: data['global']['dont compress'] = get.dont_compress
        self.__write_conf(data);
        self.__write_logs('修改rsync服务器全局配置');
        return public.returnMsg(True,'设置成功!');
    
    def get_secretkey(self,get):
        module = self.get_module(get)
        secretkey = self.__EncodeKey(module['name'], module['password'], module['port'])
        return secretkey
    
    def add_module(self,get):
        if self.__check_path(get.path): return public.returnMsg(False,'不能同步系统关键目录');
        if self.__check_module_name(get.mName): return public.returnMsg(False,'您输入的用户名已存在');
        data = self.get_rsync_conf(None);
        auth_pass = self.rsyn_path + '/secrets/' + get.mName + '.db';
        module = {'name':get.mName,
                  'path':get.path,
                  'password':get.password,
                  'comment':get.comment,
                  'read only':'false',
                  'ignore errors':True,
                  'auth users':get.mName,
                  'secrets file':auth_pass,
                  'addtime':int(time.time())
                  }
        data['modules'].insert(0,module)
        self.__write_conf(data);
        self.__write_logs('添加rsync接收帐户[' + get.mName + ']');
        return public.returnMsg(True,'添加成功!');
    
    def modify_module(self,get):
        if self.__check_path(get.path): return public.returnMsg(False,'不能同步系统关键目录');
        data = self.get_rsync_conf(None);
        for i in range(len(data['modules'])):
            if data['modules'][i]['name'] == get.mName:
                data['modules'][i]['password'] = get.password;
                data['modules'][i]['path'] = get.path;
                data['modules'][i]['comment'] = get.comment;
                self.__write_passwd(data['modules'][i]['name'], data['modules'][i]['auth users'], data['modules'][i]['password'],False)
                self.__write_conf(data);
                self.__write_logs('修改rsync接收帐户[' + get.mName + ']');
                return public.returnMsg(True,'编辑成功!');
        return public.returnMsg(False,'指定模块不存在!');
    
    def remove_module(self,get):
        data = self.get_rsync_conf(None);
        for i in range(len(data['modules'])):
            if data['modules'][i]['name'] == get.mName: 
                del(data['modules'][i])
                self.__write_conf(data);
                auth_pass = self.rsyn_path + '/secrets/' + get.mName + '.db';
                if os.path.exists(auth_pass): os.remove(auth_pass);
                self.__write_logs('删除rsync接收帐户[' + get.mName + ']');
                return public.returnMsg(True,'删除成功!');
        return public.returnMsg(False,'指定模块不存在!');
        
    
    def get_module(self,get,name = None):
        if get: name = get.mName;
        data = self.get_rsync_conf(None);
        for i in range(len(data['modules'])):
            if data['modules'][i]['name'] == name:
                data['modules'][i]['port'] = data['global']['port'];
                return data['modules'][i]
        return public.returnMsg(False,'指定模块不存在!');
    
    def get_send_conf(self,get):
        modc = self.__get_mod(get)
        if not 'rsync' in session:  return modc;
        data = self.get_rsync_conf(None);
        return data['client'];
    
    def get_send_byname(self,get):
        data = self.get_rsync_conf(None);
        for i in range(len(data['client'])):
            if data['client'][i]['name'] == get['mName']: 
                tmp = data['client'][i];
                tmp['secret_key'] = self.__EncodeKey(tmp['name'], tmp['password'], tmp['rsync']['port'])
                return tmp;
        return public.returnMsg(False,'指定任务不存在!');
    
    def __get_mod(self,get):
        #filename = 'plugin/rsync/rsync_init.py';
        #if os.path.exists(filename): os.remove(filename);
        if 'rsync' in session: return public.returnMsg(True,'OK!');
        params = {}
        params['pid'] = '100000005';
        result = panelAuth().send_cloud('check_plugin_status',params)
        try:
            if not result['status']: 
                if 'rsync' in session: del(session['rsync'])
                return result;
        except: pass;
        session['rsync'] = True
        return result
    
    def __EncodeKey(self, name, passwd, port):
        data = json.dumps({'A': re.sub("(\d+\.){3,3}\d+_",'',name), 'B': passwd, 'C': port})
        return base64.b64encode(data)
    
    def __check_dst_port(self,ip,port,timeout = 3):
        import socket
        ok = True;
        try:
            s = socket.socket()
            s.settimeout(timeout)
            s.connect((ip,port))
            s.close()
        except:
            ok = False;
        return ok;
    
    def add_ormodify_send(self,get):
        if self.__check_path(get.path): return public.returnMsg(False,'不能同步系统关键目录');
        get.delay   = getattr(get,'delay','3');
        get.model   = getattr(get,'model','default.rsync');
        get.to      = getattr(get,'to','');
        get.ip      = getattr(get,'ip','');
        get.delete  = getattr(get,'delete','true');
        get.realtime = getattr(get,'realtime',True);
        get.ps      = getattr(get,'ps','');
        get.bwlimit = getattr(get,'bwlimit','1024');
        get.compress = getattr(get,'compress','true');
        get.archive = getattr(get,'archive','true');
        get.verbose = getattr(get,'verbose','true');
        get.index = getattr(get,'index','-1');
        
        if int(get.delay) < 0: get.delay = '0';
        if int(get.bwlimit) < 0: get.bwlimit = '0';
        
        if type(get.realtime) != bool:
            get.realtime = (get.realtime == 'true') | False;
        
        
        if get.model == 'default.rsync':
            try:
                server_conf = json.loads(base64.b64decode(get['secret_key']))
            except:
                return public.returnMsg(False,'错误的接收密钥');
            
            if not re.match("^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",  get.ip): return public.returnMsg(False,'请填写正确的IP地址!');
            cron = json.loads(get.cron)
            if not self.__check_dst_port(get.ip,int(server_conf['C'])):
                return public.returnMsg(False,'无法连接['+get.ip+':'+ str(server_conf['C']) + '],请检查IP地址是否正确,若正确无误，请检查远程服务器的安全组及防火墙是否正确放行['+str(server_conf['C'])+']端口!');
        else:
            if get.path == get.to: return public.returnMsg(False,'不能同步两个相同的目录');
            if not os.path.exists(get.to): public.ExecShell('mkdir -p ' + get.to);
            server_conf = {'A':get.mName,'B':'','C':'873'}
            cron = {}
            
        if get.index == '-1':
            if self.__check_client_name(server_conf['A']): return public.returnMsg(False,'已存在同名任务!');
            
        if not os.path.exists(get.path): public.ExecShell('mkdir -p ' + get.path);
        sclient = {
           'model':get.model,
           'name': server_conf['A'],
           'ip':get.ip,
           'password':server_conf['B'],
           'path':get.path,
           'to':get.to,
           'exclude':[],
           'delete':get.delete,
           'realtime': get.realtime | False,
           'delay':str(int(get.delay)),
           'rsync':{
                'bwlimit':str(int(get.bwlimit)),
                'port': str(server_conf['C']),
                'compress':get.compress,
                'archive':get.archive,
                'verbose':get.verbose
            },
           'ps':get.ps,
           'cron':cron,
           'update':time.time()
        }
        
        if get.model == 'default.rsync':
            ef = self.rsyn_path + '/sclient/' + sclient['name'] + '_exclude'
            if not os.path.exists(ef): public.writeFile(ef,'');
            self.__write_lsync_pass(sclient['name'],sclient['password'],False)
            self.__create_crond(sclient,get);
        
        cmd_file = self.rsyn_path + '/sclient/' + sclient['name'] + '_cmd'
        public.writeFile(cmd_file,self.__get_send_cmd(sclient))
        
        data = self.get_rsync_conf(None);
        n = True;
        if get.index != '-1':
                sclient['exclude'] = data['client'][int(get.index)]['exclude']
                data['client'][int(get.index)] = sclient;
                n = False;
        if n: data['client'].insert(0,sclient)
        self.__write_conf(data,True)
        if n: 
            public.writeFile(self.rsyn_path + '/sclient/' + sclient['name'] + '_exec.log','');
            self.__write_logs('添加同步任务[' + sclient['name'] + ']');
            public.ExecShell("nohup bash " + cmd_file + " >> " + self.rsyn_path + "/sclient/"+sclient['name']+"_exec.log 2>&1 &");
            return public.returnMsg(True,'添加成功!');
        self.__write_logs('修改同步任务[' + sclient['name'] + ']');
        return public.returnMsg(True,'修改成功!')
    
    def get_rsync_logs(self,get):
        if get.mName == 'lsyncd_logs':
            path = self.rsyn_path + '/lsyncd.log';
        else:
            path = self.rsyn_path + '/sclient/' + get.mName + '_exec.log';
        if not os.path.exists(path): public.writeFile(path,'');
        return public.returnMsg(True,public.GetNumLines(path,2000));
    
    def remove_rsync_logs(self,get):
        if get.mName == 'lsyncd_logs':
            path = self.rsyn_path + '/lsyncd.log';
            self.__write_logs('清空实时同步日志');
        else:
            path = self.rsyn_path + '/sclient/' + get.mName + '_exec.log';
            self.__write_logs('清空发送日志[' + get.mName + ']');
        public.writeFile(path,'');
        
        return public.returnMsg(True,'清除成功!');
    
    def exec_cmd(self,get):
        cmd_file = self.rsyn_path + '/sclient/' + get['mName'] + '_cmd'
        sclient = self.get_send_byname(get)
        public.writeFile(cmd_file,self.__get_send_cmd(sclient))
        
        os.system('echo "【'+public.getDate()+'】" >> ' + self.rsyn_path + "/sclient/"+get.mName+"_exec.log")
        public.ExecShell("nohup bash " + cmd_file + " >> " + self.rsyn_path + "/sclient/"+get.mName+"_exec.log 2>&1 &")
        self.__write_logs('手动执行同步任务['+get['mName']+']');
        return public.returnMsg(True,'同步指令已发送!');
        
    def remove_send(self,get):
        data = self.get_rsync_conf(None);
        for i in range(len(data['client'])):
            if data['client'][i]['name'] != get.mName: continue;
            data['client'][i]['realtime'] = True
            self.__create_crond(data['client'][i],get)
            del(data['client'][i])
            public.ExecShell("rm -f " + self.rsyn_path + '/sclient/' + get.mName + '_*')
            self.__write_conf(data,True)
            self.__write_logs('删除发送配置['+get['mName']+']');
            break;
        return public.returnMsg(True,'删除成功!');
    
    def get_exclude(self,get):
        data = self.get_rsync_conf(None);
        for i in range(len(data['client'])):
            if data['client'][i]['name'] == get['mName']: return data['client'][i]['exclude'];
        return public.returnMsg(False,'指定任务不存在!');
    
    def add_exclude(self,get):
        data = self.get_rsync_conf(None);
        for i in range(len(data['client'])):
            if data['client'][i]['name'] != get['mName']: continue;
            data['client'][i]['exclude'].insert(0, get.exclude)
            self.__write_conf(data,True)
            self.__write_logs('添加排除规则['+get.exclude+']到['+get['mName']+']');
            break;
        return public.returnMsg(True,'添加成功!');
    
    def remove_exclude(self,get):
        data = self.get_rsync_conf(None);
        for i in range(len(data['client'])):
            if data['client'][i]['name'] != get['mName']: continue;
            data['client'][i]['exclude'].remove(get.exclude)
            self.__write_conf(data,True)
            self.__write_logs('从['+get['mName']+']删除排除规则['+get.exclude+']');
            break;
        return public.returnMsg(True,'删除成功!');
    
    def rsync_service(self,get):
        s_cmd = "/etc/init.d/rsynd " + get.state
        public.ExecShell(s_cmd);
        self.__check_port_appect(get);
        self.__write_logs(s_cmd + '已执行');
        return public.returnMsg(True,'操作成功!');
    
    def __write_lsyncd(self,data):
        lsyncd_conf = "settings {\n"
        for k in data['settings'].keys():
            if re.search("^\d+$",data['settings'][k]) or data['settings'][k] in ['true','false']:
                lsyncd_conf += "\t" + k + ' = ' + data['settings'][k] + ',' + "\n"
            else:
                lsyncd_conf += "\t" + k + ' = "' + data['settings'][k] + '",' + "\n"
        lsyncd_conf = lsyncd_conf[:-2] + "\n}\n";
        
        for sclient in data['client']:
            if sclient['model'] == 'default.rsync': 
                lsyncd_conf += self.__format_rsync(sclient);
                self.__write_lsync_pass(sclient['name'],sclient['password'])
            else:
                lsyncd_conf += self.__format_local(sclient);
        public.writeFile(self.lsync_file,lsyncd_conf)
        if os.path.exists('/etc/init.d/lsyncd'):
            public.ExecShell("/etc/init.d/lsyncd restart");
        else:
            public.ExecShell("systemctl restart lsyncd");
        return True
    
    def __format_local(self,sclient):
        excludes = self.__format_exclude(sclient['exclude'])
        sync = '''
sync {
    default.direct,
    source    = "%s",
    target    = "%s",
    delay = 1,
    maxProcesses = 2,
    exclude = {%s}
}
''' % (sclient['path'],sclient['to'],excludes)
        return sync
        
    def __format_exclude(self,exclude):
        excludes = '"' + '","'.join(exclude) + '"';
        if excludes == '""': 
            excludes = '".user.ini"';
        else:
            excludes += ',".user.ini"';
        return excludes
    
    def __format_rsync(self,sclient):
        password_file = self.rsyn_path + '/sclient/' + sclient['name'] + '_pass'
        excludes = self.__format_exclude(sclient['exclude'])
        sync = '''
sync {
    %s,
    source = "%s",
    target = "%s@%s::%s",
    delete = %s,
    exclude = {%s},
    delay = %s,
    init = false,
    rsync = {
        binary = "%s",
        archive = %s,
        compress = %s,
        verbose = %s,
        password_file = "%s",
        _extra = {"--bwlimit=%s","--port=%s"}
    }
}''' % (sclient['model'],
        sclient['path'],
        sclient['name'],
        sclient['ip'],
        sclient['name'],
        sclient['delete'],
        excludes,
        sclient['delay'],
        self.__bin,
        sclient['rsync']["archive"],
        sclient['rsync']["compress"],
        sclient['rsync']["verbose"],
        password_file,
        sclient['rsync']["bwlimit"],
        sclient['rsync']["port"]
        )
        return sync;
        
            
    
    def __create_crond(self,sclient,get={}):
        name = '%s_%s' % (sclient['ip'], sclient['name'])
        cron_info = public.M('crontab').where("name=?", ('R'+name,)).field('id').find()
        if cron_info:
            get['id'] = cron_info['id']
            self.__delCronExec(get)
        
        cron_info = public.M('crontab').where("name=?", ('定时数据同步任务【' + sclient['name'] + '】',)).field('id').find()
        if cron_info:
            get['id'] = cron_info['id']
            self.__delCronExec(get)
        
        if sclient['realtime']: return True
        sdate = '`date +\"%Y-%m-%d %H:%M:%S\"`';
        self.__get_send_cmd(sclient)
        cmd = '''
rname="%s"
plugin_path="%s"
logs_file=$plugin_path/sclient/${rname}_exec.log
echo "★【%s】 STSRT" >> $logs_file
echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" >> $logs_file
bash $plugin_path/sclient/${rname}_cmd >> $logs_file 2>&1
echo "【%s】 END★" >> $logs_file
echo "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<" >> $logs_file
''' % (sclient['name'],self.rsyn_path,sdate,sdate)
        data = {}
        data['backupTo'] = 'localhost'
        data['sType'] = 'toShell'
        data['week'] = ''
        data['sName'] = ''
        data['urladdress'] = ''
        data['save'] = ''

        data['name'] = '定时数据同步任务【' + sclient['name'] + '】'
        data['type'] = sclient['cron']['type']
        data['where1'] = sclient['cron']['where1']
        data['sBody'] = cmd
        data['hour'] = sclient['cron']['hour']
        data['minute'] = sclient['cron']['minute']
        
        crontab.crontab().AddCrontab(data)
        return True
    
    def __check_port_appect(self,get):
        import firewalls;
        get.port = str(self.get_rsync_conf(None)['global']['port']);
        get.ps = '数据同步工具rsync端口';
        firewalls.firewalls().AddAcceptPort(get);
            
    def __delCronExec(self, get):
        crontab.crontab().DelCrontab(get)
    
    def __get_send_cmd(self,sclient):
        s_exclude = self.rsyn_path + '/sclient/' + sclient['name'] + '_exclude'
        s_pass = self.rsyn_path + '/sclient/' + sclient['name'] + '_pass'
        public.writeFile(s_exclude,("\n".join(sclient['exclude']) + "\n.user.ini").strip() + "\n");
        self.__write_lsync_pass(sclient['name'], sclient['password'], False)
        if sclient['model'] == 'default.rsync':
            __delete = ''
            if sclient['delete'] == 'true': __delete = ' --delete';
            s_cmd = self.__bin + ' -avzP' + __delete + ' --port=' + sclient['rsync']['port']  \
                    + ' --bwlimit=' + sclient['rsync']['bwlimit'] \
                    + ' --exclude-from=' + s_exclude + ' --password-file=' + s_pass \
                    + ' ' + sclient['path'] + ' ' + sclient['name'] + '@' + sclient['ip'] + '::' + sclient['name']
        else:
            s_cmd = self.__bin + " -avzP --exclude-from=" + s_exclude + ' ' + sclient['path'] + ' ' + sclient['to'];
        return s_cmd;
    
    def __write_rsync_conf(self,data):
        conf = '';
        for gn in data['global'].keys():
            if type(data['global'][gn]) != bool: 
                conf += gn + ' = ' + str(data['global'][gn]) + "\n"
            else:
                conf += gn + "\n"
        continues = ['name','password','addtime']
        for mod in data['modules']:
            conf += "\n";
            conf += "["+mod['name']+"]\n"
            self.__write_passwd(mod['name'], mod['auth users'], mod['password'])
            if not os.path.exists(mod['path']): public.ExecShell("mkdir -p " + mod['path'])
            
            for mn in mod.keys():
                if mn in continues: continue;
                conf += "\t"
                if type(mod[mn]) != bool: 
                    conf += mn + ' = ' + str(mod[mn]) + "\n"
                else:
                    conf += mn + "\n"
        public.writeFile(self.rsyn_file,conf)
        public.ExecShell("/etc/init.d/rsynd restart");
        return True
    
    def __write_passwd(self,name,user,passwd,focre = True):
        auth_pass = self.rsyn_path + '/secrets/' + name + '.db';
        if os.path.exists(auth_pass) and focre: return True;
        public.writeFile(auth_pass,user + ':' + passwd)
        public.ExecShell("chmod 600 " + auth_pass)
        return True
    
    def __write_lsync_pass(self,name,passwd,focre = True):
        auth_pass = self.rsyn_path + '/sclient/' + name + '_pass';
        if os.path.exists(auth_pass) and focre: return True;
        public.writeFile(auth_pass,passwd)
        public.ExecShell("chmod 600 " + auth_pass)
        return True
    
    def __write_conf(self,data,lsyncd = False):
        public.writeFile(self.rsyn_path + '/config.json',json.dumps(data))
        if not lsyncd:
            self.__write_rsync_conf(data)
        else:
            self.__write_lsyncd(data)
        return True
    
    def __write_logs(self,log):
        public.WriteLog('数据同步工具',log);
        
    def __check_module_name(self,name):
        data = self.get_rsync_conf(None)
        for module in data['modules']:
            if module['name'] == name: return True;
        return False

    def __check_client_name(self,name):
        data = self.get_rsync_conf(None)
        for module in data['client']:
            if module['name'] == name: return True;
        return False
        
    def __check_path(self,path):
        if path[-1] != '/': path += '/'
        for dir_name in ['/usr/', '/var/', '/proc/', '/boot/', '/etc/', '/dev/', '/root/', '/run/', '/sys/', '/tmp/']:
            if re.match('^'+dir_name, path): return True
        if path in ['/', '/www/', '/www/server/', '/home/']: return True
        return False
        
    def to_new_version(self,get = None):
        if not os.path.exists(self.rsyn_path + 'secrets'):
            os.mkdir(self.rsyn_path + 'secrets')

        if not os.path.exists(self.rsyn_file):
            os.mknod(self.rsyn_file)
            data_conf = '''uid = root
gid = root
use chroot = yes
port = 873
hosts allow =
log file = /var/log/rsyncd.log
pid file = /var/run/rsyncd.pid
            '''
            public.ExecShell('echo "%s" > %s' % (data_conf, self.rsyn_file))
        self.rsyn_conf = {}
        with open(self.rsyn_file, "r") as conf:
            section = 'is_global'
            self.rsyn_conf[section] = {}
            for row in conf:
                if not re.match("^[\s]*?#", row) and row != "\n":
                    is_section = re.findall("\[(.*?)\]", row)
                    if is_section:
                        section = is_section[0]
                        self.rsyn_conf[section] = {}
                    else:
                        try:
                            info = row.split('=')
                            key = info[0].strip()
                            value = info[1].strip()
                            if section == 'is_global' and key in ["log file",  "pid file", "uid", "gid", "use chroot"]:
                                continue
                            if key == "secrets file":
                                passwd = re.findall(
                                    ":(\w+)", public.readFile(value))[0]
                                self.rsyn_conf[section]["passwd"] = passwd
                                continue
                            if key == "auth users":
                                continue
                                key = "user"
                            if key == "hosts allow":
                                key = "ip"
                                value = value.replace(",", "\n")
                            if key == "dont commpress":
                                key = "dont_commpress"
                                value = value.replace(' *.', ',')[2:]
                            key = key.replace(" ", "_")
                            self.rsyn_conf[section][key] = value
                        except:
                            pass

            if not 'port' in self.rsyn_conf['is_global'].keys():
                self.rsyn_conf['is_global']['port'] = 873
            if not 'ip' in self.rsyn_conf['is_global'].keys():
                self.rsyn_conf['is_global']['ip'] = ''
            
            data = self.get_rsync_conf(None)
            data['global']['port'] =  self.rsyn_conf['is_global']['port']
            del(self.rsyn_conf['is_global'])
            for k in self.rsyn_conf.keys():
                auth_pass = self.rsyn_path + '/secrets/' + k + '.db';
                com = True;
                for m in data['modules']:
                    if m['name'] == k:
                        com = False
                        break;
                if not com: continue;
                module = {
                  'name':k,
                  'path':self.rsyn_conf[k]['path'],
                  'password':self.rsyn_conf[k]['passwd'],
                  'comment':self.rsyn_conf[k]['comment'],
                  'read only':'false',
                  'ignore errors':True,
                  'auth users':k,
                  'secrets file':auth_pass,
                  'addtime':time.time()
                  }
                data['modules'].insert(0,module)
            
            serverDict = public.readFile(self.rsyn_path + '/serverdict.json')
            if serverDict:
                serverDict = json.loads(serverDict)
                for k in serverDict.keys():
                    del(serverDict[k]['cron_info']['id']);
                    tmp = k.split('_')
                    sclient = {
                       'model':'default.rsync',
                       'name': k,
                       'ip':tmp[0],
                       'password':public.readFile(self.rsyn_path + '/sclient/' + k + '.db'),
                       'path':serverDict[k]['path'],
                       'to':'',
                       'exclude':[],
                       'delete':'false',
                       'realtime': serverDict[k]['inotify_info'],
                       'delay':3,
                       'rsync':{
                            'bwlimit':'200',
                            'port': str(serverDict[k]['port']),
                            'compress':'true',
                            'archive':'true',
                            'verbose':'true'
                        },
                       'ps':'',
                       'cron':serverDict[k]['cron_info'],
                       'addtime':time.time()
                    }
                    data['client'].insert(0,sclient)
                os.remove(self.rsyn_path + '/serverdict.json')
            public.writeFile(self.rsyn_path + '/config.json',json.dumps(data))

