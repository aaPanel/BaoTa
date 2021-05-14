# -*- coding: utf-8 -*-
from .compat import builtin_str


class UpYunServiceException(Exception):
    def __init__(self, request_id, status, msg, err, headers=None):
        self.args = (request_id, status, msg, err)
        self.request_id = request_id
        self.status = status
        self.msg = msg
        self.err = err
        self.headers = headers or []


class UpYunClientException(Exception):
    def __init__(self, msg):
        self.msg = builtin_str(msg)
        super(UpYunClientException, self).__init__(msg)


class UpYunResumeTraceException(UpYunClientException):
    pass


class UpYunResumeException(UpYunClientException):
    pass
