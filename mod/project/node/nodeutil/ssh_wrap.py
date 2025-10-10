import json
import os.path
import traceback
from typing import Optional, Tuple, Callable
from mod.base.ssh_executor import SSHExecutor, CommandResult
from mod.project.node.dbutil import ServerNodeDB, Node

import public

def is_much_difference(a:float, b:float)->bool:
    if a == 0 or b == 0:
        return True
    ratio = a / b
    return ratio >= 10 or ratio <= 0.1

class SSHApi:
    is_local = False
    _local_scripts_dir = os.path.join(os.path.dirname(__file__), "ssh_warp_scripts")

    def __init__(self, host, port: int=22, username: str="root", password=None, pkey=None,
                 pkey_passwd=None, threading_mod=False, timeout=20):
        self._real_ssh_conf = {
            "host": host,
            "username": username,
            "port": port,
            "password": password,
            "key_file": "",
            "passphrase": pkey_passwd,
            "key_data": pkey,
            "strict_host_key_checking": False,
            "allow_agent": False,
            "look_for_keys": False,
            "threading_mod": threading_mod,
            "timeout": timeout,
        }
        self._ssh_executor: Optional[SSHExecutor] = None


    @classmethod
    def new_by_id(cls, node_id: int, threading_mod=False) -> Optional["SSHApi"]:
        data = ServerNodeDB().get_node_by_id(node_id)
        if not data or not isinstance(data, dict):
            return None
        data["ssh_conf"] = json.loads(data["ssh_conf"])
        if not data["ssh_conf"]:
            return None
        data["ssh_conf"]["threading_mod"] = threading_mod
        return cls(**data["ssh_conf"])

    def _get_ssh_executor(self) -> SSHExecutor:
        if self._ssh_executor:
            return self._ssh_executor
        self._ssh_executor = SSHExecutor(**self._real_ssh_conf)
        return self._ssh_executor

    def get_net_work(self) -> Tuple[Optional[dict], str]:
        data, err = self._run_script("system_info.sh")
        if err:
            return None, err
        if not data.exit_code == 0:
            return None, data.stderr
        try:
            data = json.loads(data.stdout)
            if isinstance(data, dict) and "cpu" in data and "mem" in data:
                return self._tans_net_work_form_data(data), ""
            return None, "数据格式错误: %s" % str(data)
        except Exception as e:
            return None, str(e)

    @staticmethod
    def _tans_net_work_form_data(data: dict):
        data["mem"]["memAvailable"] = round(data["mem"]["memAvailable"] / 1024 / 1024, 2)
        data["mem"]["memBuffers"] = round(data["mem"]["memBuffers"] / 1024 / 1024, 2)
        data["mem"]["memCached"] = round(data["mem"]["memCached"] / 1024 / 1024, 2)
        data["mem"]["memFree"] = round(data["mem"]["memFree"] / 1024 / 1024, 2)
        data["mem"]["memRealUsed"] = round(data["mem"]["memRealUsed"] / 1024 / 1024, 2)
        data["mem"]["memShared"] = round(data["mem"]["memShared"] / 1024 / 1024, 2)
        data["mem"]["memTotal"] = round(data["mem"]["memTotal"] / 1024 / 1024, 2)
        data["physical_memory"]= round(data["physical_memory"] / 1024 / 1024, 2)
        if is_much_difference(data["mem"]["memTotal"], data["physical_memory"]):
            if data["mem"]["memTotal"] >= 1024:
                data["mem"]["memNewTotal"] = "%.2fGB" % (data["mem"]["memTotal"] / 1024)
            else:
                data["mem"]["memNewTotal"] = "%.2fMB" % data["mem"]["memTotal"]
        else:
            if data["physical_memory"] >= 1024:
                data["mem"]["memNewTotal"] = "%.2fGB" % (data["physical_memory"] / 1024)
            else:
                data["mem"]["memNewTotal"] = "%.2fMB" % data["physical_memory"]
        return data

    def _run_script(self, script_name: str) -> Tuple[Optional[CommandResult], str]:
        local_file = os.path.join(self._local_scripts_dir, script_name)
        if not os.path.exists(local_file):
            return None, "脚本不存在"
        executor = None
        try:
            executor = self._get_ssh_executor()
            executor.open()
            result = executor.execute_local_script_collect(local_file)
            return result, ""
        except RuntimeError:
            return None, "ssh连接失败"
        except Exception as e:
            return None, str(e)
        finally:
            if executor:
                executor.close()

    def target_file_exits(self, target_file: str) -> Tuple[bool, str]:
        try:
            executor = self._get_ssh_executor()
            executor.open()
            result, err = executor.path_exists(target_file)
            return result, err
        except RuntimeError:
            print(traceback.format_exc())
            return False, "ssh连接失败"
        except Exception as e:
            return False, str(e)

    def create_dir(self, path: str) -> Tuple[bool, str]:
        try:
            executor = self._get_ssh_executor()
            executor.open()
            result, err = executor.create_dir(path)
            return result, err
        except RuntimeError:
            print(traceback.format_exc())
            return False, "ssh连接失败"
        except Exception as e:
            return False, str(e)

    def upload_file(self, filename: str, target_path: str, mode: str = "cover",
                    call_log: Callable[[int, str], None] = None) -> str:

        if not os.path.isfile(filename):
            return "文件:{}不存在".format(filename)

        target_file = os.path.join(target_path, os.path.basename(filename))
        exits, err = self.target_file_exits(target_file)
        if err:
            return err

        if exits and mode == "ignore":
            call_log(0, "文件上传:{} -> {},目标文件已存在,跳过上传".format(filename, target_file))
            return ""
        if exits and mode == "rename":
            upload_name = "{}_{}".format(os.path.basename(filename), public.md5(filename))
            call_log(0, "文件上传:{} -> {},目标文件已存在,将重命名为{}".format(filename, target_file, upload_name))
        else:
            upload_name = os.path.basename(filename)

        try:
            executor = self._get_ssh_executor()
            executor.open()
            def progress_callback(current_size: int, total_size: int):
                call_log(current_size * 100 // total_size, "" )
            executor.upload(filename, os.path.join(target_path, upload_name), progress_callback=progress_callback)
        except RuntimeError:
            print(traceback.format_exc())
            return "ssh连接失败"
        except Exception as e:
            return str(e)
        return ""

    def upload_dir_check(self, target_file: str) -> str:
        try:
            executor = self._get_ssh_executor()
            executor.open()
            path_info = executor.path_info(target_file)
            if not path_info['exists']:
                return ""
            if path_info['is_dir']:
                return "该名称路径不是目录"
            return ""
        except RuntimeError:
            print(traceback.format_exc())
            return "ssh连接失败"
        except Exception as e:
            return str(e)
