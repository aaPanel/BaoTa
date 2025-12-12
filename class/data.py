# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http:#bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------
import datetime
import sys, os, re, time
import traceback

if not 'class/' in sys.path:
    sys.path.insert(0, 'class/')
import db, public, panelMysql
import json
import idna

try:
    from BTPanel import session
except:
    pass


class data:
    __ERROR_COUNT = 0
    # 自定义排序字段
    __SORT_DATA = ['site_ssl', 'rname', 'php_version', 'backup_count', 'status', 'edate', 'total_flow', '7_day_total_flow', 'one_day_total_flow',
                   'one_hour_total_flow']
    DB_MySQL = None
    web_server = None
    setupPath = '/www/server'
    siteorder_path = '/www/server/panel/data/siteorder1.pl'
    limit_path = '/www/server/panel/data/limit1.pl'
    '''
     * 设置备注信息
     * @param String _GET['tab'] 数据库表名
     * @param String _GET['id'] 条件ID
     * @return Bool 
    '''


    def get_site_num(self, get=None):
        try:
            res = public.M('sites').query("select project_type,count(*) from sites group by project_type")
            if isinstance(res, str):
                return {}
            result = {}
            for i in res:
                result[i[0].lower()] = i[1]
            return result
        except:
            return {}

    def setPs(self, get):
        if not hasattr(get, "id"):
            return public.returnMsg(False, '缺少参数！id')
        id = get.id
        if public.M(get.table).where("id=?", (id,)).setField('ps', public.xssencode2(get.ps)):
            return public.returnMsg(True, 'EDIT_SUCCESS')
        return public.returnMsg(False, 'EDIT_ERROR')

    # 删除排序记录
    def del_sorted(self, get):
        public.ExecShell("rm -rf {}".format(self.siteorder_path))
        return public.returnMsg(True, '清除排序成功！')

    # 设置置顶
    def setSort(self, get=None):
        """
        设置置顶
        :param get: id
        :return:
        """
        file_path = os.path.join(public.get_panel_path(), "data/sort_list.json")
        if os.path.exists(file_path):
            task_top = json.loads(public.readFile(file_path))
        else:
            task_top = {'list': []}
        if get and hasattr(get, 'id'):
            task_top['list'] = [i for i in task_top['list'] if i != get['id']]
            task_top['list'].append(get['id'])
            public.writeFile(file_path, json.dumps(task_top))
            return public.returnMsg(True, '设置置顶成功！')
        return task_top

    # 取消置顶
    def removrSort(self, get):
        """
        取消任务置顶
        :param get:id
        :return:
        """
        file_path = os.path.join(public.get_panel_path(), "data/sort_list.json")
        if os.path.exists(file_path):
            task_top = json.loads(public.readFile(file_path))
        else:
            return public.returnMsg(True, '取消置顶成功！')
        if hasattr(get, 'id'):
            task_top['list'].remove(get['id'])
            public.writeFile(file_path, json.dumps(task_top))
            return public.returnMsg(True, '取消置顶成功！')
        else:
            return public.returnMsg(False, '请传入取消置顶ID！')

    # 端口扫描
    def CheckPort(self, port):
        import socket
        localIP = '127.0.0.1'
        temp = {}
        temp['port'] = port
        temp['local'] = True
        try:
            s = socket.socket()
            s.settimeout(0.01)
            s.connect((localIP, port))
            s.close()
        except:
            temp['local'] = False

        result = 0
        if temp['local']: result += 2
        return result

    # 转换时间
    def strf_date(self, sdate):
        return time.strftime('%Y-%m-%d', time.strptime(sdate, '%Y%m%d%H%M%S'))

    def get_cert_end(self, pem_file):
        if "/www/server/panel/class" not in sys.path:
            sys.path.insert(0, "/www/server/panel/class")
        import ssl_info
        return ssl_info.ssl_info().load_ssl_info(pem_file)
        # try:
        #     import OpenSSL
        #     result = {}

        #     x509 = OpenSSL.crypto.load_certificate(
        #         OpenSSL.crypto.FILETYPE_PEM, public.readFile(pem_file))
        #     # 取产品名称
        #     issuer = x509.get_issuer()
        #     result['issuer'] = ''
        #     if hasattr(issuer, 'CN'):
        #         result['issuer'] = issuer.CN
        #     if not result['issuer']:
        #         is_key = [b'0', '0']
        #         issue_comp = issuer.get_components()
        #         if len(issue_comp) == 1:
        #             is_key = [b'CN', 'CN']
        #         for iss in issue_comp:
        #             if iss[0] in is_key:
        #                 result['issuer'] = iss[1].decode()
        #                 break
        #     # 取到期时间
        #     result['notAfter'] = self.strf_date(
        #         bytes.decode(x509.get_notAfter())[:-1])
        #     # 取申请时间
        #     result['notBefore'] = self.strf_date(
        #         bytes.decode(x509.get_notBefore())[:-1])
        #     # 取可选名称
        #     result['dns'] = []
        #     for i in range(x509.get_extension_count()):
        #         s_name = x509.get_extension(i)
        #         if s_name.get_short_name() in [b'subjectAltName', 'subjectAltName']:
        #             s_dns = str(s_name).split(',')
        #             for d in s_dns:
        #                 result['dns'].append(d.split(':')[1])
        #     subject = x509.get_subject().get_components()
        #     # 取主要认证名称
        #     if len(subject) == 1:
        #         result['subject'] = subject[0][1].decode()
        #     else:
        #         result['subject'] = result['dns'][0]
        #     return result
        # except:

        #     return public.get_cert_data(pem_file)

    def get_site_ssl_info(self, siteName):
        try:
            s_file = 'vhost/nginx/{}.conf'.format(siteName)
            is_apache = False
            if not os.path.exists(s_file):
                s_file = 'vhost/apache/{}.conf'.format(siteName)
                is_apache = True

            if not os.path.exists(s_file):
                return -1

            s_conf = public.readFile(s_file)
            if not s_conf: return -1
            ssl_file = None
            if is_apache:
                if s_conf.find('SSLCertificateFile') == -1:
                    return -1
                s_tmp = re.findall(r"SSLCertificateFile\s+(.+\.pem)", s_conf)
                if not s_tmp: return -1
                ssl_file = s_tmp[0]
            else:
                if s_conf.find('ssl_certificate') == -1:
                    return -1
                s_tmp = re.findall(r"ssl_certificate\s+(.+\.pem);", s_conf)
                if not s_tmp: return -1
                ssl_file = s_tmp[0]
            ssl_info = self.get_cert_end(ssl_file)
            if not ssl_info: return -1
            ssl_info['endtime'] = int(
                int(time.mktime(time.strptime(ssl_info['notAfter'], "%Y-%m-%d")) - time.time()) / 86400)
            return ssl_info
        except:
            return -1
        # return "{}:{}".format(ssl_info['issuer'],ssl_info['notAfter'])

    def get_php_version(self, siteName):
        try:

            if not self.web_server:
                self.web_server = public.get_webserver()

            conf = public.readFile(self.setupPath + '/panel/vhost/' + self.web_server + '/' + siteName + '.conf')
            if self.web_server == 'openlitespeed':
                conf = public.readFile(
                    self.setupPath + '/panel/vhost/' + self.web_server + '/detail/' + siteName + '.conf')
            if self.web_server == 'nginx':
                rep = r"enable-php-(\w{2,5})\.conf"
            elif self.web_server == 'apache':
                rep = r"php-cgi-(\w{2,5})\.sock"
            else:
                rep = r"path\s*/usr/local/lsws/lsphp(\d+)/bin/lsphp"
            tmp = re.search(rep, conf).groups()
            if tmp[0] == '00':
                return '静态'
            if tmp[0] == 'other':
                return '其它'

            return tmp[0][0] + '.' + tmp[0][1]
        except:
            return '静态'

    def map_to_list(self, map_obj):
        try:
            if type(map_obj) != list and type(map_obj) != str: map_obj = list(map_obj)
            return map_obj
        except:
            return []

    def get_database_size(self, databaseName):
        try:
            if not self.DB_MySQL: self.DB_MySQL = panelMysql.panelMysql()
            db_size = self.map_to_list(self.DB_MySQL.query(
                "select sum(DATA_LENGTH)+sum(INDEX_LENGTH) from information_schema.tables  where table_schema='{}'".format(
                    databaseName)))[0][0]
            if not db_size: return 0
            return int(db_size)
        except:
            return 0

    def get_site_netinfo(self):
        """
        @name 获取网站流量
        """
        try:
            import PluginLoader
            args = public.dict_obj()
            args.model_index = 'panel'
            res = PluginLoader.module_run("total", "get_site_traffic", args)

            return res
        except:
            pass
        return {}

    def get_site_net(self, info, siteName):
        """
        @name 获取网站流量
        @param siteName<string> 网站名称
        @return dict
        """
        try:
            if info['status']: info = info['data']
            if siteName in info:
                return info[siteName]
        except:
            pass
        return {}

    def get_waf_status(self, info, siteName):
        """
        @name 获取waf状态
        """
        if siteName in info:
            return info[siteName]
        return {}

    def get_waf_status_all(self):
        """
        @name 获取waf状态
        """
        data = {}
        try:
            path = '/www/server/btwaf/site.json'
            res = json.loads(public.readFile(path))

            for site in res:
                data[site] = {}
                data[site]['status'] = True
                if 'open' in res[site]:
                    data[site]['status'] = res[site]['open']
        except:
            pass

        return data

    def get_site_quota(self, path):
        '''
            @name 获取网站目录配额信息
            @author hwliang<2022-02-15>
            @param path<string> 网站目录
            @return dict
        '''
        res = {
            "used": 0,
            "size": 0,
            "quota_push": {
                "size": 0,
                "used": 0,
            },
            "quota_storage": {
                "size": 0,
                "used": 0,
            }
        }
        try:
            # import PluginLoader
            # quota_info = PluginLoader.module_run('quota', 'get_quota_path', path)
            # if isinstance(quota_info, dict):
            #     quota_info["size"] = quota_info["quota_storage"]["size"]
            #     return quota_info
            return res
        except:
            return res

    def get_database_quota(self, db_name):
        '''
            @name 获取网站目录配额信息
            @author hwliang<2022-02-15>
            @param path<string> 网站目录
            @return dict
        '''
        res = {
            "used": 0,
            "size": 0,
            "quota_push": {
                "size": 0,
                "used": 0,
            },
            "quota_storage": {
                "size": 0,
                "used": 0,
            }
        }
        try:
            import PluginLoader
            quota_info = PluginLoader.module_run('quota', 'get_quota_mysql', db_name)
            if isinstance(quota_info, dict):
                quota_info["size"] = quota_info["quota_storage"]["size"]
                return quota_info
            return res
        except:
            return res

    def _decrypt(self, data):
        import PluginLoader
        if not isinstance(data, str): return data
        if not data: return data
        if data.startswith('BT-0x:'):
            res = PluginLoader.db_decrypt(data[6:])['msg']
            return res
        return data

    # 获取用户权限列表
    def get_user_power(self, get=None):
        user_Data = 'all'
        try:
            uid = session.get('uid')
            if uid != 1 and uid:
                plugin_path = '/www/server/panel/plugin/users'
                if os.path.exists(plugin_path):
                    user_authority = os.path.join(plugin_path, 'authority')
                    if os.path.exists(user_authority):
                        if os.path.exists(os.path.join(user_authority, str(uid))):
                            try:
                                data = json.loads(self._decrypt(public.ReadFile(os.path.join(user_authority, str(uid)))))
                                if data['role'] == 'administrator':
                                    user_Data = 'all'
                                else:
                                    user_Data = json.loads(self._decrypt(public.ReadFile(os.path.join(user_authority, str(uid) + '.data'))))
                            except:
                                user_Data = {}
                        else:
                            user_Data = {}
        except:
            pass
        return user_Data

    '''
     * 取数据列表
     * @param String _GET['tab'] 数据库表名
     * @param Int _GET['count'] 每页的数据行数
     * @param Int _GET['p'] 分页号  要取第几页数据
     * @return Json  page.分页数 , count.总行数   data.取回的数据
    '''

    def getData(self, get):
        try:
            net_flow_type = {
                "total_flow": "总流量",
                "7_day_total_flow": "近7天流量",
                "one_day_total_flow": "近1天流量",
                "one_hour_total_flow": "近1小时流量"
            }
            net_flow_json_file = "/www/server/panel/plugin/total/panel_net_flow.json"
            if get.table == 'sites':
                if not hasattr(get, 'order'):
                    if os.path.exists(self.siteorder_path):
                        order = public.readFile(self.siteorder_path)
                        if order.split(' ')[0] in self.__SORT_DATA:
                            get.order = order
                if not hasattr(get, 'limit') or get.limit == '' or int(get.limit) == 0:
                    try:
                        if os.path.exists(self.limit_path):
                            get.limit = int(public.readFile(self.limit_path))
                        else:
                            get.limit = 20
                    except:
                        get.limit = 20
            if "order" in get:
                order = get.order
                if get.table == 'sites':
                    public.writeFile(self.siteorder_path, order)
                o_list = order.split(' ')
                net_flow_dict = {}
                order_type = None
                if o_list[0].strip() in net_flow_type.keys():
                    net_flow_dict["flow_type"] = o_list[0].strip()
                    if len(o_list) > 1:
                        order_type = o_list[1].strip()
                    else:
                        get.order = 'id desc'
                    net_flow_dict["order_type"] = order_type
                    public.writeFile(net_flow_json_file, json.dumps(net_flow_dict))

            user_Data = self.get_user_power()
            table = get.table
            data = self.GetSql(get)
            SQL = public.M(table)
            # ftp,数据库,网站权限控制
            if user_Data != 'all' and table in ['sites', 'databases', 'ftps']:
                data['data'] = [i for i in data['data'] if str(i['id']) in user_Data.get(table, [])]
            if table == 'backup':
                backup_path = public.M('config').where('id=?', (1,)).getField('backup_path')
                import psutil
                for i in range(len(data['data'])):
                    if data['data'][i]['size'] == 0:
                        if os.path.exists(data['data'][i]['filename']):
                            data['data'][i]['size'] = os.path.getsize(data['data'][i]['filename'])
                    else:
                        if not os.path.exists(data['data'][i]['filename']):
                            if (data['data'][i]['filename'].find('/www/') != -1 or data['data'][i]['filename'].find(backup_path) != -1) and data['data'][i]['filename'][0] == '/' and data['data'][i][
                                'filename'].find('|') == -1:
                                data['data'][i]['size'] = 0
                                data['data'][i]['ps'] = '备份文件不存在！'
                    if data['data'][i]['ps'] in ['', '无']:
                        if data['data'][i]['name'][:3] == 'db_' or (
                                data['data'][i]['name'][:4] == 'web_' and data['data'][i]['name'][-7:] == '.tar.gz'):
                            data['data'][i]['ps'] = '自动备份'
                        else:
                            data['data'][i]['ps'] = '手动备份'
                    try:
                        data['data'][i]['ps'] = str(data['data'][i]['ps'])
                    except:
                        pass

                    # 判断本地文件是否存在，以确定能否下载
                    data['data'][i]['local'] = data['data'][i]['filename'].split('|')[0]
                    data['data'][i]['localexist'] = 0 if not os.path.isfile(data['data'][i]['local']) else 1
                    data['data'][i]['backup_status'] = 0
                    pl_path = data['data'][i]['filename'] + '.pl'
                    if os.path.exists(pl_path):
                        pid = public.readFile(pl_path)
                        try:
                            pid = int(pid)
                            pro = psutil.Process(pid)
                            if pro.status() ==psutil.STATUS_ZOMBIE:
                                raise
                            data['data'][i]['backup_status'] = 1
                            data['data'][i]['size'] = os.path.getsize(data['data'][i]['filename'])
                        except:
                            data['data'][i]['size'] = os.path.getsize(data['data'][i]['filename'])
                            os.remove(pl_path)
            elif table == 'sites' or table == 'databases':
                type = '0'
                if table == 'databases': type = '1'
                for i in range(len(data['data'])):
                    data['data'][i]['backup_count'] = public.M('backup').where("pid=? AND type=?", (data['data'][i]['id'], type)).count()
                    if table == 'databases': data['data'][i]['conn_config'] = json.loads(data['data'][i]['conn_config'])
                    data['data'][i]['quota'] = self.get_database_quota(data['data'][i]['name'])
                if table == 'sites':
                    try:
                        import panelSite
                        ps = panelSite.panelSite()
                    except:
                        pass
                    total_net = self.get_site_netinfo()
                    waf_data = self.get_waf_status_all()
                    for i in range(len(data['data'])):
                        data['data'][i]['domain'] = public.M('domain').where("pid=?", (data['data'][i]['id'],)).count()
                        data['data'][i]['ssl'] = self.get_site_ssl_info(data['data'][i]['name'])
                        data['data'][i]['php_version'] = self.get_php_version(data['data'][i]['name'])
                        if not data['data'][i]['status'] in ['0', '1', 0, 1]:
                            data['data'][i]['status'] = '1'
                        data['data'][i]['quota'] = self.get_site_quota(data['data'][i]['path'])
                        data['data'][i]['net'] = self.get_site_net(total_net, data['data'][i]['name'])

                        data['data'][i]['waf'] = self.get_waf_status(waf_data, data['data'][i]['name'])

                        if not data['data'][i].get('rname', ''):
                            data['data'][i]['rname'] = data['data'][i]['name']
                        try:
                            data['data'][i]['proxy'] = False
                            data['data'][i]['redirect'] = False
                            proxy = ps.GetProxyList(public.to_dict_obj({"sitename": data['data'][i]['name']}))
                            redirect = ps.GetRedirectList(public.to_dict_obj({"sitename": data['data'][i]['name']}))
                            if proxy: data['data'][i]['proxy'] = True
                            if redirect: data['data'][i]['redirect'] = True
                        except:
                            data['data'][i]['proxy'] = False
                            data['data'][i]['redirect'] = False
                    # 新增监控报表转化入口 - 流量显示
                    data["net_flow_type"] = [
                        {"total_flow": net_flow_type["total_flow"]},
                        {"7_day_total_flow": net_flow_type["7_day_total_flow"]},
                        {"one_day_total_flow": net_flow_type["one_day_total_flow"]},
                        {"one_hour_total_flow": net_flow_type["one_hour_total_flow"]}
                        # {"realtime_traffic": net_flow_type["realtime_traffic"]}
                    ]

                    try:
                        net_flow_json_info = json.loads(public.readFile(net_flow_json_file))
                        data["net_flow_info"] = net_flow_json_info
                    except Exception:
                        data["net_flow_info"] = {}

            elif table == 'firewall':
                for i in range(len(data['data'])):
                    if data['data'][i]['port'].find(':') != -1 or data['data'][i]['port'].find('.') != -1 or \
                            data['data'][i]['port'].find('-') != -1:
                        data['data'][i]['status'] = -1
                    else:
                        data['data'][i]['status'] = self.CheckPort(int(data['data'][i]['port']))
            elif table == 'ftps':
                for i in range(len(data['data'])):
                    data['data'][i]['quota'] = self.get_site_quota(data['data'][i]['path'] + '/')
                    import ftp
                    data['data'][i]['end_time'] = ftp.ftp().get_cron_config(public.to_dict_obj({'id': data['data'][i]['id']}))['end_time']
            elif table == 'domain':
                for i in data:
                    if isinstance(i, dict):
                        try:
                            i['cn_name'] = idna.decode(i['name'])
                        except:
                            i['cn_name'] = i['name']

            if isinstance(data, dict):
                file_path = os.path.join(public.get_panel_path(), "data/sort_list.json")
                if os.path.exists(file_path):
                    sort_list_raw = public.readFile(file_path)
                    sort_list = json.loads(sort_list_raw)
                    sort_list_int = [int(item) for item in sort_list["list"]]

                    for i in range(len(data['data'])):
                        if int(data['data'][i]['id']) in sort_list_int:
                            data['data'][i]['sort'] = 1
                        else:
                            data['data'][i]['sort'] = 0

                    top_list = sort_list["list"]
                    if top_list:
                        top_list = top_list[::-1]
                    top_data = [item for item in data["data"] if str(item['id']) in top_list]
                    data1 = [item for item in data["data"] if str(item['id']) not in top_list]
                    top_data.sort(key=lambda x: top_list.index(str(x['id'])))

                    data['data'] = top_data + data1

                # data['data'].sort(key=lambda item: item['sort'], reverse=True)

            try:
                for _find in data['data']:
                    _keys = _find.keys()
                    for _key in _keys:
                        _find[_key] = public.xsssec2(_find[_key])
            except:
                pass

            # 返回
            return self.get_sort_data(data)
        except:
            return public.get_error_info()

    def get_sort_data(self, data):
        """
        @获取自定义排序数据
        @param data: 数据
        """
        if 'plist' in data:
            plist = data['plist']
            o_list = plist['order'].split(' ')

            reverse = False
            sort_key = o_list[0].strip()

            if o_list[1].strip() == 'desc':
                reverse = True

            if sort_key in ['site_ssl']:
                for info in data['data']:
                    if type(info['ssl']) == int:
                        info[sort_key] = info['ssl']
                    else:
                        try:
                            info[sort_key] = info['ssl']['endtime']
                        except:
                            info[sort_key] = ''
            elif sort_key in ['total_flow', 'one_hour_total_flow', '7_day_total_flow', 'one_day_total_flow']:
                for info in data['data']:
                    info[sort_key] = 0
                    try:
                        if 'net' in info and sort_key in info['net']:
                            info[sort_key] = info['net'][sort_key]
                    except:
                        pass

            sort_reverse = 1 if reverse is True else 0
            data['data'].sort(key=lambda x: (x.get('sort', 0) == sort_reverse, x[sort_key]), reverse=reverse)
            data['data'] = data['data'][plist['shift']: plist['shift'] + plist['row']]

        return data

    '''
     * 取数据库行
     * @param String _GET['tab'] 数据库表名
     * @param Int _GET['id'] 索引ID
     * @return Json
    '''

    def getFind(self, get):
        tableName = get.table
        id = get.id
        field = self.GetField(get.table)
        SQL = public.M(tableName)
        where = "id=?"
        find = SQL.where(where, (id,)).field(field).find()
        try:
            _keys = find.keys()
            for _key in _keys:
                find[_key] = public.xsssec(find[_key])
        except:
            pass
        return find

    '''
     * 取字段值
     * @param String _GET['tab'] 数据库表名
     * @param String _GET['key'] 字段
     * @param String _GET['id'] 条件ID
     * @return String
    '''

    def getKey(self, get):
        if not hasattr(get, 'table'):
            return public.returnMsg(False, "缺少参数! table")
        if not hasattr(get, 'key'):
            return public.returnMsg(False, "缺少参数! key")
        if not hasattr(get, 'id'):
            return public.returnMsg(False, "缺少参数! id")

        tableName = get.table
        keyName = get.key
        id = get.id
        SQL = db.Sql().table(tableName)
        where = "id=?"
        retuls = SQL.where(where, (id,)).getField(keyName)
        if not retuls:
            return public.returnMsg(False, '未获取到数据!')

        try:
            if tableName == "config" and keyName == "mysql_root" and int(id) == 1:
                exec_sql = "/usr/bin/mysql --user=root --password='{password}' --default-character-set=utf8 -e 'SET sql_notes = 0;show databases;'".format(password=retuls)
                res = public.ExecShell(exec_sql)
                if 'access denied for user' in res[1].lower():
                    from database import database
                    database().SetupPassword(public.to_dict_obj({'password': retuls}))
        except:
            pass
        return public.xsssec(retuls)

    '''
     * 获取数据与分页
     * @param string table 表
     * @param string where 查询条件
     * @param int limit 每页行数
     * @param mixed result 定义分页数据结构
     * @return array
    '''

    def GetSql(self, get, result='1,2,3,4,5,8'):
        # 判断前端是否传入参数
        order = 'id desc'
        if hasattr(get, 'order'):
            # 验证参数格式
            if re.match(r"^[\w\s\-\.]+$", get.order):
                order = get.order

        search_key = 'get_list'
        limit = 20
        if hasattr(get, 'limit'):
            try:
                limit = int(get.limit)
            except ValueError:
                limit = 20
            if limit < 1:
                limit = 20
            else:
                if get.table == 'sites':
                    public.writeFile(self.limit_path, str(limit))

        if hasattr(get, 'result'):
            # 验证参数格式
            if re.match(r"^[\d\,]+$", get.result):
                result = get.result

        SQL = db.Sql()
        data = {}
        # 取查询条件
        where = ''
        search = ''
        param = ()

        logs_type = get.get("log_type", "")

        if get.table == "logs" and logs_type:
            where = " type = '{}' ".format(get.log_type)

        if hasattr(get, 'search'):
            search = get.search
            if sys.version_info[0] == 2: get.search = get.search.encode('utf-8')
            where, param = self.GetWhere(get.table, get.search)
            if get.table == 'logs' and logs_type and search:
                where = " type='{}' and ({})".format(get.log_type, where)
            if get.table == 'backup':
                where += " and type='{}'".format(int(get.type))
            if get.table == 'sites' and get.search:
                conditions = ''
                if '_' in get.search:
                    get.search = str(get.search).replace("_", "/_")
                    conditions = " escape '/'"
                pid = public.M('domain').where("name LIKE ?{}".format(conditions), ("%{}%".format(get.search),)).getField('pid')
                if pid:
                    if where:
                        where += " or id=" + str(pid)
                    else:
                        where += "id=" + str(pid)
        if get.table == 'sites':
            # search_key = 'Java'
            # if where:
            #     where = "({}) AND project_type='Java'".format(where)
            # else:
            #     where = "project_type='Java'"

            if hasattr(get, 'type'):
                if get.type != '-1':
                    if where:
                        where += " AND type_id={}".format(int(get.type))
                    else:
                        where = "type_id={}".format(int(get.type))
        if get.table == 'ftps':
            search_key = 'ftps'

        if get.table == 'databases':
            search_key = 'mysql'
            if hasattr(get, 'db_type'):
                if where:
                    where += " AND db_type='{}'".format(int(get.db_type))
                else:
                    where = "db_type='{}'".format(int(get.db_type))
            if hasattr(get, 'sid'):
                if where:
                    where += " AND sid='{}'".format(int(get.sid))
                else:
                    where = "sid='{}'".format(int(get.sid))

            if where:
                where += " and LOWER(type)=LOWER('MySQL')"
            else:
                where = 'LOWER(type) = LOWER("MySQL")'

        mysql_auto_status = "/www/server/panel/data/is_sqlist.pl"
        data['auto_list'] = os.path.exists(mysql_auto_status) and public.readFile(mysql_auto_status).lower() == "true"

        field = self.GetField(get.table)
        if get.table == 'sites':
            cront = public.M(get.table).order("id desc").field(field).select()
            if type(cront) == str:
                public.M('sites').execute("ALTER TABLE 'sites' ADD 'rname' text DEFAULT ''", ())
        # 实例化数据库对象
        public.set_search_history(get.table, search_key, search)  # 记录搜索历史
        # 是否直接返回所有列表
        if hasattr(get, 'list'):
            data = public.M(get.table).where(where, param).field(field).order(order).select()
            return data
        # 取总行数
        count = public.M(get.table).where(where, param).count()
        # get.uri = get
        # 包含分页类
        import page
        # 实例化分页类
        page = page.Page()

        info = {}
        info['count'] = count
        info['row'] = limit

        info['p'] = 1
        if hasattr(get, 'p'):
            info['p'] = int(get['p'])
            if info['p'] < 1: info['p'] = 1

        try:
            from flask import request
            info['uri'] = public.url_encode(request.full_path)
        except:
            info['uri'] = ''
        info['return_js'] = ''
        if hasattr(get, 'tojs'):
            if re.match(r"^[\w\.\-]+$", get.tojs):
                info['return_js'] = get.tojs

        data['where'] = where

        # 获取分页数据
        data['page'] = page.GetPage(info, result)
        # 取出数据
        # data['data'] = public.M(get.table).where(where,param).order(order).field(field).limit(str(page.SHIFT)+','+str(page.ROW)).select()

        o_list = order.split(' ')
        if o_list[0] in self.__SORT_DATA:
            data['data'] = public.M(get.table).where(where, param).field(field).select()
            data['plist'] = {'shift': page.SHIFT, 'row': page.ROW, 'order': order}
        else:
            data['data'] = public.M(get.table).where(where, param).order(order).field(field).limit(
                str(page.SHIFT) + ',' + str(page.ROW)).select()  # 取出数据
        data['search_history'] = public.get_search_history(get.table, search_key)

        return data

    # 获取条件
    def GetWhere(self, tableName, search):
        if not search: return "", ()

        if type(search) == bytes: search = search.encode('utf-8').strip()

        try:
            search = re.search(r"[\w\x80-\xff\.\_\-]+", search).group()
        except:
            return '', ()
        conditions = ''

        if '_' in search:
            search = str(search).replace("_", "/_")
            conditions = " escape '/'"
        wheres = {
            'sites': ("name LIKE ?{} OR ps LIKE ?{}".format(conditions, conditions), ('%' + search + '%', '%' + search + '%')),
            'ftps': ("name LIKE ?{} OR ps LIKE ?{}".format(conditions, conditions), ('%' + search + '%', '%' + search + '%')),
            'databases': ("(name LIKE ?{} OR ps LIKE ?{})".format(conditions, conditions), ("%" + search + "%", "%" + search + "%")),
            'crontab': ("name LIKE ?{}".format(conditions), ('%' + (search) + '%')),
            'logs': ("username LIKE ?{} OR type LIKE ?{} OR log LIKE ?{}".format(conditions, conditions, conditions), ('%' + search + '%','%' + search + '%','%' + search + '%')),
            'backup': ("pid=?", (search,)),
            'users': ("id='?' OR username=?{}".format(conditions), (search, search)),
            'domain': ("pid=? OR name=?{}".format(conditions), (search, search)),
            'tasks': ("status=? OR type=?", (search, search)),
        }
        try:
            return wheres[tableName]
        except:
            return '', ()

    # 获取返回的字段
    def GetField(self, tableName):
        fields = {
            'sites': "*",
            'ftps': "id,pid,name,password,status,ps,addtime,path",
            'databases': "*",
            'logs': "id,uid,username,type,log,addtime",
            'backup': "id,pid,name,filename,addtime,size,ps,cron_id",
            'users': "id,username,phone,email,login_ip,login_time",
            'firewall': "id,port,ps,addtime",
            'domain': "id,pid,name,port,addtime",
            'tasks': "id,name,type,status,addtime,start,end"
        }
        try:
            return fields[tableName]
        except:
            return ''

    # 获取返回的字段
    # def GetField(self, tableName):
    #     fields = {
    #         'sites': "id,name,path,status,ps,addtime,edate,rname",
    #         'ftps': "id,pid,name,password,status,ps,addtime,path",
    #         'databases': "id,sid,pid,name,username,password,accept,ps,addtime,db_type,conn_config",
    #         'logs': "id,uid,username,type,log,addtime",
    #         'backup': "id,pid,name,filename,addtime,size,ps",
    #         'users': "id,username,phone,email,login_ip,login_time",
    #         'firewall': "id,port,ps,addtime",
    #         'domain': "id,pid,name,port,addtime",
    #         'tasks': "id,name,type,status,addtime,start,end"
    #     }
    #     try:
    #         return fields[tableName]
    #     except:
    #         return ''

    def get_https_port(self, get):
        try:
            if not hasattr(get, 'siteName'): return public.returnMsg(False, '参数错误!')
            if os.path.exists('/www/server/panel/vhost/nginx/{}.conf'.format(get.siteName)):
                conf = public.readFile('/www/server/panel/vhost/nginx/{}.conf'.format(get.siteName))
                rep = r"listen\s+(\d+)\s*ssl"
                port = 0
                try:
                    port = int(re.search(rep, conf).groups()[0])
                except:
                    pass
                return port
        except:
            return 0

    def set_https_port(self, get):
        if not hasattr(get, 'siteName'): return public.returnMsg(False, '参数错误!')
        if not hasattr(get, 'port'): return public.returnMsg(False, '参数错误!')
        if not os.path.exists('/www/server/panel/vhost/nginx/{}.conf'.format(get.siteName)):
            return public.returnMsg(False, '配置文件不存在!')
        conf = public.readFile('/www/server/panel/vhost/nginx/{}.conf'.format(get.siteName))
        rep = r"(listen\s+\d+\s*ssl.*?;)"
        port = get.port
        old_conf = re.search(rep, conf).groups()[0]
        old_port = re.search(r"listen\s+(\d+)\s*ssl", old_conf).groups()[0]
        use_http2_on = public.is_change_nginx_http2()
        if not use_http2_on:
            new_conf = 'listen {} ssl http2;'.format(port)
        else:
            new_conf = 'listen {} ssl;'.format(port)
        conf = conf.replace(old_conf, new_conf)
        public.writeFile('/www/server/panel/vhost/nginx/{}.conf'.format(get.siteName), conf)
        apa_conf = public.readFile('/www/server/panel/vhost/apache/{}.conf'.format(get.siteName))
        apa_conf = apa_conf.replace('<VirtualHost *:{}>'.format(old_port), '<VirtualHost *:{}>'.format(port))
        self.apacheAddPort(port)
        public.writeFile('/www/server/panel/vhost/apache/{}.conf'.format(get.siteName), apa_conf)
        public.serviceReload()
        return public.returnMsg(True, '设置成功,请在防火墙放行该端口!')

    def apacheAddPort(self, port):
        port = str(port)
        filename = self.setupPath + '/apache/conf/extra/httpd-ssl.conf'
        if os.path.exists(filename):
            ssl_conf = public.readFile(filename)
            if ssl_conf:
                if ssl_conf.find('Listen 443') != -1:
                    ssl_conf = ssl_conf.replace('Listen 443', '')
                    public.writeFile(filename, ssl_conf)

        filename = self.setupPath + '/apache/conf/httpd.conf'
        if not os.path.exists(filename): return
        allConf = public.readFile(filename)
        rep = r"Listen\s+([0-9]+)\n"
        tmp = re.findall(rep, allConf)
        if not tmp: return False
        for key in tmp:
            if key == port: return False

        listen = "\nListen " + tmp[0] + "\n"
        listen_ipv6 = ''
        # if self.is_ipv6: listen_ipv6 = "\nListen [::]:" + port
        allConf = allConf.replace(listen, listen + "Listen " + port + listen_ipv6 + "\n")
        public.writeFile(filename, allConf)
        return True

    def check_port(self, port):
        '''
        @name 检查端口是否被占用
        @args port:端口号
        @return: 被占用返回True，否则返回False
        @author: lkq 2021-08-28
        '''
        a = public.ExecShell("netstat -nltp|awk '{print $4}'")
        if a[0]:
            if re.search(':' + port + '\n', a[0]):
                return True
            else:
                return False
        else:
            return False
