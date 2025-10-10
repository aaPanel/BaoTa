# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Windows面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2020 宝塔软件(https://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: baozi <1191604998@qq.com>
# +-------------------------------------------------------------------

import sys
import os
import json
import datetime

class_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# /www/server/panel/class
bt_panel_path = os.path.dirname(class_path)
sys.path.insert(0, class_path)
sys.path.insert(0, bt_panel_path)
import public
import panelPush
from push.base_push import base_push, WxAccountMsg
from panel_msg.collector import DatabasePushMsgCollect
import db_mysql
import panelMysql


class database_push(base_push):
    __TEMPLATE_PATH = os.path.join(public.get_panel_path(), "class/push/scripts/database_push.json")
    __push_model = ['dingding', 'weixin', 'mail', 'sms', 'wx_account', 'feishu']
    __push_conf = os.path.join(public.get_panel_path(), "class/push/push.json")

    def __init__(self):
        self.__push = panelPush.panelPush()


    def get_version_info(self, get=None):
        data = {
            'ps': '宝塔系统告警',
            'version': '1.0',
            'date': '2023-07-16',
            'author': '宝塔',
            'help': 'http://www.bt.cn/bbs'
        }
        return data

    # 格式化返回执行周期， 目前无作用
    def get_push_cycle(self, data: dict):
        return data

    # 获取模块推送参数
    def get_module_config(self, get: public.dict_obj):
        data = []
        item = self.__push.format_push_data(
            push=["mail", 'dingding', 'weixin', "feishu", "wx_account"],
            project='system', type='')
        item['cycle'] = 15
        item['title'] = '磁盘容量限额'
        data.append(item)
        return data

    # 获取模块配置项
    def get_push_config(self, get: public.dict_obj):
        task_id = get.id
        push_list = self.__push._get_conf()

        if task_id not in push_list["database_push"]:
            res_data = public.returnMsg(False, '未找到指定配置.')
            res_data['code'] = 100
            return res_data
        result = push_list["database_push"][task_id]
        return result

    # 清除推送次数
    @staticmethod
    def clear_push_count(task_id):
        try:
            tip_file = os.path.join(public.get_panel_path(), "data/push/tips", task_id)
            if os.path.exists(tip_file):
                os.remove(tip_file)
        except:
            pass

    # 写入推送配置文件
    def set_push_config(self, get: public.dict_obj):
        id = get.id
        module = get.name
        pdata = json.loads(get.data)
        data = self.__push._get_conf()
        if module not in data: data[module] = {}

        self.clear_push_count(id)

        if pdata["type"] == "mysql_replicate_status":
            if not pdata["project"]:
                return public.returnMsg(False, "请选择告警的从库！")
            data[module][pdata["project"]] = pdata
        elif pdata["type"] == "mysql_pwd_endtime":
            if not pdata["project"]:
                return public.returnMsg(False, "请选择告警的MySQL用户！")
            data[module][id] = pdata
        else:
            data[module][id] = pdata

        return data

    # 删除推送配置
    def del_push_config(self, get: public.dict_obj):
        # 从配置中删除信息，并做一些您想做的事，如记日志
        task_id = get.id
        module = get.name

        data = self.__push._get_conf()
        if str(task_id).strip() in data[module]:
            del data[module][task_id]
        public.writeFile(self.__push_conf, json.dumps(data))
        return public.returnMsg(True, "删除成功!")

    def get_total(self):
        return True

    # 检查并获取推送消息，返回空时，不做推送, 传入的data是配置项
    def get_push_data(self, data, total):

        current_time = datetime.datetime.now()
        stime = current_time.timestamp()
        result = {'index': stime, 'push_keys': []}

        if data['type'] in ['mysql_pwd_endtime']:
            if stime < data['index'] + 86400:
                return public.returnMsg(False, "一天推送一次，跳过.")

            sid = data["project"][0]
            username = data["project"][1]
            host = data["project"][2]

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
                    "db_password": public.M("config").where("id=?", (1,)).getField("mysql_root"),
                    "ps": "本地服务器",
                }
            else:
                conn_config = public.M("database_servers").where("id=? AND LOWER(db_type)=LOWER('mysql')", (sid,)).find()
            if not conn_config:
                return result

            mysql_obj = db_mysql.panelMysql().set_host(conn_config["db_host"], conn_config["db_port"], None, conn_config["db_user"], conn_config["db_password"])
            if isinstance(mysql_obj, bool):
                return result

            data_list = mysql_obj.query("SELECT password_last_changed FROM mysql.user WHERE user='{}' AND host='{}';".format(username, host))
            if not isinstance(data_list, list) or not data_list:
                return result

            last_time = data_list[0][0]
            expire_time = last_time + datetime.timedelta(days=data["cycle"])

            if current_time > expire_time:
                s_list = [
                    ">告警类型：MySQL密码即将到期",
                    ">告警内容：{} {}@{} 密码过期时间<font color=#ff0000>{} 天</font>".format(conn_config["ps"], username, host, expire_time.strftime("%Y-%m-%d %H:%M:%S"))
                ]
                msg = DatabasePushMsgCollect.mysql_pwd_endtime(s_list, data["title"])
                for m_module in data['module'].split(','):
                    if m_module == 'sms':
                        continue
                    elif m_module == 'wx_account':
                        result[m_module] = ToWechatAccountMsg.mysql_pwd_endtime("MySQL密码已到期")
                        continue

                    sdata = public.get_push_info('MySQL密码到期提醒', s_list)
                    sdata["push_type"] = 'MySQL密码到期'
                    result[m_module] = sdata

            elif data["cycle"] > 3 and current_time > last_time + datetime.timedelta(days=data["cycle"] - 3):
                expire_day = (current_time - (last_time + datetime.timedelta(days=data["cycle"] - 3))).days
                s_list = [
                    ">告警类型：MySQL密码即将到期",
                    ">告警内容：{} {}@{} 密码剩余天数:<font color=#ff0000>{} 天</font>".format(conn_config["ps"], username, host,expire_day)
                ]
                msg = DatabasePushMsgCollect.mysql_pwd_endtime(s_list, data["title"])
                for m_module in data['module'].split(','):
                    if m_module == 'sms':
                        continue
                    elif m_module == 'wx_account':
                        result[m_module] = ToWechatAccountMsg.mysql_pwd_endtime("MySQL密码{}天后到期".format(expire_day))
                        continue

                    sdata = public.get_push_info('MySQL密码到期提醒', s_list)
                    sdata["push_type"] = 'MySQL密码到期'
                    result[m_module] = sdata
            return result

        # MySQL 主从复制异常告警
        elif data['type'] in ['mysql_replicate_status']:
            if stime < data["index"] + data["interval"]:
                return public.returnMsg(False, "未达到间隔时间，跳过.")
            
            import PluginLoader

            args = public.dict_obj()
            args.slave_ip = data["project"]
            res = PluginLoader.plugin_run("mysql_replicate", "get_replicate_status", args)
            if res.get("status", False) is False:
                return public.returnMsg(False, "获取主从信息失败！")

            if len(res.get("data")) == 0:
                s_list = [">告警类型：MySQL主从复制异常告警",
                          ">告警内容：<font color=#ff0000>从库 {} 主从复制已停止，请尽快登录面板查看详情</font>".format(data["project"])]
                msg = DatabasePushMsgCollect.mysql_replicate_status(s_list, data["title"])
                for m_module in data['module'].split(','):
                    if m_module == 'sms':
                        continue
                    elif m_module == 'wx_account':
                        result[m_module] = ToWechatAccountMsg.mysql_replicate_status("MySQL主从复制异常告警")
                        continue

                    sdata = public.get_push_info('MySQL主从复制异常告警', s_list)
                    sdata["push_type"] = 'MySQL主从复制异常告警'
                    result[m_module] = sdata
                    return result

            io_status = False
            sql_status = False
            for item in res.get("data"):
                if item["name"] == "Slave_IO_Running" and item["value"] == "Yes":
                    io_status = True
                if item["name"] == "Slave_SQL_Running" and item["value"] == "Yes":
                    sql_status = True
                if io_status is True and sql_status is True:
                    break

            if io_status is False or sql_status is False:
                repair_txt = "请尽快登录面板查看详情"
                if data["count"] == 1: # 自动修复
                    PluginLoader.plugin_run("mysql_replicate", "repair_replicate", args)
                    repair_txt = "，正在尝试修复"

                s_list = [">告警类型：MySQL主从复制异常告警",
                          ">告警内容：<font color=#ff0000>从库 {} 主从复制发生异常{}</font>".format(data["project"], repair_txt)]
                msg = DatabasePushMsgCollect.mysql_replicate_status(s_list, data["title"])
                for m_module in data['module'].split(','):
                    if m_module == 'sms':
                        continue
                    elif m_module == 'wx_account':
                        slave_ip = data["project"][:3] if len(data["project"]) >= 3 else data["project"]
                        result[m_module] = ToWechatAccountMsg.mysql_replicate_status("从库 {} 主从复制发生异常{}".format(slave_ip, repair_txt))
                        continue
    
                    sdata = public.get_push_info('MySQL主从复制异常告警', s_list)
                    sdata["push_type"] = 'MySQL主从复制异常告警'
                    result[m_module] = sdata
                return result

        return public.returnMsg(False, "未达到阈值，跳过.")

    # 返回到前端信息的钩子, 默认为返回传入信息（即：当前设置的任务的信息）
    @staticmethod
    def get_view_msg(task_id, task_data):
        task_data["tid"] = view_msg.get_tid(task_data)
        task_data["view_msg"] = view_msg.get_msg_by_type(task_data)
        return task_data

    def get_task_template(self):
        res = public.readFile(self.__TEMPLATE_PATH)
        if not res:
            return "数据库告警设置", [{}]
        res_data = json.loads(res)

        res_data["mysql_replicate_status"]["field"][0]["items"] = self.__get_mysql_replicate()
        return "数据库警设置", [v for v in res_data.values()]

    @classmethod
    def __get_mysql_replicate(cls) -> list:
        slave_list = []
        mysql_replicate_path = os.path.join(public.get_plugin_path(), "mysql_replicate", "config.json")
        if os.path.isfile(mysql_replicate_path):
            conf = public.readFile(mysql_replicate_path)
            try:
                conf = json.loads(conf)
                slave_list = [{"title": slave_ip, "value": slave_ip} for slave_ip  in conf["slave"].keys()]
            except:
                pass
        return slave_list


