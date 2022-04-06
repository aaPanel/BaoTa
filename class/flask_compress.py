import sys,os
from gzip import GzipFile
from io import BytesIO

from flask import request, current_app,session,Response,g,abort


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
                                    'application/javascript']),
            ('COMPRESS_LEVEL', 3),
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
        response.headers['Connection'] = 'keep-alive'
        if not 'tmp_login' in session:
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
        if 'dologin' in g and app.config['SSL']:
            try:
                for k,v in request.cookies.items():
                    response.set_cookie(k,'',expires='Thu, 01-Jan-1970 00:00:00 GMT',path='/')
            except:
                pass          

        if 'rm_ssl' in g:
            import public
            try:
                for k,v in request.cookies.items():
                    response.set_cookie(k,'',expires='Thu, 01-Jan-1970 00:00:00 GMT',path='/')
            except:
                pass
            session_name = app.config['SESSION_COOKIE_NAME']
            session_id = public.get_session_id()
            response.set_cookie(session_name,'',expires='Thu, 01-Jan-1970 00:00:00 GMT',path='/')
            response.set_cookie(session_name, session_id, path='/', max_age=86400 * 30,httponly=True)

            request_token = request.cookies.get('request_token','')
            if request_token:
                response.set_cookie('request_token',request_token,path='/',max_age=86400 * 30)
        
        if response.content_length is not None:
            if response.content_length < 512:
                if not session.get('login',None) or g.get('api_request',None):
                    import public
                    default_pl = "{}/default.pl".format(public.get_panel_path())
                    admin_path = "{}/data/admin_path.pl".format(public.get_panel_path())
                    default_body = public.readFile(default_pl,'rb')
                    admin_body = public.readFile(admin_path,'rb')
                    
                    if default_body or admin_body:
                        if not default_body: default_body = b""
                        if not admin_body: admin_body = b""
                        resp_body = response.get_data()

                        if default_body and resp_body.find(default_body.strip()) != -1: 
                            result = b'{"status":false,"msg":"Error: 403 Forbidden"}'
                            response.set_data(result)
                            response.headers['Content-Length'] = len(result)
                            return response
                        
                        if admin_body and resp_body.find(admin_body.strip()) != -1: 
                            result = b'{"status":false,"msg":"Error: 403 Forbidden"}'
                            response.set_data(result)
                            response.headers['Content-Length'] = len(result)
                            return response
                        
        
        if (response.mimetype not in app.config['COMPRESS_MIMETYPES'] or
            'gzip' not in accept_encoding.lower() or
            not 200 <= response.status_code < 300 or
            (response.content_length is not None and
             response.content_length < app.config['COMPRESS_MIN_SIZE']) or
            'Content-Encoding' in response.headers):
            return response

        response.direct_passthrough = False

        if self.cache:
            key = self.cache_key(response)
            gzip_content = self.cache.get(key) or self.compress(app, response)
            self.cache.set(key, gzip_content)
        else:
            gzip_content = self.compress(app, response)

        response.set_data(gzip_content)

        response.headers['Content-Encoding'] = 'gzip'
        response.headers['Content-Length'] = response.content_length

        vary = response.headers.get('Vary')
        if vary:
            if 'accept-encoding' not in vary.lower():
                response.headers['Vary'] = '{}, Accept-Encoding'.format(vary)
        else:
            response.headers['Vary'] = 'Accept-Encoding'

        return response

    def compress(self, app, response):
        gzip_buffer = BytesIO()
        with GzipFile(mode='wb',
                      compresslevel=app.config['COMPRESS_LEVEL'],
                      fileobj=gzip_buffer) as gzip_file:
            gzip_file.write(response.get_data())
        return gzip_buffer.getvalue()
