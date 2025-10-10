import os
import time
import sys
import re  # 引入正则表达式模块
sys.path.insert(0, "/www/server/panel/class/")
import public

def initialize_backup_folder(src_folder):
    print(src_folder)
    file_names_in_db = set()
    src_folder_name = os.path.basename(src_folder)  # 提取源文件夹的名称
    backup_path = public.M('config').where("id=?", ('1',)).getField('backup_path')
    if not backup_path.endswith('/'):
        backup_path += '/'
    target_directory = '{}/backup_site_file'.format(backup_path)  # 备份文件所在的文件夹
    backup_folder = os.path.join(target_directory, src_folder_name)
    init_marker = os.path.join(backup_folder, 'initialized.pl')
    if os.path.exists(backup_folder):        
        data = public.M('crontab').where('sName=?', (src_folder,)).select()
        if data:
            cron_id = data[0]['id']
            backupTo = "localhost"
            # 定义正则表达式，匹配形如 20240906150534_all_444444444444.com.zip 的文件
            pattern = re.compile(r'^\d{14}_(all_)?' + re.escape(src_folder_name) + r'\.zip$')
        
            # 初始化：检查是否存在标记文件
            if not os.path.exists(init_marker):
                print("正在进行初始化...")

                # 扫描文件夹中的备份文件，并写入数据库
                if os.path.exists(backup_folder):
                    for filename in os.listdir(backup_folder):
                        print(filename)
                        # 使用正则表达式匹配文件名，并确保包含 src_folder_name
                        if pattern.match(filename) and src_folder_name in filename:


                            file_path = os.path.join(backup_folder, filename)
                            file_stat = os.stat(file_path)
                            size_in_kb = file_stat.st_size
                            # 修正后的上传路径拼接
                            upload_path = os.path.join(backup_path, "backup_site_file", src_folder_name, filename)
                            cloud_backup_path = upload_path
                            # 查询数据库，看是否已存在该文件名
                            existing_record = public.M('backup_site_file').where('name=?', (cloud_backup_path,)).find()
                            if existing_record:
                                
                                print(f"文件 {filename} 已存在，跳过插入。")
                                continue
                            # 插入数据库
                            public.M('backup_site_file').add(
                                'cron_id, type, name, filename, size, addtime, src_folder, backupTo', 
                                (cron_id, 1 if 'all' in filename else 0, cloud_backup_path, cloud_backup_path, '{:.2f}'.format(size_in_kb), public.format_date(), src_folder, backupTo)
                            )
    public.writeFile(init_marker,"")
    print("初始化完成")

# 主入口
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("请提供备份的源目录路径！")
        sys.exit(1)

    # 从命令行获取参数
    src_folder = sys.argv[1]
    initialize_backup_folder(src_folder)
