#!/www/server/panel/pyenv/bin/python
import os
import re
import shutil
import sys
import time
import requests
import traceback
import tarfile
import subprocess
import argparse
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Tuple, List, Union, Dict, Iterable
from hashlib import sha256, sha1
from platform import system, machine
from xml.etree import cElementTree
from io import FileIO

__all__ = ['pygvm']


class _GvmSTD:
    out = sys.stdout
    err = sys.stderr


_gvm_std = _GvmSTD()


def get_arch() -> Tuple[Optional[str], Optional[str]]:
    _system_name = system()
    if _system_name != "Linux":
        return None, "目前只支持Linux系统使用该功能。"
    _arch = machine().lower()
    arch = None
    if _arch in ("x86_64", "amd64"):
        arch = "amd64"
    elif _arch in ("i386", "i486", "i586", "x86"):
        arch = "386"
    elif _arch in ("aarch64", "arm64"):
        arch = "arm64"
    if arch is None:
        return None, "未解析出当前处理器的适配的架构。"
    return arch, None


class GVMError(Exception):
    pass


template = """#pygvm
export GOROOT="/usr/local/btgo"
export PATH="/usr/local/btgo/bin:${PATH}"
"""


class _Mirror(object):
    """
    镜像源
    """
    _cloud = ""
    name = ""

    def test_speed(self, time_out: int) -> float:
        try:
            s_time = time.time()
            res = requests.get(self._cloud, timeout=time_out)
            if res.status_code != 200:
                return sys.float_info.max
            return time.time() - s_time
        except:
            return sys.float_info.max

    def get_versions_by_cloud(self, arch: str) -> Tuple[Union[List["GoVersion"], str], Optional[List["GoVersion"]]]:
        raise NotImplemented()

    def download_url(self, go_v: "GoVersion") -> str:
        raise NotImplemented()


class _StudyGolangMirror(_Mirror):
    _cloud = "https://studygolang.com/dl"
    name = "社区源"

    def get_versions_by_cloud(self, arch: str) -> Tuple[Union[List["GoVersion"], str], Optional[List["GoVersion"]]]:
        """
        获取云端支持的已归档版本和稳定版本
        """

        res = requests.get(self._cloud)
        if res.status_code != 200:
            return "请求云端数据错误！", None
        rep = r'(<\s?h3\s?id="stable"\s?>.*\n)(?P<stable>(.*\n)+)(\s*<\s?h3\s?id="unstable"\s?>)(.*\n)+' \
              r'(?P<history>(\s*<div\s?class="toggle(Visible)?"\s?id="archive"\s?>)(.*\n)+)((\s*</div>\s*\n){5}\s*<div)'
        res = re.search(rep, res.text)
        if not res:
            return "解析错误", None
        try:
            stable = cElementTree.fromstring("<body>" + res.group("stable") + "</body>")
            history = cElementTree.fromstring(res.group("history")).find('./div[2]')
            stable_go_versions = self._parser_xml(stable, arch)
            history_go_versions = self._parser_xml(history, arch)
            stable_go_versions.sort(key=lambda x: int(x.version.split(".")[1]), reverse=True)
            history_go_versions.sort(key=lambda x: int(x.version.split(".")[1]), reverse=True)
            return stable_go_versions, history_go_versions
        except:
            traceback.print_exc(file=_gvm_std.err)
            return "解析错误", None

    @staticmethod
    def _parser_xml(datas: cElementTree.Element, arch: str) -> List["GoVersion"]:
        res_list = []
        for data in datas.findall('./div'):
            v = data.attrib.get("id")
            need_file = "{}.linux-{}.tar.gz".format(v, arch)
            for i in data.iterfind('.//tr'):
                if i.attrib.get("class") == "first":
                    continue
                file_name = i.find("./td[1]/a").text
                checksum = i.find("./td[6]/tt").text
                if need_file == file_name:
                    go_v = GoVersion.new(v, checksum, file_name)
                    if go_v:
                        res_list.append(go_v)
        return res_list

    def download_url(self, go_v: "GoVersion") -> str:
        return "{}/golang/{}".format(self._cloud, go_v.file_name)


