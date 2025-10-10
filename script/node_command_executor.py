# coding: utf-8

import sys
import os
import traceback

os.chdir('/www/server/panel/')
sys.path.insert(0, "/www/server/panel/class/")
sys.path.insert(0, "/www/server/panel/")
if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
import public

task_type, task_id = sys.argv[1], int(sys.argv[2])
if len (sys.argv) >= 4:
    sub_id = int(sys.argv[3])
else:
    sub_id = 0

pid_file = "{}/logs/executor_log/{}_{}_{}.pid".format(public.get_panel_path(), task_type, task_id, sub_id)
with open(pid_file, "w") as f:
    f.write(str(os.getpid()))

def cmd_task(main_id: int, log_id: int = 0):
    from mod.project.node.task_flow.command_task import CMDTask
    _task = CMDTask(main_id, log_id, print)
    _task.start()

def file_task(main_id: int):
    from mod.project.node.task_flow.file_task import SelfFiletransferTask
    _task = SelfFiletransferTask(main_id)
    _task.start()

def flow_task(main_id: int):
    from mod.project.node.task_flow.flow import FlowTask
    _task = FlowTask(main_id)
    _task.start()

try:
    if task_type == "command":
        cmd_task(task_id, sub_id)
    elif task_type == "file":
        file_task(task_id)
    elif task_type == "flow":
        flow_task(task_id)

except:
    traceback.print_exc()
    with open('/tmp/node_flow_task.log', 'w') as f:
        f.write(traceback.format_exc())
os.remove(pid_file)