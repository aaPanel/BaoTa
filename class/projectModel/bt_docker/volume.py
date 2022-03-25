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
import json

class volume:

    def docker_client(self,url):
        import projectModel.bt_docker.public as dp
        return dp.docker_client(url)

    def get_volume_list(self,args):
        """

        :param args:
        :return:
        """
        volumes = self.docker_client(args.url).volumes
        return self.get_volume_attr(volumes)

    def get_volume_attr(self,volumes):
        volume_list = volumes.list()
        return [v.attrs for v in volume_list]

    def add(self,args):
        """
        添加一个卷
        :param name
        :param driver  local
        :param driver_opts (dict) – Driver options as a key-value dictionary
        :param labels (dict) – Labels to set on the volume
        :return:
        """
        self.docker_client(args.url).volumes.create(
            name=args.name,
            driver=args.driver,
            driver_opts=json.loads(args.driver_opts) if args.driver_opts else None,
            labels=json.loads(args.labels) if args.labels else None
        )
        return public.returnMsg(True,"添加成功！")

    def remove(self,args):
        """
        删除一个卷
        :param name  volume name
        :param args:
        :return:
        """
        obj = self.docker_client(args.url).volumes.get(args.name)
        obj.remove()
        return public.returnMsg(True,"删除成功")
