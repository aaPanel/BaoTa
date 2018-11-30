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
import os,public,json,sys
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
        
        g.version = '6.6.6'
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
        result = self.checkLimitIp()
        if result: return result
        result = self.setSession();
        if result: return result
        result = self.checkClose();
        if result: return result
        result = self.checkWebType();
        if result: return result
        result = self.checkDomain();
        if result: return result
        result = self.checkConfig();
        #self.checkSafe();
        self.GetOS();
    
    
    #检查IP白名单
    def checkAddressWhite(self):
        token = self.GetToken();
        if not token: return redirect('/login');
        if not request.remote_addr in token['address']: return redirect('/login');
        
    
    #检查IP限制
    def checkLimitIp(self):
        if os.path.exists('data/limitip.conf'):
            iplist = public.ReadFile('data/limitip.conf')
            if iplist:
                iplist = iplist.strip();
                if not request.remote_addr in iplist.split(','): return redirect('/login')
    
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
        
    #检查域名绑定
    def checkDomain(self):
        try:
            if not session['login']: return redirect('/login')
            tmp = public.GetHost()
            domain = public.ReadFile('data/domain.conf')
            if domain:
                if(tmp.strip().lower() != domain.strip().lower()): return redirect('/login')
        except:
            return redirect('/login')
    
    #检查系统配置
    def checkConfig(self):
        if not 'config' in session:
            session['config'] = public.M('config').where("id=?",('1',)).field('webserver,sites_path,backup_path,status,mysql_root').find();
            if not 'email' in session['config']:
                session['config']['email'] = public.M('users').where("id=?",('1',)).getField('email');
            if not 'address' in session:
                session['address'] = public.GetLocalIp()
    
    def checkSafe(self):
        mods = ['/','/site','/ftp','/database','/plugin','/soft','/public'];
        if not os.path.exists('/www/server/panel/data/userInfo.json'):
            if 'vip' in session: del(session.vip);
        if not request.path in mods: return True
        if 'vip' in session: return True
        
        import panelAuth
        data = panelAuth.panelAuth().get_order_status(None);
        try:
            if data['status'] == True: 
                session.vip = data
                return True
            return redirect('/vpro');
        except:pass
        return False
    
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
            