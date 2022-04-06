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
import sys
import threading
sys.path.insert(0, "/www/server/panel/class/")
sys.path.insert(1, "/www/server/panel/")
import projectModel.bt_docker.public as bp
import projectModel.bt_docker.container as bc
import projectModel.bt_docker.status as bs
import projectModel.bt_docker.public as dp
import public

import time
class monitor:

    def docker_client(self,url):
        return bp.docker_client(url)

    def write_cpu(self,data):
        pdata = {
            "time": time.time(),
            "cpu_usage": data['cpu_usage'],
            "online_cpus": data['online_cpus'],
            "container_id": data['container_id']
        }
        dp.sql("cpu_stats").insert(pdata)

    def write_io(self,data):
        pdata = {
            "time": time.time(),
            "write_total": data['write_total'],
            "read_total": data['read_total'],
            "container_id": data['container_id']
        }
        dp.sql("io_stats").insert(pdata)

    def write_net(self,data):
        pdata = {
            "time": time.time(),
            "tx_total": data['tx_total'],
            "rx_total": data['rx_total'],
            "tx": data['tx'],
            "rx": data['rx'],
            "container_id": data['container_id']
        }
        dp.sql("net_stats").insert(pdata)

    def write_mem(self,data):
        pdata = {
            "time": time.time(),
            "mem_limit": data['limit'],
            "cache": data['cache'],
            "usage": data['usage'],
            "usage_total": data['usage_total'],
            "container_id": data['container_id']
        }
        dp.sql("mem_stats").insert(pdata)

    # 获取所有docker容器的状态信息
    def container_status_for_all_hosts(self,host_info):
        """
        获取所有服务器的容器数量
        :param args:
        :return:
        """
        while True:
            args = public.to_dict_obj({})
            args.url = host_info['url']
            container_list = bc.contianer().get_list(args)['msg']
            for c in container_list:
                args.id = c['Id']
                args.write = 1
                bs.status().stats(args)
            time.sleep(60)

    # 获取服务器的容器数量
    def container_count(self,host_info):
        while True:
            args = public.to_dict_obj({})
            args.url = host_info['url']
            container_list = bc.contianer().get_list(args)['msg']
            pdata = {
                "time":time.time(),
                "container_count": len(container_list)
            }
            dp.sql("container_count").insert(pdata)
            time.sleep(600)


    def get_all_host_stats(self,fun):
        hosts = dp.sql('hosts').select()
        for i in hosts:
            t = threading.Thread(target=fun,args=(i,))
            t.setDaemon(True)
            t.start()

def main():
    m = monitor()
    # 获取所有容器信息
    m.get_all_host_stats(m.container_status_for_all_hosts)
    m.get_all_host_stats(m.container_count)
    condition=threading.Condition()
    condition.acquire()
    condition.wait()

if __name__ == "__main__":
    main()