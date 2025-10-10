import itertools
import json
import re
import shutil
import sys
import os
import time
import traceback
import threading
from datetime import datetime

import psutil
from typing import Dict, List, Optional, Union, Any

from crontab_ssl import dict_obj
from mod.base import json_response
from mod.base.backup_tool import VersionTool
from mod.project.java import utils
from mod.base.process import RealUser, RealProcess

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public
from public import dict_obj as Get
from projectModel.watchModel import use_project_watch, add_project_watch, del_project_watch
from mod.base.web_conf import normalize_domain, is_domain, Redirect, remove_sites_service_config, RealSSLManger
from mod.base.web_conf import RealRedirect, RealLogMgr, Proxy, RealProxy
from mod.base.process.server import RealServer
from mod.project.java.java_web_conf import JavaWebConfig
from mod.project.java.server_proxy import RealServerProxy
from mod.base.git_tool import GitMager
from mod.project.java.springboot_parser import SpringConfigParser, SpringLogConfigParser

_DEBUG = True

GLOBAL_TOMCAT_PATH = "/usr/local/bttomcat"

INDEP_PROJECT_TOMCAT_PATH = "/www/server/bt_tomcat_web"

BASE_VERSIONS = {
    "tomcat7": ("7.0.109", 8231),
    "tomcat8": ("8.5.81", 8232),
    "tomcat9": ("9.0.0", 8233),
    "tomcat10": ("10.0.22", 8234),
}

JDK_SUPPORT = {
    7: "6 及更高版本",
    8: "7 及更高版本",
    9: "8 及更高版本",
    10: "8 及更高版本",
}

PS_FILE_TMPL = "{tomcat_path}/ps.txt"

CONFIG_PATH_TMPL = "{tomcat_path}/conf/server.xml"


def debug(func):
    if not _DEBUG:
        return func
    
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            err = traceback.format_exc()
            print(err)
            public.print_log(err)
        return {"msg": "报错了"}
    
    return inner


def set_java_service_link():
    java_service_bin = '/usr/bin/java-service'
    java_service_src = '/www/server/panel/script/java-service.py'
    if os.path.exists(java_service_src):
        public.ExecShell("chmod 700 " + java_service_src)
    if not os.path.exists(java_service_bin):
        if os.path.exists(java_service_src):
            public.ExecShell("ln -sf {} {}".format(java_service_src, java_service_bin))


set_java_service_link()


