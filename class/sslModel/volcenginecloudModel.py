# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: cjxin <cjxin@bt.cn>
# -------------------------------------------------------------------
# 火山引擎 DNS API
# -------------------------------------------------------------------

import json
import sys
import hashlib
import hmac
import time
from datetime import datetime
from urllib.parse import quote, urlencode

import public
import requests
from sslModel.base import sslBase


class main(sslBase):
    dns_provider_name = "volcenginecloud"
    _type = 0

    def __init__(self):
        super().__init__()
        self.endpoint = "dns.volcengineapi.com"
        self.service = "DNS"
        self.region = "cn-beijing"
        self.algorithm = "HMAC-SHA256"
        self.version = "2018-08-01"

    def __init_data(self, data):
        self.access_key = data["AccessKey"]
        self.secret_key = data["SecretKey"]

    def _hash_sha256(self, data):
        """计算SHA256哈希值"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha256(data).hexdigest()

    def _hmac_sha256(self, key, data):
        """计算HMAC-SHA256"""
        if isinstance(key, str):
            key = key.encode('utf-8')
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hmac.new(key, data, hashlib.sha256).digest()

    def _get_signature_key(self, key, date, region, service):
        """获取签名密钥"""
        k_date = self._hmac_sha256(key, date)
        k_region = self._hmac_sha256(k_date, region)
        k_service = self._hmac_sha256(k_region, service)
        k_signing = self._hmac_sha256(k_service, "request")
        return k_signing

    def _sign(self, key, msg):
        """签名函数"""
        return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).hexdigest()

    def _quote(self, value):
        """URL编码"""
        return quote(str(value), safe='~')

    def sign_request(self, dns_id, action, payload, method="POST"):
        """生成签名请求"""
        self.__init_data(self.get_dns_data(None)[dns_id])

        # 时间戳
        t = datetime.utcnow()
        amz_date = t.strftime('%Y%m%dT%H%M%SZ')
        date_stamp = t.strftime('%Y%m%d')

        # Query参数 - Action和Version必须在URL中
        query_params = {
            "Action": action,
            "Version": self.version
        }

        # 规范化查询字符串
        canonical_querystring = "&".join(
            "{}={}".format(self._quote(k), self._quote(v))
            for k, v in sorted(query_params.items())
        )

        # 规范请求
        canonical_uri = "/"
        content_type = "application/json"

        # 规范头部
        canonical_headers = "content-type:{}\nhost:{}\nx-content-sha256:{}\nx-date:{}\n".format(
            content_type, self.endpoint, self._hash_sha256(payload), amz_date
        )
        signed_headers = "content-type;host;x-content-sha256;x-date"

        # 规范请求
        payload_hash = self._hash_sha256(payload)
        canonical_request = "{}\n{}\n{}\n{}\n{}\n{}".format(
            method, canonical_uri, canonical_querystring,
            canonical_headers, signed_headers, payload_hash
        )

        # 待签名字符串
        credential_scope = "{}/{}/{}/request".format(date_stamp, self.region, self.service)
        string_to_sign = "{}\n{}\n{}\n{}".format(
            self.algorithm, amz_date, credential_scope, self._hash_sha256(canonical_request)
        )

        # 计算签名
        signing_key = self._get_signature_key(self.secret_key, date_stamp, self.region, self.service)
        signature = self._sign(signing_key, string_to_sign)

        # 授权头
        authorization_header = "{} Credential={}/{}, SignedHeaders={}, Signature={}".format(
            self.algorithm, self.access_key, credential_scope, signed_headers, signature
        )

        headers = {
            "Content-Type": content_type,
            "Host": self.endpoint,
            "X-Date": amz_date,
            "X-Content-Sha256": payload_hash,
            "Authorization": authorization_header,
        }

        # 构建完整URL
        url = "https://{}?{}".format(self.endpoint, canonical_querystring)

        return url, headers

    def create_dns_record(self, get):
        """创建DNS记录"""
        domain_name = get.domain_name
        domain_dns_value = get.domain_dns_value
        remark = get.get("remark", "")
        record_type = 'TXT'
        if 'record_type' in get:
            record_type = get.record_type

        if record_type == 'MX':
            if not domain_dns_value.split(' ')[0].isdigit():
                if not get.get('mx'):
                    return public.returnMsg(False, 'MX记录类型必须填写MX值')
                try:
                    mx = int(get.mx)
                except:
                    mx = 10
                domain_dns_value = "{} {}".format(mx, domain_dns_value)

        root_domain, sub_domain, _ = self.extract_zone(domain_name)

        try:
            # 获取ZoneID
            zone_id = self._get_zone_id(get.dns_id, root_domain)
            if not zone_id:
                return public.returnMsg(False, '未找到该域名的Zone信息')

            params = json.dumps({
                "ZID": int(zone_id),
                "Host": sub_domain if sub_domain else "@",
                "Type": record_type,
                "Value": domain_dns_value,
                "Remark": remark,
                "TTL": 600,
            })

            url, headers = self.sign_request(get.dns_id, "CreateRecord", params)
            res = requests.post(url, headers=headers, data=params).json()

            if "ResponseMetadata" in res and "Error" in res["ResponseMetadata"]:
                return public.returnMsg(False, res["ResponseMetadata"]["Error"]["Message"])

            return public.returnMsg(True, '添加成功')
        except Exception as e:
            return public.returnMsg(False, self.get_error(str(e)))

    def delete_dns_record(self, get):
        """删除DNS记录"""
        RecordId = get.RecordId
        domain_name = get.domain_name
        root_domain, _, _ = self.extract_zone(domain_name)

        try:
            zone_id = self._get_zone_id(get.dns_id, root_domain)
            if not zone_id:
                return public.returnMsg(False, '未找到该域名的Zone信息')

            params = json.dumps({
                "ZID": int(zone_id),
                "RecordID": RecordId
            })

            url, headers = self.sign_request(get.dns_id, "DeleteRecord", params)
            res = requests.post(url, headers=headers, data=params).json()

            if "ResponseMetadata" in res and "Error" in res["ResponseMetadata"]:
                return public.returnMsg(False, res["ResponseMetadata"]["Error"]["Message"])

            return public.returnMsg(True, '删除成功')
        except Exception as e:
            return public.returnMsg(False, self.get_error(str(e)))

    def _get_zone_id(self, dns_id, domain_name):
        """获取域名的ZoneID"""
        params = json.dumps({})
        url, headers = self.sign_request(dns_id, "ListZones", params)
        res = requests.post(url, headers=headers, data=params).json()

        if "ResponseMetadata" in res and "Error" in res["ResponseMetadata"]:
            return None

        zones = res.get("Result", {}).get("Zones", [])
        for zone in zones:
            if zone.get("ZoneName") == domain_name:
                return zone.get("ZID")

        return None

    def get_dns_record(self, get):
        """获取DNS记录列表"""
        domain_name = get.domain_name
        root_domain, _, sub_domain = self.extract_zone(domain_name)
        data = {}

        try:
            zone_id = self._get_zone_id(get.dns_id, root_domain)
            if not zone_id:
                public.print_log("未找到域名{}的Zone信息".format(root_domain), "ERROR")
                return {}

            params_data = {
                "ZID": int(zone_id),
            }
            if "limit" in get:
                params_data["PageSize"] = int(get.limit)
            if "p" in get:
                params_data["PageNumber"] = int(get.p)
            if "search" in get and get.search:
                params_data["SearchMode"] = "like"
                params_data["Host"] = get.search

            params = json.dumps(params_data)
            url, headers = self.sign_request(get.dns_id, "ListRecords", params)
            res = requests.post(url, headers=headers, data=params).json()

            if "ResponseMetadata" in res and "Error" in res["ResponseMetadata"]:
                public.print_log("获取DNS记录失败: {}".format(res["ResponseMetadata"]["Error"]["Message"]), "ERROR")
                return {}

            result = res.get("Result", {})
            records = result.get("Records", []) or []

            data["list"] = []
            for i in records:
                rr = i.get("Host") or ""
                record_name = rr + "." + root_domain if rr and rr != '@' else root_domain
                data["list"].append({
                    "RecordId": i.get("RecordID"),
                    "name": record_name,
                    "value": i.get("Value") or "",
                    "line": i.get("Line") or "默认",
                    "ttl": i.get("TTL") or 600,
                    "type": i.get("Type") or "",
                    "status": "启用" if i.get("Enable") else "暂停",
                    # "mx": i.get("MX") or 0,
                    "updated_on": i.get("UpdatedAt") or "",
                    "remark": i.get("Remark") or "",
                })
            data["info"] = {
                "record_total": result.get("TotalCount") or 0
            }

        except Exception as e:
            public.print_log("获取DNS记录失败: {}".format(str(e)), "ERROR")
            pass
        self.set_record_data({root_domain: data})
        return data

    def update_dns_record(self, get):
        """更新DNS记录"""
        RecordId = get.RecordId
        domain_name = get.domain_name
        domain_dns_value = get.domain_dns_value
        record_type = get.record_type
        remark = get.get("remark", "")

        if record_type == 'MX':
            if not domain_dns_value.split(' ')[0].isdigit():
                if not get.get('mx'):
                    return public.returnMsg(False, 'MX记录类型必须填写MX值')
                try:
                    mx = int(get.mx)
                except:
                    mx = 10
                domain_dns_value = "{} {}".format(mx, domain_dns_value)

        root_domain, sub_domain, _ = self.extract_zone(domain_name)

        try:
            zone_id = self._get_zone_id(get.dns_id, root_domain)
            if not zone_id:
                return public.returnMsg(False, '未找到该域名的Zone信息')

            params = json.dumps({
                "ZID": int(zone_id),
                "RecordID": RecordId,
                "Host": sub_domain if sub_domain else "@",
                "Line": get.RecordLine if hasattr(get, "RecordLine") else "default",
                "Type": record_type,
                "Value": domain_dns_value,
                "TTL": 600,
                "Remark": remark
            })

            url, headers = self.sign_request(get.dns_id, "UpdateRecord", params)
            res = requests.post(url, headers=headers, data=params).json()

            if "ResponseMetadata" in res and "Error" in res["ResponseMetadata"]:
                return public.returnMsg(False, res["ResponseMetadata"]["Error"]["Message"])

            return public.returnMsg(True, '修改成功')
        except Exception as e:
            return public.returnMsg(False, self.get_error(str(e)))

    def set_dns_record_status(self, get):
        """设置DNS记录状态"""
        RecordId = get.RecordId
        domain_name = get.domain_name
        root_domain, _, _ = self.extract_zone(domain_name)

        try:
            zone_id = self._get_zone_id(get.dns_id, root_domain)
            if not zone_id:
                return public.returnMsg(False, '未找到该域名的Zone信息')

            params = json.dumps({
                "ZID": int(zone_id),
                "RecordID": RecordId,
                "Enable": not int(get.status)
            })

            url, headers = self.sign_request(get.dns_id, "UpdateRecordStatus", params)
            res = requests.post(url, headers=headers, data=params).json()

            if "ResponseMetadata" in res and "Error" in res["ResponseMetadata"]:
                return public.returnMsg(False, res["ResponseMetadata"]["Error"]["Message"])

            return public.returnMsg(True, '设置成功')
        except Exception as e:
            return public.returnMsg(False, self.get_error(str(e)))

    def get_domain_list(self, get):
        """获取域名列表"""
        try:
            params = json.dumps({})
            url, headers = self.sign_request(get.dns_id, "ListZones", params)
            res = requests.post(url, headers=headers, data=params).json()

            if "ResponseMetadata" in res and "Error" in res["ResponseMetadata"]:
                return public.returnMsg(False, res["ResponseMetadata"]["Error"]["Message"])

            local_domain_list = [d['domain'] for d in public.M('ssl_domains').field('domain').select()]
            zones = res.get("Result", {}).get("Zones", [])

            domain_list = [
                {
                    "id": i.get("ZID"),
                    "name": i.get("ZoneName"),
                    "remark": i.get("Remark", ""),
                    "record_count": i.get("RecordCount", 0),
                    "sync": 0 if i.get("ZoneName") in local_domain_list else 1,
                }
                for i in zones
            ]

            return {"status": True, "msg": "获取成功！", "data": domain_list}
        except Exception as e:
            return {"status": False, "msg": self.get_error(str(e)), "data": []}

    def get_error(self, error):
        """错误信息处理"""
        if "ZoneNotFound" in error:
            return "域名Zone不存在，请检查DNS接口配置后重试"
        elif "RecordAlreadyExists" in error:
            return "解析记录已存在"
        elif "RecordNotFound" in error:
            return "解析记录不存在"
        elif "InvalidAccessKey" in error:
            return "无效的AccessKey"
        elif "SignatureDoesNotMatch" in error:
            return "签名验证失败，请检查SecretKey是否正确"
        elif "InvalidParameter" in error:
            return "参数错误"
        elif "ZoneAlreadyExists" in error:
            return "域名Zone已存在"
        elif "RecordLimitExceeded" in error:
            return "解析记录数量超过限制"
        else:
            return error