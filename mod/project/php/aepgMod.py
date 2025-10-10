# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------
import json
import os
# ------------------------------
# 一键应用环境包模型
# ------------------------------
import sys
import time

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

os.chdir("/www/server/panel")
import public
import panelMysql
import db_mysql

try:
    from BTPanel import cache
except:
    from cachelib import SimpleCache
    cache = SimpleCache()


class main():
    def __init__(self):
        # 2024/5/6 上午10:09 前期临时使用版本列表，后期再动态获取
        self._php_versions = ['52', '53', '54', '55', '56', '70', '71', '72', '73', '74', '80', '81', '82', '83']
        self._mysql_versions = ['5.1', '5.5', '5.6', '5.7', '8.0']
        # self._nginx_versions = ['1.8', '1.10', '1.12', '1.14', '1.16', '1.18', '1.20', '1.22', '1.24']
        self._nginx_install = True
        self._php_install = True
        self._mysql_install = True
        self._ftpd_install = True
        self.APP_PACKAGE_DB_NAME = "BT_APP_PACKAGE_DB_NAME"
        self.APP_PACKAGE_DB_USER = "BT_APP_PACKAGE_DB_USER"
        self.APP_PACKAGE_DB_PASS = "BT_APP_PACKAGE_DB_PASS"
        self._MYSQLDUMP_BIN = public.get_mysqldump_bin()
        self._rewrite_file = "{panel_path}/vhost/rewrite/{site_name}.conf"
        self._package_dir = "/www/backup/package"
        self._upload_package_dir = "/www/backup/upload_package"
        self._temp_backup_dir = "{}/temp".format(self._package_dir)
        self._temp_upload_package_dir = "{}/temp".format(self._upload_package_dir)
        self._upload_package_path = os.path.join(self._upload_package_dir, "{app_name}")
        self._backup_dir = None
        self.skey = "app_package_create"
        self._package_conf = {
            "app_name": "",
            "app_version": "",
            "exclude_dir": [],
            "php_versions": [],
            "php_libs": [],
            "php_functions": "",
            "mysql_versions": [],
            "init_sql": 0,
            "db_character": "",
            "db_config_file": [],
            "nginx_install": True,
            "php_install": True,
            "mysql_install": False,
            "ftpd_install": True,
            "run_path": "/",
            "dir_permission": [],
            "update_log": "",
            "size": 0,
            "success_url": "",
        }

    # 2024/5/6 上午10:26 返回支持选择的PHP列表
    def get_php_versions(self, get):
        '''
            @name 返回支持选择的PHP列表
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        return {
            "used": public.get_site_php_version(get.site_name),
            "versions": self._php_versions,
        }

    # 2024/5/6 上午10:26 返回支持的mysql列表
    def get_mysql_versions(self, get):
        '''
            @name 返回支持的mysql列表
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        used = "00"
        if os.path.exists("{}/mysql/bin/mysqld".format(public.get_setup_path())):
            version = public.ReadFile("{}/mysql/version.pl".format(public.get_setup_path()))
            if version != "" and "." in version:
                used = version.rsplit(".", 1)[0]

        return {
            "used": used if "." in used else "00",
            "versions": self._mysql_versions,
        }

    # 2024/5/6 上午10:38 获取指定版本PHP的当前配置情况
    def get_php_config(self, get):
        '''
            @name 获取指定版本PHP的当前配置情况
            @author wzz <2024/5/6 上午10:40>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.version = get.get("version/s", "00")
        if get.version == "00":
            return public.returnResult(status=False, msg="php_version不能为空，请传入需要获取扩展的PHP版本")

        import ajax
        a = ajax.ajax()
        res = a.GetPHPConfig(get)

        is_install = []
        for r in res["libs"]:
            if r["status"]:
                is_install.append(r)

        res["libs"] = is_install

        return public.returnResult(status=True, data=res)

    # 2024/5/8 下午4:31 获取环境信息
    def get_env_info(self, get):
        '''
            @name 获取环境信息
            @author wzz <2024/5/8 下午4:31>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name/s", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空")

        result = cache.get(self.skey)
        last_php_functions = ""
        last_php_versions = ""
        last_mysql_versions = ""
        last_init_sql = 0
        last_db_name = ""
        last_db_id = ""
        last_db_config_files_l = []
        if isinstance(result, dict):
            last_php_functions = result["php_functions"] if "php_functions" in result else ""
            last_php_versions = result["php_versions"].split(",") if "php_versions" in result else ""
            last_mysql_versions = result["mysql_versions"].split(",") if "mysql_versions" in result else ""
            last_init_sql = result["init_sql"] if "init_sql" in result else 0
            last_db_config_files = result["db_config_files"] if "db_config_files" in result else []
            for db_c in last_db_config_files:
                last_db_config_files_l.append({"file": db_c, "body": ""})
            last_db_name = result["db_name"] if "db_name" in result else ""
            last_db_id = result["db_id"] if "db_id" in result else None

        php_version = self.get_php_versions(get)
        php_version["last_php_versions"] = last_php_versions
        mysql_version = self.get_mysql_versions(get)
        mysql_version["last_mysql_versions"] = last_mysql_versions
        mysql_version["last_init_sql"] = last_init_sql
        mysql_version["last_db_config_files"] = last_db_config_files_l
        mysql_version["last_db_name"] = last_db_name
        mysql_version["last_db_id"] = last_db_id

        data = {
            "php": php_version,
            "mysql": mysql_version,
            "db": {
                "used": {},
                "all": [],
            },
            "db_config_file": [],
            "last_php_functions": last_php_functions,
        }

        get.site_info = public.M('sites').where('name=?', (get.site_name,)).find()
        if not get.site_info:
            return public.returnResult(status=False, msg="获取网站信息失败")

        get.db_info = public.M('databases').where('pid=?', (get.site_info['id'],)).find()
        get.db_all = public.M('databases').select()
        data["db"]["all"] = get.db_all
        get.config_list = []
        if get.db_info:
            data["db"]["used"] = get.db_info

            stdout, stderr = public.ExecShell("find {site_path}/* -name *.php|xargs grep \"{db_name}\"".format(
                site_path=get.site_info["path"],
                db_name=get.db_info["name"],
            ))
            find_result = stdout.split("\n")
            for fr in find_result:
                if not fr:
                    continue

                find_file = fr.split(":")[0]
                if not os.path.exists(find_file):
                    continue
                if not find_file.endswith(".php"):
                    continue
                find_body = fr.split(":")[1]
                if not find_body:
                    continue

                if len(get.config_list) > 0:
                    for conf in get.config_list:
                        if find_file in conf["file"]:
                            break
                    else:
                        get.config_list.append({"file": find_file, "body": find_body})
                else:
                    get.config_list.append({"file": find_file, "body": find_body})

        data["db_config_file"] = get.config_list
        self._package_conf["db_config_file"] = get.config_list

        return public.returnResult(status=True, data=data)

    # 2024/5/6 下午3:50 获取指定目录的权限信息
    def get_path_permission(self, get):
        '''
            @name 获取指定目录的权限信息
            @author wzz <2024/5/6 下午3:51>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            import pwd
            site_path_stat = os.stat(get.check_path)
            info = pwd.getpwuid(site_path_stat.st_uid)

            return {
                "path": get.check_path,
                "pw_name": info.pw_name,
                "st_mode": site_path_stat.st_mode,
            }
        except Exception as e:
            return {}

    # 2024/5/11 下午6:02 列出至少X级的目录
    def scan_directory(self, directory):
        for root, dirs, files in os.walk(directory):
            yield root, dirs, files
            # 限制深度为2
            if root.count(os.sep) >= directory.count(os.sep) + 2:
                del dirs[:]

    # 2024/5/11 上午11:34 根据目录获取最多两层目录
    def get_dir_list(self, get):
        '''
            @name 根据目录获取最多两层目录
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.path = get.site_info["path"]
        get.dir_permission_list = []
        has_root = False
        root_path = ""
        for root, dirs, files in self.scan_directory(get.path):
            if not has_root:
                get.check_path = root
                path_perm = self.get_path_permission(get)
                path_perm["path"] = "/"
                if path_perm:
                    get.dir_permission_list.append(path_perm)
                    has_root = True
                    root_path = root

            if len(dirs) > 0:
                for d in dirs:
                    get.check_path = os.path.join(root, d)
                    path_perm = self.get_path_permission(get)
                    path_perm["path"] = get.check_path.replace(root_path, "")
                    if path_perm:
                        get.dir_permission_list.append(path_perm)

            if len(files) > 0:
                for f in files:
                    get.check_path = os.path.join(root, f)
                    path_perm = self.get_path_permission(get)
                    path_perm["path"] = get.check_path.replace(root_path, "")
                    if path_perm:
                        get.dir_permission_list.append(path_perm)

    # 2024/5/6 下午3:52 为指定目录设置权限
    def set_path_permission(self, get):
        '''
            @name 为指定目录设置权限
            @author wzz <2024/5/6 下午3:52>
            @param  get.path/s: 指定目录
                    get.permission/dict = {
                                    "pw_name": "root",
                                    "st_mode": 16877
                                }
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            import pwd
            import stat
            pw_info = pwd.getpwnam(get.permission["pw_name"])
            public.ExecShell("chown -R {}:{} {}".format(pw_info.pw_uid, pw_info.pw_gid, get.path))
            public.ExecShell("chmod -R {} {}".format(stat.S_IMODE(get.permission["st_mode"]), get.path))

            # 2024/5/6 下午3:54 检查是否设置成功
            site_path_stat = os.stat(get.path)
            info = pwd.getpwuid(site_path_stat.st_uid)
            if info.pw_name == get.permission["pw_name"] and site_path_stat.st_mode == get.permission["st_mode"]:
                return public.returnResult(status=True, msg="设置成功")
            else:
                return public.returnResult(status=False, msg="设置失败")
        except Exception as e:
            return public.returnResult(status=False, msg="设置失败: {}".format(str(e)))

    # 2024/5/6 下午3:30 获取指定网站的根目录权限和运行目录权限
    def get_site_permission(self, get):
        '''
            @name 获取指定网站的根目录权限和运行目录权限
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            get.check_path = get.site_info["path"]
            get.root_path_permission = self.get_path_permission(get)
            get.root_path_permission.pop("path")
            from panelSite import panelSite
            site_obj = panelSite()
            get.id = get.site_info["id"]
            runPath = site_obj.GetSiteRunPath(get)
            get.check_path = get.site_info["path"] + runPath["runPath"]
            get.run_path = runPath["runPath"]
            get.run_path_permission = self.get_path_permission(get)
            get.run_path_permission.pop("path")

            # 2024/5/6 下午3:37 获取指定目录权限
            get.dir_permission = {
                "root_permission": get.root_path_permission,
                "run_permission": get.run_path_permission,
            }
        except Exception as e:
            get.dir_permission = {}

    # 2024/5/6 下午5:01 获取系统类型
    def get_os_type(self):
        '''
            @name 获取系统类型
            @author wzz <2024/5/6 下午5:02>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if os.path.exists('/usr/bin/yum'):
            return "1"
        elif os.path.exists('/usr/bin/apt-get'):
            return "3"
        else:
            return "0"

    # 2024/5/6 下午4:54 安装指定运行环境
    def install_env_soft(self, get):
        '''
            @name 安装指定运行环境
            @author wzz <2024/5/6 下午4:55>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.lib_name = get.get("name/s", "")
        get.version = get.get("version/s", "")
        if get.lib_name == "" or get.version == "":
            return public.returnResult(status=False, msg="name或version不能为空")

        # 2024/3/28 上午 10:36 检测是否已存在安装任务
        mmsg = "安装[{}]".format(get.lib_name + "-" + get.version)
        if public.M('tasks').where('name=? and status=?', (mmsg, "-1")).count():
            return public.returnMsg(False, "已存在安装任务，请勿重复添加！")

        public.ExecShell("rm -rf {}/install/{}.sh".format(public.get_panel_path(), get.lib_name))
        execstr = ("wget -O /tmp/{name}.sh {url}/install/{os_type}/{name}.sh && "
                   "bash /tmp/{name}.sh install {version}").format(
            name=get.lib_name,
            url=public.get_url(),
            os_type=self.get_os_type(),
            version=get.version,
        )
        public.M('tasks').add('id,name,type,status,addtime,execstr',
                              (None, mmsg, 'execshell', '0', time.strftime('%Y-%m-%d %H:%M:%S'), execstr))

        return public.returnResult(status=True, msg="安装任务添加成功")

    # 2024/5/6 下午5:07 将指定目录压缩成tar.gz包
    def tar_path(self, get):
        '''
            @name 将指定目录压缩成tar.gz包
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.path = get.get("path/s", "")
        if get.path == "":
            return public.returnResult(status=False, msg="path不能为空")

        get.target_path = get.get("target_path/s", "")
        if get.target_path == "":
            return public.returnResult(status=False, msg="target_path不能为空")

        if not os.path.exists(get.target_path):
            public.ExecShell("mkdir -p {}".format(get.target_path))
        if not os.path.isdir(get.target_path):
            return public.returnResult(status=False, msg="保存位置必须是一个目录")

        get.package_name = get.get("package_name/s", "")
        if get.package_name == "":
            return public.returnResult(status=False, msg="package_name不能为空")
        get.package_name = get.package_name.replace(".tar.gz", "")

        # 2024/5/6 下午5:08 排除的目录
        exclude = [
            get.path + "/.git",
            get.path + "/.svn",
            get.path + "/.idea",
            get.path + "/.vscode",
            get.path + "/.vs",
            get.path + "/.github",
            get.path + "/.gitignore",
            get.path + "/.gitattributes",
            get.path + "/.gitmodules",
            get.path + "/.gitkeep",
            get.path + "/.gitlab-ci.yml",
            get.path + "/.gitlab",
            get.path + "/.gitlab-ci",
            get.path + "/.user.ini",
        ]
        try:
            exclude.extend(get.exclude_dir)
        except:
            pass

        exclude_str = ""
        for e in exclude:
            if not os.path.exists(e):
                continue

            exclude_str += " --exclude='{}'".format(e)

        temp_sites_path = os.path.join(self._temp_backup_dir, "temp_sites")
        if not os.path.exists(temp_sites_path):
            public.ExecShell("mkdir -p {}".format(temp_sites_path))
        if not os.path.exists(os.path.join(temp_sites_path, get.app_name)):
            public.ExecShell("mkdir -p {}".format(os.path.join(temp_sites_path, get.app_name)))
        public.ExecShell("\cp -r {path}/* {temp_sites_path}/{app_name}/".format(
            path=get.path,
            temp_sites_path=temp_sites_path,
            app_name=get.app_name,
        ))

        public.ExecShell(
            "cd {temp_sites_path} && tar -zcvf {target_path}/{package_name}.tar.gz {exclude_str} {target_dir} ".format(
                temp_sites_path=temp_sites_path,
                target_path=get.target_path,
                package_name=get.package_name,
                exclude_str=exclude_str,
                target_dir=get.app_name,
            ))

        if not os.path.exists("{}/{}.tar.gz".format(get.target_path, get.package_name)):
            return public.returnResult(status=False, msg="打包失败")

        return public.returnResult(status=True, msg="打包成功")

    def __get_db_name_config(self, db_name: str):
        from database import database
        database = database()
        db_find = public.M("databases").where("name=? AND LOWER(type)=LOWER('mysql')", (db_name,)).find()

        if db_find["db_type"] == 0:  # 本地数据库
            result = panelMysql.panelMysql().execute("show databases")
            isError = database.IsSqlError(result)
            if isError:
                return public.returnResult(status=False, msg=isError)
            db_password = public.M("config").where("id=?", (1,)).getField("mysql_root")
            if not db_password:
                return public.returnResult(status=False, msg="数据库密码为空！请先设置数据库密码！")
            try:
                db_port = int(panelMysql.panelMysql().query("show global variables like 'port'")[0][1])
            except:
                db_port = 3306
            if not db_password:
                return public.returnResult(status=False, msg="{} 数据库密码不能为空".format(db_find["name"]))
            conn_config = {
                "db_host": "localhost",
                "db_port": db_port,
                "db_user": db_find["username"],
                "db_password": db_find["password"],
            }
        elif db_find["db_type"] == 1:
            # 远程数据库
            conn_config = json.loads(db_find["conn_config"])
            res = database.CheckCloudDatabase(conn_config)
            if isinstance(res, dict): return public.returnResult(status=False, msg=res)
            conn_config["db_port"] = int(conn_config["db_port"])
        elif db_find["db_type"] == 2:
            conn_config = public.M("database_servers").where("id=? AND LOWER(db_type)=LOWER('mysql')",
                                                             db_find["sid"]).find()
            res = database.CheckCloudDatabase(conn_config)
            if isinstance(res, dict): return public.returnResult(status=False, msg=res)
            conn_config["db_name"] = None
            conn_config["db_port"] = int(conn_config["db_port"])
        else:
            return public.returnResult(status=False, msg="{} 未知的数据库类型".format(db_find["name"]))
        return public.returnResult(status=True, data=conn_config)

    # 2024/5/7 上午10:24 备份指定数据库为sql文件
    def backup_database(self, get):
        '''
            @name 备份指定数据库为sql文件
            @author wzz <2024/5/7 上午10:28>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.db_name = get.get("db_name/s", "")
        if get.db_name == "":
            return public.returnResult(status=False, msg="db_name不能为空")
        get.db_id = get.get("db_id/s", "")
        if get.db_id == "":
            return public.returnResult(status=False, msg="db_id不能为空")

        if not os.path.exists(self._MYSQLDUMP_BIN):
            return public.returnResult(status=False, msg="缺少备份工具，请先通过软件管理安装MySQL!")

        db_find = public.M("databases").where("id=? AND name=? AND LOWER(type)=LOWER('mysql')",
                                              (get.db_id, get.db_name)).find()
        if not db_find:
            return public.returnResult(status=False, msg="数据库[{}]不存在".format(get.db_name))

        from database import database
        database = database()

        db_name = db_find["name"]

        conn_config = self.__get_db_name_config(db_name)
        if not conn_config["status"]:
            return conn_config

        conn_config = conn_config["data"]

        mysql_obj = db_mysql.panelMysql()
        flag = mysql_obj.set_host(
            conn_config["db_host"],
            conn_config["db_port"],
            None,
            conn_config["db_user"],
            conn_config["db_password"]
        )

        if flag is False:
            return public.returnMsg(False, database.GetMySQLError(mysql_obj._ex))

        # 2024/5/7 上午10:56 备份目录待定
        self._MYSQL_BACKUP_DIR = "/www/backup/database"
        db_backup_dir = os.path.join(self._MYSQL_BACKUP_DIR, db_name)
        if not os.path.exists(db_backup_dir):
            os.makedirs(db_backup_dir)

        file_name = "{db_name}_{backup_time}_mysql_data_{number}".format(
            db_name=db_name,
            backup_time=time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()),
            number=public.GetRandomString(5),
        )

        get.db_charset = public.get_database_character(db_name)
        self._package_conf["db_character"] = get.db_charset

        set_gtid_purged = ""
        resp = public.ExecShell("{} --help | grep set-gtid-purged >> /tmp/backup_sql.log".format(
            self._MYSQLDUMP_BIN))[0]
        if resp.find("--set-gtid-purged") != -1:
            set_gtid_purged = "--set-gtid-purged=OFF"

        if db_find["db_type"] == 2:
            db_user = conn_config["db_user"]
            db_password = conn_config["db_password"]
            db_port = int(conn_config["db_port"])
        else:
            db_user = "root"
            db_password = public.M("config").where("id=?", (1,)).getField("mysql_root")
            db_port = conn_config["db_port"]

        shell = "'{mysqldump_bin}' {set_gtid_purged} --opt --skip-lock-tables --single-transaction --routines --events --skip-triggers --default-character-set='{db_charset}' --force " \
                "--host='{db_host}' --port={db_port} --user='{db_user}' --password='{db_password}' '{db_name}'".format(
            mysqldump_bin=self._MYSQLDUMP_BIN,
            set_gtid_purged=set_gtid_purged,
            db_charset=get.db_charset,
            db_host=conn_config["db_host"],
            db_port=db_port,
            db_user=db_user,
            db_password=db_password,
            db_name=db_name,
        )

        get.export_file = os.path.join(db_backup_dir, file_name + ".sql")
        shell += "| tee /tmp/backup_sql.log > '{backup_path}' ".format(backup_path=get.export_file)
        public.ExecShell(shell, env={"MYSQL_PWD": conn_config["db_password"]})

        if not os.path.exists(get.export_file):
            return public.returnResult(status=False, msg="备份失败")

        return public.returnResult(status=True, msg="备份成功", data={"file": get.export_file})

    # 2024/5/7 下午5:24 备份指定网站的伪静态
    def backup_rewrite(self, get):
        '''
            @name 备份指定网站的伪静态
            @author wzz <2024/5/7 下午5:41>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name/s", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空")

        self._rewrite_file = self._rewrite_file.format(panel_path=public.get_panel_path(), site_name=get.site_name)
        if not os.path.exists(self._rewrite_file):
            return public.returnResult(status=True, msg="伪静态文件不存在，不需要备份")

        public.ExecShell("\cp -r {rewrite_file} {backup_dir}/rewrite.conf".format(
            rewrite_file=self._rewrite_file,
            backup_dir=self._backup_dir)
        )
        if not os.path.exists("{}/rewrite.conf".format(self._backup_dir)):
            return public.returnResult(status=False, msg="备份失败")

        return public.returnResult(status=True, msg="备份成功")

    # 2024/5/9 下午2:19 还原指定包的伪静态到指定网站中
    def restore_rewrite(self, get):
        '''
            @name 还原指定包的伪静态到指定网站中
            @author wzz <2024/5/9 下午2:20>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        self._rewrite_file = self._rewrite_file.format(panel_path=public.get_panel_path(), site_name=get.site_name)

        public.ExecShell("\cp -r {_temp_import_dir}/{app_name}/rewrite.conf {_rewrite_file}".format(
            _temp_import_dir=self._temp_import_dir,
            app_name=get.app_name,
            _rewrite_file=self._rewrite_file,
        ))

    # 2024/5/9 下午6:05 还原指定上传包的伪静态到指定网站中
    def restore_upload_rewrite(self, get):
        '''
            @name 还原指定上传包的伪静态到指定网站中
            @author wzz <2024/5/9 下午6:05>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        self._rewrite_file = self._rewrite_file.format(panel_path=public.get_panel_path(), site_name=get.site_name)

        public.ExecShell("\cp -r {_upload_package_path}/{app_name}/rewrite.conf {_rewrite_file}".format(
            _upload_package_path=self._upload_package_path,
            app_name=get.app_name,
            _rewrite_file=self._rewrite_file,
        ))

    # 2024/5/8 上午9:45 获取指定数据库连接配置文件的相对路径,并将匹配到的数据库账号密码和数据库名
    def get_db_config_file(self, get):
        '''
            @name 获取指定数据库连接配置文件的相对路径,并将匹配到的数据库账号密码和数据库名
            @author wzz <2024/5/8 上午9:45>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if len(get.db_config_files) == 0:
            return public.returnResult(status=False, msg="数据库配置文件不能为空，请选择.php文件")

        get.config_list = []
        for db_conf in get.db_config_files:
            if not db_conf:
                continue
            if not os.path.exists(db_conf):
                return public.returnResult(status=False, msg="{}不存在".format(db_conf))
            if not db_conf.endswith(".php"):
                return public.returnResult(status=False, msg="{}不是PHP文件".format(db_conf))

            # 2024/5/9 上午10:06 打开指定文件，将匹配到的内容替换成self.APP_PACKAGE_DB_NAME,self.APP_PACKAGE_DB_USER,self.APP_PACKAGE_DB_PASS
            conf_body = public.readFile(db_conf)
            if not conf_body:
                return public.returnResult(status=False, msg="{}内容为空".format(db_conf))

            db_find = public.M("databases").where("id=? AND name=? AND LOWER(type)=LOWER('mysql')",
                                                  (get.db_id, get.db_name)).find()
            if db_find:
                conf_body = conf_body.replace(db_find["username"], self.APP_PACKAGE_DB_USER)
                conf_body = conf_body.replace(db_find["name"], self.APP_PACKAGE_DB_NAME)
                conf_body = conf_body.replace(db_find["password"], self.APP_PACKAGE_DB_PASS)
                public.writeFile(db_conf, conf_body)

            get.config_list.append(db_conf.replace(get.path + "/", ""))
            self._package_conf["db_config_file"] = get.config_list

        return public.returnResult(status=True, msg="据库连接配置文件处理成功")

    # 2024/5/7 下午6:32 更新json配置文件
    def update_package_conf(self, get):
        '''
            @name 更新json配置文件
            @author wzz <2024/5/7 下午6:32>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        self._package_conf["app_name"] = get.app_name
        self._package_conf["app_version"] = get.app_version
        self._package_conf["exclude_dir"] = get.exclude_dir
        self._package_conf["php_versions"] = get.php_versions
        self._package_conf["php_functions"] = get.php_functions
        self._package_conf["mysql_versions"] = get.mysql_versions
        self._package_conf["init_sql"] = get.init_sql
        self._package_conf["run_path"] = get.run_path
        self._package_conf["dir_permission"] = get.dir_permission
        self._package_conf["update_log"] = get.update_log

        public.writeFile("{}/dir_permission.json".format(self._backup_dir), json.dumps(get.dir_permission_list))
        public.writeFile("{}/package.json".format(self._backup_dir), json.dumps(self._package_conf))

    # 2024/5/8 上午10:05 将所有数据打包成一个压缩包
    def tar_package(self, get):
        '''
            @name 将所有数据打包成一个压缩包
            @author wzz <2024/5/8 上午10:06>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.package_name = get.app_name + "_v" + get.app_version
        get.app_package_dir = os.path.join(self._package_dir, get.app_name)
        if not os.path.exists(get.app_package_dir):
            public.ExecShell("mkdir -p {}".format(get.app_package_dir))

        if get.export_file != "":
            public.ExecShell("\cp -r {export_file} {temp_backup_dir}/packages/{app_name}/init.sql".format(
                export_file=get.export_file,
                temp_backup_dir=self._temp_backup_dir,
                app_name=get.app_name,
            ))

        public.ExecShell(
            "cd {temp_backup_dir}/packages/ && tar -zcvf {app_package_dir}/{package_name}.tar.gz {app_name}".format(
                temp_backup_dir=self._temp_backup_dir,
                app_package_dir=get.app_package_dir,
                package_name=get.package_name,
                app_name=get.app_name,
            ))

        public.ExecShell("rm -rf {}/*".format(self._temp_backup_dir))

        if not os.path.exists("{}/{}.tar.gz".format(get.app_package_dir, get.package_name)):
            return public.returnResult(status=False, msg="打包失败")

        get.size = os.path.getsize("{}/{}.tar.gz".format(get.app_package_dir, get.package_name))

        return public.returnResult(status=True, msg="打包成功",
                                   data={"file": "{}/{}.tar.gz".format(get.app_package_dir, get.package_name)})

    # 2024/5/8 下午3:33 更新数据库
    def update_database(self, get):
        '''
            @name 更新数据库
            @author wzz <2024/5/8 下午3:34>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        # CREATE TABLE `app_package` (
        #   `id` INTEGER PRIMARY KEY AUTOINCREMENT,
        #   `pid` INTEGER,
        #   `site_name` TEXT,
        #   `app_name` TEXT,
        #   `app_version` TEXT,
        #   `package_name` TEXT,
        #   `package_path` TEXT,
        #   `size` TEXT,
        #   `addtime` TEXT,
        #   `update_log` TEXT,
        #   `php_versions` TEXT,
        #   `php_libs` TEXT,
        #   `php_functions` TEXT,
        #   `mysql_versions` TEXT,
        #   `db_character` TEXT,
        #   `init_sql` TEXT,
        #   `db_config_file` TEXT
        # );
        find_version = public.M('app_package').where('site_name=? AND app_name=? AND app_version=?',
                                                        (get.site_name, get.app_name, get.app_version)).find()

        try:
            php_libs = json.dumps(self._package_conf["php_libs"])
        except:
            php_libs = "[]"

        if find_version and "site_name" in find_version:
            public.M('app_package').where('id=?', (find_version["id"],)).save(
                'package_name,package_path,size,update_log,addtime,php_versions,php_libs,php_functions,mysql_versions,db_character,init_sql,db_config_file',
                (get.package_name, "{}/{}.tar.gz".format(get.app_package_dir, get.package_name), get.size,
                 get.update_log, time.strftime('%Y-%m-%d %H:%M:%S'), get.php_versions, php_libs, get.php_functions,
                 get.mysql_versions, get.db_charset, get.init_sql, json.dumps(get.config_list))
            )
        else:
            public.M('app_package').add(
                'pid,site_name,app_name,app_version,package_name,package_path,size,addtime,update_log,php_libs,php_versions,php_functions,mysql_versions,db_character,init_sql,db_config_file',
                (get.site_info["id"], get.site_name, get.app_name, get.app_version, get.package_name,
                 "{}/{}.tar.gz".format(get.app_package_dir, get.package_name), get.size,
                 time.strftime('%Y-%m-%d %H:%M:%S'), get.update_log, php_libs, get.php_versions, get.php_functions,
                 get.mysql_versions, get.db_charset, get.init_sql, json.dumps(get.config_list))
            )

    # 2024/5/9 下午4:42 更新上传应用包的数据库
    def update_upload_database(self, get):
        '''
            @name 更新上传应用包的数据库
            @author wzz <2024/5/9 下午4:43>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        # CREATE TABLE `app_package_upload` (
        #   `id` INTEGER PRIMARY KEY AUTOINCREMENT,
        #   `app_name` TEXT,
        #   `app_version` TEXT,
        #   `package_name` TEXT,
        #   `package_path` TEXT,
        #   `size` TEXT,
        #   `addtime` TEXT,
        #   `update_log` TEXT,
        #   `php_versions` TEXT,
        #   `php_libs` TEXT,
        #   `php_functions` TEXT,
        #   `mysql_versions` TEXT,
        #   `db_character` TEXT,
        #   `init_sql` TEXT,
        #   `db_config_file` TEXT
        # );
        find_version = public.M('app_package_upload').where('app_name=? AND app_version=?',
                                                            (get.app_name, get.package_info["app_version"])).find()

        try:
            php_libs = json.dumps(get.package_info["php_libs"])
        except:
            php_libs = "[]"

        self._upload_package_path = self._upload_package_path.format(app_name=get.app_name)

        if find_version and "app_name" in find_version:
            public.M('app_package_upload').where('id=?', (find_version["id"],)).save(
                'package_path,size,update_log,addtime,php_versions,php_libs,php_functions,mysql_versions,db_character,init_sql,db_config_file',
                (self._upload_package_path, get.size, get.package_info["update_log"],
                    time.strftime('%Y-%m-%d %H:%M:%S'), get.package_info["php_versions"], php_libs, get.package_info["php_functions"],
                    get.package_info["mysql_versions"], get.package_info["db_character"], get.package_info["init_sql"],
                    json.dumps(get.package_info["db_config_file"]))
            )
        else:
            public.M('app_package_upload').add(
                'app_name,app_version,package_path,size,addtime,update_log,php_libs,php_versions,php_functions,mysql_versions,db_character,init_sql,db_config_file',
                (get.app_name, get.package_info["app_version"],
                 self._upload_package_path, get.size,
                 time.strftime('%Y-%m-%d %H:%M:%S'), get.package_info["update_log"], php_libs, get.package_info["php_versions"],
                    get.package_info["php_functions"], get.package_info["mysql_versions"], get.package_info["db_character"],
                    get.package_info["init_sql"], json.dumps(get.package_info["db_config_file"]))
            )

    # 2024/5/6 上午10:49 创建一件应用环境包
    def create(self, get):
        '''
            @name 创建一件应用环境包
            @author wzz <2024/5/6 上午10:50>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name/s", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空")

        get.app_name = get.get("app_name/s", "")
        if get.app_name == "":
            return public.returnResult(status=False, msg="app_name不能为空")
        get.app_version = get.get("app_version/s", "")
        if get.app_version == "":
            return public.returnResult(status=False, msg="app_version不能为空")

        get.php_versions = get.get("php_versions/s", "00")
        # get.php_libs = get.get("php_libs/s", "")
        get.php_functions = get.get("php_functions/s", "")
        get.mysql_versions = get.get("mysql_versions/s", "00")
        get.init_sql = int(get.get("init_sql/d", 0))
        get.db_name = get.get("db_name/s", "")
        if get.db_name == "" and get.init_sql == 1:
            return public.returnResult(status=False, msg="db_name不能为空")
        get.db_id = get.get("db_id/s", "")
        if get.db_id == "" and get.init_sql == 1:
            return public.returnResult(status=False, msg="db_id不能为空")

        get.exclude_dir = get.get("exclude_dir", "[]")
        if type(get.exclude_dir) == str:
            try:
                get.exclude_dir = json.loads(get.exclude_dir)
            except:
                get.exclude_dir = []
        else:
            get.exclude_dir = []

        get.db_config_files = get.get("db_config_files", "[]")
        if type(get.db_config_files) == str:
            get.db_config_files = json.loads(get.db_config_files)

        get.success_url = get.get("success_url/s", "")
        if not get.success_url.startswith("/"):
            get.success_url = get.success_url + "/"
        self._package_conf["success_url"] = get.success_url

        get.update_log = get.get("update_log/s", "")
        get.update_log = public.xssencode2(get.update_log)

        # 2024/5/9 上午11:56 处理php扩展和函数
        get.version = public.get_site_php_version(get.site_name)
        if get.version != "00":
            php_config = self.get_php_config(get)
            self._package_conf["php_libs"] = php_config["data"]["libs"]
        self._package_conf["php_functions"] = get.php_functions

        # 2024/5/7 下午6:15 处理打包目录
        self._backup_dir = os.path.join(self._temp_backup_dir, "packages", get.app_name)
        if os.path.exists(self._backup_dir):
            public.ExecShell("rm -rf {}".format(self._backup_dir))
        public.ExecShell("mkdir -p {}".format(self._backup_dir))

        get.site_info = public.M('sites').where('name=?', (get.site_name,)).find()
        if not get.site_info:
            return public.returnResult(status=False, msg="获取网站信息失败")

        get.path = get.site_info["path"]
        get.target_path = self._backup_dir
        get.package_name = get.app_name

        # 2024/5/6 上午11:01 备份数据库
        get.export_file = ""
        get.db_charset = ""
        get.config_list = []
        if get.init_sql == 1:
            bk_result = self.backup_database(get)
            if not bk_result["status"]:
                return public.returnResult(status=False, msg=bk_result["msg"])

        # 2024/5/8 上午9:51 获取指定数据库连接配置文件的相对路径
        d_result = self.get_db_config_file(get)
        if not d_result["status"]:
            return public.returnResult(status=False, msg=d_result["msg"])

        # 2024/5/6 上午11:00 备份网站目录
        self.tar_path(get)

        # 2024/5/6 下午5:41 备份伪静态
        self.backup_rewrite(get)

        # 2024/5/8 上午9:55 获取原来网站目录的根目录和运行目录权限
        self.get_site_permission(get)

        # 2024/5/11 下午6:14 获取网站目录下最多2层的文件和目录权限
        self.get_dir_list(get)

        # 2024/5/8 上午9:59 更新压缩包里面的json配置文件
        self.update_package_conf(get)

        # 2024/5/8 上午10:12 将所有数据打包成一个压缩包
        self.tar_package(get)

        # 2024/5/8 下午3:42 更新数据库
        self.update_database(get)

        # 2024/5/10 下午3:38 保存这次填的php、mysql版本和php函数到一个json文件，方便下一次创建的时候自动填充
        last_config = {
            "php_versions": get.php_versions,
            "php_functions": get.php_functions,
            "mysql_versions": get.mysql_versions,
            "init_sql": get.init_sql,
            "db_config_files": get.db_config_files,
            "db_name": get.db_name,
            "db_id": int(get.db_id) if get.db_id != "" else "",
        }
        cache.set(self.skey, last_config, 86400)

        public.WriteLog("SITE_APP_PACKAGE", "创建一键应用环境包[{}]".format(get.app_name))
        public.set_module_logs('site_app_package', 'create', 1)

        return public.returnResult(status=True, msg="打包成功")

    # 2024/5/10 下午12:10 删除指定的应用包
    def delete(self, get):
        '''
            @name 删除指定的应用包
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name/s", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空")

        get.app_name = get.get("app_name/s", "")
        if get.app_name == "":
            return public.returnResult(status=False, msg="app_name不能为空")

        get.app_version = get.get("app_version/s", "")
        if get.app_version == "":
            return public.returnResult(status=False, msg="app_version不能为空")

        find_version = public.M('app_package').where('site_name=? AND app_name=? AND app_version=?',
                                                        (get.site_name, get.app_name, get.app_version)).find()
        if not find_version:
            return public.returnResult(status=False, msg="应用包不存在")

        public.ExecShell("rm -rf {}".format(find_version["package_path"]))

        public.M('app_package').where('id=?', (find_version["id"],)).delete()
        return public.returnResult(status=True, msg="删除成功")

    # 2024/5/9 上午10:41 返回指定网站的app_package表所有数据
    def get_db_all_result(self, get):
        '''
            @name 返回指定网站的app_package表所有数据
            @author wzz <2024/5/9 上午10:42>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        # return public.M('app_package').where("site_name=?", (get.site_name,)).order('addtime desc').select()
        return public.M('app_package').where("site_name=?", (get.site_name,)).order('app_version asc').select()

    # 2024/5/9 上午11:02 返回指定网站的app_package表的某条数据
    def get_db_result(self, get):
        '''
            @name 返回指定网站的app_package表的某条数据
            @author wzz <2024/5/9 上午11:03>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        return public.M('app_package').where("site_name=? and app_name=? and app_version=?", (get.site_name, get.app_name, get.app_version)).find()

    # 2024/5/9 下午5:15 返回上传数据库中所有的数据
    def get_upload_db_all_result(self, get):
        '''
            @name 返回上传数据库中所有的数据
            @author wzz <2024/5/9 下午5:15>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        return public.M('app_package_upload').order('app_version asc').select()

    # 2024/5/9 下午5:19 返回上传数据库中指定包的数据
    def get_upload_db_result(self, get):
        '''
            @name 返回上传数据库中指定包的数据
            @author wzz <2024/5/9 下午5:19>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        return public.M('app_package_upload').where("app_name=? and app_version=?", (get.app_name, get.app_version)).find()

    # 2024/5/9 上午10:39 获取所有的应用包列表
    def get_list(self, get):
        '''
            @name 获取所有的应用包列表
            @author wzz <2024/5/9 上午10:40>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name/s", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空")

        all_result = self.get_db_all_result(get)
        for result in all_result:
            result["status"] = True
            result["info"] = "正常"
            if not os.path.exists(result["package_path"]) or os.path.getsize(result["package_path"]) < 10:
                result["status"] = False
                result["info"] = "文件小于10B或压缩包不存在，请确认包是否正常，如果异常请删除重新创建！"

            try:
                result["db_config_file"] = json.loads(result["db_config_file"])
            except:
                pass

            try:
                result["php_libs"] = json.loads(result["php_libs"])
            except:
                pass

        all_result.reverse()
        public.set_module_logs('site_app_package', 'get_list', 1)
        return public.returnResult(status=True, data=all_result)

    # 2024/5/9 上午11:17 获取指定包中的package_conf
    def get_package_conf(self, get):
        '''
            @name 获取指定包中的package_conf
            @author wzz <2024/5/9 上午11:18>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            get.package_info = json.loads(public.readFile(get.package_json_path))
        except:
            get.package_info = {}

    # 2024/5/9 下午3:09 检查当前站点的php设置是否符合包要求的php
    def check_php_mysql(self, get):
        '''
            @name 检查当前站点的php设置是否符合包要求的php
            @author wzz <2024/5/9 下午3:10>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.version = public.get_site_php_version(get.site_name)
        if not get.version in get.package_info["php_versions"]:
            return public.returnResult(status=False, msg="当前站点PHP版本[{}]不符合包要求的PHP版本[{}]".format(
                get.version,
                get.package_info["php_versions"]
            ))

        used_mysql = self.get_mysql_versions(get)["used"]
        if get.package_info["mysql_versions"] != "00":
            if not used_mysql in get.package_info["mysql_versions"]:
                return public.returnResult(status=False, msg="当前站点MySQL版本[{}]不符合包要求的MySQL版本[{}]".format(
                    used_mysql,
                    get.package_info["mysql_versions"]
                ))

        return public.returnResult(status=True, msg="当前站点PHP和MySQL版本符合包要求")

    # 2024/5/9 下午3:06 设置php函数到指定php版本
    def set_php_disable(self, get):
        '''
            @name 设置php函数到指定php版本
            @author wzz <2024/5/9 下午3:07>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if len(get.package_info["php_functions"]) != 0:
            php_config = self.get_php_config(get)
            get.disable_functions = php_config["data"]["disable_functions"]

            p_disable_functions = get.package_info["php_functions"].split(",")
            if len(p_disable_functions) != 0:
                for p_disable_function in p_disable_functions:
                    if p_disable_function in get.disable_functions:
                        get.disable_functions = get.disable_functions.replace(p_disable_function + ",", "")

                from config import config
                c = config()
                c.setPHPDisable(get)

    # 2024/5/9 下午3:07 安装php扩展到指定php版本
    def install_phplib(self, get):
        '''
            @name 安装php扩展到指定php版本
            @author wzz <2024/5/9 下午3:08>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if len(get.package_info["php_libs"]) != 0:
            for lib_name in get.package_info["php_libs"]:
                get.lib_name = lib_name["name"]
                self.install_env_soft(get)

    # 2024/5/9 下午3:08 从已经解压的应用包中找到网站文件，然后解压拷贝到指定网站目录
    def copy_site(self, get):
        '''
            @name 从已经解压的应用包中找到网站文件，然后解压拷贝到指定网站目录
            @author wzz <2024/5/9 下午3:08>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        public.ExecShell("cd {_temp_import_dir}/{app_name} && tar -zxvf {app_name}.tar.gz".format(
            _temp_import_dir=self._temp_import_dir,
            app_name=get.app_name,
        ))
        public.ExecShell("\cp -r {_temp_import_dir}/{app_name}/{app_name}/* {site_path}".format(
            _temp_import_dir=self._temp_import_dir,
            app_name=get.app_name,
            site_path=get.site_info["path"],
        ))

        for dir_permission in get.package_info["dir_permission"].keys():
            if dir_permission == "root_permission":
                get.path = get.site_info["path"]
            if dir_permission == "run_permission":
                if get.package_info["run_path"] == "/":
                    continue

                get.path = os.path.join(get.site_info["path"], get.package_info["run_path"])

            get.permission = get.package_info["dir_permission"][dir_permission]
            self.set_path_permission(get)

        # 2024/5/11 下午6:22 恢复网站目录下最多2层的文件和目录权限
        self.set_dir_list_permission(get)

    # 2024/5/11 下午6:22 恢复网站目录下最多2层的文件和目录权限
    def set_dir_list_permission(self, get):
        '''
            @name 恢复网站目录下最多2层的文件和目录权限
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            dir_permission_list = json.loads(public.readFile("{}/dir_permission.json".format(self._backup_dir)))
        except:
            return

        for dir_permission in dir_permission_list:
            get.path = os.path.join(get.site_info["path"], dir_permission["path"])
            get.permission = dir_permission
            self.set_path_permission(get)

    # 2024/5/9 下午5:52 从上传的应用包目录找到网站文件，然后解压拷贝到指定网站目录
    def copy_upload_site(self, get):
        '''
            @name 从上传的应用包目录找到网站文件，然后解压拷贝到指定网站目录
            @author wzz <2024/5/9 下午5:52>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        public.ExecShell("cd {upload_package_path} && tar -zxvf {app_name}.tar.gz".format(
            upload_package_path=self._upload_package_path,
            app_name=get.app_name,
        ))
        public.ExecShell("\cp -r {upload_package_path}/{app_name}/* {site_path}".format(
            upload_package_path=self._upload_package_path,
            app_name=get.app_name,
            site_path=get.site_info["path"],
        ))

        for dir_permission in get.package_info["dir_permission"].keys():
            if dir_permission == "root_permission":
                get.path = get.site_info["path"]
            if dir_permission == "run_permission":
                if get.package_info["run_path"] == "/":
                    continue

                get.path = os.path.join(get.site_info["path"], get.package_info["run_path"])

            get.permission = get.package_info["dir_permission"][dir_permission]
            self.set_path_permission(get)

        # 2024/5/11 下午6:22 恢复网站目录下最多2层的文件和目录权限
        self.set_dir_list_permission(get)

    # 2024/5/9 下午3:09 检查包json配置文件中的init_sql是否为1，如果是则执行查询网站关联的数据库并导入init.sql
    def import_init_sql(self, get):
        '''
            @name 检查包json配置文件中的init_sql是否为1，如果是则执行查询网站关联的数据库并导入init.sql
            @author wzz <2024/5/9 下午3:09>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if get.package_info["init_sql"] == 1:
            get.db_info = public.M('databases').where('pid=?', (get.site_info['id'],)).find()
            if get.db_info:
                for db_conf in get.package_info["db_config_file"]:
                    db_conf = os.path.join(get.site_info["path"], db_conf)
                    if not os.path.exists(db_conf):
                        continue

                    conf_body = public.readFile(db_conf)
                    if not conf_body:
                        return public.returnResult(status=False, msg="{}内容为空".format(db_conf))

                    conf_body = conf_body.replace(self.APP_PACKAGE_DB_USER, get.db_info["username"])
                    conf_body = conf_body.replace(self.APP_PACKAGE_DB_NAME, get.db_info["name"])
                    conf_body = conf_body.replace(self.APP_PACKAGE_DB_PASS, get.db_info["password"])

                    public.writeFile(db_conf, conf_body)

                from database import database
                database = database()
                get.file = "{}/{}/init.sql".format(self._temp_import_dir, get.app_name)
                get.name = get.db_info["name"]
                import_result = database.InputSql(get)
                if not import_result["status"]:
                    return public.returnResult(status=False, msg=import_result["msg"])

            return public.returnResult(status=True, msg="导入init.sql成功")

        return public.returnResult(status=True, msg="不需要导入")

    # 2024/5/9 下午6:08 检查指定上传包json配置文件中的init_sql是否为1，如果是则执行查询网站关联的数据库并导入init.sql
    def import_upload_init_sql(self, get):
        '''
            @name 检查指定上传包json配置文件中的init_sql是否为1，如果是则执行查询网站关联的数据库并导入init.sql
            @author wzz <2024/5/9 下午6:08>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.db_info = public.M('databases').where('pid=?', (get.site_info['id'],)).find()
        if get.db_info:
            if get.package_info["init_sql"] == 1:
                from database import database
                database = database()
                get.file = "{}/init.sql".format(self._upload_package_path)
                get.name = get.db_info["name"]
                import_result = database.InputSql(get)
                if not import_result["status"]:
                    return public.returnResult(status=False, msg=import_result["msg"])

            for db_conf in get.package_info["db_config_file"]:
                sample_db_conf = ""
                if "sample" in db_conf:
                    sample_db_conf = db_conf.replace("sample_", "").replace("_sample", "").replace("-sample", "").replace("sample-", "").replace(".sample", "").replace("sample.", "").replace("sample", "")
                    db_conf = db_conf.replace("sample_", "").replace("_sample", "").replace("-sample", "").replace("sample-", "").replace(".sample", "").replace("sample.", "").replace("sample", "")

                if sample_db_conf != "":
                    sample_db_conf = os.path.join(get.site_info["path"], sample_db_conf)
                    if os.path.exists(sample_db_conf):
                        conf_body = public.readFile(sample_db_conf)
                        if conf_body:
                            conf_body = conf_body.replace(self.APP_PACKAGE_DB_USER, get.db_info["username"])
                            conf_body = conf_body.replace(self.APP_PACKAGE_DB_NAME, get.db_info["name"])
                            conf_body = conf_body.replace(self.APP_PACKAGE_DB_PASS, get.db_info["password"])

                            public.writeFile(sample_db_conf, conf_body)

                    db_conf = os.path.join(get.site_info["path"], db_conf)
                    if not os.path.exists(db_conf):
                        public.ExecShell("cp -f {} {}".format(sample_db_conf, db_conf))

                    conf_body = public.readFile(db_conf)
                    if not conf_body:
                        return public.returnResult(status=False, msg="{}内容为空".format(db_conf))

                    conf_body = conf_body.replace(self.APP_PACKAGE_DB_USER, get.db_info["username"])
                    conf_body = conf_body.replace(self.APP_PACKAGE_DB_NAME, get.db_info["name"])
                    conf_body = conf_body.replace(self.APP_PACKAGE_DB_PASS, get.db_info["password"])

                    public.writeFile(db_conf, conf_body)
                else:
                    db_conf = os.path.join(get.site_info["path"], db_conf)
                    if not os.path.exists(db_conf):
                        continue

                    conf_body = public.readFile(db_conf)
                    if not conf_body:
                        return public.returnResult(status=False, msg="{}内容为空".format(db_conf))

                    conf_body = conf_body.replace(self.APP_PACKAGE_DB_USER, get.db_info["username"])
                    conf_body = conf_body.replace(self.APP_PACKAGE_DB_NAME, get.db_info["name"])
                    conf_body = conf_body.replace(self.APP_PACKAGE_DB_PASS, get.db_info["password"])

                    public.writeFile(db_conf, conf_body)

        return public.returnResult(status=True, msg="导入init.sql成功")

    # 2024/5/9 上午10:54 应用指定的应用环境包到指定网站
    def apply_site(self, get):
        '''
            @name 应用指定的应用环境包到指定网站
            @author wzz <2024/5/9 上午10:55>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name/s", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空")

        get.app_name = get.get("app_name/s", "")
        if get.app_name == "":
            return public.returnResult(status=False, msg="app_name不能为空")

        get.app_version = get.get("app_version/s", "")
        if get.app_version == "":
            return public.returnResult(status=False, msg="app_version不能为空")

        get.site_info = public.M('sites').where('name=?', (get.site_name,)).find()
        if not get.site_info:
            return public.returnResult(status=False, msg="获取网站信息失败")

        get.package_info = self.get_db_result(get)
        if not get.package_info:
            return public.returnResult(status=False, msg="获取应用包信息失败")

        if not os.path.exists(get.package_info["package_path"]):
            return public.returnResult(status=False, msg="应用包不存在")

        # 2024/5/9 上午11:15 创建临时导入目录
        self._temp_import_dir = os.path.join(self._temp_backup_dir, "import")
        if os.path.exists(self._temp_import_dir):
            public.ExecShell("rm -rf {}".format(self._temp_import_dir))
        public.ExecShell("mkdir -p {}".format(self._temp_import_dir))

        # 2024/5/9 上午11:15 解压应用包
        public.ExecShell("tar -zxvf {} -C {}".format(get.package_info["package_path"], self._temp_import_dir))

        # 2024/5/9 上午11:23 处理包里面的json配置文件
        get.package_json_path = "{_temp_import_dir}/{app_name}/package.json".format(
            _temp_import_dir=self._temp_import_dir,
            app_name=get.app_name,
        )

        self.get_package_conf(get)
        if not get.package_info:
            return public.returnResult(status=False, msg="包异常，获取package.json配置文件失败")

        # 2024/5/9 上午11:41 检查当前站点的php设置是否符合包要求的php
        check_result = self.check_php_mysql(get)
        if not check_result["status"]:
            return public.returnResult(status=False, msg=check_result["msg"])

        # 2024/5/9 上午11:53 设置php函数到指定php版本
        self.set_php_disable(get)
        # 2024/5/9 下午12:08 安装php扩展到指定php版本
        self.install_phplib(get)
        # 2024/5/9 下午2:37 还原指定包的伪静态到指定网站中
        self.restore_rewrite(get)
        # 2024/5/9 上午11:01 从已经解压的应用包中找到网站文件，然后解压拷贝到指定网站目录
        self.copy_site(get)
        # 2024/5/9 上午11:16 检查包json配置文件中的init_sql是否为1，如果是则执行查询网站关联的数据库并导入init.sql
        import_result = self.import_init_sql(get)
        if not import_result["status"]:
            return public.returnResult(status=False, msg=import_result["msg"])

        public.set_module_logs('site_app_package', 'apply_site', 1)
        return public.returnResult(status=True, msg="应用成功")

    # 2024/5/9 下午3:50 上传应用包到指定位置
    def upload_package(self, get):
        '''
            @name 上传应用包到指定位置
            @author wzz <2024/5/9 下午3:51>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if not os.path.exists(self._temp_upload_package_dir):
            public.ExecShell("mkdir -p {}".format(self._temp_upload_package_dir))

        get.f_path = get.get("f_path/s", "")
        get.f_name = get.get("f_name/s", "")
        get.f_size = get.get("f_size/s", "")
        get.f_start = get.get("f_start/s", "")
        get.blob = get.get("blob/s", "")

        from files import files
        fileObj = files()
        upload_result = fileObj.upload(get)
        if type(upload_result) == dict and not upload_result["status"]:
            return public.returnResult(status=False, msg=upload_result["msg"])

        get.size = os.path.getsize(os.path.join(self._temp_upload_package_dir, get.f_name))

        if get.size != int(get.f_size):
            return public.returnResult(status=False, msg="上传文件大小不一致，上传失败!")

        # 2024/5/9 下午4:26 解压压缩包
        public.ExecShell("tar -zxvf {}/{} -C {}".format(self._temp_upload_package_dir, get.f_name, self._upload_package_dir))

        # 2024/5/9 下午4:27 获取配置信息写入数据库
        get.app_name = get.f_name.split("_v")[0]
        # 2024/5/9 上午11:23 处理包里面的json配置文件
        get.package_json_path = "{_upload_package_dir}/{app_name}/package.json".format(
            _upload_package_dir=self._upload_package_dir,
            app_name=get.app_name,
        )

        self.get_package_conf(get)
        if not get.package_info:
            public.ExecShell("rm -rf {}".format(os.path.join(self._temp_upload_package_dir, get.f_name)))
            public.ExecShell("rm -rf {}".format(os.path.join(self._upload_package_dir, get.app_name)))
            return public.returnResult(status=False, msg="应用包异常，获取package.json配置文件失败")

        # 2024/5/9 下午4:29 更新数据库
        self.update_upload_database(get)

        public.set_module_logs('site_app_package', 'upload_package', 1)
        return public.returnResult(status=True, msg="上传成功")

    # 2024/5/9 下午5:13 获取上传列表的所有包数据
    def get_upload_list(self, get):
        '''
            @name 获取上传列表的所有包数据
            @author wzz <2024/5/9 下午5:13>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        all_result = self.get_upload_db_all_result(get)
        for result in all_result:
            result["status"] = True
            result["info"] = "正常"
            if not os.path.exists(result["package_path"]) or os.path.getsize(result["package_path"]) < 10:
                result["status"] = False
                result["info"] = "文件小于10B或压缩包不存在，请确认包是否正常，如果异常请删除重新创建！"

            try:
                result["db_config_file"] = json.loads(result["db_config_file"])
            except:
                pass

            try:
                result["php_libs"] = json.loads(result["php_libs"])
            except:
                pass

        all_result.reverse()

        public.set_module_logs('site_app_package', 'get_upload_list', 1)
        return public.returnResult(status=True, data=all_result)

    # 2024/5/10 下午12:16 删除指定的上传包
    def delete_upload(self, get):
        '''
            @name 删除指定的上传包
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.app_name = get.get("app_name/s", "")
        if get.app_name == "":
            return public.returnResult(status=False, msg="app_name不能为空")

        get.app_version = get.get("app_version/s", "")
        if get.app_version == "":
            return public.returnResult(status=False, msg="app_version不能为空")

        find_version = public.M('app_package_upload').where('app_name=? AND app_version=?',
                                                        (get.app_name, get.app_version)).find()
        if not find_version:
            return public.returnResult(status=False, msg="应用包不存在")

        public.ExecShell("rm -rf {}".format(find_version["package_path"]))

        public.M('app_package_upload').where('id=?', (find_version["id"],)).delete()
        return public.returnResult(status=True, msg="删除成功")

    # 2024/5/9 下午6:33 获取上传列表中某一个包的数据
    def get_upload_result(self, get):
        '''
            @name 获取上传列表中某一个包的数据
            @author wzz <2024/5/9 下午6:33>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"sbt 2
            tatus":True/False,"msg":"提示信息"}
        '''
        get.app_name = get.get("app_name/s", "")
        if get.app_name == "":
            return public.returnResult(status=False, msg="app_name不能为空")

        get.app_version = get.get("app_version/s", "")
        if get.app_version == "":
            return public.returnResult(status=False, msg="app_version不能为空")

        installed_phps = []
        for v in self._php_versions:
            if os.path.exists(public.get_setup_path() + "/php/" + v + "/bin/php"):
                installed_phps.append(v)

        result = self.get_upload_db_result(get)
        result["installed_phps"] = installed_phps
        result["installed_mysql"] = self.get_mysql_versions(get)["used"]

        result["status"] = True
        result["info"] = "正常"
        if not os.path.exists(result["package_path"]) or os.path.getsize(result["package_path"]) < 10:
            result["status"] = False
            result["info"] = "文件小于10B或压缩包不存在，请确认包是否正常，如果异常请删除重新创建！"

        try:
            result["db_config_file"] = json.loads(result["db_config_file"])
        except:
            pass

        try:
            result["php_libs"] = json.loads(result["php_libs"])
        except:
            pass

        return public.returnResult(status=True, data=result)

    # 2024/5/9 下午3:35 创建网站并应用应用包
    def create_site(self, get):
        '''
            @name 创建网站并应用应用包到指定网站中，如果网站已经存在则直接应用应用包到指定网站中，如果网站不存在则创建网站并应用应用包到指定网站中
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.site_name = get.get("site_name/s", "")
        if get.site_name == "":
            return public.returnResult(status=False, msg="site_name不能为空")

        get.port = "80"
        if ":" in get.site_name:
            get.port = get.site_name.split(":")[1]
            get.site_name = get.site_name.split(":")[0]

        get.webname = get.get("webname", "")
        if get.webname == "":
            return public.returnResult(status=False, msg="webname不能为空")

        get.app_name = get.get("app_name/s", "")
        if get.app_name == "":
            return public.returnResult(status=False, msg="app_name不能为空")

        get.app_version = get.get("app_version/s", "")
        if get.app_version == "":
            return public.returnResult(status=False, msg="app_version不能为空")

        get.ps = get.get("ps/s", "")
        get.ps = public.xssencode2(get.ps)

        # 2024/5/9 上午11:23 处理包里面的json配置文件
        get.package_json_path = "{_upload_package_dir}/{app_name}/package.json".format(
            _upload_package_dir=self._upload_package_dir,
            app_name=get.app_name,
        )

        self.get_package_conf(get)
        if not get.package_info:
            return public.returnResult(status=False, msg="包异常，获取package.json配置文件失败")

        self._upload_package_path = self._upload_package_path.format(app_name=get.app_name)

        # 2024/5/9 下午5:28 选择get.package_info["php_versions"]里面版本最高的php版本
        get.php_list = get.package_info["php_versions"].split(",")
        get.php_list.sort()
        get.php_list.reverse()
        for php_version in get.php_list:
            if os.path.exists(public.get_setup_path() + "/php/" + php_version + "/bin/php"):
                get.php_version = php_version
                break

        from panelSite import panelSite
        tmp_args = {
            'webname': get.webname,
            'type': 'PHP',
            'port': get.port,
            'ps': get.ps,
            'path': os.path.join("/www/wwwroot", get.site_name),
            'type_id': 0,
            'version': get.php_version,
            'ftp': False,
            'sql': False,
        }
        if get.package_info["db_config_file"]:
            tmp_args["sql"] = "MySQL"
            tmp_args["codeing"] = get.package_info["db_character"] if get.package_info["db_character"] != "" else "utf8mb4"
            tmp_args["datauser"] = get.site_name.replace(".", "_")
            tmp_args["datapassword"] = public.GetRandomString(16)

        args = public.to_dict_obj(tmp_args)
        add_site_result = panelSite().AddSite(args)
        if "status" in add_site_result and not add_site_result["status"]:
            return public.returnResult(status=False, msg=add_site_result["msg"])
        if not add_site_result["siteStatus"]:
            return public.returnResult(status=False, msg="创建网站失败")

        get.site_info = public.M('sites').where('name=?', (get.site_name,)).find()
        if not get.site_info:
            return public.returnResult(status=False, msg="获取网站信息失败")

        get.version = public.get_site_php_version(get.site_name)
        if not get.version in get.package_info["php_versions"]:
            return public.returnResult(status=False, msg="当前站点PHP版本[{}]不符合包要求的PHP版本[{}]".format(
                get.version,
                get.package_info["php_versions"]
            ))

        # 2024/5/9 上午11:53 设置php函数到指定php版本
        self.set_php_disable(get)
        # 2024/5/9 下午12:08 安装php扩展到指定php版本
        self.install_phplib(get)
        # 2024/5/9 下午2:37 还原指定上传包的伪静态到指定网站中
        self.restore_upload_rewrite(get)
        # 2024/5/9 下午5:54 从上传的应用包目录找到网站文件，然后解压拷贝到指定网站目录
        self.copy_upload_site(get)
        # 2024/5/9 上午11:16 检查包json配置文件中的init_sql是否为1，如果是则执行查询网站关联的数据库并导入init.sql
        import_result = self.import_upload_init_sql(get)

        if not import_result["status"]:
            return public.returnResult(status=False, msg=import_result["msg"])

        success_url = "http://{}".format(get.site_name)
        if "success_url" in get.package_info:
            success_url = success_url + get.package_info["success_url"]

        add_site_result["success_url"] = success_url

        public.set_module_logs('site_app_package', 'create_site', 1)
        return public.returnResult(status=True, msg="网站创建成功", data=add_site_result)
