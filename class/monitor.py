#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 王张杰 <750755014@qq.com>
# | Maintainer: linxiao
# +-------------------------------------------------------------------

import os
import json
import time
import datetime
import re
import sqlite3

import public


class Monitor:
    def __init__(self):
        pass

    def __get_file_json(self, filename):
        try:
            if not os.path.exists(filename): return {}
            return json.loads(public.readFile(filename))
        except:
            return {}

    def __get_file_nums(self, filepath):
        if not os.path.exists(filepath): return 0

        count = 0
        for index, line in enumerate(open(filepath, 'r')):
            count += 1
        return count

    def _get_site_list(self):
        sites = public.M('sites').where('status=?', (1,)).field('name').get()
        return sites

    def _statuscode_distribute_site(self, site_name):

        try:
            day_401 = 0
            day_500 = 0
            day_502 = 0
            day_503 = 0
            conn = None
            ts = None
            start_date, end_date = self.get_time_interval(time.localtime())
            select_sql = "select time/100 as time1, sum(status_401), sum(status_500), sum(status_502), sum(status_503) from request_stat where time between {} and {}"\
            .format(start_date, end_date)

            db_path = os.path.join("/www/server/total/", "logs/{}/logs.db".format(site_name))
            if os.path.isfile(db_path):
                conn = sqlite3.connect(db_path)
                ts = conn.cursor()
                ts.execute(select_sql)
                results = ts.fetchall()

                if type(results) == list:
                    for result in results:
                        time_key = str(result[0])
                        day_401 = result[1]
                        day_500 = result[2]
                        day_502 = result[3]
                        day_503 = result[4]
        except:
            pass
        finally:
            if ts:
                ts.close()
            if conn:
                conn.close()

        return day_401, day_500, day_502, day_503

    def _statuscode_distribute_site_old(self, site_name):
        today = time.strftime('%Y-%m-%d', time.localtime())
        path = '/www/server/total/total/' + site_name + '/request/' + today + '.json'

        day_401 = 0
        day_500 = 0
        day_502 = 0
        day_503 = 0
        if os.path.exists(path):
            spdata = self.__get_file_json(path)

            for c in spdata.values():
                for d in c:
                    if '401' == d: day_401 += c['401'] or 0
                    if '500' == d: day_500 += c['500'] or 0
                    if '502' == d: day_502 += c['502'] or 0
                    if '503' == d: day_503 += c['503'] or 0

        return day_401, day_500, day_502, day_503

    def _statuscode_distribute(self, args):
        sites = self._get_site_list()

        count_401, count_500, count_502, count_503 = 0, 0, 0, 0
        for site in sites:
            site_name = site['name']
            day_401, day_500, day_502, day_503 = self._statuscode_distribute_site(site_name)
            day_401 = day_401 or 0
            day_500 = day_500 or 0
            day_502 = day_502 or 0
            day_503 = day_503 or 0
            count_401 += day_401
            count_500 += day_500
            count_502 += day_502
            count_503 += day_503
        return {'401': count_401, '500': count_500, '502': count_502, '503': count_503}

    # 获取mysql当天的慢查询数量
    def _get_slow_log_nums(self, args):
        if not os.path.exists('/etc/my.cnf'):
            return 0

        ret = re.findall(r'datadir\s*=\s*(.+)', public.ReadFile('/etc/my.cnf'))
        if not ret:
            return 0
        filename = ret[0] + '/mysql-slow.log'

        if not os.path.exists(filename):
            return 0

        count = 0
        zero_point = int(time.time()) - int(time.time() - time.timezone) % 86400
        with open(filename) as f:
            for line in f:
                line = line.strip().lower()
                if line.startswith('set timestamp='):
                    timestamp = int(line.split('=')[-1].strip(';'))
                    if timestamp >= zero_point:
                        count += 1
        return count

    # 判断字符串格式的时间是不是今天
    def _is_today(self, time_str):
        try:
            time_date = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S").date()
        except:
            try:
                time_date = datetime.datetime.strptime(time_str, "%y%m%d %H:%M:%S").date()
            except:
                time_date = datetime.datetime.strptime(time_str, "%d-%b-%Y %H:%M:%S").date()
        today = datetime.date.today()
        if time_date == today:
            return True
        return False

    # PHP慢日志
    def _php_count(self, args):
        result = 0
        if not os.path.exists('/www/server/php'):
            return result

        for i in os.listdir('/www/server/php'):
            if os.path.isdir('/www/server/php/' + i):
                php_slow = '/www/server/php/' + i + '/var/log/slow.log'
                if os.path.exists(php_slow):
                    php_info = open(php_slow, 'r')
                    for j in php_info.readlines():
                        if re.search(r'\[\d+-\w+-\d+.+', j):
                            time_str = re.findall(r'\[\d+-\w+-\d+\s+\d+:\d+:\d+\]', j)
                            time_str = time_str[0].replace('[', '').replace(']', '')
                            if self._is_today(time_str):
                                result += 1
                            else:
                                break

        return result

    # 获取当天cc攻击数
    def _get_cc_attack_num(self, args):
        zero_point = int(time.time()) - int(time.time() - time.timezone) % 86400
        log_path = '/www/server/btwaf/drop_ip.log'
        if not os.path.exists(log_path): return 0

        num = 100
        log_body = public.GetNumLines(log_path, num).split('\n')
        while True:
            if len(log_body) < num:
                break
            if json.loads(log_body[0])[0] < zero_point:
                break
            else:
                num += 100
                log_body = public.GetNumLines(log_path, num).split('\n')

        num = 0
        for line in log_body:
            try:
                item = json.loads(line)
                if item[0] > zero_point and item[-1] == 'cc':
                    num += 1
            except: continue

        return num

    # 获取当天攻击总数
    def _get_attack_num(self, args):
        today = time.strftime('%Y-%m-%d', time.localtime())
        sites = self._get_site_list()

        count = 0
        for site in sites:
            file_path = '/www/wwwlogs/btwaf/{0}_{1}.log'.format(site['name'], today)
            count += self.__get_file_nums(file_path)
        return count

    def get_exception(self, args):
        data = {'mysql_slow': self._get_slow_log_nums(args), 'php_slow': self._php_count(args),
                'attack_num': self._get_attack_num(args), 'cc_attack_num': self._get_cc_attack_num(args)}
        statuscode_distribute = self._statuscode_distribute(args)
        data.update(statuscode_distribute)
        return data

    def get_spider(self, args):
        request_data = {}
        sites = public.M('sites').field('name').order("addtime").select();
        for site_info in sites:
            ts = None
            conn = None
            try:
                site_name = site_info["name"]
                start_date, end_date = self.get_time_interval(time.localtime())
                select_sql = "select time, spider from request_stat where time between {} and {}"\
                .format(start_date, end_date)

                db_path = os.path.join("/www/server/total/", "logs/{}/logs.db".format(site_name))
                if not os.path.isfile(db_path): continue
                conn = sqlite3.connect(db_path)
                ts = conn.cursor()
                ts.execute(select_sql)
                results = ts.fetchall()

                if type(results) == list:
                    for result in results:
                        time_key = str(result[0])
                        hour = time_key[len(time_key)-2:]
                        value = result[1]
                        if hour not in request_data:
                            request_data[hour] = value
                        else:
                            request_data[hour] += value
            except:
                pass
            finally:
                if ts:
                    ts.close()
                if conn:
                    conn.close()
        return request_data

    # 获取蜘蛛数量分布
    def get_spider_old(self, args):
        today = time.strftime('%Y-%m-%d', time.localtime())
        sites = self._get_site_list()

        data = {}
        for site in sites:
            site_name = site['name']
            file_name = '/www/server/total/total/' + site_name + '/spider/' + today + '.json'
            if not os.path.exists(file_name): continue
            day_data = self.__get_file_json(file_name)
            for s_data in day_data.values():
                for s_key in s_data.keys():
                    if s_key not in data:
                        data[s_key] = s_data[s_key]
                    else:
                        data[s_key] += s_data[s_key]
        return data

    # 获取负载和上行流量
    def load_and_up_flow(self, args):
        import psutil

        load_five = float(os.getloadavg()[1])
        cpu_count = psutil.cpu_count()

        up_flow = 0
        data = public.M('network').dbfile('system').field('up').order('id desc').limit("5").get()
        if len(data) == 5:
            up_flow = round(sum([item['up'] for item in data]) / 5, 2)

        return {'load_five': load_five, 'cpu_count': cpu_count, 'up_flow': up_flow}

    def get_time_interval(self, local_time):
        start = None
        end = None
        time_key_format = "%Y%m%d00"
        start = int(time.strftime(time_key_format, local_time))
        time_key_format = "%Y%m%d23"
        end = int(time.strftime(time_key_format, local_time))
        return start, end

    def get_request_count_by_hour(self, args):
        # 获取站点每小时的请求数据
        request_data = {}
        import sqlite3
        sites = public.M('sites').field('name').order("addtime").select();
        for site_info in sites:
            ts = None
            conn = None
            try:
                site_name = site_info["name"]
                start_date, end_date = self.get_time_interval(time.localtime())
                select_sql = "select time, req from request_stat where time between {} and {}"\
                .format(start_date, end_date)
                db_path = os.path.join("/www/server/total/", "logs/{}/logs.db".format(site_name))
                if not os.path.isfile(db_path): continue
                conn = sqlite3.connect(db_path)
                ts = conn.cursor()
                ts.execute(select_sql)
                results = ts.fetchall()
                if type(results) == list:
                    for result in results:
                        time_key = str(result[0])
                        hour = time_key[len(time_key)-2:]
                        value = result[1]
                        if hour not in request_data:
                            request_data[hour] = value
                        else:
                            request_data[hour] += value
            except: pass
            finally:
                if ts:
                    ts.close()
                if conn:
                    conn.close()
        return request_data

    # 取每小时的请求数
    def get_request_count_by_hour_old(self, args):
        today = time.strftime('%Y-%m-%d', time.localtime())

        request_data = {}
        sites = self._get_site_list()
        for site in sites:
            path = '/www/server/total/total/' + site['name'] + '/request/' + today + '.json'
            if os.path.exists(path):
                spdata = self.__get_file_json(path)
                for hour, value in spdata.items():
                    count = value.get('GET', 0) + value.get('POST', 0)
                    if hour not in request_data:
                        request_data[hour] = count
                    else:
                        request_data[hour] = request_data[hour] + count

        return request_data

    # 取服务器的请求数
    def _get_request_count(self, args):
        request_data = self.get_request_count_by_hour(args)
        return sum(request_data.values())

    # 获取瞬时请求数和qps
    def get_request_count_qps(self, args):
        from BTPanel import cache

        cache_timeout = 86400

        old_total_request = cache.get('old_total_request')
        otime = cache.get("old_get_time")
        if not old_total_request or not otime:
            otime = time.time()
            old_total_request = self._get_request_count(args)
            time.sleep(2)
        ntime = time.time()
        new_total_request = self._get_request_count(args)

        qps = float(new_total_request - old_total_request) / (ntime - otime)

        cache.set('old_total_request', new_total_request, cache_timeout)
        cache.set('old_get_time', ntime, cache_timeout)
        return {'qps': qps, 'request_count': new_total_request}
