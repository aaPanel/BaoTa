import argparse
import sys
sys.path.insert(0, '/www/server/panel/class')
from btdockerModel.dkgroupModel import main
import PluginLoader
import os
import subprocess
import json
import public
# quota_info = PluginLoader.module_run('quota', 'get_quota_mysql', db_name)
# 解析命令行参数
parser = argparse.ArgumentParser()
parser.add_argument('--id', type=str, required=True, help='The id of the project group')
parser.add_argument('--action', type=str, required=True, help='The action to perform (start or stop)')
args = parser.parse_args()
# json_file = "/www/server/panel/class/projectModel/java_project_groups.json"
import PluginLoader
# 运行脚本
if __name__ == '__main__':
    # with open(json_file, 'r') as f:
    #     data = json.load(f)
    
    # # 创建一个新的空列表来保存更新后的数据
    # new_data = []
    
    # # 找到指定的项目分组
    # for group in data:

    #     if group['id'] == int(args.id):
    #         pid = str(os.getpid())
    #         # 将pid存储到group中
    #         group['pid'] = os.getpid()
    #     # 将更新后的group添加到新的列表中
    #     new_data.append(group)
    
    # # 将更新后的数据写入到文件中
    # with open(json_file, 'w') as f:
    #     json.dump(new_data, f)

    # main().start_group(args.id)

    # PluginLoader.module_run('group', 'start_group', int(args.id))
    if args.action == 'start':
       print(33)
       PluginLoader.module_run('dkgroup', 'start_group', int(args.id))
    elif args.action == 'stop':
       PluginLoader.module_run('dkgroup', 'stop_group', int(args.id))