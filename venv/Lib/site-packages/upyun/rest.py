# -*- coding: utf-8 -*-
import os

from .modules.sign import make_signature,\
    make_content_md5, encode_msg, make_purge_signature
from .modules.exception import UpYunClientException
from .modules.compat import b, str, quote, urlencode, builtin_str
from .modules.httpipe import cur_dt
from .resume import UpYunResume


def get_fileobj_size(fileobj):
    if hasattr(fileobj, 'stream'):
        return int(fileobj.getheader("Content-Length"))

    try:
        if hasattr(fileobj, 'fileno'):
            return os.fstat(fileobj.fileno()).st_size
    except IOError:
        pass

    return len(fileobj.getvalue())


class UploadObject(object):
    def __init__(self, fileobj, chunksize=None, handler=None, params=None):
        self.fileobj = fileobj
        self.chunksize = chunksize
        self.totalsize = get_fileobj_size(fileobj)
        self.readsofar = 0
        self.hdr = None
        if handler:
            self.hdr = handler(self.totalsize, params)

    def __iter__(self):
        if hasattr(self.fileobj, 'stream'):
            yield self.fileobj.iter_content(self.chunksize)
        else:
            while True:
                chunk = self.fileobj.read(self.chunksize)
                if not chunk:
                    break
                yield chunk

    def __next__(self):
        chunk = self.fileobj.read(self.chunksize)
        if chunk and self.hdr:
            self.readsofar += len(chunk)
            if self.readsofar != self.totalsize:
                self.hdr.update(self.readsofar)
            else:
                self.hdr.finish()
        return chunk

    def __len__(self):
        return self.totalsize

    def read(self, size=-1):
        return self.__next__()


