import sys
from gzip import GzipFile
from io import BytesIO

from flask import request, current_app


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
