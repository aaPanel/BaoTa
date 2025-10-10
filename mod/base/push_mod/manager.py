import json
import os
import time
from typing import Union, Optional

from .util import debug_log, set_module_logs, write_log
from .mods import TaskTemplateConfig, TaskConfig, SenderConfig, TaskRecordConfig
from .system import PushSystem
from mod.base import json_response

import sys
if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class/")
import public
class PushManager:

    def __init__(self):
        self._template_conf: Optional[TaskTemplateConfig] = None
        self._task_conf: Optional[TaskConfig] = None
        self._send_config: Optional[SenderConfig] = None
        self._send_conf_cache = {}

    @property
    def template_conf(self):
        if isinstance(self._template_conf, TaskTemplateConfig):
            return self._template_conf
        else:
            self._template_conf = TaskTemplateConfig()
            return self._template_conf

    @property
    def task_conf(self):
        if isinstance(self._task_conf, TaskConfig):
            return self._task_conf
        else:
            self._task_conf = TaskConfig()
            return self._task_conf

    @property
    def send_config(self):
        if isinstance(self._send_config, SenderConfig):
            return self._send_config
        else:
            self._send_config = SenderConfig()
            return self._send_config

    def _get_sender_conf(self, sender_id):
        if sender_id in self._send_conf_cache:
            return self._send_conf_cache[sender_id]
        tmp = self.send_config.get_by_id(sender_id)
        self._send_conf_cache[sender_id] = tmp
        return tmp

    def normalize_task_config(self, task, template) -> Union[dict, str]:
        result = {}
        sender = task.get("sender", None)
        if sender is None:
            return "未设置告警通道"
        if not isinstance(sender, list):
            return "告警通道设置错误"

        new_sender = []
        for i in sender:
            sender_conf = self._get_sender_conf(i)
            if not sender_conf:
                continue
            else:
                new_sender.append(i)
            if sender_conf["sender_type"] not in template["send_type_list"]:
                if sender_conf["sender_type"] == "sms":
                    return "不支持短信告警"
                return "不支持的告警方式:{}".format(sender_conf['data']["title"])
            if not sender_conf["used"]:
                if sender_conf["sender_type"] == "sms":
                    return "短信告警通道已关闭"
                return "已关闭的告警方式:{}".format(sender_conf['data']["title"])

        result["sender"] = new_sender
        result["task_data"] = task.get("task_data", {})
        if "default" in template and template["default"]:
            task_data = task.get("task_data", {})
            for k, v in template["default"].items():
                if k not in task_data:
                    task_data[k] = v

            result["task_data"] = task_data

        time_rule = task.get("time_rule", {})

        if "send_interval" in time_rule:
            if not isinstance(time_rule["send_interval"], int):
                return "最小间隔时间设置错误"
            if time_rule["send_interval"] < 0:
                return "最小间隔时间设置错误"

        if "time_range" in time_rule:
            if not isinstance(time_rule["time_range"], list):
                return "时间范围设置错误"
            if not len(time_rule["time_range"]) == 2:
                del time_rule["time_range"]
            else:
                time_range = time_rule["time_range"]
                if not (isinstance(time_range[0], int) and isinstance(time_range[1], int) and
                        0 <= time_range[0] < time_range[1] <= 60 * 60 * 24):
                    return "时间范围设置错误"

        result["time_rule"] = time_rule

        number_rule = task.get("number_rule", {})
        if "day_num" in number_rule:
            if not (isinstance(number_rule["day_num"], int) and number_rule["day_num"] >= 0):
                return "每日最小次数设置错误"

        if "total" in number_rule:
            if not (isinstance(number_rule["total"], int) and number_rule["total"] >= 0):
                return "最大告警次数设置错误"

        result["number_rule"] = number_rule

        if "status" not in task:
            result["status"] = True
        if "status" in task:
            if isinstance(task["status"], bool):
                result["status"] = task["status"]

        return result

    def set_task_conf_data(self, push_data: dict) -> Optional[str]:
        task_id: Optional[str] = push_data.get("task_id", None)
        template_id = push_data.get("template_id")
        task = push_data.get("task_data")

        target_task_conf = None
        if task_id is not None:
            tmp = self.task_conf.get_by_id(task_id)
            if tmp is not None:
                target_task_conf = tmp

        template = self.template_conf.get_by_id(template_id)
        if not template:
            return "未查询到告警模板"

        if template["unique"] and not target_task_conf:
            for i in self.task_conf.config:
                if i["template_id"] == template["id"]:
                    target_task_conf = i
                    break

        task_obj = PushSystem().get_task_object(template_id, template["load_cls"])
        if not task_obj:
            return "加载任务类型错误，您可以尝试修复面板"

        if task_obj.source_name in ("nodes_nginx_http_load_push", "nodes_nginx_tcp_load_push", "nodes_mysql_slave_err_push"):
            public.set_module_logs("nodes_push_9", task_obj.source_name)

        res = self.normalize_task_config(task, template)
        if isinstance(res, str):
            return res

        task_data = task_obj.check_task_data(res["task_data"])
        if isinstance(task_data, str):
            return task_data

        number_rule = task_obj.check_num_rule(res["number_rule"])
        if isinstance(number_rule, str):
            return number_rule

        time_rule = task_obj.check_time_rule(res["time_rule"])
        if isinstance(time_rule, str):
            return time_rule

        res["task_data"] = task_data
        res["number_rule"] = number_rule
        res["time_rule"] = time_rule

        res["keyword"] = task_obj.get_keyword(task_data)
        res["source"] = task_obj.source_name
        res["title"] = task_obj.get_title(task_data)

        set_module_logs("push_type", task_obj.source_name)
        if not target_task_conf:
            tmp = self.task_conf.get_by_keyword(res["source"], res["keyword"])
            if tmp:
                target_task_conf = tmp

        if not target_task_conf:
            res["id"] = self.task_conf.nwe_id()
            res["template_id"] = template_id
            res["status"] = True
            res["pre_hook"] = {}
            res["after_hook"] = {}
            res["last_check"] = 0
            res["last_send"] = 0
            res["number_data"] = {}
            res["create_time"] = time.time()
            res["record_time"] = 0
            self.task_conf.config.append(res)
            err_data = task_obj.task_config_create_hook(res)
            if err_data is not None:
                return err_data
            write_log("告警设置", "添加告警任务成功：{}".format(res["title"]))
        else:
            new_task_data = res.pop("task_data")
            target_task_conf.update(res)
            target_task_conf["task_data"].update(new_task_data)
            target_task_conf["last_check"] = 0
            target_task_conf["number_data"] = {}  # 次数控制数据置空
            err_data = task_obj.task_config_update_hook(target_task_conf)
            if err_data is not None:
                return err_data
            write_log("告警设置", "修改告警任务成功：{}".format(res["title"]))

        self.task_conf.save_config()

        return None

    def update_task_status(self, get):
        # 先调用 set_task_conf 修改任务配置
        set_conf_response = self.set_task_conf(get)
        # print(set_conf_response)
        if not set_conf_response['status']:
            return set_conf_response  # 返回错误信息

        # 读取任务数据
        file_path = '{}/data/mod_push_data/task.json'.format(public.get_panel_path())
        try:
            with open(file_path, 'r') as file:
                tasks = json.load(file)
        except (IOError, json.JSONDecodeError):
            return json_response(status=False, msg="无法读取任务数据")
        # get.title="pure-ftpd服务停止告警"
        # 查找对应的 task_id
        task_title = get.title.strip()  # 假设 get 中有 title 参数
        task_id = None
        
        for task in tasks:
            if task.get('title') == task_title:
                task_id = task.get('id')
                break

        if not task_id:
            return json_response(status=False, msg="未找到对应的任务")

        # 调用 change_task_conf 修改任务状态
        get.task_id = task_id
        return self.change_task_conf(get)

    def set_task_conf(self, get):
        task_id = None
        try:
            if hasattr(get, "task_id"):
                task_id = get.task_id.strip()
                if not task_id:
                    task_id = None
                # else:
                #     self.remove_task_conf(get)
            template_id = get.template_id.strip()
            task = json.loads(get.task_data.strip())
        except (AttributeError, json.JSONDecodeError, TypeError, ValueError):
            return json_response(status=False, msg="参数错误")
        push_data = {
            "task_id": task_id,
            "template_id": template_id,
            "task_data": task,
        }
        res = self.set_task_conf_data(push_data)
        if res:
            return json_response(status=False, msg=res)
        return json_response(status=True, msg="告警任务保存成功")

    def change_task_conf(self, get):
        try:
            task_id = get.task_id.strip()
            status = int(get.status)  # 获取status字段并转换为整数
        except (AttributeError, ValueError):
            return json_response(status=False, msg="参数错误")

        if status not in [0, 1]:
            return json_response(status=False, msg="无效的状态值")

        tmp = self.task_conf.get_by_id(task_id)
        if tmp is None:
            return json_response(status=False, msg="未查询到告警任务")

        template = self.template_conf.get_by_id(tmp['template_id'])
        if not template:
            return json_response(status=False, msg="未查询到告警模板")
        task_obj = PushSystem().get_task_object(tmp['template_id'], template["load_cls"])
        if not task_obj:
            return json_response(status=False, msg="加载任务类型错误，您可以尝试修复面板")

        tmp["status"] = bool(status)  # 将status转换为布尔值并设置
        res = task_obj.task_config_update_hook(tmp)
        if res is not None:
            return json_response(status=False, msg=res)
        write_log("告警设置", "{}告警任务成功：{}".format("开启" if status else "关闭", tmp["title"]))
        self.task_conf.save_config()
        return json_response(status=True, msg="操作成功")

    def update_ssl_task(self, get):
        import sys
        sys.path.insert(0, "/www/server/panel/class/")
        import public

        """
        根据前端发送的参数，修改对应任务的配置
        :param file_path: JSON文件的路径
        :param task_id: 需要修改的任务ID
        :param update_data: 前端发送的更新数据
        :return: 修改结果
        """
        
        def load_task_data():
            try:
                file_path = f'{public.get_panel_path()}/data/mod_push_data/task.json'
                return json.loads(public.readFile(file_path))
            except:
                return []

        def save_task_data(data):
            file_path = f'{public.get_panel_path()}/data/mod_push_data/task.json'
            with open(file_path, 'w') as file:
                json.dump(data, file, indent=4)
        
        def find_task(data, project):
            for task in data:
                if task.get('source') == 'site_ssl' and task.get('task_data', {}).get('project') == project:
                    return task
            return None

        try:
            task_id = get.task_id
            update_data = json.loads(get.task_data)

            if not update_data.get('sender'):
                return {'status': False, 'msg': '请设置告警的通知方式！'}

            status = int(get.status)
            project = update_data['task_data']['project']

            data = load_task_data()

            if not task_id:
                return self.set_task_conf(get)

            task = find_task(data, project)
            if task:
                get.task_id = task['id']
            else:
                get.task_id = ""

            self.set_task_conf(get)

            if status == 0:
                task_found = False
                for task in data:
                    if task.get('source') == 'site_ssl' and task.get('task_data', {}).get('project') == project:
                        task['status'] = False
                        task_found = True
                
                if not task_found:
                    get.task_id = ""
                    self.set_task_conf(get)
                    data = load_task_data()
                    for task in data:
                        if task.get('source') == 'site_ssl' and task.get('keyword') == project:
                            task['status'] = False
                            break

                save_task_data(data)

            return {'status': True, 'msg': '操作成功'}

        except Exception as e:
            return {'status': False, 'msg': str(e)}
                     
        
    def change_task(self,task_id,status):
        tmp = self.task_conf.get_by_id(task_id)
        tmp["status"] = bool(status)  # 将status转换为布尔值并设置
        self.task_conf.save_config()
       

    def change_ssl_task(self, get):
        # result = public.M('sites').select()
        try:
            task_id = get.task_id.strip()
            status = int(get.status)  # 获取status字段并转换为整数
            
        except (AttributeError, ValueError):
            return json_response(status=False, msg="参数错误")

        if status not in [0, 1]:
            return json_response(status=False, msg="无效的状态值")
        project=get.project
        try:
            data = json.loads(public.readFile('{}/data/mod_push_data/task.json'.format(public.get_panel_path())))
        except:
            return {'status': False, 'msg': '文件不存在'}
        self.process_tasks(data, status, project, task_id, get)
        return json_response(status=True, msg="操作成功")

    def remove_task_conf(self, get):
        try:
            task_id = get.task_id.strip()
        except AttributeError:
            return json_response(status=False, msg="参数错误")

        tmp = self.task_conf.get_by_id(task_id)
        if tmp is None:
            return json_response(status=True, msg="为查询到告警任务")

        self.task_conf.config.remove(tmp)

        self.task_conf.save_config()
        template = self.template_conf.get_by_id(tmp["template_id"])
        if template:
            task_obj = PushSystem().get_task_object(template["id"], template["load_cls"])
            if task_obj:
                task_obj.task_config_remove_hook(tmp)

        return json_response(status=True, msg="操作成功")

    @staticmethod
    def clear_task_record_by_task_id(task_id):
        tr_conf = TaskRecordConfig(task_id)
        if os.path.exists(tr_conf.config_file_path):
            os.remove(tr_conf.config_file_path)
