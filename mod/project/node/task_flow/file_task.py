import json
import os
import threading
import queue
import time
import traceback
import itertools
from datetime import datetime
from typing import List, Dict, Callable, Any, Tuple, Union
from concurrent.futures import ThreadPoolExecutor, as_completed

from mod.base.ssh_executor import SSHExecutor
from mod.project.node.dbutil import ServerNodeDB, TaskFlowsDB, TransferTask, TransferFile, TransferLog
from mod.project.node.nodeutil import ServerNode, LPanelNode, SSHApi
from mod.project.node.filetransfer.socket_server import StatusServer, StatusClient, register_cleanup


_SOCKET_FILE_DIR = "/tmp/flow_task"
if not os.path.exists(_SOCKET_FILE_DIR):
    os.mkdir(_SOCKET_FILE_DIR)

def _dir_walk(path: str) -> Tuple[List[dict], str]:
    if not os.path.isdir(path):
        return [], "{} 不是一个目录".format(path)
    res_file = []
    count = 0
    empty_dir = []
    for root, dirs, files in os.walk(path):
        if not files:
            empty_dir.append(root)
        for f in files:
            count += 1
            try:
                res_file.append({
                    "path": os.path.join(root, f),
                    "size": os.path.getsize(os.path.join(root, f)),
                    "is_dir": 0
                })
            except:
                pass
    return [{"path": d, "size": 0, "is_dir": 1} for d in empty_dir] + res_file, ""


