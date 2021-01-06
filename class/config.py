#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 x3
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2017 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------
import public,re,sys,os,nginx,apache,json,time,ols
try:
    import pyotp
except:
    public.ExecShell("pip install pyotp &")
try:
    from BTPanel import session,admin_path_checks,g,request
    import send_mail
except:pass
class config:
    _setup_path = "/www/server/panel"
    _key_file = _setup_path+"/data/two_step_auth.txt"
    _bk_key_file = _setup_path + "/data/bk_two_step_auth.txt"
    _username_file = _setup_path + "/data/username.txt"
    _core_fle_path = _setup_path + '/data/qrcode'
    __mail_config = '/www/server/panel/data/stmp_mail.json'
    __mail_list_data = '/www/server/panel/data/mail_list.json'
    __dingding_config = '/www/server/panel/data/dingding.json'
    __mail_list = []
    __weixin_user = []

    def __init__(self):
        try:
            self.mail = send_mail.send_mail()
            if not os.path.exists(self.__mail_list_data):
                ret = []
                public.writeFile(self.__mail_list_data, json.dumps(ret))
            else:
                try:
                    mail_data = json.loads(public.ReadFile(self.__mail_list_data))
                    self.__mail_list = mail_data
                except:
                    ret = []
                    public.writeFile(self.__mail_list_data, json.dumps(ret))
        except:pass
    # 返回配置邮件地址
    def return_mail_list(self, get):
        return public.returnMsg(True, self.__mail_list)

    # 删除邮件接口
    def del_mail_list(self, get):
        emial = get.email.strip()
        if emial in self.__mail_list:
            self.__mail_list.remove(emial)
            public.writeFile(self.__mail_list_data, json.dumps(self.__mail_list))
            return public.returnMsg(True, '删除成功')
        else:
            return public.returnMsg(True, '邮件不存在')

    #添加接受邮件地址
    def add_mail_address(self, get):
        if not hasattr(get, 'email'): return public.returnMsg(False, '请输入邮箱')
        emailformat = re.compile(r'[a-zA-Z0-9.-_+%]+@[a-zA-Z0-9]+\.[a-zA-Z0-9]+')
        if not emailformat.search(get.email): return public.returnMsg(False, '请输入正确的邮箱')
        # 测试发送邮件
        if get.email.strip() in self.__mail_list: return public.returnMsg(True, '邮箱已经存在')
        self.__mail_list.append(get.email.strip())
        public.writeFile(self.__mail_list_data, json.dumps(self.__mail_list))
        return public.returnMsg(True, '添加成功')

    # 添加自定义邮箱地址
    def user_mail_send(self, get):
        if not (hasattr(get, 'email') or hasattr(get, 'stmp_pwd') or hasattr(get, 'hosts') or hasattr(get, 'port')):
            return public.returnMsg(False, '请填写完整信息')
        # 自定义邮件
        self.mail.qq_stmp_insert(get.email.strip(), get.stmp_pwd.strip(), get.hosts.strip(),get.port.strip())
        # 测试发送
        if self.mail.qq_smtp_send(get.email.strip(), '宝塔告警测试邮件', '宝塔告警测试邮件'):
            if not get.email.strip() in self.__mail_list:
                self.__mail_list.append(get.email.strip())
                public.writeFile(self.__mail_list_data, json.dumps(self.__mail_list))
            return public.returnMsg(True, '添加成功')
        else:
            ret = []
            public.writeFile(self.__mail_config, json.dumps(ret))
            return public.returnMsg(False, '邮件发送失败,请检查信息是否正确,或者更换其他端口进行尝试')

    # 查看自定义邮箱配置
    def get_user_mail(self, get):
        qq_mail_info = json.loads(public.ReadFile(self.__mail_config))
        if len(qq_mail_info) == 0:
            return public.returnMsg(False, '无信息')
        if not 'port' in qq_mail_info:qq_mail_info['port']=465
        return public.returnMsg(True, qq_mail_info)


    # 用户自定义邮件发送
    def user_stmp_mail_send(self, get):
        if not (hasattr(get, 'email')): return public.returnMsg(False, '请填写邮件地址')
        emailformat = re.compile(r'[a-zA-Z0-9.-_+%]+@[a-zA-Z0-9]+\.[a-zA-Z0-9]+')
        if not emailformat.search(get.email): return public.returnMsg(False, '请输入正确的邮箱')
        # 测试发送邮件
        if not get.email.strip() in self.__mail_list: return public.returnMsg(True, '邮箱不存在,请添加到邮箱列表中')
        if not (hasattr(get, 'title')): return public.returnMsg(False, '请填写邮件标题')
        if not (hasattr(get, 'body')): return public.returnMsg(False, '请输入邮件内容')
        # 先判断是否存在stmp信息
        qq_mail_info = json.loads(public.ReadFile(self.__mail_config))
        if len(qq_mail_info) == 0:
            return public.returnMsg(False, '未找到STMP的信息,请在设置中重新添加自定义邮件STMP信息')
        if self.mail.qq_smtp_send(get.email.strip(), get.title.strip(), get.body):
            # 发送成功
            return public.returnMsg(True, '发送成功')
        else:
            return public.returnMsg(False, '发送失败')

    # 查看能使用的告警通道
    def get_settings(self, get):
        qq_mail_info = json.loads(public.ReadFile(self.__mail_config))
        if len(qq_mail_info) == 0:
            user_mail = False
        else:
            user_mail = True
        dingding_info = json.loads(public.ReadFile(self.__dingding_config))
        if len(dingding_info) == 0:
            dingding = False
        else:
            dingding = True
        ret = {}
        ret['user_mail'] = {"user_name": user_mail, "mail_list": self.__mail_list,"info":self.get_user_mail(get)}
        ret['dingding'] = {"dingding": dingding,"info":self.get_dingding(get)}
        return ret
    # 设置钉钉报警
    def set_dingding(self, get):
        if not (hasattr(get, 'url') or hasattr(get, 'atall')):
            return public.returnMsg(False, '请填写完整信息')
        if get.atall:
            get.atall = 'True'
        else: get.atall = 'False'
        self.mail.dingding_insert(get.url.strip(), get.atall)
        if self.mail.dingding_send('宝塔告警测试'):
            return public.returnMsg(True, '添加成功')
        else:
            ret = []
            public.writeFile(self.__dingding_config, json.dumps(ret))
            return public.returnMsg(False, '添加失败,请查看URL是否正确')
    # 查看钉钉
    def get_dingding(self, get):
        qq_mail_info = json.loads(public.ReadFile(self.__dingding_config))
        if len(qq_mail_info) == 0:
            return public.returnMsg(False, '无信息')
        return public.returnMsg(True, qq_mail_info)

    # 使用钉钉发送消息
    def user_dingding_send(self, get):
        qq_mail_info = json.loads(public.ReadFile(self.__dingding_config))
        if len(qq_mail_info) == 0:
            return public.returnMsg(False, '未找到您配置的钉钉的配置信息,请在设置中添加')
        if not (hasattr(get, 'content')): return public.returnMsg(False, '请输入你需要发送的数据')
        if self.mail.dingding_send(get.content):
            return public.returnMsg(True, '发送成功')
        else:
            return public.returnMsg(False, '发送失败')

    
    def getPanelState(self,get):
        return os.path.exists('/www/server/panel/data/close.pl')

    def reload_session(self):
        userInfo = public.M('users').where("id=?",(1,)).field('username,password').find()
        token = public.Md5(userInfo['username'] + '/' + userInfo['password'])
        public.writeFile('/www/server/panel/data/login_token.pl',token)

        sess_path = 'data/sess_files'
        if not os.path.exists(sess_path):
            os.makedirs(sess_path,384)
        self.clean_sess_files(sess_path)
        sess_key = public.get_sess_key()
        sess_file = os.path.join(sess_path,sess_key)
        public.writeFile(sess_file,str(int(time.time()+86400)))
        public.set_mode(sess_file,'600')
        session['login_token'] = token

    def clean_sess_files(self,sess_path):
        '''
            @name 清理过期的sess_file
            @auther hwliang<2020-07-25>
            @param sess_path(string) sess_files目录
            @return void
        '''
        s_time = time.time()
        for fname in os.listdir(sess_path):
            try:
                if len(fname) != 32: continue
                sess_file = os.path.join(sess_path,fname)
                if not os.path.isfile(sess_file): continue
                sess_tmp = public.ReadFile(sess_file)
                if not sess_tmp:
                    if os.path.exists(sess_file):
                        os.remove(sess_file)
                if s_time > int(sess_tmp):
                    os.remove(sess_file)
            except:
                pass


    
    def setPassword(self,get):
        if get.password1 != get.password2: return public.returnMsg(False,'USER_PASSWORD_CHECK')
        if len(get.password1) < 5: return public.returnMsg(False,'USER_PASSWORD_LEN')
        public.M('users').where("username=?",(session['username'],)).setField('password',public.password_salt(public.md5(get.password1.strip()),username=session['username']))
        public.WriteLog('TYPE_PANEL','USER_PASSWORD_SUCCESS',(session['username'],))
        self.reload_session()
        return public.returnMsg(True,'USER_PASSWORD_SUCCESS')
    
    def setUsername(self,get):
        if get.username1 != get.username2: return public.returnMsg(False,'USER_USERNAME_CHECK')
        if len(get.username1) < 3: return public.returnMsg(False,'USER_USERNAME_LEN')
        public.M('users').where("username=?",(session['username'],)).setField('username',get.username1.strip())
        public.WriteLog('TYPE_PANEL','USER_USERNAME_SUCCESS',(session['username'],get.username2))
        session['username'] = get.username1
        self.reload_session()
        return public.returnMsg(True,'USER_USERNAME_SUCCESS')
    
    #取用户列表
    def get_users(self,args):
        data = public.M('users').field('id,username').select()
        return data

    # 创建新用户
    def create_user(self,args):
        if session['uid'] != 1: return public.returnMsg(False,'没有权限!')
        if len(args.username) < 2: return public.returnMsg(False,'用户名不能少于2位')
        if len(args.password) < 8: return public.returnMsg(False,'密码不能少于8位')
        pdata = {
            "username": args.username.strip(),
            "password": public.password_salt(public.md5(args.password.strip()),username=args.username.strip())
        }

        if(public.M('users').where('username=?',(pdata['username'],)).count()):
            return public.returnMsg(False,'指定用户名已存在!')
        
        if(public.M('users').insert(pdata)):
            public.WriteLog('用户管理','创建新用户{}'.format(pdata['username']))
            return public.returnMsg(True,'创建新用户{}成功!'.format(pdata['username']))
        return public.returnMsg(False,'创建新用户失败!')

    # 删除用户
    def remove_user(self,args):
        if session['uid'] != 1: return public.returnMsg(False,'没有权限!')
        if int(args.id) == 1: return public.returnMsg(False,'不能删除初始默认用户!')
        username = public.M('users').where('id=?',(args.id,)).getField('username')
        if not username: return public.returnMsg(False,'指定用户不存在!')
        if(public.M('users').where('id=?',(args.id,)).delete()):
            public.WriteLog('用户管理','删除用户[{}]'.format(username))
            return public.returnMsg(True,'删除用户{}成功!'.format(username))
        return public.returnMsg(False,'用户删除失败!')

    # 修改用户
    def modify_user(self,args):
        if session['uid'] != 1: return public.returnMsg(False,'没有权限!')
        username = public.M('users').where('id=?',(args.id,)).getField('username')
        pdata = {}
        if 'username' in args:
            if len(args.username) < 2: return public.returnMsg(False,'用户名不能少于2位')
            pdata['username'] = args.username.strip()

        if 'password' in args:
            if args.password:
                if len(args.password) < 8: return public.returnMsg(False,'密码不能少于8位')
                pdata['password'] = public.password_salt(public.md5(args.password.strip()),username=username)

        if(public.M('users').where('id=?',(args.id,)).update(pdata)):
            public.WriteLog('用户管理',"编辑用户{}".format(username))
            return public.returnMsg(True,'修改成功!')
        return public.returnMsg(False,'没有提交修改!')
    
    def setPanel(self,get):
        if not public.IsRestart(): return public.returnMsg(False,'EXEC_ERR_TASK')
        isReWeb = False
        sess_out_path = 'data/session_timeout.pl'
        if 'session_timeout' in get:
            session_timeout = int(get.session_timeout)
            s_time_tmp = public.readFile(sess_out_path)
            if not s_time_tmp: s_time_tmp = '0'
            if int(s_time_tmp) != session_timeout:
                if session_timeout < 300: return public.returnMsg(False,'超时时间不能小于300秒')
                public.writeFile(sess_out_path,str(session_timeout))
                isReWeb = True

        workers_p = 'data/workers.pl'
        if 'workers' in get:
            workers = int(get.workers)
            if int(public.readFile(workers_p)) != workers:
                if workers < 1 or workers > 1024: return public.returnMsg(False,'面板线程数范围应该在1-1024之间')
                public.writeFile(workers_p,str(workers))
                isReWeb = True

        if get.domain:
            reg = r"^([\w\-\*]{1,100}\.){1,4}(\w{1,10}|\w{1,10}\.\w{1,10})$"
            if not re.match(reg, get.domain): return public.returnMsg(False,'SITE_ADD_ERR_DOMAIN')
        oldPort = public.GetHost(True)
        if not 'port' in get:
            get.port = oldPort
        newPort = get.port
        if oldPort != get.port:
            get.port = str(int(get.port))
            if self.IsOpen(get.port):
                return public.returnMsg(False,'PORT_CHECK_EXISTS',(get.port,))
            if int(get.port) >= 65535 or  int(get.port) < 100: return public.returnMsg(False,'PORT_CHECK_RANGE')
            public.writeFile('data/port.pl',get.port)
            import firewalls
            get.ps = public.getMsg('PORT_CHECK_PS')
            fw = firewalls.firewalls()
            fw.AddAcceptPort(get)
            get.port = oldPort
            get.id = public.M('firewall').where("port=?",(oldPort,)).getField('id')
            fw.DelAcceptPort(get)
            isReWeb = True
        
        if get.webname != session['title']: 
            session['title'] = get.webname
            public.SetConfigValue('title',get.webname)

        limitip = public.readFile('data/limitip.conf')
        if get.limitip != limitip: public.writeFile('data/limitip.conf',get.limitip)
        
        public.writeFile('data/domain.conf',get.domain.strip())
        public.writeFile('data/iplist.txt',get.address)
        
        
        public.M('config').where("id=?",('1',)).save('backup_path,sites_path',(get.backup_path,get.sites_path))
        session['config']['backup_path'] = os.path.join('/',get.backup_path)
        session['config']['sites_path'] = os.path.join('/',get.sites_path)
        db_backup  = get.backup_path + '/database'
        if not os.path.exists(db_backup):
            try:
                os.makedirs(db_backup,384)
            except:
                public.ExecShell('mkdir -p ' + db_backup)
        site_backup  = get.backup_path + '/site'
        if not os.path.exists(site_backup):
            try:
                os.makedirs(site_backup,384)
            except:
                public.ExecShell('mkdir -p ' + site_backup)
                
        mhost = public.GetHost()
        if get.domain.strip(): mhost = get.domain
        data = {'uri':request.path,'host':mhost+':'+newPort,'status':True,'isReWeb':isReWeb,'msg':public.getMsg('PANEL_SAVE')}
        public.WriteLog('TYPE_PANEL','PANEL_SET_SUCCESS',(newPort,get.domain,get.backup_path,get.sites_path,get.address,get.limitip))
        if isReWeb: public.restart_panel()
        return data


    def set_admin_path(self,get):
        get.admin_path = get.admin_path.strip()
        if get.admin_path == '': get.admin_path = '/'
        if get.admin_path != '/':
            if len(get.admin_path) < 6: return public.returnMsg(False,'安全入口地址长度不能小于6位!')
            if get.admin_path in admin_path_checks: return public.returnMsg(False,'该入口已被面板占用,请使用其它入口!')
            if not public.path_safe_check(get.admin_path) or get.admin_path[-1] == '.':  return public.returnMsg(False,'入口地址格式不正确,示例: /my_panel')
            if get.admin_path[0] != '/': return public.returnMsg(False,'入口地址格式不正确,示例: /my_panel')
        else:
            get.domain = public.readFile('data/domain.conf')
            if not get.domain: get.domain = ''
            get.limitip = public.readFile('data/limitip.conf')
            if not get.limitip: get.limitip = ''
            if not get.domain.strip() and not get.limitip.strip(): return public.returnMsg(False,'警告，关闭安全入口等于直接暴露你的后台地址在外网，十分危险，至少开启以下一种安全方式才能关闭：<a style="color:red;"><br>1、绑定访问域名<br>2、绑定授权IP</a>')

        admin_path_file = 'data/admin_path.pl'
        admin_path = '/'
        if os.path.exists(admin_path_file): admin_path = public.readFile(admin_path_file).strip()
        if get.admin_path != admin_path:
            public.writeFile(admin_path_file,get.admin_path)
            public.restart_panel()
        return public.returnMsg(True,'修改成功!')
               

    
    def setPathInfo(self,get):
        #设置PATH_INFO
        version = get.version
        type = get.type
        if public.get_webserver() == 'nginx':
            path = public.GetConfigValue('setup_path')+'/nginx/conf/enable-php-'+version+'.conf'
            conf = public.readFile(path)
            rep = r"\s+#*include\s+pathinfo.conf;"
            if type == 'on':
                conf = re.sub(rep,'\n\t\t\tinclude pathinfo.conf;',conf)
            else:
                conf = re.sub(rep,'\n\t\t\t#include pathinfo.conf;',conf)
            public.writeFile(path,conf)
            public.serviceReload()
        
        path = public.GetConfigValue('setup_path')+'/php/'+version+'/etc/php.ini'
        conf = public.readFile(path)
        rep = r"\n*\s*cgi\.fix_pathinfo\s*=\s*([0-9]+)\s*\n"
        status = '0'
        if type == 'on':status = '1'
        conf = re.sub(rep,"\ncgi.fix_pathinfo = "+status+"\n",conf)
        public.writeFile(path,conf)
        public.WriteLog("TYPE_PHP", "PHP_PATHINFO_SUCCESS",(version,type))
        public.phpReload(version)
        return public.returnMsg(True,'SET_SUCCESS')
    
    
    #设置文件上传大小限制
    def setPHPMaxSize(self,get):
        version = get.version
        max = get.max
        
        if int(max) < 2: return public.returnMsg(False,'PHP_UPLOAD_MAX_ERR')
        
        #设置PHP
        path = public.GetConfigValue('setup_path')+'/php/'+version+'/etc/php.ini'
        ols_php_path = '/usr/local/lsws/lsphp{}/etc/php/{}.{}/litespeed/php.ini'.format(get.version, get.version[0],get.version[1])
        if os.path.exists('/etc/redhat-release'):
            ols_php_path = '/usr/local/lsws/lsphp' + get.version + '/etc/php.ini'
        for p in [path,ols_php_path]:
            if not p:
                continue
            if not os.path.exists(p):
                continue
            conf = public.readFile(p)
            rep = r"\nupload_max_filesize\s*=\s*[0-9]+M"
            conf = re.sub(rep,r'\nupload_max_filesize = '+max+'M',conf)
            rep = r"\npost_max_size\s*=\s*[0-9]+M"
            conf = re.sub(rep,r'\npost_max_size = '+max+'M',conf)
            public.writeFile(p,conf)

        if public.get_webserver() == 'nginx':
            #设置Nginx
            path = public.GetConfigValue('setup_path')+'/nginx/conf/nginx.conf'
            conf = public.readFile(path)
            rep = r"client_max_body_size\s+([0-9]+)m"
            tmp = re.search(rep,conf).groups()
            if int(tmp[0]) < int(max):
                conf = re.sub(rep,'client_max_body_size '+max+'m',conf)
                public.writeFile(path,conf)
            
        public.serviceReload()
        public.phpReload(version)
        public.WriteLog("TYPE_PHP", "PHP_UPLOAD_MAX",(version,max))
        return public.returnMsg(True,'SET_SUCCESS')
    
    #设置禁用函数
    def setPHPDisable(self,get):
        filename = public.GetConfigValue('setup_path') + '/php/' + get.version + '/etc/php.ini'
        ols_php_path = '/usr/local/lsws/lsphp{}/etc/php/{}.{}/litespeed/php.ini'.format(get.version, get.version[0],get.version[1])
        if os.path.exists('/etc/redhat-release'):
            ols_php_path = '/usr/local/lsws/lsphp' + get.version + '/etc/php.ini'
        if not os.path.exists(filename): return public.returnMsg(False,'PHP_NOT_EXISTS')
        for file in [filename,ols_php_path]:
            if not os.path.exists(file):
                continue
            phpini = public.readFile(file)
            rep = r"disable_functions\s*=\s*.*\n"
            phpini = re.sub(rep, 'disable_functions = ' + get.disable_functions + "\n", phpini)
            public.WriteLog('TYPE_PHP','PHP_DISABLE_FUNCTION',(get.version,get.disable_functions))
            public.writeFile(file,phpini)
            public.phpReload(get.version)
        public.serviceReload()
        return public.returnMsg(True,'SET_SUCCESS')
    
    #设置PHP超时时间
    def setPHPMaxTime(self,get):
        time = get.time
        version = get.version
        if int(time) < 30 or int(time) > 86400: return public.returnMsg(False,'PHP_TIMEOUT_ERR')
        file = public.GetConfigValue('setup_path')+'/php/'+version+'/etc/php-fpm.conf'
        conf = public.readFile(file)
        rep = r"request_terminate_timeout\s*=\s*([0-9]+)\n"
        conf = re.sub(rep,"request_terminate_timeout = "+time+"\n",conf)   
        public.writeFile(file,conf)
        
        file = '/www/server/php/'+version+'/etc/php.ini'
        phpini = public.readFile(file)
        rep = r"max_execution_time\s*=\s*([0-9]+)\r?\n"
        phpini = re.sub(rep,"max_execution_time = "+time+"\n",phpini)
        rep = r"max_input_time\s*=\s*([0-9]+)\r?\n"
        phpini = re.sub(rep,"max_input_time = "+time+"\n",phpini)
        public.writeFile(file,phpini)
        
        if public.get_webserver() == 'nginx':
            #设置Nginx
            path = public.GetConfigValue('setup_path')+'/nginx/conf/nginx.conf'
            conf = public.readFile(path)
            rep = r"fastcgi_connect_timeout\s+([0-9]+);"
            tmp = re.search(rep, conf).groups()
            if int(tmp[0]) < int(time):
                conf = re.sub(rep,'fastcgi_connect_timeout '+time+';',conf)
                rep = r"fastcgi_send_timeout\s+([0-9]+);"
                conf = re.sub(rep,'fastcgi_send_timeout '+time+';',conf)
                rep = r"fastcgi_read_timeout\s+([0-9]+);"
                conf = re.sub(rep,'fastcgi_read_timeout '+time+';',conf)
                public.writeFile(path,conf)
                
        public.WriteLog("TYPE_PHP", "PHP_TIMEOUT",(version,time))
        public.serviceReload()
        public.phpReload(version)
        return public.returnMsg(True, 'SET_SUCCESS')
    
    
    #取FPM设置
    def getFpmConfig(self,get):
        version = get.version
        file = public.GetConfigValue('setup_path')+"/php/"+version+"/etc/php-fpm.conf"
        conf = public.readFile(file)
        data = {}
        rep = r"\s*pm.max_children\s*=\s*([0-9]+)\s*"
        tmp = re.search(rep, conf).groups()
        data['max_children'] = tmp[0]
        
        rep = r"\s*pm.start_servers\s*=\s*([0-9]+)\s*"
        tmp = re.search(rep, conf).groups()
        data['start_servers'] = tmp[0]
        
        rep = r"\s*pm.min_spare_servers\s*=\s*([0-9]+)\s*"
        tmp = re.search(rep, conf).groups()
        data['min_spare_servers'] = tmp[0]
        
        rep = r"\s*pm.max_spare_servers \s*=\s*([0-9]+)\s*"
        tmp = re.search(rep, conf).groups()
        data['max_spare_servers'] = tmp[0]
        
        rep = r"\s*pm\s*=\s*(\w+)\s*"
        tmp = re.search(rep, conf).groups()
        data['pm'] = tmp[0]
        data['unix'] = 'unix'
        if not isinstance(public.get_fpm_address(version),str):
            data['unix'] = 'tcp'
        
        return data


    #设置
    def setFpmConfig(self,get):
        version = get.version
        max_children = get.max_children
        start_servers = get.start_servers
        min_spare_servers = get.min_spare_servers
        max_spare_servers = get.max_spare_servers
        pm = get.pm
        if not pm in ['static','dynamic','ondemand']:
            return public.returnMsg(False,'错误的运行模式!')
        file = public.GetConfigValue('setup_path')+"/php/"+version+"/etc/php-fpm.conf"
        conf = public.readFile(file)
        
        rep = r"\s*pm.max_children\s*=\s*([0-9]+)\s*"
        conf = re.sub(rep, "\npm.max_children = "+max_children, conf)
        
        rep = r"\s*pm.start_servers\s*=\s*([0-9]+)\s*"
        conf = re.sub(rep, "\npm.start_servers = "+start_servers, conf)
        
        rep = r"\s*pm.min_spare_servers\s*=\s*([0-9]+)\s*"
        conf = re.sub(rep, "\npm.min_spare_servers = "+min_spare_servers, conf)
        
        rep = r"\s*pm.max_spare_servers \s*=\s*([0-9]+)\s*"
        conf = re.sub(rep, "\npm.max_spare_servers = "+max_spare_servers+"\n", conf)
        
        rep = r"\s*pm\s*=\s*(\w+)\s*"
        conf = re.sub(rep, "\npm = "+pm+"\n", conf)
        if pm == 'ondemand':
            if conf.find('listen.backlog = -1') != -1:
                rep = r"\s*listen\.backlog\s*=\s*([0-9-]+)\s*"
                conf = re.sub(rep, "\nlisten.backlog = 8192\n", conf)

        if get.listen == 'unix':
            listen = '/tmp/php-cgi-{}.sock'.format(version)
        else:
            listen = '127.0.0.1:10{}1'.format(version)
            

        rep = r'\s*listen\s*=\s*.+\s*'
        conf = re.sub(rep, "\nlisten = "+listen+"\n", conf)
        
        public.writeFile(file,conf)
        public.phpReload(version)
        public.sync_php_address(version)
        public.WriteLog("TYPE_PHP",'PHP_CHILDREN', (version,max_children,start_servers,min_spare_servers,max_spare_servers))
        return public.returnMsg(True, 'SET_SUCCESS')
    
    #同步时间
    def syncDate(self,get):
        time_str = public.HttpGet(public.GetConfigValue('home') + '/api/index/get_time')
        new_time = int(time_str)
        time_arr = time.localtime(new_time)
        date_str = time.strftime("%Y-%m-%d %H:%M:%S", time_arr)
        public.ExecShell('date -s "%s"' % date_str)
        public.WriteLog("TYPE_PANEL", "DATE_SUCCESS")
        return public.returnMsg(True,"DATE_SUCCESS")
        
    def IsOpen(self,port):
        #检查端口是否占用
        import socket
        s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            s.connect(('127.0.0.1',int(port)))
            s.shutdown(2)
            return True
        except:
            return False
    
    #设置是否开启监控
    def SetControl(self,get):
        try:
            if hasattr(get,'day'): 
                get.day = int(get.day)
                get.day = str(get.day)
                if(get.day < 1): return public.returnMsg(False,"CONTROL_ERR")
        except:
            pass
        
        filename = 'data/control.conf'
        if get.type == '1':
            public.writeFile(filename,get.day)
            public.WriteLog("TYPE_PANEL",'CONTROL_OPEN',(get.day,))
        elif get.type == '0':
            if os.path.exists(filename): os.remove(filename)
            public.WriteLog("TYPE_PANEL", "CONTROL_CLOSE")
        elif get.type == 'del':
            if not public.IsRestart(): return public.returnMsg(False,'EXEC_ERR_TASK')
            os.remove("data/system.db")
            import db
            sql = db.Sql()
            sql.dbfile('system').create('system')
            public.WriteLog("TYPE_PANEL", "CONTROL_CLOSE")
            return public.returnMsg(True,"CONTROL_CLOSE")
            
        else:
            data = {}
            if os.path.exists(filename):
                try:
                    data['day'] = int(public.readFile(filename))
                except:
                    data['day'] = 30
                data['status'] = True
            else:
                data['day'] = 30
                data['status'] = False
            return data
        
        return public.returnMsg(True,"SET_SUCCESS")
    
    #关闭面板
    def ClosePanel(self,get):
        filename = 'data/close.pl'
        if os.path.exists(filename):
            os.remove(filename)
            return public.returnMsg(True,'开启成功')
        public.writeFile(filename,'True')
        public.ExecShell("chmod 600 " + filename)
        public.ExecShell("chown root.root " + filename)
        return public.returnMsg(True,'PANEL_CLOSE')
    
    
    #设置自动更新
    def AutoUpdatePanel(self,get):
        #return public.returnMsg(False,'体验服务器，禁止修改!')
        filename = 'data/autoUpdate.pl'
        if os.path.exists(filename):
            os.remove(filename)
        else:
            public.writeFile(filename,'True')
            public.ExecShell("chmod 600 " + filename)
            public.ExecShell("chown root.root " + filename)
        return public.returnMsg(True,'SET_SUCCESS')
    
    #设置二级密码
    def SetPanelLock(self,get):
        path = 'data/lock'
        if not os.path.exists(path):
            public.ExecShell('mkdir ' + path)
            public.ExecShell("chmod 600 " + path)
            public.ExecShell("chown root.root " + path)
        
        keys = ['files','tasks','config']
        for name in keys:
            filename = path + '/' + name + '.pl'
            if hasattr(get,name):
                public.writeFile(filename,'True')
            else:
                if os.path.exists(filename): os.remove(filename)
                
    #设置PHP守护程序
    def Set502(self,get):
        filename = 'data/502Task.pl'
        if os.path.exists(filename):
            public.ExecShell('rm -f ' + filename)
        else:
            public.writeFile(filename,'True')
        
        return public.returnMsg(True,'SET_SUCCESS')
    
    #设置模板
    def SetTemplates(self,get):
        public.writeFile('data/templates.pl',get.templates)
        return public.returnMsg(True,'SET_SUCCESS')
    
    #设置面板SSL
    def SetPanelSSL(self,get):
        if hasattr(get,"email"):
            #rep_mail = "^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$"
            rep_mail = r"[\w!#$%&'*+/=?^_`{|}~-]+(?:\.[\w!#$%&'*+/=?^_`{|}~-]+)*@(?:[\w](?:[\w-]*[\w])?\.)+[\w](?:[\w-]*[\w])?"
            if not re.search(rep_mail,get.email):
                return public.returnMsg(False,'邮箱格式不合法')
            import setPanelLets
            sp = setPanelLets.setPanelLets()
            sps = sp.set_lets(get)
            return sps
        else:
            sslConf = '/www/server/panel/data/ssl.pl'
            if os.path.exists(sslConf):
                public.ExecShell('rm -f ' + sslConf)
                return public.returnMsg(True,'PANEL_SSL_CLOSE')
            else:
                public.ExecShell('pip install cffi')
                public.ExecShell('pip install cryptography')
                public.ExecShell('pip install pyOpenSSL')
                try:
                    if not self.CreateSSL(): return public.returnMsg(False,'PANEL_SSL_ERR')
                    public.writeFile(sslConf,'True')
                except:
                    return public.returnMsg(False,'PANEL_SSL_ERR')
                return public.returnMsg(True,'PANEL_SSL_OPEN')
    #自签证书
    def CreateSSL(self):
        if os.path.exists('ssl/input.pl'): return True
        import OpenSSL
        key = OpenSSL.crypto.PKey()
        key.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)
        cert = OpenSSL.crypto.X509()
        cert.set_serial_number(0)
        cert.get_subject().CN = public.GetLocalIp()
        cert.set_issuer(cert.get_subject())
        cert.gmtime_adj_notBefore( 0 )
        cert.gmtime_adj_notAfter(86400 * 3650)
        cert.set_pubkey( key )
        cert.sign( key, 'md5' )
        cert_ca = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
        private_key = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key)
        if len(cert_ca) > 100 and len(private_key) > 100:
            public.writeFile('ssl/certificate.pem',cert_ca,'wb+')
            public.writeFile('ssl/privateKey.pem',private_key,'wb+')
            return True
        return False
        
    #生成Token
    def SetToken(self,get):
        data = {}
        data[''] = public.GetRandomString(24)
    
    #取面板列表
    def GetPanelList(self,get):
        try:
            data = public.M('panel').field('id,title,url,username,password,click,addtime').order('click desc').select()
            if type(data) == str: data[111]
            return data
        except:
            sql = '''CREATE TABLE IF NOT EXISTS `panel` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `title` TEXT,
  `url` TEXT,
  `username` TEXT,
  `password` TEXT,
  `click` INTEGER,
  `addtime` INTEGER
);'''
            public.M('sites').execute(sql,())
            return []
    
    #添加面板资料
    def AddPanelInfo(self,get):
        
        #校验是还是重复
        isAdd = public.M('panel').where('title=? OR url=?',(get.title,get.url)).count()
        if isAdd: return public.returnMsg(False,'PANEL_SSL_ADD_EXISTS')
        import time,json
        isRe = public.M('panel').add('title,url,username,password,click,addtime',(get.title,get.url,get.username,get.password,0,int(time.time())))
        if isRe: return public.returnMsg(True,'ADD_SUCCESS')
        return public.returnMsg(False,'ADD_ERROR')
    
    #修改面板资料
    def SetPanelInfo(self,get):
        #校验是还是重复
        isSave = public.M('panel').where('(title=? OR url=?) AND id!=?',(get.title,get.url,get.id)).count()
        if isSave: return public.returnMsg(False,'PANEL_SSL_ADD_EXISTS')
        import time,json
        
        #更新到数据库
        isRe = public.M('panel').where('id=?',(get.id,)).save('title,url,username,password',(get.title,get.url,get.username,get.password))
        if isRe: return public.returnMsg(True,'EDIT_SUCCESS')
        return public.returnMsg(False,'EDIT_ERROR')
    
    #删除面板资料
    def DelPanelInfo(self,get):
        isExists = public.M('panel').where('id=?',(get.id,)).count()
        if not isExists: return public.returnMsg(False,'PANEL_SSL_ADD_NOT_EXISTS')
        public.M('panel').where('id=?',(get.id,)).delete()
        return public.returnMsg(True,'DEL_SUCCESS')
    
    #点击计数
    def ClickPanelInfo(self,get):
        click = public.M('panel').where('id=?',(get.id,)).getField('click')
        public.M('panel').where('id=?',(get.id,)).setField('click',click+1)
        return True
    
    #获取PHP配置参数
    def GetPHPConf(self,get):
        gets = [
                {'name':'short_open_tag','type':1,'ps':public.getMsg('PHP_CONF_1')},
                {'name':'asp_tags','type':1,'ps':public.getMsg('PHP_CONF_2')},
                {'name':'max_execution_time','type':2,'ps':public.getMsg('PHP_CONF_4')},
                {'name':'max_input_time','type':2,'ps':public.getMsg('PHP_CONF_5')},
                {'name':'memory_limit','type':2,'ps':public.getMsg('PHP_CONF_6')},
                {'name':'post_max_size','type':2,'ps':public.getMsg('PHP_CONF_7')},
                {'name':'file_uploads','type':1,'ps':public.getMsg('PHP_CONF_8')},
                {'name':'upload_max_filesize','type':2,'ps':public.getMsg('PHP_CONF_9')},
                {'name':'max_file_uploads','type':2,'ps':public.getMsg('PHP_CONF_10')},
                {'name':'default_socket_timeout','type':2,'ps':public.getMsg('PHP_CONF_11')},
                {'name':'error_reporting','type':3,'ps':public.getMsg('PHP_CONF_12')},
                {'name':'display_errors','type':1,'ps':public.getMsg('PHP_CONF_13')},
                {'name':'cgi.fix_pathinfo','type':0,'ps':public.getMsg('PHP_CONF_14')},
                {'name':'date.timezone','type':3,'ps':public.getMsg('PHP_CONF_15')}
                ]
        phpini_file = '/www/server/php/' + get.version + '/etc/php.ini'
        if public.get_webserver() == 'openlitespeed':
            phpini_file = '/usr/local/lsws/lsphp{}/etc/php/{}.{}/litespeed/php.ini'.format(get.version, get.version[0],get.version[1])
            if os.path.exists('/etc/redhat-release'):
                phpini_file = '/usr/local/lsws/lsphp' + get.version + '/etc/php.ini'
        phpini = public.readFile(phpini_file)
        result = []
        for g in gets:
            rep = g['name'] + r'\s*=\s*([0-9A-Za-z_&/ ~]+)(\s*;?|\r?\n)'
            tmp = re.search(rep,phpini)
            if not tmp: continue
            g['value'] = tmp.groups()[0]
            result.append(g)
        
        return result


    def get_php_config(self,get):
        #取PHP配置
        get.version = get.version.replace('.','')
        file = session['setupPath'] + "/php/"+get.version+"/etc/php.ini"
        if public.get_webserver() == 'openlitespeed':
            file = '/usr/local/lsws/lsphp{}/etc/php/{}.{}/litespeed/php.ini'.format(get.version, get.version[0],get.version[1])
            if os.path.exists('/etc/redhat-release'):
                file = '/usr/local/lsws/lsphp' + get.version + '/etc/php.ini'
        phpini = public.readFile(file)
        file = session['setupPath'] + "/php/"+get.version+"/etc/php-fpm.conf"
        phpfpm = public.readFile(file)
        data = {}
        try:
            rep = r"upload_max_filesize\s*=\s*([0-9]+)M"
            tmp = re.search(rep,phpini).groups()
            data['max'] = tmp[0]
        except:
            data['max'] = '50'
        try:
            rep = r"request_terminate_timeout\s*=\s*([0-9]+)\n"
            tmp = re.search(rep,phpfpm).groups()
            data['maxTime'] = tmp[0]
        except:
            data['maxTime'] = 0
        
        try:
            rep = r"\n;*\s*cgi\.fix_pathinfo\s*=\s*([0-9]+)\s*\n"
            tmp = re.search(rep,phpini).groups()
            
            if tmp[0] == '1':
                data['pathinfo'] = True
            else:
                data['pathinfo'] = False
        except:
            data['pathinfo'] = False
        
        return data
    
    #提交PHP配置参数
    def SetPHPConf(self,get):
        gets = ['display_errors','cgi.fix_pathinfo','date.timezone','short_open_tag','asp_tags','max_execution_time','max_input_time','memory_limit','post_max_size','file_uploads','upload_max_filesize','max_file_uploads','default_socket_timeout','error_reporting']
        filename = '/www/server/php/' + get.version + '/etc/php.ini'
        reload_str = '/etc/init.d/php-fpm-' + get.version + ' reload'
        ols_php_path = '/usr/local/lsws/lsphp{}/etc/php/{}.{}/litespeed/php.ini'.format(get.version, get.version[0],get.version[1])
        if os.path.exists('/etc/redhat-release'):
            ols_php_path = '/usr/local/lsws/lsphp' + get.version + '/etc/php.ini'
        reload_ols_str = '/usr/local/lsws/bin/lswsctrl restart'
        for p in [filename,ols_php_path]:
            if not p:
                continue
            if not os.path.exists(p):
                continue
            phpini = public.readFile(p)
            for g in gets:
                try:
                    rep = g + r'\s*=\s*(.+)\r?\n'
                    val = g+' = ' + get[g] + '\n'
                    phpini = re.sub(rep,val,phpini)
                except: continue

            public.writeFile(p,phpini)
        public.ExecShell(reload_str)
        public.ExecShell(reload_ols_str)
        return public.returnMsg(True,'SET_SUCCESS')
    
  
 # 取Session缓存方式
    def GetSessionConf(self,get):
        filename = '/www/server/php/' + get.version + '/etc/php.ini'
        if public.get_webserver() == 'openlitespeed':
            filename = '/usr/local/lsws/lsphp{}/etc/php/{}.{}/litespeed/php.ini'.format(get.version,get.version[0],get.version[1])
            if os.path.exists('/etc/redhat-release'):
                filename = '/usr/local/lsws/lsphp' + get.version + '/etc/php.ini'
        phpini = public.readFile(filename)
        rep = r'session.save_handler\s*=\s*([0-9A-Za-z_& ~]+)(\s*;?|\r?\n)'
        save_handler = re.search(rep, phpini)
        if save_handler:
            save_handler = save_handler.group(1)
        else:
            save_handler = "files"

        reppath = r'\nsession.save_path\s*=\s*"tcp\:\/\/([\d\.]+):(\d+).*\r?\n'
        passrep = r'\nsession.save_path\s*=\s*"tcp://[\w\.\?\:]+=(.*)"\r?\n'
        memcached = r'\nsession.save_path\s*=\s*"([\d\.]+):(\d+)"'
        save_path = re.search(reppath, phpini)
        if not save_path:
            save_path = re.search(memcached, phpini)
        passwd = re.search(passrep, phpini)
        port = ""
        if passwd:
            passwd = passwd.group(1)
        else:
            passwd = ""
        if save_path:
            port = save_path.group(2)
            save_path = save_path.group(1)

        else:
            save_path = ""
        return {"save_handler": save_handler, "save_path": save_path, "passwd": passwd, "port": port}

    # 设置Session缓存方式
    def SetSessionConf(self, get):
        import glob
        g = get.save_handler
        ip = get.ip
        port = get.port
        passwd = get.passwd
        if g != "files":
            iprep = r"(2(5[0-5]{1}|[0-4]\d{1})|[0-1]?\d{1,2})\.(2(5[0-5]{1}|[0-4]\d{1})|[0-1]?\d{1,2})\.(2(5[0-5]{1}|[0-4]\d{1})|[0-1]?\d{1,2})\.(2(5[0-5]{1}|[0-4]\d{1})|[0-1]?\d{1,2})"
            if not re.search(iprep, ip):
                return public.returnMsg(False, '请输入正确的IP地址')
            try:
                port = int(port)
                if port >= 65535 or port < 1:
                    return public.returnMsg(False, '请输入正确的端口号')
            except:
                return public.returnMsg(False, '请输入正确的端口号')
            prep = r"[\~\`\/\=]"
            if re.search(prep,passwd):
                return public.returnMsg(False, '请不要输入以下特殊字符 " ~ ` / = "')
        filename = '/www/server/php/' + get.version + '/etc/php.ini'
        filename_ols = None
        if os.path.exists("/usr/local/lsws"):
            filename_ols = '/usr/local/lsws/lsphp{}/etc/php/{}.{}/litespeed/php.ini'.format(get.version, get.version[0],
                                                                                        get.version[1])
            if os.path.exists('/etc/redhat-release'):
                filename_ols = '/usr/local/lsws/lsphp' + get.version + '/etc/php.ini'
            try:
                ols_php_os_path = glob.glob("/usr/local/lsws/lsphp{}/lib/php/20*".format(get.version))[0]
            except:
                ols_php_os_path = None
            if os.path.exists("/etc/redhat-release"):
                ols_php_os_path = '/usr/local/lsws/lsphp{}/lib64/php/modules/'.format(get.version)
            ols_so_list = os.listdir(ols_php_os_path)
        else:
            ols_so_list = []
        for f in [filename,filename_ols]:
            if not f:
                continue
            phpini = public.readFile(f)
            rep = r'session.save_handler\s*=\s*(.+)\r?\n'
            val = r'session.save_handler = ' + g + '\n'
            phpini = re.sub(rep, val, phpini)
            if g == "memcached":
                if not re.search("memcached.so", phpini) and "memcached.so" not in ols_so_list:
                    return public.returnMsg(False, '请先安装%s扩展' % g)
                rep = r'\nsession.save_path\s*=\s*(.+)\r?\n'
                val = r'\nsession.save_path = "%s:%s" \n' % (ip,port)
                if re.search(rep, phpini):
                    phpini = re.sub(rep, val, phpini)
                else:
                    phpini = re.sub('\n;session.save_path = "/tmp"', '\n;session.save_path = "/tmp"' + val, phpini)
            if g == "memcache":
                if not re.search("memcache.so", phpini) and "memcache.so" not in ols_so_list:
                    return public.returnMsg(False, '请先安装%s扩展' % g)
                rep = r'\nsession.save_path\s*=\s*(.+)\r?\n'
                val = r'\nsession.save_path = "tcp://%s:%s"\n' % (ip, port)
                if re.search(rep, phpini):
                    phpini = re.sub(rep, val, phpini)
                else:
                    phpini = re.sub('\n;session.save_path = "/tmp"', '\n;session.save_path = "/tmp"' + val, phpini)
            if g == "redis":
                if not re.search("redis.so", phpini) and "redis.so" not in ols_so_list:
                    return public.returnMsg(False, '请先安装%s扩展' % g)
                if passwd:
                    passwd = "?auth=" + passwd
                else:
                    passwd = ""
                rep = r'\nsession.save_path\s*=\s*(.+)\r?\n'
                val = r'\nsession.save_path = "tcp://%s:%s%s"\n' % (ip, port, passwd)
                res = re.search(rep, phpini)
                if res:
                    phpini = re.sub(rep, val, phpini)
                else:
                    phpini = re.sub('\n;session.save_path = "/tmp"', '\n;session.save_path = "/tmp"' + val, phpini)
            if g == "files":
                rep = r'\nsession.save_path\s*=\s*(.+)\r?\n'
                val = r'\nsession.save_path = "/tmp"\n'
                if re.search(rep, phpini):
                    phpini = re.sub(rep, val, phpini)
                else:
                    phpini = re.sub('\n;session.save_path = "/tmp"', '\n;session.save_path = "/tmp"' + val, phpini)
            public.writeFile(f, phpini)
        public.ExecShell('/etc/init.d/php-fpm-' + get.version + ' reload')
        public.serviceReload()
        return public.returnMsg(True, 'SET_SUCCESS')

    # 获取Session文件数量
    def GetSessionCount(self, get):
        d=["/tmp","/www/php_session"]
        
        count = 0
        for i in d:
            if not os.path.exists(i): public.ExecShell('mkdir -p %s'%i)
            list = os.listdir(i)
            for l in list:
                if os.path.isdir(i+"/"+l):
                    l1 = os.listdir(i+"/"+l)
                    for ll in l1:
                        if "sess_" in ll:
                            count += 1
                    continue
                if "sess_" in l:
                    count += 1

        s = "find /tmp -mtime +1 |grep 'sess_'|wc -l"
        old_file = int(public.ExecShell(s)[0].split("\n")[0])

        s = "find /www/php_session -mtime +1 |grep 'sess_'|wc -l"
        old_file += int(public.ExecShell(s)[0].split("\n")[0])

        return {"total":count,"oldfile":old_file}

    # 删除老文件
    def DelOldSession(self,get):
        s = "find /tmp -mtime +1 |grep 'sess_'|xargs rm -f"
        public.ExecShell(s)
        s = "find /www/php_session -mtime +1 |grep 'sess_'|xargs rm -f"
        public.ExecShell(s)
        # s = "find /tmp -mtime +1 |grep 'sess_'|wc -l"
        # old_file_conf = int(public.ExecShell(s)[0].split("\n")[0])
        old_file_conf = self.GetSessionCount(get)["oldfile"]
        if old_file_conf == 0:
            return public.returnMsg(True, '清理成功')
        else:
            return public.returnMsg(True, '清理失败')
  
    #获取面板证书
    def GetPanelSSL(self,get):
        cert = {}
        cert['privateKey'] = public.readFile('ssl/privateKey.pem')
        cert['certPem'] = public.readFile('ssl/certificate.pem')
        cert['rep'] = os.path.exists('ssl/input.pl')
        return cert
    
    #保存面板证书
    def SavePanelSSL(self,get):
        keyPath = 'ssl/privateKey.pem'
        certPath = 'ssl/certificate.pem'
        checkCert = '/tmp/cert.pl'
        public.writeFile(checkCert,get.certPem)
        if get.privateKey:
            public.writeFile(keyPath,get.privateKey)
        if get.certPem:
            public.writeFile(certPath,get.certPem)
        if not public.CheckCert(checkCert): return public.returnMsg(False,'证书错误,请检查!')
        public.writeFile('ssl/input.pl','True')
        return public.returnMsg(True,'证书已保存!')


    #获取配置
    def get_config(self,get):
        if 'config' in session:
            session['config']['distribution'] = public.get_linux_distribution()
            session['webserver'] = public.get_webserver()
            session['config']['webserver'] = session['webserver']
            return session['config']
        data = public.M('config').where("id=?",('1',)).field('webserver,sites_path,backup_path,status,mysql_root').find()
        data['webserver'] = public.get_webserver()
        data['distribution'] = public.get_linux_distribution()
        return data
    

    #取面板错误日志
    def get_error_logs(self,get):
        return public.GetNumLines('logs/error.log',2000)

    def is_pro(self,get):
        import panelAuth,json
        pdata = panelAuth.panelAuth().create_serverid(None)
        url = public.GetConfigValue('home') + '/api/panel/is_pro'
        pluginTmp = public.httpPost(url,pdata)
        pluginInfo = json.loads(pluginTmp)
        return pluginInfo

    def get_token(self,get):
        import panelApi
        return panelApi.panelApi().get_token(get)

    def set_token(self,get):
        import panelApi
        return panelApi.panelApi().set_token(get)

    def get_tmp_token(self,get):
        import panelApi
        return panelApi.panelApi().get_tmp_token(get)

    def GetNginxValue(self,get):
        n = nginx.nginx()
        return n.GetNginxValue()

    def SetNginxValue(self,get):
        n = nginx.nginx()
        return n.SetNginxValue(get)

    def GetApacheValue(self,get):
        a = apache.apache()
        return a.GetApacheValue()

    def SetApacheValue(self,get):
        a = apache.apache()
        return a.SetApacheValue(get)

    def get_ols_value(self,get):
        a = ols.ols()
        return a.get_value(get)

    def set_ols_value(self,get):
        a = ols.ols()
        return a.set_value(get)

    def get_ols_private_cache(self,get):
        a = ols.ols()
        return a.get_private_cache(get)

    def get_ols_static_cache(self,get):
        a = ols.ols()
        return a.get_static_cache(get)

    def set_ols_static_cache(self,get):
        a = ols.ols()
        return a.set_static_cache(get)

    def switch_ols_private_cache(self,get):
        a = ols.ols()
        return a.switch_private_cache(get)

    def set_ols_private_cache(self,get):
        a = ols.ols()
        return a.set_private_cache(get)

    def get_ols_private_cache_status(self,get):
        a = ols.ols()
        return a.get_private_cache_status(get)

    def get_ipv6_listen(self,get):
        return os.path.exists('data/ipv6.pl')

    def set_ipv6_status(self,get):
        ipv6_file = 'data/ipv6.pl'
        if self.get_ipv6_listen(get):
            os.remove(ipv6_file)
            public.WriteLog('面板设置','关闭面板IPv6兼容!')
        else:
            public.writeFile(ipv6_file,'True')
            public.WriteLog('面板设置','开启面板IPv6兼容!')
        public.restart_panel()
        return public.returnMsg(True,'设置成功!')

    #自动补充CLI模式下的PHP版本
    def auto_cli_php_version(self,get):
        import panelSite
        php_versions = panelSite.panelSite().GetPHPVersion(get)
        php_bin_src = "/www/server/php/%s/bin/php" % php_versions[-1]['version']
        if not os.path.exists(php_bin_src): return public.returnMsg(False,'未安装PHP!')
        get.php_version = php_versions[-1]['version']
        self.set_cli_php_version(get)
        return php_versions[-1]

    #获取CLI模式下的PHP版本
    def get_cli_php_version(self,get):
        php_bin = '/usr/bin/php'
        if not os.path.exists(php_bin) or not os.path.islink(php_bin):  return self.auto_cli_php_version(get)
        link_re = os.readlink(php_bin)
        if not os.path.exists(link_re): return self.auto_cli_php_version(get)
        import panelSite
        php_versions = panelSite.panelSite().GetPHPVersion(get)
        if len(php_versions)==0:
            return public.returnMsg(False,'获取失败!')
        del(php_versions[0])
        for v in php_versions:
            if link_re.find(v['version']) != -1: return {"select":v,"versions":php_versions}
        return {"select":self.auto_cli_php_version(get),"versions":php_versions}

    #设置CLI模式下的PHP版本
    def set_cli_php_version(self,get):
        php_bin = '/usr/bin/php'
        php_bin_src = "/www/server/php/%s/bin/php" % get.php_version
        php_ize = '/usr/bin/phpize'
        php_ize_src = "/www/server/php/%s/bin/phpize" % get.php_version
        php_fpm = '/usr/bin/php-fpm'
        php_fpm_src = "/www/server/php/%s/sbin/php-fpm" % get.php_version
        php_pecl = '/usr/bin/pecl'
        php_pecl_src = "/www/server/php/%s/bin/pecl" % get.php_version
        php_pear = '/usr/bin/pear'
        php_pear_src = "/www/server/php/%s/bin/pear" % get.php_version
        if not os.path.exists(php_bin_src): return public.returnMsg(False,'指定PHP版本未安装!')
        is_chattr = public.ExecShell('lsattr /usr|grep /usr/bin')[0].find('-i-')
        if is_chattr != -1: public.ExecShell('chattr -i /usr/bin')
        public.ExecShell("rm -f " + php_bin + ' '+ php_ize + ' ' + php_fpm + ' ' + php_pecl + ' ' + php_pear)
        public.ExecShell("ln -sf %s %s" % (php_bin_src,php_bin))
        public.ExecShell("ln -sf %s %s" % (php_ize_src,php_ize))
        public.ExecShell("ln -sf %s %s" % (php_fpm_src,php_fpm))
        public.ExecShell("ln -sf %s %s" % (php_pecl_src,php_pecl))
        public.ExecShell("ln -sf %s %s" % (php_pear_src,php_pear))
        if is_chattr != -1:  public.ExecShell('chattr +i /usr/bin')
        public.WriteLog('面板设置','设置PHP-CLI版本为: %s' % get.php_version)
        return public.returnMsg(True,'设置成功!')

    
    #获取BasicAuth状态
    def get_basic_auth_stat(self,get):
        path = 'config/basic_auth.json'
        is_install = True
        result = {"basic_user":"","basic_pwd":"","open":False,"is_install":is_install}
        if not os.path.exists(path): return result
        try:
            ba_conf = json.loads(public.readFile(path))
        except: 
            os.remove(path)
            return result
        ba_conf['is_install'] = is_install
        return ba_conf

    #设置BasicAuth
    def set_basic_auth(self,get):
        is_open = False
        if get.open == 'True': is_open = True
        tips = '_bt.cn'
        path = 'config/basic_auth.json'
        ba_conf = None
        if os.path.exists(path):
            try:
                ba_conf = json.loads(public.readFile(path))
            except:
                os.remove(path)

        if not ba_conf: 
            ba_conf = {"basic_user":public.md5(get.basic_user.strip() + tips),"basic_pwd":public.md5(get.basic_pwd.strip() + tips),"open":is_open}
        else:
            if get.basic_user: ba_conf['basic_user'] = public.md5(get.basic_user.strip() + tips)
            if get.basic_pwd: ba_conf['basic_pwd'] = public.md5(get.basic_pwd.strip() + tips)
            ba_conf['open'] = is_open
        
        public.writeFile(path,json.dumps(ba_conf))
        os.chmod(path,384)
        public.WriteLog('面板设置','设置BasicAuth状态为: %s' % is_open)
        public.writeFile('data/reload.pl','True')
        return public.returnMsg(True,"设置成功!")

    #取面板运行日志
    def get_panel_error_logs(self,get):
        filename = 'logs/error.log'
        if not os.path.exists(filename): return public.returnMsg(False,'没有找到运行日志')
        result = public.GetNumLines(filename,2000)
        return public.returnMsg(True,result)
    #清空面板运行日志
    def clean_panel_error_logs(self,get):
        filename = 'logs/error.log'
        public.writeFile(filename,'')
        public.WriteLog('面板配置','清空面板运行日志')
        return public.returnMsg(True,'已清空!')

    # 获取lets证书
    def get_cert_source(self,get):
        import setPanelLets
        sp = setPanelLets.setPanelLets()
        spg = sp.get_cert_source()
        return spg

    #设置debug模式
    def set_debug(self,get):
        debug_path = 'data/debug.pl'
        if os.path.exists(debug_path):
            t_str = '关闭'
            os.remove(debug_path)
        else:
            t_str = '开启'
            public.writeFile(debug_path,'True')
        public.WriteLog('面板配置','%s开发者模式(debug)' % t_str)
        public.restart_panel()
        return public.returnMsg(True,'设置成功!')


    #设置离线模式
    def set_local(self,get):
        d_path = 'data/not_network.pl'
        if os.path.exists(d_path):
            t_str = '关闭'
            os.remove(d_path)
        else:
            t_str = '开启'
            public.writeFile(d_path,'True')
        public.WriteLog('面板配置','%s离线模式' % t_str)
        return public.returnMsg(True,'设置成功!')
        
    # 修改.user.ini文件
    def _edit_user_ini(self,file,s_conf,act,session_path):
        public.ExecShell("chattr -i {}".format(file))
        conf = public.readFile(file)
        if act == "1":
            if "session.save_path" in conf:
                return False
            conf = conf + ":{}/".format(session_path)
            conf = conf + "\n" + s_conf
        else:
            rep = "\n*session.save_path(.|\n)*files"
            rep1 = ":{}".format(session_path)
            conf = re.sub(rep,"",conf)
            conf = re.sub(rep1,"",conf)
        public.writeFile(file, conf)
        public.ExecShell("chattr +i {}".format(file))

    # 设置php_session存放到独立文件夹
    def set_php_session_path(self,get):
        '''
        get.id      site id
        get.act     0/1
        :param get:
        :return:
        '''
        if public.get_webserver() == 'openlitespeed':
            return public.returnMsg(False, "该功能暂时不支持OpenLiteSpeed")
        import panelSite
        site_info = public.M('sites').where('id=?', (get.id,)).field('name,path').find()
        session_path = "/www/php_session/{}".format(site_info["name"])
        if not os.path.exists(session_path):
            os.makedirs(session_path)
            public.ExecShell('chown www.www {}'.format(session_path))
        run_path = panelSite.panelSite().GetSiteRunPath(get)["runPath"]
        user_ini_file = "{site_path}{run_path}/.user.ini".format(site_path=site_info["path"], run_path=run_path)
        conf = "session.save_path={}/\nsession.save_handler = files".format(session_path)
        if get.act == "1":
            if not os.path.exists(user_ini_file):
                public.writeFile(user_ini_file,conf)
                public.ExecShell("chattr +i {}".format(user_ini_file))
                return public.returnMsg(True,"设置成功")
            self._edit_user_ini(user_ini_file,conf,get.act,session_path)
            return public.returnMsg(True, "设置成功")
        else:
            self._edit_user_ini(user_ini_file,conf,get.act,session_path)
            return public.returnMsg(True, "设置成功")

    # 获取php_session是否存放到独立文件夹
    def get_php_session_path(self,get):
        import panelSite
        site_info = public.M('sites').where('id=?', (get.id,)).field('name,path').find()
        run_path = panelSite.panelSite().GetSiteRunPath(get)["runPath"]
        user_ini_file = "{site_path}{run_path}/.user.ini".format(site_path=site_info["path"], run_path=run_path)
        conf = public.readFile(user_ini_file)
        if conf and "session.save_path" in conf:
            return True
        return False
        
    def _create_key(self):
        get_token = pyotp.random_base32() # returns a 16 character base32 secret. Compatible with Google Authenticator
        public.writeFile(self._key_file,get_token)
        username = self.get_random()
        public.writeFile(self._username_file, username)

    def get_key(self,get):
        key = public.readFile(self._key_file)
        username = public.readFile(self._username_file)
        if not key:
            return public.returnMsg(False, "秘钥不存在，请开启后再试")
        if not username:
            return public.returnMsg(False, "用户名不存在，请开启后再试")
        return {"key":key,"username":username}

    def get_random(self):
        import random
        seed = "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        sa = []
        for _ in range(8):
            sa.append(random.choice(seed))
        salt = ''.join(sa)
        return salt

    def set_two_step_auth(self,get):
        if not hasattr(get,"act") or not get.act:
            return public.returnMsg(False, "请输入操作方式")
        if get.act == "1":
            if not os.path.exists(self._core_fle_path):
                os.makedirs(self._core_fle_path)
            username = public.readFile(self._username_file)
            if not os.path.exists(self._bk_key_file):
                secret_key = public.readFile(self._key_file)
                if not secret_key or not username:
                    self._create_key()
            else:
                os.rename(self._bk_key_file,self._key_file)
            secret_key = public.readFile(self._key_file)
            username = public.readFile(self._username_file)
            local_ip = public.GetLocalIp()
            if not secret_key:
                return public.returnMsg(False,"生成key或username失败，请检查硬盘空间是否不足或目录无法写入[ {} ]".format(self._setup_path+"/data/"))
            try:
                data = pyotp.totp.TOTP(secret_key).provisioning_uri(username, issuer_name=local_ip)
                public.writeFile(self._core_fle_path+'/qrcode.txt',str(data))
                return public.returnMsg(True, "开启成功")
            except Exception as e:
                return public.returnMsg(False, e)
        else:
            if os.path.exists(self._key_file):
                os.rename(self._key_file,self._bk_key_file)
            return public.returnMsg(True, "关闭成功")

    # 检测是否开启双因素验证
    def check_two_step(self,get):
        secret_key = public.readFile(self._key_file)
        if not secret_key:
            return public.returnMsg(False, "没有开启二步验证")
        return public.returnMsg(True, "已经开启二步验证")
        
    # 读取二维码data
    def get_qrcode_data(self,get):
        data = public.readFile(self._core_fle_path + '/qrcode.txt')
        if data:
            return data
        return public.returnMsg(True, "没有二维码数据，请重新开启")

    # 设置是否云控打开
    def set_coll_open(self,get):
        if not 'coll_show' in get: return public.returnMsg(False,'错误的参数!')
        if get.coll_show == 'True':
            session['tmp_login'] = True
        else:
            session['tmp_login'] = False
        return public.returnMsg(True,'设置成功!')


    # 是否显示软件推荐
    def show_recommend(self,get):
        pfile = 'data/not_recommend.pl'
        if os.path.exists(pfile):
            os.remove(pfile)
        else:
            public.writeFile(pfile,'True')
        return public.returnMsg(True,'设置成功!')

    # 是否显示工单
    def show_workorder(self,get):
        pfile = 'data/not_workorder.pl'
        if os.path.exists(pfile):
            os.remove(pfile)
        else:
            public.writeFile(pfile,'True')
        return public.returnMsg(True,'设置成功!')

    # 获取菜单列表
    def get_menu_list(self,get):
        '''
            @name 获取菜单列表
            @author hwliang<2020-08-31>
            @param get<dict_obj>
            @return list
        '''
        menu_file = 'config/menu.json'
        hide_menu_file = 'config/hide_menu.json'
        data = json.loads(public.ReadFile(menu_file))
        if not os.path.exists(hide_menu_file):
            public.writeFile(hide_menu_file,'[]')
        hide_menu = public.ReadFile(hide_menu_file)
        if not hide_menu:
            hide_menu = []
        else:
            hide_menu = json.loads(hide_menu)
        result = []
        for d in data:
            tmp = {}
            tmp['id'] = d['id']
            tmp['title'] = d['title']
            tmp['show'] = not d['id'] in hide_menu
            tmp['sort'] = d['sort']
            result.append(tmp)
        
        menus = sorted(result, key=lambda x: x['sort'])
        return menus

    
    # 设置隐藏菜单列表
    def set_hide_menu_list(self,get):
        '''
            @name 设置隐藏菜单列表
            @author hwliang<2020-08-31>
            @param get<dict_obj> {
                hide_list: json<list> 所有不显示的菜单ID
            }
            @return dict
        '''
        hide_menu_file = 'config/hide_menu.json'
        not_hide_id = ["dologin","memuAconfig","memuAsoft","memuA"] #禁止隐藏的菜单

        hide_list = json.loads(get.hide_list)
        hide_menu = []
        for h in hide_list:
            if h in not_hide_id:continue
            hide_menu.append(h)
        public.writeFile(hide_menu_file,json.dumps(hide_menu))
        public.WriteLog('面板设置','修改面板菜单显示列表成功')
        return public.returnMsg(True,'设置成功')
    

    #获取临时登录列表
    def get_temp_login(self,args):
        '''
            @name 获取临时登录列表
            @author hwliang<2020-09-2>
            @return dict
        '''
        if 'tmp_login_expire' in session: return public.returnMsg(False,'没有权限')
        public.M('temp_login').where('state=? and expire<?',(0,int(time.time()))).setField('state',-1)
        callback = ''
        if 'tojs' in args:
            callback = args.tojs
        p = 1
        if 'p' in args:
            p = int(args.p)
        rows =12
        if 'rows' in args:
            rows = int(args.rows)
        count = public.M('temp_login').count()
        data = {}
        page_data = public.get_page(count,p,rows,callback)
        data['page'] = page_data['page']
        data['data'] = public.M('temp_login').limit(page_data['shift'] + ',' + page_data['row']).order('id desc').field('id,addtime,expire,login_time,login_addr,state').select()
        for i in range(len(data['data'])):
            data['data'][i]['online_state'] = os.path.exists('data/session/{}'.format(data['data'][i]['id']))
        return data

    #设置临时登录
    def set_temp_login(self,args):
        '''
            @name 设置临时登录
            @author hwliang<2020-09-2>
            @return dict
        '''
        if 'tmp_login_expire' in session: return public.returnMsg(False,'没有权限')
        s_time = int(time.time())
        public.M('temp_login').where('state=? and expire>?',(0,s_time)).delete()
        token = public.GetRandomString(48)
        salt = public.GetRandomString(12)
        
        pdata = {
            'token': public.md5(token + salt),
            'salt': salt,
            'state':0,
            'login_time':0,
            'login_addr':'',
            'expire':s_time + 3600,
            'addtime':s_time
        }

        if not public.M('temp_login').count():
            pdata['id'] = 101

        if public.M('temp_login').insert(pdata):
            public.WriteLog('面板设置','生成临时连接,过期时间:{}'.format(public.format_date(times = pdata['expire'])))
            return {'status':True,'msg':"临时连接已生成",'token':token,'expire':pdata['expire']}
        return public.returnMsg(False,'连接生成失败')

    #删除临时登录
    def remove_temp_login(self,args):
        '''
            @name 删除临时登录
            @author hwliang<2020-09-2>
            @param args<dict_obj>{
                id: int<临时登录ID>
            }
            @return dict
        '''
        if 'tmp_login_expire' in session: return public.returnMsg(False,'没有权限')
        id = int(args.id)
        if public.M('temp_login').where('id=?',(id,)).delete():
            public.WriteLog('面板设置','删除临时登录连接')
            return public.returnMsg(True,'删除成功')
        return public.returnMsg(False,'删除失败')


    #强制弹出指定临时登录
    def clear_temp_login(self,args):
        '''
            @name 强制登出
            @author hwliang<2020-09-2>
            @param args<dict_obj>{
                id: int<临时登录ID>
            }
            @return dict
        '''
        if 'tmp_login_expire' in session: return public.returnMsg(False,'没有权限')
        id = int(args.id)
        s_file = 'data/session/{}'.format(id)
        if os.path.exists(s_file):
            os.remove(s_file)
            public.WriteLog('面板设置','强制弹出临时用户：{}'.format(id))
            return public.returnMsg(True,'已强制退出临时用户：{}'.format(id))
        public.returnMsg(False,'指定用户当前不是登录状态!')


    #查看临时授权操作日志
    def get_temp_login_logs(self,args):
        '''
            @name 查看临时授权操作日志
            @author hwliang<2020-09-2>
            @param args<dict_obj>{
                id: int<临时登录ID>
            }
            @return dict
        '''
        if 'tmp_login_expire' in session: return public.returnMsg(False,'没有权限')
        id = int(args.id)
        data = public.M('logs').where('uid=?',(id,)).order('id desc').select()
        return data

    def get_file_deny(self,args):
        import file_execute_deny
        p = file_execute_deny.FileExecuteDeny()
        return p.get_file_deny(args)

    def set_file_deny(self,args):
        import file_execute_deny
        p = file_execute_deny.FileExecuteDeny()
        return p.set_file_deny(args)

    def del_file_deny(self,args):
        import file_execute_deny
        p = file_execute_deny.FileExecuteDeny()
        return p.del_file_deny(args)