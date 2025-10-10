# -*- coding: utf-8 -*-
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyleft (c) 2015-2099 宝塔软件(http://bt.cn) All lefts reserved.
# +-------------------------------------------------------------------
# | Author: wzz
# | email : wzz@bt.cn
# +-------------------------------------------------------------------
# +-------------------------------------------------------------------
# | docker app 管理模型 -
# +-------------------------------------------------------------------
import json
import os.path
import sys
import time

if "/www/server/panel/class" not in sys.path:
    sys.path.append('/www/server/panel/class')

import public
from mod.project.docker.app.base import App


class AppManage(App):

    def __init__(self):
        super(AppManage, self).__init__()

    # 2023/12/4 下午 5:12 获取首次安装的初始化配置
    def get_install_conf(self, get):
        '''
            @name 获取首次安装的初始化配置
            @author wzz <2023/12/4 下午 3:17>
            @param 参数名<数据类型> 参数描述
            @return 数据类型
        '''
        try:
            self.get_app_json()
            if self.app_json is None:
                return {}

            self.app_json["field"][-2]["default"] = public.GetRandomString(16)
            return self.app_json
        except:
            return public.returnResult(False, "获取安装配置失败,请尝试卸载重新安装!")

    # 2023/12/4 下午 5:12 创建app
    def create_app(self, get):
        '''
            @name 创建app
            @author wzz <2023/12/4 下午 4:40>
            @param 参数名<数据类型> 参数描述
            @return 数据类型
        '''
        get.app_name = get.get("app_name", None)
        if get.app_name is None:
            return public.returnResult(False, "参数错误,请传app_name参数")

        self.set_app_name(get.app_name)
        self.get_app_json()
        self.set_app_type()

        if get.get('gpu', 'false') == 'true':
            self.set_app_template_path("{}_gpu".format(self.app_name))
        else:
            self.set_app_template_path(self.app_name)

        self.check_app_template(get)
        from btdockerModel import setupModel as ds
        if not ds.main().get_service_status():
            return public.returnResult(False, "docker服务未启动,请先启动docker服务!")
        if not ds.main().check_docker_service():
            return public.returnResult(False, "docker服务未安装成功，请先安装docker服务!")

        ccpres = self.check_compose_params(get)
        if not ccpres["status"]: return ccpres

        self.set_service_name(get.service_name)
        get.row = 10000
        installed_apps = self.get_installed_apps(get)
        self.installed_apps = installed_apps
        if installed_apps["data"]:
            for app in installed_apps["data"]:
                if app["service_name"] == self.service_name:
                    return public.returnResult(False, "已存在相同服务名称: {},请更换其他名称".format(self.service_name))

            # 2024/8/6 上午11:11 检查依赖应用是否安装
            if not self.app_json["depend"] is None:
                check_len = 0
                depend_len = len(self.app_json["depend"])
                for depend_app in self.app_json["depend"]:
                    for app in installed_apps["data"]:
                        if app["service_name"] == self.service_name:
                            return public.returnResult(False, "已存在相同服务名称: {},请更换其他名称".format(
                                self.service_name))

                        if app["appname"] in depend_app["appname"] and app["m_version"] in tuple(
                                depend_app["appversion"]):
                            check_len += 1
                            break

                if check_len != depend_len:
                    return public.returnResult(False, "请先安装依赖应用: {}".format(",".join(
                        ["{}:{}".format(i["appname"], "/".join(i["appversion"])) for i in self.app_json["depend"]])))
        else:
            if not self.app_json["depend"] is None:
                return public.returnResult(False, "请先安装依赖应用: {}".format(",".join(
                    ["{}:{}".format(i["appname"], "/".join(i["appversion"])) for i in self.app_json["depend"]])))

        if len(get.site_domains) > 0:
            for domain in get.site_domains:
                if not public.is_domain(domain):
                    return public.returnResult(False, "域名【{}】格式不正确".format(domain))

                newpid = public.M('domain').where("name=? and port=?", (domain, 80)).getField('pid')
                if newpid:
                    result = public.M('sites').where("id=?", (newpid,)).find()
                    if result:
                        return public.returnResult(False, '项目类型【{}】已存在域名：{}，请勿重复添加！'.format(
                            result['project_type'], domain))

        self.apply_installed_app_template()
        self.set_app_path()
        get.app_path = self.app_path
        self.set_service_path()
        self.set_cmd_log()
        if "scripts" in self.app_json.keys():
            self.app_scripts = self.app_json["scripts"]

        cbnet = self.check_baota_net()
        if not cbnet["status"]: return cbnet

        if not self.check_yml():
            return public.returnResult(False, "初始化{}失败,检测到docker-compose.yml文件不存在,请卸载重装后再试".format(
                self.app_name))
        self.set_compose_file()
        public.ExecShell("chmod -R 755 {}".format(self.app_path))
        public.ExecShell("echo -n > {}".format(self.app_cmd_log))

        self.app_info = [
            {
                "fieldKey": "service_name",
                "fieldTitle": "名称",
                "fieldValue": self.service_name,
            },
            {
                "fieldKey": "app_name",
                "fieldTitle": "应用名称",
                "fieldValue": self.app_json["apptitle"],
            },
            {
                "fieldKey": "app_type",
                "fieldTitle": "应用类型",
                "fieldValue": self.app_json["appTypeCN"],
            }
        ]

        ucres = self.update_conf(get)
        if not ucres["status"]: return ucres
        # 2023/12/5 上午 9:48 写入安装后的配置文件
        # self._write_conf(get)
        # 2024/8/8 上午11:32 设置启动命令行
        cmd = ("nohup echo '正在启动,可能需要等待1-5分钟以上...' >> {app_cmd_log};"
               "docker-compose -f {compose_file} up -d >> {app_cmd_log} 2>&1 && "
               "echo 'bt_successful' >> {app_cmd_log} || echo 'bt_failed' >> {app_cmd_log} &"
        .format(
            app_cmd_log=self.app_cmd_log,
            compose_file=self.compose_file,
        ))
        from mod.project.docker.app.gpu.tools import GPUTool
        if get.get('gpu', 'false') == 'true' and not GPUTool.is_install_ctk():
            cmd = ("nohup echo '正在启动,可能需要等待1-5分钟以上...' >> {app_cmd_log};"
                   "{install_ctk};"
                   "docker-compose -f {compose_file} up -d >> {app_cmd_log} 2>&1 && "
                   "echo 'bt_successful' >> {app_cmd_log} || echo 'bt_failed' >> {app_cmd_log} &"
            .format(
                app_cmd_log=self.app_cmd_log,
                install_ctk=GPUTool.ctk_install_cmd(self.app_cmd_log),
                compose_file=self.compose_file,
            ))
        self.set_up_cmd(cmd)

        # 2024/8/7 上午11:05 处理复杂一些的应用程序配置
        clres = self.set_complex_conf(get)
        if not clres["status"]: return clres

        get.app_info = self.app_info
        get.app_info.append({
            "fieldKey": "installed_log",
            "fieldTitle": "安装日志",
            "fieldValue": self.app_cmd_log,
        })
        get.app_info.append({
            "fieldKey": "gpu",
            "fieldTitle": "是否开启GPU",
            "fieldValue": True if get.get('gpu', 'false') == 'true' else False
        })

        # 2023/12/5 上午 9:48 启动应用
        self.up_app()
        create_result = {"status": True}
        if len(get.site_domains) > 0:
            create_result = self.create_proxy(get)

        self.write_installed_json(get)
        if self.app_name in ("mysql", "mariadb"):
            get.type = "mysql"
            self.apply_database_to_panel(get)
        elif self.app_name in ("postgresql"):
            get.type = "pgsql"
            self.apply_database_to_panel(get)

        public.set_module_logs('dkapp_{}'.format(self.app_name), 'create_app', 1)
        public.set_module_logs('dkapp', 'create_app', 1)

        if not create_result["status"]:
            return public.returnResult(True, "应用创建成功,反向代理创建失败,请处理错误后手动创建,错误详情: {}".format(
                create_result["msg"]))

        return public.returnResult(True, "应用创建成功,请耐心等待应用初始化,可能需要等待1-5分钟...")

    # 2023/12/4 下午 10:03 写入安装后的配置文件
    def _write_conf(self, get):
        '''
            @name 写入安装后的配置文件
            @author wzz <2023/12/4 下午 10:04>
            @param 参数名<数据类型> 参数描述
            @return 数据类型
        '''
        self.set_user_conf_file()
        public.writeFile(self.user_conf_file, json.dumps(get.__dict__))

        install_conf = self.get_install_conf(get)

        for field in install_conf['field']:
            field['default'] = getattr(get, field["attr"])

        self.set_app_conf_file()
        public.writeFile(self.app_conf_file, json.dumps(install_conf))

    # 2023/12/5 上午 11:44 更新.env文件和用户默认配置文件
    def update_conf(self, get):
        '''
            @name 更新.env文件和用户默认配置文件
            @author wzz <2023/12/5 上午 11:44>
            @param 参数名<数据类型> 参数描述
            @return 数据类型
        '''
        try:
            get.depend_app = get.get("depend_app", None)
            if type(get.depend_app) == str:
                get.depend_app = json.loads(get.depend_app)
            get.port_list = []
            get.app_db = None
            get.db_host = None
            get.depdbtype = None
            get.depmidtype = None
            get.cache_db_host = None
            envs = None
            if self.app_json["apptype"] == "MCP" :
                server_path,command,envs =  self.update_mcp_conf(get)
                self.app_json["env"].append({"key": "server_path","type": "string","default": "","desc": "服务路径"})
                self.app_json["env"].append({"key": "command","type": "string","default": "","desc": "启动命令"})
                get.server_path = server_path
                get.command = command

            if os.path.isdir("/etc/timezone"): public.ExecShell("rm -rf /etc/timezone")
            if not os.path.isfile("/etc/timezone"): public.writeFile("/etc/timezone", "Asia/Shanghai")

            for ap_json in self.app_json["env"]:
                if ap_json["type"] == "port":
                    get.c_port = None
                    get.c_port = get.get(ap_json["key"], None)
                    if get.c_port is None:
                        return public.returnResult(False, "参数错误,请传{}参数".format(ap_json["key"]))

                    for installed in self.installed_apps["data"]:
                        if get.c_port in installed["port"]:
                            return public.returnResult(False, "端口【{}】已被【{}】使用,请更换其他端口".format(get.c_port,
                                                                                                           installed[
                                                                                                               "service_name"]))
                    cpres = self.check_port(get)
                    if not cpres["status"]: return cpres
                    get.port_list.append(get.c_port)
                elif ap_json["type"] == "password":
                    key_name = ap_json["key"]
                    random_pass = public.GetRandomString(16)
                    setattr(get, key_name, get.get(key_name, random_pass))
                elif ap_json["type"] == "db_host":
                    if get.depend_app is None:
                        return public.returnResult(False, "请选择需要连接的数据库！")
                    if get.db_host is None:
                        for depend_app in get.depend_app:
                            if depend_app["appname"] in ("mysql", "mariadb", "mongodb", "postgresql"):
                                get.db_host = depend_app["service_name"]
                                get.depdbtype = depend_app["appname"]
                                break
                    setattr(get, ap_json["key"], get.db_host)
                elif ap_json["type"] == "cache_db_host":
                    if get.cache_db_host is None or get.depmidtype is None:
                        if get.depend_app is None:
                            return public.returnResult(False, "请选择需要连接的缓存器！")
                        for depend_app in get.depend_app:
                            if depend_app["appname"] == "redis" or depend_app["appname"] == "memcached":
                                get.cache_db_host = depend_app["service_name"]
                                get.depmidtype = depend_app["appname"]
                                break
                    setattr(get, ap_json["key"], get.cache_db_host)
                elif ap_json["type"] == "redis_password":
                    if get.depend_app is None:
                        return public.returnResult(False, "请选择需要连接的缓存器！")
                    for depend_app in get.depend_app:
                        if depend_app["appname"] == "redis" or depend_app["appname"] == "memcached":
                            get.cache_db_host = depend_app["service_name"]
                            get.depmidtype = depend_app["appname"]
                            break

                    args = public.dict_obj()
                    args.service_name = get.cache_db_host
                    appinfo = self.get_installed_app_info_j(args)
                    if appinfo["data"] is None:
                        return public.returnResult(False, "未找到缓存器信息")

                    for api in appinfo["data"]:
                        if api["fieldKey"] == "redis_password":
                            setattr(get, "redis_password", api["fieldValue"])
                            break
                elif ap_json["type"] == "database":
                    get.app_db = getattr(get, ap_json["key"])
                elif ap_json["type"] == "username":
                    get.db_username = getattr(get, ap_json["key"])
                elif ap_json["type"] in ("mysql_password", "mariadb_password"):
                    mysql_password = public.GetRandomString(16)
                    if not hasattr(get, ap_json["key"]):
                        get.db_password = mysql_password
                    else:
                        get.db_password = getattr(get, ap_json["key"])
                    for depend_app in get.depend_app:
                        if depend_app["appname"] in ("mysql", "mariadb"):
                            get.db_host = depend_app["service_name"]
                            get.depdbtype = depend_app["appname"]
                            break
                    if not get.db_host is None:
                        create_res = self.create_database(get)
                        if not create_res["status"]: return create_res
                    setattr(get, ap_json["key"], get.db_password)
                elif ap_json["type"] in ("pgsql_password"):
                    pgsql_password = public.GetRandomString(16)
                    if not hasattr(get, ap_json["key"]):
                        get.db_password = pgsql_password
                    else:
                        get.db_password = getattr(get, ap_json["key"])
                    for depend_app in get.depend_app:
                        if depend_app["appname"] in ("postgresql"):
                            get.db_host = depend_app["service_name"]
                            get.depdbtype = depend_app["appname"]
                            break
                    if not get.db_host is None:
                        create_res = self.create_pgsql_database(get)
                        if not create_res["status"]: return create_res
                    setattr(get, ap_json["key"], get.db_password)
                elif ap_json["type"] in ("defaultUserName", "defaultPassWord"):
                    setattr(get, ap_json["key"], ap_json["default"])
                elif ap_json["type"] == "domain_host":
                    if len(get.site_domains) > 0:
                        setattr(get, ap_json["key"], get.site_domains[0])
                    else:
                        setattr(get, ap_json["key"], public.GetLocalIp())
                elif ap_json["type"] == "server_ip":
                    if not hasattr(get, ap_json["key"]) or getattr(get, ap_json["key"]) is None or getattr(get, ap_json[
                        "key"]) == "":
                        setattr(get, ap_json["key"], public.GetLocalIp())

                if ap_json["key"] == "app_path":
                    get.app_path = self.service_path
                    public.ExecShell("sed -i 's,^APP_PATH=.*,APP_PATH={app_path},' {app_path}/.env".format(
                        app_path=self.service_path))
                elif ap_json["type"] == "url":
                    public.ExecShell("sed -i 's,^{field_attr}=.*,{field_attr}={get_parm},' {service_path}/.env".format(
                        field_attr=ap_json["key"].upper(),
                        get_parm=getattr(get, ap_json["key"]),
                        service_path=self.service_path))
                elif ap_json["key"] == "memory_limit":
                    public.ExecShell(
                        "sed -i 's/^{field_attr}=.*/{field_attr}={get_parm}MB/' {service_path}/.env".format(
                            field_attr=ap_json["key"].upper(),
                            get_parm=getattr(get, ap_json["key"]),
                            service_path=self.service_path))
                else:
                    get_parm = getattr(get, ap_json["key"]).replace('/', '\\/')
                    public.ExecShell("sed -i 's/^{field_attr}=.*/{field_attr}={get_parm}/' {service_path}/.env".format(
                        field_attr=ap_json["key"].upper(),
                        get_parm=get_parm,
                        service_path=self.service_path))

                if not ap_json["key"] in ("version", "host_ip"):
                    if ap_json["key"] in ("cpus", "memory_limit") and int(getattr(get, ap_json["key"])) == 0:
                        self.app_info.append({
                            "fieldKey": ap_json["key"],
                            "fieldTitle": ap_json["desc"],
                            "fieldValue": "不限制",
                        })
                    else:
                        self.app_info.append({
                            "fieldKey": ap_json["key"],
                            "fieldTitle": ap_json["desc"],
                            "fieldValue": getattr(get, ap_json["key"]),
                        })

            for volume in self.app_json["volumes"].keys():
                if self.app_json["volumes"][volume]["type"] == "path":
                    if os.path.exists(os.path.join(self.app_template_path, volume)):
                        public.ExecShell(
                            "cp -r {}/{} {}/{}".format(self.app_template_path, volume, self.service_path, volume))
                    else:
                        public.ExecShell("mkdir -p {}".format(self.service_path + "/{}".format(volume)))
                    public.ExecShell("chmod -R 777 {}".format(self.service_path + "/{}".format(volume)))
                if self.app_json["volumes"][volume]["type"] == "file":
                    public.ExecShell(
                        "\cp -r {}/{} {}/{}".format(self.app_template_path, volume, self.service_path, volume))

            if self.app_json["appname"] == "mysql":
                if get.m_version == "5":
                    command = "--character-set-server=utf8mb4 --collation-server=utf8mb4_general_ci --explicit_defaults_for_timestamp=true --lower_case_table_names=1"
                    if "5" in get.s_version: command = "--character-set-server=utf8mb4 --collation-server=utf8mb4_general_ci --lower_case_table_names=1"
                    if not os.path.exists(os.path.join(self.service_path, "my.cnf")):
                        public.ExecShell(
                            "\cp -r {}/my5.cnf {}/my.cnf".format(self.app_template_path, self.service_path))
                elif get.m_version == "9":
                    command = ""
                    if not os.path.exists(os.path.join(self.service_path, "my.cnf")):
                        public.ExecShell(
                            "\cp -r {}/my9.cnf {}/my.cnf".format(self.app_template_path, self.service_path))
                else:
                    command = "--default-authentication-plugin=mysql_native_password"
                    if get.m_version == "8" and "4" in get.s_version: command = ""
                    if not os.path.exists(os.path.join(self.service_path, "my.cnf")):
                        public.ExecShell(
                            "\cp -r {}/my8.cnf {}/my.cnf".format(self.app_template_path, self.service_path))
                public.ExecShell("sed -i 's/^COMMAND=.*/COMMAND={}/' {}/.env".format(command, self.service_path))
            if get.get("editcompose","") != "":
                public.WriteFile(self.service_path+"/docker-compose.yml",get.editcompose)
            public.ExecShell("sed -i 's/BT_SERVICE_NAME6/{}/g' {}/*.yml".format(self.service_name, self.service_path))
            if envs is not None:
                self.append_compose_environment(self.service_path+"/docker-compose.yml",self.service_name,envs)
            return public.returnResult(True, "更新配置成功")
        except Exception as e:
            return public.returnResult(False, "更新配置失败: {}".format(str(e)))

    def update_mcp_conf(self,get):
        """
        MCP 应用的配置更新

        in: get.mcp_server_config
            {
                "mcpServers": {
                    "amap-maps": {
                        "command": "npx",
                        "args": [
                            "-y",
                            "@amap/amap-maps-mcp-server"
                        ],
                        "env": {
                            "AMAP_MAPS_API_KEY": "您在高德官网上申请的key",
                            "XXXX":"XXXX"
                        }
                    }
                }
            }
        out:
            SSE_PATH: "/amap-maps"
            COMMAND: "npx -y @amap/amap-maps-mcp-server"
            ENVS: {
                    "AMAP_MAPS_API_KEY": "您在高德官网上申请的key",
                    "XXXX":"XXXX"
                }

        """
        mcp_server_config = json.loads(get.get("mcp_server_config"))
        if not mcp_server_config:
            return public.returnResult(False, "MCP服务器配置错误")
        if not isinstance(mcp_server_config, dict):
            return public.returnResult(False, "MCP服务器配置错误")
        if "mcpServers" not in mcp_server_config:
            return public.returnResult(False, "MCP服务器配置错误")
        if not isinstance(mcp_server_config.get("mcpServers"), dict):
            return public.returnResult(False, "MCP服务器配置错误")

        # 获取 mcpServers 中的第一个服务器名称
        server_name = list(mcp_server_config['mcpServers'].keys())[0]

        # 构建 SSE_PATH
        server_path = "/{server_path}".format(server_path=server_name)

        # 获取服务器配置
        server_config = mcp_server_config['mcpServers'][server_name]

        # 构建 COMMAND
        command = server_config['command']
        args = " ".join(server_config['args'])
        command = "{command} {args}".format(command=command, args=args)
        envs = server_config.get('env',None)

        return server_path, command, envs

    def append_compose_environment(self,file_path, service_name, new_env):
        """
        设置compose文件中的env
        @param file_path compose完整路径
        @param service_name 要修改env的services
        @new_env env环境 {'NEW_VAR': 'new_value', 'ANOTHER_VAR': 'another_value'}
        @reutrn true false
        """
        if len(new_env.keys()) == 0:
            return public.returnMsg(True,"")

        with open(file_path, 'r') as file:
            lines = file.readlines()

        # 找到服务的起始行
        service_start = -1
        for i, line in enumerate(lines):
            if line.strip().startswith(service_name + ':'):
                service_start = i
                break
        if service_start == -1:
            return public.returnMsg(False,"未找到服务 '{}'。".format(service_name))

        # 找到服务块的结束行
        service_end = len(lines)
        for i in range(service_start + 1, len(lines)):
            if lines[i].strip() and not lines[i].startswith(' '):
                service_end = i
                break

        # 找到 environment: 的位置
        env_line = -1
        for i in range(service_start, service_end):
            if lines[i].strip() == 'environment:':
                env_line = i
                break

        # 确定缩进（与服务块对齐，通常为两个空格）
        indent = '  '  # 默认缩进
        for i in range(service_start + 1, service_end):
            if lines[i].strip():
                indent = lines[i][:lines[i].index(lines[i].strip())]
                break

        # 准备要插入的环境变量行
        env_lines = ["{indent}  {key}: {value}\n".format(indent = indent,key=key, value=value) for key, value in new_env.items()]

        # 插入新环境变量
        if env_line != -1:
            # 在 environment: 的下一行插入
            lines[env_line + 1:env_line + 1] = env_lines
        else:
            # 在 image: 的上一行插入 environment: 和新环境变量
            image_line = -1
            for i in range(service_start, service_end):
                if lines[i].strip().startswith('image:'):
                    image_line = i
                    break
            if image_line == -1:
                return public.returnMsg(False,"服务 '{}' 中未找到 image:。".format(service_name))
            lines[image_line:image_line] = [f"{indent}environment:\n"] + env_lines

        with open(file_path, 'w') as file:
            file.writelines(lines)
        return public.returnMsg(True,"")

    # 2024/8/7 上午11:08 处理负责的app配置更新
    def set_complex_conf(self, get):
        if self.app_name in ("frps", "frpc"):
            return self.set_frp_conf(get)
        # elif self.app_name == "alist":
        #     return self.set_alist_conf(get)
        elif self.app_name == "nocodb":
            return self.set_nocodb_conf(get)
        elif self.app_name == "homeassistant":
            return self.set_homeassistant_conf(get)
        elif self.app_name == "openvpn":
            return self.set_openvpn_conf(get)
        elif self.app_name == "deepseek_r1":
            if self.app_scripts is None:
                return public.returnResult(False, "未找到deepseek_r1的脚本文件")

            # 2025/2/8 10:07 获取当前内存大小，如果剩余可用内存不足1550mb，就不能部署
            import psutil
            memory = psutil.virtual_memory()
            if memory.available < 1550 * 1024 * 1024:
                return public.returnResult(False, "内存不足1550MB，无法部署deepseek_r1")

            return self.set_deepseek_r1_conf(get)
        elif self.app_type == "MCP":
            server_path = self.find_field_value(self.app_info,"server_path")
            self.app_info.append({
                "fieldKey": "local_server_url",
                "fieldTitle": "内网URL",
                "fieldValue": "http://{}:{}{}".format(public.get_local_ip(), get.c_port,server_path),
            })
            self.app_info.append({
                "fieldKey": "public_server_url",
                "fieldTitle": "公网URL",
                "fieldValue": "http://{}:{}{}".format(public.get_server_ip(), get.c_port,server_path),
            })

        return public.returnResult(True, "无需处理")

    # 2025/2/5 17:22 处理deepseek_r1的配置
    def set_deepseek_r1_conf(self, get):
        '''
            @name 处理deepseek_r1的配置
        '''
        from mod.project.docker.app.gpu.tools import GPUTool
        command = self.app_scripts["command"].format(get.version)
        if get.get('gpu', 'false') == 'true' and not GPUTool.is_install_ctk():
            cmd = ("nohup echo '正在启动,可能需要等待1-5分钟以上...' >> {app_cmd_log};"
                   "{ctk_install_cmd};"
                   "docker-compose -f {compose_file} up -d >> {app_cmd_log} 2>&1 && "
                   "echo '等待 Ollama 服务启动...' >> {app_cmd_log} && "
                   "until curl -sSf http://localhost:{ollama_port}/api/tags; do sleep 2; done && "
                   "echo '启动模型 deepseek-r1...' >> {app_cmd_log} && "
                   "docker-compose -f {compose_file} exec -it ollama {command} >> {app_cmd_log} 2>&1 && "
                   "docker-compose -f {compose_file} restart >> {app_cmd_log} 2>&1 && "
                   "echo 'bt_successful' >> {app_cmd_log} || echo 'bt_failed' >> {app_cmd_log} &"
            .format(
                app_cmd_log=self.app_cmd_log,
                ctk_install_cmd=GPUTool.ctk_install_cmd(self.app_cmd_log),
                compose_file=self.compose_file,
                ollama_port=get.ollama_port,
                command=command,
            ))
        else:
            cmd = ("nohup echo '正在启动,可能需要等待1-5分钟以上...' >> {app_cmd_log};"
                   "docker-compose -f {compose_file} up -d >> {app_cmd_log} 2>&1 && "
                   "echo '等待 Ollama 服务启动...' >> {app_cmd_log} && "
                   "until curl -sSf http://localhost:{ollama_port}/api/tags; do sleep 2; done && "
                   "echo '启动模型 deepseek-r1...' >> {app_cmd_log} && "
                   "docker-compose -f {compose_file} exec -it ollama {command} >> {app_cmd_log} 2>&1 && "
                   "docker-compose -f {compose_file} restart >> {app_cmd_log} 2>&1 && "
                   "echo 'bt_successful' >> {app_cmd_log} || echo 'bt_failed' >> {app_cmd_log} &"
            .format(
                app_cmd_log=self.app_cmd_log,
                compose_file=self.compose_file,
                ollama_port=get.ollama_port,
                command=command,
            ))
        self.set_up_cmd(cmd)

        return public.returnResult(True, "deepseek_r1配置成功")

    # 2024/8/7 上午11:06 处理frp/s/c配置的更新
    def set_frp_conf(self, get):
        '''
            @name 处理frp/s/c配置的更新
        '''
        if self.app_name == "frps":
            frp_conf = "{}/data/frps.toml".format(self.service_path)
            if not os.path.exists(frp_conf):
                if os.path.exists(os.path.join(self.app_template_path, "frps.toml")):
                    public.ExecShell(
                        "\cp -r {}/frps.toml {}/data/frps.toml".format(self.app_template_path, self.service_path))
            public.ExecShell("rm -f {}/frps.toml".format(self.service_path))
        elif self.app_name == "frpc":
            frp_conf = "{}/data/frpc.toml".format(self.service_path)
            if not os.path.exists(frp_conf):
                if os.path.exists(os.path.join(self.app_template_path, "frpc.toml")):
                    public.ExecShell(
                        "\cp -r {}/frpc.toml {}/data/frpc.toml".format(self.app_template_path, self.service_path))
            public.ExecShell("rm -f {}/frpc.toml".format(self.service_path))
        else:
            return public.returnResult(False, "未知的应用程序: {}".format(self.app_name))

        if not os.path.exists(frp_conf):
            return public.returnResult(False, "未检测到{}配置文件: {}".format(self.app_name, frp_conf))

        frp_conf_content = public.readFile(frp_conf)
        if self.app_name == "frps":
            frp_conf_content = frp_conf_content.replace("bindPort = 7000", "bindPort = {}".format(get.frps_server_port))
            frp_conf_content = frp_conf_content.replace("vhostHTTPPort = 40800",
                                                        "vhostHTTPPort = {}".format(get.frps_http_port))
            frp_conf_content = frp_conf_content.replace("vhostHTTPSPort = 40443",
                                                        "vhostHTTPSPort = {}".format(get.frps_https_port))
            frp_conf_content = frp_conf_content.replace("webServer.port = 7500",
                                                        "webServer.port = {}".format(get.frps_web_port))
            frp_conf_content = frp_conf_content.replace("webServer.user = \"\"",
                                                        "webServer.user = \"{}\"".format(get.frps_user))
            frp_conf_content = frp_conf_content.replace("webServer.password = \"\"",
                                                        "webServer.password = \"{}\"".format(get.frps_password))
        else:
            frp_conf_content = frp_conf_content.replace("serverPort = 7000",
                                                        "serverPort = {}".format(get.frps_server_port))
            frp_conf_content = frp_conf_content.replace("serverAddr = \"127.0.0.1\"",
                                                        "serverAddr = \"{}\"".format(get.frps_server_ip))
            frp_conf_content = frp_conf_content.replace("webServer.port = 7400",
                                                        "webServer.port = {}".format(get.frpc_web_port))
            frp_conf_content = frp_conf_content.replace("webServer.user = \"\"",
                                                        "webServer.user = \"{}\"".format(get.frpc_user))
            frp_conf_content = frp_conf_content.replace("webServer.password = \"\"",
                                                        "webServer.password = \"{}\"".format(get.frpc_password))

        public.writeFile(frp_conf, frp_conf_content)

        if int(get.allow_access) == 1:
            # 2024/4/18 上午10:21 添加端口到系统防火墙
            from firewallModel.comModel import main as comModel
            firewall_com = comModel()
            if self.app_name == "frps":
                get.port = get.frps_server_port
                firewall_com.set_port_rule(get)
                get.port = get.frps_http_port
                firewall_com.set_port_rule(get)
                get.port = get.frps_https_port
                firewall_com.set_port_rule(get)
                get.port = get.frps_web_port
                firewall_com.set_port_rule(get)
            else:
                get.port = get.frpc_web_port
                firewall_com.set_port_rule(get)
        return public.returnResult(True, "更新{}配置成功".format(self.app_name))

    # 2024/8/8 上午11:21 处理alist的密码
    def set_alist_conf(self, get):
        '''
            @name 处理alist的密码
        '''
        alist_password = public.GetRandomString(10)
        self.app_info.append({
            "fieldKey": "alist_user",
            "fieldTitle": "Alist账号",
            "fieldValue": "admin",
        })
        self.app_info.append({
            "fieldKey": "alist_password",
            "fieldTitle": "Alist密码",
            "fieldValue": alist_password,
        })

        # 2024/8/8 上午11:32 重新设置启动命令行
        cmd = ("nohup echo '正在启动,可能需要等待1-5分钟以上...' >> {app_cmd_log};"
               "docker-compose -f {compose_file} up -d >> {app_cmd_log} 2>&1 && "
               "docker-compose -f {compose_file} exec -it {service_name} ./alist admin set {alist_password} >> {app_cmd_log} 2>&1 && "
               "echo 'bt_successful' >> {app_cmd_log} || echo 'bt_failed' >> {app_cmd_log} &"
        .format(
            service_name=self.service_name,
            alist_password=alist_password,
            app_cmd_log=self.app_cmd_log,
            compose_file=self.compose_file,
        ))
        self.set_up_cmd(cmd)

        return public.returnResult(True, "更新Alist配置成功")

    # 2024/8/22 下午5:33 处理nocodb的数据库连接
    def set_nocodb_conf(self, get):
        '''
            @name 处理nocodb的数据库连接
        '''
        if get.depend_app is None:
            return public.returnResult(False, "请选择需要连接的数据库！")
        if get.db_host is None:
            for depend_app in get.depend_app:
                if depend_app["appname"] in ("mysql", "mariadb", "mongodb", "postgresql"):
                    get.db_host = depend_app["service_name"]
                    get.depdbtype = depend_app["appname"]
                    break

        public.ExecShell("sed -i 's/^DB_HOST=.*/DB_HOST={}/' {}/.env".format(get.db_host, self.service_path))
        get.app_db = get.db_name
        if get.depdbtype in ("mysql", "mariadb"):
            create_res = self.create_database(get)
            if not create_res["status"]: return create_res
            public.ExecShell("sed -i 's/^DB_PORT=.*/DB_PORT=3306/' {}/.env".format(self.service_path))
            public.ExecShell("sed -i 's/^DB_TYPE=.*/DB_TYPE=mysql2/' {}/.env".format(self.service_path))
        elif get.depdbtype in ("postgresql"):
            create_res = self.create_pgsql_database(get)
            if not create_res["status"]: return create_res
            public.ExecShell("sed -i 's/^DB_PORT=.*/DB_PORT=5432/' {}/.env".format(self.service_path))
            public.ExecShell("sed -i 's/^DB_TYPE=.*/DB_TYPE=pg/' {}/.env".format(self.service_path))
        else:
            return public.returnResult(False, "未知的数据库类型: {}".format(get.depdbtype))
        return public.returnResult(True, "更新Nocodb配置成功")

    # 2024/8/23 下午4:43 处理homeassistant配置
    def set_homeassistant_conf(self, get):
        '''
            @name 处理homeassistant
        '''
        get.c_port = 8123
        for installed in self.installed_apps["data"]:
            if get.c_port in installed["port"]:
                return public.returnResult(False, "端口【{}】已被【{}】使用,请更换其他端口".format(
                    get.c_port, installed["service_name"]))

        cpres = self.check_port(get)
        if not cpres["status"]: return cpres

        if int(get.allow_access) == 1:
            # 2024/4/18 上午10:21 添加端口到系统防火墙
            from firewallModel.comModel import main as comModel
            firewall_com = comModel()
            get.port = get.c_port
            firewall_com.set_port_rule(get)

        get.port_list.append(get.c_port)
        self.app_info.append({
            "fieldKey": "web_http_port",
            "fieldTitle": "Web端口",
            "fieldValue": 8123,
        })
        self.app_info.append({
            "fieldKey": "access_url",
            "fieldTitle": "访问地址",
            "fieldValue": "http://{}:{}".format(public.GetLocalIp(), get.c_port),
        })

        return public.returnResult(True, "更新Homeassistant配置成功")

    # 2024/8/28 下午12:13 设置openvpn前置处理
    def set_openvpn_conf(self, get):
        '''
            @name
        '''
        cmd = ("nohup echo '正在启动,可能需要等待1-5分钟以上...' >> {app_cmd_log};"
               "docker pull kylemanna/openvpn >> {app_cmd_log} 2>&1;"
               "docker run -v {service_path}/openvpn:/etc/openvpn --rm kylemanna/openvpn ovpn_genconfig -u udp://{server_ip} >> {app_cmd_log} 2>&1;"
               "docker run -v {service_path}/openvpn:/etc/openvpn --rm -e EASYRSA_BATCH=1 -e EASYRSA_REQ_CN=OpenVPN_Server kylemanna/openvpn ovpn_initpki nopass >> {app_cmd_log} 2>&1;"
               "docker run -v {service_path}/openvpn:/etc/openvpn --rm -e EASYRSA_BATCH=1 -e EASYRSA_REQ_CN=OpenVPN_Server kylemanna/openvpn easyrsa build-client-full {service_name} nopass >> {app_cmd_log} 2>&1;"
               "docker run -v {service_path}/openvpn:/etc/openvpn --rm kylemanna/openvpn ovpn_getclient {service_name} > {service_path}/{service_name}.ovpn;"
               "docker-compose -f {compose_file} up -d >> {app_cmd_log} 2>&1 && "
               "echo 'bt_successful' >> {app_cmd_log} || echo 'bt_failed' >> {app_cmd_log} &"
               ).format(
            service_path=self.service_path,
            server_ip=get.ovpn_server_url,
            service_name=self.service_name,
            app_cmd_log=self.app_cmd_log,
            compose_file=self.compose_file,
        )

        self.set_up_cmd(cmd)
        return public.returnResult(True, "更新Openvpn配置成功")

    def rebuild_mysql_database(self, get):
        try:
            get.db_host = get.service_name
            get.c_port = None
            get.mysql_root_password = None
            get.type = "mysql"
            # 获取已安装的mysql应用信息
            installed_json = self.read_json(self.installed_json_file)

            # 直接找到符合条件的 MySQL 应用
            target_app = next(
                (i for app_list in installed_json.values() for i in app_list
                 if i["service_name"] == get.service_name and i["appname"] == "mysql"),
                None
            )

            if target_app:
                # 找到 MySQL 应用
                # 获取端口
                get.c_port = target_app["port"][0]

                # 直接获取 mysql_root_password
                get.mysql_root_password = next(
                    (info["fieldValue"] for info in target_app["appinfo"] if info["fieldKey"] == "mysql_root_password"),
                    None
                )

            db_sid = self.get_database_sid(get)
            if not db_sid:
                self.apply_database_to_panel(get)
        except Exception as e:
            public.print_log(str(e))

    # 2024/8/1 下午10:12 重建指定app
    def rebuild_app(self, get):
        '''
            @name 重建指定app
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
        command = self.set_type(0).set_path(self.compose_file).get_compose_down()
        public.ExecShell(command)
        command = self.set_type(0).set_path(self.compose_file).get_compose_up_remove_orphans()
        public.ExecShell(command)

        # 处理数据库容器,点击重建    解决远程数据库不存在的问题
        if get.app_name == "mysql":
            self.rebuild_mysql_database(get)

        return public.returnResult(True, "重建成功!")

    # 2024/8/2 上午11:40 获取指定app支持升级的版本
    def update_versions(self, get):
        '''
            @name 获取指定app支持升级的版本
        '''
        get.id = get.get("id", None)
        if get.id is None:
            return public.returnResult(False, "参数错误,请传id参数!")

        installed_json = self.read_json(self.installed_json_file)
        if not installed_json:
            return public.returnResult(True, "暂无已安装的应用!", data=[])

        self.get_apps_json()
        canupdate_version = []
        for app_type in installed_json.keys():
            for i in installed_json[app_type]:

                if i["id"] == get.id:
                    if i["m_version"] in ("main", "latest"):
                        return public.returnResult(True, "暂无可升级版本!", data=[])
                    for app in self.apps_json:
                        if app["appname"] == i["appname"]:
                            for version in app["appversion"]:
                                if version["m_version"] == i["m_version"]:
                                    for sv in version["s_version"]:
                                        if "." in sv:
                                            c_v = float(sv)
                                        else:
                                            c_v = int(sv)

                                        if "." in i["s_version"]:
                                            i_v = float(i["s_version"])
                                        else:
                                            i_v = int(i["s_version"])

                                        if c_v > i_v:
                                            canupdate_version.append({
                                                "m_version": version["m_version"],
                                                "s_version": sv,
                                                "version": "{}.{}".format(version["m_version"], sv)
                                            })

                                    if len(canupdate_version) == 0:
                                        return public.returnResult(True, "暂无可升级版本!", data=[])
                                    return public.returnResult(True, data=canupdate_version)

        return public.returnResult(False, "未找到指定应用!")

    # 2024/8/1 下午4:20 更新指定app
    def update_app(self, get):
        '''
            @name 更新指定app
        '''
        installed_json = self.read_json(self.installed_json_file)
        if not installed_json:
            return public.returnResult(False, "暂无已安装的应用!")

        get.id = get.get("id", None)
        if get.id is None:
            return public.returnResult(False, "参数错误,请传id参数!")

        get.m_version = get.get("m_version", None)
        if get.m_version is None:
            return public.returnResult(False, '参数错误,请传m_version参数!')

        get.s_version = get.get("s_version", None)
        if get.s_version is None:
            return public.returnResult(False, '参数错误,请传s_version参数!')

        self.app_version = "{}.{}".format(get.m_version, get.s_version)

        get.backup = get.get("backup", False)
        if type(get.backup) != bool:
            if get.backup == "false":
                get.backup = False
            else:
                get.backup = True
        if get.backup: self.backup_app(get)

        for app_type in installed_json.keys():
            for i in installed_json[app_type]:
                if i["id"] == get.id:
                    if i["m_version"] != get.m_version:
                        return public.returnResult(False, "只能选择大版本相同的版本号进行更新!")
                    if "." in i["s_version"]:
                        if float(i["s_version"]) == float(get.s_version):
                            return public.returnResult(False, "当前应用已是最新版本,无需更新!")
                        if float(i["s_version"]) > float(get.s_version):
                            return public.returnResult(False, "只能选择比原版本高的版本号进行更新!")
                    else:
                        if int(i["s_version"]) == int(get.s_version):
                            return public.returnResult(False, "当前应用已是最新版本,无需更新!")
                        if int(i["s_version"]) > int(get.s_version):
                            return public.returnResult(False, "只能选择比原版本高的版本号进行更新!")

                    self.set_service_name(i["service_name"])
                    self.set_app_name(i["appname"])
                    self.set_app_path()
                    self.set_service_path()
                    self.set_compose_file()
                    self.down_app()
                    get.pull = get.get("pull", False)
                    if get.pull: self.pull_app()

                    public.ExecShell(
                        "sed -i 's/^VERSION=.*/VERSION={}/' {}/.env".format(self.app_version, self.service_path))
                    command = self.set_type(0).set_path(self.compose_file).get_compose_up_remove_orphans()
                    public.ExecShell(command)

                    i["m_version"] = get.m_version
                    i["s_version"] = get.s_version
                    i["version"] = self.app_version
                    i["updateat"] = int(time.time())
                    self.write_json(self.installed_json_file, installed_json)

                    return public.returnResult(True, "更新成功!")

        return public.returnResult(False, "未找到指定应用!")

    # 2024/8/2 下午4:09 忽略指定app的更新
    def ignore_update(self, get):
        '''
            @name 忽略指定app的更新
        '''
        pass

    # 2024/8/6 上午9:07 获取依赖应用安装情况
    def get_dependence_apps(self, get):
        '''
            @name 获取依赖应用安装情况
        '''
        get.depend_app = get.get("depend_app", None)
        if get.depend_app is None:
            return public.returnResult(False, "参数错误,请传depend_app参数!")

        if type(get.depend_app) == str:
            get.depend_app = json.loads(get.depend_app)

        installed_json = self.read_json(self.installed_json_file)
        if not installed_json:
            return public.returnResult(True, "暂无已安装的应用!", data=[])

        installed_databases = []
        for depend_app in get.depend_app:
            tmp = {"appname": depend_app["app_name"], "app_type": depend_app["app_type"], "installed": []}

            for app_type in installed_json.keys():
                if app_type == depend_app["app_type"]:
                    for i in installed_json[app_type]:
                        if i["appname"] == depend_app["app_name"]:
                            installed_dep = {
                                "service_name": i["service_name"],
                                "version": i["version"]
                            }
                            if installed_dep not in tmp["installed"]:
                                tmp["installed"].append(installed_dep)

            installed_databases.append(tmp)
            del tmp

        return self.pageResult(True, data=installed_databases)

    # 2024/8/5 下午4:03 获取指定app的日志
    def get_app_log(self, get):
        '''
            @name 获取指定app的日志
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
        command = self.set_type(0).set_path(self.compose_file).set_tail("500").get_tail_compose_log()
        stdout, stderr = public.ExecShell(command)
        return public.returnResult(True, data=stdout)

    # 2024/8/6 下午4:14 获取指定应用的安装日志
    def get_app_installed_log(self, get):
        '''
            @name 获取指定应用的安装日志
        '''
        get.service_name = get.get("service_name", None)
        if get.service_name is None:
            return public.returnResult(False, "参数错误,请传service_name参数!")

        self.set_service_name(get.service_name)
        self.set_cmd_log()
        if not os.path.exists(self.app_cmd_log):
            return public.returnResult(True, data="")

        return public.returnResult(True, data=public.readFile(self.app_cmd_log))

    # 2024/8/1 下午4:22 备份指定应用
    def backup_app(self, get):
        '''
            @name 备份指定应用
        '''
        installed_json = self.read_json(self.installed_json_file)
        if not installed_json:
            return public.returnResult(False, "暂无已安装的应用!")

        get.id = get.get("id", None)
        if get.id is None:
            return public.returnResult(False, "参数错误,请传id参数!")

        for app_type in installed_json.keys():
            for i in installed_json[app_type]:
                if i["id"] == get.id:
                    self.set_service_name(i["service_name"])
                    self.set_service_backup_path()
                    backup_conf = self.backup_conf.copy()
                    backup_conf["backup_path"] = self.service_backup_path
                    backup_conf["backup_time"] = str(int(time.time()))
                    backup_conf["file_name"] = "{}_{}.tar.gz".format(i["service_name"], backup_conf["backup_time"])

                    if not os.path.exists(self.service_backup_path):
                        os.makedirs(self.service_backup_path, exist_ok=True, mode=0o755)

                    public.ExecShell(
                        "cp -r {} {}".format(os.path.join(i["path"], i["service_name"]), self.service_backup_path))
                    public.ExecShell("cd {service_backup_path} && tar -zcf {file_name} {i_name} ".format(
                        service_backup_path=self.service_backup_path,
                        file_name=backup_conf["file_name"],
                        i_name=i["service_name"]))

                    if os.path.exists("{}/{}".format(self.service_backup_path, backup_conf["file_name"])):
                        if (os.path.getsize("{}/{}".format(self.service_backup_path, backup_conf["file_name"])) == 0 or
                                os.path.getsize(
                                    "{}/{}".format(self.service_backup_path, backup_conf["file_name"])) < 10):
                            public.ExecShell("rm -f {}/{}".format(self.service_backup_path, backup_conf["file_name"]))
                            return public.returnResult(False, "备份失败!")
                    else:
                        return public.returnResult(False, "备份失败!")

                    public.ExecShell("rm -rf {}".format(os.path.join(self.service_backup_path, i["service_name"])))
                    backup_conf["size"] = os.path.getsize(
                        "{}/{}".format(self.service_backup_path, backup_conf["file_name"]))

                    backup_json = self.read_json(self.backup_json_file)
                    if backup_json:
                        if i["id"] in backup_json.keys():
                            backup_json[i["id"]].append(backup_conf)
                        else:
                            backup_json[i["id"]] = [backup_conf]
                    else:
                        backup_json = {i["id"]: [backup_conf]}
                    self.write_json(self.backup_json_file, backup_json)

                    return public.returnResult(True, "备份成功!")

        return public.returnResult(False, "未找到指定应用!")

    # 2024/8/1 下午6:05 获取备份列表
    def get_backup_list(self, get):
        '''
            @name 获取备份列表
        '''
        backup_json = self.read_json(self.backup_json_file)
        if not backup_json:
            page_data = self.get_page([], get)
            return self.pageResult(True, data=page_data["data"], page=page_data["page"])

        get.id = get.get("id", None)
        if get.id is None:
            return public.returnResult(False, "参数错误,请传id参数!")

        if not get.id in backup_json.keys():
            page_data = self.get_page([], get)
            return self.pageResult(True, data=page_data["data"], page=page_data["page"])

        page_data = self.get_page(backup_json[get.id], get)
        # 2025/1/6 15:20 时间倒序
        page_data["data"] = sorted(page_data["data"], key=lambda x: x["backup_time"], reverse=True)
        return self.pageResult(True, data=page_data["data"], page=page_data["page"])

    # 2024/8/1 下午6:19 删除备份
    def delete_backup(self, get):
        '''
            @name 删除备份
        '''
        backup_json = self.read_json(self.backup_json_file)
        if not backup_json:
            return public.returnResult(False, "暂无备份数据!")

        get.id = get.get("id", None)
        if get.id is None:
            return public.returnResult(False, "参数错误,请传id参数!")

        get.file_name = get.get("file_name", None)
        if get.file_name is None:
            return public.returnResult(False, "参数错误,请传file_name参数!")

        if not get.id in backup_json.keys():
            return public.returnResult(False, "未找到指定应用!")

        for i in backup_json[get.id]:
            if i["file_name"] == get.file_name:
                public.ExecShell("rm -f {}/{}".format(i["backup_path"], i["file_name"]))
                backup_json[get.id].remove(i)
                self.write_json(self.backup_json_file, backup_json)
                return public.returnResult(True, "删除成功!")

        return public.returnResult(False, "未找到指定备份!")

    # 2024/8/1 下午8:31 恢复备份
    def restore_backup(self, get):
        '''
            @name 恢复备份
        '''
        backup_json = self.read_json(self.backup_json_file)
        if not backup_json:
            return public.returnResult(False, "暂无备份数据!")

        get.id = get.get("id", None)
        if get.id is None:
            return public.returnResult(False, "参数错误,请传id参数!")

        installed_json = self.read_json(self.installed_json_file)
        if not installed_json:
            return public.returnResult(False, "暂无已安装的应用!")

        get.file_name = get.get("file_name", None)
        if get.file_name is None:
            return public.returnResult(False, "参数错误,请传file_name参数!")

        get.backup = get.get("backup", False)
        if type(get.backup) != bool:
            if get.backup == "false":
                get.backup = False
            else:
                get.backup = True
        if get.backup: self.backup_app(get)

        for i in backup_json[get.id]:
            if not os.path.exists("{}/{}".format(i["backup_path"], i["file_name"])):
                return public.returnResult(False, "备份文件不存在!")
            if os.path.getsize("{}/{}".format(i["backup_path"], i["file_name"])) < 10:
                return public.returnResult(False, "备份文件异常!")

            for app_type in installed_json.keys():
                for j in installed_json[app_type]:
                    if j["id"] == get.id:
                        self.set_service_name(j["service_name"])
                        self.service_path = os.path.join(j["path"], j["service_name"])
                        self.set_app_name(j["appname"])
                        self.set_compose_file()
                        self.down_app()
                        public.ExecShell("rm -rf {}".format(self.service_path))
                        public.ExecShell("cp -r {}/{} {}".format(i["backup_path"], get.file_name, j["path"]))
                        public.ExecShell("cd {} && tar -zxf {}".format(j["path"], get.file_name))
                        self.start_app(get)
                        return public.returnResult(True, "恢复成功!")

            return public.returnResult(False, "111应用不存在!")
        return public.returnResult(False, "未找到指定备份!")

    # 2024/8/1 下午9:25 上传备份文件到备份目录
    def upload_backup(self, get):
        '''
            @name 上传备份文件到备份目录
        '''
        get.id = get.get("id", None)
        if get.id is None:
            return public.returnResult(False, "参数错误,请传id参数!")
        get.f_path = get.get("f_path/s", None)
        if get.f_path is None:
            return public.returnResult(False, "参数错误,请传f_path参数!")
        get.f_name = get.get("f_name/s", None)
        if get.f_name is None:
            return public.returnResult(False, "参数错误,请传f_name参数!")
        get.file_name = get.f_name
        get.f_size = get.get("f_size/s", None)
        if get.f_size is None:
            return public.returnResult(False, "参数错误,请传f_size参数!")
        get.f_start = get.get("f_start/s", 0)
        get.blob = get.get("blob/s", None)
        if get.blob is None:
            return public.returnResult(False, "参数错误,请传blob参数!")

        get.restore_backup = get.get("restore_backup", False)
        if type(get.restore_backup) != bool:
            if get.restore_backup == "false":
                get.restore_backup = False
            else:
                get.restore_backup = True

        installed_json = self.read_json(self.installed_json_file)
        if not installed_json:
            return public.returnResult(False, "暂无已安装的应用!")

        if os.path.exists(os.path.join(get.f_path, get.f_name)):
            return public.returnResult(False, "存在同名备份文件,如需重新上传请删除同名文件!")

        from files import files
        fileObj = files()

        backup_json = self.read_json(self.backup_json_file)
        for app_type in installed_json.keys():
            for i in installed_json[app_type]:
                if i["id"].strip() == get.id.strip():
                    self.set_service_name(i["service_name"])
                    self.set_service_backup_path()
                    backup_conf = self.backup_conf.copy()
                    backup_conf["backup_path"] = self.service_backup_path
                    backup_conf["backup_time"] = str(int(time.time()))
                    backup_conf["file_name"] = get.f_name
                    backup_conf["size"] = int(get.f_size)

                    get.f_path = self.service_backup_path
                    upload_result = fileObj.upload(get)
                    if type(upload_result) == dict and not upload_result["status"]:
                        return public.returnResult(status=False, msg=upload_result["msg"])

                    get.size = os.path.getsize(os.path.join(self.service_backup_path, get.f_name))
                    if get.size != int(get.f_size):
                        return public.returnResult(status=False, msg="上传文件大小不一致，上传失败!")

                    if not backup_json or not get.id in backup_json.keys():
                        backup_json = {get.id: [backup_conf]}
                        self.write_json(self.backup_json_file, backup_json)
                        if not get.restore_backup:
                            return public.returnResult(True, "备份文件上传成功!")
                        else:
                            return self.restore_backup(get)

                    for i in backup_json[get.id]:
                        if i["file_name"] == get.f_name:
                            i["backup_time"] = str(int(time.time()))
                            self.write_json(self.backup_json_file, backup_json)
                            if not get.restore_backup:
                                return public.returnResult(True, "备份文件上传成功!")
                            else:
                                return self.restore_backup(get)
                    else:
                        backup_json[get.id].append(backup_conf)
                        self.write_json(self.backup_json_file, backup_json)
                        if not get.restore_backup:
                            return public.returnResult(True, "备份文件上传成功!")
                        else:
                            return self.restore_backup(get)

        return public.returnResult(False, "应用不存在!")

    # 2024/8/7 下午3:15 设置app状态
    def set_app_status(self, get):
        '''
            @name 设置app状态
        '''
        get.status = get.get("status", None)
        if get.status is None:
            return public.returnResult(False, "参数错误,请传status参数!")

        if not get.status in ("start", "stop", "restart", "rebuild"):
            return public.returnResult(False, "参数错误,请传start/stop/restart/rebuild参数!")

        # 根据get.status调用对应的方法
        if get.status == "start":
            return self.start_app(get)
        elif get.status == "stop":
            return self.stop_app(get)
        elif get.status == "restart":
            return self.restart_app(get)
        elif get.status == "rebuild":
            return self.rebuild_app(get)

    # 2024/8/1 下午3:40 停止指定compose服务
    def down_app(self):
        '''
            @name 停止指定compose服务
        '''
        command = self.set_type(0).set_path(self.compose_file).get_compose_down()
        public.ExecShell(command)

    # 2024/8/22 下午10:56 后台执行down_app
    def down_app_bg(self):
        '''
            @name 后台执行down_app
        '''
        command = self.set_type(0).set_path(self.compose_file).get_compose_down()
        public.ExecShell(command + " &")

    # 2024/8/1 下午3:33 卸载指定app
    def remove_app(self, get):
        '''
            @name 卸载指定app
        '''
        installed_json = self.read_json(self.installed_json_file)
        if not installed_json:
            return public.returnResult(False, "暂无已安装的应用!")

        get.id = get.get("id", None)
        if get.id is None:
            return public.returnResult(False, "参数错误,请传id参数!")

        get.delete_data = get.get("delete_data", 0)

        for app_type in installed_json.keys():
            for i in installed_json[app_type]:
                if i["id"] == get.id:
                    self.compose_file = os.path.join(i["path"], i["service_name"], "docker-compose.yml")
                    if i["appname"] == "sftpgo":
                        self.down_app_bg()
                    else:
                        self.down_app()
                    if int(get.delete_data) == 1:
                        public.ExecShell("rm -rf {}".format(os.path.join(i["path"], i["service_name"])))
                        if not i["depDataBase"] is None:
                            if i["depDataBase"]["type"] in ("mysql", "mariadb"):
                                self.delete_database_for_app(i["depDataBase"]["db"])
                            elif i["depDataBase"]["type"] in ("postgresql",):
                                self.delete_pgsql_database_for_app(i["depDataBase"]["db"])

                    if i["appname"] in ("mysql", "mariadb", "postgresql"):
                        self.set_service_name(i["service_name"])
                        for appInfo in i["appinfo"]:
                            if appInfo["fieldKey"] == "mysql_port":
                                get.c_port = appInfo["fieldValue"]
                            elif appInfo["fieldKey"] == "mariadb_port":
                                get.c_port = appInfo["fieldValue"]
                            elif appInfo["fieldKey"] == "mysql_root_password":
                                get.mysql_root_password = appInfo["fieldValue"]
                            elif appInfo["fieldKey"] == "mariadb_root_password":
                                get.mariadb_root_password = appInfo["fieldValue"]
                            elif appInfo["fieldKey"] == "postgres_password":
                                get.postgres_password = appInfo["fieldValue"]

                        if i["appname"] == "postgresql":
                            self.delete_pgsql_database_from_panel(get)
                        else:
                            self.delete_database_from_panel(get)

                    if not i["domain"] is None:
                        from mod.project.docker.sites.sitesManage import SitesManage
                        site_manage = SitesManage()

                        get.site_name = i["domain"]
                        res = public.M("docker_sites").where("name=?", (get.site_name,)).find()
                        if not res:
                            public.M("docker_domain").where("name=?", (i["domain"],)).delete()
                        else:
                            get.id = str(res["id"])
                            get.remove_path = get.delete_data
                            res = site_manage.delete_site(get)
                            if not res["status"]: return res

                    installed_json[app_type].remove(i)
                    self.write_json(self.installed_json_file, installed_json)
                    return public.returnResult(True, "卸载成功!")

        return public.returnResult(False, "未找到指定应用!")

    # 2024/8/15 下午4:33 清空所有已装应用
    def remove_all_installed(self, get):
        '''
            @name 清空所有已装应用
        '''
        installed_json = self.read_json(self.installed_json_file)
        if not installed_json:
            return public.returnResult(False, "暂无已安装的应用!")

        get.delete_data = get.get("delete_data", 0)

        for app_type in installed_json.keys():
            for i in installed_json[app_type]:
                self.compose_file = os.path.join(i["path"], i["service_name"], "docker-compose.yml")
                if i["appname"] == "sftpgo":
                    self.down_app_bg()
                else:
                    self.down_app()
                if int(get.delete_data) == 1:
                    public.ExecShell("rm -rf {}".format(os.path.join(i["path"], i["service_name"])))
                    if not i["depDataBase"] is None:
                        if i["depDataBase"]["type"] in ("mysql", "mariadb"):
                            self.delete_database_for_app(i["depDataBase"]["db"])
                        elif i["depDataBase"]["type"] in ("postgresql",):
                            self.delete_pgsql_database_for_app(i["depDataBase"]["db"])

                if i["appname"] in ("mysql", "mariadb", "postgresql"):
                    self.set_service_name(i["service_name"])
                    for appInfo in i["appinfo"]:
                        if appInfo["fieldKey"] == "mysql_port":
                            get.c_port = appInfo["fieldValue"]
                        elif appInfo["fieldKey"] == "mariadb_port":
                            get.c_port = appInfo["fieldValue"]
                        elif appInfo["fieldKey"] == "mysql_root_password":
                            get.mysql_root_password = appInfo["fieldValue"]
                        elif appInfo["fieldKey"] == "mariadb_root_password":
                            get.mariadb_root_password = appInfo["fieldValue"]
                        elif appInfo["fieldKey"] == "postgres_password":
                            get.postgres_password = appInfo["fieldValue"]

                    self.delete_database_from_panel(get)

                if not i["domain"] is None:
                    from mod.project.proxy.comMod import main as proxyMod
                    pMod = proxyMod()
                    get.site_name = i["domain"]
                    res = public.M("sites").where("name=?", (get.site_name,)).find()
                    if not res:
                        public.M("domain").where("name=?", (i["domain"],)).delete()
                    else:
                        get.id = str(res["id"])
                        res = pMod.delete(get)
                        # if not res["status"]: return res

        public.ExecShell("rm -f {}".format(self.installed_json_file))

    # 2024/8/2 下午4:47 获取app列表
    def get_apps(self, get):
        '''
            @name 获取app列表
        '''
        get.force = get.get("force/d", 0)
        if int(get.force) == 1:
            public.ExecShell("rm -f {}".format(self.apps_json_file))
            public.ExecShell("rm -f {}".format(self.app_tags_file))
            public.ExecShell("rm -rf {}".format(self.templates_path))
            public.ExecShell("rm -f {}".format(self.ollama_online_models_file))
            self.download_apps_json()
            self.update_ico()
        self.get_apps_json()
        if self.apps_json is None:
            return public.returnResult(False, "应用分类获取失败，请点击右上角【更新应用列表】")

        from mod.project.docker.app.base import App
        cbnet = App().check_baota_net()
        if not cbnet["status"]: return cbnet

        get.app_type = get.get("app_type", "all")
        # if get.app_type != "all" and not get.app_type in self.types:
        #     return public.returnResult(False, "应用类型错误,请传入：{}!".format(",".join(self.types)))
        get.row = 20000

        import re
        query = get.get("query", None)
        if query:
            pattern = re.compile(
                rf'.*{{}}.*'.format(re.escape(query)),
                flags=re.IGNORECASE
            )
        else:
            # 无查询时直接匹配所有
            pattern = re.compile(rf'^.*$', flags=re.IGNORECASE)

        installed_json = self.read_json(self.installed_json_file)

        app_list = []
        from mod.project.docker.apphub.apphubManage import AppHub
        apphub_json = AppHub().get_hub_apps()
        self.apps_json = self.apps_json + apphub_json
        for app in self.apps_json:
            if app["appstatus"] == 0: continue
            app["installedCount"] = 0
            if app["apptype"] == "AI":
                from mod.project.docker.app.gpu.tools import GPUTool
                GPUTool.register_app_gpu_option(app)

            if get.app_type in ("all", app["apptype"],"AppHub"):
                if(get.app_type == "AppHub" and app["appid"] != -1):
                    continue

                # 模糊搜索检查
                match = False
                if (pattern.search(app["appname"]) or
                        pattern.search(app["apptitle"]) or
                        pattern.search(app["appdesc"])):
                    match = True

                if not match:
                    continue  # 不匹配则跳过

                # 计算安装次数
                if not app["reuse"] and installed_json:
                    for i in installed_json[app["apptype"]]:
                        if i["appname"] == app["appname"] and i["appid"] == app["appid"]:
                            app["installedCount"] += 1
                            break
                elif installed_json:
                    if app["apptype"] in installed_json:
                        for i in installed_json[app["apptype"]]:
                            if i["appname"] == app["appname"] and i["appid"] == app["appid"]:
                                app["installedCount"] += 1

                app_list.append(app)

        page_data = self.get_page(app_list, get)
        # 2023/12/6 下午 4:13 获取系统内存，转成MB，为最大可用内存
        import psutil
        mem = psutil.virtual_memory()
        mem = int(mem.total / 1024 / 1024)
        cpu = psutil.cpu_count()
        return self.pageResult(True, data=page_data["data"], page=page_data["page"], mem=mem, cpu=cpu)

    # 2024/8/1 上午10:35 获取已安装的应用列表
    def get_installed_apps(self, get):
        '''
            @name 获取已安装的应用列表
        '''
        installed_json = self.read_json(self.installed_json_file)
        if not installed_json:
            return public.returnResult(True, "暂无已安装的应用!", data=[])

        get.app_type = get.get("app_type", "all")
        if get.app_type != "all" and not get.app_type in self.types:
            return public.returnResult(False, "应用类型错误,请传入：{}!".format(",".join(self.types)))
        if get.app_type != "all" and not get.app_type in installed_json.keys():
            return public.returnResult(True, "暂无已安装的应用!", data=[])
        get.query = get.get("query", None)

        from btdockerModel.dockerSock import container
        sk_container = container.dockerContainer()
        sk_container_list = sk_container.get_container()

        installed_apps = []
        self.get_apps_json()

        if get.app_type == "all":
            for app_type in installed_json.keys():
                type_res = self.structure_installed_apps(app_type, sk_container_list, installed_json, get.query)
                installed_apps.extend(type_res)
        else:
            installed_apps = self.structure_installed_apps(get.app_type, sk_container_list, installed_json, get.query)

        # 按照createTime倒序排序
        installed_apps = sorted(installed_apps, key=lambda x: x["createTime"], reverse=True)
        page_data = self.get_page(installed_apps, get)
        return self.pageResult(True, data=page_data["data"], page=page_data["page"])

    # 2024/8/1 下午4:02 获取指定已安装的应用信息
    def get_installed_app_info(self, get):
        '''
            @name 获取指定已安装的应用信息
        '''
        installed_json = self.read_json(self.installed_json_file)
        if not installed_json:
            return public.returnResult(False, "暂无已安装的应用!")

        get.id = get.get("id", None)
        get.service_name = get.get("service_name", None)
        if get.id is None and get.service_name is None:
            return public.returnResult(False, "参数错误,请传id/service_name参数!")

        for app_type in installed_json.keys():
            for i in installed_json[app_type]:
                if i["id"] == get.id:
                    self.get_apps_json()
                    i["canUpdate"] = 1 if self.check_canupdate(i) else 0
                    return public.returnResult(True, data=i)

                if i["service_name"] == get.service_name:
                    self.get_apps_json()
                    i["canUpdate"] = 1 if self.check_canupdate(i) else 0
                    return public.returnResult(True, data=i)

        return public.returnResult(False, "未找到指定应用!")

    # 2024/8/1 下午4:02 获取指定已安装的应用appinfo json信息
    def get_installed_app_info_j(self, get):
        '''
            @name 获取指定已安装的应用信息
        '''
        installed_json = self.read_json(self.installed_json_file)
        if not installed_json:
            return public.returnResult(False, "暂无已安装的应用!")

        get.id = get.get("id", None)
        get.service_name = get.get("service_name", None)
        if get.id is None and get.service_name is None:
            return public.returnResult(False, "参数错误,请传id/service_name参数!")

        for app_type in installed_json.keys():
            for i in installed_json[app_type]:
                if i["id"] == get.id:
                    self.get_apps_json()
                    i["canUpdate"] = 1 if self.check_canupdate(i) else 0
                    return public.returnResult(True, data=i["appinfo"])

                if i["service_name"] == get.service_name:
                    self.get_apps_json()
                    i["canUpdate"] = 1 if self.check_canupdate(i) else 0
                    return public.returnResult(True, data=i["appinfo"])

        return public.returnResult(False, "未找到指定应用!")

    # 2024/7/30 上午10:38 获取应用分类标签
    def get_tags(self, get):
        if not os.path.exists(self.app_tags_file):
            public.downloadFile(public.get_url() + '/src/dk_app/apps/apptags.json', self.app_tags_file)

        app_tags = self.read_json(self.app_tags_file)
        if not app_tags:
            public.ExecShell("rm -f {}".format(self.app_tags_file))
            public.downloadFile(public.get_url() + '/src/dk_app/apps/apptags.json', self.app_tags_file)
            app_tags = self.read_json(self.app_tags_file)
        if not app_tags:
            return []
        return app_tags


    def client_db_shell(self, get):
        """
        容器执行命令
        :param get:
        :return:
        """
        try:
            if not hasattr(get, "id"):
                return public.returnMsg(False, "缺少参数! id")
            if not hasattr(get, "appname"):
                return public.returnMsg(False, "缺少参数! appname")

            if get.appname.strip() not in ["mysql", "redis", "postgresql", "tdengine"]:
                return public.returnMsg(False, "不支持此应用链接!")

            command = "docker exec -it {}"

            if get.appname == "mysql":
                command = command.format(get.id) + " mysql -uroot -p{} --socket=/tmp/mysql.sock".format(get.password)
            elif get.appname == "redis":
                command = command.format(get.id) + " redis-cli -a {}".format(get.password)
            elif get.appname == "postgresql":
                command = command.format(get.id) + " psql -U postgres"
            elif get.appname == "tdengine":
                command = command.format(get.id) + " taos"

            return public.returnMsg(True, command)
        except Exception as e:
            return public.returnMsg(False, '获取容器失败')

    def get_app_compose(self,get):
        """
        获取应用的docker-compose.yml文件内容
        :param get:
        :return:
        """
        app_name = get.get("app_name", None)
        appid = get.get("appid", None)
        if app_name is None:
            return public.returnResult(False, "参数错误,请传app_name参数!")
        if "." in app_name or "/" in app_name:
            return public.returnResult(False, "应用名称不合法,请勿包含非法字符!")
        if get.get('gpu', 'false') == 'true':
            app_name = app_name+"_gpu"

        if appid == '-1':
            #/www/dk_project/dk_app/apphub/apphub
            compose_path = os.path.join(self.project_path, "apphub", "apphub",app_name,"latest","docker-compose.yml")
            self.app_template_path = compose_path
        else:
            #/www/dk_project/dk_app/templates
            compose_path = os.path.join(self.project_path, "templates", app_name, "docker-compose.yml")
            self.app_template_path = compose_path
            self.check_app_template(get)

        if not os.path.exists(compose_path):
            return public.returnResult(False, "未找到指定应用的docker-compose.yml文件!")

        compose_content = public.readFile(compose_path)
        return public.returnResult(True, data=compose_content)