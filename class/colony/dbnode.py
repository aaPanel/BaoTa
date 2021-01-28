#!/usr/bin/python
# coding: utf-8
"""

author: linxiao
date: 2021/1/23 9:45
"""
from colony import mysql
import public


class dbnode:
    __host = None
    __sql = None
    __settings = {}

    master_priority = 0  #  设置为备用主节点的优先级

    def __init__(self):
        # self.__settings = settings
        return 

        

    def init_host(self, settings=None):
        """初始化主机"""
        if self.__host is None:
            if not settings:
                settings = self.__settings

            import paramiko
            host = paramiko.SSHClient()
            host.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            host.connect(
                hostname=settings["host"],
                port=settings["port"],
                username=settings["root"],
                password=settings["password"]
            )
            self.__host = host

    def exec_command(self, command):
        """远程主机执行命令
        
        return: 小写标准输出
        """
        stdin, stdout, stderr = self.__host.exec_command(command)
        res = stdout.read().decode("utf-8").lower()
        return res 

    def mysql_service_is_started(self):
        # 检查数据库服务是否开启
        res = self.__host.exec_command("service mysqld status")
        if res.find("success") != -1:
            return True
        return False

    def start_mysql_service(self):
        """开启mysql服务"""
        res = self.__host.exec_command("service mysqld start")
        if res.find("success") != -1:
            return True
        return False

    def init_mysql(self, settings):
        """初始化数据库"""
        self.host = settings['host']
        self.port = settings['port']
        self.db_name = settings['name']
        self.username = settings['username']
        self.password = settings['password']

        self.__sql = mysql.mysql().set_host(
            self.host,
            self.port,
            self.db_name,
            self.username,
            self.password)

    def deploy(self, settings):
        """数据库节点部署
        
        1. 获得主机管理员权限。 使用ssh登录到主机。
        2. 初始化mysql管理员用户。为管理端主机添加一个管理员账号，后续操作都通过该账号进行。
        3. 以管理员用户身份连接到mysql。
        4. 创建复制账号，写入主主复制配置。
        """
        if self.connectable(settings['host'], settings['port']):
            self.init_host(settings)
            if not self.mysql_service_is_started():
                self.start_mysql_service()

                if not self.mysql_service_is_started():
                    return public.returnMsg(False, "Mysql服务无法启动！")

            # 初始化mysql
            return public.returnMsg(True, "数据库节点部署成功！")

                
            
        else:
            return public.returnMsg(False, "主机无法连接！")


    def connectable(self, host, port):
        """检查主机是否可连接"""
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.host, int(self.port)))
            s.shutdown(2)
            return True
        except:
            return False

    def get_run_status(self,get):
        """获取MySQL运行状态"""

        import time
        result = {}
        if not self.host_connected:
            return public.returnMsg(False, "节点主机无法连接！")
        data = self.__sql.query('show global status', is_close=False)
        gets = ['Max_used_connections',  # 活动连接数  
                'Connections',  #  最大连接数
                'Com_commit',  #  事务提交量 
                'Com_rollback',  #  事务回滚量 TPS = (Com_commit + Com_rollback) / Seconds
                'Queries',  #  每秒查询量QPS
                'Innodb_buffer_pool_reads',  #  Innodb Buffer 命中率 (1-Innodb_buffer_pool_reads/Innodb_buffer_pool_read_requests)*100%
                'Innodb_buffer_pool_read_requests',
                'Key_reads',  #  Key Buffer 读命中率 (1-Key_reads/Key_read_requests)*100%
                'Key_read_requests',
                'Key_writes',  #  Key Buffer 写命中率 (1-Key_writes/Key_write_requests)*100%
                'Key_write_requests',
                'Qcache_hits',  #  Query Cache 命中率 (Qcache_hits/(Qcache_hits+Qcache_inserts))*100%
                'Qcache_inserts',  #  
                'Bytes_received',  #  接收字节数
                'Bytes_sent',  #  发送字节数
                'Aborted_clients',
                'Aborted_connects',
                'Created_tmp_disk_tables',  # Tmp Table 状况 (Created_tmp_disk_tables/Created_tmp_tables)*100%
                'Created_tmp_tables',
                'Innodb_buffer_pool_pages_dirty',  #  当前的脏页数
                'Opened_files',  #  当前打开的文件数量
                'Open_tables',  #  Table Cache 状态量 (Open_tables/Opened_tables)*100%
                'Opened_tables',
                'Select_full_join',  #  没有使用索引的联接查询数量。如果该值不为0,应仔细检查表的索引。
                'Select_range_check',  #  在每一行数据后对键值进行检查的不带键值的联接的数量。如果不为0，应仔细检查表的索引。
                'Sort_merge_passes',  # 排序后的合并次数。如果这个变量值较大，应考虑增加sort_buffer_size系统变量的值。
                'Table_locks_waited',  #  锁表次数 TODO 确定数据是否准确
                'Innodb_row_lock_waits',  # new
                'Table_locks_immediate',  # new
                'Threads_cached',
                'Threads_connected',
                'Threads_created',  #  Thread Cache 命中率 (1-Threads_created/Connections)*100%
                'Threads_running',
                'Uptime',
                "Binlog_cache_disk_use",  #  Binlog Cache使用状况
                "Binlog_cache_use",
                "Innodb_log_waits",
                ]
        try:
            if data[0] == 1045:
                return public.returnMsg(False,'MySQL密码错误!')
        except:pass

        for d in data:
            for g in gets:
                try:
                    if d[0] == g: result[g] = d[1]
                except:
                    pass
        if not 'Run' in result and result:
            result['Run'] = int(time.time()) - int(result['Uptime'])
        tmp = self.__sql.query('show master status', is_close=False)
        try:

            result['File'] = tmp[0][0]
            result['Position'] = tmp[0][1]
        except:
            result['File'] = 'Unknown'
            result['Position'] = 'Unknown'

        # 空间碎片率(百分比)
        tmp2 = self.__sql.query('USE INFORMATION_SCHEMA;', is_close=False)
        tmp2 = self.__sql.query('SELECT SUM(DATA_LENGTH), SUM(INDEX_LENGTH), SUM(DATA_FREE) FROM `TABLES`', is_close=False)
        try:
            debris_rate = (float(tmp2[0][2] / (tmp2[0][0] + tmp2[0][1] + tmp2[0][2])))*100
            result['Space_debris_rate'] =  debris_rate
        except:
            result['Space_debris_rate'] =  0.0

        tmp3 = self.__sql.query("show slave status", is_close=False)
        try:
            result["Slave_IO_State"] = tmp3[0][0]
            result['Slave_IO_Running'] = tmp3[0][10]
            result['Slave_SQL_Running'] = tmp3[0][11] 
        except:
            result["Slave_IO_State"] = ""
            result['Slave_IO_Running'] = "Unknown"
            result['Slave_SQL_Running'] = "Unknown"

        tmp4 = self.__sql.query("select SUM(current_alloc) as current_alloc from sys.x$memory_global_by_current_bytes;", is_close=False)
        # tmp4 = self.__sql.query("select * from sys.memory_global_tota", is_close=False)
        try:
            result["Total_Allocated"] = float(tmp4[0][0])
        except:
            result["Total_Allocated"] = -1
        self.__sql.close()
        return result
