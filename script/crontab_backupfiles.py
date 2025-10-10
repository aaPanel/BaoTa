import os
import json
import zipfile
import argparse
import time
import sys
import shutil
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='zipfile')

sys.path.insert(0, "/www/server/panel/class/")
import public
from CloudStoraUpload import CloudStoraUpload  # 引入云存储上传模块

def get_cron_id(src_folder):
    """获取 `cron_id`"""
    try:
        data = public.M('crontab').where('sName=?', (src_folder,)).select()
        if data:
            return data[0]['id'], data[0]['backupTo'] ,data[0]['save_local'] # 返回 cron_id 和 backupTo 、save_local字段
        else:
            return None, None
    except Exception as e:
        print(f"获取 cron_id 失败: {str(e)}")
        return None, None

def backup_files(src_folder):
    # 引入 _CLOUD_OBJ 映射字典
    _cloud_name = {
        "tianyiyun": "天翼云cos",
        "webdav": "webdav存储",
        "minio": "minio存储",
        "dogecloud": "多吉云COS",
    }   
    print()
    print("-" * 76)
    print("★开始备份[{}]".format(public.format_date()))
    print("-" * 76)

    # 获取 cron_id 和 backupTo 字段
    cron_id, backup_to ,save_local= get_cron_id(src_folder)
    if cron_id is None:
        print(f"未找到与源文件夹 {src_folder} 相关的 cron_id，无法执行备份。")
        return

    backup_path = public.M('config').where("id=?", ('1',)).getField('backup_path')
    dst_folder_base = '{}/backup_site_file'.format(backup_path)
    dst_folder = os.path.join(dst_folder_base, os.path.basename(src_folder))

    # 创建备份目标文件夹
    if not os.path.exists(dst_folder):
        os.makedirs(dst_folder)

    try:
        # 读取已备份文件的列表
        try:
            with open(os.path.join(dst_folder, 'backup_files.json'), 'r') as f:
                backup_files = json.load(f)
        except :
            with open(os.path.join(dst_folder, 'backup_files.json'), 'w') as f:
                backup_files = {}
                json.dump(backup_files, f)            
            
        # 判断是否是第一次备份
        first_backup = len(backup_files) == 0

        # 开始备份提示
        if first_backup:
            print("|-全量备份开始")
        else:
            print("|-增量备份开始")

        # 遍历源文件夹中的所有文件，检查是否有文件需要备份
        files_to_backup = []
        for foldername, subfolders, filenames in os.walk(src_folder):
            # 排除目标备份文件夹
            if dst_folder.startswith(foldername):
                continue

            for filename in filenames:
                file_path = os.path.join(foldername, filename)

                # 获取文件的最后修改时间
                try:
                    file_time = os.path.getmtime(file_path)
                except OSError as e:
                    print(f"|-无法获取文件 {file_path} 的修改时间: {e}")
                    continue
                # 如果是第一次备份或者文件的最后修改时间在上次备份后发生变化，则添加到备份列表
                if first_backup or file_path not in backup_files or file_time > backup_files[file_path]:
                    files_to_backup.append((file_path, filename, file_time))

     
        # 如果没有文件需要备份，通知用户并退出
        if not files_to_backup:
            print("|-网站目录里没有文件发生修改，无需备份。")
            return
        # 创建压缩文件
        timestamp = time.strftime("%Y%m%d%H%M%S", time.localtime())
        src_folder_name = os.path.basename(src_folder)
        zip_filename = os.path.join(dst_folder, (timestamp + '_all_' + src_folder_name + '.zip' if first_backup else timestamp + '_' + src_folder_name + '.zip'))
        start_time = time.time()

        try:
            with zipfile.ZipFile(zip_filename, 'w') as zipf:
                # 备份所有需要备份的文件
                for file_path, filename, file_time in files_to_backup:
                    if os.path.exists(file_path):
                        try:
                            # 将文件添加到压缩文件中，保留相对于 src_folder 的路径
                            relative_path = os.path.relpath(file_path, src_folder)
                            zipf.write(file_path, arcname=relative_path)  # 使用相对路径保留目录结构
                            backup_files[file_path] = file_time  # 更新已备份文件的列表
                        except (OSError, shutil.Error) as e:
                            print(f"|-无法备份文件 {file_path}: {e}")
                            return
                    else:
                        print(f"|-文件 {file_path} 不存在，跳过")

        except zipfile.BadZipFile as e:
            print(f"|-创建压缩文件失败: {e}")
            return
        
        # 备份完成提示
        elapsed_time = time.time() - start_time
        zip_size = os.path.getsize(zip_filename)
        print("|-备份完成，耗时{:.3f}秒，压缩包大小：{}".format(elapsed_time, public.to_size(zip_size)))
        print("|-文件已备份到：{}".format(zip_filename))

        backup_type = 1 if first_backup else 0
        
        cloud_backup_path = zip_filename  # 初始备份路径为本地路径
        # backup_to="alioss"
        backup_task_status = True
        # 判断是否需要上传到云存储
        if backup_to and backup_to != 'localhost':
            if backup_to in ["tianyiyun","webdav","minio","dogecloud"]:
                cloud_name_cn = _cloud_name.get(backup_to, backup_to)  # 获取云存储的中文名
                from CloudStoraUpload import CloudStoraUpload
                _cloud_new = CloudStoraUpload()
                _cloud = _cloud_new.run(backup_to)
                if _cloud is False:
                    return False
                print("|-正在上传到{}，请稍候...".format(cloud_name_cn))
                try:
                    backup_path = _cloud_new.backup_path
                    if not backup_path.endswith('/'):
                        backup_path += '/'
                    src_folder_name = os.path.basename(src_folder)
                    upload_path = os.path.join(backup_path, "backup_site_file", src_folder_name, os.path.basename(zip_filename))
                    if _cloud.upload_file(zip_filename, upload_path):
                        print(f"|-文件已成功上传到云存储：{cloud_name_cn}")
                        cloud_backup_path = upload_path + '|' + backup_to + '|' + os.path.basename(zip_filename)  # 更新为云存储路径
                    else:
                        backup_task_status = False
                        print(f"|-上传到{cloud_name_cn}失败")
                except Exception as e:
                    backup_task_status = False
                    print(f"|-上传到{cloud_name_cn}时发生错误: {str(e)}")
            else:
                from CloudStoraUpload import CloudStoraUpload
                _cloud = CloudStoraUpload()
                _cloud.run(backup_to)
                cloud_name_cn = _cloud.obj._title
                if not _cloud.obj:
                    return False
                print("|-正在上传到{}，请稍候...".format(cloud_name_cn))
                try:
                    backup_path = _cloud.obj.backup_path
                    if not backup_path.endswith('/'):
                        backup_path += '/'
                    src_folder_name = os.path.basename(src_folder)
                    upload_path = os.path.join(backup_path, "backup_site_file", src_folder_name, os.path.basename(zip_filename))
                    if _cloud.cloud_upload_file(zip_filename, upload_path):
                        print(f"|-已成功上传到{cloud_name_cn}")
                        cloud_backup_path = upload_path + '|' + backup_to + '|' + os.path.basename(zip_filename)  # 更新为云存储路径
                    else:
                        backup_task_status = False
                        print(f"|-上传到{cloud_name_cn}失败")
                except Exception as e:
                    backup_task_status = False
                    print(f"|-上传到{cloud_name_cn}时发生错误: {str(e)}")
            if not save_local:
                if os.path.exists(zip_filename):
                    if backup_task_status:
                        print("|-备份成功，已上传到云端，并删除本地备份文件：{}".format(zip_filename))
                    else:
                        print("|-上传云端失败，已删除本地备份文件：{}".format(zip_filename))
                    os.remove(zip_filename)

        # 如果备份任务成功，则插入数据库， 并保存已备份文件的列表， 否则由于没有备份文件，则不插入数据库，也不更新已备份文件的列表
        if backup_task_status:
            # 将备份记录插入 `backup` 表，filename 字段使用云存储路径或本地路径
            public.M('backup_site_file').add('cron_id, type, name, filename, size, addtime,src_folder,backupTo',
                                (cron_id, backup_type, zip_filename,cloud_backup_path, zip_size, public.format_date(),src_folder,backup_to))

            # 保存已备份文件的列表
            try:
                with open(os.path.join(dst_folder, 'backup_files.json'), 'w') as f:
                    json.dump(backup_files, f)
            except OSError as e:
                print(f"|-无法保存已备份文件的列表: {e}")
                return

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        print("|-备份失败！" + str(e))

import sys
import os
if __name__ == "__main__":
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)  # 设置行缓冲
    parser = argparse.ArgumentParser(description='Backup files.')
    parser.add_argument('--src_folder', type=str, required=True, help='The source folder to backup.')
    args = parser.parse_args()

    backup_files(args.src_folder)
