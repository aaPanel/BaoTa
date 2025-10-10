import sys, os
from gzip import GzipFile
from io import BytesIO

try:
    import brotli
except ImportError:
    brotli = None

from flask import request, current_app, session, Response, g, abort
import public

if sys.version_info[:2] == (2, 6):
    class GzipFile(GzipFile):
        """ Backport of context manager support for python 2.6"""

        def __enter__(self):
            if self.fileobj is None:
                raise ValueError("I/O operation on closed GzipFile object")
            return self

        def __exit__(self, *args):
            self.close()


class DictCache(object):

    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        self.data[key] = value


class Compress(object):
    """
    The Compress object allows your application to use Flask-Compress.

    When initialising a Compress object you may optionally provide your
    :class:`flask.Flask` application object if it is ready. Otherwise,
    you may provide it later by using the :meth:`init_app` method.

    :param app: optional :class:`flask.Flask` application object
    :type app: :class:`flask.Flask` or None
    """

    def __init__(self, app=None):
        """
        An alternative way to pass your :class:`flask.Flask` application
        object to Flask-Compress. :meth:`init_app` also takes care of some
        default `settings`_.

        :param app: the :class:`flask.Flask` application object.
        """
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        defaults = [
            ('COMPRESS_MIMETYPES', ['text/html', 'text/css', 'text/xml',
                                    'application/json',
                                    'application/javascript',
                                    'application/x-javascript',
                                    'text/javascript',
                                    'image/png', 'image/jpg', 'image/jpeg',
                                    'image/gif',
                                    'image/svg+xml',
                                    'application/x-font-ttf',
                                    'font/opentype',
                                    'application/vnd.ms-fontobject',
                                    'application/font-woff',
                                    'application/x-font-woff',
                                    'application/font-woff2'

                                    ]),
            ('COMPRESS_MIMETYPES_STATUS', ['text/css',
                                           'application/javascript',
                                           'application/x-javascript',
                                           'text/javascript',
                                           'application/x-font-ttf',
                                           'font/opentype',
                                           'application/font-woff',
                                           'application/x-font-woff',
                                           'application/font-woff2'

                                           ]),
            ('COMPRESS_LEVEL', 6), # 2025/8/13 修改默认压缩级别，-9级约额外耗时30ms, -6约额外耗时5ms, 故修改
            ('COMPRESS_MIN_SIZE', 500),
            ('COMPRESS_CACHE_KEY', None),
            ('COMPRESS_CACHE_BACKEND', None),
            ('COMPRESS_REGISTER', True),
        ]

        for k, v in defaults:
            app.config.setdefault(k, v)

        backend = app.config['COMPRESS_CACHE_BACKEND']
        self.cache = backend() if backend else None
        self.cache_key = app.config['COMPRESS_CACHE_KEY']

        if (app.config['COMPRESS_REGISTER'] and
                app.config['COMPRESS_MIMETYPES']):
            app.after_request(self.after_request)

    def after_request(self, response):
        app = self.app or current_app
        accept_encoding = request.headers.get('Accept-Encoding', '')
        response.headers['Server'] = 'nginx'
        # response.headers['Connection'] = 'keep-alive'
        if response.status_code in [404, 403]:
            return response

        if not 'tmp_login' in session:
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
        if 'dologin' in g and app.config['SSL']:
            try:
                for k, v in request.cookies.items():
                    response.set_cookie(k, '', expires='Thu, 01-Jan-1970 00:00:00 GMT', path='/')
            except:
                pass

        if 'rm_ssl' in g:
            import public
            try:
                for k, v in request.cookies.items():
                    response.set_cookie(k, '', expires='Thu, 01-Jan-1970 00:00:00 GMT', path='/')
            except:
                pass
            session_name = app.config['SESSION_COOKIE_NAME']
            session_id = public.get_session_id()
            response.set_cookie(session_name, '', expires='Thu, 01-Jan-1970 00:00:00 GMT', path='/')
            response.set_cookie(session_name.replace('_ssl', ''), session_id, path='/', max_age=86400 * 30, httponly=True)

            request_token = request.cookies.get('request_token', '')
            if request_token:
                response.set_cookie('request_token', request_token, path='/', max_age=86400 * 30)
        elif 'set_ssl' in g:  # 设置SSL时，将sessionid写入cookie
            import public
            session_name = app.config['SESSION_COOKIE_NAME']
            session_id = public.get_session_id()
            response.set_cookie(session_name, '', expires='Thu, 01-Jan-1970 00:00:00 GMT', path='/')
            response.set_cookie(session_name + '_ssl', session_id, path='/', max_age=86400 * 30, httponly=True)

        # 如果有前置代理，直接返回
        if request.headers.get('X-Real-IP'):
            return response

        if (response.mimetype not in app.config['COMPRESS_MIMETYPES'] or
                'gzip' not in accept_encoding.lower() or
                not 200 <= response.status_code < 300 or
                (response.content_length is not None and
                 response.content_length < app.config['COMPRESS_MIN_SIZE']) or
                'Content-Encoding' in response.headers):
            g.response = response
            return response

        response.direct_passthrough = False

        # 优先使用br压缩
        if 'br' in accept_encoding.lower() and brotli is not None:
            br_content = self.get_compress(app, response, 'brotli')
            if br_content:
                response.set_data(br_content)
                response.headers['Content-Encoding'] = 'br'
        else:
            # 使用GZIP压缩
            gzip_content = self.get_compress(app, response, 'gzip')
            if gzip_content:
                response.set_data(gzip_content)
                response.headers['Content-Encoding'] = 'gzip'

        # 重新设置Content-Length
        response.headers['Content-Length'] = response.content_length

        # 设置cache-control
        if 'Cache-Control' not in response.headers:
            # 判断是否为js,css,png,jpg,gif等静态文件
            if response.mimetype in ('text/css', 'application/javascript',
                                     'application/x-javascript', 'text/javascript',
                                     'image/png', 'image/jpg', 'image/jpeg',
                                     'image/gif', 'image/svg+xml',
                                     'application/x-font-ttf', 'font/opentype',
                                     'application/vnd.ms-fontobject',
                                     'application/font-woff', 'application/x-font-woff',
                                     'application/font-woff2'):
                response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'

        vary = response.headers.get('Vary')
        if vary:
            if 'accept-encoding' not in vary.lower():
                response.headers['Vary'] = '{}, Accept-Encoding'.format(vary)
        else:
            response.headers['Vary'] = 'Accept-Encoding'

        g.response = response
        return response

    def get_compress(self, app, response, compress_type):
        '''
            @name 获取压缩后的内容
            @param app: flask app对象
            @param response: flask response对象
            @param compress_type: 压缩类型 gzip/brotli
            @return bytes
        '''
        is_static = response.mimetype in app.config['COMPRESS_MIMETYPES_STATUS']
        if is_static:
            compress_cache_path = "{}/data/compress_caches/{}".format(public.get_panel_path(), compress_type)
            if not os.path.exists(compress_cache_path):
                try:
                    os.makedirs(compress_cache_path, 384)
                except Exception as e:
                    pass

            key = public.md5(response.get_data())
            compress_cache_file = "{}/{}.gz".format(compress_cache_path, key)
            if os.path.exists(compress_cache_file):
                try:
                    # 判断文件大小
                    stat = os.stat(compress_cache_file)
                    if stat.st_size > 0:
                        with open(compress_cache_file, 'rb') as f:
                            return f.read()
                except Exception as e:
                    pass

        
        if compress_type == 'brotli':
            content = self.compress_br(app, response, is_static)
        else:
            content = self.compress_gzip(app, response, is_static)
        # 只写静态文件的缓存
        if is_static:
            try:
                with open(compress_cache_file, 'wb') as f:
                    f.write(content)
            except Exception as e:
                pass
        return content

    def compress_gzip(self, app, response, is_static):
        '''
            @name GZIP压缩
            @param app: flask app对象
            @param response: flask response对象
            @param is_static: 是否为静态文件
            @return bytes
        '''
        level = app.config['COMPRESS_LEVEL']
        try:
            if is_static and response.content_length is not None:  # 调整静态文件的压缩级别,   兼容content_length为None的情况
                if response.content_length > 1024 * 20:
                    level = 9
                elif response.content_length > 1024 * 10:
                    level = 7
                elif response.content_length > 1024 * 5:
                    level = 6
        except:
            pass
        gzip_buffer = BytesIO()
        with GzipFile(mode='wb',
                      compresslevel=level,
                      fileobj=gzip_buffer) as gzip_file:
            gzip_file.write(response.get_data())
        return gzip_buffer.getvalue()

    def compress_br(self, app, response, is_static):
        '''
            @name Brotli压缩
            @param app: flask app对象
            @param response: flask response对象
            @param is_static: 是否为静态文件
            @return bytes
        '''
        quality = app.config['COMPRESS_LEVEL']
        try:
            if is_static:  # 调整静态文件的压缩级别
                if response.content_length > 1024 * 20:
                    quality = 9
                elif response.content_length > 1024 * 10:
                    quality = 9
                elif response.content_length > 1024 * 5:
                    quality = 6
        except:
            pass
        return brotli.compress(response.get_data(), quality=quality)
