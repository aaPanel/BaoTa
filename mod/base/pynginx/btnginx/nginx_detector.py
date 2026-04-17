#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import shutil
import subprocess

import psutil
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Union, Set


# 定义Nginx实例信息的namedtuple
@dataclass
class NginxInstance:
    nginx_bin: str
    nginx_conf: str
    working_dir: str
    version: str = ""
    running: bool = False

    def to_dict(self):
        return {
            "nginx_bin": self.nginx_bin,
            "nginx_conf": self.nginx_conf,
            "working_dir": self.working_dir,
            "version": self.version,
            "running": self.running,
        }

class NginxDetector:
    """
    Nginx实例探测器
    实现readme.md中描述的三种定位策略
    """

    # 常见Nginx安装路径
    COMMON_PATHS = [
        '/usr/sbin/nginx',
        '/usr/local/nginx/sbin/nginx',
        '/usr/share/nginx',
        '/opt/nginx/sbin/nginx',
        '/home/nginx/sbin/nginx',
        '/www/server/nginx/sbin/nginx',
    ]

    def __init__(self):
        # type: () -> None
        pass

    @staticmethod
    def _parse_ng_v(ng: NginxInstance):
        try:
            v_out = subprocess.check_output([ng.nginx_bin, "-V"], stderr=subprocess.STDOUT).decode()
        except:
            return False

        regexp_ver = re.compile(r"nginx version:\s*(?P<ver>\S+)\n")
        regexp_config_path = re.compile("\s+--conf-path=(?P<path>(/\S+)+)\s*")
        regexp_prefix = re.compile("\s+--prefix=(?P<path>(/\S+)+)\s*")
        ver_res = regexp_ver.search(v_out)
        if ver_res:
            ng.version = ver_res.group("ver")

        regexp_working_dir = regexp_prefix.search(v_out)
        if regexp_working_dir:
            ng.working_dir = ng.working_dir or regexp_working_dir.group("path")

        regexp_config_path = regexp_config_path.search(v_out)
        if regexp_config_path:
            ng.nginx_conf = ng.nginx_conf or regexp_config_path.group("path")

        if not ng.nginx_conf and ng.working_dir:
            nginx_conf = os.path.join(ng.working_dir, "conf", "nginx.conf")
            if os.path.exists(nginx_conf):
                ng.nginx_conf = nginx_conf

        if not ng.nginx_conf:
            return False
        try:
            t_out = subprocess.check_output([ng.nginx_bin, "-t", "-c", ng.nginx_conf, '-p', ng.working_dir], stderr=subprocess.STDOUT).decode()
        except:
            t_out = ""

        if "test is successful" in t_out:
            return True
        return False


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
        nginx_conf = ''  # type: Optional[str]
        working_dir = ''  # type: Optional[str]

        # 解析命令行参数
        for i, arg in enumerate(cmdline):
            if arg == '-c' and i + 1 < len(cmdline):
                nginx_conf = cmdline[i + 1]
            elif arg == '-p' and i + 1 < len(cmdline):
                working_dir = cmdline[i + 1]

        return nginx_conf, working_dir

    @classmethod
    def _detect_by_process_all(cls):
        # type: () -> List[NginxInstance]
        """
        策略1: 通过进程名称匹配定位所有Nginx实例
        :return: list[NginxInstance]
        """
        results = []  # type: List[NginxInstance]
        # 使用pids()获取所有进程ID，然后逐一获取进程信息
        for pid in psutil.pids():
            ins = cls._detect_by_pid(pid)
            if ins:
                results.append(ins)
        return results

    @classmethod
    def _detect_by_pid(cls, pid: int) -> Optional[NginxInstance]:
        try:
            proc = psutil.Process(pid)
            # 查找nginx主进程
            if proc.name() == 'nginx' and 'master' in ' '.join(proc.cmdline()):
                cmdline = proc.cmdline()


                # 提取Nginx信息
                nginx_conf, working_dir = cls._extract_nginx_info(cmdline)
                bin_path = os.path.realpath(proc.exe())

                ins = NginxInstance(nginx_bin=bin_path, nginx_conf=nginx_conf, working_dir=working_dir, version="",
                                    running=True)
                if cls._parse_ng_v(ins):
                    return ins
        except Exception:
            # 忽略单个进程的错误，继续处理其他进程
            return

    @classmethod
    def _detect_by_common_paths_all(cls):
        # type: () -> List[NginxInstance]
        """
        策略3: 扫描常见安装路径定位所有Nginx实例
        :return: list[NginxInstance]
        """
        results = []  # type: List[NginxInstance]
        common_paths = cls.COMMON_PATHS.copy()
        nginx_which = shutil.which("nginx")
        if nginx_which:
            common_paths.append(os.path.dirname(nginx_which))

        for bin_path in common_paths:
            ins = cls.detect_by_bin(bin_path)
            if ins:
                results.append(ins)

        return results

    @classmethod
    def detect_by_bin(cls, bin_path: str) -> Optional[NginxInstance]:
        if os.path.exists(bin_path) and os.access(bin_path, os.X_OK):
            # 检查可执行文件是否正确
            ins = NginxInstance(nginx_bin=bin_path, nginx_conf="", working_dir="", version="", running=False)
            if cls._parse_ng_v(ins):
                return ins
        return None


def ng_detect(only_running=False):
    # type: (bool) -> List[NginxInstance]
    """
    获取所有Nginx实例
    :return: list[NginxInstance]
    """
    return NginxDetector().detect_nginx_all(only_running=only_running)


def ng_detect_by_bin(bin_path):
    # type: (str) -> Optional[NginxInstance]
    """
    通过可执行文件路径获取Nginx实例
    """
    return NginxDetector().detect_by_bin(bin_path)
