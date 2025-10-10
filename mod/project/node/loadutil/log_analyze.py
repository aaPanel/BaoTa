import os
import time
import json
import traceback
import datetime
import shutil
import math
from typing import Dict, List, Optional, Tuple, Union
from collections import defaultdict
import csv
import fcntl
from .nginx_utils import NginxUtils

_LOG_PATH = "/www/wwwlogs/load_balancing/logs/"
_TCP_LOG_PATH = "/www/wwwlogs/load_balancing/tcp_logs/"
_STATUS_CACHE_PATH = "/www/wwwlogs/load_balancing/cache/"


class LogAnalyzer:
    table_header = (
        "time", "remote_addr", "host", "request_method", "request_uri", "upstream_addr",
        "upstream_response_time", "upstream_bytes_received", "upstream_status", "upstream_cache_status",
        "request_time", "body_bytes_sent", "bytes_sent", "status", "user_agent", "referer",
        "x_forwarded_for", "x_real_ip")

    def __init__(self, log_path: str, stats_dir: str, interval: int = 300):
        """
        初始化日志分析器
        :param log_path: 日志文件路径
        :param stats_dir: 统计数据存储目录
        :param interval: 统计间隔（秒）
        """
        self.log_path = log_path
        self.stats_dir = stats_dir
        self.interval = interval
        self.lock_file = os.path.join(stats_dir, '.lock')
        self.stats_file = os.path.join(stats_dir, 'stats.json')
        self.last_position_file = os.path.join(stats_dir, 'last_position.json')
        self.last_stats_file = os.path.join(stats_dir, 'last_stats.json')

        # 创建统计目录
        os.makedirs(stats_dir, exist_ok=True)

        # 初始化统计数据
        self.stats = {
            'total': self._init_node_stats(),
            'nodes': defaultdict(self._init_node_stats)
        }

        # 加载上次统计位置和统计数据
        self.last_position = self._load_last_position()
        self.last_stats = self._load_last_stats()

    def _init_node_stats(self) -> Dict:
        """初始化节点统计数据"""
        return {
            'requests': 0,
            'errors': 0,
            'max_response_time': 0,
            'max_upstream_time': 0,
            'last_update': 0,
            'qps': 0
        }

    def _load_last_position(self) -> Dict:
        """加载上次统计位置"""
        if os.path.exists(self.last_position_file):
            with open(self.last_position_file, 'r') as f:
                return json.load(f)
        return {'position': 0, 'last_stats_time': 0, 'current_date': datetime.datetime.now().strftime('%Y-%m-%d')}

    def _load_last_stats(self) -> Dict:
        """加载上次统计数据"""
        if os.path.exists(self.last_stats_file):
            with open(self.last_stats_file, 'r') as f:
                return json.load(f)
        return {
            'total': self._init_node_stats(),
            'nodes': defaultdict(self._init_node_stats)
        }

    def _save_last_position(self):
        """保存统计位置"""
        with open(self.last_position_file, 'w') as f:
            json.dump(self.last_position, f)

    def _save_last_stats(self):
        """保存上次统计数据"""
        with open(self.last_stats_file, 'w') as f:
            json.dump(self.last_stats, f)

    def _acquire_lock(self) -> bool:
        """获取文件锁"""
        try:
            self.lock_fd = open(self.lock_file, 'w')
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except IOError:
            if hasattr(self, 'lock_fd'):
                self.lock_fd.close()
            return False

    def _release_lock(self):
        """释放文件锁"""
        try:
            if hasattr(self, 'lock_fd'):
                fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
                self.lock_fd.close()
                if os.path.exists(self.lock_file):
                    os.remove(self.lock_file)
        except Exception as e:
            print(f"释放锁时发生错误: {str(e)}")

    def _parse_log_line(self, fields: List[str]) -> Optional[Dict]:
        """解析日志行"""
        try:
            # print(fields)
            # print(self.table_header)
            if len(fields) < len(self.table_header):  # 根据新的日志格式调整
                return None

            upstream_addrs = [x.strip() for x in fields[5].split(',')]
            try:
                upstream_response_times = [float(x) for x in fields[6].split(',') if x.strip() != '-']
            except ValueError:
                upstream_response_times = [0] * len(upstream_addrs)
            upstream_response_times.append(0)

            return {
                'time': fields[0],
                'upstream_addr': fields[5][0],
                'upstream_response_time': max(upstream_response_times),
                'status': int(fields[13]),
                'request_time': float(fields[10]),
                'timestamp': time.mktime(datetime.datetime.strptime(fields[0], '%d/%b/%Y:%H:%M:%S %z').timetuple())
            }
        except (ValueError, IndexError):
            traceback.print_exc()
            return None

    def _update_stats(self, log_data: Dict):
        """更新统计数据"""
        # 更新总统计
        self._update_node_stats(self.stats['total'], log_data)

        # 更新节点统计
        node = log_data['upstream_addr']
        self._update_node_stats(self.stats['nodes'][node], log_data)

    def _update_node_stats(self, stats: Dict, log_data: Dict):
        """更新节点统计数据"""
        stats['requests'] += 1

        if log_data['status'] >= 500:
            stats['errors'] += 1

        stats['max_response_time'] = max(stats['max_response_time'], log_data['request_time'])
        stats['max_upstream_time'] = max(stats['max_upstream_time'], log_data['upstream_response_time'])
        stats['last_update'] = log_data['timestamp']

    def _calculate_qps(self, current_stats: Dict, last_stats: Dict) -> float:
        """计算 QPS"""
        time_diff = current_stats['last_update'] - last_stats['last_update']
        if time_diff <= 0:
            return 0
        request_diff = current_stats['requests'] - last_stats['requests']
        if request_diff <= 0:
            return 0
        return min(math.ceil(request_diff / time_diff), 1)

    def _check_date_change(self):
        """检查日期是否变化"""
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        if current_date != self.last_position['current_date']:
            # 重命名日志文件
            old_log_path = self.log_path
            new_log_path = f"{self.log_path}.{self.last_position['current_date']}.csv"
            shutil.move(old_log_path, new_log_path)

            # 重载 Nginx 配置
            NginxUtils.reload_nginx()

            # 重置统计数据
            self._reset_stats_without_lock()

            # 更新当前日期
            self.last_position['current_date'] = current_date
            self._save_last_position()
            return True
        return False

    def _reset_stats_without_lock(self):
        """重置统计数据（不获取锁）"""
        self.stats = {
            'total': self._init_node_stats(),
            'nodes': defaultdict(self._init_node_stats)
        }
        self.last_stats = self.stats.copy()
        self._save_stats()
        self._save_last_stats()
        self.last_position = {
            'position': 0,
            'last_stats_time': 0,
            'current_date': datetime.datetime.now().strftime('%Y-%m-%d')
        }
        self._save_last_position()

    def _save_stats(self):
        """保存统计数据"""
        with open(self.stats_file, 'w') as f:
            json.dump(self.stats, f)

    def analyze_logs(self):
        """分析日志文件"""
        if not self._acquire_lock():
            print("另一个统计进程正在运行")
            return

        try:
            print("开始分析日志文件...")
            current_time = time.time()

            # 检查日期变化
            if self._check_date_change():
                return

            if current_time - self.last_position['last_stats_time'] < self.interval:
                return

            # 累积上次统计数据
            self.stats['total']['requests'] = self.last_stats['total']['requests']
            self.stats['total']['errors'] = self.last_stats['total']['errors']
            self.stats['total']['max_response_time'] = self.last_stats['total']['max_response_time']
            self.stats['total']['max_upstream_time'] = self.last_stats['total']['max_upstream_time']

            # 累积节点统计数据
            for node, node_stats in self.last_stats['nodes'].items():
                if node not in self.stats['nodes']:
                    self.stats['nodes'][node] = self._init_node_stats()
                self.stats['nodes'][node]['requests'] = node_stats['requests']
                self.stats['nodes'][node]['errors'] = node_stats['errors']
                self.stats['nodes'][node]['max_response_time'] = node_stats['max_response_time']
                self.stats['nodes'][node]['max_upstream_time'] = node_stats['max_upstream_time']

            with open(self.log_path, 'r') as f:
                f.seek(self.last_position['position'])

                for line in csv.reader(f):
                    log_data = self._parse_log_line(line)
                    if log_data:
                        self._update_stats(log_data)

                # 计算 QPS
                for node in self.stats['nodes']:
                    last_node_stats = self.last_stats['nodes'].get(node, self._init_node_stats())
                    self.stats['nodes'][node]['qps'] = self._calculate_qps(
                        self.stats['nodes'][node],
                        last_node_stats
                    )
                self.stats['total']['qps'] = self._calculate_qps(
                    self.stats['total'],
                    self.last_stats['total']
                )

                # 保存当前统计数据作为下次计算的基准
                self.last_stats = self.stats.copy()
                self._save_last_stats()

                self.last_position['position'] = f.tell()
                self.last_position['last_stats_time'] = current_time

                self._save_stats()
                self._save_last_position()
        except Exception as e:
            print("错误:" + traceback.format_exc())
        finally:
            self._release_lock()

    def get_today_stats(self) -> Dict:
        """获取今日统计数据"""
        if not os.path.exists(self.stats_file):
            return self.stats

        with open(self.stats_file, 'r') as f:
            return json.load(f)

    def get_node_stats(self, node: str) -> Dict:
        """获取指定节点的统计数据"""
        stats = self.get_today_stats()
        return stats['nodes'].get(node, self._init_node_stats())

    def get_total_stats(self) -> Dict:
        """获取总体统计数据"""
        stats = self.get_today_stats()
        return stats['total']

    def reset_stats(self):
        """重置统计数据（带锁）"""
        if not self._acquire_lock():
            print("另一个统计进程正在运行")
            return

        try:
            self._reset_stats_without_lock()
        finally:
            self._release_lock()

    def get_log(self, position: int = -1, limit: int = 16) -> Tuple[int, List[Dict]]:
        """
        获取日志
        :param position: 上次读取的位置，-1 表示从文件末尾开始
        :param limit: 返回的条数
        :return: (新的位置, 日志列表)
        """
        if not os.path.exists(self.log_path) or os.path.getsize(self.log_path) == 0:
            return 0, []

        try:
            # 定义日志字段
            with open(self.log_path, 'rb') as f:
                # 获取文件大小
                f.seek(0, os.SEEK_END)
                file_size = f.tell()
                if position > file_size:
                    position = file_size

                # 确定起始位置
                if position == -1:
                    position = file_size

                # 计算需要读取的起始位置
                # 每条日志约236字节，考虑URI和X-Forwarded-For的扩展，使用1024字节作为单条日志的估算值
                read_size = min(limit * 1024, position)
                start_position = max(0, position - read_size)

                # 移动到起始位置
                f.seek(start_position)

                # 读取并解析日志
                logs = []
                current_position = start_position

                # 读取文件内容
                content = f.read(read_size)
                # 按行分割
                lines = content.splitlines()

                for line in lines:
                    if not line.strip():
                        continue

                    # 解析CSV行
                    try:
                        fields = next(csv.reader([line.decode()]))
                    except StopIteration:
                        continue

                    if len(fields) < len(self.table_header):
                        continue

                    # 只处理到目标位置之前的日志
                    if current_position + len(line) + 1 > position:
                        break

                    # 解析日志行
                    log_data = dict(zip(self.table_header, fields[:len(self.table_header)]))
                    logs.append((current_position, log_data))

                    # 更新当前位置
                    current_position += len(line) + 1  # +1 for newline

                # 如果没有找到日志，返回原始位置
                if not logs:
                    return start_position, []

                res_position = 0 if len(logs) <= limit and start_position == 0 else logs[-limit][0]

                # 取最后 limit 条记录并反转顺序（最新的在前）
                logs = logs[-limit:][::-1]

                # 返回最后一条日志的位置和解析后的日志列表
                return res_position, [log[1] for log in logs]

        except Exception as e:
            print(f"读取日志时发生错误: {str(e)}")
            return position, []


