import time
import unittest

import sys
if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

from mod.project.java.projectMod import main as springboot_main
from mod.base.web_conf.util import GET_CLASS
from mod.project.java import utils


class TestSpringBootConfig(unittest.TestCase):

    def setUp(self) -> None:
        self.springboot = springboot_main()

    # def test_process_for_create(self):
    #     get = GET_CLASS()
    #     get.is_java_process = ''
    #     get.search = 'ja'
    #     data = self.springboot.process_for_create(get)
    #     print(data)
    #
    # def test_process_info_for_create(self):
    #     get = GET_CLASS()
    #     get.pid = "15701"
    #     data = self.springboot.process_info_for_create(get)
    #     print(data)

    # def test_create_port(self):
    #     t = time.time()
    #     print(t)
    #     print(utils.create_a_not_used_port())
    #     print(time.time() - t)

    def test_get_jar_war_config(self):
        file = "/www/wwwroot/33_java/tduck-api.jar"
        data = utils.get_jar_war_config(file)
        if data:
            data = utils.to_utf8(data)
        print(data)


if __name__ == '__main__':
    unittest.main()
