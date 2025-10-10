import datetime
import sys

# 从命令行参数获取 special_time 和 time_type
args = sys.argv[1:]
params = {}
for arg in args:
    key, value = arg.split('=')
    params[key] = value

time_type = params['time_type']
special_time = params['special_time'].split(',')

# 获取当前的时间
current_time = datetime.datetime.now().strftime("%H:%M")

# 如果用户提供了 time_list，那么使用它，否则使用所有可能的天数
if 'time_list' in params:
    time_list = list(map(int, params['time_list'].split(',')))
else:
    if time_type == "smonth":
        time_list = list(range(1, 32))  # 所有月份的天数
    elif time_type == "sweek":
        time_list = list(range(1, 8))  # 所有星期的天数

if time_type == "smonth":
    # 获取当前是一个月中的第几天
    current_date = datetime.datetime.today().day
    # 检查当前的日期是否在 time_list 中，且当前的时间是否在 special_time 中
    if current_date not in time_list or current_time not in special_time:
        sys.exit(1)  # 如果不在，那么退出脚本
elif time_type == "sweek":
    # 获取当前是一周中的第几天（星期一为1，星期日为7）
    current_weekday = datetime.datetime.today().isoweekday()
    # 检查当前的日期是否在 time_list 中，且当前的时间是否在 special_time 中
    if current_weekday not in time_list or current_time not in special_time:
        sys.exit(1)  # 如果不在，那么退出脚本
elif time_type == "sday":
    # 检查当前的时间是否在 special_time 中
    if current_time not in special_time:
        sys.exit(1)  # 如果不在，那么退出脚本
else:
    print("time_type类型不对")
    sys.exit(1)  # 如果不在，那么退出脚本

