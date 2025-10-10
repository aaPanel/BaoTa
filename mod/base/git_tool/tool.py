import json
import os
import re
import shutil
import time

from .install import installed, install_git, version_1_5_3
from .util import read_file, write_file, ExecShell, set_ownership
from typing import Optional, Dict, Union, List
from urllib3.util import parse_url, Url
from mod.base import json_response

GIT_TMP_PATH = "/www/server/git_tmp"


class GitTool:

    def __init__(self, project_path: str, git_url: str, user_config: Optional[dict] = None, git_id: str = ""):
        self.git_url = git_url
        self.get_id = git_id
        self.project_path = project_path
        if self.project_path[-1] == '/':
            self.project_path = self.project_path[:-1]
        if not os.path.isdir(GIT_TMP_PATH):
            os.makedirs(GIT_TMP_PATH)

        self._tmp_path: Optional[str] = None
        self._askpass_path: Optional[str] = None

        self.user_config = user_config
        _conf = self.get_user_config_by_project_path()
        if _conf and not self.user_config:
            self.user_config = _conf

        self._init_tmp_path = False

    @property
    def tmp_path(self) -> Optional[str]:
        if self._tmp_path is not None:
            return self._tmp_path
        if not os.path.isdir(self.project_path):
            return None
        ino = os.stat(self.project_path).st_ino
        self._tmp_path = "{}/{}".format(GIT_TMP_PATH, str(ino))
        self._askpass_path = "{}/help_{}.sh".format(GIT_TMP_PATH, str(ino))
        return self._tmp_path

    def get_user_config_by_project_path(self) -> Optional[dict]:
        if os.path.isfile(self.project_path + "/.git/config"):
            git_config = read_file(self.project_path + "/.git/config")
            if isinstance(git_config, str):
                return self._read_user_conf_by_config(git_config)
        return None

    @property
    def askpass_path(self) -> Optional[str]:
        if self._askpass_path is not None:
            return self._askpass_path
        if not os.path.isdir(self.project_path):
            return None
        ino = os.stat(self.project_path).st_ino
        self._tmp_path = "{}/{}".format(GIT_TMP_PATH, str(ino))
        self._askpass_path = "{}/help_{}.sh".format(GIT_TMP_PATH, str(ino))
        return self._askpass_path

    def _setup_tmp_path(self) -> Optional[str]:
        if not os.path.isdir(self.project_path):
            return "目标目录：【{}】不存在，无法进行git操作".format(self.project_path)

        if not os.path.exists(self.tmp_path):
            os.makedirs(self.tmp_path)
            self._init_tmp_path = True
        else:
            if not self._init_tmp_path:
                shutil.rmtree(self.tmp_path)
                os.makedirs(self.tmp_path)
                write_file(self.askpass_path, "")
                ExecShell("chmod +x " + self.askpass_path)

        if os.path.isdir(self.tmp_path + "/.git"):
            return None
        sh_str = """cd {tmp_path}
{git_bin} init .
{git_bin} remote add origin {git_url}
""".format(tmp_path=self.tmp_path, git_bin=self.git_bin(), git_url=self.git_url)

        ExecShell(sh_str)
        if not os.path.isfile(self.tmp_path + "/.git/config"):
            return "git 初始化失败"

        git_conf = read_file(self.tmp_path + "/.git/config")
        if not (isinstance(git_conf, str) and git_conf.find("origin") != -1 and git_conf.find(self.git_url) != -1):
            return "git 设置远程路由失败"

        if self.git_url.find("ssh://") != -1:  # ssh的情况下不做处理
            return

        if isinstance(self.user_config, dict):
            sh_str_list = ["cd {}".format(self.tmp_path)]
            config_sh = self.git_bin() + " config user.{} {}"
            for k, v in self.user_config.items():
                if isinstance(k, str) and isinstance(v, str) and k.strip() and v.strip():
                    sh_str_list.append(config_sh.format(k, v))
            ExecShell("\n".join(sh_str_list))
            askpass_str = """#!/bin/sh
case "$1" in
    Username*) exec echo "{}" ;;
    Password*) exec echo "{}" ;;
esac
""".format(self.user_config.get('name', "--"), self.user_config.get('password', "--"))
            write_file(self.askpass_path, askpass_str)

    def remote_branch(self) -> Union[str, List[str]]:
        error = self._setup_tmp_path()
        if error:
            return error
        out, err = ExecShell("cd {} && export GIT_ASKPASS='{}' && git ls-remote origin".format(
            self.tmp_path, self.askpass_path))
        rep_branch = re.compile(r"refs/heads/(?P<b>[^\n]*)\n")
        branch_list = []
        for tmp_res in rep_branch.finditer(out):
            branch_list.append(tmp_res.group("b"))

        if not branch_list:
            return err
        return branch_list

    @staticmethod
    def _read_user_conf_by_config(git_config_data: str) -> Optional[dict]:
        rep_user = re.compile(r"\[user][^\n]*\n(?P<target>(\s*\w+\s*=\s*[^\n]*\n)*(\s*\w+\s*=\s*[^\n]*)?)(\s*\[)?")
        res = rep_user.search(git_config_data)
        if not res:
            return None
        res_data = dict()
        k_v_str = res.group("target")
        for line in k_v_str.split("\n"):
            if not line.strip():
                continue
            k, v = line.split("=", 1)
            res_data[k.strip()] = v.strip()
        return res_data

    @classmethod
    def global_user_conf(cls) -> dict:
        res_dict = {
            "name": None,
            "password": None,
            "email": None,
        }
        global_file = "/root/.gitconfig"
        if not os.path.isfile(global_file):
            return res_dict
        data = read_file(global_file)
        if not isinstance(data, str):
            return res_dict
        res_data = cls._read_user_conf_by_config(data)
        res_dict.update(res_data)
        return res_dict

    @classmethod
    def set_global_user_conf(cls, data) -> None:
        sh_str = cls.git_bin() + " config --global user.{} {}"
        for k, v in data.items():
            if isinstance(k, str) and isinstance(v, str) and k.strip() and v.strip():
                ExecShell(sh_str.format(k, v))

    @classmethod
    def ssh_pub_key(cls):
        key_files = ('id_ed25519', 'id_rsa', 'id_ecdsa', 'id_rsa_bt')
        for key_file in key_files:
            key_file = "/root/.ssh/{}".format(key_file)
            pub_file = "/root/.ssh/{}.pub".format(key_file)
            if os.path.isfile(pub_file) and os.path.isfile(key_file):
                data = read_file(pub_file)
                if isinstance(data, str):
                    return data
        return cls._create_ssh_key()

    @staticmethod
    def _create_ssh_key() -> str:
        key_type = "ed25519"
        ExecShell("ssh-keygen -t {s_type} -P '' -f /root/.ssh/id_{s_type} |echo y".format(s_type=key_type))
        authorized_keys = '/root/.ssh/authorized_keys'
        pub_file = "/root/.ssh/id_{s_type}.pub".format(s_type=key_type)
        ExecShell('cat %s >> %s && chmod 600 %s' % (pub_file, authorized_keys, authorized_keys))
        key_type_file = '/www/server/panel/data/ssh_key_type.pl'
        write_file(key_type_file, key_type)
        return read_file(pub_file)

    @staticmethod
    def git_bin() -> str:
        if not installed():
            if not install_git():
                raise ValueError("没有git工具，且安装失败，无法使用此功能")
        default = "/usr/bin/git"
        git_path = shutil.which("git")
        if git_path is None:
            return default
        return git_path

    def pull(self, branch, set_own: Optional[str] = None) -> Optional[str]:
        if self.git_url.startswith("https://") or self.git_url.startswith("http://"):
            res = parse_url(self.git_url)
            if isinstance(res, Url) and not res.auth:
                if self.user_config and "name" in self.user_config and "password" in self.user_config:
                    res = res._replace(auth="{}:{}".format(self.user_config["name"], self.user_config["password"]))
                    self.git_url = res.url
        git_name = self.git_name()
        if git_name is None:
            git_name = 'None'
        if os.path.isdir(self.tmp_path + "/" + git_name):
            shutil.rmtree(self.tmp_path + "/" + git_name)

        log_file = "/tmp/git_{}_log.log".format(self.get_id)

        shell_command_str = "cd {0} && {1} clone --progress -b {2} {3} &>> {4}".format(
            self.tmp_path, self.git_bin(), branch, self.git_url, log_file
        )
        if not os.path.exists(self.tmp_path): os.makedirs(self.tmp_path)
        ExecShell(shell_command_str)
        if not os.path.isdir(self.tmp_path + "/" + git_name):
            return "拉取错误"

        ExecShell("\cp -rf {}/{}/* {}/".format(self.tmp_path, git_name, self.project_path))
        if isinstance(set_own, str):
            set_ownership(self.project_path, set_own)

        if os.path.isdir(self.tmp_path + "/" + git_name):
            shutil.rmtree(self.tmp_path + "/" + git_name)

    def git_name(self) -> Optional[str]:
        if isinstance(self.git_url, str):
            name = self.git_url.rsplit("/", 1)[1]
            if name.endswith(".git"):
                name = name[:-4]
            return name
        return None

    @classmethod
    def new_id(cls) -> str:
        from uuid import uuid4
        return uuid4().hex[::2]


