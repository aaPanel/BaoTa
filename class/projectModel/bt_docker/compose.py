#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: zouhw <zhw@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# Docker模型
#------------------------------
import public
from os import path as ospath
from os import makedirs as makedirs
import projectModel.bt_docker.public as dp
import projectModel.bt_docker.container as dc
import json


class compose:
    compose_path = "{}/data/compose".format(public.get_panel_path())

    # 验证配置文件
    def check_conf(self,path):
        shell = "/usr/bin/docker-compose -f {} config".format(path)
        a,e=public.ExecShell(shell)
        if e:
            return public.returnMsg(False,"验证失败: {}".format(e))
        return public.returnMsg(True,"验证通过！")

    # 用引导方式创建模板
    def add_template_gui(self,args):
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
        file = "{}/{}.yaml".format(path,args.name)
        if not ospath.exists(path):
            makedirs(path)
        data = json.loads(args.data)
        yaml.dump(data,file)

    def get_template_kw(self,args):
        data = {
            "version":"",
            "services":{
                "server_name_str":{#用户输入
                    "build":{
                        "context":"str",
                        "dockerfile":"str",
                        "args":[],
                        "cache_from":[],
                        "labels": [],
                        "network":"str",
                        "shm_size":"str",
                        "target":"str"
                    },
                    "cap_add":"",
                    "cap_drop":"",
                    "cgroup_parent":"str",
                    "command":"str",
                    "configs":{
                        "my_config_str":[]
                    },
                    "container_name": "str",
                    "credential_spec":{
                        "file":"str",
                        "registry":"str"
                    },
                    "depends_on":[],
                    "deploy":{
                        "endpoint_mode": "str",
                        "labels":{
                            "key":"value"
                        },
                        "mode":"str",
                        "placement":[{"key":"value"}],
                        "max_replicas_per_node": "int",
                        "replicas": "int",
                        "resources":{
                            "limits":{
                                "cpus":"str",
                                "memory":"str",
                            },
                            "reservations":{
                                "cpus": "str",
                                "memory": "str",
                            },
                            "restart_policy":{
                                "condition":"str",
                                "delay":"str",
                                "max_attempts":"int",
                                "window":"str"
                            }
                        }
                    }
                }
            }
        }

    # 创建项目配置文件
    def add_template(self,args):
        """
        添加一个模板文件
        :param name                     模板名
        :param description              模板描述
        :param data                     模板内容
        :param args:
        :return:
        """
        path = "{}/template".format(self.compose_path)
        file = "{}/{}.yaml".format(path,args.name)
        if not ospath.exists(path):
            makedirs(path)
        public.writeFile(file,args.data)
        check_res = self.check_conf(file)
        if not check_res['status']:
            return check_res
        pdata = {
            "name": args.name,
            "desc": args.description,
            "path": file
        }
        dp.sql("templates").insert(pdata)
        return public.returnMsg(True,"模板添加成功！")

    def template_list(self):
        """
        获取所有模板
        :param args:
        :return:
        """
        return public.returnMsg(True,dp.sql("templates").select())

    def remove_template(self,args):
        """
        删除模板
        :param template_id
        :param args:
        :return:
        """
        dp.sql("templates").delete(id=args.template_id)
        return public.returnMsg(True,"删除成功！")

    # 创建项目
    def create(self,args):
        """
        :param project_name         项目名
        :param description          描述
        :param template_id             模板ID
        :param rags:
        :return:
        """
        template_info = dp.sql("stacks").where("id=?",(args.template_id,)).find()
        if template_info['path']:
            return public.returnMsg(False,"没有找到模板文件")
        file = "{}/{}/docker-compose.yaml".format(self.compose_path,args.project_name)
        template_content = public.readFile(template_info['path'])
        public.writeFile(file,template_content)
        shell = "/usr/bin/docker-compose -p {} -f {} up -d".format(args.project_name,file)
        public.ExecShell(shell)
        stacks_info = dp.sql("stacks").where("name=?",(args.project_name)).find()
        if not stacks_info:
            pdata = {
                "name":args.project_name,
                "status": "1",
                "path": file
            }
            dp.sql("stacks").insert(pdata)
        return public.returnMsg(True,"部署成功！")

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
    def compose_project_list(self,args):
        """
        目前仅支持本地 url: unix:///var/run/docker.sock
        """
        args.url = "unix:///var/run/docker.sock"
        container_list = dc.contianer().get_list(args)
        if not container_list['status']:
            return public.returnMsg(False,"获取容器失败！")
        stacks_info = dp.sql("stacks").select()
        for i in stacks_info:
            project_container_list = [c for c in container_list['msg'] if c['Config']['Labels']['com.docker.compose.project'] == i['name']]
            i['container'] = project_container_list
        return stacks_info

    # 删除项目
    def remove(self,args):
        """
        project_id          数据库记录的项目ID
        :param args:
        :return:
        """
        statcks_info = dp.sql("stacks").where("id=?",(args.project_id,)).find()
        if not statcks_info:
            return public.returnMsg(True,"未找到该项目配置！")
        shell = "/usr/bin/docker-compose -p {} -f {} down".format(statcks_info['name'], statcks_info['path'])
        a,e=public.ExecShell(shell)
        dp.sql("stacks").delete(id=args.project_id)
        return public.returnMsg(True,"删除成功！")

    # 停止项目
    def stop(self,args):
        """
        project_id          数据库记录的项目ID
        kill                强制停止项目 0/1
        :param args:
        :return:
        """
        statcks_info = dp.sql("stacks").where("id=?",(args.project_id,)).find()
        if not statcks_info:
            return public.returnMsg(True,"未找到该项目配置！")
        shell = "/usr/bin/docker-compose -p {} -f {} stop".format(statcks_info['name'], statcks_info['path'])
        a,e=public.ExecShell(shell)
        dp.sql("stacks").delete(id=args.project_id)
        return public.returnMsg(True,"设置成功！")

    # 启动项目
    def start(self,args):
        """
        project_id          数据库记录的项目ID
        :param args:
        :return:
        """
        statcks_info = dp.sql("stacks").where("id=?", (args.project_id,)).find()
        if not statcks_info:
            return public.returnMsg(True, "未找到该项目配置！")
        shell = "/usr/bin/docker-compose -p {} -f {} start".format(statcks_info['name'], statcks_info['path'])
        a, e = public.ExecShell(shell)
        dp.sql("stacks").delete(id=args.project_id)
        return public.returnMsg(True, "设置成功！")

    # 拉取项目内需要的镜像
    def restart(self,args):
        """
        project_id          数据库记录的项目ID
        :param args:
        :return:
        """
        statcks_info = dp.sql("stacks").where("id=?", (args.project_id,)).find()
        if not statcks_info:
            return public.returnMsg(True, "未找到该项目配置！")
        shell = "/usr/bin/docker-compose -p {} -f {} restart".format(statcks_info['name'], statcks_info['path'])
        a, e = public.ExecShell(shell)
        dp.sql("stacks").delete(id=args.project_id)
        return public.returnMsg(True, "设置成功！")

    # 拉取项目内需要的镜像
    def pull(self,args):
        """
        project_id          数据库记录的项目ID
        :param args:
        :return:
        """
        statcks_info = dp.sql("stacks").where("id=?", (args.project_id,)).find()
        if not statcks_info:
            return public.returnMsg(True, "未找到该项目配置！")
        shell = "/usr/bin/docker-compose -p {} -f {} pull".format(statcks_info['name'], statcks_info['path'])
        a, e = public.ExecShell(shell)
        dp.sql("stacks").delete(id=args.project_id)
        return public.returnMsg(True, "拉取成功！")

    # 拉取项目内需要的镜像
    def pause(self,args):
        """
        project_id          数据库记录的项目ID
        :param args:
        :return:
        """
        statcks_info = dp.sql("stacks").where("id=?", (args.project_id,)).find()
        if not statcks_info:
            return public.returnMsg(True, "未找到该项目配置！")
        shell = "/usr/bin/docker-compose -p {} -f pause".format(statcks_info['name'], statcks_info['path'])
        a, e = public.ExecShell(shell)
        dp.sql("stacks").delete(id=args.project_id)
        return public.returnMsg(True, "设置成功！")

    # 拉取项目内需要的镜像
    def unpause(self,args):
        """
        project_id          数据库记录的项目ID
        :param args:
        :return:
        """
        statcks_info = dp.sql("stacks").where("id=?", (args.project_id,)).find()
        if not statcks_info:
            return public.returnMsg(True, "未找到该项目配置！")
        shell = "/usr/bin/docker-compose -p {} -f unpause".format(statcks_info['name'], statcks_info['path'])
        a, e = public.ExecShell(shell)
        dp.sql("stacks").delete(id=args.project_id)
        return public.returnMsg(True, "设置成功！")

    # 获取官方提供的模板(一键部署模板)


    # 迁移