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
from logsModel.base import logsBase
import public, db
from html import unescape, escape
from flask import session
import datetime

class main(logsBase):

    def __init__(self):
        pass

    def get_logs_info(self, args):
        '''
            @name 获取分类日志信息
        '''
        data = public.M('logs').query('''
            select type,count(id) as 'count' from logs
            group by type
            order by count(id) desc
        ''')
        result = []
        for arrs in data:
            item = {}
            if not arrs: continue
            if len(arrs) < 2: continue
            item['count'] = arrs[1]
            item['type'] = arrs[0]
            result.append(item)
        public.set_module_logs('get_logs_info', 'get_logs_info')
        return result

    def get_logs_bytype(self, args):
        # 获取分页参数
        p = int(args.p) if 'p' in args else 1
        limit = int(args.limit) if 'limit' in args else 20

        # 支持查询“项目管理”和“网站管理”
        stypes = ['项目管理', '网站管理']

        # 检查是否有关键字
        if 'keywords' in args and args.keywords:
            # 处理关键字搜索
            keywords = args.keywords.lower().split(',')
            keyword_conditions = " or ".join(["log like ?"] * len(keywords))
            where_clause = "type in (?, ?) and ({})".format(keyword_conditions)
            params = stypes + ['%' + keyword + '%' for keyword in keywords]
        else:
            # 处理通配符搜索
            search = args.search if 'search' in args else ''
            search_wildcard = '%' + search + '%'

            # 尝试使用通配符
            where_clause = "type in (?, ?) and log like ?"
            params = stypes + [search_wildcard]

            count = public.M('logs').where(where_clause, params).count()

            if count == 0 and search:
                # 如果通配符没有结果，尝试使用方括号
                search_brackets = '[' + search + ']'
                where_clause = "type in (?, ?) and log like ?"
                params = stypes + [search_brackets]

        # 查询数据
        count = public.M('logs').where(where_clause, params).count()
        data = public.get_page(count, p, limit)
        data['data'] = public.M('logs').where(where_clause, params).limit('{},{}'.format(data['shift'], data['row'])).order('id desc').select()

        return data

    # 删除网站操作日志
    def del_website_log(self, args):
        if not hasattr(args, 'id'):
            return public.returnMsg(False, '缺少id参数')
        id_list = args.id.split(",")
        for ids in id_list:
            log_data = public.M('logs').where('id=?', (ids,)).count()
            if not log_data:
                continue

            public.M('logs').where('id=?', (ids,)).delete()

        return public.returnMsg(True, '删除成功')

    def __get_panel_dirs(self):
        '''
            @name 获取面板日志目录
        '''
        dirs = []
        for filename in os.listdir('{}/logs/request'.format(public.get_panel_path())):
            if filename.find('.json') != -1:
                dirs.append(filename)

        dirs = sorted(dirs, reverse=True)
        return dirs

    def get_panel_log(self, get):
        """
        @name 获取面板日志
        """
        p, limit, search = 1, 20, ''
        if 'p' in get: p = int(get.p)
        if 'limit' in get: limit = int(get.limit)
        if 'search' in get: search = get.search

        find_idx = 0
        log_list = []
        dirs = self.__get_panel_dirs()
        for filename in dirs:
            log_path = '{}/logs/request/{}'.format(public.get_panel_path(), filename)
            if not os.path.exists(log_path):  # 文件不存在
                continue

            if len(log_list) >= limit:
                break

            p_num = 0  # 分页计数器
            next_file = False
            while not next_file:
                if len(log_list) >= limit:
                    break
                p_num += 1
                result = self.GetNumLines(log_path, 10001, p_num).split('\r\n')
                if len(result) < 10000:
                    next_file = True
                result.reverse()
                for _line in result:
                    if not _line: continue
                    if len(log_list) >= limit:
                        break

                    try:
                        if self.find_line_str(_line, search):
                            find_idx += 1

                            if find_idx > (p - 1) * limit:

                                info = json.loads(unescape(_line))
                                for key in info:
                                    if isinstance(info[key], str):
                                        info[key] = escape(info[key])

                                info['address'] = info['ip'].split(':')[0]
                                log_list.append(info)
                    except:
                        pass

        return public.return_area(log_list, 'address')

    def get_panel_error_logs(self, get):
        '''
            @name 获取面板运行日志
        '''
        search = None
        if 'search' in get:
            search = get.search
        filename = '{}/logs/error.log'.format(public.get_panel_path())
        if not os.path.exists(filename):
            return public.returnMsg(False, '没有找到运行日志')

        if not hasattr(get, "limit"):
            get.limit = 500

        res = {}
        filedata = self.GetNumLines(filename, int(get.limit), 1, search)
        res['data'] = public.xssdecode(filedata)
        res['data'].split('\n').reverse()
        res["size"] = os.path.getsize(filename)
        return res

    def __get_ftp_log_files(self, path):
        """
        @name 获取FTP日志文件列表
        @param path 日志文件路径
        @return list
        """
        file_list = []
        if os.path.exists(path):
            for filename in os.listdir(path):
                if filename.find('.log') == -1: continue
                file_list.append('{}/{}'.format(path, filename))

        file_list = sorted(file_list, reverse=True)
        return file_list

    def get_ftp_logs(self, get):
        """
        @name 获取ftp日志
        """

        p, limit, search, username = 1, 500, '', ''
        if 'p' in get: p = int(get.p)
        if 'limit' in get: limit = int(get.limit)
        if 'search' in get: search = get.search
        if 'username' in get: username = get.username

        find_idx = 0
        ip_list = []
        log_list = []
        dirs = self.__get_ftp_log_files('{}/ftpServer/Logs'.format(public.get_soft_path()))
        for log_path in dirs:

            if not os.path.exists(log_path): continue
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
                result.reverse()
                for _line in result:
                    if not _line.strip(): continue
                    if len(log_list) >= limit:
                        break
                    try:
                        if self.find_line_str(_line, search):
                            # 根据用户名查找
                            if username and not re.search('-\s+({})\s+\('.format(username), _line):
                                continue

                            find_idx += 1
                            if find_idx > (p - 1) * limit:
                                # 获取ip归属地
                                for _ip in public.get_line_ips(_line):
                                    if not _ip in ip_list: ip_list.append(_ip)

                                info = escape(_line)
                                log_list.append(info)
                    except:
                        pass

        return self.return_line_area(log_list, ip_list)

    # 取慢日志
    def get_slow_logs(self, get):
        '''
            @name 获取慢日志
            @get.search 搜索关键字
        '''
        search, p, limit = '', 1, 1000
        if 'search' in get: search = get.search
        if 'limit' in get: limit = get.limit

        my_info = public.get_mysql_info()
        if not my_info['datadir']:
            return public.returnMsg(False, '未安装MySQL数据库!')

        path = my_info['datadir'] + '/mysql-slow.log'
        if not os.path.exists(path):
            return public.returnMsg(False, '日志文件不存在!')

        # mysql慢日志有顺序问题,倒序显示不利于排查问题
        # return public.returnMsg(True, public.xsssec(self.get_error_logs_by_search(public.GetNumLines(path, limit))))

        # 读取文件内容
        log_content = public.GetNumLines(path, limit)

        # 无关键字搜索
        if not search:
            return public.returnMsg(True, public.xsssec(log_content))

        # 匹配内容进行返回
        result = [public.xsssec(line) for line in log_content.split('\n') if search.lower() in line.lower()]

        return public.returnMsg(True, "\n".join(result))

        # find_idx = 0
        # p_num = 0 #分页计数器
        # next_file = False
        # log_list = []
        # while not next_file:
        #     if len(log_list) >= limit:
        #         break
        #     p_num += 1
        #     result = self.GetNumLines(path,10001,p_num).replace('\r\n','\n').split('\n')
        #     if len(result) < 10000:
        #         next_file = True
        #     result.reverse()

        #     for _line in result:
        #         if not _line: continue
        #         if len(log_list) >= limit:
        #             break

        #         try:
        #             if self.find_line_str(_line,search):
        #                 find_idx += 1
        #                 if find_idx > (p-1) * limit:
        #                     info = escape(_line)
        #                     log_list.append(info)
        #         except:pass
        # return log_list

    def get_error_logs_by_search(self, args):
        '''
            @name 根据搜索内容, 获取运行日志中的内容
            @args.search 匹配内容
            @return 匹配该内容的所有日志
        '''
        log_file_path = "{}/logs/error.log".format(public.get_panel_path())
        # return log_file_path
        data = public.readFile(log_file_path)
        if not data:
            return None
        data = data.split('\n')
        result = []
        for line in data:
            if args.search == None:
                result.append(line)
            elif args.search in line:
                result.append(line)

        return result

    def IP_geolocation(self, get):
        '''
            @name 列出所有IP及其归属地
            @return list {ip: {ip: ip_address, operation_num: 12 ,info: 归属地}, ...]
        '''

        result = dict()

        data = public.M('logs').query('''
            select * from logs
        ''')
        if type(data) == str:
            raise public.PanelError('数据库查询错误：' + data)
        for arrs in data:
            if not arrs or len(arrs) < 6: continue
            end = 0
            # 获得IP的尾后索引
            for ch in arrs[2]:
                if ch.isnumeric() or ch == '.':
                    end += 1
                else:
                    break

            ip_addr = arrs[2][0:end]

            if ip_addr:
                if result.get(ip_addr) != None:
                    result[ip_addr]["operation_num"] = result[ip_addr]["operation_num"] + 1
                else:
                    result[ip_addr] = {"ip": ip_addr, "operation_num": 1, "info": None}

        return_list = []

        for k in result:
            info = public.get_free_ip_info(k)
            result[k]["info"] = info["info"]
            return_list.append(result[k])

        return return_list

    def export_domain_log(self, get):
        '''
        @导出网站操作日志
        @param get:
        '''
        get.p = 1
        if not hasattr(get, "search"):
            return public.returnMsg(False, "缺少参数search")
        get.search.strip()
        get.stype = "网站管理"
        get.limit = 200
        result = self.get_logs_bytype(get)

        # 临时目录
        tmp_logs_path = "/tmp/export_domain_log"
        if not os.path.exists(tmp_logs_path):
            os.makedirs(tmp_logs_path, 0o600)
        tmp_logs_file = "{}/{}_{}.csv".format(tmp_logs_path, get.search.strip(), int(time.time()))

        # 写入临时文件
        with open(tmp_logs_file, mode="w+", encoding="utf-8") as fp:
            fp.write("用户,操作类型,详情,操作时间\n")
            for line in result["data"]:
                tmp = (
                    line["username"],
                    line["type"],
                    line["log"],
                    line["addtime"],
                )
                fp.write(",".join(tmp))
                fp.write("\n")

        return {
            "status": True,
            "output_file": tmp_logs_file,
        }


    def export_panel_log(self, get):
        """
        @导出面板操作日志
        @param get:
            search : 关键字
        """
        # 获取操作日志信息
        from data import data
        data_obj = data()
        args = public.dict_obj()

        # 关键字导出
        if hasattr(get, "search"):
            args.search = get.search
            args.where = "username LIKE ? OR type LIKE ? OR log LIKE ?"
            count = public.M("logs").where(args.where, ('%' + args.search + '%', '%' + args.search + '%', '%' + args.search + '%')).count()
        else:
            count = public.M("logs").count()

        args.table = "logs"
        args.limit = count
        args.tojs = "getLogs"
        args.p = 1

        result = data_obj.getData(args)

        # 临时目录
        tmp_logs_path = "/tmp/export_panel_log"
        if not os.path.exists(tmp_logs_path):
            os.makedirs(tmp_logs_path, 0o600)
        tmp_logs_file = "{}/panel_log_{}.csv".format(tmp_logs_path, int(time.time()))

        # 写入临时文件
        with open(tmp_logs_file, mode="w+", encoding="utf-8") as fp:
            fp.write("用户,操作类型,详情,操作时间\n")
            for line in result["data"]:
                line["log"] = line["log"].replace('\n', ' ')
                tmp = (
                    line["username"],
                    line["type"],
                    line["log"],
                    line["addtime"],
                )
                fp.write(",".join(tmp))
                fp.write("\n")
        return {
            "status": True,
            "output_file": tmp_logs_file,
        }

    def get_panel_login_log(self, get):
        '''
        @name 获取面板登录日志
        @param get
            search : 关键字
            login_type: 登陆状态
            page : 页码
            limit : 每页显示数量
        '''
        query_conditions = []
        query_params = []

        # 处理 login_type 条件
        if hasattr(get, "login_type"):
            login_type = get.login_type
            if isinstance(login_type, bytes):
                login_type = login_type.decode('utf-8').strip()
            elif isinstance(login_type, str):
                login_type = login_type.strip()

            if login_type:
                query_conditions.append("login_type = ?")
                query_params.append(login_type)

        # search
        if hasattr(get, "search"):
            search = get.search.strip()

            # 处理字节类型的 search
            if isinstance(search, bytes):
                search = search.decode('utf-8').strip()
            elif isinstance(search, str):
                search = search.strip()

            if search:
                query_conditions.append("(remote_addr LIKE ? OR user_agent LIKE ?)")
                search_params = "%{}%".format(search)
                query_params.extend([search_params, search_params])

        # 构建查询
        query_string = " AND ".join(query_conditions) if query_conditions else "1=1"

        # 分页处理
        page = int(get.page) if hasattr(get, 'page') and str(get.page).isdigit() else 1
        limit = int(get.limit) if hasattr(get, 'limit') and str(get.limit).isdigit() else 10
        offset = (page - 1) * limit

        # 执行查询  按 login_time 降序排序
        data = public.M("client_info").where(query_string, tuple(query_params)) \
            .field("id,remote_addr,remote_port,user_agent,login_time,login_type") \
            .order("login_time DESC") \
            .limit(str(offset) + ',' + str(limit)) \
            .select()
        # 获取总数
        total = public.M("client_info").where(query_string, tuple(query_params)).count()

        return {
            "data": public.return_area(data, "remote_addr"),
            "total": total
        }

    def clear_panel_login_log(self, get):
        '''
        @name 清空面板登录日志
        @param get
        '''

        if not 'uid' in session: session['uid'] = 1
        if session['uid'] != 1: return public.returnMsg(False, '没有权限!')

        public.M('client_info').where('id>?', (0,)).delete()

        public.add_security_logs(
            "清空日志", '清空所有日志条数为:{}'.format(public.M('client_info').count()))
        # 清空日志
        public.M('client_info').where('id>?', (0,)).delete()
        return public.returnMsg(True, 'LOG_CLOSE')

    def export_penel_login_log(self, get):
        '''
        @name 导出面板登录日志
        @param get
        '''
        # 获取登陆日志信息
        limit = int(get.get('limit')) if get.get('limit') else 100
        get['limit'] = limit
        result = self.get_panel_login_log(get)

        # 临时目录
        tmp_logs_path = "/tmp/export_panel_login_log"
        if not os.path.exists(tmp_logs_path):
            os.makedirs(tmp_logs_path, 0o600)
        tmp_logs_file = "{}/panel_login_log_{}.csv".format(tmp_logs_path, int(time.time()))

        # 写入临时文件
        with open(tmp_logs_file, mode="w+", encoding="utf-8") as fp:
            fp.write("登陆IP,登录地址,用户代理,登陆状态,登陆时间\n")
            count = 0
            for line in result["data"]:
                if get.get('type') == 'success' and int(line["login_type"]) != 1:
                    continue
                elif get.get('type') == 'failure' and int(line["login_type"]) == 1:
                    continue

                tmp = (
                    line["remote_addr"],
                    line["area"].get("info", "") if isinstance(line["area"], dict) else "",
                    line["user_agent"],
                    "登陆成功" if int(line["login_type"]) == 1 else "登陆失败",
                    public.format_date(times=line["login_time"])
                )

                fp.write(",".join(tmp))
                fp.write("\n")

                count += 1
                if count >= limit:
                    break

        return {
            "status": True,
            "output_file": tmp_logs_file,
        }

    def index_ssh_info(self, get):
        try:
            value_list = [0, 0]
            if not hasattr(get, 'log_type'):
                return public.returnMsg(False, '参数错误')
            select = get.log_type.strip()
            page = 1

            # 获取数据
            filepath = "/www/server/panel/config/ssh_intrusion.json"
            is_today = False
            is_yesterday = False

            today_time = datetime.date.today()
            yesterday_time = today_time - datetime.timedelta(days=1)

            if public.cache_get("yesterday_data"):
                value_list[1] = public.cache.get("yesterday_data")
            if os.path.exists(filepath):
                try:
                    filedata = json.loads(public.readFile(filepath))
                    if "data" in filedata and "today_success" in filedata["data"] and "today_error" in filedata["data"]:
                        if select == "ALL":
                            value_list[0] = int(filedata["data"]["today_success"]) + int(filedata["data"]["today_error"])
                        elif select == "Accepted":
                            value_list[0] = int(filedata["data"]["today_success"])
                        elif select == "Failed":
                            value_list[0] = int(filedata["data"]["today_error"])
                        is_today = True
                except:
                    pass

            import PluginLoader

            while True:
                args = public.dict_obj()
                args.p = page
                args.model_index = "safe"  # 模块名
                args.count = 100
                args.select = select
                if args.select == "ALL" and page == 10: return value_list

                ssh_list = PluginLoader.module_run("syslog", "get_ssh_list", args)
                if not isinstance(ssh_list, list) or len(ssh_list) == 0:
                    break

                for data in ssh_list:
                    if str(data["time"]).startswith(str(today_time)):
                        if is_today: continue
                        value_list[0] += 1
                    elif str(data["time"]).startswith(str(yesterday_time)) and not is_yesterday:
                        value_list[1] += 1
                        is_yesterday = True
                    else:
                        return value_list
                page += 1
            if not is_yesterday:
                public.cache_set("yesterday_data", value_list[1], 86400)
            return value_list
        except:
            return [0, 0]

