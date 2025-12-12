#coding: utf-8
import os
import sys
import json
import datetime
import time
import psutil
import traceback

os.chdir('/www/server/panel')
sys.path.insert(0,'class/')
import panelWarning
import public

for i in psutil.pids():
    try:
        if i == os.getpid():
            continue
        p = psutil.Process(i)
        is_python = False
        cmdline = p.cmdline()
    except:
        traceback.print_exc()
        continue

    for cmd_split in cmdline:
        if cmd_split.find('python') > 0:
            is_python = True
        if is_python and cmd_split.find('warning_list.py') > 0:
            print("当前有正在执行的风险扫描任务，请稍后再试")
            exit(0)


run_tip_file = "/www/server/panel/data/warning_list_runtime.pl"
last_run_time = 0
if os.path.exists(run_tip_file):
    try:
        last_run_time = int(public.readFile(run_tip_file))
    except:
        last_run_time = 0

today = int(datetime.datetime.now().replace(hour=0, minute=0, second=0).timestamp())
if last_run_time > 0 and last_run_time > today:
    print("今日的风险扫描任务已执行，跳过本次执行")
    exit(0)
else:
    public.writeFile(run_tip_file, str(int(time.time())))

try:
    args = public.dict_obj()
    result = panelWarning.panelWarning().get_list(args)
    # 从结果中获取得分
    score = result.get('score', 100)  # 如果没有score字段，默认为0

    # 输出格式化的结果
    print("首页风险扫描结束,当前服务器得分:{},请在首页查看".format(score))
    # print(json.dumps(result))  # 保留原有的JSON输出，以防其他程序需要解析
except Exception as e:
    print(traceback.format_exc())