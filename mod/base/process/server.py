# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: sww <sww@bt.cn>
# -------------------------------------------------------------------
import json
import os
# ------------------------------
# 服务模型
# ------------------------------
import sys, re
import time
import traceback

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

os.chdir("/www/server/panel")
import public
import glob

# 关闭系统加固执行函数后打开
def syssafe_admin(func):
    def wrapper(*args, **kwargs):
        syssafe_flag = 0
        # 检查系统加固并且关闭
        if os.path.exists('/www/server/panel/plugin/syssafe/init.sh'):
            res = public.ExecShell('bash /www/server/panel/plugin/syssafe/init.sh status')
            if 'already running' in res[0]:
                try:
                    syssafe_flag = 1
                    public.ExecShell('bash /www/server/panel/plugin/syssafe/init.sh stop')
                    res = public.ExecShell('bash /www/server/panel/plugin/syssafe/init.sh status')
                    if 'already running' in res[0]:
                        import PluginLoader
                        PluginLoader.plugin_run('syssafe', 'set_open', public.to_dict_obj({'status': 0}))
                    # print('已关闭系统加固！')
                except:
                    pass
        e = None
        result = None
        try:
            result = func(*args, **kwargs)
        except Exception as ex:
             e= ex
        try:
            if syssafe_flag:
                public.ExecShell('bash /www/server/panel/plugin/syssafe/init.sh start')
                res = public.ExecShell('bash /www/server/panel/plugin/syssafe/init.sh status')
                if 'already running' not in res[0]:
                    import PluginLoader
                    PluginLoader.plugin_run('syssafe', 'set_open', public.to_dict_obj({'status': 1}))
                # print('已开启系统加固！')
        except:
            pass
        if e is not None:
            raise e
        return result
    return wrapper



