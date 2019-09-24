#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 曹觉心 <314866873@qq.com>
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
    import urllib2
    import cryptography.hazmat
    import cryptography.hazmat.backends
    import cryptography.hazmat.primitives.serialization
else:  # python3
    from urllib.parse import urlparse
    import cryptography
import platform
import hmac
try:
    import requests
except:
    os.system('pip install requests')
    import requests
try:
    import OpenSSL
except:
    os.system('pip install pyopenssl')
    import OpenSSL
import random
import datetime
import logging
from hashlib import sha1

os.chdir("/www/server/panel")
sys.path.append("class/")
import public


def extract_zone(domain_name):
    domain_name = domain_name.lstrip("*.")
    top_domain_list = ['.ac.cn', '.ah.cn', '.bj.cn', '.com.cn', '.cq.cn', '.fj.cn', '.gd.cn', 
                        '.gov.cn', '.gs.cn', '.gx.cn', '.gz.cn', '.ha.cn', '.hb.cn', '.he.cn', 
                        '.hi.cn', '.hk.cn', '.hl.cn', '.hn.cn', '.jl.cn', '.js.cn', '.jx.cn', 
                        '.ln.cn', '.mo.cn', '.net.cn', '.nm.cn', '.nx.cn', '.org.cn']
    old_domain_name = domain_name
    m_count = domain_name.count(".")
    top_domain = "."+".".join(domain_name.rsplit('.')[-2:])
    new_top_domain = "." + top_domain.replace(".","")
    is_tow_top = False
    if top_domain in top_domain_list:
        is_tow_top = True
        domain_name = domain_name[:-len(top_domain)] + new_top_domain

    if domain_name.count(".") > 1:
        zone, middle, last = domain_name.rsplit(".", 2)        
        acme_txt = "_acme-challenge.%s" % zone
        if is_tow_top: last = top_domain[1:]
        root = ".".join([middle, last])
    else:
        zone = ""
        root = old_domain_name
        acme_txt = "_acme-challenge"
    return root, zone, acme_txt

class AliyunDns(object):
    def __init__(self, key, secret, ):
        self.key = str(key).strip()
        self.secret = str(secret).strip()
        self.url = "http://alidns.aliyuncs.com"

    def sign(self, accessKeySecret, parameters):  # '''签名方法
        def percent_encode(encodeStr):
            encodeStr = str(encodeStr)
            if sys.version_info[0] == 3:
                res = urllib.parse.quote(encodeStr, '')
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
            h = hmac.new(accessKeySecret + "&", stringToSign, sha1)
        else:
            h = hmac.new(bytes(accessKeySecret + "&", encoding="utf8"), stringToSign.encode('utf8'), sha1)
        signature = base64.encodestring(h.digest()).strip()
        return signature

    def create_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = extract_zone(domain_name)
        print("create_dns_record start: ", acme_txt, domain_dns_value)
        randomint = random.randint(11111111111111, 99999999999999)
        now = datetime.datetime.utcnow()
        otherStyleTime = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        paramsdata = {
            "Action": "AddDomainRecord", "Format": "json", "Version": "2015-01-09", "SignatureMethod": "HMAC-SHA1", "Timestamp": otherStyleTime,
            "SignatureVersion": "1.0", "SignatureNonce": str(randomint), "AccessKeyId": self.key,
            "DomainName": root,
            "RR": acme_txt,
            "Type": "TXT",
            "Value": domain_dns_value,
        }

        print(paramsdata)
        Signature = self.sign(self.secret, paramsdata)
        paramsdata['Signature'] = Signature
        req = requests.get(url=self.url, params=paramsdata)
        if req.status_code != 200:
            if req.json()['Code'] == 'IncorrectDomainUser' or req.json()['Code'] == 'InvalidDomainName.NoExist':
                raise ValueError("这个阿里云账户下面不存在这个域名，添加解析失败")
            elif req.json()['Code'] == 'InvalidAccessKeyId.NotFound' or req.json()['Code'] == 'SignatureDoesNotMatch':
                raise ValueError("API密钥错误，添加解析失败")
            else:
                raise ValueError(req.json()['Message'])
        print("create_dns_record end")

    def query_recored_items(self, host, zone=None, tipe=None, page=1, psize=200):
        randomint = random.randint(11111111111111, 99999999999999)
        now = datetime.datetime.utcnow()
        otherStyleTime = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        paramsdata = {
            "Action": "DescribeDomainRecords", "Format": "json", "Version": "2015-01-09", "SignatureMethod": "HMAC-SHA1", "Timestamp": otherStyleTime,
            "SignatureVersion": "1.0", "SignatureNonce": str(randomint), "AccessKeyId": self.key,
            "DomainName": host,
        }
        if zone:
            paramsdata['RRKeyWord'] = zone
        if tipe:
            paramsdata['TypeKeyWord'] = tipe
        Signature = self.sign(self.secret, paramsdata)
        paramsdata['Signature'] = Signature
        req = requests.get(url=self.url, params=paramsdata)
        return req.json()

    def query_recored_id(self, root, zone, tipe="TXT"):
        record_id = None
        recoreds = self.query_recored_items(root, zone, tipe=tipe)
        recored_list = recoreds.get("DomainRecords", {}).get("Record", [])
        recored_item_list = [i for i in recored_list if i["RR"] == zone]
        if len(recored_item_list):
            record_id = recored_item_list[0]["RecordId"]
        return record_id

    def delete_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = extract_zone(domain_name)
        print("delete_dns_record start: ", acme_txt, domain_dns_value)
        record_id = self.query_recored_id(root, acme_txt)
        if not record_id:
            msg = "找不到域名的record_id: ", domain_name
            print(msg)
            return
        print("start to delete dns record, id: ", record_id)
        randomint = random.randint(11111111111111, 99999999999999)
        now = datetime.datetime.utcnow()
        otherStyleTime = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        paramsdata = {
            "Action": "DeleteDomainRecord", "Format": "json", "Version": "2015-01-09", "SignatureMethod": "HMAC-SHA1", "Timestamp": otherStyleTime,
            "SignatureVersion": "1.0", "SignatureNonce": str(randomint), "AccessKeyId": self.key,
            "RecordId": record_id,
        }
        Signature = self.sign(self.secret, paramsdata)
        paramsdata['Signature'] = Signature
        req = requests.get(url=self.url, params=paramsdata)
        if req.status_code != 200:
            raise ValueError("删除解析记录失败")
        print("delete_dns_record end: ", acme_txt)

