import os
import sys
import time
from unittest import TestCase

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")


from mod.base.backup_tool import BackupTool, DB


class TestBackupTool(TestCase):

    def test_backup(self):
        src = "/www/wwwroot/aaa.test.com"
        sub_dir = "site/aaa.test.com"

        site_info = DB("sites").where("name= ?", ("aaa.test.com", )).find()
        print(site_info)
        print(BackupTool().backup(src, sub_dir=sub_dir, sync=False, site_info=site_info))
        time.sleep(2)  # 等待执行完成
        # print(BackupTool().backup(src, sub_dir=sub_dir, sync=True, site_info=site_info))

        print(os.listdir(BackupTool().backup_path + "/" + sub_dir))

    def runTest(self):
        self.test_backup()


if __name__ == '__main__':
    import unittest
    s = unittest.TestSuite()
    s.addTest(TestBackupTool())
    unittest.TextTestRunner().run(s)
