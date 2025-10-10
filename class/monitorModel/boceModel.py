# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# # Author: sww <sww@bt.cn>
# -------------------------------------------------------------------
# 拨测模块
# ------------------------------
import warnings
warnings.filterwarnings("ignore", message=r".*doesn't\s+match\s+a\s+supported\s+version", module="requests")
import codecs
import json
import os
import sys
import time
import traceback
import requests

os.chdir("/www/server/panel")
sys.path.append("class/")

from projectModel.base import projectBase  # line:6
import public
import crontab
import socket
from urllib.parse import urlparse


os.chdir('/www/server/panel')
sys.path.insert(0, 'class/')
import PluginLoader


class main(projectBase):
    alarm_dict = {
        'keyword': "网站关键词告警",
        'status_code': "网站请求错误告警",
        'delay': "网站响应时间告警",
        'similarity': "网站内容变化告警",
        'size': "网站大小变化告警",
        'sensitive': "网站敏感词告警"
    }
    alarm = 0

    def __init__(self):
        try:
            public.M('boce_task')
        except:
            public.M('boce_task').execute('''CREATE TABLE IF NOT EXISTS boce_task (
            id      INTEGER      PRIMARY KEY AUTOINCREMENT,
            name    STRING (64),
            url     STRING (128),
            status  INTEGER,
            channel STRING (128),
            cycle   INTEGER default 10,
            addtime INTEGER default 0,
            address STRING (128) default 'localhost',
            keyword STRING (128) default '',
            status_code BOOLEAN default 0,
            delay INTEGER default 0,
            similarity TEXT default '',
            size INTEGER default 0,
            sensitive BOOLEAN default 0
        )''', ())
        try:
            public.M('boce_list')
        except:
            public.M('boce_list').execute('''CREATE TABLE IF NOT EXISTS boce_list (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            pid     INTEGER,
            data    TEXT,
            status  INTEGER,
            addtime INTEGER
            )''', ())

        # try:
        #     public.M('nodes')
        # except:
        #     public.M('nodes').insert(
        #         {"name": "coll_boce", "title": "拔测监控", "level": 1, "sort": 10.0, "state": 1, "p_nid": 0, "ps": ""})

        # 查询boce_task是否有sensitive属性，默认为0
        if not public.M('boce_task').where("sensitive=?", 0).count():
            public.M('boce_task').execute('''ALTER TABLE boce_task ADD COLUMN sensitive BOOLEAN default 0 ''', ())
        # 查询boce_task是否有size属性，默认为0
        if not public.M('boce_task').where("size=?", 0).count():
            public.M('boce_task').execute('''ALTER TABLE boce_task ADD COLUMN size INTEGER default 0 ''', ())
        # 查询boce_task是否有similarity属性，默认为0
        if not public.M('boce_task').where("similarity=?", "%").count():
            public.M('boce_task').execute('''ALTER TABLE boce_task ADD COLUMN similarity TEXT default '' ''', ())
        # 查询boce_task是否有delay属性，默认为0
        if not public.M('boce_task').where("delay=?", 0).count():
            public.M('boce_task').execute('''ALTER TABLE boce_task ADD COLUMN delay INTEGER default 0''', ())
        # 查询boce_task是否有status_code属性，默认为0
        if not public.M('boce_task').where("status_code=?", 0).count():
            public.M('boce_task').execute('''ALTER TABLE boce_task ADD COLUMN status_code BOOLEAN default 0''', ())
        # 查询boce_task是否有keyword属性，默认为空
        if not public.M('boce_task').where("keyword=?", '%').count():
            public.M('boce_task').execute('''ALTER TABLE boce_task ADD COLUMN keyword STRING (128) default '' ''', ())
        # 查询boce_task是否有address属性，默认为node
        if not public.M('boce_task').where("address=?", '%').count():
            public.M('boce_task').execute('''ALTER TABLE boce_task ADD COLUMN address STRING (128) default 'node' ''',
                                          ())
        if not public.M('boce_task').where("channel=?", '%').count():
            public.M('boce_task').execute('''ALTER TABLE boce_task ADD COLUMN channel text default ''''', ())
        if not public.M('boce_task').where("alarm_count=?", '%').count():
            public.M('boce_task').execute('''ALTER TABLE boce_task ADD COLUMN alarm_count integer default -1 ''', ())

    # 取拔测任务列表
    def get_list(self, args):
        try:
            if 'p' not in args: args.p = '1'
            args.p = int(args.p)
            if 'row' not in args: args.row = '10'
            args.row = int(args.row)
            content = []
            if not hasattr(args, 'sid'): return public.returnMsg(False, '错误的参数!')
            sid = args.sid
            domains = public.M('domain').where('pid=?', (sid,)).field('name').order("id desc").select()
            domains = [i['name'] for i in domains]
            sName = public.M('sites').where('id=?', (sid,)).getField('name')
            if sName not in domains: domains.append(sName)
            # 使用字典来存储任务，以避免重复
            unique_tasks = {}

            # 遍历去重后的域名，查询与之相关的拔测任务
            for domain in set(domains):
                where = "name='{0}' OR url like '%{0}%'".format(domain)
                tasks = public.M('boce_task').where(where, ()).order("id desc").select()

                for task in tasks:
                    task_key = (task['name'], task['url'])  # 使用任务名称和URL作为唯一标识符
                    if task_key not in unique_tasks:
                        unique_tasks[task_key] = task

            # 将字典中的唯一任务转换为列表
            content = list(unique_tasks.values())
            count = len(content)
            data = public.get_page(count, args.p, args.row)
            data['data'] = content[(args.p - 1) * 10:args.p * 10]

            bock_list_sql = public.M('boce_list')

            for i in range(len(data['data'])):
                data['data'][i]['last_run_time'] = bock_list_sql.where('pid=?', (data['data'][i]['id'],)).order(
                    'id desc').getField('addtime')
                if type(data['data'][i]['last_run_time']) == list and len(data['data'][i]['last_run_time']) > 0:
                    data['data'][i]['last_run_time'] = data['data'][i]['last_run_time'][0]
                elif not data['data'][i]['last_run_time']:
                    data['data'][i]['last_run_time'] = 0

            for alarm in self.alarm_dict.keys():
                for i in data['data']:
                    if not i.get(alarm):
                        del i[alarm]
            for i in data['data']:
                if 'delay' in i.keys():
                    i['trigger_condition'] = "响应延迟大于{}ms告警".format(int(i['delay'] * 1000))
                    i['delay'] = int(i['delay'] * 1000)
                elif 'similarity' in i.keys():
                    i['similarity'] = 1
                    i['trigger_condition'] = "内容变化10%告警"
                elif 'size' in i.keys():
                    i['size'] = 1
                    i['trigger_condition'] = "响应大小相差20%告警"
                elif 'sensitive' in i.keys():
                    i['trigger_condition'] = "含有敏感词告警"
                elif 'status_code' in i.keys():
                    i['trigger_condition'] = "状态码除【200,301,302】告警"
                elif 'keyword' in i.keys():
                    i['trigger_condition'] = "不含有关键字【{}】告警".format(i['keyword'])
                else:
                    i['trigger_condition'] = ''
            for i in data['data']:
                status = public.M('crontab').where("save=?", "boce_id_{}".format(i['id'])).getField('status')
                try:
                    status = int(status)
                except:
                    status = 0
                i['status'] = status
            return data
        except:
            return traceback.format_exc()

    # 取指定拔测任务
    def get_find(self, args):
        if 'id' not in args: return public.returnMsg(False, '错误的参数!')
        id = args.id
        return public.M('boce_task').where('id=?', id).find()

    # 创建拔测任务
    def create(self, args):
        try:
            public.set_module_logs('site_boce_create', 'create', 1)
            # try:
            #     if os.path.exists('/etc/init.d/bt_syssafe'):
            #         res = public.readFile('/www/server/panel/plugin/syssafe/config.json')
            #         if res:
            #             res = json.loads(res)
            #             if res['open'] == True:
            #                 return public.returnMsg(False, '系统安全已开启，无法添加拔测任务，请关闭【系统加固】中的【计划任务加固】后在重试！')
            # except:
            #     pass
            if len(self.alarm_dict.keys() & set(args.__dict__.keys())) != 1:
                return public.returnMsg(False, '参数错误,一次只能设置一种告警任务!')
            pdata = {}
            pdata['name'] = args.name
            pdata['url'] = args.url.strip()
            pdata['address'] = args.address
            pdata['keyword'] = str(args.keyword) if hasattr(args, 'keyword') else ''
            pdata['status_code'] = args.status_code if hasattr(args, 'status_code') else 0
            pdata['delay'] = (float(args.delay) / 1000) if hasattr(args, 'delay') else 0
            pdata['alarm_count'] = args.alarm_count if hasattr(args, 'alarm_count') else 0
            if hasattr(args, 'similarity'):
                if args.similarity:
                    status = self.get_url_status(public.to_dict_obj({'url': pdata['url']}))
                    pdata['similarity'] = status['msg']['data'] if status['status'] else '11111'
            if hasattr(args, 'size'):
                if args.size == 0:
                    pdata['size'] = 0
                else:
                    status = self.get_url_status(public.to_dict_obj({'url': pdata['url']}))
                    pdata['size'] = status['msg']['size'] if status['status'] else 1
                    if pdata['size'] == 0: pdata['size'] = 1
            pdata['sensitive'] = args.sensitive if hasattr(args, 'sensitive') else 0
            pdata['channel'] = args.get('channel', '')
            if pdata['url'].find('http://') == -1 and pdata['url'].find('https://') == -1:
                return public.returnMsg(False, 'URL地址必需包含http://或https://')
            pdata['cycle'] = int(args.cycle)
            if pdata['cycle'] < 10: return public.returnMsg(False, '拔测周期最短不能少于10分钟')
            if pdata['cycle'] > 60: return public.returnMsg(False, '拔测周期最长不能超过60分钟')
            pdata['status'] = 1
            pdata['addtime'] = int(time.time())
            pdata['id'] = public.M('boce_task').insert(pdata)
            resp=self.create_task(pdata)
            if resp.get("status"):
                public.WriteLog('本地拔测监控', "创建拔测任务[{}]".format(pdata['name']))
                return public.returnMsg(True, '添加成功!')
            else:
                # 定时任务创建失败时，从数据库中删除该任务
                public.M('boce_task').where('id=?', pdata['id']).delete()
                if "系统加固" in resp.get("msg") :
                    return public.returnMsg(False, "开启失败，请检查是否对计划任务开启了系统加固！")
                return public.returnMsg(False, resp.get("msg", "未知错误！"))
        except:
            return public.returnMsg(False, traceback.format_exc())

    # 创建计划任务
    def create_task(self, pdata):
        pypath = '/www/server/panel/class/monitorModel/boceModel.py'
        p = crontab.crontab()
        args = {
            "name": "拔测任务[" + pdata['name'] + "]",
            "type": "minute-n",
            "where1": pdata['cycle'],
            "hour": "",
            "minute": "",
            "week": "",
            "sType": "toShell",
            "sName": "",
            "backupTo": "localhost",
            "save": "boce_id_{}".format(pdata['id']),
            "sBody": "btpython {} {} ".format(pypath, pdata['id']),
            "urladdress": "undefined"
        }
        return p.AddCrontab(args)

    # 发送测试
    def _send_task(self):
        url = self.sql_data['url']
        print('|-开始URL拔测:{}'.format(url))
        # 获取告警方式和告警内容
        result = {}
        try:
            # 发送请求
            print('|-开始发送测试请求')
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': url,
                'Accept-Language': 'en-US,en;q=0.9',
            }

            response = requests.get(url, headers=headers)
            response.encoding = 'utf-8'
            result['isp'] = "本地测试"
            # 获取响应内容
            result['text'] = response.text
            # 获取状态码
            result['http_code'] = response.status_code
            # 获取响应头
            result['header'] = json.dumps(dict(response.headers))
            # 获取请求头
            result['request_header'] = json.dumps(dict(response.request.headers))
            # 获取下载大小
            result['size_download'] = int(len(response.content))
            # 获取下载速度
            result['speed_download'] = result['size_download'] / response.elapsed.total_seconds()
            try:
                try:
                    import pycurl
                except:
                    res = public.ExecShell("curl -V")
                    PYCURL_SSL_LIBRARY = ''
                    if 'nss' in res[0].lower():
                        PYCURL_SSL_LIBRARY = 'nss'
                    if 'openssl' in res[0].lower():
                        PYCURL_SSL_LIBRARY = 'openssl'
                    os.system("btpip uninstall pycurl && export PYCURL_SSL_LIBRARY={} && btpip install --ignore-installed pycurl".format(PYCURL_SSL_LIBRARY))
                    import pycurl
                c = pycurl.Curl()
                c.setopt(c.URL, url)
                c.perform()
                # 获取总时间
                result['total_time'] = float(c.getinfo(pycurl.TOTAL_TIME))
                # 获取域名解析时间
                result['namelookup_time'] = float(c.getinfo(pycurl.NAMELOOKUP_TIME))
                # 获取连接时间
                result['connect_time'] = float(c.getinfo(pycurl.CONNECT_TIME))
                # 获取数据传输开始时间
                result['starttransfer_time'] = float(c.getinfo(pycurl.STARTTRANSFER_TIME))
            except:
                res = public.ExecShell('curl -s -o /dev/null -w "%{{time_total}}||%{{time_namelookup}}||%{{time_connect}}||%{{time_starttransfer}}" {}'.format(url))
                c = res[0].split('||')
                if len(c) == 4:
                    result['total_time'] = float(c[0])
                    result['namelookup_time'] =  float(c[1])
                    result['connect_time'] =  float(c[2])
                    result['starttransfer_time'] =  float(c[3])
            # 获取主ip
            try:
                parsed_url = urlparse(url)
                domain = parsed_url.netloc
                result['primary_ip'] = socket.gethostbyname(domain)
            except:
                result['primary_ip'] = ''
            return result
        except requests.exceptions.SSLError:
            print("|-请求失败，请证书是否匹配且可用！")
            return public.returnMsg(False, "请求失败，请检查证书是否匹配且可用！")
        except:
            # public.print_log(traceback.format_exc())
            print("|-请求失败，请检查域名是否可用！")
            return public.returnMsg(False, "请求失败，请检查域名是否可用！")

    # 获取当前响应大小，状态码，延迟,文本内容
    def get_url_status(self, get):
        if not hasattr(get, 'url'): return public.returnMsg(False, "缺少url参数")
        url = get['url']
        try:
            response = requests.get(url)
            response.encoding = 'utf-8'
            try:
                import pycurl
            except:
                res = public.ExecShell("curl -V")
                PYCURL_SSL_LIBRARY = ''
                if 'nss' in res[0].lower():
                    PYCURL_SSL_LIBRARY = 'nss'
                if 'openssl' in res[0].lower():
                    PYCURL_SSL_LIBRARY = 'openssl'
                os.system("btpip uninstall pycurl && export PYCURL_SSL_LIBRARY={} && btpip install --ignore-installed pycurl".format(PYCURL_SSL_LIBRARY))
                import pycurl
            c = pycurl.Curl()
            c.setopt(c.URL, url)
            c.perform()
            data = {
                'status_code': response.status_code,
                'delay': c.getinfo(pycurl.TOTAL_TIME),
                'size': int(len(response.text.encode("utf-8"))),
                'data': codecs.decode(response.content, 'utf-8')
            }
            return public.returnMsg(True, data)
        except:
            return public.returnMsg(False, "请求出错！")

    # 关键词告警
    def keyword(self, result):
        if not self.sql_data['keyword']: return
        data = []
        kes = []
        keywords = str(self.sql_data['keyword']).split(',')
        for keyword in keywords:
            if keyword not in result['text']:
                kes.append(keyword)
        if kes:
            data.append('{}|{}不存在[{}]！'.format(result['isp'], self.sql_data['url'], ','.join(kes)))
        if data:
            return self.send_notification("关键词告警", data)

    # 状态码告警
    def status_code(self, result):
        if not self.sql_data['status_code']: return
        data = []
        if result['http_code'] not in [200, 301, 302]:
            data.append('{}|{} 状态码：{} !'.format(result['isp'], self.sql_data['url'], result['http_code']))
        if data:
            return self.send_notification("状态码异常告警", data)

    # 响应延迟告警
    def delay(self, result):
        data = []
        if not self.sql_data['delay']: return
        if result['total_time'] > float(self.sql_data['delay']):
            data.append('{}|{}响应时间：{} ms ！'.format(result['isp'], self.sql_data['url'],
                                                       int(result['total_time'] * 1000)))
        if data:
            self.send_notification("响应延迟告警", data)

    # 相似度告警
    def similarity(self, result):
        if not self.sql_data['similarity']: return
        pass

    # 响应大小告警
    def size(self, result):
        if not self.sql_data['size']: return
        data = []
        if abs(len(result['text'].encode("utf-8")) - self.sql_data['size']) / self.sql_data['size'] > 0.2:
            data.append('{}|{}差异超过记录值的20%！'.format(result['isp'], self.sql_data['url']))
        self.sql_data['size'] = len(result['text'].encode("utf-8")) if len(result['text'].encode("utf-8")) else 1
        public.M('boce_task').where('id=?', self.sql_data['id']).update(self.sql_data)
        if data:
            return self.send_notification("响应大小告警", data)

    # 敏感词告警
    def sensitive(self, result):
        if not self.sql_data['sensitive']: return
        pass

    # 删除拔测任务
    def remove(self, args):
        if 'id' not in args: return public.returnMsg(False, '错误的参数!')
        id = args.id
        pdata = public.M('boce_task').where('id=?', id).find()
        public.M('boce_task').where('id=?', id).delete()
        public.M('boce_list').where('pid=?', id).delete()
        self.remove_task(id)
        public.WriteLog('拔测监控', "删除拔测任务[{}]".format(pdata['name']))
        return public.returnMsg(True, '删除成功!')

    # 删除计划任务
    def remove_task(self, pid):
        p = crontab.crontab()
        id = public.M('crontab').where("save=?", "boce_id_{}".format(pid)).getField('id')
        args = {"id": id}
        p.DelCrontab(args)

    # 删除指定任务执行记录
    def remove_task_log(self, args):
        if 'id' not in args: return public.returnMsg(False, '错误的参数!')
        id = args.id
        public.M('boce_list').where('id=?', id).delete()
        public.WriteLog('拔测监控', "删除任务记录[{}]".format(id))
        return public.returnMsg(True, '删除成功!')

    # 运行指定任务
    def start(self, args):
        try:
            if 'id' not in args: return public.returnMsg(False, '错误的参数!')
            id = args['id']
            self.sql_data = public.M('boce_task').where('id=?', id).select()
            if not self.sql_data: return public.returnMsg(False, '指定任务不存在!')
            self.sql_data = self.sql_data[0]
            if self.sql_data['address'] == 'node':
                result = PluginLoader.plugin_run("bt_boce", "start", public.to_dict_obj({'id': id}))
                return result
            result = self._send_task()
            if 'status' in result: return result
            if self.sql_data['channel'] and result:
                if self.sql_data['keyword']:
                    self.keyword(result)
                if self.sql_data['status_code']:
                    self.status_code(result)
                if self.sql_data['delay']:
                    self.delay(result)
                if self.sql_data['similarity']:
                    self.similarity(result)
                if self.sql_data['size']:
                    self.size(result)
                if self.sql_data['sensitive']:
                    self.sensitive(result)
            del result['text']
            result = [result]
            pdata = {}
            pdata['status'] = self.get_state(result, id)
            pdata['data'] = json.dumps(result)
            pdata['pid'] = id
            pdata['addtime'] = int(time.time())
            public.M('boce_list').insert(pdata)
            return result
        except:
            return public.returnMsg(False, traceback.format_exc())

    def get_state(self, data, id):
        err = 0
        for n in data:
            if not n: continue
            if n['http_code'] not in [200, 301, 302, 403, 401]: err += 1
        if err > 2:
            return 0
        return 1

    # 获取任务执行记录
    def get_task_log(self, args):
        if 'pid' not in args: return public.returnMsg(False, '错误的参数!')
        pid = args.pid
        if 'p' not in args: args.p = '1'
        args.p = int(args.p)
        data = {}
        count = public.M('boce_list').where("pid=?", pid).order("id desc").count()
        data['page'] = public.get_page(count, args.p, 12)
        data['data'] = public.M('boce_list').where("pid=?", pid).order("id desc").limit(
            '{},{}'.format(data['page']['shift'], data['page']['row'])).select()
        for i in range(len(data['data'])):
            try:
                j_data = json.loads(data['data'][i]['data'])
                total_time = 0
                for d in j_data:
                    total_time += d['total_time']
                data['data'][i]['avgrage'] = float('{:.2f}'.format(total_time / len(j_data)))
                data['data'][i]['data'] = sorted(j_data, key=lambda x: x['total_time'], reverse=True)
                data['data'][i]['max'] = float('{:.2f}'.format(data['data'][i]['data'][0]['total_time']))
                data['data'][i]['max_isp'] = data['data'][i]['data'][0]['isp']
                data['data'][i]['min'] = float('{:.2f}'.format(data['data'][i]['data'][-1]['total_time']))
                data['data'][i]['min_isp'] = data['data'][i]['data'][-1]['isp']
            except:
                continue
        return data

    # 获取告警列表
    def get_alam_list(self, args):
        return self.alarm_dict

    # 编辑拔测任务
    def modify(self, args):
        try:
            if 'id' not in args: return public.returnMsg(False, '错误的参数!')
            id = args.id
            pdata = {}
            if hasattr(args, 'name'): pdata['name'] = args.name
            if hasattr(args, 'url'):
                pdata['url'] = args.url.strip()
                if pdata['url'].find('http://') == -1 and pdata['url'].find('https://') == -1:
                    return public.returnMsg(False, 'URL地址必需包含http://或https://')
            if hasattr(args, 'cycle'):
                pdata['cycle'] = int(args.cycle)
                if pdata['cycle'] < 10: return public.returnMsg(False, '拔测周期最短不能少于10分钟')
                if pdata['cycle'] > 60: return public.returnMsg(False, '拔测周期最长不能超过60分钟')
            if hasattr(args, 'status'): pdata['status'] = args.status
            if hasattr(args, 'channel'): pdata['channel'] = args.channel
            if hasattr(args, 'alarm_count'): pdata['alarm_count'] = args.alarm_count
            public.M('boce_task').where('id=?', id).update(pdata)
            pdata = public.M('boce_task').where('id=?', id).find()
            resp=self.modify_task(pdata)
            if resp.get("status"):
                public.WriteLog('拔测监控', "修改拔测任务[{}]".format(pdata['name']))
                return public.returnMsg(True, '修改成功!')
            else:
                return public.returnMsg(False, "修改失败，请移步到计划任务页面查看该计划任务是否存在！")

        except:
            return traceback.format_exc()

    # 修改计划任务
    def modify_task(self, pdata):
        p = crontab.crontab()
        pypath = '/www/server/panel/class/monitorModel/boceModel.py'
        args = {
            "id": public.M('crontab').where("save=?", "boce_id_{}".format(pdata['id'])).getField('id'),
            "name": "拔测任务[" + str(pdata['name']) + "]",
            "type": "minute-n",
            "where1": pdata['cycle'],
            "hour": "",
            "minute": "",
            "week": "",
            "sType": "toShell",
            "sName": "",
            "backupTo": "localhost",
            "save": "boce_id_{}".format(pdata['id']),
            "sBody": "btpython {} {}".format(pypath,
                                                         pdata['id']),
            "urladdress": "undefined",
            "status": pdata['status']
        }
        id = public.M('crontab').where("save=?", "boce_id_{}".format(pdata['id'])).getField('id')
        status = public.M('crontab').where("save=?", "boce_id_{}".format(pdata['id'])).getField('status')
        if pdata['status'] == status:
            return  p.modify_crond(public.to_dict_obj(args))
       
        else:
            return p.set_cron_status(public.to_dict_obj({'id': id}))
     
    def batch_operation(self, args):
        if not hasattr(args, 'ids'): return public.returnMsg(False, '错误的参数!')
        if not hasattr(args, 'type'): return public.returnMsg(False, '错误的参数!')
        if not args.ids: return public.returnMsg(False, 'ids参不能为空!')
        if not args.type: return public.returnMsg(False, 'type参数不能为空!')
        data = []
        ids = json.loads(args.ids)
        try:
            if args.type == 'delete':
                for id in ids:
                    try:
                        data.append({public.M('boce_task').where('id=?', id).find()['name']: '删除成功!'})
                        self.remove(public.to_dict_obj({'id': id}))
                    except:
                        data.append({public.M('boce_task').where('id=?', id).find()['name']: '删除失败!'})
            elif args.type == 'exec':
                for id in ids:
                    try:
                        self.start(public.to_dict_obj({'id': id}))
                        data.append({public.M('boce_task').where('id=?', id).find()['name']: '执行成功!'})
                    except:
                        data.append({public.M('boce_task').where('id=?', id).find()['name']: '执行失败!'})
            elif args.type == 'stop':
                for id in ids:
                    try:
                        self.modify(public.to_dict_obj({'id': id, 'status': 0}))
                        data.append({public.M('boce_task').where('id=?', id).find()['name']: '停止成功!'})
                    except:
                        data.append({public.M('boce_task').where('id=?', id).find()['name']: '停止失败!'})
            elif args.type == 'start':
                for id in ids:
                    try:
                        self.modify(public.to_dict_obj({'id': id, 'status': 1}))
                        data.append({public.M('boce_task').where('id=?', id).find()['name']: '启动成功!'})
                    except:
                        data.append({public.M('boce_task').where('id=?', id).find()['name']: '启动失败!'})
            return public.returnMsg(True, data)
        except:
            return traceback.format_exc()

    def sql_name(self, get):
        # 获取boce_task表的所有字段名
        return public.M('boce_list').execute('''CREATE TABLE IF NOT EXISTS boce_list (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            pid     INTEGER,
            data    TEXT,
            status  INTEGER,
            addtime INTEGER
            )''', ())

    def send_notification(self, title, msg):
        if self.sql_data['alarm_count'] > 0:
            if os.path.exists("/www/server/panel/data/boce_alam.json"):
                boce_alam = json.loads(public.readFile("/www/server/panel/data/boce_alam.json"))
            else:
                boce_alam = {}
            import datetime
            now = datetime.datetime.now()
            zero_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            timestamp = int(zero_time.timestamp())

            data = boce_alam.get(str(self.sql_data['id']), {'time': timestamp, 'count': 0})

            if data['time'] != timestamp:
                data['time'] = timestamp
                data['count'] = 0

            if data['count'] >= self.sql_data['alarm_count'] and data['time'] == timestamp:
                return False
            data['count'] += 1
            boce_alam[str(self.sql_data['id'])] = data
            public.writeFile("/www/server/panel/data/boce_alam.json", json.dumps(boce_alam))
        data = public.get_push_info(title, msg)
        for channel in self.sql_data['channel'].split(','):
            obj = public.init_msg(channel)
            obj.send_msg(data['msg'])


if __name__ == "__main__":
    id = sys.argv[1]
    sql_data = public.M('boce_task').where('id=?', id).select()
    if not sql_data:
        print('|-指定任务不存在!')
        exit()
    sql_data = sql_data[0]
    print('|-开始执行拨测任务{}'.format(sql_data['name']))
    if sql_data['address'] == 'localhost':
        m = main()
        m.start(public.to_dict_obj({'id': id}))
    elif sql_data['address'] == 'node':
        a = PluginLoader.plugin_run("bt_boce", "start", public.to_dict_obj({'id': id}))

    print('|-执行完成拨测任务{}'.format(sql_data['name']))
