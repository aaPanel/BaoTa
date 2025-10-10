import json
import threading
import queue
import time
import traceback

from mod.base.ssh_executor import SSHExecutor
from mod.project.node.dbutil import ServerNodeDB, ExecutorDB, ExecutorLog


class Task(object):
    def __init__(self, task_id: int, log_id: int):
        self._edb = ExecutorDB()
        self.task = self._edb.ExecutorTask.find("id = ?", (task_id,))
        if not self.task:
            raise RuntimeError("指定任务不存在")
        if log_id == 0:
            self.task.elogs = self._edb.ExecutorLog.query("executor_task_id = ?", (self.task.id,))
        else:
            self.task.elogs = [self._edb.ExecutorLog.find("executor_task_id = ? AND id = ?", (self.task.id, log_id))]
        if not self.task.elogs:
            raise RuntimeError("任务无执行条目")

        self.end_queue  = queue.Queue()
        self.end_status = False


    def end_func(self):
        self._edb = ExecutorDB()
        while not self.end_queue.empty() or not self.end_status:
            if self.end_queue.empty():
                time.sleep(0.1)

            elog: ExecutorLog = self.end_queue.get()
            self._edb.ExecutorLog.update(elog)

    def start(self):
        thread_list = []
        s_db = ServerNodeDB()
        for log in self.task.elogs:
            node = s_db.get_node_by_id(log.server_id)
            if not node:
                log.status = 2
                log.update_log("节点数据丢失，无法执行\n")
                self._edb.ExecutorLog.update(log)

            ssh_conf = json.loads(node["ssh_conf"])
            if not ssh_conf:
                log.status = 2
                log.update_log("节点ssh配置数据丢失，无法执行\n")
                self._edb.ExecutorLog.update(log)

            thread = threading.Thread(target=self.run_one, args=(ssh_conf, log))
            thread.start()
            thread_list.append(thread)

        self._edb.close()
        end_th = threading.Thread(target=self.end_func)
        end_th.start()

        for i in thread_list:
            i.join()
        self.end_status = True
        end_th.join()

    def run_one(self, ssh_conf: dict, elog: ExecutorLog):
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
                print(data)
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
                elog.status = 1
                elog.write_log("任务完成\n", is_end_log=True)
            else:
                elog.status = 3
                elog.write_log("任务异常，返回状态码为：{}\n".format(res_code), is_end_log=True)
            self.end_queue.put(elog)
        except Exception as e:
            traceback.print_exc()
            elog.status = 2
            elog.write_log("\n任务失败，错误：" + str(e), is_end_log=True)
            self.end_queue.put(elog)
            return


# log_id 要执行的子任务，默认为 0，表示执行所有子任务
def run_executor_task(task_id: int, log_id: int = 0):
    t = Task(task_id, log_id)
    t.start()



