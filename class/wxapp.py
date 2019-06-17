# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2019 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------
import os
import sys
sys.path.append("class/")
import public
import db
import json
import time
import binascii 
import base64
from BTPanel import session,cache

class ScanLogin(object):
    # 扫码登录面板
    def scan_login(self, get):
        # 用于小程序
        data = public.GetRandomString(48) + ':' + str(time.time())
        public.writeFile(self.app_path+"login.pl", data)
        return public.returnMsg(True, '扫码成功, 正在登录')

    # 验证是否扫码成功
    def is_scan_ok(self, get):
        if os.path.exists(self.app_path+"login.pl"):
            key, init_time = public.readFile(
                self.app_path+'login.pl').split(':')
            if time.time() - float(init_time) < 60:
                return public.returnMsg(True, key)
        return public.returnMsg(False, '')

    # 返回二维码地址
    def login_qrcode(self, get):
        qrcode_str = 'https://app.bt.cn/app.html?&panel_url='+public.getPanelAddr()+'&v=' + public.GetRandomString(3)+'?login';
        return public.returnMsg(True, qrcode_str)

    # 设置登录状态
    def set_login(self, get):
        if os.path.exists(self.app_path+"login.pl"):
            data = public.readFile(self.app_path+'login.pl')
            public.ExecShell('rm ' + self.app_path+"login.pl")
            secret_key, init_time = data.split(':')
            if time.time() - float(init_time) < 60 and get['secret_key'] == secret_key:
                sql = db.Sql()
                userInfo = sql.table('users').where(
                    "id=?", (1,)).field('id,username,password').find()
                session['login'] = True
                session['username'] = userInfo['username']
                cache.delete('panelNum')
                cache.delete('dologin')
                public.WriteLog('TYPE_LOGIN', 'LOGIN_SUCCESS',
                                ('微信扫码登录', public.GetClientIp()))
                return public.returnMsg(True, '登录成功')
        return public.returnMsg(False, '登录失败')

class SelfModule():
    '''
    只能在面板执行的模块
    不允许外部访问
    '''

    def __init__(self):
        self.user_info_file = self.app_path + "user.json"
        if not os.path.exists(self.user_info_file):
            public.ExecShell("echo '{}' > " + self.user_info_file)
        try:
            self.user_info = json.loads(public.readFile(self.user_info_file))
        except: public.ExecShell("echo '{}' > " + self.user_info_file)
        
        user_info_file_app = self.app_path_p + "user.json"
        if os.path.exists(user_info_file_app):
            try:
                user_info_app = json.loads(public.readFile(user_info_file_app))
                for userId in user_info_app.keys():
                    if userId in self.user_info: continue;
                    self.user_info[userId] = user_info_app[userId];
            except:pass
        
    def blind_qrcode(self, get):
        '''
        生成绑定二维码
        '''
        panel_addr = public.getPanelAddr()
        token = public.GetRandomString(32)
        data = '%s:%s' % (token, int(time.time()))
        public.writeFile(self.app_path + 'token.pl',data)
        public.writeFile(self.app_path_p + 'token.pl',data)
        qrcode_str = 'https://app.bt.cn/app.html?panel_url=' + \
            panel_addr+'&panel_token=' + token + '?blind'
        return public.returnMsg(True, qrcode_str)

    def blind_del(self, get):
        # 删除绑定
        del self.user_info[get['uid']]
        public.writeFile(self.app_path+"user.json", json.dumps(self.user_info))
        public.writeFile(self.app_path_p + "user.json", json.dumps(self.user_info))
        return public.returnMsg(True, '删除成功')

    def get_user_info(self, get):
        if session['version'] < '5.8.6':
            return public.returnMsg(False, '面板版本过低，请升级到最新版')
        
        data = {}
        if not get: data = []
        for k in self.user_info.keys():
            v = self.user_info[k]
            if get:
                del(v['token'])
                data[k] = v
            else:
                data.append(v['nickName'])
        if not get: 
            data = ','.join(data);
            if not data: data = u'当前未绑定微信号';
        return public.returnMsg(True, data)

    def blind_result(self, get):
        return not os.path.exists(self.app_path + "token.pl")
    
class wxapp(SelfModule, ScanLogin):

    def __init__(self):
        self.app_path = '/www/server/panel/data/'
        self.app_path_p = '/www/server/panel/plugin/app/'
        SelfModule.__init__(self)

    def _check(self, get):
        token_data = public.readFile(self.app_path + 'token.pl')
        if not token_data: token_data = public.readFile(self.app_path_p + 'token.pl')
        if hasattr(SelfModule, get['fun']):
            return False
        elif get['fun'] in ['set_login', 'is_scan_ok', 'login_qrcode']:
            return True
        elif get['fun'] == 'blind':
            if not token_data:
                return public.returnMsg(False, '二维码过期1')
            token_data = token_data.replace('\n', '')
            password, expiration_time = token_data.split(':')
            # return True
            if time.time() - int(expiration_time) > 8*60:
                return public.returnMsg(False, '二维码过期2')
            elif get['panel_token'] != password:
                return public.returnMsg(False, '秘钥不正确')
            return True
        else:
            # 是否在白名单ip    sgin 是否正确
            if hasattr(get, 'uid') and hasattr(get, 'sgin') and hasattr(get, 'fun') and get['uid'] in self.user_info.keys():
                encryption_str = self.user_info[get['uid']]['token']+get['fun']+get['uid']
            if get['sgin'] == public.md5(binascii.hexlify(base64.b64encode(encryption_str))):
                if get['client_ip'] in ['118.24.150.167', '103.224.251.67', '125.88.182.170', '47.52.194.186', '39.104.53.226','119.147.144.162']:
                    return True
            return public.returnMsg(False, '未授权')

    # 用户绑定
    def blind(self, get):
        # 用于小程序
        self.user_info[get['uid']] = {
            "avatarUrl":  get['avatarUrl'],
            "nickName": get['nickName'],
            "token": get['token']
        }
        public.writeFile(self.app_path+"user.json", json.dumps(self.user_info))
        public.writeFile(self.app_path_p + "user.json", json.dumps(self.user_info))
        public.ExecShell("rm -rf %stoken.pl" % self.app_path)
        public.ExecShell("rm -rf %stoken.pl" % self.app_path_p)
        return public.returnMsg(True, '绑定成功')
    

    def get_safe_log(self):
        get = {
            'page': 1,
            'count': 10
        }
        print(get['page'] - 1) * get['count'], get['count']
        data = public.M('logs').limit('%s, %s' % (
            (get['page'] - 1) * get['count'], get['count'])).select()
        return data
