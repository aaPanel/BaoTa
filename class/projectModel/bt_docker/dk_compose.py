# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: zouhw <zhw@bt.cn>
# -------------------------------------------------------------------

# ------------------------------
# Docker模型
# ------------------------------
import public
import os
import time
import projectModel.bt_docker.dk_public as dp
import projectModel.bt_docker.dk_container as dc
import projectModel.bt_docker.dk_setup as ds
import json


class main:
    compose_path = "{}/data/compose".format(public.get_panel_path())
    __log_file = "/tmp/dockertmp.log"

    # 验证配置文件
    def check_conf(self, path):
        shell = "/usr/bin/docker-compose -f {} config".format(path)
        a, e = public.ExecShell(shell)
        if e:
            return public.returnMsg(False, "检测失败: {}".format(e))
        return public.returnMsg(True, "检测通过!")

    # 用引导方式创建模板
    def add_template_gui(self, args):
        """
        用引导方式创建模板
        :param name                     模板名
        :param description              模板描述
        :param data                     模板内容 {"version":3,"services":{...}...}
        :param args:
        模板文件参数：
        version 2/3version
            2: 仅支持单机
            3：支持单机和多机模式
        services:
            多个容器的集合
            下一层执行服务名
            如web1,服务名下面指定服务的变量
            web1:
                build: .                    基于dockerfile构建一个镜像
                image: nginx                服务所使用的镜像为nginx
                container_name: "web"       容器名
                depends_on:                 该服务在db服务启动后再启动
                  - db
                ports:
                  - "6061:80"               将容器的80端口映射到主机的6061端口
                networks:
                  - frontend                该容器所在的网络
                deploy:                     指定与部署和运行服务相关的配置(在使用 swarm时才会生效)
                  replicas: 6               6个副本
                  update_config:
                    parallelism: 2
                    delay: 10s
                  restart_policy:
                    condition: on-failure
        其他详细描述可以参考 https://docs.docker.com/compose/compose-file/compose-file-v3
        :return:
        """
        import yaml
        path = "{}/template".format(self.compose_path)
        file = "{}/{}.yaml".format(path, args.name)
        if not os.path.exists(path):
            os.makedirs(path)
        data = json.loads(args.data)
        yaml.dump(data, file)

    def get_template_kw(self, args):
        data = {
            "version": "",
            "services": {
                "server_name_str": {  # 用户输入
                    "build": {
                        "context": "str",
                        "dockerfile": "str",
                        "args": [],
                        "cache_from": [],
                        "labels": [],
                        "network": "str",
                        "shm_size": "str",
                        "target": "str"
                    },
                    "cap_add": "",
                    "cap_drop": "",
                    "cgroup_parent": "str",
                    "command": "str",
                    "configs": {
                        "my_config_str": []
                    },
                    "container_name": "str",
                    "credential_spec": {
                        "file": "str",
                        "registry": "str"
                    },
                    "depends_on": [],
                    "deploy": {
                        "endpoint_mode": "str",
                        "labels": {
                            "key": "value"
                        },
                        "mode": "str",
                        "placement": [{"key": "value"}],
                        "max_replicas_per_node": "int",
                        "replicas": "int",
                        "resources": {
                            "limits": {
                                "cpus": "str",
                                "memory": "str",
                            },
                            "reservations": {
                                "cpus": "str",
                                "memory": "str",
                            },
                            "restart_policy": {
                                "condition": "str",
                                "delay": "str",
                                "max_attempts": "int",
                                "window": "str"
                            }
                        }
                    }
                }
            }
        }

    # 创建项目配置文件
    def add_template(self, args):
        """
        添加一个模板文件
        :param name                     模板名
        :param remark              模板描述
        :param data                     模板内容
        :param args:
        :return:
        """
        import re
        name = args.name
        if not re.search(r"^[\w\.\-]+$", name):
            return public.returnMsg(False, "模板名不能包含特殊字符，仅支持字母、数字、下划线、点、中划线")
        template_list = self.template_list(args)['msg']['template']
        for template in template_list:
            if name == template['name']:
                return public.returnMsg(False, "此模版名已经存在！")
        path = "{}/{}/template".format(self.compose_path, name)
        file = "{}/{}.yaml".format(path, name)
        if not os.path.exists(path):
            os.makedirs(path)
        public.writeFile(file, args.data)
        check_res = self.check_conf(file)
        if not check_res['status']:
            if os.path.exists(file):
                os.remove(file)
            # return public.returnMsg(False,"模板验证失败，可能是格式错误！")
            return check_res
        pdata = {
            "name": name,
            "remark": public.xsssec(args.remark),
            "path": file
        }
        dp.sql("templates").insert(pdata)
        dp.write_log("Add template [{}] successful!".format(name))
        public.set_module_logs('docker', 'add_template', 1)
        return public.returnMsg(True, "模板添加成功!")

    def edit_template(self, args):
        """
        :param id 模板id
        :param data 模板内容
        :param remark              模板描述
        :param args:
        :return:
        """
        template_info = dp.sql("templates").where("id=?", (args.id,)).find()
        if not template_info:
            return public.returnMsg(False, "没有找改该模版！")
        public.writeFile(template_info['path'], args.data)
        check_res = self.check_conf(template_info['path'])
        if not check_res['status']:
            return check_res
        pdata = {
            "name": args.name,
            "remark": public.xsssec(args.remark),
            "path": template_info['path']
        }
        dp.sql("templates").where("id=?", (args.id,)).update(pdata)
        dp.write_log("编辑模板 [{}] 成功!".format(template_info['name']))
        return public.returnMsg(True, "修改模板成功！")

    def get_template(self, args):
        """
        id 模板ID
        获取模板内容
        :return:
        """
        template_info = dp.sql("templates").where("id=?", (args.id,)).find()
        if not template_info:
            return public.returnMsg(False, "没有找到此模板!")
        return public.returnMsg(True, public.readFile(template_info['path']))

    def template_list(self, args):
        """
        获取所有模板
        :param args:
        :return:
        """
        import projectModel.bt_docker.dk_setup as ds
        docker_setup = ds.main()
        template = dp.sql("templates").select()[::-1]
        if not isinstance(template, list):
            template = []
        data = {
            "template": template,
            "installed": docker_setup.check_docker_program(),
            "service_status": docker_setup.get_service_status()
        }
        return public.returnMsg(True, data)

    def remove_template(self, args):
        """
        删除模板
        :param template_id
        :param args:
        :return:
        """
        data = dp.sql("templates").where("id=?", (args.template_id,)).find()
        if not data:
            return public.returnMsg(False, "没有找到此模板!")
        if os.path.exists(data['path']):
            os.remove(data['path'])
        dp.sql("templates").delete(id=args.template_id)
        dp.write_log("删除模板 [{}] 成功!".format(data['name']))
        return public.returnMsg(True, "删除成功!")

    def edit_project_remark(self, args):
        """
        编辑项目
        :param project_id 项目
        :param remark备注
        :param args:
        :return:
        """
        stacks_info = dp.sql("stacks").where("id=?", (args.project_id,)).find()
        if not stacks_info:
            return public.returnMsg(False, "没有找到该项目！")
        pdata = {
            "remark": public.xsssec(args.remark)
        }
        dp.write_log("项目 [{}] 的备注修改成功 [{}] --> [{}]!".format(stacks_info['name'], stacks_info['remark'],
                                                                      public.xsssec(args.remark)))
        dp.sql("stacks").where("id=?", (args.project_id,)).update(pdata)

    def edit_template_remark(self, args):
        """
        编辑项目
        :param templates_id 项目
        :param remark备注
        :param args:
        :return:
        """
        stacks_info = dp.sql("templates").where("id=?", (args.templates_id,)).find()
        if not stacks_info:
            return public.returnMsg(False, "没有找到该模版！")
        pdata = {
            "remark": public.xsssec(args.remark)
        }
        dp.write_log("修改模板 [{}] 备注成功 [{}] --> [{}]!".format(stacks_info['name'], stacks_info['remark'],
                                                                    public.xsssec(args.remark)))
        dp.sql("templates").where("id=?", (args.templates_id,)).update(pdata)

    def create_project_in_path(self, name, path):
        shell = "cd {} && /usr/bin/docker-compose -p {} up -d &> {}".format("/".join(path.split("/")[:-1]), name,
                                                                            self.__log_file)
        public.ExecShell(shell)

    def create_project_in_file(self, project_name, file):
        project_path = "{}/{}".format(self.compose_path, project_name)
        project_file = "{}/docker-compose.yaml".format(project_path)
        if not os.path.exists(project_path):
            os.makedirs(project_path)
        template_content = public.readFile(file)
        public.writeFile(project_file, template_content)
        shell = "/usr/bin/docker-compose -p {} -f {} up -d &> {}".format(project_name, project_file, self.__log_file)
        public.ExecShell(shell)

    def check_project_container_name(self, template_data, args):
        """
        检测模板文件中的容器名是否已经存在
        :return:
        """
        import re
        import projectModel.bt_docker.dk_container as dc
        data = []
        template_container_name = re.findall("container_name\s*:\s*[\"\']+(.*)[\'\"]", template_data)
        container_list = dc.main().get_list(args)
        if not container_list["status"]:
            return public.returnMsg(False, "获取容器列表失败!")
        container_list = container_list['msg']['container_list']
        for container in container_list:
            if container['name'] in template_container_name:
                data.append(container['name'])
        if data:
            return public.returnMsg(False, "容器名已经存在！: <br>[{}]".format(", ".join(data)))
        # 获取模板所使用的端口
        rep = "(\d+):\d+"
        port_list = re.findall(rep, template_data)
        for port in port_list:
            if dp.check_socket(port):
                return public.returnMsg(False, "此端口 [{}] 已经被其他模板使用！".format(port))

    # 创建项目
    def create(self, args):
        """
        :param project_name         项目名
        :param remark          描述
        :param template_id             模板ID
        :param rags:
        :return:
        """
        project_name = public.md5(args.project_name)
        template_info = dp.sql("templates").where("id=?", (args.template_id,)).find()
        if not os.path.exists(template_info['path']):
            return public.returnMsg(False, "模板文件不存在!")
        name_exist = self.check_project_container_name(public.readFile(template_info['path']), args)
        if name_exist:
            return name_exist
        stacks_info = dp.sql("stacks").where("name=?", (project_name)).find()
        if not stacks_info:
            pdata = {
                "name": public.xsssec(args.project_name),
                "status": "1",
                "path": template_info['path'],
                "template_id": args.template_id,
                "time": time.time(),
                "remark": public.xsssec(args.remark)
            }
            dp.sql("stacks").insert(pdata)
        else:
            return public.returnMsg(False, "项目名已经存在!")
        if template_info['add_in_path'] == 1:
            self.create_project_in_path(
                project_name,
                template_info['path']
            )
        else:
            self.create_project_in_file(
                project_name,
                template_info['path']
            )
        dp.write_log("项目 [{}] 部署成功!".format(project_name))
        public.set_module_logs('docker', 'add_project', 1)
        return public.returnMsg(True, "部署成功!")

    # 列出compose文件/模板
    # def compose_file_list(self):
    #     if not os.path.exists(self.compose_path):
    #         os.mkdir(self.compose_path)
    #     project = os.listdir(self.compose_path)
    #     data = dict()
    #     for i in project:
    #         file = "{}/{}/docker-compose.yaml".format(self.compose_path,i)
    #         if not os.path.exists(file):
    #             continue
    #         data[i] = file
    #     return data

    # 项目列表
    def compose_project_list(self, args):
        """
        目前仅支持本地 url: unix:///var/run/docker.sock
        """
        args.url = "unix:///var/run/docker.sock"
        container_list = dc.main().get_list(args)
        if not container_list['status']:
            return public.returnMsg(False, "启动容器失败，请检查docker服务是否在运行!")
        if not container_list['msg']['service_status'] or not container_list['msg']['installed']:
            data = {
                "project_list": [],
                "template": [],
                "service_status": container_list['msg']['service_status'],
                "installed": container_list['msg']['installed']
            }
            return public.returnMsg(True, data)
        stacks_info = dp.sql("stacks").select()
        if isinstance(stacks_info, list):
            for i in stacks_info:
                tmp = []
                for c in container_list['msg']["container_list"]:
                    try:
                        if 'com.docker.compose.project' not in c["detail"]['Config']['Labels']:
                            continue
                    except:
                        continue
                    if c["detail"]['Config']['Labels']['com.docker.compose.project'] == public.md5(i['name']):
                        tmp.append(c)
                    if i['name'] == c["detail"]['Config']['Labels']['com.docker.compose.project']:
                        tmp.append(c)
                project_container_list = tmp
                i['container'] = project_container_list
        else:
            stacks_info = []
        template_list = self.template_list(args)
        if not template_list['status']:
            template_list = list()
        else:
            template_list = template_list['msg']['template']
        setup_docker = ds.main()
        data = {
            "project_list": stacks_info,
            "template": template_list,
            "service_status": setup_docker.get_service_status(),
            "installed": setup_docker.check_docker_program()
        }
        if data['project_list']:
            for i in data['project_list']:
                i['name'] = self.rename(i['name'])
        return public.returnMsg(True, data)

    def rename(self, name: str):
        try:
            if name[:4] != 'q18q':
                return name
            config_path = "{}/config/name_map.json".format(public.get_panel_path())
            config_data = json.loads(public.readFile(config_path))
            name_l = name.split('_')
            if name_l[0] in config_data.keys():
                name_l[0] = config_data[name_l[0]]
            return '_'.join(name_l)
        except:
            return name

    # 删除项目
    def remove(self, args):
        """
        project_id          数据库记录的项目ID
        :param args:
        :return:
        """
        statcks_info = dp.sql("stacks").where("id=?", (args.project_id,)).find()
        if not statcks_info:
            return public.returnMsg(True, "没有找到该项目名!")
        container_name = public.ExecShell("docker ps --format \"{{.Names}}\"")
        if statcks_info['name'] in container_name[0]:
            shell = f"/usr/bin/docker-compose -p {statcks_info['name']} -f {statcks_info['path']} down &> {self.__log_file}"
        else:
            shell = f"/usr/bin/docker-compose -p {public.md5(statcks_info['name'])} -f" \
                    f" {statcks_info['path']} down &> {self.__log_file}"
        public.ExecShell(shell)
        dp.sql("stacks").delete(id=args.project_id)
        dp.write_log("删除项目 [{}] 成功!".format(statcks_info['name']))
        return public.returnMsg(True, "删除成功!")

    # 停止项目
    def stop(self, args):
        """
        project_id          数据库记录的项目ID
        kill                强制停止项目 0/1
        :param args:
        :return:
        """
        statcks_info = dp.sql("stacks").where("id=?", (args.project_id,)).find()
        if not statcks_info:
            return public.returnMsg(True, "没找到项目配置!")

        shell = "/usr/bin/docker-compose -p {} -f {} stop &> {}".format(public.md5(statcks_info['name']),
                                                                        statcks_info['path'], self.__log_file)
        a, e = public.ExecShell(shell)
        dp.write_log("停止项目 [{}] 成功!".format(statcks_info['name']))
        return public.returnMsg(True, "设置成功!")

    # 启动项目
    def start(self, args):
        """
        project_id          数据库记录的项目ID
        :param args:
        :return:
        """
        statcks_info = dp.sql("stacks").where("id=?", (args.project_id,)).find()
        if not statcks_info:
            return public.returnMsg(False, "没找到项目配置!")
        shell = "/usr/bin/docker-compose -p {} -f {} start > {}".format(public.md5(statcks_info['name']),
                                                                        statcks_info['path'], self.__log_file)
        a, e = public.ExecShell(shell)
        dp.write_log("启动项目 [{}] 成功!".format(statcks_info['name']))
        return public.returnMsg(True, "设置成功!")

    # 拉取项目内需要的镜像
    def restart(self, args):
        """
        project_id          数据库记录的项目ID
        :param args:
        :return:
        """
        statcks_info = dp.sql("stacks").where("id=?", (args.project_id,)).find()
        if not statcks_info:
            return public.returnMsg(True, "没找到项目配置!")
        shell = "/usr/bin/docker-compose -p {} -f {} restart &> {}".format(public.md5(statcks_info['name']),
                                                                           statcks_info['path'], self.__log_file)
        a, e = public.ExecShell(shell)
        dp.write_log("重启项目 [{}] 成功!".format(statcks_info['name']))
        return public.returnMsg(True, "设置成功!")

    # 拉取模板内需要的镜像
    def pull(self, args):
        """
        template_id          数据库记录的项目ID
        :param args:
        :return:
        """
        statcks_info = dp.sql("templates").where("id=?", (args.template_id,)).find()
        if not statcks_info:
            return public.returnMsg(True, "没有找到该模板!")
        shell = "/usr/bin/docker-compose -p {} -f {} pull &> {}".format(statcks_info['name'], statcks_info['path'],
                                                                        self.__log_file)
        a, e = public.ExecShell(shell)
        dp.write_log("模板 [{}] 内的镜像拉取成功  !".format(statcks_info['name']))
        return public.returnMsg(True, "拉取成功!")

    # 暂停项目
    def pause(self, args):
        """
        project_id          数据库记录的项目ID
        :param args:
        :return:
        """
        statcks_info = dp.sql("stacks").where("id=?", (args.project_id,)).find()
        if not statcks_info:
            return public.returnMsg(True, "没找到项目配置!")
        shell = "/usr/bin/docker-compose -p {} -f {} pause &> {}".format(public.md5(statcks_info['name']),
                                                                         statcks_info['path'], self.__log_file)
        a, e = public.ExecShell(shell)
        dp.write_log("暂停 [{}] 成功!".format(statcks_info['name']))
        return public.returnMsg(True, "设置成功!")

    # 取消暂停项目
    def unpause(self, args):
        """
        project_id          数据库记录的项目ID
        :param args:
        :return:
        """
        statcks_info = dp.sql("stacks").where("id=?", (args.project_id,)).find()
        if not statcks_info:
            return public.returnMsg(True, "没找到项目配置!")
        shell = "/usr/bin/docker-compose -p {} -f {} unpause &> {}".format(public.md5(statcks_info['name']),
                                                                           statcks_info['path'], self.__log_file)
        a, e = public.ExecShell(shell)
        dp.write_log("取消暂停 [{}] 成功!".format(statcks_info['name']))
        return public.returnMsg(True, "设置成功!")

    # 递归扫描目录下的compose文件
    def scan_compose_file(self, path, data):
        """
        :param path 需要扫描的目录
        :param data 需要返回的数据 一个字典
        :param args:
        :return:
        """
        file_list = os.listdir(path)
        for file in file_list:
            current_path = os.path.join(path, file)
            # 判断是否是文件夹
            if os.path.isdir(current_path):
                self.scan_compose_file(current_path, data)
            else:
                if file == "docker-compose.yaml" or file == "docker-compose.yam" or file == "docker-compose.yml":
                    if "/www/server/panel/data/compose" in current_path:
                        continue
                    data.append(current_path)
        return data

    # 获取目录和子目录下的compose项目
    def get_compose_project(self, args):
        """
        :param path 需要获取的路径 是一个目录
        :param sub_dir 扫描子目录
        :param args:
        :return:
        """
        data = list()
        if args.path == "/":
            return public.returnMsg(False, "无法扫描根目录，文件数量太多!")
        if args.path[-1] == "/":
            args.path = args.path[:-1]
        if str(args.sub_dir) == "1":
            res = self.scan_compose_file(args.path, data)
            if not res:
                res = []
            else:
                tmp = list()
                for i in res:
                    tmp.append(
                        {
                            "project_name": i.split("/")[-2],
                            "conf_file": "/".join(i.split("/")),
                            "remark": "从本地添加"
                        }
                    )
                res = tmp
        else:
            yaml = "{}/docker-compose.yaml".format(args.path)
            yam = "{}/docker-compose.yam".format(args.path)
            yml = "{}/docker-compose.yml".format(args.path)
            if os.path.exists(yaml):
                res = [{
                    "project_name": args.path.split("/")[-1],
                    "conf_file": yaml,
                    "remark": "从本地添加"
                }]
            elif os.path.exists(yam):
                res = [{
                    "project_name": args.path.split("/")[-1],
                    "conf_file": yam,
                    "remark": "从本地添加"
                }]
            elif os.path.exists(yml):
                res = [{
                    "project_name": args.path.split("/")[-1],
                    "conf_file": yml,
                    "remark": "从本地添加"
                }]
            else:
                res = list()

        return res

    # 从现有目录中添加模板
    def add_template_in_path(self, args):
        """
        :param template_list list [{"project_name":"pathtest_template","conf_file":"/www/dockerce/mysecent-project/docker-compose.yaml","remark":"描述描述"}]
        :param args:
        :return:
        """
        create_failed = dict()
        create_successfully = dict()
        for template in args.template_list:
            path = template['conf_file']
            name = template['project_name']
            remark = template['remark']
            exists = self.template_list(args)['msg']['template']
            for i in exists:
                if name == i['name']:
                    create_failed[name] = "模板已存在!"
                    continue
                    # return public.returnMsg(False,"此模板名已经存在！")
            if not os.path.exists(path):
                create_failed[name] = "没找到此模板!"
                continue
                # return public.returnMsg(False,"没有找到该模板: {}".format(path))
            check_res = self.check_conf(path)
            if not check_res['status']:
                create_failed[name] = "模板验证失败，可能格式错误!"
                continue
                # return public.returnMsg(False,"模板验证失败，可能是格式错误！")
            pdata = {
                "name": name,
                "remark": remark,
                "path": path,
                "add_in_path": 1
            }
            dp.sql("templates").insert(pdata)
            create_successfully[name] = "模板添加成功!"

        for i in create_failed:
            if i in create_successfully:
                del (create_successfully[i])
            else:
                dp.write_log("从路径 [{}] 添加模板成功!".format(i))
        if not create_failed and create_successfully:
            return {'status': True, 'msg': '添加模板成功: [{}]'.format(','.join(create_successfully))}
        elif not create_successfully and create_failed:
            return {'status': True,
                    'msg': '添加模板失败: 模板名已经存在或格式错误 [{}]'.format(','.join(create_failed))}
        return {'status': True, 'msg': '这些模板成功: [{}]<br>这些模板失败: 模板名已经存在或格式错误 [{}]'.format(
            ','.join(create_successfully), ','.join(create_failed))}

    # 获取官方提供的模板(一键部署模板)

    # 迁移
