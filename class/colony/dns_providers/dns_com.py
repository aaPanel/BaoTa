# coding: utf-8
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: wzj <wzj@bt.cn>
# +-------------------------------------------------------------------
# +-------------------------------------------------------------------
# | dns.com操作类库
# +-------------------------------------------------------------------

import hashlib
import requests
import time


class DnsCom(object):
    def __init__(self, key, secret):
        self.key = str(key).strip()
        self.secret = str(secret).strip()

    def compute_signature(self, parameters):
        '''
        生成签名
        :param parameters:
        :return:
        '''
        sortedParameters = sorted(parameters.items(), key=lambda parameters: parameters[0])

        canonicalizedQueryString = ''
        for (k, v) in sortedParameters:
            canonicalizedQueryString += '&' + k + '=' + str(v)
        stringToSign = canonicalizedQueryString[1:] + self.secret
        signStr = stringToSign.encode(encoding='utf-8')
        sign = hashlib.md5(signStr).hexdigest()
        return sign

    def add_pub_params(self, user_params):
        '''
        增加公共参数
        :param user_params:
        :return:
        '''

        parameters = {
            "apiKey": self.key,
            "Timestamp": int(time.time())
        }

        for k in user_params:
            parameters[k] = user_params[k]
        parameters['Signature'] = self.compute_signature(parameters)
        return parameters

    # ---------------------解析相关接口-----------------------#
    def get_record_list(self, domain, host=None, s_type=None, page=1, page_size=100):
        '''
        获取解析记录列表
        :param domain: 域名名称
        :param host: 根据子域名进行过滤
        :param s_type: 根据记录类型进行过滤
        :param page: 第几页, 默认第一页
        :param page_size: 每页显示的数量, 默认每页显示5条
        :return:
        '''
        domain_id = self.get_domain_id(domain)
        if not domain_id: return {'status': False, 'msg': '没有查询到域名id'}
        user_params = {
            "domainID": domain_id,
            "page": page,
            "pageSize": page_size
        }
        if host:
            user_params['host'] = host
        if s_type:
            user_params['type'] = s_type
        paramsdata = self.add_pub_params(user_params)
        response = requests.get(url='https://www.dns.com/api/record/search/', params=paramsdata).json()
        if response['code'] != 0: return []
        return response['data']

    def add_record(self, domain, host, value, s_type='A', view_id=0, ttl=600, mx=1):
        '''
        添加解析记录
        :param domain: 要添加解析记录的域名（主域名，不包括 www，例如：dns.com）
        :param s_type: 记录类型，可选的记录类型为："A", "CNAME", "MX", "TXT", "NS", "AAAA", "SRV"
        :param host: 子域名，例如：www
        :param value: 记录值，例如 IP：192.168.10.2，CNAME：cname.dnspod.com.，MX：mail.dnspod.com.
        :param view_id: 线路id，默认为默认线路
        :param ttl: TTL 值，范围1 - 604800，不同等级域名最小值不同，默认为 600
        :param mx: MX 优先级，范围为0 - 50，当 recordType 选择 MX 时，mx 参数必选
        :return:
        '''
        domain_id = self.get_domain_id(domain)
        if not domain_id: return {'status': False, 'msg': '没有查询到域名id'}
        user_params = {
            "domainID": domain_id,
            "type": s_type,
            "viewID": view_id,
            "host": host,
            "value": value,
            "ttl": ttl,
        }
        if s_type.upper() == 'MX':
            user_params['mx'] = mx
        paramsdata = self.add_pub_params(user_params)
        response = requests.get(url='https://www.dns.com/api/record/create/', params=paramsdata)
        return response.json()

    def query_record_id(self, domain, host, value, s_type='A'):
        '''
        查询解析记录id
        :param domain: 域名名称
        :param host: 主机记录
        :param s_type: 解析类型
        :param value: 记录值
        :return:
        '''
        domain_id = self.get_domain_id(domain)
        if not domain_id: return {'status': False, 'msg': '没有查询到域名id'}
        user_params = {
            "domainID": domain_id,
            "type": s_type,
            "host": host,
            "value": value,
        }
        paramsdata = self.add_pub_params(user_params)
        response = requests.get(url='https://www.dns.com/api/record/search/', params=paramsdata).json()
        if response['code'] != 0:
            return None
        try:
            return response['data'][0]['recordID']
        except:
            return None

    def set_record_status(self, domain, host, value, s_type='A', status='enable'):
        '''
        设置解析记录状态
        :param domain: 域名名称
        :param host: 主机记录
        :param s_type: 解析类型
        :param value: 记录值
        :param status: 解析记录状态。可选值为：“disable” 和 “enable”，分别代表 “暂停” 和 “启用”
        :return:
        '''
        domain_id = self.get_domain_id(domain)
        if not domain_id: return {'status': False, 'msg': '没有查询到域名id'}
        if status.lower() not in ['enable', 'disable']:
            return {'status': False, 'msg': '非法操作'}
        record_id = self.query_record_id(domain, host, value, s_type)
        if not record_id: return {'status': False, 'msg': '找不到解析记录'}
        user_params = {
            "domainID": domain_id,
            "recordID": record_id,
        }
        paramsdata = self.add_pub_params(user_params)
        if status.lower() == 'enable':
            url = 'https://www.dns.com/api/record/start/'
        else:
            url = 'https://www.dns.com/api/record/pause/'
        response = requests.get(url=url, params=paramsdata)
        return response.json()

    def delete_record(self, domain, host, value, s_type='A'):
        '''
        删除解析记录
        :param domain: 域名名称
        :param host: 主机记录
        :param s_type: 解析类型
        :param value: 记录值
        :return:
        '''
        domain_id = self.get_domain_id(domain)
        if not domain_id: return {'status': False, 'msg': '没有查询到域名id'}
        record_id = self.query_record_id(domain, host, value, s_type)
        if not record_id: return {'status': False, 'msg': '找不到解析记录'}
        user_params = {
            "domainID": domain_id,
            "recordID": record_id
        }
        paramsdata = self.add_pub_params(user_params)
        response = requests.get(url='https://www.dns.com/api/record/remove/', params=paramsdata)
        return response.json()

    # ---------------------域名相关接口-----------------------#
    def get_domain_list(self, page=1, page_size=100):
        '''
        获取域名列表
        :param page: 第几页, 默认第一页
        :param length: 每页显示的数量, 默认每页显示5条
        :return:
        '''

        args = {
            'page': page,
            'pageSize': page_size
        }
        params = self.add_pub_params(args)
        response = requests.get(url='https://www.dns.com/api/domain/list/', params=params)
        return response.json()

    def get_domain_id(self, domain):
        '''
        通过域名查询域名id
        :param domain: 域名
        :return:
        '''
        args = {
            'domainID': domain
        }
        params = self.add_pub_params(args)
        response = requests.get(url='https://www.dns.com/api/domain/getsingle/', params=params)
        response_data = response.json()
        if response_data['code'] != 0:
            return None
        return response_data['data']['domainID']

    def add_domain(self, domain):
        '''
        添加域名
        :param domain: 要添加的域名
        :return:
        '''
        args = {
            'domain': domain
        }
        params = self.add_pub_params(args)
        response = requests.get(url='https://www.dns.com/api/domain/create/', params=params)
        return response.json()

    def set_domain_status(self, domain, status):
        '''
        设置域名状态
        :param domain: 要操作的域名（主域名，不包括 www，例如：dns.com）
        :param status: 可选值为：“pause” 和 “start”，分别代表 “暂停” 和 “启用”
        :return:
        '''
        if status not in ['start', 'pause']:
            return {'status': False, 'msg': '非法操作'}
        args = {
            'domain': domain
        }
        params = self.add_pub_params(args)
        response = requests.get(url='https://www.dns.com/api/domain/{}/'.format(status), params=params)
        return response.json()

    def delete_domain(self, domain):
        '''
        删除域名
        :param domain: 要删除的域名
        :return:
        '''
        args = {
            'domain': domain
        }
        params = self.add_pub_params(args)
        response = requests.get(url='https://www.dns.com/api/domain/remove/', params=params)
        return response.json()


if __name__ == '__main__':
    dns_com = DnsCom('c7722149110b7492a2e5cf1d8f3f966b', 'ecb4ff0e877a83292b9f35067e9ae673')
    # 测试获取域名列表功能
    domain_list = dns_com.get_domain_list()
    print(domain_list)
