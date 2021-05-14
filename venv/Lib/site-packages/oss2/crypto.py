# -*- coding: utf-8 -*-

"""
oss2.encryption
~~~~~~~~~~~~~~

该模块包含了客户端加解密相关的函数和类。
"""
import json
from functools import partial

from oss2.utils import b64decode_from_string, b64encode_as_string
from . import utils
from .compat import to_string, to_bytes, to_unicode
from .exceptions import OssError, ClientError, OpenApiFormatError, OpenApiServerError

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from requests.structures import CaseInsensitiveDict

from aliyunsdkcore import client
from aliyunsdkcore.acs_exception.exceptions import ServerException, ClientException
from aliyunsdkcore.http import protocol_type, format_type, method_type
from aliyunsdkkms.request.v20160120 import ListKeysRequest, GenerateDataKeyRequest, DecryptRequest, EncryptRequest

import os


class BaseCryptoProvider(object):
    """CryptoProvider 基类，提供基础的数据加密解密adapter

    """
    def __init__(self, cipher):
        self.plain_key = None
        self.plain_start = None
        self.cipher = cipher

    def make_encrypt_adapter(self, stream, key, start):
        return utils.make_cipher_adapter(stream, partial(self.cipher.encrypt, self.cipher(key, start)))

    def make_decrypt_adapter(self, stream, key, start):
        return utils.make_cipher_adapter(stream, partial(self.cipher.decrypt, self.cipher(key, start)))


_LOCAL_RSA_TMP_DIR = '.oss-local-rsa'


class LocalRsaProvider(BaseCryptoProvider):
    """使用本地RSA加密数据密钥。

        :param str dir: 本地RSA公钥私钥存储路径
        :param str key: 本地RSA公钥私钥名称前缀
        :param str passphrase: 本地RSA公钥私钥密码
        :param class cipher: 数据加密，默认aes256，用户可自行实现对称加密算法，需符合AESCipher注释规则
    """

    PUB_KEY_FILE = '.public_key.pem'
    PRIV_KEY_FILE = '.private_key.pem'

    def __init__(self, dir=None, key='', passphrase=None, cipher=utils.AESCipher):
        super(LocalRsaProvider, self).__init__(cipher=cipher)
        self.dir = dir or os.path.join(os.path.expanduser('~'), _LOCAL_RSA_TMP_DIR)

        utils.makedir_p(self.dir)

        priv_key_full_path = os.path.join(self.dir, key + self.PRIV_KEY_FILE)
        pub_key_full_path = os.path.join(self.dir, key + self.PUB_KEY_FILE)
        try:
            if os.path.exists(priv_key_full_path) and os.path.exists(pub_key_full_path):
                with open(priv_key_full_path, 'rb') as f:
                    self.__decrypt_obj = PKCS1_OAEP.new(RSA.importKey(f.read(), passphrase=passphrase))

                with open(pub_key_full_path, 'rb') as f:
                    self.__encrypt_obj = PKCS1_OAEP.new(RSA.importKey(f.read(), passphrase=passphrase))

            else:
                private_key = RSA.generate(2048)
                public_key = private_key.publickey()

                self.__encrypt_obj = PKCS1_OAEP.new(public_key)
                self.__decrypt_obj = PKCS1_OAEP.new(private_key)

                with open(priv_key_full_path, 'wb') as f:
                    f.write(private_key.exportKey(passphrase=passphrase))

                with open(pub_key_full_path, 'wb') as f:
                    f.write(public_key.exportKey(passphrase=passphrase))
        except (ValueError, TypeError, IndexError) as e:
            raise ClientError(str(e))

    def build_header(self, headers=None):
        if not isinstance(headers, CaseInsensitiveDict):
            headers = CaseInsensitiveDict(headers)

        if 'content-md5' in headers:
            headers['x-oss-meta-unencrypted-content-md5'] = headers['content-md5']
            del headers['content-md5']

        if 'content-length' in headers:
            headers['x-oss-meta-unencrypted-content-length'] = headers['content-length']
            del headers['content-length']

        headers['x-oss-meta-oss-crypto-key'] = b64encode_as_string(self.__encrypt_obj.encrypt(self.plain_key))
        headers['x-oss-meta-oss-crypto-start'] = b64encode_as_string(self.__encrypt_obj.encrypt(to_bytes(str(self.plain_start))))
        headers['x-oss-meta-oss-cek-alg'] = self.cipher.ALGORITHM
        headers['x-oss-meta-oss-wrap-alg'] = 'rsa'

        self.plain_key = None
        self.plain_start = None

        return headers

    def get_key(self):
        self.plain_key = self.cipher.get_key()
        return self.plain_key

    def get_start(self):
        self.plain_start = self.cipher.get_start()
        return self.plain_start

    def decrypt_oss_meta_data(self, headers, key, conv=lambda x:x):
        try:
            return conv(self.__decrypt_obj.decrypt(utils.b64decode_from_string(headers[key])))
        except:
            return None


