import os.path
import sys
import json

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

from mod.base import json_response, list_args
from mod.base.pynginx.btnginx import BtNginxConf, bt_nginx_format, ng_detect, NginxInstance, CreateSiteUtil, \
    ConfigFileUtil, ConfigParseError
import public


class main:

    def __init__(self):
        self.ng_format_path = "{}/data/ng_format_data".format(public.get_panel_path())
        self.not_detect_tip_file = "{}/not_detect.pl".format(self.ng_format_path)
        self.force_detect_tip_file = "{}/force.pl".format(self.ng_format_path)
        self._panel_nginx = "/www/server/nginx/sbin/nginx"

    def detect_system_nginx(self, get=None):
        # 有强制启用时进行检查
        if not os.path.exists(self.force_detect_tip_file):
            # 没有强制启用， 并且有面板nginx时，不返回
            if os.path.exists(self._panel_nginx) and os.access(self._panel_nginx, os.X_OK):
                return json_response(True, data=[])
            # 已经关闭过的不展示
            if os.path.exists(self.not_detect_tip_file):
                return json_response(True, data=[])
        ret = []
        for i in ng_detect():
            ret.append(i.to_dict())

        return json_response(True, data=ret)

    def parse_nginx(self, get):
        ng_bin = get.get("nginx_bin/s", "")
        if not ng_bin:
            return json_response(False, msg="请选择正确的Nginx实例")
        ng_conf = get.get("nginx_conf/s", "")
        if not ng_conf:
            return json_response(False, msg="请选择正确的Nginx实例")

        working_dir = get.get("working_dir/s", "")
        if not working_dir:
            return json_response(False, msg="请选择正确的Nginx实例")

        ins = NginxInstance(nginx_bin=ng_bin, nginx_conf=ng_conf, working_dir=working_dir, running=False)
        try:
            ret = bt_nginx_format(ins, tmp_path=self.ng_format_path)
        except ConfigParseError as e:
            return json_response(False, msg="配置文件解析失败：{}".format(str(e)))

        if ret.todo_warning_list:
            msg = "配置存在以下问题，无法继续接管：<br>"
            for i, warn in enumerate(ret.todo_warning_list):
                msg += "&nbsp; &nbsp; {}、{}<br>".format(i + 1, warn)
            return json_response(False, msg=msg)

        with open(os.path.join(ret.tmp_conf_path, "site_conf.json"), "r") as f:
            site_data = json.load(f)

        return json_response(True, data=site_data)

    def save_sites(self, get):
        site_names = list_args(get, "site_names")
        logs_data = []
        try:
            json_file = os.path.join(self.ng_format_path, "bt_nginx_format/site_conf.json")
            parsed_site_data = json.loads(public.readFile(json_file))
        except:
            return json_response(False, msg="站点数据未解析失败")

        data = []
        for i in parsed_site_data:
            if not site_names:
                data.append(i)
            elif i["name"] in site_names:
                data.append(i)
                site_names.remove(i["name"])

        if site_names:
            return json_response(False, msg="未解析的站点【{}】".format(",".join(site_names)))

        parsed_data_dir = os.path.join(self.ng_format_path, "bt_nginx_format")

        c_util = ConfigFileUtil(parsed_data_dir)
        try:
            has_err = False
            create_util = CreateSiteUtil(parsed_data_dir)
            with c_util.test_env():
                for site in data:
                    if site["site_type"] == "proxy":
                        res = create_util.create_proxy_site(site)
                    elif site["site_type"] == "html":
                        res = create_util.create_html_site(site)
                    elif site["site_type"] == "PHP":
                        res = create_util.create_php_site(site)
                    else:
                        res = "无法识别的网站类型"
                    if res:
                        has_err = True
                    logs_data.append({"name": site["name"],"project_type": site["site_type"],  "msg": res or "保存成功"})

            public.writeFile(os.path.join(self.ng_format_path, "last_log.json"), json.dumps(logs_data))
            if not has_err:
                c_util.use2panel()
            return json_response(True, data=logs_data)
        except:
            return json_response(False, msg="保存站点失败")


    def close_need_detect(self, get):
        os.makedirs(os.path.dirname(self.not_detect_tip_file), exist_ok=True)
        public.writeFile(self.not_detect_tip_file, "1")
        return json_response(True)

    def ng_parsed_logs(self, get):
        if os.path.exists(os.path.join(self.ng_format_path, "last_log.json")):
            try:
                data = json.loads(public.readFile(os.path.join(self.ng_format_path, "last_log.json")))
                return json_response(True, data=data)
            except:
                pass
        return json_response(True, data=[])