class RealGitMager:
    _git_config_file = "/www/server/panel/data/site_git_config.json"

    def __init__(self):
        self._config: Optional[Dict[str, List[Dict[str, Union[int, str, dict]]]]] = None
        # c = {
        #     "site_name": [{
        #         "id": "",
        #         "site_name": "aaaa",
        #         "url": "http://git.bt.cn/cjxin/panel-plugin.git",  # ssh://git@git.bt.cn/cjxin/panel-plugin.git
        #         "path_ino": 4564524,
        #         "git_path": "/www/wwwroot/site",
        #         "config": {
        #             "name": "",
        #             "password": "",
        #             "email": "",
        #         },
        #     }
        #     ]
        # }

    @property
    def configure(self) -> Dict[str, List[Dict[str, Union[int, str, dict]]]]:
        if self._config is None:
            try:
                res = read_file(self._git_config_file)
                if res is None:
                    data = {}
                else:
                    data = json.loads(res)
            except (json.JSONDecoder, TypeError, ValueError):
                data = {}

            self._config = data
        return self._config

    def save_configure(self):
        if self._config:
            write_file(self._git_config_file, json.dumps(self._config))

    def add_git(self, git_url: str, site_name: str, git_path: str, user_config: Optional[dict]) -> Union[str, list]:
        url = parse_url(git_url)
        if not (isinstance(url, Url) and url.scheme and url.host and url.path):
            return "url格式错误"

        if user_config and not (isinstance(user_config, dict) and "name" in user_config and "password" in user_config):
            return "用户信息输入错误"

        if not os.path.exists(git_path):
            return "git目标目录不存在"
        else:
            path_ino = os.stat(git_path).st_ino

        if site_name not in self.configure:
            self.configure[site_name] = []

        for c in self.configure[site_name]:
            if c["path_ino"] == path_ino or git_path == c["git_path"]:
                return "该路径已存在，请不要重复添加"

        try:
            GitTool.git_bin()
        except ValueError as e:
            return str(e)

        git_id = GitTool.new_id()
        git = GitTool(project_path=git_path, git_url=git_url, user_config=user_config, git_id=git_id)
        res = git.remote_branch()
        if isinstance(res, str):
            return res

        self.configure[site_name].append(
            {
                "id": git_id,
                "site_name": site_name,
                "url": git_url,
                "path_ino": path_ino,
                "git_path": git_path,
                "remote_branch": res,
                "remote_branch_time": int(time.time()),
                "config": user_config,
            }
        )
        self.save_configure()
        return res

    def modify_git(
            self,
            git_id: str,
            site_name: str,
            git_url: Optional[str],
            git_path: Optional[str],
            user_config: Optional[dict]
    ) -> Optional[str]:
        target = None
        for i in self.configure.get(site_name, []):
            if i["id"] == git_id:
                target = i
                break

        if target is None:
            return '指定的git配置不存在'
        if git_url:
            url = parse_url(git_url)
            if not (isinstance(url, Url) and url.scheme and url.host and url.path):
                return "url格式错误"
            target["url"] = git_url

        if git_path:
            if not os.path.exists(git_path):
                return "git目标目录不存在"
            else:
                path_ino = os.stat(git_path).st_ino
            target["path_ino"] = path_ino
            target["git_path"] = git_path

        if user_config:
            if not (isinstance(user_config, dict) and "name" in user_config and "password" in user_config):
                return "用户信息输入错误"
            target["config"] = user_config

        git = GitTool(project_path=target['git_path'],
                      git_url=target['url'],
                      user_config=target['config'],
                      git_id=target['id'])
        res = git.remote_branch()
        if isinstance(res, str):
            return res

        self.save_configure()
        return None

    def remove_git(self, git_id: str, site_name: str) -> Optional[str]:
        target = None
        for i in self.configure.get(site_name, []):
            if i["id"] == git_id:
                target = i
                break

        if target is None:
            return '指定的git配置不存在'

        self.configure[site_name].remove(target)
        self.save_configure()

    def site_git_configure(self, site_name, refresh: bool = False) -> List[dict]:
        if site_name not in self.configure:
            return []
        res_list = []
        for i in self.configure[site_name]:
            if time.time() - i.get("remote_branch_time", 0) > 60 * 60 or refresh:
                g = GitTool(project_path=i['git_path'], git_url=i['url'], user_config=i['config'], git_id=i['id'])
                res = g.remote_branch()
                if isinstance(res, str):
                    i.update(remote_branch_error=res, remote_branch=[], remote_branch_time=int(time.time()))
                else:
                    i.update(remote_branch=res, remote_branch_time=int(time.time()))
            res_list.append(i)

        return res_list

    @staticmethod
    def set_global_user(name: Optional[str], password: Optional[str], email: Optional[str] = None) -> None:
        data = {}
        if name:
            data['name'] = name
        if password:
            data['password'] = password
        if email:
            data['email'] = email
        GitTool.set_global_user_conf(data)

    def git_pull(self, git_id: str, site_name: str, branch: str) -> Optional[str]:
        target = None
        for i in self.configure.get(site_name, []):
            if i["id"] == git_id:
                target = i
                break

        if target is None:
            return '指定的git配置不存在'

        g = GitTool(
            project_path=target['git_path'],
            git_url=target['url'],
            user_config=target['config'],
            git_id=target["id"])
        return g.pull(branch)


