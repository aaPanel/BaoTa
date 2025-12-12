import glob
import hashlib
import json
import os
import re
import sys
import time
import traceback

import psutil
from datetime import datetime
from importlib import import_module
from typing import Tuple, Union, Optional, List, Dict

from .send_tool import WxAccountMsg, WxAccountLoginMsg
from .base_task import BaseTask, BaseTaskViewMsg
from .mods import PUSH_DATA_PATH, TaskConfig, SenderConfig
from .util import read_file, DB, write_file, check_site_status, GET_CLASS, ExecShell, get_config_value, public_get_cache_func, \
    public_set_cache_func, get_network_ip, public_get_user_info, public_http_post, panel_version
from mod.base.web_conf import RealSSLManger


class _WebInfo:

    def __init__(self):
        self.last_time = 0
        self._site_cache = None

    @property
    def site_list(self) -> List[Dict]:
        if self._site_cache is not None and time.time() - self.last_time < 300:
            return self._site_cache
        try:
            site_list = DB('sites').field('id,name,project_type,project_config').select()
            self._site_cache = site_list
            self.last_time = time.time()
        except:
            site_list = []

        return site_list

    def __call__(self, project_types=None, all_type=False) -> Tuple[List[Dict], Dict[str, List[Dict]]]:
        if project_types is None:
            project_types = ()

        items = []
        items_by_type = {pt: [] for pt in project_types}

        for i in self.site_list:
            if i["project_type"] not in project_types and not all_type:
                continue
            items.append({
                "title": i["name"] + "[" + i["project_type"] + "]",
                "value": i["name"]
            })

            items_by_type.setdefault(i["project_type"], []).append({
                "title": i["name"],
                "value": i["id"]
            })

        return items, items_by_type


web_info_data = _WebInfo()


class SSLTask(BaseTask):

    def __init__(self):
        super().__init__()
        self.source_name = "site_ssl"
        self.template_name = "网站证书(SSL)到期"
        self._tip_file = "{}/site_ssl.tip".format(PUSH_DATA_PATH)
        self._tip_data: Optional[dict] = None
        self._task_config = TaskConfig()

        # 每次任务使用
        self.ssl_list = []
        self.push_keys = []
        self.task_id = None

    @property
    def tips(self) -> dict:
        if self._tip_data is not None:
            return self._tip_data
        try:
            self._tip_data = json.loads(read_file(self._tip_file))
        except:
            self._tip_data = {}
        return self._tip_data

    def save_tip(self):
        write_file(self._tip_file, json.dumps(self.tips))

    def get_keyword(self, task_data: dict) -> str:
        return task_data["project"]

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        panelPath = '/www/server/panel/'
        os.chdir(panelPath)
        sys.path.insert(0, panelPath)
        # 过滤单独设置提醒的网站
        not_push_web = [i["task_data"]["project"] for i in self._task_config.config if i["source"] == self.source_name]
        sql = DB("sites")
        total = self._task_config.get_by_id(task_id).get("number_rule", {}).get("total", 1)
        if "all" in not_push_web:
            not_push_web.remove("all")

        need_check_list = []
        if task_data["project"] == "all":
            # 所有正常网站
            web_list = sql.where('status=1', ()).select()
            for web in web_list:
                if web['name'] in not_push_web:
                    continue
                if web['project_type']!="PHP":
                    if not check_site_status(web):
                        continue

                if self.tips.get(task_id, {}).get(web['name'], 0) > total:
                    continue

                if not web['project_type'].lower() in ['php', 'proxy']:
                    project_type = web['project_type'].lower() + '_'
                else:
                    project_type = ''

                need_check_list.append((web['name'], project_type))

        else:
            find = sql.where('name=? and status=1', (task_data['project'],)).find()
            if not find:
                return None

            if find['project_type']!="PHP":
                if not check_site_status(find):
                    return None

            if not find['project_type'].lower() in ['php', 'proxy']:
                project_type = find['project_type'].lower() + '_'
            else:
                project_type = ''

            need_check_list.append((find['name'], project_type))

        for name, project_type in need_check_list:
            info = self._check_ssl_end_time(name, task_data['cycle'], project_type)
            if isinstance(info, dict):  # 返回的是详情，说明需要推送了
                info['site_name'] = name
                self.push_keys.append(name)
                self.ssl_list.append(info)

        if len(self.ssl_list) == 0:
            return None

        s_list = ['>即将到期：<font color=#ff0000>{} 张</font>'.format(len(self.ssl_list))]
        for x in self.ssl_list:
            s_list.append(">网站：{}  到期：{}".format(x['site_name'], x['notAfter']))

        self.task_id = task_id
        self.title = self.get_title(task_data)
        return {"msg_list": s_list}

    @staticmethod
    def _check_ssl_end_time(site_name, limit, prefix) -> Optional[dict]:
        info = RealSSLManger(conf_prefix=prefix).get_site_ssl_info(site_name)
        if info is not None:
            end_time = datetime.strptime(info['notAfter'], '%Y-%m-%d')
            if int((end_time.timestamp() - time.time()) / 86400) <= limit:
                return info
        return None

    def get_title(self, task_data: dict) -> str:
        if task_data["project"] == "all":
            return "所有网站证书(SSL)到期提醒"
        return "网站[{}]证书(SSL)到期提醒".format(task_data["project"])

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return 'ssl_end|宝塔面板SSL到期提醒', {
            "name": push_public_data["ip"],
            "website": self.ssl_list[0]['site_name'],
            'time': self.ssl_list[0]["notAfter"],
            'total': len(self.ssl_list)
        }

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "网站SSL到期提醒"
        msg.msg = "有{}个网站的证书将到期,会影响访问".format(len(self.ssl_list))
        msg.next_msg = "请登录面板，在[网站]中进行续签操作"
        return msg

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        task_data["interval"] = 60 * 60 * 24  # 默认检测间隔时间 1 天
        if not (isinstance(task_data['cycle'], int) and task_data['cycle'] >= 1):
            return "剩余时间参数错误，至少为1天"
        return task_data

    def filter_template(self, template) -> dict:
        items, _ = web_info_data(all_type=True)
        template["field"][0]["items"].extend(items)
        return template

    def check_num_rule(self, num_rule: dict) -> Union[dict, str]:
        num_rule["get_by_func"] = "can_send_by_num_rule"
        return num_rule

    # 实际的次数检查已在 get_push_data 其他位置完成
    def can_send_by_num_rule(self, task_id: str, task_data: dict, number_rule: dict, push_data: dict) -> Optional[str]:
        return None

    def task_run_end_hook(self, res) -> None:
        if not res["do_send"]:
            return
        if self.task_id:
            if self.task_id not in self.tips:
                self.tips[self.task_id] = {}

            for w in self.push_keys:
                if w in self.tips[self.task_id]:
                    self.tips[self.task_id][w] += 1
                else:
                    self.tips[self.task_id][w] = 1

            self.save_tip()

    def task_config_update_hook(self, task: dict) -> None:
        if task["id"] in self.tips:
            self.tips.pop(task["id"])
            self.save_tip()

    def task_config_remove_hook(self, task: dict) -> None:
        if task["id"] in self.tips:
            self.tips.pop(task["id"])
            self.save_tip()


