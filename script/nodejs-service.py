#!/www/server/panel/pyenv/bin/python
#coding: utf-8
import os,sys
os.chdir("/www/server/panel")
sys.path.insert(0,"class/")

from projectModel.nodejsModel import main
import public
p = main()

if len(sys.argv) < 3:
    print("Usage: nodejs-service [project_name] [start|stop|restart]")
    sys.exit()
get = public.dict_obj()
get.project_name = sys.argv[1].strip()
action = sys.argv[2].strip()
if action not in ['start','stop','restart','status']:
    print("Usage: nodejs-service [project_name] [start|stop|restart]")
    sys.exit()

if action == 'start':
    res = p.start_project(get)
elif action == 'stop':
    res = p.stop_project(get)
elif action == 'restart':
    res = p.restart_project(get)
elif action == 'status':
    res = p.get(get)

if res['status']:
    print("\033[1;32mSUCCESS: " + res['data'] + "\033[0m")
else:
    print("\033[1;31mERROR: " + res['error_msg'] + "\033[0m")


