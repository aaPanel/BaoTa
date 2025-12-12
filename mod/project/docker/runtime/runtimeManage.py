# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------
# ------------------------------
# docker模型 - docker runtime 业务类
# ------------------------------
import json
import os
import sys
import time

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public
from btdockerModel import dk_public as dp
from mod.project.docker.runtime.base import Runtime


class RuntimeManage(Runtime):

    def __init__(self):
        super(RuntimeManage, self).__init__()
        self.runtime_path = "/www/dk_project/runtime"
        self.runtime_templates_path = "{}/templates".format(self.runtime_path)
        self.exts_file = "{}/php/exts.json".format(self.runtime_templates_path)
        self.versions_file = "{}/versions.json".format(self.runtime_templates_path)
        self.service_templates_path = "{}/".format(self.runtime_templates_path) + "{}"
        self.runtime_build_path = "{}/build".format(self.runtime_path)
        if not os.path.exists(self.runtime_build_path): os.makedirs(self.runtime_build_path, 384, True)
        self.php_build_path = "{}/php".format(self.runtime_build_path)
        if not os.path.exists(self.php_build_path): os.makedirs(self.php_build_path, 384, True)
        self.runtime_run_path = "{}/run".format(self.runtime_path)
        self.service_run_path = "{}/".format(self.runtime_run_path) + "{}"
        self.site_path = "/www/dk_project/wwwroot"
        self.site_path_pl = "/www/dk_project/wwwroot.pl"
        if os.path.exists(self.site_path_pl):
            self.site_path = public.readFile(self.site_path_pl).strip()
        if not os.path.exists(self.site_path): os.makedirs(self.site_path, 384, True)

    # 2024/11/1 10:33 下载模板到指定目录
    def download_templates(self):
        '''
            @name 下载模板到指定目录
        '''
        if os.path.exists(self.runtime_templates_path):
            public.ExecShell("rm -rf {}".format(self.runtime_templates_path))

        app_url = "{}/src/dk_app/runtime/templates.zip".format(public.get_url())
        to_file = '/tmp/templates.zip'
        if os.path.exists(to_file): public.ExecShell("rm -f {}".format(to_file))
        public.downloadFile(app_url, to_file)
        if not os.path.exists(to_file) or os.path.getsize(to_file) < 10:
            return public.returnResult(False, msg="模板更新失败!")
        public.ExecShell("unzip -o -d {} {}".format(self.runtime_path, to_file))
        return public.returnResult(True, "模板更新成功!")

    # 2024/11/1 10:18 检查模板是否存在
    def check_templates(self, get):
        '''
            @name 检查模板是否存在
        '''
        get.force_update = int(get.get("force_update", 0))

        if get.force_update == 1:
            return self.download_templates()
        if not os.path.exists(self.runtime_templates_path):
            return self.download_templates()

    # 2024/11/1 09:16 构建指定的PHP镜像
    def build_php_image(self, get):
        '''
            @name 构建指定的PHP镜像
        '''
        self.service_templates_path = self.service_templates_path.format("php")
        self.project_path = "{}/{}".format(self.php_build_path, get.runtime_name)
        if not os.path.exists(self.project_path): os.makedirs(self.project_path, 384, True)
        self.compose_file = "{}/docker-compose.yml".format(self.project_path)
        self.build_log = "{}/build.log".format(self.project_path)
        public.ExecShell("rm -f {}".format(self.build_log))

        if get.runtime_version.startswith("8."):
            public.ExecShell("\cp -r {}/php8/* {}/".format(self.service_templates_path, self.project_path))
            public.ExecShell("\cp -r {}/php8/.env {}/".format(self.service_templates_path, self.project_path))

            if not os.path.exists(self.compose_file):
                return public.returnResult(False, msg="PHP8模板不存在")
        elif get.runtime_version.startswith("7."):
            if get.runtime_version in ("7.0", "7.1"):
                public.ExecShell("\cp -r {}/php70/* {}/".format(self.service_templates_path, self.project_path))
                public.ExecShell("\cp -r {}/php70/.env {}/".format(self.service_templates_path, self.project_path))
            else:
                public.ExecShell("\cp -r {}/php72/* {}/".format(self.service_templates_path, self.project_path))
                public.ExecShell("\cp -r {}/php72/.env {}/".format(self.service_templates_path, self.project_path))

            if not os.path.exists(self.compose_file):
                return public.returnResult(False, msg="PHP7模板不存在")
        elif get.runtime_version.startswith("5."):
            public.ExecShell("\cp -r {}/php5/* {}/".format(self.service_templates_path, self.project_path))
            public.ExecShell("\cp -r {}/php5/.env {}/".format(self.service_templates_path, self.project_path))

            if not os.path.exists(self.compose_file):
                return public.returnResult(False, msg="PHP5模板不存在")
        else:
            return public.returnResult(False, msg="PHP版本: 【{}】错误".format(get.runtime_version))

        exts = get.exts.replace(",", " ")
        public.ExecShell("sed -i 's/^VERSION=.*/VERSION={}/' {}/.env".format(get.runtime_version, self.project_path))
        public.ExecShell("sed -i 's/^REPO_URL=.*/REPO_URL={}/' {}/.env".format(get.repo_url, self.project_path))
        public.ExecShell("sed -i 's/^EXTS=.*/EXTS=\"{}\"/' {}/.env".format(exts, self.project_path))

        public.ExecShell("sed -i 's/btphp:/{}:/g' {}/.env".format(get.runtime_name, self.project_path))
        public.ExecShell("sed -i 's/btphp:/{}/g' {}/*.yml".format(get.runtime_name, self.project_path))

        cmd = ("nohup echo '正在构建【{runtime_name}】,可能需要等待1-5分钟以上...' >> {build_log};"
               "docker-compose -f {compose_file} build --progress=plain >> {build_log} 2>&1 && "
               "echo 'bt_successful' >> {build_log} || echo 'bt_failed' >> {build_log} &"
        .format(
            runtime_name=get.runtime_name,
            build_log=self.build_log,
            compose_file=self.compose_file,
        ))

        import subprocess
        subprocess.Popen(cmd, shell=True)

        public.set_module_logs('build_runtime_php', 'runtime_buildphp_{}'.format(get.runtime_version), 1)

    # 2024/11/6 16:01 运行指定php项目
    def run_php_project(self, get):
        '''
            @name 运行指定php项目
        '''
        self.service_templates_path = self.service_templates_path.format("php")
        run_php_templates_path = os.path.join(self.service_templates_path, "runphp")
        self.service_run_path = self.service_run_path.format("php")
        if not os.path.exists(self.service_run_path): os.makedirs(self.service_run_path, 384, True)
        get.project_name = get.site_name.replace(".", "_")
        self.project_path = "{}/{}".format(self.service_run_path, get.project_name)
        if not os.path.exists(self.project_path): os.makedirs(self.project_path, 384, True)
        self.compose_file = "{}/docker-compose.yml".format(self.project_path)
        self.create_log = "{}/create.log".format(self.project_path)

        get.php_version = get.name.split(":")[1]
        get.project_path = self.project_path
        if get.php_version.startswith("8."):
            public.ExecShell("\cp -r {}/php8/* {}/".format(run_php_templates_path, self.project_path))
            public.ExecShell("\cp -r {}/php8/.env {}/".format(run_php_templates_path, self.project_path))

            if not os.path.exists(self.compose_file):
                return public.returnResult(False, msg="PHP8模板不存在")
        elif get.php_version.startswith("7."):
            if get.php_version in ("7.0", "7.1"):
                public.ExecShell("\cp -r {}/php70/* {}/".format(run_php_templates_path, self.project_path))
                public.ExecShell("\cp -r {}/php70/.env {}/".format(run_php_templates_path, self.project_path))
            else:
                public.ExecShell("\cp -r {}/php72/* {}/".format(run_php_templates_path, self.project_path))
                public.ExecShell("\cp -r {}/php72/.env {}/".format(run_php_templates_path, self.project_path))

            if not os.path.exists(self.compose_file):
                return public.returnResult(False, msg="PHP7模板不存在")
        elif get.php_version.startswith("5."):
            public.ExecShell("\cp -r {}/php5/* {}/".format(run_php_templates_path, self.project_path))
            public.ExecShell("\cp -r {}/php5/.env {}/".format(run_php_templates_path, self.project_path))

            if not os.path.exists(self.compose_file):
                return public.returnResult(False, msg="PHP5模板不存在")
        else:
            return public.returnResult(False, msg="PHP版本: 【{}】错误".format(get.php_version))

        public.ExecShell("sed -i 's/^IMAGE_NAME=.*/IMAGE_NAME={}/' {}/.env".format(get.name, self.project_path))
        public.ExecShell(
            "sed -i 's/^WEB_HTTP_PORT=.*/WEB_HTTP_PORT={}/' {}/.env".format(get.runtime_port, self.project_path))
        public.ExecShell("sed -i 's,^SITE_PATH=.*,SITE_PATH={},' {}/.env".format(get.site_path, self.project_path))

        cmd = ("nohup echo '正在创建【{site_name}】,可能需要等待1-5分钟以上...' >> {build_log};"
               "docker-compose -f {compose_file} up -d >> {build_log} 2>&1 && "
               "echo 'bt_successful' >> {build_log} || echo 'bt_failed' >> {build_log} &"
        .format(
            site_name=get.site_name,
            build_log=self.create_log,
            compose_file=self.compose_file,
        ))

        import subprocess
        subprocess.Popen(cmd, shell=True)

        # public.set_module_logs('runtime_runphp_{}'.format(get.version), 'run_php', 1)
        return public.returnResult()

    # 2024/11/1 15:02 运行python项目
    def run_python_project(self, get):
        '''
            @name 运行python项目
        '''
        self.service_templates_path = self.service_templates_path.format("python")
        self.service_run_path = self.service_run_path.format("python")
        if not os.path.exists(self.service_run_path): os.makedirs(self.service_run_path, 384, True)
        self.project_path = "{}/{}".format(self.service_run_path, get.runtime_name)
        if not os.path.exists(self.project_path): os.makedirs(self.project_path, 384, True)
        self.compose_file = "{}/docker-compose.yml".format(self.project_path)
        self.create_log = "{}/create.log".format(self.project_path)
        public.ExecShell("rm -f {}".format(self.create_log))

        public.ExecShell("\cp -r {}/python3/* {}/".format(self.service_templates_path, self.project_path))
        public.ExecShell("\cp -r {}/python3/.env {}/".format(self.service_templates_path, self.project_path))

        if not os.path.exists(self.compose_file):
            return public.returnResult(False, msg="Python模板不存在")

        public.ExecShell("sed -i 's/^VERSION=.*/VERSION={}/' {}/.env".format(get.runtime_version, self.project_path))
        public.ExecShell("sed -i 's/^REPO_URL=.*/REPO_URL={}/' {}/.env".format(get.repo_url, self.project_path))
        public.ExecShell("sed -i 's,^SITE_PATH=.*,SITE_PATH={},' {}/.env".format(get.site_path, self.project_path))

        public.ExecShell("sed -i 's/btpython:/{}/g' {}/*.yml".format(get.runtime_name, self.project_path))
        port_conf = self.handle_ports(get.ports)
        public.ExecShell("sed -i 's,:BTPORT_CONF:,{},g' {}/*.yml".format(port_conf, self.project_path))

        try:
            import yaml
            import glob
            yaml_files = glob.glob("{}/*.yml".format(self.project_path))
            for yf in yaml_files:
                data = public.readFile(yf)
                if data:
                    data = yaml.safe_load(data)
                    data["services"]["{}-python3".format(get.runtime_name)]["environment"][1] = "COMMAND={}".format(get.command)
                    public.writeFile(yf, yaml.dump(data))
        except:
            public.ExecShell("sed -i 's/:COMMAND:/{}/g' {}/*.yml".format(get.command, self.project_path))

        cmd = ("nohup echo '正在创建【{runtime_name}】,可能需要等待1-5分钟以上...' >> {build_log};"
               "docker-compose -f {compose_file} up -d >> {build_log} 2>&1 && "
               "echo 'bt_successful' >> {build_log} || echo 'bt_failed' >> {build_log} &"
        .format(
            runtime_name=get.runtime_name,
            build_log=self.create_log,
            compose_file=self.compose_file,
        ))

        import subprocess
        subprocess.Popen(cmd, shell=True)

        public.set_module_logs('runtime_python', 'runtime_python_{}'.format(get.runtime_version), 1)

    # 2024/11/4 14:46 运行golang项目
    def run_go_project(self, get):
        '''
            @name 运行golang项目
        '''
        self.service_templates_path = self.service_templates_path.format("go")
        self.service_run_path = self.service_run_path.format("go")
        if not os.path.exists(self.service_run_path): os.makedirs(self.service_run_path, 384, True)
        self.project_path = "{}/{}".format(self.service_run_path, get.runtime_name)
        if not os.path.exists(self.project_path): os.makedirs(self.project_path, 384, True)
        self.compose_file = "{}/docker-compose.yml".format(self.project_path)
        self.create_log = "{}/create.log".format(self.project_path)
        public.ExecShell("rm -f {}".format(self.create_log))

        public.ExecShell("\cp -r {}/go/* {}/".format(self.service_templates_path, self.project_path))
        public.ExecShell("\cp -r {}/go/.env {}/".format(self.service_templates_path, self.project_path))

        if not os.path.exists(self.compose_file):
            return public.returnResult(False, msg="Golang模板不存在")

        public.ExecShell("sed -i 's/^VERSION=.*/VERSION={}/' {}/.env".format(get.runtime_version, self.project_path))
        public.ExecShell("sed -i 's,^SITE_PATH=.*,SITE_PATH={},' {}/.env".format(get.site_path, self.project_path))

        public.ExecShell("sed -i 's/btgo:/{}/g' {}/*.yml".format(get.runtime_name, self.project_path))
        port_conf = self.handle_ports(get.ports)
        public.ExecShell("sed -i 's,:BTPORT_CONF:,{},g' {}/*.yml".format(port_conf, self.project_path))

        try:
            import yaml
            import glob
            yaml_files = glob.glob("{}/*.yml".format(self.project_path))
            for yf in yaml_files:
                data = public.readFile(yf)
                if data:
                    data = yaml.safe_load(data)
                    data["services"]["{}-python3".format(get.runtime_name)]["environment"][1] = "COMMAND={}".format(get.command)
                    public.writeFile(yf, yaml.dump(data))
        except:
            public.ExecShell("sed -i 's/:COMMAND:/{}/g' {}/*.yml".format(get.command, self.project_path))

        cmd = ("nohup echo '正在创建【{runtime_name}】,可能需要等待1-5分钟以上...' >> {build_log};"
               "docker-compose -f {compose_file} up -d >> {build_log} 2>&1 && "
               "echo 'bt_successful' >> {build_log} || echo 'bt_failed' >> {build_log} &"
        .format(
            runtime_name=get.runtime_name,
            build_log=self.create_log,
            compose_file=self.compose_file,
        ))

        import subprocess
        subprocess.Popen(cmd, shell=True)

        public.set_module_logs('runtime_go', 'runtime_go_{}'.format(get.runtime_version), 1)

    # 2024/11/4 14:54 运行java项目
    def run_java_project(self, get):
        '''
            @name 运行java项目
        '''
        self.service_templates_path = self.service_templates_path.format("java")
        self.service_run_path = self.service_run_path.format("java")
        if not os.path.exists(self.service_run_path): os.makedirs(self.service_run_path, 384, True)
        self.project_path = "{}/{}".format(self.service_run_path, get.runtime_name)
        if not os.path.exists(self.project_path): os.makedirs(self.project_path, 384, True)
        self.compose_file = "{}/docker-compose.yml".format(self.project_path)
        self.create_log = "{}/create.log".format(self.project_path)
        public.ExecShell("rm -f {}".format(self.create_log))

        public.ExecShell("\cp -r {}/java/* {}/".format(self.service_templates_path, self.project_path))
        public.ExecShell("\cp -r {}/java/.env {}/".format(self.service_templates_path, self.project_path))

        if not os.path.exists(self.compose_file):
            return public.returnResult(False, msg="Java模板不存在")

        public.ExecShell("sed -i 's/^VERSION=.*/VERSION={}/' {}/.env".format(get.runtime_version, self.project_path))
        public.ExecShell("sed -i 's,^SITE_PATH=.*,SITE_PATH={},' {}/.env".format(get.site_path, self.project_path))

        public.ExecShell("sed -i 's/btjava:/{}/g' {}/*.yml".format(get.runtime_name, self.project_path))
        port_conf = self.handle_ports(get.ports)
        public.ExecShell("sed -i 's,:BTPORT_CONF:,{},g' {}/*.yml".format(port_conf, self.project_path))

        try:
            import yaml
            import glob
            yaml_files = glob.glob("{}/*.yml".format(self.project_path))
            for yf in yaml_files:
                data = public.readFile(yf)
                if data:
                    data = yaml.safe_load(data)
                    data["services"]["{}-python3".format(get.runtime_name)]["environment"][1] = "COMMAND={}".format(get.command)
                    public.writeFile(yf, yaml.dump(data))
        except:
            public.ExecShell("sed -i 's/:COMMAND:/{}/g' {}/*.yml".format(get.command, self.project_path))

        cmd = ("nohup echo '正在创建【{runtime_name}】,可能需要等待1-5分钟以上...' >> {build_log};"
               "docker-compose -f {compose_file} up -d >> {build_log} 2>&1 && "
               "echo 'bt_successful' >> {build_log} || echo 'bt_failed' >> {build_log} &"
        .format(
            runtime_name=get.runtime_name,
            build_log=self.create_log,
            compose_file=self.compose_file,
        ))

        import subprocess
        subprocess.Popen(cmd, shell=True)

        public.set_module_logs('runtime_java', 'runtime_java_{}'.format(get.runtime_version), 1)

    def run_nodejs_project(self, get):
        '''
            @name 运行nodejs项目
        '''
        self.service_templates_path = self.service_templates_path.format("nodejs")
        self.service_run_path = self.service_run_path.format("nodejs")
        if not os.path.exists(self.service_run_path): os.makedirs(self.service_run_path, 384, True)
        self.project_path = "{}/{}".format(self.service_run_path, get.runtime_name)
        if not os.path.exists(self.project_path): os.makedirs(self.project_path, 384, True)
        self.compose_file = "{}/docker-compose.yml".format(self.project_path)
        self.create_log = "{}/create.log".format(self.project_path)
        public.ExecShell("rm -f {}".format(self.create_log))
        public.ExecShell("\cp -r {}/nodejs/* {}/".format(self.service_templates_path, self.project_path))
        public.ExecShell("\cp -r {}/nodejs/.env {}/".format(self.service_templates_path, self.project_path))

        if not os.path.exists(self.compose_file):
            return public.returnResult(False, msg="Nodejs模板不存在")
        
        repo_url = '"{}"'.format(get.repo_url.replace("/","\\/"))
        public.ExecShell("sed -i 's/^VERSION=.*/VERSION={}/' {}/.env".format(get.runtime_version, self.project_path))
        public.ExecShell("sed -i 's/^REPO_URL=.*/REPO_URL={}/' {}/.env".format(repo_url, self.project_path))
        public.ExecShell("sed -i 's,^SITE_PATH=.*,SITE_PATH={},' {}/.env".format(get.site_path, self.project_path))

        public.ExecShell("sed -i 's/btnodejs:/{}/g' {}/*.yml".format(get.runtime_name, self.project_path))
        port_conf = self.handle_ports(get.ports)
        public.ExecShell("sed -i 's,:BTPORT_CONF:,{},g' {}/*.yml".format(port_conf, self.project_path))
        public.ExecShell("sed -i 's/:COMMAND:/{}/g' {}/*.yml".format(get.command, self.project_path))

        cmd = ("nohup echo '正在创建【{runtime_name}】,可能需要等待1-5分钟以上...' >> {build_log};"
               "docker-compose -f {compose_file} up -d >> {build_log} 2>&1 && "
               "echo 'bt_successful' >> {build_log} || echo 'bt_failed' >> {build_log} &"
        .format(
            runtime_name=get.runtime_name,
            build_log=self.create_log,
            compose_file=self.compose_file,
        ))

        import subprocess
        subprocess.Popen(cmd, shell=True)

        public.set_module_logs('runtime_nodejs', 'runtime_nodejs_{}'.format(get.runtime_version), 1)

    # 2024/11/1 15:29 处理端口配置信息
    def handle_ports(self, ports):
        '''
            @name 处理端口配置信息
        '''
        # {"2362/tcp":"6236","646/tcp":["127.0.0.1","734"]}
        ports = json.loads(ports)
        # 构造 - ${HOST_IP}:${WEB_HTTP_PORT}:${APP_PORT} 用在docker-compose.yml中
        ports_str = ""
        for port in ports:
            if ports_str != "" and not "\n" in ports_str:
                ports_str += "\\n"
            ports_str += "      - "
            if isinstance(ports[port], list):
                if "tcp/udp" in port:
                    ports_str += "127.0.0.1:{}:{}".format(ports[port][1], port.split("/")[0])
                else:
                    ports_str += "127.0.0.1:{}:{}".format(ports[port][1], port)
            else:
                if "tcp/udp" in port:
                    ports_str += "0.0.0.0:{}:{}".format(ports[port], port.split("/")[0])
                else:
                    ports_str += "0.0.0.0:{}:{}".format(ports[port], port)
        return ports_str

    # 2024/11/20 10:11 添加默认的PHP扩展模板
    def add_default_php_ext_template(self):
        '''
            @name 添加默认的PHP扩展模板
        '''
        ext_templates = {
            "wordpress": "exif,igbinary,imagick,intl,apcu,memcached,opcache,shmop,mysqli,pdo_mysql,gd",
            "flarum": "curl,gd,pdo_mysql,mysqli,bz2,exif,yaf,imap",
            "苹果CMS-V10": "mysqli,pdo_mysql,zip,gd,redis,memcache,memcached",
            "SeaCMS": "mysqli,pdo_mysql,gd,curl",
        }
        top_php = "8.3"
        if os.path.exists(self.versions_file):
            try:
                top_php = json.loads(public.readFile(self.versions_file))["php"][0]
            except:
                pass

        for name in ext_templates.keys():
            args = public.dict_obj()
            args.exts = ext_templates[name]
            args.name = "{}_{}".format(name, top_php)
            args.version = top_php
            self.create_php_ext_template(args)
            args.name = "{}_7.4".format(name)
            args.version = "7.4"
            self.create_php_ext_template(args)

    # 2024/10/31 10:29 获取指定运行环境列表
    def get_runtime_list(self, get):
        '''
            @name 获取指定运行环境列表
        '''
        get.runtime_type = get.get("runtime_type", "all")
        get.p = get.get("p", 1)
        get.row = get.get("row", 10)

        if not os.path.exists(self.exts_file):
            self.check_templates(get)

        from mod.project.docker.app.base import App
        cbnet = App().check_baota_net()
        if not cbnet["status"]: return cbnet

        if get.runtime_type == "all":
            all_runtime_list = dp.sql('runtime').order('addtime desc').select()
        else:
            all_runtime_list = dp.sql('runtime').where('type=?', get.runtime_type).order('addtime desc').select()

        all_runtime_list = self.check_runtime_status(all_runtime_list)
        all_runtime_list = self.get_page(all_runtime_list, get)

        return self.pageResult(data=all_runtime_list["data"], page=all_runtime_list["page"])

    # 2024/11/1 11:40 检查运行环境的状态
    def check_runtime_status(self, all_runtime_list):
        '''
            @name 检查运行环境的状态
        '''
        from btdockerModel.dockerSock import image
        sk_image = image.dockerImage()
        all_images = sk_image.get_images()
        for runtime in all_runtime_list:
            runtime["status"] = "abnormal"
            if runtime["type"] == "php":
                stdout, stderr = public.ExecShell("grep 'bt_successful' {}".format(runtime["log_file"]))
                if not stdout:
                    runtime["status"] = "initializing"
                    stdout, stderr = public.ExecShell("grep 'bt_failed' {}".format(runtime["log_file"]))
                    if stdout:
                        runtime["status"] = "abnormal"
                    continue

                # 检查是否存在 runtime["name"]:runtime["version"]的镜像
                for image in all_images:
                    if "{}:{}".format(runtime["name"], runtime["version"]) in image["RepoTags"]:
                        runtime["status"] = "normal"
                        break
            elif runtime["type"] in ["java", "go", "python","nodejs"]:
                runtime["status"] = "running"
                # 检查是否存在运行中的容器
                stdout, stderr = public.ExecShell(
                    "docker-compose -f {} ps --format ".format(runtime["compose"]) + "\"{{.State}}\"")
                runtime["status"] = stdout.strip() if stdout.strip() else "exited"

        return all_runtime_list

    # 2024/10/31 10:30 创建指定运行环境
    def create_runtime(self, get):
        '''
            @name 创建指定运行环境
        '''
        get.runtime_name = get.get("runtime_name", None)
        if get.runtime_name is None: return public.returnResult(False, msg="请传运行环境名称：runtime_name")
        get.runtime_type = get.get("runtime_type", None)
        if get.runtime_type is None: return public.returnResult(False, msg="请传运行环境类型：runtime_type")
        get.runtime_version = get.get("runtime_version", None)
        if get.runtime_version is None: return public.returnResult(False, msg="请传运行环境版本：runtime_version")
        get.remark = get.get("remark", "")

        if get.runtime_type in ["php", "python","nodejs"]:
            get.repo_url = get.get("repo_url", None)
            if get.repo_url is None: return public.returnResult(False, msg="请传源加速地址：repo_url")
            get.exts = get.get("exts", None)
        if get.runtime_type in ["java", "go", "python","nodejs"]:
            get.site_path = get.get("site_path", None)
            if get.site_path is None: return public.returnResult(False, msg="请传站点路径：site_path")
            get.command = get.get("command", None)
            if get.command is None: return public.returnResult(False, msg="请传启动命令：command")
            get.ports = get.get("ports", None)
            if get.ports is None: return public.returnResult(False, msg="请传端口映射：ports")
            posts_dict = json.loads(get.ports)
            get.ports_dict = {}
            for p in posts_dict.keys():
                if type(posts_dict[p]) == list:
                    get.ports_dict[p] = [{"HostIp": posts_dict[p][0], "HostPort": posts_dict[p][1]}]
                else:
                    get.ports_dict[p] = [{"HostIp": "0.0.0.0", "HostPort": posts_dict[p]}]

        find_result = dp.sql("runtime").where("name=? and type=?", (get.runtime_name, get.runtime_type)).find()
        if find_result:
            return public.returnResult(False, msg="运行环境【{}】已存在,请更换其他名称!".format(get.runtime_name))

        self.check_templates(get)
        public.set_module_logs('runtime'.format(get.runtime_version), 'create_runtime', 1)

        if get.runtime_type == "php":
            self.build_php_image(get)

            dp.sql("runtime").insert({
                "name": get.runtime_name,
                "type": get.runtime_type,
                "version": get.runtime_version,
                "repo_url": get.repo_url,
                "exts": get.exts,
                "addtime": int(time.time()),
                "runtime_path": self.project_path,
                "compose": self.compose_file,
                "log_file": self.build_log,
                "remark": public.xssencode2(get.remark)
            })
        else:
            if get.runtime_type == "python":
                self.run_python_project(get)
            elif get.runtime_type == "go":
                self.run_go_project(get)
            elif get.runtime_type == "java":
                self.run_java_project(get)
            elif get.runtime_type == "nodejs":
                self.run_nodejs_project(get)

            dp.sql("runtime").insert({
                "name": get.runtime_name,
                "type": get.runtime_type,
                "version": get.runtime_version,
                "repo_url": get.get('repo_url',''),
                "path": get.site_path,
                "command": get.command,
                "ports": json.dumps(get.ports_dict),
                "addtime": int(time.time()),
                "runtime_path": self.project_path,
                "compose": self.compose_file,
                "log_file": self.create_log,
                "remark": public.xssencode2(get.remark)
            })
        return public.returnResult(msg="创建运行环境【{}】成功".format(get.runtime_name))

    # 2024/11/19 11:59
    def remove_image(self, get):
        '''
            @name
        '''
        image_name = "{}:{}".format(get.runtime_name, get.runtime_version)
        stdout, stderr = public.ExecShell("docker ps -a |grep {}".format(image_name))
        if stdout: return False

        public.ExecShell("docker image rm -f {}".format(image_name))
        return True

    # 2024/10/31 10:33 编辑指定运行环境
    def modify_runtime(self, get):
        '''
            @name 编辑指定运行环境
        '''
        get.id = get.get("id", None)
        if get.id is None: return public.returnResult(False, msg="请传运行环境ID：id")
        get.runtime_name = get.get("runtime_name", None)
        if get.runtime_name is None: return public.returnResult(False, msg="请传运行环境名称：runtime_name")
        get.runtime_type = get.get("runtime_type", None)
        if get.runtime_type is None: return public.returnResult(False, msg="请传运行环境类型：runtime_type")
        get.runtime_version = get.get("runtime_version", None)
        if get.runtime_version is None: return public.returnResult(False, msg="请传运行环境版本：runtime_version")
        get.remark = get.get("remark", "")

        if get.runtime_type in ["php", "python"]:
            get.repo_url = get.get("repo_url", None)
            if get.repo_url is None: return public.returnResult(False, msg="请传代码仓库地址：repo_url")
            get.exts = get.get("exts", None)
        if get.runtime_type in ["java", "go", "python","nodejs"]:
            get.site_path = get.get("site_path", None)
            if get.site_path is None: return public.returnResult(False, msg="请传站点路径：site_path")
            get.command = get.get("command", None)
            if get.command is None: return public.returnResult(False, msg="请传启动命令：command")
            get.ports = get.get("ports", None)
            if get.ports is None: return public.returnResult(False, msg="请传端口映射：ports")

            posts_dict = json.loads(get.ports)
            get.ports_dict = {}
            for p in posts_dict.keys():
                if type(posts_dict[p]) == list:
                    get.ports_dict[p] = [{"HostIp": posts_dict[p][0], "HostPort": posts_dict[p][1]}]
                else:
                    get.ports_dict[p] = [{"HostIp": "0.0.0.0", "HostPort": posts_dict[p]}]

        find_result = dp.sql("runtime").where("id=? and type=?", (get.id, get.runtime_type)).find()
        if not find_result: return public.returnResult(False, msg="运行环境不存在")
        if not self.remove_image(get):
            return public.returnResult(False,
                                       msg="原删除镜像失败，请手动删除：{} 后再尝试编辑".format(find_result["name"]))

        if get.runtime_type == "php":
            self.build_php_image(get)

            dp.sql("runtime").where("id=? and type=?", (get.id, get.runtime_type)).update({
                "repo_url": get.repo_url,
                "exts": get.exts
            })
        else:
            if get.runtime_type == "python":
                self.run_python_project(get)
            elif get.runtime_type == "java":
                self.run_java_project(get)
            elif get.runtime_type == "nodejs":
                self.run_nodejs_project(get)
            elif get.runtime_type == "go":
                self.run_go_project(get)
            else:
                return public.returnResult(False, msg="不支持的运行环境类型：{}".format(get.runtime_type))


            dp.sql("runtime").where("id=? and type=?", (get.id, get.runtime_type)).update({
                "path": get.site_path,
                "repo_url": get.get("repo_url", ""),
                "command": get.command,
                "ports": json.dumps(get.ports_dict)
            })
        return public.returnResult(msg="编辑成功")

    # 2024/11/1 14:29 删除指定运行环境
    def delete_runtime(self, get):
        '''
            @name 删除指定运行环境
        '''
        get.id = get.get("id", None)
        if get.id is None: return public.returnResult(False, msg="请传运行环境ID：id")

        find_result = dp.sql("runtime").where("id=?", get.id).find()
        if not find_result: return public.returnResult(False, msg="运行环境不存在")

        if find_result["type"] == "php":
            public.ExecShell("docker-compose -f {} down".format(find_result["compose"]))
            public.ExecShell("docker-compose -f {} rm -f".format(find_result["compose"]))
            public.ExecShell("docker image rm -f {}:{}".format(find_result["name"], find_result["version"]))
            public.ExecShell("rm -rf {}".format(find_result["runtime_path"]))
        elif find_result["type"] in ["java", "go", "python"]:
            public.ExecShell("docker-compose -f {} down".format(find_result["compose"]))
            public.ExecShell("docker-compose -f {} rm -f".format(find_result["compose"]))
            public.ExecShell("rm -rf {}".format(find_result["runtime_path"]))

        dp.sql("runtime").where("id=?", get.id).delete()
        find_result = dp.sql("runtime").where("id=?", get.id).find()
        if find_result: return public.returnResult(False, msg="删除失败")

        return public.returnResult(msg="删除成功")

    # 2024/11/1 14:33 批量删除指定运行环境
    def batch_delete_runtime(self, get):
        '''
            @name 批量删除指定运行环境
        '''
        get.ids = get.get("ids", None)
        if get.ids is None: return public.returnResult(False, msg="请传运行环境ID：ids")

        get.ids = get.ids.split(",")

        delete_result = []
        for id in get.ids:
            find_result = dp.sql("runtime").where("id=?", id).find()
            if not find_result:
                delete_result.append({"id": id, "status": False, "msg": "运行环境不存在"})
                continue

            if find_result["type"] == "php":
                public.ExecShell("docker-compose -f {} down".format(find_result["compose"]))
                public.ExecShell("docker-compose -f {} rm -f".format(find_result["compose"]))
                public.ExecShell("docker image rm -f {}:{}".format(find_result["name"], find_result["version"]))
                public.ExecShell("rm -rf {}".format(find_result["runtime_path"]))
            elif find_result["type"] in ["java", "go", "python"]:
                public.ExecShell("docker-compose -f {} down".format(find_result["compose"]))
                public.ExecShell("docker-compose -f {} rm -f".format(find_result["compose"]))
                public.ExecShell("rm -rf {}".format(find_result["runtime_path"]))

            dp.sql("runtime").where("id=?", id).delete()
            find_result = dp.sql("runtime").where("id=?", id).find()
            if find_result:
                delete_result.append({"id": id, "status": False, "msg": "删除失败"})
                continue

            delete_result.append({"id": id, "status": True, "msg": "删除成功"})

        return public.returnResult(msg="批量删除成功", data=delete_result)

    # 2024/10/31 10:30 清理构建缓存
    def build_prune(self, get):
        '''
            @name 清理构建缓存
        '''
        from btdockerModel.dockerSock import image
        sk_image = image.dockerImage()
        sk_image.build_prune()
        get.force_update = 1
        self.check_templates(get)
        return public.returnResult(msg="清理所有构建缓存成功")

    # 2024/10/31 10:33 设置运行环境运行状态（仅java/go/python/nodejs）
    def set_runtime_status(self, get):
        '''
            @name 设置运行环境运行状态（仅java/go/python/nodejs）
        '''
        get.compose_file = get.get("compose_file", None)
        if get.compose_file is None: return public.returnResult(False, msg="请传compose文件路径：compose_file")
        get.runtime_status = get.get("runtime_status", None)
        if get.runtime_status is None: return public.returnResult(False, msg="请传运行状态：runtime_status")

        if not get.compose_file.endswith(".yml"): return public.returnResult(False, msg="compose文件路径错误")

        self.path = get.compose_file
        if get.runtime_status == "stop":
            cmd = self.get_compose_stop()
            opt_status = "停止"
        elif get.runtime_status == "start":
            cmd = self.get_compose_up()
            opt_status = "启动"
        elif get.runtime_status == "restart":
            cmd = self.get_compose_restart()
            opt_status = "重启"
        else:
            return public.returnResult(False, msg="运行状态【{}】错误".format(get.runtime_status))

        public.ExecShell(cmd)
        return public.returnResult(msg="{}成功".format(opt_status))

    # 2024/10/31 10:33 获取指定运行环境的日志
    def get_runtime_logs(self, get):
        '''
            @name 获取指定运行环境的日志
        '''
        get.log_type = get.get("log_type", "run")
        get.compose_file = get.get("compose_file", None)
        get.log_file = get.get("log_file", None)

        if get.log_type == "run":
            if get.compose_file is None:
                return public.returnResult(False, msg="请传compose文件路径：compose_file")
            command = self.set_type(0).set_path(get.compose_file).set_tail("500").get_tail_compose_log()
            stdout, stderr = public.ExecShell(command)
            return public.returnResult(True, data=stdout)
        else:
            if get.log_file is None:
                return public.returnResult(False, msg="请传日志文件路径：log_file")
            log_body = public.readFile(get.log_file)
            return public.returnResult(True, data=log_body)

    # 2024/10/31 10:33 获取运行环境版本信息
    def get_runtime_versions(self, get):
        '''
            @name 获取运行环境版本信息
        '''
        get.runtime_type = get.get("runtime_type", "all")
        if get.runtime_type == "": return public.returnResult(False, msg="请传运行环境类型：runtime_type")
        if not get.runtime_type in ("all", "php", "java", "go", "python","nodejs"):
            return public.returnResult(False, msg="运行环境类型【{}】错误，仅支持：all、php、java、go、python、nodejs".format(get.runtime_type))

        repo_urls = [
            {
                "name": "中国科技大学",
                "repo": "mirrors.ustc.edu.cn"
            },
            {
                "name": "网易",
                "repo": "mirrors.163.com"
            },
            {
                "name": "阿里云",
                "repo": "mirrors.aliyun.com"
            },
            {
                "name": "清华大学",
                "repo": "mirrors.tuna.tsinghua.edu.cn"
            }]

        versions = {
            "php": ["8.3", "8.2", "8.1", "8.0", "7.4", "7.3", "7.2", "7.1", "7.0", "5.6"],
            "java": ["22", "21", "17", "11", "1.8"],
            "go": ["1.22", "1.21"],
            "python": ["3.13", "3.12", "3.11", "3.10", "3.9", "3.8", "3.7"],
            "nodejs": ["25.1.0","25","24", "23", "22.21.1","21.7.3","20.19.5","18.20.8"],
            "repo_urls": repo_urls
        }

        if os.path.exists(self.versions_file):
            new_versions = public.readFile(self.versions_file)
            if new_versions:
                try:
                    new_versions = json.loads(new_versions)
                    if new_versions.get(get.runtime_type,"") != "":
                        versions = new_versions
                    else:
                        get.force_update = 1
                        self.check_templates(get)
                except:
                    pass

        if get.runtime_type != "all":
            versions = {get.runtime_type: versions.get(get.runtime_type, [])}
    
        if get.runtime_type == "nodejs":
            versions["repo_urls"] = [
                {"name": "淘宝源","repo": "https://registry.npmmirror.com/"},
                {"name": "阿里源","repo": "https://npm.aliyun.com/"},
                {"name": "网易源","repo": "https://mirrors.163.com/npm/"},
                {"name": "中国科学技术大学源","repo": "https://mirrors.ustc.edu.cn/npm/"},
                {"name": "清华大学源","repo": "https://mirrors.tuna.tsinghua.edu.cn/npm/"},
            ]
        else:
            versions["repo_urls"] = repo_urls

        return public.returnResult(data=versions)

    # 2024/10/31 10:34 获取扩展模板列表
    def get_php_ext_list(self, get):
        '''
            @name 获取扩展模板列表
        '''
        get.p = get.get("p", 1)
        get.row = get.get("row", 10)

        exts = dp.sql("ext_templates").select()
        page_data = self.get_page(exts, get)
        return self.pageResult(True, data=page_data["data"], page=page_data["page"])

    # 2024/10/31 15:56 获取所有支持的扩展列表
    def get_all_exts(self, get):
        '''
            @name 获取所有支持的扩展列表
        '''
        get.version = get.get("version", "all")
        if not os.path.exists(self.exts_file): self.check_templates(get)

        try:
            exts = json.loads(public.readFile(self.exts_file))
            if get.version != "all": exts = {get.version: exts.get(get.version, [])}

            return public.returnResult(data=exts)
        except:
            import traceback
            return public.returnResult(False, data={}, msg=traceback.format_exc())

    # 2024/10/31 10:34 创建扩展模板
    def create_php_ext_template(self, get):
        '''
            @name 创建扩展模板
        '''
        get.name = get.get("name", None)
        if get.name is None: return public.returnResult(False, msg="请传模板名称：name")

        get.version = get.get("version", None)
        if get.version is None: return public.returnResult(False, msg="请传模板版本：version")

        get.exts = get.get("exts", None)
        if get.exts is None: return public.returnResult(False, msg="请传模板扩展：exts")

        find_result = dp.sql("ext_templates").where("name=?", get.name).find()
        if find_result: return public.returnResult(False, msg="模板【{}】已存在,请更换其他名称!".format(get.name))

        dp.sql("ext_templates").insert({
            "name": get.name,
            "version": get.version,
            "exts": get.exts,
            "addtime": int(time.time())
        })
        return public.returnResult(msg="创建扩展【{}】成功".format(get.name))

    # 2024/10/31 10:34 删除指定扩展模板
    def delete_php_ext_template(self, get):
        '''
            @name 删除指定扩展模板
        '''
        get.id = get.get("id", None)
        if get.id is None: return public.returnResult(False, msg="请传模板ID：id")

        find_result = dp.sql("ext_templates").where("id=?", get.id).find()
        if not find_result: return public.returnResult(False, msg="模板不存在")

        dp.sql("ext_templates").where("id=?", get.id).delete()
        find_result = dp.sql("ext_templates").where("id=?", get.id).find()
        if find_result: return public.returnResult(False, msg="删除失败")

        return public.returnResult(msg="删除成功")

    # 2024/10/31 10:34 批量删除指定扩展模板
    def batch_delete_php_ext_template(self, get):
        '''
            @name 批量删除指定扩展模板
        '''
        get.ids = get.get("ids", None)
        if get.ids is None: return public.returnResult(False, msg="请传模板ID：ids")

        get.ids = get.ids.split(",")

        delete_result = []
        for id in get.ids:
            find_result = dp.sql("ext_templates").where("id=?", id).find()
            if not find_result:
                delete_result.append({"id": id, "status": False, "msg": "模板不存在"})
                continue

            dp.sql("ext_templates").where("id=?", id).delete()
            find_result = dp.sql("ext_templates").where("id=?", id).find()
            if find_result:
                delete_result.append({"id": id, "status": False, "msg": "删除失败"})
                continue

            delete_result.append({"id": id, "status": True, "msg": "删除成功"})

        return public.returnResult(msg="批量删除成功", data=delete_result)

    # 2024/10/31 10:35 编辑扩展模板
    def modify_php_ext_template(self, get):
        '''
            @name 编辑扩展模板
        '''
        get.id = get.get("id", None)
        if get.id is None: return public.returnResult(False, msg="请传模板ID：id")

        get.version = get.get("version", None)
        if get.version is None: return public.returnResult(False, msg="请传模板版本：version")

        get.exts = get.get("exts", None)
        if get.exts is None: return public.returnResult(False, msg="请传模板扩展：exts")

        find_result = dp.sql("ext_templates").where("id=?", get.id).find()
        if not find_result: return public.returnResult(False, msg="模板不存在")

        dp.sql("ext_templates").where("id=?", get.id).update({
            "version": get.version,
            "exts": get.exts
        })

        return public.returnResult(msg="编辑成功")
