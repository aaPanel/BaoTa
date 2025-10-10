import os
import sys

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

from mod.test.test_web_conf import WebBaseTestcase, PREFIX, SITE_PATH, SUB_SITE_PATH
from mod.base.web_conf import DirTool
from mod.base.web_conf.util import DB, write_file


class TestDirTool(WebBaseTestcase):
    dir_tool = DirTool(PREFIX)

    def reset_site_config(self) -> None:
        super(TestDirTool, self).reset_site_config()

        if "/www/server/panel/class" not in sys.path:
            sys.path.insert(0, "/www/server/panel/class")
        import public

        if os.path.exists(SUB_SITE_PATH + "/.user.ini"):
            public.ExecShell("chattr -i " + SUB_SITE_PATH + "/.user.ini")
            os.remove(SUB_SITE_PATH + "/.user.ini")

        if not os.path.exists(SITE_PATH + "/.user.ini"):
            write_file(SITE_PATH + "/.user.ini", "open_basedir=/www/wwwroot/aaa.test.com/:/tmp/")

        site_info = DB("sites").where("name=?", (self.site_name,)).find()
        DB("sites").where("id=?", (site_info["id"],)).setField('path', SITE_PATH)

    def test_modify_site_path(self):
        res = self.dir_tool.modify_site_path(self.site_name, SITE_PATH, SUB_SITE_PATH)
        self.assertIsNone(res, "修改路径失败")
        self.assertTrue(os.path.exists(SUB_SITE_PATH + "/.user.ini"), ".user.ini错误")
        self.assertEqual(DB("sites").where("name=?", (self.site_name,)).find()["path"], SUB_SITE_PATH, "数据库错误")
        self.reset_site_config()

    def test_modify_site_run_path(self):
        self.dir_tool.modify_site_run_path(self.site_name, SITE_PATH, "/test_run")
        self.assertEqual(self.dir_tool.get_site_run_path(self.site_name), SUB_SITE_PATH, "修改运行目录失败")
        self.assertTrue(os.path.exists(SUB_SITE_PATH + "/.user.ini"), ".user.ini错误")
        self.reset_site_config()

    def test_index_conf(self):
        self.assertCountEqual(self.dir_tool.get_index_conf(self.site_name),
                              ["index.php", "index.html", "index.htm", "default.php", "default.html", "default.htm"],
                              "获取index信息错误")
        self.dir_tool.set_index_conf(self.site_name, "index.php", "default.php", "default.html", "default.htm")
        self.assertCountEqual(self.dir_tool.get_index_conf(self.site_name),
                              ["index.php", "default.php", "default.html", "default.htm"],
                              "设置index信息错误")

        self.reset_site_config()

    def setUp(self) -> None:
        self.reset_site_config()

    def runTest(self):
        # 测试改变path
        # self.change_env_to_nginx()
        # self.test_modify_site_path()
        # self.check_web_server_config()
        #
        # self.change_env_to_apache()
        # self.test_modify_site_path()
        # self.check_web_server_config()

        # 测试改变run_path
        # self.change_env_to_nginx()
        # self.test_modify_site_run_path()
        # self.check_web_server_config()
        #
        # self.change_env_to_apache()
        # self.test_modify_site_run_path()
        # self.check_web_server_config()

        self.change_env_to_nginx()
        self.test_index_conf()
        self.check_web_server_config()

        self.change_env_to_apache()
        self.test_index_conf()
        self.check_web_server_config()

    def tearDown(self):
        self.reset_site_config()


if __name__ == '__main__':
    import unittest

    s = unittest.TestSuite()
    s.addTest(TestDirTool())
    unittest.TextTestRunner().run(s)