class _GoOfficialDeVMirror(_Mirror):
    _cloud = "https://go.dev/dl/"
    name = "go.dev源"

    def get_versions_by_cloud(self, arch: str) -> Tuple[Union[List["GoVersion"], str], Optional[List["GoVersion"]]]:
        """
        获取云端支持的已归档版本和稳定版本
        """
        res = requests.get(self._cloud)
        if res.status_code != 200:
            return "请求云端数据错误！", None

        rep_stable_versions = re.compile(r'<div\s+class="toggleVisible"\s+id="(.|\n)*?</table>(\s+</div>){3}')
        rep_history_versions = re.compile(r'<div\s+class="toggle"\s+id="(.|\n)*?</table>(\s+</div>){3}')
        stable_versions, history_versions = [], []
        for i in rep_stable_versions.finditer(res.text):
            g = self._parser_xml_node(i.group(), arch)
            if g is not None:
                stable_versions.append(g)

        for i in rep_history_versions.finditer(res.text):
            g = self._parser_xml_node(i.group(), arch)
            if g is not None:
                history_versions.append(g)
        if not stable_versions and history_versions:
            return "解析错误", None
        return stable_versions, history_versions

    @staticmethod
    def _parser_xml_node(data: str, arch: str) -> Optional["GoVersion"]:
        try:
            node = cElementTree.fromstring(data)
            v = node.attrib.get("id")
            if v.find("rc") != -1 or v.find("beta") != -1:
                return None
            need_file = "{}.linux-{}.tar.gz".format(v, arch)
            for i in node.iterfind('.//tr'):
                if i.attrib.get("class") == "first":
                    continue
                file_name = i.find("./td[1]/a").text
                checksum = i.find("./td[6]/tt").text
                if need_file == file_name:
                    go_v = GoVersion.new(v, checksum, file_name)
                    if go_v:
                        return go_v
        except:
            return None
        return None

    def download_url(self, go_v: "GoVersion") -> str:
        return "{}/{}".format(self._cloud, go_v.file_name)


class _GoOfficialCNMirror(_GoOfficialDeVMirror):
    _cloud = "https://golang.google.cn/dl/"
    name = "官方源"


class _UstcMirror(_Mirror):
    _cloud = "https://mirrors.ustc.edu.cn/golang/"
    name = "中科大源"

    def get_versions_by_cloud(self, arch: str) -> Tuple[Union[List["GoVersion"], str], Optional[List["GoVersion"]]]:
        """
        获取云端支持的已归档版本和稳定版本
        """
        res = requests.get(self._cloud)
        if res.status_code != 200:
            return "请求云端数据错误！", None

        rep_version = re.compile(r"<a.*(?P<f>(?P<v>go[\d.]+)\.linux-%s\.tar\.gz(\.sha256)?)" % arch)
        v_map = {}
        for i in rep_version.finditer(res.text):
            v = i.group("v")
            if v not in v_map:
                v_map[v] = [v, "", ""]
            f = i.group("f")
            if f.endswith(".sha256"):
                v_map[v][1] = f
            else:
                v_map[v][2] = f

        try:
            v_list = self._get_sha256(list(v_map.values()))
        except:
            v_list = []

        if not v_list:
            return "解析错误", None

        return [], v_list

    def _get_sha256(self, v_list: List[Iterable[str]]) -> List["GoVersion"]:
        p = ThreadPoolExecutor(10)
        t_list = []
        for idx, (v, s, f) in enumerate(v_list):
            if not s:
                continue
            t = p.submit(self._query_sha256, v_list, s, idx)
            t_list.append(t)

        for i in t_list:
            i.result()
        p.shutdown()

        use_list = []
        for v, s, f in v_list:
            g = GoVersion.new(v, s, f)
            if g:
                use_list.append(g)
        return use_list

    def _query_sha256(self, v_list, s, idx):
        try:
            res = requests.get("{}/{}".format(self._cloud, s))
            if res.status_code == 200:
                v_list[idx][1] = res.text
        except:
            v_list[idx][1] = ""

    def download_url(self, go_v: "GoVersion") -> str:
        return "{}/{}".format(self._cloud, go_v.file_name)


