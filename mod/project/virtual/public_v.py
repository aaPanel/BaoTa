import json
import time

from public import *

def lang(content,*args):
    return content

def return_message(status, types, message, args=(), play="", requests=()):
    """
        @name 统一请求响应函数
        @author hezhihong
        @param status  返回状态
        @param message  返回消息
        @return dict  {"status":0/-1,"message":any}/下载对象
    """
    from flask import g
    g.return_message = True
    # 非文件下载
    if types == 0:
        return_message = {'status': status, "timestamp": int(time.time()), "message": {}}
        try:
            log_message = json.loads(ReadFile('BTPanel/static/language/' + GetLanguage() + '/public.json'))
        except:
            log_message = {}
        keys = log_message.keys()
        if type(message) == str:
            if message in keys:
                message = log_message[message]
                for i in range(len(args)):
                    rep = '{' + str(i + 1) + '}'
                    message = message.replace(rep, args[i])
            # # 从语言包查询字符串
            # if message != "":
            #     message = gettext_msg2(message)
            return_message["message"]["result"] = message
        elif type(message) == int:
            return_message["message"]["result"] = message
        elif type(message) == bool:
            return_message["message"]["result"] = message
        elif type(message) == float:
            return_message["message"]["result"] = message
        elif type(message) == dict:
            return_message["message"] = message
        elif type(message) == list:
            return_message["message"] = message
        elif type(message) == tuple:
            return_message["message"] = message
        else:
            try:
                return_message["message"] = message
            except:
                return_message["message"] = {}
        return return_message
    # # 文件下载
    # elif types == 1:
    #     # from flask import requests as requests
    #     if play == 'true':
    #         import panelVideo
    #         # start, end = panelVideo.get_range(requests)
    #         # return panelVideo.partial_response(filename, start, end)
    #     else:
    #         mimetype = "application/octet-stream"
    #         extName = filename.split('.')[-1]
    #         if extName in ['png', 'gif', 'jpeg', 'jpg']: mimetype = None
    #         public.WriteLog("TYPE_FILE", 'FILE_DOWNLOAD',
    #                         (filename, public.GetClientIp()))
    #         return send_file(filename,
    #                          mimetype=mimetype,
    #                          as_attachment=True,
    #                          etag=True,
    #                          conditional=True,
    #                          download_name=os.path.basename(filename),
    #                          max_age=0)

    # html响应对象
    elif types == 2:
        return_message = {'status': status, "timestamp": int(time.time()), "message": {}}
        if type(message) == str:
            return_message["message"]["result"] = message
        return return_message