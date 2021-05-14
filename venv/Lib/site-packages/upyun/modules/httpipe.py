# -*- coding: utf-8 -*-
import requests
import datetime
import upyun
import json

from .exception import UpYunServiceException, UpYunClientException


# - wsgiref.handlers.format_date_time
def httpdate_rfc1123(dt):
    '''Return a string representation of a date according to RFC 1123
    (HTTP/1.1).

    The supplied date must be in UTC.

    '''
    weekday = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][dt.weekday()]
    month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep',
             'Oct', 'Nov', 'Dec'][dt.month - 1]
    return '%s, %02d %s %04d %02d:%02d:%02d GMT' % \
        (weekday, dt.day, month, dt.year, dt.hour, dt.minute, dt.second)


# - Date Format: RFC 1123
def cur_dt():
    return httpdate_rfc1123(datetime.datetime.utcnow())


class UpYunHttp(object):
    def __init__(self, timeout, debug):
        self.timeout = timeout
        self.debug = debug
        self.session = requests.Session()
        self.user_agent = None

    # - http://docs.python-requests.org/
    def do_http_pipe(self, method, host, uri,
                     value=None, headers={}, stream=False, files=None):
        request_id, msg, err, status = [None] * 4
        url = 'http://%s%s' % (host, uri)
        requests.adapters.DEFAULT_RETRIES = 5
        headers = self.__set_headers(headers)

        if self.debug:
            with open('debug.log', 'a') as f:
                f.write('\n\n## Http request params ##\n\n')
                kwargs = {'method': method, 'host': host, 'uri': uri,
                          'value': value, 'headers': headers,
                          'stream': stream, 'files': files,
                          'timeout': self.timeout,
                          }
                f.write('\n'.join(map(lambda kv: '%s: %s'
                                  % (kv[0], kv[1]), kwargs.items())))

        try:
            resp = self.session.request(method, url, data=value,
                                        headers=headers, stream=stream,
                                        timeout=self.timeout, files=files)
            resp.encoding = 'utf-8'
            try:
                request_id = resp.headers['X-Request-Id']
            except KeyError:
                request_id = 'Unknown'
            status = resp.status_code
            if status // 100 != 2:
                msg = resp.reason or "Unknown"
                err = resp.text
                headers = resp.headers.items()

            if self.debug:
                with open('debug.log', 'a') as f:
                    f.write('\n\n## Http responds ##\n\n')
                    kwargs = {'request_id': request_id, 'status': status,
                              'msg': msg, 'err': err}
                    f.write('\n'.join(map(lambda kv: '%s: %s'
                                      % (kv[0], kv[1]), kwargs.items())))

        except requests.exceptions.ConnectionError as e:
            raise UpYunClientException(e)
        except requests.exceptions.RequestException as e:
            raise UpYunClientException(e)
        except Exception as e:
            raise UpYunClientException(e)

        if msg:
            raise UpYunServiceException(request_id, status, msg, err, headers)

        return resp

    def __make_user_agent(self):
        default = 'upyun-python-sdk/%s' % upyun.__version__
        return json.dumps('%s %s' % (
            default, requests.utils.default_user_agent()))

    def __set_headers(self, headers):
        if 'Date' not in headers:
            headers['Date'] = cur_dt()
        if 'User-Agent' not in headers:
            headers['User-Agent'] = self.__make_user_agent()
        return headers
