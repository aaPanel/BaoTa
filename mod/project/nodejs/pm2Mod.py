# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------
import json
import os
import re
# ------------------------------
# pm2项目功能模型
# ------------------------------
import sys
import datetime
from typing import Dict, List, Tuple

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

os.chdir("/www/server/panel")
import public

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")
from mod.project.nodejs.base import NodeJs


class main(NodeJs):

    def __init__(self):
        super(main, self).__init__()

    # 2024/7/11 下午8:07 获取pm2的监控数据
    def get_pm2_monit(self, get):
        '''
            @name 获取pm2的监控数据
        '''
        try:
            self.set_project_model("pm2")
            get_jlist = self.projectModel.get_jlist()
            if len(get_jlist) == 0:
                return public.returnResult(True, '', data=[], code=0)

            import pwd
            data = []
            cluster_mode = {}

            for jl in get_jlist:
                if jl.get("name") in ("pm2-sysmonit", "pm2-logrotate"):
                    continue

                try:
                    user = pwd.getpwuid(jl.get("pm2_env").get("uid")).pw_name
                except:
                    user = jl.get("pm2_env").get("USER")

                tmp = {
                    "mode": jl.get("pm2_env").get("exec_mode"),
                    "id": jl.get("pm_id"),
                    "pid": jl.get("pid"),
                    "name": jl.get("name"),
                    "user": user,
                    "restart": jl.get("pm2_env").get("restart_time"),
                    "uptime": jl.get("pm2_env").get("pm_uptime"),
                    "cpu": str(jl.get("monit").get("cpu")),
                    "memory": jl.get("monit").get("memory"),
                    "auto_restart": jl.get("pm2_env").get("autorestart"),
                    "status": jl.get("pm2_env").get("status"),
                    "pm2_env": jl.get("pm2_env"),
                }
                if jl.get("pm2_env").get("exec_mode") == "fork_mode":
                    if len(cluster_mode) != 0:
                        data.append(cluster_mode)
                        cluster_mode = {}
                    data.append(tmp)
                elif jl.get("pm2_env").get("exec_mode") == "cluster_mode":
                    if len(cluster_mode) == 0:
                        tmp["mode"] = "fork_mode"
                        cluster_mode["name"] = jl.get("name")
                        cluster_mode["user"] = user
                        cluster_mode["uptime"] = jl.get("pm2_env").get("pm_uptime")
                        cluster_mode["mode"] = jl.get("pm2_env").get("exec_mode")
                        cluster_mode["status"] = jl.get("pm2_env").get("status")
                        cluster_mode["data"] = []
                        cluster_mode["data"].append(tmp)
                        continue

                    if cluster_mode.get("name") == jl.get("name") or jl.get("pm2_env").get("NODE_PROJECT_NAME") == cluster_mode.get("name"):
                        tmp["mode"] = "fork_mode"
                        cluster_mode["data"].append(tmp)
                        if jl.get("pm2_env").get("status") == "online" and cluster_mode["status"] != "online":
                            cluster_mode["status"] = "online"
                    else:
                        data.append(cluster_mode)
                        cluster_mode = {}
                        tmp["mode"] = "fork_mode"
                        cluster_mode["name"] = jl.get("name")
                        cluster_mode["user"] = user
                        cluster_mode["uptime"] = jl.get("pm2_env").get("pm_uptime")
                        cluster_mode["mode"] = jl.get("pm2_env").get("exec_mode")
                        cluster_mode["status"] = jl.get("pm2_env").get("status")
                        cluster_mode["data"] = []
                        cluster_mode["data"].append(tmp)

            if len(cluster_mode) != 0:
                data.append(cluster_mode)

            return public.returnResult(True, '', data=data, code=0)
        except:
            return public.returnResult(False, '获取pm2监控数据失败', code=5)

    def get_pm2_cmd(self, version: str = None):
        if version is None:
            import PluginLoader
            nodejs_version = PluginLoader.plugin_run("nodejs", "get_default_env", None)
        else:
            nodejs_version = version
        if nodejs_version is None:
            return None
        args = public.dict_obj()
        args.nodejs_version = nodejs_version
        self.set_pm2_cmd(args.nodejs_version)

    # 2024/7/9 下午12:07 获取pm2的所有进程列表
    def get_jlist(self, loop: bool = False):
        '''
            @name 获取pm2的所有进程列表
        '''
        try:
            self.get_pm2_cmd()
            if self.pm2_cmd is None:
                args = public.dict_obj()
                nodejs_versions = self.get_nodejs_version(args)
                if nodejs_versions:
                    nodejs_versions = sorted(nodejs_versions, key=self.version_key, reverse=True)
                    self.get_pm2_cmd(nodejs_versions[0])
                else:
                    return []

                if self.pm2_cmd is None:
                    return []

            stdout, stderr = public.ExecShell("export HOME=/root;{} jlist".format(self.pm2_cmd))
            if stderr:
                return []

            return json.loads(stdout)
        except:
            try:
                args = public.dict_obj()
                nodejs_versions = self.get_nodejs_version(args)
                if nodejs_versions:
                    nodejs_versions = sorted(nodejs_versions, key=self.version_key, reverse=True)
                    self.get_pm2_cmd(nodejs_versions[0])
                else:
                    return []

                if self.pm2_cmd is None:
                    return []

                stdout, stderr = public.ExecShell("export HOME=/root;{} jlist".format(self.pm2_cmd))
                if stderr:
                    return []

                return json.loads(stdout)
            except:
                return []

    # 2024/7/11 下午5:38 获取指定pm2项目的日志
    def get_logs(self, mode: str = None, id: str = None, name: str = None, log_type: str = "all", *args, **kwargs):
        '''
            @name 获取指定pm2项目的日志
        '''
        if log_type != "all":
            log_type = "--{}".format(log_type)
        else:
            log_type = ""

        self.get_pm2_cmd()
        if self.pm2_cmd is None:
            return public.returnResult(False, '未检测到pm2，请先安装pm2或切换node版本后再试', code=5)
        if mode == "fork_mode":
            stdout, stderr = public.ExecShell("sudo {} logs {} --lines 100 {} --nostream".format(self.pm2_cmd, id, log_type))
        elif mode == "cluster_mode":
            stdout, stderr = public.ExecShell(
                "sudo {} logs {} --lines 100 {} --nostream".format(self.pm2_cmd, name, log_type))
        else:
            return public.returnResult(False, 'mode参数错误', code=5)
        if stderr and "sudo:" not in stderr:
            return public.returnResult(False, stderr, code=5)
        return public.returnResult(True, '', data=stdout, code=0)

    # 2024/7/11 下午5:55 重启pm2项目
    def restart(self, mode: str = None, id: str = None, name: str = None, project_name: str = None, *args, **kwargs):
        '''
            @name 重启pm2项目
        '''
        self.get_pm2_cmd()
        if self.pm2_cmd is None:
            return public.returnResult(False, '未检测到pm2，请先安装pm2或切换node版本后再试', code=5)

        projects = self.get_jlist()
        for project in projects:
            if project.get("name") == name or project.get("pm2_env", {}).get("NODE_PROJECT_NAME") == name:
                name = project.get("name")

        if mode == "fork_mode":
            stdout, stderr = public.ExecShell("sudo {} restart {}".format(self.pm2_cmd, id))
        elif mode == "cluster_mode":
            stdout, stderr = public.ExecShell("sudo {} restart {}".format(self.pm2_cmd, name))
        else:
            return public.returnResult(False, 'mode参数错误', code=5)

        if stderr and "sudo:" not in stderr:
            return public.returnResult(False, stderr, code=5)
        return public.returnResult(True, "重启成功", code=0)

    # 2024/7/11 下午5:56 停止pm2项目
    def stop(self, mode: str = None, id: str = None, name: str = None, project_name: str = None, *args, **kwargs):
        '''
            @name 停止pm2项目
        '''
        self.get_pm2_cmd()
        if self.pm2_cmd is None:
            return public.returnResult(False, '未检测到pm2，请先安装pm2或切换node版本后再试', code=5)
        projects = self.get_jlist()
        for project in projects:
            if project.get("name") == name or project.get("pm2_env", {}).get("NODE_PROJECT_NAME") == name:
                name = project.get("name")

        if mode == "fork_mode":
            stdout, stderr = public.ExecShell("sudo {} stop {}".format(self.pm2_cmd, id))
        elif mode == "cluster_mode":
            stdout, stderr = public.ExecShell("sudo {} stop {}".format(self.pm2_cmd, name))
        else:
            return public.returnResult(False, 'mode参数错误', code=5)
        # 忽略无效警告
        if stderr and "sudo:" not in stderr:
            return public.returnResult(False, stderr, code=5)
        return public.returnResult(True, "停止成功", code=0)

    # 2024/7/11 下午5:56 启动pm2项目
    def start(self, mode: str = None, id: str = None, name: str = None, project_name: str = None, *args, **kwargs):
        '''
            @name 启动pm2项目
        '''
        self.get_pm2_cmd()
        if self.pm2_cmd is None:
            return public.returnResult(False, '未检测到pm2，请先安装pm2或切换node版本后再试', code=5)

        get = public.dict_obj()
        get.project_name = project_name
        return self.start_project(get)

    # 2024/7/11 下午5:56 删除pm2项目
    def delete(self, mode: str = None, id: str = None, name: str = None, *args, **kwargs):
        '''
            @name 删除pm2项目
        '''
        self.get_pm2_cmd()
        if self.pm2_cmd is None:
            return public.returnResult(False, '未检测到pm2，请先安装pm2或切换node版本后再试', code=5)

        if mode == "fork_mode":
            stdout, stderr = public.ExecShell("{} delete {}".format(self.pm2_cmd, id))
        elif mode == "cluster_mode":
            stdout, stderr = public.ExecShell("{} delete {}".format(self.pm2_cmd, name))
        else:
            return public.returnResult(False, 'mode参数错误', code=5)

        if stderr:
            return public.returnResult(False, stderr, code=5)
        return public.returnResult(True, "删除成功", code=0)

    # 2024/7/18 下午6:00 从指定ecosystem.config删除pm2
    def delete_for_ecosystem(self, nodejs_version, config_file):
        '''
            @name 从指定ecosystem.config删除pm2
            @param config_file: string 配置文件路径
        '''
        self.set_pm2_cmd(nodejs_version)
        if not os.path.exists(config_file):
            return public.returnResult(False, '指定项目配置文件不存在', code=5)
        if not os.path.isfile(config_file):
            return public.returnResult(False, '指定项目配置文件不是一个文件', code=5)

        stdout, stderr = public.ExecShell("sudo {} delete {}".format(self.pm2_cmd, config_file))
        if stderr and "sudo:" not in stderr:
            return public.returnResult(False, stderr, code=5)
        return public.returnResult(True, "删除成功", code=0)

    # 2024/7/18 下午6:03 从指定ecosystem.config启动pm2
    def start_for_ecosystem(self, nodejs_version, config_file):
        '''
            @name 从指定ecosystem.config启动pm2
            @param config_file: string 配置文件路径
        '''
        self.set_pm2_cmd(nodejs_version)
        if not os.path.exists(config_file):
            return public.returnResult(False, '指定项目配置文件不存在', code=5)
        if not os.path.isfile(config_file):
            return public.returnResult(False, '指定项目配置文件不是一个文件', code=5)

        stdout, stderr = public.ExecShell("sudo {} start {}".format(self.pm2_cmd, config_file))
        if stderr and "sudo:" not in stderr:
            return public.returnResult(False, stderr, code=5)
        return public.returnResult(True, "启动成功", code=0)

    # 2024/7/11 下午2:44 创建项目
    def create_project(self, get):
        '''
            @name 创建项目
            @param get: dict_obj {}
                    get.project_type string 项目类型 nodejs/pm2/general 必传
                    get.project_name string 项目名称 my_project 必传
                    get.nodejs_version string node版本 v20.15.0 必传
                    get.project_file string 项目启动文件 /www/wwwroot/my_project/server.js 自定义添加时必传
                    get.project_cwd string 项目路径 /www/wwwroot/my_project 自定义添加时必传
                    get.cluster int 实例数量 1 必传，默认1
                    get.max_memory_limit int 最大内存限制 1024 必传，默认1024，mb
                    get.watch 自动重载 bool True/False 必传，默认False
                    get.pkg_manager string 包管理器 none/npm/yarn/pnpm/... 必传，默认none
                    get.not_install_pkg bool 是否安装依赖包 True/False 非必传
                    get.run_user string 运行用户 www/root/... 必传
                    get.config_file string 配置文件路径 /www/wwwroot/remix_app/ecosystem.config.cjs 配置文件方式添加时必传
                    get.config_body string 配置文件内容 非必传 可以单独传config_body，如果选了config_file，这里就是必传，也要传config_body
                    get.port string 端口 4001 非必传
                    get.release_firewall bool 是否放行防火墙 True/False 非必传
                    get.is_power_on bool 是否开机启动 True/False 非必传
                    get.bind_extranet bool 是否绑定外网 True/False 依赖于get.port 非必传
                    get.domains list 域名列表 ["www.bt.cn", "bt.cn", ...] 非必传
                    get.project_ps string 备注 ps 非必传
        '''
        self.set_self_get(get)
        self.set_def_name(get.def_name)
        get.config_file = get.get("config_file", "")
        get.config_body = get.get("config_body", "")
        get.project_cwd = get.get("project_cwd", "")
        get.project_file = get.get("project_file", "")
        get.add_type = get.get("add_type/d", 0)

        if get.config_file != "" or get.config_body != "":
            get.add_type = 1
            if get.config_file != "":
                if not os.path.exists(get.config_file):
                    self.ws_err_exit(False, '{} 指定项目配置文件不存在'.format(get.config_file), code=2)
                if not os.path.isfile(get.config_file):
                    self.ws_err_exit(False, '{} 指定项目配置文件不是一个文件'.format(get.config_file), code=2)
            if get.config_body == "":
                if get.config_file != "":
                    get.config_body = public.readFile(get.config_file)
                if get.config_body == "":
                    self.ws_err_exit(False, '{} 配置文件格式错误，请检查'.format(get.config_file), code=2)
                if not "module.exports" in get.config_body and not "apps:" in get.config_body:
                    self.ws_err_exit(False, '{} 配置文件格式错误，请检查'.format(get.config_file), code=2)
        else:
            if get.project_file == "":
                self.ws_err_exit(False, 'project_file参数不能为空', code=2)
            if not os.path.exists(get.project_file):
                self.ws_err_exit(False, '{} 指定项目启动文件不存在'.format(get.project_file), code=2)
            if not os.path.isfile(get.project_file):
                self.ws_err_exit(False, '{} 指定项目启动文件不是一个文件'.format(get.project_file), code=2)

        if get.project_cwd == "":
            self.ws_err_exit(False, 'project_cwd参数不能为空', code=2)
        if not os.path.exists(get.project_cwd):
            self.ws_err_exit(False, '{} 指定项目目录不存在'.format(get.project_cwd), code=2)
        if not os.path.isdir(get.project_cwd):
            self.ws_err_exit(False, '{} 指定项目目录不是一个目录'.format(get.project_cwd), code=2)

        get.project_name = get.get("project_name", None)
        get.pm2_name = get.project_name
        if get.project_name is None:
            self.ws_err_exit(False, 'project_name参数不能为空', code=2)
        get.project_name = public.xssencode2(get.project_name)
        get.project_type = get.get("project_type", None)
        if get.project_type is None:
            self.ws_err_exit(False, 'project_type参数不能为空', code=2)
        if get.project_type != "pm2":
            self.ws_err_exit(False, '此模型仅支持general项目', code=2)
        get.run_user = get.get("run_user", "www")
        get.project_args = get.get("project_args", "")
        get.env = get.get("env", "")
        if get.env != "":
            env = get.env.split("\n")
            for e in env:
                if not "=" in e:
                    self.ws_err_exit(False, "环境变量: {} 格式错误，请重新输入例如：key=value".format(e), code=2)

        self.set_pm2_cmd(get.nodejs_version)
        if self.pm2_cmd is None:
            self.ws_err_exit(False, "请先在【node {}】中安装pm2后再创建".format(get.nodejs_version), code=2)

        get.not_install_pkg = get.get("not_install_pkg", False)
        get.release_firewall = get.get("release_firewall", False)
        get.is_power_on = get.get("is_power_on", True)
        get.max_memory_limit = get.get("max_memory_limit", 1024)
        get.max_memory_restart = "{}M".format(get.max_memory_limit)
        get.project_ps = get.get("project_ps", "")

        get.watch = get.get("watch", False)
        get.cluster = get.get("cluster/d", 1)

        package_file = "{}/package.json".format(get.project_cwd)
        get.package_info = {}
        if os.path.exists(package_file):
            try:
                get.package_info = json.loads(public.readFile(package_file))
            except:
                pass

        if get.package_info:
            self.check_node_version(get)
            if not get.not_install_pkg:
                from mod.project.nodejs.packageManage import PackageManage
                PackageManage().install_package(get=get, manager=get.pkg_manager, path=get.project_cwd)

        if get.config_file != "" and get.config_body != "":
            # config_body = public.readFile(get.config_file)
            if not "module.exports" in get.config_body and not "apps:" in get.config_body:
                self.ws_err_exit(False, '{} 配置文件格式错误，请检查'.format(get.config_file), code=2)

            self.structure_ecosystem_for_config_body(get)
        else:
            self.structure_ecosystem(get)
            # 临时补丁实际上疑似存在问题 project_file 不是 pm2配置文件？
            project_file_body = public.readFile(get.project_file)
            if "module.exports" in project_file_body and "apps:" in project_file_body:
                name_re = re.compile(r'name:.*?,')
                name = name_re.search(project_file_body).group()
                get.pm2_name = name.split(":")[1].strip().replace("'", "").replace('"', "").replace(",", "")

        get._ws.send(json.dumps(self.wsResult(True, "正在构造启动脚本...", code=0)))
        self.structure_start_script(get)
        get._ws.send(json.dumps(self.wsResult(True, "启动脚本构造完成.", code=0)))
        get._ws.send(json.dumps(self.wsResult(True, "正在写入项目必要配置文件...", code=1)))
        project_id = self.create_site(get)
        if project_id is None:
            self.ws_err_exit(False, '创建网站失败，无法正常写入数据库，请尝试重新添加！', code=2)
        self.set_config(get.project_name)
        get._ws.send(json.dumps(self.wsResult(True, "配置文件写入完成.\r\n正在启动项目...", code=1)))
        start_result = self.start_project(get)
        if not start_result["status"]:
            self.ws_err_exit(False, start_result["msg"] if "msg" in start_result else start_result["error_msg"], code=5)
        get._ws.send(json.dumps(self.wsResult(True, "项目创建成功!", code=-1)))
        get._ws.close()

    # 2024/7/16 上午9:31 从config_body构造 ecosystem
    def structure_ecosystem_for_config_body(self, get):
        '''
            @name 从config_body构造 ecosystem
        '''
        log_path = os.path.join(self.pm2_logs_path, get.project_name)
        if not os.path.exists(log_path):
            os.makedirs(log_path, 493, True)
        out_file = os.path.join(str(log_path), "out.log")
        if os.path.exists(out_file) and os.path.isfile(out_file):
            public.writeFile(out_file, "")
        err_file = os.path.join(str(log_path), "err.log")
        if os.path.exists(err_file) and os.path.isfile(err_file):
            public.writeFile(err_file, "")

        public.ExecShell("chown -R {user}:{user} {project_cwd}".format(user=get.run_user, project_cwd=log_path))
        public.ExecShell("chmod 755 -R {}".format(log_path))
        public.set_own(out_file, get.run_user, get.run_user)
        public.set_mode(out_file, 755)
        public.set_own(err_file, get.run_user, get.run_user)
        public.set_mode(err_file, 755)

        user_field = "user: '{}',".format(get.run_user)
        cwd_field = 'cwd: "{}",'.format(get.project_cwd)
        out_file_field = 'out_file: "{}",'.format(out_file)
        error_file_field = 'error_file: "{}",'.format(err_file)
        log_date_format_field = 'log_date_format: "YYYY-MM-DD HH:mm:ss",'
        merge_logs_field = 'merge_logs: true,'

        name_re = re.compile(r'name:.*?,')
        name = name_re.search(get.config_body).group()
        get.pm2_name = name.split(":")[1].strip().replace("'", "").replace('"', "").replace(",", "")

        user_re = re.compile(r'user:.*?,')
        cwd_re = re.compile(r'cwd:.*?,')
        out_file_re = re.compile(r'out_file:.*?,')
        error_file_re = re.compile(r'error_file:.*?,')
        log_date_format_re = re.compile(r'log_date_format:.*?,')
        merge_logs_re = re.compile(r'merge_logs:.*?,')

        get.config_body = self.replace_or_add_field(get.config_body, user_re, user_field)
        get.config_body = self.replace_or_add_field(get.config_body, cwd_re, cwd_field)
        get.config_body = self.replace_or_add_field(get.config_body, out_file_re, out_file_field)
        get.config_body = self.replace_or_add_field(get.config_body, error_file_re, error_file_field)
        get.config_body = self.replace_or_add_field(get.config_body, log_date_format_re, log_date_format_field)
        get.ecosystem = self.replace_or_add_field(get.config_body, merge_logs_re, merge_logs_field)

    # 2024/7/15 下午3:19 构造 ecosystem
    def structure_ecosystem(self, get):
        '''
            @name 构造 ecosystem
        '''
        log_path = os.path.join(self.pm2_logs_path, get.project_name)
        if not os.path.exists(log_path):
            os.makedirs(log_path, 493, True)
        out_file = os.path.join(str(log_path), "out.log")
        if os.path.exists(out_file) and os.path.isfile(out_file):
            public.writeFile(out_file, "")
        err_file = os.path.join(str(log_path), "err.log")
        if os.path.exists(err_file) and os.path.isfile(err_file):
            public.writeFile(err_file, "")

        public.ExecShell("chown -R {user}:{user} {project_cwd}".format(user=get.run_user, project_cwd=log_path))
        public.ExecShell("chmod 755 -R {}".format(log_path))
        public.set_own(out_file, get.run_user, get.run_user)
        public.set_mode(out_file, 755)
        public.set_own(err_file, get.run_user, get.run_user)
        public.set_mode(err_file, 755)

        exec_mode = "\"fork\","
        instances = ""
        if get.cluster > 1:
            exec_mode = "\"cluster\","
            instances = "\n            instances: \"{instances}\",".format(instances=get.cluster)

        env = ""
        if get.env != "":
            env = "\n            env: {env},".format(env=json.dumps(dict([i.split("=") for i in get.env.split("\n")])))
        get.ecosystem = '''module.exports = {{
    apps: [
        {{
            name: "{project_name}",
            namespace: "{project_name}",
            max_memory_restart: "{max_memory_restart}",
            user: "{run_user}",
            exec_mode: {exec_mode}{instances}{env}
            cwd: "{project_cwd}",
            script: "{project_file}",
            args: "{project_args}",
            watch: {watch},
            out_file: {out_file},
            error_file: {error_file},
            log_date_format: "YYYY-MM-DD HH:mm:ss",
            merge_logs: true,
            interpreter: "{project_node}",
        }}
    ]
}}'''.format(
            project_name=get.project_name,
            max_memory_restart=get.max_memory_restart,
            run_user=get.run_user,
            exec_mode=exec_mode,
            instances=instances,
            env=env,
            project_cwd=get.project_cwd,
            project_file=get.project_file,
            project_args=get.project_args,
            watch="true" if get.watch else "false",
            out_file="\"{}/out.log\"".format(log_path),
            error_file="\"{}/err.log\"".format(log_path),
            project_node="/www/server/nodejs/{}/bin/node".format(get.nodejs_version),
        )

    # 2024/7/13 上午10:21 构造传统项目的启动脚本
    def structure_start_script(self, get):
        '''
            @name 构造传统项目的启动脚本
        '''
        last_env = self.get_last_env(get.nodejs_version)
        command = '''{last_env}
export NODE_PROJECT_NAME="{project_name}"
export HOME=/root
cd {project_cwd}
{pm2_cmd} start {ecosystem_config_file}'''.format(
            last_env=last_env,
            project_name=get.project_name,
            project_cwd=get.project_cwd,
            ecosystem_config_file=get.project_file,
            pm2_cmd=self.pm2_cmd,
        )

        get.config_file = get.project_file
        get.config_body = get.ecosystem
        get.project_script = command

    # 2024/7/13 上午10:12 启动项目
    def start_project(self, get):
        '''
            @name 启动项目
        '''
        # 检测pm2项目已存在,则先停止
        self.stop_project(get)

        project_find = self.get_project_find(get.project_name)
        if not project_find: return public.returnResult(False, "项目不存在", code=5)

        project_find = self.get_project_find(get.project_name)
        if project_find['edate'] != "0000-00-00" and project_find['edate'] < datetime.datetime.today().strftime("%Y-%m-%d"):
            return public.returnResult(False, "当前项目已过期，请重新设置项目到期时间", code=5)

        self._update_project(get.project_name, project_find)
        if not os.path.exists(project_find['path']):
            error_msg = '启动失败，Nodejs项目{}，运行目录{}不存在!'.format(get.project_name, project_find['path'])
            public.WriteLog(self.log_name, error_msg)
            return public.returnResult(False, error_msg, code=5)

        # 前置准备
        project_script = project_find['project_config']['project_script'].strip().replace('  ', ' ')
        log_file = "{}/{}.log".format(project_find['project_config']["log_path"], project_find["name"])
        if not project_script: return public.returnResult(True, "未配置启动脚本")

        public.writeFile(log_file, '')
        public.ExecShell('chmod 777 {}'.format(log_file))
        # 生成启动脚本
        start_cmd = project_script
        script_file = "{}/{}.sh".format(self.node_run_scripts, get.project_name)
        public.writeFile(script_file, start_cmd)

        # 执行脚本文件
        stdout, stderr = public.ExecShell("bash {}".format(script_file), env=os.environ.copy())
        public.writeFile(log_file, stdout + stderr)

        if stderr:
            return public.returnResult(False, '启动失败: {}'.format(stderr), code=5)

        self.start_by_user(project_find["id"])
        return public.returnResult(True, '启动成功')

    # 2024/7/12 上午9:58 停止项目
    def stop_project(self, get):
        '''
            @name 停止项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        project_find = self.get_project_find(get.project_name)
        if not project_find: return public.returnResult(False, '项目不存在', code=5)
        if project_find['edate'] != "0000-00-00" and project_find['edate'] < datetime.datetime.today().strftime("%Y-%m-%d"):
            return public.returnResult(False, '当前项目已过期，请重新设置项目到期时间', code=5)
        project_script = project_find['project_config']['project_script'].strip().replace('  ', ' ')
        project_script = project_script.replace('pm2 start', 'pm2 stop')
        stdout, stderr = public.ExecShell(project_script)
        public.writeFile("{}/{}.log".format(project_find['project_config']["log_path"], project_find["name"]),
                         stdout + stderr)
        if stderr:
            return public.returnResult(False, '停止失败: {}'.format(stderr), code=5)
        return public.returnResult(True, '停止成功')

    # 2024/7/17 上午11:09 重启项目
    def restart_project(self, get):
        '''
            @name 重启项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return
        '''
        project_find = self.get_project_find(get.project_name)
        if project_find:
            if project_find['edate'] != "0000-00-00" and project_find['edate'] < datetime.datetime.today().strftime("%Y-%m-%d"):
                return public.returnResult(False, '当前项目已过期，请重新设置项目到期时间', code=5)
        res = self.stop_project(get)
        if not res['status']: return res
        res = self.start_project(get)
        if not res['status']: return res
        return public.returnResult(True, '重启成功')
