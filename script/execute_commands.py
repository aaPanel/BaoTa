# import subprocess, os, sys

# os.chdir('/www/server/panel/')
# sys.path.insert(0, "class/")
# import public

# def get_crontab_data():
#     # 实际上您需要从数据库获取数据
#     cront = public.M('crontab').select()
#     return cront

# def execute_startup_services():
#     crontab_data = get_crontab_data()  # 获取crontab数据
#     for task in crontab_data:
#         if task['sType'] == 'startup_services':  # 检查任务类型
#             commands = task['sBody'].split('\n')  # 使用换行符分割多个命令
#             for command in commands:
#                 try:
#                     print(f"Executing: {command}")
#                     result = subprocess.run(command, shell=True, capture_output=True, text=True)
#                     if result.stderr:
#                         print(f"Command Error Output:\n{result.stderr}")
#                     else:
#                         print(f"Command executed successfully: {command}")
#                 except Exception as e:
#                     print(f"Error executing command: {e}")

# # 执行示例
# execute_startup_services()

import subprocess, os, sys

# 假设已经改变了工作目录并设置了sys.path
os.chdir('/www/server/panel/')
sys.path.insert(0, "class/")
import public
import crontab
def get_crontab_data():
    # 从数据库获取数据
    cront = public.M('crontab').select()
    return cront

def StartTask(task_id):
    # 这里只是示意，你需要根据实际情况来调整
    # 假设StartTask已经在public或相关模块中定义
    try:
        result = public.StartTask({'id': task_id})
        print(f"Task {task_id} executed, result: {result}")
    except Exception as e:
        print(f"Error executing task {task_id}: {e}")

def execute_startup_services():
    get = public.dict_obj()
    p = crontab.crontab()
    crontab_data = get_crontab_data()  # 获取crontab数据
    for task in crontab_data:
        if task['sType'] == 'startup_services':  # 检查任务类型
            get.id=task['id']
            # 直接调用StartTask函数执行任务
            p.StartTask(get)

# 执行示例
execute_startup_services()
