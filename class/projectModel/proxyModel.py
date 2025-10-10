# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: lkq <lkq@bt.cn>
# -------------------------------------------------------------------

# ------------------------------
# proxy模型
# ------------------------------

import os, sys, re, json, shutil, psutil, time, hashlib
from projectModel.base import projectBase
from typing import Dict, Union, List, Optional
import public, firewalls
from typing import Tuple

import ipaddress

try:
    from BTPanel import cache
except:
    pass


class mobj:
    port = ps = ''


class main(projectBase):
    _panel_path = public.get_panel_path()
    _proxy_path = '/www/server/proxy_project'
    _log_name = '项目管理'
    _proxy_logs_path = "/www/wwwlogs/proxy"
    _vhost_path = '{}/vhost'.format(_panel_path)
    _pids = None
    # 自定义排序字段
    __SORT_DATA = ['site_ssl', 'php_version', 'backup_count', 'total_flow', '7_day_total_flow', 'one_day_total_flow',
                   'one_hour_total_flow']

    sitePort = None  # 端口
    siteName = None  # 网站名称
    sitePath = None  # 根目录
    phpVersion = None  # PHP版本
    setupPath = None  # 安装路径
    isWriteLogs = None  # 是否写日志
    nginx_conf_bak = '/tmp/backup_nginx.conf'
    apache_conf_bak = '/tmp/backup_apache.conf'
    is_ipv6 = False
    conf_dir = '{}/vhost/config'.format(public.get_panel_path())  # 防盗链配置

    def __init__(self):
        self.setupPath = public.get_setup_path()
        if not os.path.exists(self._proxy_path):
            os.makedirs(self._proxy_path, 493)
        self.__proxyfile = '{}/data/proxy_project.json'.format(public.get_panel_path())
        if os.path.exists(self.nginx_conf_bak): os.remove(self.nginx_conf_bak)
        if os.path.exists(self.apache_conf_bak): os.remove(self.apache_conf_bak)
        sys.setrecursionlimit(1000000)
        if not os.path.isdir(self.conf_dir):
            os.makedirs(self.conf_dir)
        self.config_prefix = ''

    @staticmethod
    def check_webserver(use2render=False):
        setup_path = public.GetConfigValue('setup_path')
        ng_path = setup_path + '/nginx/sbin/nginx'
        ap_path = setup_path + '/apache/bin/apachectl'
        op_path = '/usr/local/lsws/bin/lswsctrl'
        not_server = False
        if not os.path.exists(ng_path) and not os.path.exists(ap_path) and not os.path.exists(op_path):
            not_server = True
        if not not_server:
            return
        tasks = public.M('tasks').where("status!=? AND type!=?", ('1', 'download')).field('id,name').select()
        for task in tasks:
            name = task["name"].lower()
            if name.find("openlitespeed") != -1:
                return "正在安装OpenLiteSpeed服务，请等待安装完成后再操作"
            if name.find("nginx") != -1:
                return "正在安装Nginx服务，请等待安装完成后再操作"
            if name.lower().find("apache") != -1:
                return "正在安装Apache服务，请等待安装完成后再操作"
        if use2render:
            return None

        return "未安装任意Web服务，请安装Nginx或Apache后再操作"

    def __get_site_format_path(self, path):
        path = path.replace('//', '/')
        if path[-1:] == '/':
            path = path[:-1]
        return path

    def __check_site_path(self, path):
        path = self.__get_site_format_path(path)
        other_path = public.M('config').where("id=?", ('1',)).field('sites_path,backup_path').find()
        if path == other_path['sites_path'] or path == other_path['backup_path']: return False
        return True

    # 域名编码转换
    def ToPunycode(self, domain):
        import re
        if sys.version_info[0] == 2: domain = domain.encode('utf8')
        tmp = domain.split('.')
        newdomain = ''
        for dkey in tmp:
            if dkey == '*': continue
            # 匹配非ascii字符
            match = re.search(u"[\x80-\xff]+", dkey)
            if not match: match = re.search(u"[\u4e00-\u9fa5]+", dkey)
            if not match:
                newdomain += dkey + '.'
            else:
                if sys.version_info[0] == 2:
                    newdomain += 'xn--' + dkey.decode('utf-8').encode('punycode') + '.'
                else:
                    newdomain += 'xn--' + dkey.encode('punycode').decode('utf-8') + '.'
        if tmp[0] == '*': newdomain = "*." + newdomain
        return newdomain[0:-1]

    # 中文路径处理
    def ToPunycodePath(self, path):
        if sys.version_info[0] == 2: path = path.encode('utf-8')
        if os.path.exists(path): return path
        import re
        match = re.search(u"[\x80-\xff]+", path)
        if not match: match = re.search(u"[\u4e00-\u9fa5]+", path)
        if not match: return path
        npath = ''
        for ph in path.split('/'):
            npath += '/' + self.ToPunycode(ph)
        return npath.replace('//', '/')

    # 路径处理
    def GetPath(self, path):
        if path[-1] == '/':
            return path[0:-1]
        return path

    @staticmethod
    def create_default_conf(get=None):
        status = {
            "page_404": True,
            "page_index": True,
            "log_split": False,
        }
        tip_file_path = public.get_panel_path() + "/data/php_create_default_conf.json"
        if os.path.exists(tip_file_path):
            data = public.readFile(tip_file_path)
            if data is not False:
                status = json.loads(data)
        return status

    # 添加站点
    def AddSite(self, get, multiple=None):
        try:
            res_msg = self.check_webserver(use2render=False)  # 检查是否有web服务
            if res_msg:
                return public.returnMsg(False, res_msg)
            # self.check_default()
            isError = public.checkWebConfig()
            if isError != True:
                return public.returnMsg(False, 'ERROR: 检测到配置文件有错误,请先排除后再操作<br><br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')

            import json, files

            get.path = self.__get_site_format_path(get.path)

            if not public.check_site_path(get.path):
                a, c = public.get_sys_path()
                return public.returnMsg(False, '请不要将网站根目录设置到以下关键目录中: <br>{}'.format("<br>".join(a + c)))
            try:
                siteMenu = json.loads(get.webname)
            except:
                return public.returnMsg(False, 'webname参数格式不正确，应该是可被解析的JSON字符串')
            self.siteName = self.ToPunycode(siteMenu['domain'].strip().split(':')[0]).strip().lower()
            self.sitePath = self.ToPunycodePath(self.GetPath(get.path.replace(' ', ''))).strip()
            self.sitePort = get.port.strip().replace(' ', '')
            if self.sitePort == "": get.port = "80"
            if not public.checkPort(self.sitePort): return public.returnMsg(False, 'SITE_ADD_ERR_PORT')
            for domain in siteMenu['domainlist']:
                if not len(domain.split(':')) == 2:
                    continue
                if not public.checkPort(domain.split(':')[1]): return public.returnMsg(False, 'SITE_ADD_ERR_PORT')

            if hasattr(get, 'version'):
                self.phpVersion = get.version.replace(' ', '')
            else:
                self.phpVersion = '00'

            if not self.phpVersion: self.phpVersion = '00'

            # php_version = self.GetPHPVersion(get)
            # is_phpv = False
            # for php_v in php_version:
            #     if self.phpVersion == php_v['version']:
            #         is_phpv = True
            #         break
            # if not is_phpv: return public.returnMsg(False, '指定PHP版本不存在!')

            domain = None

            # 表单验证
            if not self.__check_site_path(self.sitePath): return public.returnMsg(False, 'PATH_ERROR')
            if len(self.phpVersion) < 2: return public.returnMsg(False, 'SITE_ADD_ERR_PHPEMPTY')
            reg = r"^([\w\-\*]{1,100}\.){1,24}([\w\-]{1,24}|[\w\-]{1,24}\.[\w\-]{1,24})$"
            if not re.match(reg, self.siteName): return public.returnMsg(False, 'SITE_ADD_ERR_DOMAIN')
            if self.siteName.find('*') != -1: return public.returnMsg(False, 'SITE_ADD_ERR_DOMAIN_TOW')
            if self.sitePath[-1] == '.': return public.returnMsg(False, '网站目录结尾不可以是 "."')

            if not domain: domain = self.siteName

            # 是否重复
            sql = public.M('sites')
            if sql.where("name=?", (self.siteName,)).count(): return public.returnMsg(False, 'SITE_ADD_ERR_EXISTS')
            opid = public.M('domain').where("name=?", (self.siteName,)).getField('pid')

            if opid:
                if public.M('sites').where('id=?', (opid,)).count():
                    return public.returnMsg(False, 'SITE_ADD_ERR_DOMAIN_EXISTS')
                public.M('domain').where('pid=?', (opid,)).delete()

            if public.M('binding').where('domain=?', (self.siteName,)).count():
                return public.returnMsg(False, 'SITE_ADD_ERR_DOMAIN_EXISTS')

            create_conf = self.create_default_conf()
            # 创建根目录
            if not os.path.exists(self.sitePath):
                try:
                    os.makedirs(self.sitePath)
                except Exception as ex:
                    return public.returnMsg(False, '创建根目录失败, %s' % ex)
                public.ExecShell('chmod -R 755 ' + self.sitePath)
                public.ExecShell('chown -R www:www ' + self.sitePath)

            # 创建basedir
            self.DelUserInI(self.sitePath)

            # 创建默认文档
            index = self.sitePath + '/index.html'
            if not os.path.exists(index) and create_conf["page_index"]:
                public.writeFile(index, public.readFile('data/defaultDoc.html'))
                public.ExecShell('chmod -R 755 ' + index)
                public.ExecShell('chown -R www:www ' + index)

            # 创建自定义404页
            doc404 = self.sitePath + '/404.html'
            if not os.path.exists(doc404) and create_conf["page_404"]:
                public.writeFile(doc404, public.readFile('data/404.html'))
                public.ExecShell('chmod -R 755 ' + doc404)
                public.ExecShell('chown -R www:www ' + doc404)

            # 写入配置
            result = self.nginxAdd()
            result = self.apacheAdd()
            result = self.openlitespeed_add_site(get)

            # 检查处理结果
            if not result: return public.returnMsg(False, 'SITE_ADD_ERR_WRITE')

            ps = public.xssencode2(get.ps)
            # 添加放行端口
            if self.sitePort != '80':
                import firewalls
                get.port = self.sitePort
                get.ps = self.siteName
                firewalls.firewalls().AddAcceptPort(get)

            if not hasattr(get, 'type_id'): get.type_id = 0
            public.check_domain_cloud(self.siteName)
            # 写入数据库
            get.pid = sql.table('sites').add('name,path,status,ps,type_id,addtime,project_type', (self.siteName, self.sitePath, '1', ps, get.type_id, public.getDate(), "proxy"))
            # 添加更多域名
            for domain in siteMenu['domainlist']:
                get.domain = domain
                get.webname = self.siteName
                get.id = str(get.pid)
                self.AddDomain(get, multiple)

            sql.table('domain').add('pid,name,port,addtime', (get.pid, self.siteName, self.sitePort, public.getDate()))

            data = {
                'siteStatus': True,
                'siteId': get.pid,
                'sitename': self.siteName
            }

            if not multiple:
                public.serviceReload()
            public.WriteLog('TYPE_SITE', 'SITE_ADD_SUCCESS', (self.siteName,))
            if create_conf["log_split"]:
                self.site_crontab_log(self.siteName)

            return data
        except Exception as e:
            pass
    @staticmethod
    def site_crontab_log(site_name):
        if public.M("crontab").where("sName =? and sType = ?", ("ALL", "logs")).find():
            return True

        import crontab
        crontabs = crontab.crontab()
        args = {
            "name": "切割日志[{}]".format(site_name),
            "type": 'day',
            "where1": '',
            "hour": 0,
            "minute": 1,
            "sName": site_name,
            "sType": 'logs',
            "notice": '',
            "notice_channel": '',
            "save": 180,
            "save_local": '1',
            "backupTo": '',
            "sBody": '',
            "urladdress": ''
        }
        res = crontabs.AddCrontab(args)
        if res and "id" in res.keys():
            return True
        return False

    # 删除站点
    def DeleteSite(self, get, multiple=None):
        try:
            proxyconf = self.__read_config(self.__proxyfile)
            id = get.id
            if public.M('sites').where('id=?', (id,)).count() < 1: return public.returnMsg(False, '指定站点不存在!')
            siteName = get.webname
            get.siteName = siteName
            # 删除反向代理
            for i in range(len(proxyconf) - 1, -1, -1):
                if proxyconf[i]["sitename"] == siteName:
                    del proxyconf[i]
            self.__write_config(self.__proxyfile, proxyconf)

            m_path = self.setupPath + '/panel/vhost/nginx/proxy/' + siteName
            if os.path.exists(m_path): public.ExecShell("rm -rf %s" % m_path)

            m_path = self.setupPath + '/panel/vhost/apache/proxy/' + siteName
            if os.path.exists(m_path): public.ExecShell("rm -rf %s" % m_path)

            # 删除目录保护
            _dir_aith_file = "%s/panel/data/site_dir_auth.json" % self.setupPath
            _dir_aith_conf = public.readFile(_dir_aith_file)
            if _dir_aith_conf:
                try:
                    _dir_aith_conf = json.loads(_dir_aith_conf)
                    if siteName in _dir_aith_conf:
                        del (_dir_aith_conf[siteName])
                except:
                    pass
            self.__write_config(_dir_aith_file, _dir_aith_conf)

            dir_aith_path = self.setupPath + '/panel/vhost/nginx/dir_auth/' + siteName
            if os.path.exists(dir_aith_path): public.ExecShell("rm -rf %s" % dir_aith_path)

            dir_aith_path = self.setupPath + '/panel/vhost/apache/dir_auth/' + siteName
            if os.path.exists(dir_aith_path): public.ExecShell("rm -rf %s" % dir_aith_path)

            # 删除重定向
            __redirectfile = "%s/panel/data/redirect.conf" % self.setupPath
            redirectconf = self.__read_config(__redirectfile)
            for i in range(len(redirectconf) - 1, -1, -1):
                if redirectconf[i]["sitename"] == siteName:
                    del redirectconf[i]
            self.__write_config(__redirectfile, redirectconf)
            m_path = self.setupPath + '/panel/vhost/nginx/redirect/' + siteName
            if os.path.exists(m_path): public.ExecShell("rm -rf %s" % m_path)
            m_path = self.setupPath + '/panel/vhost/apache/redirect/' + siteName
            if os.path.exists(m_path): public.ExecShell("rm -rf %s" % m_path)

            # 删除配置文件
            confPath = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
            if os.path.exists(confPath): os.remove(confPath)

            confPath = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
            if os.path.exists(confPath): os.remove(confPath)
            open_basedir_file = self.setupPath + '/panel/vhost/open_basedir/nginx/' + siteName + '.conf'
            if os.path.exists(open_basedir_file): os.remove(open_basedir_file)

            # 删除openlitespeed配置
            vhost_file = "/www/server/panel/vhost/openlitespeed/{}.conf".format(siteName)
            if os.path.exists(vhost_file):
                public.ExecShell('rm -f {}*'.format(vhost_file))
            vhost_detail_file = "/www/server/panel/vhost/openlitespeed/detail/{}.conf".format(siteName)
            if os.path.exists(vhost_detail_file):
                public.ExecShell('rm -f {}*'.format(vhost_detail_file))
            vhost_ssl_file = "/www/server/panel/vhost/openlitespeed/detail/ssl/{}.conf".format(siteName)
            if os.path.exists(vhost_ssl_file):
                public.ExecShell('rm -f {}*'.format(vhost_ssl_file))
            vhost_sub_file = "/www/server/panel/vhost/openlitespeed/detail/{}_sub.conf".format(siteName)
            if os.path.exists(vhost_sub_file):
                public.ExecShell('rm -f {}*'.format(vhost_sub_file))

            vhost_redirect_file = "/www/server/panel/vhost/openlitespeed/redirect/{}".format(siteName)
            if os.path.exists(vhost_redirect_file):
                public.ExecShell('rm -rf {}*'.format(vhost_redirect_file))
            vhost_proxy_file = "/www/server/panel/vhost/openlitespeed/proxy/{}".format(siteName)
            if os.path.exists(vhost_proxy_file):
                public.ExecShell('rm -rf {}*'.format(vhost_proxy_file))

            # 删除openlitespeed监听配置
            # self._del_ols_listen_conf(siteName)

            # 删除伪静态文件
            filename = '/www/server/panel/vhost/rewrite/' + siteName + '.conf'
            if os.path.exists(filename):
                os.remove(filename)
                public.ExecShell("rm -f " + confPath + '/rewrite/' + siteName + "_*")

            # 删除日志文件
            filename = public.GetConfigValue('logs_path') + '/' + siteName + '*'
            public.ExecShell("rm -f " + filename)

            # 删除日志
            public.ExecShell("rm -f " + public.GetConfigValue('logs_path') + '/' + siteName + "-*")

            # 删除根目录
            if 'path' in get:
                if get.path == '1':
                    import files
                    get.path = self.__get_site_format_path(public.M('sites').where("id=?", (id,)).getField('path'))
                    if self.__check_site_path(get.path):
                        if public.M('sites').where("path=?", (get.path,)).count() < 2:
                            files.files().DeleteDir(get)
                    get.path = '1'

            # 重载配置
            if not multiple:
                public.serviceReload()

            # 从数据库删除
            public.M('sites').where("id=?", (id,)).delete()
            public.M('binding').where("pid=?", (id,)).delete()
            public.M('domain').where("pid=?", (id,)).delete()
            public.WriteLog('TYPE_SITE', "SITE_DEL_SUCCESS", (siteName,))
            try:
                # 检查站点是否存在
                site_exists = dp.sql('dk_sites').where('name=?', (siteName,)).find()
                # 如果站点存在，执行删除操作
                if site_exists:
                    proxy_info = dp.sql('dk_sites').where('name=?', (siteName,)).delete()
                else:
                    print("站点不存在，跳过删除操作")
            except Exception as e:
                print(e)
            return public.returnMsg(True, 'SITE_DEL_SUCCESS')
        except Exception as e:
            pass
            
    # 添加域名
    def AddDomain(self, get, multiple=None):
        # 检查配置文件
        isError = public.checkWebConfig()
        if isError != True:
            return public.returnMsg(False, 'ERROR: 检测到配置文件有错误,请先排除后再操作<br><br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')

        if not 'domain' in get: return public.returnMsg(False, '请填写域名!')
        if len(get.domain) < 3: return public.returnMsg(False, 'SITE_ADD_DOMAIN_ERR_EMPTY')
        domains = get.domain.replace(' ', '').split(',')

        res_domains = []
        for domain in domains:
            if domain == "": continue
            domain = domain.strip().split(':')
            get.domain = self.ToPunycode(domain[0]).lower()
            get.port = '80'
            # 判断通配符域名格式
            if get.domain.find('*') != -1 and get.domain.find('*.') == -1:
                res_domains.append({"name": get.domain, "status": False, "msg": '域名格式不正确'})
                continue

            # 判断域名格式
            reg = "^([\w\-\*]{1,100}\.){1,24}([\w\-]{1,24}|[\w\-]{1,24}\.[\w\-]{1,24})$"
            if not re.match(reg, get.domain):
                res_domains.append({"name": get.domain, "status": False, "msg": '域名格式不正确'})
                continue

            # 获取自定义端口
            if len(domain) == 2:
                get.port = domain[1]
            if get.port == "": get.port = "80"

            # 判断端口是否合法
            if not re.match("^\d+$", get.port):
                res_domains.append({"name": get.domain, "status": False, "msg": '端口不合法，应该为数字'})
                continue
            not_used_ports = ('21', '25', '443', '888', '8888', '8443')
            if get.port in not_used_ports:
                res_domains.append({"name": get.domain, "status": False, "msg": '端口不合法，请勿使用常用端口，例如：ssh的22端口等'})
                continue
            intport = int(get.port)
            if intport < 1 or intport > 65535:
                res_domains.append({"name": get.domain, "status": False, "msg": '端口范围不合法'})
                continue

            # 检查域名是否存在
            sql = public.M('domain')
            opid = sql.where("name=? AND (port=? OR pid=?)", (get.domain, get.port, get.id)).getField('pid')
            if opid:
                siteName = public.M('sites').where('id=?', (opid,)).getField('name')
                if siteName:
                    res_domains.append({"name": get.domain, "status": False, "msg": '指定域名[{}]已被网站[{}]绑定过了'.format(get.domain, siteName)})
                    continue
                sql.where('pid=?', (opid,)).delete()

            # 检查是否被子目录绑定
            opid = public.M('binding').where('domain=?', (get.domain,)).getField('pid')
            if opid:
                siteName = public.M('sites').where('id=?', (opid,)).getField('name')
                res_domains.append({"name": get.domain, "status": False, "msg": '指定域名[{}]已被被网站[{}]的子目录绑定过了!'.format(get.domain, siteName)})
                continue

            # 写配置文件
            self.NginxDomain(get)
            try:
                self.ApacheDomain(get)
                self.openlitespeed_domain(get)
                if self._check_ols_ssl(get.webname):
                    get.port = '443'
                    self.openlitespeed_domain(get)
                    get.port = '80'
            except:
                pass

            # 检查实际端口
            if len(domain) == 2: get.port = domain[1]

            # 添加放行端口
            if get.port != '80':
                import firewalls
                get.ps = get.domain
                firewalls.firewalls().AddAcceptPort(get)

            # 重载webserver服务
            if not multiple:
                public.serviceReload()
            full_domain = get.domain
            if not get.port in ['80', '443']: full_domain += ':' + get.port
            public.check_domain_cloud(full_domain)
            public.WriteLog('TYPE_SITE', 'DOMAIN_ADD_SUCCESS', (get.webname, get.domain))
            sql.table('domain').add('pid,name,port,addtime', (get.id, get.domain, get.port, public.getDate()))
            res_domains.append({"name": get.domain, "status": True, "msg": '添加成功'})

        return self._ckeck_add_domain(get.webname, res_domains)

    # 判断ols_ssl是否已经设置
    def _check_ols_ssl(self, webname):
        conf = public.readFile('/www/server/panel/vhost/openlitespeed/listen/443.conf')
        if conf and webname in conf:
            return True
        return False

    # openlitespeed写域名配置
    def openlitespeed_domain(self, get):
        listen_dir = '/www/server/panel/vhost/openlitespeed/listen/'
        if not os.path.exists(listen_dir):
            os.makedirs(listen_dir)
        listen_file = listen_dir + get.port + ".conf"
        listen_conf = public.readFile(listen_file)
        try:
            get.webname = json.loads(get.webname)
            get.domain = get.webname['domain'].replace('\r', '')
            get.webname = get.domain + "," + ",".join(get.webname["domainlist"])
            if get.webname[-1] == ',':
                get.webname = get.webname[:-1]
        except:
            pass

        if listen_conf:
            # 添加域名
            rep = 'map\s+{}.*'.format(get.webname)
            map_tmp = re.search(rep, listen_conf)
            if map_tmp:
                map_tmp = map_tmp.group()
                domains = map_tmp.strip().split(',')
                if not public.inArray(domains, get.domain):
                    new_map = '{},{}'.format(map_tmp, get.domain)
                    listen_conf = re.sub(rep, new_map, listen_conf)
            else:
                domains = get.webname.strip().split(',')
                map_tmp = '\tmap\t{d} {d}'.format(d=domains[0])
                listen_rep = "secure\s*0"
                listen_conf = re.sub(listen_rep, "secure 0\n" + map_tmp, listen_conf)
        else:
            listen_conf = """
listener Default%s{
    address *:%s
    secure 0
    map %s %s
}
""" % (get.port, get.port, get.webname, get.domain)
        # 保存配置文件
        public.writeFile(listen_file, listen_conf)
        return True

    # 是否跳转到https
    def IsToHttps(self, siteName):
        file = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/node_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/java_' + siteName + '.conf'

        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/go_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/other_' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/python_' + siteName + '.conf'

        conf = public.readFile(file)
        if conf:
            if conf.find('HTTP_TO_HTTPS_START') != -1: return True
            if conf.find('$server_port !~ 443') != -1: return True
        return False


    def get_site_push_status(self, get, siteName=None, stype=None):
        """
        @获取网站ssl告警通知状态
        @param get:
        @param siteName 网站名称
        @param stype 类型 ssl
        """
        import panelPush
        if get:
            siteName = get.siteName
            stype = get.stype

        result = {}
        result['status'] = False
        try:
            data = {}
            try:
                data = json.loads(public.readFile('{}/class/push/push.json'.format(public.get_panel_path())))
            except:
                pass

            if not 'site_push' in data:
                return result

            ssl_data = data['site_push']
            for key in ssl_data.keys():
                if ssl_data[key]['type'] != stype:
                    continue

                project = ssl_data[key]['project']
                if project in [siteName, 'all']:
                    ssl_data[key]['id'] = key
                    ssl_data[key]['s_module'] = 'site_push'

                    if project == siteName:
                        result = ssl_data[key]
                        break

                    if project == 'all':
                        result = ssl_data[key]
        except:
            pass

        p_obj = panelPush.panelPush()
        return p_obj.get_push_user(result)

    def _ckeck_add_domain(self, site_name, domains):
        from panelSite import panelSite
        ssl_data = panelSite().GetSSL(type("get", tuple(), {"siteName": site_name})())
        if not ssl_data["status"] or not ssl_data.get("cert_data", {}).get("dns", None):
            return {"domains": domains}
        domain_rep = []
        for i in ssl_data["cert_data"]["dns"]:
            if i.startswith("*"):
                _rep = "^[^\.]+\." + i[2:].replace(".", "\.")
            else:
                _rep = "^" + i.replace(".", "\.")
            domain_rep.append(_rep)
        no_ssl = []
        for domain in domains:
            if not domain["status"]: continue
            for _rep in domain_rep:
                if re.search(_rep, domain["name"]):
                    break
            else:
                no_ssl.append(domain["name"])
        if no_ssl:
            return {
                "domains": domains,
                "not_ssl": no_ssl,
                "tip": "本站点已启用SSL证书,但本次添加的域名：{}，无法匹配当前证书，如有需求，请重新申请证书。".format(str(no_ssl))
            }
        return {"domains": domains}

    # 检查伪静态、主配置文件是否有location冲突
    def CheckLocation(self, get):
        # 伪静态文件路径
        rewriteconfpath = "%s/panel/vhost/rewrite/%s.conf" % (self.setupPath, get.sitename)
        # 主配置文件路径
        nginxconfpath = "%s/nginx/conf/nginx.conf" % (self.setupPath)
        # vhost文件
        vhostpath = "%s/panel/vhost/nginx/%s.conf" % (self.setupPath, get.sitename)

        rep = "location\s+/[\n\s]+{"

        for i in [nginxconfpath, vhostpath]:
            conf = public.readFile(i)
            if re.findall(rep, conf):
                return public.returnMsg(False, '伪静态/nginx主配置/vhost/文件已经存在全局反向代理')

    # 读配置
    def __read_config(self, path):
        if not os.path.exists(path):
            public.writeFile(path, '[]')
        upBody = public.readFile(path)
        if not upBody: upBody = '[]'
        return json.loads(upBody)

    # 写配置
    def __write_config(self, path, data):
        return public.writeFile(path, json.dumps(data))

    # 设置OLS
    def _set_ols_proxy(self, get):
        # 添加反代配置
        proxyname_md5 = self.__calc_md5(get.proxyname)
        dir_path = "%s/panel/vhost/openlitespeed/proxy/%s/" % (self.setupPath, get.sitename)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        file_path = "{}{}_{}.conf".format(dir_path, proxyname_md5, get.sitename)
        reverse_proxy_conf = """
extprocessor %s {
  type                    proxy
  address                 %s
  maxConns                1000
  pcKeepAliveTimeout      600
  initTimeout             600
  retryTimeout            0
  respBuffer              0
}
""" % (get.proxyname, get.proxysite)
        public.writeFile(file_path, reverse_proxy_conf)
        # 添加urlrewrite
        dir_path = "%s/panel/vhost/openlitespeed/proxy/%s/urlrewrite/" % (self.setupPath, get.sitename)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        file_path = "{}{}_{}.conf".format(dir_path, proxyname_md5, get.sitename)
        reverse_urlrewrite_conf = """
RewriteRule ^%s(.*)$ http://%s/$1 [P,E=Proxy-Host:%s]
""" % (get.proxydir, get.proxyname, get.todomain)
        public.writeFile(file_path, reverse_urlrewrite_conf)

    # 设置Nginx配置
    def SetNginx(self, get):
        ng_proxyfile = "%s/panel/vhost/nginx/proxy/%s/*.conf" % (self.setupPath, get.sitename)
        ng_file = self.setupPath + "/panel/vhost/nginx/" + get.sitename + ".conf"
        p_conf = self.__read_config(self.__proxyfile)
        cureCache = ''

        if public.get_webserver() == 'nginx':
            shutil.copyfile(ng_file, '/tmp/ng_file_bk.conf')

        cureCache += '''
       location ~ /purge(/.*) {
           proxy_cache_purge cache_one $host$1$is_args$args;
           #access_log  /www/wwwlogs/%s_purge_cache.log;
       }''' % (get.sitename)
        if os.path.exists(ng_file):
            self.CheckProxy(get)
            ng_conf = public.readFile(ng_file)
            if not p_conf:
                rep = "#清理缓存规则[\w\s\~\/\(\)\.\*\{\}\;\$\n\#]+.*\n.*"
                ng_conf = re.sub(rep, '', ng_conf)
                oldconf = '''location ~ .*\\.(gif|jpg|jpeg|png|bmp|swf)$
       {
           expires      30d;
           error_log /dev/null;
           access_log /dev/null;
       }
       location ~ .*\\.(js|css)?$
       {
           expires      12h;
           error_log /dev/null;
           access_log /dev/null;
       }'''
                if "(gif|jpg|jpeg|png|bmp|swf)$" not in ng_conf:
                    ng_conf = re.sub('access_log\s*/www', oldconf + "\n\taccess_log  /www", ng_conf)
                public.writeFile(ng_file, ng_conf)
                return
            sitenamelist = []
            for i in p_conf:
                sitenamelist.append(i["sitename"])

            if get.sitename in sitenamelist:
                rep = "include.*\/proxy\/.*\*.conf;"
                if not re.search(rep, ng_conf):
                    rep = "location.+\(gif[\w\|\$\(\)\n\{\}\s\;\/\~\.\*\\\\\?]+access_log\s+/"
                    ng_conf = re.sub(rep, 'access_log  /', ng_conf)
                    ng_conf = ng_conf.replace("include enable-php-",
                                              "#清理缓存规则\n" + cureCache + "\n\t#引用反向代理规则，注释后配置的反向代理将无效\n\t" + "include " + ng_proxyfile + ";\n\n\tinclude enable-php-")
                    public.writeFile(ng_file, ng_conf)

            else:
                rep = "#清理缓存规则[\w\s\~\/\(\)\.\*\{\}\;\$\n\#]+.*\n.*"
                ng_conf = re.sub(rep, '', ng_conf)
                oldconf = '''location ~ .*\\.(gif|jpg|jpeg|png|bmp|swf)$
       {
           expires      30d;
           error_log /dev/null;
           access_log /dev/null;
       }
       location ~ .*\\.(js|css)?$
       {
           expires      12h;
           error_log /dev/null;
           access_log /dev/null;
       }'''
                if "(gif|jpg|jpeg|png|bmp|swf)$" not in ng_conf:
                    ng_conf = re.sub('access_log\s*/www', oldconf + "\n\taccess_log  /www", ng_conf)
                public.writeFile(ng_file, ng_conf)

    # 设置apache配置
    def SetApache(self, sitename):
        ap_proxyfile = "%s/panel/vhost/apache/proxy/%s/*.conf" % (self.setupPath, sitename)
        ap_file = self.setupPath + "/panel/vhost/apache/" + sitename + ".conf"
        p_conf = public.readFile(self.__proxyfile)

        if public.get_webserver() == 'apache':
            shutil.copyfile(ap_file, '/tmp/ap_file_bk.conf')

        if os.path.exists(ap_file):
            ap_conf = public.readFile(ap_file)
            if p_conf == "[]":
                rep = "\n*#引用反向代理规则，注释后配置的反向代理将无效\n+\s+IncludeOptiona[\s\w\/\.\*]+"
                ap_conf = re.sub(rep, '', ap_conf)
                public.writeFile(ap_file, ap_conf)
                return
            if sitename in p_conf:
                rep = "combined(\n|.)+IncludeOptional.*\/proxy\/.*conf"
                rep1 = "combined"
                if not re.search(rep, ap_conf):
                    ap_conf = ap_conf.replace(rep1, rep1 + "\n\t#引用反向代理规则，注释后配置的反向代理将无效\n\t" + "\n\tIncludeOptional " + ap_proxyfile)
                    public.writeFile(ap_file, ap_conf)
            else:
                # rep = "\n*#引用反向代理(\n|.)+IncludeOptional.*\/proxy\/.*conf"
                rep = "\n*#引用反向代理规则，注释后配置的反向代理将无效\n+\s+IncludeOptiona[\s\w\/\.\*]+"
                ap_conf = re.sub(rep, '', ap_conf)
                public.writeFile(ap_file, ap_conf)

    # 设置指定站点的PHP版本
    def SetPHPVersion(self, get, multiple=None):
        siteName = get.siteName
        version = get.version
        if version == 'other' and not public.get_webserver() in ['nginx', 'tengine']:
            return public.returnMsg(False, '自定义PHP配置只支持Nginx')
        try:
            # nginx
            file = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
            conf = public.readFile(file)
            if conf:
                other_path = '/www/server/panel/vhost/other_php/{}'.format(siteName)
                if not os.path.exists(other_path): os.makedirs(other_path)
                other_rep = "{}/enable-php-other.conf".format(other_path)

                if version == 'other':
                    dst = other_rep
                    get.other = get.other.strip()

                    if not get.other:
                        return public.returnMsg(False, '自定义版本时PHP连接配置不能为空!')

                    if not re.match(r"^(\d+\.\d+\.\d+\.\d+:\d+|unix:[\w/\.-]+)$", get.other):
                        return public.returnMsg(False, 'PHP连接配置格式不正确，请参考示例!')

                    other_tmp = get.other.split(':')
                    if other_tmp[0] == 'unix':
                        if not os.path.exists(other_tmp[1]):
                            return public.returnMsg(False, '指定unix套接字[{}]不存在，请核实!'.format(other_tmp[1]))
                    else:
                        if not public.check_tcp(other_tmp[0], int(other_tmp[1])):
                            return public.returnMsg(False, '无法连接[{}],请排查本机是否可连接目标服务器'.format(get.other))

                    other_conf = '''location ~ [^/]\.php(/|$)
{{
    try_files $uri =404;
    fastcgi_pass  {};
    fastcgi_index index.php;
    include fastcgi.conf;
    include pathinfo.conf;
}}'''.format(get.other)
                    public.writeFile(other_rep, other_conf)
                    conf = conf.replace(other_rep, dst)
                    rep = "include\s+enable-php-(\w{2,5})\.conf"
                    tmp = re.search(rep, conf)
                    if tmp: conf = conf.replace(tmp.group(), 'include ' + dst)
                else:
                    dst = 'enable-php-' + version + '.conf'
                    conf = conf.replace(other_rep, dst)
                    rep = "enable-php-(\w{2,5})\.conf"
                    tmp = re.search(rep, conf)
                    if tmp: conf = conf.replace(tmp.group(), dst)

                public.writeFile(file, conf)
                try:
                    import site_dir_auth
                    site_dir_auth_module = site_dir_auth.SiteDirAuth()
                    auth_list = site_dir_auth_module.get_dir_auth(get)
                    if auth_list:
                        for i in auth_list[siteName]:
                            auth_name = i['name']
                            auth_file = "{setup_path}/panel/vhost/nginx/dir_auth/{site_name}/{auth_name}.conf".format(
                                setup_path=self.setupPath, site_name=siteName, auth_name=auth_name)
                            if os.path.exists(auth_file):
                                site_dir_auth_module.change_dir_auth_file_nginx_phpver(siteName, version, auth_name)
                except:
                    pass

            # apache
            file = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
            conf = public.readFile(file)
            if conf and version != 'other':
                rep = "(unix:/tmp/php-cgi-(\w{2,5})\.sock\|fcgi://localhost|fcgi://127.0.0.1:\d+)"
                tmp = re.search(rep, conf).group()
                conf = conf.replace(tmp, public.get_php_proxy(version, 'apache'))
                public.writeFile(file, conf)
            # OLS
            if version != 'other':
                file = self.setupPath + '/panel/vhost/openlitespeed/detail/' + siteName + '.conf'
                conf = public.readFile(file)
                if conf:
                    rep = 'lsphp\d+'
                    tmp = re.search(rep, conf)
                    if tmp:
                        conf = conf.replace(tmp.group(), 'lsphp' + version)
                        public.writeFile(file, conf)
            if not multiple:
                public.serviceReload()
            public.WriteLog("TYPE_SITE", "SITE_PHPVERSION_SUCCESS", (siteName, version))
            return public.returnMsg(True, 'SITE_PHPVERSION_SUCCESS', (siteName, version))
        except:
            return public.get_error_info()
            return public.returnMsg(False, '设置失败，没有在网站配置文件中找到enable-php-xx相关配置项!')

    # 创建反向代理
    def CreateProxy(self, get):
        try:
            try:
                nocheck = get.nocheck
            except:
                nocheck = ""
            if not get.get('proxysite', None):
                return public.returnMsg(False, '目标URL不能为空')
            if not nocheck:
                if self.__CheckStart(get, "create"):
                    return self.__CheckStart(get, "create")
            if public.get_webserver() == 'nginx':
                if self.CheckLocation(get):
                    return self.CheckLocation(get)
            if not get.proxysite.split('//')[-1]:
                return public.returnMsg(False, '目标URL不能为[http://或https://],请填写完整URL，如：https://www.bt.cn')
            proxyUrl = self.__read_config(self.__proxyfile)
            proxyUrl.append({
                "proxyname": get.proxyname,
                "sitename": get.sitename,
                "proxydir": get.proxydir,
                "proxysite": get.proxysite,
                "todomain": get.todomain,
                "type": int(get.type),
                "cache": int(get.cache),
                "subfilter": json.loads(get.subfilter),
                "advanced": int(get.advanced),
                "cachetime": int(get.cachetime)
            })
            self.__write_config(self.__proxyfile, proxyUrl)
            self.SetNginx(get)
            self.SetApache(get.sitename)
            self._set_ols_proxy(get)
            status = self.SetProxy(get)
            if not status["status"]:
                return status
            if get.proxydir == '/':
                get.version = '00'
                get.siteName = get.sitename
                self.SetPHPVersion(get)
            public.serviceReload()
            return public.returnMsg(True, '添加成功')
        except Exception as e:
            pass
    # 设置反向代理
    def SetProxy(self, get):
        sitename = get.sitename  # 站点名称
        advanced = int(get.advanced)
        type = int(get.type)
        cache = int(get.cache)
        cachetime = int(get.cachetime)
        proxysite = get.proxysite
        proxydir = get.proxydir
        ng_file = self.setupPath + "/panel/vhost/nginx/" + sitename + ".conf"
        ap_file = self.setupPath + "/panel/vhost/apache/" + sitename + ".conf"
        p_conf = self.__read_config(self.__proxyfile)
        random_string = public.GetRandomString(8)

        # websocket前置map
        map_file = self.setupPath + "/panel/vhost/nginx/0.websocket.conf"
        if not os.path.exists(map_file):
            map_body = '''map $http_upgrade $connection_upgrade {
    default upgrade;
    ''  close;
}
'''
            public.writeFile(map_file, map_body)

        # 配置Nginx
        # 构造清理缓存连接
        # 构造缓存配置
        ng_cache = """
    if ( $uri ~* "\.(gif|png|jpg|css|js|woff|woff2)$" )
    {
        expires 1m;
    }
    proxy_ignore_headers Set-Cookie Cache-Control expires;
    proxy_cache cache_one;
    proxy_cache_key $host$uri$is_args$args;
    proxy_cache_valid 200 304 301 302 %sm;""" % (cachetime)
        no_cache = """
    set $static_file%s 0;
    if ( $uri ~* "\.(gif|png|jpg|css|js|woff|woff2)$" )
    {
        set $static_file%s 1;
        expires 1m;
        }
    if ( $static_file%s = 0 )
    {
    add_header Cache-Control no-cache;
    }""" % (random_string, random_string, random_string)
        ng_proxy = '''
#PROXY-START%s

location ^~ %s
{
    proxy_pass %s;
    proxy_set_header Host %s;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header REMOTE-HOST $remote_addr;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
    proxy_http_version 1.1;
    # proxy_hide_header Upgrade;

    add_header X-Cache $upstream_cache_status;

    #Set Nginx Cache
    %s
    %s
}

#PROXY-END%s'''
        ng_proxy_cache = ''
        proxyname_md5 = self.__calc_md5(get.proxyname)
        ng_proxyfile = "%s/panel/vhost/nginx/proxy/%s/%s_%s.conf" % (self.setupPath, sitename, proxyname_md5, sitename)
        ng_proxydir = "%s/panel/vhost/nginx/proxy/%s" % (self.setupPath, sitename)
        if not os.path.exists(ng_proxydir):
            public.ExecShell("mkdir -p %s" % ng_proxydir)

        # 构造替换字符串
        ng_subdata = ''
        ng_sub_filter = '''
    proxy_set_header Accept-Encoding "";%s
    sub_filter_once off;'''
        if get.subfilter:
            for s in json.loads(get.subfilter):
                if not s["sub1"]:
                    continue
                if '"' in s["sub1"]:
                    s["sub1"] = s["sub1"].replace('"', '\\"')
                if '"' in s["sub2"]:
                    s["sub2"] = s["sub2"].replace('"', '\\"')
                ng_subdata += '\n\tsub_filter "%s" "%s";' % (s["sub1"], s["sub2"])
        if ng_subdata:
            ng_sub_filter = ng_sub_filter % (ng_subdata)
        else:
            ng_sub_filter = ''

        if advanced == 1:
            if proxydir[-1] != '/':
                proxydir = '{}/'.format(proxydir)
            if proxysite[-1] != '/':
                proxysite = '{}/'.format(proxysite)
            if type == 1 and cache == 1:
                ng_proxy_cache += ng_proxy % (
                    proxydir, proxydir, proxysite, get.todomain, ng_sub_filter, ng_cache, get.proxydir)
            if type == 1 and cache == 0:
                ng_proxy_cache += ng_proxy % (
                    get.proxydir, get.proxydir, proxysite, get.todomain, ng_sub_filter, no_cache, get.proxydir)
        else:
            if type == 1 and cache == 1:
                ng_proxy_cache += ng_proxy % (
                    get.proxydir, get.proxydir, get.proxysite, get.todomain, ng_sub_filter, ng_cache, get.proxydir)
            if type == 1 and cache == 0:
                ng_proxy_cache += ng_proxy % (
                    get.proxydir, get.proxydir, get.proxysite, get.todomain, ng_sub_filter, no_cache, get.proxydir)
        public.writeFile(ng_proxyfile, ng_proxy_cache)

        # APACHE
        # 反向代理文件
        ap_proxyfile = "%s/panel/vhost/apache/proxy/%s/%s_%s.conf" % (self.setupPath, get.sitename, proxyname_md5, get.sitename)
        ap_proxydir = "%s/panel/vhost/apache/proxy/%s" % (self.setupPath, get.sitename)
        if not os.path.exists(ap_proxydir):
            public.ExecShell("mkdir -p %s" % ap_proxydir)
        ap_proxy = ''
        if type == 1:
            ap_proxy += '''#PROXY-START%s
<IfModule mod_proxy.c>
    ProxyRequests Off
    SSLProxyEngine on
    ProxyPass %s %s/
    ProxyPassReverse %s %s/
    </IfModule>
#PROXY-END%s''' % (get.proxydir, get.proxydir, get.proxysite, get.proxydir,
                   get.proxysite, get.proxydir)
        public.writeFile(ap_proxyfile, ap_proxy)
        isError = public.checkWebConfig()
        if (isError != True):
            if public.get_webserver() == "nginx":
                shutil.copyfile('/tmp/ng_file_bk.conf', ng_file)
            else:
                shutil.copyfile('/tmp/ap_file_bk.conf', ap_file)
            for i in range(len(p_conf) - 1, -1, -1):
                if get.sitename == p_conf[i]["sitename"] and p_conf[i]["proxyname"]:
                    del p_conf[i]
            self.RemoveProxy(get)
            return public.returnMsg(False, 'ERROR: %s<br><a style="color:red;">' % public.GetMsg("CONFIG_ERROR") + isError.replace("\n",
                                                                                                                                   '<br>') + '</a>')
        return public.returnMsg(True, 'SUCCESS')

    # 取代理配置文件
    def GetProxyFile(self, get):
        import files
        conf = self.__read_config(self.__proxyfile)
        sitename = get.sitename
        proxyname = get.proxyname
        proxyname_md5 = self.__calc_md5(proxyname)
        get.path = "%s/panel/vhost/%s/proxy/%s/%s_%s.conf" % (self.setupPath, get.webserver, sitename, proxyname_md5, sitename)
        for i in conf:
            if proxyname == i["proxyname"] and sitename == i["sitename"] and i["type"] != 1:
                return public.returnMsg(False, '代理已暂停')
        f = files.files()
        return f.GetFileBody(get), get.path

    # Nginx写域名配置
    def NginxDomain(self, get):
        file = self.setupPath + '/panel/vhost/nginx/' + get.webname + '.conf'
        conf = public.readFile(file)
        if not conf: return

        # 添加域名
        rep = r"server_name\s*(.*);"
        tmp = re.search(rep, conf).group()
        domains = tmp.replace(';', '').strip().split(' ')
        if not public.inArray(domains, get.domain):
            newServerName = tmp.replace(';', ' ' + get.domain + ';')
            conf = conf.replace(tmp, newServerName)

        # 添加端口
        rep = r"listen\s+[\[\]\:]*([0-9]+).*;"
        tmp = re.findall(rep, conf)
        if not public.inArray(tmp, get.port):
            listen = re.search(rep, conf).group()
            listen_ipv6 = ''
            if self.is_ipv6: listen_ipv6 = "\n\t\tlisten [::]:" + get.port + ';'
            conf = conf.replace(listen, listen + "\n\t\tlisten " + get.port + ';' + listen_ipv6)
        # 保存配置文件
        public.writeFile(file, conf)
        return True

    # Apache写域名配置
    def ApacheDomain(self, get):
        file = self.setupPath + '/panel/vhost/apache/' + get.webname + '.conf'
        conf = public.readFile(file)
        if not conf: return

        port = get.port
        siteName = get.webname
        newDomain = get.domain
        find = public.M('sites').where("id=?", (get.id,)).field('id,name,path').find()
        sitePath = find['path']
        siteIndex = 'index.php index.html index.htm default.php default.html default.htm'

        # 添加域名
        if conf.find('<VirtualHost *:' + port + '>') != -1:
            repV = r"<VirtualHost\s+\*\:" + port + ">(.|\n)*</VirtualHost>"
            domainV = re.search(repV, conf).group()
            rep = r"ServerAlias\s*(.*)\n"
            tmp = re.search(rep, domainV).group(0)
            domains = tmp.strip().split(' ')
            if not public.inArray(domains, newDomain):
                rs = tmp.replace("\n", "")
                newServerName = rs + ' ' + newDomain + "\n"
                myconf = domainV.replace(tmp, newServerName)
                conf = re.sub(repV, myconf, conf)
            if conf.find('<VirtualHost *:443>') != -1:
                repV = r"<VirtualHost\s+\*\:443>(.|\n)*</VirtualHost>"
                domainV = re.search(repV, conf).group()
                rep = r"ServerAlias\s*(.*)\n"
                tmp = re.search(rep, domainV).group(0)
                domains = tmp.strip().split(' ')
                if not public.inArray(domains, newDomain):
                    rs = tmp.replace("\n", "")
                    newServerName = rs + ' ' + newDomain + "\n"
                    myconf = domainV.replace(tmp, newServerName)
                    conf = re.sub(repV, myconf, conf)
        else:
            try:
                httpdVersion = public.readFile(self.setupPath + '/apache/version.pl').strip()
            except:
                httpdVersion = ""
            if httpdVersion == '2.2':
                vName = ''
                if self.sitePort != '80' and self.sitePort != '443':
                    vName = "NameVirtualHost  *:" + port + "\n"
                phpConfig = ""
                apaOpt = "Order allow,deny\n\t\tAllow from all"
            else:
                vName = ""
                # rep = "php-cgi-([0-9]{2,3})\.sock"
                # version = re.search(rep,conf).groups()[0]
                version = public.get_php_version_conf(conf)
                if len(version) < 2: return public.returnMsg(False, 'PHP_GET_ERR')
                phpConfig = '''
    #PHP
    <FilesMatch \\.php$>
            SetHandler "proxy:%s"
    </FilesMatch>
    ''' % (public.get_php_proxy(version, 'apache'),)
                apaOpt = 'Require all granted'

            newconf = '''<VirtualHost *:%s>
    ServerAdmin webmaster@example.com
    DocumentRoot "%s"
    ServerName %s.%s
    ServerAlias %s
    #errorDocument 404 /404.html
    ErrorLog "%s-error_log"
    CustomLog "%s-access_log" combined
    %s

    #DENY FILES
     <Files ~ (\.user.ini|\.htaccess|\.git|\.env|\.svn|\.project|LICENSE|README.md)$>
       Order allow,deny
       Deny from all
    </Files>

    #PATH
    <Directory "%s">
        SetOutputFilter DEFLATE
        Options FollowSymLinks
        AllowOverride All
        %s
        DirectoryIndex %s
    </Directory>
</VirtualHost>''' % (
                port, sitePath, siteName, port, newDomain, public.GetConfigValue('logs_path') + '/' + siteName, public.GetConfigValue('logs_path') + '/' + siteName, phpConfig, sitePath, apaOpt,
                siteIndex)
            conf += "\n\n" + newconf

        # 添加端口
        if port != '80' and port != '888': self.apacheAddPort(port)

        # 保存配置文件
        public.writeFile(file, conf)
        return True


    # 保存代理配置文件
    def SaveProxyFile(self, get):
        import files
        f = files.files()
        return f.SaveFileBody(get)

    # 检查是否存在#Set Nginx Cache
    def check_annotate(self, data):
        rep = "\n\s*#Set\s*Nginx\s*Cache"
        if re.search(rep, data):
            return True

    def old_proxy_conf(self, conf, ng_conf_file, get):
        rep = 'location\s*\~\*.*gif\|png\|jpg\|css\|js\|woff\|woff2\)\$'
        if not re.search(rep, conf):
            return conf
        self.RemoveProxy(get)
        self.CreateProxy(get)
        return public.readFile(ng_conf_file)

    # 修改反向代理
    def ModifyProxy(self, get):
        if not get.get('proxysite', None):
            return public.returnMsg(False, '目标URL不能为空')
        proxyname_md5 = self.__calc_md5(get.proxyname)
        ap_conf_file = "{p}/panel/vhost/apache/proxy/{s}/{n}_{s}.conf".format(
            p=self.setupPath, s=get.sitename, n=proxyname_md5)
        ng_conf_file = "{p}/panel/vhost/nginx/proxy/{s}/{n}_{s}.conf".format(
            p=self.setupPath, s=get.sitename, n=proxyname_md5)
        ols_conf_file = "{p}/panel/vhost/openlitespeed/proxy/{s}/urlrewrite/{n}_{s}.conf".format(
            p=self.setupPath, s=get.sitename, n=proxyname_md5)
        if self.__CheckStart(get):
            return self.__CheckStart(get)
        conf = self.__read_config(self.__proxyfile)
        random_string = public.GetRandomString(8)

        for i in range(len(conf)):
            if conf[i]["proxyname"] == get.proxyname and conf[i]["sitename"] == get.sitename:
                if int(get.type) != 1:
                    if not os.path.exists(ng_conf_file):
                        return public.returnMsg(False, "请先开启反向代理后再编辑！")
                    public.ExecShell("mv {f} {f}_bak".format(f=ap_conf_file))
                    public.ExecShell("mv {f} {f}_bak".format(f=ng_conf_file))
                    public.ExecShell("mv {f} {f}_bak".format(f=ols_conf_file))
                    conf[i]["type"] = int(get.type)
                    self.__write_config(self.__proxyfile, conf)
                    public.serviceReload()
                    return public.returnMsg(True, '修改成功')
                else:
                    if os.path.exists(ap_conf_file + "_bak"):
                        public.ExecShell("mv {f}_bak {f}".format(f=ap_conf_file))
                        public.ExecShell("mv {f}_bak {f}".format(f=ng_conf_file))
                        public.ExecShell("mv {f}_bak {f}".format(f=ols_conf_file))
                    ng_conf = public.readFile(ng_conf_file)
                    ng_conf = self.old_proxy_conf(ng_conf, ng_conf_file, get)
                    # 修改nginx配置
                    # 如果代理URL后缀带有URI则删除URI，正则匹配不支持proxypass处带有uri
                    php_pass_proxy = get.proxysite
                    if get.proxysite[-1] == '/' or get.proxysite.count('/') > 2 or '?' in get.proxysite:
                        php_pass_proxy = re.search('(https?\:\/\/[\w\.]+)', get.proxysite).group(0)
                    # ng_conf = re.sub("location\s+%s" % conf[i]["proxydir"],"location "+get.proxydir,ng_conf)
                    ng_conf = re.sub("location\s+[\^\~]*\s?%s" % conf[i]["proxydir"], "location ^~ " + get.proxydir, ng_conf)
                    ng_conf = re.sub("proxy_pass\s+%s" % conf[i]["proxysite"], "proxy_pass " + get.proxysite, ng_conf)
                    ng_conf = re.sub("location\s+\~\*\s+\\\.\(php.*\n\{\s*proxy_pass\s+%s.*" % (php_pass_proxy),
                                     "location ~* \.(php|jsp|cgi|asp|aspx)$\n{\n\tproxy_pass %s;" % php_pass_proxy, ng_conf)
                    ng_conf = re.sub("location\s+\~\*\s+\\\.\(gif.*\n\{\s*proxy_pass\s+%s.*" % (php_pass_proxy),
                                     "location ~* \.(gif|png|jpg|css|js|woff|woff2)$\n{\n\tproxy_pass %s;" % php_pass_proxy, ng_conf)

                    backslash = ""
                    if "Host $host" in ng_conf:
                        backslash = "\\"

                    ng_conf = re.sub("\sHost\s+%s" % backslash + conf[i]["todomain"], " Host " + get.todomain, ng_conf)
                    cache_rep = r"proxy_cache_valid\s+200\s+304\s+301\s+302\s+\d+m;((\n|.)+expires\s+\d+m;)*"
                    if int(get.cache) == 1:
                        if re.search(cache_rep, ng_conf):
                            expires_rep = "\{\n\s+expires\s+12h;"
                            ng_conf = re.sub(expires_rep, "{", ng_conf)
                            ng_conf = re.sub(cache_rep, "proxy_cache_valid 200 304 301 302 {0}m;".format(get.cachetime), ng_conf)
                        else:
                            ng_cache = """
    if ( $uri ~* "\.(gif|png|jpg|css|js|woff|woff2)$" )
    {
        expires 1m;
    }
    proxy_ignore_headers Set-Cookie Cache-Control expires;
    proxy_cache cache_one;
    proxy_cache_key $host$uri$is_args$args;
    proxy_cache_valid 200 304 301 302 %sm;""" % (get.cachetime)
                            if self.check_annotate(ng_conf):
                                cache_rep = '\n\s*#Set\s*Nginx\s*Cache(.|\n)*no-cache;\s*\n*\s*\}'
                                ng_conf = re.sub(cache_rep, '\n\t\t#Set Nginx Cache\n' + ng_cache, ng_conf)
                            else:
                                cache_rep = r"proxy_set_header\s+REMOTE-HOST\s+\$remote_addr;"
                                ng_conf = re.sub(cache_rep, r"\n\t\tproxy_set_header\s+REMOTE-HOST\s+\$remote_addr;\n\t\t#Set Nginx Cache" + ng_cache,
                                                 ng_conf)
                    else:
                        no_cache = """
    #Set Nginx Cache
    set $static_file%s 0;
    if ( $uri ~* "\.(gif|png|jpg|css|js|woff|woff2)$" )
    {
        set $static_file%s 1;
        expires 1m;
    }
    if ( $static_file%s = 0 )
    {
        add_header Cache-Control no-cache;
    }
}
#PROXY-END/""" % (random_string, random_string, random_string)
                        if self.check_annotate(ng_conf):
                            rep = r'\n\s*#Set\s*Nginx\s*Cache(.|\n)*'

                            ng_conf = re.sub(rep, no_cache, ng_conf)
                        else:
                            rep = r"\s+proxy_cache\s+cache_one.*[\n\s\w\_\";\$]+m;"

                            ng_conf = re.sub(rep, no_cache, ng_conf)
                    sub_rep = "sub_filter"
                    subfilter = json.loads(get.subfilter)
                    if str(conf[i]["subfilter"]) != str(subfilter) or ng_conf.find('sub_filter_once') == -1:
                        if re.search(sub_rep, ng_conf):
                            sub_rep = "\s+proxy_set_header\s+Accept-Encoding(.|\n)+off;"
                            ng_conf = re.sub(sub_rep, "", ng_conf)

                        # 构造替换字符串
                        ng_subdata = ''
                        ng_sub_filter = '''
    proxy_set_header Accept-Encoding "";%s
    sub_filter_once off;'''
                        if subfilter:
                            for s in subfilter:
                                if not s["sub1"]:
                                    continue
                                if '"' in s["sub1"]:
                                    s["sub1"] = s["sub1"].replace('"', '\\"')
                                if '"' in s["sub2"]:
                                    s["sub2"] = s["sub2"].replace('"', '\\"')
                                ng_subdata += '\n\t\tsub_filter "%s" "%s";' % (s["sub1"], s["sub2"])
                        if ng_subdata:
                            ng_sub_filter = ng_sub_filter % (ng_subdata)
                        else:
                            ng_sub_filter = ''
                        sub_rep = '#Set\s+Nginx\s+Cache'
                        ng_conf = re.sub(sub_rep, '#Set Nginx Cache\n' + ng_sub_filter, ng_conf)

                    # 修改apache配置
                    ap_conf = public.readFile(ap_conf_file)
                    ap_conf = re.sub("ProxyPass\s+%s\s+%s" % (conf[i]["proxydir"], conf[i]["proxysite"]), "ProxyPass %s %s" % (get.proxydir, get.proxysite), ap_conf)
                    ap_conf = re.sub("ProxyPassReverse\s+%s\s+%s" % (conf[i]["proxydir"], conf[i]["proxysite"]),
                                     "ProxyPassReverse %s %s" % (get.proxydir, get.proxysite), ap_conf)
                    # 修改OLS配置
                    p = "{p}/panel/vhost/openlitespeed/proxy/{s}/{n}_{s}.conf".format(p=self.setupPath, n=proxyname_md5, s=get.sitename)
                    c = public.readFile(p)
                    if c:
                        rep = 'address\s+(.*)'
                        new_proxysite = 'address\t{}'.format(get.proxysite)
                        c = re.sub(rep, new_proxysite, c)
                        public.writeFile(p, c)

                    c = public.readFile(ols_conf_file)
                    if c:
                        rep = 'RewriteRule\s*\^{}\(\.\*\)\$\s+http://{}/\$1\s*\[P,E=Proxy-Host:{}\]'.format(conf[i]["proxydir"], get.proxyname, conf[i]["todomain"])
                        new_content = 'RewriteRule ^{}(.*)$ http://{}/$1 [P,E=Proxy-Host:{}]'.format(get.proxydir, get.proxyname, get.todomain)
                        c = re.sub(rep, new_content, c)
                        public.writeFile(ols_conf_file, c)

                    conf[i]["proxydir"] = get.proxydir
                    conf[i]["proxysite"] = get.proxysite
                    conf[i]["todomain"] = get.todomain
                    conf[i]["type"] = int(get.type)
                    conf[i]["cache"] = int(get.cache)
                    conf[i]["subfilter"] = json.loads(get.subfilter)
                    conf[i]["advanced"] = int(get.advanced)
                    conf[i]["cachetime"] = int(get.cachetime)

                    public.writeFile(ng_conf_file, ng_conf)
                    public.writeFile(ap_conf_file, ap_conf)
                    self.__write_config(self.__proxyfile, conf)
                    self.SetNginx(get)
                    self.SetApache(get.sitename)

                    public.serviceReload()
                    return public.returnMsg(True, '修改成功')

    # 清除多余user.ini
    def DelUserInI(self, path, up=0):
        useriniPath = path + '/.user.ini'
        if os.path.exists(useriniPath):
            public.ExecShell('chattr -i ' + useriniPath)
            try:
                os.remove(useriniPath)
            except:
                pass

        for p1 in os.listdir(path):
            try:
                npath = path + '/' + p1
                if not os.path.isdir(npath): continue
                useriniPath = npath + '/.user.ini'
                if os.path.exists(useriniPath):
                    public.ExecShell('chattr -i ' + useriniPath)
                    os.remove(useriniPath)
                if up < 3: self.DelUserInI(npath, up + 1)
            except:
                continue
        return True

    # 添加到nginx
    def nginxAdd(self):
        listen_ipv6 = ''
        if self.is_ipv6: listen_ipv6 = "\n    listen [::]:%s;" % self.sitePort

        conf = '''server
{{
    listen {listen_port};{listen_ipv6}
    server_name {site_name};
    index index.php index.html index.htm default.php default.htm default.html;
    root {site_path};
    #CERT-APPLY-CHECK--START
    # 用于SSL证书申请时的文件验证相关配置 -- 请勿删除
    include /www/server/panel/vhost/nginx/well-known/{site_name}.conf;
    #CERT-APPLY-CHECK--END

    #SSL-START {ssl_start_msg}
    #error_page 404/404.html;
    #SSL-END

    #ERROR-PAGE-START  {err_page_msg}
    #error_page 404 /404.html;
    #error_page 502 /502.html;
    #ERROR-PAGE-END

    #PHP-INFO-START  {php_info_start}
    include enable-php-{php_version}.conf;
    #PHP-INFO-END
    
    #REWRITE-START {rewrite_start_msg}
    include {setup_path}/panel/vhost/rewrite/{site_name}.conf;
    #REWRITE-END
    
    #IP-RESTRICT-START 限制访问ip的配置，IP黑白名单
    include {setup_path}/panel/vhost/ip-restrict/{site_name}.conf;
    #IP-RESTRICT-END
    
    #FILE-RESTRICT-START 限制访问文件类型的配置
    include {setup_path}/panel/vhost/file-restrict/{site_name}.conf;
    #FILE-RESTRICT-END
    
    #禁止访问的文件或目录
    location ~ ^/(\.user.ini|\.htaccess|\.git|\.env|\.svn|\.project|LICENSE|README.md)
    {{
        return 404;
    }}

    #一键申请SSL证书验证目录相关设置
    location ~ \.well-known{{
        allow all;
    }}

    #禁止在证书验证目录放入敏感文件
    if ( $uri ~ "^/\.well-known/.*\.(php|jsp|py|js|css|lua|ts|go|zip|tar\.gz|rar|7z|sql|bak)$" ) {{
        return 403;
    }}

    location ~ .*\\.(gif|jpg|jpeg|png|bmp|swf)$
    {{
        expires      30d;
        error_log /dev/null;
        access_log /dev/null;
    }}

    location ~ .*\\.(js|css)?$
    {{
        expires      12h;
        error_log /dev/null;
        access_log /dev/null;
    }}
    access_log  {log_path}/{site_name}.log;
    error_log  {log_path}/{site_name}.error.log;
}}'''.format(
            listen_port=self.sitePort,
            listen_ipv6=listen_ipv6,
            site_path=self.sitePath,
            ssl_start_msg=public.getMsg('NGINX_CONF_MSG1'),
            err_page_msg=public.getMsg('NGINX_CONF_MSG2'),
            php_info_start=public.getMsg('NGINX_CONF_MSG3'),
            php_version=self.phpVersion,
            setup_path=self.setupPath,
            rewrite_start_msg=public.getMsg('NGINX_CONF_MSG4'),
            log_path=public.GetConfigValue('logs_path'),
            site_name=self.siteName
        )

        # 写配置文件
        if not os.path.exists("/www/server/panel/vhost/nginx/well-known"):
            os.makedirs("/www/server/panel/vhost/nginx/well-known", 0o600)
        public.writeFile("/www/server/panel/vhost/nginx/well-known/{}.conf".format(self.siteName), "")
        filename = self.setupPath + '/panel/vhost/nginx/' + self.siteName + '.conf'
        public.writeFile(filename, conf)

        # 生成伪静态文件
        urlrewritePath = self.setupPath + '/panel/vhost/rewrite'
        urlrewriteFile = urlrewritePath + '/' + self.siteName + '.conf'
        if not os.path.exists(urlrewritePath):
            os.makedirs(urlrewritePath)
        open(urlrewriteFile, 'w+').close()

        # IP黑白名单
        ip_restrict_path = self.setupPath + '/panel/vhost/ip-restrict'
        ip_restrict_file = ip_restrict_path + '/' + self.siteName + '.conf'
        if not os.path.exists(ip_restrict_path):
            os.makedirs(ip_restrict_path)
        open(ip_restrict_file, 'w+').close()

        # 文件类型限制
        file_restrict_path = self.setupPath + '/panel/vhost/file-restrict'
        file_restrict_file = file_restrict_path + '/' + self.siteName + '.conf'
        if not os.path.exists(file_restrict_path):
            os.makedirs(file_restrict_path)
        open(file_restrict_file, 'w+').close()
        return True

    # 添加apache端口
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

    # 添加到apache
    def apacheAdd(self):
        import time
        listen = ''
        if self.sitePort != '80': self.apacheAddPort(self.sitePort)
        acc = public.md5(str(time.time()))[0:8]
        try:
            httpdVersion = public.readFile(self.setupPath + '/apache/version.pl').strip()
        except:
            httpdVersion = ""
        if httpdVersion == '2.2':
            vName = ''
            if self.sitePort != '80' and self.sitePort != '443':
                vName = "NameVirtualHost  *:" + self.sitePort + "\n"
            phpConfig = ""
            apaOpt = "Order allow,deny\n\t\tAllow from all"
        else:
            vName = ""
            phpConfig = '''
    #PHP
    <FilesMatch \\.php$>
            SetHandler "proxy:%s"
    </FilesMatch>
    ''' % (public.get_php_proxy(self.phpVersion, 'apache'),)
            apaOpt = 'Require all granted'

        conf = '''%s<VirtualHost *:%s>
    ServerAdmin webmaster@example.com
    DocumentRoot "%s"
    ServerName %s.%s
    ServerAlias %s
    #errorDocument 404 /404.html
    ErrorLog "%s-error_log"
    CustomLog "%s-access_log" combined

    #DENY FILES
     <Files ~ (\.user.ini|\.htaccess|\.git|\.env|\.svn|\.project|LICENSE|README.md)$>
       Order allow,deny
       Deny from all
    </Files>
    %s
    #PATH
    <Directory "%s">
        SetOutputFilter DEFLATE
        Options FollowSymLinks
        AllowOverride All
        %s
        DirectoryIndex index.php index.html index.htm default.php default.html default.htm
    </Directory>
</VirtualHost>''' % (
            vName, self.sitePort, self.sitePath, acc, self.siteName, self.siteName, public.GetConfigValue('logs_path') + '/' + self.siteName, public.GetConfigValue('logs_path') + '/' + self.siteName,
            phpConfig, self.sitePath, apaOpt)

        htaccess = self.sitePath + '/.htaccess'
        if not os.path.exists(htaccess): public.writeFile(htaccess, ' ')
        public.ExecShell('chmod -R 755 ' + htaccess)
        public.ExecShell('chown -R www:www ' + htaccess)

        filename = self.setupPath + '/panel/vhost/apache/' + self.siteName + '.conf'
        public.writeFile(filename, conf)
        return True

    # openlitespeed
    def openlitespeed_add_site(self, get, init_args=None):
        # 写主配置httpd_config.conf
        # 操作默认监听配置
        if not self.sitePath:
            return public.returnMsg(False, "Not specify parameter [sitePath]")
        if init_args:
            self.siteName = init_args['sitename']
            self.phpVersion = init_args['phpv']
            self.sitePath = init_args['rundir']
        conf_dir = self.setupPath + '/panel/vhost/openlitespeed/'
        if not os.path.exists(conf_dir):
            os.makedirs(conf_dir)
        file = conf_dir + self.siteName + '.conf'

        v_h = """
#VHOST_TYPE BT_SITENAME START
virtualhost BT_SITENAME {
vhRoot BT_RUN_PATH
configFile /www/server/panel/vhost/openlitespeed/detail/BT_SITENAME.conf
allowSymbolLink 1
enableScript 1
restrained 1
setUIDMode 0
}
#VHOST_TYPE BT_SITENAME END
"""
        self.old_name = self.siteName
        if hasattr(get, "dirName"):
            self.siteName = self.siteName + "_" + get.dirName
            # sub_dir = self.sitePath + "/" + get.dirName
            v_h = v_h.replace("VHOST_TYPE", "SUBDIR")
            v_h = v_h.replace("BT_SITENAME", self.siteName)
            v_h = v_h.replace("BT_RUN_PATH", self.sitePath)
            # extp_name = self.siteName + "_" + get.dirName
        else:
            self.openlitespeed_domain(get)
            v_h = v_h.replace("VHOST_TYPE", "VHOST")
            v_h = v_h.replace("BT_SITENAME", self.siteName)
            v_h = v_h.replace("BT_RUN_PATH", self.sitePath)
            # extp_name = self.siteName
        public.writeFile(file, v_h, "a+")
        # 写vhost
        conf = '''docRoot                   $VH_ROOT
vhDomain                  $VH_NAME
adminEmails               example@example.com
enableGzip                1
enableIpGeo               1

index  {
  useServer               0
  indexFiles index.php,index.html
}

errorlog /www/wwwlogs/$VH_NAME_ols.error_log {
  useServer               0
  logLevel                ERROR
  rollingSize             10M
}

accesslog /www/wwwlogs/$VH_NAME_ols.access_log {
  useServer               0
  logFormat               '%{X-Forwarded-For}i %h %l %u %t "%r" %>s %b "%{Referer}i" "%{User-Agent}i"'
  logHeaders              5
  rollingSize             10M
  keepDays                10  compressArchive         1
}

scripthandler  {
  add                     lsapi:BT_EXTP_NAME php
}

extprocessor BTSITENAME {
  type                    lsapi
  address                 UDS://tmp/lshttpd/BT_EXTP_NAME.sock
  maxConns                20
  env                     LSAPI_CHILDREN=20
  initTimeout             600
  retryTimeout            0
  persistConn             1
  pcKeepAliveTimeout      1
  respBuffer              0
  autoStart               1
  path                    /usr/local/lsws/lsphpBTPHPV/bin/lsphp
  extUser                 www
  extGroup                www
  memSoftLimit            2047M
  memHardLimit            2047M
  procSoftLimit           400
  procHardLimit           500
}

phpIniOverride  {
php_admin_value open_basedir "/tmp/:BT_RUN_PATH"
}

expires {
    enableExpires           1
    expiresByType           image/*=A43200,text/css=A43200,application/x-javascript=A43200,application/javascript=A43200,font/*=A43200,application/x-font-ttf=A43200
}

rewrite  {
  enable                  1
  autoLoadHtaccess        1
  include /www/server/panel/vhost/openlitespeed/proxy/BTSITENAME/urlrewrite/*.conf
  include /www/server/panel/vhost/apache/redirect/BTSITENAME/*.conf
  include /www/server/panel/vhost/openlitespeed/redirect/BTSITENAME/*.conf
}
include /www/server/panel/vhost/openlitespeed/proxy/BTSITENAME/*.conf
'''
        open_base_path = self.sitePath
        if self.sitePath[-1] != '/':
            open_base_path = self.sitePath + '/'
        conf = conf.replace('BT_RUN_PATH', open_base_path)
        conf = conf.replace('BT_EXTP_NAME', self.siteName)
        conf = conf.replace('BTPHPV', self.phpVersion)
        conf = conf.replace('BTSITENAME', self.siteName)

        # 写配置文件
        conf_dir = self.setupPath + '/panel/vhost/openlitespeed/detail/'
        if not os.path.exists(conf_dir):
            os.makedirs(conf_dir)
        file = conf_dir + self.siteName + '.conf'

        public.writeFile(file, conf)
        return True

    # 基本设置检查
    def __CheckStart(self, get, action=""):
        isError = public.checkWebConfig()
        if isinstance(isError, str):
            if isError.find('/proxy/') == -1:  # 如果是反向代理配置文件本身的错误，跳过
                return public.returnMsg(False, '配置文件出错请先排查配置')
        if action == "create":
            if sys.version_info.major < 3:
                if len(get.proxyname) < 3 or len(get.proxyname) > 40:
                    return public.returnMsg(False, '名称必须大于3小于40个字符串')
            else:
                if len(get.proxyname.encode("utf-8")) < 3 or len(get.proxyname.encode("utf-8")) > 40:
                    return public.returnMsg(False, '名称必须大于3小于40个字符串')
        if self.__check_even(get, action):
            return public.returnMsg(False, '指定反向代理名称或代理文件夹已存在')
        # 判断代理，只能有全局代理或目录代理
        if self.__check_proxy_even(get, action):
            return public.returnMsg(False, '不能同时设置目录代理和全局代理')
        # 判断cachetime类型
        if not bool(get.cachetime):
            return public.returnMsg(False, "缓存时间不能为空")
        if get.cachetime:
            try:
                int(get.cachetime)
            except:
                return public.returnMsg(False, "缓存时间不能为空")

        rep = "http(s)?\:\/\/"
        # repd = "http(s)?\:\/\/([a-zA-Z0-9][-a-zA-Z0-9]{0,62}\.)+([a-zA-Z0-9][a-zA-Z0-9]{0,62})+.?"
        tod = "[a-zA-Z]+$"
        repte = "[\?\=\[\]\)\(\*\&\^\%\$\#\@\!\~\`{\}\>\<\,\',\"]+"
        # 检测代理目录格式
        if re.search(repte, get.proxydir):
            return public.returnMsg(False, "代理目录不能有以下特殊符号 ?,=,[,],),(,*,&,^,%,$,#,@,!,~,`,{,},>,<,\,',\"]")
        # 检测发送域名格式
        if get.todomain:
            if re.search("[\}\{\#\;\"\']+", get.todomain):
                return public.returnMsg(False, '发送域名格式错误:' + get.todomain + '<br>不能存在以下特殊字符【 }  { # ; \" \' 】 ')
        if public.get_webserver() != 'openlitespeed' and not get.todomain:
            get.todomain = "$host"

        # 检测目标URL格式
        if not re.match(rep, get.proxysite):
            return public.returnMsg(False, '域名格式错误 ' + get.proxysite)
        if re.search(repte, get.proxysite):
            return public.returnMsg(False, "目标URL不能有以下特殊符号 ?,=,[,],),(,*,&,^,%,$,#,@,!,~,`,{,},>,<,\,',\"]")
        # 检测目标url是否可用
        # if re.match(repd, get.proxysite):
        #     if self.__CheckUrl(get):
        #         return public.returnMsg(False, "目标URL无法访问")
        subfilter = json.loads(get.subfilter)
        # 检测替换内容
        if subfilter:
            for s in subfilter:
                if not s["sub1"]:
                    if s["sub2"]:
                        return public.returnMsg(False, '请输入被替换的内容')
                elif s["sub1"] == s["sub2"]:
                    return public.returnMsg(False, '替换内容与被替换内容不能一致')

    # 检查代理是否存在
    def __check_even(self, get, action=""):
        conf_data = self.__read_config(self.__proxyfile)
        for i in conf_data:
            if i["sitename"] == get.sitename:
                if action == "create":
                    if i["proxydir"] == get.proxydir or i["proxyname"] == get.proxyname:
                        return i
                else:
                    if i["proxyname"] != get.proxyname and i["proxydir"] == get.proxydir:
                        return i

    # 检测全局代理和目录代理是否同时存在
    def __check_proxy_even(self, get, action=""):
        conf_data = self.__read_config(self.__proxyfile)
        n = 0
        if action == "":
            for i in conf_data:
                if i["sitename"] == get.sitename:
                    n += 1
            if n == 1:
                return
        for i in conf_data:
            if i["sitename"] == get.sitename:
                if i["advanced"] != int(get.advanced):
                    return i

    # 计算proxyname md5
    def __calc_md5(self, proxyname):
        md5 = hashlib.md5()
        md5.update(proxyname.encode('utf-8'))
        return md5.hexdigest()

    # 取某个站点反向代理列表
    def GetProxyList(self, get):
        n = 0
        for w in ["nginx", "apache"]:
            conf_path = "%s/panel/vhost/%s/%s.conf" % (self.setupPath, w, get.sitename)
            old_conf = ""
            if os.path.exists(conf_path):
                old_conf = public.readFile(conf_path)
            rep = "(#PROXY-START(\n|.)+#PROXY-END)"
            url_rep = "proxy_pass (.*);|ProxyPass\s/\s(.*)|Host\s(.*);"
            host_rep = "Host\s(.*);"
            if re.search(rep, old_conf):
                # 构造代理配置
                if w == "nginx":
                    get.todomain = str(re.search(host_rep, old_conf).group(1))
                    get.proxysite = str(re.search(url_rep, old_conf).group(1))
                else:
                    get.todomain = ""
                    get.proxysite = str(re.search(url_rep, old_conf).group(2))
                get.proxyname = "旧代理"
                get.type = 1
                get.proxydir = "/"
                get.advanced = 0
                get.cachetime = 1
                get.cache = 0
                get.subfilter = "[{\"sub1\":\"\",\"sub2\":\"\"},{\"sub1\":\"\",\"sub2\":\"\"},{\"sub1\":\"\",\"sub2\":\"\"}]"

                # proxyname_md5 = self.__calc_md5(get.proxyname)
                # 备份并替换老虚拟主机配置文件
                public.ExecShell("cp %s %s_bak" % (conf_path, conf_path))
                conf = re.sub(rep, "", old_conf)
                public.writeFile(conf_path, conf)
                if n == 0:
                    self.CreateProxy(get)
                n += 1
            if n == "1":
                public.serviceReload()
        proxyUrl = self.__read_config(self.__proxyfile)
        sitename = get.sitename
        proxylist = []
        for i in proxyUrl:
            if i["sitename"] == sitename:
                proxylist.append(i)
        return proxylist

    # 检查反向代理配置
    def CheckProxy(self, get):
        if public.get_webserver() != 'nginx': return True
        file = self.setupPath + "/nginx/conf/proxy.conf"
        if not os.path.exists(file):
            conf = '''proxy_temp_path %s/nginx/proxy_temp_dir;
       proxy_cache_path %s/nginx/proxy_cache_dir levels=1:2 keys_zone=cache_one:10m inactive=1d max_size=5g;
       client_body_buffer_size 512k;
       proxy_connect_timeout 60;
       proxy_read_timeout 60;
       proxy_send_timeout 60;
       proxy_buffer_size 32k;
       proxy_buffers 4 64k;
       proxy_busy_buffers_size 128k;
       proxy_temp_file_write_size 128k;
       proxy_next_upstream error timeout invalid_header http_500 http_503 http_404;
       proxy_cache cache_one;''' % (self.setupPath, self.setupPath)
            public.writeFile(file, conf)

        file = self.setupPath + "/nginx/conf/nginx.conf"
        conf = public.readFile(file)
        if (conf.find('include proxy.conf;') == -1):
            rep = "include\s+mime.types;"
            conf = re.sub(rep, "include mime.types;\n\tinclude proxy.conf;", conf)
            public.writeFile(file, conf)

    # 获取站点所有域名
    def GetSiteDomains(self, get):
        data = {}
        domains = public.M('domain').where('pid=?', (get.id,)).field('name,id').select()
        binding = public.M('binding').where('pid=?', (get.id,)).field('domain,id').select()
        if type(binding) == str: return binding
        for b in binding:
            tmp = {}
            tmp['name'] = b['domain']
            tmp['id'] = b['id']
            tmp['binding'] = True
            domains.append(tmp)
        data['domains'] = domains
        data['email'] = public.M('users').where('id=?', (1,)).getField('email')
        return data

    # 获取站点列表
    def GetSiteList(self, get):
        data = self.GetSql(get)
        return data

    def GetSql(self, get, result='1,2,3,4,5,8'):
        try:
            # 判断前端是否传入参数
            order = 'id desc'
            if hasattr(get, 'order'):
                # 验证参数格式
                if re.match(r"^[\w\s\-\.]+$", get.order):
                    order = get.order

            search_key = 'get_list'
            limit = 20
            if hasattr(get, 'limit'):
                limit = int(get.limit)
                if limit < 1: limit = 20

            if hasattr(get, 'result'):
                # 验证参数格式
                if re.match(r"^[\d\,]+$", get.result):
                    result = get.result
            import db
            SQL = db.Sql()
            data = {}
            # 取查询条件
            where = ''
            search = ''
            param = ()
            if hasattr(get, 'search'):
                search = get.search
                if sys.version_info[0] == 2: get.search = get.search.encode('utf-8')
                where, param = self.GetWhere(get.table, get.search)
                if get.table == 'sites' and get.search:
                    conditions = ''
                    if '_' in get.search:
                        cs = ''
                        for i in get.search:
                            if i == '_':
                                cs += '/_'
                            else:
                                cs += i
                        get.search = cs
                        conditions = " escape '/'"
                    pid = SQL.table('domain').where("name LIKE ?{}".format(conditions),
                                                    ("%{}%".format(get.search),)).getField('pid')
                    if pid:
                        if where:
                            where += " or id=" + str(pid)
                        else:
                            where += "id=" + str(pid)
            if get.table == 'sites':
                search_key = 'proxy'
                if where:
                    where = "({}) AND project_type='proxy'".format(where)
                else:
                    where = "project_type='proxy'"

                if hasattr(get, 'type'):
                    try:
                        type_id = int(get.type)
                        if type_id > -1:
                            where += " AND type_id={}".format(type_id)
                    except:
                        pass

            field = self.GetField(get.table)
            if get.table == 'sites':
                cront = public.M(get.table).order("id desc").field(field).select()
                if type(cront) == str:
                    public.M('sites').execute("ALTER TABLE 'sites' ADD 'rname' text DEFAULT ''", ())
            # 实例化数据库对象
            public.set_search_history(get.table, search_key, search)  # 记录搜索历史
            # 是否直接返回所有列表
            if hasattr(get, 'list'):
                data = SQL.table(get.table).where(where, param).field(field).order(order).select()
                return data

            # 取总行数
            count = SQL.table(get.table).where(where, param).count()
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

            o_list = order.split(' ')
            if o_list[0] in self.__SORT_DATA:
                data['data'] = SQL.table(get.table).where(where, param).field(field).select()
                data['plist'] = {'shift': page.SHIFT, 'row': page.ROW, 'order': order}
            else:
                data['data'] = SQL.table(get.table).where(where, param).order(order).field(field).limit(
                    str(page.SHIFT) + ',' + str(page.ROW)).select()  # 取出数据
            data['search_history'] = public.get_search_history(get.table, search_key)

            return data
        except Exception as ex:
            pass
    # 获取返回的字段
    def GetField(self, tableName):
        fields = {
            'sites': "id,name,path,status,ps,addtime,edate,rname",
            'logs': "id,uid,username,type,log,addtime",
            'users': "id,username,phone,email,login_ip,login_time",
            'domain': "id,pid,name,port,addtime",
        }
        try:
            return fields[tableName]
        except:
            return ''

    # 获取条件
    def GetWhere(self, tableName, search):
        if not search:
            return "", ()

        if type(search) == bytes: search = search.encode('utf-8').strip()
        try:
            search = re.search(r"[\w\x80-\xff\.\_\-]+", search).group()
        except:
            return '', ()
        conditions = ''
        if '_' in search:
            cs = ''
            for i in search:
                if i == '_':
                    cs += '/_'
                else:
                    cs += i
            search = cs
            conditions = " escape '/'"
        wheres = {
            'sites': ("name LIKE ? OR ps LIKE ?{}".format(conditions), ('%' + search + '%', '%' + search + '%')),
            'ftps': ("name LIKE ? OR ps LIKE ?{}".format(conditions), ('%' + search + '%', '%' + search + '%')),
            'databases': (
                "(name LIKE ? {} OR ps LIKE ? {})".format(conditions, conditions),
                ("%" + search + "%", "%" + search + "%")),
            'crontab': ("name LIKE ?{}".format(conditions), ('%' + (search) + '%')),
            'logs': ("username=? OR type LIKE ?{} OR log LIKE ?{}".format(conditions, conditions),
                     (search, '%' + search + '%', '%' + search + '%')),
            'backup': ("pid=?", (search,)),
            'users': ("id='?' OR username=?", (search, search)),
            'domain': ("pid=? OR name=?", (search, search)),
            'tasks': ("status=? OR type=?", (search, search)),
        }
        try:
            return wheres[tableName]
        except:
            return '', ()

    def _del_ols_listen_conf(self, sitename):
        conf_dir = '/www/server/panel/vhost/openlitespeed/listen/'
        if not os.path.exists(conf_dir):
            return False
        for i in os.listdir(conf_dir):
            file_name = conf_dir + i
            if os.path.isdir(file_name):
                continue
            conf = public.readFile(file_name)
            if not conf:
                continue
            map_rep = 'map\s+{}.*'.format(sitename)
            conf = re.sub(map_rep, '', conf)
            if "map" not in conf:
                public.ExecShell('rm -f {}*'.format(file_name))
                continue
            public.writeFile(file_name, conf)

    # 取网站日志
    def GetSiteLogs(self, get):
        logsPath = '/www/wwwlogs/'

        serverType = public.get_webserver()
        re_log_file = None
        if serverType == "nginx":
            config_path = '/www/server/panel/vhost/nginx/{}.conf'.format(get.siteName)
            config = public.readFile(config_path)
            re_log_file = self.nginx_get_log_file(config, is_error_log=False)
        elif serverType == 'apache':
            config_path = '/www/server/panel/vhost/apache/{}.conf'.format(get.siteName)
            config = public.readFile(config_path)
            if not config:
                print('|-正在处理网站:未检测到{}站点的日志'.format(get.siteName))
                return
            re_log_file = self.apache_get_log_file(config, is_error_log=False)

        if re_log_file is not None and os.path.exists(re_log_file):
            return public.returnMsg(True, self.xsssec(public.GetNumLines(re_log_file, 1000)))

        if serverType == "nginx":
            logPath = logsPath + get.siteName + '.log'
        elif serverType == 'apache':
            logPath = logsPath + get.siteName + '-access_log'
        else:
            logPath = logsPath + get.siteName + '_ols.access_log'
        if not os.path.exists(logPath):
            return public.returnMsg(False, '日志为空')
        return public.returnMsg(True, self.xsssec(public.GetNumLines(logPath, 1000)))

    # 取网站错误日志
    def get_site_errlog(self, get):
        logsPath = '/www/wwwlogs/'
        serverType = public.get_webserver()
        re_log_file = None
        if serverType == "nginx":
            config_path = '/www/server/panel/vhost/nginx/{}.conf'.format(get.siteName)
            config = public.readFile(config_path)
            if not config:
                return public.returnMsg(False, '配置文件丢失，无法读取到日志文件信息')
            re_log_file = self.nginx_get_log_file(config, is_error_log=True)
        elif serverType == 'apache':
            config_path = '/www/server/panel/vhost/apache/{}.conf'.format(get.siteName)
            config = public.readFile(config_path)
            if not config:
                print('|-正在处理网站:未检测到{}站点的日志'.format(get.siteName))
                return public.returnMsg(False, '配置文件丢失，无法读取到日志文件信息')
            re_log_file = self.apache_get_log_file(config, is_error_log=True)

        if re_log_file is not None and os.path.exists(re_log_file):
            return public.returnMsg(True, self.xsssec(public.GetNumLines(re_log_file, 1000)))

        if serverType == "nginx":
            logPath = logsPath + get.siteName + '.error.log'
        elif serverType == 'apache':
            logPath = logsPath + get.siteName + '-error_log'
        else:
            logPath = logsPath + get.siteName + '_ols.error_log'
        if not os.path.exists(logPath):
            return public.returnMsg(False, '日志为空')
        return public.returnMsg(True, self.xsssec(public.GetNumLines(logPath, 1000)))

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

    # xss 防御
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

    @staticmethod
    def get_ssl_protocol(get):
        """ 获取全局TLS版本
        @author baozi <202-04-18>
        @param:
        @return
        """
        protocols = {
            "TLSv1": False,
            "TLSv1.1": True,
            "TLSv1.2": True,
            "TLSv1.3": False,
        }
        file_path = public.get_panel_path() + "/data/ssl_protocol.json"
        if os.path.exists(file_path):
            data = public.readFile(file_path)
            if data is not False:
                protocols = json.loads(data)
                return protocols

        return protocols

    # 删除反向代理
    def RemoveProxy(self, get, multiple=None):
        conf = self.__read_config(self.__proxyfile)
        sitename = get.sitename
        proxyname = get.proxyname
        for i in range(len(conf)):
            c_sitename = conf[i]["sitename"]
            c_proxyname = conf[i]["proxyname"]
            if c_sitename == sitename and c_proxyname == proxyname:
                proxyname_md5 = self.__calc_md5(c_proxyname)
                for w in ["apache", "nginx", "openlitespeed"]:
                    p = "{sp}/panel/vhost/{w}/proxy/{s}/{m}_{s}.conf*".format(sp=self.setupPath, w=w, s=c_sitename, m=proxyname_md5)

                    public.ExecShell('rm -f {}'.format(p))
                p = "{sp}/panel/vhost/openlitespeed/proxy/{s}/urlrewrite/{m}_{s}.conf*".format(sp=self.setupPath, m=proxyname_md5, s=get.sitename)
                public.ExecShell('rm -f {}'.format(p))
                del conf[i]
                self.__write_config(self.__proxyfile, conf)
                self.SetNginx(get)
                self.SetApache(get.sitename)
                if not multiple:
                    public.serviceReload()
                return public.returnMsg(True, '删除成功')

    @staticmethod
    def get_ip_restrict(get):
        try:
            site_name = get.site_name.strip()
        except AttributeError:
            return public.returnMsg(False, "参数错误")

        return IpRestrict(site_name).to_view()

    @staticmethod
    def set_ip_restrict(get):
        try:
            site_name = get.site_name.strip()
            set_type = get.set_type.strip()
        except (AttributeError, json.JSONDecodeError):
            return public.returnMsg(False, "参数错误")

        ip_restrict = IpRestrict(site_name)
        ip_restrict.restrict_type = set_type

        return public.returnMsg(*ip_restrict.save())

    @staticmethod
    def add_black_ip_restrict(get):
        try:
            site_name = get.site_name.strip()
            value = get.value.strip()
            ipaddress.ip_address(value)
        except (AttributeError, json.JSONDecodeError):
            return public.returnMsg(False, "参数错误")
        except ValueError:
            return public.returnMsg(False, "ip格式错误")

        ip_restrict = IpRestrict(site_name)
        black_list = ip_restrict.black_list
        if value not in black_list:
            black_list.append(value)

        ip_restrict.black_list = black_list

        return public.returnMsg(*ip_restrict.save())

    @staticmethod
    def remove_black_ip_restrict(get):
        try:
            site_name = get.site_name.strip()
            value = get.value.strip()
        except (AttributeError, json.JSONDecodeError):
            return public.returnMsg(False, "参数错误")

        ip_restrict = IpRestrict(site_name)
        black_list = ip_restrict.black_list
        if value in black_list:
            black_list.remove(value)

        ip_restrict.black_list = black_list

        return public.returnMsg(*ip_restrict.save())

    @staticmethod
    def add_white_ip_restrict(get):
        try:
            site_name = get.site_name.strip()
            value = get.value.strip()
            ipaddress.ip_address(value)
        except (AttributeError, json.JSONDecodeError):
            return public.returnMsg(False, "参数错误")
        except ValueError:
            return public.returnMsg(False, "ip格式错误")

        ip_restrict = IpRestrict(site_name)
        white_list = ip_restrict.white_list
        if value not in white_list:
            white_list.append(value)

        ip_restrict.white_list = white_list

        return public.returnMsg(*ip_restrict.save())

    @staticmethod
    def remove_white_ip_restrict(get):
        try:
            site_name = get.site_name.strip()
            value = get.value.strip()
        except (AttributeError, json.JSONDecodeError):
            return public.returnMsg(False, "参数错误")

        ip_restrict = IpRestrict(site_name)
        white_list = ip_restrict.white_list
        if value in white_list:
            white_list.remove(value)

        ip_restrict.white_list = white_list

        return public.returnMsg(*ip_restrict.save())

    @staticmethod
    def get_file_restrict(get):
        try:
            site_name = get.site_name.strip()
        except AttributeError:
            return public.returnMsg(False, "参数错误")

        return FileRestrict(site_name).to_view()

    @staticmethod
    def set_file_restrict(get):
        try:
            site_name = get.site_name.strip()
            set_status = get.set_status.strip()
        except (AttributeError, json.JSONDecodeError):
            return public.returnMsg(False, "参数错误")

        file_restrict = FileRestrict(site_name)
        file_restrict.status = set_status

        return public.returnMsg(*file_restrict.save())

    @staticmethod
    def add_file_restrict(get):
        try:
            site_name = get.site_name.strip()
            file_ext = get.file_ext.strip()
        except (AttributeError, json.JSONDecodeError):
            return public.returnMsg(False, "参数错误")

        file_restrict = FileRestrict(site_name)
        file_list = file_restrict.file_list
        if file_ext not in file_list:
            file_list.append(file_ext)

        file_restrict.file_list = file_list

        return public.returnMsg(*file_restrict.save())

    @staticmethod
    def remove_file_restrict(get):
        try:
            site_name = get.site_name.strip()
            file_ext = get.file_ext.strip()
        except (AttributeError, json.JSONDecodeError):
            return public.returnMsg(False, "参数错误")

        file_restrict = FileRestrict(site_name)
        file_list = file_restrict.file_list
        if file_ext in file_list:
            file_list.remove(file_ext)

        file_restrict.file_list = file_list

        return public.returnMsg(*file_restrict.save())


