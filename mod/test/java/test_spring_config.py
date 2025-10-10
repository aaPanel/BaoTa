import json
import os
import time
import unittest

import sys
if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

from mod.project.java.springboot_parser import SpringConfigParser, SpringLogConfigParser


class TestSpringConfigParser(unittest.TestCase):

    # def test_parser_config(self):
    #     file = "/www/java_mall/yami-shop-admin-0.0.1-SNAPSHOT.jar"
    #     # file = "/www/lilishop/lili-shop-error_jar.jar"
    #     # file = "/www/wwwroot/111_java/demo.jar"
    #     # file = "/www/wwwroot/33_java/tduck-api.jar"
    #     # file = "/www/java_mall/yami-shop-api-0.0.1-SNAPSHOT.jar"
    #
    #     scp = SpringConfigParser(file)
    #     print(scp.get_tip())
    #
    # def test_shell_env(self):
    #     SpringConfigParser.get_env_file_data("/www/wwwroot/33_java/test.sh")

    def test_parser_log_config(self):
        # file = "/www/java_mall/yami-shop-admin-0.0.1-SNAPSHOT.jar"
        # file = "/www/lilishop/run_api/buyer-api-4.3.jar"
        # file = "/www/wwwroot/111_java/demo.jar"
        # file = "/www/wwwroot/33_java/tduck-api.jar"
        file = "/www/wwwroot/55_MCMS_java/ms-mcms.jar"
        # file = "/www/java_mall/yami-shop-api-0.0.1-SNAPSHOT.jar"

        if not os.path.exists(file):
            print("文件不存在")
        scp = SpringLogConfigParser(file)
        print(scp.get_all_log_ptah())


if __name__ == '__main__':
    unittest.main()
