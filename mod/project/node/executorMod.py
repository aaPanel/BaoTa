import json
import os.path
import threading
import time
import psutil
import traceback
from datetime import datetime
from typing import List, Dict, Optional, Tuple, MutableMapping, Union

import simple_websocket
from mod.base import json_response, list_args
from mod.project.node.nodeutil import ServerNode, LocalNode, LPanelNode, SSHApi
from mod.project.node.dbutil import Script, CommandLog, TaskFlowsDB, CommandTask, ServerNodeDB, TransferTask, \
    ServerMonitorRepo, Flow
from mod.project.node.task_flow import self_file_running_log, flow_running_log, flow_useful_version

import public


class main:
    next_flow_tip_name = "user_next_flow_tip"

    @staticmethod
    def create_script(get):
        e_db = TaskFlowsDB()
        err = Script.check(get)
        if err:
            return json_response(status=False, msg=err)
        s = Script.from_dict(get)
        # 查重
        if e_db.Script.find("name = ?", (s.name,)):
            return json_response(status=False, msg="脚本名称已存在")
        err = e_db.Script.create(s)
        if isinstance(err, str):
            return json_response(status=False, msg=err)
        return json_response(status=True, msg="创建成功", data=s.to_dict())

    @staticmethod
    def modify_script(get):
        e_db = TaskFlowsDB()
        err = Script.check(get)
        if err:
            return json_response(status=False, msg=err)
        s = Script.from_dict(get)
        if not s.id:
            return json_response(status=False, msg="脚本ID不能为空")
        if not e_db.Script.find("id = ?", (s.id,)):
            return json_response(status=False, msg="脚本不存在")
        err = e_db.Script.update(s)
        if err:
            return json_response(status=False, msg=err)
        return json_response(status=True, msg="修改成功", data=s.to_dict())

    @staticmethod
    def delete_script(get):
        e_db = TaskFlowsDB()
        if not get.id:
            return json_response(status=False, msg="脚本ID不能为空")
        try:
            del_id = int(get.id)
        except:
            return json_response(status=False, msg="脚本ID格式错误")

        e_db.Script.delete(del_id)
        return json_response(status=True, msg="删除成功")

    @staticmethod
    def get_script_list(get):
        page_num = max(int(get.get('p/d', 1)), 1)
        limit = max(int(get.get('limit/d', 16)), 1)
        search = get.get('search', "").strip()
        script_type = get.get('script_type/s', "all")
        if not script_type in ["all", "python", "shell"]:
            script_type = "all"

        where_list, params = [], []
        if search:
            where_list.append("(name like ? or content like ? or description like ?)")
            params.append("%{}%".format(search))
            params.append("%{}%".format(search))
            params.append("%{}%".format(search))

        if script_type != "all":
            where_list.append("script_type = ?")
            params.append(script_type)

        where = " and ".join(where_list)
        e_db = TaskFlowsDB()
        data_list = e_db.Script.query_page(where, (*params,), page_num=page_num, limit=limit)
        count = e_db.Script.count(where, params)
        page = public.get_page(count, page_num, limit)
        page["data"] = [i.to_dict() for i in data_list]
        return page

    @staticmethod
    def bath_delete_script(get):
        script_ids = list_args(get, 'script_ids')
        try:
            script_ids = [int(i) for i in script_ids]
        except:
            return json_response(status=False, msg="脚本ID格式错误")
        if not script_ids:
            return json_response(status=False, msg="脚本ID不能为空")

        e_db = TaskFlowsDB()
        err = e_db.Script.delete(script_ids)
        if err:
            return json_response(status=False, msg=err)
        return json_response(status=True, msg="删除成功")

    @staticmethod
    def create_task(get):
        node_ids = list_args(get, 'node_ids')
        if not node_ids:
            return json_response(status=False, msg="节点ID不能为空")
        try:
            node_ids = [int(i) for i in node_ids]
        except:
            return json_response(status=False, msg="节点ID格式错误")

        e_db = TaskFlowsDB()
        script_id = get.get('script_id/d', 0)
        if script_id:
            s = e_db.Script.find("id = ?", (script_id,))
            if not s:
                return json_response(status=False, msg="脚本不存在")

        elif get.get("script_content/s", "").strip():
            if not (get.get("script_type", "").strip() in ("python", "shell")):
                return json_response(status=False, msg="脚本类型错误")
            s = Script("", get.get("script_type", "").strip(), content=get.get("script_content", "").strip())
            s.id = 0
        else:
            return json_response(status=False, msg="请选择脚本")

        nodes_db = ServerNodeDB()
        nodes = []
        timestamp = int(datetime.now().timestamp())
        for i in node_ids:
            n = nodes_db.get_node_by_id(i)
            if not n:
                return json_response(status=False, msg="节点id为【{}】的节点不存在".format(i))
            n["ssh_conf"] = json.loads(n["ssh_conf"])
            if not n["ssh_conf"]:
                return json_response(status=False, msg="节点id为【{}】的节点未配置ssh信息，无法进行指令分发".format(i))
            n["log_name"] = "{}_{}_{}.log".format(public.md5(s.content)[::2], timestamp, n['remarks'])
            nodes.append(n)

        e_task = CommandTask(
            script_id=s.id,
            script_content=s.content,
            script_type=s.script_type,
            flow_id=0,
            step_index=0,
        )
        command_task_id = e_db.CommandTask.create(e_task)
        e_task.id = command_task_id
        if not isinstance(command_task_id, int) or command_task_id <= 0:
            return json_response(status=False, msg="创建任务失败:" + command_task_id)

        log_list = []
        for i in nodes:
            elog = CommandLog(
                command_task_id=command_task_id,
                server_id=i["id"],
                ssh_host=i["ssh_conf"]["host"],
                status=0,
                log_name=i["log_name"],
            )
            elog.create_log()
            log_list.append(elog)

        last_id = e_db.CommandLog.create(log_list)
        if not isinstance(last_id, int) or last_id <= 0:
            for i in log_list:
                i.remove_log()
            return json_response(status=False, msg="创建日志失败:" + last_id)

        script_py = "{}/script/node_command_executor.py command".format(public.get_panel_path())
        res = public.ExecShell("nohup {} {} {} > /dev/null 2>&1 &".format(
            public.get_python_bin(), script_py, command_task_id)
        )

        data_dict = e_task.to_dict()
        data_dict["log_list"] = [i.to_dict() for i in log_list]
        data_dict["task_id"] = command_task_id
        return json_response(status=True, msg="创建成功", data=data_dict)

    @staticmethod
    def get_server_info(server_id: int, server_cache) -> dict:
        server_info = server_cache.get(server_id)
        if not server_info:
            server = ServerNodeDB().get_node_by_id(server_id)
            if not server:
                server_cache[server_id] = {}
            else:
                server_cache[server_id] = server
            return server_cache[server_id]
        else:
            return server_info

    @classmethod
    def get_task_list(cls, get):
        page_num = max(int(get.get('p/d', 1)), 1)
        limit = max(int(get.get('limit/d', 16)), 1)
        script_type = get.get('script_type/s', "all")
        if not script_type in ["all", "python", "shell"]:
            script_type = "all"
        search = get.get('search', "").strip()

        e_db = TaskFlowsDB()
        count, tasks = e_db.CommandTask.query_tasks(
            page=page_num, size=limit, script_type=script_type, search=search
        )

        res = []
        server_cache: Dict[int, Dict] = {}
        for i in tasks:
            task_dict = i.to_dict()
            log_list = e_db.CommandLog.query("command_task_id = ?", (i.id,))
            task_dict["log_list"] = []
            if i.script_id > 0:
                s = e_db.Script.find("id = ?", (i.script_id,))
                if s:
                    task_dict["script_name"] = s.name
            else:
                task_dict["script_name"] = "-"

            for j in log_list:
                tmp = j.to_dict()
                tmp["server_name"] = cls.get_server_info(j.server_id, server_cache).get("remarks")
                task_dict["log_list"].append(tmp)

            res.append(task_dict)

        page = public.get_page(count, page_num, limit)
        page["data"] = res
        return page

    @classmethod
    def get_task_info(cls, get):
        task_id = get.get('task_id/d', 0)
        if not task_id:
            return json_response(status=False, msg="任务ID不能为空")

        e_db = TaskFlowsDB()
        task = e_db.CommandTask.find("id = ?", (task_id,))
        if not task:
            return json_response(status=False, msg="任务不存在")

        task_dict = task.to_dict()
        task_dict["log_list"] = []
        server_cache = {}
        log_list = e_db.CommandLog.query("command_task_id = ?", (task_id,))
        for i in log_list:
            tmp = i.to_dict()
            if i.status != 0:
                tmp["log"] = i.get_log()
            tmp["server_name"] = cls.get_server_info(i.server_id, server_cache).get("remarks", "")
            task_dict["log_list"].append(tmp)

        return json_response(status=True, msg="获取成功", data=task_dict)

    @staticmethod
    def delete_task(get):
        e_db = TaskFlowsDB()
        task_id = get.get('task_id/d', 0)
        if not task_id:
            return json_response(status=False, msg="任务ID不能为空")

        task = e_db.CommandTask.find("id = ?", (task_id,))
        if not task:
            return json_response(status=False, msg="任务不存在")

        pid_file = "{}/logs/executor_log/{}.pid".format(public.get_panel_path(), task_id)
        if os.path.exists(pid_file):
            pid: str = public.readFile(pid_file)
            if pid and pid.isdigit():
                public.ExecShell("kill -9 {}".format(pid))
                os.remove(pid_file)

        log_list = e_db.CommandLog.query("command_task_id = ?", (task_id,))
        for i in log_list:
            i.remove_log()
            e_db.CommandLog.delete(i.id)

        e_db.CommandTask.delete(task_id)
        return json_response(status=True, msg="删除成功")

    @staticmethod
    def batch_delete_task(get):
        task_ids: List[int] = list_args(get, "task_ids")
        if not task_ids:
            return json_response(status=False, msg="请选择要删除的任务")
        task_ids = [int(i) for i in task_ids]
        e_db = TaskFlowsDB()
        task_list = e_db.CommandTask.query("id IN ({})".format(",".join(["?"] * len(task_ids))), (*task_ids,))
        if not task_list:
            return json_response(status=False, msg="任务不存在")
        for i in task_list:
            pid_file = "{}/logs/executor_log/{}.pid".format(public.get_panel_path(), i.id)
            if os.path.exists(pid_file):
                pid: str = public.readFile(pid_file)
                if pid and pid.isdigit():
                    public.ExecShell("kill -9 {}".format(pid))
                    os.remove(pid_file)

            log_list = e_db.CommandLog.query("command_task_id = ?", (i.id,))
            for j in log_list:
                j.remove_log()
                e_db.CommandLog.delete(j.id)
            e_db.CommandTask.delete(i.id)

        return json_response(status=True, msg="删除成功")

    @staticmethod
    def retry_task(get):
        task_id = get.get('task_id/d', 0)
        if not task_id:
            return json_response(status=False, msg="任务ID不能为空")

        log_id = get.get('log_id/d', 0)
        if not log_id:
            return json_response(status=False, msg="日志ID不能为空")

        e_db = TaskFlowsDB()
        log = e_db.CommandLog.find("id = ? AND command_task_id = ?", (log_id, task_id))
        if not log:
            return json_response(status=False, msg="日志不存在")

        log.create_log()
        log.status = 0
        e_db.CommandLog.update(log)
        script_py = "{}/script/node_command_executor.py command".format(public.get_panel_path())
        public.ExecShell("nohup {} {} {} {} > /dev/null 2>&1 &".format(
            public.get_python_bin(), script_py, task_id, log_id)
        )
        return json_response(status=True, msg="重试开始")

    @staticmethod
    def node_create_transfer_task(get):
        try:
            transfer_task_data = json.loads(get.get('transfer_task_data', "{}"))
            if not transfer_task_data:
                return json_response(status=False, msg="参数错误")
        except Exception as e:
            return json_response(status=False, msg="参数错误")

        transfer_task_data["flow_id"] = 0
        transfer_task_data["step_index"] = 0
        transfer_task_data["src_node"] = {"name": "local"}
        transfer_task_data["src_node_task_id"] = 0

        fdb = TaskFlowsDB()
        tt = TransferTask.from_dict(transfer_task_data)
        task_id = fdb.TransferTask.create(tt)
        if not task_id:
            return json_response(status=False, msg="创建任务失败")
        return json_response(status=True, msg="创建成功", data={"task_id": task_id})

    @classmethod
    def node_transferfile_status_history(cls, get):
        task_id = get.get('task_id/d', 0)
        only_error = get.get('only_error/d', 1)
        if not task_id:
            return json_response(status=False, msg="任务ID不能为空")
        fdb = TaskFlowsDB()
        ret = fdb.history_transferfile_task(task_id, only_error=only_error==1)
        fdb.close()
        return json_response(status=True, msg="获取成功", data=ret)

    @classmethod
    def node_proxy_transferfile_status(cls, get):
        ws: simple_websocket.Server = getattr(get, '_ws', None)
        if not ws:
            return json_response(False, "请使用 WebSocket 连接")

        task_id = get.get('task_id/d', 0)
        if not task_id:
            ws.send(json.dumps({"type": "end", "msg": "任务ID不能为空"}))
            ws.send("{}")
            return

        fdb = TaskFlowsDB()
        task = fdb.TransferTask.get_byid(task_id)
        if not task:
            ws.send(json.dumps({"type": "end", "msg": "任务不存在"}))
            ws.send("{}")
            return
        if task.status in (0, 3):  # 初次执行 或 出错后再次尝试
            pid = cls._start_task("file", task_id)
        elif task.status == 2: # 运行成功了， 获取历史数据并返回
            ret = fdb.history_transferfile_task(task_id)
            ws.send(json.dumps({"type": "end", "data": ret}))
            ws.send("{}")
            fdb.close()
            return
        else:  # 还在运行中
            pid_file = "{}/logs/executor_log/file_{}_0.pid".format(public.get_panel_path(), task_id)
            if os.path.exists(pid_file):
                pid = int(public.readFile(pid_file))
            else:
                pid = None

        if not pid:  # 运行失败， 返回数据库信息
            ret = fdb.history_transferfile_task(task_id)
            ws.send(json.dumps({"type": "end", "data": ret}))
            fdb.close()
            ws.send("{}")
            return

        def send_status(soc_data: dict):
            ws.send(json.dumps({"type": "status", "data": soc_data}))

        err = self_file_running_log(task_id, send_status)
        if err:
            ws.send(json.dumps({"type": "error", "msg": err}))

        ret = fdb.history_transferfile_task(task_id)
        ws.send(json.dumps({"type": "end", "data": ret}))
        fdb.close()
        ws.send("{}")  # 告诉接收端，数据传输已经结束
        return

    def run_flow_task(self, get):
        ws: simple_websocket.Server = getattr(get, '_ws', None)
        if not ws:
            return json_response(False, "请使用 WebSocket 连接")

        public.set_module_logs("nodes_flow_task", "run_flow_task")
        node_ids = list_args(get, 'node_ids')
        if not node_ids:
            ws.send(json.dumps({"type": "error", "msg": "节点ID不能为空"}))
            return
        try:
            node_ids = [int(i) for i in node_ids]
        except:
            ws.send(json.dumps({"type": "error", "msg": "节点ID格式错误"}))
            return

        try:
            flow_data = get.get('flow_data', '[]')
            if isinstance(flow_data, str):
                flow_data = json.loads(flow_data)
            elif isinstance(flow_data, (list, tuple)):
                pass
            else:
                raise
        except:
            ws.send(json.dumps({"type": "error", "msg": "流程数据格式错误"}))
            return

        strategy = {}
        if "run_when_error" in get and get.run_when_error in ("1", "true", 1, True):
            strategy["run_when_error"] = True

        has_cmd_task = False
        data_src_node = []
        for i in flow_data:
            if i["task_type"] == "command":
                has_cmd_task = True
            elif i["task_type"] == "file":
                data_src_node.append(i["src_node_id"])

        nodes_db = ServerNodeDB()
        used_nodes, target_nodes = [], []
        srv_cache = ServerMonitorRepo()
        for i in set(node_ids + data_src_node):
            n = nodes_db.get_node_by_id(i)
            if not n:
                ws.send(json.dumps({"type": "error", "msg": "节点id为【{}】的节点不存在".format(i)}))
                return
            n["ssh_conf"] = json.loads(n["ssh_conf"])
            if has_cmd_task and n["id"] in node_ids and not n["ssh_conf"]:
                ws.send(json.dumps({"type": "error", "msg": "节点【{}】的节点未启用SSH".format(n["remarks"])}))
                return
            if n["id"] in data_src_node:
                is_local = n["app_key"] == n["api_key"] == "local"
                if (not n["app_key"] and not n["api_key"]) or n["lpver"]:  # 1panel面板或者 仅有ssh配置的节点无法作为数据源
                    ws.send(json.dumps(
                        {"type": "error", "msg": "节点【{}】不是宝塔节点，无法作为数据源".format(n["remarks"])}))
                    return
                if not is_local:
                    # 检查节点版本号
                    tmp = srv_cache.get_server_status(n["id"])
                    if not tmp or not flow_useful_version(tmp["version"]):
                        ws.send(
                            json.dumps({"type": "error", "msg": "节点【{}】版本过低，请升级节点".format(n["remarks"])}))
                        return

            used_nodes.append(n)
            if n["id"] in node_ids:
                target_nodes.append(n)

        fdb = TaskFlowsDB()
        flow, err = fdb.create_flow(used_nodes, target_nodes, strategy, flow_data)
        if not flow:
            ws.send(json.dumps({"type": "error", "msg": err}))
            return
        fdb.close()

        pid = self._start_task("flow", flow.id)
        if not pid:
            ws.send(json.dumps({"type": "error", "msg": "任务启动失败"}))
            return

        def update_status(data: dict):
            ws.send(json.dumps({"type": "status", "data": data}))

        err = flow_running_log(flow.id, update_status)
        if err:
            ws.send(json.dumps({"type": "error", "msg": err}))

        ws.send(json.dumps({"type": "end", "msg": "任务结束"}))
        return

    @classmethod
    def _start_task(cls, task_type: str, task_id: int) -> Optional[int]:
        pid_file = "{}/logs/executor_log/{}_{}_0.pid".format(public.get_panel_path(), task_type, task_id)
        if os.path.exists(pid_file):
            pid = int(public.readFile(pid_file))
            if psutil.pid_exists(pid):
                return pid

        script_py = "{}/script/node_command_executor.py".format(public.get_panel_path())
        public.ExecShell("nohup {} {} {} {} > /dev/null 2>&1 &".format(
            public.get_python_bin(), script_py, task_type, task_id)
        )
        for i in range(60):
            if os.path.exists(pid_file):
                pid = int(public.readFile(pid_file))
                if psutil.pid_exists(pid):
                    return pid
            time.sleep(0.05)
        return None

    @classmethod
    def flow_task_status(cls, get):
        ws: simple_websocket.Server = getattr(get, '_ws', None)
        if not ws:
            return json_response(False, "请使用 WebSocket 连接")

        fdb = TaskFlowsDB()
        flow = fdb.Flow.last(order_by="id DESC")
        if flow and flow.status == "running":
            flow_data = fdb.history_flow_task(flow)
            ws.send(json.dumps({"type": "status", "data": flow_data}))
            for t in flow.steps:
                t: Union[CommandTask, TransferTask]
                src_node = getattr(t, "src_node", {})
                is_local_src = src_node.get("address", None) is None
                if not src_node:
                    task_data = fdb.history_command_task(t.id)
                elif is_local_src:
                    task_data = fdb.history_transferfile_task(t.id)
                else:
                    srv = ServerNode(src_node["address"], src_node["api_key"], src_node["app_key"], src_node["remarks"])
                    srv_data = srv.node_transferfile_status_history(t.src_node_task_id)
                    if srv_data["status"]:
                        task_data = srv_data["data"]
                    else:
                        task_data = {
                            "task_id": t.id, "task_type": "file",
                            "count": 0, "complete": 0, "error": 0, "data": []
                        }
                ws.send(json.dumps({"type": "status", "data": task_data}))

            err = flow_running_log(flow.id, lambda x: ws.send(json.dumps({"type": "status", "data": x})))
            if err:
                ws.send(json.dumps({"type": "error", "msg": err}))

            ws.send(json.dumps({"type": "end", "msg": "任务结束"}))
            return
        else:
            if not flow:
                ws.send(json.dumps({"type": "no_flow", "msg": "没有任务"}))  # 没有任务
                return
            flow_data = fdb.history_flow_task(flow.id)
            ws.send(json.dumps({"type": "end",  "last_flow": flow_data}))
            return

    @classmethod
    def next_flow_tip(cls, get):
        return json_response(status=True, msg="设置成功")

    @staticmethod
    def get_flow_info(get):
        flow_id = get.get("flow_id/d", 0)
        fdb = TaskFlowsDB()
        flow = fdb.Flow.get_byid(flow_id)
        if not flow:
            return json_response(status=False, msg="任务不存在")

        flow_data = fdb.history_flow_task(flow.id)
        return json_response(status=True, data=flow_data)

    @staticmethod
    def get_command_task_info(get):
        task_id = get.get("task_id/d", 0)
        fdb = TaskFlowsDB()
        task = fdb.CommandTask.get_byid(task_id)
        if not task:
            return json_response(status=False, msg="任务不存在")
        return json_response(status=True, data=fdb.history_command_task(task.id, only_error=False))

    @staticmethod
    def get_transferfile_task_info(get):
        task_id = get.get("task_id/d", 0)
        fdb = TaskFlowsDB()
        task = fdb.TransferTask.get_byid(task_id)
        if not task:
            return json_response(status=False, msg="任务不存在")

        src_node = task.src_node
        is_local_src = task.src_node.get("address", None) is None
        if is_local_src:
            return json_response(status=True, data=fdb.history_transferfile_task(task.id, only_error=False))
        else:
            srv = ServerNode(src_node["address"], src_node["api_key"], src_node["app_key"], src_node["name"])
            srv_data = srv.node_transferfile_status_history(task.src_node_task_id, only_error=False)
            if srv_data["status"]:
                task_data = srv_data["data"]
            else:
                task_data = {
                    "task_id": task.id, "task_type": "file",
                    "count": 0, "complete": 0, "error": 0, "data": []
                }
            return json_response(status=True, data=task_data)

    def flow_task_list(self, get):
        page_num = max(int(get.get('p/d', 1)), 1)
        limit = max(int(get.get('limit/d', 16)), 1)

        fdb = TaskFlowsDB()
        flow_list = fdb.Flow.query_page(page_num=page_num, limit=limit)
        count = fdb.Flow.count()
        res = []
        server_cache: Dict[int, Dict] = {}
        for flow in flow_list:
            tmp_data = fdb.history_flow_task(flow.id)
            tmp_data["server_list"] = [{
                "id": int(i),
                "name": self.get_server_info(int(i), server_cache).get("remarks", ""),
                "server_ip": self.get_server_info(int(i), server_cache).get("server_ip", ""),
            } for i in tmp_data["server_ids"].strip("|").split("|")]
            res.append(tmp_data)

        page = public.get_page(count, page_num, limit)
        page["data"] = res
        return page

    @staticmethod
    def remove_flow(get):
        flow_ids = list_args(get,"flow_ids")
        if not flow_ids:
            return json_response(status=False, msg="请选择要删除的任务")
        fdb = TaskFlowsDB()
        flows = fdb.Flow.query(
            "id IN (%s) AND status NOT IN (?, ?)" % (",".join(["?"]*len(flow_ids))),
            (*flow_ids, "waiting", "running")
        )

        command_tasks = fdb.CommandTask.query(
            "flow_id IN (%s)" % (",".join(["?"]*len(flow_ids))),
            (*flow_ids,)
        )

        command_logs = fdb.CommandLog.query(
            "command_task_id IN (%s)" % (",".join(["?"]*len(flow_ids))),
            (*flow_ids,)
        )

        for log in command_logs:
            try:
                if os.path.exists(log.log_file):
                    os.remove(log.log_file)
            except:
                pass

        fdb.CommandLog.delete([log.id for log in command_logs])
        fdb.CommandTask.delete([task.id for task in command_tasks])
        fdb.Flow.delete([flow.id for flow in flows])

        w, p = "flow_id IN (%s)" % (",".join(["?"]*len(flow_ids))), (*flow_ids,)
        fdb.TransferTask.delete_where(w, p)
        fdb.TransferLog.delete_where(w, p)
        fdb.TransferFile.delete_where(w, p)

        return json_response(status=True, msg="删除成功")

    def retry_flow(self, get):
        ws: simple_websocket.Server = getattr(get, '_ws', None)
        if not ws:
            return json_response(False, "请使用 WebSocket 连接")

        flow_id = get.get("flow_id/d", 0)
        flow = TaskFlowsDB().Flow.get_byid(flow_id)
        if not flow:
            ws.send(json.dumps({"type": "error", "msg": "任务不存在"}))
            return

        if flow.status == "complete":
            ws.send(json.dumps({"type": "error", "msg": "任务已完成, 不能重试"}))
            return

        def call_status(data):
            ws.send(json.dumps({"type": "status", "data": data}))

        pid = self._start_task("flow", flow.id)
        if not pid:
            ws.send(json.dumps({"type": "error", "msg": "任务启动失败"}))
            return

        err = flow_running_log(flow.id, call_status)
        if err:
            ws.send(json.dumps({"type": "error", "msg": err}))

        ws.send(json.dumps({"type": "end", "msg": "任务结束"}))
        return

    @staticmethod
    def stop_flow(get):
        flow_id = get.get("flow_id/d", 0)
        if not flow_id:
            return json_response(status=False, msg="请选择要停止的任务")
        pid_file = "{}/logs/executor_log/flow_{}_0.pid".format(public.get_panel_path(), flow_id)
        if os.path.exists(pid_file):
            pid = int(public.readFile(pid_file))
            if psutil.pid_exists(pid):
                psutil.Process(pid).kill()

            if os.path.exists(pid_file):
                os.remove(pid_file)

            sock_file = "/tmp/flow_task/flow_task_{}".format(flow_id)
            if os.path.exists(sock_file):
                os.remove(sock_file)

        return json_response(status=True, msg="任务已停止")

    @staticmethod
    def file_dstpath_check(get):
        path = get.get("path/s", "")
        node_ids = list_args(get, "node_ids")
        if not path or not node_ids:
            return json_response(status=False, msg="参数错误")

        if path == "/":
            return json_response(status=False, msg="不能上传到根目录")

        nodes_db = ServerNodeDB()
        ret = []

        def check_node(n_data:dict, t_srv: Union[ServerNode, LPanelNode, SSHApi]):
            res = {"id": n_data["id"], "err": "", "remarks": n_data["remarks"]}
            err = t_srv.upload_dir_check(path)
            if err:
                res["err"] = err
            ret.append(res)


        th_list = []
        for i in node_ids:
            n = nodes_db.get_node_by_id(i)
            if not n:
                ret.append({"id": i, "err": "节点不存在"})
            n["ssh_conf"] = json.loads(n["ssh_conf"])
            if n["app_key"] or n["api_key"]:
                srv = ServerNode.new_by_data(n)
            elif n["ssh_conf"]:
                srv = SSHApi(**n["ssh_conf"])
            else:
                ret.append({"id": i, "err": "节点配置错误"})
                continue

            th = threading.Thread(target=check_node, args=(n, srv))
            th.start()
            th_list.append(th)

        for th in th_list:
            th.join()

        return json_response(status=True, data=ret)