class RealServer:

    server_list = ['mysqld_safe', 'redis-server', 'mongod', 'postgres', 'nginx', 'memcached', 'httpd', 'pure-ftpd', 'jsvc', 'dockerd']
    system_info = None
    # --------------------- 常用服务管理 start----------------------
    def server_admin(self, server_name: str, option: str) -> dict:

        """
        服务管理
        :param server_name:'mysqld_safe', 'redis-server', 'mongod', 'postgres', 'nginx', 'memcached', 'httpd', 'pure-ftpd', 'jsvc', 'dockerd'
        :param option: start,stop,restart
        :return:
        """
        servers = {
            "mongod": self.__mongod_admin,
            "redis-server": self.__redis_admin,
            "memcached": self.__memcached_admin,
            "dockerd": self.__docker_admin,
            "jsvc": self.__tomcat_admin,
            "pure-ftpd": self.__ftp_admin,
            "httpd": self.__apache_admin,
            "mysqld_safe": self.__mysqld_admin,
            "nginx": self.__nginx_admin,
            "postgres": self.__pgsql_admin,
        }
        from system import system
        self.syst = system()
        if server_name in self.server_list:
            res = servers[server_name](option)
            return public.returnResult(code=1, msg=res['msg'], status=res['status'])
        else:
            return public.returnResult(code=0, msg='操作失败!参数不存在', status=False)

    def __mongod_admin(self, option: str) -> dict:
        try:
            Command = {"start": "/etc/init.d/mongodb start",
                       "stop": "/etc/init.d/mongodb stop", }
            if option != 'restart':
                public.ExecShell(Command.get(option))
                return public.returnMsg(True, '操作成功!')
            public.ExecShell(Command.get('stop'))
            public.ExecShell(Command.get('start'))
            return public.returnMsg(True, '操作成功!')
        except:
            return public.returnMsg(False, '操作失败!')

    def __redis_admin(self, option: str) -> dict:
        try:
            get = public.dict_obj()
            get.name = 'redis'
            get.type = option

            return self.syst.serverAdmin(get)
        except:
            return public.returnMsg(False, '操作失败!')

    def __memcached_admin(self, option: str) -> dict:
        try:
            get = public.dict_obj()
            get.name = 'memcached'
            get.type = option
            return self.syst.serverAdmin(get)
        except:
            return public.returnMsg(False, '操作失败!')

    def __docker_admin(self, option: str) -> dict:
        try:
            exec_str = 'systemctl {} docker.socket'.format(option)
            public.ExecShell(exec_str)
            return public.returnMsg(True, "操作成功")
        except:
            return public.returnMsg(False, '操作失败!')

    def __tomcat_admin(self, option: str) -> dict:
        try:
            get = public.dict_obj()
            get.name = 'tomcat'
            get.type = option
            self.syst.serverAdmin(get)
            return public.returnMsg(True, '操作成功!')
        except:
            return public.returnMsg(False, '操作失败!')

    def __ftp_admin(self, option: str) -> dict:
        try:
            get = public.dict_obj()
            get.name = 'pure-ftpd'
            get.type = option
            return self.syst.serverAdmin(get)
        except:
            return public.returnMsg(False, '操作失败!')

    def __apache_admin(self, option: str) -> dict:
        try:
            get = public.dict_obj()
            get.name = 'apache'
            get.type = option
            res = self.syst.serverAdmin(get)
            import time
            time.sleep(1)
            return res
        except:
            return public.returnMsg(False, '操作失败!')

    def __mysqld_admin(self, option: str) -> dict:
        try:
            get = public.dict_obj()
            get.name = 'mysqld'
            get.type = option
            return self.syst.serverAdmin(get)
        except:
            return public.returnMsg(False, '操作失败!')

    def __nginx_admin(self, option: str) -> dict:
        try:
            get = public.dict_obj()
            get.name = 'nginx'
            get.type = option
            return self.syst.serverAdmin(get)
        except:
            return public.returnMsg(False, '操作失败!')

    def __pgsql_admin(self, option: str) -> dict:
        try:
            get = public.dict_obj()
            get.name = 'pgsql'
            get.type = option
            return self.syst.serverAdmin(get)
        except:
            return public.returnMsg(False, '操作失败!')

    # ----------------------常用服务管理 end----------------------

    # ----------------------常用服务状态 start----------------------
    def server_status(self, server_name: str) -> dict:
        """
        服务状态
        :param server_name: 'mysqld_safe', 'redis-server', 'mongod', 'postgres', 'nginx', 'memcached', 'httpd', 'pure-ftpd', 'jsvc', 'dockerd'
        :return:
        """
        try:
            if server_name in self.server_list:
                res = self.__get_status(server_name)
                return public.returnResult(code=1, msg=res['msg'], data=res['data'], status=res['status'])
            else:
                return public.returnResult(code=0, msg='操作失败!参数不存在', status=False)
        except Exception as e:
            return public.returnResult(code=0, msg='操作失败!', status=False)

    def __is_installation(self, name: str) -> bool:
        map = {
            "mysqld_safe": "mysqld",
            "redis-server": "redis",
            "mongod": "mongodb",
            "postgres": "pgsql",
            "nginx": "nginx",
            "memcached": "memcached",
            "httpd": "httpd",
            "pure-ftpd": "pure-ftpd",
            "jsvc": "tomcat",
            "dockerd": "docker",
            "php": "php",
            "tamper_proof": "tamper_proof",
            "bt_security": "bt_security",
            "syssafe": "syssafe",

        }
        import glob
        dir_path = '/etc/init.d/'
        files = [os.path.basename(f) for f in glob.glob(dir_path + "*")]
        if name == "dockerd":
            res = public.ExecShell('docker -v')[0]
            if 'version' in res:
                return True
            return False
        if name == "postgres":
            res = public.ExecShell('/www/server/pgsql/bin/psql --version')[0]
            pgsql = False
            if 'PostgreSQL' in res:
                pgsql = True
            Manager = False
            if os.path.exists('/www/server/panel/plugin/pgsql_manager'):
                Manager = True
            return {'pgsql': pgsql, 'Manager': Manager}
        if name == "php":
            php_l = [i for i in files if name in i.lower()]
            if len(php_l) != 0:
                return True
        if name == "tamper_proof":
            return os.path.exists('/www/server/panel/plugin/tamper_proof')

        if name == "bt_security":
            return os.path.exists('/www/server/panel/plugin/bt_security')

        if name == "syssafe":
            return os.path.exists('/www/server/panel/plugin/syssafe')

        if map[name] in files:
            return True
        return False

    def __get_status(self, server_name: str) -> dict:
        try:
            if not self.__is_installation(server_name):
                return {'status': True, 'msg': '', 'data': {'install': False, 'status': False}}
            res = public.ExecShell('ps -ef|grep {}|grep -v grep'.format(server_name))[0]
            if 'mongod' in res:
                return {'status': True, 'msg': '', 'data': {'install': True, 'status': True}}
            return {'status': True, 'msg': '', 'data': {'install': True, 'status': False}}
        except:
            return {'status': False, 'msg': '获取失败!', 'data': {'install': False, 'status': False}}

    # ----------------------常用服务状态 end----------------------

    # ---------------------- 通用服务管理 start----------------------
    def universal_server_admin(self, server_name: str, option: str) -> dict:
        """
        通用服务管理 服务器在/etc/init.d/目录下有同名的启动文件，且启动文件中有start,stop,restart,status命令
        :param server_name: 服务名称
        :param option: start,stop,restart
        :return:
        """
        try:
            get = public.dict_obj()
            get.name = server_name
            get.type = option
            dir_path = '/etc/init.d/'
            files = [os.path.basename(f) for f in glob.glob(dir_path + "*")]
            if server_name in files:
                res = public.ExecShell('/etc/init.d/{} {}'.format(server_name, option))
                if 'is running' in res[0].lower() or 'is active' in res[0].lower() or 'already running' in res[0].lower():
                    return public.returnResult(code=1, msg='操作成功!', status=True)
                if 'is stopped' in res[0].lower() or 'is not running' in res[0].lower():
                    return public.returnResult(code=1, msg='操作成功!', status=True)
            else:
                return public.returnResult(code=0, msg='操作失败!未在/etc/init.d/目录下找到该服务', status=False)
        except:
            return public.returnResult(code=0, msg='操作失败!', status=False)

    # ---------------------- 通用服务管理 end----------------------

    # ---------------------- 通用服务状态 start----------------------
    def universal_server_status(self, server_name: str) -> dict:
        """
        通用服务状态 服务器在/etc/init.d/目录下有同名的启动文件，且启动文件中有status命令，status中有输出is running或is active
        :param server_name: 服务名称
        :return:
        """
        try:
            get = public.dict_obj()
            get.name = server_name
            get.type = 'status'
            dir_path = '/etc/init.d/'
            files = [os.path.basename(f) for f in glob.glob(dir_path + "*")]
            if server_name in files:
                res = public.ExecShell('/etc/init.d/{} status'.format(server_name))
                if 'is running' in res[0].lower() or 'is active' in res[0].lower() or 'already running' in res[0].lower():
                    return public.returnResult(code=1, msg='运行中', data=True)
                return public.returnResult(code=1, msg='未运行', data=False)
            return public.returnResult(code=0, msg='服务不存在!', status=False)
        except:
            return public.returnResult(code=0, msg='获取失败!', data=False)

    # ---------------------- 通用服务状态 end----------------------

    # ---------------------- 添加开机自启 启动脚本  start----------------------

    # 添加开机自启
    @syssafe_admin
    def add_boot(self, server_name: str, pid_file: str, start_exec: str, stop_exec: str, default_start: str = '2 3 4 5') -> dict:
        """
        添加开机自启
        :param server_name: 服务名称
        :param pid_file: 启动pid记录文件
        :param start_exec: 启动命令
        :param stop_exec: 停止命令
        :param default_start: 默认启动级别
        :return:
        """

        content = """
#! /bin/sh
# chkconfig: 2345 55 25

### BEGIN INIT INFO
# Provides:          {name}
# Required-Start:    $all
# Required-Stop:     $all
# Default-Start:     {default_start}
# Default-Stop:      0 1 6
# Short-Description: {name}
# Description:       {name}
### END INIT INFO

# Author:   licess
# website:  http://www.bt.cn

PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

case "$1" in
    start)
        echo -n "Starting {name}... "
        if [ -f {pid_file} ];then
        mPID=$(cat {pid_file})
        isStart=`ps ax | awk '{{ print $1 }}' | grep -e "^${{mPID}}$"`
        if [ "$isStart" != "" ];then
            echo "{name} (pid $mPID) already running."
            exit 1
            fi
        fi
        nohup {start_exec} &
        if [ $? != 0 ]; then
            echo " failed"
            exit 1
        else
            pid=`ps -ef|grep "{start_exec}" |grep -v grep|awk '{{print $2}}'`
            echo $! > {pid_file}
            echo " done"
        fi
        ;;
    stop)
        echo -n "Stopping {name}... "
        if [ -f {pid_file} ];then
            mPID=$(cat {pid_file})
            isStart = `ps ax | awk '{{ print $1 }}' | grep -e "^${{mPID}}$"`
            if [ "$isStart" = "" ];then
                echo "{name} is stopped"
                exit 1
                fi
        else
            echo "{name} is stopped"
            exit 1
        fi
        nohup {stop_exec} &
        if [ $? != 0 ]; then
            echo " failed. Use force-quit"
            exit 1
        else
            echo " done"
        fi
        ;;
    status)
        	if [ -f {pid_file} ];then
			mPID=`cat {pid_file}`
			isStart=`ps ax | awk '{{ print $1 }}' | grep -e "^${{mPID}}$"`
			if [ "$isStart" != '' ];then
				echo "{name} (pid `pidof {name}`) is running."
				exit 1
			else
				echo "{name} is stopped"
				exit 0
			fi
		else
			echo "{name} is stopped"
			exit 0
        fi
        ;;
    restart)
        $0 stop
        sleep 1
        $0 start
        ;;
esac
""".format(name=server_name, pid_file=pid_file, start_exec=start_exec, stop_exec=stop_exec, default_start=default_start)


        if os.path.exists(os.path.join('/etc/init.d/', server_name)):
            return public.returnResult(code=1, msg='操作失败!服务已存在', status=False)
        try:
            public.writeFile(os.path.join('/etc/init.d/', server_name), content)
            os.chmod(os.path.join('/etc/init.d/', server_name), 0o777)
            if os.path.exists('/usr/sbin/update-rc.d'):
                public.ExecShell('update-rc.d -f {} defaults'.format(server_name))
            else:
                public.ExecShell('systemctl enable {}'.format(server_name))
            return public.returnResult(code=1, msg='操作成功!', status=True)
        except:
            return public.returnResult(code=0, msg='操作失败!', status=False)

    # ---------------------- 添加开机自启 启动脚本 end----------------------

    # ---------------------- 删除开机自启 启动脚本 start----------------------
    def del_boot(self, server_name: str) -> dict:
        """
        删除启动脚本
        :param server_name: 服务名称
        :return:
        """
        try:
            if os.path.exists(os.path.join('/etc/init.d/', server_name)):
                if os.path.exists('/usr/sbin/update-rc.d'):
                    public.ExecShell('update-rc.d -f {} remove'.format(server_name))
                else:
                    public.ExecShell('systemctl disable {}'.format(server_name))
                os.remove(os.path.join('/etc/init.d/', server_name))
                return public.returnResult(code=1, msg='操作成功!', status=True)
            return public.returnResult(code=0, msg='操作失败!服务不存在', status=False)
        except:
            return public.returnResult(code=0, msg='操作失败!', status=False)

    # ---------------------- 删除开机自启 启动脚本 end----------------------

    # ---------------------- 创建服务守护进程 start----------------------

    @syssafe_admin
    def create_daemon(self, server_name: str,
                      pid_file: str,
                      start_exec: str,
                      workingdirectory: str,
                      stop_exec: str = None,
                      user: str = 'root',
                      is_power_on: int = 1,
                      logs_file: str = '',
                      environments: str = '',
                      is_fork=None,
                      restart_type='always',
                      fork_time_out=20) -> dict:
        """
        创建服务守护进程
        :param server_name: 服务名称
        :param pid_file: 启动pid记录文件
        :param start_exec: 启动命令
        :param stop_exec: 停止命令
        :return:
        """

        # 检查系统加固插件是否存在
        try:
            if not stop_exec:
                stop_exec = '/usr/bin/pkill -9 "{}"'.format(start_exec)
            content = '''
[Unit]
Description={server_name}
After=network.target

[Service]
{environments}
ExecStart={start_exec}
ExecStop={stop_exec}
WorkingDirectory={workingdirectory}
Restart={restart_type}
SyslogIdentifier={server_name}
User={user}
Type=simple
PrivateTmp=false
PIDFile={pid_file}

[Install]
WantedBy=multi-user.target
'''.format(
                start_exec=start_exec,
                workingdirectory=workingdirectory,
                user=user,
                pid_file=pid_file,
                server_name=server_name,
                environments=environments,
                restart_type=restart_type,
                stop_exec=stop_exec
            )
            exe_shell = ''
            if is_fork or is_fork is None:
                content = content.replace('Type=simple', 'Type=forking')
            if not os.path.exists('/usr/lib/systemd/system/'):
                os.makedirs('/usr/lib/systemd/system/')
            public.writeFile('/usr/lib/systemd/system/{}.service'.format(server_name), content)
            if int(is_power_on) == 1:
                exe_shell += 'systemctl enable {}\n'.format(server_name) + " && "
            else:
                exe_shell += 'systemctl disable {}\n'.format(server_name) + " && "
            exe_shell += 'systemctl daemon-reload' + " && "

            if logs_file:
                rsyslog_conf = public.readFile('/etc/rsyslog.conf')
                add_conf = "if $programname == '{}' then {}\n".format(server_name, logs_file)
                if rsyslog_conf:
                    idx = rsyslog_conf.find("if $programname == '{}' then".format(server_name))
                    if idx == -1:
                        rsyslog_conf += "\n" + add_conf
                    else:
                        line_idx = rsyslog_conf.find('\n', idx)
                        rsyslog_conf = rsyslog_conf[:idx] + add_conf + rsyslog_conf[line_idx:]
                    public.writeFile('/etc/rsyslog.conf', rsyslog_conf)

                exe_shell += 'systemctl restart rsyslog' + " && "
                if not os.path.exists(logs_file):
                    exe_shell += 'touch {}'.format(logs_file) + ' && '
                exe_shell += 'chown -R {user}:{user} {logs_file}'.format(user=user, logs_file=logs_file) + ' && '
            if is_fork is not None:
                exe_shell += 'systemctl restart {}'.format(server_name)
                public.ExecShell(exe_shell)
                return public.returnResult(code=1, msg='操作成功!', status=True)
            public.ExecShell(exe_shell)
            import subprocess, psutil
            try:
                start_time = time.time()
                process = subprocess.Popen(["systemctl", "restart", server_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                while True:
                    try:
                        p = psutil.Process(process.pid)
                        print(p.status())
                        # 检查进程的状态
                        if p.status() == psutil.STATUS_ZOMBIE:
                            break
                    except:
                        pass
                    if process.poll() is not None:
                        break
                    if time.time() - start_time > fork_time_out:
                        raise
                    time.sleep(0.1)
            except:
                content = content.replace('Type=forking','Type=simple')
                public.writeFile('/usr/lib/systemd/system/{}.service'.format(server_name), content)
                public.ExecShell('systemctl daemon-reload && systemctl restart {}'.format(server_name))
            return public.returnResult(code=1, msg='操作成功!', status=True)
        except:
            return public.returnResult(code=0, msg='操作失败!', status=False)

    # ---------------------- 创建服务守护进程 end----------------------

    # ---------------------- 删除服务守护进程 start----------------------
    @syssafe_admin
    def del_daemon(self, server_name: str) -> dict:
        """
        删除服务守护进程
        :param server_name: 服务名称
        :return:
        """
        try:
            public.ExecShell('systemctl stop {}'.format(server_name))
            if os.path.exists('/usr/lib/systemd/system/{}.service'.format(server_name)):
                public.ExecShell('systemctl disable {}'.format(server_name))
                os.remove('/usr/lib/systemd/system/{}.service'.format(server_name))
                public.ExecShell('systemctl daemon-reload')
                public.ExecShell('sed -i "/if \$programname == {}/d" /etc/rsyslog.conf'.format(server_name))
                public.ExecShell('systemctl restart rsyslog')
                return public.returnResult(code=1, msg='操作成功!', status=True)
            return public.returnResult(code=0, msg='操作失败!', status=False)
        except:
            return public.returnResult(code=0, msg='操作失败!', status=False)

    # ---------------------- 删除服务守护进程 end----------------------

    # ---------------------- 服务守护进程状态 start----------------------
    def daemon_status(self, server_name: str) -> dict:
        """
        服务守护进程状态
        :param server_name: 服务名称
        :return:
        """
        try:
            if not os.path.exists('/usr/lib/systemd/system/{}.service'.format(server_name)):
                return public.returnResult(code=0, msg='服务不存在!', status=False)
            if not self.system_info:
                self.system_info = public.ExecShell("systemctl |grep service|grep -E 'active|deactivating'|awk '{print $1}'")[0]
            if server_name+'.service' in self.system_info:
                return public.returnResult(code=1, msg='运行中', status=True)
            return public.returnResult(code=1, msg='未运行', status=False)
        except:
            return public.returnResult(code=0, msg='操作失败!', status=False)

    # ---------------------- 服务守护进程状态 end----------------------

    def daemon_admin(self, server_name: str,action:str) -> dict:
        """

        :param server_name: 项目名称
        :param action: 操作
        """
        public.ExecShell('systemctl {} {}'.format(action,server_name))
        return public.returnResult(code=1, msg='操作指令已执行', status=True)
        # if action == 'start' or action == 'restart':
        #     num = 0
        #     for i in range(5):
        #         time.sleep(0.01)
        #         if self.daemon_status(server_name)['status']:
        #             num += 1
        #         if num > 3:
        #             return public.returnResult(code=1, msg='启动成功!', status=True)
        #     return public.returnResult(code=0, msg='启动失败!', status=False)
        # return public.returnResult(code=1, msg='关闭成功!' + res[0] + res[1], status=True)

    def get_daemon_pid(self, server_name: str) -> dict:
        """
        获取守护进程pid
        :param server_name: 项目名称
        """
        res = public.ExecShell("systemctl show --property=MainPID {}".format(server_name))[0]  # type: str
        if not res.startswith('MainPID='):
            return public.returnResult(code=0, msg='获取失败!', status=False)

        try:
            pid = int(res.split("=", 1)[1])
            return public.returnResult(code=1, msg='获取成功!', data=pid, status=True)
        except:
            return public.returnResult(code=0, msg='获取失败', status=False)


    # ---------------------- 延时定时启动 start----------------------
    def add_task(self, shell: str, time: int) -> dict:
        """
        服务定时启动
        :param server_name: 服务名称
        :param start_exec: 启动命令
        :param minute: 定时启动时间
        :return:
        """
        data = {
            'type': 3,
            'time': time,
            'name': shell,
            'title': '',
            'fun': '',
            'args': ''
        }

        res = public.set_tasks_run(data)
        if res['status']:
            return public.returnResult(code=1, msg='操作成功!', status=True)
        return public.returnResult(code=0, msg='操作失败!', status=False)

    # ---------------------- 服务定时启动 end----------------------


class Server:
    server = RealServer()

    def server_admin(self, get):
        try:
            if hasattr(self.server, get.name):
                return getattr(self.server, get.name)(get.type)
            return public.returnMsg(False, '操作失败!参数不存在')
        except:
            return public.returnMsg(False, '操作失败!')

    def server_status(self, get):
        try:
            if hasattr(self.server, get.name):
                return getattr(self.server, get.name)()
            return public.returnMsg(False, '操作失败!参数不存在')
        except:
            return public.returnMsg(False, '操作失败!')

    def universal_server_admin(self, get):
        try:
            return self.server.universal_server_admin(get.name, get.type)
        except:
            return public.returnMsg(False, '操作失败!')

    def universal_server_status(self, get):
        try:
            return self.server.universal_server_status(get.name)
        except:
            return public.returnMsg(False, '操作失败!')

    def add_boot(self, get):
        try:
            return self.server.add_boot(get.name, get.pid_file, get.start_exec, get.stop_exec)
        except:
            return public.returnMsg(False, '操作失败!')

    def del_boot(self, get):
        try:
            return self.server.del_boot(get.name)
        except:
            return public.returnMsg(False, '操作失败!')

    def create_daemon(self, get):
        try:
            return self.server.create_daemon(get.name, get.pid_file, get.start_exec, get.user)
        except:
            return public.returnMsg(False, '操作失败!')

    def del_daemon(self, get):
        try:
            return self.server.del_daemon(get.name)
        except:
            return public.returnMsg(False, '操作失败!')

    def daemon_status(self, get):
        try:
            return self.server.daemon_status(get.name)
        except:
            return public.returnMsg(False, '操作失败!')

    def add_task(self, get):
        try:
            return self.server.add_task(get.shell, get.time)
        except:
            return public.returnMsg(False, '操作失败!')
