# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: cjxin <bt_ahong@qq.com>
# -------------------------------------------------------------------

# ------------------------------
# 面板日志类
# ------------------------------

import os, re, json, time
import shutil
import traceback
from datetime import datetime, timedelta
from logsModel.base import logsBase
import public, db
from html import unescape, escape


class main(logsBase):
    
    def __init__(self):
        self.serverType = public.get_webserver()
    
    def get_site_list(self, get):
        result = []
        site_list = public.M('sites').select()
        for i in site_list:
            i['project_type'] = i['project_type'].lower()
            if i['project_type'] == 'php' or i['project_type'] == 'html' or i['project_type'] == 'proxy':
                result.append(i["name"])
            else:
                data = json.loads(i['project_config']).get('bind_extranet', 0)
                if data:
                    result.append(i["name"])

        return public.returnMsg(True, result)
    
    def __get_iis_log_files(self, path):
        """
        @name 获取IIS日志文件列表
        @param path 日志文件路径
        @return list
        """
        file_list = []
        if os.path.exists(path):
            for filename in os.listdir(path):
                if filename.find('.log') == -1: continue
                file_list.append('{}/{}'.format(path, filename))
        
        file_list = sorted(file_list, reverse=False)
        return file_list
    
    def get_iis_logs(self, get):
        """
        @name 获取IIS网站日志
        """
        
        p, limit, search = 1, 2000, ''
        if 'p' in get: limit = int(get.p)
        if 'limit' in get: limit = int(get.limit)
        if 'search' in get: search = get.search
        
        import panelSite
        site_obj = panelSite.panelSite()
        data = site_obj.get_site_info(get.siteName)
        if not data:
            return public.returnMsg(False, '【{}】网站路径获取失败，请检查IIS是否存在此站点，如IIS不存在请通过面板删除此网站后重新创建.'.format(get.siteName))
        
        log_path = '{}/wwwlogs/W3SVC{}'.format(public.get_soft_path(), data['id'])
        file_list = self.__get_iis_log_files(log_path)
        
        find_idx = 0
        log_list = []
        for log_path in file_list:
            if not os.path.exists(log_path):  continue
            if len(log_list) >= limit: break
            
            p_num = 0  # 分页计数器
            next_file = False
            while not next_file:
                if len(log_list) >= limit:
                    break
                p_num += 1
                result = self.GetNumLines(log_path, 10001, p_num).split('\r\n')
                if len(result) < 10000:
                    next_file = True
                
                for _line in result:
                    if not _line: continue
                    if len(log_list) >= limit:
                        break
                    
                    try:
                        if self.find_line_str(_line, search):
                            find_idx += 1
                            if find_idx > (p - 1) * limit:
                                info = escape(_line)
                                log_list.append(info)
                    except:
                        pass
        return log_list
    
    # 取网站日志
    def get_site_logs(self, get):
        logPath = ''
        if self.serverType == 'iis':
            return self.get_iis_logs(get)
        
        elif self.serverType == 'apache':
            logPath = self.setupPath + '/wwwlogs/' + get.siteName + '-access.log'
        else:
            logPath = self.setupPath + '/wwwlogs/' + get.siteName + '.log'
        
        data = {}
        data['path'] = ''
        data['path'] = os.path.dirname(logPath)
        if os.path.exists(logPath):
            data['status'] = True
            data['msg'] = public.GetNumLines(logPath, 1000)
            return data
        data['status'] = False
        data['msg'] = '日志为空'
        return data
    
    # 取网站日志
    def get_site_access_logs(self, get):
        try:
            logsPath = '/www/wwwlogs/'
            res = public.M('sites').where('name=?', (get.siteName,)).select()
            if res:
                res = res[0]['project_type'].lower()
            else:
                return public.returnMsg(False, "网站不存在")
            if res == 'php' or res == 'proxy' or res == 'phpmod':
                res = ''
            else:
                res = res + '_'
            
            serverType = public.get_webserver()
            if serverType == "nginx":
                config_path = '/www/server/panel/vhost/nginx/{}.conf'.format(res + get.siteName)
                config = public.readFile(config_path)
                if not config:
                    print('|-正在处理网站:未检测到{}站点的日志'.format(get.siteName))
                    return public.returnMsg(False, "未检测到{}站点的日志".format(get.siteName))
                log_file = self.nginx_get_log_file_path(config, get.siteName, is_error_log=False)
            elif serverType == 'apache':
                config_path = '/www/server/panel/vhost/apache/{}.conf'.format(res + get.siteName)
                config = public.readFile(config_path)
                if not config:
                    print('|-正在处理网站:未检测到{}站点的日志'.format(get.siteName))
                    return public.returnMsg(False, "未检测到{}站点的日志".format(get.siteName))
                log_file = self.apache_get_log_file_path(config, get.siteName, is_error_log=False)
            else:
                log_file = self.open_ols_log_file_path(get.siteName, is_error_log=False)
            
            if log_file is None:
                return public.returnMsg(False, '日志为空')
            logs = public.GetNumLines(log_file, 1000)
            # 时间查找和关键字查找
            if not hasattr(get, 'time_search') or get.time_search == '[]':
                time_search = []
                start_time = 0
                import time
                end_time = int(time.time())
            else:
                time_search = json.loads(get.time_search)
                start_time = int(time_search[0])
                end_time = int(time_search[1])
            print(end_time, start_time)
            search = get.get('search', '')
            if serverType == "nginx" or serverType == 'apache':
                if time_search or search:
                    s_logs = []
                    logs = logs.strip().split('\n')
                    for log in logs:
                        is_time_search = True
                        is_search = True
                        if time_search:
                            try:
                                time = int(datetime.strptime(re.findall('\[(.*?)\]', log)[0].split(' ')[0], '%d/%b/%Y:%H:%M:%S').timestamp())
                            except:
                                time = 0
                            if time != 0 and not (start_time < time < end_time):
                                is_time_search = False
                        if search:
                            if search not in log:
                                is_search = False
                        if is_time_search and is_search:
                            s_logs.append(log)
                    logs = '\n'.join(s_logs)
            if hasattr(get, 'ip_area') and int(get.ip_area):
                logs = self.add_iparea(logs)
            return public.returnMsg(True, public.xsssec(logs))
        except:
            return traceback.format_exc()
    
    # 取网站错误日志
    def get_site_error_logs(self, get):
        try:
            logsPath = '/www/wwwlogs/'
            res = public.M('sites').where('name=?', (get.siteName,)).select()
            if res:
                res = res[0]['project_type'].lower()
            else:
                return public.returnMsg(False, "网站不存在")
            if res == 'php' or res == 'proxy' or res == 'phpmod' or res == 'wp2':
                res = ''
            else:
                res = res + '_'
            serverType = public.get_webserver()
            if serverType == "nginx":
                config_path = '/www/server/panel/vhost/nginx/{}.conf'.format(res + get.siteName)
                config = public.readFile(config_path)
                if not config:
                    print('|-正在处理网站:未检测到{}站点的日志'.format(get.siteName))
                    return public.returnMsg(False, "未检测到{}站点的日志".format(get.siteName))
                log_file = self.nginx_get_log_file_path(config, get.siteName, is_error_log=True)
            elif serverType == 'apache':
                config_path = '/www/server/panel/vhost/apache/{}.conf'.format(res + get.siteName)
                config = public.readFile(config_path)
                if not config:
                    print('|-正在处理网站:未检测到{}站点的日志'.format(get.siteName))
                    return public.returnMsg(False, "未检测到{}站点的日志".format(get.siteName))
                log_file = self.apache_get_log_file_path(config, get.siteName, is_error_log=True)
            else:
                log_file = self.open_ols_log_file_path(get.siteName, is_error_log=True)
            
            if log_file is None:
                return public.returnMsg(False, '日志为空')
            logs = public.GetNumLines(log_file, 1000)
            # 时间查找和关键字查找
            if not hasattr(get, 'time_search') or get.time_search == '[]':
                time_search = []
                start_time = 0
                import time
                end_time = time.time()
            else:
                time_search = json.loads(get.time_search)
                start_time = int(time_search[0])
                end_time = int(time_search[1])
            search = get.get('search', '')
            if serverType == "nginx":
                if time_search or search:
                    s_logs = []
                    logs = logs.strip().split('\n')
                    for log in logs:
                        is_time_search = True
                        is_search = True
                        if time_search:
                            try:
                                time = datetime.strptime(' '.join(log.split(' ')[0:2]), '%Y/%m/%d %H:%M:%S').timestamp()
                            except:
                                print(traceback.format_exc())
                                time = 0
                            if time != 0 and not (start_time < time < end_time):
                                is_time_search = False
                        if search:
                            if search not in log:
                                is_search = False
                        if is_time_search and is_search:
                            s_logs.append(log)
                    logs = '\n'.join(s_logs)
            elif serverType == 'apache':
                if time_search or search:
                    s_logs = []
                    logs = logs.strip().split('\n')
                    for log in logs:
                        is_time_search = True
                        is_search = True
                        if time_search:
                            try:
                                time = datetime.strptime(re.findall('\[(.*?)\]', log)[0], '%a %b %d %H:%M:%S.%f %Y').timestamp()
                            except:
                                time = 0
                            if time != 0 and start_time < time < end_time:
                                is_time_search = False
                        if search:
                            if search not in log:
                                is_search = False
                        if is_time_search and is_search:
                            s_logs.append(log)
                    logs = '\n'.join(s_logs)
            return public.returnMsg(True, public.xsssec(logs))
        except:
            return traceback.format_exc()
    
    def download_logs(self, get):
        try:
            if not (hasattr(get, 'siteName') and hasattr(get, 'logType') and hasattr(get, 'time_search')):
                return public.returnMsg(False, '参数错误！')
            siteName = get.siteName
            logType = get.logType
            if logType == 'access':
                data = self.get_site_access_logs(get)
                if data['status']:
                    path = '/tmp/{}-access.log'.format(siteName)
                    public.writeFile(path, data['msg'])
                    return public.returnMsg(True, path)
                else:
                    return public.returnMsg(False, '导出日志失败！')
            elif logType == 'error':
                data = self.get_site_error_logs(get)
                if data['status']:
                    path = '/tmp/{}-error.log'.format(siteName)
                    public.writeFile(path, data['msg'])
                    return public.returnMsg(True, path)
                else:
                    return public.returnMsg(False, '导出日志失败！')
            return public.returnMsg(False, '类型参数错误！')
        except:
            return public.returnMsg(False, traceback.format_exc())
    
    def clear_logs(self, get):
        try:
            logsPath = '/www/wwwlogs/'
            res = public.M('sites').where('name=?', (get.siteName,)).select()
            if res:
                res = res[0]['project_type'].lower()
            else:
                return public.returnMsg(False, "网站不存在")
            
            if res == 'php' or res == 'proxy' or res == 'phpmod':
                res = ''
            else:
                res = res + '_'
            serverType = public.get_webserver()
            if serverType == "nginx":
                config_path = '/www/server/panel/vhost/nginx/{}.conf'.format(res + get.siteName)
                config = public.readFile(config_path)
                if not config:
                    print('|-正在处理网站:未检测到{}站点的日志'.format(get.siteName))
                    return public.returnMsg(False, "未检测到{}站点的日志".format(get.siteName))
                error_log_file = self.nginx_get_log_file_path(config, get.siteName, is_error_log=True)
                access_log_file = self.nginx_get_log_file_path(config, get.siteName, is_error_log=False)
            elif serverType == 'apache':
                config_path = '/www/server/panel/vhost/apache/{}.conf'.format(res + get.siteName)
                config = public.readFile(config_path)
                if not config:
                    print('|-正在处理网站:未检测到{}站点的日志'.format(get.siteName))
                    return public.returnMsg(False, "未检测到{}站点的日志".format(get.siteName))
                error_log_file = self.apache_get_log_file_path(config, get.siteName, is_error_log=True)
                access_log_file = self.apache_get_log_file_path(config, get.siteName, is_error_log=False)
            else:
                error_log_file = self.open_ols_log_file_path(get.siteName, is_error_log=True)
                access_log_file = self.open_ols_log_file_path(get.siteName, is_error_log=False)
            if not (hasattr(get, 'siteName') and hasattr(get, 'logType') and hasattr(get, 'time_search')):
                return public.returnMsg(False, '参数错误！')
            
            logType = get.logType
            if logType == 'access':
                data = self.get_site_access_logs(get)
                if data['status']:
                    if hasattr(get, 'time_search') and get.time_search != '[]':
                        public.writeFile(access_log_file, data['msg'])
                        return public.returnMsg(True, '清理成功！')
                    else:
                        public.writeFile(access_log_file, '')
                        return public.returnMsg(True, '清理成功！')
            elif logType == 'error':
                data = self.get_site_error_logs(get)
                if data['status']:
                    if hasattr(get, 'time_search') and get.time_search != '[]':
                        public.writeFile(error_log_file, data['msg'])
                        return public.returnMsg(True, '清理成功！')
                    else:
                        public.writeFile(error_log_file, '')
                        return public.returnMsg(True, '清理成功！')
            return public.returnMsg(False, '清理失败！')
        except:
            return public.returnMsg(False, traceback.format_exc())
    
    # def get_site_list(self, get):
    #     data = public.M('sites').select()
    #     return data
    
    @staticmethod
    def nginx_get_log_file_path(nginx_config: str, site_name: str, is_error_log: bool = False):
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
    
    @staticmethod
    def apache_get_log_file_path(apache_config: str, site_name: str, is_error_log: bool = False):
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
    
    @staticmethod
    def open_ols_log_file_path(site_name: str, is_error_log: bool = False):
        if not is_error_log:
            return '/www/wwwlogs/' + site_name + '_ols.access_log'
        else:
            return '/www/wwwlogs/' + site_name + '_ols.error_log'
    
    # 获取网站日志
    def GetSiteLogs(self, get):
        ip_area = 0
        if hasattr(get, 'ip_area'):
            ip_area = int(get.ip_area)
            public.writeFile('data/ip_area.txt', str(ip_area))
        logsPath = '/www/wwwlogs/'
        res = public.M('sites').where('name=?', (get.siteName,)).select()
        if res:
            res = res[0]['project_type'].lower()
        else:
            return public.returnMsg(False, "网站不存在")
        
        if res == 'php' or res == 'proxy' or res == 'phpmod' or res == 'wp2':
            res = ''
        else:
            res = res + '_'
        serverType = public.get_webserver()
        re_log_file = None
        if serverType == "nginx":
            config_path = '/www/server/panel/vhost/nginx/{}.conf'.format(res + get.siteName)
            if not os.path.exists(config_path):
                return public.returnMsg(False, "网站配置文件丢失！")
            config = public.readFile(config_path)
            re_log_file = self.nginx_get_log_file(config, is_error_log=False)
        elif serverType == 'apache':
            config_path = '/www/server/panel/vhost/apache/{}.conf'.format(res + get.siteName)
            if not os.path.exists(config_path):
                return public.returnMsg(False, "网站配置文件丢失！")
            config = public.readFile(config_path)
            if not config:
                print('|-正在处理网站:未检测到{}站点的日志'.format(get.siteName))
                return public.returnMsg(False, "未检测到{}站点的日志".format(get.siteName))
            re_log_file = self.apache_get_log_file(config, is_error_log=False)
        
        if re_log_file is not None and os.path.exists(re_log_file):
            data = self.xsssec(public.GetNumLines(re_log_file, 1000))
            if ip_area:
                data = self.add_iparea(data)
            return public.returnMsg(True, data)
        
        if serverType == "nginx":
            logPath = logsPath + get.siteName + '.log'
        elif serverType == 'apache':
            logPath = logsPath + get.siteName + '-access_log'
        else:
            logPath = logsPath + get.siteName + '_ols.access_log'
        if not os.path.exists(logPath):
            return public.returnMsg(False, '日志为空')
        data = self.xsssec(public.GetNumLines(logPath, 1000))
        if ip_area:
            data = self.add_iparea(data)
        return public.returnMsg(True, data)
    
    def add_iparea(self, data):
        try:
            ip_pattern = r'\n\b(?:\d{1,3}\.){3}\d{1,3}\b'
            ip_addresses = re.findall(ip_pattern, data)
            ip_addresses = list(set(ip_addresses))
            ip_addresses = [ip.strip() for ip in ip_addresses]
            infos = public.get_ips_area(ip_addresses)
            for key, value in infos.items():
                if value.get('info') == '内网地址':
                    data = data.replace(key, '【{}】 {}'.format(value['info'], key))
                    continue
                if value.get('info') == '未知归属地':
                    data = data.replace(key, '【{}】 {}'.format(value['info'], key))
                    continue
                try:
                    data = data.replace(key, '【{} {} {}】 {}'.format(value['continent'], value['country'], value['province'], key))
                except:
                    pass
            return data
        except:
            return data
    
    def get_ip_area(self, get):
        try:
            ip_area_path = 'data/ip_area.txt'
            if os.path.exists(ip_area_path):
                ip_area = int(public.readFile(ip_area_path))
            else:
                ip_area = 0  # 如果文件不存在，使用默认值
        except:
            ip_area = 0
        return public.returnMsg(True, ip_area)
    
    @staticmethod
    def nginx_get_log_file(nginx_config: str, is_error_log: bool = False):
        if is_error_log:
            re_data = re.findall(r"error_log +(/(\S+/?)+) ?(.*?);", nginx_config)
        else:
            re_data = re.findall(r"access_log +(/(\S+/?)+) ?(.*?);", nginx_config)
        if re_data is None:
            return None
        for i in re_data:
            file_path = i[0].strip(";")
            if file_path != "/dev/null":
                return file_path
        return None
    
    @staticmethod
    def apache_get_log_file(apache_config: str, is_error_log: bool = False):
        if is_error_log:
            re_data = re.findall(r'''ErrorLog +['"]?(/(\S+/?)+)['"]? ?(.*?)\n''', apache_config)
        else:
            re_data = re.findall(r'''CustomLog +['"]?(/(\S+/?)+)['"]? ?(.*?)\n''', apache_config)
        if re_data is None:
            return None
        for i in re_data:
            file_path = i[0].strip('"').strip("'")
            if file_path != "/dev/null":
                return file_path
        return None
    
    def xsssec(self, text):
        replace_list = {
            "<": "＜",
            ">": "＞",
            "'": "＇",
            '"': "＂",
        }
        for k, v in replace_list.items():
            text = text.replace(k, v)
        return public.xssencode2(text)
    
    def get_site_log_file(self, get):
        res = public.M('sites').where('name=?', (get.siteName,)).select()
        if not res:
            return {
                "status": False,
                "log_file": '',
                "msg": "网站不存在"
            }
        res = res[0]['project_type'].lower()
        if res == 'php' or res == 'proxy' or res == 'phpmod' or res == 'wp2':
            res = ''
        else:
            res = res + '_'
        
        is_error_log = False
        if "is_error_log" in get and get.is_error_log.strip() in ('1', "yes"):
            is_error_log = True
        
        serverType = public.get_webserver()
        if serverType == "nginx":
            config_path = '/www/server/panel/vhost/nginx/{}.conf'.format(res + get.siteName)
            config = public.readFile(config_path)
            if not config:
                return public.returnMsg(False, "站点配置文件丢失")
            log_file = self.nginx_get_log_file_path(config, get.siteName, is_error_log=is_error_log)
        elif serverType == 'apache':
            config_path = '/www/server/panel/vhost/apache/{}.conf'.format(res + get.siteName)
            config = public.readFile(config_path)
            if not config:
                return public.returnMsg(False, "站点配置文件丢失")
            log_file = self.apache_get_log_file_path(config, get.siteName, is_error_log=is_error_log)
        else:
            log_file = self.open_ols_log_file_path(get.siteName, is_error_log=is_error_log)
        return {
            "status": True,
            "log_file": log_file,
            "msg": "获取成功"
        }
    
    def change_site_log_path(self, get=None, is_multi=False):
        mv_log = False
        try:
            log_path: str = get.log_path.strip()
            site_name: str = get.site_name.strip()
            if "mv_log" in get:
                if get.mv_log in (True, "yes", "1", "true"):
                    mv_log = True
        except AttributeError:
            return public.returnMsg(False, "参数错误")
        
        if not os.path.isdir(log_path):
            return public.returnMsg(False, "不是一个存在的文件夹路径")
        
        if log_path[-1] == "/":
            log_path = log_path[:-1]
        
        # nginx
        nginx_config_path = '/www/server/panel/vhost/nginx/{}.conf'.format(site_name)
        nginx_config = public.readFile(nginx_config_path)
        if not nginx_config:
            return public.returnMsg(False, "网站配置文件丢失，无法配置")
        
        # apache
        apache_config_path = '/www/server/panel/vhost/apache/{}.conf'.format(site_name)
        apache_config = public.readFile(apache_config_path)
        if not apache_config:
            return public.returnMsg(False, "网站配置文件丢失，无法配置")
        
        old_log_list = []
        # nginx
        old_log_file = self.nginx_get_log_file_path(nginx_config, site_name, is_error_log=False)
        old_error_log_file = self.nginx_get_log_file_path(nginx_config, site_name, is_error_log=True)
        
        old_log_list.append(old_log_file)
        old_log_list.append(old_error_log_file)
        
        if old_log_file and old_error_log_file:
            new_nginx_conf = nginx_config
            log_file_rep = re.compile(r"access_log +" + public.prevent_re_key(old_log_file))
            error_log_file_rep = re.compile(r"error_log +" + public.prevent_re_key(old_error_log_file))
            if log_file_rep.search(nginx_config):
                new_nginx_conf = log_file_rep.sub("access_log {}/{}.log".format(log_path, site_name), new_nginx_conf, 1)
            
            if error_log_file_rep.search(nginx_config):
                new_nginx_conf = error_log_file_rep.sub("error_log {}/{}.error.log".format(log_path, site_name), new_nginx_conf, 1)
            
            public.writeFile(nginx_config_path, new_nginx_conf)
        
        else:
            return public.returnMsg(False, "未找到日志配置，无法操作")
        
        # apache
        old_log_file = self.apache_get_log_file_path(apache_config, site_name, is_error_log=False)
        old_error_log_file = self.apache_get_log_file_path(apache_config, site_name, is_error_log=True)
        
        old_log_list.append(old_log_file)
        old_log_list.append(old_error_log_file)
        
        if old_log_file and old_error_log_file:
            new_apache_conf = apache_config
            log_file_rep = re.compile(r'''CustomLog +['"]?''' + public.prevent_re_key(old_log_file) + '''['"]?''')
            error_log_file_rep = re.compile(r'''ErrorLog +['"]?''' + public.prevent_re_key(old_error_log_file) + '''['"]?''')
            if log_file_rep.search(apache_config):
                new_apache_conf = log_file_rep.sub('CustomLog "{}/{}-access_log"'.format(log_path, site_name), new_apache_conf)
            
            if error_log_file_rep.search(apache_config):
                new_apache_conf = error_log_file_rep.sub('ErrorLog "{}/{}.-error_log"'.format(log_path, site_name),
                                                         new_apache_conf)
            public.writeFile(apache_config_path, new_apache_conf)
        
        if public.checkWebConfig() is not True:
            public.writeFile(nginx_config_path, nginx_config)
            public.writeFile(apache_config_path, apache_config)
            return public.returnMsg(False, "设置失败")
        
        if mv_log:  # 迁移日志文件
            for i in old_log_list:
                if os.path.isfile(i):
                    self.move_log(i, log_path)
        
        if not is_multi:
            public.serviceReload()
        return public.returnMsg(True, "设置成功")
    
    @staticmethod
    def move_log(old_log_file: str, new_dir: str):
        new_dir = new_dir.rstrip("/")  # 规范路径参数
        file_name = os.path.basename(old_log_file)
        d_file = os.path.join(new_dir, file_name)
        try:
            if os.path.isfile(d_file) and os.path.getsize(d_file) == 0:
                os.remove(d_file)
            shutil.move(old_log_file, new_dir)
        except:
            pass
        if os.path.exists(d_file):
            return True
        return False
    
    def get_backup_logs(self, get):
        try:
            id = get.id
            sql = public.M('backup')
            backup_conf = sql.where('id=?', (id,)).field('pid,addtime,fileName').find()
            if sql.ERR_INFO:
                return public.returnMsg(False, '获取备份信息失败！')
            if not backup_conf:
                return public.returnMsg(False, '获取备份信息失败！')

            pid = backup_conf['pid']
            filename = backup_conf['fileName']
            addtime = backup_conf['addtime']
            tmps = '/www/backup/site_backup_log/site_backup_{}.log'.format(pid)
            title = '备份已完成！'
            site_name = public.M('sites').where('id=?', (pid,)).getField('name')
            stop = True
            speed = '0'
            total = os.path.getsize(filename)
            if os.path.exists(filename + '.pl'):
                print(filename + '.pl')
                try:
                    import psutil
                    process_id = public.readFile(filename + '.pl')
                    process_id = int(process_id)
                    print(process_id)
                    pro = psutil.Process(process_id)
                    if pro.status() == psutil.STATUS_ZOMBIE:
                        raise
                    datetime_obj = datetime.strptime(addtime, "%Y-%m-%d %H:%M:%S")
                    start_time = datetime_obj.timestamp()
                    now_time = time.time()
                    speed = round(total / int(now_time - start_time), 2)
                    stop = False
                    title = '正在备份中，请稍后....'
                except:
                    pass
            # 单位转换
            total = public.to_size(total)
            speed = public.to_size(speed) + '/s'
            msg = public.GetNumLines(tmps, 200)
            data = {
                "title": title,
                "site_name": site_name,
                "stop": stop,
                "speed": speed,
                "total": total,
                "msg": msg,
                "status": True
            }
            return data
        except Exception as e:
            return public.returnMsg(False, str(e))
    
    def stop_backup(self, get):
        id = get.id
        backup_conf = public.M('backup').where('id=?', (id,)).field('fileName').find()
        filename = backup_conf['fileName']
        process_id = filename + '.pl'
        if os.path.exists(process_id):
            pid = public.readFile(process_id)
            if pid:
                public.ExecShell('kill -9 {}'.format(pid))
            public.ExecShell('rm -rf {}'.format(process_id))
        if os.path.exists(filename):
            public.ExecShell('rm -rf {}'.format(filename))
        public.M('backup').where('id=?', (id,)).delete()
        return public.returnMsg(True, '停止成功！')