class FiletransferTask(object):

    def __init__(self, task: Union[int, TransferTask], call_update: Callable[[Any], None]):
        self._fdb = TaskFlowsDB()
        if isinstance(task, int):
            self.task = self._fdb.TransferTask.get_byid(task)
        elif isinstance(task, TransferTask):
            self.task = task
        else:
            raise ValueError("参数异常")

        if not self.task:
            raise RuntimeError("任务不存在")

        self.event_queue = queue.Queue()
        self.trans_queue = queue.Queue()
        self.mut = threading.Lock()
        self._srv_cache: Dict[int, Union[SSHApi, LPanelNode, ServerNode]] = {}
        self.status_dict: Dict[str, Any] = {
            "task_id": self.task.id,
            "task_type": "file",
            "flow_idx": self.task.step_index -1,
            "count": 0,
            "complete": 0,
            "error": 0,
            "data": None,
        }
        self.is_trans_end = False
        self.call_update = call_update

    def _init_files(self):  # 初始化文件列表
        has_file = self._fdb.TransferFile.find("flow_id = ? AND transfer_task_id = ?", (self.task.flow_id, self.task.id))
        # 判断文件列表是否已经初始化
        if has_file:
            return

        file_list = []
        for src_item in self.task.path_list:
            dst_path = src_item["dst_path"].rstrip("/")
            src_item["path"] = src_item["path"].rstrip("/")
            if not os.path.exists(src_item["path"]):
                continue
            src_item["is_dir"] = os.path.isdir(src_item["path"])
            if src_item["is_dir"]:
                f_list, err = _dir_walk(src_item["path"])
                if not f_list:
                    src_item["dst_file"] = os.path.join(dst_path, os.path.basename(src_item["path"]))
                    file_list.append(src_item)
                else:
                    for f_item in f_list:
                        f_item["dst_file"] = f_item["path"].replace(os.path.dirname(src_item["path"]), dst_path)
                    file_list.extend(f_list)
            else:
                if not os.path.isfile(src_item["path"]):
                    continue
                src_item["dst_file"] = os.path.join(dst_path, os.path.basename(src_item["path"]))
                src_item["size"] = os.path.getsize(src_item["path"])
                file_list.append(src_item)

        t_list = []
        for f_item in file_list:
            fl = TransferFile(
                flow_id=self.task.flow_id,
                transfer_task_id=self.task.id,
                src_file=f_item["path"],
                dst_file=f_item["dst_file"],
                file_size=f_item["size"],
                is_dir=f_item["is_dir"],
            )
            t_list.append(fl)
        try:
            self._fdb.TransferFile.create(t_list)
        except:
            print("初始化文件列表失败", traceback.format_exc())

    def _init_files_log(self):
        tf_list = self._fdb.TransferFile.query("flow_id = ? AND transfer_task_id = ?", (self.task.flow_id, self.task.id))
        if not tf_list:
            return []
        has_fl = self._fdb.TransferLog.query("transfer_task_id = ? AND transfer_file_id = ?", (self.task.id, tf_list[0].id))
        if has_fl:
            return self._fdb.TransferLog.query("transfer_task_id = ?", (self.task.id,))

        fl_list =  []
        for (tf, idx) in itertools.product(tf_list, range(len(self.task.dst_nodes))):
            fl = TransferLog(
                flow_id=self.task.flow_id,
                transfer_task_id=self.task.id,
                transfer_file_id=tf.id,
                dst_node_idx=idx,
                status=0,
                progress=0,
                message=""
            )
            fl_list.append(fl)

        try:
            self._fdb.TransferLog.create(fl_list)
        except:
            print("初始化文件列表失败", traceback.format_exc())


    def _get_srv(self, idx: int) -> Union[SSHApi, LPanelNode, ServerNode]:
        with self.mut:
            if idx in self._srv_cache:
                return self._srv_cache[idx]
            if idx >= len(self.task.dst_nodes):
                raise RuntimeError("节点索引超出范围")
            srv_data: dict = self.task.dst_nodes[idx]
            if srv_data.get("lpver", None):
                srv = LPanelNode(srv_data["address"], srv_data["api_key"], srv_data["lpver"])
            elif srv_data["api_key"] or srv_data["app_key"]:
                srv = ServerNode(srv_data["address"], srv_data["api_key"], srv_data["app_key"])
            else:
                srv_data["ssh_conf"]["threading_mod"] = True  # 线程模式, 在不同线程中使用同一个ssh链接的不同会话
                srv = SSHApi(**srv_data["ssh_conf"])
            self._srv_cache[idx] = srv
            return srv

    def start(self):
        self.task.status = 1
        self._fdb.TransferTask.update(self.task)
        self._init_files()
        self._init_files_log()
        # 获取未完成文件列表
        files_logs = self._fdb.TransferLog.query("transfer_task_id = ? and status = 0", (self.task.id,))
        files_list = self._fdb.TransferFile.query("transfer_task_id = ?", (self.task.id,))
        if not files_logs:
            return
        files_map = {fl.id: fl for fl in files_list}
        for (idx, fl) in enumerate(files_logs):
            fl.log_idx = idx
            fl.tf = files_map[fl.transfer_file_id]
            self.trans_queue.put(fl)

        self.status_dict["count"] = len(files_logs)

        th_event = threading.Thread(target=self.event_func,)
        th_event.start()

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(self.once_trans, worker_id) for worker_id in range(8)]
            for i in range(8):
                executor.submit(self.once_trans)
            for future in as_completed(futures):
                print("Completed result:", future.result())

        self.is_trans_end = True
        th_event.join()
        self.task.status = 2 if self.status_dict["error"] == 0 else 3
        self._fdb.TransferTask.update(self.task)
        self._fdb.close()

    def once_trans(self, worker_id: int):
        while True:
            try:
                tl = self.trans_queue.get(block=False)
            except queue.Empty:
                print("worker_id: %s, 队列已空" % worker_id)
                break
            except Exception as e:
                print("worker_id: %s, 获取任务失败" % worker_id)
                print(traceback.format_exc())
                break

            # 执行一次文件传输
            try:
                if tl.status == 2:  # 跳过已完成的文件
                    self.event_queue.put(tl)
                    continue
                srv = self._get_srv(tl.dst_node_idx)
                if tl.tf.is_dir:           # 处理空目录
                    exits, err = srv.target_file_exits(tl.tf.dst_file)
                    if err: # 获取文件状态错误
                        tl.message = err
                        tl.status = 3
                        self.event_queue.put(tl)
                    elif exits: # 目标文件已存在
                        tl.status = 4
                        tl.progress = 100
                        self.event_queue.put(tl)
                    else: # 目标文件不存在， 创建目录
                        res, err = srv.create_dir(tl.tf.dst_file)
                        if err:
                            tl.message = err
                            tl.status = 3
                        elif isinstance(res, dict):
                            if res["status"]:
                                tl.status = 2
                                tl.progress = 100
                            else:
                                tl.message = res["msg"]
                                tl.status = 3
                        else:
                            tl.status = 2
                            tl.progress = 100

                        self.event_queue.put(tl)
                else:  # 处理文件上传
                    tl.status = 1
                    self.event_queue.put(tl)
                    def _call_log(progress, log):
                        tl.progress = progress
                        self.event_queue.put(tl)

                    err = srv.upload_file(
                        filename=tl.tf.src_file,
                        target_path=os.path.dirname(tl.tf.dst_file),
                        mode="cover",
                        call_log=_call_log)

                    if err:
                        tl.status = 3
                        tl.message = err
                    else:
                        tl.status = 2
                        tl.progress = 100

                    self.event_queue.put(tl)
            except Exception as e:
                err = traceback.format_exc()
                tl.status = 3
                tl.message = str(e) + "\n" + err
                self.event_queue.put(tl)

    def event_func(self):
        fdb = TaskFlowsDB()
        last_time = time.time()
        tmp_dict = {}
        update_fields = ("status", "message", "progress", "completed_at", "started_at")
        complete_set, error_set = set(), set()
        while True:
            try:
                tl: TransferLog = self.event_queue.get(timeout=0.1)
            except queue.Empty:
                if self.is_trans_end:
                    break
                else:
                    continue
            except Exception as e:
                print(e)
                break
            if tl.status in (2, 4):
                complete_set.add(tl.id)
                self.status_dict["complete"] = len(complete_set)
                if not tl.started_at:
                    tl.started_at = tl.started_at or datetime.now()
                tl.completed_at = tl.completed_at or datetime.now()
            elif tl.status == 3:
                error_set.add(tl.id)
                self.status_dict["error"] = len(error_set)
                tl.completed_at = datetime.now()
            elif tl.status == 1:
                tl.started_at = datetime.now()

            tmp_dict[tl.id] = tl
            if time.time() - last_time > 0.5:
                fdb.TransferLog.bath_update(tmp_dict.values(), update_fields=update_fields)
                last_time = time.time()

                self.status_dict["data"] = [i.to_show_data() for i in tmp_dict.values()]
                self.call_update(self.status_dict)
                tmp_dict.clear()


        if tmp_dict:
            fdb.TransferLog.bath_update(tmp_dict.values(), update_fields=update_fields)
            self.status_dict["data"] = [i.to_show_data() for i in tmp_dict.values()]
            self.call_update(self.status_dict)

        fdb.close()


