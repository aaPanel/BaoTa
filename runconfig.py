import os,time,sys,ssl
sys.path.insert(0,'/www/server/panel/class')
import public
bt_port = public.readFile('data/port.pl')
if bt_port: bt_port.strip()
bind = []
if os.path.exists('data/ipv6.pl'): 
    bind.append('[0:0:0:0:0:0:0:0]:%s' % bt_port)
else:
    bind.append('0.0.0.0:%s' % bt_port)

w_num = 'data/workers.pl'
if not os.path.exists(w_num): public.writeFile(w_num,'1')
workers = int(public.readFile(w_num))
if not workers: workers = 1
threads = 1
backlog = 512
reload = False
daemon = True
timeout = 7200
keepalive = 60
preload_app = True
worker_class = 'geventwebsocket.gunicorn.workers.GeventWebSocketWorker'
chdir = '/www/server/panel'
capture_output = True
access_log_format = '%(h) -  %(t)s - %(u)s - %(s)s %(H)s'
errorlog = chdir + '/logs/error.log'
accesslog = chdir + '/logs/access.log'
pidfile = chdir + '/logs/panel.pid'
if os.path.exists(chdir + '/data/ssl.pl'):
    certfile = 'ssl/certificate.pem'
    keyfile  = 'ssl/privateKey.pem'
    ciphers = 'TLSv1 TLSv1.1 TLSv1.2'
    ssl_version = 2