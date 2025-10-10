# -*- coding: utf-8 -*-
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyleft (c) 2015-2099 宝塔软件(http://bt.cn) All lefts reserved.
# +-------------------------------------------------------------------
# | Author: wzz
# | email : wzz@bt.cn
# +-------------------------------------------------------------------
# +-------------------------------------------------------------------
# | docker sub_app 管理模型 -
# +-------------------------------------------------------------------
import json
import os.path
import sys
import time
import traceback

if "/www/server/panel/class" not in sys.path:
    sys.path.append('/www/server/panel/class')

import public
from mod.project.docker.app.base import App

class OllamaBase(App):
    def __init__(self):
        super(OllamaBase, self).__init__()
        self.ollama_port = "11434"
        self.ollama_local_url = "http://127.0.0.1:{}".format(self.ollama_port)

    def set_ollama_port(self, port):
        self.ollama_port = port
        self.ollama_local_url = self.ollama_local_url.format(port)
        return self

    def set_ollama_local_url(self, port):
        self.ollama_local_url = "http://127.0.0.1:{}".format(port)
        return self


class OllamaMod(OllamaBase):

    def __init__(self):
        super(OllamaMod, self).__init__()

    # 2025/2/8 11:47 获取本地所有的models
    # https://github.com/ollama/ollama/blob/main/docs/api.md#list-local-models
    def list_local_models(self):
        uri = "/api/tags"

        ps_json, stderr = public.ExecShell("docker-compose -p {service_name} ps --format json | {grep_v}".format(
            service_name=self.service_name.lower(),
            grep_v=self.grep_version,
        ))
        if "Segmentation fault" in ps_json:
            return []

        if not ps_json.startswith("["):
            ps = json.loads("[" + ps_json.strip().replace("\n", ",") + "]")
        else:
            ps = json.loads(ps_json.strip().replace("\n", ","))

        try:
            p_port = "11434"
            for i in ps:
                if "ollama/ollama" in i["Image"]:
                    if len(i["Publishers"]) == 0: break
                    p_port = i["Publishers"][0]["PublishedPort"]
        except:
            p_port = "11434"

        self.set_ollama_local_url(p_port)
        url = self.ollama_local_url + uri
        response = public.HttpGet(url)
        if not response: return []
        response = json.loads(response)

        if "models" in response:
            models = response["models"]
            for i in models:
                i["version"] = i["name"].split(":")[-1] if ":" in i["name"] else i["name"]
                i["l_name"] = i["name"].split(":")[0] if ":" in i["name"] else i["name"]
            return models
        return []

    # 2025/2/10 15:52 获取指定模型的信息
    # https://github.com/ollama/ollama/blob/main/docs/api.md#show-model-information
    def show_model_info(self, get):
        '''
            @name 获取指定模型的信息
        '''
        get.model_name = get.get("model_name", None)
        if get.model_name is None:
            return public.returnResult(False, "model_name参数不能为空")
        get.model_version = get.get("model_version", None)
        if get.model_version is None:
            return public.returnResult(False, "model_version参数不能为空")
        get.service_name = get.get("service_name", None)
        if get.service_name is None:
            return public.returnResult(False, "service_name参数不能为空")

        self.set_service_name(get.service_name)
        uri = "/api/show"
        ps_json, stderr = public.ExecShell("docker-compose -p {service_name} ps --format json | {grep_v}".format(
            service_name=self.service_name.lower(),
            grep_v=self.grep_version,
        ))
        if "Segmentation fault" in ps_json:
            return []

        if not ps_json.startswith("["):
            ps = json.loads("[" + ps_json.strip().replace("\n", ",") + "]")
        else:
            ps = json.loads(ps_json.strip().replace("\n", ","))

        try:
            p_port = "11434"
            for i in ps:
                if "ollama/ollama" in i["Image"]:
                    if len(i["Publishers"]) == 0: break
                    p_port = i["Publishers"][0]["PublishedPort"]
        except:
            p_port = "11434"

        self.set_ollama_local_url(p_port)

        url = self.ollama_local_url + uri
        param = {"model": "{}:{}".format(get.model_name, get.model_version)}

        import requests
        response = requests.post(url, data=json.dumps(param), timeout=10)

        return public.returnResult(True, data=response.json())

    # 2025/2/10 14:51 获取在线的所有models
    def list_online_models(self):
        '''
            @name 获取在线的所有models
        '''
        if not os.path.exists(self.ollama_online_models_file):
            public.downloadFile(public.get_url() + '/src/dk_app/apps/ollama_model.json', self.ollama_online_models_file)

        try:
            models = json.loads(public.readFile(self.ollama_online_models_file))

            res = []
            for i in models:
                res.append({
                    "name": i["name"],
                    "description": i["zh_cn_msg"],
                    "version": i["parameters"],
                    "size": i["size"],
                    "can_down": True,
                })

            return res
        except:
            return []

    # 2025/2/10 14:54 获取模型列表
    def get_models_list(self, get):
        '''
            @name 获取模型列表
        '''
        get.search = get.get("search", "")
        get.p = get.get("p/d", 1)
        get.row = get.get("limit/d", 20)
        get.service_name = get.get("service_name", None)
        if get.service_name is None:
            return public.returnResult(False, "service_name参数不能为空")
        get.status = get.get("status", "all")
        self.set_service_name(get.service_name)

        local_models = self.list_local_models()
        public.print_log(local_models)
        online_models = self.list_online_models()
        res = []
        can_down = True
        if os.path.exists("/tmp/nocandown.pl"):
            can_down = False

        # 2025/2/10 14:55 合并两个列表，增加status字段，已经安装了值为installed
        for i in online_models:
            i["can_down"] = can_down

            i["status"] = "uninstall"
            for j in local_models:
                if i["name"] == j["l_name"]:
                    i["status"] = "installed" if i["version"] == j["version"] else "uninstall"

                if os.path.exists("/tmp/{model_name}:{model_version}.failed".format(
                    model_name=i["name"],
                    model_version=i["version"],
                )):
                    i["status"] = "failed"

                if os.path.exists("/tmp/{model_name}:{model_version}.pl".format(
                    model_name=i["name"],
                    model_version=i["version"],
                )):
                    i["status"] = "downloading"

                if i["status"] in ("installed", "failed", "downloading"):
                    break

            if get.status != "all":
                if get.status != i["status"]: continue
            if get.search != "":
                if get.search not in i["name"] and get.search not in i["description"]: continue

            res.append(i)

        page_data = self.get_page(res, get)
        return self.pageResult(True, data=page_data["data"], page=page_data["page"])

    # 2025/2/17 16:34 给指定应用安装指定模型
    def down_models(self, get):
        '''
            @name 给指定应用安装指定模型
            @param service_name 服务名称
            @param model_name 模型名称
            @param model_version 模型版本
        '''
        get.service_name = get.get("service_name", None)
        if get.service_name is None:
            return public.returnResult(False, "service_name参数不能为空")
        get.model_name = get.get("model_name", None)
        if get.model_name is None:
            return public.returnResult(False, "model_name参数不能为空")
        get.model_version = get.get("model_version", None)
        if get.model_version is None:
            return public.returnResult(False, "model_version参数不能为空")

        self.set_service_name(get.service_name)

        # 获取容器信息
        ps_json, stderr = public.ExecShell("docker-compose -p {service_name} ps --format json | {grep_v}".format(
            service_name=self.service_name.lower(),
            grep_v=self.grep_version,
        ))
        if "Segmentation fault" in ps_json:
            return public.returnResult(False, "获取容器信息失败，docker-compose执行异常！")

        if not ps_json.startswith("["):
            ps = json.loads("[" + ps_json.strip().replace("\n", ",") + "]")
        else:
            ps = json.loads(ps_json.strip().replace("\n", ","))

        try:
            p_port = "11434"
            for i in ps:
                if "ollama/ollama" in i["Image"]:
                    if len(i["Publishers"]) == 0: break
                    p_port = i["Publishers"][0]["PublishedPort"]
        except:
            p_port = "11434"

        self.set_ollama_local_url(p_port)
        
        # 设置日志文件
        self.set_cmd_log()
        public.ExecShell("echo > {}".format(self.app_cmd_log))
        
        # 导入下载模块并执行下载
        from mod.project.docker.app.sub_app.downModel import download_model
        import threading
        
        # 创建新线程执行下载
        download_thread = threading.Thread(
            target=download_model,
            args=(
                get.service_name,
                get.model_name,
                get.model_version,
                self.ollama_local_url,
                self.app_cmd_log
            )
        )
        download_thread.daemon = True
        download_thread.start()

        return public.returnResult(True, "正在下载模型，请稍后查看日志")

    # 2025/2/10 15:50 删除指定应用的指定模型
    def del_models(self, get):
        '''
            @name 删除指定应用的指定模型
        '''
        get.service_name = get.get("service_name", None)
        if get.service_name is None:
            return public.returnResult(False, "service_name参数不能为空")
        get.model_name = get.get("model_name", None)
        if get.model_name is None:
            return public.returnResult(False, "model_name参数不能为空")
        get.model_version = get.get("model_version", None)
        if get.model_version is None:
            return public.returnResult(False, "model_version参数不能为空")

        self.set_service_name(get.service_name)

        ps_json, stderr = public.ExecShell("docker-compose -p {service_name} ps --format json | {grep_v}".format(
            service_name=self.service_name.lower(),
            grep_v=self.grep_version,
        ))
        if "Segmentation fault" in ps_json:
            return public.returnResult(True, "删除模型失败，docker-compose执行异常！")

        if not ps_json.startswith("["):
            ps = json.loads("[" + ps_json.strip().replace("\n", ",") + "]")
        else:
            ps = json.loads(ps_json.strip().replace("\n", ","))

        serviceName = get.service_name
        if len(ps) == 2:
            serviceName = "ollama"

        cmd = ("docker-compose -p {service_name} exec -it {serviceName} ollama rm {model_name}:{model_version}".format(
            service_name=get.service_name.lower(),
            serviceName=serviceName,
            model_name=get.model_name,
            model_version=get.model_version,
        ))
        public.ExecShell(cmd)
        return public.returnResult(True, "删除模型成功！")