class GitMager:
    # 添加git信息
    @staticmethod
    def add_git(get):
        user_config = None
        try:
            git_url = get.url.strip()
            site_name = get.site_name.strip()
            git_path = get.git_path.strip()
            if hasattr(get, "config") and get.config.strip():
                user_config = json.loads(get.config.strip())
        except (json.JSONDecoder, AttributeError, TypeError):
            return json_response(status=False, msg="参数错误")
        res = RealGitMager().add_git(git_url, site_name, git_path, user_config)
        if isinstance(res, str):
            return json_response(status=False, msg=res)
        return json_response(status=True, data=res)

    # 修改git信息
    @staticmethod
    def modify_git(get):
        git_url = None
        git_path = None
        user_config = None
        try:
            git_id = get.git_id.strip()
            site_name = get.site_name.strip()
            if "url" in get:
                git_url = get.url.strip()
            if 'git_path' in get:
                git_path = get.git_path.strip()
            if hasattr(get, "user_config") and get.user_config.strip():
                user_config = json.loads(get.user_config.strip())
        except (json.JSONDecoder, AttributeError, TypeError):
            return json_response(status=False, msg="参数错误")
        res = RealGitMager().modify_git(git_id, site_name, git_url, git_path, user_config)
        if isinstance(res, str):
            return json_response(status=False, msg=res)
        return json_response(status=True, data=res)

    # 移除git信息
    @staticmethod
    def remove_git(get):
        try:
            git_id = get.git_id.strip()
            site_name = get.site_name.strip()
        except (json.JSONDecoder, AttributeError, TypeError):
            return json_response(status=False, msg="参数错误")
        res = RealGitMager().remove_git(git_id, site_name)
        if isinstance(res, str):
            return json_response(status=False, msg=res)
        return json_response(status=True, data=res)

    @staticmethod
    def site_git_configure(get):
        if not version_1_5_3():
            return json_response(status=False, msg="git 版本低于1.5.3无法使用")
        refresh = ''
        try:
            site_name = get.site_name.strip()
            if "refresh" in get:
                refresh = get.refresh.strip()
        except (AttributeError, TypeError):
            return json_response(status=False, msg="参数错误")
        if refresh in ("true", "1"):
            refresh = True
        else:
            refresh = False
        res = RealGitMager().site_git_configure(site_name, refresh=refresh)
        if isinstance(res, str):
            return json_response(status=False, msg=res)
        return json_response(status=True, data=res)

    @staticmethod
    def set_global_user(get):
        name = password = email = None
        try:
            if "name" in get:
                name = get.name.strip()
            if "password" in get:
                password = get.password.strip()
            if "email" in get:
                email = get.email.strip()
        except (AttributeError, TypeError):
            return json_response(status=False, msg="参数错误")

        RealGitMager().set_global_user(name, password, email)
        return json_response(status=True, msg="设置成功")

    @staticmethod
    def git_pull(get):
        try:
            site_name = get.site_name.strip()
            git_id = get.git_id.strip()
            branch = get.branch.strip()
        except (AttributeError, TypeError):
            return json_response(status=False, msg="参数错误")
        res = RealGitMager().git_pull(git_id, site_name, branch)
        if isinstance(res, str):
            return json_response(status=False, msg=res)
        return json_response(status=True, data=res)

    @staticmethod
    def git_global_user_conf(get=None):
        return GitTool.global_user_conf()

    @staticmethod
    def git_ssh_pub_key(get=None):
        return GitTool.ssh_pub_key()
