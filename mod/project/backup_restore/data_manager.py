#!/usr/bin/python
# coding: utf-8

import os
import sys
import json
from collections import defaultdict
from typing import Dict, List, Optional

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

if '/www/server/panel' not in sys.path:
    sys.path.insert(0, '/www/server/panel')

import public

import public
import panelMysql
import db_mysql
import database
from mod.project.backup_restore.base_util import BaseUtil
from mod.project.backup_restore.modules.soft_module import SoftModule

class DataManager(SoftModule,BaseUtil):
    def __init__(self):
        self._init_db_connections()


    def _init_db_connections(self):
        """初始化数据库连接"""
        self.mysql_obj = db_mysql.panelMysql()

    def get_data_list(self) -> dict:
        """获取所有数据列表"""
        # 先获取所有数据列表
        soft_data = self.get_soft_list()
        site_list = self.get_site_list()
        wp_tools_list = self.get_wp_tools_list()
        database_list = self.get_database_list()
        ssh_list = self.get_ssh_list()
        plugin_list = self.get_plugin_list()
        vmail_list = self.get_vmail_list()
        btnode_list = self.get_btnode_list()
        
        # 计算所有数据的总大小
        disk_use = 0
        
        # 累加软件大小
        # for soft in soft_data:
        #     try:
        #         if 'size' in soft and soft['size']:
        #             disk_use += int(soft['size'])
        #     except:
        #         pass
                
        # 累加网站大小
        for site in site_list:
            try:
                if 'size' in site and site['size']:
                    disk_use += int(site['size'])
            except:
                pass
                
        # 累加WP工具大小
        for wp in wp_tools_list:
            try:
                if 'size' in wp and wp['size']:
                    disk_use += int(wp['size'])
            except:
                pass
                
        # 累加数据库大小
        for db in database_list:
            try:
                if 'size' in db and db['size']:
                    disk_use += int(db['size'])
            except:
                pass
                
        # 累加SSH大小
        try:
            if 'ssh_size' in ssh_list:
                disk_use += int(ssh_list['ssh_size'])
            if 'command_size' in ssh_list:
                disk_use += int(ssh_list['command_size'])
        except:
            pass
            
        # 累加插件大小
        for plugin in plugin_list:
            try:
                if 'size' in plugin and plugin['size']:
                    disk_use += int(plugin['size'])
            except:
                pass
        
        # 返回所有数据
        return {
            "disk_free": BaseUtil.get_free_space(self)['free_space'],
            "disk_use": disk_use,
            "oss_list": self.get_oss_list(),
            "soft_data": soft_data,
            "site_list": site_list,
            "wp_tools_list": wp_tools_list,
            "database_list": database_list,
            "ftp_list": self.get_ftp_list(),
            "ssh_list": ssh_list,
            "crontab_list": self.get_crontab_list(),
            "firewall_list": self.get_firewall_list(),
            "plugin_list": plugin_list,
            "vmail_list": vmail_list,
            "btnode_list": btnode_list
        }
    

    def get_oss_list(self):
        data=[]
        # data['orderOpt'] = []
        configured = []
        not_configured = []
        import json
        tmp = public.readFile('data/libList.conf')
        if not tmp: return data
        libs = json.loads(tmp)
        for lib in libs:
            if not 'opt' in lib: continue
            filename = 'plugin/{}'.format(lib['opt'])
            if not os.path.exists(filename):
                continue
            else:
                plugin_path = '/www/server/panel/plugin/{}/aes_status'.format(lib['opt'])
                status = 0  # 默认值为0，表示未配置
                if os.path.exists(plugin_path):
                    with open(plugin_path, 'r') as f:
                        status_content = f.read().strip()
                        if status_content.lower() == 'true':
                            status = 1  # 如果 aes_status 文件内容为 'True' 则设置为1
                if lib['opt']=="msonedrive":
                    status = 1
            tmp = {}
            tmp['name'] = lib['name']
            tmp['value'] = lib['opt']
            tmp['status'] =status
            if status == 1:
                configured.append(tmp)
            else:
                not_configured.append(tmp)
        
        # 先添加已配置的，再添加未配置的
        data.extend(configured)
        data.extend(not_configured)
        return data
    
    def get_soft_list(self):
        soft_data = self.get_soft_data()
        simplified_soft_list = []
        
        # 处理Web服务器
        if 'web_server' in soft_data and soft_data['web_server']:
            simplified_soft_list.append({
                'name': soft_data['web_server'].get('name', ''),
                'version': soft_data['web_server'].get('version', ''),
                'size': soft_data['web_server'].get('size', 0)
            })
        
        # 处理PHP版本
        if 'php_server' in soft_data and soft_data['php_server']:
            for php in soft_data['php_server']:
                simplified_soft_list.append({
                    'name': php.get('name', ''),
                    'version': php.get('version', ''),
                    'size': php.get('size', 0)
                })
        
        # 处理MySQL服务器
        if 'mysql_server' in soft_data and soft_data['mysql_server']:
            simplified_soft_list.append({
                'name': soft_data['mysql_server'].get('type', 'mysql'),
                'version': soft_data['mysql_server'].get('version', ''),
                'size': soft_data['mysql_server'].get('size', 0)
            })
        
        # 处理FTP服务器
        if 'ftp_server' in soft_data and soft_data['ftp_server']:
            simplified_soft_list.append({
                'name': soft_data['ftp_server'].get('name', 'ftp'),
                'version': soft_data['ftp_server'].get('version', '1.0.47'),
                'size': soft_data['ftp_server'].get('size', 0)
            })
        
        # 处理JDK列表
        if 'jdk_list' in soft_data and soft_data['jdk_list']:
            for jdk in soft_data['jdk_list']:
                if isinstance(jdk, dict):
                    simplified_soft_list.append({
                        'name': jdk.get('name', 'jdk'),
                        'version': jdk.get('version', ''),
                        'size': jdk.get('size', 0)
                    })
                else:
                    simplified_soft_list.append({
                        'name': 'jdk',
                        'version': jdk,
                        'size': 0
                    })
        
        # 处理Node.js列表
        if 'node_list' in soft_data and soft_data['node_list']:
            for node in soft_data['node_list']:
                simplified_soft_list.append({
                    'name': node.get('name', ''),
                    'version': node.get('version', ''),
                    'size': node.get('size', 0)
                })
        
        # 处理Golang
        if 'golang_list' in soft_data and soft_data['golang_list']:
            for golang in soft_data['golang_list'] or []:
                if isinstance(golang, dict):
                    simplified_soft_list.append({
                        'name': golang.get('name', 'golang'),
                        'version': golang.get('version', ''),
                        'size': golang.get('size', 0)
                    })
                else:
                    simplified_soft_list.append({
                        'name': 'golang',
                        'version': golang,
                        'size': 0
                    })
        
        # 处理Tomcat
        if 'tomcat_list' in soft_data and soft_data['tomcat_list']:
            for tomcat in soft_data['tomcat_list'] or []:
                if isinstance(tomcat, dict):
                    simplified_soft_list.append({
                        'name': tomcat.get('name', 'tomcat'),
                        'version': tomcat.get('version', ''),
                        'size': tomcat.get('size', 0)
                    })
                else:
                    simplified_soft_list.append({
                        'name': 'tomcat',
                        'version': tomcat,
                        'size': 0
                    })
        
        # 处理Redis服务器
        if 'redis_server' in soft_data and soft_data['redis_server']:
            if isinstance(soft_data['redis_server'], dict):
                simplified_soft_list.append({
                    'name': soft_data['redis_server'].get('name', 'redis'),
                    'version': soft_data['redis_server'].get('version', ''),
                    'size': soft_data['redis_server'].get('size', 0)
                })
            else:
                simplified_soft_list.append({
                    'name': 'redis',
                    'version': soft_data['redis_server'],
                    'size': 0
                })
        
        # 处理Memcached服务器
        if 'memcached_server' in soft_data and soft_data['memcached_server']:
            if isinstance(soft_data['memcached_server'], dict):
                simplified_soft_list.append({
                    'name': soft_data['memcached_server'].get('name', 'memcached'),
                    'version': soft_data['memcached_server'].get('version', '1.6.12'),
                    'size': soft_data['memcached_server'].get('size', 0)
                })
            else:
                simplified_soft_list.append({
                    'name': 'memcached',
                    'version': '1.16' if not isinstance(soft_data['memcached_server'], str) else soft_data['memcached_server'],
                    'size': 0
                })
        
        # 处理MongoDB服务器
        if 'mongodb_server' in soft_data and soft_data['mongodb_server']:
            if isinstance(soft_data['mongodb_server'], dict):
                simplified_soft_list.append({
                    'name': soft_data['mongodb_server'].get('name', 'mongodb'),
                    'version': soft_data['mongodb_server'].get('version', ''),
                    'size': soft_data['mongodb_server'].get('size', 0)
                })
            else:
                simplified_soft_list.append({
                    'name': 'mongodb',
                    'version': soft_data['mongodb_server'],
                    'size': 0
                })
        
        # 处理PostgreSQL服务器
        if 'pgsql_server' in soft_data and soft_data['pgsql_server']:
            if isinstance(soft_data['pgsql_server'], dict):
                simplified_soft_list.append({
                    'name': soft_data['pgsql_server'].get('name', 'pgsql'),
                    'version': soft_data['pgsql_server'].get('version', ''),
                    'size': soft_data['pgsql_server'].get('size', 0)
                })
            else:
                simplified_soft_list.append({
                    'name': 'pgsql',
                    'version': soft_data['pgsql_server'],
                    'size': 0
                })
        
        # 处理phpMyAdmin
        if 'phpmyadmin_version' in soft_data and soft_data['phpmyadmin_version']:
            if isinstance(soft_data['phpmyadmin_version'], dict):
                simplified_soft_list.append({
                    'name': soft_data['phpmyadmin_version'].get('name', 'phpmyadmin'),
                    'version': soft_data['phpmyadmin_version'].get('version', ''),
                    'size': soft_data['phpmyadmin_version'].get('size', 0)
                })
            else:
                simplified_soft_list.append({
                    'name': 'phpmyadmin',
                    'version': soft_data['phpmyadmin_version'],
                    'size': 0
                })
                
        return simplified_soft_list

    def get_site_list(self) -> dict:
        """获取网站列表"""

        result=[]    
        try:
            data = public.M('sites').field('name,path,project_type,id,ps').select()
            if isinstance(data, str):
                return []

            for site in data:
                try:
                    path_size = public.ExecShell(f"du -sb {site['path']}")[0].split("\t")[0]
                except:
                    path_size = 0
                site_data = {
                    "name": site["name"],
                    "id": site["id"],
                    "ps": site["ps"],
                    "size": path_size,
                    "type": site["project_type"]
                }

                result.append(site_data)
            return result
        except Exception as e:
            print(f"获取网站列表失败: {str(e)}")
            return []
        
    def get_wp_tools_list(self) -> list:
        """获取网站列表"""
        result=[]    
        try:
            data = public.M('sites').field('name,path,project_type,id,ps').select()
            if isinstance(data, str):
                return []
            for site in data:
                if site['project_type'] == 'WP2':
                    try:
                        path_size = public.ExecShell(f"du -sb {site['path']}")[0].split("\t")[0]
                    except:
                        path_size = 0
                    site_data = {
                        "name": site["name"],
                        "id": site["id"],
                        "ps": site["ps"],
                        "size": path_size,
                        "type": site["project_type"]
                    }
                    print(site_data)
                    result.append(site_data)
            return result
        except Exception as e:
            print(f"获取网站列表失败: {str(e)}")
            return []

    def get_database_list(self) -> list:
        """获取MySQL数据库列表"""
        result = []
        mysql_obj = db_mysql.panelMysql()
        try:
            data = public.M('databases').field('name,type,id,sid,ps').select()
            
            for i in data:

                db_size = 0
                if i['type'].lower() in ['mysql'] and i['sid'] == 0:
                    try:
                        db_name = i['name']
                        table_list = self.mysql_obj.query(f"show tables from `{db_name}`")
                        #db_size = 0
                        for tb_info in table_list:
                            table = self.mysql_obj.query(f"show table status from `{db_name}` where name = '{tb_info[0]}'")
                            if not table: continue
                            table_6 = table[0][6] or 0
                            table_7 = table[0][7] or 0
                            db_size += int(table_6) + int(table_7)
                    except:
                        db_size = self.get_file_size("/www/server/data/{}".format(db_name))
                db_data = {
                    "name": i['name'],
                    "id": i['id'],
                    "ps": i['ps'],
                    "type": i['type'],
                    "size": db_size
                }
                result.append(db_data)
            #单独获取redis数据
            if os.path.exists("/www/server/redis/src/redis-server"):
                if os.path.exists("/www/server/redis/dump.rdb"):
                    redis_size = self.get_file_size("/www/server/redis/dump.rdb")
                elif os.path.exists("/www/server/redis/appendonly.aof"):
                    redis_size = self.get_file_size("/www/server/redis/appendonly.aof")
                else:
                    redis_size = 0
                redis_data = {
                    "name": "redis",
                    "id": 0,
                    "ps": "redis",
                    "type": "redis",
                    "size": redis_size
                }
                result.append(redis_data)
            return result
        except Exception as e:
            print(f"获取MySQL列表失败: {str(e)}")
            return []

    def get_ftp_list(self) -> list:
        """获取FTP列表"""
        try:
            data = public.M('ftps').field('name,id').select()
            if isinstance(data, str):
                return []
            return [{"name": i['name'], "id": i['id']} for i in data]
        except Exception as e:
            print(f"获取FTP列表失败: {str(e)}")
            return []

    def get_ssh_list(self) -> dict:
        """获取SSH列表"""
        result = {}
        try:
            ssh_path="/www/server/panel/config/ssh_info"
            ssh_user_command_file="/www/server/panel/config/ssh_info/user_command.json"
            path_size = self.get_file_size(ssh_path)
            command_size = self.get_file_size(ssh_user_command_file)
            print(ssh_user_command_file)
            print(path_size)
            print(command_size)

            result['ssh_size'] = int(path_size) - int(command_size)
            result['command_size'] = int(command_size)
            print(result)
            return result
        except Exception as e:
            print(f"获取SSH列表失败: {str(e)}")
            return {'ssh_size': 0, 'command_size': 0}
        
    def get_crontab_list(self) -> dict:
        result = {}
        try:
            data = public.M('crontab').field('name,id').select()
            if isinstance(data, str):
                return {}
            return [{"name": i['name'], "id": i['id']} for i in data]
        except Exception as e:
            pass

    def get_firewall_list(self) -> dict:
        result = {}
        try:
            result['firewall_domain'] = public.M('firewall_domain').count()
            result['firewall_ip'] = public.M('firewall_ip').count()
            result['firewall_conutry'] = public.M('firewall_country').count()
            result['firewall_new'] = public.M('firewall_new').count()
            result['firewall_forward'] = public.M('firewall_forward').count()
            result['firewall_malicious_ip'] = public.M('firewall_malicious_ip').count()
            return result
        except Exception as e:
            return {}
        
    def get_plugin_list(self) -> list:
        plugin_list=['btwaf','syssafe','monitor','tamper_core']
        result=[]
        for plugin in plugin_list:
            if os.path.exists("/www/server/panel/plugin/{}".format(plugin)):
                if plugin == "btwaf":
                    plugin_name="宝塔防火墙"
                elif plugin == "syssafe":
                    plugin_name="系统加固"
                elif plugin == "monitor":
                    plugin_name="网站监控报表"
                elif plugin == "tamper_core":
                    plugin_name="内核防篡改"
                result.append({
                    "name": plugin_name,
                    "size": self.get_file_size("/www/server/panel/plugin/{}".format(plugin))
                })
        return result
    
    def get_vmail_list(self) -> list:
        result=[]
        if os.path.exists("/www/vmail"):
            result.append({
                "name": "邮局数据",
                "size": self.get_file_size("/www/vmail")
            })
        return result
    
    def get_btnode_list(self) -> list:
        result=[]
        data = public.M('node').field('id,address,remarks,server_ip').select()
        for i in data:
            result.append({
                "name": i['remarks'],
                "server_ip": i['server_ip']
            })
        return result


    def get_web_status(self) -> dict:
        """获取Web服务器状态"""
        result = defaultdict(list)
        try:
            result['web'] = public.get_webserver()
            if result['web'] == "nginx":
                conf_result = public.ExecShell('ulimit -n 8192;nginx -t')
                if 'successful' not in conf_result[1]:
                    result['status'] = "err"
                    result['err'] = conf_result[1]
                else:
                    result['status'] = "ok"
            return result
        except Exception as e:
            print(f"获取Web状态失败: {str(e)}")
            return {'web': None, 'status': 'err'}

    def get_free_space(self) -> dict:
        """获取可用空间"""
        try:
            path = "/www"
            diskstat = os.statvfs(path)
            free_space = diskstat.f_bavail * diskstat.f_frsize
            return {'free_space': free_space}
        except Exception as e:
            print(f"获取可用空间失败: {str(e)}")
            return {'free_space': 0}

    def get_server_config(self) -> dict:
        """获取服务器配置信息"""
        result = {}
        try:
            # 获取Web服务器信息
            result['webserver'] = {}
            webserver = None
            if os.path.exists("/www/server/nginx/sbin/nginx"):
                webserver = "nginx"
            elif os.path.exists("/www/server/apache/bin/httpd"):
                webserver = "apache"
            result['webserver']['name'] = webserver
            result['webserver']['status'] = None

            # 获取PHP信息
            result['php'] = {}
            php_dir = "/www/server/php"
            for dir_name in os.listdir(php_dir):
                dir_path = os.path.join(php_dir, dir_name)
                if os.path.isdir(dir_path) and os.path.exists(os.path.join(dir_path, 'bin/php')):
                    php_ext = public.ExecShell(f"/www/server/php/{dir_name}/bin/php -m")[0].split("\n")
                    filtered_data = [item for item in php_ext if item not in ('[PHP Modules]', '[Zend Modules]', '')]
                    result['php'][dir_name] = {
                        'status': None,
                        'php_ext': filtered_data
                    }

            # 获取MySQL信息
            result['mysql'] = {}
            if os.path.exists("/www/server/mysql/bin/mysql"):
                # 添加MySQL相关信息
                pass

            return result
        except Exception as e:
            print(f"获取服务器配置失败: {str(e)}")
            return {}
    

if __name__ == '__main__':
    # 获取命令行参数
    if len(sys.argv) < 3:
        print("Usage: btpython data_manager.py <method>")
        sys.exit(1)
    method_name = sys.argv[1]  # 方法名
    data_manager = DataManager()  # 实例化对象
    if hasattr(data_manager, method_name):  # 检查方法是否存在
        method = getattr(data_manager, method_name)  # 获取方法
        method()  # 调用方法
    else:
        print(f"Error: 方法 '{method_name}' 不存在")