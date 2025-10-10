import datetime
import json
import os.path
import time

import psutil
import public


class SiteTotalService:
    install_time_file = "/www/server/site_total/install_time.txt"

    def __init__(self):
        self.bin_path = "/www/server/site_total/site_total"
        self.service_file = "/etc/systemd/system/site_total.service"
        self.pid_file = "/www/server/site_total/pid.txt"

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


class SiteTotalData:

    def __init__(self):
        s = SiteTotalService()
        if s.need_update():
            s.install()
        if not s.running():
            s.start()
        else:
            s.apache_conf_change()

        self.data_dir = "/www/server/site_total/data/total"

    def get_total_day_data(self, name_list=None):
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
                    result_data[i] = {"one_day_total_flow": 0}
            else:
                result_data[i] = {"one_day_total_flow": 0}

        return {"data": result_data, 'msg': "获取失败", 'status': True}

    @staticmethod
    def _format_data(data) -> dict:
        data["one_day_total_flow"] = data["traffic"]
        return data
