# -*- coding: utf-8 -*-

import hmac
import time
from hashlib import sha1

from requests.auth import AuthBase

from .compat import urlparse, json, b
from .utils import urlsafe_base64_encode

# 上传策略，参数规格详见
# https://developer.qiniu.com/kodo/manual/1206/put-policy
_policy_fields = set([
    'callbackUrl',  # 回调URL
    'callbackBody',  # 回调Body
    'callbackHost',  # 回调URL指定的Host
    'callbackBodyType',  # 回调Body的Content-Type
    'callbackFetchKey',  # 回调FetchKey模式开关

    'returnUrl',  # 上传端的303跳转URL
    'returnBody',  # 上传端简单反馈获取的Body

    'endUser',  # 回调时上传端标识
    'saveKey',  # 自定义资源名
    'insertOnly',  # 插入模式开关

    'detectMime',  # MimeType侦测开关
    'mimeLimit',  # MimeType限制
    'fsizeLimit',  # 上传文件大小限制
    'fsizeMin',  # 上传文件最少字节数

    'persistentOps',  # 持久化处理操作
    'persistentNotifyUrl',  # 持久化处理结果通知URL
    'persistentPipeline',  # 持久化处理独享队列
    'deleteAfterDays',  # 文件多少天后自动删除
    'fileType',  # 文件的存储类型，0为普通存储，1为低频存储
    'isPrefixalScope'  # 指定上传文件必须使用的前缀
])


class Auth(object):
    """七牛安全机制类

    该类主要内容是七牛上传凭证、下载凭证、管理凭证三种凭证的签名接口的实现，以及回调验证。

    Attributes:
        __access_key: 账号密钥对中的accessKey，详见 https://portal.qiniu.com/user/key
        __secret_key: 账号密钥对重的secretKey，详见 https://portal.qiniu.com/user/key
    """

    def __init__(self, access_key, secret_key):
        """初始化Auth类"""
        self.__checkKey(access_key, secret_key)
        self.__access_key = access_key
        self.__secret_key = b(secret_key)

    def get_access_key(self):
        return self.__access_key

    def __token(self, data):
        data = b(data)
        hashed = hmac.new(self.__secret_key, data, sha1)
        return urlsafe_base64_encode(hashed.digest())

    def token(self, data):
        return '{0}:{1}'.format(self.__access_key, self.__token(data))

    def token_with_data(self, data):
        data = urlsafe_base64_encode(data)
        return '{0}:{1}:{2}'.format(
            self.__access_key, self.__token(data), data)

    def token_of_request(self, url, body=None, content_type=None):
        """带请求体的签名（本质上是管理凭证的签名）

        Args:
            url:          待签名请求的url
            body:         待签名请求的body
            content_type: 待签名请求的body的Content-Type

        Returns:
            管理凭证
        """
        parsed_url = urlparse(url)
        query = parsed_url.query
        path = parsed_url.path
        data = path
        if query != '':
            data = ''.join([data, '?', query])
        data = ''.join([data, "\n"])

        if body:
            mimes = [
                'application/x-www-form-urlencoded'
            ]
            if content_type in mimes:
                data += body

        return '{0}:{1}'.format(self.__access_key, self.__token(data))

    @staticmethod
    def __checkKey(access_key, secret_key):
        if not (access_key and secret_key):
            raise ValueError('invalid key')

    def private_download_url(self, url, expires=3600):
        """生成私有资源下载链接

        Args:
            url:     私有空间资源的原始URL
            expires: 下载凭证有效期，默认为3600s

        Returns:
            私有资源的下载链接
        """
        deadline = int(time.time()) + expires
        if '?' in url:
            url += '&'
        else:
            url += '?'
        url = '{0}e={1}'.format(url, str(deadline))

        token = self.token(url)
        return '{0}&token={1}'.format(url, token)

    def upload_token(
            self,
            bucket,
            key=None,
            expires=3600,
            policy=None,
            strict_policy=True):
        """生成上传凭证

        Args:
            bucket:  上传的空间名
            key:     上传的文件名，默认为空
            expires: 上传凭证的过期时间，默认为3600s
            policy:  上传策略，默认为空

        Returns:
            上传凭证
        """
        if bucket is None or bucket == '':
            raise ValueError('invalid bucket name')

        scope = bucket
        if key is not None:
            scope = '{0}:{1}'.format(bucket, key)

        args = dict(
            scope=scope,
            deadline=int(time.time()) + expires,
        )

        if policy is not None:
            self.__copy_policy(policy, args, strict_policy)

        return self.__upload_token(args)

    def __upload_token(self, policy):
        data = json.dumps(policy, separators=(',', ':'))
        return self.token_with_data(data)

    def verify_callback(
            self,
            origin_authorization,
            url,
            body,
            content_type='application/x-www-form-urlencoded'):
        """回调验证

        Args:
            origin_authorization: 回调时请求Header中的Authorization字段
            url:                  回调请求的url
            body:                 回调请求的body
            content_type:         回调请求body的Content-Type

        Returns:
            返回true表示验证成功，返回false表示验证失败
        """
        token = self.token_of_request(url, body, content_type)
        authorization = 'QBox {0}'.format(token)
        return origin_authorization == authorization

    @staticmethod
    def __copy_policy(policy, to, strict_policy):
        for k, v in policy.items():
            if (not strict_policy) or k in _policy_fields:
                to[k] = v


