import os.path
import sys
if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

from mod.test.test_web_conf import WebBaseTestcase, PREFIX
from mod.base.web_conf import AccessRestriction
from mod.base.web_conf.util import GET_CLASS


class TestAccessRestriction(WebBaseTestcase):
    as_obj = AccessRestriction(PREFIX)

    def test_create_auth_dir(self):
        get = GET_CLASS()
        get.site_name = self.site_name
        get.name = "fshfd"
        get.dir_path = "/"
        get.password = "ssss"
        get.username = "aaaa"
        res = self.as_obj.create_auth_dir(get)
        self.assertTrue(res["status"], res["msg"])

    def test_modify_auth_dir(self):
        get = GET_CLASS()
        get.site_name = self.site_name
        get.name = "fshfd"
        get.dir_path = "/"
        get.password = "ssss"
        get.username = "aarrr"
        res = self.as_obj.modify_auth_dir(get)
        self.assertTrue(res["status"], res["msg"])

    def test_remove_auth_dir(self):
        get = GET_CLASS()
        get.site_name = self.site_name
        get.name = "fshfd"
        res = self.as_obj.remove_auth_dir(get)
        self.assertTrue(res["status"], res["msg"])

    def test_create_file_deny(self):
        get = GET_CLASS()
        get.site_name = self.site_name
        get.name = "fshfd"
        get.dir_path = "/"
        get.suffix = "[\"txt\"]"
        res = self.as_obj.create_file_deny(get)
        self.assertTrue(res["status"], res["msg"])

    def test_modify_file_deny(self):
        get = GET_CLASS()
        get.site_name = self.site_name
        get.name = "fshfd"
        get.dir_path = "/"
        get.suffix = "[\"ffff\"]"
        res = self.as_obj.modify_file_deny(get)
        self.assertTrue(res["status"], res["msg"])

    def test_remove_file_deny(self):
        get = GET_CLASS()
        get.site_name = self.site_name
        get.name = "fshfd"
        res = self.as_obj.remove_file_deny(get)
        self.assertTrue(res["status"], res["msg"])

    def test_site_access_restriction_info(self):
        get = GET_CLASS()
        get.site_name = self.site_name
        res = self.as_obj.site_access_restriction_info(get)
        self.assertTrue(res["status"], res["msg"])
        print(res["data"])

    def setUp(self) -> None:
        if os.path.exists("/www/server/panel/data/site_access.json"):
            os.remove("/www/server/panel/data/site_access.json")
        self.reset_site_config()

    def runTest(self):
        # self.change_env_to_apache()

        self.change_env_to_nginx()
        self.test_create_auth_dir()
        self.check_web_server_config()
        self.test_create_file_deny()
        self.check_web_server_config()
        self.test_modify_file_deny()
        self.check_web_server_config()
        self.test_modify_auth_dir()
        self.check_web_server_config()
        self.test_site_access_restriction_info()
        self.test_remove_auth_dir()
        self.test_remove_file_deny()
        self.check_web_server_config()

        self.change_env_to_apache()
        self.test_create_auth_dir()
        self.check_web_server_config()
        self.test_create_file_deny()
        self.check_web_server_config()
        self.test_modify_file_deny()
        self.check_web_server_config()
        self.test_modify_auth_dir()
        self.check_web_server_config()
        self.test_site_access_restriction_info()
        self.test_remove_auth_dir()
        self.test_remove_file_deny()
        self.check_web_server_config()

    def tearDown(self):
        if os.path.exists("/www/server/panel/data/site_access.json"):
            os.remove("/www/server/panel/data/site_access.json")
        self.reset_site_config()


if __name__ == '__main__':
    import unittest
    s = unittest.TestSuite()
    s.addTest(TestAccessRestriction())
    unittest.TextTestRunner().run(s)
