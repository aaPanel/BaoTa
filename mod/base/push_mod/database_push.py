# 数据库相关告警已移除，不再使用
import json
import os
import sys
import ipaddress
from datetime import datetime, timedelta
from typing import Tuple, Union, Optional

from .send_tool import WxAccountMsg
from .base_task import BaseTask, BaseTaskViewMsg
from .util import read_file, DB, GET_CLASS

try:
    if "/www/server/panel/class" not in sys.path:
        sys.path.insert(0, "/www/server/panel/class")
    from panel_msg.collector import DatabasePushMsgCollect
except ImportError:
    DatabasePushMsgCollect = None


def is_ipaddress(ip_data: str) -> bool:
    try:
        ipaddress.ip_address(ip_data)
    except ValueError:
        return False
    return True


class MysqlPwdEndTimeTask(BaseTask):

    def __init__(self):
        super().__init__()
        self.template_name = "MySQL数据库密码到期"
        self.source_name = "mysql_pwd_end"

        self.push_db_user = ""

    def get_title(self, task_data: dict) -> str:
        return "Msql:" + task_data["project"][1] + "用户密码到期提醒"

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        task_data["interval"] = 600
        if not (isinstance(task_data["project"], list) and len(task_data["project"]) == 3):
            return "设置的用户格式错误"
        project = task_data["project"]
        if not (isinstance(project[0], int) and isinstance(project[1], str) and is_ipaddress(project[2])):
            return "设置的检测用户格式错误"

        if not (isinstance(task_data["cycle"], int) and task_data["cycle"] >= 1):
            return "到期时间参数错误，至少为 1 天"
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return "_".join([str(i) for i in task_data["project"]])

    def check_num_rule(self, num_rule: dict) -> Union[dict, str]:
        num_rule["day_num"] = 1
        return num_rule

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        sid = task_data["project"][0]
        username = task_data["project"][1]
        host = task_data["project"][2]

        if "/www/server/panel/class" not in sys.path:
            sys.path.insert(0, "/www/server/panel/class")
        try:
            import panelMysql
            import db_mysql
        except ImportError:
            return None

        if sid == 0:
            try:
                db_port = int(panelMysql.panelMysql().query("show global variables like 'port'")[0][1])
                if db_port == 0:
                    db_port = 3306
            except:
                db_port = 3306
            conn_config = {
                "db_host": "localhost",
                "db_port": db_port,
                "db_user": "root",
                "db_password": DB("config").where("id=?", (1,)).getField("mysql_root"),
                "ps": "本地服务器",
            }
        else:
            conn_config = DB("database_servers").where("id=? AND LOWER(db_type)=LOWER('mysql')", (sid,)).find()
        if not conn_config:
            return None

        mysql_obj = db_mysql.panelMysql().set_host(conn_config["db_host"], conn_config["db_port"], None,
                                                   conn_config["db_user"], conn_config["db_password"])
        if isinstance(mysql_obj, bool):
            return None

        data_list = mysql_obj.query(
            "SELECT password_last_changed FROM mysql.user WHERE user='{}' AND host='{}';".format(username, host))

        if not isinstance(data_list, list) or not data_list:
            return None

        try:
            # todo：检查这里的时间转化逻辑问题
            last_time = data_list[0][0]
            expire_time = last_time + timedelta(days=task_data["cycle"])
        except:
            return None

        if datetime.now() > expire_time:
            self.title = self.get_title(task_data)
            self.push_db_user = username
            return {"msg_list": [
                ">告警类型：MySQL密码即将到期",
                ">告警内容：{} {}@{} 密码过期时间<font color=#ff0000>{} 天</font>".format(
                    conn_config["ps"], username, host, expire_time.strftime("%Y-%m-%d %H:%M:%S"))
            ]}

    # 数据库相关告警已移除，不再使用
    def filter_template(self, template: dict) -> Optional[dict]:
        return None

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return "", {}

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "MySQL数据库密码到期"
        msg.msg = "Mysql用户：{}的密码即将过期，请注意".format(self.push_db_user)
        msg.next_msg = "请登录面板，查看主机情况"
        return msg


