import sys
import json
import os
import time

panelPath = '/www/server/panel'
os.chdir(panelPath)
sys.path.append("class/")
import json, os, public

# 日志类型的英文到中文的映射
log_type_mapping = {
    'system_log': '系统日志',
    'panel_log': '面板日志',
    'www_log': '网站日志',
    'usranalyse_log': '防入侵日志',
    'mysql_log': 'MySQL日志',
    'Recycle': '回收站文件',
    'mail_log': '邮件日志',
    'php_session': 'PHP会话文件',
}


def to_size(size):
    """字节单位转换"""
    ds = ['b', 'KB', 'MB', 'GB', 'TB']
    for d in ds:
        if size < 1024:
            return f"{int(size)}{d}"
        size = size / 1024
    return '0b'


def return_login_log():
    rpath = '/var/log'
    con = ['/var/log/audit', '/var/log/maillog']
    ret = []
    if os.path.exists(rpath):
        for d in os.listdir(rpath):
            filename = rpath + '/' + d
            if os.path.isdir(filename):
                if filename in con:
                    for i in os.listdir(filename):
                        ret_size = { }
                        name = filename + '/' + i
                        if not os.path.exists(name):
                            continue
                        size = os.path.getsize(name)
                        ret_size['size'] = to_size(size)
                        ret_size['filename'] = i
                        ret_size['name'] = filename + '/' + i
                        ret_size['count_size'] = size
                        ret.append(ret_size)
            else:
                if 'maillog' in d:
                    continue
                ret_size = { }
                size = os.path.getsize(filename)
                if size >= 100:
                    ret_size['size'] = to_size(size)
                    ret_size['count_size'] = size
                    ret_size['name'] = filename
                    ret.append(ret_size)
    return ret


def return_panel():
    clear_path = [
        { 'path': '/www/server/panel', 'find': 'testDisk_' },
        { 'path': '/tmp', 'find': 'panelBoot.pl' },
        { 'path': '/www/server/panel/install', 'find': '.rpm' },
        { 'path': '/www/server/panel/install', 'find': '.zip' },
        { 'path': '/www/server/panel/install', 'find': '.gz' }
    ]

    ret = []
    for c in clear_path:
        if os.path.exists(c['path']):
            for d in os.listdir(c['path']):
                if d.find(c['find']) == -1:
                    continue
                filename = os.path.join(c['path'], d)
                if not os.path.exists(filename):
                    continue
                fsize = os.path.getsize(filename)
                ret_size = {
                    'filename': filename,
                    'size': to_size(fsize),
                    'count_size': fsize
                }
                ret.append(ret_size)
    return ret


def return_www_log():
    clear_path = [{ 'path': '/www/wwwlogs', 'find': ['.log', 'error_log', 'access_log'] }]
    ret = []

    def traverse_directory(path):
        if not os.path.exists(path):
            return
        for d in os.listdir(path):
            filename = os.path.join(path, d)
            # 如果是目录，递归遍历子目录
            if os.path.isdir(filename):
                traverse_directory(filename)
                continue
            # 如果是文件且符合日志后缀，处理文件
            if not any(d.endswith(ext) for ext in clear_path[0]['find']):
                continue
            fsize = os.path.getsize(filename)
            if fsize == 0:
                continue
            ret_size = {
                'name': filename,
                'filename': os.path.basename(filename),
                'count_size': fsize,
                'size': to_size(fsize)
            }
            ret.append(ret_size)

    # 遍历所有指定路径
    for c in clear_path:
        traverse_directory(c['path'])

    return ret


def return_usranalyse_log():
    """
    获取防入侵软件 usranalyse 的日志文件信息。
    仅扫描指定目录下的 .txt 文件，且文件大小不小于 1KB。
    """
    clear_paths = [
        '/usr/local/usranalyse/logs/log',
        '/usr/local/usranalyse/logs/total'
    ]
    target_extension = '.txt'
    logs = []

    for directory in clear_paths:
        if not os.path.exists(directory):
            # print(f"路径 {directory} 不存在，跳过。")
            continue

        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    # 确保是文件且以 .txt 结尾
                    if not file.lower().endswith(target_extension):
                        continue

                    file_path = os.path.join(root, file)

                    try:
                        size = os.path.getsize(file_path)
                    except OSError as e:
                        print(f"无法获取文件大小 {file_path}: {e}")
                        continue

                    logs.append(
                        {
                            'name': file_path,
                            'filename': file,
                            'size': to_size(size),
                            'count_size': size
                        }
                    )
        except Exception as e:
            print(f"扫描目录 {directory} 失败: {e}")
            continue

    return logs


