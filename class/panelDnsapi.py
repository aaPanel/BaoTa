# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 沐落 <cjx@bt.cn>
# +-------------------------------------------------------------------
import re

import public, os, sys, json, time, random
import requests
# from OpenSSL import crypto
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
# try:
#     import OpenSSL
# except:
#     public.ExecShell('pip install pyopenssl')
#     import OpenSSL
import random
import datetime
import logging
from hashlib import sha1
from uuid import uuid4
from itertools import chain
from typing import Set, List, Optional, Union, Dict, Tuple

os.chdir("/www/server/panel")
if 'class/' not in sys.path:
    sys.path.insert(0, 'class/')

import public

caa_value = '0 issue "letsencrypt.org"'


class ExtractZoneTool(object):

    # def __init__(self):
    #     self.top_domain_list = [
    #         '.ac.cn', '.ah.cn', '.bj.cn', '.com.cn', '.cq.cn', '.fj.cn', '.gd.cn',
    #         '.gov.cn', '.gs.cn', '.gx.cn', '.gz.cn', '.ha.cn', '.hb.cn', '.he.cn',
    #         '.hi.cn', '.hk.cn', '.hl.cn', '.hn.cn', '.jl.cn', '.js.cn', '.jx.cn',
    #         '.ln.cn', '.mo.cn', '.net.cn', '.nm.cn', '.nx.cn', '.org.cn']
    #     top_domain_list_data = public.readFile('{}/config/domain_root.txt'.format(public.get_panel_path()))
    #     if top_domain_list_data:
    #         self.top_domain_list = set(top_domain_list_data.strip().split('\n'))

    def __call__(self, domain_name):
        root, zone = public.split_domain_sld(domain_name)  # 使用统一切割方法
        if not zone:
            acme_txt = "_acme-challenge"
        else:
            acme_txt = "_acme-challenge.%s" % zone
        return root, zone, acme_txt
        # domain_name = domain_name.lstrip("*.")
        # old_domain_name = domain_name
        # top_domain = "." + ".".join(domain_name.rsplit('.')[-2:])
        # new_top_domain = "." + top_domain.replace(".", "")
        # is_tow_top = False
        # if top_domain in self.top_domain_list:
        #     is_tow_top = True
        #     domain_name = domain_name[:-len(top_domain)] + new_top_domain
        #
        # if domain_name.count(".") <= 1:
        #     zone = ""
        #     root = old_domain_name
        #     acme_txt = "_acme-challenge"
        # else:
        #     zone, middle, last = domain_name.rsplit(".", 2)
        #     acme_txt = "_acme-challenge.%s" % zone
        #     if is_tow_top:
        #         last = top_domain[1:]
        #     root = ".".join([middle, last])
        # return root, zone, acme_txt


extract_zone = ExtractZoneTool()


class BaseDns(object):
    def __init__(self):
        self.dns_provider_name = self.__class__.__name__

    def log_response(self, response):
        try:
            log_body = response.json()
        except ValueError:
            log_body = response.content
        return log_body

    def create_dns_record(self, domain_name, domain_dns_value):
        raise NotImplementedError("create_dns_record method must be implemented.")

    def delete_dns_record(self, domain_name, domain_dns_value):
        raise NotImplementedError("delete_dns_record method must be implemented.")

    @classmethod
    def new(cls, conf_data):
        raise NotImplementedError("new method must be implemented.")

    def remove_record(self, domain, host, s_type):
        raise NotImplementedError("remove_record method must be implemented.")

    def add_record_for_creat_site(self, domain, server_ip):
        raise NotImplementedError("remove_record method must be implemented.")

# class TencentCloudDns(BaseDns):
#     dns_provider_name = "tencentcloud"
#     _type = 0
#
#     def __init__(self, secret_id, secret_key):
#         self.secret_id = secret_id
#         self.secret_key = secret_key
#         self.endpoint = "dnspod.tencentcloudapi.com"
#
#         super(TencentCloudDns, self).__init__()
#
#
#     def __client(self):
#         from tencentcloud.common import credential
#         from tencentcloud.dnspod.v20210323 import dnspod_client
#         from tencentcloud.common.profile.client_profile import ClientProfile
#         from tencentcloud.common.profile.http_profile import HttpProfile
#
#         cred = credential.Credential(self.secret_id, self.secret_key)
#         httpProfile = HttpProfile()
#         httpProfile.endpoint = self.endpoint
#         clientProfile = ClientProfile()
#         clientProfile.httpProfile = httpProfile
#         client = dnspod_client.DnspodClient(cred, "", clientProfile)
#
#         return client
#
#     def create_dns_record(self, domain_name, domain_dns_value):
#         from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
#         from tencentcloud.dnspod.v20210323 import models
#
#         domain_name = domain_name
#         domain_dns_value = domain_dns_value
#         record_type = 'TXT'
#         record_line = '默认'
#
#         domain_name, _, sub_domain = extract_zone(domain_name)
#
#         client = self.__client()
#         try:
#             req = models.CreateRecordRequest()
#             params = {
#                 "Domain": domain_name,
#                 "SubDomain": sub_domain,
#                 "RecordType": record_type,
#                 "RecordLine": record_line,
#                 "Value": domain_dns_value,
#             }
#
#             req.from_json_string(json.dumps(params))
#             client.CreateRecord(req)
#             return public.returnMsg(True, '添加成功')
#         except TencentCloudSDKException as err:
#             return public.returnMsg(False, '添加失败，msg：{}'.format(err))
#
#     @classmethod
#     def new(cls, conf_data: dict):
#         secret_id = conf_data.get("secret_id", "")
#         secret_key = conf_data.get("secret_key", "")
#
#         return cls(secret_id, secret_key)

