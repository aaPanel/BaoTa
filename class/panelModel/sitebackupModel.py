# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: baozi <baozi@bt.cn>
# -------------------------------------------------------------------
# 网站备份
# ------------------------------
import shutil
import sys
import os
import time
import json
import zipfile
from typing import Dict, List, Optional

os.chdir('/www/server/panel')
if "class/" not in sys.path:
    sys.path.insert(0, "class/")

import public


class SiteBackup(object):
    _PANEL_PATH = "/www/server/panel"

    def __init__(self, site_name: str, base_backup_path: str):
        self.site_name = site_name
        self.site_id = None
        self.db_info = None
        self.database = None
        self.redirect = None
        self.proxy = None
        self.dir_auth = None
        self.ssl = None

        self._backup_path = "{}/{}".format(base_backup_path, self.site_name)
        if not os.path.exists(self._backup_path):
            os.makedirs(self._backup_path)
        self._nginx_conf = None
        self._apache_conf = None

    def backup(self):
        self.backup_db_info()
        self.backup_database()
        self.backup_redirect()
        self.backup_proxy()
        self.backup_dir_auth()
        self.backup_well_known()
        self.backup_rewrite()
        self.backup_nginx_conf()
        self.backup_apache_conf()
        self.backup_ssl()

        self._write_backup_info()

    @property
    def nginx_conf(self):
        if self._nginx_conf is not None:
            return self._nginx_conf
        self._nginx_conf = public.readFile("{}/vhost/nginx/{}.conf".format(self._PANEL_PATH, self.site_name))
        if not self._nginx_conf:
            raise ValueError("Nginx配置文件丢失，无法备份")
        return self._nginx_conf

    @property
    def apache_conf(self):
        if self._apache_conf is not None:
            return self._apache_conf
        self._apache_conf = public.readFile("{}/vhost/apache/{}.conf".format(self._PANEL_PATH, self.site_name))
        if not self._apache_conf:
            raise ValueError("Nginx配置文件丢失，无法备份")
        return self._apache_conf

    def backup_db_info(self):
        site_info = public.M("sites").where("name = ?", (self.site_name,)).find()
        if isinstance(site_info, str):
            raise ValueError("网站数据查询错误")

        if not site_info:
            raise ValueError("为查询到网站信息")

        self.site_id = site_info["id"]
        if int(site_info["type_id"]) != 0:
            site_type = public.M("site_types").where("id = ?", (int(site_info["type_id"]),)).find()
            site_info["site_type_name"] = site_type["name"]

        domains_info = public.M("domain").where("pid = ?", (self.site_id,)).select()
        if isinstance(domains_info, str):
            raise ValueError("网站数据查询错误")

        self.db_info = {
            "site_info": site_info,
            "domains_info": domains_info,
        }

    def backup_database(self):
        database_info = public.M("databases").where("pid = ?", (self.site_id,)).find()
        if isinstance(database_info, str):
            raise ValueError("网站数据查询错误")

        if not database_info:
            return

        self.database = database_info

    def backup_redirect(self):
        # nginx
        back_nginx_redirect = self._backup_path + "/nginx/redirect/"
        nginx_redirect = '/www/server/panel/vhost/nginx/redirect/%s/' % self.site_name
        if os.path.exists(nginx_redirect):
            os.makedirs(back_nginx_redirect)
            public.ExecShell('\cp -r %s* %s*' % (nginx_redirect, back_nginx_redirect))

        # apache
        back_apache_redirect = self._backup_path + "/apache/redirect/"
        apache_redirect = '/www/server/panel/vhost/apache/redirect/%s/' % self.site_name
        if os.path.exists(apache_redirect):
            os.makedirs(back_apache_redirect)
            public.ExecShell('\cp -r %s* %s*' % (apache_redirect, back_apache_redirect))

        redirect_conf = '/www/server/panel/data/redirect.conf'
        if os.path.exists(redirect_conf):
            try:
                redirect_data = json.loads(public.readFile(redirect_conf))
            except json.JSONDecodeError:
                redirect_data = []

            self.redirect = []
            for i in redirect_data:
                if i["sitename"] == self.site_name:
                    self.redirect.append(i)

            if len(self.redirect) == 0:
                self.redirect = None

    def backup_proxy(self):
        # nginx
        back_nginx_proxy = self._backup_path + "/nginx/proxy/"
        nginx_proxy = '/www/server/panel/vhost/nginx/proxy/%s/' % self.site_name
        if os.path.exists(nginx_proxy):
            os.makedirs(back_nginx_proxy)
            public.ExecShell('\cp -r %s* %s*' % (nginx_proxy, back_nginx_proxy))

        # apache
        back_apache_proxy = self._backup_path + "/apache/proxy/"
        apache_proxy = '/www/server/panel/vhost/apache/proxy/%s/' % self.site_name
        if os.path.exists(apache_proxy):
            os.makedirs(back_apache_proxy)
            public.ExecShell('\cp -r %s* %s*' % (apache_proxy, back_apache_proxy))

        proxy_conf = '/www/server/panel/data/proxyfile.json'
        if os.path.exists(proxy_conf):
            try:
                proxy_data = json.loads(public.readFile(proxy_conf))
            except json.JSONDecodeError:
                proxy_data = []

            self.proxy = []
            for i in proxy_data:
                if i["sitename"] == self.site_name:
                    self.proxy.append(i)

            if len(self.proxy) == 0:
                self.proxy = None

    def backup_rewrite(self):
        # nginx
        back_nginx_rewrite = self._backup_path + "/nginx/rewrite/%s.conf" % self.site_name
        nginx_rewrite = '/www/server/panel/vhost/rewrite/%s.conf' % self.site_name
        if os.path.exists(nginx_rewrite):
            os.makedirs(self._backup_path + "/nginx/rewrite/")
            public.ExecShell('\cp -r %s %s' % (nginx_rewrite, back_nginx_rewrite))

        # apache
        site_path = self.db_info["site_info"]["path"]
        back_apache_rewrite = self._backup_path + "/apache/rewrite/.htaccess"
        apache_rewrite = site_path + '/.htaccess'
        if os.path.exists(apache_rewrite):
            os.makedirs(self._backup_path + "/apache/rewrite/")
            public.ExecShell('\cp -r %s %s' % (apache_rewrite, back_apache_rewrite))

    def backup_dir_auth(self):
        # nginx
        back_nginx_dir_auth = self._backup_path + "/nginx/dir_auth/"
        nginx_dir_auth = '/www/server/panel/vhost/nginx/dir_auth/%s/' % self.site_name
        if os.path.exists(nginx_dir_auth):
            os.makedirs(back_nginx_dir_auth)
            public.ExecShell('\cp -r %s* %s*' % (nginx_dir_auth, back_nginx_dir_auth))

        # apache
        back_apache_dir_auth = self._backup_path + "/apache/dir_auth/"
        apache_dir_auth = '/www/server/panel/vhost/apache/dir_auth/%s/' % self.site_name
        if os.path.exists(apache_dir_auth):
            os.makedirs(back_apache_dir_auth)
            public.ExecShell('\cp -r %s* %s*' % (apache_dir_auth, back_apache_dir_auth))

        dir_auth_conf = '/www/server/panel/data/site_dir_auth.json'
        if os.path.exists(dir_auth_conf):
            try:
                dir_auth_data = json.loads(public.readFile(dir_auth_conf))
            except json.JSONDecodeError:
                dir_auth_data = {}

            if self.site_name in dir_auth_data:
                self.dir_auth = dir_auth_data[self.site_name]

    def backup_well_known(self):
        # nginx
        back_nginx_well_known = self._backup_path + "/nginx/well-known/%s.conf" % self.site_name
        nginx_well_known = '/www/server/panel/vhost/nginx/well-known/%s.conf' % self.site_name
        if os.path.exists(nginx_well_known):
            os.makedirs(self._backup_path + "/nginx/well-known/")
            public.ExecShell('\cp -r %s %s' % (nginx_well_known, back_nginx_well_known))

    def backup_nginx_conf(self):
        # nginx
        back_nginx = self._backup_path + "/nginx/%s.conf" % self.site_name
        nginx_conf = '/www/server/panel/vhost/nginx/%s.conf' % self.site_name
        if os.path.exists(nginx_conf):
            public.ExecShell('\cp -r %s %s' % (nginx_conf, back_nginx))

    def backup_apache_conf(self):
        # apache
        back_apache = self._backup_path + "/apache/%s.conf" % self.site_name
        apache_conf = '/www/server/panel/vhost/apache/%s.conf' % self.site_name
        if os.path.exists(apache_conf):
            public.ExecShell('\cp -r %s %s' % (apache_conf, back_apache))

    def backup_ssl(self):
        back_ssl = self._backup_path + "/cert/"
        ssl_path = '/www/server/panel/vhost/cert/%s/' % self.site_name
        if os.path.exists(ssl_path):
            self.ssl = True
            public.ExecShell('\cp -r %s* %s*' % (ssl_path, back_ssl))

    def _write_backup_info(self):
        public.writeFile(self._backup_path + "/site.json", json.dumps({
            "site_name": self.site_name,
            "db_info": self.db_info,
            "database": self.database,
            "redirect": self.redirect,
            "proxy": self.proxy,
            "dir_auth": self.dir_auth,
            "ssl": self.ssl,
        }))


