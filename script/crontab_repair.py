import os
import subprocess
import time
from datetime import datetime

# 日志文件路径
log_file_path = '/tmp/repair_crontab.txt'

# 写入日志并立即刷新缓冲区
def write_log(message):
    with open(log_file_path, 'a') as log_file:
        log_file.write(message + '\n')
        log_file.flush()

# 获取计划任务文件位置
def get_cron_file():
    u_path = '/var/spool/cron/crontabs'
    u_file = u_path + '/root'
    c_file = '/var/spool/cron/root'
    cron_path = c_file
    if not os.path.exists(u_path):
        cron_path = c_file

    if os.path.exists("/usr/bin/apt-get"):
        cron_path = u_file
    elif os.path.exists('/usr/bin/yum'):
        cron_path = c_file

    if cron_path == u_file:
        if not os.path.exists(u_path):
            write_log("创建目录: {}".format(u_path))
            os.makedirs(u_path, 472)
            subprocess.run(["chown", "root:crontab", u_path])
    if not os.path.exists(cron_path):
        write_log("创建文件: {}".format(cron_path))
        with open(cron_path, 'w') as f:
            f.write("")
    write_log("计划任务文件路径: {}".format(cron_path))
    return cron_path

# 更新软件源
def update_sources():
    if os.path.exists("/usr/bin/apt-get"):
        write_log("更新Ubuntu/Debian软件源...")
        # 判断是 Ubuntu 还是 Debian 系统
        is_debian = False
        version = ""
        try:
            result = subprocess.run(['lsb_release', '-is'], capture_output=True, text=True)
            if 'Debian' in result.stdout:
                is_debian = True
                version_result = subprocess.run(['lsb_release', '-cs'], capture_output=True, text=True)
                version = version_result.stdout.strip()
        except Exception as e:
            write_log("无法确定系统类型，假定为Ubuntu: {}".format(e))

        if is_debian:
            aliyun_sources = ""
            if version == "buster":
                aliyun_sources = """
deb http://mirrors.aliyun.com/debian/ buster main contrib non-free
deb http://mirrors.aliyun.com/debian/ buster-updates main contrib non-free
deb http://mirrors.aliyun.com/debian buster-backports main contrib non-free
deb http://security.debian.org/debian-security buster/updates main contrib non-free
"""
            elif version == "bullseye":
                aliyun_sources = """
deb http://mirrors.aliyun.com/debian/ bullseye main contrib non-free
deb http://mirrors.aliyun.com/debian/ bullseye-updates main contrib non-free
deb http://mirrors.aliyun.com/debian bullseye-backports main contrib non-free
deb http://security.debian.org/debian-security bullseye/updates main contrib non-free
"""
            elif version == "bookworm":
                aliyun_sources = """
deb http://mirrors.aliyun.com/debian/ bookworm main contrib non-free
deb http://mirrors.aliyun.com/debian/ bookworm-updates main contrib non-free
deb http://mirrors.aliyun.com/debian bookworm-backports main contrib non-free
deb http://security.debian.org/debian-security bookworm/updates main contrib non-free
"""
            else:
                write_log("不支持的Debian版本: {}".format(version))
                exit(1)
        else:
            aliyun_sources = """
deb http://mirrors.aliyun.com/ubuntu/ focal main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ focal-security main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ focal-updates main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ focal-proposed main restricted universe multiverse
deb http://mirrors.aliyun.com/ubuntu/ focal-backports main restricted universe multiverse
"""

        sources_list_path = "/etc/apt/sources.list"
        backup_sources_list_path = "/etc/apt/sources.list.bak"

        # 备份现有的 sources.list 文件
        if not os.path.exists(backup_sources_list_path):
            write_log("备份现有的 sources.list 文件")
            os.rename(sources_list_path, backup_sources_list_path)

        with open(sources_list_path, 'w') as f:
            f.write(aliyun_sources)

        try:
            subprocess.run(['apt-get', 'update'], check=True)
            write_log("软件源更新成功")
        except subprocess.CalledProcessError as e:
            write_log("更新软件源失败: {}".format(e))
            # 恢复原来的 sources.list 文件
            os.rename(backup_sources_list_path, sources_list_path)
            exit(1)
    elif os.path.exists('/usr/bin/yum'):
        write_log("更新CentOS软件源...")
        aliyun_sources = """
[base]
name=CentOS-$releasever - Base - mirrors.aliyun.com
baseurl=http://mirrors.aliyun.com/centos/$releasever/os/$basearch/
gpgcheck=1
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7

[updates]
name=CentOS-$releasever - Updates - mirrors.aliyun.com
baseurl=http://mirrors.aliyun.com/centos/$releasever/updates/$basearch/
gpgcheck=1
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7

[extras]
name=CentOS-$releasever - Extras - mirrors.aliyun.com
baseurl=http://mirrors.aliyun.com/centos/$releasever/extras/$basearch/
gpgcheck=1
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7

[centosplus]
name=CentOS-$releasever - Plus - mirrors.aliyun.com
baseurl=http://mirrors.aliyun.com/centos/$releasever/centosplus/$basearch/
gpgcheck=1
enabled=0
gpgkey=http://mirrors.aliyun.com/centos/RPM-GPG-KEY-CentOS-7
"""
        repo_file_path = "/etc/yum.repos.d/CentOS-Base.repo"
        backup_repo_file_path = "/etc/yum.repos.d/CentOS-Base.repo.bak"

        # 备份现有的 repo 文件
        if not os.path.exists(backup_repo_file_path):
            write_log("备份现有的 repo 文件")
            os.rename(repo_file_path, backup_repo_file_path)

        with open(repo_file_path, 'w') as f:
            f.write(aliyun_sources)

        try:
            subprocess.run(['yum', 'clean', 'all'], check=True)
            subprocess.run(['yum', 'makecache'], check=True)
            write_log("软件源更新成功")
        except subprocess.CalledProcessError as e:
            write_log("更新软件源失败: {}".format(e))
            # 恢复原来的 repo 文件
            os.rename(backup_repo_file_path, repo_file_path)
            exit(1)

