from sslModel.base import sslBase
import requests
from urllib.parse import urlparse
from urllib.parse import urljoin
import public


class main(sslBase):
    dns_provider_name = "godaddy"
    _type = 0  # 0:lest 1：锐成

    def __init__(self):
        super().__init__()

    def __init_data(self, data):
        self.key = data['Key']
        self.secret = data['Secret']
        self.base_url = 'https://api.godaddy.com'
        self.timeout = 65

        self.headers = {
            "Authorization": "sso-key {}:{}".format(self.key, self.secret)
        }

    def create_dns_record(self, get):
        dns_id = get.dns_id
        domain_name = get.domain_name
        domain_dns_value = get.domain_dns_value

        self.__init_data(self.get_dns_data(None)[dns_id])

        root_domain, sub_domain, _ = self.extract_zone(domain_name)

        body = [
            {
                "data": domain_dns_value,
                "name": sub_domain or '@',
                "type": "TXT" if 'record_type' not in get else get.record_type,
            }
        ]
        url = urljoin(self.base_url, "/v1/domains/{}/records".format(root_domain))
        try:
            response = requests.patch(
                url, headers=self.headers, json=body, timeout=self.timeout,
            )
            if response.status_code == 200:
                return public.returnMsg(False, '添加成功')
            else:
                return public.returnMsg(False, '添加失败，{}'.format(response.json()))
        except Exception as e:
            return public.returnMsg(False, '添加失败，msg：{}'.format(e))

    def get_dns_record(self, get):
        dns_id = get.dns_id
        domain_name = get.domain_name

        root_domain, _, sub_domain = self.extract_zone(domain_name)

        self.__init_data(self.get_dns_data(None)[dns_id])
        url = urljoin(self.base_url, "/v1/domains/{}/records".format(root_domain))
        data = {}
        try:
            response = requests.get(
                url, headers=self.headers, timeout=self.timeout,
            )
            json_data = response.json()
            data["list"] = [
                {
                    "name": i["name"] + "." + root_domain if i["name"] != '@' else root_domain,
                    "ttl": i["ttl"],
                    "type": i["type"],
                    "value": i["data"],
                    "line": "",
                    "status": "",
                    "mx": i.get("priority") or 0,
                    "updated_on": "",
                    "remark": "",
                }
                for i in json_data
            ]
            data["info"] = {
                "record_total": len(data["list"])
            }
            return data

        except Exception as e:
            return data

    def delete_dns_record(self, get):
        domain_name = get.domain_name
        dns_id = get.dns_id

        root_domain, sub_domain, _ = self.extract_zone(domain_name)

        self.__init_data(self.get_dns_data(None)[dns_id])

        url = urljoin(self.base_url, "/v1/domains/{}/records/{}/{}".format(root_domain, 'TXT' if 'record_type' not in get else get.record_type, sub_domain))

        try:
            response = requests.delete(
                url, headers=self.headers, timeout=self.timeout,
            )
            if response.status_code == 204:
                return public.returnMsg(True, '删除成功')
            else:
                return public.returnMsg(True, '删除失败，{}'.format(response.text))
        except Exception as e:
            return public.returnMsg(False, '删除失败，msg：{}'.format(e))
