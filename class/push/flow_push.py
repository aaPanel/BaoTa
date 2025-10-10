# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2020 宝塔软件(https://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: baozi <wzz@bt.cn>
# | Author: wzz
# | Version: 4.2
# +-------------------------------------------------------------------
import os
import json
import re
import sys
import time
from datetime import datetime, timedelta
from typing import Iterator, Optional, List, Dict

class_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# /www/server/panel/class
sys.path.insert(0, class_path)

import public, panelPush, db


class base_push:

    # 版本信息 目前无作用
    def get_version_info(self, get=None):
        raise NotImplementedError

    # 格式化返回执行周期， 目前无作用
    def get_push_cycle(self, data: dict):
        return data

    # 获取模块推送参数
    def get_module_config(self, get: public.dict_obj):
        raise NotImplementedError

    # 获取模块配置项
    def get_push_config(self, get: public.dict_obj):
        # 其实就是配置信息，没有也会从全局配置文件push.json中读取
        raise NotImplementedError

    # 删除推送配置
    def del_push_config(self, get: public.dict_obj):
        # 从配置中删除信息，并做一些您想做的事，如记日志
        raise NotImplementedError

    # 无意义？？？
    def get_total(self):
        return True

    # 检查并获取推送消息，返回空时，不做推送, 传入的data是配置项
    def get_push_data(self, data, total):
        # data 内容
        # index :  时间戳 time.time()
        # 消息 以类型为key， 以内容为value， 内容中包含title 和msg
        # push_keys： 列表，发送了信息的推送任务的id，用来验证推送任务次数（） 意义不大
        raise NotImplementedError


