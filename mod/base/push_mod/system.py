import os
import time
import traceback
from typing import Optional, List, Tuple, Dict, Type, Any, Union
import datetime
from threading import Thread

from .base_task import BaseTask
from .mods import TaskTemplateConfig, TaskConfig, TaskRecordConfig, SenderConfig
from .send_tool import sms_msg_normalize
from .tool import load_task_cls_by_path, load_task_cls_by_function, T_CLS, load_task_cls
from .util import get_server_ip, get_network_ip, format_date, get_config_value
from .compatible import rsync_compatible


WAIT_TASK_LIST: List[Thread] = []


class PushSystem:

    def __init__(self):
        self.task_cls_cache: Dict[str, Type[T_CLS]] = {}
        self._today_zero: Optional[datetime.datetime] = None
        self._sender_type_class: Optional[dict] = {}
        self.sd_cfg = SenderConfig()

    def sender_cls(self, sender_type: str):
        if not self._sender_type_class:
            from mod.base.msg import WeiXinMsg, MailMsg, WebHookMsg, FeiShuMsg, DingDingMsg, SMSMsg, WeChatAccountMsg
            self._sender_type_class = {
                "weixin": WeiXinMsg,
                "mail": MailMsg,
                "webhook": WebHookMsg,
                "feishu": FeiShuMsg,
                "dingding": DingDingMsg,
                "sms": SMSMsg,
                "wx_account": WeChatAccountMsg,
            }
        return self._sender_type_class[sender_type]

    def get_sms_sender_id(self) -> Optional[str]:
        for sender in self.sd_cfg.config:
            if sender["sender_type"] == "sms":
                return sender["id"]
        return None

    def can_run_task_list(self) -> Tuple[List[dict], Dict[int, dict]]:
        import datetime
        result = []
        result_template = {}
        task_template_ids = set()
        for task in TaskConfig().config:
            if not task["status"]:
                continue
            task_template_ids.add(task['template_id'])
            # 间隔检测时间未到跳过
            if "interval" in task["task_data"] and isinstance(task["task_data"]["interval"], int):
                if "type" in task["task_data"] and task["task_data"]['type'] == "site_ssl":
                    sms_id = self.get_sms_sender_id()  # 改为使用类名来调用静态方法
                    if sms_id and sms_id in task['sender']:
                        # 获取当前时间
                        current_time = datetime.datetime.now()
                        # 检查当前时间是否在9点到12点之间
                        if not (9 <= current_time.hour < 12):
                            continue
                if time.time() < task["last_check"] + task["task_data"]["interval"]:
                    continue
            result.append(task)

        for template in TaskTemplateConfig().config:
            if template["id"] not in task_template_ids:
                continue
            result_template[template['id']] = template

        return result, result_template

    def get_task_object(self, template_id, load_cls_data: dict) -> Optional[BaseTask]:
        if template_id in self.task_cls_cache:
            return self.task_cls_cache[template_id]()

        cls = load_task_cls(load_cls_data)

        if not cls:
            return None
        self.task_cls_cache[template_id] = cls
        return cls()

    def run(self):
        rsync_compatible()
        task_list, task_template = self.can_run_task_list()
        for t in task_list:
            if t["template_id"] not in task_template:
                continue
            template = task_template[t["template_id"]]
            if not template["used"]:
                continue
            try:
                _PushRunner(t, template, self)()
            except:
                print("任务执行失败", t["id"], template["title"], t["task_data"])
                traceback.print_exc()
                continue

        global WAIT_TASK_LIST
        if WAIT_TASK_LIST:  # 有任务启用子线程的，要等到这个线程结束，再结束主线程
            for i in WAIT_TASK_LIST:
                i.join()

    def get_today_zero(self) -> datetime.datetime:
        if self._today_zero is None:
            t = datetime.datetime.today()
            t_zero = datetime.datetime.combine(t, datetime.time.min)
            self._today_zero = t_zero
        return self._today_zero


