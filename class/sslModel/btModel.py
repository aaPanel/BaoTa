from sslModel.base import sslBase
import public
import hmac
import hashlib
import json
import time
import requests
from typing import Dict, Any, Optional, Tuple


class main(sslBase):
    def __init__(self):
        super().__init__()

    def __init_data(self, data):
        self.account_id = data["AccountID"]
        self.access_key = data["AccessKey"]
        self.secret_key = data["SecretKey"]
        self.base_url = "https://dmp.bt.cn"


    def _generate_signature(self, method: str, path: str, body: str) -> Tuple[str, str]:
        """生成 API 签名"""
        timestamp = str(int(time.time()))

        signing_string = f"{self.account_id}\n{timestamp}\n{method.upper()}\n{path}\n{body}"

        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            signing_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return timestamp, signature

    def _request(self, method: str, path: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发起 API 请求"""
        url = self.base_url + path

        body_str = ""
        body_bytes = None
        if data is not None:
            body_str = json.dumps(data, separators=(',', ':'))
            body_bytes = body_str.encode('utf-8')

        timestamp, signature = self._generate_signature(method, path, body_str)

        headers = {
            "Content-Type": "application/json",
            "X-Account-ID": self.account_id,
            "X-Access-Key": self.access_key,
            "X-Timestamp": timestamp,
            "X-Signature": signature
        }

        response = requests.request(
            method=method.upper(),
            url=url,
            data=body_bytes,
            headers=headers
        )

        result = response.json()

        if not result.get("status"):
            raise Exception(f"API 请求失败: {result.get('msg')}")

        return result

    def create_dns_record(self, get):
        domain_name = get.domain_name
        domain_dns_value = get.domain_dns_value
        record_type = 'TXT'
        if 'record_type' in get:
            record_type = get.record_type
        mx = 0
        if record_type == 'MX':
            if not get.get('mx'):
                return public.returnMsg(False, 'MX记录类型必须填写MX值')
            mx = int(get.mx)

        domain_name, sub_domain, _ = self.extract_zone(domain_name)

        if not sub_domain:
            sub_domain = '@'
        domain_data = self.get_domain_list(get)
        if not domain_data['status']:
            return domain_data
        domain_list = domain_data['data']
        domain_id = None
        for d in domain_list:
            if d['name'] == domain_name:
                domain_id = d['id']
                break
        if not domain_id:
            return public.returnMsg(False, '域名不存在，请先添加域名')
        try:
            body = {
                "domain_type": 1,
                "domain_id": domain_id,
                "record": sub_domain,
                "type": record_type,
                "value": domain_dns_value,
                "TTL": int(get.ttl) if 'ttl' in get else 600,
                "MX": mx,
                "line": "默认",
                "remark": get.remark if 'remark' in get else "",
                "view_id": 0,
            }
            res = self._request("POST", "/api/v1/dns/record/create", body)
        except Exception as e:
            public.print_log(e)
            return public.returnMsg(False, "添加解析记录失败: {}".format(e))
        if not res.get("status"):
            return public.returnMsg(False, "添加解析记录失败: {}".format(res.get("msg")))
        return public.returnMsg(True, "添加解析记录成功")

    def delete_dns_record(self, get):
        domain_name = get.domain_name
        domain_name, sub_domain, _ = self.extract_zone(domain_name)
        domain_data = self.get_domain_list(get)
        if not domain_data['status']:
            return domain_data
        domain_list = domain_data['data']
        domain_id = None
        for d in domain_list:
            if d['name'] == domain_name:
                domain_id = d['id']
                break
        if not domain_id:
            return public.returnMsg(False, '域名不存在，请先添加域名')

        record_id = get.RecordId
        try:
            body = {
                "record_id": record_id,
                "domain_type":1,
                "domain_id":domain_id
            }
            res = self._request("POST", "/api/v1/dns/record/delete", body)
        except Exception as e:
            public.print_log(e)
            return public.returnMsg(False, "删除解析记录失败: {}".format(e))
        if not res.get("status"):
            return public.returnMsg(False, "删除解析记录失败: {}".format(res.get("msg")))
        return public.returnMsg(True, "删除解析记录成功")

    def update_dns_record(self, get):
        domain_name = get.domain_name
        domain_dns_value = get.domain_dns_value
        record_type = 'TXT'
        if 'record_type' in get:
            record_type = get.record_type
        mx = 0
        if record_type == 'MX':
            if not get.get('mx'):
                return public.returnMsg(False, 'MX记录类型必须填写MX值')
            mx = int(get.mx)

        domain_name, sub_domain, _ = self.extract_zone(domain_name)

        if not sub_domain:
            sub_domain = '@'
        domain_data = self.get_domain_list(get)
        if not domain_data['status']:
            return domain_data
        domain_list = domain_data['data']
        domain_id = None
        for d in domain_list:
            if d['name'] == domain_name:
                domain_id = d['id']
                break
        if not domain_id:
            return public.returnMsg(False, '域名不存在，请先添加域名')
        record_id = get.RecordId
        try:
            body = {
                "record_id": record_id,
                "domain_type": 1,
                "domain_id": domain_id,
                "record": sub_domain,
                "type": record_type,
                "value": domain_dns_value,
                "TTL": int(get.ttl) if 'ttl' in get else 600,
                "MX": mx,
                "line": "默认",
                "remark": get.remark if 'remark' in get else "",
                "view_id": 0,
            }
            res = self._request("POST", "/api/v1/dns/record/update", body)
        except Exception as e:
            public.print_log(e)
            return public.returnMsg(False, "修改解析记录失败: {}".format(e))
        if not res.get("status"):
            return public.returnMsg(False, "修改解析记录失败: {}".format(res.get("msg")))
        return public.returnMsg(True, "修改解析记录成功")

    def set_dns_record_status(self, get):
        domain_name = get.domain_name
        domain_name, sub_domain, _ = self.extract_zone(domain_name)
        domain_data = self.get_domain_list(get)
        if not domain_data['status']:
            return domain_data
        domain_list = domain_data['data']
        domain_id = None
        for d in domain_list:
            if d['name'] == domain_name:
                domain_id = d['id']
                break
        if not domain_id:
            return public.returnMsg(False, '域名不存在，请先添加域名')
        record_id = get.RecordId
        try:
            body = {
                "record_id": record_id,
                "domain_type":1,
                "domain_id":domain_id,
            }
            res = self._request("POST", "/api/v1/dns/record/{}".format("start" if get.status == '0' else "pause"), body)
        except Exception as e:
            public.print_log(e)
            return public.returnMsg(False, "设置解析记录状态失败: {}".format(e))
        if not res.get("status"):
            return public.returnMsg(False, "设置解析记录状态失败: {}".format(res.get("msg")))
        return public.returnMsg(True, "设置解析记录状态成功")

    def get_dns_record(self, get):
        domain_name = get.domain_name
        domain_data = self.get_domain_list(get)
        if not domain_data['status']:
            return domain_data
        domain_list = domain_data['data']
        domain_id = None
        for d in domain_list:
            if d['name'] == domain_name:
                domain_id = d['id']
                break
        if not domain_id:
            return public.returnMsg(False, '域名不存在，请先添加域名')
        try:
            body = {
                "domain_id": domain_id,
                "searchKey": "record",
                "domain_type": 1,
                "p": get.p,
                "row": get.limit,
            }
            if "search" in get and get.search:
                body["searchValue"] = get.search

            res = self._request("POST", "/api/v1/dns/record/list", body)
        except Exception as e:
            public.print_log(e)
            return public.returnMsg(False, "获取解析记录失败: {}".format(e))
        data = {"info": {"record_total": res.get("data", {}).get("count", 0)}, "list": []}
        for i in res.get("data", {}).get("data", []):
            data["list"].append({
                "RecordId": i["record_id"],
                "name": i["record"]+"."+domain_name if i["record"] != "@" else domain_name,
                "type": i["type"],
                "value": i["value"],
                "ttl": i["TTL"],
                "mx": i.get("MX", 0),
                "status": "暂停" if i["state"] == 2 else "启用",
                "line": i.get("line", "默认"),
                "remark": i.get("remark", ""),
            })
        return data




    def get_domain_list(self, get):
        self.__init_data(self.get_dns_data(None)[get.dns_id])

        try:
            res = self._request("POST", "/api/v1/domain/manage/list", {"p":1,"rows":10, "status":1})
        except Exception as e:
            public.print_log(e)
            return public.returnMsg(False, "获取域名列表失败: {}".format(e))
        data = []
        local_domain_list = [d['domain'] for d in public.M('ssl_domains').field('domain').select()]

        for i in res.get("data", {}).get("data", []):
            data.append({
                "id": i["id"],
                "name": i["full_domain"],
                "sync": 0 if i["full_domain"] in local_domain_list else 1,
            })

        return {"status": True, "msg": "获取成功", "data": data}

