# -*- coding: utf-8 -*-

from werkzeug.routing import Map, Rule
from werkzeug.exceptions import NotFound
from werkzeug.http import parse_cookie
from flask import request


# Monkeys are made for freedom.
try:
    from geventwebsocket.gunicorn.workers import GeventWebSocketWorker as Worker
    from geventwebsocket.handler import WebSocketHandler
    from gunicorn.workers.ggevent import PyWSGIHandler

    import gevent
except ImportError:
    pass


class SocketMiddleware(object):

    def __init__(self, wsgi_app, app, socket):
        self.ws = socket
        self.app = app
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        adapter = self.ws.url_map.bind_to_environ(environ)
        try:
            handler, values = adapter.match()
            environment = environ['wsgi.websocket']
            cookie = None
            if 'HTTP_COOKIE' in environ:
                cookie = parse_cookie(environ['HTTP_COOKIE'])

            with self.app.app_context():
                with self.app.request_context(environ):
                    # add cookie to the request to have correct session handling
                    request.cookie = cookie

                    handler(environment, **values)
                    return []
        except (NotFound, KeyError):
            return self.wsgi_app(environ, start_response)


class Sockets(object):

    def __init__(self, app=None):
        #: Compatibility with 'Flask' application.
        #: The :class:`~werkzeug.routing.Map` for this instance. You can use
        #: this to change the routing converters after the class was created
        #: but before any routes are connected.
        self.url_map = Map()

        #: Compatibility with 'Flask' application.
        #: All the attached blueprints in a dictionary by name. Blueprints
        #: can be attached multiple times so this dictionary does not tell
        #: you how often they got attached.
        self.blueprints = {}
        self._blueprint_order = []

        if app:
            self.init_app(app)

    def init_app(self, app):
        app.wsgi_app = SocketMiddleware(app.wsgi_app, app, self)

    def route(self, rule, **options):

        def decorator(f):
            endpoint = options.pop('endpoint', None)
            self.add_url_rule(rule, endpoint, f, **options)
            return f
        return decorator

    def add_url_rule(self, rule, _, f, **options):
        self.url_map.add(Rule(rule, endpoint=f))

    def register_blueprint(self, blueprint, **options):
        """
        Registers a blueprint for web sockets like for 'Flask' application.

        Decorator :meth:`~flask.app.setupmethod` is not applied, because it
        requires ``debug`` and ``_got_first_request`` attributes to be defined.
        """
        first_registration = False

        if blueprint.name in self.blueprints:
            assert self.blueprints[blueprint.name] is blueprint, (
                'A blueprint\'s name collision occurred between %r and '
                '%r.  Both share the same name "%s".  Blueprints that '
                'are created on the fly need unique names.'
                % (blueprint, self.blueprints[blueprint.name], blueprint.name))
        else:
            self.blueprints[blueprint.name] = blueprint
            self._blueprint_order.append(blueprint)
            first_registration = True

        blueprint.register(self, options, first_registration)


# CLI sugar.
if ('Worker' in locals() and 'PyWSGIHandler' in locals() and
        'gevent' in locals()):

    class GunicornWebSocketHandler(PyWSGIHandler, WebSocketHandler):
        def log_request(self):
            if '101' not in self.status:
                super(GunicornWebSocketHandler, self).log_request()

    Worker.wsgi_handler = GunicornWebSocketHandler
    worker = Worker
