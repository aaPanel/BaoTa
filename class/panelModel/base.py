# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: cjxin <cjxin@bt.cn>
# -------------------------------------------------------------------
# 面板其他模型新增功能
# ------------------------------
import json
import os
import time

import db
import public


class panelBase:
    history_data_dir = None
    data_dir = None
    __plugin_path = '/www/server/total'
    __frontend_path = '/www/server/panel/plugin/total'

    def __init__(self):
        pass

    @staticmethod
    def get_time_interval(local_time):
        time_key_format = "%Y%m%d00"
        start = int(time.strftime(time_key_format, local_time))
        time_key_format = "%Y%m%d23"
        end = int(time.strftime(time_key_format, local_time))
        return start, end

    @staticmethod
    def get_time_interval_min(local_time):
        time_key_format = "%Y%m%d0000"
        start = int(time.strftime(time_key_format, local_time))
        time_key_format = "%Y%m%d2359"
        end = int(time.strftime(time_key_format, local_time))
        return start, end

    def get_time_interval_hour(self, local_time, second):
        start = int(time.mktime(local_time) - second)
        start_str = time.strftime("%Y%m%d%H", time.localtime(start))
        end_str = time.strftime("%Y%m%d%H", local_time)
        return start_str, end_str

    def get_last_days(self, day):
        now = time.localtime()
        if day == 30:
            last_month = now.tm_mon - 1
            if last_month <= 0:
                last_month = 12
            import calendar
            _, last_month_days = calendar.monthrange(now.tm_year, last_month)
            day = last_month_days
        else:
            day += 1

        t1 = time.mktime(
            (now.tm_year, now.tm_mon, now.tm_mday - day, 0, 0, 0, 0, 0, 0))
        t2 = time.localtime(t1)
        start, _ = self.get_time_interval(t2)
        _, end = self.get_time_interval(now)
        start_7_day_hour, end_7_day_hour = self.get_time_interval_hour(now, 604800)
        start_one_day_hour, end_one_day_hour = self.get_time_interval_hour(now, 86400)
        start_hour, end_hour = self.get_time_interval_hour(now, 3600)
        return [start, end,
                start_one_day_hour, end_one_day_hour,
                start_hour, end_hour,
                start_7_day_hour, end_7_day_hour]

    @staticmethod
    def get_time_key(date=None):
        if date is None:
            date = time.localtime()
        time_key = 0
        time_key_format = "%Y%m%d%H"
        if type(date) == time.struct_time:
            time_key = int(time.strftime(time_key_format, date))
        if type(date) == str:
            time_key = int(time.strptime(date, time_key_format))
        return time_key

    def get_query_date(self, query_date):
        """
        获取查询日期的时间区间
        查询日期的表示形式是以区间的格式表示，这里也考虑到了数据库里面实际存储的方式。
        在数据库里面是以小时为单位统计日志数据，所以这里的区间也是也小时来表示。
        比如表示今天，假设今天是2021/3/30，查询日期的格式是2021033000-2021033023。
        @param query_date:
        @return: 2021033000-2021033023
        """
        start_date = None
        end_date = None
        if query_date == "today":
            start_date, end_date = self.get_time_interval(time.localtime())
        elif query_date == "yesterday":
            # day - 1
            now = time.localtime()
            yes_i = time.mktime((now.tm_year, now.tm_mon, now.tm_mday - 1, 0, 0, 0, 0, 0, 0))
            yes = time.localtime(yes_i)
            start_date, end_date = self.get_time_interval(yes)
        elif query_date.startswith("l"):
            days = int(query_date[1:])
            start_date, end_date = self.get_last_days(days)
        elif query_date.startswith("this_month"):
            now = time.localtime()
            start_date = time.localtime(time.mktime((now.tm_year, now.tm_mon, 1, 0, 0, 0, 0, 0, 0)))
            start_date = self.get_time_key(start_date)
            end_date = self.get_time_key(now) + 1
        elif query_date.startswith("h1"):
            # 近1小时查询
            # hours = int(query_date[1:])
            # 如果当前小时未超过30分钟，把上一小时数据计算进来，否则只算当前一小时的数据。
            now = time.localtime()
            if now.tm_min >= 30:
                start_date = time.mktime((now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, 0, 0, 0, 0, 0))
                start_date = self.get_time_key(start_date)
                end_date = start_date
            else:
                s = time.localtime(time.mktime((now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour - 1, 0, 0, 0, 0, 0)))
                start_date = self.get_time_key(s)
                e = time.localtime(time.mktime((now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, 0, 0, 0, 0, 0)))
                end_date = self.get_time_key(e)
        else:
            if query_date.find("-") >= 0:
                s, e = query_date.split("-")
                start_time = time.strptime(s.strip(), "%Y%m%d")
                start_date, _ = self.get_time_interval(start_time)
                end_time = time.strptime(e.strip(), "%Y%m%d")
                _, end_date = self.get_time_interval(end_time)
            else:
                if query_date.isdigit():
                    s_time = time.strptime(query_date, "%Y%m%d")
                    start_date, end_date = self.get_time_interval(s_time)

        return start_date, end_date

    def __get_file_json(self, filename, defaultv={}):
        try:
            if not os.path.exists(filename): return defaultv
            return json.loads(public.readFile(filename))
        except:
            os.remove(filename)
            return defaultv

    def __read_frontend_config(self):
        config_json = self.__frontend_path + "/config.json"
        data = {}
        if os.path.exists(config_json):
            data = json.loads(public.readFile(config_json))
        return data

    def get_default_site(self):
        config = self.__read_frontend_config()
        default = None
        if "default_site" in config:
            default = config["default_site"]
        if not default:
            site = public.M('sites').field('name').order("addtime").find()
            default = site["name"]
        return default

    def get_site_settings(self, site):
        """获取站点配置"""

        config_path = "/www/server/total/config.json"
        config = self.__get_file_json(config_path)
        if not config:
            return {}

        if site not in config.keys():
            res_config = config["global"]
            res_config["push_report"] = False
        else:
            res_config = config[site]

        for k, v in config["global"].items():
            if k not in res_config.keys():
                if k == "push_report":
                    res_config[k] = False
                else:
                    res_config[k] = v
        res_config["default_site"] = self.get_default_site()
        return res_config

    def get_data_dir(self):
        if self.data_dir is None:
            default_data_dir = os.path.join(self.__plugin_path, "logs")
            settings = self.get_site_settings("global")
            if "data_dir" in settings.keys():
                config_data_dir = settings["data_dir"]
            else:
                config_data_dir = default_data_dir
            self.data_dir = default_data_dir if not config_data_dir else config_data_dir
        return self.data_dir

    def get_log_db_path(self, site, db_name="logs.db", history=False):
        site = site.replace('_', '.')
        if not history:
            data_dir = self.get_data_dir()
            db_path = os.path.join(data_dir, site, db_name)
        else:
            data_dir = self.get_history_data_dir()
            db_name = "history_logs.db"
            db_path = os.path.join(data_dir, site, db_name)
        return db_path

    def get_history_data_dir(self):
        if self.history_data_dir is None:
            default_history_data_dir = os.path.join(self.__plugin_path, "logs")
            settings = self.get_site_settings("global")
            if "history_data_dir" in settings.keys():
                config_data_dir = settings["history_data_dir"]
            else:
                config_data_dir = default_history_data_dir
            self.history_data_dir = default_history_data_dir if not config_data_dir else config_data_dir
        return self.history_data_dir

    def _get_ts(self, get):
        """
        @获取数据库连接对象
        @return:
        """
        db_name = get.db_name if "db_name" in get else "total.db"
        db_path = self.get_log_db_path(get.site_name, db_name=db_name)  # 数据库路径
        if not os.path.isdir(os.path.dirname(db_path)):
            os.makedirs(os.path.dirname(db_path))
            public.set_mode(os.path.dirname(db_path), "755")
            public.set_own(os.path.dirname(db_path), "www")

        ts = db.Sql()
        ts.dbfile(db_path)
        if not ts:
            return False
        return ts
