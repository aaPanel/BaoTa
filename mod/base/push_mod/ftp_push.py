import json
import os
import sys
import time
from typing import Tuple, Union, Optional, Dict, List

from .mods import PUSH_DATA_PATH, TaskTemplateConfig, TaskConfig
import traceback
from .base_task import BaseTask, BaseTaskViewMsg
from .util import read_file, DB, GET_CLASS, write_file, debug_log, to_dict_obj, random_string


class FTPLogTask(BaseTask):

    def __init__(self):
        super().__init__()
        self.source_name: str = 'ftp_log'
        self.title: str = 'FTP日志扫描告警'  # 这个是告警任务的标题(根据实际情况改变)
        self.template_name: str = 'FTP日志扫描告警'  # 这个告警模板的标题(不会改变)

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        """
        检查设置的告警参数（是否合理）
        @param task_data: 传入的告警参数，提前会经过默认值处理（即没有的字段添加默认值）
        @return: 当检查无误时，返回一个 dict 当做后续的添加和修改的数据，
                当检查有误时， 直接返回错误信息的字符串
        """
        all_type = ("login_error", "area", "upload_shell", "time", "anonymous")
        if "task_type" not in task_data:
            task_data["task_type"] = all_type

        for i in task_data["task_type"]:
            if i not in all_type:
                return "任务类型错误"
        task_data["interval"] = 60 * 60 * 24
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        """
        返回一个关键字，用于后续查询或执行任务时使用， 例如：防篡改告警，可以根据其规则id生成一个关键字，
        后续通过规则id和来源tamper 查询并使用
        @param task_data: 通过check_args后生成的告警参数字典
        @return: 返回一个关键词字符串
        """
        return "ftp_log"

    def get_title(self, task_data: dict) -> str:
        """
        返回一个标题
        @param task_data: 通过check_args后生成的告警参数字典
        @return: 返回一个关键词字符串
        """
        if self.title:
            return self.title
        return self.template_name

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
        status, data = self._get_ftp_log_analysis(task_data)
        if not status:
            return None
        if not data:
            return None
        s_list = [">通知类型：FTP日志扫描告警"]
        for k, v in data.items():
            s_list.append(">ip地址：{}存在{}".format(k, v['type']))

        return {"msg_list": s_list}

    @staticmethod
    def _get_ftp_log_analysis(task_data: dict):
        try:
            import PluginLoader
            args = GET_CLASS()
            args.model_index = "logs"  # 模块名
            args.search = json.dumps(task_data["task_type"])
            args.username = "[]"
            args.day = 1
            data = PluginLoader.module_run("ftp", "log_analysis", args)
            # print(data)
            if 'status' in data.keys():
                return False, ''
            return True, data
        except:
            return False, ''

    def filter_template(self, template: dict) -> Optional[dict]:
        """
        过滤 和 更改模板中的信息, 返回空表是当前无法设置该任务
        @param template: 任务的模板信息
        @return:
        """
        return template

    @staticmethod
    def set_ftp_log_task(status: bool, task_type: List[str], channel: List[str]):
        from .manager import PushManager
        PushManager().set_task_conf_data({
            "template_id": "101",
            "task_data": {
                "status": status,
                "sender": channel,
                "task_data": {
                    "task_type": task_type,
                },
                "number_rule": {
                    "day_num": 1
                }
            }
        })

    # def task_config_create_hook(self, task: dict) -> Optional[str]:
    #     task["last_check"] = time.time()
    #     return None
    #
    # def task_config_update_hook(self, task: dict) -> Optional[str]:
    #     task["last_check"] = time.time()
    #     return None


