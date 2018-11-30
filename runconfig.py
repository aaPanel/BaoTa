import os,time,sys
sys.path.append('/www/server/panel/class')
import public
bt_port = public.readFile('data/port.pl')
if bt_port: bt_port.strip()
bind = ['0.0.0.0:%s' % bt_port]
workers = 1
threads = 1
backlog = 512
reload = False
daemon = True
timeout = 7200
keepalive = 1
preload_app = True
worker_class = 'geventwebsocket.gunicorn.workers.GeventWebSocketWorker'
chdir = '/www/server/panel'
capture_output = True
access_log_format = '%(t)s %(p)s %(h)s "%(r)s" %(s)s %(L)s %(b)s %(f)s" "%(a)s"'
loglevel = 'info'
errorlog = chdir + '/logs/error.log'
accesslog = chdir + '/logs/access.log'
pidfile = chdir + '/logs/panel.pid'
if os.path.exists(chdir + '/data/ssl.pl'):
    certfile = 'ssl/certificate.pem'
    keyfile  = 'ssl/privateKey.pem'