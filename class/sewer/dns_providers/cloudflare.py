try:
	import urllib.parse as urlparse
except:
	import urlparse

import requests

from . import common


class CloudFlareDns(common.BaseDns):
    """
    """

    dns_provider_name = "cloudflare"

    def __init__(
        self,
        CLOUDFLARE_EMAIL,
        CLOUDFLARE_API_KEY,
        CLOUDFLARE_API_BASE_URL="https://api.cloudflare.com/client/v4/",
    ):
        self.CLOUDFLARE_DNS_ZONE_ID = None
        self.CLOUDFLARE_EMAIL = CLOUDFLARE_EMAIL
        self.CLOUDFLARE_API_KEY = CLOUDFLARE_API_KEY
        self.CLOUDFLARE_API_BASE_URL = CLOUDFLARE_API_BASE_URL
        self.HTTP_TIMEOUT = 65  # seconds

        if CLOUDFLARE_API_BASE_URL[-1] != "/":
            self.CLOUDFLARE_API_BASE_URL = CLOUDFLARE_API_BASE_URL + "/"
        else:
            self.CLOUDFLARE_API_BASE_URL = CLOUDFLARE_API_BASE_URL
        super(CloudFlareDns, self).__init__()

    def find_dns_zone(self, domain_name):
        url = urlparse.urljoin(self.CLOUDFLARE_API_BASE_URL, "zones?status=active")
        headers = {"X-Auth-Email": self.CLOUDFLARE_EMAIL, "X-Auth-Key": self.CLOUDFLARE_API_KEY}
        find_dns_zone_response = requests.get(url, headers=headers, timeout=self.HTTP_TIMEOUT)
        if find_dns_zone_response.status_code != 200:
            raise ValueError(
                "Error creating cloudflare dns record: status_code={status_code} response={response}".format(
                    status_code=find_dns_zone_response.status_code,
                    response=self.log_response(find_dns_zone_response),
                )
            )

        result = find_dns_zone_response.json()["result"]
        for i in result:
            if i["name"] in domain_name:
                setattr(self, "CLOUDFLARE_DNS_ZONE_ID", i["id"])
        if isinstance(self.CLOUDFLARE_DNS_ZONE_ID, type(None)):
            raise ValueError(
                "Error unable to get DNS zone for domain_name={domain_name}: status_code={status_code} response={response}".format(
                    domain_name=domain_name,
                    status_code=find_dns_zone_response.status_code,
                    response=self.log_response(find_dns_zone_response),
                )
            )


    def create_dns_record(self, domain_name, domain_dns_value):
        # if we have been given a wildcard name, strip wildcard
        domain_name = domain_name.lstrip("*.")
        self.find_dns_zone(domain_name)

        url = urllib.parse.urljoin(
            self.CLOUDFLARE_API_BASE_URL,
            "zones/{0}/dns_records".format(self.CLOUDFLARE_DNS_ZONE_ID),
        )
        headers = {"X-Auth-Email": self.CLOUDFLARE_EMAIL, "X-Auth-Key": self.CLOUDFLARE_API_KEY}
        body = {
            "type": "TXT",
            "name": "_acme-challenge" + "." + domain_name + ".",
            "content": "{0}".format(domain_dns_value),
        }
        create_cloudflare_dns_record_response = requests.post(
            url, headers=headers, json=body, timeout=self.HTTP_TIMEOUT
        )
        if create_cloudflare_dns_record_response.status_code != 200:
            # raise error so that we do not continue to make calls to ACME
            # server
            raise ValueError(
                "Error creating cloudflare dns record: status_code={status_code} response={response}".format(
                    status_code=create_cloudflare_dns_record_response.status_code,
                    response=self.log_response(create_cloudflare_dns_record_response),
                )
            )
    def delete_dns_record(self, domain_name, domain_dns_value):
        class MockResponse(object):
            def __init__(self, status_code=200, content="mock-response"):
                self.status_code = status_code
                self.content = content
                super(MockResponse, self).__init__()

            def json(self):
                return {}

        delete_dns_record_response = MockResponse()
        headers = {"X-Auth-Email": self.CLOUDFLARE_EMAIL, "X-Auth-Key": self.CLOUDFLARE_API_KEY}

        dns_name = "_acme-challenge" + "." + domain_name
        list_dns_payload = {"type": "TXT", "name": dns_name}
        list_dns_url = urllib.parse.urljoin(
            self.CLOUDFLARE_API_BASE_URL,
            "zones/{0}/dns_records".format(self.CLOUDFLARE_DNS_ZONE_ID),
        )

        list_dns_response = requests.get(
            list_dns_url, params=list_dns_payload, headers=headers, timeout=self.HTTP_TIMEOUT
        )

        for i in range(0, len(list_dns_response.json()["result"])):
            dns_record_id = list_dns_response.json()["result"][i]["id"]
            url = urllib.parse.urljoin(
                self.CLOUDFLARE_API_BASE_URL,
                "zones/{0}/dns_records/{1}".format(self.CLOUDFLARE_DNS_ZONE_ID, dns_record_id),
            )
            headers = {"X-Auth-Email": self.CLOUDFLARE_EMAIL, "X-Auth-Key": self.CLOUDFLARE_API_KEY}
            delete_dns_record_response = requests.delete(
                url, headers=headers, timeout=self.HTTP_TIMEOUT
            )

