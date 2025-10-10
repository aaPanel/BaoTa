# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------
#
# ------------------------------

import json
import sys
import os

import panelSite
import public
from datalistModel.base import dataBase

if '/www/server/panel' not in sys.path:
    sys.path.insert(0, '/www/server/panel')


class main(dataBase):
    site_obj = None

    def __init__(self):
        self.site_obj = panelSite.panelSite()

    # 2024/12/19 15:48 处理通用参数
    def check_parm(self, get):
        '''
            @name 处理通用参数
        '''
        get.site_list = get.get("site_list", [])
        if type(get.site_list) == str:
            try:
                get.site_list = json.loads(get.site_list)
            except:
                pass

        get.all = get.get("all/d", 0)
        if get.all != 0:
            public.set_module_logs('全选设置网站', 'check_parm', 1)

        get.exclude_ids = get.get("exclude_ids", [])
        if type(get.exclude_ids) == str:
            try:
                get.exclude_ids = json.loads(get.exclude_ids)
            except:
                pass

        get.project_type = get.get("project_type", None)
        if get.project_type is None:
            return public.returnResult(False, '请选择项目类型: [PHP,Node,proxy,WP2,Java,html,Go,net,Other]')

        return public.returnResult(True, '检查完成!')

    # 2024/12/19 14:16 批量删除网站
    def batch_delete_sites(self, get):
        '''
            @name 批量删除网站
        '''
        check_parm = self.check_parm(get)
        if not check_parm["status"]: return check_parm
        get.ftp = get.get("database/d", 0)
        get.database = get.get("database/d", 0)
        get.path = get.get("path/d", 0)

        error_list = []
        success_list = []
        # 2024/12/19 15:07 如果不是全选所有数据的删除模式，就按照get.site_list的数据进行删除
        if get.all == 0:
            for site in get.site_list:
                if "id" not in site:
                    error_list.append({"id": None, "name": site["name"], "status": False, "msg": "ID传参错误，请检查网站传参是否正确!"})
                    continue
                if "name" not in site:
                    error_list.append({"id": site["id"], "name": None, "status": False, "msg": "name传参错误，请检查网站传参是否正确!"})
                    continue

                get.id = site["id"]
                get.webname = site["name"]
                result = self.site_obj.DeleteSite(get, multiple=1)
                if not result["status"]:
                    error_list.append({"id": site["id"], "name": site["name"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"id": site["id"], "name": site["name"], "status": True, "msg": "删除成功!"})
        else:
            all_sites_info = public.M('sites').where("project_type=?", (get.project_type,)).field('id,name,project_type').select()
            for site in all_sites_info:
                if not site: continue
                if get.project_type != site["project_type"]: continue
                if site["id"] in get.exclude_ids: continue

                get.id = site["id"]
                get.webname = site["name"]
                result = self.site_obj.DeleteSite(get, multiple=1)
                if not result["status"]:
                    error_list.append({"id": site["id"], "name": site["name"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"id": site["id"], "name": site["name"], "status": True, "msg": "删除成功!"})

        public.serviceReload()
        return public.returnResult(True, '操作成功!', {"error": error_list, "success": success_list})

    # 2024/12/19 15:34 批量设置网站状态
    def batch_set_site_status(self, get):
        '''
            @name 批量设置网站状态
        '''
        check_parm = self.check_parm(get)
        if not check_parm["status"]: return check_parm

        get.option = get.get("option/d", 0)

        error_list = []
        success_list = []
        if get.all == 0:
            for site in get.site_list:
                if "id" not in site:
                    error_list.append({"id": None, "name": site["name"], "status": False, "msg": "ID传参错误，请检查网站传参是否正确!"})
                    continue
                if "name" not in site:
                    error_list.append({"id": site["id"], "name": None, "status": False, "msg": "name传参错误，请检查网站传参是否正确!"})
                    continue

                get.id = site["id"]
                get.name = site["name"]
                if int(site["phpsync"]) == 1:
                    get.sitename = site["name"]
                    if get.option == 0:
                        get.project_action = "stop"
                    elif get.option == 1:
                        get.project_action = "start"
                    else:
                        get.project_action = "restart"
                    self.batch_set_phpsync_status(get, error_list, success_list)
                    continue

                if get.option == 0:
                    result = self.site_obj.SiteStop(get)
                else:
                    result = self.site_obj.SiteStart(get)

                if not result["status"]:
                    error_list.append({"id": site["id"], "name": site["name"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"id": site["id"], "name": site["name"], "status": True, "msg": "设置成功!"})
        else:
            all_sites_info = public.M('sites').where("project_type=?", (get.project_type,)).field('id,name,project_type').select()
            for site in all_sites_info:
                if not site: continue
                if get.project_type != site["project_type"]: continue
                if site["id"] in get.exclude_ids: continue

                get.id = site["id"]
                get.name = site["name"]

                project_config = {}
                if "project_config" in site:
                    try:
                        project_config = json.loads(site["project_config"])
                    except:
                        error_list.append({"id": site["id"], "name": site["name"], "status": False, "msg": "项目配置文件解析失败!"})
                        continue

                if "type" in project_config and project_config["type"] == "PHPMOD":
                    get.sitename = site["name"]
                    self.batch_set_phpsync_status(get, error_list, success_list)
                    continue

                if get.option == 0:
                    result = self.site_obj.SiteStop(get)
                else:
                    result = self.site_obj.SiteStart(get)

                if not result["status"]:
                    error_list.append({"id": site["id"], "name": site["name"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"id": site["id"], "name": site["name"], "status": True, "msg": "设置成功!"})

        public.serviceReload()
        return public.returnResult(True, '操作成功!', {"error": error_list, "success": success_list})

    # 2024/12/19 16:02 批量备份站点
    def batch_site_backup(self, get):
        '''
            @name 批量备份站点
        '''
        check_parm = self.check_parm(get)
        if not check_parm["status"]: return check_parm

        error_list = []
        success_list = []
        if get.all == 0:
            for site in get.site_list:
                if "id" not in site:
                    error_list.append({"id": None, "name": site["name"], "status": False, "msg": "ID传参错误，请检查网站传参是否正确!"})
                    continue
                if "name" not in site:
                    error_list.append({"id": site["id"], "name": None, "status": False, "msg": "name传参错误，请检查网站传参是否正确!"})
                    continue

                get.id = site["id"]
                result = self.site_obj.ToBackup(get)
                if not result["status"]:
                    error_list.append({"id": site["id"], "name": site["name"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"id": site["id"], "name": site["name"], "status": True, "msg": "备份成功!"})
        else:
            all_sites_info = public.M('sites').where("project_type=?", (get.project_type,)).field('id,name,project_type').select()
            for site in all_sites_info:
                if not site: continue
                if get.project_type != site["project_type"]: continue
                if site["id"] in get.exclude_ids: continue

                get.id = site["id"]
                result = self.site_obj.ToBackup(get)
                if not result["status"]:
                    error_list.append({"id": site["id"], "name": site["name"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"id": site["id"], "name": site["name"], "status": True, "msg": "备份成功!"})

        return public.returnResult(True, '操作成功!', {"error": error_list, "success": success_list})

    # 2024/12/19 16:08 批量设置到期时间
    def batch_set_site_edate(self, get):
        '''
            @name 批量设置到期时间
        '''
        check_parm = self.check_parm(get)
        if not check_parm["status"]: return check_parm

        get.edate = get.get("edate", "0000-00-00")

        error_list = []
        success_list = []
        if get.all == 0:
            for site in get.site_list:
                if "id" not in site:
                    error_list.append({"id": None, "name": site["name"], "status": False, "msg": "ID传参错误，请检查网站传参是否正确!"})
                    continue
                if "name" not in site:
                    error_list.append({"id": site["id"], "name": None, "status": False, "msg": "name传参错误，请检查网站传参是否正确!"})
                    continue

                get.id = site["id"]
                result = self.site_obj.SetEdate(get)
                if not result["status"]:
                    error_list.append({"id": site["id"], "name": site["name"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"id": site["id"], "name": site["name"], "status": True, "msg": "设置成功!"})
        else:
            all_sites_info = public.M('sites').where("project_type=?", (get.project_type,)).field('id,name,project_type').select()
            for site in all_sites_info:
                if not site: continue
                if get.project_type != site["project_type"]: continue
                if site["id"] in get.exclude_ids: continue

                get.id = site["id"]
                result = self.site_obj.SetEdate(get)
                if not result["status"]:
                    error_list.append({"id": site["id"], "name": site["name"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"id": site["id"], "name": site["name"], "status": True, "msg": "设置成功!"})

        return public.returnResult(True, '操作成功!', {"error": error_list, "success": success_list})

    # 2024/12/19 16:11 批量设置php版本
    def batch_set_php_version(self, get):
        '''
            @name 批量设置php版本
        '''
        check_parm = self.check_parm(get)
        if not check_parm["status"]: return check_parm

        get.version = get.get("version", "00")

        error_list = []
        success_list = []
        if get.all == 0:
            for site in get.site_list:
                if "id" not in site:
                    error_list.append({"id": None, "name": site["name"], "status": False, "msg": "ID传参错误，请检查网站传参是否正确!"})
                    continue
                if "name" not in site:
                    error_list.append({"id": site["id"], "name": None, "status": False, "msg": "name传参错误，请检查网站传参是否正确!"})
                    continue

                get.sites_id = site["id"]
                get.siteName = site["name"]
                result = self.site_obj.SetPHPVersion(get, multiple=1)
                if not result["status"]:
                    error_list.append({"id": site["id"], "name": site["name"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"id": site["id"], "name": site["name"], "status": True, "msg": "设置成功!"})
        else:
            all_sites_info = public.M('sites').where("project_type=?", (get.project_type,)).field('id,name,project_type').select()
            for site in all_sites_info:
                if not site: continue
                if get.project_type != site["project_type"]: continue
                if site["id"] in get.exclude_ids: continue

                get.sites_id = site["id"]
                get.siteName = site["name"]
                result = self.site_obj.SetPHPVersion(get, multiple=1)
                if not result["status"]:
                    error_list.append({"id": site["id"], "name": site["name"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"id": site["id"], "name": site["name"], "status": True, "msg": "设置成功!"})

        public.serviceReload()
        return public.returnResult(True, '操作成功!', {"error": error_list, "success": success_list})

    # 2024/12/19 16:18 批量设置防跨站
    def batch_set_site_basedir(self, get):
        '''
            @name
        '''
        check_parm = self.check_parm(get)
        if not check_parm["status"]: return check_parm

        get.stat = get.get("stat", "open")

        error_list = []
        get.site_ids = []
        if get.all == 0:
            for site in get.site_list:
                if "id" not in site:
                    error_list.append({"id": None, "name": site["name"], "status": False, "msg": "ID传参错误，请检查网站传参是否正确!"})
                    continue
                if "name" not in site:
                    error_list.append({"id": site["id"], "name": None, "status": False, "msg": "name传参错误，请检查网站传参是否正确!"})
                    continue

                get.site_ids.append(site["id"])
        else:
            all_sites_info = public.M('sites').where("project_type=?", (get.project_type,)).field('id,name,project_type').select()
            for site in all_sites_info:
                if not site: continue
                if get.project_type != site["project_type"]: continue
                if site["id"] in get.exclude_ids: continue

                get.site_ids.append(site["id"])

        sites_info = public.M("sites").where(
            "project_type=? AND id IN ({})".format(','.join(["?"]*len(get.site_ids))), ("PHP", *get.site_ids)
        ).field("id,name,path").select()

        res = {
            "error": error_list,
            "success": [],
        }
        stat = get.stat
        for site in sites_info:
            get_obj = public.dict_obj()
            get_obj.path = site["path"]
            get_obj.id = site["id"]
            run_path = self.site_obj.GetRunPath(get_obj)
            if not run_path:
                res["errors"].append(public.returnMsg(False, "运行目录获取失败"))
            filename = (site["path"] + run_path + '/.user.ini').replace("//", "/")
            if stat == "close":  # 关闭
                if os.path.exists(filename):
                    new_get = public.dict_obj()
                    new_get.path = site["path"]
                    tmp = self.site_obj.SetDirUserINI(new_get)
                    tmp["id"] = site["id"]
                    tmp["name"] = site["name"]
                    if tmp["status"] is False:
                        res["error"].append(tmp)
                    else:
                        res["success"].append(tmp)
                else:
                    res["success"].append({"id": site["id"], "name":site["name"], "status": True, "msg": "防跨站文件不存在，跳过关闭"})
            else:
                if not os.path.exists(filename):
                    new_get = public.dict_obj()
                    new_get.path = site["path"]
                    tmp = self.site_obj.SetDirUserINI(new_get)
                    tmp["id"] = site["id"]
                    tmp["name"] = site["name"]
                    if tmp["status"] is False:
                        res["error"].append(tmp)
                    else:
                        res["success"].append(tmp)
                else:
                    res["success"].append({"id": site["id"], "name":site["name"], "status": True, "msg": "防跨站文件已存在，跳过开启"})
        return public.returnResult(True, '操作成功!', res)

    # 2024/12/19 16:48 批量设置防盗链
    def batch_site_referer(self, get):
        '''
            @name 批量设置防盗链
        '''
        check_parm = self.check_parm(get)
        if not check_parm["status"]: return check_parm

        get.fix = get.get("fix", "jpg,jpeg,gif,png,js,css")
        get.domains = get.get("domains", None)
        if get.domains is None:
            return public.returnResult(False, '请输入域名!')
        get.return_rule = get.get("return_rule", "404")
        get.http_status = get.get("http_status", True)
        get.status = get.get("status", True)

        error_list = []
        get.site_ids = []
        if get.all == 0:
            for site in get.site_list:
                if "id" not in site:
                    error_list.append({"id": None, "name": site["name"], "status": False, "msg": "ID传参错误，请检查网站传参是否正确!"})
                    continue
                if "name" not in site:
                    error_list.append({"id": site["id"], "name": None, "status": False, "msg": "name传参错误，请检查网站传参是否正确!"})
                    continue

                get.site_ids.append(site["id"])
        else:
            all_sites_info = public.M('sites').where("project_type=?", (get.project_type,)).field('id,name,project_type').select()
            for site in all_sites_info:
                if not site: continue
                if get.project_type != site["project_type"]: continue
                if site["id"] in get.exclude_ids: continue

                get.site_ids.append(site["id"])

        fix = get.fix
        domains = get.domains
        status = get.status
        return_rule = get.return_rule
        http_status = get.http_status

        sites_info = public.M("sites").where(
            "project_type=? AND id IN ({})".format(','.join(["?"]*len(get.site_ids))), ("PHP", *get.site_ids)
        ).field("id,name").select()

        if len(domains) < 3:
            domains = ""

        sites_domains = {s["id"]: domains for s in sites_info}
        domains_info = public.M("domain").where(
            "pid IN ({})".format(','.join(["?"]*len(sites_domains))), list(sites_domains.keys())
        ).field("pid,name").select()

        for domain in domains_info:
            sites_domains[domain["pid"]] += ',' + domain["name"]

        res = {
            "error": error_list,
            "success": [],
        }
        for site in sites_info:
            get_obj = public.dict_obj()
            get_obj.id = site["id"]
            get_obj.name = site["name"]
            get_obj.fix = fix
            get_obj.domains = sites_domains[site["id"]].strip(",")
            get_obj.status = status
            get_obj.return_rule = return_rule
            get_obj.http_status = http_status
            tmp = self.site_obj.SetSecurity(get_obj)
            tmp["id"] = site["id"]
            tmp["name"] = site["name"]
            if tmp["status"] is False:
                res["error"].append(tmp)
            else:
                res["success"].append(tmp)

        return public.returnResult(True, '操作成功!', res)

    # 2024/12/19 17:02 批量设置流量限制
    def batch_site_limit_net(self, get):
        '''
            @name 批量设置流量限制
        '''
        check_parm = self.check_parm(get)
        if not check_parm["status"]: return check_parm
        get.value = get.get("value", False)
        get.perserver = get.get("perserver", 300)
        get.perip = get.get("perip", 25)
        get.limit_rate = get.get("limit_rate", 512)
        get.type = get.get("type", 0)
        get.close_limit_net = get.get("close_limit_net", 0)

        error_list = []
        get.site_ids = []
        if get.all == 0:
            for site in get.site_list:
                if "id" not in site:
                    error_list.append({"id": None, "name": site["name"], "status": False, "msg": "ID传参错误，请检查网站传参是否正确!"})
                    continue
                if "name" not in site:
                    error_list.append({"id": site["id"], "name": None, "status": False, "msg": "name传参错误，请检查网站传参是否正确!"})
                    continue

                get.site_ids.append(site["id"])
        else:
            all_sites_info = public.M('sites').where("project_type=?", (get.project_type,)).field('id,name,project_type').select()
            for site in all_sites_info:
                if not site: continue
                if get.project_type != site["project_type"]: continue
                if site["id"] in get.exclude_ids: continue

                get.site_ids.append(site["id"])

        perserver = get.perserver
        perip = get.perip
        limit_rate = get.limit_rate
        close_limit_net = get.close_limit_net

        sites_info = public.M("sites").where(
            "project_type=? AND id IN ({})".format(','.join(["?"]*len(get.site_ids))), ("PHP", *get.site_ids)
        ).field("id,name,path").select()

        res = {
            "error": [],
            "success": [],
        }
        if close_limit_net in ("true", "1", 1, True):
            for site in sites_info:
                get_obj = public.dict_obj()
                get_obj.id = site["id"]
                tmp = self.site_obj.CloseLimitNet(get_obj)
                tmp["id"] = site["id"]
                tmp["name"] = site["name"]
                if tmp["status"] is False:
                    res["error"].append(tmp)
                else:
                    res["success"].append(tmp)
            return res

        for site in sites_info:
            get_obj = public.dict_obj()
            get_obj.id = site["id"]
            get_obj.perserver = perserver
            get_obj.perip = perip
            get_obj.limit_rate = limit_rate
            tmp = self.site_obj.SetLimitNet(get_obj)
            tmp["id"] = site["id"]
            tmp["name"] = site["name"]
            if tmp["status"] is False:
                res["error"].append(tmp)
            else:
                res["success"].append(tmp)

        return public.returnResult(True, '操作成功!', res)

    # 2024/12/19 17:14 批量设置伪静态
    def batch_set_site_rewrite(self, get):
        '''
            @name 批量设置伪静态
        '''
        check_parm = self.check_parm(get)
        if not check_parm["status"]: return check_parm

        get.rewrite_data = get.get("rewrite_data", "")

        if get.all == 0:
            get.sites = json.dumps(get.site_list)
            result = self.site_obj.SetRewriteLists(get)
        else:
            all_sites_info = public.M('sites').where("project_type=?", (get.project_type,)).field('id,name,project_type').select()
            get.sites = []
            for site in all_sites_info:
                if not site: continue
                if get.project_type != site["project_type"]: continue
                if site["id"] in get.exclude_ids: continue

                get.sites.append({"id": site["id"], "name": site["name"], "file":"/www/server/panel/vhost/rewrite/{}.conf".format(site["name"])})
            get.sites = json.dumps(get.sites)
            result = self.site_obj.SetRewriteLists(get)

        res = {
            "error": [],
            "success": [],
        }
        if "status" in result and not result["status"]: return result

        for site in result:
            if site["status"] is False:
                res["error"].append({"id": site["id"], "name": site["name"], "status": False, "msg": site["msg"], "file": site["file"]})
            else:
                res["success"].append({"id": site["id"], "name": site["name"], "status": True, "msg": "设置成功!", "file": site["file"]})

        return public.returnResult(True, '操作成功!', res)

    # 2024/12/19 17:45 批量设置网站分类
    def batch_set_site_type(self, get):
        '''
            @name 批量设置网站分类
        '''
        check_parm = self.check_parm(get)
        if not check_parm["status"]: return check_parm

        get.id = get.get("id", 0)

        get.site_ids = []
        if get.all == 0:
            for site in get.site_list:
                if "id" not in site: continue
                if "name" not in site: continue

                get.site_ids.append(site["id"])
        else:
            all_sites_info = public.M('sites').where("project_type=?", (get.project_type,)).field('id,name,project_type').select()
            for site in all_sites_info:
                if not site: continue
                if get.project_type != site["project_type"]: continue
                if site["id"] in get.exclude_ids: continue

                get.site_ids.append(site["id"])

        get.site_ids = json.dumps(get.site_ids)
        self.site_obj.set_site_type(get)
        return public.returnResult(True, '设置成功!')

    # 2024/12/19 17:51 批量获取网站域名
    def batch_get_site_domains(self, get):
        '''
            @name 批量获取网站域名
        '''
        check_parm = self.check_parm(get)
        if not check_parm["status"]: return check_parm

        get.pids = []
        if get.all == 0:
            for site in get.site_list:
                if "id" not in site: continue
                if "name" not in site: continue

                get.pids.append(site["id"])
        else:
            all_sites_info = public.M('sites').where("project_type=?", (get.project_type,)).field('id,name,project_type').select()
            for site in all_sites_info:
                if not site: continue
                if get.project_type != site["project_type"]: continue
                if site["id"] in get.exclude_ids: continue

                get.pids.append(site["id"])

        get.pids = json.dumps(get.pids)
        result = self.site_obj.get_domains(get)
        return public.returnResult(True, '获取成功!', result)

    # 2024/12/19 17:58 批量设置nodejs项目状态
    def batch_set_nodejs_project_status(self, get):
        '''
            @name 批量设置nodejs项目状态
        '''
        check_parm = self.check_parm(get)
        if not check_parm["status"]: return check_parm

        get.status = get.get("status", "start")
        error_list = []
        success_list = []
        if get.all == 0:
            for site in get.site_list:
                if "project_name" not in site:
                    error_list.append({"project_name": None, "project_type": site["project_type"], "status": False, "msg": "ID传参错误，请检查网站传参是否正确!"})
                    continue
                if "project_type" not in site:
                    error_list.append({"project_name": site["project_name"], "project_type": None, "status": False, "msg": "name传参错误，请检查网站传参是否正确!"})
                    continue

                get.project_name = site["project_name"]
                get.project_type = site["project_type"]
                get.pm2_name = site["pm2_name"] if "pm2_name" in site else None

                from mod.project.nodejs.comMod import main as comMod
                nodejs_obj = comMod()
                result = nodejs_obj.set_project_status(get)
                if not result["status"]:
                    error_list.append({"project_name": site["project_name"], "project_type": site["project_type"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"project_name": site["project_name"], "project_type": site["project_type"], "status": True, "msg": "设置成功!"})
        else:
            all_sites_info = public.M('sites').where("project_type=?", (get.project_type,)).select()
            for site in all_sites_info:
                if not site: continue
                if get.project_type != site["project_type"]: continue
                if site["id"] in get.exclude_ids: continue
                if not "project_config" in site: continue
                project_config = json.loads(site["project_config"])

                get.project_name = site["name"]
                get.project_type = project_config["project_type"] if "project_type" in project_config else "nodejs"
                get.pm2_name = site["name"]

                from mod.project.nodejs.comMod import main as comMod
                nodejs_obj = comMod()
                result = nodejs_obj.set_project_status(get)
                if not result["status"]:
                    error_list.append({"project_name": site["name"], "project_type": site["project_type"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"project_name": site["name"], "project_type": site["project_type"], "status": True, "msg": "设置成功!"})

        return public.returnResult(True, '操作成功!', {"error": error_list, "success": success_list})

    # 2024/12/19 18:31 批量设置java项目状态
    def batch_set_java_project_status(self, get):
        '''
            @name 批量设置java项目状态
        '''
        check_parm = self.check_parm(get)
        if not check_parm["status"]: return check_parm

        error_list = []
        success_list = []
        get.status = get.get("status", "start")
        if get.all == 0:
            for site in get.site_list:
                if "project_name" not in site:
                    error_list.append({"project_name": None, "status": False, "msg": "ID传参错误，请检查网站传参是否正确!"})
                    continue

                get.project_name = site["project_name"]

                from mod.project.java.projectMod import main as comMod
                java_obj = comMod()
                if get.status == "start":
                    result = java_obj.start_project(get)
                elif get.status == "stop":
                    result = java_obj.stop_project(get)
                else:
                    result = java_obj.restart_project(get)

                if not result["status"]:
                    error_list.append({"project_name": site["project_name"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"project_name": site["project_name"], "status": True, "msg": "设置成功!"})
        else:
            all_sites_info = public.M('sites').where("project_type=?", (get.project_type,)).select()
            for site in all_sites_info:
                if not site: continue
                if get.project_type != site["project_type"]: continue
                if site["id"] in get.exclude_ids: continue
                if not "project_config" in site: continue

                get.project_name = site["name"]

                from mod.project.java.projectMod import main as comMod
                java_obj = comMod()
                if get.status == "start":
                    result = java_obj.start_project(get)
                elif get.status == "stop":
                    result = java_obj.stop_project(get)
                else:
                    result = java_obj.restart_project(get)

                if not result["status"]:
                    error_list.append({"project_name": site["name"], "project_type": site["project_type"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"project_name": site["name"], "project_type": site["project_type"], "status": True, "msg": "设置成功!"})

        return public.returnResult(True, '操作成功!', {"error": error_list, "success": success_list})

    # 2024/12/20 14:15 批量设置go项目状态
    def batch_set_go_project_status(self, get):
        '''
            @name 批量设置go项目状态
        '''
        check_parm = self.check_parm(get)
        if not check_parm["status"]: return check_parm

        error_list = []
        success_list = []
        get.status = get.get("status", "start")
        if get.all == 0:
            for site in get.site_list:
                if "project_name" not in site:
                    error_list.append({"project_name": None, "status": False, "msg": "ID传参错误，请检查网站传参是否正确!"})
                    continue

                get.project_name = site["project_name"]

                from projectModel.goModel import main as comMod
                go_obj = comMod()
                if get.status == "start":
                    result = go_obj.start_project(get)
                elif get.status == "stop":
                    result = go_obj.stop_project(get)
                else:
                    result = go_obj.restart_project(get)

                if not result["status"]:
                    error_list.append({"project_name": site["project_name"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"project_name": site["project_name"], "status": True, "msg": "设置成功!"})
        else:
            all_sites_info = public.M('sites').where("project_type=?", (get.project_type,)).select()
            for site in all_sites_info:
                if not site: continue
                if get.project_type != site["project_type"]: continue
                if site["id"] in get.exclude_ids: continue
                if not "project_config" in site: continue

                get.project_name = site["name"]

                from projectModel.goModel import main as comMod
                go_obj = comMod()
                if get.status == "start":
                    result = go_obj.start_project(get)
                elif get.status == "stop":
                    result = go_obj.stop_project(get)
                else:
                    result = go_obj.restart_project(get)

                if not result["status"]:
                    error_list.append({"project_name": site["name"], "project_type": site["project_type"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"project_name": site["name"], "project_type": site["project_type"], "status": True, "msg": "设置成功!"})

        return public.returnResult(True, '操作成功!', {"error": error_list, "success": success_list})

    # 2024/12/20 14:21 批量设置python项目状态
    def batch_set_python_project_status(self, get):
        '''
            @name 批量设置python项目状态
        '''
        check_parm = self.check_parm(get)
        if not check_parm["status"]: return check_parm

        error_list = []
        success_list = []
        get.status = get.get("status", "start")
        if get.all == 0:
            for site in get.site_list:
                if "project_name" not in site:
                    error_list.append({"project_name": None, "status": False, "msg": "ID传参错误，请检查网站传参是否正确!"})
                    continue

                get.project_name = site["project_name"]

                from projectModel.pythonModel import main as comMod
                python_obj = comMod()
                if get.status == "start":
                    result = python_obj.start_project(get)
                elif get.status == "stop":
                    result = python_obj.stop_project(get)
                else:
                    result = python_obj.restart_project(get)

                if not result["status"]:
                    error_list.append({"project_name": site["project_name"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"project_name": site["project_name"], "status": True, "msg": "设置成功!"})
        else:
            all_sites_info = public.M('sites').where("project_type=?", (get.project_type,)).select()
            for site in all_sites_info:
                if not site: continue
                if get.project_type != site["project_type"]: continue
                if site["id"] in get.exclude_ids: continue
                if not "project_config" in site: continue

                get.project_name = site["name"]

                from projectModel.pythonModel import main as comMod
                python_obj = comMod()
                if get.status == "start":
                    result = python_obj.start_project(get)
                elif get.status == "stop":
                    result = python_obj.stop_project(get)
                else:
                    result = python_obj.restart_project(get)

                if not result["status"]:
                    error_list.append({"project_name": site["name"], "project_type": site["project_type"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"project_name": site["name"], "project_type": site["project_type"], "status": True, "msg": "设置成功!"})

        return public.returnResult(True, '操作成功!', {"error": error_list, "success": success_list})

    # 2024/12/20 10:40 批量设置证书
    def batch_set_site_ssl(self, get):
        '''
            @name 批量设置证书
        '''
        check_parm = self.check_parm(get)
        if not check_parm["status"]: return check_parm
        get.ssl_hash = get.get("ssl_hash", None)
        if get.ssl_hash is None:
            return public.returnResult(False, "请传入证书hash")
        get.certName = get.get("certName", None)
        if get.certName is None:
            return public.returnResult(False, "请传入证书域名")
        
        error_list = []
        success_list = []
        if get.all == 0:
            for btinfo in get.site_list:
                btinfo["ssl_hash"] = get.ssl_hash
                btinfo["certName"] = get.certName
                btinfo["siteName"] = btinfo["name"]
                
            get.BatchInfo = get.site_list
        else:
            get.BatchInfo = []
            all_sites_info = public.M('sites').where("project_type=?", (get.project_type,)).field('id,name,project_type').select()
            for site in all_sites_info:
                if not site: continue
                if get.project_type != site["project_type"]: continue
                if site["id"] in get.exclude_ids: continue

                get.BatchInfo.append({"ssl_hash": get.ssl_hash, "siteName": site["name"], "certName": get.certName})

        get.BatchInfo = json.dumps(get.BatchInfo)

        import panelSSL
        ssl_obj = panelSSL.panelSSL()
        result = ssl_obj.SetBatchCertToSite(get)
        if "status" in result and not result["status"]:
            return public.returnResult(False, result["msg"])

        for r in result["successList"]:
            if r["status"] is False:
                error_list.append({"certName": r["certName"], "siteName": r["siteName"], "status": False, "msg": r["error_msg"]})
            else:
                success_list.append({"certName": r["certName"], "siteName": r["siteName"], "status": True, "msg": "设置成功!"})

        return public.returnResult(True, '操作成功!', {"error": error_list, "success": success_list})

    # 2024/12/23 17:58 批量设置php动态项目状态
    def batch_set_phpsync_status(self, get, error_list, success_list):
        '''
            @name 批量设置php动态项目状态
        '''
        from mod.project.php.php_asyncMod import main as comMod
        php_obj = comMod()

        result = php_obj.modify_project_run_state(get)
        if not result["status"]:
            error_list.append({"id": get.id, "name": get.sitename, "status": False, "msg": result["msg"]})
        else:
            success_list.append({"id": get.id, "name": get.sitename, "status": True, "msg": "设置成功!"})

    # 2024/12/20 10:40 数据库批量区域
    # 2024/12/20 10:40 处理数据库通用参数
    def check_db_parm(self, get):
        '''
            @name 处理数据库通用参数
        '''
        get.database_list = get.get("database_list", [])
        if type(get.database_list) == str:
            try:
                get.database_list = json.loads(get.database_list)
            except:
                pass

        get.all = get.get("all/d", 0)
        if get.all != 0:
            public.set_module_logs('全选设置数据库', 'check_db_parm', 1)

        get.exclude_ids = get.get("exclude_ids", [])
        if type(get.exclude_ids) == str:
            try:
                get.exclude_ids = json.loads(get.exclude_ids)
            except:
                pass

        # get.project_type = get.get("project_type", None)
        # if get.project_type is None:
        #     return public.returnResult(False, '请选择项目类型: [PHP,Node,proxy,WP2,Java,html,Go,net,Other]')

        return public.returnResult(True, '检查完成!')

    # 2024/12/20 10:40 批量删除数据库
    def batch_delete_database(self, get):
        '''
            @name 批量删除数据库
        '''
        check_parm = self.check_db_parm(get)
        if not check_parm["status"]: return check_parm
        
        error_list = []
        success_list = []
        import database
        db_obj = database.database()
        if get.all == 0:
            for db in get.database_list:
                if "id" not in db:
                    error_list.append({"id": None, "name": db["name"], "status": False, "msg": "ID传参错误，请检查数据库传参是否正确!"})
                    continue
                if "name" not in db:
                    error_list.append({"id": db["id"], "name": None, "status": False, "msg": "name传参错误，请检查数据库传参是否正确!"})
                    continue

                get.id = db["id"]
                get.name = db["name"]
                result = db_obj.DeleteDatabase(get)
                if not result["status"]:
                    error_list.append({"id": db["id"], "name": db["name"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"id": db["id"], "name": db["name"], "status": True, "msg": "删除成功!"})
                
        else:
            all_dbs_info = public.M('databases').field('id,name').select()
            for db in all_dbs_info:
                if not db: continue
                if db["id"] in get.exclude_ids: continue

                get.id = db["id"]
                get.name = db["name"]
                result = db_obj.DeleteDatabase(get)
                if not result["status"]:
                    error_list.append({"id": db["id"], "name": db["name"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"id": db["id"], "name": db["name"], "status": True, "msg": "删除成功!"})

        return public.returnResult(True, '操作成功!', {"error": error_list, "success": success_list})

    # 2024/12/20 11:07 批量设置mysql权限
    def batch_set_mysql_access(self, get):
        '''
            @name 批量设置mysql权限
        '''
        check_parm = self.check_db_parm(get)
        if not check_parm["status"]: return check_parm

        get.dataAccess = get.get("dataAccess", "127.0.0.1")
        get.access = get.get("access", "127.0.0.1")
        get.address = get.get("address", "")

        if get.all == 0:
            get.name = []
            for db in get.database_list:
                get.name.append(db["name"])
        else:
            get.name = []
            all_dbs_info = public.M('databases').field('id,name').select()
            for db in all_dbs_info:
                if not db: continue
                if db["id"] in get.exclude_ids: continue

                get.name.append(db["name"])

        get.name = ",".join(get.name)
        import database
        db_obj = database.database()
        return db_obj.SetDatabaseAccess(get)
    
    # 2024/12/20 11:11 批量设置mysql的数据库分类
    def batch_set_mysql_type(self, get):
        '''
            @name 批量设置mysql的数据库分类
        '''
        check_parm = self.check_db_parm(get)
        if not check_parm["status"]: return check_parm

        get.id = get.get("id/d", 0)
        get.db_type = "mysql"

        if get.all == 0:
            get.database_names = []
            for db in get.database_list:
                get.database_names.append(db["name"])
        else:
            get.database_names = []
            all_dbs_info = public.M('databases').field('id,name').select()
            for db in all_dbs_info:
                if not db: continue
                if db["id"] in get.exclude_ids: continue

                get.database_names.append(db["name"])

        get.database_names = ",".join(get.database_names)
        import database
        db_obj = database.database()
        return db_obj.set_database_type_by_name(get)

    # 2024/12/20 11:20 批量同步数据库到服务器
    def batch_sync_db_to_server(self, get):
        '''
            @name 批量同步数据库到服务器
        '''
        check_parm = self.check_db_parm(get)
        if not check_parm["status"]: return check_parm

        get.type = 1

        if get.all == 0:
            get.ids = []
            for db in get.database_list:
                get.ids.append(db["id"])
        else:
            get.ids = []
            all_dbs_info = public.M('databases').field('id,name').select()
            for db in all_dbs_info:
                if not db: continue
                if db["id"] in get.exclude_ids: continue

                get.ids.append(db["id"])

        get.ids = json.dumps(get.ids)
        import database
        db_obj = database.database()
        return db_obj.SyncToDatabases(get)

    # 2024/12/20 11:28 批量备份mysql数据库
    def batch_backup_mysql(self, get):
        '''
            @name 批量备份mysql数据库
        '''
        check_parm = self.check_db_parm(get)
        if not check_parm["status"]: return check_parm

        import database
        db_obj = database.database()
        error_list = []
        success_list = []
        if get.all == 0:
            for db in get.database_list:
                get.id = db["id"]
                result = db_obj.ToBackup(get)
                if not result["status"]:
                    error_list.append({"id": db["id"], "name": db["name"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"id": db["id"], "name": db["name"], "status": True, "msg": "备份成功!"})
        else:
            all_dbs_info = public.M('databases').field('id,name').select()
            for db in all_dbs_info:
                if not db: continue
                if db["id"] in get.exclude_ids: continue

                get.id = db["id"]
                result = db_obj.ToBackup(get)
                if not result["status"]:
                    error_list.append({"id": db["id"], "name": db["name"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"id": db["id"], "name": db["name"], "status": True, "msg": "备份成功!"})

        return public.returnResult(True, '操作成功!', {"error": error_list, "success": success_list})

    # 2024/12/20 11:32 批量删除redis数据库
    def batch_delete_redis(self, get):
        '''
            @name 批量删除redis数据库
        '''
        check_parm = self.check_db_parm(get)
        if not check_parm["status"]: return check_parm
        get.db_idx = get.get("db_idx", None)
        get.sid = get.get("sid", None)
        if get.sid is None:
            return public.returnResult(False, "请传入数据库sid")

        error_list = []
        success_list = []
        from databaseModel.redisModel import main
        redis_obj = main()
        if get.all == 0:
            for db in get.database_list:
                get.key = db["key"]
                result = redis_obj.del_redis_val(get)
                if not result["status"]:
                    error_list.append({"id": get.sid, "name": db["key"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"id": get.sid, "name": db["key"], "status": True, "msg": "删除成功!"})
        else:
            db_keylist = redis_obj.get_db_keylist(get)["data"]
            if not db_keylist:
                return public.returnResult(False, "获取数据库列表失败")

            for db in db_keylist:
                if not db: continue
                if db["name"] in get.exclude_ids: continue

                get.key = db["name"]
                result = redis_obj.del_redis_val(get)
                if not result["status"]:
                    error_list.append({"id": db["name"], "name": db["name"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"id": db["name"], "name": db["name"], "status": True, "msg": "删除成功!"})

        return public.returnResult(True, '操作成功!', {"error": error_list, "success": success_list})

    # 2024/12/20 11:48 批量删除指定sqlite
    def batch_delete_sqlite(self, get):
        '''
            @name 批量删除指定sqlite
        '''
        check_parm = self.check_db_parm(get)
        if not check_parm["status"]: return check_parm

        from databaseModel.sqliteModel import main
        sqlite_obj = main()
        error_list = []
        success_list = []
        if get.all == 0:
            for db in get.database_list:
                get.path = db["path"]
                result = sqlite_obj.DeleteDatabase(get)
                if not result["status"]:
                    error_list.append({"id": db["name"], "name": db["path"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"id": db["name"], "name": db["path"], "status": True, "msg": "删除成功!"})
        else:
            database_list = sqlite_obj.get_list(get)
            for db in database_list:
                if not db: continue
                if db["path"] in get.exclude_ids: continue

                get.path = db["path"]
                result = sqlite_obj.DeleteDatabase(get)
                if not result["status"]:
                    error_list.append({"id": db["name"], "name": db["path"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"id": db["name"], "name": db["path"], "status": True, "msg": "删除成功!"})

        return public.returnResult(True, '操作成功!', {"error": error_list, "success": success_list})

    # 2024/12/20 11:55 批量备份sqlite
    def batch_backup_sqlite(self, get):
        '''
            @name 批量备份sqlite
        '''
        check_parm = self.check_db_parm(get)
        if not check_parm["status"]: return check_parm

        from databaseModel.sqliteModel import main
        sqlite_obj = main()
        error_list = []
        success_list = []
        if get.all == 0:
            for db in get.database_list:
                get.path = db["path"]
                result = sqlite_obj.ToBackup(get)
                if not result["status"]:
                    error_list.append({"id": db["name"], "name": db["path"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"id": db["name"], "name": db["path"], "status": True, "msg": "备份成功!"})
        else:
            database_list = sqlite_obj.get_list(get)
            for db in database_list:
                if not db: continue
                if db["path"] in get.exclude_ids: continue

                get.path = db["path"]
                result = sqlite_obj.ToBackup(get)
                if not result["status"]:
                    error_list.append({"id": db["name"], "name": db["path"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"id": db["name"], "name": db["path"], "status": True, "msg": "备份成功!"})

        return public.returnResult(True, '操作成功!', {"error": error_list, "success": success_list})

    # 2024/12/20 12:00 FTP批量区域
    # 2024/12/20 12:02 FTP通用参数检测
    def check_ftp_parm(self, get):
        '''
            @name FTP通用参数检测
        '''
        get.ftp_list = get.get("ftp_list", [])
        if type(get.ftp_list) == str:
            try:
                get.ftp_list = json.loads(get.ftp_list)
            except:
                pass

        get.all = get.get("all/d", 0)
        if get.all != 0:
            public.set_module_logs('全选设置FTP', 'check_ftp_parm', 1)

        get.exclude_ids = get.get("exclude_ids", [])
        if type(get.exclude_ids) == str:
            try:
                get.exclude_ids = json.loads(get.exclude_ids)
            except:
                pass

        return public.returnResult(True, '检查完成!')

    # 2024/12/20 11:59 批量设置ftp启用状态
    def batch_set_ftp_status(self, get):
        '''
            @name 批量设置ftp启用状态
        '''
        check_parm = self.check_ftp_parm(get)
        if not check_parm["status"]: return check_parm

        get.status = get.get("status/d", None)
        if get.status is None:
            return public.returnResult(False, "请传入状态")

        error_list = []
        success_list = []
        import ftp
        ftp_obj = ftp.ftp()
        if get.all == 0:
            for ftp in get.ftp_list:
                get.id = ftp["id"]
                get.username = ftp["name"]
                result = ftp_obj.SetStatus(get)
                if not result["status"]:
                    error_list.append({"id": ftp["id"], "name": ftp["name"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"id": ftp["id"], "name": ftp["name"], "status": True, "msg": "设置成功!"})
        else:
            all_ftp_info = public.M('ftps').field('id,name').select()
            for ftp in all_ftp_info:
                if not ftp: continue
                if ftp["id"] in get.exclude_ids: continue

                get.id = ftp["id"]
                get.username = ftp["name"]
                result = ftp_obj.SetStatus(get)
                if not result["status"]:
                    error_list.append({"id": ftp["id"], "name": ftp["name"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"id": ftp["id"], "name": ftp["name"], "status": True, "msg": "设置成功!"})

        return public.returnResult(True, '操作成功!', {"error": error_list, "success": success_list})

    # 2024/12/20 12:08 批量设置ftp密码
    def batch_set_ftp_password(self, get):
        '''
            @name 批量设置ftp密码
        '''
        check_parm = self.check_ftp_parm(get)
        if not check_parm["status"]: return check_parm

        if get.all == 0:
            get.data = get.ftp_list
        else:
            all_ftp_info = public.M('ftps').field('id,name').select()
            get.data = []
            for ftp in all_ftp_info:
                import random
                password = ''.join(random.sample('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', 10))
                get.data.append({"id": ftp["id"], "ftp_username": ftp["name"], "new_password": password})

        get.data = json.dumps(get.data)
        import ftp
        ftp_obj = ftp.ftp()
        return ftp_obj.BatchSetUserPassword(get)

    # 2024/12/20 12:14 批量设置ftp分类
    def batch_set_ftp_type(self, get):
        '''
            @name 批量设置ftp分类
        '''
        check_parm = self.check_ftp_parm(get)
        if not check_parm["status"]: return check_parm

        get.id = get.get("id/d", 0)

        if get.all == 0:
            get.ftp_names = []
            for ftp in get.ftp_list:
                get.ftp_names.append(ftp["name"])
        else:
            get.ftp_names = []
            all_ftp_info = public.M('ftps').field('id,name').select()
            for ftp in all_ftp_info:
                if not ftp: continue
                if ftp["id"] in get.exclude_ids: continue

                get.ftp_names.append(ftp["name"])

        get.ftp_names = ",".join(get.ftp_names)
        import ftp
        ftp_obj = ftp.ftp()
        return ftp_obj.set_ftp_type_by_id(get)

    # 2024/12/24 12:11 批量删除FTP账户
    def batch_delete_ftp(self, get):
        '''
            @name 批量删除FTP账户
        '''
        check_parm = self.check_ftp_parm(get)
        if not check_parm["status"]: return check_parm

        error_list = []
        success_list = []
        import ftp
        ftp_obj = ftp.ftp()

        if get.all == 0:
            for f in get.ftp_list:
                get.id = f["id"]
                get.username = f["name"]
                result = ftp_obj.DeleteUser(get)
                if not result["status"]:
                    error_list.append({"id": f["id"], "name": f["name"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"id": f["id"], "name": f["name"], "status": True, "msg": "删除成功!"})
        else:
            all_ftp_info = public.M('ftps').field('id,name').select()
            for ftp in all_ftp_info:
                if not ftp: continue
                if ftp["id"] in get.exclude_ids: continue

                get.id = ftp["id"]
                get.username = ftp["name"]
                result = ftp_obj.DeleteUser(get)
                if not result["status"]:
                    error_list.append({"id": ftp["id"], "name": ftp["name"], "status": False, "msg": result["msg"]})
                else:
                    success_list.append({"id": ftp["id"], "name": ftp["name"], "status": True, "msg": "删除成功!"})

        return public.returnResult(True, '操作成功!', {"error": error_list, "success": success_list})
