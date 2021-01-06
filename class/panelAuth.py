#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2019 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# AUTH验证接口
#------------------------------

import public,time,json,os
from BTPanel import session,cache

class panelAuth:
    __product_list_path = 'data/product_list.pl'
    __product_bay_path = 'data/product_bay.pl'
    __product_id = '100000011'
    
    def create_serverid(self,get):
        try:
            userPath = 'data/userInfo.json'
            if not os.path.exists(userPath): return public.returnMsg(False,'请先登陆宝塔官网用户')
            tmp = public.readFile(userPath)
            if len(tmp) < 2: tmp = '{}'
            data = json.loads(tmp)
            if not data: return public.returnMsg(False,'请先登陆宝塔官网用户')
            if not 'serverid' in data:
                s1 = self.get_mac_address() + self.get_hostname()
                s2 = self.get_cpuname()
                serverid = public.md5(s1) + public.md5(s2)
                data['serverid'] = serverid
                public.writeFile(userPath,json.dumps(data))
            return data
        except: return public.returnMsg(False,'请先登陆宝塔官网用户')


    def create_plugin_other_order(self,get):
        pdata = self.create_serverid(get)
        pdata['pid'] = get.pid
        pdata['cycle'] = get.cycle
        p_url = public.GetConfigValue('home') + '/api/Pluginother/create_order'
        if get.type == '1':
            pdata['renew'] = 1
            p_url = public.GetConfigValue('home') + '/api/Pluginother/renew_order'
        return json.loads(public.httpPost(p_url,pdata))

    def get_order_stat(self,get):
        pdata = self.create_serverid(get)
        pdata['order_id'] = get.oid
        p_url = public.GetConfigValue('home') + '/api/Pluginother/order_stat'
        if get.type == '1':  p_url = public.GetConfigValue('home') + '/api/Pluginother/re_order_stat'
        return json.loads(public.httpPost(p_url,pdata))
    
    def check_serverid(self,get):
        if get.serverid != self.create_serverid(get): return False
        return True
    
    def get_plugin_price(self,get):
        try:
            userPath = 'data/userInfo.json'
            if not 'pluginName' in get: return public.returnMsg(False,'参数错误!')
            if not os.path.exists(userPath): return public.returnMsg(False,'请先登陆宝塔官网帐号!')
            params = {}
            params['pid'] = self.get_plugin_info(get.pluginName)['id']
            #params['ajax2'] = '1';
            data = self.send_cloud('get_product_discount', params)
            return data
        except:
            del(session['get_product_list'])
            return public.returnMsg(False,'正在同步信息，请重试!' + public.get_error_info())
    
    def get_plugin_info(self,pluginName):
        data = self.get_business_plugin(None)
        if not data: return None
        for d in data:
            if d['name'] == pluginName: return d
        return None
    
    def get_plugin_list(self,get):
        try:
            if not session.get('get_product_bay') or not os.path.exists(self.__product_bay_path):
                data = self.send_cloud('get_order_list_byuser', {})
                if data: public.writeFile(self.__product_bay_path,json.dumps(data))
                session['get_product_bay'] = True
            data = json.loads(public.readFile(self.__product_bay_path))
            return data
        except: return None
    
    # def get_buy_code(self,get):
    #     params = {}
    #     params['pid'] = get.pid
    #     params['cycle'] = get.cycle
    #     data = self.send_cloud('create_order', params)
    #     if not data: return public.returnMsg(False,'连接服务器失败!')
    #     return data

    def get_buy_code(self, get):
        """
        获取支付二维码
        """
        params = {}
        params['pid'] = get.pid
        params['cycle'] = get.cycle
        if 'source' in get: params['source'] = get.source


        key = '{}_{}_get_buy_code'.format(params['pid'], params['cycle'])
        data = cache.get(key)
        if data: return data

        data = self.send_cloud('create_order', params)
        if not data: return public.returnMsg(False, '连接服务器失败!')
        cache.set(key, data, 120)
        cache.set('{}_buy_code_id'.format(data['data']['oid']), key, 120)
        return data

    # def check_pay_status(self,get):
    #     params = {}
    #     params['id'] = get.id
    #     data = self.send_cloud('check_product_pays', params)
    #     if not data: return public.returnMsg(False,'连接服务器失败!')
    #     if data['status'] == True:
    #         self.flush_pay_status(get)
    #         if 'get_product_bay' in session: del(session['get_product_bay'])
    #     return data

    def check_pay_status(self,get):
        """
        检查制服状态
        @get.id 支付id
        """
        params = {}
        params['id'] = get.id
        data = self.send_cloud('check_product_pays', params)
        if not data: return public.returnMsg(False,'连接服务器失败!')
        if data['status'] == True:
            self.flush_pay_status(get)
            if 'get_product_bay' in session: del(session['get_product_bay'])

            buy_oid = '_buy_code_id'.format(params['id'])
            buy_code_key = cache.get(buy_oid)
            if buy_code_key:
                cache.delete(buy_code_key)
                cache.delete(buy_oid)
        return data
    
    def flush_pay_status(self,get):
        if 'get_product_bay' in session: del(session['get_product_bay'])
        data = self.get_plugin_list(get)
        if not data: return public.returnMsg(False,'连接服务器失败!')
        return public.returnMsg(True,'状态刷新成功!')
    
    def get_renew_code(self):
        pass
    
    def check_renew_code(self):
        pass
    
    def get_business_plugin(self,get):
        try:
            if not session.get('get_product_list') or not os.path.exists(self.__product_list_path):
                data = self.send_cloud('get_product_list', {})
                if data: public.writeFile(self.__product_list_path,json.dumps(data))
                session['get_product_list'] = True
            data = json.loads(public.readFile(self.__product_list_path))
            return data
        except: return None
    
    def get_ad_list(self):
        pass
    
    def check_plugin_end(self):
        pass
    
    def get_re_order_status_plugin(self,get):
        params = {}
        params['pid'] = getattr(get,'pid',0)
        data = self.send_cloud('get_re_order_status', params)
        if not data: return public.returnMsg(False,'连接服务器失败!')
        if data['status'] == True:
            self.flush_pay_status(get)
            if 'get_product_bay' in session: del(session['get_product_bay'])
        return data
    
    def get_voucher_plugin(self,get):
        params = {}
        params['pid'] = getattr(get,'pid',0)
        params['status'] = '0'
        data = self.send_cloud('get_voucher', params)
        if not data: return []
        return data
    
    def create_order_voucher_plugin(self,get):
        params = {}
        params['pid'] = getattr(get,'pid',0)
        params['code'] = getattr(get,'code',0)
        data = self.send_cloud('create_order_voucher', params)
        if not data: return public.returnMsg(False,'连接服务器失败!')
        if data['status'] == True:
            self.flush_pay_status(get)
            if 'get_product_bay' in session: del(session['get_product_bay'])
        return data
    
    
    def send_cloud(self,module,params):
        try:
            cloudURL = 'http://www.bt.cn/api/Plugin/'
            userInfo = self.create_serverid(None)
            params['os'] = 'Linux'
            if 'status' in userInfo:
                params['uid'] = 0
                params['serverid'] = ''
            else:
                params['uid'] = userInfo['uid']
                params['serverid'] = userInfo['serverid']
            result = public.httpPost(cloudURL + module,params)
            result = json.loads(result.strip())
            if not result: return None
            return result
        except: return None
        
    def send_cloud_pro(self,module,params):
        try:
            cloudURL = 'http://www.bt.cn/api/invite/'
            userInfo = self.create_serverid(None)
            params['os'] = 'Linux'
            if 'status' in userInfo:
                params['uid'] = 0
                params['serverid'] = ''
            else:
                params['uid'] = userInfo['uid']
                params['serverid'] = userInfo['serverid']
            result = public.httpPost(cloudURL + module,params)
            
            result = json.loads(result)
            if not result: return None
            return result
        except: return None
    
    def get_voucher(self,get):
        params = {}
        params['product_id'] = self.__product_id
        params['status'] = '0'
        data = self.send_cloud_pro('get_voucher', params)
        return data
    
    def get_order_status(self,get):
        params = {}
        data = self.send_cloud_pro('get_order_status', params)
        return data
        
    
    def get_product_discount_by(self,get):
        params = {}
        data = self.send_cloud_pro('get_product_discount_by', params)
        return data
    
    def get_re_order_status(self,get):
        params = {}
        data = self.send_cloud_pro('get_re_order_status', params)
        return data
    
    def create_order_voucher(self,get):
        code = getattr(get,'code','1')
        params = {}
        params['code'] = code
        data = self.send_cloud_pro('create_order_voucher', params)
        return data
    
    def create_order(self,get):
        cycle = getattr(get,'cycle','1')
        params = {}
        params['cycle'] = cycle
        data = self.send_cloud_pro('create_order', params)
        return data
    
    def get_mac_address(self):
        import uuid
        mac=uuid.UUID(int = uuid.getnode()).hex[-12:]
        return ":".join([mac[e:e+2] for e in range(0,11,2)])
    
    def get_hostname(self):
        import socket
        return socket.getfqdn(socket.gethostname())
    
    def get_cpuname(self):
        return public.ExecShell("cat /proc/cpuinfo|grep 'model name'|cut -d : -f2")[0].strip()
    
    