# -*- coding: utf-8 -*-

import json
import base64

from .modules.compat import urlencode, b
from .modules.exception import UpYunClientException, UpYunServiceException
from .modules.sign import (
    decode_msg,
    make_signature,
    make_content_md5
)
from .modules.httpipe import cur_dt


class AvPretreatment(object):
    HOST = 'p0.api.upyun.com'
    PRETREAT = '/pretreatment/'
    STATUS = '/status/'
    KEYS = ['service',
            'status_code',
            'path',
            'description',
            'task_id',
            'info',
            'signature']

    def __init__(self, service, operator, password,
                 auth_server, chunksize, hp):
        self.service = service
        self.operator = operator
        self.password = password
        self.auth_server = auth_server
        self.chunksize = chunksize
        self.hp = hp

    # --- public API
    def pretreat(self, tasks, source, notify_url, app_name=None):
        data = {'service': self.service, 'source': source,
                'notify_url': notify_url, 'tasks': tasks,
                'app_name': app_name, 'accept': 'json'}
        if not app_name:
            data.pop('app_name')
        return self.__requests_pretreatment(data)

    def status(self, taskids):
        data = {}
        if type(taskids) == 'str':
            taskids = taskids.split(',')
        if type(taskids) == list and len(taskids) <= 20:
            taskids = ','.join(taskids)
        else:
            raise UpYunClientException('length of taskids should less than 20')

        data['service'] = self.service
        data['task_ids'] = taskids
        content = self.__requests_status(data)
        if type(content) == dict and 'tasks' in content:
            return content['tasks']
        raise UpYunServiceException(None, 500,
                                    'Servers except respond tasks list',
                                    'Service Error')

    # --- private API
    def __requests_pretreatment(self, data):
        method = 'POST'
        tasks = data['tasks']
        assert isinstance(tasks, list)
        data['tasks'] = decode_msg(base64.b64encode(b(json.dumps(tasks))))

        uri = self.PRETREAT
        value = urlencode(data)
        dt = cur_dt()
        md5sum = make_content_md5(b(value))
        signature = make_signature(username=self.operator,
                                   password=self.password,
                                   auth_server=self.auth_server,
                                   method=method, uri=uri,
                                   date=dt, content_md5=md5sum)
        headers = {'Authorization': signature,
                   'Content-Type': 'application/x-www-form-urlencoded',
                   'Date': dt,
                   'Content-MD5': md5sum}
        resp = self.hp.do_http_pipe(method, self.HOST, uri,
                                    headers=headers, value=value)
        return self.__handle_resp(resp)

    def __requests_status(self, data):
        method = 'GET'
        dt = cur_dt()
        data = urlencode(data)
        uri = '%s?%s' % (self.STATUS, data)
        signature = make_signature(username=self.operator,
                                   password=self.password,
                                   auth_server=self.auth_server,
                                   method=method, uri=uri, date=dt)
        headers = {'Authorization': signature,
                   'Date': dt}
        resp = self.hp.do_http_pipe(method, self.HOST, uri, headers=headers)
        return self.__handle_resp(resp)

    def __handle_resp(self, resp):
        content = None
        try:
            content = resp.json()
        except Exception as e:
            raise UpYunClientException(e)
        return content

    def __set_params_by_post(self, value):
        data = {}
        for k, v in value.items():
            if k in self.KEYS:
                data[k] = ''.join(v) if isinstance(v, list) else v
        return data