class SiteRecover:

    def __init__(self, site_name: str, base_backup_path: str, force_names: Optional[List[str]] = None):
        self.site_name = site_name
        self.site_id = None
        self._backup_path = "{}/{}".format(base_backup_path, self.site_name)
        if not os.path.exists(self._backup_path):
            raise ValueError("备份数据中没有这个网站")

        if not os.path.exists(self._backup_path + "/site.json"):
            raise ValueError("备份数据读取错误")
        try:
            site_data = json.loads(public.readFile(self._backup_path + "/site.json"))
        except json.JSONDecodeError:
            raise ValueError("备份数据读取错误")

        self.db_info = site_data["db_info"]
        self.database = site_data["database"]
        self.redirect = site_data["redirect"]
        self.proxy = site_data["proxy"]
        self.dir_auth = site_data["dir_auth"]
        self.ssl = site_data["ssl"]
        if isinstance(force_names, (list, tuple)):
            self._force_names = force_names
        else:
            self._force_names = tuple()

        self._not_recover = False
        self._recover_msg = "恢复成功"

    def recover(self):
        self.recover_db_info()
        self.recover_database()
        self.recover_redirect()
        self.recover_proxy()
        self.recover_dir_auth()
        self.recover_well_known()
        self.recover_rewrite()
        self.recover_nginx_conf()
        self.recover_apache_conf()
        self.recover_ssl()
        return self._recover_msg

    def recover_db_info(self):
        site_info = self.db_info["site_info"]
        domains_info = self.db_info["domains_info"]
        old_site_info = public.M("sites").where("name = ?", (self.site_name,)).find()
        if old_site_info:
            if self.site_name in self._force_names:  # 如果是强制恢复，则不跳过后续操作
                return
            self._not_recover = True
            self._recover_msg = "网站【{}】在服务上已存在，跳过其恢复过程".format(self.site_name)
            return

        site_type_id = 0
        if "site_type_name" in site_info:
            site_type = public.M("site_types").where("name = ?", (site_info["site_type_name"],)).find()
            if not site_type:
                site_type_id = public.M("site_types").add("name", (site_info["site_type_name"],))
            else:
                site_type_id = site_type["id"]

        self.site_id = public.M('sites').add('name,path,status,ps,addtime,type_id,project_type,project_config', (
            site_info['name'], site_info['path'], site_info['status'], site_info['ps'],
            site_info['addtime'], site_type_id, site_info['project_type'], site_info['project_config']))
        for domain in domains_info:
            public.M('domain').add('pid,name,port,addtime', (
                self.site_id, domain['name'], domain['port'], domain['addtime']))

    def recover_database(self):
        if self._not_recover:
            return
        pass

    def recover_redirect(self):
        if self._not_recover:
            return
        if self.redirect is None:
            return

            # nginx
        back_nginx_redirect = self._backup_path + "/nginx/redirect/"
        nginx_redirect = '/www/server/panel/vhost/nginx/redirect/%s/' % self.site_name
        if os.path.exists(back_nginx_redirect):
            if not os.path.exists(nginx_redirect):
                os.makedirs(nginx_redirect)
            public.ExecShell('\cp -r %s* %s*' % (back_nginx_redirect, nginx_redirect))

        # apache
        back_apache_redirect = self._backup_path + "/apache/redirect/"
        apache_redirect = '/www/server/panel/vhost/apache/redirect/%s/' % self.site_name
        if os.path.exists(back_apache_redirect):
            if not os.path.exists(apache_redirect):
                os.makedirs(apache_redirect)
            public.ExecShell('\cp -r %s* %s*' % (back_apache_redirect, apache_redirect))

        redirect_conf = '/www/server/panel/data/redirect.conf'
        if os.path.exists(redirect_conf):
            try:
                redirect_data = json.loads(public.readFile(redirect_conf))
            except json.JSONDecodeError:
                redirect_data = []
            redirect_names = {i["redirectname"] for i in redirect_data}
            for i in self.redirect:
                if i["redirectname"] not in redirect_names:
                    redirect_data.append(i)

            public.writeFile(redirect_conf, json.dumps(redirect_data))

    def recover_proxy(self):
        if self._not_recover:
            return
        if self.proxy is None:
            return

        # nginx
        back_nginx_proxy = self._backup_path + "/nginx/proxy/"
        nginx_proxy = '/www/server/panel/vhost/nginx/proxy/%s/' % self.site_name
        if os.path.exists(back_nginx_proxy):
            if not os.path.exists(nginx_proxy):
                os.makedirs(nginx_proxy)
            public.ExecShell('\cp -r %s* %s*' % (back_nginx_proxy, nginx_proxy))

        # apache
        back_apache_proxy = self._backup_path + "/apache/proxy/"
        apache_proxy = '/www/server/panel/vhost/apache/proxy/%s/' % self.site_name
        if os.path.exists(back_apache_proxy):
            if not os.path.exists(apache_proxy):
                os.makedirs(apache_proxy)
            public.ExecShell('\cp -r %s* %s*' % (back_apache_proxy, apache_proxy))

        proxy_conf = '/www/server/panel/data/proxyfile.json'
        if os.path.exists(proxy_conf):
            try:
                proxy_data = json.loads(public.readFile(proxy_conf))
            except json.JSONDecodeError:
                proxy_data = []

            proxynames = {i["proxyname"] for i in proxy_data if i["sitename"] == self.site_name}
            for i in self.proxy:
                if i["proxyname"]  not in proxynames:
                    proxy_data.append(i)

            public.writeFile(proxy_conf, json.dumps(proxy_data))

    def recover_rewrite(self):
        if self._not_recover:
            return

        # nginx
        back_nginx_rewrite = self._backup_path + "/nginx/rewrite/%s.conf" % self.site_name
        nginx_rewrite = '/www/server/panel/vhost/rewrite/%s.conf' % self.site_name
        if os.path.exists(back_nginx_rewrite):
            public.ExecShell('\cp -r %s %s' % (back_nginx_rewrite, nginx_rewrite))

        # apache
        site_path = self.db_info["site_info"]["path"]
        back_apache_rewrite = self._backup_path + "/apache/rewrite/.htaccess"
        apache_rewrite = site_path + '/.htaccess'
        if os.path.exists(back_apache_rewrite):
            public.ExecShell('\cp -r %s %s' % (back_apache_rewrite, apache_rewrite))

    def recover_dir_auth(self):
        if self._not_recover:
            return
        if self.dir_auth is None:
            return

        # nginx
        back_nginx_dir_auth = self._backup_path + "/nginx/dir_auth/"
        nginx_dir_auth = '/www/server/panel/vhost/nginx/dir_auth/%s/' % self.site_name
        if os.path.exists(back_nginx_dir_auth):
            if not os.path.exists(nginx_dir_auth):
                os.makedirs(nginx_dir_auth)
            public.ExecShell('\cp -r %s* %s*' % (back_nginx_dir_auth, nginx_dir_auth))

        # apache
        back_apache_dir_auth = self._backup_path + "/apache/dir_auth/"
        apache_dir_auth = '/www/server/panel/vhost/apache/dir_auth/%s/' % self.site_name
        if os.path.exists(back_apache_dir_auth):
            if not os.path.exists(apache_dir_auth):
                os.makedirs(apache_dir_auth)
            public.ExecShell('\cp -r %s* %s*' % (back_apache_dir_auth, apache_dir_auth))

        dir_auth_conf = '/www/server/panel/data/site_dir_auth.json'
        if os.path.exists(dir_auth_conf):
            try:
                dir_auth_data = json.loads(public.readFile(dir_auth_conf))
            except json.JSONDecodeError:
                dir_auth_data = {}

            dir_auth_data[self.site_name] = self.dir_auth
            public.writeFile(dir_auth_conf, json.dumps(dir_auth_data))

    def recover_well_known(self):
        if self._not_recover:
            return
        # nginx
        back_nginx_well_known = self._backup_path + "/nginx/well-known/%s.conf" % self.site_name
        nginx_well_known = '/www/server/panel/vhost/nginx/well-known/%s.conf' % self.site_name
        if os.path.exists(back_nginx_well_known):
            if not os.path.exists("www/server/panel/vhost/nginx/well-known"):
                os.makedirs("www/server/panel/vhost/nginx/well-known")
            public.ExecShell('\cp -r %s %s' % (back_nginx_well_known, nginx_well_known))

    def recover_nginx_conf(self):
        if self._not_recover:
            return
        # nginx
        back_nginx = self._backup_path + "/nginx/%s.conf" % self.site_name
        nginx_conf = '/www/server/panel/vhost/nginx/%s.conf' % self.site_name
        if os.path.exists(back_nginx):
            public.ExecShell('\cp -r %s %s' % (back_nginx, nginx_conf))

    def recover_apache_conf(self):
        if self._not_recover:
            return
        # apache
        back_apache = self._backup_path + "/apache/%s.conf" % self.site_name
        apache_conf = '/www/server/panel/vhost/apache/%s.conf' % self.site_name
        if os.path.exists(back_apache):
            public.ExecShell('\cp -r %s %s' % (back_apache, apache_conf))

    def recover_ssl(self):
        if self._not_recover:
            return
        if self.ssl is None:
            return
        back_ssl = self._backup_path + "/cert/"
        ssl_path = '/www/server/panel/vhost/cert/%s/' % self.site_name
        if os.path.exists(back_ssl):
            if not os.path.exists(ssl_path):
                os.makedirs(ssl_path)
            public.ExecShell('\cp -r %s* %s*' % (back_ssl, ssl_path))


