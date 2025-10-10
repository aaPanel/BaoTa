import hashlib
import hmac
import json
import time
from datetime import datetime

import public
import requests
from sslModel.base import sslBase


class main(sslBase):
    dns_provider_name = "tencentcloud"
    _type = 0

    def __init__(self):
        super().__init__()
        self.endpoint = "dnspod.tencentcloudapi.com"
        self.host = "https://dnspod.tencentcloudapi.com"
        self.version = "2021-03-23"
        self.algorithm = "TC3-HMAC-SHA256"

    def __init_data(self, data):
        self.secret_id = data["secret_id"]
        self.secret_key = data["secret_key"]

    def get_headers(self, dns_id, action, payload, region="", token=""):
        self.__init_data(self.get_dns_data(None)[dns_id])
        timestamp = int(time.time())
        # timestamp = 1551113065
        date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
        # ************* 步骤 1：拼接规范请求串 *************
        http_request_method = "POST"
        canonical_uri = "/"
        canonical_querystring = ""
        ct = "application/json; charset=utf-8"
        canonical_headers = "content-type:%s\nhost:%s\nx-tc-action:%s\n" % (ct, self.endpoint, action.lower())
        signed_headers = "content-type;host;x-tc-action"
        hashed_request_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        canonical_request = (http_request_method + "\n" +
                             canonical_uri + "\n" +
                             canonical_querystring + "\n" +
                             canonical_headers + "\n" +
                             signed_headers + "\n" +
                             hashed_request_payload)
        # ************* 步骤 2：拼接待签名字符串 *************
        credential_scope = date + "/" + "dnspod" + "/" + "tc3_request"
        hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        string_to_sign = (self.algorithm + "\n" +
                          str(timestamp) + "\n" +
                          credential_scope + "\n" +
                          hashed_canonical_request)
        # ************* 步骤 3：计算签名 *************
        # 计算签名摘要函数
        def sign(key, msg):
            return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()
        secret_date = sign(("TC3" + self.secret_key).encode("utf-8"), date)
        secret_service = sign(secret_date, "dnspod")
        secret_signing = sign(secret_service, "tc3_request")
        signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
        # ************* 步骤 4：拼接 Authorization *************
        authorization = (self.algorithm + " " +
                         "Credential=" + self.secret_id + "/" + credential_scope + ", " +
                         "SignedHeaders=" + signed_headers + ", " +
                         "Signature=" + signature)
        headers = {
            "Authorization": authorization,
            "Content-Type": "application/json; charset=utf-8",
            "Host": self.endpoint,
            "X-TC-Action": action,
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Version": self.version
        }
        if region:
            headers["X-TC-Region"] = region
        if token:
            headers["X-TC-Token"] = token
        return headers

    def create_dns_record(self, get):
        domain_name = get.domain_name
        domain_dns_value = get.domain_dns_value
        remark = get.get("remark", "")
        record_type = 'TXT'
        if 'record_type' in get:
            record_type = get.record_type
        record_line = '默认'
        if 'record_line' in get:
            record_line = get.record_line
        mx = 10
        if record_type == 'MX':
            if not get.get('mx'):
                return public.returnMsg(False, 'MX记录类型必须填写MX值')
            mx = int(get.mx)

        domain_name, sub_domain, _ = self.extract_zone(domain_name)

        try:
            params = json.dumps({
                "Domain": domain_name,
                "SubDomain": sub_domain,
                "RecordType": record_type,
                "RecordLine": record_line,
                "Value": domain_dns_value,
                "Remark": remark,
                "MX": mx
            })
            headers = self.get_headers(get.dns_id, "CreateRecord", params)
            res = requests.post(self.host, headers=headers, data=params).json()
            if "Error" in res['Response']:
                return public.returnMsg(False, res['Response']["Error"]["Message"])
            return public.returnMsg(True, '添加成功')
        except Exception as e:
            return public.returnMsg(False, '添加失败，msg：{}'.format(e))

    def delete_dns_record(self, get):
        try:
            domain_name = get.domain_name
            RecordId = get.RecordId
            root_domain, _, sub_domain = self.extract_zone(domain_name)

            params = json.dumps({
                "Domain": root_domain,
                "RecordId": int(RecordId)
            })
            headers = self.get_headers(get.dns_id, "DeleteRecord", params)
            res = requests.post(self.host, headers=headers, data=params).json()
            if "Error" in res['Response']:
                return public.returnMsg(False, res['Response']["Error"]["Message"])
            return public.returnMsg(True, '删除成功!')
        except Exception as e:
            return public.returnMsg(False, e)

    def get_dns_record(self, get):

        domain_name, _, sub_domain = self.extract_zone(get.domain_name)
        params = {
            "Domain": domain_name,
        }
        if "limit" in get:
            params["Limit"] = int(get.limit)
        if "p" in get:
            params["Offset"] = ((int(get.p) - 1) * int(get.limit))
        if "search" in get:
            params["Keyword"] = get.search
        params = json.dumps(params)

        data = {}
        try:
            headers = self.get_headers(get.dns_id, "DescribeRecordList", params)
            json_data = requests.post(self.host, headers=headers, data=params).json()
            json_data = json_data['Response']
            if "Error" in json_data:
                if json_data["Error"]["Code"] == "ResourceNotFound.NoDataOfRecord":
                    data = {"info": {'record_total': 0}, "list": []}
                else:
                    data = json_data
            # if 'RecordList' in json_data:
            #     data['list'] = json_data['RecordList']
            if 'RecordCountInfo' in json_data:
                data['info'] = {
                    "record_total": json_data['RecordCountInfo']['SubdomainCount']
                }
            data["list"] = [
                {
                    "RecordId": i["RecordId"],
                    "name": i["Name"] + "." + domain_name if i["Name"] != '@' else domain_name,
                    "value": i["Value"],
                    "line": i["Line"],
                    "ttl": i["TTL"],
                    "type": i["Type"],
                    "status": "启用" if i["Status"] == "ENABLE" else "暂停" if i["Status"] == "DISABLE" else i["Status"],
                    "mx": i.get("MX"),
                    "updated_on": i["UpdatedOn"],
                    "remark": i.get("Remark") or "",
                }
                for i in json_data["RecordList"]
            ]

        except Exception as e:
            pass
        self.set_record_data({domain_name: data})
        return data

    def update_dns_record(self, get):
        RecordId = get.RecordId
        RecordLine = get.RecordLine
        domain_name = get.domain_name
        domain_dns_value = get.domain_dns_value
        record_type = get.record_type
        remark = get.get("remark", "")

        mx = 10
        if record_type == 'MX':
            if not get.get('mx'):
                return public.returnMsg(False, 'MX记录类型必须填写MX值')
            mx = int(get.mx)
        domain_name, sub_domain, _ = self.extract_zone(domain_name)

        try:
            params = json.dumps({
                "Domain": domain_name,
                "SubDomain": sub_domain,
                "RecordType": record_type,
                "RecordLine": RecordLine,
                "Remark": remark,
                "Value": domain_dns_value,
                "RecordId": int(RecordId),
                "MX": mx
            })
            headers = self.get_headers(get.dns_id, "ModifyRecord", params)
            res = requests.post(self.host, headers=headers, data=params).json()
            if "Error" in res['Response']:
                return public.returnMsg(False, res['Response']["Error"]["Message"])
            return public.returnMsg(True, '修改成功!')
        except Exception as e:
            return public.returnMsg(False, e)

    def set_dns_record_status(self, get):
        RecordId = get.RecordId
        status = "DISABLE" if int(get.status) else "ENABLE"
        domain_name = get.domain_name
        domain_name, sub_domain, _ = self.extract_zone(domain_name)
        try:
            params = json.dumps({
                "Domain": domain_name,
                "RecordId": int(RecordId),
                "Status": status
            })
            headers = self.get_headers(get.dns_id, "ModifyRecordStatus", params)
            res = requests.post(self.host, headers=headers, data=params).json()
            if "Error" in res['Response']:
                return public.returnMsg(False, res['Response']["Error"]["Message"])
            return public.returnMsg(True, '设置成功!')
        except Exception as e:
            return public.returnMsg(False, e)

    def get_domain_list(self, get):
        try:
            params = json.dumps({})
            headers = self.get_headers(get.dns_id, "DescribeDomainList", params)
            res = requests.post(self.host, headers=headers, data=params).json()
            local_domain_list = [d['domain'] for d in public.M('ssl_domains').field('domain').select()]

            domain_list = [
                {
                    "id": i["DomainId"],
                    "name": i["Name"],
                    "remark": i.get("Remark") or "",
                    "record_count": i.get("RecordCount") or 0,
                    "sync": 0 if i["Name"] in local_domain_list else 1,
                }
                for i in res["Response"]["DomainList"]
            ]

            if "Error" in res['Response']:
                return public.returnMsg(False, res['Response']["Error"]["Message"])
            return {"status": True, "msg": "获取成功！","data": domain_list}
        except Exception as e:
            return {"status": False, "msg": str(e), "data": []}
