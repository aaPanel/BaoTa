#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <2879625666@qq.com>
# +-------------------------------------------------------------------

#------------------------------
# API-Demo of Python
#------------------------------
import time,hashlib,sys,os,json
class bt_api:
    __BT_KEY = '4vKENa5oEo8ZoNBuN7Rt6QGtlgB0Bo5i'
    __BT_PANEL = 'http://192.168.1.245:8888'

    #如果希望多台面板，可以在实例化对象时，将面板地址与密钥传入
    def __init__(self,bt_panel = None,bt_key = None):
        if bt_panel: 
            self.__BT_PANEL = bt_panel
            self.__BT_KEY = bt_key


    #取面板日志
    def get_logs(self):
        #拼接URL地址
        url = self.__BT_PANEL + '/data?action=getData'

        #准备POST数据
        p_data = self.__get_key_data()  #取签名
        p_data['table'] = 'logs'
        p_data['limit'] = 10
        p_data['tojs'] = 'test'

        #请求面板接口
        result = self.__http_post_cookie(url,p_data)

        #解析JSON数据
        return json.loads(result)

    #创建网站
    def create_site(self):
        #拼接URL地址
        url = self.__BT_PANEL + '/site?action=AddSite'

        #准备POST数据
        p_data = self.__get_key_data()  #取签名
        p_data['webname'] = '{"domain":"1.com","domainlist":[],"count":0}'
        p_data['ps'] = "1.com"
        p_data['path'] = '/www/wwwroot/1_com'
        p_data['ftp'] = "true"
        p_data['ftp_username'] = "ftp_1_com"
        p_data['ftp_password'] = "4fxFYbSTbksYMhPE"
        p_data['sql'] = "true"
        p_data['codeing'] = "utf8"
        p_data['datauser'] = "sql_1_com"
        p_data['datapassword'] = "ThHZjXRpyKEH6dA8"
        p_data['type'] = "PHP"
        p_data['version'] = "72"
        p_data['type_id'] = "0"
        p_data['port'] = "80"
        #请求面板接口
        result = self.__http_post_cookie(url,p_data)

        #解析JSON数据
        return json.loads(result)


    #计算MD5
    def __get_md5(self,s):
        m = hashlib.md5()
        m.update(s.encode('utf-8'))
        return m.hexdigest()

    #构造带有签名的关联数组
    def __get_key_data(self):
        now_time = int(time.time())
        p_data = {
                    'request_token':self.__get_md5(str(now_time) + '' + self.__get_md5(self.__BT_KEY)),
                    'request_time':now_time
                 }
        return p_data


    #发送POST请求并保存Cookie
    #@url 被请求的URL地址(必需)
    #@data POST参数，可以是字符串或字典(必需)
    #@timeout 超时时间默认1800秒
    #return string
    def __http_post_cookie(self,url,p_data,timeout=1800):
        cookie_file = './' + self.__get_md5(self.__BT_PANEL) + '.cookie';
        if sys.version_info[0] == 2:
            #Python2
            import urllib,urllib2,ssl,cookielib

            #创建cookie对象
            cookie_obj = cookielib.MozillaCookieJar(cookie_file)

            #加载已保存的cookie
            if os.path.exists(cookie_file):cookie_obj.load(cookie_file,ignore_discard=True,ignore_expires=True)

            ssl._create_default_https_context = ssl._create_unverified_context

            data = urllib.urlencode(p_data)
            req = urllib2.Request(url, data)
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_obj))
            response = opener.open(req,timeout=timeout)

            #保存cookie
            cookie_obj.save(ignore_discard=True, ignore_expires=True)
            return response.read()
        else:
            #Python3
            import urllib.request,ssl,http.cookiejar
            cookie_obj = http.cookiejar.MozillaCookieJar(cookie_file)
            cookie_obj.load(cookie_file,ignore_discard=True,ignore_expires=True)
            handler = urllib.request.HTTPCookieProcessor(cookie_obj)
            data = urllib.parse.urlencode(p_data).encode('utf-8')
            req = urllib.request.Request(url, data)
            opener = urllib.request.build_opener(handler)
            response = opener.open(req,timeout = timeout)
            cookie_obj.save(ignore_discard=True, ignore_expires=True)
            result = response.read()
            if type(result) == bytes: result = result.decode('utf-8')
            return result


if __name__ == '__main__':
    #实例化宝塔API对象
    my_api = bt_api()

    #调用get_logs方法
    r_data = my_api.create_site()

    #打印响应数据
    print(r_data)