class SiteEndTimeTask(BaseTask):

    def __init__(self):
        super().__init__()
        self.source_name = "site_end_time"
        self.template_name = "站点到期提醒"
        self.title = "站点到期提醒"
        self._tip_file = "{}/site_end_time.tip".format(PUSH_DATA_PATH)
        self._tip_data: Optional[dict] = None
        self._task_config = TaskConfig()

        self.push_keys = []
        self.task_id = None

    @property
    def tips(self) -> dict:
        if self._tip_data is not None:
            return self._tip_data
        try:
            self._tip_data = json.loads(read_file(self._tip_file))
        except:
            self._tip_data = {}
        return self._tip_data

    def save_tip(self):
        write_file(self._tip_file, json.dumps(self.tips))

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        task_data["interval"] = 60 * 60 * 24  # 默认检测间隔时间 1 天
        if not (isinstance(task_data['cycle'], int) and task_data['cycle'] >= 1):
            return "剩余时间参数错误，至少为1天"
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return "site_end_time"

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        m_end_date = time.strftime('%Y-%m-%d', time.localtime(time.time() + 86400 * int(task_data['cycle'])))
        web_list = DB('sites').where(
            'edate>? AND edate<? AND (status=? OR status=?)',
            ('0000-00-00', m_end_date, 1, u'正在运行')
        ).field('id,name, edate').select()
        if not (isinstance(web_list, list) and len(web_list) >= 1):
            return None

        total = self._task_config.get_by_id(task_id).get("number_rule", {}).get("total", 1)
        s_list = ['>即将到期：<font color=#ff0000>{} 个站点</font>'.format(len(web_list))]
        for x in web_list:
            if self.tips.get(x['name'], 0) >= total:
                continue
            self.push_keys.append(x['name'])
            s_list.append(">网站：{}  到期：{}".format(x['name'], x[' edate']))

        if not self.push_keys:
            return None

        self.task_id = task_id
        self.title = self.get_title(task_data)
        return {
            "msg_list": s_list
        }

    def check_num_rule(self, num_rule: dict) -> Union[dict, str]:
        num_rule["get_by_func"] = "can_send_by_num_rule"
        return num_rule

    # 实际的次数检查已在 get_push_data 其他位置完成
    def can_send_by_num_rule(self, task_id: str, task_data: dict, number_rule: dict, push_data: dict) -> Optional[str]:
        return None

    def filter_template(self, template) -> dict:
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return '', {}

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "网站到期提醒"
        msg.msg = "有{}个站点即将到期,可能影响网站访问".format(len(self.push_keys))
        msg.next_msg = "请登录面板，在[网站]中查看详情"
        return msg

    def task_run_end_hook(self, res) -> None:
        if not res["do_send"]:
            return
        if self.push_keys:
            for w in self.push_keys:
                if w in self.tips:
                    self.tips[w] += 1
                else:
                    self.tips[w] = 1
            self.save_tip()

    def task_config_update_hook(self, task: dict) -> None:
        if os.path.exists(self._tip_file):
            os.remove(self._tip_file)

    def task_config_remove_hook(self, task: dict) -> None:
        if os.path.exists(self._tip_file):
            os.remove(self._tip_file)


