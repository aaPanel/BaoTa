# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------

# ------------------------------
# Docker模型
# ------------------------------
import public
import os
import time
import json
import re
import projectModel.bt_docker.dk_public as dp
import projectModel.bt_docker.dk_setup as ds
import projectModel.bt_docker.dk_volume as dv


class main:
    compose_path = "{}/data/compose".format(public.get_panel_path())
    project_path = "/www/dk_project"
    templates_path = f"{project_path}/templates"
    config_path = f"{public.get_panel_path()}/config"
    info_path = f"{config_path}/docker_project_info.json"
    __first_pl = f"{project_path}/first.pl"
    log_file = ""

    def __init__(self):
        self.docker_setup = ds.main()
        if not os.path.exists(self.templates_path): os.system(f"mkdir -p {self.templates_path}")
        self.compose_cmd = "/usr/bin/docker-compose" if self.docker_setup.check_docker_program() \
            else "/usr/local/bin/docker-compose"

    def __check_conf(self, filename):
        '''
        验证配置文件是否可执行
        @param filename: docker-compose.yml文件路劲
        @return:
        '''
        return public.ExecShell(f"{self.compose_cmd} -f {filename} config")

    def sync_item(self, get):
        '''
        同步官方可以一键部署的项目
        @param get: 空对象
        @return:
        '''
        os.remove(self.info_path)
        project_info = self.get_project_list(get)
        failed_list = []
        successes_list = []
        for info in project_info["project_info"]:
            if info["server_name"]:
                down_project_yml = self.__download_project_yml(info["server_name"])
                if not down_project_yml["status"]:
                    failed_list.append(info["server_name"])
                    continue
                successes_list.append(info["server_name"])
        data = [{"successes": len(successes_list), "server_name": successes_list},
                {"failed": len(failed_list), "server_name": failed_list}]
        return data

    def __first_sync_item(self, project_info):
        '''
        同步官方可以一键部署的项目
        @param get: 空对象
        @return:
        '''
        failed_list = []
        successes_list = []
        for info in project_info:
            if info["server_name"]:
                down_project_yml = self.__download_project_yml(info["server_name"])
                if not down_project_yml["status"]:
                    failed_list.append(info["server_name"])
                    continue
                successes_list.append(info["server_name"])
        data = [{"successes": len(successes_list), "server_name": successes_list},
                {"failed": len(failed_list), "server_name": failed_list}]
        return data

    def get_project_list(self, get):
        '''
        获取支持一键部署的项目列表
        @param get:
        @return:
        '''
        get.url = "unix:///var/run/docker.sock"
        data = self.__get_docker_status(get)
        try:
            project_info = []
            if not os.path.exists(self.info_path):
                down_info = self.__download_info(self.info_path)
                if not down_info["status"]: return project_info
            project_info = json.loads(public.readFile(self.info_path))
            project_info.sort(key=lambda x: x["sort"])
            if not os.path.exists(self.__first_pl):
                sync_result = self.__first_sync_item(project_info)
                for result in sync_result:
                    if result.get("successes") and result["successes"] <= 0:
                        project_info = []
                        data["project_info"] = project_info
                        return data
                public.ExecShell(f"echo \"first\" > {self.__first_pl}")
        except:
            project_info = []
        data["project_info"] = project_info
        return data

    def __get_docker_status(self, args):
        '''
        获取docker安装和启动状态
        @param args:
        @return:
        '''
        return {
            "installed": self.docker_setup.check_docker_program(),
            "service_status": self.docker_setup.get_service_status()
        }

    def __download_info(self, info_path):
        '''
        下载版本信息: info.json
        @param info_path: string info.json文件的路劲
        @return:
        '''
        url = f"{public.get_url()}/install/lib/docker_project/docker_project_info.json"
        dp.download_file(url, info_path)
        if os.path.exists(info_path):
            return public.returnMsg(True, "info.json下载完成!")
        return public.returnMsg(False, "info.json下载失败!")

    def __download_project_yml(self, server_name):
        '''
        下载指定项目压缩包
        @param server_name: string 模板名称,如nextcloud
        @return:
        '''
        try:
            path = f"{self.templates_path}/{server_name}"
            filename = f"{self.templates_path}/{server_name}.tar.gz"
            compose_file = f"{path}/docker-compose.yml"
            url = f"{public.get_url()}/install/lib/docker_project/templates/{server_name}.tar.gz"
            dp.download_file(url, filename)
            if not os.path.exists(filename):
                return public.returnMsg(False, f"{server_name}下载失败,请重新同步!")
            if os.path.getsize(filename) == 0:
                os.remove(filename)
                return public.returnMsg(False, f"{server_name}下载失败,请重新同步!")
            self.__tar_x_yml(server_name, path, filename)
            if os.path.exists(compose_file):
                check_conf = self.__check_conf(compose_file)
                if check_conf[1]:
                    return public.returnMsg(False, f"{server_name}yml文件测试失败,{check_conf[1]}")
                return public.returnMsg(True, f"{server_name}下载完成!")
        except:
            return public.returnMsg(False, f"{server_name}下载失败,请重新同步!")

    def __tar_x_yml(self, server_name, path=None, filename=None):
        '''
        解压项目模板方法
        @param server_name: 模板名称,如nextcloud
        @param path: 项目模板路劲,如/www/dk_project/templates/nextcloud
        @param filename: 项目模板压缩包,如/www/dk_project/templates/nextcloud.tar.gz
        @return:
        '''
        tar_result = public.ExecShell(f"tar xvf {filename} -C {self.templates_path}")
        if tar_result[1]:
            os.remove(path)
            os.remove(filename)
            return public.returnMsg(False, f"{server_name}解压失败")
        return public.returnMsg(True, f"{server_name}解压成功")

    def create_project_volume(self, server_name, project_name, dir_names, volume_path):
        '''
        创建指定项目的数据存储卷
        @param volume_path:
        @param project_name: string
        @param dir_names: list [dir_name,dir_name,...]
        @return:
        '''
        args = public.dict_obj()
        args.url = "unix:///var/run/docker.sock"
        # volumes = dv.main().get_volume_list(args)
        # {'status': True, 'msg': {'volume': [], 'installed': True, 'service_status': True}}
        # if volumes['status']:
        #     volumes = volumes['msg']['volume']
        # else:
        #     volumes = list()
        # volume的值,一个list: []
        for dir_name in dir_names:
            # # 如果已经存在就跳过
            # for volume in volumes:
            #     if dir_name == volume["Name"]:
            #         continue
            if volume_path == "":
                path = f"{self.project_path}/projects/{project_name}/data/{dir_name}"
            else:
                path = f"{volume_path}/data/{dir_name}"
            is_mkdir = public.ExecShell(f"mkdir -p {path}")
            if is_mkdir[1]: return public.returnMsg(False, f"目录创建失败,原因如下: {is_mkdir[1]}")
            args.name = f"{project_name}_{server_name}_{dir_name}"
            args.driver = "local"
            args.driver_opts = {'type': 'none', 'device': path, 'o': 'bind'}
            args.labels = {}
            dv.main().add(args)
        return public.returnMsg(True, "存储卷已创建完成")

    def get_project(self, get):
        '''
        获取指定一键部署项目的配置信息
        @param get: get.server_name
        @return:
        '''
        try:
            server_name = getattr(get, "server_name")
            info_path = f"{self.templates_path}/{server_name}/conf.json"
            project_info = json.loads(public.readFile(info_path))
            volume_placeholder = f"默认: {self.project_path}/projects/您的项目名称/data/"
            total_sum = len(project_info)
            volume_path = {"id": total_sum + 1, "sort": total_sum + 1, "type": "string",
                           "key": "VOLUME_PATH", "value": "", "placeholder": volume_placeholder,
                           "ps": "数据存储目录"}
            project_info.append(volume_path)
        except:
            project_info = []
        return project_info

    def __get_server_ps(self, project_conf, conf_key):
        '''
        获取对应服务名的标题
        @param project_conf:
        @param conf_key:
        @return:
        '''
        get = public.dict_obj()
        for conf in project_conf:
            if conf["key"] == "SERVER_NAME":
                get.server_name = conf["value"]
        server_conf = self.get_project(get)
        for server in server_conf:
            if conf_key == server["key"]:
                return server["ps"]
        return conf_key

    def get_logs(self, get):
        '''
        获取项目部署日志
        @param get:
        @return:
        '''
        try:
            import files
            return public.returnMsg(True, files.files().GetLastLine(log_file, 20))
        except:
            return public.returnMsg(True, '\n' * 20)

    def create_project(self, get):
        '''
        创建一键部署的项目
        @param get: dict_obj {dk_def_name:create_project
                                dk_model_name:project
                                data:{"project_conf":[{"key":"server_name","value":"nextcloud","ps":"网盘"},{"key":"PORT","value":"8180","ps":"端口"},{"key":"PROJECT_NAME","value":"wzznb","ps":"项目名称"},{"key":"DB_ROOT_PASS","value":"bt_nextcloud","ps":"数据库root密码"},{"key":"DB_NAME","value":"nextcloud","ps":"数据库名"},{"key":"DB_PASS","value":"bt_nextcloud","ps":"数据库密码"},{"key":"DB_USER","value":"nextcloud","ps":"数据库用户"},{"key":"VOLUME_PATH","value":"默认路劲: /www/dk_project/您的项目名称/data/","ps":"数据存储目录"},{"key": "VOLUMES","value": ["nextcloud","db"],"ps": "需要挂载的数据卷名"}],"dk_model_name":"project","dk_def_name":"create_project"}
                                }
        @return:
        '''
        project_conf = getattr(get, "project_conf")
        remark = ""
        for conf in project_conf:
            if conf["key"] != "REMARK" and type(conf["value"]) != list:
                if re.search('\s', conf["value"]):
                    server_ps = self.__get_server_ps(project_conf, conf["key"])
                    return public.returnMsg(False, f"{server_ps}不能存在空格")
            if conf["key"] != "VOLUME_PATH" and conf["key"] != "REMARK":
                if conf["value"] == "":
                    server_ps = self.__get_server_ps(project_conf, conf["key"])
                    return public.returnMsg(False, f"{server_ps}不能为空!")
            if conf["key"].upper() == "PROJECT_NAME": project_name = conf["value"].strip()
            if conf["key"].upper() == "VOLUME_PATH": project_volume = conf["value"].strip()
            if conf["key"].upper() == "SERVER_NAME": server_name = conf["value"].strip()
            if conf["key"].upper() == "VOLUMES":  # VOLUMES = list
                volumes = conf["value"]
            if conf["key"].upper() == "PORT":
                if dp.check_socket(conf["value"]):
                    return public.returnMsg(False,
                                            f"服务器端口[{conf['value']}]已被占用，请更换为其他端口！")
                project_port = conf["value"]
            if conf["key"] == "REMARK": remark = conf["value"]
        config_path = "{}/config/name_map.json".format(public.get_panel_path())
        if not os.path.exists(config_path):
            public.writeFile(config_path, json.dumps({}))
        if public.readFile(config_path) == '':
            public.writeFile(config_path, json.dumps({}))
        name_map = json.loads(public.readFile(config_path))
        name_str = 'q18q' + public.GetRandomString(10).lower()
        name_map[name_str] = project_name
        project_name = name_str
        public.writeFile(config_path, json.dumps(name_map))
        server_dir = f"{self.templates_path}/{server_name}"
        project_dir = f"{self.project_path}/projects/{project_name}/{project_name}_{server_name}"
        public.set_module_logs('docker_project', 'create_project', 1)
        check_result = self.__create_dir(project_dir, project_name, server_name, server_dir)
        if not check_result["status"]: return check_result
        self.__write_config(project_dir, project_name, server_name, project_conf)
        self.create_project_volume(server_name, project_name, volumes, project_volume)
        run_result = self.__project_run(project_dir, project_name)
        if run_result["status"]:
            self.__add_sql(project_dir, project_name, server_name, remark)
            dp.write_log(f"一键部署项目 [{server_name}] 成功!")
            return self.__return_msg(project_port)
        return run_result

    def __project_run(self, project_dir, project_name):
        '''
        运行项目
        @param project_dir: 项目运行目录
        @param server_name: 服务名称
        @return:
        '''
        global log_file
        log_file = f"{project_dir}/{project_name}_run.log"
        filename = f"{project_dir}/docker-compose.yml"
        check_result = self.__check_conf(filename)
        if check_result[1]:
            return public.returnMsg(False, f"项目启动失败{check_result[1]}")
        run_result = public.ExecShell(f"cd {project_dir} && {self.compose_cmd} up -d 2>&1 | tee "
                                      f"-a {log_file}")
        if run_result[1]:
            if "failed" not in run_result[1]:
                return public.returnMsg(True, f"创建成功")
            return public.returnMsg(False, f"项目启动失败,原因如下:{run_result[1]}")
        return public.returnMsg(True, f"创建成功")

    def __create_dir(self, project_dir, project_name, server_name, server_dir):
        '''
        创建项目目录
        @param project_dir: 项目目录
        @param project_name: 项目名称
        @param server_dir: 服务源目录
        @return:
        '''
        if self.__check_repeat(project_dir, project_name, server_name):
            return public.returnMsg(False, f"{project_name}已存在,请更换项目名称")
        mk_result = public.ExecShell(f"mkdir -p {project_dir}")
        if mk_result[1]: return public.returnMsg(False,
                                                 f"用户项目目录创建失败,详情: {mk_result[1]}")
        cp_result = public.ExecShell(f"cp -a {server_dir}/. {project_dir}/")
        if cp_result[1]: return public.returnMsg(False, f"项目目录复制失败,详情: {cp_result[1]}")
        return public.returnMsg(True, "")

    def __add_sql(self, project_dir, project_name, server_name, remark):
        '''
        添加项目到docker数据库中
        @param project_dir: 项目路劲
        @param project_name: 项目名称
        @return:
        '''
        pdata = {
            "name": public.xsssec(f"{project_name}_{server_name}"),
            "status": "1",
            "path": f"{project_dir}/docker-compose.yml",
            "template_id": "",
            "time": time.time(),
            "remark": public.xsssec(remark)
        }
        dp.sql("stacks").insert(pdata)

    def __return_msg(self, project_port):
        '''
        创建成功后返回给用户的数据
        @param project_port:
        @return:
        '''
        server_ip = public.get_server_ip()
        local_ip = public.GetLocalIp()
        data = {"protocol": "http", "server_ip": server_ip, "local_ip": local_ip,
                "port": project_port}
        return public.returnMsg(True, data)

    def __check_repeat(self, project_dir, project_name, server_name):
        '''
        检查是否存在相同项目
        @param project_dir: 项目路劲
        @return:
        '''
        # if os.path.exists(project_dir):
        #     return True
        stacks_info = dp.sql("stacks").where("name=?", (f"{project_name}_{server_name}",)).find()
        if stacks_info:
            return True
        return False

    def __write_config(self, project_dir, project_name, server_name, project_conf):
        '''
        写配置文件
        @param project_dir: 用户项目目录
        @param project_name: 项目名称
        @param server_name: 服务名称，如nextcloud
        @param project_conf: 新的配置文件内容
        @return:
        '''
        old_env_path = f"{self.templates_path}/{server_name}/.env"
        new_env_path = f"{project_dir}/.env"
        env_conf = ""
        if not os.path.exists(old_env_path):
            public.ExecShell(f"echo > {old_env_path}")
        with open(old_env_path) as env:
            lines = env.readlines()
        # 取旧文件转字典
        old_dict = {}
        for line in lines:
            if "=" in line:
                temp = line.split("=")
                old_dict[temp[0]] = temp[1]
        # 新数据转字典
        new_dict = {}
        for conf in project_conf:
            if conf["key"] == "VOLUME_PATH":
                project_volume = conf["value"]
                if "默认路劲" in project_volume:
                    conf["value"] = f"{self.project_path}/{project_name}/data/"
                continue
            if conf["key"] == "VOLUMES": continue
            new_dict[conf["key"].upper()] = conf["value"]
        # 旧字典更新新字典的内容
        old_dict.update(new_dict)
        # 拼接成新的环境变量文件
        for key, value in old_dict.items():
            env_conf += f"{key}={value.strip()}\n"
        # info_path = f"{project_dir}/conf.json"
        # public.writeFile(info_path, json.dumps(project_conf))
        public.writeFile(new_env_path, env_conf)
        return True

    def sync_compose_template(self, server_name):
        '''
        同步模板到项目模板页面
        @param server_name: 模板名称
        @return:
        '''
        data = dp.sql("templates").where("name=?", (server_name,)).find()
        # if data: dp.sql("templates").delete(id=data["id"])
        if data: return
        pdata = {
            "name": server_name,
            "remark": "仅限堡塔Docker快速部署项目使用的模板[勿删勿单独使用来创建项目]",
            "path": f"{self.templates_path}/{server_name}/docker-compose.yml"
        }
        dp.sql("templates").insert(pdata)
        dp.write_log("Add template [{}] successful!".format(server_name))
