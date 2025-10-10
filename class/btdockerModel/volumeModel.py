# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------

# ------------------------------
# Docker模型
# ------------------------------
import docker.errors
import public
from btdockerModel import dk_public as dp
from btdockerModel.dockerBase import dockerBase


class main(dockerBase):

    def docker_client(self, url):
        return dp.docker_client(url)

    def get_volume_container_name(self, volume_detail, container_list):
        '''
        拼接对应的容器名与卷名
        @param volume_detail: 卷字典
        @param container_list: 容器详情列表
        @return:
        '''
        try:
            for container in container_list:
                if not container['Mounts']:
                    continue
                for mount in container['Mounts']:
                    if "Name" not in mount:
                        continue
                    if volume_detail['Name'] == mount['Name']:
                        volume_detail['container'] = container['Names'][0].replace("/", "")
            if 'container' not in volume_detail:
                volume_detail['container'] = ''
        except:
            volume_detail['container'] = ''

        return volume_detail

    def get_volume_list(self, args):
        """
        :param self._url: 链接docker的URL
        :return:
        """
        try:
            data = list()
            from btdockerModel.dockerSock import volume
            sk_volume = volume.dockerVolume()
            volume_list = sk_volume.get_volumes()

            from btdockerModel.dockerSock import container
            sk_container = container.dockerContainer()
            container_list = sk_container.get_container()

            if "Volumes" in volume_list and type(volume_list["Volumes"]) == list:
                for v in volume_list["Volumes"]:
                    v["CreatedAt"] = dp.convert_timezone_str_to_timestamp(v["CreatedAt"])
                    data.append(self.get_volume_container_name(v, container_list))

                return sorted(data, key=lambda x: x['CreatedAt'], reverse=True)
            else:
                return []
        except Exception as e:
            return []

    def add(self, args):
        """
        添加一个卷
        :param name
        :param driver  local
        :param driver_opts (dict) – Driver options as a key-value dictionary
        :param labels str
        :return:
        """
        try:
            args.driver_opts = args.get("driver_opts", "")
            args.labels = args.get("labels", "")
            if args.driver_opts != "":
                args.driver_opts = dp.set_kv(args.driver_opts)
            if args.labels != "":
                args.labels = dp.set_kv(args.labels)

            if len(args.name) < 2:
                return public.returnMsg(False, "卷名不能少于2个字符！")

            self.docker_client(self._url).volumes.create(
                name=args.name,
                driver=args.driver,
                driver_opts=args.driver_opts if args.driver_opts else None,
                labels=args.labels if args.labels != "" else None
            )
            dp.write_log("添加存储卷 [{}] 成功！".format(args.name))
            return public.returnMsg(True, "添加成功!")
        except docker.errors.APIError as e:
            if "volume name is too short, names should be at least two alphanumeric characters" in str(e):
                return public.returnMsg(False, "卷名不能少于2个字符！")
            if "volume name" in str(e):
                return public.returnMsg(False, "卷名已存在！")
            return public.returnMsg(False, "添加失败！ {}".format(e))
        except Exception as e:
            if "driver_opts must be a dictionary" in str(e):
                return public.returnMsg(False, "选项和标签必须是键值对，例如：key=value！")
            return public.returnMsg(False, "添加失败！ {}".format(e))

    def remove(self, args):
        """
        删除一个卷
        :param name  volume name
        :param args:
        :return:
        """
        try:
            obj = self.docker_client(self._url).volumes.get(args.name)
            obj.remove()
            dp.write_log("删除存储卷 [{}] 成功！".format(args.name))
            return public.returnMsg(True, "删除成功")

        except docker.errors.APIError as e:
            if "volume is in use" in str(e):
                return public.returnMsg(False, "存储卷正在使用中，无法删除！")
            if "no such volume" in str(e):
                return public.returnMsg(False, "存储卷不存在！")
            return public.returnMsg(False, "删除失败！ {}".format(e))

    def prune(self, args):
        """
        删除无用的卷
        :param args:
        :return:
        """
        try:
            res = self.docker_client(self._url).volumes.prune()
            if not res['VolumesDeleted']:
                return public.returnMsg(False, "没有无用的存储卷！")

            dp.write_log("删除无用的存储卷成功！")
            return public.returnMsg(True, "删除成功！")
        except docker.errors.APIError as e:
            return public.returnMsg(False, "删除失败！ {}".format(e))