class CloudxnsDns(object):
    def __init__(self, key, secret, ):
        self.key = key
        self.secret = secret
        self.APIREQUESTDATE = time.ctime()

    def extract_zone(self,domain_name):
        domain_name = domain_name.lstrip("*.")
        if domain_name.count(".") > 1:
            zone, middle, last = str(domain_name).rsplit(".", 2)
            root = ".".join([middle, last])
            acme_txt = "_acme-challenge.%s" % zone
        else:
            zone = ""
            root = domain_name
            acme_txt = "_acme-challenge"
        return root, zone, acme_txt

    def get_headers(self, url, parameter=''):
        APIREQUESTDATE = self.APIREQUESTDATE
        APIHMAC = public.Md5(self.key + url + parameter + APIREQUESTDATE + self.secret)
        headers = {
            "API-KEY": self.key,
            "API-REQUEST-DATE": APIREQUESTDATE,
            "API-HMAC": APIHMAC,
            "API-FORMAT": "json"
        }
        return headers

    def get_domain_list(self):
        url = "https://www.cloudxns.net/api2/domain"
        headers = self.get_headers(url)
        req = requests.get(url=url, headers=headers,verify=False)
        req = req.json()
        
        return req

    def get_domain_id(self, domain_name):
        req = self.get_domain_list()
        for i in req["data"]:
            if domain_name.strip() == i['domain'][:-1]:
                return i['id']
        return False

    def create_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = self.extract_zone(domain_name)
        domain = self.get_domain_id(root)
        if not domain:
            raise ValueError('域名不存在这个cloudxns用户下面，添加解析失败。')

        print("create_dns_record,", acme_txt, domain_dns_value)
        url = "https://www.cloudxns.net/api2/record"
        data = {
            "domain_id": int(domain),
            "host": acme_txt,
            "value": domain_dns_value,
            "type": "TXT",
            "line_id": 1,
        }
        parameter = json.dumps(data)
        headers = self.get_headers(url, parameter)
        req = requests.post(url=url, headers=headers, data=parameter,verify=False)
        req = req.json()
       
        print("create_dns_record_end")
        return req

    def delete_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = self.extract_zone(domain_name)
        print("delete_dns_record start: ", acme_txt, domain_dns_value)
        url = "https://www.cloudxns.net/api2/record/{}/{}".format(self.get_record_id(root), self.get_domain_id(root))
        headers = self.get_headers(url, )
        req = requests.delete(url=url, headers=headers, verify=False)
        req = req.json()
        print("delete_dns_record_success")
        return req

    def get_record_id(self, domain_name):
        url = "http://www.cloudxns.net/api2/record/{}?host_id=0&offset=0&row_num=2000".format(self.get_domain_id(domain_name))
        headers = self.get_headers(url, )
        req = requests.get(url=url, headers=headers,verify=False)
        req = req.json()
        for i in req['data']:
            if i['type'] == "TXT":
                return i['record_id']
        return False

class Dns_com(object):

    
    def get_dns_obj(self):
        p_path = '/www/server/panel/plugin/dns'
        if not os.path.exists(p_path +'/dns_main.py'): return None
        sys.path.insert(0,p_path)
        import dns_main
        return dns_main.dns_main()

    def create_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = extract_zone(domain_name)
        print("[DNS]创建TXT记录,", acme_txt, domain_dns_value)
        result = self.get_dns_obj().add_txt(acme_txt + '.' + root,domain_dns_value)
        if result == "False":
            raise ValueError('[DNS]当前绑定的宝塔DNS云解析账户里面不存在这个域名,添加解析失败!')
        print("[DNS]TXT记录创建成功")
        print("[DNS]尝试验证TXT记录")
        time.sleep(10)

    def delete_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = extract_zone(domain_name)
        print("[DNS]准备删除TXT记录: ", acme_txt, domain_dns_value)
        result = self.get_dns_obj().remove_txt(acme_txt + '.' + root)
        print("[DNS]TXT记录删除成功")

