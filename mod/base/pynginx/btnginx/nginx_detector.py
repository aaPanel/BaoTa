#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import psutil
from collections import namedtuple
from typing import List, Dict, Tuple, Optional, Union, Set, NamedTuple


# 定义Nginx实例信息的namedtuple
class NginxInstance(NamedTuple):
    nginx_bin: str
    nginx_conf: str


class NginxDetector:
    """
    Nginx实例探测器
    实现readme.md中描述的三种定位策略
    """

    # 常见Nginx安装路径
    COMMON_PATHS = [
        '/usr/local/nginx/',
        '/etc/nginx/',
        '/usr/share/nginx/',
        '/opt/nginx/',
        '/home/nginx/',
        '/www/server/nginx/'
    ]

    def __init__(self):
        # type: () -> None
        pass

    def detect_nginx_all(self, only_running =False):
        # type: (bool) -> List[NginxInstance]
        """
        按照优先级依次尝试三种探测策略，返回所有可能的结果
        :return: list[NginxInstance] 包含nginx可执行文件路径和主配置文件路径的列表
        """
        results = []  # type: List[NginxInstance]
        found_configs = set()  # type: Set[str] # 用于去重，基于主配置文件路径

        # 策略1: 进程名称匹配
        process_results = self._detect_by_process_all()
        for result in process_results:
            if result.nginx_conf not in found_configs:
                results.append(result)
                found_configs.add(result.nginx_conf)

        # 策略2: 标准端口监听探测
        port_results = self._detect_by_port_all()
        for result in port_results:
            if result.nginx_conf not in found_configs:
                results.append(result)
                found_configs.add(result.nginx_conf)

        if only_running:
            return  [result for result in results if os.path.exists(result.nginx_conf)]

        # 策略3: 常见路径兜底扫描
        path_results = self._detect_by_common_paths_all()
        for result in path_results:
            if result.nginx_conf not in found_configs:
                results.append(result)
                found_configs.add(result.nginx_conf)

        return results

    @staticmethod
    def _extract_nginx_info(cmdline):
        # type: (List[str]) -> Tuple[Optional[str], Optional[str]]
        """
        从命令行参数中提取Nginx可执行文件路径和配置文件路径
        :param cmdline: 命令行参数列表
        :return: tuple(nginx_bin, nginx_conf)
        """
        nginx_bin = None  # type: Optional[str]
        nginx_conf = None  # type: Optional[str]

        # 解析命令行参数
        for i, arg in enumerate(cmdline):
            if arg.endswith('nginx') and os.path.exists(arg):
                nginx_bin = arg
            elif arg == '-c' and i + 1 < len(cmdline):
                nginx_conf = cmdline[i + 1]

        # 如果没有通过-c参数指定配置文件，则使用默认路径
        if not nginx_conf and nginx_bin:
            # 尝试在可执行文件同目录下查找配置文件
            bin_dir = os.path.dirname(nginx_bin)
            possible_conf = os.path.join(bin_dir, '..', 'conf', 'nginx.conf')
            if os.path.exists(possible_conf):
                nginx_conf = os.path.abspath(possible_conf)
            else:
                # 尝试默认配置路径
                possible_conf = '/etc/nginx/nginx.conf'
                if os.path.exists(possible_conf):
                    nginx_conf = possible_conf

        return nginx_bin, nginx_conf

    @staticmethod
    def _detect_by_process_all():
        # type: () -> List[NginxInstance]
        """
        策略1: 通过进程名称匹配定位所有Nginx实例
        :return: list[NginxInstance]
        """
        results = []  # type: List[NginxInstance]
        processed_pids = set()  # type: Set[int] # 避免重复处理相同PID

        try:
            # 使用pids()获取所有进程ID，然后逐一获取进程信息
            for pid in psutil.pids():
                try:
                    # 检查是否已处理过该PID
                    if pid in processed_pids:
                        continue

                    proc = psutil.Process(pid)
                    # 查找nginx主进程
                    if proc.name() == 'nginx' and 'master' in ' '.join(proc.cmdline()):
                        cmdline = proc.cmdline()
                        processed_pids.add(pid)

                        # 提取Nginx信息
                        nginx_bin, nginx_conf = NginxDetector._extract_nginx_info(cmdline)

                        if nginx_bin and nginx_conf:
                            results.append(NginxInstance(nginx_bin=nginx_bin, nginx_conf=nginx_conf))
                except (psutil.NoSuchProcess, psutil.AccessDenied, IndexError, psutil.ZombieProcess):
                    # 忽略单个进程的错误，继续处理其他进程
                    continue
        except Exception:
            # 忽略整体错误，返回已找到的结果
            pass

        return results

    @staticmethod
    def _detect_by_port_all():
        # type: () -> List[NginxInstance]
        """
        策略2: 通过80/443端口绑定检测定位所有Nginx实例
        :return: list[NginxInstance]
        """
        results = []  # type: List[NginxInstance]
        processed_pids = set()  # type: Set[int] # 避免重复处理相同PID

        try:
            # 获取监听80和443端口的连接
            connections = psutil.net_connections(kind='inet')

            # 遍历所有连接
            for conn in connections:
                if conn.laddr.port in [80, 443] and conn.status == 'LISTEN':
                    try:
                        # 检查是否已处理过该PID
                        if conn.pid in processed_pids:
                            continue

                        proc = psutil.Process(conn.pid)
                        processed_pids.add(conn.pid)

                        # 检查是否为nginx进程
                        if 'nginx' in proc.name():
                            # 获取进程命令行参数
                            cmdline = proc.cmdline()

                            # 提取Nginx信息
                            nginx_bin, nginx_conf = NginxDetector._extract_nginx_info(cmdline)

                            if nginx_bin and nginx_conf:
                                results.append(NginxInstance(nginx_bin=nginx_bin, nginx_conf=nginx_conf))
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
        except Exception:
            pass

        return results

    @classmethod
    def _detect_by_common_paths_all(cls):
        # type: () -> List[NginxInstance]
        """
        策略3: 扫描常见安装路径定位所有Nginx实例
        :return: list[NginxInstance]
        """
        results = []  # type: List[NginxInstance]
        processed_configs = set()  # type: Set[str] # 避免重复处理相同配置文件

        for base_path in cls.COMMON_PATHS:
            # 检查可执行文件是否存在
            nginx_bin = os.path.join(base_path, 'sbin', 'nginx')
            if not os.path.exists(nginx_bin):
                nginx_bin = os.path.join(base_path, 'nginx')
                if not os.path.exists(nginx_bin):
                    continue

            # 检查配置文件是否存在
            nginx_conf = os.path.join(base_path, 'conf', 'nginx.conf')
            if not os.path.exists(nginx_conf):
                nginx_conf = os.path.join(base_path, 'nginx.conf')
                if not os.path.exists(nginx_conf):
                    nginx_conf = '/etc/nginx/nginx.conf'
                    if not os.path.exists(nginx_conf):
                        continue

            # 避免重复处理相同配置文件
            if nginx_conf in processed_configs:
                continue

            processed_configs.add(nginx_conf)
            results.append(NginxInstance(nginx_bin=nginx_bin, nginx_conf=nginx_conf))

        return results


def ng_detect(only_running=False):
    # type: (bool) -> List[NginxInstance]
    """
    获取所有Nginx实例
    :return: list[NginxInstance]
    """
    return NginxDetector().detect_nginx_all(only_running=only_running)
