#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http:#bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------

import public,os,sys,db,time,json
from BTPanel import session,cache,json_header
from flask import request,redirect,g

class userlogin:
    
    def request_post(self,post):
        if not hasattr(post, 'username') or not hasattr(post, 'password'):
            return public.returnJson(False,'LOGIN_USER_EMPTY'),json_header
        
        self.error_num(False)
        if self.limit_address('?') < 1: return public.returnJson(False,'LOGIN_ERR_LIMIT'),json_header
        
        post.username = post.username.strip();
        password = public.md5(post.password.strip());
        sql = db.Sql();
        userInfo = sql.table('users').where("id=?",(1,)).field('id,username,password').find()
        m_code = cache.get('codeStr')
        if 'code' in session:
            if session['code'] and not 'is_verify_password' in session:
                if not hasattr(post, 'code'): return public.returnJson(False,'验证码不能为空!'),json_header
                if not public.checkCode(post.code):
                    public.WriteLog('TYPE_LOGIN','LOGIN_ERR_CODE',('****','****',public.GetClientIp()));
                    return public.returnJson(False,'CODE_ERR'),json_header
        try:
            s_pass = public.md5(public.md5(userInfo['password'] + '_bt.cn'))
            if userInfo['username'] != post.username or s_pass != password:
                public.WriteLog('TYPE_LOGIN','LOGIN_ERR_PASS',('****','******',public.GetClientIp()));
                num = self.limit_address('+');
                return public.returnJson(False,'LOGIN_USER_ERR',(str(num),)),json_header
            _key_file = "/www/server/panel/data/two_step_auth.txt"
            if hasattr(post,'vcode'):
                if self.limit_address('?',v="vcode") < 1: return public.returnJson(False,'您多次验证失败，禁止10分钟'),json_header
                import pyotp
                secret_key = public.readFile(_key_file)
                if not secret_key:
                    return public.returnJson(False, "没有找到key,请尝试在命令行关闭谷歌验证后在开启"),json_header
                t = pyotp.TOTP(secret_key)
                result = t.verify(post.vcode)
                if not result:
                    if public.sync_date(): result = t.verify(post.vcode)
                    if not result:
                        num = self.limit_address('++',v="vcode")
                        return public.returnJson(False, '验证失败，您还可以尝试[{}]次!'.format(num)), json_header
                now = int(time.time())
                public.writeFile("/www/server/panel/data/dont_vcode_ip.txt",json.dumps({"client_ip":public.GetClientIp(),"add_time":now}))
                self.limit_address('--',v="vcode")
                return self._set_login_session(userInfo)

            acc_client_ip = self.check_two_step_auth()

            if not os.path.exists(_key_file) or acc_client_ip:
                return self._set_login_session(userInfo)
            self.limit_address('-')
            session['is_verify_password'] = True
            return "1"
        except Exception as ex:
            stringEx = str(ex)
            if stringEx.find('unsupported') != -1 or stringEx.find('-1') != -1: 
                os.system("rm -f /tmp/sess_*")
                os.system("rm -f /www/wwwlogs/*log")
                public.ServiceReload()
                return public.returnJson(False,'USER_INODE_ERR'),json_header
            public.WriteLog('TYPE_LOGIN','LOGIN_ERR_PASS',('****','******',public.GetClientIp()));
            num = self.limit_address('+');
            return public.returnJson(False,'LOGIN_USER_ERR',(str(num),)),json_header

    def request_tmp(self,get):
        try:
            if not hasattr(get,'tmp_token'): return public.returnJson(False,'错误的参数!'),json_header
            save_path = '/www/server/panel/config/api.json'
            data = json.loads(public.ReadFile(save_path))
            if not 'tmp_token' in data or not 'tmp_time' in data: return public.returnJson(False,'验证失败!'),json_header
            if (time.time() - data['tmp_time']) > 120: return public.returnJson(False,'过期的Token'),json_header
            if get.tmp_token != data['tmp_token']: return public.returnJson(False,'错误的Token'),json_header
            userInfo = public.M('users').where("id=?",(1,)).field('id,username').find()
            session['login'] = True;
            session['username'] = userInfo['username'];
            session['tmp_login'] = True
            public.WriteLog('TYPE_LOGIN','LOGIN_SUCCESS',(userInfo['username'],public.GetClientIp()));
            self.limit_address('-');
            cache.delete('panelNum')
            cache.delete('dologin')
            sess_input_path = 'data/session_last.pl'
            public.writeFile(sess_input_path,str(int(time.time())))
            del(data['tmp_token'])
            del(data['tmp_time'])
            public.writeFile(save_path,json.dumps(data))
            self.set_request_token()
            self.login_token()
            return redirect('/')
        except:
            return public.returnJson(False,'登录失败,' + public.get_error_info()),json_header


    def login_token(self):
        import config
        config.config().reload_session()

    def request_get(self,get):
        #if os.path.exists('/www/server/panel/install.pl'): raise redirect('/install');
        if not 'title' in session: session['title'] = public.getMsg('NAME');
        domain = public.readFile('data/domain.conf')
        
        if domain:
            if(public.GetHost().lower() != domain.strip().lower()): 
                errorStr = public.ReadFile('./BTPanel/templates/' + public.GetConfigValue('template') + '/error2.html')
                try:
                    errorStr = errorStr.format(public.getMsg('PAGE_ERR_TITLE'),public.getMsg('PAGE_ERR_DOMAIN_H1'),public.getMsg('PAGE_ERR_DOMAIN_P1'),public.getMsg('PAGE_ERR_DOMAIN_P2'),public.getMsg('PAGE_ERR_DOMAIN_P3'),public.getMsg('NAME'),public.getMsg('PAGE_ERR_HELP'))
                except IndexError:pass
                return errorStr
        if os.path.exists('data/limitip.conf'):
            iplist = public.readFile('data/limitip.conf')
            if iplist:
                iplist = iplist.strip();
                if not public.GetClientIp() in iplist.split(','):
                    errorStr = public.ReadFile('./BTPanel/templates/' + public.GetConfigValue('template') + '/error2.html')
                    try:
                        errorStr = errorStr.format(public.getMsg('PAGE_ERR_TITLE'),public.getMsg('PAGE_ERR_IP_H1'),public.getMsg('PAGE_ERR_IP_P1',(public.GetClientIp(),)),public.getMsg('PAGE_ERR_IP_P2'),public.getMsg('PAGE_ERR_IP_P3'),public.getMsg('NAME'),public.getMsg('PAGE_ERR_HELP'))
                    except IndexError:pass
                    return errorStr
        
        sql = db.Sql()
        
        if 'login' in session:
            if session['login'] == True:
                return redirect('/')
        
        if not 'code' in session:
            session['code'] = False
        self.error_num(False)

    #生成request_token
    def set_request_token(self):
        session['request_token_head'] = public.GetRandomString(48)

    #防暴破
    def error_num(self,s = True):
        nKey = 'panelNum'
        num = cache.get(nKey)
        if not num:
            cache.set(nKey,1)
            num = 1
        if s: cache.inc(nKey,1)
        if num > 6: session['code'] = True;
    
    #IP限制
    def limit_address(self,type,v=""):
        import time
        clientIp = public.GetClientIp();
        numKey = 'limitIpNum_' + v + clientIp
        limit = 6;
        outTime = 600;
        try:
            #初始化
            num1 = cache.get(numKey)
            if not num1:
                cache.set(numKey,1,outTime);
                num1 = 1;
                        
            #计数
            if type == '+':
                cache.inc(numKey,1)
                self.error_num();
                session['code'] = True;
                return limit - (num1+1);

            #计数验证器
            if type == '++':
                cache.inc(numKey,1)
                self.error_num();
                session['code'] = False;
                return limit - (num1+1);

            #清空
            if type == '-':
                cache.delete(numKey);
                session['code'] = False;
                return 1;

            #清空验证器
            if type == '--':
                cache.delete(numKey);
                session['code'] = False;
                return 1;
            return limit - num1;
        except:
            return limit;

    # 登录成功设置session
    def _set_login_session(self,userInfo):
        try:
            session['login'] = True
            session['username'] = userInfo['username']
            public.WriteLog('TYPE_LOGIN','LOGIN_SUCCESS',(userInfo['username'],public.GetClientIp()))
            self.limit_address('-')
            cache.delete('panelNum')
            cache.delete('dologin')
            sess_input_path = 'data/session_last.pl'
            public.writeFile(sess_input_path,str(int(time.time())))
            self.set_request_token()
            self.login_token()
            return public.returnJson(True,'LOGIN_SUCCESS'),json_header
        except Exception as ex:
            stringEx = str(ex)
            if stringEx.find('unsupported') != -1 or stringEx.find('-1') != -1:
                os.system("rm -f /tmp/sess_*")
                os.system("rm -f /www/wwwlogs/*log")
                public.ServiceReload()
                return public.returnJson(False,'USER_INODE_ERR'),json_header
            public.WriteLog('TYPE_LOGIN','LOGIN_ERR_PASS',('****','******',public.GetClientIp()))
            num = self.limit_address('+');
            return public.returnJson(False,'LOGIN_USER_ERR',(str(num),)),json_header


    # 检查是否需要进行二次验证
    def check_two_step_auth(self):
        dont_vcode_ip_info = public.readFile("/www/server/panel/data/dont_vcode_ip.txt")
        acc_client_ip = False
        if dont_vcode_ip_info:
            dont_vcode_ip_info = json.loads(dont_vcode_ip_info)
            ip = dont_vcode_ip_info["client_ip"] == public.GetClientIp()
            now = int(time.time())
            v_time = now - int(dont_vcode_ip_info["add_time"])
            if ip and v_time < 86400:
                acc_client_ip = True
        return acc_client_ip