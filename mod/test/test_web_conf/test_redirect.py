import json
import os
import shutil
import sys

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

from mod.test.test_web_conf import WebBaseTestcase, PREFIX, NGINX_CONFIG_CASE, APACHE_CONFIG_CASE
from mod.base.web_conf import ConfigMgr, Redirect
from mod.base.web_conf.util import GET_CLASS


class TestRedirect(WebBaseTestcase):
    redirect = Redirect()

    def test_create_project_redirect(self):
        get = GET_CLASS()
        get.sitename = self.site_name
        get.redirectpath = "/"
        get.redirecttype = "301"
        get.domainorpath = "path"
        get.redirectname = "aaa"
        get.tourl = ""
        get.topath = "/ashdjadg"
        get.redirectdomain = "[]"
        get.type = "1"
        get.errorpage = "0"
        get.holdpath = "1"
        print(self.redirect.create_project_redirect(get))

    def test_modify_project_redirect(self):
        get = GET_CLASS()
        get.sitename = self.site_name
        get.redirectpath = "/"
        get.redirecttype = "301"
        get.domainorpath = "domain"
        get.redirectname = "aaa"
        get.tourl = "https://www.baidu.com"
        get.topath = ""
        get.redirectdomain = json.dumps([self.site_name])
        get.type = "1"
        get.errorpage = "0"
        get.holdpath = "1"
        print(self.redirect.modify_project_redirect(get))

    def test_remove_project_redirect(self):
        get = GET_CLASS()
        get.sitename = self.site_name
        get.redirectname = "aaa"
        print(self.redirect.remove_project_redirect(get))

    def test_get_project_redirect_list(self):
        get = GET_CLASS()
        get.sitename = self.site_name
        print(self.redirect.get_project_redirect_list(get))

    def setUp(self) -> None:
        self.reset_site_config()
        self.config_mgr = ConfigMgr(self.site_name, PREFIX)

    def runTest(self):
        # self.change_env_to_nginx()
        # self.test_create_project_redirect()
        # self.test_modify_project_redirect()
        # self.test_get_project_redirect_list()
        # self.test_remove_project_redirect()
        # self.check_web_server_config()
        #
        self.change_env_to_apache()
        self.test_create_project_redirect()
        self.test_modify_project_redirect()
        self.test_get_project_redirect_list()
        self.test_remove_project_redirect()
        self.check_web_server_config()

    # def tearDown(self):
    #     pass
    #     self.reset_site_config()


if __name__ == '__main__':
    import unittest

    s = unittest.TestSuite()
    s.addTest(TestRedirect())
    unittest.TextTestRunner().run(s)