# 在远程节点上执行文件传输
class NodeFiletransferTask(object):

    def __init__(self, task: TransferTask, call_update: Callable[[Any], None]):
        self.task = task
        src_node = task.src_node
        self.srv = ServerNode(src_node["address"],src_node["api_key"], src_node["app_key"], src_node["name"])
        self.call_update = call_update
        self.default_status_data = {
            "task_id": self.task.id,
            "task_type": "file",
        }
        self.status_dict = dict() # 状态数据

    def start(self):
        fdb = TaskFlowsDB()
        self.task.status = 1
        fdb.TransferTask.update(self.task)
        err = self.srv.proxy_transferfile_status(self.task.src_node_task_id, self.handle_proxy_data)
        if err:
            self.task.status = 3
            self.task.message += ";" + err
        else:
            if self.status_dict and self.status_dict.get("error", 0):
                self.task.status = 3
            else:
                self.task.status = 2
        if self.task.message:
            self.task.status = 3

        fdb.TransferTask.update(self.task)

    def handle_proxy_data(self, data):
        ret = {"count": 0,"complete": 0,"error": 0,"data": []}
        try:
            data_dict = json.loads(data)
            if  "type" not in data_dict:
                return

            if data_dict["type"] == "status":
                if "init" in data_dict["data"]:  # 初始化状态跳过
                    return
                ret.update(data_dict["data"])
                ret.update(self.default_status_data)
            else:  # end / error 状态 获取历史数据或错误信息
                if "data" in data_dict:
                    ret.update(data_dict["data"])
                    ret.update(self.default_status_data)
                elif "msg" in data_dict:
                    self.task.message = data_dict["msg"]
                    return
        except:
            print(traceback.format_exc())
            ret["data"].append({"message": "数据源节点执行传输异常，请检查节点是否正常"})
            ret.update(self.default_status_data)

        self.status_dict = ret
        self.call_update(ret)


# 本机执行文件传输，返回信息到远程节点
class SelfFiletransferTask(object):

    def __init__(self, task_id: int):
        self.status_server = StatusServer(self.get_status, (_SOCKET_FILE_DIR + "/file_task_" + str(task_id)))
        self.f_task = FiletransferTask(task_id, self.update_status)

    @staticmethod
    def get_status( init: bool = False):
        return {"init": True }

    def start_status_server(self):
        t = threading.Thread(target=self.status_server.start_server, args=(), daemon=True)
        t.start()
        register_cleanup(self.status_server)

    def update_status(self, update_data: Dict):
        self.status_server.update_status(update_data)

    def start(self):
        self.start_status_server()
        self.f_task.start()
        return


def self_file_running_log(task_id: int, call_log:  Callable[[Union[str,dict]], None], timeout:float = 3.0) -> str:
    socket_file = _SOCKET_FILE_DIR + "/file_task_" + str(task_id)
    while not os.path.exists(socket_file):
        if timeout <= 0:
            return "任务启动超时"
        timeout -= 0.05
        time.sleep(0.05)

    s_client = StatusClient(socket_file, callback=call_log)
    s_client.connect()
    s_client.wait_receive()
    return  ""