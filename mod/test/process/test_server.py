import unittest
import sys
import time

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")
if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
from mod.base import RealServer

realserver = RealServer()


class TestRealServer(unittest.TestCase):
    def test_server_admin(self):
        res = realserver.server_admin('httpd', 'stop')
        self.assertEqual(res['code'], 1)
        res = realserver.server_admin('httpd', 'start')
        self.assertEqual(res['code'], 1)

    def test_server_status(self):
        res = realserver.server_status('httpd')
        self.assertEqual(res['code'], 1)

    def test_add_boot(self):
        server_name = 'swwnb'
        pidfile = '/tmp/test.pl'
        start_exec = 'btpython /root/1.py'
        stop_exec = 'kill <cat /tmp/test.pl'
        res = realserver.add_boot(server_name, pidfile, start_exec, stop_exec)
        self.assertEqual(res['code'], 1)

    def test_universal_server_admin(self):
        res = realserver.universal_server_admin('swwnb', 'stop')
        self.assertEqual(res['code'], 1)
        res = realserver.universal_server_admin('swwnb', 'start')
        self.assertEqual(res['code'], 1)

    def test_universal_server_status(self):
        res = realserver.universal_server_status('swwnb')
        self.assertEqual(res['code'], 1)

    def test_create_daemon(self):
        server_name = 'swwnb'
        pidfile = '/tmp/test.pl'
        start_exec = 'btpython /root/1.py'
        workingdirectory = '/tmp'
        res = realserver.create_daemon(server_name, pidfile, start_exec, workingdirectory)
        self.assertEqual(res['code'], 1)

    def test_daemon_status(self):
        res = realserver.daemon_status('swwnb')
        self.assertEqual(res['code'], 1)

    def test_del_daemon(self):
        res = realserver.del_daemon('swwnb')
        self.assertEqual(res['code'], 1)

    # def test_del_boot(self):
    #     res = realserver.del_boot('swwnb')
    #     self.assertEqual(res['code'], 1)

    def test_add_task(self):
        res = realserver.add_task('echo 1 > /time/111.log', int(time.time()) + 3000)
        self.assertEqual(res['code'], 1)


if __name__ == '__main__':
    unittest.main()
