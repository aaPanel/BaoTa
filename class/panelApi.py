#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2017 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 阿良 <287962566@qq.com>
# +-------------------------------------------------------------------
import public,os,json,time
class panelApi:
    save_path = '/www/server/panel/config/api.json'
    timeout = 600
    max_bind = 5
    def get_token(self,get):
        data = self.get_api_config()
        if not 'key' in data:
            data['key'] = public.GetRandomString(16)
            public.writeFile(self.save_path,json.dumps(data))

        if 'token_crypt' in data:
            data['token'] = public.de_crypt(data['token'],data['token_crypt'])
        else:
            data['token'] = "***********************************"
                
        data['limit_addr'] = '\n'.join(data['limit_addr'])
        data['bind'] = self.get_bind_token()
        qrcode = (public.getPanelAddr() + "|" + data['token'] + "|" + data['key'] + '|' + data['bind']['token']).encode('utf-8')
        data['qrcode'] = public.base64.b64encode(qrcode).decode('utf-8')
        data['apps'] = sorted(data['apps'],key=lambda x: x['time'],reverse=True)
        del(data['key'])
        return data


    def login_for_app(self,get):
        from BTPanel import cache
        tid = get.tid
        if(len(tid) != 12): return public.returnMsg(False,'无效的登录密钥')
        session_id = cache.get(tid)
        if not session_id: return public.returnMsg(False,'指定密钥不存在，或已过期')
        if(len(session_id) != 64): return public.returnMsg(False,'无效的登录密钥')
        cache.set(session_id,'True',120)
        return public.returnMsg(True,'扫码成功,正在登录!')

    def get_api_config(self):
        tmp = public.ReadFile(self.save_path)
        if not tmp or not os.path.exists(self.save_path): 
            data = { "open":False, "token":"", "limit_addr":[] }
            public.WriteFile(self.save_path,json.dumps(data))
            public.ExecShell("chmod 600 " + self.save_path)
            tmp = public.ReadFile(self.save_path)
        data = json.loads(tmp)

        is_save = False
        if not 'binds' in data:
            data['binds'] = []
            is_save = True

        if not 'apps' in data:
            data['apps'] = []
            is_save = True

        data['binds'] = sorted(data['binds'],key=lambda x: x['time'],reverse=True)
        if len(data['binds']) > 5:
            data['binds'] = data['binds'][:5]
            is_save = True
        
        if is_save:
            self.save_api_config(data)
        return data

    def save_api_config(self,data):
        public.WriteFile(self.save_path,json.dumps(data))
        public.set_mode(self.save_path,'600')
        return True

    def check_bind(self,args):
        if not 'bind_token' in args or not 'client_brand' in args or not 'client_model' in args:
            return 0
        if not args.client_brand or not args.client_model:
            return '无效的设备'
        
        bind = self.get_bind_token(args.bind_token)
        if bind['token'] != args.bind_token:
            return '当前二维码已过期，请刷新页面重新扫码!'

        apps = self.get_apps()
        if len(apps) >= self.max_bind:
            return '该服务器最多绑定{}台设备，已达到上限!'.format(self.max_bind)

        bind['status'] = 1
        bind['brand'] = args.client_brand
        bind['model'] = args.client_model
        self.set_bind_token(bind)
        return 1

    def get_bind_status(self,args):
        bind = self.get_bind_token(args.bind_token)
        return bind

    def get_app_bind_status(self,args):
        if not 'bind_token' in args:
            return 0
        if self.get_app_find(args.bind_token):
            return 1
        return 0
    
    def set_bind_token(self,bind):
        data = self.get_api_config()
        is_save = False
        for i in range(len(data['binds'])):
            if data['binds'][i]['token'] == bind['token']:
                data['binds'][i] = bind
                is_save = True
                break
        if is_save:
            self.save_api_config(data)
        return True


    def get_apps(self,args = None):
        data = self.get_api_config()
        return data['apps']

    def get_app_find(self,bind_token):
        apps = self.get_apps()
        for s_app in apps:
            if s_app['token'] == bind_token:
                return s_app
        return None

    def add_bind_app(self,args):
        bind = self.get_bind_token(args.bind_token)
        if bind['status'] == 0:
            return public.returnMsg(False,'未通过验证!')
        apps = self.get_apps()
        if len(apps) >= self.max_bind:
            return public.returnMsg(False,'一台服务器最多允许{}个设备绑定!'.format(self.max_bind))

        args.bind_app = args.bind_token
        self.remove_bind_app(args)
        data = self.get_api_config()
        data['apps'].append(bind)
        self.save_api_config(data)
        self.remove_bind_token(args.bind_token)
        return public.returnMsg(True,'绑定成功!')

    def remove_bind_token(self,bind_token):
        data = self.get_api_config()
        tmp_binds = []
        for s_bind in data['binds']:
            if bind_token == s_bind['token']:
                continue
            tmp_binds.append(s_bind)
        data['binds'] = tmp_binds
        self.save_api_config(data)

    def remove_bind_app(self,args):
        data = self.get_api_config()
        tmp_apps = []
        for s_app in data['apps']:
            if args.bind_app == s_app['token']:
                continue
            tmp_apps.append(s_app)
        data['apps'] = tmp_apps
        self.save_api_config(data)
        s_file = '/dev/shm/{}'.format(args.bind_app)
        if os.path.exists(s_file):
            os.remove(s_file)
        return public.returnMsg(True,'删除成功!')

    def get_bind_token(self,token = None):
        data = self.get_api_config()
        s_time = time.time()
        binds = []
        bind = None
        is_write = False
        for i in range(len(data['binds'])):
            if s_time - data['binds'][i]['time'] > self.timeout:
                is_write = True
                continue
            binds.append(data['binds'][i])
            if token:
                if token == data['binds'][i]['token']:
                    bind = data['binds'][i]
            else:
                if not bind:
                    bind = data['binds'][i]
        if not bind:
            if len(binds) > 0:
                binds = sorted(binds,key=lambda x: x['time'],reverse=True)
                bind = binds[0]
            else:
                bind = {"time":s_time,"token":public.GetRandomString(18),'status':0}
                binds.append(bind)
                is_write = True

        if is_write:
            data['binds'] = binds
            self.save_api_config(data)
        return bind
        

    def set_token(self,get):
        if 'request_token' in get: return public.returnMsg(False,'不能通过API接口配置API')
        data = self.get_api_config()
        if get.t_type == '1':
            token = public.GetRandomString(32)
            data['token'] = public.md5(token)
            data['token_crypt'] = public.en_crypt(data['token'],token).decode('utf-8')
            public.WriteLog('API配置','重新生成API-Token')
        elif get.t_type == '2':
            data['open'] = not data['open']
            stats = {True:'开启',False:'关闭'}
            if not 'token_crypt' in data:
                token = public.GetRandomString(32)
                data['token'] = public.md5(token)
                data['token_crypt'] = public.en_crypt(data['token'],token).decode('utf-8')
            public.WriteLog('API配置','%sAPI接口' % stats[data['open']])
            token = stats[data['open']] + '成功!'
        elif get.t_type == '3':
            data['limit_addr'] = get.limit_addr.split('\n')
            public.WriteLog('API配置','变更IP限制为[%s]' % get.limit_addr)
            token ='保存成功!'
        self.save_api_config(data)
        return public.returnMsg(True,token)

    def get_tmp_token(self,get):
        if not 'request_token' in get: return public.returnMsg(False,'只能通过API接口获取临时密钥')
        data = self.get_api_config()
        data['tmp_token'] = public.GetRandomString(64)
        data['tmp_time'] = time.time()
        self.save_api_config(data)
        return public.returnMsg(True,data['tmp_token'])