# def return_usranalyse_log():
#     clear_path = [{'path': '/usr/local/usranalyse/logs/log/www', 'find': 'txt'},
#                   {'path': '/usr/local/usranalyse/logs/total/www', 'find': 'txt'},
#                   {'path': '/usr/local/usranalyse/logs/log/root', 'find': 'txt'},
#                   {'path': '/usr/local/usranalyse/logs/total/root', 'find': 'txt'}]
#     ret = []
#     for c in clear_path:
#         if os.path.exists(c['path']):
#             for d in os.listdir(c['path']):
#                 if d.find(c['find']) == -1:
#                     continue
#                 filename = c['path'] + '/' + d
#                 if not os.path.exists(filename):
#                     continue
#                 fsize = os.path.getsize(filename)
#                 if fsize < 1024:
#                     continue
#                 ret_size = {}
#                 ret_size['name'] = filename
#                 ret_size['filename'] = os.path.basename(filename)
#                 ret_size['count_size'] = fsize
#                 ret_size['size'] = to_size(fsize)
#                 ret.append(ret_size)
#     return ret


def return_mysql_log():
    """
    检查 MySQL 慢日志和错误日志是否存在，并返回文件路径和大小信息
    """
    ret = []

    # 1. 检查 MySQL 慢日志
    try:
        # print("|---检查 MySQL 慢日志")
        my_info = public.get_mysql_info()
        if not my_info['datadir']:
            ret.append({ 'type': 'slow_log', 'log': '未安装MySQL数据库!' })
        else:
            path = my_info['datadir'] + '/mysql-slow.log'
            if os.path.exists(path):
                fsize = os.path.getsize(path)
                if fsize > 0:  # 只有在文件大小大于 0 时才添加
                    ret.append(
                        {
                            'type': 'slow_log',
                            'filename': os.path.basename(path),
                            'path': path,
                            'count_size': fsize,
                            'size': to_size(fsize)
                        }
                    )
            else:
                ret.append({ 'type': 'slow_log', 'log': '慢日志文件不存在!' })
    except Exception as e:
        print(f"检查慢日志时发生错误: {e}")
        ret.append({ 'type': 'slow_log', 'log': f'检查慢日志时发生错误: {e}' })

    # 2. 检查 MySQL 错误日志
    try:
        # print("|---检查 MySQL 错误日志")
        my_info = public.get_mysql_info()
        if not my_info['datadir']:
            ret.append({ 'type': 'error_log', 'log': '未安装MySQL数据库!' })
        else:
            path = my_info['datadir']
            error_log_file = ''
            # 查找错误日志文件
            for d in os.listdir(path):
                if d.endswith('.err'):
                    error_log_file = os.path.join(path, d)
                    break

            if error_log_file and os.path.exists(error_log_file):
                fsize = os.path.getsize(error_log_file)
                if fsize > 0:  # 只有在文件大小大于 0 时才添加
                    ret.append(
                        {
                            'type': 'error_log',
                            'filename': os.path.basename(error_log_file),
                            'path': error_log_file,
                            'count_size': fsize,
                            'size': to_size(fsize)
                        }
                    )
            else:
                ret.append({ 'type': 'error_log', 'log': '错误日志文件不存在!' })
    except Exception as e:
        print(f"检查错误日志时发生错误: {e}")
        ret.append({ 'type': 'error_log', 'log': f'检查错误日志时发生错误: {e}' })

    return ret


# 回收站

def return_recycle_log():
    clear_path = [
        { 'path': '/.Recycle_bin' },
        { 'path': '/www/.Recycle_bin' }
    ]
    ret = []

    def traverse_directory(path):
        if not os.path.exists(path):
            return
        for d in os.listdir(path):
            filename = os.path.join(path, d)
            # 如果是目录，递归遍历子目录
            if os.path.isdir(filename):
                traverse_directory(filename)
                continue
            # 如果是文件，处理文件
            fsize = os.path.getsize(filename)
            if fsize < 1024:
                continue
            ret_size = {
                'name': filename,
                'filename': os.path.basename(filename),
                'count_size': fsize,
                'size': to_size(fsize)
            }
            ret.append(ret_size)

    # 遍历所有指定路径
    for c in clear_path:
        traverse_directory(c['path'])

    return ret