class BaseRestrict:
    def __init__(self, config_file: str, site_name: str):
        self._conf_file = config_file
        self._conf = self.read_conf()
        self.site_name = site_name

    def read_conf(self):
        if not os.path.exists(self._conf_file):
            return {}
        try:
            conf = json.loads(public.readFile(self._conf_file))
        except:
            conf = {}
        return conf

    def to_view(self):
        return self._conf


class IpRestrict(BaseRestrict):
    def __init__(self, site_name: str):
        ip_restrict_conf_dir = "{}/data/ip_restrict_data".format(public.get_panel_path())
        if not os.path.exists(ip_restrict_conf_dir):
            os.makedirs(ip_restrict_conf_dir)
        super().__init__("{}/{}".format(ip_restrict_conf_dir, site_name), site_name)

    @property
    def restrict_type(self):
        return self._conf.get("restrict_type", "black")

    @restrict_type.setter
    def restrict_type(self, data: str):
        if data in ("black", "white", "closed"):
            self._conf["restrict_type"] = data

    @property
    def black_list(self):
        return self._conf.get("black_list", [])

    @black_list.setter
    def black_list(self, list_data: list):
        self._conf["black_list"] = list_data

    @property
    def white_list(self):
        return self._conf.get("white_list", [])

    @white_list.setter
    def white_list(self, list_data: list):
        self._conf["white_list"] = list_data

    def save(self) -> Tuple[bool, str]:
        if not self._conf:  # 没有的时候不操作
            return True, "操作成功"
        public.writeFile(self._conf_file, json.dumps(self._conf))
        ip_restrict_file = "{}/vhost/ip-restrict/{}.conf".format(public.get_panel_path(), self.site_name)

        if self.restrict_type == "closed":
            public.writeFile(ip_restrict_file, "")
            public.serviceReload()
            return True, "操作成功"

        tmp_conf = []
        if self.restrict_type == "white":
            for i in self.white_list:
                tmp_conf.append("allow {};".format(i))

            tmp_conf.append("deny all; # 除开上述IP外，其他IP全部禁止访问")
        elif self.restrict_type == "black":
            for i in self.black_list:
                tmp_conf.append("deny {};".format(i))
        else:
            raise ValueError("错误的类型，无法操作")

        public.writeFile(ip_restrict_file, "\n".join(tmp_conf))
        isError = public.checkWebConfig()
        if isError is not True:
            public.writeFile(ip_restrict_file, "")
            return False, "操作失败"
        public.serviceReload()
        return True, "操作成功"