class HuaweiCloudDns(BaseDns):
    dns_provider_name = "huaweicloud"
    _type = 0

    def __init__(self, ak, sk, project_id):
        self.ak = ak
        self.sk = sk
        self.project_id = project_id
        self.region = "cn-south-1"

        super(HuaweiCloudDns, self).__init__()

    def __client(self):
        from huaweicloudsdkcore.auth.credentials import BasicCredentials
        from huaweicloudsdkdns.v2.region.dns_region import DnsRegion
        from huaweicloudsdkdns.v2 import DnsClient

        credentials = BasicCredentials(self.ak, self.sk, self.project_id)
        client = DnsClient.new_builder() \
            .with_credentials(credentials) \
            .with_region(DnsRegion.value_of(self.region)) \
            .build()
        return client

    def create_dns_record(self, domain_name, domain_dns_value):
        from huaweicloudsdkdns.v2 import (CreateRecordSetWithLineRequest,
                                          CreateRecordSetWithLineRequestBody)

        record_type = 'TXT'

        if record_type == 'TXT':
            domain_dns_value = "\"{}\"".format(domain_dns_value)

        root_domain, _, sub_domain = extract_zone(domain_name)

        try:
            client = self.__client()
            zone_dic = self.get_zoneid_dict(client)
            request = CreateRecordSetWithLineRequest()
            request.zone_id = zone_dic[root_domain]
            request.body = CreateRecordSetWithLineRequestBody(
                records=[domain_dns_value],
                type=record_type,
                name="_acme-challenge.{}".format(domain_name)
            )
            client.create_record_set_with_line(request)
            return public.returnMsg(True, '添加成功')
        except Exception as e:
            return public.returnMsg(False, '添加失败，msg：{}'.format(e))

    def get_zoneid_dict(self, client):
        from huaweicloudsdkdns.v2 import ListPublicZonesRequest
        """
        获取所有域名对应id
        """
        request = ListPublicZonesRequest()
        response = client.list_public_zones(request).to_dict()
        data = {i["name"][:-1]: i["id"] for i in response["zones"]}

        return data

    @classmethod
    def new(cls, conf_data: dict) -> BaseDns:
        ak = conf_data.get("ak", None) or conf_data.get("AccessKey", "")
        sk = conf_data.get("sk", None) or conf_data.get("SecretKey", "")
        project_id = conf_data.get("project_id", None) or conf_data.get("project_id", "")

        return cls(ak, sk, project_id)

class DNSPodDns(BaseDns):
    dns_provider_name = "dnspod"
    _type = 0  # 0:lest 1：锐成

    def __init__(self, DNSPOD_ID, DNSPOD_API_KEY, DNSPOD_API_BASE_URL="https://dnsapi.cn/"):
        self.DNSPOD_ID = DNSPOD_ID
        self.DNSPOD_API_KEY = DNSPOD_API_KEY
        self.DNSPOD_API_BASE_URL = DNSPOD_API_BASE_URL
        self.HTTP_TIMEOUT = 65  # seconds
        self.DNSPOD_LOGIN = "{0},{1}".format(self.DNSPOD_ID, self.DNSPOD_API_KEY)

        if DNSPOD_API_BASE_URL[-1] != "/":
            self.DNSPOD_API_BASE_URL = DNSPOD_API_BASE_URL + "/"
        else:
            self.DNSPOD_API_BASE_URL = DNSPOD_API_BASE_URL
        super(DNSPodDns, self).__init__()

    def create_dns_record(self, domain_name, domain_dns_value):
        domain_name, _, subd = extract_zone(domain_name)
        if self._type == 1:
            self.add_record(domain_name, subd.replace('_acme-challenge.', ''), domain_dns_value, 'CNAME')
        else:
            self.add_record(domain_name, subd, domain_dns_value, 'TXT')

    def add_record(self, domain_name, subd, domain_dns_value, s_type):
        url = urljoin(self.DNSPOD_API_BASE_URL, "Record.Create")
        body = {
            "record_type": s_type,
            "domain": domain_name,
            "sub_domain": subd,
            "value": domain_dns_value,
            "record_line_id": "0",
            "format": "json",
            "login_token": self.DNSPOD_LOGIN,
        }
        create_dnspod_dns_record_response = requests.post(
            url, data=body, timeout=self.HTTP_TIMEOUT
        ).json()
        if create_dnspod_dns_record_response["status"]["code"] != "1":
            raise ValueError(
                "Error creating dnspod dns record: status_code={status_code} response={response}".format(
                    status_code=create_dnspod_dns_record_response["status"]["code"],
                    response=create_dnspod_dns_record_response["status"]["message"],
                )
            )

    def remove_record(self, domain_name, subd, s_type):
        url = urljoin(self.DNSPOD_API_BASE_URL, "Record.List")
        rootdomain = domain_name
        body = {
            "login_token": self.DNSPOD_LOGIN,
            "format": "json",
            "domain": rootdomain,
            "subdomain": subd,
            "record_type": s_type,
        }

        list_dns_response = requests.post(url, data=body, timeout=self.HTTP_TIMEOUT).json()
        for i in range(0, len(list_dns_response["records"])):
            if list_dns_response["records"][i]['name'] != subd:
                continue
            rid = list_dns_response["records"][i]["id"]
            urlr = urljoin(self.DNSPOD_API_BASE_URL, "Record.Remove")
            bodyr = {
                "login_token": self.DNSPOD_LOGIN,
                "format": "json",
                "domain": rootdomain,
                "record_id": rid,
            }
            requests.post(
                urlr, data=bodyr, timeout=self.HTTP_TIMEOUT
            ).json()

    def delete_dns_record(self, domain_name, domain_dns_value):
        try:
            domain_name, _, subd = extract_zone(domain_name)
            self.remove_record(domain_name, subd, 'TXT')
            self.remove_record(domain_name, '_acme-challenge', 'CNAME')
        except:
            pass

    def add_record_for_creat_site(self, domain, server_ip):
        domain_name, zone, _ = extract_zone(domain)
        self.add_record(domain_name, zone, server_ip, "A")

    @classmethod
    def new(cls, conf_data: dict) -> BaseDns:
        key = conf_data.get("key", None) or conf_data.get("ID", "")
        secret = conf_data.get("secret", None) or conf_data.get("Token", "")
        base_url = "https://dnsapi.cn/"

        return cls(key, secret, base_url)


