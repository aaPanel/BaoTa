import unittest
import sys

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")
if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
from mod.base import RealUser

realuser = RealUser()


class TestRealUser(unittest.TestCase):
    def setUp(self):
        realuser.add_user('test1', 'test1', 'test1')
        realuser.add_group('test')

    def tearDown(self):
        realuser.remove_user('test1')
        realuser.remove_user('test')
        realuser.remove_group('test1')
        realuser.remove_group('test')

    def test_get_user_list(self):
        print('get_user_list:')
        res = realuser.get_user_list()
        print(res)
        self.assertEqual(res['code'], 1)

    def test_get_group_list(self):
        print('get_group_list:')
        res = realuser.get_group_list()
        print(res)
        self.assertEqual(res['code'], 1)

    def test_add_user(self):
        print('add_user:')
        res = realuser.add_user('test', 'test', 'test')
        print(res)
        self.assertEqual(res['code'], 1)

    def test_remove_user(self):
        print('remove_user:')
        res = realuser.remove_user('test1')
        print(res)
        self.assertEqual(res['code'], 1)

    def test_edit_user_pwd(self):
        print('edit_user_pwd:')
        res = realuser.edit_user_pwd('test1', 'test111')
        print(res)
        self.assertEqual(res['code'], 1)

    def test_edit_user_group(self):
        print('edit_user_group:')
        res = realuser.edit_user_group('test1', 'test')
        print(res)
        self.assertEqual(res['code'], 1)

    def test_edit_user_ps(self):
        print('edit_user_ps:')
        res = realuser.edit_user_ps('test1', 'test')
        print(res)
        self.assertEqual(res['code'], 1)

    def test_edit_user_status(self):
        print('edit_user_status:')
        res = realuser.edit_user_status('test1', '0')
        print(res)
        self.assertEqual(res['code'], 1)

    def test_edit_user_login_shell(self):
        print('edit_user_login_shell:')
        res = realuser.edit_user_login_shell('test1', '/bin/bash')
        print(res)
        self.assertEqual(res['code'], 1)

    def test_edit_user_home(self):
        print('edit_user_home:')
        res = realuser.edit_user_home('test1', '/home/test1')
        print(res)
        self.assertEqual(res['code'], 1)

    def test_get_user_info(self):
        print('get_user_info:')
        res = realuser.get_user_info('test1')
        print(res)
        self.assertEqual(res['code'], 1)

    def test_add_group(self):
        print('add_group:')
        res = realuser.add_group('test2')
        print(res)
        realuser.remove_group('test2')
        self.assertEqual(res['code'], 1)

    def test_remove_group(self):
        realuser.add_group('test')
        print('remove_group:')
        res = realuser.remove_group('test')
        print(res)
        self.assertEqual(res['code'], 1)

    def test_edit_group_name(self):
        print('edit_group_name:')
        res = realuser.edit_group_name('test', 'test5')
        print(res)
        print(realuser.remove_group('test5'))
        self.assertEqual(res['code'], 1)

    def test_get_group_info(self):
        print('get_group_info:')
        res = realuser.get_group_info('test1')
        print(res)
        self.assertEqual(res['code'], 1)

    def test_get_group_user(self):
        print('get_group_user:')
        res = realuser.get_group_user('test1')
        print(res)
        self.assertEqual(res['code'], 1)

    def test_get_user_group(self):
        print('get_user_group:')
        res = realuser.get_user_group('test1')
        print(res)
        self.assertEqual(res['code'], 1)

    def test_edit_user_permission(self):
        print('edit_user_permission:')
        res = realuser.edit_user_permission('test1', '777')
        print(res)
        self.assertEqual(res['code'], 1)

    def test_edit_group_permission(self):
        print('edit_group_permission:')
        res = realuser.edit_group_permission('test1', '777')
        print(res)
        self.assertEqual(res['code'], 1)

    def test_edit_user_name(self):
        print('edit_user_name:')
        res = realuser.edit_user_name('test1', 'test')
        print(res)
        self.assertEqual(res['code'], 1)


if __name__ == '__main__':
    unittest.main()
