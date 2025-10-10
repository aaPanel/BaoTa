# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: miku <miku@bt.cn>
# -------------------------------------------------------------------
import json
import os
import sys
import time
import sys
import concurrent.futures
import threading
import hashlib
import datetime

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

if '/www/server/panel' not in sys.path:
    sys.path.insert(0, '/www/server/panel')

import public
from mod.project.backup_restore.base_util import BaseUtil
from mod.project.backup_restore.data_manager import DataManager
from mod.project.backup_restore.config_manager import ConfigManager

class SiteModule(DataManager,BaseUtil,ConfigManager):
    def __init__(self):
        self.base_path = '/www/backup/backup_restore'
        self.bakcup_task_json = self.base_path + '/backup_task.json'
        self.site_dir_auth_path="/www/server/panel/data/site_dir_auth.json"
        self.redirect_conf_path="/www/server/panel/data/redirect.conf"
        self.proxy_conf_path="/www/server/panel/data/proxyfile.json"

    def get_site_backup_conf(self,timestamp=None):
        backup_conf = self.get_backup_conf(timestamp)
        site_id = json.loads(backup_conf['site_id'])

        site_data = public.M('sites').field('name,path,project_type,id,ps').select()
        domian_data = public.M('domain').field('name,id,pid,id,port').select()

        if 'ALL' in site_id:
            filtered_sites = [site for site in site_data]
        else:
            filtered_sites = [site for site in site_data if site['id'] in site_id]
        filtered_domain =  [name for name in domian_data]

        pid_map = {}
        for domain in filtered_domain:
            pid = domain["pid"]
            if pid not in pid_map:
                pid_map[pid] = []
            pid_map[pid].append({"name": domain["name"], "port": domain["port"]})
        
        for site in filtered_sites:
            site_id = site["id"]
            if site_id in pid_map:
                site["domains"] = pid_map[site_id]
            site["data_type"] = "backup"
            site["status"] = 0
            site["msg"] = None
        return filtered_sites

    def backup_site_data(self,timestamp):
        data_list=self.get_backup_data_list(timestamp)
        if not data_list:
            return None
        import panelSite
        data_backup_path=data_list['backup_path']
        site_id=data_list['site_id']

        site_backup_path=data_backup_path + '/site/'
        if not os.path.exists(site_backup_path):
            public.ExecShell('mkdir -p {}'.format(site_backup_path))
        self.print_log("====================================================",'backup')
        self.print_log("开始备份站点数据",'backup')
        
        self.backup_site_config(site_backup_path,site_id)


        import db
        site_sql = db.Sql()
        site_sql.table('sites')
        domain_sql = db.Sql()
        domain_sql.table('domain')

        for site in data_list['data_list']['site']:
            #备份db数据库数据
            site_id=site['id']
            site_db_record = site_sql.where('id=?', (site_id,)).find()
            site['site_db_record'] = site_db_record

            if 'domains' in site:
                for domain in site['domains']:
                    pass
                    # domain_db_record = domain_sql.where('name=?', (domain['name'],)).find()
                    # site['domain_db_record'] = domain_db_record

            #备份网站数据
            last_path=os.path.basename(site['path'])
            site["last_path"]=last_path
            site_path=site_backup_path  + last_path
            
            if site["project_type"] == "PHP":
                try:
                    site["php_ver"] = panelSite.panelSite().GetSitePHPVersion(public.to_dict_obj({'siteName': site['name']}))['phpversion']
                except:
                    site["php_ver"] = None

            site['status'] = 1
            # time.sleep(2)
            log_str="备份{}项目：{}".format(site['project_type'],site['name'])
            self.print_log(log_str,"backup")
            #self.print_log("备份{}项目：{}".format(site['project_type'],site['name']),'backup')
            self.update_backup_data_list(timestamp, data_list)

            #备份网站项目
            public.ExecShell("cp -rpa {} {}".format(site['path'],site_path))
            site_zip=site_backup_path+last_path+".zip"
            public.ExecShell("cd {} && zip -r {}.zip {}".format(site_backup_path,last_path,last_path))
            if os.path.exists(site_zip):
                site_zip_size = public.ExecShell("du -sb {}".format(site_zip))[0].split("\t")[0]
                site['data_file_name'] = site_zip
                site['size'] = site_zip_size
                site['zip_sha256'] = self.get_file_sha256(site_zip)

            #清理备份网站目录
            public.ExecShell("rm -rf {}".format(site_path))

            #创建配置文件备份目录
            webserver_conf_path = ["apache", "cert", "config", "nginx", "open_basedir", 
                                 "openlitespeed", "other_php", "rewrite", "ssl", 
                                 "ssl_saved", "template", "tomcat"]
            conf_backup_path = site_backup_path + site['name'] + "_conf/"
            public.ExecShell(f"mkdir -p '{conf_backup_path}'")
            
            #创建子目录
            for wpath in webserver_conf_path:
                web_conf_backup_path = conf_backup_path + wpath
                public.ExecShell(f"mkdir -p '{web_conf_backup_path}'")
            
            #备份网站配置文件
            self.backup_web_conf(site['name'], conf_backup_path)

            #打包网站配置文件
            site_name=site['name']
            site_conf_zip=site_backup_path+site_name+"_conf.zip"
            public.ExecShell("cd {} && zip -r {}_conf.zip {}_conf".format(site_backup_path,site_name,site_name))
            if os.path.exists(site_conf_zip):
                site['conf_file_name'] = site_conf_zip
                site['zip_sha256'] = self.get_file_sha256(site_conf_zip)
                site['conf_sha256'] = self.get_file_sha256(site_conf_zip)  
            site['status'] = 2
            backup_file_name = site['data_file_name'].replace(site_backup_path,"")
            format_backup_file_size = self.format_size(int(site['size']))
            new_log_str="{}项目 {} ✓ ({})".format(site['project_type'],site['name'],format_backup_file_size)
            self.replace_log(log_str,new_log_str,'backup')
            #self.print_log("{}项目 {} ✓ ({})".format(site['project_type'],site['name'],format_backup_file_size),'backup')

            self.update_backup_data_list(timestamp, data_list)

        self.print_log("站点数据备份完成",'backup')

    def backup_site_config(self,site_backup_path,site_id):
        #直接备份站点db文件
        public.ExecShell("\cp -rpa /www/server/panel/data/db/site.db {site_backup_path}site.db".format(site_backup_path=site_backup_path))

        site_id=json.loads(site_id)
        if not 'ALL' in site_id:
            import sqlite3
            conn = sqlite3.connect("{site_backup_path}site.db".format(site_backup_path=site_backup_path))
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sites WHERE id NOT IN ({})".format(','.join(map(str, site_id))))
            cursor.execute("DELETE FROM domain WHERE pid NOT IN ({})".format(','.join(map(str, site_id))))
            conn.commit()
            cursor.close()
            conn.close()

        public.ExecShell("\cp -rpa /www/server/panel/data/db/default.db {site_backup_path}default.db".format(site_backup_path=site_backup_path))
        #备份加密访问配置文件
        if os.path.exists("/www/server/panel/data/site_dir_auth.json"):
            public.ExecShell("\cp -rpa /www/server/panel/data/site_dir_auth.json {site_backup_path}site_dir_auth.json".format(site_backup_path=site_backup_path))
        # 备份加密密码
        if os.path.exists("/www/server/pass/"):
            public.ExecShell("\cp -rpa /www/server/pass/ {site_backup_path}pass/".format(site_backup_path=site_backup_path))

        #备份反代配置
        if os.path.exists("/www/server/proxy_project/sites"):
            public.ExecShell("mkdir -p {site_backup_path}proxy_project/".format(site_backup_path=site_backup_path))
            public.ExecShell("\cp -rpa /www/server/proxy_project/sites {site_backup_path}proxy_project/sites/".format(site_backup_path=site_backup_path))

        #备份重定向配置
        if os.path.exists("/www/server/panel/data/redirect.conf"):
            public.ExecShell("\cp -rpa /www/server/panel/data/redirect.conf {site_backup_path}redirect.conf".format(site_backup_path=site_backup_path))

        if os.path.exists("/www/server/panel/data/proxyfile.json"):
            public.ExecShell("\cp -rpa /www/server/panel/data/proxyfile.json {site_backup_path}proxyfile.json".format(site_backup_path=site_backup_path))

        #备份wp加速配置文件
        if os.path.exists("/www/server/nginx/conf/"):
            nginx_conf_list=os.listdir("/www/server/nginx/conf/")
            for nginx_conf_name in nginx_conf_list:
                if "wpfastcgi" in nginx_conf_name:
                    public.ExecShell("\cp -rpa /www/server/nginx/conf/{nginx_conf_name} {site_backup_path}{nginx_conf_name}".format(nginx_conf_name=nginx_conf_name,site_backup_path=site_backup_path))

        #备份well-known文件
        if os.path.exists("/www/server/panel/vhost/nginx/well-known"):
            public.ExecShell("\cp -rpa /www/server/panel/vhost/nginx/well-known {site_backup_path}/well-known".format(site_backup_path=site_backup_path))

        public.ExecShell("mkdir -p {site_backup_path}/monitor_conf/".format(site_backup_path=site_backup_path))
        public.ExecShell("\cp -rpa /www/server/panel/vhost/nginx/0.monitor*.conf {site_backup_path}/monitor_conf/".format(site_backup_path=site_backup_path))

    def restore_site_config(self,site_backup_path):
        site_db_file=site_backup_path + "site.db"
        default_db_file=site_backup_path + "default.db"
        dir_auth_file=site_backup_path + "site_dir_auth.json"
        pass_path=site_backup_path + "pass"
        proxy_project_path=site_backup_path + "proxy_project"
        redirect_file=site_backup_path + "redirect.conf"
        proxyfile_file=site_backup_path + "proxyfile.json"
        if os.path.exists(site_db_file):
            public.ExecShell("\cp  -rpa {site_db_file} /www/server/panel/data/db".format(site_db_file=site_db_file))
        if os.path.exists(default_db_file):
            public.ExecShell("\cp  -rpa {default_db_file} /www/server/panel/data/default.db".format(default_db_file=default_db_file))
        if os.path.exists(dir_auth_file):
            public.ExecShell("mkdir -p /www/server/pass")
            public.ExecShell("\cp  -rpa {dir_auth_file} /www/server/panel/data/site_dir_auth.json".format(dir_auth_file=dir_auth_file))
        if os.path.exists(pass_path):
            public.ExecShell("\cp  -rpa {pass_path}/* /www/server/pass/".format(pass_path=pass_path))
        if os.path.exists(proxy_project_path):
            if not os.path.exists("/www/server/proxy_project/sites/"):
                public.ExecShell("mkdir -p /www/server/proxy_project/sites/")
            public.ExecShell("\cp  -rpa {proxy_project_path}/sites/* /www/server/proxy_project/sites/".format(proxy_project_path=proxy_project_path))
        if os.path.exists(redirect_file):
            public.ExecShell("\cp  -rpa {redirect_file} /www/server/panel/data/redirect.conf".format(redirect_file=redirect_file))
        if os.path.exists(proxyfile_file):
            public.ExecShell("\cp  -rpa {proxyfile_file} /www/server/panel/data/proxyfile.json".format(proxyfile_file=proxyfile_file))
        

        public.ExecShell("\cp -rpa {site_backup_path}/*wpfastcgi.conf /www/server/nginx/conf/".format(site_backup_path=site_backup_path))

        if os.path.exists(site_backup_path + "well-known"):
            if not os.path.exists("/www/server/panel/vhost/nginx/well-known"):
                public.ExecShell("mkdir -p /www/server/panel/vhost/nginx/well-known")   
            public.ExecShell("\cp -rpa {site_backup_path}well-known/* /www/server/panel/vhost/nginx/well-known/".format(site_backup_path=site_backup_path))

        public.ExecShell("\cp -rpa {site_backup_path}monitor_conf/* /www/server/panel/vhost/nginx/".format(site_backup_path=site_backup_path))

    def restore_site_python_env(self,timestamp):
        self.print_log("================================================","restore")
        self.print_log("开始还原站点Python依赖...",'restore')
        restore_data=self.get_restore_data_list(timestamp)
        site_data=restore_data['data_list']['site']
        for site in site_data:
            if site['project_type'] == 'Python':
                python_site_config=site['site_db_record']['project_config']
                requirement_path=json.loads(python_site_config)['requirement_path']
                vpath=json.loads(python_site_config)['vpath']
                if requirement_path:
                    pip3_path=vpath + "/bin/pip3"
                    pip2_path=vpath + "/bin/pip2"
                    if os.path.exists(pip3_path):
                        pip_install_cmd="{} install -r {}".format(pip3_path,requirement_path)
                    elif os.path.exists(pip2_path):
                        pip_install_cmd="{} install -r {}".format(pip2_path,requirement_path)
                    public.ExecShell(pip_install_cmd)
        self.print_log("站点Python依赖还原完成",'restore')

    def test_get_web_conf(self,site_name:str):
        conf_list=os.listdir("/www/server/panel/vhost/nginx/")
        for conf_name in conf_list:
            if conf_name.endswith(".conf"):
                if site_name in conf_name:
                    print(conf_name)
                    return True
        return False

    def backup_web_conf(self, site_name: str, conf_backup_path: str) -> None:
        """备份网站配置文件
        
        Args:
            site_name: 网站名称
            conf_backup_path: 配置文件备份路径
        """
        # 定义需要备份的配置文件和路径映射
        conf_paths = {
            'cert': "/www/server/panel/vhost/cert/{site_name}".format(site_name=site_name),
            'rewrite': "/www/server/panel/vhost/rewrite/{site_name}.conf".format(site_name=site_name),
            'nginx': {
                'main': "/www/server/panel/vhost/nginx/{site_name}.conf".format(site_name=site_name),
                'redirect': "/www/server/panel/vhost/nginx/redirect/{site_name}".format(site_name=site_name),
                'proxy': "/www/server/panel/vhost/nginx/proxy/{site_name}".format(site_name=site_name),
                'dir_auth': "/www/server/panel/vhost/nginx/dir_auth/{site_name}".format(site_name=site_name)
            },
            'apache': {
                'main': "/www/server/panel/vhost/apache/{site_name}.conf".format(site_name=site_name),
                'redirect': "/www/server/panel/vhost/apache/redirect/{site_name}".format(site_name=site_name),
                'proxy': "/www/server/panel/vhost/apache/proxy/{site_name}".format(site_name=site_name),
                'dir_auth': "/www/server/panel/vhost/apache/dir_auth/{site_name}".format(site_name=site_name)
            }
        }

        # 备份证书
        if os.path.exists(conf_paths['cert']):
            public.ExecShell(f"mkdir -p {conf_backup_path}cert/")
            public.ExecShell(f"\cp -rpa {conf_paths['cert']} {conf_backup_path}cert/")
        
        # 备份伪静态
        if os.path.exists(conf_paths['rewrite']):
            public.ExecShell(f"\cp -rpa {conf_paths['rewrite']} {conf_backup_path}rewrite")

        rewrite_file_list = os.listdir("/www/server/panel/vhost/rewrite/")
        for rewrite_file in rewrite_file_list:
            if rewrite_file.endswith(".conf"):  
                if site_name in rewrite_file:
                    public.ExecShell(f"\cp -rpa /www/server/panel/vhost/rewrite/{rewrite_file} {conf_backup_path}rewrite")
        
        # 备份nginx配置
        nginx_paths = conf_paths['nginx']
        if os.path.exists(nginx_paths['main']):
            public.ExecShell(f"\cp -rpa {nginx_paths['main']} {conf_backup_path}nginx/")
        if not os.path.exists(nginx_paths['main']):
            print(site_name)
            web_conf_list=os.listdir("/www/server/panel/vhost/nginx/")
            for web_conf_name in web_conf_list:
                if web_conf_name.endswith(".conf"):
                    if site_name in web_conf_name:
                        public.ExecShell(f"\cp -rpa /www/server/panel/vhost/nginx/{web_conf_name} {conf_backup_path}nginx/")


        if os.path.exists(nginx_paths['redirect']):
            public.ExecShell(f"mkdir -p {conf_backup_path}nginx/redirect/{site_name}/")
            public.ExecShell(f"\cp -rpa {nginx_paths['redirect']}/* {conf_backup_path}nginx/redirect/{site_name}/")
        
        if os.path.exists(nginx_paths['proxy']):
            public.ExecShell(f"mkdir -p {conf_backup_path}nginx/proxy/{site_name}/")
            public.ExecShell(f"\cp -rpa {nginx_paths['proxy']}/* {conf_backup_path}nginx/proxy/{site_name}/")
        
        if os.path.exists(nginx_paths['dir_auth']):
            public.ExecShell(f"mkdir -p {conf_backup_path}nginx/dir_auth/{site_name}/")
            public.ExecShell(f"\cp -rpa {nginx_paths['dir_auth']}/* {conf_backup_path}nginx/dir_auth/{site_name}/")
        
        # 备份apache配置
        apache_paths = conf_paths['apache']
        if os.path.exists(apache_paths['main']):
            public.ExecShell(f"\cp -rpa {apache_paths['main']} {conf_backup_path}apache/")

        if not os.path.exists(apache_paths['main']):
            web_conf_list=os.listdir("/www/server/panel/vhost/apache/")
            for web_conf_name in web_conf_list:
                if web_conf_name.endswith(".conf"):
                    if site_name in web_conf_name:
                        public.ExecShell(f"\cp -rpa /www/server/panel/vhost/apache/{web_conf_name} {conf_backup_path}apache/")
        
        if os.path.exists(apache_paths['redirect']):
            public.ExecShell(f"mkdir -p {conf_backup_path}apache/redirect/{site_name}/")
            public.ExecShell(f"\cp -rpa {apache_paths['redirect']}/* {conf_backup_path}apache/redirect/{site_name}/")
        
        if os.path.exists(apache_paths['proxy']):
            public.ExecShell(f"mkdir -p {conf_backup_path}apache/proxy/{site_name}/")
            public.ExecShell(f"\cp -rpa {apache_paths['proxy']}/* {conf_backup_path}apache/proxy/{site_name}/")
        
        if os.path.exists(apache_paths['dir_auth']):
            public.ExecShell(f"mkdir -p {conf_backup_path}apache/dir_auth/{site_name}/")
            public.ExecShell(f"\cp -rpa {apache_paths['dir_auth']}/* {conf_backup_path}apache/dir_auth/{site_name}/")

    

    def restore_web_conf(self, site_name: str, conf_backup_path: str) -> None:
        """还原网站配置文件
        
        Args:
            site_name: 网站名称
            conf_backup_path: 配置文件备份路径
        """
        # 定义需要还原的配置文件和路径映射
        conf_paths = {
            'cert': "/www/server/panel/vhost/cert/{site_name}".format(site_name=site_name),
            'rewrite': "/www/server/panel/vhost/rewrite/{site_name}.conf".format(site_name=site_name),
            'nginx': {
                'main': "/www/server/panel/vhost/nginx/{site_name}.conf".format(site_name=site_name),
                'redirect': "/www/server/panel/vhost/nginx/redirect/{site_name}".format(site_name=site_name),
                'proxy': "/www/server/panel/vhost/nginx/proxy/{site_name}".format(site_name=site_name)
            },
            'apache': {
                'main': "/www/server/panel/vhost/apache/{site_name}.conf".format(site_name=site_name),
                'redirect': "/www/server/panel/vhost/apache/redirect/{site_name}".format(site_name=site_name),
                'proxy': "/www/server/panel/vhost/apache/proxy/{site_name}".format(site_name=site_name)
            }
        }
        
        # 还原证书
        if os.path.exists(f"{conf_backup_path}cert"):
            public.ExecShell(f"\cp -rpa {conf_backup_path}cert {conf_paths['cert']}")
        
        # 还原伪静态
        if os.path.exists(f"{conf_backup_path}rewrite"):
            public.ExecShell(f"\cp -rpa {conf_backup_path}rewrite {conf_paths['rewrite']}")
        
        # 还原nginx配置
        if os.path.exists(f"{conf_backup_path}nginx"):
            public.ExecShell(f"\cp -rpa {conf_backup_path}nginx {conf_paths['nginx']['main']}")
        if os.path.exists(f"{conf_backup_path}nginx/redirect"):
            public.ExecShell(f"\cp -rpa {conf_backup_path}nginx/redirect {conf_paths['nginx']['redirect']}")
        if os.path.exists(f"{conf_backup_path}nginx/proxy"):
            public.ExecShell(f"\cp -rpa {conf_backup_path}nginx/proxy {conf_paths['nginx']['proxy']}")
        
        # 还原apache配置
        if os.path.exists(f"{conf_backup_path}apache"):
            public.ExecShell(f"\cp -rpa {conf_backup_path}apache {conf_paths['apache']['main']}")
        if os.path.exists(f"{conf_backup_path}apache/redirect"):
            public.ExecShell(f"\cp -rpa {conf_backup_path}apache/redirect {conf_paths['apache']['redirect']}")
        if os.path.exists(f"{conf_backup_path}apache/proxy"):
            public.ExecShell(f"\cp -rpa {conf_backup_path}apache/proxy {conf_paths['apache']['proxy']}")


    def restore_site_data(self, timestamp: str) -> None:
        """还原站点数据
        
        Args:
            timestamp: 备份时间戳
        """

        restore_data=self.get_restore_data_list(timestamp)
        site_backup_path=self.base_path + "/{timestamp}_backup/site/".format(timestamp=timestamp)

        self.restore_site_config(site_backup_path)


        if not os.path.exists(site_backup_path):
            self.print_log(f"站点备份目录不存在: {site_backup_path}", 'restore')
            return
        
        self.print_log("====================================================","restore")
        self.print_log("开始还原站点数据", 'restore')
        # 还原每个站点)
        for site in restore_data['data_list']['site']:
            try:   
                site['restore_status'] = 1
                self.update_restore_data_list(timestamp, restore_data)
                site_name = site['name']
                log_str="还原{}项目：{}".format(site['project_type'],site['name'])
                self.print_log(log_str,'restore')
                

                # # 还原数据库记录
                # if 'site_db_record' in site:
                #     print(site['site_db_record'])
                #     self.restore_site_db_data(site['site_db_record'])
                
                # # 还原域名记录
                # if 'domain_db_record' in site:
                #     import db
                #     domain_sql = db.Sql()
                #     domain_sql.table('domain')
                #     if 'id' in site['domain_db_record']:
                #         del site['domain_db_record']['id']
                #     domain_sql.insert(site['domain_db_record'])
                
                # 还原站点文件
                last_path = site['last_path']
                site_path = site['path']
                site_zip = site_backup_path + last_path + ".zip"

                if os.path.exists(site_zip):
                    public.ExecShell(f"cd {site_backup_path} && unzip -o {last_path}.zip")

                site_data_path=site_backup_path + last_path
                if os.path.exists(site_data_path):
                    site_parent_path = os.path.dirname(site_path)
                    if not os.path.exists(site_parent_path):
                        public.ExecShell("mkdir -p {}".format(site_parent_path))
                    public.ExecShell("chown -R www:www {}".format(site_parent_path))
                    public.ExecShell("chmod -R 755 {}".format(site_parent_path))
                    public.ExecShell("cd {} && mv {} {}".format(site_backup_path,last_path,site_parent_path))


                #     # 设置站点数据类型
                #     site_data_type = "directory" if os.path.isdir(site_data_path) else "file"
                
                #还原配置文件
                site_name=site['name']
                site_conf_zip = site_backup_path + site_name + "_conf.zip"
                if os.path.exists(site_conf_zip):
                    public.ExecShell("cd {site_backup_path} && unzip -o {site_name}_conf.zip".format(site_backup_path=site_backup_path,site_name=site_name))
                    conf_backup_path = "{site_backup_path}/{site_name}_conf/".format(site_backup_path=site_backup_path,site_name=site_name)
                    public.ExecShell("cd {site_backup_path} && \cp -rpa {site_name}_conf/*  /www/server/panel/vhost".format(site_backup_path=site_backup_path,site_name=site_name))
                    #self.restore_web_conf(site_name, conf_backup_path)
                
                new_log_str="{}项目：{} ✓".format(site['project_type'],site['name'])
                self.replace_log(log_str,new_log_str,'restore')
                site['restore_status'] = 2
                self.update_restore_data_list(timestamp, restore_data)
            except Exception as e:
                site['restore_status'] = 3
                self.update_restore_data_list(timestamp, restore_data)
                new_log_str="{}项目：{} 原因: {}".format(site['project_type'],site['name'],str(e))
                self.replace_log(log_str,new_log_str,'restore')
                continue
        #print(restore_data)
    
        self.print_log("站点数据还原完成", 'restore')
        self.restore_site_python_env(timestamp)


    def restore_site_db_data(self,site_db_record:dict):
        import db
        sql = db.Sql()
        sql.table('sites')
        if 'id' in site_db_record:
            del site_db_record['id']
            
        # 处理SQL关键字字段，防止语法错误
        # 'index'是SQL关键字，需要特殊处理
        if 'index' in site_db_record:
            # 如果index是None，转换为空字符串或0
            if site_db_record['index'] is None:
                site_db_record['index'] = ''
            # 或者使用引号或特殊标记包围它
            # sql._escape_index = True 
            
        # 打印SQL前的记录用于调试
        print("准备插入数据库的记录:", site_db_record)
            
        try:
            # 插入新记录
            sql.insert(site_db_record)
            print("站点数据库记录还原成功")
        except Exception as e:
            print(f"站点数据库记录还原失败: {str(e)}")
            # 尝试构建不带关键字的插入语句
            field_names = []
            field_values = []
            for key, value in site_db_record.items():
                if key != 'index':  # 跳过index字段
                    field_names.append(key)
                    field_values.append(value)
                    
            try:
                # 构建自定义SQL语句并执行
                fields_str = ', '.join([f"`{name}`" for name in field_names])
                placeholders = ', '.join(['%s'] * len(field_values))
                custom_sql = f"INSERT INTO sites ({fields_str}) VALUES ({placeholders})"
                sql.execute(custom_sql, tuple(field_values))
                print("使用自定义SQL语句站点数据库记录还原成功")
            except Exception as e2:
                print(f"自定义SQL还原站点数据库记录也失败: {str(e2)}")

    def backup_site_dir_auth(self,site_name:str):
        if os.path.exists(self.site_dir_auth_path):
            site_dir_auth_data=json.loads(public.ReadFile(self.site_dir_auth_path))
            if site_name in site_dir_auth_data:
                result = {site_name: site_dir_auth_data[site_name]}
                print(json.dumps(result))
                return result
        return False
    
    def restore_site_dir_auth(self,site_name:str,backup_data_path:str):
        if os.path.exists(backup_data_path):
            dir_auth_backup_data=json.loads(public.ReadFile(backup_data_path))
            if os.path.exists(self.site_dir_auth_path):
                site_dir_auth_data=json.loads(public.ReadFile(self.site_dir_auth_path))
                site_dir_auth_data[site_name] = dir_auth_backup_data[site_name]
                public.WriteFile(self.site_dir_auth_path,json.dumps(site_dir_auth_data))

    def backup_dir_pass(self,site_name:str,backup_data_path:str):
        if os.path.exists(self.site_dir_auth_path):
            site_dir_auth_data=json.loads(public.ReadFile(self.site_dir_auth_path))
            if site_name in site_dir_auth_data:
                result = {site_name: site_dir_auth_data[site_name]}
                print(json.dumps(result))
                return result
        return {}

    def backup_redirect_conf(self,site_name:str):
        if os.path.exists(self.redirect_conf_path):
            redirect_conf_data=json.loads(public.ReadFile(self.redirect_conf_path))
            for item in redirect_conf_data:
                if site_name in item['sitename']:
                    return item
        return False
    
    def restore_redirect_conf(self,site_name:str,backup_data_path:str):
        if os.path.exists(backup_data_path):
            redirect_conf_data=json.loads(public.ReadFile(backup_data_path))
            local_redirect_conf_data=[]
            if os.path.exists(self.redirect_conf_path):
                local_redirect_conf_data=json.loads(public.ReadFile(self.redirect_conf_path))
            data_exists=None
            for item in local_redirect_conf_data:
                if item['sitename'] == redirect_conf_data['sitename']:
                    data_exists=True
            if not data_exists:
                local_redirect_conf_data.append(redirect_conf_data)
            public.WriteFile(self.redirect_conf_path,json.dumps(local_redirect_conf_data))
        return False
    
    def backup_proxy_conf(self,site_name:str):
        if os.path.exists(self.proxy_conf_path):
            proxy_conf_data=json.loads(public.ReadFile(self.proxy_conf_path))
            for item in proxy_conf_data:
                if site_name in item['sitename']:
                    return item
        return False
    
    def restore_proxy_conf(self,site_name:str,backup_data_path:str):
        if os.path.exists(backup_data_path):
            proxy_conf_data=json.loads(public.ReadFile(backup_data_path))
            local_proxy_conf_data=[]
            if os.path.exists(self.proxy_conf_path):
                local_proxy_conf_data=json.loads(public.ReadFile(self.proxy_conf_path))
            data_exists=None
            for item in local_proxy_conf_data:
                if item['sitename'] == proxy_conf_data['sitename']:
                    data_exists=True
            if not data_exists:
                local_proxy_conf_data.append(proxy_conf_data)
            public.WriteFile(self.proxy_conf_path,json.dumps(local_proxy_conf_data))
        return False
                
if __name__ == '__main__':
    # 获取命令行参数
    if len(sys.argv) < 3:
        print("Usage: btpython backup_manager.py <method> <timestamp>")
        sys.exit(1)
    method_name = sys.argv[1]  # 方法名
    timestamp = sys.argv[2]    # IP地址     
    site_module = SiteModule()  # 实例化对象
    if hasattr(site_module, method_name):  # 检查方法是否存在
        method = getattr(site_module, method_name)  # 获取方法
        method(timestamp)  # 调用方法
    else:
        print(f"Error: 方法 '{method_name}' 不存在")