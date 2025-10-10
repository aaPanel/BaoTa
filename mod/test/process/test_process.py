import unittest
import sys

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")
from mod.base import RealProcess

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
import public

real_process = RealProcess()


class TestRealProcess(unittest.TestCase):

    def test_get_process_list(self):
        res = real_process.get_process_list()
        self.assertEqual(res['code'], 1)

    def test_get_process_info_by_pid(self):
        res = real_process.get_process_info_by_pid(1)
        self.assertEqual(res['code'], 1)

    def test_get_process_info_by_name(self):
        res = real_process.get_process_info_by_name('system')
        self.assertEqual(res['code'], 1)

    def test_get_process_info_by_exec(self):
        res = real_process.get_process_info_by_exec('/usr/sbin/sshd')
        self.assertEqual(res['code'], 1)

    def test_get_process_info_by_port(self):
        res = real_process.get_process_info_by_port(22)
        self.assertEqual(res['code'], 1)

    def test_get_process_info_by_ip(self):
        res = real_process.get_process_info_by_ip('192.168.168.66')
        self.assertEqual(res['code'], 1)

    def test_get_process_info_by_openfile(self):
        res = real_process.get_process_info_by_openfile('/etc/passwd')
        self.assertEqual(res['code'], 1)

    def test_get_process_ps(self):
        res = real_process.get_process_ps('grep')
        self.assertEqual(res['code'], 1)

    def test_get_process_tree(self):
        res = real_process.get_process_tree(1)
        self.assertEqual(res['code'], 1)

    # def test_kill_pid(self):
    #     try:
    #         pid = real_process.get_process_info_by_exec('/www/server/panel/mod/test/process/test.py')['data'][0]['pid']
    #         res = real_process.kill_pid(pid)
    #         self.assertEqual(res['code'], 1)
    #     except:
    #         pass

    # def test_kill_name(self):
    #     try:
    #         name = real_process.get_process_info_by_exec('/www/server/panel/mod/test/process/test.py')['data'][0]['name']
    #         res = real_process.kill_name(name)
    #         self.assertEqual(res['code'], 1)
    #     except:
    #         pass
    #
    # def test_kill_tree(self):
    #     try:
    #         pid = real_process.get_process_info_by_exec('/www/server/panel/mod/test/process/test.py')['data'][0]['pid']
    #         res = real_process.kill_tree(pid)
    #         self.assertEqual(res['code'], 1)
    #     except:
    #         pass
    #
    # def test_kill_proc_all(self):
    #     pid = real_process.get_process_info_by_exec('/www/server/panel/mod/test/process/test.py')['data'][0]['pid']
    #     res = real_process.kill_proc_all(pid)
    #     self.assertEqual(res['code'], 1)
    #
    # def test_kill_port(self):
    #     res = real_process.kill_port(22)
    #     self.assertEqual(res['code'], 1)

    def test_add_black_ip(self):
        res = real_process.add_black_ip(['1.2.3.4'])
        self.assertEqual(res['code'], 1)

    def test_del_black_ip(self):
        res = real_process.del_black_ip(['1.2.3.4'])
        self.assertEqual(res['code'], 1)

    def test_firewall_reload(self):
        res = real_process.firewall_reload()
        self.assertEqual(res['code'], 1)

    def test_get_run_list(self):
        res = real_process.get_run_list()
        self.assertEqual(res['code'], 1)



if __name__ == '__main__':
    unittest.main()
