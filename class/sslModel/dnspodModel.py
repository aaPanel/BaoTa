from sslModel.base import sslBase
import requests
from urllib.parse import urlparse
from urllib.parse import urljoin
import public

class main(sslBase):
    dns_provider_name = "dnspod"
    _type = 0  # 0:lest 1：锐成

    def __init__(self):
        super().__init__()

    def __init_data(self,data):

        self.DNSPOD_ID = data['ID']
        self.DNSPOD_API_KEY = data['Token']
        self.DNSPOD_API_BASE_URL = 'https://dnsapi.cn/'
        self.HTTP_TIMEOUT = 65  # seconds
        self.DNSPOD_LOGIN = "{0},{1}".format(self.DNSPOD_ID, self.DNSPOD_API_KEY)

    def create_dns_record(self,get):
        """
        @name 创建dns记录
        @param get.dns_id dns_id
        @param get.domain_name 域名
        @param get.domain_dns_value 域名解析值
        """
        dns_id = get.dns_id
        domain_name = get.domain_name
        domain_dns_value = get.domain_dns_value
        remark = get.get('remark')
        record_type = 'TXT'
        if 'record_type' in get:
            record_type = get.record_type
        mx = 0
        if record_type == 'MX':
            mx = get.get('mx')
            if not mx:
                return public.returnMsg(False, 'MX记录类型必须填写MX记录值')

        self.__init_data(self.get_dns_data(None)[dns_id])
        domain_name, subd, _ = self.extract_zone(domain_name)

        return self.add_record(domain_name, subd, domain_dns_value, record_type, remark, mx)

    def delete_dns_record(self,get):
        """
        @name 删除dns记录
        @param get.dns_id dns_id
        @param get.domain_name 域名
        """
        dns_id = get.dns_id
        domain_name = get.domain_name
        RecordId = get.RecordId

        self.__init_data(self.get_dns_data(None)[dns_id])

        try:
            domain_name, subd, _ = self.extract_zone(domain_name)
            res = self.remove_record(domain_name, RecordId)
            if res["status"]["code"] != '1':
                return public.returnMsg(False, res["status"]["message"])
        except Exception as e:
            return public.returnMsg(False, e)

        return public.returnMsg(True, '删除成功')

    def get_dns_record(self,get):
        """
        @name 获取dns记录
        @param get.dns_id dns_id
        @param get.domain_name 域名
        @return json
        """
        dns_id = get.dns_id
        domain_name = get.domain_name

        self.__init_data(self.get_dns_data(None)[dns_id])

        domain_name, _, subd = self.extract_zone(domain_name)

        url = urljoin(self.DNSPOD_API_BASE_URL, "Record.List")
        rootdomain = domain_name
        body = {
            "login_token": self.DNSPOD_LOGIN,
            "format": "json",
            "domain": rootdomain,
        }

        if "limit" in get:
            body["length"] = get.limit
        if "p" in get:
            body["offset"] = ((int(get.p) - 1) * int(get.limit))
        if "search" in get:
            body["keyword"] = get.search

        try:
            list_dns_response = requests.post(url, data=body, timeout=self.HTTP_TIMEOUT).json()
        except:
            list_dns_response = {}
        data = {}
        if list_dns_response.get("status", {}).get("code") == "10":
            data = {"info": {'record_total': 0}, "list": []}
        if 'records' in list_dns_response:
            for i in list_dns_response['records']:
                i['name'] = i['name'] + "." + domain_name if i['name'] != '@' else domain_name
                i['RecordId'] = i['id']
                i["status"] = "启用" if i["status"] == "enable" else "暂停" if i["status"] == "disable" else i["status"]
            data['list'] = list_dns_response['records']
        if 'info' in list_dns_response:
            data['info'] = list_dns_response['info']
        if not data:
            data = list_dns_response
        self.set_record_data({domain_name: data})
        return data

    def add_record(self, domain_name, subd, domain_dns_value, s_type, remark="", mx=0):
        """
        @name 添加记录
        @param domain_name 域名
        @param subd 子域名
        @param domain_dns_value 解析值
        @param s_type 记录类型
        """
        url = urljoin(self.DNSPOD_API_BASE_URL, "Record.Create")
        body = {
            "record_type": s_type,
            "domain": domain_name,
            "sub_domain": subd,
            "value": domain_dns_value,
            "remark": remark,
            "mx": mx,
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
        return public.returnMsg(True, '添加成功')

    def remove_record(self, domain_name, RecordId):
        rootdomain = domain_name

        urlr = urljoin(self.DNSPOD_API_BASE_URL, "Record.Remove")
        bodyr = {
            "login_token": self.DNSPOD_LOGIN,
            "format": "json",
            "domain": rootdomain,
            "record_id": RecordId,
        }
        return requests.post(
            urlr, data=bodyr, timeout=self.HTTP_TIMEOUT
        ).json()

    def add_record_for_creat_site(self, domain, server_ip):
        domain_name, zone, _ = self.extract_zone(domain)
        self.add_record(domain_name, zone, server_ip, "A")

    def update_dns_record(self, get):
        domain_name = get.domain_name

        mx = 0
        if get.record_type == 'MX':
            mx = get.get('mx')
            if not mx:
                return public.returnMsg(False, 'MX记录类型必须填写MX记录值')
        domain_name, subd, _ = self.extract_zone(domain_name)

        self.__init_data(self.get_dns_data(None)[get.dns_id])

        url = urljoin(self.DNSPOD_API_BASE_URL, "Record.Modify")

        body = {
            "login_token": self.DNSPOD_LOGIN,
            "domain": domain_name,
            "record_id": get.RecordId,
            "sub_domain": subd,
            "record_type": get.record_type,
            "record_line": get.RecordLine,
            "value": get.domain_dns_value,
            "remark": get.get("remark"),
            "mx": mx,
        }
        try:
            res = requests.post(
                url, data=body, timeout=self.HTTP_TIMEOUT
            ).json()
            if res["status"]["code"] != '1':
                return public.returnMsg(False, res["status"]["message"])

            return public.returnMsg(True, "修改成功")
        except Exception as e:
            return public.returnMsg(False, "操作失败:{}".format(e))

    def set_dns_record_status(self, get):
        domain_name = get.domain_name
        status = "disable" if int(get.status) else "enable"

        domain_name, subd, _ = self.extract_zone(domain_name)

        self.__init_data(self.get_dns_data(None)[get.dns_id])

        url = urljoin(self.DNSPOD_API_BASE_URL, "Record.Status")

        body = {
            "login_token": self.DNSPOD_LOGIN,
            "domain": domain_name,
            "record_id": get.RecordId,
            "status": status,
        }
        try:
            res = requests.post(
                url, data=body, timeout=self.HTTP_TIMEOUT
            ).json()
            if res["status"]["code"] != '1':
                return public.returnMsg(False, res["status"]["message"])

            return public.returnMsg(True, "设置成功")
        except Exception as e:
            return public.returnMsg(False, "操作失败:{}".format(e))

    def get_domain_list(self, get):
        self.__init_data(self.get_dns_data(None)[get.dns_id])
        url = urljoin(self.DNSPOD_API_BASE_URL, "Domain.List")
        body = {
            "login_token": self.DNSPOD_LOGIN,
            "format": "json",
        }
        try:
            res = requests.post(
                url, data=body, timeout=self.HTTP_TIMEOUT
            ).json()
            local_domain_list = [d['domain'] for d in public.M('ssl_domains').field('domain').select()]

            domain_list = [
                {
                    "id": i["id"],
                    "name": i["name"],
                    "remark": i.get("remark") or "",
                    "record_count": i.get("records") or 0,
                    "sync": 0 if i["name"] in local_domain_list else 1,
                }
                for i in res["domains"]
            ]
            return {"status": True, "msg": "获取成功", "data": domain_list}
        except Exception as e:
            return {"status": False, "msg": str(e), "data": []}