# 返回邮件日志
def return_mail_log():
    rpath = '/var/spool'
    con = ['cron', 'anacron']
    ret = []
    if os.path.exists(rpath):
        for d in os.listdir(rpath):
            if d in con:
                continue
            dpath = os.path.join(rpath, d)
            if not os.path.exists(dpath) or not os.path.isdir(dpath):
                continue
            for n in os.listdir(dpath):
                filename = os.path.join(dpath, n)
                if not os.path.isfile(filename):
                    continue  # 只处理文件
                fsize = os.path.getsize(filename)
                if fsize == 0:
                    continue
                ret.append(
                    {
                        'filename': filename,
                        'size': to_size(fsize),
                        'count_size': fsize
                    }
                )
    rpath = '/var/log'
    if os.path.exists(rpath):
        for d in os.listdir(rpath):
            if 'maillog' not in d:
                continue
            filename = os.path.join(rpath, d)
            if not os.path.isfile(filename):
                continue  # 只处理文件
            fsize = os.path.getsize(filename)
            if fsize == 0:
                continue
            ret.append(
                {
                    'filename': filename,
                    'size': to_size(fsize),
                    'count_size': fsize
                }
            )
    return ret


# 返回php_session文件
def return_session():
    spath = '/tmp'
    total = count = 0
    import shutil
    ret = { }
    if os.path.exists(spath):
        for d in os.listdir(spath):
            if d.find('sess_') == -1: continue
            filename = spath + '/' + d
            if not os.path.exists(filename): continue
            fsize = os.path.getsize(filename)
            total += fsize
            count += 1;
            ret['php_session'] = ({ 'count': count, 'size': to_size(total), 'count_size': total })
    # if count < 2: return []
    return ret


def get_log_data():
    ret = { }
    ret['system_log'] = return_login_log()
    ret['panel_log'] = return_panel()
    ret['www_log'] = return_www_log()
    ret['usranalyse_log'] = return_usranalyse_log()
    ret['mysql_log'] = return_mysql_log()
    ret['Recycle'] = return_recycle_log()
    ret['mail_log'] = return_mail_log()
    ret['php_session'] = return_session()
    # ret['total_log'] = return_total_log()
    # # 自定义路径或者文件
    # ret['user_config'] =user_config_path(None)
    return ret


# 清理 php_session 文件
def ClearSession(data):
    if data:
        spath = '/tmp'
        total = count = 0

        if os.path.exists(spath):
            print("|---开始清理 php_session 文件...")
            for d in os.listdir(spath):
                if d.find('sess_') == -1:
                    continue

                filename = os.path.join(spath, d)

                if not os.path.exists(filename):
                    print(f"|---文件 {filename} 不存在，跳过！")
                    continue

                fsize = os.path.getsize(filename)
                total += fsize

                # 判断是否为目录并清理
                if os.path.isdir(filename):
                    print(f"|---{filename} 是一个目录，跳过！")
                    shutil.rmtree(filename)
                else:
                    if fsize < 1024:
                        print(f"|---文件大小小于 1KB，不清理: {filename}")
                        continue
                    os.remove(filename)
                    print(f"|---清理文件: {filename}")

                count += 1

            # 打印结果
            if count > 0:
                print(f"|---成功清理了 {count} 个 php_session 文件，总大小为 {total} 字节。")
            else:
                print("|---未找到需要清理的日志文件。")
            return True
        else:
            print(f"|---目录 {spath} 不存在，无法清理 php_session 文件。")
            return False


