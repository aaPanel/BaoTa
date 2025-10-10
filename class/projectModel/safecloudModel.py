# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wpl <wpl@bt.cn>
# -------------------------------------------------------------------

# 堡塔面板云安全检测-检测项：
# 1. 恶意文件检测[支持]
# 2. 首页风险[支持]
# 3. 网站漏洞扫描[支持]
# 4. 恶意进程检测[开发中……]
# 5. 蜜罐检测[开发中……]
# 6. 攻击链分析[开发中……]
#
# ------------------------------
import os
import re
import json
import sys
import time
import threading
import queue
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any
import hashlib
import requests
import psutil
import fcntl  # 文件锁
from typing import Dict, List, Set, Tuple
import sqlite3

os.chdir("/www/server/panel")
sys.path.append("class/")
import public
import config
from projectModel.base import projectBase


class WebshellDetector:
    """木马检测引擎基类
    @time: 2025-02-19
    """

    def detect(self, file_path: str) -> bool:
        raise NotImplementedError


class PatternDetector(WebshellDetector):
    """基于特征码的检测引擎
    @time: 2025-02-19
    """

    def __init__(self):
        self.rules = {
            'eval_pattern': r'(?:eval|assert)\s*\([^)]*(?:\$_(?:POST|GET|REQUEST|COOKIE)|base64_decode|gzinflate|str_rot13)',
            'system_pattern': r'(?:system|exec|shell_exec)\s*\([^)]*(?:\$|base64_decode)',
            'file_write_pattern': r'(?:file_put_contents|fwrite)\s*\([^,]+,\s*\$_(?:POST|GET)',
            'dangerous_functions': r'(?:passthru|popen|proc_open|create_function)\s*\(',
            'suspicious_encoding': r'(?:base64_decode\s*\(\s*strrev|str_rot13\s*\(\s*base64_decode)\s*\('
        }
        self.compiled_patterns = {name: re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                                  for name, pattern in self.rules.items()}

    def detect(self, file_path: str) -> tuple:
        """基于特征码的检测引擎
        @time: 2025-02-19
        @param file_path: 文件路径
        @return: 是否可疑, 规则名称
        """
        try:
            # 首先尝试 UTF-8
            encodings = ['utf-8', 'gbk', 'gb2312', 'iso-8859-1', 'latin1']
            content = None

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    # logging.error("Error reading file {}: {}".format(file_path, str(e)))
                    return False, ''

            if content is None:
                # 如果所有编码都失败，使用二进制模式读取
                with open(file_path, 'rb') as f:
                    content = f.read().decode('utf-8', errors='ignore')

            # 添加基本过滤，跳过明显的二进制文件
            if b'\x00' in content.encode('utf-8'):
                return False, ''

            for name, pattern in self.compiled_patterns.items():
                if pattern.search(content):
                    return True, name
            return False, ''
        except Exception as e:
            # logging.error("Error scanning file {}: {}".format(file_path, str(e)))
            return False, ''


class BehaviorDetector(WebshellDetector):
    """基于行为分析的检测引擎
    @time: 2025-02-19
    @param file_path: 文件路径
    @return: 是否可疑, 规则名称
    """

    def detect(self, file_path: str) -> tuple:
        try:
            if os.access(file_path, os.X_OK):
                return True, 'executable_permission'

            if os.path.getsize(file_path) < 1024 and file_path.endswith(('.php', '.jsp')):
                return True, 'suspicious_size'

            return False, ''
        except Exception as e:
            # logging.error("Error analyzing file behavior {}: {}".format(file_path, str(e)))
            return False, ''


class YaraDetector(WebshellDetector):
    """基于 Yara 规则的检测引擎
    @time: 2025-02-19
    @param file_path: 文件路径
    @return: 是否可疑, 规则名称
    """

    RULE_CATEGORIES = {
        'webshells': '网站木马检测规则',
        'crypto': '加密挖矿检测规则'
    }

    def __init__(self):
        self.rules = {}  # 每个类别对应一个规则集
        self.base_path = '/www/server/panel/data/safeCloud/rules'
        self.rules_loaded = False
        self.rules_stats = {category: {'total': 0, 'loaded': 0} for category in self.RULE_CATEGORIES}
        self._load_all_rules()

    def _install_yara(self):
        """进程异步安装yara-python模块
        @return: bool
        """
        try:
            # 定义安装锁文件
            lock_file = '/tmp/install_yara.lock'

            # 检查是否已经在安装
            if os.path.exists(lock_file):
                return False

            # 创建锁文件
            public.writeFile(lock_file, str(time.time()))

            # 定义安装脚本
            install_script = '''#!/bin/bash
btpip install yara-python
rm -f /tmp/install_yara.lock
'''
            script_file = '/tmp/install_yara.sh'
            public.writeFile(script_file, install_script)
            public.ExecShell('chmod +x {}'.format(script_file))

            # 使用进程执行安装
            public.ExecShell('nohup {} >> /tmp/install_yara.log 2>&1 &'.format(script_file))
            return True

        except Exception as e:
            public.WriteLog('safecloud', 'yara-python安装失败: {}'.format(str(e)))
            if os.path.exists(lock_file):
                os.remove(lock_file)
            return False

    def check_yara(self):
        """检查并安装yara-python模块
        @return: bool
        """
        try:
            import yara
            return True
        except ImportError:
            self._install_yara()
            return False

    def _load_all_rules(self) -> None:
        """加载所有类别的规则
        @time: 2025-02-19
        @return: 是否加载成功
        """
        # 检查yara-python模块
        if not self.check_yara():
            return public.returnMsg(False, '正在安装所需的模块，请稍后重试')

        try:
            import yara
        except ImportError:
            return public.returnMsg(False, '依赖模块未安装，请稍后重试')

        try:
            # 确保基础规则目录存在
            if not os.path.exists(self.base_path):
                os.makedirs(self.base_path, mode=0o755)
                zip_file = "yara_rules.zip"
                downfile = os.path.join(self.base_path, zip_file)
                public.downloadFile("{}/safeCloud/{}".format(public.get_url(), zip_file), downfile)

                o, e = public.ExecShell("unzip -o {} -d {}".format(downfile, self.base_path))
                # 解压报错
                if e != "":
                    return False

            # 加载每个类别的规则
            for category in self.RULE_CATEGORIES:
                category_path = os.path.join(self.base_path, category)

                # 确保类别目录存在
                if not os.path.exists(category_path):
                    os.makedirs(category_path, mode=0o755)
                    continue

                # 获取该类别下的所有规则文件
                rule_files = {}
                for root, _, files in os.walk(category_path):
                    for file in files:
                        if file.endswith(('.yar', '.yara')):
                            self.rules_stats[category]['total'] += 1
                            name = "{}_{}".format(category, os.path.splitext(file)[0])
                            path = os.path.join(root, file)
                            rule_files[name] = path

                if rule_files:
                    try:
                        # 编译该类别的规则
                        self.rules[category] = yara.compile(filepaths=rule_files)
                        self.rules_stats[category]['loaded'] = len(rule_files)
                    except yara.Error as e:
                        continue

            # 如果至少有一个类别的规则加载成功
            self.rules_loaded = bool(self.rules)

            # 输出规则加载统计
            # self._log_rules_stats()

        except Exception as e:
            pass

    def _log_rules_stats(self) -> None:
        """记录规则加载统计信息
        @time: 2025-02-19
        @return: 是否记录成功
        """
        stats = ["Yara rules loading statistics:"]
        for category, info in self.rules_stats.items():
            stats.append("- {}: {} rules loaded".format(category, info['loaded'] / info['total']))

    def detect(self, file_path: str) -> tuple:
        """
        使用所有类别的 Yara 规则检测文件
        @time: 2025-02-19
        @param file_path: 文件路径
        @return: (is_suspicious: bool, rule_name: str) 是否可疑, 规则名称
        """
        if not self.rules_loaded:
            self._load_all_rules()
            if not self.rules_loaded:
                return False, ''

        try:
            # 基础文件检查
            if not os.path.exists(file_path) or not os.access(file_path, os.R_OK):
                return False, ''

            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:  # 10MB
                return False, ''

            # 对每个类别的规则进行检测
            for category, rules in self.rules.items():
                try:
                    matches = rules.match(file_path, timeout=60)
                    if matches:
                        rule_name = matches[0].rule
                        match_details = []

                        # 收集匹配详情
                        for match in matches[0].strings:
                            match_details.append("{}: {}".format(match[1], match[2].decode('utf-8', errors='ignore')))


                        return True, "yara_{}_{}".format(category, rule_name)

                except yara.TimeoutError:
                    pass
                except yara.Error as e:
                    pass
                except Exception as e:
                    pass
            return False, ''

        except Exception as e:
            return False, ''

    def get_rules_status(self) -> dict:
        """获取规则加载状态统计信息
        @time: 2025-02-19
        @return: <dict>规则加载状态统计信息
        """
        return {
            'total_categories': len(self.RULE_CATEGORIES),
            'loaded_categories': len(self.rules),
            'stats_by_category': self.rules_stats,
            'is_functional': self.rules_loaded
        }


class CloudDetector(WebshellDetector):
    """云端检测引擎
    @time: 2025-02-19
    @param file_path: 文件路径
    @return: <tuple> 是否可疑, 规则名称
    """

    def __init__(self):
        self.cache_file = '/www/server/panel/data/safeCloud/cloud_config.json'
        self.url_cache = self._load_cache()  # 加载缓存配置
        self.last_check_time = self.url_cache.get('last_check', 0)  # 上次检查时间
        self.check_url = self.url_cache.get('check_url', '')  # 检测URL
        self.request_count = 0  # 请求次数
        self.last_request_time = 0  # 上次请求时间
        # 配置参数
        self.cache_ttl = 86400  # URL缓存时间(24小时)
        self.rate_limit = {
            'max_requests': 100,  # 每小时最大请求数
            'interval': 3600,  # 计数周期(秒)
            'min_interval': 1  # 两次请求的最小间隔(秒)
        }

    def _load_cache(self) -> dict:
        """加载缓存配置
        @time: 2025-02-19
        @return: <dict> 缓存配置
        """
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            # logging.error("Error loading cloud config cache: {}".format(str(e)))
            pass
        return {'last_check': 0, 'check_url': ''}

    def _save_cache(self) -> None:
        """保存缓存配置
        @time: 2025-02-19
        """
        try:
            cache_dir = os.path.dirname(self.cache_file)
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)
            with open(self.cache_file, 'w') as f:
                json.dump({
                    'last_check': self.last_check_time,
                    'check_url': self.check_url
                }, f)
        except Exception as e:
            # logging.error("Error saving cloud config cache: {}".format(str(e)))
            pass

    def _update_check_url(self) -> bool:
        """更新检测URL
        @time: 2025-02-19
        @return: <bool> 是否更新成功
        """
        current_time = time.time()

        # 检查缓存是否有效
        if self.check_url and (current_time - self.last_check_time) < self.cache_ttl:
            return True

        try:
            ret = requests.get('http://www.bt.cn/checkWebShell.php').json()
            if ret['status'] and ret['url']:
                self.check_url = ret['url']
                self.last_check_time = current_time
                self._save_cache()
                return True
        except Exception as e:
            # logging.error("Error updating check URL: {}".format(str(e)))
            pass
        return False

    def _check_rate_limit(self) -> bool:
        """检查频率限制
        @time: 2025-02-19
        @return: <bool> 是否检查成功
        """
        current_time = time.time()

        # 检查最小请求间隔
        # if (current_time - self.last_request_time) < self.rate_limit['min_interval']:
        #     return False

        # 重置计数器
        if (current_time - self.last_request_time) > self.rate_limit['interval']:
            self.request_count = 0

        # 检查请求数限制
        if self.request_count >= self.rate_limit['max_requests']:
            return False

        self.request_count += 1
        self.last_request_time = current_time
        return True

    def detect(self, file_path: str) -> tuple:
        """检测文件是否为木马
        @time: 2025-02-19
        @param file_path: 文件路径
        @return: <tuple> 是否可疑, 规则名称
        """
        try:
            # 基础检查
            if not os.path.exists(file_path) or not os.path.isfile(file_path):
                return False, ''

            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size < 1024:  # 小于1KB，视为空文件
                return False, ''
            if file_size > 10 * 1024 * 1024:  # 10MB限制
                return False, ''

            # 频率限制检查
            if not self._check_rate_limit():
                logging.warning("Cloud detection rate limit exceeded for: {}".format(file_path))
                return False, ''

            # 确保有可用的检测URL
            if not self._update_check_url():
                return False, ''

            # 读取文件内容
            file_content = self.ReadFile(file_path)
            if not file_content:
                return False, ''

            # 计算文件MD5
            md5_hash = self.FileMd5(file_path)
            if not md5_hash:
                return False, ''

            # 发送检测请求
            try:
                upload_data = {
                    'inputfile': file_content,
                    'md5': md5_hash
                }
                response = requests.post(self.check_url, upload_data, timeout=20)
                # 添加响应内容检查
                if not response.content:
                    # logging.error("Empty response from cloud detection for file: {}".format(file_path))
                    return False, ''
                try:
                    result = response.json()
                except json.JSONDecodeError as je:
                    # logging.error("Invalid JSON response from cloud detection for {}: {}".format(file_path, response.content))
                    return False, ''

                # 查看是否需要告警
                if isinstance(result, dict) and result.get('msg') == 'ok':
                    try:
                        is_webshell = result.get('data', {}).get('data', {}).get('level') == 5
                        if is_webshell:
                            return True, 'cloud_detection'
                    except (KeyError, AttributeError) as e:
                        # logging.error("Unexpected response structure for {}: {}".format(file_path, result))
                        return False, ''

            except Exception as e:
                # logging.error("Cloud detection error for {}: {}".format(file_path, str(e)))
                pass

            return False, ''

        except Exception as e:
            # logging.error("Error in cloud detection: {}".format(str(e)))
            return False, ''

    def ReadFile(self, filepath: str, mode: str = 'r') -> str:
        """读取文件内容
        @time: 2025-02-19
        @param filepath: 文件路径
        @param mode: 文件模式
        @return: <str> 文件内容
        """
        if not os.path.exists(filepath):
            return ''
        try:
            with open(filepath, mode) as fp:
                return fp.read()
        except Exception:
            try:
                with open(filepath, mode, encoding="utf-8") as fp:
                    return fp.read()
            except Exception as e:
                # logging.error("Error reading file {}: {}".format(filepath, str(e)))
                return ''

    def FileMd5(self, filepath: str) -> str:
        """计算文件MD5
        @time: 2025-02-19
        @param filepath: 文件路径
        @return: <str> 文件MD5
        """
        try:
            if not os.path.exists(filepath) or not os.path.isfile(filepath):
                return ''
            md5_hash = hashlib.md5()
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(64 * 1024), b''):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except Exception as e:
            # logging.error("Error calculating MD5 for {}: {}".format(filepath, str(e)))
            return ''


