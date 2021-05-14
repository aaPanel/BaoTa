# -*- coding: utf-8 -*-

"""
oss2.exceptions
~~~~~~~~~~~~~~

异常类。
"""

import re

import xml.etree.ElementTree as ElementTree
from xml.parsers import expat


from .compat import to_string
from .headers import *


_OSS_ERROR_TO_EXCEPTION = {}  # populated at end of module


OSS_CLIENT_ERROR_STATUS = -1
OSS_REQUEST_ERROR_STATUS = -2
OSS_INCONSISTENT_ERROR_STATUS = -3
OSS_FORMAT_ERROR_STATUS = -4
OSS_SELECT_CLIENT_ERROR_STATUS = -5


class OssError(Exception):
    def __init__(self, status, headers, body, details):
        #: HTTP 状态码
        self.status = status

        #: 请求ID，用于跟踪一个OSS请求。提交工单时，最好能够提供请求ID
        self.request_id = headers.get(OSS_REQUEST_ID, '')

        #: HTTP响应体（部分）
        self.body = body

        #: 详细错误信息，是一个string到string的dict
        self.details = details

        #: OSS错误码
        self.code = self.details.get('Code', '')

        #: OSS错误信息
        self.message = self.details.get('Message', '')

    def __str__(self):
        error = {'status': self.status,
                 OSS_REQUEST_ID : self.request_id,
                 'details': self.details}
        return str(error)

    def _str_with_body(self):
        error = {'status': self.status,
                 OSS_REQUEST_ID : self.request_id,
                 'details': self.body}
        return str(error)


class ClientError(OssError):
    def __init__(self, message):
        OssError.__init__(self, OSS_CLIENT_ERROR_STATUS, {}, 'ClientError: ' + message, {})

    def __str__(self):
        return self._str_with_body()


class RequestError(OssError):
    def __init__(self, e):
        OssError.__init__(self, OSS_REQUEST_ERROR_STATUS, {}, 'RequestError: ' + str(e), {})
        self.exception = e

    def __str__(self):
        return self._str_with_body()


class InconsistentError(OssError):
    def __init__(self, message, request_id=''):
        OssError.__init__(self, OSS_INCONSISTENT_ERROR_STATUS, {OSS_REQUEST_ID : request_id}, 'InconsistentError: ' + message, {})

    def __str__(self):
        return self._str_with_body()


class OpenApiFormatError(OssError):
    def __init__(self, message):
        OssError.__init__(self, OSS_FORMAT_ERROR_STATUS, {}, message, {})

    def __str__(self):
        return self._str_with_body()


class OpenApiServerError(OssError):
    def __init__(self, status, request_id, message, error_code):
        OssError.__init__(self, status, {OSS_REQUEST_ID : request_id}, '', {'Code': error_code, 'Message': message})


class ServerError(OssError):
    pass


class NotFound(ServerError):
    status = 404
    code = ''


class MalformedXml(ServerError):
    status = 400
    code = 'MalformedXML'


class InvalidRequest(ServerError):
    status = 400
    code = 'InvalidRequest'


class OperationNotSupported(ServerError):
    status = 400
    code = 'OperationNotSupported'


class RestoreAlreadyInProgress(ServerError):
    status = 409
    code = 'RestoreAlreadyInProgress'


class InvalidArgument(ServerError):
    status = 400
    code = 'InvalidArgument'

    def __init__(self, status, headers, body, details):
        super(InvalidArgument, self).__init__(status, headers, body, details)
        self.name = details.get('ArgumentName')
        self.value = details.get('ArgumentValue')


class InvalidDigest(ServerError):
    status = 400
    code = 'InvalidDigest'


class InvalidObjectName(ServerError):
    status = 400
    code = 'InvalidObjectName'


class NoSuchBucket(NotFound):
    status = 404
    code = 'NoSuchBucket'


class NoSuchKey(NotFound):
    status = 404
    code = 'NoSuchKey'


class NoSuchUpload(NotFound):
    status = 404
    code = 'NoSuchUpload'


class NoSuchWebsite(NotFound):
    status = 404
    code = 'NoSuchWebsiteConfiguration'


class NoSuchLifecycle(NotFound):
    status = 404
    code = 'NoSuchLifecycle'


