# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: csj <csj@bt.cn>
# -------------------------------------------------------------------
# ------------------------------
# docker compose 工具类
# ------------------------------
import json
import yaml
import sys
import os
os.chdir('/www/server/panel')
sys.path.append('class/')

import public


class DockerComposeUtils:
    @staticmethod
    def docker_info():
        try:
            return json.loads(public.ExecShell('docker info --format json')[0])
        except:
            return {}

    @staticmethod
    def compose_version():
        try:
            return public.ExecShell('docker-compose version --short')[0].strip()
        except:
            return ""

    @staticmethod
    def network_inspect(name):
        try:
            out, err = public.ExecShell(f"docker network inspect {name}")
            data = json.loads(out.strip())
            if isinstance(data, list) and data:
                return data[0]
            return {}
        except:
            return {}

    @staticmethod
    def volume_inspect(name):
        try:
            out, err = public.ExecShell(f"docker volume inspect {name}")
            data = json.loads(out.strip())
            if isinstance(data, list) and data:
                return data[0]
            return {}
        except:
            return {}

    @staticmethod
    def load_compose_config(compose_file_path):
        out, err = public.ExecShell(f"docker-compose -f {compose_file_path} config")
        if err:
            raise Exception(f"docker-compose文件读取错误: {err}")
        return yaml.safe_load(out)

    @staticmethod
    def network_exists(name):
        try:
            out, err = public.ExecShell(f"docker network inspect {name}")
            return out.strip() not in ('', '[]') and 'No such network' not in out and 'Error' not in out
        except:
            return False

    @staticmethod
    def to_tuple(v):
        try:
            return tuple(int(x) for x in str(v).strip().lstrip('v').split('.') if x != '')
        except:
            return (0,)

    @staticmethod
    def check_elf_file(file_path):
        """
        检查文件是否是ELF文件
        """
        try:
            out, err = public.ExecShell(f"file {file_path}")
            return 'ELF' in out or 'executable' in out
        except:
            return False

    @staticmethod
    def check_special_file(file_path):
        """
        检查文件是否是特殊的系统文件
        0:普通文件    备份和还原可用
        1:风险文件    备份警示还原
        2:系统性文件  不备份不还原
        3:已存在于compose项目下 ，通常不需要额外的备份和还原
        """
        import stat

        # 特殊文件黑名单 (即使用户强行挂载了宿主机的这些文件，通常也不建议备份回去覆盖)
        # Docker 容器启动时往往会自动生成这些，还原回去可能导致网络故障
        # 风险文件
        sys_files = {
            "/etc/timezone",
            "/etc/localtime",
            "/etc/resolv.conf",
            "/etc/hosts",
            "/etc/hostname",
        }
        # 系统文件夹
        sys_folders = {
            "/sys",
            "/proc",
            "/dev",
            "/lib/modules",
            "/lib",
            "/lib64"
        }
        # 风险文件夹
        risk_folders = {
            "/bin",
            "/sbin",
            "/usr/bin",
            "/usr/sbin",
        }

        if file_path in sys_files:
            return 2
        if any(file_path.startswith(d) for d in sys_folders):
            return 2

        try:
            mode = os.stat(file_path).st_mode

            # A. 检查是否为 Socket (例如 /var/run/docker.sock)
            # B. 检查是否为字符设备 (Character Device) (例如 /dev/kvm, /dev/null, /dev/tty)
            # C. 检查是否为块设备 (Block Device) (例如 /dev/sda)
            # D. 检查是否为命名管道 (FIFO / Named Pipe)
            if stat.S_ISSOCK(mode) or stat.S_ISCHR(mode) or stat.S_ISBLK(mode) or stat.S_ISFIFO(mode):
                return 2
        except PermissionError:
            # 没有权限读取属性，为了安全起见，跳过
            return 2
        except OSError:
            return 2

        if DockerComposeUtils.check_elf_file(file_path) or any(file_path.startswith(d) for d in risk_folders):
            return 1

        return 0
