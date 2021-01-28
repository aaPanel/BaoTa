# coding: utf-8
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: wzj <wzj@bt.cn>
# +-------------------------------------------------------------------
# +-------------------------------------------------------------------
# | 腾讯云dnspod操作类库
# +-------------------------------------------------------------------

import base64
import hmac
from hashlib import sha1
import requests
import time
import random
import public


class Dnspod(object):
    def __init__(self, secretId, secret):
        self.secretId = str(secretId).strip()
        self.secret = str(secret).strip()
        self.host = 'cns.api.qcloud.com'
        self.url = 'https://cns.api.qcloud.com/v2/index.php'

    def hash_hmac(self, code):
        '''
        sha1签名
        :param code:
        :return:
        '''
        hmac_code = hmac.new(self.secret.encode(), code.encode(), sha1).digest()
        return base64.b64encode(hmac_code).decode()

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
            canonicalizedQueryString += '&' + k + '=' + str(v)
        stringToSign = 'GET' + self.host + '/v2/index.php?' + canonicalizedQueryString[1:]
        signature = self.hash_hmac(stringToSign)
        return signature

    def add_pub_params(self, user_params):
        '''
        增加公共参数
        :param user_params:
        :return:
        '''

        parameters = {
            "Timestamp": int(time.time()),
            "Nonce": random.randint(11111111111111, 99999999999999),
            "SecretId": self.secretId,
            "SignatureMethod": "HmacSHA1"
        }

        for k in user_params:
            parameters[k] = user_params[k]
        parameters['Signature'] = self.compute_signature(parameters)
        return parameters

    # ---------------------解析相关接口-----------------------#

    def get_record_list(self, domain, rrkeyword=None, typekeyword=None, offset=0, length=100):
        '''
        获取解析记录列表
        :param domain: 域名名称
        :param rrkeyword: 根据子域名进行过滤
        :param typekeyword: 根据记录类型进行过滤
        :param offset: 偏移量，默认为0
        :param length: 返回数量，默认20，最大值100
        :return:
        '''
        user_params = {
            "Action": "RecordList",
            "domain": domain,
            "offset": offset,
            "length": length
        }
        if rrkeyword:
            user_params['subDomain'] = rrkeyword
        if typekeyword:
            user_params['recordType'] = typekeyword
        paramsdata = self.add_pub_params(user_params)
        response = requests.get(url=self.url, params=paramsdata).json()
        if response['code'] != 0: return []
        return response['data']['records']

    def query_record_id(self, domain, host, value, s_type='A'):
        '''
        查询解析记录id
        :param domain: 域名名称
        :param host: 主机记录
        :param s_type: 解析类型
        :param value: 记录值
        :return:
        '''
        record_list = self.get_record_list(domain, host, s_type)
        try:
            for item in record_list:
                if item['value'] == value:
                    return item['id']
            return None
        except:
            return None

    def add_record(self, domain, host, value, s_type='A', line='默认', ttl=600, mx=1):
        '''
        添加解析记录
        :param domain: 要添加解析记录的域名（主域名，不包括 www，例如：qcloud.com）
        :param s_type: 记录类型，可选的记录类型为："A", "CNAME", "MX", "TXT", "NS", "AAAA", "SRV"
        :param host: 子域名，例如：www
        :param value: 记录值，例如 IP：192.168.10.2，CNAME：cname.dnspod.com.，MX：mail.dnspod.com.
        :param line: 记录的线路名称，例如："默认"
        :param ttl: TTL 值，范围1 - 604800，不同等级域名最小值不同，默认为 600
        :param mx: MX 优先级，范围为0 - 50，当 recordType 选择 MX 时，mx 参数必选
        :return:
        '''
        user_params = {
            "Action": "RecordCreate",
            "domain": domain,
            "subDomain": host,
            "recordType": s_type,
            "recordLine": line,
            "value": value,
            "ttl": ttl,
        }
        if s_type.upper() == 'MX':
            user_params['mx'] = mx
        paramsdata = self.add_pub_params(user_params)
        response = requests.get(url=self.url, params=paramsdata).json()
        if response['code'] != 0:
            return public.returnMsg(False, response['message'])
        return public.returnMsg(True, '设置成功')

    def set_record_status(self, domain, record_id, status='enable'):
        '''
        设置解析记录状态
        :param domain: 域名名称
        :param record_id: 解析记录 ID
        :param status: 解析记录状态。取值：Enable: 启用解析 Disable: 暂停解析
        :return:
        '''
        if status.lower() not in ['enable', 'disable']:
            return {'status': False, 'msg': '非法操作'}
        user_params = {
            "Action": "RecordStatus",
            "domain": domain,
            "recordId": record_id,
            "status": status
        }
        paramsdata = self.add_pub_params(user_params)
        response = requests.get(url=self.url, params=paramsdata).json()
        if response['code'] != 0:
            return public.returnMsg(False, response['message'])
        return public.returnMsg(True, '设置成功')

    def delete_record(self, domain, record_id):
        '''
        删除解析记录
        :param domain: 域名名称
        :param record_id: 解析记录id
        :return:
        '''
        user_params = {
            "Action": "RecordDelete",
            "domain": domain,
            "recordId": record_id
        }
        paramsdata = self.add_pub_params(user_params)
        response = requests.get(url=self.url, params=paramsdata)
        return response.json()

    # ---------------------域名相关接口-----------------------#

    def get_domain_list(self, offset=0, length=100):
        '''
        获取域名列表
        :param offset: 偏移量，默认为0
        :param length: 返回数量，默认20，最大值100
        :return:
        '''

        args = {
            'Action': 'DomainList',
            'offset': offset,
            'length': length
        }
        params = self.add_pub_params(args)
        response = requests.get(url=self.url, params=params)
        return response.json()

    def add_domain(self, domain):
        '''
        添加域名
        :param domain: 要操作的域名（主域名，不包括 www，例如：qcloud.com）
        :return:
        '''
        args = {
            'Action': 'DomainCreate',
            'domain': domain
        }
        params = self.add_pub_params(args)
        response = requests.get(url=self.url, params=params)
        return response.json()

    def set_domain_status(self, domain, status):
        '''
        设置域名状态
        :param domain: 要操作的域名（主域名，不包括 www，例如：qcloud.com）
        :param status: 可选值为：“disable” 和 “enable”，分别代表 “暂停” 和 “启用”
        :return:
        '''
        args = {
            'Action': 'SetDomainStatus',
            'domain': domain,
            'status': status
        }
        params = self.add_pub_params(args)
        response = requests.get(url=self.url, params=params)
        return response.json()

    def delete_domain(self, domain):
        '''
        删除域名
        :param domain:
        :return:
        '''
        args = {
            'Action': 'DomainDelete',
            'domain': domain
        }
        params = self.add_pub_params(args)
        response = requests.get(url=self.url, params=params)
        return response.json()