class NoSuchCors(NotFound):
    status = 404
    code = 'NoSuchCORSConfiguration'


class NoSuchLiveChannel(NotFound):
    status = 404
    code = 'NoSuchLiveChannel'


class NoSuchBucketPolicy(NotFound):
    status = 404
    code = 'NoSuchBucketPolicy'


class Conflict(ServerError):
    status = 409
    code = ''


class BucketNotEmpty(Conflict):
    status = 409
    code = 'BucketNotEmpty'


class PositionNotEqualToLength(Conflict):
    status = 409
    code = 'PositionNotEqualToLength'

    def __init__(self, status, headers, body, details):
        super(PositionNotEqualToLength, self).__init__(status, headers, body, details)
        self.next_position = int(headers[OSS_NEXT_APPEND_POSITION])


class ObjectNotAppendable(Conflict):
    status = 409
    code = 'ObjectNotAppendable'


class ChannelStillLive(Conflict):
    status = 409
    code = 'ChannelStillLive'


class LiveChannelDisabled(Conflict):
    status = 409
    code = 'LiveChannelDisabled'


class PreconditionFailed(ServerError):
    status = 412
    code = 'PreconditionFailed'


class NotModified(ServerError):
    status = 304
    code = ''


class AccessDenied(ServerError):
    status = 403
    code = 'AccessDenied'

class NoSuchServerSideEncryptionRule(NotFound):
    status = 404
    code = 'NoSuchServerSideEncryptionRule'

class InvalidEncryptionAlgorithmError(ServerError):
    status = 400
    code = 'InvalidEncryptionAlgorithmError' 

class SelectOperationFailed(ServerError):
    code = 'SelectOperationFailed'
    def __init__(self, status, code, message):
        self.status = status
        self.code = code
        self.message = message

    def __str__(self):
        error = {'status': self.status,
                 'code': self.code,
                 'details': self.message}
        return str(error)

class SelectOperationClientError(OssError):
    def __init__(self, message, request_id):
        OssError.__init__(self, OSS_SELECT_CLIENT_ERROR_STATUS, {'x-oss-request-id': request_id}, 'SelectOperationClientError: ' + message, {})
        
    def __str__(self):
        error = {'x-oss-request-id':self.request_id,
                'message': self.message}
        return str(error)

class SignatureDoesNotMatch(ServerError):
    status = 403
    code = 'SignatureDoesNotMatch'

class ObjectAlreadyExists(ServerError):
    status = 400
    code = 'ObjectAlreadyExists'

def make_exception(resp):
    status = resp.status
    headers = resp.headers
    body = resp.read(4096)
    details = _parse_error_body(body)
    code = details.get('Code', '')

    try:
        klass = _OSS_ERROR_TO_EXCEPTION[(status, code)]
        return klass(status, headers, body, details)
    except KeyError:
        return ServerError(status, headers, body, details)


def _walk_subclasses(klass):
    for sub in klass.__subclasses__():
        yield sub
        for subsub in _walk_subclasses(sub):
            yield subsub


for klass in _walk_subclasses(ServerError):
    status = getattr(klass, 'status', None)
    code = getattr(klass, 'code', None)

    if status is not None and code is not None:
        _OSS_ERROR_TO_EXCEPTION[(status, code)] = klass


# XML parsing exceptions have changed in Python2.7 and ElementTree 1.3
if hasattr(ElementTree, 'ParseError'):
    ElementTreeParseError = (ElementTree.ParseError, expat.ExpatError)
else:
    ElementTreeParseError = (expat.ExpatError)


def _parse_error_body(body):
    try:
        root = ElementTree.fromstring(body)
        if root.tag != 'Error':
            return {}

        details = {}
        for child in root:
            details[child.tag] = child.text
        return details
    except ElementTreeParseError:
        return _guess_error_details(body)


def _guess_error_details(body):
    details = {}
    body = to_string(body)

    if '<Error>' not in body or '</Error>' not in body:
        return details

    m = re.search('<Code>(.*)</Code>', body)
    if m:
        details['Code'] = m.group(1)

    m = re.search('<Message>(.*)</Message>', body)
    if m:
        details['Message'] = m.group(1)

    return details
