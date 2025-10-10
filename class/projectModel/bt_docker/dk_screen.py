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
import projectModel.bt_docker.dk_public as dp
import time

class main:

    def get_status(self,args):
        """
        start_time
        stop_time
        :param args:
        :return:
        """
        data = dict()
        # 容器总数
        data['container_count'] = self.__get_container_count(args)
        # 镜像信息，镜像总数，占用空间大小
        data['image_info'] = dp.sql("image_infos").where("time>=? and time<=?",(args.start_time,args.stop_time)).select()
        # 主机信息
        data['host'] = len(dp.sql('hosts').select())
        # 1小时内容器占用资源前三平均值
        data['container_top'] = {"cpu":self.__get_cpu_avg(),"mem":self.__get_mem_avg()}
        return data

    def __get_container_count(self,args):
        count = dp.sql('container_count').where("time>=? and time<=?", (args.start_time, args.stop_time)).select()
        if not count:
            return 0
        return count[-1]

    def __get_mem_avg(self):
        now = int(time.time())
        start_time = now - 3600
        data = dp.sql("mem_stats").where("time>=? and time<=?",(start_time,now)).select()
        containers = list()
        info = dict()
        # 获取容器ID
        for d in data:
            containers.append(d['container_id'])
        # 获取每个容器1小时内的cpu使用率总和
        containers = set(containers)
        for c in containers:
            num = 0
            usage = 0
            for d in data:
                if d['container_id'] == c:
                    num += 1
                    usage += float(d['usage'])
            if num != 0:
                info[c] = usage / num
        return info

    def __get_cpu_avg(self):
        now = int(time.time())
        start_time = now - 3600
        data = dp.sql("cpu_stats").where("time>=? and time<=?",(start_time,now)).select()
        containers = list()
        info = dict()
        # 获取容器ID
        for d in data:
            containers.append(d['container_id'])
        # 获取每个容器1小时内的cpu使用率总和
        containers = set(containers)
        for c in containers:
            num = 0
            cpu_usage = 0
            for d in data:
                if d['container_id'] == c:
                    num += 1
                    cpu_usage += float(0 if d['cpu_usage'] == '0.0' else d['cpu_usage'])
            if num != 0:
                info[c] = cpu_usage / num
        return info