class UpYunRest(object):
    def __init__(self, service, username, password, auth_server,
                 endpoint, chunksize, hp):
        self.service = service
        self.username = username
        self.password = password
        self.auth_server = auth_server
        self.chunksize = chunksize
        self.endpoint = endpoint
        self.hp = hp
        self.host = None

    # --- public API
    def usage(self, key):
        res = self.__do_http_request('GET', key, args='?usage')
        return str(int(res))

    def _resume(self, key, f, file_size, checksum=None,
                secret=None, headers=None, store=None,
                reporter=None, part_size=None):
        if secret:
            headers = headers or {}
            headers['Content-Secret'] = secret
        resumer = UpYunResume(self, key, f, file_size,
                              headers, checksum, store, reporter, part_size)
        return resumer.upload()

    def put(self, key, value, checksum, headers, handler, params, secret,
            need_resume, store, reporter, part_size):
        """
        >>> with open('foo.png', 'rb') as f:
        >>>    res = up.put('/path/to/bar.png', f, checksum=False,
        >>>                 headers={'x-gmkerl-rotate': '180'}})
        """
        if need_resume and hasattr(value, 'fileno'):
            value.seek(0, os.SEEK_END)
            length = value.tell()
            value.seek(0, os.SEEK_SET)
            return self._resume(key, value, length, checksum, secret,
                                headers, store, reporter, part_size)

        if headers is None:
            headers = {}

        if isinstance(value, str):
            value = b(value)

        if checksum is True:
            headers['Content-MD5'] = make_content_md5(value, self.chunksize)

        if secret:
            headers['Content-Secret'] = secret

        if hasattr(value, 'fileno'):
            value = UploadObject(value, chunksize=self.chunksize,
                                 handler=handler, params=params)

        h = self.__do_http_request('PUT', key, value, headers)
        return self.__get_meta_headers(h)

    def get(self, key, value, handler, params):
        '''
        >>> with open('bar.png', 'wb') as f:
        >>>    up.get('/path/to/bar.png', f)
        '''
        return self.__do_http_request('GET', key, of=value, stream=True,
                                      handler=handler, params=params)

    def delete(self, key):
        self.__do_http_request('DELETE', key)

    def mkdir(self, key):
        headers = {'Folder': 'true'}
        self.__do_http_request('POST', key, headers=headers)

    @staticmethod
    def __make_list_headers(limit, order, begin):
        headers = {}
        header_tuple = (("X-List-Limit", limit),
                        ("X-List-Order", order),
                        ("X-List-Iter", begin))

        for k, v in header_tuple:
            if v is not None:
                headers[k] = str(v)
        return headers

    def getlist(self, key, limit, order, begin):
        headers = self.__make_list_headers(limit, order, begin)
        content = self.__do_http_request('GET', key, headers=headers)
        if content == '':
            return []
        items = content.split('\n')
        return [dict(zip(['name', 'type', 'size', 'time'],
                x.split('\t'))) for x in items]

    def get_list_with_iter(self, key, limit, order, begin):
        headers = self.__make_list_headers(limit, order, begin)
        resp = self.__do_http_request('GET', key, headers=headers,
                                      with_headers=True)
        ret = {'files': [], 'iter': None}
        if resp['headers']:
            ret['iter'] = dict(resp['headers']).get('x-upyun-list-iter')
        if resp['content'] == '':
            return ret
        items = resp['content'].split('\n')
        ret['files'] = [dict(zip(['name', 'type', 'size', 'time'],
                                 x.split('\t'))) for x in items]
        return ret

    def iterlist(self, key, limit, order, begin):
        headers = self.__make_list_headers(limit, order, begin)
        lines = self.__do_http_request('GET', key, headers=headers,
                                       stream=True, iter_line=True)
        for line in lines:
            decoded_line = line.decode('utf-8')
            yield dict(zip(['name', 'type', 'size', 'time'],
                           decoded_line.split('\t')))

    def getinfo(self, key):
        h = self.__do_http_request('HEAD', key)
        return self.__get_meta_headers(h)

    def purge(self, keys, domain):
        domain = domain or '%s.b0.upaiyun.com' % (self.service)
        if isinstance(keys, builtin_str):
            keys = [keys]
        if isinstance(keys, list):
            urlfmt = 'http://%s/%s'
            urlstr = '\n'.join([urlfmt % (domain, k if k[0] != '/' else k[1:])
                                for k in keys]) + '\n'
        else:
            raise UpYunClientException('keys type error')

        method = 'POST'
        host = 'purge.upyun.com'
        uri = '/purge/'
        params = urlencode({'purge': urlstr})
        headers = {'Content-Type': 'application/x-www-form-urlencoded',
                   'Accept': 'application/json'}
        self.__set_auth_headers(urlstr, headers=headers, is_purge=True)

        resp = self.hp.do_http_pipe(method, host, uri,
                                    value=params, headers=headers)
        content = self.__handle_resp(resp, method, uri=uri)
        invalid_urls = content['invalid_domain_of_url']
        return [k[7 + len(domain):] for k in invalid_urls if k]

    # --- private API
    def __do_http_request(self, method=None, key=None,
                          value=None, headers=None, of=None, args='',
                          stream=False, handler=None,
                          params=None, iter_line=False, with_headers=False):
        _uri = '/%s/%s' % (self.service, key if key[0] != '/' else key[1:])
        uri = '%s%s' % (quote(encode_msg(_uri), safe='~/'), args)

        if headers is None:
            headers = {}

        if self.host:
            headers["HOST"] = self.host

        length = 0
        if hasattr(value, '__len__'):
            length = len(value)
            headers['Content-Length'] = str(length)
        elif hasattr(value, 'fileno'):
            length = get_fileobj_size(value)
            headers['Content-Length'] = str(length)
            # [ugly]:compatible with newest requests feature
            # force the stream upload with empty file to normal upload
            if not length:
                value = ''
        elif value is not None:
            raise UpYunClientException('object type error')

        self.__set_auth_headers(uri, method, length, headers)

        resp = self.hp.do_http_pipe(method, self.endpoint, uri,
                                    value, headers, stream)
        return self.__handle_resp(resp, method, of, handler,
                                  params, iter_line=iter_line,
                                  with_headers=with_headers)

    do_http_request = __do_http_request

    def __handle_resp(self, resp, method=None, of=None,
                      handler=None, params=None, uri=None,
                      iter_line=False, with_headers=False):
        content = None
        try:
            if method == 'GET' and of:
                readsofar = 0
                try:
                    totalsize = int(resp.headers['content-length'])
                except (KeyError, TypeError):
                    totalsize = 0

                hdr = None
                if handler and totalsize > 0:
                    hdr = handler(totalsize, params)

                for chunk in resp.iter_content(self.chunksize):
                    if chunk and hdr:
                        readsofar += len(chunk)
                        if readsofar != totalsize:
                            hdr.update(readsofar)
                        else:
                            hdr.finish()
                    if not chunk:
                        break
                    of.write(chunk)
            elif method == 'GET' and iter_line:
                content = resp.iter_lines()
            elif method == 'GET' and with_headers:
                content = {'content': resp.text,
                           'headers': resp.headers.items()}
            elif method == 'GET':
                content = resp.text
            elif method == 'PUT' or method == 'HEAD':
                content = resp.headers.items()
            elif method == 'POST' and uri == '/purge/':
                content = resp.json()
        except Exception as e:
            raise UpYunClientException(e)
        return content

    def __get_meta_headers(self, headers):
        heads = {}
        for k, v in headers:
            k = k.lower()
            if k[:8] == 'x-upyun-' and k[8:] != 'uuid' and k[8:] != 'cluster':
                heads[k[8:]] = v
            elif k == "content-md5":
                heads[k] = v
            elif k == "etag":
                heads[k] = v
        return heads

    def __set_auth_headers(self, playload, method=None,
                           length=0, headers=None, is_purge=False):
        if headers is None:
            headers = {}

        dt = cur_dt()
        if not is_purge:
            signature = make_signature(username=self.username,
                                       password=self.password,
                                       auth_server=self.auth_server,
                                       method=method, uri=playload, date=dt,
                                       content_md5=headers.get('Content-MD5'))
        else:
            signature = make_purge_signature(self.service, self.username,
                                             self.password, playload, dt)

        headers['Authorization'] = signature
        headers['Date'] = dt
        return headers
