#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------


# +-------------------------------------------------------------------
# | 宝塔网络通信库
# +-------------------------------------------------------------------

import ssl
import public
import json

class http:

    def __init__(self):
        pass

    def get(self,url,timeout = 60,headers = {},verify = False):
        pass

    def post(self,url,data,timeout = 60,headers = {},verify = False):
        pass

    def _get_py2(self,url,timeout,headers):
        import urllib2
        req = urllib2.Request(url, headers = headers)
        r_response = urllib2.urlopen(req,timeout = timeout,)
        return response(r_response.read(),r_response.getcode(),r_response.headers)

    def _get_py3(self,url,timeout,headers):
        import urllib.request
        req = urllib.request.Request(url,headers = headers)
        r_response = urllib.request.urlopen(req,timeout = timeout)
        return response(r_response.read(),r_response.getcode(),r_response.headers)

    def _get_curl(self,url,timeout,headers):
        headers_str = self._str_headers(headers)
        result = public.ExecShell("curl -sS -i --connect-timeout {} {} {}".format(timeout,url,headers_str))[0]


    #to headers
    def _str_headers(self,headers):
        str_headers = ''
        for key in headers.keys():
            str_headers += ' -H "{}"'.format(key + ": " + headers[key])
        return str_headers



#响应对象
class response:
    status_code = None
    headers = {}
    request_body = None
    def __init__(self,body,status_code,headers):
        self.request_body = body
        self.status_code = status_code
        self.format_headers(headers)

    def format_headers(self,raw_headers):
        for h in raw_headers:
            h = h.strip()
            tmp = h.split(': ')
            if len(tmp) < 2: tmp.append('')
            self.headers[tmp[0]] = tmp[1]

    #取格式化JSON响应
    def json(self):
        try:
            return json.loads(self.request_body)
        except:
            return {}

    #取text响应
    def text(self):
        return request_body


