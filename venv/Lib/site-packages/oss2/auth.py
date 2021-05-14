# -*- coding: utf-8 -*-

import hmac
import hashlib
import time

from . import utils
from .compat import urlquote, to_bytes, is_py2
from .headers import *
import logging

AUTH_VERSION_1 = 'v1'
AUTH_VERSION_2 = 'v2'

logger = logging.getLogger(__name__)


def make_auth(access_key_id, access_key_secret, auth_version=AUTH_VERSION_1):
    if auth_version == AUTH_VERSION_2:
        logger.debug("Init Auth V2: access_key_id: {0}, access_key_secret: ******".format(access_key_id))
        return AuthV2(access_key_id.strip(), access_key_secret.strip())
    else:
        logger.debug("Init Auth v1: access_key_id: {0}, access_key_secret: ******".format(access_key_id))
        return Auth(access_key_id.strip(), access_key_secret.strip())


class AuthBase(object):
    """用于保存用户AccessKeyId、AccessKeySecret，以及计算签名的对象。"""
    def __init__(self, access_key_id, access_key_secret):
        self.id = access_key_id.strip()
        self.secret = access_key_secret.strip()

    def _sign_rtmp_url(self, url, bucket_name, channel_name, expires, params):
        expiration_time = int(time.time()) + expires

        canonicalized_resource = "/%s/%s" % (bucket_name, channel_name)
        canonicalized_params = []

        if params:
            items = params.items()
            for k, v in items:
                if k != "OSSAccessKeyId" and k != "Signature" and k != "Expires" and k != "SecurityToken":
                    canonicalized_params.append((k, v))

        canonicalized_params.sort(key=lambda e: e[0])
        canon_params_str = ''
        for k, v in canonicalized_params:
            canon_params_str += '%s:%s\n' % (k, v)

        p = params if params else {}
        string_to_sign = str(expiration_time) + "\n" + canon_params_str + canonicalized_resource
        logger.debug('Sign Rtmp url: string to be signed = {0}'.format(string_to_sign))


        h = hmac.new(to_bytes(self.secret), to_bytes(string_to_sign), hashlib.sha1)
        signature = utils.b64encode_as_string(h.digest())

        p['OSSAccessKeyId'] = self.id
        p['Expires'] = str(expiration_time)
        p['Signature'] = signature

        return url + '?' + '&'.join(_param_to_quoted_query(k, v) for k, v in p.items())