class ViewMsgFormat(object):
    _FORMAT = {
        "mysql_pwd_endtime": (
            lambda x: "<span>剩余时间小于{}天{}</span>".format(
                x.get("cycle"),
                "(如未处理，次日会重新发送1次，持续%d天)" % x.get("push_count", 0) if x.get("push_count", 0) else ""
            )
        ),
        "mysql_replicate_status": (lambda x: "<span>MySQL主从复制异常告警</span>".format()),
    }

    _TID = {
        "mysql_pwd_endtime": "database_push@0",
        "mysql_replicate_status": "database_push@1",
    }

    def get_msg_by_type(self, data):
        return self._FORMAT[data["type"]](data)

    def get_tid(self, data):
        return self._TID[data["type"]]


view_msg = ViewMsgFormat()


class ToWechatAccountMsg:
    @staticmethod
    def mysql_pwd_endtime(message: str):
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "MySQL数据库密码到期提醒"
        msg.msg = message
        msg.next_msg = "请登录面板，在[数据库]中修改密码"
        return msg

    @staticmethod
    def mysql_replicate_status(message: str):
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "MySQL主从复制异常告警"
        msg.msg = message
        msg.next_msg = "请登录面板，在[软件商店-MySQL主从复制(重构版)]中查看"
        return msg
