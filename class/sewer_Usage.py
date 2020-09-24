#:coding:utf-8
# The MIT License (MIT)
#
# Copyright (c) 2017 Komu Wairagu
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "https://github.com/komuw/sewer", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys, os
import time
import copy
import json
import base64
import hashlib
import binascii
import urllib

if sys.version_info[0] == 2:  # python2
    import urlparse
    import urllib2
    import cryptography.hazmat
    import cryptography.hazmat.backends
    import cryptography.hazmat.primitives.serialization
else:  # python3
    from urllib.parse import urlparse
    import cryptography
import platform
import hmac
try:
    import requests
except:
    os.system('pip install requests')
    import requests
try:
    import OpenSSL
except:
    os.system('pip install pyopenssl')
    import OpenSSL
import random
import datetime
import logging
from hashlib import sha1

os.chdir("/www/server/panel")
if not 'class/' in sys.path:
    sys.path.insert(0,'class/')
import public


class ACMEclient(object):
    def __init__(
            self,
            dns_class,
            domain_alt_names=[],
            Manual=0,  # 手动验证 0 非手动,1 获取手动要添加的txt记录值,2 验证添加后的txt解析记录
            contact_email=None,
            account_key=None,
            certificate_key=None,
            bits=2048,
            digest="sha256",
            ACME_REQUEST_TIMEOUT=7,  # 请求超时时间/s
            ACME_AUTH_STATUS_WAIT_PERIOD=8,  # 认证等待时间/s
            ACME_AUTH_STATUS_MAX_CHECKS=3,  # 验证最大重试次数
            ACME_DIRECTORY_URL="https://acme-v02.api.letsencrypt.org/directory",
            LOG_LEVEL="INFO",
    ):
        self.Manual = Manual
        self.domain_name = domain_alt_names[0]
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

        self.logger = logging.getLogger()
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(handler)
        self.logger.setLevel(self.LOG_LEVEL)

        try:
            self.all_domain_names = copy.copy(self.domain_alt_names)
            # self.all_domain_names.insert(0, self.domain_name)
            self.domain_alt_names = list(set(self.domain_alt_names))

            self.User_Agent = self.get_user_agent()
            acme_endpoints = self.get_acme_endpoints().json()
            self.ACME_GET_NONCE_URL = acme_endpoints["newNonce"]
            self.ACME_TOS_URL = acme_endpoints["meta"]["termsOfService"]
            self.ACME_KEY_CHANGE_URL = acme_endpoints["keyChange"]
            self.ACME_NEW_ACCOUNT_URL = acme_endpoints["newAccount"]
            self.ACME_NEW_ORDER_URL = acme_endpoints["newOrder"]
            self.ACME_REVOKE_CERT_URL = acme_endpoints["revokeCert"]

            # 唯一帐户标识符
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

            print(
                "初始化成功,  domain_names={}, acme_server={}".format(
                    self.all_domain_names,
                    self.ACME_DIRECTORY_URL,
                )
            )
        except Exception as e:
            self.logger.error("无法初始化客户端. error={0}".format(str(e)))
            sys.exit(json.dumps({"data": "无法初始化acme客户端"}))

    @staticmethod
    def log_response(response):
        try:
            log_body = response.json()
        except ValueError:
            log_body = response.content[:30]
        return log_body

    @staticmethod
    def get_user_agent():
        return "{system}: {machine} ".format(
            system=platform.system(),
            machine=platform.machine(),
        )

    def get_acme_endpoints(self):
        print("获取_acme_端点")
        headers = {"User-Agent": self.User_Agent}
        i = 0
        while i < 3:
            try:
                get_acme_endpoints = requests.get(
                    self.ACME_DIRECTORY_URL, timeout=self.ACME_REQUEST_TIMEOUT, headers=headers
                )
            except Exception:
                i += 1
            else:
                break
        else:
            sys.exit(json.dumps({"data": "与 Let's Encrypt 的网络请求超时"}))

        if get_acme_endpoints.status_code not in [200, 201]:
            raise ValueError(
                "获取Acme端点时出错: status_code={status_code} response={response}".format(
                    status_code=get_acme_endpoints.status_code,
                    response=self.log_response(get_acme_endpoints),
                )
            )
        return get_acme_endpoints

    def create_certificate_key(self):
        print("创建certificate_key")
        return self.create_key().decode()

    def create_account_key(self):
        self.logger.debug("创建account_key")
        return self.create_key().decode()

    def create_key(self, key_type=OpenSSL.crypto.TYPE_RSA):
        key = OpenSSL.crypto.PKey()
        key.generate_key(key_type, self.bits)
        private_key = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key)
        return private_key

    def create_csr(self):
        print("创建_csr")
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
        print("acme注册")
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
            public.WriteFile(os.path.join(ssl_home_path, "apply_for_cert_issuance_response"), acme_register_response.text, mode="w")
            raise ValueError(
                "注册时出错： status_code={status_code} response={response}".format(
                    status_code=acme_register_response.status_code,
                    response=self.log_response(acme_register_response),
                )
            )
        kid = acme_register_response.headers["Location"]
        setattr(self, "kid", kid)
        print("acme_注册_成功")
        return acme_register_response

    def apply_for_cert_issuance(self):
        print("申请颁发证书")
        identifiers = []
        for domain_name in self.all_domain_names:
            identifiers.append({"type": "dns", "value": domain_name})
        payload = {"identifiers": identifiers}
        url = self.ACME_NEW_ORDER_URL
        apply_for_cert_issuance_response = self.make_signed_acme_request(url=url, payload=payload)
        if apply_for_cert_issuance_response.status_code != 201:
            public.WriteFile(os.path.join(ssl_home_path, "apply_for_cert_issuance_response"), apply_for_cert_issuance_response.text, mode="w")
            raise ValueError(
                "申请证书颁发时出错: status_code={status_code} response={response}".format(
                    status_code=apply_for_cert_issuance_response.status_code,
                    response=self.log_response(apply_for_cert_issuance_response),
                )
            )
        apply_for_cert_issuance_response_json = apply_for_cert_issuance_response.json()
        finalize_url = apply_for_cert_issuance_response_json["finalize"]
        authorizations = apply_for_cert_issuance_response_json["authorizations"]
        print("申请颁发证书成功")
        return authorizations, finalize_url

    def get_identifier_authorization(self, url):
        print("获得标识符授权")
        headers = {"User-Agent": self.User_Agent}
        i = 0
        while i < 3:
            try:
                get_identifier_authorization_response = requests.get(
                    url, timeout=self.ACME_REQUEST_TIMEOUT, headers=headers
                )
            except Exception:
                i += 1
            else:
                break
        else:
            sys.exit(json.dumps({"data": "与 Let's Encrypt 的网络请求超时"}))

        if get_identifier_authorization_response.status_code not in [200, 201]:
            raise ValueError(
                "获取标识符授权出错: status_code={status_code} response={response}".format(
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
        print(
            "获取标识符授权成功. identifier_auth={0}".format(identifier_auth)
        )

        return identifier_auth

    def get_keyauthorization(self, dns_token):
        print("获得密钥授权")
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

    def check_authorization_status(self, authorization_url, desired_status=None, dns_names_to_delete=[]):
        """
        检查授权的状态，验证dns有没有添加txt解析记录
        """
        print("检查授权状态")
        time.sleep(self.ACME_AUTH_STATUS_WAIT_PERIOD)  # 等待
        desired_status = desired_status or ["pending", "valid"]
        number_of_checks = 0
        while True:
            headers = {"User-Agent": self.User_Agent}
            i = 0
            while i < 3:
                try:
                    check_authorization_status_response = requests.get(
                        authorization_url, timeout=self.ACME_REQUEST_TIMEOUT, headers=headers
                    )
                except Exception:
                    i += 1
                else:
                    break
            else:
                sys.exit(json.dumps({"data": "与 Let's Encrypt 的网络请求超时"}))

            authorization_status = check_authorization_status_response.json()["status"]
            number_of_checks = number_of_checks + 1
            if number_of_checks == self.ACME_AUTH_STATUS_MAX_CHECKS:
                msg = "检查完成={0}.允许最大检查={1}. 检查之间的间隔={2}秒.".format(
                    number_of_checks,
                    self.ACME_AUTH_STATUS_MAX_CHECKS,
                    self.ACME_AUTH_STATUS_WAIT_PERIOD,
                )
                print (msg)
                for i in dns_names_to_delete:  # 验证失败后也删除添加的dns
                    self.dns_class.delete_dns_record(i["dns_name"], i["domain_dns_value"])
                sys.exit(json.dumps({"status": False, "data": "验证txt解析失败", "msg": msg, }))
            if authorization_status in desired_status:
                break
            else:
                print("验证dns txt 失败等待{}秒重新验证dns，返回的信息：".format(self.ACME_AUTH_STATUS_WAIT_PERIOD))
                print(check_authorization_status_response.json())
                public.WriteFile(os.path.join(ssl_home_path, "check_authorization_status_response"), check_authorization_status_response.text, mode="w")
                # 等待
                time.sleep(self.ACME_AUTH_STATUS_WAIT_PERIOD)
        print("检查授权状态结束")
        return check_authorization_status_response

    def respond_to_challenge(self, acme_keyauthorization, dns_challenge_url):
        print("回应challenge")
        payload = {"keyAuthorization": acme_keyauthorization}
        respond_to_challenge_response = self.make_signed_acme_request(dns_challenge_url, payload)
        print("回应challenge_成功")
        return respond_to_challenge_response

    def send_csr(self, finalize_url):
        self.logger.info("send_csr")
        payload = {"csr": self.calculate_safe_base64(self.csr)}
        send_csr_response = self.make_signed_acme_request(url=finalize_url, payload=payload)

        if send_csr_response.status_code not in [200, 201]:
            raise ValueError(
                "发送csr时出错: status_code={status_code} response={response}".format(
                    status_code=send_csr_response.status_code,
                    response=self.log_response(send_csr_response),
                )
            )
        send_csr_response_json = send_csr_response.json()
        certificate_url = send_csr_response_json["certificate"]
        print("send_csr_success")
        return certificate_url

    def download_certificate(self, certificate_url):
        print("下载证书")
        download_certificate_response = self.make_signed_acme_request(
            certificate_url, payload="DOWNLOAD_Z_CERTIFICATE"
        )
        if download_certificate_response.status_code not in [200, 201]:
            raise ValueError(
                "获取签名证书时出错: status_code={status_code} response={response}".format(
                    status_code=download_certificate_response.status_code,
                    response=self.log_response(download_certificate_response),
                )
            )
        pem_certificate = download_certificate_response.content.decode("utf-8")
        print("下载证书成功")
        return pem_certificate

    def sign_message(self, message):
        self.logger.debug("sign_message")
        pk = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, self.account_key.encode())
        return OpenSSL.crypto.sign(pk, message.encode("utf8"), self.digest)

    def get_nonce(self):
        """
        https://tools.ietf.org/html/draft-ietf-acme-acme#section-6.4
        对ACME服务器的每个请求都必须包含一个新的未使用的nonce 。
        """
        print("get_nonce")
        headers = {"User-Agent": self.User_Agent}
        i = 0
        while i < 3:
            try:
                response = requests.get(
                    self.ACME_GET_NONCE_URL, timeout=self.ACME_REQUEST_TIMEOUT, headers=headers
                )
            except Exception:
                i += 1
            else:
                break
        else:
            sys.exit(json.dumps({"data": "与 Let's Encrypt 的网络请求超时"}))

        nonce = response.headers["Replay-Nonce"]
        return nonce

    @staticmethod
    def stringfy_items(payload):
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
        if sys.version_info[0] == 3:
            if isinstance(un_encoded_data, str):
                un_encoded_data = un_encoded_data.encode("utf8")
        r = base64.urlsafe_b64encode(un_encoded_data).rstrip(b"=")
        return r.decode("utf8")

    def get_acme_header(self, url):
        print("get_acme_header")
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
        print("签署acme请求")
        headers = {"User-Agent": self.User_Agent}
        payload = self.stringfy_items(payload)
        if payload in ["GET_Z_CHALLENGE", "DOWNLOAD_Z_CERTIFICATE"]:
            i = 0
            while i < 3:
                try:
                    response = requests.get(url, timeout=self.ACME_REQUEST_TIMEOUT, headers=headers)
                except Exception:
                    i += 1
                else:
                    break
            else:
                sys.exit(json.dumps({"data": "与 Let's Encrypt 的网络请求超时"}))

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
            i = 0
            while i < 3:
                try:
                    response = requests.post(
                        url, data=data.encode("utf8"), timeout=self.ACME_REQUEST_TIMEOUT, headers=headers
                    )
                except Exception:
                    i += 1
                else:
                    break
            else:
                sys.exit(json.dumps({"data": "与 Let's Encrypt 的网络请求超时"}))

        return response

    def get_certificate(self):
        self.logger.debug("get_certificate")
        domain_dns_value = "placeholder"
        dns_names_to_delete = []
        # try:
        self.acme_register()
        authorizations, finalize_url = self.apply_for_cert_issuance()

        responders = []
        domain_txt_dns_value = []
        for url in authorizations:
            identifier_auth = self.get_identifier_authorization(url)
            authorization_url = identifier_auth["url"]
            dns_name = identifier_auth["domain"]
            dns_token = identifier_auth["dns_token"]
            dns_challenge_url = identifier_auth["dns_challenge_url"]

            acme_keyauthorization, domain_dns_value = self.get_keyauthorization(dns_token)
            _, _, acme_txt = extract_zone(dns_name)
            domain_txt_dns_value.append({"acme_txt": acme_txt,"dns_name":dns_name, "acme_txt_value": domain_dns_value})
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

        # 1
        if self.Manual == 1:

            print("请添加txt解析")
            print(domain_txt_dns_value)
            public.WriteFile(os.path.join(ssl_home_path, "domain_txt_dns_value.json"), json.dumps(domain_txt_dns_value), mode="w")
            public.WriteFile(os.path.join(ssl_home_path, "Confirmation_verification"), "", mode="w")
            num = 0
            while True:
                if os.path.isfile(os.path.join(ssl_home_path, "Confirmation_verification")):
                    Confirmation_verification = public.ReadFile(os.path.join(ssl_home_path, "Confirmation_verification"))
                    if Confirmation_verification.strip() == "ok":
                        break
                time.sleep(5)
                num += 1
                if num > 90:
                    timeout_info = json.dumps({"data": "当前txt解析记录已经过期，请重新获取", "status": False})
                    public.WriteFile(os.path.join(ssl_home_path, "timeout_info"), timeout_info, mode="w")
                    sys.exit(timeout_info)  # 5分钟后失效
        for i in responders:
            auth_status_response = self.check_authorization_status(i["authorization_url"])
            if auth_status_response.json()["status"] == "pending":
                self.respond_to_challenge(i["acme_keyauthorization"], i["dns_challenge_url"])

        for i in responders:
            self.check_authorization_status(i["authorization_url"], ["valid"], dns_names_to_delete)
        certificate_url = self.send_csr(finalize_url)
        certificate = self.download_certificate(certificate_url)
        # except Exception as e:
        #     sys.exit("错误：无法颁发证书. error={0}".format(str(e)))
        # finally:
        #     for i in dns_names_to_delete:
        #         self.dns_class.delete_dns_record(i["dns_name"], i["domain_dns_value"])
        for i in dns_names_to_delete:
            self.dns_class.delete_dns_record(i["dns_name"], i["domain_dns_value"])
        return certificate

    def cert(self):
        return self.get_certificate()

    def renew(self):
        """  续签证书。 续订实际上是获得新证书。 https://letsencrypt.org/docs/rate-limits/  """
        return self.cert()


def extract_zone(domain_name):
    domain_name = domain_name.lstrip("*.")
    if domain_name.count(".") > 1:
        zone, middle, last = str(domain_name).rsplit(".", 2)
        root = ".".join([middle, last])
        acme_txt = "_acme-challenge.%s" % zone
    else:
        zone = ""
        root = domain_name
        acme_txt = "_acme-challenge"
    return root, zone, acme_txt


class DNSPodDns(object):
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

    def create_dns_record(self, domain_name, domain_dns_value):
        print("create_dns_record {}  {}".format(domain_name, domain_dns_value))
        # if we have been given a wildcard name, strip wildcard
        domain_name = domain_name.lstrip("*.")
        subd = ""
        if domain_name.count(".") != 1:  # not top level domain
            pos = domain_name.rfind(".", 0, domain_name.rfind("."))
            subd = domain_name[:pos]
            domain_name = domain_name[pos + 1:]
            if subd != "":
                subd = "." + subd
        if sys.version_info[0] == 2:
            url = urlparse.urljoin(self.DNSPOD_API_BASE_URL, "Record.Create")
        else:
            url = urllib.parse.urljoin(self.DNSPOD_API_BASE_URL, "Record.Create")
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
        if create_dnspod_dns_record_response["status"]["code"] != "1":
            if create_dnspod_dns_record_response["status"]["code"] == "13" or create_dnspod_dns_record_response["status"]["code"] == "7":
                sys.exit(json.dumps({"data": "这个dnspod账户下不存在这个域名，添加解析失败", "msg": create_dnspod_dns_record_response}))
            elif create_dnspod_dns_record_response["status"]["code"] == "10004" or create_dnspod_dns_record_response["status"]["code"] == "10002":
                sys.exit(json.dumps({"data": "dnspod API密钥错误，添加解析失败", "msg": create_dnspod_dns_record_response}))
            else:
                sys.exit(json.dumps({"data": create_dnspod_dns_record_response["status"]['message'], "msg": create_dnspod_dns_record_response}))
        print("create_dns_record_end")

    def delete_dns_record(self, domain_name, domain_dns_value):
        print("delete_dns_record", domain_name)
        domain_name = domain_name.lstrip("*.")
        subd = ""
        if domain_name.count(".") != 1:  # not top level domain
            pos = domain_name.rfind(".", 0, domain_name.rfind("."))
            subd = domain_name[:pos]
            domain_name = domain_name[pos + 1:]
            if subd != "":
                subd = "." + subd
        if sys.version_info[0] == 2:
            url = urlparse.urljoin(self.DNSPOD_API_BASE_URL, "Record.List")
        else:
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
            print("list_dns_record_response. status_code={0}. message={1}".format(list_dns_response["status"]["code"], list_dns_response["status"]["message"]))
            return
        for i in range(0, len(list_dns_response["records"])):
            rid = list_dns_response["records"][i]["id"]
            if sys.version_info[0] == 2:
                urlr = urlparse.urljoin(self.DNSPOD_API_BASE_URL, "Record.Remove")
            else:
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
                print("delete_dns_record_response. status_code={0}. message={1}".format(delete_dns_record_response["status"]["code"], delete_dns_record_response["status"]["message"], ))
        print("delete_dns_record_success")


class AliyunDns(object):
    def __init__(self, key, secret, ):
        self.key = str(key).strip()
        self.secret = str(secret).strip()
        self.url = "http://alidns.aliyuncs.com"

    def sign(self, accessKeySecret, parameters):  # '''签名方法
        def percent_encode(encodeStr):
            encodeStr = str(encodeStr)
            if sys.version_info[0] == 3:
                res = urllib.parse.quote(encodeStr, '')
            else:
                res = urllib2.quote(encodeStr, '')
            res = res.replace('+', '%20')
            res = res.replace('*', '%2A')
            res = res.replace('%7E', '~')
            return res

        sortedParameters = sorted(parameters.items(), key=lambda parameters: parameters[0])
        canonicalizedQueryString = ''
        for (k, v) in sortedParameters:
            canonicalizedQueryString += '&' + percent_encode(k) + '=' + percent_encode(v)
        stringToSign = 'GET&%2F&' + percent_encode(canonicalizedQueryString[1:])
        if sys.version_info[0] == 2:
            h = hmac.new(accessKeySecret + "&", stringToSign, sha1)
        else:
            h = hmac.new(bytes(accessKeySecret + "&", encoding="utf8"), stringToSign.encode('utf8'), sha1)
        signature = base64.encodestring(h.digest()).strip()
        return signature

    def create_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = extract_zone(domain_name)
        print("create_dns_record start: ", acme_txt, domain_dns_value)
        randomint = random.randint(11111111111111, 99999999999999)
        now = datetime.datetime.utcnow()
        otherStyleTime = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        paramsdata = {
            "Action": "AddDomainRecord", "Format": "json", "Version": "2015-01-09", "SignatureMethod": "HMAC-SHA1", "Timestamp": otherStyleTime,
            "SignatureVersion": "1.0", "SignatureNonce": str(randomint), "AccessKeyId": self.key,
            "DomainName": root,
            "RR": acme_txt,
            "Type": "TXT",
            "Value": domain_dns_value,
        }
        Signature = self.sign(self.secret, paramsdata)
        paramsdata['Signature'] = Signature
        req = requests.get(url=self.url, params=paramsdata)
        if req.status_code != 200:
            if req.json()['Code'] == 'IncorrectDomainUser' or req.json()['Code'] == 'InvalidDomainName.NoExist':
                sys.exit(json.dumps({"data": "这个阿里云账户下面不存在这个域名，添加解析失败", "msg": req.json()}))
            elif req.json()['Code'] == 'InvalidAccessKeyId.NotFound' or req.json()['Code'] == 'SignatureDoesNotMatch':
                sys.exit(json.dumps({"data": "API密钥错误，添加解析失败", "msg": req.json()}))
            else:
                sys.exit(json.dumps({"data": req.json()['Message'], "msg": req.json()}))
        print("create_dns_record end")

    def query_recored_items(self, host, zone=None, tipe=None, page=1, psize=200):
        randomint = random.randint(11111111111111, 99999999999999)
        now = datetime.datetime.utcnow()
        otherStyleTime = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        paramsdata = {
            "Action": "DescribeDomainRecords", "Format": "json", "Version": "2015-01-09", "SignatureMethod": "HMAC-SHA1", "Timestamp": otherStyleTime,
            "SignatureVersion": "1.0", "SignatureNonce": str(randomint), "AccessKeyId": self.key,
            "DomainName": host,
        }
        if zone:
            paramsdata['RRKeyWord'] = zone
        if tipe:
            paramsdata['TypeKeyWord'] = tipe
        Signature = self.sign(self.secret, paramsdata)
        paramsdata['Signature'] = Signature
        req = requests.get(url=self.url, params=paramsdata)
        return req.json()

    def query_recored_id(self, root, zone, tipe="TXT"):
        record_id = None
        recoreds = self.query_recored_items(root, zone, tipe=tipe)
        recored_list = recoreds.get("DomainRecords", {}).get("Record", [])
        recored_item_list = [i for i in recored_list if i["RR"] == zone]
        if len(recored_item_list):
            record_id = recored_item_list[0]["RecordId"]
        return record_id

    def delete_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = extract_zone(domain_name)
        print("delete_dns_record start: ", acme_txt, domain_dns_value)
        record_id = self.query_recored_id(root, acme_txt)
        if not record_id:
            msg = "找不到域名的record_id: ", domain_name
            print(msg)
            return
        print("start to delete dns record, id: ", record_id)
        randomint = random.randint(11111111111111, 99999999999999)
        now = datetime.datetime.utcnow()
        otherStyleTime = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        paramsdata = {
            "Action": "DeleteDomainRecord", "Format": "json", "Version": "2015-01-09", "SignatureMethod": "HMAC-SHA1", "Timestamp": otherStyleTime,
            "SignatureVersion": "1.0", "SignatureNonce": str(randomint), "AccessKeyId": self.key,
            "RecordId": record_id,
        }
        Signature = self.sign(self.secret, paramsdata)
        paramsdata['Signature'] = Signature
        req = requests.get(url=self.url, params=paramsdata)
        if req.status_code != 200:
            sys.exit(json.dumps({"data": "删除解析记录失败", "msg": req.json()}))
        print("delete_dns_record end: ", acme_txt)


class CloudxnsDns(object):
    def __init__(self, key, secret, ):
        self.key = key
        self.secret = secret
        self.APIREQUESTDATE = time.ctime()

    def get_headers(self, url, parameter=''):
        APIREQUESTDATE = self.APIREQUESTDATE
        APIHMAC = public.Md5(self.key + url + parameter + APIREQUESTDATE + self.secret)
        headers = {
            "API-KEY": self.key,
            "API-REQUEST-DATE": APIREQUESTDATE,
            "API-HMAC": APIHMAC,
            "API-FORMAT": "json"
        }
        return headers

    def get_domain_list(self):
        url = "https://www.cloudxns.net/api2/domain"
        headers = self.get_headers(url)
        req = requests.get(url=url, headers=headers)
        req = req.json()
        if req['code'] != 1:
            sys.exit(json.dumps({"data": "密钥错误，添加解析失败", "status": False, "msg": req}))
        return req

    def get_domain_id(self, domain_name):
        req = self.get_domain_list()
        for i in req["data"]:
            if domain_name.strip() == i['domain'][:-1]:
                return i['id']
            # print (i['domain'][:-1], "======", domain_name.strip())
        sys.exit(json.dumps({"data": "域名不存在这个cloudxns用户下面，添加解析失败", "status": False, "msg": req}))

    def create_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = extract_zone(domain_name)
        print("create_dns_record,", acme_txt, domain_dns_value)
        url = "https://www.cloudxns.net/api2/record"
        data = {
            "domain_id": int(self.get_domain_id(root)),
            "host": acme_txt,
            "value": domain_dns_value,
            "type": "TXT",
            "line_id": 1,
        }
        parameter = json.dumps(data)
        headers = self.get_headers(url, parameter)
        req = requests.post(url=url, headers=headers, data=parameter)
        req = req.json()
        if req['code'] != 1:
            sys.exit(json.dumps({"data": "密钥错误，添加解析失败", "status": False, "msg": req}))

        print("create_dns_record_end")

    def delete_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = extract_zone(domain_name)
        print("delete_dns_record start: ", acme_txt, domain_dns_value)
        url = "https://www.cloudxns.net/api2/record/{}/{}".format(self.get_record_id(root), self.get_domain_id(root))
        headers = self.get_headers(url, )
        req = requests.delete(url=url, headers=headers, )
        req = req.json()
        print("delete_dns_record_success")

    def get_record_id(self, domain_name):
        url = "http://www.cloudxns.net/api2/record/{}?host_id=0&offset=0&row_num=2000".format(self.get_domain_id(domain_name))
        headers = self.get_headers(url, )
        req = requests.get(url=url, headers=headers, )
        req = req.json()
        for i in req['data']:
            if i['type'] == "TXT":
                return i['record_id']


class Dns_com(object):

    def create_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = extract_zone(domain_name)
        print("create_dns_record,", acme_txt, domain_dns_value)
        result = public.ExecShell('''{} /www/server/panel/plugin/dns/dns_main.py add_txt {} {}'''.format(public.get_python_bin(),acme_txt + '.' + root, domain_dns_value))
        if result[0].strip() == "False":
            sys.exit(json.dumps({"data": "当前绑定的宝塔DNS云解析账户里面不存在这个域名,添加解析失败!"}))
        print("create_dns_record_end")

    def delete_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = extract_zone(domain_name)
        print("delete_dns_record start: ", acme_txt, domain_dns_value)
        public.ExecShell('''{} /www/server/panel/plugin/dns/dns_main.py remove_txt {} {}'''.format(public.get_python_bin() ,acme_txt + '.' + root, domain_dns_value))
        print("delete_dns_record_success")


class Dns_Manual(object):
    def create_dns_record(self, domain_name, domain_dns_value):
        pass

    def delete_dns_record(self, domain_name, domain_dns_value):
        pass


if __name__ == "__main__":#dns调用验证脚本
    if len(sys.argv) == 1:
        print ('''dnspod使用方法: python  xxxx.py  '{"dnsapi":"dns_dp","key":"ID","secret":"Token","domain_alt_names":"a.com,b.com","contact_email":"290070744@qq.com","dnssleep":10,"path":"/xxx/xxx"}' ''')
        print ('''阿里dns使用方法: python xxxx.py  '{"dnsapi":"dns_ali","key":"AccessKey","secret":"SecretKey","domain_alt_names":"a.com,b.com","contact_email":"290070744@qq.com","dnssleep":10,"path":"/xxx/xxx"}' ''')
        sys.exit(json.dumps({"data": "给脚本传的参数格式错误"}))
    print(sys.argv[1])
    data = json.loads(sys.argv[1])
    # data = {"domain_alt_names": "a1.jiangwenhui.xyz", "dnssleep": "10", "dnsapi": "dns_dp", "secret": "xxxxxxxxxx", "contact_email": "", "key": "xxxxx","path":"/xxx/xxx"}
    Manual = 0
    dnsapi = data['dnsapi']
    key = data['key']
    secret = data['secret']
    if dnsapi == "dns_dp":  # 腾讯DnsPod
        dns_class = DNSPodDns(DNSPOD_ID=key, DNSPOD_API_KEY=secret)
    elif dnsapi == "dns_ali":  # 阿里云DNS
        dns_class = AliyunDns(key=key, secret=secret)
    elif dnsapi == "dns_cx":  # CloudXns
        dns_class = CloudxnsDns(key=key, secret=secret)
    elif dnsapi == "dns_bt":  # dns.com
        dns_class = Dns_com()
    elif dnsapi == "dns":  # 手动的
        dns_class = Dns_Manual()
        Manual = 1
    domain_alt_names = data['domain_alt_names'].split(",")
    ACME_AUTH_STATUS_WAIT_PERIOD = int(data['dnssleep'])  # 等待时间/秒
    contact_email = data['contact_email']
    sitename = data['path'].split("/")[-1]

    ssl_home_path = os.path.join("/www/server/panel/vhost/cert/", sitename)
    public.ExecShell("mkdir -p {}".format(ssl_home_path))
    if os.path.isfile(os.path.join(ssl_home_path, "account_key.key")):  # 如果存在account_key就是续签
        with open(os.path.join(ssl_home_path, "account_key.key"), 'r') as account_key_file:
            account_key = account_key_file.read()
    else:
        account_key = None
    client = ACMEclient(
        account_key=account_key,
        Manual=Manual,  # 手动验证 0 非手动 ,1 获取手动要添加的txt记录值
        contact_email=contact_email,
        dns_class=dns_class,
        domain_alt_names=domain_alt_names,
        ACME_AUTH_STATUS_WAIT_PERIOD=ACME_AUTH_STATUS_WAIT_PERIOD,  # 验证域名解析授权状态的等待时间/秒
        ACME_AUTH_STATUS_MAX_CHECKS=2,  # 检查授权状态的最大次数
        # ACME_DIRECTORY_URL="https://acme-staging-v02.api.letsencrypt.org/directory",  # 测试api地址 https://acme-staging-v02.api.letsencrypt.org/directory
        ACME_DIRECTORY_URL="https://acme-v02.api.letsencrypt.org/directory",  #    正式ali地址 https://acme-v02.api.letsencrypt.org/directory
        ACME_REQUEST_TIMEOUT=30,  # ACME请求超时/s
    )

    certificate = client.cert()
    certificate_key = client.certificate_key
    account_key = client.account_key

    print("证书certificate:{}".format(certificate))
    print("证书certificate_key:{}".format(certificate_key))
    print("your letsencrypt.org account key is:{}".format(account_key))

    home_key = os.path.join(ssl_home_path, "privkey.pem")
    home_csr = os.path.join(ssl_home_path, "fullchain.pem")
    with open(home_csr, 'w') as certificate_file:
        certificate_file.write(certificate)
    with open(home_key, 'w') as certificate_key_file:
        certificate_key_file.write(certificate_key)
    if not os.path.isfile(os.path.join(ssl_home_path, "account_key.key")):
        with open(os.path.join(ssl_home_path, "account_key.key"), 'w') as account_key_file:
            account_key_file.write(account_key)

    key_install_path = data['path']
    ssl_certificate = os.path.join(key_install_path, "fullchain.pem")
    ssl_certificate_key = os.path.join(key_install_path, "privkey.pem")
    key_install_path = key_install_path.replace("*.", '')
    ssl_certificate = ssl_certificate.replace("*.", '')
    ssl_certificate_key = ssl_certificate_key.replace("*.", '')
    public.ExecShell("mkdir -p {}".format(key_install_path))
    public.ExecShell('''/bin/cp  {} {}'''.format(home_csr, ssl_certificate))
    public.ExecShell('''/bin/cp  {} {}'''.format(home_key, ssl_certificate_key))
    print("ssl_success")
    # 重载Web服务配置
    if os.path.exists('/www/server/nginx/sbin/nginx'):
        result = public.ExecShell('/etc/init.d/nginx reload')
        if result[1].find('nginx.pid') != -1:
            public.ExecShell('pkill -9 nginx && sleep 1');
            public.ExecShell('/etc/init.d/nginx start');
    else:
        result = public.ExecShell('/etc/init.d/httpd reload')
