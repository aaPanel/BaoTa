# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: cjxin <cjxin@bt.cn>
# -------------------------------------------------------------------

import os
import time
import json
import datetime

import public
from panelModel.base import panelBase


class main(panelBase):
    _PLUGIN_DIR = os.path.join(public.get_panel_path(), "plugin")
    _OVERVIEW_TEMPLATE = os.path.join(public.get_panel_path(), "config/overview_template.json")
    _OVERVIEW_SETTING = os.path.join(public.get_panel_path(), "config/overview_setting.json")
    __db_objs = {}

    def __init__(self):
        overview_setting = []
        if not os.path.isfile(self._OVERVIEW_SETTING):
            temp_data = json.loads(public.readFile(self._OVERVIEW_TEMPLATE))
            id = 0
            for temp in temp_data:
                for option in temp.get("option", []):
                    if option.get("name") in ["sites", "databases", "safety_risk", "memo"]:
                        option["id"] = id
                        option["template"] = temp["template"]
                        option["params"] = [p["option"][0] for p in option.get("params", []) if p.get("option")]
                        id += 1
                        overview_setting.append(option)
            public.writeFile(self._OVERVIEW_SETTING, json.dumps(overview_setting))
        # else:
        #     temp_overview_setting = json.loads(public.readFile(self._OVERVIEW_SETTING))
        #     if temp_overview_setting != overview_setting:
        #         public.writeFile(self._OVERVIEW_SETTING, json.dumps(overview_setting))

    # 获取监控报表默认数据
    def _default_monitor(self):
        sites = public.M("sites").field("name").select()
        site_name = sites[0]["name"]
        try:
            json_data = public.readFile(os.path.join(public.get_setup_path(), "monitor/config/config.json"))
            data_save_path = json_data["data_save_path"]
            if not os.path.exists(data_save_path): return site_name
        except:
            return site_name
        file_max = 0
        for site in sites:
            path = os.path.join(data_save_path, site["name"], "request_total.db")
            if not os.path.exists(path): continue
            file_size = os.path.getsize(path)
            if file_size >= file_max:
                file_max = file_size
                site_name = site["name"]
        return site_name

    # 获取首页概览
    def GetTemplateOverview(self, get):
        select_option_dict = {
            "site_all": public.M("sites").field("name").select()
        }

        overview_template = public.readFile(self._OVERVIEW_TEMPLATE)
        overview_template = json.loads(overview_template)
        for template in overview_template:
            template_option = template.get("option", [])
            for i in range(len(template_option)-1, -1, -1):
                option = template_option[i]
                if option["name"] == "total":
                    if not os.path.exists("/www/server/panel/plugin/total"):
                        del template_option[i]
                        continue

                if option.get("status", False) is False:
                    if option.get("type") == "plugin":  # 插件
                        plugin_path = os.path.join(self._PLUGIN_DIR, option["name"])
                        option["status"] = os.path.exists(plugin_path)

                option_params = option.get("params", [])
                for params in option_params:
                    select_option = params.get("select_option")
                    if select_option is not None and select_option_dict.get(select_option) is not None:
                        params["option"] = select_option_dict.get(select_option)
                        for site in params["option"]:
                            site["source"] = site["name"]
        return {"status": True, "msg": "ok", "data": overview_template}

    # 获取首页概览
    def GetOverview(self, get):
        func_dict = {
            "sites": self._base,
            "ftps": self._base,
            "databases": self._base,
            "total": self._total,
            "safety_risk": self._safety_risk,
            "memo": self._memo,
            "btwaf": self._btwaf,
            "tamper_core": self._tamper_core,
            "ssh_log": self._ssh_log,
            "open_dir": self._open_dir,
            "monitor": self._monitor,
        }
        try:
            overview_setting = public.readFile(self._OVERVIEW_SETTING)
            overview_setting = json.loads(overview_setting)
        except Exception as err:
            overview_setting = []

        nlist = []
        for overview in overview_setting:
            if overview.get("title", '') == "文件/内容快速查找":
                nlist.append(overview)
            overview["value"] = []
            params_list = overview.get("params")
            if not params_list or len(params_list) == 0 or not params_list[0]: continue
            if overview.get("name") == "sites":
                overview["source"]["href"] = "/site"
                if params_list[0].get("name") == "docker网站":
                    overview["source"]["href"] = ""

            if overview.get("type") == "plugin":  # 插件
                from panelPlugin import panelPlugin
                get = public.dict_obj()
                get.sName = overview["name"]
                overview["plugin_info"] = panelPlugin().get_soft_find(get)

            if overview.get("status", False) is True:
                func = func_dict.get(overview["name"])
                if func is not None:
                    overview["value"] = func(overview["name"], params_list)
            if overview["name"] == "total":
                overview["title"] = "旧版监控报表"
                if not os.path.exists("/www/server/panel/plugin/total"): continue
            nlist.append(overview)

        return {"status": True, "msg": "ok", "data": nlist}

    # 添加首页概览
    def AddOverview(self, get):
        if not hasattr(get, "overview"):
            return public.returnMsg(False, "缺少参数! overview")
        try:
            overview_setting = public.readFile(self._OVERVIEW_SETTING)
            overview_setting = json.loads(overview_setting)
        except Exception as err:
            overview_setting = []

        overview = json.loads(get.overview)
        if None in overview["params"]:
            return public.returnMsg(False, "请添加网站后再开启此概览")

        if overview.get("value") is not None:
            del overview["value"]

        max_id = 0
        for over in overview_setting:
            if over["name"] == overview["name"]:
                if None in over["params"]:
                    overview_setting.remove(over)
                    break
                else:
                    return public.returnMsg(False, "已存在该概览！")
            if over["id"] > max_id: max_id = over["id"]

        overview["id"] = max_id + 1

        overview_setting.append(overview)

        public.writeFile(self._OVERVIEW_SETTING, json.dumps(overview_setting))
        return {"status": True, "msg": "添加成功！", "data": overview_setting}

    # 修改首页概览
    def SetOverview(self, get):
        if not hasattr(get, "overview"):
            return public.returnMsg(False, "缺少参数! overview")

        overview = json.loads(get.overview)

        overview_setting = []
        if isinstance(overview, list):
            overview_setting = overview
        elif isinstance(overview, dict):
            try:
                overview_setting = public.readFile(self._OVERVIEW_SETTING)
                overview_setting = json.loads(overview_setting)
            except Exception as err:
                overview_setting = []

            if overview.get("value") is not None:
                del overview["value"]

            for idx in range(len(overview_setting)):
                over = overview_setting[idx]
                if over["id"] == overview["id"]:
                    overview_setting[idx] = overview
                    break
            else:
                return public.returnMsg(False, "不存在！")

        public.writeFile(self._OVERVIEW_SETTING, json.dumps(overview_setting))
        return {"status": True, "msg": "修改成功！", "data": overview_setting}

    # 2024/12/25 17:30 拖动排序位置
    def SortOverview(self, get):
        get.overview = get.get("overview", None)
        if get.overview is None:
            return public.returnMsg(False, "缺少参数! overview")

        get.overview = json.loads(get.overview)

        try:
            overview_setting = public.readFile(self._OVERVIEW_SETTING)
            overview_setting = json.loads(overview_setting)
        except:
            return public.returnMsg(False, "获取数据失败！")

        new_overview_setting = []
        for ov in get.overview:
            for over in overview_setting:
                if over["id"] == ov:
                    new_overview_setting.append(over)
                    break

        public.writeFile(self._OVERVIEW_SETTING, json.dumps(new_overview_setting))
        return {"status": True, "msg": "修改成功！", "data": new_overview_setting}

    # 删除首页概览
    def DelOverview(self, get):
        if not hasattr(get, "overview_id"):
            return public.returnMsg(False, "缺少参数! overview_id")
        if not str(get.overview_id).isdigit():
            return public.returnMsg(False, "参数错误! overview_id")

        try:
            overview_setting = public.readFile(self._OVERVIEW_SETTING)
            overview_setting = json.loads(overview_setting)
        except Exception as err:
            overview_setting = []

        overview_id = int(get.overview_id)
        for idx in range(len(overview_setting) - 1, -1, -1):
            over = overview_setting[idx]
            if int(over["id"]) == overview_id:
                del overview_setting[idx]
                break

        ret = public.writeFile(self._OVERVIEW_SETTING, json.dumps(overview_setting))
        return {"status": True, "msg": "删除成功！", "data": overview_setting}

    # 获取基础功能数据
    def _base(self, name: str, params_list: list) -> list:
        source_dict = {
            "sites": lambda t_type: public.M("sites").count() if t_type == "all" else public.M("sites").where(
                "LOWER(project_type)=LOWER(?)", (t_type,)).count(),
            "ftps": lambda t_type: public.M("ftps").count() if t_type == "all" else public.M("ftps").where(
                "LOWER(status)=LOWER(?)", (t_type,)).count(),
            "databases": lambda t_type: public.M("databases").count() if t_type == "all" else public.M(
                "databases").where("LOWER(type)=LOWER(?)", (t_type,)).count(),
        }
        value_list = [0]
        for params in params_list:
            if name == "databases" and params["source"] == "redis":
                from databaseModel.redisModel import panelRedisDB
                data = panelRedisDB.get_options("databases", 16)
                if not isinstance(data, int):
                    data = 0
                value_list[0] = data
            elif name == "sites":
                where = ""
                if params["source"] != "all":
                    where = "LOWER(project_type)=LOWER('{}')".format(params["source"])
                value_list[0] = public.M("sites").where(where, ()).count() + public.M("docker_sites").count()
                docker_site_start_num = public.M("docker_sites").where("status=1", ()).count()
                docker_site_stop_num = public.M("docker_sites").where("status=0", ()).count()
                if where:
                    start_num = public.M("sites").where(where + " and status='1'", ()).count() + docker_site_start_num
                    stop_num = public.M("sites").where(where + " and status='0'", ()).count() + docker_site_stop_num
                else:
                    start_num = public.M("sites").where("status='1'", ()).count() + docker_site_start_num
                    stop_num = public.M("sites").where("status='0'", ()).count() + docker_site_stop_num
                value_list.append(start_num)
                value_list.append(stop_num)
            else:
                data = source_dict.get(name)(params["source"])
                if not isinstance(data, int):
                    data = 0
                value_list[0] = data
        return value_list

    # 云安全检测总风险数量
    def _safety_risk(self, name: str, params_list: list) -> list:
        # value_list = [0]
        # from panelWarning import panelWarning

        # data = panelWarning().get_scan_bar(None)
        # if isinstance(data, dict):
        #     safety_risk = data.get("count")
        #     value_list[0] = safety_risk

        # return value_list
        value_list = [0]
        try:
            # 使用PluginLoader调用云安全插件的方法
            import PluginLoader, public
            args = public.dict_obj()
            args.model_index = 'project'
            # 调用云查杀接口
            res = PluginLoader.module_run('safecloud', 'get_safecloud_list', args)
            
            if (isinstance(res, dict) and 
                res.get('status') is True and 
                isinstance(res.get('data'), dict)):
                
                total_risk = res['data'].get('total', 0)
                value_list[0] = total_risk
                return value_list
                
        except Exception as e:
            # 如果出错，记录日志（可选）
            # public.WriteLog('安全风险', f'从云安全获取数据失败: {str(e)}')
            pass
            
        # 如果上面失败，使用原来的方式获取数据
        try:
            from panelWarning import panelWarning
            data = panelWarning().get_scan_bar(None)
            if isinstance(data, dict):
                safety_risk = data.get("count", 0)
                value_list[0] = safety_risk
        except Exception:
            # 如果两种方式都失败，保持默认值0
            pass
                
        return value_list

    def _monitor(self, name: str, params_list: list) -> list:
        try:
            SiteName = params_list[0]['source']
            param = params_list[1]['source']
            __run_path = '{}/monitor'.format(public.get_setup_path())
            db_file = '{}/data/dbs/{}/{}.db'.format(__run_path, SiteName, 'request_total')
            if db_file not in self.__db_objs:
                if not os.path.exists(db_file) or os.path.getsize(db_file) == 0:
                    return [0, 0]
                import db
                db_obj = db.Sql()
                db_obj._Sql__DB_FILE = db_file
                self.__db_objs[db_file] = db_obj
            else:
                db_obj = self.__db_objs[db_file]
            # 构造查询条件
            now_time = datetime.datetime.now().strftime('%Y%m%d')
            last_time = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y%m%d')
            result = []
            for i in [now_time, last_time]:
                params_data = {
                    'pv': "SUM(pv_number) as pv",
                    'uv': "SUM(uv_number) as uv",
                    'ip': "SUM(ip_number) as ip",
                    'spider': "SUM(spider_count) as spider",
                }
                sql = 'select {} from request_total where date="{}";'.format(params_data[param], i)
                # 从数据库获取数据
                data = db_obj.table('request_total').query(sql)
                try:
                    data = data[0][0]
                    if data is None:
                        data = 0
                except:
                    data = 0
                result.append(data)
            db_obj.close()
            return result
        except:
            public.print_log(public.get_error_info())
            return []

    # 获取网站监控报表
    def _total(self, name: str, params_list: list) -> list:
        totoal_data_path = "/www/server/total/logs"
        value_list = [0, 0]

        site = params_list[0]["source"]
        target = params_list[1]["source"]  # pv u ip spider
        if target not in ["pv", "uv", "ip", "spider"]:
            return value_list

        site_db_path = os.path.join(totoal_data_path, site, "total.db")
        if not os.path.exists(site_db_path):
            return value_list

        today_time = datetime.date.today()
        today_start = today_time.strftime("%Y%m%d00")
        today_end = today_time.strftime("%Y%m%d23")

        db_obj = public.M("request_stat").dbfile(site_db_path)
        today_data = db_obj.field("sum({target}) as {target}".format(target=target)).where("time between ? and ?", (
        today_start, today_end)).find()
        if today_data and isinstance(today_data, dict) and today_data.get(target):
            value_list[0] = today_data[target]

        yesterday_time = today_time - datetime.timedelta(days=1)
        yesterday_start = yesterday_time.strftime("%Y%m%d00")
        yesterday_end = yesterday_time.strftime("%Y%m%d23")

        db_obj = public.M("request_stat").dbfile(site_db_path)
        yesterday_data = db_obj.field("sum({target}) as {target}".format(target=target)).where("time between ? and ?", (
        yesterday_start, yesterday_end)).find()
        if yesterday_data and isinstance(yesterday_data, dict) and yesterday_data.get(target):
            value_list[1] = yesterday_data[target]
        return value_list

    # waf
    def _btwaf(self, name: str, params_list: list) -> list:
        value_list = [0, 0]

        waf_db_path = "/www/server/btwaf/totla_db/totla_db.db"
        if not os.path.exists(waf_db_path):
            return value_list

        today_time = int(datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        yesterday_time = today_time - 86400
        try:
            today_data = public.M("totla_log").dbfile(waf_db_path).field('time').where("time>=?", (today_time)).order(
                'id desc').count()
            if isinstance(today_data, int):
                value_list[0] = today_data
        except:
            pass
        try:
            yesterday_data = public.M("totla_log").dbfile(waf_db_path).field('time').where("time>=? and time<=?", (
            yesterday_time, today_time)).order('id desc').count()
            if isinstance(yesterday_data, int):
                value_list[1] = yesterday_data
        except:
            pass
        return value_list

    # 防篡改
    def _tamper_core(self, name: str, params_list: list) -> list:
        value_list = [0, 0]

        tamper_core_dir = "/www/server/tamper/total"
        if not os.path.exists(tamper_core_dir):
            return value_list

        today_time = datetime.date.today()
        yesterday_time = today_time - datetime.timedelta(days=1)
        for p_name in os.listdir(tamper_core_dir):
            dir_path = os.path.join(tamper_core_dir, str(p_name))
            if not os.path.isdir(dir_path): continue

            today_path = os.path.join(dir_path, "{}.json".format(today_time))  # 今日
            if os.path.isfile(today_path):
                today_info = public.readFile(today_path)
                today_info = json.loads(today_info)
                for info in today_info.values():
                    value_list[0] += sum(info.values())

            yesterday_path = os.path.join(dir_path, "{}.json".format(yesterday_time))  # 昨日
            if os.path.isfile(yesterday_path):
                yesterday_info = public.readFile(yesterday_path)
                yesterday_info = json.loads(yesterday_info)
                for info in yesterday_info.values():
                    value_list[1] += sum(info.values())

        return value_list

    # SSH登录日志数
    def _ssh_log(self, name: str, params_list: list) -> list:
        value_list = [0, 0]

        # select = params_list[0]["source"]
        #
        # page = 1
        # args = public.dict_obj()
        # args.select = select
        #
        # # 获取数据
        # filepath = "/www/server/panel/config/ssh_intrusion.json"
        # is_today = False
        # if os.path.exists(filepath):
        #     try:
        #         filedata = json.loads(public.readFile(filepath))
        #         log_type = args.select
        #         if "data" in filedata and "today_success" in filedata["data"] and "today_error" in filedata["data"]:
        #             if log_type == "ALL":
        #                 value_list[0] = int(filedata["data"]["today_success"]) + int(filedata["data"]["today_error"])
        #             elif log_type == "Accepted":
        #                 value_list[0] = int(filedata["data"]["today_success"])
        #             elif log_type == "Failed":
        #                 value_list[0] = int(filedata["data"]["today_error"])
        #             is_today = True
        #     except:
        #         pass
        #
        # import PluginLoader
        #
        # while True:
        #     args.p = page
        #     args.model_index = "safe"  # 模块名
        #     args.count = 100
        #
        #     ssh_list = PluginLoader.module_run("syslog", "get_ssh_list", args)
        #     if not isinstance(ssh_list, list):
        #         break
        #     if len(ssh_list) == 0:
        #         break
        #
        #     today_time = datetime.date.today()
        #     yesterday_time = today_time - datetime.timedelta(days=1)
        #     for data in ssh_list:
        #         if str(data["time"]).startswith(str(today_time)):
        #             if is_today: continue
        #             value_list[0] += 1
        #         elif str(data["time"]).startswith(str(yesterday_time)):
        #             value_list[1] += 1
        #         else:
        #             return value_list
        #     page += 1
        return value_list

    # 快捷目录
    def _open_dir(self, name: str, params_list: list) -> list:
        value_list = []
        for params in params_list:
            value_list.append(params["source"])
        return value_list

    # 备忘录
    def _memo(self, name: str, params_list: list) -> list:
        value_list = []
        memo_path = "/www/server/panel/data/memo.txt"
        if not os.path.exists(memo_path):
            public.writeFile(memo_path, "")
        content = public.readFile(memo_path)
        value_list.append(content)
        return value_list