class SafeCloudModel:
    # 恶意文件 云端上报配置[目前不给支持]
    def __init__(self):
        self.upload_config = {
            'url': 'http://w-check.bt.cn/upload_web.php',
            'max_file_size': 2 * 1024 * 1024,  # 最大文件大小限制(1MB)
            'max_daily_uploads': 50,  # 每日最大上报数量
            'min_upload_interval': 300,  # 最小上报间隔(秒)
            'cache_file': '/www/server/panel/data/safeCloud/upload_stats.json'
        }
        self.upload_stats = self._load_upload_stats()

    def _load_upload_stats(self) -> dict:
        """加载上报统计数据
        @return: dict 上报统计信息
        """
        try:
            if os.path.exists(self.upload_config['cache_file']):
                with open(self.upload_config['cache_file'], 'r') as f:
                    stats = json.load(f)
                    # 检查是否需要重置每日统计
                    if stats.get('date') != time.strftime('%Y-%m-%d'):
                        stats = self._reset_upload_stats()
                    return stats
        except Exception as e:
            # logging.error("加载上报统计数据失败: {}".format(str(e)))
            pass
        return self._reset_upload_stats()

    def _get_upload_filename(self, file_path: str) -> str:
        """生成上传文件名
        @param file_path: 文件路径
        @return: str 处理后的文件名 (format: filename_timestamp.ext)
        """
        try:
            # 获取原始文件名和扩展名
            filename, ext = os.path.splitext(os.path.basename(file_path))

            # 获取当前时间戳
            timestamp = str(int(time.time()))

            # 构造新文件名: 原文件名_时间戳.扩展名
            return "{}_{}.{}".format(filename, timestamp, ext)
        except Exception as e:
            # 出错时返回原文件名
            return os.path.basename(file_path)

    def _reset_upload_stats(self) -> dict:
        """重置上报统计数据
        @return: dict 初始化的统计信息
        """
        return {
            'date': time.strftime('%Y-%m-%d'),
            'count': 0,
            'last_upload_time': 0,
            'uploaded_files': []  # 记录已上报的文件MD5
        }

    def _save_upload_stats(self) -> None:
        """保存上报统计数据"""
        try:
            cache_dir = os.path.dirname(self.upload_config['cache_file'])
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)
            with open(self.upload_config['cache_file'], 'w') as f:
                json.dump(self.upload_stats, f)
        except Exception as e:
            # logging.error("保存上报统计数据失败: {}".format(str(e)))
            pass

    def _check_upload_limits(self, file_path: str) -> tuple:
        """检查上报限制
        @param file_path: 文件路径
        @return: (bool, str) 是否可以上报，原因
        """
        current_time = time.time()

        # 检查文件大小
        try:
            if os.path.getsize(file_path) > self.upload_config['max_file_size']:
                return False, "文件超过大小限制"
        except Exception:
            return False, "无法获取文件大小"

        # 检查是否已上报过该文件
        file_md5 = self.FileMd5(file_path)
        if file_md5 in self.upload_stats['uploaded_files']:
            return False, "文件已上报"

        # 检查日期是否需要重置
        if self.upload_stats['date'] != time.strftime('%Y-%m-%d'):
            self.upload_stats = self._reset_upload_stats()

        # 检查每日上报数量
        if self.upload_stats['count'] >= self.upload_config['max_daily_uploads']:
            return False, "超过每日上报限制"

        # 检查最小上报间隔
        if (current_time - self.upload_stats['last_upload_time']) < self.upload_config['min_upload_interval']:
            return False, "上报过于频繁"

        return True, ""

    def upload_malicious_file(self, file_path: str, rule_name: str) -> bool:
        """上报恶意文件
        @param file_path: 文件路径
        @param rule_name: 规则名称
        @return: bool 是否上报成功
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return False

            # 检查上报限制
            can_upload, reason = self._check_upload_limits(file_path)
            if not can_upload:
                # logging.warning("文件上报受限 {}: {}".format(file_path, reason))
                return False

            # 生成带时间戳的上传文件名
            upload_filename = self._get_upload_filename(file_path)

            # 准备上报数据
            upload_data = {
                'filename': upload_filename,
                'rule_name': rule_name,
                'upload_time': time.strftime('%Y-%m-%d %H:%M:%S')
            }

            # 读取文件内容
            try:
                with open(file_path, 'rb') as f:
                    files = {
                        'file': (upload_data['filename'], f),
                        'data': ('data.json', json.dumps(upload_data))
                    }

                    # 发送上报请求
                    response = requests.post(
                        self.upload_config['url'],
                        files=files,
                        timeout=30
                    )

                    if response.status_code == 200:
                        # 更新统计信息
                        self.upload_stats['count'] += 1
                        self.upload_stats['last_upload_time'] = time.time()
                        self.upload_stats['uploaded_files'].append(self.FileMd5(file_path))
                        self._save_upload_stats()
                        # logging.info("恶意文件上报成功: {}".format(file_path))
                        return True
                    else:
                        # logging.error("恶意文件上报失败 {}: HTTP {}".format(file_path, response.status_code))
                        return False

            except Exception as e:
                # logging.error("上报文件时发生错误 {}: {}".format(file_path, str(e)))
                return False

        except Exception as e:
            # logging.error("处理文件上报时发生错误: {}".format(str(e)))
            pass


class Config:
    """配置管理类
    @time: 2025-02-19
    """

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self.load_config()

        # Sanitize monitor_dirs and save if changed
        changed = False
        monitor_dirs = self.config.get('monitor_dirs', [])

        if isinstance(monitor_dirs, list) and "/" in monitor_dirs:
            monitor_dirs_copy = monitor_dirs.copy()
            monitor_dirs_copy.remove("/")
            changed = True
            if "/www" not in monitor_dirs_copy:
                monitor_dirs_copy.append("/www")
            if "/web/wwwroot" not in monitor_dirs_copy:
                monitor_dirs_copy.append("/web/wwwroot")

            self.config['monitor_dirs'] = monitor_dirs_copy

        if changed:
            self.save_config()
            
        # 初始化时检测并更新 OSS 挂载目录
        self.check_oss_mounts()

    def load_config(self) -> Dict:
        """加载配置文件
        @time: 2025-02-19
        @return: <dict> 配置文件
        """
        default_config = {
            'monitor_dirs': ['/www', "/web/wwwroot"],
            'supported_exts': ['.php', '.jsp', '.asp', '.aspx'],
            'scan_interval': 3600,  # 扫描间隔 6小时 = 21600秒
            'max_threads': 4,
            'log_level': 'INFO',
            'scan_oss': False,  # OSS目录扫描开关，默认关闭
            'oss_dirs': [],  # 存储检测到的OSS挂载目录
            'has_oss_mounts': False,  # 是否存在OSS挂载
            'dynamic_detection': True,  # 动态查杀开关,默认开启
            # 过滤目录
            'exclude_dirs': [
                '/proc',
                '/sys',
                '/dev',
                '/tmp',
                '/run',
                '/usr',
                '/media',
                '/mnt',
                '/sys',
                '/run',
                '/opt',
                '/etc',
                '/boot',
                '/usr/src/',
                '/.Recycle_bin/',
                '/var/lib/docker/',
                '/www/server/',
                '/var/',
                '/www/wwwlogs/',
                '/www/backup/'
            ],
            'max_file_size': 5 * 1024 * 1024,  # 5MB
            'scan_delay': 0.1,  # 每个文件扫描后的延迟(秒)
            'skipped_dirs': {},  # 存储跳过的目录信息，格式: {'dir_path': {'file_count': count, 'mtime': timestamp}}
            'max_files_per_dir': 10000,  # 每个目录的最大文件数限制
            'quarantine': False,  # 是否隔离文件，默认为False
            "alertable": {
                "status": True,  # 是否开启告警
                "safe_type": ["webshell"],  # 告警功能,webshell木马
                "sender": [],  # 告警方法
                "interval": 10800,  # 告警间隔 3小时告警一次
                "time_rule": {
                    "send_interval": 600  # 告警发送间隔 10分钟发送一次
                },
                "number_rule": {
                    "day_num": 20  # 告警发送数量 20个
                }
            }
        }

        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            else:
                # 如果配置文件不存在，创建一个新的
                with open(self.config_path, 'w') as f:
                    json.dump(default_config, f, indent=4)
                pass
        except Exception as e:
            pass

        return default_config

    def save_config(self) -> None:
        """保存配置文件
        @time: 2025-02-19
        @return: <None> 保存配置文件
        """
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            pass

    def update_skipped_dirs(self, dir_path: str, file_count: int, mtime: float) -> None:
        """更新跳过目录的信息
        @time: 2025-02-19
        @param dir_path: 目录路径
        @param file_count: 文件数量
        @param mtime: 修改时间
        @return: <None> 更新跳过目录的信息
        """
        try:
            self.config['skipped_dirs'][dir_path] = {
                'file_count': file_count,
                'mtime': mtime
            }
            self.save_config()
        except Exception as e:
            pass

    def is_dir_skipped(self, dir_path: str, current_mtime: float) -> bool:
        """检查目录是否应该被跳过
        @time: 2025-02-19
        @param dir_path: 目录路径
        @param dir_path: 目录路径
        @param current_mtime: 当前修改时间
        @return: <bool> 是否跳过
        """
        if dir_path in self.config['skipped_dirs']:
            # 如果目录的修改时间没有变化，继续跳过
            if self.config['skipped_dirs'][dir_path]['mtime'] == current_mtime:
                return True
            # 如果修改时间变化了，移除跳过标记
            else:
                del self.config['skipped_dirs'][dir_path]
                self.save_config()
        return False

    def check_oss_mounts(self) -> dict:
        """检测OSS挂载情况
        @time: 2025-03-14
        @return: dict {
            'status': bool,    # 是否检测成功
            'msg': str,        # 提示信息
            'has_mounts': bool # 是否存在挂载
        }
        """
        try:
            # 定义支持的云存储类型
            cloud_storage_types = {
                'fuse.ossfs': '阿里云OSS',
                'fuse.s3fs': 'AWS S3',
                'fuse.cosfs': '腾讯云COS',
                'fuse.obsfs': '华为云OBS',
                'fuse.bosfs': '百度智能云BOS',
                'fuse.rclone': 'Rclone通用存储'
            }

            oss_dirs = []
            mount_info = {}  # 存储挂载点及其对应的存储类型

            # 方法1: 通过 /proc/mounts 检测
            if os.path.exists('/proc/mounts'):
                with open('/proc/mounts', 'r') as f:
                    for line in f:
                        parts = line.split()
                        if len(parts) >= 3:
                            fs_type = parts[2]
                            mount_point = parts[1]

                            # 检查是否是支持的云存储类型
                            if fs_type in cloud_storage_types or any(
                                    tool in line for tool in ['ossfs', 's3fs', 'cosfs', 'obsfs', 'bosfs', 'rclone']
                            ):
                                oss_dirs.append(mount_point)
                                mount_info[mount_point] = cloud_storage_types.get(fs_type, '未知云存储')

            # 方法2: 通过 mount 命令检测（备用方案）
            if not oss_dirs:
                try:
                    # 使用grep的or条件匹配所有支持的存储类型
                    mount_cmd = "mount | grep -E 'ossfs|s3fs|cosfs|obsfs|bosfs|rclone'"
                    mount_output = public.ExecShell(mount_cmd)[0]
                    for line in mount_output.splitlines():
                        if line:
                            parts = line.split()
                            if len(parts) >= 3:
                                mount_point = parts[2]
                                # 识别存储类型
                                storage_type = '未知云存储'
                                for fs_type, name in cloud_storage_types.items():
                                    if fs_type in line or fs_type.split('.')[1] in line:
                                        storage_type = name
                                        break
                                oss_dirs.append(mount_point)
                                mount_info[mount_point] = storage_type
                except:
                    pass

            # 去重
            oss_dirs = list(set(oss_dirs))

            # 更新配置
            self.config['oss_dirs'] = oss_dirs
            self.config['has_oss_mounts'] = bool(oss_dirs)

            # 如果存在云存储挂载，默认加入排除目录（默认不扫描）
            if oss_dirs and not self.config.get('scan_oss', False):
                exclude_dirs = set(self.config['exclude_dirs'])
                exclude_dirs.update(oss_dirs)
                self.config['exclude_dirs'] = list(exclude_dirs)
                self.save_config()

                # 生成挂载信息消息
                mount_details = ["{}:{}".format(path, type_) for path, type_ in mount_info.items()]
                return {
                    'status': True,
                    'msg': "检测到{}个云存储挂载目录，已默认加入过滤列表。挂载详情：{}".format(len(oss_dirs),
                                                                                            ", ".join(mount_details)),
                    'has_mounts': True
                }
            else:
                return {
                    'status': True,
                    'msg': '未检测到云存储挂载，无需处理',
                    'has_mounts': False
                }

        except Exception as e:
            return {
                'status': False,
                'msg': '检测云存储挂载失败: {}'.format(str(e)),
                'has_mounts': False
            }


class main(projectBase):
    def __init__(self):
        self.__path = '/www/server/panel/data/safeCloud'
        # 确保配置目录存在
        if not os.path.exists(self.__path):
            os.makedirs(self.__path, mode=0o755)
        self.__config = Config(os.path.join(self.__path, 'config.json'))

        # 创建日志目录
        self.__log_dir = os.path.join(self.__path, 'log')
        self.__log_file = os.path.join(self.__log_dir, 'detection_{}.log'.format(
            time.strftime("%Y%m%d")
        ))

        # 初始化检测引擎:正则匹配\行为分析\yara规则匹配\clamv检测\机器分析
        self.__detectors = [
            PatternDetector(),  # 正则匹配
            # BehaviorDetector(),  # 行为分析
            YaraDetector(),  # 添加 Yara 检测引擎
            CloudDetector()  # 添加云查杀引擎
        ]

        # 创建必要的目录
        self.__risk_files = os.path.join(self.__path, 'risk_files')
        self.__last_scan = os.path.join(self.__path, 'last_scan.json')
        self.__ignored_md5_list_path = os.path.join(self.__path, 'ignored_md5s.list')
        self.__dir_record = os.path.join(self.__path, 'dir_record.json')
        self.__dir_record_db_path = os.path.join(self.__path, 'dir_record.db')
        self.__json_dir_record_path = os.path.join(self.__path,
                                                   'dir_record.json')  # Path to old JSON file for migration

        self._initialize_dir_database()  # Initialize or migrate database

        for path in [self.__path, self.__risk_files, self.__log_dir]:
            if not os.path.exists(path):
                os.makedirs(path)

    def _get_db_conn(self):
        """获取SQLite数据库连接"""
        conn = sqlite3.connect(self.__dir_record_db_path)
        return conn

    def _create_db_schema(self, conn):
        """创建数据库表结构"""
        cursor = conn.cursor()
        # Table for directory information
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS directory_info (
                dir_path_md5_suffix_16 TEXT(16) PRIMARY KEY,
                mtime INTEGER NOT NULL,
                file_count INTEGER NOT NULL,
                depth INTEGER NOT NULL
            )
        ''')
        # Table for metadata (like last update timestamp)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scan_metadata (
                meta_key TEXT PRIMARY KEY,
                meta_value TEXT NOT NULL
            )
        ''')
        # 确保 last_dir_record_update 元数据键存在，如果它还不存在的话
        cursor.execute("INSERT OR IGNORE INTO scan_metadata (meta_key, meta_value) VALUES (?, ?)",
                       ('last_dir_record_update', str(time.time())))
        conn.commit()

    def _initialize_dir_database(self):
        """初始化目录记录数据库，并删除旧的JSON文件（如果存在）"""
        json_exists = os.path.exists(self.__json_dir_record_path)
        db_exists = os.path.exists(self.__dir_record_db_path)

        # 如果旧的JSON文件存在，则删除它
        if json_exists:
            try:
                os.remove(self.__json_dir_record_path)
            except Exception as e:
                pass

        conn = self._get_db_conn()
        try:
            if not db_exists:
                self._create_db_schema(conn)  # 创建表结构
            else:
                self._create_db_schema(conn)  # 确保表结构是最新的，并初始化元数据（如果需要）
        except Exception as e:
            pass
        finally:
            conn.close()

    # 初始化告警配置 外部接口,给告警配置提供初始化配置
    def init_config(self, get=None):
        return {}

    def get_file_info(self, file_path: str) -> Dict:
        """获取文件信息
        @time: 2025-02-19
        @param file_path: 文件路径
        @return: <dict> 文件信息
        """
        return {
            'path': file_path,
            'mtime': os.path.getmtime(file_path),
            'size': os.path.getsize(file_path)
        }

    def FileMd5(self, filepath):
        """
        @time: 2025-02-19
        @name 生成文件的MD5
        @param filename 文件路径
        @return string(32): 文件的MD5值，失败时返回空字符串
        """
        try:
            if not filepath or not os.path.exists(filepath) or not os.path.isfile(filepath):
                return ''
            import hashlib
            md5_hash = hashlib.md5()
            # 分块读取文件（64KB），避免大文件占用过多内存
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(64 * 1024), b''):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except Exception as e:
            return ''

    def write_detection_log(self, file_path: str, rule_name: str, is_quarantined: bool = False) -> None:
        """写入检测日志
        @time: 2025-02-19
        @param file_path: 文件路径
        @param rule_name: 匹配规则
        @param is_quarantined: 是否已隔离
        """
        try:
            # 获取文件MD5
            md5_hash = self.FileMd5(file_path)

            # 根据规则确定风险等级 0-低危 1-中危 2-高危
            risk_level = 2

            # 构建日志条目
            log_entry = "{}|{}|{}|{}|{}|{}|{}|{}|{}\n".format(
                os.path.basename(file_path),  # 文件名
                file_path,  # 文件完整路径
                "WebShell",  # 风险标签
                md5_hash,  # 文件MD5
                risk_level,  # 风险等级
                time.strftime("%Y-%m-%d %H:%M:%S"),  # 发现时间
                "true" if is_quarantined else "false",  # 是否隔离
                rule_name,  # 匹配规则
                "0"  # 处理状态(0:未处理, 1:已处理)
            )

            # 定义要写入的日志文件列表
            log_files = [
                # 总日志文件
                os.path.join(self.__log_dir, "detection_all.log"),
                # 当天日志文件
                os.path.join(self.__log_dir, "detection_{}.log".format(
                    time.strftime("%Y%m%d")
                ))
            ]

            # 写入所有日志文件
            for log_file in log_files:
                try:
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write(log_entry)
                except Exception as e:
                    # logging.error("Error writing to log file {}: {}".format(log_file, str(e)))
                    pass

        except Exception as e:
            # logging.error("Error in write_detection_log: {}".format(str(e)))
            pass

    def _get_risk_level(self, rule_name: str) -> int:
        """根据规则确定风险等级
        @time: 2025-02-19
        @param rule_name: 规则名称
        @return: 0-低危 1-中危 2-高危
        """
        high_risk_rules = ['eval_pattern', 'system_pattern']
        medium_risk_rules = ['file_write_pattern', 'dangerous_functions']

        if rule_name in high_risk_rules:
            return 2
        elif rule_name in medium_risk_rules:
            return 1
        return 0

    def scan_file(self, file_path: str) -> tuple:
        """检查单个文件
        @time: 2025-02-19
        @param file_path: 文件路径
        @return: <tuple> 是否可疑, 规则名称
        """
        try:
            # 加载或使用缓存的被忽略MD5集合
            if not hasattr(self, '_cached_ignored_md5_set') or \
                    not hasattr(self, '_cached_ignored_md5_set_time') or \
                    (time.time() - self._cached_ignored_md5_set_time > 300):  # 缓存5分钟
                _, self._cached_ignored_md5_set = self._load_ignored_md5_list_and_set()  # 获取set
                self._cached_ignored_md5_set_time = time.time()

            current_file_md5 = self.FileMd5(file_path)
            if current_file_md5 and current_file_md5 in self._cached_ignored_md5_set:
                return False, ''  # 直接返回 False, ''

            # 如果未被忽略，则继续执行检测引擎
            for detector in self.__detectors:
                is_suspicious, rule = detector.detect(file_path)
                if is_suspicious:
                    return True, rule
            return False, ''  # 所有引擎都未检测到问题
        except Exception as e:
            return False, ''

    def handle_suspicious_file(self, file_path: str, rule_name: str) -> bool:
        """处理可疑文件
        @time: 2025-02-19
        @param file_path: 文件路径
        @param rule_name: 规则名称
        @return: 是否处理成功
        """
        try:
            filename = "{}_{}".format(
                os.path.basename(file_path),
                time.strftime("%Y%m%d_%H%M%S")
            )
            quarantine_path = os.path.join(self.__risk_files, filename)
            # 记录日志
            self.write_detection_log(file_path, rule_name, self.__config.config['quarantine'])

            # 移动文件到隔离区
            self.Mv_Recycle_bin(file_path)

            return True
        except Exception as e:
            return False

    def get_dir_info(self, dir_path: str) -> Dict:
        """获取目录信息
        @param dir_path: 目录路径
        @return: 目录信息字典
        """
        try:
            return {
                'mtime': os.path.getmtime(dir_path),
                'file_count': 0,  # 记录目录中的文件数量
                'skip': False,  # 是否跳过该目录
                'depth': len(dir_path.split(os.sep))  # 添加目录深度信息
            }
        except Exception as e:
            return None

    def cpu_guard(self, max_usage=7, max_sleep=10):
        """动态节流控制器
        @param max_usage: 最大CPU使用率阈值(%)
        @param max_sleep: 最大睡眠时间(秒)
        """
        try:
            current_cpu = psutil.cpu_percent(interval=0.1)
            if current_cpu > max_usage:
                # 计算建议的睡眠时间
                sleep_time = 0.5 * (current_cpu / max_usage)
                # 限制最大睡眠时间
                sleep_time = min(sleep_time, max_sleep)
                time.sleep(sleep_time)
        except Exception as e:
            # 如果获取CPU使用率失败，使用最小睡眠时间
            time.sleep(0.5)

    def get_new_files(self) -> List[str]:
        """获取新增或修改的文件列表
        @time: 2025-02-19
        @return: 新增或修改的文件列表
        """
        new_files = []
        current_dirs_data_for_db_save = {}
        total_files = 0  # 当次扫描的文件数
        MAX_DEPTH = 20  # 最大深度
        MAX_FILES_PER_DIR = 10000  # 单个目录最大文件数

        try:
            dir_record_result = self.load_dir_record()
            last_dirs_info_by_hash = dir_record_result.get('directories_by_hash', {})
            # is_first_scan = not bool(last_dirs_info)
            # 首次扫描判断：如果数据库为空（或load_dir_record因错误返回空），则认为是首次
            is_first_scan = not bool(last_dirs_info_by_hash)

            dir_stack = []
            processed_dirs_set = set()  # Stores original paths that have been processed

            for base_dir in self.__config.config['monitor_dirs']:
                if os.path.exists(base_dir) and os.path.isdir(base_dir):
                    dir_info = self.get_dir_info(base_dir)
                    if dir_info:
                        dir_stack.append((base_dir, dir_info['depth']))

            while dir_stack:
                current_dir_original_path, current_depth = dir_stack[-1]

                if current_dir_original_path in processed_dirs_set:
                    dir_stack.pop()
                    continue

                if current_depth > MAX_DEPTH:
                    try:
                        self.__config.update_skipped_dirs(current_dir_original_path, 0, os.path.getmtime(current_dir_original_path))
                    except OSError:
                        pass
                    processed_dirs_set.add(current_dir_original_path)
                    dir_stack.pop()
                    continue

                is_excluded = False
                for excluded_pattern in self.__config.config['exclude_dirs']:
                    if excluded_pattern in current_dir_original_path:
                        is_excluded = True
                        break

                if is_excluded or os.path.islink(current_dir_original_path):
                    processed_dirs_set.add(current_dir_original_path)
                    dir_stack.pop()
                    continue

                try:
                    current_mtime_float = os.path.getmtime(current_dir_original_path)
                    current_mtime_int = int(current_mtime_float)

                    if self.__config.is_dir_skipped(current_dir_original_path, current_mtime_float):
                        processed_dirs_set.add(current_dir_original_path)
                        dir_stack.pop()
                        continue

                    subdirs_to_scan = []
                    try:
                        with os.scandir(current_dir_original_path) as entries:
                            for entry in entries:
                                if entry.is_dir(follow_symlinks=False):
                                    dir_path = entry.path
                                    is_sub_excluded = False
                                    for excluded_pattern in self.__config.config['exclude_dirs']:
                                        if excluded_pattern in dir_path:
                                            is_sub_excluded = True
                                            break
                                    if not is_sub_excluded and dir_path not in processed_dirs_set:
                                        child_depth = current_depth + 1
                                        if child_depth <= MAX_DEPTH:
                                            subdirs_to_scan.append((dir_path, child_depth))
                                        else:
                                            processed_dirs_set.add(dir_path)
                                            try:
                                                self.__config.update_skipped_dirs(dir_path, 0,
                                                                                  os.path.getmtime(dir_path))
                                            except OSError:
                                                pass
                    except OSError as e:
                        processed_dirs_set.add(current_dir_original_path)
                        dir_stack.pop()
                        continue

                    if subdirs_to_scan:
                        dir_stack.extend(subdirs_to_scan)
                        continue

                    dir_stack.pop()
                    processed_dirs_set.add(current_dir_original_path)

                    # Calculate hash for current_dir_original_path to look up in last_dirs_info_by_hash
                    current_dir_hash_suffix_16 = hashlib.md5(current_dir_original_path.encode('utf-8')).hexdigest()[
                                                 -16:]

                    if not is_first_scan and current_dir_hash_suffix_16 in last_dirs_info_by_hash:
                        last_mtime_from_db = last_dirs_info_by_hash[current_dir_hash_suffix_16].get('mtime', 0)
                        if current_mtime_int == last_mtime_from_db:
                            # mtime is same, store its data for saving, then skip file processing for this dir
                            current_dirs_data_for_db_save[current_dir_original_path] = {
                                'mtime': current_mtime_int,
                                'file_count': last_dirs_info_by_hash[current_dir_hash_suffix_16].get('file_count', 0),
                                'depth': current_depth
                            }
                            continue

                    file_count_in_dir = 0
                    current_scan_time = time.time()

                    with os.scandir(current_dir_original_path) as entries:
                        for entry in entries:
                            if entry.is_file(follow_symlinks=False):
                                file_count_in_dir += 1
                                total_files += 1

                                if file_count_in_dir > MAX_FILES_PER_DIR:
                                    try:
                                        self.__config.update_skipped_dirs(current_dir_original_path, file_count_in_dir,
                                                                          current_mtime_float)
                                    except OSError:
                                        pass
                                    break

                                if total_files % 100 == 0:
                                    self.cpu_guard()

                                file_path = entry.path
                                if os.path.splitext(file_path)[1].lower() in self.__config.config['supported_exts']:
                                    try:
                                        file_stat = entry.stat(follow_symlinks=False)
                                        if file_stat.st_size > self.__config.config['max_file_size']:
                                            continue

                                        file_mtime = file_stat.st_mtime
                                        if (current_scan_time - file_mtime) <= 60:
                                            new_files.append(file_path)
                                    except OSError as e:
                                        continue

                    current_dirs_data_for_db_save[current_dir_original_path] = {
                        'mtime': current_mtime_int,
                        'file_count': file_count_in_dir,
                        'depth': current_depth
                    }

                except OSError as e:
                    processed_dirs_set.add(current_dir_original_path)
                    dir_stack.pop()
                    continue

            self.save_dir_record({
                'directories': current_dirs_data_for_db_save,  # Pass dict keyed by original_path
                'last_update': time.time()
            })

            self.save_current_scan({
                'scan_time': time.time(),
                'total_files': total_files,
                'is_first_scan': is_first_scan
            })

        except Exception as e:
            pass

        return new_files

    def scan_suspicious_files(self, file_list: List[str]) -> List[str]:
        """对文件列表进行木马查杀
        @time: 2025-02-19
        @param file_list: 文件列表
        @return: <list> 可疑文件列表
        """
        detected_webshells = []
        try:
            for file_path in file_list:
                try:
                    is_suspicious, rule = self.scan_file(file_path)
                    if is_suspicious:
                        # 如果文件是可疑的，判断是否需要隔离处理
                        if self.__config.config['quarantine']:
                            self.handle_suspicious_file(file_path, rule)
                        else:
                            self.write_detection_log(file_path, rule)
                        detected_webshells.append(file_path)
                except Exception as e:
                    continue
            if detected_webshells:
                self.send_webshell_batch_alert(detected_webshells)
        except Exception as e:
            # logging.error("Error in scan_suspicious_files: {}".format(str(e)))
            pass

        return detected_webshells

    # 主要检测入口
    def webshell_detection(self, get: Dict) -> Dict:
        """主要检测入口
        @time: 2025-02-19
        @param get: 请求参数
        @return: <dict> 检测结果
        """
        try:
            # 检测是否开启动态查杀开关
            if not self.__config.config.get('dynamic_detection', True):
                return public.returnMsg(True, '动态查杀功能已关闭，跳过检测')
            # task任务频率控制：12小时执行一次
            safecloud_dir = '/www/server/panel/data/safeCloud'
            if not os.path.exists(safecloud_dir):
                os.makedirs(safecloud_dir)

            last_detection_file = '{}/last_detection_time.json'.format(safecloud_dir)
            current_time = int(time.time())
            is_task = hasattr(get, 'is_task') and get.is_task == 1
            # 检查上次执行时间（仅对计划任务生效）
            if is_task and os.path.exists(last_detection_file):
                try:
                    with open(last_detection_file, 'r') as f:
                        # 添加文件锁
                        fcntl.flock(f, fcntl.LOCK_SH)
                        try:
                            last_detection_data = json.load(f)
                        finally:
                            fcntl.flock(f, fcntl.LOCK_UN)

                    last_detection_time = last_detection_data.get('time', 0)
                    # 检查是否需要执行 (12小时 = 21600秒)
                    if (current_time - last_detection_time) < 43200:
                        return public.returnMsg(True, '距离上次扫描时间不足12小时，跳过本次扫描')
                except Exception as e:
                    return {
                        'status': False,
                        'msg': "扫描过程中发生错误: {}".format(str(e)),
                        'detected': []
                    }

            # 更新执行时间（提前写入，防止长时间执行导致多次触发）
            if is_task:
                try:
                    with open(last_detection_file, 'w') as f:
                        fcntl.flock(f, fcntl.LOCK_EX)
                        try:
                            json.dump({'time': current_time}, f)
                        finally:
                            fcntl.flock(f, fcntl.LOCK_UN)
                except Exception as e:
                    return {
                        'status': False,
                        'msg': "扫描过程中发生错误: {}".format(str(e)),
                        'detected': []
                    }

            # 获取新增或修改的文件
            new_files = self.get_new_files()

            # 对新增文件进行木马查杀
            detected_webshells = self.scan_suspicious_files(new_files)

            # 告警配置
            return {
                'status': True,
                'msg': "扫描完成，发现{}个可疑文件".format(len(detected_webshells)),
                'detected': detected_webshells
            }
        except Exception as e:
            return {
                'status': False,
                'msg': "扫描过程中发生错误: {}".format(str(e)),
                'detected': []
            }

    def load_last_scan(self) -> Dict:
        """加载上次扫描结果
        @time: 2025-02-19
        @return: <dict> 上次扫描结果
        """
        if not os.path.exists(self.__last_scan):
            return {}
        try:
            with open(self.__last_scan, 'r') as f:
                return json.load(f)
        except Exception as e:
            return {}

    def save_current_scan(self, scan_data: Dict) -> None:
        """保存当前扫描结果
        @time: 2025-02-19
        @param scan_data: 扫描结果
        @return: <None> 保存当前扫描结果
        """
        try:
            # 读取上次的扫描结果
            last_scan_info = self.load_last_scan()
            # last_total_files = last_scan_info.get('total_files', 0)
            # 添加更多元数据
            scan_data.update({
                'scan_version': '1.0',
                'scan_timestamp': time.time(),
                'scan_date': time.strftime("%Y-%m-%d %H:%M:%S"),
                # 'total_dirs': len(scan_data['directories']),
                'total_files': scan_data.get('total_files', 0),  # 单次扫描文件总数
            })

            # 确保目录存在
            scan_dir = os.path.dirname(self.__last_scan)
            if not os.path.exists(scan_dir):
                os.makedirs(scan_dir)

            # 保存当前扫描结果
            with open(self.__last_scan, 'w') as f:
                json.dump(scan_data, f, indent=4)

        except Exception as e:
            # logging.error("Error saving current scan: {}".format(str(e)))
            pass

    def load_dir_record(self) -> Dict:
        """加载目录记录
        @time: 2025-02-19
        @return: 目录记录信息
        """
        # try:
        #     if os.path.exists(self.__dir_record):
        #         with open(self.__dir_record, 'r') as f:
        #             return json.load(f)
        #     return {'directories': {}, 'last_update': 0}
        # except Exception as e:
        #     # logging.error("加载目录记录失败: {}".format(str(e)))
        #     return {'directories': {}, 'last_update': 0}
        directories_by_hash = {}
        last_update_ts = 0.0

        if not os.path.exists(self.__dir_record_db_path):
            return {'directories_by_hash': {}, 'last_update': last_update_ts}

        conn = self._get_db_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT dir_path_md5_suffix_16, mtime, file_count, depth FROM directory_info")
            rows = cursor.fetchall()
            for row in rows:
                hash_suffix, mtime, file_count, depth = row
                directories_by_hash[hash_suffix] = {
                    'mtime': mtime,
                    'file_count': file_count,
                    'depth': depth
                }

            cursor.execute("SELECT meta_value FROM scan_metadata WHERE meta_key = ?", ('last_dir_record_update',))
            row_meta = cursor.fetchone()
            if row_meta:
                try:
                    last_update_ts = float(row_meta[0])
                except ValueError:
                    last_update_ts = 0.0
        except sqlite3.Error as e:
            return {'directories_by_hash': {}, 'last_update': 0.0}
        finally:
            conn.close()

        return {'directories_by_hash': directories_by_hash, 'last_update': last_update_ts}

    def save_dir_record(self, record_data: Dict) -> None:
        """保存目录记录
        @time: 2025-02-19
        @param record_data: 目录记录数据
        """
        current_dirs_by_original_path = record_data.get('directories', {})
        last_update_ts = record_data.get('last_update', time.time())

        conn = self._get_db_conn()
        cursor = conn.cursor()
        try:
            conn.execute("BEGIN TRANSACTION")
            cursor.execute("DELETE FROM directory_info")  # Clear old records

            for original_path, data in current_dirs_by_original_path.items():
                try:
                    path_hash_suffix_16 = hashlib.md5(original_path.encode('utf-8')).hexdigest()[-16:]
                    mtime = int(data['mtime'])
                    file_count = int(data['file_count'])
                    depth = int(data['depth'])

                    cursor.execute('''
                        INSERT INTO directory_info (dir_path_md5_suffix_16, mtime, file_count, depth)
                        VALUES (?, ?, ?, ?)
                    ''', (path_hash_suffix_16, mtime, file_count, depth))
                except Exception as e:
                    pass

            cursor.execute('''
                INSERT OR REPLACE INTO scan_metadata (meta_key, meta_value) VALUES (?, ?)
            ''', ('last_dir_record_update', str(last_update_ts)))

            conn.commit()
        except sqlite3.Error as e:
            try:
                conn.rollback()
            except sqlite3.Error as rb_err:
                pass
        finally:
            conn.close()

    # 获取木马文件检测结果
    def get_webshell_result(self, get):
        """
            @name 木马隔离文件
            @author wpl@bt.cn
            @time 2025-02-14
            @return list 木马文件列表
        """
        try:
            # 埋点
            public.set_module_logs("safe_detect", "get_webshell_result")
            # 获取上次扫描信息
            last_scan_info = self.load_last_scan()
            last_scan_stats = {
                'scan_time': time.strftime("%Y-%m-%d %H:%M:%S",
                                           time.localtime(last_scan_info.get('scan_timestamp', 0))),
                'total_files': last_scan_info.get('total_files', 0)
                # 'total_dirs': last_scan_info.get('total_dirs', 0)
            }

            # 确定时间范围
            current_time = time.time()
            time_range = None
            if hasattr(get, 'day'):
                if get.day == '1':
                    time_range = current_time - 24 * 3600  # 今天（24小时内）
                elif get.day == '7':
                    time_range = current_time - 7 * 24 * 3600  # 近7天
                elif get.day == '30':
                    time_range = current_time - 30 * 24 * 3600  # 近30天

            ret = []
            risk_stats = {0: 0, 1: 0, 2: 0}  # 风险等级统计
            processed_stats = {0: 0, 1: 0}  # 处理状态统计

            # 读取总日志文件
            log_path = os.path.join(self.__log_dir, "detection_all.log")
            if not os.path.exists(log_path):
                return {
                    'status': True,
                    'msg': "日志文件不存在",
                    'detected': [],
                    'last_scan_time': last_scan_stats['scan_time'],
                    'total_scanned_files': last_scan_stats['total_files'],
                    'risk_stats': risk_stats,
                    'processed_stats': processed_stats
                }

            with open(log_path, 'r', encoding='utf-8') as f:
                for line in f.readlines():
                    line = line.strip()
                    if not line: continue

                    try:
                        # 解析日志行
                        parts = line.split('|')
                        if len(parts) >= 9:
                            file_info = {
                                'filename': parts[0],
                                'filepath': parts[1],
                                'threat_type': parts[2],
                                'md5': parts[3],
                                'risk_level': int(parts[4]),
                                'time': parts[5],
                                'quarantined': parts[6].lower() == 'true',
                                'rule': parts[7],
                                'processed': int(parts[8])
                            }

                            # 时间范围筛选
                            if time_range:
                                log_time = time.mktime(time.strptime(file_info['time'], "%Y-%m-%d %H:%M:%S"))
                                if log_time < time_range:
                                    continue

                            # ... existing code for risk level description ...
                            file_info['risk_level_desc'] = {
                                0: '低危',
                                1: '中危',
                                2: '高危'
                            }.get(file_info['risk_level'], '未知')

                            # ... existing code for filtering ...
                            if hasattr(get, 'risk_level') and str(file_info['risk_level']) != str(get.risk_level):
                                continue

                            if hasattr(get, 'processed'):
                                if str(file_info['processed']) != str(get.processed):
                                    continue
                            else:
                                if file_info['processed'] != 0:
                                    continue

                            # 更新统计信息
                            risk_stats[file_info['risk_level']] += 1
                            processed_stats[file_info['processed']] += 1

                            ret.append(file_info)
                    except Exception as e:
                        # logging.error("Error parsing log line: {}".format(str(e)))
                        continue

            # ... existing code ...
            ret.sort(key=lambda x: x['time'], reverse=True)

            return {
                'status': True,
                'msg': "获取成功",
                'detected': ret,
                'last_scan_time': last_scan_stats['scan_time'],
                'total_scanned_files': last_scan_stats['total_files'],
                'total_detected': len(ret),
                'risk_stats': risk_stats,
                'processed_stats': processed_stats
            }

        except Exception as e:
            # logging.error("Error in webshell_file: {}".format(str(e)))
            return {
                'status': True,
                'msg': "扫描过程中发生错误: {}".format(str(e)),
                'detected': [],
                'last_scan_time': '',
                'total_scanned_files': 0,
                'total_detected': 0,
                'risk_stats': risk_stats,
                'processed_stats': processed_stats
            }

    # 开启自动检测服务 每两小时执行一次

    # 配置获取
    def get_config(self, get) -> Dict:
        """获取配置信息
        @time: 2025-02-19
        @return: <dict> 配置信息
        """
        try:
            return {
                'status': True,
                'msg': '获取成功',
                'data': {
                    'monitor_dirs': self.__config.config.get('monitor_dirs', []),
                    # 'supported_exts': self.__config.config.get('supported_exts', []),
                    'scan_interval': self.__config.config.get('scan_interval', 1),
                    'scan_oss': self.__config.config.get('scan_oss', False),
                    'has_oss_mounts': self.__config.config.get('has_oss_mounts', False),
                    'oss_dirs': self.__config.config.get('oss_dirs', []),
                    # 'max_threads': self.__config.config.get('max_threads', 4),
                    # 'log_level': self.__config.config.get('log_level', 'INFO'),
                    'exclude_dirs': self.__config.config.get('exclude_dirs', []),
                    # 'max_file_size': self.__config.config.get('max_file_size', 5242880),
                    # 'scan_delay': self.__config.config.get('scan_delay', 0.1),
                    # 'skipped_dirs': self.__config.config.get('skipped_dirs', {}),
                    # 'max_files_per_dir': self.__config.config.get('max_files_per_dir', 10000),
                    'quarantine': self.__config.config.get('quarantine', False),
                    'alertable': self.__config.config.get('alertable', {}),
                    'dynamic_detection': self.__config.config.get('dynamic_detection', True)
                }
            }
        except Exception as e:
            # logging.error("Error getting config: {}".format(str(e)))
            return {
                'status': False,
                'msg': "获取配置失败: {}".format(str(e)),
                'data': {}
            }

    def set_config(self, get):
        """修改配置信息
        @time: 2025-02-19
        @param get.quarantine: 是否隔离
        @param get.monitor_dirs: 监控目录列表 (换行符分隔，用于批量覆盖)
        @param get.exclude_dirs: 排除目录列表 (换行符分隔，用于批量覆盖)
        @param get.add_monitor_path: 要添加到监控列表的单个目录路径
        @param get.delete_monitor_path: 要从监控列表删除的单个目录路径
        @param get.add_exclude_path: 要添加到排除列表的单个目录路径
        @param get.delete_exclude_path: 要从排除列表删除的单个目录路径
        @param get.supported_exts: 支持的文件扩展名列表
        """
        try:
            # 定义可修改的配置项及其验证规则
            config_rules = {
                'quarantine': {
                    'validator': lambda x: str(x).lower() in ('true', 'false'),
                    'converter': lambda x: str(x).lower() == 'true',
                    'error_msg': "quarantine 参数必须是 'true' 或 'false'",
                    'success_msg': lambda x: "文件拦截功能已{}".format("开启" if x else "关闭")
                },
                'dynamic_detection': {
                    'validator': lambda x: str(x).lower() in ('true', 'false'),
                    'converter': lambda x: str(x).lower() == 'true',
                    'error_msg': "dynamic_detection 参数必须是 'true' 或 'false'",
                    'success_msg': lambda x: "动态查杀功能已{}".format("开启" if x else "关闭")
                },
                'scan_oss': {
                    'validator': lambda x: str(x).lower() in ('true', 'false'),
                    'converter': lambda x: str(x).lower() == 'true',
                    'error_msg': "scan_oss 参数必须是 'true' 或 'false'",
                    'success_msg': lambda x: "OSS目录扫描已{}".format("开启" if x else "关闭"),
                    'pre_check': lambda: self.__config.config.get('has_oss_mounts', False),
                    'pre_check_msg': "未检测到OSS存储桶挂载，无需设置",
                    'post_process': self._handle_oss_scan_change
                },
                'monitor_dirs': {  # 批量覆盖
                    'validator': lambda x: isinstance(x, str),
                    'converter': lambda x: x.strip().split('\\n'),  # Split by newline
                    'error_msg': 'monitor_dirs 格式错误，请确保每行一个目录路径',
                    'success_msg': lambda x: "监控目录列表已更新，当前共{}个目录".format(len(x))
                },
                'exclude_dirs': {  # 批量覆盖
                    'validator': lambda x: isinstance(x, str),
                    'converter': lambda x: list(set(p.strip() for p in x.strip().split('\\n') if p.strip())),
                    # Split by newline, strip, filter empty, unique
                    'error_msg': 'exclude_dirs 格式错误，请确保每行一个目录路径',
                    'success_msg': lambda x: "排除目录列表已更新，当前共{}个目录".format(len(x))
                },
                'supported_exts': {
                    'validator': lambda x: isinstance(x, str) and x.strip(),
                    'converter': lambda x: [ext.strip() if ext.strip().startswith('.') else '.{}'.format(ext.strip())
                                            for ext in x.strip().split('\\n')],
                    'error_msg': 'supported_exts 格式错误，请确保每行一个扩展名',
                    'success_msg': lambda x: "监控文件类型已更新，当前支持{}种扩展名".format(len(x))
                }
            }

            # 记录修改项
            changed = False
            success_messages = []

            # 处理每个配置项 (批量覆盖)
            for key, rule in config_rules.items():
                value_str = getattr(get, key, None)  # get表单传递过来的都是字符串
                if value_str is not None:  # 检查是否存在此参数
                    try:
                        # 前置检查（如果有）
                        if 'pre_check' in rule and not rule['pre_check']():
                            return public.returnMsg(False, rule['pre_check_msg'])

                        # 验证参数 (原始字符串)
                        if not rule['validator'](value_str):
                            return public.returnMsg(False, rule['error_msg'])

                        # 转换值
                        new_value = rule['converter'](value_str)

                        # 对目录和扩展名进行额外验证和处理
                        if key == 'monitor_dirs':
                            # 过滤掉空行和不存在的目录
                            new_value = [path for path in new_value if path and os.path.exists(path)]
                            if not new_value and value_str.strip() != "":  # 如果输入非空但结果为空，说明路径都无效
                                return public.returnMsg(False, '提供的监控目录路径均无效或不存在')
                            # 允许清空列表
                            if value_str.strip() == "" and self.__config.config.get(key):
                                new_value = []


                        elif key == 'supported_exts':
                            # 过滤掉空行和重复的扩展名
                            new_value = list(set(ext for ext in new_value if ext))
                            if not new_value and value_str.strip() != "":
                                return public.returnMsg(False, '未提供有效的文件扩展名')
                            # 允许清空列表
                            if value_str.strip() == "" and self.__config.config.get(key):
                                new_value = []

                        elif key == 'exclude_dirs':  # 对于批量设置的exclude_dirs，已在converter中处理
                            if not new_value and value_str.strip() != "":
                                return public.returnMsg(False, '提供的排除目录路径格式不正确或均为空')
                            if value_str.strip() == "" and self.__config.config.get(key):
                                new_value = []

                        # 检查值是否发生变化
                        old_value = self.__config.config.get(key)
                        if new_value != old_value:
                            self.__config.config[key] = new_value
                            changed = True

                            # 执行后置处理（如果有）
                            if 'post_process' in rule:
                                rule['post_process'](new_value)

                            if key not in ['quarantine', 'dynamic_detection', 'scan_oss']:  # 这些有专门的成功消息
                                success_messages.append(rule['success_msg'](new_value))
                            elif 'success_msg' in rule:  # 对于布尔型，使用其自身的success_msg
                                success_messages.append(rule['success_msg'](new_value))


                    except Exception as e:
                        return public.returnMsg(False, '处理 {} 参数时出错: {}'.format(key, str(e)))

            # 处理单个路径的新增/删除
            # --- Monitor Dirs Single Path Operations ---
            add_monitor_path = getattr(get, 'add_monitor_path', None)
            if add_monitor_path and isinstance(add_monitor_path, str):
                path_to_add = add_monitor_path.strip()
                if not path_to_add:
                    return public.returnMsg(False, "新增监控目录失败：路径不能为空")
                if not os.path.exists(path_to_add):
                    return public.returnMsg(False, "新增监控目录失败：路径 '{}' 不存在或无效".format(path_to_add))

                current_monitor_dirs = self.__config.config.setdefault('monitor_dirs', [])
                if path_to_add not in current_monitor_dirs:
                    current_monitor_dirs.append(path_to_add)
                    self.__config.config['monitor_dirs'] = list(
                        set(current_monitor_dirs))  # Ensure uniqueness if added multiple ways
                    changed = True
                    success_messages.append("监控目录已新增: {}".format(path_to_add))
                else:
                    success_messages.append("监控目录已存在，未重复添加: {}".format(path_to_add))

            delete_monitor_path = getattr(get, 'delete_monitor_path', None)
            if delete_monitor_path and isinstance(delete_monitor_path, str):
                path_to_delete = delete_monitor_path.strip()
                if not path_to_delete:
                    return public.returnMsg(False, "删除监控目录失败：路径不能为空")

                current_monitor_dirs = self.__config.config.get('monitor_dirs', [])
                if path_to_delete in current_monitor_dirs:
                    current_monitor_dirs.remove(path_to_delete)
                    self.__config.config['monitor_dirs'] = current_monitor_dirs
                    changed = True
                    success_messages.append("监控目录已删除: {}".format(path_to_delete))
                else:
                    return public.returnMsg(False, "删除监控目录失败：路径 '{}' 不在监控列表中".format(path_to_delete))

            # --- Exclude Dirs Single Path Operations ---
            add_exclude_path = getattr(get, 'add_exclude_path', None)
            if add_exclude_path and isinstance(add_exclude_path, str):
                path_to_add = add_exclude_path.strip()
                if not path_to_add:
                    return public.returnMsg(False, "新增排除目录失败：路径不能为空")
                # 对于排除目录，通常不检查路径是否存在
                current_exclude_dirs = self.__config.config.setdefault('exclude_dirs', [])
                if path_to_add not in current_exclude_dirs:
                    current_exclude_dirs.append(path_to_add)
                    self.__config.config['exclude_dirs'] = list(set(current_exclude_dirs))  # Ensure uniqueness
                    changed = True
                    success_messages.append("排除目录已新增: {}".format(path_to_add))
                else:
                    success_messages.append("排除目录已存在，未重复添加: {}".format(path_to_add))

            delete_exclude_path = getattr(get, 'delete_exclude_path', None)
            if delete_exclude_path and isinstance(delete_exclude_path, str):
                path_to_delete = delete_exclude_path.strip()
                if not path_to_delete:
                    return public.returnMsg(False, "删除排除目录失败：路径不能为空")

                current_exclude_dirs = self.__config.config.get('exclude_dirs', [])
                if path_to_delete in current_exclude_dirs:
                    current_exclude_dirs.remove(path_to_delete)
                    self.__config.config['exclude_dirs'] = current_exclude_dirs
                    changed = True
                    success_messages.append("排除目录已删除: {}".format(path_to_delete))
                else:
                    return public.returnMsg(False, "删除排除目录失败：路径 '{}' 不在排除列表中".format(path_to_delete))

            # 如果有修改，保存配置
            if changed:
                try:
                    self.__config.save_config()
                    if success_messages:
                        return public.returnMsg(True, '设置成功：{}'.format(
                            '；'.join(list(set(success_messages)))))  # 使用set去重消息
                    else:  # 如果changed为True但没有具体成功消息（例如，只清空了列表）
                        return public.returnMsg(True, '配置已更新')
                except Exception as e:
                    return public.returnMsg(False, '保存配置文件失败: {}'.format(str(e)))
            else:
                # 如果有尝试进行单个路径操作但路径已存在或不存在于删除列表，仍然给一个提示
                if success_messages:
                    return public.returnMsg(True, '；'.join(list(set(success_messages))))
                return public.returnMsg(False, '未检测到配置变更或无需变更')

        except Exception as e:
            # logging.error("Error in set_config: {}".format(str(e)))
            return public.returnMsg(False, '修改配置失败: {}'.format(str(e)))

    # 开启恶意文件检测
    def start_malware_detection(self):

        pass

    def _handle_oss_scan_change(self, enable: bool) -> None:
        """处理OSS扫描设置变更
        @time: 2025-03-14
        @param enable: bool 是否启用OSS扫描
        """
        try:
            exclude_dirs = set(self.__config.config['exclude_dirs'])
            oss_dirs = set(self.__config.config.get('oss_dirs', []))

            if not enable:
                # 关闭扫描时，将OSS目录添加到排除目录
                exclude_dirs.update(oss_dirs)
            else:
                # 开启扫描时，从排除目录中移除OSS目录
                exclude_dirs = {
                    dir_path for dir_path in exclude_dirs
                    if dir_path not in oss_dirs
                }

            self.__config.config['exclude_dirs'] = list(exclude_dirs)
            self.__config.save_config()
        except Exception as e:
            pass

    def start_service(self, get):
        '''
            @time: 2025-02-19
            @name 启动服务
            @return dict
        '''
        if self.get_service_status2(): return public.returnMsg(False, '服务已启动!')
        self.wrtie_init()
        shell_info = '''
            # 填写启动服务脚本
        '''
        init_file = '/etc/init.d/bt_cloud_safe'
        public.WriteFile('/www/server/panel/class/projectModel/bt_cloud_safe', shell_info)
        time.sleep(0.3)
        public.ExecShell("{} start".format(init_file))
        if self.get_service_status2():
            # public.WriteLog('文件监控','启动服务')
            return public.returnMsg(True, '启动成功!')
        return public.returnMsg(False, '启动失败!')

    def stop_service(self, get):
        '''
            @time: 2025-02-19
            @name 停止服务
            @return dict
        '''
        if not self.get_service_status2(): return public.returnMsg(False, '服务已停止!')
        init_file = '/etc/init.d/bt_cloud_safe'
        public.ExecShell("{} stop".format(init_file))
        time.sleep(0.3)
        if not self.get_service_status2():
            public.WriteLog('木马云查杀', '停止服务')
            return public.returnMsg(True, '停止成功!')
        return public.returnMsg(False, '停止失败!')

    def convert_to_bool(self, value):
        if isinstance(value, bool):
            return value
        elif isinstance(value, str):
            lower_value = value.lower()
            if lower_value in ['true', '1', 'yes']:
                return True
            elif lower_value in ['false', '0', 'no']:
                return False
        return None

    # 告警配置
    def set_alarm_config(self, get):
        '''
            @time: 2025-02-19
            @name 设置告警配置
                - 支持告警方式:邮件、企业微信机器人、钉钉机器人、飞书机器人
                - 支持功能:木马查杀
                - 支持频率:10分钟内,仅限告警一次
            @param get.status: 是否开启[用户可设置]
            @param get.safe_type: 告警功能,目前支持webshell木马[用户可设置]
            @param get.sender: 告警方式[用户可设置]
            @param get.interval: 告警间隔 默认3小时仅限告警一次
            @param get.time_rule: 告警时间规则 默认10分钟内仅限告警一次
            @param get.number_rule: 告警数量规则 默认一天仅限告警20次
            @return dict
        '''
        try:
            # 参数验证
            if not hasattr(get, 'status') or not hasattr(get, 'safe_type') or not hasattr(get, 'sender'):
                return public.returnMsg(False, '参数错误: 必须提供 status, safe_type 和 sender')

            # 转换并验证状态值
            try:
                # status = bool(get.status)
                status = self.convert_to_bool(get.status)
            except:
                return public.returnMsg(False, 'status 必须为布尔值')

            # 验证告警功能
            supported_types = ['webshell']
            if get.safe_type not in supported_types:
                return public.returnMsg(False, '请勾选支持告警类型!')

            # 验证告警方式
            # supported_senders = ['mail', 'wx_account', 'dingding', 'weixin', 'feishu']
            sender_list = get.sender.split(',')
            # for sender in sender_list:
            #     if sender not in supported_senders:
            #         return public.returnMsg(False, '不支持的告警方式: {}，支持的方式: {}'.format(sender, ",".join(supported_senders)))

            # 获取现有配置
            current_config = self.__config.config.get('alertable', {})

            # 构造告警配置
            alert_data = {
                "status": status,
                "safe_type": [get.safe_type],
                "sender": sender_list,
                # 保持其他配置项不变或使用默认值
                "interval": current_config.get('interval', 10800),  # 3小时
                "time_rule": current_config.get('time_rule', {"send_interval": 600}),  # 10分钟
                "number_rule": current_config.get('number_rule', {"day_num": 20})  # 每天20次
            }

            # 保存配置
            from mod.base.push_mod.safe_mod_push import SafeCloudTask
            res = SafeCloudTask.set_push_conf(alert_data)

            if not res:
                # 更新本地配置
                self.__config.config['alertable'] = alert_data
                self.__config.save_config()
                return public.returnMsg(True, '告警配置设置成功')
            else:
                return public.returnMsg(False, '告警配置设置失败: {}'.format(res))

        except Exception as e:
            return public.returnMsg(False, '设置告警配置时发生错误: {}'.format(str(e)))

    # 获取告警配置
    def get_alarm_config(self, get):
        '''
            @time: 2025-02-19
            @name 获取告警配置
            @return dict
        '''

        pass

    def send_webshell_batch_alert(self, file_paths: List[str]) -> None:
        """发送木马检测批量告警
        @param file_paths: 木马文件路径列表
        @return: None
        """
        try:
            # 检查是否有文件需要告警
            if not file_paths:
                return

            # 检查告警配置是否已启用
            alert_config = self.__config.config.get('alertable', {})
            if not alert_config.get('status', False) or not alert_config.get('sender'):
                logging.info("告警功能未启用或未配置告警方式，跳过告警发送")
                return

            # 构造告警消息
            alert_msg = [
                "【恶意文件检测】检测到服务器被恶意植入木马文件，请进入面板，点击首页-安全风险，进行查看",
                "已检测出木马文件数量为{}".format(len(file_paths)),
                "木马文件路径如下："
            ]

            # 添加所有文件路径
            alert_msg.extend(file_paths)

            # 发送告警消息
            from mod.base.push_mod.safe_mod_push import SafeCloudTask
            try:
                SafeCloudTask.do_send(
                    msg_list=alert_msg,
                    wx_msg="检测到{}个木马文件".format(len(file_paths)),
                    wx_thing_type="堡塔云安全中心-木马告警"
                )
            except Exception as e:
                pass

        except Exception as e:
            pass

    def test_alarm_send(self, get) -> dict:
        """测试告警发送
        @time: 2025-02-19
        @return dict
        """
        try:
            # 检查告警配置是否已启用
            alert_config = self.__config.config.get('alertable', {})
            if not alert_config.get('status', False):
                return public.returnMsg(False, '告警功能未启用，请先启用告警功能')

            if not alert_config.get('sender'):
                return public.returnMsg(False, '未配置告警方式，请先配置告警方式')

            # 构造测试消息
            test_msg = [
                "【安全告警测试】",
                "这是一条测试消息，用于验证告警配置是否正常。",
                "当前告警方式: {}".format(','.join(alert_config['sender'])),
                "发送时间: {}".format(time.strftime('%Y-%m-%d %H:%M:%S'))
            ]

            # 发送测试消息
            from mod.base.push_mod.safe_mod_push import SafeCloudTask
            try:
                SafeCloudTask.do_send(
                    msg_list=test_msg,
                    wx_msg="安全告警测试消息",
                    wx_thing_type="堡塔云安全中心-测试告警"
                )
                return public.returnMsg(True, '测试消息发送成功')
            except Exception as e:
                return public.returnMsg(False, '测试消息发送失败: {}'.format(str(e)))

        except Exception as e:
            return public.returnMsg(False, '执行告警测试时发生错误: {}'.format(str(e)))

    def GetCheckUrl(self):
        '''
            @time: 2025-02-19
            @name 获取云端URL地址
            @author lkq<2022-4-12>
            @return URL
        '''
        try:

            ret = requests.get('http://www.bt.cn/checkWebShell.php').json()
            if ret['status']:
                return ret['url']
            return False
        except:
            return False

    def ReadFile(self, filepath, mode='r'):
        '''
            @time: 2025-02-19
            @name 读取文件内容
            @param filepath 文件路径
            @return 文件内容
        '''
        import os
        if not os.path.exists(filepath): return False
        try:
            fp = open(filepath, mode)
            f_body = fp.read()
            fp.close()
        except Exception as ex:
            if sys.version_info[0] != 2:
                try:
                    fp = open(filepath, mode, encoding="utf-8")
                    f_body = fp.read()
                    fp.close()
                except Exception as ex2:
                    return False
            else:
                return False
        return f_body

    def test_file(self, get):
        '''
            @time: 2025-02-19
            @name 测试文件是否为木马
            @param get.filepath 要检测的文件路径
            @return dict
        '''
        try:
            # 验证参数
            if not hasattr(get, 'filepath'):
                return public.returnMsg(False, '请提供要检测的文件路径!')

            filepath = get.filepath
            if not os.path.exists(filepath):
                return public.returnMsg(False, '文件不存在: {}'.format(filepath))

            # 获取文件大小
            file_size = os.path.getsize(filepath)
            if file_size > 1024000:  # 1MB限制
                return public.returnMsg(False, '文件大小超过限制(1MB)')

            # 获取云端检测URL
            url = self.GetCheckUrl()
            if not url:
                return public.returnMsg(False, '获取云端检测地址失败')

            # 进行云端检测
            try:
                # 准备上传数据
                upload_data = {
                    'inputfile': self.ReadFile(filepath),
                    'md5': self.FileMd5(filepath)
                }

                # 发送检测请求
                upload_res = requests.post(url, upload_data, timeout=20).json()

                # 处理响应结果
                if upload_res['msg'] == 'ok':
                    is_webshell = upload_res['data']['data']['level'] == 5
                    return {
                        'status': True,
                        'msg': '检测完成',
                        'data': {
                            'filepath': filepath,
                            'is_webshell': is_webshell,
                            'level': upload_res['data']['data']['level'],
                            'md5': upload_data['md5']
                        }
                    }
                else:
                    return public.returnMsg(False, '云端检测失败: {}'.format(upload_res['msg']))

            except Exception as e:
                return public.returnMsg(False, '云端检测请求失败: {}'.format(str(e)))

        except Exception as e:
            # logging.error("Error in test_file: {}".format(str(e)))
            return public.returnMsg(False, '测试过程发生错误: {}'.format(str(e)))

    # 移动到回收站
    def Mv_Recycle_bin(self, path):
        if not os.path.islink(path):
            path = os.path.realpath(path)
        rPath = public.get_recycle_bin_path(path)
        rFile = os.path.join(rPath, path.replace('/', '_bt_') + '_t_' + str(time.time()))
        try:
            import shutil
            shutil.move(path, rFile)
            public.WriteLog('TYPE_FILE', 'FILE_MOVE_RECYCLE_BIN', (path,))
            return True
        except:
            public.WriteLog(
                'TYPE_FILE', 'FILE_MOVE_RECYCLE_BIN_ERR', (path,))
            return False

    def deal_webshell_file(self, get):
        """
        @name 批量处理恶意文件（删除文件及对应日志）
        @author wpl
        @param file_list: [{"filepath": "/path/file.php", "md5": "a1b2c3..."}, ...]
        @param action_type: "delete"  # 预留其他操作类型
        @return 处理结果及详细报告
        """
        result = {
            "status": True,
            "success": [],
            "failed": [],
            "total": 0,
            "log_modified": False,
            "log_entries_removed": []  # 新增：记录被删除的日志条目
        }

        try:
            # 参数校验
            if not hasattr(get, 'file_list'):
                return public.returnMsg(False, "缺少必要参数: file_list")

            try:
                if isinstance(get.file_list, str):
                    file_list = json.loads(get.file_list)
                else:
                    file_list = get.file_list
            except Exception as e:
                return public.returnMsg(False, "文件列表解析失败: {}".format(str(e)))

            if not isinstance(file_list, list) or len(file_list) == 0:
                return public.returnMsg(False, "文件列表格式错误")

            result['total'] = len(file_list)

            # 校验文件列表格式
            valid_files = []
            for item in file_list:
                if not isinstance(item, dict) or 'filepath' not in item or 'md5' not in item:
                    result['failed'].append({
                        "filepath": str(item.get('filepath', '')),
                        "md5": str(item.get('md5', '')),
                        "reason": "参数格式错误"
                    })
                    continue
                valid_files.append(item)

            if not valid_files:
                return public.returnMsg(False, "无有效待处理文件")

            # 首先处理日志文件
            log_path = os.path.join(self.__log_dir, "detection_all.log")
            if os.path.exists(log_path):
                try:
                    # 使用文件锁保证原子操作
                    with open(log_path, 'r+') as f:
                        fcntl.flock(f, fcntl.LOCK_EX)
                        try:
                            # 读取全部日志
                            remaining_lines = []
                            removed_lines = []

                            for line in f:
                                line = line.strip()
                                if not line:
                                    continue

                                # 解析日志行
                                parts = line.split('|')
                                if len(parts) < 9:
                                    remaining_lines.append(line + '\n')
                                    continue

                                log_filepath = parts[1]
                                log_md5 = parts[3].lower()

                                # 检查是否需要删除该记录
                                should_remove = False
                                for file_info in valid_files:
                                    target_path = os.path.normpath(file_info['filepath'])
                                    target_md5 = file_info['md5'].lower()

                                    if (os.path.normpath(log_filepath) == target_path and
                                            log_md5 == target_md5):
                                        should_remove = True
                                        removed_lines.append({
                                            'filepath': log_filepath,
                                            'md5': log_md5,
                                            'full_log': line
                                        })
                                        break

                                if not should_remove:
                                    remaining_lines.append(line + '\n')

                            # 更新日志文件
                            f.seek(0)
                            f.writelines(remaining_lines)
                            f.truncate()

                            result['log_modified'] = True
                            result['log_entries_removed'] = removed_lines

                        finally:
                            fcntl.flock(f, fcntl.LOCK_UN)

                except Exception as e:
                    # logging.error("处理日志文件时出错: {}".format(str(e)))
                    result['log_modified'] = False

            # 处理文件删除
            processed_files = set()  # 用于去重 (filepath, md5)
            for file_info in valid_files:
                filepath = file_info['filepath']
                target_md5 = file_info['md5'].lower()

                # 去重检查
                unique_key = (os.path.normpath(filepath), target_md5)
                if unique_key in processed_files:
                    result['failed'].append({
                        "filepath": filepath,
                        "md5": target_md5,
                        "reason": "重复提交"
                    })
                    continue
                processed_files.add(unique_key)

                # 尝试删除文件（如果存在）
                try:
                    if os.path.exists(filepath):
                        # 校验当前文件MD5
                        try:
                            with open(filepath, 'rb') as f:
                                current_md5 = hashlib.md5(f.read()).hexdigest().lower()
                        except Exception as e:
                            result['failed'].append({
                                "filepath": filepath,
                                "md5": target_md5,
                                "reason": "MD5计算失败: {}".format(str(e))
                            })
                            continue

                        # MD5匹配校验
                        if current_md5 != target_md5:
                            result['failed'].append({
                                "filepath": filepath,
                                "md5": target_md5,
                                "reason": "MD5不匹配(当前:{})".format(current_md5)
                            })
                            continue

                        # 执行文件删除
                        try:
                            # os.remove(filepath)
                            # 目前采用转移到回收站，不直接删除，避免删除了正常文件
                            self.Mv_Recycle_bin(filepath)
                            result['success'].append({
                                "filepath": filepath,
                                "md5": target_md5
                            })
                        except Exception as e:
                            result['failed'].append({
                                "filepath": filepath,
                                "md5": target_md5,
                                "reason": "删除失败: {}".format(str(e))
                            })
                    else:
                        # 文件不存在也记录到成功列表，因为目标是移除该文件
                        result['success'].append({
                            "filepath": filepath,
                            "md5": target_md5,
                            "note": "文件已不存在"
                        })

                except Exception as e:
                    result['failed'].append({
                        "filepath": filepath,
                        "md5": target_md5,
                        "reason": "处理过程出错: {}".format(str(e))
                    })

            return {
                "status": True,
                "msg": "处理完成",
                "data": result
            }

        except Exception as e:
            error_msg = "处理过程中发生严重错误: {}".format(str(e))
            # logging.exception(error_msg)
            return {
                "status": False,
                "msg": error_msg,
                "data": result
            }

    def get_safecloud_list(self, get) -> dict:
        # 获取云安全检测 查杀数量
        # 恶意文件检测、漏洞扫描、首页风险
        # 首页风险：/www/server/panel/data/warning/resultresult.json  读取risk里的status为false的
        # 漏洞扫描：/www/server/panel/data/scanning.json，读取loophole_num
        # 恶意文件检测：/www/server/panel/data/safeCloud/log/detection_all.log 只统计高危
        # 总数  累加
        """获取云安全检测统计数据
        @return: dict {
            'total': 总风险数,
            'malware': 恶意文件检测数量,
            'vulnerability': 网站漏洞检测数量,
            'security': 安全风险检测数量,
            'baseline': 基线检测数量,
            'hids': 入侵检测数量,
            "security_score": 安全得分,
            'update_time': 更新时间
        }
        """
        try:
            result = {
                'total': 0,  # 总风险数
                'malware': 0,  # 恶意文件检测数量
                'vulnerability': 0,  # 网站漏洞检测数量
                'security': 0,  # 安全风险检测数量
                'baseline': 0,  # 基线检测数量
                'hids': 0,  # 入侵检测数量
                'security_score': 100,  # 默认安全得分为100
                'update_time': time.strftime('%Y-%m-%d %H:%M:%S')
            }

            # 1. 统计首页风险（security状态为false的数量）
            security_file = '/www/server/panel/data/warning/resultresult.json'
            try:
                if os.path.exists(security_file):
                    security_data = json.loads(public.readFile(security_file))
                    if isinstance(security_data, dict):
                        # 获取首页风险检测得分
                        result['security_score'] = int(security_data.get('score', 100))
                        # 获取检查时间
                        result['check_time'] = security_data.get('check_time', '')
                        # 统计risk中status为false的项目数量
                        if 'risk' in security_data:
                            result['security'] = sum(
                                1 for item in security_data['risk']
                                if isinstance(item, dict) and item.get('status') is False
                            )
            except Exception as e:
                # logging.error("读取安全风险数据失败: {}".format(str(e)))
                pass

            # 2. 统计漏洞扫描数量
            scanning_file = '/www/server/panel/data/scanning.json'
            try:
                if os.path.exists(scanning_file):
                    with open(scanning_file, 'r') as f:
                        scanning_data = json.load(f)
                        result['vulnerability'] = int(scanning_data.get('loophole_num', 0))
            except Exception as e:
                # logging.error("读取漏洞扫描数据失败: {}".format(str(e)))
                pass

            # 3. 统计恶意文件检测数量（高危）
            detection_log = '/www/server/panel/data/safeCloud/log/detection_all.log'
            try:
                if os.path.exists(detection_log):
                    with open(detection_log, 'r') as f:
                        # 读取所有行
                        high_risk_count = 0
                        for line in f:
                            try:
                                if line.strip():
                                    parts = line.strip().split('|')
                                    if len(parts) >= 9:
                                        # 假设风险等级在第5个字段，高危为2
                                        risk_level = parts[4]
                                        if risk_level == '2':  # 高危
                                            high_risk_count += 1
                            except Exception as e:
                                continue
                        result['malware'] = high_risk_count
            except Exception as e:
                # logging.error("读取恶意文件检测数据失败: {}".format(str(e)))
                pass

            # 4. 统计基线检测数量
            safe_detect_file = '/www/server/panel/data/safe_detect.json'
            try:
                if os.path.exists(safe_detect_file):
                    safe_detect_content = public.readFile(safe_detect_file)
                    if safe_detect_content and safe_detect_content != -1:
                        safe_detect_data = json.loads(safe_detect_content)
                        # 获取danger数量
                        result['baseline'] = safe_detect_data.get('risk_count', {}).get('danger', 0)
            except Exception as e:
                # logging.error("读取基线检测数据失败: {}".format(str(e)))
                pass
            # 5. 统计入侵检测数量
            hids_installed = os.path.exists('/www/server/panel/plugin/bt_hids/btpanelhids.sh')
            if hids_installed:
                try:
                    # 统计高危和中危数量
                    high_risk = public.M('risk').dbfile('bt_hids').where('level=?', ('high',)).count()
                    medium_risk = public.M('risk').dbfile('bt_hids').where('level=?', ('medium',)).count()
                    result['hids'] = high_risk + medium_risk
                except Exception as e:
                    # logging.error("读取入侵检测数据失败: {}".format(str(e)))
                    pass

            # 计算总数
            result['total'] = (
                    result['security'] +
                    result['vulnerability'] +
                    result['malware'] +
                    result['baseline'] +
                    result['hids']
            )

            return {
                'status': True,
                'msg': '获取成功',
                'data': result
            }

        except Exception as e:
            # logging.error("获取安全检测统计失败: {}".format(str(e)))
            return {
                'status': False,
                'msg': '获取统计数据失败: {}'.format(str(e)),
                'data': {
                    'total': 0,
                    'malware': 0,
                    'vulnerability': 0,
                    'security': 0,
                    'baseline': 0,
                    'hids': 0,
                    'security_score': 100,
                    'update_time': time.strftime('%Y-%m-%d %H:%M:%S')
                }
            }

    def get_security_logs(self, get) -> dict:
        """获取安全日志统计,功能：首页风险、漏洞扫描、恶意文件检测
        @time: 2025-02-24
        @return: dict 安全日志统计信息
        """
        try:
            result = {
                'home_risks': {
                    'count': 0,
                    'score': 0,
                    'check_time': '',
                    'items': []  # 风险项
                },
                'vulnerabilities': {
                    'site_count': 0,  # 总扫描站点数
                    'risk_count': 0,  # 风险数量
                    'scan_time': '',  # 最近扫描时间
                    'items': []  # 风险项
                },
                'malware': {
                    'count': 0,
                    'last_scan_time': '',
                    'total_scanned': 0,
                    'risk_stats': {},
                    'items': []  # 风险项
                },
                'total': 0,
                'update_time': time.strftime('%Y-%m-%d %H:%M:%S')
            }

            # 1. 读取首页风险
            try:
                risk_file = '/www/server/panel/data/warning/resultresult.json'
                if os.path.exists(risk_file):
                    with open(risk_file, 'r') as f:
                        risk_data = json.load(f)

                        # 获取风险得分和检测时间
                        result['home_risks'].update({
                            'score': risk_data.get('score', 0),
                            'check_time': risk_data.get('check_time', '')
                        })

                        # 获取风险项列表
                        if 'risk' in risk_data:
                            risk_items = []
                            for item in risk_data['risk']:
                                if not isinstance(item, dict):
                                    continue

                                # 只收集状态为 False（有风险）的项
                                if item.get('status', True) is False:
                                    risk_items.append({
                                        'title': item.get('title', '未知风险'),  # 风险标题
                                        'ps': item.get('ps', ''),  # 风险备注
                                        'level': item.get('level', 0),  # 风险等级
                                        'ignore': item.get('ignore', False),  # 是否忽略
                                        'msg': item.get('msg', ''),  # 风险描述
                                        'tips': item.get('tips', []),  # 温馨提示
                                        'remind': item.get('remind', ''),  # 解决方案
                                        'check_time': item.get('check_time', 0)  # 检测时间
                                    })

                            result['home_risks']['items'] = risk_items
                            result['home_risks']['count'] = len(risk_items)
            except Exception as e:
                # logging.error("读取首页风险数据失败: {}".format(str(e)))
                pass

            # 2. 读取漏洞扫描
            try:
                vuln_file = '/www/server/panel/data/scanning.json'
                if os.path.exists(vuln_file):
                    with open(vuln_file, 'r') as f:
                        vuln_data = json.load(f)
                        # 获取基础信息
                        result['vulnerabilities']['site_count'] = vuln_data.get('site_num', 0)
                        result['vulnerabilities']['risk_count'] = vuln_data.get('loophole_num', 0)
                        result['vulnerabilities']['scan_time'] = time.strftime(
                            '%Y-%m-%d %H:%M:%S',
                            time.localtime(vuln_data.get('time', 0))
                        )

                        # 获取具体漏洞信息
                        if 'info' in vuln_data:
                            for site in vuln_data['info']:
                                if 'cms' in site:
                                    for cms in site['cms']:
                                        vuln_item = {
                                            'site_name': site.get('name', ''),
                                            'site_path': site.get('path', ''),
                                            'risk_desc': cms.get('ps', ''),
                                            'risk_level': cms.get('dangerous', 0),
                                            'repair': cms.get('repair', '')
                                        }
                                        result['vulnerabilities']['items'].append(vuln_item)
            except Exception as e:
                # logging.error("读取漏洞扫描数据失败: {}".format(str(e)))
                pass

            # 3. 读取恶意文件检测
            try:
                webshell_result = self.get_webshell_result(get)
                if webshell_result.get('status', False):
                    result['malware'] = {
                        'count': webshell_result.get('total_detected', 0),
                        'last_scan_time': webshell_result.get('last_scan_time', ''),
                        'total_scanned': webshell_result.get('total_scanned_files', 0),
                        'risk_stats': webshell_result.get('risk_stats', {}),
                        'items': webshell_result.get('detected', [])
                    }
            except Exception as e:
                # logging.error("读取恶意文件检测数据失败: {}".format(str(e)))
                pass

            # 计算总风险数
            result['total'] = (
                    result['home_risks']['count'] +
                    result['vulnerabilities']['risk_count'] +
                    result['malware']['count']
            )

            return {
                'status': True,
                'msg': '获取成功',
                'data': result
            }

        except Exception as e:
            # logging.error("获取安全日志统计失败: {}".format(str(e)))
            return {
                'status': False,
                'msg': '获取统计数据失败: {}'.format(str(e)),
                'data': result
            }

    # 4. 统计企业防篡改
    def get_tamper_stats(self):
        """获取企业防篡改统计数据"""
        try:
            tamper_file = '/www/server/tamper/total/total.json'
            if not os.path.exists(tamper_file):
                return 0, False

            tamper_data = json.loads(public.readFile(tamper_file))
            if not isinstance(tamper_data, dict):
                return 0, False

            # 统计所有拦截操作的总和
            total_blocks = sum([
                tamper_data.get('create', 0),
                tamper_data.get('modify', 0),
                tamper_data.get('unlink', 0),
                tamper_data.get('rename', 0),
                tamper_data.get('mkdir', 0),
                tamper_data.get('rmdir', 0),
                tamper_data.get('chmod', 0),
                tamper_data.get('chown', 0),
                tamper_data.get('link', 0)
            ])

            return total_blocks, True
        except Exception as e:
            return 0, False

    def get_virus_db_time(self):
        """获取病毒库更新时间"""
        try:
            rules_dir = '/www/server/panel/data/safeCloud/rules'
            if not os.path.exists(rules_dir):
                return ''

            # 获取rules目录的最后修改时间
            mtime = os.path.getmtime(rules_dir)
            return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mtime))
        except:
            return ''

    def get_protect_days(self):
        """获取保护天数"""
        try:
            protect_file = '/www/server/panel/data/safeCloud/install_time.pl'

            # 如果文件不存在，创建并记录当前时间
            if not os.path.exists(protect_file):
                install_time = time.time()
                public.writeFile(protect_file, str(install_time))
            else:
                install_time = float(public.readFile(protect_file))

            # 计算保护天数

            protect_days = int((time.time() - install_time) / 86400)
            return max(protect_days, 1)  # 确保不会返回负数

        except Exception as e:
            return 1

    def get_hids_risk_count(self):
        """获取入侵检测高中危告警总数
        @return: (int) 告警总数, (bool) 服务状态
        """
        try:
            # 统计高危和中危
            high_risk = public.M('risk').dbfile('bt_hids').where('level=?', ('high',)).count()
            medium_risk = public.M('risk').dbfile('bt_hids').where('level=?', ('medium',)).count()
            risk_count = high_risk + medium_risk

            return risk_count, True

        except Exception as e:
            return 0, False

    def get_security_status(self) -> dict:
        """获取所有安全功能的状态
        @return: dict {
            'vul_scan': bool,       # 漏洞扫描状态
            'tamper': bool,         # 企业防篡改状态
            'tamper_installed': bool,  # 企业防篡改安装状态
            'file_detection': bool, # 恶意文件检测状态
            'hids': bool,          # 入侵检测状态
            'hids_installed': bool,    # 入侵检测安装状态
            'risk_scan': bool,     # 首页风险扫描（默认开启）
            'safe_detect': bool    # 服务器安全检测（默认开启）
        }
        """
        try:
            status = {
                'risk_scan': True,  # 首页风险扫描默认开启
                'safe_detect': True,  # 服务器安全检测默认开启
                'vul_scan': False,
                'tamper': False,
                'tamper_installed': False,  # 企业防篡改安装状态
                'file_detection': False,
                'hids': False,
                'hids_installed': False  # 入侵检测安装状态
            }

            # 1. 检查漏洞扫描状态
            try:
                if "/www/server/panel" not in sys.path:
                    sys.path.insert(0, '/www/server/panel')
                from mod.base.push_mod import TaskConfig
                res = TaskConfig().get_by_keyword("vulnerability_scanning", "vulnerability_scanning")
                status['vul_scan'] = bool(res and int(res.get('status', 0)) == 1)
            except:
                pass

            # 2. 检查企业防篡改状态
            try:
                # 检查安装状态
                status['tamper_installed'] = os.path.exists('/www/server/panel/plugin/tamper_core/install.sh')

                kernel_loaded = bool(public.ExecShell("lsmod | grep tampercore")[0].strip())
                controller_running = bool(public.ExecShell("ps aux | grep tamperuser | grep -v grep")[0].strip())
                status['tamper'] = kernel_loaded and controller_running
            except:
                pass

            # 3. 检查恶意文件检测状态
            try:
                config_file = '/www/server/panel/data/safeCloud/config.json'
                if os.path.exists(config_file):
                    config = json.loads(public.readFile(config_file))
                    status['file_detection'] = bool(config.get('dynamic_detection'))
            except:
                pass

            # 4. 检查入侵检测状态
            try:
                # 检查安装状态
                status['hids_installed'] = os.path.exists('/www/server/panel/plugin/bt_hids/btpanelhids.sh')

                # 检查进程和内核模块
                process_running = bool(public.ExecShell(
                    "ps aux |grep '/bt_hids/load_hids.py'|grep -v grep")[0].strip())
                kernel_loaded = bool(public.ExecShell("lsmod | grep hids_driver")[0].strip())

                # 检查状态文件
                status_file = '/www/server/panel/data/hids_data/status.pl'
                if os.path.exists(status_file):
                    file_status = public.readFile(status_file).strip() == 'True'
                else:
                    file_status = False

                status['hids'] = process_running and kernel_loaded and file_status
            except:
                pass

            return status

        except Exception as e:
            # 返回所有功能默认关闭的状态（除了首页风险和服务器安全检测）
            return {
                'risk_scan': True,
                'safe_detect': True,
                'vul_scan': False,
                'tamper': False,
                'tamper_installed': False,  # 添加安装状态默认值
                'file_detection': False,
                'hids': False,
                'hids_installed': False,  # 添加安装状态默认值
            }

    def _calculate_dynamic_deduction(self, risk_details: dict) -> dict:
        """计算动态扣分（基于优先级的叠加式扣分）"""
        try:
            deduction = 0
            deductions = []
            suggestions = []

            # 1. 基线检查优先级（首页风险和服务器安全检测）
            baseline_risks = (
                    risk_details.get('homepage_risk', {}).get('total', 0) +
                    risk_details.get('safe_detect', {}).get('total', 0)
            )
            if baseline_risks > 0:
                deduction += 3
                deductions.append({
                    'type': '服务器风险',
                    'deduction': 3,
                    'details': "存在{}个未处理的服务器风险".format(baseline_risks)
                })
                suggestions.append("建议优先处理基线检查发现的风险")

            # 2. 漏洞修复优先级
            vul_risks = risk_details.get('vul_scan', {}).get('total', 0)
            if vul_risks > 0:
                deduction += 2
                deductions.append({
                    'type': '漏洞风险',
                    'deduction': 2,  # 漏洞风险扣分
                    'details': "存在{}个待修复漏洞".format(vul_risks)
                })
                suggestions.append("建议及时修复系统漏洞")

            # 3. 告警处理优先级（入侵检测告警）
            hids_risks = risk_details.get('hids', {}).get('total', 0)
            if hids_risks > 0:
                deduction += 2
                deductions.append({
                    'type': '入侵检测',
                    'deduction': 2,
                    'details': "存在{}个未处理告警".format(hids_risks)
                })
                suggestions.append("建议及时处理入侵检测告警")

            return {
                'deduction': deduction,
                'deductions': deductions,
                'suggestions': suggestions
            }
        except Exception as e:
            return {'deduction': 0, 'deductions': [], 'suggestions': []}

    def _calculate_time_decay(self, risk_details: dict) -> dict:
        """计算时间衰减（基于风险存在时间）"""
        try:
            deduction = 0
            deductions = []

            # 获取各模块最早的未处理风险时间
            risk_times = {}

            # 1. 检查首页风险时间
            try:
                risk_file = '/www/server/panel/data/warning/resultresult.json'
                if os.path.exists(risk_file):
                    risk_data = json.loads(public.readFile(risk_file))
                    for risk in risk_data.get('risk', []):
                        if not risk.get('status', True):  # 未处理的风险
                            risk_times['homepage_risk'] = risk.get('time', 0)
                            break
            except:
                pass

            # 2. 检查漏洞扫描时间
            try:
                vul_file = '/www/server/panel/data/scanning.json'
                if os.path.exists(vul_file):
                    vul_data = json.loads(public.readFile(vul_file))
                    risk_times['vul_scan'] = vul_data.get('time', 0)
            except:
                pass

            # 计算时间衰减
            current_time = time.time()
            for module, risk_time in risk_times.items():
                if not risk_time:
                    continue

                days = (current_time - risk_time) / 86400
                if days > 15:  # 超过15天
                    decay = 1.5
                elif days > 7:  # 超过7天
                    decay = 1.2
                else:
                    continue

                # 获取模块原始扣分
                module_deduction = risk_details.get(module, {}).get('total', 0)
                if module_deduction > 0:
                    extra_deduction = module_deduction * (decay - 1)
                    deduction += extra_deduction
                    deductions.append({
                        'type': "{}时间衰减".format(module),
                        'deduction': round(extra_deduction, 1),
                        'details': "风险存在{}天，扣分系数×{}".format(int(days), decay)
                    })

            return {
                'deduction': round(deduction, 1),
                'deductions': deductions
            }
        except Exception as e:
            return {'deduction': 0, 'deductions': []}

    def _calculate_rewards(self) -> dict:
        """计算奖励分数（基于安全行为）"""
        try:
            bonus = 0
            details = []

            # 1. 连续30天无新增风险（+5分）
            if self._check_no_new_risks(30):
                bonus += 5
                details.append({
                    'type': '安全运营',
                    'bonus': 5,
                    'details': '连续30天无新增风险'
                })

            # 2. 基线检查全部达标（+3分）
            if self._check_baseline_compliance():
                bonus += 3
                details.append({
                    'type': '基线达标',
                    'bonus': 3,
                    'details': '所有基线检查项达标'
                })

            # 3. 用户互动奖励（暂不实现）

            return {
                'bonus': min(8, bonus),  # 总奖励上限8分
                'details': details
            }
        except Exception as e:
            return {'bonus': 0, 'details': []}

    def _check_no_new_risks(self, days: int) -> bool:
        """检查指定天数内是否无新增风险"""
        try:
            start_time = time.time() - (days * 86400)

            # 检查各模块新增风险
            # 1. 检查入侵检测
            hids_new = public.M('risk').dbfile('bt_hids').where('time>?', (start_time,)).count()
            if hids_new > 0:
                return False

            # 2. 检查恶意文件
            malware_log = '/www/server/panel/data/safeCloud/log/detection_all.log'
            if os.path.exists(malware_log):
                with open(malware_log, 'r') as f:
                    for line in f:
                        if float(line.split('|')[0]) > start_time:
                            return False

            # 3. 检查其他模块...

            return True

        except Exception as e:
            return False

    def _check_baseline_compliance(self) -> bool:
        """检查基线是否全部达标"""
        try:
            # 1. 检查首页风险
            risk_file = '/www/server/panel/data/warning/resultresult.json'
            if os.path.exists(risk_file):
                risk_data = json.loads(public.readFile(risk_file))
                if any(not risk.get('status', True) for risk in risk_data.get('risk', [])):
                    return False

            # 2. 检查服务器安全检测
            safe_file = '/www/server/panel/data/safe_detect.json'
            if os.path.exists(safe_file):
                safe_data = json.loads(public.readFile(safe_file))
                if safe_data.get('risk_count', {}).get('danger', 0) > 0:
                    return False

            return True

        except Exception as e:
            return False

    def _calculate_security_score(self, risk_details: dict) -> dict:
        """计算安全评分和等级
        @param risk_details: dict 各模块风险详情
        @return: dict {
            'score': int,          # 安全评分(0-100)
            'level': str,          # 安全等级
            'level_description': str,    # 等级描述
            'deductions': list,    # 扣分详情
            'suggestions': list,   # 改进建议
            'rewards': list       # 奖励详情
        }
        """
        try:
            # 1. 基础评分计算
            base_score = 100
            deductions = []  # 记录扣分详情
            suggestions = []  # 记录改进建议

            # 2. 计算各模块扣分
            module_scores = self._calculate_module_scores(risk_details)
            base_score -= module_scores['total_deduction']
            deductions.extend(module_scores['deductions'])
            suggestions.extend(module_scores['suggestions'])

            # 3. 计算动态扣分
            dynamic_result = self._calculate_dynamic_deduction(risk_details)
            base_score -= dynamic_result['deduction']
            deductions.extend(dynamic_result['deductions'])
            suggestions.extend(dynamic_result['suggestions'])

            # 4. 计算时间衰减
            decay_result = self._calculate_time_decay(risk_details)
            base_score -= decay_result['deduction']
            deductions.extend(decay_result['deductions'])

            # 5. 计算奖励分数
            rewards = self._calculate_rewards()
            base_score += rewards['bonus']

            # 6. 确保分数在0-100范围内
            final_score = max(0, min(100, int(base_score)))

            # 7. 确定安全等级
            level_info = self._get_security_level(final_score)

            return {
                'score': final_score,
                'level': level_info['level'],
                'level_description': level_info['level_description'],
                'deductions': deductions,
                'suggestions': suggestions,
                'rewards': rewards['details']
            }

        except Exception as e:
            return {
                'score': 100,
                'level': '安全',
                'level_description': '当前系统安全状态良好，所有安全措施均已落实，无明显漏洞或风险。建议定期进行安全检查以保持此状态',
                'deductions': [],
                'suggestions': [],
                'rewards': []
            }

    def _calculate_module_scores(self, risk_details: dict) -> dict:
        """计算各模块扣分"""
        SCORE_CONFIG = {
            'homepage_risk': {
                'high': 3,
                'medium': 2,
                'limit': 20,
                'weight': 1.2,
                'name': '首页风险'
            },
            'file_detection': {
                'high': 4,
                'medium': 2,
                'limit': 30,
                'weight': 1.0,
                'name': '恶意文件检测'
            },
            'vul_scan': {
                'per_risk': 3,
                'limit': 15,
                'weight': 1.0,
                'name': '漏洞扫描'
            },
            'safe_detect': {
                'high': 3,
                'medium': 2,
                'limit': 15,
                'weight': 1.0,
                'name': '服务器安全检测'
            },
            'hids': {
                'high': 4,
                'medium': 2,
                'limit': 15,
                'weight': 1.3,
                'name': '入侵检测'
            }
        }

        total_deduction = 0
        deductions = []
        suggestions = []

        try:
            for module, config in SCORE_CONFIG.items():
                if module not in risk_details:
                    continue

                module_data = risk_details[module]
                if not isinstance(module_data, dict):
                    continue

                module_deduction = 0

                # 漏洞扫描使用特殊的计分逻辑
                if module == 'vul_scan':
                    total_vuls = int(module_data.get('total', 0))
                    if total_vuls > 0:
                        module_deduction = total_vuls * config['per_risk'] * config['weight']
                        # 应用上限
                        original_deduction = module_deduction
                        module_deduction = min(module_deduction, config['limit'])

                        if module_deduction > 0:
                            deductions.append({
                                'module': config['name'],
                                'deduction': round(module_deduction, 1),
                                'details': "发现{}个漏洞".format(total_vuls)
                            })

                        if original_deduction > config['limit']:
                            suggestions.append(
                                "建议优先处理{}的漏洞，可提升{}分".format(config['name'],
                                                                         int(original_deduction - module_deduction))
                            )
                else:
                    # 其他模块使用高中危计分逻辑
                    high_count = int(module_data.get('high', 0))
                    medium_count = int(module_data.get('medium', 0))

                    module_deduction = (
                                               high_count * config['high'] +
                                               medium_count * config['medium']
                                       ) * config['weight']

                    # 应用单模块上限
                    original_deduction = module_deduction
                    module_deduction = min(module_deduction, config['limit'])

                    if module_deduction > 0:
                        deductions.append({
                            'module': config['name'],
                            'deduction': round(module_deduction, 1),
                            'details': "高危{}个, 中危{}个".format(high_count, medium_count)
                        })

                        if original_deduction > config['limit']:
                            suggestions.append(
                                "建议优先处理{}的风险，可提升{}分".format(config['name'],
                                                                         int(original_deduction - module_deduction))
                            )

                total_deduction += module_deduction

            return {
                'total_deduction': round(total_deduction, 1),
                'deductions': deductions,
                'suggestions': suggestions
            }

        except Exception as e:
            return {
                'total_deduction': 0,
                'deductions': [],
                'suggestions': []
            }

    def _get_security_level(self, score: int) -> dict:
        """根据分数获取安全等级
        @param score: int 安全评分
        @return: dict {
            'level': str,       # 安全等级
            'level_description': str        # 等级描述
        }
        """
        try:
            if score >= 90:
                return {
                    'level': '安全',
                    'level_description': '当前系统安全状态良好，所有安全措施均已落实，无明显漏洞或风险。建议定期进行安全检查以保持此状态'
                }
            elif score >= 80:
                return {
                    'level': '待加固',
                    'level_description': '系统存在一定安全隐患，需对部分配置或策略进行改进。建议尽快修复发现的问题以防止潜在风险扩大'
                }
            elif score >= 60:
                return {
                    'level': '中风险',
                    'level_description': '系统存在较明显的安全漏洞，可能被利用导致数据泄露或服务中断。需紧急处理并加强防护措施'
                }
            else:
                return {
                    'level': '高风险',
                    'level_description': '系统处于高风险状态，您的资产已经显露在黑客入侵和病毒感染的风险下，请您尽快处理'
                }
        except Exception as e:
            return {'level': '安全',
                    'level_description': '当前系统安全状态良好，所有安全措施均已落实，无明显漏洞或风险。建议定期进行安全检查以保持此状态'}

    def _check_no_new_risks_days(self, days: int) -> bool:
        """检查指定天数内是否无新增风险
        @param days: int 天数
        @return: bool 是否无新增风险
        """
        try:
            start_time = time.time() - (days * 86400)

            # 检查各模块新增风险
            # 1. 检查入侵检测
            hids_new = public.M('risk').dbfile('bt_hids').where('time>?', (start_time,)).count()
            if hids_new > 0:
                return False

            # 2. 检查恶意文件
            malware_log = '/www/server/panel/data/safeCloud/log/detection_all.log'
            if os.path.exists(malware_log):
                with open(malware_log, 'r') as f:
                    for line in f:
                        if float(line.split('|')[0]) > start_time:
                            return False

            # 3. 检查其他模块...

            return True

        except Exception as e:
            return False

    def get_safe_overview(self, get) -> dict:
        """获取安全总览统计数据
        @time: 2025-03-11
        @return: dict {
            'score': int,          # 安全评分(0-100)
            'level': str,          # 安全等级
            'level_description': str,    # 等级描述
            'risk_count': int,     # 风险总数
            'protect_days': int,   # 保护天数
            'virus_update_time': str,  # 病毒库更新时间
            'risk_scan_time': str,     # 首页风险扫描时间
            'security_status': dict,   # 安全功能状态
            'risk_details': dict,      # 各模块风险详情
            'score_details': dict      # 评分详情
        }
        """
        try:
            result = {
                "score": 100,
                "level": "安全",
                "level_description": "当前系统安全状态良好，所有安全措施均已落实，无明显漏洞或风险。建议定期进行安全检查以保持此状态",
                "risk_count": 0,
                "protect_days": 1,
                "virus_update_time": "",
                "risk_scan_time": "",
                "security_status": self.get_security_status(),
                "risk_details": {
                    "homepage_risk": {
                        "high": 0,
                        "medium": 0,
                        "total": 0
                    },
                    "vul_scan": {
                        "high": 0,
                        "medium": 0,
                        "total": 0
                    },
                    "hids": {
                        "high": 0,
                        "medium": 0,
                        "total": 0
                    },
                    "safe_detect": {
                        "high": 0,
                        "medium": 0,
                        "total": 0
                    },
                    "tamper": {
                        "total": 0
                    },
                    "file_detection": {
                        "high": 0,
                        "medium": 0,
                        "total": 0
                    }
                },
                "score_details": {
                    "deductions": [],
                    "suggestions": [],
                    "rewards": []
                }
            }

            # 1. 统计首页风险
            try:
                risk_file = '/www/server/panel/data/warning/resultresult.json'
                if os.path.exists(risk_file):
                    risk_data = json.loads(public.readFile(risk_file))
                    check_time = risk_data.get('check_time', '')
                    if check_time and isinstance(check_time, str):
                        # Replace / with - in date portion while preserving time portion
                        try:
                            date_part, time_part = check_time.split(' ', 1)
                            standardized_date = date_part.replace('/', '-')
                            result['risk_scan_time'] = "{} {}".format(standardized_date, time_part)
                        except Exception:
                            # Fallback if format is unexpected
                            result['risk_scan_time'] = check_time
                    else:
                        result['risk_scan_time'] = check_time
                    # 只统计未处理的风险(status=False)
                    high_risk = sum(1 for risk in risk_data.get('risk', [])
                                    if not risk.get('status', True))
                    result['risk_details']['homepage_risk'].update({
                        'high': high_risk,
                        'total': high_risk
                    })
            except Exception as e:
                pass

            # 2. 统计漏洞扫描
            try:
                vul_file = '/www/server/panel/data/scanning.json'
                if os.path.exists(vul_file):
                    vul_data = json.loads(public.readFile(vul_file))
                    total_vuls = vul_data.get('loophole_num', 0)
                    result['risk_details']['vul_scan'].update({
                        'total': total_vuls
                    })
            except Exception as e:
                pass

            # 3. 统计入侵检测
            try:
                high_risk, medium_risk = public.M('risk').dbfile('bt_hids').where('level=?', ('high',)).count(), \
                    public.M('risk').dbfile('bt_hids').where('level=?', ('medium',)).count()
                result['risk_details']['hids'].update({
                    'high': high_risk,
                    'medium': medium_risk,
                    'total': high_risk + medium_risk
                })
            except Exception as e:
                pass

            # 4. 统计服务器安全检测
            try:
                safe_file = '/www/server/panel/data/safe_detect.json'
                if os.path.exists(safe_file):
                    safe_data = json.loads(public.readFile(safe_file))
                    danger_count = safe_data.get('risk_count', {}).get('danger', 0)
                    result['risk_details']['safe_detect'].update({
                        'high': danger_count,
                        'total': danger_count
                    })
            except Exception as e:
                pass

            # 5. 统计企业防篡改
            try:
                tamper_blocks, _ = self.get_tamper_stats()
                result['risk_details']['tamper']['total'] = tamper_blocks
            except Exception as e:
                pass

            # 6. 统计恶意文件检测
            try:
                detection_log = '/www/server/panel/data/safeCloud/log/detection_all.log'
                if os.path.exists(detection_log):
                    with open(detection_log, 'r') as f:
                        total_detections = len(f.readlines())
                        result['risk_details']['file_detection'].update({
                            'high': total_detections,
                            'total': total_detections
                        })
            except Exception as e:
                pass

            # 7. 计算总风险数（只统计指定模块）
            risk_modules = {
                'homepage_risk',  # 首页风险
                'vul_scan',  # 漏洞扫描
                'hids',  # 入侵检测
                'safe_detect',  # 服务器安全检测
                'file_detection'  # 恶意文件检测
            }
            result['risk_count'] = sum(
                result['risk_details'][module]['total']
                for module in risk_modules
                if module in result['risk_details']
            )

            # 8. 计算安全评分和等级
            score_result = self._calculate_security_score(result['risk_details'])
            result.update({
                'score': score_result['score'],
                'level': score_result['level'],
                'level_description': score_result['level_description'],
                'score_details': {
                    'deductions': score_result['deductions'],
                    'suggestions': score_result['suggestions'],
                    'rewards': score_result['rewards']
                }
            })

            # 9. 获取保护天数
            result['protect_days'] = self.get_protect_days()

            # 10. 获取病毒库更新时间
            result['virus_update_time'] = self.get_virus_db_time()

            return result

        except Exception as e:
            return {
                "score": 100,
                "level": "安全",
                "level_description": "当前系统安全状态良好，所有安全措施均已落实，无明显漏洞或风险。建议定期进行安全检查以保持此状态",
                "risk_count": 0,
                "protect_days": 1,
                "virus_update_time": "",
                "risk_scan_time": "",
                "security_status": self.get_security_status(),
                "risk_details": {},
                "score_details": {
                    "deductions": [],
                    "suggestions": [],
                    "rewards": []
                }
            }

    def _should_update_trend(self, trend_file: str, interval: int) -> bool:
        """检查是否需要更新趋势数据
        @param trend_file: str 趋势数据文件路径
        @param interval: int 更新间隔(秒)
        @return: bool 是否需要更新
        """
        try:
            if not os.path.exists(trend_file):
                return True

            # 获取文件最后修改时间
            mtime = os.path.getmtime(trend_file)
            current_time = time.time()

            # 如果距离上次更新超过间隔时间，则需要更新
            return (current_time - mtime) > interval
        except:
            return True

    def get_pending_alarm_trend(self, get) -> dict:
        """获取待处理告警趋势"""
        try:
            trend_file = '/www/server/panel/data/safeCloud/alarm_trend.json'
            UPDATE_INTERVAL = 6 * 3600  # 更新间隔6小时（秒）
            MAX_POINTS = 28  # 最大保留点数（7天*4次/天）
            current_time = int(time.time())

            # 1. 获取当前风险统计
            risk_counts = self._get_risk_counts()
            current_total = risk_counts['high_risk'] + risk_counts['medium_risk'] + risk_counts['low_risk']

            # 2. 处理趋势数据
            trend_data = []
            need_update = False

            # 2.1 读取现有数据（如果存在）
            if os.path.exists(trend_file):
                try:
                    file_content = public.readFile(trend_file)
                    if file_content and file_content != -1:
                        trend_data = json.loads(file_content)

                        # 检查是否需要更新
                        last_update_time = trend_data[-1]['timestamp'] if trend_data else 0
                        last_count = trend_data[-1]['count'] if trend_data else 0

                        # 如果时间间隔超过更新间隔或者总数发生变化，需要更新
                        need_update = (current_time - last_update_time > UPDATE_INTERVAL) or (
                                current_total != last_count)
                    else:
                        need_update = True
                except:
                    need_update = True
            else:
                # 2.2 文件不存在，创建初始数据
                need_update = True

            # 3. 如果需要更新，准备新数据
            if need_update:
                # 如果是新文件或数据无效，创建初始数据
                if not trend_data:
                    trend_data = [
                        {'timestamp': current_time, 'count': current_total},
                        {'timestamp': current_time, 'count': current_total}
                    ]
                else:
                    # 添加新数据点
                    trend_data.append({
                        'timestamp': current_time,
                        'count': current_total
                    })

                    # 限制数据点数量
                    if len(trend_data) > MAX_POINTS:
                        trend_data = trend_data[-MAX_POINTS:]

                # 确保目录存在
                trend_dir = os.path.dirname(trend_file)
                if not os.path.exists(trend_dir):
                    os.makedirs(trend_dir, mode=0o755, exist_ok=True)

                # 写入新数据（只保存趋势列表）
                public.writeFile(trend_file, json.dumps(trend_data))

            # 4. 返回数据
            return {
                'total': current_total,
                'high_risk': risk_counts['high_risk'],
                'medium_risk': risk_counts['medium_risk'],
                'low_risk': risk_counts['low_risk'],
                'trend_list': trend_data
            }

        except Exception as e:
            # 确保返回有效的初始数据
            current_time = int(time.time())
            return {
                'total': 0,
                'high_risk': 0,
                'medium_risk': 0,
                'low_risk': 0,
                'trend_list': [
                    {'timestamp': current_time, 'count': 0},
                    {'timestamp': current_time, 'count': 0}
                ]
            }

    def _get_risk_counts(self) -> dict:
        """获取各安全模块的风险统计
        @return: dict {
            'high_risk': int,
            'medium_risk': int,
            'low_risk': int
        }
        """
        result = {
            'high_risk': 0,
            'medium_risk': 0,
            'low_risk': 0
        }

        try:
            # 1. 首页风险检测
            try:
                risk_file = '/www/server/panel/data/warning/resultresult.json'
                if os.path.exists(risk_file):
                    risk_data = json.loads(public.readFile(risk_file))
                    result['high_risk'] += sum(1 for risk in risk_data.get('risk', [])
                                               if not risk.get('status', True))
            except Exception as e:
                pass

            # 2. 漏洞扫描
            try:
                vul_file = '/www/server/panel/data/scanning.json'
                if os.path.exists(vul_file):
                    vul_data = json.loads(public.readFile(vul_file))
                    result['medium_risk'] += vul_data.get('loophole_num', 0)
            except Exception as e:
                pass

            # 3. 入侵检测
            try:
                result['high_risk'] += public.M('risk').dbfile('bt_hids').where('level=?', ('high',)).count()
                result['medium_risk'] += public.M('risk').dbfile('bt_hids').where('level=?', ('medium',)).count()
            except Exception as e:
                pass

            # 4. 服务器安全检测
            try:
                safe_file = '/www/server/panel/data/safe_detect.json'
                if os.path.exists(safe_file):
                    safe_data = json.loads(public.readFile(safe_file))
                    result['high_risk'] += safe_data.get('risk_count', {}).get('danger', 0)
            except Exception as e:
                pass

            # 5. 恶意文件检测
            try:
                detection_log = '/www/server/panel/data/safeCloud/log/detection_all.log'
                if os.path.exists(detection_log):
                    with open(detection_log, 'r') as f:
                        result['high_risk'] += len(f.readlines())
            except Exception as e:
                pass

        except Exception as e:
            pass

        return result

    def get_security_trend(self, get) -> dict:
        """获取安全趋势（每24小时更新一次）
        @return: dict {
            'trend_list': list[dict] # 趋势列表
        }
        """
        try:
            trend_file = '/www/server/panel/data/safeCloud/security_trend.json'
            UPDATE_INTERVAL = 24 * 3600  # 更新间隔24小时（秒）
            MAX_POINTS = 7  # 最大保留点数（7天）
            current_time = int(time.time())

            # 1. 检查文件是否存在并读取数据
            trend_data = []
            need_update = False

            if os.path.exists(trend_file):
                try:
                    file_content = public.readFile(trend_file)
                    if file_content and file_content != -1:
                        trend_data = json.loads(file_content)

                        # 检查是否需要更新
                        if trend_data and isinstance(trend_data, list):
                            last_update_time = trend_data[-1].get('timestamp', 0)
                            need_update = (current_time - last_update_time) > UPDATE_INTERVAL
                        else:
                            need_update = True
                    else:
                        need_update = True
                except:
                    need_update = True
            else:
                # 文件不存在，需要创建
                need_update = True

            # 2. 如果不需要更新，直接返回现有数据
            if not need_update and trend_data:
                return {'trend_list': trend_data}

            # 3. 获取最新统计数据
            current_stats = {
                'timestamp': current_time,
                'risk_scan': 0,
                'vul_scan': 0,
                'server_risks': 0,
                'file_detection': 0,
                'hids_risks': 0,
                'unhandled_risks': 0,
                'handled_risks': 0
            }

            # 4. 统计各模块风险数
            try:
                # 首页风险
                risk_file = '/www/server/panel/data/warning/resultresult.json'
                if os.path.exists(risk_file):
                    risk_content = public.readFile(risk_file)
                    if risk_content and risk_content != -1:
                        risk_data = json.loads(risk_content)
                        current_stats['risk_scan'] = sum(1 for risk in risk_data.get('risk', [])
                                                         if not risk.get('status', True))

                # 漏洞扫描
                vul_file = '/www/server/panel/data/scanning.json'
                if os.path.exists(vul_file):
                    vul_content = public.readFile(vul_file)
                    if vul_content and vul_content != -1:
                        vul_data = json.loads(vul_content)
                        current_stats['vul_scan'] = vul_data.get('loophole_num', 0)

                # 服务器安全检测
                safe_file = '/www/server/panel/data/safe_detect.json'
                if os.path.exists(safe_file):
                    safe_content = public.readFile(safe_file)
                    if safe_content and safe_content != -1:
                        safe_data = json.loads(safe_content)
                        current_stats['server_risks'] = safe_data.get('risk_count', {}).get('danger', 0)

                # 恶意文件检测
                detection_log = '/www/server/panel/data/safeCloud/log/detection_all.log'
                if os.path.exists(detection_log):
                    try:
                        with open(detection_log, 'r') as f:
                            current_stats['file_detection'] = len(f.readlines())
                    except:
                        pass

                # 入侵检测
                try:
                    high_risk = public.M('risk').dbfile('bt_hids').where('level=?', ('high',)).count()
                    medium_risk = public.M('risk').dbfile('bt_hids').where('level=?', ('medium',)).count()
                    current_stats['hids_risks'] = high_risk + medium_risk
                except:
                    pass

                # 计算未处理风险总数
                current_total = (
                        current_stats['risk_scan'] +
                        current_stats['vul_scan'] +
                        current_stats['server_risks'] +
                        current_stats['file_detection'] +
                        current_stats['hids_risks']
                )

                # 处理未处理和已处理风险数
                if trend_data and len(trend_data) > 0:
                    last_stats = trend_data[-1]
                    last_unhandled = last_stats.get('unhandled_risks', 0)
                    current_stats['unhandled_risks'] = current_total

                    # 如果当前风险数小于上次，计算已处理数
                    if current_total < last_unhandled:
                        current_stats['handled_risks'] = last_unhandled - current_total
                    else:
                        current_stats['handled_risks'] = last_stats.get('handled_risks', 0)

                    # 检查是否需要更新当天的数据
                    if current_total != last_unhandled:
                        # 判断最后一条记录是否是同一天
                        last_day = time.strftime('%Y-%m-%d', time.localtime(last_stats['timestamp']))
                        current_day = time.strftime('%Y-%m-%d', time.localtime(current_time))

                        if last_day == current_day:
                            # 如果是同一天，替换最后一条记录
                            trend_data[-1] = current_stats
                            need_update = True
                        else:
                            # 不是同一天，追加新记录
                            need_update = True
                else:
                    # 首次统计
                    current_stats['unhandled_risks'] = current_total
                    current_stats['handled_risks'] = 0
                    need_update = True

            except Exception as e:
                # 确保字段存在
                current_stats['unhandled_risks'] = 0
                current_stats['handled_risks'] = 0

            # 4. 更新趋势数据
            if need_update:
                # 如果不是替换操作，则追加新数据
                if not trend_data or trend_data[-1]['timestamp'] != current_stats['timestamp']:
                    trend_data.append(current_stats)

                # 限制数据点数量
                if len(trend_data) > MAX_POINTS:
                    trend_data = trend_data[-MAX_POINTS:]

                # 确保目录存在并保存数据
                trend_dir = os.path.dirname(trend_file)
                if not os.path.exists(trend_dir):
                    os.makedirs(trend_dir, mode=0o755, exist_ok=True)
                public.writeFile(trend_file, json.dumps(trend_data))

            return {'trend_list': trend_data}

        except Exception as e:
            # 返回至少包含一个空记录的列表
            return {
                'trend_list': [{
                    'timestamp': int(time.time()),
                    'risk_scan': 0,
                    'vul_scan': 0,
                    'server_risks': 0,
                    'file_detection': 0,
                    'hids_risks': 0,
                    'unhandled_risks': 0,
                    'handled_risks': 0
                }]
            }

    def get_security_dynamic(self, get) -> dict:
        """获取安全动态"""
        try:
            events = []

            # 1. 获取恶意文件检测事件
            try:
                log_file = '/www/server/panel/data/safeCloud/log/detection_all.log'
                if os.path.exists(log_file):
                    # 使用 deque 获取最后30行
                    from collections import deque
                    last_lines = deque(maxlen=30)

                    with open(log_file, 'r') as f:
                        for line in f:
                            last_lines.append(line)

                    # 处理最后30行数据
                    for line in last_lines:
                        try:
                            # 解析日志行
                            parts = line.strip().split('|')
                            if len(parts) >= 9:
                                filename, filepath, threat_type, md5, level, detect_time, status, detect_type, handled = parts[
                                                                                                                         :9]

                                # 转换时间字符串为时间戳
                                try:
                                    time_stamp = int(time.mktime(time.strptime(detect_time, '%Y-%m-%d %H:%M:%S')))
                                except:
                                    time_stamp = int(time.time())

                                events.append({
                                    'type': 'file_detection',
                                    'behavior': threat_type,
                                    'level': int(level),
                                    'time': time_stamp,
                                    'scan_type': '文件扫描',
                                    'description': "发现{}: {}".format(threat_type, filename),
                                    'solution': '建议立即隔离或删除该文件',
                                    'file_path': filepath,
                                    'detect_type': detect_type
                                })
                        except Exception as e:
                            continue
            except Exception as e:
                pass

            # 2. 获取入侵检测事件
            try:
                risk_list = public.M('risk').dbfile('bt_hids').order('id desc').limit(100).select()
                for risk in risk_list:
                    try:
                        # 转换时间字符串为时间戳
                        try:
                            risk_time_str = risk.get('time', '')
                            if isinstance(risk_time_str, str) and risk_time_str:
                                risk_time = int(time.mktime(time.strptime(risk_time_str, '%Y-%m-%d %H:%M:%S')))
                            else:
                                risk_time = int(time.time())
                        except:
                            risk_time = int(time.time())

                        # 转换风险等级
                        level = 4 if risk['level'] == 'serious' else 3 if risk['level'] == 'high' else 2

                        events.append({
                            'type': 'hids',
                            'behavior': risk.get('type', '未知风险'),
                            'level': level,
                            'time': risk_time,
                            'scan_type': '主机入侵检测',
                            'description': risk.get('msg', ''),
                            'solution': risk.get('solution', '请及时处理该安全风险'),
                            'file_path': risk.get('file_path', ''),
                            'detect_type': risk.get('risk_type', '')
                        })
                    except Exception as e:
                        continue
            except Exception as e:
                pass

            # 确保所有时间戳都是整数类型
            events = [event for event in events if isinstance(event['time'], int)]

            # 按时间排序（降序）
            events.sort(key=lambda x: x['time'], reverse=True)

            # 只返回最近50条记录
            return {'events': events[:50]}

        except Exception as e:
            return {'events': []}

    def _get_ignored_md5_set(self) -> set:
        """从 ignored_md5s.list 文件加载MD5到集合中。"""
        ignored_set = set()
        if os.path.exists(self.__ignored_md5_list_path):
            try:
                with open(self.__ignored_md5_list_path, 'r', encoding='utf-8') as f_ignore:
                    for line in f_ignore:
                        md5_hash = line.strip()
                        if md5_hash:  # 确保不是空行
                            ignored_set.add(md5_hash.lower())
            except Exception as e:
                pass
        return ignored_set

    # 新增
    def ignore_file(self, get):
        """
        * @description: 从检测日志中删除文件条目，上传为误报，
        *               并将其当前MD5添加到忽略列表以供后续扫描跳过。
        * @author: Mr wpl
        * @time: 2025-06-07
        * @param get.filepath: str - 要忽略文件的完整路径。
        * @param get.md5: str - 文件在日志中记录的MD5 (用于删除日志)。
        * @param get.filename: str - 用于误报上传的文件名。
        * @param get.risk: int - 用于误报上传的风险等级。
        * @returns dict - 操作结果。
        """
        try:
            # 1. 参数校验
            if not hasattr(get, 'filepath') or not hasattr(get, 'md5'):
                return public.returnMsg(False, '参数不完整: 缺少 filepath 或 md5 (日志中的MD5)')

            target_filepath = get.filepath.strip()
            logged_md5 = get.md5.strip().lower()  # 来自日志条目的MD5

            if not target_filepath or not logged_md5:
                return public.returnMsg(False, '参数错误: filepath 或 md5 (日志中的MD5) 不能为空')

            # 2. 删除日志条目
            log_path = os.path.join(self.__log_dir, "detection_all.log")
            log_entry_deleted = False
            if os.path.exists(log_path):
                try:
                    with open(log_path, 'r+', encoding='utf-8') as f:
                        fcntl.flock(f, fcntl.LOCK_EX)  # 文件锁
                        try:
                            lines = f.readlines()
                            remaining_lines = []
                            for line_content in lines:
                                stripped_line = line_content.strip()
                                if not stripped_line:  # 保留空行
                                    remaining_lines.append(line_content)
                                    continue
                                parts = stripped_line.split('|')
                                if len(parts) >= 9:
                                    log_file_path_in_entry = parts[1]
                                    log_md5_in_entry = parts[3].lower()
                                    # 精确匹配路径和记录的MD5
                                    if os.path.normpath(log_file_path_in_entry) == os.path.normpath(target_filepath) and \
                                            log_md5_in_entry == logged_md5:
                                        log_entry_deleted = True
                                        continue  # 跳过此行
                                remaining_lines.append(line_content)

                            if log_entry_deleted:
                                f.seek(0)
                                f.writelines(remaining_lines)
                                f.truncate()
                        finally:
                            fcntl.flock(f, fcntl.LOCK_UN)  # 释放锁
                except Exception as e:
                    pass

            # 3. 误报上传 (使用文件的当前内容)
            upload_status_message = "误报上传未执行或相关参数(filename, risk)缺失。"
            current_file_exists_for_upload = os.path.exists(target_filepath)

            if hasattr(get, 'filename') and hasattr(get, 'risk'):
                if not current_file_exists_for_upload:
                    upload_status_message = "误报上传失败：文件 {} 当前不存在于磁盘。".format(target_filepath)
                else:
                    import requests
                    upload_url = 'https://www.bt.cn/api/v2/error/information'

                    upload_filename_for_api = get.filename

                    try:
                        params_for_upload = {"auto": "1", "class": "2", "type": "0"}
                        try:
                            risk_value = int(get.risk)
                            if risk_value == 0:
                                params_for_upload['class'] = "0"
                                params_for_upload['type'] = "0"
                            elif 1 <= risk_value <= 5:
                                params_for_upload['class'] = "1"
                                params_for_upload['type'] = str(risk_value)
                        except ValueError:
                            pass

                        # 适配您提供的两步上传逻辑 (先获取token，然后用token上传)
                        token = None
                        # 阶段1: 获取 token
                        f_for_token_content = None
                        with open(target_filepath, 'rb') as f_for_token_handle:
                            f_for_token_content = f_for_token_handle.read()
                        files_for_token_stage = {
                            'file': (upload_filename_for_api, f_for_token_content, 'application/octet-stream')}

                        token_response = requests.post(upload_url, files=files_for_token_stage)
                        token_data = token_response.json()

                        if token_data.get('success') and token_data.get('res', {}).get('token'):
                            token = token_data['res']['token']
                        else:
                            upload_status_message = "误报上传失败（获取token阶段）：{}".format(token_data.get('msg', 'API响应无效或未包含token'))

                        # 阶段2: 使用token上传
                        if token:
                            time.sleep(1)
                            f_for_upload_content = None
                            with open(target_filepath, 'rb') as f_for_upload_handle:
                                f_for_upload_content = f_for_upload_handle.read()
                            files_for_final_upload = {
                                'file': (upload_filename_for_api, f_for_upload_content, 'application/octet-stream')}

                            data_payload_final = {
                                "token": token,
                                "type": params_for_upload['type'],
                                "class": params_for_upload['class'],
                                "auto": params_for_upload['auto']
                            }
                            upload_response_final = requests.post(upload_url, files=files_for_final_upload,
                                                                  data=data_payload_final)
                            response_data_final = upload_response_final.json()

                            if response_data_final.get('success'):
                                upload_status_message = '误报信息已成功提交上传。'
                            else:
                                upload_status_message = "误报上传失败（数据提交阶段）：{}".format(response_data_final.get('msg', 'API响应无效'))
                    except Exception as e:
                        pass

            # 4. 将文件的 CURRENT MD5 添加到忽略列表
            md5_handling_status_message = ""
            if current_file_exists_for_upload:
                current_file_md5_for_ignore = self.FileMd5(target_filepath)
                if current_file_md5_for_ignore:
                    if self._add_md5_to_ignore_list(current_file_md5_for_ignore):
                        md5_handling_status_message = "文件当前内容 (MD5: {}) 已被记录，将在后续扫描中被跳过（忽略列表最多保留10000条）。".format(current_file_md5_for_ignore)
                    else:
                        md5_handling_status_message = "文件未能添加到后续扫描的忽略列表（内部错误）。"
                        # return public.returnMsg(False, '添加到忽略列表时发生内部错误')
                else:
                    md5_handling_status_message = "无法计算文件当前内容的MD5，未能添加到忽略列表。"
            else:
                md5_handling_status_message = "由于文件当前不存在，无法将其特定内容添加到忽略列表。"

            # 构建最终消息
            final_user_message = "处理文件 '{}' 的忽略请求：".format(target_filepath)
            if log_entry_deleted:
                final_user_message += " 相关日志条目已删除。"
            else:
                final_user_message += " 在日志中未找到与提供的路径和MD5完全匹配的条目。"

            final_user_message += " {}".format(upload_status_message)
            final_user_message += " {}".format(md5_handling_status_message)

            return public.returnMsg(True, final_user_message)
        except Exception as e:
            return public.returnMsg(False, '忽略异常')

    def _load_ignored_md5_list_and_set(self) -> Tuple[List[str], Set[str]]:
        """
        从 ignored_md5s.list 文件加载MD5到列表和集合中。
        列表保持顺序，集合用于快速查找。
        """
        ignored_list: List[str] = []
        ignored_set: Set[str] = set()
        if os.path.exists(self.__ignored_md5_list_path):
            try:
                with open(self.__ignored_md5_list_path, 'r', encoding='utf-8') as f_ignore:
                    for line in f_ignore:
                        md5_hash = line.strip()
                        if md5_hash:
                            if md5_hash.lower() not in ignored_set:  # 确保加入小写，避免重复
                                ignored_list.append(md5_hash.lower())
                                ignored_set.add(md5_hash.lower())
            except Exception as e:
                pass
        return ignored_list, ignored_set

    def _save_ignored_md5_list(self, ignored_list: list) -> None:
        """
        将MD5列表保存回 ignored_md5s.list 文件。
        会覆盖原文件。
        """
        try:
            # 确保目录存在
            ignore_dir = os.path.dirname(self.__ignored_md5_list_path)
            if not os.path.exists(ignore_dir):
                os.makedirs(ignore_dir, mode=0o755, exist_ok=True)

            with open(self.__ignored_md5_list_path, 'w', encoding='utf-8') as f_save:
                fcntl.flock(f_save, fcntl.LOCK_EX)  # 文件锁
                try:
                    for md5_hash in ignored_list:
                        f_save.write(md5_hash + '\n')
                finally:
                    fcntl.flock(f_save, fcntl.LOCK_UN)  # 释放锁
        except Exception as e:
            pass

    def _add_md5_to_ignore_list(self, md5_to_add: str) -> bool:
        """
        添加MD5到忽略列表，并维护列表大小不超过 10000
        如果MD5已存在，则将其移到列表末尾（视为最新）。
        返回 True 如果操作成功 (添加或已存在)，False 如果出错。
        """
        if not md5_to_add:
            return False

        md5_to_add = md5_to_add.lower()
        ignored_list, ignored_set = self._load_ignored_md5_list_and_set()

        if md5_to_add in ignored_set:
            # 如果已存在，先移除，再添加到末尾，使其成为最新的
            ignored_list = [m for m in ignored_list if m != md5_to_add]

        ignored_list.append(md5_to_add)

        # 如果超过最大数量，从列表头部删除旧的条目
        while len(ignored_list) > 10000:
            ignored_list.pop(0)  # 删除最早添加的

        self._save_ignored_md5_list(ignored_list)
        return True
