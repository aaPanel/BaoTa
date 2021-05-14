# -*- coding: utf-8 -*-
import os
import time

from .modules.exception import UpYunClientException
from .modules.sign import make_policy, make_signature
from .modules.httpipe import cur_dt


class FormUpload(object):

    def __init__(self, service, username, password,
                 auth_server, endpoint, hp):
        self.service = service
        self.username = username
        self.password = password
        self.auth_server = auth_server
        self.hp = hp
        self.host = endpoint
        self.uri = '/%s/' % service

    def upload(self, key, value, expiration, **kwargs):
        expiration = expiration or 1800
        expiration += int(time.time())
        dt = cur_dt()
        data = {
            'service': self.service,
            'expiration': expiration,
            'save-key': key,
            'date': dt,
        }
        data.update(kwargs)
        policy = make_policy(data)
        signature = make_signature(
            username=self.username,
            password=self.password,
            auth_server=self.auth_server,
            method='POST',
            uri=self.uri,
            date=dt,
            policy=policy
        )
        postdata = {
            'policy': policy,
            'authorization': signature,
            'file': (os.path.basename(value.name), value),
        }
        resp = self.hp.do_http_pipe('POST', self.host, self.uri,
                                    files=postdata)
        return self.__handle_resp(resp)

    def __handle_resp(self, resp):
        content = None
        try:
            content = resp.json()
        except Exception as e:
            raise UpYunClientException(e)
        return content
