# coding: utf-8

import sys
import os
import traceback

os.chdir('/www/server/panel/')
sys.path.insert(0, "/www/server/panel/class/")
sys.path.insert(0, "/www/server/panel/")

try:
    from mod.project.node.filetransfer import run_file_transfer_task
    run_file_transfer_task(int(sys.argv[1]))
except:
    traceback.print_exc()
    with open('/tmp/node_file_transfer.pl', 'w') as f:
        f.write(traceback.format_exc())