# 安装crontab服务
def install_service():
    write_log("安装crontab服务...")
    try:
        if os.path.exists("/usr/bin/apt-get"):
            # 检查cron是否已安装
            result = subprocess.run(['dpkg-query', '-W', '-f=${Status}', 'cron'], capture_output=True, text=True)
            if 'install ok installed' in result.stdout:
                write_log("Crontab服务已安装")
                return

            result = subprocess.run(['apt-get', 'install', '-y', 'cron'], check=True)
            if result.returncode != 0:
                update_sources()
                subprocess.run(['apt-get', 'install', '-y', 'cron'], check=True)
        elif os.path.exists('/usr/bin/yum'):
            # 检查cronie是否已安装
            result = subprocess.run(['rpm', '-q', 'cronie'], capture_output=True, text=True)
            if 'is not installed' not in result.stdout:
                write_log("Crontab服务已安装")
                return
            result = subprocess.run(['yum', 'install', '-y', 'cronie', '--disablerepo=centos-sclo-rh'], check=True)
            if result.returncode != 0:
                update_sources()
            subprocess.run(['yum', 'install', '-y', 'cronie', '--disablerepo=centos-sclo-rh'], check=True)
        write_log("Crontab服务安装成功")
    except subprocess.CalledProcessError as e:
        write_log("安装crontab服务失败: {}".format(e))

# 启动crontab服务
def start_service():
    write_log("启动crontab服务...")
    try:
        service_name = 'crond'
        if os.path.exists('/usr/bin/apt-get'):
            service_name = 'cron'
        subprocess.run(['systemctl', 'start', service_name], check=True)
        write_log("Crontab服务启动成功")
    except subprocess.CalledProcessError as e:
        write_log("启动crontab服务失败: {}".format(e))

# 获取系统服务文件路径
def get_service_file_path(service_name):
    if os.path.exists('/usr/bin/apt-get'):
        return "/lib/systemd/system/{}.service".format(service_name)
    elif os.path.exists('/usr/lib/systemd/system'):
        return "/usr/lib/systemd/system/{}.service".format(service_name)
    return None

# 检查crontab服务状态
def check_service_status():
    write_log("检查crontab服务状态...")
    service_name = 'crond'
    try:
        if os.path.exists('/usr/bin/apt-get'):
            service_name = 'cron'
        service_file = get_service_file_path(service_name)
        if service_file and not os.path.exists(service_file):
            write_log("检查到系统未安装crontab,开始执行安装操作...")
            return False
        result = subprocess.run(['systemctl', 'status', service_name], capture_output=True, text=True)
        if 'active (running)' in result.stdout:
            write_log("系统的Crontab服务正在运行")
            return True
        else:
            write_log("系统的Crontab服务未运行,开始执行启动操作...")
            return False
    except subprocess.CalledProcessError as e:
        write_log("检查crontab服务状态失败: {}".format(e))
        return False

# 解析crontab任务并注释掉错误的行
def parse_crontab(crontab_path):
    write_log("解析crontab任务: {}".format(crontab_path))
    try:
        result = subprocess.check_output(['crontab', '-l'], text=True)
        lines = result.splitlines()
    except Exception as e:
        write_log("检查crontab文件失败，请检查是否开了系统加固")
        exit(1)

    cron_jobs = []
    corrected_lines = []
    for line in lines:
        if line.strip() and not line.startswith('#'):
            parts = line.split()
            if len(parts) < 6 or not is_valid_cron_time(parts[:5]):
                write_log("无效的crontab行: {}，已注释".format(line.strip()))
                corrected_lines.append("# " + line)
                continue
            schedule = " ".join(parts[:5])
            command = " ".join(parts[5:])
            cron_jobs.append((schedule, command))
            corrected_lines.append(line)
        else:
            corrected_lines.append(line)
    
    # 更新crontab文件
    try:
        with open('/tmp/temp_cron', 'w') as f:
            f.write("\n".join(corrected_lines) + "\n")
        subprocess.run(['crontab', '/tmp/temp_cron'])
        write_log("crontab文件更新成功")
    except Exception as e:
        write_log("写入crontab文件失败: {}".format(e))
        write_log("检查crontab文件失败，请检查是否开了系统加固")
        exit(1)

    return cron_jobs

