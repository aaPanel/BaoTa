import os
import time
import threading
from datetime import datetime

from .socket_server import StatusServer, StatusClient, register_cleanup
from mod.project.node.dbutil import FileTransferDB, FileTransfer, FileTransferTask
from mod.project.node.nodeutil import ServerNode, LocalNode, LPanelNode
from typing import Optional, Callable, Union


class Filetransfer:
    SOCKET_FILE_DIR = "/tmp/filetransfer"
    if not os.path.exists(SOCKET_FILE_DIR):
        os.mkdir(SOCKET_FILE_DIR)

    def __init__(self, task_id: int):
        self.ft_db = FileTransferDB()
        task_data, err = self.ft_db.get_task(task_id)
        if err is None:
            raise ValueError(err)

        self.task = FileTransferTask.from_dict(task_data)

        file_list = self.ft_db.get_task_file_transfers(task_id)
        if not file_list:
            raise ValueError("task_id:{} file_list is empty".format(task_id))

        self.file_map = {file_data["transfer_id"]: FileTransfer.from_dict(file_data) for file_data in file_list}
        self.file_count = len(self.file_map)
        self.file_complete = sum([1 for file in self.file_map.values() if file.status == "complete"])
        self.file_error = sum([1 for file in self.file_map.values() if file.status == "error"])
        self.count_size = sum([file.file_size for file in self.file_map.values()])
        self.complete_size = sum([file.file_size for file in self.file_map.values() if file.status == "complete"])
        self.current_file_size = 0 # 记录当前文件完成的大小
        self._srv = StatusServer(self.get_task_status, self.SOCKET_FILE_DIR + "/task_" + str(task_id))

        if self.task.task_action == "upload":
            self.sn = LocalNode()
            if self.task.target_node["lpver"]:
                self.dn = LPanelNode(self.task.target_node["address"], self.task.target_node["api_key"],
                                     self.task.target_node["lpver"])
            else:
                self.dn = ServerNode(self.task.target_node["address"], self.task.target_node["api_key"],
                                     self.task.target_node["app_key"])
        else:
            if self.task.source_node["lpver"]:
                self.sn = LPanelNode(self.task.source_node["address"], self.task.source_node["api_key"],
                                     self.task.source_node["lpver"])
            else:
                self.sn = ServerNode(self.task.source_node["address"], self.task.source_node["api_key"],
                                     self.task.source_node["app_key"])
            self.dn = LocalNode()

        self._close_func: Optional[Callable]= None

    def get_task_status(self, init: bool = False) -> dict:
        task_dict = self.task.to_dict()
        task_dict.update({
            "file_count": self.file_count,
            "file_complete": self.file_complete,
            "file_error": self.file_error,
            "count_size": self.count_size,
            "complete_size": self.complete_size,
            "progress": (self.complete_size + self.current_file_size) * 100 / self.count_size if self.count_size > 0 else 0,
        })
        return {
            "task": task_dict,
            "file_status_list": [{
                "source_path": file.src_file,
                "target_path": file.dst_file,
                "status": file.status,
                "progress": file.progress,
                "log": file.message,
            } for file in self.file_map.values()],
        }

    def start_server(self):
        t = threading.Thread(target=self._srv.start_server, args=(), daemon=True)
        t.start()
        register_cleanup(self._srv)
        def close():
            self._srv.stop()

        self._close_func = close

    def close(self):
        if self._close_func is None:
            return
        self._close_func()

    def update_status(self):
        self._srv.update_status()

    def run(self):
        self.task.status = "running"
        self.ft_db.update_task(self.task)
        self.start_server()

        pending_list = [file for file in self.file_map.values() if file.status == "pending"]
        for file in pending_list:
            if file.is_dir > 0:
                # 空文件夹处理部分
                exits, _ = self.dn.target_file_exits(file.dst_file)
                if exits:
                    file.progress = 100
                    file.status = "complete"
                    self.ft_db.update_file_transfer(file)
                    continue
                res, err = self.dn.create_dir(path=file.dst_file)
                if err:
                    file.progress = 0
                    file.status = "failed"
                    file.message = err
                else:
                    if res["status"]:
                        file.progress = 100
                        file.status = "complete"
                    else:
                        file.progress = 0
                        file.status = "failed"
                        file.message = res["msg"]
                self.ft_db.update_file_transfer(file)
                continue


            file.status = "running"
            file.started_at = datetime.now()
            self.ft_db.update_file_transfer(file)

            def call_log(progress, log):
                file.progress = progress
                self.current_file_size = file.file_size * progress // 100
                self.ft_db.update_file_transfer(file)
                self.update_status()

            if self.task.task_action == "upload":
                self.ft_db.update_file_transfer(file)
                res = self.dn.upload_file(
                    filename=file.src_file,
                    target_path=os.path.dirname(file.dst_file),
                    mode=self.task.default_mode,
                    call_log=call_log,
                )
            else:
                self.ft_db.update_file_transfer(file)
                res = self.sn.download_file(
                    filename=file.src_file,
                    target_path=os.path.dirname(file.dst_file),
                    mode=self.task.default_mode,
                    call_log=call_log,
                )

            self.current_file_size = 0

            if res:
                file.status = "failed"
                file.message = res
                self.file_error += 1
            else:
                file.status = "complete"
                file.progress = 100
                self.file_complete += 1
                self.complete_size += file.file_size

            self.ft_db.update_file_transfer(file)
            self.update_status()

        if self.file_error == 0:
            self.task.status = "complete"
        else:
            self.task.status = "failed"
        self.ft_db.update_task(self.task)
        self.update_status()
        time.sleep(10)
        self.close()


def run_file_transfer_task(task_id: int):
    ft = Filetransfer(task_id)
    ft.run()

def task_running_log(task_id: int, call_log:  Callable[[Union[str,dict]], None]):
    socket_file = Filetransfer.SOCKET_FILE_DIR + "/task_" + str(task_id)
    if not os.path.exists(socket_file):
        call_log("任务状态链接不存在")
        return
    s_client =  StatusClient(socket_file, callback=call_log)
    s_client.connect()

def wait_running(task_id: int, timeout:float = 3.0) -> str:
    socket_file = Filetransfer.SOCKET_FILE_DIR + "/task_" + str(task_id)
    while not os.path.exists(socket_file):
        if timeout <= 0:
            return "任务启动超时"
        timeout -= 0.05
        time.sleep(0.05)
    return  ""