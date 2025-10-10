# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 x3
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: bazoi <bazoi@bt.cn>
# +--------------------------------------------------------------------
# |   宝塔DNS管理平台
# +--------------------------------------------------------------------
import shutil
import sys
import os
import json
import random
import datetime
import hmac
import re
import base64
from urllib.parse import urljoin
from hashlib import sha1
from uuid import uuid4
from itertools import chain
from typing import Set, List, Optional, Union, Dict, Tuple
from mod.base import json_response

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public

try:
    import requests
except:
    public.ExecShell('pip install requests')
    import requests

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
        if domain_name.startswith('*.'):
            domain_name = domain_name[2:]
        return public.split_domain_sld(domain_name)
        # domain_name_copy = domain_name
        # top_domain = "." + ".".join(domain_name.rsplit('.')[-2:])
        # new_top_domain = "." + top_domain.replace(".", "")
        # is_tow_top = False
        # if top_domain in self.top_domain_list:
        #     is_tow_top = True
        #     domain_name = domain_name[:-len(top_domain)] + new_top_domain
        #
        # if domain_name.count(".") <= 1:
        #     zone = ""
        #     root = domain_name_copy
        # else:
        #     zone, middle, last = domain_name.rsplit(".", 2)
        #     if is_tow_top:
        #         last = top_domain[1:]
        #     root = ".".join([middle, last])
        #
        # return root, zone


extract_zone = ExtractZoneTool()


class BaseDns(object):
    def __init__(self):
        self.dns_provider_name = self.__class__.__name__

    @staticmethod
    def load_response(response):
        try:
            log_body = response.json()
        except ValueError:
            log_body = response.content
        return log_body

    def add_record(self, domain: str, host: str, r_type: str, value: str, weight: int = 1, ttl=600):
        raise NotImplementedError("add_record method must be implemented.")

    def remove_record(self, domain: str, host: Optional[str] = None, r_type: Optional[str] = None):
        raise NotImplementedError("remove_record method must be implemented.")

    def modify_record(self, domain: str, host: str, r_type: str, value: str, weight: int = 1, ttl=600):
        raise NotImplementedError("modify_record method must be implemented.")

    def get_record_list(self, domain, host: Optional[str] = None, r_type: Optional[str] = None):
        raise NotImplementedError("get_record_list must be implemented.")

    def get_record_list_by_view(self, domain):
        raise NotImplementedError("get_record_list must be implemented.")

    def get_domain_list(self):
        return []

    @classmethod
    def new(cls, conf_data):
        raise NotImplementedError("new method must be implemented.")

    def transform_record_type(self, r_type: str):
        if r_type not in ("显性URL", "隐性URL"):
            return r_type
        self_cls = self.__class__
        if self_cls is AliyunDns:
            return "REDIRECT_URL" if r_type == "显性URL" else "FORWARD_URL"
        elif self_cls is CloudFlareDns:
            return "URI"


