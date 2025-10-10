import copy
import os
import re
import sys
import json
import socket
import time
import traceback

import psutil
import errno

from typing import Optional, List
from threading import Thread
from urllib3.util import parse_url, Url

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public


from mod.base import RealServer
from mod.base import json_response
from mod.project.java.projectMod import main as java_mod
from mod.project.java import utils


class ProjectUpdate:

    def __init__(self, project_name: str, new_jar: str, new_port: int = None, run_time: int = None):
        self.project_name = project_name
        self.new_jar = new_jar
        self.j_project = java_mod()
        self.keep_path = self.j_project._java_project_path + "/keep"

        if not os.path.exists(self.keep_path):
            os.makedirs(self.keep_path, 0o755)

        self.keep_log = "{}/{}.log".format(self.keep_path, self.project_name)

        # 不停机更新时使用
        self.new_port = new_port
        self.run_time = run_time
        self.keep_status = []
        self.new_project_config = None
        self.old_project_config = None

        self.old_pro: Optional[psutil.Process] = None
        self.new_pro: Optional[psutil.Process] = None

        self.end = False
        self.old_project_data = None
        self.proxy_data = {
            "scheme": "http"
        }

    @staticmethod
    def new_suffix() -> str:
        import uuid
        return "_" + uuid.uuid4().hex[::4]

    def start_spring_project(self, project_data: dict, write_systemd_file=True, need_wait=True, ) -> dict:
        return self.j_project._start_spring_boot_project(project_data, write_systemd_file, need_wait)

    def restart_update(self) -> dict:
        project_data = self.j_project.get_project_find(self.project_name)
        if not project_data:
            return json_response(False, msg="项目不存在")

        project_config = project_data['project_config']
        old_jar = project_config['project_jar']
        if self.new_jar != old_jar:
            if not os.path.isfile(self.new_jar):
                return json_response(False, msg="项目jar包不存在")

            project_config['jar_path'] = os.path.dirname(self.new_jar)
            project_config['project_jar'] = self.new_jar
            old_jar_name = os.path.basename(old_jar)
            project_cmd_list = project_config['project_cmd'].split(" ")
            for i in range(len(project_cmd_list)):
                if old_jar_name in project_cmd_list[i]:
                    project_cmd_list[i] = self.new_jar
                    break

            new_project_cmd = " ".join(project_cmd_list)
            project_config['project_cmd'] = new_project_cmd
            project_config["change_flag"] = True

        s_admin = RealServer()
        server_name = "spring_" + project_config["project_name"] + project_config.get("server_name_suffix", "")
        if s_admin.daemon_status(server_name)["msg"] == "服务不存在!":
            self.j_project.stop_by_kill_pid(project_data)
            if os.path.isfile(project_config["pids"]):
                os.remove(project_config["pids"])
            return self.start_spring_project(project_data, write_systemd_file=True, need_wait=False)

        if "change_flag" in project_config and project_config.get("change_flag", False):
            del project_config["change_flag"]
            s_admin.daemon_admin(server_name, "stop")
            s_admin.del_daemon(server_name)
            self.j_project.stop_by_kill_pid(project_data)
            if os.path.isfile(project_config["pids"]):
                os.remove(project_config["pids"])

            public.M("sites").where("id=?", (project_data["id"],)).update(
                {"project_config": json.dumps(project_config)}
            )
            return self.start_spring_project(project_data, write_systemd_file=True)
        else:
            return self.start_spring_project(project_data, write_systemd_file=False)

    # 实际执行启动的线程
    def run_task(self):
        print("___________开始________________")
        try:
            res = self.start_new()
            self.keep_status[0]["status"] = 1
            if res:
                self.keep_status[0]["msg"] = res
                return
            else:
                self.keep_status[0]["msg"] = "新实例已启动，新实例pid:{}".format(self.new_pro.pid)
            res = self.set_nginx_upstream()
            self.keep_status[1]["status"] = 1
            if res:
                self.stop_new()
                self.keep_status[1]["msg"] = res
                return
            else:
                self.keep_status[1]["msg"] = "Nginx已配置完成轮询设置，您可以访问新实例了"
            res = self.wait_time()
            self.keep_status[2]["status"] = 1
            if res:
                self.keep_status[2]["msg"] = res
                return
            else:
                self.keep_status[2]["msg"] = "等待时间结束，新实例已启动成功"
            res = self.stop_old()
            self.keep_status[3]["status"] = 1
            self.keep_status[3]["msg"] = res if res else "停止旧实例成功，项目更新已结束"
            public.M("sites").where("id=?", (self.old_project_data["id"],)).update(
                {"project_config": json.dumps(self.new_project_config)}
            )
        except:
            print(traceback.format_exc())
            pass

    def stop_new(self):
        new_server_name = "spring_" + self.project_name + self.new_project_config.get("server_name_suffix", "")
        RealServer().server_admin(new_server_name, "stop")
        RealServer().del_daemon(new_server_name)
        if self.new_pro and self.new_pro.is_running():
            self.new_pro.kill()

    def start_new(self) -> Optional[str]:
        self.keep_status[0]["status"] = -1
        self.new_project_config['server_name_suffix'] = self.new_suffix()
        self.new_project_config['pids'] = "{}/pids/{}.pid".format(
            self.j_project._java_project_vhost, self.project_name + self.new_project_config['server_name_suffix']
        )

        if not self.new_port or self.new_port in self.old_listen_port() or \
                utils.check_port_with_net_connections(self.new_port):
            self.new_port = utils.create_a_not_used_port()

        old_jar = self.old_project_config['project_jar']
        if self.new_jar != old_jar:
            if not os.path.isfile(self.new_jar):
                return "项目jar包不存在"

            self.new_project_config['jar_path'] = os.path.dirname(self.new_jar)
            self.new_project_config['project_jar'] = self.new_jar
            old_jar_name = os.path.basename(old_jar)
            project_cmd_list = self.new_project_config['project_cmd'].split(" ")
            for i in range(len(project_cmd_list)):
                if old_jar_name in project_cmd_list[i]:
                    project_cmd_list[i] = self.new_jar
                    break

            new_project_cmd = " ".join(project_cmd_list)
            self.new_project_config['project_cmd'] = new_project_cmd

        if "--server.port=" in self.new_project_config['project_cmd']:
            self.new_project_config['project_cmd'] = re.sub(
                r"--server\.port=\d+",
                "--server.port={}".format(self.new_port),
                self.new_project_config['project_cmd']
            )
        else:
            self.new_project_config['project_cmd'] += " --server.port={}".format(self.new_port)

        self.old_project_data["project_config"] = self.new_project_config

        self.start_spring_project(self.old_project_data, write_systemd_file=True)
        time.sleep(1)
        new_pid = self.j_project.get_project_pid(self.old_project_data)
        if not new_pid:
            return "项目启动失败"
        self.new_pro = psutil.Process(new_pid)
        self.keep_status[0]["msg"] = "新实例pid为:{}".format(new_pid)
        # 开始等待进程启动
        server_name = "spring_" + self.project_name + self.new_project_config.get("server_name_suffix", "")
        wait_num = 1
        for i in range(5 * 60 * 2 - 2):
            if self.end:
                RealServer().server_admin(server_name, "stop")
                RealServer().del_daemon(server_name)
                return "退出操作"
            if not self.new_pro.is_running():
                RealServer().del_daemon(server_name)
                return "项目启动失败"

            conns = self.new_pro.connections()
            for c in conns:
                if c.status == "LISTEN" and c.laddr.port == self.new_port:
                    return
            self.keep_status[0]["msg"] = "新实例pid为:{}, 正在等待该进程监听端口：{}, 已等待{}s".format(new_pid, self.new_port, wait_num)
            wait_num += 0.5
            time.sleep(0.5)

        RealServer().server_admin(server_name, "stop")
        RealServer().del_daemon(server_name)
        return "启动超时"

    def old_listen_port(self) -> List[int]:
        connects = self.old_pro.connections()
        res = []
        for i in connects:
            if i.status == "LISTEN":
                res.append(i.laddr.port)
        return res

    def set_nginx_upstream(self) -> Optional[str]:
        self.keep_status[1]["status"] = -1
        ng_file = "/www/server/panel/vhost/nginx/java_{}.conf".format(self.project_name)
        res = public.checkWebConfig()
        if res is not True:
            return "Nginx配置文件错误，无法开始轮询配置"
        ng_data = public.readFile(ng_file)
        if not isinstance(ng_data, str):
            return "Nginx配置文件读取错误，无法开始轮询配置"

        old_proxy_res = None
        for tmp_res in re.finditer(r"\s*proxy_pass\s+(?P<url>\S+)\s*;", ng_data, re.M):
            url: Url = parse_url(tmp_res.group("url"))
            if url.hostname in ("127.0.0.1", "localhost", "0.0.0.0") and url.port in self.old_listen_port():
                old_proxy_res = tmp_res
                self.proxy_data["scheme"] = url.scheme
                self.proxy_data["old_port"] = url.port
        if not old_proxy_res:
            return "未找到原实例的代理配置"

        upstream_file = "/www/server/panel/vhost/nginx/java_{}_upstream.conf".format(self.project_name)
        public.writeFile(upstream_file, """
upstream {}_backend {{
    server 127.0.0.1:{};
    server 127.0.0.1:{};
}}
""".format(self.project_name, self.proxy_data["old_port"], self.new_port))

        new_config = ng_data.replace(old_proxy_res.group(), "\n        proxy_pass {}://{}_backend;".format(
            self.proxy_data["scheme"], self.project_name))

        public.writeFile(ng_file, new_config)

        res = public.checkWebConfig()
        if res is not True:
            public.writeFile(ng_file, ng_data)
            return "Nginx配置文件错误，无法开始轮询配置"
        else:
            public.serviceReload()

    def wait_time(self):
        self.keep_status[2]["status"] = -1
        if not self.run_time:
            self.run_time = 10 * 60
        for i in range(self.run_time):
            if self.end:
                return "退出操作"
            self.keep_status[2]["msg"] = "已进入轮询测试等待"
            if i > 0:
                self.keep_status[2]["msg"] = "已进入轮询测试等待，已等待{}s, 共需等待{}s".format(i, self.run_time)
            time.sleep(1)
            if not self.new_pro.is_running():
                return "新示例已退出，无法继续执行操作"
        return None

    def select_new_or_old(self, option: str):
        if option == "use_new":
            self.keep_status[2]["status"] = 1
            self.keep_status[2]["msg"] = "已跳过等待时间，使用新实例运行"
            res = self.stop_old()
            public.M("sites").where("id=?", (self.old_project_data["id"],)).update(
                {"project_config": json.dumps(self.new_project_config)}
            )
            self.keep_status[3]["status"] = 1
            self.keep_status[3]["msg"] = res if res else "停止旧实例成功，项目更新已结束"
            return {"status": False if res else True, "msg": res if res else "停止旧实例成功，项目更新已结束"}

        self.keep_status[2]["status"] = 1
        self.keep_status[2]["msg"] = "已跳过等待时间，使用原实例运行"
        self.keep_status[3]["name"] = "停止新实例"
        self.keep_status[3]["status"] = 1
        ng_file = "/www/server/panel/vhost/nginx/java_{}.conf".format(self.project_name)
        ng_data = public.readFile(ng_file)
        if not isinstance(ng_data, str):
            return {"status": False, "msg": "Nginx配置文件读取错误，无法取消轮询并使用原实例"}
        res = public.checkWebConfig()
        if res is not True:
            return {"status": False, "msg": "Nginx配置文件错误，无法取消轮询并使用原实例"}

        upstream_file = "/www/server/panel/vhost/nginx/java_{}_upstream.conf".format(self.project_name)
        new_config = ng_data.replace(
            "{}_backend".format(self.project_name),
            "127.0.0.1:{}".format(self.proxy_data["old_port"])
        )
        public.writeFile(ng_file, new_config)
        res = public.checkWebConfig()
        if res is not True:
            public.writeFile(ng_file, ng_data)
            return {"status": False, "msg": "Nginx配置文件设置错误，无法取消轮询并使用原实例"}
        else:
            os.remove(upstream_file)
            public.serviceReload()
            self.stop_new()

            return {"status": True, "msg": "停止新实例成功，项目更新已结束"}

    def stop_old(self):
        self.keep_status[3]["status"] = -1
        ng_file = "/www/server/panel/vhost/nginx/java_{}.conf".format(self.project_name)
        ng_data = public.readFile(ng_file)
        if not isinstance(ng_data, str):
            return "Nginx配置文件读取错误，无法取消轮询，使用新实例"

        res = public.checkWebConfig()
        if res is not True:
            return "Nginx配置文件错误，无法取消轮询，使用新实例"

        old_proxy_res = None
        for tmp_res in re.finditer(r"\s*proxy_pass\s+(?P<url>\S+)\s*;", ng_data, re.M):
            if tmp_res.group("url").find("{}_backend".format(self.project_name)):
                old_proxy_res = tmp_res

        if not old_proxy_res:
            return "未找到轮询的代理配置"

        upstream_file = "/www/server/panel/vhost/nginx/java_{}_upstream.conf".format(self.project_name)
        if os.path.isfile(upstream_file):
            os.remove(upstream_file)

        new_config = ng_data.replace(old_proxy_res.group(), "\n        proxy_pass {}://127.0.0.1:{};".format(
            self.proxy_data["scheme"], self.new_port))

        public.writeFile(ng_file, new_config)

        res = public.checkWebConfig()
        if res is not True:
            public.writeFile(ng_file, ng_data)
            return "Nginx配置文件错误，无法结束轮询配置"
        else:
            public.serviceReload()

        old_server_name = "spring_" + self.project_name + self.old_project_config.get("server_name_suffix", "")
        RealServer().server_admin(old_server_name, "stop")
        RealServer().del_daemon(old_server_name)
        if self.old_pro and self.old_pro.is_running():
            self.old_pro.kill()

        return None

    def keep_update(self):
        pid_file = "{}/{}.pid".format(self.keep_path, self.project_name)
        log_file = "{}/{}.log".format(self.keep_path, self.project_name)
        pid = os.getpid()
        public.writeFile(pid_file, str(pid))
        if os.path.exists(log_file):
            os.remove(log_file)

        project_data = self.j_project.get_project_find(self.project_name)
        if not project_data:
            return json_response(False, msg="项目不存在")

        project_config = project_data['project_config']
        self.old_project_data = project_data
        self.old_project_config = project_config
        self.new_project_config = copy.deepcopy(project_config)

        try:
            self.old_pro = psutil.Process(self.j_project.get_project_pid(project_data))
        except:
            pass
        if not self.old_pro:
            return json_response(False, msg="项目未启动")

        self.end = False
        self.keep_status = [
            {
                "name": "启动新实例",
                "status": 0,
                "msg": "",
            },
            {
                "name": "设置Nginx轮询",
                "status": 0,
                "msg": "",
            },
            {
                "name": "等待并检查新实例",
                "status": 0,
                "msg": "",
            },
            {
                "name": "停止旧实例",
                "status": 0,
                "msg": "",
            }
        ]

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        socket_file = "{}/{}.socket".format(self.keep_path, self.project_name)
        # 清理旧的socket文件，如果存在
        if os.path.exists(socket_file):
            os.remove(socket_file)

        # 设置为非阻塞
        sock.bind(socket_file)
        sock.setblocking(False)  # 0表示非阻塞，1表示阻塞
        sock.listen(2)

        update_run_task = Thread(target=self.run_task)
        update_run_task.start()

        while True:
            if not update_run_task.is_alive():
                public.writeFile(log_file, json.dumps(self.keep_status))
                break

            try:
                # 读取客户端发送的数据
                conn, _ = sock.accept()
                data = conn.recv(1024)
            except socket.error as e:
                if e.errno not in (errno.EAGAIN, errno.EWOULDBLOCK):
                    raise e
                time.sleep(0.1)
                continue

            if not data:
                time.sleep(0.1)
                continue

            # 打印接收到的数据
            print("Received:", data.decode())
            data_str = data.decode()
            if data_str == "stop_new":
                if self.keep_status[0]["status"] == -1:
                    self.end = True
                    update_run_task.join()
                    public.writeFile(log_file, json.dumps(self.keep_status))
                    conn.sendall(json.dumps({
                        "status": True,
                        "msg": "已关闭更新任务，并停止新实例"
                    }).encode())
                    break
                else:
                    conn.sendall(json.dumps({
                        "status": False,
                        "msg": "新实例启动完成，已加入轮询，无法继续执行该操作"
                    }).encode())
            elif data_str == "status":
                conn.sendall(json.dumps(self.keep_status).encode())
            elif data_str in ("use_new", "use_old"):
                if self.keep_status[2]["status"] != -1:
                    conn.sendall(json.dumps({
                        "status": False,
                        "msg": "已超过轮询等待时间，无法执行该操作"
                    }).encode())
                else:
                    self.end = True
                    update_run_task.join()
                    public.writeFile(log_file, json.dumps(self.keep_status))
                    res = self.select_new_or_old(data_str)
                    conn.sendall(json.dumps(res).encode())

            time.sleep(0.1)

        # 关闭服务器端socket
        sock.close()
        # 清理旧的socket文件，如果存在
        if os.path.exists(socket_file):
            os.remove(socket_file)

    def get_keep_status(self):
        try:
            log_file = "{}/{}.log".format(self.keep_path, self.project_name)
            pid_file = "{}/{}.pid".format(self.keep_path, self.project_name)
            log_data = public.readFile(log_file)
            data = None
            if isinstance(log_data, str):
                try:
                    data = json.loads(log_data)
                except:
                    pass

            if data:
                return json_response(True, data={
                    "running": False,
                    "keep_msg": data
                })

            pid_data = public.readFile(pid_file)
            er_msg = "没有正在进行的更新任务"
            if not isinstance(pid_data, str):
                return json_response(False, msg=er_msg)
            try:
                pid = int(pid_data)
                if not psutil.pid_exists(pid):
                    return json_response(False, msg=er_msg)
            except:
                return json_response(False, msg=er_msg)

            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                sock.connect("{}/{}.socket".format(self.keep_path, self.project_name))
            except Exception:
                public.print_log(public.get_error_info())
                return json_response(False, msg="链接错误请尝试强制停止更新")
            data = b"status"
            sock.sendall(data)

            # 接收响应
            sock.settimeout(1)
            response = sock.recv(1024 * 2)
            sock.close()
            try:
                data = json.loads(response.decode())
            except:
                public.print_log(public.get_error_info())
                return json_response(False, msg="链接错误请尝试强制停止更新")
            return json_response(True, data={
                "running": True,
                "keep_msg": data
            })
        except:
            public.print_log(public.get_error_info())
            return json_response(False, msg="链接错误请尝试强制停止更新")

    def keep_option(self, option: str) -> dict:
        try:
            pid_file = "{}/{}.pid".format(self.keep_path, self.project_name)
            pid_data = public.readFile(pid_file)
            er_msg = "没有正在进行的更新任务, 无法执行操作"
            if not isinstance(pid_data, str) or pid_data == "0":
                return json_response(False, msg=er_msg)
            try:
                pid = int(pid_data)
                if not psutil.pid_exists(pid):
                    return json_response(False, msg=er_msg)
            except:
                return json_response(False, msg=er_msg)

            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                sock.connect("{}/{}.socket".format(self.keep_path, self.project_name))
            except Exception:
                return json_response(False, msg="链接错误,无法执行操作，请尝试强制停止更新")

            sock.sendall(option.encode())

            # 接收响应
            sock.settimeout(10)
            response = sock.recv(1024)
            sock.close()
            try:
                data = json.loads(response.decode())
            except:
                public.print_log(public.get_error_info())
                return json_response(False, msg="链接错误请尝试强制停止更新")
            if isinstance(data, dict):
                return json_response(data['status'], msg=data['msg'])
            else:
                return json_response(False, msg="链接错误请尝试强制停止更新")
        except:
            public.print_log(public.get_error_info())
            return json_response(False, msg="链接错误请尝试强制停止更新")


if __name__ == '__main__':
    def run_main(project_name: str, new_jar: str, new_port: int, run_time: int,):
        pu = ProjectUpdate(project_name, new_jar=new_jar, run_time=run_time, new_port=new_port)
        pu.keep_update()

    if len(sys.argv) == 5:
        run_main(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))