class TcpLogAnalyzer:
    table_header = (
        "time_local", "remote_addr", "protocol", "status", "bytes_sent", "bytes_received",
        "session_time", "upstream_addr", "upstream_bytes_sent", "upstream_bytes_received",
        "upstream_connect_time"
    )

    def __init__(self, log_path: str, stats_dir: str, interval: int = 300):
        """
        初始化TCP日志分析器
        :param log_path: 日志文件路径
        :param stats_dir: 统计数据存储目录
        :param interval: 统计间隔（秒）
        """
        self.log_path = log_path
        self.stats_dir = stats_dir
        self.interval = interval
        self.lock_file = os.path.join(stats_dir, '.lock')
        self.stats_file = os.path.join(stats_dir, 'stats.json')
        self.last_position_file = os.path.join(stats_dir, 'last_position.json')
        self.last_stats_file = os.path.join(stats_dir, 'last_stats.json')

        # 创建统计目录
        os.makedirs(stats_dir, exist_ok=True)

        # 初始化统计数据
        self.stats = {
            'total': self._init_node_stats(),
            'nodes': defaultdict(self._init_node_stats)
        }

        # 加载上次统计位置和统计数据
        self.last_position = self._load_last_position()
        self.last_stats = self._load_last_stats()

    def _init_node_stats(self) -> Dict:
        """初始化节点统计数据"""
        return {
            'requests': 0,
            'errors': 0,
            'max_response_time': 0,
            'max_upstream_time': 0,
            'last_update': 0,
            'qps': 0
        }

    def _load_last_position(self) -> Dict:
        """加载上次统计位置"""
        if os.path.exists(self.last_position_file):
            with open(self.last_position_file, 'r') as f:
                return json.load(f)
        return {'position': 0, 'last_stats_time': 0, 'current_date': datetime.datetime.now().strftime('%Y-%m-%d')}

    def _load_last_stats(self) -> Dict:
        """加载上次统计数据"""
        if os.path.exists(self.last_stats_file):
            with open(self.last_stats_file, 'r') as f:
                return json.load(f)
        return {
            'total': self._init_node_stats(),
            'nodes': defaultdict(self._init_node_stats)
        }

    def _save_last_position(self):
        """保存统计位置"""
        with open(self.last_position_file, 'w') as f:
            json.dump(self.last_position, f)

    def _save_last_stats(self):
        """保存上次统计数据"""
        with open(self.last_stats_file, 'w') as f:
            json.dump(self.last_stats, f)

    def _acquire_lock(self) -> bool:
        """获取文件锁"""
        try:
            self.lock_fd = open(self.lock_file, 'w')
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except IOError:
            if hasattr(self, 'lock_fd'):
                self.lock_fd.close()
            return False

    def _release_lock(self):
        """释放文件锁"""
        try:
            if hasattr(self, 'lock_fd'):
                fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
                self.lock_fd.close()
                if os.path.exists(self.lock_file):
                    os.remove(self.lock_file)
        except Exception as e:
            print(f"释放锁时发生错误: {str(e)}")

    def _parse_log_line(self, fields: List[str]) -> Optional[Dict]:
        """解析TCP日志行"""
        try:
            if len(fields) < len(self.table_header):
                return None

            # 解析上游服务器地址列表
            upstream_addrs = [addr.strip() for addr in fields[7].strip('"').split(',')]

            # 解析上游连接时间列表
            upstream_connect_times = []
            for t in fields[10].strip('"').split(','):
                try:
                    upstream_connect_times.append(float(t.strip()) if t.strip() != '-' else 0)
                except ValueError:
                    upstream_connect_times.append(0)

            return {
                'time': fields[0],
                'upstream_addrs': upstream_addrs,
                'upstream_connect_times': upstream_connect_times,
                'status': int(fields[3]),
                'session_time': float(fields[6]),
                'timestamp': time.mktime(datetime.datetime.strptime(fields[0], '%d/%b/%Y:%H:%M:%S %z').timetuple())
            }
        except (ValueError, IndexError):
            traceback.print_exc()
            return None

    def _update_stats(self, log_data: Dict):
        """更新统计数据"""
        # 更新总统计
        self._update_node_stats(self.stats['total'], {
            'status': log_data['status'],
            'session_time': log_data['session_time'],
            'timestamp': log_data['timestamp'],
            'upstream_connect_time': max(log_data['upstream_connect_times'])
        })

        # 更新节点统计
        for i, node in enumerate(log_data['upstream_addrs']):
            if i < len(log_data['upstream_connect_times']):
                self._update_node_stats(self.stats['nodes'][node], {
                    'status': log_data['status'],
                    'session_time': log_data['session_time'],
                    'upstream_connect_time': log_data['upstream_connect_times'][i],
                    'timestamp': log_data['timestamp']
                })

    def _update_node_stats(self, stats: Dict, log_data: Dict):
        """更新节点统计数据"""
        stats['requests'] += 1

        if log_data['status'] != 200:
            stats['errors'] += 1

        stats['max_response_time'] = max(stats['max_response_time'], log_data['session_time'])
        stats['max_upstream_time'] = max(stats['max_upstream_time'], log_data.get('upstream_connect_time', 0))
        stats['last_update'] = log_data['timestamp']

    def _calculate_qps(self, current_stats: Dict, last_stats: Dict) -> float:
        """计算 QPS"""
        time_diff = current_stats['last_update'] - last_stats['last_update']
        if time_diff <= 0:
            return 0
        request_diff = current_stats['requests'] - last_stats['requests']
        if request_diff <= 0:
            return 0
        return min(math.ceil(request_diff / time_diff), 1)

    def _check_date_change(self):
        """检查日期是否变化"""
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        if current_date != self.last_position['current_date']:
            # 重命名日志文件
            old_log_path = self.log_path
            new_log_path = f"{self.log_path}.{self.last_position['current_date']}.csv"
            shutil.move(old_log_path, new_log_path)

            # 重载 Nginx 配置
            NginxUtils.reload_nginx()

            # 重置统计数据
            self._reset_stats_without_lock()

            # 更新当前日期
            self.last_position['current_date'] = current_date
            self._save_last_position()
            return True
        return False

    def _reset_stats_without_lock(self):
        """重置统计数据（不获取锁）"""
        self.stats = {
            'total': self._init_node_stats(),
            'nodes': defaultdict(self._init_node_stats)
        }
        self.last_stats = self.stats.copy()
        self._save_stats()
        self._save_last_stats()
        self.last_position = {
            'position': 0,
            'last_stats_time': 0,
            'current_date': datetime.datetime.now().strftime('%Y-%m-%d')
        }
        self._save_last_position()

    def _save_stats(self):
        """保存统计数据"""
        with open(self.stats_file, 'w') as f:
            json.dump(self.stats, f)

    def analyze_logs(self):
        """分析日志文件"""
        if not self._acquire_lock():
            print("另一个统计进程正在运行")
            return

        try:
            print("开始分析日志文件...")
            current_time = time.time()

            # 检查日期变化
            if self._check_date_change():
                return

            if current_time - self.last_position['last_stats_time'] < self.interval:
                return

            # 累积上次统计数据
            self.stats['total']['requests'] = self.last_stats['total']['requests']
            self.stats['total']['errors'] = self.last_stats['total']['errors']
            self.stats['total']['max_response_time'] = self.last_stats['total']['max_response_time']
            self.stats['total']['max_upstream_time'] = self.last_stats['total']['max_upstream_time']

            # 累积节点统计数据
            for node, node_stats in self.last_stats['nodes'].items():
                if node not in self.stats['nodes']:
                    self.stats['nodes'][node] = self._init_node_stats()
                self.stats['nodes'][node]['requests'] = node_stats['requests']
                self.stats['nodes'][node]['errors'] = node_stats['errors']
                self.stats['nodes'][node]['max_response_time'] = node_stats['max_response_time']
                self.stats['nodes'][node]['max_upstream_time'] = node_stats['max_upstream_time']

            with open(self.log_path, 'r') as f:
                f.seek(self.last_position['position'])

                for line in csv.reader(f):
                    log_data = self._parse_log_line(line)
                    if log_data:
                        self._update_stats(log_data)

                # 计算 QPS
                for node in self.stats['nodes']:
                    last_node_stats = self.last_stats['nodes'].get(node, self._init_node_stats())
                    self.stats['nodes'][node]['qps'] = self._calculate_qps(
                        self.stats['nodes'][node],
                        last_node_stats
                    )
                self.stats['total']['qps'] = self._calculate_qps(
                    self.stats['total'],
                    self.last_stats['total']
                )

                # 保存当前统计数据作为下次计算的基准
                self.last_stats = self.stats.copy()
                self._save_last_stats()

                self.last_position['position'] = f.tell()
                self.last_position['last_stats_time'] = current_time

                self._save_stats()
                self._save_last_position()
        except Exception as e:
            print("错误:" + traceback.format_exc())
        finally:
            self._release_lock()

    def get_today_stats(self) -> Dict:
        """获取今日统计数据"""
        if not os.path.exists(self.stats_file):
            return self.stats

        with open(self.stats_file, 'r') as f:
            return json.load(f)

    def get_node_stats(self, node: str) -> Dict:
        """获取指定节点的统计数据"""
        stats = self.get_today_stats()
        return stats['nodes'].get(node, self._init_node_stats())

    def get_total_stats(self) -> Dict:
        """获取总体统计数据"""
        stats = self.get_today_stats()
        return stats['total']

    def reset_stats(self):
        """重置统计数据（带锁）"""
        if not self._acquire_lock():
            print("另一个统计进程正在运行")
            return

        try:
            self._reset_stats_without_lock()
        finally:
            self._release_lock()

    def get_log(self, position: int = -1, limit: int = 16) -> Tuple[int, List[Dict]]:
        """
        获取日志
        :param position: 上次读取的位置，-1 表示从文件末尾开始
        :param limit: 返回的条数
        :return: (新的位置, 日志列表)
        """
        if not os.path.exists(self.log_path) or os.path.getsize(self.log_path) == 0:
            return 0, []

        try:
            with open(self.log_path, 'rb') as f:
                # 获取文件大小
                f.seek(0, os.SEEK_END)
                file_size = f.tell()
                if position > file_size:
                    position = file_size

                # 确定起始位置
                if position == -1:
                    position = file_size

                # 计算需要读取的起始位置
                # 每条日志约158字节，使用512字节作为单条日志的估算值
                read_size = min(limit * 512, position)
                start_position = max(0, position - read_size)

                # 移动到起始位置
                f.seek(start_position)

                # 读取并解析日志
                logs = []
                current_position = start_position

                # 读取文件内容
                content = f.read(read_size)
                # 按行分割
                lines = content.splitlines()

                for line in lines:
                    if not line.strip():
                        continue

                    # 解析CSV行
                    try:
                        fields = next(csv.reader([line.decode()]))
                    except StopIteration:
                        continue

                    if len(fields) < len(self.table_header):
                        continue

                    # 只处理到目标位置之前的日志
                    if current_position + len(line) + 1 > position: # +1 for newline
                        break

                    # 解析日志行
                    log_data = dict(zip(self.table_header, fields[:len(self.table_header)]))
                    logs.append((current_position, log_data))

                    # 更新当前位置
                    current_position += len(line) + 1  # +1 for newline

                # 如果没有找到日志，返回原始位置
                if not logs:
                    return start_position, []

                res_position = 0 if len(logs) <= limit and start_position == 0 else logs[-limit][0]

                # 取最后 limit 条记录并反转顺序（最新的在前）
                logs = logs[-limit:][::-1]

                # 返回最后一条日志的位置和解析后的日志列表
                return res_position, [log[1] for log in logs]

        except Exception as e:
            print(f"读取日志时发生错误: {str(e)}")
            return position, []


