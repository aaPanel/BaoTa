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
import projectModel.bt_docker.dk_public as dp
import docker.errors

class main:

    __docker_url = None

    def docker_client(self,url):
        import projectModel.bt_docker.dk_public as dp
        return dp.docker_client(url)

    def get_container_list(self):
        '''
        获取容器详情生成列表
        @return: list
        '''
        containers = self.docker_client(self.__docker_url).containers
        c_list = containers.list(all=True)
        # 获取容器详情生成列表
        return [container_info.attrs for container_info in c_list]

    def get_volume_container_name(self, volume_detail, container_list):
        '''
        拼接对应的容器名与卷名
        @param volume_detail: 卷字典
        @param container_list: 容器详情列表
        @return:
        '''
        for container in container_list:
            if not container['Mounts']:
                continue
            for mount in container['Mounts']:
                if "Name" not in mount:
                    continue
                if volume_detail['Name'] == mount['Name']:
                    volume_detail['container'] = container['Name'].replace("/","")
        if 'container' not in volume_detail:
            volume_detail['container'] = ''
        return volume_detail

    def get_volume_list(self,args):
        """
        :param args.url: 链接docker的URL
        :return:
        """
        import projectModel.bt_docker.dk_setup as ds
        self.__docker_url = args.url
        client = self.docker_client(args.url)
        docker_setup = ds.main()
        installed = docker_setup.check_docker_program()
        service_status = docker_setup.get_service_status()
        if not client:
            data = {
                "volume": [],
                "installed": installed,
                "service_status": service_status
            }
            return public.returnMsg(True,data)
        volumes = client.volumes

        data = {
            "volume": self.get_volume_attr(volumes),
            "installed": installed,
            "service_status": service_status
        }
        return public.returnMsg(True,data)

    def get_volume_attr(self,volumes):
        volume_list = volumes.list()
        data = list()
        container_list = self.get_container_list()
        for v in volume_list:
            v = self.get_volume_container_name(v.attrs, container_list)
            data.append(v)
        return data

    def add(self,args):
        """
        添加一个卷
        :param name
        :param driver  local
        :param driver_opts (dict) – Driver options as a key-value dictionary
        :param labels str
        :return:
        """
        self.docker_client(args.url).volumes.create(
            name=args.name,
            driver=args.driver,
            driver_opts=args.driver_opts if args.driver_opts else None,
            labels=dp.set_kv(args.labels)
        )
        dp.write_log("添加存储卷 [{}] 成功！".format(args.name))
        return public.returnMsg(True,"添加成功!")

    def remove(self,args):
        """
        删除一个卷
        :param name  volume name
        :param args:
        :return:
        """
        try:
            obj = self.docker_client(args.url).volumes.get(args.name)
            obj.remove()
            dp.write_log("删除存储卷 [{}] 成功！".format(args.name))
            return public.returnMsg(True,"删除成功")
        except docker.errors.APIError as e:
            if "volume is in use" in str(e):
                return public.returnMsg(False,"存储卷正在使用中，无法删除！")
            return public.returnMsg(False,"删除失败！ {}".format(e))