class PanelPwdEndTimeTask(BaseTask):

    def __init__(self):
        super().__init__()
        self.source_name = "panel_pwd_end_time"
        self.template_name = "面板密码有效期"
        self.title = "面板密码有效期"

        self.limit_days = 0

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        task_data["interval"] = 60 * 60 * 24  # 默认检测间隔时间 1 天
        if not (isinstance(task_data['cycle'], int) and task_data['cycle'] >= 1):
            return "剩余时间参数错误，至少为1天"
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return "pwd_end_time"

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        if "/www/server/panel/class" not in sys.path:
            sys.path.insert(0, "/www/server/panel/class")
        import config
        c_obj = config.config()
        res = c_obj.get_password_config(None)
        if res['expire'] > 0 and res['expire_day'] < task_data['cycle']:
            self.limit_days = res['expire_day']

            s_list = [">告警类型：登录密码即将过期",
                      ">剩余天数：<font color=#ff0000>{}  天</font>".format(res['expire_day'])]

            return {
                'msg_list': s_list
            }
        self.title = self.get_title(task_data)
        return None

    def filter_template(self, template) -> dict:
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return '', dict()

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "面板密码到期提醒"
        msg.msg = "登录密码将于{}天后过期".format(self.limit_days)
        msg.next_msg = "请登录面板，在[设置]中修改密码"
        return msg


class PanelLoginTask(BaseTask):
    push_tip_file = "/www/server/panel/data/panel_login_send.pl"

    def __init__(self):
        # import public
        # public.print_log("panel_login")
        super().__init__()
        self.source_name = "panel_login"
        self.template_name = "面板登录告警"
        self.title = "面板登录告警"

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        return {}

    def get_keyword(self, task_data: dict) -> str:
        return "panel_login"

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        return None

    def filter_template(self, template) -> dict:
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return "login_panel|面板登录提醒", {
            'name': push_data.get("ip"),
            'time': time.strftime('%Y-%m-%d %X', time.localtime()),
            'type': '[' + push_data.get("is_type") + ']',
            'user': push_data.get("username")
        }

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountLoginMsg.new_msg()
        msg.thing_type = "面板登录提醒"
        msg.login_name = push_data.get("username")
        msg.login_ip = push_data.get("login_ip")
        msg.login_type = push_data.get("is_type")
        msg.address = push_data.get("login_ip_area")
        return msg

    def task_config_update_hook(self, task: dict) -> None:
        sender = task["sender"]
        if len(sender) > 0:
            send_id = sender[0]
        else:
            return

        sender_data = SenderConfig().get_by_id(send_id)
        if sender_data:
            write_file(self.push_tip_file, sender_data["sender_type"])

    def task_config_create_hook(self, task: dict) -> None:
        sender = task["sender"]
        if len(sender) > 0:
            send_id = sender[0]
        else:
            return

        sender_data = SenderConfig().get_by_id(send_id)
        if sender_data:
            write_file(self.push_tip_file, sender_data["sender_type"])

    def task_config_remove_hook(self, task: dict) -> None:
        if os.path.exists(self.push_tip_file):
            os.remove(self.push_tip_file)


class SSHLoginErrorTask(BaseTask):
    _months = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
               'Sep': '09', 'Sept': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}

    def __init__(self):
        super().__init__()
        self.source_name = "ssh_login_error"
        self.template_name = "SSH登录失败告警"
        self.title = "SSH登录失败告警"

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        if not (isinstance(task_data['cycle'], int) and task_data['cycle'] >= 1):
            return "时间长度参数错误，至少为1分钟"
        if not (isinstance(task_data['count'], int) and task_data['count'] >= 1):
            return "数量参数错误，至少为1次"
        if not (isinstance(task_data['interval'], int) and task_data['interval'] >= 60):
            return "间隔时间参数错误，至少为60秒"
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return "ssh_login_error"

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        import PluginLoader
        args = GET_CLASS()
        args.model_index = 'safe'
        args.count = task_data['count']
        args.p = 1
        res = PluginLoader.module_run("syslog", "get_ssh_error", args)
        if 'status' in res:
            return None

        last_info = res[task_data['count'] - 1]
        if self.to_date(times=last_info['time']) >= time.time() - task_data['cycle'] * 60:
            s_list = [">通知类型：SSH登录失败告警",
                      ">告警内容：<font color=#ff0000>{} 分钟内登录失败超过 {} 次</font> ".format(
                          task_data['cycle'], task_data['count'])]

            return {
                'msg_list': s_list,
                'count': task_data['count']
            }

        return None

    @staticmethod
    def to_date(times, fmt_str="%Y-%m-%d %H:%M:%S"):
        if times:
            if isinstance(times, int):
                return times
            if isinstance(times, float):
                return int(times)
            if re.match(r"^\d+$", times):
                return int(times)
        else:
            return 0
        ts = time.strptime(times, fmt_str)
        return time.mktime(ts)

    def filter_template(self, template) -> dict:
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return '', dict()

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "SSH登录失败告警"
        msg.msg = "登录失败超过{}次".format(push_data['count'])
        msg.next_msg = "请登录面板，查看SSH登录日志"
        return msg