class MysqlReplicateStatusTask(BaseTask):

    def __init__(self):
        super().__init__()
        self.template_name = "MySQL主从复制异常告警"
        self.source_name = "mysql_replicate_status"
        self.title = "MySQL主从复制异常告警"

        self.slave_ip = ''

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        if not (isinstance(task_data["project"], str) and task_data["project"]):
            return "请选择告警的从库！"

        if not (isinstance(task_data["count"], int) and task_data["count"] in (1, 2)):
            return "是否自动修复选择错误！"

        if not (isinstance(task_data["interval"], int) and task_data["interval"] >= 60):
            return "检查间隔时间错误，至少需要60s的间隔"
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return task_data["project"]

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        import PluginLoader

        args = GET_CLASS()
        args.slave_ip = task_data["project"]
        res = PluginLoader.plugin_run("mysql_replicate", "get_replicate_status", args)
        if res.get("status", False) is False:
            return None

        self.slave_ip = task_data["project"]
        if len(res.get("data", [])) == 0:
            s_list = [">告警类型：MySQL主从复制异常告警",
                      ">告警内容：<font color=#ff0000>从库 {} 主从复制已停止，请尽快登录面板查看详情</font>".format(
                          task_data["project"])]
            return {"msg_list": s_list}

        sql_status = io_status = False
        for item in res.get("data", []):
            if item["name"] == "Slave_IO_Running" and item["value"] == "Yes":
                io_status = True
            if item["name"] == "Slave_SQL_Running" and item["value"] == "Yes":
                sql_status = True
            if io_status is True and sql_status is True:
                break

        if io_status is False or sql_status is False:
            repair_txt = "请尽快登录面板查看详情"
            if task_data["count"] == 1:  # 自动修复
                PluginLoader.plugin_run("mysql_replicate", "repair_replicate", args)
                repair_txt = "，正在尝试修复"

            s_list = [">告警类型：MySQL主从复制异常告警",
                      ">告警内容：<font color=#ff0000>从库 {} 主从复制发生异常{}</font>".format(
                          task_data["project"], repair_txt)]
            return {"msg_list": s_list}
        return None

    @staticmethod
    def _get_mysql_replicate():
        slave_list = []
        mysql_replicate_path = os.path.join("/www/server/panel/plugin", "mysql_replicate", "config.json")
        if os.path.isfile(mysql_replicate_path):
            conf = read_file(mysql_replicate_path)
            try:
                conf = json.loads(conf)
                slave_list = [{"title": slave_ip, "value": slave_ip} for slave_ip in conf["slave"].keys()]
            except:
                pass
        return slave_list

    # 数据库相关告警已移除，不再使用
    def filter_template(self, template: dict) -> Optional[dict]:
        return None

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return '', {}

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "MySQL主从复制异常告警"
        msg.msg = "从库 {} 主从复制发生异常".format(self.slave_ip)
        msg.next_msg = "请登录面板，在[软件商店-MySQL主从复制(重构版)]中查看"
        return msg


class ViewMsgFormat(BaseTaskViewMsg):
    _FORMAT = {
        "30": (
            lambda x: "<span>剩余时间小于{}天{}</span>".format(
                x["task_data"].get("cycle"),
                ("(如未处理，次日会重新发送1次，持续%d天)" % x.get("number_rule", {}).get("day_num", 0)) if x.get(
                    "number_rule", {}).get("day_num", 0) else ""

            )
        ),
        "31": (lambda x: "<span>MySQL主从复制异常告警</span>".format()),
    }

    def get_msg(self, task: dict) -> Optional[str]:
        if task["template_id"] in self._FORMAT:
            return self._FORMAT[task["template_id"]](task)
        return None
