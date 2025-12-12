# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: csj <csj@bt.cn>
# -------------------------------------------------------------------
# ------------------------------
# docker应用商店 apphub 业务类
# ------------------------------
import json
import os
import sys
import re
import time
from datetime import datetime, timedelta

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public
from mod.base.git_tool import GitTool
from mod.project.docker.app.base import App
import mod.base.git_tool.install as GitInstall

class AppHub():
    _instance = None
    hub_config_path = os.path.join(App.dk_project_path,'dk_app','apphub_config.json')   #/www/dk_project/dk_app/apphub_config.json
    hub_home_path = os.path.join(App.dk_project_path,'dk_app','apphub','apphub')        #/www/dk_project/dk_app/apphub/apphub
    hub_apps_path = os.path.join(hub_home_path,'apps.json')                             #/www/dk_project/dk_app/apphub/apphub/apps.json

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance") or cls._instance is None:
            cls._instance = super(AppHub, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_config(cls):
        '''
            @name 获取外部应用配置
        '''
        if not os.path.exists(cls.hub_config_path):
            apphub_config = {
                "git_config": {
                    "git_url": "",
                    "git_branch": "main",
                    "user_config": {
                        "name": "",
                        "password": ""
                    }
                }
            }
            public.writeFile(cls.hub_config_path, json.dumps(apphub_config))
        return json.loads(public.readFile(cls.hub_config_path))

    def install_apphub(self,get):

        git_install = GitInstall.install_git()
        if not git_install:
            return public.returnMsg(False, "安装git失败，请检查网络或手动安装git")

        return public.returnMsg(True, "环境安装成功")

    def get_hub_apps(self):
        '''
            @name 获取外部应用列表
        '''
        res = []
        try:
            if os.path.exists(AppHub.hub_apps_path):
                res=json.loads(public.readFile(self.hub_apps_path))
        except:
            pass
        return res

    def generate_apphub(self, get):
        '''
            @name 解析外部应用列表
        '''
        apps = []
        if not os.path.isdir(self.hub_home_path):
            return public.returnResult(False, "apphub目录不存在")
        for name in os.listdir(self.hub_home_path):
            app_dir = os.path.join(self.hub_home_path, name)
            if not os.path.isdir(app_dir): continue

            app_info=public.readFile(os.path.join(app_dir, 'app.json'))
            if not app_info: continue

            try:
                app_info = json.loads(app_info)
            except Exception as e:
                continue

            if "reuse" not in app_info: app_info["reuse"] = True
            if "icon" not in app_info: app_info["icon"] = ""
            if "sort" not in app_info: app_info["sort"] = 999
            if "cpu" not in app_info: app_info["cpu"] = 0
            if "mem" not in app_info: app_info["mem"] = 0
            if "disk" not in app_info: app_info["disk"] = 10240
            if "installed" not in app_info: app_info["installed"] = False
            if "updateat" not in app_info: app_info["updateat"] = 0

            apps.append(app_info)

        self.apphub_apps = apps

        public.writeFile(self.hub_apps_path, json.dumps(apps, indent=4, ensure_ascii=False))

        self.generate_apphub_icon()

        return public.returnMsg(True,"解析成功")

    def generate_apphub_icon(self):
        '''
            @name 创建外部应用图标
            #/static/img/soft_ico/apphub/ico-apphub_xxx.png
        '''
        apphub_ico_path = "{}/BTPanel/static/img/soft_ico/apphub/".format(public.get_panel_path())
        if os.path.exists(apphub_ico_path):
            public.ExecShell("rm -rf {}".format(apphub_ico_path))
        public.ExecShell("mkdir -p {}".format(apphub_ico_path))

        for name in os.listdir(self.hub_home_path):
            app_dir = os.path.join(self.hub_home_path, name,'icon.png')
            if not os.path.exists(app_dir): continue

            app_icon_path = os.path.join(apphub_ico_path, "ico-apphub_{}.png".format(name))
            public.ExecShell("cp {} {}".format(app_dir,app_icon_path))
        return True

    def set_apphub_git(self, get):
        '''
            @name 设置git配置
            @param get: git_url, git_branch, user, password
        '''
        config = self.get_config()
        git_config = config.get("git_config", {})
        git_config["git_url"] = get.git_url.strip()
        git_config["git_branch"] = get.git_branch.strip()
        if "name" in get and "password" in get:
            git_config["user_config"] = {
                "name": get.get("name", ""),
                "password": get.get("password", "")
            }
        config["git_config"] = git_config
        public.writeFile(self.hub_config_path, json.dumps(config, indent=4, ensure_ascii=False))
        return public.returnMsg(True, "git信息配置成功")

    def import_git_apphub(self,get):
        '''
            @name 从git导入外部应用
            @param None
        '''
        if not GitInstall.installed():
            return public.returnMsg(False, "缺少git环境，请先安装git")

        abs_path = os.path.dirname(self.hub_home_path)
        if not os.path.exists(abs_path): os.makedirs(abs_path)

        gitconfig = self.get_config()
        if not gitconfig or not gitconfig.get("git_config", {}).get("git_url", ""):
            return public.returnMsg(False, "请先设置git信息")

        git_url = gitconfig.get("git_config", {}).get("git_url", "")
        git_user = gitconfig.get("git_config", {}).get("user_config", {})
        git_branch = gitconfig.get("git_config", {}).get("git_branch", {})

        git = GitTool(project_path=abs_path, git_url=git_url,user_config=git_user,git_id="-1")
        public.ExecShell("rm -rf /tmp/git_-1_log.log")
        res = git.pull(git_branch)

        if res is not None:
            return public.returnMsg(False, "从git导入失败")

        #解析全部应用
        res = self.generate_apphub(get)
        if not res["status"]:
            return public.returnMsg(False, res["msg"])
        #删除模板
        public.ExecShell("rm -rf {}".format(os.path.join(AppHub.hub_home_path, "templates")))

        public.set_module_logs('apphub', 'import_git_apphub', 1)
        return public.returnMsg(True, "从git导入成功")

    def import_zip_apphub(self, get):
        '''
            @name 从压缩到包导入外部应用
            @param get: sfile: zip文件路径
        '''
        sfile = get.sfile.strip()
        files = sfile.split(",")

        for sfile in files:

            if not sfile.endswith(('.zip', '.gz')):
                return public.returnMsg(False, "文件格式不正确，请选择zip或gz文件")

            if not os.path.exists(self.hub_home_path):
                os.makedirs(self.hub_home_path)

            if sfile.endswith('.zip'):
                res, err = public.ExecShell("unzip -o {} -d {}".format(sfile, self.hub_home_path))
            elif sfile.endswith('.gz'):
                res, err = public.ExecShell("tar -xzvf {} -C {}".format(sfile, self.hub_home_path))
            else:
                err = "{},不支持的文件格式".format(sfile)

            if err:
                return public.returnMsg(False, "导入失败: " + str(err))

            res = self.generate_apphub(get)
            if not res["status"]:
                return public.returnMsg(False, res["msg"])

        public.set_module_logs('apphub', 'import_zip_apphub', 1)

        return public.returnMsg(True, "导入成功")

    def parser_zip_apphub(self, get):
        '''
            @name 解析zip包
            @param get: sfile: zip文件路径
            @return app_list: 外部应用列表
        '''
        sfile = get.sfile.strip()

        app_list = []

        from mod.project.docker.apphub.tool import GzHandler, ZipHandler
        if sfile.endswith(".gz"):
            handler = GzHandler()
        else:
            handler = ZipHandler()

        files = handler.get_files(sfile)

        if 'status' in files:
            return public.returnMsg(False, files['msg'])

        for file, file_struck in files.items():
            if 'app.json' in file_struck and file_struck['app.json']['is_dir'] == 0:

                filename = file_struck['app.json']['fullpath']

                appinfo = handler.get_file_info(sfile, filename)
                if 'status' in appinfo and appinfo['status'] == False:
                    return public.returnMsg(False, appinfo['msg'])

                try:
                    appinfo = json.loads(appinfo['data'])
                    appinfo["parser_from"] = sfile
                    app_list.append(appinfo)
                except:
                    pass

        return app_list

    def clean_apphub(self, get):
        '''
            @name 清理应用缓存
            @param None
        '''
        public.ExecShell("rm -rf {}".format(self.hub_home_path))
        return public.returnMsg(True, "清理成功")