# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# # Author: sww <sww@bt.cn>
# -------------------------------------------------------------------
# 网站日志关键字告警模块
# ------------------------------
import os
import sys
import json
import re
import traceback
from datetime import datetime

if '/www/server/panel/class' not in sys.path:
    sys.path.append("/www/server/panel/class")
import public, crontab
from urllib.parse import quote


class main:

    # 删除定时任务
    def del_crontab(self, get):
        """
        删除定时任务
        :param get:
        :return:
        """
        try:
            p = crontab.crontab()
            id = public.M('crontab').where("name=?", "[勿删]网站日志关键字告警任务").getField('id')
            args = public.to_dict_obj({"id": id})
            p.DelCrontab(args)
        except:
            pass

    # 添加定时任务
    def add_crontab(self, cycle: int):
        """
        添加定时任务
        :param get:
        cycle:检查周期
        :return:
        """
        pypath = '/www/server/panel/script/site_log_push.py'
        p = crontab.crontab()
        args = {
            "name": "[勿删]网站日志关键字告警任务",
            "type": "minute-n",
            "where1": cycle,
            "hour": "",
            "minute": "",
            "week": "",
            "sType": "toShell",
            "sName": "",
            "backupTo": "localhost",
            "save": '',
            "sBody": "btpython {} >> {} 2>&1".format(pypath, '/www/server/panel/logs/site_log_psuh.log'),
            "urladdress": "undefined"
        }
        print(p.AddCrontab(args))

    # 获取网站日志关键字告警配置
    def get_site_log_push(self, get: None):
        data = {'sitenames': [], 'cycle': 5, 'keys': [], 'channel': ''}
        if os.path.exists('/www/server/panel/config/site_log_push.json'):
            data = json.loads(open('/www/server/panel/config/site_log_push.json').read())
        return data

    # 设置网站日志关键字告警配置
    def set_push_task(self, get):
        """
        添加或删除推送任务
        :param get:
        sitename:站点名称  存在删除 不存在添加
        cycle:检查周期
        keys:关键字列表
        :return:
        """
        try:
            old_data = self.get_site_log_push(None)
            if hasattr(get, 'cycle') and get['cycle'] != '' and get['cycle'] != '0' and get['cycle'] != 0:
                old_data['cycle'] = int(get['cycle'])
                self.del_crontab(None)
                self.add_crontab(old_data['cycle'])
            if hasattr(get, 'sitename') and get['sitename'] != '':
                if get['sitename'] not in old_data['sitenames']:
                    old_data['sitenames'].append(get['sitename'])
                else:
                    old_data['sitenames'].remove(get['sitename'])
            if hasattr(get, 'keys') and get['keys'] != '' and get['keys'] != '[]':
                old_data['keys'] = list(set(json.loads(get['keys'])))
            if hasattr(get, 'channel') and get['channel'] != '':
                old_data['channel'] = get['channel']
            public.writeFile('/www/server/panel/config/site_log_push.json', json.dumps(old_data))
            return public.returnMsg(True, '设置成功!')
        except:
            print(traceback.format_exc())
            return public.returnMsg(False, '设置失败!')

    def get_site_log_push_status(self, get):
        try:
            if not hasattr(get, 'sitename'):
                return public.returnMsg(False, '参数错误!')
            sitename = get['sitename']
            config = self.get_site_log_push(None)
            status = False
            if sitename in config['sitenames']:
                status = True
            return {'status': status, 'config': config}
        except:
            return {'status': False, 'config': {}}

    # 获取日志路径
    def get_site_log_file(self, get):
        res = public.M('sites').where('name=?', (get.siteName,)).select()[0]['project_type'].lower()
        if res == 'php':
            res = ''
        else:
            res = res + '_'

        serverType = public.get_webserver()
        if serverType == "nginx":
            config_path = '/www/server/panel/vhost/nginx/{}.conf'.format(res + get.siteName)
            config = public.readFile(config_path)
            if not config:
                return public.returnMsg(False, "站点配置文件丢失")
            log_file = self.nginx_get_log_file_path(config, get.siteName)
        elif serverType == 'apache':
            config_path = '/www/server/panel/vhost/apache/{}.conf'.format(res + get.siteName)
            config = public.readFile(config_path)
            if not config:
                return public.returnMsg(False, "站点配置文件丢失")
            log_file = self.apache_get_log_file_path(config, get.siteNameg)
        else:
            return public.returnMsg(False, "不支持的Web服务器类型")
        return {
            "status": True,
            "log_file": log_file,
            "msg": "获取成功"
        }

    def nginx_get_log_file_path(self, nginx_config: str, site_name: str, is_error_log: bool = False):
        log_file = None
        if is_error_log:
            re_data = re.findall(r"error_log +(/(\S+/?)+) ?(.*?);", nginx_config)
        else:
            re_data = re.findall(r"access_log +(/(\S+/?)+) ?(.*?);", nginx_config)
        if re_data is None:
            log_file = None
        else:
            for i in re_data:
                file_path = i[0].strip(";")
                if file_path != "/dev/null" and not file_path.endswith("purge_cache.log"):
                    if os.path.isdir(os.path.dirname(file_path)):
                        log_file = file_path
                        break

        logsPath = '/www/wwwlogs/'
        if log_file is None:
            if is_error_log:
                log_file = logsPath + site_name + '.log'
            else:
                log_file = logsPath + site_name + '.error.log'
            if not os.path.isfile(log_file):
                log_file = None

        return log_file

    def apache_get_log_file_path(self, apache_config: str, site_name: str, is_error_log: bool = False):
        log_file = None
        if is_error_log:
            re_data = re.findall(r'''ErrorLog +['"]?(/(\S+/?)+)['"]? ?(.*?)\n''', apache_config)
        else:
            re_data = re.findall(r'''CustomLog +['"]?(/(\S+/?)+)['"]? ?(.*?)\n''', apache_config)
        if re_data is None:
            log_file = None
        else:
            for i in re_data:
                file_path = i[0].strip('"').strip("'")
                if file_path != "/dev/null":
                    if os.path.isdir(os.path.dirname(file_path)):
                        log_file = file_path
                        break

        logsPath = '/www/wwwlogs/'
        if log_file is None:
            if is_error_log:
                log_file = logsPath + site_name + '-access_log'
            else:
                log_file = logsPath + site_name + '-error_log'
            if not os.path.isfile(log_file):
                log_file = None

        return log_file

    # 获取日志内容
    def run(self, get=None):
        public.set_module_logs("sitelogpush", "run_push")
        print('开始运行网站日志检查任务【{}】'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        config = self.get_site_log_push(None)
        endtime = int(datetime.now().timestamp()) - 60 * int(config['cycle'])
        result = {}
        if not config:
            return
        for sitename in config['sitenames']:
            print('开始检查站点【{}】'.format(sitename))
            log_file = self.get_site_log_file(public.to_dict_obj({'siteName': sitename}))
            if not log_file['status']:
                continue
            if not os.path.exists(log_file['log_file']):
                continue
            with open(log_file['log_file'], 'r') as f:
                lines = f.readlines()
                lines.reverse()
                logs = ''
                for line in lines:
                    print(line)
                    try:
                        date_str = line.split('[')[1].split()[0]
                        date_obj = datetime.strptime(date_str, '%d/%b/%Y:%H:%M:%S')
                        timestamp = int(date_obj.timestamp())
                        print(timestamp, endtime)
                        if timestamp < endtime:
                            break
                    except:
                        print(traceback.format_exc())
                        continue
                    logs += line
            for key in config['keys']:
                num = logs.count(key)
                url_code_num = logs.count(quote(key))
                if num < 0: num = 0
                if url_code_num < 0: url_code_num = 0
                if num > 0 or url_code_num > 0:
                    if sitename not in result:
                        result[sitename] = {}
                    result[sitename][key] = num + url_code_num
            if sitename in result:
                print('站点【{}】出现关键字告警：'.format(sitename))
            else:
                print('站点【{}】未出现关键字告警'.format(sitename))
        if result:
            self.send_msg(result)
            print('告警消息发送成功【{}】'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        print('网站日志检查任务结束【{}】'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        return public.returnMsg(True, '运行成功!')

    # 发送消息
    def send_msg(self, result: dict):
        channels = self.get_site_log_push(None)['channel']
        title = '网站日志关键字告警'
        msg = []
        print(result)
        for name, res in result.items():
            pust_msg = '站点【{}】出现关键字告警：'.format(name)
            for key, num in res.items():
                pust_msg += '【{}】出现【{}】次；'.format(key, num)
            msg.append(pust_msg)
        data = public.get_push_info(title, msg)
        for channel in channels.split(','):
            obj = public.init_msg(channel)
            obj.send_msg(data['msg'])

    def get_logs(self, get=None):
        log_path = '/www/server/panel/logs/site_log_psuh.log'
        if not os.path.exists(log_path):
            return public.returnMsg(True, '日志文件不存在!')
        return public.returnMsg(True, public.readFile(log_path))
