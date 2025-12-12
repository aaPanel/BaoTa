#! /www/server/panel/pyenv/bin/python3
import copy
import json
import os
import re
import shutil
import sys
import tarfile
import threading
import time
from platform import machine

import requests
import traceback
import subprocess
import argparse
from typing import Optional, Tuple, List, Union, Dict, TextIO
from xml.etree import cElementTree
from io import FileIO

os.chdir("/www/server/panel")
if "class/" not in sys.path:
    sys.path.insert(0, "class/")
if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

from mod.project.python.pyenv_tool import EnvironmentManager

import public


class _VmSTD:
    out = sys.stdout
    err = sys.stderr


_vm_std = _VmSTD()


def is_aarch64() -> bool:
    _arch = machine().lower()
    if _arch in ("aarch64", "arm64"):
        return True
    return False


def parse_version_to_list(version: str) -> Tuple[int, int, int]:
    tmp = version.split(".")
    if len(tmp) == 1:
        return int(tmp[0]), 0, 0
    elif len(tmp) == 2:
        return int(tmp[0]), int(tmp[1]), 0
    else:
        return int(tmp[0]), int(tmp[1]), int(tmp[2])


def _get_index_of_python(url_list: List[str], timeout=10) -> Optional[Dict]:
    task_list = []
    result_list: List[dict] = []

    def get_result(test_url, idx):
        try:
            nonlocal result_list
            response = requests.get(test_url, timeout=timeout)
            result_list[idx]["data"] = response.text
            result_list[idx]["time"] = time.time()
        except Exception as e:
            pass

    for i, url in enumerate(url_list):
        task = threading.Thread(target=get_result, args=(url, i))
        result_list.append({
            "data": None,
            "time": time.time() + 60 * 60,
            "url": url
        })
        task_list.append(task)
        task.start()

    for i in task_list:
        i.join()

    result_list.sort(key=lambda x: x["time"])  # 按照时间降序
    return result_list[0]


def get_index_of_python() -> Optional[Dict]:
    url_list = [
        "https://repo.huaweicloud.com/python/",
        "https://www.python.org/ftp/python/",
    ]
    print("正在检查网络状况......", file=_vm_std.out, flush=True)
    res = _get_index_of_python(url_list, timeout=10)
    if res is None:
        res = _get_index_of_python(url_list, timeout=60)
        if res is None:
            print("无法链接网络，查询CPython解释器版本......", file=_vm_std.out, flush=True)
    return res


def get_index_of_pypy_python() -> Optional[Dict]:
    url_list = [
        "https://buildbot.pypy.org/mirror/",
        "https://downloads.python.org/pypy/",
    ]
    print("正在检查网络状况......", file=_vm_std.out, flush=True)
    res = _get_index_of_python(url_list, timeout=10)
    if res is None:
        res = _get_index_of_python(url_list, timeout=60)
        if res is None:
            print("无法链接网络，查询PyPy解释器版本......", file=_vm_std.out, flush=True)
    return res