class DNSPodDns(BaseDns):
    dns_provider_name = "dnspod"

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

    def add_record(self, domain: str, host: str, r_type: str, value: str, weight: int = 1, ttl=600):
        url = urljoin(self.DNSPOD_API_BASE_URL, "Record.Create")
        body = {
            "record_type": r_type,
            "domain": domain,
            "sub_domain": host,
            "value": value,
            "record_line_id": "0",
            "format": "json",
            "weight": weight,
            "ttl": ttl,
            "login_token": self.DNSPOD_LOGIN,
        }
        add_response = requests.post(
            url, data=body, timeout=self.HTTP_TIMEOUT
        ).json()
        if add_response["status"]["code"] != "1":
            raise ValueError(
                "Error creating dnspod dns record: status_code={status_code} response={response}".format(
                    status_code=add_response["status"]["code"],
                    response=add_response["status"]["message"],
                )
            )

    def get_record_list_by_view(self, domain):
        records = self.get_record_list(domain)
        if records is None:
            return []
        res = []
        for record in records:
            res.append({
                "host": record['name'],
                "type": record['type'],
                "value": record['value'],
                "ttl": record['ttl'],
                "updated_on": datetime.datetime.strptime(record['updated_on'], "%Y-%m-%d %H:%M:%S").timestamp(),
            })
        return res

    def get_record_list(self, domain, host: Optional[str] = None, r_type: Optional[str] = None):
        url = urljoin(self.DNSPOD_API_BASE_URL, "Record.List")
        body = {
            "login_token": self.DNSPOD_LOGIN,
            "format": "json",
            "domain": domain
        }
        if host is not None and isinstance(host, str):
            body["subdomain"] = host
        if r_type is not None and isinstance(r_type, str):
            body["record_type"] = r_type

        list_response = requests.post(url, data=body, timeout=self.HTTP_TIMEOUT).json()
        if "records" in list_response:
            return list_response["records"]
        else:
            return None

    def remove_record(self, domain, host: Optional[str] = None, r_type: Optional[str] = None):
        records = self.get_record_list(domain, host, r_type)
        if records is None:
            return False, "未查询到记录信息，没有执行删除"
        for record in records:
            if record['name'] != host or record['type'] != r_type:
                continue
            record_id = record["id"]
            url = urljoin(self.DNSPOD_API_BASE_URL, "Record.Remove")
            body = {
                "login_token": self.DNSPOD_LOGIN,
                "format": "json",
                "domain": domain,
                "record_id": record_id,
            }
            requests.post(
                url, data=body, timeout=self.HTTP_TIMEOUT
            ).json()

        return True, "删除成功"

    def modify_record(self, domain: str, host: str, r_type: str, value: str, weight: int = 1, ttl=600):
        records = self.get_record_list(domain, host, r_type)
        if records is None:
            return False, "未查询到记录信息，无法执行修改"

        for record in records:
            if record['name'] != host and record['type'] != r_type:
                continue

            record_id = record["id"]
            url = urljoin(self.DNSPOD_API_BASE_URL, "Record.Modify")
            body = {
                "record_type": r_type,
                "record_id": record_id,
                "domain": domain,
                "sub_domain": host,
                "value": value,
                "record_line_id": "0",
                "format": "json",
                "weight": weight,
                "ttl": ttl,
                "login_token": self.DNSPOD_LOGIN,
            }
            add_response = requests.post(
                url, data=body, timeout=self.HTTP_TIMEOUT
            ).json()

            if add_response["status"]["code"] != "1":
                raise ValueError(
                    "Error creating dnspod dns record: status_code={status_code} response={response}".format(
                        status_code=add_response["status"]["code"],
                        response=add_response["status"]["message"],
                    )
                )

    def get_domain_list(self):
        url = urljoin(self.DNSPOD_API_BASE_URL, "Domain.List")
        body = {
            "format": "json",
            "login_token": self.DNSPOD_LOGIN,
        }
        domain_list_resp = requests.post(
            url, data=body, timeout=self.HTTP_TIMEOUT
        ).json()
        if domain_list_resp["status"]["code"] != "1":
            return {}
        domains = domain_list_resp["domains"]
        return {d["name"]: d for d in domains}

    @classmethod
    def new(cls, conf_data: dict) -> BaseDns:
        key = conf_data.get("key", None) or conf_data.get("ID", "")
        secret = conf_data.get("secret", None) or conf_data.get("Token", "")
        base_url = "https://dnsapi.cn/"

        return cls(key, secret, base_url)


