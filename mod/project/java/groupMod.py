import copy
import json
import os.path
import sys
import time
import psutil
from typing import Optional, Dict, Union, List, Tuple, Any, Iterable

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public

from mod.base import RealServer, json_response
from mod.project.java import utils
from mod.project.java.projectMod import debug, main as JavaProject


class Group:
    GROUP_DATA_DIR = "/www/server/panel/data/java_group"
    GROUP_TMP_DIR = "/var/tmp/springboot/group"

    def __init__(self, group_id: Optional[str] = None, group_data: Optional[dict] = None):
        self.group_id = group_id
        if isinstance(group_data, dict):
            self.config: Optional[Dict[str, Union[str, List]]] = group_data
        else:
            self.config = self.load_group_data_by_id()

        if not os.path.exists(self.GROUP_DATA_DIR):
            os.makedirs(self.GROUP_DATA_DIR, 0o600)

        if not os.path.exists(self.GROUP_TMP_DIR):
            os.makedirs(self.GROUP_TMP_DIR)

        self.running_data = {
            "length": 0,  # 已完成的数量
            "remaining": 0,  # 未完成的数量
            "executing": 0,  # 正在执行的数量
            "projects": [],  # 项目操作详情
            "msg": "",  # 信息
            "status": True,
        }

    # 如果有配置文件，则表示可以执行
    def can_running(self) -> bool:
        return isinstance(self.config, dict)

    @staticmethod
    def new_group_id() -> str:
        from uuid import uuid4
        return uuid4().hex[::2]

    # 从配置文件中加载数据
    def load_group_data_by_id(self) -> Optional[dict]:
        config_file = "{}/{}.json".format(self.GROUP_DATA_DIR, self.group_id)
        try:
            data = json.loads(public.readFile(config_file))
        except:
            return None
        if isinstance(data, dict):
            return data
        else:
            return None

    def save_group_data(self):
        if self.config:
            config_file = "{}/{}.json".format(self.GROUP_DATA_DIR, self.group_id)
            public.writeFile(config_file, json.dumps(self.config))

    # 更新旧版数据
    @classmethod
    def update_group_data(cls) -> None:
        json_file = "/www/server/panel/class/projectModel/java_project_groups.json"
        if not os.path.isfile(json_file):
            return
        data_str = public.readFile(json_file)
        try:
            data = json.loads(data_str)
        except:
            os.remove(json_file)
            return

        try:
            java_projects = public.M("sites").where('project_type=?', ('Java',)).field("id,name").select()
        except:
            return

        projects_dict = {i["name"]: i["id"] for i in java_projects}

        for idx, i in enumerate(data):
            name = i.get("group_name", "默认分组-{}".format(idx + 1))
            projects = i.get("projects", [])
            order = i.get("order", [])  # type: list
            tmp_p = []
            for p in projects:
                if p["project_name"] in projects_dict and p["project_name"] in order:
                    tmp_p.append({
                        "id": projects_dict[p["project_name"]],
                        "name": p["project_name"],
                        "level": order.index(p["project_name"]) + 1,
                        "check_info": {
                            "type": "port",
                            "port": [],
                            "wait_time": 180,
                        }
                    })

            if tmp_p:
                group_id = cls.new_group_id()
                public.writeFile(
                    "{}/{}.json".format(cls.GROUP_DATA_DIR, group_id),
                    json.dumps({
                        "group_name": name,
                        "projects": tmp_p,
                        "sort_type": "sequence",
                    })
                )

        if os.path.isfile(json_file):
            os.remove(json_file)

    # 检查数据
    def check_group_data(self) -> Optional[str]:
        """
        一个组的格式
        group = {
            "group_name": "aaa",
            "projects": [
                {
                    "id": 84,
                    "name": "tduck-api",
                    "level": 1,
                    "check_info": {
                        "type": ("port" or "active"),
                        "port": [8456, 8511],
                        "wait_time": 180,
                    }
                }
            ],
            "sort_type": ("simultaneous" or "sequence")
        }
        """
        # 检查self.config是否为字典
        if not isinstance(self.config, dict):
            return "参数格式错误"

        # 检查'sort_type'键是否存在且值为("simultaneous" or "sequence")
        if "sort_type" not in self.config or self.config["sort_type"] not in ("simultaneous", "sequence"):
            return "编排方式设置错误"

        if 'group_name' not in self.config or not isinstance(self.config["group_name"], str) \
                or not self.config["group_name"]:
            return "分组名称设置错误"

        # 检查projects键是否存在且为列表
        if "projects" not in self.config or not isinstance(self.config["projects"], list):
            return "项目列表设置错误"

        # id 不能重复
        site_id_set = set()
        # 遍历projects列表中的每个项目
        for project in self.config["projects"]:
            # 检查每个项目是否为字典
            if not isinstance(project, dict):
                return "项目列表设置错误"

            # 检查'id', 'name', 'level', 'check_info'键是否存在
            if not all(key in project for key in ("id", "name", "level", "check_info")):
                return "项目项目配置信息缺失"

            # 检查id、level是否为整数
            if not isinstance(project["id"], int) or not isinstance(project["level"], int):
                return "项目id或优先级参数格式错误"
            else:
                if project["id"] in site_id_set:
                    return "项目id不能重复"
                else:
                    site_id_set.add(project["id"])

            # 检查'check_info'是否为字典
            if not isinstance(project["check_info"], dict):
                return "项目{}检查策略设置错误".format(project["name"])

            # 检查'check_info'中的type, 'port', 'wait_time'
            if not all(key in project["check_info"] for key in ("type", "port", "wait_time")):
                return "项目{}检查策略信息缺失".format(project["name"])

            # 检查type的值
            if project["check_info"]["type"] not in ("port", "active"):
                return "项目{}检查策略类型设置错误".format(project["name"])

        # 如果所有检查都通过，则数据格式正确
        return None

    # 执行 check_info 中的判断，返回现在的进程是否属于在运行中， 如果不是运行中， 就是异常
    @staticmethod
    def do_check_info(check_info: dict, process: psutil.Process):
        if check_info["type"] == "port":
            timeout = time.time() > process.create_time() + 60 * 3
            listen = []
            connections = process.connections()
            for connection in connections:
                if connection.status == "LISTEN":
                    listen.append(connection.laddr.port)

            if not check_info["port"]:
                if not timeout and not bool(listen):
                    return "waiting"
                if not bool(listen):
                    return 'failed'
                else:
                    return 'succeeded'
            else:
                res = not bool(set([int(port) for port in check_info["port"]]) - set(listen))  # 如果所有的端口都在监听中，则返回True
                if not timeout and not res:
                    return 'waiting'
                if res:
                    return 'succeeded'
                else:
                    return 'failed'
        else:
            create_time = process.create_time()
            if time.time() > create_time + int(check_info["wait_time"]):
                return "succeeded"
            else:
                return "waiting"

    @staticmethod
    def is_running(pid: int):
        try:
            return psutil.Process(pid).is_running()
        except:
            return False

    # 获取运行状态信息
    def run_status(self, last_write_time: float) -> dict:
        default_error = {
                "running": False,
                "msg": "操作出错，已退出",
                "running_data": None,
                "last_write_time": 0,
            }
        pid_file = "{}/{}.pid".format(Group.GROUP_TMP_DIR, self.group_id)
        log_file = "{}/{}.log".format(Group.GROUP_TMP_DIR, self.group_id)
        if not os.path.isfile(pid_file):
            return default_error
        try:
            pid = int(public.readFile(pid_file))
        except:
            return default_error

        try:
            data = json.loads(public.readFile(log_file))
        except:  # 如果读取出错，则说明进程出现问题，则杀死进程，并清除数据，返回错误
            if os.path.isfile(log_file):
                os.remove(log_file)
            if os.path.isfile(pid_file):
                os.remove(pid_file)
            if self.is_running(pid):
                psutil.Process(pid).kill()

            return default_error

        # 如果进程不在运行，则返回上一次运行的数据（防止卡顿导致导致最后的数据没有读取到）
        if not self.is_running(pid):
            return {
                "running": False,
                "msg": "操作进程已退出",
                "running_data": data,
                "last_write_time": os.path.getmtime(log_file),
            }

        # 如果还在运行， 则进行长链接， 等待最多5秒， 如果没有数据被写入， 且进程依旧在运行，则返回上一次的数据；
        # 若不在运行则说明，且没有写入则说明等待期间出错了 （启动进程退出前必定会进行一次写入）
        # 如果有数据被写入则返回最新数据

        for i in range(50):
            m_time = os.path.getmtime(log_file)
            if abs(m_time - last_write_time) > 0.001:  # 如果时间差大于0.001秒，则说明数据再次被写入了，则退出循环，返回数据
                now_write_time = m_time
                break
            elif i == 49:  # 最后一次检测后，直接退出循环
                continue
            else:
                time.sleep(0.1)
        else:  # 如果 5 秒内没有数据被写入，则返回上一次的数据
            if not self.is_running(pid):  # 不在运行, 说明等待期间出错了
                if os.path.isfile(log_file):
                    os.remove(log_file)
                if os.path.isfile(pid_file):
                    os.remove(pid_file)
                    return default_error

            # 在运行，则返回上一次的数据
            return {
                "running": self.is_running(pid),
                "msg": "运行中",
                "running_data": data,
                "last_write_time": last_write_time,
            }

        #
        try:
            data = json.loads(public.readFile(log_file))
        except:
            if self.is_running(pid):
                psutil.Process(pid).kill()
            if os.path.isfile(log_file):
                os.remove(log_file)
            if os.path.isfile(pid_file):
                os.remove(pid_file)
            return {
                "running": False,
                "msg": "操作进程出错，已退出",
                "running_data": None,
                "last_write_time": 0,
            }
        running = self.is_running(pid)
        return {
            "running": running,
            "msg": "运行中" if running else "操作进程已结束",
            "running_data": data,
            "last_write_time": now_write_time,
        }

    # 获取可操作状态的信息
    def get_operation_info(self) -> Tuple[Iterable[str], str]:
        pid_file = "{}/{}.pid".format(Group.GROUP_TMP_DIR, self.group_id)
        try:
            pid = int(public.readFile(pid_file))
            p = psutil.Process(pid)
            if not p.is_running():
                return ("start", "stop"), ""
            else:
                last_cmd = p.cmdline()[-2] if len(p.cmdline()) == 4 else ""
                return ("termination",), last_cmd

        except:
            pass
        return ("start", "stop"), ""

    def group_info(self, project_cache: Optional[dict] = None) -> Optional[dict]:
        if not self.config:
            return
        if not project_cache:
            project_ids = [i["id"] for i in self.config["projects"]]
            if not project_ids:
                data = copy.deepcopy(self.config)
                data["group_id"] = self.group_id
                return data

            projects = public.M('sites').where(
                'project_type=? and id IN ({})'.format(",".join(["?"] * len(project_ids))),
                ('Java', *project_ids)).select()
            project_cache = {}
            for i in projects:
                i["project_config"] = json.loads(i["project_config"])
                project_cache[i["id"]] = i

        j_pro = JavaProject()

        res = copy.deepcopy(self.config)
        res["group_id"] = self.group_id
        res["operation_info"], res["now_operation"] = self.get_operation_info()
        running_num = 0
        need_del = []
        for idx, i in enumerate(res["projects"]):
            if i["id"] in project_cache:
                try:
                    listen = []
                    pid = j_pro.get_project_pid(project_cache[i["id"]])
                    p = psutil.Process(int(pid))
                    connections = p.connections()
                    for connection in connections:
                        if connection.status == "LISTEN":
                            listen.append(connection.laddr.port)
                except:
                    i["running"] = False
                    i["project_status"] = 'not_run'
                    i["pid"] = None
                    i["listen"] = []
                    continue

                running_num += 1
                i["running"] = True
                i["project_status"] = self.do_check_info(i["check_info"], p)
                i["pid"] = p.pid
                i["listen"] = listen
            else:
                need_del.append(idx)

        for j in need_del[::-1]:
            del res["projects"][j]
            del self.config["projects"][j]

        if need_del:
            self.save_group_data()

        if not res["now_operation"]:
            all_num = len(res["projects"])
            if all_num == 0:
                res["operation_info"] = []
            else:
                if running_num == all_num:
                    res["operation_info"] = ["stop"]
                if running_num == 0:
                    res["operation_info"] = ["start"]

        return res

    # 运行一个Group相关的函数
    # ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓ ↓
    def run_operation(self, operation: str) -> Optional[str]:
        pid_file = "{}/{}.pid".format(Group.GROUP_TMP_DIR, self.group_id)

        if operation not in ("start", "stop"):
            return "指定的操作不存在"

        try:
            p = psutil.Process(public.readFile(pid_file))
            if p.is_running():
                return "操作运行中， 请等待上一个操作执行完成"
        except:
            pass

        if os.path.exists(pid_file):
            os.remove(pid_file)

        self.build_run_sort(reverse=(operation == "stop"))
        self.save_running_data()
        panel_path = "/www/server/panel"
        public.ExecShell(
            "nohup {}/pyenv/bin/python3 {}/mod/project/java/group_script.py {} {} &> /tmp/group_script.log & \n"
            "echo $! > {} ".format(
                panel_path, panel_path, operation, self.group_id, pid_file)
        )
        return None

    def build_run_sort(self, reverse=False) -> List[List[dict]]:
        projects = self.config["projects"]  # type: List[Dict[str, Union[int, str, dict]]]
        if self.config["sort_type"] == "simultaneous":
            projects_group = [projects]
        else:
            projects_group = []
            projects.sort(key=lambda x: x['level'])
            last_level = -1
            for i in projects:
                if i['level'] != last_level:
                    last_level = i['level']
                    projects_group.append([i])
                else:
                    projects_group[-1].append(i)

        self.running_data['length'] = len(projects)
        self.running_data['remaining'] = len(projects)
        for g in projects_group:
            names = [i["name"] for i in g]
            self.running_data["projects"].append({
                "names": names,
                "msg": "",
                "running": False,
                "data": {
                    i["name"]: {"status": False, "msg": "", "pid": 0, "name": i["name"]}
                    for i in g
                }
            })

        if reverse:
            self.running_data["projects"] = self.running_data["projects"][::-1]
            return projects_group[::-1]

        return projects_group

    # 真正执行启动的逻辑
    def real_run_start(self):
        pid_file = "{}/{}.pid".format(Group.GROUP_TMP_DIR, self.group_id)
        pid = os.getpid()
        public.writeFile(pid_file, str(pid))
        if not self.can_running():
            self.running_data["msg"] = "项目组配置文件错误，无法启动该项目组"
            self.running_data["status"] = False
            self.save_running_data()
            return

        # 构建运行启动的信息，并返回运行顺序
        self.running_data["msg"] = "启动操作运行中"
        run_sort = self.build_run_sort(reverse=False)
        self.save_running_data()
        for idx, g in enumerate(run_sort):
            res_msg = self._run_start_one_step(g, sort_idx=idx)
            if isinstance(res_msg, str):
                self.running_data["msg"] = res_msg
                self.running_data["status"] = False
                self.save_running_data()
                return

        self.running_data["msg"] = "启动操作运行成功"
        self.running_data["status"] = True
        self.save_running_data()

    def save_running_data(self):
        log_file = "{}/{}.log".format(Group.GROUP_TMP_DIR, self.group_id)
        public.writeFile(log_file, json.dumps(self.running_data))

    # 执行启动任务的每一个优先级中所有的项目
    def _run_start_one_step(self, projects: List[dict], sort_idx: int) -> Optional[str]:
        j_pro = JavaProject()

        step_running_data = self.running_data["projects"][sort_idx]  # type: Dict[str, Any]
        step_running_data["running"] = True
        step_running_data["msg"] = "正在启动【{}】项目".format(", ".join(step_running_data["names"]))
        self.running_data["remaining"] -= len(projects)
        self.running_data["executing"] = len(projects)
        self.save_running_data()

        need_wait_project = []
        error_msg = None
        # 尝试启动每一个项目
        for p in projects:
            project_data = j_pro.get_project_find(p["name"])
            if not project_data:
                step_running_data["data"][p["name"]]["msg"] = "项目【{}】已丢失，无法启动".format(p["name"])
                continue
            project_pid = j_pro.get_project_pid(project_data)
            if project_pid:
                step_running_data["data"][p["name"]]["status"] = True
                step_running_data["data"][p["name"]]["msg"] = "项目【{}】已处于运行状态，未重新执行启动操作".format(
                    p["name"])
                step_running_data["data"][p["name"]]["pid"] = project_pid
                continue

            res = j_pro.start_spring_boot_project(project_data, wait=False)  # 不等待启动成功
            if not res["status"]:
                step_running_data["data"][p["name"]]["status"] = False
                step_running_data["data"][p["name"]]["msg"] = "在执行启动项目【{}】指令的时出现错误：{}".format(
                    p["name"], res["msg"])

                error_msg = "出现无法处理的项目启动问题：" + res["msg"]
                break  # 出现无法启动的项目，直接退出
            else:
                need_wait_project.append((project_data, p["check_info"]))

        if error_msg:
            return error_msg

        if not need_wait_project:
            return None

        self.save_running_data()
        time.sleep(0.5)
        while need_wait_project:
            remove_idx = []
            error_projects = []
            change = False
            for idx, (pd, check_info) in enumerate(need_wait_project):
                if "process" not in pd or not isinstance(pd["process"], psutil.Process):
                    try:
                        pid = j_pro.get_project_pid(pd)
                        process = psutil.Process(int(pid))
                    except:
                        process = None
                else:
                    process = pd["process"]

                if not isinstance(process, psutil.Process) or not process.is_running():
                    step_running_data["data"][pd["name"]]["status"] = False
                    step_running_data["data"][pd["name"]]["msg"] = "项目【{}】启动失败，详细情况请查看日志".format(
                        pd["name"])
                    change = True
                    remove_idx.append(idx)
                    error_projects.append(pd["name"])
                    continue
                else:
                    if step_running_data["data"][pd["name"]]["pid"] == 0:
                        step_running_data["data"][pd["name"]]["pid"] = process.pid
                        change = True

                    tmp_res = self.do_check_info(check_info, process)
                    if tmp_res == "succeeded":
                        step_running_data["data"][pd["name"]]["status"] = True
                        step_running_data["data"][pd["name"]]["msg"] = "项目【{}】启动成功".format(pd["name"])
                        remove_idx.append(idx)
                        self.running_data["executing"] -= 1
                        change = True
                    elif tmp_res == "failed":
                        step_running_data["data"][pd["name"]]["status"] = False
                        step_running_data["data"][pd["name"]]["msg"] = "项目【{}】启动失败，详细情况请查看日志".format(
                            pd["name"])
                        remove_idx.append(idx)
                        error_projects.append(pd["name"])
                        change = True
                        continue

            if remove_idx:
                for idx in remove_idx:
                    need_wait_project.pop(idx)

            if error_projects:
                return "项目【{}】启动失败无法继续执行启动操作，请查看日志".format(",".join(error_projects))
            if change is True:
                self.save_running_data()
            if need_wait_project:
                time.sleep(0.2)

        step_running_data["running"] = False
        self.save_running_data()
        return

    def real_run_stop(self):
        pid_file = "{}/{}.pid".format(Group.GROUP_TMP_DIR, self.group_id)
        pid = os.getpid()
        public.writeFile(pid_file, str(pid))
        if not self.can_running():
            self.running_data["msg"] = "项目组配置文件错误，无法停止该项目组"
            self.running_data["status"] = False
            self.save_running_data()
            return

        # 构建运行启动的信息，并返回运行顺序
        self.running_data["msg"] = "项目组停止操作运行中"
        run_sort = self.build_run_sort(reverse=True)
        self.save_running_data()
        for idx, g in enumerate(run_sort):
            self._run_stop_one_step(g, sort_idx=idx)

        self.running_data["msg"] = "停止操作运行成功"
        self.running_data["status"] = True
        self.save_running_data()

    def _run_stop_one_step(self, projects: List[dict], sort_idx: int) -> None:
        j_pro = JavaProject()

        step_running_data = self.running_data["projects"][sort_idx]  # type: Dict[str, Any]
        step_running_data["running"] = True
        step_running_data["msg"] = "正在执行【{}】项目的停止任务".format(", ".join(step_running_data["names"]))
        self.running_data["remaining"] -= len(projects)
        self.running_data["executing"] = len(projects)

        need_wait_project = []
        # 尝试停止每一个项目
        for p in projects:
            project_data = j_pro.get_project_find(p["name"])
            if not project_data:
                step_running_data["data"][p["name"]]["msg"] = "项目【】已丢失，无法执行停止操作"
                continue

            project_pid = j_pro.get_project_pid(project_data)
            if not project_pid:
                step_running_data["data"][p["name"]]["status"] = True
                step_running_data["data"][p["name"]]["msg"] = "项目【{}】已停止".format(p["name"])
                continue
            else:
                project_data["pid"] = project_pid

            project_config = project_data["project_config"]
            server_name = "spring_" + project_config["project_name"] + project_config.get("server_name_suffix", "")
            s_admin = RealServer()
            if s_admin.daemon_status(server_name)["msg"] == "服务不存在!":
                j_pro.stop_by_kill_pid(project_data)
                if os.path.isfile(project_config["pids"]):
                    os.remove(project_config["pids"])
            else:
                s_admin.daemon_admin(server_name, "stop")
            utils.stop_by_user(project_data["id"])
            need_wait_project.append((project_data, p["check_info"]))

        if not need_wait_project:
            return None

        self.save_running_data()
        time.sleep(0.05)
        wait_num = 0
        while need_wait_project and wait_num < 10:
            remove_idx = []
            change = False
            for idx, (pd, check_info) in enumerate(need_wait_project):
                pid = pd["pid"]
                pid_info = j_pro.real_process.get_process_info_by_pid(pid)["data"]
                if not pid_info:
                    step_running_data["data"][pd["name"]]["status"] = True
                    step_running_data["data"][pd["name"]]["msg"] = "项目【{}】停止成功".format(pd["name"])
                    remove_idx.append(idx)
                    self.running_data["executing"] -= 1
                    change = True

            if remove_idx:
                for idx in remove_idx:
                    need_wait_project.pop(idx)

            if change is True:
                self.save_running_data()

            wait_num += 1
            if need_wait_project:
                time.sleep(0.1)

        step_running_data["running"] = False
        self.save_running_data()

        return

    def termination_operation(self) -> None:
        pid_file = "{}/{}.pid".format(Group.GROUP_TMP_DIR, self.group_id)
        try:
            pid = int(public.readFile(pid_file))
            p = psutil.Process(pid)
            p.kill()
            os.remove(pid_file)
        except:
            pass