class ServicesTask(BaseTask):

    def __init__(self):
        super().__init__()
        self.source_name = "services"
        self.template_name = "服务停止告警"

        self.pids = None

        self.service_name = ''
        self.restart = None

    @staticmethod
    def services_list() -> Tuple[str, List]:
        res_list = []
        default = None
        php_path = "/www/server/php"
        if os.path.exists(php_path) and glob.glob(php_path + "/*"):
            res_list.append({
                "title": "php-fpm服务停止",
                "value": "php-fpm"
            })
        if os.path.exists('/etc/init.d/httpd'):
            default = "apache"
            res_list.append({
                "title": "apache服务停止",
                "value": "apache"
            })
        if os.path.exists('/etc/init.d/nginx'):
            default = "nginx"
            res_list.append({
                "title": "nginx服务停止",
                "value": "nginx"
            })
        if os.path.exists('/etc/init.d/mysqld'):
            res_list.append({
                "title": "mysql服务停止",
                "value": "mysql"
            })
        if os.path.exists('/www/server/tomcat/bin'):
            res_list.append({
                "title": "tomcat服务停止",
                "value": "tomcat"
            })
        if os.path.exists('/etc/init.d/pure-ftpd'):
            res_list.append({
                "title": "pure-ftpd服务停止",
                "value": "pure-ftpd"
            })
        if os.path.exists('/www/server/redis'):
            res_list.append({
                "title": "redis服务停止",
                "value": "redis"
            })
        if os.path.exists('/etc/init.d/memcached'):
            res_list.append({
                "title": "memcached服务停止",
                "value": "memcached"
            })
        if not default:
            if res_list:
                default = res_list[0]["value"]
            else:
                default=""
        return default, res_list

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        default, s_list = self.services_list()
        if task_data["project"] not in {i["value"] for i in s_list}:
            return "所选择的服务不存在"
        if task_data["count"] not in (1, 2):
            return "自动重启选择错误"
        if not (isinstance(task_data['interval'], int) and task_data['interval'] >= 60):
            return "间隔时间参数错误，至少为60秒"
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return task_data["project"]

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        self.title = self.get_title(task_data)
        ser_name = task_data['project']
        default, server_list = self.services_list()
        if ser_name not in [v["value"] for v in server_list]:
            return None
        if self.get_server_status(ser_name):
            return None

        s_list = [
            ">服务类型：" + task_data["project"],
            ">服务状态：【" + task_data["project"] + "】服务已停止"]

        self.service_name = task_data["project"]

        if task_data["count"] == 1:
            self._services_start(task_data["project"])
            if not self.get_server_status(task_data["project"]):
                self.restart = False
                s_list[1] = ">服务状态：【" + task_data["project"] + "】服务重启失败"
            else:
                self.restart = True
                s_list[1] = ">服务状态：【" + task_data["project"] + "】服务重启成功"

        return {
            "msg_list": s_list
        }

    def get_title(self, task_data: dict) -> str:
        return task_data["project"] + "服务停止告警"

    @staticmethod
    def _services_start(service_name: str):
        if service_name == "php-fpm":
            base_path = "/www/server/php"
            if not os.path.exists(base_path):
                return None
            for p in os.listdir(base_path):
                init_file = os.path.join("/etc/init.d", "php-fpm-{}".format(p))
                if not os.path.isfile(init_file):
                    return None
                ExecShell("{} start".format(init_file))
        elif service_name == 'mysql':
            init_file = os.path.join("/etc/init.d", "mysqld")
            ExecShell("{} start".format(init_file))

        elif service_name == 'apache':
            init_file = os.path.join("/etc/init.d", "httpd")
            ExecShell("{} start".format(init_file))

        else:
            init_file = os.path.join("/etc/init.d", service_name)
            ExecShell("{} start".format(init_file))

    def get_pid_name(self, pname):
        try:
            if not self.pids:
                self.pids = psutil.pids()
            for pid in self.pids:
                if psutil.Process(pid).name() == pname: return True
            return False
        except:
            return True

    def get_server_status(self, name: str) -> bool:
        # time.sleep(5)
        if name == "php-fpm":
            base_path = "/www/server/php"
            if not os.path.exists(base_path):
                return False
            for p in os.listdir(base_path):
                pid_file = os.path.join(base_path, p, "var/run/php-fpm.pid")
                if os.path.exists(pid_file):
                    php_pid = int(read_file(pid_file))
                    status = self.check_process(php_pid)
                    if status:
                        return True
            return False

        elif name == 'nginx':
            if os.path.exists('/etc/init.d/nginx'):
                pid_f = '/www/server/nginx/logs/nginx.pid'
                if os.path.exists(pid_f):
                    try:
                        pid = read_file(pid_f)
                        print('/www/server/nginx/logs/nginx.pid', pid)
                        return self.check_process(pid)
                    except:
                        pass
            return False

        elif name == 'apache':
            if os.path.exists('/etc/init.d/httpd'):
                pid_f = '/www/server/apache/logs/httpd.pid'
                if os.path.exists(pid_f):
                    pid = read_file(pid_f)
                    return self.check_process(pid)
            return False

        elif name == 'mysql':
            if os.path.exists('/tmp/mysql.sock'):
                return True
            return False

        elif name == 'tomcat':
            status = False
            if os.path.exists('/www/server/tomcat/logs/catalina-daemon.pid'):
                if self.get_pid_name('jsvc'):
                    status = True
            if not status:
                if self.get_pid_name('java'):
                    status = True
            return status

        elif name == 'pure-ftpd':
            pid_f = '/var/run/pure-ftpd.pid'
            if os.path.exists(pid_f):
                pid = read_file(pid_f)
                return self.check_process(pid)
            return False

        elif name == 'redis':
            pid_f = '/www/server/redis/redis.pid'
            if os.path.exists(pid_f):
                pid = read_file(pid_f)
                return self.check_process(pid)
            return False

        elif name == 'memcached':
            pid_f = '/var/run/memcached.pid'
            if os.path.exists(pid_f):
                pid = read_file(pid_f)
                return self.check_process(pid)
            return False

        return True

    def check_process(self, pid):
        try:
            return psutil.pid_exists(int(pid))
        except Exception as e:
            return False

    def filter_template(self, template: dict) -> Optional[dict]:
        default, server_list = self.services_list()
        if not server_list:
            return None
        template["field"][0]["items"] = server_list
        template["field"][0]["default"] = default
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return "servcies|{}".format(self.title), {
            'name': '{}'.format(get_config_value('title')),
            'product': self.service_name,
            'product1': self.service_name
        }

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        if len(self.service_name) > 14:
            service_name = self.service_name[:11] + "..."
        else:
            service_name = self.service_name
        msg.thing_type = "{}服务停止提醒".format(service_name)
        if self.restart is None:
            msg.msg = "{}服务已停止".format(service_name)
        elif self.restart is True:
            msg.msg = "{}服务重启成功".format(service_name)
        else:
            msg.msg = "{}服务重启失败".format(service_name)
        return msg


