import os
import sys
if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

from mod.test.test_web_conf import WebBaseTestcase, PREFIX
from mod.base.web_conf import get_default_site, set_default_site, check_default


class TestDefaultSite(WebBaseTestcase):
    def test_check_default(self):
        vhost_path = "/www/server/panel/vhost"
        nginx = vhost_path + '/nginx'
        httpd = vhost_path + '/apache'
        check_default()
        self.assertTrue(os.path.exists(httpd + '/0.default.conf'))
        self.assertTrue(os.path.exists(nginx + '/0.default.conf'))

    def test_get_default_site(self):
        self.assertEqual(get_default_site(), (self.site_name, PREFIX), "设置默认站点错误")

    def test_set_default_site(self):
        set_default_site(site_name=self.site_name, prefix=PREFIX, domain=self.site_name)

    def setUp(self) -> None:
        self.reset_site_config()
        vhost_path = "/www/server/panel/vhost"
        nginx = vhost_path + '/nginx'
        httpd = vhost_path + '/apache'

        if os.path.exists(httpd + '/0.default.conf'):
            os.remove(httpd + '/0.default.conf')
        if os.path.exists(httpd + '/default.conf'):
            os.remove(httpd + '/default.conf')

        if os.path.exists(nginx + '/0.default.conf'):
            os.remove(nginx + '/0.default.conf')
        if os.path.exists(nginx + '/default.conf'):
            os.remove(nginx + '/default.conf')

        panel_path = "/www/server/panel"
        new_ds_file = panel_path + "/data/mod_default_site.pl"
        if os.path.exists(new_ds_file):
            os.remove(new_ds_file)

    def runTest(self):
        self.test_check_default()
        self.test_set_default_site()
        self.test_get_default_site()

        self.change_env_to_nginx()
        self.check_web_server_config()

        self.change_env_to_apache()
        self.check_web_server_config()

    def tearDown(self):
        self.reset_site_config()
        set_default_site(None)


if __name__ == '__main__':
    import unittest
    s = unittest.TestSuite()
    s.addTest(TestDefaultSite())
    unittest.TextTestRunner().run(s)
