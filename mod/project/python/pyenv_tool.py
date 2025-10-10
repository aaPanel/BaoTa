# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: baozi <baozi@bt.cn>
# -------------------------------------------------------------------
# ------------------------------
# python项目-虚拟环境管理模块
# ------------------------------
import pwd
import re
import os
import json
import subprocess
import time
import sys
import traceback
import shutil
from collections import OrderedDict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable, Union

if "/www/server/panel/class" not in sys.path:
    sys.path.append("/www/server/panel/class")

import public


_SYS_BIN_PATH =("/usr/local/sbin", "/usr/local/bin", "/usr/sbin", "/usr/bin", "/sbin", "/bin")


# 1. set_python_version 设置环境     2. uninstall_py_version 移除或卸载环境


def _run_command_with_call_log(cmd: Union[List[str], str], call_log: Optional[Callable[[str], None]] = None, user='') -> Optional[str]:
    if not callable(call_log):
        call_log = lambda x: print(x)

    if user and user != "root":
        res = pwd.getpwnam(user)
        uid = res.pw_uid
        gid = res.pw_gid

        def pre_exec_fn():
            os.setgid(gid)
            os.setuid(uid)
    else:
        pre_exec_fn = None

    # 执行命令
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=True,
            preexec_fn=pre_exec_fn
        )

        # 实时读取输出
        while True:
            output = process.stdout.readline()  # type: ignore
            if output == '' and process.poll() is not None:
                break
            if output:
                call_log(output.strip())

        # 检查返回码
        if process.returncode != 0:
            error_msg = "执行失败，返回码：{}".format(process.returncode)
            call_log(error_msg)
            return error_msg

        return None

    except Exception as e:
        error_msg = str(e)
        call_log(error_msg)
        return error_msg


def python_manager_path() -> str:
    _p = "/www/server/python_manager"
    if os.path.exists(_p):
        return os.path.realpath(_p)
    return _p


def pyenv_path() -> str:
    _p = "/www/server/pyporject_evn"
    if os.path.exists(_p):
        return os.path.realpath(_p)
    return _p


