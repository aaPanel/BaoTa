import json
import os.path
import re
import sys
import time
import psutil
from uuid import uuid4
from typing import Optional, Union, List, Dict, Tuple, Any, Set

SERVICE_PATH = "/www/server/python_project/service"
if not os.path.isdir(SERVICE_PATH):
    try:
        os.makedirs(SERVICE_PATH, 0o755)
    except:
        pass

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

import public
from mod.base import json_response
from mod.project.python.pyenv_tool import PythonEnvironment, EnvironmentManager


class Environment(object):

    def __init__(self, project_name: str, python_path: str,python_bin:str, project_path: str, user: str,
                 env_list: List[Dict[str, str]], env_file: str):
        self.python_path = python_path
        self.project_path = project_path
        self.env_list = env_list
        self.env_file = env_file
        self.project_name = project_name
        self.user = user
        self._env_cache: Optional[str] = None
        self.pyenv = EnvironmentManager().get_env_py_path(python_bin)

    @classmethod
    def form_project_conf(cls, project_config: dict) -> Union["Environment", str]:
        if not isinstance(project_config, dict):
            return '项目配置文件格式错误'

        python_path: str = project_config.get("vpath")
        python_bin: str = project_config.get("python_bin", project_config.get("vpath"))
        project_path: str = project_config.get("path")
        env_list = project_config.get("env_list", [])
        env_file = project_config.get("env_file", "")
        project_name = project_config.get("pjname")
        user = project_config.get("user", "root")
        if not python_path or not project_path or not project_name:
            return '项目配置文件格式错误'

        if not os.path.isdir(python_path) or not os.path.isdir(project_path):
            return '项目配置中指定的项目目录或虚拟环境目录不存在'

        python_path = python_path.rstrip("/")
        project_path = project_path.rstrip("/")
        if not python_path.endswith("/bin"):
            python_path = python_path + "/bin"
            if not os.path.isdir(python_path):
                return '项目配置中指定的虚拟环境目录不存在'

        return cls(project_name, python_path, python_bin, project_path, user, env_list, env_file)

    # 组合环境变量，用于启动服务
    def shell_env(self) -> str:
        if self._env_cache is not None:
            return self._env_cache

        # cd 到指定路径， 加载环境变量， 加载环境变量文件， 设置Python环境到首位
        res_env_list = ["cd {}".format(self.project_path)]
        if isinstance(self.env_list, list):
            for i in self.env_list:
                if not isinstance(i, dict):
                    continue
                if 'k' in i and 'v' in i:
                    res_env_list.append("export {}={}".format(i['k'], i['v']))

        if self.env_file and os.path.isfile(self.env_file):
            res_env_list.append("source {}".format(self.env_file))

        res_env_list.append(self.pyenv.activate_shell())

        self._env_cache = "\n".join(res_env_list)

        return self._env_cache


