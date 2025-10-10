# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Windows面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2020 宝塔软件(https://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: baozi <1191604998@qq.com>
# +-------------------------------------------------------------------
import json
import os
import sys
import time
import datetime
import psutil
import threading

class_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# /www/server/panel/class
bt_panel_path = os.path.dirname(class_path)
sys.path.insert(0, class_path)
sys.path.insert(0, bt_panel_path)
import public
import panelPush
from push.base_push import base_push, WxAccountMsg
from panel_msg.collector import SystemPushMsgCollect


class system_push(base_push):
    __push_conf = "{}/class/push/push.json".format(public.get_panel_path())
    __task_template = "{}/push/scripts/system_push.json"

    def __init__(self):
        self.__push = panelPush.panelPush()

        # 缓存硬盘信息，使一次检查之内不用频繁查询磁盘（磁盘有多个，可以设置多个）
        self._disk_info = None

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
        item['cycle'] = 30
        item['title'] = '防篡改'
        data.append(item)
        return data

    # 获取模块配置项
    def get_push_config(self, get: public.dict_obj):
        task_id = get.id
        push_list = self.__push._get_conf()

        if task_id not in push_list["system_push"]:
            res_data = public.returnMsg(False, '未找到指定配置.')
            res_data['code'] = 100
            return res_data
        result = push_list["system_push"][task_id]
        return result

    @staticmethod
    def clear_push_count(task_id):
        """清除推送次数"""
        task_data_cache.set("tip_" + task_id, [])
        task_data_cache.save_cache()

    @staticmethod
    def _get_can_next():
        ws = public.get_webserver()
        default = None
        res_list = []
        if os.path.exists('/etc/init.d/nginx'):
            if ws == "nginx":
                default = "nginx"
            res_list.append({
                "title": "重启nginx服务",
                "value": "nginx"
            })
        if os.path.exists('/etc/init.d/httpd'):
            if ws == "apache":
                default = "apache"
            res_list.append({
                "title": "重启apache服务",
                "value": "apache"
            })
        if os.path.exists('/etc/init.d/mysqld'):
            res_list.append({
                "title": "重启mysql服务",
                "value": "mysql"
            })
        if os.path.exists('/www/server/redis'):
            res_list.append({
                "title": "重启redis服务",
                "value": "redis"
            })
        if os.path.exists('/etc/init.d/memcached'):
            res_list.append({
                "title": "重启memcached服务",
                "value": "memcached"
            })

        php_path = "/www/server/php"
        if os.path.exists(php_path):
            for k in os.listdir(php_path):
                if k.isnumeric():
                    res_list.append({
                        "title": "重启php" + k,
                        "value": "php" + k
                    })

        if not res_list:
            return None, None
        if not default:
            default = res_list[0]["value"]
        return res_list, default

    def _check_next_data(self, next_data):
        if not isinstance(next_data, list):
            return public.returnMsg(False, "后置操作设置错误")

        res_list, _ = self._get_can_next()
        if res_list is None:
            return public.returnMsg(False, "后置操作设置错误")

        can_use = [i["value"] for i in res_list]

        for i in next_data:
            if i not in can_use:
                return public.returnMsg(False, "后置操作设置错误， 不存在的值：{}".format(i))
        return None

    # 写入推送配置文件
    def set_push_config(self, get: public.dict_obj):
        pdata = json.loads(get.data)
        task_id = get.id
        conf_data = self.__push._get_conf()
        if "system_push" not in conf_data:
            conf_data["system_push"] = dict()
        # 检查输入参数是否合理:
        if "cycle" in pdata and not (1 <= pdata["cycle"] <= 15):
            return public.returnMsg(False, "检查时长大于15分钟不利于发现问题")
        if "count" in pdata:
            if pdata["type"] == "disk" and pdata["cycle"] == 2:
                if not 0 < pdata["count"] < 100:
                    return public.returnMsg(False, "设置的检查范围不正确")
            if pdata["type"] != "disk" and not 0 < pdata["count"] < 100:
                return public.returnMsg(False, "设置的检查范围不正确")
        
        if "next_data" in pdata:
            res = self._check_next_data(pdata["next_data"])
            if isinstance(res, dict):
                return res

        # 处理检查特殊情况 -> 可以直接查出平均值:
        if pdata["type"] == "load":
            pdata["interval"] = pdata["cycle"] * 60
        elif pdata["type"] != "disk":
            pdata["interval"] = 60

        for conf_id, task in conf_data["system_push"].items():
            # 已存在的做修改
            if task["type"] == pdata["type"] and task["project"] == pdata["project"]:
                task["interval"] = pdata["interval"]
                task["module"] = pdata["module"]
                task["push_count"] = pdata["push_count"]
                task["cycle"] = pdata["cycle"]
                task["count"] = pdata["count"]
                if "next_data" in pdata:
                    task["next_data"] = pdata["next_data"]
                task["status"] = True  # 设置后自动开启

                self.clear_push_count(conf_id)
                break
        else:
            # 不存在的做添加
            # 磁盘告警需要通过挂载目录指定
            project_name = pdata.get("project", "").strip()
            if pdata["type"] == "disk" and not (project_name in self._get_disk_name() or project_name != "@any"):
                return public.returnMsg(False, "指定的磁盘不存在")
            if pdata["type"] == "disk":
                title = "任意磁盘余量" if project_name == "@any" else "挂载目录【{}】的磁盘余量告警".format(project_name)
            elif pdata["type"] == "cpu":
                title = "CPU占用过高告警"
            elif pdata["type"] == "mem":
                title = "内存占用过高告警"
            else:
                title = "负载过高告警"
            pdata["status"] = True
            pdata["title"] = title

            conf_data["system_push"][str(task_id)] = pdata

        public.set_module_logs("system_push", "set_push_config", 1)

        return conf_data

    # 删除推送配置
    def del_push_config(self, get: public.dict_obj):
        # 从配置中删除信息，并做一些您想做的事，如记日志
        task_id = get.id
        data = self.__push._get_conf()
        if str(task_id).strip() in data["system_push"]:
            del data["system_push"][task_id]
        public.writeFile(self.__push_conf, json.dumps(data))
        return public.returnMsg(True, '删除成功.')

    def get_total(self):
        return True

    # 检查并获取推送消息，返回空时，不做推送, 传入的data是配置项
    def get_push_data(self, data, total):
        # data 内容
        # index :  时间戳 time.time()
        # 消息 以类型为key， 以内容为value， 内容中包含title 和msg
        # push_keys： 列表，发送了信息的推送任务的id，用来验证推送任务次数（） 意义不大
        tip_list = task_data_cache.get("tip_" + data["id"])
        if tip_list is None:
            tip_list = []
        today = datetime.date.today()
        try:
            for i in range(len(tip_list)-1, -1, -1):
                tip_time = datetime.datetime.fromtimestamp(float(tip_list[i]))
                if tip_time.date() < today:
                    del tip_list[i]
        except ValueError:
            tip_list = []
        if 0 < data["push_count"] <= len(tip_list):
            return None
        if data["type"] == "disk":
            return self._get_disk_push_data(data, tip_list)
        elif data["type"] == "cpu":
            return self._get_cpu_push_data(data, tip_list)
        elif data["type"] == "load":
            return self._get_load_push_data(data, tip_list)
        else:
            return self._get_mem_push_data(data, tip_list)

    def _get_disk_push_data(self, task_data, tip_list):
        stime = time.time()
        result = {'index': stime, 'push_keys': [stime, ]}
        disk_info = self._get_disk_info()
        unsafe_disk_list = []
        wx_msg = ""
        for d in disk_info:
            if task_data["project"] != "@any" and task_data["project"] != d["path"]:
                continue
            free = int(d["size"][2]) / 1048576
            proportion = int(d["size"][3] if d["size"][3][-1] != "%" else d["size"][3][:-1])
            if task_data["cycle"] == 1 and free < task_data["count"]:
                unsafe_disk_list.append(
                    "挂载在【{}】上的磁盘剩余容量为{}G，小于告警值{}G.".format(
                        d["path"], round(free, 2), task_data["count"])
                )
                wx_msg = "剩余容量小于{}G".format(task_data["count"])
            if task_data["cycle"] == 2 and proportion > task_data["count"]:
                unsafe_disk_list.append(
                    "挂载在【{}】上的磁盘已使用容量为{}%，大于告警值{}%.".format(
                        d["path"], round(proportion, 2), task_data["count"])
                )
                wx_msg = "占用量大于{}%".format(task_data["count"])
                
        if len(unsafe_disk_list) == 0:
            return None

        s_list = [
            ">通知类型：磁盘余量告警",
            ">告警内容:\n" + "\n".join(unsafe_disk_list)]
        msg = SystemPushMsgCollect.system_disk(s_list, task_data["title"])
        sdata = public.get_push_info('磁盘余量告警', s_list)
        sdata["push_type"] = "首页磁盘告警"
        for m_module in task_data['module'].split(','):
            if m_module == 'sms':
                sdata = {
                    'sm_type': 'machine_exception',
                    'sm_args': public.check_sms_argv({
                        'name': self._get_panel_name(),
                        'type': "磁盘空间不足",
                    })}
                result[m_module] = sdata
                continue
            elif m_module == 'wx_account':
                result[m_module] = ToWechatAccountMsg.system_disk(wx_msg, task_data['project'])
                continue

            result[m_module] = sdata

        tip_list.append(result["index"])
        task_data_cache.set("tip_" + task_data["id"], tip_list)
        return result

    def _get_cpu_push_data(self, task_data, tip_list):
        stime = datetime.datetime.now()
        result = {'index': stime.timestamp(), 'push_keys': [stime.timestamp(), ]}
        cache_key = "cpu_push_data"
        # 清除过期的缓存
        expiration = stime - datetime.timedelta(seconds=task_data["cycle"] * 60 + 10)
        cache_list = task_data_cache.get(cache_key)
        if cache_list is None:
            cache_list = []

        for i in range(len(cache_list)-1, -1, -1):
            data_time, _ = cache_list[i]
            if datetime.datetime.fromtimestamp(data_time) < expiration:
                del cache_list[i]

        # 记录下次的
        cache_list.append((time.time(), psutil.cpu_percent(1)))
        task_data_cache.set(cache_key, cache_list)

        if len(cache_list) < task_data["cycle"]:  # 小于指定次数不推送
            return None

        if len(cache_list) > 0:
            avg_data = sum(i[1] for i in cache_list) / len(cache_list)
        else:
            avg_data = 0

        if avg_data < task_data["count"]:
            return None
        else:
            cache_list = []
        
        next_msg = ""
        if "next_data" in task_data and task_data["next_data"]:
            next_msg = self.do_next_data(task_data["next_data"])

        s_list = [
            ">通知类型：CPU高占用告警",
            ">告警内容：最近{}分钟内机器CPU平均占用率为{}%，高于告警值{}%".format(
                task_data["cycle"], round(avg_data, 2), task_data["count"]),
            next_msg
        ]
        SystemPushMsgCollect.system_cpu(s_list, task_data['title'])
        sdata = public.get_push_info('CPU高占用告警', s_list)
        sdata["push_type"] = "首页CPU告警"
        for m_module in task_data['module'].split(','):
            if m_module == 'sms':
                sdata = {
                    'sm_type': 'machine_exception',
                    'sm_args': public.check_sms_argv({
                        'name': self._get_panel_name(),
                        'type': "CPU高占用",
                    })}
                result[m_module] = sdata
                continue
            elif m_module == 'wx_account':
                result[m_module] = ToWechatAccountMsg.system_cpu(round(avg_data, 2))
                continue

            result[m_module] = sdata

        tip_list.append(result["index"])
        task_data_cache.set("tip_" + task_data["id"], tip_list)
        return result

    def _get_load_push_data(self, task_data, tip_list):
        stime = time.time()
        result = {'index': stime, 'push_keys': [stime, ]}
        now_load = os.getloadavg()
        cpu_count = psutil.cpu_count()
        now_load = [i/(cpu_count * 2) * 100 for i in now_load]
        need_push = False
        avg_data = 0
        if task_data["cycle"] == 15 and task_data["count"] < now_load[2]:
            avg_data = now_load[2]
            need_push = True
        elif task_data["cycle"] == 5 and task_data["count"] < now_load[1]:
            avg_data = now_load[1]
            need_push = True
        elif task_data["cycle"] == 1 and task_data["count"] < now_load[0]:
            avg_data = now_load[0]
            need_push = True

        if need_push is False:
            return None

        next_msg = ""
        if "next_data" in task_data:
            next_msg = self.do_next_data(task_data["next_data"])

        s_list = [
            ">通知类型：负载超标告警",
            ">告警内容：最近{}分钟内机器平均负载率为{}%，高于{}%告警值".format(
                task_data["cycle"], round(avg_data, 2), task_data["count"]),
            next_msg
        ]
        SystemPushMsgCollect.system_load(s_list, task_data['title'])
        sdata = public.get_push_info('负载超标告警', s_list)
        sdata["push_type"] = "首页负载告警"
        for m_module in task_data['module'].split(','):
            if m_module == 'sms':
                sdata = {
                    'sm_type': 'machine_exception',
                    'sm_args': public.check_sms_argv({
                        'name': self._get_panel_name(),
                        'type': "平均负载过高",
                    })}
                result[m_module] = sdata
                continue

            elif m_module == 'wx_account':
                result[m_module] = ToWechatAccountMsg.system_load(round(avg_data, 2))
                continue

            result[m_module] = sdata

        tip_list.append(result["index"])
        task_data_cache.set("tip_" + task_data["id"], tip_list)
        return result

    def _get_mem_push_data(self, task_data, tip_list):
        stime = datetime.datetime.now()
        result = {'index': stime.timestamp(), 'push_keys': []}
        mem = psutil.virtual_memory()
        real_used = (mem.total - mem.free - mem.buffers - mem.cached) / mem.total
        expiration = stime - datetime.timedelta(seconds=task_data["cycle"] * 60 + 10)

        cache_key = "mem_push_data"

        cache_list = task_data_cache.get(cache_key)
        if cache_list is None:
            cache_list = [(stime.timestamp(), real_used)]
        else:
            cache_list.append((stime.timestamp(), real_used))

        for i in range(len(cache_list)-1, -1, -1):
            data_time, _ = cache_list[i]
            if datetime.datetime.fromtimestamp(data_time) < expiration:
                del cache_list[i]

        task_data_cache.set(cache_key, cache_list)
        if len(cache_list) < task_data["cycle"]:
            return None

        avg_data = sum(i[1] for i in cache_list) / len(cache_list)
        if avg_data * 100 < task_data["count"]:
            return None
        else:
            task_data_cache.set(cache_key, [])
        
        next_msg = ""
        if "next_data" in task_data:
            next_msg = self.do_next_data(task_data["next_data"])

        s_list = [
            ">通知类型：内存高占用告警",
            ">告警内容：最近{}分钟内机器内存平均占用率为{}%，高于告警值{}%".format(
                task_data["cycle"], round(avg_data * 100, 2), task_data["count"]),
            next_msg
        ]
        SystemPushMsgCollect.system_mem(s_list, task_data["title"])
        sdata = public.get_push_info('内存高占用告警', s_list)
        sdata["push_type"] = "首页内存告警"
        for m_module in task_data['module'].split(','):
            if m_module == 'sms':
                sdata = {
                    'sm_type': 'machine_exception',
                    'sm_args': public.check_sms_argv({
                        'name': self._get_panel_name(),
                        'type': "内存高占用",
                    })}
                result[m_module] = sdata
                continue

            elif m_module == 'wx_account':
                result[m_module] = ToWechatAccountMsg.system_mem(round(avg_data * 100, 2))
                continue

            result[m_module] = sdata

        tip_list.append(result["index"])
        task_data_cache.set("tip_" + task_data["id"], tip_list)
        return result
    
    @staticmethod
    def _get_panel_name():
        data = public.GetConfigValue("title")  # 若获得别名，则使用别名
        if data == "":
            data = "宝塔面板"
        return data

    # 返回到前端信息的钩子, 默认为返回传入信息（即：当前设置的任务的信息）
    @staticmethod
    def get_view_msg(task_id, task_data):
        task_data["tid"] = view_msg.get_tid(task_data)
        task_data["view_msg"] = view_msg.get_msg_by_type(task_data)
        return task_data

    @staticmethod
    def _get_bak_task_template():
        return [
            {
                "field": [
                    {
                        "attr": "project",
                        "name": "磁盘信息",
                        "type": "select",
                        "items": [
                        ]
                    },
                    {
                        "attr": "cycle",
                        "name": "检测类型",
                        "type": "radio",
                        "suffix": "",
                        "default": 2,
                        "items": [
                            {
                                "title": "剩余容量",
                                "value": 1
                            },
                            {
                                "title": "占用百分比",
                                "value": 2
                            },

                        ],
                    },
                    {
                        "attr": "count",
                        "name": "占用率超过",
                        "type": "number",
                        "unit": "%",
                        "suffix": "后触发告警",
                        "default": 80,
                        "err_msg_prefix": "磁盘阈值"
                    },
                    {
                        "attr": "interval",
                        "name": "间隔时间",
                        "type": "number",
                        "unit": "秒",
                        "suffix": "后再次监控检测条件",
                        "default": 600
                    },
                    {
                        "attr": "push_count",
                        "name": "每天发送",
                        "type": "number",
                        "unit": "次",
                        "suffix": (
                            "后，当日不再发送，次日恢复&nbsp;&nbsp;&nbsp;&nbsp;"
                            "<i style='color: #999;font-style: initial;font-size: 12px;margin-right: 5px'>*</i>"
                            "<span style='color:#999'>设置为0时，每天触发告警次数没有上限</span>"
                        ),
                        "default": 3
                    }
                ],
                "sorted": [
                    [
                        "project"
                    ],
                    [
                        "cycle"
                    ],
                    [
                        "count"
                    ],
                    # [
                    #     "interval"
                    # ],
                    [
                        "push_count"
                    ]
                ],
                "module": [
                    "wx_account",
                    "dingding",
                    "feishu",
                    "mail",
                    "weixin",
                    "sms"
                ],
                "tid": "system_push@0",
                "type": "disk",
                "title": "首页磁盘告警",
                "name": "system_push"
            },
            {
                "field": [
                    {
                        "attr": "cycle",
                        "name": "每",
                        "type": "select",
                        "unit": "分钟",
                        "suffix": "内平均",
                        "width": "70px",
                        "disabled": True,
                        "default": 5,
                        "items": [
                            {
                                "title": "1",
                                "value": 3
                            },
                            {
                                "title": "5",
                                "value": 5
                            },
                            {
                                "title": "15",
                                "value": 15
                            }
                        ]
                    },
                    {
                        "attr": "count",
                        "name": "CPU占用超过",
                        "type": "number",
                        "unit": "%",
                        "suffix": "后触发告警",
                        "default": 80,
                        "err_msg_prefix": "CPU"
                    },
                    {
                        "attr": "interval",
                        "name": "间隔时间",
                        "type": "number",
                        "unit": "秒",
                        "suffix": "后再次监控检测条件",
                        "default": 60
                    },
                    {
                        "attr": "push_count",
                        "name": "每天发送",
                        "type": "number",
                        "unit": "次",
                        "suffix": (
                            "后，当日不再发送，次日恢复&nbsp;&nbsp;&nbsp;&nbsp;"
                            "<i style='color: #999;font-style: initial;font-size: 12px;margin-right: 5px'>*</i>"
                            "<span style='color:#999'>设置为0时，每天触发告警次数没有上限</span>"
                        ),
                        "default": 3
                    }
                ],
                "sorted": [
                    [
                        "cycle",
                        "count"
                    ],
                    # [
                    #     "interval"
                    # ],
                    [
                        "push_count"
                    ]
                ],
                "module": [
                    "wx_account",
                    "dingding",
                    "feishu",
                    "mail",
                    "weixin",
                    "sms"
                ],
                "tid": "system_push@1",
                "type": "cpu",
                "title": "首页CPU告警",
                "name": "system_push"
            },
            {
                "field": [
                    {
                        "attr": "cycle",
                        "name": "每",
                        "type": "select",
                        "unit": "分钟",
                        "suffix": "内平均",
                        "default": 5,
                        "width": "70px",
                        "disabled": True,
                        "items": [
                            {
                                "title": "1",
                                "value": 1
                            },
                            {
                                "title": "5",
                                "value": 5
                            },
                            {
                                "title": "15",
                                "value": 15
                            }
                        ]
                    },
                    {
                        "attr": "count",
                        "name": "负载超过",
                        "type": "number",
                        "unit": "%",
                        "suffix": "后触发告警",
                        "default": 80,
                        "err_msg_prefix": "负载"
                    },
                    {
                        "attr": "interval",
                        "name": "间隔时间",
                        "type": "number",
                        "unit": "秒",
                        "suffix": "后再次监控检测条件",
                        "default": 60
                    },
                    {
                        "attr": "push_count",
                        "name": "每天发送",
                        "type": "number",
                        "unit": "次",
                        "suffix": (
                            "后，当日不再发送，次日恢复&nbsp;&nbsp;&nbsp;&nbsp;"
                            "<i style='color: #999;font-style: initial;font-size: 12px;margin-right: 5px'>*</i>"
                            "<span style='color:#999'>设置为0时，每天触发告警次数没有上限</span>"
                        ),
                        "default": 3
                    }
                ],
                "sorted": [
                    [
                        "cycle",
                        "count"
                    ],
                    # [
                    #     "interval"
                    # ],
                    [
                        "push_count"
                    ]
                ],
                "module": [
                    "wx_account",
                    "dingding",
                    "feishu",
                    "mail",
                    "weixin",
                    "sms"
                ],
                "tid": "system_push@2",
                "type": "load",
                "title": "首页负载告警",
                "name": "system_push"
            },
            {
                "field": [
                    {
                        "attr": "cycle",
                        "name": "每",
                        "type": "select",
                        "unit": "分钟",
                        "suffix": "内平均",
                        "width": "70px",
                        "disabled": True,
                        "default": 5,
                        "items": [
                            {
                                "title": "1",
                                "value": 3
                            },
                            {
                                "title": "5",
                                "value": 5
                            },
                            {
                                "title": "15",
                                "value": 15
                            }
                        ]
                    },
                    {
                        "attr": "count",
                        "name": "内存使用率超过",
                        "type": "number",
                        "unit": "%",
                        "suffix": "后触发告警",
                        "default": 80,
                        "err_msg_prefix": "内存"
                    },
                    {
                        "attr": "interval",
                        "name": "间隔时间",
                        "type": "number",
                        "unit": "秒",
                        "suffix": "后再次监控检测条件",
                        "default": 60
                    },
                    {
                        "attr": "push_count",
                        "name": "每天发送",
                        "type": "number",
                        "unit": "次",
                        "suffix": (
                            "后，当日不再发送，次日恢复&nbsp;&nbsp;&nbsp;&nbsp;"
                            "<i style='color: #999;font-style: initial;font-size: 12px;margin-right: 5px'>*</i>"
                            "<span style='color:#999'>设置为0时，每天触发告警次数没有上限</span>"
                        ),
                        "default": 3
                    }
                ],
                "sorted": [
                    [
                        "cycle",
                        "count"
                    ],
                    # [
                    #     "interval"
                    # ],
                    [
                        "push_count"
                    ]
                ],
                "module": [
                    "wx_account",
                    "dingding",
                    "feishu",
                    "mail",
                    "weixin",
                    "sms"
                ],
                "tid": "system_push@3",
                "type": "mem",
                "title": "首页内存告警",
                "name": "system_push"
            }
        ]

    def _get_disk_name(self) -> list:
        """获取硬盘挂载点"""
        from system import system

        disk_info = system.GetDiskInfo2(None, human=False)

        return [(d.get("path"), d.get("size")[0]) for d in disk_info]

    def _get_disk_info(self) -> list:
        """获取硬盘挂载点"""
        if self._disk_info is not None:
            return self._disk_info

        from system import system

        self._disk_info = system.GetDiskInfo2(None, human=False)

        return self._disk_info

    def get_task_template(self):
        res_data = public.readFile(self.__task_template)
        if not res_data:
            res_data = self._get_bak_task_template()
        else:
            res_data = json.loads(res_data)

        for (path, total_size) in self._get_disk_name():
            res_data[0]["field"][0]["items"].append({
                "title": "【{}】的磁盘".format(path),
                "value": path,
                "count_default": round((int(total_size) * 0.2) / 1024 / 1024, 1)
            })

        return "首页系统告警", res_data

    def do_next_data(self, args):
        res = []
        for service_name in args:
            if service_name.startswith("php"):
                base_path = "/www/server/php"
                if not os.path.exists(base_path):
                    return None
                for p in os.listdir(base_path):
                    if p != service_name.replace("php", ""):
                        continue
                    init_file = os.path.join("/etc/init.d", "php-fpm-{}".format(p))
                    if not os.path.isfile(init_file):
                        continue
                    public.ExecShell("{} start".format(init_file))
                    res.append(1)
            elif service_name == 'mysql':
                init_file = os.path.join("/etc/init.d", "mysqld")
                public.ExecShell("{} start".format(init_file))
                res.append(1)

            elif service_name == 'apache':
                init_file = os.path.join("/etc/init.d", "httpd")
                public.ExecShell("{} start".format(init_file))
                res.append(1)

            else:
                init_file = os.path.join("/etc/init.d", service_name)
                public.ExecShell("{} start".format(init_file))
                res.append(1)
        if len(res) == len(args):
            return "重启任务已执行"
        else:
            return "重启任务执行失败"