class _PushRunner:

    def __init__(self, task: dict, template: dict, push_system: PushSystem, custom_push_data: Optional[dict] = None):
        self._public_push_data: Optional[dict] = None
        self.result: dict = {
            "do_send": False,
            "stop_msg": "",
            "push_data": {},
            "check_res": False,
            "check_stop_on": "",
            "send_data": {},
        }  # 记录结果
        self.change_fields = set()  # 记录task变化值
        self.task_obj: Optional[BaseTask] = None
        self.task = task
        self.template = template
        self.push_system = push_system
        self._add_hook_msg: Optional[str] = None  # 记录前置钩子处理后的追加信息
        self.custom_push_data = custom_push_data

        self.tr_cfg = TaskRecordConfig(task["id"])
        self.is_number_rule_by_func = False  # 记录这个任务是否使用自定义的次数检测， 如果是，就不需要做次数更新

    def save_result(self):

        t = TaskConfig()
        tmp = t.get_by_id(self.task["id"])
        if tmp:
            for f in self.change_fields:
                tmp[f] = self.task[f]

            if self.result["do_send"]:
                tmp["last_send"] = int(time.time())
            tmp["last_check"] = int(time.time())

            t.save_config()

        if self.result["push_data"]:
            result_data = self.result.copy()
            self.tr_cfg.config.append(
                {
                    "id": self.tr_cfg.nwe_id(),
                    "template_id": self.template["id"],
                    "task_id": self.task["id"],
                    "do_send": result_data.pop("do_send"),
                    "send_data": result_data.pop("push_data"),
                    "result": result_data,
                    "create_time": int(time.time()),
                }
            )
            self.tr_cfg.save_config()

    @property
    def public_push_data(self) -> dict:
        if self._public_push_data is None:
            self._public_push_data = {
                'ip': get_server_ip(),
                'local_ip': get_network_ip(),
                'server_name': get_config_value('title')
            }
        data = self._public_push_data.copy()
        data['time'] = format_date()
        data['timestamp'] = int(time.time())
        return data

    def __call__(self):
        # print("=====================\ntask:", self.task)
        self.run()
        self.save_result()
        if self.task_obj:
            self.task_obj.task_run_end_hook(self.result)
        # print("result", self.result, "\n======================")
        return self.result_to_return()

    def result_to_return(self) -> dict:
        return self.result

    def run(self):
        self.task_obj = self.push_system.get_task_object(self.template["id"], self.template["load_cls"])

        if not self.task_obj or not isinstance(self.task_obj, BaseTask):
            self.result["stop_msg"] = "任务类加载失败"
            return

        if self.custom_push_data is None:
            push_data = self.task_obj.get_push_data(self.task["id"], self.task["task_data"])
            if not push_data:
                return
        else:
            push_data = self.custom_push_data

        self.result["push_data"] = push_data
        # 执行前置钩子
        if self.task["pre_hook"] and "hook_type" in self.task["pre_hook"]:
            if not self.run_hook(self.task["pre_hook"], "pre_hook"):
                return

        # 执行时间规则判断
        if not self.run_time_rule(self.task["time_rule"]):
            return

        # 执行发送次数规则判断
        if not self.number_rule(self.task["number_rule"]):
            return

        # 执行发送信息
        self.send_message(push_data)
        self.change_fields.add("number_data")
        if "day_num" not in self.task["number_data"]:
            self.task["number_data"]["day_num"] = 0

        if "total" not in self.task["number_data"]:
            self.task["number_data"]["total"] = 0

        self.task["number_data"]["day_num"] += 1
        self.task["number_data"]["total"] += 1
        self.task["number_data"]["time"] = int(time.time())

        # 执行后置钩子
        if self.task["after_hook"] and "hook_type" in self.task["after_hook"]:
            self.run_hook(self.task["after_hook"], "after_hook")

    # todo: 下个版本实现一些自定义的hook函数，同时实现用户脚本的hook记录在 self.result 最后统一储存
    def run_hook(self, hook_data: dict, hook_name: str) -> bool:
        """
        执行hook操作，并返回是否继续执行, 并将hook的执行结果记录
        @param hook_name: 钩子的名称，如：after_hook， pre_hook
        @param hook_data: 执行的内容
        @return:
        """
        return True

    def run_time_rule(self, time_rule: dict) -> bool:
        if "send_interval" in time_rule and time_rule["send_interval"] > 0:
            if self.task["last_send"] + time_rule["send_interval"] > time.time():
                self.result['stop_msg'] = '小于最小发送时间，不进行发送'
                self.result['check_stop_on'] = "time_rule_send_interval"
                return False

        time_range = time_rule.get("time_range", None)
        if time_range and isinstance(time_range, list) and len(time_range) == 2:
            t_zero = self.push_system.get_today_zero()
            start_time = t_zero + datetime.timedelta(seconds=time_range[0])
            end_time = t_zero + datetime.timedelta(seconds=time_range[1])
            if not start_time < datetime.datetime.now() < end_time:
                self.result['stop_msg'] = '不在可发送告警的时间范围之内'
                self.result['check_stop_on'] = "time_rule_time_range"
                return False
        return True

    def number_rule(self, number_rule: dict) -> bool:
        number_data = self.task.get("number_data", {})
        # 判断通过 自定义函数的方式确认是否达到发送次数
        if "get_by_func" in number_rule and isinstance(number_rule["get_by_func"], str):
            f = getattr(self.task_obj, number_rule["get_by_func"], None)
            if f is not None and callable(f):
                res = f(self.task["id"], self.task["task_data"], number_data, self.result["push_data"])
                if isinstance(res, str):
                    self.result['stop_msg'] = res
                    self.result['check_stop_on'] = "number_rule_get_by_func"
                    return False

            # 只要是走了使用函数检查的，不再处理默认情况 change_fields 中不添加 number_data
            return True

        if "day_num" in number_rule and isinstance(number_rule["day_num"], int) and number_rule["day_num"] > 0:
            record_time = number_data.get("time", 0)
            if record_time < self.push_system.get_today_zero().timestamp():  # 昨日触发
                self.task["number_data"]["day_num"] = record_num = 0
                self.task["number_data"]["time"] = time.time()
                self.change_fields.add("number_data")
            else:
                record_num = self.task["number_data"].get("day_num")
            if record_num >= number_rule["day_num"]:
                self.result['stop_msg'] = "超过每日限制次数:{}".format(number_rule["day_num"])
                self.result['check_stop_on'] = "number_rule_day_num"
                return False

        if "total" in number_rule and isinstance(number_rule["total"], int) and number_rule["total"] > 0:
            record_total = number_data.get("total", 0)
            if record_total >= number_rule["total"]:
                self.result['stop_msg'] = "超过最大限制次数:{}".format(number_rule["total"])
                self.result['check_stop_on'] = "number_rule_total"
                return False

        return True

    def send_message(self, push_data: dict):
        self.result["do_send"] = True
        self.result["push_data"] = push_data
        wx_account = []
        for sender_id in self.task["sender"]:
            conf = self.push_system.sd_cfg.get_by_id(sender_id)
            if conf is None:
                continue
            if not conf["used"]:
                self.result["send_data"][sender_id] = "告警通道{}已关闭，跳过发送".format(conf["data"].get("title"))
                continue
            sd_cls = self.push_system.sender_cls(conf["sender_type"])
            if conf["sender_type"] == "weixin":
                res = sd_cls(conf).send_msg(
                    self.task_obj.to_weixin_msg(push_data, self.public_push_data),
                    self.task_obj.title
                )

            elif conf["sender_type"] == "mail":
                res = sd_cls(conf).send_msg(
                    self.task_obj.to_mail_msg(push_data, self.public_push_data),
                    self.task_obj.title
                )

            elif conf["sender_type"] == "webhook":
                res = sd_cls(conf).send_msg(
                    self.task_obj.to_web_hook_msg(push_data, self.public_push_data),
                    self.task_obj.title,
                    self.task_obj.template_name
                )

            elif conf["sender_type"] == "feishu":
                res = sd_cls(conf).send_msg(
                    self.task_obj.to_feishu_msg(push_data, self.public_push_data),
                    self.task_obj.title
                )
            elif conf["sender_type"] == "dingding":
                res = sd_cls(conf).send_msg(
                    self.task_obj.to_dingding_msg(push_data, self.public_push_data),
                    self.task_obj.title
                )
            elif conf["sender_type"] == "sms":
                try:
                    sm_type, sm_args = self.task_obj.to_sms_msg(push_data, self.public_push_data)
                    if not sm_type or not sm_args:
                        continue
                    sm_args = sms_msg_normalize(sm_args)
                    res = sd_cls(conf).send_msg(sm_type, sm_args)
                except NotImplementedError:
                    res = "暂不支持该短信通道"

            elif conf["sender_type"] == "wx_account":
                wx_account.append(conf)
                continue
            else:
                continue
            if isinstance(res, str) and res.find("Traceback") != -1:
                self.result["send_data"][sender_id] = "执行信息发送过程中报错了, 未发送成功"
            if isinstance(res, str):
                self.result["send_data"][sender_id] = res
            else:
                self.result["send_data"][sender_id] = 1

        if len(wx_account) > 0:
            sd_cls = self.push_system.sender_cls("wx_account")
            try:
                wx_account_msg = self.task_obj.to_wx_account_msg(push_data, self.public_push_data)
            except NotImplementedError:
                res = "暂不支持该微信公众号发通道"
            else:
                res = sd_cls(*wx_account).send_msg(wx_account_msg)
            for i in wx_account:
                if isinstance(res, str):
                    self.result["send_data"][i["id"]] = res
                else:
                    self.result["send_data"][i["id"]] = 1