class CloudFlareDns(BaseDns):
    dns_provider_name = "cloudflare"
    _type = 0  # 0:lest 1：锐成

    def __init__(
            self,
            CLOUDFLARE_EMAIL,
            CLOUDFLARE_API_KEY,
            CLOUDFLARE_API_BASE_URL="https://api.cloudflare.com/client/v4/",
    ):
        self.CLOUDFLARE_DNS_ZONE_ID = None
        self.CLOUDFLARE_EMAIL = CLOUDFLARE_EMAIL
        self.CLOUDFLARE_API_KEY = CLOUDFLARE_API_KEY
        self.CLOUDFLARE_API_BASE_URL = CLOUDFLARE_API_BASE_URL
        self.HTTP_TIMEOUT = 65  # seconds

        try:
            import urllib.parse as urlparse
        except:
            import urlparse

        if CLOUDFLARE_API_BASE_URL[-1] != "/":
            self.CLOUDFLARE_API_BASE_URL = CLOUDFLARE_API_BASE_URL + "/"
        else:
            self.CLOUDFLARE_API_BASE_URL = CLOUDFLARE_API_BASE_URL
        super(CloudFlareDns, self).__init__()

    def _get_auth_headers(self) -> dict:
        if self.CLOUDFLARE_EMAIL is None and isinstance(self.CLOUDFLARE_API_KEY, str):
            return {"Authorization": "Bearer " + self.CLOUDFLARE_API_KEY}
        else:
            return {"X-Auth-Email": self.CLOUDFLARE_EMAIL, "X-Auth-Key": self.CLOUDFLARE_API_KEY}

    def find_dns_zone(self, domain_name):
        url = urljoin(self.CLOUDFLARE_API_BASE_URL, "zones?status=active&per_page=1000")
        headers = self._get_auth_headers()
        find_dns_zone_response = requests.get(url, headers=headers, timeout=self.HTTP_TIMEOUT)
        if find_dns_zone_response.status_code != 200:
            raise ValueError(
                "Error creating cloudflare dns record: status_code={status_code} response={response}".format(
                    status_code=find_dns_zone_response.status_code,
                    response=self.log_response(find_dns_zone_response),
                )
            )

        result = find_dns_zone_response.json()["result"]
        for i in result:
            if i["name"] in domain_name:
                setattr(self, "CLOUDFLARE_DNS_ZONE_ID", i["id"])
        if isinstance(self.CLOUDFLARE_DNS_ZONE_ID, type(None)):
            raise ValueError(
                "Error unable to get DNS zone for domain_name={domain_name}: status_code={status_code} response={response}".format(
                    domain_name=domain_name,
                    status_code=find_dns_zone_response.status_code,
                    response=self.log_response(find_dns_zone_response),
                )
            )

    def add_record(self, domain_name, value, s_type):
        url = urljoin(
            self.CLOUDFLARE_API_BASE_URL,
            "zones/{0}/dns_records".format(self.CLOUDFLARE_DNS_ZONE_ID),
        )
        headers = self._get_auth_headers()
        body = {
            "type": s_type,
            "name": domain_name,
            "content": "{0}".format(value),
        }

        create_cloudflare_dns_record_response = requests.post(
            url, headers=headers, json=body, timeout=self.HTTP_TIMEOUT
        )
        if create_cloudflare_dns_record_response.status_code != 200:
            raise ValueError(
                "Error creating cloudflare dns record: status_code={status_code} response={response}".format(
                    status_code=create_cloudflare_dns_record_response.status_code,
                    response=self.log_response(create_cloudflare_dns_record_response),
                )
            )

    def create_dns_record(self, domain_name, domain_dns_value):
        domain_name = domain_name.lstrip("*.")
        self.find_dns_zone(domain_name)

        url = urljoin(
            self.CLOUDFLARE_API_BASE_URL,
            "zones/{0}/dns_records".format(self.CLOUDFLARE_DNS_ZONE_ID),
        )
        headers = self._get_auth_headers()
        body = {
            "type": "TXT",
            "name": "_acme-challenge" + "." + domain_name + ".",
            "content": "{0}".format(domain_dns_value),
        }

        if self._type == 1:
            body['type'] = 'CNAME'
            root, _, acme_txt = extract_zone(domain_name)
            body['name'] = acme_txt.replace('_acme-challenge.', '')

        create_cloudflare_dns_record_response = requests.post(
            url, headers=headers, json=body, timeout=self.HTTP_TIMEOUT
        )
        if create_cloudflare_dns_record_response.status_code != 200:
            # raise error so that we do not continue to make calls to ACME
            # server
            raise ValueError(
                "Error creating cloudflare dns record: status_code={status_code} response={response}".format(
                    status_code=create_cloudflare_dns_record_response.status_code,
                    response=self.log_response(create_cloudflare_dns_record_response),
                )
            )

    def remove_record(self, domain_name, dns_name, s_type):
        headers = self._get_auth_headers()

        list_dns_payload = {"type": s_type, "name": dns_name}
        list_dns_url = urljoin(
            self.CLOUDFLARE_API_BASE_URL,
            "zones/{0}/dns_records".format(self.CLOUDFLARE_DNS_ZONE_ID),
        )

        list_dns_response = requests.get(
            list_dns_url, params=list_dns_payload, headers=headers, timeout=self.HTTP_TIMEOUT
        )

        for i in range(0, len(list_dns_response.json()["result"])):
            dns_record_id = list_dns_response.json()["result"][i]["id"]
            url = urljoin(
                self.CLOUDFLARE_API_BASE_URL,
                "zones/{0}/dns_records/{1}".format(self.CLOUDFLARE_DNS_ZONE_ID, dns_record_id),
            )
            headers = self._get_auth_headers()
            requests.delete(
                url, headers=headers, timeout=self.HTTP_TIMEOUT
            )

    def delete_dns_record(self, domain_name, domain_dns_value):
        domain_name = domain_name.lstrip("*.")
        dns_name = "_acme-challenge" + "." + domain_name
        self.remove_record(domain_name, dns_name, 'TXT')

    def add_record_for_creat_site(self, domain, server_ip):
        domain_name, zone, _ = extract_zone(domain)
        self.find_dns_zone(domain_name)
        self.add_record(zone, server_ip, "A")

    @classmethod
    def new(cls, conf_data: dict) -> BaseDns:
        key = conf_data.get("key", None) or conf_data.get("E-Mail", None) or conf_data.get("E-MAIL", None)
        secret = conf_data.get("secret", None) or conf_data.get("API Key", None) or conf_data.get("API KEY", None)
        base_url = "https://api.cloudflare.com/client/v4/"

        if key is None and secret is None:
            secret = conf_data.get("API Token", None)  # 处理api - token的情况
        if key is None and secret is None:
            raise Exception("没有找到有效的DNS API密钥信息")
        return cls(key, secret, base_url)


