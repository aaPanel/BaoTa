# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------

import docker.errors
# ------------------------------
# Docker模型
# ------------------------------
import public

from btdockerModel import dk_public as dp
from btdockerModel.dockerBase import dockerBase


class main(dockerBase):

    def docker_client(self, url):
        return dp.docker_client(url)

    def get_network_id(self, get):
        """
        asdf
        @param get:
        @return:
        """
        networks = self.docker_client(self._url).networks
        network = networks.get(get.id)
        return network.attrs

    def get_host_network(self, get):
        """
        获取服务器的docker网络
        :param get:
        :return:
        """
        try:
            client = self.docker_client(self._url)
            if not client: return []

            networks = client.networks
            network_attr = self.get_network_attr(networks)

            data = list()

            for attr in network_attr:
                get.id = attr["Id"]
                c_result = self.get_network_id(get)
                subnet = ""
                gateway = ""
                subnetv6 = ""
                gatewayv6 = ""

                if attr["IPAM"]["Config"]:
                    if "Subnet" in attr["IPAM"]["Config"][0]:
                        subnet = attr["IPAM"]["Config"][0]["Subnet"]
                    if "Gateway" in attr["IPAM"]["Config"][0]:
                        gateway = attr["IPAM"]["Config"][0]["Gateway"]

                    if len(attr["IPAM"]["Config"]) > 1:
                        if "Subnet" in attr["IPAM"]["Config"][1]:
                            subnetv6 = attr["IPAM"]["Config"][1]["Subnet"]
                        if "Gateway" in attr["IPAM"]["Config"][1]:
                            gatewayv6 = attr["IPAM"]["Config"][1]["Gateway"]

                tmp = {
                    "id": attr["Id"],
                    "name": attr["Name"],
                    "time": dp.convert_timezone_str_to_timestamp(attr["Created"]),
                    "driver": attr["Driver"],
                    "subnet": subnet,
                    "gateway": gateway,
                    "subnetv6": subnetv6,
                    "gatewayv6": gatewayv6,
                    "labels": attr["Labels"],
                    "used": 1 if c_result["Containers"] else 0,
                    "containers": c_result["Containers"],
                }
                data.append(tmp)

            return sorted(data, key=lambda x: x['time'], reverse=True)
        except Exception as e:
            err = str(e)
            if "Connection reset by peer" in err:
                return public.returnMsg(False, "docker服务运行异常，请尝试重启docker后再试！")
            return []

    def get_network_attr(self, networks):
        network = networks.list()
        return [i.attrs for i in network]

    def add(self, get):
        """
        :param name 网络名称
        :param driver  bridge/ipvlan/macvlan/overlay
        :param options Driver options as a key-value dictionary
        :param subnet '124.42.0.0/16'
        :param gateway '124.42.0.254'
        :param iprange '124.42.0.0/24'
        :param labels Map of labels to set on the network. Default None.
        :param remarks 备注
        :param get:
        :return:
        """
        import docker

        # 传参 给默认值
        subnet = get.get("subnet", "")
        gateway = get.get("gateway", "")
        iprange = get.get("iprange", "")
        subnet_v6 = get.get("subnet_v6", "")
        gateway_v6 = get.get("gateway_v6", "")
        v6_status = get.get("status/d", 0)

        ipam_pool4 = docker.types.IPAMPool(
            subnet=subnet,
            gateway=gateway,
            iprange=iprange
        )

        if v6_status != 0:
            ipam_pool6 = docker.types.IPAMPool(
                subnet=subnet_v6,
                gateway=gateway_v6,
            )
            ipam_config = docker.types.IPAMConfig(
                pool_configs=[ipam_pool4, ipam_pool6]
            )
        else:
            ipam_config = docker.types.IPAMConfig(
                pool_configs=[ipam_pool4]
            )

        try:
            self.docker_client(self._url).networks.create(
                name=get.name,
                options=dp.set_kv(get.options),
                driver=get.driver,  # 使用用户指定的网络驱动类型
                ipam=ipam_config,
                enable_ipv6=v6_status,
            )
        except docker.errors.APIError as e:
            print(str(e))
            if "failed to allocate gateway" in str(e):
                return public.returnMsg(False, "网关设置有误，请输入与此子网相符的网关：{}".format(get.subnet))
            if "invalid CIDR address" in str(e):
                return public.returnMsg(False, "子网地址格式错误，请输入例如：172.16.0.0/16")
            if "invalid Address SubPool" in str(e):
                return public.returnMsg(False, "IP范围格式错误，请输入与此子网相符的IP范围：{}".format(get.subnet))
            if "Pool overlaps with other one on this address space" in str(e):
                return public.returnMsg(False, "IP范围【{}】已经存在！".format(get.subnet))
            if "kernel version failed to meet the minimum ipvlan kernel requirement" in str(e):
                return public.returnMsg(False, "你的系统内核版本低于 4.2,不满足ipvlan对内核版本的最小要求，请更新内核或选择其他网络模式")
            if "not a swarm manager" in str(e):
                return public.returnMsg(False, "当前节点不是 Swarm 管理节点。需要进行相关配置后才能使用。")
            return public.returnMsg(False, "添加网络失败！ {}".format(str(e)))

        dp.write_log("添加网络 [{}] [{}] 成功!".format(get.name, get.iprange))
        return public.returnMsg(True, "添加网络成功!")

    def del_network(self, get):
        """
        :param id
        :param get:
        :return:
        """
        try:
            networks = self.docker_client(self._url).networks.get(get.id)
            attrs = networks.attrs
            if attrs['Name'] in ["bridge", "none"]:
                return public.returnMsg(False, "系统默认网络不能被删除！")

            networks.remove()
            dp.write_log("删除网络 [{}] 成功!".format(attrs['Name']))
            return public.returnMsg(True, "删除成功！")

        except docker.errors.APIError as e:
            if " has active endpoints" in str(e):
                return public.returnMsg(False, "网络正在被使用中无法被删除!")
            return public.returnMsg(False, "删除失败! {}".format(str(e)))

    def prune(self, get):
        """
        删除无用的网络
        :param get:
        :return:
        """
        try:
            res = self.docker_client(self._url).networks.prune()
            if not res['NetworksDeleted']:
                return public.returnMsg(False, "没有无用的网络！")

            dp.write_log("删除无用的网络成功！")
            return public.returnMsg(True, "删除成功！")

        except docker.errors.APIError as e:
            return public.returnMsg(False, "删除失败！ {}".format(str(e)))

    def disconnect(self, get):
        """
        断开某个容器的网络
        :param id
        :param container_id
        :param get:
        :return:
        """
        try:
            get.id = get.get("id/s", "")
            get.container_id = get.get("container_id/s", "")
            if get.id == "":
                return public.returnMsg(False, "网络ID不能为空,请传入有效的网络ID！")
            if get.container_id == "":
                return public.returnMsg(False, "容器ID不能为空,请传入有效的容器ID！")

            networks = self.docker_client(self._url).networks.get(get.id)
            networks.disconnect(get.container_id)
            dp.write_log("断开网络 [{}] 成功!".format(get.id))
            return public.returnMsg(True, "断开网络成功！")
        except docker.errors.APIError as e:
            if "No such container" in str(e):
                return public.returnMsg(False, "容器ID: {}, 不存在！".format(get.container_id))
            if "network" in str(e) and "Not Found" in str(e):
                return public.returnMsg(False, "网络ID: {}, 不存在！".format(get.id))
            return public.returnMsg(False, "断开网络失败！ {}".format(str(e)))

    def connect(self, get):
        """
        连接到指定网络
        :param id
        :param container_id
        :param get:
        :return:
        """
        try:
            networks = self.docker_client(self._url).networks.get(get.id)
            networks.connect(get.container_id)
            dp.write_log("连接网络 [{}] 成功!".format(get.id))
            return public.returnMsg(True, "连接网络成功！")
        except docker.errors.APIError as e:
            if "No such container" in str(e):
                return public.returnMsg(False, "容器ID: {}, 不存在！".format(get.container_id))
            if "network" in str(e) and "Not Found" in str(e):
                return public.returnMsg(False, "网络ID: {}, 不存在！".format(get.id))
            return public.returnMsg(False, "连接网络失败！ {}".format(str(e)))

    # 2024/11/27 14:37 创建网络
    def create_network(self, get):
        '''
            @name 创建网络
        '''
        get.subnet = get.get("subnet", "")
        get.gateway = get.get("gateway", "")
        get.iprange = get.get("iprange", "")
        get.subnet_v6 = get.get("subnet_v6", "")
        get.gateway_v6 = get.get("gateway_v6", "")
        get.v6_status = get.get("status", 0)

        get.name = get.get("name", None)
        if get.name is None: return public.returnResult(False, "网络名称不能为空！")

        get.driver = get.get("driver", "bridge")
        get.options = get.get("options", "")

        ipam_pool4 = {}
        ipam_pool6 = {}
        if get.subnet != "":
            if get.gateway == "": return public.returnResult(False, "网关不能为空！")
            if get.iprange == "": return public.returnResult(False, "IP范围不能为空！")

            ipam_pool4 = {
                "subnet": get.subnet,
                "gateway": get.gateway,
                "iprange": get.iprange
            }

        if get.v6_status != 0:
            ipam_pool6 = {
                "subnet": get.subnet_v6,
                "gateway": get.gateway_v6,
            }

        if not ipam_pool4 and not ipam_pool6:
            get.ipam = None
        elif not ipam_pool6:
            get.ipam = {
                "Driver": "default",
                "Config": [{
                    "Subnet": get.subnet,
                    "Gateway": get.gateway,
                    "IPRange": get.iprange
                }]
            }
        else:
            get.ipam = {
                "Driver": "default",
                "Config": [{
                    "Subnet": get.subnet,
                    "Gateway": get.gateway,
                    "IPRange": get.iprange
                }, {
                    "Subnet": get.subnet_v6,
                    "Gateway": get.gateway_v6,
                }]
            }

        get.post_data = {
            "name": get.name,
            "options": None,
            "driver": get.driver,
            "ipam": get.ipam,
            "enable_ipv6": bool(get.v6_status),
        }

        from btdockerModel.dockerSock import network
        sk_network = network.dockerNetWork()
        create_network = sk_network.create_network(get)

        if not create_network:
            return public.returnResult(False, "创建网络失败！")
        if "message" in create_network:
            if "already exists" in create_network["message"]:
                return public.returnResult(False, "网络名称：【{}】 已存在！".format(get.name))
            return public.returnResult(False, create_network["message"])
        return public.returnResult(True, "创建网络成功！")