class FileRestrict(BaseRestrict):

    def __init__(self, site_name: str):
        restrict_conf_dir = "{}/data/file_restrict_data".format(public.get_panel_path())
        if not os.path.exists(restrict_conf_dir):
            os.makedirs(restrict_conf_dir)
        super().__init__("{}/{}".format(restrict_conf_dir, site_name), site_name)

    @property
    def status(self):
        return self._conf.get("status", "closed")

    @status.setter
    def status(self, stat_str: str):
        if stat_str in ("closed", "open"):
            self._conf["status"] = stat_str

    @property
    def file_list(self):
        return self._conf.get("file_list", [])

    @file_list.setter
    def file_list(self, list_data: list):
        self._conf["file_list"] = list_data

    def save(self) -> Tuple[bool, str]:
        if not self._conf:  # 没有的时候不操作
            return True, "操作成功"
        public.writeFile(self._conf_file, json.dumps(self._conf))

        file_restrict_file = "{}/vhost/file-restrict/{}.conf".format(public.get_panel_path(), self.site_name)

        if self.status == "closed" or len(self.file_list) == 0:
            public.writeFile(file_restrict_file, "")
            public.serviceReload()
            return True, "操作成功"

        tmp_conf = []
        for i in self.file_list:
            tmp_conf.append(public.prevent_re_key(i))

        public.writeFile(file_restrict_file, (
            'if ( $uri ~ "^/.*\.({})$" ) {{\n'
            '    return 404;\n'
            '}}\n'
        ).format("|".join(tmp_conf)))

        isError = public.checkWebConfig()
        if isError is not True:
            public.writeFile(file_restrict_file, "")
            return False, "操作失败"
        public.serviceReload()
        return True, "操作成功"