class GroupMager:
    cache_type = ["springboot"]

    def __init__(self):
        self.project_cache: Optional[dict] = None

        if not os.path.exists(Group.GROUP_DATA_DIR):
            os.makedirs(Group.GROUP_DATA_DIR, 0o600)

        if not os.path.exists(Group.GROUP_TMP_DIR):
            os.makedirs(Group.GROUP_TMP_DIR)

    def _get_project_cache(self):
        if self.project_cache is not None:
            return
        java_projects = public.M("sites").where('project_type=?', ('Java',)).select()
        _cache = {}
        for i in java_projects:
            config = json.loads(i["project_config"])
            if config["java_type"] in self.cache_type:
                i["project_config"] = config
                _cache[i["id"]] = i

        self.project_cache = _cache

    def group_list(self) -> List[dict]:
        group_list = []
        for i in os.listdir(Group.GROUP_DATA_DIR):
            file = "{}/{}".format(Group.GROUP_DATA_DIR, i)
            if os.path.isfile(file) and i.endswith(".json"):
                group_id = i[:-5]
                try:
                    data = json.loads(public.readFile(file))
                except:
                    continue
                g = Group(group_id, data)
                group_list.append(g)

        if not group_list:
            return []

        self._get_project_cache()
        res = []
        for i in group_list:
            res.append(i.group_info(self.project_cache))

        return res

    @staticmethod
    def add_group(data: dict) -> Optional[str]:
        g = Group(Group.new_group_id(), data)
        res = g.check_group_data()
        if isinstance(res, str):
            return res
        g.save_group_data()

    @staticmethod
    def remove_group(group_id: str) -> None:
        config_file = "{}/{}.json".format(Group.GROUP_DATA_DIR, group_id)
        if os.path.isfile(config_file):
            os.remove(config_file)

    @staticmethod
    def add_project_to_group(group_id: str, project_name: str, check_info: dict, level: Optional[int]) -> Optional[str]:
        g = Group(group_id)
        if not g.config:
            return "项目组不存在"
        p = public.M("sites").where('project_type=? AND name=?', ('Java', project_name)).find()
        if not p:
            return "指定项目【{}】不存在".format(project_name)
        project_config = json.loads(p["project_config"])
        if not project_config["java_type"] in GroupMager.cache_type:
            return "指定项目【{}】不是spring boot项目, 不支持添加到项目组".format(project_name)

        used_project = [p["id"] for p in g.config["projects"]]
        if p["id"] in used_project:
            return "项目【{}】已存在于项目组【{}】".format(project_name, group_id)

        if level is None:
            if not g.config["projects"]:
                level = 1
            else:
                level = max([p["level"] for p in g.config["projects"]]) + 1

        g.config["projects"].append({
            "name": project_name,
            "id": p["id"],
            "check_info": check_info,
            "level": level,
        })
        res = g.check_group_data()
        if isinstance(res, str):
            return res
        g.save_group_data()

    @staticmethod
    def add_projects_to_group(group_id: str, project_ids: List[int]) -> Optional[str]:
        g = Group(group_id)
        if not g.config:
            return "项目组不存在"
        project_list = public.M("sites").where(
            'project_type=? AND id IN ({})'.format(",".join(["?"] * len(project_ids))),
            ('Java', *project_ids)
        ).select()

        used_project = [p["id"] for p in g.config["projects"]]
        start_level = max([p["level"] for p in g.config["projects"]] + [1])  # 最小值为1
        for p in project_list:
            if p["id"] in used_project:
                return "项目【{}】已存在于项目组【{}】".format(p["name"], group_id)
            project_config = json.loads(p["project_config"])
            if not project_config["java_type"] in GroupMager.cache_type:
                return "指定项目【{}】不是spring boot项目, 不支持添加到项目组".format(p["name"])

            g.config["projects"].append({
                "name": p["name"],
                "id": p["id"],
                "check_info": {
                    "type": "port",
                    "port": [],
                    "wait_time": 180,
                },
                "level": start_level + 1,
            })
            start_level += 1

        res = g.check_group_data()
        if isinstance(res, str):
            return res
        g.save_group_data()

    @staticmethod
    def remove_project_from_group(group_id: str, project_id: int) -> Optional[str]:
        g = Group(group_id)
        if not g.config:
            return "项目组不存在"
        target_idx = None
        for idx, p in enumerate(g.config["projects"]):
            if p["id"] == project_id:
                target_idx = idx
                break
        if target_idx is not None:
            g.config["projects"].pop(target_idx)
            g.save_group_data()

    @staticmethod
    def modify_group(group_id: str, group_data: dict) -> Optional[str]:
        g = Group(group_id, group_data)
        res = g.check_group_data()
        if isinstance(res, str):
            return res
        g.save_group_data()

    @staticmethod
    def modify_group_projects(group_id: str, project_datas: list) -> Optional[str]:
        g = Group(group_id)
        if not g.config:
            return "项目组不存在"

        project_ids = [p["id"] for p in project_datas]
        project_list = public.M("sites").where(
            'project_type=? AND id IN ({})'.format(",".join(["?"] * len(project_ids))),
            ('Java', *project_ids)
        ).select()

        for p in project_list:
            project_config = json.loads(p["project_config"])
            if not project_config["java_type"] in GroupMager.cache_type:
                return "指定项目【{}】不是spring boot项目, 不支持设置到项目组".format(p["name"])

        g.config["projects"] = project_datas
        res = g.check_group_data()
        if isinstance(res, str):
            return res

        g.save_group_data()

    @staticmethod
    def modify_group_project(group_id: str, project_id: int,
                             check_info: Optional[dict], level: Optional[int]) -> Optional[str]:
        g = Group(group_id)
        if not g.config:
            return "项目组不存在"
        p = public.M("sites").where('project_type=? AND id=?', ('Java', project_id)).find()
        if not p:
            return "指定项目不存在"

        target_idx = None
        for idx, p in enumerate(g.config["projects"]):
            if p["id"] == project_id:
                target_idx = idx
                break

        if target_idx is None:
            return "指定项目不在该项目组内"
        update_data = {}
        if check_info is not None:
            update_data["check_info"] = check_info
        if level is not None:
            update_data["level"] = level

        g.config["projects"][target_idx].update(update_data)

        res = g.check_group_data()
        if isinstance(res, str):
            return res

        g.save_group_data()

    @staticmethod
    def change_sort_type(group_id: str, sort_type: str) -> Optional[str]:
        g = Group(group_id)
        if not g.config:
            return "项目组不存在"

        if sort_type not in ("simultaneous", "sequence"):
            return "排序方式错误"
        g.config["sort_type"] = sort_type
        g.save_group_data()