# 清理功能
def remove_file(get):
    ret = []
    # 记录用户的选择的文件
    data = json.loads(get.data)
    if 'system_log' in data:
        print("|---开始清理系统日志")
        system_log = data['system_log']
        if len(system_log) != 0:
            for i in system_log:
                # 统计listFile
                count_size = int(i['count_size'])
                ret.append(count_size)
                # 清理系统日志
                if int(i['count_size']) < 1024:
                    print('|---文件{}大小小于 1KB，不清理!'.format(i["name"]))
                    continue
                if i['name'].endswith('.log'):
                    print(f'|---清空日志文件内容: {i["name"]}')
                    with open(i['name'], 'w') as f:
                        f.write('')
                else:
                    os.remove(i['name'])
                    print(f'|---清理文件: {i["name"]}')
        else:
            print("|---未找到需要清理的日志文件。")

    # 面板日志
    if 'panel_log' in data:
        print("|---开始清理面板日志文件")
        if len(data["panel_log"]) != 0:
            for i in data['panel_log']:
                # 统计总量
                count_size = int(i['count_size'])
                ret.append(count_size)
                if int(i['count_size']) < 1024:
                    print(f'|---文件大小小于 1KB，不清理: {i["filename"]}')
                    continue
                os.remove(i['filename'])
                print(f'|---清理文件: {i["filename"]}')
        else:
            print("|---未找到需要清理的日志文件。")

    # 网站日志
    if 'www_log' in data:
        print("|---开始清理网站日志")
        if len(data["www_log"]) != 0:
            for i in data['www_log']:
                if os.path.isdir(i['name']):
                    continue
                # 如果文件小于 1024 字节，不清理，打印提示信息
                if int(i['count_size']) < 1024:
                    print('|---文件{}大小小于 1KB，不清理!'.format(i["name"]))
                    continue
                # 如果文件是 .log 结尾，则将文件内容置空
                if i['name'].endswith('.log'):
                    with open(i['name'], 'w') as f:
                        f.write('')
                print('|---清理文件: {}'.format(i["name"]))
                # 总大小
                count_size = int(i['count_size'])
                ret.append(count_size)
        else:
            print("|---未找到需要清理的日志文件。")
    # 堡塔防入侵日志
    if 'usranalyse_log' in data:
        print("|---开始清理防入侵日志")
        if len(data["usranalyse_log"]) != 0:
            for i in data['usranalyse_log']:
                # 总大小
                count_size = int(i['count_size'])
                ret.append(count_size)

                # 仅清理超过1024KB (1MB) 的文件
                if count_size < 1024:
                    print('|---文件{}大小小于 1KB，不清理!'.format(i["name"]))
                    continue

                if os.path.isdir(i['name']):
                    continue  # 跳过目录

                os.remove(i['name'])
                print("|---清理文件: {}".format(i['name']))
        else:
            print("|---未找到需要清理的日志文件。")
    # 清理 MySQL 日志
    if 'mysql_log' in data:
        print("|---开始清理 MySQL 日志")
        mysql_logs = data['mysql_log']

        if mysql_logs:
            for log in mysql_logs:
                count_size = int(log['count_size'])

                # 小于 1KB 的文件不清理
                if count_size < 1024:
                    print('|---文件 {} 大小小于 1KB，不清理!'.format(log["filename"]))
                    continue

                # 统计文件大小
                ret.append(count_size)
                file_path = log['path']  # 使用 'path' 来获取完整的文件路径
                try:
                    if os.path.exists(file_path):
                        # 清空日志文件内容而不是删除文件
                        with open(file_path, 'w') as f:
                            f.truncate(0)  # 清空文件内容
                        print("|---成功清空 MySQL 日志文件: {} (大小: {})".format(file_path, log['size']))
                    else:
                        print("|---文件不存在，无法清空: {}".format(file_path))
                except Exception as e:
                    print("|---清空 MySQL 日志文件 {} 失败: {}".format(file_path, e))
        else:
            print("|---未找到需要清理的日志文件。")

    # 回收站清理
    if 'Recycle' in data:
        print("|---开始清理回收站文件")
        Recycle = data['Recycle']
        if len(Recycle) != 0:
            for i in Recycle:
                print(i['name'])
                count_size = int(i['count_size'])
                ret.append(count_size)
                if int(i['count_size']) < 1024:
                    print('|---文件{}大小小于 1KB，不清理!'.format(i["name"]))
                    continue
                try:
                    os.remove(i['name'])
                    print('|---清理文件: {}'.format(i["name"]))
                except:
                    os.system('rm -rf {}'.format(i['name']))
        else:
            print("|---未找到需要清理的日志文件。")

    # 清理邮件日志
    if 'mail_log' in data:
        print("|---开始清理邮件日志")
        if data["mail_log"]:
            for log in data['mail_log']:
                file_path = log['filename']
                try:
                    if os.path.exists(file_path):
                        with open(file_path, 'w') as f:
                            f.truncate(0)
                        print("|---成功清空邮件日志文件: {} (大小: {})".format(file_path, log['size']))
                    else:
                        print("|---文件不存在，无法清空: {}".format(file_path))
                except Exception as e:
                    print("|---清空邮件日志文件 {} 失败: {}".format(file_path, e))
        else:
            print("|---未找到需要清理的日志文件。")

    # 清理 PHP 会话日志
    if 'php_session' in data:
        print("|---开始清理PHP会话日志")
        php_session = data['php_session']
        if 'php_session' in php_session:
            if int(php_session['php_session']['count']) > 0:
                # 统计
                count_size = int(php_session['php_session']['count_size'])
                ret.append(count_size)
                # 清理php_session
                ClearSession(php_session)
        else:
            print("|---未找到需要清理的日志文件。")

    return to_size(sum(ret))


