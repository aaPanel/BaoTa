# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http:#bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: sww <sww@bt.cn>
# -------------------------------------------------------------------

# ------------------------------
# shell脚本异常推送
# ------------------------------
import os, sys, re

panel_path = '/www/server/panel'
os.chdir(panel_path)
if not 'class/' in sys.path: sys.path.insert(0, 'class/')
import public


def get_cron_log(echo):
    log_path = "/www/server/cron/{}.log".format(echo)
    if not os.path.exists(log_path): return (False, "")
    logs = public.GetNumLines(log_path, 100)
    if len(re.findall(r"(★\[.*?\])", logs)) < 2 and not len(logs.split('\n')) < 100:
        logs = public.GetNumLines(log_path, 500)
    logs = logs.split('\n')
    logs.reverse()
    pattern = r"(★\[.*?\])"
    start = 0
    end = 0
    flag = 0
    for i in range(len(logs)):
        if re.findall(pattern, logs[i]):
            if flag == 0:
                start = i
                flag = 1
            else:
                end = i
                break
    if end == 0: end = -1
    logs = logs[start:end]
    if not logs: return (False, "")
    return (True, "\n".join(logs[start:end]))


def push_msg(echo, channel, keyword, name):
    data = get_cron_log(echo)
    if not data[0]: return
    data = data[1]
    if keyword:
        if keyword in data:
            data = public.get_push_info('计划任务shell告警', ["任务名称：{}".format(name),"告警关键词:{}".format(keyword)])
            send_msg(channel, data)


def send_msg(channels, data):
    for channel in channels.split(','):
        try:
            obj = public.init_msg(channel)
            obj.send_msg(data['msg'])
        except:
            pass


if __name__ == '__main__':
    echo = sys.argv[1]
    channel = sys.argv[2]
    keyword = sys.argv[3]
    name = sys.argv[4]
    print(echo, channel, keyword, name)
    push_msg(echo, channel, keyword, name)
