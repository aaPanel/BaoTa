#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------
from flask import request,redirect,g
from BTPanel import session,cache
from datetime import datetime
import os,public,json,sys,time
class dict_obj:
    def __contains__(self, key):
        return getattr(self,key,None)
    def __setitem__(self, key, value): setattr(self,key,value)
    def __getitem__(self, key): return getattr(self,key,None)
    def __delitem__(self,key): delattr(self,key)
    def __delattr__(self, key): delattr(self,key)
    def get_items(self): return self



class panelSetup:
    def init(self):
        ua = request.headers.get('User-Agent')
        if ua:
            ua = ua.lower();
            if ua.find('spider') != -1 or ua.find('bot') != -1: return redirect('https://www.baidu.com');
        g.version = '7.0.2'
        g.title =  public.GetConfigValue('title')
        g.uri = request.path
        session['version'] = g.version;
        session['title'] = g.title
        return None
        
        
class panelAdmin(panelSetup):
    setupPath = '/www/server'
            
    #本地请求
    def local(self):
        result = panelSetup().init()
        if result: return result
        result = self.setSession();
        if result: return result
        result = self.checkClose();
        if result: return result
        result = self.checkWebType();
        if result: return result
        result = self.check_login();
        if result: return result
        result = self.checkConfig();
        self.GetOS();
    
        
    #设置基础Session
    def setSession(self):
        session['menus'] = sorted(json.loads(public.ReadFile('config/menu.json')),key=lambda x:x['sort'])
        session['yaer'] = datetime.now().year
        session['download_url'] = 'http://download.bt.cn';
        if not 'brand' in session:
            session['brand'] = public.GetConfigValue('brand');
            session['product'] = public.GetConfigValue('product');
            session['rootPath'] = '/www'
            session['download_url'] = 'http://download.bt.cn';
            session['setupPath'] = session['rootPath'] + '/server';
            session['logsPath'] = '/www/wwwlogs';
            session['yaer'] = datetime.now().year
        if not 'menu' in session:
            session['menu'] = public.GetLan('menu');
        if not 'lan' in session:
            session['lan'] = public.GetLanguage();
        if not 'home' in session:
            session['home'] = 'http://www.bt.cn';
            
    
    #检查Web服务器类型
    def checkWebType(self):
        if os.path.exists(self.setupPath + '/nginx'):
            session['webserver'] = 'nginx'
        else:
            session['webserver'] = 'apache'
        if os.path.exists(self.setupPath+'/'+session['webserver']+'/version.pl'):
            session['webversion'] = public.ReadFile(self.setupPath+'/'+session['webserver']+'/version.pl').strip()
        filename = self.setupPath+'/data/phpmyadminDirName.pl'
        if os.path.exists(filename):
            session['phpmyadminDir'] = public.ReadFile(filename).strip()
    
    #检查面板是否关闭
    def checkClose(self):
        if os.path.exists('data/close.pl'):
            return redirect('/close');
        
    #检查登录
    def check_login(self):
        try:
            api_check = True
            if not 'login' in session: 
                api_check = self.get_sk()
                if api_check: 
                    session.clear()
                    return api_check
            else:
                if session['login'] == False: 
                    session.clear()
                    return redirect('/login')
            if api_check:
                try:
                    sess_out_path = 'data/session_timeout.pl'
                    sess_input_path = 'data/session_last.pl'
                    if not os.path.exists(sess_out_path): public.writeFile(sess_out_path,'86400')
                    if not os.path.exists(sess_input_path): public.writeFile(sess_input_path,str(int(time.time())))
                    session_timeout = int(public.readFile(sess_out_path))
                    session_last = int(public.readFile(sess_input_path))
                    if time.time() - session_last > session_timeout: 
                        os.remove(sess_input_path)
                        session['login'] = False;
                        cache.set('dologin',True)
                        session.clear()
                        return redirect('/login')
                    public.writeFile(sess_input_path,str(int(time.time())))
                except:pass

            filename = '/www/server/panel/data/login_token.pl'
            if os.path.exists(filename):
                token = public.readFile(filename).strip()
                if 'login_token' in session:
                    if session['login_token'] != token:
                        session.clear()
                        return redirect('/login?dologin=True')
        except:
            session.clear()
            return redirect('/login')

    #获取sk
    def get_sk(self,):
        save_path = '/www/server/panel/config/api.json'
        if not os.path.exists(save_path): return redirect('/login')
        api_config = json.loads(public.ReadFile(save_path))
        if not api_config['open']: return redirect('/login')
        from BTPanel import get_input
        get = get_input()
        if not 'request_token' in get or not 'request_time' in get: return redirect('/login')
        client_ip = public.GetClientIp()
        if not client_ip in api_config['limit_addr']: return public.returnJson(False,'IP校验失败,您的访问IP为['+client_ip+']')
        request_token = public.md5(get.request_time + api_config['token'])
        if get.request_token == request_token: return False
        return public.returnJson(False,'密钥校验失败')

    
    #检查系统配置
    def checkConfig(self):
        if not 'config' in session:
            session['config'] = public.M('config').where("id=?",('1',)).field('webserver,sites_path,backup_path,status,mysql_root').find();
            if not 'email' in session['config']:
                session['config']['email'] = public.M('users').where("id=?",('1',)).getField('email');
            if not 'address' in session:
                session['address'] = public.GetLocalIp()
    
    #获取操作系统类型 
    def GetOS(self):
        if not 'server_os' in session:
            tmp = {}
            if os.path.exists('/etc/redhat-release'):
                tmp['x'] = 'RHEL';
                tmp['osname'] = public.ReadFile('/etc/redhat-release').split()[0];
            elif os.path.exists('/usr/bin/yum'):
                tmp['x'] = 'RHEL';
                tmp['osname'] = public.ReadFile('/etc/issue').split()[0];
            elif os.path.exists('/etc/issue'): 
                tmp['x'] = 'Debian';
                tmp['osname'] = public.ReadFile('/etc/issue').split()[0];
            session['server_os'] = tmp
            