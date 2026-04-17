# coding: utf-8

import sys
import os
import traceback
import argparse

os.chdir('/www/server/panel/')
sys.path.insert(0, "/www/server/panel/class/")
sys.path.insert(0, "/www/server/panel/")
if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
import public

parser = argparse.ArgumentParser()
parser.add_argument("--task_type", type=str, required=True, help="任务类型")
parser.add_argument("--task_id", type=int, required=True, help="任务ID")
parser.add_argument("--exclude_nodes", type=str, help="排除节点")
args = parser.parse_args()

task_type, task_id = args.task_type, args.task_id
ex_ids = []
if args.exclude_nodes:
    ex_ids = [int(i) for i in args.exclude_nodes.split(",")]


pid_file = "{}/logs/executor_log/{}_{}_0.pid".format(public.get_panel_path(), task_type, task_id)
with open(pid_file, "w") as f:
    f.write(str(os.getpid()))

def cmd_task(main_id: int, log_id: int = 0):
    from mod.project.node.task_flow.command_task import CMDTask
    _task = CMDTask(main_id, log_id, print)
    _task.start()

def file_task(main_id: int, exclude_nodes: list, log_id: int = 0):
    from mod.project.node.task_flow.file_task import SelfFiletransferTask
    _task = SelfFiletransferTask(main_id, exclude_nodes, log_id)
    _task.start()

def flow_task(main_id: int):
    from mod.project.node.task_flow.flow import FlowTask
    _task = FlowTask(main_id)
    _task.start()

try:
    if task_type == "command":
        cmd_task(task_id)
    elif task_type == "file":
        file_task(task_id, ex_ids)
    elif task_type == "flow":
        flow_task(task_id)

except:
    traceback.print_exc()
    with open('/tmp/node_flow_task.log', 'w') as f:
        f.write(traceback.format_exc())
os.remove(pid_file)