def get_cloud() -> _Mirror:
    _m_list = [
        _StudyGolangMirror(),
        _GoOfficialCNMirror(),
        _GoOfficialDeVMirror(),  # 不稳定 禁用
    ]

    v4_file = '/www/server/panel/data/v4.pl'
    if os.path.exists(v4_file):
        try:
            with open(v4_file, 'rt', encoding='utf-8') as fp:
                if fp.read().strip() == "-4":
                    _m_list = _m_list[1:]
        except:
            pass

    def test_with_time_out(time_out: int) -> _Mirror:
        p = ThreadPoolExecutor(len(_m_list))
        res_task = []
        for m in _m_list:
            res_task.append(p.submit(m.test_speed, time_out))

        time_list = []
        for idx, t in enumerate(res_task):
            time_list.append((t.result(timeout=None), idx))
        time_list.sort(key=lambda x: x[0])
        return _m_list[time_list[0][1]]

    try:
        return test_with_time_out(10)
    except:
        try:
            return test_with_time_out(60)
        except:
            pass

    # 都无法获取时，使用 中科大 的源
    return _UstcMirror()


class GoVersion:
    __slots__ = ("version", "checksum", "file_name", "_cloud", "bt_gvm_path")

    def __init__(self, v: str, checksum: str, file_name: str):
        self.version = v
        self.checksum = checksum
        self.file_name = file_name
        self._cloud: Optional[_Mirror] = None
        self.bt_gvm_path = "/usr/local/btgojdk"

    def set_cloud(self, c: _Mirror):
        self._cloud = c
        print("正在使用【{}】源进行下载".format(c.name))

    def check(self, file) -> bool:
        """calculate file sha256 """
        print("[2/4] 校验文件hash值.....", file=_gvm_std.out, flush=True)
        sha_obj = sha256() if len(self.checksum) == 64 else sha1()
        with open(file, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha_obj.update(chunk)
        hash_value = sha_obj.hexdigest()
        print("计算值：{}".format(hash_value), file=_gvm_std.out, flush=True)
        print("验证值：{}".format(self.checksum), file=_gvm_std.out, flush=True)
        return hash_value == self.checksum

    @classmethod
    def new(cls, v: str, checksum: str, file_name: str) -> Optional["GoVersion"]:
        v_rep = r"(?P<target>go1\.\d{1,2}(\.\d{1,2})?)"
        v_res = re.search(v_rep, v)
        v = None
        if v_res:
            v = v_res.group("target")

        checksum_rep = r"(?P<target>([0-9a-f]{64})|([0-9a-f]{40}))"
        checksum_res = re.search(checksum_rep, checksum)
        checksum = None
        if checksum_res:
            checksum = checksum_res.group("target")
        if not v or not checksum_res:
            return None
        return cls(v, checksum, file_name)

    def __str__(self) -> str:
        return "[v:{}, checksum:{}]".format(self.version, self.checksum)

    def serialize(self) -> str:
        return "({}:{}:{})".format(self.version, self.checksum, self.file_name)

    def show(self) -> str:
        return self.version

    @classmethod
    def deserialize(cls, data: str) -> Optional["GoVersion"]:
        if data[0] == "(" and data[-1] == ")":
            data = data[1:-1]
        return cls.new(*data.split(":")[:3])

    def _download(self) -> bool:
        cache_dir = os.path.join(self.bt_gvm_path, "cached")
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        dst = os.path.join(cache_dir, self.file_name)
        if os.path.exists(dst):
            print("[1/4] 使用缓存的sdk文件......", file=_gvm_std.out, flush=True)
            return self.check(dst)

        print("[1/4] 下载sdk文件......", file=_gvm_std.out, flush=True)
        response = requests.get(self._cloud.download_url(self), stream=True)
        total_size = int(response.headers.get('content-length', 0))
        print("需要下载的文件大小: %.2fM" % (total_size / (1024 * 1024)), file=_gvm_std.out, flush=True)
        block_size = 1024 * 1024
        downloaded_size = 0
        with open(dst, 'wb') as f:
            for data in response.iter_content(block_size):
                f.write(data)
                downloaded_size += len(data)
                progress = (downloaded_size / total_size) * 100
                print(f"Downloading....\t %.2f%% completed" % progress,
                      end='\r', flush=True, file=_gvm_std.out)
        print('Download complete', file=_gvm_std.out, flush=True)
        return self.check(dst)

    def _install(self) -> bool:
        print("[3/4] 解压安装.....", file=_gvm_std.out, flush=True)
        tar_filename = os.path.join(self.bt_gvm_path, "cached", self.file_name)
        target_directory = self.bt_gvm_path
        try:
            with tarfile.open(tar_filename, 'r:gz') as tar:
                tar.extractall(path=target_directory)
        except:
            return False
        src = os.path.join(self.bt_gvm_path, "go")
        if not os.path.isdir(src):
            return False
        os.rename(src, os.path.join(self.bt_gvm_path, self.version))
        return True

    def install(self) -> Tuple[bool, str]:
        if not os.path.exists(self.bt_gvm_path):
            os.makedirs(self.bt_gvm_path)
        print("开始安装......", file=_gvm_std.out, flush=True)
        dst = os.path.join(self.bt_gvm_path, self.version)
        if os.path.isdir(dst):
            return True, "已安装"

        # 下载文件
        if not self._download():
            return False, "文件下载并验证失败！"
        # 安装go
        if not self._install():
            return False, "解压安装失败！"

        print("[4/4] 使用{}.....".format(self.version), file=_gvm_std.out, flush=True)
        flag, err = self.use(self.bt_gvm_path, self.version)
        if not flag:
            return False, err
        print("安装完成!", file=_gvm_std.out, flush=True)
        print("若找不到go指令,可以尝试重新打开终端", file=_gvm_std.out, flush=True)
        return True, ""

    @classmethod
    def use(cls, bt_gvm_path, version) -> Tuple[bool, str]:
        # 建立软链接
        src = os.path.join(bt_gvm_path, version)
        if not os.path.isdir(src):
            return False, "{}文件丢失。".format(version)
        dst = "/usr/local/btgo"
        if os.path.islink(dst):
            os.unlink(dst)
        os.symlink(src, dst)
        cls.add_to_path()
        time.sleep(0.1)
        out, err = cls.test()
        if version in out:
            return True, ""
        else:
            return False, err

    @staticmethod
    def test() -> Tuple[str, str]:
        # 执行命令并获取输出
        os.environ["PATH"] = "/usr/local/btgo/bin:" + os.environ["PATH"]
        p = subprocess.Popen("go version", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, env=os.environ)
        output, err = p.communicate()
        return output.decode(), err.decode()

    @staticmethod
    def add_to_path():
        profile = "/etc/profile"
        with open(profile, "r") as f:
            profile_data = f.read()
        if profile_data.find(template) != -1:
            return
        with open(profile, "a") as f:
            f.write("\n" + template)
        os.system("source {}".format(profile))

    @staticmethod
    def parse_version(data: str) -> Tuple[bool, str]:
        v_rep = r"(?P<target>1\.\d{1,2}(\.\d{1,2})?)"
        v_res = re.search(v_rep, data)
        v = None
        if v_res:
            v = v_res.group("target")
            return True, "go" + v
        else:
            return False, ""


class GVM(object):
    stable_versions: Optional[List[GoVersion]] = None
    history_versions: Optional[List[GoVersion]] = None
    arch = ""
    use_shell = False
    bt_gvm_path = "/usr/local/btgojdk"
    now_version = None

    def __init__(self):
        self.get_now_version()
        if not os.path.exists(self.bt_gvm_path):
            os.makedirs(self.bt_gvm_path)
        self._cloud = None

    @staticmethod
    def check_use():
        res = os.popen("lsattr /etc/profile")
        return res.read().find("--i--") == -1

    @property
    def cloud(self):
        if not isinstance(self._cloud, _Mirror):
            self._cloud = get_cloud()
        return self._cloud

    def get_now_version(self) -> None:
        now_version = "/usr/local/btgo"
        if os.path.islink(now_version):
            now_version = os.path.basename(os.readlink(now_version))
        else:
            now_version = None
        self.now_version = now_version

    def __new__(cls, *args, **kwargs) -> Union["GVM", str]:
        arch, errmsg = get_arch()
        if errmsg:
            return errmsg
        _gvm = super().__new__(cls, *args, **kwargs)
        _gvm.arch = arch
        return _gvm

    # 获取版本
    def get_go_version(self):
        self.stable_versions, self.history_versions = self._get_versions_by_local()
        if not self.history_versions:
            if self.use_shell:
                print("未找到本地记录文件，将向云端请求GO版本数据，这可能需要一段时间，请稍等", file=_gvm_std.out)
            self.stable_versions, self.history_versions = self._get_versions_by_cloud()
            # 缓存数据到本地
            if isinstance(self.stable_versions, list):
                self._save_cached(self.stable_versions, self.history_versions)
        if not self.history_versions and isinstance(self.stable_versions, str):
            raise GVMError("网络错误：" + self.stable_versions)
        return self.stable_versions, self.history_versions

    def _get_versions_by_local(self) -> [Tuple[Optional[List[GoVersion]], Optional[List[GoVersion]]]]:
        """
        获取本地已归档版本和稳定版本的缓存数据
        """
        local_path = "/www/server/panel/data/pygvm"
        if not os.path.exists(local_path):
            os.makedirs(local_path)
            return None, None
        stable_file = os.path.join(local_path, "stable_versions.txt")
        history_file = os.path.join(local_path, "history_versions.txt")
        if not os.path.isfile(stable_file) or not os.path.isfile(history_file):
            return None, None
        with open(stable_file, "r") as f:
            _arch = f.readline().strip()
            if _arch != self.arch:
                return None, None
            stable_versions = [GoVersion.deserialize(line.strip()) for line in f.readlines()]
        with open(history_file, "r") as f:
            _arch = f.readline().strip()
            if _arch != self.arch:
                return None, None
            history_versions = [GoVersion.deserialize(line.strip()) for line in f.readlines()]

        return stable_versions, history_versions

    def _get_versions_by_cloud(self) -> Tuple[Union[List[GoVersion], str], Optional[List[GoVersion]]]:
        """
        获取云端支持的已归档版本和稳定版本
        """
        return self.cloud.get_versions_by_cloud(self.arch)

    def _save_cached(self, stable_go_versions: List[GoVersion], history_go_versions: List[GoVersion]) -> None:
        local_path = "/www/server/panel/data/pygvm"
        if not os.path.exists(local_path):
            os.makedirs(local_path)
        with open(os.path.join(local_path, "stable_versions.txt"), "w") as f:
            f.write(self.arch + "\n")
            for go_v in stable_go_versions:
                f.write(go_v.serialize() + "\n")
        with open(os.path.join(local_path, "history_versions.txt"), "w") as f:
            f.write(self.arch + "\n")
            for go_v in history_go_versions:
                f.write(go_v.serialize() + "\n")

    @staticmethod
    def del_cached():
        local_path = "/www/server/panel/data/pygvm"
        stable_file = os.path.join(local_path, "stable_versions.txt")
        history_file = os.path.join(local_path, "history_versions.txt")
        if os.path.isfile(stable_file):
            os.remove(stable_file)
        if os.path.isfile(history_file):
            os.remove(history_file)

    def api_ls(self) -> List[str]:
        return [i.strip() for i in os.listdir(self.bt_gvm_path) if i.startswith("go1")]

    def cmd_ls(self) -> None:
        versions = [i.strip() for i in os.listdir(self.bt_gvm_path) if i.startswith("go1")]
        if not versions:
            print("未安装任何一个版本的GO语言SDK")
            return
        print("version: ")
        for i in versions:
            if i == self.now_version:
                i += "    <- Now use this version"
            print("    " + i)

    def api_ls_remote(self, is_all: bool) -> Tuple[Optional[List[GoVersion]], Optional[List[GoVersion]], Optional[str]]:
        try:
            self.get_go_version()
        except GVMError as e:
            return [], [], str(e)
        if is_all:
            self.stable_versions.sort(key=lambda x: int(x.version.split(".")[1]), reverse=True)
            self.history_versions.sort(key=lambda x: int(x.version.split(".")[1]), reverse=True)
            return self.stable_versions, self.history_versions, None
        stable_v = [".".join(i.version.split(".")[:2]) for i in self.stable_versions]
        res_history = {}
        for i in self.history_versions:
            parse_list = i.version.split(".")
            v = ".".join(parse_list[:2])
            if len(parse_list) > 2:
                # 三级版本号
                three_idx = int(parse_list[2])
            else:
                three_idx = 0
            # 在稳定版中已存在的就不在展示
            if v in stable_v:
                continue
            if v in res_history:
                if three_idx > res_history[v][0]:
                    res_history[v] = [three_idx, i]
            else:
                res_history[v] = [three_idx, i]
        res_h = []
        for i in res_history.values():
            res_h.append(i[1])
        res_h.sort(key=lambda x: int(x.version.split(".")[1]), reverse=True)
        return self.stable_versions, res_h, None

    def cmd_ls_remote(self, is_all: bool) -> None:
        stable, history, err = self.api_ls_remote(is_all)
        installed = self.api_ls()
        if err:
            print("获取版本信息时出错了", file=sys.stderr)
            print(err, file=sys.stderr)
        print("Stable Version:")
        for i in stable:
            if i.version in installed:
                i.version += "    <- installed"
            print("    " + i.version)
        print("History Version:")
        for i in history:
            if i.version in installed:
                i.version += "    <- installed"
            print("    " + i.version)

    def _get_version(self, version) -> Union[GoVersion, str]:
        stable, history, err = self.api_ls_remote(True)
        if err:
            if self.use_shell:
                print("获取版本信息时出错了", file=_gvm_std.err)
                print(err, file=_gvm_std.err)

            return err
        for i in stable:
            if i.version == version:
                return i
        for i in history:
            if i.version == version:
                return i
        if self.use_shell:
            print("未找到对应版本", file=_gvm_std.err)
        return "未找到对应版本"

    def api_use(self, version) -> Tuple[bool, str]:
        versions = self.api_ls()
        if version not in versions:
            return False, "未找到对应版本"
        res = GoVersion.use(self.bt_gvm_path, version)
        self.get_now_version()
        return res

    def cmd_use(self, version) -> None:
        flag, err = self.api_use(version)
        if flag:
            print("已切换到:{}".format(version))
            print("若找不到go指令,可以尝试重新打开终端")
        else:
            print(err, file=sys.stderr)

    def api_install(self, version) -> Tuple[bool, str]:
        go_v = self._get_version(version)
        if isinstance(go_v, str):
            return False, go_v
        go_v.set_cloud(self.cloud)
        return go_v.install()

    def cmd_install(self, version) -> None:
        go_v = self._get_version(version)
        go_v.set_cloud(self.cloud)
        if isinstance(go_v, str):
            pass
        _, err = go_v.install()
        if err:
            print(err, file=sys.stderr)

    def api_uninstall(self, version: str) -> Tuple[bool, str]:
        versions = self.api_ls()
        if version not in versions:
            return False, "未找到对应版本"
        next_version = None
        for i in versions:
            if i != version:
                next_version = i
                break
        if next_version is not None and version == self.now_version:
            GoVersion.use(self.bt_gvm_path, next_version)
        target_dir = os.path.join(self.bt_gvm_path, version)
        if os.path.exists:
            shutil.rmtree(target_dir, ignore_errors=True)
        return True, ""

    def cmd_uninstall(self, version: str) -> None:
        flag, err = self.api_uninstall(version)
        if flag:
            print("已成功卸载:{}".format(version))
        else:
            print(err, file=sys.stderr)

    def cmd_clean_cache(self) -> None:
        local_path = "/www/server/panel/data/pygvm"
        for i in ("stable_versions.txt", "history_versions.txt"):
            if os.path.isfile(local_path + "/" + i):
                os.remove(local_path + "/" + i)
        cache_dir = os.path.join(self.bt_gvm_path, "cached")
        if os.path.isdir(cache_dir):
            shutil.rmtree(cache_dir)
        return

    @staticmethod
    def set_goproxy(proxy: str) -> bool:
        if os.path.isfile("/usr/local/btgo/bin/go"):
            try:
                subprocess.check_output([
                    "/usr/local/btgo/bin/go", "env", "-w", "GOPROXY=" + proxy, "GO111MODULE=on"
                ])
                return True
            except Exception:
                pass
        return False

    @staticmethod
    def get_goproxy() -> str:
        if os.path.isfile("/usr/local/btgo/bin/go"):
            try:
                out = subprocess.check_output(["/usr/local/btgo/bin/go", "env", "GOPROXY"])
                if out:
                    return out.decode("utf-8").strip()
            except:
                pass
        return ""

    @staticmethod
    def set_std(out: FileIO, err: FileIO) -> None:
        _gvm_std.out = out
        _gvm_std.err = err


pygvm = GVM()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='gvm go语言sdk管理器')
    # 添加子命令
    subparsers = parser.add_subparsers(title='operation', dest='command')
    # 添加ls子命令
    subparsers.add_parser('ls', help='展示已安装的Go语言SDK版本')
    # 添加ls子命令
    subparsers.add_parser('clean-cache', help='清除缓存')
    # 添加ls_r子命令
    parser_ls_r = subparsers.add_parser('ls-remote', help='展示可安装Go语言SDK的版本，默认只展示每个版本中较新的版本')
    parser_ls_r.add_argument('-a', action='store_true', help='展示可以安装的所有Go语言SDK版本')
    # 添加use子命令
    parser_use = subparsers.add_parser('use', help='使用指定版本')
    parser_use.add_argument('use_param', type=str, help='完整的版本号')
    # 添加install子命令
    parser_install = subparsers.add_parser('install', help='安装指定版本')
    parser_install.add_argument('install_param', type=str, help='完整的版本号')
    # 添加uninstall子命令
    parser_uninstall = subparsers.add_parser('uninstall', help='卸载并删除指定版本')
    parser_uninstall.add_argument('uninstall_param', type=str, help='完整的版本号')

    input_args = parser.parse_args()
    gvm = GVM()
    if isinstance(gvm, str):
        print(gvm, file=sys.stderr)
        exit(1)
    gvm.use_shell = True
    if input_args.command == 'ls':
        gvm.cmd_ls()
    elif input_args.command == "ls-remote":
        _is_all = True if input_args.a else False
        gvm.cmd_ls_remote(_is_all)
    elif input_args.command == "use":
        _flag, _v = GoVersion.parse_version(input_args.use_param)
        if _flag:
            gvm.cmd_use(_v)
        else:
            print("版本参数错误，应该是1.xx.xx的结构", file=sys.stderr)
    elif input_args.command == "install":
        _flag, _v = GoVersion.parse_version(input_args.install_param)
        if _flag:
            gvm.cmd_install(_v)
        else:
            print("版本参数错误，应该是1.xx.xx的结构", file=sys.stderr)
    elif input_args.command == "uninstall":
        _flag, _v = GoVersion.parse_version(input_args.uninstall_param)
        if _flag:
            gvm.cmd_uninstall(_v)
        else:
            print("版本参数错误，应该是1.xx.xx的结构", file=sys.stderr)
    elif input_args.command == "clean-cache":
        gvm.cmd_clean_cache()
    else:
        print("使用pygvm -h 查看操作指令", file=sys.stderr)
