# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: baozi <lkq@bt.cn>
# -------------------------------------------------------------------

# ------------------------------
# Python模型
# ------------------------------

import os, re, json, time, shutil, psutil
import sys
import ssh_terminal
import subprocess
from projectModel.base import projectBase
import public
from typing import Union, Dict, TextIO, Optional, Tuple, List, Set, Callable

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")
from mod.base import json_response
from mod.project.python.pyenv_tool import EnvironmentManager, PythonEnvironment
from urllib3.util import Url, parse_url

try:
    from BTPanel import cache, python_env_ssh
    from projectModel.btpyvm import PYVM
except:
    PYVM = None
    pass


def _init_gvm() -> None:
    panel_path = "/www/server/panel"
    pyvm_path = "/usr/bin/pyvm"
    bt_py_project_env_path = "/usr/bin/py-project-env"
    try:
        if not os.path.exists(pyvm_path):
            real_path = '{}/class/projectModel/btpyvm.py'.format(panel_path)
            os.chmod(real_path, mode=0o755)
            os.symlink(real_path, pyvm_path)

        if not os.path.exists(bt_py_project_env_path):
            real_path = '{}/script/btpyprojectenv.sh'.format(panel_path)
            os.chmod(real_path, mode=0o755)
            os.symlink(real_path, bt_py_project_env_path)
    except Exception:
        pass


_init_gvm()
del _init_gvm


