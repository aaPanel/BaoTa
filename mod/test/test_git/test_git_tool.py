import json
import os
import sys
import time
from unittest import TestCase

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

from mod.base.git_tool import GitTool, GitMager
from mod.base.web_conf.util import GET_CLASS


class TestGitTool(TestCase):
    def runTest(self):
        # g = GitTool(
        #     project_path="/www/test/git_test",
        #     git_url="http://git.bt.cn/baozi/bt_sync.git",
        #     user_config={
        #         "name": "baozi",
        #         "password": "swt258452.",
        #         "email": "1191604998@qq.com",
        #     }
        # )
        # g.pull("master")
        os.remove("/www/server/panel/data/site_git_config.json")

        get = GET_CLASS()
        get.git_path = "/www/test/git_test"
        get.site_name = "git_test"
        get.url = "http://git.bt.cn/baozi/bt_sync.git"
        get.config = json.dumps({
                "name": "baozi",
                "password": "swt258452.",
                "email": "1191604998@qq.com",
            })

        gm = GitMager()
        print(gm.add_git(get))

        get = GET_CLASS()
        get.site_name = "git_test"
        get.refresh = "1"
        print(gm.site_git_configure(get))

        # get = GET_CLASS()
        # get.git_path = "/www/test/git_test1"
        # get.site_name = "git_test"
        # get.git_id = "git_test"
        # print(gm.modify_git(get))
        #
        # gm.git_pull("master")


if __name__ == '__main__':
    import unittest
    s = unittest.TestSuite()
    s.addTest(TestGitTool())
    unittest.TextTestRunner().run(s)
