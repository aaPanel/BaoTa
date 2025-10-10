import datetime
import json
import os
import time
import importlib
from typing import Tuple, Union, Optional, Dict, List, Any

from .send_tool import WxAccountMsg
from .util import debug_log, get_webserver, read_file, set_module_logs
from .base_task import BaseTask, BaseTaskViewMsg

db = importlib.import_module("db", package="class")


class _MonitorWebInfo:

    def __init__(self):
        self.last_time = 0
        self._site_cache = None

    @property
    def site_list(self) -> List[Dict]:
        if self._site_cache is not None and time.time() - self.last_time < 300:
            return self._site_cache
        try:
            self._site_cache = self._get_can_set_site_list()
            site_list = self._site_cache
            self.last_time = time.time()
        except:
            site_list = []

        return site_list

    @classmethod
    def _get_can_set_site_list(cls) -> List[Dict]:
        webserver = get_webserver()
        if webserver not in ("nginx", "apache"):
            return []
        data = []
        panel_path = "/www/server/panel"
        for i in cls.all_site_list() + cls.docker_projects():
            if i['project_type'] in ("php", "proxy", "wp2", "docker"):
                file = "{}/vhost/{}/{}.conf".format(panel_path, webserver, i["name"])
            else:
                file = "{}/vhost/{}/{}_{}.conf".format(panel_path, webserver, i['project_type'], i["name"])
            if not os.path.exists(file):
                continue
            data.append({
                "title": i.get("rname", i["name"]),
                "value": i["name"]
            })
        return data

    @staticmethod
    def docker_projects() -> List[Dict]:
        db_path = "/www/server/panel/data/db/docker.db"
        sql = db.Sql()
        sql._Sql__DB_FILE = db_path

        if not os.path.exists(db_path):
            return []

        data = sql.table("docker_sites").field("id,name").select()
        res = []
        for i in data:
            res.append({
                "id": i["id"],
                "name": i["name"],
                "project_type": "docker"
            })

        return res

    @staticmethod
    def all_site_list() -> List[Dict]:
        sql = db.Sql()
        sites = sql.table("sites").select()
        res = []
        for i in sites:
            res.append({
                "id": i["id"],
                "name": i["name"],
                "project_type": i["project_type"].lower(),
                "rname": i.get("rname", i["name"])
            })

        return res


    def __call__(self, only_name: bool = False) -> List[Dict]:
        if only_name:
            return [i["value"] for i in self.site_list]
        return self.site_list


monitor_web_info = _MonitorWebInfo()

def _monitor_status() -> bool:
    return os.path.exists("/www/server/monitor/monitor") and \
        os.path.exists("/www/server/panel/plugin/monitor/monitor_main.py")