class PythonEnvironment:
    """Python环境元数据载体类"""
    _BT_PROJECT_ENV_SHELL = "/www/server/panel/script/btpyprojectenv.sh"
    _bt_etc_pyenv = "/www/server/panel/data/bt_etc_pyenv.sh"
    project_to_pyenv_map_file = "/www/server/panel/data/python_project_name2env.txt"
    default_pip_source = "https://mirrors.aliyun.com/pypi/simple/"
    _ONLY_BINARY_NAMES = {"numpy", "scipy", "pandas", "cryptography", "pyOpenSSL", "Pillow", "opencv-python","psycopg2-binary", "opencv", "mysqlclient", "lxml", "pyarrow"}
    _PYENV_FORMAT_DATA = """
# Start-Python-Env 命令行环境设置
if [ -f '/www/server/panel/data/bt_etc_pyenv.sh' ]; then source /www/server/panel/data/bt_etc_pyenv.sh; fi
# End-Python-Env
"""

    @staticmethod
    def return_profile():
        if os.path.exists('/root/.bash_profile'):
            return '/root/.bash_profile'
        if os.path.exists('/root/.bashrc'):
            return '/root/.bashrc'
        fd = open('/root/.bashrc', mode="w", encoding="utf-8")
        fd.close()
        return '/root/.bashrc'

    # ptah python安装路径
    def __init__(self, bin_path: str, version: str, env_type: str, **kwargs):
        self.bin_path = bin_path
        self.version = version
        self.env_type = env_type  # conda venv virtualenv system
        self.conda_path = kwargs.get("conda_path", "")
        self.venv_name = kwargs.get("venv_name", "")
        self.activate_sh = kwargs.get("activate_sh", "")
        self.system_path = kwargs.get("system_path", "")
        self.ps = kwargs.get("ps", "")
        self.site_packages = kwargs.get("site_packages", "")  # 应当支持site-packages 为空的情况
        self._pip_source = ""
        if not os.path.isfile(self.project_to_pyenv_map_file):
            public.writeFile(self.project_to_pyenv_map_file, "")

    def set_pip_source(self, pip_source: str):
        self._pip_source = pip_source

    def to_dict(self, **kwargs) -> Dict:
        data = {
            "bin_path": self.bin_path,
            "version": self.version,
            "type": self.env_type,
            "conda_path": self.conda_path,
            "venv_name": self.venv_name,
            "activate_sh": self.activate_sh,
            "system_path" : self.system_path,
            "ps": self.ps,
            "site_packages": self.site_packages
        }
        for k, v in kwargs.items():
            if k in data:
                continue
            data[k] = v
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> Optional["PythonEnvironment"]:
        if not isinstance(data, dict):
            return None
        try:
            return cls(
                data["bin_path"],
                data["version"],
                data["type"],
                conda_path=data.get("conda_path"),
                venv_name=data.get("venv_name"),
                activate_sh=data.get("activate_sh"),
                system_path=data.get("system_path"),
                ps=data.get("ps"),
                site_packages=data.get("site_packages"),
            )
        except Exception as e:
            # print("PythonEnvironment.from_dict error: {}".format(str(e)))
            return None

    def create_venv(self, env_path: str, ps: str = "") -> Optional[str]:
        if self.env_type != "system":
            return "请选择一个系统环境进行虚拟环境的创建"

        # 创建目录
        parent_dir = os.path.dirname(env_path)
        if not os.path.exists(parent_dir):
            try:
                os.makedirs(parent_dir)
            except Exception as e:
                return "创建目录失败：{}".format(str(e))

        try:
            subprocess.run(
                [self.bin_path, "-m", "venv", env_path],
                capture_output=True, text=True, check=True
            )
        except Exception as e:
            print("创建虚拟环境失败: {}".format(str(e)))
            return str(e)

        site_packages = _EnvironmentDetector.get_site_packages(env_path + "/bin/python")
        _ep = EnvironmentReporter()
        _ep.update_report({
            "bin_path": env_path + "/bin/python",
            "version": self.version,
            "type": "venv",
            "conda_path": self.conda_path,
            "venv_name": os.path.basename(env_path),
            "activate_sh": "source {}/bin/activate".format(env_path),
            "system_path": self.bin_path,
            "site_packages": site_packages,
            "ps":  ps or os.path.basename(env_path),
        })
        return None

    def create_venv_sync(self, env_path: str, ps: str = "", call_log:Optional[Callable[[str], None]] = None):
        """通过call_log函数实时返回创建日志， 应用于websocket场景"""
        if call_log is None:
            call_log = lambda x: print(x)

        # 执行命令
        res = _run_command_with_call_log([self.bin_path, "-u", "-m", "venv", env_path], call_log)
        if res is not None:
            return res

        try:
            site_packages = _EnvironmentDetector.get_site_packages(env_path + "/bin/python")
            _ep = EnvironmentReporter()
            _ep.update_report({
                "bin_path": env_path + "/bin/python",
                "version": self.version,
                "type": "venv",
                "conda_path": self.conda_path,
                "venv_name": os.path.basename(env_path),
                "activate_sh": "source {}/bin/activate".format(env_path),
                "system_path": self.bin_path,
                "site_packages": site_packages,
                "ps": ps or os.path.basename(env_path),
            })
            call_log("虚拟环境创建成功")
            return None
        except Exception as e:
            error_msg = f"更新环境配置失败：{str(e)}"
            call_log(error_msg)
            return error_msg

    def _site_pkg_name2bin(self, pkg_name: str) -> Optional[str]:
        """通过包名查询在site-packages的*-info/RECORD可执行文件的位置  (可用于 pip, gunicorn, uwsgi)"""
        record_file = ""
        name_lower = pkg_name.lower()
        if not self.site_packages or not os.path.exists(self.site_packages):
            return None
        for i in os.listdir(self.site_packages):
            i_lower = i.lower()
            if i.endswith(".dist-info") and i_lower.startswith(name_lower + "-"):
                record_file = os.path.join(self.site_packages, i, "RECORD")
                break
        if not record_file:
            return None
        with open(record_file, "r") as f:
            for line in f:
                tmp = line.split(",")
                if len(tmp) != 3:
                    continue
                # 可执行文件的位置不会site-packages在文件夹下
                if name_lower in os.path.basename(tmp[0].lower()) and tmp[0].startswith("../"):
                    bin_p = Path(self.site_packages) / tmp[0]
                    if bin_p.exists():
                        return str(bin_p.resolve())
        return None

    def uwsgi_bin(self) -> Optional[str]:
        return self._site_pkg_name2bin("uwsgi")

    def pip_bin(self) -> Optional[str]:
        return self._site_pkg_name2bin("pip")

    def gunicorn_bin(self) -> Optional[str]:
        return self._site_pkg_name2bin("gunicorn")

    def activate_shell(self) -> Optional[str]:
        """获取激活环境的shell命令， venv和conda执行对应的脚本即可，"""
        if self.env_type == "venv":
            res_sh = self.activate_sh
        elif self.env_type == "conda":
            init_sh = "{}/etc/profile.d/conda.sh".format(os.path.dirname(os.path.dirname(self.conda_path)))
            remove_panel_py = (
                "bt_env_deactivate > /dev/null 2>&1 \n"
                "export PATH=$(echo $PATH | tr ':' '\\n' | grep -v '{}' | tr '\\n' ':') \n"
                "export PATH=$(echo $PATH | tr ':' '\\n' | grep -v '{}' | tr '\\n' ':') \n".format(
                    python_manager_path(),
                    pyenv_path()
                )
            )
            return "{}{} init >/dev/null 2>&1\nsource {}\n{}".format(
                remove_panel_py, self.conda_path, init_sh, self.activate_sh
            )
        elif self.env_type == "system":
            if any((self.bin_path.startswith(i) for i in _SYS_BIN_PATH)):
                res_sh = 'export PATH="{}":"$PATH"'.format(os.path.dirname(self.bin_path))
            else:
                res_sh = "export _BT_PROJECT_ENV={} && source {} NULL \n".format(
                    os.path.dirname(os.path.dirname(self.bin_path)),
                    self._BT_PROJECT_ENV_SHELL
                )
        else:
            return ""

        if self.env_type != "conda" and len(CondaDetector().find_conda_executable()) > 0:
            res_sh = """# 彻底停用 Conda 环境并清除所有 Conda 相关路径
conda deactivate
unset CONDA_PREFIX
unset CONDA_EXE
unset _CE_CONDA
unset _CE_M
export PATH=$(echo $PATH | tr ':' '\\n' | grep -v 'conda' | tr '\\n' ':') 
export LD_LIBRARY_PATH=$(echo $LD_LIBRARY_PATH | tr ':' '\\n' | grep -v 'conda' | tr '\\n' ':')
""" + res_sh

        return res_sh + "\n"

    def _install_pip(self, call_log:Optional[Callable[[str], None]] = None) -> Optional[str]:
        if not callable(call_log):
            call_log = lambda x: print(x)
        sh = self.activate_shell() + "\n" + " ".join([self.bin_path, "-u", "-m", "ensurepip"])
        return _run_command_with_call_log(sh, call_log)

    def pip_install(self, pkg: str, version: str= "", no_cache: bool=False, call_log:Optional[Callable[[str], None]] = None) -> Optional[str]:
        if not self.pip_bin():
            self._install_pip(call_log)
        if not callable(call_log):
            call_log = lambda x: print(x)
        cmd = [self.pip_bin(), "install"]
        if version:
            cmd.append("{}=={}".format(pkg, version))
        else:
            cmd.append(pkg)

        cmd.append("-i")
        if self._pip_source:
            cmd.append(self._pip_source)
        else:
            cmd.append(self.default_pip_source)
        if no_cache:
            cmd.append("--no-cache-dir")

        cmd_pip = " ".join(cmd)
        if pkg.lower().find("mysqlclient") != -1:
            mysql_flag = self.build_mysql_env()
            cmd_pip = mysql_flag + cmd_pip

        cmd = self.activate_shell() + "\n" + cmd_pip
        error_list = set()
        err_msg = "ERROR: Failed building wheel for"
        def check_error_with_log(output: str) -> None:
            idx = output.find(err_msg)
            if idx != -1:
                pkg_name = output[idx + len(err_msg):].strip().split()[0].strip()
                if pkg_name in self._ONLY_BINARY_NAMES:
                    error_list.add(pkg_name)
            return call_log(output)

        res = _run_command_with_call_log(cmd, check_error_with_log)
        if error_list:
            call_log("发现编译错误的包:【{}】,尝试以二进制方式安装".format(", ".join(error_list)))
            cmd = cmd + "  --only-binary=" + ",".join(error_list)
            return _run_command_with_call_log(cmd, call_log)
        return res

    @staticmethod
    def build_mysql_env() -> str:
        if os.path.exists("/www/server/mysql"):
            return (
                "export LD_LIBRARY_PATH=\"/www/server/mysql/lib:$LD_LIBRARY_PATH\""
                "export MYSQLCLIENT_CFLAGS='-I/www/server/mysql/include'\n"
                "export MYSQLCLIENT_LDFLAGS='-L/www/server/mysql/lib -lmysqlclient'\n"
            )
        elif os.path.exists("/usr/local/mysql"):
            return (
                "export MYSQLCLIENT_CFLAGS='-I/usr/local/mysql/include'\n"
                "export MYSQLCLIENT_LDFLAGS='-L/usr/local/mysql/lib -lmysqlclient'\n"
            )
        else:
            return ""

    def pip_uninstall(self, pkg: str, call_log:Optional[Callable[[str], None]] = None) -> Optional[str]:
        if not self.pip_bin():
            return "pip未安装"
        cmd = self.activate_shell() + "\n" + " ".join([self.pip_bin(), "uninstall", "-y", pkg])
        return _run_command_with_call_log(cmd, call_log)

    def pip_list(self, force: bool = False) -> List[Tuple[str, str]]:
        if not self.pip_bin():
            return []
        prefix_path = os.path.dirname(os.path.dirname(self.bin_path))
        if not force and not any (self.bin_path.startswith(i) for i in _SYS_BIN_PATH):
            try:
                old_cache = json.loads(public.readFile(os.path.join(prefix_path, "pip_list.cache")))
                mtime = int(os.path.getmtime(self.site_packages))
                if old_cache and int(old_cache.get("mtime", 0)) == mtime:
                    return old_cache["data"]
            except:
                pass

        cmd = self.activate_shell() + "\n" + " ".join([self.pip_bin(), "list"])
        res_out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL, shell=True)
        pip_list = []
        for line in res_out.split("\n"):
            try:
                tmp = line.strip().split()
                if len(tmp) >= 2:
                    if tmp[0] == "Package":
                        continue
                    if tmp[0].startswith("-----"):
                        continue
                    pip_list.append((tmp[0], tmp[1]))
            except:
                pass
        mtime = int(os.path.getmtime(self.site_packages))
        public.writeFile(os.path.join(prefix_path, "pip_list.cache"), json.dumps({"mtime": mtime, "data": pip_list}))
        return pip_list

    def pkg_file_exits(self, pkg_name: str) -> bool:
        pkg_name_lower = pkg_name.lower()
        if not self.site_packages or not os.path.exists(self.site_packages):
            return False
        for name in os.listdir(self.site_packages):
            name_lower = name.lower()
            if name_lower.startswith(pkg_name_lower) and name.endswith(".dist-info"):
                return True

        return False

    def init_site_server_pkg(self, call_log:Optional[Callable[[str], None]] = None) -> bool:
        pkg_list = ("uwsgi", "gunicorn", "uvicorn", "hypercorn", "daphne")
        status = True
        for pkg in pkg_list:
            if self.pkg_file_exits(pkg):
                call_log("{} 已安装".format(pkg))
                continue
            call_log("正在安装 {} ....".format(pkg))
            if pkg not in [i[0] for i in self.pip_list()]:
                res = self.pip_install(pkg, call_log=call_log)
                if res:
                    status = False
        return status

    def exec_shell(self,cmd: str, call_log:Optional[Callable[[str], None]] = None, user=""):
        cmd = self.activate_shell() + "\n" + cmd
        return _run_command_with_call_log(cmd, call_log=call_log, user=user)

    @classmethod
    def profile_check_use(cls):
        out, _ = public.ExecShell("lsattr {}".format(cls.return_profile()))
        return out.find("--i") == -1

    @staticmethod
    def _remove_old_python_env():
        try:
            data = public.readFile("/etc/profile")
            rep = re.compile(r'# +Start-Python-Env[^\n]*\n(export +PATH=".*")\n# +End-Python-Env')
            rep2 = re.compile(r'# +Start-Python-Env[^\n]*\nif\s+\[ +-f[^\n]*\n# +End-Python-Env')
            data = rep.sub("", data)
            data = rep2.sub("", data)
            public.writeFile("/etc/profile", data)
        except:
            pass

    @classmethod
    def set_profile_env(cls, pyenv: Optional["PythonEnvironment"]) -> Optional[str]:
        if pyenv and pyenv.env_type == "conda":
            return "Conda环境不支持直接设置，请在命令行中执行conda activate {}".format(pyenv.venv_name)
        if not cls.profile_check_use():
            return "疑似开启了系统加固，无法操作环境变量相关设置"
        _profile = cls.return_profile()
        if not os.path.isfile("/etc/profile"):
            return "文件不存在"
        cls._remove_old_python_env()
        data = public.readFile(_profile)
        data = re.sub(r'# +Start-Python-Env[^\n]*\nif\s+\[ +-f[^\n]*\n# +End-Python-Env', "", data)
        data += cls._PYENV_FORMAT_DATA
        public.writeFile(_profile, data)
        if not pyenv and os.path.isfile(cls._bt_etc_pyenv):
            os.remove(cls._bt_etc_pyenv)
            return None
        if pyenv:
            cmd = "#{}\n{}".format(pyenv.bin_path, pyenv.activate_shell())
            public.writeFile(cls._bt_etc_pyenv, cmd)
        return None

    def remove(self) -> Optional[str]:
        if self.env_type == "conda":
            return "Conda环境不支持操作，请在命令行中执行conda remove -n {}".format(self.venv_name)
        elif not self.bin_path.startswith(python_manager_path()) and \
                not self.bin_path.startswith(pyenv_path()):
            return "非面板安装或创建的Python环境不支持操作，请手动处理"
        try:
            home = os.path.dirname(os.path.dirname(self.bin_path))
            public.print_log(os.path.isdir(home) and (home.startswith(python_manager_path()) or home.startswith(pyenv_path())), home)
            if os.path.isdir(home) and (home.startswith(python_manager_path()) or home.startswith(pyenv_path())):
                shutil.rmtree(home)
        except:
            return "删除失败"

    @property
    def can_remove(self):
        if self.env_type == "conda":
            return False
        if not self.bin_path.startswith(python_manager_path()) and \
                not self.bin_path.startswith(pyenv_path()):
            return False
        return True

    @property
    def can_create(self):
        if self.env_type == "system":
            return True
        return False

    @property
    def can_set_default(self):
        if self.env_type == "conda":
            return False
        return True

    @property
    def path_name(self):
        if any(self.bin_path.startswith(i) for i in _SYS_BIN_PATH):
            return ""

        return Path(self.bin_path).parent.parent.name

    @classmethod
    def profile_env_bin(cls) -> Optional[str]:
        if not os.path.isfile("/etc/profile"):
            return None
        data = public.readFile("/etc/profile")
        for line in data.split("\n"):
            if line.find("source /www/server/panel/data/bt_etc_pyenv.sh"):
                break
        else:
            return None

        active_data: str = public.readFile(cls._bt_etc_pyenv)
        if not active_data:
            return None

        bin_path = active_data.split("\n", 1)[0].strip("#")
        return bin_path

    def use2project(self, project_name: str):
        if not project_name:
            return
        with open(self.project_to_pyenv_map_file, "r+") as f:
            home = os.path.dirname(os.path.dirname(self.bin_path))
            for i in _SYS_BIN_PATH:
                if self.bin_path.startswith(i):
                    home = i
                    break
            data = f.read()

            lines = data.split("\n")
            for i, line in enumerate(lines):
                if line.startswith(project_name + ":"):
                    lines[i] = "{}:{}".format(project_name, home)
                    break
            else:
                lines.append("{}:{}".format(project_name, home))
            f.seek(0)
            f.truncate()
            f.write("\n".join(lines))