class PanelSafePushTask(BaseTask):
    def __init__(self):
        super().__init__()
        self.source_name = "panel_safe_push"
        self.template_name = "面板安全告警"
        self.title = "面板安全告警"

        self.msg_list = []

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        task_data["interval"] = 60
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return "panel_safe_push"

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        s_list = []
        # 面板登录用户安全
        t_add, t_del, total = self.get_records_calc('login_user_safe', DB('users'))
        if t_add > 0 or t_del > 0:
            s_list.append(
                ">登录用户变更：<font color=#ff0000>总 {} 个，新增 {} 个 ，删除 {} 个</font>.".format(total, t_add, t_del))

        # 面板日志发生删除
        t_add, t_del, total = self.get_records_calc('panel_logs_safe', DB('logs'), 1)
        if t_del > 0:
            s_list.append(">面板日志发生删除，删除条数：<font color=#ff0000>{} 条</font>".format(t_del))

        debug_str = '关闭'
        debug_status = 'False'
        # 面板开启开发者模式告警
        if os.path.exists('/www/server/panel/data/debug.pl'):
            debug_status = 'True'
            debug_str = '开启'

        skey = 'panel_debug_safe'
        tmp = public_get_cache_func(skey)['data']
        if not tmp:
            public_set_cache_func(skey, debug_status)
        else:
            if str(debug_status) != tmp:
                s_list.append(">面板开发者模式发生变更，当前状态：{}".format(debug_str))
                public_set_cache_func(skey, debug_status)

        # 面板用户名和密码发生变更
        find = DB('users').where('id=?', (1,)).find()
        if find:
            skey = 'panel_user_change_safe'
            user_str = self.hash_md5(find['username']) + '|' + self.hash_md5(find['password'])
            tmp = public_get_cache_func(skey)['data']
            if not tmp:
                public_set_cache_func(skey, user_str)
            else:
                if user_str != tmp:
                    s_list.append(">面板登录帐号或密码发生变更")
                    public_set_cache_func(skey, user_str)

        if len(s_list) == 0:
            return None
        self.msg_list = s_list
        return {"msg_list": s_list}

    @staticmethod
    def hash_md5(data: str) -> str:
        h = hashlib.md5()
        h.update(data.encode('utf-8'))
        return h.hexdigest()

    @staticmethod
    def get_records_calc(skey, table, stype=0):
        """
            @name 获取指定表数据是否发生改变
            @param skey string 缓存key
            @param table db 表对象
            @param stype : 0 计算总条数 1 只计算删除
            @return array
                total int 总数
        """
        total_add = 0
        total_del = 0

        # 获取当前总数和最大索引值
        u_count = table.count()
        u_max = table.order('id desc').getField('id')

        n_data = {'count': u_count, 'max': u_max}
        tmp = public_get_cache_func(skey)['data']
        if not tmp:
            public_set_cache_func(skey, n_data)
        else:
            n_data = tmp
            # 检测上一次记录条数是否被删除
            pre_count = table.where('id<=?', (n_data['max'])).count()
            if stype == 1:
                if pre_count < n_data['count']:  # 有数据被删除，记录被删条数
                    total_del += n_data['count'] - pre_count

                n_count = u_max - pre_count  # 上次记录后新增的条数
                n_idx = u_max - n_data['max']  # 上次记录后新增的索引差
                if n_count < n_idx:
                    total_del += n_idx - n_count
            else:

                if pre_count < n_data['count']:  # 有数据被删除，记录被删条数
                    total_del += n_data['count'] - pre_count
                elif pre_count > n_data['count']:
                    total_add += pre_count - n_data['count']

                t1_del = 0
                n_count = u_count - pre_count  # 上次记录后新增的条数

                if u_max > n_data['max']:
                    n_idx = u_max - n_data['max']  # 上次记录后新增的索引差
                    if n_count < n_idx: t1_del = n_idx - n_count

                # 新纪录除开删除，全部计算为新增
                t1_add = n_count - t1_del
                if t1_add > 0:
                    total_add += t1_add

                total_del += t1_del

            public_set_cache_func(skey, {'count': u_count, 'max': u_max})
        return total_add, total_del, u_count

    def filter_template(self, template: dict) -> Optional[dict]:
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return '', {}

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "面板安全告警"
        the_msg = []
        for d in self.msg_list:
            if d.find("用户变更"):
                the_msg.append("用户变更")
            if d.find("日志发生删除"):
                the_msg.append("面板日志删除")
            if d.find("开发者模式"):
                the_msg.append("开发者模式变更")
            if d.find("登录帐号或密码"):
                the_msg.append("帐号密码变更")

        msg.msg = "、".join(the_msg)
        if len(the_msg) > 20:
            msg.msg = msg.msg[:17] + "..."
        msg.next_msg = "请登录面板，查看对应事项"
        return msg


