# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------
# ------------------------------
# nodejs模型 - 通用基类
# ------------------------------
import json
import os
import re
import shutil
import sys
import time
from typing import Union

import psutil

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public

try:
    import idna
except:
    public.ExecShell('btpip install idna')
    import idna

try:
    from BTPanel import cache
except:
    pass


class NodeJs():

    def __init__(self):
        self.pm2_cmd = None
        self.pack_cmd = None
        self._pids = None
        self.get = None
        self.def_name = None
        self.nodejs_plugin_path = public.get_plugin_path('nodejs')
        self.panel_path = public.get_panel_path()
        self.vhost_path = '{}/vhost'.format(self.panel_path)
        self.npm_exec_log = '{}/logs/npm-exec.log'.format(self.panel_path)
        self._is_nginx_http3 = None
        self.nodejs_path = '{}/nodejs'.format(public.get_setup_path())
        self.log_name = '网站 - Node项目'
        self.node_logs_path = "/www/wwwlogs/nodejs"
        self.pm2_logs_path = "/www/wwwlogs/pm2"
        self.install_logs_path = "/www/wwwlogs/nodejs/install_logs"
        self.node_logs = '{}/vhost/logs'.format(self.nodejs_path)
        self.install_logs_file = None
        self.container_id = None
        self.manager = "npm"
        self.projectModel = None
        self.nodejs_bin = None
        self.nodejs_version = None
        self.set_strict_ssl = None
        self.node_pid_path = '{}/vhost/pids'.format(self.nodejs_path)
        self.node_run_scripts = '{}/vhost/scripts'.format(self.nodejs_path)
        self.pm2_config_path = '{}/vhost/pm2_configs'.format(self.nodejs_path)
        self.www_home = '/home/www'
        self.project_structure = {
            "nodejs": "NodeJS项目",
            "pm2": "PM2项目",
            "general": "传统Node项目",
        }
        if not os.path.exists(self.node_run_scripts):
            os.makedirs(self.node_run_scripts, 493)
        if not os.path.exists(self.node_pid_path):
            os.makedirs(self.node_pid_path, 493)
        if not os.path.exists(self.node_logs_path):
            os.makedirs(self.node_logs_path, 493)
        if not os.path.exists(self.www_home):
            os.makedirs(self.www_home, 493)
            public.set_own(self.www_home, 'www')
        if not os.path.exists(self.install_logs_path):
            os.makedirs(self.install_logs_path, 493)
        if not os.path.exists(self.pm2_config_path):
            os.makedirs(self.pm2_config_path, 493)
        if not os.path.exists(self.pm2_logs_path):
            os.makedirs(self.pm2_logs_path, 493)

    def set_pack_cmd(self, nodejs_version):
        pack_path = "{}/{}/lib/node_modules/{}/bin".format(self.nodejs_path, nodejs_version, self.manager)
        if os.path.exists(pack_path) and os.path.isdir(pack_path):
            self.pack_cmd = pack_path
        return self

    def set_pm2_cmd(self, nodejs_version):
        pm2_path = "{}/{}/lib/node_modules/pm2/bin".format(self.nodejs_path, nodejs_version)
        if os.path.exists(pm2_path) and os.path.isdir(pm2_path):
            self.pm2_cmd = "{}/{}/bin/pm2".format(self.nodejs_path, nodejs_version)
        return self

    def set_self_get(self, get):
        self.get = get
        return self

    def set_install_logs(self, project_name: str) -> 'NodeJs':
        self.install_logs_file = os.path.join(self.install_logs_path, "{}_install.log".format(project_name))
        return self

    def get_strict_ssl(self) -> 'NodeJs':
        # self.set_strict_ssl = ["{}/{}".format(self.nodejs_bin, self.manager), "config", "set", "strict-ssl", "false"]
        self.set_strict_ssl = "{}/{} config set strict-ssl false".format(self.nodejs_bin, self.manager)
        return self

    def set_nodejs_bin(self) -> 'NodeJs':
        self.nodejs_bin = os.path.join(self.nodejs_path, self.nodejs_version, "bin")
        return self

    def set_nodejs_version(self, nodejs_version: str) -> 'NodeJs':
        self.nodejs_version = nodejs_version
        return self

    def set_def_name(self, def_name: str) -> 'NodeJs':
        self.def_name = def_name
        return self

    def wsResult(self, status: bool = True, msg: str = "", data: any = None, timestamp: int = None, code: int = 0,
                 args: any = None):
        rs = public.returnResult(status, msg, data, timestamp, code, args)
        rs["def_name"] = self.def_name
        return rs

    # 2024/6/25 下午2:40 获取日志类型的websocket返回值
    def exec_logs(self, get, command, cwd=None, write_log=False):
        '''
            @name 获取日志类型的websocket返回值
            @author wzz <2024/6/25 下午2:41>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if self.def_name is None: self.set_def_name(get.def_name)
        from subprocess import Popen, PIPE, STDOUT

        p = Popen(command, stdout=PIPE, stderr=STDOUT, cwd=cwd)

        while True:
            if p.poll() is not None:
                break

            line = p.stdout.readline()  # 非阻塞读取
            if line:
                try:
                    if hasattr(get, '_ws'):
                        get._ws.send(json.dumps(self.wsResult(
                            True,
                            "{}".format(line.decode('utf-8').rstrip()),
                        )))

                    if write_log:
                        public.WriteFile(self.install_logs_file, line.decode('utf-8').rstrip() + "\n", "a+")
                except:
                    continue
            else:
                break

    def get_install_cmd(self, package_name: str = None, is_global: bool = False, force: bool = False,
                        check_update: bool = False, *args, **kwargs) -> list:
        cmd = ["{}/{}".format(self.nodejs_bin, self.manager), "install"]
        if package_name is not None:
            cmd.append("{}".format(package_name))
        if is_global:
            cmd.append("-g")
        if force:
            cmd.append("--force")
        if check_update:
            cmd.append("npm-check-updates")
        for arg in args:
            cmd.append("{}".format(arg))
        for key in kwargs:
            cmd.append("--{} {}".format(key, kwargs[key]))
        return cmd

    def set_project_model(self, projectModel: str = None) -> 'NodeJs':
        if projectModel is None:
            self.projectModel = None
        elif projectModel == "nodejs":
            from mod.project.nodejs.nodeMod import main as nodeMod
            self.projectModel = nodeMod()
        elif projectModel == "pm2":
            from mod.project.nodejs.pm2Mod import main as pm2Mod
            self.projectModel = pm2Mod()
        elif projectModel == "general":
            from mod.project.nodejs.generalMod import main as generalMod
            self.projectModel = generalMod()
        else:
            self.projectModel = None
        return self

    def set_manager(self, manager: str) -> 'NodeJs':
        self.manager = manager
        return self

    # 2024/7/10 下午4:56 设置nodejs版本路径
    def set_nodejs_path(self, nodejs_path: str) -> 'NodeJs':
        self.nodejs_path = nodejs_path
        return self

    # 2024/7/10 下午4:56 获取已安装的nodejs版本列表
    def get_nodejs_version(self, get) -> list:
        try:
            from projectModel.nodejsModel import main
            return main().get_nodejs_version(get)
        except:
            return []

    # 2024/7/10 下午5:02 将node版本转成元祖
    def version_key(self, version):
        return tuple(map(int, re.findall(r'\d+', version)))

    # 2024/7/10 下午5:12 获取指定的nodejs版本允许使用的包管理器
    def package_managers(self, nodejs_versions) -> list:
        package_managers = []
        top_version = int(nodejs_versions[0].split('.')[0].split('v')[-1])
        if top_version >= 14:
            package_managers.append("pnpm")
        if top_version >= 8:
            package_managers.append("yarn")
        package_managers.append("npm")

        return package_managers

    # 2024/7/10 下午9:10 获取可以使用的用户列表
    def get_system_user_list(self, get):
        '''
            @name 获取可以使用的用户列表
        '''
        from projectModel.base import projectBase
        return projectBase().get_system_user_list(get)

    # 2024/7/12 上午9:12
    def check_port_is_used(self, port, sock=False):
        '''
            @name 检查端口是否被占用
            @author hwliang<2021-08-09>
            @param port: int<端口>
            @return bool
        '''
        if not isinstance(port, int): port = int(port)
        if port == 0: return False
        project_list = public.M('sites').where('status=? AND project_type=?', (1, 'Node')).field(
            'name,path,project_config').select()
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

    # 2024/7/12 上午9:06 创建网站
    def create_site(self, get):
        '''
            @name
        '''
        try:
            get.project_args = get.get("project_args", "")
            get.project_script = get.get("project_script", "")
            get.pkg_manager = get.get("pkg_manager", "")
            get.env = get.get("env", "")
            get.project_file = get.get("project_file", "")
            get.config_file = get.get("config_file", "")
            get.config_body = get.get("config_body", "")
            get.project_type = get.get("project_type", "")
            get.pm2_name = get.get("pm2_name", "")
            get.watch = get.get("watch", False)
            get.cluster = get.get("cluster/d", 1)
            get.add_type = get.get("add_type", None)
            get.bind_extranet = 1 if len(get.domains) > 0 else 0
            pdata = {
                'name': get.project_name,
                'path': get.project_cwd,
                'ps': get.project_ps,
                'status': 1,
                'type_id': 0,
                'project_type': 'Node',
                'project_config': json.dumps({
                    'project_name': get.project_name,
                    'pm2_name': get.pm2_name,
                    'add_type': get.add_type,
                    'watch': get.watch,
                    'cluster': get.cluster,
                    'project_cwd': get.project_cwd,
                    'project_file': get.project_file,
                    'project_script': get.project_script,
                    'project_args': get.project_args,
                    'project_type': get.project_type,
                    'config_file': get.config_file,
                    'config_body': get.config_body,
                    'env': get.env,
                    'bind_extranet': get.bind_extranet,
                    'domains': [],
                    'is_power_on': get.is_power_on,
                    'run_user': get.run_user,
                    'max_memory_limit': get.max_memory_limit,
                    'nodejs_version': get.nodejs_version,
                    'port': int(get.port) if get.port != "" else None,
                    'log_path': self.node_logs_path,
                    'pkg_manager': get.pkg_manager}),
                'addtime': public.getDate()
            }

            project_id = public.M('sites').insert(pdata)
            if get.bind_extranet == 1:
                format_domains = []
                for domain in get.domains:
                    if domain.find(':') == -1: domain += ':80'
                    format_domains.append(domain)
                get.domains = format_domains
                self.project_add_domain(get)
            if project_id:
                public.WriteLog(self.log_name,
                                '添加{}【{}】'.format(self.project_structure[get.project_type], get.project_name))
                return project_id
        except:
            pass

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
            return public.return_error('指定项目不存在', data='')
        project_id = project_find['id']

        domains = get.domains
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
                public.M('domain').add('name,pid,port,addtime',
                                       (domain_arr[0], project_id, domain_arr[1], public.getDate()))
                if not domain in project_find['project_config']['domains']:
                    project_find['project_config']['domains'].append(domain)
                public.WriteLog(self.log_name, '成功添加域名{}到项目{}'.format(domain, get.project_name))
                res_domains.append({"name": domain_arr[0], "status": True, "msg": '添加成功'})
                flag = True
            else:
                public.WriteLog(self.log_name, '添加域名错误，域名{}已存在'.format(domain))
                res_domains.append(
                    {"name": domain_arr[0], "status": False, "msg": '添加错误，域名{}已存在'.format(domain)})
        if flag:
            public.M('sites').where('id=?', (project_id,)).save('project_config',
                                                                json.dumps(project_find['project_config']))
            self.set_config(get.project_name)

        return self._ckeck_add_domain(get.project_name, res_domains)

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
            return {"domains": domains, "not_ssl": no_ssl,
                    "tip": "本站点已启用SSL证书,但本次添加的域名：{}，无法匹配当前证书，如有需求，请重新申请证书。".format(
                        str(no_ssl))}
        return {"domains": domains}

    def get_project_find(self, project_name):
        '''
            @name 获取指定项目配置
            @author hwliang<2021-08-09>
            @param project_name<string> 项目名称
            @return dict
        '''
        project_info = public.M('sites').where('project_type=? AND name=?', ('Node', project_name)).find()
        if isinstance(project_info, str):
            raise public.PanelError('数据库查询错误：' + project_info)
        if not project_info: return False
        project_info['project_config'] = json.loads(project_info['project_config'])
        return project_info

    # 2024/7/12 上午9:59
    def _update_project(self, project_name, project_info):
        # 检查是否需要更新
        # 移动日志文件
        # 保存
        target_file = self.node_logs_path + "/" + project_name + ".log"
        if "log_path" in project_info['project_config']:
            return
        log_file = "{}/{}.log".format(self.node_logs, project_name)

        if os.path.exists(log_file):
            self._move_logs(log_file, target_file)
            if not os.path.exists(target_file):
                return
            else:
                os.remove(log_file)

        project_info['project_config']["log_path"] = self.node_logs_path
        pdata = {
            'name': project_name,
            'project_config': json.dumps(project_info['project_config'])
        }
        public.M('sites').where('name=?', (project_name,)).update(pdata)

    def get_project_state_by_cwd(self, project_name):
        '''
            @name 通过cwd获取项目状态
            @author hwliang<2022-01-17>
            @param project_name<string> 项目名称
            @return bool or list
        '''
        project_find = self.get_project_find(project_name)
        self._pids = psutil.pids()
        if not project_find: return []
        all_pids = []
        for i in self._pids:
            try:
                p = psutil.Process(i)
                if p.cwd() == project_find['path']:
                    pname = p.name()
                    if pname in ['node', 'npm', 'pm2', 'yarn'] or pname.find('node ') == 0:
                        cmdline = ','.join(p.cmdline())
                        if cmdline.find('God Daemon') != -1: continue
                        env_list = p.environ()
                        if 'name' in env_list:
                            if not env_list['name'] == project_name: continue
                        if 'NODE_PROJECT_NAME' in env_list:
                            if not env_list['NODE_PROJECT_NAME'] == project_name: continue
                        all_pids.append(i)
            except:
                continue
        if all_pids:
            pid_file = "{}/{}.pid".format(self.node_pid_path, project_name)
            public.writeFile(pid_file, str(all_pids[0]))
            return all_pids
        return False

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
                if p.status() == "zombie":
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

    def get_other_pids(self, pid):
        '''
            @name 获取其他进程pid列表
            @author hwliang<2021-08-10>
            @param pid: string<项目pid>
            @return list
        '''
        project_name = None
        for pid_name in os.listdir(self.node_pid_path):
            pid_file = '{}/{}'.format(self.node_pid_path, pid_name)
            # s_pid = int(public.readFile(pid_file))
            data = public.readFile(pid_file)
            if isinstance(data, str):
                try:
                    s_pid = int(data)
                except:
                    return []
            else:
                return []
            if pid == s_pid:
                project_name = pid_name[:-4]
                break
        project_find = self.get_project_find(project_name)
        if not project_find: return []
        if not self._pids: self._pids = psutil.pids()
        all_pids = []
        for i in self._pids:
            try:
                p = psutil.Process(i)
                if p.cwd() == project_find['path']:
                    pname = p.name()
                    if pname in ['node', 'npm', 'pm2', 'yarn'] or pname.find('node ') == 0:
                        cmdline = ','.join(p.cmdline())
                        if cmdline.find('God Daemon') != -1: continue
                        env_list = p.environ()
                        if 'name' in env_list:
                            if not env_list['name'] == project_name: continue
                        if 'NODE_PROJECT_NAME' in env_list:
                            if not env_list['NODE_PROJECT_NAME'] == project_name: continue
                        all_pids.append(i)
            except:
                continue
        return all_pids

    def _move_logs(self, s_file, target_file):
        if os.path.getsize(s_file) > 3145928:
            res = public.GetNumLines(s_file, 3000)
            public.WriteFile(target_file, res)
        else:
            shutil.copyfile(s_file, target_file)

    def check_domain(self, domain: str) -> Union[str, bool]:
        domain = self.domain_to_puny_code(domain)
        # 判断通配符域名格式
        if domain.find('*') != -1 and domain.find('*.') == -1:
            return False

        # 判断域名格式
        reg = "^([\w\-\*]{1,100}\.){1,24}([\w\-]{1,24}|[\w\-]{1,24}\.[\w\-]{1,24})$"
        if not re.match(reg, domain):
            return False
        return domain

    @staticmethod
    def domain_to_puny_code(domain):
        match = re.search(u"[^u\0000-u\001f]+", domain)
        if not match:
            return domain
        try:
            if domain.startswith("*."):
                return "*." + idna.encode(domain[2:]).decode("utf8")
            else:
                return idna.encode(domain).decode("utf8")
        except:
            return domain

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

    def exists_nginx_ssl(self, project_name):
        '''
            @name 判断项目是否配置Nginx SSL配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return tuple
        '''
        config_file = "{}/nginx/node_{}.conf".format(public.get_vhost_path(), project_name)
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

    def exists_apache_ssl(self, project_name):
        '''
            @name 判断项目是否配置Apache SSL配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return bool
        '''
        config_file = "{}/apache/node_{}.conf".format(public.get_vhost_path(), project_name)
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

    def is_nginx_http3(self):
        """判断nginx是否可以使用http3"""
        if getattr(self, "_is_nginx_http3", None) is None:
            _is_nginx_http3 = public.ExecShell("nginx -V 2>&1| grep 'http_v3_module'")[0] != ''
            setattr(self, "_is_nginx_http3", _is_nginx_http3)
        return self._is_nginx_http3

    @staticmethod
    def _replace_nginx_conf(config_file, mut_config: dict) -> bool:
        """尝试替换"""
        data: str = public.readFile(config_file)
        tab_spc = "    "
        rep_list = [( r"([ \f\r\t\v]*listen[^;\n]*;\n(\s*http2\s+on\s*;[^\n]*\n)?)+", mut_config["listen_ports"] + "\n"),
                    (r"[ \f\r\t\v]*root [ \f\r\t\v]*/[^;\n]*;", "    root {};".format(mut_config["site_path"])),
                    (r"[ \f\r\t\v]*server_name [ \f\r\t\v]*[^\n;]*;",
                     "   server_name {};".format(mut_config["domains"])), (
                        r"[ \f\r\t\v]*location */ *\{ *\n *proxy_pass[^\n;]*;\n *proxy_set_header *Host",
                        "{}location / {{\n{}proxy_pass {};\n{}proxy_set_header Host".format(tab_spc, tab_spc * 2,
                                                                                            mut_config["url"],
                                                                                            tab_spc * 2, )),
                    ("[ \f\r\t\v]*#SSL-START(.*\n){2,15}[ \f\r\t\v]*#SSL-END",
                     "{}#SSL-START SSL相关配置\n{}#error_page 404/404.html;\n{}{}\n{}#SSL-END".format(
                         tab_spc, tab_spc, tab_spc, mut_config["ssl_config"],
                         tab_spc))]
        for rep, info in rep_list:
            if re.search(rep, data):
                data = re.sub(rep, info, data, 1)
            else:
                return False

        public.writeFile(config_file, data)
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
    error_page 497  https://$host$request_uri;'''.format(vhost_path=self.vhost_path, priject_name=project_name,
                                                         http3_header=http3_header)

            if is_force_ssl:
                ssl_config += '''
    #HTTP_TO_HTTPS_START
    if ($server_port !~ 443){
        rewrite ^(/.*)$ https://$host$1 permanent;
    }
    #HTTP_TO_HTTPS_END'''

        config_file = "{}/nginx/node_{}.conf".format(self.vhost_path, project_name)
        template_file = "{}/template/nginx/node_http.conf".format(self.vhost_path)
        listen_ports = "\n".join(listen_ports_list).strip()

        config_body = public.readFile(template_file)
        mut_config = {"site_path": project_find['path'], "domains": ' '.join(domains),
                      "url": 'http://127.0.0.1:{}'.format(project_find['project_config']['port']),
                      "ssl_config": ssl_config,
                      "listen_ports": listen_ports}
        config_body = config_body.format(site_path=mut_config["site_path"], domains=mut_config["domains"],
                                         project_name=project_name, panel_path=self.panel_path,
                                         log_path=public.get_logs_path(),
                                         url=mut_config["url"], host='$host', listen_ports=listen_ports,
                                         ssl_config=ssl_config)

        # # 恢复旧的SSL配置
        # ssl_config = self.get_nginx_ssl_config(project_name)
        # if ssl_config:
        #     config_body.replace('#error_page 404/404.html;',ssl_config)

        rewrite_file = "{panel_path}/vhost/rewrite/node_{project_name}.conf".format(panel_path=self.panel_path,
                                                                                    project_name=project_name)
        if not os.path.exists(rewrite_file):
            public.writeFile(rewrite_file, '# 请将伪静态规则或自定义NGINX配置填写到此处\n')
        if not os.path.exists("/www/server/panel/vhost/nginx/well-known"):
            os.makedirs("/www/server/panel/vhost/nginx/well-known", 0o600)
        apply_check = "{}/vhost/nginx/well-known/{}.conf".format(self.panel_path, project_name)
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

        config_file = "{}/apache/node_{}.conf".format(self.vhost_path, project_name)
        template_file = "{}/template/apache/node_http.conf".format(self.vhost_path)
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
                ssl_key_file = "{vhost_path}/cert/{project_name}/privkey.pem".format(project_name=project_name,
                                                                                     vhost_path=public.get_vhost_path())
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
            apache_config_body += config_body.format(site_path=project_find['path'],
                                                     server_name='{}.{}'.format(p, project_name),
                                                     domains=' '.join(domains), log_path=public.get_logs_path(),
                                                     server_admin='admin@{}'.format(project_name),
                                                     url='http://127.0.0.1:{}'.format(
                                                         project_find['project_config']['port']), port=p,
                                                     ssl_config=ssl_config,
                                                     project_name=project_name)
            apache_config_body += "\n"

            # 添加端口到主配置文件
            if not p in [80]:
                s.apacheAddPort(p)

        # 写.htaccess
        rewrite_file = "{}/.htaccess".format(project_find['path'])
        if not os.path.exists(rewrite_file): public.writeFile(rewrite_file,
                                                              '# 请将伪静态规则或自定义Apache配置填写到此处\n')

        # 写配置文件
        public.writeFile(config_file, apache_config_body)
        return True

    def get_node_bin(self, nodejs_version):
        '''
            @name 获取指定node版本的node路径
            @author hwliang<2021-08-10>
            @param nodejs_version<string> nodejs版本
            @return string
        '''
        node_path = '{}/{}/bin/node'.format(self.nodejs_path, nodejs_version)
        if not os.path.exists(node_path): return False
        return node_path

    def get_npm_bin(self, nodejs_version):
        '''
            @name 获取指定node版本的npm路径
            @author hwliang<2021-08-10>
            @param nodejs_version<string> nodejs版本
            @return string
        '''
        npm_path = '{}/{}/bin/npm'.format(self.nodejs_path, nodejs_version)
        if not os.path.exists(npm_path): return False
        return npm_path

    def get_last_env(self, nodejs_version, project_cwd=None):
        '''
            @name 获取前置环境变量
            @author hwliang<2021-08-25>
            @param nodejs_version<string> Node版本
            @return string
        '''
        nodejs_bin_path = '{}/{}/bin'.format(self.nodejs_path, nodejs_version)
        if project_cwd:
            _bin = '{}/node_modules/.bin'.format(project_cwd)
            if os.path.exists(_bin):
                nodejs_bin_path = _bin + ':' + nodejs_bin_path

        last_env = '''PATH={nodejs_bin_path}:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
'''.format(nodejs_bin_path=nodejs_bin_path)
        return last_env

    @staticmethod
    def start_by_user(project_id):
        file_path = "{}/data/push/tips/project_stop.json".format(public.get_panel_path())
        if not os.path.exists(file_path):
            data = {}
        else:
            data_content = public.readFile(file_path)
            try:
                data = json.loads(data_content)
            except json.JSONDecodeError:
                data = {}
        data[str(project_id)] = False
        public.writeFile(file_path, json.dumps(data))

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

    @staticmethod
    def stop_by_user(project_id):
        file_path = "{}/data/push/tips/project_stop.json".format(public.get_panel_path())
        if not os.path.exists(file_path):
            data = {}
        else:
            data_content = public.readFile(file_path)
            try:
                data = json.loads(data_content)
            except json.JSONDecodeError:
                data = {}
        data[str(project_id)] = True
        public.writeFile(file_path, json.dumps(data))

    # 2024/7/12 下午12:40 websocket错误退出函数
    def ws_err_exit(self, status: bool = True,
                    msg: str = "",
                    data: any = None,
                    timestamp: int = None,
                    code: int = 0,
                    args: any = None):
        '''
            @name websocket错误退出函数
        '''
        self.get._ws.send(json.dumps(self.wsResult(status, msg, data, timestamp, code, args)))
        self.get._ws.close()

    # 2024/7/12 下午5:45 删除node项目
    def remove_project(self, get):
        '''
            @name 删除node项目
        '''
        get.pm2_name = get.get("pm2_name", "")
        if get.pm2_name != "":
            from mod.project.nodejs.pm2Mod import main
            main().delete(mode="cluster_mode", name=get.pm2_name)

        from projectModel.nodejsModel import main
        remove_result = main().remove_project(get)
        from mod.base.web_conf.redirect import Redirect
        Redirect().remove_redirect_by_project_name(get.project_name)
        if not remove_result["status"]:
            return public.returnResult(False, remove_result["error_msg"], code=5)
        return public.returnResult(True, '删除成功', code=0)

    # 2024/7/13 上午10:22 检测环境变量是否有误，并返回构造好的环境变量
    def get_run_env(self, get):
        '''
            @name 检测环境变量是否有误，并返回构造好的环境变量
        '''
        get.env = "\n".join(map(lambda x: "{}".format(x), get.env))

    # 2024/7/12 上午10:40 检测node版本是否符合要求
    def check_node_version(self, get):
        '''
            @name 判断是否存在"engines"，并且判断 get.nodejs_version 是否在大于等于"engines"中的node版本
        '''
        if "engines" in get.package_info:
            if "node" in get.package_info["engines"]:
                # 2024/7/12 上午10:24 获取engines的数学符号
                get_nodejs_version = self.version_key(get.nodejs_version)
                if ">=" in get.package_info["engines"]["node"]:
                    engines_node_version = get.package_info["engines"]["node"].replace(">=", "v").strip()
                    engines_node_version = self.version_key(engines_node_version)
                    if get_nodejs_version < engines_node_version:
                        self.ws_err_exit(False, '当前项目【{}】要求使用【{}】以上的node版本'.format(
                            get.project_name,
                            "v" + ".".join(map(str, engines_node_version))), code=2)
                elif ">" in get.package_info["engines"]["node"]:
                    engines_node_version = get.package_info["engines"]["node"].replace(">", "v").strip()
                    engines_node_version = self.version_key(engines_node_version)
                    if get_nodejs_version <= engines_node_version:
                        self.ws_err_exit(False, '当前项目【{}】要求使用【{}】以上的node版本'.format(
                            get.project_name,
                            "v" + ".".join(map(str, engines_node_version))), code=2)
                elif "<=" in get.package_info["engines"]["node"]:
                    engines_node_version = get.package_info["engines"]["node"].replace("<=", "v").strip()
                    engines_node_version = self.version_key(engines_node_version)
                    if get_nodejs_version > engines_node_version:
                        self.ws_err_exit(False, '当前项目【{}】要求使用【{}】以下的node版本'.format(
                            get.project_name,
                            "v" + ".".join(map(str, engines_node_version))), code=2)
                elif "<" in get.package_info["engines"]["node"]:
                    engines_node_version = get.package_info["engines"]["node"].replace("<", "v").strip()
                    engines_node_version = self.version_key(engines_node_version)
                    if get_nodejs_version >= engines_node_version:
                        self.ws_err_exit(False, '当前项目【{}】要求使用【{}】以下的node版本'.format(
                            get.project_name,
                            "v" + ".".join(map(str, engines_node_version))), code=2)
                elif "==" in get.package_info["engines"]["node"]:
                    engines_node_version = get.package_info["engines"]["node"].replace("==", "v").strip()
                    engines_node_version = self.version_key(engines_node_version)
                    if get_nodejs_version != engines_node_version:
                        self.ws_err_exit(False, '当前项目【{}】要求使用【{}】的node版本'.format(
                            get.project_name,
                            "v" + ".".join(map(str, engines_node_version))), code=2)

    def replace_or_add_field(self, config_body, regex, field):
        if regex.search(config_body):
            return regex.sub("       " + field, config_body)
        else:
            match = re.search(r'(apps\s*:\s*\[.*?\{)', config_body, re.DOTALL)
            if match:
                insert_position = match.end()
                return config_body[:insert_position] + "\n            " + field + config_body[insert_position:]
            # match = re.search(r'(apps:\s*\[.*\{)', config_body, re.DOTALL)
            # if match:
            #     insert_position = match.end()
            #     return config_body[:insert_position] + "\n            " + field + config_body[insert_position:]
        return config_body

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
        if get: project_name = get.project_name.strip()
        pid_file = "{}/{}.pid".format(self.node_pid_path, project_name)
        if not os.path.exists(pid_file): return False
        data = public.readFile(pid_file)
        if isinstance(data, str) and data:
            pid = int(data)
            pids = self.get_project_pids(pid=pid)
        else:
            return self.get_project_state_by_cwd(project_name)
        if not pids: return self.get_project_state_by_cwd(project_name)
        return True

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
        percent = round(100.00 * (process_cpu_time - old_process_cpu_time) / (new_time - old_time) / psutil.cpu_count(),
                        2)
        return percent

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
        pid_file = "{}/{}.pid".format(self.node_pid_path, project_name)
        if not os.path.exists(pid_file): return load_info
        data = public.readFile(pid_file)
        if isinstance(data, str) and data:
            pid = int(data)
            pids = self.get_project_pids(pid=pid)
        else:
            return load_info
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
        from data import data
        return data().get_site_ssl_info('node_{}'.format(project_name))

    def get_project_stat(self, project_info):
        '''
            @name 获取项目状态信息
            @author hwliang<2021-08-09>
            @param project_info<dict> 项目信息
            @return list
        '''
        project_info['project_config'] = json.loads(project_info['project_config'])
        if ("pm2_name" in project_info['project_config'] and
            "project_type" in project_info['project_config'] and
            project_info['project_config']["project_type"] == "pm2") or "pm2" in project_info['project_config']['project_script']:
            from mod.project.nodejs.pm2Mod import main
            pm2_list = main().get_jlist()
            project_info['run'] = False
            for pm2_info in pm2_list:
                if pm2_info.get("name") in ("pm2-sysmonit", "pm2-logrotate"):
                    continue

                project_info['run'] = pm2_info.get("pm2_env").get("status") == "online"
                if project_info['run']:
                    project_info['load_info'] = pm2_info
                    break
        else:
            project_info['run'] = self.get_project_run_state(project_name=project_info['name'])
        project_info['load_info'] = {}
        if project_info['run']:
            project_info['load_info'] = self.get_project_load_info(project_name=project_info['name'])
        project_info['ssl'] = self.get_ssl_end_date(project_name=project_info['name'])
        project_info['listen'] = []
        project_info['listen_ok'] = True
        if project_info['load_info']:
            for pid in project_info['load_info'].keys():
                if not 'connections' in project_info['load_info'][pid]:
                    project_info['load_info'][pid]['connections'] = []
                for conn in project_info['load_info'][pid]['connections']:
                    if not conn['status'] == 'LISTEN': continue
                    if not conn['local_port'] in project_info['listen']:
                        project_info['listen'].append(conn['local_port'])
            if project_info['listen']:
                if project_info['project_config']['port'] is None:
                    project_info['project_config']['port'] = project_info['listen'][0]
                project_info['listen_ok'] = project_info['project_config']['port'] in project_info['listen']

        return project_info

    def is_install_nodejs(self, get):
        '''
            @name 是否安装nodejs版本管理器
            @author hwliang<2021-08-09>
            @param get<dict_obj> 请求数据
            @return bool
        '''
        return os.path.exists(self.nodejs_plugin_path)

    def rebuild_project(self, project_name):
        '''
            @name 重新构建指定项目
            @author hwliang<2021-08-26>
            @param project_name: string<项目名称>
            @return bool
        '''
        project_find = self.get_project_find(project_name)
        if not project_find: return False
        nodejs_version = project_find['project_config']['nodejs_version']
        npm_bin = self.get_npm_bin(nodejs_version)

        public.ExecShell(
            self.get_last_env(nodejs_version) + "cd {} && {} rebuild &>> {}".format(project_find['path'], npm_bin,
                                                                                    self.npm_exec_log))
        return True
