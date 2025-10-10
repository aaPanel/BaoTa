# -*- coding: utf-8 -*-
# import os
# import glob
# from datetime import datetime
# import sys

# class LogTools:
#     def __init__(self):
#         pass

#     def split_specific_log_by_date(self, log_dir, num_logs_to_keep):
#         # 获取指定目录下的所有.log文件
#         log_files = glob.glob(os.path.join(log_dir, '*.log'))
        
#         for log_path in log_files:
#             log_file = os.path.basename(log_path)
#             with open(log_path, 'r') as f:
#                 logs = f.read()
#             if not logs:
#                 print("日志文件内容为空，跳过文件：{}".format(log_file))
#                 continue

#             # 根据换行符切分日志内容
#             log_entries = logs.split('\n')

#             # 创建一个以标识符为名的目录，用于存储按日期切分的日志
#             identifier = log_file[:-4]  # 移除.log后缀作为标识符
#             output_dir = os.path.join(os.path.dirname(log_path), identifier)
#             if not os.path.exists(output_dir):
#                 os.makedirs(output_dir)

#             # 写入切分后的日志
#             output_file = os.path.join(output_dir, '{}.log'.format(datetime.now().strftime('%Y-%m-%d')))
#             with open(output_file, 'a') as f:
#                 f.write(logs)

#             # 删除旧的日志文件，只保留最新的num_logs_to_keep个日志文件
#             all_log_files = sorted(os.listdir(output_dir), reverse=True)
#             for old_log_file in all_log_files[num_logs_to_keep:]:
#                 os.remove(os.path.join(output_dir, old_log_file))

#             # 清空原始日志文件
#             open(log_path, 'w').close()

# if __name__ == "__main__":
#     log_tools = LogTools()
#     num_logs_to_keep = int(sys.argv[1])  # 从命令行参数获取要保留的日志文件数量
#     log_dir = sys.argv[2]  # 从命令行参数获取要切割的日志文件的目录
#     log_tools.split_specific_log_by_date(log_dir, num_logs_to_keep)



# # -*- coding: utf-8 -*-
# import os
# import shutil
# from datetime import datetime
# import sys
# import re

# class LogTools:
#     def __init__(self):
#         pass

#     def split_specific_log_by_date(self, log_path, num_logs_to_keep):
#         # 根据日期切割指定的.log文件
#         log_file = os.path.basename(log_path)
#         with open(log_path, 'r') as f:
#             logs = f.read()
#         if not logs:
#             print("未找到日志文件：{}".format(log_file))
#             return

#         # 根据换行符切分日志内容
#         log_entries = logs.split('\n')

#         # 创建一个以标识符为名的目录，用于存储按日期切分的日志
#         identifier = log_file[:-4]  # 移除.log后缀作为标识符
#         output_dir = os.path.join(os.path.dirname(log_path), identifier)
#         if not os.path.exists(output_dir):
#             os.makedirs(output_dir)

#         # 写入切分后的日志
#         output_file = os.path.join(output_dir, '{}.log'.format(datetime.now().strftime('%Y-%m-%d')))
#         with open(output_file, 'a') as f:
#             f.write(logs)

#         # 删除旧的日志文件，只保留最新的num_logs_to_keep个日志文件
#         all_log_files = sorted(os.listdir(output_dir), reverse=True)
#         for old_log_file in all_log_files[num_logs_to_keep:]:
#             os.remove(os.path.join(output_dir, old_log_file))

#         # 清空原始日志文件
#         open(log_path, 'w').close()

# if __name__ == "__main__":
#     log_tools = LogTools()
#     num_logs_to_keep = int(sys.argv[1])  # 从命令行参数获取要保留的日志文件数量
#     log_path = sys.argv[2]  # 从命令行参数获取要切割的日志文件路径
#     log_tools.split_specific_log_by_date(log_path, num_logs_to_keep)



# # -*- coding: utf-8 -*-
# import os
# from datetime import datetime
# import sys

# class LogTools:
#     def __init__(self):
#         pass

#     def split_log_file_by_date(self, log_path, num_logs_to_keep):
#         # 根据日期切割指定的.log文件
#         log_file = os.path.basename(log_path)
#         with open(log_path, 'r') as f:
#             logs = f.read()
#         if not logs:
#             print("日志文件内容为空，跳过文件：{}".format(log_file))
#             return