class SSHLoginTask(BaseTask):
    push_tip_file = "/www/server/panel/data/ssh_send_type.pl"

    def __init__(self):
        super().__init__()
        self.source_name = "ssh_login"
        self.template_name = "SSH登录告警"
        self.title = "SSH登录告警"

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        return {}

    def get_keyword(self, task_data: dict) -> str:
        return "ssh_login"

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        return None

    def filter_template(self, template) -> dict:
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return "", {}

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        login_ip = push_data.get("login_ip")
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "SSH登录安全告警"
        if len(login_ip) == 0:  # 检查后门用户时使同
            msg.msg = "服务器存在后门用户"
            msg.next_msg = "请检查/ect/passwd文件"
            return msg

        elif len(login_ip) > 15:
            login_ip = login_ip[:12] + "..."

        msg.msg = "登录ip:{}".format(login_ip)
        msg.next_msg = "请登录面板，检查是否为安全登录"
        return msg

    def task_config_update_hook(self, task: dict) -> None:
        if "/www/server/panel/class" not in sys.path:
            sys.path.insert(0, "/www/server/panel/class")

        from ssh_security import ssh_security
        ssh_security().start_jian(None)

        sender = task["sender"]
        if len(sender) > 0:
            send_id = sender[0]
        else:
            return

        sender_data = SenderConfig().get_by_id(send_id)
        if sender_data:
            write_file(self.push_tip_file, sender_data["sender_type"])

    def task_config_create_hook(self, task: dict) -> None:
        return self.task_config_update_hook(task)

    def task_config_remove_hook(self, task: dict) -> None:
        if os.path.exists(self.push_tip_file):
            os.remove(self.push_tip_file)