class SiteBackupManager:
    # 旧版路径  # 正式版未使用过，可在正式版移除
    _OLD_BASE_BACKUP_PATH = "/www/server/site_backup"
    _OLD_RECOVER_PATH = "/www/server/site_backup/recovery"
    _OLD_SITE_BACK_CONFIG = "/www/server/site_backup/site_backup.json"

    _BACKUP_PATH = public.M('config').where("id=?", (1,)).getField('backup_path')
    _BASE_BACKUP_PATH = "{}/site_backup".format(_BACKUP_PATH)
    _RECOVER_PATH = "{}/site_backup/recovery".format(_BACKUP_PATH)
    _SITE_BACK_CONFIG = "{}/site_backup/site_backup.json".format(_BACKUP_PATH)

    def __init__(self):
        self._to_new()
        if not os.path.exists(self._BASE_BACKUP_PATH):
            os.makedirs(self._BASE_BACKUP_PATH)

        self._config = None

    # 旧版路径  # 正式版未使用过，可在正式版移除
    def _to_new(self):
        if os.path.isdir(self._OLD_BASE_BACKUP_PATH) and not os.path.isdir(self._BASE_BACKUP_PATH):
            shutil.move(self._OLD_BASE_BACKUP_PATH, self._BASE_BACKUP_PATH)

    @property
    def config(self) -> Dict[str, List[str]]:
        if self._config is not None:
            return self._config
        default_conf = {}
        try:
            self._config = json.loads(public.readFile(self._SITE_BACK_CONFIG))
        except (json.JSONDecodeError, TypeError):
            pass
        if isinstance(self._config, dict):
            return self._config

        self._config = default_conf
        return self._config

    def save_config(self):
        public.writeFile(self._SITE_BACK_CONFIG, json.dumps(self._config))

    def backup(self, site_list: list):
        backup_name = "site_backup_{}".format(int(time.time()))

        backup_path = "{}/{}".format(self._BASE_BACKUP_PATH, backup_name)
        backup_file = "{}/{}.zip".format(self._BASE_BACKUP_PATH, backup_name)
        if not os.path.exists(backup_path):
            os.makedirs(backup_path)

        res = []
        for site in site_list:
            site_backup = SiteBackup(site_name=site, base_backup_path=backup_path)
            try:
                site_backup.backup()
            except ValueError as e:
                res.append({
                    "name": site,
                    "status": False,
                    "msg": str(e)
                })
            else:
                res.append({
                    "name": site,
                    "status": True,
                    "msg": "备份成功"
                })

        public.ExecShell('cd {}  &&  zip -r {}.zip {}'.format(self._BASE_BACKUP_PATH, backup_name, backup_name))
        time.sleep(0.01)
        public.ExecShell("rm -rf {}".format(backup_path))

        if not os.path.isfile(backup_file):
            return public.returnMsg(False, "备份文件生成失败")

        for r in res:
            if not r["status"]:
                continue

            if r["name"] not in self.config:
                self.config[r["name"]] = []
            self.config[r["name"]].append(backup_name)

        self.save_config()

        return res

    def recover(self, recover_name, force_names: Optional[List[str]] = None):
        recover_path = "{}/{}.zip".format(self._BASE_BACKUP_PATH, recover_name)
        if not os.path.exists(recover_path):
            return False, "没有指定的源文件"
        if not os.path.exists(self._RECOVER_PATH):
            os.makedirs(self._RECOVER_PATH)
        else:
            return False, "有正在恢复的任务，无法操作"

        public.ExecShell("cp -p {} {}/{}.zip".format(recover_path, self._RECOVER_PATH, recover_name))

        zip_file_name = "{}/{}.zip".format(self._RECOVER_PATH, recover_name)
        base_recover_path = "{}/{}".format(self._RECOVER_PATH, recover_name)
        with zipfile.ZipFile(zip_file_name, "r") as z:
            z.extractall(self._RECOVER_PATH)

        res = []
        for site in os.listdir(base_recover_path):
            if force_names is not None and site not in force_names:
                res.append({
                    "name": site,
                    "status": True,
                    "msg": "未选择，跳过恢复"
                })
                continue
            try:
                res_msg = SiteRecover(site_name=site,
                                      base_backup_path=base_recover_path,
                                      force_names=force_names
                                      ).recover()
            except ValueError as e:
                res.append({
                    "name": site,
                    "status": False,
                    "msg": str(e)
                })
            else:
                res.append({
                    "name": site,
                    "status": True,
                    "msg": res_msg,
                })

        public.ExecShell("rm -rf {}".format(self._RECOVER_PATH))
        return True, res

    def backup_list(self):
        res = []
        for i in os.listdir(self._BASE_BACKUP_PATH):
            file_name = self._BASE_BACKUP_PATH + "/" + i
            if os.path.isfile(file_name) and i.endswith(".zip"):
                res.append({
                    "name": i,
                    'filename': file_name,
                    "size": self.to_size(int(os.path.getsize(file_name))),
                    "time": int(os.path.getctime(file_name))
                })
        res.sort(key=lambda x: x["time"], reverse=True)
        return res

    @staticmethod
    def to_size(data):
        ds = ['b', 'KB', 'MB', 'GB', 'TB']
        for d in ds:
            if int(data) < 1024:
                return "%.2f%s" % (data, d)
            data = data / 1024
        return '0b'

    def backup_list_by_site(self, site_name) -> List:
        if site_name not in self.config:
            return []
        res = []
        del_idx = []
        for idx, file_name in enumerate(self.config[site_name]):
            if not file_name.endswith(".zip"):
                file_name += ".zip"

            file_path = "{}/{}".format(self._BASE_BACKUP_PATH, file_name)
            if os.path.isfile(file_path):
                res.append({
                    "name": file_name,
                    'filename': file_path,
                    "size": self.to_size(int(os.path.getsize(file_path))),
                    "time": int(os.path.getctime(file_path))
                })
            else:
                del_idx.append(idx)

        if del_idx:
            for i in del_idx[::-1]:  # 倒序删除
                del self.config[site_name][i]

        res.sort(key=lambda x: x["time"], reverse=True)
        return res

    def backup_site_list(self) -> List:
        res = list(self.config.keys())
        res.sort()
        return res