class MonitorWebData:
    _CONF_FILE = "/www/server/monitor/config/config.json"
    _DB_PATH = None
    try:
        tmp_data = json.loads(read_file(_CONF_FILE))
        if isinstance(tmp_data, dict):
            _DB_PATH = tmp_data["data_save_path"]
    except:
        pass

    @classmethod
    def set_cache(cls, key: str, value: Any):
        cache_dict = getattr(cls, "_cache_data", None)
        if cache_dict is None:
            cache_dict = {}
            setattr(cls, "_cache_data", cache_dict)

        cache_dict[key] = value

    @classmethod
    def get_cache(cls, key: str) -> Optional[Any]:
        cache_dict = getattr(cls, "_cache_data", dict())
        return cache_dict.get(key, None)


    def __init__(self, site_name: str):
        self.site_name = site_name
        self._time_start: Optional[datetime.datetime] = None
        self.now: datetime.datetime = datetime.datetime.now()

    def set_time(self, cycle: Union[int, float], cycle_unit: str = ""):
        if cycle_unit not in ("m", "h", ""):
            raise ValueError("cycle_unit must be m、h or empty")
        if not isinstance(cycle, (int, float)) or cycle < 0:
            raise ValueError("cycle must be int or float and cycle must be greater than 0")

        if cycle_unit in ("m", "h"):
            cycle_time = cycle * 60 if cycle_unit == "m" else cycle * 3600
            self._time_start = self.now - datetime.timedelta(seconds=cycle_time)
        elif cycle == 0:
            self._time_start = datetime.datetime(self.now.year, self.now.month, 1, 0, 0, 0)

        elif cycle > 1:
            self._time_start = datetime.datetime.fromtimestamp(int(cycle))

    def time(self) -> datetime.datetime:
        return self._time_start

    def _query(self, target_type: str="traffic") -> int:
        if not self._time_start:
            raise ValueError("time_range must be set")
        if  target_type not in ("traffic", "request"):
            raise ValueError("target_type must be traffic or request")

        db_file = "{}/{}/request_total.db".format(self._DB_PATH, self.site_name)
        if not os.path.exists(db_file):
            return 0

        cache_key = "{}_{}".format(self.site_name, int(self._time_start.timestamp()))
        cache_data = self.get_cache(cache_key)
        if isinstance(cache_data, dict):
            return cache_data[target_type]

        date = 10000 * self._time_start.year + 100 * self._time_start.month + self._time_start.day
        if self._time_start.hour == 0 and self._time_start.minute == 0:
            where = "date >= {}".format(date)
        elif self._time_start.minute == 0:
            where = "date > {} OR (date = {} AND hour >= {})".format(date, date, self._time_start.hour)
        else:
            where = "date > {} OR (date = {} AND hour > {}) OR (date = {} AND hour = {} AND minute >= {})".format(
                date, date, self._time_start.hour, date, self._time_start.hour, self._time_start.minute)


        field = "SUM(request) as request,SUM(sent_bytes) as sent_bytes"

        sql = db.Sql()
        sql._Sql__DB_FILE = db_file
        data = sql.table("request_total").where(where, tuple()).field(field).select()
        sql.close()
        if not isinstance(data, list) or not data:
            return 0

        res = {
            "request": 0 if data[0]["request"] is None else data[0]["request"],
            "traffic": 0 if data[0]["sent_bytes"] is None else data[0]["sent_bytes"]
        }
        self.set_cache(cache_key, res)
        return res[target_type]

    def query_traffic(self):
        return self._query("traffic")

    def query_request(self):
        return self._query("request")


class _ShowData:

    @staticmethod
    def show_traffic(traffic: int) -> str:
        if traffic < 1024:
            return "{:.1f}B".format(traffic)
        elif traffic < 1024 * 1024:
            return "{:.1f}KB".format(traffic / 1024)
        elif traffic < 1024 * 1024 * 1024:
            return "{:.1f}MB".format(traffic / 1024 / 1024)
        elif traffic < 1024 * 1024 * 1024 * 1024:
            return "{:.1f}GB".format(traffic / 1024 / 1024 / 1024)
        else:
            return "{:.1f}TB".format(traffic / 1024 / 1024 / 1024 / 1024)

    @staticmethod
    def show_request(request: int) -> str:
        if request < 1000:
            return "{}次".format(request)
        elif request < 1000 * 1000:
            return "{:.1f}千次".format(request / 1000)
        elif request < 1000 * 1000 * 1000:
            return "{:.1f}百万次".format(request / 1000 / 1000)
        else:
            return "{:.1f}亿次".format(request / 1000 / 1000 / 100)

    def trans_target_number(self, number: int, unit: str):
        if not isinstance(number, (int, float)) or number < 0:
            raise ValueError("number must be int or float and number must be greater than 0")

        if unit in ("c", "kc", "mc"):
            if unit == "c":
                _target_number = number
            elif unit == "kc":
                _target_number = number * 1000
            else:
                _target_number = number * 1000 * 1000

        elif unit in ("mb", "gb"):
            if unit == "mb":
                _target_number = number * 1024 * 1024
            else:
                _target_number = number * 1024 * 1024 * 1024
        else:
            raise ValueError("unit must be c、kc、mc、mb、gb")

        setattr(self, "_target_number", _target_number)
        return _target_number

    @property
    def target_number(self):
        return getattr(self, "_target_number", 0)


