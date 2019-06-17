# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 6.x
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 梁凯强<1249648969@qq.com>
# +-------------------------------------------------------------------

# +--------------------------------------------------------------------
# |   微架构 - 命令群发
# +--------------------------------------------------------------------
import re, sys, os, public, time, json
from inc.coll_db import M, write_log
from BTPanel import session, redirect, cache
import requests
import gevent
import gevent.pool
import sys
from datetime import datetime
import uuid
import hmac
from hashlib import sha1
import base64
import urllib

class coll_shell:
    __host_data = None
    __result_list = []
    __shell_code = None
    def __init__(self):
        pass
    
    # 返回组名
    def get_group_name(self,get):
        sql = M('server_group').get()
        return sql


    #获取远程机器的命令执行记录
    def get_host_history(self,get):
        sid=get.sid
        sid_info=self.get_host_info(sid)
        if len(sid_info) ==1:
            public_params = {"Format": "json",
                                "SignatureMethod": "HMAC-SHA1",
                                "Timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                                "SignatureNonce": str(uuid.uuid1()),
                                "AccessKeyId": sid_info[0][6]}
                # 接口的私有参数
            private_params = {"rows": 10}
            paramsdata = dict(public_params, **private_params)
            signature = self._sign(sid_info[0][-1], public_params)
            paramsdata['signature'] = signature
            url = sid_info[0][5] + '/agent/get_shell_history.json'
            ret = public.HttpPost(url, paramsdata, timeout=3)
            if re.search('data',ret):
                return ret
            else:
                return public.returnMsg(False,'连接失败')
        else:
            return public.returnMsg(False,'不存在')

    #获取所有的命令执行记录
    def get_history(self, get):
        sql = M('history_shell')
        if not 'p' in get: get.p = 1
        count = sql.count()
        data = public.get_page(count,int(get.p))
        data['data'] = sql.limit(data['shift']+',' + data['row']).field('id,username,time,shell,data,error,sid,gid').select()
        return data

    #查看常用命令
    def get_used_shell(self, get):
        sql = M('used_shell')
        if not 'p' in get: get.p = 1
        count = sql.count()
        data = public.get_page(count,get.p)
        data['data'] = sql.limit(data['shift']+',' + data['row']).field('id,time,username,shell,ps').select()
        return data

    #添加常用命令
    def add_used_shell(self,get):
        if not 'shell' in get:public.returnMsg(False,'参数为shell')
        sql = M('used_shell').where("shell=?", (get.shell,)).select()
        if sql:return public.returnMsg(False,'已经存在')
        data={"time":datetime.now().strftime("%Y-%m-%d:%H:%M:%S"),"username":session['coll_username'],"shell":get.shell,"ps":get.ps}
        M('used_shell').insert(data)
        return public.returnMsg(True,'添加成功')

    # 删除常用命令
    def del_used_shell(self,get):
        if not 'id' in get:public.returnMsg(False,'参数为id')
        sql = M('used_shell').where("id=?", (get.id,)).delete()
        return public.returnMsg(True,'删除成功')

    #删除命令记录
    def del_history(self,get):
        ret = M('history_shell').delete()
        return public.returnMsg(True,'删除成功')

    #查看所有机器
    def get_host(self, get):
        sql = M('server_list')
        if not 'p' in get: get.p = 1
        count = sql.count()
        data = public.get_page(count,get.p)
        data['data'] = sql.limit(data['shift']+',' + data['row']).field('sid,uid,gid,address,config,panel,AccessKeyId,state,ps,area,addtime,sort,AccessToekn').select()
        return data

    # 查看组里面的机器
    def get_group_list(self, gid):
        ret = M('server_list').where("gid=?", (gid,)).select()
        return ret

    # 查看当前机器的所有信息
    def get_host_info(self, sid):
        ret = M('server_list').where("sid=?", (sid,)).select()
        return ret

    #判断是否是数字
    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            pass
        try:
            import unicodedata
            unicodedata.numeric(s)
            return True
        except (TypeError, ValueError):
            pass
        return False

    # 汇总机器
    def host_count(self, get):
        sid_list = get.sid
        gid_list = get.gid
        group_count = []
        host_count = []
        if len(json.loads(gid_list)) == 0:
            pass
        elif len(json.loads(gid_list)) == 1:
            gid_list = json.loads(gid_list)[0]
            ret = self.get_group_list(gid=gid_list)
            if not len(ret) == 0:
                group_count.append(ret)
        else:
            for i in json.loads(gid_list):
                ret = self.get_group_list(gid=i)
                if not len(ret) == 0:
                    group_count.append(ret)
        if len(sid_list) == 0:
            pass
        else:
            for i in json.loads(sid_list):
                ret = self.get_host_info(sid=i)
                if not len(ret) == 0:
                    host_count.append(ret)

        host_fei = []
        if len(group_count) >= 1:
            if len(host_count) >= 1:
                for i in group_count:
                    for i2 in host_count:
                        if i2[0] in i:
                            host_fei.append(i2)
        if len(host_fei) >= 1:
            for i in host_fei:
                if i in host_count:
                    host_count.remove(i)

        group_host_count = []
        if len(group_count) >= 1:
            for i in group_count[0]:
                group_host_count.append(i)

        if len(host_count) >= 1:
            for i2 in host_count:
                group_host_count.append(i2[0])

        return group_host_count

    def get_username(self, sid):
        return session['coll_username']

    # 取结果
    def get_output(self, ret_list):
        if len(ret_list) == 0:
            return False
        elif len(ret_list) == 1:
            if not ret_list[0]['resulut']:
                ret_list[0]['data'] = False
                return ret_list
            data = {"id": int(ret_list[0]['resulut'])}
            if re.search('^http://', ret_list[0]['host'][5]):
                url = ret_list[0]['host'][5] + '/agent/get_shell_output.json'
                ret = public.HttpPost(url, data, timeout=50)
                ret_list[0]['ip'] = ret_list[0]['host'][3]
                ret_list[0]['data'] = ret
                return ret_list
        else:
            for i in range(0, len(ret_list)):
                if not ret_list[i]['resulut']:
                    ret_list[i]['ip'] = ret_list[i]['host'][3]
                    ret_list[i]['data'] = False
                    continue
                data = {"id": int(ret_list[i]['resulut'])}
                if re.search('^http://', ret_list[i]['host'][5]):
                    url = ret_list[i]['host'][5] + '/agent/get_shell_output.json'
                    ret_list[i]['ip'] = ret_list[i]['host'][3]
                    ret = public.HttpPost(url, data, timeout=50)
                    ret_list[i]['data'] = ret
            return ret_list

    # 存入数据库
    def insert_sql(self):
        if len(self.__result_list)>=1:
            for i in self.__result_list:
                error_data={"status":"false","msg":"error"}
                if i['resulut']:
                    data = {"username": session['coll_username'], "time": datetime.now().strftime("%Y-%m-%d:%H:%M:%S"), "shell": i['shell_code'],"data": i['data'], "error": 0, "sid": i['sid'], "gid": i['gid']}
                else:
                    data = {"username": session['coll_username'], "time": datetime.now().strftime("%Y-%m-%d:%H:%M:%S"), "shell": i['shell_code'],"data":"连接服务器失败", "error": 1, "sid": i['sid'], "gid": i['gid']}
    
                M('history_shell').insert(data)
            return True
        else:
            return False
    #执行shell
    def set_shell(self, get):
        self.__host_data = None
        self.__result_list = []
        self.__shell_code = None
        sid_list = get.sid
        gid_list = get.gid
        result = {"status": False, "msg": "\u65e0\u6570\u636e"}
        ret = self.host_count(get)
        if len(ret) == 0:
            return public.returnMsg(False, '无数据')
        else:
            self.__host_data = ret
            self.run_shell(get)
            result = self.out_data()
            self.insert_sql()
        return result

    #启动post请求
    def run_Spider(self, url, data, data2):
        ret = public.HttpPost(url, data, timeout=3)
        if self.is_number(ret):
            host_list = {}
            host_list['host'] = data2
            host_list['resulut'] = ret
            self.__result_list.append(host_list)
        else:
            host_list = {}
            host_list['host'] = data2
            host_list['resulut'] = False
            self.__result_list.append(host_list)
        return ret

    #计算秘钥
    def _sign(self, access_key_secret, parameters):
        if not access_key_secret: return public.ReturnMsg(False,'access_key_secret不能为空')
        def percent_encode(encodeStr):
            encodeStr = str(encodeStr)
            if sys.version_info[0] == 3:
                res = urllib.parse.quote(encodeStr, '')
            else:
                res = urllib.quote(encodeStr, '')
            res = res.replace('+', '%20')
            res = res.replace('*', '%2A')
            res = res.replace('%7E', '~')
            return res

        sortedParameters = sorted(parameters.items(), key=lambda item: item[0])
        stringToSign = ''
        for (k, v) in sortedParameters:
            stringToSign += percent_encode(k) + percent_encode(v)
        if sys.version_info[0] == 2:
            h = hmac.new(str(access_key_secret), stringToSign.strip(), sha1)
        else:
            h = hmac.new(access_key_secret.encode('utf-8'), stringToSign.encode('utf8'), sha1)
        signature = base64.encodestring(h.digest()).strip()
        return signature

    #启动携程
    def run_shell(self, get):
        pool = gevent.pool.Pool(20)
        threads = []
        for i in self.__host_data:
            public_params = {"Format": "json",
                             "SignatureMethod": "HMAC-SHA1",
                             "Timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                             "SignatureNonce": str(uuid.uuid1()),
                             "AccessKeyId": i[6]}
            # 接口的私有参数
            private_params = {"shell": get.shell}
            self.__shell_code = get.shell
            paramsdata = dict(public_params, **private_params)
            signature = self._sign(i[-1], public_params)
            paramsdata['signature'] = signature
            url = i[5] + '/agent/exec_shell.json'
            threads.append(pool.spawn(self.run_Spider, url, paramsdata, i))
        ret = gevent.joinall(threads)
        return ret

    #结果集
    def out_Spider(self, url, data, data2):
        ret = public.HttpPost(url, data, timeout=50)
        self.__result_list[data2]['data'] = ret
        return self.__result_list
    
    #返回结果集
    def out_data(self):
        if len(self.__result_list) == 0:
            return False
        else:
            pool = gevent.pool.Pool(20)
            threads = []
            for i in range(0, len(self.__result_list)):
                if not self.__result_list[i]['resulut']:
                    self.__result_list[i]['ip'] = self.__result_list[i]['host'][3]
                    self.__result_list[i]['shell_code'] = self.__shell_code
                    self.__result_list[i]['sid'] = self.__result_list[i]['host'][0]
                    self.__result_list[i]['gid'] = self.__result_list[i]['host'][2]
                    self.__result_list[i]['data'] = False
                    continue

                if re.search('^http://', self.__result_list[i]['host'][5]):
                    public_params = {"Format": "json",
                                     "SignatureMethod": "HMAC-SHA1",
                                     "Timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                                     "SignatureNonce": str(uuid.uuid1()),
                                     "AccessKeyId": self.__result_list[i]['host'][6]}
                    # 接口的私有参数
                    private_params = {"id": int(self.__result_list[i]['resulut'])}
                    paramsdata = dict(public_params, **private_params)
                    signature = self._sign(self.__result_list[i]['host'][-1], public_params)
                    paramsdata['signature'] = signature

                    url = self.__result_list[i]['host'][5] + '/agent/get_shell_output.json'
                    self.__result_list[i]['ip'] = self.__result_list[i]['host'][3]
                    self.__result_list[i]['sid'] = self.__result_list[i]['host'][0]
                    self.__result_list[i]['gid'] = self.__result_list[i]['host'][2]
                    self.__result_list[i]['shell_code'] = self.__shell_code
                    threads.append(pool.spawn(self.out_Spider, url, paramsdata, i))
                    ret = gevent.joinall(threads)
        return self.__result_list

