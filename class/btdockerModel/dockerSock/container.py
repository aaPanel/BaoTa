# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------
# docker模型sock 封装库 容器库
# -------------------------------------------------------------------
import socket
import select
import json

import public
from btdockerModel.dockerSock.sockBase import base


class dockerContainer(base):
    def __init__(self):
        super(dockerContainer, self).__init__()

    # 2024/3/13 上午 11:20 获取所有容器列表
    def get_container(self):
        '''
            @name 获取所有容器列表
            @author wzz <2024/3/13 上午 10:54>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            return json.loads(public.ExecShell("curl -s --unix-socket {} http:/{}/containers/json?all=1".format(self._sock, self.get_api_version()))[0])
        except Exception as e:
            try:
                c_list = public.ExecShell("whereis curl | awk 'print {$1}'")[0].split(" ")
                for c in c_list:
                    if not c.endswith("/curl"): continue
                    res, err = public.ExecShell("{} -s --unix-socket {} http:/{}/containers/json?all=1".format(c, self._sock, self.get_api_version()))
                    if not err: return json.loads(res)
                return []
            except:
                return []

    # 2024/3/28 下午 11:37 获取指定容器的inspect
    def get_container_inspect(self, container_id: str):
        '''
            @name 获取指定容器的inspect
            @param container_id: 容器id
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            return json.loads(public.ExecShell("curl -s --unix-socket {} http:/{}/containers/{}/json".format(self._sock, self.get_api_version(), container_id))[0])
        except Exception as e:
            try:
                c_list = public.ExecShell("whereis curl | awk 'print {$1}'")[0].split(" ")
                for c in c_list:
                    if not c.endswith("/curl"): continue
                    res, err = public.ExecShell("{} -s --unix-socket {} http:/{}/containers/{}/json".format(c, self._sock, self.get_api_version(), container_id))
                    if not err: return json.loads(res)
                return []
            except:
                return []

    # 2025/1/18 11:05 构造返回日志
    def structure_docker_logs(self, log_data: str) -> list:
        """
        @name: 清理 Docker 日志并转换为 JSON 格式
        @param: raw_logs: 原始日志字符串
        @return: 日志对象列表
        """
        formatted_logs = []

        # 逐行处理日志
        for line in log_data.split('\n'):
            line = line.strip()

            if line:
                # 只处理包含日期时间戳的行，去除其它无用的字符
                parts = line.split(' ', 1)  # 按第一个空格分割时间戳和日志内容
                if len(parts) > 1:
                    timestamp = parts[0]
                    message = parts[1]
                    formatted_logs.append(message)

        # 返回格式化后的日志
        return "\n".join(formatted_logs)

    # 2025/1/18 10:26 获取容器日志
    def get_container_logs(self, container_id: str, options: dict) -> list:
        '''
            @name 获取容器日志
            @param container_id: 容器id
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
              # 定义 Docker API 请求路径
        url = f"/containers/{container_id}/logs?stdout=true&stderr=true&timestamps=true"

        if options:
            if "since" in options  and options["since"] != "":
                url += "&since={}".format(options['since'])
            if "until" in options  and options["until"] != "":
                url += "&until={}".format(options['until'])
            if "tail" in options  and options["tail"] != "":
                url += "&tail={}".format(options['tail'])

        # 设置 Unix socket 地址
        unix_socket = "/var/run/docker.sock"

        # 连接到 Docker 的 UNIX socket
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client_socket:
            client_socket.settimeout(1)
            client_socket.connect(unix_socket)

            # 构建 HTTP 请求
            http_request = f"GET {url} HTTP/1.1\r\n"
            http_request += "Host: localhost\r\n"
            http_request += "Accept: application/json\r\n"
            http_request += "Content-Type: application/json\r\n"
            http_request += "Connection: close\r\n\r\n"

            # 发送请求
            client_socket.sendall(http_request.encode())

            # 接收响应
            response = b""
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                response += data

            # 从响应中分割出 HTTP 头部和响应体
            headers, body = response.split(b"\r\n\r\n", 1)

            # 只保留日志部分，解码并忽略无法解码的字符
            log_data = body.decode('utf-8', errors='replace')

            result = self.structure_docker_logs(log_data)

            # 返回日志内容
            return result