class main(projectBase):
    _panel_path = public.get_panel_path()
    _project_path = '/www/server/python_project'
    _log_name = '项目管理'
    _pyv_path = '/www/server/pyporject_evn'
    _tmp_path = '/var/tmp'
    _logs_path = '{}/vhost/logs'.format(_project_path)
    _script_path = '{}/vhost/scripts'.format(_project_path)
    _pid_path = '{}/vhost/pids'.format(_project_path)
    _env_path = '{}/vhost/env'.format(_project_path)
    _prep_path = '{}/prep'.format(_project_path)
    _activate_path = '{}/active_shell'.format(_project_path)
    _project_logs = '/www/wwwlogs/python'
    _vhost_path = '{}/vhost'.format(_panel_path)
    _pip_source = "https://mirrors.aliyun.com/pypi/simple/"
    __log_split_script_py = public.get_panel_path() + '/script/run_log_split.py'
    _project_conf = {}
    _pids = None
    pip_source_dict = {
        "阿里云": "https://mirrors.aliyun.com/pypi/simple/",
        "清华大学": "https://pypi.tuna.tsinghua.edu.cn/simple",
        "中国科技大学": "https://pypi.mirrors.ustc.edu.cn/simple/",
        "豆瓣": "https://pypi.douban.com/simple/",
        "腾讯云": "https://mirrors.cloud.tencent.com/pypi/simple",
        "华为云": "https://mirrors.huaweicloud.com/repository/pypi/simple",
        "网易": "https://mirrors.163.com/pypi/simple/"
    }

    def __init__(self):
        if not os.path.exists(self._project_path):
            os.makedirs(self._project_path, mode=0o755)

        if not os.path.exists(self._logs_path):
            os.makedirs(self._logs_path, mode=0o777)

        if not os.path.exists(self._project_logs):
            os.makedirs(self._project_logs, mode=0o777)

        if not os.path.exists(self._pyv_path):
            os.makedirs(self._pyv_path, mode=0o755)

        if not os.path.exists(self._script_path):
            os.makedirs(self._script_path, mode=0o755)

        if not os.path.exists(self._pid_path):
            os.makedirs(self._pid_path, mode=0o777)

        if not os.path.exists(self._prep_path):
            os.makedirs(self._prep_path, mode=0o755)

        if not os.path.exists(self._env_path):
            os.makedirs(self._env_path, mode=0o755)

        if not os.path.exists(self._activate_path):
            os.makedirs(self._activate_path, mode=0o755)
        self._pids = None
        self._pyvm_tool = None
        self._environment_manager: Optional[EnvironmentManager] = None

    @property
    def pyvm(self):
        if PYVM is None:
            return None
        if self._pyvm_tool is None:
            self._pyvm_tool = PYVM()
        return self._pyvm_tool

    @property
    def environment_manager(self):
        if self._environment_manager is None:
            self._environment_manager = EnvironmentManager()
        return self._environment_manager

    def need_update_project(self, update_name: str):
        tip_file = "{}/{}.pl".format(self._project_path, update_name)
        if os.path.exists(tip_file):
            return True
        return False

    # def get_cloud_version(self, get=None):
    #     """从云端获取Python版本
    #     @author baozi <202-02-22>
    #     @param:
    #     @return  list[str] : 可用python版本列表
    #     """
    #     res = public.httpGet(public.get_url() + '/install/plugin/pythonmamager/pyv.txt')
    #     if not res:
    #         return {"status": False,
    #                 "msg": "请求不到官方python版本数据，请切换节点试一试.<br>相关教程参考:<br><a>https://www.bt.cn/bbs/thread-87257-1-1.html</a>"}
    #     text = res.split('\n')
    #     pyv_data = {"v": text, "time": int(time.time())}
    #     public.writeFile('{}/pyproject_v.txt'.format(self._tmp_path), json.dumps(pyv_data))
    #     return text
    #
    # def get_pyv_can_install(self):
    #     """获取那些版本的python能安装
    #     @author baozi <202-02-22>
    #     @param:
    #     @return  list[str] : 可用python版本列表
    #     """
    #     pyv_data = public.readFile('{}/pyproject_v.txt'.format(self._tmp_path))
    #     if not pyv_data:
    #         return self.get_cloud_version()
    #     try:
    #         res: dict = json.loads(pyv_data)
    #         if time.time() - res["time"] > 60 * 60 * 24 * 30:
    #             return self.get_cloud_version()
    #         else:
    #             return res["v"]
    #     except:
    #         return self.get_cloud_version()
    #
    # def GetCloudPython(self, get):
    #     """显示可以安装的python版本
    #
    #     @author baozi <202-02-22>
    #     @param:
    #         get  (dict ):  无请求信息
    #     @return  msg : 返回Python版本的安装情况
    #     """
    #     data = self.get_pyv_can_install()
    #     existpy = self._get_python_v(get)
    #     if "status" in data:
    #         return public.returnMsg(False, data["msg"])
    #     v = []
    #     l = {}
    #     for i in data:
    #         i = i.strip()
    #         if re.match(r"[\d\.]+", i):
    #             v.append(i)
    #     for i in v:
    #         if i.split()[0] in existpy:
    #             l[i] = "1"
    #         else:
    #             l[i] = "0"
    #
    #     l = sorted(l.items(), key=lambda d: [int(i) for i in d[0].split('.')], reverse=True)
    #     for i, v in enumerate(l):
    #         l[i] = {"version": v[0], "installed": v[1]}
    #     return public.return_data(True, l)

    # def _get_python_v(self, get):
    #     """获取已安装的Python版本
    #     @author baozi <202-02-22>
    #     @param:
    #         get  (dict ):  无请求信息
    #     @return  list[str] : 已安装python版本列表
    #     """
    #     if get is not None and "is_pypy" in get and get.is_pypy in ("1", "true", 1, True):
    #         path = '{}/pypy_versions'.format(self._pyv_path)
    #     else:
    #         path = '{}/versions'.format(self._pyv_path)
    #     if not os.path.exists(path):
    #         return []
    #     data = os.listdir(path)
    #     return data

    # def GetPythonVersion(self, get):
    #     """获取已安装的Python版本
    #     @author baozi <202-02-22>
    #     @param:
    #         get  (dict ):  无请求信息
    #     @return  list[str] : 已安装python版本列表
    #     """
    #     return self._get_python_v(get)

    # def InstallPythonV(self, get):
    #     """安装新的Python
    #     @author baozi <202-02-22>
    #     @param:
    #         get  (dict): 请求信息,包含版本号
    #     @return  msg :  是否安装成功
    #     """
    #     can_install = self.get_pyv_can_install()
    #     if get.version not in can_install:
    #         return public.returnMsg(False, '该版本尚未支持，请到论坛反馈。')
    #     if get.version in self._get_python_v(None):
    #         return public.returnMsg(False, "该版本已安装过，无需重复安装")
    #     _sh = f"bash {self._panel_path}/script/get_python.sh {get.version} {public.get_url()}&> {self._logs_path}/py.log"
    #     public.ExecShell(_sh)
    #     path = '{}/versions/{}/bin/'.format(self._pyv_path, get.version)
    #     if "2.7" in get.version:
    #         path = path + "python"
    #     else:
    #         path = path + "python3"
    #     if os.path.exists(path):
    #         # public.writeFile(f"{self._logs_path}/py.log", "")
    #         return public.returnMsg(True, "安装成功！")
    #     return public.returnMsg(False, "安装失败！{}".format(path))

    # def install_pip(self, vpath, pyv, is_pypy=False):
    #     """安装包管理工具pip
    #     @author baozi <202-02-22>
    #     @param:
    #         vpath  (str):  Python环境地址
    #         pyv  (str):  Python版本
    #     @return
    #     """
    #     if self.pyvm is not None:
    #         self.pyvm.is_pypy = is_pypy
    #         self.pyvm.re_install_pip_tools(pyv, vpath)
    #         return
    #
    #     # 以下部分不再使用，使用pyvm安装pip
    #     if [int(i) for i in pyv.split('.')] > [3, 6]:
    #         pyv = "3.6"
    #
    #     _pyv = pyv.split('.')[1]
    #     _sh = f'bash {self._panel_path}/script/get_python.sh {pyv} {public.get_url()} {vpath} &>> {self._logs_path}/py.log'
    #     public.ExecShell(_sh)
    #     res = public.ExecShell("{}/bin/pip3 -V".format(vpath))[0]
    #     if res.find(vpath) == -1:
    #         public.ExecShell("rm -rf {}/bin/pip*".format(vpath))
    #         public.ExecShell("rm -rf {}/lib/python{}/site-packages/pip*".format(vpath, pyv))
    #         public.ExecShell("rm -rf {}/bin/python3 -m ensurepip --default-pip")

    # def __write_log(self, pjname, msg):
    #     """写日志
    #     @author baozi <202-02-22>
    #     @param:
    #         pjname ( str ) : 项目名称
    #         msg  ( dict ):  需要写入的日志信息
    #     @return
    #     """
    #     path = f"{self._logs_path}/{pjname}.log"
    #     localtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    #     if not os.path.exists(path):
    #         public.ExecShell("touch %s" % path)
    #     public.writeFile(path, localtime + "\n" + msg + "\n", "a+")

    def RemovePythonV(self, get):
        """卸载面板安装的Python
        @author baozi <202-02-22>
        @param:
            get  ( dict ):  请求信息，包含要删除的版本信息
        @return  msg : 是否删除成功
        """
        v = get.version.split()[0]
        if "is_pypy" in get and get.is_pypy in ("1", "true", 1, True):
            path = '{}/pypy_versions'.format(self._pyv_path)
        else:
            path = '{}/versions'.format(self._pyv_path)
        if not os.path.exists(path):
            return public.returnMsg(True, "卸载Python成功")
        python_bin = "{}/{}/bin/python".format(path, v)
        if not os.path.exists(python_bin):
            python_bin = "{}/{}/bin/python3".format(path, v)
        if not os.path.exists(python_bin):
            return public.returnMsg(False, "Python版本不存在")

        res = EnvironmentManager().multi_remove_env(os.path.realpath(python_bin))
        return res

    # def remove_python(self, pyv):
    #     """删除安装目录
    #     @author baozi <202-02-22>
    #     @param:
    #         pyv  ( str ):  版本号
    #     @return
    #     """
    #     py_path = f'{self._pyv_path}/versions/{pyv}'
    #     if os.path.exists(py_path):
    #         import shutil
    #         shutil.rmtree(py_path)

    def _get_project_conf(self, name_id) -> Union[Dict, bool]:
        """获取项目的配置信息
        @author baozi <202-02-22>
        @param:
            name_id  ( str|id ):  项目名称或者项目id
        @return dict_onj: 项目信息
        """
        if isinstance(name_id, int):
            _id = name_id
            _name = None
        else:
            _id = None
            _name = name_id
        data = public.M('sites').where('project_type=? AND (name = ? OR id = ?)', ('Python', _name, _id)).field(
            'name,path,status,project_config').find()
        if not data: return False
        project_conf = json.loads(data['project_config'])
        if "env_list" not in project_conf:
            project_conf["env_list"] = []
        if "env_file" not in project_conf:
            project_conf["env_file"] = ""
        if "call_app" not in project_conf:
            project_conf["call_app"] = ""
        if not os.path.exists(data["path"]):
            self.__stop_project(project_conf)
        return project_conf

        # 获取已经安装的模块

    # def GetPackages(self, get):
    #     conf = self._get_project_conf(get.name.strip())
    #     if not conf:
    #         return public.returnMsg(False, "没有该项目，请尝试刷新页面")
    #
    #     piplist = []
    #     l = public.ExecShell("%s list" % self._get_vp_pip(conf["vpath"]))[0].split("\n")
    #     for d in l[2:]:
    #         try:
    #             p, v = d.split()
    #             piplist.append((p, v))
    #         except:
    #             pass
    #     return piplist

    # def MamgerPackage(self, get):
    #     """安装与卸载虚拟环境模块
    #     @author baozi <202-02-22>
    #     @param:
    #         get  ( 请求信息 ):  包含操作act,pjname,p,v
    #     @return  msg : 操作成功与否
    #     """
    #     conf = self._get_project_conf(get.name.strip())
    #     if not conf:
    #         return public.returnMsg(False, "没有该项目，请尝试刷新页面")
    #     if self.prep_status(conf) == "running":
    #         return public.returnMsg(False, "项目环境安装制作中.....<br>请勿操作")
    #     vp = conf["vpath"]
    #     if get.act == "install":
    #         tmp_env = self.build_mysql_env()
    #         _sh = f"%s install -i {self._pip_source} %s"
    #         pkg = get.p if not get.v else f"{get.p}=={get.v}"
    #         if get.p.lower() == "mysqlclient":
    #             _sh = tmp_env + _sh
    #         public.ExecShell(_sh % (self._get_vp_pip(vp), pkg))
    #         pkgs = public.ExecShell("%s list" % self._get_vp_pip(vp))[0]
    #         _pkg = get.p.lower()
    #         if '_' in _pkg:
    #             _pkg = _pkg.replace("_", "-")
    #         if get.p.lower() in pkgs.lower() or _pkg in pkgs.lower():
    #             return public.returnMsg(True, "安装成功")
    #         else:
    #             return public.returnMsg(False, "安装失败")
    #     else:
    #         if get.p == "pip":
    #             return public.returnMsg(False, "PIP不能卸载。。。。")
    #         _sh = "echo 'y' | %s uninstall %s"
    #         public.ExecShell(_sh % (self._get_vp_pip(vp), get.p))
    #         packages = public.ExecShell("%s list" % self._get_vp_pip(vp))[0]
    #         if get.p not in packages.lower():
    #             return public.returnMsg(True, "卸载成功")
    #         else:
    #             return public.returnMsg(False, "卸载失败")

    def _get_vp_pip(self, vpath):
        """获取虚拟环境下的pip
        @author baozi <202-02-22>
        @param:
            vpath  ( str ):  虚拟环境位置
        @return  str : pip 位置
        """
        if os.path.exists('{}/bin/pip'.format(vpath)):
            return '{}/bin/pip'.format(vpath)
        else:
            return '{}/bin/pip3'.format(vpath)

    def _get_vp_python(self, vpath):
        """获取虚拟环境下的python解释器
        @author baozi <202-02-22>
        @param:
            vpath  ( str ):  虚拟环境位置
        @return  str : python解释器 位置
        """
        if os.path.exists('{}/bin/python'.format(vpath)):
            return '{}/bin/python'.format(vpath)
        else:
            return '{}/bin/python3'.format(vpath)

    @staticmethod
    def _check_port(port: str):
        """检查端口是否合格
        @author baozi <202-02-22>
        @param
            port  ( str ):  端口号
        @return   [bool,msg]: 结果 + 错误信息
        """
        try:
            if 0 < int(port) < 65535:
                data = public.ExecShell("ss  -nultp|grep ':%s '" % port)[0]
                if data:
                    return False, "该端口已经被占用"
                else:
                    return True, ""
            else:
                return False, "请输入正确的端口范围 1 < 端口 < 65535"
        except ValueError:
            return False, "端口请输入整数"

    @staticmethod
    def _check_project_exist(project_name):
        """检查项目是否存在
        @author baozi <202-02-22>
        @param:
            pjname  ( str ):  项目名称
            path  ( str ):  项目路径
        @return  bool : 返回验证结果
        """
        data = public.M('sites').where('name=?', (project_name,)).field('id').find()
        return bool(data)

    @staticmethod
    def _check_project_path_exist(path=None):
        """检查项目地址是否存在
        @author baozi <202-02-22>
        @param:
            pjname  ( str ):  项目名称
            path  ( str ):  项目路径
        @return  bool : 返回验证结果
        """
        data = public.M('sites').where('path=? ', (path,)).field('id').find()
        return bool(data)

    @staticmethod
    def __check_feasibility(values):
        """检查用户部署方式的可行性
        @author baozi <202-02-22>
        @param:
            values  ( dict ):  用户输入参数的规范化数据
        @return  msg
        """
        re_v = re.compile(r"\s+(?P<ver>[23]\.\d+(\.\d+)?)\s*")
        version_res = re_v.search(values["version"])
        if not version_res:
            return None
        version = version_res.group("ver")
        xsgi = values["xsgi"]
        framework = values["framework"]
        stype = values["stype"]
        if framework == "sanic" and [int(i) for i in version.split('.')[:2]] < [3, 7]:
            return "sanic框架不支持python3.7以下的版本"
        if xsgi == "asgi" and stype == "uwsgi":
            return "uWsgi服务框架不支持asgi协议"

    # @staticmethod
    # def copy_pyv(src: str, dst: str):
    #     """复制python环境到指定项目"""
    #     import files
    #     get = public.dict_obj()
    #     get.sfile = src
    #     get.dfile = dst
    #     files.files().CopyFile(get)
    #
    #     if not os.path.exists(dst):
    #         return False
    #     python3 = os.path.join(dst, 'bin/python3')
    #     python = os.path.join(dst, 'bin/python')
    #     if os.path.exists(python3) and not os.path.exists(python):
    #         os.symlink(python3, python)
    #
    #     import pwd
    #     res = pwd.getpwnam('www')
    #     uid = res.pw_uid
    #     gid = res.pw_gid
    #     os.chown(get.dfile, uid, gid)
    #     return True

    def simple_prep_env(self, values: dict) -> Optional[bool]:
        """
        准备python虚拟环境和服务器应用
        """
        log_path: str = "{}/{}.log".format(self._logs_path, values['pjname'])
        fd = open(log_path, 'w')
        fd.flush()
        py_env = EnvironmentManager().get_env_py_path(values.get("python_bin", ""))
        if not py_env:
            fd.write("|- 环境丢失，无法继续初始化python环境。")
            fd.flush()
            fd.close()
            return False

        def call_log(log: str) -> None:
            if log[-1] != "\n":
                log += "\n"
            fd.write(log)
            fd.flush()

        try:
            # 安装服务器依赖
            call_log("\n|- 开始安装托管服务依赖库.\n")
            py_env.init_site_server_pkg(call_log=call_log)
            py_env.use2project(values['pjname'])
            # 安装第三方依赖
            self.install_requirement(values, py_env, call_log=call_log)
            self.__prepare_start_conf(values, pyenv=py_env)
            call_log("\n|- 配置文件输出成功\n")
            initialize = values.get("initialize", '')
            if initialize:
                call_log("\n|- 开始执行项目初始化命令.......\n")
                if values.get("env_list", None) or values.get("env_file", None):
                    env_file = "{}/{}.env".format(self._env_path, values["pjname"])
                    initialize = "source {env_file} \n".format(env_file=env_file) + initialize
                py_env.exec_shell(initialize, call_log=call_log, user=values.get("user", "root"))
                call_log("\n|- 项目初始化命令执行结束-------\n")

            # 先尝试启动
            conf = self._get_project_conf(values['pjname'])
            self.__start_project(conf)
            call_log("\n|- 已尝试启动项目\n")
            for k, v in values.items():  # 更新配置文件
                if k not in conf:
                    conf[k] = v

            pdata = {
                "project_config": json.dumps(conf)
            }
            public.M('sites').where('name=?', (values['pjname'].strip(),)).update(pdata)
            fd.close()
        except:
            import traceback
            if not fd.closed:
                fd.write(traceback.format_exc())
                fd.write("\n|- 环境准备失败\n")
                fd.close()
        return True

    def install_requirement(self, values: dict, pyenv: PythonEnvironment, call_log: Callable[[str], None]):
        if "requirement_path" in values and values["requirement_path"] is not None:
            call_log("\n|- 开始安装需求包....\n")
            requirement_data = public.read_rare_charset_file(values['requirement_path'])
            if not isinstance(requirement_data, str):
                call_log("\n|- 未识别到安装包信息\n")
            list_sh = []
            list_normative_pkg = []
            for i in requirement_data.split("\n"):
                tmp_data = i.strip()
                if not tmp_data or tmp_data.startswith("#"):
                    continue
                if re.search(r"-e\s+\.{0,2}/", tmp_data):  # 本地库依赖且为可编辑模式的不安装
                    continue
                tmp_env = ""
                if tmp_data.find("-e") != -1:
                    tmp_env += "cd {}\n".format(values["path"])
                if tmp_data.find("git+") != -1:
                    tmp_sh = tmp_env + "{} install {}".format(pyenv.pip_bin(), tmp_data)
                    rep_name_list = [re.compile(r"#egg=(?P<name>\S+)"), re.compile(r"/(?P<name>\S+\.git)")]
                    name = tmp_data
                    for tmp_rep in rep_name_list:
                        tmp_name = tmp_rep.search(tmp_data)
                        if tmp_name:
                            name = tmp_name.group("name")
                            break
                    list_sh.append((name, tmp_sh))

                elif tmp_data.find("file:") != -1:
                    tmp_sh = tmp_env + "{} install {}".format(pyenv.pip_bin(), tmp_data)

                    list_sh.append((tmp_data.split("file:", 1)[1], tmp_sh))
                else:
                    if tmp_data.find("==") != -1:
                        pkg_name, pkg_version = tmp_data.split("==")
                    elif tmp_data.find(">=") != -1:
                        pkg_name, pkg_version = tmp_data.split(">=")
                    else:
                        pkg_name, pkg_version = tmp_data, ""
                    list_normative_pkg.append((pkg_name, pkg_version))


            length = len(list_sh) + len(list_normative_pkg)
            for idx, (name, tmp_sh) in enumerate(list_sh):
                call_log("\n|- ({}/{})开始安装【{}】...\n".format(idx + 1, length, name))
                pyenv.exec_shell(tmp_sh, call_log=call_log)

            for idx, (name, pkg_version) in enumerate(list_normative_pkg):
                call_log("\n|- ({}/{})开始安装【{}】...\n".format(idx + len(list_sh) + 1, length, name))
                pyenv.pip_install(name, pkg_version, call_log=call_log)
            call_log("\n|- 需求包安装执行完毕....\n")

    def re_prep_env(self, get: public.dict_obj):
        name = get.name.strip()
        project_info = self.get_project_find(name)
        if not project_info:
            return public.returnMsg(False, "项目不存在")
        project_conf = project_info['project_config']

        prep_status = self.prep_status(project_conf)
        if prep_status == "complete":
            return public.returnMsg(False, "项目准备已完成，无需再次准备")
        if prep_status == "running":
            return public.returnMsg(False, "项目准备中，不能再次开启准备")
        self.run_simple_prep_env(project_info["id"], project_conf)
        time.sleep(0.5)
        return public.returnMsg(True, "已重新进行准备，请等待准备完成。")

    @staticmethod
    def exec_shell(sh_str: str, out: TextIO, timeout=None, user=None):
        if user:
            import pwd
            res = pwd.getpwnam(user)
            uid = res.pw_uid
            gid = res.pw_gid

            def preexec_fn():
                os.setgid(gid)
                os.setuid(uid)
        else:
            preexec_fn = None

        p = subprocess.Popen(sh_str, stdout=out, stderr=out, shell=True, preexec_fn=preexec_fn)
        p.wait(timeout=timeout)
        return

    def run_simple_prep_env(self, project_id: int, project_conf: dict) -> Tuple[bool, str]:
        prep_pid_file = "{}/{}.pid".format(self._prep_path, project_conf["pjname"])
        if os.path.exists(prep_pid_file):
            pid = public.readFile(prep_pid_file)
            try:
                ps = psutil.Process(int(pid))
                if ps.is_running():
                    return False, "项目准备中，不能再次开启准备"
            except:
                pass
            os.remove(prep_pid_file)

        tmp_sh = "nohup {}/pyenv/bin/python3 {}/script/py_project_env.py {} &> /dev/null & \necho $! > {}".format(
            self._panel_path, self._panel_path, project_id, prep_pid_file
        )
        res = public.ExecShell(tmp_sh)
        return True, ""

    def prep_status(self, project_conf: dict):
        try:
            prep_pid_file = "{}/{}.pid".format(self._prep_path, project_conf["pjname"])
            pid = public.readFile(prep_pid_file)
            if isinstance(pid, str):
                ps = psutil.Process(int(pid))
                if ps.is_running() and os.path.samefile(ps.exe(), "/www/server/panel/pyenv/bin/python3") and \
                        any("script/py_project_env.py" in tmp for tmp in ps.cmdline()):
                    return "running"
        except:
            pass
        v_path = project_conf["vpath"]
        v_pip: str = self._get_vp_pip(v_path)
        v_python: str = self._get_vp_python(v_path)
        if not os.path.exists(v_path) or not os.path.exists(v_python) or not os.path.exists(v_pip):
            return "failure"
        return "complete"

    # 检查输入参数
    def __check_args(self, get):
        """检查输入的参数
        @author baozi <202-02-22>
        @param:
            get  ( dict ):   创建Python项目时的请求
        @return  dict : 规范化的请求参数
        参数列表：
            pjname
            port
            stype
            path
            user
            requirement_path
            env_list
            env_file
            framework

            可能有：
               # venv_path
               # version

               venv_path 和 version 替换为 python_bin

               initialize

               project_cmd

               xsgi
               rfile
               call_app

               is_pypy
               logpath
               auto_run
        """

        project_cmd = ""
        xsgi = "wsgi"
        rfile = ""
        call_app = "app"
        user = "root"
        initialize = ""
        try:
            pjname = get.pjname.strip()
            port = get.port
            stype = get.stype.strip()
            path = get.path.strip().rstrip("/")
            python_bin = get.get("python_bin/s", "")
            if not python_bin or not os.path.exists(python_bin):
                return False, public.returnMsg(False, "python环境选择错误")
            if "user" in get and get.user.strip():
                user = get.user.strip()
            if "requirement_path" in get and get.requirement_path.strip():
                requirement_path = get.requirement_path.strip()
            else:
                requirement_path = None
            if "env_list" in get and get.env_list:
                if isinstance(get.env_list, str):
                    env_list = json.loads(get.env_list.strip())
                else:
                    env_list = get.env_list
            else:
                env_list = []
            if "env_file" in get and get.env_file.strip():
                env_file = get.env_file.strip()
            else:
                env_file = None
            if "framework" in get and get.framework.strip():
                framework = get.framework.strip()
            else:
                framework = 'python'
            if "project_cmd" in get and get.project_cmd.strip():
                project_cmd = get.project_cmd.strip()
            if "xsgi" in get and get.xsgi.strip():
                if get.xsgi.strip() not in ("wsgi", "asgi"):
                    xsgi = "wsgi"
                else:
                    xsgi = get.xsgi.strip()
            if "rfile" in get and get.rfile.strip():
                rfile = get.rfile.strip()
                if not os.path.exists:
                    return False, public.returnMsg(False, "项目启动文件不存在")
            if "call_app" in get and get.call_app.strip():
                call_app = get.call_app.strip()
            if "initialize" in get and get.initialize.strip():
                initialize = get.initialize.strip()
        except:
            return False, public.returnMsg(False, "参数错误")

        danger_cmd_list = [
            'rm', 'rmi', 'kill', 'init', 'shutdown', 'reboot', 'chmod', 'chown', 'dd', 'fdisk', 'killall', 'mkfs',
            'mkswap', 'mount', 'swapoff', 'swapon', 'umount', 'userdel', 'usermod', 'passwd', 'groupadd', 'groupdel',
            'groupmod', 'chpasswd', 'chage', 'usermod', 'useradd', 'userdel', 'pkill'
        ]

        name_rep = re.compile(r"""[\\/:*<|>"'#&$^)(]+""")
        if name_rep.search(pjname):
            return False, public.returnMsg(False, "项目名称不能包含特殊字符")
        # 命令行启动跳过端口检测
        flag, msg = (True, "") if stype == "command" and port == "" else self._check_port(port)
        if not flag:
            return False, public.returnMsg(False, msg)
        if stype not in ("uwsgi", "gunicorn", "command"):
            return False, public.returnMsg(False, "运行方式选择错误")
        if not os.path.isdir(path):
            return False, public.returnMsg(False, "项目路径不存在")
        if user not in self.get_system_user_list():
            return False, public.returnMsg(False, "用户名不存在")
        if not isinstance(env_list, list):
            return False, public.returnMsg(False, "环境变量格式错误")
        if env_file and not os.path.isfile(env_file):
            return False, public.returnMsg(False, "环境变量文件不存在")

        if initialize:
            for d_cmd in danger_cmd_list:
                if re.search(r"\s+%s\s+" % d_cmd, project_cmd):
                    return False, public.returnMsg(False, "当前初始化操作中存在危险命令:{}".format(d_cmd))

        is_pypy = False
        if "is_pypy" in get:
            is_pypy = get.is_pypy in ("1", "true", 1, True, "True")

        # 处理环境相关参数
        # if "venv_path" in get and get.venv_path.strip():
        #     venv_path: str = get.venv_path.strip()
        #     if not os.path.exists(venv_path):
        #         return False, public.returnMsg(False, "指定的环境不存在")
        #     if venv_path.endswith("/"):
        #         venv_path = venv_path[:-1]
        #     if venv_path.endswith("/bin"):
        #         venv_path = venv_path[:-4]
        #     python_bin = None
        #     if os.path.isfile(venv_path + "/bin/python"):
        #         python_bin = venv_path + "/bin/python"
        #     elif os.path.isfile(venv_path + "/bin/python3"):
        #         python_bin = venv_path + "/bin/python3"
        #
        #     if not python_bin:
        #         return False, public.returnMsg(False, "指定的环境不存在")
        #
        #     out, error = public.ExecShell("{} -V".format(python_bin))
        #     res = re.search(r"(?P<ver>(\d+\.){1,2}\d*)", out)
        #     if not res:
        #         return False, public.returnMsg(False, "指定的环境检测错误")
        #     else:
        #         version = res.group("ver")
        # elif "version" in get and get.version.strip():
        #     version = get.version.strip()
        #     if is_pypy:
        #         if not os.path.exists("{}/pypy_versions/{}".format(self._pyv_path, version)):
        #             return False, public.returnMsg(False, "指定的环境版本不存在")
        #     else:
        #         if not os.path.exists("{}/versions/{}".format(self._pyv_path, version)):
        #             return False, public.returnMsg(False, "指定的环境版本不存在")
        #     venv_path = self._pyv_path + '/' + pjname + "_venv"
        # else:
        #     return False, public.returnMsg(False, "未指定运行环境")

        em = EnvironmentManager()
        env = em.get_env_py_path(python_bin)
        if not env:
            return False, public.returnMsg(False, "未找到指定运行环境")

        auto_run = False
        if "auto_run" in get:
            auto_run = get.auto_run in ("1", "true", 1, True, "True")

        if "logpath" not in get or not get.logpath.strip():
            logpath = os.path.join(self._project_logs, pjname)
        else:
            logpath = get.logpath.strip()
            if not os.path.exists(logpath):
                logpath = os.path.join(self._project_logs, pjname)

        # 对run_file 进行检查
        if stype == "command":
            if not project_cmd:
                return False, public.returnMsg(False, "缺少必要的启动命令")
        else:
            if not xsgi or not rfile or not call_app:
                return False, public.returnMsg(False, "缺少必要的服务器托管启动参数")

        if requirement_path and not os.path.isfile(requirement_path):
            return False, public.returnMsg(False, "未找到指定依赖包文件【requirement.txt】")

        if self._check_project_exist(pjname):
            return False, public.returnMsg(False, "项目已经存在")
        if self._check_project_path_exist(path):
            return False, public.returnMsg(False, "该路径已存在其他项目")

        return True, {
            "pjname": pjname,
            "port": port,
            "stype": stype,
            "path": path,
            "user": user,
            "requirement_path": requirement_path,
            "env_list": env_list,
            "env_file": env_file,
            "framework": framework,
            "vpath": os.path.dirname(os.path.dirname(env.bin_path)),
            "version": env.version,
            "python_bin": env.bin_path,
            "project_cmd": project_cmd,
            "xsgi": xsgi,
            "rfile": rfile,
            "call_app": call_app,
            "auto_run": auto_run,
            "logpath": logpath,
            "is_pypy": is_pypy,
            "initialize": initialize,
        }

    def CreateProject(self, get):
        """创建Python项目
        @author baozi <202-02-22>
        @param:
            get  ( dict ):  请求信息
        @return  test : 创建情况
        """
        # 检查输入参数
        flag, values = self.__check_args(get)
        if not flag:
            return values

        public.set_module_logs("create_python_project", "create")
        # 检查服务器部署的可行性
        msg = self.__check_feasibility(values)
        if msg:
            return public.returnMsg(False, msg)

        # 默认不开启映射，不绑定外网
        values["domains"], values["bind_extranet"] = [], 0
        # 默认进程数与线程数
        values["processes"], values["threads"] = 4, 2
        # 默认日志等级info
        values["loglevel"] = "info"
        # 默认uwsgi使用http
        values['is_http'] = "is_http"

        p_data = {
            "name": values["pjname"],
            "path": values["path"],
            "ps": values["pjname"],
            "status": 1,
            'type_id': 0,
            "project_type": "Python",
            "addtime": public.getDate(),
            "project_config": json.dumps(values)
        }
        res = public.M("sites").insert(p_data)
        if isinstance(res, str) and res.startswith("error"):
            return public.returnMsg(False, "项目记录失败，请联系官方")

        self.run_simple_prep_env(res, values)
        time.sleep(0.5)
        # 返回信息
        public.WriteLog(self._log_name, "添加Python项目{}".format(values["pjname"]))
        flag, tip = self._release_firewall(get)
        tip = "" if flag else "<br>" + tip
        return public.returnMsg(True, "项目添加成功" + tip)

    def __prepare_start_conf(self, values, force=False, pyenv: Optional[PythonEnvironment]=None):
        """准备启动的配置文件,python运行不需要,uwsgi和gunicorn需要
        @author baozi <202-02-22>
        @param:
            values  ( dict ):  用户传入的参数
        @return   :
        """
        # 加入默认配置
        if pyenv is None:
            pyenv = EnvironmentManager().get_env_py_path(values.get("python_bin", values.get("vpath")))
            public.print_log(pyenv.to_dict())
        if not pyenv:
            return
        values["user"] = values['user'] if 'user' in values else 'root'
        values["processes"] = values['processes'] if 'processes' in values else 4
        values["threads"] = values['threads'] if 'threads' in values else 2
        if not os.path.isdir(values['logpath']):
            os.makedirs(values['logpath'], mode=0o777)

        env_file = "{}/{}.env".format(self._env_path, values["pjname"])
        self._build_env_file(env_file, values)

        self.__prepare_uwsgi_start_conf(values, pyenv, force)
        self.__prepare_gunicorn_start_conf(values, pyenv, force)
        if "project_cmd" not in values:
            values["project_cmd"] = ''
        self.__prepare_cmd_start_conf(values, pyenv, force)
        self.__prepare_python_start_conf(values, pyenv, force)

    @staticmethod
    def _get_callable_app(project_config: dict):
        callable_app = "application" if project_config['framework'] == "django" else "app"
        data = public.read_rare_charset_file(project_config.get("rfile", ""))
        if isinstance(data, str):
            re_list = (
                re.compile(r"\s*(?P<app>\w+)\s*=\s*(make|create)_?app(lication)?", re.M | re.I),
                re.compile(r"\s*(?P<app>app|application)\s*=\s*", re.M | re.I),
                re.compile(r"\s*(?P<app>\w+)\s*=\s*(Flask\(|flask\.Flask\()", re.M | re.I),
                re.compile(r"\s*(?P<app>\w+)\s*=\s*(Sanic\(|sanic\.Sanic\()", re.M | re.I),
                re.compile(r"\s*(?P<app>\w+)\s*=\s*get_wsgi_application\(\)", re.M | re.I),
                re.compile(r"\s*(?P<app>\w+)\s*=\s*(FastAPI\(|fastapi\.FastAPI\()", re.M | re.I),
                re.compile(r"\s*(?P<app>\w+)\s*=\s*.*web\.Application\(", re.M | re.I),
                re.compile(r"\s*(?P<app>server|service|web|webserver|web_server|http_server|httpserver)\s*=\s*",
                           re.M | re.I),
            )
            for i in re_list:
                res = i.search(data)
                if not res:
                    continue
                callable_app = res.group("app")
                break

        return callable_app

    def __prepare_uwsgi_start_conf(self, values, pyenv: PythonEnvironment, force=False):
        # uwsgi
        if not values["rfile"]:
            return
        uwsgi_file = "{}/uwsgi.ini".format(values['path'])
        cmd_file = "{}/{}_uwsgi.sh".format(self._script_path, values["pjname"])
        if not force and os.path.exists(uwsgi_file) and os.path.exists(cmd_file):
            return

        template_file = "{}/template/python_project/uwsgi_conf.conf".format(self._vhost_path)
        values["is_http"] = values["is_http"] if "is_http" in values else True
        env_file = "{}/{}.env".format(self._env_path, values["pjname"])

        if "call_app" not in values or not values["call_app"]:
            callable_app = self._get_callable_app(values)
        else:
            callable_app = values["call_app"]
        if not os.path.exists(uwsgi_file):
            config_body: str = public.readFile(template_file)
            config_body = config_body.format(
                path=values["path"],
                rfile=values["rfile"],
                processes=values["processes"],
                threads=values["threads"],
                is_http="" if values["is_http"] else "#",
                is_socket="#" if values["is_http"] else "",
                port=values["port"],
                user=values["user"],
                logpath=values['logpath'],
                app=callable_app,
            )
            public.writeFile(uwsgi_file, config_body)
        pid_file = "{}/{}.pid".format(self._pid_path, values["pjname"])

        _sh = "%s -d --ini %s/uwsgi.ini --pidfile='%s'" % (pyenv.uwsgi_bin() or "uwsgi", values['path'], pid_file)
        values["start_sh"] = _sh

        self._create_cmd_file(
            cmd_file=cmd_file,
            v_ptah_bin=os.path.dirname(self._get_vp_python(values['vpath'])),
            project_path=values["path"],
            command=_sh,
            log_file="{}/uwsgi.log".format(values["logpath"]),
            pid_file="/dev/null",
            env_file=env_file,
            activate_sh= pyenv.activate_shell(),
            evn_name=public.Md5(values["pjname"]),
        )

    def __prepare_gunicorn_start_conf(self, values, pyenv: PythonEnvironment, force=False):
        # gunicorn
        if not values["rfile"]:
            return
        gconf_file = "{}/gunicorn_conf.py".format(values['path'])
        cmd_file = "{}/{}_gunicorn.sh".format(self._script_path, values["pjname"])
        if not force and os.path.exists(gconf_file) and os.path.exists(cmd_file):
            return

        worker_class = "sync" if values["xsgi"] == "wsgi" else 'uvicorn.workers.UvicornWorker'
        template_file = "{}/template/python_project/gunicorn_conf.conf".format(self._vhost_path)
        values["loglevel"] = values["loglevel"] if "loglevel" in values else "info"
        if not os.path.exists(gconf_file):
            config_body: str = public.readFile(template_file)
            config_body = config_body.format(
                path=values["path"],
                processes=values["processes"],
                threads=values["threads"],
                user=values["user"],
                worker_class=worker_class,
                port=values["port"],
                logpath=values['logpath'],
                loglevel=values["loglevel"]
            )
            public.writeFile(gconf_file, config_body)

        error_log = '{}/gunicorn_error.log'.format(values["logpath"])
        access_log = '{}/gunicorn_acess.log'.format(values["logpath"])
        if not os.path.isfile(error_log):
            public.writeFile(error_log, "")
        if not os.path.isfile(access_log):
            public.writeFile(access_log, "")
        self._pass_dir_for_user(values["logpath"], values["user"])
        public.set_own(error_log, values["user"])
        public.set_own(access_log, values["user"])
        _app = values['rfile'].replace((values['path'] + "/"), "")[:-3]
        _app = _app.replace("/", ".")
        if "call_app" not in values or not values["call_app"]:
            callable_app = self._get_callable_app(values)
        else:
            callable_app = values["call_app"]
        _app += ":" + callable_app
        _sh = "%s -c %s/gunicorn_conf.py %s " % (pyenv.gunicorn_bin() or "gunicorn", values['path'], _app)

        values["start_sh"] = _sh
        pid_file = "{}/{}.pid".format(self._pid_path, values["pjname"])
        env_file = "{}/{}.env".format(self._env_path, values["pjname"])
        self._create_cmd_file(
            cmd_file=cmd_file,
            v_ptah_bin=os.path.dirname(self._get_vp_python(values['vpath'])),
            project_path=values["path"],
            command=_sh,
            log_file=error_log,
            pid_file=pid_file,
            env_file=env_file,
            activate_sh= pyenv.activate_shell(),
            evn_name=public.Md5(values["pjname"]),
        )

    def __prepare_cmd_start_conf(self, values, pyenv: PythonEnvironment, force=False):
        if "project_cmd" not in values or not values["project_cmd"]:
            return
        cmd_file = "{}/{}_cmd.sh".format(self._script_path, values["pjname"])
        if not force and os.path.exists(cmd_file):
            return
        pid_file = "{}/{}.pid".format(self._pid_path, values["pjname"])
        log_file = values['logpath'] + "/error.log"
        env_file = "{}/{}.env".format(self._env_path, values["pjname"])

        self._create_cmd_file(
            cmd_file=cmd_file,
            v_ptah_bin=os.path.dirname(self._get_vp_python(values['vpath'])),
            project_path=values["path"],
            command=values["project_cmd"],
            log_file=log_file,
            pid_file=pid_file,
            env_file=env_file,
            activate_sh= pyenv.activate_shell(),
            evn_name=public.Md5(values["pjname"]),
        )

        values["start_sh"] = values["project_cmd"]

    def __prepare_python_start_conf(self, values, pyenv: PythonEnvironment, force=False):
        if not values["rfile"]:
            return
        cmd_file = "{}/{}_python.sh".format(self._script_path, values["pjname"])
        if not force and os.path.exists(cmd_file):
            return
        pid_file = "{}/{}.pid".format(self._pid_path, values["pjname"])
        env_file = "{}/{}.env".format(self._env_path, values["pjname"])
        self._build_env_file(env_file, values)

        log_file = (values['logpath'] + "/error.log").replace("//", "/")
        v_python = self._get_vp_python(values['vpath'])
        command = "{vpath} -u {run_file} {parm} ".format(
            vpath=v_python,
            run_file=values['rfile'],
            parm=values.get("parm", "")
        )
        self._create_cmd_file(
            cmd_file=cmd_file,
            v_ptah_bin=os.path.dirname(v_python),
            project_path=values["path"],
            command=command,
            log_file=log_file,
            pid_file=pid_file,
            env_file=env_file,
            activate_sh= pyenv.activate_shell(),
            evn_name=public.Md5(values["pjname"]),
        )

        values["start_sh"] = command

    @staticmethod
    def _build_env_file(env_file: str, values: dict):
        env_body_list = []
        if "env_file" in values and values["env_file"] and os.path.isfile(values["env_file"]):
            env_body_list.append("source {}\n".format(values["env_file"]))
        if "env_list" in values:
            for tmp in values["env_list"]:
                if "k" not in tmp or "v" not in tmp:
                    continue
                env_body_list.append("export {}={}\n".format(tmp["k"], tmp["v"]))

        public.writeFile(env_file, "".join(env_body_list))

    @staticmethod
    def _create_cmd_file(cmd_file, v_ptah_bin, project_path, command, log_file, pid_file, env_file, activate_sh='', evn_name=""):
        start_cmd = '''#!/bin/bash
PATH={v_ptah_bin}:{project_path}:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
export BT_PYTHON_SERVICE_SID={sid}
{activate_sh}
source {env_file}
cd {project_path}
nohup {command} &>> {log_file} &
echo $! > {pid_file}'''.format(
            v_ptah_bin=v_ptah_bin,
            activate_sh=activate_sh,
            project_path=project_path,
            command=command,
            log_file=log_file,
            pid_file=pid_file,
            env_file=env_file,
            sid=evn_name,
        )
        public.writeFile(cmd_file, start_cmd)

    def _get_cmd_file(self, project_conf):
        cmd_file_map = {
            "python": "_python.sh",
            "uwsgi": "_uwsgi.sh",
            "gunicorn": "_gunicorn.sh",
            "command": "_cmd.sh",
        }
        cmd_file = "{}/{}{}".format(self._script_path, project_conf["pjname"], cmd_file_map[project_conf["stype"]])
        if project_conf["stype"] == "uwsgi":
            data = public.readFile(cmd_file)
            if data and "--pidfile" not in data:
                os.remove(cmd_file)
        return cmd_file

    @staticmethod
    def get_project_pids(pid):
        """
            @name 获取项目进程pid列表
            @author baozi<2021-08-10>
            @param pid: int 主进程pid
            @return list
        """
        try:
            p = psutil.Process(pid)
            return [p.pid] + [c.pid for c in p.children(recursive=True) if p.status() != psutil.STATUS_ZOMBIE]
        except:
            return []

    def get_project_run_state(self, project_name):
        '''
            @name 获取项目运行状态
            @author hwliang<2021-08-12>
            @param project_name<string> 项目名称
            @return bool
        '''
        pid_file = "{}/{}.pid".format(self._pid_path, project_name)
        pid = public.readFile(pid_file)
        project_data = self.get_project_find(project_name)
        if isinstance(pid, str):
            try:
                pid = int(pid)
                psutil.Process(pid)
            except:
                pid = self._get_pid_by_env_name(project_data)
                if not pid:
                    pid = self._get_pid_by_command(project_data)
        else:
            pid = self._get_pid_by_env_name(project_data)
            if not pid:
                pid = self._get_pid_by_command(project_data)

        if not pid:
            return []

        pids = self.get_project_pids(pid=pid)
        if not pids:
            return []
        return pids

    @staticmethod
    def other_service_pids(project_data: dict) -> Set[int]:
        from mod.project.python.serviceMod import ServiceManager
        s_mgr = ServiceManager(project_data["name"], project_data["project_config"])
        return s_mgr.other_service_pids()

    def _get_pid_by_command(self, project_data: dict) -> Optional[int]:
        project_config = project_data["project_config"]
        v_path = project_config['vpath']
        runfile = project_config['rfile']
        path = project_config['path']
        stype = project_config["stype"]
        pids = []
        try:
            if stype == "python":
                for i in psutil.process_iter(['pid', 'exe', 'cmdline']):
                    try:
                        if i.status() == "zombie":
                            continue
                        if v_path in i.exe() and runfile in " ".join(i.cmdline()):
                            pids.append(i.pid)
                    except:
                        pass

            elif stype in ("uwsgi", "gunicorn"):
                for i in psutil.process_iter(['pid', 'exe', 'cmdline']):
                    try:
                        if i.status() == "zombie":
                            continue
                        if v_path in i.exe() and stype in i.exe() and \
                                path in " ".join(i.cmdline()) and stype in " ".join(i.cmdline()):
                            pids.append(i.pid)
                    except:
                        pass
            elif stype == "command":
                for i in psutil.process_iter(['pid', 'exe']):
                    try:
                        if i.status() == "zombie":
                            continue
                        if v_path in i.exe() and i.cwd().startswith(path.rstrip("/")):
                            pids.append(i.pid)
                    except:
                        pass
            else:
                return None
        except:
            return None

        running_pid = []
        other_service_pids = self.other_service_pids(project_data)
        for pid in pids:
            if pid in psutil.pids() and pid not in other_service_pids:
                running_pid.append(pid)

        if len(running_pid) == 1:
            pid_file = "{}/{}.pid".format(self._pid_path, project_data["name"])
            public.writeFile(pid_file, str(running_pid[0]))
            return running_pid[0]

        main_pid = []
        for pid in running_pid:
            try:
                p = psutil.Process(pid)
                if p.ppid() not in running_pid:
                    main_pid.append(pid)
            except:
                pass

        if len(main_pid) == 1:
            pid_file = "{}/{}.pid".format(self._pid_path, project_data["name"])
            public.writeFile(pid_file, str(main_pid[0]))
            return main_pid[0]

        return None

    def _get_pid_by_env_name(self, project_data: dict):
        env_key = "BT_PYTHON_SERVICE_SID={}".format(public.Md5(project_data["name"]))
        pid_file = "{}/{}.pid".format(self._pid_path, project_data["name"])
        target_list = []
        for p in psutil.pids():
            try:
                data: str = public.readFile("/proc/{}/environ".format(p))
                if data.rfind(env_key) != -1:
                    target_list.append(p)
            except:
                continue

        main_pid = 0
        for i in target_list:
            try:
                p = psutil.Process(i)
                if p.ppid() not in target_list:
                    main_pid = i
            except:
                continue
        if main_pid:
            public.writeFile(pid_file, str(main_pid))
            return main_pid

        return None

    def __start_project(self, project_conf, reconstruction=False):
        """启动 项目
        @author baozi <202-02-22>
        @param:
            project_conf  ( dict ):  站点配置
            reconstruction  ( bool ):  是否重写启动指令
        @return  bool : 是否启动成功
        """
        if self.get_project_run_state(project_name=project_conf["pjname"]):
            return True
        uwsgi_file = "{}/uwsgi.ini".format(project_conf['path'])
        gconf_file = "{}/gunicorn_conf.py".format(project_conf['path'])
        cmd_file = self._get_cmd_file(project_conf)
        if not os.path.exists(cmd_file) or not os.path.exists(uwsgi_file) or not os.path.exists(gconf_file):
            self.__prepare_start_conf(project_conf)
        pid_file = "{}/{}.pid".format(self._pid_path, project_conf["pjname"])
        if os.path.exists(pid_file):
            os.remove(pid_file)
        run_user = project_conf["user"]
        public.ExecShell("chown -R {}:{} {}".format(run_user, run_user, project_conf["path"]))
        public.set_mode(cmd_file, 755)
        public.set_mode(self._pid_path, 777)
        public.set_own(cmd_file, run_user)

        # 处理日志文件
        log_file = self._project_logfile(project_conf)
        if not os.path.exists(log_file):
            public.ExecShell("touch  {}".format(log_file))
        public.ExecShell("chown  {}:{} {}".format(run_user, run_user, log_file))
        self._pass_dir_for_user(os.path.dirname(log_file), run_user)  # 让进程至少可以访问到日志文件
        self._pass_dir_for_user(os.path.dirname(project_conf["path"]), run_user)  # 让进程至少可以访问到程序文件

        # 执行脚本文件
        if project_conf["stype"] in ("uwsgi", "gunicorn"):
            res = public.ExecShell("{}".format(cmd_file), env=os.environ.copy())
        else:
            res = public.ExecShell("{}".format(cmd_file), user=run_user, env=os.environ.copy())
        time.sleep(1)

        if self._pids:
            self._pids = None  # 清理缓存重新检查
        if self.get_project_run_state(project_name=project_conf["pjname"]):
            return True
        return False

    def only_start_main_project(self, project_name):
        """启动项目api接口
        @author baozi <202-02-22>
        @param:
            get  ( dict ):  请求信息，包含name
        @return   msg: 启动情况信息
        """
        project_conf = self._get_project_conf(name_id=project_name)
        if not project_conf:
            return public.returnMsg(False, "没有该项目，请尝试刷新页面")
        if self.prep_status(project_conf) == "running":
            return public.returnMsg(False, "项目环境安装制作中.....<br>请勿操作")
        if "port" in project_conf and project_conf["port"]:
            flag, msg = self._check_port(project_conf["port"])
            if not flag:
                return public.returnMsg(False, msg)
        if not os.path.exists(project_conf["path"]):
            return public.returnMsg(False, "项目文件丢失，无法启动")
        flag = self.__start_project(project_conf)
        pdata = {
            "project_config": json.dumps(project_conf)
        }
        public.M('sites').where('name=?', (project_name,)).update(pdata)
        if flag:
            self.start_by_user(self.get_project_find(project_name)["id"])
            return public.returnMsg(True, "项目启动成功")
        else:
            return public.returnMsg(False, "项目启动失败")

    def StartProject(self, get):
        project_name = None
        if hasattr(get, "name"):
            project_name = get.name.strip()
        if hasattr(get, "project_name"):
            project_name = get.project_name.strip()
        if not project_name:
            return public.returnMsg(False, "请选择要启动的项目")

        project_find = self.get_project_find(project_name)
        if not project_find:
            return public.returnMsg(False, "没有该项目，请尝试刷新页面后重试")
        # 2024.4.3 修复项目过期时间判断不对
        mEdate = time.strftime('%Y-%m-%d', time.localtime())
        if project_find['edate'] != "0000-00-00" and project_find['edate'] < mEdate:
            return public.return_error('当前项目已过期，请重新设置项目到期时间')

        from mod.project.python.serviceMod import ServiceManager

        s_mgr = ServiceManager.new_mgr(project_name)
        if isinstance(s_mgr, str):
            return public.returnMsg(False, s_mgr)

        s_mgr.start_project()
        return public.returnMsg(True, "启动指令已执行，请注意查看日志")

    def start_project(self, get):
        get.name = get.project_name
        return self.StartProject(get)

    def __stop_project(self, project_conf, reconstruction=False):
        """停止项目
        @author baozi <202-02-22>
        @param:
            project_conf  ( dict ):  站点配置
        @return  bool : 是否停止成功
        """
        project_name = project_conf["pjname"]
        if not self.get_project_run_state(project_name):
            return True
        pid_file = "{}/{}.pid".format(self._pid_path, project_conf["pjname"])
        pid = int(public.readFile(pid_file))
        pids = self.get_project_pids(pid=pid)
        if not pids:
            return True
        self.kill_pids(pids=pids)
        if os.path.exists(pid_file):
            os.remove(pid_file)
        return True

    @staticmethod
    def kill_pids(pids=None):
        """
            @name 结束进程列表
            @author hwliang<2021-08-10>
            @param pids: string<进程pid列表>
            @return dict
        """
        if not pids:
            return public.return_data(True, '没有进程')
        pids = sorted(pids, reverse=True)
        for i in pids:
            try:
                p = psutil.Process(i)
                p.terminate()
            except:
                pass

        for i in pids:
            try:
                p = psutil.Process(i)
                p.kill()
            except:
                pass

        return public.return_data(True, '进程已全部结束')

    def StopProject(self, get):
        project_name = None
        if hasattr(get, "name"):
            project_name = get.name.strip()
        if hasattr(get, "project_name"):
            project_name = get.project_name.strip()
        if not project_name:
            return public.returnMsg(False, "请选择要停止的项目")
        project_find = self.get_project_find(project_name)
        if not project_find:
            return public.returnMsg(False, "没有该项目，请尝试刷新页面后重试")
        # 2024.4.3 修复项目过期时间判断不对
        mEdate = time.strftime('%Y-%m-%d', time.localtime())
        if project_find['edate'] != "0000-00-00" and project_find['edate'] < mEdate:
            return public.return_error('当前项目已过期，请重新设置项目到期时间')

        from mod.project.python.serviceMod import ServiceManager

        s_mgr = ServiceManager.new_mgr(project_name)
        if isinstance(s_mgr, str):
            return public.returnMsg(False, s_mgr)

        s_mgr.stop_project()
        return public.returnMsg(True, "停止指令已执行，请注意查看日志")

    def only_stop_main_project(self, project_name):
        """停止项目的api接口
        @author baozi <202-02-22>
        @param:
            get  ( dict ):  请求信息
        @return  msg : 返回停止操作的结果
        """
        project_find = self.get_project_find(project_name)
        if not project_find:
            return public.returnMsg(False, "没有该项目，请尝试刷新页面")
        project_conf = project_find["project_config"]
        if self.prep_status(project_conf) == "running":
            return public.returnMsg(False, "项目环境安装制作中.....<br>请勿操作")
        res = self.__stop_project(project_conf)
        pdata = {
            "project_config": json.dumps(project_conf)
        }
        public.M('sites').where('name=?', (project_name,)).update(pdata)
        if res:
            self.stop_by_user(self.get_project_find(project_name)["id"])
            return public.returnMsg(True, "项目停止成功")
        else:
            return public.returnMsg(False, "项目停止失败")

    def restart_project(self, get):
        get.name = get.project_name
        return self.RestartProject(get)

    def RestartProject(self, get):
        name = get.name.strip()
        project_find = self.get_project_find(name)
        if not project_find:
            return public.returnMsg(False, "没有该项目，请尝试刷新页面后重试")
        # 2024.4.3 修复项目过期时间判断不对
        mEdate = time.strftime('%Y-%m-%d', time.localtime())
        if project_find['edate'] != "0000-00-00" and project_find['edate'] < mEdate:
            return public.return_error('当前项目已过期，请重新设置项目到期时间')
        conf = project_find["project_config"]
        if self.prep_status(conf) == "running":
            return public.returnMsg(False, "项目环境安装制作中.....<br>请勿操作")
        from mod.project.python.serviceMod import ServiceManager

        s_mgr = ServiceManager.new_mgr(name)
        if isinstance(s_mgr, str):
            return public.returnMsg(False, s_mgr)

        s_mgr.stop_project()
        s_mgr.start_project()
        return public.returnMsg(True, "项目重启指令已执行，请注意查看日志")

    def stop_project(self, get):
        get.name = get.project_name
        return self.StopProject(get)

    def remove_project(self, get):
        get.name = get.project_name
        get.remove_env = True
        return self.RemoveProject(get)

    def RemoveProject(self, get):
        """删除项目接口
        @author baozi <202-02-22>
        @param:
            get  ( dict ):  请求信息对象
        @return  msg : 是否删除成功
        """
        name = get.name.strip()
        project = self.get_project_find(name)
        if not project:
            return public.returnMsg(False, "没有该项目，请尝试刷新页面")
        conf = project["project_config"]
        if not conf:
            return public.returnMsg(False, "没有该项目，请尝试刷新页面")
        if self.prep_status(conf) == "running":
            return public.returnMsg(False, "项目环境安装制作中.....<br>请勿操作")
        pid = self.get_project_run_state(name)
        if pid:
            self.StopProject(get)

        self.del_crontab(name)
        self.remove_redirect_by_project_name(get.name)
        self.clear_config(get.name)
        logfile = self._logs_path + "/%s.log" % conf["pjname"]
        # if hasattr(get, "remove_env") and get.remove_env not in (1, "1", "true", True):
        #     if os.path.basename(conf["vpath"]).find(project["name"]) == -1:
        #         try:
        #             shutil.move(conf["vpath"], self._pyv_path + '/' + project["name"] + "_venv")
        #         except:
        #             pass
        # elif os.path.exists(conf["vpath"]) and self._check_venv_path(conf["vpath"], project["id"]):
        #     shutil.rmtree(conf["vpath"])

        try:
            em = EnvironmentManager()
            python_bin = conf.get("python_bin", "")
            if not python_bin:
                python_bin_data = em.get_env_py_path(conf["vpath"])
                if python_bin_data:
                    python_bin = python_bin_data.bin_path
            if python_bin:
                em.multi_remove_env(python_bin)
        except Exception as e:
            pass

        if os.path.exists(logfile):
            os.remove(logfile)
        if os.path.exists(conf["path"] + "/uwsgi.ini"):
            os.remove(conf["path"] + "/uwsgi.ini")
        if os.path.exists(conf["path"] + "/gunicorn_conf.py"):
            os.remove(conf["path"] + "/gunicorn_conf.py")

        for suffix in ("_python.sh", "_uwsgi.sh", "_gunicorn.sh", "_cmd.sh"):
            cmd_file = os.path.join("{}/{}{}".format(self._script_path, conf["pjname"], suffix))
            if os.path.exists(cmd_file):
                os.remove(cmd_file)
        from mod.base.web_conf import remove_sites_service_config
        remove_sites_service_config(get.name, "python_")
        public.M('domain').where('pid=?', (project['id'],)).delete()
        public.M('sites').where('name=?', (name,)).delete()
        public.WriteLog(self._log_name, '删除Python项目{}'.format(name))
        return public.returnMsg(True, "删除成功")

    @staticmethod
    def _check_venv_path(v_path: str, project_id) -> bool:
        site_list = public.M('sites').where('project_type=?', ('Python',)).select()
        if not isinstance(site_list, list):
            return True
        for site in site_list:
            conf = json.loads(site["project_config"])
            if conf["vpath"] == v_path and site["id"] != project_id:
                return False
        return True

    @staticmethod
    def xsssec(text):
        return text.replace('<', '&lt;').replace('>', '&gt;')

    @staticmethod
    def last_lines(filename, lines=1):
        block_size = 3145928
        block = ''
        nl_count = 0
        start = 0
        fsock = open(filename, 'rU')
        try:
            fsock.seek(0, 2)
            curpos = fsock.tell()
            while (curpos > 0):
                curpos -= (block_size + len(block))
                if curpos < 0: curpos = 0
                fsock.seek(curpos)
                try:
                    block = fsock.read()
                except:
                    continue
                nl_count = block.count('\n')
                if nl_count >= lines: break
            for n in range(nl_count - lines + 1):
                start = block.find('\n', start) + 1
        finally:
            fsock.close()
        return block[start:]

    @staticmethod
    def _project_logfile(project_conf):
        if project_conf["stype"] in ("python", "command"):
            log_file = project_conf["logpath"] + "/error.log"
        elif project_conf["stype"] == "gunicorn":
            log_file = project_conf["logpath"] + "/gunicorn_error.log"
        else:
            log_file = project_conf["logpath"] + "/uwsgi.log"
        return log_file

    def GetProjectLog(self, get):
        """获取项目日志api
        @author baozi <202-02-22>
        @param:
            get  ( dict ):  请求信息，需要包含项目名称
        @return  msg : 日志信息
        """
        project_conf = self._get_project_conf(get.name.strip())
        if not project_conf: return public.returnMsg(False, '项目不存在')
        log_file = self._project_logfile(project_conf)
        if not os.path.exists(log_file):
            return public.returnMsg(False, '日志文件不存在')
        log_file_size = os.path.getsize(log_file)
        if log_file_size > 3145928:
            return {"status": True, "path": log_file, "data": self.xsssec(self.last_lines(log_file, 3000)),
                    "size": public.to_size(log_file_size)}
        return {"status": True, "path": log_file, "data": self.xsssec(public.GetNumLines(log_file, 3000)),
                "size": public.to_size(log_file_size)}

    # def GetPythonInstallLog(self, get):
    #     log_file = f"{self._logs_path}/py.log"
    #     if not os.path.exists(log_file): return public.returnMsg(False, '日志文件不存在')
    #     if os.path.getsize(log_file) > 3145928:
    #         return public.returnMsg(True, self.xsssec(self.last_lines(log_file, 3000)))
    #     return public.returnMsg(True, self.xsssec(public.GetNumLines(log_file, 3000)))
    #
    # def GetProjectCreateLog(self, get):
    #     name = get.name.strip()
    #     log_file = f"{self._logs_path}/{name}.log"
    #     if not os.path.exists(log_file): return public.returnMsg(False, '日志文件不存在')
    #     if os.path.getsize(log_file) > 3145928:
    #         return public.returnMsg(True, self.xsssec(self.last_lines(log_file, 3000)))
    #     return public.returnMsg(True, self.xsssec(public.GetNumLines(log_file, 3000)))

    def GetProjectList(self, get):
        """获取项目列表
        @author baozi <202-02-22>
        @param:
            get  ( dict ):  请求信息
        @return  msg : _description_
        """
        if not self.need_update_project("mod"):
            self.update_all_project()
        if not 'p' in get:  get.p = 1
        if not 'limit' in get: get.limit = 20
        if not 'callback' in get: get.callback = ''
        if not 'order' in get: get.order = 'id desc'
        type_id = None
        if "type_id" in get:
            try:
                type_id = int(get.type_id)
            except:
                type_id = None

        if 'search' in get:
            get.project_name = get.search.strip()
            search = "%{}%".format(get.project_name)
            if type_id is None:
                count = public.M('sites').where('project_type=? AND (name LIKE ? OR ps LIKE ?)', ('Python', search, search)).count()
                data = public.get_page(count, int(get.p), int(get.limit), get.callback)
                data['data'] = public.M('sites').where('project_type=? AND (name LIKE ? OR ps LIKE ?)', ('Python', search, search)).limit(data['shift'] + ',' + data['row']).order(get.order).select()
            else:
                count = public.M('sites').where('project_type=? AND (name LIKE ? OR ps LIKE ?) AND type_id = ?',
                                                ('Python', search, search, type_id)).count()
                data = public.get_page(count, int(get.p), int(get.limit), get.callback)
                data['data'] = public.M('sites').where('project_type=? AND (name LIKE ? OR ps LIKE ?) AND type_id = ?', ('Python', search, search, type_id)).limit(data['shift'] + ',' + data['row']).order(get.order).select()
        else:
            if type_id is None:
                count = public.M('sites').where('project_type=?', 'Python').count()
                data = public.get_page(count, int(get.p), int(get.limit), get.callback)
                data['data'] = public.M('sites').where('project_type=?', 'Python').limit(data['shift'] + ',' + data['row']).order(get.order).select()
            else:
                count = public.M('sites').where('project_type=? AND type_id = ?', ('Python', type_id)).count()
                data = public.get_page(count, int(get.p), int(get.limit), get.callback)
                data['data'] = public.M('sites').where('project_type=? AND type_id = ?', ('Python', type_id)).limit(data['shift'] + ',' + data['row']).order(get.order).select()

        if isinstance(data["data"], str) and data["data"].startswith("error"):
            raise public.PanelError("数据库查询错误：" + data["data"])

        for i in range(len(data['data'])):
            data['data'][i]["ssl"] = self.get_ssl_end_date(data['data'][i]["name"])
            self._get_project_state(data['data'][i])
        return data

    def _get_project_state(self, project_info):
        """获取项目详情信息
        @author baozi <202-02-22>
        @param:
            project_info  ( dict ):  项目详情
        @return   : 项目详情的列表
        """
        if not isinstance(project_info['project_config'], dict):
            project_info['project_config'] = json.loads(project_info['project_config'])

        pyenv = self.environment_manager.get_env_py_path(
            project_info['project_config'].get("python_bin", project_info['project_config']["vpath"])
        )
        if pyenv:
            project_info["shell_active"] = self.get_active_shell(project_info["name"], pyenv)
            project_info["pyenv_data"] = pyenv.to_dict()
        else:
            project_info["shell_active"] = ""
            project_info["pyenv_data"] = {}

        project_info["project_config"]["prep_status"] = self.prep_status(project_info['project_config'])
        if project_info["project_config"]["stype"] == "python":
            project_info["config_file"] = None
        elif project_info["project_config"]["stype"] == "uwsgi":
            project_info["config_file"] = '{}/uwsgi.ini'.format(project_info["project_config"]["path"])
        else:
            project_info["config_file"] = '{}/gunicorn_conf.py'.format(project_info["project_config"]["path"])
        pids = self.get_project_run_state(project_info["name"])
        if not pids:
            project_info['run'], project_info['status'], project_info["project_config"]["status"] = False, 0, 0
            project_info["listen"] = []
        else:
            project_info['run'], project_info['status'], project_info["project_config"]["status"] = True, 1, 1
            mem, cpu = self.get_mem_and_cpu(pids)
            project_info.update({"cpu": cpu, "mem": mem})
            project_info["listen"] = self._list_listen(pids)
        project_info["pids"] = pids
        for i in ("start_sh", "stop_sh", "check_sh"):
            if i in project_info["project_config"]:
                project_info["project_config"].pop(i)

    def get_active_shell(self, p_name, pyenv) -> str:
        pyenv.use2project(p_name)
        env_file = os.path.join(self._env_path, "{}.env".format(p_name))
        evn_sh = "\nsource {}\n".format(env_file)
        if pyenv.env_type == "conda":
            public.writeFile("{}/{}.sh".format(self._activate_path, p_name), pyenv.activate_shell() + evn_sh)
        else:
            return "unset _BT_PROJECT_ENV && source /www/server/panel/script/btpyprojectenv.sh {} {}".format(p_name, evn_sh)
        return "source {}/{}.sh".format(self._activate_path, p_name)


    @staticmethod
    def _list_listen(pids: List[int]) -> List[int]:
        res = set()
        try:
            for i in pids:
                p = psutil.Process(i)
                for conn in p.connections():
                    if conn.status == "LISTEN":
                        res.add(conn.laddr.port)
        except:
            pass
        return list(res)

    # def GetProjectConf(self, get):
    #     """获取项目配置信息
    #     @author baozi <202-02-22>
    #     @param:
    #         get  ( dict ):  请求信息，站点名称name
    #     @return  可修改项目  uwsgi: rfile, processes, threads, is_http, port, user, logpath, other
    #                         gunicorn: rfile, processes, threads, port, user, logpath, loglevel, other
    #     """
    #     project_conf = self._get_project_conf(get.name.strip())
    #     if not project_conf:
    #         return public.return_error('项目不存在')
    #     res_data = {
    #         "rfile": project_conf["rfile"],
    #         "xsgi": project_conf["xsgi"],
    #         "processes": project_conf["processes"] if "processes" in project_conf else 4,
    #         "threads": project_conf["threads"] if "threads" in project_conf else 2,
    #         "port": project_conf["port"],
    #         "user": project_conf["user"],
    #         "logpath": project_conf["logpath"],
    #         "stype": project_conf["stype"],
    #         "is_http": project_conf["is_http"] if "is_http" in project_conf else True,
    #         "loglevel": project_conf["loglevel"] if "loglevel" in project_conf else 'info'
    #     }
    #     return res_data

    def ChangeProjectConf(self, get):
        """修改项目配置信息
        @author baozi <202-02-22>
        @param:
            get  ( dict ):  用户请求信息 包含name，data
        @return
        """
        conf = self._get_project_conf(get.name.strip())
        if not conf:
            return public.returnMsg("没有该项目")
        if self.prep_status(conf) == "running":
            return public.returnMsg(False, "项目环境安装制作中.....<br>请勿操作")
        if not os.path.exists(conf["path"]):
            return public.returnMsg(False, "项目文件丢失，请尝试移除本项目，重新建立")
        data: dict = get.data

        change_values = {}
        if "call_app" in data and data["call_app"] != conf["call_app"]:
            conf["call_app"] = data["call_app"]
            change_values["call_app"] = data["call_app"]

        try:
            if "env_list" in data and isinstance(data["env_list"], str):
                conf["env_list"] = json.loads(data["env_list"])
        except:
            return public.returnMsg(False, "环境变量格式错误")

        if "env_list" in data and isinstance(data["env_list"], list):
            conf["env_list"] = data["env_list"]

        if "env_file" in data and isinstance(data["env_file"], str) and data["env_file"] != conf["env_file"]:
            conf["env_file"] = data["env_file"]

        # stype
        if "stype" in data and data["stype"] != conf["stype"]:
            if data["stype"] not in ("uwsgi", "gunicorn", "python", "command"):
                return public.returnMsg(False, "启动方式选择错误")
            else:
                self.__stop_project(conf)
                conf["stype"] = data["stype"]
        if "xsgi" in data and data["xsgi"] != conf["xsgi"]:
            if data["xsgi"] not in ("wsgi", "asgi"):
                return public.returnMsg(False, "网络协议选择错误")
            else:
                conf["xsgi"] = data["stype"]
                change_values["xsgi"] = data["stype"]
        # 检查服务器部署的可行性
        msg = self.__check_feasibility(conf)
        if msg: return public.returnMsg(False, msg)
        # rfile
        if "rfile" in data and data["rfile"] != conf["rfile"]:
            if not data["rfile"].startswith(conf["path"]):
                return public.returnMsg(False, "启动文件不在项目目录下")
            change_values["rfile"] = data["rfile"]
            conf["rfile"] = data["rfile"]
        # parm
        if conf["stype"] == "python":
            conf["parm"] = data["parm"] if "parm" in data else conf["parm"]
        # project_cmd
        if conf["stype"] == "command":
            project_cmd = conf.get("project_cmd", "")
            if "project_cmd" in data:
                project_cmd = data.get("project_cmd", "")
            if not project_cmd:
                return public.returnMsg(False, "没有自定义启动命令")
            else:
                conf["project_cmd"] = project_cmd

        # processes and threads
        try:
            if "processes" in data and int(data["processes"]) != int(conf["processes"]):
                change_values["processes"], conf["processes"] = int(data["processes"]), int(data["processes"])
            if "threads" in data and int(data["threads"]) != int(conf["threads"]):
                change_values["threads"], conf["threads"] = int(data["threads"]), int(data["threads"])
        except ValueError:
            return public.returnMsg(False, "线程或进程数设置有误")

        # port 某些情况下可以关闭
        if "port" in data and data["port"] != conf["port"] and data["port"]:
            # flag, msg = self._check_port(data["port"])
            # if not flag:
            #     return public.returnMsg(False, msg)
            change_values["port"] = data["port"]
            conf["port"] = data["port"]

        # user
        if "user" in data and data["user"] != conf["user"]:
            if data["user"] in self.get_system_user_list():
                change_values["user"] = data["user"]
                conf["user"] = data["user"]

        # auto_run
        if "auto_run" in data and data["auto_run"] != conf["auto_run"]:
            if isinstance(data["auto_run"], bool):
                conf["auto_run"] = data["auto_run"]
        # logpath
        if "logpath" in data and data["logpath"].strip() and data["logpath"] != conf["logpath"]:
            data["logpath"] = data["logpath"].rstrip("/")
            if os.path.isfile(data["logpath"]):
                return public.returnMsg(False, "日志路径不应当是一个文件")
            if '\n' in data["logpath"].strip():
                return public.returnMsg(False, "日志路径不能包含换行")
            change_values["logpath"] = data["logpath"]
            conf["logpath"] = data["logpath"]

        # 特殊 uwsgi和gunicorn 不需要修改启动的脚本，只需要修改配置文件
        if conf["stype"] == "gunicorn":
            if "loglevel" in data and data["loglevel"] != conf["loglevel"]:
                if data["loglevel"] in ("debug", "info", "warning", "error", "critical"):
                    change_values["loglevel"] = data["loglevel"]
                    conf["loglevel"] = data["loglevel"]
            config_file = public.readFile(conf["path"] + "/gunicorn_conf.py")
            if config_file:
                config_file = self.__change_gunicorn_config_to_file(change_values, config_file)
                public.writeFile(conf["path"] + "/gunicorn_conf.py", config_file)

        if conf["stype"] == "uwsgi":
            if "is_http" in data and isinstance(data["is_http"], bool):
                change_values["is_http"] = data["is_http"]
                conf["is_http"] = data["is_http"]
            if "port" not in change_values:
                change_values["port"] = conf["port"]
            config_file = public.readFile(conf["path"] + "/uwsgi.ini")
            if config_file:
                config_file = self.__change_uwsgi_config_to_file(change_values, config_file)
                public.writeFile(conf["path"] + "/uwsgi.ini", config_file)

        self.__prepare_start_conf(conf, force=True)

        # 尝试重启项目
        msg = ''
        if not self.__stop_project(conf, reconstruction=True):
            msg = "修改成功，但尝试重启时，项目停止失败"
        if not self.__start_project(conf, reconstruction=True):
            msg = "修改成功，但尝试重启时，项目启动失败"

        pdata = {
            "project_config": json.dumps(conf)
        }
        public.M('sites').where('name=?', (get.name.strip(),)).update(pdata)
        public.WriteLog(self._log_name, 'Python项目{}, 修改了启动配置项'.format(get.name.strip()))

        if msg:
            return public.returnMsg(False, msg)

        return public.returnMsg(True, "修改成功")

    @staticmethod
    def __change_uwsgi_config_to_file(changes, config_file):
        """修改配置信息
        @author baozi <202-03-08>
        @param:
            changes  ( dict ):  改变的项和值
            config_file  ( string ):  需要改变的文件
        @return
        """
        reps = {
            "rfile": (r'wsgi-file\s{0,3}=\s{0,3}[^#\n]*\n', lambda x: f"wsgi-file={x.strip()}\n"),
            "processes": (r'processes\s{0,3}=\s{0,3}[\d]*\n', lambda x: f"processes={x.strip()}\n"),
            "threads": (r'threads\s{0,3}=\s{0,3}[\d]*\n', lambda x: f"threads={x.strip()}\n"),
            "user": (
                r'uid\s{0,3}=\s{0,3}[^\n]*\ngid\s{0,3}=\s{0,3}[^\n]*\n',
                lambda x: f"uid={x.strip()}\ngid={x.strip()}\n"
            ),
            "logpath": (r'daemonize\s{0,3}=\s{0,3}.*\n', lambda x: f"daemonize={x.strip().rstrip('/')}/uwsgi.log\n"),
            "call_app": (r'callable\s*=\s{0,3}.*\n', lambda x: f"callable={x.strip()}\n")
        }
        if "logpath" in changes and not os.path.exists(changes['logpath']):
            os.makedirs(changes['logpath'], mode=0o777)
        for k, (rep, fun) in reps.items():
            if k not in changes: continue
            config_file = re.sub(rep, fun(str(changes[k])), config_file)

        if "port" in changes:
            # 被用户关闭了预设的通信方式
            if config_file.find("\n#http") != -1 and config_file.find("\n#socket") != -1:
                pass
            elif "is_http" in changes:
                # 按照预设的方式修改
                rep = r"\n#?http\s{0,3}=\s{0,3}((\d{0,3}\.){3}\d{0,3})?:\d{2,5}\n#?socket\s{0,3}=\s{0,3}((\d{0,3}\.){3}\d{0,3})?:\d{2,5}\n"
                is_http, is_socket = ("", "#") if changes["is_http"] else ("#", "")
                new = "\n{is_http}http=0.0.0.0:{port}\n{is_socket}socket=0.0.0.0:{port}\n".format(
                    is_http=is_http, port=changes["port"], is_socket=is_socket)
                config_file = re.sub(rep, new, config_file)
            else:
                rpe_h = r'http\s{0,3}=\s{0,3}((\d{0,3}\.){3}\d{0,3})?:\d{2,5}\n'
                config_file = re.sub(rpe_h, f"http=0.0.0.0:{changes['port']}\n", config_file)
                rpe_s = r'socket\s{0,3}=\s{0,3}((\d{0,3}\.){3}\d{0,3})?:\d{2,5}\n'
                config_file = re.sub(rpe_s, f"socket=0.0.0.0:{changes['port']}\n", config_file)

        return config_file

    @staticmethod
    def __prevent_re(test_str):
        # 防正则转译
        re_char = ['$', '(', ')', '*', '+', '.', '[', ']', '{', '}', '?', '^', '|', '\\']
        res = ""
        for i in test_str:
            if i in re_char:
                res += "\\" + i
            else:
                res += i
        return res

    def __get_uwsgi_config_from_file(self, config_file, conf):
        """检查并从修改的配置信息获取必要信息
        @author baozi <202-03-08>
        @param:
            changes  ( dict ):  改变的项和值
            config_file  ( string ):  需要改变的文件
        @return
        """
        # 检查必要项目
        check_reps = [
            (r"\n\s?chdir\s{0,3}=\s{0,3}" + self.__prevent_re(conf["path"]) + r"[^\n]*\n", "不能修改项目路径"),
            (r"\n\s?pidfile\s{0,3}=\s{0,3}" + self.__prevent_re(conf["path"] + "/uwsgi.pid") + r"[^\n]*\n",
             "不能修改项目的pidfile文件位置"),
            (r"\n\s?master\s{0,3}=\s{0,3}true[^\n]*\n", "不能修改主进程相关配置"),
        ]
        for rep, msg in check_reps:
            if not re.search(rep, config_file):
                return False, msg

        get_reps = {
            "rfile": (r'\n\s?wsgi-file\s{0,3}=\s{0,3}(?P<target>[^#\n]*)\n', None),
            "module": (r'\n\s?module\s{0,3}=\s{0,3}(?P<target>[^\n/:])*:[^\n]*\n', None),
            "processes": (r'\n\s?processes\s{0,3}=\s{0,3}(?P<target>[\d]*)\n', None),
            "threads": (r'\n\s?threads\s{0,3}=\s{0,3}(?P<target>[\d]*)\n', None),
            "logpath": (
                r'\n\s?daemonize\s{0,3}=\s{0,3}(?P<target>[^\n]*)\n', "没有检查到。配置项：日志路径，请注意您的修改")
        }
        changes = {}
        for k, (rep, msg) in get_reps.items():
            res = re.search(rep, config_file)
            if not res and msg:
                return False, msg
            elif res:
                changes[k] = res.group("target").strip()
        if "module" in changes:
            _rfile = conf["path"] + changes["module"].replace(".", "/") + ".py"
            if os.path.isfile(_rfile):
                changes["rfile"] = _rfile
            changes.pop("module")

        if "logpath" in changes:
            if not os.path.exists(changes['logpath']):
                os.makedirs(changes['logpath'], mode=0o777)
            if "/" in changes["logpath"]:
                _path, filename = changes["logpath"].rsplit("/", 1)
                if filename != "uwsgi.log":
                    return False, "为方便日志管理，日志文件名称请使用 uwsgi.log "
                else:
                    changes["logpath"] = _path
            else:
                if changes["logpath"] != "uwsgi.log":
                    return False, "为方便日志管理，日志文件名称请使用 uwsgi.log"
                else:
                    changes["logpath"] = conf["path"]

        # port 相关查询
        rep_h = r'\n\s{0,3}http\s{0,3}=\s{0,3}((\d{0,3}\.){3}\d{0,3})?:(?P<target>\d{2,5})[^\n]*\n'
        rep_s = r'\n\s{0,3}socket\s{0,3}=\s{0,3}((\d{0,3}\.){3}\d{0,3})?:(?P<target>\d{2,5})[^\n]*\n'
        res_http = re.search(rep_h, config_file)
        res_socket = re.search(rep_s, config_file)
        if res_http:
            changes["port"] = res_http.group("target").strip()
        elif res_socket:
            changes["port"] = res_socket.group("target").strip()
        else:
            # 被用户关闭了预设的通信方式
            changes["port"] = ""

        return True, changes

    @staticmethod
    def __change_gunicorn_config_to_file(changes, config_file):
        """修改配置信息
        @author baozi <202-03-08>
        @param:
            changes  ( dict ):  改变的项和值
            config_file  ( string ):  需要改变的文件
        @return
        """
        reps = {
            "processes": (r'workers\s{0,3}=\s{0,3}[^\n]*\n', lambda x: f"workers = {x.strip()}\n"),
            "threads": (r'threads\s{0,3}=\s{0,3}[\d]*\n', lambda x: f"threads = {x.strip()}\n"),
            "user": (r'user\s{0,3}=\s{0,3}[^\n]*\n', lambda x: f"user = '{x.strip()}'\n"),
            "loglevel": (r'loglevel\s{0,3}=\s{0,3}[^\n]*\n', lambda x: f"loglevel = '{x.strip()}'\n"),
            "port": (r'bind\s{0,3}=\s{0,3}[^\n]*\n', lambda x: f"bind = '0.0.0.0:{x.strip()}'\n"),
        }
        for k, (rep, fun) in reps.items():
            if k not in changes: continue
            config_file = re.sub(rep, fun(str(changes[k])), config_file)
        if "logpath" in changes:
            if not os.path.exists(changes['logpath']):
                os.makedirs(changes['logpath'], mode=0o777)
            rpe_accesslog = r'''accesslog\s{0,3}=\s{0,3}['"](/[^/\n]*)*['"]\n'''
            config_file = re.sub(rpe_accesslog,
                                 "accesslog = '{}/gunicorn_acess.log'\n".format(changes['logpath']),
                                 config_file)
            rpe_errorlog = r'''errorlog\s{0,3}=\s{0,3}['"](/[^/\n]*)*['"]\n'''
            config_file = re.sub(rpe_errorlog,
                                 "errorlog = '{}/gunicorn_error.log'\n".format(changes['logpath']),
                                 config_file)

        return config_file

    def __get_gunicorn_config_from_file(self, config_file, conf):
        """修改配置信息
        @author baozi <202-03-08>
        @param:
            config_file  ( dict ):  被改变的文件
            conf  ( string ):  项目原配置
        @return
        """
        # 检查必要项目
        check_reps = [
            (r'''\n\s?chdir ?= ?["']''' + self.__prevent_re(conf["path"]) + '''["']\n''', "请不要修改项目路径"),
            (r'''\n\s?pidfile\s{0,3}=\s{0,3}['"]''' + self.__prevent_re(
                conf["path"] + "/gunicorn.pid") + r'''['"][^\n]*\n''',
             "不能修改项目的pidfile文件位置,这将导致我们无法准确监控项目运行情况"),
            (r'''\n\s?worker_class\s{0,3}=\s{0,3}((['"]sync['"])|(['"]uvicorn\.workers\.UvicornWorker['"]))[^\n]*\n''',
             "请不要修改worker_class相关配置"),
        ]
        for rep, msg in check_reps:
            if not re.findall(rep, config_file):
                return False, msg

        get_reps = {
            "port": (r'''\n\s?bind\s{0,3}=\s{0,3}['"]((\d{0,3}\.){3}\d{0,3})?:(?P<target>\d{2,5})['"][^\n]*\n''',
                     "没有检查到配置项：bind，请注意您的修改"),
            "processes": (r'\n\s?workers\s{0,3}=\s{0,3}(?P<target>[^\n]*)[^\n]*\n', None),
            "threads": (r'\n\s?threads\s{0,3}=\s{0,3}(?P<target>[\d]*)[^\n]*\n', None),
            "logpath": (r'''\n\s?errorlog\s{0,3}=\s{0,3}['"](?P<target>[^"'\n]*)['"][^\n]*\n''',
                        "没有检查到配置项：日志路径，请注意您的修改"),
            "loglevel": (r'''\n\s?loglevel\s{0,3}=\s{0,3}['"](?P<target>[^'"\n]*)['"][^\n]*\n''',
                         "没有检查到配置项：日志等级，请注意您的修改")
        }
        changes: Dict[str, str] = {}
        for k, (rep, msg) in get_reps.items():
            res = re.search(rep, config_file)
            if not res and msg:
                return False, msg
            elif res:
                changes[k] = str(res.group("target").strip())

        if "logpath" in changes:
            if not os.path.exists(changes['logpath']):
                os.makedirs(changes['logpath'], mode=0o777)
            if "/" in changes["logpath"]:
                _path, filename = changes["logpath"].rsplit("/", 1)
                if filename != "gunicorn_error.log":
                    return False, "为方便日志管理，日志文件名称请使用 gunicorn_error.log"
                else:
                    changes["logpath"] = _path
            else:
                if changes["logpath"] != "gunicorn_error.log":
                    return False, "为方便日志管理，日志文件名称请使用 gunicorn_error.log"
                else:
                    changes["logpath"] = conf["path"]
            rep_accesslog = r'''\n\s?accesslog\s{0,3}=\s{0,3}['"]''' + self.__prevent_re(
                changes["logpath"] + "/gunicorn_acess.log") + r'''['"][^\n]*\n'''
            if not re.search(rep_accesslog, config_file):
                return False, "为方便日志管理, 请将错误日志(errorlog) 与 访问日志(accesslog) 放到同一文件路径下"

        if "loglevel" in changes:
            if not changes["loglevel"] in ("debug", "info", "warning", "error", "critical"):
                return False, "日志等级配置错误"
        return True, changes

    @staticmethod
    def get_ssl_end_date(project_name):
        '''
            @name 获取SSL信息
            @author hwliang<2021-08-09>
            @param project_name <string> 项目名称
            @return dict
        '''
        import data
        return data.data().get_site_ssl_info('python_{}'.format(project_name))

    def GetProjectInfo(self, get):
        """获取项目所有信息
        @author baozi <202-03-08>
        @param:
            get  ( dict ):  请求信息，站点名称name
        @return
        """
        project = self.get_project_find(get.name.strip())
        if not project:
            return public.returnMsg(False, "没该项目")
        if self.prep_status(project["project_config"]) == "running":
            return public.returnMsg(False, "项目环境安装制作中.....<br>请勿操作")
        self._get_project_state(project)
        project_conf = project["project_config"]
        if project_conf["stype"] == "python":
            return project
        project_conf["processes"] = project_conf["processes"] if "processes" in project_conf else 4
        project_conf["threads"] = project_conf["threads"] if "threads" in project_conf else 2

        if project_conf["stype"] != "python":
            project_conf["is_http"] = bool(project_conf.get("is_http", True))

        project["ssl"] = self.get_ssl_end_date(get.name.strip())
        return project

    # 取文件配置
    def GetConfFile(self, get):
        """获取项目配置文件信息
        @author baozi <202-03-08>
        @param:
            get  ( dict ):  用户请求信息 包含name
        @return 文件信息
        """
        project_conf = self._get_project_conf(get.name.strip())
        if not project_conf:
            return public.return_error('项目不存在')

        import files
        if project_conf["stype"] in ("python", "command"):
            return public.returnMsg(False, "Python或自定义命令的启动方式没有配置文件可修改")
        elif project_conf["stype"] == "gunicorn":
            get.path = project_conf["path"] + "/gunicorn_conf.py"
        else:
            get.path = project_conf["path"] + "/uwsgi.ini"
        f = files.files()
        return f.GetFileBody(get)

    # 保存文件配置
    def SaveConfFile(self, get):
        """修改项目配置文件信息
        @author baozi <202-03-08>
        @param:
            get  ( dict ):  用户请求信息 包含name,data,encoding
        @return 文件信息
        """
        project_conf = self._get_project_conf(get.name.strip())
        if not project_conf:
            return public.return_error('项目不存在')

        import files

        data = get.data
        if project_conf["stype"] == "python":
            return public.returnMsg(False, "Python启动方式没有配置文件可修改")
        elif project_conf["stype"] == "gunicorn":
            get.path = project_conf["path"] + "/gunicorn_conf.py"
            flag, changes = self.__get_gunicorn_config_from_file(data, project_conf)
            if not flag:
                return public.returnMsg(False, changes)
        else:
            get.path = project_conf["path"] + "/uwsgi.ini"
            flag, changes = self.__get_uwsgi_config_from_file(data, project_conf)
            if not flag:
                return public.returnMsg(False, changes)

        project_conf.update(changes)

        f = files.files()
        get.encoding = "utf-8"
        result = f.SaveFileBody(get)
        if not result["status"]:
            return public.returnMsg(False, "保存失败")

        # 尝试重启项目
        msg = ''
        if not self.__stop_project(project_conf, reconstruction=True):
            msg = "修改成功，但尝试重启时，项目停止失败"
        if not self.__start_project(project_conf, reconstruction=True):
            msg = "修改成功，但尝试重启时，项目启动失败"

        pdata = {
            "project_config": json.dumps(project_conf)
        }
        public.M('sites').where('name=?', (get.name.strip(),)).update(pdata)
        public.WriteLog(self._log_name, 'Python项目{}, 修改了启动配置项'.format(get.name.strip()))

        if msg:
            return public.returnMsg(False, msg)

        return public.returnMsg(True, "修改成功")

    # ———————————————————————————————————————————
    #   Nginx 与 Apache 相关的设置内容(包含SSL)  |
    # ———————————————————————————————————————————

    def exists_nginx_ssl(self, project_name):
        '''
            @name 判断项目是否配置Nginx SSL配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return tuple
        '''
        config_file = "{}/nginx/python_{}.conf".format(public.get_vhost_path(), project_name)
        if not os.path.exists(config_file):
            return False, False

        config_body = public.readFile(config_file)
        if not config_body:
            return False, False

        is_ssl, is_force_ssl = False, False
        if config_body.find('ssl_certificate') != -1:
            is_ssl = True
        if config_body.find('HTTP_TO_HTTPS_START') != -1:
            is_force_ssl = True
        return is_ssl, is_force_ssl

    def exists_apache_ssl(self, project_name):
        '''
            @name 判断项目是否配置Apache SSL配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return bool
        '''
        config_file = "{}/apache/python_{}.conf".format(public.get_vhost_path(), project_name)
        if not os.path.exists(config_file):
            return False, False

        config_body = public.readFile(config_file)
        if not config_body:
            return False, False

        is_ssl, is_force_ssl = False, False
        if config_body.find('SSLCertificateFile') != -1:
            is_ssl = True
        if config_body.find('HTTP_TO_HTTPS_START') != -1:
            is_force_ssl = True
        return is_ssl, is_force_ssl

    def set_apache_config(self, project):
        '''
            @name 设置Apache配置
            @author hwliang<2021-08-09>
            @param project: dict<项目信息>
            @return bool
        '''
        project_name = project['name']

        # 处理域名和端口
        ports = []
        domains = []
        for d in project['project_config']['domains']:
            domain_tmp = d.split(':')
            if len(domain_tmp) == 1:
                domain_tmp.append(80)
            if not int(domain_tmp[1]) in ports:
                ports.append(int(domain_tmp[1]))
            if not domain_tmp[0] in domains:
                domains.append(domain_tmp[0])

        config_file = "{}/apache/python_{}.conf".format(self._vhost_path, project_name)
        template_file = "{}/template/apache/python_http.conf".format(self._vhost_path)
        config_body = public.readFile(template_file)
        apache_config_body = ''

        # 旧的配置文件是否配置SSL
        is_ssl, is_force_ssl = self.exists_apache_ssl(project_name)
        if is_ssl:
            if not 443 in ports: ports.append(443)

        from panelSite import panelSite
        s = panelSite()

        # 根据端口列表生成配置
        for p in ports:
            # 生成SSL配置
            ssl_config = ''
            if p == 443 and is_ssl:
                ssl_key_file = "{vhost_path}/cert/{project_name}/privkey.pem".format(project_name=project_name,
                                                                                     vhost_path=public.get_vhost_path())
                if not os.path.exists(ssl_key_file): continue  # 不存在证书文件则跳过
                ssl_config = '''#SSL
    SSLEngine On
    SSLCertificateFile {vhost_path}/cert/{project_name}/fullchain.pem
    SSLCertificateKeyFile {vhost_path}/cert/{project_name}/privkey.pem
    SSLCipherSuite EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5
    SSLProtocol All -SSLv2 -SSLv3 -TLSv1
    SSLHonorCipherOrder On'''.format(project_name=project_name, vhost_path=public.get_vhost_path())
            else:
                if is_force_ssl:
                    ssl_config = '''#HTTP_TO_HTTPS_START
    <IfModule mod_rewrite.c>
        RewriteEngine on
        RewriteCond %{SERVER_PORT} !^443$
        RewriteRule (.*) https://%{SERVER_NAME}$1 [L,R=301]
    </IfModule>
    #HTTP_TO_HTTPS_END'''

            # 生成vhost主体配置
            apache_config_body += config_body.format(
                site_path=project['path'],
                server_name='{}.{}'.format(p, project_name),
                domains=' '.join(domains),
                log_path=public.get_logs_path(),
                server_admin='admin@{}'.format(project_name),
                url='http://127.0.0.1:{}'.format(project['project_config']['port']),
                port=p,
                ssl_config=ssl_config,
                project_name=project_name
            )
            apache_config_body += "\n"

            # 添加端口到主配置文件
            if p not in [80]:
                s.apacheAddPort(p)

        # 写.htaccess
        rewrite_file = "{}/.htaccess".format(project['path'])
        if not os.path.exists(rewrite_file):
            public.writeFile(rewrite_file, '# 请将伪静态规则或自定义Apache配置填写到此处\n')

        from mod.base.web_conf import ap_ext
        apache_config_body = ap_ext.set_extension_by_config(project_name, apache_config_body)
        # 写配置文件
        public.writeFile(config_file, apache_config_body)
        return True

    def set_nginx_config(self, project, is_modify=False, proxy_port=None):
        '''
            @name 设置Nginx配置
            @author hwliang<2021-08-09>
            @param project: dict<项目信息>
            @return bool
        '''
        project_name = project['name']
        ports = []
        domains = []

        for d in project['project_config']['domains']:
            domain_tmp = d.split(':')
            if len(domain_tmp) == 1: domain_tmp.append(80)
            if not int(domain_tmp[1]) in ports:
                ports.append(int(domain_tmp[1]))
            if not domain_tmp[0] in domains:
                domains.append(domain_tmp[0])
        listen_ipv6 = public.listen_ipv6()
        is_ssl, is_force_ssl = self.exists_nginx_ssl(project_name)
        listen_ports_list = []
        for p in ports:
            listen_ports_list.append("    listen {};".format(p))
            if listen_ipv6:
                listen_ports_list.append("    listen [::]:{};".format(p))

        ssl_config = ''
        if is_ssl:
            http3_header = ""
            if self.is_nginx_http3():
                http3_header = '''\n    add_header Alt-Svc 'quic=":443"; h3=":443"; h3-29=":443"; h3-27=":443";h3-25=":443"; h3-T050=":443"; h3-Q050=":443";h3-Q049=":443";h3-Q048=":443"; h3-Q046=":443"; h3-Q043=":443"';'''

            nginx_ver = public.nginx_version()
            if nginx_ver:
                port_str = ["443"]
                if listen_ipv6:
                    port_str.append("[::]:443")
                use_http2_on = False
                for p in port_str:
                    listen_str = "    listen {} ssl".format(p)
                    if nginx_ver < [1, 9, 5]:
                        listen_str += ";"
                    elif [1, 9, 5] <= nginx_ver < [1, 25, 1]:
                        listen_str += " http2;"
                    else:  # >= [1, 25, 1]
                        listen_str += ";"
                        use_http2_on = True
                    listen_ports_list.append(listen_str)

                    if self.is_nginx_http3():
                        listen_ports_list.append("    listen {} quic;".format(p))
                if use_http2_on:
                    listen_ports_list.append("    http2 on;")

            else:
                listen_ports_list.append("    listen 443 ssl;")

            ssl_config = '''ssl_certificate    {vhost_path}/cert/{priject_name}/fullchain.pem;
    ssl_certificate_key    {vhost_path}/cert/{priject_name}/privkey.pem;
    ssl_protocols TLSv1.1 TLSv1.2 TLSv1.3;
    ssl_ciphers EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    add_header Strict-Transport-Security "max-age=31536000";{http3_header}
    error_page 497  https://$host$request_uri;'''.format(vhost_path=self._vhost_path, priject_name=project_name, http3_header=http3_header)

            if is_force_ssl:
                ssl_config += '''
    #HTTP_TO_HTTPS_START
    if ($server_port !~ 443){
        rewrite ^(/.*)$ https://$host$1 permanent;
    }
    #HTTP_TO_HTTPS_END'''

        config_file = "{}/nginx/python_{}.conf".format(self._vhost_path, project_name)
        template_file = "{}/template/nginx/python_http.conf".format(self._vhost_path)
        listen_ports = "\n".join(listen_ports_list).strip()

        p_port = proxy_port if proxy_port else project['project_config']['port']

        proxy_content = "# proxy"

        if is_modify != "close" and (is_modify or project["project_config"]["stype"] != "command"):
            proxy_content = '''# proxy
    location / {{
        proxy_pass http://127.0.0.1:{p_port};
        proxy_set_header Host {host}:$server_port;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header REMOTE-HOST $remote_addr;
        add_header X-Cache $upstream_cache_status;
        proxy_set_header X-Host $host:$server_port;
        proxy_set_header X-Scheme $scheme;
        proxy_connect_timeout 30s;
        proxy_read_timeout 86400s;
        proxy_send_timeout 30s;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }}'''.format(p_port=p_port, host="127.0.0.1")

        config_body = public.readFile(template_file)
        mut_config = {
            "site_path": project['path'],
            "domains": ' '.join(domains),
            "ssl_config": ssl_config,
            "listen_ports": listen_ports,
            "proxy": proxy_content  # 添加代理内容替换
        }
        config_body = config_body.format(
            site_path=project['path'],
            domains=mut_config["domains"],
            project_name=project_name,
            panel_path=self._panel_path,
            log_path=public.get_logs_path(),
            host='127.0.0.1',
            listen_ports=listen_ports,
            ssl_config=ssl_config,
            proxy=mut_config["proxy"]  # 添加代理替换
        )

        rewrite_file = "{panel_path}/vhost/rewrite/python_{project_name}.conf".format(
            panel_path=self._panel_path, project_name=project_name)
        if not os.path.exists(rewrite_file):
            public.writeFile(rewrite_file, '# 请将伪静态规则或自定义NGINX配置填写到此处\n')
        if not os.path.exists("/www/server/panel/vhost/nginx/well-known"):
            os.makedirs("/www/server/panel/vhost/nginx/well-known", 0o600)
        apply_check = "{}/vhost/nginx/well-known/{}.conf".format(self._panel_path, project_name)
        from mod.base.web_conf import ng_ext
        config_body = ng_ext.set_extension_by_config(project_name, config_body)
        if not os.path.exists(apply_check):
            public.writeFile(apply_check, '')
        if not os.path.exists(config_file):
            public.writeFile(config_file, config_body)
        else:
            if not self._replace_nginx_conf(config_file, mut_config):
                public.writeFile(config_file, config_body)
        return True

    @staticmethod
    def _replace_nginx_conf(config_file, mut_config: dict) -> bool:
        """尝试替换"""
        data: str = public.readFile(config_file)
        tab_spc = "    "
        rep_list = [
            (
                 r"([ \f\r\t\v]*listen[^;\n]*;\n(\s*http2\s+on\s*;[^\n]*\n)?)+",
                mut_config["listen_ports"] + "\n"
            ),
            (
                r"[ \f\r\t\v]*root [ \f\r\t\v]*/[^;\n]*;",
                "    root {};".format(mut_config["site_path"])
            ),
            (
                r"[ \f\r\t\v]*server_name [ \f\r\t\v]*[^\n;]*;",
                "   server_name {};".format(mut_config["domains"])
            ),
            (
                r"(location / {)(.*?)(})",
                mut_config["proxy"].strip()
            ),
            (
                "[ \f\r\t\v]*#SSL-START(.*\n){2,15}[ \f\r\t\v]*#SSL-END",
                "{}#SSL-START SSL相关配置\n{}#error_page 404/404.html;\n{}{}\n{}#SSL-END".format(
                    tab_spc, tab_spc, tab_spc, mut_config["ssl_config"], tab_spc)
            )
        ]
        for rep, info in rep_list:
            if re.search(rep, data):
                data = re.sub(rep, info, data, 1)
            else:
                return False
        public.writeFile(config_file, data)
        return True

    def clear_nginx_config(self, project):
        '''
            @name 清除nginx配置
            @author hwliang<2021-08-09>
            @param project: dict<项目信息>
            @return bool
        '''
        project_name = project['name']
        config_file = "{}/nginx/python_{}.conf".format(self._vhost_path, project_name)
        if os.path.exists(config_file):
            os.remove(config_file)
        rewrite_file = "{panel_path}/vhost/rewrite/python_{project_name}.conf".format(
            panel_path=self._panel_path, project_name=project_name)
        if os.path.exists(rewrite_file):
            os.remove(rewrite_file)
        return True

    def clear_apache_config(self, project):
        '''
            @name 清除apache配置
            @author hwliang<2021-08-09>
            @param project_find: dict<项目信息>
            @return bool
        '''
        project_name = project['name']
        config_file = "{}/apache/python_{}.conf".format(self._vhost_path, project_name)
        if os.path.exists(config_file):
            os.remove(config_file)
        return True

    def get_project_find(self, project_name) -> Union[bool, dict]:
        '''
            @name 获取指定项目配置
            @author hwliang<2021-08-09>
            @param project_name<string> 项目名称
            @return dict
        '''
        project_info = public.M('sites').where('project_type=? AND name=?', ('Python', project_name)).find()
        if isinstance(project_info, str):
            raise public.PanelError('数据库查询错误：' + project_info)
        if not project_info: return False
        project_info['project_config'] = json.loads(project_info['project_config'])
        if "env_list" not in project_info['project_config']:
            project_info['project_config']["env_list"] = []
        if "env_file" not in project_info['project_config']:
            project_info['project_config']["env_file"] = ""
        return project_info

    def clear_config(self, project_name):
        '''
            @name 清除项目配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return bool
        '''
        project_find = self.get_project_find(project_name)
        if not project_find: return False
        self.clear_nginx_config(project_find)
        self.clear_apache_config(project_find)
        public.serviceReload()
        return True

    def set_config(self, project_name, is_modify=False, proxy_port=None):
        '''
            @name 设置项目配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return bool
        '''
        project_find = self.get_project_find(project_name)
        if not project_find: return False
        if not project_find['project_config']: return False
        if not project_find['project_config']['bind_extranet']: return False
        if not project_find['project_config']['domains']: return False
        self.set_nginx_config(project_find, is_modify, proxy_port)
        self.set_apache_config(project_find)
        public.serviceReload()
        return True

    def BindExtranet(self, get):
        '''
            @name 绑定外网
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                name: string<项目名称>
            }
            @return dict
        '''
        res_msg = self._check_webserver()
        if res_msg:
            return public.return_error(res_msg)
        project_name = get.name.strip()
        project_find = self.get_project_find(project_name)
        if self.prep_status(project_find["project_config"]) == "running":
            return public.return_error("项目环境安装制作中.....<br>请勿操作")
        if not project_find: return public.return_error('项目不存在')
        if not project_find['project_config']['domains']: return public.return_error(
            '请先到【域名管理】选项中至少添加一个域名')
        project_find['project_config']['bind_extranet'] = 1
        public.M('sites').where("id=?", (project_find['id'],)).setField('project_config',
                                                                        json.dumps(project_find['project_config']))
        self.set_config(project_name)
        public.WriteLog(self._log_name, 'Python项目{}, 开启外网映射'.format(project_name))
        return public.returnMsg(True, '开启外网映射成功')

    def unBindExtranet(self, get):
        '''
            @name 解绑外网
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                name: string<项目名称>
            }
            @return dict
        '''
        project_name = get.name.strip()
        self.clear_config(project_name)
        public.serviceReload()
        project_find = self.get_project_find(project_name)
        project_find['project_config']['bind_extranet'] = 0
        public.M('sites').where("id=?", (project_find['id'],)).setField(
            'project_config', json.dumps(project_find['project_config']))
        public.WriteLog(self._log_name, 'Python项目{}, 关闭外网映射'.format(project_name))
        return public.returnMsg(True, '关闭成功')

    def GetProjectDomain(self, get):
        '''
            @name 获取指定项目的域名列表
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                name: string<项目名称>
            }
            @return dict
        '''
        project_name = get.name.strip()
        project_id = public.M('sites').where('name=?', (project_name,)).getField('id')
        if not project_id:
            return public.returnMsg(False, '未查询到该网站')
        domains = public.M('domain').where('pid=?', (project_id,)).order('id desc').select()
        return domains

    def RemoveProjectDomain(self, get):
        '''
            @name 为指定项目删除域名
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                name: string<项目名称>
                domain: string<域名>
            }
            @return dict
        '''
        project_name = get.name.strip()
        project_find = self.get_project_find(project_name)
        if not project_find:
            return public.return_error('指定项目不存在')
        domain_arr = get.domain.split(':')
        if len(domain_arr) == 1:
            domain_arr.append(80)

        # 从域名配置表中删除
        project_id = public.M('sites').where('name=?', (project_name,)).getField('id')
        if len(project_find['project_config']['domains']) == 1:
            if int(project_find['project_config']['bind_extranet']):
                return public.returnMsg(False, '项目至少需要一个域名')
        domain_id = public.M('domain').where('name=? AND pid=?', (domain_arr[0], project_id)).getField('id')
        if not domain_id:
            return public.returnMsg(False, '指定域名不存在')
        public.M('domain').where('id=?', (domain_id,)).delete()

        # 从 project_config 中删除
        if get.domain in project_find['project_config']['domains']:
            project_find['project_config']['domains'].remove(get.domain)
        if get.domain + ":80" in project_find['project_config']['domains']:
            project_find['project_config']['domains'].remove(get.domain + ":80")

        public.M('sites').where('id=?', (project_id,)).save('project_config',
                                                            json.dumps(project_find['project_config']))
        public.WriteLog(self._log_name, '从项目：{}，删除域名{}'.format(project_name, get.domain))
        self.set_config(project_name)
        return public.returnMsg(True, '删除域名成功')

    def MultiRemoveProjectDomain(self, get):
        '''
            @name 为指定项目删除域名
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                name: string<项目名称>
                domain: string<域名>
            }
            @return dict
        '''
        project_name = get.name.strip()
        project_find = self.get_project_find(project_name)
        if not project_find:
            return public.return_error('指定项目不存在')
        domain_ids: list = get.domain_ids

        try:
            if isinstance(domain_ids, str):
                domain_ids = json.loads(domain_ids)
            for i in range(len(domain_ids)):
                domain_ids[i] = int(domain_ids[i])
        except:
            return public.returnMsg(False, '域名id参数错误')

        # 获取正确的IDS
        project_id = public.M('sites').where('name=?', (project_name,)).getField('id')
        _all_id = public.M('domain').where('pid=?', (project_id,)).field("id,name,port").select()
        if not isinstance(_all_id, list):
            return public.returnMsg(False, '网站数据错误')
        all_id = {i["id"]: (i["name"], i["port"]) for i in _all_id}
        # 从域名配置表中删除
        for i in domain_ids:
            if i not in all_id:
                return public.returnMsg(False, '域名id参数不来自本站点')
        is_all = len(domain_ids) == len(all_id)
        not_del = None
        if is_all:
            domain_ids.sort(reverse=True)
            domain_ids, not_del = domain_ids[:-1], domain_ids[-1]
        if not_del:
            not_del = {"id": not_del, "name": all_id[not_del][0], "port": all_id[not_del][1]}

        public.M('domain').where(f'id IN ({",".join(["?"] * len(domain_ids))})', domain_ids).delete()

        del_domains = []
        for i in domain_ids:
            # 从 project_config 中删除
            d_n, d_p = all_id[i]
            del_domains.append(d_n + ':' + str(d_p))
            if d_n in project_find['project_config']['domains']:
                project_find['project_config']['domains'].remove(d_n)
            if d_n + ':' + str(d_p) in project_find['project_config']['domains']:
                project_find['project_config']['domains'].remove(d_n + ':' + str(d_p))

        public.M('sites').where('id=?', (project_id,)).save(
            'project_config', json.dumps(project_find['project_config']))
        public.WriteLog(self._log_name, '从项目：{}，批量删除域名:'.format(project_name, del_domains))
        self.set_config(project_name)

        if isinstance(not_del, dict):
            error_data = {not_del["name"]: "项目至少需要一个域名"}
        else:
            error_data = {}

        return {
            "status": True,
            "msg": "删除成功 :{}".format(del_domains),
            "error": error_data,
            "success": del_domains
        }

    def AddProjectDomain(self, get):
        '''
            @name 为指定项目添加域名
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                name: string<项目名称>
                domains: list<域名列表>
            }
            @return dict
        '''
        project_name = get.name.strip()
        project_find = self.get_project_find(project_name)
        if not project_find:
            return public.return_error('指定项目不存在')
        project_id = project_find['id']
        domains = get.domains
        check_cloud = False
        flag = False
        res_domains = []
        for domain in domains:
            domain = domain.strip()
            if not domain: continue
            domain_arr = domain.split(':')
            domain_arr[0] = self.check_domain(domain_arr[0])
            if domain_arr[0] is False:
                res_domains.append({"name": domain, "status": False, "msg": '域名格式错误'})
                continue
            if len(domain_arr) == 1:
                domain_arr.append("")
            if domain_arr[1] == "":
                domain_arr[1] = 80
                domain += ':80'
            try:
                if not (0 < int(domain_arr[1]) < 65535):
                    res_domains.append({"name": domain, "status": False, "msg": '域名格式错误'})
                    continue
            except ValueError:
                res_domains.append({"name": domain, "status": False, "msg": '域名格式错误'})
                continue
            if not public.M('domain').where('name=?', (domain_arr[0],)).count():
                public.M('domain').add('name,pid,port,addtime',
                                       (domain_arr[0], project_id, domain_arr[1], public.getDate()))
                if not domain in project_find['project_config']['domains']:
                    project_find['project_config']['domains'].append(domain)
                public.WriteLog(self._log_name, '成功添加域名{}到项目{}'.format(domain, project_name))
                res_domains.append({"name": domain_arr[0], "status": True, "msg": '添加成功'})
                if not check_cloud:
                    public.check_domain_cloud(domain_arr[0])
                    check_cloud = True
                flag = True
            else:
                public.WriteLog(self._log_name, '添加域名错误，域名{}已存在'.format(domain))
                res_domains.append(
                    {"name": domain_arr[0], "status": False, "msg": '添加失败，域名{}已存在'.format(domain)})
        if flag:
            public.M('sites').where('id=?', (project_id,)).save('project_config',
                                                                json.dumps(project_find['project_config']))
            self.set_config(project_name)

        return self._check_add_domain(project_name, res_domains)

    def auto_run(self):
        '''
        @name 开机自动启动
        '''
        # 获取数据库信息
        project_list = public.M('sites').where('project_type=?', ('Python',)).field('name,path,project_config').select()
        get = public.dict_obj()
        success_count = 0
        error_count = 0
        for project in project_list:
            project_config = json.loads(project['project_config'])
            if project_config['auto_run'] in [0, False, '0', None]: continue
            project_name = project['name']
            project_state = self.get_project_run_state(project_name=project_name)
            if not project_state:
                get.name = project_name
                result = self.StartProject(get)
                if not result['status']:
                    error_count += 1
                    error_msg = '自动启动Python项目[' + project_name + ']失败!'
                    public.WriteLog(self._log_name, error_msg)
                else:
                    success_count += 1
                    success_msg = '自动启动Python项目[' + project_name + ']成功!'
                    public.WriteLog(self._log_name, success_msg)
        if (success_count + error_count) < 1: return False
        dene_msg = '共需要启动{}个Python项目，成功{}个，失败{}个'.format(success_count + error_count, success_count,
                                                                       error_count)
        public.WriteLog(self._log_name, dene_msg)
        return True

    # —————————————
    #  日志切割   |
    # —————————————
    def del_crontab(self, name):
        """
        @name 删除项目日志切割任务
        @auther hezhihong<2022-10-31>
        @return
        """
        cron_name = '[勿删]Python项目[{}]运行日志切割'.format(name)
        cron_path = public.GetConfigValue('setup_path') + '/cron/'
        cron_list = public.M('crontab').where("name=?", (cron_name,)).select()
        if cron_list:
            for i in cron_list:
                if not i: continue
                cron_echo = public.M('crontab').where("id=?", (i['id'],)).getField('echo')
                args = {"id": i['id']}
                import crontab
                crontab.crontab().DelCrontab(args)
                del_cron_file = cron_path + cron_echo
                public.ExecShell("crontab -u root -l| grep -v '{}'|crontab -u root -".format(del_cron_file))

    def add_crontab(self, name, log_conf, python_path):
        """
        @name 构造站点运行日志切割任务
        """
        cron_name = f'[勿删]Python项目[{name}]运行日志切割'
        if not public.M('crontab').where('name=?', (cron_name,)).count():
            cmd = '{pyenv} {script_path} {name}'.format(
                pyenv=python_path,
                script_path=self.__log_split_script_py,
                name=name
            )
            args = {
                "name": cron_name,
                "type": 'day' if log_conf["log_size"] == 0 else "minute-n",
                "where1": "" if log_conf["log_size"] == 0 else log_conf["minute"],
                "hour": log_conf["hour"],
                "minute": log_conf["minute"],
                "sName": name,
                "sType": 'toShell',
                "notice": '0',
                "notice_channel": '',
                "save": str(log_conf["num"]),
                "save_local": '1',
                "backupTo": '',
                "sBody": cmd,
                "urladdress": ''
            }
            import crontab
            res = crontab.crontab().AddCrontab(args)
            if res and "id" in res.keys():
                return True, "新建任务成功"
            return False, res["msg"]
        return True

    def change_cronta(self, name, log_conf):
        """
        @name 更改站点运行日志切割任务
        """
        python_path = "/www/server/panel/pyenv/bin/python3"
        if not python_path: return False
        cronInfo = public.M('crontab').where('name=?', (f'[勿删]Python项目[{name}]运行日志切割',)).find()
        if not cronInfo:
            return self.add_crontab(name, log_conf, python_path)
        import crontab
        recrontabMode = crontab.crontab()
        id = cronInfo['id']
        del (cronInfo['id'])
        del (cronInfo['addtime'])
        cronInfo['sBody'] = '{pyenv} {script_path} {name}'.format(
            pyenv=python_path,
            script_path=self.__log_split_script_py,
            name=name
        )
        cronInfo['where_hour'] = log_conf['hour']
        cronInfo['where_minute'] = log_conf['minute']
        cronInfo['save'] = log_conf['num']
        cronInfo['type'] = 'day' if log_conf["log_size"] == 0 else "minute-n"
        cronInfo['where1'] = '' if log_conf["log_size"] == 0 else log_conf['minute']

        columns = 'where_hour,where_minute,sBody,save,type,where1'
        values = (
            cronInfo['where_hour'], cronInfo['where_minute'], cronInfo['sBody'], cronInfo['save'], cronInfo['type'],
            cronInfo['where1'])
        recrontabMode.remove_for_crond(cronInfo['echo'])
        if cronInfo['status'] == 0: return False, '当前任务处于停止状态,请开启任务后再修改!'
        sync_res=recrontabMode.sync_to_crond(cronInfo)
        if not sync_res['status']:
            return False,sync_res['msg']
        public.M('crontab').where('id=?', (id,)).save(columns, values)
        public.WriteLog('计划任务', '修改计划任务[' + cronInfo['name'] + ']成功')
        return True, '修改成功'

    def mamger_log_split(self, get):
        """管理日志切割任务
        @author baozi <202-02-27>
        @param:
            get  ( dict ):  包含name, mode, hour, minute
        @return
        """
        name = get.name.strip()
        project_conf = self._get_project_conf(name_id=name)
        if not project_conf:
            return public.returnMsg(False, "没有该项目，请尝试刷新页面")
        try:
            _compress = False
            _log_size = float(get.log_size) if float(get.log_size) >= 0 else 0
            _hour = get.hour.strip() if 0 <= int(get.hour) < 24 else "2"
            _minute = get.minute.strip() if 0 <= int(get.minute) < 60 else '0'
            _num = int(get.num) if 0 < int(get.num) <= 1800 else 180
            if "compress" in get:
                _compress = int(get.compress) == 1
        except (ValueError, AttributeError):
            _log_size = 0
            _hour = "2"
            _minute = "0"
            _num = 180
            _compress = False

        if _log_size != 0:
            _log_size = _log_size * 1024 * 1024
            _hour = 0
            _minute = 5

        log_conf = {
            "log_size": _log_size,
            "hour": _hour,
            "minute": _minute,
            "num": _num,
            "compress": _compress,
        }
        flag, msg = self.change_cronta(name, log_conf)
        if flag:
            conf_path = '{}/data/run_log_split.conf'.format(public.get_panel_path())
            if os.path.exists(conf_path):
                try:
                    data = json.loads(public.readFile(conf_path))
                except:
                    data = {}
            else:
                data = {}
            data[name] = {
                "stype": "size" if bool(_log_size) else "day",
                "log_size": _log_size,
                "limit": _num,
                "compress": _compress,
            }
            public.writeFile(conf_path, json.dumps(data))
            project_conf["log_conf"] = log_conf
            pdata = {
                "project_config": json.dumps(project_conf)
            }
            public.M('sites').where('name=?', (name,)).update(pdata)
        return public.returnMsg(flag, msg)

    def set_log_split(self, get):
        """设置日志计划任务状态
        @author baozi <202-02-27>
        @param:
            get  ( dict ):  包含项目名称name
        @return  msg : 操作结果
        """
        name = get.name.strip()
        project_conf = self._get_project_conf(name_id=name)
        if not project_conf:
            return public.returnMsg(False, "没有该项目，请尝试刷新页面")
        cronInfo = public.M('crontab').where('name=?', (f'[勿删]Python项目[{name}]运行日志切割',)).find()
        if not cronInfo:
            return public.returnMsg(False, "该项目没有设置运行日志的切割任务")

        status_msg = ['停用', '启用']
        status = 1
        import crontab
        recrontabMode = crontab.crontab()

        if cronInfo['status'] == status:
            status = 0
            recrontabMode.remove_for_crond(cronInfo['echo'])
        else:
            cronInfo['status'] = 1
            sync_res=recrontabMode.sync_to_crond(cronInfo)
            if not sync_res['status']:
                return public.returnMsg(False, sync_res['msg'])
        public.M('crontab').where('id=?', (cronInfo["id"],)).setField('status', status)
        public.WriteLog('计划任务', '修改计划任务[' + cronInfo['name'] + ']状态为[' + status_msg[status] + ']')
        return public.returnMsg(True, '设置成功')

    def get_log_split(self, get):
        """获取站点的日志切割任务
        @author baozi <202-02-27>
        @param:
            get  ( dict ):   name
        @return msg : 操作结果
        """

        name = get.name.strip()
        project_conf = self._get_project_conf(name_id=name)
        if not project_conf:
            return public.returnMsg(False, "没有该项目，请尝试刷新页面")
        cronInfo = public.M('crontab').where('name=?', (f'[勿删]Python项目[{name}]运行日志切割',)).find()
        if not cronInfo:
            return public.returnMsg(False, "该项目没有设置运行日志的切割任务")

        if "log_conf" not in project_conf:
            return public.returnMsg(False, "日志切割配置丢失，请尝试重新设置")
        res = project_conf["log_conf"]
        res["status"] = cronInfo["status"]
        return {"status": True, "data": res}

    # ——————————————————————————————————————————————
    #   对用户的项目目录进行预先读取， 获取有效信息   |
    # ——————————————————————————————————————————————

    def _get_requirements_by_readme_file(self, path) -> Optional[str]:
        readme_rep = re.compile("^[Rr][Ee][Aa][Dd][Mm][Ee]")
        readme_files = self.__search_file(readme_rep, path, this_type="file")
        if not readme_files: return None

        # 从README找安装依赖包文件
        target_path = None
        requirements_rep = re.compile(r'pip\s+install\s+-r\s+(?P<target>[A-z0-9_/.]*)')
        for i in readme_files:
            file_data = public.read_rare_charset_file(i)
            if not isinstance(file_data, str):
                continue
            target = re.search(requirements_rep, file_data)
            if target:
                requirements_path = os.path.join(path, target.group("target"))
                if os.path.exists(requirements_path) and os.path.isfile(requirements_path):
                    target_path = str(requirements_path)
                    break
        if not target_path:
            return None
        return target_path

    def _get_requirements_file_by_name(self, path) -> Optional[str]:
        requirements_rep = re.compile(r"^[rR]equirements\.txt$")
        requirements_path = self.__search_file(requirements_rep, path, this_type="file")
        if not requirements_path:
            requirements_rep2 = re.compile(r"^[Rr]equirements?")
            requirements_dir = self.__search_file(requirements_rep2, path, this_type="dir")
            if requirements_dir:
                for i in requirements_dir:
                    tmp = self._get_requirements_file_by_name(i)
                    if tmp:
                        return tmp
            return None
        return requirements_path[0]

    def get_requirements_file(self, path: str) -> Optional[str]:
        requirement_path = self._get_requirements_file_by_name(path)
        if not requirement_path:
            requirement_path = self._get_requirements_by_readme_file(path)
        return requirement_path

    @staticmethod
    def _get_framework_by_requirements(requirements_path: str) -> Optional[str]:
        file_body = public.read_rare_charset_file(requirements_path)
        if not isinstance(file_body, str):
            return None
        rep_list = [
            (r"[Dd]jango(\s*==|\s*\n)", "django"),
            (r"[Ff]lask(\s*==|\s*\n)", "flask"),
            (r"[Ss]anic(\s*==|\s*\n)", "sanic"),
            (r"[Ff]ast[Aa]pi(\s*==|\s*\n)", "fastapi"),
            (r"[Tt]ornado(\s*==|\s*\n)", "tornado"),
            (r"aiohttp(\s*==|\s*\n)", "aiohttp"),
        ]
        frameworks = set()
        for rep_str, framework in rep_list:
            if re.search(rep_str, file_body):
                frameworks.add(framework)
        if "aiohttp" in frameworks and len(frameworks) == 2:
            frameworks.remove("aiohttp")
            return frameworks.pop()

        if len(frameworks) == 1:
            return frameworks.pop()
        return None

    @staticmethod
    def _check_runfile_framework_xsgi(
            runfile_list: List[str],
            framework: str = None) -> Tuple[Optional[str], Optional[str], Optional[str]]:

        if not runfile_list:
            return None, None, None
        framework_check_dict = {
            "django": [
                (re.compile(r"from\s+django\.core\.asgi\s+import\s+get_asgi_application"), "asgi"),
                (re.compile(r"get_asgi_application\(\)"), "asgi"),
                (re.compile(r"from\s+django\.core\.wsgi\s+import\s+get_wsgi_application"), "wsgi"),
                (re.compile(r"get_wsgi_application\(\)"), "wsgi"),
            ],
            "flask": [
                (re.compile(r"from\s+flask\s+import(.*)Flask"), "wsgi"),
                (re.compile(r"\s*=\s*Flask\(.*\)"), "wsgi"),
                (re.compile(r"from\s+flask\s+import"), "wsgi"),
            ],
            "fastapi": [
                (re.compile(r"from\s+fastapi\s+import(.*)FastAPI"), "asgi"),
                (re.compile(r"\s*=\s*FastAPI\(.*\)"), "asgi"),
                (re.compile(r"from\s+fastapi\s+import"), "asgi"),
            ],
            "sanic": [
                (re.compile(r"from\s+sanic\s+import\s+Sanic"), "asgi"),
                (re.compile(r"\s*=\s*Sanic\(.*\)c"), "asgi"),
                (re.compile(r"from\s+sanic\s+import"), "asgi"),
            ],
            "tornado": [
                (re.compile(r"import\s+tornado"), None),
            ],

        }
        if framework and framework in framework_check_dict:
            framework_check_dict = {framework: framework_check_dict[framework]}
        for i in runfile_list:
            file_data = public.read_rare_charset_file(i)
            if not isinstance(file_data, str):
                continue
            for tmp_framework, check_list in framework_check_dict.items():
                for tmp_rep, xwgi in check_list:
                    if re.search(tmp_rep, file_data):
                        return i, tmp_framework, xwgi
        if framework:
            return runfile_list[0], framework, None
        if runfile_list:
            return runfile_list[0], None, None
        return None, None, None

    def _get_run_file_list(self, path, search_sub=False) -> List[str]:
        """
        常用的名称： manager，wsgi，asgi，app，main，run, server
        """
        runfile_rep = re.compile(r"^(wsgi|asgi|app|main|manager|run|server)\.py$")
        maybe_runfile = self.__search_file(runfile_rep, path, this_type="file")

        if maybe_runfile:
            return maybe_runfile
        elif not search_sub:
            return []

        for i in os.listdir(path):
            tmp_path = os.path.join(path, i)
            if os.path.isdir(tmp_path):
                maybe_runfile = self._get_run_file_list(tmp_path, search_sub=False)
                if maybe_runfile:
                    return maybe_runfile
        return []

    def get_info(self, get):
        """ 对用户的项目目录进行预先读取， 获取有效信息
        @author baozi <202-03-10>
        @param:
            get  ( dict ):  请求信息，包含path，路径
        @return  _type_ : _description_
        """
        if "path" not in get:
            return public.returnMsg(False, "没有选择项目路径信息")
        else:
            path = get.path.strip()
        if path[-1] == "/":
            path = path[:-1]
        if not os.path.exists(path):
            return public.returnMsg(False, "项目目录不存在")

        # 找requirement文件
        requirement_path = self.get_requirements_file(path)
        maybe_runfile_list = self._get_run_file_list(path, search_sub=True)
        framework = None
        if requirement_path:
            framework = self._get_framework_by_requirements(requirement_path)

        runfile, framework, xsgi = self._check_runfile_framework_xsgi(maybe_runfile_list, framework)

        call_app = "app"
        if framework and runfile:
            values = {
                "framework": framework,
                "rfile": runfile,
            }
            call_app = self._get_callable_app(values)

        return {
            "framework": framework,
            "requirement_path": requirement_path,
            "runfile": runfile,
            "xsgi": xsgi,
            "call_app": call_app
        }

    @staticmethod
    def __search_file(name_rep: re.Pattern, path: str, this_type="file", exclude=None) -> List[str]:
        target_names = []
        for f_name in os.listdir(path):
            f_name.encode('utf-8')
            target_name = name_rep.search(f_name)
            if target_name:
                target_names.append(f_name)

        res = []
        for i in target_names:
            if exclude and i.find(exclude) != -1:
                continue
            _path = os.path.join(path, i)
            if this_type == "file" and os.path.isfile(_path):
                res.append(_path)
                continue
            if this_type == "dir" and not os.path.isfile(_path):
                res.append(_path)
                continue

        return res

    def get_info_by_runfile(self, get):
        """ 通过运行文件对用户的项目预先读取， 获取有效信息
        @author baozi <202-03-10>
        @param:
            get  ( dict ):  请求信息，包含path，路径
        @return  _type_ : _description_
        """
        if "runfile" not in get:
            return public.returnMsg(False, "没有选择项目路径信息")
        else:
            runfile = get.runfile.strip()
        if not os.path.isfile(runfile):
            return False, "项目运行文件错误"

        runfile, framework, xsgi = self._check_runfile_framework_xsgi([runfile])
        if runfile is None:
            return {
                "framework": None,
                "xsgi": None,
                "call_app": None
            }

        values = {
            "framework": framework,
            "rfile": runfile,
        }

        call_app = self._get_callable_app(values)

        return {
            "framework": framework,
            "xsgi": xsgi,
            "call_app": call_app
        }

    def for_split(self, logsplit, project):
        """日志切割方法调用
        @author baozi <202-03-20>
        @param:
            logsplit  ( LogSplit ):  日志切割方法，传入 pjanme:项目名称 sfile:日志文件路径 log_prefix:产生的日志文件前缀
            project  ( dict ):  项目内容
        @return
        """
        if project['project_config']["stype"] == "uwsgi":  # uwsgi 启动
            log_file = project['project_config']["logpath"] + "/uwsgi.log"
            logsplit(project["name"], log_file, project["name"])
        elif project['project_config']["stype"] == "gunicorn":  # gunicorn 启动
            log_file = project['project_config']["logpath"] + "/gunicorn_error.log"
            logsplit(project["name"], log_file, project["name"] + "_error")
            log_file2 = project['project_config']["logpath"] + "/gunicorn_acess.log"
            logsplit(project["name"], log_file2, project["name"] + "_acess")
        else:   # 命令行启动或原本的python启动
            log_file = project['project_config']["logpath"] + "/error.log"
            logsplit(project["name"], log_file, project["name"])

    @staticmethod
    def _check_add_domain(site_name, domains):
        from panelSite import panelSite
        ssl_data = panelSite().GetSSL(type("get", tuple(), {"siteName": site_name})())
        if not ssl_data["status"] or not ssl_data.get("cert_data", {}).get("dns", None):
            return {"domains": domains}
        domain_rep = []
        for i in ssl_data["cert_data"]["dns"]:
            if i.startswith("*"):
                _rep = "^[^\.]+\." + i[2:].replace(".", "\.")
            else:
                _rep = "^" + i.replace(".", "\.")
            domain_rep.append(_rep)
        no_ssl = []
        for domain in domains:
            if not domain["status"]: continue
            for _rep in domain_rep:
                if re.search(_rep, domain["name"]):
                    break
            else:
                no_ssl.append(domain["name"])
        if no_ssl:
            return {
                "domains": domains,
                "not_ssl": no_ssl,
                "tip": "本站点已启用SSL证书,但本次添加的域名：{}，无法匹配当前证书，如有需求，请重新申请证书。".format(
                    str(no_ssl))
            }
        return {"domains": domains}

    # @staticmethod
    # def _get_pid_by_ps(check_sh: str) -> List[int]:
    #     _check_sh = check_sh.rsplit("|", 1)[0]
    #     _check_sh += "| awk '{print $2}'"
    #     s, e = public.ExecShell(_check_sh)
    #     pids = [int(i) for i in s.split("\n") if bool(i.strip())]
    #     return pids

    def get_mem_and_cpu(self, pids: list):
        mem, cpusum = 0, 0
        for pid in pids:
            res = self.get_process_info_by_pid(pid)
            if "memory_used" in res:
                mem += res["memory_used"]
            if "cpu_percent" in res:
                cpusum += res["cpu_percent"]
        return mem, cpusum

    @staticmethod
    def get_proc_rss(pid):
        status_path = '/proc/' + str(pid) + '/status'
        if not os.path.exists(status_path):
            return 0
        status_file = public.readFile(status_path)
        if not status_file:
            return 0
        rss = 0
        try:
            rss = int(re.search(r'VmRSS:\s*(\d+)\s*kB', status_file).groups()[0])
        except:
            pass
        rss = int(rss) * 1024
        return rss

    def get_process_info_by_pid(self, pid):
        process_info = {}
        try:
            if not os.path.exists('/proc/{}'.format(pid)): return process_info
            p = psutil.Process(pid)
            status_ps = {'sleeping': '睡眠', 'running': '活动'}
            with p.oneshot():
                process_info['memory_used'] = self.get_proc_rss(pid)
                process_info['cpu_percent'] = self.get_cpu_precent(p)
                return process_info
        except:
            return process_info

    def get_cpu_precent(self, p):
        '''
            @name 获取进程cpu使用率
            @author hwliang<2021-08-09>
            @param p: Process<进程对像>
            @return dict
        '''
        skey = "cpu_pre_{}".format(p.pid)
        old_cpu_times = cache.get(skey)

        process_cpu_time = self.get_process_cpu_time(p.cpu_times())
        if not old_cpu_times:
            cache.set(skey, [process_cpu_time, time.time()], 3600)
            old_cpu_times = cache.get(skey)
            process_cpu_time = self.get_process_cpu_time(p.cpu_times())

        old_process_cpu_time = old_cpu_times[0]
        old_time = old_cpu_times[1]
        new_time = time.time()
        cache.set(skey, [process_cpu_time, new_time], 3600)
        percent = round(100.00 * (process_cpu_time - old_process_cpu_time) / (new_time - old_time) / psutil.cpu_count(), 2)
        return percent

    @staticmethod
    def get_process_cpu_time(cpu_times):
        cpu_time = 0.00
        for s in cpu_times:
            cpu_time += s
        return cpu_time

    def get_project_status(self, project_id):
        # 仅使用在项目停止告警中
        project_info = public.M('sites').where('project_type=? AND id=?', ('Python', project_id)).find()
        if not project_info:
            return None, project_info["name"]
        if self.is_stop_by_user(project_id):
            return True, project_info["name"]
        project_config = json.loads(project_info['project_config'])
        res = self.get_project_run_state(project_name=project_info["name"])
        return bool(res), project_info["name"]

    # def update_env(self, get):
    #     is_pypy = False
    #     try:
    #         name = get.name.strip()
    #         update_version = get.update_version.strip()
    #         if hasattr(get, "is_pypy") and get.is_pypy.strip() in (True, 1, "1", "true"):
    #             is_pypy = True
    #     except AttributeError:
    #         return public.returnMsg(False, "参数错误")
    #     project_conf = self._get_project_conf(name_id=name)
    #     if not project_conf:
    #         return public.returnMsg(False, "没有该项目，请尝试刷新页面")
    #     if is_pypy:
    #         sfile = "{}/pypy_versions/{}".format(self._pyv_path, update_version)
    #     else:
    #         sfile = "{}/versions/{}".format(self._pyv_path, update_version)
    #     if not os.path.exists(sfile):
    #         return public.returnMsg(False, "没有安装指定的版本，无法升级")
    #     if self._update_env(project_conf, update_version, is_pypy=is_pypy):
    #         project_conf["version"] = update_version
    #         project_conf["is_pypy"] = is_pypy
    #         pdata = {
    #             "project_config": json.dumps(project_conf)
    #         }
    #         public.M('sites').where('name=?', (project_conf['pjname'].strip(),)).update(pdata)
    #
    #     return public.returnMsg(True, "升级操作已执行")
    #
    # def _update_env(self, project_conf: dict, update_version: str, is_pypy: bool) -> Optional[bool]:
    #     """
    #     准备python虚拟环境和服务器应用
    #     """
    #     import files
    #     log_path: str = "{}/{}_update.log".format(self._logs_path, project_conf['pjname'])
    #     pip_freeze_file: str = "{}/{}_update.text".format(self._project_path, project_conf['pjname'])
    #     fd = None
    #     try:
    #         fd = open(log_path, 'w')
    #         fd.write("\n|- 开始升级虚拟环境的python版本.......\n")
    #         fd.write("\n|- 开始记录虚拟环境中的包.......\n")
    #         vp_pip = self._get_vp_pip(project_conf["vpath"])
    #         self.exec_shell("{} freeze > {}".format(vp_pip, pip_freeze_file), fd)
    #         if not os.path.exists(pip_freeze_file):
    #             fd.write("\n|- 未备份成功.......\n")
    #             fd.flush()
    #             return False
    #         fd.write("\n|- 包版本记录完成.......\n")
    #         fd.write("\n|- 开始备份当前环境.......\n")
    #         fd.flush()
    #         back_path = project_conf["vpath"] + "_backup"
    #         if os.path.exists(back_path):
    #             shutil.rmtree(back_path)
    #         copy_shell = "\mv {} {}_backup".format(project_conf["vpath"], project_conf["vpath"])
    #         self.exec_shell(copy_shell, fd)
    #         if not os.path.exists(project_conf["vpath"] + "_backup"):
    #             fd.write("\n|- 未备份成功.......\n")
    #             fd.flush()
    #             return False
    #         fd.write("\n|- 备份成功.......\n")
    #         fd.write("\n|- 开始虚拟环境版本升级.......\n")
    #         fd.flush()
    #         get = public.dict_obj()
    #         if not is_pypy:
    #             get.sfile = "{}/versions/{}".format(self._pyv_path, update_version)
    #         else:
    #             get.sfile = "{}/pypy_versions/{}".format(self._pyv_path, update_version)
    #         get.dfile = project_conf["vpath"]
    #         res = files.files().CopyFile(get)
    #         if res["status"] is False:
    #             return False
    #         os.chown(get.dfile, *self._get_www_state())
    #         self.install_pip(project_conf['vpath'], update_version)
    #         if not os.path.exists(project_conf['vpath']):
    #             return False
    #         fd.write("\n|- 虚拟环境版本升级成功\n")
    #         fd.write("\n|- 开始恢复包版本\n")
    #         fd.flush()
    #         v_python = self._get_vp_python(project_conf["vpath"])
    #         _sh = "{} -m pip install -i {} -r {}".format(v_python, self._pip_source, pip_freeze_file)
    #         self.exec_shell(_sh, fd)
    #         fd.write("\n|- 包版本恢复已执行\n")
    #         fd.write("\n|- 虚拟环境升级成功\n")
    #         fd.flush()
    #         return True
    #     except:
    #         import traceback
    #         if fd is not None:
    #             fd.close()
    #         return False
    #
    # def recover_env(self, get):
    #     try:
    #         name = get.name.strip()
    #     except AttributeError:
    #         return public.returnMsg(False, "参数错误")
    #     project_conf = self._get_project_conf(name_id=name)
    #     if not project_conf:
    #         return public.returnMsg(False, "没有该项目，请尝试刷新页面")
    #     back_path = project_conf["vpath"] + "_backup"
    #     if not os.path.exists(back_path):
    #         return public.returnMsg(False, "没有历史文件不能恢复")
    #
    #     public.ExecShell("\mv {} {}_change".format(project_conf["vpath"], project_conf["vpath"]))
    #     public.ExecShell("\mv {}_backup {}".format(project_conf["vpath"], project_conf["vpath"]))
    #     public.ExecShell("\mv {}_change {}_backup".format(project_conf["vpath"], project_conf["vpath"]))
    #     v_python = self._get_vp_python(project_conf["vpath"])
    #     version_str = public.ExecShell("{} -V".format(v_python))[0]
    #     result = re.search(r"(?P<target>\d+\.\d+\.\d*)", version_str)
    #     if result:
    #         project_conf["version"] = result.group("target")
    #         pdata = {
    #             "project_config": json.dumps(project_conf)
    #         }
    #         public.M('sites').where('name=?', (project_conf['pjname'].strip(),)).update(pdata)
    #
    #     return public.returnMsg(True, "恢复操作已执行")

    @staticmethod
    def _serializer_of_list(s: list, installed: List[str]) -> List[Dict]:
        return [{
            "version": v.version,
            "type": "stable",
            "installed": True if v.version in installed else False
        } for v in s]

    def list_py_version(self, get: public.dict_obj) -> Dict:
        """
        获取已安装的sdk，可安装的sdk
        """
        if self.pyvm is None:
            return public.returnMsg(False, "Python版本管理工具丢失")
        force = False
        if "force" in get and get.force in ("1", "true"):
            force = True
        self.pyvm.async_version = True
        res = self.pyvm.python_versions(force)
        # res["command_path"] += self._project_env_path_list()
        install_data = public.M("tasks").where("status in (0, -1) and name LIKE ?", ("安装[Python-%",)).select()

        install_version = []
        for i in install_data:
            install_version.append(i["name"].replace("安装[Python-", "").replace("]", ""))

        for i in res.get("sdk", {}).get("all", []):
            if i["version"] in install_version:
                i["is_install"] = True
            else:
                i["is_install"] = False

        for i in res.get("sdk", {}).get("streamline", []):
            if i["version"] in install_version:
                i["is_install"] = True
            else:
                i["is_install"] = False

        res.get("sdk", {}).get("all", []).sort(key=lambda x: (x["installed"], x["is_install"]), reverse=True)
        res.get("sdk", {}).get("streamline", []).sort(key=lambda x: (x["installed"], x["is_install"]), reverse=True)

        return res

    # def _project_env_path_list(self):
    #     site_list = public.M('sites').where('project_type=?', ('Python',)).select()
    #     if not isinstance(site_list, list):
    #         return []
    #     res = []
    #     paths = set()
    #     for site in site_list:
    #         conf = json.loads(site["project_config"])
    #         bin_path = os.path.join(conf["vpath"], "bin")
    #         paths.add(conf["vpath"])
    #         if not os.path.exists(bin_path):
    #             continue
    #         res.append({
    #             "python_path": bin_path,
    #             "type": "project",
    #             "project_name": site["name"],
    #             "is_pypy": os.path.exists(os.path.join(conf["vpath"], "is_pypy.pl"))
    #         })
    #
    #     for i in os.listdir(self._pyv_path):
    #         if i == "versions":
    #             continue
    #         if i.endswith("_backup"):
    #             continue
    #         if not i.endswith("_venv"):
    #             continue
    #         tmp_path = os.path.join(self._pyv_path, i)
    #         if tmp_path in paths:
    #             continue
    #         if not os.path.isdir(tmp_path):
    #             continue
    #
    #         res.append({
    #             "python_path": os.path.join(tmp_path, "bin"),
    #             "type": "project",
    #             "project_name": os.path.basename(tmp_path)[:-5],
    #             "is_pypy": os.path.exists(os.path.join(tmp_path, "is_pypy.pl"))
    #         })
    #
    #     return res

    @staticmethod
    def _parser_version(version: str) -> Optional[str]:
        v_rep = re.compile(r"(?P<target>\d+\.\d{1,2}(\.\d{1,2})?)")
        v_res = v_rep.search(version)
        if v_res:
            return v_res.group("target")
        return None

    # def set_python_version(self, get):
    #     try:
    #         env_type = get.env_type.strip()
    #         env_key = get.env_key.strip()
    #         if "is_pypy" in get:
    #             is_pypy = get.is_pypy.strip()
    #         else:
    #             is_pypy = False
    #     except AttributeError:
    #         return public.returnMsg(False, "参数错误")
    #
    #     if env_type == "project":
    #         python_path = "{}/{}_venv/bin".format(self._pyv_path, env_key)
    #         if not os.path.exists(python_path):
    #             project_conf = self._get_project_conf(env_key)
    #             if not project_conf:
    #                 return public.returnMsg(False, "没有指定项目")
    #             python_path = os.path.join(project_conf["vpath"], "bin")
    #     elif env_type == "clear":
    #         flag, msg = self.pyvm.set_python_path(None)
    #         return public.returnMsg(flag, msg)
    #     else:
    #         if is_pypy in ("1", "true"):
    #             python_path = os.path.join(self._pyv_path, "pypy_versions", env_key, "bin")
    #         else:
    #             python_path = os.path.join(self._pyv_path, "versions", env_key, "bin")
    #
    #     if not os.path.exists(python_path):
    #         return public.returnMsg(False, "没有指定的环境已丢失")
    #
    #     flag, msg = self.pyvm.set_python_path(python_path)
    #     if not flag:
    #         return public.returnMsg(False, msg)
    #     else:
    #         return public.returnMsg(True, "设置成功")

    def install_py_version(self, get: public.dict_obj) -> Dict:
        """
        安装一个版本的sdk
        """
        if self.pyvm is None:
            return public.returnMsg(False, "Python包管理器错误")
        version = self._parser_version(getattr(get, "version", ''))
        if version is None:
            return public.returnMsg(False, "版本参数信息错误")

        is_pypy = False
        if "is_pypy" in get and get.is_pypy in ("1", "true"):
            is_pypy = True

        log_path = self._logs_path + "/py.log"
        out_err = open(log_path, "w")
        self.pyvm.set_std(out_err, out_err)
        self.pyvm.is_pypy = is_pypy
        flag, msg = self.pyvm.api_install(version)
        self.pyvm.set_std(sys.stdout, sys.stderr)
        time.sleep(0.1)
        out_err.close()
        if not flag:
            return public.returnMsg(False, msg)

        return public.returnMsg(True, "安装成功")

    def async_install_py_version(self, get: public.dict_obj) -> Dict:
        if not os.path.exists("{}/class/projectModel/btpyvm.py".format(public.get_panel_path())):
            return public.returnMsg(False, "Python包管理器错误, 请尝试修复面板")

        version = self._parser_version(getattr(get, "version", ''))
        if os.path.exists("{}/versions/{}".format(self._pyv_path, version)):
            return public.returnMsg(False, "该版本已经安装")
        if public.M("tasks").where("status in (0, -1) and name=?", ("安装[Python-{}]".format(version),)).find():
            return public.returnMsg(False, "该版本的安装已加入任务队列, 请等待完成")
        extended = getattr(get, "extended", '')
        if version is None:
            return public.returnMsg(False, "版本参数信息错误")
        sh_str = "{}/pyenv/bin/python3 {}/class/projectModel/btpyvm.py install {} --extend='{}'".format(
            public.get_panel_path(), public.get_panel_path(), version, extended
        )

        if not os.path.exists("/tmp/panelTask.pl"):  # 如果当前任务队列并未执行，就把日志清空
            public.writeFile('/tmp/panelExec.log', '')
        task_id = public.M('tasks').add(
            'id,name,type,status,addtime,execstr',
            (None, '安装[Python-{}]'.format(version), 'execshell', '0', time.strftime('%Y-%m-%d %H:%M:%S'), sh_str))

        self._create_install_wait_msg(task_id, version)
        return public.returnMsg(True, "任务已添加到队列")

    @staticmethod
    def _create_install_wait_msg(task_id: int, version: str):
        from panel_msg.msg_file import message_mgr

        file_path = "/tmp/panelExec.log"
        if not os.path.exists(file_path):
            public.writeFile(file_path, "")

        soft_name = "Python-{}".format(version)
        data = {
            "soft_name": "Python-{}".format(version),
            "install_status": "等待安装" + soft_name,
            "file_name": file_path,
            "self_type": "soft_install",
            "status": 0,
            "task_id": task_id
        }
        title = "等待安装" + soft_name
        res = message_mgr.collect_message(title, ["Python版本管理", soft_name], data)
        if isinstance(res, str):
            public.WriteLog("消息盒子", "安装信息收集失败")
            return None

        return res

    def uninstall_py_version(self, get: public.dict_obj) -> Dict:
        """
        卸载一个指定版本的sdk
        """
        if self.pyvm is None:
            return public.returnMsg(False, "Python包管理器错误")
        version = self._parser_version(getattr(get, "version", ''))
        if version is None:
            return public.returnMsg(False, "版本参数信息错误")

        is_pypy = False
        if "is_pypy" in get and get.is_pypy in ("1", "true"):
            is_pypy = True

        self.pyvm.is_pypy = is_pypy
        flag, msg = self.pyvm.api_uninstall(version)
        if not flag:
            return public.returnMsg(False, msg)

        return public.returnMsg(True, "卸载成功")

    def update_all_project(self):
        all_project = public.M('sites').where('project_type=?', ('Python',)).select()
        if not isinstance(all_project, list):
            return
        for p in all_project:
            project_config = json.loads(p["project_config"])
            if project_config["stype"] == "python":
                project_config["project_cmd"] = "{vpath} -u {run_file} {parm} ".format(
                    vpath=self._get_vp_python(project_config["vpath"]),
                    run_file=project_config['rfile'],
                    parm=project_config['parm']
                )
                project_config["stype"] = "command"
                public.M("sites").where("id=?", (p["id"],)).update({"project_config": json.dumps(project_config)})

    @staticmethod
    def _read_requirement_file(requirement_path):
        requirement_dict = {}
        requirement_data = public.read_rare_charset_file(requirement_path)
        if isinstance(requirement_data, str):
            for i in requirement_data.split("\n"):
                tmp_data = i.strip()
                if not tmp_data or tmp_data.startswith("#"):
                    continue
                if re.search(r"-e\s+\.{0,2}/", tmp_data):  # 本地库依赖且为可编辑模式的不安装
                    continue
                if tmp_data.find("git+") != -1:
                    rep_name_list = [re.compile(r"#egg=(?P<name>\S+)"), re.compile(r"/(?P<name>\S+\.git)")]
                    name = tmp_data
                    for tmp_rep in rep_name_list:
                        tmp_name = tmp_rep.search(tmp_data)
                        if tmp_name:
                            name = tmp_name.group("name")
                            break
                    ver = tmp_data
                    for tmp_i in tmp_data.split():
                        if "git+" in tmp_i:
                            ver = tmp_i
                    requirement_dict[name] = ver

                elif tmp_data.find("file:") != -1:
                    file = tmp_data.split("file:", 1)[1]
                    name = os.path.basename(file)
                    requirement_dict[name] = file
                else:
                    if tmp_data.find("==") != -1:
                        n, v = tmp_data.split("==", 1)
                        requirement_dict[n.strip()] = v.strip()
                    else:
                        requirement_dict[tmp_data] = "--"
        return requirement_dict

    def get_env_info(self, get):
        force = False
        try:
            project_name = get.project_name.strip()
            if "force" in get:
                if isinstance(get.force, str):
                    if get.force in ("1", "true"):
                        force = True
                else:
                    force = bool(get.force)
        except:
            return public.returnMsg(False, "参数错误")

        project_info = self.get_project_find(project_name)
        if not isinstance(project_info, dict):
            return public.returnMsg(False, "没有找到项目")
        conf = project_info["project_config"]
        pyenv = EnvironmentManager().get_env_py_path(conf.get("python_bin", conf.get("vpath")))
        python_version = pyenv.version
        requirement_path = conf.get("requirement_path", "")

        if requirement_path and os.path.isfile(requirement_path):
            requirement_dict = self._read_requirement_file(requirement_path)
        else:
            requirement_dict = {}

        pip_list_data = pyenv.pip_list(force)
        pip_list = []
        for p, v in pip_list_data:
            if p in requirement_dict:
                pip_list.append({"name": p, "version": v, "requirement": requirement_dict.pop(p)})

            else:
                pip_list.append({"name": p, "version": v, "requirement": "--"})

        for k, v in requirement_dict.items():
            pip_list.append({"name": k, "version": "--", "requirement": v})

        return {
            "python_version": python_version,
            "requirement_path": requirement_path,
            "pip_list": pip_list,
            "pip_source": self.pip_source_dict
        }

    def modify_requirement(self, get):
        try:
            project_name = get.project_name.strip()
            requirement_path = get.requirement_path.strip()
        except:
            return public.returnMsg(False, "参数错误")

        project_info = self.get_project_find(project_name)
        if not isinstance(project_info, dict):
            return public.returnMsg(False, "没有找到项目")
        conf = project_info["project_config"]

        if not os.path.isfile(requirement_path):
            return public.returnMsg(False, "requirement.txt文件不存在")

        conf["requirement_path"] = requirement_path
        public.M("sites").where("id=?", (project_info["id"],)).update({"project_config": json.dumps(conf)})

        return public.returnMsg(True, "修改成功")

    def manage_package(self, get):
        """安装与卸载虚拟环境模块"""
        requirement_path = ""
        package_name = ''
        package_version = ''
        pip_source = "阿里云"
        active = "install"
        try:
            project_name = get.project_name.strip()
            if "package_name" in get and get.package_name.strip():
                package_name = get.package_name.strip()
            if "package_version" in get and get.package_version.strip():
                package_version = get.package_version.strip()
            if "requirement_path" in get and get.requirement_path.strip():
                requirement_path = get.requirement_path.strip()
            if "active" in get and get.active.strip():
                active = get.active.strip()
            if "pip_source" in get and get.pip_source.strip():
                pip_source = get.pip_source.strip()
                if pip_source not in self.pip_source_dict:
                    return public.returnMsg(False, "pip源错误")
        except:
            return public.returnMsg(False, "参数错误")
        log_file = "{}/pip_{}.log".format(self._logs_path, project_name)
        conf = self._get_project_conf(project_name)
        if not isinstance(conf, dict):
            return public.returnMsg(False, "没有该项目，请尝试刷新页面")

        pyenv = EnvironmentManager().get_env_py_path(conf.get("python_bin", conf.get("vpath", "")))
        if not pyenv:
            return public.returnMsg(False, "没有找到python环境")
        public.writeFile(log_file, "")

        if self.prep_status(conf) == "running":
            return public.returnMsg(False, "项目环境安装制作中.....<br>请勿操作")

        if not (package_name or requirement_path):
            return public.returnMsg(False, "参数错误")

        if requirement_path:
            if not os.path.isfile(requirement_path):
                return public.returnMsg(False, "依赖包记录文件不存在")

        if active not in ("install", "uninstall"):
            return public.returnMsg(False, "操作参数错误")

        real_pip_source = self.pip_source_dict[pip_source]
        pyenv.set_pip_source(real_pip_source)
        log_file = "{}/pip_{}.log".format(self._logs_path, project_name)
        log_fd = open(log_file, "w")
        def call_log(log: str) -> None:
            if not log.endswith("\n"):
                log += "\n"
            log_fd.write(log)
            log_fd.flush()

        if requirement_path:
            conf["requirement_path"] = requirement_path
            public.M("sites").where("name=?", (project_name,)).update({"project_config": json.dumps(conf)})
            self.install_requirement(conf, pyenv, call_log)
            log_fd.write("|-安装结束\n")
            log_fd.close()
            return public.returnMsg(True, "安装结束")

        if active == "install":
            res = pyenv.pip_install(package_name, version=package_version, call_log=call_log)
            log_fd.write("|-安装结束\n")
            log_fd.close()
            if res is None:
                return public.returnMsg(True, "安装成功")
            else:
                return public.returnMsg(False, "安装失败")
        else:
            if package_name == "pip":
                return public.returnMsg(False, "PIP不能卸载....")
            res = pyenv.pip_uninstall(package_name, call_log=call_log)
            log_fd.write("|-卸载结束\n")
            log_fd.close()
            if res is None:
                return public.returnMsg(True, "卸载成功")
            else:
                return public.returnMsg(False, "卸载失败")


    # ————————————————————————————————————
    #              虚拟终端               |
    # ————————————————————————————————————

    def set_export(self, project_name):
        conf = self._get_project_conf(project_name)
        if not conf:
            return False, "没有该项目\r\n"
        v_path_bin = conf["vpath"] + "/bin"
        if not os.path.exists(conf["path"]):
            return False, "项目文件丢失\r\n"
        if not os.path.exists(v_path_bin):
            return False, "没有该虚拟环境\r\n"
        pre_v_path_bin = self.__prevent_re(v_path_bin)
        msg = "虚拟环境已就绪！"  # 使用中文的感叹号
        _cd_sh = "clear\ncd %s\n" % conf["path"]
        _sh = 'if [[ "$PATH" =~ "^%s:.*" ]]; then { echo "%s"; } else { export PATH="%s:${PATH}"; echo "%s"; } fi\n' % (
            pre_v_path_bin, msg, v_path_bin, msg
        )
        return True, _sh + _cd_sh

    def get_port_status(self, get):
        try:
            conf = self.get_project_find(get.project_name.strip())
            if not conf:
                return json_response(False, "未找到项目")
        except:
            return json_response(False, '参数错误')

        pids = self.get_project_run_state(get.project_name.strip())
        if not pids:
            return json_response(False, "项目未启动")

        ports = []
        for pid in pids:
            try:
                p = psutil.Process(pid)
                for i in p.connections():
                    if conf["project_config"]["stype"] != "command" and str(i.laddr.port) != conf["project_config"]["port"]:
                        continue

                    if i.status == "LISTEN" and i.laddr.port not in ports:
                        ports.append(str(i.laddr.port))
            except:
                pass

        if not ports:
            return json_response(False, "未找到端口")

        # 初始化结果字典
        res: Dict[str, Dict] = {str(i): {
            "port": i,
            "fire_wall": None,
            "nginx_proxy": None,
        } for i in ports}

        # 获取端口规则列表
        from firewallModel.comModel import main
        port_list = main().port_rules_list(get)['data']

        # 更新防火墙信息
        for i in port_list:
            if str(i["Port"]) in res:
                res[str(i["Port"])]['fire_wall'] = i
        try:
            # 读取配置文件
            file_path = "{}/nginx/python_{}.conf".format(self._vhost_path, get.project_name)
            config_file = public.readFile(file_path)

            # 匹配 location 块
            rep_location = re.compile(r"\s*location\s+([=*~^]*\s+)?/\s*{")
            tmp = rep_location.search(config_file)

            # 找到 location 块结束位置
            end_idx = self.find_nginx_block_end(config_file, tmp.end() + 1)
            if not end_idx:
                return json_response(True, data=res)
            block = config_file[tmp.start():end_idx]
            # 获取 proxy_pass 配置
            res_pass = re.compile(r"proxy_pass\s+(?P<pass>\S+)\s*;", re.M)
            res_pass_res = res_pass.search(block)

            # 解析端口信息
            res_url = parse_url(res_pass_res.group("pass"))

            # 更新 nginx_proxy 信息
            for i in res:
                if i == str(res_url.port):
                    res[i]['nginx_proxy'] = {
                        "proxy_dir": "/",
                        "status": True,
                        "site_name": get.project_name,
                        "proxy_port": i
                    }

            return json_response(True, "获取成功", data=list(res.values()))
        except:
            return json_response(True, "获取成功", data=list(res.values()))

    @staticmethod
    def _project_domain_list(project_id: int):
        return public.M('domain').where('pid=?', (project_id,)).select()

    # 添加代理
    def add_server_proxy(self, get):
        if not hasattr(get, "site_name") or not get.site_name.strip():
            return json_response(status=False, msg="参数错误")

        project_data = self.get_project_find(get.site_name)
        if not project_data:
            return json_response(False, "未找到项目")

        if not hasattr(get, "proxy_port"):
            return json_response(status=False, msg="参数错误")
        else:
            if 65535 < int(get.proxy_port) < 0:
                return json_response(False, "请输入正确的端口范围")

        if not hasattr(get, "status"):
            return json_response(status=False, msg="参数错误")

        file_path = "{}/nginx/python_{}.conf".format(self._vhost_path, get.site_name)
        config_file = public.readFile(file_path)
        if not isinstance(config_file, str):
            return json_response(False, "未找到配置文件")

        if int(get.status):
            self.set_config(get.site_name, is_modify=True, proxy_port=get.proxy_port)
        else:
            is_modify = "close" if project_data["project_config"]["stype"] != "command" else False
            self.set_config(get.site_name, is_modify=is_modify)

        return json_response(status=True, msg="成功更新代理配置")

    @staticmethod
    def find_nginx_block_end(data: str, start_idx: int) -> Optional[int]:
        if len(data) < start_idx + 1:
            return None

        level = 1
        line_start = 0
        for i in range(start_idx + 1, len(data)):
            if data[i] == '\n':
                line_start = i + 1
            if data[i] == '{' and line_start and data[line_start: i].find("#") == -1:  # 没有注释的下一个{
                level += 1
            elif data[i] == '}' and line_start and data[line_start: i].find("#") == -1:  # 没有注释的下一个}
                level -= 1
            if level == 0:
                return i

        return None


