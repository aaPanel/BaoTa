import json
import os
import sys
import time
from typing import Tuple, Union, Optional, Dict

from .mods import PUSH_DATA_PATH, TaskTemplateConfig, TaskConfig
import traceback
from .base_task import BaseTask, BaseTaskViewMsg
from .site_push import web_info_data
from .util import read_file, DB, GET_CLASS, write_file, debug_log, to_dict_obj, random_string, get_webserver


class WEBLogTask(BaseTask):
    CROM_CONFIG_FILE = "/www/server/panel/data/cron_task_analysis.json"

    def __init__(self):
        super().__init__()
        self.source_name: str = 'web_log_scan'
        self.title: str = 'Web日志扫描告警'  # 这个是告警任务的标题(根据实际情况改变)
        self.template_name: str = 'Web日志扫描告警'  # 这个告警模板的标题(不会改变)

    @staticmethod
    def get_site_log_file(site_name: str) -> str:
        if "/www/server/panel/class" not in sys.path:
            sys.path.insert(0, "/www/server/panel/class")

        from logsModel.siteModel import main as SiteModel

        res = SiteModel().get_site_log_file(to_dict_obj({"siteName": site_name}))
        if "log_file" in res and res["log_file"]:
            return res["log_file"]
        return ""

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        """
        检查设置的告警参数（是否合理）
        @param task_data: 传入的告警参数，提前会经过默认值处理（即没有的字段添加默认值）
        @return: 当检查无误时，返回一个 dict 当做后续的添加和修改的数据，
                当检查有误时， 直接返回错误信息的字符串
        """
        if "interval" in task_data:
            task_data.pop("interval")
        site_name = task_data.get("site_name", "")
        if not site_name:
            return "请配置站点名称"
        items, _ = web_info_data(all_type=True)
        for item in items:
            if item["value"] == site_name:
                break
        else:
            return "站点不存在"
        task_data["log_path"] = self.get_site_log_file(site_name)
        if not os.path.exists(task_data["log_path"]):
            return "站点日志文件不存在"
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        """
        返回一个关键字，用于后续查询或执行任务时使用， 例如：防篡改告警，可以根据其规则id生成一个关键字，
        后续通过规则id和来源tamper 查询并使用
        @param task_data: 通过check_args后生成的告警参数字典
        @return: 返回一个关键词字符串
        """
        return "web_log_scan_{}".format(task_data["log_path"])

    def get_title(self, task_data: dict) -> str:
        """
        返回一个标题
        @param task_data: 通过check_args后生成的告警参数字典
        @return: 返回一个关键词字符串
        """
        return "网站【{}】Web日志扫描提醒".format(task_data["site_name"])

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        """
        判断这个任务是否需要返送
        @param task_id: 任务id
        @param task_data: 任务的告警参数
        @return: 如果触发了告警，返回一个dict的原文，作为告警信息，否则应当返回None表示未触发
                返回之中应当包含一个 msg_list 的键（值为List[str]类型），将主要的信息返回
                用于以下信息的自动序列化包含[dingding, feishu, mail, weixin, web_hook]
                短信和微信公众号由于长度问题，必须每个任务手动实现
        """
        return None

    def filter_template(self, template: dict) -> Optional[dict]:
        """
        过滤 和 更改模板中的信息, 返回空表是当前无法设置该任务
        @param template: 任务的模板信息
        @return:
        """
        items, _ = web_info_data(all_type=True)
        template["field"][0]["items"].extend(items)
        return template

    @classmethod
    def all_web_log_scan(cls) -> Dict[str, str]:
        res = {}
        for i in TaskConfig().get_by_source("web_log_scan"):
            if i["status"] is True:
                if "log_path" not in i["task_data"]:
                    i["task_data"]["log_path"] = cls.get_site_log_file(i["task_data"]["site_name"])
                res[i["task_data"]["log_path"]] = i["task_data"]["site_name"]
        return res

    @classmethod
    def set_path_to_config(cls, path: str, status: bool):
        try:
            conf = json.loads(read_file(cls.CROM_CONFIG_FILE))
        except:
            conf = {}

        if path in conf and not status:  # 移除配置
            conf.pop(path)
        elif path not in conf and status:  # 新增配置
            conf[path] = {"status": 1, "cycle": '1', "path": path}

        if len(conf) > 1:
            cls.add_crontab()
        else:
            cls.remove_crontab()

        write_file(cls.CROM_CONFIG_FILE, json.dumps(conf))

    def task_config_create_hook(self, task: dict) -> None:
        self.set_path_to_config(task["task_data"]["log_path"], task["status"])

    def task_config_update_hook(self, task: dict) -> None:
        self.set_path_to_config(task["task_data"]["log_path"], task["status"])

    def task_config_remove_hook(self, task: dict) -> None:
        self.set_path_to_config(task["task_data"]["log_path"], False)

    @staticmethod
    def add_crontab():
        """
        @name 构造日志切割任务
        """
        cron_name = '[勿删]web日志定期检测服务'
        if not DB('crontab').where('name=?', (cron_name,)).count():
            cmd = '{} /www/server/panel/script/cron_log_analysis.py'.format(
                "/www/server/panel/pyenv/bin/python3.7"
            )
            args = {
                "name": cron_name,
                "type": 'day',
                "where1": '',
                "hour": '11',
                "minute": '50',
                "sName": "",
                "sType": 'toShell',
                "notice": '0',
                "notice_channel": '',
                "save": '',
                "save_local": '1',
                "backupTo": '',
                "sBody": cmd,
                "urladdress": ''
            }
            if "/www/server/panel/class" not in sys.path:
                sys.path.insert(0, "/www/server/panel/class")
            import crontab
            res = crontab.crontab().AddCrontab(args)
            if res and "id" in res.keys():
                return True
            return False
        return True

    @staticmethod
    def remove_crontab():
        """
        @name 删除项目定时任务
        @auther hezhihong<2022-10-31>
        @return
        """
        try:
            cron_name = '[勿删]web日志定期检测服务'
            if "/www/server/panel/class" not in sys.path:
                sys.path.insert(0, "/www/server/panel/class")
            import crontab
            p = crontab.crontab()
            cron_id = DB('crontab').where("name=?", (cron_name,)).getField('id')
            args = {"id": cron_id}
            p.DelCrontab(args)
            return True
        except:
            return False


