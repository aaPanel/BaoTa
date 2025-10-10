import unittest
import sys
if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")
from mod.base import RealProcess

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
import public

from mod.project.php.php_asyncMod import main as php_async
phpasync = php_async()

class Testmain(unittest.TestCase):
    def test_create_project(self):
        args = {
            'webname':{"domain":"test.c","domainlist":[]},
            'php_version':'74',
            'site_path':'/xiaopacai/swoole-webim-demo-master',
            'project_cmd':'php server/hsw_server.php start',
            'install_dependence':'1',
            'sql':'',
            'sql_name':'',
            'sql_user': '',
            'sql_pwd': '',
            'sql_codeing': '',
            'project_ps': '',
            'open_proxy': '',
            'project_proxy_path': '',
            'project_port': '',
        }
        # phpasync.create_project(public.to_dict_obj(args))


    def test_delete_site(self):
        args = {
            'webname':"test.c",
            'id':'1',
        }
        # phpasync.delete_site(public.to_dict_obj(args))

    def test_get_project_list(self):
        res = phpasync.get_project_list(public.to_dict_obj({}))
        self.assertEqual(type(res), dict)

    def test_project_get_domain(self):
        args = {
            'sitename':'sdadaw.c'
        }
        res = phpasync.project_get_domain(public.to_dict_obj(args))
        self.assertEqual(type(res), dict)


    def test_project_remove_domain(self):
        self.fail()

    def test_project_add_domain(self):
        args = {
            'sitename':'sdadaw.c',
            'domain':["daw.daw","ssff.cxs"]
        }
        res = phpasync.project_add_domain(public.to_dict_obj(args))
        self.assertEqual(type(res), dict)
    def test_get_project_run_state(self):
        args = {
            'sitename':'sdadaw.c',
        }
        res = phpasync.get_project_run_state(public.to_dict_obj(args))
        self.assertEqual(type(res), dict)

    def test_modify_project_run_state(self):
        args = {
            'sitename':'sdadaw.c',
            'status':'stop'
        }
        res = phpasync.modify_project_run_state(public.to_dict_obj(args))
        self.assertEqual(type(res), dict)

    def test_async_dependence_config(self):
        self.fail()

    def test_modify_project(self):
        args = {
            'sitename':'sdadaw.c',
            'php_version':'74',
            'project_path':'/xiaopacai/swoole-webim-demo-master',
            'project_cmd':'php server/hsw_server.php start',
            'site_run_path':'/xiaopacai/swoole-webim-demo-master',
            'project_port': '',
        }
        res = phpasync.modify_project(public.to_dict_obj(args))
        self.assertEqual(type(res), dict)

    def test_get_project_log(self):
        args = {
            'sitename':'sdadaw.c',
        }
        res = phpasync.get_project_log(public.to_dict_obj(args))
        self.assertEqual(type(res), dict)

    def test_get_config_file(self):
        args = {
            'sitename':'sdadaw.c',
        }
        res = phpasync.get_config_file(public.to_dict_obj(args))
        self.assertEqual(type(res), dict)

    def test_upload_version(self):
        self.fail()

    def test_get_version_list(self):
        args = {
            'sitename':'sdadaw.c',
        }
        res = phpasync.get_version_list(public.to_dict_obj(args))

    def test_remove_version(self):
        args = {
            'sitename':'sdadaw.c',
            'version':'1'
        }
        res = phpasync.remove_version(public.to_dict_obj(args))
        self.assertEqual(type(res), dict)

    def test_recover_version(self):
        args = {
            'sitename':'sdadaw.c',
            'version':'1'
        }
        res = phpasync.recover_version(public.to_dict_obj(args))
        self.assertEqual(res['code'], 1)

    def test_now_file_backup(self):
        args = {
            'sitename':'sdadaw.c',
            'version':'2'
        }
        res = phpasync.now_file_backup(public.to_dict_obj(args))
        self.assertEqual(res['code'], 1)

    def test_set_version_ps(self):
        args = {
            'sitename':'sdadaw.c',
            'version':'2',
            'ps':'test'
        }
        res = phpasync.set_version_ps(public.to_dict_obj(args))
        self.assertEqual(res['code'], 1)

    def test_get_setup_log(self):
        args = {
            'sitename':'sdadaw.c',
        }
        res = phpasync.get_setup_log(public.to_dict_obj(args))
        self.assertEqual(type(res), dict)

    def test_add_crontab(self):
        pass

    def test_get_crontab_list(self):
        args = {
            'sitename':'sdadaw.c',
        }
        res = phpasync.get_crontab_list(public.to_dict_obj(args))
        self.assertEqual(res['code'], 1)

    def test_start_task(self):
        args = {
            'id':'19',
        }
        res = phpasync.start_task(public.to_dict_obj(args))
        self.assertEqual(res['code'], 1)

    def test_modify_crontab_status(self):
        args = {
            'id':'19',
        }
        res = phpasync.modify_crontab_status(public.to_dict_obj(args))
        self.assertEqual(res['code'], 1)

    def test_remove_crontab(self):
        args = {
            'id':'19',
        }
        res = phpasync.remove_crontab(public.to_dict_obj(args))
        self.assertEqual(res['code'], 1)

    def test_modify_crontab(self):
        pass

    def test_get_crontab_log(self):
        args = {
            'id':'19',
        }
        res = phpasync.get_crontab_log(public.to_dict_obj(args))
        self.assertEqual(res['code'], 1)

    def test_clearn_logs(self):
        args = {
            'id':'19',
        }
        res = phpasync.clearn_logs(public.to_dict_obj(args))
        self.assertEqual(res['code'], 1)

    def test_get_group_list(self):
        res = phpasync.get_group_list(public.to_dict_obj('{}'))
        self.assertEqual(res['code'], 1)

    def test_create_group(self):
        args = {
            'group_name':'test',
        }
        res = phpasync.create_group(public.to_dict_obj(args))
        self.assertEqual(res['code'], 1)

    def test_remove_group(self):
        args = {
            'group_name':'test',
        }
        res = phpasync.remove_group(public.to_dict_obj(args))
        self.assertEqual(res['code'], 1)

    def test_group_add_project(self):
        args = {
            'group_name':'test',
            'project_name':'sdadaw.c'
        }
        res = phpasync.group_add_project(public.to_dict_obj(args))
        self.assertEqual(res['code'], 1)

    def test_group_remove_project(self):
        args = {
            'group_name':'test',
            'project_name':'sdadaw.c'
        }
        res = phpasync.group_remove_project(public.to_dict_obj(args))
        self.assertEqual(res['code'], 1)

    def test_set_group_interval(self):
        args = {
            'group_name':'test',
            'interval':'15'
        }
        res = phpasync.set_group_interval(public.to_dict_obj(args))
        self.assertEqual(res['code'], 1)

    def test_set_group_status(self):
        args = {
            'group_name':'test',
            'status':'1'
        }
        res = phpasync.set_group_status(public.to_dict_obj(args))
        self.assertEqual(res['code'], 1)

    def test_get_proxy_file(self):
        args = {
            'sitename':'sdadaw.c',
            'proxyname':'test'
        }
        res = phpasync.get_proxy_file(public.to_dict_obj(args))
        self.assertEqual(res['code'], 1)

    def test_save_proxy_file(self):
        args = {
            'sitename':'sdadaw.c',
            'proxyname':'test',
            'file':'test'
        }
        res = phpasync.save_proxy_file(public.to_dict_obj(args))
        self.assertEqual(res['code'], 1)

if __name__ == '__main__':
    unittest.main()
