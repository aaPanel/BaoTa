
import os
import shutil
import sys

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

from mod.test.test_web_conf import WebBaseTestcase, PREFIX, NGINX_CONFIG_CASE, APACHE_CONFIG_CASE
from mod.base.web_conf import ConfigMgr, Proxy
from mod.base.web_conf.util import GET_CLASS


class TestProxy(WebBaseTestcase):
    proxy_obj = Proxy(PREFIX)

    def test_create_project_proxy(self):
        get = GET_CLASS()
        get.proxyname = "aaa"
        get.sitename = self.site_name
        get.proxydir = "/"
        get.proxysite = "https://www.baidu.com"
        get.todomain = "www.baidu.com"
        get.type = "1"
        get.cache = "1"
        get.subfilter = '[{"sub1":"","sub2":""},{"sub1":"","sub2":""},{"sub1":"","sub2":""}]'
        get.advanced = "1"
        get.cachetime = "1"
        print(self.proxy_obj.create_proxy(get))

        # get = GET_CLASS()
        # get.proxyname = "ggfff"
        # get.sitename = self.site_name
        # get.proxydir = "/dad"
        # get.proxysite = "https://www.baidu.com"
        # get.todomain = "www.baidu.com"
        # get.type = "1"
        # get.cache = "1"
        # get.subfilter = '[{"sub1":"","sub2":""},{"sub1":"","sub2":""},{"sub1":"","sub2":""}]'
        # get.advanced = "1"
        # get.cachetime = "1"
        # print(self.proxy_obj.create_proxy(get))

    def test_modify_project_proxy(self):
        get = GET_CLASS()
        get.proxyname = "ggfff"
        get.sitename = self.site_name
        get.proxydir = "/dygvccc"
        get.proxysite = "https://www.baidu.com"
        get.todomain = "www.baidu.com"
        get.type = "1"
        get.cache = "1"
        get.subfilter = '[{"sub1":"","sub2":""},{"sub1":"","sub2":""},{"sub1":"","sub2":""}]'
        get.advanced = "0"
        get.cachetime = "1"
        print(self.proxy_obj.modify_proxy(get))

    def test_remove_project_proxy(self):
        get = GET_CLASS()
        get.proxyname = "aaa"
        get.sitename = self.site_name
        print(self.proxy_obj.remove_proxy(get))

    def test_get_project_proxy_list(self):
        get = GET_CLASS()
        get.sitename = self.site_name
        print(self.proxy_obj.get_proxy_list(get))

    def setUp(self) -> None:
        self.reset_site_config()
        self.config_mgr = ConfigMgr(self.site_name, PREFIX)
        panel_path = "/www/server/panel"
        _proxy_conf_file = "{}/data/mod_proxy_file.conf".format(panel_path)
        if os.path.exists(_proxy_conf_file):
            os.remove(_proxy_conf_file)

        ng_proxy_dir = "/www/server/panel/vhost/nginx/proxy/" + self.site_name
        ap_proxy_dir = "/www/server/panel/vhost/apache/proxy/" + self.site_name
        if os.path.exists(ng_proxy_dir):
            shutil.rmtree(ng_proxy_dir)

        if os.path.exists(ap_proxy_dir):
            shutil.rmtree(ap_proxy_dir)

    def runTest(self):
        # self.change_env_to_nginx()
        # self.test_create_project_proxy()
        # self.test_remove_project_proxy()
        # self.check_web_server_config()

        self.change_env_to_apache()
        self.test_create_project_proxy()
        self.test_remove_project_proxy()
        self.test_modify_project_proxy()
        self.test_get_project_proxy_list()
        self.check_web_server_config()

    # def tearDown(self):
    #     self.reset_site_config()


if __name__ == '__main__':
    import unittest

    s = unittest.TestSuite()
    s.addTest(TestProxy())
    unittest.TextTestRunner().run(s)