def push_by_task_keyword(source: str, keyword: str, push_data: Optional[dict] = None) -> Union[str, dict]:
    """
    通过关键字查询告警任务，并发送信息
    @param push_data:
    @param source:
    @type keyword:
    @return:
    """
    push_system = PushSystem()
    target_task = None
    for i in TaskConfig().config:
        if i["source"] == source and i["keyword"] == keyword:
            target_task = i
            break
    if not target_task:
        return "未查找到该任务"

    target_template = TaskTemplateConfig().get_by_id(target_task["template_id"])
    if not target_template["used"]:
        return "该任务类型已被禁止使用"
    if not target_task['status']:
        return "该任务已停止"

    return _PushRunner(target_task, target_template, push_system, push_data)()


def push_by_task_id(task_id: str, push_data: Optional[dict] = None):
    """
    通过任务id触发告警 并 发送信息
    @param push_data:
    @param task_id:
    @return:
    """
    push_system = PushSystem()
    target_task = TaskConfig().get_by_id(task_id)
    if not target_task:
        return "未查找到该任务"

    target_template = TaskTemplateConfig().get_by_id(target_task["template_id"])
    if not target_template["used"]:
        return "该任务类型已被禁止使用"
    if not target_task['status']:
        return "该任务已停止"

    return _PushRunner(target_task, target_template, push_system, push_data)()


def get_push_public_data():
    data = {
        'ip': get_server_ip(),
        'local_ip': get_network_ip(),
        'server_name': get_config_value('title'),
        'time': format_date(),
        'timestamp': int(time.time())}

    return data