class FTPUserTask(BaseTask):
    CONFIG_PATH = '/www/server/panel/data/ftp_push_config.json'

    def __init__(self):
        super().__init__()
        self.source_name: str = 'ftp_user'
        self.title: str = 'FTP用户密码到期提醒'  # 这个是告警任务的标题(根据实际情况改变)
        self.template_name: str = 'FTP用户密码到期提醒'

        self.push_keys = []

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        task_data["interval"] = 60 * 60 * 24
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return "ftp_user"

    def get_title(self, task_data: dict) -> str:
        if self.title:
            return self.title
        return self.template_name

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        if "/www/server/panel/class" not in sys.path:
            sys.path.insert(0, "/www/server/panel/class")

        try:
            import ftp
            ftp_obj = ftp.ftp()
            end_time_data = self.get_endtime_config()
            ftp_user = self.ftp_user()
            msg_list = [
                ">通知类型：FTP用户密码到期提醒"
            ]
            print(end_time_data)
            for ftp_id, (end_time, action) in end_time_data.items():
                if ftp_id not in ftp_user:
                    continue

                if int(end_time) < time.time():
                    if action == 1:
                        msg_list.append(">用户：{}密码已到期".format(ftp_user[ftp_id]))
                        self.push_keys.append(ftp_id)

                    elif action == 2:
                        res = ftp_obj.SetStatus(to_dict_obj({'id': ftp_id, 'username': ftp_user[ftp_id], 'status': 0}))
                        if res["status"]:
                            msg_list.append(">用户：{}密码已到期，【已停止】请及时处理！".format(ftp_user[ftp_id]))
                        else:
                            msg_list.append(">用户：{}密码已到期，【停止失败】请及时处理！".format(ftp_user[ftp_id]))
                        self.push_keys.append(ftp_id)

                    elif action == 3:
                        new_pwd = random_string(12)
                        res = ftp_obj.SetUserPassword(
                            to_dict_obj({'id': ftp_id, 'ftp_username': ftp_user[ftp_id], 'new_password': new_pwd})
                        )
                        if res["status"]:
                            msg_list.append(">用户：{}密码已到期，【已修改】新密码为：{}".format(ftp_user[ftp_id], new_pwd))
                        else:
                            msg_list.append(">用户：{}密码已到期，【修改失败】请及时处理！".format(ftp_user[ftp_id]))
                        self.push_keys.append(ftp_id)
        except:
            print("ftp_user push error")
            traceback.print_exc()
            return None

        if len(msg_list) == 1:
            return None
        return {"msg_list": msg_list}

    @staticmethod
    def ftp_user():
        ftp_user = DB("ftps").select()
        data = {}
        for i in ftp_user:
            data[i["id"]] = i["name"]
        return data

    @classmethod
    def get_endtime_config(cls) -> Dict[int, Tuple[int, int]]:
        """
        获取ftp用户到期时间
        :return: key: id values (到期时间，处理方式)
        """
        data = json.loads(read_file(cls.CONFIG_PATH))
        content = {}
        for action, i in data.items():
            if action == 'channel' or action == '0':
                continue
            for j in i:
                if j["is_push"]:
                    continue
                content[j['id']] = (int(j['end_time']), int(action))
        return content

    def filter_template(self, template: dict) -> Optional[dict]:
        """
        过滤 和 更改模板中的信息, 返回空表是当前无法设置该任务
        @param template: 任务的模板信息
        @return:
        """
        return template

    def task_run_end_hook(self, res: dict) -> None:
        if not res["do_send"]:
            return
        try:
            data = json.loads(read_file(self.CONFIG_PATH))
            for action, data_list in data.items():
                if action == 'channel':
                    continue
                for j in data_list:
                    if j['id'] in self.push_keys:
                        j['is_push'] = True
            write_file(self.CONFIG_PATH, json.dumps(data))
        except:
            pass

    def task_config_update_hook(self, task: dict) -> None:
        if task["sender"]:
            try:
                data = json.loads(read_file(self.CONFIG_PATH))
                data["channel"] = ",".join(task["sender"])
                write_file(self.CONFIG_PATH, json.dumps(data))
            except:
                pass

    def task_config_create_hook(self, task: dict) -> None:
        self.task_config_update_hook(task)

    def task_config_remove_hook(self, task: dict) -> None:
        try:
            data = json.loads(read_file(self.CONFIG_PATH))
            new_data = {
                "channel": data.pop("channel", ""),
                "0": [],
            }
            for _, data_list in data.items():
                new_data["0"].extend(data_list)

            write_file(self.CONFIG_PATH, json.dumps(new_data))
        except:
            pass


class ViewMsgFormat(BaseTaskViewMsg):
    _FORMAT = {
        "101": (
            lambda x: "<span>定期扫描FTP日志并发送告警信息</span>"
        ),
        "102": (
            lambda x: "<span>当检查到FTP用户的密码到期后发送提醒信息</span>"
        )
    }

    def get_msg(self, task: dict) -> Optional[str]:
        if task["template_id"] == "101":
            return self._FORMAT["101"](task)
        if task["template_id"] == "102":
            return self._FORMAT["102"](task)
        return None


FTPLogTask.VIEW_MSG = FTPUserTask.VIEW_MSG = ViewMsgFormat