class CloudFlareDns(BaseDns):
    dns_provider_name = "cloudflare"

    def __init__(
            self,
            CLOUDFLARE_EMAIL,
            CLOUDFLARE_API_KEY,
            CLOUDFLARE_API_BASE_URL="https://api.cloudflare.com/client/v4/",
    ):
        self.CLOUDFLARE_EMAIL = CLOUDFLARE_EMAIL
        self.CLOUDFLARE_API_KEY = CLOUDFLARE_API_KEY
        self.CLOUDFLARE_API_BASE_URL = CLOUDFLARE_API_BASE_URL
        self.HTTP_TIMEOUT = 65  # seconds

        self._domain_zone_id_cache = {}

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

    def find_dns_zone(self, domain):
        for domain_key, zone_id in self._domain_zone_id_cache.items():
            if domain_key in domain:
                return self._domain_zone_id_cache[domain_key]

        url = urljoin(self.CLOUDFLARE_API_BASE_URL, "zones?status=active&per_page=1000")
        headers = self._get_auth_headers()
        find_dns_zone_response = requests.get(url, headers=headers, timeout=self.HTTP_TIMEOUT)
        if find_dns_zone_response.status_code != 200:
            raise ValueError(
                "Error creating cloudflare dns record: status_code={status_code} response={response}".format(
                    status_code=find_dns_zone_response.status_code,
                    response=self.load_response(find_dns_zone_response),
                )
            )

        result = find_dns_zone_response.json()["result"]
        self._domain_zone_id_cache = {}
        for i in result:
            self._domain_zone_id_cache[i["name"]] = i["id"]

        for domain_key, zone_id in self._domain_zone_id_cache.items():
            if domain_key in domain:
                return self._domain_zone_id_cache[domain_key]

        raise ValueError(
            ("Error unable to get DNS zone for domain_name={domain_name}: "
             "status_code={status_code} response={response}").format(
                domain_name=domain,
                status_code=find_dns_zone_response.status_code,
                response=self.load_response(find_dns_zone_response),
            )
        )

    def get_domain_list(self):
        url = urljoin(self.CLOUDFLARE_API_BASE_URL, "zones?status=active&per_page=1000")
        headers = self._get_auth_headers()
        find_dns_zone_response = requests.get(url, headers=headers, timeout=self.HTTP_TIMEOUT)
        if find_dns_zone_response.status_code != 200:
            return {}
        domains = find_dns_zone_response.json()["result"]
        return {d["name"]: d for d in domains}

    def add_record(self, domain: str, host: str, r_type: str, value: str, weight: int = 1, ttl=600):
        zone_id = self.find_dns_zone(domain)
        url = urljoin(
            self.CLOUDFLARE_API_BASE_URL,
            "zones/{0}/dns_records".format(zone_id),
        )
        headers = self._get_auth_headers()
        body = {
            "type": r_type,
            "name": host,
            "content": "{0}".format(value),
            "ttl": ttl
        }

        create_cloudflare_dns_record_response = requests.post(
            url, headers=headers, json=body, timeout=self.HTTP_TIMEOUT
        )
        if create_cloudflare_dns_record_response.status_code != 200:
            raise ValueError(
                "Error creating cloudflare dns record: status_code={status_code} response={response}".format(
                    status_code=create_cloudflare_dns_record_response.status_code,
                    response=self.load_response(create_cloudflare_dns_record_response),
                )
            )

    def get_record_list_by_view(self, domain):
        records = self.get_record_list(domain)
        if records is None:
            return []
        res = []
        for record in records:
            res.append({
                "host": record['name'],
                "type": record['type'],
                "value": record['content'],
                "ttl": record['ttl'],
                "modified_on": datetime.datetime.strptime(record['updated_on'], "%Y-%m-%dT%H:%M:%S.%fZ").timestamp(),
            })
        return res

    def get_record_list(self, domain, host: Optional[str] = None, r_type: Optional[str] = None):
        zone_id = self.find_dns_zone(domain)
        list_dns_url = urljoin(
            self.CLOUDFLARE_API_BASE_URL,
            "zones/{0}/dns_records?per_page=50000".format(zone_id),
        )
        list_dns_payload = {}
        if host is not None and isinstance(host, str):
            list_dns_payload["name"] = host
        if r_type is not None and isinstance(r_type, str):
            list_dns_payload["type"] = r_type

        headers = self._get_auth_headers()
        list_response = requests.get(
            list_dns_url, params=list_dns_payload, headers=headers, timeout=self.HTTP_TIMEOUT
        ).json()
        if "success" and list_response["success"] is False:
            return None
        if "result" in list_response:
            return list_response["result"]
        else:
            return None

    def remove_record(self, domain: str, host: Optional[str] = None, r_type: Optional[str] = None):
        headers = self._get_auth_headers()
        zone_id = self.find_dns_zone(domain)
        records = self.get_record_list(domain, host, r_type)
        if records is None:
            return False, "未查询到记录信息，无法执行修改"

        for record in records:
            if record['name'] != host or record['type'] != r_type:
                continue
            dns_record_id = record["id"]
            url = urljoin(
                self.CLOUDFLARE_API_BASE_URL,
                "zones/{0}/dns_records/{1}".format(zone_id, dns_record_id),
            )
            requests.delete(
                url, headers=headers, timeout=self.HTTP_TIMEOUT
            )

    def modify_record(self, domain: str, host: str, r_type: str, value: str, weight: int = 1, ttl=600):
        records = self.get_record_list(domain, host, r_type)
        if records is None:
            return False, "未查询到记录信息，无法执行修改"

        headers = self._get_auth_headers()
        zone_id = self.find_dns_zone(domain)

        for record in records:
            if record['name'] != host and record['type'] != r_type:
                continue

            record_id = record["id"]
            url = urljoin(
                self.CLOUDFLARE_API_BASE_URL,
                "zones/{0}/dns_records/{1}".format(zone_id, record_id),
            )

            body = {
                "type": r_type,
                "name": host,
                "content": "{0}".format(value),
                "ttl": ttl
            }
            modify_response = requests.put(
                url, data=body, timeout=self.HTTP_TIMEOUT, headers=headers
            ).json()

            if modify_response.status_code != 200:
                raise ValueError(
                    "Error creating cloudflare dns record: status_code={status_code} response={response}".format(
                        status_code=modify_response.status_code,
                        response=self.load_response(modify_response),
                    )
                )

    @classmethod
    def new(cls, conf_data: dict) -> BaseDns:
        key = conf_data.get("key", None) or conf_data.get("E-Mail", None)
        secret = conf_data.get("secret", None) or conf_data.get("API Key", None)
        base_url = "https://api.cloudflare.com/client/v4/"

        if key is None and secret is None:
            secret = conf_data.get("API Token", None)  # 处理api - token的情况
        if key is None and secret is None:
            raise Exception("没有找到有效的DNS API密钥信息")
        return cls(key, secret, base_url)


