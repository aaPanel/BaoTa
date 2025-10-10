import json
import os
import shutil
import sys

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

from mod.test.test_web_conf import WebBaseTestcase, PREFIX, NGINX_CONFIG_CASE, APACHE_CONFIG_CASE
from mod.base.web_conf import SSLManager, set_default_site
from mod.base.web_conf.util import GET_CLASS


class TestSSLManager(WebBaseTestcase):
    ssl = SSLManager(PREFIX)

    def test_set_site_ssl_conf(self):
        # 开启
        get = GET_CLASS()
        get.ssl_id = "2"  # 保证这个ID存在
        get.site_name = self.site_name
        print(self.ssl.set_site_ssl_conf(get))

    def test_mutil_set_site_ssl_conf(self):
        # 开启
        get = GET_CLASS()
        get.ssl_id = "9"  # 保证这个ID存在
        get.site_names = json.dumps([self.site_name, "www.123test.com"])
        print(self.ssl.mutil_set_site_ssl_conf(get))

    def test_close_site_ssl_conf(self):
        # 关闭
        get = GET_CLASS()
        get.site_name = self.site_name
        print(self.ssl.close_site_ssl_conf(get))

    def setUp(self) -> None:
        self.reset_site_config()

    def runTest(self):
        set_default_site(site_name=self.site_name)
        self.change_env_to_nginx()
        self.test_set_site_ssl_conf()
        self.test_mutil_set_site_ssl_conf()
        self.test_close_site_ssl_conf()
        self.check_web_server_config()

        # self.change_env_to_apache()
        # self.test_set_site_ssl_conf()
        # self.test_mutil_set_site_ssl_conf()
        # self.test_close_site_ssl_conf()
        # self.check_web_server_config()

    # def tearDown(self):
    #     pass
    #     self.reset_site_config()


if __name__ == '__main__':
    import unittest
    s = unittest.TestSuite()
    s.addTest(TestSSLManager())
    unittest.TextTestRunner().run(s)
