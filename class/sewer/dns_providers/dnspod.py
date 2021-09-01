#coding: utf-8
try:
	import urllib.parse as urlparse
except:
	import urlparse

import requests

from . import common


class DNSPodDns(common.BaseDns):
    """
    """

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

    def extract_zone(self,domain_name):
        domain_name = domain_name.lstrip("*.")
        top_domain_list = ['.ac.cn', '.ah.cn', '.bj.cn', '.com.cn', '.cq.cn', '.fj.cn', '.gd.cn', 
                            '.gov.cn', '.gs.cn', '.gx.cn', '.gz.cn', '.ha.cn', '.hb.cn', '.he.cn', 
                            '.hi.cn', '.hk.cn', '.hl.cn', '.hn.cn', '.jl.cn', '.js.cn', '.jx.cn', 
                            '.ln.cn', '.mo.cn', '.net.cn', '.nm.cn', '.nx.cn', '.org.cn']
        old_domain_name = domain_name
        m_count = domain_name.count(".")
        top_domain = "."+".".join(domain_name.rsplit('.')[-2:])
        new_top_domain = "." + top_domain.replace(".","")
        is_tow_top = False
        if top_domain in top_domain_list:
            is_tow_top = True
            domain_name = domain_name[:-len(top_domain)] + new_top_domain

        if domain_name.count(".") > 1:
            zone, middle, last = domain_name.rsplit(".", 2)        
            acme_txt = "_acme-challenge.%s" % zone
            if is_tow_top: last = top_domain[1:]
            root = ".".join([middle, last])
        else:
            zone = ""
            root = old_domain_name
            acme_txt = "_acme-challenge"
        return root, zone, acme_txt

    def create_dns_record(self, domain_name, domain_dns_value):
        # if we have been given a wildcard name, strip wildcard
        #domain_name = domain_name.lstrip("*.")
        #subd = ""
        #if domain_name.count(".") != 1:  # not top level domain
        #    pos = domain_name.rfind(".", 0, domain_name.rfind("."))
        #    subd = domain_name[:pos]
        #    domain_name = domain_name[pos + 1 :]
        #    if subd != "":
        #        subd = "." + subd

        domain_name,_,subd = self.extract_zone(domain_name)
        url = urlparse.urljoin(self.DNSPOD_API_BASE_URL, "Record.Create")
        body = {
            "record_type": "TXT",
            "domain": domain_name,
            "sub_domain": subd,
            "value": domain_dns_value,
            "record_line_id": "0",
            "format": "json",
            "login_token": self.DNSPOD_LOGIN,
        }
        print(body)
        create_dnspod_dns_record_response = requests.post(
            url, data=body, timeout=self.HTTP_TIMEOUT
        ).json()
        if create_dnspod_dns_record_response["status"]["code"] != "1":
            # raise error so that we do not continue to make calls to ACME
            # server
            raise ValueError(
                "Error creating dnspod dns record: status_code={status_code} response={response}".format(
                    status_code=create_dnspod_dns_record_response["status"]["code"],
                    response=create_dnspod_dns_record_response["status"]["message"],
                )
            )

    def delete_dns_record(self, domain_name, domain_dns_value):
        #domain_name = domain_name.lstrip("*.")
        #subd = ""
        #if domain_name.count(".") != 1:  # not top level domain
        #    pos = domain_name.rfind(".", 0, domain_name.rfind("."))
        #    subd = domain_name[:pos]
        #    domain_name = domain_name[pos + 1 :]
        #    if subd != "":
        #        subd = "." + subd

        domain_name,_,subd = self.extract_zone(domain_name)
        url = urllib.parse.urljoin(self.DNSPOD_API_BASE_URL, "Record.List")
        # pos = domain_name.rfind(".",0, domain_name.rfind("."))
        subdomain = subd
        rootdomain = domain_name
        body = {
            "login_token": self.DNSPOD_LOGIN,
            "format": "json",
            "domain": rootdomain,
            "subdomain": subdomain,
            "record_type": "TXT",
        }
        print(body)
        list_dns_response = requests.post(url, data=body, timeout=self.HTTP_TIMEOUT).json()
        for i in range(0, len(list_dns_response["records"])):
            rid = list_dns_response["records"][i]["id"]
            urlr = urllib.parse.urljoin(self.DNSPOD_API_BASE_URL, "Record.Remove")
            bodyr = {
                "login_token": self.DNSPOD_LOGIN,
                "format": "json",
                "domain": rootdomain,
                "record_id": rid,
            }
            delete_dns_record_response = requests.post(
                urlr, data=bodyr, timeout=self.HTTP_TIMEOUT
            ).json()


