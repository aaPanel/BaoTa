#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2020 宝塔软件(http://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 沐落 <cjx@bt.cn>
# | Author: lx
# | 消息通道邮箱模块 
# +-------------------------------------------------------------------

import os, sys, public, base64, json, re
import sys, os
panelPath = "/www/server/panel"
os.chdir(panelPath)
sys.path.insert(0,panelPath + "/class/")
import public

class sms_msg:

    _APIURL = 'http://www.bt.cn/api/wmsg'
    __UPATH = panelPath + '/data/userInfo.json'
    conf_path = panelPath + '/data/sms_main.json'

        #构造方法
    def __init__(self):
        self.setupPath = public.GetConfigValue('setup_path')
        pdata = {}
        data = {}
        if os.path.exists(self.__UPATH):
            try:
                self.__userInfo = json.loads(public.readFile(self.__UPATH));

                if self.__userInfo:
                    pdata['access_key'] = self.__userInfo['access_key'];
                    data['secret_key'] = self.__userInfo['secret_key'];
            except :
                self.__userInfo = None
        else:
            pdata['access_key'] = 'test'
            data['secret_key'] = '123456'

        pdata['data'] = data
        self.__PDATA = pdata
        self.__module_name = self.__class__.__name__.replace('_msg','')


    def get_version_info(self,get):
        """
        获取版本信息
        """
        data = {}
        data['ps'] = '宝塔短信消息通道，用于接收面板消息推送'
        data['version'] = '1.1'
        data['date'] = '2022-08-02'
        data['author'] = '宝塔'
        data['title'] = '短信'
        data['help'] = 'http://www.bt.cn'
        return data

    def get_config(self,get):
        result = {}
        data = {}
        skey = 'sms_count_{}'.format(public.get_user_info()['username'])
        try:
            from BTPanel import cache
            result = cache.get(skey)
        except:
            cache = None
        if not result:
            result = self.request('get_user_sms')
            if cache: cache.set(skey,result,3600)
        try:
            data = json.loads(public.readFile(self.conf_path))
        except :pass

        for key in data.keys():
            result[key] = data[key]
        return result


    def is_strong_password(self,password):
        """判断密码复杂度是否安全
        非弱口令标准：长度大于等于9，分别包含数字、小写。
        @return: True/False
        @author: linxiao<2020-9-19>
        """
        if len(password) < 6:return False

        import re
        digit_reg = "[0-9]"  # 匹配数字 +1
        lower_case_letters_reg = "[a-z]"  # 匹配小写字母 +1
        special_characters_reg = r"((?=[\x21-\x7e]+)[^A-Za-z0-9])"  # 匹配特殊字符 +1

        regs = [digit_reg,lower_case_letters_reg,special_characters_reg]
        grade = 0
        for reg in regs:
            if re.search(reg, password):
                grade += 1

        if grade >= 2 or (grade == 1 and len(password) >= 9):
            return True
        return False

    def __check_auth_path(self):

        auth = public.readFile('data/admin_path.pl')
        if not auth: return False

        slist = ['/','/123456','/admin123','/111111','/bt','/login','/cloudtencent','/tencentcloud','/admin','/admin888','/test']
        if auth in slist: return False

        if not self.is_strong_password(auth.strip('/')):
            return False
        return True

    def set_config(self,get):

        data = {}
        try:
            data = json.loads(public.readFile(self.conf_path))
        except :pass

        if 'login' in get:
            is_login = int(get['login'])
            if is_login and not self.__check_auth_path(): return public.returnMsg(False,'安全入口过于简单，存在安全隐患. <br>1、长度不得少于9位<br>2、英文+数字组合.')
            data['login'] = is_login

        public.writeFile(self.conf_path,json.dumps(data));
        return public.returnMsg(True, '操作成功!')

    """
    @发送短信
    @sm_type 预警类型, ssl_end|宝塔SSL到期提醒
    @sm_args 预警参数
    """
    def send_msg(self,sm_type = None,sm_args = None):

        s_type = sm_type
        title = '宝塔告警提醒'
        tmps = sm_type.split('|')
        if len(tmps) >= 2:
            s_type = tmps[0]
            title = tmps[1]

        self.__PDATA['data']['sm_type'] = s_type
        self.__PDATA['data']['sm_args'] = sm_args
        result = self.request('send_msg')

        try:

            res = {}
            uinfo = public.get_user_info()
            u_key = '{}****{}'.format(uinfo['username'][0:3],uinfo['username'][-3:])

            res[u_key] = 0
            if result['status']:
                res[u_key] = 1

                skey = 'sms_count_{}'.format(public.get_user_info()['username'])
                try:
                    from BTPanel import cache
                except:
                    cache = None
                if not result:
                    result = self.request('get_user_sms')
                    if cache: cache.set(skey,result,3600)

            public.write_push_log(self.__module_name,title,res)
        except:pass

        return result

    def canonical_data(self, args):
        """规范数据内容

        Args:
            args(dict): 消息原始参数

        Returns:
            new args: 替换后的消息参数
        """

        if not type(args) == dict: return args
        new_args = {}
        for param, value in args.items():
            if type(value) != str:
                new_str = str(value)
            else:
                new_str = value.replace(".", "_").replace("+", "＋")
            new_args[param] = new_str
        return new_args

    def push_data(self,data):
        sm_args = self.canonical_data(data['sm_args'])
        return self.send_msg(data['sm_type'],sm_args)

    #发送请求
    def request(self,dname):

        pdata = {}
        pdata['access_key'] = self.__PDATA['access_key']
        pdata['data'] = json.dumps(self.__PDATA['data'])
        try:
            result = public.httpPost(self._APIURL + '/' + dname,pdata)
            result = json.loads(result)
            # print("发送result:")
            # print(result)
            return result
        except Exception as e:
            # print("短信发送异常:")
            # print(e)
            return public.returnMsg(False,public.get_error_info())

    def uninstall(self):
        if os.path.exists(self.conf_path):
            os.remove(self.conf_path)