try:
	import urllib.parse as urlparse
except:
	import urlparse
import requests

from . import common


class DuckDNSDns(common.BaseDns):

    dns_provider_name = "duckdns"

    def __init__(self, duckdns_token, DUCKDNS_API_BASE_URL="https://www.duckdns.org"):

        self.duckdns_token = duckdns_token
        self.HTTP_TIMEOUT = 65  # seconds

        if DUCKDNS_API_BASE_URL[-1] != "/":
            self.DUCKDNS_API_BASE_URL = DUCKDNS_API_BASE_URL + "/"
        else:
            self.DUCKDNS_API_BASE_URL = DUCKDNS_API_BASE_URL
        super(DuckDNSDns, self).__init__()

    def _common_dns_record(self, logger_info, domain_name, payload_end_arg):
        # if we have been given a wildcard name, strip wildcard
        domain_name = domain_name.lstrip("*.")
        # add provider domain to the domain name if not present
        provider_domain = ".duckdns.org"
        if domain_name.rfind(provider_domain) == -1:
            "".join((domain_name, provider_domain))

        url = urlparse.urljoin(self.DUCKDNS_API_BASE_URL, "update")

        payload = dict([("domains", domain_name), ("token", self.duckdns_token), payload_end_arg])
        update_duckdns_dns_record_response = requests.get(
            url, params=payload, timeout=self.HTTP_TIMEOUT
        )

        normalized_response = update_duckdns_dns_record_response.text

        if update_duckdns_dns_record_response.status_code != 200 or normalized_response != "OK":
            # raise error so that we do not continue to make calls to DuckDNS
            # server
            raise ValueError(
                "Error creating DuckDNS dns record: status_code={status_code} response={response}".format(
                    status_code=update_duckdns_dns_record_response.status_code,
                    response=normalized_response,
                )
            )

    def create_dns_record(self, domain_name, domain_dns_value):
        self._common_dns_record("create_dns_record", domain_name, ("txt", domain_dns_value))

    def delete_dns_record(self, domain_name, domain_dns_value):
        self._common_dns_record("delete_dns_record", domain_name, ("clear", "true"))
