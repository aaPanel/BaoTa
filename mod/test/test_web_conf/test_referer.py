import json
import os
import shutil
import sys

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

from mod.test.test_web_conf import WebBaseTestcase, PREFIX, NGINX_CONFIG_CASE, APACHE_CONFIG_CASE
from mod.base.web_conf import ConfigMgr, Referer
from mod.base.web_conf.util import GET_CLASS


class TestReferer(WebBaseTestcase):
    referer = Referer(PREFIX)

    def test_referer_security(self):
        # 开启
        get = GET_CLASS()
        get.status = "true"
        get.http_status = "false"
        get.name = self.site_name
        get.fix = "fsf,dhjdh,uooo"
        get.domains = self.site_name + ",www.asdad.com"
        get.return_rule = "403"
        print(self.referer.set_referer_security(get))

        # 修改
        get = GET_CLASS()
        get.status = "true"
        get.http_status = "false"
        get.name = self.site_name
        get.fix = "fsf,dhjdh,hjhlh"
        get.domains = self.site_name + ",www.asdad.com"
        get.return_rule = "404"
        print(self.referer.set_referer_security(get))

        # 删除
        get = GET_CLASS()
        get.status = "false"
        get.http_status = "false"
        get.name = self.site_name
        get.fix = "fsf,dhjdh,hjhlh"
        get.domains = self.site_name + ",www.asdad.com"
        get.return_rule = "404"
        print(self.referer.set_referer_security(get))

        get = GET_CLASS()
        get.site_name = self.site_name
        print(self.referer.get_referer_security(get))

    def setUp(self) -> None:
        self.reset_site_config()
        self.config_mgr = ConfigMgr(self.site_name, PREFIX)

    def runTest(self):
        self.change_env_to_nginx()
        self.test_referer_security()
        self.check_web_server_config()

    # def tearDown(self):
    #     pass
    #     self.reset_site_config()


if __name__ == '__main__':
    import unittest
    s = unittest.TestSuite()
    s.addTest(TestReferer())
    unittest.TextTestRunner().run(s)
