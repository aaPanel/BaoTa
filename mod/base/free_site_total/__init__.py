import datetime
import json
import os.path
import re
import time
from typing import Optional
import psutil
import public


class SiteTotalService:
    install_time_file = "/www/server/site_total/install_time.txt"

    def __init__(self):
        self.bin_path = "/www/server/site_total/site_total"
        self.service_file = "/etc/systemd/system/site_total.service"
        self.pid_file = "/www/server/site_total/pid.txt"
        self.stop_always_flags = "/www/server/site_total/stop_always.txt"


    def set_stop_always(self, flag: bool):
        """
        是否停止统计服务
        :param flag:
        :return:
        """
        if flag:
            public.writeFile(self.stop_always_flags, "1")
            self.stop()
        else:
            if os.path.exists(self.stop_always_flags):
                os.remove(self.stop_always_flags)
            self.start()

    @classmethod
    def get_install_time(cls):
        if not os.path.exists(cls.install_time_file):
            public.writeFile(cls.install_time_file, '1')
            m_time = 0
        else:
            m_time = os.path.getmtime(cls.install_time_file)
        return m_time

    @classmethod
    def set_install_time(cls):
        public.writeFile(cls.install_time_file, '1')

    @classmethod
    def install(cls):
        m_time = cls.get_install_time()
        if m_time > time.time() - 86400:  # 24小时内不反复尝试安装
            return False
        sh = "nohup curl {}/site_total/install.sh|bash 2>&1 >/dev/null &".format(public.get_url())
        cls.set_install_time()
        public.ExecShell(sh)

    @classmethod
    def upgrade(cls) -> str:
        sh = "curl {}/site_total/install.sh|bash 2>&1".format(public.get_url())
        cls.set_install_time()
        out, err = public.ExecShell(sh)
        return  out + err

    @staticmethod
    def need_update():
        file = "/www/server/panel/vhost/apache/0.site_total_log_format.conf"
        file_data = public.readFile(file)
        if not isinstance(file_data, str):
            return False
        if "logio" not in file_data:
            return True
        return False


    def start(self):
        if not os.path.exists(self.bin_path):
            self.install()
            return

        if os.path.exists(self.pid_file):
            os.remove(self.pid_file)
        if os.path.exists(self.service_file):
            public.ExecShell("systemctl start site_total")
        else:
            public.ExecShell("nohup {} 2>&1 >/dev/null &".format(self.bin_path))

    def stop(self):
        if os.path.exists(self.service_file):
            public.ExecShell("systemctl stop site_total")
        else:
            public.ExecShell("pkill site_total")

    def pid(self):
        if not os.path.exists(self.pid_file):
            return False
        data = public.readFile(self.pid_file)
        if data:
            try:
                return int(data)
            except:
                pass
        return 0

    def get_pid(self):
        for pid in psutil.pids():
            try:
                p = psutil.Process(pid)
                if os.path.realpath(p.exe()) == os.path.realpath(self.bin_path):
                    public.writeFile(self.pid_file, str(pid))
                    return pid
            except:
                pass
        return

    def running(self):
        pid = self.pid()
        if not pid:
            pid = self.get_pid()
            return bool(pid)
        else:
            if os.path.exists("/proc/%s" % pid):
                return True
            else:
                pid = self.get_pid()
                return bool(pid)

    @staticmethod
    def apache_conf_change():
        """
        检查apache配置是否需要修改
        :return:
        """
        if not public.get_webserver() == "apache":
            return
        tip_pl = "/www/server/site_total/change_apache.pl"
        if os.path.exists(tip_pl):
            return
        file = "/www/server/site_total/scripts/apache_site.conf"
        file_data = public.readFile(file)
        if not isinstance(file_data, str):
            return False
        if "|/usr/bin/logger" in file_data:
            public.writeFile(file, file_data.replace("|/usr/bin/logger", "| /usr/bin/logger"))
        ap_ext_path = "{}/vhost/apache/extension".format(public.get_panel_path())
        if not os.path.exists(ap_ext_path):
            os.makedirs(ap_ext_path)
        change = False
        for dir_name in os.listdir(ap_ext_path):
            site_file = "{}/{}/{}".format(ap_ext_path, dir_name, "site_total.conf")
            if not os.path.isfile(site_file):
                continue
            tmp_data = public.readFile(site_file)
            if not isinstance(tmp_data, str):
                continue
            if "|/usr/bin/logger" in tmp_data:
                public.writeFile(site_file, tmp_data.replace("|/usr/bin/logger", "| /usr/bin/logger"))
                change = True
        if change:
            public.ServiceReload()
        public.writeFile(tip_pl, "1")

    def reload(self):
        if os.path.exists(self.service_file):
            public.ExecShell("systemctl restart site_total")
        else:
            self.stop()
            self.start()



