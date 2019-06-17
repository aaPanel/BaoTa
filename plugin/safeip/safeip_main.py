#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------

# +-------------------------------------------------------------------
# | 高防IP
# +-------------------------------------------------------------------
import os,sys,public,json,urllib,binascii

class safeip_main:
    __PDATA = None;
    __APIURL = 'http://www.bt.cn/api/Safeip';
    __UPATH = 'data/userInfo.json';
    __userInfo = None;

    def __init__(self):
        pdata = {}
        data = {}
        if os.path.exists(self.__UPATH):
            self.__userInfo = json.loads(public.readFile(self.__UPATH));
            if self.__userInfo:
                pdata['access_key'] = self.__userInfo['access_key'];
                data['secret_key'] = self.__userInfo['secret_key'];
        else:
            pdata['access_key'] = 'test';
            data['secret_key'] = '123456';
        pdata['data'] = data;
        self.__PDATA = pdata;

    def get_order(self,get):
        return self.send_server('get_order');

    def get_clients(self,get):
        return self.send_server('get_clients');

    #获取可用的节点列表
    def get_nodes(self,get):
        return self.send_server('get_nodes');

    #取产品列表
    def get_products(self,get):
        data = {}
        data['products'] = self.send_server('get_products');
        self.__init__()
        data['nodes'] = self.send_server('get_nodes');
        return data

    #取4层防护列表
    def get_l4_list(self,get):
        return self.send_server('l4_list')

    #取指定4层防护规则
    def get_l4_find(self,get):
        self.__PDATA['l4_id'] = get.l4_id
        return self.send_server('l4_find');

    #添加4层防护规则
    def l4_insert(self,get):
        self.__PDATA['s_ip'] = get.s_ip
        self.__PDATA['pool'] = get.pool
        self.__PDATA['s_port'] = get.s_port
        self.__PDATA['d_ip'] = get.d_ip
        self.__PDATA['d_port'] = get.d_port
        return self.send_server('l4_insert');

    #编辑4层防护规则 
    def l4_update(self,get):
        self.__PDATA['l4_id'] = get.l4_id
        self.__PDATA['pool'] = get.pool
        self.__PDATA['d_ip'] = get.d_ip
        self.__PDATA['d_port'] = get.d_port
        return self.send_server('l4_update');

    #删除4层防护规则
    def l4_delete(self,get):
        self.__PDATA['l4_id'] = get.l4_id
        return self.send_server('l4_delete');

    #取7层防护集合
    def get_l7_collection(self,get):
        return self.send_server('l7_collection');

    #取7层防护列表
    def get_l7_list(self,get):
        return self.send_server('l7_list');

    #取指定7层防护规则
    def get_l7_find(self,get):
        self.__PDATA['l7_id'] = get.l7_id
        return self.send_server('l7_find');

    #添加7层防护
    def l7_insert(self,get):
        self.__PDATA['content'] = get.content
        self.__PDATA['pool'] = get.pool
        self.__PDATA['forward_ips'] = get.forward_ips
        self.__PDATA['domain'] = get.domain
        if(int(self.__PDATA['pool']) > 1):
            self.__PDATA['public_pem'] = get.public_pem
            self.__PDATA['private_key'] = get.private_key
        return self.send_server('l7_insert');

    #修改7层防护
    def l7_update(self,get):
        self.__PDATA['l7_id'] = get.l7_id
        self.__PDATA['content'] = get.content
        self.__PDATA['pool'] = get.pool
        self.__PDATA['forward_ips'] = get.forward_ips
        self.__PDATA['domain'] = get.domain
        if(int(self.__PDATA['pool']) > 1):
            self.__PDATA['public_pem'] = get.public_pem
            self.__PDATA['private_key'] = get.private_key
        return self.send_server('l7_update');

    #删除7层防护
    def l7_delete(self,get):
        self.__PDATA['l7_id'] = get.l7_id
        return self.send_server('l7_delete');


    #取IP状态
    def ip_state(self,get):
        self.__PDATA['ip'] = get.ip
        return self.send_server('ip_state');

    #获取高防IP回源段
    def ip_source(self,get):
        return self.send_server('ip_source');

    #查询IP统计信息
    def ip_total(self,get):
        self.__PDATA['ip'] = get.ip
        return self.send_server('ip_total');

    #启动流量清洗
    def clean_open(self,get):
        self.__PDATA['ip'] = get.ip
        self.__PDATA['end_time'] = get.end_time
        return self.send_server('clean_open');

    #关闭清洗流量
    def clean_close(self,get):
        self.__PDATA['i_id'] = get.i_id
        return self.send_server('clean_close');


    #获取清洗防护实例列表
    def clean_list(self,get):
        return self.send_server('clean_list')

    #获取DDOS流量
    def ddos_stat(self,get):
        data = {}
        self.__PDATA['ip'] = get.ip
        self.__PDATA['start_time'] = get.start_time
        self.__PDATA['end_time'] = get.end_time
        data['ddos'] = self.send_server('ddos_stat')
        if not data['ddos']: data['ddos'] = [{"data": [{"pps": 0, "bps": 0, "type": "1"}, {"pps": 0, "bps": 0, "type": "3"}], "time": int(time.time()) * 1000}]
        
        self.__init__();
        data['bus'] = self.business_stat(get)
        if not data['bus']: data['bus'] = [{"data": [{"pps": 0, "bps": 0, "type": "4"}, {"pps": 0, "bps": 0, "type": "5"}], time: int(time.time()) * 1000}]
        return data

    #获取业务流量
    def business_stat(self,get):
        self.__PDATA['ip'] = get.ip
        self.__PDATA['start_time'] = get.start_time
        self.__PDATA['end_time'] = get.end_time
        return self.send_server('business_stat')

    #获取当日流量峰值
    def max_stat(self,get):
        self.__PDATA['ip'] = get.ip
        return self.send_server('max_stat')

    #获取攻击事件信息
    def attack_list(self,get):
        self.__PDATA['ip'] = get.ip
        self.__PDATA['start_time'] = get.start_time
        self.__PDATA['end_time'] = get.end_time
        return self.send_server('attack_list')

    #创建订单
    def create_order(self,get):
        self.__PDATA['cycle'] = get.cycle
        self.__PDATA['pid'] = get.pid
        self.__PDATA['isp_id'] = get.isp_id
        return self.send_server('create_order')

    #检查订单是否支付成功
    def order_stat(self,get):
        self.__PDATA['order_id'] = get.order_id
        return self.send_server('order_stat')

    #创建续费订单
    def renew_order(self,get):
        self.__PDATA['cycle'] = get.cycle
        self.__PDATA['order_id'] = get.order_id
        return self.send_server('renew_order')

    #检查续费状态
    def renew_stat(self,get):
        self.__PDATA['order_id'] = get.order_id
        return self.send_server('renew_stat')

    #发送请求
    def send_server(self,action):
        if self.__PDATA['access_key'] == 'test': return public.returnMsg(False,'请先绑定宝塔用户!');
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data']);
        result = public.httpPost(self.__APIURL + '/' + action,self.__PDATA);
        try:
            return json.loads(result);
        except: return result

    

    #加密数据
    def De_Code(self,data):
        if sys.version_info[0] == 2:
            pdata = urllib.urlencode(data);
        else:
            #import urllib.parse
            pdata = urllib.parse.urlencode(data);
            if type(pdata) == str: pdata = pdata.encode('utf-8')
        return binascii.hexlify(pdata);
    
    #解密数据
    def En_Code(self,data):
        if sys.version_info[0] == 2:
            result = urllib.unquote(binascii.unhexlify(data));
        else:
            if type(data) == str: data = data.encode('utf-8')
            tmp = binascii.unhexlify(data)
            if type(tmp) != str: tmp = tmp.decode('utf-8')
            result = urllib.parse.unquote(tmp)

        if type(result) != str: result = result.decode('utf-8')
        return json.loads(result);