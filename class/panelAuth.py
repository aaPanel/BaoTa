# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2019 宝塔软件(http:#bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# -------------------------------------------------------------------

# ------------------------------
# AUTH验证接口
# ------------------------------

from urllib import request
import public, time, json, os, re

# from pluginAuth import Plugin
try:
    from BTPanel import session, cache
except:
    pass


class panelAuth:
    __request_url = None
    __product_list_path = 'data/product_list.pl'
    __product_bay_path = 'data/product_bay.pl'
    __product_id = '100000011'

    def create_serverid(self, get):
        default_msg = '请先登陆宝塔官网用户'
        try:
            userPath = 'data/userInfo.json'
            if not os.path.exists(userPath): 
                return public.get_user_info()
                # return public.returnMsg(False, default_msg)
            tmp = public.readFile(userPath)
            if len(tmp) < 2: tmp = '{}'
            data = json.loads(tmp)
            if not data: return public.returnMsg(False, default_msg)
            if not 'serverid' in data:
                data['serverid'] = self.get_serverid()
                public.writeFile(userPath, json.dumps(data))
            return data
        except:
            return public.returnMsg(False, default_msg)

    def get_serverid(self, force=False):
        '''
            @name 重新生成serverid
            @author hwliang<2021-06-22>
            @return string
        '''
        serverid_file = 'data/sid.pl'
        if os.path.exists(serverid_file) and not force:
            serverid = public.readFile(serverid_file)
            if re.match("^\w{64}$", serverid): return serverid
        s1 = self.get_mac_address() + self.get_hostname()
        s2 = self.get_cpuname()
        serverid = public.md5(s1) + public.md5(s2)
        public.writeFile(serverid_file, serverid)
        return serverid

    def get_wx_order_status(self, get):
        """
        检查支付状态
        @get.wxoid 支付id
        """
        params = {}
        params['wxoid'] = get.wxoid
        if 'kf' in get: params['kf'] = get.kf
        if "py_type" in get: params['py_type'] = get.py_type

        data = self.send_cloud('check_order_pay_status', params)
        if not data: return self.res_request_error()
        if data['status'] == True:
            self.flush_pay_status(get)
            if 'get_product_bay' in session: del (session['get_product_bay'])

            buy_oid = '_buy_code_id'.format(params['wxoid'])
            buy_code_key = cache.get(buy_oid)
            if buy_code_key:
                cache.delete(buy_code_key)
                cache.delete(buy_oid)
        return data

    def get_apply_copon(self, get):
        """
        获取优惠券
        @get.coupon 优惠券
        """
        params = {}
        if hasattr(get,'type'): params['type'] = get.type
        data = self.send_cloud('apply_coupon', params)
        cache.delete('get_coupon_list')

        if not data: self.res_request_error()
        return data

    def get_ignore_time(self, get):
        """
        获取忽略时间
        @get.coupon 优惠券
        """
        try:
            limit = int(public.readFile('data/ignore_coupon_time.pl'))
        except:
            limit = 0

        if limit == -100 or limit > time.time():
            return 1
        return 0

    def _get_coupon_list_no_cache(self,get):
        """
        获取优惠券-无缓存
        @get.coupon 优惠券
        """
        params = {}
        if hasattr(get,'type'): params['type'] = get.type
        if hasattr(get,'pid'): params['pid'] = get.pid
        data = self.send_cloud('get_coupon_list', params)

        if not data:
            if type(data) == list:
                return []
            return self.res_request_error()
        return data

    def get_coupon_list(self,get):
        """
        获取优惠券
        @get.coupon 优惠券
        """
        #用户是否忽略
        if self.get_ignore_time(get):
            return []

        if not hasattr(get,'type') or get.type in (5, "5"):
            return self._get_coupon_list_no_cache(get)

        skey = 'get_coupon_list'
        data = cache.get(skey)
        if type(data) == list: return data

        params = {}
        if hasattr(get,'type'): params['type'] = get.type
        if hasattr(get,'pid'): params['pid'] = get.pid
        data = self.send_cloud('get_coupon_list', params)

        if not data:
            if type(data) == list:
                cache.set(skey,data,600)
                return []
            return self.res_request_error()
        cache.set(skey,data,600)
        return data

    def ignore_coupon_time(self, get):
        """
        获取优惠券
        @get.coupon 优惠券
        @get.limit_time 限制时间  永久 -100
        """
        if not hasattr(get, 'limit_time')or not get.limit_time: return public.returnMsg(False, '缺少参数limit_time或参数不能为空!')
        limit_time = int(get.limit_time)
        if limit_time < time.time() and limit_time > 0:
            return public.returnMsg(False, '时间不能小于当前时间!')

        public.writeFile('data/ignore_coupon_time.pl', str(limit_time))

        msg = '忽略成功,以后将不会显示优惠券信息.'
        if limit_time > 0: msg = '忽略成功,【{}】 之前将不再给你显示优惠券信息.'.format(public.format_date(times=limit_time))
        return public.returnMsg(True, msg)

    def create_plugin_other_order(self, get):
        if not hasattr(get, 'pid') or not hasattr(get, 'cycle'): return public.returnMsg(False, '参数错误!')
        pdata = self.create_serverid(get)
        pdata['pid'] = get.pid
        pdata['cycle'] = get.cycle
        p_url = public.GetConfigValue('home') + '/api/Pluginother/create_order'
        if get.type == '1':
            pdata['renew'] = 1
            p_url = public.GetConfigValue('home') + '/api/Pluginother/renew_order'
        try:
            res = public.httpPost(p_url, pdata)
            return json.loads(res)
        except:
            if pdata['uid'] == -1:
                return public.returnMsg(False, '请先绑定宝塔官网帐号!')
            raise public.PanelError('{}\n{}\n连接官网失败，请检查网络状况!'.format(p_url, res))

    def create_plugin_with_credit(self, get):
        if not hasattr(get, 'pid') or not hasattr(get, 'cycle'): return public.returnMsg(False, '参数错误!')
        pdata = self.create_serverid(get)
        pdata['pid'] = get.pid
        pdata['cycle'] = get.cycle
        p_url = public.GetConfigValue('home') + '/api/v2/order/product/create_plugin_with_credit'
        if get.type == '1':
            pdata['renew'] = 1
            p_url = public.GetConfigValue('home') + '/api/v2/order/product/create_plugin_with_credit'
        try:
            res = public.httpPost(p_url, pdata)
            res = json.loads(res)

            return {'status': res['success'], 'msg': res['res']}
        except:
            if pdata['uid'] == -1:
                return public.returnMsg(False, '请先绑定宝塔官网帐号!')
            raise public.PanelError('{}\n{}\n连接官网失败，请检查网络状况!'.format(p_url, res))

    def get_order_stat(self, get):
        pdata = self.create_serverid(get)
        pdata['order_id'] = get.oid
        p_url = public.GetConfigValue('home') + '/api/Pluginother/order_stat'
        if get.type == '1':  p_url = public.GetConfigValue('home') + '/api/Pluginother/re_order_stat'
        return json.loads(public.httpPost(p_url, pdata))

    def check_serverid(self, get):
        if get.serverid != self.create_serverid(get): return False
        return True

    def get_plugin_price(self,get):
        """
        @name 获取插件价格
        @author cjxin<2022-07-28>
        @param get.pid 插件id
        @param get.pluginName 插件名称
        @return dict
        """
        try:
            userPath = 'data/userInfo.json'
            if not os.path.exists(userPath):
                return public.returnMsg(False,'请先登陆宝塔官网帐号!')

            pid = 0
            if 'pid' in get: pid = get.pid
            if not pid:
                if not 'pluginName' in get:
                    return public.returnMsg(False,'参数错误!')
                pid = self.get_plugin_info(get.pluginName)['id']

            if not pid: return public.returnMsg(False,'参数错误!')

            skey = 'get_plugin_price_{}'.format(pid)
            data = cache.get(skey)
            if data:
                return data

            cache_data = {}
            plugin_file = '{}/config/plugin_price.json'.format(public.get_panel_path())
            try:
                 cache_data =  json.loads(public.readFile(plugin_file))
            except: pass

            params = {}
            params['pid'] = pid
            data = self.send_cloud('get_product_discount', params)
            if not data:
                if pid in cache_data:
                    return cache_data[pid]
                return public.returnMsg(False,'获取价格失败!')

            cache_data[pid] = data
            public.writeFile(plugin_file,json.dumps(cache_data))

            cache.set(skey,data,300)
            return data
        except:
            del(session['get_product_list'])
            return public.returnMsg(False,'正在同步信息，请重试!' + public.get_error_info())

    def get_plugin_info(self, pluginName):
        data = self.get_business_plugin(None)
        if not data: return None
        for d in data:
            if d['name'] == pluginName: return d
        return None

    def get_plugin_list(self, get):
        try:
            import PluginLoader
            PluginLoader.get_plugin_list(1)
            if not session.get('get_product_bay') or not os.path.exists(self.__product_bay_path):
                data = self.send_cloud('get_order_list_byuser', {})
                if data: public.writeFile(self.__product_bay_path, json.dumps(data))
                session['get_product_bay'] = True
            data = json.loads(public.readFile(self.__product_bay_path))
            return data
        except:
            return None

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
        if not hasattr(get, 'pid'):
            return public.returnMsg(False, '缺少参数pid')
        if not hasattr(get, 'cycle'):
            return public.returnMsg(False, '缺少参数cycle')

        params = {}
        params['pid'] = get.pid
        params['cycle'] = get.cycle
        params['num'] = 1  # 购买数量
        params['version'] = public.version()
        if 'num' in get: params['num'] = get.num
        if 'source' in get: params['source'] = get.source
        if 'coupon' in get: params['coupon'] = get.coupon
        regain = get.get("regain/d", 0)

        try:
            params["mac"] = self.get_mac_address()
            data = self.send_cloud('create_order_v1', params)
            if data.get("data", {}).get("code", 0) == 1000:
                msg = "检测到当前服务器为镜像克隆环境，授权信息不可用，请解绑当前账号，并重新绑定获取授权信息"
                data["msg"] = msg
                data["data"]["msg"] = msg
                return  data
            get.get_ali_msg = get.get("get_ali_msg", 0)
            if int(get.get_ali_msg) == 1 or float(data["price"]) >= 6000:
                if data["ali_msg"] == "" or regain == 1:
                    ali_params = {"wxoid": data["data"]["wxoid"], "regain": regain}
                    ali_data = self.send_cloud('get_order_ali', ali_params)
                    data["ali_msg"] = ali_data["ali_msg"]
        except:
            data = self.send_cloud('create_order', params)
        if not data: return self.res_request_error()
        if 'is_coupon' in data:
            if self.get_ignore_time(get):
                data['is_coupon'] = []
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

    def check_pay_status(self, get):
        """
        检查支付状态
        @get.id 支付id
        """
        params = {}
        params['id'] = get.id
        data = self.send_cloud('check_product_pays', params)
        if not data: return self.res_request_error()
        if data['status'] == True:
            self.flush_pay_status(get)
            if 'get_product_bay' in session: del (session['get_product_bay'])

            buy_oid = '_buy_code_id'.format(params['id'])
            buy_code_key = cache.get(buy_oid)
            if buy_code_key:
                cache.delete(buy_code_key)
                cache.delete(buy_oid)
        return data

    def flush_pay_status(self, get):
        if 'get_product_bay' in session: del (session['get_product_bay'])
        data = self.get_plugin_list(get)
        if not data: return self.res_request_error()
        return public.returnMsg(True, '状态刷新成功!')

    def get_renew_code(self):
        pass

    def check_renew_code(self):
        pass

    def get_business_plugin(self, get):
        try:
            if not session.get('get_product_list') or not os.path.exists(self.__product_list_path):
                data = self.send_cloud('get_product_list', {})
                if data: public.writeFile(self.__product_list_path, json.dumps(data))
                session['get_product_list'] = True
            data = json.loads(public.readFile(self.__product_list_path))
            return data
        except:
            return None

    def get_ad_list(self):
        pass

    def check_plugin_end(self):
        pass

    def get_coupons(self, get):
        """
        @name 获取用户抵扣卷列表
        @param uid 用户id
        """
        params = {}
        data = self.send_cloud_v2('v2/user/get_coupons', params)
        return data

    def get_last_paid_time(self, get):
        """
        @name 获取用户抵扣卷列表
        @param uid 用户id
        """
        if not hasattr(get, 'pid'): return public.returnMsg(False, '缺少参数pid')
        params = {}
        params['product_id'] = int(get.pid)
        data = self.send_cloud_v2('v2/order/product/get_last_paid_time', params)
        return data

    def get_credits(self, get):
        """
        @获取用户余额
        @param uid 用户id
        """
        params = {}
        data = self.send_cloud_v2('v2/user/get_credits', params)
        return data

    def create_with_credit_by_panel(self, get):
        """
        @name 使用余额购买
        @param uid 用户id
        @param product_id 产品id
        @param cycle 购买周期
        @param num 购买数量
        @param coupon 优惠券id
        """
        params = {}
        params['product_id'] = int(get.pid)
        params['cycle'] = get.cycle
        params['num'] = 1  # 购买数量
        if 'num' in get: params['num'] = get.num
        if 'coupon' in get: params['coupon'] = get.coupon

        data = self.send_cloud_v2('v2/order/product/create_with_credit_by_panel', params)
        return data

    def rest_unbind_count(self, get):
        """
        @name 获取当前订单可解绑次数
        """
        params = {}
        data = self.send_cloud_v2('v2/authorization_v1/rest_unbind_count', params)
        return data

    def unbind_authorization(self, get):
        """
        @name 解绑专业版/企业版
        """
        params = {}
        data = self.send_cloud_v2('v2/authorization_v1/unbind_authorization', params)
        return data

    def get_pay_unbind_count(self, get):
        """
        @name 购买解绑次数
        """
        params = {}
        params['product_id'] = int(get.pid)
        data = self.send_cloud_v2('v2/order/unbind_count/create', params)
        return data

    def get_re_order_status_plugin(self, get):
        params = {}
        params['pid'] = getattr(get, 'pid', 0)
        data = self.send_cloud('get_re_order_status', params)
        if not data: return self.res_request_error()
        if data['status'] == True:
            self.flush_pay_status(get)
            if 'get_product_bay' in session: del (session['get_product_bay'])
        return data

    def get_voucher_plugin(self, get):
        params = {}
        params['pid'] = getattr(get, 'pid', 0)
        params['status'] = '0'
        data = self.send_cloud('get_voucher', params)
        if not data: return []
        return data

    def get_all_voucher_plugin(self, get):
        """
        @name 获取所有可用的优惠券
        @param pid 产品id, 100000000表示获取所有
        """
        params = {}
        params['pid'] = getattr(get, 'pid', 0)
        params['status'] = '0'
        data = self.send_cloud('get_all_voucher', params)
        if not data: return []
        return data

    def create_order_voucher_plugin(self, get):
        params = {}
        params['pid'] = getattr(get, 'pid', 0)
        params['code'] = getattr(get, 'code', 0)
        data = self.send_cloud('create_order_voucher', params)
        if not data: return self.res_request_error()
        if data['status'] == True:
            self.flush_pay_status(get)
            if 'get_product_bay' in session: del (session['get_product_bay'])
        return data

    def get_auth_bind_num(self, get):
      """
      @name 获取授权绑定次数
      """
      params = {}
      params['pid'] = getattr(get, 'pid', 0)
      data = self.send_cloud('get_auth_unbind_count', params)
      if not data: return self.res_request_error()
      return data

    def get_voucher(self, get):
        params = {}
        params['product_id'] = self.__product_id
        params['status'] = '0'
        data = self.send_cloud_pro('get_voucher', params)
        return data

    def get_order_status(self, get):
        params = {}
        data = self.send_cloud_pro('get_order_status', params)
        return data

    def get_product_discount_by(self, get):
        params = {}
        data = self.send_cloud_pro('get_product_discount_by', params)
        return data

    def get_re_order_status(self, get):
        params = {}
        data = self.send_cloud_pro('get_re_order_status', params)
        return data

    def create_order_voucher(self, get):
        code = getattr(get, 'code', '1')
        params = {}
        params['code'] = code
        data = self.send_cloud_pro('create_order_voucher', params)
        return data

    def create_order(self, get):
        cycle = getattr(get, 'cycle', '1')
        params = {}
        params['cycle'] = cycle
        data = self.send_cloud_pro('create_order', params)
        return data

    def get_mac_address(self):
        import uuid
        mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
        return ":".join([mac[e:e + 2] for e in range(0, 11, 2)])

    def get_hostname(self):
        import socket
        try:
            hostname = socket.getfqdn(socket.gethostname())
        except:
            # 尝试通过文件获取
            hostname_file = '/etc/hostname'
            proc_hostname_file = '/proc/sys/kernel/hostname'
            if os.path.exists(proc_hostname_file):
                hostname = public.readFile(proc_hostname_file).strip()
            elif os.path.exists(hostname_file):
                hostname = public.readFile(hostname_file).strip()
            else:
                # 通过命令获取
                hostname = public.ExecShell("hostname")[0].strip()

        # 如果都获取不到，则使用默认值
        if not hostname:
            hostname = 'localhost'
        return hostname

    def get_cpuname(self):
        return public.ExecShell("cat /proc/cpuinfo|grep 'model name'|cut -d : -f2")[0].strip()

    def get_plugin_remarks(self,get):
        """
        @name 获取插件描述，用于支付页面
        """
        ikey = 'plugin_remarks'
        remarks_file = '{}/config/plugin_remarks.json'.format(public.get_panel_path())
        if ikey in session:
            return session.get(ikey)
        data = self.send_cloud_wpanel('get_plugin_remarks',{})
        if not data:
            try:
                data = json.loads(public.readFile(remarks_file))
            except:
                return self.res_request_error()
        session[ikey] = data
        public.writeFile(remarks_file,json.dumps(data))
        return data

    def set_user_adviser(self, get):
        params = {}
        params['status'] = get.status
        data = self.send_cloud_wpanel('set_user_adviser', params)
        if not data:
            return self.res_request_error()
        return data

    """
    @官网连接失败错误URL
    """

    def res_request_error(self):
        return public.returnMsg(False, '接口请求失败（{}）!'.format(self.__request_url))

    """
    @name 统一请求接口
    @param url 返回URL不是www.bt.cn，修改config/config.json的home字段
    """

    def request_post(self, url, params):

        self.__request_url = public.get_home_node(url)
        try:
            try:
                result = public.httpPost(url, params)
                if result == False:
                    raise Exception('接口请求失败（{}）!'.format(self.__request_url))
            except Exception as ex:
                raise public.error_conn_cloud(str(ex))

            result = json.loads(result.strip())
            if not result:
                if type(result) == list:
                    return []
                return None
            return result
        except:
            return None

    def send_cloud_wpanel(self, module, params):

        cloudURL = public.GetConfigValue('home') + '/api/panel/'
        userInfo = self.create_serverid(None)
        if 'status' in userInfo:
            params['uid'] = 0
            params['serverid'] = ''
        else:
            params['uid'] = userInfo['uid']
            params['serverid'] = userInfo['serverid']
        params['os'] = 'Linux'
        return self.request_post(cloudURL + module, params)

    def send_cloud_v2(self, module, params):

        cloudURL = 'https://www.bt.cn/api/'
        userInfo = self.create_serverid(None);
        if 'status' in userInfo:
            params['uid'] = 0
            params['serverid'] = ''
        else:
            params['uid'] = userInfo['uid']
            params['serverid'] = userInfo['serverid']
            params['access_key'] = userInfo['access_key']
        params['os'] = 'Linux'
        return self.request_post(cloudURL + module, params)

    def send_cloud(self, module, params):

        cloudURL = public.GetConfigValue('home') + '/api/Plugin/'
        userInfo = self.create_serverid(None)
        params['os'] = 'Linux'
        if 'status' in userInfo:
            params['uid'] = 0
            params['serverid'] = ''
        else:
            params['uid'] = userInfo['uid']
            params['serverid'] = userInfo['serverid']
            params['access_key'] = userInfo['access_key']

        return self.request_post(cloudURL + module, params)

    def send_cloud_pro(self, module, params):

        cloudURL = public.GetConfigValue('home') + '/api/invite/'
        userInfo = self.create_serverid(None)
        params['os'] = 'Linux'
        if 'status' in userInfo:
            params['uid'] = 0
            params['serverid'] = ''
        else:
            params['uid'] = userInfo['uid']
            params['serverid'] = userInfo['serverid']
            params['access_key'] = userInfo['access_key']

        return self.request_post(cloudURL + module, params)


    def receive_products(self, get):
        """
        @name 领取活动产品
        @author chudong<2025-11-26>
        @param get.detail_id 详情ID
        @return dict
        """
        try:
            u = public.get_user_info()
            if not isinstance(u, dict):
                return public.returnMsg(False, '请先绑定宝塔账号')
            serverid = u.get('serverid')
            access_key = u.get('access_key')
            uid = u.get('uid')
            if not serverid or not access_key or uid is None:
                return public.returnMsg(False, '请先绑定宝塔账号')
            
            detail_id = getattr(get, 'detail_id', '')
            if not detail_id:
                return public.returnMsg(False, '参数错误')

            payload = {
                'serverid': serverid,
                'access_key': access_key,
                'uid': uid,
                'detail_id': detail_id,
                'mac': self.get_mac_address()
            }
            url = 'https://www.bt.cn/newapi/activity/panelapi/receive_products'
            res = public.httpPost(url, payload)

            if not res:
                return public.returnMsg(False, '连接服务器失败')
            try:
                result = json.loads(res)
            except:
                return public.returnMsg(False, '服务器返回数据错误')
            # 刷新软件列表状态,确保最新软件列表信息获取
            public.flush_plugin_list()
            return result
        except:
            return public.returnMsg(False, '领取失败')



    def get_free_activity_info(self, get):
        """
        @name 获取活动产品信息
        @author chudong<2025-11-26>
        @param get.activity_id 活动ID
        @return dict
        """
        try:
            u = public.get_user_info()
            if not isinstance(u, dict):
                return public.returnMsg(False, '请先绑定宝塔账号')
            serverid = u.get('serverid')
            access_key = u.get('access_key')
            uid = u.get('uid')
            if not serverid or not access_key or uid is None:
                return public.returnMsg(False, '请先绑定宝塔账号')
            
            activity_id = getattr(get, 'activity_id', 0)
            if not activity_id:
                return public.returnMsg(False, '参数错误，activity_id不能为空')

            payload = {
                'serverid': serverid,
                'access_key': access_key,
                'uid': uid,
                'activity_id': activity_id
            }
            url = 'https://www.bt.cn/newapi/activity/panelapi/get_free_activity_info'
            res = public.httpPost(url, payload)
            if not res:
                return public.returnMsg(False, '连接服务器失败')
            try:
                result = json.loads(res)
                result_detail  = result['data'][0]
            except:
                return public.returnMsg(False, '服务器返回数据错误')
            return public.returnResult(True, '获取成功', result_detail)
        except:
            return public.returnMsg(False, '领取失败')


    
