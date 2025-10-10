import os
import shutil
import sys
import time
from unittest import TestCase

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")


from mod.base.backup_tool import VersionTool


class TestVersionTool(TestCase):

    def test_backup(self):
        src = "/www/wwwroot/aaa.test.com"
        v = VersionTool()
        print(v.publish("aaa", src, "1.0.0", sync=False))
        print(v.version_list("aaa"))
        time.sleep(2)  # 等待执行完成
        # print(BackupTool().backup(src, sub_dir=sub_dir, sync=True, site_info=site_info))
        v.recover('aaa', '1.0.0', src)

    def runTest(self):
        self.test_backup()


if __name__ == '__main__':
    import unittest
    s = unittest.TestSuite()
    s.addTest(TestVersionTool())
    unittest.TextTestRunner().run(s)
