# -*- coding: utf-8 -*-

"""
oss2.http
~~~~~~~~

这个模块包含了HTTP Adapters。尽管OSS Python SDK内部使用requests库进行HTTP通信，但是对使用者是透明的。
该模块中的 `Session` 、 `Request` 、`Response` 对requests的对应的类做了简单的封装。
"""

import platform

import requests
from requests.structures import CaseInsensitiveDict

from . import __version__, defaults
from .compat import to_bytes
from .exceptions import RequestError
from .utils import file_object_remaining_bytes, SizedFileAdapter

import logging

_USER_AGENT = 'aliyun-sdk-python/{0}({1}/{2}/{3};{4})'.format(
    __version__, platform.system(), platform.release(), platform.machine(), platform.python_version())

logger = logging.getLogger(__name__)

class Session(object):
    """属于同一个Session的请求共享一组连接池，如有可能也会重用HTTP连接。"""
    def __init__(self):
        self.session = requests.Session()

        psize = defaults.connection_pool_size
        self.session.mount('http://', requests.adapters.HTTPAdapter(pool_connections=psize, pool_maxsize=psize))
        self.session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=psize, pool_maxsize=psize))

    def do_request(self, req, timeout):
        try:
            logger.debug("Send request, method: {0}, url: {1}, params: {2}, headers: {3}, timeout: {4}".format(
                req.method, req.url, req.params, req.headers, timeout))
            return Response(self.session.request(req.method, req.url,
                                                 data=req.data,
                                                 params=req.params,
                                                 headers=req.headers,
                                                 stream=True,
                                                 timeout=timeout))
        except requests.RequestException as e:
            raise RequestError(e)


class Request(object):
    def __init__(self, method, url,
                 data=None,
                 params=None,
                 headers=None,
                 app_name=''):
        self.method = method
        self.url = url
        self.data = _convert_request_body(data)
        self.params = params or {}

        if not isinstance(headers, CaseInsensitiveDict):
            self.headers = CaseInsensitiveDict(headers)
        else:
            self.headers = headers

        # tell requests not to add 'Accept-Encoding: gzip, deflate' by default
        if 'Accept-Encoding' not in self.headers:
            self.headers['Accept-Encoding'] = None

        if 'User-Agent' not in self.headers:
            if app_name:
                self.headers['User-Agent'] = _USER_AGENT + '/' + app_name
            else:
                self.headers['User-Agent'] = _USER_AGENT
        logger.debug("Init request, method: {0}, url: {1}, params: {2}, headers: {3}".format(method, url, params,
                                                                                             headers))


_CHUNK_SIZE = 8 * 1024


class Response(object):
    def __init__(self, response):
        self.response = response
        self.status = response.status_code
        self.headers = response.headers
        self.request_id = response.headers.get('x-oss-request-id', '')

        # When a response contains no body, iter_content() cannot
        # be run twice (requests.exceptions.StreamConsumedError will be raised).
        # For details of the issue, please see issue #82
        #
        # To work around this issue, we simply return b'' when everything has been read.
        #
        # Note you cannot use self.response.raw.read() to implement self.read(), because
        # raw.read() does not uncompress response body when the encoding is gzip etc., and
        # we try to avoid depends on details of self.response.raw.
        self.__all_read = False

        logger.debug("Get response headers, req-id:{0}, status: {1}, headers: {2}".format(self.request_id, self.status,
                                                                                          self.headers))

    def read(self, amt=None):
        if self.__all_read:
            return b''

        if amt is None:
            content_list = []
            for chunk in self.response.iter_content(_CHUNK_SIZE):
                content_list.append(chunk)
            content = b''.join(content_list)

            self.__all_read = True
            # logger.debug("Get response body, req-id: {0}, content: {1}", self.request_id, content)
            return content
        else:
            try:
                return next(self.response.iter_content(amt))
            except StopIteration:
                self.__all_read = True
                return b''

    def __iter__(self):
        return self.response.iter_content(_CHUNK_SIZE)


# requests对于具有fileno()方法的file object，会用fileno()的返回值作为Content-Length。
# 这对于已经读取了部分内容，或执行了seek()的file object是不正确的。
#
# _convert_request_body()对于支持seek()和tell() file object，确保是从
# 当前位置读取，且只读取当前位置到文件结束的内容。
def _convert_request_body(data):
    data = to_bytes(data)

    if hasattr(data, '__len__'):
        return data

    if hasattr(data, 'seek') and hasattr(data, 'tell'):
        return SizedFileAdapter(data, file_object_remaining_bytes(data))

    return data


