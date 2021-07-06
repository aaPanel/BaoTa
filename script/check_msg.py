#coding: utf-8
import sys,os,time
os.chdir('/www/server/panel/')
sys.path.insert(0,"class/")
import public
import http_requests
http_requests.DEFAULT_TYPE = 'src'
os.environ['BT_TASK'] = '1'

import panelMessage
import re
msgObj = panelMessage.panelMessage()
data = msgObj.get_messages()
for x in data:
    if x['level'] in ['danger', 'error'] and not x['send'] and x['retry_num'] < 5:
        msg = '服务器IP【{}】: {}'.format(
            public.GetLocalIp(), re.sub('，?<a\s*.+</a>', '', x['msg']))
        is_send = False

        ret = public.return_is_send_info()
        for key in ret:
            if ret[key]:
                ret = public.send_body_words(key, '宝塔消息提醒', msg)
                if ret:
                    is_send = True
        pdata = {}
        if is_send:
            pdata['send'] = 1
            pdata['retry_num'] = 0
        else:
            pdata['send'] = 0
            pdata['retry_num'] = x['retry_num'] + 1

        msgObj.set_send_status(x['id'], pdata)
        time.sleep(5)