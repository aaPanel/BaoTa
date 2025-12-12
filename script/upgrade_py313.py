# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016  宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: baozi <baozi@bt.cn>
# +-------------------------------------------------------------------
# | 宝塔面板python环境更新模块，功能如下：
# | 仅在11.2版本中使用，用来将用户的系统环境升级到3.13
# +-------------------------------------------------------------------
import os
import subprocess
import sys
import json
import re
import shutil
import sys
import time
import tempfile
import psutil
import fcntl

from typing import Optional, Union, List, Dict, Tuple, Any, Set
from contextlib import contextmanager

_PANEL_PATH = "/www/server/panel"
_LOG_FILE = os.path.join(_PANEL_PATH, "logs/upgrade_py313.log")
_LOCK_FILE = os.path.join(_PANEL_PATH, ".upgrade_py313.lock")


@contextmanager
def single_instance_lock(lockfile_path):
    """单实例锁的上下文管理器"""
    lockfile = None
    locked = False
    try:
        # 打开锁文件
        lockfile = open(lockfile_path, 'w')
        # 尝试获取排他锁
        fcntl.flock(lockfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        # 写入当前进程PID
        lockfile.write(str(os.getpid()))
        lockfile.flush()
        locked = True
        yield lockfile
    except (IOError, OSError):
        # 无法获取锁，说明已有实例在运行
        print("另一个实例已在运行")
        sys.exit(1)
    except:
        pass
    finally:
        if lockfile and locked:
            try:
                fcntl.flock(lockfile.fileno(), fcntl.LOCK_UN)
                lockfile.close()
                os.unlink(lockfile_path)
            except:
                pass


class _EnvUtil(object):

    def __init__(self):
        self.env_shell_url = "/install/pyenv/upgrade_py313.sh"
        self.pip_txt_url = "/install/pyenv/pip313.txt"

    @staticmethod
    def start_prepare_env():
        try:
            # 只安装python3.13环境，不执行替换
            _sh = "cd /www/server/panel && bash script/upgrade_py313.sh --prepare --disable-color"
            proc = subprocess.Popen(_sh, shell=True, stderr=sys.stderr, stdout=sys.stdout)
            proc.wait()
        except:
            pass

    # 检查磁盘空间
    @staticmethod
    def check_disk_free() -> bool:
        disk_usage = psutil.disk_usage(_PANEL_PATH)
        return disk_usage.free > 1024 * 1024 * 500

    @staticmethod
    def check_tools() -> Optional[str]:
        wget_path = shutil.which("wget")
        if not wget_path:
            try:
                if os.path.exists("/usr/bin/yum"):
                    subprocess.run(
                        ['yum', 'install', '-y', 'wget'],
                        check=True, stdout=sys.stdout, stderr=sys.stderr
                    )
                else:
                    subprocess.run(
                        ['apt-get', 'install', '-y', 'wget'],
                        check=True, stdout=sys.stdout, stderr=sys.stderr
                    )
            except Exception:
                return "未检查到wget工具，且尝试安装失败，请自行安装wget工具并重新开始"
        else:
            return None

        wget_path = shutil.which("wget")
        if not wget_path:
            return "未检查到wget工具，且尝试安装失败，请自行安装wget工具并重新开始"
        return None

    # 下载和更新升级环境的shell脚本
    def download_env_shell(self) -> Optional[str]:
        target_file = "{}/script/upgrade_py313.sh".format(_PANEL_PATH)
        return self._download_file(self.env_shell_url, target_file)

    def download_pip_txt(self) -> Optional[str]:
        target_file = "{}/script/pip313.txt".format(_PANEL_PATH)
        return self._download_file(self.pip_txt_url, target_file)

    @staticmethod
    def _get_down_host() -> str:
        try:
            import json
            with open('{}/data/node_url.pl'.format(_PANEL_PATH)) as f:
                res = json.load(f)
            down_url = res['down-node']['url']
            if down_url:
                return "https://{}".format(down_url)
        except:
            pass
        return 'https://download.bt.cn'

    # 使用 sys_fd 传递临时文件描述符
    @classmethod
    def _download_file(cls, uri: str, target_file: str) -> Optional[str]:
        import urllib3
        urllib3.disable_warnings()
        import requests
        tmp_fd, tmp_path = tempfile.mkstemp(prefix="env_shell_")

        def _close():
            try:
                os.remove(tmp_path)
                os.close(tmp_fd)
            except Exception:
                pass

        headers = {"User-Agent": "BT-Panel"}
        host: str = cls._get_down_host()
        url = "{}/{}".format(host, uri.lstrip("/"))
        try:
            resp = requests.get(url, stream=True, verify=False, timeout=60, headers=headers)
            if resp.status_code != 200:
                _close()
                return "下载失败，返回码：{}".format(resp.status_code)

            with os.fdopen(tmp_fd, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8048):
                    if chunk:
                        f.write(chunk)

        except Exception as e:
            _close()
            return "下载失败：{}".format(str(e))

        if not (os.path.isfile(tmp_path) and os.path.getsize(tmp_path) > 10):
            _close()
            return "下载失败"

        if os.path.isfile(target_file):
            os.remove(target_file)
        shutil.move(tmp_path, target_file)
        return None

    # 已有python3.13环境
    @staticmethod
    def has_py313() -> bool:
        code = "import sys; print('%d.%d' % (sys.version_info.major, sys.version_info.minor))"
        now_env = os.path.join(_PANEL_PATH, "pyenv/bin/python3")
        pre_env = os.path.join(_PANEL_PATH, "pyenv313/bin/python3")
        for env in [now_env, pre_env]:
            if not os.path.exists(env):
                continue
            try:
                ver = subprocess.check_output([env, "-c", code], text=True)
                if ver.strip() == "3.13":
                    return True
            except:
                import traceback
                print(traceback.format_exc())
                pass
        return False

    def prepare(self):
        if self.has_py313():
            print("已存在python3.13环境, 退出")
            return
        print("检查环境...")
        if not self.check_disk_free():
            return "磁盘空间不足【500M】，请清理后再进行操作"
        err = self.check_tools()
        if err:
            return err

        print("开始下载升级环境脚本...")
        err = self.download_env_shell()
        if err:
            err = "获取最新升级环境脚本失败：{}".format(err)
            print(err)
            return
        err = self.download_pip_txt()
        if err:
            err = "获取最新升级库版本信息失败：{}".format(err)
            print(err)
            return err

        print("开始执行升级环境脚本...")
        self.start_prepare_env()
        if not self.has_py313():
            print("环境准备失败！")
            return
        print("环境准备完成")


if __name__ == "__main__":
    log_fd = open(_LOG_FILE, "a+")
    os.dup2(log_fd.fileno(), sys.stdout.fileno())
    os.dup2(log_fd.fileno(), sys.stderr.fileno())  # 输出到日志文件
    with single_instance_lock(_LOCK_FILE):
        if len(sys.argv) > 1:
            opt= sys.argv[1]
        else:
            opt = ""
        if opt == "prepare-env":
            env_util = _EnvUtil()
            env_util.prepare()
        else:
            print("Usage: python {} upgrade-python|update-plugins-package".format(sys.argv[0]))
