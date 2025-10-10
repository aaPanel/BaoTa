# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author:
# -------------------------------------------------------------------

# ------------------------------
# 容器启动顺序
# ------------------------------
import copy
import json
import os.path
import sys
import time
import subprocess
import psutil

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public
from btdockerModel.containerModel import main as docker
from btdockerModel.dockerSock import container
from btdockerModel import dk_public as dp


class main():
    GROUP_PATH = "/www/server/panel/data/docker_groups.json"

    def __init__(self):
        if not os.path.exists(self.GROUP_PATH):
            public.WriteFile(self.GROUP_PATH, "[]")

    # 添加组信息
    def add_group(self, get):
        try:

            if not hasattr(get, "group_name"):
                return public.returnMsg(False, "缺少参数name")

            if not hasattr(get, "container_info"):
                return public.returnMsg(False, "缺少参数container_info")

            interval = 30 if not get.interval else int(get.interval)

            container_info = get.container_info.split(',') if get.container_info else []
            from uuid import uuid4
            group_id = uuid4().hex[::2]

            file_data = self.__readFile()
            for group in file_data:
                if group["group_name"] == get.group_name.strip():
                    return public.returnMsg(False, "分组已存在")
                for temp in container_info:
                    if temp in group["order"]:
                        return public.returnMsg(False, "容器 {} 已经被分组 {} 添加了！".format(temp, group['group_name']))

            pdata = {
                "id": group_id,
                "group_name": get.group_name.strip(),
                "interval": interval,
                "order": container_info,
            }

            file_data.append(pdata)
            public.writeFile(self.GROUP_PATH, json.dumps(file_data))

            return public.returnMsg(True, "添加成功")
        except Exception as e:
            return public.returnMsg(False, "添加失败:{}".format(e))

    # 编辑组信息
    def update_group(self, get):
        try:
            if not hasattr(get, "id"):
                return public.returnMsg(False, "缺少参数id")

            interval = 30 if not get.interval else int(get.interval)
            container_info = get.container_info.split(",") if get.container_info else []
            file_data = self.__readFile()

            for group in file_data:
                if group["id"] == get.id.strip():
                    group["group_name"] = get.group_name.strip()
                    group["interval"] = interval
                    group["order"] = container_info
                    break

            public.writeFile(self.GROUP_PATH, json.dumps(file_data))

            return public.returnMsg(True, "编辑成功")
        except Exception as e:
            return public.returnMsg(False, "编辑失败：{}".format(e))

    # 删除组信息
    def del_group(self, get):
        try:
            if not hasattr(get, "id"):
                return public.returnMsg(False, "缺少参数id")

            file_data = self.__readFile()
            for index, data in enumerate(file_data):
                if data["id"] == get.id.strip():
                    del file_data[index]
                    break

            public.writeFile(self.GROUP_PATH, json.dumps(file_data))
            return public.returnMsg(True, "删除成功")
        except Exception as e:
            return public.returnMsg(False, "删除失败：{}".format(e))

    # 获取组信息
    def get_group(self, get):
        file_data = self.__readFile()

        # 拿配置文件数据
        for group in file_data:
            group["status"] = 0
            # 标记文件
            status_file = "/tmp/{}.json".format(group["id"])
            try:
                info = json.loads(public.readFile(status_file))
            except:
                info = {
                    "group_id": group["id"],
                    "status": 0,
                    "start_failed": ""
                }
            group["status"] = info["status"]
            group["start_failed"] = info["start_failed"]

        return public.returnResult(True, data=file_data)

    # 从组启动/停止容器
    def group_status(self, group_id, status):
        sk_container = container.dockerContainer()
        container_list = sk_container.get_container()

        if status not in ["start", "stop"]:
            return public.returnMsg(False, "status参数错误")

        # 状态启动中
        status_file = "/tmp/{}.json".format(group_id)

        group_data = {
            "group_id": group_id,
            "status": 0,
            "start_failed": ""
        }

        if status == "start":
            group_data["status"] = 2
        else:
            group_data["status"] = 4
        public.writeFile(status_file, json.dumps(group_data))

        try:
            get = public.dict_obj()
            file_data = self.__readFile()
            # 获取对应ID的信息
            group_info = self.__group_info(group_id, file_data)
            if group_info:
                # 获取容器列表名称列表
                container_order = group_info["order"]
                # 依次启动容器
                for containers in container_order:
                    get.id = containers
                    get.status = status
                    # 顺序开启并且容器已经开启了
                    if status == "start" and self.__is_running(containers, container_list):
                        continue
                    result = docker().set_container_status(get)

                    if not result["status"] and status == "start":
                        # 写入失败标记文件       # 启动失败直接返回
                        group_data["status"] = 3
                        # 用于记录启动失败的容器
                        group_data["start_failed"] = containers
                        public.writeFile(status_file, json.dumps(group_data))
                        return public.returnMsg(False, "容器[{}]操作失败".format(containers))
                    # 启动时间间隔
                    if len(container_order) > 1:
                        time.sleep(int(group_info["interval"]))

                if status == "start":
                    group_data["status"] = 1
                elif status == "stop":
                    group_data["status"] = 0
                public.writeFile(status_file, json.dumps(group_data))
                return public.returnMsg(True, "操作成功")
        except Exception as e:
            return public.returnMsg(False, "操作失败：{}".format(e))

    # 脚本调用
    def script_group(self, get):
        pid_file = "/tmp/docker_groups.pid"
        try:
            p = psutil.Process(public.readFile(pid_file))
            if p.is_running():
                return "操作运行中， 请等待上一个操作执行完成"
        except:
            pass

        if os.path.exists(pid_file):
            os.remove(pid_file)

        file_data = self.__readFile()
        for group in file_data:
            if group['id'] == get.id.strip():
                public.ExecShell(
                    "nohup /www/server/panel/pyenv/bin/python3 /www/server/panel/script/set_docker_groups.py {} {} &> /tmp/docker_groups.log & \n"
                    "echo $! > {} ".format(group['id'], get.status, pid_file)
                )

        return public.returnMsg(True, "容器开始按顺序{}".format(get.status))

    # 顺序启动 / 停止 分组
    def modify_group_status(self, get):
        try:
            group_ids = [i for i in get.id.split(",")]

            status = get.status.strip()
            if status not in ["start", "stop"]:
                return public.returnMsg(False, "无效的状态！")

            for group_id in group_ids:
                get.id = group_id
                return self.script_group(get)
        except Exception as e:
            return public.returnMsg(False, "操作失败:{}".format(e))

    # 获取Json文件内容
    def __readFile(self):
        try:
            return json.loads(public.readFile(self.GROUP_PATH)) if public.readFile(self.GROUP_PATH) else []
        except:
            return []

    # 返回指定组信息
    def get_info(self, get):
        if not hasattr(get, "id"):
            return public.returnMsg(False, "缺少参数id")
        return public.returnResult(True, data=self.__group_info(get.id, self.__readFile()))

    # 获取指定组信息  内部使用
    def __group_info(self, group_id, filedata):
        result = None
        for result in filedata:
            if group_id == result["id"]:
                break
        return result

    # 容器是否正在运行
    def __is_running(self, container_name, container_list):
        container_status = {dp.rename(temp['Names'][0].replace("/", "")): temp["State"] for temp in container_list}

        if container_name in container_status and container_status[container_name] == "running":
            return True
        else:
            return False

    def docker_list(self, get):
        try:
            # 获取容器列表和运行状态
            sk_container = container.dockerContainer()
            container_list = sk_container.get_container()

            filedata = self.__readFile()

            # 构建容器状态列表
            container_status_list = []

            # 构建分组容器字典
            group_containers = {group_data["group_name"]: group_data["order"] for group_data in filedata}

            # 遍历每个容器并获取状态
            for temp in container_list:
                container_name = dp.rename(temp['Names'][0].replace("/", ""))  # 假设容器信息中包含名称字段
                container_status = {
                    "name": container_name,
                    "status": temp["State"],
                    "group": ""
                }


                for group_name, group_order in group_containers.items():
                    if container_name in group_order:
                        container_status["group"] = group_name
                        break
                container_status_list.append(container_status)

            return public.returnResult(True, data=container_status_list)
        except Exception as e:
            return public.returnResult(True, data=[])