def is_valid_cron_time(parts):
    write_log("验证crontab时间格式: {}".format(parts))
    for part in parts:
        if part != '*' and not part.isdigit() and not (part.startswith('*/') and part[2:].isdigit()):
            return False
    return True

# 创建临时crontab任务
def create_temp_crontab(crontab_path):
    temp_cron_command = '/bin/echo "Crontab test executed" >> /tmp/crontab_test.log'
    cron_entry = "* * * * * " + temp_cron_command + "\n"
    
    # 读取当前crontab
    try:
        current_crontab = subprocess.check_output(['crontab', '-l']).decode('utf-8')
    except subprocess.CalledProcessError:
        write_log("没有找到当前的crontab任务")
        current_crontab = ""
    
    # 将临时任务添加到crontab中
    try:
        with open(crontab_path, 'w') as f:
            f.write(current_crontab)
            f.write(cron_entry)
        subprocess.run(['crontab', crontab_path])
        write_log("临时crontab任务已创建")
    except Exception as e:
        write_log("写入crontab文件失败: {}".format(e))
        write_log("请检查是否开了系统加固")
        exit(1)

# 检查临时crontab任务是否执行
def check_temp_crontab_log():
    log_file = '/tmp/crontab_test.log'
    write_log("等待70秒，确保临时任务有时间执行")
    time.sleep(70)  # 等待70秒，确保任务有时间执行
    
    if os.path.exists(log_file):
        write_log("检查临时crontab任务日志...")
        with open(log_file, 'r') as f:
            logs = f.readlines()
        for log in logs:
            if "Crontab test executed" in log:
                write_log("临时crontab任务已成功执行")
                return True
    write_log("临时crontab任务未执行")
    return False

# 删除临时crontab任务
def delete_temp_crontab(crontab_path):
    write_log("删除临时crontab任务...")
    temp_cron_command = '/bin/echo "Crontab test executed" >> /tmp/crontab_test.log'
    
    # 读取当前crontab
    try:
        current_crontab = subprocess.check_output(['crontab', '-l']).decode('utf-8')
    except subprocess.CalledProcessError as e:
        write_log("没有找到当前的crontab任务")
        current_crontab = ""
    
    # 删除临时任务
    new_crontab = [line for line in current_crontab.splitlines() if temp_cron_command not in line]
    
    # 更新crontab
    try:
        with open(crontab_path, 'w') as f:
            f.write('\n'.join(new_crontab) + '\n')
        subprocess.run(['crontab', crontab_path])
        write_log("临时crontab任务已删除")
    except Exception as e:
        write_log("写入crontab文件失败: {}".format(e))
        write_log("请检查是否开了系统加固")
        exit(1)
    
    # 删除临时日志文件
    if os.path.exists('/tmp/crontab_test.log'):
        write_log("删除临时日志文件")
        os.remove('/tmp/crontab_test.log')

def modify_status_flag():
    flag_path = '/tmp/crontab_service_status.flag'
    with open(flag_path, 'w') as f:
        f.write("1")

def main():
    write_log("开始修复crontab服务...")
    crontab_path = get_cron_file()
    
    # 步骤1：检查服务是否安装，否则安装
    write_log("开始检查crontab服务是否安装")
    if not check_service_status():
        install_service()
    
    # 步骤2：检查服务是否运行，否则启动服务
    write_log("开始检查crontab服务是否运行")
    if not check_service_status():
        start_service()
    
    # 步骤3：检查服务是否运行且健康
    write_log("开始检查crontab服务是否正常")
    if not check_service_status():
        write_log("crontab服务未运行或不健康，修复失败")
        return
    
    # 步骤4：检查crontab文件是否正常，并注释掉错误的行
    write_log("开始检查crontab文件是否正常")
    cron_jobs = parse_crontab(crontab_path)
    if not cron_jobs:
        write_log("未找到有效的crontab任务")
    
    # 步骤5：创建并检查临时crontab任务
    write_log("开始创建一条临时crontab任务做测试，执行周期为1分钟，请耐心等候...")
    create_temp_crontab(crontab_path)
    if check_temp_crontab_log():
        delete_temp_crontab(crontab_path)
    else:
        write_log("crontab服务修复失败")
        return 
    modify_status_flag()
    write_log("服务修复完成！")

if __name__ == "__main__":
    main()