def get_log_analyze(site_type: str, site_name: str, date:str="", interval=300) -> Union[LogAnalyzer, TcpLogAnalyzer]:
    if site_type == "http":
        logfile = _LOG_PATH + site_name + "/proxy_access.log"
        if date and date != datetime.date.today().strftime("%Y-%m-%d"):
            logfile += "." + date + ".csv"
        return LogAnalyzer(logfile, _STATUS_CACHE_PATH + site_name, interval)
    else:
        logfile = _TCP_LOG_PATH + site_name + "/tcp_load.log"
        if date and date != datetime.date.today().strftime("%Y-%m-%d"):
            logfile += "." + date + ".csv"
        return TcpLogAnalyzer(logfile, _STATUS_CACHE_PATH + site_name, interval)


def get_log_file(site_type: str, site_name: str, date:str="") -> str:
    if site_type == "http":
        logfile = _LOG_PATH + site_name + "/proxy_access.log"
        if date and date != datetime.date.today().strftime("%Y-%m-%d"):
            logfile += "." + date + ".csv"
        return logfile
    else:
        logfile = _TCP_LOG_PATH + site_name + "/tcp_load.log"
        if date and date != datetime.date.today().strftime("%Y-%m-%d"):
            logfile += "." + date + ".csv"
        return logfile