class AliyunDns(BaseDns):
    dns_provider_name = "alidns"

    def __init__(self, key, secret):
        self.key = str(key).strip()
        self.secret = str(secret).strip()
        self.url = "https://alidns.aliyuncs.com"
        super(AliyunDns, self).__init__()

    def sign(self, accessKeySecret, parameters):  # '''签名方法
        def percent_encode(encodeStr):
            import urllib.request
            encodeStr = str(encodeStr)
            res = urllib.request.quote(encodeStr, '')
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
        signature = base64.encodebytes(h.digest()).strip()
        return signature

    def add_record(self, domain: str, host: str, r_type: str, value: str, weight: int = 1, ttl=600):
        random_int = random.randint(11111111111111, 99999999999999)
        now = datetime.datetime.utcnow()
        otherStyleTime = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        paramsdata = {
            "Action": "AddDomainRecord",
            "Format": "json",
            "Version": "2015-01-09",
            "SignatureMethod": "HMAC-SHA1",
            "Timestamp": otherStyleTime,
            "SignatureVersion": "1.0",
            "SignatureNonce": str(random_int),
            "AccessKeyId": self.key,
            "DomainName": domain,
            "RR": host,
            "Type": r_type,
            "Value": value,
            "TTL": ttl,
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

    def get_record_list(self, domain, host: Optional[str] = None, r_type: Optional[str] = None):
        random_int = random.randint(11111111111111, 99999999999999)
        now = datetime.datetime.utcnow()
        otherStyleTime = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        params_data = {
            "Action": "DescribeDomainRecords",
            "Format": "json",
            "Version": "2015-01-09",
            "SignatureMethod": "HMAC-SHA1",
            "Timestamp": otherStyleTime,
            "SignatureVersion": "1.0",
            "SignatureNonce": str(random_int),
            "AccessKeyId": self.key,
            "DomainName": domain,
            "PageNumber": 1,
            "PageSize": 1000,
        }
        if host is not None and isinstance(host, str):
            params_data["RRKeyWord"] = host
        if r_type is not None and isinstance(r_type, str):
            params_data["TypeKeyWord"] = r_type

        Signature = self.sign(self.secret, params_data)
        params_data['Signature'] = Signature
        req_data = requests.get(url=self.url, params=params_data).json()
        record_list = req_data.get("DomainRecords", {}).get("Record", [])
        return record_list

    def get_record_list_by_view(self, domain):
        records = self.get_record_list(domain)
        if records is None:
            return []
        res = []
        for record in records:
            res.append({
                "host": record['RR'],
                "type": record['Type'],
                "value": record['Value'],
                "ttl": record['ttl'],
                "modified_on": record['UpdateTimestamp'],
            })
        return res

    def remove_record(self, domain: str, host: Optional[str] = None, r_type: Optional[str] = None):
        records = self.get_record_list(domain, host, r_type)
        if records is None:
            return False, "未查询到记录信息，无法执行修改"

        random_int = random.randint(11111111111111, 99999999999999)
        now = datetime.datetime.utcnow()
        otherStyleTime = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        params_data = {
            "Action": "DeleteDomainRecord",
            "Format": "json",
            "Version": "2015-01-09",
            "SignatureMethod": "HMAC-SHA1",
            "Timestamp": otherStyleTime,
            "SignatureVersion": "1.0",
            "SignatureNonce": str(random_int),
            "AccessKeyId": self.key,
            "RecordId": None,
        }
        for record in records:
            if record['RR'] != host or record['Type'] != r_type:
                continue
            record_id = record["RecordId"]
            p_data = params_data.copy()
            p_data["RecordId"] = record_id

            Signature = self.sign(self.secret, p_data)
            p_data['Signature'] = Signature
            req = requests.get(url=self.url, params=p_data)
            if req.status_code != 200:
                raise ValueError("删除解析记录失败")

    def modify_record(self, domain: str, host: str, r_type: str, value: str, weight: int = 1, ttl=600):
        records = self.get_record_list(domain, host, r_type)
        if records is None:
            return False, "未查询到记录信息，无法执行修改"

        random_int = random.randint(11111111111111, 99999999999999)
        now = datetime.datetime.utcnow()
        otherStyleTime = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        params_data = {
            "Action": "UpdateDomainRecord",
            "Format": "json",
            "Version": "2015-01-09",
            "SignatureMethod": "HMAC-SHA1",
            "Timestamp": otherStyleTime,
            "SignatureVersion": "1.0",
            "SignatureNonce": str(random_int),
            "AccessKeyId": self.key,
            "RR": host,
            "Type": r_type,
            "Value": value,
            "TTL": ttl,
            "RecordId": None
        }

        for record in records:
            if record['RR'] != host and record['Type'] != r_type:
                continue

            record_id = record["RecordId"]
            p_data = params_data.copy()
            p_data["RecordId"] = record_id

            Signature = self.sign(self.secret, p_data)
            p_data['Signature'] = Signature
            req = requests.get(url=self.url, params=p_data)
            if req.status_code != 200:
                if req.json()['Code'] == 'IncorrectDomainUser' or req.json()['Code'] == 'InvalidDomainName.NoExist':
                    raise ValueError("这个阿里云账户下面不存在这个域名，添加解析失败")
                elif req.json()['Code'] == 'InvalidAccessKeyId.NotFound' or req.json()['Code'] == 'SignatureDoesNotMatch':
                    raise ValueError("API密钥错误，添加解析失败")
                else:
                    raise ValueError(req.json()['Message'])

    def get_domain_list(self):
        random_int = random.randint(11111111111111, 99999999999999)
        now = datetime.datetime.utcnow()
        otherStyleTime = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        paramsdata = {
            "Action": "DescribeDomains",
            "Format": "json",
            "Version": "2015-01-09",
            "SignatureMethod": "HMAC-SHA1",
            "Timestamp": otherStyleTime,
            "SignatureVersion": "1.0",
            "SignatureNonce": str(random_int),
            "AccessKeyId": self.key,
            "PageNumber": 1,
            "PageSize": 1000,
        }

        Signature = self.sign(self.secret, paramsdata)
        paramsdata['Signature'] = Signature
        req = requests.get(url=self.url, params=paramsdata)
        if req.status_code != 200:
            req_json = req.json()
            if req_json['Code'] == 'IncorrectDomainUser' or req_json['Code'] == 'InvalidDomainName.NoExist':
                raise ValueError("这个阿里云账户下面不存在这个域名，添加解析失败")
            elif req_json['Code'] == 'InvalidAccessKeyId.NotFound' or req_json['Code'] == 'SignatureDoesNotMatch':
                raise ValueError("API密钥错误，添加解析失败")
            else:
                raise ValueError(req_json['Message'])

        domains = req.json()["Domains"]["Domain"]
        return {d["DomainName"]: d for d in domains}

    @classmethod
    def new(cls, conf_data: dict) -> "AliyunDns":
        key = conf_data.get("key", None) or conf_data.get("AccessKey", "")
        secret = conf_data.get("secret", None) or conf_data.get("SecretKey", "")

        return cls(key, secret)


# 未完善请勿使用
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


    def add_record(self, domain: str, host: str, r_type: str, value: str, weight: int = 1, ttl=600):
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
                    response=self.load_response(create_cloudflare_dns_record_response),
                )
            )

    def modify_record(self, domain: str, host: str, r_type: str, value: str, weight: int = 1, ttl=600):
        pass


    def remove_record(self, domain: str, host: Optional[str] = None, r_type: Optional[str] = None):
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
                    response=self.load_response(dns_response),
                )
            )

    def get_record_list(self, domain, host: Optional[str] = None, r_type: Optional[str] = None):
        pass

    def get_record_list_by_view(self, domain):
        pass


    @classmethod
    def new(cls, conf_data: dict) -> BaseDns:
        key = conf_data.get("key", None) or conf_data.get("Key", "")
        secret = conf_data.get("secret", None) or conf_data.get("Secret", "")
        base_url = "https://api.godaddy.com"

        return cls(key, secret, base_url)