class PythonService(object):

    def __init__(self, sid: str, name: str, command: str, level: Optional[int], log_type: Optional[str]):
        self.sid = sid
        self.name = name
        self.command = command
        self.level = level
        self.log_type = log_type
        self.env: Optional[Environment] = None

    def set_env(self, env: Environment):
        self.env = env

    def write_pid(self, pid: int):
        if not self.env:
            raise RuntimeError('未设置环境')
        pid_file = os.path.join(SERVICE_PATH, '{}/{}.pid'.format(self.env.project_name, self.name))
        if not os.path.isdir(os.path.dirname(pid_file)):
            os.makedirs(os.path.dirname(pid_file), 0o755)
        public.writeFile(pid_file, str(pid))

    def read_pid(self) -> Optional[int]:
        if not self.env:
            raise RuntimeError('未设置环境')
        pid_file = os.path.join(SERVICE_PATH, '{}/{}.pid'.format(self.env.project_name, self.name))
        if not os.path.isfile(pid_file):
            return None

        res = None
        try:
            res = int(public.readFile(pid_file))
        except:
            pass
        if isinstance(res, int) and res > 0:
            return res
        return None

    @classmethod
    def from_config(cls, config: dict,
                    env: Optional[Environment]) -> Union['PythonService', "MainPythonService", 'CeleryService', str]:
        sid = config.get('sid', None)
        if sid == 'main':
            return MainPythonService(env)

        name: str = config.get('name', "")
        command: str = config.get('command', "")
        if not sid or not name or not command:
            return '缺少必要参数'

        if not isinstance(command, str) or not isinstance(name, str) or not isinstance(sid, str):
            return '参数类型错误'

        level = config.get('level', 11)
        log_type = config.get('log_type', "append")

        if command.split()[0].endswith("celery"):
            res = CeleryService(sid, name, command, level, log_type)
        else:
            res = cls(sid, name, command, level, log_type)

        if env:
            res.set_env(env)
        return res

    # 执行启动服务并返回PID信息或错误信息
    def start(self) -> Optional[int]:
        if not self.env:
            raise RuntimeError('未设置环境')
        log_file = os.path.join(SERVICE_PATH, '{}/{}.log'.format(self.env.project_name, self.name))
        pid_file = os.path.join(SERVICE_PATH, '{}/{}.pid'.format(self.env.project_name, self.name))
        if not os.path.exists(os.path.dirname(pid_file)):
            os.makedirs(os.path.dirname(pid_file), 0o755)
        if os.path.exists(pid_file):
            os.remove(pid_file)
        prep_sh = self.env.shell_env()
        prep_sh += "\nexport BT_PYTHON_SERVICE_SID={}".format(self.sid)
        if not os.path.isfile(log_file):
            public.writeFile(log_file, '')
        public.set_own(log_file, self.env.user)
        public.set_mode(log_file, "755")
        if self.log_type == "append":
            prep_sh += "\nnohup {} &>> {} &".format(self.command, log_file)
        else:
            prep_sh += "\nnohup {} &> {} &".format(self.command, log_file)

        public.print_log(prep_sh)
        res = public.ExecShell(prep_sh, user=self.env.user)
        public.print_log(res)
        time.sleep(0.5)
        return self.get_service_pid()

    def get_service_pid(self, only_service: bool = False) -> Optional[int]:
        pid = self.read_pid()
        if pid and psutil.pid_exists(pid):
            return pid

        if not pid:
            pid = self.get_pid_by_env_key()
        if not pid and not only_service:
            pid = self.get_pid_by_command()

        if pid:
            self.write_pid(pid)
            return pid
        return None

    def get_pid_by_env_key(self) -> Optional[int]:
        env_key = "BT_PYTHON_SERVICE_SID={}".format(self.sid)
        target = []
        for p in psutil.pids():
            try:
                data: str = public.readFile("/proc/{}/environ".format(p))
                if data.rfind(env_key) != -1:
                    target.append(p)
            except:
                continue

        for i in target:
            try:
                p = psutil.Process(i)
                if p.ppid() not in target:
                    return i
            except:
                continue
        return None

    def get_pid_by_command(self) -> Optional[int]:
        cmd_list = self.split_command()
        target = []
        for p in psutil.process_iter(["cmdline", "pid", "exe"]):
            try:
                real_cmd = p.cmdline()
                if cmd_list == real_cmd:
                    target.append(p)
                if real_cmd[2:] == cmd_list[1:] and real_cmd[0].startswith(self.env.python_path):
                    target.append(p)
            except:
                continue

        for p in target:
            try:
                if p.ppid() not in target:
                    return p.pid
            except:
                continue
        return None

    def split_command(self) -> List[str]:
        res = []
        tmp = ""
        in_quot = False
        for i in self.command:
            if i in (' ', '\t', '\r'):
                if tmp and not in_quot:
                    res.append(tmp)
                    tmp = ""
                if in_quot:
                    tmp += ' '

            elif i in ("'", '"'):
                if in_quot:
                    in_quot = False
                else:
                    in_quot = True
            else:
                tmp += i

        if tmp:
            res.append(tmp)

        return res

    def stop(self) -> None:
        pid = self.get_service_pid()
        if not pid:
            return
        try:
            p = psutil.Process(pid)
            p.kill()
        except:
            pass

    def get_log(self) -> str:
        if not self.env:
            raise RuntimeError('未设置环境')
        log_file = os.path.join(SERVICE_PATH, '{}/{}.log'.format(self.env.project_name, self.name))
        if not os.path.isfile(log_file):
            return '暂无日志'
        data = public.GetNumLines(log_file, 1000)
        if not data:
            return '暂无日志'
        return data

    @staticmethod
    def _get_ports_by_pid(pid: int) -> List[int]:
        try:
            res = set()
            for con in psutil.Process(pid).connections():
                if con.status == 'LISTEN':
                    res.add(con.laddr.port)
            return list(res)
        except:
            return []

    def get_info(self) -> Dict[str, Any]:
        if not self.env:
            raise RuntimeError('未设置环境')
        pid = self.get_service_pid()
        public.print_log(pid)
        public.print_log(self.name)
        public.print_log(self.__class__.__name__)
        if isinstance(pid, int) and psutil.pid_exists(pid):
            ports = self._get_ports_by_pid(pid)
            return {
                'pid': pid,
                'ports': ports
            }
        return {"pid": None, "ports": []}