class MonitorTrafficAttackTask(BaseTask, _ShowData):
    def __init__(self):
        super().__init__()
        self.source_name = "monitor_traffic_attack"
        self.template_name = "[监控报表]网站流量异常告警"

        self.task_site_name = ""
        self.task_log_show = ""

    def filter_template(self, template: dict) -> Optional[dict]:
        if not _monitor_status():
            return None
        template["field"][0]["items"] = monitor_web_info()
        return template

    def get_keyword(self, task_data: dict) -> str:
        return "{}_{}{}_{}{}".format(
            task_data["site"], task_data["cycle"], task_data["cycle_unit"],
            task_data["traffic"], task_data["traffic_unit"]
        )

    def get_title(self, task_data: dict) -> str:
        return "网站[{}]流量异常告警(监控报表)".format(task_data["site"])

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        if not _monitor_status():
            return "监控报表未安装，无法设置规则"
        site = task_data.get("site", "")
        if site not in monitor_web_info(only_name=True):
            return "指定的网站不存在或未开启外网映射，无法获取流量数据，不可设置规则"
        task_data["interval"] = 60
        if not (isinstance(task_data.get('cycle', None), (int, float)) and task_data['cycle'] > 0):
            return "周期参数错误，不能设置小于等于0的数据"
        if task_data.get('cycle_unit', None) not in ("m", "h"):
            return "周期的单位参数错误，只能为小时或分钟"
        if not (isinstance(task_data.get('traffic', None), (int, float)) and task_data['traffic'] > 0):
            return "流量阈值参数错误，不能设置小于等于0的数据"
        if task_data.get('traffic_unit', None) not in ("mb", "gb"):
            return "流量阈值的单位参数错误，只能为MB或GB"
        set_module_logs("push", "monitor_traffic")
        return task_data

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        m = MonitorWebData(task_data["site"])
        m.set_time(task_data["cycle"], task_data["cycle_unit"])
        self.trans_target_number(task_data["traffic"], task_data["traffic_unit"])
        traffic = m.query_traffic()
        if traffic > self.target_number:
            s_list = [
                ">网站：" + task_data["site"],
                ">检查结果：自{}起的{}{}的流量达到{}，超过阈值{}".format(
                    m.time().strftime("%Y-%m-%d %H:%M:%S"),
                    task_data["cycle"],
                    "小时" if task_data["cycle_unit"] == "h" else "分钟",
                    self.show_traffic(traffic),
                    self.show_traffic(self.target_number)
                ),
                ">提示：请登录面板，尝试进行流量限制或在防火墙中进行流量过滤"
            ]
            self.task_site_name = task_data["site"]
            self.task_log_show = "近{}{}的流量达{}".format(
                task_data["cycle"],
                "小时" if task_data["cycle_unit"] == "h" else "分钟",
                self.show_traffic(self.target_number)
            )
            self.title = self.get_title(task_data)
            return {"msg_list": s_list}

        return None

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        if len(self.task_site_name) > 14:
            site_name = self.task_site_name[:11] + "..."
        else:
            site_name = self.task_site_name
        msg.thing_type = "{}流量异常告警".format(site_name)
        if len(self.task_log_show) > 20:
            msg.msg = self.task_log_show[:17] + "..."
        else:
            msg.msg = self.task_log_show

        return msg


