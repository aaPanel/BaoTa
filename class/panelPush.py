# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 沐落 <cjx@bt.cn>
# | Author: lx
# | 消息推送管理
# | 对外方法 get_modules_list、install_module、uninstall_module、get_module_template、set_push_config、get_push_config、del_push_config
# +-------------------------------------------------------------------

import json
import os
import sys
import time
from importlib import import_module

panelPath = "/www/server/panel"
os.chdir(panelPath)
sys.path.insert(0, panelPath + "/class/")
import public

try:
    from BTPanel import session
except:
    pass


class panelPush:
    __conf_path = "{}/class/push/push.json".format(panelPath)

    def __init__(self):
        spath = '{}/class/push'.format(panelPath)
        if not os.path.exists(spath): os.makedirs(spath)
        self._all_push_mode = {}
        self.base_push_mode = None

    @property
    def all_push_mode(self) -> dict:
        if self._all_push_mode:
            return self._all_push_mode
        spath = '{}/class/push'.format(panelPath)
        module_names = [i[:-3] for i in os.listdir(spath) if i.endswith(".py")]
        for m in module_names:
            try:
                push_class = getattr(import_module(".{}".format(m), package="push"), m, None)
            except:
                continue
            if m == "base_push":
                self.base_push_mode = push_class()
            elif push_class is not None:
                self._all_push_mode[m] = push_class()

        return self._all_push_mode

    """
    @获取推送模块列表
    """

    def get_modules_list(self, get):
        cpath = '{}/class/push/push_list.json'.format(panelPath)
        try:
            spath = os.path.dirname(cpath)
            if not os.path.exists(spath): os.makedirs(spath)

            if 'force' in get or not os.path.exists(cpath):
                if not 'download_url' in session: session['download_url'] = public.get_url()
                public.downloadFile('{}/linux/panel/push/push_list.json'.format(session['download_url']), cpath)
        except:
            pass

        if not os.path.exists(cpath):
            return {}

        data = {}
        push_list = self._get_conf()
        # module_list = public.get_modules('class/push')
        module_list = self.all_push_mode

        configs = json.loads(public.readFile(cpath))
        for p_info in configs:
            p_info['data'] = {}
            p_info['setup'] = False
            p_info['info'] = False
            key = p_info['name']
            try:
                if key in module_list:
                    p_info['setup'] = True
                    # if key in module_list:
                    #     print(dir(module_list))
                    #     print(dir(module_list[key]))
                    #     print(dir(getattr(module_list[key], key)))
                    push_module = module_list[key]
                    p_info['info'] = push_module.get_version_info(None)
                    # 格式化消息通道
                    if key in push_list:
                        p_info['data'] = self.__get_push_list(push_list[key])
                    # 格式化返回执行周期
                    if hasattr(push_module, 'get_push_cycle'):
                        p_info['data'] = push_module.get_push_cycle(p_info['data'])
            except:
                return public.get_error_object(None)
            data[key] = p_info
        return data

    """
    安装/更新消息通道模块
    @name 需要安装的模块名称
    """

    def install_module(self, get):
        module_name = get.name
        down_url = public.get_url()

        local_path = '{}/class/push'.format(panelPath)
        if not os.path.exists(local_path): os.makedirs(local_path)

        sfile = '{}/{}.py'.format(local_path, module_name)
        public.downloadFile('{}/linux/panel/push/{}.py'.format(down_url, module_name), sfile)
        if not os.path.exists(sfile): return public.returnMsg(False, '【{}】模块安装失败'.format(module_name))
        if os.path.getsize(sfile) < 1024: return public.returnMsg(False, '【{}】模块安装失败'.format(module_name))

        sfile = '{}/class/push/{}.html'.format(panelPath, module_name)
        public.downloadFile('{}/linux/panel/push/{}.html'.format(down_url, module_name), sfile)

        return public.returnMsg(True, '【{}】模块安装成功.'.format(module_name))

    """
    卸载消息通道模块
    @name 需要卸载的模块名称
    """

    def uninstall_module(self, get):
        module_name = get.name
        sfile = '{}/class/push/{}.py'.format(panelPath, module_name)
        if os.path.exists(sfile): os.remove(sfile)

        return public.returnMsg(True, '【{}】模块卸载成功'.format(module_name))

    """
    @获取模块执行日志
    """

    def get_module_logs(self, get):
        module_name = get.name
        id = get.id
        return []

    """
    获取模块模板
    """

    def get_module_template(self, get):
        sfile = '{}/class/push/{}.html'.format(panelPath, get.module_name)

        if not os.path.exists(sfile):
            return public.returnMsg(False, '模板文件不存在.')

        shtml = public.readFile(sfile)
        return public.returnMsg(True, shtml)

    """
    @获取模块推送参数，如：panel_push ssl到期，服务停止
    """

    def get_module_config(self, get):
        module = get.name
        # p_list = public.get_modules('class/push')
        p_list = self.all_push_mode
        push_module = p_list.get(module, None)

        if not module in p_list:
            return public.returnMsg(False, '指定模块{}未安装.'.format(module))

        if not hasattr(push_module, 'get_module_config'):
            return public.returnMsg(False, '指定模块{}不存在 get_module_config 方法.'.format(module))
        return push_module.get_module_config(get)

    """
    @获取模块配置项
    @优先调用模块内的get_push_config
    """

    def get_push_config(self, get):
        module = get.name
        id = get.id
        # p_list = public.get_modules('class/push')
        p_list = self.all_push_mode
        if not module in p_list:
            return public.returnMsg(False, '指定模块{}未安装.'.format(module))

        result = None
        push_module = p_list[module]
        if not hasattr(push_module, 'get_push_config'):
            push_list = self._get_conf()

            res_data = public.returnMsg(False, '未找到指定配置.')
            res_data['code'] = 100
            if not module in push_list:
                return res_data
            if not id in push_list[module]:
                return res_data

            result = push_list[module][id]
        else:
            result = push_module.get_push_config(get)
            if "code" in result:
                return result
        return self.get_push_user(result)

    def get_push_user(self, result):

        # 获取发送给谁
        if not 'to_user' in result:
            result['to_user'] = {}
            if 'module' in result:
                for s_module in result['module'].split(','):
                    result['to_user'][s_module] = 'default'
            else:
                return False

        info = {}
        for s_module in result['module'].split(','):
            if s_module == "":
                continue
            msg_obj = public.init_msg(s_module)
            if not msg_obj: continue

            info[s_module] = {}
            data = msg_obj.get_config(None)

            if 'list' in data:
                for key in result['to_user'][s_module].split(','):
                    if not key in data['list']:
                        continue
                    info[s_module][key] = data['list'][key]
        result['user_info'] = info
        return result

    """
    @设置推送配置
    @优先调用模块内的set_push_config
    """

    def set_push_config(self, get):
        if not hasattr(get, "id"):
            return public.returnMsg(False, '缺少参数！id')
        if not hasattr(get, "name"):
            return public.returnMsg(False, '没有模块信息')
        if not hasattr(get, "data"):
            return public.returnMsg(False, '没有告警设置信息')

        module = get.name
        id = get.id
        # p_list = public.get_modules('class/push')
        p_list = self.all_push_mode
        get_data_dict = json.loads(get['data'])
        if 'title' in get_data_dict.keys():
            title = get_data_dict["title"]
        elif "type" in get_data_dict.keys():
            title = get_data_dict["type"]
        else:
            title = module
        res = public.WriteLog('告警设置', '添加告警任务【{}】'.format(title))
        if not module in p_list:
            return public.returnMsg(False, '指定模块{}未安装.'.format(module))

        pdata = json.loads(get.data)
        if not 'module' in pdata or not pdata['module']:
            return public.returnMsg(False, '未设置指定告警方式，请重新选择.')

        if module == "load_balance_push":
            pdata = self.__get_args(pdata, 'cycle', "200|301|302|403|404", type_list=(str,))
        else:
            pdata = self.__get_args(pdata, 'cycle', 1, type_list=(int,))
        pdata = self.__get_args(pdata, 'count', 1, type_list=(int, float))
        pdata = self.__get_args(pdata, 'interval', 600, type_list=(int, float))
        pdata = self.__get_args(pdata, 'key', '', type_list=(str,))
        if "next_data" in pdata and not isinstance(pdata["next_data"], (str, dict, list, tuple)):
            pdata["next_data"] = []

        if "day_limit" in pdata and not isinstance(pdata["day_limit"], (str, int, float)):
            pdata["day_limit"] = 0

        nData = {}
        for skey in ['key', 'type', 'cycle', 'count', 'interval', 'module', 'title', 'project', 'status', 'index',
                     'push_count', "next_data", "day_limit"]:
            if skey in pdata:
                nData[skey] = pdata[skey]

        if isinstance(nData["push_count"], (int, float)):
            nData["push_count"] = int(nData["push_count"])
        elif isinstance(nData["push_count"], str):
            try:
                nData["push_count"] = int(nData["push_count"])
            except:
                nData["push_count"] = 3
        try:
            public.set_module_logs('set_push_config', nData['type'])
        except:pass
        class_obj = p_list[module]
        if hasattr(class_obj, 'set_push_config'):
            get['data'] = json.dumps(nData)
            result = class_obj.set_push_config(get)
            if 'status' in result: return result

            data = result
        else:
            data = self._get_conf()
            if not module in data: data[module] = {}
            data[module][id] = nData

        public.writeFile(self.__conf_path, json.dumps(data))
        # 兼容 负载均衡中的接口
        if module == "load_balance_push":
            try:
                from mod.base.push_mod import PushManager, get_default_module_dict
                pmgr = PushManager()
                df_mdl = get_default_module_dict()
                push_data = {
                    "template_id": "50",
                    "task_data": {
                        "sender": [df_mdl[i.strip()] for i in nData.get("module", "").split(",") if i.strip() in df_mdl],
                        "task_data": {
                            "project": nData.get("project", ""),
                            "cycle": nData.get("cycle", "200|301|302|403|404")
                        },
                        "number_rule": {
                            "day_num": nData.get("push_count", 2)
                        }
                    }
                }
                res = pmgr.set_task_conf_data(push_data)
                public.print_log(res)
            except:
                pass

        # 兼容 文件同步中的接口
        if module == "rsync_push":
            try:
                from mod.base.push_mod import PushManager, get_default_module_dict
                pmgr = PushManager()
                df_mdl = get_default_module_dict()
                sender_list = [df_mdl[i.strip()] for i in nData.get("module", "").split(",") if i.strip() in df_mdl]
                push_data = {
                    "template_id": "40",
                    "task_data": {
                        "status": bool(nData.get("status", True)),
                        "sender": sender_list,
                        "task_data": {
                            "interval": nData.get("interval", 600)
                        },
                        "number_rule": {
                            "day_num": nData.get("push_count", 3)
                        }
                    }
                }
                pmgr.set_task_conf_data(push_data)
            except:
                pass
        return public.returnMsg(True, '保存成功.')

    """
    @设置推送状态
    """

    def set_push_status(self, get):
        id = get.id
        module = get.name

        data = self._get_conf()
        # 兼容 文件同步中的接口
        if module == "rsync_push":
            try:
                from mod.base.push_mod import TaskConfig
                tc = TaskConfig()
                # print(tc)
                for i in tc.config:
                    # print(i)
                    if i["source"] == i['keyword'] == "rsync_push":
                        print(i)
                        i["status"] =int(get.status)

                        print(i["status"])
                tc.save_config()
            except:
                pass

        # 写日志
        color = 'green' if not data[module][id]['status'] else 'red'
        status = '开启' if not data[module][id]['status'] else '关闭'
        public.WriteLog('告警设置',
                              "设置任务【{}】的状态为【<span style='color:{}'>{}</span>】".format(data[module][id]['title'],color,status))
        if not module in data:
            return public.returnMsg(True, '模块名称不存在.')
        if id == "panel_login":
            return public.returnMsg(False, '不支持暂停面板登录告警，如需暂停请直接删除.')
        if id == "ssh_login":
            return public.returnMsg(False, '不支持暂停SSH登录告警，如需暂停请直接删除.')
        if id not in data[module]:
            return public.returnMsg(True, '指定推送任务不存在.')

        # 写日志
        color = 'green' if not data[module][id]['status'] else 'red'
        status ='开启' if not data[module][id]['status'] else '关闭'
        public.WriteLog('告警设置',
                              "设置任务【{}】的状态为【<span style='color:{}'>{}</span>】".format(data[module][id]['title'],color,status))

        status = int(get.status)
        if status:
            data[module][id]['status'] = True
        else:
            data[module][id]['status'] = False
        public.writeFile(self.__conf_path, json.dumps(data))
        return public.returnMsg(True, '操作成功.')

    """
    @删除指定配置
    """

    def del_push_config(self, get):
        id = get.id
        module = get.name
        data = self._get_conf()
        if id == "panel_login":
            public.WriteLog('告警设置', "删除告警任务【面板登录提醒】")
        elif id == "ssh_login":
            public.WriteLog('告警设置', "删除告警任务【SSH登录告警】")
        else:
            public.WriteLog('告警设置', "删除告警任务【{}】".format(data[module][id]['title']))

        # p_list = public.get_modules('class/push')
        p_list = self.all_push_mode
        if not module in p_list:
            return public.returnMsg(False, '指定模块{}未安装.'.format(module))
        push_module = p_list[module]
        if not hasattr(push_module, 'del_push_config'):
            data = self._get_conf()
            del data[module][id]
            public.writeFile(self.__conf_path, json.dumps(data))
            return public.returnMsg(True, '删除成功.')

        return push_module.del_push_config(get)

    """
    获取消息通道配置列表
    """

    def get_push_msg_list(self, get):
        data = {}
        msgs = self.__get_msg_list()
        from panelMessage import panelMessage
        pm = panelMessage()
        for x in msgs:
            x['setup'] = False
            key = x['name']
            try:
                obj = pm.init_msg_module(key)
                if obj:
                    x['setup'] = True
                    if key == 'sms': x[
                        'title'] = '{}<a title="请确保有足够的短信条数，否则您将无法收到通知." href="javascript:;" class="bt-ico-ask">?</a>'.format(
                        x['title'])
            except:
                pass
            data[key] = x
        return data

    """
    @ 获取消息推送配置
    """

    def _get_conf(self):
        data = {}
        try:
            if os.path.exists(self.__conf_path):
                data = json.loads(public.readFile(self.__conf_path))
                self.update_config(data)
        except:
            pass
        return data

    """
    @ 获取插件版本信息
    """

    def get_version_info(self):
        """
        获取版本信息
        """
        data = {}
        data['ps'] = ''
        data['version'] = '1.0'
        data['date'] = '2020-07-14'
        data['author'] = '宝塔'
        data['help'] = 'http://www.bt.cn'
        return data

    """
    @格式化推送对象
    """

    def format_push_data(self, push=['dingding', 'weixin', 'feishu'], project='', type=''):
        item = {
            'title': '',
            'project': project,
            'type': type,
            'cycle': 1,
            'count': 1,
            'keys': [],
            'helps': [],
            'push': push
        }
        return item

    def push_message_immediately(self, channel_data):
        """推送消息到指定的消息通道，即时

        Args:
            channel_data(dict):
                key: msg_channel, 消息通道名称，多个用逗号相连
                value: msg obj, 每种消息通道的消息内容格式，可能包含标题

        Returns:
            {
                status: True/False,
                msg: {
                    "email": {"status": msg},
                    ...
                }
            }
        """
        if type(channel_data) != dict:
            return public.returnMsg(False, "参数有误")

        from panelMessage import panelMessage
        pm = panelMessage()
        channel_res = {}
        res = {
            "status": False,
            "msg": channel_res
        }

        for module, msg in channel_data.items():
            modules = []
            if module.find(",") != -1:
                modules = module.split(",")
            else:
                modules.append(module)
            for m_module in modules:
                msg_obj = pm.init_msg_module(m_module)
                if not msg_obj: continue
                ret = msg_obj.push_data(msg)
                if ret and "status" in ret and ret['status']:
                    res["status"] = True
                    channel_res[m_module] = ret
                else:
                    msg = "消息推送失败。"
                    if "msg" in ret:
                        msg = ret["msg"]
                    channel_res[m_module] = public.returnMsg(False, msg)
        return res

    """
    @格式为消息通道格式
    """

    def format_msg_data(self):
        data = {
            'title': '',
            'to_email': '',
            'sms_type': '',
            'sms_argv': {},
            'msg': ''
        }
        return data

    def __get_msg_list(self):
        """
        获取消息通道列表
        """
        data = []
        cpath = '{}/data/msg.json'.format(panelPath)
        if not os.path.exists(cpath):
            return data
        try:
            conf = public.readFile(cpath)
            data = json.loads(conf)
        except:
            try:
                time.sleep(0.5)
                conf = public.readFile(cpath)
                data = json.loads(conf)
            except:
                pass

        return data

    def __get_args(self, data, key, val='', type_list=(str,)):
        """
        @获取默认参数
        """
        if not key in data:
            data[key] = val
        if type(data[key]) not in type_list:
            data[key] = val
        return data

    def __get_push_list(self, data):
        """
        @格式化列表数据
        """
        m_data = {}
        result = {}
        for x in self.__get_msg_list():
            m_data[x['name']] = x

        for skey in data:
            result[skey] = data[skey]

            m_list = []
            for x in data[skey]['module'].split(','):
                if x in m_data: m_list.append(m_data[x]['title'])
            result[skey]['m_title'] = '、'.join(m_list)

            m_cycle = []
            if data[skey]['cycle'] > 1:
                m_cycle.append('每{}秒'.format(data[skey]['cycle']))
            m_cycle.append('{}次，间隔{}秒'.format(data[skey]['count'], data[skey]['interval']))
            result[skey]['m_cycle'] = ''.join(m_cycle)

            # 兼容旧版本没有返回project项，导致前端无法编辑问题
            if "project" not in result[skey] and "type" in result[skey]:
                if result[skey]["type"] == "services":
                    services = ['nginx', 'apache', "pure-ftpd", 'mysql', 'php-fpm', 'memcached', 'redis']
                    _title = result[skey]['title']
                    for s in services:
                        if _title.find(s) != -1:
                            result[skey]["project"] = s
                else:
                    result[skey]["project"] = result[skey]["type"]
            if "project" in result[skey]:
                if result[skey]["project"] == "FTP服务端":
                    result[skey]["project"] = "pure-ftpd"
        return result

    # ************************************************推送
    """
    @推送data/push目录的所有文件
    """

    def push_messages_from_file(self):

        path = "{}/data/push".format(panelPath)
        if not os.path.exists(path): os.makedirs(path)

        from panelMessage import panelMessage
        pm = panelMessage()

        for x in os.listdir(path):
            try:
                spath = '{}/{}'.format(path, x)
                #判断文件是否为.json 结尾
                if not spath.endswith(".json"): continue
                if os.path.isdir(spath): continue
                data = json.loads(public.readFile(spath))

                msg_obj = pm.init_msg_module(data['module'])
                if not msg_obj: continue

                ret = msg_obj.push_data(data)
                if ret['status']: pass

                os.remove(spath)
            except:
                print(public.get_error_info())

    """
    @消息推送线程
    """

    def start(self):

        total = 0
        interval = 5

        tips = '{}/data/push/tips'.format(public.get_panel_path())
        if not os.path.exists(tips): os.makedirs(tips)

        try:
            if True:
                # 推送文件
                self.push_messages_from_file()

                # 调用推送子模块
                data = {}
                is_write = False
                path = "{}/class/push/push.json".format(panelPath)

                if os.path.exists(path):
                    data = public.readFile(path)
                    data = json.loads(data)

                # p = public.get_modules('class/push')
                p = self.all_push_mode
                for skey in data:
                    if skey in ("site_push", "system_push", "database_push", "rsync_push",
                                "load_balance_push", "task_manager_push"):
                        continue
                    if len(data[skey]) <= 0: continue
                    if skey in ['panelLogin_push', 'panel_login']: continue  # 面板登录主动触发

                    total = None
                    if skey not in p:
                        continue
                    obj = p[skey]

                    for x in data[skey]:
                        if x in ['panelLogin_push', 'panel_login']: continue  # 面板登录主动触发
                        try:
                            item = data[skey][x]
                            item['id'] = x
                            if not item['status']: continue
                            if not item['module']: continue
                            if not 'index' in item: item['index'] = 0

                            if time.time() - item['index'] < item['interval']:
                                print('{} 未达到间隔时间，跳过.'.format(item['title']))
                                continue

                            # 验证推送次数
                            push_record = {}
                            tips_path = '{}/{}'.format(tips, x)
                            if 'push_count' in item and item['push_count'] > 0:
                                item['tips_list'] = []
                                try:
                                    push_record = json.loads(public.readFile(tips_path))
                                except:
                                    pass
                                for k in push_record:
                                    if push_record[k] < item['push_count']:
                                        continue
                                    item['tips_list'].append(k)

                            # 获取推送数据
                            if not total: total = obj.get_total()
                            rdata = obj.get_push_data(item, total)
                            if not rdata:
                                continue
                            push_status = False
                            for m_module in item['module'].split(','):
                                if m_module == "":
                                    continue
                                if not m_module in rdata:
                                    continue

                                msg_obj = public.init_msg(m_module)
                                if not msg_obj: continue

                                if 'to_user' in item and m_module in item['to_user']:
                                    rdata[m_module]['to_user'] = item['to_user'][m_module]

                                ret = msg_obj.push_data(rdata[m_module])
                                data[skey][x]['index'] = rdata['index']
                                is_write = True
                                push_status = True

                            # 获取是否推送成功.
                            if push_status:
                                if 'push_keys' in rdata:
                                    for k in rdata['push_keys']:
                                        if k not in push_record:
                                            push_record[k] = 0
                                        push_record[k] += 1
                                    public.writeFile(tips_path, json.dumps(push_record))
                        except:
                            # print(public.get_error_info())
                            pass

                if is_write:
                    public.writeFile(path, json.dumps(data))
                # time.sleep(interval)
        except:
            # print(public.get_error_info())
            pass

    def __get_login_panel_info(self):
        """
        @name 获取面板登录列表
        @auther cjxin
        @date 2022-09-29
        """
        import config
        c_obj = config.config()
        send_type = c_obj.get_login_send(None)['msg']
        if not send_type:
            return False
        return {"type": "panel_login", "module": send_type, "interval": 600, "status": True, "title": "面板登录告警",
                "cycle": 1, "count": 1, "key": "", "module_type": 'site_push'}

    def __get_ssh_login_info(self):
        """
        @name 获取SSH登录列表
        @auther cjxin
        @date 2022-09-29
        """
        import ssh_security
        c_obj = ssh_security.ssh_security()
        send_type = c_obj.get_login_send(None)['msg']
        if not send_type or send_type in ['error']:
            return False

        return {"type": "ssh_login", "module": send_type, "interval": 600, "status": True, "title": "SSH登录告警",
                "cycle": 1, "count": 1, "key": "", "module_type": 'site_push'}

    def get_push_list(self, get):
        """
        @获取所有推送列表
        """
        conf = self._get_conf()
        del_key_list = []

        # 用于缓存同一module结果，从而避免多次调用get_push_user
        module_user_info_cache = {}

        for key in conf.keys():
            # 先调用一遍各模块内部的get_view_msg， 获取额外信息
            push_module = self.all_push_mode.get(key, None)
            for x in list(conf[key].keys()):
                data = conf[key][x]
                data['module_type'] = key

                # 检查可见性
                if hasattr(push_module, "can_view_task") and not push_module.can_view_task(data):
                    del_key_list.append((key, x))

                # 获取额外显示信息
                if hasattr(push_module, "get_view_msg"):
                    data = push_module.get_view_msg(x, data)

                # 获取 data['module']，可能是逗号分隔的多个模块
                modules = data.get('module', '')
                module_key = modules  # 使用完整字符串作为缓存键

                if module_key:
                    if module_key not in module_user_info_cache:
                        # 第一次遇到此 module_key，调用一次 get_push_user
                        # print(f"模块 {module_key} 第一次调用 get_push_user")
                        updated_data = self.get_push_user(data)
                        module_user_info_cache[module_key] = updated_data.get('user_info', None)
                        data = updated_data
                    else:
                        # 使用缓存的 user_info
                        # print(f"模块 {module_key} 使用缓存的 user_info")
                        data['user_info'] = module_user_info_cache[module_key]
                else:
                    # 没有module信息则正常调用
                    data = self.get_push_user(data)

                conf[key][x] = data

        # 删除不可见的key
        for key, idx in del_key_list:
            del conf[key][idx]

        if 'site_push' not in conf:
            conf['site_push'] = {}

        data = conf['site_push']
        for skey in ['panel_login']:
            info = None
            if skey in ['panel_login']:
                info = self.__get_login_panel_info()
            # elif skey in ['ssh_login']:
            #     info = self.__get_ssh_login_info()

            if info is not False:
                info = self.all_push_mode.get("site_push").get_view_msg(skey, info)
                modules = info.get('module', '')
                module_key = modules
                if module_key:
                    if module_key not in module_user_info_cache:
                        # print(f"模块 {module_key} 第一次调用 get_push_user (site_push)")
                        updated_info = self.get_push_user(info)
                        module_user_info_cache[module_key] = updated_info.get('user_info', None)
                        info = updated_info
                    else:
                        # print(f"模块 {module_key} 使用缓存的 user_info (site_push)")
                        info['user_info'] = module_user_info_cache[module_key]
                else:
                    info = self.get_push_user(info)
                data[skey] = info
            else:
                if skey in data:
                    del data[skey]
        conf['site_push'] = data
        return conf

    def get_push_logs(self, get):
        """
        @name 获取推送日志
        """

        p = 1
        limit = 15
        if 'p' in get: p = get.p
        if 'limit' in get: limit = get.limit

        where = "type = '告警通知'"
        sql = public.M('logs')

        # 查询关键字过滤
        if hasattr(get, 'keyword'):
            keyword = get.keyword.strip()
            if keyword:
                where += " and log like '%{}%'".format(keyword)

        if hasattr(get, 'status') and get.status:

            target_status = get.status.strip()
            if target_status == "true":
                where += " and log like '%成功</span>%'"
            elif target_status == "false":
                where += " and log like '%失败</span>%'"

        # 查询数据库记录总数
        count = sql.where(where, ()).count()
        data = public.get_page(count, int(p), int(limit))
        
        # 查询数据
        raw_logs = public.M('logs').where(where, ()).limit('{},{}'.format(data['shift'], data['row'])).order('id desc').select()
        data['data'] = raw_logs
        return data


    # 兼容旧版本的告警
    def update_config(self, config):
        if "site_push" not in config:
            config["site_push"] = {}
        if "panel_push" in config:
            for k, v in config["panel_push"].items():
                if v["type"] != "endtime":
                    config["site_push"][k] = v
                if "push_count" not in v:
                    v["push_count"] = 1 if v["type"] == "ssl" else 0
            del config["panel_push"]
            public.writeFile(self.__conf_path, json.dumps(config))

    # 获取模板
    def get_task_template(self, get):
        res = []
        title, tasks = self.all_push_mode["site_push"].get_task_template()
        res.append({
            "title": title,
            "template": tasks,
        })
        title, tasks = self.all_push_mode["database_push"].get_task_template()
        res.append({
            "title": title,
            "template": tasks,
        })
        title, tasks = self.all_push_mode["system_push"].get_task_template()
        res.append({
            "title": title,
            "template": tasks,
        })

        for k, v in self.all_push_mode.items():
            if k in ["base_push", "site_push", "system_push"]:
                continue
            # 不是可以检测的插件就跳过
            if hasattr(v, "check_self_plugin"):
                if not v.check_self_plugin():
                    continue
            else:
                continue
            if hasattr(v, "get_task_template"):
                title, tasks = v.get_task_template()
                if tasks is None:
                    continue
                res.append({
                    "title": title,
                    "template": tasks,
                })
        return res


if __name__ == '__main__':
    panelPush().start()