class SiteTotalData:

    def __init__(self):
        """
        初始化流量统计数据管理模块
        """
        s = SiteTotalService()
        if s.need_update():
            s.install()
        if not s.running() and not os.path.exists(s.stop_always_flags):
            s.start()
        else:
            s.apache_conf_change()

        self.data_dir = "/www/server/site_total/data/total"

    def get_total_day_data(self, name_list=None):
        """
        获取指定站点的流量统计数据
        :param name_list: 站点名称列表
        :return: 流量统计数据
        """
        if not os.path.exists(self.data_dir):
            return {'data': {}, 'msg': "获取失败", 'status': True}

        name_list = name_list or []
        result_data = {}
        today = datetime.date.today()
        file_name = "{}.json".format(today.strftime("%Y-%m-%d"))
        for i in name_list:
            file_path = os.path.join(self.data_dir, i, file_name)
            if os.path.exists(file_path):
                try:
                    tmp_data = json.loads(public.readFile(file_path))
                    result_data[i] = self._format_data(tmp_data)
                except:
                    result_data[i] = {
                        "one_day_total_flow": 0,
                        "one_day_total_uv": 0,
                        "one_day_total_ip": 0,
                        "one_day_total_pv": 0,
                        "one_day_total_request": 0,
                    }
            else:
                result_data[i] = {
                    "one_day_total_flow": 0,
                    "one_day_total_uv": 0,
                    "one_day_total_ip": 0,
                    "one_day_total_pv": 0,
                    "one_day_total_request": 0,
                }

        return {"data": result_data, 'msg': "获取失败", 'status': True}

    @staticmethod
    def _format_data(data) -> dict:
        data["one_day_total_flow"] = data["traffic"]
        data["one_day_total_uv"] = data["uv"]
        data["one_day_total_ip"] = data["ip"]
        data["one_day_total_pv"] = data["pv"]
        data["one_day_total_request"] = data["requests"]
        return data


class SiteTotalConfig:
    """
    站点流量统计配置管理模块
    """

    def __init__(self):
        self.version = 0.0
        self.config_file = "/www/server/site_total/config.json"

    def get_version(self):
        """
        获取流量统计模块版本
        :return: 流量统计模块版本
        """
        out, err = public.ExecShell("cd /www/server/site_total && ./site_total version")
        version_regexp = re.compile(r"Version:\s+(?P<ver>\d+\.\d+)")
        ver = version_regexp.search(out +  err)
        if not ver:
            self.version = 0.0
        else:
            self.version = ver.group("ver")

    @staticmethod
    def stop_always(status: bool = True):
        SiteTotalService().set_stop_always(bool(status))

    def read_config(self):
        """
        读取流量统计配置文件
        :return: 流量统计配置
        """
        res = public.readFile(self.config_file)
        if not res:
            return {}
        try:
            return json.loads(res)
        except:
            return {}

    def write_config(self, data: dict) -> Optional[str]:
        """
        写入流量统计配置文件
        :param data: 流量统计配置
        :return: 错误信息
        """
        public.writeFile(self.config_file, json.dumps(data))
        SiteTotalService().reload()
        return None

    @staticmethod
    def update_config(old_config: dict):
        """
        更新配置，删除不存在的站点配置
        :param old_config: 旧配置
        :return: 更新后的配置
        """
        all_sites = public.M('sites').field('id').select()
        all_ids = set([i['id'] for i in all_sites])
        if "is_open" not in old_config:
            old_config["is_open"] = True
        if "sites" not in old_config:
            old_config["sites"] = []

        remove_idx = []
        for idx, site in enumerate(old_config["sites"]):
            if site["site_id"] not in all_ids:
                remove_idx.append(idx)
            else:
                all_ids.remove(site["site_id"])

        for idx in remove_idx[::-1]:
            del old_config["sites"][idx]

        for site_id in all_ids:
            old_config["sites"].append({"site_id": site_id, "is_open": True})

        return old_config

    def one_site_status(self, site_id: int, status: bool = True) -> Optional[str]:
        """
        设置指定站点的流量统计状态，关闭/开启
        :param site_id: 站点ID
        :param status: 是否开启流量统计
        :return: 错误信息
        """
        self.get_version()
        if not float(self.version) >= 1.7:
            res = SiteTotalService().upgrade()
            self.get_version()
            if not float(self.version) >= 1.7:
                return res
        config = self.read_config()
        config = self.update_config(config)
        for site in config["sites"]:
            if site["site_id"] == site_id:
                site["is_open"] = status
                break

        if status and os.path.exists(SiteTotalService().stop_always_flags):
            SiteTotalService().set_stop_always(False)

        self.write_config(config)

    def get_status(self):
        """
        获取所有站点的流量统计状态
        :return: 流量统计状态
        """
        config = self.read_config()
        config = self.update_config(config)
        if os.path.exists(SiteTotalService().stop_always_flags):
            config["is_open"] = False
        return config
