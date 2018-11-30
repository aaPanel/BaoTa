#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http:#bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------

import public,os,sys,db
from BTPanel import session,cache,json_header
from flask import request,redirect,g

class userlogin:
    
    def request_post(self,post):
        if not (hasattr(post, 'username') or hasattr(post, 'password') or hasattr(post, 'code')):
            return public.returnJson(False,'LOGIN_USER_EMPTY'),json_header
        
        self.error_num(False)
        if self.limit_address('?') < 1: return public.returnJson(False,'LOGIN_ERR_LIMIT'),json_header
        
        post.username = post.username.strip();
        password = public.md5(post.password.strip());
        sql = db.Sql();
        userInfo = sql.table('users').where("id=?",(1,)).field('id,username,password').find()
        m_code = cache.get('codeStr')
        if 'code' in session:
            if session['code']:
                if not public.checkCode(post.code):
                    public.WriteLog('TYPE_LOGIN','LOGIN_ERR_CODE',('****','****',public.GetClientIp()));
                    return public.returnJson(False,'CODE_ERR'),json_header
        try:
            if userInfo['username'] != post.username or userInfo['password'] != password:
                public.WriteLog('TYPE_LOGIN','LOGIN_ERR_PASS',('****','******',public.GetClientIp()));
                num = self.limit_address('+');
                return public.returnJson(False,'LOGIN_USER_ERR',(str(num),)),json_header
            
            session['login'] = True;
            session['username'] = userInfo['username'];
            public.WriteLog('TYPE_LOGIN','LOGIN_SUCCESS',(userInfo['username'],public.GetClientIp()));
            self.limit_address('-');
            cache.delete('panelNum')
            cache.delete('dologin')
            return public.returnJson(True,'LOGIN_SUCCESS'),json_header
        except Exception as ex:
            stringEx = str(ex)
            if stringEx.find('unsupported') != -1 or stringEx.find('-1') != -1: 
                os.system("rm -f /tmp/sess_*")
                os.system("rm -f /www/wwwlogs/*log")
                public.ServiceReload()
                return public.returnJson(False,'磁盘Inode已用完,面板已尝试释放Inode,请重试...'),json_header
            public.WriteLog('TYPE_LOGIN','LOGIN_ERR_PASS',('****','******',public.GetClientIp()));
            num = self.limit_address('+');
            return public.returnJson(False,'LOGIN_USER_ERR',(str(num),)),json_header

    def request_get(self,get):
        #if os.path.exists('/www/server/panel/install.pl'): raise redirect('/install');
        if not 'title' in session: session['title'] = public.getMsg('NAME');
        domain = public.readFile('data/domain.conf')
        
        if domain:
            if(public.GetHost().lower() != domain.strip().lower()): 
                
                errorStr = '''
<meta charset="utf-8">
<title>%s</title>
</head><body>
<h1>%s</h1>
    <p>%s</p>
    <p>%s</p>
    <p>%s</p>
<hr>
<address>%s 6.x <a href="http://www.bt.cn/bbs" target="_blank">%s</a></address>
</body></html>
    ''' % (public.getMsg('PAGE_ERR_TITLE'),public.getMsg('PAGE_ERR_DOMAIN_H1'),public.getMsg('PAGE_ERR_DOMAIN_P1'),public.getMsg('PAGE_ERR_DOMAIN_P2'),public.getMsg('PAGE_ERR_DOMAIN_P3'),public.getMsg('NAME'),public.getMsg('PAGE_ERR_HELP'))
                return errorStr
        if os.path.exists('data/limitip.conf'):
            iplist = public.readFile('data/limitip.conf')
            if iplist:
                iplist = iplist.strip();
                if not public.GetClientIp() in iplist.split(','):
                    errorStr = '''
<meta charset="utf-8">
<title>%s</title>
</head><body>
<h1>%s</h1>
    <p>%s</p>
    <p>%s</p>
    <p>%s</p>
<hr>
<address>%s 6.x <a href="http://www.bt.cn/bbs" target="_blank">%s</a></address>
</body></html>
''' % (public.getMsg('PAGE_ERR_TITLE'),public.getMsg('PAGE_ERR_IP_H1'),public.getMsg('PAGE_ERR_IP_P1',(public.GetClientIp(),)),public.getMsg('PAGE_ERR_IP_P2'),public.getMsg('PAGE_ERR_IP_P3'),public.getMsg('NAME'),public.getMsg('PAGE_ERR_HELP'))
                    return errorStr
        
        sql = db.Sql()
        
        if 'login' in session:
            if session['login'] == True:
                return redirect('/')
        
        if not 'code' in session:
            session['code'] = False
        self.error_num(False)

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
    def limit_address(self,type):
        import time
        clientIp = public.GetClientIp();
        numKey = 'limitIpNum_' + clientIp
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
            
            #清空
            if type == '-':
                cache.delete(numKey);
                session['code'] = False;
                return 1;
            return limit - num1;
        except:
            return limit;


