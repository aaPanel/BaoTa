try:
	import urllib.parse as urlparse
except:
	import urlparse
import requests
from . import common

try:
    rackspace_dependencies = True
    import tldextract
except ImportError:
    rackspace_dependencies = False

import time


class RackspaceDns(common.BaseDns):
    """
    """

    dns_providername = "rackspace"

    def get_rackspace_credentials(self):
        RACKSPACE_IDENTITY_URL = "https://identity.api.rackspacecloud.com/v2.0/tokens"
        payload = {
            "auth": {
                "RAX-KSKEY:apiKeyCredentials": {
                    "username": self.RACKSPACE_USERNAME,
                    "apiKey": self.RACKSPACE_API_KEY,
                }
            }
        }
        find_rackspace_api_details_response = requests.post(RACKSPACE_IDENTITY_URL, json=payload)
        if find_rackspace_api_details_response.status_code != 200:
            raise ValueError(
                "Error getting token and URL details from rackspace identity server: status_code={status_code} response={response}".format(
                    status_code=find_rackspace_api_details_response.status_code,
                    response=self.log_response(find_rackspace_api_details_response),
                )
            )
        data = find_rackspace_api_details_response.json()
        api_token = data["access"]["token"]["id"]
        url_data = next(
            (item for item in data["access"]["serviceCatalog"] if item["type"] == "rax:dns"), None
        )
        if url_data is None:
            raise ValueError(
                "Error finding url data for the rackspace dns api in the response from the identity server"
            )
        else:
            api_base_url = url_data["endpoints"][0]["publicURL"] + "/"
        return (api_token, api_base_url)

    def __init__(self, RACKSPACE_USERNAME, RACKSPACE_API_KEY):

        if not rackspace_dependencies:
            raise ImportError(
                """You need to install RackspaceDns dependencies. run; pip3 install sewer[rackspace]"""
            )
        self.RACKSPACE_DNS_ZONE_ID = None
        self.RACKSPACE_USERNAME = RACKSPACE_USERNAME
        self.RACKSPACE_API_KEY = RACKSPACE_API_KEY
        self.HTTP_TIMEOUT = 65  # seconds
        super(RackspaceDns, self).__init__()
        self.RACKSPACE_API_TOKEN, self.RACKSPACE_API_BASE_URL = self.get_rackspace_credentials()
        self.RACKSPACE_HEADERS = {
            "X-Auth-Token": self.RACKSPACE_API_TOKEN,
            "Content-Type": "application/json",
        }

    def get_dns_zone(self, domain_name):
        extracted_domain = tldextract.extract(domain_name)
        self.RACKSPACE_DNS_ZONE = ".".join([extracted_domain.domain, extracted_domain.suffix])

    def find_dns_zone_id(self, domain_name):
        self.get_dns_zone(domain_name)
        url = self.RACKSPACE_API_BASE_URL + "domains"
        find_dns_zone_id_response = requests.get(url, headers=self.RACKSPACE_HEADERS)
        if find_dns_zone_id_response.status_code != 200:
            raise ValueError(
                "Error getting rackspace dns domain info: status_code={status_code} response={response}".format(
                    status_code=find_dns_zone_id_response.status_code,
                    response=self.log_response(find_dns_zone_id_response),
                )
            )
        result = find_dns_zone_id_response.json()
        domain_data = next(
            (item for item in result["domains"] if item["name"] == self.RACKSPACE_DNS_ZONE), None
        )
        if domain_data is None:
            raise ValueError(
                "Error finding information for {dns_zone} in dns response data:\n{response_data})".format(
                    dns_zone=self.RACKSPACE_DNS_ZONE,
                    response_data=self.log_response(find_dns_zone_id_response),
                )
            )
        dns_zone_id = domain_data["id"]
        return dns_zone_id

    def find_dns_record_id(self, domain_name, domain_dns_value):
        self.RACKSPACE_DNS_ZONE_ID = self.find_dns_zone_id(domain_name)
        url = self.RACKSPACE_API_BASE_URL + "domains/{0}/records".format(self.RACKSPACE_DNS_ZONE_ID)
        find_dns_record_id_response = requests.get(url, headers=self.RACKSPACE_HEADERS)
        if find_dns_record_id_response.status_code != 200:
            raise ValueError(
                "Error finding dns records for {dns_zone}: status_code={status_code} response={response}".format(
                    dns_zone=self.RACKSPACE_DNS_ZONE,
                    status_code=find_dns_record_id_response.status_code,
                    response=self.log_response(find_dns_record_id_response),
                )
            )
        records = find_dns_record_id_response.json()["records"]
        RACKSPACE_RECORD_DATA = next(
            (item for item in records if item["data"] == domain_dns_value), None
        )
        if RACKSPACE_RECORD_DATA is None:
            raise ValueError(
                "Couldn't find record with name {domain_name}\ncontaining data: {domain_dns_value}\nin the response data:{response_data}".format(
                    domain_name=domain_name,
                    domain_dns_value=domain_dns_value,
                    response_data=self.log_response(find_dns_record_id_response),
                )
            )
        record_id = RACKSPACE_RECORD_DATA["id"]
        return record_id

    def poll_callback_url(self, callback_url):
        start_time = time.time()
        while True:
            callback_url_response = requests.get(callback_url, headers=self.RACKSPACE_HEADERS)
            if time.time() > start_time + self.HTTP_TIMEOUT:
                raise ValueError(
                    "Timed out polling callbackurl for dns record status.  Last status_code={status_code} last response={response}".format(
                        status_code=callback_url_response.status_code,
                        response=self.log_response(callback_url_response),
                    )
                )
            if callback_url_response.status_code != 200:
                raise Exception(
                    "Could not get dns record status from callback url.  Status code ={status_code}. response={response}".format(
                        status_code=callback_url_response.status_code,
                        response=self.log_response(callback_url_response),
                    )
                )
            if callback_url_response.json()["status"] == "ERROR":
                raise Exception(
                    "Error in creating/deleting dns record: status_Code={status_code}. response={response}".format(
                        status_code=callback_url_response.status_code,
                        response=self.log_response(callback_url_response),
                    )
                )
            if callback_url_response.json()["status"] == "COMPLETED":
                break

    def create_dns_record(self, domain_name, domain_dns_value):
        # strip wildcard if present
        domain_name = domain_name.lstrip("*.")
        self.RACKSPACE_DNS_ZONE_ID = self.find_dns_zone_id(domain_name)
        record_name = "_acme-challenge." + domain_name
        url = urlparse.urljoin(
            self.RACKSPACE_API_BASE_URL, "domains/{0}/records".format(self.RACKSPACE_DNS_ZONE_ID)
        )
        body = {
            "records": [{"name": record_name, "type": "TXT", "data": domain_dns_value, "ttl": 3600}]
        }
        create_rackspace_dns_record_response = requests.post(
            url, headers=self.RACKSPACE_HEADERS, json=body, timeout=self.HTTP_TIMEOUT
        )

        if create_rackspace_dns_record_response.status_code != 202:
            raise ValueError(
                "Error creating rackspace dns record: status_code={status_code} response={response}".format(
                    status_code=create_rackspace_dns_record_response.status_code,
                    response=create_rackspace_dns_record_response.text,
                )
            )
            # response=self.log_response(create_rackspace_dns_record_response)))
            # After posting the dns record we want created, the response gives us a url to check that will
        # update when the job is done
        callback_url = create_rackspace_dns_record_response.json()["callbackUrl"]
        self.poll_callback_url(callback_url)


    def delete_dns_record(self, domain_name, domain_dns_value):
        record_name = "_acme-challenge." + domain_name
        self.RACKSPACE_DNS_ZONE_ID = self.find_dns_zone_id(domain_name)
        self.RACKSPACE_RECORD_ID = self.find_dns_record_id(domain_name, domain_dns_value)
        url = self.RACKSPACE_API_BASE_URL + "domains/{domain_id}/records/?id={record_id}".format(
            domain_id=self.RACKSPACE_DNS_ZONE_ID, record_id=self.RACKSPACE_RECORD_ID
        )
        delete_dns_record_response = requests.delete(url, headers=self.RACKSPACE_HEADERS)
        # After sending a delete request, if all goes well, we get a 202 from the server and a URL that we can poll
        # to see when the job is done
        if delete_dns_record_response.status_code != 202:
            raise ValueError(
                "Error deleting rackspace dns record: status_code={status_code} response={response}".format(
                    status_code=delete_dns_record_response.status_code,
                    response=self.log_response(delete_dns_record_response),
                )
            )
        callback_url = delete_dns_record_response.json()["callbackUrl"]
        self.poll_callback_url(callback_url)
