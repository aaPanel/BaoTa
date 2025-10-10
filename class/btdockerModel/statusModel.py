# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------
import time,json

# ------------------------------
# Docker模型
# ------------------------------
import public
from btdockerModel import dk_public as dp
from btdockerModel.dockerBase import dockerBase


class main(dockerBase):
    __stats_tmp = dict()
    __docker = None

    def docker_client(self, url):
        if not self.__docker:
            self.__docker = dp.docker_client(url)
        return self.__docker

    def io_stats(self, stats, write=None):
        drive_io = stats['blkio_stats']['io_service_bytes_recursive']
        if drive_io:
            if len(drive_io) <= 2:
                try:
                    now = drive_io[0]['value']
                    self.__stats_tmp['read_total'] = now
                except:
                    self.__stats_tmp['read_total'] = 0
                try:
                    now = drive_io[1]['value']
                    self.__stats_tmp['write_total'] = now
                except:
                    self.__stats_tmp['write_total'] = 0
            else:
                try:
                    now = drive_io[0]['value'] + drive_io[2]['value']
                    self.__stats_tmp['read_total'] = now
                except:
                    self.__stats_tmp['read_total'] = 0
                try:
                    now = drive_io[1]['value'] + drive_io[3]['value']
                    self.__stats_tmp['write_total'] = now
                except:
                    self.__stats_tmp['write_total'] = 0
            if write:
                self.__stats_tmp['container_id'] = stats['id']
                self.write_io(self.__stats_tmp)

    def net_stats(self, stats, cache, write=None):
        try:
            net_io = stats['networks']['eth0']
            net_io_old = cache['networks']['eth0']
        except:
            self.__stats_tmp['rx_total'] = 0
            self.__stats_tmp['rx'] = 0
            self.__stats_tmp['tx_total'] = 0
            self.__stats_tmp['tx'] = 0
            if write:
                self.__stats_tmp['container_id'] = stats['id']
                self.write_net(self.__stats_tmp)
            return
        time_now = stats["time"]
        time_old = cache["time"]
        try:
            now = net_io["rx_bytes"]
            self.__stats_tmp['rx_total'] = now
            old = net_io_old["rx_bytes"]
            self.__stats_tmp['rx'] = int((now - old) / (time_now - time_old))
        except:
            self.__stats_tmp['rx_total'] = 0
            self.__stats_tmp['rx'] = 0
        try:
            now = net_io["tx_bytes"]
            old = net_io_old["tx_bytes"]
            self.__stats_tmp['tx_total'] = now
            self.__stats_tmp['tx'] = int((now - old) / (time_now - time_old))
        except:
            self.__stats_tmp['tx_total'] = 0
            self.__stats_tmp['tx'] = 0
        if write:
            self.__stats_tmp['container_id'] = stats['id']
            self.write_net(self.__stats_tmp)
        # return data

    def mem_stats(self, stats, write=None):
        mem = stats['memory_stats']
        try:
            self.__stats_tmp['limit'] = mem['limit']
            self.__stats_tmp['usage_total'] = mem['usage']
            if 'cache' not in mem['stats']:
                mem['stats']['cache'] = 0
            self.__stats_tmp['usage'] = mem['usage'] - mem['stats']['cache']
            self.__stats_tmp['cache'] = mem['stats']['cache']
            # data['mem_useage'] = round(mem['usage'] * 100 / data['limit'],2)
        except:
            # return public.get_error_info()
            self.__stats_tmp['limit'] = 0
            self.__stats_tmp['usage'] = 0
            self.__stats_tmp['cache'] = 0
            self.__stats_tmp['usage_total'] = 0
            # data['mem_useage'] = 0
        if write:
            self.__stats_tmp['container_id'] = stats['id']
            self.write_mem(self.__stats_tmp)
        # return data

    def cpu_stats(self, stats, write=None):
        # cpu_limit = dp.sql('container').where("c_id=?",(stats['id'],)).find()
        # if cpu_limit:
        #     cpu_limit = cpu_limit['cpu_limit']
        # else:
        #     cpu_limit = 1
        try:
            cpu = stats['cpu_stats']['cpu_usage']['total_usage'] - stats[
                'precpu_stats']['cpu_usage']['total_usage']
        except:
            cpu = 0
        try:
            system = stats['cpu_stats']['system_cpu_usage'] - stats[
                'precpu_stats']['system_cpu_usage']
        except:
            system = 0
        try:
            self.__stats_tmp['online_cpus'] = stats['cpu_stats']['online_cpus']
        except:
            self.__stats_tmp['online_cpus'] = 0
        if cpu > 0 and system > 0:
            self.__stats_tmp['cpu_usage'] = round(
                (cpu / system) * 100 * self.__stats_tmp['online_cpus'], 2)
        else:
            self.__stats_tmp['cpu_usage'] = 0.0
        if write:
            self.__stats_tmp['container_id'] = stats['id']
            self.write_cpu(self.__stats_tmp)
        # return data

    def stats(self, args):
        """
        获取某个容器的cpu，内存，网络io，磁盘io.
        :param url
        :param id
        :param args:
        :return:
        """
        try:
            container = self.docker_client(self._url).containers.get(args.id)
            stats = container.stats(decode=None, stream=False)
            stats['time'] = time.time()
            cache = public.cache_get('stats')
            if not cache:
                cache = stats
                public.cache_set('stats', stats)
            write = None
            if hasattr(args, "write"):
                write = args.write
                self.__stats_tmp['expired'] = time.time() - (args.save_date * 86400)
            stats['id'] = args.id
            import json
            from pygments import highlight, lexers, formatters
            formatted_json = json.dumps(stats, indent=3)
            colorful_json = highlight(formatted_json.encode('utf-8'), lexers.JsonLexer(), formatters.TerminalFormatter())
            # print(colorful_json)
            self.io_stats(stats, write)
            self.net_stats(stats, cache, write)
            self.cpu_stats(stats, write)
            self.mem_stats(stats, write)
            public.cache_set('stats', stats)
            self.__stats_tmp['detail'] = stats
            if 'dk_status' in args and args.dk_status != 'running':
                self.__stats_tmp['read_total'] = 0
                self.__stats_tmp['write_total'] = 0
            return self.__stats_tmp
        except Exception as ex:
            if "No such container" in str(ex):
                return public.returnMsg(False, '容器不存在，请刷新浏览器后再试！')
            return public.returnMsg(False, '获取容器状态失败: ' + str(ex))

    def top(self, get):
        """
        获取容器内进程信息
        @param get:
        @return:
        """
        container = self.docker_client(self._url).containers.get(get.id)
        return container.top()

    def write_cpu(self, data):
        pdata = {
            "time": time.time(),
            "cpu_usage": data['cpu_usage'],
            "online_cpus": data['online_cpus'],
            "container_id": data['container_id']
        }
        dp.sql("cpu_stats").where("time<?", (self.__stats_tmp['expired'],)).delete()
        dp.sql("cpu_stats").insert(pdata)

    def write_io(self, data):
        pdata = {
            "time": time.time(),
            "write_total": data['write_total'],
            "read_total": data['read_total'],
            "container_id": data['container_id']
        }
        dp.sql("io_stats").where("time<?", (self.__stats_tmp['expired'],)).delete()
        dp.sql("io_stats").insert(pdata)

    def write_net(self, data):
        pdata = {
            "time": time.time(),
            "tx_total": data['tx_total'],
            "rx_total": data['rx_total'],
            "tx": data['tx'],
            "rx": data['rx'],
            "container_id": data['container_id']
        }
        dp.sql("net_stats").where("time<?", (self.__stats_tmp['expired'],)).delete()
        dp.sql("net_stats").insert(pdata)

    def write_mem(self, data):
        pdata = {
            "time": time.time(),
            "mem_limit": data['limit'],
            "cache": data['cache'],
            "usage": data['usage'],
            "usage_total": data['usage_total'],
            "container_id": data['container_id']
        }
        dp.sql("mem_stats").where("time<?", (self.__stats_tmp['expired'],)).delete()
        dp.sql("mem_stats").insert(pdata)

    # 获取某服务器容器总数
    def get_container_count(self, args):
        return len(self.docker_client(self._url).containers.list())

    # 获取监控容器资源并记录每分钟

    # 获取Docker总览信息
    def get_docker_system_info(self,get):
        """
        获取Docker总览信息
        :param args:
        :return:
        """
        result = {
            "containers": {
                "usage": '-',
                "total": '-',
                "size": '-',  # 容器总大小
            },
            "images": {
                "usage": '-',
                "total": '-',
                "size": '-',  # 镜像总大小
            },
            "volumes": {
                "usage": '-',
                "total": '-',
                "size": '-',  # 卷总大小
            },
            "networks": {
                "usage": 0,
                "total": 0,
            },
            "composes": {
                "usage": 0,
                "total": 0,
            },
            "mirrors": 0,
        }

        system_info = self.docker_client(self._url).info()
        result["mirrors"] = len(system_info.get("RegistryConfig", {}).get("IndexConfigs", {}).keys())

        dfs,err = public.ExecShell("docker system df --format json")
        for df in dfs.split("\n"):
            if not df:
                continue
            try:
                df = json.loads(df)
            except:
                break
            if df.get("Type") == "Containers":
                result["containers"]["usage"] = df.get("Active", 0)
                result["containers"]["total"] = df.get("TotalCount", 0)
                result["containers"]["size"] = df.get("Size", 0)
            elif df.get("Type") == "Images":
                result["images"]["usage"] = df.get("Active", 0)
                result["images"]["total"] = df.get("TotalCount", 0)
                result["images"]["size"] = df.get("Size", 0)
            elif df.get("Type") == "Local Volumes":
                result["volumes"]["usage"] = df.get("Active", 0)
                result["volumes"]["total"] = df.get("TotalCount", 0)
                result["volumes"]["size"] = df.get("Size", 0)


        network_info = self.docker_client(self._url).networks.list()
        result["networks"]["total"] = len(network_info)

        from mod.project.docker.composeMod import main as Compose
        dk_compose = Compose()
        compose_list = dk_compose.ls(get)
        # for compose in compose_list:
        #     if "exited" in compose.get("Status", ""):
        #         result["composes"]["usage"] += 1
        result["composes"]["total"] = len(compose_list)
        # result["composes"]["usage"] = len(compose_list) - result["composes"]["usage"]

        return public.returnResult(True,data=result)