class MainPythonService(PythonService):
    from projectModel.pythonModel import main as py_project_main
    _py_main_class = py_project_main

    def __init__(self, env: Environment):
        super().__init__('main', 'main', 'main', 10, 'append')
        self.set_env(env)

    @property
    def py_main(self):
        return self._py_main_class()

    def start(self) -> Optional[int]:
        if not self.env:
            raise RuntimeError('未设置环境')
        self.py_main.only_start_main_project(self.env.project_name)
        return self.get_service_pid()

    def get_service_pid(self, only_service: bool = False) -> Optional[int]:
        if not self.env:
            raise RuntimeError('未设置环境')
        pids: List[int] = self.py_main.get_project_run_state(self.env.project_name)
        if not pids:
            return None
        pids.sort()
        return pids[0]

    def stop(self) -> None:
        if not self.env:
            raise RuntimeError('未设置环境')
        self.py_main.only_stop_main_project(self.env.project_name)

    def get_log(self) -> str:
        if not self.env:
            raise RuntimeError('未设置环境')
        get_obj = public.dict_obj()
        get_obj.name = self.env.project_name
        res = self.py_main.GetProjectLog(get_obj)
        data = None
        if res['status']:
            data = res['data']

        if not data:
            return '暂无日志'
        return data

    def get_info(self):
        res = super().get_info()
        res['name'] = "项目主服务"
        return res


class CeleryService(PythonService):

    def get_celery_env(self) -> Tuple[str, str]:
        celery = "{}/celery".format(self.env.python_path)
        if not os.path.isfile(celery):
            return '', ''
        celery_data = public.readFile(celery)
        if not isinstance(celery_data, str):
            return '', ''
        celery_python = celery_data.split("\n", 1)[0]
        if celery_python.startswith("#!"):
            celery_python = celery_python[2:].strip()
        return celery_python, celery

    def get_pid_by_command(self) -> Optional[int]:
        celery_env = self.get_celery_env()
        if not celery_env[0] or not celery_env[1]:
            return super().get_pid_by_command()
        target = []
        cmd_list = list(celery_env) + self.split_command()[1:]
        for p in psutil.process_iter(["cmdline", "pid"]):
            try:
                if cmd_list == p.cmdline():
                    target.append(p)
            except:
                continue

        for p in target:
            try:
                if p.ppid() not in target:
                    return p.pid
            except:
                continue
        return None