class PythonVersion:

    def __init__(self, v: str, is_pypy: bool = False, filename: str = None):
        self.version = v
        self.is_pypy = is_pypy
        self.bt_python_path = "/www/server/pyporject_evn/versions"
        self.bt_pypy_path = "/www/server/pyporject_evn/pypy_versions"
        self._file_name = filename.strip() if isinstance(filename, str) else None

        self._ver_t = None
        if not os.path.exists(self.bt_python_path):
            os.makedirs(self.bt_python_path)

        if not os.path.exists(self.bt_pypy_path):
            os.makedirs(self.bt_pypy_path)

    @property
    def ver_t(self) -> Tuple[int, int, int]:
        if self._ver_t is not None:
            return self._ver_t
        self._ver_t = parse_version_to_list(self.version)
        return self._ver_t

    @property
    def installed(self) -> bool:
        if self.is_pypy:
            return os.path.exists(self.bt_pypy_path + "/" + self.version)
        return os.path.exists(self.bt_python_path + "/" + self.version)

    @staticmethod
    def check(file) -> bool:
        print("[2/3] 验证源码文件......", file=_vm_std.out, flush=True)
        if not os.path.exists(file):
            print("文件不存在，无法验证", file=_vm_std.out, flush=True)
            return False
        if os.path.getsize(file) < 1024 * 1024 * 10:
            print("文件内容缺失", file=_vm_std.out, flush=True)
            os.remove(file)
            return False
        return True

    @property
    def file_name(self) -> str:
        if self._file_name:
            return self._file_name
        if self.is_pypy and not self._file_name:
            raise Exception("没有文件名称")
        return "Python-{}.tar.xz".format(self.version)

    @staticmethod
    def _download_file(dst, url):
        print(url, file=_vm_std.out, flush=True)
        response = requests.get(url, stream=True, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
        })
        total_size = int(response.headers.get('content-length', 0))
        print("需要下载的源码文件大小: %.2fM" % (total_size / (1024 * 1024)), file=_vm_std.out, flush=True)
        if total_size == 0:
            print("文件下载出错！", file=_vm_std.out, flush=True)
        downloaded_size = 0
        block_size = 1024 * 1024
        with open(dst, 'wb') as f:
            for data in response.iter_content(block_size):
                f.write(data)
                downloaded_size += len(data)
                progress = (downloaded_size / total_size) * 100
                print(f"下载中....\t %.2f%% completed" % progress, end='\r', flush=True, file=_vm_std.out)
        response.close()

    def download(self, base_url) -> bool:
        if self.is_pypy:
            cache_dir = os.path.join(self.bt_pypy_path, "cached")
        else:
            cache_dir = os.path.join(self.bt_python_path, "cached")
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        dst = os.path.join(cache_dir, self.file_name)
        if os.path.exists(dst) and os.path.getsize(dst) > 1024 * 1024 * 10:
            print("[1/3] 使用缓存中的源码文件......", file=_vm_std.out, flush=True)
            return self.check(dst)

        print("[1/3] 下载源码文件......", file=_vm_std.out, flush=True)
        print("下载源码文件中......", file=_vm_std.out, flush=True)
        down_url = "{}{}/{}".format(base_url, self.version, self.file_name)
        if self.is_pypy:
            down_url = "{}{}".format(base_url, self.file_name)
        self._download_file(dst, down_url)
        print('下载完成', file=_vm_std.out, flush=True)
        return self.check(dst)

    def _install(self, extended_args='') -> bool:
        if self.is_pypy:
            return self._install_pypy()
        print("[3/3] 解压安装.....", file=_vm_std.out, flush=True)
        install_sh = "{}/script/install_python.sh".format(public.get_panel_path())
        check_openssl_args, extended_args = self._parse_extended_args(extended_args)
        sh_str = "bash {} {} {} '{}'".format(install_sh, self.version, check_openssl_args, extended_args)
        p = subprocess.Popen(sh_str, stdout=_vm_std.out, stderr=_vm_std.out, shell=True)
        p.wait()
        if not os.path.exists(self.bt_python_path + "/" + self.version):
            return False
        self.install_pip_tool(self.bt_python_path + "/" + self.version)
        return True

    @staticmethod
    def _parse_extended_args(extended_args) -> Tuple[str, str]:
        rep_openssl = re.compile(r"--with-openssl=(?P<path>\S+)")
        res = rep_openssl.search(extended_args)
        if res:
            path = res.group("path")
            if os.path.exists(path):
                return "not_check_openssl", extended_args
            else:
                extended_args = extended_args.replace(res.group(), "")
                return "check_openssl", extended_args
        return "check_openssl", extended_args

    def _install_pypy(self) -> bool:
        print("[3/3] 解压安装.....", file=_vm_std.out, flush=True)
        cache_dir = os.path.join(self.bt_pypy_path, "cached")
        d_file = os.path.join(cache_dir, self.file_name)
        tar = tarfile.open(d_file, "r|bz2")
        tar.extractall(self.bt_pypy_path)
        tar.close()
        os.renames(self.bt_pypy_path + "/" + self.file_name[:-8], self.bt_pypy_path + "/" + self.version)
        if not os.path.exists(self.bt_pypy_path + "/" + self.version):
            return False
        public.writeFile("{}/{}/is_pypy.pl".format(self.bt_pypy_path, self.version), "")
        self.install_pip_tool(self.bt_pypy_path + "/" + self.version)
        return True

    def install_pip_tool(self, python_path):
        print("正在安装pip工具.....", file=_vm_std.out, flush=True)
        python_bin = "{}/bin/python3".format(python_path)
        pip_bin = "{}/bin/pip3".format(python_path)
        if not os.path.exists(python_bin):
            python_bin = "{}/bin/python".format(python_path)
            pip_bin = "{}/bin/pip".format(python_path)

        if self._ver_t[:2] < (3, 4):
            _ver = "{}.{}".format(*self._ver_t[:2])
            if self._ver_t[:2] in ((3, 1), (3, 0)):
                _ver = "3.2"

            cache_dir = os.path.join(self.bt_python_path, "cached")
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)
            get_pip_file = os.path.join(cache_dir, "get-pip{}.py".format(_ver))
            if not os.path.exists(get_pip_file):
                url = "{}/install/plugin/pythonmamager/pip/get-pip{}.py".format(public.get_url(), _ver)
                self._download_file(get_pip_file, url)

            shutil.copyfile(get_pip_file, os.path.join(python_path, "get-pip.py"))

            sh_str = "{} {}".format(python_bin, os.path.join(python_path, "get-pip.py"))
            p = subprocess.Popen(sh_str, stdout=_vm_std.out, stderr=_vm_std.out, shell=True)
            p.wait()
            print("pip工具安装结束", file=_vm_std.out, flush=True)
        else:
            sh_str = "{} -m ensurepip".format(python_bin)
            p = subprocess.Popen(sh_str, stdout=_vm_std.out, stderr=_vm_std.out, shell=True)
            p.wait()
            print("pip工具安装结束", file=_vm_std.out, flush=True)

        if not os.path.exists(pip_bin):
            print("pip工具安装失败！！！!", file=_vm_std.out, flush=True)
        else:
            self.update_pip_tool(pip_bin)

    @staticmethod
    def update_pip_tool(pip_bin: str):
        update_str = "{} install --upgrade pip setuptools".format(pip_bin)
        p = subprocess.Popen(update_str, stdout=_vm_std.out, stderr=_vm_std.out, shell=True)
        p.wait()

    def install(self, base_url, extended_args='') -> Tuple[bool, str]:
        print("开始安装......", file=_vm_std.out, flush=True)
        if not self.is_pypy:
            dst = os.path.join(self.bt_python_path, self.version)
        else:
            dst = os.path.join(self.bt_pypy_path, self.version)
        if os.path.isdir(dst):
            return True, "已安装"
        # 下载文件
        if not self.download(base_url):
            return False, "文件下载并验证失败！"
        # 安装python
        if not self._install(extended_args):
            return False, "解压安装失败！"
        print("安装完成!", file=_vm_std.out, flush=True)
        home_path = self.bt_python_path + "/" + self.version
        if self.is_pypy:
            home_path = self.bt_pypy_path + "/" + self.version

        bin_path = "{}/bin/python".format(home_path)
        if not os.path.exists(bin_path):
            bin_path = "{}/bin/python3".format(home_path)
        if not os.path.exists(bin_path):
            print("python安装失败！")
            return False, "python安装失败！"

        if bin_path == "{}/bin/python3".format(home_path):
            os.symlink(os.path.realpath(bin_path), "{}/bin/python".format(home_path))
        elif bin_path == "{}/bin/python".format(home_path) and not os.path.exists("{}/bin/python3".format(home_path)):
            os.symlink(os.path.realpath(bin_path), "{}/bin/python3".format(home_path))

        EnvironmentManager.add_python_env("system", bin_path)
        return True, ""

    @staticmethod
    def parse_version(version: str) -> Tuple[bool, str]:
        v_rep = re.compile(r"(?P<target>\d+\.\d{1,2}(\.\d{1,2})?)")
        v_res = v_rep.search(version)
        if v_res:
            v = v_res.group("target")
            return True, v
        else:
            return False, ""


