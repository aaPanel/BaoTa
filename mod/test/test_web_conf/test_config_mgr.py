
import sys
if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

from mod.test.test_web_conf import WebBaseTestcase, PREFIX, NGINX_CONFIG_CASE, APACHE_CONFIG_CASE
from mod.base.web_conf import ConfigMgr


class TestConfigMgr(WebBaseTestcase):

    def test_nginx_config(self):
        self.assertEqual(self.config_mgr.nginx_config(), NGINX_CONFIG_CASE, "nginx 配置文件读取错误")

    def test_apache_config(self):
        self.assertEqual(self.config_mgr.apache_config(), APACHE_CONFIG_CASE, "apache 配置文件读取错误")

    def test_save_nginx_config(self):
        self.config_mgr.save_nginx_config(NGINX_CONFIG_CASE + "\n\n")
        self.assertEqual(self.config_mgr.nginx_config(), NGINX_CONFIG_CASE + "\n\n", "nginx 配置文件保存错误")

        self.assertIsInstance(self.config_mgr.save_nginx_config("hshdgajdgg"), str, "nginx 配置文件保存错误")

    def test_save_apache_config(self):
        self.config_mgr.save_apache_config(APACHE_CONFIG_CASE + "\n\n")
        self.assertEqual(self.config_mgr.apache_config(), APACHE_CONFIG_CASE + "\n\n", "apache 配置文件保存错误")

        self.assertIsInstance(self.config_mgr.save_apache_config("hshdgajdgg"), str, "apache 配置文件保存错误")

    def test_history_list(self):
        print(self.config_mgr.history_list())

    def test_history_conf(self):
        res = self.config_mgr.history_list()
        if len(res["nginx"]) > 0:
            print(self.config_mgr.history_conf(res["nginx"][0]))

        if len(res["apache"]) > 0:
            print(self.config_mgr.history_conf(res["apache"][0]))

    def setUp(self) -> None:
        self.reset_site_config()
        self.config_mgr = ConfigMgr(self.site_name, PREFIX)

    def runTest(self):
        self.change_env_to_nginx()
        self.test_nginx_config()
        self.test_save_nginx_config()
        self.test_history_list()
        self.test_history_conf()
        self.check_web_server_config()

        self.change_env_to_apache()
        self.test_apache_config()
        self.test_save_apache_config()
        self.test_history_list()
        self.test_history_conf()
        self.check_web_server_config()

    def tearDown(self):
        self.reset_site_config()


if __name__ == '__main__':
    import unittest
    s = unittest.TestSuite()
    s.addTest(TestConfigMgr())
    unittest.TextTestRunner().run(s)
