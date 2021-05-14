# -*- coding: utf-8 -*-

import hashlib
import base64
import hmac
import json

import requests

from .compat import b, PY3, builtin_str, bytes, str
from .exception import UpYunClientException

DEFAULT_CHUNKSIZE = 8192


def make_content_md5(value, chunksize=DEFAULT_CHUNKSIZE):
    if hasattr(value, 'fileno'):
        md5 = hashlib.md5()
        for chunk in iter(lambda: value.read(chunksize), b''):
            md5.update(chunk)
        value.seek(0)
        return md5.hexdigest()
    elif isinstance(value, bytes) or (not PY3 and
                                      isinstance(value, builtin_str)):
        return hashlib.md5(value).hexdigest()
    else:
        raise UpYunClientException('object type error')


def decode_msg(msg):
    if isinstance(msg, bytes):
        msg = msg.decode('utf-8')
    return msg


def encode_msg(msg):
    if isinstance(msg, str):
        msg = msg.encode('utf-8')
    return msg


def make_policy(data):
    policy = json.dumps(data)
    return base64.b64encode(b(policy))


def make_signature(**kwargs):
    """The standard signature algorithm. avaliable kwargs:
    username: operator
    password: password md5
    method: GET, POST ...
    uri: uri
    date: fmt rfc1123
    *policy: params md5
    *content_md5: content md5
    *auth_server: the remote address of authentication server
    """
    for k in kwargs:
        if isinstance(kwargs[k], bytes):
            kwargs[k] = kwargs[k].decode()

    if kwargs.get('auth_server'):
        auth_server = kwargs.pop('auth_server')
        resp = requests.post(auth_server, json=kwargs)
        return resp.text

    signarr = [kwargs['method'], kwargs['uri'], kwargs['date']]
    if kwargs.get('policy'):
        signarr.append(kwargs['policy'])
    if kwargs.get('content_md5'):
        signarr.append(kwargs['content_md5'])
    signstr = '&'.join(signarr)
    signature = base64.b64encode(
        hmac.new(b(kwargs['password']), b(signstr),
                 digestmod=hashlib.sha1).digest()
    ).decode()
    return 'UPYUN %s:%s' % (kwargs['username'], signature)


def make_purge_signature(service, username, password, uri, date):
    signstr = '&'.join([uri, service, date, password])
    signature = hashlib.md5(b(signstr)).hexdigest()
    return 'UpYun %s:%s:%s' % (service, username, signature)
