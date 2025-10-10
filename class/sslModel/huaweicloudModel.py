import json

from sslModel.base import sslBase

import public

import copy
import sys
import hashlib
import hmac
import binascii
from datetime import datetime
import requests


class main(sslBase):
    dns_provider_name = "huaweicloud"
    _type = 0

    def __init__(self):
        super().__init__()
        self.region = "cn-south-1"
        self.BasicDateFormat = "%Y%m%dT%H%M%SZ"
        self.Algorithm = "SDK-HMAC-SHA256"
        self.HeaderXDate = "X-Sdk-Date"
        self.HeaderHost = "host"
        self.HeaderAuthorization = "Authorization"
        self.HeaderContentSha256 = "x-sdk-content-sha256"
        self.url = "https://dns.cn-north-1.myhuaweicloud.com"

    def __init_data(self, data):
        self.ak = data["AccessKey"]
        self.sk = data["SecretKey"]
        self.project_id = data["project_id"]

    def sign_to_response(self, dns_id, method="", url="", headers=None, body=""):
        url = self.url + url
        self.__init_data(self.get_dns_data(None)[dns_id])
        if sys.version_info.major < 3:
            body = body
            from urllib import quote, unquote

            def hmacsha256(keyByte, message):
                return hmac.new(keyByte, message, digestmod=hashlib.sha256).digest()

            # Create a "String to Sign".
            def StringToSign(canonicalRequest, t):
                bytes = HexEncodeSHA256Hash(canonicalRequest)
                return "%s\n%s\n%s" % (self.Algorithm, datetime.strftime(t, self.BasicDateFormat), bytes)

        else:
            body = body.encode("utf-8")
            from urllib.parse import quote, unquote

            def hmacsha256(keyByte, message):
                return hmac.new(keyByte.encode('utf-8'), message.encode('utf-8'), digestmod=hashlib.sha256).digest()

            # Create a "String to Sign".
            def StringToSign(canonicalRequest, t):
                bytes = HexEncodeSHA256Hash(canonicalRequest.encode('utf-8'))
                return "%s\n%s\n%s" % (self.Algorithm, datetime.strftime(t, self.BasicDateFormat), bytes)

        def HexEncodeSHA256Hash(data):
            sha256 = hashlib.sha256()
            sha256.update(data)
            return sha256.hexdigest()

        def findHeader(headers, header):
            for k in headers:
                if k.lower() == header.lower():
                    return headers[k]
            return None

        def CanonicalQueryString(query):
            keys = []
            for key in query:
                keys.append(key)
            keys.sort()
            a = []
            for key in keys:
                k = quote(key, safe='~')
                value = query[key]
                if type(value) is list:
                    value.sort()
                    for v in value:
                        kv = k + "=" + quote(str(v), safe='~')
                        a.append(kv)
                else:
                    kv = k + "=" + quote(str(value), safe='~')
                    a.append(kv)
            return '&'.join(a)

        def SignStringToSign(stringToSign, signingKey):
            hm = hmacsha256(signingKey, stringToSign)
            return binascii.hexlify(hm).decode()

        def AuthHeaderValue(signature, AppKey, signedHeaders):
            return "%s Access=%s, SignedHeaders=%s, Signature=%s" % (
                self.Algorithm, AppKey, ";".join(signedHeaders), signature)

        spl = url.split("://", 1)
        scheme = 'http'
        if len(spl) > 1:
            scheme = spl[0]
            url = spl[1]
        query = {}
        spl = url.split('?', 1)
        url = spl[0]
        if len(spl) > 1:
            for kv in spl[1].split("&"):
                spl = kv.split("=", 1)
                key = spl[0]
                value = ""
                if len(spl) > 1:
                    value = spl[1]
                if key != '':
                    key = unquote(key)
                    value = unquote(value)
                    if key in query:
                        query[key].append(value)
                    else:
                        query[key] = [value]
        spl = url.split('/', 1)
        host = spl[0]
        if len(spl) > 1:
            url = '/' + spl[1]
        else:
            url = '/'
        if headers is None:
            headers = {"content-type": "application/json"}
        else:
            headers = copy.deepcopy(headers)

        headerTime = findHeader(headers, self.HeaderXDate)

        if headerTime is None:
            t = datetime.utcnow()
            headers[self.HeaderXDate] = datetime.strftime(t, self.BasicDateFormat)
        else:
            t = datetime.strptime(headerTime, self.BasicDateFormat)

        haveHost = False
        for key in headers:
            if key.lower() == 'host':
                haveHost = True
                break
        if not haveHost:
            headers["host"] = host
        signedHeaders = []
        for key in headers:
            signedHeaders.append(key.lower())
        signedHeaders.sort()
        a = []
        __headers = {}
        for key in headers:
            keyEncoded = key.lower()
            value = headers[key]
            valueEncoded = value.strip()
            __headers[keyEncoded] = valueEncoded
            if sys.version_info.major == 3:
                headers[key] = valueEncoded.encode("utf-8").decode('iso-8859-1')
        for key in signedHeaders:
            a.append(key + ":" + __headers[key])
        canonicalHeaders = '\n'.join(a) + "\n"

        hexencode = findHeader(headers, self.HeaderContentSha256)
        if hexencode is None:
            hexencode = HexEncodeSHA256Hash(body)
        pattens = unquote(url).split('/')
        CanonicalURI = []
        for v in pattens:
            CanonicalURI.append(quote(v, safe="~"))
        CanonicalURL = "/".join(CanonicalURI)
        if CanonicalURL[-1] != '/':
            CanonicalURL = CanonicalURL + "/"  # always end with /

        canonicalRequest = "%s\n%s\n%s\n%s\n%s\n%s" % (method.upper(), CanonicalURL, CanonicalQueryString(query),
                                                       canonicalHeaders, ";".join(signedHeaders), hexencode)

        stringToSign = StringToSign(canonicalRequest, t)
        signature = SignStringToSign(stringToSign, self.sk)
        authValue = AuthHeaderValue(signature, self.ak, signedHeaders)
        headers[self.HeaderAuthorization] = authValue
        headers["content-length"] = str(len(body))
        queryString = CanonicalQueryString(query)
        if queryString != "":
            url = url + "?" + queryString

        res = requests.request(method, scheme + "://" + host + url, headers=headers, data=body)
        return res

    def create_dns_record(self, get):
        domain_name = get.domain_name
        domain_dns_value = get.domain_dns_value
        remark = get.get("remark", "")
        record_type = 'TXT'
        if 'record_type' in get:
            record_type = get.record_type
        if record_type == 'TXT':
            domain_dns_value = "\"{}\"".format(domain_dns_value)
        if get.record_type == 'MX':
            if not get.get('mx'):
                return public.returnMsg(False, 'MX记录类型必须填写MX值')
            mx = get.mx
            domain_dns_value = "{} {}".format(mx, domain_dns_value)

        root_domain, sub_domain, _ = self.extract_zone(domain_name)
        if sub_domain == "@":
            domain_name = root_domain

        try:
            zone_dic = self.get_zoneid_dict(get.dns_id)
            zone_id = zone_dic.get(root_domain)
            body = json.dumps({
                "name": domain_name,
                "type": record_type,
                "records": [domain_dns_value],
                "description": remark,
            })

            res = self.sign_to_response(get.dns_id, "POST", "/v2.1/zones/{}/recordsets".format(zone_id), body=body)
            if res.status_code != 202:
                return public.returnMsg(False, self.get_error(res.text))

            return public.returnMsg(True, '添加成功')
        except Exception as e:
            return public.returnMsg(False, self.get_error(str(e)))

    def delete_dns_record(self, get):
        domain_name = get.domain_name
        RecordId = get.RecordId
        root_domain, sub_domain, _ = self.extract_zone(domain_name)

        zone_dic = self.get_zoneid_dict(get.dns_id)
        zone_id = zone_dic[root_domain]
        try:
            res = self.sign_to_response(get.dns_id, "DELETE", "/v2.1/zones/{}/recordsets/{}".format(zone_id, RecordId))
            if res.status_code != 202:
                return public.returnMsg(False, self.get_error(res.text))
            return public.returnMsg(True, '删除成功')
        except Exception as e:
            return public.returnMsg(False, self.get_error(str(e)))

    def get_zoneid_dict(self, dns_id):
        """
        获取所有域名对应id
        """
        res = self.sign_to_response(dns_id, "GET", "/v2/zones")
        if res.status_code != 200:
            return {}
        response = res.json()
        data = {i["name"][:-1]: i["id"] for i in response["zones"]}

        return data

    def get_dns_record(self, get):
        domain_name = get.domain_name
        root_domain, sub_domain, _ = self.extract_zone(domain_name)
        data = {}
        try:
            zone_dic = self.get_zoneid_dict(get.dns_id)
            zone_id = zone_dic[root_domain]

            limit = 100
            offset = 0
            if "limit" in get:
                limit = int(get.limit)
            if "p" in get:
                offset = ((int(get.p) - 1) * int(get.limit))
            url = "/v2.1/zones/{}/recordsets?limit={}&offset={}".format(zone_id, limit, offset)
            if "search" in get:
                name = get.search
                url = url + "&name={}".format(name)

            res = self.sign_to_response(get.dns_id, "GET", url)
            if res.status_code != 200:
                return {}
            response = res.json()

            line_type_dict = {
                "default_view": "全网默认",
                "Dianxin": "电信",
                "Liantong": "联通",
                "Yidong": "移动",
                "Jiaoyuwang": "教育网",
                "Tietong": "铁通",
                "Pengboshi": "鹏博士",
                "CN": "中国大陆",
                "Abroad": "全球",
            }

            data["list"] = [
                {
                    "RecordId": i["id"],
                    "name": i["name"][:-1],
                    "value":'\r\n'.join(i["records"]).split(' ')[-1] if i["type"] == "MX" else '\r\n'.join(i["records"]).replace('"', '') if i["type"] == "TXT" else '\r\n'.join(i["records"]),
                    "line": line_type_dict.get(i["line"], "其它"),
                    "ttl": i["ttl"],
                    "type": i["type"],
                    "status": "启用"if i["status"] == "ACTIVE" else "暂停" if i["status"] == "DISABLE" else i["status"],
                    "mx": '\r\n'.join(i["records"]).split(' ')[0],
                    "updated_on": i.get("update_at", ""),
                    "remark": i.get("description") or "",
                }
                for i in response["recordsets"]
            ]
            data["info"] = {
                'record_total': response['metadata']['total_count']
            }
        except Exception as e:
            pass
        self.set_record_data({root_domain: data})
        return data

    def update_dns_record(self, get):
        domain_name = get.domain_name
        RecordId = get.RecordId
        record_type = get.record_type
        remark = get.get("remark", "")
        domain_dns_value = get.domain_dns_value
        root_domain, sub_domain, _ = self.extract_zone(domain_name)

        if sub_domain == "@":
            domain_name = root_domain
        if get.record_type == 'MX':
            if not get.get('mx'):
                return public.returnMsg(False, 'MX记录类型必须填写MX值')
            mx = get.mx
            domain_dns_value = "{} {}".format(mx, domain_dns_value)
        if record_type == 'TXT':
            domain_dns_value = "\"{}\"".format(domain_dns_value)

        zone_dic = self.get_zoneid_dict(get.dns_id)
        zone_id = zone_dic[root_domain]
        try:
            body = json.dumps({
                "name": domain_name,
                "type": record_type,
                "records": [domain_dns_value],
                "description": remark,
            })

            res = self.sign_to_response(get.dns_id, "PUT", "/v2.1/zones/{}/recordsets/{}".format(zone_id, RecordId), body=body)
            if res.status_code != 202:
                return public.returnMsg(False, self.get_error(res.text))

            return public.returnMsg(True, '修改成功')
        except Exception as e:
            return public.returnMsg(False, self.get_error(str(e)))

    def set_dns_record_status(self, get):
        RecordId = get.RecordId
        status = "DISABLE" if int(get.status) else "ENABLE"

        try:
            body = json.dumps({
                "status": status,
            })

            res = self.sign_to_response(get.dns_id, "PUT", "/v2.1/recordsets/{}/statuses/set".format(RecordId), body=body)
            if res.status_code != 202:
                return public.returnMsg(False, self.get_error(res.text))

            return public.returnMsg(True, '设置成功')
        except Exception as e:
            return public.returnMsg(False, self.get_error(str(e)))

    def get_domain_list(self, get):
        try:
            res = self.sign_to_response(get.dns_id, "GET", "/v2/zones")
            if res.status_code != 200:
                return public.returnMsg(False, self.get_error(res.text))
            response = res.json()
            local_domain_list = [d['domain'] for d in public.M('ssl_domains').field('domain').select()]

            domain_list = [
                {
                    "id": i["id"],
                    "name": i["name"][:-1],
                    "remark": i.get("description") or "",
                    "record_count": i.get("record_num") or 0,
                    "sync": 0 if i["name"][:-1] in local_domain_list else 1,
                }
                for i in response["zones"]
            ]
            return {"status": True, "msg": "获取成功！","data": domain_list}
        except Exception as e:
            return {"status": False, "msg": self.get_error(str(e)), "data": []}

    def get_error(self, error):
        if "DNS.0317" in error:
            return "此记录为系统默认域名记录值，不能删除。"
        elif "DNS.0318" in error:
            return "此记录为系统默认域名记录值，不能更新。"
        elif "DNS.0321" in error:
            return "子域名级别超过限制。"
        elif "DNS.0324" in error:
            return "系统默认解析记录不能操作。"
        elif "DNS.0308" in error:
            return "记录集类型非法。"
        elif "DNS.0307" in error:
            return "记录集的值非法。"
        elif "DNS.0302" in error:
            return "这个华为云账户下面不存在这个域名，请检查dns接口配置后重试"
        elif "APIGW.0301" in error:
            return "dns账号信息有误"
        elif "DNS.0312" in error:
            return "存在同名的主机记录"
        elif "DNS.0313" in error:
            return "不存在这条记录"
        else:
            return error
