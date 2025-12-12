# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: cjxin <cjxin@bt.cn>
# -------------------------------------------------------------------

# 备份
# ------------------------------
import os, sys, re, json, shutil, psutil, time
from panelModel.base import panelBase
import public, config, panelTask

try:
    from BTPanel import cache
except:pass

class main(panelBase):
    __table = 'task_list'
    # public.check_database_field("ssl_data.db","ssl_info")
    task_obj = panelTask.bt_task()

    def __init__(self):
        pass


    """
    @name 获取面板日志
    """
    def get_update_logs(self,get):
        try:

            skey = 'panel_update_logs'
            res = cache.get(skey)
            if res: return res

            res = public.httpPost('https://www.bt.cn/Api/getUpdateLogs?type=Linux',{})

            start_index = res.find('(') + 1
            end_index = res.rfind(')')
            json_data = res[start_index:end_index]

            res = json.loads(json_data)
            cache.set(skey,res,60)
        except:
            res = []

        return res

    # 2025/1/6 16:38 检查指定账户是否已经领取满了14天企业版体验卷
    def check_exp_ltd(self):
        '''
            @name 检查指定账户是否已经领取满了14天企业版体验卷
        '''
        data = public.get_user_info()
        data['o'] = public.get_oem_name()
        if data['o'] != "install_ltd":
            return {
                "no_exceed_limit": False,
                "user_give": False
            }

        from BTPanel import cache
        ikey = 'check_exp_ltd_cache'
        data_cache = cache.get(ikey)
        if data_cache: return data_cache

        sUrl = 'https://api.bt.cn/auth/GetUserGiveAway'
        import panelSSL
        ssl_obj = panelSSL.panelSSL()
        pdata = {"data": ssl_obj.De_Code(data)}
        try:
            exp_ltd_info = json.loads(public.httpPost(sUrl, pdata))
        except:
            return {
                "no_exceed_limit": False,
                "user_give": False
            }

        if not exp_ltd_info:
            return {
                "no_exceed_limit": False,
                "user_give": False
            }

        # {
        #     "no_exceed_limit": true, // 没有超过限制，如果这个值是False就表示不能再领取，超过最大使用次数了
        #     "user_give": false // 表示本机当前的时间线下是否领取了体验卷
        # }
        return exp_ltd_info

    # 2025/2/24 10:50 企业版宝塔面板安装标识检测
    def get_exp_ltd(self, get):
        '''
            @name 企业版宝塔面板安装标识检测
        '''
        data = {
            "install_ltd": False if not os.path.exists("data/install_ltd.pl") else True,
            "exp_ltd": self.check_exp_ltd(),
            "aliyun_ecs_ltd": False if not os.path.exists("data/aliyun_ecs_ltd.pl") else True,
        }
        return data

    def get_public_config(self, args):
        """
        @name 获取公共配置
        """

        _config_obj = config.config()
        data = _config_obj.get_config(args)

        data['task_list'] = self.task_obj.get_task_lists(args)
        data['task_count'] = public.M('tasks').where("status!=?", ('1',)).count()
        data['get_pd'] = self.get_pd(args)
        data["install_ltd"] = False if not os.path.exists("data/install_ltd.pl") else True
        data["aliyun_ecs_ltd"] = False if not os.path.exists("data/aliyun_ecs_ltd.pl") else True
        data["login_origin"] = _config_obj.get_login_origin()
        data['ipv6'] = ''
        if _config_obj.get_ipv6_listen(None): data['ipv6'] = 'checked'
        data['is_local'] = ''
        if public.is_local(): data['is_local'] = 'checked'

        if data['get_pd'] and data['get_pd'][2] != -1:
            time_diff = (data['get_pd'][2]-int(time.time())) % (365*86400)
            data['active_pro_time'] = int(time.time()) - (365*86400 - time_diff)
        else:
            data['active_pro_time'] = 0
        data['status_code'] = _config_obj.get_not_auth_status()
        if os.path.exists('/www/server/panel/config/api.json'):
            try:
                res = json.loads(public.readFile('/www/server/panel/config/api.json'))
                data['api'] = 'checked' if res['open'] else ''
            except:
                public.ExecShell('rm -f /www/server/panel/config/api.json')
                data['api'] = ''
        else:
            data['api'] = ''
        data['total'] = os.path.exists('/www/server/panel/plugin/total') or os.path.exists('/www/server/panel/plugin/monitor')
        data['disk_usage'] = public.get_disk_usage(public.get_panel_path())
        data['uid'] = ''
        if os.path.exists('/www/server/panel/data/userInfo.json'):
            res = public.readFile('/www/server/panel/data/userInfo.json')
            if res:
                try:
                    res = json.loads(res)
                    data['uid'] = res['uid']
                except:
                    pass
        #检测是否有迁移还原任务
        if os.path.exists('/www/server/panel/data/migration.pl'):
            data['migration'] = True
        else:
            data['migration'] = False
        # 判断是否隐藏广告和企业版标识
        if os.path.exists('/www/server/panel/data/hide_ad.pl'):
            data['hide_ad'] = True
        else:
            data['hide_ad'] = False
        data['o'] = public.get_oem_name()
        return data

    def get_pd(self, get):
        from BTPanel import cache
        tmp = -1
        try:
            import panelPlugin
            # get = public.dict_obj()
            # get.init = 1
            tmp1 = panelPlugin.panelPlugin().get_cloud_list(get)
        except:
            tmp1 = None
        if tmp1:
            tmp = tmp1[public.to_string([112, 114, 111])]
            ltd = tmp1.get('ltd', -1)
        else:
            ltd = -1
            tmp4 = cache.get(
                public.to_string([112, 95, 116, 111, 107, 101, 110]))
            if tmp4:
                tmp_f = public.to_string([47, 116, 109, 112, 47]) + tmp4
                if not os.path.exists(tmp_f): public.writeFile(tmp_f, '-1')
                tmp = public.readFile(tmp_f)
                if tmp: tmp = int(tmp)
        if not ltd: ltd = -1
        if tmp == None: tmp = -1
        if ltd < 1:
            if ltd == -2:
                tmp3 = public.to_string([
                    60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34,
                    98, 116, 108, 116, 100, 45, 103, 114, 97, 121, 34, 62, 60,
                    115, 112, 97, 110, 32, 115, 116, 121, 108, 101, 61, 34, 99,
                    111, 108, 111, 114, 58, 32, 35, 102, 99, 54, 100, 50, 54,
                    59, 102, 111, 110, 116, 45, 119, 101, 105, 103, 104, 116,
                    58, 32, 98, 111, 108, 100, 59, 109, 97, 114, 103, 105, 110,
                    45, 114, 105, 103, 104, 116, 58, 53, 112, 120, 34, 62,
                    24050, 36807, 26399, 60, 47, 115, 112, 97, 110, 62, 60, 97,
                    32, 99, 108, 97, 115, 115, 61, 34, 98, 116, 108, 105, 110,
                    107, 34, 32, 111, 110, 99, 108, 105, 99, 107, 61, 34, 98,
                    116, 46, 115, 111, 102, 116, 46, 117, 112, 100, 97, 116,
                    97, 95, 108, 116, 100, 40, 41, 34, 62, 32493, 36153, 60,
                    47, 97, 62, 60, 47, 115, 112, 97, 110, 62
                ])
            elif tmp == -1:
                tmp3 = public.to_string([
                    60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34,
                    98, 116, 112, 114, 111, 45, 102, 114, 101, 101, 34, 32,
                    111, 110, 99, 108, 105, 99, 107, 61, 34, 98, 116, 46, 115,
                    111, 102, 116, 46, 117, 112, 100, 97, 116, 97, 95, 99, 111,
                    109, 109, 101, 114, 99, 105, 97, 108, 95, 118, 105, 101,
                    119, 40, 41, 34, 32, 116, 105, 116, 108, 101, 61, 34,
                    28857, 20987, 21319, 32423, 21040, 21830, 19994, 29256, 34,
                    62, 20813, 36153, 29256, 60, 47, 115, 112, 97, 110, 62
                ])
            elif tmp == -2:
                tmp3 = public.to_string([
                    60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34,
                    98, 116, 112, 114, 111, 45, 103, 114, 97, 121, 34, 62, 60,
                    115, 112, 97, 110, 32, 115, 116, 121, 108, 101, 61, 34, 99,
                    111, 108, 111, 114, 58, 32, 35, 102, 99, 54, 100, 50, 54,
                    59, 102, 111, 110, 116, 45, 119, 101, 105, 103, 104, 116,
                    58, 32, 98, 111, 108, 100, 59, 109, 97, 114, 103, 105, 110,
                    45, 114, 105, 103, 104, 116, 58, 53, 112, 120, 34, 62,
                    24050, 36807, 26399, 60, 47, 115, 112, 97, 110, 62, 60, 97,
                    32, 99, 108, 97, 115, 115, 61, 34, 98, 116, 108, 105, 110,
                    107, 34, 32, 111, 110, 99, 108, 105, 99, 107, 61, 34, 98,
                    116, 46, 115, 111, 102, 116, 46, 117, 112, 100, 97, 116,
                    97, 95, 112, 114, 111, 40, 41, 34, 62, 32493, 36153, 60,
                    47, 97, 62, 60, 47, 115, 112, 97, 110, 62
                ])
            if tmp >= 0 and ltd in [-1, -2]:
                if tmp == 0:
                    tmp2 = public.to_string([27704, 20037, 25480, 26435])
                    tmp3 = public.to_string([
                        60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61,
                        34, 98, 116, 112, 114, 111, 34, 62, 123, 48, 125, 60,
                        115, 112, 97, 110, 32, 115, 116, 121, 108, 101, 61, 34,
                        99, 111, 108, 111, 114, 58, 32, 35, 102, 99, 54, 100,
                        50, 54, 59, 102, 111, 110, 116, 45, 119, 101, 105, 103,
                        104, 116, 58, 32, 98, 111, 108, 100, 59, 34, 62, 123,
                        49, 125, 60, 47, 115, 112, 97, 110, 62, 60, 47, 115,
                        112, 97, 110, 62
                    ]).format(
                        public.to_string([21040, 26399, 26102, 38388, 65306]),
                        tmp2)
                else:
                    tmp2 = time.strftime(
                        public.to_string([37, 89, 45, 37, 109, 45, 37, 100]),
                        time.localtime(tmp))
                    tmp3 = public.to_string([
                        60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61,
                        34, 98, 116, 112, 114, 111, 34, 62, 21040, 26399,
                        26102, 38388, 65306, 60, 115, 112, 97, 110, 32, 115,
                        116, 121, 108, 101, 61, 34, 99, 111, 108, 111, 114, 58,
                        32, 35, 102, 99, 54, 100, 50, 54, 59, 102, 111, 110,
                        116, 45, 119, 101, 105, 103, 104, 116, 58, 32, 98, 111,
                        108, 100, 59, 109, 97, 114, 103, 105, 110, 45, 114,
                        105, 103, 104, 116, 58, 53, 112, 120, 34, 62, 123, 48,
                        125, 60, 47, 115, 112, 97, 110, 62, 60, 97, 32, 99,
                        108, 97, 115, 115, 61, 34, 98, 116, 108, 105, 110, 107,
                        34, 32, 111, 110, 99, 108, 105, 99, 107, 61, 34, 98,
                        116, 46, 115, 111, 102, 116, 46, 117, 112, 100, 97,
                        116, 97, 95, 112, 114, 111, 40, 41, 34, 62, 32493,
                        36153, 60, 47, 97, 62, 60, 47, 115, 112, 97, 110, 62
                    ]).format(tmp2)
            else:
                tmp3 = public.to_string([
                    60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34,
                    98, 116, 108, 116, 100, 45, 103, 114, 97, 121, 34, 32, 111,
                    110, 99, 108, 105, 99, 107, 61, 34, 98, 116, 46, 115, 111,
                    102, 116, 46, 117, 112, 100, 97, 116, 97, 95, 108, 116,
                    100, 40, 41, 34, 32, 116, 105, 116, 108, 101, 61, 34,
                    28857, 20987, 21319, 32423, 21040, 20225, 19994, 29256, 34,
                    62, 20813, 36153, 29256, 60, 47, 115, 112, 97, 110, 62
                ])
        else:
            tmp3 = public.to_string([
                60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34, 98,
                116, 108, 116, 100, 34, 62, 21040, 26399, 26102, 38388, 65306,
                60, 115, 112, 97, 110, 32, 115, 116, 121, 108, 101, 61, 34, 99,
                111, 108, 111, 114, 58, 32, 35, 102, 99, 54, 100, 50, 54, 59,
                102, 111, 110, 116, 45, 119, 101, 105, 103, 104, 116, 58, 32,
                98, 111, 108, 100, 59, 109, 97, 114, 103, 105, 110, 45, 114,
                105, 103, 104, 116, 58, 53, 112, 120, 34, 62, 123, 125, 60, 47,
                115, 112, 97, 110, 62, 60, 97, 32, 99, 108, 97, 115, 115, 61,
                34, 98, 116, 108, 105, 110, 107, 34, 32, 111, 110, 99, 108,
                105, 99, 107, 61, 34, 98, 116, 46, 115, 111, 102, 116, 46, 117,
                112, 100, 97, 116, 97, 95, 108, 116, 100, 40, 41, 34, 62,
                32493, 36153, 60, 47, 97, 62, 60, 47, 115, 112, 97, 110, 62
            ]).format(
                time.strftime(
                    public.to_string([37, 89, 45, 37, 109, 45, 37, 100]),
                    time.localtime(ltd)))

        return tmp3, tmp, ltd

    @staticmethod
    def set_backup_path(get):
        try:
            backup_path = get.backup_path.strip().rstrip("/")
        except AttributeError:
            return public.returnMsg(False, "参数错误")

        if not os.path.exists(backup_path):
            return public.returnMsg(False, "指定目录不存在")

        if backup_path[-1] == "/":
            backup_path = backup_path[:-1]

        import files
        try:
            from BTPanel import session
        except:
            session = None
        fs = files.files()

        if not fs.CheckDir(get.backup_path):
            return public.returnMsg(False, '不能使用系统关键目录作为默认备份目录')
        if session is not None:
            session['config']['backup_path'] = os.path.join('/', backup_path)
        db_backup = backup_path + '/database'
        site_backup = backup_path + '/site'

        if not os.path.exists(db_backup):
            try:
                os.makedirs(db_backup, 384)
            except:
                public.ExecShell('mkdir -p ' + db_backup)

        if not os.path.exists(site_backup):
            try:
                os.makedirs(site_backup, 384)
            except:
                public.ExecShell('mkdir -p ' + site_backup)

        public.M('config').where("id=?", ('1',)).save('backup_path', (get.backup_path,))
        public.WriteLog('TYPE_PANEL', 'PANEL_SET_SUCCESS', (get.backup_path,))

        public.restart_panel()
        return public.returnMsg(True, "设置成功")
    
    def get_soft_status(self, get):
        if not hasattr(get, 'name'): return public.returnMsg(False, '参数错误')
        s_status = False
        status = False
        setup = False
        name = get.name.strip()
        if name == 'web': name = public.get_webserver()
        version = ''
        if name == 'sqlite':
            status = True
        if name in ['mysql', 'pgsql', 'sqlserver', 'mongodb', 'redis']:
            count = public.M('database_servers').where("LOWER(db_type)=LOWER(?)", (name,)).count()
            if count > 0: status = True
        if os.path.exists('/www/server/{}'.format(name)) and len(os.listdir('/www/server/{}'.format(name))) > 2 :
            if not public.M('tasks').where("name like ? and status == -1", ('安装%{}%'.format(name.replace('-', '')),)).count() > 0:
                status = True
                setup = True
        if name == 'openlitespeed':
            status = os.path.exists('/usr/local/lsws/bin/lswsctrl')
            setup = status

        path_data = {
                "nginx": "/www/server/nginx/logs/nginx.pid",
                "mysql": "/www/server/data/localhost.localdomain.pid",
                "apache": "/www/server/apache/logs/httpd.pid",
                "pure-ftpd": "/var/run/pure-ftpd.pid",
                "redis": "/www/server/redis/redis.pid",
                "pgsql":"/www/server/pgsql/data_directory/postmaster.pid",
                "openlitespeed":"/tmp/lshttpd/lshttpd.pid"
            }
        if status:
            if name == 'mysql':
                datadir = public.get_datadir()
                if datadir:
                    path_data["mysql"] = "{}/{}.pid".format(datadir, public.get_hostname())
            if name in path_data.keys():
                if os.path.exists(path_data[name]):
                    pid = public.readFile(path_data[name])
                    if pid:
                        try:
                            psutil.Process(int(pid))
                            s_status = True
                        except:
                            pass

        if not s_status:
                other_check = {   # 软件名称 to 进程名称
                    "mysql": "mysqld",
                    # "pure-ftpd": "pure-ftpd",
                    # "nginx": "nginx"
                }
                if name in other_check:
                    for proc in psutil.process_iter():
                        if proc.name() == other_check[name]:
                            cmdline = proc.cmdline()
                            if cmdline and any("/www/server" in arg for arg in cmdline):
                                s_status = True
                                public.writeFile(path_data[name], str(proc.pid))
                                break
        version_data = {
            "nginx": '/www/server/nginx/version.pl',
            "mysql": "/www/server/mysql/version.pl",
            "pgsql": "/www/server/pgsql/data/PG_VERSION",
            "apache": "/www/server/apache/version.pl",
            "pure-ftpd": "/www/server/pure-ftpd/version.pl",
            "openlitespeed":"/usr/local/lsws/VERSION",
            "redis": "/www/server/redis/version.pl"
        }
        if name in version_data.keys():
            if os.path.exists(version_data[name]):
                version = public.readFile(version_data[name]).strip()
        title_data = {
            "nginx": "Nginx",
            "mysql": "MySQL",
            "pgsql": "PostgreSQL",
            "mongodb": "MongoDB",
            "redis": "Redis",
            "apache": "Apache",
            "openlitespeed": "OpenLiteSpeed",
            "pure-ftpd": "Pure-FTPd",
        }
        s_version_data = {
            'mysql': 'mysqld',
            'apache': 'httpd',
        }
        
        data = {
            "status": status,
            "s_status": s_status,
            "msg": '',
            "version": version,
            "name": name.replace('-', ''),
            "title": title_data.get(name, name),
            "admin": os.path.exists('/www/server/panel/plugin/' + name),
            "s_version": s_version_data.get(name, name),
            "setup": setup
        }
        return data
    
    def get_xfs_disk(self, get):
        try:
            path = get.path.strip()
            res = self.__get_path_dev_mountpoint(path)
            if res is None:
                return public.returnMsg(False, "当前分区不为xfs分区!此功能不可用!")
            if 'prjquota' not in res["opts"]:
                return public.returnMsg(False, "指定xfs分区未开启目录配额功能!请先在/etc/fstab中{}分区增加prjquota参数 \n fstab配置示例：/dev/vdc1 /data xfs defaults,prjquota 0 0 ".format(res['mountpoint']))
            return public.returnMsg(True, res)
        except Exception as e:
            return public.returnMsg(False, str(e))
        
    def __get_path_dev_mountpoint(self, path: str):
        disk_list = self.__get_xfs_disk()
        disk_list.sort(key=lambda item: (item["mountpoint"].count("/"), len(item["mountpoint"][item["mountpoint"].find("/"):])), reverse=True)
        for disk in disk_list:
            if path.startswith(disk["mountpoint"]):
                return disk
        return None


    def __get_xfs_disk(self) -> list:
        disks = []
        for disk in psutil.disk_partitions():
            if disk.fstype == "xfs":
                disk_info = {
                    "mountpoint": disk.mountpoint,  # 磁盘挂载点
                    "device": disk.device,  # 磁盘分区设备名称
                    "free": psutil.disk_usage(disk.mountpoint).free,  # 磁盘分区设备名称
                    "opts": disk.opts.split(","),  # 磁盘分区的选项
                }
                disks.append(disk_info)
        return disks

    def get_ftp_mysql_status(self, get):
        data = {}
        data['ftp'] = self.get_soft_status(public.to_dict_obj({'name': 'pure-ftpd'}))['setup']
        data['mysql'] = self.get_soft_status(public.to_dict_obj({'name': 'mysql'}))['setup']
        return data

    # 获取时区
    @staticmethod
    def GetZoneinfo(get):
        zone_list = (
            'Asia', 'Africa', 'America', 'Antarctica', 'Arctic',
            'Atlantic', 'Australia', 'Europe', 'Indian', 'Pacific'
        )
        path = "/etc/localtime"
        if os.path.islink(path):
            real_path = os.readlink(path)
            current_timezone = os.path.basename(real_path)
            current_area = os.path.basename(os.path.dirname(real_path))
        elif os.path.exists("/etc/timezone"):
             current_tz = public.readFile("/etc/timezone").strip().split('/')
             if len(current_tz) > 1:
                 current_area = current_tz[0]
                 current_timezone = current_tz[1]
             else:
                 current_timezone = current_tz[0]
                 current_area = 'Asia'
        else:
            if not os.path.exists(path):
                if os.path.exists('/usr/share/zoneinfo/Asia/Shanghai'):
                    current_timezone = 'Shanghai'
                    current_area = 'Asia'
                    os.symlink('/usr/share/zoneinfo/Asia/Shanghai', path)
                else:
                    return public.returnMsg(False, "无法获取时区信息")
            else:
                out, _ = public.ExecShell("date +%z")
                if re.match('^[+-]\d{4}$', out):
                    current_area = "Etc"
                    out = out[:3] if out[1] != "0" else (out[0] + out[2])
                    current_timezone = "UTC{}".format(out[:3])
                else:
                    return public.returnMsg(False, "无法获取时区信息")

        if get.zone:
            target_area = get.zone
        else:
            if current_area == "Etc":
                target_area = "Asia"
            else:
                target_area = current_area
        area_list = []
        if not os.path.exists('/usr/share/zoneinfo/' + target_area):
            return public.returnMsg(False, "无法获取时区信息")
        for area in os.listdir('/usr/share/zoneinfo/' + target_area):
            if os.path.isdir('/usr/share/zoneinfo/' + target_area + '/' + area):
                continue
            area_list.append(area)

        data = {
            'zone': {'0': current_area, '1': current_timezone},
            'zoneList': zone_list,
            'areaList': sorted(area_list)
        }
        return data

    # 设置时区
    @staticmethod
    def SetZone(get):
        target_path = '/usr/share/zoneinfo/' + get.zone + '/' + get.area
        if not os.path.exists(target_path):
            return public.returnMsg(False, "无法设置时区,目标时区不存在!")
        if os.path.exists('/etc/localtime'):
            os.remove('/etc/localtime')
        os.symlink(target_path, '/etc/localtime')
        if os.path.exists('/etc/timezone'): # Debian 系机器会有，所以同步更新一下
            public.writeFile('/etc/timezone', get.zone + '/' + get.area + "\n")

        time.tzset() # 重新加载时区
        return {'status': True, 'msg': "设置成功!"}