class _EnvironmentDetector:
    """环境检测基类"""
    _ver_regexp = re.compile(r"Python\s+(\d+\.\d+(\.\d+)?)")
    _pypy_regexp = re.compile(r"PyPy\s+(\d+\.\d+(\.\d+)?)")
    _site_packages_regexp = re.compile(r"pip\s+[\d.]+\s+from\s+(?P<path>(/[^/]+)+)/pip\s+\(python")

    def detect(self) -> List[PythonEnvironment]:
        raise NotImplementedError

    @staticmethod
    def now_env_path_list():
        """使用子进程获取 PATH """
        try:
            result = subprocess.run(
                ["bash", "-c", "echo $PATH"],
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip().split(":")
        except Exception as e:
            print("获取PATH失败: {}".format(str(e)))
            return os.getenv("PATH", "").split(":")

    @classmethod
    def _parse_version_data(cls, data: str) -> Optional[str]:
        ver_res = cls._ver_regexp.search(data)
        if ver_res:
            ver = ver_res.group()
        else:
            return None
        pypy_ver_res = cls._pypy_regexp.search(data)
        if pypy_ver_res:
            pypy_ver = pypy_ver_res.group()
            return "{} ({})".format(ver, pypy_ver)
        return ver

    @classmethod
    def _parse_site_packages(cls, data: str) -> Optional[str]:
        path_res = cls._site_packages_regexp.search(data)
        if path_res:
            return path_res.group("path")
        return None

    @classmethod
    def site_pkgs_by_python_bin(cls, python_bin: str) -> Optional[str]:
        lib_path = Path(python_bin).parent.parent / "lib"
        if not lib_path.is_dir():
            return None

        for p in lib_path.iterdir():
            p: Path
            if p.is_dir() and (p.name.startswith("python") or p.name.startswith("pypy")):
                site_packages_path: Path = p / "site-packages"
                if site_packages_path.is_dir():
                    return str(site_packages_path.resolve())

    @classmethod
    def site_pkgs_by_cmd(cls, python_path: str) -> Optional[str]:
        try:
            result = subprocess.run(
                [python_path, "-m", "pip", "-V"],
                capture_output=True, text=True, check=True
            )
            return cls._parse_site_packages(result.stdout.strip() + "\n" + result.stderr.strip())
        except Exception as e:
            print("获取site-packages失败: {}".format(str(e)))

    @classmethod
    def get_site_packages(cls, python_path: str) -> Optional[str]:
        if not any(python_path.startswith(p) for p in _SYS_BIN_PATH):
            site_packages = cls.site_pkgs_by_python_bin(python_path)
            if site_packages:
                return site_packages
        site_packages = cls.site_pkgs_by_cmd(python_path)
        if site_packages and os.path.isdir(site_packages):
            return site_packages


class CondaDetector(_EnvironmentDetector):
    """Conda环境检测器"""

    def __init__(self):
        self.conda_paths = []

    def find_conda_executable(self) -> List[str]:
        # 预定义候选路径（保持原有逻辑）
        conda_paths = [
            Path(os.path.expanduser("~/miniconda3")),
            Path(os.path.expanduser("~/anaconda3")),
            Path("/opt/conda"),
            Path(os.getenv("CONDA_EXE", "")).resolve().parent.parent,  # 从CONDA_EXE推导安装目录
            Path(os.getenv("CONDA_PREFIX", "")).resolve()   # 从CONDA_EXE推导安装目录
        ]

        # 新增：从系统PATH查找
        for dir_path in self.now_env_path_list():
            p = Path(dir_path)
            if p.is_dir():
                # 查找conda可执行文件（兼容符号链接）
                conda_candidate = p / "conda"
                if conda_candidate.exists():
                    conda_paths.insert(0, conda_candidate.resolve().parent.parent)  # 定位到conda安装根目录

        res_list = []
        # 验证候选路径
        for path in conda_paths:
            conda_bin = path / "condabin" / "conda"
            if str(conda_bin) not in res_list and conda_bin.exists() and os.access(conda_bin, os.X_OK):
                res_list.append(str(conda_bin))
        return res_list

    def detect(self) -> List[PythonEnvironment]:
        if not self.conda_paths:
            self.conda_paths = self.find_conda_executable()

        res_list = []
        for conda_path in self.conda_paths:
            res_list.extend(self.detect_by_conda_bin(conda_path))
        return res_list

    @classmethod
    def detect_by_conda_bin(cls, conda_path: str) -> List[PythonEnvironment]:
        res_list = []
        try:
            result = subprocess.run(
                [conda_path, "env", "list", "--json"],
                capture_output=True, text=True, check=True
            )
            env_data = json.loads(result.stdout)
            if not env_data.get("root_prefix", None):
                root_prefix = Path(conda_path.split("/bin")[0]).resolve()
            else:
                root_prefix = Path(env_data["root_prefix"]).resolve()
            # 解析环境名称和路径
            for env_spec in env_data["envs"]:
                tmp_p = Path(env_spec).resolve()
                env_name = "base" if tmp_p == root_prefix else tmp_p.name

                bin_path = "{}/bin/python".format(str(tmp_p))
                if not os.path.exists(bin_path) or not os.access(bin_path, os.X_OK):
                    bin_path = "{}/bin/python3".format(str(tmp_p))
                if not os.path.exists(bin_path) or not os.access(bin_path, os.X_OK):
                    continue
                version = cls.get_py_version(conda_path, env_name)
                if not version:
                    continue

                site_packages = cls.get_site_packages(bin_path)
                if not site_packages:
                    continue

                pe = PythonEnvironment(bin_path, version, "conda")
                pe.conda_path = conda_path
                pe.venv_name = env_name
                pe.activate_sh = "conda activate {}".format(env_name)
                pe.site_packages = site_packages
                res_list.append(pe)

        except Exception as e:
            print(f"Conda检测失败: {str(e)}")
            pass
        return res_list

    @classmethod
    def get_py_version(cls, conda_path: str, name: str) -> Optional[str]:
        """conda run -n base python --version"""
        try:
            result = subprocess.run(
                [conda_path, "run", "-n", name, "python", "--version"],
                capture_output=True, text=True, check=True
            )
            return cls._parse_version_data(result.stdout.strip() + "\n" + result.stderr.strip())
        except Exception as e:
            print(f"Conda环境检测失败: {str(e)}")
            return None

    @classmethod
    def find_conda_python(cls, path: str) -> List[PythonEnvironment]:
        p = Path(path).expanduser().resolve()
        if p.is_file() and os.access(p, os.X_OK):
            return cls.detect_by_conda_bin(str(p))
        return []


class VirtualEnvDetector(_EnvironmentDetector):
    """虚拟环境检测器（支持venv/virtualenv）"""
    ENV_MARKERS = ["pyvenv.cfg", "bin/activate"]
    NAME_REGEXPS = [
        re.compile(r'''!=\s*x\s*]\s*;\s*then\s*VIRTUAL_ENV_PROMPT=['"]?(?P<name>[^'"\s]+)['"]?\n'''),
        re.compile(r'''_OLD_VIRTUAL_PS1="\$\{PS1:-}"\s+PS1=['"\s]*\(['"\s]*(?P<name>.*)['"\s]*\)['"\s]*\$\{PS1:-}"'''),
        re.compile(r'''VIRTUAL_ENV=["']?(/.*)/(?P<name>\S*)["']?\n'''),
    ]

    def __init__(self, search_dirs: List[str]):
        self.search_dirs = search_dirs

    def detect(self) -> List[PythonEnvironment]:
        envs = []
        max_depth = 2
        find_bin_path = set()
        for base_dir in self.search_dirs:
            expanded_dir = os.path.expanduser(base_dir)
            if not os.path.exists(expanded_dir):
                continue

            for root, dirs, _ in os.walk(expanded_dir, topdown=True):
                # 避免过多搜索子目录
                if root.replace(expanded_dir, "").count(os.sep) >= max_depth:
                    dirs.clear()
                    continue

                for tmp_dir in dirs:
                    if all(Path(root) / tmp_dir / marker  for marker in self.ENV_MARKERS):
                        bin_path = "{}/bin/python".format(root)
                        if not os.path.exists(bin_path) or not os.access(bin_path, os.X_OK):
                            bin_path = "{}/bin/python3".format(root)
                        if not os.path.exists(bin_path) or not os.access(bin_path, os.X_OK):
                            continue
                        if bin_path in find_bin_path:
                            continue
                        data = self.get_env_info(root)
                        if not data:
                            continue
                        site_packages = self.get_site_packages(bin_path)
                        if not site_packages:
                            continue
                        find_bin_path.add(bin_path)
                        pe = PythonEnvironment(bin_path, data[1], "venv")
                        pe.activate_sh = "source {}/bin/activate".format(root)
                        pe.system_path = data[0]
                        pe.venv_name = data[2]
                        pe.site_packages = site_packages
                        envs.append(pe)
        return envs

    @classmethod
    def get_env_info(cls, path: str) -> Optional[Tuple[str, str, str]]:
        cfg_file = Path(path) / "pyvenv.cfg"
        atv_file = Path(path) / "bin" / "activate"
        if not cfg_file.exists():
            return None

        if not atv_file.exists():
            return None

        version_list = []
        name = ""
        try:
            with open(cfg_file, "r") as fp:
                for line in fp:
                    if line.startswith("home ="):
                        # home_dir = line.split("=")[1].strip()  # 改为从虚拟环境的bin目录中获取
                        continue
                    elif line.startswith("implementation ="):
                        version_list.insert(0, line.split("=")[1].strip())
                    elif line.startswith("version_info ="):
                        v = line.split("=")[1].strip()
                        if v.count(".") > 2:
                            v = ".".join(v.split(".")[:3])
                        version_list.append(v)
                    elif line.startswith("version ="):
                        version_list.append(line.split("=")[1].strip())
            with open(atv_file, "r") as fp:
                atv_data = fp.read()
            for regexp in cls.NAME_REGEXPS:
                res = regexp.search(atv_data)
                if res:
                    name = res.group("name").strip().strip('"\'')
                    break
        except Exception as e:
            print("获取虚拟环境信息失败：{}".format(str(e)))
            return None

        if not version_list:
            return None

        bin_path = "{}/bin/python".format(path)
        if not os.path.exists(bin_path) or not os.access(bin_path, os.X_OK):
            bin_path = "{}/bin/python3".format(path)
            if not os.path.exists(bin_path) or not os.access(bin_path, os.X_OK):
                return None

        real_bin = os.path.realpath(bin_path)
        if len(version_list) == 1:
            if os.path.basename(real_bin).startswith("pypy"):
                version_list.insert(0, "Python")
                version_list.append("(PyPy)")
            else:
                version_list.insert(0, "Python")

        version = " ".join(version_list)
        if not name:
            name = os.path.basename(path)

        return real_bin, version, name

    @classmethod
    def find_venv_python(cls, path: str) -> Optional[PythonEnvironment]:
        p = Path(path).resolve()
        while str(p) != "/":
            if not p.exists() or not p.is_dir():
                break
            bin_path = "{}/bin/python".format(str(p))
            if not os.path.exists(bin_path) or not os.access(bin_path, os.X_OK):
                bin_path = "{}/bin/python3".format(str(p))
                if not os.path.exists(bin_path) or not os.access(bin_path, os.X_OK):
                    p = p.parent
                    continue

            data = cls.get_env_info(str(p))
            if not data:
                p = p.parent
                continue

            site_packages = cls.get_site_packages(bin_path)
            if not site_packages:
                p = p.parent
                continue

            pe = PythonEnvironment(bin_path, data[1], "venv")
            pe.activate_sh = "source {}/bin/activate".format(str(p))
            pe.system_path = data[0]
            pe.venv_name = data[2]
            pe.site_packages = site_packages
            return pe

        return None


class SystemPythonDetector(_EnvironmentDetector):
    """系统Python检测器"""

    def __init__(self, search_dirs: List[str]):
        self.search_dirs = search_dirs
        self.python_bin_map = {}
        self.regexp_name = re.compile("^(python|pypy)([23](\.\d+)?)?$")

    @staticmethod
    def get_conda_path() -> List[str]:
        conda_path = []
        for i in CondaDetector().find_conda_executable():
            base_path = i.split("/bin/")[0]
            envs_path = base_path + "/envs"
            conda_path.extend([envs_path, base_path])
        return conda_path

    def is_conda_python(self, python_bin: str) -> bool:
        if hasattr(self, "_conda_path"):
            _conda_path = self._conda_path
        else:
            _conda_path = self.get_conda_path()
            setattr(self, "_conda_path", _conda_path)
        for i in _conda_path:
            if python_bin.startswith(i):
                return True
        return False

    def detect(self) -> List[PythonEnvironment]:
        # 新增：从系统PATH查找
        self.python_bin_map = {}
        for dir_path in self.now_env_path_list():
            p = Path(dir_path)
            if not p.is_dir():
                continue

            self.detect_by_path(p)

        max_depth = 2
        for base_dir in self.search_dirs:
            expanded_dir = os.path.expanduser(base_dir)
            if not os.path.exists(expanded_dir):
                continue

            for root, dirs, _ in os.walk(expanded_dir, topdown=True):
                # 避免过多搜索子目录
                if root.replace(expanded_dir, "").count(os.sep) >= max_depth:
                    dirs.clear()
                    continue

                for tmp_dir in dirs:
                    self.detect_by_path(Path(root) / tmp_dir)

        res_list = []
        for python_bin in self.python_bin_map.values():
            if self.is_conda_python(str(python_bin)):
                continue
            version = self.get_py_version(str(python_bin))
            if not version:
                continue

            site_packages = self.get_site_packages(str(python_bin))
            if not site_packages:
                site_packages = ""

            pe = PythonEnvironment(str(python_bin), version, "system")
            pe.site_packages = site_packages
            res_list.append(pe)

        return res_list

    def detect_by_path(self, test_path: Path):
        for python_bin_name in os.listdir(test_path):
            if not self.regexp_name.match(python_bin_name):
                continue
            python_bin = Path(test_path) / python_bin_name
            if python_bin.exists() and python_bin.is_file() and not python_bin.is_symlink() and os.access(python_bin, os.X_OK):
                fs_inode = os.stat(python_bin).st_ino
                if fs_inode in self.python_bin_map and len(str(python_bin)) > len(self.python_bin_map[fs_inode]):
                    continue
                self.python_bin_map[fs_inode] = str(python_bin.resolve())
                # 如果查询目录不是系统目录，此时应该为Python安装目录， 则只检查一个有效的Python环境
                if str(test_path) not in _SYS_BIN_PATH:
                    return

    @classmethod
    def get_py_version(cls, python_bin: str) -> Optional[str]:
        try:
            res = subprocess.run([python_bin, "--version"],
                capture_output=True, text=True, check=True
            )
            return cls._parse_version_data(res.stdout.strip() + "\n" + res.stderr.strip())
        except Exception as e:
            print("获取Python版本失败：{}".format(str(e)))
            return None

    @classmethod
    def find_system_python(cls, path: str) -> Optional[PythonEnvironment]:
        p = Path(path).resolve()
        if p.is_file() and os.access(p, os.X_OK):
            if cls.is_conda_python(cls([]), str(p)):
                return None
            version = cls.get_py_version(str(p))
            if not version:
                return None
            site_packages = cls.get_site_packages(str(p))
            if not site_packages:
                site_packages = ""
            ep = PythonEnvironment(str(p), version, "system")
            ep.site_packages = site_packages
            return ep
        return None


class EnvironmentReporter:
    """环境报告生成器"""
    REPORT_FILE = "/www/server/panel/data/python_project_env.json"

    def __init__(self):
        _python_manager_path = python_manager_path()
        _pyenv_path = pyenv_path()
        self.detectors = [
            CondaDetector(),
            VirtualEnvDetector([
                _pyenv_path,
                _python_manager_path,
            ]),
            SystemPythonDetector([
                _pyenv_path,
                "{}/versions".format(_pyenv_path),
                "{}/pypy_versions".format(_pyenv_path),
                "{}/versions".format(_python_manager_path),
            ])
        ]

    def generate_report(self) -> Dict:
        report = {"environments": [], "update_time": int(time.time())}
        for detector in self.detectors:
            try:
                envs = detector.detect()
                report["environments"].extend([e.to_dict() for e in envs])
            except Exception as e:
                print("环境检测失败：{}".format(str(e)))
                traceback.print_exc()
                continue
        return report

    @classmethod
    def update_report(cls, *now_report: Dict) -> Optional[str]:
        try:
            with open(cls.REPORT_FILE, "r") as fs:
                old_data = json.loads(fs.read())
        except:
            old_data = {"environments": [], "update_time": int(time.time())}

        path_map = OrderedDict()
        for e in old_data["environments"]:
            path_map[e["bin_path"]] = e

        add_list = []
        for e in now_report:
            if e["bin_path"] in path_map:
                tmp_ps = path_map[e["bin_path"]]["ps"]
                path_map[e["bin_path"]].update(e)
                if tmp_ps and not path_map[e["bin_path"]]["ps"]:
                    path_map[e["bin_path"]]["ps"] = tmp_ps
            else:
                path_map[e["bin_path"]] = e
                add_list.append(e)

        now_data = {"environments": add_list + old_data["environments"], "update_time": int(time.time())}
        try:
            with open(cls.REPORT_FILE, "w") as fs:
                fs.write(json.dumps(now_data, indent=4))
            return None
        except Exception as e:
            return "保存记录失败：{}".format(e)

    def init_report(self):
        if os.path.exists(self.REPORT_FILE):
            r = self.generate_report()
            # public.print_log("环境记录已存在，更新记录")
            # public.print_log(r)
            self.update_report(*r["environments"])
        else:
            with open(self.REPORT_FILE, "w") as fs:
                fs.write(json.dumps(self.generate_report(), indent=4))
        em = EnvironmentManager()
        all_py_project = public.M("sites").where("project_type=?", ("Python",)).field('id,project_config').select()
        for project in all_py_project:
            project_config: dict = json.loads(project['project_config'])
            if "python_bin" in project_config:
                continue
            p = em.get_env_py_path(project_config.get("vpath"))
            if p:
                project_config["python_bin"] = p.bin_path

            public.M("sites").where("id=?", (project['id'],)).update({"project_config": json.dumps(project_config)})



class EnvironmentManager:
    _REPORT_FILE = "/www/server/panel/data/python_project_env.json"

    def __init__(self):
        self._all_env = None

    @property
    def all_env(self) -> List[PythonEnvironment]:
        venv_src_map = {}
        if self._all_env is None:
            self._all_env = []
            for e in self.load_report()["environments"]:
                if not os.path.isfile(e["bin_path"]):  # 文件已不存在的，就不在再展示
                    continue
                tmp_p = PythonEnvironment.from_dict(e)
                self._all_env.append(tmp_p)
                if tmp_p.env_type == "venv":
                    venv_src_map[tmp_p.system_path] = tmp_p

        for tmp_p in self._all_env:
            if tmp_p.env_type == "system" and tmp_p.bin_path in venv_src_map:
                venv_src_map.pop(tmp_p.bin_path)

        for tmp_p in venv_src_map.values():
            self._all_env.remove(tmp_p)

        return self._all_env

    def get_env_py_path(self, python_path: str) -> Optional[PythonEnvironment]:
        python_path = python_path.rstrip("/")
        for tmp_p in self.all_env:
            if tmp_p.bin_path == python_path:
                return tmp_p
        # 兼容旧版本
        if python_path.startswith("/www/server/pyporject_evn/"):
            for tmp_p in self.all_env:
                if tmp_p.bin_path.startswith(python_path) and tmp_p.env_type == "system":
                    return tmp_p
        return None

    @staticmethod
    def load_report() -> Dict:
        with open(EnvironmentReporter.REPORT_FILE, "r") as fs:
            return json.loads(fs.read())

    @staticmethod
    def add_python_env(add_type: str, path: str) -> Optional[str]:
        p = Path(path)
        if not p.exists():
            return "Python环境不存在"
        if path.find("conda") and add_type == "system":
            tmp_path = path.rsplit("/bin")[0]
            if os.path.isfile(tmp_path + "/condabin/conda"):
                add_type = "conda"
                path = tmp_path + "/condabin/conda"
            elif os.path.isfile(tmp_path + "/../../condabin/conda"):
                add_type = "conda"
                path = os.path.realpath(tmp_path + "/../../condabin/conda")

        if add_type == "system":
            tmp_p = SystemPythonDetector.find_system_python(path)
            if not tmp_p:
                return "Python环境不存在"
            p_list = [tmp_p]
        elif add_type == "venv":
            tmp_p = VirtualEnvDetector.find_venv_python(path)
            if not tmp_p:
                return "Python环境不存在"
            else:
                p_list = [tmp_p]
                system_p = SystemPythonDetector.find_system_python(tmp_p.system_path)
                if system_p:
                    p_list.append(system_p)
        elif add_type == "conda":
            p_list = CondaDetector.find_conda_python(path)
            if not p_list:
                return "Python环境不存在"
        else:
            return "指定类型错误"

        _ep = EnvironmentReporter()
        _ep.update_report(*[p.to_dict() for p in p_list])
        return None

    def multi_remove_env(self, *more_path: str) -> List[Dict]:
        """批量移除Python虚拟环境（从管理列表中移除）

        :param path: 要移除的Python环境路径
        :param more_path: 其他要移除的路径（可变参数）
        :return: 错误信息或None（成功）
        可以移除的条件，
        1.是python_manager/pyporject_evn下的环境，
        2.非conda环境，
        3.无项目使用中，
        4.system环境,需要无以此环境为home的vnev环境
        """
        # 合并所有待删除路径并进行标准化处理
        paths_to_remove = {os.path.normpath(p) for p in more_path}

        to_remove = []
        saved = []

        for p in self.all_env:
            if p.bin_path in paths_to_remove:
                to_remove.append(p)
                paths_to_remove.remove(p.bin_path)
            else:
                saved.append(p)

        if paths_to_remove:
            msg = "Python环境不存在:%s"
            return [{"path": p, "status": False, "msg": msg % p} for p in paths_to_remove]

        bin_path2project = self.all_python_project_map()
        # 优先处理顺序 有项目使用的、conda、venv、system（非系统）、系统环境
        to_remove.sort(key=lambda x: (
            x.bin_path not in bin_path2project,
            ("conda", "venv", "system").index(x.env_type),
            any(x.bin_path.startswith(syp) for syp in _SYS_BIN_PATH)
        ))

        res_map = {p.bin_path: {
            "path": p.bin_path, "status": True, "msg": "Python环境删除成功"
        } for p in  to_remove}

        real_remove = []
        for p in to_remove:
            if p.env_type == "conda":
                res_map[p.bin_path].update(
                    status=False,
                    msg="Conda环境不支持操作，请在命令行中执行conda remove -n {}".format(p.venv_name)
                )
                saved.append(p)
                continue
            elif p.bin_path in bin_path2project:
                res_map[p.bin_path].update(
                    status=False,
                    msg="Python环境正在被项目【{}】使用，请先删除项目再操作".format(bin_path2project[p.bin_path][0])
                )
                saved.append(p)
                continue
            elif not p.bin_path.startswith(python_manager_path()) and \
                    not p.bin_path.startswith(pyenv_path()):
                res_map[p.bin_path].update(
                    status=False,
                    msg="非面板安装或创建的Python环境不支持操作，请手动处理"
                )
                saved.append(p)
                continue
            elif p.env_type == "system":
                for i in saved:
                    if i.system_path == p.bin_path:
                        res_map[p.bin_path].update(
                            status=False,
                            msg="该Python环境正在被虚拟环境【{}】使用中，请先删除虚拟环境再操作".format(
                                i.venv_name or i.ps or i.version
                        ))
                        saved.append(p)
                        break
                else:
                    real_remove.append(p)
            else:
                real_remove.append(p)

        if real_remove:
            for p in real_remove:
                msg = p.remove()
                if msg:
                    res_map[p.bin_path].update(
                        status=False,
                        msg=msg
                    )
                    # saved.append(p)  执行过删除的，即使删除失败，也要不保留记录
                else:
                    res_map[p.bin_path].update(
                        status=True,
                        msg="Python环境移除成功"
                    )

            saved_bin = {p.bin_path for p in saved}
            report = self.load_report()
            report["update_time"] = int(time.time())
            report["environments"] = [i for i in report["environments"] if i["bin_path"] in saved_bin]
            public.writeFile(self._REPORT_FILE, json.dumps(report, indent=4))
        return list(res_map.values())

    # 查询数据库中所有项目对环境的使用情况，返回映射关系
    def all_python_project_map(self):
        res_map = {}
        all_py_project = public.M("sites").where("project_type=?", ("Python",)).field('name,project_config').select()
        for project in all_py_project:
            project_config: dict = json.loads(project['project_config'])
            p = self.get_env_py_path(project_config.get('python_bin', project_config.get("vpath")))
            if p:
                res_map.setdefault(p.bin_path, []).append(project["name"])

        return res_map

    def set_python2env(self, path: str) -> Optional[str]:
        """设置python环境到命令行"""
        if path == "":
            pyenv = None
        else:
            pyenv = self.get_env_py_path(path)
            if not pyenv:
                return "Python环境不存在"
        PythonEnvironment.set_profile_env(pyenv)
        return None


    def get_default_python_env(self) -> Optional[PythonEnvironment]:
        """获取默认python环境"""
        p_bin = PythonEnvironment.profile_env_bin()
        if not p_bin:
            return None
        pyenv = self.get_env_py_path(p_bin)
        if pyenv:
            return pyenv
        return None

    def set_python_env_ps(self, path: str, ps: str) -> Optional[str]:
        """设置python环境"""
        pyenv = self.get_env_py_path(path)
        if not pyenv:
            return "Python环境不存在"
        pyenv.ps = ps
        EnvironmentReporter().update_report(pyenv.to_dict())
        return None


    @staticmethod
    def _is_valid_env_name(name: str) -> bool:
        """校验虚拟环境名称合法性"""
        # Linux文件系统命名规则
        forbidden_chars = {'/', '\\', ':', '*', '?', '"', '<', '>', '|', '\0'}
        max_length = 255  # 最大文件名长度

        # 基本规则检查
        if not name:
            return False
        if any(char in forbidden_chars for char in name):
            return False
        if len(name) > max_length:
            return False
        if name in ('.', '..'):  # 保留名称
            return False

        # 增强校验：推荐使用小写字母、数字、下划线和连字符
        # if not re.match(r'^[a-z0-9_.-]+$', name):
        #     return False

        return True

    def create_python_env(self,
                          venv_name: str,
                          src_python_bin: str,
                          ps:str,
                          call_log: Callable[[str], None] = None) -> Optional[str]:

        if call_log and callable(call_log):
            real_call = call_log
        else:
            real_call = lambda x: None

        if not self._is_valid_env_name(venv_name):
            err_msg3 = "虚拟环境名称不合法"
            real_call(err_msg3)
            return err_msg3

        err_msg = "源Python环境不存在"
        if not os.path.exists(src_python_bin):
            real_call(err_msg)
            return err_msg
        src_p = self.get_env_py_path(src_python_bin)
        if not src_p:
            real_call(err_msg)
            return err_msg

        if src_p.env_type != "system":
            err_msg2 = "需要使用系统Python环境来创建虚拟环境"
            real_call(err_msg2)
            return err_msg2

        venv_path = "/www/server/pyporject_evn/{}".format(venv_name)
        if call_log and callable(call_log):
            call_log("开始创建虚拟环境")
            return src_p.create_venv_sync(venv_path, ps, call_log)
        else:
            return src_p.create_venv(venv_path, ps)


if __name__ == '__main__':
    EnvironmentReporter().init_report()