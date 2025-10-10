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
import re

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

if '/www/server/panel' not in sys.path:
    sys.path.insert(0, '/www/server/panel')



import public
from mod.project.backup_restore.base_util import BaseUtil
#from mod.project.backup_restore.data_manager import DataManager
from mod.project.backup_restore.config_manager import ConfigManager


class SoftModule(BaseUtil,ConfigManager):
    def __init__(self):
        self.base_path = '/www/backup/backup_restore'
        self.bakcup_task_json = self.base_path + '/backup_task.json'
    
    def get_install_type(self):
        if os.path.exists("/usr/bin/yum") or os.path.exists("/usr/bin/dnf") or os.path.exists("/usr/sbin/yum"):
            return 1
        elif os.path.exists("/usr/bin/apt") or os.path.exists("/usr/sbin/apt-get") or os.path.exists("/usr/bin/apt-get"):
            return 4
        else:
            return 0

    def get_web_server(self):
        if os.path.exists("/www/server/nginx/sbin/nginx"):
            nginx_version = public.ExecShell("nginx -v 2>&1")[0].replace("\n", "")
            version_match = re.search(r'nginx/(\d+\.\d+)', nginx_version)
            if version_match:
                nginx_version = version_match.group(1)
            
            result = {
                "name": "nginx",
                "version": nginx_version,
                "size": BaseUtil().get_file_size("/www/server/nginx/")
            }
            self.print_log("nginx {} ✓".format(nginx_version),'backup')
            return result
        pass
        
    def get_php_server(self):
        php_dir="/www/server/php"
        if os.path.exists(php_dir):
            phplist=[]
            for dir_name in os.listdir(php_dir):
                dir_path = dir_path = os.path.join(php_dir, dir_name)
                if os.path.isdir(dir_path) and os.path.exists(os.path.join(dir_path, 'bin/php')):
                    phplist.append(int(dir_name)) 
            
            result=[]
            for php_ver in phplist:
                php_ext=public.ExecShell("/www/server/php/{}/bin/php -m".format(php_ver))[0].split("\n")
                filtered_data = [item for item in php_ext if item not in ('[PHP Modules]', '[Zend Modules]', '')]
                php_result = {
                    "name": "php",
                    "version": php_ver,
                    "php_ext": filtered_data,
                    "size": BaseUtil().get_file_size("/www/server/php/{}".format(php_ver))
                }
                # 将PHP版本号转换为带小数点的格式
                if isinstance(php_ver, (int, str)) and len(str(php_ver)) == 2:
                    # 例如：54 -> 5.4, 70 -> 7.0
                    php_result['version'] = f"{str(php_ver)[0]}.{str(php_ver)[1]}"
                elif isinstance(php_ver, (int, str)) and len(str(php_ver)) == 3:
                    # 例如：82 -> 8.2
                    php_result['version'] = f"{str(php_ver)[0]}.{str(php_ver)[1:]}"
                result.append(php_result)
                self.print_log("php {} ✓".format(php_result['version']),'backup')
            return result
        return None

    def get_mysql_server(self):
        if os.path.exists("/www/server/mysql/bin/mysql"):
            if os.path.exists("/www/server/mysql/version.pl"):
                mysql_version=public.ReadFile("/www/server/mysql/version.pl").replace("\n", "")
            elif os.path.exists("/www/server/mysql/version_check.pl"):
                mysql_version=public.ExecShell("/www/server/mysql/version_check.pl")[0].replace("\n", "")

            match = re.search(r'10\.\d+', mysql_version)
            if match:
                version = match.group()
                type="mariadb"
                mysql_version=version
            else:
                type="mysql"
                mysql_version=mysql_version[0:3]
            result={
                "type": type,
                "version": mysql_version,
                "size": BaseUtil().get_file_size("/www/server/mysql/")
            }
            self.print_log("mysql {} ✓".format(mysql_version),'backup')
            return result
        else:
            return False

    def get_ftp_server(self,get=None):
        if os.path.exists("/www/server/pure-ftpd/bin/pure-pw"):
            size=BaseUtil().get_file_size("/www/server/pure-ftpd/")
            try:
                pure_ftp_port=public.ExecShell("cat /www/server/pure-ftpd/etc/pure-ftpd.conf | grep Bind|awk '{print $2}'")[0].replace("\n", "").replace("0.0.0.0,","")
                pure_ftp_port=int(pure_ftp_port)
            except:
                pure_ftp_port=21
            self.print_log("pure-ftpd {} ✓".format(pure_ftp_port),'backup')
            return {
                "name": "pure-ftpd",
                "version": "1.0.49",
                "size": size,
                "port": int(pure_ftp_port)
            }
        else:
            return None

    def get_jdk_list(self,get=None):
        java_dir="/www/server/java"
        if not os.path.exists(java_dir):
            return []
        jdk_list=[]
        for dir_name in os.listdir(java_dir):
            if "tar.gz" in dir_name:
                continue
            if not dir_name.startswith("jdk"):
                continue

            dir_path = os.path.join(java_dir, dir_name)
            if os.path.isdir(dir_path):
                size=BaseUtil().get_file_size(os.path.join(java_dir, dir_name))
                dir_name=dir_name.replace("jdk-","")
                jdk_list.append({
                    "name": "jdk",
                    "version": dir_name,
                    "size": size
                })
                self.print_log("jdk {} ✓".format(dir_name),'backup')
        return jdk_list
    
    def get_tomcat_list(self,get=None):
        from mod.project.java.projectMod import main as java_mod
        args = public.dict_obj()
        try:
            tomcat_list = []
            tomcat_info = java_mod().get_tomcat_list(args)
            for tomcat_id, tomcat_data in tomcat_info.items():
                tomcat_list.append({
                    "name": "tomcat",
                    "version": tomcat_data['version'],
                    "size": BaseUtil().get_file_size(tomcat_data['path']),
                    "path": tomcat_data['path'],
                    "port": tomcat_data['port'],
                    "type": tomcat_data['type'],
                    "user": tomcat_data['user'],
                    "auto_start": tomcat_data['auto_start'],
                    "ps": tomcat_data['ps'],
                    "jdk_path": tomcat_data['jdk_path'],
                    "tomcat_name": tomcat_id
                })
                self.print_log("tomcat {} ✓".format(tomcat_data['version']),'backup')
            return tomcat_list
        except:
            return None

    
    def get_node_list(self):
        node_dir="/www/server/nodejs"
        if not os.path.exists(node_dir):
            return None
        node_list=[]

        result=[]
        for dir_name in os.listdir(node_dir):
            if re.match(r"^v[1-9]\d*(\.\d+)*$", dir_name):
                node_list.append(dir_name)

        for node_ver in node_list:
            node_ver_path=os.path.join(node_dir,node_ver)
            node_mod_path=os.path.join(node_ver_path,"lib","node_modules")
            if os.path.isdir(node_mod_path):
                mod_list=os.listdir(node_mod_path)
            else:
                mod_list=[]
            node_result = {
                "name": "node",
                "version": node_ver,
                "mod_list": mod_list,
                "size": BaseUtil().get_file_size("/www/server/nodejs/{}".format(node_ver))
            }
            result.append(node_result)
            self.print_log("node {} ✓".format(node_ver),'backup')
        return result

    def get_golang_list(self,get=None):
        try:
            from BTPanel import cache
            from projectModel.btpygvm import pygvm
        except:
            return None
        
        installed_list=pygvm.api_ls()
        try:
            used_version=pygvm.now_version
        except:
            used_version=None
        result=[]
        for installed_ver in installed_list:
            if os.path.exists("/usr/local/btgojdk/{}".format(installed_ver)):
                size=BaseUtil().get_file_size("/usr/local/btgojdk/{}".format(installed_ver))
            else:
                size=0
            result.append({
                "name": "golang",
                "version": installed_ver,
                "used": used_version,
                "size": size
            })
            self.print_log("golang {} ✓".format(installed_ver),'backup')
        return result
    
        

    def get_pyenv_list(self):
        pyenv_path="/www/server/panel/data/project_env.json"

    
    def get_redis_server(self):
        if os.path.exists("/www/server/redis/src/redis-server") and os.path.exists("/www/server/redis/version.pl"):
            redis_version=public.ReadFile("/www/server/redis/version.pl")
            size=BaseUtil().get_file_size("/www/server/redis/")
            self.print_log("redis {} ✓".format(redis_version[0:3]),'backup')
            return {
                "name": "redis",
                "version": redis_version[0:3],
                "size": size
            }
        else:
            return None
        
    def get_memcached_server(self):
        if os.path.exists("/usr/local/memcached/bin/memcached"):
            size=BaseUtil().get_file_size("/usr/local/memcached/")
            self.print_log("memcached {} ✓".format("1.6.12"),'backup')
            return {
                "name": "memcached",
                "version": "1.6.12",
                "size": size
            }
        else:
            return None
        
    def get_dotnet_list(self):
        dotnet_path="/www/server/dotnet"
        if not os.path.exists(dotnet_path):
            return None
        dotnet_list=[]
        for dir_name in os.listdir(dotnet_path):
            if dir_name[0].isdigit():
                if os.path.exists(os.path.join(dotnet_path, dir_name,"dotnet")):
                    size=BaseUtil().get_file_size(os.path.join(dotnet_path, dir_name))
                    dotnet_list.append({
                        "name": "dotnet",
                        "version": dir_name,
                        "size": size
                    })
                    self.print_log("dotnet {} ✓".format(dir_name),'backup')
        return dotnet_list

    def get_mongodb_server(self):
        if os.path.exists("/www/server/mongodb/bin/mongo") and os.path.exists("/www/server/mongodb/version.pl"):
            mongodb_version=public.ReadFile("/www/server/mongodb/version.pl")
            size=BaseUtil().get_file_size("/www/server/mongodb/")
            self.print_log("mongodb {} ✓".format(mongodb_version[0:3]),'backup')
            return {
                "name": "mongodb",
                "version": mongodb_version[0:3],
                "size": size
            }
        else:
            return None

    def get_pgsql_server(self):
        if os.path.exists("/www/server/pgsql/bin/pg_config"):
            pgsql_version=public.ExecShell("/www/server/pgsql/bin/pg_config --version")[0].replace("\n", "").split(" ")[1]
            size=BaseUtil().get_file_size("/www/server/pgsql/")
            self.print_log("pgsql {} ✓".format(pgsql_version),'backup')
            return {
                "name": "pgsql",
                "version": pgsql_version,
                "size": size
            }
        else:
            return None
    def get_phpmyadmin_version(self):
        if os.path.exists("/www/server/phpmyadmin/version.pl"):
            phpmyadmin_version=public.ReadFile("/www/server/phpmyadmin/version.pl").replace("\n", "")
            size=BaseUtil().get_file_size("/www/server/phpmyadmin/")
            self.print_log("phpmyadmin {} ✓".format(phpmyadmin_version),'backup')
            return {
                "name": "phpmyadmin",
                "version": phpmyadmin_version,
                "size": size
            }
        else:
            return None
    
    def get_python_list(self,get=None):
        if not os.path.exists("/www/server/pyporject_evn/versions"):
            return None
        python_list=[]
        for python_ver in os.listdir("/www/server/pyporject_evn/versions"):
            if os.path.exists("/www/server/pyporject_evn/versions/{}/bin/python3".format(python_ver)) or os.path.exists("/www/server/pyporject_evn/versions/{}/bin/python2".format(python_ver)):
                python_list.append({
                    "name": "python",
                    "version": python_ver,
                    "size": BaseUtil().get_file_size("/www/server/pyporject_evn/versions/{}".format(python_ver))
                })
                self.print_log("python {} ✓".format(python_ver),'backup')
            return python_list
            
    def get_soft_data(self,timestamp=None):
        self.print_log("====================================================","backup")
        self.print_log("开始备份软件信息","backup")
        result = {
            "web_server": self.get_web_server(),
            "php_server": self.get_php_server(),
            "mysql_server": self.get_mysql_server(),
            "ftp_server": self.get_ftp_server(),
            "jdk_list": self.get_jdk_list(),
            "node_list": self.get_node_list(),
            "golang_list": self.get_golang_list(),
            "dotnet_list": self.get_dotnet_list(),
            "tomcat_list": self.get_tomcat_list(),
            "python_list": self.get_python_list(),
            "redis_server": self.get_redis_server(),
            "memcached_server": self.get_memcached_server(),
            "mongodb_server": self.get_mongodb_server(),
            "pgsql_server": self.get_pgsql_server(),
            "phpmyadmin_version": self.get_phpmyadmin_version()
        }
        public.WriteFile("/root/soft.json",json.dumps(result))
        self.print_log("软件信息备份完成",'backup')
        return result

    def backup_soft_data(self,timestamp):
        pass
    
    def restore_soft_data(self,timestamp):
        pass

    def install_web_server(self,timestamp):
        restore_data=self.get_restore_data_list(timestamp)
        web_server=restore_data['data_list']['soft']['web_server']
        install_type=self.get_install_type()
        print(install_type)
        if web_server['name'] == 'nginx':
            log_str="开始安装nginx-{}".format(web_server['version'])
            self.print_log(log_str,"restore")
            restore_data['data_list']['soft']['status']['status'] = 1
            restore_data['data_list']['soft']['status']['name'] = 'nginx'
            restore_data['data_list']['soft']['status']['version'] = web_server['version']
            self.update_restore_data_list(timestamp, restore_data)
            result=public.ExecShell("cd /www/server/panel/install && wget -O nginx.sh http://download.bt.cn/install/{}/nginx.sh && bash nginx.sh install {}".format(install_type,web_server['version']))
        elif web_server['name'] == 'apache':
            self.print_log("开始安装apache服务","restore")
            restore_data['data_list']['soft']['status']['status'] = 1
            restore_data['data_list']['soft']['status']['name'] = 'apache'
            restore_data['data_list']['soft']['status']['version'] = web_server['version']
            self.update_restore_data_list(timestamp, restore_data)
            result=public.ExecShell("cd /www/server/panel/install && wget -O apache.sh http://download.bt.cn/install/{}/apache.sh && bash apache.sh install {}".format(install_type,web_server['version']))
        if web_server['name'] == 'nginx' and os.path.exists("/www/server/nginx/sbin/nginx"):
            new_log_str="{}-{} ✓".format(web_server['name'],web_server['version'])
            self.replace_log(log_str,new_log_str,"restore")
        elif web_server['name'] == 'apache' and os.path.exists("/www/server/apache/bin/httpd"):
            new_log_str="{}-{} ✓".format(web_server['name'],web_server['version'])
            self.replace_log(log_str,new_log_str,"restore")
        else:
            combined_output = (result[0] + result[1]).splitlines()
            err_msg = '\n'.join(combined_output[-10:])
            new_log_str="{}-{} ✗ 安装失败 原因： {} \n 请尝试在还原任务结束后在软件商店重新安装web服务器".format(web_server['name'],web_server['version'],err_msg)
            self.replace_log(log_str,new_log_str,"restore")
        #self.print_log("web服务器安装完成","restore")
    
    def install_php_server(self,timestamp):
        restore_data=self.get_restore_data_list(timestamp)
        php_server=restore_data['data_list']['soft']['php_server']
        install_type=self.get_install_type()
        for php_ver in php_server:
            php_ver=php_ver['version']
            restore_data['data_list']['soft']['status']['status'] = 1
            restore_data['data_list']['soft']['status']['name'] = 'php'
            restore_data['data_list']['soft']['status']['version'] = php_ver
            self.update_restore_data_list(timestamp, restore_data)
            log_str="开始安装php-{}".format(php_ver)
            self.print_log(log_str,"restore")
            path_ver=php_ver.replace('.','')
            if os.path.exists("/www/server/php/{}".format(path_ver)):
                new_log_str="php-{} ✓".format(php_ver)
                self.replace_log(log_str,new_log_str,"restore")
                continue
            # 将PHP版本号转换为带小数点的格式
            # if isinstance(php_ver, (int, str)) and len(str(php_ver)) == 2:
            #     php_ver = f"{str(php_ver)[0]}.{str(php_ver)[1]}"
            # elif isinstance(php_ver, (int, str)) and len(str(php_ver)) == 3:
            #     php_ver = f"{str(php_ver)[0]}.{str(php_ver)[1:]}"
            result=public.ExecShell("cd /www/server/panel/install && wget -O php.sh http://download.bt.cn/install/{}/php.sh && bash php.sh install {}".format(install_type,php_ver))
            if not os.path.exists("/www/server/php/{}".format(path_ver)):
                combined_output = (result[0] + result[1]).splitlines()
                err_msg = '\n'.join(combined_output[-10:])
                new_log_str="php-{} ✗ 安装失败 原因：{} \n 请尝试在还原任务结束后在软件商店重新安装php".format(php_ver,err_msg)
                self.replace_log(log_str,new_log_str,"restore")
            else:
                new_log_str="php-{} ✓".format(php_ver)
                self.replace_log(log_str,new_log_str,"restore")

    def install_php_ext(self,timestamp):
        restore_data=self.get_restore_data_list(timestamp)
        php_server_data=restore_data['data_list']['soft']['php_server']
        for php_server in php_server_data:
            php_ver=php_server['version'].replace('.','')
            php_ext=php_server['php_ext']
            local_php_ext=public.ExecShell("/www/server/php/{}/bin/php -m".format(php_ver))[0].split("\n")
            filtered_data = [item for item in local_php_ext if item not in ('[PHP Modules]', '[Zend Modules]', '')]
            for ext in php_ext:
                if ext not in filtered_data:
                    ext=ext.lower()
                    log_str="开始安装php-{}扩展-{}".format(php_ver,ext)

                    install_cmd="cd /www/server/panel/install && wget -O {ext}.sh http://download.bt.cn/install/1/{ext}.sh && bash {ext}.sh install {php_ver}".format(ext=ext,php_ver=php_ver)
                    if 'OPcache' in ext:
                        install_cmd="cd /www/server/panel/install && wget -O opcache.sh http://download.bt.cn/install/1/opcache.sh && bash opcache.sh install {php_ver}".format(php_ver=php_ver)
                    
                    if 'SourceGuardian' in ext:
                        install_cmd="cd /www/server/panel/install && wget -O sg16.sh http://download.bt.cn/install/1/sg16.sh && bash sg16.sh install {php_ver}".format(php_ver=php_ver)

                    if 'swoole' in ext:
                        if int(php_ver) >= 81:
                            install_cmd="cd /www/server/panel/install && wget -O swoole6.sh http://download.bt.cn/install/1/swoole6.sh && bash swoole6.sh install {php_ver}".format(php_ver=php_ver)
                        elif int(php_ver) >= 80:
                            install_cmd="cd /www/server/panel/install && wget -O swoole5.sh http://download.bt.cn/install/1/swoole5.sh && bash swoole5.sh install {php_ver}".format(php_ver=php_ver)
                        else:
                            install_cmd="cd /www/server/panel/install && wget -O swoole4.sh http://download.bt.cn/install/1/swoole4.sh && bash swoole4.sh install {php_ver}".format(php_ver=php_ver)

                    result=public.ExecShell(install_cmd)
                    new_log_str="php-{}扩展-{} ✓".format(php_ver,ext)
                    self.replace_log(log_str,new_log_str,"restore")


    def install_node(self,timestamp):
        restore_data=self.get_restore_data_list(timestamp)
        node_list=restore_data['data_list']['soft']['node_list']
        for node_data in node_list:
            node_ver=node_data['version']
            log_str="开始安装node-{}".format(node_ver)
            self.print_log(log_str,"restore")
            if os.path.exists("/www/server/nodejs/{}".format(node_ver)):
                new_log_str="node-{} ✓".format(node_ver)
                self.replace_log(log_str,new_log_str,"restore")
                continue
            result=public.ExecShell("cd /www/server/panel/install && wget -O node_plugin_install.sh http://download.bt.cn/install/0/node_plugin_install.sh && bash node_plugin_install.sh {}".format(node_ver))

            for mod_list in node_data['mod_list']:
                mod_name=mod_list
                mod_shell='''
export PATH
export HOME=/root
export NODE_PATH="/www/server/nodejs/{node_ver}/etc/node_modules"
/www/server/nodejs/{node_ver}//bin/npm config set registry https://registry.npmmirror.com/
/www/server/nodejs/{node_ver}//bin/npm config set prefix /www/server/nodejs/{node_ver}/
/www/server/nodejs/{node_ver}//bin/npm config set cache /www/server/nodejs/{node_ver}//cache
/www/server/nodejs/{node_ver}//bin/npm config set strict-ssl false
/www/server/nodejs/{node_ver}//bin/yarn config set registry https://registry.npmmirror.com/
/www/server/nodejs/{node_ver}/bin/npm install {mod_name} -g &> /www/server/panel/plugin/nodejs/exec.log           
                '''.format(node_ver=node_ver,mod_name=mod_name)
                result=public.ExecShell(mod_shell)
                if os.path.exists("/www/server/nodejs/{}".format(node_ver)):
                    new_log_str="node-{} ✓".format(node_ver)
                    self.replace_log(log_str,new_log_str,"restore")
                else:
                    combined_output = (result[0] + result[1]).splitlines()
                    err_msg = '\n'.join(combined_output[-10:])
                    new_log_str="node-{} ✗ 安装失败 原因：{} \n 请尝试在还原任务结束后在软件商店重新安装node".format(node_ver,err_msg)
                    self.replace_log(log_str,new_log_str,"restore")

    def install_mysql_server(self,timestamp):
        restore_data=self.get_restore_data_list(timestamp)
        mysql_server=restore_data['data_list']['soft']['mysql_server']
        install_type=self.get_install_type()
        if mysql_server['type'] == 'mariadb':
            pass
        elif mysql_server['type'] == 'mysql':
            log_str="开始安装mysql-{}".format(mysql_server['version'])
            self.print_log(log_str,"restore")
            if os.path.exists("/www/server/mysql/bin/mysql"):
                new_log_str="mysql-{} ✓".format(mysql_server['version'])
                self.replace_log(log_str,new_log_str,"restore")
                return
            result=public.ExecShell("cd /www/server/panel/install && wget -O mysql.sh http://download.bt.cn/install/{}/mysql.sh && bash mysql.sh install {}".format(install_type,mysql_server['version']))
            if os.path.exists("/www/server/mysql/bin/mysql"):
                new_log_str="mysql-{} ✓".format(mysql_server['version'])
                self.replace_log(log_str,new_log_str,"restore")
            else:
                combined_output = (result[0] + result[1]).splitlines()
                err_msg = '\n'.join(combined_output[-10:])
                new_log_str="mysql-{} ✗ 安装失败 原因：{} \n 请尝试在还原任务结束后在软件商店重新安装mysql".format(mysql_server['version'],err_msg)
                self.replace_log(log_str,new_log_str,"restore")

    def install_jdk(self,timestamp):
        restore_data=self.get_restore_data_list(timestamp)
        jdk_list=restore_data['data_list']['soft']['jdk_list']
        install_type=self.get_install_type()
        for jdk in jdk_list:
            jdk_ver=jdk['version']
            log_str="开始安装jdk-{}".format(jdk_ver)
            self.print_log(log_str,"restore")
            if os.path.exists("/www/server/java/{}".format(jdk_ver)):
                new_log_str="jdk-{} ✓".format(jdk_ver)
                self.replace_log(log_str,new_log_str,"restore")
                continue
            restore_data['data_list']['soft']['status']['status'] = 1
            restore_data['data_list']['soft']['status']['name'] = 'jdk'
            restore_data['data_list']['soft']['status']['version'] = jdk_ver
            self.update_restore_data_list(timestamp, restore_data)
            if "jdk" in jdk_ver:
                result=public.ExecShell("cd /www/server/panel/install && wget -O jdk.sh http://download.bt.cn/install/0/jdk.sh && bash jdk.sh install {}".format(jdk_ver))
            else:
                result=public.ExecShell("cd /www/server/panel/install && wget -O jdk.sh http://download.bt.cn/install/0/jdk.sh && bash jdk.sh install jdk-{}".format(jdk_ver))
            if os.path.exists("/www/server/java/{}".format(jdk_ver)) or os.path.exists("/www/server/java/jdk-{}".format(jdk_ver)): 
                new_log_str="jdk-{} ✓".format(jdk_ver)
                self.replace_log(log_str,new_log_str,"restore")
            else:
                combined_output = (result[0] + result[1]).splitlines()
                err_msg = '\n'.join(combined_output[-10:])
                new_log_str="jdk-{} ✗ 安装失败 原因：{} \n 请尝试在还原任务结束后在软件商店重新安装jdk".format(jdk_ver,err_msg)
                self.replace_log(log_str,new_log_str,"restore")

    def install_mongodb_server(self,timestamp):
        restore_data=self.get_restore_data_list(timestamp)
        mongodb_server=restore_data['data_list']['soft']['mongodb_server']
        install_type=self.get_install_type()
        log_str="开始安装mongodb-{}".format(mongodb_server['version'])
        self.print_log(log_str,"restore")
        if os.path.exists("/www/server/mongodb/bin/mongo") and os.path.exists("/www/server/mongodb/version.pl"):
            new_log_str="mongodb-{} ✓".format(mongodb_server['version'])
            self.replace_log(log_str,new_log_str,"restore")
            return
        
        restore_data['data_list']['soft']['status']['status'] = 1
        restore_data['data_list']['soft']['status']['name'] = 'mongodb'
        restore_data['data_list']['soft']['status']['version'] = mongodb_server['version']
        self.update_restore_data_list(timestamp, restore_data)
        result=public.ExecShell("cd /www/server/panel/install && wget -O mongodb.sh http://download.bt.cn/install/0/mongodb.sh && bash mongodb.sh install {}".format(mongodb_server['version']))
        if os.path.exists("/www/server/mongodb/bin/mongo"):
            new_log_str="mongodb-{} ✓".format(mongodb_server['version'])
            self.replace_log(log_str,new_log_str,"restore")
        else:
            combined_output = (result[0] + result[1]).splitlines()
            err_msg = '\n'.join(combined_output[-10:])
            new_log_str="mongodb-{} ✗ 安装失败 原因：{} \n 请尝试在还原任务结束后在软件商店重新安装mongodb".format(mongodb_server['version'],err_msg)
            self.replace_log(log_str,new_log_str,"restore")

    def install_memcached_server(self,timestamp):
        restore_data=self.get_restore_data_list(timestamp)
        memcached_server=restore_data['data_list']['soft']['memcached_server']
        install_type=self.get_install_type()
        log_str="开始安装memcached-{}".format(memcached_server['version'])
        self.print_log(log_str,"restore")
        if os.path.exists("/usr/local/memcached/bin/memcached"):
            new_log_str="memcached-{} ✓".format(memcached_server['version'])
            self.replace_log(log_str,new_log_str,"restore")
            return
        restore_data['data_list']['soft']['status']['status'] = 1
        restore_data['data_list']['soft']['status']['name'] = 'memcached'
        restore_data['data_list']['soft']['status']['version'] = memcached_server['version']
        self.update_restore_data_list(timestamp, restore_data)
        result=public.ExecShell("cd /www/server/panel/install && wget -O memcached.sh http://download.bt.cn/install/0/memcached.sh && bash memcached.sh install")
        if os.path.exists("/usr/local/memcached/bin/memcached"):
            new_log_str="memcached-{} ✓".format(memcached_server['version'])
            self.replace_log(log_str,new_log_str,"restore")
        else:
            combined_output = (result[0] + result[1]).splitlines()
            err_msg = '\n'.join(combined_output[-10:])
            new_log_str="memcached-{} ✗ 安装失败 原因：{} \n 请尝试在还原任务结束后在软件商店重新安装memcached".format(memcached_server['version'],err_msg)
            self.replace_log(log_str,new_log_str,"restore")

    def install_redis_server(self,timestamp):
        restore_data=self.get_restore_data_list(timestamp)
        redis_server=restore_data['data_list']['soft']['redis_server']
        install_type=self.get_install_type()
        log_str="开始安装redis-{}".format(redis_server['version'])
        self.print_log(log_str,"restore")
        if os.path.exists("/www/server/redis/src/redis-server") and os.path.exists("/www/server/redis/version.pl"):
            new_log_str="redis-{} ✓".format(redis_server['version'])
            self.replace_log(log_str,new_log_str,"restore")
            return
        restore_data['data_list']['soft']['status']['status'] = 1
        restore_data['data_list']['soft']['status']['name'] = 'redis'
        restore_data['data_list']['soft']['status']['version'] = redis_server['version']
        self.update_restore_data_list(timestamp, restore_data)
        result=public.ExecShell("cd /www/server/panel/install && wget -O redis.sh http://download.bt.cn/install/0/redis.sh && bash redis.sh install {}".format(redis_server['version']))
        if os.path.exists("/www/server/redis/src/redis-cli"):
            new_log_str="redis-{} ✓".format(redis_server['version'])
            self.replace_log(log_str,new_log_str,"restore")
        else:
            combined_output = (result[0] + result[1]).splitlines()
            err_msg = '\n'.join(combined_output[-10:])
            new_log_str="redis-{} ✗ {}".format(redis_server['version'],err_msg)
            self.replace_log(log_str,new_log_str,"restore")
    
    def install_pgsql_server(self,timestamp):
        restore_data=self.get_restore_data_list(timestamp)
        pgsql_server=restore_data['data_list']['soft']['pgsql_server']
        log_str="开始安装pgsql-{}".format(pgsql_server['version'])
        self.print_log(log_str,"restore")
        if os.path.exists("/www/server/pgsql/bin/pg_config"):
            new_log_str="pgsql-{} ✓".format(pgsql_server['version'])
            self.replace_log(log_str,new_log_str,"restore")
            return
        restore_data['data_list']['soft']['status']['status'] = 1
        restore_data['data_list']['soft']['status']['name'] = 'pgsql'
        restore_data['data_list']['soft']['status']['version'] = pgsql_server['version']
        self.update_restore_data_list(timestamp, restore_data)

        down_file="postgresql-{pgsql_version}.tar.gz".format(pgsql_version=pgsql_server['version'])
        down_url="http://download.bt.cn/src/postgresql-{pgsql_version}.tar.gz".format(pgsql_version=pgsql_server['version'])

        result=public.ExecShell("cd /www/server/panel/install && wget -O pgsql_install.sh http://download.bt.cn/install/0/pgsql_install.sh && bash pgsql_install.sh {} {}".format(down_file,down_url))
        if os.path.exists("/www/server/pgsql/bin/psql"):
            new_log_str="pgsql-{} ✓".format(pgsql_server['version'])
            self.replace_log(log_str,new_log_str,"restore")
        else:
            combined_output = (result[0] + result[1]).splitlines()
            err_msg = '\n'.join(combined_output[-10:])
            new_log_str="pgsql-{} ✗ {}".format(pgsql_server['version'],err_msg)
            self.replace_log(log_str,new_log_str,"restore")
        pass
    
    def install_phpmyadmin(self,timestamp):
        restore_data=self.get_restore_data_list(timestamp)
        phpmyadmin_server=restore_data['data_list']['soft']['phpmyadmin_version']
        log_str="开始安装phpmyadmin-{}".format(phpmyadmin_server['version'])
        self.print_log(log_str,"restore")
        restore_data['data_list']['soft']['status']['status'] = 1
        restore_data['data_list']['soft']['status']['name'] = 'phpmyadmin'
        restore_data['data_list']['soft']['status']['version'] = phpmyadmin_server['version']
        self.update_restore_data_list(timestamp, restore_data)
        result=public.ExecShell("cd /www/server/panel/install && wget -O phpmyadmin.sh http://download.bt.cn/install/0/phpmyadmin.sh && bash phpmyadmin.sh install {}".format(phpmyadmin_server['version']))
        new_log_str="phpmyadmin-{} ✓".format(phpmyadmin_server['version'])
        self.replace_log(log_str,new_log_str,"restore")

    def install_golang(self,timestamp):
        restore_data=self.get_restore_data_list(timestamp)
        go_lang_list=restore_data['data_list']['soft']['golang_list']
        restore_data['data_list']['soft']['status']['status'] = 1
        restore_data['data_list']['soft']['status']['name'] = 'golang'
        restore_data['data_list']['soft']['status']['version'] = 'go'
        self.update_restore_data_list(timestamp, restore_data)
        from projectModel.goModel import main
        for go_lang in go_lang_list:
            go_lang_ver=go_lang['version']
            log_str="开始安装golang-{}".format(go_lang_ver)
            self.print_log(log_str,"restore")
            if os.path.exists("/usr/local/btgojdk/{}".format(go_lang_ver)):
                new_log_str="golang-{} ✓".format(go_lang_ver)
                self.replace_log(log_str,new_log_str,"restore")
                continue
            go_lang_use=go_lang['used']
            args = public.dict_obj()
            args.version = go_lang_ver
            result=main().install_go_sdk(args)
            if result['status'] == False:
                new_log_str="golang-{} ✗ 原因：{}".format(go_lang_ver,result['msg'])
                self.replace_log(log_str,new_log_str,"restore")
            elif result['status'] == True:
                new_log_str="golang-{} ✓".format(go_lang_ver)
                self.replace_log(log_str,new_log_str,"restore")
        if not os.path.exists("/usr/local/btgo".format(go_lang_use)):
            public.ExecShell("ln -s /usr/local/btgojdk/{} /usr/local/btgo".format(go_lang_use))
        
    def install_tomcat(self,timestamp):
        restore_data=self.get_restore_data_list(timestamp)
        tomcat_list=restore_data['data_list']['soft']['tomcat_list']
        restore_data['data_list']['soft']['status']['status'] = 1
        restore_data['data_list']['soft']['status']['name'] = 'tomcat'
        restore_data['data_list']['soft']['status']['version'] = 'tomcat'
        from mod.project.java.projectMod import main as java_mod
        for tomcat in tomcat_list:
            log_str="开始安装tomcat-{}".format(tomcat['tomcat_name'])
            self.print_log(log_str,"restore")
            try:
                if os.path.exists(tomcat['path']):
                    new_log_str="tomcat-{} ✓".format(tomcat['tomcat_name'])
                    self.replace_log(log_str,new_log_str,"restore")
                    continue
            except:
                pass
            if tomcat['type'] == 'indep':
                install_type='custom'
            else:
                install_type="global"
            base_version="tomcat" + str(tomcat['version'].split('.')[0])
            args = public.dict_obj()
            args.install_type = install_type
            args.user = tomcat['user']
            args.auto_start = tomcat['auto_start']
            args.port = tomcat['port']
            args.jdk_path = tomcat['jdk_path']
            args.ps = tomcat['ps']
            args.name = tomcat['tomcat_name']
            args.base_version = base_version
            args.release_firewall = False
            result=java_mod().install_tomcat(args)
            new_log_str="tomcat-{} ✓".format(tomcat['tomcat_name'])
            self.replace_log(log_str,new_log_str,"restore")
    
    def install_dotnet(self,timestamp):
        try:
            restore_data=self.get_restore_data_list(timestamp)
            dotnet_list=restore_data['data_list']['soft']['dotnet_list']
            if not os.path.exists("/www/server/panel/plugin/dotnet"):
                public.ExecShell(" cd /www/server/panel/plugin;wget -O dotnet_T8Y5P.tar.gz http://download.bt.cn/src/dotnet_T8Y5P.tar.gz;tar -xvf dotnet_T8Y5P.tar.gz;rm -f dotnet_T8Y5P.tar.gz")
                if not os.path.exists("/www/server/panel/plugin/dotnet"):
                    return {'status': False, 'msg': '安装失败'}
            for dotnet in dotnet_list:
                dotnet_ver=dotnet['version']
                log_str="开始安装dotnet-{}".format(dotnet_ver)
                self.print_log(log_str,"restore")
                restore_data['data_list']['soft']['status']['status'] = 1
                restore_data['data_list']['soft']['status']['name'] = 'dotnet'
                restore_data['data_list']['soft']['status']['version'] = dotnet_ver
                self.update_restore_data_list(timestamp, restore_data)
                try:
                    version = dotnet_ver
                    if os.path.exists("/www/server/dotnet/{}/dotnet".format(version)):
                        new_log_str="dotnet-{} ✓".format(version)
                        self.replace_log(log_str,new_log_str,"restore")
                        continue
                    if version in ('8.0.100', "9.0.201", "8.0.407"):
                        try:
                            res = public.ExecShell("gcc --version | grep -oP '\d+\.\d+\.\d+'")[0].split('\n')[0].strip()
                            if int(res.split('.')[0]) < int(5):
                                new_log_str="dotnet-{} ✗ 原因：gcc版本不足5.2.0".format(version)
                                self.replace_log(log_str,new_log_str,"restore")
                                continue
                            if res.split('.')[0] == '5' and int(res.split('.')[1]) < int(2):
                                new_log_str="dotnet-{} ✗ 原因：gcc版本不足5.2.0".format(version)
                                self.replace_log(log_str,new_log_str,"restore")
                                continue
                        except:
                            pass

                    dotnet_tar_file="dotnet-sdk-{version}-linux-x64.tar.gz".format(version=version)
                    public.writeFile('/www/server/dotnet/{}.pl'.format(version), str(os.getpid()))
                    public.ExecShell('wget -O /www/server/panel/plugin/dotnet/{} https://download.bt.cn/src/dotnet/{}'.format(dotnet_tar_file, dotnet_tar_file))
                    public.ExecShell('mkdir -p /www/server/dotnet/{}'.format(version))
                    public.ExecShell('tar -zxvf /www/server/panel/plugin/dotnet/{} -C /www/server/dotnet/{}'.format(dotnet_tar_file, version))
                    public.ExecShell('rm -rf /www/server/panel/plugin/dotnet/{}'.format(dotnet_tar_file))
                    public.ExecShell('rm -rf /www/server/dotnet/{}.pl'.format(version))
                    res = public.ExecShell('/www/server/dotnet/{}/dotnet --version'.format(version))[0]
                    if res.strip() == version:
                        new_log_str="dotnet-{} ✓".format(version)
                        self.replace_log(log_str,new_log_str,"restore")
                    else:
                        new_log_str="dotnet-{} ✗ 安装失败，请尝试在还原任务结束后在软件商店重新安装dotnet".format(version)
                        self.replace_log(log_str,new_log_str,"restore")
                except:
                    pass
        except:
            self.print_log("dotnet安装失败，请尝试在软件商店重新安装","restore")
    
    def install_python(self,timestamp):
        restore_data=self.get_restore_data_list(timestamp)
        python_list=restore_data['data_list']['soft']['python_list']
        for python in python_list:
            restore_data['data_list']['soft']['status']['status'] = 1
            restore_data['data_list']['soft']['status']['name'] = 'python'
            restore_data['data_list']['soft']['status']['version'] = python['version']
            self.update_restore_data_list(timestamp, restore_data)
            python_ver=python['version']
            log_str="开始安装python-{}".format(python_ver)
            self.print_log(log_str,"restore")
            if os.path.exists("/www/server/pyporject_evn/versions/{}/bin/python3".format(python_ver)) or os.path.exists("/www/server/pyporject_evn/versions/{}/bin/python2".format(python_ver)):
                new_log_str="python-{} ✓".format(python_ver)
                self.replace_log(log_str,new_log_str,"restore")
                continue
            install_shell="/www/server/panel/pyenv/bin/python3 /www/server/panel/class/projectModel/btpyvm.py install {} --extend=''".format(python_ver)
            result=public.ExecShell(install_shell)
            new_log_str="python-{} ✓".format(python_ver)
            self.replace_log(log_str,new_log_str,"restore")
            
    def install_ftp_server(self,timestamp):
        restore_data=self.get_restore_data_list(timestamp)
        ftp_server=restore_data['data_list']['soft']['ftp_server']
        log_str="开始安装ftp-{}".format(ftp_server['version'])
        self.print_log(log_str,"restore")
        restore_data['data_list']['soft']['status']['status'] = 1
        restore_data['data_list']['soft']['status']['name'] = 'pure-ftpd'
        restore_data['data_list']['soft']['status']['version'] = ftp_server['version']
        if os.path.exists("/www/server/pure-ftpd/bin/pure-pw"):
            new_log_str="ftp-{} ✓".format(ftp_server['version'])
            self.replace_log(log_str,new_log_str,"restore")
            return
        self.update_restore_data_list(timestamp, restore_data)
        result=public.ExecShell("cd /www/server/panel/install && wget -O pureftpd.sh http://download.bt.cn/install/0/pureftpd.sh && bash pureftpd.sh install")
        public.ExecShell("rm -f /www/server/pure-ftpd/etc/pureftpd.passwd")
        public.ExecShell("rm -f /www/server/pure-ftpd/etc/pureftpd.pdb")
        if not os.path.exists("/www/server/pure-ftpd/bin/pure-pw"):
            combined_output = (result[0] + result[1]).splitlines()
            err_msg = '\n'.join(combined_output[-10:])
            new_log_str="ftp-{} ✗ 安装失败 原因：{} \n请尝试在还原任务结束后在软件商店重新安装ftp".format(ftp_server['version'],err_msg)
            self.replace_log(log_str,new_log_str,"restore")
        else:
            new_log_str="ftp-{} ✓".format(ftp_server['version'])
            self.replace_log(log_str,new_log_str,"restore")

        import ftp 
        if ftp_server['port'] != 21:
            args=public.dict_obj()
            args.port = str(ftp_server['port'])
            result = ftp.ftp().setPort(args)
            result = ftp.ftp().setPort(args)
    

    def install_env(self,timestamp):
        self.print_log("==================================","restore")
        self.print_log("开始检查还原面板运行环境","restore")
        self.print_log("如有相同环境将跳过安装","restore")
        restore_data=self.get_restore_data_list(timestamp)
        env_list=restore_data['data_list']['soft']['status']={}
        env_list=restore_data['data_list']['soft']['status']['name']=None
        env_list=restore_data['data_list']['soft']['status']['version']=None
        env_list=restore_data['data_list']['soft']['status']['status']=None
        env_list=restore_data['data_list']['soft']['status']['err_msg']=None
        self.update_restore_data_list(timestamp, restore_data)

    def install_plugin(self,timestamp):
        pass
    
    def install_plugin(self,timestamp):
        import PluginLoader
        import panelPlugin
        plugin = panelPlugin.panelPlugin()

        sName="pgsql_manager"
        sVersion="2"
        sMin_version="6"
        get = public.dict_obj()
        get.sName = sName
        get.version = sVersion
        get.min_version = sMin_version
        info = plugin.install_plugin(get)
        print(info)
        return
        args = public.dict_obj()
        args.tmp_path = info['tmp_path']
        args.plugin_name = sName
        args.install_opt = info['install_opt']


        print(result)

    def restore_env(self,timestamp):
        self.print_log("==================================","restore")
        self.print_log("开始还原面板运行环境","restore")
        self.print_log("如有相同环境将跳过安装","restore")
        restore_data=self.get_restore_data_list(timestamp)
        restore_data['data_list']['soft']['status']={}
        restore_data['data_list']['soft']['status']['name']=None
        restore_data['data_list']['soft']['status']['version']=None
        restore_data['data_list']['soft']['status']['status']=None
        restore_data['data_list']['soft']['status']['err_msg']=[]
        self.update_restore_data_list(timestamp, restore_data)
    
        soft_json_data=restore_data['data_list']['soft']
        try:
            if soft_json_data['web_server']:
                self.install_web_server(timestamp)
        except:
            pass
        try:        
            if soft_json_data['php_server']:
                self.install_php_server(timestamp)
                self.install_php_ext(timestamp)
        except:
            pass
        try:
            if soft_json_data['mysql_server']:
                self.install_mysql_server(timestamp)
        except:
            pass
        try:
            if soft_json_data['ftp_server']:
                self.install_ftp_server(timestamp)
        except:
            pass
        try:
            if soft_json_data['jdk_list']:
                self.install_jdk(timestamp)
        except:
            pass
        try:
            if soft_json_data['node_list']:
                self.install_node(timestamp)
        except:
            pass
        try:
            if soft_json_data['golang_list']:
                self.install_golang(timestamp)
        except:
            pass
        try:
            if soft_json_data['tomcat_list']:
                self.install_tomcat(timestamp)
        except:
            pass

        try:
            if soft_json_data['python_list']:
                self.install_python(timestamp)
        except:
            pass
        try:
            if soft_json_data['redis_server']:
                self.install_redis_server(timestamp)
        except:
            pass
        try:
            if soft_json_data['memcached_server']:
                self.install_memcached_server(timestamp)
        except:
            pass
        try:
            if soft_json_data['mongodb_server']:
                self.install_mongodb_server(timestamp)
        except:
            pass
        try:
            if soft_json_data['dotnet_list']:
                self.install_dotnet(timestamp)
        except:
            pass
        try:
            if soft_json_data['pgsql_server']:
                self.install_pgsql_server(timestamp)
        except:
            pass
        try:
            if soft_json_data['phpmyadmin_version']:
                self.install_phpmyadmin(timestamp)
        except:
            pass

        restore_data['data_list']['soft']['status']['name']="success"
        restore_data['data_list']['soft']['status']['version']="success"
        restore_data['data_list']['soft']['status']['status']=2
        restore_data['data_list']['soft']['status']['err_msg']=None
        self.update_restore_data_list(timestamp, restore_data)


if __name__ == '__main__':
    # 获取命令行参数
    if len(sys.argv) < 2:
        print("Usage: btpython backup_manager.py <method> <timestamp>")
        sys.exit(1)
    method_name = sys.argv[1]  # 方法名  p
    timestamp = sys.argv[2]
    soft_manager = SoftModule()  # 实例化对象
    if hasattr(soft_manager, method_name):  # 检查方法是否存在
        method = getattr(soft_manager, method_name)  # 获取方法
        method(timestamp)  # 调用方法
    else:
        print(f"Error: 方法 '{method_name}' 不存在")