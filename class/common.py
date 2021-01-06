#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------
from BTPanel import session, cache , request, redirect, g
from datetime import datetime
import os
import public
import json
import sys
import time


class dict_obj:
    def __contains__(self, key):
        return getattr(self, key, None)

    def __setitem__(self, key, value): setattr(self, key, value)
    def __getitem__(self, key): return getattr(self, key, None)
    def __delitem__(self, key): delattr(self, key)
    def __delattr__(self, key): delattr(self, key)
    def get_items(self): return self


class panelSetup:
    def init(self):
        ua = request.headers.get('User-Agent','')
        if ua:
            ua = ua.lower()
            if ua.find('spider') != -1 or ua.find('bot') != -1:
                return redirect('https://www.baidu.com')
        
        g.version = '7.5.32'
        g.title = public.GetConfigValue('title')
        g.uri = request.path
        g.debug = os.path.exists('data/debug.pl')
        g.pyversion = sys.version_info[0]
        session['version'] = g.version
        
        if request.method == 'GET':
            if not g.debug:
                g.cdn_url = public.get_cdn_url()
                if not g.cdn_url:
                    g.cdn_url = '/static'
                else:
                    g.cdn_url = '//' + g.cdn_url + '/' + g.version
            else:
                g.cdn_url = '/static'
            session['title'] = g.title
            dirPath = '/www/server/phpmyadmin/pma'
            if os.path.exists(dirPath):
                public.ExecShell("rm -rf {}".format(dirPath))
            
            dirPath = '/www/server/adminer'
            if os.path.exists(dirPath):
                public.ExecShell("rm -rf {}".format(dirPath))
            
            dirPath = '/www/server/panel/adminer'
            if os.path.exists(dirPath):
                public.ExecShell("rm -rf {}".format(dirPath))
            
        g.is_aes = False
        return None