class PyenvSshTerminal(ssh_terminal.ssh_terminal):
    _set_python_export = None

    def send(self):
        '''
            @name 写入数据到缓冲区
            @author hwliang<2020-08-07>
            @return void
        '''
        try:
            while self._ws.connected:
                if self._s_code:
                    time.sleep(0.1)
                    continue
                client_data = self._ws.receive()
                if not client_data: continue
                if client_data == '{}': continue
                if len(client_data) > 10:
                    if client_data.find('{"host":"') != -1:
                        continue
                    if client_data.find('"resize":1') != -1:
                        self.resize(client_data)
                        continue
                    if client_data.find('{"pj_name"') != -1:
                        client_data = self.__set_export(client_data)
                        if not client_data:
                            continue

                self._ssh.send(client_data)
        except Exception as ex:
            ex = str(ex)

            if ex.find('_io.BufferedReader') != -1:
                self.debug('从websocket读取数据发生错误，正在重新试')
                self.send()
                return
            elif ex.find('closed') != -1:
                self.debug('会话已中断')
            else:
                self.debug('写入数据到缓冲区发生错误: {}'.format(ex))

        if not self._ws.connected:
            self.debug('客户端已主动断开连接')
        self.close()

    def __set_export(self, client_data):
        _data = json.loads(client_data)
        flag, msg = main().set_export(_data["pj_name"])
        if not flag:
            self._ws.send(msg)
            return None
        return msg
