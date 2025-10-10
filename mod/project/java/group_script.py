import sys
if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

from mod.project.java.groupMod import Group


def start_group(g_id: str):
    g = Group(g_id)
    g.real_run_start()


def stop_group(g_id: str):
    g = Group(g_id)
    g.real_run_stop()


if __name__ == '__main__':
    if len(sys.argv) >= 3:
        action = sys.argv[1]
        group_id = sys.argv[2]
    else:
        print("参数错误")
        exit(1)

    if action == "start":
        start_group(group_id)
    else:
        stop_group(group_id)


