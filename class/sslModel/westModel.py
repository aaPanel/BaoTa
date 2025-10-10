import hashlib
import time

import requests

from sslModel.base import sslBase
import public


class main(sslBase):

    def __init__(self):
        super().__init__()

    def __init_data(self, data):
        self.api_url = 'https://api.west.cn/api/v2/domain/'
        #    账号
        self.user_name = data["user_name"]
        #    api 密码
        self.api_password = data["api_password"]
        self.headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'}

    def get_params(self):
        timestamp = str(time.time() * 1000)
        token = hashlib.md5((self.user_name + self.api_password + timestamp).encode("utf-8")).hexdigest()
        return {"username": self.user_name, "token": token, "time": timestamp}

    def _request(self, dns_id, body):
        self.__init_data(self.get_dns_data(None)[dns_id])
        params = self.get_params()
        try:
            res = requests.post(self.api_url, headers=self.headers, params=params, data=body)

            if res.status_code != 200:
                return False, res.text
            json_data = res.json()
            if json_data['result'] != 200:
                return False, json_data['msg']
            return True, json_data
        except Exception as e:
            return False, e

    def get_dns_record(self, get):
        domain_name, _, sub_domain = self.extract_zone(get.domain_name)
        limit = "500"
        p = "1"
        if "limit" in get:
            limit = str(get["limit"])
        if "p" in get:
            p = str(get["p"])
        body = {
            "domain": domain_name,
            "act": "getdnsrecord",
            "limit": limit,
            "pageno": p,
        }
        if "search" in get:
            body["host"] = get["search"]
        try:
            flag, res = self._request(get.dns_id, body)

            data = {"list": [], "info": {"record_total": res['data']['total']}}
            if not flag:
                data = {}
            for record in res['data']["items"]:
                data["list"].append(
                    {
                        "RecordId": record["id"],
                        "name": record["item"] + "." + domain_name if record["item"] != "@" else domain_name,
                        "value": record["value"],
                        "line": record["line"] if record["line"] else "默认",
                        "ttl": record["ttl"],
                        "type": record["type"],
                        "status": "启用" if record["pause"] == 0 else "暂停",
                        "mx": record["level"],
                        "updated_on": "",
                        "remark": "",
                    }
                )
        except Exception as e:
            data = {}
        self.set_record_data({domain_name: data})
        return data

    def create_dns_record(self, get):
        domain_name, sub_domain, _ = self.extract_zone(get.domain_name)
        record_type = 'TXT'
        if 'record_type' in get:
            record_type = get.record_type
        mx = 10
        if record_type == 'MX':
            if not get.get('mx'):
                return public.returnMsg(False, 'MX记录类型必须填写MX值')
            mx = get.mx
        body = {
            "act": "adddnsrecord",
            "domain": domain_name,
            "host": sub_domain,
            "type": record_type,
            "value": get.domain_dns_value,
            "ttl": "600",
            "level": mx,
            "line": "",
        }
        try:
            flag, res = self._request(get.dns_id, body)
            if not flag:
                return public.returnMsg(False, '添加失败：{}'.format(res))
            return public.returnMsg(True, "添加成功")
        except Exception as e:
            return public.returnMsg(False, '添加失败：{}'.format(e))

    def delete_dns_record(self, get):
        domain_name, _, sub_domain = self.extract_zone(get.domain_name)

        body = {
            "act": "deldnsrecord",
            "domain": domain_name,
            "id": get.RecordId,
        }
        try:
            flag, res = self._request(get.dns_id, body)
            if not flag:
                return public.returnMsg(False, '删除失败：{}'.format(res))
            return public.returnMsg(True, "删除成功")
        except Exception as e:
            return public.returnMsg(False, '删除失败：{}'.format(e))

    def update_dns_record(self, get):
        # 不能修改主机记录和类型
        domain_name, sub_domain, _ = self.extract_zone(get.domain_name)
        mx = 10
        if get.record_type == 'MX':
            if not get.get('mx'):
                return public.returnMsg(False, 'MX记录类型必须填写MX值')
            mx = get.mx
        body = {
            "act": "moddnsrecord",
            "id": get.RecordId,
            "domain": domain_name,
            "host": sub_domain,
            "type": get.record_type,
            "value": get.domain_dns_value,
            "level": mx,
            "ttl": "600",
        }
        try:
            flag, res = self._request(get.dns_id, body)
            if not flag:
                return public.returnMsg(False, '修改失败：{}'.format(res))
            return public.returnMsg(True, "修改成功")
        except Exception as e:
            return public.returnMsg(False, '修改失败：{}'.format(e))

    def set_dns_record_status(self, get):
        domain_name, sub_domain, _ = self.extract_zone(get.domain_name)
        body = {
            "act": "pause",
            "id": get.RecordId,
            "domain": domain_name,
            "val": get.status,
        }
        try:
            flag, res = self._request(get.dns_id, body)
            if not flag:
                return public.returnMsg(False, '修改失败：{}'.format(res))
            return public.returnMsg(True, "设置成功")
        except Exception as e:
            return public.returnMsg(False, '修改失败：{}'.format(e))

    def get_domain_list(self, get):
        return {"status": False, "msg": "暂不支持", "data": []}




