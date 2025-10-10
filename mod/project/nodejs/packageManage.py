# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------
# ------------------------------
# nodejs模型 - 依赖包管理
# ------------------------------
import json
import sys

from mod.project.nodejs.base import NodeJs
from mod.project.nodejs.utils import test_registry_url

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public


class PackageManage(NodeJs):

    def __init__(self):
        super(PackageManage, self).__init__()

    # 2024/7/11 上午11:52 安装依赖包
    def install_package(self, get, manager: str = "npm",
                        package_name: str = None,
                        path: str = None,
                        is_global: bool = False,
                        force: bool = False,
                        check_update: bool = False,
                        *args, **kwargs):
        '''
            @name 安装依赖包
            @param manager:
            @param package_name string 依赖包名称
            @param path string 项目路径
            @param is_global:
            @param force:
            @param check_update:
        '''
        import os
        if path is None:
            self.ws_err_exit(False, 'path参数不能为空', code=2)

        get._ws.send(json.dumps(self.wsResult(
            True,
            "开始安装依赖包...",
            code=1
        )))

        # node_modules_path = '{}/node_modules'.format(path)
        lock_file = ("package-lock.json", "yarn.lock", "pnpm-lock.yaml")
        for lock in lock_file:
            if os.path.exists("{}/{}".format(path, lock)):
                public.ExecShell("rm -f {}/{}".format(path, lock))

        self.set_nodejs_version(get.nodejs_version).set_nodejs_bin().set_manager(manager).get_strict_ssl()
        self.set_install_logs(get.project_name)
        public.ExecShell("echo -n > {}".format(self.install_logs_file))
        public.ExecShell(self.set_strict_ssl)

        get._ws.send(json.dumps(self.wsResult(
            True,
            "开始检查可用镜像源...",
            code=1
        )))

        registry_name, registry_url = test_registry_url()
        if registry_url is None:
            get._ws.send(json.dumps(self.wsResult(
                True,
                "检测到镜像源不可用，这可能会导致后续安装执行失败!",
                code=1
            )))
        else:
            get._ws.send(json.dumps(self.wsResult(
                True,
                "检测到可用镜像源: {}".format(registry_name),
                code=1
            )))
            public.ExecShell("{}/{} config set registry {}".format(self.nodejs_bin, self.manager, registry_url))

        command = self.get_install_cmd(
            package_name=package_name,
            is_global=is_global,
            force=force,
            check_update=check_update,
            *args, **kwargs
        )

        self.exec_logs(get, command, path, write_log=True)

        get._ws.send(json.dumps(self.wsResult(
            True,
            "依赖包安装结束...如果项目启动失败，请检查安装日志！",
            code=0
        )))
