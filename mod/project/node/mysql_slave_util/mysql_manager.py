# -*- coding: utf-8 -*-
"""
MySQL 主从复制 MySQL 管理模块
负责 MySQL 配置、用户管理、数据备份等操作
"""

import os
import re
import time
import datetime
import hashlib
import random
import string
from typing import List, Dict, Any, Union
import public
import panelMysql
import db_mysql
import database


class MySQLManager:
    """MySQL 管理器"""
    
    def __init__(self):
        self.mysql_cnf = "/etc/my.cnf"
        self.mysqldump_bin = "/www/server/mysql/bin/mysqldump"
        self.master_backup_path = "/www/backup/mysql_master"

    def get_mysql_version(self) -> Union[str, None]:
        """获取MySQL版本"""
        allowed_versions = {'5.7', '8.0', '8.4', '9.0', '10.3', '10.4', '10.5', '10.6', '10.7', '10.8', '10.9', '10.11'}
        file_paths = [
            '/www/server/mysql/version.pl',
            '/www/server/mysql/version_check.pl'
        ]
        version_pattern = re.compile(r'\b(\d+\.\d+)\b(?:\.\d+)*')
        
        for path in file_paths:
            try:
                if os.path.exists(path):
                    content = public.ReadFile(path)
                    matches = version_pattern.findall(content)
                    for version in matches:
                        if version in allowed_versions:
                            return version
                            
                    mariadb_pattern = re.compile(r'(?:mariadb_|(\d+\.\d+\.\d+)-MariaDB)')
                    mariadb_match = mariadb_pattern.search(content.lower())
                    if mariadb_match:
                        version_str = mariadb_match.group(1) if mariadb_match.group(1) else mariadb_match.group(0).split('_')[1]
                        parts = version_str.split('.')[:2]
                        mariadb_version = '.'.join(parts)
                        if mariadb_version in allowed_versions:
                            return mariadb_version
            except:
                continue
        return None

    def config_master(self, slave_ip: str) -> Dict[str, Any]:
        """配置主库"""
        my_cnf = public.ReadFile(self.mysql_cnf)
        if not my_cnf:
            return public.returnMsg(False, "获取mysql配置文件失败")
        
        if "gtid_mode=ON" not in my_cnf or "enforce_gtid_consistency=ON" not in my_cnf:
            if "[mysqld]" not in my_cnf:
                my_cnf += "\n[mysqld]\n"
            
            if "gtid_mode=ON" not in my_cnf:
                my_cnf = my_cnf.replace("[mysqld]", "[mysqld]\ngtid_mode=ON")
            if "enforce_gtid_consistency=ON" not in my_cnf:
                my_cnf = my_cnf.replace("[mysqld]", "[mysqld]\nenforce_gtid_consistency=ON")
            
            if not public.WriteFile(self.mysql_cnf, my_cnf):
                return public.returnMsg(False, "写入MySQL配置文件失败")
            
            public.ExecShell("/etc/init.d/mysqld restart")

        return public.returnMsg(True, "MySQL主库配置成功")

    def create_slave_user(self, slave_ip: str, master_user: str = None, master_password: str = None) -> Dict[str, Any]:
        """创建从库用户"""
        if not master_user:
            master_user = slave_ip + "_slave"
        if not master_password:
            master_password = self.new_password()

        master_host = slave_ip
        mysql_obj = db_mysql.panelMysql()
        
        # 检查用户是否存在，存在则删除
        slave_user_check = mysql_obj.query("select * from mysql.user where user='{master_user}'".format(master_user=master_user))
        if len(slave_user_check) > 0:
            mysql_obj.execute("drop user '{master_user}'@'{master_host}'".format(master_user=master_user, master_host=master_host))
        
        mysql_obj.execute("create user '{master_user}'@'{master_host}' identified by '{master_password}'".format(
            master_user=master_user, master_host=master_host, master_password=master_password))
        mysql_obj.execute("grant replication slave on *.* to '{master_user}'@'{master_host}'".format(
            master_user=master_user, master_host=master_host))
        mysql_obj.execute("flush privileges;")

        return {
            "status": True,
            "user": master_user,
            "password": master_password
        }

    def backup_master_data(self, db_names: List[str]) -> Dict[str, Any]:
        """备份主库数据"""
        db_names_str = " ".join(db_names)
        
        try:
            db_port = int(panelMysql.panelMysql().query("show global variables like 'port'")[0][1])
        except:
            db_port = 3306

        db_user = "root"
        db_password = public.M("config").where("id=?", (1,)).getField("mysql_root")
        db_host = "localhost"
        backup_date = datetime.datetime.now().strftime("%Y%m%d-%H%M")
        file_name = "{backup_time}_mysql_master_data.sql".format(backup_time=backup_date)

        shell = "'{mysqldump_bin}' --databases {db_name} --single-transaction --flush-logs --set-gtid-purged=ON  --triggers --routines --events --force --quick " \
                "--host='{db_host}' --port={db_port} --user='{db_user}' --password='{db_password}' ".format(
                mysqldump_bin=self.mysqldump_bin,
                db_host=db_host,
                db_port=db_port,
                db_user=db_user,
                db_password=db_password,
                db_name=db_names_str
            )

        export_sql_file = os.path.join(self.master_backup_path, file_name)
        if not os.path.exists(self.master_backup_path):
            os.makedirs(self.master_backup_path)
        
        shell += " > '{export_sql_file}' ".format(export_sql_file=export_sql_file)
        
        # 执行备份
        result = public.ExecShell(shell, env={"MYSQL_PWD": db_password})
        if not os.path.exists(export_sql_file):
            return public.returnMsg(False, "备份失败")
        
        # 获取数据库信息
        mysql_data = public.M('databases').field('name,type,id,sid,ps,username,password').select()
        db_info = [db for db in mysql_data if db["name"] in db_names]
        
        for item in db_info:
            item['db_access'] = database.database().GetDatabaseAccess(public.to_dict_obj({'name': item['name']}))['msg']

        sql_file_sha256 = self.get_file_sha256(export_sql_file)
        sql_file_size = public.ExecShell("du -sb {}".format(export_sql_file))[0].split("\t")[0]

        return {
            "status": True,
            "backup_file": export_sql_file,
            "db_info": db_info,
            "file_sha256": sql_file_sha256,
            "file_size": sql_file_size
        }

    def database_list(self) -> List[Dict[str, Any]]:
        """获取主库数据库列表"""
        result = []
        data = public.M('databases').field('name,type,id,sid,ps').select()
        mysql_obj = db_mysql.panelMysql()

        for i in data:
            if i['type'].lower() in ['mysql'] and i['sid'] == 0:
                try:
                    db_name = i['name']
                    table_list = mysql_obj.query("show tables from `{db_name}`".format(db_name=db_name))
                    db_size = 0
                    for tb_info in table_list:
                        table = mysql_obj.query("show table status from `%s` where name = '%s'" % (db_name, tb_info[0]))
                        if not table: 
                            continue
                        table_6 = table[0][6]
                        table_7 = table[0][8]
                        if table_6 is None:
                            table_6 = 0
                        if table_7 is None:
                            table_7 = 0
                        db_size += int(table_6) + int(table_7)
                    table_type_query = mysql_obj.query("SHOW TABLE STATUS FROM `{db_name}` WHERE Engine = 'MyISAM';".format(db_name=db_name))
                    if len(table_type_query) > 0:
                        table_type="MyISAM"
                    else:
                        table_type="InnoDB"
                except:
                    db_size = 0
                    table_type="InnoDB"

                mysql_data = {
                    "name": i['name'],
                    "id": i['id'],
                    "ps": i['ps'],
                    "size": db_size,
                    "type": table_type
                }
                result.append(mysql_data)
        return result

    def get_master_sql_list(self) -> List[Dict[str, Any]]:
        """获取主库备份文件列表"""
        try:
            log_list = []
            if not os.path.exists(self.master_backup_path):
                return log_list
                
            files = os.listdir(self.master_backup_path)
            for file in files:
                file_path = os.path.join(self.master_backup_path, file)
                if os.path.isfile(file_path):
                    file_stat = os.stat(file_path)
                    log_list.append({
                        "name": file,
                        "path": file_path,
                        "size": file_stat.st_size,
                        "mtime": file_stat.st_mtime,
                        "update_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(file_stat.st_mtime))
                    })
            # 按最后修改时间降序排序
            log_list.sort(key=lambda x: x["mtime"], reverse=True)
            return log_list
        except Exception as e:
            return []

    def del_master_sql(self, file_path: str) -> Dict[str, Any]:
        """删除主库备份文件"""
        if not os.path.exists(file_path):
            return public.returnMsg(False, "文件不存在")
        os.remove(file_path)
        return public.returnMsg(True, "删除成功")

    def drop_slave_user(self, master_user: str, slave_ip: str) -> bool:
        """删除从库用户"""
        try:
            mysql_obj = db_mysql.panelMysql()
            mysql_obj.execute("drop user '{master_user}'@'{slave_ip}'".format(
                master_user=master_user, slave_ip=slave_ip))
            return True
        except:
            return False

    @staticmethod
    def new_password() -> str:
        """生成随机密码"""
        password = "".join(random.sample(string.ascii_letters + string.digits, 16))
        return password

    @staticmethod
    def get_file_sha256(file_path: str) -> str:
        """获取文件SHA256值"""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                sha256.update(chunk)
        return sha256.hexdigest() 