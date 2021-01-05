#coding: utf-8
# +-------------------------------------------------------------------
# | 集群架构 - DNS管理模块
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(https://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------
import public,os,sys,json,time,random
import requests
from OpenSSL import crypto
import sys, os
import time
import copy
import json
import base64
import hashlib
import binascii
import urllib

if sys.version_info[0] == 2:  # python2
    import urlparse
    from urlparse import urljoin
    import urllib2
    import cryptography.hazmat
    import cryptography.hazmat.backends
    import cryptography.hazmat.primitives.serialization
else:  # python3
    from urllib.parse import urlparse
    from urllib.parse import urljoin
    import cryptography
import platform
import hmac
try:
    import requests
except:
    public.ExecShell('pip install requests')
    import requests
try:
    import OpenSSL
except:
    public.ExecShell('pip install pyopenssl')
    import OpenSSL
import random
import datetime
import logging
from hashlib import sha1


class clusterDns:


    def __init__(self):

        pass

class aliyun:
    key = None
    secret = None
    url = "https://alidns.aliyuncs.com"
    def __init__(self, key, secret, ):
        self.key = str(key).strip()
        self.secret = str(secret).strip()

    def sign(self, parameters):
        '''
            @name 签名
            @author hwliang<2020-10-30>
            @param parameters<dict> 被签名的参数
            @return string
        '''
        def percent_encode(encodeStr):
            encodeStr = str(encodeStr)
            if sys.version_info[0] == 3:
                import urllib.request
                res = urllib.request.quote(encodeStr, '')
            else:
                res = urllib2.quote(encodeStr, '')
            res = res.replace('+', '%20')
            res = res.replace('*', '%2A')
            res = res.replace('%7E', '~')
            return res

        sortedParameters = sorted(parameters.items(), key=lambda parameters: parameters[0])
        canonicalizedQueryString = ''
        for (k, v) in sortedParameters:
            canonicalizedQueryString += '&' + percent_encode(k) + '=' + percent_encode(v)
        stringToSign = 'GET&%2F&' + percent_encode(canonicalizedQueryString[1:])
        if sys.version_info[0] == 2:
            h = hmac.new(self.secret + "&", stringToSign, sha1)
            signature = base64.encodestring(h.digest()).strip()
        else:
            h = hmac.new(bytes(self.secret + "&", encoding="utf8"), stringToSign.encode('utf8'), sha1)
            signature = base64.encodebytes(h.digest()).strip()
        
        return signature


    def get_params(self,action,pdata={}):
        '''
            @name 构造请求参数
            @author hwliang<2020-10-30>
            @param action<string> 请求动作
            @return dict
        '''
        randomint = random.randint(11111111111111, 99999999999999)
        now = datetime.datetime.utcnow()
        otherStyleTime = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        paramsdata = {
            "Action":action,
            "Format": "json", 
            "Version": "2015-01-09", 
            "SignatureMethod": "HMAC-SHA1", 
            "Timestamp": otherStyleTime,
            "SignatureVersion": "1.0", 
            "SignatureNonce": str(randomint),
            "Lang": 'cn',
            "AccessKeyId": self.key
            }
        for k in pdata.keys():
            paramsdata[k] = pdata[k]
        paramsdata['Signature'] = self.sign(paramsdata)
        return paramsdata

    def check_result(self,req):
        '''
            @name 检查响应结果
            @author hwliang<2020-10-30>
            @param req<requests> 响应结果
            @return mixed
        '''
        result = req.json()
        if req.status_code != 200:
            if result['Code'] == 'IncorrectDomainUser' or result['Code'] == 'InvalidDomainName.NoExist':
                return public.returnMsg(False,"这个阿里云账户下面不存在这个域名")
            elif result['Code'] == 'InvalidAccessKeyId.NotFound' or result['Code'] == 'SignatureDoesNotMatch':
                return public.returnMsg(False,"API密钥错误")
            else:
                return public.returnMsg(False,result['Message'])
        return result
        
    def get_domain_list(self,args = None):
        '''
            @name 获取域名列表
            @author hwliang<2020-10-30>
            @param args<dict_obj> 前端参数
            @return list
        '''
        paramsdata = self.get_params('DescribeDomains')
        req = requests.get(url=self.url, params=paramsdata,verify=False)
        result = self.check_result(req)
        return result

    def add_record(self,domain,s_type,host,value):
        '''
            @name 添加解析记录
            @author hwliang<2020-10-30>
            @param args<dict_obj> 前端参数
            @return list
        '''
        paramsdata = {}
        paramsdata['DomainName'] = domain
        paramsdata['RR'] = host
        paramsdata['Type'] = s_type
        paramsdata['Value'] = value
        paramsdata = self.get_params('AddDomainRecord',paramsdata)
        
        req = requests.get(url=self.url, params=paramsdata,verify=False)
        result = self.check_result(req)
        if 'status' in result:
            if not result['status']: return result
        return public.returnMsg(True,'添加成功')

    def query_recored_items(self, domain, host=None, s_type=None, page=1, psize=200):
        '''
            @name 获取解析列表
            @author hwliang<2020-10-30>
            @param domain<string> 域名
            @param host<string> 记录值关键词
            @param s_type<string> 记录类型关键词
            @param page<int> 分页
            @param psize<int> 每页行数
            @return list
        '''
        paramsdata = {}
        paramsdata['DomainName'] = domain
        paramsdata['PageNumber'] = page
        paramsdata['PageSize'] = psize
        if host: paramsdata['RRKeyWord'] = host
        if s_type: paramsdata['TypeKeyWord'] = s_type
        paramsdata = self.get_params('DescribeDomainRecords',paramsdata)
        
        req = requests.get(url=self.url, params=paramsdata,verify=False)
        result = self.check_result(req)
        return result

    def query_recored_id(self, domain, host, s_type="A"):
        '''
            @name 获取解析标识
            @author hwliang<2020-10-30>
            @param domain<string> 域名
            @param zone<string> 记录值关键词
            @param tipe<string> 记录类型关键词
            @return int or None
        '''
        record_id = None
        recoreds = self.query_recored_items(domain, host, s_type=s_type)
        recored_list = recoreds.get("DomainRecords", {}).get("Record", [])
        recored_item_list = [i for i in recored_list if i["RR"] == host]
        if len(recored_item_list):
            record_id = recored_item_list[0]["RecordId"]
        return record_id

    def remove_record(self,domain,host,s_type = 'A'):
        '''
            @name 删除解析记录
            @author hwliang<2020-10-30>
            @param domain<string> 域名
            @param host<string> 记录值关键词
            @param s_type<string> 记录类型关键词
            @return dict
        '''
        record_id = self.query_recored_id(domain,host,s_type)
        if not record_id:
            return public.returnMsg(False,"找不到域名的record_id: {}".format(domain))
        paramsdata = {}
        paramsdata['RecordId'] = record_id
        paramsdata = self.get_params('DeleteDomainRecord',paramsdata)
        req = requests.get(url=self.url, params=paramsdata,verify=False)
        
        result = self.check_result(req)
        if 'status' in result:
            if not result['status']: return result
        return public.returnMsg(True,'删除成功')


class dnspod:

    dns_provider_name = "dnspod"
    url = 'https://dnsapi.cn/'
    http_timeout = 60
    dnspod_id = None
    dnspod_api_key = None
    dnspod_login = None

    def __init__(self, dnspod_id, dnspod_api_key):
        self.dnspod_id = dnspod_id
        self.dnspod_api_key = dnspod_api_key
        self.dnspod_login = "{0},{1}".format(self.dnspod_id, self.dnspod_api_key)



    def get_params(self):
        '''
            @name 构造请求参数
            @author hwliang<2020-10-30>
            @return dict
        '''
        params = {
            "format": "json",
            "login_token": self.dnspod_login,
            "lang":'cn',
            "error_on_empty":'no'
        }
        return params


    def get_domain_list(self,args=None):
        '''
            @name 域取域名列表
            @author hwliang<2020-10-30>
            @return dict
        '''
        url = urljoin(self.url, "Domain.List")
        params = self.get_params()
        req = requests.post(url, data=params, timeout=self.http_timeout).json()
        return req


    def get_record_list(self,domain):
        url = urljoin(self.url, "Record.List")
        params = self.get_params()
        params['domain'] = domain
        req = requests.post(url, data=params, timeout=self.http_timeout).json()
        return req

    def add_record(self,domain,host,value,s_type):
        url = urljoin(self.url, "Record.Create")
        params = self.get_params()
        params['record_type'] = s_type
        params['domain'] = domain
        params['sub_domain'] = host
        params['value'] = value
        params['record_line_id'] = '0'

        req = requests.post(url, data=params, timeout=self.http_timeout).json()
        if req["status"]["code"] != "1":
            raise ValueError(
                "Error creating dnspod dns record: status_code={status_code} response={response}".format(
                    status_code=req["status"]["code"],
                    response=req["status"]["message"],
                )
            )


    def remove_record(self,domain,host,s_type):
        url = urljoin(self.url, "Record.List")
        params = self.get_params()
        params['record_type'] = s_type
        params['domain'] = domain
        params['subdomain'] = host
        list_dns_response = requests.post(url, data=params, timeout=self.http_timeout).json()
        urlr = urljoin(self.url, "Record.Remove")
        for i in range(0, len(list_dns_response["records"])):
            if list_dns_response["records"][i]['name'] != host:
                continue
            record_id = list_dns_response["records"][i]["id"]
            params = self.get_params()
            params['domain'] = domain
            params['record_id'] = record_id
            requests.post(urlr, data=params, timeout=self.http_timeout).json()


if __name__ == '__main__':

    # p = aliyun('LTAITMESjonZoGdy','PvqEM3G6XLwQaCFfPDEgqVwoBouvWv')
    # print(p.get_domain_list())
    domain = 'iisv.cn'
    p = dnspod('101362','825e1a7c41f74a21d9234f5b708b6819')
    d = p.get_record_list(domain)
    print(d['records'])