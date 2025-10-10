# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 x3
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2017 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------
import base64
import sys
import traceback
import public, re, os, nginx, apache, json, time, ols
import PluginLoader
from theme_config import ThemeConfigManager

try:
    import pyotp
except:
    public.ExecShell("pip install pyotp &")
try:
    from BTPanel import session, admin_path_checks, g, request, cache
    import send_mail
    import requests
except:
    pass


class config:
    _setup_path = "/www/server/panel"
    _key_file = _setup_path + "/data/two_step_auth.txt"
    _bk_key_file = _setup_path + "/data/bk_two_step_auth.txt"
    _username_file = _setup_path + "/data/username.txt"
    _core_fle_path = _setup_path + '/data/qrcode'
    __mail_config = '/www/server/panel/data/stmp_mail.json'
    __mail_list_data = '/www/server/panel/data/mail_list.json'
    __dingding_config = '/www/server/panel/data/dingding.json'
    __panel_asset_config = '/www/server/panel/data/panel_asset.json'
    __mail_list = []
    __weixin_user = []



    __menu_dict = {i["id"]: i["href"] for i in public.get_menu()}

    def __init__(self):
        try:
            self.themeManager = ThemeConfigManager(self.__panel_asset_config)
            
            ssl_dir = os.path.join(self._setup_path, "ssl")
            if not os.path.exists(ssl_dir):
                os.makedirs(ssl_dir)

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
        except:
            pass

    """
    @
    """

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

    # 添加接受邮件地址
    def add_mail_address(self, get):
        if not hasattr(get, 'email'): return public.returnMsg(False, '请输入邮箱')
        emailformat = re.compile(r'[a-zA-Z0-9.-_+%]+@[a-zA-Z0-9]+\.[a-zA-Z0-9]+')
        if not emailformat.search(get.email): return public.returnMsg(False, '请输入正确的邮箱')
        # 测试发送邮件
        if get.email.strip() in self.__mail_list: return public.returnMsg(False, '邮箱已经存在')
        self.__mail_list.append(get.email.strip())
        public.writeFile(self.__mail_list_data, json.dumps(self.__mail_list))
        return public.returnMsg(True, '添加成功')

    # 添加自定义邮箱地址
    def user_mail_send(self, get):
        if not (hasattr(get, 'email') or hasattr(get, 'stmp_pwd') or hasattr(get, 'hosts') or hasattr(get, 'port')):
            return public.returnMsg(False, '请填写完整信息')
        # 自定义邮件
        self.mail.qq_stmp_insert(get.email.strip(), get.stmp_pwd.strip(), get.hosts.strip(), get.port.strip())
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
        if not 'port' in qq_mail_info: qq_mail_info['port'] = 465
        return public.returnMsg(True, qq_mail_info)

    # 清空数据
    def set_empty(self, get):
        type = get.type.strip()
        if type == 'dingding':
            ret = []
            public.writeFile(self.__dingding_config, json.dumps(ret))
            return public.returnMsg(True, '清空成功')
        else:
            ret = []
            public.writeFile(self.__mail_config, json.dumps(ret))
            return public.returnMsg(True, '清空成功')

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
        sm = send_mail.send_mail()
        return sm.get_settings()

    # 设置钉钉报警
    def set_dingding(self, get):
        if not (hasattr(get, 'url') or hasattr(get, 'atall')):
            return public.returnMsg(False, '请填写完整信息')
        if get.atall == 'True' or get.atall == '1':
            get.atall = 'True'
        else:
            get.atall = 'False'
        push_url = get.url.strip()
        channel = "dingding"
        if push_url.find("weixin.qq.com") != -1:
            channel = "weixin"
        msg = ""
        try:
            from panelMessage import panelMessage
            pm = panelMessage()
            if hasattr(pm, "init_msg_module"):
                msg_module = pm.init_msg_module(channel)
                if msg_module:
                    _res = msg_module.set_config(get)
                    if _res["status"]:
                        return _res
        except Exception as e:
            msg = str(e)
            print("设置钉钉配置异常: {}".format(msg))
        if not msg:
            return public.returnMsg(False, '添加失败,请查看URL是否正确!')
        else:
            return public.returnMsg(False, msg)

    # 查看钉钉
    def get_dingding(self, get):
        sm = send_mail.send_mail()
        return sm.get_dingding()

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

    def getPanelState(self, get):
        return os.path.exists('/www/server/panel/data/close.pl')

    def reload_session(self):
        userInfo = public.M('users').where("id=?", (1,)).field('username,password').find()
        token = public.Md5(userInfo['username'] + '/' + userInfo['password'])
        public.writeFile('/www/server/panel/data/login_token.pl', token)
        skey = 'login_token'
        cache.set(skey, token)
        sess_path = 'data/sess_files'
        if not os.path.exists(sess_path):
            os.makedirs(sess_path, 384)
        self.clean_sess_files(sess_path)
        sess_key = public.get_sess_key()
        sess_file = os.path.join(sess_path, sess_key)
        public.writeFile(sess_file, str(int(time.time() + 86400)))
        public.set_mode(sess_file, '600')
        session['login_token'] = token

    def clean_sess_files(self, sess_path):
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
                sess_file = os.path.join(sess_path, fname)
                if not os.path.isfile(sess_file): continue
                sess_tmp = public.ReadFile(sess_file)
                if not sess_tmp:
                    if os.path.exists(sess_file):
                        os.remove(sess_file)
                if s_time > int(sess_tmp):
                    os.remove(sess_file)
            except:
                pass

    def get_password_safe_file(self):
        '''
            @name 获取密码复杂度配置文件
            @auther hwliang<2021-10-18>
            @return string
        '''
        return public.get_panel_path() + '/data/check_password_safe.pl'

    def check_password_safe(self, password):
        '''
            @name 密码复杂度验证
            @auther hwliang<2021-10-18>
            @param password(string) 密码
            @return bool
        '''
        # 是否检测密码复杂度
        is_check_file = self.get_password_safe_file()
        if not os.path.exists(is_check_file): return True

        # 密码长度验证
        if len(password) < 8: return False

        num = 0
        # 密码是否包含数字
        if re.search(r'[0-9]+', password): num += 1
        # 密码是否包含小写字母
        if re.search(r'[a-z]+', password): num += 1
        # 密码是否包含大写字母
        if re.search(r'[A-Z]+', password): num += 1
        # 密码是否包含特殊字符
        if re.search(r'[^\w\s]+', password): num += 1
        # 密码是否包含以上任意3种组合
        if num < 3: return False
        return True

    def set_password_safe(self, get):
        '''
            @name 设置密码复杂度
            @auther hwliang<2021-10-18>
            @param get(string) 参数
            @return dict
        '''
        is_check_file = self.get_password_safe_file()
        if os.path.exists(is_check_file):
            os.remove(is_check_file)
            public.WriteLog('TYPE_PANEL', '关闭密码复杂度验证')
            return public.returnMsg(True, '已关闭密码复杂度验证')
        else:
            public.writeFile(is_check_file, 'True')
            public.WriteLog('TYPE_PANEL', '开启密码复杂度验证')
            return public.returnMsg(True, '已开启密码复杂度验证')

    def get_password_safe(self, get):
        '''
            @name 获取密码复杂度
            @auther hwliang<2021-10-18>
            @param get(string) 参数
            @return bool
        '''
        is_check_file = self.get_password_safe_file()
        return os.path.exists(is_check_file)

    def get_password_expire_file(self):
        '''
            @name 获取密码过期配置文件
            @auther hwliang<2021-10-18>
            @return string
        '''
        return public.get_panel_path() + '/data/password_expire.pl'

    def set_password_expire(self, get):
        '''
            @name 设置密码过期时间
            @auther hwliang<2021-10-18>
            @param get<dict_obj>{
                expire: int<密码过期时间> 单位:天,
            }
            @return dict
        '''
        expire = int(get.expire)
        expire_file = self.get_password_expire_file()
        if expire <= 0:
            if os.path.exists(expire_file):
                os.remove(expire_file)
            public.WriteLog('TYPE_PANEL', '关闭密码过期验证')
            return public.returnMsg(True, '已关闭密码过期验证')
        min_expire = 10
        max_expire = 365 * 5
        if expire < min_expire: return public.returnMsg(False, '密码过期时间不能小于{}天'.format(min_expire))
        if expire > max_expire: return public.returnMsg(False, '密码过期时间不能大于{}天'.format(max_expire))

        public.writeFile(self.get_password_expire_file(), str(expire))

        if expire > 0:
            expire_time_file = public.get_panel_path() + '/data/password_expire_time.pl'
            public.writeFile(expire_time_file, str(int(time.time()) + (expire * 86400)))

        public.WriteLog('TYPE_PANEL', '设置密码过期时间为：[{}]天'.format(expire))
        return public.returnMsg(True, '已设置密码过期时间为：[{}]天'.format(expire))

    def get_password_config(self, get=None):
        '''
            @name 获取密码配置
            @auther hwliang<2021-10-18>
            @param get<dict_obj> 参数
            @return dict{expire:int,expire_time:int,password_safe:bool}
        '''
        expire_file = self.get_password_expire_file()
        expire = 0
        expire_time = 0
        if os.path.exists(expire_file):
            expire = public.readFile(expire_file)
            try:
                expire = int(expire)
            except:
                expire = 0

            # 检查密码过期时间文件是否存在
            expire_time_file = public.get_panel_path() + '/data/password_expire_time.pl'
            if not os.path.exists(expire_time_file) and expire > 0:
                public.writeFile(expire_time_file, str(int(time.time()) + (expire * 86400)))

            expire_time = public.readFile(expire_time_file)
            if expire_time:
                expire_time = int(expire_time)
            else:
                expire_time = 0

        data = {}
        data['expire'] = expire
        data['expire_time'] = expire_time
        data['password_safe'] = self.get_password_safe(get)
        data['ps'] = '当前未开启密码过期配置，为了您的面板安全，请考虑开启!'
        if data['expire_time']:
            data['expire_day'] = int((expire_time - time.time()) / 86400)
            if data['expire_day'] < 10:
                if data['expire_day'] <= 0:
                    data['ps'] = '您的密码已经过期，为防止下次无法登录，请立即修改密码!'
                else:
                    data[
                        'ps'] = "您的面板密码还有 <span style='color:red;'>{}</span> 天就过期了，为了不影响您正常登录，请尽快修改密码!".format(
                        data['expire_day'])
            else:
                data['ps'] = "您的面板密码离过期时间还有 <span style='color:green;'>{}</span> 天!".format(
                    data['expire_day'])
        return data

    def setPassword(self, get):
        if not public.M('users').where("username=?", (session['username'],)).find():
            return public.returnMsg(False, '设置失败,请尝试重新登陆后再试！')
        get.password1 = public.url_decode(public.rsa_decrypt(get.password1))
        get.password2 = public.url_decode(public.rsa_decrypt(get.password2))
        if get.password1 != get.password2: return public.returnMsg(False, 'USER_PASSWORD_CHECK')

        if len(get.password1) < 5: return public.returnMsg(False, 'USER_PASSWORD_LEN')

        if not self.check_password_safe(get.password1): return public.returnMsg(False,
                                                                                '密码复杂度验证失败，要求：长度大于8位，数字、大写字母、小写字母、特殊字符最少3项组合')
        if get.password1:
            public.M('users').where("username=?", (session['username'],)).setField('password', public.password_salt(
                public.md5(get.password1.strip()), username=session['username']))
        public.WriteLog('TYPE_PANEL', 'USER_PASSWORD_SUCCESS', (session['username'],))
        public.add_security_logs("修改密码", "密码修改成功！[" + session['username'] + "]")

        # 是否设置过密码
        mark_file = public.get_panel_path() + '/data/mark_pwd.pl'
        if not os.path.exists(mark_file):
            public.writeFile(mark_file, '')
        else:
            self.reload_session()

        # 密码过期时间
        expire_time_file = public.get_panel_path() + '/data/password_expire_time.pl'
        if os.path.exists(expire_time_file): os.remove(expire_time_file)
        self.get_password_config(None)
        if session.get('password_expire', False):
            session['password_expire'] = False
        return public.returnMsg(True, 'USER_PASSWORD_SUCCESS')

    def setlastPassword(self, get):
        public.add_security_logs("修改密码", "使用上一次密码成功！")
        self.reload_session()
        # 密码过期时间
        expire_time_file = public.get_panel_path() + '/data/password_expire_time.pl'
        if os.path.exists(expire_time_file): os.remove(expire_time_file)
        self.get_password_config(None)
        if session.get('password_expire', False):
            session['password_expire'] = False
        return public.returnMsg(True, 'USER_PASSWORD_SUCCESS')

    def setUsername(self, get):
        get.username1 = public.url_decode(public.rsa_decrypt(get.username1))
        get.username2 = public.url_decode(public.rsa_decrypt(get.username2))
        if get.username1 != get.username2: return public.returnMsg(False, 'USER_USERNAME_CHECK')
        if len(get.username1) < 3: return public.returnMsg(False, 'USER_USERNAME_LEN')
        public.M('users').where("username=?", (session['username'],)).setField('username', get.username1.strip())
        public.WriteLog('TYPE_PANEL', 'USER_USERNAME_SUCCESS', (session['username'], get.username2))
        session['username'] = get.username1

        # 是否设置过用户名
        mark_file = public.get_panel_path() + '/data/mark_uname.pl'
        if not os.path.exists(mark_file):
            public.writeFile(mark_file, '')
        else:
            self.reload_session()

        return public.returnMsg(True, 'USER_USERNAME_SUCCESS')

    # 取用户列表
    def get_users(self, args):
        data = public.M('users').field('id,username').select()
        return data

    # 创建新用户
    def create_user(self, args):
        args.username = public.url_decode(args.username)
        args.password = public.url_decode(args.password)
        if session['uid'] != 1: return public.returnMsg(False, '没有权限!')
        if len(args.username) < 2: return public.returnMsg(False, '用户名不能少于2位')
        if len(args.password) < 8: return public.returnMsg(False, '密码不能少于8位')
        pdata = {
            "username": args.username.strip(),
            "password": public.password_salt(public.md5(args.password.strip()), username=args.username.strip())
        }

        if (public.M('users').where('username=?', (pdata['username'],)).count()):
            return public.returnMsg(False, '指定用户名已存在!')

        if (public.M('users').insert(pdata)):
            public.WriteLog('用户管理', '创建新用户{}'.format(pdata['username']))
            return public.returnMsg(True, '创建新用户{}成功!'.format(pdata['username']))
        return public.returnMsg(False, '创建新用户失败!')

    # 删除用户
    def remove_user(self, args):
        if session['uid'] != 1: return public.returnMsg(False, '没有权限!')
        if int(args.id) == 1: return public.returnMsg(False, '不能删除初始默认用户!')
        username = public.M('users').where('id=?', (args.id,)).getField('username')
        if not username: return public.returnMsg(False, '指定用户不存在!')
        if (public.M('users').where('id=?', (args.id,)).delete()):
            public.WriteLog('用户管理', '删除用户[{}]'.format(username))
            return public.returnMsg(True, '删除用户{}成功!'.format(username))
        return public.returnMsg(False, '用户删除失败!')

    # 修改用户
    def modify_user(self, args):
        if session['uid'] != 1: return public.returnMsg(False, '没有权限!')
        username = public.M('users').where('id=?', (args.id,)).getField('username')
        pdata = {}
        if 'username' in args:
            args.username = public.url_decode(args.username)
            if len(args.username) < 2: return public.returnMsg(False, '用户名不能少于2位')
            pdata['username'] = args.username.strip()

        if 'password' in args:
            if args.password:
                args.password = public.url_decode(args.password)
                if len(args.password) < 8: return public.returnMsg(False, '密码不能少于8位')
                pdata['password'] = public.password_salt(public.md5(args.password.strip()), username=username)

        if (public.M('users').where('id=?', (args.id,)).update(pdata)):
            public.WriteLog('用户管理', "编辑用户{}".format(username))
            return public.returnMsg(True, '修改成功!')
        return public.returnMsg(False, '没有提交修改!')

    def setPanel(self, get):
        if not public.IsRestart(): return public.returnMsg(False, 'EXEC_ERR_TASK')
        limitip_path = "{}/data/limitip.conf".format(self._setup_path)
        if not get.get('limitip') and os.path.exists(limitip_path):
            os.truncate(limitip_path, 0)

        if 'limitip' in get:
            if get.limitip.find('/') != -1:
                return public.returnMsg(False, '授权IP格式不正确,不支持子网段写法')
        isReWeb = False
        sess_out_path = 'data/session_timeout.pl'
        if 'session_timeout' in get:
            try:
                session_timeout = int(get.session_timeout)
                s_time_tmp = public.readFile(sess_out_path)
                if not s_time_tmp: s_time_tmp = '0'
                if int(s_time_tmp) != session_timeout:
                    if session_timeout < 300: return public.returnMsg(False, '超时时间不能小于300秒')
                    if session_timeout > 86400 * 30: return public.returnMsg(False, '超时时间不能大于30天')
                    public.writeFile(sess_out_path, str(session_timeout))
                    isReWeb = True
            except:
                # return public.returnMsg(False, "超时时间必需是整数!")
                pass
        # else:
        #     return public.returnMsg(False, '超时时间不能为空!')

        workers_p = 'data/workers.pl'
        if 'workers' in get:
            workers = int(get.workers)
            if int(public.readFile(workers_p)) != workers:
                if workers < 1 or workers > 1024: return public.returnMsg(False, '面板线程数范围应该在1-1024之间')
                public.writeFile(workers_p, str(workers))
                isReWeb = True

        if "domain" in get and get.domain != "":
            if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", get.domain): return public.returnMsg(False,
                                                                                                      '不能绑定ip')
            reg = r"^([\w\-\*]{1,100}\.){1,4}(\w{1,10}|\w{1,10}\.\w{1,10})$"
            if not re.match(reg, get.domain): return public.returnMsg(False, 'SITE_ADD_ERR_DOMAIN')
            import idna
            domain_idna = idna.encode(get.domain.strip()).decode("utf-8")
            public.writeFile('data/domain.conf', domain_idna)
            public.WriteLog('TYPE_PANEL', 'PANEL_SET_SUCCESS', (get.domain,))

        if get.get("domain") == "":
            if os.path.exists('data/domain.conf'): os.remove('data/domain.conf')

        if "address" in get and get.address != "":
            if not public.check_ip(get.address):
                return public.returnMsg(False, '请设置正确的服务器ipv4或ipv6地址')
            public.writeFile('data/iplist.txt', get.address)
            public.WriteLog('TYPE_PANEL', 'PANEL_SET_SUCCESS', (get.address,))

        oldPort = public.GetHost(True)
        if not 'port' in get:
            get.port = oldPort
        newPort = get.port
        if oldPort != get.port:
            get.port = str(int(get.port))
            if self.IsOpen(get.port):
                return public.returnMsg(False, 'PORT_CHECK_EXISTS', (get.port,))
            if int(get.port) >= 65535 or int(get.port) < 100: return public.returnMsg(False, 'PORT_CHECK_RANGE')
            public.writeFile('data/port.pl', get.port)
            import firewalls
            get.ps = public.getMsg('PORT_CHECK_PS')
            fw = firewalls.firewalls()
            fw.AddAcceptPort(get)
            get.port = oldPort
            get.id = public.M('firewall').where("port=?", (oldPort,)).getField('id')
            fw.DelAcceptPort(get)
            isReWeb = True
            public.WriteLog('TYPE_PANEL', 'PANEL_SET_SUCCESS', (newPort,))

        if "webname" in get and get.webname != session['title']:
            if get.webname.strip() == '': get.webname = '宝塔Linux面板'
            session['title'] = public.xssencode2(get.webname)
            public.SetConfigValue('title', public.xssencode2(get.webname))
            public.WriteLog('TYPE_PANEL', 'PANEL_SET_SUCCESS', ('TITLE', get.webname))

        limitip = public.readFile('data/limitip.conf')
        if "limitip" in get and get.limitip != limitip:
            public.writeFile('data/limitip.conf', get.limitip)
            cache.set('limit_ip', [])
            public.WriteLog('TYPE_PANEL', 'PANEL_SET_SUCCESS', ('LIMIT_IP',))

        import files
        fs = files.files()
        if "backup_path" in get and get.backup_path != "":
            if not fs.CheckDir(get.backup_path): return public.returnMsg(False, '不能使用系统关键目录作为默认备份目录')
            session['config']['backup_path'] = os.path.join('/', get.backup_path)
            db_backup = get.backup_path + '/database'
            site_backup = get.backup_path + '/site'

            if not os.path.exists(db_backup):
                try:
                    os.makedirs(db_backup, 384)
                except:
                    public.ExecShell('mkdir -p ' + db_backup)

            if not os.path.exists(site_backup):
                try:
                    os.makedirs(site_backup, 384)
                except:
                    public.ExecShell('mkdir -p ' + site_backup)

            public.M('config').where("id=?", ('1',)).save('backup_path', (get.backup_path,))
            isReWeb = True
            public.WriteLog('TYPE_PANEL', 'PANEL_SET_SUCCESS', (get.backup_path,))

        if "sites_path" in get and get.sites_path != "":
            if not fs.CheckDir(get.sites_path): return public.returnMsg(False, '不能使用系统关键目录作为默认建站目录')

            session['config']['sites_path'] = os.path.join('/', get.sites_path)
            public.M('config').where("id=?", ('1',)).save('sites_path', (get.sites_path,))
            public.WriteLog('TYPE_PANEL', 'PANEL_SET_SUCCESS', (get.sites_path,))

        mhost = public.GetHost()
        if "domain" in get and get.domain.strip(): mhost = get.domain
        data = {'uri': request.path, 'host': mhost + ':' + newPort, 'status': True, 'isReWeb': isReWeb,
                'msg': public.getMsg('PANEL_SAVE')}

        if isReWeb: public.restart_panel()
        return data

    def set_admin_path(self, get):
        get.admin_path = public.rsa_decrypt(get.admin_path.strip()).strip()
        if len(get.admin_path) < 6:
            return public.returnMsg(False, '安全入口地址长度不能小于6位!')
        if get.admin_path in admin_path_checks:
            return public.returnMsg(False, '该入口已被面板占用,请使用其它入口!')
        if not public.path_safe_check(get.admin_path) or get.admin_path[-1] == '.':
            return public.returnMsg(False, '入口地址格式不正确,示例: /my_panel')
        if get.admin_path[0] != '/':
            return public.returnMsg(False, '入口地址格式不正确,示例: /my_panel')
        if get.admin_path.find("//") != -1:
            return public.returnMsg(False, '入口地址格式不正确,示例: /my_panel')
        admin_path_file = 'data/admin_path.pl'
        admin_path = '/'
        if os.path.exists(admin_path_file):
            admin_path = public.readFile(admin_path_file).strip()
        if get.admin_path != admin_path:
            public.writeFile(admin_path_file, get.admin_path)
            public.restart_panel()
        return public.returnMsg(True, '修改成功!')

    def setPathInfo(self, get):
        # 设置PATH_INFO
        version = get.version
        type = get.type
        if public.get_webserver() == 'nginx':
            path = public.GetConfigValue('setup_path') + '/nginx/conf/enable-php-' + version + '.conf'
            conf = public.readFile(path)
            if not conf:
                return public.returnMsg(False, '配置文件{}不存在！'.format(path))
            rep_pathinfo = re.compile(r"\s+#?include\s+pathinfo\.conf;")
            if type == 'on':
                conf = rep_pathinfo.sub('\n        include pathinfo.conf;', conf)
            else:
                conf = rep_pathinfo.sub('\n        #include pathinfo.conf;', conf)
            public.writeFile(path, conf)
            public.serviceReload()

        path = public.GetConfigValue('setup_path') + '/php/' + version + '/etc/php.ini'
        conf = public.readFile(path)
        if not conf:
            return public.returnMsg(False, '请检查php {} 版本是否安装，或 {}/php/{}/etc/php.ini 配置文件是否存在'.format(version,public.GetConfigValue('setup_path'),version))
        rep = r"\n*\s*cgi\.fix_pathinfo\s*=\s*([0-9]+)\s*\n"
        status = '0'
        if type == 'on': status = '1'
        conf = re.sub(rep, "\ncgi.fix_pathinfo = " + status + "\n", conf)
        public.writeFile(path, conf)
        public.WriteLog("TYPE_PHP", "PHP_PATHINFO_SUCCESS", (version, type))
        public.phpReload(version)
        return public.returnMsg(True, 'SET_SUCCESS')

    # 设置文件上传大小限制
    def setPHPMaxSize(self, get):
        version = get.version
        max = get.max

        if int(max) < 2: return public.returnMsg(False, 'PHP_UPLOAD_MAX_ERR')

        # 设置PHP
        path = public.GetConfigValue('setup_path') + '/php/' + version + '/etc/php.ini'
        ols_php_path = '/usr/local/lsws/lsphp{}/etc/php/{}.{}/litespeed/php.ini'.format(get.version, get.version[0],
                                                                                        get.version[1])
        if os.path.exists('/etc/redhat-release'):
            ols_php_path = '/usr/local/lsws/lsphp' + get.version + '/etc/php.ini'
        for p in [path, ols_php_path]:
            if not p:
                continue
            if not os.path.exists(p):
                continue
            conf = public.readFile(p)
            rep = r"\nupload_max_filesize\s*=\s*[0-9]+M?m?"
            conf = re.sub(rep, r'\nupload_max_filesize = ' + max + 'M', conf)
            rep = r"\npost_max_size\s*=\s*[0-9]+M?m?"
            conf = re.sub(rep, r'\npost_max_size = ' + max + 'M', conf)
            public.writeFile(p, conf)

        if public.get_webserver() == 'nginx':
            # 设置Nginx
            path = public.GetConfigValue('setup_path') + '/nginx/conf/nginx.conf'
            conf = public.readFile(path)
            if not conf:
                return public.returnMsg(False, "nginx的配置文件异常,请重新安装nginx后再试")
            rep = r"client_max_body_size\s+([0-9]+)m?M?"
            tmp = re.search(rep, conf).groups()
            if int(tmp[0]) < int(max):
                conf = re.sub(rep, 'client_max_body_size ' + max + 'm', conf)
                public.writeFile(path, conf)

        public.serviceReload()
        public.phpReload(version)
        public.WriteLog("TYPE_PHP", "PHP_UPLOAD_MAX", (version, max))
        return public.returnMsg(True, 'SET_SUCCESS')

    # 设置禁用函数
    def setPHPDisable(self, get):
        filename = public.GetConfigValue('setup_path') + '/php/' + get.version + '/etc/php.ini'
        cli_filename = public.GetConfigValue('setup_path') + '/php/' + get.version + '/etc/php-cli.ini'
        ols_php_path = '/usr/local/lsws/lsphp{}/etc/php/{}.{}/litespeed/php.ini'.format(get.version, get.version[0],
                                                                                        get.version[1])
        ols_php_path_cli = '/usr/local/lsws/lsphp{}/etc/php/{}.{}/litespeed/php-cli.ini'.format(
            get.version, get.version[0], get.version[1])
        if os.path.exists('/etc/redhat-release'):
            ols_php_path = '/usr/local/lsws/lsphp' + get.version + '/etc/php.ini'
            ols_php_path_cli = '/usr/local/lsws/lsphp' + get.version + '/etc/php-cli.ini'
        if not os.path.exists(filename): return public.returnMsg(False, 'PHP_NOT_EXISTS')
        for file in [filename, cli_filename, ols_php_path, ols_php_path_cli]:
            if not os.path.exists(file):
                continue
            phpini = public.readFile(file)
            rep = r"disable_functions\s*=\s*.*\n"
            phpini = re.sub(rep, 'disable_functions = ' + get.disable_functions + "\n", phpini)
            public.WriteLog('TYPE_PHP', 'PHP_DISABLE_FUNCTION', (get.version, get.disable_functions))
            public.writeFile(file, phpini)
            public.phpReload(get.version)
        public.serviceReload()
        return public.returnMsg(True, 'SET_SUCCESS')

    # 设置PHP超时时间
    def setPHPMaxTime(self, get):
        time = get.time
        version = get.version
        if int(time) < 30 or int(time) > 86400: return public.returnMsg(False, 'PHP_TIMEOUT_ERR')
        file = public.GetConfigValue('setup_path') + '/php/' + version + '/etc/php-fpm.conf'
        conf = public.readFile(file)
        if not conf:
            return public.returnMsg(False, 'PHP_NOT_EXISTS')
        rep = r"request_terminate_timeout\s*=\s*([0-9]+)\n"
        conf = re.sub(rep, "request_terminate_timeout = " + time + "\n", conf)
        public.writeFile(file, conf)

        file = '/www/server/php/' + version + '/etc/php.ini'
        phpini = public.readFile(file)
        rep = r"max_execution_time\s*=\s*([0-9]+)\r?\n"
        phpini = re.sub(rep, "max_execution_time = " + time + "\n", phpini)
        rep = r"max_input_time\s*=\s*([0-9]+)\r?\n"
        phpini = re.sub(rep, "max_input_time = " + time + "\n", phpini)
        public.writeFile(file, phpini)
        if public.get_webserver() == 'nginx':
            # 设置Nginx
            path = public.GetConfigValue('setup_path') + '/nginx/conf/nginx.conf'
            if os.path.exists(path):
                conf = public.readFile(path)
            if not conf:
                return public.returnMsg(False, "nginx的配置文件异常,请重新安装nginx后再试")
            rep = r"fastcgi_connect_timeout\s+([0-9]+);"
            tmp = re.search(rep, conf).groups()
            if int(tmp[0]) < int(time):
                conf = re.sub(rep, 'fastcgi_connect_timeout ' + time + ';', conf)
                rep = r"fastcgi_send_timeout\s+([0-9]+);"
                conf = re.sub(rep, 'fastcgi_send_timeout ' + time + ';', conf)
                rep = r"fastcgi_read_timeout\s+([0-9]+);"
                conf = re.sub(rep, 'fastcgi_read_timeout ' + time + ';', conf)
                public.writeFile(path, conf)

        public.WriteLog("TYPE_PHP", "PHP_TIMEOUT", (version, time))
        public.serviceReload()
        public.phpReload(version)
        return public.returnMsg(True, 'SET_SUCCESS')

    # 取FPM设置
    def getFpmConfig(self, get):
        import os
        version = get.version
        file = public.GetConfigValue('setup_path') + "/php/" + version + "/etc/php-fpm.conf"
        if not os.path.exists(file) or os.path.getsize(file) < 10:
            return public.returnMsg(False, '{}<br>配置文件不存在或文件大小异常!'.format(file))

        conf = public.readFile(file)
        if not conf:
            return public.returnMsg(False, '{}<br>配置文件异常!'.format(file))
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

        rep = r"\s*listen.allowed_clients\s*=\s*([\w\.,/]+)\s*"
        tmp = re.search(rep, conf).groups()
        data['allowed'] = tmp[0]

        data['unix'] = 'unix'
        data['port'] = ''
        data['bind'] = '/tmp/php-cgi-{}.sock'.format(version)

        fpm_address = public.get_fpm_address(version, True)
        if not isinstance(fpm_address, str):
            data['unix'] = 'tcp'
            data['port'] = fpm_address[1]
            data['bind'] = fpm_address[0]

        return data

    # 设置
    def setFpmConfig(self, get):
        import os
        required_parameters = ['version', 'max_children', 'start_servers', 'min_spare_servers', 'max_spare_servers', 'pm']

        for param in required_parameters:
            if not hasattr(get, param):
                return public.returnMsg(False, '缺少参数！{}'.format(param))

        version = get.version
        max_children = get.max_children
        start_servers = get.start_servers
        min_spare_servers = get.min_spare_servers
        max_spare_servers = get.max_spare_servers
        pm = get.pm

        if not pm in ['static', 'dynamic', 'ondemand']:
            return public.returnMsg(False, '错误的运行模式!')
        file = public.GetConfigValue('setup_path') + "/php/" + version + "/etc/php-fpm.conf"
        if not os.path.exists(file) or os.path.getsize(file) < 10:
            return public.returnMsg(False, '{}<br>配置文件不存在或文件大小异常,请尝试重装php!'.format(file))

        conf = public.readFile(file)

        rep = r"\s*pm.max_children\s*=\s*([0-9]+)\s*"
        conf = re.sub(rep, "\npm.max_children = " + max_children, conf)

        rep = r"\s*pm.start_servers\s*=\s*([0-9]+)\s*"
        conf = re.sub(rep, "\npm.start_servers = " + start_servers, conf)

        rep = r"\s*pm.min_spare_servers\s*=\s*([0-9]+)\s*"
        conf = re.sub(rep, "\npm.min_spare_servers = " + min_spare_servers, conf)

        rep = r"\s*pm.max_spare_servers \s*=\s*([0-9]+)\s*"
        conf = re.sub(rep, "\npm.max_spare_servers = " + max_spare_servers + "\n", conf)

        rep = r"\s*pm\s*=\s*(\w+)\s*"
        conf = re.sub(rep, "\npm = " + pm + "\n", conf)
        if pm == 'ondemand':
            if conf.find('listen.backlog = -1') != -1:
                rep = r"\s*listen\.backlog\s*=\s*([0-9-]+)\s*"
                conf = re.sub(rep, "\nlisten.backlog = 8192\n", conf)

        if get.listen == 'unix':
            listen = '/tmp/php-cgi-{}.sock'.format(version)
        else:
            default_listen = '127.0.0.1:10{}1'.format(version)
            if 'bind_port' in get:
                if get.bind_port.find('sock') != -1:
                    listen = default_listen
                else:
                    listen = get.bind_port
            else:
                listen = default_listen

        rep = r'\s*listen\s*=\s*.+\s*'
        conf = re.sub(rep, "\nlisten = " + listen + "\n", conf)

        if 'allowed' in get:
            if not get.allowed: get.allowed = '127.0.0.1'
            rep = r"\s*listen.allowed_clients\s*=\s*([\w\.,/]+)\s*"
            conf = re.sub(rep, "\nlisten.allowed_clients = " + get.allowed + "\n", conf)

        public.writeFile(file, conf)
        public.phpReload(version)
        public.sync_php_address(version)
        public.WriteLog("TYPE_PHP", 'PHP_CHILDREN',
                        (version, max_children, start_servers, min_spare_servers, max_spare_servers))
        return public.returnMsg(True, 'SET_SUCCESS')

    def GetPhpPeclLog(self, get):
        if not "version" in get: return public.returnMsg(False, '请传入version参数')
        phpv=get.version
        log_path="/tmp/pecl-{}.log".format(phpv)
        if os.path.exists(log_path):
            return public.returnMsg(True, public.xsssec(public.GetNumLines(log_path, 50)))
        else:
            return public.returnMsg(False,"未找到相关执行日志！")

    def phpPeclInstall(self,get):
        if not "version" in get: return public.returnMsg(False, '请传入version参数')
        if not "name" in get: return public.returnMsg(False, '请传入name参数')

        phpv=get.version
        name=get.name

        if not os.path.exists("/www/server/php/{}/bin/pecl".format(phpv)):
            return public.returnMsg(False,'未找到pecl执行文件，请使用编译安装方式重装php后再使用此功能')

        php_ext_path={
            "52":"20060613",
            "53":"20090626",
            "54":"20100525",
            "55":"20121212",
            "56":"20131226",
            "70":"20151012",
            "71":"20160303",
            "72":"20170718",
            "73":"20180731",
            "74":"20190902",
            "80":"20200930",
            "81":"20210902",
            "82":"20220829",
            "83":"20230831"
        }

        php_so_path="/www/server/php/{}/lib/php/extensions/no-debug-non-zts-{}/{}.so".format(phpv,php_ext_path[phpv],name)
        if os.path.exists(php_so_path):
            return public.returnMsg(True, '{}扩展已安装，请勿重新安装！'.format(name))

        if not os.path.exists("/www/server/php/{}/etc/php-cli.ini".format(phpv)):
            import shutil
            shutil.copy2("/www/server/php/{}/etc/php.ini".format(phpv),'/www/server/php/{}/etc/php-cli.ini".format(phpv)')

        pecl_result=public.ExecShell("yes ''|/www/server/php/{}/bin/pecl install {} |tee /tmp/pecl-{}.log".format(phpv,name,phpv))[0]

        if "install ok" in pecl_result:
            public.ExecShell("echo 'extension={}.so' >> /www/server/php/{}/etc/php.ini".format(name,phpv))
            if os.path.exists("/www/server/php/{}/etc/php-cli.ini".format(phpv)):
                public.ExecShell("echo 'extension={}.so' >> /www/server/php/{}/etc/php-cli.ini".format(name,phpv))
            public.phpReload(phpv)
            return public.returnMsg(True, '安装{}扩展成功！'.format(name))
        elif "already installed" in pecl_result:
            return public.returnMsg(True, '{}扩展已安装，请勿重新安装！'.format(name))
        elif "No releases available for package" in pecl_result:
            return public.returnMsg(False, '安装{}扩展失败！未在pecl上找到此包！'.format(name))
        else:
            return public.returnMsg(False, '安装{}扩展失败！详细错误请查看安装日志'.format(name))

    def phpPeclUninstall(self,get):

        if not "version" in get: return public.returnMsg(False, '请传入version参数')
        if not "name" in get: return public.returnMsg(False, '请传入name参数')

        phpv=get.version
        name=get.name

        if not os.path.exists("/www/server/php/{}/bin/pecl".format(phpv)):
            return public.returnMsg(False,'未找到pecl执行文件，请使用编译安装方式重装php后再使用此功能')

        pecl_result=public.ExecShell("/www/server/php/{}/bin/pecl uninstall {}".format(phpv,name))[0]

        public.ExecShell("sed -i '/{}.so/d' /www/server/php/{}/etc/php.ini".format(name,phpv))
        if os.path.exists("/www/server/php/{}/etc/php-cli.ini".format(phpv)):
            public.ExecShell("sed -i '/{}.so/d' /www/server/php/{}/etc/php-cli.ini".format(name,phpv))

        public.phpReload(phpv)
        return public.returnMsg(True, '删除{}扩展成功！'.format(name))

    def GetPeclInstallList(self,get):
        if not "version" in get: return public.returnMsg(False, '请传入version参数')
        phpv=get.version

        if not os.path.exists("/www/server/php/{}/bin/pecl".format(phpv)):
            return public.returnMsg(False,'未找到pecl执行文件，请使用编译安装方式重装php后再使用此功能')

        packages = []
        pecl_list_result=public.ExecShell("/www/server/php/{}/bin/pecl list".format(phpv))[0]
        lines = pecl_list_result.splitlines()
        for line in lines[3:]:
            parts = line.split()
            if len(parts) == 3:
                package = {
                    "Package": parts[0],
                    "Version": parts[1],
                    "State": parts[2]
                }
                packages.append(package)
        return packages

    # 同步时间
    def syncDate(self, get):
        """
        @name 同步时间
        @author hezhihong
        """
        # 取国际标准0时时间戳
        time_str = public.HttpGet(public.GetConfigValue('home') + '/api/index/get_time')
        try:
            new_time = int(time_str) - 28800
        except:
            return public.returnMsg(False, '连接时间服务器失败!')
        if not new_time: public.returnMsg(False, '连接时间服务器失败!')
        # 取所在时区偏差秒数
        add_time = '+0000'
        try:
            add_time = public.ExecShell('date +"%Y-%m-%d %H:%M:%S %Z %z"')[0].replace('\n', '').strip().split()[-1]
            print(add_time)
        except:
            pass
        add_1 = False
        if add_time[0] == '+':
            add_1 = True
        add_v = int(add_time[1:-2]) * 3600 + int(add_time[-2:]) * 60
        if add_1:
            new_time += add_v
        else:
            new_time -= add_v
        # 设置所在时区时间
        date_str = public.format_date(times=new_time)
        public.ExecShell('date -s "%s"' % date_str)
        public.WriteLog("TYPE_PANEL", "DATE_SUCCESS")
        return public.returnMsg(True, "DATE_SUCCESS")

    # 设置同步时间计划任务
    def syncDateCrontab(self, get):
        if not hasattr(get, "sName"):
            return public.returnMsg(False, "缺少参数! sName")
        if not hasattr(get, "sType"):
            return public.returnMsg(False, "缺少参数! sType")
        count = public.M('crontab').where("sName=? and sType=?", (get["sName"], get["sType"])).count()
        if count == 0:
            import crontab
            resp = crontab.crontab().AddCrontab(get)
            return resp
        return public.returnMsg(True, "计划任务已创建!")

    def IsOpen(self, port):
        # 检查端口是否占用
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect(('127.0.0.1', int(port)))
            s.shutdown(2)
            return True
        except:
            return False

    # 设置是否开启监控
    def SetControl(self, get):
        try:
            if hasattr(get, 'day'):
                get.day = int(get.day)
                get.day = str(get.day)
                if (get.day < 1): return public.returnMsg(False, "CONTROL_ERR")
        except:
            pass
        # 开启监控时开启面板日报统计
        # if not os.path.exists('/www/server/panel/data/start_daily.pl') and get.type == '1':
        #     date = time.time()
        #     # 格式化日期为字符串
        #     yesterday_date_str = public.format_date("%Y%m%d", date - 86400)
        #     public.writeFile('/www/server/panel/data/start_daily.pl', yesterday_date_str)
        # elif os.path.exists('/www/server/panel/data/start_daily.pl') and get.type == '0':
        #     os.remove('/www/server/panel/data/start_daily.pl')
        filename = 'data/control.conf'
        if get.type == '1':
            public.writeFile(filename, get.day)
            public.WriteLog("TYPE_PANEL", 'CONTROL_OPEN', (get.day,))
        elif get.type == '0':
            if os.path.exists(filename): os.remove(filename)
            public.WriteLog("TYPE_PANEL", "CONTROL_CLOSE")
        elif get.type == 'del':
            if not public.IsRestart(): return public.returnMsg(False, 'EXEC_ERR_TASK')
            os.remove("data/system.db")
            public.ExecShell("/www/server/panel/BT-Task")
            public.ExecShell("touch /www/server/panel/data/system.db")
            public.ExecShell("chmod 777 /www/server/panel/data/system.db")
            public.ExecShell("chmod 777 /www/server/panel/data/system.sql")
            panel_path = public.get_panel_path()
            data_path = "{}/data/sql_index.pl".format(panel_path)
            public.ExecShell("rm -f {}".format(data_path))
            import db
            sql = db.Sql()
            sql.dbfile('system').create('system')
            public.WriteLog("TYPE_PANEL", "CONTROL_CLEAR")
            return public.returnMsg(True, "CONTROL_CLEAR")

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

            # 增加数据库大小计算机
            data['size'] = 0
            db_file = '{}/data/system.db'.format(public.get_panel_path())
            if os.path.exists(db_file):
                data['size'] = os.path.getsize(db_file)
            # 检查数据中的表是否存在
            self.check_tables()
            return data

        return public.returnMsg(True, "SET_SUCCESS")

    def check_tables(self):
        import db
        db_obj = db.Sql()
        db_obj.dbfile('/www/server/panel/data/system.db')
        table_list = db_obj.query('SELECT name FROM sqlite_master WHERE type="table"')
        fail_list = [i[0] for i in table_list if len(i)>0]
        def_table = ['cpuio','load_average','diskio','network','process_top_list']
        def_table_sql= {
            'cpuio':"""CREATE TABLE `cpuio` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `pro` INTEGER,
  `mem` INTEGER,
  `addtime` INTEGER
);
""",
            'load_average':"""CREATE TABLE `load_average` (
`id` INTEGER PRIMARY KEY AUTOINCREMENT,
`pro` REAL,
`one` REAL,
`five` REAL,
`fifteen` REAL,
`addtime` INTEGER
);
""",
            'diskio':"""CREATE TABLE `diskio` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `read_count` INTEGER,
  `write_count` INTEGER,
  `read_bytes` INTEGER,
  `write_bytes` INTEGER,
  `read_time` INTEGER,
  `write_time` INTEGER,
  `addtime` INTEGER
);
""",
            'network':"""CREATE TABLE `network` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `up` INTEGER,
  `down` INTEGER,
  `total_up` INTEGER,
  `total_down` INTEGER,
  `down_packets` INTEGER,
  `up_packets` INTEGER,
  `addtime` INTEGER
);
""",
            'process_top_list':"""CREATE TABLE `process_top_list` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `cpu_top` REAL,
  `memory_top` REAL,
  `disk_top` REAL,
  `net_top` REAL,
  `all_top` REAL,
  `addtime` INTEGER
);
"""
        }
        for table in def_table:
            if table not in fail_list:
                db_obj.execute(def_table_sql[table])

    # 关闭面板
    def ClosePanel(self, get):
        filename = 'data/close.pl'
        if os.path.exists(filename):
            os.remove(filename)
            return public.returnMsg(True, '开启成功')
        public.writeFile(filename, 'True')
        public.ExecShell("chmod 600 " + filename)
        public.ExecShell("chown root.root " + filename)
        return public.returnMsg(True, 'PANEL_CLOSE')

    # 设置自动更新
    def AutoUpdatePanel(self, get):
        # return public.returnMsg(False,'体验服务器，禁止修改!')
        filename = 'data/autoUpdate.pl'
        if os.path.exists(filename):
            os.remove(filename)
        else:
            public.writeFile(filename, 'True')
            public.ExecShell("chmod 600 " + filename)
            public.ExecShell("chown root.root " + filename)
        return public.returnMsg(True, 'SET_SUCCESS')

    # 设置二级密码
    def SetPanelLock(self, get):
        path = 'data/lock'
        if not os.path.exists(path):
            public.ExecShell('mkdir ' + path)
            public.ExecShell("chmod 600 " + path)
            public.ExecShell("chown root.root " + path)

        keys = ['files', 'tasks', 'config']
        for name in keys:
            filename = path + '/' + name + '.pl'
            if hasattr(get, name):
                public.writeFile(filename, 'True')
            else:
                if os.path.exists(filename): os.remove(filename)

    # 设置PHP守护程序
    def Set502(self, get):
        filename = 'data/502Task.pl'
        if os.path.exists(filename):
            public.ExecShell('rm -f ' + filename)
        else:
            public.writeFile(filename, 'True')

        return public.returnMsg(True, 'SET_SUCCESS')

    # 设置模板
    def SetTemplates(self, get):
        public.writeFile('data/templates.pl', get.templates)
        return public.returnMsg(True, 'SET_SUCCESS')

    def is_ssl_cookie_modified(self):
        from flask import request
        # 假设当SSL启用时，会在cookie名称添加'_ssl'
        suffix = '_ssl'

        # 遍历所有cookie，检查是否有名称以'_ssl'结尾
        for cookie_name in request.cookies:
            if cookie_name.endswith(suffix):
                return True
        return False


    # 设置面板SSL
    def SetPanelSSL(self, get):
        if hasattr(get, "email"):
            import setPanelLets
            sp = setPanelLets.setPanelLets()
            sps = sp.set_lets(get)
            public.reload_panel()
            return sps
        else:
            sslConf = '/www/server/panel/data/ssl.pl'
            if os.path.exists('/www/server/panel/ssl/baota_root.crt'):
                public.ExecShell('rm -f /www/server/panel/ssl/baota_root.crt')
            if os.path.exists(sslConf) and not 'cert_type' in get:
                if os.path.exists('/www/server/panel/data/ssl_verify_data.pl'):
                    return public.returnMsg(False, '检测到当前面板已开启访问设备验证，请先关闭访问设备验证！')
                public.ExecShell('rm -f ' + sslConf)
                try:
                    g.rm_ssl = True
                except:
                    pass
                public.reload_panel()
                return public.returnMsg(True, 'PANEL_SSL_CLOSE')
            else:
                if not 'cert_type' in get:
                    return public.returnMsg(False, '请刷新页面重试!')
                if get.cert_type in [1, '1'] and get.privateKey and get.certPem:
                    result = self.SavePanelSSL(get)
                    if not result['status']: return result
                    public.writeFile(sslConf, 'True')
                    public.reload_panel()
                else:
                    try:
                        if not self.CreateSSL(): return public.returnMsg(False, 'PANEL_SSL_ERR')
                        public.writeFile(sslConf, 'True')
                        public.reload_panel()
                    except:
                        return public.returnMsg(False, 'PANEL_SSL_ERR')
                try:
                    g.set_ssl = True
                except:
                    pass
                return public.returnMsg(True, 'PANEL_SSL_OPEN')

    # 自签证书
    def CreateSSL(self):
        userInfo = public.get_user_info()
        if userInfo:
            domains = []
            req_host = public.GetHost()
            server_ip = public.get_ip()
            domains.append(req_host)
            if server_ip != req_host and not server_ip in ['127.0.0.1', '::1', 'localhost']:
                domains.append(server_ip)
            pdata = {
                "action": "get_domain_cert",
                "company": "宝塔面板",
                "domain": ','.join(domains),
                "uid": userInfo['uid'],
                "access_key": userInfo['access_key'],
                "panel": 1
            }
            cert_api = 'https://api.bt.cn/bt_cert'
            http_data = public.httpPost(cert_api, {'data': json.dumps(pdata)})
            if http_data is not False:
                try:
                    result = json.loads(http_data)
                except:
                    result = {}
                if 'status' in result:
                    if result['status']:
                        public.writeFile('ssl/certificate.pem', result['cert'])
                        public.writeFile('ssl/privateKey.pem', result['key'])
                        public.writeFile('ssl/baota_root.pfx', base64.b64decode(result['pfx']), 'wb+')
                        public.writeFile('ssl/root_password.pl', result['password'])
                        return True

        if os.path.exists('ssl/input.pl'): return True
        import OpenSSL
        key = OpenSSL.crypto.PKey()
        key.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)
        cert = OpenSSL.crypto.X509()
        cert.set_serial_number(0)
        cert.get_subject().CN = public.GetLocalIp()
        cert.set_issuer(cert.get_subject())
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(86400 * 3650)
        cert.set_pubkey(key)
        cert.sign(key, 'md5')
        cert_ca = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
        private_key = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key)

        if len(cert_ca) > 100 and len(private_key) > 100:
            public.writeFile('ssl/certificate.pem', cert_ca, 'wb+')
            public.writeFile('ssl/privateKey.pem', private_key, 'wb+')
            return True
        return False

    # 生成Token
    def SetToken(self, get):
        data = {}
        data[''] = public.GetRandomString(24)

    # 取面板列表
    def GetPanelList(self, get):
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
            public.M('sites').execute(sql, ())
            return []

    # 添加面板资料
    def AddPanelInfo(self, get):

        # 校验是还是重复
        isAdd = public.M('panel').where('title=? OR url=?', (get.title, get.url)).count()
        if isAdd: return public.returnMsg(False, 'PANEL_SSL_ADD_EXISTS')
        import time, json
        isRe = public.M('panel').add('title,url,username,password,click,addtime', (
            public.xssencode2(get.title), public.xssencode2(get.url), public.xssencode2(get.username), get.password, 0,
            int(time.time())))
        if isRe: return public.returnMsg(True, 'ADD_SUCCESS')
        return public.returnMsg(False, 'ADD_ERROR')

    # 修改面板资料
    def SetPanelInfo(self, get):
        # 校验是还是重复
        isSave = public.M('panel').where('(title=? OR url=?) AND id!=?', (get.title, get.url, get.id)).count()
        if isSave: return public.returnMsg(False, 'PANEL_SSL_ADD_EXISTS')
        import time, json

        # 更新到数据库
        isRe = public.M('panel').where('id=?', (get.id,)).save('title,url,username,password',
                                                               (get.title, get.url, get.username, get.password))
        if isRe: return public.returnMsg(True, 'EDIT_SUCCESS')
        return public.returnMsg(False, 'EDIT_ERROR')

    # 删除面板资料
    def DelPanelInfo(self, get):
        isExists = public.M('panel').where('id=?', (get.id,)).count()
        if not isExists: return public.returnMsg(False, 'PANEL_SSL_ADD_NOT_EXISTS')
        public.M('panel').where('id=?', (get.id,)).delete()
        return public.returnMsg(True, 'DEL_SUCCESS')

    # 点击计数
    def ClickPanelInfo(self, get):
        click = public.M('panel').where('id=?', (get.id,)).getField('click')
        public.M('panel').where('id=?', (get.id,)).setField('click', click + 1)
        return True

    # 获取PHP配置参数
    def GetPHPConf(self, get):
        gets = [
            {'name': 'short_open_tag', 'type': 1, 'ps': public.getMsg('PHP_CONF_1')},
            {'name': 'asp_tags', 'type': 1, 'ps': public.getMsg('PHP_CONF_2')},
            {'name': 'max_execution_time', 'type': 2, 'ps': public.getMsg('PHP_CONF_4')},
            {'name': 'max_input_time', 'type': 2, 'ps': public.getMsg('PHP_CONF_5')},
            {'name': 'memory_limit', 'type': 2, 'ps': public.getMsg('PHP_CONF_6')},
            {'name': 'post_max_size', 'type': 2, 'ps': public.getMsg('PHP_CONF_7')},
            {'name': 'file_uploads', 'type': 1, 'ps': public.getMsg('PHP_CONF_8')},
            {'name': 'upload_max_filesize', 'type': 2, 'ps': public.getMsg('PHP_CONF_9')},
            {'name': 'max_file_uploads', 'type': 2, 'ps': public.getMsg('PHP_CONF_10')},
            {'name': 'default_socket_timeout', 'type': 2, 'ps': public.getMsg('PHP_CONF_11')},
            {'name': 'error_reporting', 'type': 3, 'ps': public.getMsg('PHP_CONF_12')},
            {'name': 'display_errors', 'type': 1, 'ps': public.getMsg('PHP_CONF_13')},
            {'name': 'cgi.fix_pathinfo', 'type': 0, 'ps': public.getMsg('PHP_CONF_14')},
            {'name': 'date.timezone', 'type': 3, 'ps': public.getMsg('PHP_CONF_15')}
        ]
        phpini_file = '/www/server/php/' + get.version + '/etc/php.ini'
        if public.get_webserver() == 'openlitespeed':
            phpini_file = '/usr/local/lsws/lsphp{}/etc/php/{}.{}/litespeed/php.ini'.format(get.version, get.version[0],
                                                                                           get.version[1])
            if os.path.exists('/etc/redhat-release'):
                phpini_file = '/usr/local/lsws/lsphp' + get.version + '/etc/php.ini'
        phpini = public.readFile(phpini_file)
        if not phpini:
            return public.returnMsg(False, "读取PHP配置文件出错，请尝试重新安装这个PHP！")
        result = []
        for g in gets:
            rep = g['name'] + r'\s*=\s*([0-9A-Za-z_&/ ~]+)(\s*;?|\r?\n)'
            tmp = re.search(rep, phpini)
            if not tmp: continue
            g['value'] = tmp.groups()[0]
            result.append(g)

        return result

    def get_php_config(self, get):
        # 取PHP配置
        get.version = get.version.replace('.', '')
        file = session['setupPath'] + "/php/" + get.version + "/etc/php.ini"
        if public.get_webserver() == 'openlitespeed':
            file = '/usr/local/lsws/lsphp{}/etc/php/{}.{}/litespeed/php.ini'.format(get.version, get.version[0],
                                                                                    get.version[1])
            if os.path.exists('/etc/redhat-release'):
                file = '/usr/local/lsws/lsphp' + get.version + '/etc/php.ini'
        phpini = public.readFile(file)
        file = session['setupPath'] + "/php/" + get.version + "/etc/php-fpm.conf"
        phpfpm = public.readFile(file)
        data = {}
        try:
            rep = r"upload_max_filesize\s*=\s*([0-9]+)M"
            tmp = re.search(rep, phpini).groups()
            data['max'] = tmp[0]
        except:
            data['max'] = '50'
        try:
            rep = r"request_terminate_timeout\s*=\s*([0-9]+)\n"
            tmp = re.search(rep, phpfpm).groups()
            data['maxTime'] = tmp[0]
        except:
            data['maxTime'] = 0

        try:
            rep = r"\n;*\s*cgi\.fix_pathinfo\s*=\s*([0-9]+)\s*\n"
            tmp = re.search(rep, phpini).groups()

            if tmp[0] == '1':
                data['pathinfo'] = True
            else:
                data['pathinfo'] = False
        except:
            data['pathinfo'] = False

        return data

    # 提交PHP配置参数
    def SetPHPConf(self, get):
        php_list = ["52", "53", "54", "55", "56", "70", "71", "72", "73", "74", "80", "81", "82", "83", "84"]
        if not hasattr(get, 'version'):
            return public.returnMsg(False, 'PHP版本错误!')
        if get.version not in php_list:
            return public.returnMsg(False, 'PHP版本错误!')
        gets = ['display_errors', 'cgi.fix_pathinfo', 'date.timezone', 'short_open_tag', 'asp_tags',
                'max_execution_time', 'max_input_time', 'memory_limit', 'post_max_size', 'file_uploads',
                'upload_max_filesize', 'max_file_uploads', 'default_socket_timeout', 'error_reporting']
        filename = '/www/server/php/' + get.version + '/etc/php.ini'
        reload_str = '/etc/init.d/php-fpm-' + get.version + ' reload'
        ols_php_path = '/usr/local/lsws/lsphp{}/etc/php/{}.{}/litespeed/php.ini'.format(get.version, get.version[0],
                                                                                        get.version[1])
        if os.path.exists('/etc/redhat-release'):
            ols_php_path = '/usr/local/lsws/lsphp' + get.version + '/etc/php.ini'
        reload_ols_str = '/usr/local/lsws/bin/lswsctrl restart'
        for p in [filename, ols_php_path]:
            if not p:
                continue
            if not os.path.exists(p):
                continue
            phpini = public.readFile(p)
            for g in gets:
                try:
                    rep = g + r'\s*=\s*(.+)\r?\n'
                    val = g + ' = ' + get[g] + '\n'
                    phpini = re.sub(rep, val, phpini)
                except:
                    continue

            public.writeFile(p, phpini)
        public.ExecShell(reload_str)
        public.ExecShell(reload_ols_str)
        return public.returnMsg(True, 'SET_SUCCESS')

    # 取Session缓存方式
    def GetSessionConf(self, get):
        filename = '/www/server/php/' + get.version + '/etc/php.ini'
        if public.get_webserver() == 'openlitespeed':
            filename = '/usr/local/lsws/lsphp{}/etc/php/{}.{}/litespeed/php.ini'.format(get.version, get.version[0],
                                                                                        get.version[1])
            if os.path.exists('/etc/redhat-release'):
                filename = '/usr/local/lsws/lsphp' + get.version + '/etc/php.ini'
        phpini = public.readFile(filename)
        rep = r'session.save_handler\s*=\s*([0-9A-Za-z_& ~]+)(\s*;?|\r?\n)'
        save_handler = re.search(rep, phpini)
        try:
            save_handler = re.search(rep, phpini)
            if save_handler:
                save_handler = save_handler.group(1)
            else:
                save_handler = "files"
        except:
            save_handler = "files"

        reppath = r'\nsession.save_path\s*=\s*"tcp\:\/\/([\w\.]+):(\d+).*\r?\n'
        passrep = r'\nsession.save_path\s*=\s*"tcp://[\w\.\?\:]+=(.*)"\r?\n'
        memcached = r'\nsession.save_path\s*=\s*"([\w\.]+):(\d+)"'
        try:
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
        except:
            passwd = ""
            save_path = ""
            port = ""
        return {"save_handler": save_handler, "save_path": save_path, "passwd": passwd, "port": port}

    # 设置Session缓存方式
    def SetSessionConf(self, get):
        import glob
        g = get.save_handler
        ip = get.ip.strip()
        port = get.port
        passwd = get.passwd
        if g != "files":
            iprep = r"(2(5[0-5]{1}|[0-4]\d{1})|[0-1]?\d{1,2})\.(2(5[0-5]{1}|[0-4]\d{1})|[0-1]?\d{1,2})\.(2(5[0-5]{1}|[0-4]\d{1})|[0-1]?\d{1,2})\.(2(5[0-5]{1}|[0-4]\d{1})|[0-1]?\d{1,2})"
            rep_domain = "^(?=^.{3,255}$)[a-zA-Z0-9\_\-][a-zA-Z0-9\_\-]{0,62}(\.[a-zA-Z0-9\_\-][a-zA-Z0-9\_\-]{0,62})+$"
            if not re.search(iprep, ip) and not re.search(rep_domain, ip):
                if ip != "localhost":
                    return public.returnMsg(False, '请输入正确的【域名或IP】地址！')
            try:
                port = int(port)
                if port >= 65535 or port < 1:
                    return public.returnMsg(False, '请输入正确的端口号')
            except:
                return public.returnMsg(False, '请输入正确的端口号')
            prep = r"[\~\`\/\=]"
            if re.search(prep, passwd):
                return public.returnMsg(False, '请不要输入以下特殊字符 " ~ ` / = "')
        filename = '/www/server/php/' + get.version + '/etc/php.ini'
        filename_ols = None
        ols_exist = os.path.exists("/usr/local/lsws/bin/lswsctrl")
        if ols_exist:
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
        for f in [filename, filename_ols]:
            if not f:
                continue
            phpini = public.readFile(f)
            rep = r'session.save_handler\s*=\s*(.+)\r?\n'
            val = r'session.save_handler = ' + g + '\n'
            phpini = re.sub(rep, val, phpini)
            if not ols_exist:
                if g == "memcached":
                    if not re.search("memcached.so", phpini):
                        return public.returnMsg(False, '请先安装%s扩展' % g)
                    rep = r'\nsession.save_path\s*=\s*(.+)\r?\n'
                    val = r'\nsession.save_path = "%s:%s" \n' % (ip, port)
                    if re.search(rep, phpini):
                        phpini = re.sub(rep, val, phpini)
                    else:
                        phpini = re.sub('\n;session.save_path = "/tmp"', '\n;session.save_path = "/tmp"' + val, phpini)
                if g == "memcache":
                    if not re.search("memcache.so", phpini):
                        return public.returnMsg(False, '请先安装%s扩展' % g)
                    rep = r'\nsession.save_path\s*=\s*(.+)\r?\n'
                    val = r'\nsession.save_path = "tcp://%s:%s"\n' % (ip, port)
                    if re.search(rep, phpini):
                        phpini = re.sub(rep, val, phpini)
                    else:
                        phpini = re.sub('\n;session.save_path = "/tmp"', '\n;session.save_path = "/tmp"' + val, phpini)
                if g == "redis":
                    if not re.search("redis.so", phpini):
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
            else:
                if g == "memcached":
                    if "memcached.so" not in ols_so_list:
                        return public.returnMsg(False, '请先安装%s扩展' % g)
                    rep = r'\nsession.save_path\s*=\s*(.+)\r?\n'
                    val = r'\nsession.save_path = "%s:%s" \n' % (ip, port)
                    if re.search(rep, phpini):
                        phpini = re.sub(rep, val, phpini)
                    else:
                        phpini = re.sub('\n;session.save_path = "/tmp"', '\n;session.save_path = "/tmp"' + val, phpini)
                if g == "memcache":
                    if "memcache.so" not in ols_so_list:
                        return public.returnMsg(False, '请先安装%s扩展' % g)
                    rep = r'\nsession.save_path\s*=\s*(.+)\r?\n'
                    val = r'\nsession.save_path = "tcp://%s:%s"\n' % (ip, port)
                    if re.search(rep, phpini):
                        phpini = re.sub(rep, val, phpini)
                    else:
                        phpini = re.sub('\n;session.save_path = "/tmp"', '\n;session.save_path = "/tmp"' + val, phpini)
                if g == "redis":
                    if "redis.so" not in ols_so_list:
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
        d = ["/tmp", "/www/php_session"]

        count = 0
        for i in d:
            if not os.path.exists(i): public.ExecShell('mkdir -p %s' % i)
            list = os.listdir(i)
            for l in list:
                if os.path.isdir(i + "/" + l):
                    l1 = os.listdir(i + "/" + l)
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

        return {"total": count, "oldfile": old_file}

    # 删除老文件
    def DelOldSession(self, get):
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

    # 获取面板证书
    def GetPanelSSL(self, get):
        cert = {}
        key_file = 'ssl/privateKey.pem'
        cert_file = 'ssl/certificate.pem'
        if not os.path.exists(key_file):
            self.CreateSSL()
        cert['privateKey'] = public.readFile(key_file)
        cert['certPem'] = public.readFile(cert_file)
        cert['download_root'] = False
        cert['info'] = {}
        if not cert['privateKey']:
            cert['privateKey'] = ''
            cert['certPem'] = ''
        else:
            cert['info'] = public.get_cert_data(cert_file)
            if not cert['info']:
                self.CreateSSL()
                cert['info'] = public.get_cert_data(cert_file)
            if cert['info']:
                if cert['info']['issuer'] == '宝塔面板':
                    if os.path.exists('ssl/baota_root.pfx'):
                        cert['download_root'] = True
                        cert['root_password'] = public.readFile('ssl/root_password.pl')
        ssl_path = "/www/server/panel/ssl/"
        if os.path.exists(ssl_path + 'baota_root.pfx') and not os.path.exists(ssl_path + 'baota_root.crt'):
            passwd = ''
            if os.path.exists('{}/root_password.pl'.format(ssl_path)):
                pwd = public.readFile('{}/root_password.pl'.format(ssl_path))
                if pwd.strip():
                    passwd = "-passin file:{ssl_path}root_password.pl".format(ssl_path=ssl_path)
            shell = 'openssl pkcs12 -in {ssl_path}/baota_root.pfx -clcerts -nokeys -out {ssl_path}/baota_root.crt {passwd}'.format(ssl_path=ssl_path,passwd=passwd)
            public.print_log(public.ExecShell(shell))
        cert['rep'] = os.path.exists('ssl/input.pl')
        return cert

    # 保存面板证书
    def SavePanelSSL(self, get):
        keyPath = 'ssl/privateKey.pem'
        certPath = 'ssl/certificate.pem'
        checkCert = '/tmp/cert.pl'
        ssl_pl = 'data/ssl.pl'
        if not 'certPem' in get: return public.returnMsg(False, '缺少certPem参数!')
        if not 'privateKey' in get: return public.returnMsg(False, '缺少privateKey参数!')

        import ssl_info
        # 验证证书和密钥是否匹配格式是否为pem
        ssl_info = ssl_info.ssl_info()
        check_flag, check_msg = ssl_info.verify_certificate_and_key_match(get.privateKey, get.certPem)
        if not check_flag: return public.returnMsg(False, check_msg)
        # 验证证书链是否完整
        check_chain_flag, check_chain_msg = ssl_info.verify_certificate_chain(get.certPem)
        if not check_chain_flag: return public.returnMsg(False, check_chain_msg)

        public.writeFile(checkCert, get.certPem)
        if not public.CheckCert(checkCert):
            os.remove(checkCert)
            return public.returnMsg(False, '证书错误,请检查!')
        if get.privateKey:
            public.writeFile(keyPath, get.privateKey)
        if get.certPem:
            public.writeFile(certPath, get.certPem)
        public.writeFile('ssl/input.pl', 'True')
        if os.path.exists(ssl_pl): public.writeFile('data/reload.pl', 'True')
        return public.returnMsg(True, '证书已保存!')

    # 获取ftp端口
    def get_ftp_port(self):
        # 获取FTP端口
        if 'port' in session: return session['port']
        import re
        try:
            file = public.GetConfigValue('setup_path') + '/pure-ftpd/etc/pure-ftpd.conf'
            conf = public.readFile(file)
            rep = r"\n#?\s*Bind\s+[0-9]+\.[0-9]+\.[0-9]+\.+[0-9]+,([0-9]+)"
            port = re.search(rep, conf).groups()[0]
        except:
            port = '21'
        session['port'] = port
        return port

    # 获取配置
    def get_config(self, get):
        import system
        data = {}
        data.update(system.system().GetConcifInfo())
        if 'config' in session:
            session['config']['distribution'] = public.get_linux_distribution()
            session['webserver'] = public.get_webserver()
            session['config']['webserver'] = session['webserver']
            if "basic_auth" in session['config'].keys():
                session['config']['basic_auth'] = self.get_basic_auth_stat(None)
            data = session['config']
        if not data:
            data = public.M('config').where("id=?", ('1',)).field(
                'webserver,sites_path,backup_path,status,mysql_root').find()
        data['webserver'] = public.get_webserver()
        data['distribution'] = public.get_linux_distribution()
        data['request_iptype'] = self.get_request_iptype()
        data['request_type'] = self.get_request_type()
        data['improvement'] = public.get_improvement()
        data['isSetup'] = True
        data['ftpPort'] = int(self.get_ftp_port())
        data['basic_auth'] = self.get_basic_auth_stat(None)
        data['recycle_bin'] = os.path.exists("data/recycle_bin.pl")
        data['recycle_db_bin'] = os.path.exists('data/recycle_bin_db.pl')
        data['notice_risk_ignore'] = self.get_notice_risk_ignore()
        if os.path.exists(public.GetConfigValue('setup_path') + '/nginx') == False \
                and os.path.exists(public.GetConfigValue('setup_path') + '/apache') == False \
                and os.path.exists('/usr/local/lsws/bin/lswsctrl') == False \
                and os.path.exists(public.GetConfigValue('setup_path') + '/php') == False:
            # 查询安装过或者是有正在安装的任务就不显示推荐安装
            num = public.M('tasks').where("name like ? or name like ? or name like ? or name like ? or name like ?", ('%nginx%', '%apache%', '%php%', '%mysql%', '%pureftpd%')).count()
            if not num:
                data['isSetup'] = False
        p_token = self.get_token(None)
        data['app'] = {'open': p_token['open'], 'apps': p_token['apps']}
        if 'api' not in data: data['api'] = 'checked' if p_token['open'] else ''
        import panelSSL
        data['user_info'] = panelSSL.panelSSL().GetUserInfo(None)
        data['user'] = {}
        try:
            data['user']['username'] = public.get_user_info()['username']
        except:
            pass
        data['table_header'] = self.get_table_header(None)
        data["debug"] = "checked" if self.get_debug() else ""

        data["left_title"] = public.readFile("data/title.pl") if os.path.exists("data/title.pl") else ""

        from password import password
        data["username"] = password().get_panel_username(get)
        data["webname"] = public.GetConfigValue("title")

        sess_out_path = 'data/session_timeout.pl'
        if not os.path.exists(sess_out_path):
            public.writeFile(sess_out_path, '86400')
        s_time_tmp = public.readFile(sess_out_path)
        try:
            s_time = int(s_time_tmp)
        except:
            public.writeFile(sess_out_path, '86400')
            s_time = 86400

        data['session_timeout_source'] = s_time
        data['session_timeout'] = self.show_time_by_seconds(s_time)

        data['SSL'] = os.path.exists('data/ssl.pl')

        return data
        # data = {}
        # if 'config' in session:
        #     session['config']['distribution'] = public.get_linux_distribution()
        #     session['webserver'] = public.get_webserver()
        #     session['config']['webserver'] = session['webserver']
        #     data = session['config']
        # if not data:
        #     data = public.M('config').where("id=?",('1',)).field('webserver,sites_path,backup_path,status,mysql_root').find()
        # data['webserver'] = public.get_webserver()
        # data['distribution'] = public.get_linux_distribution()
        # data['request_iptype'] = self.get_request_iptype()
        # data['request_type'] = self.get_request_type()
        # data['improvement'] = public.get_improvement()
        # return data

    # 取面板错误日志
    def get_error_logs(self, get):
        return public.GetNumLines('logs/error.log', 2000)

    def is_pro(self, get):
        import panelAuth, json
        pdata = panelAuth.panelAuth().create_serverid(None)
        url = public.GetConfigValue('home') + '/api/panel/is_pro'
        pluginTmp = public.httpPost(url, pdata)
        pluginInfo = json.loads(pluginTmp)
        return pluginInfo

    def get_token(self, get):
        import panelApi
        return panelApi.panelApi().get_token(get)

    def set_token(self, get):
        import panelApi
        return panelApi.panelApi().set_token(get)

    def get_tmp_token(self, get):
        import panelApi
        return panelApi.panelApi().get_tmp_token(get)

    def GetNginxValue(self, get):
        n = nginx.nginx()
        return n.GetNginxValue()

    def SetNginxValue(self, get):
        n = nginx.nginx()
        return n.SetNginxValue(get)

    def GetApacheValue(self, get):
        a = apache.apache()
        return a.GetApacheValue()

    def SetApacheValue(self, get):
        a = apache.apache()
        return a.SetApacheValue(get)

    def get_ols_value(self, get):
        a = ols.ols()
        return a.get_value(get)

    def set_ols_value(self, get):
        a = ols.ols()
        return a.set_value(get)

    def get_ols_private_cache(self, get):
        a = ols.ols()
        return a.get_private_cache(get)

    def get_ols_static_cache(self, get):
        a = ols.ols()
        return a.get_static_cache(get)

    def set_ols_static_cache(self, get):
        a = ols.ols()
        return a.set_static_cache(get)

    def switch_ols_private_cache(self, get):
        a = ols.ols()
        return a.switch_private_cache(get)

    def set_ols_private_cache(self, get):
        a = ols.ols()
        return a.set_private_cache(get)

    def get_ols_private_cache_status(self, get):
        a = ols.ols()
        return a.get_private_cache_status(get)

    def get_ipv6_listen(self, get):
        return os.path.exists('data/ipv6.pl')

    def set_ipv6_status(self, get):
        ipv6_file = 'data/ipv6.pl'
        if self.get_ipv6_listen(get):
            os.remove(ipv6_file)
            public.WriteLog('面板设置', '关闭面板IPv6兼容!')
        else:
            public.writeFile(ipv6_file, 'True')
            public.WriteLog('面板设置', '开启面板IPv6兼容!')
        public.restart_panel()
        return public.returnMsg(True, '设置成功!')

    # 自动补充CLI模式下的PHP版本
    def auto_cli_php_version(self, get):
        import panelSite
        php_versions = panelSite.panelSite().GetPHPVersion(get)
        if len(php_versions) == 0:
            return public.returnMsg(False, '获取失败!')
        php_bin_src = "/www/server/php/%s/bin/php" % php_versions[-1]['version']
        if not os.path.exists(php_bin_src): return public.returnMsg(False, '未安装PHP!')
        get.php_version = php_versions[-1]['version']
        self.set_cli_php_version(get)
        return php_versions[-1]

    # 获取CLI模式下的PHP版本
    def get_cli_php_version(self, get):
        php_bin = '/usr/bin/php'
        if not os.path.exists(php_bin) or not os.path.islink(php_bin):  return self.auto_cli_php_version(get)
        link_re = os.readlink(php_bin)
        if not os.path.exists(link_re): return self.auto_cli_php_version(get)
        import panelSite
        php_versions = panelSite.panelSite().GetPHPVersion(get)
        if len(php_versions) == 0:
            return public.returnMsg(False, '获取失败!')
        del (php_versions[0])
        for v in php_versions:
            if link_re.find(v['version']) != -1: return {"select": v, "versions": php_versions}
        return {"select": self.auto_cli_php_version(get), "versions": php_versions}

    # 设置CLI模式下的PHP版本
    def set_cli_php_version(self, get):
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
        php_cli_ini = '/etc/php-cli.ini'
        php_cli_ini_src = "/www/server/php/%s/etc/php-cli.ini" % get.php_version
        if not os.path.exists(php_bin_src): return public.returnMsg(False, '指定PHP版本未安装!')
        is_chattr = public.ExecShell('lsattr /usr|grep /usr/bin')[0].find('-i-')
        if is_chattr != -1: public.ExecShell('chattr -i /usr/bin')
        public.ExecShell(
            "rm -f " + php_bin + ' ' + php_ize + ' ' + php_fpm + ' ' + php_pecl + ' ' + php_pear + ' ' + php_cli_ini)
        public.ExecShell("ln -sf %s %s" % (php_bin_src, php_bin))
        public.ExecShell("ln -sf %s %s" % (php_ize_src, php_ize))
        public.ExecShell("ln -sf %s %s" % (php_fpm_src, php_fpm))
        public.ExecShell("ln -sf %s %s" % (php_pecl_src, php_pecl))
        public.ExecShell("ln -sf %s %s" % (php_pear_src, php_pear))
        public.ExecShell("ln -sf %s %s" % (php_cli_ini_src, php_cli_ini))
        import jobs
        jobs.set_php_cli_env()
        if is_chattr != -1:  public.ExecShell('chattr +i /usr/bin')
        public.WriteLog('面板设置', '设置PHP-CLI版本为: %s' % get.php_version)
        return public.returnMsg(True, '设置成功!')

    # 获取BasicAuth状态
    def get_basic_auth_stat(self, get):
        path = 'config/basic_auth.json'
        is_install = True
        result = {"basic_user": "", "basic_pwd": "", "open": False, "is_install": is_install}
        if not os.path.exists(path): return result
        try:
            ba_conf = json.loads(public.readFile(path))
        except:
            os.remove(path)
            return result
        ba_conf['is_install'] = is_install
        return ba_conf

    # 设置BasicAuth
    def set_basic_auth(self, get):
        is_open = False
        if get.open == 'True': is_open = True
        tips = '_bt.cn'
        path = 'config/basic_auth.json'
        ba_conf = None
        if is_open:
            if not get.basic_user.strip() or not get.basic_pwd.strip(): return public.returnMsg(False,
                                                                                                'BasicAuth认证用户名和密码不能为空!')
        if os.path.exists(path):
            try:
                ba_conf = json.loads(public.readFile(path))
            except:
                os.remove(path)

        if not ba_conf:
            ba_conf = {"basic_user": public.md5(get.basic_user.strip() + tips),
                       "basic_pwd": public.md5(get.basic_pwd.strip() + tips), "open": is_open}
        else:
            if get.basic_user: ba_conf['basic_user'] = public.md5(get.basic_user.strip() + tips)
            if get.basic_pwd: ba_conf['basic_pwd'] = public.md5(get.basic_pwd.strip() + tips)
            ba_conf['open'] = is_open

        public.writeFile(path, json.dumps(ba_conf))
        os.chmod(path, 384)
        public.WriteLog('面板设置', '设置BasicAuth状态为: %s' % is_open)
        public.add_security_logs('面板设置', ' 设置BasicAuth状态为: %s' % is_open)
        public.writeFile('data/reload.pl', 'True')
        return public.returnMsg(True, "设置成功!")

    # xss 防御
    def xsssec(self, text):
        return text.replace('<', '&lt;').replace('>', '&gt;')

    # 取面板运行日志
    def get_panel_error_logs(self, get):
        filename = 'logs/error.log'
        if not os.path.exists(filename): return public.returnMsg(False, '没有找到运行日志')
        result = public.GetNumLines(filename, 2000)
        return public.returnMsg(True, self.xsssec(result))

    # 清空面板运行日志
    def clean_panel_error_logs(self, get):
        filename = 'logs/error.log'
        public.writeFile(filename, '')
        public.WriteLog('面板配置', '清空面板运行日志')
        public.add_security_logs('运行日志', ' 清空面板运行日志')
        return public.returnMsg(True, '已清空!')

    # 获取lets证书
    def get_cert_source(self, get):
        import setPanelLets
        sp = setPanelLets.setPanelLets()
        spg = sp.get_cert_source()
        return spg

    # 设置debug模式
    def set_debug(self, get):
        debug_path = 'data/debug.pl'
        if os.path.exists(debug_path):
            t_str = '关闭'
            os.remove(debug_path)
        else:
            t_str = '开启'
            public.writeFile(debug_path, 'True')
        public.WriteLog('面板配置', '%s开发者模式(debug)' % t_str)
        public.restart_panel()
        return public.returnMsg(True, '设置成功!')

    # 获取debug状态
    def get_debug(self):
        debug_path = 'data/debug.pl'
        return ((os.path.exists(debug_path) and (public.readFile(debug_path) == "True")))

    def Get_debug(self, get):
        return {"debug": "checked" if self.get_debug() else ""}

    # 设置离线模式
    def set_local(self, get):
        d_path = 'data/not_network.pl'
        if os.path.exists(d_path):
            t_str = '关闭'
            os.remove(d_path)
        else:
            t_str = '开启'
            public.writeFile(d_path, 'True')
        public.WriteLog('面板配置', '%s离线模式' % t_str)
        return public.returnMsg(True, '设置成功!')

    # 修改.user.ini文件
    def _edit_user_ini(self, file, s_conf, act, session_path):
        public.ExecShell("chattr -i {}".format(file))
        conf = public.readFile(file)
        if not conf:
            return False
        if act == "1":
            if "session.save_path" in conf:
                return False
            conf = conf + ":{}/".format(session_path)
            conf = conf + "\n" + s_conf
        else:
            rep = "\n*session.save_path(.|\n)*files"
            rep1 = ":{}".format(session_path)
            conf = re.sub(rep, "", conf)
            conf = re.sub(rep1, "", conf)
        public.writeFile(file, conf)
        public.ExecShell("chattr +i {}".format(file))

    # 设置php_session存放到独立文件夹
    def set_php_session_path(self, get):
        '''
        get.id      site id
        get.act     0/1
        :param get:
        :return:
        '''
        if not hasattr(get, 'id'):
            return public.returnMsg(False, "缺少参数! id")

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
                public.writeFile(user_ini_file, conf)
                public.ExecShell("chattr +i {}".format(user_ini_file))
                return public.returnMsg(True, "设置成功")
            self._edit_user_ini(user_ini_file, conf, get.act, session_path)
            return public.returnMsg(True, "设置成功")
        else:
            self._edit_user_ini(user_ini_file, conf, get.act, session_path)
            return public.returnMsg(True, "设置成功")

    # 获取php_session是否存放到独立文件夹
    def get_php_session_path(self, get):
        import panelSite
        site_info = public.M('sites').where('id=?', (get.id,)).field('name,path').find()
        if site_info:
            run_path = panelSite.panelSite().GetSiteRunPath(get)["runPath"]
            user_ini_file = "{site_path}{run_path}/.user.ini".format(site_path=site_info["path"], run_path=run_path)
            conf = public.readFile(user_ini_file)
            if conf and "session.save_path" in conf:
                return True
        return False

    def _create_key(self):
        get_token = pyotp.random_base32()  # returns a 16 character base32 secret. Compatible with Google Authenticator
        public.writeFile(self._key_file, get_token)
        username = self.get_random()
        public.writeFile(self._username_file, username)

    def get_key(self, get):
        key = public.readFile(self._key_file)
        username = public.readFile(self._username_file)
        if not key:
            return public.returnMsg(False, "秘钥不存在，请开启后再试")
        if not username:
            return public.returnMsg(False, "用户名不存在，请开启后再试")
        return {"key": key, "username": username}

    def get_random(self):
        import random
        seed = "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        sa = []
        for _ in range(8):
            sa.append(random.choice(seed))
        salt = ''.join(sa)
        return salt

    def set_two_step_auth(self, get):
        if not hasattr(get, "act") or not get.act:
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
                os.rename(self._bk_key_file, self._key_file)
            secret_key = public.readFile(self._key_file)
            username = public.readFile(self._username_file)
            local_ip = public.GetLocalIp()
            if not secret_key:
                return public.returnMsg(False,
                                        "生成key或username失败，请检查硬盘空间是否不足或目录无法写入[ {} ]".format(
                                            self._setup_path + "/data/"))
            try:
                try:
                    panel_name = json.loads(public.readFile(self._setup_path + '/config/config.json'))['title']
                except:
                    panel_name = '宝塔Linux面板'
                data = pyotp.totp.TOTP(secret_key).provisioning_uri(username,
                                                                    issuer_name='{}--{}'.format(panel_name, local_ip))
                public.writeFile(self._core_fle_path + '/qrcode.txt', str(data))
                return public.returnMsg(True, "开启成功")
            except Exception as e:
                return public.returnMsg(False, e)
        else:
            if os.path.exists(self._key_file):
                os.rename(self._key_file, self._bk_key_file)

            if os.path.exists("/www/server/panel/data/dont_vcode_ip.txt"):
                os.remove("/www/server/panel/data/dont_vcode_ip.txt")
            return public.returnMsg(True, "关闭成功")

    # 检测是否开启双因素验证
    def check_two_step(self, get):
        secret_key = public.readFile(self._key_file)
        if not secret_key:
            return public.returnMsg(False, "没有开启二步验证")
        return public.returnMsg(True, "已经开启二步验证")

    # 读取二维码data
    def get_qrcode_data(self, get):
        data = public.readFile(self._core_fle_path + '/qrcode.txt')
        if data:
            return data
        return public.returnMsg(True, "没有二维码数据，请重新开启")

    # 设置是否云控打开
    def set_coll_open(self, get):
        if not 'coll_show' in get: return public.returnMsg(False, '错误的参数!')
        if get.coll_show == 'True':
            session['tmp_login'] = True
        else:
            session['tmp_login'] = False
        return public.returnMsg(True, '设置成功!')

    # 是否显示软件推荐
    def show_recommend(self, get):
        pfile = 'data/not_recommend.pl'
        if os.path.exists(pfile):
            os.remove(pfile)
        else:
            public.writeFile(pfile, 'True')
        return public.returnMsg(True, '设置成功!')

    # 是否显示工单
    def show_workorder(self, get):
        pfile = 'data/not_workorder.pl'
        if os.path.exists(pfile):
            os.remove(pfile)
        else:
            public.writeFile(pfile, 'True')
        return public.returnMsg(True, '设置成功!')

    # 获取菜单列表
    def get_menu_list_old(self, get):
        '''
            @name 获取菜单列表
            @author hwliang<2020-08-31>
            @param get<dict_obj>
            @return list
        '''
        try:
            menu_file = '/www/server/panel/config/menu.json'
            menu_data = json.loads(public.ReadFile(menu_file))["menu"]
            hide_menu_file = '/www/server/panel/config/hide_menu.json'
            show_menu_file = '/www/server/panel/config/show_menu.json'
            default_data = ["memuA", "memuAsite", "memuAdatabase", 'memuDocker', "memuAcontrol", "memuAfirewall", "memuAfiles", "memuAlogs", "memuAxterm", "memuAcrontab", "memuAsoft", "memuAconfig", "dologin", "memu_btwaf"]
            show_menu_data = default_data
            if os.path.exists(show_menu_file):
                data = public.ReadFile(show_menu_file)
                if data:
                    try:
                        show_menu_data = json.loads(data)
                    except:
                        public.ExecShell('rm -f ' + show_menu_file)
                if "memu_total" in show_menu_data:
                    show_menu_data.remove("memu_total")
                    public.writeFile(show_menu_file, json.dumps(show_menu_data))
            # 获取之前设置的隐藏页面
            try:
                if os.path.exists(hide_menu_file):
                    hide_menu = public.ReadFile(hide_menu_file)
                    show_menu_data = [i for i in show_menu_data if i not in hide_menu]
                    public.ExecShell("rm -rf {}".format(hide_menu_file))
            except:
                pass
                # 将显示菜单保存
            if 'memuA' not in show_menu_data:
                show_menu_data.append('memuA')
            # 新增菜单保存到文件
            path = '/www/server/panel/config/{}.pl'
            menu_list = ["memuAvhost"]
            for menu in menu_list:
                if not os.path.exists(path.format(menu)):
                    # if menu == "memuAmail" and not os.path.exists('/www/server/panel/plugin/mail_sys'):
                    #     continue
                    public.writeFile(path.format(menu), '')
                    if menu not in show_menu_data:
                        show_menu_data.append(menu)

            public.WriteFile(show_menu_file, json.dumps(show_menu_data))
            default_site_menu = ['php', 'java', 'node', 'go', 'python', 'net', 'nginx', 'html',"other"]
            default_site_menu_name = {'php': 'PHP网站', 'java': 'java项目', 'node': 'Node.js项目', 'go': 'Go项目', 'python': 'Python项目', 'net': '.NET项目', 'other': '其他项目', 'nginx': '反向代理','html':'HTML项目'}
            site_menu = ['php', 'java', 'node', 'go', 'python', 'net', 'nginx', 'html',"other"]
            if os.path.exists('/www/server/panel/data/site_menu.json'):
                site_menu_data = public.readFile('/www/server/panel/data/site_menu.json')
                if site_menu_data:
                    site_menu = json.loads(site_menu_data)
            result = []
            for d in menu_data:
                tmp = {}
                tmp['id'] = d['id']
                tmp['title'] = d['title']
                tmp['show'] = d['id'] in show_menu_data
                tmp['sort'] = d['sort']
                if d['id'] == 'memuAsite':
                    tmp['children'] = []
                    for i in default_site_menu:
                        con = {}
                        con['id'] = i
                        con['title'] = default_site_menu_name[i]
                        con['show'] = i in site_menu
                        tmp['children'].append(con)
                result.append(tmp)
            uid = session.get('uid')
            if uid != 1 and uid:
                if public.M('users').where('id=?', (uid,)).select():
                    plugin_path = '/www/server/panel/plugin/users'
                    if not os.path.exists(plugin_path): return []
                    user_authority = os.path.join(plugin_path, 'authority')
                    if not os.path.exists(user_authority): return []

                    if not os.path.exists(os.path.join(user_authority, str(uid))): return []
                    try:
                        data = json.loads(self._decrypt(public.ReadFile(os.path.join(user_authority, str(uid)))))
                        if not int(data['state']): return [{'id': 'dologin', 'title': '退出', 'show': True, 'sort': 18}]
                        if data['role'] == 'administrator':
                            menus = sorted(result, key=lambda x: x['sort'])
                            return menus
                        else:
                            for i in result:
                                __menu_dict = {m['id']: m['href'] for m in menu_data}
                                if self.__menu_dict[i['id']] in data['menu'] or i['id'] == 'dologin':
                                    i['show'] = True
                                else:
                                    i['show'] = False
                    except:
                        return []
            menus = sorted(result, key=lambda x: x['sort'])
            return menus
        except:
            print(traceback.format_exc())


    # 新增菜单需要
    # 在 menu.json 中添加
    # 在 init.py 中添加入口
    # 前端添加一条相同菜单
    def update_menu_show(self, menu_data, show_menu_data):
        show_menu_data = {i["id"]: i for i in show_menu_data} if show_menu_data else {}
        for menu in menu_data:
            if menu['id'] in show_menu_data.keys():
                menu['show'] = show_menu_data[menu['id']]['show']
                if menu['children']:
                    menu['children'] = self.update_menu_show(menu['children'], show_menu_data[menu['id']].get("children", []))
        return menu_data

    def get_menu_list(self, get):
        default_path = '/www/server/panel/config/menu.json'
        local_menu_path = '/www/server/panel/config/local_menu.json'

        if not os.path.exists(local_menu_path):
            if not os.path.exists("/www/server/panel/config/show_menu.json"):
                menu_data = {}
            else:
                menu_data = {"version": "", "menu": self.get_menu_list_old(None)}
        else:
            try:
                menu_data = json.loads(public.readFile(local_menu_path))
            except:
                menu_data = {}
        default_data = json.loads(public.readFile(default_path))

        if menu_data:
            if menu_data['version'] != default_data['version']:
                menu_data["menu"] = self.update_menu_show(default_data['menu'], menu_data['menu'])
                menu_data['version'] = default_data['version']
                public.writeFile(local_menu_path, json.dumps(menu_data))
        else:
            menu_data = default_data
            public.writeFile(local_menu_path, json.dumps(menu_data))
        if get == "local":
            return menu_data

        uid = session.get('uid')
        if uid != 1 and uid:
            return self.get_menu_list_old(None)

        return menu_data['menu']

    def set_hide_menu_list(self, get):
        hide_list = json.loads(get.hide_list)

        menu_data = self.get_menu_list("local")
        menu_data['menu'] = self._edit_menu(menu_data['menu'], hide_list)
        public.writeFile('/www/server/panel/config/local_menu.json', json.dumps(menu_data))
        return public.returnMsg(True, '设置成功')

    def _edit_menu(self, menu_data, hide_list):
        for menu in menu_data:
            if menu['id'] in hide_list:
                menu['show'] = not menu['show']
                menu['update_time'] = int(time.time())
            if menu['children']:
                menu['children'] = self._edit_menu(menu['children'], hide_list)
        return menu_data

    # 数据解密
    def _decrypt(self, data):
        if not isinstance(data, str): return data
        if not data: return data
        if data.startswith('BT-0x:'):
            res = PluginLoader.db_decrypt(data[6:])['msg']
            return res
        return data

    def set_site_hide_menu(self, get):
        """
        设置站点菜单隐藏菜单
        :param get:
        :return:
        """
        hide_list = json.loads(get.hide_list)
        site_hide_menu = ['php', 'java', 'node', 'go', 'python', 'net', 'other', 'nginx', 'html']
        if os.path.exists("/www/server/panel/data/site_menu.json"):
            data = public.ReadFile("/www/server/panel/data/site_menu.json")
            if data:
                try:
                    site_hide_menu = json.loads(data)
                    site_hide_menu.remove("proxy")
                except:
                    pass
        for i in hide_list:
            if i in site_hide_menu:
                if len(site_hide_menu) == 1: return public.returnMsg(False, "至少保留1个网站项目!")
                site_hide_menu.remove(i)
            else:
                site_hide_menu.append(i)
        public.WriteFile("/www/server/panel/data/site_menu.json", json.dumps(site_hide_menu))
        try:
            g.menus = json.dumps(self.get_menu_list(None))
        except:
            pass
        return public.returnMsg(True, "设置成功")

    # 设置隐藏菜单列表
    def set_hide_menu_list_old(self, get):
        '''
            @name 设置隐藏菜单列表
            @author hwliang<2020-08-31>
            @param get<dict_obj> {
                hide_list: json<list> 所有不显示的菜单ID
            }
            @return dict
        '''
        show_menu_file = '/www/server/panel/config/show_menu.json'
        not_hide_id = ["dologin", "memuAconfig", "memuAsoft", "memuA"]  # 禁止隐藏的菜单
        show_menu_data = ['memuA', 'memuAsite', 'memuAftp', 'memuAdatabase', 'memuDocker', 'memuAcontrol', 'memuAfirewall', 'memuAfiles', 'memuAlogs', 'memuAxterm', 'memuAssl', 'memuAcrontab', 'memuAsoft',
                          'memuAconfig', 'dologin', 'memuAssl']
        if hasattr(get, 'site_menu') and int(get.site_menu) == 1:
            return self.set_site_hide_menu(get)
        hide_list = json.loads(get.hide_list)
        if os.path.exists(show_menu_file):
            show_menu_data = json.loads(public.ReadFile(show_menu_file))

        for i in hide_list:
            if i in not_hide_id: continue
            if i in show_menu_data:
                show_menu_data.remove(i)
            else:
                show_menu_data.append(i)
        public.writeFile(show_menu_file, json.dumps(show_menu_data))
        try:
            g.menus = json.dumps(self.get_menu_list(None))
            session['menu'] = g.menus
        except:
            pass
        public.WriteLog('面板设置', '修改面板菜单显示列表成功')
        return public.returnMsg(True, '设置成功')

    # 获取临时登录列表
    def get_temp_login(self, args):
        '''
            @name 获取临时登录列表
            @author hwliang<2020-09-2>
            @return dict
        '''
        if 'tmp_login_expire' in session: return public.returnMsg(False, '没有权限')
        public.M('temp_login').where('state=? and expire<?', (0, int(time.time()))).setField('state', -1)
        callback = ''
        if 'tojs' in args:
            callback = args.tojs
        p = 1
        if 'p' in args:
            p = int(args.p)
        rows = 12
        if 'rows' in args:
            rows = int(args.rows)
        count = public.M('temp_login').count()
        data = {}
        page_data = public.get_page(count, p, rows, callback)
        data['page'] = page_data['page']
        data['data'] = public.M('temp_login').limit(page_data['shift'] + ',' + page_data['row']).order('id desc').field(
            'id,addtime,expire,login_time,login_addr,state').select()
        for i in range(len(data['data'])):
            data['data'][i]['online_state'] = os.path.exists('data/session/{}'.format(data['data'][i]['id']))
        return data

    # 设置临时登录
    def set_temp_login(self, get):
        '''
            @name 设置临时登录
            @author hwliang<2020-09-2>
            @return dict
        '''
        s_time = int(time.time())
        expire_time = get.expire_time if "expire_time" in get else s_time + 3600 * 3
        try:
            expire_time = int(expire_time)
        except:
            expire_time = s_time + 3600 * 3
        if 'tmp_login_expire' in session: return public.returnMsg(False, '没有权限')
        public.M('temp_login').where('state=? and expire>?', (0, s_time)).delete()
        token = public.GetRandomString(48)
        salt = public.GetRandomString(12)

        pdata = {
            'token': public.md5(token + salt),
            'salt': salt,
            'state': 0,
            'login_time': 0,
            'login_addr': '',
            'expire': expire_time,
            'addtime': s_time
        }

        if not public.M('temp_login').count():
            pdata['id'] = 101

        if public.M('temp_login').insert(pdata):
            public.WriteLog('面板设置', '生成临时连接,过期时间:{}'.format(public.format_date(times=pdata['expire'])))
            return {'status': True, 'msg': "临时连接已生成", 'token': token, 'expire': pdata['expire']}
        return public.returnMsg(False, '连接生成失败')

    # 删除临时登录
    def remove_temp_login(self, args):
        '''
            @name 删除临时登录
            @author hwliang<2020-09-2>
            @param args<dict_obj>{
                id: int<临时登录ID>
            }
            @return dict
        '''
        if 'tmp_login_expire' in session: return public.returnMsg(False, '没有权限')
        id = int(args.id)
        if public.M('temp_login').where('id=?', (id,)).delete():
            public.WriteLog('面板设置', '删除临时登录连接')
            return public.returnMsg(True, '删除成功')
        return public.returnMsg(False, '删除失败')

    # 强制弹出指定临时登录
    def clear_temp_login(self, args):
        '''
            @name 强制登出
            @author hwliang<2020-09-2>
            @param args<dict_obj>{
                id: int<临时登录ID>
            }
            @return dict
        '''
        if 'tmp_login_expire' in session: return public.returnMsg(False, '没有权限')
        id = int(args.id)
        s_file = 'data/session/{}'.format(id)
        if os.path.exists(s_file):
            os.remove(s_file)
            public.WriteLog('面板设置', '强制弹出临时用户：{}'.format(id))
            return public.returnMsg(True, '已强制退出临时用户：{}'.format(id))
        public.returnMsg(False, '指定用户当前不是登录状态!')

    # 查看临时授权操作日志
    def get_temp_login_logs(self, args):
        '''
            @name 查看临时授权操作日志
            @author hwliang<2020-09-2>
            @param args<dict_obj>{
                id: int<临时登录ID>
            }
            @return dict
        '''
        if 'tmp_login_expire' in session: return public.returnMsg(False, '没有权限')
        id = int(args.id)
        data = public.M('logs').where('uid=?', (id,)).order('id desc').select()
        return data

    def get_file_deny(self, args):
        import file_execute_deny
        p = file_execute_deny.FileExecuteDeny()
        return p.get_file_deny(args)

    def set_file_deny(self, args):
        import file_execute_deny
        p = file_execute_deny.FileExecuteDeny()
        return p.set_file_deny(args)

    def del_file_deny(self, args):
        import file_execute_deny
        p = file_execute_deny.FileExecuteDeny()
        return p.del_file_deny(args)

    # 查看告警
    def get_login_send(self, get):
        send_type = ""
        login_send_type_conf = "/www/server/panel/data/panel_login_send.pl"
        if os.path.exists(login_send_type_conf):
            send_type = public.ReadFile(login_send_type_conf).strip()
        else:

            if os.path.exists("/www/server/panel/data/login_send_type.pl"):
                send_type = public.readFile("/www/server/panel/data/login_send_type.pl")
            else:
                if os.path.exists('/www/server/panel/data/login_send_mail.pl'):
                    send_type = "mail"
                if os.path.exists('/www/server/panel/data/login_send_dingding.pl'):
                    send_type = "dingding"
        return public.returnMsg(True, send_type)

    # 取消告警
    def clear_login_send(self, get):
        type = get.type.strip()
        if type == 'mail':
            if os.path.exists("/www/server/panel/data/login_send_mail.pl"):
                os.remove("/www/server/panel/data/login_send_mail.pl")
        elif type == 'dingding':
            if os.path.exists("/www/server/panel/data/login_send_dingding.pl"):
                os.remove("/www/server/panel/data/login_send_dingding.pl")

        login_send_type_conf = "/www/server/panel/data/login_send_type.pl"
        if os.path.exists(login_send_type_conf):
            os.remove(login_send_type_conf)
        login_send_type_conf = "/www/server/panel/data/panel_login_send.pl"
        if os.path.exists(login_send_type_conf):
            os.remove(login_send_type_conf)
        return public.returnMsg(True, '取消登录告警成功！')

    def get_login_area(self, get):
        """
        @获取面板登录告警
        @return
            login_status 是否开启面板登录告警
            login_area 是否开启面板异地登录告警
        """
        result = {}
        result['login_status'] = self.get_login_send(get)['msg']

        result['login_area'] = ''
        sfile = '{}/data/panel_login_area.pl'.format(public.get_panel_path())
        if os.path.exists(sfile):
            result['login_area_status'] = public.readFile(sfile)
        return result

    def set_login_area(self, get):
        """
        @name 设置异地登录告警
        @param get
        """
        sfile = '{}/data/panel_login_area.pl'.format(public.get_panel_path())
        set_type = get.type.strip()
        obj = public.init_msg(set_type)
        if not obj:
            return public.returnMsg(False, "未安装告警模块。")

        public.writeFile(sfile, set_type)
        return public.returnMsg(True, '设置成功')

    def get_login_area_list(self, get):
        """
        @name 获取面板常用地区登录

        """
        data = {}
        sfile = '{}/data/panel_login_area.json'.format(public.get_panel_path())
        try:
            data = json.loads(public.readFile(sfile))
        except:
            pass

        result = []
        for key in data.keys():
            result.append({'area': key, 'count': data[key]})

        result = sorted(result, key=lambda x: x['count'], reverse=True)
        return result

    def clear_login_list(self, get):
        """
        @name 清理常用登录地区
        """
        sfile = '{}/data/panel_login_area.json'.format(public.get_panel_path())
        if os.path.exists(sfile):
            os.remove(sfile)
        return public.returnMsg(True, '操作成功.')

    # def get_login_send(self,get):
    #     result={}
    #     import time
    #     time.sleep(0.01)
    #     if os.path.exists('/www/server/panel/data/login_send_mail.pl'):
    #         result['mail']=True
    #     else:
    #         result['mail']=False
    #     if os.path.exists('/www/server/panel/data/login_send_dingding.pl'):
    #         result['dingding']=True
    #     else:
    #         result['dingding']=False
    #     if result['mail'] or result['dingding']:
    #         return public.returnMsg(True, result)
    #     return public.returnMsg(False, result)

    # 设置告警
    def set_login_send(self, get):
        login_send_type_conf = "/www/server/panel/data/panel_login_send.pl"

        set_type = get.type.strip()
        msg_configs = self.get_msg_configs(get)
        if set_type not in msg_configs.keys():
            return public.returnMsg(False, '不支持该发送类型')
        _conf = msg_configs[set_type]
        if "data" not in _conf or not _conf["data"]:
            return public.returnMsg(False, "该通道未配置, 请重新选择。")

        from panelMessage import panelMessage
        pm = panelMessage()
        obj = pm.init_msg_module(set_type)
        if not obj:
            return public.returnMsg(False, "消息通道未安装。")

        public.writeFile(login_send_type_conf, set_type)
        return public.returnMsg(True, '设置成功')

        # if type=='mail':
        #     if not os.path.exists("/www/server/panel/data/login_send_mail.pl"):
        #         os.mknod("/www/server/panel/data/login_send_mail.pl")
        #     if os.path.exists("/www/server/panel/data/login_send_dingding.pl"):
        #         os.remove("/www/server/panel/data/login_send_dingding.pl")
        #     return public.returnMsg(True, '设置成功')
        # elif type=='dingding':
        #     if not os.path.exists("/www/server/panel/data/login_send_dingding.pl"):
        #         os.mknod("/www/server/panel/data/login_send_dingding.pl")
        #     if os.path.exists("/www/server/panel/data/login_send_mail.pl"):
        #         os.remove("/www/server/panel/data/login_send_mail.pl")
        #     return public.returnMsg(True, '设置成功')
        # else:
        #     return public.returnMsg(False,'不支持该发送类型')

    # 告警日志
    def get_login_log(self, get):
        public.create_logs()
        import page
        page = page.Page()
        count = public.M('logs2').where('type=?', (u'堡塔登录提醒',)).field('log,addtime').count()
        limit = 7
        info = {}
        info['count'] = count
        info['row'] = limit
        info['p'] = 1
        if hasattr(get, 'p'):
            info['p'] = int(get['p'])
        info['uri'] = get
        info['return_js'] = ''
        if hasattr(get, 'tojs'):
            info['return_js'] = get.tojs
        data = {}
        # 获取分页数据
        data['page'] = page.GetPage(info, '1,2,3,4,5,8')
        data['data'] = public.M('logs2').where('type=?', (u'堡塔登录提醒',)).field('log,addtime').order(
            'id desc').limit(
            str(page.SHIFT) + ',' + str(page.ROW)).field('log,addtime').select()
        return data

    # 白名单设置
    def login_ipwhite(self, get):
        type = get.type
        if type == 'get':
            return self.get_login_ipwhite(get)
        if type == 'add':
            return self.add_login_ipwhite(get)
        if type == 'del':
            return self.del_login_ipwhite(get)
        if type == 'clear':
            return self.clear_login_ipwhite(get)

    # 查看IP白名单
    def get_login_ipwhite(self, get):
        try:
            path = '/www/server/panel/data/send_login_white.json'
            ip_white = json.loads(public.ReadFile('/www/server/panel/data/send_login_white.json'))
            if not ip_white: return public.returnMsg(True, [])
            return public.returnMsg(True, ip_white)
        except:
            public.WriteFile(path, '[]')
            return public.returnMsg(True, [])

    def add_login_ipwhite(self, get):
        ip = get.ip.strip()
        try:
            path = '/www/server/panel/data/send_login_white.json'
            ip_white = json.loads(public.ReadFile('/www/server/panel/data/send_login_white.json'))
            if not ip in ip_white:
                ip_white.append(ip)
                public.WriteFile(path, json.dumps(ip_white))
            return public.returnMsg(True, "添加成功")
        except:
            public.WriteFile(path, json.dumps([ip]))
            return public.returnMsg(True, "添加成功")

    def del_login_ipwhite(self, get):
        ip = get.ip.strip()
        try:
            path = '/www/server/panel/data/send_login_white.json'
            ip_white = json.loads(public.ReadFile('/www/server/panel/data/send_login_white.json'))
            if ip in ip_white:
                ip_white.remove(ip)
                public.WriteFile(path, json.dumps(ip_white))
            return public.returnMsg(True, "删除成功")
        except:
            public.WriteFile(path, json.dumps([]))
            return public.returnMsg(True, "删除成功")

    def clear_login_ipwhite(self, get):
        path = '/www/server/panel/data/send_login_white.json'
        public.WriteFile(path, json.dumps([]))
        return public.returnMsg(True, "清空成功")

    def set_ssl_verify(self, get):
        """
        设置双向认证
        """
        sslConf = 'data/ssl_verify_data.pl'
        status = int(get.status)
        if status:
            if not os.path.exists('data/ssl.pl'): return public.returnMsg(False, '需要先开启面板SSL功能!')
            public.writeFile(sslConf, 'True')
        else:
            if os.path.exists(sslConf): os.remove(sslConf)
            public.restart_panel()

        ca_path = "/www/server/panel/plugin/ssl_verify/client/ca.pem"
        if not os.path.exists(ca_path):
            return public.returnMsg(False, 'ca文件不存在,可通过企业版插件[堡塔限制访问型证书->双向认证->服务器证书]获取')
        ca_content = public.readFile(ca_path)

        crl_path = "/www/server/panel/plugin/ssl_verify/client/crl.pem"
        if not os.path.exists(crl_path):
            return public.returnMsg(False, 'crl文件不存在,可通过企业版插件[堡塔限制访问型证书->双向认证->服务器证书]获取')
        crl_content = public.readFile(crl_path)

        if 'crl' in get and 'ca' in get:
            crl = 'ssl/crl.pem'
            ca = 'ssl/ca.pem'
            if get.crl:
                if get.crl.strip() != crl_content.strip():
                    return public.returnMsg(False, 'crl内容不匹配!')
                public.writeFile(crl, get.crl.strip())
            if get.ca:
                if get.ca.strip() != ca_content.strip():
                    return public.returnMsg(False, 'cert内容不匹配!')
                public.writeFile(ca, get.ca.strip())
            return public.returnMsg(True, '面板双向认证证书已保存!')
        else:
            msg = '开启'
            if not status: msg = '关闭'
            return public.returnMsg(True, '面板双向认证{}成功!'.format(msg))

    def get_ssl_verify(self, get):
        """
        获取双向认证
        """
        result = {'status': False, 'ca': '', 'crl': ''}
        sslConf = 'data/ssl_verify_data.pl'
        if os.path.exists(sslConf): result['status'] = True

        ca = 'ssl/ca.pem'
        crl = 'ssl/crl.pem'
        if os.path.exists(crl):
            result['crl'] = public.readFile(crl)
        if os.path.exists(crl):
            result['ca'] = public.readFile(ca)
        return result

    def set_not_auth_status(self, get):
        '''
            @name 设置未认证时的响应状态
            @author hwliang<2021-12-16>
            @param status_code<int> 状态码
            @return dict
        '''
        if not 'status_code' in get:
            return public.returnMsg(False, '参数错误!')

        if re.match("^\d+$", get.status_code):
            status_code = int(get.status_code)
            if status_code != 0:
                if status_code < 100 or status_code > 999:
                    return public.returnMsg(False, '状态码范围错误!')
        else:
            return public.returnMsg(False, '状态码范围错误!')

        public.save_config('abort', get.status_code)
        public.WriteLog('面板设置', '将未授权响应状态码设置为:{}'.format(get.status_code))
        return public.returnMsg(True, '设置成功!')

    def get_not_auth_status(self):
        '''
            @name 获取未认证时的响应状态
            @author hwliang<2021-12-16>
            @return int
        '''
        try:
            status_code = int(public.read_config('abort'))
            return status_code
        except:
            return 0

    def get_request_iptype(self, get=None):
        '''
            @name 获取云端请求线路
            @author hwliang<2022-02-09>
            @return auto/ipv4/ipv6
        '''

        v4_file = '{}/data/v4.pl'.format(public.get_panel_path())
        if not os.path.exists(v4_file): return 'auto'
        iptype = public.readFile(v4_file)
        if isinstance(iptype, str):
            iptype = iptype.strip()
        if not iptype: return 'auto'
        if iptype == '-4': return 'ipv4'
        return 'ipv6'

    def set_request_iptype(self, get):
        '''
            @name 设置云端请求线路
            @author hwliang<2022-02-09>
            @param iptype<str> auto/ipv4/ipv6
            @return dict
        '''
        v4_file = '{}/data/v4.pl'.format(public.get_panel_path())
        if not 'iptype' in get:
            return public.returnMsg(False, '参数错误!')
        if get.iptype == 'auto':
            public.writeFile(v4_file, ' ')
        elif get.iptype == 'ipv4':
            public.writeFile(v4_file, ' -4 ')
        else:
            public.writeFile(v4_file, ' -6 ')
        public.WriteLog('面板设置', '将云端请求线路设置为:{}'.format(get.iptype))
        return public.returnMsg(True, '设置成功!')

    def get_request_type(self, get=None):
        '''
            @name 获取云端请求方式
            @author hwliang<2022-02-09>
            @return python/curl/php
        '''
        http_type_file = '{}/data/http_type.pl'.format(public.get_panel_path())
        if not os.path.exists(http_type_file): return 'python'
        http_type = public.readFile(http_type_file).strip()
        if not http_type:
            os.remove(http_type_file)
            return 'python'
        return http_type

    def set_request_type(self, get):
        '''
            @name 设置云端请求方式
            @author hwliang<2022-02-09>
            @param http_type<str> python/curl/php
            @return dict
        '''
        http_type_file = '{}/data/http_type.pl'.format(public.get_panel_path())
        if not 'http_type' in get:
            return public.returnMsg(False, '参数错误!')
        if get.http_type == 'php':
            if not os.listdir('{}/php'.format(public.get_setup_path())): return public.returnMsg(False,
                                                                                                 '没有可用的PHP版本!')

        public.writeFile(http_type_file, get.http_type)
        public.WriteLog('面板设置', '将云端请求方式设置为:{}'.format(get.http_type))
        return public.returnMsg(True, '设置成功!')

    def get_node_config(self, get):
        '''
            @name 获取节点配置
            @author hwliang<2022-03-16>
            @return list
        '''
        import string
        node_list = [{"node_name": "自动选择", "node_id": 0, "node_ip": "", "status": 1}]
        node_file = '{}/config/api_node.json'.format(public.get_panel_path())
        hosts_file = '{}/config/hosts.json'.format(public.get_panel_path())
        if not os.path.exists(hosts_file): return node_list
        new_node_list = node_list
        node_list = json.loads(public.readFile(node_file))
        for old in node_list:
            if old["node_name"] == "自动选择": continue
            if old["status"] == 1:
                new_node_list[0]["status"] = 0
                new_node_list.append(old)
                break
        host_info = public.Get_ip_info()
        node_names = []
        for i in range(len(host_info)):
            node_name = host_info[i]["province"] + host_info[i]["city"] + host_info[i]["carrier"]
            if host_info[i]["city"] == "" or host_info[i][
                "carrier"] not in string.ascii_lowercase + string.ascii_uppercase:
                node_name = host_info[i]["country"] + host_info[i]["province"]
            if node_name not in node_names:
                node_names.append(node_name)
            else:
                node_name += "节点2"
            if "ipv6" in node_name: node_name = "ipv6地址(本机无ipv6请勿使用)"
            node = {
                "node_name": node_name,
                "node_id": i + 1,
                "node_ip": host_info[i]["ip"],
                "status": 0
            }
            if len(new_node_list) > 1:
                if not set(new_node_list[1]["node_name"]) ^ set(node["node_name"]): continue
            new_node_list.append(node)
        public.writeFile(node_file, json.dumps(new_node_list))
        for node in new_node_list:
            # node['speed'] = self.test_node(node['node_ip'])
            del (node['node_ip'])
        return new_node_list

    def test_node(self, node_ip):
        '''
            @name 测试节点
            @author hwliang<2022-03-16>
            @param node_ip<str> 节点IP
            @return int 节点延迟
        '''
        if not node_ip: node_ip = "api.bt.cn"
        s_time = time.time()
        import requests
        headers = {"Host": "api.bt.cn", "User-Agent": "BT-Panel"}
        try:
            res = requests.get('https://{}'.format(node_ip), headers=headers, timeout=1, verify=False).text
        except:
            return 0
        e_time = time.time()
        if res != 'ok': return 0
        return int((e_time - s_time) * 1000)

    def set_node_config(self, get):
        '''
            @name 设置节点配置
            @author hwliang<2022-03-16>
            @param node_id<str> 节点ID
            @return dict
        '''
        node_file = '{}/config/api_node.json'.format(public.get_panel_path())
        if not 'node_id' in get:
            return public.returnMsg(False, '参数错误!')
        node_id = int(get.node_id)
        if not os.path.exists(node_file):
            return public.returnMsg(False, '节点配置文件不存在!')
        node_list = json.loads(public.readFile(node_file))
        node_name = '自动选择'
        for node in node_list:
            if node['node_id'] == node_id:
                node['status'] = 1
                node_name = node['node_name']
                continue
            node['status'] = 0
        public.writeFile(node_file, json.dumps(node_list))
        self.sync_node_config()
        public.WriteLog('面板设置', '将节点配置设置为:{}'.format(node_name))
        return public.returnMsg(True, '设置成功!')

    def sync_cloud_node_list(self):
        '''
            @name  同步云端的节点列表
            @author hwliang<2022-03-16>
            @return void
        '''
        node_file = '{}/config/api_node.json'.format(public.get_panel_path())
        if not os.path.exists(node_file):
            public.writeFile(node_file, '[]')

        node_list = json.loads(public.readFile(node_file))
        try:
            url = "{}/lib/other/api_node.json".format(public.get_url())
            res = public.httpGet(url)
            if not res: return
            cloud_list = json.loads(res)
        except:
            return
        for cloud_node in cloud_list:
            is_insert = True
            for node in node_list:
                if node['node_id'] == cloud_node['node_id']:
                    node['node_name'] = cloud_node['node_name']
                    node['node_ip'] = cloud_node['node_ip']
                    is_insert = False
                    break
            if is_insert: node_list.append(cloud_node)
        public.writeFile(node_file, json.dumps(node_list))
        # self.sync_node_config()

    def sync_node_config(self):
        '''
            @name 同步节点配置
            @author hwliang<2022-03-16>
            @return void
        '''

        node_file = '{}/config/api_node.json'.format(public.get_panel_path())
        if not os.path.exists(node_file): return
        node_list = json.loads(public.readFile(node_file))
        node_info = {}
        for node in node_list:
            if node['status'] == 1:
                node_info = node
                break
        if not node_info: return
        public.ExecShell("sed -i '/api.bt.cn/d' /etc/hosts")
        public.ExecShell("sed -i '/www.bt.cn/d' /etc/hosts")
        if not node_info['node_ip']: return
        public.ExecShell("echo '{} api.bt.cn' >> /etc/hosts".format(node_info['node_ip']))
        public.ExecShell("echo '{} www.bt.cn' >> /etc/hosts".format(node_info['node_ip']))

    def set_click_logs(self, get):
        '''
            @name 设置点击日志
            @
        '''
        path = '{}/logs/click'.format(public.get_panel_path())
        if not os.path.exists(path): os.makedirs(path)

        file = "{}/{}.json".format(path, public.format_date(format="%Y-%m-%d"))
        try:
            ndata = json.loads(get['ndata'])
        except:
            ndata = {}

        try:
            data = json.loads(public.readFile(file))
        except:
            data = {}

        for x in ndata:
            if not x in data: data[x] = 0
            data[x] += ndata[x]

        public.writeFile(file, json.dumps(data))
        return []

    def get_msg_configs(self, get):
        """
        获取消息通道配置列表
        """
        cpath = 'data/msg.json'
        example = 'config/examples/msg.example.json'
        if not os.path.exists(cpath) and os.path.exists(example):
            import shutil
            shutil.copy(example, cpath)
        try:
            # 配置文件异常处理
            json.loads(public.readFile(cpath))
        except:
            if os.path.exists(cpath): os.remove(cpath)
        data = {}
        if os.path.exists(cpath):
            msgs = json.loads(public.readFile(cpath))
            for x in msgs:
                x['data'] = {}
                x['setup'] = False
                x['info'] = False
                key = x['name']
                try:
                    obj = public.init_msg(x['name'])
                    if obj:
                        x['setup'] = True
                        x['data'] = obj.get_config(None)
                        x['info'] = obj.get_version_info(None)
                except:
                    pass
                data[key] = x

        web_hook = public.init_msg("web_hook")
        if web_hook is False:
            return data
        default = {
            "name": None,
            "title": None,
            "version": "1.0",
            "date": "2023-10-30",
            "help": "https://www.bt.cn/bbs/thread-121791-1-1.html",
            "ps": "宝塔自定义API信息通道，用于接收面板消息推送",
            "setup": True,
            "info": web_hook.get_version_info(),
            "data": None
        }

        web_hook_conf = web_hook.get_config()
        for item in web_hook_conf:
            if item["status"]:
                tmp = default.copy()
                tmp["name"] = item["name"]
                tmp["title"] = "API:" + item["name"]
                tmp["data"] = item
                data[item["name"]] = tmp

        return data

    def get_module_template(self, get):
        """
        获取模块模板
        """
        panelPath = public.get_panel_path()
        module_name = get.module_name
        sfile = '{}/class/msg/{}.html'.format(panelPath, module_name)
        if not os.path.exists(sfile):
            return public.returnMsg(False, '模板文件不存在.')

        if module_name in ["sms"]:

            obj = public.init_msg(module_name)
            if obj:
                args = public.dict_obj()
                args.reload = True
                data = obj.get_config(args)
                from flask import render_template_string
                shtml = public.readFile(sfile)
                return public.returnMsg(True, render_template_string(shtml, data=data))
        else:
            shtml = public.readFile(sfile)
            return public.returnMsg(True, shtml)

    def set_default_channel(self, get):
        """
        设置默认消息通道
        """
        default_channel_pl = "/www/server/panel/data/default_msg_channel.pl"

        new_channel = get.channel
        default = False
        if "default" in get:
            _default = get.default
            if not _default or _default in ["false"]:
                default = False
            else:
                default = True

        ori_default_channel = ""
        if os.path.exists(default_channel_pl):
            ori_default_channel = public.readFile(ori_default_channel)

        if default:
            # 设置为默认
            from panelMessage import panelMessage
            pm = panelMessage()
            obj = pm.init_msg_module(new_channel)
            if not obj: return public.returnMsg(False, '设置失败，【{}】未安装'.format(new_channel))

            public.writeFile(default_channel_pl, new_channel)
            if ori_default_channel:
                return public.returnMsg(True, '已成功将[{}]改为[{}]面板默认消息通道。'.format(ori_default_channel,
                                                                                             new_channel))
            else:
                return public.returnMsg(True, '已设置[{}]为默认消息通道。'.format(new_channel))
        else:
            # 取消默认设置
            if os.path.exists(default_channel_pl):
                os.remove(default_channel_pl)
            return public.returnMsg(True, "已取消[{}]作为面板默认消息通道。".format(new_channel))

    def set_msg_config(self, get):
        """
        设置消息通道配置
        """
        from panelMessage import panelMessage
        pm = panelMessage()
        module_name = get.name
        # 删除不使用的标记信息
        not_use_tip = self._get_msg_module_not_use_tip()
        if module_name in not_use_tip:
            not_use_tip.remove(module_name)
        self._set_msg_module_not_use_tip(not_use_tip)
        mod_path = '{}/class/msg/{}_msg.py'.format(public.get_panel_path(), get.name)
        if not os.path.exists(mod_path):
            self.install_msg_module(get)
        obj = pm.init_msg_module(get.name)
        if not obj: return public.returnMsg(False, '设置失败，【{}】未安装'.format(get.name))
        return obj.set_config(get)

    @staticmethod
    def _get_msg_module_not_use_tip() -> list:
        tip_file = '{}/data/msg_not_use.tip'.format(public.get_panel_path())
        not_use_tip = public.readFile(tip_file)
        if not not_use_tip:
            not_use_tip = []
        else:
            try:
                not_use_tip = json.loads(not_use_tip)
                if not isinstance(not_use_tip, list):
                    return []
            except json.JSONDecodeError:
                not_use_tip = []
        return not_use_tip

    @staticmethod
    def _set_msg_module_not_use_tip(tip):
        tip_file = '{}/data/msg_not_use.tip'.format(public.get_panel_path())
        public.writeFile(tip_file, json.dumps(tip))

    def install_msg_module(self, get):
        """
        安装/更新消息通道模块
        @name 需要安装的模块名称
        """
        module_name = ""
        try:
            module_name = get.name
            # 删除不使用的标记信息
            not_use_tip = self._get_msg_module_not_use_tip()
            if module_name in not_use_tip:
                not_use_tip.remove(module_name)
            self._set_msg_module_not_use_tip(not_use_tip)

            down_url = public.get_url()

            local_path = '{}/class/msg'.format(public.get_panel_path())
            if not os.path.exists(local_path): os.makedirs(local_path)

            import panelTask
            task_obj = panelTask.bt_task()

            sfile1 = '{}/{}_msg.py'.format(local_path, module_name)
            down_url1 = '{}/linux/panel/msg/{}_msg.py'.format(down_url, module_name)

            sfile2 = '{}/class/msg/{}.html'.format(public.get_panel_path(), module_name)
            down_url2 = '{}/linux/panel/msg/{}.html'.format(down_url, module_name)

            public.WriteLog('安装模块', '安装【{}】'.format(module_name))
            task_obj.create_task('下载文件', 1, down_url1, sfile1)
            task_obj.create_task('下载文件', 1, down_url2, sfile2)

            timeout = 0
            is_install = False
            while timeout < 5:
                try:
                    if os.path.exists(sfile1) and os.path.exists(sfile2):
                        msg_obj = public.init_msg(module_name)
                        if msg_obj and msg_obj.get_version_info:
                            is_install = True
                            break
                except:
                    pass
                time.sleep(0.1)
                is_install = True

            if not is_install:
                return public.returnMsg(False, '安装[{}]模块失败，请检查网络原因。'.format(module_name))

            public.set_module_logs('msg_push', 'install_module', 1)
            return public.returnMsg(True, '【{}】模块安装成功.'.format(module_name))
        except:
            pass
        return public.returnMsg(False, '【{}】模块安装失败.'.format(module_name))

    def uninstall_msg_module(self, get):
        """
        卸载消息通道模块
        @name 需要卸载的模块名称
        @is_del 是否需要删除配置文件
        """
        module_name = get.name
        obj = public.init_msg(module_name)
        if 'is_del' in get:
            try:
                obj.uninstall()
            except:
                pass

        sfile = '{}/class/msg/{}_msg.py'.format(public.get_panel_path(), module_name)
        if os.path.exists(sfile):
            # 增加不使用的标记信息
            not_use_tip = self._get_msg_module_not_use_tip()
            if module_name not in not_use_tip:
                not_use_tip.append(module_name)
            self._set_msg_module_not_use_tip(not_use_tip)
            # os.remove(sfile)

        default_channel_pl = "{}/data/default_msg_channel.pl".format(public.get_panel_path())
        default_channel = public.readFile(default_channel_pl)
        if default_channel and default_channel == module_name:
            os.remove(default_channel_pl)
        return public.returnMsg(True, '【{}】模块卸载成功'.format(module_name))

    def get_msg_fun(self, get):
        """
        @获取消息模块指定方法
        @auther: cjxin
        @date: 2022-08-16
        @param: get.module_name 消息模块名称(如：sms,weixin,dingding)
        @param: get.fun_name 消息模块方法名称(如：send_sms,push_msg)
        """
        module_name = get.module_name
        fun_name = get.fun_name

        m_objs = public.init_msg(module_name)
        if not m_objs: return public.returnMsg(False, '设置失败，【{}】未安装'.format(module_name))

        return getattr(m_objs, fun_name)(get)

    def get_msg_configs_by(self, get):
        """
        @name 获取单独消息通道配置
        @auther: cjxin
        @date: 2022-08-16
        @param: get.name 消息模块名称(如：sms,weixin,dingding)
        """
        name = get.name
        res = {}
        res['data'] = {}
        res['setup'] = False
        res['info'] = False
        try:
            obj = public.init_msg(name)
            if obj:
                res['setup'] = True
                res['data'] = obj.get_config(None)
                res['info'] = obj.get_version_info(None);
        except:
            pass
        return res

    def get_msg_push_list(self, get):
        """
        @name 获取消息通道配置列表
        @auther: cjxin
        @date: 2022-08-16
        @
        """
        cpath = 'data/msg.json'
        try:
            if 'force' in get or not os.path.exists(cpath):
                if not 'download_url' in session: session['download_url'] = public.get_url()
                public.downloadFile('{}/linux/panel/msg/msg.json'.format(session['download_url']), cpath)
        except:
            pass

        data = {}
        if os.path.exists(cpath):
            msgs = json.loads(public.readFile(cpath))
            for x in msgs:
                x['setup'] = False
                x['info'] = False
                key = x['name']
                try:
                    obj = public.init_msg(x['name'])
                    if obj:
                        x['setup'] = True
                        x['info'] = obj.get_version_info(None)
                except:
                    print(public.get_error_info())
                    pass
                data[key] = x
        return data

    def set_improvement(self, get):
        '''
            @name 设置用户体验改进计划开关
            @author hwliang
            @return dict
        '''

        tip_file = '{}/data/improvement.pl'.format(public.get_panel_path())
        if not 'status' in get: return public.returnMsg(False, '必需要有status参数!')

        status = 1 if int(get.status) else 0
        if status:
            public.WriteFile(tip_file, '1')
        else:
            if os.path.exists(tip_file):
                os.remove(tip_file)
        tip_file_set = '{}/data/is_set_improvement.pl'.format(public.get_panel_path())
        public.WriteFile(tip_file_set, '')
        status_msg = ['关闭', '开启']
        msg = '已[{}]用户体验改进计划'.format(status_msg[status])

        public.WriteLog('面板设置', msg)
        return public.returnMsg(True, msg)

    def stop_nps(self, get):
        if 'software_name' not in get:
            public.returnMsg(False, '参数错误')
        if get.software_name == "panel":
            self._stop_panel_nps()
        else:
            public.WriteFile("data/%s_nps.pl" % get.software_name, "")
        return public.returnMsg(True, '关闭成功')

    def get_nps(self, get):
        if not hasattr(get, 'software_name'):
            return public.ReturnMsg(False, '参数错误')
        software_name = get.software_name
        if software_name == "panel":
            return self._get_panel_nps()
        data = {'safe_day': 0}
        # conf = self.get_config(None)
        # 判断运行天数
        if os.path.exists("data/%s_nps_time.pl" % software_name):
            try:
                nps_time = float(public.ReadFile("data/%s_nps_time.pl" % software_name))
                data['safe_day'] = int((time.time() - nps_time) / 86400)

            except:
                public.WriteFile("data/%s_nps_time.pl" % software_name, "%s" % time.time())
        else:
            public.WriteFile("data/%s_nps_time.pl" % software_name, "%s" % time.time())

        if not os.path.exists("data/%s_nps.pl" % software_name):
            # 如果安全运行天数大于5天 并且没有没有填写过nps的信息
            data['nps'] = False
        else:
            data['nps'] = True
        return data

    def update_nps(self, get):
        url = "https://nps.bt.cn/api/index.php"
        data = {
            'action': "list",
            'product_type': get.get('product_type', 0),
            'version': get.get('version', -1)}
        res = requests.post(url, data=data)
        if res.status_code == 200:
            data1 = res.json()['data']
            public.writeFile('/www/server/panel/data/nps_{}.json'.format(get.get('product_type', 0)), json.dumps(data1))
            return data1
        return False

    def get_nps_new(self, get):
        """
        获取问卷
        """
        try:
            product_type = get.get('product_type', 0)
            nps_path = '/www/server/panel/data/nps_{}.json'.format(product_type)
            # request发送post请求并指定form_data参数
            if not os.path.exists(nps_path):
                data = self.update_nps(get)
                if not data:
                    return public.returnMsg(False, "获取问卷失败")
            else:
                data = json.loads(public.readFile(nps_path))
                public.run_thread(self.update_nps, (get,))
            return public.returnMsg(True, data)
        except:
            return public.returnMsg(False, "获取问卷失败")

    # 获取NPS标签列表
    def get_nps_info(self, get):
        try:
            api_url = 'https://nps.bt.cn/api/index.php'
            data = {
                'action': 'tags',
                'product_type': get.get('product_type/d', 0)
            }
            res = requests.post(api_url, data=data, timeout=10)
            if res.status_code == 200:
                return public.returnMsg(True, res.json()['data'])
            else:
                return public.returnMsg(False, "获取失败")
        except:
            return public.returnMsg(True, "获取失败")


    def write_nps_new(self, get):
        '''
            @name nps 提交
            @param rate 评分
            @param feedback 反馈内容
        '''
        try:
            if not hasattr(get, 'software_name'): public.returnMsg(False, '参数错误')
            software_name = get['software_name']
            public.WriteFile("data/{}_nps.pl".format(software_name), "1")
            user_info = json.loads(public.ReadFile("{}/data/userInfo.json".format(public.get_panel_path())))
            api_url = 'https://nps.bt.cn/api/index.php'
            if not hasattr(get, 'questions'):
                return public.returnMsg(False, "参数错误")
            else:
                try:
                    content = json.loads(get.questions)
                    for _, i in content.items():
                        if len(i) > 512:
                            public.ExecShell("rm -f data/{}_nps.pl".format(software_name))
                            return public.returnMsg(False, "提交的文本太长，请调整后重新提交（MAX：512）")
                except:
                    return public.returnMsg(False, "参数错误")
            if not hasattr(get, 'product_type'):
                return public.returnMsg(False, "参数错误")
            if not hasattr(get, 'rate'):
                return public.returnMsg(False, "参数错误")
            if not hasattr(get, 'reason_tags'):
                get['reason_tags'] = "1"
            if not hasattr(get, 'is_paid'):
                get['is_paid'] = 0  # 是否付费
            if not hasattr(get, 'phone_back'):
                get.phone_back = 0
            if not hasattr(get, 'feedback'):
                get.feedback = ""
            data = {
                'action': "submit",
                'uid': user_info['uid'],  # 用户ID
                'access_key': user_info['access_key'],  # 用户密钥
                'product_type': get['product_type'],  # 产品类型
                'phone_back': get['back_phone'],  # 是否回访
                'panel_version': public.version(),  # 面板版本
                'reason_tags': get['reason_tags'],  # 问题标签
                'rate': get['rate'],  # 评分
                'serverid': user_info['serverid'],  # 服务器ID
                'questions': get['questions'],  # 问题列表
                'is_paid': get['is_paid'],  # 是否付费
                'feedback': get['feedback'],  # 反馈内容
            }
            try:
                res = requests.post(api_url, data=data, timeout=10)
                if software_name == "panel":
                    self._stop_panel_nps(is_complete=True)
                if res.status_code == 200:
                    return public.returnMsg(True, "提交成功")
                else:
                    return public.returnMsg(True, "提交成功")
            except:
                return public.returnMsg(True, "提交成功")
        except:
            return public.returnMsg(True, "提交成功")

    def write_nps(self, get):
        '''
            @name nps 提交
            @param rate 评分
            @param feedback 反馈内容

        '''
        if 'product_type' not in get: public.returnMsg(False, '参数错误')
        if 'software_name' not in get: public.returnMsg(False, '参数错误')
        software_name = get.software_name
        product_type = get.product_type
        import json, requests
        api_url = 'https://www.bt.cn/api/v2/contact/nps/submit'
        user_info = json.loads(public.ReadFile("{}/data/userInfo.json".format(public.get_panel_path())))
        if 'rate' not in get:
            return public.returnMsg(False, "参数错误")
        if 'feedback' not in get:
            get.feedback = ""
        if 'phone_back' not in get:
            get.phone_back = 0
        else:
            if get.phone_back == 1:
                get.phone_back = 1
            else:
                get.phone_back = 0

        if 'questions' not in get:
            return public.returnMsg(False, "参数错误")

        try:
            get.questions = json.loads(get.questions)
        except:
            return public.returnMsg(False, "参数错误")

        data = {
            "uid": user_info['uid'],
            "access_key": user_info['access_key'],
            "serverid": user_info['serverid'],
            "product_type": product_type,
            "rate": get.rate,
            "feedback": get.feedback,
            "phone_back": get.phone_back,
            "questions": json.dumps(get.questions)
        }
        try:
            requests.post(api_url, data=data, timeout=10).json()
            if software_name == "panel":
                self._stop_panel_nps(is_complete=True)
            else:
                public.WriteFile("data/{}_nps.pl".format(software_name), "1")
        except:
            pass
        return public.returnMsg(True, "提交成功")

    def set_table_header(self, get):
        """设置表头"""
        # allow_headers = ("PHP_Site", "File_Header","MysqlTableColumn","FtpTableColumn")
        table_name = getattr(get, "table_name", None)
        table_data = getattr(get, "table_data", None)
        if not (table_data and table_name):
            return public.returnMsg(False, "参数错误")
        # if table_name not in allow_headers:
        #     return public.returnMsg(False, "参数错误")

        header_file = "{}/data/table_header_conf.json".format(public.get_panel_path())

        header_data = self.get_table_header(None)

        header_data[table_name] = table_data
        public.writeFile(header_file, json.dumps(header_data))

        return public.returnMsg(True, "修改成功")

    def get_table_header(self, get):
        """获取表头"""
        table_name = "PHP_Site"
        if hasattr(get, "table_name"):
            table_name = get.table_name
        header_file = "{}/data/table_header_conf.json".format(public.get_panel_path())
        if not os.path.exists(header_file):
            header_data = {table_name: ''}
        else:
            try:
                header_data = json.loads(public.readFile(header_file))
                if not isinstance(header_data, dict):
                    header_data = {}
                header_data = {table_name: header_data.get(table_name, '')}
            except:
                header_data = {table_name: ''}

        if header_data.get("PHP_Site", None):
            try:
                s_table = json.loads(header_data["PHP_Site"])
                for d in s_table:
                    if d["title"] == "流量":
                        if public.GetWebServer() == "openlitespeed":
                            d["disabled"] = True
                            d["value"] = False
                        else:
                            d["disabled"] = False
                header_data["PHP_Site"] = json.dumps(s_table)
            except:
                pass

        return header_data

    @staticmethod
    def _get_panel_nps_data():
        panel_path = public.get_panel_path()
        try:
            nps_file = "{}/data/btpanel_nps_data".format(panel_path)
            if os.path.exists(nps_file):
                with open(nps_file, mode="r") as fp:
                    nps_data = json.load(fp)
            else:
                time_file = "{}/data/panel_nps_time.pl".format(panel_path)
                post_nps_done = "{}/data/panel_nps.pl".format(panel_path)
                if not os.path.exists(time_file):
                    install_time = time.time()
                else:
                    with open(time_file, mode="r") as fp:
                        install_time = float(fp.read())
                nps_data = {
                    "time": install_time,
                    "status": "complete" if os.path.exists(post_nps_done) else "waiting",
                    "popup_count": 0
                }

                with open(nps_file, mode="w") as fp:
                    fp.write(json.dumps(nps_data))
        except:
            nps_data = {
                "time": time.time(),
                "status": "waiting",
                "popup_count": 0
            }

        return nps_data

    @staticmethod
    def _save_panel_nps_data(nps_data):
        panel_path = public.get_panel_path()
        nps_file = "{}/data/btpanel_nps_data".format(panel_path)
        with open(nps_file, mode="w") as fp:
            fp.write(json.dumps(nps_data))

    def _get_panel_nps(self):
        nps_data = self._get_panel_nps_data()
        safe_day = int((time.time() - nps_data["time"]) / 86400)
        res = {'safe_day': safe_day}
        if nps_data["status"] == "complete":
            res["nps"] = False
        elif nps_data["status"] == "stopped":
            res["nps"] = False
        else:
            if safe_day >= 10:
                res["nps"] = True
        return res

    def _stop_panel_nps(self, is_complete: bool = False):
        nps_data = self._get_panel_nps_data()
        if is_complete:
            nps_data["status"] = "complete"
        else:
            nps_data["status"] = "stopped"

        self._save_panel_nps_data(nps_data)

    @staticmethod
    def set_limit_area(get):
        '''
        设置地区限制访问
        @param get:
        @return:
        '''
        try:
            have_maxminddb, _ = public.ExecShell("btpip freeze | grep maxminddb")
            if not have_maxminddb:
                public.ExecShell("btpip install -U pip")
                _, err = public.ExecShell("btpip install maxminddb")
                if err: return public.returnMsg(False, '设置失败，未安装maxminddb模块！请手动安装：btpip install maxminddb')

            empty_content = {
                "limit_area": {
                    "city": [],
                    "province": [],
                    "country": []
                },
                "limit_area_status": "false",
                "limit_type": "deny"
            }

            try:
                limit_area_json = json.loads(public.readFile('data/limit_area.json'))
            except json.decoder.JSONDecodeError:
                limit_area_json = empty_content
            except TypeError:
                limit_area_json = empty_content
            except Exception as e:
                limit_area_json = empty_content

            get_limit_area = json.loads(get.limit_area) if "limit_area" in get else limit_area_json["limit_area"]
            limit_area_status = get.limit_area_status if "limit_area_status" in get else limit_area_json["limit_area_status"]
            limit_type = get.limit_type if "limit_type" in get else limit_area_json["limit_type"]

            file_content = {
                "limit_area": get_limit_area,
                "limit_area_status": limit_area_status,
                "limit_type": limit_type
            }

            public.writeFile('data/limit_area.json', json.dumps(file_content))

            limit_area_file = "data/limit_area.pl"
            if limit_area_status == "true":
                if not os.path.isfile(limit_area_file):
                    public.writeFile(limit_area_file, 'True')
            else:
                if os.path.isfile(limit_area_file):
                    os.remove(limit_area_file)

            return public.returnMsg(True, '设置成功!')
        except:
            import traceback
            print(traceback.format_exc())
            # public.print_log(traceback.format_exc())
            return public.returnMsg(False, '设置失败！')

    @staticmethod
    def get_limit_area(get):
        '''
        获取地区限制访问信息
        @param get:
        @return:
        '''
        return public.get_limit_area()

    @staticmethod
    def set_popularize(get=None):
        """推荐功能收集计数
        @author baozi <202-04-18>
        @param:
        @return
        """
        public.set_module_logs("config", "set_popularize", 1)
        return public.returnMsg(True, "记录成功")

    def set_recommend_show(self, get):
        if not hasattr(get, 'show'):
            return public.returnMsg(False, '参数错误')
        show = get.show
        if int(show):
            if os.path.exists('/www/server/panel/data/recommend_show.pl'):
                os.remove('/www/server/panel/data/recommend_show.pl')
        else:
            public.writeFile('/www/server/panel/data/recommend_show.pl')

    # 设置左侧菜单标题
    def set_left_title(self, get):
        '''
        设置左侧菜单标题
        :param get
        :return
        '''
        if get.get('title', None) is None: return public.returnMsg(False, '参数错误!')

        public.writeFile('data/title.pl', get.title.strip())
        return public.returnMsg(True, '设置成功!')

    # 设置全局开关
    def set_status_info(self, get):
        '''
            设置全局开关
            :param get
            :return
        '''
        try:
            file_path = os.path.join(public.get_panel_path(), "data/global_status.json")
            if not os.path.exists(file_path):
                public.writeFile(file_path, json.dumps({}))
            if get.get('name', None) is None: return public.returnMsg(False, '参数错误!')
            if get.get('status', 0) is None: return public.returnMsg(False, '参数错误!')

            filedata = json.loads(public.readFile(file_path))

            filedata.update({get.name: int(get.status)})

            public.writeFile(file_path, json.dumps(filedata))
            return public.returnMsg(True, '设置成功!')
        except Exception as e:
            return public.returnMsg(False, '设置失败!')

    # 获取全局开关
    def get_status_info(self, get):
        '''
            获取全局开关
            :param get
            :return
        '''

        file_path = os.path.join(public.get_panel_path(), "data/global_status.json")
        if not os.path.exists(file_path):
            return public.returnMsg(True, {})

        result = public.readFile(file_path)
        if not result:
            return public.returnMsg(True, {})

        return public.returnMsg(True, json.loads(result))

    # 获取备忘录内容
    def get_memo_body(self, get):
        memo_path = "/www/server/panel/data/memo.txt"
        if not os.path.exists(memo_path):
            public.writeFile(memo_path, "")

        content = public.readFile(memo_path)
        return content

    def set_ua(self, get):
        try:
            ua_file = '/www/server/panel/class/limitua.json'
            if os.path.exists(ua_file):
                with open(ua_file, 'r') as f:
                    data = json.load(f)
                # 检查 ua_list 是否为空，如果为空则设置 id 为 1，否则计算最大 id 并加 1
                if data['ua_list']:
                    id = max(ua['id'] for ua in data['ua_list']) + 1
                else:
                    id = 1
            else:
                id = 1  # 如果文件不存在，从1开始
                data = {
                    "ua_list": [],
                    "status": "0"
                }


            current_ua = {"id": id, "name": request.user_agent.string}  # 当前登录用户的UA
            if not data['ua_list'] or data['ua_list'][0]['name'] != current_ua['name']:  # 如果列表为空或者当前UA与列表中的第一个UA不同，则替换
                data['ua_list'].insert(0, current_ua)  # 将当前UA插入到列表的第一个位置

            ua_list = [{"id": id + i + 1, "name": self.process_ua(ua)} for i, ua in enumerate(get.ua_list.split('\n')) if ua.strip()]  # 将字符串转换为列表并添加到ua_list，忽略空的UA
            added_uas = []  # 保存已经添加成功的UA
            for ua in ua_list:
                if ua['name'] not in [ua['name'] for ua in data['ua_list']]:  # 如果UA尚未存在于列表中，则添加
                    data['ua_list'].append(ua)
                    added_uas.append(ua['name'])

            public.writeFile('/www/server/panel/class/limitua.json', json.dumps(data))  # 将数据保存为JSON文件
            return public.returnMsg(True, "设置成功！")
        except Exception as e:
            return public.returnMsg(False, "设置失败！" + str(e))

    def process_ua(self, ua):
        # 将括号内的逗号替换为其他字符
        return re.sub(r'(\(.*?\))', lambda x: x.group(1).replace(',', ';'), ua)

    def get_limit_ua(self, get):
        try:
            ua_file = '/www/server/panel/class/limitua.json'
            if not os.path.exists(ua_file): return []
            with open(ua_file, 'r') as f:
                data = json.load(f)  # 读取JSON文件
            ua_list = data.get('ua_list', [])  # 获取ua_list字段的值
            if ua_list:
                ua_list.pop(0)  # 删除第一行的数据
            status = data.get('status', '0')  # 获取status字段的值
            return public.returnMsg(True, {"ua_list": ua_list, "status": status})
        except Exception as e:
            return public.returnMsg(False, str(e))

    # 修改UA数据
    def modify_ua(self, get):
        try:
            ua_file = '/www/server/panel/class/limitua.json'
            if not os.path.exists(ua_file):
                # 文件不存在，创建文件并初始化基本结构
                data = {'ua_list': [], 'status': False}
                with open(ua_file, 'w') as f:
                    json.dump(data, f)
            else:

                with open(ua_file, 'r') as f:
                    data = json.load(f)
            # 如果get中包含id和new_name，那么修改对应的UA
            if 'id' in get and 'new_name' in get:

                for ua in data['ua_list']:
                    if ua['id'] == int(get.id):
                        ua['name'] = get.new_name
            # 如果get中包含status，那么修改status的值
            if 'status' in get:
                data['status'] = get.status
                if len(data['ua_list'])==1 and data['status']=="1":
                    return public.returnMsg(False, "请先添加ua后再开启！")
            with open(ua_file, 'w') as f:
                json.dump(data, f)
            return public.returnMsg(True, "修改成功！")
        except Exception as e:
            return public.returnMsg(False, "修改失败！" + str(e))

    # 删除UA数据
    def delete_ua(self, get):
        try:
            ua_file = '/www/server/panel/class/limitua.json'
            if not os.path.exists(ua_file):
                # 文件不存在，创建文件并初始化基本结构
                data = {'ua_list': [], 'status': False}
                with open(ua_file, 'w') as f:
                    json.dump(data, f)
            else:
                with open(ua_file, 'r') as f:
                    data = json.load(f)
                data['ua_list'] = [ua for ua in data['ua_list'] if ua['id'] != int(get.id)]
                with open(ua_file, 'w') as f:
                    json.dump(data, f)
                return public.returnMsg(True, "删除成功！")
        except Exception as e:
            return public.returnMsg(False, "删除失败！" + str(e))

    @staticmethod
    def show_time_by_seconds(seconds: int) -> str:
        if seconds // (60 * 60 * 24) >= 4:  # 4天及以上的，使用天+小时展示
            minutes, seconds = divmod(seconds, 60)
            hours, minutes = divmod(minutes, 60)
            days, hours = divmod(hours, 24)
            if hours == 0:
                return "%d天" % days
            if minutes == 0:
                return "%d天%d小时" % (days, hours)
            hours = hours + minutes / 60
            return "%d天%.1f小时" % (days, hours)

        elif seconds // (60 * 60) >= 1:  # 3天以内1小时以上，用小时+分钟表示
            minutes, seconds = divmod(seconds, 60)
            hours, minutes = divmod(minutes, 60)
            if minutes == 0:
                return "%d小时" % hours
            return "%d小时%d分钟" % (hours, minutes)
        else:  # 1小时以内，用分钟表示
            minutes, seconds = divmod(seconds, 60)
            return "%d分钟" % minutes

    # 面板 通过余额购买商业证书
    def balance_pay_cert(self,get):
        try:
            user_info = json.loads(public.ReadFile("{}/data/userInfo.json".format(public.get_panel_path())))
            url = "https://nps.bt.cn/api/v2/order/product/create_cert_with_credit"
            data = {
                "pid": get.get('pid/d', 0),  # 商业证书ID
                "uid": user_info['uid'],   # 用户id
                'access_key': user_info['access_key'],  # 用户密钥
                "install": get.get('install/d', 0),  # 是否购买人工部署服务
                "years": get.get('years/d', 1),  # 购买年限
                "num": get.get('num/d', 1),  # 购买数量
            }

            # request发送post请求并指定form_data参数
            res = requests.post(url, data=data)
            if res.status_code == 200:
                return public.returnMsg(True, '购买成功')
            return public.returnMsg(False, "购买失败")
        except:
            return public.returnMsg(False, "购买失败")

    def err_collection(self, get):
        # 提交错误登录信息
        _form = get.get("form_data", {})
        if 'username' in _form: _form['username'] = '******'
        if 'password' in _form: _form['password'] = '******'
        if 'phone' in _form: _form['phone'] = '******'

        error = get.get("errinfo", "")
        # 获取面板地址
        panel_addr = public.get_server_ip() + ":" + str(public.get_panel_port())
        if panel_addr in error:
            error = error.replace(panel_addr, "127.0.0.1:10086")
        try:
            error = re.sub(r'https?:\/\/(.*?:.*?)\/', 'http://127.0.0.1:10086/', error)
        except:pass
        # 错误信息
        error_infos = {
            "REQUEST_DATE": public.getDate(),  # 请求时间
            "PANEL_VERSION": public.version(),  # 面板版本
            "OS_VERSION": public.get_os_version(),  # 操作系统版本
            "REMOTE_ADDR": public.GetClientIp(),  # 请求IP
            "REQUEST_URI": get.get("uri", ""),  # 请求URI
            "REQUEST_FORM": public.xsssec(str(_form)),  # 请求表单
            "USER_AGENT": public.xsssec(request.headers.get('User-Agent')),  # 客户端连接信息
            "ERROR_INFO": error,  # 错误信息
            "PACK_TIME": public.readFile("/www/server/panel/config/update_time.pl") if os.path.exists("/www/server/panel/config/update_time.pl") else public.getDate(),  # 打包时间
            "TYPE": 1,
            "ERROR_ID": "{}_{}".format(error.split("\n")[0].strip(),get.get("uri", ""))
        }

        pkey = public.Md5(error_infos["ERROR_ID"])

        # 提交
        if not public.cache_get(pkey):
            try:
                public.run_thread(public.httpPost, ("https://api.bt.cn/bt_error/index.php", error_infos))
                public.cache_set(pkey, 1, 1800)
            except Exception as e:
                pass

        return public.returnMsg(True, "OK")
    # 设置面板界面配置
    def set_panel_theme(self, get):
        try:
            return self.themeManager.save_config(get.data)
        except Exception as e:
            return public.returnMsg(False, f'设置面板界面配置失败: {str(e)}')

    # 获取面板界面配置  
    def get_panel_theme(self, get=None):
        try:
            return self.themeManager.get_config()
        except Exception as e:
            return public.returnMsg(False, f'获取面板界面配置失败: {str(e)}')

    # 更新面板界面配置
    def update_panel_theme(self, get):
        try:
            return self.themeManager.update_config(get)
        except Exception as e:
            return public.returnMsg(False, f'更新面板界面配置失败: {str(e)}')
    
    # 验证主题文件
    def validate_theme_file(self, get):
        try:
            if not hasattr(get, 'file_path'):
                return public.returnMsg(False, '缺少file_path参数')
            return self.themeManager.validate_theme_file(get.file_path)
        except Exception as e:
            return public.returnMsg(False, f'验证主题文件失败: {str(e)}')
    
    # 导入主题配置
    def import_theme_config(self, get):
        try:
            if not hasattr(get, 'file_path'):
                return public.returnMsg(False, '缺少file_path参数')
            backup_existing = getattr(get, 'backup_existing', True)
            if isinstance(backup_existing, str):
                backup_existing = backup_existing.lower() in ['true', '1', 'yes']
            return self.themeManager.import_theme_config(get.file_path, backup_existing)
        except Exception as e:
            return public.returnMsg(False, f'导入主题配置失败: {str(e)}')
    
    # 导出主题配置
    def export_theme_config(self, get):
        try:
            export_path = getattr(get, 'export_path', None)
            return self.themeManager.export_theme_config(export_path)
        except Exception as e:
            return public.returnMsg(False, f'导出主题配置失败: {str(e)}')
    
    # 获取导出文件信息
    def get_export_file_info(self, get):
        try:
            if not hasattr(get, 'file_path'):
                return public.returnMsg(False, '缺少file_path参数')
            return self.themeManager.get_export_file_info(get.file_path)
        except Exception as e:
            return public.returnMsg(False, f'获取导出文件信息失败: {str(e)}')

    # 设置登录归属地来源
    def set_login_origin(self, get):
        login_origin_path = 'data/login_origin.pl'
        if not 'status' in get: return public.returnMsg(False, '必需要有status参数!')
        status = 1 if int(get.status) else 0
        if status:
            t_str = '开启'
            public.writeFile(login_origin_path, 'True')
        else:
            t_str = '关闭'
            public.writeFile(login_origin_path, 'False')
        public.WriteLog('面板配置', '%s登录IP归属地通知' % t_str)
        return public.returnMsg(True, '设置成功!')
        
    # 获取登录归属地来源
    def get_login_origin(self):
      """获取登录归属地来源，若文件不存在则创建并初始化为True"""
      login_origin_path = 'data/login_origin.pl'
      try:
          # 检查文件是否存在，不存在则创建并写入默认值
          if not os.path.exists(login_origin_path):
              public.writeFile(login_origin_path, 'True')
              return True
          # 文件存在则读取并解析内容
          content = public.readFile(login_origin_path)
          return content.strip() == 'True'
          
      except Exception as e:
          # 记录错误日志并返回默认值
          return False
      
    # 设置安全风险忽略
    def SetNoticeIgnore(self, get):
        notice_risk_ignore_path = 'data/notice_risk_ignore.json'
        data = {}
        name = get.name
        if not 'name' in get: return public.returnMsg(False, '必需要有name参数!')
        try:
            if not os.path.exists(notice_risk_ignore_path):
                data = { 'https':False,  'port':False}
                data[name] = True
            else:
                data = json.loads(public.readFile(notice_risk_ignore_path))
                if name in data and data[name] == True:
                    data[name] = False
                else:
                    data[name] = True
            public.writeFile(notice_risk_ignore_path, json.dumps(data))
            return public.returnMsg(True, '设置成功!')
        except Exception as e:
            return public.returnMsg(False, '设置失败!')
        

    # 获取安全风险忽略
    def get_notice_risk_ignore(self):
        notice_risk_ignore_path = 'data/notice_risk_ignore.json'
        if not os.path.exists(notice_risk_ignore_path):
            return { 'https': False, 'port': False }
        return json.loads(public.readFile(notice_risk_ignore_path))


    @staticmethod
    def get_versionnumber(get):
        # 打时会替换 为版本时间戳
        return {"status": True, "msg": "ok", "code": 200, "data": {"version_number": int("1758787359")}}



if __name__ == '__main__':
    c = config()
    if sys.argv[1] == 'SetPanelSSL':
        get = public.to_dict_obj({})
        res = c.SetPanelSSL(get)
        if res['status']:
            print('关闭面板ssl成功')
        else:
            print('关闭失败，请查看面板ssl是否开启')
