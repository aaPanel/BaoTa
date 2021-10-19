# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2019 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------
import os
import sys
if not 'class/' in sys.path:
    sys.path.insert(0,'class/')
import public
import json
import time
from BTPanel import session,cache,request

class wxapp():

    def __init__(self):
        self.app_path = '/www/server/panel/data/'
        self.app_path_p = '/www/server/panel/plugin/app/'

    def _check(self, get):
        if get['fun'] in ['set_login', 'is_scan_ok', 'login_qrcode']:
            return True
        return public.returnMsg(False, '未授权')

    # 验证是否扫码成功
    def is_scan_ok(self, get):
        if os.path.exists(self.app_path+"app_login_check.pl"):
            key, init_time = public.readFile(self.app_path+'app_login_check.pl').split(':')
            if time.time() - float(init_time) > 180:
                return public.returnMsg(False, '二维码失效')
            session_id = public.get_session_id()
            if cache.get(session_id) == 'True':
                return public.returnMsg(True, '扫码成功')
        return public.returnMsg(False, '')

    # 返回二维码地址
    def login_qrcode(self, get):
        tid = public.GetRandomString(12)
        qrcode_str = 'https://app.bt.cn/app.html?&panel_url='+public.getPanelAddr()+'&v=' + public.GetRandomString(3)+'?login&tid=' + tid
        data = public.get_session_id() + ':' + str(time.time())
        public.writeFile(self.app_path + "app_login_check.pl", data)
        cache.set(tid,public.get_session_id(),360)
        cache.set(public.get_session_id(),tid,360)
        return public.returnMsg(True, qrcode_str)

    # 设置登录状态
    def set_login(self, get):
        session_id = public.get_session_id()
        if cache.get(session_id) == 'True':
            return self.check_app_login(get)
        return public.returnMsg(False, '登录失败1')

     #验证APP是否登录成功
    def check_app_login(self,get):
        #判断是否存在绑定
        btapp_info = json.loads(public.readFile('/www/server/panel/config/api.json'))
        if not btapp_info:return public.returnMsg(False,'未绑定')
        if not btapp_info['open']:return public.returnMsg(False,'未开启API')
        if not 'apps' in btapp_info:return public.returnMsg(False,'未绑定手机')
        if not btapp_info['apps']:return public.returnMsg(False,'未绑定手机')
        try:
            session_id=public.get_session_id()
            if not os.path.exists(self.app_path+'app_login_check.pl'):return public.returnMsg(False,'等待APP扫码登录1')
            data = public.readFile(self.app_path+'app_login_check.pl')
            public.ExecShell('rm ' + self.app_path+"app_login_check.pl")
            secret_key, init_time = data.split(':')
            if len(session_id)!=64:return public.returnMsg(False,'等待APP扫码登录2')
            if len(secret_key)!=64:return public.returnMsg(False,'等待APP扫码登录2')
            if time.time() - float(init_time) < 180 and session_id != secret_key:
                return public.returnMsg(False,'等待APP扫码登录')
            cache.delete(session_id)
            userInfo = public.M('users').where("id=?",(1,)).field('id,username').find()
            session['login'] = True
            session['username'] = userInfo['username']
            session['tmp_login'] = True
            public.WriteLog('TYPE_LOGIN','APP扫码登录，帐号：{},登录IP：{}'.format(userInfo['username'],public.GetClientIp()+ ":" + str(request.environ.get('REMOTE_PORT'))))
            cache.delete('panelNum')
            cache.delete('dologin')
            session['session_timeout'] = time.time() + public.get_session_timeout()
            login_type = 'data/app_login.pl'
            self.set_request_token()
            import config
            config.config().reload_session()
            public.writeFile(login_type,'True')
            public.login_send_body("堡塔APP",userInfo['username'],public.GetClientIp(),str(request.environ.get('REMOTE_PORT')))
            return public.returnMsg(True,'登录成功!')
        except:
            return public.returnMsg(False, '登录失败2')
    #生成request_token
    def set_request_token(self):
        session['request_token_head'] = public.GetRandomString(48)
