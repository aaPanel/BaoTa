# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------
# ------------------------------
# docker模型
# ------------------------------
import json
import os
import sys
import time


if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

os.chdir("/www/server/panel")
import public

from mod.project.docker.app.appManageMod import AppManage
from mod.project.docker.runtime.runtimeManage import RuntimeManage
from mod.project.docker.sites.sitesManage import SitesManage
from mod.project.docker.app.sub_app.ollamaMod import OllamaMod
from mod.project.docker.apphub.apphubManage import AppHub
from btdockerModel import dk_public as dp


class main(AppManage, RuntimeManage, SitesManage, OllamaMod):

    def __init__(self):
        super(main, self).__init__()
        OllamaMod.__init__(self)

    # 2024/6/26 下午5:49 获取所有已部署的项目列表
    def get_project_list(self, get):
        '''
            @name 获取所有已部署的项目列表
            @author wzz <2024/6/26 下午5:49>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            if self.def_name is None: self.set_def_name(get.def_name)
            if hasattr(get, '_ws') and hasattr(get._ws, 'btws_get_project_list'):
                return

            while True:
                compose_list = self.ls(get)
                if len(compose_list) == 0:
                    if hasattr(get, '_ws'):
                        get._ws.send(json.dumps(self.wsResult(
                            True,
                            data=[],
                        )))

                stacks_info = dp.sql("stacks").select()
                compose_project = []

                for j in compose_list:
                    t_status = j["Status"].split(",")
                    container_count = 0
                    for ts in t_status:
                        container_count += int(ts.split("(")[1].split(")")[0])

                    j_name = j['Name']
                    if "bt_compose_" in j_name:
                        config_path = "{}/config/name_map.json".format(public.get_panel_path())
                        name_map = json.loads(public.readFile(config_path))
                        if j_name in name_map:
                            j_name = name_map[j_name]
                        else:
                            j_name = j_name.replace("bt_compose_", "")

                    tmp = {
                        "id": None,
                        "name": j_name,
                        "status": "1",
                        "path": j['ConfigFiles'],
                        "template_id": None,
                        "time": None,
                        "remark": "",
                        "run_status": j['Status'].split("(")[0].lower(),
                        "container_count": container_count,
                    }
                    for i in stacks_info:
                        if public.md5(i['name']) in j['Name']:
                            tmp["name"] = i['name']
                            tmp["run_status"] = j['Status'].split("(")[0].lower()
                            tmp["template_id"] = i['template_id']
                            tmp["time"] = i['time']
                            tmp["remark"] = i["remark"]
                            tmp["id"] = i['id']
                            break

                        if i['name'] == j['Name']:
                            tmp["run_status"] = j['Status'].split("(")[0].lower()
                            tmp["template_id"] = i['template_id']
                            tmp["time"] = i['time']
                            tmp["remark"] = i["remark"]
                            tmp["id"] = i['id']
                            break

                    if tmp["time"] is None:
                        if os.path.exists(j['ConfigFiles']):
                            get.path = j['ConfigFiles']
                            compose_ps = self.ps(get)
                            if len(compose_ps) > 0 and "CreatedAt" in compose_ps[0]:
                                tmp["time"] = dp.convert_timezone_str_to_timestamp(compose_ps[0]['CreatedAt'])

                    compose_project.append(tmp)

                if hasattr(get, '_ws'):
                    setattr(get._ws, 'btws_get_project_list', True)
                    get._ws.send(json.dumps(self.wsResult(
                        True,
                        data=sorted(compose_project, key=lambda x: x["time"] if x["time"] is not None else float('-inf'), reverse=True),
                    )))

                time.sleep(2)
        except Exception as e:
            return public.returnResult(False, str(e))

    # 2024/6/26 下午8:55 获取指定compose.yml的docker-compose ps
    def get_project_ps(self, get):
        '''
            @name 获取指定compose.yml的docker-compose ps
            @author wzz <2024/6/26 下午8:56>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            if self.def_name is None: self.set_def_name(get.def_name)
            if hasattr(get, '_ws') and hasattr(get._ws, 'btws_get_project_ps_{}'.format(get.path)):
                return

            from btdockerModel.dockerSock import container
            sk_container = container.dockerContainer()

            while True:
                compose_list = self.ps(get)
                if len(compose_list) == 0:
                    if hasattr(get, '_ws'):
                        get._ws.send(json.dumps(self.wsResult(
                            True,
                            data=[],
                        )))
                    break

                for l in compose_list:
                    if not "Image" in l:
                        l["Image"] = ""
                        if "ID" in l:
                            l["inspect"] = sk_container.get_container_inspect(l["ID"])
                            l["Image"] = l["inspect"]["Config"]["Image"]

                    if not "Ports" in l:
                        l["Ports"] = ""
                        if "Publishers" in l and not l["Publishers"] is None:
                            for p in l["Publishers"]:
                                if p["URL"] == "":
                                    l["Ports"] += "{}/{},".format(p["TargetPort"], p["Protocol"])
                                    continue

                                l["Ports"] += "{}:{}->{}/{},".format(p["URL"], p["PublishedPort"], p["TargetPort"], p["Protocol"])
                    #构造容器详情所需的ports 实现参考了containerModel.struct_container_ports
                    ports_data = dict()
                    for port in l["Publishers"]:
                        key = str(port["TargetPort"]) + "/" + port["Protocol"]
                        if key not in ports_data.keys():
                            ports_data[str(port["TargetPort"]) + "/" + port["Protocol"]] = [{
                                "HostIp": port["URL"],
                                "HostPort": str(port["PublishedPort"])
                            }] if port["URL"] != "" else None
                        else:
                            ports_data[str(port["TargetPort"]) + "/" + port["Protocol"]].append({
                                "HostIp": port["URL"],
                                "HostPort": str(port["PublishedPort"])
                            })
                    l["ports"] =ports_data
                if hasattr(get, '_ws'):
                    setattr(get._ws, 'btws_get_project_ps_{}'.format(get.path), True)
                    get._ws.send(json.dumps(self.wsResult(
                        True,
                        data=compose_list,
                    )))

                time.sleep(2)
        except Exception as e:
            return public.returnResult(False, str(e))

    # 2024/11/11 14:34 获取所有正在运行的容器信息和已安装的应用信息
    def get_some_info(self, get):
        '''
            @name 获取所有正在运行的容器信息和已安装的应用信息
        '''
        get.type = get.get("type", "container")
        if not get.type in ("container", "app"):
            return public.returnResult(status=False, msg="仅支持container和app两种类型")

        if get.type == "container":
            from btdockerModel.dockerSock import container
            sk_container = container.dockerContainer()
            sk_container_list = sk_container.get_container()

            data = []
            for container in sk_container_list:
                if not "running" in container["State"]: continue

                port_list = []
                for p in container["Ports"]:
                    if not "PublicPort" in p: continue
                    if not p["PublicPort"] in port_list:
                        port_list.append(p["PublicPort"])

                data.append({
                    "id": container["Id"],
                    "name": container["Names"][0].replace("/", ""),
                    "status": container["State"],
                    "image": container["Image"],
                    "created_time": container["Created"],
                    "ports": port_list,
                })

            return public.returnResult(True, data=data)
        else:
            get.row = 10000
            installed_apps = self.get_installed_apps(get)
            not_allow_category = ("Database", "System")

            for app in installed_apps["data"]:
                if not "running" in app["status"]: installed_apps["data"].remove(app)
                if app["apptype"] in not_allow_category: installed_apps["data"].remove(app) if app in installed_apps["data"] else None

            return public.returnResult(status=installed_apps["status"], data=installed_apps["data"])

    def generate_apphub(self, get):
        '''
            @name 解析外部应用列表
            @author csj <2025/7/9>
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        return AppHub().generate_apphub(get)

    def create_app(self,get):
        '''
            @name 创建应用
            @author csj <2025/7/9>
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if get.get("appid","0") == "-1": # 从apphub创建应用
            self.templates_path = os.path.join(AppHub.hub_home_path, "templates")
            self.apps_json_file = os.path.join(AppHub.hub_home_path, "apps.json")

            version = get.get("version","latest")
            app_name = get.get("app_name","")

            if not os.path.exists(self.templates_path):
                os.makedirs(self.templates_path)

            #/www/dk_project/dk_app/apphub/apphub/templates/app_name/version
            app_version_path = os.path.join(AppHub.hub_home_path, app_name, version)
            if not os.path.exists(app_version_path):
                return public.returnMsg(False, "应用 {} 的版本 {} 不存在".format(app_name, version))

            # /www/dk_project/dk_app/apphub/apphub/templates/app_name
            app_template_path = os.path.join(self.templates_path, app_name)

            public.ExecShell("\cp -r {} {}".format(app_version_path,app_template_path))

        return super().create_app(get)

    def get_apphub_config(self, get):
        '''
            @name 获取apphub配置
            @author csj <2025/7/9>
            @return dict{"status":True/False,"data":{}}
        '''
        return public.returnResult(True,data=AppHub.get_config())

    def set_apphub_git(self,get):
        '''
            @name 设置外部应用的git地址
            @author csj <2025/7/9>
            @param get: git_url, git_branch, user, password
        '''
        if not hasattr(get, 'git_url') or not get.git_url:
            return public.returnMsg(False, "未设置git地址")
        if not hasattr(get, 'git_branch') or not get.git_branch:
            return public.returnMsg(False, "未设置分支名称")

        return AppHub().set_apphub_git(get)

    def import_git_apphub(self,get):
        '''
            @name 从git导入外部应用
            @author csj <2025/7/9>
        '''
        return AppHub().import_git_apphub(get)

    def install_apphub(self,get):
        '''
            @name 安装apphub所需环境
            @author csj <2025/7/9>
        '''
        return AppHub().install_apphub(get)

    def import_zip_apphub(self,get):
        '''
            @name 从zip包导入外部应用
            @author csj <2025/7/9>
            @param get: sfile: zip文件路径
        '''
        if not hasattr(get, 'sfile') or not get.sfile:
            return public.returnMsg(False, "未设置zip文件路径")

        return AppHub().import_zip_apphub(get)

    def parser_zip_apphub(self,get):
        '''
            @name 解析zip包
            @author csj <2025/7/9>
            @param get: sfile: zip文件路径
            @return dict{"status":True/False,"data":[]}
        '''
        if not hasattr(get, 'sfile') or not get.sfile:
            return public.returnMsg(False, "请选择文件路径")

        app_list = []
        files = get.sfile.split(',')
        for sfile in files:
            get.sfile = sfile

            apps = AppHub().parser_zip_apphub(get)
            app_list.extend(apps)
        return public.returnResult(True,data=app_list)

    def clean_apphub(self,get):
        '''
            @name 清理apphub缓存
            @author csj <2025/11/3>
        '''
        return AppHub().clean_apphub(get)

if __name__ == '__main__':
    pass