if __name__ == '__main__':
    dnspod = Dnspod('AKIDvMhwzsb3NjVIyVOCJIBx5jDbpqfH4NI8', 'qV0JTDl7HQT3Yr0xhFbkhRzMXWSEn9cv')
    # 测试获取解析记录列表
    record_list = dnspod.get_record_list('bbtt.cn', 'www', 'A')
    print(record_list)
    # 测试添加解析记录
    # print(dnspod.add_record('bbtt.cn', 'www', '192.168.1.181'))
    # 测试获取解析记录id
    print(dnspod.query_record_id('bbtt.cn', 'www', '192.168.1.180'))
    # 测试修改解析记录状态
    # print(dnspod.set_record_status('bbtt.cn', 'www', '192.168.1.180', status='disable'))
    # 测试删除解析记录
    # print(dnspod.delete_record('bbtt.cn', 'www', '192.168.1.180'))

    # 测试获取域名列表
    # domain_list = dnspod.get_domain_list()
    # print(domain_list)
    # 测试添加域名功能
    # print(dnspod.add_domain('bbtt.cn'))
    # 测试设置域名状态功能
    # print(dnspod.set_domain_status('bbtt.cn', 'disable'))
    # 测试删除域名功能
    # print(dnspod.delete_domain('bbtt.cn'))