class MonitorTrafficTotalTask(BaseTask, _ShowData):

    def __init__(self):
        super().__init__()
        self.source_name = "monitor_traffic_total"
        self.template_name = "[监控报表]网站流量限额提醒"

        self.task_site_name = ""
        self.task_log_show = ""

    def filter_template(self, template: dict) -> Optional[dict]:
        if not _monitor_status():
            return None
        template["field"][0]["items"] = monitor_web_info()
        return template

    def get_keyword(self, task_data: dict) -> str:
        return "{}_{}_{}{}".format(
            task_data["site"], task_data["cycle"],task_data["traffic"], task_data["traffic_unit"]
        )

    def get_title(self, task_data: dict) -> str:
        return "网站[{}]流量限额提醒(监控报表)".format(task_data["site"])

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        if not _monitor_status():
            return "监控报表未安装，无法设置规则"
        task_data["interval"] = 60
        site = task_data.get("site", "")
        if site not in monitor_web_info(only_name=True):
            return "指定的网站不存在或未开启外网映射，无法获取流量数据，不可设置规则"
        if not (isinstance(task_data.get('cycle', None), (int, float)) and task_data['cycle'] >= 0):
            return "周期参数错误，不能设置小于0的数据"
        if task_data['cycle'] !=0 and task_data['cycle'] < 1709168485:
            return "周期参数错误，时间错误"
        if task_data['cycle'] > 1709168485 * 1000:
            task_data['cycle'] = task_data['cycle'] // 1000
        if not (isinstance(task_data.get('traffic', None), (int, float)) and task_data['traffic'] > 0):
            return "流量阈值参数错误，不能设置小于等于0的数据"
        if task_data.get('traffic_unit', None) not in ("mb", "gb"):
            return "流量阈值的单位参数错误，只能为MB或GB"
        set_module_logs("push", "monitor_traffic")
        return task_data

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        m = MonitorWebData(task_data["site"])
        m.set_time(task_data["cycle"])
        self.trans_target_number(task_data["traffic"], task_data["traffic_unit"])
        traffic = m.query_traffic()
        if traffic > self.target_number:
            if task_data["cycle"] == 0:
                time_show = "本月({})".format(m.time().strftime("%Y-%m"))
                time_show_wx = "本月"
            else:
                time_show = "自{}日起累计".format(m.time().strftime("%Y-%m-%d"))
                time_show_wx = "自{}-{}日".format(m.time().month, m.time().day)
            s_list = [
                ">网站：" + task_data["site"],
                ">检查结果：{}的流量达到{}，超过阈值{}".format(
                    time_show,
                    self.show_traffic(traffic),
                    self.show_traffic(self.target_number)
                ),
                ">提示：请登录面板，查看资源使用情况，并尝试进行限制"
            ]
            self.task_site_name = task_data["site"]
            self.task_log_show = time_show_wx + "流量达" + self.show_traffic(self.target_number)
            self.title = self.get_title(task_data)
            return {"msg_list": s_list}

        return None

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        if len(self.task_site_name) > 14:
            site_name = self.task_site_name[:11] + "..."
        else:
            site_name = self.task_site_name
        msg.thing_type = "{}流量限额提醒".format(site_name)
        if len(self.task_log_show) > 20:
            msg.msg = self.task_log_show[:17] + "..."
        else:
            msg.msg = self.task_log_show

        return msg


