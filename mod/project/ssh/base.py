import json
import os
import sys
from datetime import datetime

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

os.chdir("/www/server/panel")
import public


class SSHbase():
    def __init__(self):
        super().__init__()

    @staticmethod
    def return_area(result, key):
        """
        @name 格式化返回带IP归属地的数组
        @param result<list> 数据数组
        @param key<str> ip所在字段
        @return list
        """
        if not result:
            return result

        # 添加IP查询缓存
        ip_cache_file = 'data/ip_location_cache.json'
        ip_cache = {}

        # 确保缓存目录存在
        cache_dir = os.path.dirname(ip_cache_file)
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)

        # 读取IP缓存
        try:
            if os.path.exists(ip_cache_file):
                ip_cache = json.loads(public.readFile(ip_cache_file))
        except Exception as e:
            public.print_log('读取IP缓存失败: {}'.format(str(e)))
            ip_cache = {}

        # 只查询未缓存的IP
        new_ips = set()
        for data in result:
            ip = data.get(key)
            if not ip or public.is_ipv6(ip):
                continue
            if ip not in ip_cache:
                new_ips.add(ip)

        # 批量查询新IP
        for ip in new_ips:
            try:
                if "127.0.0" in ip:
                    ip_cache[ip] = {"info": "本机地址(例如左侧终端)"}
                    continue

                ip_area = public.get_ip_location(ip)
                if not ip_area:
                    ip_cache[ip] = {"info": "未知地区"}
                    continue

                # ip_area = ip_area.raw
                country = ip_area.get("country", {})
                ip_area["info"] = "{} {} {}".format(
                    country.get('country', '未知'),
                    country.get('province', '未知'),
                    country.get('city', '未知')
                ) if country else "未知地区"
                ip_cache[ip] = ip_area
            except Exception as e:
                public.print_log('查询IP {} 失败: {}'.format(ip, str(e)))
                ip_cache[ip] = {"info": "未知地区"}

        # 只有当有新IP被查询时才更新缓存文件
        if new_ips:
            try:
                public.writeFile(ip_cache_file, json.dumps(ip_cache))
            except Exception as e:
                public.print_log('更新IP缓存失败: {}'.format(str(e)))
                pass

        # 使用缓存数据，确保不修改原始数据
        result_with_area = []
        for data in result:
            data_copy = data.copy()  # 创建数据副本
            ip = data_copy.get(key, '')
            data_copy['area'] = ip_cache.get(ip, {"info": "未知地区"})
            result_with_area.append(data_copy)

        return result_with_area

    @staticmethod
    def journalctl_system():
        try:
            if os.path.exists('/etc/os-release'):
                f = public.readFile('/etc/os-release')
                f = f.split('\n')
                ID = ''
                VERSION_ID = 0
                for line in f:
                    if line.startswith('VERSION_ID'):
                        VERSION_ID = int(line.split('=')[1].split('.')[0].strip('"'))
                    if line.startswith('ID'):
                        if ID != '': continue
                        ID = line.strip().split('=')[1].strip('"')
                        try:
                            ID = ID.split('.')[0]
                        except:
                            pass
                if (ID.lower() == 'debian' and VERSION_ID >= 11) or (ID.lower() == 'ubuntu' and VERSION_ID >= 20):
                    return True
                return False
        except:
            return False

    @staticmethod
    def parse_login_entry(parts, year):
        """解析登录条目"""
        try:
            # 判断日志格式类型
            if 'T' in parts[0]:  # centos7以外的格式
                # 解析ISO格式时间戳
                dt = datetime.fromisoformat(parts[0].replace('Z', '+00:00'))
                user_index = parts.index('user') + 1 if 'user' in parts else parts.index('for') + 1
                ip_index = parts.index('from') + 1
                port_index = parts.index('port') + 1 if 'port' in parts else -1
            else:
                # 解析传统格式时间
                month = parts[0]
                day = parts[1]
                time_str = parts[2]
                # 如果月份大于当前月，说明年份不对，直接把year修改成1970年
                if datetime.strptime("{} {}".format(month, day), "%b %d").month > datetime.now().month:
                    year = "1970"
                dt_str = "{} {} {} {}".format(month, day, year, time_str)
                dt = datetime.strptime(dt_str, "%b %d %Y %H:%M:%S")
                user_index = parts.index('for') + 1 if "invalid" not in parts else -6
                ip_index = parts.index('from') + 1
                port_index = parts.index('port') + 1 if 'port' in parts else -1

            entry = {
                "timestamp": int(dt.timestamp()),
                "time": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "type": "success" if ("Accepted" in parts) else "failed",
                "status": 1 if ("Accepted" in parts) else 0,
                "user": parts[user_index],
                "address": parts[ip_index],
                "port": parts[port_index] if port_index != -1 else "",
                "deny_status": 0,
                "login_type": "publickey" if "publickey" in parts else "password"  # 添加登录类型
            }
            return entry
        except Exception as e:
            public.print_log(public.get_error_info())
            return None
