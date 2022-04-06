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
import json
import public

class network:

    def docker_client(self,url):
        import projectModel.bt_docker.public as dp
        return dp.docker_client(url)

    def get_host_network(self,args):
        """
        获取服务器的docker网络
        :param args:
        :return:
        """
        networks = self.docker_client(args.url).networks
        return self.get_network_attr(networks)

    def get_network_attr(self,networks):
        network = networks.list()
        return [i.attrs for i in network]

    def add(self,args):
        """
        :param name 网络名称
        :param driver  bridge/ipvlan/macvlan/overlay
        :param options Driver options as a key-value dictionary
        :param subnet '124.42.0.0/16'
        :param gateway '124.42.0.254'
        :param iprange '124.42.0.0/24'
        :param labels Map of labels to set on the network. Default None.
        :param args:
        :return:
        """
        import docker
        ipam_pool = docker.types.IPAMPool(
            subnet=args.subnet,
            gateway=args.gateway,
            iprange=args.iprange
        )
        ipam_config = docker.types.IPAMConfig(
            pool_configs=[ipam_pool]
        )
        self.docker_client(args.url).networks.create(
            name=args.name,
            options=json.loads(args.options) if args.options else None,
            driver="bridge",
            ipam=ipam_config,
            labels=json.loads(args.loables) if args.labels else None
        )
        return public.returnMsg(True,"添加成功！")

    def del_network(self,args):
        """
        :param id
        :param args:
        :return:
        """
        networks = self.docker_client(args.url).networks.get(args.id)
        networks.remove()
        return public.returnMsg(True, "删除成功！")