class main(JavaWebConfig, Proxy, Redirect, GitMager):
    
    def __init__(self):
        super().__init__()
        self._bt_tomcat_path = "/usr/local/bttomcat"
        self._bt_jdk_path = "/usr/local/btjdk/"
        self._java_path = "/www/server/java/"
        self._vhost_path = "/www/server/panel/vhost"
        self._java_project_path = "/var/tmp/springboot/"
        self._java_project_vhost = "/var/tmp/springboot/vhost"
        self._java_spring_boot_log_path = "/www/wwwlogs/java/springboot"
        self._site_tomcat_path = '/www/server/bt_tomcat_web/'
        if not os.path.exists(self._java_project_vhost):
            os.makedirs(self._java_project_vhost + "/pids", 0o777)
            os.makedirs(self._java_project_vhost + "/scripts", 0o755)
        if not os.path.exists(self._java_project_vhost + "/env"):
            os.makedirs(self._java_project_vhost + "/env", 0o755)
        if not os.path.exists(self._java_spring_boot_log_path):
            os.makedirs(self._java_spring_boot_log_path, 0o755)
        if not os.path.exists(self._site_tomcat_path):
            os.makedirs(self._site_tomcat_path, 0o755)
        
        self._default_java_log = "/www/wwwlogs/java"
        if not os.path.exists(self._default_java_log):
            os.makedirs(self._default_java_log, 0o701)
        
        # 实现Proxy初始化
        Proxy.__init__(self, config_prefix = "java_")
        # 实现Redirect初始化
        Redirect.__init__(self, config_prefix = "java_")
        
        self._real_process: Optional[RealProcess] = None
    
    @property
    def real_process(self) -> RealProcess:
        if self._real_process is None:
            self._real_process = RealProcess()
        return self._real_process
    
    @staticmethod
    def is_stop_by_user(project_id):
        return utils.is_stop_by_user(project_id)
    
    @staticmethod
    def write_project_log(log_str: str):
        public.WriteLog("项目管理", log_str)
    
    def get_system_info(self, get=None):
        return json_response(
            status = True, data = {
                "jdk_info": self._local_jdk_info(),
                "tomcat_status": self._bt_tomcat_info(),
            }
        )
    
    @staticmethod
    def _local_jdk_info() -> List[Dict]:
        ret = []
        jdk_tool = utils.JDKManager()
        current_java_home = jdk_tool.get_env_jdk()
        # 获取已安装的JDK版本
        for version in jdk_tool.versions_list:
            jdk_path = '/www/server/java/' + version + '/bin/java'
            is_current = os.path.dirname(os.path.dirname(jdk_path)) == current_java_home
            if os.path.exists('/www/server/java/' + version):
                ret.append({'name': version, 'path': jdk_path, 'operation': 1, 'is_current': is_current})
            else:
                ret.append({'name': version, 'path': '', 'operation': 0, 'is_current': False})
            name = '安装[{}]'.format(version)
            install_data = public.M('tasks').where("status in (0, -1) and name=?", (name,)).find()
            if install_data:
                ret[-1]['operation'] = 3
        
        ret.sort(key = lambda x: (x['operation'] == 1, x['operation'] == 3), reverse = True)
        
        # 检查其他JDK路径
        jdk_paths = [
            ('JDK', '/usr/bin/java'),
            ('jdk8', '/usr/java/jdk1.8.0_121/bin/java'),
            ('openjdk8', '/usr/local/btjdk/jdk8/bin/java'),
            ('jdk7', '/usr/java/jdk1.7.0_80/bin/java')
        ]
        
        for i in jdk_tool.custom_jdk_list:
            is_current = utils.normalize_jdk_path(i) == current_java_home
            ret.append({'name': '自定义JDK', 'path': i, 'operation': 1, 'is_current': is_current})
        
        for name, path in jdk_paths:
            if os.path.exists(path):
                is_current = os.path.dirname(os.path.dirname(path)) == current_java_home
                ret.append({'name': name, 'path': path, 'operation': 2, 'is_current': is_current})
        
        return ret
    
    @staticmethod
    def _bt_tomcat_info() -> List[Dict]:
        versions = [7, 8, 9, 10]
        data = []
        for i in versions:
            soft_name = "安装[Java项目Tomcat-{}]".format(i)
            install_data = public.M('tasks').where("status in (0, -1) and name=?", (soft_name,)).find()
            tmp = utils.bt_tomcat(i).status()
            tmp["version"] = i
            if install_data:
                tmp["is_install"] = True
            else:
                tmp["is_install"] = False
            data.append(tmp)
        return data
    
    def process_for_create(self, get):
        is_java_process = True
        search = ''
        
        if hasattr(get, "is_java_process"):
            is_java_process = get.is_java_process.strip()
            if is_java_process in ("0", 0, False, "false"):
                is_java_process = False
            else:
                is_java_process = True
        if hasattr(get, "search"):
            search = get.search.strip()
        
        res = []
        rep_bt_tomcat = re.compile(r"(/usr/local/bttomcat/.*)|(/www/server/(bt_)?tomcat(_web)?/.*)/jsvc")
        rep_not_use = re.compile(
            r"php|system|crond|NetworkManager|uwsgi|dotnet|bash|/www/server/tamper|mysql|nginx|httpd|tail|python|sshd"
        )
        if is_java_process:
            target_list = utils.jps()
            all_spring_project_pid = self.all_spring_project_pid()
            for pid in target_list:
                if pid in all_spring_project_pid:
                    continue
                try:
                    p = psutil.Process(pid)
                    if search and not (search in p.name() or search in ' '.join(p.cmdline())):  # 有搜索条件，但不符合搜索条件
                        continue
                    if rep_bt_tomcat.search(p.exe()):
                        continue
                    res.append(
                        {
                            "pid": pid,
                            "name": p.name(),
                            "exe": p.exe(),
                            "cmdline": p.cmdline(),
                            "username": p.username(),
                            "create_time:": p.create_time(),
                            "status": p.status(),
                        }
                    )
                except:
                    continue
            
            return res
        
        # 若未选择java进程， 则在所有进程中搜索
        for i in psutil.process_iter(["pid", "name", "exe", "cmdline", "username", "create_time", "status"]):
            if not i.exe():
                continue
            if rep_not_use.search(i.exe()):
                continue
            if search and not (search in i.name() or search in ' '.join(i.cmdline())):  # 有搜索条件， 但不符合搜索条件
                continue
            if rep_bt_tomcat.search(i.exe()):
                continue
            try:
                res.append(
                    {
                        "pid": i.pid,
                        "name": i.name(),
                        "exe": i.exe(),
                        "cmdline": i.cmdline(),
                        "username": i.username(),
                        "create_time:": i.create_time(),
                        "status": i.status(),
                    }
                )
            except:
                continue
        
        return res
    
    @staticmethod
    def process_info_for_create(get):
        try:
            pid = int(get.pid.strip())
        except:
            return json_response(status = False, msg = "参数错误")
        
        try:
            p = psutil.Process(pid)
            
            cmdline = p.cmdline()
            ports = []
            for i in p.connections():
                if i.status == "LISTEN" and i.laddr and i.laddr.port not in ports:
                    ports.append(i.laddr.port)
            user = p.username()
            env = p.environ()
            exe = p.exe()
        except:
            public.print_log(public.get_error_info())
            return json_response(status = False, msg = "进程解析失败")
        
        pwd_path = env.get("PWD")
        env_list = []
        for key, value in env.items():
            if key.lower().find("spring") != -1 or key.lower().find("java") != -1:
                env_list.append({"k": key, "v": value})
        
        java_bin = ""
        if exe.endswith("java"):  # 目前支持用户使用java命令启动的java进程
            java_bin = exe
            if cmdline[0].endswith("java"):
                cmdline[0] = java_bin
        
        jar_path = ""
        target_jar_idx = None
        for idx, i in enumerate(cmdline):
            if i.endswith(".jar") or i.endswith(".war") and not (i.startswith("-") or "=" in i):
                if not jar_path:
                    jar_path = i
                    target_jar_idx = idx
        
        # 处理获取的java路径
        project_name = ""
        if jar_path:
            if not jar_path.startswith("/"):  # 处理相对路径
                jar_path = os.path.abspath(os.path.join(pwd_path, jar_path))
            cmdline[target_jar_idx] = jar_path
            project_name = os.path.basename(jar_path).rsplit(".", 1)[0]
        
        if not os.path.exists(jar_path):
            jar_path = None
        
        return json_response(
            status = True, data = {
                "project_name": project_name,
                "jar_path": jar_path,
                "java_bin": java_bin,
                "port": ports[0] if len(ports) else 0,
                "user": user,
                "env": env_list,
                "cmdline": " ".join(cmdline),
                "pid": pid,
            }
        )
    
    @staticmethod
    def check_spring_boot_args(get) -> Union[Dict, str]:
        by_process = 0
        domains = []
        proxy_path = "/"
        jmx_status = False
        watch_file = False
        env_file = ""
        env_list = []
        try:
            project_name = get.project_name.strip()
            project_jar = get.project_jar.strip()
            project_jdk = get.project_jdk.strip()
            # port = int(get.port)
            run_user = get.run_user.strip()
            project_cmd = get.project_cmd.strip()  # type:str
            ps = get.project_ps.strip()
            if hasattr(get, "env_file"):
                env_file = get.env_file.strip()
                if not isinstance(env_file, str) and os.path.exists(env_file):
                    return "环境变量文件不存在"
            if hasattr(get, "env_list"):
                env_list = get.env_list
                if not isinstance(env_list, list):
                    return "环境变量格式错误"
            if hasattr(get, "domains"):
                domains = get.domains
                if not isinstance(domains, list):
                    return "域名参数错误"
            if hasattr(get, "proxy_path"):
                proxy_path = get.proxy_path
                if not isinstance(domains, str) and not proxy_path.startswith("/"):
                    return "代理路径必须是以/开头的字符串"
            if hasattr(get, "jmx_status"):
                jmx_status = utils.js_value_to_bool(get.jmx_status)
            if hasattr(get, "watch_file"):
                watch_file = utils.js_value_to_bool(get.watch_file)
            if hasattr(get, "by_process"):
                by_process = int(get.by_process)
                if by_process < 0:
                    by_process = 0
        except (AttributeError, ValueError):
            return "参数格式错误"
        
        if not project_name:
            return "项目名称不能为空"
        if not 1 <= len(project_name) <= 20:
            return "项目名称不超过20字符"
        if public.M('sites').where('name=?', (project_name,)).count():
            return '指定项目名称已存在: {}'.format(project_name)
        
        if not os.path.exists(project_jar):
            return '请输入正确的jar包路径'
        
        project_jdk = utils.normalize_jdk_path(project_jdk)
        if not isinstance(project_jdk, str):
            return '项目JDK路径不存在'
        if not os.path.exists(project_jdk):
            return '请输入正确的JDK路径'
        if not utils.test_jdk(project_jdk):
            return '请输入正确的JDK路径'
        
        # if project_cmd.find(project_jdk) == -1:
        #     return '启动命令中不包含JDK路径，请确认无误再添加'
        #
        # if project_cmd.find(project_jar) == -1:
        #     return '启动命令中不包含jar路径，请确认无误后再添加'
        
        # 检查project_cmd的起始命令是否是相对路径，如果是，则需要处理为绝对路径
        if project_cmd.startswith("./") or project_cmd.startswith("../"):
            path = os.path.dirname(project_jar)
            project_cmd_bin = os.path.abspath(os.path.join(path, project_cmd.split(" ", 1)[0]))
            if os.path.exists(project_cmd_bin):
                project_cmd = project_cmd_bin + " " + project_cmd.split(" ", 1)[1]
            else:
                return "启动命令的二进制文件为相对路径，这可能导致服务启动失败，请改为绝对路径使用"
        
        # if not by_process and not utils.check_port(port):
        #     return '端口格式错误或已被其他进程使用'
        
        if domains:
            if not public.is_apache_nginx():
                return "未安装Nginx"
            err_msg = public.checkWebConfig()
            if isinstance(err_msg, str):
                return (
                        'WEB服务器配置配置文件错误ERROR:<br><font style="color:red;">'
                        + err_msg.replace("\n", '<br>') + '</font>'
                )
        
        if run_user not in [i["username"] for i in RealUser().get_user_list()["data"]]:
            return '请输入正确的启动用户'
        
        if domains:
            domains, err = normalize_domain(*domains)
            if err:
                return "<br>".join(["域名：{}，错误信息：{}".format(i['domain'], i['msg']) for i in err])
            else:
                for d, p in domains:
                    if public.M('domain').where('name=?', d).count():
                        return '指定域名已存在: {}'.format(d)
        
        return {
            "project_name": project_name,
            "project_jar": project_jar,
            "project_jdk": project_jdk,
            # "port": port,
            "run_user": run_user,
            "project_cmd": project_cmd,
            "ps": ps,
            "env_list": env_list,
            "env_file": env_file,
            "domains": ["{}:{}".format(i[0], i[1]) for i in domains],
            "proxy_path": proxy_path,
            "jmx_status": jmx_status,
            "watch_file": watch_file,
            "by_process": by_process,
        }
    
    def create_spring_boot_project(self, get):
        config = self.check_spring_boot_args(get)
        if isinstance(config, str):
            return json_response(status = False, msg = config)
        
        project_config = {
            'ssl_path': '/www/wwwroot/java_node_ssl',
            'project_jdk': config["project_jdk"],
            'project_name': config["project_name"],
            'project_jar': config["project_jar"],
            'bind_extranet': 0 if not config["domains"] else 1,
            'domains': config["domains"],
            'run_user': get.run_user.strip(),
            'jmx_status': config["jmx_status"],
            'project_cmd': config["project_cmd"],
            'java_type': 'springboot',
            'jar_path': os.path.dirname(config["project_jar"]),
            'pids': "{}/pids/{}.pid".format(self._java_project_vhost, config["project_name"]),
            'logs': "{}/{}.log".format(self._java_spring_boot_log_path, config["project_name"]),
            'scripts': "{}/scripts/{}.sh".format(self._java_project_vhost, config["project_name"]),
            'watch_file': config["watch_file"],
            'env_list': config["env_list"],
            'env_file': config["env_file"],
            'proxy_path': config["proxy_path"],
            "nohup_log": True,
            "static_info": {},
            "proxy_info": [],
            "daemon_status": get.get("daemon_status", False),
            "server_name_suffix": ""
        }
        
        pdata = {
            'name': config["project_name"],
            'path': config["project_jar"],
            'ps': config["ps"],
            'status': 1,
            'type_id': 0,
            'project_type': 'Java',
            'project_config': json.dumps(project_config),
            'addtime': public.getDate()
        }
        project_id = public.M('sites').insert(pdata)
        if not isinstance(project_id, int):
            return json_response(status = False, msg = '创建项目失败')
        pdata["project_config"] = project_config
        pdata["id"] = project_id
        
        if project_config["domains"]:
            for domain in project_config["domains"]:
                domain_name, port = domain.split(":")
                public.M('domain').insert(
                    {
                        'name': domain_name,
                        'pid': project_id,
                        'port': port,
                        'addtime': public.getDate()
                    }
                )
        
        error_msg = self._setup_spring_boot_project(pdata, by_process = config["by_process"])
        if error_msg:
            return json_response(status = True, msg = error_msg)
        if project_config["domains"]:
            public.check_domain_cloud(project_config["domains"][0])
        return json_response(status = True, msg = '项目创建成功, 若未能启动成功, 请查看日志信息，获取启动失败原因')
    
    def _setup_spring_boot_project(self, pdata, by_process=False) -> Optional[str]:
        project_config = pdata["project_config"]
        if project_config["jmx_status"]:
            pass
        # project_config["project_cmd"] = self._build_jmx_cmd(project_config["project_cmd"], project_config['jmx_status'])
        if not by_process:
            start_status = self._start_spring_boot_project(pdata, write_systemd_file = True, need_wait = False)
            if isinstance(start_status, dict):
                start_status = start_status["msg"]
        
        else:
            public.writeFile(project_config['pids'], str(by_process))
            start_status = "添加成功"
        
        if project_config["watch_file"]:
            add_project_watch(
                p_name = project_config["project_name"],
                p_type = "java",
                site_id = pdata["id"],
                watch_path = project_config["project_jar"]
            )
        if project_config["domains"]:
            res = self.create_config(
                pdata,
                domains = [i.split(":", 1) for i in project_config["domains"]],
                use_ssl = False,
            )
        
        return start_status
    
    @staticmethod
    def _get_systemd_server_name(project_config: dict) -> str:
        try:
            project_config["project_name"].encode('ascii')
        except Exception:
            name = public.Md5(project_config["project_name"])  # 如果不都是ascii编码的，则用md5的结果作为server名称
        else:
            name = project_config["project_name"]
        return "spring_" + name + project_config.get("server_name_suffix", "")
    
    # 实际启动项目的函数
    def _start_spring_boot_project(
        self,
        project_data: dict,
        write_systemd_file=True,
        need_wait=False,
    ) -> dict:
        
        old_pid = self.get_project_pid(project_data)
        project_config = project_data["project_config"]
        server_name = self._get_systemd_server_name(project_config)
        
        # 先检查环境变量文件是否存在，没有的时候先写空
        env_file = project_config['env_file']
        env_list = project_config['env_list']
        env_path = "{}/env/{}.env".format(self._java_project_vhost, project_config["project_name"])
        
        if isinstance(env_list, list):
            if not os.path.exists(os.path.dirname(env_path)):
                os.makedirs(os.path.dirname(env_path), 0o755)
            public.writeFile(
                env_path, "\n".join(
                    ["{}={}".format(i["k"], i["v"]) for i in env_list if "k" in i and "v" in i]
                )
            )
        else:
            if not os.path.isfile(env_path):
                public.writeFile(env_path, "")
        
        if env_file and not os.path.isfile(env_file):
            if not os.path.exists(os.path.dirname(env_file)):
                os.makedirs(os.path.dirname(env_file), 0o755)
            public.writeFile(env_file, "")
        
        log_file = project_config['logs']
        pid_file = project_config['pids']
        
        if not os.path.exists(log_file):
            public.writeFile(log_file, "")
        
        if not os.path.exists(pid_file):
            public.writeFile(pid_file, "0")
        
        # 修改文件权限
        public.ExecShell(
            "chown {usr}:{usr} {file}".format(
                usr = project_config["run_user"], file = project_config["project_jar"]
            )
        )
        public.ExecShell(
            "chown {usr}:{usr} {file}".format(usr = project_config["run_user"], file = log_file)
        )
        public.set_mode(log_file, "666")  # 保障其他用户也可以写入日志（syslog）
        public.ExecShell(
            "chown {usr}:{usr} {file}".format(usr = project_config["run_user"], file = pid_file)
        )
        utils.pass_dir_for_user(os.path.dirname(log_file), project_config['run_user'])

        # 写入启动脚本
        project_cmd = project_config['project_cmd']
        # 前置准备
        if project_config["nohup_log"]:
            collect_log = log_file
        else:
            collect_log = '/dev/null'

        jar_path = project_config['jar_path']

        env = "EnvironmentFile={}".format(env_path)
        pre_sh = "source {}".format(env_path)
        if env_file:
            env += "\nEnvironmentFile={}".format(env_file)
            pre_sh += "\nsource {}".format(env_file)

        env_key = "BT_JAVA_SERVICE_SID={}".format(public.Md5(project_data["name"]))

        # 启动脚本
        start_cmd = '''#!/bin/bash
        PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
        export PATH
        export {env_key}
        cd {jar_path}
        {pre_sh}
        nohup {project_cmd} &>> {log} &
        echo $! > {pid_file}'''.format(
            env_key=env_key,
            jar_path=jar_path,
            project_cmd=project_cmd,
            pid_file=pid_file,
            log=collect_log,
            pre_sh=pre_sh,
        )
        public.writeFile(project_config['scripts'], start_cmd)
        
        # 如果存在服务文件，没有要求写入时，就直接执行启动停止操作
        s_admin = RealServer()
        if not write_systemd_file and not utils.not_systemd():
            res = s_admin.daemon_status(server_name)
            msg = res['msg']
            if msg in ("运行中", "未运行"):
                with utils.tmp_close_security(project_config["run_user"]) as t:
                    s_admin.daemon_admin(server_name, "restart")
                    if need_wait:
                        return self._wait_start_status(project_data, old_pid = old_pid)
                    else:
                        return json_response(status = True, msg = "操作已执行")

            if msg == "操作失败!":
                return res
            # 还有一种服务文件丢失的情况走下面的写文件并启动

        if utils.not_systemd():
            with utils.tmp_close_security(project_config["run_user"]) as t:
                public.ExecShell("/bin/bash {}".format(project_config['scripts']), user=project_config["run_user"])
                return json_response(status=True, msg="操作已执行")

        with utils.tmp_close_security(project_config["run_user"]) as t:
            res = s_admin.create_daemon(
                server_name = server_name,
                pid_file = pid_file,
                start_exec = "/bin/bash {}".format(project_config['scripts']),
                workingdirectory = jar_path,
                user = project_config["run_user"],
                logs_file = "",
                environments = env,
                restart_type = "always" if project_config.get("daemon_status", False) else "no",
                is_fork = 1,
            )
            if not res["status"]:
                return res

            s_admin.daemon_admin(server_name, "start")
        if need_wait:
            return self._wait_start_status(project_data, old_pid = old_pid)
        return json_response(status = True, msg = "操作已执行")
    
    def _wait_start_status(self, project_data: dict, old_pid: int) -> dict:
        # 当为重启时，等待关闭
        if old_pid:
            try:
                p = psutil.Process(old_pid)
                for i in range(20):
                    time.sleep(0.05)
                    if not p.is_running():
                        break
            except:
                pass
        
        project_config = project_data['project_config']
        pid = self.get_project_pid(project_data)
        if not pid:
            for i in range(2):
                time.sleep(0.05)
                pid = self.get_project_pid(project_data)
                if pid:
                    break
        
        if not pid:
            return json_response(
                False,
                msg = "启动失败,详细信息请查看日志",
                data = public.GetNumLines(project_config["logs"], 30)
            )
        
        for i in range(3):
            port = self._get_port_by_pid(pid)
            if port:
                return json_response(True, "启动成功")
            time.sleep(0.05)
            if i > 1 and i % 5 == 0:
                if pid not in psutil.pids():
                    return json_response(
                        False,
                        msg = "启动失败,详细信息请查看日志",
                        data = public.GetNumLines(project_config["logs"], 30)
                    )
        
        pid = self.get_project_pid(project_data)
        if not pid:
            return json_response(
                False,
                msg = "启动失败,详细信息请查看日志",
                data = public.GetNumLines(project_config["logs"], 30)
            )
        else:
            return json_response(True, "启动成功")
    
    @staticmethod
    def _get_port_by_pid(pid: int) -> Optional[int]:
        try:
            p = psutil.Process(pid)
            for i in p.connections():
                if i.status == "LISTEN":
                    return i.laddr.port
        except:
            return None
    
    #         # 启动脚本
    #         start_cmd = '''#!/bin/bash
    # PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
    # export PATH
    # {env}
    # cd {jar_path}
    # nohup {project_cmd} {collect_log} &
    # echo $! > {pid_file}
    # '''.format(
    #             jar_path=jar_path,
    #             project_cmd=project_cmd,
    #             pid_file=pid_file,
    #             log_file=log_file,
    #             env=env,
    #             collect_log=collect_log
    #         )
    #         script_file = project_config['scripts']
    #         # 写入启动脚本
    #         public.writeFile(script_file, start_cmd)
    #         if os.path.exists(pid_file):
    #             os.remove(pid_file)
    #         public.set_mode(script_file, 755)
    #         # 修改文件权限
    #         public.ExecShell(
    #             "chown {usr}:{usr} {file}".format(usr=project_config["run_user"], file=project_config["project_jar"])
    #         )
    #         if not os.path.exists(log_file):
    #             public.writeFile(log_file, "")
    #
    #         public.ExecShell(
    #             "chown {usr}:{usr} {file}".format(usr=project_config["run_user"], file=log_file)
    #         )
    #         utils.pass_dir_for_user(os.path.dirname(log_file), project_config['run_user'])
    #         # 执行脚本文件
    #         res = public.ExecShell("bash {}".format(script_file), user=project_config['run_user'], env=os.environ.copy())
    #
    #         time.sleep(1)
    #         error_msg = '启动失败，您可以尝试查看控制台日志，以获取具体失败原因'
    #         if not os.path.exists(pid_file):
    #             return error_msg
    #
    #         # 获取PID
    #         try:
    #             pid = int(public.readFile(pid_file))
    #         except:
    #             return error_msg
    #         if pid not in psutil.pids():
    #             return error_msg
    #
    #         return None
    
    @staticmethod
    def _build_jmx_cmd(cmd_str: str, jmx_status: bool):
        has_jmx_args = cmd_str.find("-Dcom.sun.management.jmxremote") != -1
        if not jmx_status:
            if not has_jmx_args:
                return cmd_str
            
            cmd_str_list = cmd_str.split(" ")
            for i in range(len(cmd_str_list) - 1, -1, -1):
                if cmd_str_list[i].startswith("-Dcom.sun.management.jmxremote"):
                    cmd_str_list.pop(i)
                if cmd_str_list[i].startswith("-Djava.rmi.server.hostname=127.0.0.1"):
                    cmd_str_list.pop(i)
            
            return " ".join(cmd_str_list)
        
        if jmx_status and has_jmx_args:
            port = re.search(r"-Dcom\.sun\.management\.jmxremote\.port=(?P<port>\d+)", cmd_str)
            if not utils.check_port(port.group("port")):  # 如果原来的port被占用了，则生成一个随机的port并替换
                cmd_str = re.sub(
                    r"-Dcom\.sun\.management\.jmxremote\.port=(\d+)",
                    "-Dcom.sun.management.jmxremote.port={}".format(utils.create_a_not_used_port()),
                    cmd_str
                )
            return cmd_str
        
        add_cmd = (
            " -Dcom.sun.management.jmxremote"
            " -Dcom.sun.management.jmxremote.port={}"
            " -Djava.rmi.server.hostname=127.0.0.1"
            " -Dcom.sun.management.jmxremote.local.only=true"
            " -Dcom.sun.management.jmxremote.authenticate=false"
            " -Dcom.sun.management.jmxremote.ssl=false"
        ).format(utils.create_a_not_used_port())
        
        cmd_str = cmd_str.lstrip(" ")
        first_space_idx = cmd_str.find(" ")  # 把jmx的配置放到第一个空格之后
        if first_space_idx == -1:
            return cmd_str + add_cmd
        else:
            return cmd_str[:first_space_idx] + add_cmd + cmd_str[first_space_idx:]
    
    @staticmethod
    def check_tomcat_args(get) -> Union[Dict, str]:
        port = None
        jdk_path = None
        project_name = get.get("project_name", "")
        try:
            if get.get("domain", ""):
                domain = get.domain
            elif get.get("domains", ""):
                domain = get.domains
            if isinstance(domain, str):
                domain = domain.strip()
            elif isinstance(domain, list):
                domain = domain[0]
            tomcat_version = int(get.tomcat_version)
            project_path = get.project_path.strip()
            if hasattr(get, "port"):
                port = int(get.port)
            if hasattr(get, "jdk_path"):
                jdk_path = get.jdk_path.strip()
            ps = get.project_ps.strip()
        except:
            return "参数错误"
        
        if not is_domain(domain):
            return "请输入正确的域名"
        
        if not os.path.exists(project_path):
            os.makedirs(project_path)
            public.set_own(project_path, 'www')

        create_by_name = False
        if "tomcat_name" in get and get.tomcat_name:
            create_by_name = True
        if tomcat_version not in (7, 8, 9, 10) and not create_by_name:
            return "请选择正确的Tomcat版本"
        
        if jdk_path is not None:
            if not os.path.exists(jdk_path):
                return "JDK路径不存在"
            jdk_path = utils.normalize_jdk_path(jdk_path)
            if not isinstance(jdk_path, str):
                return '项目JDK路径不存在'
            if not utils.test_jdk(jdk_path):
                return "JDK路径错误"
        
        # !端口占用检测移至tomcat添加时期
        # if port is not None:
        #     if not utils.check_port(port):
        #         return "端口被占用"
        
        domain_list, err = normalize_domain(domain)
        if not err:
            domain = domain_list[0]
            if public.M('domain').where('name=?', domain[0]).count():
                return '指定域名已存在: {}'.format(domain[0])
            if not project_name:
                project_name = domain[0]
            domain = "{}:{}".format(domain[0], domain[1])
        else:
            return "<br>".join(["域名：{}，错误信息：{}".format(i['domain'], i['msg']) for i in err])
        
        return {
            "project_name": project_name,
            "project_jdk": jdk_path,
            "ps": ps,
            "port": port,
            "domains": [domain, ],
            "tomcat_version": tomcat_version,
            "project_path": project_path,
        }
    
    def create_tomcat_project(self, get):
        config = self.check_tomcat_args(get)
        if isinstance(config, str):
            return json_response(status=False, msg=config)
        
        tomcat_name = get.get("tomcat_name", "")
        if tomcat_name:
            info = self.get_tomcat_list().get(tomcat_name, {})
            if not info:
                return json_response(status=False, msg="tomcat_name is not exists")
            if info["type"] == "global":
                tomcat = utils.bt_tomcat(config["tomcat_version"])
                java_type = "neizhi"
            else:
                tomcat = utils.site_tomcat(tomcat_name)
                java_type = "duli"
        else:
            tomcat_name = "tomcat{}".format(config["tomcat_version"])
            java_type = "neizhi"
            tomcat = utils.bt_tomcat(config["tomcat_version"])
        
        if not tomcat.installed:
            return json_response(status = False, msg = "指定的Tomcat版本未安装")
        if tomcat.is_error_config_xml():
            return json_response(status = False, msg = "Tomcat配置文件出错，请尝试修复已有项目或重装Tomcat")
        
        if config["project_jdk"] and tomcat.jdk_path != config["project_jdk"]:
            if not tomcat.replace_jdk(config["project_jdk"]):
                return json_response(status = False, msg = "替换JDK失败")
        
        if config["port"] and not tomcat.set_port(config["port"]):
            return json_response(status = False, msg = "设置端口失败")
        
        tomcat_host_name = (config["domains"][0] if isinstance(config["domains"], list) else config["domains"]).split(":")[0]
        if not tomcat.add_host(name=tomcat_host_name, path = config["project_path"]):
            return json_response(status = False, msg = "添加失败")
        
        # 有web服务且可以重启
        if public.is_apache_nginx() and not isinstance(public.checkWebConfig(), str):
            bind_extranet = 1
        else:
            bind_extranet = 0
        
        if os.path.isfile(config["project_path"]):
            path = os.path.basename(config["project_path"])
        else:
            path = config["project_path"]
        
        project_config = {
            'project_name': config["project_name"],
            'bind_extranet': bind_extranet,
            'domains': config['domains'],
            'tomcat_version': config["tomcat_version"],
            "tomcat_name": tomcat_name,
            'java_type': java_type,
            # 'server_xml': '/usr/local/bt_mod_tomcat/tomcat%s/conf/server.xml' % config["tomcat_version"],
            'server_xml': CONFIG_PATH_TMPL.format(tomcat_path=tomcat.path),
            'port': int(tomcat.port()),
            'auth': '1',  # 默认开机自动启动
            'logs': os.path.dirname(tomcat.log_file),
            'ssl_path': '/www/wwwroot/java_node_ssl',
            "proxy_info": [],
        }
        
        # 添加数据库信息
        pdata = {
            'name': config["project_name"],
            'path': config["project_path"],
            'ps': config["ps"],
            'status': 1,
            'type_id': 0,
            'project_type': 'Java',
            'project_config': json.dumps(project_config),
            'addtime': public.getDate()
        }
        tomcat.save_config_xml()
        project_id = public.M('sites').insert(pdata)
        pdata["id"] = project_id
        for domain in config["domains"]:
            domain_name, port = domain.split(":")
            public.M('domain').insert(
                {
                    'name': domain_name,
                    'pid': project_id,
                    'port': port,
                    'addtime': public.getDate()
                }
            )
        tomcat.set_service()
        
        pdata["project_config"] = project_config
        
        if bind_extranet:
            self.create_config(
                pdata,
                domains = [i.split(":") for i in config['domains']],
                use_ssl = False
            )
        
        public.check_domain_cloud(config['domains'][0])
        return json_response(status = True, msg = '项目创建成功')
    
    @staticmethod
    def check_site_tomcat_args(get) -> Union[Dict, str]:
        jdk_path = None
        access_mode = "domain"
        auth = False
        try:
            domain = get.domains[0]
            tomcat_version = int(get.tomcat_version)
            project_path = get.project_path.strip()
            if hasattr(get, "project_jdk"):
                jdk_path = get.project_jdk.strip()
            if hasattr(get, "access_mode"):
                access_mode = get.access_mode
            port = int(get.port)
            run_user = get.run_user.strip()
            ps = get.project_ps.strip()
            if hasattr(get, "auth"):
                auth = utils.js_value_to_bool(get.auth)  # 实际上是 auto_start
        except Exception as e:
            public.print_log(e)
            return "参数错误"
        
        if not utils.check_port(port):
            return "端口已被使用"
        
        if not is_domain(domain):
            return "请输入正确的域名"
        
        if not os.path.exists(project_path):
            os.makedirs(project_path)
            public.set_own(project_path, 'www')
        if tomcat_version not in (7, 8, 9, 10):
            return "请选择正确的Tomcat版本"
        if access_mode not in ("domain", "ip"):
            return "请选择正确的访问模式"
        
        if jdk_path:
            if not os.path.exists(jdk_path):
                return "JDK路径不存在"
            jdk_path = utils.normalize_jdk_path(jdk_path)
            if not isinstance(jdk_path, str):
                return "JDK路径错误"
            if not utils.test_jdk(jdk_path):
                return "JDK检查错误"
        
        if run_user not in [i["username"] for i in RealUser().get_user_list()["data"]]:
            return '请输入正确的启动用户'
        
        domain_list, err = normalize_domain(domain)
        if err:
            return "<br>".join(["域名：{}，错误信息：{}".format(i['domain'], i['msg']) for i in err])
        else:
            for d, p in domain_list:
                if public.M('domain').where('name=?', d).count():
                    return '指定域名已存在: {}'.format(d)
            domain = domain_list[0]
            project_name = domain[0]
            domain = "{}:{}".format(domain[0], domain[1])
        
        return {
            "project_name": project_name,
            "project_jdk": jdk_path,
            "run_user": run_user,
            "port": port,
            "ps": ps,
            "domains": [domain, ],
            "tomcat_version": tomcat_version,
            "project_path": project_path,
            'ssl_path': '/www/wwwroot/java_node_ssl',
            "access_mode": access_mode,
            "auth": auth,
        }
    
    def create_site_tomcat_project(self, get):
        config = self.check_site_tomcat_args(get)
        if isinstance(config, str):
            return json_response(status = False, msg = config)
        
        site_tomcat_path = os.path.join(self._site_tomcat_path, config["project_name"])
        if os.path.exists(site_tomcat_path):
            return json_response(status = False, msg = "该网站已经存在。如想建立请删除%s" % site_tomcat_path)
        
        # 首先需要先复制好文件过去
        if not os.path.exists(site_tomcat_path):
            os.makedirs(site_tomcat_path)
        
        bt_tomcat_back = "/usr/local/bttomcat/tomcat_bak%d"
        if not os.path.exists(bt_tomcat_back % config["tomcat_version"] + '/conf/server.xml'):
            return json_response(
                False,
                "tomcat{v}的配置文件不存在，请重新安装tomcat{v}".format(v = config["tomcat_version"])
            )
        public.ExecShell(
            'cp -r %s/* %s  && chown -R %s:%s %s' % (
                bt_tomcat_back % int(config["tomcat_version"]), site_tomcat_path,
                config["run_user"], config["run_user"], site_tomcat_path
            )
        )
        tomcat = utils.site_tomcat(config["project_name"])
        if not tomcat:
            return json_response(status = False, msg = "Tomcat未能初始化成功")
        
        # server.xml
        if os.path.exists(site_tomcat_path + '/conf/server.xml'):
            tomcat.reset_tomcat_server_config(config["port"])
        else:
            os.system('rm -rf %s' % site_tomcat_path)
            return json_response(False, "配置文件不存在请重新安装tomcat后尝试新建网站")
        
        if config["project_jdk"] and tomcat.jdk_path != config["project_jdk"]:
            res = tomcat.replace_jdk(config["project_jdk"])
            if res:
                os.system('rm -rf %s' % site_tomcat_path)
                return json_response(status = False, msg = "JDK替换失败")
        
        log_path = "/www/wwwlogs/java/{}".format(config["project_name"])
        if not os.path.exists(log_path) or os.path.isfile(log_path):
            os.makedirs(log_path, mode = 0o755)
        tomcat.change_log_path(log_path, prefix = config["project_name"].replace(".", '_'))
        
        if not tomcat.add_host(config["project_name"], config["project_path"]):
            os.system('rm -rf %s' % site_tomcat_path)
            return json_response(status = False, msg = "添加失败")
        if config["access_mode"] == "ip":
            tomcat.host_to_root(config["project_name"], config["project_path"], config["port"])
        
        # 有web服务且可以重启
        if public.is_apache_nginx() and not isinstance(public.checkWebConfig(), str):
            bind_extranet = 1
        else:
            bind_extranet = 0
        
        if os.path.isfile(config["project_path"]):
            path = os.path.basename(config["project_path"])
        else:
            path = config["project_path"]
        
        project_config = {
            'project_name': config["project_name"],
            "project_jdk": config["project_jdk"],
            'bind_extranet': bind_extranet,
            'domains': config["domains"],
            'tomcat_version': config["tomcat_version"],
            'java_type': 'duli',
            'server_xml': site_tomcat_path + "/conf/server.xml",
            'port': config["port"],
            "run_user": config["run_user"],
            'logs': log_path,
            "proxy_info": [],
            "access_mode": config["access_mode"],
            "auth": config["auth"]
        }
        
        pdata = {
            'name': config["project_name"],
            'path': config["project_path"],
            'ps': config["ps"],
            'status': 1,
            'type_id': 0,
            'project_type': 'Java',
            'project_config': json.dumps(project_config),
            'addtime': public.getDate()
        }
        tomcat.save_config_xml()
        project_id = public.M('sites').insert(pdata)
        pdata["id"] = project_id
        for domain in config["domains"]:
            domain_name, port = domain.split(":")
            public.M('domain').insert(
                {
                    'name': domain_name,
                    'pid': project_id,
                    'port': port,
                    'addtime': public.getDate()
                }
            )
        
        tomcat.set_service(user = config["run_user"], auto_start = config["auth"])
        
        pdata["project_config"] = project_config
        if bind_extranet:
            self.create_config(
                pdata,
                domains = [i.split(":") for i in config['domains']],
                use_ssl = False
            )
        public.check_domain_cloud(config['domains'][0])
        return json_response(status = True, msg = '项目创建成功')

    def create_project(self, get: Get):
        # *入参校验
        # project_port = get.get("port", "")
        # if public.M("sites").where("project_type=? AND project_config like ?", ("Java","%{}%".format(project_port))).count():
        #     return json_response(status=False, msg="端口已被其他java项目使用，请检查")

        project_type = int(get.get("project_type", ""))
        if project_type == "":
            return json_response(status = False, msg = "项目类型错误")
        
        # !开始统一传入project_name
        project_name = get.get("project_name", "")
        if not project_name:
            return json_response(False, "项目名不能为空")
        if public.M("sites").where("project_type=? AND name=?", ("Java", project_name)).count():
            return json_response(False, "已存在相同名称项目")
        
        project_path = get.get("project_path", "")
        project_jar = get.get("project_jar", "")
        if not project_path and project_jar and project_type == 0:
            project_path = project_jar
        if not os.path.exists(project_path):
            return json_response(False, "项目文件路径不存在")
        
        # *处理项目文件
        # if os.path.isfile(project_path) and os.path.basename(project_path).endswith(".war") and project_type != 0:
        #     target_dir = project_path.replace(".war", "")
        #     if not os.path.exists(target_dir):
        #         os.mkdir(target_dir)
        #     try:
        #         from zipfile import ZipFile
        #         with ZipFile(project_path, "r") as z:
        #             z.extractall(target_dir)
        #     except Exception:
        #         return json_response(False, "指定war包解压失败")
        #     os.remove(project_path)
        #     get.project_path = target_dir
        
        # *创建网站
        public.set_module_logs("create_java_project", "create")
        create_result = None
        if project_type == 0:
            public.set_module_logs("create_java_spring", "create")
            create_result = self.create_spring_boot_project(get)
        
        elif project_type == 1:
            public.set_module_logs("create_java_tomcat", "create")
            create_result = self.create_tomcat_project(get)
        
        # elif project_type == 2:
        #     create_result = self.create_site_tomcat_project(get)
        #     return
        
        if not create_result or not create_result.get("status", ""):
            return create_result
        
        # *防火墙放行
        if get.get("release_firewall", ""):
            from firewallModel.comModel import main
            f_get = public.dict_obj()
            f_get.protocol = "tcp"
            f_get.port = get.port
            f_get.choose = "all"
            f_get.types = "accept"
            f_get.brief = ""
            f_get.domain = ""
            f_get.chain = "INPUT"
            f_get.operation = "add"
            f_get.strategy = "accept"
            main().set_port_rule(f_get)
        
        # *添加反向代理
        # !统一为domains
        if (get.get("domains", "") and get.domains[0] != "") and get.get("proxy_dir", ""):
            p_get = public.dict_obj()
            p_get.site_name = get.project_name
            p_get.proxy_dir = get.proxy_dir
            p_get.proxy_port = get.port
            p_get.add_headers = []
            p_get.status = "1"
            proxy_result = self.add_server_proxy(p_get)
            if not proxy_result["status"]:
                self.remove_project(get)
                # return json_response(False, "添加反向代理失败")
                return proxy_result

            # *关联静态目录
            if get.get("static_dir", ""):
                p_get.status = 1
                p_get.index = "index.html"
                p_get.path = get["static_dir"]
                p_get.project_name = get.project_name
                static_res = self.set_static_path(p_get)
                if not static_res["status"]:
                    self.remove_project(get)
                    return json_response(False, "关联静态资源失败:" + static_res["msg"])
        
        return create_result
    
    @staticmethod
    def get_project_find(project_name: str) -> Optional[dict]:
        project_info = public.M('sites').where('project_type=? AND name=?', ('Java', project_name)).find()
        if not project_info:
            return None
        
        # 做旧项目的兼容性处理
        project_info['project_config'] = json.loads(project_info['project_config'])
        if "jmx_status" not in project_info['project_config']:
            project_info['project_config']['jmx_status'] = False
        if "nohup_log" not in project_info['project_config']:
            project_info['project_config']['nohup_log'] = True
        
        if "env_file" not in project_info['project_config']:
            project_info['project_config']['env_file'] = ''
        if "env_list" not in project_info['project_config']:
            project_info['project_config']['env_list'] = []
        
        if "static_path" in project_info['project_config'] and "static_info" not in project_info['project_config']:
            project_info['project_config']['static_info'] = {
                "path": project_info['project_config']['static_path'],
                "status": True,
                "index": "",
                "use_try_file": True
            }
            public.M('sites').where("id=?", (project_info['id'],)).update(
                {'project_config': json.dumps(project_info['project_config'])}
            )
        
        if "proxy_info" not in project_info['project_config']:
            rsp = RealServerProxy(project_info)
            proxy_list = rsp.get_proxy_list()
            project_info['project_config']['proxy_info'] = proxy_list
        
        # 兼容旧版本的守护进程
        if 'auth' in project_info['project_config'] and project_info['project_config']['auth'] in (1, "1") and \
                "daemon_status" not in project_info['project_config']:
            project_info['project_config']['daemon_status'] = True
        
        if 'daemon_status' not in project_info['project_config']:
            project_info['project_config']['daemon_status'] = False
        
        if "jdk_path" in project_info['project_config']:  # 兼容旧版本的Tomcat独立项目
            project_info['project_config']["project_jdk"] = utils.normalize_jdk_path(
                project_info['project_config']['jdk_path']
            )
        
        return project_info
    
    def modify_spring_boot_project(self, get, project_data: Optional[dict] = None):
        if not project_data:
            try:
                project_name = self.get_project_find(get.project_name.strip())
            except:
                return json_response(status = False, msg = "项目名称错误")
            if not project_data:
                return json_response(status = False, msg = "项目不存在")
        else:
            project_name = project_data['name']
        
        change_flag = False
        project_config = project_data['project_config']
        if hasattr(get, 'run_user') and get.run_user.strip() != project_config['run_user']:
            project_config['run_user'] = get.run_user.strip()
            change_flag = True
        if hasattr(get, 'project_jdk'):
            input_jdk = utils.normalize_jdk_path(get.project_jdk.strip())
            if not isinstance(input_jdk, str):
                return json_response(False, 'JDK检测错误')
            
            if input_jdk != project_config['project_jdk']:
                project_config['project_jdk'] = input_jdk
                change_flag = True
        
        if hasattr(get, 'project_jar') and get.project_jar.strip() != project_config['project_jar']:
            project_config['project_jar'] = get.project_jar.strip()
            if not os.path.isfile(project_config['project_jar']):
                return json_response(False, '项目jar包不存在')
            project_config['jar_path'] = os.path.dirname(project_config['project_jar'])
            change_flag = True
        
        if hasattr(get, 'project_cmd') and get.project_cmd.strip():
            if get.project_cmd.strip() != project_config['project_cmd']:
                project_cmd = get.project_cmd.strip()
                if project_cmd.startswith("./") or project_cmd.startswith("../"):
                    path = os.path.dirname(project_config['project_jar'])
                    project_cmd_bin = os.path.abspath(os.path.join(path, project_cmd.split(" ", 1)[0]))
                    if os.path.exists(project_cmd_bin):
                        project_cmd = project_cmd_bin + " " + project_cmd.split(" ", 1)[1]
                    else:
                        return json_response(
                            False,
                            "启动命令的二进制文件为相对路径，这可能导致服务启动失败，请改为绝对路径在使用"
                        )
                project_config['project_cmd'] = project_cmd
                change_flag = True
        else:
            return json_response(False, '缺少project_cmd参数')
        
        if hasattr(get, 'daemon_status'):
            daemon_status = utils.js_value_to_bool(get.daemon_status)
            if daemon_status != project_config['daemon_status']:
                project_config['daemon_status'] = daemon_status
                change_flag = True
        
        # 检查jar包是否在cmd中
        if project_config['project_cmd'].find(get.project_jar.strip()) == -1:
            return json_response(False, '项目jar包名称不在项目启动命令中，请检查')
        
        if hasattr(get, 'jmx_status') and utils.js_value_to_bool(get.jmx_status) != project_config['jmx_status']:
            project_config['jmx_status'] = utils.js_value_to_bool(get.jmx_status)
            change_flag = True
        
        if hasattr(get, "env_file") and get.env_file.strip() != project_config['env_file']:
            project_config['env_file'] = get.env_file.strip()
            if project_config['env_file'] and not os.path.exists(project_config['env_file']):
                return json_response(False, '项目环境文件不存在')
            change_flag = True
        
        if hasattr(get, "env_list"):
            env_list = get.env_list
            if isinstance(env_list, str):
                try:
                    env_list = json.loads(env_list)
                except:
                    return json_response(False, '项目环境变量格式错误')
            if not isinstance(env_list, list):
                return json_response(False, '项目环境变量格式错误')
            if env_list != project_config['env_list']:
                project_config['env_list'] = env_list
                change_flag = True
        
        if hasattr(get, 'watch_file'):
            project_config['watch_file'] = utils.js_value_to_bool(get.watch_file)
            if project_config['watch_file']:
                add_project_watch(
                    p_name = get.project_name.strip(),
                    p_type = "java",
                    site_id = project_data["id"],
                    watch_path = get.project_jar.strip()
                )
            else:
                del_project_watch(get.project_name.strip())
        
        if change_flag:
            project_config["change_flag"] = True
        
        pdata = {
            'name': project_name,
            'path': get.project_jar.strip(),
            'ps': get.project_ps.strip(),
            'project_config': json.dumps(project_config)
        }
        public.M('sites').where('name=?', (get.project_name,)).update(pdata)
        if get.get("release_firewall", "") and get.get("prot", ""):
            from firewallModel.comModel import main
            f_get = public.dict_obj()
            f_get.protocol = "tcp"
            f_get.port = get.port
            f_get.choose = "all"
            f_get.types = "accept"
            f_get.brief = ""
            f_get.domain = ""
            f_get.chain = "INPUT"
            f_get.operation = "add"
            f_get.strategy = "accept"
            main().set_port_rule(f_get)

        return json_response(True, '项目修改成功，重启后生效')
    
    def modify_tomcat_project(self, get, project_data: Optional[dict] = None):
        if not project_data:
            try:
                project_name = self.get_project_find(get.project_name.strip())
            except:
                return json_response(status = False, msg = "项目名称错误")
            if not project_data:
                return json_response(status = False, msg = "项目不存在")
        else:
            project_name = project_data['name']
        
        project_config = project_data['project_config']
        tomcat = utils.bt_tomcat(project_config["tomcat_version"])
        if tomcat.is_error_config_xml():
            return json_response(False, 'Tomcat配置文件错误, 请尝试刷新并修复项目')
        
        flag = False
        # 更换JDK
        if hasattr(get, 'project_jdk') and get.project_jdk:
            jdk_path = utils.normalize_jdk_path(get.project_jdk.strip())
            if not isinstance(jdk_path, str):
                return json_response(False, 'JDK检测错误')
            if jdk_path != tomcat.jdk_path:
                if not utils.test_jdk(jdk_path):
                    return json_response(False, '当前JDK不可用')
                
                res = tomcat.replace_jdk(jdk_path)
                if not res:
                    return json_response(False, res)
                flag = True
        
        if hasattr(get, 'project_path'):
            if get.project_path.strip() == project_data['path']:
                pass
            else:
                if not tomcat.set_host_path_by_name(project_name, get.project_path.strip()):
                    return json_response(False, '项目路径设置失败')
                flag = True
                project_data['path'] = get.project_path.strip()
        
        # 更换描述
        if hasattr(get, 'project_ps'):
            if get.project_ps.strip() != project_data['ps']:
                project_data['ps'] = get.project_ps.strip()
        
        if flag:
            tomcat.restart()
        
        pdata = {
            'path': project_data['path'],
            'ps': project_data['ps'],
        }
        public.M('sites').where('name=?', (get.project_name,)).update(pdata)
        return json_response(True, '项目修改成功')
    
    def modify_site_tomcat_project(self, get, project_data: Optional[dict] = None):
        if not project_data:
            try:
                project_name = self.get_project_find(get.project_name.strip())
            except:
                return json_response(status = False, msg = "项目名称错误")
            if not project_data:
                return json_response(status = False, msg = "项目不存在")
        else:
            project_name = project_data['name']
        
        project_config = project_data['project_config']
        tomcat = utils.site_tomcat(project_name)
        if not tomcat:
            return json_response(False, '项目的Tomcat已被删除，请尝试修复项目')
        if tomcat.is_error_config_xml():
            return json_response(False, 'Tomcat配置文件错误, 请尝试刷新并修复项目')
        
        flag = False
        # 更换JDK
        if hasattr(get, 'project_jdk') and get.project_jdk:
            jdk_path = utils.normalize_jdk_path(get.project_jdk.strip())
            if not isinstance(jdk_path, str):
                return json_response(False, 'JDK检测错误')
            if jdk_path != tomcat.jdk_path:
                if not utils.test_jdk(jdk_path):
                    return json_response(False, '当前JDK不可用')
                
                res = tomcat.replace_jdk(jdk_path)
                if isinstance(res, str):
                    return json_response(False, res)
                flag = True
                project_config["project_jdk"] = jdk_path
        
        if hasattr(get, 'port'):
            try:
                port = int(get.port)
            except:
                return json_response(False, '端口信息错误')
            
            if port != tomcat.port():
                if not utils.check_port(port):
                    return json_response(False, '端口已被占用')
                
                res = tomcat.set_port(port)
                if not res:
                    return json_response(False, '端口设置失败')
                tomcat.save_config_xml()
                flag = True
                project_config["port"] = port
        
        if hasattr(get, "access_mode"):
            access_mode = get.access_mode.strip()
            if access_mode not in ("domain", "ip"):
                return json_response(False, '访问模式错误')
            
            if access_mode != project_config.get("access_mode", "domain"):
                project_config["access_mode"] = get.access_mode.strip()
                if access_mode == "domain":
                    res = tomcat.root_to_host(
                        project_config["project_name"], project_data["path"], project_config["port"]
                    )
                else:
                    res = tomcat.host_to_root(
                        project_config["project_name"], project_data["path"], project_config["port"]
                    )
                if res:
                    return json_response(False, "Tomcat配置文件设置错误：" + res)
                tomcat.save_config_xml()
                flag = True
        
        # 更换描述
        if hasattr(get, 'project_ps'):
            if get.project_ps.strip() != project_data['ps']:
                project_data['ps'] = get.project_ps.strip()
        
        if hasattr(get, 'project_path'):
            if get.project_path.strip() != project_data['path']:
                if not tomcat.set_host_path_by_name(project_name, get.project_path.strip()):
                    return json_response(False, '项目路径设置失败')
                project_data['path'] = get.project_path.strip()
                flag = True
        
        if hasattr(get, 'run_user'):
            if "run_user" not in project_config:
                project_config["run_user"] = "root"
            if get.run_user.strip() != project_config.get("run_user", "root"):
                run_user = get.run_user.strip()
                if run_user not in [i["username"] for i in RealUser().get_user_list()["data"]]:
                    return json_response(False, '请输入正确的启动用户')
                else:
                    project_config["run_user"] = run_user
                flag = True
        
        if hasattr(get, 'auth'):
            tmp_auth = utils.js_value_to_bool(get.auth)
            if "auth" not in project_config:
                project_config["auth"] = False
            if tmp_auth != project_config["auth"]:
                project_config["auth"] = tmp_auth
                flag = True
        
        if flag:
            tomcat.set_service(
                user = project_config.get("run_user", "root"), auto_start = project_config.get("auth", False)
            )
        
        pdata = {
            'path': project_data['path'],
            'ps': project_data['ps'],
            'project_config': json.dumps(project_config),
        }
        public.M('sites').where('name=?', (get.project_name,)).update(pdata)
        return json_response(True, '项目修改成功')
    
    def modify_project(self, get):
        try:
            project_data = self.get_project_find(get.project_name.strip())
        except:
            return json_response(status = False, msg = "参数错误")
        if not project_data:
            return json_response(status = False, msg = "项目不存在")
        project_config = project_data["project_config"]
        if project_config["java_type"] == "springboot":
            return self.modify_spring_boot_project(get, project_data)
        elif project_config["java_type"] == "duli":
            return self.modify_site_tomcat_project(get, project_data)
        else:
            return self.modify_tomcat_project(get, project_data)
    
    def get_project_pid(self, project_data: dict) -> Optional[int]:
        # 从pid文件中获取项目pid
        project_config = project_data["project_config"]
        if project_config["java_type"] == "springboot":
            pid_file = project_config["pids"]
            pid = None
            if os.path.isfile(pid_file):
                try:
                    pid = int(public.readFile(pid_file))
                except:
                    pass
        elif project_config["java_type"] == "neizhi":
            tomcat = utils.bt_tomcat(project_config["tomcat_version"])
            if tomcat:
                pid = tomcat.pid()
            else:
                return None
        else:
            if project_config.get("tomcat_name", ""):
                tomcat = utils.site_tomcat(project_config["tomcat_name"])
            else:
                tomcat = utils.site_tomcat(project_data["name"])
            if tomcat:
                pid = tomcat.pid()
            else:
                return None
        if not pid and project_config["java_type"] == "springboot":
            try:
                pid = self._get_pid_by_env_key(project_data)
                if not pid:
                    return self._get_pid_by_command(project_data)
            except:
                return None
        
        try:
            psutil.Process(pid)
        except:
            return None
        
        return pid
    
    @staticmethod
    def _get_pid_by_env_key(project_data) -> Optional[int]:
        env_key = "BT_JAVA_SERVICE_SID={}".format(public.Md5(project_data["name"]))
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
            public.writeFile(project_data["project_config"]['pids'], str(main_pid))
            public.set_mode(project_data["project_config"]['pids'], "666")
            return main_pid
        
        return None
    
    def _get_pid_by_command(self, project_data: dict) -> Optional[int]:
        project_config = project_data["project_config"]
        if project_config["java_type"] != "springboot":
            return None
        
        server_name = self._get_systemd_server_name(project_config)
        server_admin = RealServer()
        pid = server_admin.get_daemon_pid(server_name)["data"]
        if isinstance(pid, int):
            try:
                p = psutil.Process(pid)
                if p.is_running():
                    public.writeFile(project_data["project_config"]['pids'], str(pid))
                    return pid
            except:
                pass
        
        jdk_path = utils.normalize_jdk_path(project_config['project_jdk'])
        project_jar = project_config['project_jar']
        jar_name = os.path.basename(project_jar)
        jar_cmd = project_config['project_cmd']
        port_rep = re.search(r"--server\.port=\d+", jar_cmd)
        pids = []
        for pro in psutil.process_iter(['pid', 'exe', 'cmdline']):
            if pro.status() == "zombie":
                continue
            try:
                if port_rep and port_rep.group() not in pro.cmdline():
                    continue
                if jdk_path == utils.normalize_jdk_path(pro.exe()) and any((jar_name in i for i in pro.cmdline())):
                    pids.append(pro.pid)
            except:
                pass
        
        if not pids:
            return None
        
        running_pid = []
        for pid in pids:
            if pid in psutil.pids():
                running_pid.append(pid)
        
        if len(running_pid) == 1:
            public.writeFile(project_data["project_config"]['pids'], str(running_pid[0]))
            public.set_mode(project_data["project_config"]['pids'], "666")
            return running_pid[0]
        for pid in running_pid:
            p = psutil.Process(pid)
            if p.ppid() not in running_pid:
                public.writeFile(project_data["project_config"]['pids'], str(pid))
                public.set_mode(project_data["project_config"]['pids'], "666")
                return pid
        
        return None
    
    def all_spring_project_pid(self):
        projects = public.M('sites').where('project_type=?', ("Java",)).select()
        res = []
        for i in projects:
            i["project_config"] = json.loads(i["project_config"])
            if i["project_config"]["java_type"] == "springboot":
                tmp = self.get_project_pid(i)
                if tmp and tmp > 0:
                    res.append(tmp)
        return res
    
    def project_process(self, project_data) -> Optional[psutil.Process]:
        pid = self.get_project_pid(project_data)
        if not pid:
            return None
        try:
            return psutil.Process(pid)
        except:
            return None
    
    def start_spring_boot_project(self, project_data: dict, wait: bool = False):
        change_flag = False
        project_config = project_data['project_config']
        if "change_flag" in project_config:
            change_flag = project_config.get("change_flag", False)
            del project_config["change_flag"]
            public.M("sites").where("id=?", (project_data["id"],)).update(
                {"project_config": json.dumps(project_config)}
            )
        res = self._start_spring_boot_project(project_data, change_flag, need_wait = wait)
        if res["status"] is True:
            utils.start_by_user(project_data["id"])
        return res
    
    def start_project(self, get):
        try:
            project_data = self.get_project_find(get.project_name)
        except:
            return json_response(False, '项目名称参数错误')
        
        if not project_data:
            return json_response(False, '项目不存在')
        
        p = self.project_process(project_data)
        if p and p.is_running():
            return json_response(False, '项目已启动')
        
        project_config = project_data['project_config']
        if project_config["java_type"] == "springboot":
            return self.start_spring_boot_project(project_data)
        
        elif project_config["java_type"] == "neizhi":
            res = utils.bt_tomcat(project_config["tomcat_version"]).start()
            if not res:
                return json_response(False, '项目启动失败')
        else:
            tomcat_name = project_config.get("tomcat_name", "")
            if tomcat_name:
                tomcat = utils.site_tomcat(tomcat_name)
            else:
                tomcat = utils.site_tomcat(project_config["project_name"])
            if not tomcat:
                return json_response(False, '独立项目的Tomcat文件丢失，请尝试修复项目')
            if not tomcat.running():
                res = tomcat.start(project_config.get("run_user", "root"))
                if not res:
                    return json_response(False, '项目启动失败')
        
        utils.start_by_user(project_data["id"])
        return json_response(True, "项目启动成功")
    
    def stop_project(self, get):
        try:
            project_data = self.get_project_find(get.project_name)
        except:
            return json_response(False, '项目名称参数错误')
        
        if not project_data:
            return json_response(False, '项目不存在')
        
        project_config = project_data['project_config']
        if project_config["java_type"] == "springboot":
            server_name = self._get_systemd_server_name(project_config)
            s_admin = RealServer()
            daemon_status = s_admin.daemon_status(server_name)
            if daemon_status["msg"] == "服务不存在!":
                self.stop_by_kill_pid(project_data)
                if os.path.isfile(project_config["pids"]):
                    os.remove(project_config["pids"])
            elif daemon_status["msg"] == "操作失败":
                self.stop_by_kill_pid(project_data)
                if os.path.isfile(project_config["pids"]):
                    os.remove(project_config["pids"])
            else:
                s_admin.daemon_admin(server_name, "stop")
            utils.stop_by_user(project_data["id"])
            return json_response(True, msg = "项目停止指令已执行")
        elif project_config["java_type"] == "neizhi":
            res = utils.bt_tomcat(project_config["tomcat_version"]).stop()
            if not res:
                return json_response(False, '项目停止失败')
        else:
            if project_config.get("tomcat_name", ""):
                tomcat = utils.site_tomcat(project_config["tomcat_name"])
            else:
                tomcat = utils.site_tomcat(project_config["project_name"])
            if not tomcat:
                return json_response(False, '独立项目的Tomcat文件丢失，请尝试修复项目')
            if tomcat.running():
                res = tomcat.stop()
                if not res:
                    return json_response(False, '项目停止失败')
        utils.stop_by_user(project_data["id"])
        return json_response(True, "项目停止成功")
    
    def stop_by_kill_pid(self, project_data):
        pid = self.get_project_pid(project_data)
        if not pid:
            return
        try:
            p = psutil.Process(pid)
            p.kill()
        except:
            pass
    
    def restart_project(self, get):
        try:
            project_data = self.get_project_find(get.project_name)
        except:
            return json_response(False, '项目名称参数错误')
        
        if not project_data:
            return json_response(False, '项目不存在')
        
        project_config = project_data['project_config']
        if project_config["java_type"] == "springboot":
            s_admin = RealServer()
            server_name = self._get_systemd_server_name(project_config)
            if s_admin.daemon_status(server_name)["msg"] == "服务不存在!":
                self.stop_by_kill_pid(project_data)
                if os.path.isfile(project_config["pids"]):
                    os.remove(project_config["pids"])
                return self._start_spring_boot_project(project_data, write_systemd_file = True)
            
            if "change_flag" in project_config and project_config.get("change_flag", False):
                del project_config["change_flag"]
                s_admin.daemon_admin(server_name, "stop")
                s_admin.del_daemon(server_name)
                self.stop_by_kill_pid(project_data)
                if os.path.isfile(project_config["pids"]):
                    os.remove(project_config["pids"])
                
                public.M("sites").where("id=?", (project_data["id"],)).update(
                    {"project_config": json.dumps(project_config)}
                )
                return self._start_spring_boot_project(project_data, write_systemd_file = True)
            else:
                return self._start_spring_boot_project(project_data, write_systemd_file = False)
        
        self.stop_project(get)
        time.sleep(0.5)
        self.start_project(get)
        
        return json_response(True, "项目重启已执行")
    
    @debug
    def fix_project(self, get):
        try:
            project_name = get.project_name.strip()
            project_data = self.get_project_find(project_name)
        except:
            return json_response(status = False, msg = "参数错误")
        if not project_data:
            return json_response(False, "未找到项目")
        
        project_config = project_data["project_config"]
        if project_config["java_type"] == "springboot":
            return json_response(status = False, msg = "非springboot项目不支持该功能")
        
        if project_config["java_type"] == "neizhi":
            return self._fix_bt_tomcat(project_data)
        else:
            return self._fix_site_tomcat(project_data)
    
    @staticmethod
    def _fix_bt_tomcat(project_data: dict):
        project_config = project_data["project_config"]
        ver = int(project_config["tomcat_version"])
        tomcat = utils.bt_tomcat(ver)
        if not tomcat.installed:
            bt_tomcat_back = "/usr/local/bttomcat/tomcat_bak%d"
            if not os.path.exists(bt_tomcat_back % ver + '/conf/server.xml'):
                return json_response(False, "tomcat{v}的配置文件不存在，请重新安装tomcat{v}".format(v = ver))
            
            if os.path.exists(tomcat.path):
                shutil.rmtree(tomcat.path)
            
            public.ExecShell('cp -r %s/* %s' % (bt_tomcat_back % ver, tomcat.path))
        
        if not tomcat.installed:
            return json_response(False, "tomcat{v}安装修复失败".format(v = ver))
        if tomcat.is_error_config_xml():
            tomcat.repair_config([{"name": project_data["name"], "path": project_data["path"]}])
        else:
            tomcat.add_host(project_data["name"], project_data["path"])
            tomcat.save_config_xml()
        tomcat.restart()
        
        return json_response(True, "Tomcat项目修复成功")
    
    def _fix_site_tomcat(self, project_data: dict):
        project_config = project_data["project_config"]
        tomcat = utils.site_tomcat(project_config["project_name"])
        ver = int(project_config["tomcat_version"])
        if not tomcat or not tomcat.installed:
            bt_tomcat_back = "/usr/local/bttomcat/tomcat_bak%d"
            if not os.path.exists(bt_tomcat_back % ver + '/conf/server.xml'):
                return json_response(False, "tomcat{v}的配置文件不存在，请重新安装tomcat{v}".format(v = ver))
            
            site_tomcat_path = os.path.join(self._site_tomcat_path, project_config["project_name"])
            if os.path.exists(site_tomcat_path):
                shutil.rmtree(site_tomcat_path)
            
            run_user = project_config.get("run_user", "www")
            public.ExecShell(
                'cp -r %s/* %s  && chown -R %s:%s %s' % (
                    bt_tomcat_back % ver, site_tomcat_path,
                    run_user, run_user, site_tomcat_path
                )
            )
        
        tomcat = utils.site_tomcat(project_config["project_name"])
        if not tomcat or not tomcat.installed:
            return json_response(False, "Tomcat安装修复失败")
        
        tomcat.reset_tomcat_server_config(project_config["port"])
        if tomcat.jdk_path != project_config["project_jdk"]:
            tomcat.replace_jdk(project_config["project_jdk"])
        
        log_path = "/www/wwwlogs/java/{}".format(project_config["project_name"])
        if not os.path.exists(log_path) or os.path.isfile(log_path):
            os.makedirs(log_path, mode = 0o755)
        
        tomcat.change_log_path(log_path, prefix = project_config["project_name"].replace(".", '_'))
        tomcat.add_host(project_config["project_name"], project_data["path"])
        if project_config.get("access_mode", "domain") == "ip":
            tomcat.host_to_root(project_config["project_name"], project_data["path"], project_config["port"])
        
        tomcat.save_config_xml()
        tomcat.restart(by_user = project_config.get("run_user", "root"))
        
        return json_response(True, "Tomcat项目修复成功")
    
    def project_list(self, get):
        """取项目列表"""
        p = 1
        limit = 12
        callback = ""
        order = "id desc"
        search = ""
        type_id = None
        try:
            if hasattr(get, "p"):
                p = int(get.p)
            if hasattr(get, "limit"):
                limit = int(get.limit)
            if hasattr(get, "callback"):
                callback = get.callback.strip()
            if hasattr(get, "order"):
                order = get.order.strip()
            if hasattr(get, "search"):
                search = get.search.strip()
            if hasattr(get, "type_id") and get.type_id:
                type_id = int(get.type_id)
        except:
            return json_response(False, '参数错误')
        
        type_filter = ''
        if type_id is not None:
            type_filter = ' AND type_id=?'
        
        if search:
            search = "%{}%".format(search)
            if type_filter:
                where_str = 'project_type=? AND (name LIKE ? OR ps LIKE ?)' + type_filter
                where_args = ('Java', search, search, type_id)
            else:
                where_str = 'project_type=? AND (name LIKE ? OR ps LIKE ?)'
                where_args = ('Java', search, search)
            count = public.M('sites').where(where_str, where_args).count()
            
            data = public.get_page(count, p, limit, callback)
            data['data'] = public.M('sites').where(where_str, where_args).limit(
                data['shift'] + ',' + data['row']
            ).order(order).select()
        else:
            if type_filter:
                where_str = 'project_type=?' + type_filter
                where_args = ('Java', type_id)
            else:
                where_str = 'project_type=?'
                where_args = ('Java',)
            count = public.M('sites').where(where_str, where_args).count()
            data = public.get_page(count, p, limit, callback)
            data['data'] = public.M('sites').where(where_str, where_args).limit(
                data['shift'] + ',' + data['row']
            ).order(order).select()
        
        for project_data in data['data']:
            project_config = json.loads(project_data['project_config'])
            project_data['project_config'] = project_config
            
            # 如果内置项目 或 独立项目 的tomcat配置文件丢失
            if project_config['java_type'] == 'neizhi':
                tomcat = utils.bt_tomcat(project_config["tomcat_version"])
            elif project_config['java_type'] == 'duli':
                if project_config.get("tomcat_name", ""):
                    tomcat = utils.site_tomcat(project_config["tomcat_name"])
                else:
                    tomcat = utils.site_tomcat(project_config["project_name"])
            else:
                continue
            if not tomcat:
                project_data["server_config_error"] = "Tomcat丢失请尝试修复项目"
            else:
                project_data["server_config_error"] = tomcat.check_config(
                    project_config["project_name"], project_data["path"],
                    project_config.get("access_mode", "domain")
                )

                #修正server_xml记录
                server_xml = project_config["server_xml"]
                config_path = CONFIG_PATH_TMPL.format(tomcat_path=tomcat.path)
                if server_xml != config_path:
                    project_config["server_xml"] = config_path
                    public.M('sites').where('id=?', (project_data['id'],)).setField('project_config', json.dumps(project_config))
        
        for i in range(len(data['data'])):
            self.get_project_stat(data['data'][i])
        
        return data
    
    @staticmethod
    def get_process_tree_listen_and_pids(pid: int):
        listen_list = []
        pids = []
        try:
            p = psutil.Process(pid)
            for connection in p.connections():
                if connection.status == 'LISTEN':
                    listen_list.append(connection.laddr.port)
            pids.append(pid)
            for subp in p.children(recursive = True):
                pids.append(subp.pid)
                for connection in subp.connections():
                    if connection.status == 'LISTEN':
                        listen_list.append(connection.laddr.port)
        except Exception as e:
            public.print_log(e)
            pass
        return pids, listen_list
    
    def get_project_stat(self, project_data: dict) -> dict:
        if isinstance(project_data['project_config'], str):
            project_config = json.loads(project_data['project_config'])
            project_data['project_config'] = project_config
        
        project_data["pid"] = self.get_project_pid(project_data)
        if project_data["project_config"]["java_type"] == "springboot":
            project_data["project_config"]["watch_file"] = use_project_watch(project_data["name"])
        project_data["listen"] = []
        project_data["ssl"] = RealSSLManger("java_").get_site_ssl_info(project_data["name"])
        if not project_data["ssl"]:
            project_data["ssl"] = -1
        if project_data["pid"]:
            project_data["pid_info"] = self.real_process.get_process_info_by_pid(project_data["pid"])["data"]
            pids, listen = self.get_process_tree_listen_and_pids(project_data["pid"])
            project_data["pid"] = ",".join([str(i) for i in pids])
            project_data["listen"] = listen
            if project_data['project_config']["java_type"] == "springboot":
                project_data['project_config']["port"] = ",".join([str(i) for i in listen])
        else:
            project_data["pid_info"] = None
        
        project_data["starting"] = False
        if project_data["pid"] and not project_data["listen"]:
            project_data["starting"] = True
        
        if os.path.exists("{}/nginx/{}.conf".format(self._vhost_path, project_data["name"])) or \
                os.path.exists("{}/apache/{}.conf".format(self._vhost_path, project_data["name"])):
            
            project_data["bind_extranet"] = True
        else:
            project_data["bind_extranet"] = False
        
        if project_data['project_config']["java_type"] == "duli" and "project_jdk" not in project_data[
            'project_config']:
            if project_data['project_config'].get("tomcat_name", ""):
                tomcat = utils.site_tomcat(project_data['project_config']["tomcat_name"])
            else:
                tomcat = utils.site_tomcat(project_data["name"])
            if tomcat:
                project_data['project_config']["project_jdk"] = tomcat.jdk_path
            else:
                project_data['project_config']["project_jdk"] = "/usr/local/btjdk/jdk8"
        
        return project_data
    
    @staticmethod
    def _project_domain_list(project_id: int):
        return public.M('domain').where('pid=?', (project_id,)).select()
    
    def project_domain_list(self, get):
        try:
            project_data = self.get_project_find(get.project_name.strip())
        except:
            return json_response(False, '参数错误')
        
        if not project_data:
            return json_response(False, '指定项目不存在')
        
        data = self._project_domain_list(project_data['id'])
        return json_response(True, data = data)
    
    def add_domains(self, get):
        """ 为指定项目添加域名 """
        try:
            if isinstance(get.domains, str):
                domains = json.loads(get.domains)
            else:
                domains = get.domains
            project_data = self.get_project_find(get.project_name.strip())
        except:
            return json_response(False, 'domains参数错误')
        
        if not isinstance(domains, list):
            return json_response(False, '域名参数错误')
        
        if not project_data:
            return json_response(False, '指定项目不存在')
        
        project_id = project_data['id']
        project_name = project_data["name"]
        
        domain_list, err = normalize_domain(*domains)
        if err:
            return "<br>".join(["域名：{}，错误信息：{}".format(i['domain'], i['msg']) for i in err])
        
        res_domains = []
        check_cloud = False
        for d, p in domain_list:
            if not public.M('domain').where('name=?', (d,)).count():
                public.M('domain').add('name,pid,port,addtime', (d, project_id, p, public.getDate()))
                self.write_project_log('成功添加域名{}到项目{}'.format(d, get.project_name))
                res_domains.append({"name": d, "status": True, "msg": '添加成功'})
                if not check_cloud:
                    public.check_domain_cloud(d)
                    check_cloud = True
            else:
                self.write_project_log('添加域名错误，域名{}已存在'.format(d))
                res_domains.append({"name": d, "status": False, "msg": '添加失败，域名{}已存在'.format(d)})
        all_domain = self._project_domain_list(project_id)
        # 写配置文件
        if utils.js_value_to_bool(project_data["project_config"]["bind_extranet"]):
            res = self._set_domain(project_data, [(i["name"], str(i["port"])) for i in all_domain])
            if res:
                return json_response(True, msg = "域名记录成功，但配置文件写入时失败:" + res, data = res_domains)
        # 更新Tomcat配置文件
        java_type = project_data["project_config"].get("java_type", "")
        if java_type != "springboot":
            if java_type == "neizhi":
                tomcat_obj = utils.bt_tomcat(ver = project_data["project_config"]["tomcat_version"])
            else:
                tomcat_obj = utils.site_tomcat(site_name = project_name)
            if not tomcat_obj:
                return json_response(False, "更新tomcat配置文件失败")
            for domain in [i["name"] for i in res_domains if i["status"]]:
                tomcat_obj.add_host(
                    name = domain,
                    path = project_data["path"],
                    context_path = project_name
                )
            if not tomcat_obj.save_config_xml():
                return json_response(False, "更新tomcat配置文件失败")
        return json_response(True, msg = "添加成功", data = res_domains)
    
    def remove_domains(self, get):
        """ 移除指定项目中的域名 """
        try:
            if isinstance(get.domains, str):
                remove_list = json.loads(get.domains)
            else:
                remove_list = get.domains
            project_data = self.get_project_find(get.project_name.strip())
        except:
            return json_response(False, '参数错误')
        
        if not project_data:
            return json_response(False, '指定项目不存在')
        
        if not isinstance(remove_list, list):
            return json_response(False, '域名参数错误')
        
        all_domain = self._project_domain_list(project_data["id"])
        if not all_domain:
            return json_response(False, '指定项目中没有域名可被删除')
        
        bind_extranet = False
        if os.path.exists("{}/nginx/java_{}.conf".format(self._vhost_path, project_data["name"])) or \
                os.path.exists("{}/apache/java_{}.conf".format(self._vhost_path, project_data["name"])):
            bind_extranet = True
        
        if len(all_domain) == 1 and bind_extranet:
            return json_response(
                False, '请至少保留一个域名，如无需外网映射，关闭即可', data = [{
                    "domain": all_domain[0]["name"],
                    "status": False,
                    "msg": "无法删除最后一个域名"
                }]
            )
        
        all_domain.sort(key = lambda x: x["id"], reverse = True)
        all_domain_id_dict = {i["id"]: i for i in all_domain}
        
        del_id_list = [i for i in all_domain_id_dict if i in remove_list]
        
        res_data = []
        # 说明选中了所有域名，这时需要保持一个默认域名
        default_domain = None
        if len(all_domain_id_dict) == len(del_id_list) and bind_extranet:
            default_domain = all_domain[0]
            del_id_list.remove(default_domain["id"])
        
        for i in del_id_list:
            public.M('domain').delete(id = i)
            res_data.append(
                {
                    "domain": all_domain_id_dict[i]["name"],
                    "status": True,
                    "msg": "删除成功"
                }
            )
        self.write_project_log('成功删除域名{}'.format([all_domain_id_dict[i]["name"] for i in del_id_list]))
        if default_domain:
            res_data.append(
                {
                    "domain": default_domain["name"],
                    "status": False,
                    "msg": "无法删除最后一个域名"
                }
            )
        
        if bind_extranet:
            now_domain = self._project_domain_list(project_data["id"])
            # 写配置文件
            res = self._set_domain(project_data, [(i["name"], str(i["port"])) for i in now_domain])
            if res:
                return json_response(False, msg = "域名记录删除成功，但配置文件写入时失败:" + res, data = res_data)
        
        # 更新Tomcat配置文件
        project_name = project_data["name"]
        java_type = project_data["project_config"].get("java_type", "")
        if java_type != "springboot":
            if java_type == "neizhi":
                tomcat_obj = utils.bt_tomcat(ver = project_data["project_config"]["tomcat_version"])
            else:
                tomcat_obj = utils.site_tomcat(site_name = project_name)
            if not tomcat_obj:
                return json_response(False, "更新tomcat配置文件失败")
            for domain in [i["domain"] for i in res_data if i["status"]]:
                tomcat_obj.remove_host(
                    host_name = domain,
                    context_path = project_name
                )
            if not tomcat_obj.save_config_xml():
                return json_response(False, "更新tomcat配置文件失败")
        
        return json_response(True, msg = "删除成功", data = res_data)
    
    def bind_extranet(self, get):
        """开放外网映射"""
        try:
            project_data = self.get_project_find(get.project_name.strip())
        except:
            return json_response(False, '参数错误')
        if not project_data:
            return json_response(False, '指定项目不存在: {}'.format(get.project_name))
        
        if not public.is_apache_nginx():
            return json_response(False, "未安装Nginx")
        
        err_msg = public.checkWebConfig()
        if isinstance(err_msg, str):
            msg = 'WEB服务器配置配置文件错误ERROR:<br><font style="color:red;">' + \
                  err_msg.replace("\n", '<br>') + '</font>'
            return json_response(False, msg = msg)
        
        res = self._open_config_file(project_data)
        if isinstance(res, str):
            return json_response(False, msg = res)
        project_config = project_data["project_config"]
        project_config["bind_extranet"] = 1
        public.M('sites').where('id=?', (project_data["id"],)).update(
            {"project_config": json.dumps(project_config)}
        )
        return json_response(True, msg = "设置成功")
    
    def unbind_extranet(self, get):
        """关闭外网映射"""
        try:
            project_data = self.get_project_find(get.project_name.strip())
        except:
            return json_response(False, '参数错误')
        if not project_data:
            return json_response(False, '指定项目不存在: {}'.format(get.project_name))
        
        project_config = project_data["project_config"]
        self._close_apache_config_file(project_data)
        project_config["bind_extranet"] = 0
        public.M('sites').where('id=?', (project_data["id"],)).update(
            {"project_config": json.dumps(project_config)}
        )
        return json_response(True, msg = "设置成功")
    
    def remove_project(self, get):
        """删除指定项目"""
        try:
            project_data = self.get_project_find(get.project_name.strip())
        except:
            return json_response(False, '参数错误')
        
        if not project_data:
            return json_response(False, '指定项目不存在: {}'.format(get.project_name))
        
        project_config = project_data["project_config"]
        project_name = project_data["name"]
        if project_config['java_type'] == 'duli':
            if project_config.get("tomcat_name", ""):
                tomcat = utils.site_tomcat(project_config["tomcat_name"])
            else:
                tomcat = utils.site_tomcat(project_name)
            # 关闭独立项目
            if tomcat:
                tomcat.stop()
                tomcat.remove_service()
            if os.path.exists(path = tomcat.path):
                shutil.rmtree(tomcat.path)
        
        elif project_config['java_type'] == 'neizhi':
            # 删除tomcat站点
            try:
                domains = project_config.get("domains", project_config.get("domain", ""))
                domain = (domains[0] if isinstance(domains, list) and domains else domains).split(":")[0]
                tomcat = utils.bt_tomcat(project_config["tomcat_version"])
                tomcat.remove_host(domain, project_name)
                tomcat.save_config_xml()
                if tomcat.running():
                    tomcat.restart()
            except:
                return json_response(False, '删除Tomcat配置失败，请尝试修复Tomcat后再次删除项目')
        
        elif project_config['java_type'] == 'springboot':
            # 停止项目
            server_name = self._get_systemd_server_name(project_config)
            s_admin = RealServer()
            s_admin.daemon_admin(server_name, "stop")
            s_admin.del_daemon(server_name)
            
            pid_file = project_config['pids']
            if os.path.exists(pid_file):
                os.remove(pid_file)
            script_file = project_config['scripts']
            if os.path.exists(script_file):
                os.remove(script_file)
            env_path = "{}/env/{}.env".format(self._java_project_vhost, project_config["project_name"])
            if os.path.exists(env_path):
                os.remove(env_path)
            log_file = project_config['logs']
            if os.path.exists(log_file):
                os.remove(log_file)
        else:
            return json_response(False, '项目类型错误')
        
        # !区分开项目名
        threading.Thread(target = remove_sites_service_config, args = (project_name, "java_")).start()
        public.M('domain').where('pid=?', (project_data['id'],)).delete()
        public.M('sites').where('name=?', (project_name,)).delete()
        self.write_project_log('删除Java项目{}'.format(get.project_name))
        return json_response(True, '删除项目成功')
    
    def config_file_list(self, get):
        """获取配置文件列表"""
        try:
            project_data = self.get_project_find(get.project_name.strip())
        except:
            return json_response(False, '参数错误')
        
        if not project_data:
            return json_response(False, '指定项目不存在: {}'.format(get.project_name))
        project_name = project_data["name"]
        res_list = []
        bind_extranet = int(project_data["project_config"]["bind_extranet"]) != 0
        if bind_extranet:
            if public.get_webserver() == "nginx":
                config_file = "{}/nginx/java_{}.conf".format(self._vhost_path, project_name)
                res_list.append(
                    {
                        "name": "nginx配置文件",
                        "path": config_file,
                        "status": os.path.exists(config_file),
                        "type": "server"
                    }
                )
            else:
                config_file = "{}/apache/java_{}.conf".format(self._vhost_path, project_name)
                res_list.append(
                    {
                        "name": "apache配置文件",
                        "path": config_file,
                        "status": os.path.exists(config_file),
                        "type": "server"
                    }
                )
            rewrite_file = "{}/rewrite/java_{}.conf".format(self._vhost_path, project_name)
            res_list.append(
                {
                    "name": "伪静态配置文件",
                    "path": rewrite_file,
                    "status": os.path.exists(rewrite_file),
                    "type": "rewrite"
                }
            )
            
            p_list = RealProxy("java_").get_proxy_list(public.to_dict_obj({"sitename": project_name}))
            f, r_list = RealRedirect("java_").get_redirect_list(public.to_dict_obj({"sitename": project_name}))
            for p in p_list:
                res_list.append(
                    {
                        "name": "反向代理【{}】".format(p["proxyname"]),
                        "path": p["proxy_conf_file"],
                        "status": os.path.exists(p["proxy_conf_file"]),
                        "type": "proxy"
                    }
                )
            
            if f:
                for r in r_list:
                    res_list.append(
                        {
                            "name": "重定向",
                            "path": r["redirect_conf_file"],
                            "status": os.path.exists(r["redirect_conf_file"]),
                            "type": "redirect"
                        }
                    )
        
        if project_data["project_config"]["java_type"] == "neizhi":
            tomcat = utils.bt_tomcat(project_data["project_config"]["tomcat_version"])
            res_list.append(
                {
                    "name": "Tomcat【{}】配置文件".format(project_data["project_config"]["tomcat_version"]),
                    "path": os.path.join(tomcat.path, "conf/server.xml"),
                    "status": tomcat.installed,
                    "type": "tomcat"
                }
            )
        elif project_data["project_config"]["java_type"] == "duli":
            if project_data["project_config"].get("tomcat_name", ""):
                tomcat = utils.site_tomcat(project_data["project_config"]["tomcat_name"])
            else:
                tomcat = utils.site_tomcat(project_data["name"])
            res_list.append(
                {
                    "name": "Tomcat配置文件",
                    "path": os.path.join(tomcat.path, "conf/server.xml"),
                    "status": tomcat.installed,
                    "type": "tomcat"
                }
            )
        else:
            try:
                pid = self.get_project_pid(project_data)
                if not pid:
                    pid = 0
                spc = SpringConfigParser(
                    jar_path = project_data["project_config"]["project_jar"],
                    process = pid,
                )
                used, _ = spc.app_config()
                show_spring_config = []
                for i, _ in used[::-1]:  # 按照优先级排序
                    if i == "命令行或环境变量":
                        continue
                    f_name = os.path.basename(i)
                    if f_name in show_spring_config:
                        continue
                    else:
                        show_spring_config.append(f_name)
                    profile = f_name[len(spc.config_name):]  # 取出 - + profile + 后缀部分
                    if profile in (".yml", ".yaml", ".properties"):
                        profile = ""
                    else:
                        profile = profile.rsplit(".", 1)[0]
                    res_list.append(
                        {
                            "name": "Spring配置" + profile,
                            "path": i,
                            "status": True,
                            "type": "local_spring" if i.startswith("/") else "spring",
                            "data": spc.raw_data.get(i, "")
                        }
                    )
            except:
                pass
        
        sort_tuple = {
            "local_spring": 10,
            "spring": 9,
            "tomcat": 8,
            "server": 11,
            "proxy": 6,
            "redirect": 5,
            "rewrite": 4,
            
        }
        res_list.sort(key = lambda x: sort_tuple[x["type"]], reverse = True)
        return json_response(True, data = res_list)
    
    # 未使用
    def project_log_list(self, get):
        """获取日志文件列表"""
        try:
            project_data = self.get_project_find(get.project_name.strip())
        except:
            return json_response(False, '参数错误')
        
        if not project_data:
            return json_response(False, '指定项目不存在: {}'.format(get.project_name))
        project_name = project_data["name"]
        res = RealLogMgr(conf_prefix = "java_").get_site_log_path(public.to_dict_obj({"sitename": project_name}))
        res_list = []
        if isinstance(res, str):
            res_list.extend(
                [
                    {"type": "access", "path": None, "log_size": 0, "msg": "无法从配置文件中获取日志文件路径"},
                    {"type": "error", "path": None, "log_size": 0, "msg": "无法从配置文件中获取错误日志文件路径"}
                ]
            )
        else:
            access_file = res["log_file"]
            error_file = res["error_log_file"]
            access_file_size = error_file_size = 0
            if os.path.isfile(access_file):
                access_file_size = os.path.getsize(access_file)
            
            if os.path.isfile(error_file):
                error_file_size = os.path.getsize(error_file)
            
            res_list.extend(
                [
                    {"type": "access", "path": access_file, "log_size": access_file_size, "msg": ""},
                    {"type": "error", "path": error_file, "log_size": error_file_size, "msg": ""}
                ]
            )
        
        project_config = project_data["project_config"]
        if project_config["java_type"] == "springboot":
            log_file = project_config['logs']
            if not os.path.isfile(log_file):
                pass
    
    def get_command(self, get):
        """获取命令， 包含设置和取消jmx的设置"""
        project_cmd = None
        jmx_status = None
        try:
            if hasattr(get, "project_cmd"):
                project_cmd = get.project_cmd.strip()
            if hasattr(get, "jmx_status"):
                jmx_status = utils.js_value_to_bool(get.jmx_status)
            project_jdk = utils.normalize_jdk_path(get.project_jdk.strip())
            project_jar = get.project_jar.strip()
        except json.JSONDecodeError:
            return json_response(False, '参数错误')
        
        if not isinstance(project_jdk, str):
            return json_response(False, '项目JDK路径不存在')
        
        project_jdk = os.path.join(project_jdk, "bin/java")
        if not os.path.isfile(project_jdk):
            return json_response(False, '项目JDK不存在')
        if not os.path.isfile(project_jar):
            return json_response(False, '项目jar不存在')
        
        if not isinstance(project_cmd, str) and project_cmd:
            cmd = '{} -jar -Xmx1024M -Xms256M {} '.format(project_jdk, project_jar)
            cmd = self._build_jmx_cmd(cmd, jmx_status)
        
        else:
            cmd = self._build_jmx_cmd(project_cmd, jmx_status)
        
        return json_response(True, data = cmd)
    
    def set_project_log_status(self, get):
        """设置项目日志是否开启"""
        try:
            project_data = self.get_project_find(get.project_name.strip())
            status = utils.js_value_to_bool(get.status)
        except:
            return json_response(False, '参数错误')
        if not project_data:
            return json_response(False, '指定项目不存在: {}'.format(get.project_name))
        
        if project_data["project_config"]["java_type"] == "springboot":
            project_config = project_data["project_config"]
            project_config["nohup_log"] = status
            project_config["change_flag"] = True
            pdata = {
                'project_config': json.dumps(project_config)
            }
            public.M('sites').where('id=?', (project_data["id"],)).update(pdata)
            
            return json_response(True, "修改成功, 重启项目后生效")
        else:
            return json_response(False, "非springboot项目无法关闭")
    
    def get_jmx_status(self, get):
        """设置项目日志是否开启"""
        try:
            project_data = self.get_project_find(get.project_name.strip())
        except:
            return json_response(False, '参数错误')
        if not project_data:
            return json_response(False, '指定项目不存在: {}'.format(get.project_name))
        
        project_config = project_data["project_config"]
        if not project_config["java_type"] == "springboot":
            return json_response(False, "目前支持springboot 项目的jmx 监控")
        
        pid = self.get_project_pid(project_data)
        if not pid:
            return json_response(False, "未启动的项目，不能获取jmx信息")
        
        jmx_info = self.get_jmx_data_by_pid(pid)
        if not jmx_info:
            return json_response(False, "项目未启用jmx，无法获取jmx信息")
        jmx_url = 'service:jmx:rmi:///jndi/rmi://{}:{}/jmxrmi'.format(jmx_info["host"], jmx_info["port"])
        
        from mod.project.java.jmxquery import JMXConnection, JMXQuery
        try:
            # 创建 JMXConnection
            # JMX 连接信息
            jmxConnection = JMXConnection(
                connection_uri = jmx_url,
                java_path = os.path.join(project_config["project_jdk"], "bin/java")
            )
            jmxQuery = [JMXQuery("*:*")]
            # 执行查询
            metrics = jmxConnection.query(jmxQuery)
        except Exception:
            public.print_log(public.get_error_info())
            return json_response(False, "连接失败！ {}".format(jmx_url))
        
        # 创建 JMX 查询
        jmx_status_info = {}
        type_list = ["MemoryPool", "GarbageCollector"]
        percent_list = ["SystemCpuLoad", "ProcessCpuLoad"]
        microsecond_list = [
            "StartTime", "Uptime", "endTime", "startTime", "CollectionTime", "CurrentThreadCpuTime",
            "CurrentThreadUserTime", "endTime", "startTime", "CollectionTime", "TotalCompilationTime",
        ]
        nanoseconds_list = ["ProcessCpuTime", ]
        size_list = ["FreePhysicalMemorySize", "TotalPhysicalMemorySize", "committed", "init", "max", "used"]
        value_dict = {
            "True": "是",
            "False": "否",
            "None": "无",
        }
        
        # 解析结果
        for metric in metrics:
            java_type_obj = re.search(r"type=([\w\s]+)", metric.mBeanName)
            if not java_type_obj:
                continue
            java_type = java_type_obj.group(1)
            name_obj = re.search(r"name=([\w\s]+)", metric.mBeanName)
            name = None
            if name_obj:
                name = name_obj.group(1)
            
            if jmx_status_info.get(java_type) is None:
                if java_type in type_list:
                    jmx_status_info[java_type] = []
                else:
                    jmx_status_info[java_type] = {}
            type_info: Union[Dict[str, Any], List[Dict[str, Any]]] = jmx_status_info[java_type]
            
            if name is not None:
                name = name.replace(" ", "_")
                if isinstance(type_info, list):
                    for info in type_info:
                        if info["name"] == name:
                            type_info = info
                            break
                    else:
                        info = {"name": name}
                        type_info.append(info)
                        type_info = info
                else:
                    if type_info.get(name) is None:
                        type_info[name] = {}
                    type_info = type_info[name]
            
            value = value_dict.get(str(metric.value))
            if value is None:
                value = metric.value
            
            if metric.attributeKey:
                if metric.attribute is not None and type_info.get(metric.attribute) is None:
                    type_info[metric.attribute] = {}
                
                if value == -1:
                    value = "无限制"
                elif metric.attributeKey in size_list:
                    value = public.to_size(value)
                elif metric.attributeKey in microsecond_list:
                    value = datetime.fromtimestamp(int(value) / 1000).strftime('%Y-%m-%d %H:%M:%S')
                elif metric.attributeKey in nanoseconds_list:
                    value = "{} 秒".format(int(value) / 1e9)
                
                type_info[metric.attribute][metric.attributeKey] = value
            else:
                if metric.attribute in size_list:
                    value = public.to_size(value)
                elif metric.attribute in percent_list:
                    value = "{}%".format(round(int(value) * 100, 2))
                elif metric.attribute in microsecond_list:
                    value = datetime.fromtimestamp(int(value) / 1000).strftime('%Y-%m-%d %H:%M:%S')
                elif metric.attribute in nanoseconds_list:
                    value = "{} 秒".format(int(value) / 1e9)
                type_info[metric.attribute] = value
        
        return json_response(True, data = jmx_status_info)
    
    @staticmethod
    def get_jmx_data_by_pid(pid) -> Optional[dict]:
        try:
            p = psutil.Process(pid)
            cmd_line = p.cmdline()
        except:
            return None
        
        data = {
            "port": "",
            "host": "127.0.0.1"
        }
        for i in cmd_line:
            if i.startswith("-Dcom.sun.management.jmxremote.port"):
                data["port"] = i.split("=")[1]
            
            if i.startswith("-Djava.rmi.server.hostname"):
                data["host"] = i.split("=")[1]
        if not data["port"]:
            return None
        return data
    
    def get_project_info(self, get):
        """设置项目日志是否开启"""
        try:
            project_data = self.get_project_find(get.project_name.strip())
        except:
            return json_response(False, '参数错误')
        if not project_data:
            return json_response(False, '指定项目不存在: {}'.format(get.project_name))
        
        project_data = self.get_project_stat(project_data)
        return json_response(True, data = project_data)
    
    # 上传版本
    def upload_version(self, get):
        """
        上传压缩包并存储为版本
        """
        if not hasattr(get, 'sitename'):
            return json_response(False, '项目名称不能为空')
        if not hasattr(get, 'version'):
            return json_response(False, '版本号不能为空')
        if not hasattr(get, 'ps'):
            get.ps = ''
        try:
            upload_files = os.path.join("/tmp", get.f_name)
            if "/www/server/panel/class" not in sys.path:
                sys.path.insert(0, "/www/server/panel/class")
            
            from files import files
            
            file_obj = files()
            ff = file_obj.upload(get)
            if type(ff) == int:
                return ff
            if not ff['status']:
                return json_response(False, ff['msg'])
            
            output_dir = str(os.path.join('/tmp', public.GetRandomString(16)))
            os.makedirs(output_dir, 777)
            is_jar_war = os.path.splitext(upload_files)[-1] in (".jar", ".war")
            if not self.extract_archive(upload_files, output_dir)[0] and not is_jar_war:
                return json_response(False, '解压失败,仅支持zip,tar.gz,tar,bz2,gz格式的压缩包')
            
            version_tool = VersionTool()
            if not is_jar_war:
                if len(os.listdir(output_dir)) == 1:
                    real_output_dir = str(os.path.join(output_dir, os.listdir(output_dir)[0]))
                    if os.path.isdir(real_output_dir):
                        output_dir = real_output_dir
                
                res = version_tool.publish_by_src_path(get.sitename, output_dir, get.version, get.ps, sync = True)
                public.ExecShell('rm -rf {}'.format(output_dir))
                public.ExecShell('rm -rf {}'.format(upload_files))
            else:
                res = version_tool.publish_by_file(get.sitename, upload_files, get.version, get.ps)
                public.ExecShell('rm -rf {}'.format(upload_files))
            if res is None:
                return public.returnResult(True, '添加成功')
            return json_response(False, '添加失败' + res)
        except:
            return json_response(False, traceback.format_exc())
    
    @staticmethod
    def extract_archive(file_path, output_dir):
        try:
            import tarfile
            import zipfile
            import gzip
            import bz2
            
            name = os.path.basename(file_path)
            if name.endswith('.tar.gz'):
                with tarfile.open(file_path, 'r:gz') as tar:
                    tar.extractall(output_dir)
            elif name.endswith('.zip'):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(output_dir)
            elif name.endswith('.gz'):
                with gzip.open(file_path, 'rb') as f_in, open(os.path.join(output_dir, name[:-3]), 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            elif name.endswith('.tar'):
                with tarfile.open(file_path, 'r') as tar:
                    tar.extractall(output_dir)
            elif name.endswith('.bz2'):
                with open(file_path, 'rb') as f_in, open(os.path.join(output_dir, name[:-4]), 'wb') as f_out:
                    with bz2.BZ2File(f_in) as bz:
                        shutil.copyfileobj(bz, f_out)
            else:
                return False, '文件格式错误.'
        except:
            return False, '解压失败'
        
        return True, '解压成功'
    
    # 获取列表
    @staticmethod
    def get_version_list(get):
        if not hasattr(get, 'sitename'):
            return public.returnResult(False, '项目名称不能为空')
        version_tool = VersionTool()
        return json_response(True, data = version_tool.version_list(get.sitename))
    
    # 删除版本
    @staticmethod
    def remove_version(get):
        if not hasattr(get, 'sitename'):
            return json_response(False, '项目名称不能为空')
        if not hasattr(get, 'version'):
            return json_response(False, '版本号不能为空')
        version_tool = VersionTool()
        if version_tool.remove(get.sitename, get.version) is None:
            return public.returnResult(True, '删除成功')
        return json_response(False, '删除失败')
    
    # 恢复版本
    def recover_version(self, get):
        try:
            if not hasattr(get, 'sitename'):
                return json_response(False, '项目名称不能为空')
            if not hasattr(get, 'version'):
                return json_response(False, '版本号不能为空')
            
            project_data = self.get_project_find(get.sitename)
            if not project_data:
                return json_response(False, '指定项目不存在: {}'.format(get.sitename))
            
            version_tool = VersionTool()
            project_config = project_data['project_config']
            # spring jar 包情况
            if project_config["java_type"] == "springboot":
                v_info = version_tool.get_version_info(get.sitename, get.version)
                if not v_info:
                    return json_response(False, '指定版本不存在: {}'.format(get.version))
                
                path = os.path.join(version_tool.pack_path, v_info['zip_name'])
                if not os.path.isfile:
                    return json_response(False, '指定版本文件丢失')
                if os.path.exists(project_config["project_jar"] + "_back"):
                    os.remove(project_config["project_jar"] + "_back")
                if not path.endswith(".jar"):  # 如果不是jar包，则解压并寻找jar包
                    output_dir = str(os.path.join('/tmp', public.GetRandomString(16)))
                    os.makedirs(output_dir, 777)
                    if not self.extract_archive(path, output_dir)[0]:
                        return json_response(False, '解压失败')
                    else:
                        for f in os.listdir(output_dir):
                            if f.endswith(".jar"):
                                path = os.path.join(output_dir, f)
                                break
                        else:
                            return json_response(False, '未找到jar包文件')
                
                shutil.move(project_config["project_jar"], project_config["project_jar"] + "_back")
                shutil.copyfile(path, project_config["project_jar"])
                
                return json_response(True, "版本文件替换成功，重启后生效")
            # war 包
            v_info = version_tool.get_version_info(get.sitename, get.version)
            if not v_info:
                return json_response(False, '指定版本不存在: {}'.format(get.version))
            path = os.path.join(version_tool.pack_path, v_info['zip_name'])
            if path.endswith(".war") and os.path.isfile(project_data["path"]):  # 如果是war包
                if os.path.exists(project_data["path"] + "_back"):
                    os.remove(project_data["path"] + "_back")
                shutil.move(project_data["path"], project_data["path"] + "_back")
                shutil.copyfile(path, project_data["path"])
                return json_response(True, "版本文件替换成功，重启后生效")
            
            res = version_tool.recover(get.sitename, get.version, project_data['path'])
            if res is not True:
                return json_response(False, res)
            return json_response(True, '恢复成功')
        except:
            return json_response(False, traceback.format_exc())
    
    def now_file_backup(self, get):
        try:
            if not hasattr(get, 'sitename'):
                return json_response(False, '项目名称不能为空')
            if not hasattr(get, 'version') or not get.version.strip():
                return json_response(False, '版本号不能为空')
            else:
                get.version = get.version.strip()
            if not hasattr(get, 'ps'):
                get.ps = ''
            project_data = self.get_project_find(get.sitename)
            if not project_data:
                return json_response(False, '指定项目不存在: {}'.format(get.sitename))
            path = project_data['path']
            version_tool = VersionTool()
            project_config = project_data['project_config']
            if project_config["java_type"] == "springboot":
                res = version_tool.publish_by_file(get.sitename, project_config["project_jar"], get.version, get.ps)
            else:
                if os.path.isdir(path):
                    res = version_tool.publish_by_src_path(get.sitename, path, get.version, get.ps, sync = True)
                elif os.path.isfile(path):
                    res = version_tool.publish_by_file(get.sitename, path, get.version, get.ps)
                else:
                    return json_response(False, '添加失败')
            if res is None:
                return json_response(True, '添加成功')
            return json_response(False, '添加失败:' + res)
        except:
            return json_response(False, traceback.format_exc())
    
    @staticmethod
    def set_version_ps(get):
        if not hasattr(get, 'sitename'):
            return json_response(False, '项目名称不能为空')
        if not hasattr(get, 'version'):
            return json_response(False, '版本号不能为空')
        if not hasattr(get, 'ps'):
            get.ps = ''
        version_tool = VersionTool()
        res = version_tool.set_ps(get.sitename, get.version, get.ps)
        if not res:
            return json_response(False, '设置失败')
        return json_response(True, '设置成功')
    
    def change_log_path(self, get):
        """"修改日志文件地址
        @author baozi <202-03-13>
        @param:
            get  ( dict ):  请求: 包含项目名称和新的路径
        @return
        """
        try:
            project_data = self.get_project_find(get.project_name.strip())
            new_log_path = get.path.strip().rstrip("/")
        except:
            return json_response(False, '参数错误')
        if not project_data:
            return json_response(False, '项目不存在')
        if not new_log_path.startswith('/'):
            return json_response(False, '路径格式错误')
        if not os.path.exists(new_log_path):
            os.makedirs(new_log_path, mode = 0o777)
        
        project_config = project_data["project_config"]
        if project_config['java_type'] == 'springboot':
            project_config['logs'] = new_log_path + '/' + project_data["name"] + '.log'
            project_config["change_flag"] = True
            pdata = {
                'name': project_data["name"],
                'project_config': json.dumps(project_config)
            }
            public.M('sites').where('id=?', (project_data["id"],)).update(pdata)
            # 重启项目
            res = self.restart_project(get)
            self.write_project_log('修改Java项目{}日志路径为:{}'.format(get.project_name, new_log_path))
            return json_response(True, "项目日志路径修改成功")
        elif project_config['java_type'] == 'duli':
            project_config['logs'] = new_log_path + '/'
            if project_config.get("tomcat_name", ""):
                tomcat = utils.site_tomcat(project_config["tomcat_name"])
            else:
                tomcat = utils.site_tomcat(project_data["name"])
            if not tomcat.change_log_path(new_log_path, project_data["name"].replace(".", "_")):
                return public.returnMsg(False, "项目日志路径修改失败")
            pdata = {
                'name': project_data["name"],
                'project_config': json.dumps(project_config)
            }
            public.M('sites').where('name=?', (get.project_name.strip(),)).update(pdata)
            # 重启项目
            tomcat.restart()
            self.write_project_log('修改Java项目{}日志路径为:{}'.format(get.project_name, new_log_path))
            return json_response(True, "项目日志路径修改成功")
        
        elif project_config['java_type'] == 'neizhi':
            tomcat = utils.bt_tomcat(project_config['tomcat_version'])
            if not tomcat.change_log_path(new_log_path, str(project_config['tomcat_version'])):
                return public.returnMsg(False, "项目日志路径修改失败")
            
            tomcat.restart()
            self.write_project_log('修改Java项目{}日志路径为:{}'.format(get.project_name, new_log_path))
            return json_response(True, "项目日志路径修改成功")
        else:
            return json_response(False, "项目类型错误")
    
    def multi_remove_project(self, get):
        """
            @name 批量删除项目
            @author baozi<2023-3-2>
            @param get<dict_obj>{
                project_names: list[string] <项目名称>所组成的列表
            }
            @return dict
        """
        try:
            project_names = get.project_names
            if isinstance(project_names, list):
                project_names = [i.strip() for i in project_names]
            else:
                project_names = []
        except:
            return json_response(False, "参数错误")
        if not project_names:
            return json_response(False, "未选中要删除的站点")
        
        projects = public.M('sites').where(
            'project_type=? AND name in ({})'.format(",".join(["?"] * len(project_names))),
            ('Java', *project_names)
        ).select()
        
        if not projects:
            return public.returnMsg(False, "未选中要删除的站点")
        
        _duli, _neizh, _springboot = [], [], []
        for project in projects:
            project['project_config'] = json.loads(project['project_config'])
            if project['project_config']['java_type'] == 'duli':
                _duli.append(project)
            elif project['project_config']['java_type'] == 'neizhi':
                _neizh.append(project)
            elif project['project_config']['java_type'] == 'springboot':
                _springboot.append(project)
        
        # 执行每种删除的独特操作
        if _duli:
            self._multi_remove_duli(_duli)
        if _neizh:
            self._multi_remove_neizhi(_neizh)
        if _springboot:
            self._multi_remove_springboot(_springboot)
        
        # 清除Nginx， Apache 配置文件，并重起服务
        for i in projects:
            remove_sites_service_config(i["name"], config_prefix = "java_")
        
        # 从面板数据库删除信息
        project_ids = tuple([i["id"] for i in projects])
        public.M('domain').where('pid IN ({})'.format(",".join(["?"] * len(projects))), project_ids).delete()
        public.M('sites').where('id IN ({})'.format(",".join(["?"] * len(project_ids))), project_ids).delete()
        self.write_project_log('批量删除Java项目:[{}]'.format("; ".join([i["name"] for i in projects])))
        
        for project in projects:
            self.del_crontab(project["name"])
        
        return json_response(True, "删除项目成功", data = [i["name"] for i in projects])
    
    @staticmethod
    def _multi_remove_duli(projects):
        for project in projects:
            # 关闭独立项目
            tomcat = utils.site_tomcat(project["name"])
            if tomcat:
                tomcat.stop()
                tomcat.remove_service()
                if os.path.exists(tomcat.path):
                    shutil.rmtree(tomcat.path)
    
    @staticmethod
    def _multi_remove_neizhi(projects):
        used_tomcat: Dict[int, utils.TomCat] = {}
        for project in projects:
            ver = int(project['project_config']['tomcat_version'])
            if ver in used_tomcat:
                tomcat = used_tomcat[ver]
            else:
                tomcat = utils.bt_tomcat(ver)
                if not tomcat:
                    continue
                used_tomcat[ver] = tomcat
            
            tomcat.remove_host(project["name"])
        
        for t in used_tomcat.values():
            t.save_config_xml()
            t.restart()
    
    def _multi_remove_springboot(self, projects):
        for project in projects:
            # 停止项目
            project_config = project["project_config"]
            server_name = self._get_systemd_server_name(project_config)
            s_admin = RealServer()
            s_admin.daemon_admin(server_name, "stop")
            s_admin.del_daemon(server_name)
            
            pid_file = project_config['pids']
            if os.path.exists(pid_file):
                os.remove(pid_file)
            script_file = project_config['scripts']
            if os.path.exists(script_file):
                os.remove(script_file)
            env_path = "{}/env/{}.env".format(self._java_project_vhost, project_config["project_name"])
            if os.path.exists(env_path):
                os.remove(env_path)
            log_file = project_config['logs']
            if os.path.exists(log_file):
                os.remove(log_file)
    
    def multi_set_project(self, get):
        """
            @name 批量设置项目
            @author baozi<2023-3-2>
            @param get<dict_obj>{
                project_names: list[string] <项目名称>所组成的列表
            }
            @return dict
        """
        try:
            project_names = get.project_names
            set_type = get.operation.strip()
        except:
            return json_response(False, "参数错误")
        if set_type not in ["start", "stop"]:
            return public.returnMsg(False, "操作信息错误")
        if isinstance(project_names, list):
            project_names = [i.strip() for i in project_names]
        else:
            project_names = []
        
        projects = public.M('sites').where(
            'project_type=? AND name in ({})'.format(",".join(["?"] * len(project_names))),
            ('Java', *project_names)
        ).select()
        
        if not projects:
            return json_response(False, "未选中要启动的站点")
        
        project_names = [i["name"] for i in projects]
        spring_boot_projects = []
        duli_tomcat = []
        bt_tomcat = {}
        error_list = []
        for project in projects:
            project['project_config'] = json.loads(project['project_config'])
            if project['project_config']['java_type'] == 'neizhi':
                ver = int(project['project_config']['tomcat_version'])
                if ver not in bt_tomcat:
                    tomcat = utils.bt_tomcat(project['project_config']['tomcat_version'])
                    if not tomcat:
                        error_list.append(
                            {
                                "project_name": project["name"], "msg": "启动失败,没有安装Tomcat{}".format(
                                project['project_config']['tomcat_version']
                            )
                            }
                        )
                        project_names.remove(project["name"])
                        continue
                    bt_tomcat[ver] = tomcat
            
            if project['project_config']['java_type'] == 'duli':
                if project['project_config'].get("tomcat_name", ""):
                    tomcat = utils.site_tomcat(project['project_config']["tomcat_name"])
                else:
                    tomcat = utils.site_tomcat(project["name"])
                if tomcat:
                    duli_tomcat.append(tomcat)
            
            if project['project_config']['java_type'] == 'springboot':
                spring_boot_projects.append(project)
        
        for t in itertools.chain(bt_tomcat.values(), duli_tomcat):
            if set_type == "start":
                t.start()
            else:
                t.stop()
        
        for i in spring_boot_projects:
            if set_type == "start":
                self.start_project(public.to_dict_obj({"project_name": i["name"]}))
            else:
                self.stop_project(public.to_dict_obj({"project_name": i["name"]}))
        
        if error_list:
            return json_response(
                True, msg = "部分项目操作失败", data = {
                    "error_list": error_list,
                    "project_names": project_names
                }
            )
        return json_response(
            True, msg = "启动成功" if set_type == "start" else "停止成功", data = {
                "project_names": project_names
            }
        )
    
    @staticmethod
    def del_crontab(project_name: str):
        """
        @name 删除项目日志切割任务
        @auther hezhihong<2022-10-31>
        @return
        """
        cron_name = '[勿删]Java项目[{}]运行日志切割'.format(project_name)
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
    
    def get_load_info(self, get):
        try:
            project_data = self.get_project_find(get.project_name.strip())
        except:
            return json_response(False, '参数错误')
        
        if not project_data:
            return json_response(False, "未找到项目")
        
        pid = self.get_project_pid(project_data)
        if not pid:
            return json_response(False, "项目未启动")
        
        res = self.real_process.get_process_tree(pid)
        if isinstance(res["data"], list):
            res["data"] = {i.get("pid", "0"): i for i in res["data"]}
        return res
    
    def get_port_status(self, get):
        try:
            project_data = self.get_project_find(get.project_name.strip())
        except:
            return json_response(False, '参数错误')
        
        if not project_data:
            return json_response(False, "未找到项目")
        
        pid = self.get_project_pid(project_data)
        if not pid:
            return json_response(False, "项目未启动")
        
        _, ports = self.get_process_tree_listen_and_pids(pid)
        
        if not ports:
            return json_response(False, "未找到端口")
        
        res = {str(i): {
            "port": i,
            "fire_wall": None,
            "nginx_proxy": None,
        } for i in ports}
        
        from firewallModel.comModel import main
        port_list = main().port_rules_list(get)["data"]
        for i in port_list:
            if str(i["Port"]) in res:
                res[str(i["Port"])]['fire_wall'] = i
        
        rsp = RealServerProxy(project_data)
        proxy_list = rsp.get_proxy_list()
        for i in proxy_list:
            if str(i["proxy_port"]) in res:
                res[str(i["proxy_port"])]['nginx_proxy'] = i
        
        return json_response(True, "获取成功", data = list(res.values()))
    
    def add_server_proxy(self, get):
        if not hasattr(get, "site_name") or not get.site_name.strip():
            return json_response(status = False, msg = "参数错误")
        
        project_data = self.get_project_find(get.site_name)
        if not project_data:
            return json_response(False, "未找到项目")
        
        rp = RealServerProxy(project_data)
        proxy_data = rp.check_args(get, is_modify = False)
        if isinstance(proxy_data, str):
            return json_response(status = False, msg = proxy_data)
        
        # 使用正则匹配尝试添加
        res = rp.create_proxy(proxy_data)
        if res is None:
            return json_response(status = True, msg = "添加成功")
        
        # 尝试模板生成
        proxy_info = project_data['project_config'].get("proxy_info", [])
        proxy_info.append(proxy_data)
        project_data['project_config']['proxy_info'] = proxy_info
        domain_list = self._project_domain_list(project_data['id'])
        domains = [(i["name"], str(i["port"])) for i in domain_list]
        
        ssl, f_ssl = self._get_ssl_status(project_data['name'])
        error_msg = self.create_config(project_data, domains, ssl, f_ssl)
        if not error_msg:
            public.serviceReload()
            pdata = {
                'project_config': json.dumps(project_data['project_config'])
            }
            public.M("sites").where("id=?", (project_data['id'],)).update(pdata)
            return json_response(status = True, msg = "添加成功")
        
        return json_response(status = False, msg = error_msg)
    
    def modify_server_proxy(self, get):
        if not hasattr(get, "site_name") or not get.site_name.strip():
            return json_response(status = False, msg = "参数错误")
        
        project_data = self.get_project_find(get.site_name)
        if not project_data:
            return json_response(False, "未找到项目")
        
        rp = RealServerProxy(project_data)
        proxy_data = rp.check_args(get, is_modify = True)
        if isinstance(proxy_data, str):
            return json_response(status = False, msg = proxy_data)
        
        proxy_info = project_data['project_config'].get("proxy_info", [])
        idx = None
        for index, i in enumerate(proxy_info):
            if i["proxy_id"] == proxy_data["proxy_id"] and i["site_name"] == proxy_data["site_name"]:
                idx = index
                break
        
        if idx is None:
            return json_response(status = False, msg = "未找到该id的反向代理配置")
        
        # 使用正则匹配尝试添加
        res = rp.modify_proxy(proxy_data)
        if res is None:
            return json_response(status = True, msg = "修改成功")
        
        # 尝试模板生成
        proxy_info[idx] = proxy_data
        project_data['project_config']['proxy_info'] = proxy_info
        domain_list = self._project_domain_list(project_data['id'])
        domains = [(i["name"], str(i["port"])) for i in domain_list]
        ssl, f_ssl = self._get_ssl_status(project_data['name'])
        error_msg = self.create_config(project_data, domains, ssl, f_ssl)
        if not error_msg:
            public.serviceReload()
            pdata = {
                'project_config': json.dumps(project_data['project_config'])
            }
            public.M("sites").where("id=?", (project_data['id'],)).update(pdata)
            return json_response(status = True, msg = "修改成功")
        
        return json_response(status = False, msg = error_msg)
    
    def remove_server_proxy(self, get):
        try:
            site_name = get.site_name.strip()
            proxy_id = get.proxy_id.strip()
        except:
            return json_response(status = False, msg = "参数错误")
        project_data = self.get_project_find(site_name)
        if not project_data:
            return json_response(False, "未找到项目")
        
        rp = RealServerProxy(project_data)
        msg = rp.remove_proxy(site_name, proxy_id)
        if msg:
            return json_response(status = False, msg = msg)
        return json_response(status = True, msg = "删除成功")
    
    def server_proxy_list(self, get):
        try:
            site_name = get.site_name.strip()
        except:
            return json_response(status = False, msg = "参数错误")
        
        project_data = self.get_project_find(site_name)
        if not project_data:
            return json_response(False, "未找到项目")
        
        _p = RealServerProxy(project_data)
        data = _p.get_proxy_list()
        return json_response(status = True, data = data)
    
    @staticmethod
    def check_env_for_project(get):
        project_cmd = ""
        by_process = 0
        env_list = []
        env_file = ''
        try:
            if hasattr(get, "project_cmd") and get.project_cmd:
                project_cmd = get.project_cmd.strip()
            project_jar = get.project_jar.strip()
            if hasattr(get, "by_process") and get.by_process:
                by_process = int(get.by_process)
            if hasattr(get, "env_list") and get.env_list:
                env_list = get.env_list
            if hasattr(get, "env_file") and get.env_file:
                env_file = get.env_file
        except:
            return json_response(status = False, msg = "env参数错误")
        if not os.path.exists(project_jar):
            return json_response(status = False, msg = "jar文件不存在")
        if env_file and not os.path.exists(env_file):
            return json_response(status = False, msg = "环境变量文件不存在")
        try:
            spring_parser = SpringConfigParser(
                jar_path = project_jar,
                process = by_process,
                cmd = project_cmd,
                env_list = env_list,
                env_file = env_file,
            )
            data = spring_parser.get_tip()
        except:
            data = []
        if not data:
            return json_response(status = True, msg = "未检测到配置问题", data = data)
        
        return json_response(status = True, data = data)
    
    def set_static_path(self, get):
        try:
            project_name = get.project_name.strip()
            project_data = self.get_project_find(project_name)
            status = utils.js_value_to_bool(get.status)
            index = get.index.strip()
            path = get.path.strip()
        except:
            return json_response(status = False, msg = "参数错误")
        
        if not project_data:
            return json_response(False, "未找到项目")
        
        if not project_data["project_config"]["java_type"] == "springboot":
            return json_response(status = False, msg = "非springboot项目无法设置静态文件")
        
        proxy_info = project_data['project_config'].get("proxy_info", [])
        for i in proxy_info:
            if i["proxy_dir"] == "/":
                return json_response(status = False, msg = "项目已存在根路由【/】配置，无法设置态文件配置")
        
        project_data["project_config"]["static_info"] = {
            "status": status,
            "index": index,
            "path": path,
            "use_try_file": True,
        }
        
        res = self._set_static_path(project_data)
        if isinstance(res, str):
            return json_response(status = False, msg = res)
        
        public.M("sites").where("id=?", (project_data["id"],)).update(
            {
                "project_config": json.dumps(project_data["project_config"])
            }
        )
        
        return json_response(status = True, msg = "设置成功")
    
    def get_keep_status(self, get):
        try:
            project_name = get.project_name.strip()
            project_data = self.get_project_find(project_name)
        except:
            return json_response(status = False, msg = "参数错误")
        from mod.project.java.project_update import ProjectUpdate
        
        if not project_data:
            return json_response(False, "未找到项目")
        
        if not project_data["project_config"]["java_type"] == "springboot":
            return json_response(status = False, msg = "非springboot项目不支持该功能")
        
        p = ProjectUpdate(project_name, project_data["project_config"]["project_jar"])
        res = p.get_keep_status()
        return res
    
    def update_project_by_restart(self, get):
        try:
            project_name = get.project_name.strip()
            project_jar = get.project_jar.strip()
            project_data = self.get_project_find(project_name)
        except:
            return json_response(status = False, msg = "参数错误")
        
        if not project_data:
            return json_response(False, "未找到项目")
        
        if not project_data["project_config"]["java_type"] == "springboot":
            return json_response(status = False, msg = "非springboot项目不支持该功能")
        
        from mod.project.java.project_update import ProjectUpdate
        
        p = ProjectUpdate(project_name, new_jar = project_jar)
        res = p.restart_update()
        return res
    
    def update_project_by_keep(self, get):
        now_port = 0
        run_time = 0
        try:
            project_name = get.project_name.strip()
            project_jar = get.project_jar.strip()
            if hasattr(get, "now_port") and get.now_port:
                now_port = int(get.now_port)
            if hasattr(get, "run_time") and get.run_time:
                run_time = int(get.run_time)
            project_data = self.get_project_find(project_name)
        except:
            return json_response(status = False, msg = "参数错误")
        
        if not project_data:
            return json_response(False, "未找到项目")
        
        if not project_data["project_config"]["java_type"] == "springboot":
            return json_response(status = False, msg = "非springboot项目不支持该功能")
        
        if not os.path.isfile(project_jar):
            return json_response(status = False, msg = "jar文件不存在")
        
        if public.get_webserver() != "nginx":
            return json_response(status = False, msg = "当前只支持nginx使用")
        
        ng_file = "/www/server/panel/vhost/nginx/java_{}.conf".format(project_name)
        if not os.path.exists(ng_file):
            return json_response(status = False, msg = "未启用外网访问的不能进行不停机更新")
        
        panel_path = "/www/server/panel"
        pid_file = "{}/keep/{}.pid".format(self._java_project_path, project_name)
        public.ExecShell(
            "nohup {}/pyenv/bin/python3 {}/mod/project/java/project_update.py {} {} {} {} &> /dev/null & \n"
            "echo $! > {} ".format(
                panel_path, panel_path, project_name, project_jar, now_port, run_time, pid_file
            )
        )
        return json_response(status = True, msg = "更新任务已开始")
    
    def force_stop(self, get):
        try:
            project_name = get.project_name.strip()
            project_data = self.get_project_find(project_name)
        except:
            return json_response(status = False, msg = "参数错误")
        
        if not project_data:
            return json_response(False, "未找到项目")
        
        project_config = project_data["project_config"]
        pid_file = "{}/keep/{}.pid".format(self._java_project_path, project_name)
        pid_data = public.readFile(pid_file)
        if isinstance(pid_data, str) and pid_data != "0":
            try:
                p = psutil.Process(int(pid_data))
                p.kill()
            except:
                pass
        
        service_list = []
        rep_service = re.compile(r"^spring_%s_\S{8}$" % public.prevent_re_key(project_name), re.M)
        for i in os.scandir("/usr/lib/systemd/system"):
            if i.is_file() and rep_service.match(i.name):
                service_list.append(i.name)
        
        now_name = self._get_systemd_server_name(project_config)
        if now_name in service_list:
            service_list.remove(now_name)
        
        for i in service_list:
            public.ExecShell("systemctl stop {}".format(i))
            os.remove("/usr/lib/systemd/system/{}".format(i))
        
        public.ExecShell("systemctl daemon-reload")
        upstream_file = "/www/server/panel/vhost/nginx/java_{}_upstream.conf".format(project_name)
        if os.path.isfile(upstream_file):  # 说明新旧同时存在 则删除旧的
            upstream_data = public.readFile(upstream_file)
            if isinstance(upstream_data, str):
                old_upstream_data = re.search(r"server 127\.0\.0\.1:(?P<port>\d+);", upstream_data)
                if old_upstream_data:
                    old_port = old_upstream_data.group("port")
                    ng_file = "/www/server/panel/vhost/nginx/java_{}.conf".format(project_name)
                    ng_data = public.readFile(ng_file)
                    if not isinstance(ng_data, str):
                        return "Nginx配置文件读取错误，无法取消轮询，使用新实例"
                    new_config = ng_data.replace("{}_backend".format(project_name), "127.0.0.1:{}".format(old_port))
                    
                    public.writeFile(ng_file, new_config)
                    res = public.checkWebConfig()
                    if res is not True:
                        public.writeFile(ng_file, ng_data)
                    else:
                        os.remove(upstream_file)
                        public.serviceReload()
        
        return json_response(status = True, msg = "强制停止成功")
    
    def keep_option(self, get):
        try:
            project_name = get.project_name.strip()
            option = get.option.strip()
            project_data = self.get_project_find(project_name)
        except:
            return json_response(status = False, msg = "参数错误")
        
        if not project_data:
            return json_response(False, "未找到项目")
        
        if option not in ("use_new", "use_old", "stop_new"):
            return json_response(status = False, msg = "参数错误")
        
        if not project_data["project_config"]["java_type"] == "springboot":
            return json_response(status = False, msg = "非springboot项目不支持该功能")
        
        from mod.project.java.project_update import ProjectUpdate
        
        p = ProjectUpdate(project_name, project_data["project_config"]["project_jar"])
        res = p.keep_option(option)
        return res
    
    def get_spring_log_list(self, get):
        try:
            project_name = get.project_name.strip()
            project_data = self.get_project_find(project_name)
        except:
            return json_response(status = False, msg = "参数错误")
        
        if not project_data:
            return json_response(False, "未找到项目")
        
        if not project_data["project_config"]["java_type"] == "springboot":
            return json_response(status = False, msg = "非springboot项目不支持该功能")
        
        pid = self.get_project_pid(project_data)
        project_config = project_data["project_config"]
        project_jar = project_config["project_jar"]
        project_cmd = project_config["project_cmd"]
        env_list = project_config["env_list"]
        env_file = project_config["env_file"]
        
        spring_log_parser = SpringLogConfigParser(
            jar_path = project_jar,
            process = pid,
            cmd = project_cmd,
            env_list = env_list,
            env_file = env_file,
        )
        try:
            res = []
            for i in spring_log_parser.get_all_log_ptah():
                for j in os.scandir(i):
                    if j.is_file() and j.name.endswith(".log"):
                        log_path = os.path.join(i, j.name)
                        res.append(log_path)
        except:
            pass
        
        return json_response(status = True, data = res)
    
    @staticmethod
    def get_spring_log_data(get):
        try:
            log_file = get.log_file.strip()
        except:
            return json_response(status = False, msg = "参数错误")
        
        if not os.path.isfile(log_file):
            return json_response(status = False, msg = "日志文件不存在")
        
        return json_response(status = True, data = public.GetNumLines(log_file, 1000))
    
    @staticmethod
    def install_jdk_new(get):
        if not hasattr(get, 'version') or not get.version.strip():
            return json_response(False, '版本号不能为空')
        version = get.version.strip()
        if os.path.exists('/www/server/java/' + version):
            return json_response(False, '版本已经存在')
        jdk_manager = utils.JDKManager()
        if version not in jdk_manager.versions_list:
            return public.returnMsg(False, '版本号不存在')
        
        jdk_manager.async_install_jdk(version)
        
        return json_response(True, '已添加到安装任务，请在消息盒子中查看安装情况')
    
    @staticmethod
    def install_tomcat_new(get):
        java_path = None
        if not hasattr(get, 'version') or not get.version.strip():
            return json_response(False, '版本号不能为空')
        version = get.version.strip()
        if hasattr(get, 'java_path') and get.java_path.strip():
            java_path = get.java_path.strip()
        
        if version not in ("7", "8", "9", "10"):
            return public.returnMsg(False, '版本选择错误，仅支持7, 8, 9, 10版本')
        
        res = utils.TomCat.async_install_tomcat_new(version, java_path)
        if res is not None:
            return json_response(False, res)
        
        return json_response(True, '已添加到安装任务，请在消息盒子中查看安装情况')
    
    def install_tomcat(self, get: Get) -> Dict:
        infos = self.get_tomcat_list()
        path = None
        
        # *参数校验
        install_type = get.get("install_type", "")
        if install_type not in ("global", "custom"):
            return json_response(False, "错误的安装类型")
        
        base_version = get.get("base_version", "")
        if base_version not in BASE_VERSIONS.keys():
            return json_response(False, "不支持的安装版本")
        
        installed_version = infos.keys()
        name = get.get("name", "")
        if name in installed_version:
            return json_response(False, "指定版本名称已存在")
        
        port = get.get("port", "")
        if not port and install_type == "global":
            port = BASE_VERSIONS[base_version][1]
        elif not utils.check_port(port):
            return json_response(False, "指定端口不合法或已被使用")
        
        jdk_path = get.get("jdk_path", "")
        if not os.path.exists(jdk_path):
            return json_response(False, "指定JDK不存在")
        
        user = get.get("user", "")
        if not user:
            return json_response(False, "指定启动用户不合法")
        
        ps = get.get("ps", "")
        release_firewall = get.get("release_firewall", "")
        auto_start = bool(get.get("auto_start", ""))

        # *基准版本安装状态
        info = infos.get(base_version, {})
        if info and install_type == "global":
            return json_response(True, "{}全局版本已安装".format(base_version))

        install_manage_sh = utils.TomCat.build_make_sh(get)
        version = BASE_VERSIONS[base_version][0].split(".")[0]
        if not info:
            res = utils.TomCat.async_install_tomcat_new(version, jdk_path, install_manage_sh)
            if res is not None:
                return json_response(False, res)
            return json_response(True, "已添加到安装任务，请在消息盒子中查看安装情况")
        else:
            res = public.ExecShell(install_manage_sh)
            public.print_log(res)
            target_path = INDEP_PROJECT_TOMCAT_PATH + "/" + name
            if os.path.exists(target_path):
                return json_response(True, "安装完成")
            return json_response(False, "安装失败")


        # *基准版本安装状态
        info = infos.get(base_version, {})
        base_path = ""
        if info:
            base_path = infos[base_version].get("path", "")
        else:
            version = BASE_VERSIONS[base_version][0].split(".")[0]
            install_msg = utils.TomCat.async_install_tomcat_new(version, jdk_path)
            if install_msg:
                return json_response(False, install_msg)
            # 刷新以开始任务
            from files import files
            files().GetTaskSpeed(Get())
            # !阻塞安装
            count = 0
            flag = False
            while count < 60:
                if os.path.exists(GLOBAL_TOMCAT_PATH + "/" + base_version):
                    info = self.get_tomcat_list().get(base_version, "")
                    base_path = info.get("path", "")
                    # 等待安装配置完成
                    time.sleep(6)
                    flag = True
                    break
                time.sleep(1)
                count += 1
            if not flag:
                return json_response(False, "安装超时")
        
        # *自定义安装
        if install_type == "global":
            # 指定版本已安装
            public.print_log("指定版本已安装")
            path = base_path
        else:
            bak_dir_name = base_version.replace("tomcat", "tomcat_bak")
            bak_path = "{tomcat_dir_path}/{bak_dir_name}/".format(
                tomcat_dir_path = os.path.dirname(base_path),
                bak_dir_name = bak_dir_name
            )
            # *复制到自定义安装文件夹
            target_path = f"{INDEP_PROJECT_TOMCAT_PATH}/{name}"
            if not os.path.exists(bak_path):
                return json_response(False, "目录不存在")
            import shutil
            
            try:
                if os.path.exists(target_path):
                    shutil.rmtree(target_path)
                shutil.copytree(bak_path, target_path)
            except Exception as e:
                public.print_log(e)
                return json_response(False, "自定义安装失败")
            else:
                path = target_path
        
        tomcat_obj = utils.TomCat(path)
        
        # *指定JDK
        res = tomcat_obj.replace_jdk(jdk_path)
        if res is not None:
            return json_response(False, res)
        
        # *备注文件
        ps_file = PS_FILE_TMPL.format(tomcat_path = path)
        if not os.path.exists(ps_file) or ps:
            with open(ps_file, "w") as f:
                f.write(ps)

        # *指定端口
        if port:
            if not tomcat_obj.set_port(int(port)):
                return json_response(False, "设置指定端口失败")

            # *放行端口
            if release_firewall:
                from firewallModel.comModel import main

                f_get = public.dict_obj()
                f_get.protocol = "tcp"
                f_get.port = get.port
                f_get.choose = "all"
                f_get.types = "accept"
                f_get.brief = ""
                f_get.domain = ""
                f_get.chain = "INPUT"
                f_get.operation = "add"
                f_get.strategy = "accept"
                main().set_port_rule(f_get)
        
        # *指定启动用户
        if user:
            res = tomcat_obj.change_default_user(user)
            if not res:
                return json_response(False, "设置指定启动用户失败")
        
        # *指定开机自启
        if auto_start != "":
            tomcat_obj.set_service(auto_start = auto_start)
        
        if not tomcat_obj.save_config_xml():
            return json_response(False, "保存设置失败")
        
        tomcat_obj.restart()
        return json_response(True, "安装完成")
    
    def uninstall_tomcat(self, get: Get):
        tomcat_name = get.get("tomcat_name", "")
        infos = self.get_tomcat_list()
        if tomcat_name not in infos.keys():
            return "指定tomcat名称不存在"
        path = infos.get(tomcat_name, "").get("path", "")
        tomcat_obj = utils.TomCat(path)
        
        # *停止tomcat
        if not tomcat_obj.stop():
            return json_response(False, "停止tomcat失败")
        
        # *移除服务
        tomcat_obj.remove_service()
        
        # *删除文件
        try:
            shutil.rmtree(path)
        except:
            return json_response(False, "卸载tomcat失败")
        else:
            res = not os.path.exists(path)
            msg = "卸载tomcat成功" if res else "卸载tomcat失败"
            return json_response(res, msg)
    
    # def get_tomcat_config_path(self, get: Get) -> str:
    #     tomcat_name = get.tomcat_name
    #     infos = self.get_tomcat_list()
    #     info = infos.get(tomcat_name, "")
    #     config_path = ""
    #     if info:
    #         path = info.get("path", "")
    #         config_path = CONFIG_PATH_TMPL.format(tomcat_path = path)
    #         if not os.path.exists(config_path):
    #             config_path = ""
    #     return config_path
    
    def start_tomcat(self, get: Get) -> Dict:
        tomcat_name = get.get("tomcat_name", "")
        stype = get.get("type", "")
        if not all((tomcat_name, stype)):
            return json_response(False, "参数错误")
        infos = self.get_tomcat_list()
        if tomcat_name not in infos.keys():
            return json_response(False, "指定tomcat名称不存在")
        info = infos.get(tomcat_name, {})
        path = infos.get(tomcat_name, "").get("path", "")
        tomcat_obj = utils.TomCat(path)
        if stype == "start":
            res = tomcat_obj.start(by_user = info["user"])
            msg = "启动成功" if res else "启动失败"
            return json_response(res, msg)
        elif stype == "stop":
            res = tomcat_obj.stop()
            msg = "停止成功" if res else "停止失败"
            return json_response(res, msg)
        else:
            res = tomcat_obj.restart(by_user = info["user"])
            msg = "重启成功" if res else "重启失败"
            return json_response(res, msg)
    
    def modify_tomcat(self, get: Get) -> Dict:
        tomcat_name = get.get("tomcat_name", "")
        port = get.get("port", "")
        user = get.get("user", "")
        auto_start = get.get("auto_restart", "")
        jdk_path = get.get("jdk_path", "")
        ps = get.get("ps", "")
        log_path = get.get("log_path", "")
        
        infos = self.get_tomcat_list()
        info = infos.get(tomcat_name, "")
        if not info:
            return json_response(False, "项目不存在")
        
        tomcat_path = info["path"]
        install_type = info["type"]
        
        tomcat_obj = utils.TomCat(tomcat_path = tomcat_path)
        if port:
            if not tomcat_obj.set_port(int(port)):
                return json_response(False, "设置指定端口失败")
        if user:
            res = tomcat_obj.change_default_user(user)
            if not res:
                return json_response(res, "设置启动用户失败")

        if jdk_path:
            res = tomcat_obj.replace_jdk(jdk_path)
            if res is not None:
                return json_response(False, res)
        
        if ps:
            ps_path = PS_FILE_TMPL.format(tomcat_path = tomcat_obj.path)
            try:
                with open(ps_path, "w") as f:
                    f.write(ps)
            except Exception as e:
                public.print_log(e)
                return json_response(False, str(e))
        
        if log_path:
            if not os.path.exists(log_path) and os.path.isdir(log_path):
                return json_response(False, f"无效的日志目录地址: {log_path}")
            prefix = f"-{tomcat_name}" if install_type == "indep" else ""
            if not tomcat_obj.change_log_path(log_path = log_path, prefix = prefix):
                return json_response(False, "更改日志目录失败")

        if auto_start != "":
            tomcat_obj.set_service(auto_start=auto_start == "true")

        if not tomcat_obj.save_config_xml():
            return json_response(False, "保存设置失败")
        
        return json_response(True, "设置Tomcat完成")
    
    @classmethod
    def get_tomcat_list(cls, get=None):
        jdk_list = cls._local_jdk_info()

        def _get_tomcat_version_cmd(tomcat_path: str) -> str:
            java_bin = ""
            for jdk_info in jdk_list:
                if jdk_info["operation"] in (1, 2):
                    java_bin = jdk_info["path"]
            if not java_bin:
                return ""
            out, _ =public.ExecShell(
                "{} -cp {}/lib/catalina.jar org.apache.catalina.util.ServerInfo".format(java_bin, tomcat_path)
            )
            regexp = re.compile(r"Server\s+number:\s+(?P<version>[.\d]+\s+)")
            match = regexp.search(out)
            if match:
                return match.group("version").strip()
            return ""

        def _get_tomcat_version_logs(tomcat_path: str):
            logs = [os.path.join(tomcat_path, "logs", i) for i in os.listdir(os.path.join(tomcat_path, "logs"))
                     if (i.endswith(".log") or i.endswith(".out")) and i.startswith("catalina")]
            version = ""
            if len(logs) == 0:
                return ""
            regexp = re.compile(r":\s+Apache\s+Tomcat/(?P<version>[.\d]+\s+)")
            try:
                for log in logs:
                    n = 0
                    with open(log, "r") as f:
                        for line in f.readlines():
                            n += 1
                            match = regexp.search(line)
                            if match:
                                version = match.group("version").strip()
                            if n > 1000:
                                break
            except:
                pass
            return version
        
        def _get_tomcat_version(tomcat_path: str) -> str:
            version_file_path_temp = "{tomcat_path}/version.pl"
            version = ""
            version_file_path = version_file_path_temp.format(tomcat_path = tomcat_path)
            
            if os.path.exists(version_file_path):
                with open(version_file_path, "r") as f:
                    version = f.read().strip()
            else:
                version = _get_tomcat_version_cmd(tomcat_path)
                if not version:
                    version = _get_tomcat_version_logs(tomcat_path)
                if version:
                    public.writeFile(version_file_path, version)

            return version
        
        def _get_jdk_version(jdk_path) -> str:
            jdk_version = ""
            jdk_release = "{jdk_path}/release".format(jdk_path = jdk_path)
            if os.path.exists(jdk_release):
                with open(jdk_release, "r") as f:
                    for line in f.readlines():
                        if "JAVA_VERSION=" in line:
                            jdk_version = line.split("=")[-1].replace("\"", "").strip()
            return jdk_version
        
        def _get_tomcat_ps(tomcat_path: str) -> str:
            ps = ""
            ps_file = PS_FILE_TMPL.format(tomcat_path = tomcat_path)
            if os.path.exists(ps_file):
                with open(ps_file, "r") as f:
                    ps = f.read()
            return ps
        
        def _get_tomcat_info(tomcat_path: str) -> Dict:
            types = {GLOBAL_TOMCAT_PATH: "global", INDEP_PROJECT_TOMCAT_PATH: "indep"}
            tomcat_obj = utils.TomCat(tomcat_path = tomcat_path)
            info = tomcat_obj.status()
            info["ps"] = _get_tomcat_ps(tomcat_path = tomcat_path)
            info["type"] = types[os.path.dirname(tomcat_path)]
            info["version"] = _get_tomcat_version(tomcat_path = tomcat_path)
            info["config_path"] = CONFIG_PATH_TMPL.format(tomcat_path = tomcat_path)
            info["jdk_version"] = _get_jdk_version(info["jdk_path"])
            try:
                info["jdk_support"] = JDK_SUPPORT.get(int(info["version"].split(".")[0]), "")
            except:
                info["jdk_support"] = "--"
            info["auto_start"] = tomcat_obj.service_exists
            info["user"] = tomcat_obj.user
            info["log_file"] = tomcat_obj.log_file
            return info
        
        tomcat_info_dict = {}
        from itertools import chain
        
        for item in chain(
                os.scandir(GLOBAL_TOMCAT_PATH), os.scandir(INDEP_PROJECT_TOMCAT_PATH)
        ):
            if item.is_dir() and "_bak" not in item.name:
                tomcat_info_dict[item.name] = _get_tomcat_info(tomcat_path = item.path)
        
        return tomcat_info_dict
    
    # def get_tomcat_info(self, get: Get) -> Dict:
    #     tomcat_name = get.get("tomcat_name", "")
    #     if not tomcat_name:
    #         public.print_log("指定tomcat名称不正确")
    #         return {}
    #     infos = self.get_tomcat_list()
    #     return infos.get(tomcat_name, {})
    
    @staticmethod
    def get_jar_port(get: Get) -> Dict:
        port = ""
        jar_path = get.get("jar_path", "")
        if not os.path.exists(jar_path):
            return json_response(status = False, data = {"port": port}, msg = "jar路径不存在，获取端口失败")
        try:
            scp = SpringConfigParser(jar_path=jar_path)
            res, _ = scp.app_config()
            port = res[0][1]["server"]["port"]
        except:
            json_response(status = False, data = {"port": port}, msg = "jar包未能正确解析，获取端口失败")
        return json_response(status = True, data = {"port": port}, msg = "获取端口成功")

    def get_project_status(self, project_id):
        # 仅使用在项目停止告警中
        project_info = public.M('sites').where('project_type=? AND id=?', ('Java', project_id)).find()
        if not project_info:
            return None, ""

        project_info["project_config"] = json.loads(project_info["project_config"])
        pid = self.get_project_pid(project_info)
        if project_info['project_config']['java_type'] == 'springboot':
            if utils.is_stop_by_user(project_id):
                return True, project_info["name"]
            return True if isinstance(pid, int) else False, project_info["name"]

        if project_info['project_config']['java_type'] == 'duli':
            if utils.is_stop_by_user(project_id):
                return True, project_info["name"]
            return True if isinstance(pid, int) else False, project_info["name"]

        if project_info['project_config']['java_type'] == 'neizhi':
            if utils.is_stop_by_user(project_id):
                return True, project_info["name"]

            return True if isinstance(pid, int) else False, project_info["name"]