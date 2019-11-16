#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: 黄文良 <287962566@qq.com>
#-------------------------------------------------------------------

#-------------------------------------------------------------------
# ACME v2客户端
#-------------------------------------------------------------------
import os
import time
import copy
import json
import base64
import hashlib
import logging
import binascii
import platform
import sys
import requests
import OpenSSL
import cryptography

os.chdir('/www/server/panel')
sys.path.append('class/')
import public

class acme_v2:
    _url = None
    _apis = None
    debug = True
    def __init__(
        self,
        domain_name = "www.bt.cn",
        dns_class = None,
        domain_alt_names=None,
        contact_email=None,
        account_key=None,
        certificate_key=None,
        bits=2048,
        digest="sha256",
        ACME_REQUEST_TIMEOUT=7,
        ACME_AUTH_STATUS_WAIT_PERIOD=8,
        ACME_AUTH_STATUS_MAX_CHECKS=3
        ):
        if self.debug:
            self._url = 'https://acme-staging-v02.api.letsencrypt.org/directory'
        else:
            self._url = 'https://acme-v02.api.letsencrypt.org/directory'

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
        self.ACME_DIRECTORY_URL = self._url

        self.all_domain_names = copy.copy(self.domain_alt_names)
        self.all_domain_names.insert(0, self.domain_name)
        self.domain_alt_names = list(set(self.domain_alt_names))
        self.User_Agent = self.get_user_agent()
        
        
            

        acme_endpoints = self.get_apis()
        self.ACME_GET_NONCE_URL = acme_endpoints["newNonce"]
        self.ACME_TOS_URL = acme_endpoints["meta"]["termsOfService"]
        self.ACME_CAA_ID = acme_endpoints["meta"]["caaIdentities"]
        self.ACME_KEY_CHANGE_URL = acme_endpoints["keyChange"]
        self.ACME_NEW_ACCOUNT_URL = acme_endpoints["newAccount"]
        self.ACME_NEW_ORDER_URL = acme_endpoints["newOrder"]
        self.ACME_REVOKE_CERT_URL = acme_endpoints["revokeCert"]


        self.kid = None

        self.certificate_key = certificate_key or self.create_certificate_key()
        self.csr = self.create_csr()

        if not account_key:
            self.account_key = self.create_account_key()
            self.PRIOR_REGISTERED = False
        else:
            self.account_key = account_key
            self.PRIOR_REGISTERED = True

    #获取API接口清单
    def get_apis(self):
        if self._apis: return self._apis
        result = json.loads(self._http_get(self._url).read())
        if result: 
            self._apis = result
            return self._apis
        return False

    #创建CSR
    def create_csr(self):
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

    def get_user_agent(self):
        return "BT-Panel/7.0"

    def create_certificate_key(self):
        return self.create_key().decode()

    def create_account_key(self):
        return self.create_key().decode()

    #创建Key
    def create_key(self, key_type=OpenSSL.crypto.TYPE_RSA):
        key = OpenSSL.crypto.PKey()
        key.generate_key(key_type, self.bits)
        private_key = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key)
        return private_key

    #注册帐户
    def register(self):
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
        print(url)
        acme_register_response = self.make_signed_acme_request(url=url, payload=payload)
        print(acme_register_response)

        if acme_register_response.code not in [201, 200, 409]:
            raise ValueError(
                "Error while registering: status_code={status_code} response={response}".format(
                    status_code=acme_register_response.status_code,
                    response=self.log_response(acme_register_response),
                )
            )

        kid = acme_register_response.info().getheaders("Location")
        setattr(self, "kid", kid)
        print(acme_register_response.read())
        print(acme_register_response.info().headers)
        return acme_register_response

    def log_response(self,response):
        try:
            tmp = response.read()
            log_body = json.loads(tmp)
        except ValueError:
            log_body = tmp[:30]
        return log_body

    def make_signed_acme_request(self, url, payload):
        headers = {"User-Agent": self.User_Agent}
        payload = self.stringfy_items(payload)
        if payload in ["GET_Z_CHALLENGE", "DOWNLOAD_Z_CERTIFICATE"]:
            response = self._http_get(url, headers)
        else:
            payload64 = self.calculate_safe_base64(json.dumps(payload))
            protected = self.get_acme_header(url)
            protected64 = self.calculate_safe_base64(json.dumps(protected))
            signature = self.sign_message(message="{0}.{1}".format(protected64, payload64))
            signature64 = self.calculate_safe_base64(signature)  # str
            data = {"protected": protected64, "payload": payload64, "signature": signature64}
            
            headers.update({"Content-Type": "application/jose+json"})
            response = self._http_post(url, data, headers)
        return response

    def sign_message(self, message):
        pk = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, self.account_key.encode())
        return OpenSSL.crypto.sign(pk, message.encode("utf8"), self.digest)

    #构造请求头
    def get_acme_header(self,url):
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

    def get_nonce(self):
        headers = {"User-Agent": self.User_Agent}
        response = self._http_get(self.ACME_GET_NONCE_URL, headers=headers)
        tmp = response.info().getheaders("Replay-Nonce")
        if not tmp: return ''
        return tmp[0]


    #将参数转换为Base64
    def calculate_safe_base64(self,un_encoded_data):
        if sys.version_info[0] == 3:
            if isinstance(un_encoded_data, str):
                un_encoded_data = un_encoded_data.encode("utf8")
        r = base64.urlsafe_b64encode(un_encoded_data).rstrip(b"=")
        return r.decode("utf8")

    #参数转换
    def stringfy_items(self,payload):
        if isinstance(payload, str):
            return payload

        for k, v in payload.items():
            if isinstance(k, bytes):
                k = k.decode("utf-8")
            if isinstance(v, bytes):
                v = v.decode("utf-8")
            payload[k] = v
        return payload

    #GET请求
    def _http_get(self,url,headers = {},timeout = 30):
        if sys.version_info[0] == 2:
            try:
                import urllib2,ssl
                if sys.version_info[0] == 2:
                    reload(urllib2)
                    reload(ssl)
                try:
                    ssl._create_default_https_context = ssl._create_unverified_context
                except:pass;
                req = urllib2.Request(url, headers = headers)
                response = urllib2.urlopen(req,timeout = timeout,)
                return response
            except Exception as ex:
                print(public.get_error_info())
                return str(ex);
        else:
            try:
                import urllib.request,ssl
                try:
                    ssl._create_default_https_context = ssl._create_unverified_context
                except:pass;
                req = urllib.request.Request(url,headers = headers)
                response = urllib.request.urlopen(req,timeout = timeout)
                return response
            except Exception as ex:
                print(public.get_error_info())
                return str(ex)

    #POST请求
    def _http_post(self,url,data,headers = {},timeout = 30):
        data = json.dumps(data).encode('utf8')
        if sys.version_info[0] == 2:
            try:
                import urllib,urllib2,ssl
                try:
                    ssl._create_default_https_context = ssl._create_unverified_context
                except:pass
                req = urllib2.Request(url, data,headers = headers)
                response = urllib2.urlopen(req,timeout=timeout)
                return response
            except Exception as ex:
                print(public.get_error_info())
                return str(ex);
        else:
            try:
                import urllib.request,ssl
                try:
                    ssl._create_default_https_context = ssl._create_unverified_context
                except:pass;
                req = urllib.request.Request(url, data,headers = headers)
                response = urllib.request.urlopen(req,timeout = timeout)
                return response
            except Exception as ex:
                print(public.get_error_info())
                return str(ex);






if __name__ == "__main__":
    p = acme_v2()
    p.register()

