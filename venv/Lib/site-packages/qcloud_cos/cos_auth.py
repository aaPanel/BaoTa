# -*- coding: utf-8 -*-

from six.moves.urllib.parse import quote, unquote, urlparse, urlencode
import hmac
import time
import hashlib
import logging
from requests.auth import AuthBase
from .cos_comm import to_unicode, to_bytes
logger = logging.getLogger(__name__)


def filter_headers(data):
    """只设置host content-type 还有x开头的头部.

    :param data(dict): 所有的头部信息.
    :return(dict): 计算进签名的头部.
    """
    headers = {}
    for i in data:
        if i == 'Content-Type' or i == 'Host' or i[0] == 'x' or i[0] == 'X':
            headers[i] = data[i]
    return headers


class CosS3Auth(AuthBase):

    def __init__(self, conf, key=None, params={}, expire=10000):
        self._secret_id = conf._secret_id
        self._secret_key = conf._secret_key
        self._anonymous = conf._anonymous
        self._expire = expire
        self._params = params
        if key:
            key = to_unicode(key)
            if key[0] == u'/':
                self._path = key
            else:
                self._path = u'/' + key
        else:
            self._path = u'/'

    def __call__(self, r):
        path = self._path
        uri_params = self._params
        headers = filter_headers(r.headers)
        uri_params = dict([(k.lower(), v) for k, v in uri_params.items()])
        # reserved keywords in headers urlencode are -_.~, notice that / should be encoded and space should not be encoded to plus sign(+)
        headers = dict([(k.lower(), quote(to_bytes(v), '-_.~')) for k, v in headers.items()])  # headers中的key转换为小写，value进行encode
        uri_params = dict([(k.lower(), v) for k, v in uri_params.items()])
        format_str = u"{method}\n{host}\n{params}\n{headers}\n".format(
            method=r.method.lower(),
            host=path,
            params=urlencode(sorted(uri_params.items())).replace('+', '%20').replace('%7E', '~'),
            headers='&'.join(map(lambda tupl: "%s=%s" % (tupl[0], tupl[1]), sorted(headers.items())))
        )
        logger.debug("format str: " + format_str)

        start_sign_time = int(time.time())
        sign_time = "{bg_time};{ed_time}".format(bg_time=start_sign_time-60, ed_time=start_sign_time+self._expire)
        sha1 = hashlib.sha1()
        sha1.update(to_bytes(format_str))

        str_to_sign = "sha1\n{time}\n{sha1}\n".format(time=sign_time, sha1=sha1.hexdigest())
        logger.debug('str_to_sign: ' + str(str_to_sign))
        sign_key = hmac.new(to_bytes(self._secret_key), to_bytes(sign_time), hashlib.sha1).hexdigest()
        sign = hmac.new(to_bytes(sign_key), to_bytes(str_to_sign), hashlib.sha1).hexdigest()
        logger.debug('sign_key: ' + str(sign_key))
        logger.debug('sign: ' + str(sign))
        sign_tpl = "q-sign-algorithm=sha1&q-ak={ak}&q-sign-time={sign_time}&q-key-time={key_time}&q-header-list={headers}&q-url-param-list={params}&q-signature={sign}"

        r.headers['Authorization'] = sign_tpl.format(
            ak=self._secret_id,
            sign_time=sign_time,
            key_time=sign_time,
            params=';'.join(sorted(map(lambda k: k.lower(), uri_params.keys()))),
            headers=';'.join(sorted(headers.keys())),
            sign=sign
        )
        if self._anonymous:
            r.headers['Authorization'] = ""
        logger.debug("sign_key" + str(sign_key))
        logger.debug(r.headers['Authorization'])
        logger.debug("request headers: " + str(r.headers))
        return r


if __name__ == "__main__":
    pass
