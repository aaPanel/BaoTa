import os
import sys

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

from mod.test.test_web_conf import WebBaseTestcase, PREFIX, SITE_PATH, SUB_SITE_PATH
from mod.base.web_conf import normalize_domain, NginxDomainTool, ApacheDomainTool, ConfigMgr, set_default_site
from mod.base.web_conf.util import DB, write_file, read_file


class DomainToolTest(WebBaseTestcase):

    def test_normalize_domain(self):
        res, err = normalize_domain("www.example.com", "www.example.com:2546545", "www.example.com:4545")
        self.assertCountEqual(res, [("www.example.com", "80"), ("www.example.com", "4545")])
        print(err)

    def test_nginx_domain_tool(self):
        ngd_tool = NginxDomainTool(PREFIX)
        # 检查default_site 与 域名设置
        set_default_site(self.site_name)
        res, _ = normalize_domain("www.example.com", "www.example.com:2546545", "www.example.com:4545")
        res = ngd_tool.nginx_set_domain(self.site_name, (self.site_name, "80"), *res)
        self.assertEqual(res, None, "设置域名出错")

        conf_mager = ConfigMgr(self.site_name, PREFIX)
        conf = conf_mager.nginx_config()
        self.assertIn("www.example.com", conf)
        self.assertIn("4545", conf)
        print(conf)

    def test_apache_domain_tool(self):
        ngd_tool = ApacheDomainTool(PREFIX)

        res, _ = normalize_domain("www.example.com", "www.example.com:2546545", "www.example.com:4545")
        res = ngd_tool.apache_set_domain(self.site_name, (self.site_name, "80"), *res)
        self.assertEqual(res, None, "设置域名出错")

        conf_mager = ConfigMgr(self.site_name, PREFIX)
        conf = conf_mager.apache_config()
        self.assertIn("www.example.com", conf)
        self.assertIn("4545", conf)
        print(conf)

    def setUp(self) -> None:
        self.reset_site_config()

    def runTest(self):
        self.test_normalize_domain()

        # self.change_env_to_nginx()
        # self.test_nginx_domain_tool()
        # self.check_web_server_config()

        self.change_env_to_apache()
        self.test_apache_domain_tool()
        self.check_web_server_config()

    def tearDown(self):
        self.reset_site_config()


if __name__ == '__main__':
    import unittest
    s = unittest.TestSuite()
    s.addTest(DomainToolTest())
    unittest.TextTestRunner().run(s)