def load_web_log_template():
    from .mods import load_task_template_by_config
    load_task_template_by_config(
        [{
            "id": "110",
            "ver": "1",
            "used": True,
            "source": "web_log_scan",
            "title": "Web日志扫描告警",
            "load_cls": {
                "load_type": "path",
                "cls_path": "mod.base.push_mod.web_log_push",
                "name": "WEBLogTask"
            },
            "template": {
                "field": [
                    {
                        "attr": "site_name",
                        "name": "站点名称",
                        "type": "select",
                        "default": "",
                        "unit": "",
                        "suffix": "",
                        "items": []
                    }

                ],
                "sorted": [
                    [
                        "site_name"
                    ],
                ],
            },
            "default": {},
            "advanced_default": {},
            "send_type_list": [
                "dingding",
                "feishu",
                "mail",
                "weixin",
                "webhook"
            ],
            "unique": False,
            "tags":["site"],
            "description": "定期扫描网站的Nginx或Apache访问日志，检查潜在的风险，（如：SQL 注入、XSS 攻击、命令执行等）并通知管理人员。"
        }]
    )


class ViewMsgFormat(BaseTaskViewMsg):

    def __init__(self):
        self.web = get_webserver()

    def get_msg(self, task: dict) -> Optional[str]:
        if task["template_id"] == "110":
            return "定期扫描网站【{}】的{}访问日志并报告PHP攻击、恶意扫描、SQL注入、XSS攻击的情况".format(task["task_data"]["site_name"], self.web)
        return None


WEBLogTask.VIEW_MSG = ViewMsgFormat