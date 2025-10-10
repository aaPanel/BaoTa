import time
import copy
import json
import base64
import hashlib
import logging
import binascii
import platform
import sys
import http_requests as requests
import OpenSSL
import cryptography
from . import __version__ as sewer_version
from .config import ACME_DIRECTORY_URL_PRODUCTION



class Client(object):
    """
    todo: improve documentation.

    usage:
        import sewer
        dns_class = sewer.CloudFlareDns(CLOUDFLARE_EMAIL='example@example.com',
                                        CLOUDFLARE_API_KEY='nsa-grade-api-key')

        1. to create a new certificate.
        client = sewer.Client(domain_name='example.com',
                              dns_class=dns_class)
        certificate = client.cert()
        certificate_key = client.certificate_key
        account_key = client.account_key

        with open('certificate.crt', 'w') as certificate_file:
            certificate_file.write(certificate)

        with open('certificate.key', 'w') as certificate_key_file:
            certificate_key_file.write(certificate_key)


        2. to renew a certificate:
        with open('account_key.key', 'r') as account_key_file:
            account_key = account_key_file.read()

        client = sewer.Client(domain_name='example.com',
                              dns_class=dns_class,
                              account_key=account_key)
        certificate = client.renew()
        certificate_key = client.certificate_key

    todo:
        - handle more exceptions
    """

    def __init__(
        self,
        domain_name,
        dns_class,
        domain_alt_names=None,
        contact_email=None,
        account_key=None,
        certificate_key=None,
        bits=2048,
        digest="sha256",
        ACME_REQUEST_TIMEOUT=7,
        ACME_AUTH_STATUS_WAIT_PERIOD=8,
        ACME_AUTH_STATUS_MAX_CHECKS=3,
        ACME_DIRECTORY_URL=ACME_DIRECTORY_URL_PRODUCTION,
        LOG_LEVEL="INFO",
    ):

        self.domain_name = domain_name
        self.dns_class = dns_class
        if not domain_alt_names:
            domain_alt_names = []
        self.domain_alt_names = domain_alt_names
        self.domain_alt_names = list(set(self.domain_alt_names))
        self.contact_email = contact_email
        self.bits = bits
        self.digest = digest
        self.ACME_REQUEST_TIMEOUT = ACME_REQUEST_TIMEOUT
        self.ACME_AUTH_STATUS_WAIT_PERIOD = ACME_AUTH_STATUS_WAIT_PERIOD
        self.ACME_AUTH_STATUS_MAX_CHECKS = ACME_AUTH_STATUS_MAX_CHECKS
        self.ACME_DIRECTORY_URL = ACME_DIRECTORY_URL
        self.LOG_LEVEL = LOG_LEVEL.upper()

        try:
            self.all_domain_names = copy.copy(self.domain_alt_names)
            self.all_domain_names.insert(0, self.domain_name)
            self.domain_alt_names = list(set(self.domain_alt_names))

            self.User_Agent = self.get_user_agent()
            acme_endpoints = self.get_acme_endpoints().json()
            self.ACME_GET_NONCE_URL = acme_endpoints["newNonce"]
            self.ACME_TOS_URL = acme_endpoints["meta"]["termsOfService"]
            self.ACME_KEY_CHANGE_URL = acme_endpoints["keyChange"]
            self.ACME_NEW_ACCOUNT_URL = acme_endpoints["newAccount"]
            self.ACME_NEW_ORDER_URL = acme_endpoints["newOrder"]
            self.ACME_REVOKE_CERT_URL = acme_endpoints["revokeCert"]

            # unique account identifier
            # https://tools.ietf.org/html/draft-ietf-acme-acme#section-6.2
            self.kid = None

            self.certificate_key = certificate_key or self.create_certificate_key()
            self.csr = self.create_csr()

            if not account_key:
                self.account_key = self.create_account_key()
                self.PRIOR_REGISTERED = False
            else:
                self.account_key = account_key
                self.PRIOR_REGISTERED = True

        except Exception as e:
            raise e

    @staticmethod
    def log_response(response):
        """
        renders response as json or as a string
        """
        # TODO: use this to handle all response logs.
        try:
            log_body = response.json()
        except ValueError:
            log_body = response.content[:30]
        return log_body

    @staticmethod
    def get_user_agent():
        return "python-requests/{requests_version} ({system}: {machine}) sewer {sewer_version} ({sewer_url})".format(
            requests_version=requests.__version__,
            system=platform.system(),
            machine=platform.machine(),
            sewer_version=sewer_version.__version__,
            sewer_url=sewer_version.__url__,
        )

    def get_acme_endpoints(self):
        headers = {"User-Agent": self.User_Agent}
        get_acme_endpoints = requests.get(
            self.ACME_DIRECTORY_URL, timeout=self.ACME_REQUEST_TIMEOUT, headers=headers,verify=False
        )
        if get_acme_endpoints.status_code not in [200, 201]:
            raise ValueError(
                "Error while getting Acme endpoints: status_code={status_code} response={response}".format(
                    status_code=get_acme_endpoints.status_code,
                    response=self.log_response(get_acme_endpoints),
                )
            )
        return get_acme_endpoints

    def create_certificate_key(self):
        return self.create_key().decode()

    def create_account_key(self):
        return self.create_key().decode()

    def create_key(self, key_type=OpenSSL.crypto.TYPE_RSA):
        key = OpenSSL.crypto.PKey()
        key.generate_key(key_type, self.bits)
        private_key = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key)
        return private_key

    def create_csr(self):
        """
        https://tools.ietf.org/html/draft-ietf-acme-acme#section-7.4
        The CSR is sent in the base64url-encoded version of the DER format. (NB: this
        field uses base64url, and does not include headers, it is different from PEM.)
        """
        X509Req = OpenSSL.crypto.X509Req()
        X509Req.get_subject().CN = self.domain_name

        if self.domain_alt_names:
            SAN = "DNS:{0}, ".format(self.domain_name).encode("utf8") + ", ".join(
                "DNS:" + i for i in self.domain_alt_names
            ).encode("utf8")
        else:
            SAN = "DNS:{0}".format(self.domain_name).encode("utf8")

        X509Req.add_extensions(
            [
                OpenSSL.crypto.X509Extension(
                    "subjectAltName".encode("utf8"), critical=False, value=SAN
                )
            ]
        )
        pk = OpenSSL.crypto.load_privatekey(
            OpenSSL.crypto.FILETYPE_PEM, self.certificate_key.encode()
        )
        X509Req.set_pubkey(pk)
        X509Req.set_version(2)
        X509Req.sign(pk, self.digest)
        return OpenSSL.crypto.dump_certificate_request(OpenSSL.crypto.FILETYPE_ASN1, X509Req)

    def acme_register(self):
        """
        https://tools.ietf.org/html/draft-ietf-acme-acme#section-7.3
        The server creates an account and stores the public key used to
        verify the JWS (i.e., the "jwk" element of the JWS header) to
        authenticate future requests from the account.
        The server returns this account object in a 201 (Created) response, with the account URL
        in a Location header field.
        This account URL will be used in subsequest requests to ACME, as the "kid" value in the acme header.
        If the server already has an account registered with the provided
        account key, then it MUST return a response with a 200 (OK) status
        code and provide the URL of that account in the Location header field.
        If there is an existing account with the new key
        provided, then the server SHOULD use status code 409 (Conflict) and
        provide the URL of that account in the Location header field
        """
        if self.PRIOR_REGISTERED:
            payload = {"onlyReturnExisting": True}
        elif self.contact_email:
            payload = {
                "termsOfServiceAgreed": True,
                "contact": ["mailto:{0}".format(self.contact_email)],
            }
        else:
            payload = {"termsOfServiceAgreed": True}

        url = self.ACME_NEW_ACCOUNT_URL
        acme_register_response = self.make_signed_acme_request(url=url, payload=payload)

        if acme_register_response.status_code not in [201, 200, 409]:
            raise ValueError(
                "Error while registering: status_code={status_code} response={response}".format(
                    status_code=acme_register_response.status_code,
                    response=self.log_response(acme_register_response),
                )
            )

        kid = acme_register_response.headers["Location"]
        setattr(self, "kid", kid)

        return acme_register_response

    def apply_for_cert_issuance(self):
        """
        https://tools.ietf.org/html/draft-ietf-acme-acme#section-7.4
        The order object returned by the server represents a promise that if
        the client fulfills the server's requirements before the "expires"
        time, then the server will be willing to finalize the order upon
        request and issue the requested certificate.  In the order object,
        any authorization referenced in the "authorizations" array whose
        status is "pending" represents an authorization transaction that the
        client must complete before the server will issue the certificate.

        Once the client believes it has fulfilled the server's requirements,
        it should send a POST request to the order resource's finalize URL.
        The POST body MUST include a CSR:

        The date values seem to be ignored by LetsEncrypt although they are
        in the ACME draft spec; https://tools.ietf.org/html/draft-ietf-acme-acme#section-7.4
        """
        identifiers = []
        for domain_name in self.all_domain_names:
            identifiers.append({"type": "dns", "value": domain_name})

        payload = {"identifiers": identifiers}
        url = self.ACME_NEW_ORDER_URL
        apply_for_cert_issuance_response = self.make_signed_acme_request(url=url, payload=payload)

        if apply_for_cert_issuance_response.status_code != 201:
            raise ValueError(
                "Error applying for certificate issuance: status_code={status_code} response={response}".format(
                    status_code=apply_for_cert_issuance_response.status_code,
                    response=self.log_response(apply_for_cert_issuance_response),
                )
            )

        apply_for_cert_issuance_response_json = apply_for_cert_issuance_response.json()
        finalize_url = apply_for_cert_issuance_response_json["finalize"]
        authorizations = apply_for_cert_issuance_response_json["authorizations"]

        return authorizations, finalize_url

    def get_identifier_authorization(self, url):
        """
        https://tools.ietf.org/html/draft-ietf-acme-acme#section-7.5
        When a client receives an order from the server it downloads the
        authorization resources by sending GET requests to the indicated
        URLs.  If the client initiates authorization using a request to the
        new authorization resource, it will have already received the pending
        authorization object in the response to that request.

        This is also where we get the challenges/tokens.
        """
        headers = {"User-Agent": self.User_Agent}
        get_identifier_authorization_response = requests.get(
            url, timeout=self.ACME_REQUEST_TIMEOUT, headers=headers,verify=False
        )
        if get_identifier_authorization_response.status_code not in [200, 201]:
            raise ValueError(
                "Error getting identifier authorization: status_code={status_code} response={response}".format(
                    status_code=get_identifier_authorization_response.status_code,
                    response=self.log_response(get_identifier_authorization_response),
                )
            )
        res = get_identifier_authorization_response.json()
        domain = res["identifier"]["value"]
        wildcard = res.get("wildcard")
        if wildcard:
            domain = "*." + domain

        for i in res["challenges"]:
            if i["type"] == "dns-01":
                dns_challenge = i
        dns_token = dns_challenge["token"]
        dns_challenge_url = dns_challenge["url"]
        identifier_auth = {
            "domain": domain,
            "url": url,
            "wildcard": wildcard,
            "dns_token": dns_token,
            "dns_challenge_url": dns_challenge_url,
        }


        return identifier_auth

    def get_keyauthorization(self, dns_token):
        acme_header_jwk_json = json.dumps(
            self.get_acme_header("GET_THUMBPRINT")["jwk"], sort_keys=True, separators=(",", ":")
        )
        acme_thumbprint = self.calculate_safe_base64(
            hashlib.sha256(acme_header_jwk_json.encode("utf8")).digest()
        )
        acme_keyauthorization = "{0}.{1}".format(dns_token, acme_thumbprint)
        base64_of_acme_keyauthorization = self.calculate_safe_base64(
            hashlib.sha256(acme_keyauthorization.encode("utf8")).digest()
        )

        return acme_keyauthorization, base64_of_acme_keyauthorization

    def check_authorization_status(self, authorization_url, desired_status=None):
        """
        https://tools.ietf.org/html/draft-ietf-acme-acme#section-7.5.1
        To check on the status of an authorization, the client sends a GET(polling)
        request to the authorization URL, and the server responds with the
        current authorization object.

        https://tools.ietf.org/html/draft-ietf-acme-acme#section-8.2
        Clients SHOULD NOT respond to challenges until they believe that the
        server's queries will succeed. If a server's initial validation
        query fails, the server SHOULD retry[intended to address things like propagation delays in
        HTTP/DNS provisioning] the query after some time.
        The server MUST provide information about its retry state to the
        client via the "errors" field in the challenge and the Retry-After
        """
        desired_status = desired_status or ["pending", "valid","invalid"]
        number_of_checks = 0
        while True:
            headers = {"User-Agent": self.User_Agent}
            check_authorization_status_response = requests.get(
                authorization_url, timeout=self.ACME_REQUEST_TIMEOUT, headers=headers,verify=False
            )
            a_auth = check_authorization_status_response.json()
            authorization_status = a_auth["status"]
            number_of_checks = number_of_checks + 1
            if number_of_checks == self.ACME_AUTH_STATUS_MAX_CHECKS:
                raise StopIteration(
                    "Checks done={0}. Max checks allowed={1}. Interval between checks={2}seconds. >>>> {3}".format(
                        number_of_checks,
                        self.ACME_AUTH_STATUS_MAX_CHECKS,
                        self.ACME_AUTH_STATUS_WAIT_PERIOD,
                        json.dumps(a_auth)
                    )
                )
            if authorization_status in desired_status:
                if authorization_status == "invalid":
                    try:
                        import panelLets
                        if 'error' in a_auth['challenges'][0]:
                            ret_title = a_auth['challenges'][0]['error']['detail']
                        elif 'error' in a_auth['challenges'][1]:
                            ret_title = a_auth['challenges'][1]['error']['detail']
                        elif 'error' in a_auth['challenges'][2]:
                            ret_title = a_auth['challenges'][2]['error']['detail']
                        else:
                            ret_title = str(a_auth)
                        ret_title = panelLets.panelLets().get_error(ret_title)
                    except:
                        ret_title = str(a_auth)
                    raise StopIteration(
                        "{0} >>>> {1}".format(
                            ret_title,
                            json.dumps(a_auth)
                        )
                    )
                break
            else:
                # for any other status, sleep then retry
                time.sleep(self.ACME_AUTH_STATUS_WAIT_PERIOD)

        return check_authorization_status_response

    def respond_to_challenge(self, acme_keyauthorization, dns_challenge_url):
        """
        https://tools.ietf.org/html/draft-ietf-acme-acme#section-7.5.1
        To prove control of the identifier and receive authorization, the
        client needs to respond with information to complete the challenges.
        The server is said to "finalize" the authorization when it has
        completed one of the validations, by assigning the authorization a
        status of "valid" or "invalid".

        Usually, the validation process will take some time, so the client
        will need to poll the authorization resource to see when it is finalized.
        To check on the status of an authorization, the client sends a GET(polling)
        request to the authorization URL, and the server responds with the
        current authorization object.
        """
        payload = {"keyAuthorization": "{0}".format(acme_keyauthorization)}
        respond_to_challenge_response = self.make_signed_acme_request(dns_challenge_url, payload)

        return respond_to_challenge_response

    def send_csr(self, finalize_url):
        """
        https://tools.ietf.org/html/draft-ietf-acme-acme#section-7.4
        Once the client believes it has fulfilled the server's requirements,
        it should send a POST request(include a CSR) to the order resource's finalize URL.
        A request to finalize an order will result in error if the order indicated does not have status "pending",
        if the CSR and order identifiers differ, or if the account is not authorized for the identifiers indicated in the CSR.
        The CSR is sent in the base64url-encoded version of the DER format(OpenSSL.crypto.FILETYPE_ASN1)

        A valid request to finalize an order will return the order to be finalized.
        The client should begin polling the order by sending a
        GET request to the order resource to obtain its current state.
        """
        payload = {"csr": self.calculate_safe_base64(self.csr)}
        send_csr_response = self.make_signed_acme_request(url=finalize_url, payload=payload)

        if send_csr_response.status_code not in [200, 201]:
            raise ValueError(
                "Error sending csr: status_code={status_code} response={response}".format(
                    status_code=send_csr_response.status_code,
                    response=self.log_response(send_csr_response),
                )
            )
        send_csr_response_json = send_csr_response.json()
        certificate_url = send_csr_response_json["certificate"]
        return certificate_url

    def download_certificate(self, certificate_url):
        download_certificate_response = self.make_signed_acme_request(
            certificate_url, payload="DOWNLOAD_Z_CERTIFICATE"
        )

        if download_certificate_response.status_code not in [200, 201]:
            raise ValueError(
                "Error fetching signed certificate: status_code={status_code} response={response}".format(
                    status_code=download_certificate_response.status_code,
                    response=self.log_response(download_certificate_response),
                )
            )


        pem_certificate = download_certificate_response.content
        if type(pem_certificate) == bytes: pem_certificate = pem_certificate.decode('utf-8')

        return pem_certificate

    def sign_message(self, message):
        pk = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, self.account_key.encode())
        return OpenSSL.crypto.sign(pk, message.encode("utf8"), self.digest)

    def get_nonce(self):
        """
        https://tools.ietf.org/html/draft-ietf-acme-acme#section-6.4
        Each request to an ACME server must include a fresh unused nonce
        in order to protect against replay attacks.
        """
        headers = {"User-Agent": self.User_Agent}
        response = requests.get(
            self.ACME_GET_NONCE_URL, timeout=self.ACME_REQUEST_TIMEOUT, headers=headers,verify=False
        )
        nonce = response.headers["Replay-Nonce"]
        return nonce

    @staticmethod
    def stringfy_items(payload):
        """
        method that takes a dictionary and then converts any keys or values
        in that are of type bytes into unicode strings.
        This is necessary esp if you want to then turn that dict into a json string.
        """
        if isinstance(payload, str):
            return payload

        for k, v in payload.items():
            if isinstance(k, bytes):
                k = k.decode("utf-8")
            if isinstance(v, bytes):
                v = v.decode("utf-8")
            payload[k] = v
        return payload

    @staticmethod
    def calculate_safe_base64(un_encoded_data):
        """
        takes in a string or bytes
        returns a string
        """
        if sys.version_info[0] == 3:
            if isinstance(un_encoded_data, str):
                un_encoded_data = un_encoded_data.encode("utf8")
        r = base64.urlsafe_b64encode(un_encoded_data).rstrip(b"=")
        return r.decode("utf8")

    def get_acme_header(self, url):
        """
        https://tools.ietf.org/html/draft-ietf-acme-acme#section-6.2
        The JWS Protected Header MUST include the following fields:
        - "alg" (Algorithm)
        - "jwk" (JSON Web Key, only for requests to new-account and revoke-cert resources)
        - "kid" (Key ID, for all other requests). gotten from self.ACME_NEW_ACCOUNT_URL
        - "nonce". gotten from self.ACME_GET_NONCE_URL
        - "url"
        """
        header = {"alg": "RS256", "nonce": self.get_nonce(), "url": url}

        if url in [self.ACME_NEW_ACCOUNT_URL, self.ACME_REVOKE_CERT_URL, "GET_THUMBPRINT"]:
            private_key = cryptography.hazmat.primitives.serialization.load_pem_private_key(
                self.account_key.encode(),
                password=None,
                backend=cryptography.hazmat.backends.default_backend(),
            )
            public_key_public_numbers = private_key.public_key().public_numbers()
            # private key public exponent in hex format
            exponent = "{0:x}".format(public_key_public_numbers.e)
            exponent = "0{0}".format(exponent) if len(exponent) % 2 else exponent
            # private key modulus in hex format
            modulus = "{0:x}".format(public_key_public_numbers.n)
            jwk = {
                "kty": "RSA",
                "e": self.calculate_safe_base64(binascii.unhexlify(exponent)),
                "n": self.calculate_safe_base64(binascii.unhexlify(modulus)),
            }
            header["jwk"] = jwk
        else:
            header["kid"] = self.kid
        return header

    def make_signed_acme_request(self, url, payload):
        headers = {"User-Agent": self.User_Agent}
        payload = self.stringfy_items(payload)

        if payload in ["GET_Z_CHALLENGE", "DOWNLOAD_Z_CERTIFICATE"]:
            response = requests.get(url, timeout=self.ACME_REQUEST_TIMEOUT, headers=headers,verify=False)
        else:
            payload64 = self.calculate_safe_base64(json.dumps(payload))
            protected = self.get_acme_header(url)
            protected64 = self.calculate_safe_base64(json.dumps(protected))
            signature = self.sign_message(message="{0}.{1}".format(protected64, payload64))  # bytes
            signature64 = self.calculate_safe_base64(signature)  # str
            data = json.dumps(
                {"protected": protected64, "payload": payload64, "signature": signature64}
            )
            headers.update({"Content-Type": "application/jose+json"})
            response = requests.post(
                url, data=data.encode("utf8"), timeout=self.ACME_REQUEST_TIMEOUT, headers=headers ,verify=False
            )
        return response

    def get_certificate(self):
        domain_dns_value = "placeholder"
        dns_names_to_delete = []
        try:
            self.acme_register()
            authorizations, finalize_url = self.apply_for_cert_issuance()
            responders = []
            for url in authorizations:
                identifier_auth = self.get_identifier_authorization(url)
                authorization_url = identifier_auth["url"]
                dns_name = identifier_auth["domain"]
                dns_token = identifier_auth["dns_token"]
                dns_challenge_url = identifier_auth["dns_challenge_url"]

                acme_keyauthorization, domain_dns_value = self.get_keyauthorization(dns_token)
                self.dns_class.create_dns_record(dns_name, domain_dns_value)
                dns_names_to_delete.append(
                    {"dns_name": dns_name, "domain_dns_value": domain_dns_value}
                )
                responders.append(
                    {
                        "authorization_url": authorization_url,
                        "acme_keyauthorization": acme_keyauthorization,
                        "dns_challenge_url": dns_challenge_url,
                    }
                )

            # for a case where you want certificates for *.example.com and example.com
            # you have to create both dns records AND then respond to the challenge.
            # see issues/83
            for i in responders:
                # Make sure the authorization is in a status where we can submit a challenge
                # response. The authorization can be in the "valid" state before submitting
                # a challenge response if there was a previous authorization for these hosts
                # that was successfully validated, still cached by the server.
                auth_status_response = self.check_authorization_status(i["authorization_url"])
                if auth_status_response.json()["status"] == "pending":
                    self.respond_to_challenge(i["acme_keyauthorization"], i["dns_challenge_url"])

            for i in responders:
                # Before sending a CSR, we need to make sure the server has completed the
                # validation for all the authorizations
                self.check_authorization_status(i["authorization_url"], ["valid"])

            certificate_url = self.send_csr(finalize_url)
            certificate = self.download_certificate(certificate_url)
        except Exception as e:
            raise e
        finally:
            for i in dns_names_to_delete:
                self.dns_class.delete_dns_record(i["dns_name"], i["domain_dns_value"])

        return certificate

    def cert(self):
        """
        convenience method to get a certificate without much hassle
        """
        return self.get_certificate()

    def renew(self):
        """
        renews a certificate.
        A renewal is actually just getting a new certificate.
        An issuance request counts as a renewal if it contains the exact same set of hostnames as a previously issued certificate.
            https://letsencrypt.org/docs/rate-limits/
        """
        return self.cert()
