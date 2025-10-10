import json
import os
import threading
import queue
import time
import traceback
from typing import List, Dict, Callable, Any, Union, Optional

from mod.base.ssh_executor import SSHExecutor
from mod.project.node.dbutil import ServerNodeDB, CommandTask, CommandLog, TaskFlowsDB, TransferTask
from mod.project.node.dbutil import TaskFlowsDB
from mod.project.node.nodeutil import LPanelNode, ServerNode, SSHApi
from mod.project.node.filetransfer.socket_server import StatusServer, StatusClient, register_cleanup

from .command_task import CMDTask
from .file_task import FiletransferTask, NodeFiletransferTask

_SOCKET_FILE_DIR = "/tmp/flow_task"
if not os.path.exists(_SOCKET_FILE_DIR):
    os.mkdir(_SOCKET_FILE_DIR)



class FlowTask:

    def __init__(self, flow_id: int, step_idx: int=0, sub_id: int=0):
        self._fdb = TaskFlowsDB()
        self.flow = self._fdb.Flow.get_byid(flow_id)
        if not self.flow:
            raise RuntimeError("任务不存在")

        self.steps: List[Union[CommandTask, TransferTask]] = [
            *self._fdb.CommandTask.query("flow_id = ?", (flow_id,)),
            *self._fdb.TransferTask.query("flow_id = ?", (flow_id,))
        ]

        self.steps.sort(key=lambda x: x.step_index, reverse=False)

        if not self.steps:
            raise RuntimeError("任务内容不存在")
        self.now_idx = 1
        self.run_when_error = False
        if self.flow.strategy.get("run_when_error", False):
            self.run_when_error = True

        self.status_server = StatusServer(self.get_status, (_SOCKET_FILE_DIR + "/flow_task_" + str(flow_id)))

    def get_status(self, init: bool = False):
        flow_data = self.flow.to_dict()
        flow_data["steps"] = [x.to_show_data() for x in self.steps]
        flow_data["now_idx"] = self.now_idx
        return flow_data

    def start_status_server(self):
        t = threading.Thread(target=self.status_server.start_server, args=(), daemon=True)
        t.start()
        register_cleanup(self.status_server)

    def update_status(self, update_data: Dict):
        self.status_server.update_status(update_data)

    def _run(self) -> bool:
        def call_log(log_data):
            self.update_status(log_data)

        all_status = True  # 任务全部成功
        for step in self.steps:
            if isinstance(step, CommandTask):
                if step.status != 2: # 跳过已完成的
                    has_err = self.run_cmd_task(step, call_log)
                    all_status = all_status and not has_err
                    if has_err and not self.run_when_error:
                        return False
            elif isinstance(step, TransferTask):
                if step.status != 2: # 跳过已完成的
                    has_err = self.run_transfer_task(step, call_log)
                    all_status = all_status and not has_err
                    if has_err and not self.run_when_error:
                        return False
            self.now_idx += 1
        return all_status

    def start(self):
        self.start_status_server()

        self.flow.status = "running"
        self._fdb.Flow.update(self.flow)
        all_status = self._run()
        self.flow.status = "complete" if all_status else "error"
        self._fdb.Flow.update(self.flow)

        self.status_server.stop()
        return

    @staticmethod
    def run_cmd_task(task: CommandTask, call_log: Callable[[Any], None]) -> bool:
        task = CMDTask(task, 0, call_log)
        task.start()
        return task.status_dict["error"] > 0

    @staticmethod
    def run_transfer_task(task: TransferTask, call_log: Callable[[Any], None]) -> Optional[str]:
        if task.src_node_task_id != 0:
            task = NodeFiletransferTask(task, call_log)
            task.start()
        else:
            task = FiletransferTask(task, call_log)
            task.start()
            return task.status_dict["error"] > 0


def flow_running_log(task_id: int, call_log:  Callable[[Union[str,dict]], None], timeout:float = 3.0) -> str:
    socket_file = _SOCKET_FILE_DIR + "/flow_task_" + str(task_id)
    while not os.path.exists(socket_file):
        if timeout <= 0:
            return "任务启动超时"
        timeout -= 0.05
        time.sleep(0.05)

    s_client = StatusClient(socket_file, callback=call_log)
    s_client.connect()
    s_client.wait_receive()
    return  ""

def flow_useful_version(ver: str):
    # # todo: 临时处理, 上线前确认最新版本号检查逻辑
    # return True
    try:
        ver_list = [int(i) for i in ver.split(".")]
        if ver_list[0] > 11:
            return True
        if ver_list[0] == 11 and ver_list[1] >= 1:
            return True
    except:
        pass
    return False