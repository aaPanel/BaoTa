# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: lkq <lkq@bt.cn>
# -------------------------------------------------------------------

# ------------------------------
# Go模型
# ------------------------------

import os, sys, re, json, shutil, psutil, time
import traceback

from projectModel.base import projectBase
from typing import Dict, Union, List, Optional
import public, firewalls, panelSite

try:
    from BTPanel import cache
    from projectModel.btpygvm import pygvm
except:
    pass


class mobj:
    port = ps = ''


class main(projectBase):
    _panel_path = public.get_panel_path()
    _go_path = '/www/server/go_project'
    _log_name = '项目管理'
    _go_pid_path = '/var/tmp/gopids'
    _go_logs_path = "/www/wwwlogs/go"
    _go_logs = '{}/vhost/logs'.format(_go_path)
    _go_run_scripts = '{}/vhost/scripts'.format(_go_path)
    _vhost_path = '{}/vhost'.format(_panel_path)
    _pids = None
    __log_split_script_py = public.get_panel_path() + '/script/run_log_split.py'

    def __init__(self):
        if not os.path.exists(self._go_path):
            os.makedirs(self._go_path, 493)

        if not os.path.exists(self._go_pid_path):
            public.ExecShell("mkdir -p /var/tmp/gopids/ && chmod 777 /var/tmp/gopids/")

        if not os.path.exists(self._go_logs_path):
            public.ExecShell("mkdir -p %s && chmod 777 %s" % (self._go_logs_path, self._go_logs_path))

        if not os.path.exists(self._go_run_scripts):
            public.ExecShell("mkdir -p %s && chmod 777 %s" % (self._go_run_scripts, self._go_run_scripts))

        self._init_gvm()

    def get_system_user(self, get):
        '''
        @name 获取系统所有的用户
        @Author:lkq 2021-09-06
        @return list
        '''
        path = '/etc/passwd'
        user_list = public.ReadFile(path)
        resutl = []
        result2 = ["root", "www", "mysql"]
        if isinstance(user_list, str):
            user_list = user_list.split('\n')
            [resutl.append(x.split(":")[0]) for x in user_list if x.split(":")[0] != '']
            return resutl
        else:
            return result2

    def get_project_find(self, project_name):
        '''
            @name 获取指定项目配置
            @author hwliang<2021-08-09>
            @param project_name<string> 项目名称
            @return dict
        '''
        project_info = public.M('sites').where('project_type=? AND name=?', ('Go', project_name)).find()
        if isinstance(project_info, str):
            raise public.PanelError('数据库查询错误：'+ project_info)
        if not project_info: return False
        project_info['project_config'] = json.loads(project_info['project_config'])
        return project_info

    def get_other_pids(self, pid):
        '''
            @name 获取其他进程pid列表
            @author hwliang<2021-08-10>
            @param pid: string<项目pid>
            @return list
        '''
        plugin_name = None
        for pid_name in os.listdir(self._go_pid_path):
            pid_file = '{}/{}'.format(self._go_pid_path, pid_name)
            try:
                s_pid = int(public.readFile(pid_file))
            except:
                continue
            if pid == s_pid:
                plugin_name = pid_name[:-4]
                break
        project_find = self.get_project_find(plugin_name)
        if not project_find: return []
        if not self._pids: self._pids = psutil.pids()
        all_pids = []
        for i in self._pids:
            try:
                p = psutil.Process(i)
                if p.cwd() == project_find['path'] and p.username() == project_find['project_config']['run_user']:
                    if p.name() in ['node', 'npm', 'pm2']:
                        all_pids.append(i)
            except:
                continue
        return all_pids

    def get_project_pids(self, get=None, pid=None):
        '''
            @name 获取项目进程pid列表
            @author hwliang<2021-08-10>
            @param pid: string<项目pid>
            @return list
        '''
        if get: pid = int(get.pid)
        if not self._pids: self._pids = psutil.pids()
        project_pids = []

        for i in self._pids:
            try:
                p = psutil.Process(i)
                if p.status()=="zombie":
                    continue
                if p.ppid() == pid:
                    if i in project_pids: 
                        continue
                    project_pids.append(i)
            except:
                continue
        other_pids = []
        for i in project_pids:
            other_pids += self.get_project_pids(pid=i)
        if os.path.exists('/proc/{}'.format(pid)):
            project_pids.append(pid)

        all_pids = list(set(project_pids + other_pids))
        if not all_pids:
            all_pids = self.get_other_pids(pid)
        return sorted(all_pids)

    def get_project_run_state(self, get=None, project_name=None):
        '''
            @name 获取项目运行状态
            @author hwliang<2021-08-12>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @param project_name<string> 项目名称
            @return bool
        '''
        if get:
            project_name = get.project_name.strip()
        pid_file = "{}/{}.pid".format(self._go_pid_path, project_name)
        try:
            pid = int(public.readFile(pid_file))
        except:
            pid = 0
        if not pid or not os.path.exists('/proc/{}'.format(pid)):
            pid = self.get_pid_by_command(project_name)
        if not pid:
            return False
        pids = self.get_project_pids(pid=pid)
        if not pids:
            return False
        return True

    def get_pid_by_command(self, project_name: str):
        """
            @name 根据命令获取进程pid
            @author baozi<2024-06-06>
            @param project_name<string> 项目名称
            @return int | None
        """
        project_find = self.get_project_find(project_name)
        project_config = project_find['project_config']
        project_exe = project_config['project_exe']
        project_cmd = project_config['project_cmd']
        cmd_list = self.split_command(project_cmd)
        pids = []
        for i in psutil.process_iter(['pid', 'exe', 'cmdline']):
            try:
                if i.status() == "zombie":
                    continue
                if project_exe == i.exe() and cmd_list[1:] == i.cmdline()[1:]:
                    pids.append(i.pid)
            except:
                pass

        running_pid = []
        for pid in pids:
            if pid in psutil.pids():
                running_pid.append(pid)

        if len(running_pid) == 1:
            pid_file = "{}/{}.pid".format(self._go_pid_path, project_name)
            public.writeFile(pid_file, str(running_pid[0]))
            return running_pid[0]

        main_pid = []
        for pid in running_pid:
            p = psutil.Process(pid)
            if p.ppid() not in running_pid:
                main_pid.append(pid)

        if len(main_pid) == 1:
            pid_file = "{}/{}.pid".format(self._go_pid_path, project_name)
            public.writeFile(pid_file, str(main_pid[0]))
            return main_pid[0]

        return None

    @staticmethod
    def split_command(command: str):
        res = []
        tmp = ""
        in_quot = False
        for i in command:
            if i in (' ', '\t', '\r'):
                if tmp and not in_quot:
                    res.append(tmp)
                    tmp = ""
                if in_quot:
                    tmp += ' '

            elif i in ("'", '"'):
                in_quot = not in_quot
            else:
                tmp += i

        if tmp:
            res.append(tmp)

        return res

    def get_process_cpu_time(self, cpu_times):
        cpu_time = 0.00
        for s in cpu_times: cpu_time += s
        return cpu_time

    def get_cpu_precent(self, p):
        '''
            @name 获取进程cpu使用率
            @author hwliang<2021-08-09>
            @param p: Process<进程对像>
            @return dict
        '''
        skey = "cpu_pre_{}".format(p.pid)
        old_cpu_times = cache.get(skey)

        process_cpu_time = self.get_process_cpu_time(p.cpu_times())
        if not old_cpu_times:
            cache.set(skey, [process_cpu_time, time.time()], 3600)
            # time.sleep(0.1)
            old_cpu_times = cache.get(skey)
            process_cpu_time = self.get_process_cpu_time(p.cpu_times())

        old_process_cpu_time = old_cpu_times[0]
        old_time = old_cpu_times[1]
        new_time = time.time()
        cache.set(skey, [process_cpu_time, new_time], 3600)
        percent = round(100.00 * (process_cpu_time - old_process_cpu_time) / (new_time - old_time) / psutil.cpu_count(), 2)
        return percent

    def format_connections(self, connects):
        '''
            @name 获取进程网络连接信息
            @author hwliang<2021-08-09>
            @param connects<pconn>
            @return list
        '''
        result = []
        for i in connects:
            raddr = i.raddr
            if not i.raddr:
                raddr = ('', 0)
            laddr = i.laddr
            if not i.laddr:
                laddr = ('', 0)
            result.append({
                "fd": i.fd,
                "family": i.family,
                "local_addr": laddr[0],
                "local_port": laddr[1],
                "client_addr": raddr[0],
                "client_rport": raddr[1],
                "status": i.status
            })
        return result

    def get_connects(self, pid):
        '''
            @name 获取进程连接信息
            @author hwliang<2021-08-09>
            @param pid<int>
            @return dict
        '''
        connects = 0
        try:
            if pid == 1: return connects
            tp = '/proc/' + str(pid) + '/fd/'
            if not os.path.exists(tp): return connects
            for d in os.listdir(tp):
                fname = tp + d
                if os.path.islink(fname):
                    l = os.readlink(fname)
                    if l.find('socket:') != -1: connects += 1
        except:
            pass
        return connects

    def object_to_dict(self, obj):
        '''
            @name 将对象转换为字典
            @author hwliang<2021-08-09>
            @param obj<object>
            @return dict
        '''
        result = {}
        for name in dir(obj):
            value = getattr(obj, name)
            if not name.startswith('__') and not callable(value) and not name.startswith('_'): result[name] = value
        return result

    def list_to_dict(self, data):
        '''
            @name 将列表转换为字典
            @author hwliang<2021-08-09>
            @param data<list>
            @return dict
        '''
        result = []
        for s in data:
            result.append(self.object_to_dict(s))
        return result

    def get_process_info_by_pid(self, pid):
        '''
            @name 获取进程信息
            @author hwliang<2021-08-12>
            @param pid: int<进程id>
            @return dict
        '''
        process_info = {}
        try:
            if not os.path.exists('/proc/{}'.format(pid)): return process_info
            p = psutil.Process(pid)
            status_ps = {'sleeping': '睡眠', 'running': '活动'}
            with p.oneshot():
                p_mem = p.memory_full_info()
                if p_mem.uss + p_mem.rss + p_mem.pss + p_mem.data == 0: return process_info
                p_state = p.status()
                if p_state in status_ps: p_state = status_ps[p_state]
                # process_info['exe'] = p.exe()
                process_info['name'] = p.name()
                process_info['pid'] = pid
                process_info['ppid'] = p.ppid()
                process_info['create_time'] = int(p.create_time())
                process_info['status'] = p_state
                process_info['user'] = p.username()
                process_info['memory_used'] = p_mem.uss
                process_info['cpu_percent'] = self.get_cpu_precent(p)
                process_info['io_write_bytes'], process_info['io_read_bytes'] = self.get_io_speed(p)
                process_info['connections'] = self.format_connections(p.connections())
                process_info['connects'] = self.get_connects(pid)
                process_info['open_files'] = self.list_to_dict(p.open_files())
                process_info['threads'] = p.num_threads()
                process_info['exe'] = ' '.join(p.cmdline())
                return process_info
        except:
            return process_info

    def get_io_speed(self, p):
        '''
            @name 获取磁盘IO速度
            @author hwliang<2021-08-12>
            @param p: Process<进程对像>
            @return list
        '''
        skey = "io_speed_{}".format(p.pid)
        old_pio = cache.get(skey)
        if not hasattr(p, 'io_counters'): return 0, 0
        pio = p.io_counters()
        if not old_pio:
            cache.set(skey, [pio, time.time()], 3600)
            # time.sleep(0.1)
            old_pio = cache.get(skey)
            pio = p.io_counters()

        old_write_bytes = old_pio[0].write_bytes
        old_read_bytes = old_pio[0].read_bytes
        old_time = old_pio[1]

        new_time = time.time()
        write_bytes = pio.write_bytes
        read_bytes = pio.read_bytes

        cache.set(skey, [pio, new_time], 3600)

        write_speed = int((write_bytes - old_write_bytes) / (new_time - old_time))
        read_speed = int((read_bytes - old_read_bytes) / (new_time - old_time))

        return write_speed, read_speed

    def get_project_load_info(self, get=None, project_name=None):
        '''
            @name 获取项目负载信息
            @author hwliang<2021-08-12>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        if get: project_name = get.project_name.strip()
        load_info = {}
        pid_file = "{}/{}.pid".format(self._go_pid_path, project_name)
        if not os.path.exists(pid_file): return load_info
        try:
            pid = int(public.readFile(pid_file))
        except:
            return load_info
        pids = self.get_project_pids(pid=pid)
        if not pids: return load_info
        for i in pids:
            process_info = self.get_process_info_by_pid(i)
            if process_info: load_info[i] = process_info
        return load_info

    def get_ssl_end_date(self, project_name):
        '''
            @name 获取SSL信息
            @author hwliang<2021-08-09>
            @param project_name <string> 项目名称
            @return dict
        '''
        import data
        return data.data().get_site_ssl_info('go_{}'.format(project_name))

    def get_project_stat(self, project_info, has_load_info=True):
        '''
            @name 获取项目状态信息
            @author hwliang<2021-08-09>
            @param project_info<dict> 项目信息
            @param has_load_info<bool> 是否获取项目信息  后续发现并非获取load_info导致的接口缓慢，故默认为True
            @return list
        '''
        if isinstance(project_info['project_config'],str):
            project_info['project_config'] = json.loads(project_info['project_config'])
        project_info['run'] = self.get_project_run_state(project_name=project_info['name'])
        if has_load_info is True:
            project_info['load_info'] = self.get_project_load_info(project_name=project_info['name'])
        project_info['ssl'] = self.get_ssl_end_date(project_name=project_info['name'])
        project_info['listen'] = []
        project_info['listen_ok'] = True
        if 'load_info' in project_info and project_info['load_info']:
            for pid in project_info['load_info'].keys():
                if not 'connections' in project_info['load_info'][pid]:
                    project_info['load_info'][pid]['connections'] = []
                for conn in project_info['load_info'][pid]['connections']:
                    if not conn['status'] == 'LISTEN': continue
                    if not conn['local_port'] in project_info['listen']:
                        project_info['listen'].append(conn['local_port'])
            if project_info['listen']:
                project_info['listen_ok'] = project_info['project_config']['port'] in project_info['listen']

        if not project_info['listen'] and project_info['run']:
            project_info['listen'] = self.get_project_listen(project_name=project_info['name'])
            if project_info['listen']:
                project_info['listen_ok'] = project_info['project_config']['port'] in project_info['listen']

        return project_info

    def get_project_listen(self, project_name):
        pid_file = "{}/{}.pid".format(self._go_pid_path, project_name)
        try:
            process_pid = int(public.readFile(pid_file))
        except:
            return []
        pids = self.get_project_pids(pid=process_pid)
        ports = set()
        # 获取指定进程及其子进程的所有连接
        connections = psutil.net_connections()

        # 遍历连接，筛选出指定进程及其子进程的连接
        for conn in connections:
            if conn.pid in set(pids):
                if conn.laddr and conn.status == 'LISTEN':
                    ports.add(conn.laddr.port)

        return list(ports)

    def exists_nginx_ssl(self, project_name):
        '''
            @name 判断项目是否配置Nginx SSL配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return tuple
        '''
        config_file = "{}/nginx/go_{}.conf".format(public.get_vhost_path(), project_name)
        if not os.path.exists(config_file):
            return False, False

        config_body = public.readFile(config_file)
        if not config_body:
            return False, False

        is_ssl, is_force_ssl = False, False
        if config_body.find('ssl_certificate') != -1:
            is_ssl = True
        if config_body.find('HTTP_TO_HTTPS_START') != -1:
            is_force_ssl = True
        return is_ssl, is_force_ssl

    def check_port_is_used(self, port, sock=False):
        '''
            @name 检查端口是否被占用
            @author hwliang<2021-08-09>
            @param port: int<端口>
            @return bool
        '''
        if not isinstance(port, int): port = int(port)
        if port == 0: return False
        project_list = public.M('sites').where('status=? AND project_type=?', (1, 'Go')).field('name,path,project_config').select()
        for project_find in project_list:
            project_config = json.loads(project_find['project_config'])
            if not 'port' in project_config: continue
            try:
                if int(project_config['port']) == port:
                    return True
            except:
                continue
        if sock: return False
        return public.check_tcp('127.0.0.1', port)

    def exists_apache_ssl(self, project_name):
        '''
            @name 判断项目是否配置Apache SSL配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return bool
        '''
        config_file = "{}/apache/go_{}.conf".format(public.get_vhost_path(), project_name)
        if not os.path.exists(config_file):
            return False, False

        config_body = public.readFile(config_file)
        if not config_body:
            return False, False

        is_ssl, is_force_ssl = False, False
        if config_body.find('SSLCertificateFile') != -1:
            is_ssl = True
        if config_body.find('HTTP_TO_HTTPS_START') != -1:
            is_force_ssl = True
        return is_ssl, is_force_ssl

    def set_apache_config(self, project_find):
        '''
            @name 设置Apache配置
            @author hwliang<2021-08-09>
            @param project_find: dict<项目信息>
            @return bool
        '''
        project_name = project_find['name']

        # 处理域名和端口
        ports = []
        domains = []
        for d in project_find['project_config']['domains']:
            domain_tmp = d.split(':')
            if len(domain_tmp) == 1: domain_tmp.append(80)
            if not int(domain_tmp[1]) in ports:
                ports.append(int(domain_tmp[1]))
            if not domain_tmp[0] in domains:
                domains.append(domain_tmp[0])

        config_file = "{}/apache/go_{}.conf".format(self._vhost_path, project_name)
        template_file = "{}/template/apache/go_http.conf".format(self._vhost_path)
        config_body = public.readFile(template_file)
        apache_config_body = ''

        # 旧的配置文件是否配置SSL
        is_ssl, is_force_ssl = self.exists_apache_ssl(project_name)
        if is_ssl:
            if not 443 in ports: ports.append(443)

        from panelSite import panelSite
        s = panelSite()

        # 根据端口列表生成配置
        for p in ports:
            # 生成SSL配置
            ssl_config = ''
            if p == 443 and is_ssl:
                ssl_key_file = "{vhost_path}/cert/{project_name}/privkey.pem".format(project_name=project_name, vhost_path=public.get_vhost_path())
                if not os.path.exists(ssl_key_file): continue  # 不存在证书文件则跳过
                ssl_config = '''#SSL
    SSLEngine On
    SSLCertificateFile {vhost_path}/cert/{project_name}/fullchain.pem
    SSLCertificateKeyFile {vhost_path}/cert/{project_name}/privkey.pem
    SSLCipherSuite EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5
    SSLProtocol All -SSLv2 -SSLv3 -TLSv1
    SSLHonorCipherOrder On'''.format(project_name=project_name, vhost_path=public.get_vhost_path())
            else:
                if is_force_ssl:
                    ssl_config = '''#HTTP_TO_HTTPS_START
    <IfModule mod_rewrite.c>
        RewriteEngine on
        RewriteCond %{SERVER_PORT} !^443$
        RewriteRule (.*) https://%{SERVER_NAME}$1 [L,R=301]
    </IfModule>
    #HTTP_TO_HTTPS_END'''

            # 生成vhost主体配置
            apache_config_body += config_body.format(
                site_path=project_find['path'],
                server_name='{}.{}'.format(p, project_name),
                domains=' '.join(domains),
                log_path=public.get_logs_path(),
                server_admin='admin@{}'.format(project_name),
                url='http://127.0.0.1:{}'.format(project_find['project_config']['port']),
                port=p,
                ssl_config=ssl_config,
                project_name=project_name
            )
            apache_config_body += "\n"

            # 添加端口到主配置文件
            if not p in [80]:
                s.apacheAddPort(p)

        # 写.htaccess
        rewrite_file = "{}/.htaccess".format(project_find['path'].rsplit("/", 1)[0])  # go项目路径是运行文件，不是项目根目录
        if not os.path.exists(rewrite_file): public.writeFile(rewrite_file, '# 请将伪静态规则或自定义Apache配置填写到此处\n')
        from mod.base.web_conf import ap_ext
        apache_config_body = ap_ext.set_extension_by_config(project_name, apache_config_body)

        # 写配置文件
        public.writeFile(config_file, apache_config_body)
        return True

    def set_nginx_config(self, project_find):
        '''
            @name 设置Nginx配置
            @author hwliang<2021-08-09>
            @param project_find: dict<项目信息>
            @return bool
        '''
        project_name = project_find['name']
        ports = []
        domains = []

        for d in project_find['project_config']['domains']:
            domain_tmp = d.split(':')
            if len(domain_tmp) == 1: domain_tmp.append(80)
            if not int(domain_tmp[1]) in ports:
                ports.append(int(domain_tmp[1]))
            if not domain_tmp[0] in domains:
                domains.append(domain_tmp[0])
        listen_ipv6 = public.listen_ipv6()
        is_ssl, is_force_ssl = self.exists_nginx_ssl(project_name)
        listen_ports_list = []
        for p in ports:
            listen_ports_list.append("    listen {};".format(p))
            if listen_ipv6:
                listen_ports_list.append("    listen [::]:{};".format(p))

        ssl_config = ''
        if is_ssl:
            http3_header = ""
            if self.is_nginx_http3():
                http3_header = '''\n    add_header Alt-Svc 'quic=":443"; h3=":443"; h3-29=":443"; h3-27=":443";h3-25=":443"; h3-T050=":443"; h3-Q050=":443";h3-Q049=":443";h3-Q048=":443"; h3-Q046=":443"; h3-Q043=":443"';'''

            nginx_ver = public.nginx_version()
            if nginx_ver:
                port_str = ["443"]
                if listen_ipv6:
                    port_str.append("[::]:443")
                use_http2_on = False
                for p in port_str:
                    listen_str = "    listen {} ssl".format(p)
                    if nginx_ver < [1, 9, 5]:
                        listen_str += ";"
                    elif [1, 9, 5] <= nginx_ver < [1, 25, 1]:
                        listen_str += " http2;"
                    else:  # >= [1, 25, 1]
                        listen_str += ";"
                        use_http2_on = True
                    listen_ports_list.append(listen_str)

                    if self.is_nginx_http3():
                        listen_ports_list.append("    listen {} quic;".format(p))
                if use_http2_on:
                    listen_ports_list.append("    http2 on;")

            else:
                listen_ports_list.append("    listen 443 ssl;")

            ssl_config = '''ssl_certificate    {vhost_path}/cert/{priject_name}/fullchain.pem;
    ssl_certificate_key    {vhost_path}/cert/{priject_name}/privkey.pem;
    ssl_protocols TLSv1.1 TLSv1.2 TLSv1.3;
    ssl_ciphers EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    add_header Strict-Transport-Security "max-age=31536000";{http3_header}
    error_page 497  https://$host$request_uri;'''.format(vhost_path=self._vhost_path, priject_name=project_name, http3_header=http3_header)

            if is_force_ssl:
                ssl_config += '''
    #HTTP_TO_HTTPS_START
    if ($server_port !~ 443){
        rewrite ^(/.*)$ https://$host$1 permanent;
    }
    #HTTP_TO_HTTPS_END'''

        config_file = "{}/nginx/go_{}.conf".format(self._vhost_path, project_name)
        template_file = "{}/template/nginx/go_http.conf".format(self._vhost_path)

        listen_ports = "\n".join(listen_ports_list).strip()

        config_body = public.readFile(template_file)
        mut_config = {
            "site_path": project_find['path'],
            "domains": ' '.join(domains),
            "url": 'http://127.0.0.1:{}'.format(project_find['project_config']['port']),
            "ssl_config": ssl_config,
            "listen_ports": listen_ports
        }
        config_body = config_body.format(
            site_path=mut_config["site_path"],
            domains=mut_config["domains"],
            project_name=project_name,
            panel_path=self._panel_path,
            log_path=public.get_logs_path(),
            url=mut_config["url"],
            host='$host',
            listen_ports=listen_ports,
            ssl_config=mut_config["ssl_config"]
        )

        # # 恢复旧的SSL配置
        # ssl_config = self.get_nginx_ssl_config(project_name)
        # if ssl_config:
        #     config_body.replace('#error_page 404/404.html;',ssl_config)

        rewrite_file = "{panel_path}/vhost/rewrite/go_{project_name}.conf".format(panel_path=self._panel_path,
                                                                                  project_name=project_name)
        if not os.path.exists(rewrite_file):
            public.writeFile(rewrite_file, '# 请将伪静态规则或自定义NGINX配置填写到此处\n')
        apply_check = "{}/vhost/nginx/well-known/{}.conf".format(self._panel_path, project_name)
        if not os.path.exists("/www/server/panel/vhost/nginx/well-known"):
            os.makedirs("/www/server/panel/vhost/nginx/well-known", 0o600)
        if not os.path.exists(apply_check):
            public.writeFile(apply_check, '')
        from mod.base.web_conf import ng_ext
        config_body = ng_ext.set_extension_by_config(project_name, config_body)
        if not os.path.exists(config_file):
            public.writeFile(config_file, config_body)
        else:
            if not self._replace_nginx_conf(config_file, mut_config):
                public.writeFile(config_file, config_body)
        return True

    @staticmethod
    def _replace_nginx_conf(config_file, mut_config: dict) -> bool:
        """尝试替换"""
        data: str = public.readFile(config_file)
        tab_spc = "    "
        rep_list = [
            (
                r"([ \f\r\t\v]*listen[^;\n]*;\n(\s*http2\s+on\s*;[^\n]*\n)?)+",
                tab_spc + mut_config["listen_ports"] + "\n"
            ),
            (
                r"[ \f\r\t\v]*root [ \f\r\t\v]*/[^;\n]*;",
                "    root {};".format(mut_config["site_path"])
            ),
            (
                r"[ \f\r\t\v]*server_name [ \f\r\t\v]*[^\n;]*;",
                "    server_name {};".format(mut_config["domains"])
            ),
            (
                r"[ \f\r\t\v]*location */ *\{ *\n *proxy_pass[^\n;]*;\n *proxy_set_header *Host",
                "{}location / {{\n{}proxy_pass {};\n{}proxy_set_header Host".format(
                    tab_spc, tab_spc * 2, mut_config["url"], tab_spc * 2, )
            ),
            (
                "[ \f\r\t\v]*#SSL-START(.*\n){2,15}[ \f\r\t\v]*#SSL-END",
                "{}#SSL-START SSL相关配置\n{}#error_page 404/404.html;\n{}{}\n{}#SSL-END".format(
                    tab_spc, tab_spc, tab_spc, mut_config["ssl_config"], tab_spc)
            )
        ]
        for rep, info in rep_list:
            if re.search(rep, data):
                data = re.sub(rep, info, data, 1)
            else:
                return False

        public.writeFile(config_file, data)
        return True

    def clear_nginx_config(self, project_find):
        '''
            @name 清除nginx配置
            @author hwliang<2021-08-09>
            @param project_find: dict<项目信息>
            @return bool
        '''
        project_name = project_find['name']
        config_file = "{}/nginx/go_{}.conf".format(self._vhost_path, project_name)
        if os.path.exists(config_file):
            os.remove(config_file)
        rewrite_file = "{panel_path}/vhost/rewrite/go_{project_name}.conf".format(panel_path=self._panel_path, project_name=project_name)
        if os.path.exists(rewrite_file):
            os.remove(rewrite_file)
        return True

    def clear_apache_config(self, project_find):
        '''
            @name 清除apache配置
            @author hwliang<2021-08-09>
            @param project_find: dict<项目信息>
            @return bool
        '''
        project_name = project_find['name']
        config_file = "{}/apache/go_{}.conf".format(self._vhost_path, project_name)
        if os.path.exists(config_file):
            os.remove(config_file)
        return True

    def clear_config(self, project_name):
        '''
            @name 清除项目配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return bool
        '''
        project_find = self.get_project_find(project_name)
        if not project_find: return False
        self.clear_nginx_config(project_find)
        self.clear_apache_config(project_find)
        public.serviceReload()
        return True

    def set_config(self, project_name):
        '''
            @name 设置项目配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return bool
        '''
        project_find = self.get_project_find(project_name)
        if not project_find: return False
        if not project_find['project_config']: return False
        if not project_find['project_config']['bind_extranet']: return False
        if not project_find['project_config']['domains']: return False
        self.set_nginx_config(project_find)
        self.set_apache_config(project_find)
        public.serviceReload()
        return True

    def kill_pids(self, get=None, pids=None):
        '''
            @name 结束进程列表
            @author hwliang<2021-08-10>
            @param pids: string<进程pid列表>
            @return dict
        '''
        if get: pids = get.pids
        if not pids: return public.return_data(True, '没有进程')
        pids = sorted(pids, reverse=True)
        for i in pids:
            try:
                p = psutil.Process(i)
                p.terminate()
            except:
                pass
        return public.return_data(True, '进程已全部结束')

    def bind_extranet(self, get):
        '''
            @name 绑定外网
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        res_msg = self._check_webserver()
        if res_msg:
            return public.return_error(res_msg)
        project_name = get.project_name.strip()
        project_find = self.get_project_find(project_name)
        if not project_find: return public.return_error('项目不存在')
        if not project_find['project_config']['domains']: return public.return_error('请先到【域名管理】选项中至少添加一个域名')
        project_find['project_config']['bind_extranet'] = 1
        public.M('sites').where("id=?", (project_find['id'],)).setField('project_config', json.dumps(project_find['project_config']))
        self.set_config(project_name)
        public.WriteLog(self._log_name, 'Go项目{}, 开启外网映射'.format(project_name))
        return public.return_data(True, '开启外网映射成功')

    def unbind_extranet(self, get):
        '''
            @name 解绑外网
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        project_name = get.project_name.strip()
        self.clear_config(project_name)
        public.serviceReload()
        project_find = self.get_project_find(project_name)
        project_find['project_config']['bind_extranet'] = 0
        public.M('sites').where("id=?", (project_find['id'],)).setField('project_config', json.dumps(project_find['project_config']))
        public.WriteLog(self._log_name, 'Go项目{}, 关闭外网映射'.format(project_name))
        return public.return_data(True, '关闭成功')

    def restart_project(self, get):
        '''
            @name 重启项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        project_find = self.get_project_find(get.project_name)
        # 2024.4.3 修复项目过期时间判断不对
        mEdate = time.strftime('%Y-%m-%d', time.localtime())
        if project_find['edate'] != "0000-00-00" and project_find['edate'] < mEdate:
            return public.return_error('当前项目已过期，请重新设置项目到期时间')
        res = self.stop_project(get)
        if not res['status']: return res

        res = self.start_project(get)
        if not res['status']: return res
        return public.return_data(True, '重启成功')

    def stop_project(self, get):
        '''
            @name 停止项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        pid_file = "{}/{}.pid".format(self._go_pid_path, get.project_name)
        if not os.path.exists(pid_file): return public.return_error('项目未启动')
        try:
            pid = int(public.readFile(pid_file))
        except:
            return public.return_error('项目未启动')
        pids = self.get_project_pids(pid=pid)
        if not pids: return public.return_error('项目未启动')

        project_find = self.get_project_find(get.project_name)
        # 2024.4.3 修复项目过期时间判断不对
        mEdate = time.strftime('%Y-%m-%d', time.localtime())
        if project_find['edate'] != "0000-00-00" and project_find['edate'] < mEdate:
            return public.return_error('当前项目已过期，请重新设置项目到期时间')

        self.kill_pids(pids=pids)
        if os.path.exists(pid_file): os.remove(pid_file)
        self.stop_by_user(self.get_project_find(get.project_name)["id"])
        return public.return_data(True, '停止成功')

    def start_project(self, get):
        '''
            @name 启动项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        if not os.path.exists(self._go_pid_path):
            public.ExecShell("mkdir -p /var/tmp/gopids/ && chmod 777 /var/tmp/gopids/")
        else:
            ret = public.get_mode_and_user("/var/tmp/gopids/")
            if isinstance(ret, dict):
                if ret['mode'] != 777:
                    public.ExecShell("chmod 777 /var/tmp/gopids/")
        project_find = self.get_project_find(get.project_name)
        if not project_find: return public.returnMsg(False, '项目不存在')
        # 2024.4.3 修复项目过期时间判断不对
        mEdate = time.strftime('%Y-%m-%d', time.localtime())
        if project_find['edate'] != "0000-00-00" and project_find['edate'] < mEdate:
            return public.return_error('当前项目已过期，请重新设置项目到期时间')

        self._update_project(get.project_name, project_find)
        log_file = "{}/{}.log".format(project_find['project_config']["log_path"], project_find["name"])
        pid_file = "{}/{}.pid".format(self._go_pid_path, get.project_name)
        # public.writeFile(log_file,"")
        public.set_own(log_file, project_find['project_config']['run_user'])
        project_cmd = project_find["project_config"]['project_cmd']
        project_log_status = project_find["project_config"].get('project_log', 1)
        log_exec = ''
        if int(project_log_status):
            log_exec = " &>> {}".format(log_file)
        if 'project_path' in project_find['project_config']:
            jar_path = project_find['project_config']['project_path']
        else:
            jar_path = '/root'

        project_config = project_find["project_config"]
        pre_sh_list = []
        if 'env_file' in project_config:
            env_file = project_config['env_file']
            if os.path.isfile(env_file):
                pre_sh_list.append("source {}".format(env_file))
        if "env_list" in project_config:
            for env in project_config['env_list']:
                if "k" in env and "v" in env:
                    pre_sh_list.append("export {}={}".format(env['k'], env['v']))

        # 启动脚本
        start_cmd = '''#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