class GoDaddyDns(BaseDns):
    _type = 0  # 0:lest 1：锐成
    http_timeout = 65

    def __init__(self, sso_key: str, sso_secret: str, base_url='https://api.godaddy.com'):
        self.sso_key = sso_key
        self.sso_secret = sso_secret
        self.base_url = base_url
        super(GoDaddyDns, self).__init__()
        self._headers = None

    def _get_auth_headers(self) -> dict:
        if self._headers is not None:
            return self._headers
        self._headers = {
            "Authorization": "sso-key {}:{}".format(self.sso_key, self.sso_secret)
        }
        return self._headers

    def create_dns_record(self, domain_name, domain_dns_value):
        domain_name = domain_name.lstrip("*.")
        root, zone, acme_txt = extract_zone(domain_name)

        url = urljoin(
            self.base_url,
            "/v1/domains/{}/records".format(root),
        )
        headers = self._get_auth_headers()
        body = [
            {
                "data": domain_dns_value,
                "name": acme_txt,
                "type": "TXT",
            }
        ]

        if self._type == 1:
            body[0]['type'] = 'CNAME'
            root, _, acme_txt = extract_zone(domain_name)
            body[0]['name'] = acme_txt.replace('_acme-challenge.', '')

        create_godaday_dns_record_response = requests.patch(
            url, headers=headers, json=body, timeout=self.http_timeout
        )
        if create_godaday_dns_record_response.status_code != 200:
            # raise error so that we do not continue to make calls to ACME
            # server
            raise ValueError(
                "Error creating cloudflare dns record: status_code={status_code} response={response}".format(
                    status_code=create_godaday_dns_record_response.status_code,
                    response=self.log_response(create_godaday_dns_record_response),
                )
            )

    def add_record(self, root, host, value, s_type):
        url = urljoin(
            self.base_url,
            "/v1/domains/{}/records".format(root),
        )
        headers = self._get_auth_headers()

        body = [{
            "type": s_type,
            "name": host,
            "data": "{0}".format(value),
        }]

        create_cloudflare_dns_record_response = requests.patch(
            url, headers=headers, json=body, timeout=self.http_timeout
        )
        if create_cloudflare_dns_record_response.status_code != 200:
            raise ValueError(
                "Error creating cloudflare dns record: status_code={status_code} response={response}".format(
                    status_code=create_cloudflare_dns_record_response.status_code,
                    response=self.log_response(create_cloudflare_dns_record_response),
                )
            )

    def remove_record(self, domain_name, dns_name, s_type):
        headers = self._get_auth_headers()

        list_dns_url = urljoin(
            self.base_url,
            "/v1/domains/{}/records/{}/{}".format(domain_name, s_type, dns_name),
        )

        dns_response = requests.delete(
            list_dns_url, headers=headers, timeout=self.http_timeout
        )
        if dns_response.status_code != 200:
            raise ValueError(
                "Error creating cloudflare dns record: status_code={status_code} response={response}".format(
                    status_code=dns_response.status_code,
                    response=self.log_response(dns_response),
                )
            )

    def add_record_for_creat_site(self, domain, server_ip):
        root, zone, _ = extract_zone(domain)
        self.add_record(root, zone, server_ip, "A")

    def delete_dns_record(self, domain_name, domain_dns_value):
        root, zone, acme_txt = extract_zone(domain_name)
        self.remove_record(root, acme_txt, 'TXT')

    @classmethod
    def new(cls, conf_data: dict) -> BaseDns:
        key = conf_data.get("key", None) or conf_data.get("Key", "")
        secret = conf_data.get("secret", None) or conf_data.get("Secret", "")
        base_url = "https://api.godaddy.com"

        return cls(key, secret, base_url)


