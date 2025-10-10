# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------
# 网站流量模块
# ------------------------------
import json, time, datetime
import public
from panelModel.base import panelBase


class main(panelBase):
    # php模块流量快速分析
    def get_ip_flows_table_name(self):
        current_time = datetime.datetime.now()
        formatted_time = current_time.strftime("%Y%m")
        return "ip_flows_stat_" + formatted_time

    def format_current_time(self, get):
        """
        @获取当前时间
        @param get:
        @return:
        """
        query_time_dict = {
            "h1": 1,
            "l7": 1 * 24 * 6,
            "l30": 1 * 24 * 29
        }
        if get.query_date == "today":
            start_date, end_date = self.get_time_interval_min(time.localtime())
        elif get.query_date == "yesterday":
            start_date, end_date = self.get_time_interval_min(time.localtime(time.time() - 86400))
        elif get.query_date in query_time_dict:
            current_time = datetime.datetime.now()
            one_hour_ago = current_time - datetime.timedelta(hours=query_time_dict[get.query_date])
            start_date = one_hour_ago.strftime("%Y%m%d%H%M")
            end_date = current_time.strftime("%Y%m%d%H%M")
        else:
            start_date, end_date = self.get_time_interval_min(time.localtime())

        return start_date, end_date

    def process_trend_data(self, get, res):
        """
        @处理趋势数据
        @param get:
        @return:
        """
        query_time_dict = {
            "today": 100,
            "yesterday": 100,
            "l7": 10000,
            "l30": 10000
        }
        grouped_data = {}

        try:
            for item in res:
                hour = str(int(item["time"]) // query_time_dict[get.query_date])

                if hour not in grouped_data:
                    grouped_data[hour] = {"time": int(hour), "flow": 0}

                grouped_data[hour]["flow"] += item["flow"]
        except TypeError as e:
            print(e)
            return []

        return self._complete_data(list(grouped_data.values()), get)

    def _complete_data(self, data, get):
        """
        @补全数据
        @param data:
        @return:
        """
        start_time, end_time = self.format_current_time(get)
        if get.query_date == "today" or get.query_date == "yesterday":
            time_key = '%Y%m%d%H'
            start_time = str(start_time)[0:10]
            end_time = str(end_time)[0:10]
            delta = datetime.timedelta(hours=1)
        elif get.query_date == "l7" or get.query_date == "l30":
            time_key = '%Y%m%d'
            start_time = str(start_time)[0:8]
            end_time = str(end_time)[0:8]
            delta = datetime.timedelta(days=1)
        elif get.query_date == "h1":
            time_key = '%Y%m%d%H%M'
            delta = datetime.timedelta(minutes=1)
        else:
            time_key = '%Y%m%d'
            start_time = str(start_time)[0:8]
            end_time = str(end_time)[0:8]
            delta = datetime.timedelta(days=1)

        start_date = datetime.datetime.strptime(str(start_time), time_key)
        end_date = datetime.datetime.strptime(str(end_time), time_key)

        current_date = start_date
        try:
            while current_date <= end_date:
                current_time = int(current_date.strftime(time_key))
                if not any(entry["time"] == current_time for entry in data):
                    data.append({"time": current_time, "flow": 0})
                current_date += delta
        except TypeError as e:
            print(e)
            return []

        data.sort(key=lambda x: x["time"])
        return data

    def get_ip_flow_trend(self, get):
        """
        @获取IP流量趋势
        @param get:
        @return:
        """
        try:
            start_time, end_time = self.format_current_time(get)
            get.db_name = "ip_total.db"
            table_name = self.get_ip_flows_table_name()
            ts = self._get_ts(get)
            if not ts:
                return []

            ts.table(table_name)
            ts.field("time,flow")
            ts.where("time between ? and ?", (start_time, end_time))
            res = ts.select()
            ts.close()

            if "h1" in get.query_date:
                return self._complete_data(res, get)

            return self.process_trend_data(get, res)
        except:
            return []

    def get_ip_flows_areas_info(self, get):
        """
        @获取IP流量地区top10信息
        @param get:
        @return:
        """
        start_time, end_time = self.format_current_time(get)
        # print(start_time, end_time)
        get.db_name = "ip_total.db"
        table_name = self.get_ip_flows_table_name()
        ts = self._get_ts(get)
        if not ts:
            return []

        query_sql = ("select ip,country,province,city,sum(flow) as flow from {} "
                     "where time between ? and ? and ip != ''"
                     "group by ip order by flow desc limit 10").format(table_name)
        res = ts.query(query_sql, (start_time, end_time))
        ts.close()

        # 封装数据
        data = []
        ip_rules_file = "data/ssh_deny_ip_rules.json"
        try:
            ip_rules = json.loads(public.readFile(ip_rules_file))
        except Exception:
            ip_rules = []

        try:
            for item in res:
                deny_status = 1 if item[0] in ip_rules else 0
                if deny_status == 0:
                    panel_ip_deny = public.M('firewall_ip').field("address").select()
                    for i in panel_ip_deny:
                        if i["address"] == item[0]:
                            deny_status = 1
                            break

                data.append({
                    "ip": item[0],
                    "country": item[1],
                    "province": item[2],
                    "city": item[3],
                    "flow": item[4],
                    "deny_status": deny_status
                })
        except IndexError as e:
            print(e)
            return []

        return data
