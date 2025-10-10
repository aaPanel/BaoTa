# coding: utf-8

import sys
import os
import time
import traceback

os.chdir('/www/server/panel/')
sys.path.insert(0, "/www/server/panel/class/")
sys.path.insert(0, "/www/server/panel/")

try:
    from mod.project.node.loadutil.log_analyze import get_log_analyze
    from mod.project.node.dbutil import NodeDB

    all_loads = NodeDB().loads_list("all", 0, 1000)
    if isinstance(all_loads, list):
        for load in all_loads:
            if load['site_type'] == 'http':
                la = get_log_analyze("http", load['site_name'], interval=500)
            else:
                la = get_log_analyze("tcp", load['name'],interval=500)
            la.analyze_logs()

except Exception as e:
    traceback.print_exc()
    with open('/tmp/total_load_msg.pl', 'w') as f:
        f.write(str(int(time.time())))
        f.write("{}".format(traceback.format_exc()))
