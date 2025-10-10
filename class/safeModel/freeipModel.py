#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: cjxin <cjxin@bt.cn>
#-------------------------------------------------------------------

# 免费IP库1
#------------------------------
import os,re,json,time
from safeModel.base import safeBase
import public


class main(safeBase):
    _sfile = '{}/data/free_ip_area.json'.format(public.get_panel_path())

    def __init__(self):
        try:
            self.user_info = public.get_user_info()
        except:
            self.user_info = None

    def get_ip_area(self,get):
        """
        @获取IP地址所在地
        @param get: dict/array
        """
        ips = get['ips']
        arrs,result = [],{}
        for ip in ips:arrs.append(ip)
        if len(arrs) > 0:
            data = self.__get_cloud_ip_info(arrs)
            for ip in data:
                result[ip] = data[ip]
        return result


    def __get_cloud_ip_info(self,ips):
        """
        @获取IP地址所在地
        @得判断是否是我们的用户
        @param ips:
        """
        result = {}
        try:
            '''
                @从云端获取IP地址所在地
                @param data 是否是宝塔用户,如果不是则不返回
                @param ips: IP地址
            '''
            data = {}
            data['ip'] = ','.join(ips)
            data['uid'] = self.user_info['uid']
            data["serverid"]=self.user_info["serverid"]
            #如果不是我们的用户，那么不返回数据
            res = public.httpPost('https://www.bt.cn/api/ip/info',data)
            res = json.loads(res)
            data = self.get_ip_area_cache()
            for key in res:
                info = res[key]
                if public.is_local_ip(key):
                    res[key]['city']="内网地址"
                if not res[key]['city']: continue
                if not res[key]['city'].strip() and not res[key]['continent'].strip():
                    info = {'info':'未知归属地'}
                else:
                    info['info'] = '{} {} {} {}'.format(info['carrier'],info['country'],info['province'],info['city']).strip()
                data[key] = info
                result[key] = info
            self.set_ip_area_cache(data)
        except:
            pass
        return result


    def get_ip_area_cache(self):
        """
        @获取IP地址所在地
        @param get:
        """
        data = {}
        try:
            data = json.loads(public.readFile(self._sfile))
        except:
            public.writeFile(self._sfile,json.dumps({}))
        return data

    def set_ip_area_cache(self,data):
        """
        @设置IP地址所在地
        @param data:
        """
        public.writeFile(self._sfile,json.dumps(data))
        return True