class Auth(AuthBase):
    """签名版本1"""
    _subresource_key_set = frozenset(
        ['response-content-type', 'response-content-language',
         'response-cache-control', 'logging', 'response-content-encoding',
         'acl', 'uploadId', 'uploads', 'partNumber', 'group', 'link',
         'delete', 'website', 'location', 'objectInfo', 'objectMeta',
         'response-expires', 'response-content-disposition', 'cors', 'lifecycle',
         'restore', 'qos', 'referer', 'stat', 'bucketInfo', 'append', 'position', 'security-token',
         'live', 'comp', 'status', 'vod', 'startTime', 'endTime', 'x-oss-process',
         'symlink', 'callback', 'callback-var', 'tagging', 'encryption', 'versions',
         'versioning', 'versionId', 'policy', 'requestPayment', 'x-oss-traffic-limit', 'qosInfo', 'asyncFetch',
         'x-oss-request-payer', 'sequential']
    )

    def _sign_request(self, req, bucket_name, key):
        req.headers['date'] = utils.http_date()

        signature = self.__make_signature(req, bucket_name, key)
        req.headers['authorization'] = "OSS {0}:{1}".format(self.id, signature)

    def _sign_url(self, req, bucket_name, key, expires):
        expiration_time = int(time.time()) + expires

        req.headers['date'] = str(expiration_time)
        signature = self.__make_signature(req, bucket_name, key)

        req.params['OSSAccessKeyId'] = self.id
        req.params['Expires'] = str(expiration_time)
        req.params['Signature'] = signature

        return req.url + '?' + '&'.join(_param_to_quoted_query(k, v) for k, v in req.params.items())

    def __make_signature(self, req, bucket_name, key):
        if is_py2:
            string_to_sign = self.__get_string_to_sign(req, bucket_name, key)
        else:
            string_to_sign = self.__get_bytes_to_sign(req, bucket_name, key)

        logger.debug('Make signature: string to be signed = {0}'.format(string_to_sign))

        h = hmac.new(to_bytes(self.secret), to_bytes(string_to_sign), hashlib.sha1)
        return utils.b64encode_as_string(h.digest())

    def __get_string_to_sign(self, req, bucket_name, key):
        resource_string = self.__get_resource_string(req, bucket_name, key)
        headers_string = self.__get_headers_string(req)

        content_md5 = req.headers.get('content-md5', '')
        content_type = req.headers.get('content-type', '')
        date = req.headers.get('date', '')
        return '\n'.join([req.method,
                          content_md5,
                          content_type,
                          date,
                          headers_string + resource_string])

    def __get_headers_string(self, req):
        headers = req.headers
        canon_headers = []
        for k, v in headers.items():
            lower_key = k.lower()
            if lower_key.startswith('x-oss-'):
                canon_headers.append((lower_key, v))

        canon_headers.sort(key=lambda x: x[0])

        if canon_headers:
            return '\n'.join(k + ':' + v for k, v in canon_headers) + '\n'
        else:
            return ''

    def __get_resource_string(self, req, bucket_name, key):
        if not bucket_name:
            return '/' + self.__get_subresource_string(req.params)
        else:
            return '/{0}/{1}{2}'.format(bucket_name, key, self.__get_subresource_string(req.params))

    def __get_subresource_string(self, params):
        if not params:
            return ''

        subresource_params = []
        for key, value in params.items():
            if key in self._subresource_key_set:
                subresource_params.append((key, value))

        subresource_params.sort(key=lambda e: e[0])

        if subresource_params:
            return '?' + '&'.join(self.__param_to_query(k, v) for k, v in subresource_params)
        else:
            return ''

    def __param_to_query(self, k, v):
        if v:
            return k + '=' + v
        else:
            return k

    def __get_bytes_to_sign(self, req, bucket_name, key):
        resource_bytes = self.__get_resource_string(req, bucket_name, key).encode('utf-8')
        headers_bytes = self.__get_headers_bytes(req)

        content_md5 = req.headers.get('content-md5', '').encode('utf-8')
        content_type = req.headers.get('content-type', '').encode('utf-8')
        date = req.headers.get('date', '').encode('utf-8')
        return b'\n'.join([req.method.encode('utf-8'),
                          content_md5,
                          content_type,
                          date,
                          headers_bytes + resource_bytes])

    def __get_headers_bytes(self, req):
        headers = req.headers
        canon_headers = []
        for k, v in headers.items():
            lower_key = k.lower()
            if lower_key.startswith('x-oss-'):
                canon_headers.append((lower_key, v))

        canon_headers.sort(key=lambda x: x[0])

        if canon_headers:
            return b'\n'.join(to_bytes(k) + b':' + to_bytes(v) for k, v in canon_headers) + b'\n'
        else:
            return b''

class AnonymousAuth(object):
    """用于匿名访问。

    .. note::
        匿名用户只能读取public-read的Bucket，或只能读取、写入public-read-write的Bucket。
        不能进行Service、Bucket相关的操作，也不能罗列文件等。
    """
    def _sign_request(self, req, bucket_name, key):
        pass

    def _sign_url(self, req, bucket_name, key, expires):
        return req.url + '?' + '&'.join(_param_to_quoted_query(k, v) for k, v in req.params.items())
    
    def _sign_rtmp_url(self, url, bucket_name, channel_name, expires, params):
        return url + '?' + '&'.join(_param_to_quoted_query(k, v) for k, v in params.items())


