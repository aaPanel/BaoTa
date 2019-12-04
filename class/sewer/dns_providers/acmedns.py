try:
	import urllib.parse as urlparse
except:
	import urlparse

try:
    acmedns_dependencies = True
    from dns.resolver import Resolver
except ImportError:
    acmedns_dependencies = False
import requests

from . import common


class AcmeDnsDns(common.BaseDns):
    """
    """

    dns_provider_name = "acmedns"

    def __init__(self, ACME_DNS_API_USER, ACME_DNS_API_KEY, ACME_DNS_API_BASE_URL):

        if not acmedns_dependencies:
            raise ImportError(
                """You need to install AcmeDnsDns dependencies. run; pip3 install sewer[acmedns]"""
            )

        self.ACME_DNS_API_USER = ACME_DNS_API_USER
        self.ACME_DNS_API_KEY = ACME_DNS_API_KEY
        self.HTTP_TIMEOUT = 65  # seconds

        if ACME_DNS_API_BASE_URL[-1] != "/":
            self.ACME_DNS_API_BASE_URL = ACME_DNS_API_BASE_URL + "/"
        else:
            self.ACME_DNS_API_BASE_URL = ACME_DNS_API_BASE_URL
        super(AcmeDnsDns, self).__init__()

    def create_dns_record(self, domain_name, domain_dns_value):
        # if we have been given a wildcard name, strip wildcard
        domain_name = domain_name.lstrip("*.")

        resolver = Resolver(configure=False)
        resolver.nameservers = ["8.8.8.8"]
        answer = resolver.query("_acme-challenge.{0}.".format(domain_name), "TXT")
        subdomain, _ = str(answer.canonical_name).split(".", 1)

        url = urlparse.urljoin(self.ACME_DNS_API_BASE_URL, "update")
        headers = {"X-Api-User": self.ACME_DNS_API_USER, "X-Api-Key": self.ACME_DNS_API_KEY}
        body = {"subdomain": subdomain, "txt": domain_dns_value}
        update_acmedns_dns_record_response = requests.post(
            url, headers=headers, json=body, timeout=self.HTTP_TIMEOUT
        )
        if update_acmedns_dns_record_response.status_code != 200:
            # raise error so that we do not continue to make calls to ACME
            # server
            raise ValueError(
                "Error creating acme-dns dns record: status_code={status_code} response={response}".format(
                    status_code=update_acmedns_dns_record_response.status_code,
                    response=self.log_response(update_acmedns_dns_record_response),
                )
            )

    def delete_dns_record(self, domain_name, domain_dns_value):
        pass