class TaskDataCache(object):
    """记录告警检测的平均数据"""
    _FILE = "{}/data/push/tips/system_data.json".format(public.get_panel_path())

    def __init__(self):
        if not os.path.exists(self._FILE):
            self._data = {}
            if not os.path.exists(os.path.dirname(self._FILE)):
                os.makedirs(os.path.dirname(self._FILE), 0o600)
        else:
            try:
                
                self._data = json.loads(public.readFile(self._FILE))
                if not isinstance(self._data, dict):
                    self._data = {}
            except:
                self._data = {}
        print(self._data)

    def save_cache(self):
        public.writeFile(self._FILE, json.dumps(self._data))
        
    def get(self, key):
        return self._data.get(key, None)

    def set(self, key, value):
        self._data[key] = value
        print(self._data)
        print(self._FILE)
        public.writeFile(self._FILE, json.dumps(self._data))
        print(public.readFile(self._FILE))

task_data_cache = TaskDataCache()


class ViewMsgFormat(object):
    _FORMAT = {
        "disk": (
            lambda x: "<span>挂载在{}上的磁盘{}触发</span>".format(
                x.get("project"),
                "余量不足%.1fG" % round(x.get("count"), 1) if x.get("cycle") == 1 else "占用超过%d%%" % x.get("count"),
            )
        ),
        "cpu": (
            lambda x: "<span>{}分钟内平均CUP占用超过{}%触发</span>".format(
                x.get("cycle"), x.get("count")
            )
        ),
        "load": (
            lambda x: "<span>{}分钟内平均负载超过{}%触发</span>".format(
                x.get("cycle"), x.get("count")
            )
        ),
        "mem": (
            lambda x: "<span>{}分钟内内存使用率超过{}%触发</span>".format(
                x.get("cycle"), x.get("count")
            )
        )
    }

    _TID = {
        "disk": "system_push@0",
        "cpu": "system_push@1",
        "load": "system_push@2",
        "mem": "system_push@3",
    }

    def get_msg_by_type(self, data):
        if data["type"] in ["ssl", "site_endtime", "panel_pwd_endtime"]:
            return self._FORMAT["ssl"](data)
        return self._FORMAT[data["type"]](data)

    def get_tid(self, data):
        return self._TID[data["type"]]


view_msg = ViewMsgFormat()


class ToWechatAccountMsg:
    @staticmethod
    def system_disk(msg_data: str, path: str):
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "宝塔首页磁盘告警"
        if len(msg_data) > 20:
            path = path[:17] + "..."
        msg.msg = msg_data
        if len(path) > 14:
            path = path[:11] + "..."
        msg.next_msg = "检查挂载点:{}".format(path)  # 小于14
        return msg

    @staticmethod
    def system_mem(count: float):
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "宝塔首页内存告警"
        msg.msg = "主机内存占用超过：{}%".format(count)
        msg.next_msg = "请登录面板，查看主机情况"
        return msg

    @staticmethod
    def system_load(count: float):
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "宝塔首页负载告警"
        msg.msg = "主机负载超过：{}%".format(count)
        msg.next_msg = "请登录面板，查看主机情况"
        return msg

    @staticmethod
    def system_cpu(count: float):
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "宝塔首页cpu告警"
        msg.msg = "主机CPU占用超过：{}%".format(count)
        msg.next_msg = "请登录面板，查看主机情况"
        return msg