class StsAuth(object):
    """用于STS临时凭证访问。可以通过官方STS客户端获得临时密钥（AccessKeyId、AccessKeySecret）以及临时安全令牌（SecurityToken）。

    注意到临时凭证会在一段时间后过期，在此之前需要重新获取临时凭证，并更新 :class:`Bucket <oss2.Bucket>` 的 `auth` 成员变量为新
    的 `StsAuth` 实例。

    :param str access_key_id: 临时AccessKeyId
    :param str access_key_secret: 临时AccessKeySecret
    :param str security_token: 临时安全令牌(SecurityToken)
    :param str auth_version: 需要生成auth的版本，默认为AUTH_VERSION_1(v1)
    """
    def __init__(self, access_key_id, access_key_secret, security_token, auth_version=AUTH_VERSION_1):
        logger.debug("Init StsAuth: access_key_id: {0}, access_key_secret: ******, security_token: ******".format(access_key_id))
        self.__auth = make_auth(access_key_id, access_key_secret, auth_version)
        self.__security_token = security_token

    def _sign_request(self, req, bucket_name, key):
        req.headers[OSS_SECURITY_TOKEN] = self.__security_token
        self.__auth._sign_request(req, bucket_name, key)

    def _sign_url(self, req, bucket_name, key, expires):
        req.params['security-token'] = self.__security_token
        return self.__auth._sign_url(req, bucket_name, key, expires)

    def _sign_rtmp_url(self, url, bucket_name, channel_name, expires, params):
        params['security-token'] = self.__security_token
        return self.__auth._sign_rtmp_url(url, bucket_name, channel_name, expires, params)


def _param_to_quoted_query(k, v):
    if v:
        return urlquote(k, '') + '=' + urlquote(v, '')
    else:
        return urlquote(k, '')


def v2_uri_encode(raw_text):
    raw_text = to_bytes(raw_text)

    res = ''
    for b in raw_text:
        if isinstance(b, int):
            c = chr(b)
        else:
            c = b

        if (c >= 'A' and c <= 'Z') or (c >= 'a' and c <= 'z')\
            or (c >= '0' and c <= '9') or c in ['_', '-', '~', '.']:
            res += c
        else:
            res += "%{0:02X}".format(ord(c))

    return res


_DEFAULT_ADDITIONAL_HEADERS = set(['range',
                                   'if-modified-since'])


