import datetime
import os, sys

os.chdir('/www/server/panel/')
sys.path.insert(0, "class/")
sys.path.insert(0, "/www/server/panel/")
import public

def get_filter_time(hours=0):
    """返回当前时间减去指定小时数的datetime对象"""
    return datetime.datetime.now() - datetime.timedelta(hours=hours)

def get_ssh_log():
    if os.path.exists("/var/log/auth.log"):
        file_path = "/var/log/auth.log"
    else:
        file_path = "/var/log/secure"
    with open(file_path, 'r') as f:
        lines = f.readlines()
        if not lines:
            return []
        return lines

def parse_secure_log(filter_time=None):
    """解析SSH日志中'Failed password'的记录，并按filter_time过滤

    参数:
        filter_time (datetime, optional): 只返回此时间之后的记录

    返回:
        list: 包含[时间, IP, 端口, 用户名]的列表，时间为datetime对象，无效用户为None
    """
    result = {}
    year = datetime.datetime.now().year

    try:
        ssh_log = get_ssh_log()
        for line in ssh_log:
            line = line.strip()
            if 'Failed password' not in line:
                continue
            parts = line.split()
            if 'T' in parts[0]:
                # 解析ISO格式时间戳
                log_time = datetime.datetime.fromisoformat(parts[0].replace('Z', '+00:00')).replace(tzinfo=None)
                ip_index = parts.index('from') + 1
            else:
                # 解析传统格式时间
                month = parts[0]
                day = parts[1]
                time_str = parts[2]
                dt_str = "{} {} {} {}".format(month, day, year, time_str)
                log_time = datetime.datetime.strptime(dt_str, "%b %d %Y %H:%M:%S")
                ip_index = parts.index('from') + 1
            # 根据filter_time过滤
            if filter_time and log_time < filter_time:
                continue

            ip = parts[ip_index]
            result[ip] = result.get(ip, 0) + 1
    except FileNotFoundError:
        print("错误: 未找到ssh日志文件")
    except PermissionError:
        print("错误: 无权限读取ssh日志文件")
    except Exception as e:
        print("发生了点小错误:"+str(e))
    return result

if __name__ == "__main__":
    if len(sys.argv) < 3 :
        print("Usage: python script.py <past_hours> <failed_count> <ban_time>s")
        sys.exit(1)

    past_hours = int(sys.argv[1])
    failed_count = int(sys.argv[2])
    ban_time = int(sys.argv[3])
    filter_time = get_filter_time(past_hours)
    failed_attempts = parse_secure_log(filter_time)

    frequent_ips = [ip for ip, count in failed_attempts.items() if count > failed_count]

    from firewallModel.comModel import main as comModel
    commodel = comModel()
    for ip in frequent_ips:
        get = public.dict_obj()
        get['types'] = "drop"
        get['brief'] = "SSH爆破IP {}小时内失败{}次".format(past_hours,failed_attempts[ip])
        get['address'] = ip
        get['chain'] = "INPUT"
        get['family'] = "ipv4"
        get['operation'] = "add"
        get['strategy'] = "drop"
        get['timeout'] = ban_time
        commodel.set_ip_rule(get)
        print(ip,get['brief'])
    print("本次运行共封禁{}个IP 可在安全-IP规则中查看".format(len(frequent_ips)))
    print("程序运行结束...")