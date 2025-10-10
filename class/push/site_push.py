# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Windows面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2020 宝塔软件(https://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 沐落 <cjx@bt.cn>
# +-------------------------------------------------------------------
import glob
import hashlib
import sys, os, time, json, re, psutil
from datetime import datetime
from importlib import import_module

panelPath = "/www/server/panel"
os.chdir(panelPath)
sys.path.append("class/")
import public, time, panelPush
import config
from push.base_push import base_push, WxAccountMsg, WxAccountLoginMsg
from panel_msg.collector import SitePushMsgCollect

try:
    from BTPanel import cache
except:
    from cachelib import SimpleCache

    cache = SimpleCache()


class site_push(base_push):
    __task_template = "{}/class/push/scripts/site_push.json".format(panelPath)
    __push_model = ['dingding', 'weixin', 'mail', 'sms', 'wx_account', 'feishu']
    __conf_path = "{}/class/push/push.json".format(panelPath)
    pids = None

    def __init__(self):
        self.__push = panelPush.panelPush()

    # -----------------------------------------------------------start 添加推送 ------------------------------------------------------
    def get_version_info(self, get):
        """
        获取版本信息
        """
        data = {}
        data['ps'] = ''
        data['version'] = '1.0'
        data['date'] = '2020-08-10'
        data['author'] = '宝塔'
        data['help'] = 'http://www.bt.cn/bbs'
        return data

    """
    @获取推送模块配置
    """

    def get_module_config(self, get):

        stype = None
        if 'type' in get:
            stype = get.type

        data = []
        # 证书到期提醒
        item = self.__push.format_push_data()
        item['cycle'] = 30
        item['type'] = 'ssl'
        item['push'] = self.__push_model
        item['title'] = '网站SSL到期提醒'
        item['helps'] = ['SSL到期提醒一天只发送一次']
        data.append(item)

        # 网站到期提醒
        item = self.__push.format_push_data(push=['dingding', 'weixin', 'mail'])
        item['cycle'] = 15
        item['type'] = 'site_endtime'
        item['title'] = '网站到期提醒'
        item['helps'] = ['网站到期提醒一天只发送一次']
        data.append(item)

        for data_item in data:
            if stype == data_item['type']:
                return data_item
        return data

    def get_push_cycle(self, data):
        """
        @获取执行周期
        """
        result = {}
        for skey in data:
            result[skey] = data[skey]

            m_cycle = []
            m_type = data[skey]['type']
            if m_type in ['endtime', 'ssl', 'site_endtime']:
                m_cycle.append('剩余{}天时，每天1次'.format(data[skey]['cycle']))

            if len(m_cycle) > 0:
                result[skey]['m_cycle'] = ''.join(m_cycle)
        return result

    @staticmethod
    def _to_project_type(type_id: int):
        if type_id == 1:
            return "Java"
        if type_id == 2:
            return "Node"
        if type_id == 3:
            return "Go"
        if type_id == 4:
            return "Python"
        if type_id == 5:
            return "Other"

    @staticmethod
    def _to_project_id(type_name):
        if type_name == "Java":
            return 0
        if type_name == "Node":
            return 1
        if type_name == "Go":
            return 2
        if type_name == "Python":
            return 3
        if type_name == "Other":
            return 4

    @staticmethod
    def _to_project_model(type_id: int):
        if type_id == 1:
            return "javaModel"
        if type_id == 2:
            return "nodejsModel"
        if type_id == 3:
            return "goModel"
        if type_id == 4:
            return "pythonModel"
        if type_id == 5:
            return "otherModel"

    def get_server_status(self, server_name):
        status = self.check_run(server_name)
        if status:
            return 1
        return 0

        # 检测指定进程是否存活

    def checkProcess(self, pid):
        try:
            if not self.pids: self.pids = psutil.pids()
            if int(pid) in self.pids: return True
            return False
        except Exception as e:
            return False

        # 名取PID

    def getPid(self, pname):
        try:
            if not self.pids: self.pids = psutil.pids()
            for pid in self.pids:
                if psutil.Process(pid).name() == pname: return True
            return False
        except:
            return True

        # 检查是否启动

    def check_run(self, name):
        if name == "php-fpm":
            status = False
            base_path = "/www/server/php"
            if not os.path.exists(base_path):
                return status
            for p in os.listdir(base_path):
                pid_file = os.path.join(base_path, p, "var/run/php-fpm.pid")
                if os.path.exists(pid_file):
                    php_pid = int(public.readFile(pid_file))
                    status = self.checkProcess(php_pid)
                    if status:
                        return status
            return status
        elif name == 'nginx':
            status = False
            if os.path.exists('/etc/init.d/nginx'):
                pidf = '/www/server/nginx/logs/nginx.pid'
                if os.path.exists(pidf):
                    try:
                        pid = public.readFile(pidf)
                        status = self.checkProcess(pid)
                    except:
                        pass
            return status
        elif name == 'apache':
            status = False
            if os.path.exists('/etc/init.d/httpd'):
                pidf = '/www/server/apache/logs/httpd.pid'
                if os.path.exists(pidf):
                    pid = public.readFile(pidf)
                    status = self.checkProcess(pid)
            return status
        elif name == 'mysql':
            if os.path.exists('/tmp/mysql.sock'):
                return True
            return False
        elif name == 'tomcat':
            status = False
            if os.path.exists('/www/server/tomcat/logs/catalina-daemon.pid'):
                if self.getPid('jsvc'): status = True
            if not status:
                if self.getPid('java'): status = True
            return status
        elif name == 'pure-ftpd':
            pidf = '/var/run/pure-ftpd.pid'
            status = False
            if os.path.exists(pidf):
                pid = public.readFile(pidf)
                status = self.checkProcess(pid)
            return status
        elif name == 'redis':
            status = False
            pidf = '/www/server/redis/redis.pid'
            if os.path.exists(pidf):
                pid = public.readFile(pidf)
                status = self.checkProcess(pid)
            return status
        elif name == 'memcached':
            status = False
            pidf = '/var/run/memcached.pid'
            if os.path.exists(pidf):
                pid = public.readFile(pidf)
                status = self.checkProcess(pid)
            return status
        return True

    def clear_push_count(self, task_id):
        """
        @清除推送次数
        """
        try:
            # 编辑后清理推送次数标记
            tip_file = '{}/data/push/tips/{}'.format(public.get_panel_path(), task_id)
            if os.path.exists(tip_file):
                os.remove(tip_file)
            DayLimit().clear_push(task_id)
        except:
            pass

    def set_push_config(self, get):
        """
        @name 设置推送配置
        """
        id = get.id
        module = get.name
        pdata = json.loads(get.data)

        data = self.__push._get_conf()
        if not module in data: data[module] = {}

        self.clear_push_count(id)

        is_create = True
        if pdata["type"] == "project_status":
            if not (1 <= pdata["cycle"] <= 5):
                return public.returnMsg(False, '不支持的项目类型.')
            sql = public.M("sites")
            sql = sql.where("project_type = ? and id = ?", (self._to_project_type(pdata["cycle"]), pdata["project"]))
            web_info = sql.field("id,name").find()
            if not web_info:
                return public.returnMsg(False, '没有该项目，不可设置告警')
            pdata['title'] = '{}项目[{}]停止告警'.format(self._to_project_type(pdata["cycle"]), web_info["name"])

            for x in data[module]:
                item = data[module][x]
                if item['type'] == "project_status" and item['project'] == pdata['project']:
                    data[module][x] = pdata
                    break
            else:
                data[module][id] = pdata
            self._remove_project_push_count_by_id(str(pdata["project"]))
            public.set_module_logs('site_push_project', 'set_push_config', 1)
            return data

        if pdata['type'] in ['ssl', 'services']:
            if pdata['type'] == 'ssl':
                pdata["title"] = (
                                     "所有网站" if pdata["project"] == "all" else "网站【{}】".format(pdata["project"])
                                 ) + "证书(SSL)到期告警"
            else:
                pdata['title'] = pdata["project"] + "服务停止告警"

            for x in data[module]:
                if x not in data[module] or not data[module][x]:
                    continue
                item = data[module][x]
                if item['type'] == pdata['type'] and item['project'] == pdata['project']:
                    is_create = False
                    data[module][x] = pdata
        elif pdata['type'] in ['panel_login']:
            p_module = pdata['module'].split(',')
            if len(p_module) > 1:
                return public.returnMsg(False, '面板登录告警只支持配置一个告警方式.')

            if not pdata['status']:
                return public.returnMsg(False, '不支持暂停面板登录告警，如需暂停请直接删除.')

            import config
            c_obj = config.config()

            args = public.dict_obj()
            args.type = pdata['module'].strip()

            res = c_obj.set_login_send(args)
            if not res['status']:
                return res
            else:
                id = 'panel_login'

        elif pdata['type'] in ['ssh_login']:

            p_module = pdata['module'].split(',')
            if len(p_module) > 1:
                return public.returnMsg(False, 'SSH登录告警只支持配置一个告警方式.')

            if not pdata['status']:
                return public.returnMsg(False, '不支持暂停SSH登录告警，如需暂停请直接删除.')

            import ssh_security
            c_obj = ssh_security.ssh_security()

            args = public.dict_obj()
            args.type = pdata['module'].strip()

            res = c_obj.set_login_send(args)
            if not res['status']: 
                return res
            else:
                id = 'ssh_login'
        
        elif pdata['type'] in ['ssh_login_error']:

            res = public.get_ips_area(['127.0.0.1'])
            if 'status' in res:
                return res

        elif pdata['type'] in ['panel_safe_push']:
            pdata['interval'] = 30

        if is_create:
            data[module][id] = pdata
        public.set_module_logs('site_push_ssl', 'set_push_config', 1)
        return data

    def del_push_config(self, get):
        """
        @name 删除推送记录
        @param get
            id = 告警记录标识
            module = 告警模块, site_push,panel_push
        """
        id = get.id
        module = get.name
        self.clear_push_count(id)

        data = self.__push.get_push_list(get)
        info = data[module][id]
        if id in ['panel_login']:

            c_obj = config.config()
            args = public.dict_obj()
            args.type = info['module'].strip()
            res = c_obj.clear_login_send(args)
            if not res['status']: return res
        elif id in ['ssh_login']:

            import ssh_security
            c_obj = ssh_security.ssh_security()
            res = c_obj.clear_login_send(None)

            if not res['status']: return res

        try:
            data = self.__push._get_conf()
            del data[module][id]
            public.writeFile(self.__conf_path, json.dumps(data))
        except:
            pass
        return public.returnMsg(True, '删除成功.')

    # -----------------------------------------------------------end 添加推送 ------------------------------------------------------
    def get_unixtime(self, data, format="%Y-%m-%d %H:%M:%S"):
        import time
        timeArray = time.strptime(data, format)
        timeStamp = int(time.mktime(timeArray))
        return timeStamp

    def get_site_ssl_info(self, webType, siteName, project_type=''):
        """
        @获取SSL详细信息
        @webType string web类型 /nginx /apache /iis
        @siteName string 站点名称
        """
        result = False
        if webType in ['nginx', 'apache']:
            path = public.get_setup_path()
            if public.get_os('windows'):
                conf_file = '{}/{}/conf/vhost/{}.conf'.format(path, webType, siteName)
                ssl_file = '{}/{}/conf/ssl/{}/fullchain.pem'.format(path, webType, siteName)
            else:
                conf_file = '{}/vhost/{}/{}{}.conf'.format(public.get_panel_path(), webType, project_type, siteName)
                ssl_file = '{}/vhost/cert/{}/fullchain.pem'.format(public.get_panel_path(), siteName)

            conf = public.readFile(conf_file)

            if not conf:
                return result

            if conf.find('SSLCertificateFile') >= 0 or conf.find('ssl_certificate') >= 0:

                if os.path.exists(ssl_file):
                    cert_data = public.get_cert_data(ssl_file)
                    return cert_data
        return result

    def get_total(self):
        return True

    def get_ssl_push_data(self, data):
        """
        @name 获取SSL推送数据
        @param data
            type = ssl
            project = 项目名称
            siteName = 站点名称
        """

        if time.time() < data['index'] + 86400:
            return public.returnMsg(False, "SSL一天推送一次，跳过.")

        push_keys = []
        ssl_list = []
        sql = public.M('sites')
        if data['project'] == 'all':
            # 过滤单独设置提醒的网站
            not_push_web = []
            push_list = self.__push._get_conf()['site_push']
            for k, v in push_list.values():
                if v["project"] != 'all' and v["type"] == "ssl":
                    not_push_web.append(v["project"])

            # 所有正常网站
            web_list = sql.where('status=1', ()).select()
            for web in web_list:
                project_type = ''
                if web['name'] in not_push_web:
                    continue
                if web['name'] in data['tips_list']:
                    continue

                if not web['project_type'] in ['PHP']:
                    project_type = web['project_type'].lower() + '_'

                info = self.__check_endtime(web['name'], data['cycle'], project_type)
                if isinstance(info, dict):  # 返回的是详情，说明需要推送了
                    info['siteName'] = web['name']
                    push_keys.append(web['name'])
                    ssl_list.append(info)
        else:
            project_type = ''
            find = sql.where('name=? and status=1', (data['project'],)).find()
            if not find: return public.returnMsg(False, "没有可用的站点.")

            if not find['project_type'] == 'PHP':
                project_type = find['project_type'].lower() + '_'

            info = self.__check_endtime(find['name'], data['cycle'], project_type)
            if isinstance(info, dict):  # 返回的是详情，说明需要推送了
                info['siteName'] = find['name']
                ssl_list.append(info)
                push_keys.append(find['name'])

        return self.__get_ssl_result(data, ssl_list, push_keys)

    def get_panel_update_data(self, data):
        """
        @name 获取面板更新推送
        @param push_keys array 推送次数缓存key
        """
        stime = time.time()
        result = {'index': stime, 'push_keys': [data['id']]}

        # 面板更新提醒
        if self.user_can_request_hour() != datetime.now().hour:
            return public.returnMsg(False, "不在固定时间段内，跳过.")
        if stime < data['index'] + 60 * 60 * 23.5:  # 改为23.5小时， 防止由于小时数限制导致次数后延，6次后过一天
            return public.returnMsg(False, "一天推送一次，跳过.")

        s_url = '{}/api/panel/updateLinux'
        if public.get_os('windows'):
            s_url = '{}/api/wpanel/updateWindows'
        s_url = s_url.format('https://www.bt.cn')

        try:
            res = json.loads(public.httpPost(s_url, {}))
            if not res:
                return public.returnMsg(False, "获取更新信息失败.")
        except:
            pass

        n_ver = res['version']
        if res['is_beta']:
            n_ver = res['beta']['version']

        old_ver = public.get_cache_func(data['type'])['data']
        if not old_ver:
            public.set_cache_func(data['type'], n_ver)
        else:
            if old_ver == n_ver:
                # 处理推送次数逻辑
                if data['id'] in data['tips_list']:
                    print('已超过通知次数，跳过.')
                    return result
            else:
                # 清除缓存
                data['tips_list'] = []
                try:
                    tips_path = '{}/data/push/tips/{}'.format(public.get_panel_path(), data['id'])
                    os.remove(tips_path)
                    print('已发现新版本，重新计数通知次数.')
                except:
                    pass
                public.set_cache_func(data['type'], n_ver)

        s_list = [">通知类型：面板版本更新", ">当前版本：{} ".format(public.version()),
                  ">最新版本：{}".format(n_ver)]

        check_status = self._compare_version(public.version(), n_ver)
        if check_status == -1:
            for m_module in data['module'].split(','):
                if m_module == 'sms':
                    continue
                elif m_module == 'wx_account':
                    result[m_module] = ToWechatAccountMsg.panel_update(n_ver)
                    continue

                sdata = public.get_push_info('面板更新提醒', s_list)
                sdata["push_type"] = "面板更新提醒"
                result[m_module] = sdata

        return result

    # 版本号比较
    def _compare_version(self, version1, version2):
        """
        版本号比较
        @param version1: 版本号 1
        @param version2: 版本号 2
        @return: -1 version_1 < version_2
        @return: 0 version_1 == version_2
        @return: 1 version_1 > version_2
        """
        version_1 = version1.split(".")
        version_2 = version2.split(".")

        len1 = len(version_1)
        len2 = len(version_2)
        # 比较长度，并在较短的列表末尾补充0
        if len1 < len2:
            version_1 += [0] * (len2 - len1)
        else:
            version_2 += [0] * (len1 - len2)
        for v_1, v_2 in zip(version_1, version_2):
            v_1 = int(v_1)
            v_2 = int(v_2)
            if v_1 < v_2:
                return -1
            if v_1 > v_2:
                return 1
        return 0

    def get_panel_safe_push(self, data, result):
        s_list = []
        # 面板登录用户安全
        t_add, t_del, total = self.get_records_calc('login_user_safe', public.M('users'))
        if t_add > 0 or t_del > 0:
            s_list.append(
                ">登录用户变更：<font color=#ff0000>总 {} 个，新增 {} 个 ，删除 {} 个</font>.".format(total, t_add, t_del))

        # 面板日志发生删除
        t_add, t_del, total = self.get_records_calc('panel_logs_safe', public.M('logs'), 1)
        if t_del > 0:
            s_list.append(">面板日志发生删除，删除条数：<font color=#ff0000>{} 条</font>".format(t_del))

        debug_str = '关闭'
        debug_status = 'False'
        # 面板开启开发者模式告警
        if os.path.exists('{}/data/debug.pl'.format(public.get_panel_path())):
            debug_status = 'True'
            debug_str = '开启'

        skey = 'panel_debug_safe'
        tmp = public.get_cache_func(skey)['data']
        if not tmp:
            public.set_cache_func(skey, debug_status)
        else:
            if str(debug_status) != tmp:
                s_list.append(">面板开发者模式发生变更，当前状态：{}".format(debug_str))
                public.set_cache_func(skey, debug_status)

        # #面板开启api告警
        # api_str = 'False'
        # s_path = '{}/config/api.json'.format(public.get_panel_path())
        # if os.path.exists(s_path):
        #     api_str = public.readFile(s_path).strip()
        #     if not api_str: api_str = 'False'

        # api_str = public.md5(api_str)
        # skey = 'panel_api_safe'
        # tmp = public.get_cache_func(skey)['data']
        # if not tmp:
        #     public.set_cache_func(skey,api_str)
        # else:
        #     if api_str != tmp:
        #         s_list.append(">面板API配置发生改变，请及时确认是否本人操作.")
        #         public.set_cache_func(skey,api_str)

        # 面板用户名和密码发生变更
        find = public.M('users').where('id=?', (1,)).find()

        if find:
            skey = 'panel_user_change_safe'
            user_str = public.md5(find['username']) + '|' + public.md5(find['password'])
            tmp = public.get_cache_func(skey)['data']
            if not tmp:
                public.set_cache_func(skey, user_str)
            else:
                if user_str != tmp:
                    s_list.append(">面板登录帐号或密码发生变更")
                    public.set_cache_func(skey, user_str)

        if len(s_list) > 0:
            day_limit = None
            if "day_limit" in data:
                try:
                    day_limit = int(data["day_limit"])
                except ValueError:
                    day_limit = None

            day_limit_conf = DayLimit()
            if day_limit and day_limit_conf.push_num(data["id"]) >= day_limit:
                return public.returnMsg(False, "推送次数达到上限，跳过.")

            SitePushMsgCollect.panel_safe_push(s_list)
            sdata = public.get_push_info('宝塔面板安全告警', s_list)
            for m_module in data['module'].split(','):
                if m_module == 'sms':
                    continue
                elif m_module == 'wx_account':
                    result[m_module] = ToWechatAccountMsg.panel_safe_push(s_list)
                else:
                    sdata["push_type"] = "面板安全告警"
                    result[m_module] = sdata
            day_limit_conf.set_push(data["id"])
        return result

    def get_push_data(self, data, total):
        """
        @检测推送数据
        @data dict 推送数据
            title:标题
            project:项目
            type:类型 ssl:证书提醒
            cycle:周期 天、小时
            keys:检测键值
        """
        stime = time.time()
        if not 'tips_list' in data: data['tips_list'] = []
        if not 'project' in data: data['project'] = ''

        # 优先处理面板更新
        if data['type'] in ['panel_update']:
            return self.get_panel_update_data(data)

        result = {'index': stime, 'push_keys': [data['id']]}
        if data['project']:
            result['push_keys'] = [data['project']]

        # 检测推送次数,超过次数不再推送
        if data['project'] in data['tips_list'] or data['id'] in data['tips_list']:
            return result

        if data['type'] in ['ssl']:
            return self.get_ssl_push_data(data)

        elif data['type'] in ['site_endtime']:
            result['push_keys'] = []

            if stime < data['index'] + 86400:
                return public.returnMsg(False, "一天推送一次，跳过.")

            mEdate = public.format_date(format='%Y-%m-%d', times=stime + 86400 * int(data['cycle']))
            web_list = public.M('sites').where('edate>? AND edate<? AND (status=? OR status=?)',
                                               ('0000-00-00', mEdate, 1, u'正在运行')).field('id,name,edate').select()

            if len(web_list) > 0:
                s_list = ['>即将到期：<font color=#ff0000>{} 个站点</font>'.format(len(web_list))]
                for x in web_list:
                    if x['name'] in data['tips_list']: continue
                    result['push_keys'].append(x['name'])

                    s_list.append(">网站：{}  到期：{}".format(x['name'], x['edate']))

                msg = SitePushMsgCollect.site_endtime(s_list, data["title"])

                for m_module in data['module'].split(','):
                    if m_module == 'sms':
                        continue
                    elif m_module == 'wx_account':
                        result[m_module] = ToWechatAccountMsg.site_endtime(len(web_list))
                        continue

                    sdata = public.get_push_info('宝塔面板网站到期提醒', s_list)
                    sdata["push_type"] = '网站到期'
                    result[m_module] = sdata
                return result

        elif data['type'] in ['panel_pwd_endtime']:
            if stime < data['index'] + 86400:
                return public.returnMsg(False, "一天推送一次，跳过.")

            import config
            c_obj = config.config()
            res = c_obj.get_password_config(None)

            s_list = [">告警类型：登录密码即将过期",
                      ">剩余天数：<font color=#ff0000>{}  天</font>".format(res['expire_day'])]

            if res['expire'] > 0 and res['expire_day'] < data['cycle']:
                msg = SitePushMsgCollect.panel_pwd_endtime(s_list, data["title"])
                for m_module in data['module'].split(','):
                    if m_module == 'sms':
                        continue
                    elif m_module == 'wx_account':
                        result[m_module] = ToWechatAccountMsg.panel_pwd_endtime(res['expire_day'])
                        continue

                    sdata = public.get_push_info('宝塔面板密码到期提醒', s_list)
                    sdata["push_type"] = '面板密码有效期'
                    result[m_module] = sdata
                return result

        elif data['type'] in ['clear_bash_history']:
            stime = time.time()

            result = {'index': stime}

        elif data['type'] in ['panel_bind_user_change']:
            # 面板绑定帐号发生变更
            uinfo = public.get_user_info()

            user_str = public.md5(uinfo['username'])
            old_str = public.get_cache_func(data['type'])['data']
            if not old_str:
                public.set_cache_func(data['type'], user_str)
            else:
                if user_str != old_str:

                    for m_module in data['module'].split(','):
                        if m_module == 'sms': continue

                        s_list = [">告警类型：面板绑定帐号变更",
                                  ">当前绑定帐号：{}****{}".format(uinfo['username'][:3], uinfo['username'][-4:])]
                        sdata = public.get_push_info('面板绑定帐号变更提醒', s_list)
                        result[m_module] = sdata

                    public.set_cache_func(data['type'], user_str)
                    return result

        elif data['type'] in ['panel_safe_push']:
            return self.get_panel_safe_push(data, result)

        elif data['type'] in ['panel_oneav_push']:
            # 微步在线木马扫描提醒
            sfile = '{}/plugin/oneav/oneav_main.py'.format(public.get_panel_path())
            if not os.path.exists(sfile): return

            _obj = public.get_script_object(sfile)
            _main = getattr(_obj, 'oneav_main', None)
            if not _main: return

            args = public.dict_obj()
            args.p = 1
            args.count = 1000

            f_list = []
            s_day = public.getDate(format='%Y-%m-%d')

            for line in _main().get_logs(args):

                # 未检测到当天日志，跳出
                if public.format_date(times=line['time']).find(s_day) == -1:
                    break
                if line['file'] in f_list: continue

                f_list.append(line['file'])

            if not f_list: return

            for m_module in data['module'].split(','):
                if m_module == 'sms': continue

                s_list = [">告警类型：木马检测告警",
                          ">通知内容：<font color=#ff0000>发现疑似木马文件 {} 个</font>".format(len(f_list)),
                          ">文件列表：[{}]".format('、'.join(f_list))]
                sdata = public.get_push_info('宝塔面板木马检测告警', s_list)
                result[m_module] = sdata
            return result

        # 登录失败次数
        elif data['type'] in ['ssh_login_error']:
            import PluginLoader

            args = public.dict_obj()
            args.model_index = 'safe'
            args.count = data['count']
            args.p = 1
            res = PluginLoader.module_run("syslog", "get_ssh_error", args)
            if 'status' in res:
                return

            day_limit = None
            if "day_limit" in data:
                try:
                    day_limit = int(data["day_limit"])
                except ValueError:
                    day_limit = None

            day_limit_conf = DayLimit()
            if type(res) == list:
                last_info = res[data['count'] - 1]
                if public.to_date(times=last_info['time']) >= time.time() - data['cycle'] * 60:
                    if day_limit and day_limit_conf.push_num(data["id"]) >= day_limit:
                        return

                    s_list = [">通知类型：SSH登录失败告警",
                              ">告警内容：<font color=#ff0000>{} 分钟内登录失败超过 {} 次</font> ".format(
                                  data['cycle'], data['count'])]

                    msg = SitePushMsgCollect.ssh_login_error(s_list)

                    for m_module in data['module'].split(','):
                        if m_module == 'sms':
                            continue
                        elif m_module == 'wx_account':
                            result[m_module] = ToWechatAccountMsg.ssh_login_error(data['count'])
                            continue

                        sdata = public.get_push_info('SSH登录失败告警', s_list)
                        sdata["push_type"] = 'SSH登录失败告警'
                        result[m_module] = sdata
                    
                    day_limit_conf.set_push(data["id"])
                    return result

        elif data['type'] in ['services']:
            ser_name = data['project']

            server_list, default = self.__get_services()
            if server_list is None:
                return public.returnMsg(False, "服务未安装，跳过.")
            if ser_name not in [v["value"] for v in server_list]:
                return public.returnMsg(False, "服务未安装，跳过.")
            status = self.get_server_status(ser_name)
            if status > 0:
                return public.returnMsg(False, "状态正常，跳过.")
            else:
                return self.__get_service_result(data)

        elif data["type"] == "project_status":
            return self._get_project_status_push_data(data)

        return public.returnMsg(False, "未达到阈值，跳过.")

    def get_records_calc(self, skey, table, stype=0):
        '''
            @name 获取指定表数据是否发生改变
            @param skey string 缓存key
            @param table db 表对象
            @param stype int 0:计算总条数 1:只计算删除
            @return array
                total int 总数

        '''
        total_add = 0
        total_del = 0

        # 获取当前总数和最大索引值
        u_count = table.count()
        u_max = table.order('id desc').getField('id')

        n_data = {'count': u_count, 'max': u_max}
        tmp = public.get_cache_func(skey)['data']
        if not tmp:
            public.set_cache_func(skey, n_data)
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
                t1_add = 0
                n_count = u_count - pre_count  # 上次记录后新增的条数

                if u_max > n_data['max']:
                    n_idx = u_max - n_data['max']  # 上次记录后新增的索引差
                    if n_count < n_idx: t1_del = n_idx - n_count

                # 新纪录除开删除，全部计算为新增
                t1_add = n_count - t1_del
                if t1_add > 0: total_add += t1_add

                total_del += t1_del

            public.set_cache_func(skey, {'count': u_count, 'max': u_max})
        return total_add, total_del, u_count

    def __check_endtime(self, siteName, cycle, project_type=''):
        """
        @name 检测到期时间
        @param siteName str 网站名称
        @param cycle int 提前提醒天数
        @param project_type str 网站类型
        """
        info = self.get_site_ssl_info(public.get_webserver(), siteName, project_type)
        if info:
            endtime = self.get_unixtime(info['notAfter'], '%Y-%m-%d')
            day = int((endtime - time.time()) / 86400)
            if day <= cycle:
                return info

        return False

    def __get_ssl_result(self, data, clist, push_keys=[]):
        """
        @ssl到期返回
        @data dict 推送数据
        @clist list 证书列表
        @return dict
        """
        if len(clist) == 0:
            return public.returnMsg(False, "未找到到期证书，跳过.")

        result = {'index': time.time(), 'push_keys': push_keys}

        s_list = ['>即将到期：<font color=#ff0000>{} 张</font>'.format(len(clist))]
        for x in clist:
            s_list.append(">网站：{}  到期：{}".format(x['siteName'], x['notAfter']))

        msg = SitePushMsgCollect.ssl(s_list, data["title"])
        for m_module in data['module'].split(','):
            sdata = self.__push.format_msg_data()
            if m_module in ['sms']:
                sdata['sm_type'] = 'ssl_end|宝塔面板SSL到期提醒'
                sdata['sm_args'] = public.check_sms_argv({
                    'name': public.get_push_address(),
                    'website': public.push_argv(clist[0]["siteName"]),
                    'time': clist[0]["notAfter"],
                    'total': len(clist)
                })
            elif m_module == "wx_account":
                sdata = ToWechatAccountMsg.ssl(len(clist))
            else:
                sdata = public.get_push_info('宝塔面板SSL到期提醒', s_list)
                sdata["push_type"] = '网站证书(SSL)到期'
            result[m_module] = sdata
        return result

    # 服务停止返回
    def __get_service_result(self, data):
        s_idx = int(time.time())
        if s_idx < data['index'] + data['interval']:
            return public.returnMsg(False, "未达到间隔时间，跳过.")
        
        day_limit = None
        if "day_limit" in data:
            try:
                day_limit = int(data["day_limit"])
            except ValueError:
                day_limit = None

        day_limit_conf = DayLimit()
        if day_limit and day_limit_conf.push_num(data["id"]) >= day_limit:
            return public.returnMsg(False, "推送次数达到上限，跳过.")


        result = {'index': s_idx}
        s_list = [
            ">服务类型：" + data["project"],
            ">服务状态：【" + data["project"] + "】服务已停止"]
        restart = None
        if data["count"] == 1:
            self._services_start(data["project"])
            if not self.check_run(data["project"]):
                restart = False
                s_list[1] = ">服务状态：【" + data["project"] + "】服务重启失败"
            else:
                restart = True
                s_list[1] = ">服务状态：【" + data["project"] + "】服务重启成功"

        SitePushMsgCollect.services(s_list, data['title'])

        for m_module in data['module'].split(','):
            result[m_module] = self.__push.format_msg_data()

            if m_module in ['sms']:
                result[m_module]['sm_type'] = 'servcies'
                result[m_module]['sm_args'] = {'name': '{}'.format(public.GetConfigValue('title')),
                                               'product': data["project"], 'product1': data["project"]}
            elif m_module == "wx_account":
                result[m_module] = ToWechatAccountMsg.services(data["project"], restart=restart)
            else:
                sdata = public.get_push_info('堡塔服务停止告警', s_list)
                sdata["push_type"] = "服务停止告警"
                result[m_module] = sdata

        day_limit_conf.set_push(data["id"])
        return result

    @staticmethod
    def _services_start(service_name):
        if service_name == "php-fpm":
            base_path = "/www/server/php"
            if not os.path.exists(base_path):
                return None
            for p in os.listdir(base_path):
                init_file = os.path.join("/etc/init.d", "php-fpm-{}".format(p))
                if not os.path.isfile(init_file):
                    return None
                public.ExecShell("{} start".format(init_file))
        elif service_name == 'mysql':
            init_file = os.path.join("/etc/init.d", "mysqld")
            public.ExecShell("{} start".format(init_file))

        elif service_name == 'apache':
            init_file = os.path.join("/etc/init.d", "httpd")
            public.ExecShell("{} start".format(init_file))

        else:
            init_file = os.path.join("/etc/init.d", service_name)
            public.ExecShell("{} start".format(init_file))

    def _get_project_status_push_data(self, data):
        model_obj = import_module(".{}".format(self._to_project_model(data["cycle"])), package="projectModel")
        push_count_data = self._project_push_count()
        if len(push_count_data.get(str(data["project"]), [])) >= data["push_count"]:
            return None
        model_main_obj = model_obj.main()
        running, project_name = getattr(model_main_obj, "get_project_status")(data["project"])
        if running is not False:
            return None
        restart = None
        s_list = [
            ">项目类型：" + self._to_project_type(data["cycle"]) + "项目",
            ">项目名称：" + project_name,
            ">项目状态：检查到项目状态为停止"]

        if int(data["count"]) == 1:
            get_obj = public.dict_obj()
            get_obj.project_name = project_name
            result = getattr(model_main_obj, "start_project")(get_obj)
            if result["status"] is True:
                restart = True
                s_list[2] = ">项目状态：检查到项目状态为停止，现已重启成功"
            else:
                restart = False
                s_list[2] = ">项目状态：检查到项目状态为停止，尝试重启但失败"

        s_idx = int(time.time())
        result = {'index': s_idx}
        sdata = public.get_push_info('堡塔项目停止告警', s_list)
        sdata["push_type"] = "项目停止告警"
        SitePushMsgCollect.project_status(s_list, data["title"])

        for m_module in data['module'].split(','):
            result[m_module] = self.__push.format_msg_data()
            if m_module == "sms":
                continue
            elif m_module == "wx_account":
                result[m_module] = ToWechatAccountMsg.project_status(project_name, restart=restart)
            else:
                result[m_module] = sdata
        if str(data["project"]) in push_count_data:
            push_count_data[str(data["project"])].append(s_idx)
        else:
            push_count_data[str(data["project"])] = [s_idx]
        self._save_project_push_count()
        return result

    def _project_push_count(self):
        if hasattr(self, "project_push_count_data"):
            return self.project_push_count_data
        filename = "{}/data/push/tips/project_status.json".format(public.get_panel_path())
        if not os.path.exists(filename):
            self.project_push_count_data = {}
        else:
            data = public.readFile(filename)
            if data is False:
                self.project_push_count_data = {}
            else:
                try:
                    self.project_push_count_data = json.loads(data)
                except json.JSONDecodeError:
                    self.project_push_count_data = {}

        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        for key, value in self.project_push_count_data.items():
            new_value = []
            for v in value:
                if v >= today:
                    new_value.append(v)
            self.project_push_count_data[key] = new_value

        return self.project_push_count_data

    def _save_project_push_count(self):
        if not hasattr(self, "project_push_count_data"):
            return
        filename = "{}/data/push/tips/project_status.json".format(public.get_panel_path())
        public.writeFile(filename, json.dumps(self.project_push_count_data))

    def _remove_project_push_count_by_id(self, project_id):
        if not hasattr(self, "project_push_count_data"):
            self._project_push_count()
        self.project_push_count_data[str(project_id)] = []
        filename = "{}/data/push/tips/project_status.json".format(public.get_panel_path())
        public.writeFile(filename, json.dumps(self.project_push_count_data))

    def get_task_template(self):
        res = public.readFile(self.__task_template)
        if not res:
            return "常用告警设置", [{}]
        res_data = json.loads(res)
        web, web_by_type = self.__get_web()
        res_data["ssl"]["field"][0]["items"].extend(web)
        res_data["project_status"]["field"][1]["all_items"] = web_by_type
        res_data["project_status"]["field"][1]["items"] = web_by_type[0]
        _ls, default = self.__get_services()
        if not _ls:
            del res_data["services"]
        else:
            res_data["services"]["field"][0]["items"] = _ls
            res_data["services"]["field"][0]["default"] = default
        return "常用告警设置", [v for v in res_data.values()]

    @staticmethod
    def get_view_msg(task_id, task_data):
        task_data["tid"] = view_msg.get_tid(task_data)
        task_data["view_msg"] = view_msg.get_msg_by_type(task_data)
        if task_data["tid"] in ("site_push@9", "site_push@6"):
            if task_data["count"] == 0:
                task_data["count"] == 2
        return task_data

    def __get_web(self):
        items = []
        items_by_type = [[], [], [], [], []]
        res_list = public.M('sites').field('id,name,project_type').select()
        for i in res_list:
            items.append({
                "title": i["name"] + "[" + i["project_type"] + "]",
                "value": i["name"]
            })
            if i["project_type"] == "PHP" or i["project_type"] == "proxy":
                continue
            idx = self._to_project_id(i["project_type"])
            if idx is None:
                continue
            items_by_type[idx].append({
                "title": i["name"],
                "value": i["id"]
            })
        return items, items_by_type

    def __get_services(self):
        ws = public.get_webserver()
        default = None
        res_list = []
        php_path = "/www/server/php"
        if os.path.exists(php_path) and glob.glob(php_path + "/*"):
            res_list.append({
                "title": "php-fpm服务停止",
                "value": "php-fpm"
            })
        if os.path.exists('/etc/init.d/nginx'):
            if ws == "nginx":
                default = "nginx"
            res_list.append({
                "title": "nginx服务停止",
                "value": "nginx"
            })
        if os.path.exists('/etc/init.d/httpd'):
            if ws == "apache":
                default = "apache"
            res_list.append({
                "title": "apache服务停止",
                "value": "apache"
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
        if not res_list:
            return None, None
        if not default:
            default = res_list[0]["value"]
        return res_list, default

    def get_push_config(self, get: public.dict_obj):
        task_id = get.id
        push_list = self.__push._get_conf()
        if 'site_push' not in push_list:
            push_list["site_push"] = {}

        res_data = public.returnMsg(False, '未找到指定配置.')
        res_data['code'] = 100
        if not task_id in push_list["site_push"]:
            return res_data

        return push_list["site_push"][task_id]

    def _get_no_user_tip(self) -> str:
        """没有用户信息的需要，写一个临时文件做标记，并尽可能保持不变"""
        tip_file = "{}/data/no_user_tip.pl".format(panelPath)
        if not os.path.exists(tip_file):
            data: str = public.get_network_ip()
            data = "没有用户信息时的标记文件\n" + hashlib.sha256(data.encode("utf-8")).hexdigest()
            public.writeFile(tip_file, data)
        else:
            data = public.readFile(tip_file)
            if isinstance(data, bool):
                os.remove(tip_file)
                return self._get_no_user_tip()
        return data

    def user_can_request_hour(self):
        """根据哈希值，输出一个用户可查询"""
        user_info = public.get_user_info()
        if not bool(user_info):
            user_info = self._get_no_user_tip()
        else:
            user_info = json.dumps(user_info)

        hash_value = hashlib.md5(user_info.encode("utf-8")).digest()
        sum_value = 0
        for i in range(4):
            sum_value = sum_value + int.from_bytes(hash_value[i * 32: (i + 1) * 32], "big")

        res = sum_value % 24
        return res


class ViewMsgFormat(object):
    _FORMAT = {
        "ssl": (
            lambda x: "<span>剩余时间小于{}天{}</span>".format(
                x.get("cycle"),
                ("(如未处理，次日会重新发送1次，持续%s天)" % str(x.get("push_count", '0')) if str(x.get("push_count", '0')) != '0' else "")
            )
        ),
        "site_endtime": (),
        "panel_pwd_endtime": (),
        "panel_login": (
            lambda x: "<span>面板登录时，发出告警</span>"
        ),
        "ssh_login": (
            lambda x: "<span>检测到SSH登录本机时，发出告警</span>"
        ),
        "ssh_login_error": (
            lambda x: "<span>{}分钟内连续{}次失败登录触发,每{}秒后再次检测</span>".format(
                x.get("cycle"), x.get("count"), x.get("interval"),
            )
        ),
        "services": (
            lambda x: "<span>服务停止时发送一次通知,{}秒后再次检测</span>".format(x.get("interval"))
        ),
        "project_status": (
            lambda x: "<span>项目停止时发送通知，{}秒后再次检测，每日发送{}次</span>".format(x.get("interval"), x.get("push_count"))
        ),
        "panel_safe_push": (
            lambda x: "<span>面板出现如:用户变更、面板日志删除、开启开发者等危险操作时发送告警</span>"
        ),
        "panel_update": (
            lambda x: "<span>检测到新的版本时发送一次通知</span>"
        )
    }

    _TID = {
        "ssl": "site_push@0",
        "site_endtime": "site_push@1",
        "panel_pwd_endtime": "site_push@2",
        "panel_login": "site_push@3",
        "ssh_login": "site_push@4",
        "ssh_login_error": "site_push@5",
        "services": "site_push@6",
        "panel_safe_push": "site_push@7",
        "panel_update": "site_push@8",
        "project_status": "site_push@9",
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
    def ssl(count: int):
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "网站SSL到期提醒"
        msg.msg = "有{}个网站的证书将到期,会影响访问".format(count)
        msg.next_msg = "请登录面板，在[网站]中进行续签操作"
        return msg

    @staticmethod
    def site_endtime(count: int):
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "网站到期提醒"
        msg.msg = "有{}个站点即将到期,可能影响网站访问".format(count)
        msg.next_msg = "请登录面板，在[网站]中查看详情"
        return msg

    @staticmethod
    def panel_pwd_endtime(limit_days: int):
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "面板密码到期提醒"
        msg.msg = "登录密码将于{}天后过期".format(limit_days)
        msg.next_msg = "请登录面板，在[设置]中修改密码"
        return msg

    # 特殊，请没有next
    @staticmethod
    def panel_login(name, ip, login_type, address, login_time):
        msg = WxAccountLoginMsg.new_msg()
        msg.login_name = name
        msg.login_ip = ip
        msg.login_type = login_type
        msg.address = address
        # msg.time = login_time
        return msg

    @staticmethod
    def ssh_login(login_ip: str):
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

    @staticmethod
    def ssh_login_error(count: int):
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "SSH登录失败告警"
        msg.msg = "登录失败超过{}次".format(count)
        msg.next_msg = "请登录面板，查看SSH登录日志"
        return msg

    # 特殊，请没有next
    @staticmethod
    def services(service_name: str, restart):
        msg = WxAccountMsg.new_msg()
        if len(service_name) > 14:
            service_name = service_name[:11] + "..."
        msg.thing_type = "{}服务停止提醒".format(service_name)
        if restart is None:
            msg.msg = "{}服务已停止".format(service_name)
        elif restart is True:
            msg.msg = "{}服务重启成功".format(service_name)
        else:
            msg.msg = "{}服务重启失败".format(service_name)
        return msg

    @staticmethod
    def panel_safe_push(data_list: list):
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "面板安全告警"
        the_msg = []
        for d in data_list:
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

    @staticmethod
    def panel_update(n_ver: str):
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "面板更新提醒"
        msg.msg = "最新版:{}已发布".format(n_ver)
        msg.next_msg = "您可以登录面板，执行更新"
        return msg

    @staticmethod
    def project_status(project_name, restart):
        msg = WxAccountMsg.new_msg()
        if len(project_name) >= 14:
            project_name = project_name[:11] + "..."
        msg.thing_type = "项目停止告警"
        if restart is None:
            msg.msg = "项目{}已停止".format(project_name)
        elif restart is False:
            msg.msg = "项目{}重启成功".format(project_name)
        else:
            msg.msg = "项目{}重启失败".format(project_name)
        return msg


class DayLimit:
    _TIP_FILE = '{}/data/push/tips/day_limit.tip'.format(public.get_panel_path())

    def __init__(self):
        self._tip = None

    @property
    def tips(self) -> dict:
        if self._tip is not None:
            return self._tip

        if os.path.exists(self._TIP_FILE):
            try:
                tip = json.loads(public.readFile(self._TIP_FILE))
            except (json.JSONDecodeError, TypeError):
                tip = {}
        else:
            tip = {}

        now_day = datetime.now()
        if "day_limit_today_time" in tip:
            old_day = datetime.fromtimestamp(tip["day_limit_today_time"])
            if old_day.date() != now_day.date():
                tip = dict()
                tip["day_limit_today_time"] = now_day.timestamp()
        else:
            tip["day_limit_today_time"] = now_day.timestamp()

        self._tip = tip
        return self._tip

    def _save_tip(self):
        if self._tip is not None:
            public.writeFile(self._TIP_FILE, json.dumps(self._tip))

    def push_num(self, task_id):
        if not isinstance(task_id, str):
            task_id = str(task_id)
        if task_id not in self.tips:
            return 0
        return self.tips[task_id]

    def set_push(self, task_id):
        if not isinstance(task_id, str):
            task_id = str(task_id)
        if task_id not in self.tips:
            self.tips[task_id] = 1
        else:
            self.tips[task_id] += 1
        self._save_tip()

    def clear_push(self, task_id):
        if not isinstance(task_id, str):
            task_id = str(task_id)
        if task_id in self.tips:
            self.tips[task_id] = 0
            self._save_tip()
