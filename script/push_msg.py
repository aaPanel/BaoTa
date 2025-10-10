#coding: utf-8
import sys,os,time
os.chdir('/www/server/panel/')
sys.path.insert(0, "class/")
sys.path.insert(0, "/www/server/panel/")
import http_requests
import traceback
http_requests.DEFAULT_TYPE = 'src'
os.environ['BT_TASK'] = '1'

try:
    import panelPush
    import threading
    push = panelPush.panelPush()
    push.start()

    from mod.base.push_mod import PushSystem

    PushSystem().run()

    # os.system("echo yes,{} > /tmp/push.pl".format(time.time()))
except Exception as e:
    traceback.print_exc()
    # print("开启推送消息进程异常。")
    with open('/tmp/push.pl', 'w') as f:
        f.write(str(int(time.time())))
        f.write("{}".format(traceback.format_exc()))
