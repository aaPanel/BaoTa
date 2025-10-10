import os
f = open('data/port.pl','r')
bt_port = f.read()
f.close()
if bt_port:
    bt_port.strip()
else:
    bt_port = 8888
bind = []
if os.path.exists('data/ipv6.pl'):
    bind.append('[0:0:0:0:0:0:0:0]:%s' % bt_port)
else:
    bind.append('0.0.0.0:%s' % bt_port)

w_num = 'data/workers.pl'
workers = 1
if os.path.exists(w_num):
    f = open(w_num,'r')
    w_str = f.read()
    f.close()
    if w_str:
        workers = int(w_str.strip())

threads = 3
backlog = 512
daemon = True
timeout = 7200
keepalive = 60
debug = os.path.exists('data/debug.pl')
reload = debug
preload_app = not debug
worker_class = 'geventwebsocket.gunicorn.workers.GeventWebSocketWorker'
chdir = '/www/server/panel'
capture_output = True
graceful_timeout=0
loglevel = 'info'
if debug: loglevel = 'debug'
errorlog = chdir + '/logs/error.log'
accesslog = chdir + '/logs/error.log'
pidfile = chdir + '/logs/panel.pid'
if os.path.exists(chdir + '/data/ssl.pl'):
    certfile = 'ssl/certificate.pem'
    keyfile  = 'ssl/privateKey.pem'
    ciphers = 'TLSv1 TLSv1.1 TLSv1.2'
    ssl_version = 2