class main:

    @staticmethod
    def backup_list(get):
        return SiteBackupManager().backup_list()

    @staticmethod
    def backup_sites(get):
        try:
            sites_list = json.loads(get.sites_data.strip())
        except (json.JSONDecodeError, AttributeError):
            return public.returnMsg(False, "参数错误")

        return SiteBackupManager().backup(sites_list)

    @staticmethod
    def site_list(get):
        try:
            return SiteBackupManager().backup_site_list()
        except:
            public.print_log(public.get_error_info())

    @staticmethod
    def backup_list_by_site(get):
        try:
            site_name = get.site_name.strip()
        except AttributeError:
            return public.returnMsg(False, "参数错误")
        return SiteBackupManager().backup_list_by_site(site_name=site_name)

    @staticmethod
    def recover_sites(get):
        try:
            file_name = get.file_name.strip()
            if file_name.endswith(".zip"):
                file_name = file_name[:-4]
            force_names = None
            if "force_names" in get:
                force_names = json.loads(get.force_names.strip())
            if not isinstance(force_names, (list, type(None))):
                raise ValueError()
        except (json.JSONDecodeError, AttributeError, ValueError):
            return public.returnMsg(False, "参数错误")

        flag, data = SiteBackupManager().recover(file_name, force_names=force_names)
        if not flag:
            return public.returnMsg(False, data)
        return public.returnMsg(True, "恢复完成")