class PanelUpdateTask(BaseTask):

    def __init__(self):
        super().__init__()
        self.source_name = "panel_update"
        self.template_name = "面板更新提醒"
        self.title = "面板更新提醒"
        self.new_ver = ''

    def _get_no_user_tip(self) -> str:
        """没有用户信息的需要，写一个临时文件做标记，并尽可能保持不变"""
        tip_file = "/www/server/panel/data/no_user_tip.pl"
        if not os.path.exists(tip_file):
            data: str = get_network_ip()
            data = "没有用户信息时的标记文件\n" + hashlib.sha256(data.encode("utf-8")).hexdigest()
            write_file(tip_file, data)
        else:
            data = read_file(tip_file)
            if isinstance(data, bool):
                os.remove(tip_file)
                return self._get_no_user_tip()
        return data

    def user_can_request_hour(self):
        """根据哈希值，输出一个用户可查询"""
        user_info = public_get_user_info()
        if not bool(user_info):
            user_info_str = self._get_no_user_tip()
        else:
            user_info_str = json.dumps(user_info)

        hash_value = hashlib.md5(user_info_str.encode("utf-8")).digest()
        sum_value = 0
        for i in range(4):
            sum_value = sum_value + int.from_bytes(hash_value[i * 32: (i + 1) * 32], "big")

        res = sum_value % 24
        return res

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        task_data["interval"] = 60 * 60  # 默认检测间隔时间 1 小时
        return task_data

    def check_num_rule(self, num_rule: dict) -> Union[dict, str]:
        num_rule['day_num'] = 1  # 默认一天发一次
        return num_rule

    def get_keyword(self, task_data: dict) -> str:
        return "panel_update"

    @property
    def is_stable_version(self) -> int:
        """判断版本是否是稳定版本, 如果是稳定版返回稳定版主版本号，否则返回0，表示正式版"""
        ver = panel_version()
        ver_mian = int(ver.split(".")[0])
        if ver_mian % 2 == 0 and ver_mian > 9:
            return ver_mian
        return 0

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        # 不在固定时间段内，跳过
        if self.user_can_request_hour() != datetime.now().hour:
            return None
        sub_path = "/api/panel/get_panel_version_v3"
        if self.is_stable_version:
            sub_path = "/api/panel/get_stable_panel_version_v3"
        try:
            res = json.loads(read_file('/www/server/panel/data/node_url.pl'))
            www_url = res['www-node']['url']
            s_url = 'https://{}{}'.format(www_url, sub_path)
        except:
            s_url = 'https://www.bt.cn{}'.format(sub_path)
        try:
            res = json.loads(public_http_post(s_url, {}))
            # print(res)
            if not res:
                return None
            n_ver = res['OfficialVersion']["version"]
        except:
            traceback.print_exc()
            return None

        n_main = int(n_ver.split(".")[0])
        if self.is_stable_version:  # 稳定版主版本号必须一致才提示更新
            if n_main != self.is_stable_version:
                return None
        now_version = panel_version()
        # print("now_version:", now_version, "new_ver:", n_ver)
        # 新版本大于当前版本在做后续判断, 否则不推送
        if not self.version_large(n_ver, now_version):
            return None

        self.new_ver = n_ver
        cache_key = "panel_update_cache"
        old_ver = public_get_cache_func(cache_key)['data']
        if (old_ver and old_ver != n_ver) or not old_ver:
            s_list = [">通知类型：面板版本更新",
                      ">当前版本：{} ".format(now_version),
                      ">最新版本：{}".format(n_ver)]
            return {
                "msg_list": s_list
            }
        public_set_cache_func(cache_key, n_ver)
        return None

    @staticmethod
    def version_large(new_ver: str, old_ver: str) -> bool:
        if not new_ver or not old_ver:
            return False
        new_ver_list = new_ver.split(".")
        old_ver_list = old_ver.split(".")
        if len(new_ver_list) < 3:
            new_ver_list.extend(["0"] * (3 - len(new_ver_list)))
        if len(old_ver_list) < 3:
            old_ver_list.extend(["0"] * (3 - len(old_ver_list)))
        for i in range(3):
            if int(new_ver_list[i]) > int(old_ver_list[i]):
                return True
        return False

    def filter_template(self, template: dict) -> Optional[dict]:
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return "", {}

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "面板更新提醒"
        msg.msg = "最新版:{}已发布".format(self.new_ver)
        msg.next_msg = "您可以登录面板，执行更新"
        return msg

    def task_run_end_hook(self, res: dict) -> None:
        if res["do_send"]:
            public_set_cache_func("panel_update_cache", self.new_ver)


