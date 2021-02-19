#!/usr/bin/python
# coding: utf-8
"""

author: linxiao
date: 2021/1/23 9:45
"""
from random import choice

from colony import mysql
import public
from .ssh_client import ssh_client


class dbnode:
    __ssh_client = None
    __sql_client = None
    __settings = {}

    master_priority = 0  # 设置为备用主节点的优先级

    def __init__(self):
        # self.__settings = settings
        return

    def init_host(self, settings=None):
        """初始化主机"""
        if self.__ssh_client is None:
            if not settings:
                settings = self.__settings

            host = ssh_client(
                settings["host"],
                settings["port"],
                settings["root"],
                settings["password"])
            host.connect_ssh()
            self.__ssh_client = host

    def exec_command(self, command, multi_line=False):
        """远程主机执行命令

        multi_line: 是否执行多行命令, 多行命令每行用“;”分隔。
        return: 小写标准输出
        """
        try:
            stdout, stderr = self.__ssh_client.exec_command(command,
                                                            get_pty=multi_line)
            res = stdout
            return public.returnMsg(True, res)
        except Exception as e:
            print("执行命令: {} 出现错误:".format(command))
            print(e)
            return public.returnMsg(False, str(e))

    def get_mysql_option(self, key, config_file="/etc/my.cnf"):
        """读取my.cnf配置文件，获取对应的配置项"""
        command = "sed -n '/^{key}\s*=/p' {file};".format(
            key=key,
            file=config_file
        )
        result = self.exec_command(command)
        status = result['status']
        res = result['msg']
        if status and res:
            if res.find("=") != -1:
                _key, _value = res.split("=")
                if _key.strip() == key:
                    return _value.strip()
            else:
                return res.strip()
        return ""

    def write_mysql_option(self, section, key, value, config_file="/etc/my.cnf"):
        """往mysql配置文件中写入配置

        如果存在key选项，忽略[section]定位，直接执行替换该行配置；
        如果不存在，在[section]的下一行写入配置选项。

        return: True/False 是否替换成功
        """
        value = str(value)
        option = key + " = " + value
        command = \
            "num=$(sed -n '/^{key}\s*=/=' {file});" \
            "if [[ \"$num\" -gt 0 ]];" \
            "then " \
            "sed -i \"$num\"\"c {option}\" {file};" \
            "echo `sed -n '/^{key}\s*=/p' {file}`;" \
            "else " \
            "sed -i '/\[{section}\]/ a\\{option}' {file};" \
            "echo `sed -n '/^{key}\s*=/p' {file}`;" \
            "fi".format(file=config_file,
                        section=section,
                        key=key,
                        option=option)
        result = self.exec_command(command, multi_line=True)
        status = result['status']
        res = result['msg']
        if status and res:
            _key, _value = res.split("=")
            if _key.strip() == key and _value.strip() == value:
                return True
        return False

    def remove_option(self, key, config_file="/etc/my.cnf"):
        """删除mysql配置选项"""
        command = \
            "sed -i '/^{key}\s*=/d' {file};" \
            "sed -n '/^{key}\s*=/p' {file};".format(
                file=config_file,
                key=key)
        stdin, stdout, stderr = self.exec_command(command, multi_line=True)
        res = stdout.read().decode("utf-8").lower()
        res = res.strip()
        if not res:
            return True
        return False

    def mysql_service_is_started(self):
        """检查数据库服务是否开启"""
        print("正在检查mysql服务...")
        result = self.exec_command("service mysqld status")
        status = result['status']
        res = result['msg']
        if status and res.find("success") != -1:
            print("mysql服务已启动。")
            return True
        print("mysql服务未启动。")
        return False

    def start_mysql_service(self):
        """开启mysql服务"""
        print("正在开启mysql服务...")
        command = "service mysqld start"
        result = self.exec_command(command)
        status = result['status']
        res = result['msg']
        if status and res.find("success") != -1:
            print("mysql服务开启成功。")
            return True
        print("mysql服务开启失败！")
        return False

    def stop_mysql_service(self):
        """停止mysql服务"""
        print("停止mysql服务...")
        result = self.exec_command("service mysqld stop")
        status = result['status']
        res = result['msg']
        if status and res.find("success") != -1:
            print("mysql服务已停止。")
            return True
        print("mysql停止失败！")
        return False

    def init_mysql(self, settings):
        """初始化数据库"""
        self.host = settings['host']
        self.port = settings['port']
        self.db_name = settings['name']
        self.username = settings['username']
        self.password = settings['password']

        self.__sql_client = mysql.mysql().set_host(
            self.host,
            self.port,
            self.db_name,
            self.username,
            self.password)

    def generate_pass(self, length=16):
        """生成指定位数的随机密码"""
        password = []
        char_set = {
            'small': 'abcdefghijklmnopqrstuvwxyz',
            'nums': '0123456789',
            'big': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        }

        def check_prev_char(password, current_char_set):
            """检查密码是否重复"""
            index = len(password)
            if index == 0:
                return False
            else:
                prev_char = password[index - 1]
                if prev_char in current_char_set:
                    return True
                else:
                    return False

        while len(password) < length:
            key = choice(list(char_set.keys()))
            a_char = choice(char_set[key])
            if check_prev_char(password, char_set[key]):
                continue
            else:
                password.append(a_char)
        return ''.join(password)

    def create_db_user_if_not_exists(self, username):
        """创建数据库用户，如果用户不存在"""
        pass

    def deploy(self, settings):
        """数据库节点部署
        
        1. 获得主机管理员权限。 使用ssh登录到主机。
        2. 初始化mysql管理员用户。为管理端主机添加一个管理员账号，后续操作都通过该账号进行。
        3. 以管理员用户身份连接到mysql。
        4. 创建复制账号，写入主主复制配置。
        """
        host = settings['host']
        port = settings['port']
        manager_user = settings['db_manager_user']
        replication_user = settings['db_replication_user']

        if self.connectable(host, port):
            self.init_host(settings)
            if not self.mysql_service_is_started():
                self.start_mysql_service()

                if not self.mysql_service_is_started():
                    return public.returnMsg(False, "Mysql服务无法启动！")

            # 初始化mysql
            print("正在初始化管理员账户:{}".format(manager_user))
            self.stop_mysql_service()
            self.write_mysql_option("mysqld", "skip-grant-tables", "on")
            self.start_mysql_service()
            if self.mysql_service_is_started():
                # 确定 mysql 库是否支持空用户连接
                # generate password & update root password
                mysql_port = 3306
                try:
                    mysql_port_option = self.get_mysql_option("port")
                    if mysql_port_option.isdigit():
                        mysql_port = int(mysql_port_option)
                except:
                    mysql_port = 3306

                if not self.connectable(host, mysql_port):
                    return public.returnMsg(False, "Mysql服务无法连接，请检查地址是否正确或者端口({})是否开启。".format(mysql_port))

                tmp_settings = {
                    "host": host,
                    "port": mysql_port,
                    "name":"",
                    "username":"",
                    "password":"",
                }
                self.init_mysql(tmp_settings)
                result = self.__sql_client.execute("select host, user from mysql.user where user='root'")
                return public.returnMsg(True, result)
                # remove skip-grant-tables option
                # restart mysql service
                # 确认密码修改成功

            return public.returnMsg(True, "数据库节点部署成功！")
        else:
            return public.returnMsg(False, "主机:{} 无法连接！".format(host))

    def connectable(self, host, port):
        """检查主机是否可连接"""
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, int(port)))
            s.shutdown(2)
            return True
        except Exception as e:
            print(e)
            return False

    def get_run_status(self, get):
        """获取MySQL运行状态"""

        import time
        result = {}
        if not self.host_connected:
            return public.returnMsg(False, "节点主机无法连接！")
        data = self.__sql_client.query('show global status', is_close=False)
        gets = ['Max_used_connections',  # 活动连接数  
                'Connections',  # 最大连接数
                'Com_commit',  # 事务提交量
                'Com_rollback',
                # 事务回滚量 TPS = (Com_commit + Com_rollback) / Seconds
                'Queries',  # 每秒查询量QPS
                'Innodb_buffer_pool_reads',
                # Innodb Buffer 命中率 (1-Innodb_buffer_pool_reads/Innodb_buffer_pool_read_requests)*100%
                'Innodb_buffer_pool_read_requests',
                'Key_reads',
                # Key Buffer 读命中率 (1-Key_reads/Key_read_requests)*100%
                'Key_read_requests',
                'Key_writes',
                # Key Buffer 写命中率 (1-Key_writes/Key_write_requests)*100%
                'Key_write_requests',
                'Qcache_hits',
                # Query Cache 命中率 (Qcache_hits/(Qcache_hits+Qcache_inserts))*100%
                'Qcache_inserts',  #
                'Bytes_received',  # 接收字节数
                'Bytes_sent',  # 发送字节数
                'Aborted_clients',
                'Aborted_connects',
                'Created_tmp_disk_tables',
                # Tmp Table 状况 (Created_tmp_disk_tables/Created_tmp_tables)*100%
                'Created_tmp_tables',
                'Innodb_buffer_pool_pages_dirty',  # 当前的脏页数
                'Opened_files',  # 当前打开的文件数量
                'Open_tables',
                # Table Cache 状态量 (Open_tables/Opened_tables)*100%
                'Opened_tables',
                'Select_full_join',  # 没有使用索引的联接查询数量。如果该值不为0,应仔细检查表的索引。
                'Select_range_check',
                # 在每一行数据后对键值进行检查的不带键值的联接的数量。如果不为0，应仔细检查表的索引。
                'Sort_merge_passes',
                # 排序后的合并次数。如果这个变量值较大，应考虑增加sort_buffer_size系统变量的值。
                'Table_locks_waited',  # 锁表次数 TODO 确定数据是否准确
                'Innodb_row_lock_waits',  # new
                'Table_locks_immediate',  # new
                'Threads_cached',
                'Threads_connected',
                'Threads_created',
                # Thread Cache 命中率 (1-Threads_created/Connections)*100%
                'Threads_running',
                'Uptime',
                "Binlog_cache_disk_use",  # Binlog Cache使用状况
                "Binlog_cache_use",
                "Innodb_log_waits",
                ]
        try:
            if data[0] == 1045:
                return public.returnMsg(False, 'MySQL密码错误!')
        except:
            pass

        for d in data:
            for g in gets:
                try:
                    if d[0] == g: result[g] = d[1]
                except:
                    pass
        if not 'Run' in result and result:
            result['Run'] = int(time.time()) - int(result['Uptime'])
        tmp = self.__sql_client.query('show master status', is_close=False)
        try:

            result['File'] = tmp[0][0]
            result['Position'] = tmp[0][1]
        except:
            result['File'] = 'Unknown'
            result['Position'] = 'Unknown'

        # 空间碎片率(百分比)
        tmp2 = self.__sql_client.query('USE INFORMATION_SCHEMA;', is_close=False)
        tmp2 = self.__sql_client.query(
            'SELECT SUM(DATA_LENGTH), SUM(INDEX_LENGTH), SUM(DATA_FREE) FROM `TABLES`',
            is_close=False)
        try:
            debris_rate = (float(
                tmp2[0][2] / (tmp2[0][0] + tmp2[0][1] + tmp2[0][2]))) * 100
            result['Space_debris_rate'] = debris_rate
        except:
            result['Space_debris_rate'] = 0.0

        tmp3 = self.__sql_client.query("show slave status", is_close=False)
        try:
            result["Slave_IO_State"] = tmp3[0][0]
            result['Slave_IO_Running'] = tmp3[0][10]
            result['Slave_SQL_Running'] = tmp3[0][11]
        except:
            result["Slave_IO_State"] = ""
            result['Slave_IO_Running'] = "Unknown"
            result['Slave_SQL_Running'] = "Unknown"

        tmp4 = self.__sql_client.query(
            "select SUM(current_alloc) as current_alloc from sys.x$memory_global_by_current_bytes;",
            is_close=False)
        # tmp4 = self.__sql.query("select * from sys.memory_global_tota", is_close=False)
        try:
            result["Total_Allocated"] = float(tmp4[0][0])
        except:
            result["Total_Allocated"] = -1
        self.__sql_client.close()
        return result