class AliKMSProvider(BaseCryptoProvider):
    """使用aliyun kms服务加密数据密钥。kms的详细说明参见
        https://help.aliyun.com/product/28933.html?spm=a2c4g.11186623.3.1.jlYT4v
        此接口在py3.3下暂时不可用，详见
        https://github.com/aliyun/aliyun-openapi-python-sdk/issues/61

        :param str access_key_id: 可以访问kms密钥服务的access_key_id
        :param str access_key_secret: 可以访问kms密钥服务的access_key_secret
        :param str region: kms密钥服务地区
        :param str cmkey: 用户主密钥
        :param str sts_token: security token，如果使用的是临时AK需提供
        :param str passphrase: kms密钥服务密码
        :param class cipher: 数据加密，默认aes256，当前仅支持默认实现
    """
    def __init__(self, access_key_id, access_key_secret, region, cmkey, sts_token = None, passphrase=None, cipher=utils.AESCipher):

        if not issubclass(cipher, utils.AESCipher):
            raise ClientError('AliKMSProvider only support AES256 cipher')

        super(AliKMSProvider, self).__init__(cipher=cipher)
        self.cmkey = cmkey
        self.sts_token = sts_token
        self.context = '{"x-passphrase":"' + passphrase + '"}' if passphrase else ''
        self.clt = client.AcsClient(access_key_id, access_key_secret, region)

        self.encrypted_key = None

    def build_header(self, headers=None):
        if not isinstance(headers, CaseInsensitiveDict):
            headers = CaseInsensitiveDict(headers)
        if 'content-md5' in headers:
            headers['x-oss-meta-unencrypted-content-md5'] = headers['content-md5']
            del headers['content-md5']

        if 'content-length' in headers:
            headers['x-oss-meta-unencrypted-content-length'] = headers['content-length']
            del headers['content-length']

        headers['x-oss-meta-oss-crypto-key'] = self.encrypted_key
        headers['x-oss-meta-oss-crypto-start'] = self.__encrypt_data(to_bytes(str(self.plain_start)))
        headers['x-oss-meta-oss-cek-alg'] = self.cipher.ALGORITHM
        headers['x-oss-meta-oss-wrap-alg'] = 'kms'

        self.encrypted_key = None
        self.plain_start = None

        return headers

    def get_key(self):
        plain_key, self.encrypted_key = self.__generate_data_key()
        return plain_key

    def get_start(self):
        self.plain_start = utils.random_counter()
        return self.plain_start

    def __generate_data_key(self):
        req = GenerateDataKeyRequest.GenerateDataKeyRequest()

        req.set_accept_format(format_type.JSON)
        req.set_method(method_type.POST)

        req.set_KeyId(self.cmkey)
        req.set_KeySpec('AES_256')
        req.set_NumberOfBytes(32)
        req.set_EncryptionContext(self.context)
        if self.sts_token:
            req.set_STSToken(self.sts_token)

        resp = self.__do(req)

        return b64decode_from_string(resp['Plaintext']), resp['CiphertextBlob']

    def __encrypt_data(self, data):
        req = EncryptRequest.EncryptRequest()

        req.set_accept_format(format_type.JSON)
        req.set_method(method_type.POST)
        req.set_KeyId(self.cmkey)
        req.set_Plaintext(data)
        req.set_EncryptionContext(self.context)
        if self.sts_token:
            req.set_STSToken(self.sts_token)

        resp = self.__do(req)

        return resp['CiphertextBlob']

    def __decrypt_data(self, data):
        req = DecryptRequest.DecryptRequest()

        req.set_accept_format(format_type.JSON)
        req.set_method(method_type.POST)
        req.set_CiphertextBlob(data)
        req.set_EncryptionContext(self.context)
        if self.sts_token:
            req.set_STSToken(self.sts_token)

        resp = self.__do(req)
        return resp['Plaintext']

    def __do(self, req):

        try:
            body = self.clt.do_action_with_exception(req)

            return json.loads(to_unicode(body))
        except ServerException as e:
            raise OpenApiServerError(e.http_status, e.request_id, e.message, e.error_code)
        except ClientException as e:
            raise ClientError(e.message)
        except (ValueError, TypeError) as e:
            raise OpenApiFormatError('Json Error: ' + str(e))

    def decrypt_oss_meta_data(self, headers, key, conv=lambda x: x):
        try:
            if key.lower() == 'x-oss-meta-oss-crypto-key'.lower():
                return conv(b64decode_from_string(self.__decrypt_data(headers[key])))
            else:
                return conv(self.__decrypt_data(headers[key]))
        except OssError as e:
            raise e
        except:
            return None