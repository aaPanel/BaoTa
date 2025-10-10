import json
import threading
import queue
import time
import traceback
from typing import List, Dict, Callable, Any, Union

from mod.base.ssh_executor import SSHExecutor
from mod.project.node.dbutil import ServerNodeDB, CommandTask, CommandLog, TaskFlowsDB


class CMDTask(object):

    def __init__(self, task: Union[int, CommandTask], log_id: int, call_update: Callable[[Any], None]):
        self._edb = TaskFlowsDB()
        if isinstance(task, int):
            self.task = self._edb.CommandTask.find("id = ?", (task,))
        elif isinstance(task, CommandTask):
            self.task = task
        else:
            raise ValueError("task 参数错误")
        if not self.task:
            raise RuntimeError("指定任务不存在")
        if log_id == 0:
            self.task.elogs = self._edb.CommandLog.query("command_task_id = ? ", (self.task.id,))
        else:
            self.task.elogs = [self._edb.CommandLog.find("command_task_id = ? AND id = ?", (self.task.id, log_id))]
        if not self.task.elogs:
            raise RuntimeError("任务无执行条目")

        self.task.status = 1
        self._edb.CommandTask.update(self.task)
        self.end_queue  = queue.Queue()
        self.end_status = False
        self.status: List[Dict] = []
        self.call_update = call_update
        self.status_dict: Dict[str, Union[List[Any], int]] = {
            "task_id": self.task.id,
            "task_type": "command",
            "flow_idx": self.task.step_index -1,
            "count": len(self.task.elogs),
            "complete": 0,
            "error": 0,
            "data": [],
        }

    def end_func(self):
        edb = TaskFlowsDB()
        tmp_dict: Dict[int, CommandLog] = {}
        last_time = time.time()
        update_fields=("status",)
        complete_set, error_set = set(), set()
        while True:
            try:
                elog: CommandLog = self.end_queue.get(timeout=0.1)
            except queue.Empty:
                if self.end_status:
                    break
                else:
                    continue
            except Exception as e:
                print(e)
                break

            if elog.status in (3, 4):
                error_set.add(elog.id)
                self.status_dict["error"] = len(error_set)
            elif elog.status == 2:
                complete_set.add(elog.id)
                self.status_dict["complete"] = len(complete_set)

            tmp_dict[elog.id] = elog
            if time.time() - last_time > 0.5:
                edb.CommandLog.bath_update(tmp_dict.values(), update_fields=update_fields)
                self.status_dict["data"] = [ l.to_show_data() for l in tmp_dict.values()]
                self.call_update(self.status_dict)
                tmp_dict.clear()

        if tmp_dict:
            edb.CommandLog.bath_update(tmp_dict.values(), update_fields=update_fields)
            self.status_dict["data"] = [ l.to_show_data() for l in tmp_dict.values()]
            self.call_update(self.status_dict)

        return

    def start(self):
        thread_list = []
        s_db = ServerNodeDB()
        end_th = threading.Thread(target=self.end_func)
        end_th.start()

        for (idx, log) in enumerate(self.task.elogs):
            log.log_idx = idx
            if log.status == 2: # 跳过已完成的
                self.end_queue.put(log)
                continue

            log.status = 1
            ssh_conf = None
            node = s_db.get_node_by_id(log.server_id)
            if not node:
                log.status = 3
                log.write_log("节点数据丢失，无法执行\n")

            else:
                ssh_conf = json.loads(node["ssh_conf"])
                if not ssh_conf:
                    log.status = 3
                    log.write_log("节点ssh配置数据丢失，无法执行\n")

            self.end_queue.put(log)

            if not ssh_conf:
                continue

            thread = threading.Thread(target=self.run_one, args=(ssh_conf, log))
            thread.start()
            thread_list.append(thread)

        for i in thread_list:
            i.join()
        self.end_status = True
        end_th.join()
        if self.status_dict["error"] > 0:
            self.task.status = 3
        else:
            self.task.status = 2
        self._edb.CommandTask.update(self.task)
        self._edb.close()

    def run_one(self, ssh_conf: dict, elog: CommandLog):
        ssh = SSHExecutor(
            host=ssh_conf["host"],
            port=ssh_conf["port"],
            username=ssh_conf["username"],
            password=ssh_conf["password"],
            key_data=ssh_conf["pkey"],
            passphrase=ssh_conf["pkey_passwd"])
        elog.write_log("开始执行任务\n开始建立ssh连接...\n")
        try:
            ssh.open()
            def on_stdout(data):
                if isinstance(data, bytes):
                    data = data.decode()
                elog.write_log(data)

            elog.write_log("开始执行脚本...\n\n")
            t = time.time()
            res_code = ssh.execute_script_streaming(
                script_content=self.task.script_content,
                script_type=self.task.script_type,
                timeout=60*60,
                on_stdout=on_stdout,
                on_stderr=on_stdout
            )
            take_time = round((time.time() - t)* 1000, 2)
            elog.write_log("\n\n执行结束，耗时[{}ms]\n".format(take_time))
            if res_code == 0:
                elog.status = 2
                elog.write_log("任务完成\n", is_end_log=True)
            else:
                elog.status = 4
                elog.write_log("任务异常，返回状态码为：{}\n".format(res_code), is_end_log=True)
            self.end_queue.put(elog)
        except Exception as e:
            traceback.print_exc()
            elog.status = 3
            elog.write_log("\n任务失败，错误：" + str(e), is_end_log=True)
            self.end_queue.put(elog)
            return