class flow_push(base_push):
    __push_conf = "{}/class/push/push.json".format(public.get_panel_path())
    __flow_limit_conf = "/www/server/total/limit_config.json"
    __plugin_path = '/www/server/total'

    def __init__(self) -> None:
        self.__push = panelPush.panelPush()
        self._tip_counter = None
        self._push_counter = None

    # 版本信息 目前无作用
    def get_version_info(self, get=None):
        data = {}
        data['ps'] = '网站流量限额告警'
        data['version'] = '1.0'
        data['date'] = '2023-09-21'
        data['author'] = '宝塔'
        data['help'] = 'http://www.bt.cn/bbs'
        return data

    # 获取模块推送参数
    def get_module_config(self, get: public.dict_obj):
        data = []
        item = self.__push.format_push_data(push=["mail", 'dingding', 'weixin', "feishu", "wx_account"],
                                            project='rsync', type='')
        item['cycle'] = 30
        item['title'] = '网站流量限额'
        data.append(item)
        return data

    # 获取模块配置项
    def get_push_config(self, get: public.dict_obj):
        id = get.id
        # 其实就是配置信息，没有也会从全局配置文件push.json中读取
        push_list = self.__push._get_conf()

        if id not in push_list["flow_push"]:
            res_data = public.returnMsg(False, '未找到指定配置.')
            res_data['code'] = 100
            return res_data
        result = push_list["flow_push"][id]
        return result

    def get_flow_limit_conf(self):
        """
        获取网站流量限额配置文件
        @return:
        """
        try:
            flow_limit_conf = json.loads(public.readFile(self.__flow_limit_conf))
        except (json.JSONDecodeError, TypeError):
            flow_limit_conf = []

        return flow_limit_conf

    # 写入推送配置文件
    def set_push_config(self, site_name, id):
        flow_limit_conf = self.get_flow_limit_conf()
        if len(flow_limit_conf) == 0:
            return public.returnMsg(False, '没有配置网站流量限额，无法设置告警')

        self._del_today_push_counter({"site_name": site_name, "id": id})

        return public.returnMsg(True, '已设置网站流量限额告警')

    # 删除推送配置
    def del_push_config(self, get: public.dict_obj):
        # 从配置中删除信息，并做一些您想做的事，如记日志
        id = get.id
        data = self.__push._get_conf()
        if str(id).strip() in data["flow_push"]:
            del data["flow_push"][id]
        public.writeFile(self.__push_conf, json.dumps(data))
        return public.returnMsg(True, '删除成功.')

    # 无意义？？？
    def get_total(self):
        return True

    def _get_ts(self, site_name):
        """
        @获取数据库连接对象
        @return:
        """
        sys.path.insert(0, "/www/server/panel/plugin/total")
        from total_base import totalBase

        totalbase = totalBase()

        db_path = totalbase.get_log_db_path(site_name, db_name='total.db')  # 数据库路径
        ts = db.Sql()
        ts.dbfile(db_path)
        if not ts:
            return False
        return ts

    def get_flow_limit_push_data(self):
        """
        获取网站流量限额推送数据
        @return:
        """
        limit_rule = []
        _limit_config = self.get_flow_limit_conf()
        if len(_limit_config) == 0: return []

        for l_conf in _limit_config:
            ts = self._get_ts(l_conf["site_name"])
            if not ts: continue

            for rule in l_conf["rules"]:
                if rule["limit_status"] is False: continue
                start_time, end_time, table_name = self._get_time_range_table_name(rule)

                ts.table(table_name).field('sum(length) as length,sum(req) as request')
                res = ts.where("time between ? and ?", (start_time, end_time)).find()

                if type(res) != dict: continue
                if res["length"] is None and res["request"] is None: continue

                _is_push, n_res = self._compare_threshold_percentage(rule, res)
                if _is_push:
                    if rule["limit_action"] != "alert":
                        self._stop_site(l_conf["site_name"])
                    push_msg = self._structure_push_msg(l_conf, rule, n_res)
                    limit_rule.append({
                        "site_name": l_conf["site_name"],
                        "push_msg": push_msg,
                        "cycle": rule["cycle"],
                        "module": rule["module"],
                        "id": rule["id"]
                    })
            ts.close()

        return limit_rule

    def _structure_push_msg(self, l_conf, rule, n_res):
        """
        @构造告警内容
        @param l_conf:
        @param rule:
        @param n_res:
        @return:
        """
        time_period = {
            "month": "1个自然月",
            "30day": "30天",
            "1day": "1天",
            "1h": "1小时",
            "30m": "30分钟",
            "10m": "10分钟"
        }

        limit_unit = "访问请求次数" if rule["limit_unit"] == "frequency" else "访问流量"
        limit_action = "告警" if rule["limit_action"] == "alert" else "告警并停止网站"
        limit_period = time_period[rule["time_period"]]
        if rule["limit_unit"] == "frequency":
            rule_unit = "次"
            r_res = n_res[1]
            r_value = rule["limit_value"]
        else:
            rule_unit = rule["limit_unit"]
            r_res, _ = self._to_size(n_res[0])
            r_value, _ = self._to_size(int(rule["limit_value"]))

        push_msg = "当前网站【{}】产生的{}为【{} {}】，限额策略：限额【{} {}】，{}内超过阈值【{}%】则【{}】，请关注或及时处理！".format(
            l_conf["site_name"],
            limit_unit,
            r_res,
            rule_unit,
            r_value,
            rule_unit,
            limit_period,
            rule["threshold_percentage"],
            limit_action,
            limit_action
        )
        return push_msg

    def _get_time_range_table_name(self, rule):
        """
        @获取查询时间范围和表名
        @param rule:
        @return:
        """
        start_time = int(time.strftime("%Y%m%d%H", time.localtime(time.time() - 3600)))
        if rule["rule_type"] == "moment":
            time_key_format = "%Y%m%d"
            today = int(time.strftime(time_key_format, time.localtime()))
            table_name = "flow_minute_limit_{}".format(today)
            if rule["time_period"] == "10m":
                start_time = int(time.strftime("%Y%m%d%H%M", time.localtime(time.time() - 600)))
            elif rule["time_period"] == "30m":
                start_time = int(time.strftime("%Y%m%d%H%M", time.localtime(time.time() - 1800)))
            end_time = int(time.strftime("%Y%m%d%H%M", time.localtime(time.time() + 60)))
        else:
            table_name = "flow_day_limit"
            if rule["time_period"] == "1h":
                start_time = int(time.strftime("%Y%m%d%H", time.localtime(time.time() - 3600)))
            elif rule["time_period"] == "1day":
                start_time = int(time.strftime("%Y%m%d%H", time.localtime(time.time() - 86400)))
            elif rule["time_period"] == "30day":
                start_time = int(time.strftime("%Y%m%d%H", time.localtime(time.time() - 86400 * 30)))
            elif rule["time_period"] == "month":
                today = int(time.strftime("%d", time.localtime()))
                start_time = int(time.strftime("%Y%m%d%H", time.localtime(time.time() - 86400 * (today - 1))))
            end_time = int(time.strftime("%Y%m%d%H", time.localtime(time.time() + 3600)))

        return start_time, end_time, table_name

    def _compare_threshold_percentage(self, rule, res):
        """
        @比较是否超过设置的阈值百分比
        @param rule:
        @param res:
        @return:
        """
        try:
            if rule["limit_unit"] == "frequency":
                if int(res["request"]) / int(rule["limit_value"]) * 100 > int(rule["threshold_percentage"]):
                    return True, [res["length"], res["request"]]
            else:
                if rule["limit_unit"] == "GB":
                    rule["limit_value"] = int(rule["limit_value"]) * 1024 * 1024 * 1024
                elif rule["limit_unit"] == "MB":
                    rule["limit_value"] = int(rule["limit_value"]) * 1024 * 1024
                if int(res["length"]) / int(rule["limit_value"]) * 100 > int(rule["threshold_percentage"]):
                    return True, [res["length"], res["request"]]
            return False, None
        except TypeError:
            return False, None

    def _to_size(self, size):
        """
        @格式化流量单位，传进来的是字节，返回需要的单位和对应的值
        @param size:
        @return:
        """
        if size < 1024:
            return size, "B"
        elif size < 1024 * 1024:
            return round(size / 1024), "KB"
        elif size < 1024 * 1024 * 1024:
            return round(size / 1024 / 1024), "MB"
        elif size < 1024 * 1024 * 1024 * 1024:
            return round(size / 1024 / 1024 / 1024), "GB"
        else:
            return round(size / 1024 / 1024 / 1024 / 1024), "TB"

    # 检查并获取推送消息，返回空时，不做推送, 传入的data是配置项
    def get_push_data(self, data, total):
        # 返回内容
        # index :  时间戳 time.time()
        # 消息 以类型为key， 以内容为value， 内容中包含title 和msg
        # push_keys： 列表，发送了信息的推送任务的id，用来验证推送任务次数（） 意义不大
        """
        @检测推送数据，触发式任务使用这个
        @data dict 推送数据
            title:标题
            count:触发次数
            cycle:周期 天、小时
            keys:检测键值
        """
        flow_limit_push_data = self.get_flow_limit_push_data()
        if len(flow_limit_push_data) == 0: return None

        for push_data in flow_limit_push_data:
            s_list = [">通知类型：网站流量限额告警"]
            for m_module in push_data['module'].split(','):
                if m_module == 'sms':
                    continue

                cycle, sending_interval = self._get_today_push_counter(push_data)

                if cycle >= int(push_data["cycle"]): continue
                if int(time.time()) - sending_interval < 60: continue

                s_list.append(">告警内容：<font color=#ff0000>{}</font> \n".format(push_data["push_msg"]))

                sdata = public.get_push_info('网站流量限额告警', s_list)
                self._set_today_push_counter(push_data)

                if not sdata: continue

                msg_obj = public.init_msg(m_module)
                if not msg_obj: continue
                msg_obj.push_data(sdata)

        return None

    def _stop_site(self, site_name):
        """
        @停止网站
        @param site_name:
        @return:
        """
        id = public.M('sites').where('name=?', (site_name,)).getField('id')
        if not id: return False

        from panelSite import panelSite
        get = public.dict_obj()
        get.id = id
        get.name = site_name
        site_obj = panelSite()
        site_obj.SiteStop(get)

    def get_push_data_by_event(self, data, task_name: str):
        # 返回内容
        # index :  时间戳 time.time()
        # 消息 以类型为key， 以内容为value， 内容中包含title 和msg
        # push_keys： 列表，发送了信息的推送任务的id，用来验证推送任务次数（） 意义不大
        """
        @检测推送数据
        @data dict 推送数据
            title:标题
            count:触发次数
            cycle:周期 天、小时
            keys:检测键值
        """
        return None
        # if self._get_today_push_counter(data["id"]) >= data["push_count"]:
        #     return None
        # result = {'index': time.time(), }
        # flow_limit_push_data = self.get_flow_limit_push_data()
        # if len(flow_limit_push_data) == 0:
        #     return None
        #
        # for push_data in flow_limit_push_data:
        #     for m_module in data['module'].split(','):
        #         if m_module == 'sms':
        #             continue
        #         s_list = [
        #             ">通知类型：网站流量限额告警",
        #             ">告警内容：<font color=#ff0000>{}</font> ".format(push_data.push_msg),
        #         ]
        #         sdata = public.get_push_info('网站流量限额告警', s_list)
        #         result[m_module] = sdata
        # self._set_today_push_counter(data["id"])
        # return result

    @property
    def push_counter(self) -> dict:
        if self._push_counter is not None:
            return self._push_counter
        else:
            today_push_counter = '{}/data/push/tips/flow_today.json'.format(public.get_panel_path())
            t_day = datetime.now().strftime('%Y-%m-%d')
            if os.path.exists(today_push_counter):
                tip = json.loads(public.readFile(today_push_counter))
                if tip["t_day"] != t_day:
                    tip = {"t_day": t_day}
            else:
                tip = {"t_day": t_day}
        self._push_counter = tip
        return self._push_counter

    def save_push_counter(self):
        today_push_counter = '{}/data/push/tips/flow_today.json'.format(public.get_panel_path())
        if self._push_counter is not None:
            public.writeFile(today_push_counter, json.dumps(self.push_counter))

    def _get_today_push_counter(self, push_data):
        if push_data["site_name"] in self.push_counter:
            if str(push_data["id"]) in self.push_counter[push_data["site_name"]]:
                res = self.push_counter[push_data["site_name"]][str(push_data["id"])]
            else:
                res = 0

            if "sending_interval" in self.push_counter[push_data["site_name"]]:
                sending_interval = self.push_counter[push_data["site_name"]]["sending_interval"]
            else:
                sending_interval = 0
        else:
            res = 0
            sending_interval = 0
        return res, sending_interval

    def _set_today_push_counter(self, push_data):
        if push_data["site_name"] in self.push_counter:
            if str(push_data["id"]) in self.push_counter[push_data["site_name"]]:
                self.push_counter[push_data["site_name"]][str(push_data["id"])] += 1
            else:
                self.push_counter[push_data["site_name"]][str(push_data["id"])] = 1
        else:
            try:
                if type(self.push_counter[push_data["site_name"]]) != dict:
                    self.push_counter[push_data["site_name"]] = {}
            except:
                self.push_counter[push_data["site_name"]] = {}

            self.push_counter[push_data["site_name"]][str(push_data["id"])] = 1

        self.push_counter[push_data["site_name"]]["sending_interval"] = int(time.time())
        self.save_push_counter()

    def _del_today_push_counter(self, push_data):
        if push_data["site_name"] in self.push_counter:
            del self.push_counter[push_data["site_name"]][str(push_data["id"])]
        self.save_push_counter()

    @staticmethod
    def _get_bak_task_template():
        return {
            "field": [
                {
                    "attr": "interval",
                    "name": "间隔",
                    "type": "number",
                    "unit": "秒",
                    "suffix": "后，再次检查",
                    "default": 600
                },
                {
                    "attr": "push_count",
                    "name": "每日发送",
                    "type": "number",
                    "unit": "次",
                    "suffix": "后，不再发送，次日恢复",
                    "default": 2
                }
            ],
            "sorted": [
                # [
                #     "interval"
                # ],
                [
                    "push_count"
                ]
            ],
            "type": "flow_push",
            "module": [
                "wx_account",
                "dingding",
                "feishu",
                "mail",
                "weixin"
            ],
            "tid": "flow_push@0",
            "title": "网站流量限额告警",
            "name": "flow_push"
        }

    def get_task_template(self):
        # res_data = self._get_bak_task_template()
        return "", None

    @staticmethod
    def get_view_msg(task_id, task_data):
        task_data["tid"] = "flow_push@0"
        task_data["view_msg"] = "<span>网站流量/请求超出限额时，推送告警信息(每日推送{}次后不在推送)<span>".format(
            task_data["push_count"])
        return task_data

    def check_self_plugin(self):
        if os.path.exists(self.__flow_limit_conf):
            return True
        return False

    def main(self):
        if len(sys.argv) < 2:
            print("参数错误")
            return
        task_name = sys.argv[1]
        tip = FlowPushTip()
        try:
            data = self.__push._get_conf()
            if "flow_push" not in data:
                return
            flow_push_conf: Dict[str, dict] = data["flow_push"]
            for key, item in flow_push_conf.items():
                item['id'] = key
                if item["status"] is False:
                    continue  # 跳过关闭的任务
                if not (item["project"] in ("flow_push", "all") or item["project"] != task_name):
                    continue  # 跳过不匹配的任务
                if tip.have(task_name):
                    continue  # 推送时间频繁地跳过

                # 获取推送信息
                rdata = self.get_push_data_by_event(item, task_name)
                if not rdata:
                    continue
                for m_module in item['module'].split(','):
                    if m_module == "":
                        continue
                    if m_module not in rdata:
                        continue
                    msg_obj = public.init_msg(m_module)
                    if not msg_obj:
                        continue
                    msg_obj.push_data(rdata[m_module])
            tip.save_tip_list()
        except:
            print(public.get_error_info())


