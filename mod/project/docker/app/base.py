# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------
# ------------------------------
# docker模型 - docker app 基类
# ------------------------------
import json
import os
import sys
import time
from datetime import timedelta

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public
from mod.project.docker.composeMod import main as composeMod

dk_project_path="/www/dk_project"
project_path_file = "{}/class/btdockerModel/config/project_path.pl".format(public.get_panel_path())
if os.path.exists(project_path_file):
    path = public.readFile(project_path_file)
    if path:
        dk_project_path = path.strip()
class App(composeMod):
    dk_project_path = dk_project_path

    def __init__(self):
        super(App, self).__init__()
        self.types = (
            "BuildWebsite",
            "Database",
            "WebServer",
            "RunTime",
            "Tools",
            "AI",
            "Storage",
            "Media",
            "Middleware",
            "DevOps",
            "DevTool",
            "Securtiy",
            "Email",
            "Other",
        )
        self.app_name = None
        self.service_name = None
        self.data = None
        self.app_path = None
        self.service_path = None
        self.plugin_path = None
        self.project_path = os.path.join(self.dk_project_path, "dk_app")
        if not os.path.exists(self.project_path):
            public.ExecShell("mkdir -p {}".format(self.project_path))
        self.ollama_online_models_file = "{}/ollama_online_models.json".format(self.project_path)
        self.templates_path = os.path.join(self.project_path, "templates")
        self.app_template_path = None
        self.delete_pl = False
        self.r_id = False
        self.user_conf_file = None
        self.site_domains = None
        self.compose_file = None
        self.all_ports = []
        self.app_cmd_log = None
        self.up_cmd = None
        self.host_str = "127.0.0.1:"
        self.apps_json_file = os.path.join(self.project_path, "apps.json")
        # self.apps_json_file = os.path.join("/www/server/panel/mod/project/docker/app", "apps.json")
        self.app_json = None
        self.apps_json = None
        self.apps_list = None
        self.app_tags_file = os.path.join(self.project_path, "apptags.json")
        # self.app_tags_file = os.path.join("/www/server/panel/mod/project/docker/app", "apptags.json")
        self.installed_json_file = os.path.join(self.project_path, "installed.json")
        self.installed_app_template = {
            "id": None,  # name + appid + appname = md5
            "service_name": None,  # unique
            "appid": None,
            "appdesc": None,
            "appname": None,
            "apptitle": None,
            "appstatus": None,
            "apptype": None,
            "canUpdate": None,
            "createat": None,
            "updateat": None,
            "m_version": None,
            "s_version": None,
            "home": None,
            "cpu": 0,
            "mem": 0,
            "disk": 0,
            "path": None,
            "host_ip": "127.0.0.1",
            "port": None,
            "domain": None,
            "icon": None,
            "status": None,
            "version": None,
            "sort": None,
            "installed": True,
            "backup": None,
            "depDataBase": None,
            "appinfo": None,
        }
        self.installed_app = None
        self.app_conf_file = None
        self.app_installed_json = []
        self.app_version = None
        self.plugin_version = None
        self.app_type = None
        self.backup_path = os.path.join(self.dk_project_path, "backup")
        self.apps_backup_path = os.path.join(self.backup_path, "apps")
        self.service_backup_path = None
        self.backup_conf = {
            "backup_type": "local",
            "backup_path": None,
            "backup_time": str,
            "file_name": None,
            "size": int,
        }
        self.backup_json_file = os.path.join(self.backup_path, "backup.json")
        self.app_scripts = None

    def set_up_cmd(self, cmd) -> 'App':
        self.up_cmd = cmd
        return self

    def set_service_backup_path(self) -> 'App':
        self.service_backup_path = os.path.join(self.apps_backup_path, self.service_name)
        return self

    def set_app_type(self) -> 'App':
        self.app_type = self.app_json["apptype"]
        return self

    def set_service_path(self) -> 'App':
        self.service_path = os.path.join(self.app_path, self.service_name)
        return self

    def set_service_name(self, service_name: str) -> 'App':
        self.service_name = service_name
        return self

    def set_app_conf_file(self) -> 'App':
        self.app_conf_file = os.path.join(self.service_path, "{}_conf.json".format(self.app_name))
        return self

    def apply_installed_app_template(self):
        self.installed_app = self.installed_app_template.copy()

    def set_cmd_log(self) -> 'App':
        self.app_cmd_log = os.path.join("/tmp", "{}.log".format(self.service_name))
        return self

    def set_app_name(self, app_name: str) -> 'App':
        self.app_name = app_name
        return self

    def set_compose_file(self) -> 'App':
        self.compose_file = os.path.join(self.service_path, "docker-compose.yml")
        return self

    def set_site_domains(self, get) -> 'App':
        self.site_domains = get.domain.split('\n')
        return self

    def set_user_conf_file(self) -> 'App':
        self.user_conf_file = os.path.join(self.service_path, "user_conf.json")
        return self

    def set_plugin_path(self, app_name: str) -> 'App':
        self.plugin_path = os.path.join(public.get_panel_path(), "plugin", app_name)
        return self

    def set_app_template_path(self, app_name: str) -> 'App':
        self.app_template_path = os.path.join(self.templates_path, app_name)
        return self

    def set_app_path(self) -> 'App':
        self.app_path = os.path.join(self.project_path, self.app_name)
        return self

    def set_data(self, data: str) -> 'App':
        try:
            self.data = json.loads(data)
            return self
        except:
            pass

    def read_json(self, file):
        try:
            return json.loads(public.readFile(file))
        except:
            return False

    def write_json(self, file, data):
        try:
            public.writeFile(file, json.dumps(data))
            return True
        except:
            return False

    def get_installed_json(self) -> 'App':
        '''
            @name 获取已安装的json配置文件信息
        '''
        try:
            installed_json = json.loads(public.readFile(self.installed_json_file))
            for app_type in installed_json.keys():
                if app_type == self.app_type:
                    self.app_installed_json = installed_json[app_type]
                    return self
        except:
            return self

    def get_app_json(self) -> 'App':
        try:
            try:
                apps_json = json.loads(public.readFile(self.apps_json_file))
            except:
                apps_json = public.readFile(self.apps_json_file)

            if not apps_json:
                return self

            for app in apps_json:
                if app["appname"] == self.app_name:
                    self.app_json = app
                    return self
        except:
            return self

    def download_apps_json(self) -> 'App':
        try:
            public.downloadFile(public.get_url() + '/src/dk_app/apps/apps.json', self.apps_json_file)
            public.downloadFile(public.get_url() + '/src/dk_app/apps/apptags.json', self.app_tags_file)
            return self
        except:
            return self

    def get_apps_json(self) -> 'App':
        try:
            if not os.path.exists(self.apps_json_file) or not os.path.exists(self.app_tags_file):
                public.ExecShell("rm -f {}".format(self.apps_json_file))
                public.ExecShell("rm -f {}".format(self.app_tags_file))
                self.download_apps_json()
            try:
                apps_json = json.loads(public.readFile(self.apps_json_file))
            except:
                apps_json = public.readFile(self.apps_json_file)

            if not apps_json:
                return self

            if type(apps_json) == str:
                try:
                    apps_json = json.loads(apps_json)
                except:
                    return self

            self.apps_json = apps_json
            return self
        except:
            return self

    # 2024/7/29 下午3:33 检查域名是否允许被添加到当前应用
    def check_domain(self):
        if not "DOMAIN" in self.data["install_config@0"] or self.data["install_config@0"]["DOMAIN"] == "":
            return public.returnResult(False, "域名不能为空!")

        # 2024/2/23 下午 12:05 如果其他地方有这个域名，则禁止添加
        for domain in self.site_domains:
            newpid = public.M('domain').where("name=? and port=?", (domain, 80)).getField('pid')
            if newpid:
                result = public.M('sites').where("id=?", (newpid,)).find()
                if result:
                    user_conf = self.read_json(self.user_conf_file)
                    if not user_conf:
                        return public.returnResult(False, '项目类型【{}】已存在域名：{}，请勿重复添加！'.format(
                            result['project_type'], domain))
                    if user_conf.get("install_config@0").get("DOMAIN") != domain:
                        return public.returnResult(False, '项目类型【{}】已存在域名：{}，请勿重复添加！'.format(
                            result['project_type'], domain))
                    self.delete_pl = True
                    self.r_id = result['id']
                    break

        return public.returnResult(True)

    # 2024/7/2 上午10:40 检查wordpress的compose.yml文件是否存在
    def check_yml(self):
        '''
            @name
            @author wzz <2024/7/2 上午10:41>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if not os.path.exists(self.service_path):
            os.makedirs(self.service_path, exist_ok=True, mode=0o755)

        if os.path.exists(os.path.join(self.service_path, "docker-compose.yml")):
            public.ExecShell("rm -f {}".format(os.path.join(self.service_path, "docker-compose.yml")))

        if os.path.exists(os.path.join(self.service_path, ".env")):
            public.ExecShell("rm -f {}".format(os.path.join(self.service_path, ".env")))

        if not os.path.exists(os.path.join(self.service_path, "docker-compose.yml")):
            public.ExecShell("\cp -r {}/*.yml {}".format(
                self.app_template_path, self.service_path))

        if not os.path.exists(os.path.join(self.service_path, ".env")):
            public.ExecShell("\cp -r {}/.env {}".format(
                self.app_template_path, self.service_path))

        if (not os.path.exists(os.path.join(self.service_path, "docker-compose.yml")) or
                not os.path.exists(os.path.join(self.service_path, ".env"))):
            return False
        return True

    # 2024/8/15 下午3:54 更新图标
    def update_ico(self):
        '''
            @name 更新图标
        '''
        zip_ico_path = "{}/BTPanel/static/img/soft_ico/".format(public.get_panel_path())
        ico_path = os.path.join(public.get_panel_path(), "BTPanel/static/img/soft_ico/dkapp")
        if os.path.exists(ico_path):
            public.ExecShell("rm -rf {}".format(ico_path))
        tmp_path = os.path.join("/tmp", "dkapp_ico")
        if not os.path.exists(tmp_path):
            public.ExecShell("mkdir -p {}".format(tmp_path))

        public.downloadFile(public.get_url() + '/src/dk_app/apps/dkapp_ico.zip',
                            os.path.join(tmp_path, "dkapp_ico.zip"))
        public.ExecShell("unzip -o {}/dkapp_ico.zip -d {}".format(tmp_path, zip_ico_path))
        public.ExecShell("cd {} && mv dkapp_ico dkapp".format(zip_ico_path))

        public.ExecShell("chmod -R 644 {}".format(ico_path))
        public.ExecShell("chown -R root:root {}".format(ico_path))
        public.ExecShell("rm -rf {}".format(tmp_path))

    # 2024/8/15 下午5:54 检查baota_net docker网络是否存在
    def check_baota_net(self):
        '''
            @name 检查baota_net 是否存在
        '''
        stdout, stderr = public.ExecShell("docker network ls | grep baota_net")
        if not stdout:
            stdout, stderr = public.ExecShell("docker network create baota_net")
            if stderr and "setlocale: LC_ALL: cannot change locale (en_US.UTF-8)" not in stderr:
                return public.returnResult(False, "创建baota_net网络失败, err: {}".format(stderr))
        return public.returnResult(True)

    # 2024/7/29 下午4:32 检查端口是否被其他进程占用而非本应用
    def check_port(self, get):
        '''
            @name 检查端口是否被其他进程占用而非本应用
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        result_port = int(get.c_port)
        if result_port > 65535 or result_port < 0:
            return public.returnResult(False, "端口范围错误,请传入0-65535之间的端口!")

        import psutil
        for net_port in psutil.net_connections("tcp4"):
            self.all_ports.append(net_port.laddr.port)

        if int(get.c_port) in self.all_ports:
            get.path = self.compose_file
            compose_ps = self.ps(get)
            is_break = False
            for ps in compose_ps:
                if ps == "": continue
                publishers = ps.get("Publishers")
                for pu in publishers:
                    if int(get.c_port) == int(pu.get("PublishedPort")):
                        is_break = True
                        break
                if is_break: break
            else:
                from safeModel.firewallModel import main as firewall_main
                get.port = str(get.c_port)
                res_dict = firewall_main().get_listening_processes(get)
                return public.returnResult(False, "{}端口已被【{}】占用,请更换端口!".format(
                    get.port,
                    res_dict.get("process_name")))

        return public.returnResult(True)

    # 2024/7/29 下午4:56 启动应用
    def up_app(self):
        '''
            @name
            @author wzz <2024/7/29 下午4:57>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        import subprocess
        subprocess.Popen(self.up_cmd, shell=True)

    # 2024/7/29 下午5:03 添加docker网站项目
    def create_proxy(self, get):
        '''
            @name 添加docker网站项目
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        from mod.project.docker.sites.sitesManage import SitesManage
        site_manage = SitesManage()

        try:
            args = public.to_dict_obj({
                "name": self.service_name,
                "type": "app",
                "domains": get.domain,
                "port": get.port_list[0],
                "remark": self.service_name,
            })
            create_result = site_manage.create_site(args)
            if not create_result['status']:
                return public.returnResult(False, create_result['msg'])
        except Exception as e:
            return public.returnResult(False, "域名访问添加失败,原因：{}".format(str(e)))
        return public.returnResult(True)

    # 2024/7/29 下午5:09 检测是否关闭域名访问并且不允许外部访问
    def check_close_domain(self, get):
        '''
            @name 检测是否关闭域名访问并且不允许外部访问
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if get.disable_domain == 1 and get.allow_access == 1:
            self.host_str = "0.0.0.0:"

    # 2024/7/30 上午10:17 写入已安装的APP数据为json
    def write_installed_json(self, get):
        '''
            @name 写入已安装的APP数据为json
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        installed_app_id = public.md5(
            self.service_name + str(self.app_json["appid"]) + self.app_json["appname"] + str(int(time.time())))
        self.installed_app["id"] = installed_app_id
        self.installed_app["service_name"] = self.service_name
        self.installed_app["appid"] = self.app_json["appid"]
        self.installed_app["appdesc"] = self.app_json["appdesc"]
        self.installed_app["appname"] = self.app_json["appname"]
        self.installed_app["apptitle"] = self.app_json["apptitle"]
        self.installed_app["appstatus"] = self.app_json["appstatus"]
        self.installed_app["apptype"] = self.app_json["apptype"]
        self.installed_app["canUpdate"] = 0
        self.installed_app["createat"] = int(time.time())
        self.installed_app["updateat"] = self.app_json["updateat"]
        self.installed_app["home"] = self.app_json["home"]
        self.installed_app["cpu"] = self.app_json["cpu"]
        self.installed_app["mem"] = self.app_json["mem"]
        self.installed_app["disk"] = self.app_json["disk"]
        self.installed_app["path"] = self.app_path
        self.installed_app["port"] = get.port_list
        self.installed_app["icon"] = self.app_json["icon"]
        self.installed_app["status"] = None
        self.installed_app["host_ip"] = get.host_ip
        self.installed_app["m_version"] = get.m_version
        self.installed_app["s_version"] = get.s_version
        self.installed_app["version"] = get.version
        self.installed_app["sort"] = self.app_json["sort"]
        self.installed_app["domain"] = get.site_domains[0] if len(get.site_domains) > 0 else None
        self.installed_app["depDataBase"] = {"db": get.app_db, "type": get.depdbtype}
        self.installed_app["depMiddleWare"] = {"db": get.cache_db_host, "type": get.depmidtype}
        self.installed_app["appinfo"] = get.app_info

        installed_json = self.read_json(self.installed_json_file)
        if installed_json:
            for app_type in installed_json.keys():
                if app_type == self.app_type:
                    installed_json[app_type].append(self.installed_app)
                    break
            else:
                installed_json[self.app_type] = [self.installed_app]
        else:
            installed_json = {self.app_type: [self.installed_app]}

        self.write_json(self.installed_json_file, installed_json)

    # 2024/7/31 上午11:52 校验web项目的传参
    def check_web_params(self, get):
        '''
            @name 参数校验
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.domain = get.get("domain", None)
        if get.domain is None:
            return public.returnResult(False, '参数错误,请传domain参数!')

        get.disable_domain = get.get("disable_domain", None)
        if get.disable_domain is None:
            return public.returnResult(False, '参数错误,请传disable_domain参数!')

        return public.returnResult(True)

    # 2024/7/31 上午11:57 校验通用compose配置传参
    def check_compose_params(self, get):
        '''
            @name 参数校验
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.app_name = get.get("app_name", None)
        if get.app_name is None:
            return public.returnResult(False, '参数错误,请传app_name参数!')

        # get.app_path = get.get("app_path", None)
        # if get.app_path is None:
        #     return public.returnResult(False, '参数错误,请传app_path参数!')

        get.cpus = get.get("cpus", 0)
        get.memory_limit = get.get("memory_limit", 0)

        get.m_version = get.get("m_version", None)
        if get.m_version is None:
            return public.returnResult(False, '参数错误,请传m_version参数!')

        get.s_version = get.get("s_version", None)
        get.s_version = get.s_version.strip(".undefined") if get.s_version is not None else None
        if get.s_version is None:
            return public.returnResult(False, '参数错误,请传s_version参数!')

        if get.s_version == "" or get.s_version is None:
            if get.m_version == "" or get.m_version is None: get.version = "latest"
            get.version = get.m_version
        else:
            get.version = "{}.{}".format(get.m_version, get.s_version)

        get.service_name = get.get("service_name", None)
        if get.service_name is None:
            return public.returnResult(False, '参数错误,请传service_name参数!')

        get.allow_access = get.get("allow_access", None)
        if get.allow_access is None:
            return public.returnResult(False, '参数错误,请传allow_access参数!')

        get.host_ip = "127.0.0.1"
        if int(get.allow_access) == 1:
            get.host_ip = "0.0.0.0"

        get.domain = get.get("domain", "")
        get.site_domains = get.domain.split("\n") if get.domain != "" else []
        if len(get.site_domains) > 0:
            cwsres = self.check_web_status()
            if not cwsres["status"]: return cwsres

        get.disable_domain = get.get("disable_domain", 0)
        if int(get.disable_domain) == 0 and self.app_type in ("BuildWebsite", "Storage"):
            if get.domain == "":
                return public.returnResult(False, '域名不能为空,或者请勾选不设置域名!')

        return public.returnResult(True)

    # 2024/8/1 上午9:45 添加数据库到面板远程数据库管理中
    def apply_database_to_panel(self, get):
        '''
            @name 添加数据库到面板远程数据库管理中
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        # 2024/8/1 上午9:52 因为数据库可能第一时间不会初始化完成，所以先插入数据库服务器信息，弃用导包的方式
        get.db_host = "127.0.0.1"
        get.db_port = get.c_port
        get.db_user = "root"
        if self.app_name == "mysql":
            get.db_password = get.mysql_root_password
        elif self.app_name == "mariadb":
            get.db_password = get.mariadb_root_password
        elif self.app_name == "postgresql":
            get.db_user = get.postgres_user
            get.db_password = get.postgres_password
        get.ps = self.service_name
        get.db_ps = self.service_name

        if public.M("database_servers").where("db_host=? AND db_port=? AND LOWER(db_type)=LOWER('mysql')",
                                              (get.db_host, get.db_port)).count():
            return public.returnMsg(False, "指定服务器已存在: [{}:{}]".format(get.db_host, get.db_port))
        get.db_port = int(get.db_port)
        pdata = {
            "db_host": get.db_host,
            "db_port": get.db_port,
            "db_user": get.db_user,
            "db_type": get.type,
            "db_password": get.db_password,
            "ps": public.xssencode2(get.db_ps.strip()),
            "addtime": int(time.time())
        }

        result = public.M("database_servers").insert(pdata)

        if isinstance(result, int):
            public.WriteLog("数据库管理", "添加远程{app_name}服务器[{db_host}:{db_port}]".format(
                app_name=self.app_name, db_host=get.db_host, db_port=get.db_port))
            return public.returnMsg(True, "添加成功!")
        return public.returnMsg(False, "添加失败： {result}".format(result=result))

    # 2024/8/1 上午9:55 删除面板远程数据库中的指定数据库
    def delete_database_from_panel(self, get):
        '''
            @name 删除面板远程数据库中的指定数据库
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        from database import database
        db_list = database().GetCloudServer(get)
        for db in db_list:
            if "db_type" not in db:
                continue
            if db["ps"] == self.service_name:
                get.id = db['id']
                database().RemoveCloudServer(get)
                break
            if (db["db_host"] == "127.0.0.1" and db["db_port"] == int(get.c_port) and db["db_type"] == "mysql" and
                    db["db_password"] == get.mysql_root_password):
                get.id = db['id']
                database().RemoveCloudServer(get)
                break

    # 2024/8/21 下午3:56 删除面板pgsql指定远程数据库中的数据库
    def delete_pgsql_database_from_panel(self, get):
        '''
            @name 删除面板pgsql指定远程数据库中的数据库
        '''
        from databaseModel.pgsqlModel import main as pgsqlModel
        args = public.dict_obj()
        args.data = {"type": "pgsql"}
        db_list = pgsqlModel().GetCloudServer(args)
        for db in db_list:
            if db["ps"] == self.service_name:
                args.id = db["id"]
                pgsqlModel().RemoveCloudServer(args)
                break

    # 2024/8/15 下午4:01 删除指定app的数据库
    def delete_database_for_app(self, depDataBase):
        '''
            @name 删除指定app的数据库
        '''
        from database import database
        from datalistModel.dataModel import main as dataModel
        args = public.dict_obj()
        args.search = depDataBase
        args.table = "databases"
        args.p = 1
        args.limit = 20000
        args.db_type = "mysql"
        db_list = dataModel().get_data_list(args)
        if type(db_list) != dict: return
        for db in db_list["data"]:
            if db["name"] == depDataBase:
                args.id = db["id"]
                args.name = db["name"]
                database().DeleteDatabase(args)
                break

    # 2024/8/21 下午3:21 删除指定app的pgsql数据库
    def delete_pgsql_database_for_app(self, depDataBase):
        '''
            @name 删除指定app的pgsql数据库
        '''
        from databaseModel.pgsqlModel import main as pgsqlModel
        args = public.dict_obj()
        args.search = depDataBase
        args.table = "databases"
        args.p = 1
        args.limit = 20000
        db_list = pgsqlModel().get_list(args)
        for db in db_list["data"]:
            if db["name"] == depDataBase:
                args.id = db["id"]
                args.name = db["name"]
                pgsqlModel().DeleteDatabase(args)
                break

    # 2024/8/5 下午6:25 获取指定数据库的sid
    def get_database_sid(self, get):
        '''
            @name 获取指定数据库的sid
        '''
        from database import database
        db_list = database().GetCloudServer(get)
        for db in db_list:
            if get.db_host == db["ps"]:
                return db["id"]
        return False

    # 2024/8/5 下午6:25 获取指定数据库的sid
    def get_pgsql_database_sid(self, get):
        '''
            @name 获取指定pgsql数据库的sid
        '''
        from databaseModel.pgsqlModel import main as pgsqlModel
        args = public.dict_obj()
        args.search = get.db_host
        args.table = "databases"
        args.p = 1
        args.limit = 20000
        db_list = pgsqlModel().GetCloudServer(args)
        for db in db_list:
            if get.db_host == db["ps"]:
                return db["id"]
        return False

    # 2024/8/1 上午10:36 构造返回
    def structure_installed_apps(self, app_type, sk_container_list, installed_json, query=None):
        '''
            @name 构造返回
        '''
        installed_apps = []
        current_timestamp = int(time.time())
        from btdockerModel import dk_public as dp
        server_ip = public.GetLocalIp()
        for i in installed_json[app_type]:
            i["server_ip"] = server_ip
            if not "site_id" in i.keys():
                i["site_id"] = None
                i["site_name"] = None
                i["site_addtime"] = None

            if not i["domain"] is None and i["site_id"] is None:
                find_result = dp.sql("docker_sites").where("name=?", (i["domain"],)).find()
                if find_result:
                    i["site_id"] = find_result["id"]
                    i["site_name"] = i["domain"]
                    i["site_addtime"] = find_result["addtime"]
                else:
                    # 2024/11/21 15:18 如果网站没了则不显示域名
                    i["domain"] = None
                    # 2024/11/21 15:08 如果id查询异常则尝试重新添加一个网站；先不使用，用上面的逻辑
                    # from mod.project.docker.sites.sitesManage import SitesManage
                    # site_manage = SitesManage()
                    #
                    # args = public.to_dict_obj({
                    #     "name": i["service_name"],
                    #     "type": "app",
                    #     "domains": i["domain"],
                    #     "port": i["port"][0],
                    #     "remark": i["domain"],
                    # })
                    # create_result = site_manage.create_site(args)
                    # # 2024/11/21 15:14 如果网站无法创建就不显示域名了
                    # if not create_result['status']: i["domain"] = None

            i["createTime"] = i["createat"]
            time_diff = current_timestamp - i["createat"]
            time_diff_delta = timedelta(seconds=time_diff)
            days = time_diff_delta.days
            hours = time_diff_delta.seconds // 3600
            if days > 0:
                i["createat"] = "{}天{}小时".format(days, hours)
            else:
                i["createat"] = "{}小时".format(hours)

            if not query is None:
                if (not query in i["appname"] and not query in i["apptitle"] and
                        not query in i["appdesc"] and not query in i["service_name"]):
                    continue

            i["status"] = None
            if not i["status"] is None and i["status"] != "running":
                continue

            if len(sk_container_list) == 0:
                if os.path.exists("/tmp/{}.log".format(i["service_name"])):
                    i["status"] = "initializing"
                else:
                    i["status"] = "exited"
                if not i in installed_apps:
                    installed_apps.append(i)
                continue

            for j in sk_container_list:
                i["container_id"] = j["Id"]
                if not "createdBy" in j["Labels"].keys():
                    continue
                if j["Labels"]["createdBy"] != "bt_apps":
                    continue

                if "com.docker.compose.service" in j["Labels"].keys() and j["Labels"]["com.docker.compose.service"] == \
                        i["service_name"].lower():
                    i["status"] = j['State']
                    break

                if "com.docker.compose.project" in j["Labels"].keys() and j["Labels"]["com.docker.compose.project"] == \
                        i["service_name"].lower():
                    i["status"] = j['State']
                    break
            else:
                if os.path.exists("/tmp/{}.log".format(i["service_name"])):
                    check_bt_successful = \
                    public.ExecShell("cat /tmp/{}.log | grep bt_successful".format(i["service_name"]))[0]
                    if check_bt_successful == "":
                        check_bt_failed = \
                        public.ExecShell("cat /tmp/{}.log | grep bt_failed".format(i["service_name"]))[0]
                        if check_bt_failed != "":
                            i["status"] = "exited"
                        else:
                            i["status"] = "initializing"
                    else:
                        if i["appname"] == "sftpgo":
                            check_started = \
                            public.ExecShell("cat /tmp/{}.log | grep Started".format(i["service_name"]))[0]
                            if check_started == "":
                                i["status"] = "initializing"
                        else:
                            i["status"] = "exited"
                else:
                    i["status"] = "initializing"

            i["canUpdate"] = 1 if self.check_canupdate(i) else 0
            if i["appname"] == "jenkins":
                jenkins_key_file = "{}/jenkins_key.pl".format(os.path.join(i["path"], i["service_name"]))
                if not os.path.exists(jenkins_key_file):
                    cmd = "docker-compose -f {} exec -it {} cat /var/jenkins_home/secrets/initialAdminPassword".format(
                        os.path.join(i["path"], i["service_name"], "docker-compose.yml"), i["service_name"])
                    pass_key = public.ExecShell(cmd)[0]
                    if pass_key != "": public.writeFile(jenkins_key_file, pass_key)
                else:
                    pass_key = public.readFile(jenkins_key_file)

                if pass_key == "":
                    i["appinfo"].append({"fieldKey": "jenkins_pass_key", "fieldTitle": "jenkins密钥",
                                         "fieldValue": "请等待Jenkins初始化完毕后刷新已安装页面后获取密钥！"})
                else:
                    i["appinfo"].append(
                        {"fieldKey": "jenkins_pass_key", "fieldTitle": "jenkins密钥", "fieldValue": pass_key})
            elif i["appname"] == "nginx_proxy_manager":
                i["appinfo"].append(
                    {"fieldKey": "allow_access", "fieldTitle": "默认邮箱", "fieldValue": "admin@example.com"})
                i["appinfo"].append({"fieldKey": "allow_access", "fieldTitle": "默认密码", "fieldValue": "changeme"})
            elif i["appname"] == "openlist" or i["appname"] == "openlist":
                appname = i["appname"]
                compose_file = "{}/{}/docker-compose.yml".format(i["path"], i["service_name"])
                pass_file = "{}/{}/alist_pass.pl".format(i["path"], i["service_name"])
                i["appinfo"].append({
                    "fieldKey": "{}_user".format(appname),
                    "fieldTitle": "{}账号".format(appname),
                    "fieldValue": "admin",
                })
                if not os.path.exists(pass_file):
                    alist_password = public.GetRandomString(10)
                    i["appinfo"].append({
                        "fieldKey": "{}_password".format(appname),
                        "fieldTitle": "设置{}密码(复制到终端)".format(appname),
                        "fieldValue": "docker-compose -f {compose_file} exec -it {service_name} ./{bin} admin set {alist_password}".format(
                            bin=appname,
                            compose_file=compose_file,
                            service_name=i["service_name"],
                            alist_password=alist_password,
                        ),
                    })
                    public.writeFile(pass_file, alist_password)
                else:
                    alist_password = public.readFile(pass_file)
                    i["appinfo"].append({
                        "fieldKey": "{}_password".format(appname),
                        "fieldTitle": "{}密码".format(appname),
                        "fieldValue": alist_password,
                    })
                    i["appinfo"].append({
                        "fieldKey": "{}_password".format(appname),
                        "fieldTitle": "重设{}密码(复制到终端)".format(appname),
                        "fieldValue": "docker-compose -f {compose_file} exec -it {service_name} ./{bin} admin set {alist_password}".format(
                            bin=appname,
                            compose_file=compose_file,
                            service_name=i["service_name"],
                            alist_password=alist_password,
                        ),
                    })
            elif i["appname"] == "openvpn":
                i["appinfo"].append({"fieldKey": "ovpnfile", "fieldTitle": "ovpn文件(导入客户端)",
                                     "fieldValue": "{}/{}/{}.ovpn".format(i["path"], i["service_name"],
                                                                          i["service_name"])})
            elif i["appname"] == "rustdesk":
                secret_key = public.readFile("{}/{}/data/id_ed25519.pub".format(i["path"], i["service_name"]))
                i["appinfo"].append(
                    {"fieldKey": "secret_key", "fieldTitle": "密钥(key)", "fieldValue": "{}".format(secret_key)})

            allow_access = "是" if i["host_ip"] == "0.0.0.0" else "否" if i["domain"] is None else "是"
            i["appinfo"].append({"fieldKey": "allow_access", "fieldTitle": "允许外部访问", "fieldValue": allow_access})
            if i["status"] == "created": i["status"] = "initializing"
            if not i in installed_apps:
                installed_apps.append(i)

        return installed_apps

    # 2024/8/1 下午4:05 根据apps_json最新版本与已装的版本对比，返回canupdate True/False
    def check_canupdate(self, installed_app):
        '''
            @name 根据apps_json最新版本与已装的版本对比，返回canupdate True/False
        '''
        if installed_app["m_version"] in ("main", "latest"):
            return False

        for app in self.apps_json:
            if app["appname"] == installed_app["appname"]:
                for version in app["appversion"]:
                    if version["m_version"] == installed_app["m_version"]:
                        for s_version in version["s_version"]:
                            if "." in s_version:
                                c_v = float(s_version)
                            else:
                                c_v = int(s_version)

                            if "." in installed_app["s_version"]:
                                i_v = float(installed_app["s_version"])
                            else:
                                i_v = int(installed_app["s_version"])

                            if c_v > i_v:
                                return True
        return False

    # 2024/8/1 下午9:59 停止指定app
    def stop_app(self, get):
        '''
            @name 停止指定app
        '''
        get.service_name = get.get("service_name", None)
        if get.service_name is None:
            return public.returnResult(False, "参数错误,请传service_name参数!")
        get.app_name = get.get("app_name", None)
        if get.app_name is None:
            return public.returnResult(False, "参数错误,请传app_name参数!")

        self.set_service_name(get.service_name)
        self.set_app_name(get.app_name)
        self.set_app_path()
        self.set_service_path()
        self.set_compose_file()
        command = self.set_type(0).set_path(self.compose_file).get_compose_stop()
        stdout, stderr = public.ExecShell(command)
        if stderr:
            if not "Stopped" in stderr:
                return public.returnResult(False, "停止失败: {}!".format(stderr))
        return public.returnResult(True, "停止成功!")

    # 2024/8/1 下午10:02 启动指定app
    def start_app(self, get):
        '''
            @name 启动指定app
        '''
        get.service_name = get.get("service_name", None)
        if not self.service_name is None:
            get.service_name = self.service_name
        if get.service_name is None:
            return public.returnResult(False, "参数错误,请传service_name参数!")
        get.app_name = get.get("app_name", None)
        if not self.app_name is None:
            get.app_name = self.app_name
        if get.app_name is None:
            return public.returnResult(False, "参数错误,请传app_name参数!")

        self.set_service_name(get.service_name)
        self.set_app_name(get.app_name)
        self.set_app_path()
        self.set_cmd_log()
        self.set_service_path()
        self.set_compose_file()
        compose_cmd = self.set_type(0).set_path(self.compose_file).get_compose_up_remove_orphans()
        # command = ("nohup echo '正在启动,可能需要等待1-5分钟以上...' >> {app_cmd_log};"
        #        "{compose_cmd} >> {app_cmd_log} 2>&1 && "
        #        "echo 'bt_successful' >> {app_cmd_log} || echo 'bt_failed' >> {app_cmd_log} &"
        # .format(
        #     compose_cmd=compose_cmd,
        #     app_cmd_log=self.app_cmd_log,
        #     compose_file=self.compose_file,
        # ))
        stdout, stderr = public.ExecShell(compose_cmd)
        if stderr:
            if "create failed" in stderr:
                return public.returnResult(False, "启动失败: {}!".format(stderr))
            if "Started" in stderr:
                return public.returnResult(True, "启动成功!")
            if not "Running" in stderr:
                return public.returnResult(False, "启动失败: {}!".format(stderr))
        return public.returnResult(True, "启动成功!")

    # 2024/8/1 下午10:11 重启指定app
    def restart_app(self, get):
        '''
            @name 重启指定app
        '''
        get.service_name = get.get("service_name", None)
        if get.service_name is None:
            return public.returnResult(False, "参数错误,请传service_name参数!")
        get.app_name = get.get("app_name", None)
        if get.app_name is None:
            return public.returnResult(False, "参数错误,请传app_name参数!")

        self.set_service_name(get.service_name)
        self.set_app_name(get.app_name)
        self.set_app_path()
        self.set_service_path()
        self.set_compose_file()
        command = self.set_type(0).set_path(self.compose_file).get_compose_restart()
        public.ExecShell(command)
        return public.returnResult(True, "重启成功!")

    # 2024/8/1 下午10:50 拉取指定app的镜像
    def pull_app(self):
        '''
            @name 拉取指定app的镜像
        '''
        command = self.set_type(0).set_path(self.compose_file).get_compose_pull()
        public.ExecShell(command)

    # 2024/8/5 下午2:41 检查指定app模板是否存在
    def check_app_template(self, get):
        '''
            @name 检查指定app模板是否存在
        '''
        get.force_update = get.get("force_update", False)

        if get.force_update:
            return self.download_app_template(get)
        if not os.path.exists(self.app_template_path):
            return self.download_app_template(get)
        if not os.path.exists((os.path.join(self.app_template_path, "docker-compose.yml"))):
            return self.download_app_template(get)
        if not os.path.exists((os.path.join(self.app_template_path, ".env"))):
            return self.download_app_template(get)

    # 2024/8/5 下午2:42 下载并解压指定app的模版
    def download_app_template(self, get):
        '''
            @name 下载并解压指定app的模版
        '''
        if os.path.exists(self.app_template_path):
            public.ExecShell("rm -rf {}".format(self.app_template_path))

        app_url = "{}/src/dk_app/apps/templates/{}.zip".format(public.get_url(), get.app_name)
        # 检查GPU参数，重定向templates路径
        if get.get('gpu', 'false') == 'true':
            app_url = "{}/src/dk_app/apps/templates/{}_gpu.zip".format(public.get_url(), get.app_name)

        to_file = '/tmp/{}.zip'.format(get.app_name)
        if os.path.exists(to_file):
            public.ExecShell("rm -f {}".format(to_file))
        public.downloadFile(app_url, to_file)
        if not os.path.exists(to_file) or os.path.getsize(to_file) < 10:
            return public.returnResult(False, "下载失败!")
        public.ExecShell("unzip -o -d {} {}".format(self.templates_path, to_file))
        return public.returnResult(True, "下载成功!")

    # 2024/8/5 下午6:19 创建指定app的数据库
    def create_database(self, get):
        '''
            @name 创建指定app的数据库
        '''
        get.app_db = get.get("app_db", None)
        if get.app_db is None:
            return public.returnResult(False, "参数错误,请传app_db参数!")
        get.db_username = get.get("db_username", None)
        if get.db_username is None:
            return public.returnResult(False, "参数错误,请传username参数!")
        get.db_password = get.get("db_password", None)
        if get.db_password is None:
            return public.returnResult(False, "参数错误,请传password参数!")

        db_sid = self.get_database_sid(get)
        if not db_sid:
            return public.returnResult(False, "未找到指定数据库应用,请前往重建对应数据库或者手动添加远程数据库!")


        res = public.M("databases").where("name=? and sid=?", (get.app_db, db_sid)).find()
        if res:
            return public.returnResult(True, "数据库已存在!")

        from database import database
        args = public.dict_obj()
        args.name = get.app_db
        args.db_user = get.db_username
        args.password = get.db_password
        args.dataAccess = "%"
        args.address = "%"
        args.codeing = "utf8mb4"
        args.dtype = "MySQL"
        args.ps = get.app_db
        args.sid = db_sid
        args.listen_ip = "0.0.0.0/0"
        create_res = database().AddDatabase(args)
        if not create_res["status"]:
            return public.returnResult(False, create_res["msg"])
        return public.returnResult(True, "创建成功!")

    # 2024/8/21 下午2:59 创建指定app的pgsql数据库
    def create_pgsql_database(self, get):
        '''
            @name 创建指定app的pgsql数据库
        '''
        get.app_db = get.get("app_db", None)
        if get.app_db is None:
            return public.returnResult(False, "参数错误,请传database参数!")
        get.db_username = get.get("db_username", None)
        if get.db_username is None:
            return public.returnResult(False, "参数错误,请传username参数!")
        get.db_password = get.get("db_password", None)
        if get.db_password is None:
            return public.returnResult(False, "参数错误,请传password参数!")

        db_sid = self.get_pgsql_database_sid(get)
        if not db_sid:
            return public.returnResult(False, "未找到指定数据库应用!")

        res = public.M("databases").where("name=? and sid=?", (get.app_db, db_sid)).find()
        if res:
            return public.returnResult(True, "数据库已存在!")

        from databaseModel.pgsqlModel import main as pgsqlModel
        args = public.dict_obj()
        args.name = get.app_db
        args.db_user = get.db_username
        args.password = get.db_password
        args.ps = get.app_db
        args.sid = db_sid
        args.listen_ip = "0.0.0.0/0"
        create_res = pgsqlModel().AddDatabase(args)
        if not create_res["status"]:
            return public.returnResult(False, create_res["msg"])
        return public.returnResult(True, "创建成功!")

    def find_field_value(self,data, target_key):
        """
        用于从env中 找出某个env的值
        eg:
            [{host:0.0.0.0},{port:2222}]  port -> 2222

        参数:
        - data: JSON 列表
        - target_key: 要查找的 fieldKey

        返回:
        - 匹配的 fieldValue，如果未找到则返回 None

        """
        for item in data:
            if item.get("fieldKey") == target_key:
                return item.get("fieldValue")
        return None
