#!/usr/bin/python
#coding: utf-8

import sys
import os
import json
import time
import datetime
import re

import public


class Monitor:
    def __init__(self):
        pass

    def _get_file_json(self, filename):
        if not os.path.exists(filename):
            return []
        data = []
        with open(filename) as f:
            for line in f:
                try:
                    data.append(json.loads(line))
                except: pass
        return data

    def _get_site_list(self):
        sites = public.M('sites').where('status=?', (1,)).field('name').get()
        return sites

    def _ip_query(self, ip):
        import ipdb

        db = ipdb.City("/www/server/panel/data/data.ipdb")
        if sys.version_info[0] == 2:
            ip_info = db.find_info(unicode(ip), "CN")
        else:
            ip_info = db.find_info(ip, "CN")
        if ip_info.country_name == '中国':
            return ip_info.region_name
        return None

    def get_access_ip(self, args):
        if hasattr(args, 'date_str'):
            date_str = args['date_str']
        else:
            date_str = time.strftime('%Y-%m-%d', time.localtime())

        sites = self._get_site_list()

        t_access_ip = {}
        for site in sites:
            site_name = site['name']
            log_path = '/www/server/total/logs/{0}/{1}.log'.format(site_name, date_str)
            log_body = self._get_file_json(log_path)
            for item in log_body:
                ua = item[-2]
                client_ip = item[1]
                ip_region = self._ip_query(client_ip)
                if not ip_region or not ua or 'bot' in ua or 'spider' in ua:
                    continue
                t_access_ip[client_ip] = ip_region

        return t_access_ip

    def _statuscode_distribute(self, args):
        sites = self._get_site_list()

        count_401, count_500, count_502, count_503 = 0, 0, 0, 0

        for site in sites:
            site_name = site['name']
            path = '/www/server/total/logs/' + site_name + '/error'
            if not os.path.isdir(path): continue

            for fname in os.listdir(path):
                status_code = fname.split('.')[0]
                log_path = os.path.join(path, fname)
                log_body = self._get_file_json(log_path)
                for item in log_body:
                    if self._is_today(item[0]):
                        if status_code == '401':
                            count_401 += 1
                        elif status_code == '500':
                            count_500 += 1
                        elif status_code == '502':
                            count_502 += 1
                        elif status_code == '503':
                            count_503 += 1
        return {'401': count_401, '500': count_500, '502': count_502, '503': count_503}

    def _get_slow_log_nums(self, args):
        import database

        my_obj = database.database()
        filename = my_obj.GetMySQLInfo(args)['datadir'] + '/mysql-slow.log'

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

    def _utc_to_stamp(self, utc_time_str, utc_format='%Y-%m-%dT%H:%M:%SZ'):
        import pytz

        local_tz = pytz.timezone('Asia/Shanghai')
        local_format = "%Y-%m-%d %H:%M:%S"
        utc_dt = datetime.datetime.strptime(utc_time_str, utc_format)
        local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
        time_str = local_dt.strftime(local_format)
        return int(time.mktime(time.strptime(time_str, local_format)))

    def _str_to_stamp(self, time_str):
        try:
            return int(time.mktime(time.strptime(time_str, '%Y-%m-%d %H:%M:%S')))
        except:
            return int(time.mktime(time.strptime(time_str, "%y%m%d %H:%M:%S")))

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

    # 取php版本
    def return_php(self, get):
        ret = []
        if not os.path.exists('/www/server/php'):
            return ret
        for i in os.listdir('/www/server/php'):
            if os.path.isdir('/www/server/php/' + i):
                ret.append(i)
        return ret

    # mysql是否到最大连接数测试
    def mysql_client_count(self, get):
        ret = public.M('config').field('mysql_root').select()
        password = ret[0]['mysql_root']
        sql = ''' mysql -uroot -p''' + password + ''' -e "select User,Host from mysql.user where host='%'" '''
        result = public.ExecShell(sql)
        if re.search('Too many connections', result[1]):
            return True
        else:
            return False

    def _get_error_log_nums(self, args):
        import database

        my_obj = database.database()
        path = my_obj.GetMySQLInfo(args)['datadir']
        filename = ''
        for n in os.listdir(path):
            if len(n) < 5: continue
            if n[-3:] == 'err':
                filename = path + '/' + n
                break

        if not os.path.exists(filename):
            return 0

        count = 0
        zero_point = int(time.time()) - int(time.time() - time.timezone) % 86400
        with open(filename) as f:
            for line in f:
                line = line.strip()
                if '[ERROR]' in line or '[Note]' in line:
                    line_arr = line.split()
                    if len(line_arr[0]) > 11:
                        timestamp = self._utc_to_stamp(line_arr[0].split('.')[0] + 'Z')
                    else:
                        timestamp = self._str_to_stamp(line_arr[0] + ' ' + line_arr[1])
                    if timestamp > zero_point:
                        count += 1
        return count

    def get_exception(self, args):
        data = {'mysql_slow': self._get_slow_log_nums(args), 'php_slow': self._php_count(args), 'attack_num': self.get_attack_nums(args)}
        statuscode_distribute = self._statuscode_distribute(args)
        data.update(statuscode_distribute)
        return data

    # 获取异常日志
    def get_exception_logs(self, get):
        import page

        page = page.Page()
        count = public.M('logs').where("type=? and strftime('%m-%d','now','localtime') = strftime('%m-%d',addtime)", (u'消息推送',)).count()
        limit = 12
        info = {}
        info['count'] = count
        info['row'] = limit
        info['p'] = 1
        if hasattr(get, 'p'):
            info['p'] = int(get['p'])
        info['uri'] = get
        info['return_js'] = ''
        if hasattr(get, 'tojs'):
            info['return_js'] = get.tojs
        data = {}

        # 获取分页数据
        data['page'] = page.GetPage(info, '1,2,3,4,5,8')
        data['data'] = public.M('logs').where("type=? and strftime('%m-%d','now','localtime') = strftime('%m-%d',addtime)", (u'消息推送',))\
            .order('id desc').limit(str(page.SHIFT) + ',' + str(page.ROW)).field('log,addtime').select()
        return data

    # 获取攻击数
    def get_attack_nums(self, args):
        file_name = '/www/server/btwaf/total.json'
        if not os.path.exists(file_name): return 0

        try:
            file_body = json.loads(public.readFile(file_name))
            return int(file_body['total'])
        except:
            return 0