class ProjectStatusTask(BaseTask):

    def __init__(self):
        super().__init__()
        self.source_name = "project_status"
        self.template_name = "项目停止告警"

        self.project_name = ''
        self.restart = None

    @staticmethod
    def _to_project_type(type_id: int):
        if type_id == 1:
            return "Java"
        elif type_id == 2:
            return "Node"
        elif type_id == 3:
            return "Go"
        elif type_id == 4:
            return "Python"
        elif type_id == 5:
            return "Other"

    @staticmethod
    def _to_project_id(type_name):
        if type_name == "Java":
            return 0
        elif type_name == "Node":
            return 1
        elif type_name == "Go":
            return 2
        elif type_name == "Python":
            return 3
        elif type_name == "Other":
            return 4

    @staticmethod
    def _to_project_model(type_id: int):
        if type_id == 1:
            return "javaModel"
        elif type_id == 2:
            return "nodejsModel"
        elif type_id == 3:
            return "goModel"
        elif type_id == 4:
            return "pythonModel"
        elif type_id == 5:
            return "otherModel"

    def get_title(self, task_data: dict) -> str:
        return "项目{}停止告警".format(self._get_project_name(task_data["project"]))

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        if not (isinstance(task_data["cycle"], int) and 1 <= task_data["cycle"] <= 5):
            return '不支持的项目类型.'
        sql = DB("sites")
        web_info = sql.where(
            "project_type = ? and id = ?",
            (self._to_project_type(task_data["cycle"]), task_data["project"])
        ).field("id,name").find()

        if not web_info:
            return '没有该项目，不可设置告警'

        if task_data["count"] not in (1, 2):
            return "自动重启选择错误"
        if not (isinstance(task_data['interval'], int) and task_data['interval'] >= 60):
            return "间隔时间参数错误，至少为60秒"
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return "{}_{}".format(task_data["cycle"], self._get_project_name(task_data["project"]))

    @staticmethod
    def _get_project_name(project_id: int) -> str:
        data = DB('sites').where('id = ?', (project_id,)).field('id,name').find()
        if isinstance(data, dict):
            return data["name"]
        return "<unknown>"

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        if "/www/server/panel/class" not in sys.path:
            sys.path.insert(0, "/www/server/panel/class")
        if self._to_project_model(task_data["cycle"]) == "javaModel":
            from mod.project.java.projectMod import main
            model_main_obj = main()
        else:
            model_obj = import_module(".{}".format(self._to_project_model(task_data["cycle"])), package="projectModel")
            model_main_obj = model_obj.main()
        try:
            running, project_name = getattr(model_main_obj, "get_project_status")(task_data["project"])
            if running is not False:
                return None
        except:
            return None

        s_list = [
            ">项目类型：" + self._to_project_type(task_data["cycle"]) + "项目",
            ">项目名称：" + project_name,
            ">项目状态：检查到项目状态为停止"]
        self.project_name = project_name

        if int(task_data["count"]) == 1:
            get_obj = GET_CLASS()
            get_obj.project_name = project_name
            result = getattr(model_main_obj, "start_project")(get_obj)
            if result["status"] is True:
                self.restart = True
                s_list[2] = ">项目状态：检查到项目状态为停止，现已重启成功"
            else:
                self.restart = False
                s_list[2] = ">项目状态：检查到项目状态为停止，尝试重启但失败"

        self.title = self.get_title(task_data)

        return {
            "msg_list": s_list,
        }

    def filter_template(self, template: dict) -> Optional[dict]:
        supported = ("Java", "Node", "Go", "Python", "Other")
        _, web_by_type_map = web_info_data(project_types=supported)
        web_by_type = [[] for _ in range(len(supported))]
        for i, web_list in web_by_type_map.items():
            web_by_type[self._to_project_id(i)] = web_list
        template["field"][1]["all_items"] = web_by_type
        template["field"][1]["items"] = web_by_type[0]
        if not web_by_type:
            return None
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return '', {}

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        if len(self.project_name) >= 14:
            project_name = self.project_name[:11] + "..."
        else:
            project_name = self.project_name
        msg.thing_type = "项目停止告警"
        if self.restart is None:
            msg.msg = "项目{}已停止".format(project_name)
        elif self.restart is True:
            msg.msg = "项目{}重启成功".format(project_name)
        else:
            msg.msg = "项目{}重启失败".format(project_name)
        return msg


class ViewMsgFormat(BaseTaskViewMsg):
    _FORMAT = {
        "1": (
            lambda x: "<span>剩余时间小于{}天{}</span>".format(
                x["task_data"].get("cycle"),
                ("(如未处理，次日会重新发送1次，持续%d天)" % x.get("number_rule", {}).get("total", 0)) if x.get("number_rule", {}).get("total", 0) else ""
            )
        ),
        "2": (),
        "3": (),
        "8": (
            lambda x: "<span>面板登录时，发出告警</span>"
        ),
        "7": (
            lambda x: "<span>检测到SSH登录本机时，发出告警</span>"
        ),
        "4": (
            lambda x: "<span>{}分钟内连续{}次失败登录触发,每{}秒后再次检测</span>".format(
                x["task_data"].get("cycle"), x["task_data"].get("count"), x["task_data"].get("interval"),
            )
        ),
        "5": (
            lambda x: "<span>服务停止时发送一次通知,{}秒后再次检测</span>".format(x["task_data"].get("interval"))
        ),
        "9": (
            lambda x: "<span>项目停止时发送通知，{}秒后再次检测，每日发送{}次</span>".format(
                x["task_data"].get("interval"),
                x.get("number_rule", {}).get("day_num", 0))
        ),
        "6": (
            lambda x: "<span>面板出现如:用户变更、面板日志删除、开启开发者等危险操作时发送告警</span>"
        ),
        "10": (
            lambda x: "<span>检测到新的版本时发送一次通知</span>"
        )
    }

    def get_msg(self, task: dict) -> Optional[str]:
        if task["template_id"] in ["1", "2", "3"]:
            return self._FORMAT["1"](task)
        if task["template_id"] in self._FORMAT:
            return self._FORMAT[task["template_id"]](task)
        return None


SSLTask.VIEW_MSG = SiteEndTimeTask.VIEW_MSG = PanelPwdEndTimeTask.VIEW_MSG = PanelLoginTask.VIEW_MSG = \
    SSHLoginErrorTask.VIEW_MSG = ServicesTask.VIEW_MSG = PanelSafePushTask.VIEW_MSG = SSHLoginTask.VIEW_MSG = \
    PanelUpdateTask.VIEW_MSG = ProjectStatusTask.VIEW_MSG = ViewMsgFormat