# -*- coding=utf-8

import xml.dom.minidom


class CosException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


def digest_xml(data):
    msg = dict()
    try:
        tree = xml.dom.minidom.parseString(data)
        root = tree.documentElement

        result = root.getElementsByTagName('Code')
        msg['code'] = result[0].childNodes[0].nodeValue

        result = root.getElementsByTagName('Message')
        msg['message'] = result[0].childNodes[0].nodeValue

        result = root.getElementsByTagName('Resource')
        msg['resource'] = result[0].childNodes[0].nodeValue

        result = root.getElementsByTagName('RequestId')
        msg['requestid'] = result[0].childNodes[0].nodeValue

        result = root.getElementsByTagName('TraceId')
        if result:
            msg['traceid'] = result[0].childNodes[0].nodeValue
        else:
            msg['traceid'] = 'Unknown'
        return msg
    except Exception as e:
        return "Response Error Msg Is INVALID"


class CosClientError(CosException):
    """Client端错误，如timeout"""
    def __init__(self, message):
        CosException.__init__(self, message)


class CosServiceError(CosException):
    """COS Server端错误，可以获取特定的错误信息"""
    def __init__(self, method, message, status_code):
        CosException.__init__(self, message)
        if method == 'HEAD':  # 对HEAD进行特殊处理
            self._origin_msg = ''
            self._digest_msg = message
        else:
            self._origin_msg = message
            self._digest_msg = digest_xml(message)
        self._status_code = status_code

    def get_origin_msg(self):
        """获取原始的XML格式错误信息"""
        return self._origin_msg

    def get_digest_msg(self):
        """获取经过处理的dict格式的错误信息"""
        return self._digest_msg

    def get_status_code(self):
        """获取http error code"""
        return self._status_code

    def get_error_code(self):
        """获取COS定义的错误码描述,服务器返回错误信息格式出错时，返回空 """
        if isinstance(self._digest_msg, dict):
            return self._digest_msg['code']
        return "Unknown"

    def get_error_msg(self):
        if isinstance(self._digest_msg, dict):
            return self._digest_msg['message']
        return "Unknown"

    def get_resource_location(self):
        if isinstance(self._digest_msg, dict):
            return self._digest_msg['resource']
        return "Unknown"

    def get_trace_id(self):
        if isinstance(self._digest_msg, dict):
            return self._digest_msg['requestid']
        return "Unknown"

    def get_request_id(self):
        if isinstance(self._digest_msg, dict):
            return self._digest_msg['traceid']
        return "Unknown"