Group.update_group_data()


class main:

    def __init__(self):
        pass

    @staticmethod
    def group_list(get):
        return GroupMager().group_list()

    @staticmethod
    def group_info(get):
        try:
            group_id = get.group_id.strip()
        except:
            return json_response(status=False, msg="参数错误")
        g = Group(group_id)
        if not g.config:
            return json_response(status=False, msg="项目组不存在")
        else:
            return json_response(status=True, data=g.group_info())

    @staticmethod
    def add_group(get):
        try:
            group_name = get.group_name.strip()
        except:
            return json_response(status=False, msg="参数错误")
        res = GroupMager().add_group({
            "group_name": group_name,
            "sort_type": "simultaneous",
            "projects": [],
        })
        if isinstance(res, str):
            return json_response(status=False, msg=res)
        else:
            return json_response(status=True, msg="添加成功")

    @staticmethod
    def add_group_with_data(get):
        try:
            group_name = get.group_name.strip()
            sort_type = get.sort_type.strip()
            if hasattr(get, "projects"):
                projects = get.projects
                if isinstance(projects, str):
                    projects = json.loads(projects)
            else:
                projects = []
        except:
            return json_response(status=False, msg="参数错误")
        res = GroupMager().add_group({
            "group_name": group_name,
            "sort_type": sort_type,
            "projects": projects,
        })
        if isinstance(res, str):
            return json_response(status=False, msg=res)
        else:
            return json_response(status=True, msg="添加成功")

    @staticmethod
    def modify_group(get):
        try:
            group_id = get.group_id.strip()
            if isinstance(get.group_data, str):
                group_data = json.loads(get.group_data)
            else:
                group_data = get.group_data
        except:
            return json_response(status=False, msg="参数错误")
        res = GroupMager.modify_group(group_id, group_data)
        if isinstance(res, str):
            return json_response(status=False, msg=res)
        else:
            return json_response(status=True, msg="修改成功")

    @staticmethod
    def remove_group(get):
        try:
            group_id = get.group_id.strip()
        except:
            return json_response(status=False, msg="参数错误")
        GroupMager.remove_group(group_id)
        return json_response(status=True, msg="删除成功")

    @staticmethod
    def add_project_to_group(get):
        check_info = {
            "type": "port",
            "port": [],
            "wait_time": 180,
        }
        level = None
        try:
            group_id = get.group_id.strip()
            project_name = get.project_name.strip()
            if hasattr(get, "check_info") and get.check_info:
                check_info = json.loads(get.check_info)
            if hasattr(get, "level") and get.level:
                level = int(get.level)
        except:
            return json_response(status=False, msg="参数错误")
        res = GroupMager.add_project_to_group(group_id, project_name, check_info, level)
        if isinstance(res, str):
            return json_response(status=False, msg=res)
        else:
            return json_response(status=True, msg="添加成功")

    @staticmethod
    def add_projects_to_group(get):

        try:
            group_id = get.group_id.strip()
            if hasattr(get, "project_ids") and isinstance(get.project_ids, str):
                project_ids = json.loads(get.project_ids)
            else:
                if isinstance(get.project_ids, list):
                    project_ids = get.project_ids
                else:
                    return json_response(status=False, msg="参数错误")
        except:
            return json_response(status=False, msg="参数错误")
        res = GroupMager.add_projects_to_group(group_id, project_ids)
        if isinstance(res, str):
            return json_response(status=False, msg=res)
        else:
            return json_response(status=True, msg="添加成功")

    @staticmethod
    def remove_project_from_group(get):
        try:
            group_id = get.group_id.strip()
            project_id = int(get.project_id)
        except:
            return json_response(status=False, msg="参数错误")
        res = GroupMager.remove_project_from_group(group_id, project_id)
        if isinstance(res, str):
            return json_response(status=False, msg=res)
        else:
            return json_response(status=True, msg="删除成功")

    @staticmethod
    def modify_group_project(get):
        check_info = None
        level = None
        try:
            group_id = get.group_id.strip()
            project_id = int(get.project_id)
            if hasattr(get, "check_info") and get.check_info:
                check_info = json.loads(get.check_info)
            if hasattr(get, "level") and get.level:
                level = int(get.level)
        except:
            return json_response(status=False, msg="参数错误")
        res = GroupMager.modify_group_project(group_id, project_id, check_info, level)
        if isinstance(res, str):
            return json_response(status=False, msg=res)
        else:
            return json_response(status=True, msg="修改成功")

    @staticmethod
    def modify_group_projects(get):
        try:
            group_id = get.group_id.strip()
            if isinstance(get.project_datas, str):
                project_datas = json.loads(get.project_datas)
            else:
                project_datas = get.project_datas
        except:
            return json_response(status=False, msg="参数错误")
        res = GroupMager.modify_group_projects(group_id, project_datas)
        if isinstance(res, str):
            return json_response(status=False, msg=res)
        else:
            return json_response(status=True, msg="修改成功")

    @staticmethod
    def change_sort_type(get):
        try:
            group_id = get.group_id.strip()
            sort_type = get.sort_type.strip()
        except:
            return json_response(status=False, msg="参数错误")
        res = GroupMager.change_sort_type(group_id, sort_type)
        if isinstance(res, str):
            return json_response(status=False, msg=res)
        else:
            return json_response(status=True, msg="修改成功")

    @staticmethod
    def start_group(get):
        try:
            group_id = get.group_id.strip()
        except:
            return json_response(status=False, msg="参数错误")

        g = Group(group_id)
        if not g.config:
            return json_response(status=False, msg="项目组不存在")

        res = g.run_operation("start")

        if isinstance(res, str):
            return json_response(status=False, msg=res)
        else:
            return json_response(status=True, msg="启动进行中")

    @staticmethod
    def stop_group(get):
        try:
            group_id = get.group_id.strip()
        except:
            return json_response(status=False, msg="参数错误")

        g = Group(group_id)
        if not g.config:
            return json_response(status=False, msg="项目组不存在")

        res = g.run_operation("stop")

        if isinstance(res, str):
            return json_response(status=False, msg=res)
        else:
            return json_response(status=True, msg="停止进行中")

    @staticmethod
    def get_run_status(get):
        last_write_time = 0
        try:
            group_id = get.group_id.strip()
            if hasattr(get, "last_write_time") and get.last_write_time:
                last_write_time = float(get.last_write_time)
        except:
            return json_response(status=False, msg="参数错误")

        g = Group(group_id)
        if not g.config:
            return json_response(status=False, msg="项目组不存在")

        run_status = g.run_status(last_write_time)
        run_status["running_step"] = None
        if isinstance(run_status, dict):
            if isinstance(run_status["running_data"], dict) and "projects" in run_status["running_data"]:
                projects = run_status["running_data"]["projects"]
                for i in projects:
                    if i["running"] is True:
                        run_status["running_step"] = i

        return json_response(status=True, data=run_status)

    @staticmethod
    def termination_operation(get):
        try:
            group_id = get.group_id.strip()
        except:
            return json_response(status=False, msg="参数错误")
        Group(group_id).termination_operation()
        return json_response(status=True, msg="操作成功")

    @staticmethod
    def spring_projects(get):
        java_projects = public.M("sites").where('project_type=?', ('Java',)).field("name,id,project_config").select()
        res = []
        for i in java_projects:
            config = json.loads(i["project_config"])
            if config["java_type"] in GroupMager.cache_type:
                res.append({
                    "name": i["name"],
                    "id": i["id"]
                })

        return res