#         # 根据换行符切分日志内容
#         log_entries = logs.split('\n')

#         # 创建一个以标识符为名的目录，用于存储按日期切分的日志
#         identifier = log_file[:-4]  # 移除.log后缀作为标识符
#         output_dir = os.path.join(os.path.dirname(log_path), identifier)
#         if not os.path.exists(output_dir):
#             os.makedirs(output_dir)

#         # 写入切分后的日志
#         output_file = os.path.join(output_dir, '{}.log'.format(datetime.now().strftime('%Y-%m-%d')))
#         with open(output_file, 'a') as f:
#             f.write(logs)

#         # 删除旧的日志文件，只保留最新的num_logs_to_keep个日志文件
#         all_log_files = sorted(os.listdir(output_dir), reverse=True)
#         for old_log_file in all_log_files[num_logs_to_keep:]:
#             os.remove(os.path.join(output_dir, old_log_file))

#         # 清空原始日志文件
#         open(log_path, 'w').close()

#     def split_log_dir_by_date(self, log_dir, num_logs_to_keep):
#         # 获取指定目录下的所有.txt文件
#         for root, dirs, files in os.walk(log_dir):
#             for file in files:
#                 if file.endswith('.txt'):
#                     log_path = os.path.join(root, file)
#                     self.split_log_file_by_date(log_path, num_logs_to_keep)

# if __name__ == "__main__":
#     log_tools = LogTools()
#     num_logs_to_keep = int(sys.argv[1])  # 从命令行参数获取要保留的日志文件数量
#     log_path_or_dir = sys.argv[2]  # 从命令行参数获取要切割的日志文件路径或目录

#     if os.path.isfile(log_path_or_dir):
#         log_tools.split_log_file_by_date(log_path_or_dir, num_logs_to_keep)
#     elif os.path.isdir(log_path_or_dir):
#         log_tools.split_log_dir_by_date(log_path_or_dir, num_logs_to_keep)



# -*- coding: utf-8 -*-
import os
from datetime import datetime
import sys

class LogTools:
    def __init__(self):
        pass

    def split_log_file_by_date(self, log_path, num_logs_to_keep, output_dir):
        # 根据日期切割指定的.log文件
        log_file = os.path.basename(log_path)
        with open(log_path, 'r') as f:
            logs = f.read()
        if not logs:
            print("日志文件内容为空，跳过文件：{}".format(log_file))
            return

        # 根据换行符切分日志内容
        log_entries = logs.split('\n')

        # 创建一个以标识符为名的目录，用于存储按日期切分的日志
        identifier = log_file[:-4]  # 移除.log后缀作为标识符
        output_dir = os.path.join(output_dir, identifier)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 写入切分后的日志
        output_file = os.path.join(output_dir, '{}.txt'.format(datetime.now().strftime('%Y-%m-%d')))
        with open(output_file, 'a') as f:
            f.write(logs)

        # 删除旧的日志文件，只保留最新的num_logs_to_keep个日志文件
        all_log_files = sorted(os.listdir(output_dir), reverse=True)
        for old_log_file in all_log_files[num_logs_to_keep:]:
            os.remove(os.path.join(output_dir, old_log_file))

        # 清空原始日志文件
        open(log_path, 'w').close()

    def split_log_dir_by_date(self, log_dir, num_logs_to_keep):
        # 获取指定目录下的所有.txt文件
        for root, dirs, files in os.walk(log_dir):
            for file in files:
                if file.endswith('.txt'):
                    log_path = os.path.join(root, file)
                    relative_path = os.path.relpath(root, log_dir)
                    output_dir = os.path.join(log_dir, 'rotate_file', relative_path)
                    self.split_log_file_by_date(log_path, num_logs_to_keep, output_dir)

if __name__ == "__main__":
    log_tools = LogTools()
    num_logs_to_keep = int(sys.argv[1])  # 从命令行参数获取要保留的日志文件数量
    log_path_or_dir = sys.argv[2]  # 从命令行参数获取要切割的日志文件路径或目录

    if os.path.isfile(log_path_or_dir):
        output_dir = os.path.join(os.path.dirname(log_path_or_dir), 'rotate_file')
        log_tools.split_log_file_by_date(log_path_or_dir, num_logs_to_keep, output_dir)
    elif os.path.isdir(log_path_or_dir):
        log_tools.split_log_dir_by_date(log_path_or_dir, num_logs_to_keep)
