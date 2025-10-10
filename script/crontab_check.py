import os
import subprocess
import time
import re
from datetime import datetime, timedelta
import sys

os.chdir('/www/server/panel')
if 'class/' not in sys.path:
    sys.path.insert(0, 'class/')
import public

try:
    import croniter
except:
    public.ExecShell("btpip install croniter")

# 用于记录任务失败次数和上次执行时间的文件路径
task_info_file = '{}/data/task_info.txt'.format(public.get_panel_path())
# 正则表达式用于匹配 syslog 和 ISO 8601 格式
syslog_regex = re.compile(r'^(?P<month>\w{3})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+\S+\s+')
iso_regex = re.compile(r'^(?P<datetime_iso>[\d\-T:\.]+)\+08:00')

# 读取任务失败次数和上次执行时间
def read_task_info():
    if not os.path.exists(task_info_file):
        return {}
    task_info = {}
    with open(task_info_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue  # 跳过空行
            try:
                task, count, time_str = line.split(':', 2)  # 使用 maxsplit 确保只分成三部分
                task_info[task] = {
                    'failure_count': int(count),
                    'last_execution_time': datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                }
            except ValueError as e:
                print("解析任务信息时出错: {}，跳过此行: {}".format(e, line))
                continue  # 如果解析失败，跳过该行
    return task_info

# 写入任务失败次数和上次执行时间
def write_task_info(task_info):
    with open(task_info_file, 'w') as f:
        for task, info in task_info.items():
            f.write("{}:{}:{}\n".format(task, info['failure_count'], info['last_execution_time'].strftime('%Y-%m-%d %H:%M:%S')))

# 获取计划任务文件位置
def get_cron_file():
    u_path = '/var/spool/cron/crontabs'
    u_file = u_path + '/root'
    c_file = '/var/spool/cron/root'
    cron_path = c_file
    if not os.path.exists(u_path):
        cron_path = c_file

    if os.path.exists("/usr/bin/apt-get"):
        cron_path = u_file
    elif os.path.exists('/usr/bin/yum'):
        cron_path = c_file

    if cron_path == u_file:
        if not os.path.exists(u_path):
            os.makedirs(u_path, 472)
            subprocess.run(["chown", "root:crontab", u_path])
    if not os.path.exists(cron_path):
        with open(cron_path, 'w') as f:
            f.write("")
    return cron_path

# 安装系统日志服务
def install_syslog_service():
    try:
        if os.path.exists('/usr/bin/apt-get'):
            subprocess.run(['apt-get', 'install', '-y', 'rsyslog'], check=True)
        elif os.path.exists('/usr/bin/yum'):
            subprocess.run(['yum', 'install', '-y', 'rsyslog'], check=True)
    except subprocess.CalledProcessError as e:
        print("安装系统日志服务失败: {}".format(e))

# 确保系统日志服务正在运行
def ensure_syslog_service_running():
    try:
        result = subprocess.run(['systemctl', 'status', 'rsyslog'], capture_output=True, text=True)
        if 'active (running)' not in result.stdout:
            subprocess.run(['systemctl', 'start', 'rsyslog'], check=True)
            print("系统日志服务已启动。")
            return False  # 刚启动服务，返回False
        else:
            return True  # 服务已经在运行
    except subprocess.CalledProcessError as e:
        print("启动系统日志服务失败: {}".format(e))
        return False

# 检查crontab服务状态
def check_service_status():
    service_name = 'crond'
    try:
        if os.path.exists('/usr/bin/apt-get'):
            service_name = 'cron'
        
        result = subprocess.run(['systemctl', 'status', service_name], capture_output=True, text=True)
        if 'active (running)' in result.stdout:
            print("Crontab服务正在运行。")
            return True
        else:
            print("Crontab服务未运行。")
            create_status_flag()
            return False
    except subprocess.CalledProcessError as e:
        print("检查crontab服务状态失败: {}".format(e))
        create_status_flag()
        return False

# 解析crontab任务
def parse_crontab(crontab_path):
    if not os.path.exists(crontab_path):
        print("找不到crontab文件: {}".format(crontab_path))
        create_status_flag()
        return []

    with open(crontab_path, 'r') as f:
        lines = f.readlines()

    cron_jobs = []
    error_line = False
    for line in lines:
        if line.strip() and not line.startswith('#'):
            parts = line.split()
            if parts[0] == '@reboot':
                print(parts)
                continue
            elif len(parts) < 6 or not is_valid_cron_time(parts[:5]):
                print("无效的crontab行: {}".format(line.strip()))
                error_line = True
                continue
            schedule = " ".join(parts[:5])
            command = " ".join(parts[5:])
            cron_jobs.append((schedule, command))
    if error_line:
        create_status_flag()
        return
    return cron_jobs

def is_valid_cron_time(parts):
    for part in parts:
        if part != '*' and not part.isdigit() and not (part.startswith('*/') and part[2:].isdigit()):
            return False
    return True

def next_execution_time(schedule):
    now = datetime.now()
    cron_iter = croniter.croniter(schedule, now)
    return cron_iter.get_next(datetime)

def previous_execution_time(schedule):
    now = datetime.now()
    cron_iter = croniter.croniter(schedule, now)
    return cron_iter.get_prev(datetime)

# 获取日志文件路径
def get_log_path():
    # 根据系统类型选择正确的日志文件路径
    if os.path.exists('/usr/bin/apt-get'):
        return '/var/log/syslog'  # Ubuntu/Debian 系列
    elif os.path.exists('/usr/bin/yum'):
        return '/var/log/cron'  # CentOS/RedHat 系列
    else:
        raise Exception("不支持的操作系统类型，无法确定日志文件路径")
    
# 检查任务日志并记录失败次数
def check_task_log(command, prev_execution_time, check_time=None):
        # 获取日志文件路径
    try:
        log_path = get_log_path()
    except Exception as e:
        print(e)
        return True, "无法确定日志文件路径，跳过检查"
    
    task_info = read_task_info()

    # 确保系统日志服务正在运行
    if not ensure_syslog_service_running():
        install_syslog_service()
        return True, "日志服务刚启动，跳过检查"

    # 如果日志文件不存在，尝试创建日志文件并重启日志服务
    if not os.path.exists(log_path):
        print("日志文件不存在，尝试创建...")
        try:
            with open(log_path, 'w') as f:
                f.write("")  # 创建空的日志文件
            subprocess.run(['systemctl', 'restart', 'rsyslog'], check=True)
            print("日志文件已创建并重启系统日志服务。")
        except Exception as e:
            print("日志文件创建或服务重启失败: {}".format(e))
        return True, "日志服务刚启动，跳过检查"

    # 如果 check_time 未指定，默认使用当前时间
    if check_time is None:
        check_time = datetime.now()

    # 获取日志文件的最早记录时间
    earliest_log_time = get_earliest_log_time(log_path)
    if earliest_log_time and earliest_log_time > check_time:
        return True, "日志最早记录时间 ({}) 晚于任务执行时间 ({})，日志可能不完整，跳过检查".format(earliest_log_time, check_time)

    # 计算一小时前的时间
    one_hour_ago = check_time - timedelta(hours=1)

    # 打开日志文件进行读取，只读取最后10MB
    log_size = os.path.getsize(log_path)
    bytes_to_read = min(10 * 1024 * 1024, log_size)  # 最多读取10MB
    with open(log_path, 'rb') as f:
        f.seek(-bytes_to_read, os.SEEK_END)
        log_lines = f.read().decode('utf-8').splitlines()

    if not log_lines:
        return True, "系统日志为空，跳过检查"
    
    # 检查上次执行时间是否不同
    if command in task_info and task_info[command]['last_execution_time'] == prev_execution_time:
        print("任务 '{}' 的上次执行时间与之前相同，跳过失败计数更新。".format(command))
        return True, "上次执行时间相同，跳过失败计数更新"

    # 遍历日志文件中的每一行
    for log_line in log_lines:
        if not log_line.strip():
            continue  # 跳过空行

        # 只处理包含目标命令的日志行
        if command not in log_line:
            continue

        log_time = parse_log_time(log_line)

        if not log_time or log_time < one_hour_ago:
            continue

        print("任务在 {} 成功执行".format(log_time))
        # 如果任务成功执行，将其失败次数重置为0，并更新上次执行时间
        task_info[command] = {
            'failure_count': 0,
            'last_execution_time': prev_execution_time
        }
        write_task_info(task_info)
        return True, "任务成功执行"

    # 如果日志中找不到匹配的命令，增加失败次数
    if command not in task_info:
        task_info[command] = {
            'failure_count': 0,
            'last_execution_time': prev_execution_time
        }

    # 增加失败次数并更新上次执行时间
    task_info[command]['failure_count'] += 1
    task_info[command]['last_execution_time'] = prev_execution_time
    write_task_info(task_info)

    # 如果某个任务失败次数达到3次
    if task_info[command]['failure_count'] >= 3:
        print("任务 '{}' 连续3次未执行。".format(command))
        create_status_flag()

    return False, "任务未按预定时间执行"

# 解析日志行中的时间戳
def parse_log_time(log_line):
    log_line = log_line.strip()  # 去除前后的空白字符
    if not log_line:
        print("日志行为空，跳过解析")
        return None

    print("正在解析日志行: {}".format(log_line))  # 显示非空日志行
    syslog_match = syslog_regex.match(log_line)
    if syslog_match:
        log_time_str = "{} {} {}".format(syslog_match.group('month'), syslog_match.group('day'), syslog_match.group('time'))
        try:
            log_time = datetime.strptime(log_time_str, '%b %d %H:%M:%S')
            log_time = log_time.replace(year=datetime.now().year)
            return log_time
        except ValueError as e:
            print("解析 syslog 时间格式时出错: {}".format(e))
    # 解析 ISO 8601 格式的时间戳
    iso_match = iso_regex.search(log_line)
    if iso_match:
        print("匹配到的时间戳: {}".format(iso_match.group('datetime_iso')))  # 添加匹配调试信息
        try:
            return datetime.fromisoformat(iso_match.group('datetime_iso'))
        except ValueError as e:
            print("解析 ISO 8601 时间格式时出错: {}".format(e))
    else:
        print("无法匹配时间戳: {}".format(log_line))

    return None

# 获取日志文件的最早记录时间
def get_earliest_log_time(log_path):
    try:
        with open(log_path, 'r') as f:
            log_lines = f.readlines()
        for log_line in log_lines:
            log_time = parse_log_time(log_line)
            if log_time:
                return log_time
    except Exception as e:
        print("获取日志最早时间时出错: {}".format(e))
    return None

def check_crontab_tasks(cron_jobs):
    now = datetime.now()
    executed_any_task = False
    for schedule, command in cron_jobs:
        prev_time = previous_execution_time(schedule)
        next_time = next_execution_time(schedule)

        print("下次执行时间: {}".format(next_time))
        print("上次执行时间: {}".format(prev_time))
        print("当前时间: {}".format(now))

        if prev_time <= now < next_time:
            status, message = check_task_log(command, prev_execution_time=prev_time, check_time=prev_time)
            if status:
                print("任务 '{}' 按预定时间执行。".format(command))
                executed_any_task = True
            else:
                print("任务 '{}' 未按预定时间执行。".format(command))
                create_status_flag()
                return 
        else:
            print("当前时间不在任务 '{}' 的执行周期内。".format(command))

    return executed_any_task

def create_status_flag():
    print("正在创建标记文件...")
    flag_path = '/tmp/crontab_service_status.flag'
    with open(flag_path, 'w') as f:
        f.write("0")
    print("创建标记文件: {}".format(flag_path))

def remove_status_flag():
    flag_path = '/tmp/crontab_service_status.flag'
    if os.path.exists(flag_path):
        os.remove(flag_path)
        print("删除标记文件: {}".format(flag_path))

def main():
    remove_status_flag()
    
    if not check_service_status():
        print("Crontab服务未运行或不健康。")
        return 
    
    crontab_path = get_cron_file()
    cron_jobs = parse_crontab(crontab_path)
    if not cron_jobs:
        print("未找到有效的crontab任务。")
        return 

    if check_crontab_tasks(cron_jobs):
        print("Crontab服务正常运行。")
        with open('/tmp/crontab_service_status.flag', 'w') as f:
            f.write("1")
    else:
        print("没有任务按预定时间执行。")
        print("Crontab服务可能有问题。")
        create_status_flag()

if __name__ == "__main__":
    main()
