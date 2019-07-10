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

    def create_dns_record(self, domain_name, domain_dns_value):
        self.logger.info("create_dns_record")
        # if we have been given a wildcard name, strip wildcard
        domain_name = domain_name.lstrip("*.")
        subd = ""
        if domain_name.count(".") != 1:  # not top level domain
            pos = domain_name.rfind(".", 0, domain_name.rfind("."))
            subd = domain_name[:pos]
            domain_name = domain_name[pos + 1 :]
            if subd != "":
                subd = "." + subd

        url = urlparse.urljoin(self.DNSPOD_API_BASE_URL, "Record.Create")
        body = {
            "record_type": "TXT",
            "domain": domain_name,
            "sub_domain": "_acme-challenge" + subd,
            "value": domain_dns_value,
            "record_line_id": "0",
            "format": "json",
            "login_token": self.DNSPOD_LOGIN,
        }
        create_dnspod_dns_record_response = requests.post(
            url, data=body, timeout=self.HTTP_TIMEOUT
        ).json()
        self.logger.debug(
            "create_dnspod_dns_record_response. status_code={0}. response={1}".format(
                create_dnspod_dns_record_response["status"]["code"],
                create_dnspod_dns_record_response["status"]["message"],
            )
        )
        if create_dnspod_dns_record_response["status"]["code"] != "1":
            # raise error so that we do not continue to make calls to ACME
            # server
            raise ValueError(
                "Error creating dnspod dns record: status_code={status_code} response={response}".format(
                    status_code=create_dnspod_dns_record_response["status"]["code"],
                    response=create_dnspod_dns_record_response["status"]["message"],
                )
            )
        self.logger.info("create_dns_record_end")

    def delete_dns_record(self, domain_name, domain_dns_value):
        self.logger.info("delete_dns_record")
        domain_name = domain_name.lstrip("*.")
        subd = ""
        if domain_name.count(".") != 1:  # not top level domain
            pos = domain_name.rfind(".", 0, domain_name.rfind("."))
            subd = domain_name[:pos]
            domain_name = domain_name[pos + 1 :]
            if subd != "":
                subd = "." + subd

        url = urllib.parse.urljoin(self.DNSPOD_API_BASE_URL, "Record.List")
        # pos = domain_name.rfind(".",0, domain_name.rfind("."))
        subdomain = "_acme-challenge." + subd
        rootdomain = domain_name
        body = {
            "login_token": self.DNSPOD_LOGIN,
            "format": "json",
            "domain": rootdomain,
            "subdomain": subdomain,
            "record_type": "TXT",
        }
        list_dns_response = requests.post(url, data=body, timeout=self.HTTP_TIMEOUT).json()
        if list_dns_response["status"]["code"] != "1":
            self.logger.error(
                "list_dns_record_response. status_code={0}. message={1}".format(
                    list_dns_response["status"]["code"], list_dns_response["status"]["message"]
                )
            )
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
            if delete_dns_record_response["status"]["code"] != "1":
                self.logger.error(
                    "delete_dns_record_response. status_code={0}. message={1}".format(
                        delete_dns_record_response["status"]["code"],
                        delete_dns_record_response["status"]["message"],
                    )
                )

        self.logger.info("delete_dns_record_success")
