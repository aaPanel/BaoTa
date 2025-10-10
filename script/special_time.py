import datetime
import sys

# 从命令行参数获取特殊时间点
args = sys.argv[1:]
params = {}
for arg in args:
    key, value = arg.split('=')
    params[key] = value

special_times = params['special_time'].split(',')

# 获取当前的时间
current_time = datetime.datetime.now().strftime("%H:%M")

# 检查当前的时间是否在特殊时间点中
if current_time not in special_times:
    sys.exit(1)  # 如果不在，那么退出脚本