class AuthV2(AuthBase):
    """签名版本2，与版本1的区别在：
    1. 使用SHA256算法，具有更高的安全性
    2. 参数计算包含所有的HTTP查询参数
    """
    def _sign_request(self, req, bucket_name, key, in_additional_headers=None):
        """把authorization放入req的header里面

        :param req: authorization信息将会加入到这个请求的header里面
        :type req: oss2.http.Request

        :param bucket_name: bucket名称
        :param key: OSS文件名
        :param in_additional_headers: 加入签名计算的额外header列表
        """
        if in_additional_headers is None:
            in_additional_headers = _DEFAULT_ADDITIONAL_HEADERS

        additional_headers = self.__get_additional_headers(req, in_additional_headers)

        req.headers['date'] = utils.http_date()

        signature = self.__make_signature(req, bucket_name, key, additional_headers)

        if additional_headers:
            req.headers['authorization'] = "OSS2 AccessKeyId:{0},AdditionalHeaders:{1},Signature:{2}"\
                .format(self.id, ';'.join(additional_headers), signature)
        else:
            req.headers['authorization'] = "OSS2 AccessKeyId:{0},Signature:{1}".format(self.id, signature)

    def _sign_url(self, req, bucket_name, key, expires, in_additional_headers=None):
        """返回一个签过名的URL

        :param req: 需要签名的请求
        :type req: oss2.http.Request

        :param bucket_name: bucket名称
        :param key: OSS文件名
        :param int expires: 返回的url将在`expires`秒后过期.
        :param in_additional_headers: 加入签名计算的额外header列表

        :return: a signed URL
        """

        if in_additional_headers is None:
            in_additional_headers = set()

        additional_headers = self.__get_additional_headers(req, in_additional_headers)

        expiration_time = int(time.time()) + expires

        req.headers['date'] = str(expiration_time)  # re-use __make_signature by setting the 'date' header

        req.params['x-oss-signature-version'] = 'OSS2'
        req.params['x-oss-expires'] = str(expiration_time)
        req.params['x-oss-access-key-id'] = self.id

        signature = self.__make_signature(req, bucket_name, key, additional_headers)

        req.params['x-oss-signature'] = signature

        return req.url + '?' + '&'.join(_param_to_quoted_query(k, v) for k, v in req.params.items())

    def __make_signature(self, req, bucket_name, key, additional_headers):
        if is_py2:
            string_to_sign = self.__get_string_to_sign(req, bucket_name, key, additional_headers)
        else:
            string_to_sign = self.__get_bytes_to_sign(req, bucket_name, key, additional_headers)

        logger.debug('Make signature: string to be signed = {0}'.format(string_to_sign))

        h = hmac.new(to_bytes(self.secret), to_bytes(string_to_sign), hashlib.sha256)
        return utils.b64encode_as_string(h.digest())

    def __get_additional_headers(self, req, in_additional_headers):
        # we add a header into additional_headers only if it is already in req's headers.

        additional_headers = set(h.lower() for h in in_additional_headers)
        keys_in_header = set(k.lower() for k in req.headers.keys())

        return additional_headers & keys_in_header

    def __get_string_to_sign(self, req, bucket_name, key, additional_header_list):
        verb = req.method
        content_md5 = req.headers.get('content-md5', '')
        content_type = req.headers.get('content-type', '')
        date = req.headers.get('date', '')

        canonicalized_oss_headers = self.__get_canonicalized_oss_headers(req, additional_header_list)
        additional_headers = ';'.join(sorted(additional_header_list))
        canonicalized_resource = self.__get_resource_string(req, bucket_name, key)

        return verb + '\n' +\
            content_md5 + '\n' +\
            content_type + '\n' +\
            date + '\n' +\
            canonicalized_oss_headers +\
            additional_headers + '\n' +\
            canonicalized_resource

    def __get_resource_string(self, req, bucket_name, key):
        if bucket_name:
            encoded_uri = v2_uri_encode('/' + bucket_name + '/' + key)
        else:
            encoded_uri = v2_uri_encode('/')

        logging.info('encoded_uri={0} key={1}'.format(encoded_uri, key))

        return encoded_uri + self.__get_canonalized_query_string(req)

    def __get_canonalized_query_string(self, req):
        encoded_params = {}
        for param, value in req.params.items():
            encoded_params[v2_uri_encode(param)] = v2_uri_encode(value)

        if not encoded_params:
            return ''

        sorted_params = sorted(encoded_params.items(), key=lambda e: e[0])
        return '?' + '&'.join(self.__param_to_query(k, v) for k, v in sorted_params)

    def __param_to_query(self, k, v):
        if v:
            return k + '=' + v
        else:
            return k

    def __get_canonicalized_oss_headers(self, req, additional_headers):
        """
        :param additional_headers: 小写的headers列表, 并且这些headers都不以'x-oss-'为前缀.
        """
        canon_headers = []

        for k, v in req.headers.items():
            lower_key = k.lower()
            if lower_key.startswith('x-oss-') or lower_key in additional_headers:
                canon_headers.append((lower_key, v))

        canon_headers.sort(key=lambda x: x[0])

        return ''.join(v[0] + ':' + v[1] + '\n' for v in canon_headers)

    def __get_bytes_to_sign(self, req, bucket_name, key, additional_header_list):
        verb = req.method.encode('utf-8')
        content_md5 = req.headers.get('content-md5', '').encode('utf-8')
        content_type = req.headers.get('content-type', '').encode('utf-8')
        date = req.headers.get('date', '').encode('utf-8')

        canonicalized_oss_headers = self.__get_canonicalized_oss_headers_bytes(req, additional_header_list)
        additional_headers = ';'.join(sorted(additional_header_list)).encode('utf-8')
        canonicalized_resource = self.__get_resource_string(req, bucket_name, key).encode('utf-8')

        return verb + b'\n' +\
            content_md5 + b'\n' +\
            content_type + b'\n' +\
            date + b'\n' +\
            canonicalized_oss_headers +\
            additional_headers + b'\n' +\
            canonicalized_resource
    
    def __get_canonicalized_oss_headers_bytes(self, req, additional_headers):
        """
        :param additional_headers: 小写的headers列表, 并且这些headers都不以'x-oss-'为前缀.
        """
        canon_headers = []

        for k, v in req.headers.items():
            lower_key = k.lower()
            if lower_key.startswith('x-oss-') or lower_key in additional_headers:
                canon_headers.append((lower_key, v))

        canon_headers.sort(key=lambda x: x[0])

        return b''.join(to_bytes(v[0]) + b':' + to_bytes(v[1]) + b'\n' for v in canon_headers)