class panelAdmin(panelSetup):
    setupPath = '/www/server'

    # 本地请求
    def local(self):
        result = panelSetup().init()
        if result:
            return result
        result = self.check_login()
        if result:
            return result
        result = self.setSession()
        if result:
            return result
        result = self.checkClose()
        if result:
            return result
        result = self.checkWebType()
        if result:
            return result
        result = self.checkConfig()
        self.GetOS()

    # 设置基础Session
    def setSession(self):
        if request.method == 'GET':
            g.menus = public.get_menus()
            g.yaer = datetime.now().year

        if not 'brand' in session:
            session['brand'] = public.GetConfigValue('brand')
            session['product'] = public.GetConfigValue('product')
            session['rootPath'] = '/www'
            session['download_url'] = 'http://download.bt.cn'
            session['setupPath'] = session['rootPath'] + '/server'
            session['logsPath'] = '/www/wwwlogs'
            session['yaer'] = datetime.now().year
        if not 'menu' in session:
            session['menu'] = public.GetLan('menu')
        if not 'lan' in session:
            session['lan'] = public.GetLanguage()
        if not 'home' in session:
            session['home'] = 'http://www.bt.cn'
        return False

    # 检查Web服务器类型
    def checkWebType(self):
        #if request.method == 'GET':
        if not 'webserver' in session:
            if os.path.exists('/usr/local/lsws/bin/lswsctrl'):
                session['webserver'] = 'openlitespeed'
            elif os.path.exists(self.setupPath + '/apache/bin/apachectl'):
                session['webserver'] = 'apache'
            else:
                session['webserver'] = 'nginx'
        if not 'webversion' in session:
            if os.path.exists(self.setupPath+'/'+session['webserver']+'/version.pl'):
                session['webversion'] = public.ReadFile(self.setupPath+'/'+session['webserver']+'/version.pl').strip()
            
        if not 'phpmyadminDir' in session:
            filename = self.setupPath+'/data/phpmyadminDirName.pl'
            if os.path.exists(filename):
                session['phpmyadminDir'] = public.ReadFile(filename).strip()
        return False

    # 检查面板是否关闭
    def checkClose(self):
        if os.path.exists('data/close.pl'):
            return redirect('/close')

    # 检查登录
    def check_login(self):
        try:
            api_check = True
            g.api_request = False
            if not 'login' in session:
                api_check = self.get_sk()
                if api_check:
                    session.clear()
                    return api_check
                g.api_request = True
            else:
                if session['login'] == False:
                    session.clear()
                    return redirect('/login')
                
                if 'tmp_login_expire' in session:
                    s_file = 'data/session/{}'.format(session['tmp_login_id'])
                    if session['tmp_login_expire'] < time.time():
                        session.clear()
                        if os.path.exists(s_file): os.remove(s_file)
                        return redirect('/login')
                    if not os.path.exists(s_file):
                        session.clear()
                        return redirect('/login')
                
            if api_check:
                try:
                    sess_out_path = 'data/session_timeout.pl'
                    sess_input_path = 'data/session_last.pl'
                    if not os.path.exists(sess_out_path):
                        public.writeFile(sess_out_path, '86400')
                    if not os.path.exists(sess_input_path):
                        public.writeFile(
                            sess_input_path, str(int(time.time())))
                    session_timeout = int(public.readFile(sess_out_path))
                    session_last = int(public.readFile(sess_input_path))
                    if time.time() - session_last > session_timeout:
                        os.remove(sess_input_path)
                        session['login'] = False
                        cache.set('dologin', True)
                        session.clear()
                        return redirect('/login')
                    public.writeFile(sess_input_path, str(int(time.time())))
                except:
                    pass

            filename = '/www/server/panel/data/login_token.pl'
            if os.path.exists(filename):
                token = public.readFile(filename).strip()
                if 'login_token' in session:
                    if session['login_token'] != token:
                        session.clear()
                        return redirect('/login?dologin=True&go=1')
            if api_check:
                filename = 'data/sess_files/' + public.get_sess_key()
                if not os.path.exists(filename):
                    session.clear()
                    return redirect('/login?dologin=True&go=2')
        except:
            session.clear()
            return redirect('/login')

    # 获取sk
    def get_sk(self):
        save_path = '/www/server/panel/config/api.json'
        if not os.path.exists(save_path):
            return redirect('/login')

        
        try:
            api_config = json.loads(public.ReadFile(save_path))
        except:
            os.remove(save_path)
            return redirect('/login')
        
        if not api_config['open']:
            return redirect('/login')
        from BTPanel import get_input
        get = get_input()
        client_ip = public.GetClientIp()
        if not 'client_bind_token' in get:
            if not 'request_token' in get or not 'request_time' in get:
                return redirect('/login')
            
            num_key = client_ip + '_api'
            if not public.get_error_num(num_key,20):
                return public.returnJson(False,'连续20次验证失败,禁止1小时')


            if not client_ip in api_config['limit_addr']:
                public.set_error_num(num_key)
                return public.returnJson(False, 'IP校验失败,您的访问IP为['+client_ip+']')
        else:
            num_key = client_ip + '_app'
            if not public.get_error_num(num_key,20):
                return public.returnJson(False,'连续20次验证失败,禁止1小时')
            a_file = '/dev/shm/' + get.client_bind_token
            if not os.path.exists(a_file):
                import panelApi
                if not panelApi.panelApi().get_app_find(get.client_bind_token):
                    public.set_error_num(num_key)
                    return public.returnJson(False,'未绑定的设备')
                public.writeFile(a_file,'')
            
            if not 'key' in api_config:
                public.set_error_num(num_key)
                return public.returnJson(False, '密钥校验失败')
            if not 'form_data' in get:
                public.set_error_num(num_key)
                return public.returnJson(False,'没有找到form_data数据')
            
            g.form_data = json.loads(public.aes_decrypt(get.form_data,api_config['key']))
            
            get = get_input()
            if not 'request_token' in get or not 'request_time' in get:
                return redirect('/login')
            g.is_aes = True
            g.aes_key = api_config['key']
        
        request_token = public.md5(get.request_time + api_config['token'])
        if get.request_token == request_token:
            public.set_error_num(num_key,True)
            return False
        public.set_error_num(num_key)
        return public.returnJson(False, '密钥校验失败')

    # 检查系统配置
    def checkConfig(self):
        if not 'config' in session:
            session['config'] = public.M('config').where("id=?", ('1',)).field(
                'webserver,sites_path,backup_path,status,mysql_root').find()
            if not 'email' in session['config']:
                session['config']['email'] = public.M(
                    'users').where("id=?", ('1',)).getField('email')
            if not 'address' in session:
                session['address'] = public.GetLocalIp()
        return False

    # 获取操作系统类型
    def GetOS(self):
        if not 'server_os' in session:
            tmp = {}
            if os.path.exists('/etc/redhat-release'):
                tmp['x'] = 'RHEL'
                tmp['osname'] = public.ReadFile(
                    '/etc/redhat-release').split()[0]
            elif os.path.exists('/usr/bin/yum'):
                tmp['x'] = 'RHEL'
                tmp['osname'] = public.ReadFile('/etc/issue').split()[0]
            elif os.path.exists('/etc/issue'):
                tmp['x'] = 'Debian'
                tmp['osname'] = public.ReadFile('/etc/issue').split()[0]
            session['server_os'] = tmp
        return False
