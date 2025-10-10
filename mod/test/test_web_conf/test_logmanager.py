import json
import os.path
import shutil
import sys

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

from mod.test.test_web_conf import WebBaseTestcase, PREFIX, NGINX_CONFIG_CASE, APACHE_CONFIG_CASE
from mod.base.web_conf import ConfigMgr, LogMgr
from mod.base.web_conf.util import GET_CLASS

LOG_FORMAT_1 = json.dumps([
    "server_addr", "server_port", "host", "remote_addr", "remote_port", "protocol", "method", "uri",
    "status", "sent_bytes", "referer", "user_agent", "take_time"
])
LOG_FORMAT_2 = json.dumps([
    "server_addr", "host", "remote_addr", "remote_port", "protocol", "method", "uri",
    "status", "user_agent", "take_time"
])


class TestRealLogMgr(WebBaseTestcase):
    log_mgr = LogMgr(PREFIX)

    def test_log_format_mager(self):
        # 查看初始
        get = GET_CLASS()
        get.site_name = self.site_name
        print(self.log_mgr.log_format_data(get))

        # 添加 一个格式
        get = GET_CLASS()
        get.format_name = "btlog1"
        get.keys = LOG_FORMAT_1
        get.space_character = "|"
        print(self.log_mgr.add_log_format(get))

        # 添加 第二个格式
        get = GET_CLASS()
        get.format_name = "btlog2"
        get.keys = LOG_FORMAT_2
        get.space_character = " "
        print(self.log_mgr.add_log_format(get))

        # 修改 第二个格式
        get = GET_CLASS()
        get.format_name = "btlog2"
        get.keys = LOG_FORMAT_2
        get.space_character = "|"
        print(self.log_mgr.modify_log_format(get))

        # 删除 第一个格式
        # get = GET_CLASS()
        # get.format_name = "btlog1"
        # print(self.log_mgr.remove_log_format(get))

        # 查看格式
        get = GET_CLASS()
        get.site_name = self.site_name
        print(self.log_mgr.log_format_data(get))

    def test_set_site_log_format(self):
        # 设置使用 第二个
        get = GET_CLASS()
        get.site_name = self.site_name
        get.format_name = "btlog2"
        print(self.log_mgr.set_site_log_format(get))

        # 修改 第二个格式
        get = GET_CLASS()
        get.format_name = "btlog2"
        get.keys = LOG_FORMAT_2
        get.space_character = "|"
        print(self.log_mgr.modify_log_format(get))

        # 设置使用 第一个
        get = GET_CLASS()
        get.site_name = self.site_name
        get.format_name = "btlog1"
        print(self.log_mgr.set_site_log_format(get))

        # 查看格式
        get = GET_CLASS()
        get.site_name = self.site_name
        print(self.log_mgr.log_format_data(get))

    def test_site_log_path(self):
        # 查看初始
        get = GET_CLASS()
        get.site_name = self.site_name
        print(self.log_mgr.get_site_log_path(get))

        # 修改日志路径
        get = GET_CLASS()
        get.site_name = self.site_name
        get.log_path = "/www/test/logs"
        print(self.log_mgr.set_site_log_path(get))

    def test_site_crontab_log(self):
        get = GET_CLASS()
        get.site_name = self.site_name
        get.hour = "1"
        get.minute = "1"
        get.save = "180"
        print(self.log_mgr.site_crontab_log(get))

    def setUp(self) -> None:
        self.reset_site_config()
        self.config_mgr = ConfigMgr(self.site_name, PREFIX)
        panel_path = "/www/server/panel"
        if os.path.exists("{}/data/ng_log_format.json".format(panel_path)):
            os.remove("{}/data/ng_log_format.json".format(panel_path))

        if os.path.exists("{}/vhost/nginx/log_format".format(panel_path)):
            shutil.rmtree("{}/vhost/nginx/log_format".format(panel_path))

        if os.path.exists("{}/data/ap_log_format.json".format(panel_path)):
            os.remove("{}/data/ap_log_format.json".format(panel_path))

        if os.path.exists("{}/vhost/apache/log_format".format(panel_path)):
            shutil.rmtree("{}/vhost/apache/log_format".format(panel_path))

    def runTest(self):
        # self.change_env_to_nginx()
        # self.test_log_format_mager()
        # print("==================================")
        # self.test_set_site_log_format()
        # self.check_web_server_config()

        # self.change_env_to_apache()
        # self.test_log_format_mager()
        # print("==================================")
        # self.test_set_site_log_format()
        # self.check_web_server_config()

        # self.change_env_to_nginx()
        # self.log_mgr = LogMgr(PREFIX)
        # self.test_site_log_path()
        # self.check_web_server_config()

        # self.change_env_to_apache()
        # self.log_mgr = LogMgr(PREFIX)
        # self.test_site_log_path()
        # self.check_web_server_config()

        self.test_site_crontab_log()

    def tearDown(self):
        pass
        self.reset_site_config()


if __name__ == '__main__':
    import unittest

    s = unittest.TestSuite()
    s.addTest(TestRealLogMgr())
    unittest.TextTestRunner().run(s)