class _PyCommandManager(object):
    _FORMAT_DATA = """
# Start-Python-Env 命令行环境设置
export PATH="{}${{PATH}}"
# End-Python-Env
"""

    @staticmethod
    def check_use():
        out, _ = public.ExecShell("lsattr /etc/profile")
        return out.find("--i") == -1

    def set_python_env(self, python_path: str) -> Tuple[bool, str]:
        if python_path is None:
            python_path = ""  # 清除设置
        else:
            python_path = python_path + ":"

        if not self.check_use():
            return False, "疑似开启了系统加固，无法操作"
        try:
            rep = re.compile(r'# +Start-Python-Env[^\n]*\n(export +PATH=".*")\n# +End-Python-Env')
            profile_data = public.readFile("/etc/profile")
            if not isinstance(profile_data, str):
                return False, "配置文件加载错误"
            tmp_res = rep.search(profile_data)
            if tmp_res is not None:
                new_profile_data = rep.sub(self._FORMAT_DATA.format(python_path).strip("\n"), profile_data, 1)
            else:
                new_profile_data = profile_data + self._FORMAT_DATA.format(python_path)
            public.writeFile("/etc/profile", new_profile_data)
            return True, "配置设置成功"
        except:
            return False, "设置错误"

    @staticmethod
    def get_python_env() -> Optional[str]:
        profile_data = public.readFile("/etc/profile")
        if not isinstance(profile_data, str):
            return None
        rep = re.compile(r'# +Start-Python-Env[^\n]*\n(export +PATH="(?P<target>.*)")\n# +End-Python-Env')
        tmp_res = rep.search(profile_data)
        if tmp_res is None:
            return None
        path_data = tmp_res.group("target")
        python_path = path_data.split(":")[0].strip()
        if os.path.exists(python_path):
            return python_path
        return None