class ServiceManager:
    MAIN_SERVICE_CONF = {
        "sid": "main",
        "name": "main",
        "command": "main",
        "level": 10,
        "log_type": "append",
    }

    def __init__(self, project_name: str, project_config: dict):
        self.project_name = project_name
        self.project_config = project_config
        self._other_services: Optional[List[Dict]] = None
        self._env: Optional[Environment] = None

    @classmethod
    def new_mgr(cls, project_name: str) -> Union["ServiceManager", str]:
        data = public.M("sites").where(
            'project_type=? AND name=? ', ('Python', project_name)
        ).field('id,project_config').find()
        if not data:
            return "未查询到网站信息"
        project_config = json.loads(data['project_config'])
        return cls(project_name, project_config)

    @property
    def service_list(self) -> List[Dict]:
        res = [self.MAIN_SERVICE_CONF]
        res.extend(self.other_services)
        res.sort(key=lambda x: x['level'])
        return res

    @property
    def other_services(self) -> List[Dict]:
        if self._other_services is None:
            services = []
            for service in self.project_config.get('services', []):
                if service.get('sid') == 'main':
                    continue
                services.append(service)
            self._other_services = services
        return self._other_services

    @staticmethod
    def new_id() -> str:
        return uuid4().hex[::3]

    def save_service_conf(self) -> Optional[str]:
        data = public.M("sites").where(
            'project_type=? AND name=? ', ('Python', self.project_name)
        ).field('id,project_config').find()
        if not data:
            return "未查询到网站信息"
        data['project_config'] = json.loads(data['project_config'])
        data['project_config']['services'] = self.other_services
        public.M("sites").where('id=?', (data['id'],)).update({'project_config': json.dumps(data['project_config'])})

    def add_service(self, service_conf: dict) -> Optional[str]:
        try:
            conf = {
                "name": service_conf.get("name", "").strip(),
                "command": service_conf.get("command", "").strip(),
                "level": int(service_conf.get("level", 11)),
                "log_type": service_conf.get("log_type", "append"),
            }
        except:
            return "参数错误"

        if re.search(r"[\s$^`]+", conf['name']):
            return "服务名不能包含空格等特殊符号"

        for i in self.other_services:
            if i['name'] == conf['name']:
                return "服务名不能重复"
            if i['command'] == conf['command']:
                return "该启动命令已存在，服务名为：{}".format(i['name'])

        if not (conf['name'] and conf['command']):
            return "服务名称和启动命令不能为空"

        conf["sid"] = self.new_id()

        self.other_services.append(conf)
        self.save_service_conf()

    def modify_service(self, sid: str, service_conf: dict) -> Optional[str]:
        target_data = None
        for i in self.other_services:
            if i["sid"] == sid:
                target_data = i
                break
        if target_data is None:
            return "未找到该服务"

        name = target_data["name"]
        if "name" in service_conf and service_conf["name"] != target_data["name"]:
            name = service_conf["name"].strip()
            if re.search(r"[\s$^`]+", name):
                return "服务名不能包含空格等特殊符号"
        command = target_data["command"]
        if "command" in service_conf and service_conf["command"] != target_data["command"]:
            command = service_conf["command"].strip()

        for i in self.other_services:
            if i["sid"] == sid:
                continue
            if i["name"] == name:
                return "服务名不能重复"
            if i["command"] == command:
                return "该启动命令已存在，服务名为：{}".format(i["name"])

        if name != target_data["name"]:
            log_file = os.path.join(SERVICE_PATH, '{}/{}.log'.format(self.project_name, target_data["name"]))
            pid_file = os.path.join(SERVICE_PATH, '{}/{}.pid'.format(self.project_name, target_data["name"]))
            if os.path.exists(log_file):
                os.rename(log_file, os.path.join(SERVICE_PATH, '{}/{}.log'.format(self.project_name, name)))
            if os.path.exists(pid_file):
                os.rename(pid_file, os.path.join(SERVICE_PATH, '{}/{}.pid'.format(self.project_name, name)))

            target_data["name"] = name

        target_data["command"] = command
        target_data["level"] = int(service_conf.get("level", target_data["level"]))
        target_data["log_type"] = service_conf.get("log_type", target_data["log_type"])
        self.save_service_conf()

    def remove_service(self, sid: str) -> Optional[str]:
        del_idx = None
        for idx, i in enumerate(self.other_services):
            if i["sid"] == sid:
                del_idx = idx
                break

        if del_idx is None:
            return "未找到该服务"
        del_conf = self.other_services.pop(del_idx)
        self.save_service_conf()
        log_file = os.path.join(SERVICE_PATH, '{}/{}.log'.format(self.project_name, del_conf["name"]))
        pid_file = os.path.join(SERVICE_PATH, '{}/{}.pid'.format(self.project_name, del_conf["name"]))
        if os.path.exists(log_file):
            os.remove(log_file)
        if os.path.exists(pid_file):
            os.remove(pid_file)

    def _get_service_conf_by_sid(self, sid: str) -> Optional[Dict]:
        for i in self.service_list:
            if i["sid"] == sid:
                return i
        return None

    def _build_service_by_conf(self, conf: dict) -> Union[PythonService, str]:
        if not self._env:
            self._env = Environment.form_project_conf(self.project_config)
        if isinstance(self._env, str):
            return self._env
        return PythonService.from_config(conf, env=self._env)

    def handle_service(self, sid: str, action: str = "start") -> Optional[str]:
        public.print_log(action)
        conf = self._get_service_conf_by_sid(sid)
        if conf is None:
            return "未找到该服务"

        service = self._build_service_by_conf(conf)
        if isinstance(service, str):
            return service
        pid = service.get_service_pid()
        if not pid:
            pid = -1
        if action == "start":
            if not psutil.pid_exists(pid):
                service.start()
        elif action == "stop":
            service.stop()
        elif action == "restart":
            if psutil.pid_exists(pid):
                service.stop()
                for i in range(50):
                    if not psutil.pid_exists(pid):
                        break
                    time.sleep(0.1)
                else:
                    service.stop()
                    time.sleep(1)

            service.start()
        else:
            return "未知操作"

        return None

    def get_service_log(self, sid: str) -> Tuple[bool, str]:
        conf = self._get_service_conf_by_sid(sid)
        if conf is None:
            return False, "未找到该服务"
        service = self._build_service_by_conf(conf)
        if isinstance(service, str):
            return False, service
        return True, service.get_log()

    def get_services_info(self) -> List[dict]:
        res = []
        for i in self.service_list:
            service = self._build_service_by_conf(i)
            if isinstance(service, str):
                i["error"] = service
                res.append(i)
            else:
                i.update(service.get_info())
            res.append(i)

        return res

    def start_project(self):
        services = [self._build_service_by_conf(i) for i in self.service_list]
        for i in services:
            if isinstance(i, str):
                continue
            pid = i.get_service_pid()
            if isinstance(pid, int) and pid > 0 and psutil.pid_exists(pid):
                continue
            i.start()
            time.sleep(0.5)
        return "启动指令已执行"

    def stop_project(self):
        services = [self._build_service_by_conf(i) for i in self.service_list]
        for i in services[::-1]:
            if isinstance(i, str):
                continue
            i.stop()
        return "停止指令已执行"

    def other_service_pids(self) -> Set[int]:
        res_pid = []
        for i in self.other_services:
            service = self._build_service_by_conf(i)
            if isinstance(service, str):
                continue
            pid = service.get_service_pid()
            if isinstance(pid, int) and pid > 0 and psutil.pid_exists(pid):
                res_pid.append(pid)

        sub_pid = []

        def get_sub_pid(pro: psutil.Process) -> List[int]:
            tmp_res = []
            if pro.status() != psutil.STATUS_ZOMBIE and pro.children():
                for sub_pro in pro.children():
                    tmp_res.append(sub_pro.pid)
                    tmp_res.extend(get_sub_pid(sub_pro))
            return tmp_res

        for i in res_pid:
            try:
                p = psutil.Process(i)
                sub_pid.extend(get_sub_pid(p))
            except:
                pass

        return set(res_pid + sub_pid)


