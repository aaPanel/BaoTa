import os.path
import sys
if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

from mod.test.test_web_conf import WebBaseTestcase, PREFIX, NGINX_CONFIG_CASE, APACHE_CONFIG_CASE
from mod.base.web_conf.util import GET_CLASS, service_reload
from mod.base.web_conf import IpRestrict, ConfigMgr


class TestIpRestrict(WebBaseTestcase):
    ip_restrict = IpRestrict(PREFIX)

    def setUp(self) -> None:
        self.reset_site_config()
        setup_path = "/www/server/panel"
        ip_restrict_conf = "{}/data/ip_restrict_data/{}{}".format(setup_path, PREFIX, self.site_name)
        if os.path.exists(ip_restrict_conf):
            os.remove(ip_restrict_conf)
        nginx_ip_restrict_conf = "{}/vhost/ip-restrict/{}{}.conf".format(setup_path, PREFIX, self.site_name)
        if os.path.exists(nginx_ip_restrict_conf):
            os.remove(nginx_ip_restrict_conf)

    def test_black_ip_restrict(self):
        # 设置为黑名单格式
        get = GET_CLASS()
        get.site_name = self.site_name
        # black white closed
        get.set_type = "black"
        self.ip_restrict.set_ip_restrict(get)

        # 添加黑名单信息
        get = GET_CLASS()
        get.site_name = self.site_name
        get.value = "192.168.168.65"
        self.ip_restrict.add_black_ip_restrict(get)

        config_mgr = ConfigMgr(self.site_name, PREFIX)
        self.assertIn("ip-restrict", config_mgr.nginx_config())
        setup_path = "/www/server/panel"
        ip_restrict_conf = "{}/data/ip_restrict_data/{}{}".format(setup_path, PREFIX, self.site_name)
        nginx_ip_restrict_conf = "{}/vhost/ip-restrict/{}{}.conf".format(setup_path, PREFIX, self.site_name)

        self.assertTrue(os.path.exists(ip_restrict_conf))
        self.assertTrue(os.path.exists(nginx_ip_restrict_conf))

        # 移除黑名单信息
        # get = GET_CLASS()
        # get.site_name = self.site_name
        # get.value = "192.168.168.65"
        # self.ip_restrict.remove_black_ip_restrict(get)

    def test_white_ip_restrict(self):
        # 设置为白名单格式
        get = GET_CLASS()
        get.site_name = self.site_name
        # black white closed
        get.set_type = "white"
        self.ip_restrict.set_ip_restrict(get)

        # 添加白名单信息
        get = GET_CLASS()
        get.site_name = self.site_name
        get.value = "192.168.168.65"  # "192.168.168.66"
        self.ip_restrict.add_white_ip_restrict(get)

        config_mgr = ConfigMgr(self.site_name, PREFIX)
        self.assertIn("ip-restrict", config_mgr.nginx_config())
        setup_path = "/www/server/panel"
        ip_restrict_conf = "{}/data/ip_restrict_data/{}{}".format(setup_path, PREFIX, self.site_name)
        nginx_ip_restrict_conf = "{}/vhost/ip-restrict/{}{}.conf".format(setup_path, PREFIX, self.site_name)

        self.assertTrue(os.path.exists(ip_restrict_conf))
        self.assertTrue(os.path.exists(nginx_ip_restrict_conf))

        # 移除白名单信息
        get = GET_CLASS()
        get.site_name = self.site_name
        get.value = "192.168.168.65"
        self.ip_restrict.remove_white_ip_restrict(get)

    def test_ip_restrict_conf(self):
        # 添加黑名单信息
        get = GET_CLASS()
        get.site_name = self.site_name
        get.value = "192.168.168.65"
        self.ip_restrict.add_black_ip_restrict(get)

        # 设置为白单格式
        get = GET_CLASS()
        get.site_name = self.site_name
        # black white closed
        get.set_type = "white"
        self.ip_restrict.set_ip_restrict(get)
        # 添加白名单信息
        get = GET_CLASS()
        get.site_name = self.site_name
        get.value = "192.168.168.65"  # "192.168.168.66"
        self.ip_restrict.add_white_ip_restrict(get)

        get = GET_CLASS()
        get.site_name = self.site_name
        print(self.ip_restrict.restrict_conf(get))

    def runTest(self):
        # self.change_env_to_nginx()
        # self.test_black_ip_restrict()
        # self.check_web_server_config()

        # self.change_env_to_nginx()
        # self.test_white_ip_restrict()
        # self.check_web_server_config()

        self.change_env_to_nginx()
        self.test_ip_restrict_conf()
        self.check_web_server_config()


if __name__ == '__main__':
    import unittest
    s = unittest.TestSuite()
    s.addTest(TestIpRestrict())
    unittest.TextTestRunner().run(s)
