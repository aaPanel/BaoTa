# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: lkq <lkq@bt.cn>
# -------------------------------------------------------------------

# ------------------------------
# 其他模型
# ------------------------------
import re
import json
import shutil
import sys
import time
import os
from typing import Optional, List, Iterator, Tuple, Dict

import public
from projectModel.base import projectBase


class main(projectBase):
    PANEL_PATH = public.get_panel_path()
    _vhost_path = '{}/vhost'.format(PANEL_PATH)
    _log_name = '项目管理'
    SETUP_PATH = '/www/server/panel'

    def __init__(self):
        pass

    @staticmethod
    def project_find(project_name) -> Optional[dict]:
        """
            @name 获取指定项目配置 
            @param project_name<string> 项目名称
        """
        project_info = public.M('sites').where('project_type=? AND name=?', ('html', project_name)).find()
        # public.print_log(project_info)
        if not isinstance(project_info, dict):
            return None
        return project_info

    def get_project_list(self, get):
        '''
            @name 获取项目列表
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''

        if not 'p' in get:  get.p = 1
        if not 'limit' in get: get.limit = 20
        if not 'callback' in get: get.callback = ''
        if not 'order' in get: get.order = 'id desc'
        type_id = None
        if hasattr(get,"type_id"):
            try:
                type_id = int(get.type_id)
            except:
                type_id = None

        if 'search' in get:
            get.project_name = get.search.strip()
            search = "%{}%".format(get.project_name)
            if type_id is None:
                count = public.M('sites').where('project_type=? AND (name LIKE ? OR ps LIKE ?)',
                                                ('html', search, search)).count()
                data = public.get_page(count, int(get.p), int(get.limit), get.callback)
                data['data'] = public.M('sites').where('project_type=? AND (name LIKE ? OR ps LIKE ?)',
                                                       ('html', search, search)).limit(
                    data['shift'] + ',' + data['row']).order(get.order).select()
            else:
                count = public.M('sites').where('project_type=? AND (name LIKE ? OR ps LIKE ?) AND type_id = ?',
                                                ('html', search, search, type_id)).count()
                data = public.get_page(count, int(get.p), int(get.limit), get.callback)
                data['data'] = public.M('sites').where('project_type=? AND (name LIKE ? OR ps LIKE ?) AND type_id = ?',
                                                       ('html', search, search, type_id)).limit(
                    data['shift'] + ',' + data['row']).order(get.order).select()
        else:
            if type_id is None:
                count = public.M('sites').where('project_type=?', 'html').count()
                data = public.get_page(count, int(get.p), int(get.limit), get.callback)
                data['data'] = public.M('sites').where('project_type=?', 'html').limit(
                    data['shift'] + ',' + data['row']).order(get.order).select()
            else:
                count = public.M('sites').where('project_type=? AND type_id = ?', ('html', type_id)).count()
                data = public.get_page(count, int(get.p), int(get.limit), get.callback)
                data['data'] = public.M('sites').where('project_type=? AND type_id = ?', ('html', type_id)).limit(
                    data['shift'] + ',' + data['row']).order(get.order).select()

        # ssl
        for val in data['data']:
            print(val["name"])
            val['ssl'] = self.get_site_ssl_info(val["name"])

        return data

    def project_get_domain(self, get):
        '''
            @name 获取指定项目的域名列表
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        project_id = public.M('sites').where('name=?', (get.project_name,)).getField('id')
        if not project_id:
            return public.return_data(False, '站点查询失败')
        domains = public.M('domain').where('pid=?', (project_id,)).order('id desc').select()
        # project_find = self.get_project_find(get.project_name)
        # if not project_find:
        #     return public.return_data(False, '站点查询失败')
        # if len(domains) != len(project_find['project_config']['domains']):
        #     public.M('domain').where('pid=?', (project_id,)).delete()
        #     if not project_find: return []
        #     for d in project_find['project_config']['domains']:
        #         domain = {}
        #         arr = d.split(':')
        #         if len(arr) < 2: arr.append(80)
        #         domain['name'] = arr[0]
        #         domain['port'] = int(arr[1])
        #         domain['pid'] = project_id
        #         domain['addtime'] = public.getDate()
        #         public.M('domain').insert(domain)
        #     if project_find['project_config']['domains']:
        #         domains = public.M('domain').where('pid=?', (project_id,)).select()
        return domains

    def project_remove_domain(self, get):
        '''
            @name 为指定项目删除域名
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
                domain: string<域名>
            }
            @return dict
        '''
        project_find = self.project_find(get.project_name)
        if not project_find:
            return public.return_error('指定项目不存在')
        project_name = project_find["name"]
        domain_arr = get.domain.split(':')
        if len(domain_arr) == 1:
            domain_arr.append("80")

        project_id = project_find["id"]
        if public.M('domain').where("pid=?", (project_id,)).count() <= 1:
            return public.return_error('项目至少需要一个域名')
        domain_id = public.M('domain').where('name=? AND pid=? AND port= ?',
                                             (domain_arr[0], project_id, domain_arr[1])).getField('id')
        if not domain_id:
            return public.return_error('指定域名不存在')
        public.M('domain').where('id=?', (domain_id,)).delete()

        public.WriteLog(self._log_name, '从项目：{}，删除域名{}'.format(get.project_name, get.domain))

        # 写配置文件
        self._nginx_set_domain(project_id, project_name, prefix="html_")
        self._apache_set_domain(project_id, project_name, project_find["path"])

        return public.returnMsg(True, '删除域名成功')

    def _test_domain_list(self, domain_list: List[str]) -> Tuple[List[Tuple[str, str]], List[Dict]]:
        res, error = [], []
        for i in domain_list:
            if not i.strip():
                continue
            d_list = [i.strip() for i in i.split(":")]
            if len(d_list) > 1:
                try:
                    p = int(d_list[1])
                    if not (1 < p < 65535):
                        error.append({
                            "domain": i,
                            "msg": "端口范围错误"
                        })
                        continue
                    else:
                        d_list[1] = str(p)
                except:
                    error.append({
                        "domain": i,
                        "msg": "端口范围错误"
                    })
                    continue
            else:
                d_list.append("80")
            d, p = d_list
            d = self.check_domain(d)
            if isinstance(d, str):
                res.append((d, p)),
                continue
            error.append({
                "domain": i,
                "msg": "域名格式错误"
            })

        res = list(set(res))
        return res, error

    def project_add_domain(self, get):
        '''
            @name 为指定项目添加域名
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
                domains: list<域名列表>
            }
            @return dict
        '''
        try:
            if isinstance(get.domains, str):
                domains = json.loads(get.domains)
            else:
                domains = get.domains
        except json.JSONDecodeError:
            return public.return_error('参数错误')
        if not isinstance(domains, list):
            return public.return_error('参数错误')
        project_find = self.project_find(get.project_name)
        if not project_find:
            return public.return_error('指定项目不存在')
        project_id = project_find['id']
        project_name = project_find["name"]
        res_domains = []
        check_cloud = False
        for domain in domains:
            domain = domain.strip()
            if not domain:
                continue
            domain_arr = domain.split(':')
            domain_arr[0] = self.check_domain(domain_arr[0])
            if domain_arr[0] is False:
                res_domains.append({"name": domain, "status": False, "msg": '域名格式错误'})
                continue
            if len(domain_arr) == 1:
                domain_arr.append("")
            if domain_arr[1] == "":
                domain_arr[1] = 80
                domain += ':80'
            try:
                if not (0 < int(domain_arr[1]) < 65535):
                    res_domains.append({"name": domain, "status": False, "msg": '域名格式错误'})
                    continue
            except ValueError:
                res_domains.append({"name": domain, "status": False, "msg": '域名格式错误'})
                continue
            if not public.M('domain').where('name=? and port=?', (domain_arr[0], domain_arr[1])).count():
                public.M('domain').add('name,pid,port,addtime',
                                       (domain_arr[0], project_id, domain_arr[1], public.getDate()))
                public.WriteLog(self._log_name, '成功添加域名{}到项目{}'.format(domain, get.project_name))
                res_domains.append({"name": domain_arr[0], "status": True, "msg": '添加成功'})
                if not check_cloud:
                    check_cloud = True
                    public.check_domain_cloud(domain_arr[0])
            else:
                public.WriteLog(self._log_name, '添加域名错误，域名{}已存在'.format(domain))
                res_domains.append(
                    {"name": domain_arr[0], "status": False, "msg": '添加失败，域名{}已存在'.format(domain)})

        # 写配置文件
        self._nginx_set_domain(project_id, project_name, prefix="html_")
        self._apache_set_domain(project_id, project_name, project_find["path"])

        return self._check_add_domain(get.project_name, res_domains)

    def _apache_set_domain(self, project_id, project_name, site_path):
        file = '{}/apache/html_{}.conf'.format(self._vhost_path, project_name)
        conf: str = public.readFile(file)
        if not isinstance(conf, str):
            return False

        all_domains_data = public.M('domain').where('pid=?', (project_id,)).select()
        if not isinstance(all_domains_data, list):
            return False
        domains, ports = set(), set()
        for i in all_domains_data:
            domains.add(str(i["name"]))
            ports.add(str(i["port"]))

        domains_str = " ".join(domains)

        # 设置域名
        rep_server_name = re.compile(r"\s*ServerAlias\s*(.*)\n", re.M)
        new_conf = rep_server_name.sub("\n    ServerAlias {}\n".format(domains_str), conf)

        rep_ports = re.compile(r"<VirtualHost +.*:(?P<port>\d+)+\s*>")
        need_remove_port = []
        for tmp in rep_ports.finditer(new_conf):
            if tmp.group("port") in ports:
                ports.remove(tmp.group("port"))
            elif tmp.group("port") != "443":
                need_remove_port.append(tmp.group("port"))

        if need_remove_port:
            for i in need_remove_port:
                tmp_rep = re.compile(r"<VirtualHost.*" + i + r"(.|\n)*?</VirtualHost[^\n]*\n?")
                new_conf = tmp_rep.sub("", new_conf, 1)

        if ports:
            # 添加其他的port
            try:
                httpdVersion = public.readFile('/www/server/apache/version.pl').strip()
            except:
                httpdVersion = ""
            if httpdVersion == '2.2':
                apaOpt = "Order allow,deny\n\t\tAllow from all"
            else:
                apaOpt = 'Require all granted'

            template_file = "{}/template/apache/html_http.conf".format(self._vhost_path)
            config_body = public.readFile(template_file)
            other_config_body_list = []
            for p in ports:
                other_config_body_list.append(config_body.format(
                    port=p,
                    server_admin="admin@{}".format(project_name),
                    site_path=site_path,
                    server_name='{}.{}'.format(p, project_name),
                    domains=domains_str,
                    log_path=self._get_sites_log_path(),
                    project_name=project_name,
                    apa_opt=apaOpt,
                ))
            new_conf += "\n" + "\n".join(other_config_body_list)
        from mod.base.web_conf import ap_ext
        # 先清空再统一设置
        new_conf = ap_ext.remove_extension_from_config(project_name, new_conf)
        new_conf = ap_ext.set_extension_by_config(project_name, new_conf)

        public.writeFile(file, new_conf)
        # 添加端口
        self.apache_add_ports(port_list=ports)

        return True

    @staticmethod
    def get_project_info(get):
        '''
            @name 获取指定项目信息
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        project_info = public.M('sites').where('project_type=? AND name=?', ('html', get.project_name)).find()
        if not project_info:
            return public.return_error('指定项目不存在!')
        return project_info

    @staticmethod
    def _format_path_str(path: str):
        return path.replace('//', '/').rstrip("/")

    @staticmethod
    def _check_site_path(path):
        other_path = public.M('config').where("id=?", ('1',)).field('sites_path,backup_path').find()
        # public.print_log(other_path)
        if path == other_path['sites_path'] or path == other_path['backup_path']:
            return False
        return True

    # 添加到nginx
    def set_nginx_conf(self, ports: Iterator[str], domains: List[str], site_name, site_path):
        listen_ipv6 = public.listen_ipv6()
        listen_ports = ''
        for p in ports:
            listen_ports += "    listen {};\n".format(p)
            if listen_ipv6:
                listen_ports += "    listen [::]:{};\n".format(p)
        listen_ports = listen_ports.strip()
        config_file = "{}/nginx/html_{}.conf".format(self._vhost_path, site_name)
        template_file = "{}/template/nginx/html_http.conf".format(self._vhost_path)

        config_body = public.readFile(template_file)

        conf = config_body.format(
            listen_ports=listen_ports,
            site_path=site_path,
            ssl_start_msg=public.getMsg('NGINX_CONF_MSG1'),
            err_page_msg=public.getMsg('NGINX_CONF_MSG2'),
            setup_path="/www/server",
            rewrite_start_msg=public.getMsg('NGINX_CONF_MSG4'),
            log_path=self._get_sites_log_path(),
            site_name=site_name,
            domains=' '.join(domains)
        )
        from mod.base.web_conf import ng_ext
        conf = ng_ext.set_extension_by_config(site_name, conf)

        # 写配置文件
        if not os.path.exists("{}/nginx/well-known".format(self._vhost_path)):
            os.makedirs("{}/nginx/well-known".format(self._vhost_path), 0o600)
        public.writeFile("{}/nginx/well-known/{}.conf".format(self._vhost_path, site_name), "")
        public.writeFile(config_file, conf)

        # 生成伪静态文件
        rewrite_file = "{}/rewrite/html_{}.conf".format(self._vhost_path, site_name)
        if not os.path.exists(os.path.dirname(rewrite_file)):
            os.makedirs(os.path.dirname(rewrite_file))
        if not os.path.exists(rewrite_file):
            public.writeFile(rewrite_file, '# 请将伪静态规则或自定义NGINX配置填写到此处\n')

        return True

    def get_project_find(self, project_name):
        '''
            @name 获取指定项目配置
            @author hwliang<2021-08-09>
            @param project_name<string> 项目名称
            @return dict
        '''
        project_info = public.M('sites').where('project_type=? AND name=?', ('html', project_name)).find()
        if isinstance(project_info, str):
            raise public.PanelError('数据库查询错误：'+ project_info)
        if not project_info: return False
        project_info['project_config'] = json.loads(project_info['project_config'])
        return project_info

    def set_apache_config(self, project_info):
        self._apache_set_domain(project_info["id"], project_info["name"], project_info["path"])

    def set_apache_conf(self, ports: Iterator[str], domains: List[str], site_name, site_path):
        self.apache_add_ports(port_list=ports)
        try:
            httpdVersion = public.readFile('/www/server/apache/version.pl').strip()
        except:
            httpdVersion = ""
        if httpdVersion == '2.2':
            apaOpt = "Order allow,deny\n\t\tAllow from all"
        else:
            apaOpt = 'Require all granted'

        config_file = "{}/apache/html_{}.conf".format(self._vhost_path, site_name)
        template_file = "{}/template/apache/html_http.conf".format(self._vhost_path)

        config_body = public.readFile(template_file)
        apache_config_body_list = []
        domains = " ".join(domains)
        for p in ports:
            apache_config_body_list.append(config_body.format(
                port=p,
                server_admin="admin@{}".format(site_name),
                site_path=site_path,
                server_name='{}.{}'.format(p, site_name),
                domains=domains,
                log_path=self._get_sites_log_path(),
                project_name=site_name,
                apa_opt=apaOpt,
            ))
        apache_config_body = "\n".join(apache_config_body_list)
        from mod.base.web_conf import ap_ext
        apache_config_body = ap_ext.set_extension_by_config(site_name, apache_config_body)
        htaccess = site_path + '/.htaccess'
        if not os.path.exists(htaccess):
            public.writeFile(htaccess, ' ')
        public.ExecShell('chmod -R 755 ' + htaccess)
        public.ExecShell('chown -R www:www ' + htaccess)
        public.writeFile(config_file, apache_config_body)
        return True

    def create_project(self, get):
        res_msg = self._check_webserver()  # 检查是否有web服务
        if res_msg:
            return public.returnMsg(False, res_msg)
        isError = public.checkWebConfig()
        if isError is not True:
            return public.returnMsg(False, 'ERROR: 检测到配置文件有错误,请先排除后再操作<br><br>'
                                           '<a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')
        public.set_module_logs("create_html_project", "create")
        get.path = self._format_path_str(get.path)
        if not public.check_site_path(get.path):
            a, c = public.get_sys_path()
            return public.returnMsg(False, '请不要将网站根目录设置到以下关键目录中: <br>{}'.format("<br>".join(a + c)))
        try:
            siteMenu = json.loads(get.webname.strip())
        except json.JSONDecodeError:
            return public.returnMsg(False, 'webname参数格式不正确，应该是可被解析的JSON字符串')
        site_name = self.domain_to_puny_code(siteMenu['domain'].strip().split(':')[0]).strip().lower()
        public.check_domain_cloud(site_name)
        site_path = get.path.replace(' ', '')
        site_port = get.port.strip().replace(' ', '')

        if site_port == "":
            site_port = "80"
        if not public.checkPort(site_port):
            return public.returnMsg(False, 'SITE_ADD_ERR_PORT')

        # 表单验证
        if not self._check_site_path(site_path):
            return public.returnMsg(False, 'PATH_ERROR')
        if not re.match(r"^([\w\-*]{1,100}\.){1,24}([\w\-]{1,24}|[\w\-]{1,24}\.[\w\-]{1,24})$", site_name):
            return public.returnMsg(False, 'SITE_ADD_ERR_DOMAIN')
        if site_name.find('*') != -1:
            return public.returnMsg(False, 'SITE_ADD_ERR_DOMAIN_TOW')
        if site_path[-1] == '.':
            return public.returnMsg(False, '网站目录结尾不可以是 "."')

        main_domain = site_name
        old_pid = public.M('domain').where("name=? and port=?", (main_domain, int(site_port))).getField('pid')

        if old_pid:
            if public.M('sites').where('id=?', (old_pid,)).count():
                return public.returnMsg(False, 'SITE_ADD_ERR_DOMAIN_EXISTS')
            public.M('domain').where('pid=?', (old_pid,)).delete()

        if public.M('binding').where('domain=?', (site_name,)).count():
            return public.returnMsg(False, 'SITE_ADD_ERR_DOMAIN_EXISTS')

        # 是否重复
        sql = public.M('sites')
        if sql.where("name=?", (site_name,)).count():
            if public.is_ipv4(site_name):
                site_name = site_name + "_" + str(site_port)
            else:
                return public.returnMsg(False, 'SITE_ADD_ERR_EXISTS')

        domain_list, error = self._test_domain_list(siteMenu['domainlist'])
        if error:
            return public.returnMsg(False, '域名信息解析错误')

        all_domains = set((i[0] for i in domain_list))
        all_domains.add(site_name)
        all_ports = set((i[1] for i in domain_list))
        all_ports.add(site_port)

        # 创建根目录
        if not os.path.exists(site_path):
            try:
                os.makedirs(site_path)
            except Exception as ex:
                return public.returnMsg(False, '创建根目录失败, %s' % ex)
            public.ExecShell('chmod -R 755 ' + site_path)
            public.ExecShell('chown -R www:www ' + site_path)

        # 创建默认文档
        index = site_path + '/index.html'
        if not os.path.exists(index):
            public.writeFile(index, public.readFile('/www/server/panel/data/defaultDoc.html'))
            public.ExecShell('chmod -R 755 ' + index)
            public.ExecShell('chown -R www:www ' + index)

        # 创建自定义404页
        doc404 = site_path + '/404.html'
        if not os.path.exists(doc404):
            public.writeFile(doc404, public.readFile('/www/server/panel/data/404.html'))
            public.ExecShell('chmod -R 755 ' + doc404)
            public.ExecShell('chown -R www:www ' + doc404)


        # 创建basedir
        self.del_user_ini_file(site_path)
        user_ini_file = site_path + '/.user.ini'
        if not os.path.exists(user_ini_file):
            public.writeFile(user_ini_file, 'open_basedir=' + site_path + '/:/tmp/')
            public.ExecShell('chmod 644 ' + user_ini_file)
            public.ExecShell('chown root:root ' + user_ini_file)
            public.ExecShell('chattr +i ' + user_ini_file)

        ngx_open_basedir_path = self.SETUP_PATH + '/vhost/open_basedir/nginx'
        if not os.path.exists(ngx_open_basedir_path):
            os.makedirs(ngx_open_basedir_path, 384)
        ngx_open_basedir_file = ngx_open_basedir_path + '/{}.conf'.format(site_name)
        ngx_open_basedir_body = '''set $bt_safe_dir "open_basedir";
