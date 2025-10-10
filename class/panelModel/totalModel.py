# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: cjxin <cjxin@bt.cn>
# -------------------------------------------------------------------

# 备份
# ------------------------------
import datetime
import json
import os
import time

import db
import public
from panelModel.base import panelBase


class main(panelBase):
    __plugin_path = '/www/server/total'
    _limit_config_file = __plugin_path + '/limit_config.json'
    _flow_push_config_file = '/www/server/panel/class/push/flow_push.json'
    _limit_total_create_time_file = __plugin_path + '/logs/{}/limit_total_create_time.json'
    __frontend_path = '/www/server/panel/plugin/total'

    def __init__(self):
        pass

    def get_site_flow(self, site, start_date, end_date):
        """获取站点总流量"""
        db_path = self.get_log_db_path(site, db_name='total.db')
        ts = db.Sql()
        ts.dbfile(db_path)
        total_flow = 0
        if not ts:
            return total_flow
        # 统计数据
        ts.table("request_stat").field('sum(length) as length')
        ts.where("time between ? and ?", (start_date, end_date))
        sum_data = ts.find()

        if type(sum_data) != dict:
            sum_data['length'] = 0
            return sum_data

        total_flow = sum_data['length'] if sum_data['length'] else 0

        return total_flow

    def get_realtime_traffic(self, site=None):
        """获取实时流量"""
        res_data = []
        if site is not None:
            flow_file = self.__plugin_path + "/logs/{}/flow_sec.json".format(
                site)
            if not os.path.isfile(flow_file):
                return res_data
            flow_data = public.readFile(flow_file)
            datetime_now = datetime.datetime.now()
            lines = flow_data.split("\n")
            for line in lines:
                if not line: continue
                try:
                    _flow, _write_time = line.split(",")
                    datetime_log = datetime.datetime.fromtimestamp(
                        float(_write_time))
                    datetime_interval = datetime_now - datetime_log
                    if datetime_interval.seconds < 3:
                        data = {"timestamp": _write_time, "flow": int(_flow)}
                        res_data.append(data)

                except Exception as e:
                    print("Real-time traffic error:", str(e))
            if len(res_data) > 1:
                res_data.sort(key=lambda o: o["timestamp"], reverse=True)
        return res_data

    def get_site_overview_sum_data(self, site, start_date, end_date):
        """获取站点流量数据"""
        sum_data = {}
        db_path = self.get_log_db_path(site, db_name='total.db')
        ts = db.Sql()
        ts.dbfile(db_path)
        if not ts:
            return sum_data
        # 统计数据
        ts.table("request_stat").field('time,length')
        ts.where("time between ? and ?", (start_date, end_date))
        sum_data = ts.select()
        return sum_data

    def get_site_traffic(self, get):
        """
       @获取网站总流量和实时流量
       @return
           data : 网站总流量和实时流量
           data:{
                'site':{
                'total_flow': 网站总流量
                'realtime_traffic': 实时流量
                }
           }
       """
        if not os.path.exists(self.__frontend_path):
            return {'data': {}, 'msg': '请先安装网站监控报表！', 'status': False}

        try:
            date = self.get_last_days(30)
            sites = public.M('sites').field('name').order("addtime").select()
            data = {}
            msg = True
            for site_info in sites:
                try:
                    site = site_info["name"]
                    data[site] = {
                        'total_flow': 0,
                        '7_day_total_flow': 0,
                        'one_day_total_flow': 0,
                        'one_hour_total_flow': 0
                        # 'realtime_traffic': realtime_traffic
                    }
                    for key in data[site].keys():
                        if key == "total_flow":
                            start_date = date[0]
                            end_date = date[1]
                        elif key == "one_day_total_flow":
                            start_date = date[2]
                            end_date = date[3]
                        elif key == "one_hour_total_flow":
                            start_date = date[4]
                            end_date = date[5]
                        elif key == "l7_day_total_flow":
                            start_date = date[6]
                            end_date = date[7]
                        data[site][key] = self.get_site_flow(
                            site,
                            start_date,
                            end_date
                        )
                    # realtime_traffic_list = self.get_realtime_traffic(site)
                    # if len(realtime_traffic_list) > 0:
                    #     realtime_traffic = realtime_traffic_list[0]["flow"]
                    # else:
                    #     realtime_traffic = 0
                except Exception as e:
                    msg = str(e)
                    if msg.find("object does not support item assignment") != -1:
                        msg = "数据文件/www/server/total/logs/{}/logs.db已损坏。".format(site)

            return {'data': data, 'msg': msg, 'status': True}

        except Exception as e:
            return {'data': {}, 'msg': e, 'status': False}

    @staticmethod
    def monitor_config_data():
        """
        @name 获取网站监控报表重构版配置文件
        """
        conf_file = '{}/monitor/config/config.json'.format(public.get_setup_path())
        try:
            conf_data_str = public.readFile(conf_file)
            conf_data = json.loads(conf_data_str)
            if isinstance(conf_data, dict):
                return conf_data
        except Exception as e:
            pass
        return None

    def new_get_site_traffic(self, args):
        """
        @name 获取网站总流量和实时流量
        @param args.names 获取的网站列表
        @return dict
           {"one_day_total_flow": 0}
        """
        if not os.path.exists("/www/server/panel/plugin/monitor"):
            return {'data': {}, 'msg': '请先安装重构版网站监控报表！', 'status': False}
        if 'names' in args:
            names = args.names
        else:
            names = []
        monitor_config = self.monitor_config_data()
        db_path = monitor_config['data_save_path']
        if not os.path.isdir(db_path):
            return {'data': {}, 'msg': "没有相关数据", 'status': True}
        try:
            result_data = {}
            now_time = int(time.time())
            start_time = public.format_date(format="%Y%m%d", times=now_time)

            fields = 'SUM(sent_bytes) as one_day_total_flow'

            for i in names:
                db_file = '{}/{}/{}.db'.format(db_path, i, "request_total")
                if not os.path.exists(db_file):
                    continue
                db_obj = db.Sql()
                db_obj._Sql__DB_FILE = db_file
                tmp_result = db_obj.table('request_total').where("date=? Group By date", (start_time,)).field(fields).find()
                if 'one_day_total_flow' in tmp_result:
                    result_data[i] = tmp_result
                else:
                    result_data[i] = {"one_day_total_flow": 0}
                db_obj.close()
            return {'data': result_data, 'msg': True, 'status': True}
        except:
            pass
        return {'data': {}, 'msg': "获取失败", 'status': True}

    def get_all_site_flow(self, get):
        """
        @获取网站流量数据
        @param get['start'] 开始时间
        @param get['end'] 结束时间
        @return
            data' : 网站流量数据
            data:{
                [
                {'time': 时间戳, 'length': 网站总流量}
                ]
            }
        """
        if not os.path.exists(self.__frontend_path):
            return {'data': {}, 'msg': '请先安装网站监控报表！', 'status': False}

        try:
            msg = True
            time_key_format = "%Y%m%d%H"
            start_date = int(get.start)
            end_date = int(get.end)
            start_date = int(time.strftime(time_key_format, time.localtime(start_date)))
            end_date = int(time.strftime(time_key_format, time.localtime(end_date)))

            list_data = []
            sites = public.M('sites').field('name').order("addtime").select()
            for site_info in sites:
                try:
                    site = site_info["name"]
                    site_overview_info = self.get_site_overview_sum_data(site, start_date, end_date)
                    if site_overview_info:
                        list_data.append(site_overview_info)

                except Exception as e:
                    msg = str(e)
                    if msg.find("object does not support item assignment") != -1:
                        msg = "数据文件/www/server/total/logs/{}/logs.db已损坏。".format(site)

            data = dict()
            for site_info in list_data:
                for i in site_info:
                    if data.get(i['time']):
                        data[i['time']] += i['length']
                    else:
                        data[i['time']] = i['length']

            result = [{'time': k, 'length': v} for k, v in data.items()]

            def sort_key(d):
                return d['time']

            result.sort(key=sort_key, reverse=False)

            return {'data': result, 'msg': msg, 'status': True}
        except Exception as e:
            return {'data': [], 'msg': e, 'status': False}

    # 网站 --》 php项目 --》 流量限制 --》 流量限额
    def get_generated_flow_info(self, get):
        """
        @获取已产生的流量相关信息
        @param get:
        @return:
        """
        get.site_name = get.site_name if "site_name" in get else self.get_default_site()
        today_time = int(time.strftime("%Y%m%d%H", time.localtime()))
        tomorrow_time = int(time.strftime("%Y%m%d%H", time.localtime(time.time() + 86400)))
        sum_data = {"length": 0, "request": 0}

        if not os.path.exists(self._limit_total_create_time_file.format(get.site_name)):
            return sum_data

        try:
            create_time = json.loads(public.readFile(self._limit_total_create_time_file.format(get.site_name)))
            limit_total_create_time = create_time["limit_total_create_time"]
        except:
            limit_total_create_time = int(time.strftime("%Y%m%d%H", time.localtime()))

        time_interval = int(str(today_time)[0:8]) - int(str(limit_total_create_time)[0:8])
        if time_interval >= 30:
            start_time = int(time.strftime("%Y%m%d", time.localtime(time.time() - 2592000)))
            end_time = tomorrow_time
        else:
            start_time = limit_total_create_time
            end_time = tomorrow_time

        ts = self._get_ts(get)
        if not ts:
            return sum_data

        ts.table("request_stat").field('sum(length) as length,sum(req) as request')
        ts.where("time between ? and ?", (start_time, end_time))
        res = ts.find()
        ts.close()
        if type(res) != dict:
            return sum_data

        return res

    def get_limit_config(self, get):
        """
        @获取流量限制配置
        @param get:
        @return:
        """
        limit_result = []
        time_period = {
            "month": "1个自然月",
            "30day": "30天",
            "1day": "1天",
            "1h": "1小时",
            "30m": "30分钟",
            "10m": "10分钟"
        }

        get.site_name = get.site_name if "site_name" in get else self.get_default_site()
        _limit_config = self._read_flow_config(self._limit_config_file)
        if len(_limit_config) == 0:
            return limit_result
        for l_conf in _limit_config:
            if l_conf["site_name"] == get.site_name:
                if len(l_conf["rules"]) == 0:
                    return limit_result

                for rule in l_conf["rules"]:
                    limit_unit = "次数" if rule["limit_unit"] == "frequency" else "流量"
                    limit_action = "告警" if rule["limit_action"] == "alert" else "告警并停止网站"
                    tmp = {
                        "id": rule["id"],
                        "limit_status": rule["limit_status"],
                        "rule_type": "累计" if rule["rule_type"] == "total" else "实时",
                        "time_period": time_period[rule["time_period"]],
                        "limit_value": rule["limit_value"] + rule["limit_unit"],
                        "rule": "当访问【{}】超过限额阈值【{}%】时【{}】".format(
                            limit_unit,
                            rule["threshold_percentage"],
                            limit_action
                        )
                    }
                    limit_result.append(tmp)
                return limit_result

        return limit_result

    def set_limit_status(self, get):
        """
        @设置流量限制状态
        @param get:
        @return:
        """
        get.site_name = get.site_name if "site_name" in get else self.get_default_site()
        get.id = int(get.id) if "id" in get else 0
        get.limit_status = get.limit_status if "limit_status" in get else "true"

        if get.limit_status == "true":
            get.limit_status = True
        elif get.limit_status == "false":
            get.limit_status = False
        else:
            get.limit_status = False

        _limit_config = self._read_flow_config(self._limit_config_file)
        for l_conf in _limit_config:
            if l_conf["site_name"] == get.site_name:
                if len(l_conf["rules"]) == 0:
                    return public.returnMsg(False, '规则不存在')
                for rule in l_conf["rules"]:
                    if rule["id"] == get.id:
                        rule["limit_status"] = get.limit_status
                        break
                else:
                    return public.returnMsg(False, '规则不存在')
                break
        else:
            return public.returnMsg(False, '规则不存在')

        if self._write_flow_config(_limit_config, self._limit_config_file) is False:
            return public.returnMsg(False, '写入配置文件失败')

        return public.returnMsg(True, '设置成功')

    def _read_flow_config(self, file_path):
        """
        @读取流量限制配置
        @param file_path:
        @return:
        """
        if not os.path.exists(file_path):
            if file_path == "/www/server/panel/class/push/push.json":
                return {}
            if file_path == '/www/server/panel/class/push/flow_push.json':
                return {}
            return []
        try:
            return json.loads(public.readFile(file_path))
        except:
            if file_path == "/www/server/panel/class/push/push.json":
                return {}
            if file_path == '/www/server/panel/class/push/flow_push.json':
                return {}
            return []

    def _write_flow_config(self, config, file_path):
        """
        @写入流量限制配置
        @param config:
        @param file_path:
        @return:
        """
        try:
            public.writeFile(file_path, json.dumps(config))
            return True
        except Exception as e:
            print(str(e))
            return False

    def _structure_limit_config(self, get):
        """
        @构造准备写入的配置文件内容
        @param get:
        @return:
        """
        limit_rule = {
            "limit_status": get.limit_status,
            "rule_type": get.rule_type,
            "time_period": get.time_period,
            "limit_value": get.limit_value,
            "limit_unit": get.limit_unit,
            "limit_action": get.limit_action,
            "threshold_percentage": get.threshold_percentage,
            "cycle": get.cycle,
            "module": get.module
        }
        _limit_config = self._read_flow_config(self._limit_config_file)
        for l_conf in _limit_config:
            if l_conf["site_name"] == get.site_name:
                existing_ids = [rule["id"] for rule in l_conf["rules"]]
                if existing_ids:
                    new_id = max(existing_ids) + 1
                else:
                    new_id = 1
                limit_rule["id"] = new_id
                l_conf["rules"].append(limit_rule)
                break
        else:
            conf_id = 1
            limit_rule["id"] = conf_id
            _limit_config.append({"site_name": get.site_name, "rules": [limit_rule]})
        return _limit_config, limit_rule["id"]

    def create_flow_rule(self, get):
        """
        @创建流量限制规则
        @param get:
        @return:
        """
        get.site_name = get.site_name if "site_name" in get else self.get_default_site()  # 站点名称
        get.rule_type = get.rule_type if "rule_type" in get else 'total'  # total:总流量限制 moment:实时流量限制
        get.time_period = get.time_period if "time_period" in get else "30day"  # 限制时间段
        get.limit_value = get.limit_value if "limit_value" in get else 10  # 限制值
        get.limit_unit = get.limit_unit if "limit_unit" in get else "GB"  # 限制单位
        get.limit_action = get.limit_action if "limit_action" in get else "alert"  # 限制动作
        get.threshold_percentage = get.threshold_percentage if "threshold_percentage" in get else 80  # 阈值百分比
        get.limit_status = get.limit_status if "limit_status" in get else "true"  # 状态
        get.cycle = get.cycle if "cycle" in get else 2  # 告警次数
        get.module = get.module if "module" in get else "mail"  # 告警方式

        if get.limit_status == "true":
            get.limit_status = True
        elif get.limit_status == "false":
            get.limit_status = False
        else:
            get.limit_status = True

        if self._create_table(get) is False:
            return public.returnMsg(False, '创建表失败')

        _limit_config, l_id = self._structure_limit_config(get)
        if self._write_flow_config(_limit_config, self._limit_config_file) is False:
            return public.returnMsg(False, '写入配置文件失败')

        if not self._set_push_config(get, l_id)["status"]:
            return public.returnMsg(False, '设置告警失败')

        if not os.path.exists(self._limit_total_create_time_file.format(get.site_name)):
            limit_total_create_time = int(time.strftime("%Y%m%d%H", time.localtime()))
            public.writeFile(self._limit_total_create_time_file.format(get.site_name), json.dumps({
                "limit_total_create_time": limit_total_create_time
            }))

        return public.returnMsg(True, '创建成功')

    def _create_table(self, get):
        """
        @创建表
        @param get:
        @return:
        """
        ts = self._get_ts(get)
        if not ts:
            return False

        if get.rule_type == "moment":
            time_key_format = "%Y%m%d"
            today = int(time.strftime(time_key_format, time.localtime()))
            table_name = "flow_minute_limit_{}".format(today)
        else:
            table_name = "flow_day_limit"

        sql = """
        CREATE TABLE IF NOT EXISTS {} (
            time INTEGER primary key, 
            req INTEGER default 0, 
            length INTEGER default 0
        );""".format(table_name)
        ts.execute(sql)
        ts.execute("create index {}_time_index on {} (time);".format(table_name, table_name))
        ts.table("sqlite_master").field('name').where("type=? and name=?", ('table', table_name))
        res = ts.count()
        ts.close()
        if not res:
            return False
        return True

    def remove_flow_rule(self, get):
        """
        @删除流量限制规则
        @param get:
        @return:
        """
        get.site_name = get.site_name if "site_name" in get else ""
        get.id = int(get.id) if get.id else 0

        _limit_config = self._read_flow_config(self._limit_config_file)
        for l_conf in _limit_config:
            if l_conf["site_name"] == get.site_name:
                if len(l_conf["rules"]) == 0:
                    self._remove_all_table(get)
                    return public.returnMsg(False, '规则不存在')
                for rule in l_conf["rules"]:
                    if rule["id"] == get.id:
                        l_conf["rules"].remove(rule)
                        if len(l_conf["rules"]) == 0:
                            self._remove_all_table(get)
                        break
                else:
                    return public.returnMsg(False, '规则不存在')
                break
        else:
            self._remove_all_table(get)
            return public.returnMsg(False, '规则不存在')

        if self._write_flow_config(_limit_config, self._limit_config_file) is False:
            return public.returnMsg(False, '写入配置文件失败')

        _push_config = self._read_flow_config(self._flow_push_config_file)
        for k, v in _push_config.items():
            if v["l_id"] == get.id:
                del _push_config[k]
                break

        self._write_flow_config(_push_config, self._flow_push_config_file)
        self._remove_site_tip(get.site_name, get.id)

        return public.returnMsg(True, '删除成功')

    def _remove_site_tip(self, site_name, id):
        """
        @删除站点提示
        @param site_name:
        @param id:
        @return:
        """
        today_push_counter = '{}/data/push/tips/flow_today.json'.format(public.get_panel_path())
        t_day = datetime.datetime.now().strftime('%Y-%m-%d')
        if os.path.exists(today_push_counter):
            tip = json.loads(public.readFile(today_push_counter))
            if tip["t_day"] != t_day:
                return
            if site_name in tip:
                del tip[site_name][str(id)]
                public.writeFile(today_push_counter, json.dumps(tip))

    def _remove_all_table(self, get):
        """
        @删除所有指定网站的流量限制表
        @param get:
        @return:
        """
        if os.path.exists(self._limit_total_create_time_file.format(get.site_name)):
            os.remove(self._limit_total_create_time_file.format(get.site_name))
        ts = self._get_ts(get)
        if not ts:
            return False

        tables_list = ts.table("sqlite_master").field('name').where("type=?", ('table',)).select()

        ts.execute("drop table if exists flow_day_limit")
        ts.execute("drop table if exists flow_limit_total")
        for table in tables_list:
            if "flow_minute_limit_" in table["name"]:
                ts.execute("drop table if exists {}".format(table["name"]))
        ts.close()
        return True

    def modify_flow_rule(self, get):
        """
        @修改流量限制规则 TODO 修改接口暂时不对接
        @param get:
        @return:
        """
        get.site_name = get.site_name if "site_name" in get else self.get_default_site()
        get.id = int(get.id) if "id" in get else 0
        get.rule_type = get.rule_type if "rule_type" in get else 'total'  # total:总流量限制 moment:实时流量限制
        get.limit_unit = get.limit_unit if "limit_unit" in get else "GB"  # 限制单位
        get.limit_action = get.limit_action if "limit_action" in get else "alert"  # 限制动作
        get.limit_value = get.limit_value if "limit_value" in get else 10  # 限制值
        get.threshold_percentage = get.threshold_percentage if "threshold_percentage" in get else 80  # 阈值百分比

        _limit_config = self._read_flow_config(self._limit_config_file)
        for l_conf in _limit_config:
            if l_conf["site_name"] == get.site_name:
                if len(l_conf["rules"]) == 0:
                    return public.returnMsg(False, '规则不存在')
                for rule in l_conf["rules"]:
                    if rule["id"] == get.id:
                        rule["rule_type"] = get.rule_type
                        rule["limit_unit"] = get.limit_unit
                        rule["limit_action"] = get.limit_action
                        rule["limit_value"] = get.limit_value
                        rule["threshold_percentage"] = get.threshold_percentage
                        break
                else:
                    return public.returnMsg(False, '规则不存在')
                break
        else:
            return public.returnMsg(False, '规则不存在')

        if self._write_flow_config(_limit_config, self._limit_config_file) is False:
            return public.returnMsg(False, '写入配置文件失败')

        return public.returnMsg(True, '修改成功')

    def _set_push_config(self, get, l_id):
        import sys
        sys.path.insert(0, '/www/server/panel/class/push')
        from flow_push import flow_push
        flow_push = flow_push()

        cycle = get.cycle

        pdata = self._get_flow_push_json()
        public.WriteLog('告警设置', '添加告警任务【{}】'.format(pdata["title"]))

        if not 'module' in pdata or not pdata['module']:
            return public.returnMsg(False, '未设置指定告警方式，请重新选择.')

        public.set_module_logs('set_push_config', pdata['type'])

        id = time.time()
        pdata['id'] = id
        pdata['l_id'] = l_id
        pdata['cycle'] = cycle

        flow_push_path = "{}/class/push/push.json".format(public.get_panel_path())
        _flow_push = self._read_flow_config(flow_push_path)
        if "flow_push" not in _flow_push:
            _flow_push["flow_push"] = {
                "1695276484112": {
                    "key": "",
                    "type": "flow_push",
                    "cycle": 0,
                    "count": 0,
                    "interval": 600,
                    "module": "mail",
                    "title": "\u7f51\u7ad9\u6d41\u91cf\u9650\u989d\u544a\u8b66",
                    "project": "flow",
                    "status": True,
                    "push_count": 2,
                    "id": "1695276484112",
                    "index": 1695278173.645564,
                    "tips_list": []
                }
            }
            self._write_flow_config(_flow_push, flow_push_path)

        _push_config = self._read_flow_config(self._flow_push_config_file)
        _push_config[id] = pdata

        self._write_flow_config(_push_config, self._flow_push_config_file)

        result = flow_push.set_push_config(get.site_name, l_id)
        if not result['status']:
            return result
        return public.returnMsg(True, '保存成功.')

    def _get_flow_push_json(self):
        """
        @获取流量告警配置
        @return:
        """
        flow_push_conf = {
            "key": "",
            "type": "flow_push",
            "cycle": 0,
            "count": 0,
            "interval": 600,
            "module": "mail",
            "title": "网站流量限额告警",
            "project": "flow",
            "status": True,
            "push_count": 0,
            "id": "",
            "index": 0,
            "tips_list": [],
            "l_id": 0,
        }

        return flow_push_conf

    def __get_args(self, data, key, val='', type_list=(str,)):
        """
        @获取默认参数
        """
        if not key in data:
            data[key] = val
        if type(data[key]) not in type_list:
            data[key] = val
        return data
