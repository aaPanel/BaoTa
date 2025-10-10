#!/www/server/panel/pyenv/bin/python3
#coding: utf-8

import os
import sys
import time

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

os.chdir("/www/server/panel")


from mod.project.java.projectMod import main as java_mod
import public


java_mod_obj = java_mod()


def print_success(msg):
    print("\033[1;32m" + msg + "\033[0m")


def print_error(msg):
    print("\033[1;31m" + msg + "\033[0m")


def main(action: str, project_name: str):
    project_data = java_mod_obj.get_project_find(project_name)
    if action == "start":
        pid = java_mod_obj.get_project_pid(project_data)
        if pid:
            print_success("项目运行中，Pid:{}".format(pid))
            return
        res = java_mod_obj.start_project(public.to_dict_obj({"project_name": project_name}))
    elif action == "stop":
        res = java_mod_obj.stop_project(public.to_dict_obj({"project_name": project_name}))
    else:  # restart
        res = java_mod_obj.restart_project(public.to_dict_obj({"project_name": project_name}))

    if res["status"]:
        print_success(res["msg"])
    else:
        print_error(res["msg"])

    if action != "stop":
        time.sleep(0.5)
        pid = java_mod_obj.get_project_pid(project_data)
        if pid:
            print_success("项目运行中，Pid:{}".format(pid))
        else:
            print_error("未获取到Pid，项目启动可能失败")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: java-service [project_name] [start|stop|restart]")
        sys.exit()

    if sys.argv[2] not in ("start", "stop", "restart"):
        print("未知操作【{}】".format(sys.argv[2]), file=sys.stderr)
        print("Usage: java-service [project_name] [start|stop|restart]")
        sys.exit()
    main(sys.argv[2], sys.argv[1])