# 未上线
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
                    response=self.load_response(find_dns_zone_response),
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
                    response=self.load_response(find_dns_zone_response),
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
        url = urljoin(self.base_url, "/api/record", )
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
                    response=self.load_response(create_dns_la_record_response),
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
                    response=self.load_response(get_record_list_response),
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
            raise ValueError(
                "Error unable to get DNS zone for domain_name={domain_name}".format(domain_name=domain_name))
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


class DomainListCache(object):
    _CACHE_TIP = '{}/plugin/dns_api_manager/cache.tip'.format(public.get_panel_path())
    _CACHE_DATA = '{}/plugin/dns_api_manager/cache.json'.format(public.get_panel_path())

    def __init__(self):
        self._cache = None
        self.read()

    def clear(self):
        self._cache = {}
        if os.path.exists(self._CACHE_DATA):
            os.remove(self._CACHE_DATA)

    def set(self, cache_id, data: dict):
        self._cache[cache_id] = data

    def get(self, cache_id):
        if cache_id in self._cache:
            return self._cache[cache_id]
        return None

    def save(self):
        now = int(datetime.datetime.now().timestamp())
        if self._cache:
            res = public.writeFile(self._CACHE_DATA, json.dumps(self._cache))
            public.writeFile(self._CACHE_TIP, str(now + 60 * 60))

    def _remove_cache(self):
        now = int(datetime.datetime.now().timestamp())
        last = int(public.ReadFile(self._CACHE_TIP))
        if last < now:
            if os.path.exists(self._CACHE_DATA):
                os.remove(self._CACHE_DATA)

    def read(self):
        self._remove_cache()
        if not os.path.exists(self._CACHE_DATA):
            self._cache = {}

        try:
            data = json.loads(public.readFile(self._CACHE_DATA))
            if not isinstance(data, dict):
                data = {}
        except:
            data = {}

        self._cache = data


