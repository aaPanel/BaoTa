# coding: utf-8
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: wzj <wzj@bt.cn>
# +-------------------------------------------------------------------
# +-------------------------------------------------------------------
# | dns操作类库
# +-------------------------------------------------------------------
import re
import sys
import public


class dns(object):
    def get_dns_class(self, dns_type, key, secret):
        '''
        根据dns类型获取对应的操作类
        :param dns_type: dns类型
        :param key: api key
        :param secret: api secret
        :return:
        '''
        sys.path.append('class/colony')
        if dns_type == 'ali':
            from .dns_providers import AliyunDns
            return AliyunDns(key, secret)
        elif dns_type == 'dnspod':
            from .dns_providers import Dnspod
            return Dnspod(key, secret)
        elif dns_type == 'dns_com':
            from .dns_providers import DnsCom
            return DnsCom(key, secret)

    # ---------------------解析相关接口-----------------------
    def get_record_list(self, get):
        '''
        获取解析记录列表
        :return:
        '''
        dns_type = get.dns_type.strip()
        key = get.key.strip()
        secret = get.secret.strip()
        domain = get.domain.strip()
        host = get.host.strip()
        s_type = get.s_type.strip() if 's_type' in get else 'A'
        if dns_type not in ('ali', 'dnspod', 'dns_com'):
            return public.returnMsg(False, "不支持的dns类型！")
        return self.get_dns_class(dns_type, key, secret).get_record_list(domain, host, s_type)

    def add_record(self, get):
        '''
        添加解析记录
        :param domain: 域名名称
        :param host: 主机记录
        :param s_type: 解析类型
        :param value: 记录值
        :return:
        '''
        dns_type = get.dns_type.strip()
        key = get.key.strip()
        secret = get.secret.strip()
        domain = get.domain.strip()
        host = get.host.strip()
        value = get.value.strip()
        s_type = get.s_type.strip() if 's_type' in get else 'A'
        if dns_type not in ('ali', 'dnspod', 'dns_com'):
            return public.returnMsg(False, "不支持的dns类型！")
        return self.get_dns_class(dns_type, key, secret).add_record(domain, host, value, s_type)

    def set_record_status(self, get):
        '''
        设置解析记录状态
        :param domain: 域名名称
        :param record_id: 解析记录id
        :param status: 解析记录状态。取值：enable: 启用解析 disable: 暂停解析
        :return:
        '''
        dns_type = get.dns_type.strip()
        key = get.key.strip()
        secret = get.secret.strip()
        domain = get.domain.strip()
        record_id = get.record_id
        status = get.status.strip()
        if dns_type not in ('ali', 'dnspod', 'dns_com'):
            return public.returnMsg(False, "不支持的dns类型！")
        return self.get_dns_class(dns_type, key, secret).set_record_status(domain, record_id, status)

    def delete_record(self, get):
        '''
        删除解析记录
        :param domain: 域名名称
        :param record_id: 解析记录id
        :return:
        '''
        dns_type = get.dns_type.strip()
        key = get.key.strip()
        secret = get.secret.strip()
        domain = get.domain.strip()
        record_id = get.record_id.strip()
        if dns_type not in ('ali', 'dnspod', 'dns_com'):
            return public.returnMsg(False, "不支持的dns类型！")
        return self.get_dns_class(dns_type, key, secret).delete_record(domain, record_id)

    def check_node(self, get):
        '''
        检测域名下的节点服务状态，无法访问的状态设置为disable
        :param domain: 域名名称
        :param host: 主机记录
        :param s_type: 解析类型
        :param port: 服务端口
        :return:
        '''
        dns_type = get.dns_type.strip()
        port = int(get.port)
        if dns_type not in ('ali', 'dnspod', 'dns_com'):
            return public.returnMsg(False, "不支持的dns类型！")
        record_list = self.get_record_list(get)
        print(record_list)
        for item in record_list:
            if dns_type == 'ali':
                node_ip = item['Value']
                record_id = item['RecordId']
            else:
                node_ip = item['value']
                record_id = item['id']
            if port == 443:
                url = 'https://{}'.format(node_ip)
            else:
                url = 'http://{}'.format(node_ip)
            print('check url: ', url)
            http_status = self.http_get(url)
            print('check status: ', http_status)
            get['record_id'] = record_id
            if not http_status:
                get['status'] = 'disable'
                self.set_record_status(get)
            else:
                get['status'] = 'enable'
                self.set_record_status(get)
        return self.get_record_list(get)

    def http_get(self, url):
        '''
        发送检测请求
        :param url:
        :return:
        '''
        ret = re.search(r'https://', url)
        if ret:
            try:
                from gevent import monkey
                monkey.patch_ssl()
                import requests
                ret = requests.get(url, verify=False, timeout=5)
                # print(ret.status_code)
                status = [200, 301, 302, 404, 403]
                if ret.status_code in status:
                    return True
                else:
                    return False
            except:
                # print(traceback.format_exc())
                return False
        else:
            try:
                import requests
                ret = requests.get(url, timeout=5)
                # print(ret.status_code)
                status = [200, 301, 302, 404, 403]
                if ret.status_code in status:
                    return True
                return False
            except:
                # print(traceback.format_exc())
                return False

    # ---------------------域名相关接口-----------------------
    def get_domain_list(self, get):
        '''
        获取域名列表
        :return:
        '''
        dns_type = get.dns_type.strip()
        key = get.key.strip()
        secret = get.secret.strip()
        if dns_type not in ('ali', 'dnspod', 'dns_com'):
            return public.returnMsg(False, "不支持的dns类型！")
        return self.get_dns_class(dns_type, key, secret).get_domain_list()

    def add_domain(self, get):
        '''
        添加域名
        '''
        dns_type = get.dns_type.strip()
        key = get.key.strip()
        secret = get.secret.strip()
        domain = get.domain.strip()
        if dns_type not in ('ali', 'dnspod', 'dns_com'):
            return public.returnMsg(False, "不支持的dns类型！")
        return self.get_dns_class(dns_type, key, secret).add_domain(domain)

    def delete_domain(self, get):
        '''
        删除域名
        '''
        dns_type = get.dns_type.strip()
        key = get.key.strip()
        secret = get.secret.strip()
        domain = get.domain.strip()
        if dns_type not in ('ali', 'dnspod', 'dns_com'):
            return public.returnMsg(False, "不支持的dns类型！")
        return self.get_dns_class(dns_type, key, secret).delete_domain(domain)
