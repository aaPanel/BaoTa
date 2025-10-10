# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wuwei <bt_wuwei@qq.com>
# -------------------------------------------------------------------
import os
import re
import sys
import traceback
import math

import projectModel.bt_docker.dk_public as dp
import public
from databaseModel.pgsqlModel import panelPgsql
from databaseModel.redisModel import panelRedisDB
from monitorModel.base import monitorBase
from panelMysql import panelMysql


# ------------------------------
# 常用软件状态
# ------------------------------


class main(monitorBase):
    """
    常用软件负载情况检测
    """
    soft_introduction = {
        'nginx': "Nginx是一个高性能的HTTP和反向代理web服务器，轻量级，占有内存少，并发能力强。",
        'mysqld_safe': "MySQL是一种关系数据库管理系统。",
        'redis-server': "Redis是一个高性能的key-value数据库。",
        'mongod': "Mongod 基于分布式文件存储的数据库，旨在为WEB应用提供可扩展的高性能数据存储解决方案。",
        'postgres': "PostgreSQL 是一个免费的对象-关系数据库服务器。",
        'memcached': "Memcached 是一个高性能的分布式内存对象缓存系统。",
        'httpd': "Apache 一个安全，高效且可扩展的服务器，该服务器提供与当前HTTP标准同步的HTTP服务。",
        'pure-ftpd': "PureFTP是一款专注于程序健壮和软件安全的免费FTP服务器软件。",
        'jsvc': "Tomcat 开发和调试JSP程序的首选。",
        'dockerd': "Docker 是一个开源的应用容器引擎。",
    }
    statusOption = {"0": "stop", "1": "start", "2": "restart"}
    ROWS = 5
    sys.path.insert(0, 'class/')
    from system import system
    syst = system()

    def __init__(self):
        self.docker_obj = self.docker_client()

    # 获取软件负载的总调度函数
    def get_status(self, get):
        """
        获取常用软件负载情况总调度函数
        :param get:
        :type:服务类型
        :return:
        """
        try:
            if not hasattr(get, 'type'):
                return public.returnMsg(False, '参数传递错误，请重试!')
            sql_set = {
                "mysqld_safe": self.__get_mysql_status,
                "redis-server": self.__get_redis_status,
                "mongod": self.__get_mongo_status,
                "postgres": self.__get_pgsql_status,
                "nginx": self.__get_nginx_status,
                "memcached": self.__get_memcached_status,
                "httpd": self.__get_apache_status,
                "pure-ftpd": self.__get_ftp_status,
                "jsvc": self.__get_tomcat_status,
                "dockerd": self.__get_docker_status,
                'tomcat_info': self.__get_tomcat_usr_info
            }
            if get.type == 'tomcat_info':
                return self.__get_tomcat_usr_info()
            if 'redis' in get.type:
                get.type = "redis-server"
            if 'pure' in get.type:
                get.type = "pure-ftpd"
            installation = self.__is_installation(get.type)
            if get.type not in self.__get_sever_status_list():
                return {"status": False, "soft_introduction": self.soft_introduction.get(get.type),
                        'installation': installation}
            infos = {}
            infos['soft_info'] = sql_set.get(get.type)()
            pro = self.__get_process_status(get.type)
            infos['pro_info'] = pro['pro_info']
            infos['memory_info'] = pro['memory_info']
            infos["soft_introduction"] = self.soft_introduction[get.type]
            infos['status'] = True
            infos['installation'] = installation
            if get.type == 'dockerd':
                if not hasattr(get, 'limit'):
                    return public.returnMsg(False, '参数传递错误，请重试!')
                if not hasattr(get, 'p'):
                    return public.returnMsg(False, '参数传递错误，请重试!')
                containers_introduction = {}
                containers_introduction['running'] = len([k for k in infos['soft_info'] if
                                                          k['container_status'] == "正在运行"])
                containers_introduction['exited'] = len([k for k in infos['soft_info'] if
                                                         k['container_status'] == "停止"])
                containers_introduction['paused'] = len([k for k in infos['soft_info'] if
                                                         k['container_status'] == "暂停"])
                infos['containers_introduction'] = containers_introduction
                if hasattr(get, 'limit'):
                    self.ROWS = int(get.limit)
                # start = 0
                # if limit * (p - 1) > 0: start = limit * (p - 1)
                # end = limit * p
                # if limit * p > num: end = num + 1
                # now = "<div><span class='Pcurrent'>{}</span>".format(p)
                # last = "<a class='Pend' href='/monitor/soft/get_status?p={}&limit={}&type=dockerd''>上一页</a>".format(
                #     p - 1, limit, p - 1)
                # next = "<a class='Pend' href='/monitor/soft/get_status?p={}&limit={}&type=dockerd'>下一页</a>".format(
                #     p + 1, limit, p + 1)
                # nestst = "<a class='Pend' href='/monitor/soft/get_status?p={}&limit={}&type=dockerd''>尾页</a>".format(
                #     int(math.ceil(num / limit)), limit)
                # infos['soft_info'] = infos['soft_info'][start:end]

                res = self.get_page(infos['soft_info'], get)
                infos['page'] = res['page']
                infos['soft_info'] = res['data']
            return infos
        except:
            pass

    # 软件状态调整的总调度函数
    def sever_admin(self, get):
        try:
            if not hasattr(get, 'option'):
                return public.returnMsg(False, '参数传递错误，请重试!')
            service = {
                'mongod': self.__mongod_admin,
                'redis-server': self.__redis_admin,
                'memcached': self.__memcached_admin,
                'dockerd': self.__docker_admin,
                'jsvc': self.__tomcat_admin,
                'pure-ftpd': self.__ftp_admin,
                'httpd': self.__apache_admin,
                'mysqld_safe': self.__mysqld_admin,
                "nginx": self.__nginx_admin,
                "postgres": self.__pgsql_admin
            }
            if 'redis' in get.name:
                get.name = "redis-server"
            if 'pure' in get.name:
                get.name = "pure-ftpd"
            installation = self.__is_installation(get.name)
            if not installation:
                return public.returnMsg(False, "该服务未安装")
            return service.get(get.name, "未找到{}服务".format(get.name))(get.option)
        except:
            return public.returnMsg(False, "设置出错")

    def __is_installation(self, name):
        map = {
            "mysqld_safe": "/www/server/mysql/bin/mysqld_safe",
            "redis-server": "/www/server/redis/src/redis-server",
            "mongod": "/www/server/mongodb/bin",
            "postgres": "/www/server/pgsql/bin/postgres",
            "nginx": "/www/server/nginx/sbin/nginx",
            "memcached": "/usr/local/memcached/bin/memcached",
            "httpd": "/www/server/apache/bin/httpd",
            "pure-ftpd": "/www/server/pure-ftpd/bin",
            "jsvc": "/www/server/tomcat/bin/jsvc",
            "dockerd": "/usr/bin/dockerd",
            "php": "/www/server/php/",
            "tamper_proof": "/www/server/panel/plugin/tamper_proof",
            "bt_security": "/www/server/panel/plugin/bt_security",
            "syssafe": "/www/server/panel/plugin/syssafe",
            "tamper_proof_refactored": "/www/server/panel/plugin/tamper_proof_refactored",
        }
        if name in map:
            if name == 'php':
                if len(os.listdir(map[name])) > 0:
                    return True
            return os.path.exists(map[name])
        else:
            return False

    def __get_nginx_status(self):
        """
        获取nginx负载情况
        :return:{'soft_info':soft_info,'pro_info':pro_info,'memory_info':memory_info}
        """
        try:
            res = public.HttpGet("http://127.0.0.1/nginx_status")
            if res:
                numerical_name = ['active_connections', 'accepts', 'handled', 'requests', 'Reading', 'Writing',
                                  'Waiting']
                numerical_value = re.findall(r"\d+", res)
                soft_info = dict(zip(numerical_name, numerical_value))
                return soft_info
        except:
            return {"soft_info": "软件查询出错"}

    def __get_mysql_status(self):
        """
        获取MySQL数据库负载情况
        :return:{'soft_info':soft_info,'pro_info':pro_info,'memory_info':memory_info}
        """
        soft_info = {}
        try:
            mysql = panelMysql()
            data = mysql.query('show global status')
            gets = ['Max_used_connections', 'Com_commit', 'Com_rollback', 'Questions', 'Innodb_buffer_pool_reads',
                    'Innodb_buffer_pool_read_requests', 'Key_reads', 'Key_read_requests', 'Key_writes',
                    'Key_write_requests', 'Qcache_hits', 'Qcache_inserts', 'Bytes_received', 'Bytes_sent',
                    'Aborted_clients', 'Aborted_connects', 'Created_tmp_disk_tables', 'Created_tmp_tables',
                    'Innodb_buffer_pool_pages_dirty', 'Opened_files', 'Open_tables', 'Opened_tables',
                    'Select_full_join', 'Select_range_check', 'Sort_merge_passes', 'Table_locks_waited',
                    'Threads_cached', 'Threads_connected', 'Threads_created', 'Threads_running', 'Connections',
                    'Uptime']
            for d in data:
                for g in gets:
                    try:
                        if d[0] == g: soft_info[g] = d[1]
                    except:
                        pass
            # 计算命中率
            soft_info['Thread_cache_hit_ratio'] = round(
                (1 - int(soft_info['Threads_cached']) / int(soft_info['Connections'])) * 100, 2)
            try:
                soft_info['Index_hit_ratio'] = round(
                    (1 - int(soft_info['Key_reads']) / int(soft_info['Key_read_requests'])) * 100, 2)
            except:
                soft_info['Index_hit_ratio'] = 0
            soft_info['Innodb_index_hit_ratio'] = round(
                (1 - int(soft_info['Innodb_buffer_pool_reads']) / int(
                    soft_info['Innodb_buffer_pool_read_requests'])) * 100, 2)
            soft_info['Query_cache_hit_ratio'] = round(
                (1 - int(soft_info['Created_tmp_disk_tables']) / int(soft_info['Created_tmp_tables'])) * 100, 2)
            soft_info['Bytes_sent'] = public.to_size(soft_info['Bytes_sent'])
            soft_info['Bytes_received'] = public.to_size(soft_info['Bytes_received'])
            seconds = int(soft_info['Uptime'])
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            soft_info['Uptime'] = "%d小时%02d分钟%02d秒" % (h, m, s)
            return soft_info
        except:
            return {"soft_info": "无数据库"}

    def __get_redis_status(self):
        """
        获取redis的服务信息，进程信息，内存信息
        :return:{'soft_info':soft_info,'pro_info':pro_info,'memory_info':memory_info}
        """
        try:
            soft_info = {}
            redis_db = panelRedisDB()
            redis_cnn = redis_db.redis_conn()
            r = redis_cnn.info()
            redis_info_item = [
                'tcp_port',
                'uptime_in_days',  # 已运行天数
                'connected_clients',  # 连接的客户端数量
                'used_memory',  # Redis已分配的内存总量
                'used_memory_rss',  # Redis占用的系统内存总量
                'used_memory_peak',  # Redis所用内存的高峰值
                'mem_fragmentation_ratio',  # 内存碎片比率
                'total_connections_received',  # 运行以来连接过的客户端的总数量
                'total_commands_processed',  # 运行以来执行过的命令的总数量
                'instantaneous_ops_per_sec',  # 服务器每秒钟执行的命令数量
                'keyspace_hits',  # 查找数据库键成功的次数
                'keyspace_misses',  # 查找数据库键失败的次数
                'latest_fork_usec'  # 最近一次 fork() 操作耗费的毫秒数
            ]
            for i, j in r.items():
                if i in redis_info_item:
                    soft_info[str(i)] = str(j)
            soft_info['used_memory'] = public.to_size(soft_info['used_memory'])
            soft_info['used_memory_rss'] = public.to_size(soft_info['used_memory_rss'])
            soft_info['used_memory_peak'] = public.to_size(soft_info['used_memory_peak'])
            return soft_info
        except:
            return {"soft_info": "软件查询出错"}

    def __get_mongo_status(self):
        """
        获取mongo数据库负载信息
        :return:{'soft_info':soft_info,'pro_info':pro_info,'memory_info':memory_info}
        """
        try:
            import pymongo
        except:
            os.system("btpip install pymongo")
            import pymongo
        try:
            soft_info = {}
            # 连接 MongoDB 服务器
            client = pymongo.MongoClient('mongodb://localhost:27017')
            sa_path = '{}/data/mongo.root'.format(public.get_panel_path())
            if os.path.exists(sa_path):
                pwd = public.readFile(sa_path)
                client.admin.authenticate("root", pwd)
            else:
                pass
            # 执行 serverStatus 命令
            status = client.admin.command('serverStatus')
            db_stats = client.mydb.command('dbStats')
            soft_info["version"] = client.server_info()['version']
            soft_info["now_connection"] = status['connections']['current']
            soft_info["maximum_connection"] = status['connections']['available']
            soft_info["query_num"] = status['opcounters']['query']
            soft_info["insert_num"] = status['opcounters']['insert']
            soft_info["update_num"] = status['opcounters']['update']
            soft_info["delete_num"] = status['opcounters']['delete']
            soft_info["hit_times"] = status['opcounters']['query']
            soft_info["misses_hit"] = soft_info["query_num"] - soft_info["hit_times"]
            soft_info["dataSize"] = db_stats['dataSize']
            soft_info["storageSize"] = db_stats['storageSize']
            soft_info["resident"] = public.to_size(status['mem']['resident'])
            return soft_info
        except:
            return {"soft_info": "软件查询出错"}

    def __get_pgsql_status(self):
        """
        获取pgsql的服务信息，进程信息，内存信息
        :return: {'soft_info':soft_info,'pro_info':pro_info,'memory_info':memory_info}
        """
        try:
            soft_info = {}
            pgsql = panelPgsql()
            datas = pgsql.query(
                "select datid,datname,numbackends,xact_commit,xact_rollback,blks_read,blks_hit,tup_inserted,tup_fetched,deadlocks,stats_reset from pg_stat_database where datname='postgres'")
            keys = ['datid', 'datname', 'numbackends', 'xact_commit', 'xact_rollback', 'blks_read', 'blks_hit',
                    'tup_inserted', 'tup_fetched', 'deadlocks', 'stats_reset']
            soft_info = dict(zip(keys, list(datas[0])))
            soft_info['stats_reset'] = soft_info['stats_reset'].strftime("%Y-%m-%d %H:%M:%S")
            return soft_info
        except:
            return {"soft_info": "软件查询出错"}

    def __get_memcached_status(self):
        """
        获取memcached的服务信息，进程信息，内存信息
        :return: {'soft_info':soft_info,'pro_info':pro_info,'memory_info':memory_info}
        """
        try:
            import telnetlib, re;
            conf = public.readFile('/etc/init.d/memcached')
            result = {}
            result['bind'] = re.search('IP=(.+)', conf).groups()[0]
            result['port'] = int(re.search('PORT=(\d+)', conf).groups()[0])
            result['maxconn'] = int(re.search('MAXCONN=(\d+)', conf).groups()[0])
            result['cachesize'] = int(re.search('CACHESIZE=(\d+)', conf).groups()[0])
            try:
                tn = telnetlib.Telnet(result['bind'], result['port'])
            except:
                raise public.PanelError('获取负载状态失败，请检查服务是否启动!')
            tn.write(b"stats\n")
            tn.write(b"quit\n")
            data = tn.read_all()
            if type(data) == bytes: data = data.decode('utf-8')
            data = data.replace('STAT', '').replace('END', '').split("\n")
            res = ['cmd_get', 'get_hits', 'get_misses', 'limit_maxbytes', 'curr_items', 'bytes', 'evictions',
                   'limit_maxbytes', 'bytes_written', 'bytes_read', 'curr_connections'];
            for d in data:
                if len(d) < 3: continue
                t = d.split()
                if not t[0] in res: continue
                result[t[0]] = int(t[1])
            result['hit'] = 1
            if result['get_hits'] > 0 and result['cmd_get'] > 0:
                result['hit'] = float(result['get_hits']) / float(result['cmd_get']) * 100
            result['bytes_read'] = public.to_size(result['bytes_read'])
            result['bytes_written'] = public.to_size(result['bytes_written'])
            result['limit_maxbytes'] = public.to_size(result['limit_maxbytes'])
            return result
        except:
            return {"soft_info": "软件查询出错"}

    def __get_apache_status(self):
        """
        获取apache的服务信息，进程信息，内存信息
        :return:{'soft_info':soft_info,'pro_info':pro_info,'memory_info':memory_info}
        """
        try:
            import apache
            a = apache.apache()
            a = a.GetApacheStatus()
            soft_info = {}
            for key, value in a.items():
                soft_info['apache_' + key] = value
            return soft_info
        except:
            return {"soft_info": "软件查询出错"}

    def __get_ftp_status(self):
        """
        获取ftp的连接情况，进程信息，内存信息
        :return: {'soft_info':soft_info,'pro_info':pro_info,'memory_info':memory_info}
        """
        soft_info = {}
        try:
            import subprocess
        except:
            os.system('ptpip install subprocess')
            import subprocess
        # 查看 Pure-FTPd 的服务器连接状态 -- 很慢
        # result = subprocess.check_output(['/www/server/pure-ftpd/sbin/pure-ftpwho', '-s'])
        # datas = result.decode().split('\n')[:-1]
        # if datas != []:
        #     for infos in datas:
        #         info = infos.split("|")
        #         content = {}
        #         content['proc_ID'] = info[0]
        #         content['login_usr'] = info[1]
        #         content['connection_statu'] = info[2]
        #         content['connection_port'] = info[-5]
        #         content['upload'] = info[-4]
        #         content['download'] = info[-3]
        #         content['downlaod_files_num'] = info[-2]
        #         content['uplaod_files_num'] = info[-1]
        #         soft_info[info[5]] = content
        try:
            file = '/www/server/pure-ftpd/etc/pure-ftpd.conf'
            conf = public.readFile(file)
            conf = conf.split("\n")
            info = []
            info1 = []
            [info.append(i) for i in conf if i != '']  # 去除空行
            [info1.append(i) for i in info if i[0] != '#']  # 去除注释
            [soft_info.update({i.split(" ")[0]: i.split(" ")[-1]}) for i in info1]
            return soft_info
        except:
            return {'soft_info': '软件信息查询出错'}

    def __get_tomcat_status(self):
        """
        获取tomcat的信息
        :return: {'soft_info':soft_info,'pro_info':pro_info,'memory_info':memory_info}
        """
        try:
            import requests, re
            try:
                import xml.etree.ElementTree as ET
            except:
                import xml.etree.ElementTree as ET

            user_path = '/www/server/tomcat/conf/tomcat-users.xml'
            conf = public.readFile(user_path)
            user_info = '<user username="admin" password="admin" roles="manager-gui"/>'
            if user_info not in conf:
                conf = conf.split('\n')
                try:
                    conf.remove('</tomcat-users>')
                except:
                    pass
                conf.append(user_info)
                conf.append('</tomcat-users>')
                conf = "\n".join(conf)
                public.writeFile(user_path, conf)
                sys.path.insert(0, "/www/server/panel/class/")
                import system as Mysys
                mysys = Mysys.system()
                get = public.dict_obj()
                get.name = 'tomcat'
                get.type = 'restart'
                mysys.ServiceAdmin(get)
            soft_info = {}
            url = 'http://localhost:8080/manager/status/all?XML=true'
            auth = ('admin', 'admin')
            headers = {'Content-Type': 'text/plain; charset=utf-8'}
            response = requests.get(url, auth=auth, headers=headers)
            if response.status_code == 200:
                root = ET.fromstring(response.text)  # 解析XML响应
                conn_elem = root.find(".//connector")
                thread_info = conn_elem.find("threadInfo")
                requestInfo = conn_elem.find("requestInfo")
                mem_elem = root.find(".//memory")
                soft_info['free_memory'] = public.to_size(mem_elem.attrib['free'])
                soft_info['total_memory'] = public.to_size(mem_elem.attrib['total'])
                soft_info['max_memory'] = public.to_size(mem_elem.attrib['max'])
                soft_info['maxThreads'] = thread_info.attrib['maxThreads']
                soft_info['currentThreadCount'] = thread_info.attrib['currentThreadCount']
                soft_info['currentThreadsBusy'] = thread_info.attrib['currentThreadsBusy']
                soft_info['maxTime'] = requestInfo.attrib['maxTime']
                soft_info['processingTime'] = requestInfo.attrib['processingTime']
                soft_info['requestCount'] = requestInfo.attrib['requestCount']
                soft_info['errorCount'] = requestInfo.attrib['errorCount']
                soft_info['bytesReceived'] = requestInfo.attrib['bytesReceived']
                soft_info['bytesSent'] = requestInfo.attrib['bytesSent']
                soft_info['errorCount'] = requestInfo.attrib['errorCount']
            else:
                raise '无法获取Tomcat状态，因为响应码不是200。'
            return soft_info
        except:
            return {"soft_info": "软件查询出错"}

    # 获取容器的attr
    def get_container_attr(self, containers):
        c_list = containers.list(all=True)
        return [container_info.attrs for container_info in c_list]

    def __get_docker_status(self):
        """
        获取docker的服务容器信息，docker进程信息，docker使用内存信息
        :return: {'soft_info':{'容器名:镜像名:镜像版本':{容器详细使用信息}...},'pro_info':pro_info,'memory_info':memory_info}
        """
        try:
            soft_info = []
            if not self.docker_obj:
                return public.returnMsg(True, '')
            containers = self.docker_obj.containers
            attr_list = self.get_container_attr(containers)
            for attr in attr_list:
                cpu_usage = dp.sql("cpu_stats").where("container_id=?", (attr["Id"],)).select()
                if cpu_usage and isinstance(cpu_usage, list):
                    cpu_usage = cpu_usage[-1]['cpu_usage']
                else:
                    cpu_usage = "0.0"
                container_info = {}
                Option = {'running': "正在运行", 'exited': '停止', 'paused': '暂停'}
                container_info['container_status'] = Option[attr["State"]["Status"]]  # 状态
                container_info['container_start_time'] = attr['Created'].split('.')[0].replace("T", " ")  # 启动时间
                container_info['container_internal_port'] = list(attr['NetworkSettings']['Ports'].keys())
                container_info['container_internal_port'] = ["8080/tcp", "8080/tcp"]
                container_info['container_cpu_usage'] = cpu_usage + "%"  # 使用cpu
                container_info['container_WorkingDir'] = attr['GraphDriver']['Data']['WorkDir']  # 容器的工作目录
                container_info['container_Hostname'] = attr['Config']['Hostname']  # 容器主机名
                container_info['container_name'] = attr['Name'].replace("/", "") + ":" + attr['Config']['Image']

                soft_info.append(container_info)
                # client = docker.DockerClient(base_url="unix:///var/run/docker.sock")
                # client.networks.list()
                # 获取所有容器
                # containers = client.containers.list()
                # c_list = containers.list(all=True)
                # 遍历所有容器，获取容器的负载状态
                # for container in containers:
                #     container_info = {}
                #
                #     stats = container.stats(stream=False)
                #     container_info['cpu_usage'] = public.to_size(stats['cpu_stats']['cpu_usage']['total_usage'])
                #     container_info['mem_usage'] = public.to_size(stats['memory_stats']['usage'])
                #     container_info['network_rx'] = public.to_size(stats['networks']['eth0']['rx_bytes'])
                #     container_info['network_tx'] = public.to_size(stats['networks']['eth0']['tx_bytes'])
                #     try:
                #         container_info['io_read'] = public.to_size(
                #             stats['blkio_stats']['io_service_bytes_recursive'][0]['value'])
                #     except:
                #         container_info['io_read'] = 0
                #     try:
                #         container_info['io_write'] = public.to_size(
                #             stats['blkio_stats']['io_service_bytes_recursive'][1]['value'])
                #     except:
                #         container_info['io_write'] = 0
                #     soft_info[container.name + ":" + str(container.attrs['Config']['Image'])] = container_info
            return soft_info
        except:
            return {"soft_info": "软件查询出错"}

    def __get_process_status(self, name):
        """
        获取进程的进程信息，内存信息
        :param name: 进程名
        :return: {'pro_info': pro_info, 'memory_ingo': memory_ingo} #进程信息，内存信息
        """
        import psutil
        import datetime
        processes = psutil.process_iter()
        # 遍历进程列表，查找指定进程
        for proc in processes:
            try:
                # 获取进程信息
                pinfo = proc.as_dict(attrs=['pid', 'status', 'ppid', 'name', 'exe', 'cmdline', 'connections'])

                # 判断进程名是否为指定进程名
                if proc.name() == name:
                    if proc.name() == "httpd" or proc.name() == "postgres" or proc.name() == "jsvc":
                        if proc.ppid() != 1:
                            continue
                    pro_info = {}
                    pro_info['pid'] = pinfo['pid']
                    pro_info['status'] = pinfo['status']
                    pro_info['ppid'] = psutil.Process(pinfo['ppid']).name()
                    pro_info['user_name'] = proc.username()
                    pro_info['num_threads'] = proc.num_threads()
                    pro_info['io_read'] = public.to_size(proc.io_counters()[0])
                    pro_info['io_write'] = public.to_size(proc.io_counters()[1])
                    pro_info['socket'] = len(pinfo['connections'])
                    pro_info['create_time'] = str(datetime.datetime.fromtimestamp(proc.create_time())).split('.')[0]
                    pro_info['name'] = pinfo['name']
                    pro_info['exe'] = pinfo['exe']
                    pro_info['start_command'] = " ".join(pinfo['cmdline'])
                    memory_ingo = {}
                    memory_ingo['rss'] = proc.memory_info().rss
                    memory_ingo['vms'] = proc.memory_info().vms
                    memory_ingo['shared'] = proc.memory_info().shared
                    memory_ingo['text'] = proc.memory_info().text
                    memory_ingo['data'] = proc.memory_info().data
                    memory_ingo['lib'] = proc.memory_info().lib
                    memory_ingo['dirty'] = proc.memory_info().dirty
                    memory_ingo['pss'] = proc.memory_full_info().pss
                    memory_ingo['swap'] = proc.memory_full_info().swap
                    for i, j in memory_ingo.items():
                        memory_ingo[i] = public.to_size(j)
                    return {'pro_info': pro_info, 'memory_info': memory_ingo}
            except:
                return {'pro_info': "", 'memory_info': ""}
        else:
            return {'pro_info': "", 'memory_info': ""}

    def __get_sever_status_list(self):
        """
        查询服务存在列表
        :return:【服务名，。。。】
        """
        try:
            import psutil
        except:
            os.system("btpip intsall psutil")
            import psutil
        try:
            all_sever_name_list = ['nginx', 'mysqld_safe', 'redis-server', 'mongod', 'postgres', 'memcached', 'httpd',
                                   'pure-ftpd', 'jsvc', 'dockerd']
            survive_sever_list = []
            processes = psutil.process_iter()
            for proc in processes:
                if proc.name() in all_sever_name_list:
                    if proc.name() == 'jsvc':
                        if proc.exe() == "/www/server/tomcat/bin/jsvc":
                            survive_sever_list.append(proc.name())
                        continue
                    if int(proc.ppid()) == 1:
                        survive_sever_list.append(proc.name())
            return list(set(survive_sever_list))
        except:
            return public.returnMsg(False, "服务列表信息查询出错")

    def __get_tomcat_usr_info(self):
        try:
            tomcat_status = False
            if 'jsvc' in self.__get_sever_status_list(): tomcat_status = True
            user_path = '/www/server/tomcat/conf/tomcat-users.xml'
            if os.path.exists(user_path):
                conf = public.readFile(user_path)
                user_info = '<user username="admin" password="admin" roles="manager-gui"/>'
                if user_info not in conf:
                    return {'status': False, 'soft_introduction': self.soft_introduction['jsvc'],
                            'tomcat_status': tomcat_status}
            return {'status': True, 'soft_introduction': self.soft_introduction['jsvc'], 'tomcat_status': tomcat_status}
        except:
            return {'status': False, 'soft_introduction': self.soft_introduction['jsvc'],
                    'tomcat_status': tomcat_status}

    def __mongod_admin(self, option):
        try:
            statusString = self.statusOption[option]
            Command = {"start": "/etc/init.d/mongodb start",
                       "stop": "/etc/init.d/mongodb stop", }
            if option != '2':
                public.ExecShell(Command.get(statusString))
                return public.returnMsg(True, '操作成功!')
            public.ExecShell(Command.get('stop'))
            public.ExecShell(Command.get('start'))
            return public.returnMsg(True, '操作成功!')
        except:
            return public.returnMsg(False, '操作失败!')

    def __redis_admin(self, option):
        try:
            statusString = self.statusOption[option]
            get = public.dict_obj()
            get.name = 'redis'
            get.type = statusString

            return self.syst.ServiceAdmin(get)
        except:
            return public.returnMsg(False, '操作失败!')

    def __memcached_admin(self, option):
        try:
            statusString = self.statusOption[option]
            get = public.dict_obj()
            get.name = 'memcached'
            get.type = statusString
            return self.syst.ServiceAdmin(get)
        except:
            return public.returnMsg(False, '操作失败!')

    def __docker_admin(self, option):
        try:
            s_type = self.statusOption[option]
            exec_str = 'systemctl {} docker.socket'.format(s_type)
            public.ExecShell(exec_str)
            if s_type in ['start', 'restart']:
                try:
                    import docker
                    self.__docker = docker.from_env()
                except:
                    return public.returnMsg(True, 'Docker 链接失败。请检查Docker是否正常启动')
                for container in self.__docker.containers.list(all=True):
                    try:
                        container.start()
                    except:
                        pass
            return public.returnMsg(True, "操作成功")
        except:
            return public.returnMsg(False, '操作失败!')

    def __tomcat_admin(self, option):
        try:
            statusString = self.statusOption[option]
            get = public.dict_obj()
            get.name = 'tomcat'
            get.type = statusString
            self.syst.ServiceAdmin(get)
            return public.returnMsg(True, '操作成功!')
        except:
            return public.returnMsg(False, '操作失败!')

    def __ftp_admin(self, option):
        try:
            statusString = self.statusOption[option]
            get = public.dict_obj()
            get.name = 'pure-ftpd'
            get.type = statusString
            return self.syst.ServiceAdmin(get)
        except:
            return public.returnMsg(False, '操作失败!')

    def __apache_admin(self, option):
        try:
            statusString = self.statusOption[option]
            get = public.dict_obj()
            get.name = 'apache'
            get.type = statusString
            res = self.syst.ServiceAdmin(get)
            import time
            time.sleep(1)
            return res
        except:
            return public.returnMsg(False, '操作失败!')

    def __mysqld_admin(self, option):
        try:
            statusString = self.statusOption[option]
            get = public.dict_obj()
            get.name = 'mysqld'
            get.type = statusString
            return self.syst.ServiceAdmin(get)
        except:
            return public.returnMsg(False, '操作失败!')

    def __nginx_admin(self, option):
        try:
            statusString = self.statusOption[option]
            get = public.dict_obj()
            get.name = 'nginx'
            get.type = statusString
            return self.syst.ServiceAdmin(get)
        except:
            return public.returnMsg(False, '操作失败!')

    def __pgsql_admin(self, option):
        try:
            statusString = self.statusOption[option]
            get = public.dict_obj()
            get.name = 'pgsql'
            get.type = statusString
            return self.syst.ServiceAdmin(get)
        except:
            return public.returnMsg(False, '操作失败!')

    # 实例化docker
    def docker_client(self):
        """
        目前仅支持本地服务器
        :param url: unix:///var/run/docker.sock
        :return:
        """
        try:
            try:
                import docker
            except Exception as e:
                if 'cryptography' in str(e):
                    os.system('btpip uninstall cryptography')
                    os.system('btpip install cryptography==38.0.4')
                import docker
            client = docker.DockerClient(base_url="unix:///var/run/docker.sock")
            client.networks.list()
            return client
        except:
            return False

    # 结束进程树
    def __kill_process_all(self, pid):
        import psutil
        if pid < 30: return public.returnMsg(True, '已结束此进程树!')
        try:
            if pid not in psutil.pids(): public.returnMsg(True, '已结束此进程树!')
            p = psutil.Process(pid)
            ppid = p.ppid()
            name = p.name()
            p.kill()
            public.ExecShell('pkill -9 ' + name)
            if name.find('php-') != -1:
                public.ExecShell("rm -f /tmp/php-cgi-*.sock")
            elif name.find('mysql') != -1:
                public.ExecShell("rm -f /tmp/mysql.sock")
            elif name.find('mongod') != -1:
                public.ExecShell("rm -f /tmp/mongod*.sock")
            self.__kill_process_lower(pid)
            if ppid: return self.kill_process_all(ppid)
            return public.returnMsg(True, '已结束此进程!')
        except:
            return public.returnMsg(False, '结束进程失败!')

    def __kill_process_lower(self, pid):
        import psutil
        pids = psutil.pids()
        for lpid in pids:
            if lpid < 30: continue
            p = psutil.Process(lpid)
            ppid = p.ppid()
            if ppid == pid:
                p.kill()
                return self.__kill_process_lower(lpid)
        return True

    # 构造分页结构
    def get_page(self, data, get):
        # 包含分页类
        import page
        # 实例化分页类
        page = page.Page()
        info = {}
        info['count'] = len(data)
        info['row'] = self.ROWS
        info['p'] = 1
        if hasattr(get, 'p'):
            try:
                info['p'] = int(get['p'])
            except:
                info['p'] = 1
        info['uri'] = {}
        info['return_js'] = ''
        if hasattr(get, 'tojs'):
            info['return_js'] = get.tojs

        # 获取分页数据
        result = {}
        result['page'] = page.GetPage(info, '1,2,3,4,5,8')
        n = 0
        result['data'] = []
        for i in range(info['count']):
            if n >= page.ROW: break
            if i < page.SHIFT: continue
            n += 1
            result['data'].append(data[i])
        return result

    # 获取指定软件日志
    def get_log(self, get):
        try:
            if not hasattr(get, 'name'):
                return public.returnMsg(False, "请指定软件")
            log_path_map = {
                'Nginx': self.__get_nginx_log_path,
                'Php': self.__get_php_log_path,
                'Mongodb': self.__get_mongo_log_path,
                'Memcache': self.__get_memcache_log_path,
                'Redis': self.__get_redis_log_path,
                'Apache': self.__get_apache_log_path,
                'Pgsql': self.__get_postgress_log_path,
                '网站防篡改': self.__new_get_tamper_proof_log_path,
                '网站防篡改程序-旧版': self.__get_tamper_proof_log_path
            }

            # mysql请求logs模块下的慢日志和错误日志接口   不在这里进行获取日志
            if get.name.strip() == "Mysql":
                return []

            if get.name not in log_path_map.keys():
                return public.returnMsg(False, "请指定正确软件")
            if get.name == 'Docker':
                return log_path_map[get.name](get)
            path = log_path_map[get.name]()
            if type(path) == list:
                if get.name == 'Php':
                    logs = []
                    php_path = '/www/server/php/'
                    file_list = os.listdir(php_path)
                    for i in range(len(file_list)):
                        log = self.__GetOpeLogs(path[i])
                        log['msg'] = self.__search_log(log['msg'], get)
                        log['file'] = path[i]
                        log.update({'version': file_list[i]})
                        logs.append(log)
                    logs = sorted(logs, key=lambda x: x['version'], reverse=True)
                    return logs
            else:
                logs = self.__GetOpeLogs(path)
                logs['file'] = path
                logs['msg'] = self.__search_log(logs['msg'], get)
                return logs
        except:
            pass

    def __search_log(self, log, get):
        if hasattr(get, 'search'):
            if get.search != '':
                msg_l = log.split('\n')
                msg_l = [i for i in msg_l if get.search.lower() in i.lower()]
                log = '\n'.join(msg_l)
        return log

    # 取指定日志
    def __GetOpeLogs(self, path):
        try:
            if not os.path.exists(path):
                return public.returnMsg(False, 'AJAX_LOG_FILR_NOT_EXISTS')
            if public.readFile(path) == '':
                return public.returnMsg(True, '')
            return public.returnMsg(
                True, public.xsssec(public.GetNumLines(path, 200)))
        except:
            return public.returnMsg(False, '')

    # Docker日志
    def get_docker_log(self, get):
        try:
            if get.name != 'Docker':
                return ''
            logs = public.M('logs').where('type=? or type=?', ('Docker','Docker module')).select()
            if hasattr(get, 'search'):
                if get.search != '':
                    logs = [i for i in logs if
                            get.search in i['log'] or get.search in i['addtime'] or get.search in i['username']]
            self.ROWS = 10
            if hasattr(get, 'ROWS'):
                self.ROWS = int(get.ROWS)
            l = self.get_page(logs, get)
            return l
        except:
            pass

    # 防入侵日志
    def get_bt_security_log(self, get):
        try:
            if get.name != 'bt_security':
                return ''
            # 从数据库中选择类型为'防入侵'的所有日志记录
            logs = public.M('logs').where('type=?', (u'防入侵',)).order('id desc').select()

            # 如果传入的参数`get`有`search`属性，并且`search`属性的值不为空，那么在所有的日志记录中搜索包含`search`值的记录
            if hasattr(get, 'search'):
                if get.search != '':
                    logs = [i for i in logs if get.search in i['log'] or get.search in i['addtime']]

            # 设置每页显示的日志记录数为10。如果传入的参数`get`有`ROWS`属性，那么使用`ROWS`的值作为每页显示的日志记录数
            self.ROWS = 10
            if hasattr(get, 'ROWS'):
                self.ROWS = int(get.ROWS)

            # 调用`get_page`方法对日志记录进行分页
            data = self.get_page(logs, get)

            return public.returnMsg(True, data)
        except Exception as e:
            return public.returnMsg(False, "获取失败" + str(e))

    # 系统加固日志
    def get_syssafe_log(self, get):
        try:
            if get.name != 'syssafe':
                return ''
            # 从数据库中选择类型为'系统加固'的所有日志记录
            logs = public.M('logs').where('type=?', (u'系统加固',)).order('id desc').select()

            # 如果传入的参数`get`有`search`属性，并且`search`属性的值不为空，那么在所有的日志记录中搜索包含`search`值的记录
            if hasattr(get, 'search'):
                if get.search != '':
                    logs = [i for i in logs if get.search in i['log'] or get.search in i['addtime']]

            # 设置每页显示的日志记录数为10。如果传入的参数`get`有`ROWS`属性，那么使用`ROWS`的值作为每页显示的日志记录数
            self.ROWS = 10
            if hasattr(get, 'ROWS'):
                self.ROWS = int(get.ROWS)

            # 调用`get_page`方法对日志记录进行分页
            data = self.get_page(logs, get)
            return public.returnMsg(True, data)
        except Exception as e:
            return public.returnMsg(False, "获取失败" + str(e))

    # 软件日志删除
    def del_soft_log(self, get):
        try:
            if not hasattr(get, 'type'):
                return public.returnMsg(False, '缺少参数type')

            del_type = int(get.type)
            if del_type not in [0, 1, 2]:
                return public.returnMsg(False, '参数type错误')

            # 删除 防入侵日志/Docker日志/系统加固日志
            if del_type == 0:
                if not hasattr(get, 'id'):
                    return public.returnMsg(False, '缺少参数id')
                id_list = get.id.split(",")
                err_list = []
                succ_list = []
                for ids in id_list:
                    log_data = public.M('logs').where('id=?', (ids,)).count()
                    if not log_data:
                        err_list.append(ids)
                        continue
                        # return public.returnMsg(False, '日志不存在')
                    public.M('logs').where('id=?', (ids,)).delete()
                    succ_list.append(ids)
                    # return public.returnMsg(True, "删除成功")
                return {
                    "error": err_list,
                    "msg": "删除成功",
                    "status": True,
                    "success": succ_list
                }

            # --清空日志--
            # Nginx   Memcache    网站防篡改重构版  Mongodb Php Redis
            elif del_type == 1:
                if not hasattr(get, 'path'):
                    return public.returnMsg(False, "缺少参数path")

                slow_log_path = get.path.strip()
                if not os.path.exists(slow_log_path):
                    return public.returnMsg(False, "日志文件不存在")

                public.ExecShell("echo > {}".format(slow_log_path))
                return public.returnMsg(True, "清空日志成功")
            else:
                # --清空日志--
                # Mysql慢日志/错误日志
                if not hasattr(get, 'assort'):
                    return public.returnMsg(False, "缺少参数assort")
                types = get.assort.strip()

                if types not in ['slow', 'error']:
                    return public.returnMsg(False, "参数assort错误")

                if types == "slow":
                    # Mysql慢日志
                    my_info = public.get_mysql_info()
                    if not my_info['datadir']:
                        return public.returnMsg(False, '未安装MySQL数据库')

                    slow_log_path = my_info['datadir'] + '/mysql-slow.log'
                    if not os.path.exists(slow_log_path):
                        return public.returnMsg(False, '日志文件不存在')

                    public.ExecShell("echo > {}".format(slow_log_path))
                    return public.returnMsg(True, '清空日志成功')
                else:
                    # Mysql错误日志
                    from database import database

                    database = database()
                    my_info = database.GetMySQLInfo(get)['datadir']
                    if not os.path.exists(my_info): return public.returnMsg(False, '数据库目录不存在，请检查Mysql是否安装正常')

                    error_log_path = ''
                    for n in os.listdir(my_info):
                        if len(n) < 5: continue
                        if n[-3:] == 'err':
                            error_log_path = my_info + '/' + n
                            break
                    if not os.path.exists(error_log_path): return public.returnMsg(False, '日志文件不存在')

                    public.ExecShell("echo > {}".format(error_log_path))
                    return public.returnMsg(True, '清空日志成功')

        except:
            return public.returnMsg(False, "清空日志失败")

    def __get_nginx_log_path(self):
        try:
            path = '/www/wwwlogs/nginx_error.log'
            if os.path.exists(path):
                return path
            return ''
        except:
            return ''

    def __get_postgress_log_path(self):
        path = '/www/server/pgsql/logs/pgsql.log'
        if os.path.exists(path):
            return path
        else:
            return ''

    def __get_php_log_path(self):
        try:
            path_l = []
            path = '/www/server/php/'
            file_list = os.listdir(path)
            for i in file_list:
                path_l.append(path + i + '/var/log/php-fpm.log')
            return path_l
        except:
            return []

    def __get_memcache_log_path(self):
        try:
            txt = public.ExecShell('journalctl -u memcached.service > /www/wwwlogs/memcache.log 2>&1')[1]
            if not txt:
                return '/www/wwwlogs/memcache.log'
            else:
                return ''
        except:
            return ''

    def __get_redis_log_path(self):
        try:
            log_path = '/www/server/redis/redis.log'
            if os.path.exists(log_path):
                return log_path
            else:
                return ''
        except:
            return ''

    def __get_apache_log_path(self):
        try:
            log_path = '/www/wwwlogs/error_log'
            if os.path.exists(log_path):
                return log_path
            else:
                return ''
        except:
            return ''

    def __get_mongo_log_path(self):
        try:
            mongo_path = '/www/server/mongodb/config.conf'
            if os.path.exists(mongo_path):
                conf = public.readFile(mongo_path)
                tmp = re.findall('path' + ":\s+(.+)", conf)
                if not tmp: return ""
                return tmp[0]
            return ''
        except:
            return ''

    def __get_ftp_log_path(self, get):
        try:
            ftp_path = "/var/log/pure-ftpd.log"
            if os.path.exists(ftp_path):
                return ftp_path
            else:
                return ''
        except:
            return ''

    def __get_tamper_proof_log_path(self) -> str:
        try:
            log_path = '/www/server/panel/plugin/tamper_proof/service.log'
            if os.path.exists(log_path):
                return log_path
            else:
                return ''
        except:
            return ''


    def __new_get_tamper_proof_log_path(self) -> str:
        try:
            log_path = '/www/server/panel/plugin/tamper_proof_refactored/service.log'
            if os.path.exists(log_path):
                return log_path
            else:
                return ''
        except:
            return ''

    def soft_log_list(self, get):
        try:
            # 初始化软件列表和映射关系
            soft_list = ['nginx', 'httpd', 'mysqld_safe', 'redis-server', 'php', 'pure-ftpd', 'mongod', 'postgres', 'memcached',
                         'dockerd', 'tamper_proof', 'bt_security', 'syssafe', 'tamper_proof_refactored']
            name_map = {
                'pure-ftpd': 'FTP', 'mysqld_safe': 'Mysql', 'redis-server': 'Redis', 'mongod': 'Mongodb',
                'postgres': 'Pgsql', 'memcached': 'Memcache', 'httpd': 'Apache',
                'nginx': 'Nginx', 'php': 'Php', 'dockerd': 'Docker', 'tamper_proof': '网站防篡改程序-旧版', 'bt_security': '堡塔防入侵', 'syssafe': '宝塔系统加固',
                "tamper_proof_refactored": "网站防篡改"
            }

            # 使用列表推导式-->构建符合安装状态和映射后的软件列表
            installed_soft_list = [
                name_map[software]
                for software in soft_list
                if self.__is_installation(software) and (software != "postgres" or self.__is_installation("postgresql"))
            ]

            return installed_soft_list
        except:
            return []