class RealDnsMager(object):
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
    }

    NOT_USED_LIST: list = ["GoDaddyDns", "DNSLADns"]

    RULE_MAP: Dict[str, List[str]] = {
        "AliyunDns": ["AccessKey", "SecretKey"],
        "DNSPodDns": ["ID", "Token"],
        "CloudFlareDns": ["E-Mail", "API Key"],
        "GoDaddyDns": ["Key", "Secret"],
        "DNSLADns": ["APIID", "API密钥"]
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

    def get_dns_obj_by_domain(self, domain) -> BaseDns:
        root, _ = extract_zone(domain)
        for key, value in self.config.items():
            for dns_config in value:
                if root in dns_config.get("domains", []):
                    return self.CLS_MAP[key].new(dns_config)
        raise Exception("没有找到域名为{}的有效的DNS API密钥信息".format(domain))

    def add_conf(self,
                 dns_type: str,
                 conf_data: List[dict],
                 ps: str,
                 domains: List[str],
                 force_domain: Optional[str]):

        if dns_type in self.NOT_USED_LIST:
            return False, "当前DNS平台还未完全支持，请等待后续更新"

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
                data[conf.get("name")] = str(conf.get("value")).strip()
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

        if dns_type in self.NOT_USED_LIST:
            return False, "当前DNS平台还未完全支持，请等待后续更新"

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
        if dns_type in self.NOT_USED_LIST:
            return False, "当前DNS平台还未完全支持，请等待后续更新"

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
            root, _ = extract_zone(domain)
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


class DNSApiManager:
    _DEFAULT_ERROR = (
        "执行中发生了错误，您可以尝试：<br>"
        "1. 检查API通行证是否有效，或是否填写错误<br>"
        "2. 检查域名是否托管在该平台下<br>"
        "3. 检查解析值是否正确<br>"
    )

    def __init__(self):
        pass

    @staticmethod
    def get_dns_api_conf(get=None):
        api_init = '{}/config/dns_api_init_v2.json'.format(public.get_panel_path())

        apis = json.loads(public.ReadFile(api_init))
        m = RealDnsMager()
        result = []

        for data in apis:
            if data["name"] == "dns":
                continue
            if data["name"] in m.NOT_USED_LIST:
                continue
            if data["name"] in m.CLS_MAP:
                conf_list = m.config.get(data["name"], None)
                tmp = []
                if conf_list:
                    for conf in conf_list:
                        tmp_dict = {
                            "ps": conf.pop("ps", ""),
                            "domains": conf.pop("domains", []),
                            "id": conf.pop("id")
                        }
                        for table in data["add_table"]:
                            if table["fields"][0] in conf:
                                tmp_dict["conf"] = [{"name": f, "value": conf.get(f, "")} for f in table["fields"]]
                        if "conf" in tmp_dict:
                            tmp.append(tmp_dict)
                data["data"] = tmp
                result.append(data)

        return json_response(status=True, data=result)

    @staticmethod
    def add_dns_api(get):
        try:
            dns_type = get.dns_type.strip()
            ps = get.ps.strip()
            conf_data = json.loads(get.pdata.strip())
            domains = json.loads(get.domains.strip())
            force_domain = None
            if "force_domain" in get:
                force_domain = get.force_domain.strip()
        except (json.JSONDecodeError, AttributeError, KeyError):
            return json_response(status=False, msg="参数错误")

        f, msg = RealDnsMager().add_conf(dns_type, conf_data, ps, domains, force_domain)
        return json_response(status=f, msg=msg)

    @staticmethod
    def set_dns_api(get):
        try:
            dns_type = get.dns_type.strip()
            api_id = get.api_id.strip()
            ps = None
            conf_data = None
            domains = None
            force_domain = None
            if "ps" in get:
                ps = get.ps.strip()
            if "force_domain" in get:
                force_domain = get.force_domain.strip()
            if "pdata" in get:
                conf_data = json.loads(get.pdata.strip())
            if "domains" in get:
                domains = json.loads(get.domains.strip())
        except (json.JSONDecodeError, AttributeError, KeyError):
            return json_response(status=False, msg="参数错误")
        try:
            f, msg = RealDnsMager().modify_conf(api_id, dns_type, conf_data, ps, domains, force_domain)
            return json_response(status=f, msg=msg)
        except:
            public.print_log(public.get_error_info())

    @staticmethod
    def remove_dns_api(get):
        try:
            dns_type = get.dns_type.strip()
            api_id = get.api_id.strip()
        except (json.JSONDecodeError, AttributeError, KeyError):
            return json_response(status=False, msg="参数错误")
        f, msg = RealDnsMager().remove_conf(api_id, dns_type)
        return json_response(status=f, msg=msg)

    @staticmethod
    def remove_domain(get):
        try:
            domain = get.domain.strip()
        except (json.JSONDecodeError, AttributeError, KeyError):
            return json_response(status=False, msg="参数错误")
        root, _ = extract_zone(domain)
        m = RealDnsMager()
        m.remove_domains_by_root(root)
        m.save_config()
        return json_response(status=True, msg="删除成功")

    def query_dns(self, get):
        domain = get.domain
        dns_type = get.dns_type
        res = public.query_dns(domain, dns_type)
        if not res:
            return json_response(status=False, msg="参数错误")

        return json_response(status=True, data=res)

    @staticmethod
    def get_record_list(get):
        """
        获取解析记录列表
        """
        try:
            domain = get.domain.strip()
        except (json.JSONDecodeError, AttributeError, KeyError):
            return json_response(status=False, msg="参数错误")

        m = RealDnsMager()
        try:
            dns_onj = m.get_dns_obj_by_domain(domain)
            return json_response(status=True, data=dns_onj.get_record_list_by_view(domain))
        except Exception as e:
            return json_response(status=False, msg=str(e))

    @classmethod
    def create_record(cls, get):
        """
        @创建解析记录
        """
        try:
            domain = get.domain.strip()
            host = get.host.strip()
            r_type = get.r_type.strip()
            value = get.value.strip()
            ttl = int(get.ttl.strip())
        except (json.JSONDecodeError, AttributeError, KeyError):
            return json_response(status=False, msg="参数错误")
        domain, _ = extract_zone(domain)

        try:
            m = RealDnsMager()
            dns_obj = m.get_dns_obj_by_domain(domain)
            r_type = dns_obj.transform_record_type(r_type)
            dns_obj.add_record(domain, host, r_type, value, ttl=ttl)
            return json_response(status=True, msg="添加成功")
        except:
            # return public.returnMsg(False, public.get_error_info())
            return json_response(status=False, msg=cls._DEFAULT_ERROR)

    @classmethod
    def delete_record(cls, get):
        """
        @删除解析记录
        @domain	String	解析记录所在的域名
        @recordId   Int	解析记录 ID
        """
        try:
            domain = get.domain.strip()
            host = get.host.strip()
            r_type = get.r_type.strip()
        except (json.JSONDecodeError, AttributeError, KeyError):
            return json_response(status=False, msg="参数错误")
        domain, _ = extract_zone(domain)

        try:
            m = RealDnsMager()
            dns_obj = m.get_dns_obj_by_domain(domain)
            dns_obj.remove_record(domain, host, r_type)
            return json_response(status=True, msg="删除成功")
        except:
            # return public.returnMsg(False, public.get_error_info())
            return json_response(status=False, msg=cls._DEFAULT_ERROR)

    @staticmethod
    def get_domain_list(get=None):
        """
        @name 获取域名列表
        @param search 搜索关键字
        """
        res = []
        cache = DomainListCache()
        cache_change = False
        domain_change = False
        m = RealDnsMager()
        for key, value in m.config.items():
            if key in m.NOT_USED_LIST:
                continue
            for dns_config in value:
                config_id = dns_config["id"]
                dns_obj: BaseDns = m.CLS_MAP[key].new(dns_config)
                cloud_domain_data = cache.get(config_id)
                if cloud_domain_data is None:
                    try:
                        cloud_domain_data = dns_obj.get_domain_list()
                    except Exception:
                        public.print_log(public.get_error_info())
                        cloud_domain_data = {}
                    cache_change = True
                    cache.set(config_id, cloud_domain_data)

                if "domains" not in dns_config:
                    dns_config['domains'] = []

                domains = dns_config.get("domains")
                for d in domains:
                    tmp = {
                        "name": d,
                        "api_id": config_id,
                        "api_type": key,
                        "cloud_have": False,
                        "ps": dns_config["ps"]
                    }
                    if d in cloud_domain_data:
                        tmp["cloud_have"] = True

                    res.append(tmp)

                for cloud_d in cloud_domain_data.keys():
                    if cloud_d not in domains:
                        m.remove_domains_by_root(cloud_d)  # 删除其他地方的数据
                        dns_config["domains"].append(cloud_d)
                        domain_change = True
                        res.append({
                            "name": cloud_d,
                            "api_id": config_id,
                            "api_type": key,
                            "cloud_have": True,
                            "ps": dns_config["ps"]
                        })

        if cache_change:
            cache.save()

        if domain_change:
            m.save_config()

        return json_response(status=True, data=res)