set $bt_safe_open "{}/:/tmp/";'''.format(site_path)

        public.writeFile(ngx_open_basedir_file, ngx_open_basedir_body)

        # 写入配置
        result = self.set_nginx_conf(all_ports, all_domains, site_name, site_path)
        result = self.set_apache_conf(all_ports, all_domains, site_name, site_path)

        # 检查处理结果
        if not result:
            return public.returnMsg(False, 'SITE_ADD_ERR_WRITE')

        ps = public.xssencode2(get.ps)
        # 添加放行端口
        if site_port != '80':
            import firewalls
            get_obj = public.dict_obj()
            get_obj.port = site_port
            get_obj.ps = site_name
            firewalls.firewalls().AddAcceptPort(get_obj)

        if not hasattr(get, 'type_id'):
            get.type_id = 0

        # 写入数据库
        get.pid = sql.table('sites').add('name,path,status,ps,type_id,project_type,addtime',
                                         (site_name, site_path, '1', ps, get.type_id, "html", public.getDate()))

        sql.table('domain').add('pid,name,port,addtime', (get.pid, main_domain, site_port, public.getDate()))
        for d, p in domain_list:
            sql.table('domain').add('pid,name,port,addtime', (get.pid, d, p, public.getDate()))

        data = {"siteStatus": True, "siteId": get.pid, 'ftpStatus': False}

        # 添加FTP
        if get.get("ftp", "false") == 'true':
            import ftp
            result = ftp.ftp().AddUser(get)
            if result['status']:
                data['ftpStatus'] = True
                data['ftpUser'] = get.ftp_username
                data['ftpPass'] = get.ftp_password

        public.serviceReload()
        public.WriteLog('TYPE_SITE', 'SITE_ADD_SUCCESS', (site_name,))
        return data

    def clear_config(self, project_name):
        self.clear_nginx_config(project_name)
        self.clear_apache_config(project_name)
        public.serviceReload()
        return True

    def clear_nginx_config(self, project_name):
        config_file = "{}/nginx/html_{}.conf".format(self._vhost_path, project_name)
        if os.path.exists(config_file):
            os.remove(config_file)
        rewrite_file = "{}/rewrite/html_{}.conf".format(self._vhost_path, project_name)
        if os.path.exists(rewrite_file):
            os.remove(rewrite_file)
        return True

    def clear_apache_config(self, project_name):
        config_file = "{}/apache/html_{}.conf".format(self._vhost_path, project_name)
        if os.path.exists(config_file):
            os.remove(config_file)
        return True

    # 删除指定项目
    def remove_project(self, get):
        project_find = self.project_find(get.project_name)

        if not project_find:
            return public.return_error('指定项目不存在: {}'.format(get.project_name))

        self.clear_config(get.project_name)
        # 删除配置信息
        from mod.base.web_conf import remove_sites_service_config
        remove_sites_service_config(get.project_name, "html_")

        public.M('domain').where('pid=?', (project_find['id'],)).delete()
        public.M('sites').where('name=?', (get.project_name,)).delete()
        public.WriteLog(self._log_name, '删除其他项目{}'.format(get.project_name))
        return public.return_data(True, '删除项目成功')

    @staticmethod
    def _check_add_domain(site_name, domains):
        from panelSite import panelSite
        ssl_data = panelSite().GetSSL(type("get", tuple(), {"siteName": site_name})())
        res = {"domains": domains}
        if not ssl_data["status"]:
            return res
        domain_rep = []
        for i in ssl_data["cert_data"]["dns"]:
            if i.startswith("*"):
                _rep = r"^[^\.]+\." + i[2:].replace(".", r"\.")
            else:
                _rep = "^" + i.replace(".", r"\.")
            domain_rep.append(_rep)
        no_ssl = []
        for domain in domains:
            if not domain["status"]:
                continue
            for _rep in domain_rep:
                if re.search(_rep, domain["name"]):
                    break
            else:
                no_ssl.append(domain["name"])
        if not no_ssl:
            return res
        res["not_ssl"] = no_ssl
        res["tip"] = "本站点已启用SSL证书,但本次添加的域名：{}，无法匹配当前证书，如有需求，请重新申请证书。".format(
            str(no_ssl))
        return res

    def project_dir_info(self, get):
        try:
            project_name = get.project_name
        except AttributeError:
            return public.returnMsg(False, "参数错误")
        project_info = self.project_find(project_name)
        if not project_info:
            return public.returnMsg(False, "未查询到网站")
        data = {
            'userini': False,
            'path': project_info["path"],
        }
        run_path = self._get_site_run_path(project_name, project_info["path"])
        user_ini_file = run_path + '/.user.ini'
        user_ini_conf = public.readFile(user_ini_file)
        if user_ini_conf and "open_basedir" in user_ini_conf:
            data['userini'] = True
        data['run_path'] = run_path.replace(project_info["path"], "")

        return data

    def set_dir_user_ini(self, get):
        try:
            project_name = get.project_name
        except AttributeError:
            return public.returnMsg(False, "参数错误")
        project_info = self.project_find(project_name)
        if not project_info:
            return public.returnMsg(False, "未查询到网站")
        site_path = project_info["path"]
        run_path = self._get_site_run_path(project_name, project_info["path"])
        filename = run_path + '/.user.ini'
        conf = public.readFile(filename)
        try:
            if os.path.exists(filename):
                public.ExecShell("chattr -i " + filename)
            if conf and "open_basedir" in conf:
                rep = "\n*open_basedir.*"
                conf = re.sub(rep, "", conf)
                if not conf:
                    os.remove(filename)
                else:
                    public.writeFile(filename, conf)
                    if os.path.exists(filename):
                        public.ExecShell("chattr +i " + filename)

                return public.returnMsg(True, 'SITE_BASEDIR_CLOSE_SUCCESS')

            if conf and "session.save_path" in conf:
                s_path = re.search(r'session.save_path\s*=\s*(.*)', conf).groups(1)[0]
                public.writeFile(filename, conf + '\nopen_basedir={}/:/tmp/:{}'.format(site_path, s_path))
            else:
                public.writeFile(filename, 'open_basedir={}/:/tmp/'.format(site_path))
            if os.path.exists(filename):
                public.ExecShell("chattr +i " + filename)
            if not os.path.exists(filename):
                return public.returnMsg(False, '.user.ini文件不存在,设置防跨站失败,请关闭防篡改或其他安全软件后再试!')

            public.serviceReload()
            return public.returnMsg(True, 'SITE_BASEDIR_OPEN_SUCCESS')
        except Exception as e:
            if os.path.exists(filename):
                public.ExecShell("chattr +i " + filename)
            if "Operation not permitted" in str(e):
                return public.returnMsg(False, "{}\t权限拒绝,设置防跨站失败,请关闭防篡改或其他安全软件后再试!".format(str(e)))
            return public.returnMsg(False, str(e))

    def change_site_path(self, get):
        try:
            project_name = get.project_name
            path = get.path
        except AttributeError:
            return public.returnMsg(False, "参数错误")
        project_info = self.project_find(project_name)
        if not project_info:
            return public.returnMsg(False, "未查询到网站")
        if path == "":
            return public.returnMsg(False, "DIR_EMPTY")

        if not self._check_site_path(path):
            return public.returnMsg(False, "PATH_ERROR")
        if not public.check_site_path(path):
            a, c = public.get_sys_path()
            return public.returnMsg(False, '请不要将网站根目录设置到以下关键目录中: <br>{}'.format("<br>".join(a + c)))

        if not os.path.exists(path):
            return public.returnMsg(False, '指定的网站根目录不存在，无法设置，请检查输入信息.')

        if project_info["path"] == path:
            return public.returnMsg(False, "SITE_PATH_ERR_RE")

        nginx_file = '{}/nginx/html_{}.conf'.format(self._vhost_path, project_name)
        nginx_conf = public.readFile(nginx_file)
        if nginx_conf:
            new_conf = nginx_conf.replace(project_info["path"], path)
            public.writeFile(nginx_file, new_conf)

        apache_file = '{}/apache/html_{}.conf'.format(self._vhost_path, project_name)
        apache_conf = public.readFile(apache_file)
        if apache_conf:
            rep_doc = re.compile(r"DocumentRoot\s+.*\n")
            new_conf = rep_doc.sub('DocumentRoot "' + path + '"\n', apache_conf)

            rep_dir = re.compile(r"<Directory\s+.*\n")
            new_conf = rep_dir.sub('<Directory "' + path + "\">\n", new_conf)
            public.writeFile(apache_file, new_conf)

        public.M("sites").where("id=?", (project_info["id"],)).setField('path', path)
        public.WriteLog('TYPE_SITE', 'SITE_PATH_SUCCESS', (project_name,))
        self._check_run_path_exists(project_info)

        # 创建basedir
        userIni = path + '/.user.ini'
        if os.path.exists(userIni):
            public.ExecShell("chattr -i " + userIni)
        public.writeFile(userIni, 'open_basedir=' + path + '/:/tmp/')
        public.ExecShell('chmod 644 ' + userIni)
        public.ExecShell('chown root:root ' + userIni)
        public.ExecShell('chattr +i ' + userIni)
        public.serviceReload()

        return public.returnMsg(True, "SET_SUCCESS")

    def _check_run_path_exists(self, project_info):
        run_path = self._get_site_run_path(project_info["name"], project_info["path"])
        if os.path.exists(run_path):
            return True
        self.set_site_run_path(None, run_path="/", project_info=project_info)
        public.WriteLog('TYPE_SITE', '因修改网站[{}]根目录，检测到原指定的运行目录[.{}]不存在，已自动将运行目录切换为[./]'.format(site_info['name'], run_path))

    def set_site_run_path(self, get, run_path=None, project_info=None):
        if not run_path or project_info:
            try:
                project_name = get.project_name
                run_path = get.path
            except AttributeError:
                return public.returnMsg(False, "参数错误")
            project_info = self.project_find(project_name)
            if not project_info:
                return public.returnMsg(False, "未查询到网站")
        project_name = project_info["name"]
        old_run_path = self._get_site_run_path(project_info["name"], project_info["path"])
        site_path = project_info["path"]
        # 处理Nginx
        filename = '{}/nginx/html_{}.conf'.format(self._vhost_path, project_name)
        nginx_conf = public.readFile(filename)
        if nginx_conf:
            tmp = re.search(r'\s*root\s+(.+);', nginx_conf)
            if tmp:
                o_path = tmp.groups()[0]
                new_conf = nginx_conf.replace(o_path, site_path + run_path)
                public.writeFile(filename, new_conf)

        # 处理Apache
        filename = '{}/apache/html_{}.conf'.format(self._vhost_path, project_name)
        ap_conf = public.readFile(filename)
        if ap_conf:
            tmp = re.search(r'\s*DocumentRoot\s*"(.+)"\s*\n', ap_conf)
            if tmp:
                o_path = tmp.groups()[0]
                new_conf = ap_conf.replace(o_path, site_path + run_path)
                public.writeFile(filename, new_conf)

        s_path = old_run_path + "/.user.ini"
        d_path = site_path + run_path + "/.user.ini"
        if s_path != d_path:
            public.ExecShell("chattr -i {}".format(s_path))
            public.ExecShell("mv {} {}".format(s_path, d_path))
            public.ExecShell("chattr +i {}".format(d_path))

        public.serviceReload()
        return public.returnMsg(True, 'SET_SUCCESS')

    def _get_site_run_path(self, site_name: str, site_path: str) -> str:
        run_path = site_path
        webserver = public.get_webserver()
        filename = "{}/{}/html_{}.conf".format(self._vhost_path, webserver, site_name)
        if not os.path.exists(filename):
            return run_path
        conf = public.readFile(filename)
        if webserver == 'nginx':
            tmp1 = re.search(r'\s*root\s+(?P<path>.+);', conf)
            if tmp1:
                run_path = tmp1.group("path")
        elif webserver == 'apache':
            tmp1 = re.search(r'\s*DocumentRoot\s*"(?P<path>.+)"\s*\n', conf)
            if tmp1:
                run_path = tmp1.group("path")
        else:
            tmp1 = re.search(r"vhRoot\s*(?P<path>.*)", conf)
            if tmp1:
                run_path = tmp1.group("path")

        return run_path

    def get_site_ssl_info(self, siteName):
        try:
            s_file = 'vhost/nginx/html_{}.conf'.format(siteName)
            is_apache = False
            if not os.path.exists(s_file):
                s_file = 'vhost/apache/html_{}.conf'.format(siteName)
                is_apache = True

            if not os.path.exists(s_file):
                return -1

            s_conf = public.readFile(s_file)
            if not s_conf: return -1
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
            import traceback
            print(traceback.format_exc())
            return -1

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