class AliyunDns(object):
    _type = 0  # 0:lest 1：锐成

    def __init__(self, key, secret, ):
        self.key = str(key).strip()
        self.secret = str(secret).strip()
        self.url = "http://alidns.aliyuncs.com"

    def sign(self, accessKeySecret, parameters):  # '''签名方法
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
            h = hmac.new(accessKeySecret + "&", stringToSign, sha1)
        else:
            h = hmac.new(bytes(accessKeySecret + "&", encoding="utf8"), stringToSign.encode('utf8'), sha1)
        signature = base64.encodestring(h.digest()).strip()
        return signature

    def create_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = extract_zone(domain_name)
        if self._type == 1:
            acme_txt = acme_txt.replace('_acme-challenge.', '')
            self.add_record(root, 'CNAME', acme_txt, domain_dns_value)
        else:
            try:
                self.add_record(root, 'CAA', '@', caa_value)
            except:
                pass
            self.add_record(root, 'TXT', acme_txt, domain_dns_value)

    def add_record(self, domain, s_type, host, value):
        randomint = random.randint(11111111111111, 99999999999999)
        now = datetime.datetime.utcnow()
        otherStyleTime = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        paramsdata = {
            "Action": "AddDomainRecord", "Format": "json", "Version": "2015-01-09", "SignatureMethod": "HMAC-SHA1",
            "Timestamp": otherStyleTime,
            "SignatureVersion": "1.0", "SignatureNonce": str(randomint), "AccessKeyId": self.key,
            "DomainName": domain,
            "RR": host,
            "Type": s_type,
            "Value": value,
        }

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

    def query_recored_items(self, host, zone=None, tipe=None, page=1, psize=200):
        randomint = random.randint(11111111111111, 99999999999999)
        now = datetime.datetime.utcnow()
        otherStyleTime = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        paramsdata = {
            "Action": "DescribeDomainRecords", "Format": "json", "Version": "2015-01-09",
            "SignatureMethod": "HMAC-SHA1", "Timestamp": otherStyleTime,
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

    def remove_record(self, domain, host, s_type='TXT'):
        record_id = self.query_recored_id(domain, host, s_type)
        if not record_id:
            msg = "找不到域名的record_id: ", domain
            print(msg)
            return
        randomint = random.randint(11111111111111, 99999999999999)
        now = datetime.datetime.utcnow()
        otherStyleTime = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        paramsdata = {
            "Action": "DeleteDomainRecord", "Format": "json", "Version": "2015-01-09", "SignatureMethod": "HMAC-SHA1",
            "Timestamp": otherStyleTime,
            "SignatureVersion": "1.0", "SignatureNonce": str(randomint), "AccessKeyId": self.key,
            "RecordId": record_id,
        }
        Signature = self.sign(self.secret, paramsdata)
        paramsdata['Signature'] = Signature
        req = requests.get(url=self.url, params=paramsdata)
        if req.status_code != 200:
            raise ValueError("删除解析记录失败")

    def delete_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = extract_zone(domain_name)
        self.remove_record(root, acme_txt, 'TXT')
        self.remove_record(root, '@', 'CAA')
        self.remove_record(root, '_acme-challenge', 'CNAME')

    def add_record_for_creat_site(self, domain, server_ip):
        root, zone, _ = extract_zone(domain)
        self.add_record(root, "A", zone, server_ip)

    @classmethod
    def new(cls, conf_data: dict) -> "AliyunDns":
        key = conf_data.get("key", None) or conf_data.get("AccessKey", "")
        secret = conf_data.get("secret", None) or conf_data.get("SecretKey", "")

        return cls(key, secret)


class CloudxnsDns(object):
    def __init__(self, key, secret, ):
        self.key = key
        self.secret = secret
        self.APIREQUESTDATE = time.ctime()

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
        req = requests.get(url=url, headers=headers, verify=False)
        req = req.json()

        return req

    def get_domain_id(self, domain_name):
        req = self.get_domain_list()
        for i in req["data"]:
            if domain_name.strip() == i['domain'][:-1]:
                return i['id']
        return False

    def create_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = extract_zone(domain_name)
        domain = self.get_domain_id(root)
        if not domain:
            raise ValueError('域名不存在这个cloudxns用户下面，添加解析失败。')

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
        req = requests.post(url=url, headers=headers, data=parameter, verify=False)
        req = req.json()

        return req

    def delete_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = extract_zone(domain_name)
        print("delete_dns_record start: ", acme_txt, domain_dns_value)
        url = "https://www.cloudxns.net/api2/record/{}/{}".format(self.get_record_id(root, 'TXT'),
                                                                  self.get_domain_id(root))
        headers = self.get_headers(url, )
        req = requests.delete(url=url, headers=headers, verify=False)
        req = req.json()
        return req

    def get_record_id(self, domain_name, s_type='TXT'):
        url = "http://www.cloudxns.net/api2/record/{}?host_id=0&offset=0&row_num=2000".format(
            self.get_domain_id(domain_name))
        headers = self.get_headers(url, )
        req = requests.get(url=url, headers=headers, verify=False)
        req = req.json()
        for i in req['data']:
            if i['type'] == s_type:
                return i['record_id']
        return False


class Dns_com(object):
    _type = 0  # 0:lest 1：锐成

    def __init__(self, key, secret):
        pass

    def get_dns_obj(self):
        p_path = '/www/server/panel/plugin/dns'
        if not os.path.exists(p_path + '/dns_main.py'): return None
        sys.path.insert(0, p_path)
        import dns_main
        public.mod_reload(dns_main)
        return dns_main.dns_main()

    def create_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = extract_zone(domain_name)

        if self._type == 1:
            acme_txt = acme_txt.replace('_acme-challenge.', '')
            result = self.add_record(acme_txt + '.' + root, domain_dns_value)
        else:
            result = self.get_dns_obj().add_txt(acme_txt + '.' + root, domain_dns_value)

        if result == "False":
            raise ValueError('[DNS]当前绑定的宝塔DNS云解析账户里面不存在这个域名[{}],添加解析失败!'.format(
                (acme_txt + '.' + root, domain_dns_value)))
        time.sleep(5)

    def delete_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = extract_zone(domain_name)
        self.get_dns_obj().remove_txt(acme_txt + '.' + root)


class DNSLADns(BaseDns):
    dns_provider_name = "dnsla"
    _type = 0  # 0:lest 1：锐成

    def __init__(self, api_id, api_secret):
        self.api_id = api_id
        self.api_secret = api_secret
        self.base_url = "https://api.dns.la"
        self.http_timeout = 65  # seconds
        self._token = None
        self.domain_list = None
        super(DNSLADns, self).__init__()

    @classmethod
    def new(cls, conf_data) -> BaseDns:
        key = conf_data.get("key", None) or conf_data.get("APIID", "")
        secret = conf_data.get("secret", None) or conf_data.get("API密钥", "")

        return cls(key, secret)

    def _get_auth_headers(self) -> dict:
        if self._token is None:
            self._token = base64.b64encode("{}:{}".format(self.api_id, self.api_secret).encode("utf-8")).decode("utf-8")
        return {"Authorization": "Basic " + self._token}

    def find_dns_zone(self, domain_name):
        url = urljoin(self.base_url, "/api/domainList?pageIndex=1&pageSize=1000")
        headers = self._get_auth_headers()
        find_dns_zone_response = requests.get(url, headers=headers, timeout=self.http_timeout)
        if find_dns_zone_response.status_code != 200:
            raise ValueError(
                "Error creating DNS.LA domains: status_code={status_code} response={response}".format(
                    status_code=find_dns_zone_response.status_code,
                    response=self.log_response(find_dns_zone_response),
                )
            )

        result = find_dns_zone_response.json()["data"]["results"]
        self.domain_list = result
        have = False
        for domain_data in result:
            if domain_data["domain"].rstrip(".") == domain_name:
                have = True
                break

        if not have:
            raise ValueError(
                (
                    "Error unable to get DNS zone for domain_name={domain_name}: "
                    "status_code={status_code} response={response}"
                ).format(
                    domain_name=domain_name,
                    status_code=find_dns_zone_response.status_code,
                    response=self.log_response(find_dns_zone_response),
                )
            )

    @staticmethod
    def _format_s_type_to_request(s_type):
        trans = {
            "A": 1,
            "NS": 2,
            "CNAME": 5,
            "MX": 15,
            "TXT": 16,
            "AAAA": 28,
            "SRV": 33,
            "CAA": 257,
            "URL": 256
        }

        if isinstance(s_type, (int, float)):
            if int(s_type) in trans.values():
                return int(s_type)

        if isinstance(s_type, str):
            if s_type in trans:
                return trans[s_type]
        return 16

    def add_record(self, domain, s_type, host, value):
        url = urljoin(self.base_url, "/api/record",)
        headers = self._get_auth_headers()

        domain_id = self._get_domain_id(domain)

        body = {
            "domainId": domain_id,
            "type": self._format_s_type_to_request(s_type),
            "host": host,
            "data": value,
            "ttl": 600,
        }

        create_dns_la_record_response = requests.post(
            url, headers=headers, json=body, timeout=self.http_timeout
        )
        if create_dns_la_record_response.status_code != 200:
            raise ValueError(
                "Error creating cloudflare dns record: status_code={status_code} response={response}".format(
                    status_code=create_dns_la_record_response.status_code,
                    response=self.log_response(create_dns_la_record_response),
                )
            )

    def create_dns_record(self, domain_name, domain_dns_value):
        domain_name = domain_name.lstrip("*.")
        root, zone, acme_txt = extract_zone(domain_name)
        self.find_dns_zone(root)

        if self._type == 1:
            return self.add_record(root, 'CNAME', acme_txt.replace('_acme-challenge.', ''), domain_dns_value)
        else:
            return self.add_record(root, 'TXT', acme_txt, domain_dns_value)

    def add_record_for_creat_site(self, domain, server_ip):
        root, zone, _ = extract_zone(domain)
        self.add_record(root, "A", zone, server_ip)

    def get_record_list(self, domain_id: str) -> list:
        url = urljoin(self.base_url, "/api/recordList?pageIndex=1&pageSize=10&domainId={}".format(domain_id))
        headers = self._get_auth_headers()
        get_record_list_response = requests.get(url, headers=headers, timeout=self.http_timeout)
        if get_record_list_response.status_code != 200:
            raise ValueError(
                "Error unable to get record list : status_code={status_code} response={response}".format(
                    status_code=get_record_list_response.status_code,
                    response=self.log_response(get_record_list_response),
                )
            )

        result = get_record_list_response.json()["data"]["results"]
        if isinstance(result, list):
            return result
        else:
            return []

    def _get_domain_id(self, domain_name: str) -> str:
        if domain_name.count('.') > 2:
            domain_name, _, _ = extract_zone(domain_name)
        if self.domain_list is None:
            self.find_dns_zone(domain_name)
        domain_id = None
        for domain_data in self.domain_list:
            if domain_data["domain"].rstrip(".") == domain_name:
                domain_id = domain_data["id"]
        if domain_id is None:
            raise ValueError("Error unable to get DNS zone for domain_name={domain_name}".format(domain_name=domain_name))
        return domain_id

    def remove_record(self, domain_name, dns_name, s_type):
        domain_id = self._get_domain_id(domain_name)
        record_list = self.get_record_list(domain_id)
        trans_type = self._format_s_type_to_request(s_type)
        remove_record_id_list = []
        for record in record_list:
            if record["type"] == trans_type and (record["host"] == dns_name or record["displayHost"] == dns_name):
                remove_record_id_list.append(record["id"])

        headers = self._get_auth_headers()

        del_record_url_list = [urljoin(self.base_url, "/api/record?id={}".format(i)) for i in remove_record_id_list]

        for del_record_url in del_record_url_list:
            requests.delete(
                del_record_url, headers=headers, timeout=self.http_timeout
            )

    def delete_dns_record(self, domain_name, domain_dns_value):
        domain_name = domain_name.lstrip("*.")
        root, zone, acme_txt = extract_zone(domain_name)
        self.remove_record(root, acme_txt, 'TXT')


class DnsMager(object):
    """
    config = {
        "CloudFlareDns": [
            {
                "E-Mail": "122456944@qq.com",
                "API Key": "dsgvfcdkjausvgfkjasdfgakj",
                "ps": "xxx",
                "id": 1,
                "domains": [  # domains 可以不存在，内容是根域名
                ]
            }
        ]
        ........
    }"""

    CONF_FILE = "{}/config/dns_mager.conf".format(public.get_panel_path())
    CLS_MAP: Dict = {
        "AliyunDns": AliyunDns,
        "DNSPodDns": DNSPodDns,
        "CloudFlareDns": CloudFlareDns,
        "GoDaddyDns": GoDaddyDns,
        "DNSLADns": DNSLADns,
        "HuaweiCloudDns": HuaweiCloudDns,
        # "TencentCloudDns": TencentCloudDns,
    }
    RULE_MAP: Dict[str, List[str]] = {
        "AliyunDns": ["AccessKey", "SecretKey"],
        "DNSPodDns": ["ID", "Token"],
        "CloudFlareDns": ["E-Mail", "API Key"],
        "GoDaddyDns": ["Key", "Secret"],
        "DNSLADns": ["APIID", "API密钥"],
        "HuaweiCloudDns": ["ak", "sk", "project_id"],
        # "TencentCloudDns": ["secret_id", "secret_key"],
    }

    def __init__(self):
        self._config: Optional[Dict[str, Dict[str, Union[int, str]]]] = None

    @staticmethod
    def _get_new_id() -> str:
        return uuid4().hex

    @classmethod
    def _read_config_old(cls) -> Optional[Dict[str, List[Dict[str, Union[str, list]]]]]:
        old_config_file = "{}/config/dns_api.json".format(public.get_panel_path())
        if os.path.isfile(old_config_file):
            try:
                data = json.loads(public.readFile(old_config_file))
            except json.JSONDecodeError:
                return None
            res = {}
            rule_list = ("AliyunDns", "DNSPodDns", "CloudFlareDns", "GoDaddyDns")
            if isinstance(data, list):
                for d in data:
                    if d["name"] not in rule_list:
                        continue

                    conf_data = d.get("data", None)
                    if isinstance(data, list):
                        tmp = {i["name"]: i["value"] for i in conf_data if i["value"].strip()}
                        tmp["ps"] = "默认账户"
                        tmp["id"] = cls._get_new_id()
                        if len(tmp) > 2:
                            res[d["name"]] = [tmp]

            if res:
                return res
        return None

    @staticmethod
    def _get_acme_dns_api() -> Dict[str, Dict[str, str]]:
        path = '/root/.acme.sh'
        if not os.path.exists(path + '/account.conf'):
            path = "/.acme.sh"
        account = public.readFile(path + '/account.conf')
        if not account:
            return {}
        rule_map: Dict[str, Dict[str, str]] = {
            "AliyunDns": {
                "AccessKey": "SAVED_Ali_Key",
                "SecretKey": "SAVED_Ali_Secret",
            },
            "DNSPodDns": {
                "ID": "SAVED_DP_Id",
                "Token": "SAVED_DP_Key"
            },
            "CloudFlareDns": {
                "E-Mail": "SAVED_CF_MAIL",
                "API Key": "SAVED_CF_KEY",
            },
            "GoDaddyDns": {
                "Key": "SAVED_GD_Key",
                "Secret": "SAVED_GD_Secret",
            },
            "DNSLADns": {
                "APIID": "SAVED_LA_Id",
                "API密钥": "SAVED_LA_Key"
            }
        }
        res = {}
        for rule_name, rule in rule_map.items():
            tmp = {}
            for r_key, r_value in rule.items():
                account_res = re.search(r_value + "\s*=\s*'(.+)'", account)
                if account_res:
                    tmp[r_key] = account_res.groups()[0]

            if len(tmp) == len(rule):
                res[rule_name] = tmp
        return res

    @property
    def config(self) -> dict:
        if self._config is not None:
            return self._config

        change = False
        if not os.path.exists(self.CONF_FILE):
            change = True
            old_config = self._read_config_old()
            if old_config is not None:
                self._config = old_config
            else:
                self._config = {}

            l_data = self._get_config_data_from_letsencrypt_data()
            if l_data is not None:
                for tmp_conf in l_data:
                    key = tmp_conf["dns_name"]
                    if key not in self._config:
                        self._config[key] = []
                    for v in self._config[key]:
                        if all([v.get(n, None) == m for n, m in tmp_conf["conf_data"].items()]):
                            break
                    else:
                        tmp_data = {
                            "ps": "配置中的默认账户",
                            "id": self._get_new_id(),
                        }
                        tmp_data.update(tmp_conf["conf_data"])
                        self._config[key].append(tmp_data)
        else:
            try:
                config_data = json.loads(public.readFile(self.CONF_FILE))
            except json.JSONDecodeError:
                self._config = {}
            else:
                if isinstance(config_data, dict):
                    self._config = config_data
                else:
                    self._config = {}

        acme_conf = self._get_acme_dns_api()
        if acme_conf:
            for key, value in acme_conf.items():
                if key not in self._config:
                    self._config[key] = []
                for v in self._config[key]:
                    if all([v.get(n, None) == m for n, m in value.items()]):
                        break
                else:
                    change = True
                    value["ps"] = "检测到的acme_dns"
                    value["id"] = self._get_new_id()
                    self._config[key].append(value)

        if change:
            self.save_config()

        return self._config

    def save_config(self):
        if self._config is None:
            _ = self.config
        public.writeFile(self.CONF_FILE, json.dumps(self._config))

    def get_dns_objs_by_name(self, name) -> List[BaseDns]:
        pass

    def get_dns_obj_by_domain(self, domain) -> BaseDns:
        root, _, _ = extract_zone(domain)
        try:
            data = public.M('ssl_domains').field('dns_id').where("domain=?", (root,)).select()
            dns_id = data[0]['dns_id']
        except:
            dns_id = ''
        for key, value in self.config.items():
            for dns_config in value:
                if root in dns_config.get("domains", []) or str(dns_id) == dns_config["id"]:
                    return self.CLS_MAP[key].new(dns_config)
        raise Exception("没有找到域名为{}的有效的DNS API密钥信息".format(domain))

    def get_dns_by_auth_string(self, auth_string: str) -> BaseDns:
        tmp = auth_string.split('|')
        dns_name = tmp[0]
        if dns_name not in self.CLS_MAP:
            raise Exception("没有找到名为{}的dns验证平台".format(dns_name))
        if len(tmp) >= 3:
            if tmp[2] == "":
                key = None
                secret = tmp[1]
            else:
                key = tmp[1]
                secret = tmp[2]
            return self.CLS_MAP.get(dns_name).new({"key": key, "secret": secret})
        else:
            config_list = self.config.get(dns_name, [])
            if len(config_list) == 0:
                raise Exception("没有找到有效的DNS API密钥信息")
            return self.CLS_MAP.get(dns_name).new(config_list[0])

    def add_conf(self,
                 dns_type: str,
                 conf_data: List[dict],
                 ps: str,
                 domains: List[str],
                 force_domain: Optional[str]
                 ):
        if dns_type not in self.CLS_MAP:
            return False, "不支持的DNS平台"

        f, data = self._parse_data(conf_data, dns_type)
        if not f:
            return False, data

        if not isinstance(domains, list):
            return False, "域名参数格式错误"

        if dns_type not in self.config:
            self.config[dns_type] = []

        for v in self.config[dns_type]:
            if all([v.get(n, None) == m for n, m in data.items()]):
                return False, "该通行凭证已添加过"

        data["ps"] = ps
        data["id"] = self._get_new_id()
        root_list = self.paser_domains_list_to_root_list(domains)
        all_domains = self._get_all_root(with_out=None)
        for root in root_list:
            if root in all_domains:
                return False, "域名{}已绑定其他api账户，不能添加".format(root)

        if force_domain is not None and not isinstance(force_domain, str):
            return False, "域名参数格式错误"
        if force_domain is not None:
            force_root = self.paser_domains_list_to_root_list([force_domain])[0]
            if force_root not in root_list:
                if force_root in all_domains:
                    self.remove_domains_by_root(force_root)

        data["domains"] = root_list
        self.config[dns_type].append(data)
        self.save_config()
        return True, "保存成功"

    def _parse_data(self, conf_data: List[dict], dns_type: str) -> Tuple[bool, Union[dict, str]]:
        data = {}
        if not isinstance(conf_data, list):
            return False, "参数格式错误"
        for conf in conf_data:
            if isinstance(conf, dict) and "name" in conf and "value" in conf:
                data[conf.get("name")] = conf.get("value")
        if not data:
            return False, "参数格式错误,没有指定参数"
        if dns_type == "CloudFlareDns" and len(data) == 1 and "API Token" in data:
            return True, data

        for n in self.RULE_MAP[dns_type]:
            if n not in data:
                return False, "参数格式错误,参数名称与平台不对应"

        return True, data

    def modify_conf(self,
                    api_id: str,
                    dns_type: str,
                    conf_data: Optional[List[Dict]],
                    ps: Optional[str],
                    domains: Optional[List[str]],
                    force_domain: Optional[str]):  # 强制添加的域名

        if dns_type not in self.CLS_MAP:
            return False, "不支持的DNS平台"

        target_idx = -1
        if dns_type not in self.config:
            self.config[dns_type] = []

        for idx, v in enumerate(self.config[dns_type]):
            if api_id == v.get("id", None):
                target_idx = idx

        if target_idx == -1:
            return False, "不存在这个通行凭证"

        if conf_data is not None:
            f, data = self._parse_data(conf_data, dns_type)
            if not f:
                return False, data

            self.config[dns_type][target_idx].update(**data)
            if ps is not None:
                self.config[dns_type][target_idx].update(ps=ps)

        if domains is not None and not isinstance(domains, list):
            return False, "域名参数格式错误"

        if domains is not None:
            root_list = self.paser_domains_list_to_root_list(domains)
            all_domains = self._get_all_root(with_out=self.config[dns_type][target_idx].get("domains"))
            for root in root_list:
                if root in all_domains:
                    return False, "域名{}已绑定其他api账户，不能添加".format(root)
            self.config[dns_type][target_idx]["domains"] = root_list

        if force_domain is not None and not isinstance(force_domain, str):
            return False, "域名参数格式错误"
        if force_domain is not None:
            root = self.paser_domains_list_to_root_list([force_domain])[0]
            self.remove_domains_by_root(root)
            if "domains" not in self.config[dns_type][target_idx]:
                self.config[dns_type][target_idx]["domains"] = []
            self.config[dns_type][target_idx]["domains"].append(root)

        self.save_config()
        return True, "修改成功"

    def remove_domains_by_root(self, root: str):
        for key, value in self.config.items():
            for dns_config in value:
                domains = dns_config.get("domains", None)
                if domains is not None and root in domains:
                    domains.remove(root)

    def _get_all_root(self, with_out: Optional[List[str]]) -> Set[str]:
        all_domains = set(
            chain(*[c.get("domains", []) for c in
                    chain(*[c_list for c_list in self.config.values()])]
                  )
        )
        if with_out is not None:
            return all_domains - set(with_out)
        return all_domains

    def test_domains_api(self, domains: List[str]) -> List[dict]:
        res = [{}] * len(domains)
        for idx, domain in enumerate(domains):
            root = self.paser_domains_list_to_root_list([domain])[0]
            for key, conf in self.config.items():
                for c in conf:
                    if root in c.get("domains", []):
                        res[idx] = {
                            "dns_name": key,
                            "conf": c,
                            "rooot": root,
                            "domain": domain
                        }
        return res

    def remove_conf(self, api_id: str, dns_type: str):
        if dns_type not in self.CLS_MAP:
            return False, "不支持的DNS平台"

        if dns_type not in self.config:
            self.config[dns_type] = []
        target_idx = -1
        for idx, v in enumerate(self.config[dns_type]):
            if api_id == v.get("id", None):
                target_idx = idx

        if target_idx == -1:
            return False, "不存在这个通行凭证"

        del self.config[dns_type][target_idx]
        self.save_config()
        return True, "删除成功"

    @classmethod
    def paser_auth_to(cls, auth_to_string: str) -> Tuple[Optional[str], Optional[Dict[str, str]]]:
        tmp = auth_to_string.split('|')
        dns_name = tmp[0]
        if dns_name not in cls.CLS_MAP:
            return None, None
        if len(tmp) != 3:
            return None, None

        if tmp[2] == "":
            key = None
            secret = tmp[1]
        else:
            key = tmp[1]
            secret = tmp[2]

        if dns_name == "CloudFlareDns" and key is None:
            return "CloudFlareDns", {"API Token": secret}
        elif key and secret:
            return dns_name, dict(zip(cls.RULE_MAP[dns_name], [key, secret]))
        return None, None

    @classmethod
    def paser_domains_list_to_root_list(cls, domains_list: List[str]) -> List[str]:
        res = []
        for domain in domains_list:
            root, _, _ = extract_zone(domain)
            if root in res:
                continue
            res.append(root)
        return res

    @classmethod
    def _get_config_data_from_letsencrypt_data(cls) -> Optional[List[Dict[str, Union[str, list, dict]]]]:
        conf_file = "{}/config/letsencrypt.json".format(public.get_panel_path())
        if not os.path.exists(conf_file):
            return None
        tmp_config = public.readFile(conf_file)
        try:
            orders = json.loads(tmp_config)["orders"]
        except (json.JSONDecodeError, KeyError):
            return None

        res = {}
        for order in orders:
            if 'auth_type' in order and order['auth_type'] == "dns":
                if order["auth_to"].find("|") == -1 or order["auth_to"].find("/") != -1:  # 文件验证跳过
                    continue
                if order["auth_to"] in res:
                    tmp_conf = res[order["auth_to"]]
                else:
                    dns_name, conf_dict = cls.paser_auth_to(order["auth_to"])
                    if dns_name is None:
                        continue
                    tmp_conf = {
                        "dns_name": dns_name,
                        "conf_data": conf_dict,
                        "domains": []
                    }
                    res[order["auth_to"]] = tmp_conf
                root_list = order.get("domains", [])
                for root in root_list:
                    if root not in tmp_conf["domains"]:
                        tmp_conf["domains"].append(root)

        if len(res) == 0:
            return None
        return list(res.values())
