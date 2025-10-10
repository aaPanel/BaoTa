import os, sys, re, json, shutil, psutil, time
import uuid
from datetime import datetime
from hashlib import md5

from sslModel.base import sslBase
import public


class main(sslBase):

    def get_dnsapi_add_data(self):
        data = [
            {
                'name': 'DNSPod',
                'id': 'DNSPodDns',
                'params': ['ID', 'Token']
            },
            {
                'name': '阿里云DNS',
                'id': 'AliyunDns',
                'params': ['AccessKey', 'SecretKey']
            },
            {
                'name': '腾讯云DNS',
                'id': 'TencentCloudDns',
                'params': ['secret_id', 'secret_key']
            },
            {
                'name': '华为云DNS',
                'id': 'HuaweiCloudDns',
                'params': ['AccessKey', 'SecretKey', 'project_id']
            },
            {
                'name': 'CloudFlare',
                'id': 'CloudFlareDns',
                'params': ['E-Mail', 'API Key']
            },
            {
                'name': '西部数码',
                'id': 'WestDns',
                'params': ['user_name', 'api_password']
            },
            # godaddy接口访问不了，先注释
            # {
            #     'name': 'GoDaddy',
            #     'id': 'GoDaddyDns',
            #     'params': ['Key', 'Secret']
            # },
        ]
        return data

    def get_dns_data(self, get):
        api_data = super().get_dns_data(get)
        add_data = self.get_dnsapi_add_data()
        return {"data": [i for i in api_data.values()], "add_data": add_data}

    def add_dns_data(self, get):
        dns_name = get.dns_name
        ps = get.ps
        pdata = json.loads(get.pdata)

        if dns_name not in [i['id'] for i in self.get_dnsapi_add_data()]:
            return public.returnMsg(False, "暂不支持此类型")

        pdata.update({'id': uuid.uuid4().hex, 'ps': ps})

        sfile = "{}/config/dns_mager.conf".format(public.get_panel_path())
        try:
            data = json.loads(public.readFile(sfile))
        except:
            data = {}
        type_data = data.get(dns_name)
        if type_data:
            type_data.append(pdata)
        else:
            type_data = [pdata]
        data[dns_name] = type_data
        public.writeFile(sfile, json.dumps(data))
        return public.returnMsg(True, "添加成功")

    def del_dns_data(self, get):
        dns_id = get.dns_id

        sfile = "{}/config/dns_mager.conf".format(public.get_panel_path())
        data = json.loads(public.readFile(sfile))

        for key in data.keys():
            for val in data[key]:
                if val['id'] == dns_id:
                    data[key].remove(val)
        public.writeFile(sfile, json.dumps(data))
        return public.returnMsg(True, "删除成功")

    def upd_dns_data(self, get):
        dns_id = get.dns_id
        ps = get.ps
        pdata = {}
        if 'pdata' in get:
            pdata = json.loads(get.pdata)
        pdata.update({'ps': ps})
        sfile = "{}/config/dns_mager.conf".format(public.get_panel_path())
        data = json.loads(public.readFile(sfile))

        for key in data.keys():
            for val in data[key]:
                if val['id'] == dns_id:
                    val.update(pdata)
        public.writeFile(sfile, json.dumps(data))
        return public.returnMsg(True, "修改成功")