class main:

    def __init__(self):
        pass

    @staticmethod
    def get_services_info(get):
        try:
            project_name = get.project_name.strip()
        except:
            return json_response(False, '参数错误')

        s_mgr = ServiceManager.new_mgr(project_name)
        if isinstance(s_mgr, str):
            return json_response(False, s_mgr)
        return json_response(True, data=s_mgr.get_services_info())

    @staticmethod
    def add_service(get):
        try:
            project_name = get.project_name.strip()
            service_conf = get.service_conf
            if isinstance(service_conf, str):
                service_conf = json.loads(service_conf)
            if not isinstance(service_conf, dict):
                return json_response(False, '服务参数配置错误')
        except:
            return json_response(False, '参数错误')

        s_mgr = ServiceManager.new_mgr(project_name)
        if isinstance(s_mgr, str):
            return json_response(False, s_mgr)
        res = s_mgr.add_service(service_conf)
        if isinstance(res, str):
            return json_response(False, res)
        return json_response(True, msg="添加成功")

    @staticmethod
    def modify_service(get):
        try:
            project_name = get.project_name.strip()
            sid = get.sid.strip()
            service_conf = get.service_conf
            if isinstance(service_conf, str):
                service_conf = json.loads(service_conf)
            if not isinstance(service_conf, dict):
                return json_response(False, '服务参数配置错误')
        except:
            return json_response(False, '参数错误')

        s_mgr = ServiceManager.new_mgr(project_name)
        if isinstance(s_mgr, str):
            return json_response(False, s_mgr)

        res = s_mgr.modify_service(sid, service_conf)
        if isinstance(res, str):
            return json_response(False, res)
        return json_response(True, msg="修改成功")

    @staticmethod
    def remove_service(get):
        try:
            project_name = get.project_name.strip()
            sid = get.sid.strip()
        except:
            return json_response(False, '参数错误')

        s_mgr = ServiceManager.new_mgr(project_name)
        if isinstance(s_mgr, str):
            return json_response(False, s_mgr)
        res = s_mgr.remove_service(sid)
        if isinstance(res, str):
            return json_response(False, res)

        return json_response(True, msg="删除成功")

    @staticmethod
    def handle_service(get):
        try:
            project_name = get.project_name.strip()
            sid = get.sid.strip()
            action = get.option.strip()
        except:
            return json_response(False, '参数错误')
        s_mgr = ServiceManager.new_mgr(project_name)
        if isinstance(s_mgr, str):
            return json_response(False, s_mgr)
        res = s_mgr.handle_service(sid, action)
        if isinstance(res, str):
            return json_response(False, res)

        return json_response(True, msg="操作成功")

    @staticmethod
    def get_service_log(get):
        try:
            project_name = get.project_name.strip()
            sid = get.sid.strip()
        except:
            return json_response(False, '参数错误')
        s_mgr = ServiceManager.new_mgr(project_name)
        if isinstance(s_mgr, str):
            return json_response(False, s_mgr)
        res, log = s_mgr.get_service_log(sid)
        if not res:
            return json_response(False, log)
        return json_response(True, data=log)

