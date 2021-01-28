# coding: utf-8
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: wzj <wzj@bt.cn>
# +-------------------------------------------------------------------
# +-------------------------------------------------------------------
# | 阿里云dns操作类库
# +-------------------------------------------------------------------

import sys
import base64
import hmac
from hashlib import sha1
import requests
import time
import uuid
import public


class AliyunDns(object):
    def __init__(self, key, secret):
        self.key = str(key).strip()
        self.secret = str(secret).strip()
        self.url = "http://alidns.aliyuncs.com"

    def percent_encode(self, encode_str):
        encode_str = str(encode_str)
        if sys.version_info[0] == 3:
            import urllib.parse
            res = urllib.parse.quote(encode_str, '')
        else:
            import urllib2
            res = urllib2.quote(encode_str, '')
        res = res.replace('+', '%20')
        res = res.replace('*', '%2A')
        res = res.replace('%7E', '~')
        return res

    def compute_signature(self, parameters):
        '''
        生成签名
        :param accessKeySecret:
        :param parameters:
        :return:
        '''
        sortedParameters = sorted(parameters.items(), key=lambda parameters: parameters[0])
        canonicalizedQueryString = ''
        for (k, v) in sortedParameters:
            canonicalizedQueryString += '&' + self.percent_encode(k) + '=' + self.percent_encode(v)
        stringToSign = 'GET&%2F&' + self.percent_encode(canonicalizedQueryString[1:])
        if sys.version_info[0] == 2:
            h = hmac.new(self.secret + "&", stringToSign, sha1)
        else:
            h = hmac.new(bytes(self.secret + "&", encoding="utf8"), stringToSign.encode('utf8'), sha1)
        signature = base64.encodestring(h.digest()).strip()
        return signature

    def add_pub_params(self, user_params):
        '''
        增加公共参数
        :param user_params:
        :return:
        '''
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        parameters = {
            'Format': 'JSON',
            'Version': '2015-01-09',
            'AccessKeyId': self.key,
            'SignatureVersion': '1.0',
            'SignatureMethod': 'HMAC-SHA1',
            'SignatureNonce': str(uuid.uuid1()),
            'Timestamp': timestamp
        }

        for k in user_params:
            parameters[k] = user_params[k]
        parameters['Signature'] = self.compute_signature(parameters)
        return parameters

    # ---------------------解析相关接口-----------------------#
    def get_record_list(self, domain, rrkeyword=None, typekeyword=None, page=1, size=200):
        '''
        获取解析记录列表
        :param domain: 域名名称
        :param rrkeyword: 主机记录的关键字，按照“%RRKeyWord%”模式搜索，不区分大小写
        :param typekeyword: 解析类型的关键字，按照全匹配搜索，不区分大小写
        :param page: 当前页数，起始值为1，默认为1
        :param size: 分页查询时设置的每页行数，最大值500，默认为20
        :return:
        '''
        user_params = {
            "Action": "DescribeDomainRecords",
            "DomainName": domain,
            "PageNumber": page,
            "PageSize": size
        }
        if rrkeyword:
            user_params['RRKeyWord'] = rrkeyword
        if typekeyword:
            user_params['TypeKeyWord'] = typekeyword
        paramsdata = self.add_pub_params(user_params)
        response = requests.get(url=self.url, params=paramsdata)
        if response.status_code != 200:
            return []
        return response.json()['DomainRecords']['Record']

    def query_record_id(self, domain, host, value, s_type='A'):
        '''
        查询解析记录id
        :param domain: 域名名称
        :param host: 主机记录
        :param s_type: 解析类型
        :param value: 记录值
        :return:
        '''
        user_params = {
            "Action": "DescribeDomainRecords",
            "DomainName": domain,
            "RRKeyWord": host,
            "TypeKeyWord": s_type,
            "ValueKeyWord": value
        }
        paramsdata = self.add_pub_params(user_params)
        response = requests.get(url=self.url, params=paramsdata)
        if response.status_code != 200:
            return None
        try:
            return response.json()['DomainRecords']['Record'][0]['RecordId']
        except:
            return None

    def add_record(self, domain, host, value, s_type='A'):
        '''
        添加解析记录
        :param domain: 域名名称
        :param s_type: 解析记录类型
        :param host: 主机记录，如果要解析@.exmaple.com，主机记录要填写”@”，而不是空
        :param value: 记录值
        :return:
        '''
        user_params = {
            "Action": "AddDomainRecord",
            "DomainName": domain,
            "RR": host,
            "Type": s_type,
            "Value": value,
        }
        paramsdata = self.add_pub_params(user_params)
        response = requests.get(url=self.url, params=paramsdata).json()
        if 'RecordId' in response:
            return public.returnMsg(True, '添加成功')
        return public.returnMsg(False, response['Message'])

    def set_record_status(self, domain, record_id, status='enable'):
        '''
        设置解析记录状态
        :param domain: 域名
        :param record_id: 解析记录的id
        :param status: 解析记录状态。取值：enable: 启用解析 disable: 暂停解析
        :return:
        '''
        if status.lower() not in ['enable', 'disable']:
            return public.returnMsg(False, '非法操作')
        user_params = {
            "Action": "SetDomainRecordStatus",
            "RecordId": record_id,
            "Status": status
        }
        paramsdata = self.add_pub_params(user_params)
        response = requests.get(url=self.url, params=paramsdata)
        if response.status_code == 200:
            return public.returnMsg(True, '设置成功')
        return public.returnMsg(False, '设置失败')

    def delete_record(self, domain, record_id):
        '''
        删除解析记录
        :param domain: 域名名称
        :param record_id: 解析记录id
        :return:
        '''
        user_params = {
            "Action": "DeleteDomainRecord",
            "RecordId": record_id,
        }
        paramsdata = self.add_pub_params(user_params)
        response = requests.get(url=self.url, params=paramsdata)
        if response.status_code == 200:
            return public.returnMsg(True, '删除成功')
        return public.returnMsg(False, '删除失败')

    # -------------------域名管理相关接口------------------------
    def get_domain_list(self, page=1, size=100):
        '''
        获取域名列表
        :param page: 当前页数，起始值为1，默认为1
        :param size: 分页查询时设置的每页行数，最大值100，默认为20
        :return:
        '''
        user_params = {
            "Action": "DescribeDomains",
            "PageNumber": page,
            "PageSize": size
        }
        paramsdata = self.add_pub_params(user_params)
        response = requests.get(url=self.url, params=paramsdata)
        return response.json()

    def add_domain(self, domain):
        '''
        添加域名
        :param domain: 域名名称
        :return:
        '''
        args = {
            'Action': 'AddDomain',
            'DomainName': domain
        }
        params = self.add_pub_params(args)
        response = requests.get(url=self.url, params=params)
        return response.json()

    def delete_domain(self, domain):
        '''
        删除域名
        :param domain: 域名名称
        :return:
        '''
        args = {
            'Action': 'DeleteDomain',
            'DomainName': domain
        }
        params = self.add_pub_params(args)
        response = requests.get(url=self.url, params=params)
        return response.json()


if __name__ == '__main__':
    ali_dns = AliyunDns('LTAI4FjZKbemERTBHJxhZb3i', 'xc9srA49YiY63Ch7r8Et1Sv2J01uML')
    # 测试获取解析记录列表
    record_list = ali_dns.get_record_list('wangzhj.top', 'www', 'A')
    print(record_list)
    # 测试添加解析记录
    # print(ali_dns.add_record('wangzhj.top', 'www', '192.168.1.181'))
    # 测试获取解析记录id
    print(ali_dns.query_record_id('wangzhj.top', 'www', '192.168.1.181'))
    # 测试设置解析记录状态
    # print(ali_dns.set_record_status('wangzhj.top', 'www', '192.168.1.181', status='disable'))
    # 测试删除解析记录
    # print(ali_dns.delete_record('wangzhj.top', 'www', '192.168.1.181'))

    # domain_list = ali_dns.get_domain_list()
    # print(domain_list)
    # 测试添加域名功能
    # print(ali_dns.add_domain('www.wangzhj.top'))
    # 测试删除域名功能
    # print(ali_dns.delete_domain('www.wangzhj.top'))
