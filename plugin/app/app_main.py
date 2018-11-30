# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2019 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 戴艺森 <623815825@qq.com>
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
from BTPanel import session
   
 
class SelfModule():
    '''
    只能在面板执行的模块
    不允许外部访问
    '''

    def __init__(self):
        self.user_info_file = self.app_path+"user.json"
        
        if not os.path.exists(self.user_info_file):
            public.ExecShell("echo '{}' > " + self.user_info_file)
        self.user_info = json.loads(public.readFile(self.user_info_file))
        
        user_info_file_app = self.app_path_p + "user.json"
        if os.path.exists(user_info_file_app):
            user_info_app = json.loads(public.readFile(user_info_file_app))
            for userId in user_info_app.keys():
                if userId in self.user_info: continue;
                self.user_info[userId] = user_info_app[userId];
        
    def blind_qrcode(self, get):
        '''
        生成绑定二维码
        '''
        panel_addr = public.getPanelAddr()
        token = public.GetRandomString(32)
        data = '%s:%s' % (token, int(time.time()))
        public.writeFile(self.app_path + 'token.pl',data)
        public.writeFile(self.app_path_p + 'token.pl',data)
        qrcode_str = 'https://app.bt.cn/app.html?panel_url=' + panel_addr+'&panel_token=' + token + '?blind'
        return public.returnMsg(True, qrcode_str)

    def blind_del(self, get):
        # 删除绑定
        del(self.user_info[get['uid']])
        public.writeFile(self.app_path + "user.json", json.dumps(self.user_info))
        public.writeFile(self.app_path_p + "user.json", json.dumps(self.user_info))
        return public.returnMsg(True, '删除成功')

    def get_user_info(self, get):
        if session['version'] < '5.8.6':
            return public.returnMsg(False, '面板版本过低，请升级到最新版')
        return public.returnMsg(True, self.user_info)

    def blind_result(self, get):
        return not os.path.exists(self.app_path + "token.pl")


class monitorModule():
    '''
    监控数据 处理
    '''

    def getInfo(self, get):
        import ajax
        self.ajax = ajax.ajax()
        now_time_stamp = time.time()
        if get.stype == '7':
            # 近7天
            get.start = now_time_stamp - 7*24*3600
            get.end = now_time_stamp
        elif get.stype == '1':
            # 昨天
            get.end = now_time_stamp - now_time_stamp % 86400 + time.timezone
            get.start = get.end - 24*3600
        elif get.stype == '-1':
            # 自定义
            get.start = time.mktime(time.strptime(get.start, "%Y-%m-%d"))
            get.end = time.mktime(time.strptime(get.end, "%Y-%m-%d"))

        else:
            # 实时
            get.start = now_time_stamp - now_time_stamp % 86400 + time.timezone
            get.end = now_time_stamp

        return {'cpuIO': self.__GetCpuIO(get), 'netWorkIo': self.__GetNetWorkIo(get),
                'diskIo': self.__GetDiskIo(get), 'LoadAverage': self.__GetLoadAverage(get)}

    def __GetCpuIO(self, get):
        res = self.ajax.GetCpuIo(get)
        res = res[::(120+len(res))/120]
        mem_list = []
        cpu_list = []
        date_list = []
        if res:
            for i in res:
                mem_list.append(i['mem'])
                cpu_list.append(i['pro'])

            date_spacing = len(res) / 5
            for i in xrange(6):
                n = -1 if i == 5 else i*date_spacing
                addtime_arr = res[n]['addtime'].split(' ')
                addtime = addtime_arr[0] if get.stype == '7' or get.stype == '-1' else addtime_arr[1]
                date_list.append(addtime)
        return [date_list, [{'cpu': cpu_list}], [{'mem': mem_list}]]

    def __GetNetWorkIo(self, get):
        res = self.ajax.GetNetWorkIo(get)
        res = res[::(120+len(res))/120]
        up_list = []
        down_list = []
        date_list = []
        if res:
            for i in res:
                up_list.append(i['up'])
                down_list.append(i['down'])
            date_spacing = len(res) / 5
            for i in xrange(6):
                n = -1 if i == 5 else i*date_spacing
                addtime_arr = res[n]['addtime'].split(' ')
                addtime = addtime_arr[0] if get.stype == '7' or get.stype == '-1' else addtime_arr[1]
                date_list.append(addtime)
        return [date_list, [{'上行': up_list}, {'下行': down_list}]]

    def __GetDiskIo(self, get):
        res = self.ajax.GetDiskIo(get)
        res = res[::(120+len(res))/120]
        read_count = []
        write_count = []
        date_list = []
        if res:
            for i in res:
                read_count.append(i['read_count'])
                write_count.append(i['write_count'])
            date_spacing = len(res) / 5
            for i in xrange(6):
                n = -1 if i == 5 else i*date_spacing
                addtime_arr = res[n]['addtime'].split(' ')
                addtime = addtime_arr[0] if get.stype == '7' or get.stype == '-1' else addtime_arr[1]
                date_list.append(addtime)
        return [date_list, [{'读取次数': read_count}, {'写入次数': write_count}]]

    def __GetLoadAverage(self, get):
        res = self.ajax.get_load_average(get)
        res = res[::(120+len(res))/120]
        load_list = []
        date_list = []
        if res:
            for i in res:
                load_list.append(i['pro'])

            date_spacing = len(res) / 5
            for i in xrange(6):
                n = -1 if i == 5 else i*date_spacing
                addtime_arr = res[n]['addtime'].split(' ')
                addtime = addtime_arr[0] if get.stype == '7' or get.stype == '-1' else addtime_arr[1]
                date_list.append(addtime)
        return [date_list, [{'负载状态': load_list}]]


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


