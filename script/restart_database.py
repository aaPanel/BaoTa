import subprocess
import os
def check_mysql_status():
    if not os.path.exists("/usr/bin/ps"):
        print("无法使用ps命令获取mysql状态 请联系宝塔技术人员")
        return True
    try:
        command = "ps -ef | grep mysqld | grep /www/server/mysql | grep -v grep"
        result = subprocess.run(
                command, 
                shell=True, 
                text=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
        return bool(result.stdout.strip())
    except Exception as e:
        print("无法使用获取mysql状态 请联系宝塔技术人员")
        return True

def start_mysql():
    try:
        result = subprocess.run(
            ['/etc/init.d/mysqld', 'start'], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        if result.returncode == 0:
            print("MySQL started successfully.")
        else:
            print("MySQL启动失败！")
            print("Error output:", result.stderr)
    except FileNotFoundError:
        print("Error: mysql启动文件找不到")
    except Exception as e:
        print(f"出现错误: {e}")

if not check_mysql_status():
    start_mysql()