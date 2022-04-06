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
from projectModel.base import projectBase
import public

class main(projectBase):

    # 主机（本地docker/远程docker）操作方法
    @staticmethod
    def hosts_fun():
        import projectModel.bt_docker.host as dh
        return dh.docker_host()

    def set_hosts(self,args):
        """
        操作主机 添加/删除
        :param args:
        :return:
        """
        if args.act == "add":
            return self.hosts_fun().add(args)
        else:
            return self.hosts_fun().delete(args)

    def get_hosts_list(self,args=None):
        """
        获取主机列表
        :param args:
        :return:
        """
        return self.hosts_fun().get_list()

    # 容器编排(目前仅支持单机，使用命令方式部署)
    def compose_fun(self):
        import projectModel.bt_docker.compose as bc
        return bc.compose()

    def compose_create(self,args):
        return self.compose_fun().create(args)

    # def compose_file_list(self,args):
    #     return self.compose_fun().compose_file_list()

    def compose_project_list(self,args):
        return self.compose_fun().compose_project_list(args)

    def compose_remove(self,args):
        return self.compose_fun().remove(args)

    def compose_start(self,args):
        return self.compose_fun().start(args)

    def compose_stop(self,args):
        return self.compose_fun().stop(args)

    def compose_restart(self,args):
        return self.compose_fun().restart(args)

    def compose_pull(self,args):
        return self.compose_fun().pull(args)

    def compose_pause(self,args):
        return self.compose_fun().pause(args)

    def compose_unpause(self,args):
        return self.compose_fun().unpause(args)

    def compose_add_template(self,args):
        return self.compose_fun().add_template(args)

    def compose_remove_template(self,args):
        return self.compose_fun().remove_template(args)

    def compose_template_list(self,args):
        return self.compose_fun().template_list()

    # 容器操作方法
    @staticmethod
    def containers_fun():
        import projectModel.bt_docker.container as dc
        return dc.contianer()

    def get_all_containers(self,args):
        """
        获取所有容器的详细配置
        :param url
        :param args:
        :return:
        """
        return self.containers_fun().get_list(args)

    def get_containers_logs(self,args):
        """
        获取某个容器的日志
        :param args:
        :return:
        """
        return self.containers_fun().get_logs(args)

    def run_a_container(self,args):
        """
        创建并运行一个容器
        :return:
        """
        return self.containers_fun().run(args)

    def delete_a_container(self,args):
        """
        :param id
        :param args:
        :return:
        """
        return self.containers_fun().del_container(args)

    def commit_a_container(self,args):
        return self.containers_fun().commit(args)

    def export_a_container(self,args):
        return self.containers_fun().export(args)

    # 镜像操作方法
    @staticmethod
    def image_fun():
        import projectModel.bt_docker.image as di
        return di.image()

    def image_list(self,args):
        return self.image_fun().image_list(args)

    def image_save(self,args):
        return self.image_fun().save(args)

    def image_load(self,args):
        return self.image_fun().load(args)

    def image_pull(self,args):
        return self.image_fun().pull(args)

    def image_pull_from(self,args):
        return self.image_fun().pull_from_some_registry(args)

    def image_remove(self,args):
        return self.image_fun().remove(args)

    def image_push(self,args):
        return self.image_fun().push(args)

    def image_build(self,args):
        return self.image_fun().build(args)

    # 仓库操作方法
    @staticmethod
    def registry_fun():
        import projectModel.bt_docker.registry as di
        return di.registry()

    # def login_check(self,args):
    #     return self.registry_fun().login(args)

    def registry_list(self,args):
        return self.registry_fun().registry_list()

    def registry_add(self,args):
        return self.registry_fun().add(args)

    def registry_remove(self,args):
        return self.registry_fun().remove(args)

    # 大屏

    def get_screen_data(self,args):
        """
        获取大屏数据
        :return:
        """
        data = {
            # docker服务器信息
            "host_lists": self.get_hosts_list(),
            # 所有docker容器数量
            "container_total": self.container_for_all_hosts(),
            # 获取所有镜像信息
            "image_total": self.image_for_all_host()
        }
        return public.returnMsg(True,data)

    # 大屏所有主机下的容器数量
    def container_for_all_hosts(self,args=None):
        """
        获取所有服务器的容器数量
        :param args:
        :return:
        """
        import projectModel.bt_docker.public as dp
        hosts = dp.sql('hosts').select()
        num = 0
        for i in hosts:
            args.url = i['url']
            res = self.container_for_host(args)
            if not res['status']:
                continue
            num += res['msg']
        return public.returnMsg(True,num)

    def container_for_host(self,args):
        """
        获取某台服务器的docker容器数量
        :param url
        :param args:
        :return:
        """
        res = self.get_all_containers(args)
        if not res['status']:
            return res
        return public.returnMsg(True,len(res['msg']))

    def image_for_host(self,args):
        """
        获取镜像大小和获取镜像数量
        :param args:
        :return:
        """
        res = self.image_list(args)
        if not res['status']:
            return res
        num = len(res['msg'])
        size = 0
        for i in res['msg']:
            size += i['Size']
        return public.returnMsg(True,{'num':num,'size':size})

    def image_for_all_host(self,args=None):
        """
        获取所有服务器的镜像数量和大小
        :param args:
        :return:
        """
        import projectModel.bt_docker.public as dp
        hosts = dp.sql('hosts').select()
        num = 0
        size = 0
        for i in hosts:
            args.url = i['url']
            res = self.image_for_host(args)
            if not res['status']:
                continue
            num += res['msg']['num']
            size += res['msg']['size']
        return public.returnMsg(True,{'num':num,'size':size})

    # 网络
    @staticmethod
    def network_fun():
        import projectModel.bt_docker.network as dn
        return dn.network()

    def get_host_network(self,args):
        """
        获取主机上的所有网络
        :param args:
        :return:
        """
        return self.network_fun().get_host_network(args)

    def add_network(self,args):
        """
        添加一个网络
        :param args:
        :return:
        """
        return self.network_fun().add(args)

    def del_network(self,args):
        """

        :param args:
        :return:
        """
        return self.network_fun().del_network(args)

    # volumes方法
    @staticmethod
    def volume_fun():
        import projectModel.bt_docker.volume as dv
        return dv.volume()

    def get_volume_lists(self,args):
        return self.volume_fun().get_volume_list(args)

    def add_volume(self,args):
        return self.volume_fun().add(args)

    def remove_volume(self,args):
        return self.volume_fun().remove(args)