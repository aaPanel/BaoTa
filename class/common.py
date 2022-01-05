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
from public import dict_obj
import os
import public
import json
import sys
import time


class panelSetup:
    def init(self):
        panel_path = public.get_panel_path()
        if os.getcwd() != panel_path: os.chdir(panel_path)

        g.ua = request.headers.get('User-Agent','')
        if g.ua:
            ua = g.ua.lower()
            if ua.find('spider') != -1 or g.ua.find('bot') != -1:
                return redirect('https://www.baidu.com')
        
        g.version = '7.9.12'
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
            
        g.recycle_bin_open = 0
        if os.path.exists("data/recycle_bin.pl"): g.recycle_bin_open = 1
        
        g.recycle_bin_db_open = 0
        if os.path.exists("data/recycle_bin_db.pl"): g.recycle_bin_db_open = 1
        g.is_aes = False
        self.other_import()
        return None


    def other_import(self):
        g.o = public.readFile('data/o.pl')
        g.other_css = []
        g.other_js = []
        if g.o:
            s_path = 'BTPanel/static/other/{}'
            css_name = "css/{}.css".format(g.o)
            css_file = s_path.format(css_name)
            if os.path.exists(css_file): g.other_css.append('/static/other/{}'.format(css_name))
            
            js_name = "js/{}.js".format(g.o)
            js_file = s_path.format(js_name)
            if os.path.exists(js_file): g.other_js.append('/static/other/{}'.format(js_name))



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
            session['download_url'] = public.GetConfigValue('download')
            session['setupPath'] = session['rootPath'] + '/server'
            session['logsPath'] = '/www/wwwlogs'
            session['yaer'] = datetime.now().year
        if not 'menu' in session:
            session['menu'] = public.GetLan('menu')
        if not 'lan' in session:
            session['lan'] = public.GetLanguage()
        if not 'home' in session:
            session['home'] = public.GetConfigValue('home')
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
                    # session.clear()
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
                ua_md5 = public.md5(g.ua)
                if ua_md5 != session.get('login_user_agent',ua_md5):
                    session.clear()
                    return redirect('/login')
                
            if api_check:
                now_time = time.time()
                session_timeout = session.get('session_timeout',0)
                if session_timeout < now_time and session_timeout != 0:
                    session.clear()
                    return redirect('/login?dologin=True&go=0')
        
            login_token = session.get('login_token','')
            if login_token:
                if login_token != public.get_login_token_auth():
                    session.clear()
                    return redirect('/login?dologin=True&go=1')
            
            # if api_check:
            #     filename = 'data/sess_files/' + public.get_sess_key()
            #     if not os.path.exists(filename):
            #         session.clear()
            #         return redirect('/login?dologin=True&go=2')

            # 标记新的会话过期时间
            session['session_timeout'] = time.time() + public.get_session_timeout()
        except:
            public.WriteLog('登录检查', public.get_error_info())
            session.clear()
            return redirect('/login')

    # 获取sk
    def get_sk(self):
        save_path = '/www/server/panel/config/api.json'
        if not os.path.exists(save_path):
            return public.error_not_login('/login')

        
        try:
            api_config = json.loads(public.ReadFile(save_path))
        except:
            os.remove(save_path)
            return  public.error_not_login('/login')
        
        if not api_config['open']:
            return  public.error_not_login('/login')
        from BTPanel import get_input
        get = get_input()
        client_ip = public.GetClientIp()
        if not 'client_bind_token' in get:
            if not 'request_token' in get or not 'request_time' in get:
                return  public.error_not_login('/login')
            
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
                return  public.error_not_login('/login')
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
            issue_file = '/etc/issue'
            redhat_release = '/etc/redhat-release'
            if os.path.exists(redhat_release):
                tmp['x'] = 'RHEL'
                tmp['osname'] = self.get_osname(redhat_release)
            elif os.path.exists('/usr/bin/yum'):
                tmp['x'] = 'RHEL'
                tmp['osname'] = self.get_osname(issue_file)
            elif os.path.exists(issue_file):
                tmp['x'] = 'Debian'
                tmp['osname'] = self.get_osname(issue_file)
            session['server_os'] = tmp
        return False


    def get_osname(self,i_file):
        '''
            @name 从指定文件中获取系统名称
            @author hwliang<2021-04-07>
            @param i_file<string> 指定文件全路径
            @return string
        '''
        if not os.path.exists(i_file): return ''
        issue_str = public.ReadFile(i_file).strip()
        if issue_str: return issue_str.split()[0]
        return ''