class MonitorHttpFloodTask(BaseTask, _ShowData):

    def filter_template(self, template: dict) -> Optional[dict]:
        if not _monitor_status():
            return None
        template["field"][0]["items"] = monitor_web_info()
        return template

    def __init__(self):
        super().__init__()
        self.source_name = "monitor_http_flood"
        self.template_name = "[监控报表]网站请求异常告警"

        self.task_site_name = ""
        self.task_log_show = ""

    def get_keyword(self, task_data: dict) -> str:
        return "{}_{}{}_{}{}".format(
            task_data["site"], task_data["cycle"], task_data["cycle_unit"],
            task_data["request"], task_data["request_unit"]
        )

    def get_title(self, task_data: dict) -> str:
        return "网站[{}]请求异常告警(监控报表)".format(task_data["site"])

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        if not _monitor_status():
            return "监控报表未安装，无法设置规则"
        task_data["interval"] = 60
        site = task_data.get("site", "")
        if task_data.get('cycle_unit', None) not in ("m", "h"):
            return "周期的单位参数错误，只能为小时或分钟"
        if not (isinstance(task_data.get('cycle', None), (int, float)) and task_data['cycle'] > 0):
            return "周期参数错误，不能设置小于等于0的数据"
        if site not in monitor_web_info(only_name=True):
            return "指定的网站不存在或未开启外网映射，无法获取流量数据，不可设置规则"
        if not (isinstance(task_data.get('request', None), (int, float)) and task_data['request'] > 0):
            return "流量阈值参数错误，不能设置小于等于0的数据"
        if task_data.get('request_unit', None) not in ("c", "kc", "mc"):
            return "请求阈值参数错误，只能为”次“、”千次“、“百万次”"
        set_module_logs("push", "monitor_traffic")
        return task_data

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        m = MonitorWebData(task_data["site"])
        m.set_time(task_data["cycle"], task_data["cycle_unit"])
        self.trans_target_number(task_data["request"], task_data["request_unit"])
        request = m.query_request()
        if request > self.target_number:
            s_list = [
                ">网站：" + task_data["site"],
                ">检查结果：自{}起的{}{}的请求数达到{}，超过阈值{}".format(
                    m.time().strftime("%Y-%m-%d %H:%M:%S"),
                    task_data["cycle"],
                    "小时" if task_data["cycle_unit"] == "h" else "分钟",
                    self.show_request(request),
                    self.show_request(self.target_number)
                ),
                ">提示：请登录面板，尝试进行限制或在防火墙中进行流量过滤"
            ]
            self.task_site_name = task_data["site"]
            self.task_log_show = "近{}{}的请求数达{}".format(
                task_data["cycle"],
                "小时" if task_data["cycle_unit"] == "h" else "分钟",
                self.show_request(self.target_number)
            )
            self.title = self.get_title(task_data)
            return {"msg_list": s_list}

        return None

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        if len(self.task_site_name) > 14:
            site_name = self.task_site_name[:14]
        else:
            site_name = self.task_site_name
        msg.thing_type = "{}请求异常告警".format(site_name)
        if len(self.task_log_show) > 20:
            msg.msg = self.task_log_show[:20]
        else:
            msg.msg = self.task_log_show

        return msg


class ViewMsgFormat(BaseTaskViewMsg):

    def get_msg(self, task: dict) -> str:
        task_data = task["task_data"]
        if task["template_id"] == "130":
            return "网站【{}】近{}{}的流量消耗达{}时，发出告警信息".format(
                task_data['site'], task_data['cycle'], "分钟" if task_data['cycle_unit'] == 'm' else '小时',
                _ShowData.show_traffic(_ShowData().trans_target_number(task_data['traffic'], task_data['traffic_unit']))
            )
        if task["template_id"] == "132":
            return "网站【{}】近{}{}的请求数达{}时，发出告警信息".format(
                task_data['site'], task_data['cycle'], "分钟" if task_data['cycle_unit'] == 'm' else '小时',
                _ShowData.show_request(_ShowData().trans_target_number(task_data['request'], task_data['request_unit']))
            )
        if task["template_id"] == "131":
            if task_data["cycle"] == 0:
                d = datetime.date.today().replace(day=1)
                time_show = "本月({})累计".format(d.strftime("%Y-%m"))
            else:
                d = datetime.datetime.fromtimestamp(task_data["cycle"])
                time_show = "自{}日起累计".format(d.strftime("%Y-%m-%d"))
            return "网站【{}】{}的流量消耗达{}时，发出告警信息".format(
                task_data['site'], time_show,
                _ShowData.show_traffic(_ShowData().trans_target_number(task_data['traffic'], task_data['traffic_unit']))
            )
        return ""


MonitorHttpFloodTask.VIEW_MSG = MonitorTrafficTotalTask.VIEW_MSG = MonitorTrafficAttackTask.VIEW_MSG = ViewMsgFormat