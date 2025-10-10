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

    def docker_client(self,url):
        import projectModel.bt_docker.dk_public as dp
        return dp.docker_client(url)

    def get_host_network(self,args):
        """
        获取服务器的docker网络
        :param args:
        :return:
        """
        import projectModel.bt_docker.dk_setup as ds
        docker_setup = ds.main()
        installed = docker_setup.check_docker_program()
        service_status = docker_setup.get_service_status()
        client = self.docker_client(args.url)
        if not client:
            data = {
                "images_list": [],
                "registry_list": [],
                "installed": installed,
                "service_status": service_status
            }
            return public.returnMsg(True,data)
        networks = client.networks
        network_attr = self.get_network_attr(networks)
        data = list()
        for attr in network_attr:
            subnet = ""
            gateway = ""
            if attr["IPAM"]["Config"]:
                if "Subnet" in attr["IPAM"]["Config"][0]:
                    subnet = attr["IPAM"]["Config"][0]["Subnet"]
                if "Gateway" in attr["IPAM"]["Config"][0]:
                    gateway = attr["IPAM"]["Config"][0]["Gateway"]
            tmp = {
                "id": attr["Id"],
                "name":attr["Name"],
                "time":attr["Created"],
                "driver":attr["Driver"],
                "subnet":subnet,
                "gateway": gateway,
                "labels": attr["Labels"]
            }
            data.append(tmp)

        res = {
            "network": data,
            "installed": installed,
            "service_status": service_status
        }
        return public.returnMsg(True,res)

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
        :param remarks 备注
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
            options=dp.set_kv(args.options),
            driver="bridge",
            ipam=ipam_config,
            labels=dp.set_kv(args.labels)
        )
        dp.write_log("添加网络 [{}] [{}] 成功!".format(args.name, args.iprange))
        return public.returnMsg(True,"添加网络成功!")

    def del_network(self,args):
        """
        :param id
        :param args:
        :return:
        """
        try:

            networks = self.docker_client(args.url).networks.get(args.id)
            attrs = networks.attrs
            if attrs['Name'] in ["bridge","none"]:
                return public.returnMsg(False, "系统默认网络不能被删除！")
            networks.remove()
            dp.write_log("删除网络 [{}] 成功!".format(attrs['Name']))
            return public.returnMsg(True, "删除成功！")
        except docker.errors.APIError as e:
            if " has active endpoints" in str(e):
                return public.returnMsg(False,"网络正在被使用中无法被删除!")
            return public.returnMsg(False,"删除失败! {}".format(str(e)))