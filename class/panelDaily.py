#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2019 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: linxiao
# Maintainer： hezhihong
#-------------------------------------------------------------------

#------------------------------
# 面板日报
# 为用户呈现服务器数据概况
#------------------------------
import os
import re
import sys
import time
import psutil
import json
import datetime

os.chdir("/www/server/panel")
sys.path.insert(0, "/www/server/panel")
sys.path.insert(0, "class/")

import public
from system import system
from panelPlugin import panelPlugin
from BTPanel import auth, cache

class panelDaily:
    def __init__(self):
        self.check_databases()
    def check_databases(self):
        """检查数据表是否存在"""
        tables = ["app_usage", "server_status", "backup_status", "daily"]
        import sqlite3
        conn = sqlite3.connect("/www/server/panel/data/system.db")
        cur = conn.cursor()
        table_key = ",".join(["'"+t+"'" for t in tables])
        sel_res = cur.execute("SELECT name FROM sqlite_master WHERE type='table' and name in ({})".format(table_key))
        res = sel_res.fetchall()
        to_commit = False
        exists_dbs = []
        if res:
            exists_dbs = [d[0] for d in res]

        if "app_usage" not in exists_dbs:
            csql = '''CREATE TABLE IF NOT EXISTS `app_usage` (
                    `time_key` INTEGER PRIMARY KEY,
                    `app` TEXT,
                    `disks` TEXT,
                    `addtime` DATETIME DEFAULT CURRENT_TIMESTAMP
                )'''
            cur.execute(csql)
            to_commit = True

        if "server_status" not in exists_dbs:
            csql = '''CREATE TABLE IF NOT EXISTS `server_status` (
                    `status` TEXT,
                    `addtime` DATETIME DEFAULT CURRENT_TIMESTAMP
                )'''
            cur.execute(csql)
            to_commit = True

        if "backup_status" not in exists_dbs:
            csql = '''CREATE TABLE IF NOT EXISTS `backup_status` (
                    `id` INTEGER,
                    `target` TEXT,
                    `status` INTEGER,
                    `msg` TEXT DEFAULT "",
                    `addtime` DATETIME DEFAULT CURRENT_TIMESTAMP
                )'''
            cur.execute(csql)
            to_commit = True

        if "daily" not in exists_dbs:
            csql = '''CREATE TABLE IF NOT EXISTS `daily` (
                    `time_key` INTEGER,
                    `evaluate` INTEGER,
                    `addtime` DATETIME DEFAULT CURRENT_TIMESTAMP
                )'''
            cur.execute(csql)
            to_commit = True

        if to_commit:
            conn.commit()
        cur.close()
        conn.close()
        return True

    def get_time_key(self, date=None):
        if date is None:
            date = time.localtime()
        time_key = 0
        time_key_format = "%Y%m%d"
        if type(date) == time.struct_time:
            time_key = int(time.strftime(time_key_format, date))
        if type(date) == str:
            time_key = int(time.strptime(date, time_key_format))
        return time_key
    
    def check_daily_status(self,get=None):
        if os.path.exists('/www/server/panel/data/start_daily.pl'):
            return True
        else:
            return False
    def set_daily_status(self,get=None):
        set_status=get.status
        if set_status == "start":
            public.set_module_logs('daily', 'set_daily_status', 1)
            date = time.time()
            yesterday_date_str = public.format_date("%Y%m%d", date - 86400)
            public.writeFile('/www/server/panel/data/start_daily.pl', yesterday_date_str)
            return public.returnMsg(True, '开启成功')
        elif set_status == "stop":
            if os.path.exists('/www/server/panel/data/start_daily.pl'):
                os.remove('/www/server/panel/data/start_daily.pl')
                return public.returnMsg(True, '关闭成功')

    def store_app_usage(self, time_key=None):
        """存储应用磁盘空间使用情况

        应用分类:
        网站,数据库,FTP,插件

        磁盘:
        名称,磁盘1已使用,磁盘1总空间-名称,磁盘2已使用,磁盘2总空间
        """

        self.check_databases()

        if time_key is None:
            time_key = self.get_time_key()
        # 重复存取判断
        import db
        sql = db.Sql().dbfile('system')
        sql1 = sql.table("system").table("app_usage")
        record = sql1.field("time_key").where("time_key=?", (time_key)).find()
        if record and "time_key" in record:
            if record["time_key"] == time_key:
                return True

        site_paths = public.M('sites').field('path').select()
        site_path_size = 0
        for p in site_paths:
            site_path = p["path"]
            if site_path:
                site_path_size += public.get_path_size(site_path)

        database_size = public.get_path_size("/www/server/data")

        ftp_paths = public.M("ftps").field("path").select()
        ftp_path_size = 0
        for p in ftp_paths:
            ftp_path = p["path"]
            if ftp_path:
                ftp_path_size += public.get_path_size(ftp_path)

        plugins_size = public.get_path_size("/www/server/panel/plugin")
        other_plugin_dirs = [
            "/www/server/total",
            "/www/server/btwaf",
            "/www/server/coll",
            "/www/server/nginx",
            "/www/server/apache",
            "/www/server/redis"
        ]
        for plugin_path in other_plugin_dirs:
            plugins_size += public.get_path_size(plugin_path)


        wwwlogs_size=public.get_path_size("/www/wwwlogs")

        default_backup_path = '/www/backup'
        backup_path = public.M('config').where("id=?", (1,)).getField('backup_path')
        if backup_path: 
            if os.path.exists(backup_path):
                default_backup_path = backup_path
        backup_size=public.get_path_size(default_backup_path)


        disk_info = system().GetDiskInfo2(human=False)
        disk_line = ""
        disk_total = 0
        disk_usage = 0
        for info in disk_info:
            disk_name = info["path"].replace("-", "_")
            if disk_line:
                disk_line += "-"
            t, u, un, per = info["size"]
            it, iu, _1, _2 = info["inodes"]
            n_disk_line = "{},{},{},{},{}".format(disk_name, u, t, iu, it)
            if disk_name == "/":
                disk_total = t
                disk_usage = u

            disk_line =  disk_line + n_disk_line

        # usage_rate = round(disk_use_size / disk_total_size, 2)

        app_line = "{},{},{},{},{},{}".format(disk_total, disk_usage, site_path_size, database_size, ftp_path_size, plugins_size,wwwlogs_size,backup_size)
        res = public.M("system").dbfile("system").table("app_usage").add("time_key,app,disks",
            (time_key, app_line, disk_line))
        if res == time_key:
            return True
        return False

    def parse_char_unit(self, num_str):
        num_val = 0
        try:
            num_val = float(num_str)
        except:
            usage = num_str
            if usage.find("G") != -1:
                usage = usage.replace("G", "")
                num_val = float(usage) * 1024 * 1024 * 1024
            elif usage.find("M") != -1:
                usage = usage.replace("M", "")
                num_val = float(usage) * 1024 * 1024
            else:
                num_val = float(usage)
        return num_val

    def parse_app_usage_info(self, info):
        """解析空间占用信息"""
        if not info:
            return {}
        
        app_data = info["app"].split(",")
        if len(app_data) == 8:
            disk_total, disk_usage, sites, databases, ftps, plugins, logs, backup= info["app"].split(",")
        elif len(app_data) == 6:
            disk_total, disk_usage, sites, databases, ftps, plugins = info["app"].split(",")
            logs = 0
            backup = 0

        disk_total, disk_usage, sites, databases, ftps, plugins = info["app"].split(",")
        disk_tmp = info["disks"].split("-")
        disk_info = {}
        for dinfo in disk_tmp:
            disk_name,usage,total,iusage,itotal= dinfo.split(",")
            tinfo = {}
            tinfo["usage"] = self.parse_char_unit(usage)
            tinfo["total"] = self.parse_char_unit(total)
            tinfo["iusage"] = iusage
            tinfo["itotal"] = itotal
            disk_info[disk_name] = tinfo
        return {
            "apps": {
                "disk_total": disk_total,
                "disk_usage": disk_usage,
                "sites": public.to_size(sites),
                "databases": public.to_size(databases),
                "ftps": ftps,
                "plugins": public.to_size(plugins),
                "logs": public.to_size(logs),
                "backup": public.to_size(backup),
            },
            "disks": disk_info
        }

    def get_app_usage(self, get):

        cur_date = time.localtime()
        cur_time_key = self.get_time_key()
        last_day = time.localtime(time.mktime((
            cur_date.tm_year, cur_date.tm_mon, cur_date.tm_mday-1, 0,0,0,0,0,0
        )))
        last_time_key = self.get_time_key(last_day)
        selector = public.M("system").dbfile("system").table("app_usage") \
        .where("time_key =? or time_key=?", (cur_time_key, last_time_key))
        res = selector.select()
        if type(res) == str or not res:
            return {}
        today_data = {}
        last_data = {}
        for usage_info in res:
            if usage_info["time_key"] == cur_time_key:
                today_data = self.parse_app_usage_info(usage_info)
            if usage_info["time_key"] == last_time_key:
                last_data = self.parse_app_usage_info(usage_info)

        if not today_data:
            return {}

        # disk
        for disk_key, disk_info in today_data["disks"].items():
            total = int(disk_info["total"])
            usage = int(disk_info["usage"])

            itotal = int(disk_info["itotal"])
            iusage = int(disk_info["iusage"])

            if last_data and disk_key in last_data["disks"].keys():
                last_data_info = last_data["disks"]
                compare_info = last_data_info[disk_key]
                ltotal = int(compare_info["total"])
                if ltotal == total:  # 扩容
                    lusage = int(compare_info["usage"])
                    increase = 0
                    diff = usage - lusage
                    if diff > 0:
                        increase = round(diff / total, 2)
                    disk_info["incr"] = increase

                litotal = int(compare_info["itotal"])
                if True:  # 扩容
                    liusage = int(compare_info["iusage"])
                    iincrease = 0
                    diff = iusage - liusage
                    if diff > 0:
                        iincrease = round(diff / itotal, 2)
                    disk_info["iincr"] = iincrease

        # apps
        today_app_data = today_data["apps"]
        disk_total = int(today_app_data["disk_total"])
        if last_data and last_data["apps"]["disk_total"] == today_app_data["disk_total"]:
            last_app_data = last_data["apps"]
            for size_key, size_value in today_app_data.items():
                if size_key == "disks": continue
                if size_key == "disk_total": continue
                if size_key == "disk_usage": continue
                size_increase = 0
                size_diff = int(size_value) - int(last_app_data[size_key])
                if size_diff>0:
                    size_increase = round(size_diff / disk_total, 2)

                today_app_data[size_key] = {
                    "val": size_value,
                    "incr": size_increase
                }
        return today_data

    def get_timestamp_interval(self, local_time):
        start = None
        end = None
        start = time.mktime((local_time.tm_year, local_time.tm_mon,
                             local_time.tm_mday, 0, 0, 0, 0, 0, 0))
        end = time.mktime((local_time.tm_year, local_time.tm_mon,
                           local_time.tm_mday, 23, 59, 59, 0, 0, 0))
        return start, end

    #服务是否启动
    def check_server(self):
        try:
            check_list = [
                "php", "nginx", "apache", "mysql", "tomcat", "pure-ftpd", "redis", "memcached"
            ]
            pp = panelPlugin()
            get = public.dict_obj()
            status_str = ""
            for serv in check_list:
                started = False
                installed = False
                get.name = serv
                info = pp.getPluginInfo(get)
                if not info:
                    continue
                versions = info["versions"]
                for v in versions:
                    if v["status"]:
                        installed = True
                    if "run" in v.keys() and v["run"]:
                        installed = True
                        started = True
                        break
                tag = 0
                if installed:
                    tag = 1
                    if not started:
                        tag = 2
                status_str += str(tag)

            if '2' in status_str:
                public.M("system").dbfile("server_status").add(
                    "status, addtime", (status_str, time.time()))
        except Exception as e:
            return True

    def get_daily_data(self, get):
        """根据日期获取面板日报数据"""
        auth_key = "IS_PRO_OR_LTD_FOR_PANEL_DAILY"
        cache_res = cache.get(auth_key)
        if not cache_res:
            try:
                pp = panelPlugin()
                soft_list = pp.get_soft_list(get)
                if soft_list["pro"] < 0 and soft_list["ltd"] < 0:
                    if os.path.exists("/www/server/panel/data/start_daily.pl"):
                        os.remove("/www/server/panel/data/start_daily.pl")
                    return {
                        "status": False,
                        "msg": "No authorization.",
                        "data": [],
                        "date": get.date
                    }
                cache.set(auth_key, True, 86400)
            except:

                return {
                    "status": False,
                    "msg": "获取不到授权信息，请检查网络是否正常->{}".format(public.get_error_info()),
                    "data": [],
                    "date": get.date
                }
        if not os.path.exists("/www/server/panel/data/start_daily.pl"):
            public.writeFile("/www/server/panel/data/start_daily.pl", get.date)
        return self.get_daily_data_local(get.date)

    def get_daily_data_local(self, date_str):
        name = ""
        date = time.strptime(date_str, "%Y%m%d")
        time_key = self.get_time_key(date)

        self.check_databases()

        addtime_fmt = time.strftime("%Y-%m-%d", date)
        score = 0
        start, end = self.get_timestamp_interval(date)
        db = public.M("system").dbfile("system")
        # cpu data
        # return high_percent_data
        cpu_detail = []
        try:
            sql= db.table("cpuio")
            cpu_data = sql.where("addtime>=? and addtime<=? and pro > 80.00", (start, end)).order("addtime").select()
            last_time = None
            #return cpu_mem_data
            cpu_high_data = []
            for record in cpu_data:
                current_time = record['addtime']
                # 如果是第一次记录或者与上条记录相隔超过5分钟（300秒），则保留此记录
                if last_time is None or current_time - last_time > 300:
                    last_time = current_time
                    sql = db.table("process_top_list")
                    process_top_data=sql.where("addtime>=? and addtime<=?", (last_time, current_time)).order("addtime").select()
                    cpu_top_data = json.loads(process_top_data[0]['cpu_top'])
                    record['pid'] = cpu_top_data[0][1]
                    record['cmdline'] = cpu_top_data[0][2]
                    cpu_high_data.append(record)
                    last_time = current_time
                    cpu_detail.append(
                        {
                            "time": last_time,
                            "name": cpu_top_data[0][2],
                            "pid": cpu_top_data[0][1],
                            "percent": record["pro"]
                        }
                    )
            # sql = db.table("process_high_percent")
            # high_percent_data = sql.where("addtime>=? and addtime<=?", (start, end)).order("addtime").select()
            # if len(high_percent_data)> 0:
            #     # st = float(high_percent_data[0]["addtime"])
            #     for hpro in high_percent_data:
            #         # _t = float(hpro["addtime"])
            #         cpu_percent = int(hpro["cpu_percent"])
            #         if cpu_percent >= 80:
            #             cpu_detail.append(
            #                 {
            #                     "time": hpro["addtime"],
            #                     "name": hpro["name"],
            #                     "pid": hpro["pid"],
            #                     "percent": cpu_percent
            #                 }
            #             )
        except:
            sql = db.table("process_top_list")
            high_percent_data = sql.where("addtime>=? and addtime<=?", (start, end)).order("addtime").select()
            if len(high_percent_data)> 0:
                for hpro in high_percent_data:
                    cpu_list = json.loads(hpro["cpu_top"])
                    for hhpro in cpu_list:
                        cpu_percent =int(hhpro[0])
                        if cpu_percent >= 80:
                            cpu_detail.append(
                            {
                                "time": hhpro[5],
                                "name": hhpro[3],
                                "pid": hhpro[1],
                                "percent": cpu_percent
                            }
                        )
        cpu_ex = len(cpu_detail)
        cpu_score = 0
        cpu_desc = ""
        if cpu_ex == 0:
            cpu_score = 20
        else:
            cpu_desc = "CPU出现过载情况"
        cpu_data = {
            "ex": cpu_ex,
            "detail": cpu_detail
        }

        # ram
        ram_detail = []
        #if len(high_percent_data)> 0:
        try:
            sql= db.table("cpuio")
            ram_data = sql.where("addtime>=? and addtime<=? and mem > 80.00", (start, end)).order("addtime").select()
            last_time = None
            ram_high_data = []
            for record in ram_data:
                current_time = record['addtime']
                # 如果是第一次记录或者与上条记录相隔超过5分钟（300秒），则保留此记录
                if last_time is None or current_time - last_time > 300:
                    last_time = current_time
                    sql = db.table("process_top_list")
                    process_top_data=sql.where("addtime>=? and addtime<=?", (last_time, current_time)).order("addtime").select()
                    ram_top_data = json.loads(process_top_data[0]['memory_top'])
                    record['pid'] = ram_top_data[0][1]
                    record['cmdline'] = ram_top_data[0][2]
                    ram_high_data.append(record)
                    last_time = current_time
                    sql = db.table("process_top_list")
                    ram_detail.append(
                        {
                            "time": last_time,
                            "name": ram_top_data[0][2],
                            "pid": ram_top_data[0][1],
                            "percent": record["mem"]
                        }
                    )
            # # st = float(high_percent_data[0]["addtime"])
            #     for hpro in high_percent_data:
            #         # _t = float(hpro["addtime"])
            #         rss = float(hpro["memory"])
            #         total = psutil.virtual_memory().total
            #         mem_percent = round(100 * rss / total, 2)
            #         if mem_percent >= 80:
            #             ram_detail.append(
            #                 {
            #                     "time": hpro["addtime"],
            #                     "name": hpro["name"],
            #                     "pid": hpro["pid"],
            #                     "percent": mem_percent
            #                 }
            #             )
        except:
            for hpro in high_percent_data:
                ram_list = json.loads(hpro["memory_top"])
                total = psutil.virtual_memory().total
                for hhpro in ram_list:
                    # return hhpro[1]
                    mem_percent =round(100 *hhpro[0] / total, 2)
                    # return hhpro[5]
                    if mem_percent >= 80:
                        ram_detail.append(
                        {
                            "time": hhpro[5],
                            "name": hhpro[3],
                            "pid": hhpro[1],
                            "percent": mem_percent
                        }
                    )
        ram_ex = len(ram_detail)
        ram_desc = ""
        ram_score = 0
        if ram_ex == 0:
            ram_score = 20
        else:
            if ram_ex > 1:
                ram_desc = "内存在多个时间点出现占用80%"
            else:
                ram_desc = "内存出现占用超过80%"
        ram_data = {
            "ex": ram_ex,
            "detail": ram_detail
        }

        # disk
        selector = public.M("system").dbfile("system").table("app_usage") \
        .where("time_key=?", (time_key,))
        res = selector.select()
        app_info = {}
        if res and type(res) != str:
            app_info = self.parse_app_usage_info(res[0])
        disk_detail = []
        if app_info:
            disk_info = app_info["disks"]
            for key, info in disk_info.items():
                usage = int(info["usage"])
                total = int(info["total"])
                usage_percent = round(usage / total, 2)
                iusage = int(info["iusage"])
                itotal = int(info["itotal"])
                if itotal > 0:
                    iusage_percent = round(iusage / itotal, 2)
                else:
                    iusage_percent = 0
                if usage_percent >= 0.8:
                    disk_detail.append({
                        "name": key,
                        "percent": usage_percent*100,
                        "ipercent": iusage_percent*100,
                        "usage": usage,
                        "total": total,
                        "iusage": iusage,
                        "itotal": itotal
                    })

        disk_ex = len(disk_detail)
        disk_desc = ""
        disk_score = 0
        if disk_ex == 0:
            disk_score = 20
        else:
            disk_desc = "有磁盘空间占用已经超过80%"

        disk_data = {
            "ex": disk_ex,
            "detail": disk_detail,
            "app_data":app_info["apps"]
        }

        # server
        exception_data = public.M("system").dbfile("system").table("server_status") \
        .where("addtime>=? and addtime<=?", (start, end,)).order("addtime desc").select()
        check_list = [
                "php", "nginx", "apache", "mysql", "tomcat", "pure-ftpd", "redis", "memcached"
            ]

        server_data = {}
        server_ex = 0
        server_desc = ""
        for i, serv in enumerate(check_list):
            if serv == "pure-ftpd":
                serv = "ftpd"
            ex = 0
            sub_detail = []
            for ss in exception_data:
                _stat = ss["status"]
                if i < len(_stat):
                    if _stat[i] == "2":
                        sub_detail.append({"time": ss["addtime"], "desc": "退出"})
                        ex += 1
                        server_ex += 1

            server_data[serv] = {
                "ex": ex,
                "detail": sub_detail
            }

        server_score = 0
        if server_ex == 0:
            server_score = 20
        else:
            server_desc = "系统级服务有出现异常退出情况"

        # backup
        no_select_data = public.M("crontab").field("name,sName,sType").where(
            "sType in (?, ?, ?) and addtime<?", ("database", "enterpriseBackup", "site", datetime.datetime.fromtimestamp(int(end)))).select()
        db_backup = set()
        for x in no_select_data:
            if x["sType"] == "database":
                db_backup.add(x["sName"])
            elif x["sType"] == "enterpriseBackup":
                s = x["name"]
                name = s[s.rfind("[")+1:s.rfind("]")]
                db_backup.add(name)
        all_db_backup = "ALL" in db_backup
        site_backup = set(x["sName"] for x in no_select_data if x["sType"] == "site")
        all_site_backup = "ALL" in site_backup
        no_db_backup = []
        no_site_backup = []

        if not all_db_backup:
            databases = public.M("databases").field("name,addtime").where("LOWER(type)=LOWER('mysql')",()).select()
            for tdb in databases:
                dt = time.strptime(tdb['addtime'], '%Y-%m-%d %H:%M:%S')
                if int(end) < int(time.mktime(dt)): continue
                db_name = tdb["name"]
                if db_name not in db_backup:
                    no_db_backup.append({"name":db_name})

        if not all_site_backup:
            sites = public.M("sites").field("name,addtime").select()
            for tsite in sites:
                dt = time.strptime(tsite['addtime'], '%Y-%m-%d %H:%M:%S')
                if int(end) < int(time.mktime(dt)): continue
                site_name = tsite["name"]
                if site_name not in site_backup:
                    no_site_backup.append({"name":site_name})

        select_data = public.M("system").dbfile("system").table("backup_status") \
            .where("addtime>=? and addtime<=?", (start, end)).select()

        backup_data = {
            "database": {
                "no_backup": no_db_backup,
                "backup": []
            },
            "site": {
                "no_backup": no_site_backup,
                "backup": []
            },
            "path": {
                "no_backup": [],
                "backup": []
            }
        }
        backup_ex = 0
        for data_line in select_data:
            status = data_line["status"]
            if status:
                continue

            target = data_line["target"]
            cron_id = data_line["id"]
            cron_info = public.M("crontab").where("id=?", (cron_id)).find()
            if not cron_info:
                if target.find("|") == -1:
                    continue
                target_tmp = target.split("|")
                backup_type = target_tmp[1]
            else:
                name = cron_info["name"]
                backup_type = cron_info["sType"]

            backup_ex += 1
            backup_time = data_line["addtime"]
            if backup_type not in backup_data.keys():
                backup_data[backup_type] = {}
                backup_data[backup_type]["backup"] = []
                backup_data[backup_type]["no_backup"] = []
            backup_data[backup_type]["backup"].append({
                "name": name,
                "target": target,
                "status": status,
                "target": target,
                "time": backup_time
            })

        backup_desc = ""
        backup_score = 0
        if backup_ex == 0:
            backup_score = 20
        else:
            backup_desc = "有计划任务备份失败"

        if len(no_db_backup) == 0:
            backup_score += 10
        else:
            if backup_desc:
                backup_desc += ";"
            backup_desc += "有数据库未及时备份"

        if len(no_site_backup) == 0:
            backup_score += 10
        else:
            if backup_desc:
                backup_desc += ";"
            backup_desc += "有网站未备份"

        # exception
        panel_ex = 0
        panel_ex_data = public.M('logs').where('addtime like ? and type=?',(str(addtime_fmt)+"%",'用户登录',)).select()
        panel_ex_detail = []
        if panel_ex_data and type(panel_ex_data) == list:
            for line in panel_ex_data:
                log = line["log"]
                if log.find("失败") >=0 or log.find("错误") >= 0:
                    panel_ex += 1
                    panel_ex_detail.append({
                        "time": time.mktime(time.strptime(line["addtime"], "%Y-%m-%d %H:%M:%S")),
                        "desc": line["log"],
                        "username": line["username"],
                    })
            panel_ex_detail.sort(key=lambda x: x["time"])

        sel_data = public.M('logs').where('type=?', ('SSH安全',)).where("addtime like ?", (str(addtime_fmt)+"%",)).select()
        # data = public.get_page(count, int(args.p), int(rows))
        ssh_detail = []
        ssh_ex = 0
        if sel_data:
            for line in sel_data:
                log = line["log"]
                if log.find("存在异常") >= 0:
                    ssh_ex += 1
                    ssh_detail.append({
                        "time": time.mktime(time.strptime(line["addtime"], "%Y-%m-%d %H:%M:%S")),
                        "desc": line["log"],
                        "username": line["username"]
                    })
            ssh_detail.sort(key=lambda x: x["time"])

        exception_desc = ""
        exception_score = 0
        if ssh_ex == 0:
            exception_score = 10
        else:
            exception_desc = "SSH有异常登录"

        if panel_ex == 0:
            exception_score += 10
        else:
            if panel_ex > 10:
                exception_score -= 10
            if exception_desc:
                exception_desc += ";"
            exception_desc += "面板登录有错误".format(panel_ex)
        exception_data = {
            "panel": {
                "ex": panel_ex,
                "detail": panel_ex_detail
            },
            "ssh": {
                "ex": ssh_ex,
                "detail": ssh_detail
            }
        }

        try:
            from projectModel.safecloudModel import main as safecloud
            safe_json=safecloud().get_security_logs(self)
            safe_data={}
            safe_data['home_risks']={}
            safe_data['home_risks']['ex']=safe_json['data']['home_risks']['count']
            safe_data['home_risks']['detail']={}
            safe_data['home_risks']['detail']['check_time']=safe_json['data']['home_risks']['check_time']
            safe_data['home_risks']['detail']['items']=safe_json['data']['home_risks']['items']

            safe_data['vulnerabilities']={}
            safe_data['vulnerabilities']['ex']=safe_json['data']['vulnerabilities']['risk_count']
            safe_data['vulnerabilities']['detail']={}
            safe_data['vulnerabilities']['detail']['check_time']=safe_json['data']['vulnerabilities']['scan_time']
            safe_data['vulnerabilities']['detail']['items']=safe_json['data']['vulnerabilities']['items']

            safe_data['malware']={}
            safe_data['malware']['ex']=safe_json['data']['malware']['count']
            safe_data['malware']['detail']={}
            safe_data['malware']['detail']['check_time']=safe_json['data']['malware']['last_scan_time']
            safe_data['malware']['detail']['risk_stats']=safe_json['data']['malware']['risk_stats']
            safe_data['malware']['detail']['items']=safe_json['data']['malware']['items']
        except:
            safe_data={}
            safe_data['home_risks']={}
            safe_data['home_risks']['ex']=0
            safe_data['home_risks']['detail']={}
            safe_data['home_risks']['detail']['check_time']= None
            safe_data['vulnerabilities']={}
            safe_data['vulnerabilities']['ex']=0
            safe_data['vulnerabilities']['detail']={}
            safe_data['vulnerabilities']['detail']['check_time']= None
            safe_data['malware']={}
            safe_data['malware']['ex']=0
            safe_data['malware']['detail']={}
            safe_data['malware']['detail']['check_time']= None
            
            

        score = cpu_score + ram_score + disk_score + server_score + backup_score + exception_score
        descs = [cpu_desc, ram_desc, disk_desc, server_desc, backup_desc, exception_desc]
        summary = []
        for d in descs:
            if d:
                if d.find(";")>=0:
                    for xd in d.split(";"):
                        summary.append(xd)
                else:
                    summary.append(d)

        if not summary:
            summary.append("服务器运行正常，请继续保持！")

        evaluate_desc = self.evaluate(score)

        # return
        return {
            "data": {
                "cpu": cpu_data,
                "ram": ram_data,
                "disk": disk_data,
                "server": server_data,
                "backup": backup_data,
                "exception": exception_data,
                "safe": safe_data
            },
            "evaluate": evaluate_desc,
            "score": score,
            "date": time_key,
            "summary": summary,
            "status": True
        }

    def evaluate(self, score):
        desc = ""
        if score >= 100:
            desc = "正常"
        elif score >= 80:
            desc = "良好"
        else:
            desc = "一般"
        return desc

    def get_daily_list(self, get):
        if not os.path.exists("/www/server/panel/data/start_daily.pl"):
            date = time.time()
            # 格式化日期为字符串
            yesterday_date_str = public.format_date("%Y%m%d", date - 86400)
            public.writeFile("/www/server/panel/data/start_daily.pl", yesterday_date_str)
        import db
        sql = db.Sql().dbfile('system')
        daily_list = sql.table("daily").where("time_key>?", 0).select()
        data = []
        if not isinstance(daily_list, list):
            return data
        for line in daily_list:
            line["evaluate"] = self.evaluate(line["evaluate"])
            data.append(line)
        return data