class PYVM(object):
    bt_python_path = "/www/server/pyporject_evn/versions"
    bt_pypy_path = "/www/server/pyporject_evn/pypy_versions"
    _c_py_version_default = (
        "2.7.18", "3.0.1", "3.1.5", "3.2.6", "3.3.7", "3.4.10", "3.5.10", "3.6.15", "3.7.17", "3.8.19",
        "3.9.19", "3.10.14", "3.11.9", "3.12.3"
    )

    _pypy_version_default = (
        ("3.10.14", "pypy3.10-v7.3.16-linux64.tar.bz2"),
        ("3.9.19", "pypy3.10-v7.3.16-linux64.tar.bz2"),
        ("3.8.16", "pypy3.8-v7.3.11-linux64.tar.bz2"),
        ("3.7.13", "pypy3.7-v7.3.9-linux64.tar.bz2"),
        ("3.6.12", "pypy3.6-v7.3.3-linux64.tar.bz2"),
        ("2.7.18", "pypy2.7-v7.3.16-linux64.tar.bz2"),
    )

    def __init__(self, use_shell=False):
        if not os.path.exists(self.bt_python_path):
            os.makedirs(self.bt_python_path)
        if not os.path.exists(self.bt_pypy_path):
            os.makedirs(self.bt_pypy_path)
        self.use_shell = use_shell
        self._cpy_base_url = None
        self._pypy_base_url = None
        self.stable_versions: Optional[List[PythonVersion]] = None
        self._py_cmd_mgr = _PyCommandManager()
        self.is_pypy = False
        self.async_version = False

    def now_python_path(self) -> Optional[str]:
        return self._py_cmd_mgr.get_python_env()

    def set_python_path(self, python_path) -> Tuple[bool, str]:
        return self._py_cmd_mgr.set_python_env(python_path)

    @staticmethod
    def check_use():
        res = os.popen("lsattr /etc/profile")
        return res.read().find("--i--") == -1

    @property
    def base_url(self):
        if self.is_pypy:
            if self._pypy_base_url is not None:
                return self._pypy_base_url
            res = get_index_of_pypy_python()
            if res is not None:
                self._pypy_base_url = res["url"]
                return self._pypy_base_url
        else:
            if self._cpy_base_url is not None:
                return self._cpy_base_url
            res = get_index_of_python()
            if res is not None:
                self._cpy_base_url = res["url"]
                return self._cpy_base_url
        return None

    # 获取版本
    def get_py_version(self, force=False):
        if isinstance(self.stable_versions, list) and len(self.stable_versions) > 1:
            return self.stable_versions
        if not force:
            self.stable_versions = self._get_versions_by_local()

        if not force and self.async_version and not self.stable_versions:
            self._async_get_versions()
            if self.is_pypy:
                self.stable_versions = [
                    PythonVersion(v, is_pypy=True, filename=f) for v, f in self._pypy_version_default
                ]
                return self.stable_versions
            self.stable_versions = [PythonVersion(i, is_pypy=False) for i in self._c_py_version_default]
            return self.stable_versions

        if not self.stable_versions:
            if self.use_shell:
                print("未找到本地记录文件，将向云端请求Python版本数据，这可能需要一段时间，请稍等", file=_vm_std.out)
            self.stable_versions, err = self._get_versions_by_cloud()
            # 缓存数据到本地
            if isinstance(self.stable_versions, list) and len(self.stable_versions) > 1:
                self._save_cached(self.stable_versions)
            else:
                print(err, file=_vm_std.out)

        if force and not self.stable_versions:
            self.stable_versions = self._get_versions_by_local()

        if not self.stable_versions:
            self.stable_versions = []

        return self.stable_versions

    def _async_get_versions(self):
        pyvm_mgr = copy.deepcopy(self)

        def get_versions():
            pyvm_mgr.async_version = False
            pyvm_mgr.get_py_version(force=True)

        task = threading.Thread(target=get_versions)
        task.start()

    def _get_versions_by_local(self) -> [Optional[List[PythonVersion]]]:
        """
        获取本地稳定版本的缓存数据
        """
        local_path = "/www/server/panel/data/pyvm"
        if not os.path.exists(local_path):
            os.makedirs(local_path)
            return None
        stable_file = os.path.join(local_path, "stable_versions.txt")
        if self.is_pypy:
            stable_file = os.path.join(local_path, "pypy_versions.txt")
        if not os.path.isfile(stable_file):
            return None
        with open(stable_file, "r") as f:
            if self.is_pypy:
                stable_versions = []
                for line in f.readlines():
                    v, filename = line.split("|")
                    stable_versions.append(PythonVersion(v, is_pypy=True, filename=filename))
            else:
                stable_versions = [PythonVersion(line.strip()) for line in f.readlines()]

        return stable_versions

    def _get_versions_by_cloud(self) -> Tuple[Optional[List[PythonVersion]], Optional[str]]:
        """
        获取云端支持的稳定版本 排除2.7的稳定版本以外的其他版本
        """
        if self.is_pypy:
            return self._get_pypy_versions_by_cloud()

        res = get_index_of_python()
        if res is None:
            return None, "无法链接到云端，请检查网络链接"
        self._base_url: str = res["url"]
        data_txt: str = res["data"]

        try:
            stable_go_versions = self.__parser_xml(data_txt)
            return stable_go_versions, None
        except:
            traceback.print_exc(file=_vm_std.err)
            return None, "解析错误"

    def _get_pypy_versions_by_cloud(self) -> Tuple[Optional[List[PythonVersion]], Optional[str]]:
        """
        获取云端支持的稳定版本 排除2.7的稳定版本以外的其他版本
        """

        if self.base_url is None:
            return None, "无法链接到云端，请检查网络链接"
        try:
            stable_versions = []
            ver_json = json.loads(requests.get(self.base_url + "versions.json").text)
            arch = 'aarch64' if is_aarch64() else "x64"
            for i in ver_json:
                if i["stable"] is True and i["latest_pypy"] is True:
                    for file in i["files"]:
                        if file["arch"] == arch and file["platform"] == "linux":
                            stable_versions.append(
                                PythonVersion(i["python_version"], is_pypy=True, filename=file["filename"])
                            )
            return stable_versions, None
        except:
            traceback.print_exc(file=_vm_std.err)
            return None, "解析错误"

    def __parser_xml(self, data_txt: str) -> List[PythonVersion]:
        res_list = []
        # 只取pre部分
        start = data_txt.rfind("<pre>")
        end = data_txt.rfind("</pre>") + len("</pre>")
        if not start > 0 or not end > 0:
            return res_list
        data_txt = data_txt[start:end] # 去除hr标签导致的错误
        last_2 = {
            "data": (2, 0, 0),
            "version": None,
        }

        root = cElementTree.fromstring(data_txt)
        for data in root.findall("./a"):
            v_str = data.text
            if v_str.startswith("2."):
                ver = v_str.strip("/")
                t_version = parse_version_to_list(ver)
                if t_version > last_2["data"]:
                    last_2["data"] = t_version
                    last_2["version"] = ver
                continue
            if v_str.startswith("3."):
                p_v = PythonVersion(v_str.strip("/"))
                res_list.append(p_v)
                continue

        if last_2["version"]:
            res_list.insert(0, PythonVersion(last_2["version"]))

        res_list.sort(key=lambda x: x.ver_t)

        need_remove = []
        for ver in res_list[::-1]:
            if not self.test_last_version_is_stable(ver):
                need_remove.append(ver)
            else:
                break
        for ver in need_remove:
            res_list.remove(ver)

        return res_list

    # 检查最新的版本是否有正式发布版本包
    def test_last_version_is_stable(self, ver: PythonVersion) -> bool:
        response = requests.get("{}{}/".format(self.base_url, ver.version), timeout=10)
        data = response.text
        if data.find(ver.file_name) != -1:
            return True
        else:
            return False

    def _save_cached(self, stable_go_versions: List[PythonVersion]) -> None:
        local_path = "/www/server/panel/data/pyvm"
        if not os.path.exists(local_path):
            os.makedirs(local_path)

        if self.is_pypy:
            with open(os.path.join(local_path, "pypy_versions.txt"), "w") as f:
                for py_v in stable_go_versions:
                    f.write(py_v.version + "|" + py_v.file_name + "\n")
            return

        with open(os.path.join(local_path, "stable_versions.txt"), "w") as f:
            for py_v in stable_go_versions:
                f.write(py_v.version + "\n")

    @staticmethod
    def del_cached():
        local_path = "/www/server/panel/data/pyvm"
        stable_file = os.path.join(local_path, "stable_versions.txt")
        pypy_file = os.path.join(local_path, "pypy_versions.txt")
        if os.path.isfile(stable_file):
            os.remove(stable_file)
        if os.path.isfile(pypy_file):
            os.remove(pypy_file)

    def api_ls(self) -> Tuple[List[str], List[str]]:
        return [i.strip() for i in os.listdir(self.bt_python_path) if i.startswith("2") or i.startswith("3")], \
            [i.strip() for i in os.listdir(self.bt_pypy_path) if i.startswith("2") or i.startswith("3")]

    def cmd_ls(self) -> None:
        cpy_versions, pypy_versions = self.api_ls()
        versions = pypy_versions if self.is_pypy else cpy_versions
        if not versions:
            print("未安装任何一个版本的Python解释器")
            return
        print("version: ")
        for i in versions:
            print("    " + i)

    def api_ls_remote(self, is_all: bool, force=False) -> Tuple[Optional[List[PythonVersion]], Optional[str]]:
        self.get_py_version(force)
        self.stable_versions.sort(key=lambda k: k.ver_t, reverse=True)
        if is_all:
            return self.stable_versions, None
        res_new = []
        tow_list = [0, 0]
        for i in self.stable_versions:
            if i.ver_t[:2] != tow_list:
                res_new.append(i)
                tow_list = i.ver_t[:2]

        return res_new, None

    def cmd_ls_remote(self, is_all: bool) -> None:
        stable, err = self.api_ls_remote(is_all)
        cpy_installed, pypy_install = self.api_ls()
        installed = pypy_install if self.is_pypy else cpy_installed
        if err:
            print("获取版本信息时出错了", file=sys.stderr)
            print(err, file=sys.stderr)
        print("Stable Version:")
        for i in stable:
            if i.version in installed:
                i.version += "    <- installed"
            print("    " + i.version)

    def _get_version(self, version) -> Union[PythonVersion, str]:
        stable, err = self.api_ls_remote(True)
        if err:
            if self.use_shell:
                print("获取版本信息时出错了", file=_vm_std.err)
                print(err, file=_vm_std.err)
            return err
        for i in stable:
            if i.version == version:
                return i

        if self.use_shell:
            print("未找到对应版本", file=_vm_std.err)
        return "未找到对应版本"

    def re_install_pip_tools(self, version, python_path):
        py_v = self._get_version(version)
        if isinstance(py_v, str):
            return False, py_v
        if not py_v.installed:
            return False, "未安装的版本"
        if not self.is_pypy:
            public.ExecShell("rm -rf {}/bin/pip*".format(python_path))
            public.ExecShell(
                "rm -rf {}/lib/python{}.{}/site-packages/pip*".format(python_path, py_v.ver_t[0], py_v.ver_t[1]))
        else:
            public.ExecShell("rm -rf {}/bin/pip*".format(python_path))
            public.ExecShell(
                "rm -rf {}/lib/pypy{}.{}/site-packages/pip*".format(python_path, py_v.ver_t[0], py_v.ver_t[1])
            )

        py_v.install_pip_tool(python_path)

    def api_install(self, version) -> Tuple[bool, str]:
        py_v = self._get_version(version)
        if isinstance(py_v, str):
            return False, py_v
        if self.base_url is None:
            return False, "网络连接错误"
        return py_v.install(self.base_url)

    def cmd_install(self, version, extended_args='') -> None:
        py_v = self._get_version(version)
        if isinstance(py_v, str):
            pass
        if self.base_url is None:
            print("网络连接错误", file=sys.stderr)
            return
        _, err = py_v.install(self.base_url, extended_args)
        if err:
            print(err, file=sys.stderr)

    def api_uninstall(self, version: str) -> Tuple[bool, str]:
        if not self.is_pypy:
            py_path = self.bt_python_path + "/" + version
        else:
            py_path = self.bt_pypy_path + "/" + version
        if os.path.exists(py_path):
            import shutil
            shutil.rmtree(py_path)
        return True, "卸载成功"

    def cmd_uninstall(self, version: str) -> None:
        _, msg = self.api_uninstall(version)
        print(msg, file=sys.stdout)
        return

    @staticmethod
    def set_std(out: TextIO, err: TextIO) -> None:
        _vm_std.out = out
        _vm_std.err = err

    @staticmethod
    def _serializer_of_list(s: list, installed: List[str]) -> List[Dict]:
        return [{
            "version": v.version,
            "type": "stable",
            "installed": True if v.version in installed else False
        } for v in s]

    def python_versions(self, refresh=False):
        res = {
            'status': True,
            'cpy_installed': [],
            'pypy_installed': [],
            'sdk': {
                "all": [],
                "streamline": [],
                "pypy": [],
            },
            'use': self.now_python_path(),
            'command_path': None,
        }
        sdk = res["sdk"]
        old_type = self.is_pypy
        cpy_installed, pypy_installed = self.api_ls()
        cpy_installed.sort(key=lambda x: int(x.split(".")[1]), reverse=True)
        res['cpy_installed'] = cpy_installed
        pypy_installed.sort(key=lambda x: int(x.split(".")[1]), reverse=True)
        res['pypy_installed'] = pypy_installed

        res["command_path"] = [{
            "python_path": os.path.join(self.bt_python_path, i, "bin"),
            "type": "version",
            "version": i,
            "is_pypy": False,
        } for i in cpy_installed] + [{
            "python_path": os.path.join(self.bt_pypy_path, i, "bin"),
            "type": "version",
            "version": i,
            "is_pypy": True,
        } for i in pypy_installed]

        # cpy
        self.is_pypy = False
        self.get_py_version(refresh)
        self.stable_versions.sort(key=lambda k: k.ver_t, reverse=True)
        if not self.stable_versions:
            sdk["all"] = sdk["streamline"] = [
                {"version": v, "type": "stable", "installed": True} for v in cpy_installed
            ]
        else:
            sdk["all"] = self._serializer_of_list(self.stable_versions, cpy_installed)
            res_new = []
            tow_list = [0, 0]
            for i in self.stable_versions:
                if i.ver_t[:2] != tow_list:
                    res_new.append(i)
                    tow_list = i.ver_t[:2]

            sdk["streamline"] = self._serializer_of_list(res_new, cpy_installed)
            for i in sdk["streamline"]:
                if i["version"] in cpy_installed:
                    cpy_installed.remove(i["version"])
            if set(cpy_installed):
                for i in set(cpy_installed):
                    sdk["streamline"].insert(0, {
                        "version": i,
                        "type": "stable",
                        "installed": True
                    })

        # pypy
        self.is_pypy = True
        self.stable_versions = []
        self.get_py_version(refresh)
        self.stable_versions.sort(key=lambda k: k.ver_t, reverse=True)
        if not self.stable_versions:
            sdk["pypy"] = [
                {"version": v, "type": "stable", "installed": True} for v in pypy_installed
            ]
        else:
            sdk["pypy"] = self._serializer_of_list(self.stable_versions, pypy_installed)

        self.stable_versions = None
        self.is_pypy = old_type

        return res


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='pyvm Python解释器版本管理器')
    parser.add_argument('-pypy', action='store_true', help='管理PyPy解释器')
    # 添加子命令
    subparsers = parser.add_subparsers(title='operation', dest='command')
    # 添加ls子命令
    subparsers.add_parser('ls', help='展示已安装的Python解释器版本')
    subparsers.add_parser('clear_cache', help='清除版本缓存')
    # 添加ls子命令
    parser_ls_r = subparsers.add_parser('ls-remote', help='展示可安装Python解释器版本，默认只展示每个版本中较新的版本')
    parser_ls_r.add_argument('-a', action='store_true', help='展示可以安装的所有Python解释器版本')
    # 添加install子命令
    parser_install = subparsers.add_parser('install', help='安装指定版本')
    parser_install.add_argument('version', type=str, help='要安装的Python版本，例如3.10.0')
    parser_install.add_argument(
        '--extend', type=str, default='',
        help="传递给Python编译的额外选项，用单引号包围多个选项，如'--disable-ipv6 --enable-loadable-sqlite-extensions'"
    )

    # 添加uninstall子命令
    parser_uninstall = subparsers.add_parser('uninstall', help='卸载并删除指定版本')
    parser_uninstall.add_argument('uninstall_param', type=str, help='完整的版本号')
    # 添加install_pip子命令
    parser_uninstall = subparsers.add_parser('install_pip', help='卸载并删除指定版本')
    parser_uninstall.add_argument('install_pip_param', type=str, help='完整的版本号')

    input_args = parser.parse_args()
    pyvm = PYVM()
    if isinstance(pyvm, str):
        print(pyvm, file=sys.stderr)
        exit(1)
    if input_args.pypy:
        pyvm.is_pypy = True
    pyvm.use_shell = True
    if input_args.command == 'clear_cache':
        pyvm.del_cached()
    elif input_args.command == 'ls':
        pyvm.cmd_ls()
    elif input_args.command == "ls-remote":
        _is_all = True if input_args.a else False
        pyvm.cmd_ls_remote(_is_all)
    elif input_args.command == "install":
        extended = input_args.extend
        _flag, _v = PythonVersion.parse_version(input_args.version)
        if _flag:
            pyvm.cmd_install(_v, extended)
        else:
            print("版本参数错误，应该是1.xx.xx的结构", file=sys.stderr)
    elif input_args.command == "uninstall":
        _flag, _v = PythonVersion.parse_version(input_args.uninstall_param)
        if _flag:
            pyvm.cmd_uninstall(_v)
        else:
            print("版本参数错误，应该是1.xx.xx的结构", file=sys.stderr)
    elif input_args.command == "install_pip":
        _flag, _v = PythonVersion.parse_version(input_args.install_pip_param)
        if _flag:
            pyvm.re_install_pip_tools(_v, pyvm.bt_python_path + "/" + _v)
        else:
            print("版本参数错误，应该是1.xx.xx的结构", file=sys.stderr)
    else:
        print("使用pyvm -h 查看操作指令", file=sys.stderr)
