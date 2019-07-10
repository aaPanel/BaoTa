import os
import logging
import argparse

from . import Client
from . import __version__ as sewer_version
from .config import ACME_DIRECTORY_URL_STAGING, ACME_DIRECTORY_URL_PRODUCTION


def main():
    """
    Usage:
        1. To get a new certificate:
        CLOUDFLARE_EMAIL=example@example.com \
        CLOUDFLARE_API_KEY=api-key \
        sewer \
        --dns cloudflare \
        --domain example.com \
        --action run

        2. To renew a certificate:
        CLOUDFLARE_EMAIL=example@example.com \
        CLOUDFLARE_API_KEY=api-key \
        sewer \
        --account_key /path/to/your/account.key \
        --dns cloudflare \
        --domain example.com \
        --action renew
    """
    parser = argparse.ArgumentParser(
        prog="sewer",
        description="""Sewer is a Let's Encrypt(ACME) client.
            Example usage::
            CLOUDFLARE_EMAIL=example@example.com \
            CLOUDFLARE_API_KEY=api-key \
            sewer \
            --dns cloudflare \
            --domain example.com \
            --action run""",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s {version}".format(version=sewer_version.__version__),
        help="The currently installed sewer version.",
    )
    parser.add_argument(
        "--account_key",
        type=argparse.FileType("r"),
        required=False,
        help="The path to your letsencrypt/acme account key. \
        eg: --account_key /home/myaccount.key",
    )
    parser.add_argument(
        "--certificate_key",
        type=argparse.FileType("r"),
        required=False,
        help="The path to your certificate key. \
        eg: --certificate_key /home/mycertificate.key",
    )
    parser.add_argument(
        "--dns",
        type=str,
        required=True,
        choices=[
            "cloudflare",
            "aurora",
            "acmedns",
            "aliyun",
            "hurricane",
            "rackspace",
            "dnspod",
            "duckdns",
        ],
        help="The name of the dns provider that you want to use.",
    )
    parser.add_argument(
        "--domain",
        type=str,
        required=True,
        help="The domain/subdomain name for which \
        you want to get/renew certificate for. \
        wildcards are also supported \
        eg: --domain example.com",
    )
    parser.add_argument(
        "--alt_domains",
        type=str,
        required=False,
        default=[],
        nargs="*",
        help="A list of alternative domain/subdomain name/s(if any) for which \
        you want to get/renew certificate for. \
        eg: --alt_domains www.example.com blog.example.com",
    )
    parser.add_argument(
        "--bundle_name",
        type=str,
        required=False,
        help="The name to use for certificate \
        certificate key and account key. Default is name of domain.",
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        required=False,
        default="production",
        choices=["production", "staging"],
        help="Whether to use letsencrypt/acme production/live endpoints \
        or staging endpoints. production endpoints are used by default. \
        eg: --endpoint staging",
    )
    parser.add_argument(
        "--email",
        type=str,
        required=False,
        help="Email to be used for registration and recovery. \
        eg: --email me@example.com",
    )
    parser.add_argument(
        "--action",
        type=str,
        required=True,
        choices=["run", "renew"],
        help="The action that you want to perform. \
        Either run (get a new certificate) or renew (renew a certificate). \
        eg: --action run",
    )
    parser.add_argument(
        "--out_dir",
        type=str,
        required=False,
        default=os.getcwd(),
        help="""The dir where the certificate and keys file will be stored.
            default:  The directory you run sewer command.
            eg: --out_dir /data/ssl/
            """,
    )
    parser.add_argument(
        "--loglevel",
        type=str,
        required=False,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="The log level to output log messages at. \
        eg: --loglevel DEBUG",
    )

    args = parser.parse_args()

    dns_provider = args.dns
    domain = args.domain
    alt_domains = args.alt_domains
    action = args.action
    account_key = args.account_key
    certificate_key = args.certificate_key
    bundle_name = args.bundle_name
    endpoint = args.endpoint
    email = args.email
    loglevel = args.loglevel
    out_dir = args.out_dir

    # Make sure the output dir user specified is writable
    if not os.access(out_dir, os.W_OK):
        raise OSError("The dir '{0}' is not writable".format(out_dir))

    logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)
    logger.setLevel(loglevel)

    if account_key:
        account_key = account_key.read()
    if certificate_key:
        certificate_key = certificate_key.read()
    if bundle_name:
        file_name = bundle_name
    else:
        file_name = "{0}".format(domain)
    if endpoint == "staging":
        ACME_DIRECTORY_URL = ACME_DIRECTORY_URL_STAGING
    else:
        ACME_DIRECTORY_URL = ACME_DIRECTORY_URL_PRODUCTION

    if dns_provider == "cloudflare":
        from . import CloudFlareDns

        try:
            CLOUDFLARE_EMAIL = os.environ["CLOUDFLARE_EMAIL"]
            CLOUDFLARE_API_KEY = os.environ["CLOUDFLARE_API_KEY"]

            dns_class = CloudFlareDns(
                CLOUDFLARE_EMAIL=CLOUDFLARE_EMAIL, CLOUDFLARE_API_KEY=CLOUDFLARE_API_KEY
            )
            logger.info("chosen_dns_provider. Using {0} as dns provider.".format(dns_provider))
        except KeyError as e:
            logger.error("ERROR:: Please supply {0} as an environment variable.".format(str(e)))
            raise

    elif dns_provider == "aurora":
        from . import AuroraDns

        try:
            AURORA_API_KEY = os.environ["AURORA_API_KEY"]
            AURORA_SECRET_KEY = os.environ["AURORA_SECRET_KEY"]

            dns_class = AuroraDns(
                AURORA_API_KEY=AURORA_API_KEY, AURORA_SECRET_KEY=AURORA_SECRET_KEY
            )
            logger.info("chosen_dns_provider. Using {0} as dns provider.".format(dns_provider))
        except KeyError as e:
            logger.error("ERROR:: Please supply {0} as an environment variable.".format(str(e)))
            raise

    elif dns_provider == "acmedns":
        from . import AcmeDnsDns

        try:
            ACME_DNS_API_USER = os.environ["ACME_DNS_API_USER"]
            ACME_DNS_API_KEY = os.environ["ACME_DNS_API_KEY"]
            ACME_DNS_API_BASE_URL = os.environ["ACME_DNS_API_BASE_URL"]

            dns_class = AcmeDnsDns(
                ACME_DNS_API_USER=ACME_DNS_API_USER,
                ACME_DNS_API_KEY=ACME_DNS_API_KEY,
                ACME_DNS_API_BASE_URL=ACME_DNS_API_BASE_URL,
            )
            logger.info("chosen_dns_provider. Using {0} as dns provider.".format(dns_provider))
        except KeyError as e:
            logger.error("ERROR:: Please supply {0} as an environment variable.".format(str(e)))
            raise
    elif dns_provider == "aliyun":
        from . import AliyunDns

        try:
            aliyun_ak = os.environ["ALIYUN_AK_ID"]
            aliyun_secret = os.environ["ALIYUN_AK_SECRET"]
            aliyun_endpoint = os.environ.get("ALIYUN_ENDPOINT", "cn-beijing")
            dns_class = AliyunDns(aliyun_ak, aliyun_secret, aliyun_endpoint)
            logger.info("chosen_dns_provider. Using {0} as dns provider.".format(dns_provider))
        except KeyError as e:
            logger.error("ERROR:: Please supply {0} as an environment variable.".format(str(e)))
            raise
    elif dns_provider == "hurricane":
        from . import HurricaneDns

        try:
            he_username = os.environ["HURRICANE_USERNAME"]
            he_password = os.environ["HURRICANE_PASSWORD"]
            dns_class = HurricaneDns(he_username, he_password)
            logger.info("chosen_dns_provider. Using {0} as dns provider.".format(dns_provider))
        except KeyError as e:
            logger.error("ERROR:: Please supply {0} as an environment variable.".format(str(e)))
            raise
    elif dns_provider == "rackspace":
        from . import RackspaceDns

        try:
            RACKSPACE_USERNAME = os.environ["RACKSPACE_USERNAME"]
            RACKSPACE_API_KEY = os.environ["RACKSPACE_API_KEY"]
            dns_class = RackspaceDns(RACKSPACE_USERNAME, RACKSPACE_API_KEY)
            logger.info("chosen_dns_prover. Using {0} as dns provider. ".format(dns_provider))
        except KeyError as e:
            logger.error("ERROR:: Please supply {0} as an environment variable.".format(str(e)))
            raise
    elif dns_provider == "dnspod":
        from . import DNSPodDns

        try:
            DNSPOD_ID = os.environ["DNSPOD_ID"]
            DNSPOD_API_KEY = os.environ["DNSPOD_API_KEY"]
            dns_class = DNSPodDns(DNSPOD_ID, DNSPOD_API_KEY)
            logger.info("chosen_dns_prover. Using {0} as dns provider. ".format(dns_provider))
        except KeyError as e:
            logger.error("ERROR:: Please supply {0} as an environment variable.".format(str(e)))
            raise
    elif dns_provider == "duckdns":
        from . import DuckDNSDns

        try:
            duckdns_token = os.environ["DUCKDNS_TOKEN"]

            dns_class = DuckDNSDns(duckdns_token=duckdns_token)
            logger.info("chosen_dns_provider. Using {0} as dns provider.".format(dns_provider))
        except KeyError as e:
            logger.error("ERROR:: Please supply {0} as an environment variable.".format(str(e)))
            raise
    else:
        raise ValueError("The dns provider {0} is not recognised.".format(dns_provider))

    client = Client(
        domain_name=domain,
        dns_class=dns_class,
        domain_alt_names=alt_domains,
        contact_email=email,
        account_key=account_key,
        certificate_key=certificate_key,
        ACME_DIRECTORY_URL=ACME_DIRECTORY_URL,
        LOG_LEVEL=loglevel,
    )
    certificate_key = client.certificate_key
    account_key = client.account_key

    # prepare file path
    account_key_file_path = os.path.join(out_dir, "{0}.account.key".format(file_name))
    crt_file_path = os.path.join(out_dir, "{0}.crt".format(file_name))
    crt_key_file_path = os.path.join(out_dir, "{0}.key".format(file_name))

    # write out account_key in out_dir directory
    with open(account_key_file_path, "w") as account_file:
        account_file.write(account_key)
    logger.info("account key succesfully written to {0}.".format(account_key_file_path))

    if action == "renew":
        message = "Certificate Succesfully renewed. The certificate, certificate key and account key have been saved in the current directory"
        certificate = client.renew()
    else:
        message = "Certificate Succesfully issued. The certificate, certificate key and account key have been saved in the current directory"
        certificate = client.cert()

    # write out certificate and certificate key in out_dir directory
    with open(crt_file_path, "w") as certificate_file:
        certificate_file.write(certificate)
    with open(crt_key_file_path, "w") as certificate_key_file:
        certificate_key_file.write(certificate_key)

    logger.info("certificate succesfully written to {0}.".format(crt_file_path))
    logger.info("certificate key succesfully written to {0}.".format(crt_key_file_path))

    logger.info("the_end. {0}".format(message))