class RequestsAuth(AuthBase):
    def __init__(self, auth):
        self.auth = auth

    def __call__(self, r):
        if r.body is not None and r.headers['Content-Type'] == 'application/x-www-form-urlencoded':
            token = self.auth.token_of_request(
                r.url, r.body, 'application/x-www-form-urlencoded')
        else:
            token = self.auth.token_of_request(r.url)
        r.headers['Authorization'] = 'QBox {0}'.format(token)
        return r


class QiniuMacAuth(object):
    """
    Sign Requests

    Attributes:
        __access_key
        __secret_key

    http://kirk-docs.qiniu.com/apidocs/#TOC_325b437b89e8465e62e958cccc25c63f
    """

    def __init__(self, access_key, secret_key):
        self.qiniu_header_prefix = "X-Qiniu-"
        self.__checkKey(access_key, secret_key)
        self.__access_key = access_key
        self.__secret_key = b(secret_key)

    def __token(self, data):
        data = b(data)
        hashed = hmac.new(self.__secret_key, data, sha1)
        return urlsafe_base64_encode(hashed.digest())

    def token_of_request(
            self,
            method,
            host,
            url,
            qheaders,
            content_type=None,
            body=None):
        """
        <Method> <PathWithRawQuery>
        Host: <Host>
        Content-Type: <ContentType>
        [<X-Qiniu-*> Headers]

        [<Body>] #这里的 <Body> 只有在 <ContentType> 存在且不为 application/octet-stream 时才签进去。

        """
        parsed_url = urlparse(url)
        netloc = parsed_url.netloc
        path = parsed_url.path
        query = parsed_url.query

        if not host:
            host = netloc

        path_with_query = path
        if query != '':
            path_with_query = ''.join([path_with_query, '?', query])
        data = ''.join(["%s %s" %
                        (method, path_with_query), "\n", "Host: %s" %
                        host, "\n"])

        if content_type:
            data += "Content-Type: %s" % (content_type) + "\n"

        data += qheaders
        data += "\n"

        if content_type and content_type != "application/octet-stream" and body:
            data += body.decode(encoding='UTF-8')

        return '{0}:{1}'.format(self.__access_key, self.__token(data))

    def qiniu_headers(self, headers):
        res = ""
        for key in headers:
            if key.startswith(self.qiniu_header_prefix):
                res += key + ": %s\n" % (headers.get(key))
        return res

    @staticmethod
    def __checkKey(access_key, secret_key):
        if not (access_key and secret_key):
            raise ValueError('QiniuMacAuthSign : Invalid key')


class QiniuMacRequestsAuth(AuthBase):
    def __init__(self, auth):
        self.auth = auth

    def __call__(self, r):
        token = self.auth.token_of_request(
            r.method, r.headers.get('Host', None),
            r.url, self.auth.qiniu_headers(r.headers),
            r.headers.get('Content-Type', None),
            r.body
        )
        r.headers['Authorization'] = 'Qiniu {0}'.format(token)
        return r
