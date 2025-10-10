from .load_db import LoadSite, HttpNode, TcpNode, NodeDB
from .node_db import Node, ServerNodeDB, ServerMonitorRepo, NodeAPPKey
from .file_transfer_db import FileTransfer, FileTransferDB, FileTransferTask
# from .executor import Script, ScriptGroup, ExecutorDB, ExecutorLog, ExecutorTask
from .node_task_flow import Script, Flow, CommandTask, CommandLog, TransferFile, TransferLog, TaskFlowsDB, \
    TransferTask

# 初始化数据库
try:
    NodeDB().init_db()
    ServerNodeDB().init_db()
    FileTransferDB().init_db()
    # ExecutorDB().init_db()
    TaskFlowsDB().init_db()
except Exception as e:
    import public
    public.print_error()