class FlowPushTip(object):
    _FILE = '{}/data/push/tips/flow_push.tip'.format(public.get_panel_path())

    def __init__(self):
        self._tip_map = None

    @property
    def tip_list(self) -> dict:
        if self._tip_map is not None:
            return self._tip_map

        if os.path.exists(self._FILE):
            try:
                tip = json.loads(public.readFile(self._FILE))
            except:
                tip = {}
        else:
            tip = {}

        self._tip_map = tip
        return self._tip_map

    def save_tip_list(self):
        if self._tip_map is not None:
            public.writeFile(self._FILE, json.dumps(self._tip_map))

    def have(self, name):
        now = time.time()
        if name in self.tip_list:
            if now > self.tip_list[name]:
                self.tip_list[name] = now + 60 * 3
                return False
            else:
                return True
        else:
            self.tip_list[name] = now + 60 * 3
            return False


class LogChecker:
    """
    排序查询并获取日志内容
    """
    rep_time = re.compile(r'(?P<target>(\w{3}\s+){2}(\d{1,2})\s+(\d{2}:?){3}\s+\d{4})')
    format_str = '%a %b %d %H:%M:%S %Y'
    err_datetime = datetime.fromtimestamp(0)
    err_list = ("error", "Error", "ERROR", "exitcode = 10", "failed")

    def __init__(self, log_file: str, start_time: datetime):
        self.log_file = log_file
        self.start_time = start_time
        self.is_over_time = None  # None:还没查到时间，未知， False: 可以继续网上查询， True:比较早的数据了，不再向上查询
        self.has_err = False  # 目前已查询的内容中是否有报错信息

    def _format_time(self, log_line) -> Optional[datetime]:
        try:
            date_str_res = self.rep_time.search(log_line)
            if date_str_res:
                time_str = date_str_res.group("target")
                return datetime.strptime(time_str, self.format_str)
        except Exception:
            return self.err_datetime
        return None

    # 返回日志内容
    def __call__(self):
        _buf = b""
        file_size, fp = os.stat(self.log_file).st_size - 1, open(self.log_file, mode="rb")
        fp.seek(-1, 2)
        while file_size:
            read_size = min(1024, file_size)
            fp.seek(-read_size, 1)
            buf: bytes = fp.read(read_size) + _buf
            fp.seek(-read_size, 1)
            if file_size > 1024:
                idx = buf.find(ord("\n"))
                _buf, buf = buf[:idx], buf[idx + 1:]
            for i in self._get_log_line_from_buf(buf):
                self._check(i)
                if self.is_over_time:
                    fp.close()
                    return self.has_err
            file_size -= read_size
        fp.close()
        return False

    # 从缓冲中读取日志
    @staticmethod
    def _get_log_line_from_buf(buf: bytes) -> Iterator[str]:
        n, m = 0, 0
        buf_len = len(buf) - 1
        for i in range(buf_len, -1, -1):
            if buf[i] == ord("\n"):
                log_line = buf[buf_len + 1 - m: buf_len - n + 1].decode("utf-8")
                yield log_line
                n = m = m + 1
            else:
                m += 1
        yield buf[0: buf_len - n + 1].decode("utf-8")

    # 格式化并筛选查询条件
    def _check(self, log_line: str) -> None:
        # 筛选日期
        for err in self.err_list:
            if err in log_line:
                self.has_err = True

        ck_time = self._format_time(log_line)
        if ck_time:
            self.is_over_time = self.start_time > ck_time


if __name__ == "__main__":
    flow_push = flow_push()
    flow_push.get_flow_limit_push_data()
    # flow_push().main()
