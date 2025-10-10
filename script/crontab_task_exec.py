#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# 任务编排调用脚本
#------------------------------
import sys
import os
import time
import json
os.chdir('/www/server/panel')
sys.path.insert(0, 'class/')
import PluginLoader
import public

args = public.dict_obj()

if len(sys.argv) < 2:
    print('错误: 未找到任务ID.')
    sys.exit()

args.trigger_id = int(sys.argv[1])
args.model_index = 'crontab'

# 获取任务信息
trigger_info = public.M('trigger').where('trigger_id=?', (args.trigger_id,)).find()
if not trigger_info:
    print('错误: 任务不存在.')
    sys.exit()

# 检查开始时间
start_time_str = trigger_info.get('start_time', '0')
if not start_time_str:
    start_time_str = '0'
try:
    start_time = float(start_time_str)
except ValueError:
    start_time = 0

current_timestamp = time.time()
if start_time > 0 and current_timestamp < start_time:
    print('错误: 任务尚未到开始执行时间.')
    sys.exit()

# 处理执行次数
exec_count = trigger_info.get('exec_count', 0)
count_file = '/www/server/panel/data/task_count.json'
task_counts = {}

if os.path.exists(count_file):
    with open(count_file, 'r') as f:
        task_counts = json.load(f)

current_count = task_counts.get(str(args.trigger_id), 0)
if int(exec_count) > 0 and current_count >= int(exec_count):
    print('已达到最大执行次数！任务执行失败！')
    sys.exit()

# 调用任务
res = PluginLoader.module_run('trigger', 'test_trigger', args)

# 更新执行次数
task_counts[str(args.trigger_id)] = current_count + 1
with open(count_file, 'w') as f:
    json.dump(task_counts, f)

if not res['status']:
    print(res['msg'])
    sys.exit()

print('任务执行成功.')
