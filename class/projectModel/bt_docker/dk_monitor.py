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
import projectModel.bt_docker.dk_public as dp
import projectModel.bt_docker.dk_container as dc
import projectModel.bt_docker.dk_status as ds
import projectModel.bt_docker.dk_image as di
import public

import time
class main:

    __save_date = None
    __day_sec = 86400

    def __init__(self,save_date):
        if not save_date:
            self.__save_date = 30
        else:
            self.__save_date = save_date

    def docker_client(self,url):
        return dp.docker_client(url)

    def get_all_host_stats(self,fun):
        """
        获取所有主机信息并获取该主机下的容器状态
        :param fun: 需要调用的方法，用于获取并记录容器状态
        :return:
        """
        hosts = dp.sql('hosts').select()
        for i in hosts:
            t = threading.Thread(target=fun,args=(i,))
            t.setDaemon(True)
            t.start()

    # 获取所有docker容器的状态信息
    def container_status_for_all_hosts(self,host_info):
        """
        获取所有服务器的容器数量
        :param host_info: 服务器的配置信息，用于获取并记录容器状态
        :return:
        """
        # while True:
        args = public.to_dict_obj({})
        args.url = host_info['url']
        container_list = dc.main().get_list(args)['msg']
        for c in container_list['container_list']:
            args.id = c['id']
            args.write = 1
            args.save_date = self.__save_date
            ds.main().stats(args)
            # time.sleep(60)

    # 获取所有服务器的容器数量
    def container_count(self):
        # while True:
        hosts = dp.sql('hosts').select()
        n = 0
        for i in hosts:
            args = public.to_dict_obj({})
            args.url = i['url']
            container_list = dc.main().get_list(args)['msg']
            n += len(container_list)
        pdata = {
            "time":int(time.time()),
            "container_count": n
        }
        expired = time.time() - (self.__save_date * self.__day_sec)
        dp.sql("container_count").where("time<?",(expired,)).delete()
        dp.sql("container_count").insert(pdata)
            # time.sleep(60)

    def image_for_all_host(self):
        # while True:
        hosts = dp.sql('hosts').select()
        num = 0
        size = 0
        for i in hosts:
            args = public.to_dict_obj({})
            args.url = i['url']
            res = di.main().image_for_host(args)
            if not res['status']:
                continue
            print(res)
            num += res['msg']['num']
            size += res['msg']['size']
        pdata = {
            "time":int(time.time()),
            "num": num,
            "size": int(size)
        }
        expired = time.time() - (self.__save_date * self.__day_sec)
        dp.sql("image_infos").where("time<?",(expired,)).delete()
        dp.sql("image_infos").insert(pdata)
            # time.sleep(60)

def monitor():

    # 获取所有容器信息
    while True:
        save_date = dp.docker_conf()['SAVE']
        m = main(save_date)
        m.get_all_host_stats(m.container_status_for_all_hosts)
        # 开始获取容器总数
        t = threading.Thread(target=m.container_count)
        t.setDaemon(True)
        t.start()
        # 获取镜像详情
        t = threading.Thread(target=m.image_for_all_host)
        t.setDaemon(True)
        t.start()
        time.sleep(60)
    # condition=threading.Condition()
    # condition.acquire()
    # condition.wait()

if __name__ == "__main__":
    monitor()