def clean_logs(selected_logs):
    get = public.dict_obj()
    get.data = json.dumps(selected_logs)  # 将字典转换为字符串
    remove_file(get)


def clean_user_config_log(directories):
    if not isinstance(directories, list):
        directories = [directories]

    log_extensions = ['.log', '.txt', '.out', '.err', '.log.1']

    for directory in directories:
        if not os.path.exists(directory):
            print(f"|---目录 {directory} 不存在,跳过清理！")
            continue

        print(f"|---开始清理目录 {directory} 下的日志文件...")
        small_files_count = 0
        cleaned_files_count = 0

        for root, dirs, files in os.walk(directory):
            for file in files:
                if any(file.endswith(ext) for ext in log_extensions):
                    file_path = os.path.join(root, file)
                    if os.path.getsize(file_path) < 1024:
                        small_files_count += 1
                    else:
                        try:
                            # 清空文件内容
                            with open(file_path, 'w') as f:
                                f.truncate(0)
                            cleaned_files_count += 1
                        except Exception as e:
                            print(f"|---无法清空文件 {file_path}: {str(e)}")

        # 打印结果
        if small_files_count > 0:
            print(f"|---共有 {small_files_count} 个日志文件小于 1KB，不进行清理。")
        if cleaned_files_count > 0:
            print(f"|---成功清理了 {cleaned_files_count} 个日志文件。")
        if small_files_count == 0 and cleaned_files_count == 0:
            print("|---未找到需要清理的日志文件。")


def main():
    # 获取所有日志数据
    log_data = get_log_data()
    # 获取用户输入的日志类型，支持多个类型，以逗号分隔
    log_types = sys.argv[1].split(',') if len(sys.argv) > 1 else ["all"]
    if len(sys.argv) >= 3:

        argv_list = sys.argv[2].split(",")

        # 传过来的是文件夹列表则表明是自定义路径类型
        if all([os.path.isdir(i) for i in argv_list]):
            log_types = ["user_config"]

        # 传过来的是多个清理类型
        if all([i in log_type_mapping.keys() for i in argv_list]):
            log_types = argv_list

    # 确保自定义类型 "user_config" 只能单独选择
    if "user_config" in log_types and len(log_types) > 1:
        print("|---自定义日志类型只能单独选择")
        sys.exit(1)

    selected_logs = { }
    if "all" in log_types:
        selected_logs = log_data
        log_types = ["全部日志"]
    else:
        for log_type in log_types:
            if log_type not in log_data and log_type != "user_config":
                print(f"|---未知的日志类型: {log_type}")
                sys.exit(1)
            if log_type != "user_config":
                selected_logs[log_type] = log_data[log_type]
                # print(f"开始清理{log_type_mapping.get(log_type, log_type)}")
    if "user_config" in log_types:
        if len(sys.argv) < 3:
            print("|---请提供目录路径作为第二个参数")
            sys.exit(1)

        # 将用户提供的目录路径转换为列表格式
        directories = sys.argv[2].split(',')
        directory_list = [directory.strip() for directory in directories]
        # print(f"开始清理目录 {directory_list} 下的日志文件")

        clean_user_config_log(directory_list)
    else:
        clean_logs(selected_logs)


if __name__ == "__main__":
    main()