class app_main(SelfModule, ScanLogin):

    def __init__(self):
        self.app_path = '/www/server/panel/plugin/app/'
        self.app_path_p = '/www/server/panel/data/'
        SelfModule.__init__(self)

    def _check(self, get):
        token_data = public.readFile(self.app_path + 'token.pl')
        if hasattr(SelfModule, get['fun']):
            return False
        elif get['fun'] in ['set_login', 'is_scan_ok', 'login_qrcode']:
            return True
        elif get['fun'] == 'blind':
            if not token_data:
                return public.returnMsg(False, '二维码过期')

            token_data = token_data.replace('\n', '')
            password, expiration_time = token_data.split(':')
            # return True
            if time.time() - int(expiration_time) > 8*60:
                return public.returnMsg(False, '二维码过期')
            elif get['panel_token'] != password:
                return public.returnMsg(False, '秘钥不正确')
            return True
        else:
            # 是否在白名单ip    sgin 是否正确
            return get.client_ip
            if hasattr(get, 'uid') and hasattr(get, 'sgin') and hasattr(get, 'fun') and get['uid'] in self.user_info.keys():
                encryption_str = self.user_info[get['uid']]['token']+get['fun']+get['uid']
            if sys.version_info[0] == 3: 
                sgin = public.md5(binascii.hexlify(base64.b64encode(encryption_str.encode('utf-8'))).decode('utf-8'))
            else:
                sgin = public.md5(binascii.hexlify(base64.b64encode(encryption_str)))
            if get['sgin'] == sgin:
                if get['client_ip'] in ['11.183.194.99','118.24.150.167', '103.224.251.67', '125.88.182.170', '47.52.194.186', '39.104.53.226','119.147.144.162']:
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
        public.writeFile(self.app_path + "user.json", json.dumps(self.user_info))
        public.writeFile(self.app_path_p + "user.json", json.dumps(self.user_info))
        public.ExecShell("rm -rf %stoken.pl" % self.app_path)
        public.ExecShell("rm -rf %stoken.pl" % self.app_path_p)
        return public.returnMsg(True, '绑定成功')

    # 小程序功能入口
    def app_entrance(self, get):
        models = {'task_manager':u'宝塔任务管理器','btwaf':u'宝塔网站防火墙'}
        model_title = u'微信小程序';
        model = get.model
        if 'mod_name' in get: 
            get.name = get.mod_name;
            model = get.mod_name;
        if get.model in models: model_title = models[model]
        if not self.__check_end(model): return public.returnMsg(False,'[' + model_title + ']插件未购买或已到期');
        if get.action in ['loadInfo']:
            return monitorModule().getInfo(get)
        
        if 'mod_action' in get: get.action = get.mod_action;
        if 'mod_s' in get: get.s = get.mod_s;
        if 'mod_fun' in get: get.fun = get.mod_fun;
        app_module = __import__(get.model)
        if sys.version_info[0] == 3:
            from importlib import reload
        reload(app_module)
        result = eval('app_module.' + get.model + '().' + get.action+'(get)')
        return result
    
    def __check_end(self,model):
        if 'vip' in session: return True;
        #if public.readFile('/www/server/panel/class/common.py').find('checkSafe') != -1: return True;
        tmp = json.loads(public.readFile(self.app_path_p + 'product_bay.pl'))
        if not tmp: return False;
        product_bay = tmp['data']
        models = {'task_manager':u'宝塔任务管理器','btwaf':u'宝塔网站防火墙'}
        if model in models: return self.__is_end(product_bay, models[model])
        return self.__is_end(product_bay,u'微信小程序')
    
    def __is_end(self,product_bay,model_title):
        day_time = time.time()
        for v in product_bay:
            if v['product'] == model_title:
                if day_time <= v['endtime'] and v['state'] == 1: return True
        return False

    def get_config(self, model, action):
        conf = {
            "data": ['getData', 'ToBackup', 'DelBackup'],
            "system": ['GetLoadAverage', 'GetSystemTotal', 'GetNetWork', 'GetAllInfo'],
            "panelSite": ['AddDomain', 'DelDomain', 'DelBackup', 'HttpToHttps', 'CloseToHttps'],
            "panelWaf": ['AddAcceptPort', 'DelAcceptPort', 'SetSshStatus', 'SetSshPort', 'SetPing']
        }
        if model not in conf.keys():
            return False
        if not action in conf[model]:
            return False
        return True

    def get_safe_log(self):
        get = {
            'page': 1,
            'count': 10
        }
        print(get['page'] - 1) * get['count'], get['count']
        data = public.M('logs').limit('%s, %s' % (
            (get['page'] - 1) * get['count'], get['count'])).select()
        return data


if __name__ == '__main__':
    app = monitorModule()

    class get():
        stype = '-1'
        start = '2017-10-05'
        end = '2018-03-01'
    res = app.getInfo(get)
    print(res)