cd {jar_path}
{pre_sh}
nohup {project_cmd} {log_exec} &
echo $! > {pid_file}'''.format(
            jar_path=jar_path,
            project_cmd=project_cmd,
            pid_file=pid_file,
            log_exec=log_exec,
            pre_sh="\n".join(pre_sh_list),
        )

        script_file = "{}/{}.sh".format(self._go_run_scripts, get.project_name)
        # 写入启动脚本
        public.writeFile(script_file, start_cmd)
        if os.path.exists(pid_file): os.remove(pid_file)

        if not os.path.exists(log_file):
            public.ExecShell("touch  {}".format(log_file))
        public.ExecShell("chown  {}:{} {}".format(project_find['project_config']['run_user'],
                                                  project_find['project_config']['run_user'], log_file))
        self._pass_dir_for_user(os.path.dirname(log_file), project_find['project_config']['run_user'])

        public.ExecShell("chown -R {}:{} {}".format(project_find['project_config']['run_user'], project_find['project_config']['run_user'], jar_path))
        public.set_mode(script_file, 755)
        public.set_own(script_file, project_find['project_config']['run_user'])
        # 执行脚本文件
        p = public.ExecShell("bash {}".format(script_file), user=project_find['project_config']['run_user'], env=os.environ.copy())
        time.sleep(1)
        if not os.path.exists(pid_file):
            return public.returnMsg(False, '启动失败,请尝试切换启动用户')
        # 获取PID
        try:
            pid = int(public.readFile(pid_file))
        except:
            return public.returnMsg(False, '启动失败{}'.format(p.replace("\n", "<br>")))
        pids = self.get_project_pids(pid=pid)
        if not pids:
            if os.path.exists(pid_file): os.remove(pid_file)
            return public.returnMsg(False, '启动失败<br>{}'.format(public.GetNumLines(log_file, 20).replace("\n", "<br>")))
        # return public.returnMsg(True, '启动成功')

        self.start_by_user(project_find["id"])
        return public.return_data(True, '启动成功')

    def get_project_list(self, get):
        '''
            @name 获取项目列表
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''

        if not 'p' in get:  get.p = 1
        if not 'limit' in get: get.limit = 20
        if not 'callback' in get: get.callback = ''
        if not 'order' in get: get.order = 'id desc'
        type_id = None
        if "type_id" in get:
            try:
                type_id = int(get.type_id)
            except:
                type_id = None

        if 'search' in get:
            get.project_name = get.search.strip()
            search = "%{}%".format(get.project_name)
            if type_id is None:
                count = public.M('sites').where('project_type=? AND (name LIKE ? OR ps LIKE ?)', ('Go', search, search)).count()
                data = public.get_page(count, int(get.p), int(get.limit), get.callback)
                data['data'] = public.M('sites').where('project_type=? AND (name LIKE ? OR ps LIKE ?)', ('Go', search, search)).limit(data['shift'] + ',' + data['row']).order(get.order).select()
            else:
                count = public.M('sites').where('project_type=? AND (name LIKE ? OR ps LIKE ?) AND type_id = ?',
                                                ('Go', search, search, type_id)).count()
                data = public.get_page(count, int(get.p), int(get.limit), get.callback)
                data['data'] = public.M('sites').where('project_type=? AND (name LIKE ? OR ps LIKE ?) AND type_id = ?', ('Go', search, search, type_id)).limit(data['shift'] + ',' + data['row']).order(
                    get.order).select()
        else:
            if type_id is None:
                count = public.M('sites').where('project_type=?', 'Go').count()
                data = public.get_page(count, int(get.p), int(get.limit), get.callback)
                data['data'] = public.M('sites').where('project_type=?', 'Go').limit(data['shift'] + ',' + data['row']).order(get.order).select()
            else:
                count = public.M('sites').where('project_type=? AND type_id = ?', ('Go', type_id)).count()
                data = public.get_page(count, int(get.p), int(get.limit), get.callback)
                data['data'] = public.M('sites').where('project_type=? AND type_id = ?', ('Go', type_id)).limit(data['shift'] + ',' + data['row']).order(get.order).select()

        if isinstance(data["data"], str) and data["data"].startswith("error"):
            raise public.PanelError("数据库查询错误：" + data["data"])

        for i in range(len(data['data'])):
            data['data'][i] = self.get_project_stat(data['data'][i])
        return data

    #  设置批量网站到期时间
    def set_site_etime_multiple(self, get):
        '''
            @name 批量网站到期时间
            @param sites_id "1,2"
            @param edate 2023-11-30
        '''
        if not hasattr(get, 'sites_id'):
            return public.return_error('sites_id不可缺少！')
        sites_id = get.sites_id.split(',')
        set_edate_successfully = []
        set_edate_failed = {}
        for site_id in sites_id:
            get.id = site_id
            site_name = public.M('sites').where("id=?", (site_id,)).getField('name')
            if not site_name:
                continue

            if hasattr(get, 'edate') and get.edate != '':
                public.M('sites').where('id=?', (get.id,)).setField('edate', get.edate)
                public.WriteLog('TYPE_SITE', 'SITE_EXPIRE_SUCCESS', (site_name, get.edate))
                set_edate_successfully.append(site_name)
            else:
                set_edate_failed[site_name] = '设置时错误了，请再试一次'

        return {'status': True, 'msg': '设置网站 [ {} ] 到期时间成功'.format(','.join(set_edate_successfully)), 'error': set_edate_failed,
                'success': set_edate_successfully}

    def project_get_domain(self, get):
        '''
            @name 获取指定项目的域名列表
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        project_id = public.M('sites').where('name=?', (get.project_name,)).getField('id')
        if not project_id:
            return public.return_data(False, '站点查询失败')
        domains = public.M('domain').where('pid=?', (project_id,)).order('id desc').select()
        # project_find = self.get_project_find(get.project_name)
        # if not project_find:
        #     return public.return_data(False, '站点查询失败')
        # if len(domains) != len(project_find['project_config']['domains']):
        #     public.M('domain').where('pid=?', (project_id,)).delete()
        #     if not project_find: return []
        #     for d in project_find['project_config']['domains']:
        #         domain = {}
        #         arr = d.split(':')
        #         if len(arr) < 2: arr.append(80)
        #         domain['name'] = arr[0]
        #         domain['port'] = int(arr[1])
        #         domain['pid'] = project_id
        #         domain['addtime'] = public.getDate()
        #         public.M('domain').insert(domain)
        #     if project_find['project_config']['domains']:
        #         domains = public.M('domain').where('pid=?', (project_id,)).select()
        return domains

    def project_remove_domain(self, get):
        '''
            @name 为指定项目删除域名
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
                domain: string<域名>
            }
            @return dict
        '''
        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return public.return_error('指定项目不存在')
        last_domain = get.domain
        domain_arr = get.domain.split(':')
        if len(domain_arr) == 1:
            domain_arr.append(80)

        project_id = public.M('sites').where('name=?', (get.project_name,)).getField('id')
        if len(project_find['project_config']['domains']) == 1: return public.return_error('项目至少需要一个域名')
        domain_id = public.M('domain').where('name=? AND pid=?', (domain_arr[0], project_id)).getField('id')
        if not domain_id:
            return public.return_error('指定域名不存在')
        public.M('domain').where('id=?', (domain_id,)).delete()

        if get.domain in project_find['project_config']['domains']:
            project_find['project_config']['domains'].remove(get.domain)
        if get.domain + ":80" in project_find['project_config']['domains']:
            project_find['project_config']['domains'].remove(get.domain + ":80")

        public.M('sites').where('id=?', (project_id,)).save('project_config', json.dumps(project_find['project_config']))
        public.WriteLog(self._log_name, '从项目：{}，删除域名{}'.format(get.project_name, get.domain))
        self.set_config(get.project_name)
        return public.return_data(True, '删除域名成功')

    def project_add_domain(self, get):
        '''
            @name 为指定项目添加域名
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
                domains: list<域名列表>
            }
            @return dict
        '''
        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return public.return_error('指定项目不存在')
        project_id = project_find['id']
        domains = get.domains
        check_cloud = False
        flag = False
        res_domains = []
        for domain in domains:
            domain = domain.strip()
            if not domain: continue
            domain_arr = domain.split(':')
            domain_arr[0] = self.check_domain(domain_arr[0])
            if domain_arr[0] is False:
                res_domains.append({"name": domain, "status": False, "msg": '域名格式错误'})
                continue
            if len(domain_arr) == 1:
                domain_arr.append("")
            if domain_arr[1] == "":
                domain_arr[1] = 80
                domain += ':80'
            try:
                if not (0 < int(domain_arr[1]) < 65535):
                    res_domains.append({"name": domain, "status": False, "msg": '域名格式错误'})
                    continue
            except ValueError:
                res_domains.append({"name": domain, "status": False, "msg": '域名格式错误'})
                continue

            if not public.M('domain').where('name=?', (domain_arr[0],)).count():
                public.M('domain').add('name,pid,port,addtime', (domain_arr[0], project_id, domain_arr[1], public.getDate()))
                if not domain in project_find['project_config']['domains']:
                    project_find['project_config']['domains'].append(domain)
                public.WriteLog(self._log_name, '成功添加域名{}到项目{}'.format(domain, get.project_name))
                res_domains.append({"name": domain_arr[0], "status": True, "msg": '添加成功'})
                if not check_cloud:
                    public.check_domain_cloud(domain_arr[0])
                    check_cloud = True
                flag = True
            else:
                public.WriteLog(self._log_name, '添加域名错误，域名{}已存在'.format(domain))
                res_domains.append({"name": domain_arr[0], "status": False, "msg": '添加错误，域名{}已存在'.format(domain)})
        if flag:
            public.M('sites').where('id=?', (project_id,)).save('project_config', json.dumps(project_find['project_config']))
            self.set_config(get.project_name)

        return self._ckeck_add_domain(get.project_name, res_domains)

    def get_project_info(self, get):
        '''
            @name 获取指定项目信息
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        project_info = public.M('sites').where('project_type=? AND name=?', ('Go', get.project_name)).find()
        if not project_info: return public.return_error('指定项目不存在!')
        has_load_info = False
        if "has_load_info" in get and get.has_load_info in (1, "1", "ture", "Ture"):
            has_load_info = True
        project_info = self.get_project_stat(project_info, has_load_info)
        project_info['project_config']['project_log'] = int(project_info['project_config'].get('project_log', 1))
        ps = panelSite.panelSite()
        web_log = 0
        try:
            res = ps.GetLogsStatus(public.to_dict_obj({'name': project_info['name']}))
            if res:
                web_log = 1
        except:
            pass
        project_info['project_config']['web_log'] = web_log
        return project_info

    def project_logs(self, get):
        id = get.id
        status = get.status
        web_info = public.M('sites').where('id=?', (id,)).getField('project_config')
        web_info = json.loads(web_info)
        if int(status) != int(web_info.get('project_log',1)):
            web_info['project_log'] = status
            public.M('sites').where('id=?', (id,)).setField('project_config', json.dumps(web_info))
        return public.returnMsg(True, '设置成功,请手动【重启项目】后配置生效')

    def create_project(self, get):
        '''
            @name 创建新的项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
            project_name: string<项目名称>
            project_exe: string<项目可执行文件>
            project_ps: string<项目备注信息>
            bind_extranet: int<是否绑定外网> 1:是 0:否
            domains: list<域名列表> ["domain1:80","domain2:80"]  // 在bind_extranet=1时，需要填写
            is_power_on: int<是否开机启动> 1:是 0:否
            run_user: string<运行用户>
            project_cmd: string<项目执行的命令>
            port 端口号
            }
            @return dict
        '''
        project_name = get.project_name.strip()
        if not re.match("^\w+$", project_name):
            return public.return_error('项目名称格式不正确，支持字母、数字、下划线，表达式: ^[0-9A-Za-z_]$')
        public.set_module_logs("create_go_project", "create")
        if public.M('sites').where('name=?', (get.project_name,)).count():
            return public.return_error('指定项目名称已存在: {}'.format(get.project_name))
        get.project_exe = get.project_exe.strip()
        if not os.path.exists(get.project_exe):
            return public.return_error('项目目录不存在: {}'.format(get.project_exe))

        # 端口占用检测
        try:
            ports = int(get.port)
            if ports < 10 and ports > 65535:
                return public.return_error('端口号不合法，请输入10-65535之间的数字')
        except:
            return public.return_error('端口号不合法，请输入10-65535之间的数字')
        if self.check_port_is_used(get.port):
            return public.return_error('指定端口已被其它应用占用，请修改您的项目配置使用其它端口, 端口: {}'.format(get.port))
        # if 'domains' in get:
        #     domains = json.loads(get.domains)
        #     if len(domains)>1:
        #         get.bind_extranet=1
        #     else:
        #         get.bind_extranet=0
        # else:
        #     get.domains=[]
        #     get.bind_extranet=0

        domains = []
        if get.bind_extranet == 1:
            domains = get.domains
            public.check_domain_cloud(domains[0])
        for domain in domains:
            domain_arr = domain.split(':')
            if public.M('domain').where('name=?', domain_arr[0]).count():
                return public.return_error('指定域名已存在: {}'.format(domain))

        if hasattr(get, "env_file") and get.env_file.strip():
            env_file = get.env_file.strip()
            if not os.path.exists(get.env_file):
                return public.return_error('环境变量文件不存在: {}'.format(get.env_file))
        else:
            env_file = ''

        if hasattr(get, "env_list") and get.env_list:
            if isinstance(get.env_list, str):
                try:
                    env_list = json.loads(get.env_list)
                except:
                    return public.return_error('环境变量格式不正确')
            else:
                env_list = get.env_list

            if not isinstance(env_list, list):
                return public.return_error('环境变量格式不正确')

        else:
            env_list = []

        if not 'project_cmd' in get:
            get.project_cmd = get.project_exe
        # 获取可执行文件的的根目录
        project_path = os.path.dirname(get.project_exe)
        pdata = {
            'name': get.project_name,
            'path': get.project_exe,
            'ps': get.project_ps,
            'status': 1,
            'type_id': 0,
            'project_type': 'Go',
            'project_config': json.dumps(
                {
                    'ssl_path': '/www/wwwroot/java_node_ssl',
                    'project_name': get.project_name,
                    'project_exe': get.project_exe,
                    'bind_extranet': get.bind_extranet,
                    'domains': [],
                    'project_cmd': get.project_cmd,
                    'is_power_on': get.is_power_on,
                    'run_user': get.run_user,
                    'port': int(get.port),
                    'project_path': project_path,
                    'log_path': self._go_logs_path,
                    'porject_log': get.get('porject_log', 1),
                    'web_log': get.get('web_log', 1),
                    'env_file': env_file,
                    'env_list': env_list,
                }
            ),
            'addtime': public.getDate()
        }
        project_id = public.M('sites').insert(pdata)
        if get.bind_extranet == 1:
            format_domains = []
            for domain in domains:
                if domain.find(':') == -1: domain += ':80'
                format_domains.append(domain)
            get.domains = format_domains
            self.project_add_domain(get)
        self.set_config(get.project_name)
        public.WriteLog(self._log_name, '添加Go项目{}'.format(get.project_name))
        self.start_project(get)
        flag, tip = self._release_firewall(get)
        msg = '添加项目成功' + ("" if flag else "<br>" + tip)
        return public.return_data(True, msg, project_id)

    def modify_project(self, get):
        '''
            @name 修改指定项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
            project_name: string<项目名称>
            project_exe: string<项目可执行文件>  可以修改
            project_ps: string<项目备注信息>  可以修改
            is_power_on: int<是否开机启动> 1:是 0:否  可以修改
            run_user: string<运行用户>   可以修改
            project_cmd: string<项目执行的命令>  可以修改
            port 端口号   可以修改端口
            }
            @return dict
        '''
        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return public.return_error('指定项目不存在: {}'.format(get.project_name))

        if not os.path.exists(get.project_exe):
            return public.return_error('项目目录不存在: {}'.format(get.project_exe))

        if hasattr(get, 'port'):
            if int(project_find['project_config']['port']) != int(get.port):
                if self.check_port_is_used(get.get('port/port'), True):
                    return public.return_error('指定端口已被其它应用占用，请修改您的项目配置使用其它端口, 端口: {}'.format(get.port))
                project_find['project_config']['port'] = int(get.port)
        # if hasattr(get,'project_cwd'): project_find['project_config']['project_cwd'] = get.project_cwd.strip()
        if hasattr(get, 'project_exe'): project_find['project_config']['project_exe'] = get.project_exe.strip()
        if hasattr(get, 'is_power_on'): project_find['project_config']['is_power_on'] = get.is_power_on
        if hasattr(get, 'run_user'): project_find['project_config']['run_user'] = get.run_user.strip()
        if hasattr(get, 'project_cmd'): project_find['project_config']['project_cmd'] = get.project_cmd.strip()
        if hasattr(get, 'web_log'): project_find['project_config']['web_log'] = get.web_log
        if hasattr(get, 'project_log'): project_find['project_config']['project_log'] = get.project_log

        if hasattr(get, "env_file") and get.env_file.strip():
            env_file = get.env_file.strip()
            if not os.path.exists(get.env_file):
                return public.return_error('环境变量文件不存在: {}'.format(get.env_file))
            project_find['project_config']['env_file'] = env_file

        if hasattr(get, "env_list") and get.env_list:
            if isinstance(get.env_list, str):
                try:
                    env_list = json.loads(get.env_list)
                except:
                    return public.return_error('环境变量格式不正确')
            else:
                env_list = get.env_list

            if not isinstance(env_list, list):
                return public.return_error('环境变量格式不正确')
            project_find['project_config']['env_list'] = env_list

        pdata = {
            'path': get.project_exe,
            'ps': get.project_ps,
            'project_config': json.dumps(project_find['project_config'])
        }

        public.M('sites').where('name=?', (get.project_name,)).update(pdata)
        self.set_config(get.project_name)
        try:
            ps = panelSite.panelSite()
            res = ps.GetLogsStatus(public.to_dict_obj({'name': get.project_name}))
            # 如果日志状态与配置状态不一致，则修改日志状态
            if res != bool(int(project_find['project_config']['web_log'])):
                ps.logsOpen(public.to_dict_obj({'id': project_find['id']}))
        except:
            pass

        public.WriteLog(self._log_name, '修改Go项目{}'.format(get.project_name))
        # 重启项目
        self.stop_project(get)
        self.start_project(get)
        return public.return_data(True, '修改项目成功,并重启')

    def remove_project(self, get):
        '''
            @name 删除指定项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return public.return_error('指定项目不存在: {}'.format(get.project_name))

        self.stop_project(get)
        self.clear_config(get.project_name)
        public.M('domain').where('pid=?', (project_find['id'],)).delete()
        public.M('sites').where('name=?', (get.project_name,)).delete()
        pid_file = "{}/{}.pid".format(self._go_pid_path, get.project_name)
        if os.path.exists(pid_file): os.remove(pid_file)
        script_file = '{}/{}.sh'.format(self._go_run_scripts, get.project_name)
        if os.path.exists(script_file): os.remove(script_file)
        if "log_path" not in project_find['project_config']:
            log_file = "{}/{}.log".format(self._go_logs, project_find["name"])
        else:
            log_file = "{}/{}.log".format(project_find['project_config']["log_path"], project_find["name"])
        if os.path.exists(log_file): os.remove(log_file)
        self.del_crontab(get.project_name.strip())
        from mod.base.web_conf import remove_sites_service_config
        remove_sites_service_config(get.project_name, "go_")
        public.WriteLog(self._log_name, '删除Go项目{}'.format(get.project_name))
        return public.return_data(True, '删除项目成功')

    # xss 防御
    def xsssec(self, text):
        return text.replace('<', '&lt;').replace('>', '&gt;')

    def last_lines(self, filename, lines=1):
        block_size = 3145928
        block = ''
        nl_count = 0
        start = 0
        fsock = open(filename, 'rU')
        try:
            fsock.seek(0, 2)
            curpos = fsock.tell()
            while (curpos > 0):
                curpos -= (block_size + len(block))
                if curpos < 0: curpos = 0
                fsock.seek(curpos)
                try:
                    block = fsock.read()
                except:
                    continue
                nl_count = block.count('\n')
                if nl_count >= lines: break
            for n in range(nl_count - lines + 1):
                start = block.find('\n', start) + 1
        finally:
            fsock.close()
        return block[start:]

    def get_project_log(self, get):
        '''
        @name 取项目日志
        @author lkq<2021-08-27>
        @param  domain 域名
        @param  project_name 项目名称
        @return string
        '''
        project_info = self.get_project_find(get.project_name.strip())
        if not project_info: return public.returnMsg(False, '项目不存在')
        if "log_path" not in project_info['project_config']:
            log_file = "{}/{}.log".format(self._go_logs, project_info["name"])
        else:
            log_file = "{}/{}.log".format(project_info['project_config']["log_path"], project_info["name"])
        if not os.path.exists(log_file): return public.returnMsg(False, '日志文件不存在')
        log_file_size = os.path.getsize(log_file)
        res = {
            "status": True,
            "size": public.to_size(log_file_size),
            "path": log_file.rsplit("/", 1)[0],
            "data": ""
        }
        if log_file_size > 3145928:
            res["data"] = self.xsssec(self.last_lines(log_file, 3000))
        else:
            res["data"] = self.xsssec(public.GetNumLines(log_file, 3000))
        return res

    def auto_run(self):
        '''
        @name 开机自动启动
        '''
        # 获取数据库信息
        project_list = public.M('sites').where('project_type=?', ('Go',)).field('name,path,project_config').select()
        get = public.dict_obj()
        success_count = 0
        error_count = 0
        for project_find in project_list:
            project_config = json.loads(project_find['project_config'])
            if project_config['is_power_on'] in [0, False, '0', None]: continue
            project_name = project_find['name']
            project_state = self.get_project_run_state(project_name=project_name)
            if not project_state:
                get.project_name = project_name
                result = self.start_project(get)
                if not result['status']:
                    error_count += 1
                    error_msg = '自动启动Nodej项目[' + project_name + ']失败!'
                    public.WriteLog(self._log_name, error_msg)
                else:
                    success_count += 1
                    success_msg = '自动启动Go项目[' + project_name + ']成功!'
                    public.WriteLog(self._log_name, success_msg)
        if (success_count + error_count) < 1: return False
        dene_msg = '共需要启动{}个Go项目，成功{}个，失败{}个'.format(success_count + error_count, success_count, error_count)
        public.WriteLog(self._log_name, dene_msg)
        return True

    def change_log_path(self, get):
        """"修改日志文件地址
        @author baozi <202-03-13>
        @param:
            get  ( dict ):  请求: 包含项目名称和新的路径
        @return
        """
        project_info = self.get_project_find(get.project_name.strip())
        if not project_info: return public.returnMsg(False, '项目不存在')
        new_log_path = get.path.strip() if "path" in get else None
        if not new_log_path or new_log_path[0] != "/":
            return public.returnMsg(False, "路径设置错误")
        if new_log_path[-1] == "/": new_log_path = new_log_path[:-1]
        if not os.path.exists(new_log_path):
            os.makedirs(new_log_path, mode=0o777)
        project_info['project_config']['log_path'] = new_log_path
        pdata = {
            'name': project_info["name"],
            'project_config': json.dumps(project_info['project_config'])
        }
        public.M('sites').where('name=?', (get.project_name.strip(),)).update(pdata)
        # 重启项目
        # return self.restart_project(get)
        res = self.stop_project(get)
        res = self.start_project(get)
        public.WriteLog(self._log_name, 'GO项目{}, 修改日志路径成功'.format(get.project_name))
        return public.returnMsg(True, "项目日志路径修改成功")

    def for_split(self, logsplit, project):
        """日志切割方法调用
        @author baozi <202-03-20>
        @param:
            logsplit  ( LogSplit ):  日志切割方法，传入 pjanme:项目名称 sfile:日志文件路径 log_prefix:产生的日志文件前缀
            project  ( dict ):  项目内容
        @return
        """
        log_file = "{}/{}.log".format(project['project_config']["log_path"], project["name"])
        logsplit(project["name"], log_file, project["name"])

    # —————————————
    #  日志切割   |
    # —————————————
    def del_crontab(self, name):
        """
        @name 删除项目日志切割任务
        @auther hezhihong<2022-10-31>
        @return
        """
        cron_name = f'[勿删]GO项目[{name}]运行日志切割'
        cron_path = public.GetConfigValue('setup_path') + '/cron/'
        cron_list = public.M('crontab').where("name=?", (cron_name,)).select()
        if cron_list:
            for i in cron_list:
                if not i: continue
                cron_echo = public.M('crontab').where("id=?", (i['id'],)).getField('echo')
                args = {"id": i['id']}
                import crontab
                crontab.crontab().DelCrontab(args)
                del_cron_file = cron_path + cron_echo
                public.ExecShell("crontab -u root -l| grep -v '{}'|crontab -u root -".format(del_cron_file))

    def add_crontab(self, name, log_conf, python_path):
        """
        @name 构造站点运行日志切割任务
        """
        cron_name = f'[勿删]GO项目[{name}]运行日志切割'
        if not public.M('crontab').where('name=?', (cron_name,)).count():
            cmd = '{pyenv} {script_path} {name}'.format(
                pyenv=python_path,
                script_path=self.__log_split_script_py,
                name=name
            )
            args = {
                "name": cron_name,
                "type": 'day' if log_conf["log_size"] == 0 else "minute-n",
                "where1": "" if log_conf["log_size"] == 0 else log_conf["minute"],
                "hour": log_conf["hour"],
                "minute": log_conf["minute"],
                "sName": name,
                "sType": 'toShell',
                "notice": '0',
                "notice_channel": '',
                "save": str(log_conf["num"]),
                "save_local": '1',
                "backupTo": '',
                "sBody": cmd,
                "urladdress": ''
            }
            import crontab
            res = crontab.crontab().AddCrontab(args)
            if res and "id" in res.keys():
                return True, "新建任务成功"
            return False, res["msg"]
        return True

    def change_cronta(self, name, log_conf):
        """
        @name 更改站点运行日志切割任务
        """
        python_path = "/www/server/panel/pyenv/bin/python3"
        if not python_path: return False
        cronInfo = public.M('crontab').where('name=?', (f'[勿删]GO项目[{name}]运行日志切割',)).find()
        if not cronInfo:
            return self.add_crontab(name, log_conf, python_path)
        import crontab
        recrontabMode = crontab.crontab()
        id = cronInfo['id']
        del (cronInfo['id'])
        del (cronInfo['addtime'])
        cronInfo['sBody'] = '{pyenv} {script_path} {name}'.format(
            pyenv=python_path,
            script_path=self.__log_split_script_py,
            name=name
        )
        cronInfo['where_hour'] = log_conf['hour']
        cronInfo['where_minute'] = log_conf['minute']
        cronInfo['save'] = log_conf['num']
        cronInfo['type'] = 'day' if log_conf["log_size"] == 0 else "minute-n"
        cronInfo['where1'] = '' if log_conf["log_size"] == 0 else log_conf['minute']

        columns = 'where_hour,where_minute,sBody,save,type,where1'
        values = (cronInfo['where_hour'], cronInfo['where_minute'], cronInfo['sBody'], cronInfo['save'], cronInfo['type'], cronInfo['where1'])
        recrontabMode.remove_for_crond(cronInfo['echo'])
        if cronInfo['status'] == 0: return False, '当前任务处于停止状态,请开启任务后再修改!'
        sync_res=recrontabMode.sync_to_crond(cronInfo)
        if not sync_res['status']:
            return False,sync_res['msg']
        # if not recrontabMode.sync_to_crond(cronInfo)['status']:
        #     return False, '写入计划任务失败,请检查磁盘是否可写或是否开启了系统加固!'
        public.M('crontab').where('id=?', (id,)).save(columns, values)
        public.WriteLog('计划任务', '修改计划任务[' + cronInfo['name'] + ']成功')
        return True, '修改成功'

    def mamger_log_split(self, get):
        """管理日志切割任务
        @author baozi <202-02-27>
        @param:
            get  ( dict ):  包含name, mode, hour, minute
        @return
        """
        name = get.name.strip()
        project = self.get_project_find(name)
        if not project:
            return public.returnMsg(False, "没有该项目，请尝试刷新页面")
        try:
            _log_size = float(get.log_size) if float(get.log_size) >= 0 else 0
            _hour = get.hour.strip() if 0 <= int(get.hour) < 24 else "2"
            _minute = get.minute.strip() if 0 <= int(get.minute) < 60 else '0'
            _num = int(get.num) if 0 < int(get.num) <= 1800 else 180
            _compress = int(get.compress) == 1
        except (ValueError, AttributeError, KeyError):
            _log_size = 0
            _hour = "2"
            _minute = "0"
            _num = 180
            _compress = False

        if _log_size != 0:
            _log_size = _log_size * 1024 * 1024
            _hour = 0
            _minute = 5

        log_conf = {
            "log_size": _log_size,
            "hour": _hour,
            "minute": _minute,
            "num": _num,
            "compress": _compress
        }
        flag, msg = self.change_cronta(name, log_conf)
        if flag:
            conf_path = '{}/data/run_log_split.conf'.format(public.get_panel_path())
            if os.path.exists(conf_path):
                try:
                    data = json.loads(public.readFile(conf_path))
                except:
                    data = {}
            else:
                data = {}
            data[name] = {
                "stype": "size" if bool(_log_size) else "day",
                "log_size": _log_size,
                "limit": _num,
                "compress": _compress,
            }
            public.writeFile(conf_path, json.dumps(data))
            project["project_config"]["log_conf"] = log_conf
            pdata = {
                "project_config": json.dumps(project["project_config"])
            }
            public.M('sites').where('name=?', (name,)).update(pdata)
        return public.returnMsg(flag, msg)

    def set_log_split(self, get):
        """设置日志计划任务状态
        @author baozi <202-02-27>
        @param:
            get  ( dict ):  包含项目名称name
        @return  msg : 操作结果
        """
        name = get.name.strip()
        project_conf = self.get_project_find(name)
        if not project_conf:
            return public.returnMsg(False, "没有该项目，请尝试刷新页面")
        cronInfo = public.M('crontab').where('name=?', (f'[勿删]GO项目[{name}]运行日志切割',)).find()
        if not cronInfo:
            return public.returnMsg(False, "该项目没有设置运行日志的切割任务")

        status_msg = ['停用', '启用']
        status = 1
        import crontab
        recrontabMode = crontab.crontab()

        if cronInfo['status'] == status:
            status = 0
            recrontabMode.remove_for_crond(cronInfo['echo'])
        else:
            cronInfo['status'] = 1
            sync_res=recrontabMode.sync_to_crond(cronInfo)
            if not sync_res['status']:
                return public.returnMsg(False, sync_res['msg'])

        public.M('crontab').where('id=?', (cronInfo["id"],)).setField('status', status)
        public.WriteLog('计划任务', '修改计划任务[' + cronInfo['name'] + ']状态为[' + status_msg[status] + ']')
        return public.returnMsg(True, '设置成功')

    def get_log_split(self, get):
        """获取站点的日志切割任务
        @author baozi <202-02-27>
        @param:
            get  ( dict ):   name
        @return msg : 操作结果
        """

        name = get.name.strip()
        project_conf = self.get_project_find(name)
        if not project_conf:
            return public.returnMsg(False, "没有该项目，请尝试刷新页面")
        if self._check_old(project_conf):
            return {"status": False, "msg": "更新版本后需要重启项目，才能开启运行日志切割任务，建议您找一个合适的时间重启项目", "is_old": True}
        cronInfo = public.M('crontab').where('name=?', (f'[勿删]GO项目[{name}]运行日志切割',)).find()
        if not cronInfo:
            return public.returnMsg(False, "该项目没有设置运行日志的切割任务")

        if "log_conf" not in project_conf["project_config"]:
            return public.returnMsg(False, "日志切割配置丢失，请尝试重新设置")
        res = project_conf["project_config"]["log_conf"]
        res["status"] = cronInfo["status"]
        return {"status": True, "data": res}

    def _update_project(self, project_name, project_info):
        # 检查是否需要更新
        # 移动日志文件
        # 保存
        target_file = self._go_logs_path + "/" + project_name + ".log"
        if "log_path" in project_info['project_config']:
            return
        log_file = "{}/{}.log".format(self._go_logs, project_name)

        if os.path.exists(log_file):
            self._move_logs(log_file, target_file)
            if not os.path.exists(target_file):
                return
            else:
                os.remove(log_file)

        project_info['project_config']["log_path"] = self._go_logs_path
        pdata = {
            'name': project_name,
            'project_config': json.dumps(project_info['project_config'])
        }
        public.M('sites').where('name=?', (project_name,)).update(pdata)

    def _move_logs(self, s_file, target_file):
        if os.path.getsize(s_file) > 3145928:
            res = self.last_lines(s_file, 3000)
            public.WriteFile(target_file, res)
        else:
            shutil.copyfile(s_file, target_file)

    def _check_old(self, project_info):
        if not "log_path" in project_info['project_config']:
            return True

    def _ckeck_add_domain(self, site_name, domains):
        from panelSite import panelSite
        ssl_data = panelSite().GetSSL(type("get", tuple(), {"siteName": site_name})())
        if not ssl_data["status"] or not ssl_data.get("cert_data", {}).get("dns", None):
            return {"domains": domains}
        domain_rep = []
        for i in ssl_data["cert_data"]["dns"]:
            if i.startswith("*"):
                _rep = "^[^\.]+\." + i[2:].replace(".", "\.")
            else:
                _rep = "^" + i.replace(".", "\.")
            domain_rep.append(_rep)
        no_ssl = []
        for domain in domains:
            if not domain["status"]: continue
            for _rep in domain_rep:
                if re.search(_rep, domain["name"]):
                    break
            else:
                no_ssl.append(domain["name"])
        if no_ssl:
            return {
                "domains": domains,
                "not_ssl": no_ssl,
                "tip": "本站点已启用SSL证书,但本次添加的域名：{}，无法匹配当前证书，如有需求，请重新申请证书。".format(str(no_ssl))
            }
        return {"domains": domains}

    def _init_gvm(self) -> None:
        gvm_path = "/usr/bin/pygvm"
        try:
            if not os.path.exists(gvm_path):
                os.symlink('{}/class/projectModel/btpygvm.py'.format(self._panel_path), gvm_path)
            os.chmod(gvm_path, mode=0o755)
        except Exception:
            pass

    @staticmethod
    def _serializer_of_list(s: list, h: list, installed: List[str]) -> List[Dict]:
        return [{
            "version": v.version,
            "type": "stable",
            "installed": True if v.version in installed else False
        } for v in s] + [{
            "version": v.version,
            "type": "history",
            "installed": True if v.version in installed else False
        } for v in h]

    def list_go_sdk(self, get: public.dict_obj) -> Dict:
        """
        获取已安装的sdk，可安装的sdk
        """
        if isinstance(pygvm, str):
            return public.returnMsg(False, pygvm)
        if "force" in get and get.force == "true":
            pygvm.cmd_clean_cache()
        installed: List[str] = pygvm.api_ls()
        installed.sort(key=lambda x: int(x.split(".")[1]), reverse=True)
        sdk = {"all": [], "streamline": []}
        all_s, all_h, errmsg = pygvm.api_ls_remote(True)
        streamline_s, streamline_h, errmsg = pygvm.api_ls_remote(False)
        if errmsg:
            return public.returnMsg(False, errmsg)

        sdk["all"] = self._serializer_of_list(all_s, all_h, installed)
        sdk["streamline"] = self._serializer_of_list(streamline_s, streamline_h, installed)

        pygvm.get_now_version()
        goproxy = {
            "now": pygvm.get_goproxy(),
            "list": [
                {"name": "七牛云", "proxy": "https://goproxy.cn,direct"},
                {"name": "官方源", "proxy": "https://goproxy.io,direct"},
                {"name": "阿里云", "proxy": "https://mirrors.aliyun.com/goproxy,direct"},
                {"name": "华为源", "proxy": "https://mirrors.huaweicloud.com/repository/goproxy,direct"}
            ]
        }
        installing = public.M('tasks').where("status in (-1, 0) and name like '安装[GO%'", ()).field("name").select()
        in_vers = []
        for i in installing:
            in_vers.append(self._parser_version(i["name"]))

        for s in sdk["all"]:
            s["is_install"] = s["version"] in in_vers

        for s in sdk["streamline"]:
            s["is_install"] = s["version"] in in_vers

        return {"status": True, "installed": installed, "sdk": sdk, "used": pygvm.now_version, "goproxy":goproxy}

    @staticmethod
    def set_goproxy(get):
        if "proxy" not in get or not get.proxy:
            return public.returnMsg(False, "请指定代理地址")
        res = pygvm.set_goproxy(get.proxy)
        if not res:
            return public.returnMsg(False, "设置代理失败")
        return public.returnMsg(True, "设置代理成功")

    def set_go_environment(self, get):
        get.version = get.name
        return self.use_go_sdk(get)

    @staticmethod
    def _parser_version(version: str) -> Optional[str]:
        v_rep = r"(?P<target>\d\.\d{1,2}(\.\d{1,2})?)"
        v_res = re.search(v_rep, version)
        if v_res:
            return "go" + v_res.group("target")

    def install_go_sdk(self, get: public.dict_obj) -> Dict:
        """
        安装一个版本的sdk
        """
        if isinstance(pygvm, str):
            return public.returnMsg(False, pygvm)
        if pygvm.check_use() is False:
            return public.returnMsg(False, "关键路径不可修改，请查看是否开启了【系统加固】")
        pygvm.get_now_version()
        version = self._parser_version(getattr(get, "version", ''))
        if version is None:
            return public.returnMsg(False, "版本参数信息错误")

        log_path = self._go_path + "/vhost/gvm_log.log"
        if os.path.isfile(log_path):
            if os.stat(log_path).st_size > 0:
                return public.returnMsg(False, "有一个版本正在安装，请稍等。")
        out_err = open(log_path, "w")
        pygvm.set_std(out_err, out_err)
        flag, msg = pygvm.api_install(version)
        pygvm.set_std(sys.stdout, sys.stderr)
        time.sleep(0.1)
        out_err.seek(0, 0)
        out_err.truncate()
        out_err.close()
        if not flag:
            return public.returnMsg(False, msg)

        return public.returnMsg(True, "安装成功")

    def install_go_sdk_async(self, get):
        if isinstance(pygvm, str):
            return public.returnMsg(False, pygvm)

        pygvm.get_now_version()
        version = self._parser_version(getattr(get, "version", ''))
        if version is None:
            return public.returnMsg(False, "版本参数信息错误")

        python_bin = "{}/pyenv/bin/python3".format(public.get_panel_path())
        shell_str = "{} {}/class/projectModel/btpygvm.py install {}".format(
            python_bin, public.get_panel_path(), version
        )

        if not os.path.exists("/tmp/panelTask.pl"):  # 如果当前任务队列并未执行，就把日志清空
            public.writeFile('/tmp/panelExec.log', '')
        soft_name = "GO-" + version[2:]
        task_id = public.M('tasks').add(
            'id,name,type,status,addtime,execstr',
            (None, '安装[{}]'.format(soft_name), 'execshell', '0', time.strftime('%Y-%m-%d %H:%M:%S'),
             "{{\n{}\n}}".format(shell_str))
        )
        self._create_install_wait_msg(task_id, version)
        return public.returnMsg(True, "安装任务已提交")

    @staticmethod
    def _create_install_wait_msg(task_id: int, version: str):
        from panel_msg.msg_file import message_mgr

        file_path = "/tmp/panelExec.log"
        if not os.path.exists(file_path):
            public.writeFile(file_path, "")

        soft_name = "GO-" + version[2:]
        data = {
            "soft_name": soft_name,
            "install_status": "等待安装" + soft_name,
            "file_name": file_path,
            "self_type": "soft_install",
            "status": 0,
            "task_id": task_id
        }
        title = "等待安装" + soft_name
        res = message_mgr.collect_message(title, ["GO-SDK管理", soft_name], data)
        if isinstance(res, str):
            public.WriteLog("消息盒子", "安装信息收集失败")
            return None
        return res

    def uninstall_go_sdk(self, get: public.dict_obj) -> Dict:
        """
        卸载一个指定版本的sdk
        """
        if isinstance(pygvm, str):
            return public.returnMsg(False, pygvm)
        if pygvm.check_use() is False:
            return public.returnMsg(False, "关键路径不可修改，请查看是否开启了系统加固")
        pygvm.get_now_version()
        version = self._parser_version(getattr(get, "version", ''))
        if version is None:
            return public.returnMsg(False, "版本参数信息错误")

        flag, msg = pygvm.api_uninstall(version)
        if not flag:
            return public.returnMsg(False, msg)

        return public.returnMsg(True, "卸载成功")

    def use_go_sdk(self, get: public.dict_obj) -> Dict:
        """
        使用一个版本的sdk
        """
        if isinstance(pygvm, str):
            return public.returnMsg(False, pygvm)
        if pygvm.check_use() is False:
            return public.returnMsg(False, "关键路径不可修改，请查看是否开启了系统加固")
        pygvm.get_now_version()
        version = self._parser_version(getattr(get, "version", ''))
        if version is None:
            return public.returnMsg(False, "版本参数信息错误")

        flag, msg = pygvm.api_use(version)
        if not flag:
            return public.returnMsg(False, msg)

        return public.returnMsg(True, "切换成功")

    def get_project_status(self, project_id):
        # 仅使用在项目停止告警中
        project_info = public.M('sites').where('project_type=? AND id=?', ('Go', project_id)).find()
        if not project_info:
            return None, project_info["name"]
        if self.is_stop_by_user(project_id):
            return True, project_info["name"]
        res = self.get_project_run_state(project_name=project_info['name'])
        return res, project_info["name"]
