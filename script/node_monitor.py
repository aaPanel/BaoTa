# coding: utf-8

import sys
import os
import traceback
import time

os.chdir('/www/server/panel/')
sys.path.insert(0, "/www/server/panel/class/")
sys.path.insert(0, "/www/server/panel/")

try:
    from mod.project.node.nodeutil import monitor_all_node_status

    monitor_all_node_status()
except Exception as e:
    traceback.print_exc()
    with open('/tmp/node_monitor.pl', 'w') as f:
        f.write(str(int(time.time())))
        f.write("{}".format(traceback.format_exc()))
