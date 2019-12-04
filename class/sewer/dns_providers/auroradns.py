# DNS Provider for AuroRa DNS from the dutch hosting provider pcextreme
# https://www.pcextreme.nl/aurora/dns
# Aurora uses libcloud from apache
# https://libcloud.apache.org/
try:
    aurora_dependencies = True
    from libcloud.dns.providers import get_driver
    from libcloud.dns.types import Provider, RecordType
    import tldextract
except ImportError:
    aurora_dependencies = False
from . import common


class AuroraDns(common.BaseDns):
    """
    Todo: re-organize this class so that we make it easier to mock things out to
    facilitate better tests.
    """

    dns_provider_name = "aurora"

    def __init__(self, AURORA_API_KEY, AURORA_SECRET_KEY):

        if not aurora_dependencies:
            raise ImportError(
                """You need to install AuroraDns dependencies. run; pip3 install sewer[aurora]"""
            )

        self.AURORA_API_KEY = AURORA_API_KEY
        self.AURORA_SECRET_KEY = AURORA_SECRET_KEY
        super(AuroraDns, self).__init__()

    def create_dns_record(self, domain_name, domain_dns_value):
        # if we have been given a wildcard name, strip wildcard
        domain_name = domain_name.lstrip("*.")

        extractedDomain = tldextract.extract(domain_name)
        domainSuffix = extractedDomain.domain + "." + extractedDomain.suffix

        if extractedDomain.subdomain is "":
            subDomain = "_acme-challenge"
        else:
            subDomain = "_acme-challenge." + extractedDomain.subdomain

        cls = get_driver(Provider.AURORADNS)
        driver = cls(key=self.AURORA_API_KEY, secret=self.AURORA_SECRET_KEY)
        zone = driver.get_zone(domainSuffix)
        zone.create_record(name=subDomain, type=RecordType.TXT, data=domain_dns_value)

        return

    def delete_dns_record(self, domain_name, domain_dns_value):

        extractedDomain = tldextract.extract(domain_name)
        domainSuffix = extractedDomain.domain + "." + extractedDomain.suffix

        if extractedDomain.subdomain is "":
            subDomain = "_acme-challenge"
        else:
            subDomain = "_acme-challenge." + extractedDomain.subdomain

        cls = get_driver(Provider.AURORADNS)
        driver = cls(key=self.AURORA_API_KEY, secret=self.AURORA_SECRET_KEY)
        zone = driver.get_zone(domainSuffix)

        records = driver.list_records(zone)
        for x in records:
            if x.name == subDomain and x.type == "TXT":
                record_id = x.id
                record = driver.get_record(zone_id=zone.id, record_id=record_id)
                driver.delete_record(record)
        return
