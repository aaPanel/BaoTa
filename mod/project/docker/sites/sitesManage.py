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
import re
import time
from datetime import datetime, timedelta

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public
from btdockerModel import dk_public as dp
from mod.project.docker.sites.base import Sites


class SitesManage(Sites):

    def __init__(self):
        super(SitesManage, self).__init__()
        self.enable_php_template = '''
location ~ [^/]\.php(/|$) {{
    if (!-f $document_root$fastcgi_script_name) {{
        return 404;
    }}
    fastcgi_pass 127.0.0.1:{port};
    include fastcgi.conf;
    include fastcgi_params;
    fastcgi_index index.php;

    set $real_script_name $fastcgi_script_name;
    if ($fastcgi_script_name ~ "^(.+?\.php)(/.+)$") {{
        set $real_script_name $1;
        set $path_info $2;
    }}
    fastcgi_param SCRIPT_FILENAME $document_root$real_script_name;
    fastcgi_param SCRIPT_NAME $real_script_name;
    fastcgi_param PATH_INFO $path_info;
}}'''


    # 2024/11/6 10:44 运行指定php环境
    def run_php(self, get):
        '''
            @name 运行指定php环境
        '''
        # 2024/11/6 10:44 查询是否存在指定版本的docker image
        from btdockerModel.dockerSock import image
        sk_image = image.dockerImage()
        img_inspect = sk_image.inspect(get.name)
        if not img_inspect:
            return public.returnResult(False, msg="未找到指定的php环境镜像！")

        # 2024/11/6 10:45 运行指定php环境
        from mod.project.docker.runtime.runtimeManage import RuntimeManage
        runtimeManage = RuntimeManage()
        run_result = runtimeManage.run_php_project(get)
        if not run_result["status"]: return run_result

        return public.returnResult(True)

    # 2024/10/29 17:45 获取所有Docker网站项目列表
    def get_site_list(self, get):
        '''
            @name 获取所有Docker网站项目列表
        '''
        get.type = get.get("type", "all")
        if not get.type in ("php", "java", "go", "python", "proxy", "app", "all","nodejs"):
            return public.returnResult(False, msg="type仅支持php、java、go、python、proxy、app、all")

        if not os.path.exists("{}/synced_docker_sites.pl".format(self.sites_config_path)):
            args = public.dict_obj()
            self.sync_docker_sites(args)

        if not os.path.exists("{}/init_exts_templates.pl".format(self.sites_config_path)):
            exts = dp.sql("ext_templates").select()
            if not exts:
                from mod.project.docker.runtime.runtimeManage import RuntimeManage
                runtimeManage = RuntimeManage()
                runtimeManage.download_templates()
                runtimeManage.add_default_php_ext_template()
                public.writeFile("{}/init_exts_templates.pl".format(self.sites_config_path), "init exts templates")

        get.query = get.get("query", "")
        get.p = get.get("p", 1)
        get.row = get.get("row", 10)
        get.classify = get.get("classify", 999)
        where_parm = [None, (None,)]

        if get.type == "all":
            if get.classify != 999:
                where_parm = ["classify=?", (get.classify,)]
                if get.query == "":
                    sites_result = dp.sql("docker_sites").where(where_parm[0], where_parm[1]).order("addtime desc").select()
                else:
                    where_parm[0] = "classify=? and (name like ? or remark like ?)"
                    where_parm[1] = (get.classify, "%{}%".format(get.query), "%{}%".format(get.query))
                    sites_result = dp.sql("docker_sites").where(where_parm[0], where_parm[1]).order("addtime desc").select()
            else:
                if get.query == "":
                    sites_result = dp.sql("docker_sites").order("addtime desc").select()
                else:
                    where_parm[0] = "name like ? or remark like ?"
                    where_parm[1] = ("%{}%".format(get.query), "%{}%".format(get.query))
                    sites_result = dp.sql("docker_sites").where(where_parm[0], where_parm[1]).order("addtime desc").select()
        else:
            where_parm[0] = "type=?"
            where_parm[1] = (get.type,)
            if get.classify != 999:
                where_parm[0] = "type=? and classify=?"
                where_parm[1] = (get.type, get.classify)
            if get.query == "":
                sites_result = dp.sql("docker_sites").where(where_parm[0], where_parm[1]).order("addtime desc").select()
            else:
                where_parm[0] = "type=? and classify=? and (? in name or ? in remark)"
                where_parm[1] = (get.type, get.classify, get.query, get.query)
                sites_result = dp.sql("docker_sites").where(where_parm[0], where_parm[1]).order("addtime desc").select()

        sites_result = self.get_page(sites_result, get)

        try:
            path = '/www/server/btwaf/site.json'
            waf_res = json.loads(public.readFile(path))
        except:
            waf_res = {}

        type_infp = {
            "php": "PHP",
            "java": "JAVA",
            "go": "Go",
            "python": "Python",
            "proxy": "反向代理",
            "app": "Docker应用",
            "nodejs": "Nodejs"
        }

        for site in sites_result["data"]:
            site["type"] = type_infp[site["type"]]
            get.site_name = site["name"]
            project_config = self.read_json_conf(get)
            site["healthy"] = 1
            site["waf"] = {}
            if not project_config:
                site["healthy"] = 0
                site["conf_path"] = ""
                site["ssl"] = -1
                site["proxy_pass"] = ""
                continue

            site["conf_path"] = public.get_setup_path() + '/panel/vhost/nginx/' + get.site_name + '.conf'
            site["ssl"] = self.get_site_ssl_info(get.site_name)
            site["proxy_pass"] = project_config["proxy_info"][0]["proxy_pass"] if len(project_config["proxy_info"]) > 0 else ""

            if waf_res:
                for waf in waf_res:
                    if "open" in waf_res[waf]:
                        site["waf"] = {"status": True}

        return self.pageResult(data=sites_result["data"], page=sites_result["page"])

    # 2024/10/29 18:00 创建指定类型的网站项目
    def create_site(self, get):
        '''
            @name 创建指定类型的网站项目
        '''
        get.domains = get.get("domains", "")
        if not get.domains:
            return public.returnResult(status=False, msg="域名不能为空，至少输入一个域名！")
        get.remark = get.get("remark", "")

        get.domain_list = get.domains.split("\n") if get.domains != "" else []
        # get.domain_list = json.loads(get.domains) if get.domains != "" else []
        get.site_port = get.domain_list[0].strip().split(":")[1] if ":" in get.domain_list[0] else "80"
        get.port_list = [get.site_port]
        from mod.base.web_conf import util
        get.domain_name = get.site_name = util.to_puny_code(get.domain_list[0].strip().split(":")[0]).strip().lower()
        public.check_domain_cloud(get.site_name)
        if get.domain_name.find("*.") != -1: return public.returnResult(False, "主域名不能是通配符域名！")

        cwsres = self.check_web_status()
        if not cwsres["status"]: return cwsres

        from firewallModel.comModel import main as comModel
        firewall_com = comModel()

        get.type = get.get("type", None)
        if get.type is None: return public.returnResult(False, "type参数不能为空！")
        get.name = get.get("name", None)
        if get.name is None: return public.returnResult(False, "name参数不能为空！")

        get.proxy_path = get.get("proxy_path", "/")
        get.runtime_port = None
        get.enable_php_conf = ""
        get.port = get.get("port", None)
        get.runtime_port = get.port
        get.project_name = None
        get.project_path = None
        get.container_id = get.get("container_id", None)
        if get.port is None: return public.returnResult(False, "port参数不能为空！")

        if get.type == "php":

            # 2024/11/6 11:08 检查端口是否占用
            import psutil
            all_ports = []
            for net_port in psutil.net_connections("tcp4"):
                all_ports.append(net_port.laddr.port)

            if int(get.runtime_port) in all_ports:
                get.port = str(get.runtime_port)
                from safeModel.firewallModel import main as firewall_main
                res_dict = firewall_main().get_listening_processes(get)
                return public.returnResult(False, msg="{}端口已被【{}】占用,请更换端口!".format(get.port, res_dict.get("process_name")))

            run_result = self.run_php(get)
            if not run_result["status"]: return run_result

            # 2024/11/6 17:23 写入nginx连接php-fpm的配置文件
            enable_php_body = public.readFile("/www/dk_project/runtime/templates/php/enable_php_template.conf")
            if enable_php_body: self.enable_php_template = enable_php_body
            get.enable_php_conf = self.enable_php_template.format(port=get.runtime_port)

        elif get.type in ("java", "go", "python", "app", "proxy","nodejs"):

            get.proxy_pass = get.get("proxy_pass", "http://127.0.0.1:{}".format(get.port))
            get.proxy_host = get.get("proxy_host", "$http_host")
            get.proxy_type = "http"
        else:
            return public.returnResult(False, "type参数: {} 不支持！".format(get.type))

        if get.site_port != "80":
            get.domain_name = "{}_{}".format(get.domain_name, get.site_port)
            get.site_path = get.get("site_path", "/www/dk_project/wwwroot/{}".format(get.domain_name))
            cache_name = "{}_{}".format(get.site_name.replace(".", "_"), get.site_port)
        else:
            get.site_path = get.get("site_path", "/www/dk_project/wwwroot/{}".format(get.site_name))
            cache_name = get.site_name.replace(".", "_")

        if dp.sql("docker_sites").where("name=?", (get.domain_name,)).count():
            return public.returnResult(False, "域名【{}】已存在，请勿重复添加！".format(get.domain_name))

        for domain in get.domain_list:
            domain = domain.strip().split(":")[0]
            if not public.is_domain(domain):
                return public.returnResult(False, "域名【{}】格式不正确".format(domain))

            newpid = public.M('domain').where("name=? and port=?", (domain, 80)).getField('pid')
            if newpid:
                result = public.M('sites').where("id=?", (newpid,)).find()
                if result:
                    return public.returnResult(False, '项目类型【{}】已存在域名：{}，请勿重复添加！'.format(
                        result['project_type'], domain))

            newpid = dp.sql("docker_domain").where("name=? and port=?", (domain, 80)).getField('pid')
            if newpid:
                result = dp.sql("docker_sites").where("id=?", (newpid,)).find()
                if result:
                    return public.returnResult(False, 'docker网站项目【{}】已存在域名：{}，请勿重复添加！'.format(result['name'], domain))

            if not ":" in domain.strip(): continue

            d_port = domain.strip().split(":")[1]
            if not public.checkPort(d_port):
                return public.returnResult(status=False, msg='端口【{}】不合法！'.format(d_port))

            get.port = d_port
            firewall_com.set_port_rule(get)

        self.site_config_path = os.path.join(self.sites_config_path, get.domain_name)
        # 2024/4/18 上午10:46 写入网站配置文件
        get.http_block = "proxy_cache_path {site_config_path}/proxy_cache_dir levels=1:2 keys_zone={cache_name}_cache:20m inactive=1d max_size=5g;".format(
            site_config_path=self.site_config_path,
            cache_name=cache_name
        )

        get.service_info = {
            "name": get.name,
            "port": get.runtime_port,
            "project_name": get.project_name,
            "project_path": get.project_path,
        }
        get.old_info = {}

        get.remark = public.xssencode2(get.get("remark", ""))
        if get.remark == "":
            get.remark = get.domain_name

        # 2024/4/18 上午10:22 写入数据库
        ires = self.insert_sites(get)
        if not ires["status"]: return ires

        # 2024/6/4 下午4:30 写nginx配置文件
        self.write_nginx_conf(get)

        # 2024/11/8 15:32 创建比网站相关目录和默认文档
        self.create_must_dir(get)
        self.create_default_html(get)

        self.site_conf_file = '{}/{}.json'.format(self.site_config_path, get.domain_name)
        public.writeFile(self.site_conf_file, json.dumps(self.init_site_json))

        cres = self.check_after_create(get)
        if not cres["status"]: return cres

        # 2024/11/19 11:48 开启防跨站
        get.id = get.pid
        get.status = 1
        self.SetDirUserINI(get)

        public.WriteLog('TYPE_SITE', 'SITE_ADD_SUCCESS', (get.site_name,))
        public.set_module_logs('docker_site', 'create', 1)
        public.set_module_logs('docker_site_{}'.format(get.type), 'create', 1)
        public.serviceReload()

        return public.returnResult(msg="创建网站成功")

    # 2024/10/31 10:04 设置指定网站的备注
    def set_remak(self, get):
        '''
            @name 设置指定网站的备注
        '''
        get.remark = get.get("remark", "")
        get.id = get.get("id", None)
        if get.id is None: return public.returnResult(False, "id参数不能为空！")
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        dp.sql("docker_sites").where("id=?", (get.id,)).setField("remark", public.xssencode2(get.remark))

        get.proxy_json_conf["remark"] = public.xssencode2(get.remark)
        self._site_proxy_conf_path = "{path}/{site_name}/{site_name}.json".format(
            path=self.sites_config_path,
            site_name=get.site_name
        )
        public.writeFile(self._site_proxy_conf_path, json.dumps(get.proxy_json_conf))

        return public.returnResult(msg="修改备注成功")

    # 2024/10/31 10:05 设置网站到期时间
    def set_site_edate(self, get):
        '''
            @name 设置网站到期时间
        '''
        get.edate = get.get("edate", "0000-00-00")
        get.id = get.get("id", None)
        if get.id is None: return public.returnResult(False, "id参数不能为空！")

        dp.sql("docker_sites").where("id=?", (get.id,)).setField("edate", get.edate)
        return public.returnResult(msg="设置到期时间成功")

    # 2024/10/31 10:05 设置网站运行状态
    def set_site_status(self, get):
        '''
            @name 设置网站运行状态
        '''
        get.status = get.get("status", 1)
        get.id = get.get("id", None)
        if get.id is None: return public.returnResult(False, "id参数不能为空！")
        get.site_name = get.get("site_name", None)
        if get.site_name is None: return public.returnResult(False, "site_name参数不能为空！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            old_file = "{path}/{site_name}/{site_name}.json".format(
                path="/www/server/proxy_project/sites",
                site_name=get.site_name
            )
            if not os.path.exists(old_file):
                return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

            os.makedirs("{}/{}".format(self.sites_config_path, get.site_name), exist_ok=True)
            public.ExecShell("\cp -r {} {}".format(old_file, os.path.join(self.sites_config_path, get.site_name)))
            get.proxy_json_conf = self.read_json_conf(get)
            if not get.proxy_json_conf:
                return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        if int(get.status) == 1:
            get.proxy_json_conf["stop_site"] = False
            args = public.dict_obj()
            args.id = [get.id]
            args.classify = get.proxy_json_conf["classify"] if "classify" in get.proxy_json_conf else 0
            self.set_site_type(args)
        else:
            get.proxy_json_conf["stop_site"] = True
            args = public.dict_obj()
            args.id = [get.id]
            args.classify = "-2"
            self.set_site_type(args)

        dp.sql("docker_sites").where("id=?", (get.id,)).setField("status", get.status)

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="设置运行状态成功")

    # 2024/10/31 10:04 删除指定网站
    def delete_site(self, get):
        '''
            @name 删除指定网站
        '''
        get.id = get.get("id", None)
        if get.id is None: return public.returnResult(False, "id参数不能为空！")
        get.remove_path = get.get("remove_path", 0)
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")
        get.reload = get.get("reload/d", 1)

        find_result = dp.sql("docker_sites").where("id=?", (get.id,)).find()
        if not find_result: return public.returnResult(False, "未找到指定网站！")

        # 2024/11/6 16:36 停止指定php环境
        if find_result["type"] == "php":
            service_info = json.loads(find_result["service_info"])
            public.ExecShell("docker-compose -f {} down".format(os.path.join(service_info["project_path"], "docker-compose.yml")))
            public.ExecShell("docker-compose -f {} rm -f".format(os.path.join(service_info["project_path"], "docker-compose.yml")))
            public.ExecShell("rm -rf {}".format(service_info["project_path"]))

        # 2024/4/18 上午10:46 删除网站配置文件
        self.site_config_path = os.path.join(self.sites_config_path, find_result["name"])
        public.ExecShell("rm -rf {}".format(self.site_config_path))
        nginx_conf = os.path.join("/www/server/panel/vhost/nginx", "{}.conf".format(find_result["name"]))
        public.ExecShell("rm -rf {}".format(nginx_conf))
        redirect_dir = public.get_setup_path() + '/panel/vhost/nginx/redirect/' + get.site_name
        if os.path.exists(redirect_dir):
            public.ExecShell('rm -rf {}'.format(redirect_dir))

        logs_file = public.get_logs_path() + '/{}*'.format(get.site_name)
        public.ExecShell('rm -f {}'.format(logs_file))

        self._site_proxy_conf_path = "{path}/{site_name}".format(
            path=self.sites_config_path,
            site_name=get.site_name
        )
        public.ExecShell('rm -rf {}'.format(self._site_proxy_conf_path))

        if get.remove_path == 1:
            public.ExecShell("rm -rf {}".format(find_result["path"]))

        # 2024/4/18 上午10:22 删除数据库
        dp.sql("docker_sites").where("id=?", (get.id,)).delete()
        # 2024/11/6 10:15 删除所有docker_domain里面pid=id的域名
        dp.sql("docker_domain").where("pid=?", (get.id,)).delete()

        # 2024/11/7 14:50 删除json配置文件
        conf_path = "{path}/{site_name}/{site_name}.json".format(
            path=self.sites_config_path,
            site_name=find_result["name"]
        )
        public.ExecShell("rm -rf {}".format(conf_path))


        if get.reload == 1:
            public.serviceReload()

        return public.returnResult(msg="删除网站成功")

    # 2024/10/31 10:05 批量删除指定网站
    def batch_delete_site(self, get):
        '''
            @name 批量删除指定网站
        '''
        get.site_list = get.get("site_list", [])
        get.remove_path = get.get("remove_path/d", 0)
        get.reload = get.get("reload/d", 0)

        try:
            site_list = json.loads(get.site_list)
        except:
            return public.returnResult(False, "请传入需要删除的网站列表!")

        acc_list = []
        for site in site_list:
            args = public.dict_obj()
            args.site_name = site["site_name"]
            args.remove_path = get.remove_path
            args.reload = get.reload
            args.id = site["id"]
            de_result = self.delete_site(args)
            if not de_result["status"]:
                acc_list.append({"site_name": site["site_name"], "status": False})
                continue

            acc_list.append({"site_name": site["site_name"], "status": True})

        public.serviceReload()

        return public.returnResult(True, msg="批量删除站点成功！", data=acc_list)

    # 2024/11/7 17:30 清空所有网站
    def prune_sites(self, get):
        '''
            @name 清空所有网站
        '''
        get.remove_path = get.get("remove_path/d", 0)

        select_result = dp.sql("docker_sites").select()
        acc_list = []
        for site in select_result:
            args = public.dict_obj()
            args.site_name = site["name"]
            args.remove_path = get.remove_path
            args.reload = 0
            args.id = site["id"]
            de_result = self.delete_site(args)
            if not de_result["status"]:
                acc_list.append({"site_name": site["name"], "status": False})
                continue

            acc_list.append({"site_name": site["name"], "status": True})

        public.serviceReload()

        return public.returnResult(True, msg="清空所有网站成功！", data=acc_list)

    # 2024/10/31 10:07 获取指定网站的网站目录
    def get_site_path(self, get):
        '''
            @name 获取指定网站的网站目录
        '''
        get.id = get.get("id", None)
        if get.id is None: return public.returnResult(False, "id参数不能为空！")

        site_result = dp.sql("docker_sites").where("id=?", (get.id,)).find()
        if not site_result: return public.returnResult(False, "未找到指定网站！")

        return public.returnResult(data=site_result)

    # 2024/10/31 10:07 设置指定网站的网站目录
    def set_site_path(self, get):
        '''
            @name 设置指定网站的网站目录
        '''
        get.id = get.get("id", None)
        if get.id is None: return public.returnResult(False, "id参数不能为空！")
        path = get.get("path", None)
        if path is None: return public.returnResult(False, "path参数不能为空！")
        get.site_name = get.get("site_name", None)
        if get.site_name is None: return public.returnResult(False, "site_name参数不能为空！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        get.proxy_json_conf["site_path"] = path
        dp.sql("docker_sites").where("id=?", (get.id,)).setField("path", path)

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])

        # 2024/11/20 10:45 如果项目是php类型，则替换docker-compose.yml的site_path，然后重新up容器
        if "type" in get.proxy_json_conf and get.proxy_json_conf["type"] == "php":
            service_info = json.loads(dp.sql("docker_sites").where("id=?", (get.id,)).getField("service_info"))
            public.ExecShell("sed -i 's,^SITE_PATH=.*,SITE_PATH={},' {}/.env".format(path, service_info["project_path"]))
            public.ExecShell("docker-compose -f {} up -d".format(os.path.join(service_info["project_path"], "docker-compose.yml")))

        public.serviceReload()

        return public.returnResult(msg="设置网站目录成功")

    # 2024/10/31 10:08 设置指定网站的运行目录
    def set_site_run_path(self, get):
        '''
            @name 设置指定网站的运行目录
        '''
        get.id = get.get("id", None)
        if get.id is None: return public.returnResult(False, "id参数不能为空！")
        get.run_path = get.get("run_path", None)
        if get.run_path is None: return public.returnResult(False, "run_path参数不能为空！")
        get.site_name = get.get("site_name", None)
        if get.site_name is None: return public.returnResult(False, "site_name参数不能为空！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        get.proxy_json_conf["run_path"] = get.run_path.replace(get.proxy_json_conf["site_path"], "")
        if not get.proxy_json_conf["run_path"]: get.proxy_json_conf["run_path"] = "/"
        dp.sql("docker_sites").where("id=?", (get.id,)).setField("run_path", get.proxy_json_conf["run_path"])

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])

        # 2024/11/20 10:45 如果项目是php类型，则替换env的site_path，然后重新up容器
        if "type" in get.proxy_json_conf and get.proxy_json_conf["type"] == "php":
            service_info = json.loads(dp.sql("docker_sites").where("id=?", (get.id,)).getField("service_info"))
            public.ExecShell("sed -i 's,^SITE_PATH=.*,SITE_PATH={},' {}/.env".format(os.path.join(get.proxy_json_conf["site_path"], get.proxy_json_conf["run_path"].replace("/","",1)), service_info["project_path"]))
            public.ExecShell("docker-compose -f {} up -d".format(os.path.join(service_info["project_path"], "docker-compose.yml")))

        public.serviceReload()

        return public.returnResult(msg="设置网站运行目录成功")

    # 2024/4/21 下午10:46 设置商业ssl证书
    def set_cert(self, get):
        '''
            @name
            @author wzz <2024/4/21 下午10:46>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.oid = get.get("oid", "")
        if get.oid == "":
            return public.returnResult(status=False, msg="oid不能为空！")

        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.siteName = get.site_name

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        from mod.project.docker.sites.sslManage import SslManage
        ssl_manage = SslManage()
        set_result = ssl_manage.set_cert(get)
        if not set_result["status"]: return set_result

        get.proxy_json_conf["ssl_info"]["ssl_status"] = True
        get.proxy_json_conf["https_port"] = "443"

        self._site_proxy_conf_path = "{path}/{site_name}/{site_name}.json".format(
            path=self.sites_config_path,
            site_name=get.site_name
        )
        public.writeFile(self._site_proxy_conf_path, json.dumps(get.proxy_json_conf))

        return set_result

    # 2024/10/31 10:08 保存并启用指定网站的SSL
    def set_ssl(self, get):
        '''
            @name 保存并启用指定网站的SSL
        '''
        get.key = get.get("key", "")
        if get.key == "":
            return public.returnResult(status=False, msg="key不能为空！")

        get.csr = get.get("csr", "")
        if get.csr == "":
            return public.returnResult(status=False, msg="csr不能为空！")

        get.siteName = get.get("siteName", "")
        get.site_name = get.get("site_name", "")
        if get.siteName == "":
            if get.site_name == "":
                return public.returnResult(status=False, msg="网站名不能为空！")

            get.siteName = get.site_name
        else:
            get.site_name = get.siteName

        get.type = -1

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        from mod.project.docker.sites.sslManage import SslManage
        ssl_manage = SslManage()
        result = ssl_manage.set_ssl_to_site(get)
        if not result["status"]: return result

        get.proxy_json_conf["ssl_info"]["ssl_status"] = True
        get.proxy_json_conf["https_port"] = "443"

        self._site_proxy_conf_path = "{path}/{site_name}/{site_name}.json".format(
            path=self.sites_config_path,
            site_name=get.site_name
        )
        public.writeFile(self._site_proxy_conf_path, json.dumps(get.proxy_json_conf))

        return result

    # 2024/11/7 15:21 申请let' encrypt证书
    def apply_cert_api(self, get):
        '''
            @name
            @author wzz <2024/4/21 下午11:34>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.domains = get.get("domains", "")
        if get.domains == "":
            return public.returnResult(status=False, msg="domains不能为空！")

        get.auth_type = get.get("auth_type", "")
        if get.auth_type == "":
            return public.returnResult(status=False, msg="auth_type不能为空！")

        get.auth_to = get.get("auth_to", "")
        if get.auth_to == "":
            return public.returnResult(status=False, msg="auth_to不能为空！")

        get.auto_wildcard = get.get("auto_wildcard", "")
        if get.auto_wildcard == "":
            return public.returnResult(status=False, msg="auto_wildcard不能为空！")

        get.id = get.get("id", "")
        if get.id == "":
            return public.returnResult(status=False, msg="id不能为空！")

        get.siteName = get.site_name

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        from mod.project.docker.sites.sslManage import Acme_V2
        acme = Acme_V2()
        result = acme.apply_cert_api(get)
        if not result["status"]: return result

        get.proxy_json_conf["ssl_info"]["ssl_status"] = True
        get.proxy_json_conf["https_port"] = "443"

        self._site_proxy_conf_path = "{path}/{site_name}/{site_name}.json".format(
            path=self.sites_config_path,
            site_name=get.site_name
        )
        public.writeFile(self._site_proxy_conf_path, json.dumps(get.proxy_json_conf))

        return result

    # 2024/4/21 下午11:36 验证let' encrypt dns
    def apply_dns_auth(self, get):
        '''
            @name
            @author wzz <2024/4/21 下午11:36>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.index = get.get("index", "")
        if get.index == "":
            return public.returnResult(status=False, msg="index不能为空！")

        from acme_v2 import acme_v2
        acme = acme_v2()
        return acme.apply_dns_auth(get)

    # 2024/4/21 下午11:44 设置证书夹里面的证书
    def SetBatchCertToSite(self, get):
        '''
            @name
            @author wzz <2024/4/21 下午11:44>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.BatchInfo = get.get("BatchInfo", "")
        if get.BatchInfo == "":
            return public.returnResult(status=False, msg="BatchInfo不能为空！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        from mod.project.docker.sites.sslManage import SslManage
        ssl_manage = SslManage()
        set_result = ssl_manage.SetBatchCertToSite(get)
        if not "successList" in set_result: return set_result

        for re in set_result["successList"]:
            if re["status"] and re["siteName"] == get.site_name:
                get.proxy_json_conf["ssl_info"]["ssl_status"] = True
                break

        self._site_proxy_conf_path = "{path}/{site_name}/{site_name}.json".format(
            path=self.sites_config_path,
            site_name=get.site_name
        )
        public.writeFile(self._site_proxy_conf_path, json.dumps(get.proxy_json_conf))

        return set_result

    # 2024/4/22 上午9:43 设置强制https
    def set_force_https(self, get):
        '''
            @name 设置强制https
            @param get:
                    site_name: 网站名
                    force_https: 1/0
            @return:
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.force_https = get.get("force_https/d", 999)
        if get.force_https == 999:
            return public.returnResult(status=False, msg="force_https不能为空！")

        get.siteName = get.site_name

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        get.proxy_json_conf["ssl_info"]["force_https"] = True if get.force_https == 1 else False

        from mod.project.docker.sites.sslManage import SslManage
        ssl_manage = SslManage()
        if get.force_https == 1:
            result = ssl_manage.HttpToHttps(get)
        else:
            result = ssl_manage.CloseToHttps(get)

        if not result["status"]: return result

        self._site_proxy_conf_path = "{path}/{site_name}/{site_name}.json".format(
            path=self.sites_config_path,
            site_name=get.site_name
        )
        public.writeFile(self._site_proxy_conf_path, json.dumps(get.proxy_json_conf))

        return result

    # 2024/4/21 下午11:03 关闭SSl证书
    def close_ssl(self, get):
        '''
            @name
            @author wzz <2024/4/21 下午11:04>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.siteName = get.get("siteName", "")
        if get.siteName == "":
            return public.returnResult(status=False, msg="siteName不能为空！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        from mod.project.docker.sites.sslManage import SslManage
        ssl_manage = SslManage()
        result = ssl_manage.CloseSSLConf(get)
        if not result["status"]: return result

        get.proxy_json_conf["ssl_info"]["ssl_status"] = False
        get.proxy_json_conf["https_port"] = "443"

        self._site_proxy_conf_path = "{path}/{site_name}/{site_name}.json".format(
            path=self.sites_config_path,
            site_name=get.site_name
        )
        public.writeFile(self._site_proxy_conf_path, json.dumps(get.proxy_json_conf))

        return result

    # 2024/4/19 下午11:46 给指定网站添加域名
    def add_domain(self, get):
        '''
            @name
            @author wzz <2024/4/19 下午11:46>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")
        get.id = get.get("id", "")
        if get.id == "":
            return public.returnResult(status=False, msg="id不能为空！")
        get.domains = get.get("domains", "")
        if get.domains == "":
            return public.returnResult(status=False, msg="domains不能为空！")
        if "," in get.domains:
            return public.returnResult(status=False, msg="域名不能包含逗号！")

        isError = public.checkWebConfig()
        if isError != True:
            return public.returnResult(False, 'ERROR: 检测到配置文件有错误,请先排除后再操作<br><br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')

        get.domain_list = get.domains.strip().replace(' ', '').split("\n")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        from firewallModel.comModel import main as comModel
        firewall_com = comModel()

        res_domains = []
        for domain in get.domain_list:
            if domain == "": continue
            domain = domain.strip().split(':')
            get.domain = self.ToPunycode(domain[0]).lower()
            get.port = '80'

            # 判断通配符域名格式
            if get.domain.find('*') != -1 and get.domain.find('*.') == -1:
                res_domains.append({"name": get.domain, "status": False, "msg": '域名格式不正确'})
                continue

            # 判断域名格式
            reg = "^([\w\-\*]{1,100}\.){1,24}([\w\-]{1,24}|[\w\-]{1,24}\.[\w\-]{1,24})$"
            if not re.match(reg, get.domain):
                res_domains.append({"name": get.domain, "status": False, "msg": '域名格式不正确'})
                continue

            # 获取自定义端口
            if len(domain) == 2:
                get.port = domain[1]
            if get.port == "": get.port = "80"

            # 判断端口是否合法
            if not re.match("^\d+$", get.port):
                res_domains.append({"name": get.domain, "status": False, "msg": '端口不合法，应该为数字'})
                continue

            not_used_ports = ('21', '25', '443', '888', '8888', '8443')
            if get.port in not_used_ports:
                res_domains.append(
                    {"name": get.domain, "status": False, "msg": '端口不合法，请勿使用常用端口，例如：ssh的22端口等'})
                continue

            intport = int(get.port)
            if intport < 1 or intport > 65535:
                res_domains.append({"name": get.domain, "status": False, "msg": '端口范围不合法'})
                continue

            # 2024/11/7 18:07 检查域名是否已经存在
            find_pid = dp.sql("docker_domain").where("name=? and port=?", (get.domain, get.port)).getField('pid')
            if find_pid:
                siteName = dp.sql("docker_sites").where("id=?", (find_pid,)).getField('name')
                if siteName:
                    res_domains.append({"name": get.domain, "status": False, "msg": '指定域名[{}]已被网站[{}]绑定过了'.format(get.domain, siteName)})
                    continue

                dp.sql("docker_domain").where("pid=?", (find_pid,)).delete()

            # if get.domain in get.proxy_json_conf["domain_list"]:
            #     res_domains.append({"name": get.domain, "status": False, "msg": '指定域名[{}]已经存在'.format(get.domain)})
            #     continue

            # 2024/11/7 18:09 写配置文件
            if not get.domain in get.proxy_json_conf["domain_list"]:
                get.proxy_json_conf["domain_list"].append(get.domain)
            if not get.port in get.proxy_json_conf["site_port"]:
                get.proxy_json_conf["site_port"].append(get.port)

            # 2024/11/7 18:19 写入数据库
            dp.sql("docker_domain").add('name,port,pid', (get.domain, get.port, get.id))

            firewall_com.set_port_rule(get)
            res_domains.append({"name": get.domain, "status": True})

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(status=True, data=res_domains)

    # 2024/4/20 上午12:07 删除指定网站的某个域名
    def del_domain(self, get):
        '''
            @name
            @author wzz <2024/4/20 上午12:07>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.id = get.get("id", "")
        if get.id == "":
            return public.returnResult(status=False, msg="id不能为空！")
        get.port = get.get("port", "")
        if get.port == "":
            return public.returnResult(status=False, msg="port不能为空！")
        get.domain = get.get("domain", "")
        if get.domain == "":
            return public.returnResult(status=False, msg="domain不能为空！")
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")
        get.reload = get.get("reload/d", 1)

        # 2024/4/20 上午12:02 更新json文件
        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        if len(get.proxy_json_conf["domain_list"]) < 2 and dp.sql("docker_domain").where("pid=?", (get.id,)).count() < 2:
            return public.returnResult(status=False, msg="至少保留一个域名！")

        while get.domain in get.proxy_json_conf["domain_list"]:
            get.proxy_json_conf["domain_list"].remove(get.domain)
        if get.port in get.proxy_json_conf["site_port"] and len(get.proxy_json_conf["site_port"]) != 1:
            find_r = dp.sql("docker_domain").where("name=? and port=?", (get.domain, get.port)).find()
            if find_r:
                while get.port in get.proxy_json_conf["site_port"]:
                    get.proxy_json_conf["site_port"].remove(get.port)

        dp.sql("docker_domain").where("name=? and port=?", (get.domain, get.port)).delete()

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        if get.reload == 1:
            public.serviceReload()

        return public.returnResult(status=True, msg="删除域名成功")

        # 2024/4/20 上午12:20 批量删除指定网站域名

    def batch_del_domain(self, get):
        '''
            @name 批量删除指定网站域名
            @param get:
            @return:
        '''
        get.del_domain_list = get.get("del_domain_list", None)
        if get.del_domain_list is None:
            return public.returnResult(status=False, msg="del_domain_list不能为空！")

        try:
            get.del_domain_list = json.loads(get.del_domain_list)
        except:
            return public.returnResult(status=False, msg="del_domain_list格式错误！")

        res_domains = {"success": [], "error": []}
        for domain in get.del_domain_list:
            args = public.dict_obj()
            args.id = domain["id"]
            args.port = domain["port"]
            args.domain = domain["domain"]
            args.site_name = domain["site_name"]
            args.reload = 0
            del_result = self.del_domain(args)
            if not del_result["status"]:
                res_domains["error"].append({"domain": args.domain, "msg": del_result["msg"]})
                continue

            res_domains["success"].append({"domain": args.domain})
        public.serviceReload()

        return public.returnResult(status=True, data=res_domains)

    # 2024/4/18 下午9:58 设置全局日志
    def set_global_log(self, get):
        '''
            @name
            @author wzz <2024/4/18 下午9:58>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.log_type = get.get("log_type", "default")
        if not get.log_type in ["default", "file", "rsyslog", "off"]:
            return public.returnResult(status=False, msg="日志类型错误，请传入default/file/rsyslog/off！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        get.proxy_json_conf["proxy_log"]["log_type"] = get.log_type

        if get.log_type == "file":
            get.log_path = get.get("log_path", "")
            if get.log_path == "":
                return public.returnResult(status=False, msg="日志路径不能为空！")
            if not get.log_path.startswith("/"):
                return public.returnResult(status=False, msg="日志路径必须以/开头！")

            get.proxy_json_conf["proxy_log"]["log_path"] = get.log_path
            get.proxy_json_conf["proxy_log"]["log_conf"] = self.init_site_json["proxy_log"]["log_conf"].format(
                log_path=get.log_path,
                site_name=get.site_name
            )
        elif get.log_type == "rsyslog":
            get.log_path = get.get("log_path", "")
            if get.log_path == "":
                return public.returnResult(status=False, msg="日志路径不能为空！")
            site_name = get.site_name.replace(".", "_")
            get.proxy_json_conf["proxy_log"]["log_conf"] = (
                "\n    access_log syslog:server={server_host},nohostname,tag=nginx_{site_name}_access;"
                "\n    error_log syslog:server={server_host},nohostname,tag=nginx_{site_name}_error;"
                .format(
                    server_host=get.log_path,
                    site_name=site_name
                ))
            get.proxy_json_conf["proxy_log"]["rsyslog_host"] = get.log_path
        elif get.log_type == "off":
            get.proxy_json_conf["proxy_log"]["log_conf"] = "\n    access_log off;\n    error_log off;"
        else:
            get.proxy_json_conf["proxy_log"]["log_conf"] = "    " + self.init_site_json["proxy_log"][
                "log_conf"].format(
                log_path=public.get_logs_path(),
                site_name=get.site_name
            )

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="设置成功！")

    # 2024/4/18 下午10:21 设置basic_auth
    def set_dir_auth(self, get):
        '''
            @name 设置basic_auth
            @param  auth_type: add/edit
                    auth_path: /api
                    username: admin
                    password: admin
            @return:
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.name = get.get("name", "")
        if get.name == "":
            return public.returnResult(status=False, msg="name不能为空！")

        get.auth_path = get.get("auth_path", "")
        if get.auth_path == "":
            return public.returnResult(status=False, msg="auth_path不能为空！")
        if not get.auth_path.startswith("/"):
            return public.returnResult(status=False, msg="auth_path必须以/开头！")

        get.username = get.get("username", "")
        get.password = get.get("password", "")
        if get.username == "" or get.password == "":
            return public.returnResult(status=False, msg="用户名和密码不能为空！")

        if len(get.password) > 8:
            return public.returnResult(status=False, msg="密码不能超过8位，超过的部分无法验证！")

        get.password = public.hasPwd(get.password)

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        if len(get.proxy_json_conf["basic_auth"]) == 0:
            return public.returnResult(status=False, msg="【{}】不存在http认证中，请先添加！".format(get.auth_path))

        for i in range(len(get.proxy_json_conf["basic_auth"])):
            if get.proxy_json_conf["basic_auth"][i]["auth_path"] == get.auth_path:
                if get.proxy_json_conf["basic_auth"][i]["auth_name"] == get.name:
                    get.proxy_json_conf["basic_auth"][i]["username"] = get.username
                    get.proxy_json_conf["basic_auth"][i]["password"] = get.password
                    break

        auth_file = "/www/server/pass/{site_name}/{name}.htpasswd".format(site_name=get.site_name, name=get.name)
        public.writeFile(auth_file, "{}:{}".format(get.username, get.password))

        self._site_proxy_conf_path = "{path}/{site_name}/{site_name}.json".format(
            path=self.sites_config_path,
            site_name=get.site_name
        )
        public.writeFile(self._site_proxy_conf_path, json.dumps(get.proxy_json_conf))

        public.serviceReload()

        return public.returnResult(msg="设置成功！")

    # 2024/4/22 下午4:17 添加指定网站的basic_auth
    def add_dir_auth(self, get):
        '''
            @name 添加指定网站的basic_auth
            @author wzz <2024/4/22 下午4:17>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.auth_path = get.get("auth_path", "")
        if get.auth_path == "":
            return public.returnResult(status=False, msg="auth_path不能为空！")
        if not get.auth_path.startswith("/"):
            return public.returnResult(status=False, msg="auth_path必须以/开头！")

        get.name = get.get("name", "")
        if get.name == "":
            return public.returnResult(status=False, msg="name不能为空！")

        get.username = get.get("username", "")
        if get.username == "":
            return public.returnResult(status=False, msg="username不能为空！")

        get.password = get.get("password", "")
        if get.password == "":
            return public.returnResult(status=False, msg="password不能为空！")
        if len(get.password) > 8:
            return public.returnResult(status=False, msg="密码不能超过8位，超过的部分无法验证！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        auth_file = "/www/server/pass/{site_name}/{name}.htpasswd".format(site_name=get.site_name, name=get.name)

        auth_conf = {
            "auth_status": True,
            "auth_path": get.auth_path,
            "auth_name": get.name,
            "username": get.username,
            "password": public.hasPwd(get.password),
            "auth_file": auth_file,
        }

        if len(get.proxy_json_conf["basic_auth"]) != 0:
            for i in range(len(get.proxy_json_conf["basic_auth"])):
                if get.proxy_json_conf["basic_auth"][i]["auth_path"] == get.auth_path:
                    return public.returnResult(status=False,
                                               msg="【{}】已存在http认证中，无法重复添加！".format(get.auth_path))

        if not os.path.exists("/www/server/pass"):
            public.ExecShell("mkdir -p /www/server/pass")
        if not os.path.exists("/www/server/pass/{}".format(get.site_name)):
            public.ExecShell("mkdir -p /www/server/pass/{}".format(get.site_name))
        public.writeFile(auth_file, "{}:{}".format(get.username, public.hasPwd(get.password)))

        get.proxy_json_conf["basic_auth"].append(auth_conf)

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])

        return public.returnResult(msg="添加成功！")

    # 2024/4/23 上午9:34 删除指定网站的basic_auth
    def del_dir_auth(self, get):
        '''
            @name 删除指定网站的basic_auth
            @author wzz <2024/4/23 上午9:35>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.auth_path = get.get("auth_path", "")
        if get.auth_path == "":
            return public.returnResult(status=False, msg="auth_path不能为空！")

        get.name = get.get("name", "")
        if get.name == "":
            return public.returnResult(status=False, msg="name不能为空！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        auth_file = "/www/server/pass/{site_name}/{name}.htpasswd".format(site_name=get.site_name, name=get.name)

        panel_port = public.readFile('/www/server/panel/data/port.pl')
        proxy_list = self.get_proxy_list(get)
        if proxy_list["data"][0]["proxy_pass"] == "https://127.0.0.1:{}".format(
                panel_port.strip()) and get.auth_path.strip() == "/":
            return public.returnResult(False, "【{}】是面板的反代，不能删除【/】的http认证！".format(get.site_name))

        if len(get.proxy_json_conf["basic_auth"]) != 0:
            for i in range(len(get.proxy_json_conf["basic_auth"])):
                if get.proxy_json_conf["basic_auth"][i]["auth_path"] == get.auth_path:
                    if get.proxy_json_conf["basic_auth"][i]["auth_name"] == get.name:
                        get.proxy_json_conf["basic_auth"].pop(i)
                        break

        public.ExecShell("rm -f {}".format(auth_file))

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="删除成功！")

    # 2024/4/18 下午10:26 设置全局gzip
    def set_global_gzip(self, get):
        '''
            @name 设置全局gzip
            @param get:
            @return:
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.gzip_status = get.get("gzip_status/d", 999)
        if get.gzip_status == 999:
            return public.returnResult(status=False, msg="gzip_status不能为空，请传number 1或0！")
        get.gzip_min_length = get.get("gzip_min_length", "10k")
        get.gzip_comp_level = get.get("gzip_comp_level", "6")
        if get.gzip_min_length[0] == "0" or get.gzip_min_length.startswith("-"):
            return public.returnResult(status=False, msg="gzip_min_length参数不合法，请输入大于0的数字！")
        if get.gzip_comp_level == "0" or get.gzip_comp_level.startswith("-"):
            return public.returnResult(status=False, msg="gzip_comp_level参数不合法，请输入大于0的数字！")
        get.gzip_types = get.get(
            "gzip_types",
            "text/plain application/javascript application/x-javascript text/javascript text/css application/xml application/json image/jpeg image/gif image/png font/ttf font/otf image/svg+xml application/xml+rss text/x-js"
        )

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        get.proxy_json_conf["gzip"]["gzip_status"] = True if get.gzip_status == 1 else False
        if get.proxy_json_conf["gzip"]["gzip_status"]:
            get.proxy_json_conf["gzip"]["gzip_status"] = True
            get.proxy_json_conf["gzip"]["gzip_min_length"] = get.gzip_min_length
            get.proxy_json_conf["gzip"]["gzip_comp_level"] = get.gzip_comp_level
            get.proxy_json_conf["gzip"]["gzip_types"] = get.gzip_types
            get.gzip_conf = ("gzip on;"
                             "\n    gzip_min_length {gzip_min_length};"
                             "\n    gzip_buffers 4 16k;"
                             "\n    gzip_http_version 1.1;"
                             "\n    gzip_comp_level {gzip_comp_level};"
                             "\n    gzip_types {gzip_types};"
                             "\n    gzip_vary on;"
                             "\n    gzip_proxied expired no-cache no-store private auth;"
                             "\n    gzip_disable \"MSIE [1-6]\.\";").format(
                gzip_min_length=get.gzip_min_length,
                gzip_comp_level=get.gzip_comp_level,
                gzip_types=get.gzip_types
            )
            get.proxy_json_conf["gzip"]["gzip_conf"] = get.gzip_conf
        else:
            get.proxy_json_conf["gzip"]["gzip_conf"] = ""

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="设置成功！")

    # 2024/4/18 下午10:27 设置全局缓存
    def set_global_cache(self, get):
        '''
            @name 设置全局缓存
            @param get:
            @return:
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.cache_status = get.get("cache_status/d", 999)
        if get.cache_status == 999:
            return public.returnResult(status=False, msg="cache_status不能为空，请传number 1或0！")

        get.expires = get.get("expires", "1d")
        if get.expires[0] == "0" or get.expires.startswith("-"):
            return public.returnResult(status=False, msg="expires参数不合法，请输入大于0的数字！")
        expires = "expires {}".format(get.expires)

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        static_cache = ("\n    location ~ .*\\.(css|js|jpe?g|gif|png|webp|woff|eot|ttf|svg|ico|css\.map|js\.map)$"
                        "\n    {{"
                        "\n        {expires};"
                        "\n        error_log /dev/null;"
                        "\n        access_log /dev/null;"
                        "\n    }}").format(
            expires=expires,
        )

        cache_conf = ("\n    proxy_cache {cache_zone};"
                      "\n    proxy_cache_key $host$uri$is_args$args;"
                      "\n    proxy_ignore_headers Set-Cookie Cache-Control expires X-Accel-Expires;"
                      "\n    proxy_cache_valid 200 304 301 302 {expires};"
                      "\n    proxy_cache_valid 404 1m;"
                      "{static_cache}").format(
            cache_zone=get.proxy_json_conf["proxy_cache"]["cache_zone"],
            expires=get.expires,
            static_cache=get.proxy_json_conf["proxy_cache"]["static_cache"] if get.proxy_json_conf["proxy_cache"][
                                                                                   "static_cache"] != "" else static_cache
        )

        get.proxy_json_conf["proxy_cache"]["cache_status"] = True if get.cache_status == 1 else False
        if get.proxy_json_conf["proxy_cache"]["cache_status"]:
            get.proxy_json_conf["proxy_cache"]["cache_status"] = True
            get.proxy_json_conf["proxy_cache"]["expires"] = get.expires
            get.proxy_json_conf["proxy_cache"]["cache_conf"] = cache_conf
        else:
            get.proxy_json_conf["proxy_cache"]["cache_status"] = False
            get.proxy_json_conf["proxy_cache"]["cache_conf"] = static_cache

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="设置成功！")

    # 2024/4/18 下午10:43 设置全局websocket支持
    def set_global_websocket(self, get):
        '''
            @name
            @author wzz <2024/4/19 下午2:37>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.websocket_status = get.get("websocket_status/d", 999)
        if get.websocket_status == 999:
            return public.returnResult(status=False, msg="websocket_status不能为空，请传number 1或0！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        if get.websocket_status == 1:
            get.proxy_json_conf["websocket"]["websocket_status"] = True
        else:
            get.proxy_json_conf["websocket"]["websocket_status"] = False

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="设置成功！")

    # 2024/4/22 上午10:27 创建重定向
    def CreateRedirect(self, get):
        '''
            @name
            @author wzz <2024/4/22 上午10:27>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.domainorpath = get.get("domainorpath", "")
        if get.domainorpath == "":
            return public.returnResult(status=False, msg="domainorpath不能为空！")

        get.redirecttype = get.get("redirecttype", "")
        if get.redirecttype == "":
            return public.returnResult(status=False, msg="redirecttype不能为空！")

        get.redirectpath = get.get("redirectpath", "")
        if get.domainorpath == "path" and get.redirectpath == "":
            return public.returnResult(status=False, msg="redirectpath不能为空！")

        get.tourl = get.get("tourl", "")
        if get.tourl == "":
            return public.returnResult(status=False, msg="tourl不能为空！")

        get.redirectdomain = get.get("redirectdomain", "")
        if get.domainorpath == "domain" and get.redirectdomain == "":
            return public.returnResult(status=False, msg="redirectdomain不能为空！")

        get.redirectname = get.get("redirectname", "")
        if get.redirectname == "":
            return public.returnResult(status=False, msg="redirectname不能为空！")

        get.sitename = get.site_name
        get.type = 1
        get.holdpath = 1

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        get.proxy_json_conf["redirect"]["redirect_status"] = True

        from panelRedirect import panelRedirect
        result = panelRedirect().CreateRedirect(get)

        self._site_proxy_conf_path = "{path}/{site_name}/{site_name}.json".format(
            path=self.sites_config_path,
            site_name=get.site_name
        )
        public.writeFile(self._site_proxy_conf_path, json.dumps(get.proxy_json_conf))

        return result

    # 2024/4/22 上午10:45 删除指定网站的某个重定向规则
    def DeleteRedirect(self, get):
        '''
            @name 删除指定网站的某个重定向规则
            @author wzz <2024/4/22 上午10:45>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.redirectname = get.get("redirectname", "")
        if get.redirectname == "":
            return public.returnResult(status=False, msg="redirectname不能为空！")

        get.sitename = get.site_name

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        from panelRedirect import panelRedirect
        redirect_list = panelRedirect().GetRedirectList(get)
        if len(redirect_list) == 0:
            get.proxy_json_conf["redirect"]["redirect_status"] = False
            self._site_proxy_conf_path = "{path}/{site_name}/{site_name}.json".format(
                path=self.sites_config_path,
                site_name=get.site_name
            )
            public.writeFile(self._site_proxy_conf_path, json.dumps(get.proxy_json_conf))

        return panelRedirect().DeleteRedirect(get)

    # 2024/4/23 上午10:38 编辑指定网站的某个重定向规则
    def ModifyRedirect(self, get):
        '''
            @name 编辑指定网站的某个重定向规则
            @author wzz <2024/4/23 上午10:38>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.domainorpath = get.get("domainorpath", "")
        if get.domainorpath == "":
            return public.returnResult(status=False, msg="domainorpath不能为空！")

        get.redirecttype = get.get("redirecttype", "")
        if get.redirecttype == "":
            return public.returnResult(status=False, msg="redirecttype不能为空！")

        get.redirectpath = get.get("redirectpath", "")
        if get.domainorpath == "path" and get.redirectpath == "":
            return public.returnResult(status=False, msg="redirectpath不能为空！")

        get.tourl = get.get("tourl", "")
        if get.tourl == "":
            return public.returnResult(status=False, msg="tourl不能为空！")

        get.redirectdomain = get.get("redirectdomain", "")
        if get.domainorpath == "domain" and get.redirectdomain == "":
            return public.returnResult(status=False, msg="redirectdomain不能为空！")

        get.redirectname = get.get("redirectname", "")
        if get.redirectname == "":
            return public.returnResult(status=False, msg="redirectname不能为空！")

        get.sitename = get.site_name
        get.type = get.get("type/d", 1)
        get.holdpath = get.get("holdpath/d", 1)

        from panelRedirect import panelRedirect

        return panelRedirect().ModifyRedirect(get)

    # 2024/4/26 下午3:32 获取指定网站指定重定向规则的信息
    def GetRedirectFile(self, get):
        '''
            @name 获取指定网站指定重定向规则的信息
            @author wzz <2024/4/26 下午3:32>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.path = get.get("path", "")
        if get.path == "":
            return public.returnResult(status=False, msg="path不能为空！")

        if not os.path.exists(get.path):
            return public.returnResult(status=False, msg="重定向已停止或配置文件目录不存在！")

        import files
        f = files.files()
        return f.GetFileBody(get)

    # 2024/11/22 10:45 获取防盗链信息
    def GetSecurity(self, get):
        '''
            @name 获取防盗链信息
        '''
        file = '/www/server/panel/vhost/nginx/' + get.name + '.conf'
        conf = public.readFile(file)
        data = {}
        if type(conf) == bool: return public.returnMsg(False, '读取配置文件失败!')
        if conf.find('SECURITY-START') != -1:
            rep = "#SECURITY-START(\n|.)+#SECURITY-END"
            tmp = re.search(rep, conf).group()
            content = re.search("\(.+\)\$", tmp)
            if content:
                data['fix'] = content.group().replace('(', '').replace(')$', '').replace('|', ',')
            else:
                data['fix'] = ''
            try:
                data['domains'] = ','.join(list(set(re.search("valid_referers\s+none\s+blocked\s+(.+);\n", tmp).groups()[0].split())))
            except:
                data['domains'] = ','.join(list(set(re.search("valid_referers\s+(.+);\n", tmp).groups()[0].split())))
            data['status'] = True
            data['http_status'] = tmp.find('none blocked') != -1
            try:
                data['return_rule'] = re.findall(r'(return|rewrite)\s+.*(\d{3}|(/.+)\s+(break|last));', conf)[0][1].replace('break', '').strip()
            except:
                data['return_rule'] = '404'
        else:
            conf_file = '/www/server/panel/vhost/config/{}_door_chain.json'.format(get.name)
            try:
                data = json.loads(public.readFile(conf_file))
                data['status'] = data['status'] == "true"
            except:
                data = {}
                data['fix'] = 'jpg,jpeg,gif,png,js,css'
                domains = public.M('docker_domain').where('pid=?', (get.id,)).field('name').select()
                tmp = []
                for domain in domains:
                    tmp.append(domain['name'])
                data['domains'] = ','.join(tmp)
                data['return_rule'] = '404'
                data['status'] = False
                data['http_status'] = False
        return data

    # 2024/4/22 上午11:12 设置防盗链
    def SetSecurity(self, get):
        '''
            @name 设置防盗链
            @author wzz <2024/4/22 上午11:12>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.fix = get.get("fix", "")
        if get.fix == "":
            return public.returnResult(status=False, msg="fix不能为空！")

        get.domains = get.get("domains", "")
        if get.domains == "":
            return public.returnResult(status=False, msg="domains不能为空！")

        get.return_rule = get.get("return_rule", "")
        if get.return_rule == "":
            return public.returnResult(status=False, msg="return_rule不能为空！")

        get.http_status = get.get("http_status", "")
        if get.http_status == "":
            return public.returnResult(status=False, msg="http_status不能为空！")

        get.status = get.get("status", "")
        if get.status == "":
            return public.returnResult(status=False, msg="status不能为空！")

        get.id = get.get("id", "")
        if get.id == "":
            return public.returnResult(status=False, msg="id不能为空！")

        get.name = get.site_name

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        get.proxy_json_conf["security"]["security_status"] = True if get.status == "true" else False
        get.proxy_json_conf["security"]["static_resource"] = get.fix
        get.proxy_json_conf["security"]["domains"] = get.domains
        get.proxy_json_conf["security"]["return_resource"] = get.return_rule
        get.proxy_json_conf["security"]["http_status"] = True if get.http_status else False

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="设置成功！")

    # 2024/11/7 15:26 添加全局IP黑白名单
    def add_ip_limit(self, get):
        '''
            @name 添加全局IP黑白名单
            @author wzz <2024/4/23 下午3:08>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.ip_type = get.get("ip_type", "black")
        if get.ip_type not in ["black", "white"]:
            return public.returnResult(status=False, msg="ip_type参数错误，必须传black或white！")

        get.ips = get.get("ips", "")
        if get.ips == "":
            return public.returnResult(status=False, msg="ips不能为空，请输入IP，一行一个！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        get.ips = get.ips.split("\n")
        for ip in get.ips:
            if ip not in get.proxy_json_conf["ip_limit"]["ip_{}".format(get.ip_type)]:
                get.proxy_json_conf["ip_limit"]["ip_{}".format(get.ip_type)].append(ip)

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="设置成功！")

    # 2024/4/23 下午3:12 删除全局IP黑白名单
    def del_ip_limit(self, get):
        '''
            @name 删除全局IP黑白名单
            @author wzz <2024/4/23 下午3:12>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.ip_type = get.get("ip_type", "black")
        if get.ip_type not in ["black", "white"]:
            return public.returnResult(status=False, msg="ip_type参数错误，必须传black或white！")

        get.ip = get.get("ip", "")
        if get.ip == "":
            return public.returnResult(status=False, msg="ip不能为空，请输入IP！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        if get.ip in get.proxy_json_conf["ip_limit"]["ip_{}".format(get.ip_type)]:
            get.proxy_json_conf["ip_limit"]["ip_{}".format(get.ip_type)].remove(get.ip)

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="删除成功！")

    # 2024/4/23 下午3:13 批量删除全局IP黑白名单
    def batch_del_ip_limit(self, get):
        '''
            @name 批量删除全局IP黑白名单
            @author wzz <2024/4/23 下午3:14>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.ip_type = get.get("ip_type", "black")
        if get.ip_type not in ["black", "white", "all"]:
            return public.returnResult(status=False, msg="ip_type参数错误，必须传black或white！")

        get.ips = get.get("ips", "")
        if get.ips == "":
            return public.returnResult(status=False, msg="ips不能为空，请输入IP，一行一个！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        get.ips = get.ips.split("\n")
        for ip in get.ips:
            if get.ip_type == "all":
                if ip in get.proxy_json_conf["ip_limit"]["ip_black"]:
                    get.proxy_json_conf["ip_limit"]["ip_black"].remove(ip)
                if ip in get.proxy_json_conf["ip_limit"]["ip_white"]:
                    get.proxy_json_conf["ip_limit"]["ip_white"].remove(ip)
            else:
                if ip in get.proxy_json_conf["ip_limit"]["ip_{}".format(get.ip_type)]:
                    get.proxy_json_conf["ip_limit"]["ip_{}".format(get.ip_type)].remove(ip)

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="删除成功！")

    # 2024/4/22 下午9:01 获取指定网站的方向代理列表
    def get_proxy_list(self, get):
        '''
            @name
            @author wzz <2024/4/22 下午9:02>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_path = get.get("proxy_path", "")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        if len(get.proxy_json_conf["proxy_info"]) == 0:
            return public.returnResult(status=False, msg="没有代理信息！")

        subs_filter = get.proxy_json_conf["subs_filter"] if "subs_filter" in get.proxy_json_conf else \
        public.ExecShell("nginx -V 2>&1|grep 'ngx_http_substitutions_filter' -o")[0] != ""

        if get.proxy_path != "":
            for info in get.proxy_json_conf["proxy_info"]:
                if not "proxy_buffering" in info: info["proxy_buffering"] = True
                if info["proxy_path"] == get.proxy_path:
                    info["global_websocket"] = get.proxy_json_conf["websocket"]["websocket_status"]
                    info["subs_filter"] = subs_filter
                    if "http://unix:" in info["proxy_pass"]:
                        info["proxy_pass"] = info["proxy_pass"].replace("http://unix:", "")
                    return public.returnResult(data=info)
            else:
                return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

        return public.returnResult(data=get.proxy_json_conf["proxy_info"])

    # 2024/4/23 上午11:16 获取指定网站的所有配置信息
    def get_global_conf(self, get):
        '''
            @name 获取指定网站的所有配置信息
            @author wzz <2024/4/23 上午11:16>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        return public.returnResult(data=get.proxy_json_conf)

    # 2024/4/22 下午9:04 设置指定网站指定URL的反向代理
    def set_url_proxy(self, get):
        '''
            @name
            @author wzz <2024/4/22 下午9:04>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_path = get.get("proxy_path", "")
        if get.proxy_path == "":
            return public.returnResult(status=False, msg="proxy_path不能为空！")

        get.proxy_host = get.get("proxy_host", "")
        if get.proxy_host == "":
            return public.returnResult(status=False, msg="proxy_host不能为空！")

        get.proxy_pass = get.get("proxy_pass", "")
        if get.proxy_pass == "":
            return public.returnResult(status=False, msg="proxy_pass不能为空！")

        get.proxy_type = get.get("proxy_type", "")
        if get.proxy_type == "":
            return public.returnResult(status=False, msg="proxy_type不能为空！")

        get.proxy_connect_timeout = get.get("proxy_connect_timeout", "60s")
        get.proxy_send_timeout = get.get("proxy_send_timeout", "600s")
        get.proxy_read_timeout = get.get("proxy_read_timeout", "600s")

        get.remark = get.get("remark", "")
        if get.remark != "":
            get.remark = public.xssencode2(get.remark)

        if get.proxy_type == "unix":
            if not get.proxy_pass.startswith("http://unix:"):
                if not get.proxy_pass.startswith("/"):
                    return public.returnResult(status=False,
                                               msg="unix文件路径必须以/或http://unix:开头，如/tmp/flask_app.sock！")
                if not get.proxy_pass.endswith(".sock"):
                    return public.returnResult(status=False, msg="unix文件必须以.sock结尾，如/tmp/flask_app.sock！")
                if not os.path.exists(get.proxy_pass):
                    return public.returnResult(status=False, msg="代理目标不存在！")
                get.proxy_pass = "http://unix:" + get.proxy_pass
        elif get.proxy_type == "http":
            if not get.proxy_pass.startswith("http://") and not get.proxy_pass.startswith("https://"):
                return public.returnResult(status=False, msg="代理目标必须以http://或https://开头！")

        get.websocket = get.get("websocket/d", 1)

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        if get.proxy_json_conf["websocket"]["websocket_status"] and get.websocket != 1:
            return public.returnResult(status=False,
                                       msg="全局websocket为开启状态，不允许单独关闭此URL的websocket支持！")

        for info in get.proxy_json_conf["proxy_info"]:
            if info["proxy_path"] == get.proxy_path:
                info["proxy_host"] = get.proxy_host
                info["proxy_pass"] = get.proxy_pass
                info["proxy_type"] = get.proxy_type
                info["timeout"]["proxy_connect_timeout"] = get.proxy_connect_timeout.replace("s", "")
                info["timeout"]["proxy_send_timeout"] = get.proxy_send_timeout.replace("s", "")
                info["timeout"]["proxy_read_timeout"] = get.proxy_read_timeout.replace("s", "")
                info["websocket"]["websocket_status"] = True if get.websocket == 1 else False
                info["remark"] = get.remark
                break
        else:
            return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="设置成功！")

    # 2024/4/19 下午2:59 添加反向代理
    def add_proxy(self, get):
        '''
            @name
            @author wzz <2024/4/19 下午3:00>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_path = get.get("proxy_path", "")
        if get.proxy_path == "":
            return public.returnResult(status=False, msg="proxy_path不能为空！")

        get.proxy_pass = get.get("proxy_pass", "")
        if get.proxy_pass == "":
            return public.returnResult(status=False, msg="proxy_pass不能为空！")

        get.proxy_host = get.get("proxy_host", "$http_host")
        get.proxy_type = get.get("proxy_type", "http")
        get.remark = get.get("remark", "")
        get.proxy_timeout = "proxy_connect_timeout 60s;\n      proxy_send_timeout 600s;\n      proxy_read_timeout 600s;"

        if get.remark != "":
            get.remark = public.xssencode2(get.remark)
        if get.proxy_type == "unix":
            if not get.proxy_pass.startswith("/"):
                return public.returnResult(status=False, msg="unix文件路径必须以/开头，如/tmp/flask_app.sock！")
            if not get.proxy_pass.endswith(".sock"):
                return public.returnResult(status=False, msg="unix文件必须以.sock结尾，如/tmp/flask_app.sock！")
            if not os.path.exists(get.proxy_pass):
                return public.returnResult(status=False, msg="代理目标不存在！")

            get.proxy_pass = "http://unix:{}".format(get.proxy_pass)
        elif get.proxy_type == "http":
            if not get.proxy_pass.startswith("http://") and not get.proxy_pass.startswith("https://"):
                return public.returnResult(status=False, msg="代理目标必须以http://或https://开头！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        # 2024/4/19 下午3:45 检测是否已经存在proxy_path,有的话就返回错误
        for proxy_info in get.proxy_json_conf["proxy_info"]:
            if proxy_info["proxy_path"] == get.proxy_path:
                return public.returnResult(status=False,
                                           msg="【{}】已存在反向代理中，无法重复添加！".format(get.proxy_path))

        if len(get.proxy_json_conf["basic_auth"]) != 0:
            for i in range(len(get.proxy_json_conf["basic_auth"])):
                if get.proxy_json_conf["basic_auth"][i]["auth_path"] == get.proxy_path:
                    return public.returnResult(status=False, msg="【{}】已存在basicauth中，请先删除再添加反向代理！".format(
                        get.proxy_path))

        sni_conf = ""
        if get.proxy_pass.startswith("https://"):
            sni_conf = "proxy_ssl_server_name on;"
        get.proxy_conf = self._template_proxy_conf.format(
            ip_limit="",
            gzip="",
            proxy_cache="",
            sub_filter="",
            server_log="",
            basic_auth="",
            proxy_pass=get.proxy_pass,
            proxy_host=get.proxy_host,
            proxy_path=get.proxy_path,
            SNI=sni_conf,
            custom_conf="",
            timeout_conf=get.proxy_timeout,
            PROXY_BUFFERING="",
            websocket_support=get.proxy_json_conf["websocket"]["websocket_conf"],
        )

        get.proxy_json_conf["proxy_info"].append({
            "proxy_type": get.proxy_type,
            "proxy_path": get.proxy_path,
            "proxy_pass": get.proxy_pass,
            "proxy_host": get.proxy_host,
            "ip_limit": {
                "ip_black": [],
                "ip_white": [],
            },
            "basic_auth": {},
            "proxy_cache": {
                "cache_status": False,
                "cache_zone": "",
                "static_cache": "",
                "expires": "1d",
                "cache_conf": "",
            },
            "gzip": {
                "gzip_status": False,
                "gzip_min_length": "10k",
                "gzip_comp_level": "6",
                "gzip_types": "text/plain application/javascript application/x-javascript text/javascript text/css application/xml application/json image/jpeg image/gif image/png font/ttf font/otf image/svg+xml application/xml+rss text/x-js",
                "gzip_conf": "gzip on;\n     gzip_min_length 10k;\n     gzip_buffers 4 16k;\n     gzip_http_version 1.1;\n     gzip_comp_level 2;\n     gzip_types text/plain application/javascript application/x-javascript text/javascript text/css application/xml;\n     gzip_vary on;\n     gzip_proxied expired no-cache no-store private auth;\n     gzip_disable \"MSIE [1-6]\.\";",
            },
            "sub_filter": {
                "sub_filter_str": [],
            },
            "websocket": {
                "websocket_status": True,
                "websocket_conf": "proxy_http_version 1.1;\n      proxy_set_header Upgrade $http_upgrade;\n      proxy_set_header Connection $connection_upgrade;",
            },
            "proxy_log": {
                "log_type": "off",
                "log_conf": "",
            },
            "timeout": {
                "proxy_connect_timeout": "60",
                "proxy_send_timeout": "600",
                "proxy_read_timeout": "600",
                "timeout_conf": "proxy_connect_timeout 60s;\n      proxy_send_timeout 600s;\n      proxy_read_timeout 600s;",
            },
            "custom_conf": "",
            "proxy_conf": get.proxy_conf,
            "remark": get.remark,
            "template_proxy_conf": self._template_proxy_conf,
        })

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="添加成功！")

    # 2024/4/22 下午9:34 删除指定网站指定URL的反向代理
    def del_url_proxy(self, get):
        '''
            @name 删除指定网站指定URL的反向代理
            @param get:
            @return:
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_path = get.get("proxy_path", "")
        if get.proxy_path == "":
            return public.returnResult(status=False, msg="proxy_path不能为空！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        for info in get.proxy_json_conf["proxy_info"]:
            if info["proxy_path"] == get.proxy_path:
                get.proxy_json_conf["proxy_info"].remove(info)
                break
        else:
            return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="删除成功！")

    # 2024/4/22 下午9:36 设置指定网站指定URL反向代理的备注
    def set_url_remark(self, get):
        '''
            @name 设置指定网站指定URL反向代理的备注
            @param get:
            @return:
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_path = get.get("proxy_path", "")
        if get.proxy_path == "":
            return public.returnResult(status=False, msg="proxy_path不能为空！")

        get.remark = get.get("remark", "")
        if get.remark != "":
            get.remark = public.xssencode2(get.remark)

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        for info in get.proxy_json_conf["proxy_info"]:
            if info["proxy_path"] == get.proxy_path:
                info["remark"] = get.remark
                break
        else:
            return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="设置成功！")

    # 2024/4/22 下午9:40 添加指定网站指定URL的内容替换
    def add_sub_filter(self, get):
        '''
            @name 添加指定网站指定URL的内容替换
            @param get:
            @return:
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_path = get.get("proxy_path", "")
        if get.proxy_path == "":
            return public.returnResult(status=False, msg="proxy_path不能为空！")

        get.oldstr = get.get("oldstr", "")
        get.newstr = get.get("newstr", "")

        if get.oldstr == "" and get.newstr == "":
            return public.returnResult(status=False, msg="oldstr和newstr不能同时为空！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        get.sub_type = get.get("sub_type", "g")
        if get.sub_type == "":
            get.sub_type = "g"
        import re
        if not re.match(r'^[ior]+$|^g(?!.*o)|^o(?!.*g)$', get.sub_type):
            return public.returnResult(status=False,
                                       msg="get.sub_type 只能包含 'g'、'i'、'o' 或 'r' 中的字母组合，并且 'g' 和 'o' 不能同时存在！")

        is_subs = public.ExecShell("nginx -V 2>&1|grep 'ngx_http_substitutions_filter' -o")[0]
        if not is_subs and re.search(u'[\u4e00-\u9fa5]', get.oldstr + get.newstr):
            return public.returnResult(status=False,
                                       msg="您输入的内容包含中文，检测到当前nginx版本不支持，请尝试重新安装nginx 1.20以上的版本后重试！")

        if get.sub_type != "g" and not is_subs:
            return public.returnResult(status=False,
                                       msg="检测到当前nginx版本仅支持默认替换类型，请尝试重新安装nginx 1.20以上的版本后重试！")

        if not "g" in get.sub_type and not "o" in get.sub_type:
            get.sub_type = "g" + get.sub_type

        for info in get.proxy_json_conf["proxy_info"]:
            if info["proxy_path"] == get.proxy_path:
                for sub in info["sub_filter"]["sub_filter_str"]:
                    if get.oldstr == sub["oldstr"]:
                        return public.returnResult(status=False,
                                                   msg="替换前内容：【{}】的配置信息已存在，请勿重复添加！".format(
                                                       get.oldstr))
                info["sub_filter"]["sub_filter_str"].append(
                    {
                        "sub_type": get.sub_type,
                        "oldstr": get.oldstr,
                        "newstr": get.newstr
                    }
                )
                break
        else:
            return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="设置成功！")

    # 2024/4/22 下午10:00 删除指定网站指定URL的内容替换
    def del_sub_filter(self, get):
        '''
            @name 删除指定网站指定URL的内容替换
            @param get:
            @return:
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_path = get.get("proxy_path", "")
        if get.proxy_path == "":
            return public.returnResult(status=False, msg="proxy_path不能为空！")

        get.oldstr = get.get("oldstr", "")
        get.newstr = get.get("newstr", "")

        if get.oldstr == "" and get.newstr == "":
            return public.returnResult(status=False, msg="oldstr和newstr不能同时为空！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        for info in get.proxy_json_conf["proxy_info"]:
            if info["proxy_path"] == get.proxy_path:
                for sub in info["sub_filter"]["sub_filter_str"]:
                    if get.oldstr == sub["oldstr"]:
                        info["sub_filter"]["sub_filter_str"].remove(sub)
                        break
                else:
                    return public.returnResult(status=False,
                                               msg="未找到替换前内容：【{}】的配置信息！".format(get.oldstr))
                break
        else:
            return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="删除成功！")

    # 2024/4/22 下午10:03 设置指定网站指定URL的内容压缩
    def set_url_gzip(self, get):
        '''
            @name 设置指定网站指定URL的内容压缩
            @param get:
            @return:
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_path = get.get("proxy_path", "")
        if get.proxy_path == "":
            return public.returnResult(status=False, msg="proxy_path不能为空！")

        get.gzip_status = get.get("gzip_status/d", 999)
        if get.gzip_status == 999:
            return public.returnResult(status=False, msg="gzip_status不能为空，请传number 1或0！")
        get.gzip_min_length = get.get("gzip_min_length", "10k")
        get.gzip_comp_level = get.get("gzip_comp_level", "6")
        if get.gzip_min_length[0] == "0" or get.gzip_min_length.startswith("-"):
            return public.returnResult(status=False, msg="gzip_min_length参数不合法，请输入大于0的数字！")
        if get.gzip_comp_level == "0" or get.gzip_comp_level.startswith("-"):
            return public.returnResult(status=False, msg="gzip_comp_level参数不合法，请输入大于0的数字！")
        get.gzip_types = get.get(
            "gzip_types",
            "text/plain application/javascript application/x-javascript text/javascript text/css application/xml application/json image/jpeg image/gif image/png font/ttf font/otf image/svg+xml application/xml+rss text/x-js"
        )

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        for info in get.proxy_json_conf["proxy_info"]:
            if info["proxy_path"] == get.proxy_path:
                info["gzip"]["gzip_status"] = True if get.gzip_status == 1 else False
                if get.gzip_status == 1:
                    info["gzip"]["gzip_types"] = get.gzip_types
                    info["gzip"]["gzip_min_length"] = get.gzip_min_length
                    info["gzip"]["gzip_comp_level"] = get.gzip_comp_level
                    info["gzip"]["gzip_conf"] = ("gzip on;"
                                                 "\n      gzip_min_length {gzip_min_length};"
                                                 "\n      gzip_buffers 4 16k;"
                                                 "\n      gzip_http_version 1.1;"
                                                 "\n      gzip_comp_level {gzip_comp_level};"
                                                 "\n      gzip_types {gzip_types};"
                                                 "\n      gzip_vary on;"
                                                 "\n      gzip_proxied expired no-cache no-store private auth;"
                                                 "\n      gzip_disable \"MSIE [1-6]\.\";").format(
                        gzip_min_length=get.gzip_min_length,
                        gzip_comp_level=get.gzip_comp_level,
                        gzip_types=get.gzip_types,
                    )
                else:
                    info["gzip"]["gzip_conf"] = ""
                break
        else:
            return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="设置成功！")

    # 2024/4/22 下午10:15 添加指定网站指定URL的IP黑白名单
    def add_url_ip_limit(self, get):
        '''
            @name 添加指定网站指定URL的IP黑白名单
            @author wzz <2024/4/22 下午10:16>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_path = get.get("proxy_path", "")
        if get.proxy_path == "":
            return public.returnResult(status=False, msg="proxy_path不能为空！")

        get.ip_type = get.get("ip_type", "black")
        if get.ip_type not in ["black", "white"]:
            return public.returnResult(status=False, msg="ip_type参数错误，必须传black或white！")

        get.ips = get.get("ips", "")
        if get.ips == "":
            return public.returnResult(status=False, msg="ips不能为空，请输入IP，一行一个！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        get.ips = get.ips.split("\n")
        for info in get.proxy_json_conf["proxy_info"]:
            if info["proxy_path"] == get.proxy_path:
                for ip in get.ips:
                    if get.ip_type == "black":
                        if not ip in info["ip_limit"]["ip_black"]:
                            info["ip_limit"]["ip_black"].append(ip)
                    else:
                        if not ip in info["ip_limit"]["ip_white"]:
                            info["ip_limit"]["ip_white"].append(ip)
                break
        else:
            return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="设置成功！")

    # 2024/4/22 下午10:21 删除指定网站指定URL的IP黑白名单
    def del_url_ip_limit(self, get):
        '''
            @name 删除指定网站指定URL的IP黑白名单
            @param get:
            @return:
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_path = get.get("proxy_path", "")
        if get.proxy_path == "":
            return public.returnResult(status=False, msg="proxy_path不能为空！")

        get.ip_type = get.get("ip_type", "black")
        if get.ip_type not in ["black", "white"]:
            return public.returnResult(status=False, msg="ip_type参数错误，必须传black或white！")

        get.ip = get.get("ip", "")
        if get.ip == "":
            return public.returnResult(status=False, msg="ip不能为空，请输入IP！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        for info in get.proxy_json_conf["proxy_info"]:
            if info["proxy_path"] == get.proxy_path:
                if get.ip in info["ip_limit"]["ip_{ip_type}".format(ip_type=get.ip_type)]:
                    info["ip_limit"]["ip_{ip_type}".format(ip_type=get.ip_type)].remove(get.ip)
                break
        else:
            return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="设置成功！")

    # 2024/4/24 上午11:21 批量删除指定网站指定URL的IP黑白名单
    def batch_del_url_ip_limit(self, get):
        '''
            @name 批量删除指定网站指定URL的IP黑白名单
            @author wzz <2024/4/24 上午11:22>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.ip_type = get.get("ip_type", "black")
        if get.ip_type not in ["black", "white", "all"]:
            return public.returnResult(status=False, msg="ip_type参数错误，必须传black或white！")

        get.ips = get.get("ips", "")
        if get.ips == "":
            return public.returnResult(status=False, msg="ips不能为空，请输入IP，一行一个！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        for info in get.proxy_json_conf["proxy_info"]:
            if info["proxy_path"] == get.proxy_path:
                get.ips = get.ips.split("\n")
                if get.ip_type == "all":
                    for ip in get.ips:
                        if ip in info["ip_limit"]["ip_black"]:
                            info["ip_limit"]["ip_black"].remove(ip)
                        if ip in info["ip_limit"]["ip_white"]:
                            info["ip_limit"]["ip_white"].remove(ip)
                else:
                    for ip in get.ips:
                        if ip in info["ip_limit"]["ip_{ip_type}".format(ip_type=get.ip_type)]:
                            info["ip_limit"]["ip_{ip_type}".format(ip_type=get.ip_type)].remove(ip)
                break
        else:
            return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="删除成功！")

    # 2024/4/22 下午8:14 设置指定网站指定URL的缓存
    def set_url_cache(self, get):
        '''
            @name 设置指定网站指定URL的缓存
            @param get:
            @return:
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.cache_status = get.get("cache_status/d", 999)
        if get.cache_status == 999:
            return public.returnResult(status=False, msg="cache_status不能为空，请传number 1或0！")

        get.expires = get.get("expires", "1d")
        if get.expires[0] == "0" or get.expires.startswith("-"):
            return public.returnResult(status=False, msg="expires参数不合法，请输入大于0的数字！")

        expires = "expires {}".format(get.expires)

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        static_cache = ("\n    location ~ .*\\.(css|js|jpe?g|gif|png|webp|woff|eot|ttf|svg|ico|css\.map|js\.map)$"
                        "\n    {{"
                        "\n        {expires};"
                        "\n        error_log /dev/null;"
                        "\n        access_log /dev/null;"
                        "\n    }}").format(
            expires=expires,
        )

        for info in get.proxy_json_conf["proxy_info"]:
            if info["proxy_path"] == get.proxy_path:
                info["proxy_cache"]["cache_status"] = True if get.cache_status == 1 else False
                info["proxy_cache"]["expires"] = get.expires
                if get.cache_status == 1:
                    info["proxy_cache"]["cache_conf"] = ("\n    proxy_cache {cache_zone};"
                                                         "\n    proxy_cache_key $host$uri$is_args$args;"
                                                         "\n    proxy_ignore_headers Set-Cookie Cache-Control expires X-Accel-Expires;"
                                                         "\n    proxy_cache_valid 200 304 301 302 {expires};"
                                                         "\n    proxy_cache_valid 404 1m;"
                                                         "{static_cache}").format(
                        cache_zone=get.proxy_json_conf["proxy_cache"]["cache_zone"],
                        expires=get.expires,
                        static_cache=static_cache,
                    )
                else:
                    info["proxy_cache"]["cache_conf"] = ""
                break
        else:
            return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="设置成功！")

    # 2024/4/24 上午9:57 设置指定网站指定URL的自定义配置
    def set_url_custom_conf(self, get):
        '''
            @name 设置指定网站指定URL的自定义配置
            @author wzz <2024/4/24 上午9:58>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_path = get.get("proxy_path", "")
        if get.proxy_path == "":
            return public.returnResult(status=False, msg="proxy_path不能为空！")

        get.custom_conf = get.get("custom_conf", "")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        for info in get.proxy_json_conf["proxy_info"]:
            if info["proxy_path"] == get.proxy_path:
                info["custom_conf"] = get.custom_conf
                break
        else:
            return public.returnResult(status=False, msg="未找到此URL【{}】的代理信息！".format(get.proxy_path))

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="设置成功！")

    # 2024/4/24 下午5:39 获取指定网站的网站日志
    def GetSiteLogs(self, get):
        '''
            @name 获取指定网站的网站日志
            @author wzz <2024/4/24 下午5:39>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.type = get.get("type", "access")
        log_name = get.site_name
        if get.type != "access":
            log_name = get.site_name + ".error"

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        if get.proxy_json_conf["proxy_log"]["log_type"] == "default":
            log_file = public.get_logs_path() + "/" + log_name + '.log'
        elif get.proxy_json_conf["proxy_log"]["log_type"] == "file":
            log_file = get.proxy_json_conf["proxy_log"]["log_path"] + "/" + log_name + '.log'
        else:
            return public.returnResult(data={"msg": "", "size": 0})

        if os.path.exists(log_file):
            return public.returnResult(
                data={
                    "msg": self.xsssec(public.GetNumLines(log_file, 1000)),
                    "size": public.to_size(os.path.getsize(log_file))
                }
            )

        return public.returnResult(data={"msg": "", "size": 0})

    # 2024/4/25 上午10:51 清理指定网站的反向代理缓存
    def clear_cache(self, get):
        '''
            @name 清理指定网站的反向代理缓存
            @author wzz <2024/4/25 上午10:51>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        cache_dir = "{sites_config_path}/{site_name}/proxy_cache_dir".format(sites_config_path=self.sites_config_path, site_name=get.site_name)
        if os.path.exists(cache_dir):
            public.ExecShell("rm -rf {cache_dir}/*".format(cache_dir=cache_dir))

            public.serviceReload()
            return public.returnResult(msg="清理成功！")

        return public.returnResult(msg="清理失败，缓存目录不存在！")

    # 2024/4/25 下午9:24 设置指定网站的https端口
    def set_https_port(self, get):
        '''
            @name 设置指定网站的https端口
            @author wzz <2024/4/25 下午9:24>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.https_port = get.get("https_port", "443")
        if not public.checkPort(get.https_port) and get.https_port != "443":
            return public.returnResult(status=False, msg="https端口【{}】不合法！".format(get.https_port))

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        get.proxy_json_conf["https_port"] = get.https_port

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="设置成功！")

    # 2024/4/20 下午2:38 保存额外的配置文件
    def save_block_config(self, get):
        '''
            @name 保存配置文件
            @param get:
            @return:
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.conf_type = get.get("conf_type", "")
        if get.conf_type == "":
            return public.returnResult(status=False, msg="conf_type不能为空！")

        get.body = get.get("body", "")
        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        if get.conf_type == "http_block":
            get.proxy_json_conf["http_block"] = get.body
        else:
            get.proxy_json_conf["server_block"] = get.body

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="保存成功！")

    # 2024/4/20 下午2:22 获取配置文件
    def get_nginx_config(self, get):
        '''
            @name
            @author wzz <2024/4/20 下午2:22>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        site_conf = public.readFile(public.get_setup_path() + '/panel/vhost/nginx/' + get.site_name + '.conf')
        ssl_conf = get.proxy_json_conf["ssl_info"]["ssl_conf"].format(
            site_name=get.site_name,
        )
        if get.proxy_json_conf["ssl_info"]["force_https"]:
            ssl_conf = get.proxy_json_conf["ssl_info"]["force_ssl_conf"].format(
                site_name=get.site_name,
                force_conf=get.proxy_json_conf["ssl_info"]["force_ssl_conf"],
            )

        if "如果反代网站访问异常且这里已经配置了内容，请优先排查此处的配置是否正确" in get.proxy_json_conf[
            "http_block"]:
            http_block = get.proxy_json_conf["http_block"]
        else:
            http_block = '''# 可设置server|upstream|map等所有http字段，如：
        # server {{
        #     listen 10086;
        #     server_name ...
        # }}
        # upstream stream_ser {{
        #     server back_test.com;
        #     server ...
        # }}
        {default_describe}
        {http_block}'''.format(
                default_describe=self.init_site_json["default_describe"],
                http_block=get.proxy_json_conf["http_block"],
            )

        if "如果反代网站访问异常且这里已经配置了内容，请优先排查此处的配置是否正确" in get.proxy_json_conf[
            "server_block"]:
            server_block = get.proxy_json_conf["server_block"]
        else:
            server_block = '''# 可设置server|location等所有server字段，如：
        # location /web {{
        #     try_files $uri $uri/ /index.php$is_args$args;
        # }}
        # error_page 404 /diy_404.html;
        {default_describe}
        {server_block}'''.format(
                default_describe=self.init_site_json["default_describe"],
                server_block=get.proxy_json_conf["server_block"],
            )

        data = {
            "site_conf": site_conf if not site_conf is False else "",
            "http_block": http_block,
            "server_block": server_block,
            "ssl_conf": ssl_conf,
        }

        return public.returnResult(data=data)

    # 2024/4/20 上午9:17 获取域名列表和https端口
    def get_domain_list(self, get):
        '''
            @name 获取域名列表和https端口
            @param get:
            @return:
        '''
        get.id = get.get("id", "")
        if get.id == "":
            return public.returnResult(status=False, msg="id不能为空！")
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        select_result = dp.sql("docker_domain").where("pid=?", get.id).select()
        if not select_result:
            return public.returnResult(status=False, msg="未找到此ID【{}】的域名信息！".format(get.id))

        # 2024/4/20 上午12:02 更新json文件
        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        result_data = {}
        result_data["domain_list"] = select_result
        if get.proxy_json_conf["ssl_info"]["ssl_status"]:
            if not "https_port" in get.proxy_json_conf or get.proxy_json_conf["https_port"] == "":
                get.proxy_json_conf["https_port"] = "443"
            result_data["https_port"] = get.proxy_json_conf["https_port"]
        else:
            result_data["https_port"] = "未开启HTTPS"

        # 2024/4/20 上午9:21 domain_list里面没有的域名健康状态显示为0
        for domain in result_data["domain_list"]:
            domain["healthy"] = 1
            if domain["name"] not in get.proxy_json_conf["domain_list"]:
                domain["healthy"] = 0

        return public.returnResult(data=result_data)

    # 2024/11/7 17:05 设置指定网站的伪静态
    def set_site_rewrite(self, get):
        '''
            @name 设置指定网站的伪静态
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.rewrite_conf = get.get("rewrite_conf", "")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        get.proxy_json_conf["rewrite_conf"] = get.rewrite_conf

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="设置成功！")

    # 2024/11/7 17:08 获取指定网站的伪静态
    def get_site_rewrite(self, get):
        '''
            @name 获取指定网站的伪静态
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        return public.returnResult(data=get.proxy_json_conf["rewrite_conf"])

    # 2024/10/31 10:29 设置指定网站监听IPv6
    def set_site_ipv6(self, get):
        '''
            @name 设置指定网站监听IPv6
        '''
        get.site_name = get.get("site_name", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        get.ipv6_status = get.get("ipv6_status/d", 0)

        get.proxy_json_conf["ipv6_status"] = True if get.ipv6_status == 1 else False

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="设置成功！")

    # 2024/10/31 10:26 获取指定网站的默认文档
    def get_index(self, get):
        '''
            @name 获取指定网站的默认文档
        '''
        get.id = get.get("id", None)
        if get.id is None: return public.returnResult(status=False, msg="id不能为空！")
        get.site_name = get.get("site_name", None)
        if get.site_name is None: return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        return public.returnResult(True, data=get.proxy_json_conf["index_conf"].replace(" ", "\n"))

    # 2024/10/31 10:26 设置指定网站的默认文档
    def set_index(self, get):
        '''
            @name 设置指定网站的默认文档
        '''
        get.id = get.get("id", None)
        if get.id is None: return public.returnResult(status=False, msg="id不能为空！")
        get.site_name = get.get("site_name", None)
        if get.site_name is None: return public.returnResult(status=False, msg="site_name不能为空！")
        get.index = get.get("index", None)
        if get.index is None: return public.returnResult(status=False, msg="index不能为空！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        get.proxy_json_conf["index_conf"] = get.index.replace("\n", " ")

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="设置成功！")

    def read_file(self, path):
        '''
            @name
        '''
        data = {}
        try:
            fp = open(path, 'rb')
            if fp:
                srcBody = fp.read()
                fp.close()
                try:
                    data['encoding'] = 'utf-8'
                    data['data'] = srcBody.decode(data['encoding'])
                except:
                    try:
                        data['encoding'] = 'GBK'
                        data['data'] = srcBody.decode(data['encoding'])
                    except:
                        try:
                            data['encoding'] = 'BIG5'
                            data['data'] = srcBody.decode(data['encoding'])
                        except:
                            return public.returnResult(False, '文件编码不被兼容，无法正确读取文件!')
        except OSError as e:
            return public.returnResult(False, '打开文件失败，文件可能被其它进程占用!')
        except Exception as e:
            return public.returnResult(False, '打开文件失败，{}'.format(str(e)))

        return data

    # 2024/11/8 14:54 获取指定默认页面内容
    def get_default_body(self, get):
        '''
            @name 获取指定默认页面内容
        '''
        get.default_type = get.get("default_type", "all")
        if not get.default_type in ("all", "index", "404", "not_found", "stop"):
            return public.returnResult(status=False, msg="default_type参数错误！")

        pl_path = os.path.join(self.sites_config_path, "no_auto_create_404.pl")
        auto_create_404 = True if not os.path.exists(pl_path) else False

        if get.default_type == "not_found":
            not_found_body = self.read_file("/www/server/nginx/html/index.html")
            if not "encoding" in not_found_body:
                public.writeFile("/www/server/nginx/html/index.html", getattr(self, "default_not_found_body"))
                not_found_body = {"default_not_found_body": getattr(self, "default_not_found_body"), "encoding": "utf-8"}
            return public.returnResult(True, data={"not_found": not_found_body, "auto_create_404": auto_create_404})

        if get.default_type != "all":
            diy_filename = os.path.join(self.sites_config_path, "default_{}.html".format(get.default_type))
            if not os.path.exists(diy_filename):
                if os.path.isfile("/www/dk_project/runtime/templates/html/default_{}.html".format(get.default_type)):
                    public.writeFile(diy_filename, public.readFile("/www/dk_project/runtime/templates/html/default_{}.html".format(get.default_type)))
                else:
                    public.writeFile(diy_filename, getattr(self, "default_{}_body".format(get.default_type)))

            diy_body = self.read_file(diy_filename)
            if not "encoding" in diy_body:
                public.writeFile(diy_filename, getattr(self, "default_{}_body".format(get.default_type)))
                return public.returnResult(True, data={"default_{}_body".format(get.default_type): getattr(self, "default_{}_body".format(get.default_type)), "encoding": "utf-8"})

            return public.returnResult(True, data={get.default_type: diy_body, "auto_create_404": auto_create_404})
        else:
            return_result = {}
            for default_type in ("index", "404", "stop"):
                diy_filename = os.path.join(self.sites_config_path, "default_{}.html".format(default_type))
                if not os.path.exists(diy_filename):
                    if os.path.isfile("/www/dk_project/runtime/templates/html/default_{}.html".format(default_type)):
                        public.writeFile(diy_filename, public.readFile("/www/dk_project/runtime/templates/html/default_{}.html".format(default_type)))
                    else:
                        public.writeFile(diy_filename, getattr(self, "default_{}_body".format(default_type)))

                diy_body = self.read_file(diy_filename)
                if not "encoding" in diy_body:
                    public.writeFile(diy_filename, getattr(self, "default_{}_body".format(default_type)))
                    return_result[default_type] = {"default_{}_body".format(default_type): getattr(self, "default_{}_body".format(default_type)), "encoding": "utf-8"}
                else:
                    return_result[default_type] = diy_body

            not_found_body = self.read_file("/www/server/nginx/html/index.html")
            if not "encoding" in not_found_body:
                public.writeFile("/www/server/nginx/html/index.html", getattr(self, "default_not_found_body"))
                not_found_body = {"default_not_found_body": getattr(self, "default_not_found_body"), "encoding": "utf-8"}
            return_result["not_found"] = not_found_body
            return_result["auto_create_404"] = auto_create_404

            return public.returnResult(True, data=return_result)

    # 2024/11/8 15:33 修改指定默认页面内容
    def set_default_body(self, get):
        '''
            @name 修改指定默认页面内容
        '''
        get.default_type = get.get("default_type", None)
        if not get.default_type in ("index", "404", "not_found", "stop"):
            return public.returnResult(status=False, msg="default_type参数错误！")
        get.encoding = get.get("encoding", "utf-8")

        get.default_body = get.get("default_body", None)
        if not get.default_body:
            return public.returnResult(status=False, msg="default_body不能为空！")

        # 2024/11/8 15:35 检测是不是html内容
        if not re.match(r"<html.*?>.*?</html>", get.default_body, re.S) and not re.match(r"<.*?doctype.*?html>", get.default_body, re.S):
            return public.returnResult(status=False, msg="必须输入html内容！")

        if get.default_type == "not_found":
            public.writeFile("/www/server/nginx/html/index.html", get.default_body)
            return public.returnResult(msg="设置成功！")

        diy_filename = os.path.join(self.sites_config_path, "default_{}.html".format(get.default_type))

        get.path = diy_filename
        get.data = get.default_body
        import files
        f = files.files()
        return f.SaveFileBody(get)

    # 2024/11/8 15:44 设置是否在创建网站时自动创建404.html页面
    def set_auto_create_404(self, get):
        '''
            @name 设置是否在创建网站时自动创建404.html页面
        '''
        get.auto_create = get.get("auto_create", 1)
        pl_path = os.path.join(self.sites_config_path, "no_auto_create_404.pl")

        if int(get.auto_create) == 0:
            public.writeFile(pl_path, "False")
        else:
            public.ExecShell("rm -f {}".format(pl_path))

        return public.returnResult(msg="设置成功！")

    # 2024/11/8 15:51 设置指定网站404页面的开启状态
    def set_404_status(self, get):
        '''
            @name 设置指定网站404页面的开启状态
        '''
        get.site_name = get.get("site_name", None)
        if not get.site_name:
            return public.returnResult(status=False, msg="site_name不能为空！")
        get.status = get.get("status", 0)

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        if int(get.status) == 1:
            err_age_404 = "error_page 404 /404.html;"
        else:
            err_age_404 = "#error_page 404 /404.html;"

        get.proxy_json_conf["err_age_404"] = err_age_404

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="设置成功！")

    # 2024/11/8 15:54 设置指定网站的404.html页面内容
    def set_404_body(self, get):
        '''
            @name 设置指定网站的404.html页面内容
        '''
        get.site_name = get.get("site_name", None)
        if not get.site_name:
            return public.returnResult(status=False, msg="site_name不能为空！")
        get.file_body = get.get("file_body", "")
        get.encoding = get.get("encoding", "utf-8")

        # 2024/11/8 15:35 检测是不是html内容
        if not re.match(r"<html.*?>.*?</html>", get.file_body, re.S) and not re.match(r"<.*?doctype.*?html>", get.file_body, re.S):
            return public.returnResult(status=False, msg="必须输入html内容！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        get.site_path = get.proxy_json_conf["site_path"]
        get.run_path = get.proxy_json_conf["run_path"]

        if get.run_path == "/":
            file_path = os.path.join(get.site_path, "404.html")
        else:
            file_path = os.path.join(get.site_path, get.run_path, "404.html")
        get.path = file_path
        get.data = get.file_body
        import files
        f = files.files()
        return f.SaveFileBody(get)

    # 2024/11/14 14:56 获取指定网站的404.html页面内容
    def get_404_body(self, get):
        '''
            @name 获取指定网站的404.html页面内容
        '''
        get.site_name = get.get("site_name", None)
        if not get.site_name:
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        get.site_path = get.proxy_json_conf["site_path"]
        get.run_path = get.proxy_json_conf["run_path"]

        if get.run_path == "/":
            file_path = os.path.join(get.site_path, "404.html")
        else:
            file_path = os.path.join(get.site_path, get.run_path, "404.html")

        get.path = file_path
        import files
        f = files.files()
        read_result = f.GetFileBody(get)
        if not read_result["status"]:
            return {
                "auto_save": None,
                "data": "",
                "encoding": "utf-8",
                "historys": [],
                "only_read": False,
                "size": 0,
                "st_mtime": str(int(time.time())),
                "status": True,
            }
        return read_result

    # 2024/11/8 14:42 创建默认html文件
    def create_default_html(self, get):
        '''
            @name 创建默认html文件
        '''
        self.get_default_body(get)

        if not os.path.exists(os.path.join(get.site_path, 'index.html')):
            public.writeFile(os.path.join(get.site_path, 'index.html'), public.readFile(os.path.join(self.sites_config_path, "default_index.html")))
            public.ExecShell('chown www:www {}'.format(os.path.join(get.site_path, 'index.html')))
            public.ExecShell('chmod 755 {}'.format(os.path.join(get.site_path, 'index.html')))
        if not os.path.exists(os.path.join(self.sites_config_path, "no_auto_create_404.pl")):
            if not os.path.exists(os.path.join(get.site_path, '404.html')):
                public.writeFile(os.path.join(get.site_path, '404.html'), public.readFile(os.path.join(self.sites_config_path, "default_404.html")))
                public.ExecShell('chown www:www {}'.format(os.path.join(get.site_path, '404.html')))
                public.ExecShell('chmod 755 {}'.format(os.path.join(get.site_path, '404.html')))
        if not os.path.isdir(os.path.join(self.sites_config_path, "stop")):
            os.makedirs(os.path.join(self.sites_config_path, "stop"))
            public.ExecShell('chown -R www:www {}'.format(os.path.join(self.sites_config_path, "stop")))
            public.ExecShell('chmod -R 755 {}'.format(os.path.join(self.sites_config_path, "stop")))
        if not os.path.isfile(os.path.join(self.sites_config_path, "stop/index.html")):
            public.writeFile(os.path.join(self.sites_config_path, "stop/index.html"), public.readFile(os.path.join(self.sites_config_path, "default_stop.html")))
            public.ExecShell('chown www:www {}'.format(os.path.join(self.sites_config_path, "stop/index.html")))
            public.ExecShell('chmod 755 {}'.format(os.path.join(self.sites_config_path, "stop/index.html")))

    # 2024/11/8 16:23 获取默认站点
    def get_default_site(self, get):
        '''
            @name 获取默认站点
        '''
        site_names = dp.sql("docker_sites").where("status=?", 1).field("name").order("id desc").select()
        default_site = public.readFile('/www/server/panel/data/defaultSite.pl')
        return public.returnResult(True, data={"sites": site_names, "defaultSite": default_site})

    # 2024/11/8 16:30 设置默认站点
    def set_default_site(self, get):
        '''
            @name 设置默认站点
        '''
        get.site_name = get.get("site_name", "")
        if not get.site_name:
            return public.returnResult(status=False, msg="site_name不能为空！")

        old_default_site = public.readFile('/www/server/panel/data/defaultSite.pl')
        if not old_default_site:
            if get.site_name == "0":
                public.ExecShell("rm -f /www/server/panel/data/defaultSite.pl")
                return public.returnResult(msg="设置成功！")

        if old_default_site == get.site_name:
            return public.returnResult(status=False, msg="此站点已经是默认站点！")
        else:
            public.ExecShell("rm -f /www/server/panel/data/defaultSite.pl")

            args = public.dict_obj()
            args.site_name = old_default_site
            args.proxy_json_conf = self.read_json_conf(args)

            if args.proxy_json_conf:
                update_result = self.update_nginx_conf(args)
                if not update_result["status"]:
                    return public.returnResult(status=False, msg=update_result["msg"])

        if get.site_name == "0":
            public.ExecShell("rm -f /www/server/panel/data/defaultSite.pl")
            return public.returnResult(msg="设置成功！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        public.writeFile('/www/server/panel/data/defaultSite.pl', get.site_name)

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="设置成功！")

    # 2024/11/8 17:13 将原来反代项目里面所有docker的反代写入新的docker_sites数据库中
    def sync_docker_sites(self, get):
        '''
            @name 将原来反代项目里面所有docker的反代写入新的docker_sites数据库中
            @param get:
            @return:
        '''
        # 2024/11/8 17:15 获取所有sites数据库中proxy类型的数据
        old_proxy_sites = public.M("sites").where("project_type=?", ("proxy",)).select()

        from safeModel.firewallModel import main as firewall_main
        from mod.project.proxy.comMod import main as proxy_main

        for old_site in old_proxy_sites:
            p_json_file = "/www/server/proxy_project/sites/{site_name}/{site_name}.json".format(site_name=old_site["name"])
            if not os.path.exists(p_json_file): continue
            args = public.dict_obj()
            args.site_name = old_site["name"]
            get.proxy_json_conf = proxy_main().read_json_conf(args)
            if not get.proxy_json_conf: continue

            if not "proxy_info" in get.proxy_json_conf: continue
            if len(get.proxy_json_conf["proxy_info"]) < 1: continue
            public.writeFile(os.path.join(self.sites_config_path, "{site_name}.json".format(site_name=old_site["name"])), json.dumps(get.proxy_json_conf))

            for proxy_info in get.proxy_json_conf["proxy_info"]:
                if not "proxy_pass" in proxy_info: continue
                if not proxy_info["proxy_pass"]: continue

                proxy_port = proxy_info["proxy_pass"].split(":")[-1]
                args = public.dict_obj()
                args.port = proxy_port
                res_dict = firewall_main().get_listening_processes(args)
                if not "process_name" in res_dict: continue
                if not res_dict["process_name"]: continue
                if "docker" in res_dict["process_name"]:

                    container_id = None
                    project_name = None
                    dk_site_info = dp.sql('dk_sites').where('name=?', (old_site["name"],)).find()
                    if dk_site_info:
                        container_id = dk_site_info["container_id"]
                        project_name = dk_site_info["container_name"]

                    get.service_info = {
                        "name": old_site["name"],
                        "port": args.port,
                        "project_name": project_name,
                        "project_path": None,
                    }
                    get.old_info = json.dumps(old_site)

                    pdata = {
                        "name": old_site["name"],
                        "path": old_site["path"],
                        "run_path": "/",
                        "remark": public.xssencode2(old_site["ps"]),
                        "type": "proxy",
                        "service_info": json.dumps(get.service_info),
                        "old_info": get.old_info,
                        "addtime": old_site["addtime"],
                        "container_id": container_id,
                    }

                    get.pid = dp.sql("docker_sites").insert(pdata)
                    if not get.pid:
                        break

                    domain_list = public.M("domain").where("pid=?", (old_site["id"],)).field("name").find()
                    for domain in domain_list:
                        dp.sql("docker_domain").insert({
                            "name": domain,
                            "pid": get.pid,
                            "port": "80" if ":" not in domain else domain.split(":")[1],
                            "addtime": old_site["addtime"],
                        })
                    break

        public.writeFile("{}/synced_docker_sites.pl".format(self.sites_config_path), "True")

        return public.returnResult(True)

    # 2024/11/13 14:59 获取分类列表
    def get_site_types(self, get):
        '''
            @name 获取分类列表
        '''
        now_time = public.getDate()
        check_default_result = dp.sql("docker_site_classifys").where("name=?", ("默认分类",)).find()
        if not check_default_result:
            dp.sql("docker_site_classifys").insert({
                "id": 0,
                "name": "默认分类",
                "ps": "默认分类",
                "addtime": now_time
            })
        check_stop_result = dp.sql("docker_site_classifys").where("name=?", ("已停止的网站",)).find()
        if not check_stop_result:
            dp.sql("docker_site_classifys").insert({
                "id": -2,
                "name": "已停止的网站",
                "ps": "已停止的网站",
                "addtime": now_time
            })

        # 查询所有分类
        classify_list = dp.sql("docker_site_classifys").order("id desc").select()

        # 2024/11/28 15:09 排序，id为0的默认分类排在最前面，-2为已停止的网站排在第二
        new_classify_list = []
        for classify in classify_list:
            if classify["id"] == 0:
                new_classify_list.insert(0, classify)
            elif classify["id"] == -2:
                new_classify_list.insert(1, classify)
            else:
                new_classify_list.append(classify)

        return public.returnResult(True, data=new_classify_list)

    # 2024/11/13 15:19 添加分类
    def add_site_type(self, get):
        '''
            @name 添加分类
        '''
        get.name = get.get("name", "")
        if not get.name:
            return public.returnResult(status=False, msg="name不能为空！")

        get.ps = get.get("ps", "")
        now_time = public.getDate()
        get.id = dp.sql("docker_site_classifys").insert({
            "name": public.xssencode2(get.name),
            "ps": public.xssencode2(get.ps),
            "addtime": now_time
        })

        return public.returnResult(msg="添加成功！")

    # 2024/11/13 15:20 编辑分类
    def edit_site_type(self, get):
        '''
            @name 编辑分类
        '''
        get.id = get.get("id", "")
        if not get.id:
            return public.returnResult(status=False, msg="id不能为空！")

        get.name = get.get("name", "")
        if not get.name:
            return public.returnResult(status=False, msg="name不能为空！")

        get.ps = get.get("ps", "")
        now_time = public.getDate()
        dp.sql("docker_site_classifys").where("id=?", (get.id,)).update({
            "name": public.xssencode2(get.name),
            "ps": public.xssencode2(get.ps),
            "addtime": now_time
        })

        return public.returnResult(msg="编辑成功！")

    # 2024/11/13 15:20 删除分类
    def del_site_type(self, get):
        '''
            @name 删除分类
        '''
        get.id = get.get("id", "")
        if not get.id:
            return public.returnResult(status=False, msg="id不能为空！")

        dp.sql("docker_site_classifys").where("id=?", (get.id,)).delete()

        # 2024/11/13 15:21 将所有docker_sites里面的classify字段设置为0
        dp.sql("docker_sites").where("classify=?", (get.id,)).update({"classify": 0})
        return public.returnResult(msg="删除成功！")

    # 2024/11/13 15:24 为指定网站设置分类
    def set_site_type(self, get):
        '''
            @name 为指定网站设置分类
        '''
        get.id = get.get("id", None)
        if get.id is None:
            return public.returnResult(status=False, msg="id不能为空！")

        get.classify = get.get("classify", 0)

        if type(get.id) == str:
            try:
                get.id = json.loads(get.id)
            except:
                return public.returnResult(status=False, msg="id参数错误！")

        for id in get.id:
            dp.sql("docker_sites").where("id=?", (id,)).update({"classify": get.classify})

        return public.returnResult(msg="设置成功！")

    def GetSiteDomain(self,get):
        """
        @name 获取网站域名对应的站点名
        @param cert_list 证书域名列表
        @auther hezhihong
        return 证书域名对应的站点名字典，如证书域名未绑定则为空
        """
        all_site=[]  #所有站点名列表
        cert_list=[] #证书域名列表
        site_list=[] #证书域名列表对应的站点名列表
        all_domain = [] #所有域名列表
        try:
            cert_list=json.loads(get.cert_list)
        except:pass
        result={}
        #取所有站点名和所有站点的绑定域名
        all_sites=public.M('docker_sites').field('name').select()
        for site in all_sites:
            all_site.append(site['name'])
            if not cert_list:continue
            tmp_dict={}
            tmp_dict['name']=site['name']
            pid = public.M('docker_sites').where("name=?",(site['name'],)).getField('id')
            domain_list=public.M('docker_domain').where("pid=?",(pid,)).field('name').select()
            for domain in domain_list:
                all_domain.append(domain['name'])
        #取证书域名所在的所有域名列表
        site_domain=[]#证书域名对应的站点名列表
        if cert_list and all_domain:
            for cert in cert_list:
                d_cert=''
                if re.match("^\*\..*",cert):
                    d_cert=cert.replace('*.','')
                for domain in all_domain:
                    if cert == domain:
                        site_domain.append(domain)
                    else:
                        replace_str=domain.split('.')[0]+'.'
                        if d_cert and d_cert==domain.replace(replace_str,''):
                            site_domain.append(domain)
        #取证书域名对应的站点名
        for site in site_domain:
            site_id=public.M('docker_domain').where("name=?",(site,)).getField('pid')
            site_name=public.M('docker_sites').where("id=?",(site_id,)).getField('name')
            site_list.append(site_name)
        site_list=sorted(set(site_list),key=site_list.index)
        result['all']=all_site
        result['site']=site_list
        return  result

    # 2024/11/18 09:30 获取防跨站状态和运行目录信息
    def GetDirUserINI(self, get):
        '''
            @name 获取防跨站状态和运行目录信息
        '''
        get.id = get.get("id", None)
        if not get.id:
            return public.returnResult(status=False, msg="id不能为空！")

        find_result = dp.sql("docker_sites").where("id=?", get.id).find()
        if not find_result:
            return public.returnResult(status=False, msg="未找到此ID【{}】的站点信息！".format(get.id))

        data = {'userini': False}
        user_ini_file = os.path.join(find_result["path"], ".user.ini")
        try:
            user_ini_conf = public.readFile(user_ini_file)
        except OSError:
            user_ini_conf = {}
        if user_ini_conf and "open_basedir" in user_ini_conf:
            data['userini'] = True

        # 2024/11/18 09:35 获取runpath
        p_data = {}
        path = find_result["path"]

        filename = os.path.join(public.get_setup_path(), 'panel/vhost/nginx', find_result["name"] + '.conf')
        if os.path.exists(filename):
            conf = public.readFile(filename)
            rep = '\s*root\s+(.+);'
            tmp1 = re.search(rep, conf)
            if tmp1: path = tmp1.groups()[0]

        if find_result["path"] == path:
            p_data['runPath'] = '/'
        else:
            p_data['runPath'] = path.replace(find_result["path"], '')

        dirnames = []
        dirnames.append('/')
        if not os.path.exists(find_result["path"]): os.makedirs(find_result["path"])

        dirnames = []
        if os.path.exists(find_result["path"]):
            dirnames = ['/' + entry.name for entry in os.scandir(find_result["path"]) if entry.is_dir() and not entry.is_symlink() and entry.name != '.well-known' and entry.name != "proxy_cache_dir"]
        p_data['dirs'] = ['/'] + dirnames

        data['runPath'] = p_data

        return public.returnResult(True, data=data)

    # 2024/11/18 10:43 设置防跨站
    def SetDirUserINI(self, get):
        '''
            @name 设置防跨站
        '''
        get.id = get.get("id", None)
        if not get.id:
            return public.returnResult(status=False, msg="id不能为空！")

        get.status = get.get("status", 0)
        find_result = dp.sql("docker_sites").where("id=?", get.id).find()
        if not find_result:
            return public.returnResult(status=False, msg="未找到此ID【{}】的站点信息！".format(get.id))

        user_ini_file = os.path.join(find_result["path"], ".user.ini")
        conf = public.readFile(user_ini_file)
        if os.path.exists(user_ini_file): public.ExecShell("chattr -i " + user_ini_file)

        if int(get.status) == 0:
            if conf and "open_basedir" in conf:
                rep = "\n*open_basedir.*"
                conf = re.sub(rep, "", conf)
                if not conf:
                    os.remove(user_ini_file)
                else:
                    public.writeFile(user_ini_file, conf)
                    if os.path.exists(user_ini_file): public.ExecShell("chattr +i " + user_ini_file)
        else:
            if conf and "session.save_path" in conf:
                rep = "session.save_path\s*=\s*(.*)"
                s_path = re.search(rep, conf).groups(1)[0]
                public.writeFile(user_ini_file, conf + '\nopen_basedir={}/:/tmp/:{}'.format(find_result["path"], s_path))
            else:
                public.writeFile(user_ini_file, 'open_basedir={}/:/tmp/'.format(find_result["path"]))

            if os.path.exists(user_ini_file): public.ExecShell("chattr +i " + user_ini_file)

        return public.returnResult(msg="设置成功！")

    # 2024/11/18 16:32 刷新nginx_conf
    def reload_nginx_conf(self, get):
        '''
            @name 刷新nginx_conf
        '''
        get.siteName = get.get("siteName", None)

        if get.siteName is None:
            site_names = dp.sql("docker_sites").field("name").select()

            reload_result = []
            for site_name in site_names:
                get.site_name = site_name["name"]
                get.proxy_json_conf = self.read_json_conf(get)
                if not get.proxy_json_conf:
                    reload_result.append(
                        {"site_name": get.site_name, "status": False, "msg": "读取配置文件失败，请删除网站重新添加！"})
                    continue

                update_result = self.update_nginx_conf(get)
                if not update_result["status"]:
                    reload_result.append({"site_name": get.site_name, "status": False, "msg": update_result["msg"]})
        else:
            get.site_name = get.siteName
            get.proxy_json_conf = self.read_json_conf(get)
            if not get.proxy_json_conf:
                return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

            update_result = self.update_nginx_conf(get)
            if not update_result["status"]:
                return public.returnResult(status=False, msg=update_result["msg"])

        public.serviceReload()
        return public.returnResult(msg="设置网站目录成功")

    # 2024/11/20 10:56 获取指定网站的PHP信息
    def get_php_project_info(self, get):
        '''
            @name 获取指定网站的PHP信息
        '''
        get.id = get.get("id", None)
        if not get.id:
            return public.returnResult(status=False, msg="id不能为空！")

        find_result = dp.sql("docker_sites").where("id=?", get.id).find()
        if not find_result:
            return public.returnResult(status=False, msg="未找到此ID【{}】的站点信息！".format(get.id))

        try:
            service_info = json.loads(find_result["service_info"])
        except:
            return public.returnResult(status=False, msg="ID【{}】站点的service_info读取失败，请重新添加网站再试！".format(get.id))

        php_name = service_info["name"].split(":")[0]
        php_version = service_info["name"].split(":")[1]
        php_project_info = {
            "used": {"name": php_name, "version": php_version},
        }

        # 2024/11/20 11:00 获取php运行环境列表
        from mod.project.docker.runtime.runtimeManage import RuntimeManage
        runtimeManage = RuntimeManage()
        get.runtime_type = "php"
        get.row = 20000
        php_runtime_list = runtimeManage.get_runtime_list(get)
        if not php_runtime_list["status"]: return php_runtime_list

        runtime_list = php_runtime_list["data"]
        runtime_names = []
        for runtime in runtime_list:
            if runtime["status"] != "normal": continue
            runtime_names.append({"name": runtime["name"], "version": runtime["version"]})

        php_project_info["runtime_list"] = runtime_names

        return public.returnResult(True, data=php_project_info)

    # 2024/11/20 11:10 切换指定网站的PHP版本
    def switch_php_version(self, get):
        '''
            @name 切换指定网站的PHP版本
        '''
        get.id = get.get("id", None)
        if not get.id:
            return public.returnResult(status=False, msg="id不能为空！")

        get.runtime_name = get.get("runtime_name", None)
        if not get.runtime_name:
            return public.returnResult(status=False, msg="runtime_name不能为空！")

        find_result = dp.sql("docker_sites").where("id=?", get.id).find()
        if not find_result:
            return public.returnResult(status=False, msg="未找到此ID【{}】的站点信息！".format(get.id))

        try:
            service_info = json.loads(find_result["service_info"])
        except:
            return public.returnResult(status=False, msg="ID【{}】站点的service_info读取失败，请重新添加网站再试！".format(get.id))

        service_info["name"] = get.runtime_name

        dp.sql("docker_sites").where("id=?", get.id).update({"service_info": json.dumps(service_info)})

        # 2024/11/20 11:14 替换项目env里面的IMAGE_NAME，
        public.ExecShell("sed -i 's/^IMAGE_NAME=.*/IMAGE_NAME={}/' {}/.env".format(get.runtime_name, service_info["project_path"]))
        public.ExecShell("docker-compose -f {}/docker-compose.yml down".format(service_info["project_path"]))
        public.ExecShell("docker-compose -f {}/docker-compose.yml up -d".format(service_info["project_path"]))

        public.serviceReload()

        return public.returnResult(msg="设置成功！")

    # 2024/11/22 12:02 获取指定网站的所有域名
    def GetSiteDomains(self, get):
        '''
            @name 获取指定网站的所有域名
        '''
        get.id = get.get("id", None)
        if not get.id:
            return public.returnResult(status=False, msg="id不能为空！")

        data = {}
        n_list = []
        from sslModel import dataModel
        get.docker_site_id = get.id
        dns_data = dataModel.main().get_domain_dns_config(get)
        for domain in dns_data:
            tmp = {'id': domain['domain_id'], 'name': domain['name'], 'binding': False, 'apply_ssl': 1, 'dns_status': domain['status'], 'root_domain_id': domain['domain_id']}
            if public.checkIp(domain['name']): tmp['apply_ssl'] = 0
            n_list.append(tmp)

        data['domains'] = n_list

        return data

    def get_domian_dns_dic(self):
        try:
            from sslModel import dataModel
            data = dataModel.main().get_domain_dns_config(public.dict_obj())
            return {i["name"]: {"dns_status": i["status"], "root_domain_id": i["domain_id"]} for i in data}
        except:
            return {}

    # 2024/11/26 09:17 部署指定let's encrypt证书
    def set_cert_to_site(self, get):
        '''
            @name
        '''
        from mod.project.docker.sites.sslManage import Acme_V2
        acme = Acme_V2()
        exclude_data = acme.get_exclude_hash(get)
        ssl_hash = exclude_data['exclude_hash_let'].get(get.index)
        if not ssl_hash:
            return public.returnResult(False, "未找到此证书")
        get.ssl_hash = ssl_hash

        from mod.project.docker.sites.sslManage import SslManage
        ssl_manage = SslManage()
        return ssl_manage.SetCertToSite(get)

    # 2024/11/28 16:50 设置proxy_buffering状态
    def set_proxy_buffering(self, get):
        '''
            @name 设置proxy_buffering状态
        '''
        get.site_name = get.get("site_name", None)
        if not get.site_name:
            return public.returnResult(status=False, msg="site_name不能为空！")

        get.status = get.get("status", 0)
        get.proxy_path = get.get("proxy_path", None)
        if not get.proxy_path:
            return public.returnResult(status=False, msg="proxy_path不能为空！")

        get.proxy_json_conf = self.read_json_conf(get)
        if not get.proxy_json_conf:
            return public.returnResult(status=False, msg="读取配置文件失败，请删除网站重新添加！")

        for proxy_info in get.proxy_json_conf["proxy_info"]:
            if not "proxy_pass" in proxy_info: continue
            if not proxy_info["proxy_pass"]: continue

            if get.proxy_path == proxy_info["proxy_path"]:
                print(get.proxy_path)
                print(proxy_info["proxy_path"])
                if int(get.status) == 1:
                    proxy_info["proxy_buffering"] = True
                else:
                    proxy_info["proxy_buffering"] = False
                break

        update_result = self.update_nginx_conf(get)
        if not update_result["status"]:
            return public.returnResult(status=False, msg=update_result["msg"])
        public.serviceReload()

        return public.returnResult(msg="设置成功！")
