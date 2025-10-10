# coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: zhwen <zhwen@aapanel.com>
# +-------------------------------------------------------------------
import os
import time
import json
import sys
import public_wp as public
import re
import requests
from bs4 import BeautifulSoup
import panelMysql as panelMysql
from wptoolkitModel import base
from public_wp import Param
from public_wp import Validator
from wptoolkitModel.base import wpbase

# import wp-toolkit core
# from wp_toolkit import wp_version, wpmgr, wpfastcgi_cache


def get_mem():
    import psutil
    mem = psutil.virtual_memory()
    memInfo = {'memTotal': int(mem.total / 1024 / 1024), 'memFree': int(mem.free / 1024 / 1024),
               'memBuffers': int(mem.buffers / 1024 / 1024), 'memCached': int(mem.cached / 1024 / 1024)}
    return memInfo['memTotal']


class one_key_wp(wpbase):
    wp_package_url = 'https://wordpress.org/latest.zip'
    # wp_package_url = 'http://download.bt.cn/install/package/wordpress-5.9.1.zip'
    base_path = "/www/server/panel/"
    wp_session_path = '{}/data/wp_session'.format(base_path)
    package_zip = '{}/package/wp.zip'.format(base_path)
    md5_file = '{}/package/md5'.format(base_path)
    log_path = '/tmp/schedule.log'
    __php_tmp_file = '/tmp/wp_tmp'.format(base_path)
    panel_db = "/www/server/panel/data/default.db"
    timeout_count = 0
    old_time = 0
    __wp_session = None
    __session_resp = None
    __ajax_nonce = None
    __domain = None
    __plugin_page_content = None
    wp_user = None
    wp_passwd = None

    def __init__(self, get=None):
        super(one_key_wp, self).__init__(get)
        self.create_wp_table()
        if not self.__wp_session:
            self.__wp_session = requests.Session()

        # import PluginLoader
        # self.__IS_PRO_MEMBER = PluginLoader.get_auth_state() > 0

    def get_headers(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36',
            'Host': self.__domain
        }

    def get_plugin_page(self):
        _get_ajax_nonce_url = "http://{}/wp-admin/plugins.php".format(self.__domain)
        self.__plugin_page_content = self.__wp_session.get(_get_ajax_nonce_url, headers=self.get_headers(),
                                                           verify=False).text

    def get_wp_nonce(self, content, rep):
        rex = re.search(rep, content)
        if rex:
            return rex.group(1)

    def get_nonce(self):
        resp = self.__session_resp
        if resp != '1':
            resp = resp.text
        else:
            self.get_plugin_page()
            resp = self.__plugin_page_content
        _ajax_nonce_rep = '"ajax_nonce\\\"\\:\\\"(\\w+)'
        rex = re.search(_ajax_nonce_rep, resp)
        if rex:
            self.__ajax_nonce = rex.group(1)

    def __load_cookies(self, s_id):
        self.__domain = self.get_wp_auth(s_id)
        f = '{}/{}'.format(self.wp_session_path, self.__domain)
        c = public.readFile(f)
        if c:
            mtime = os.path.getmtime(f)
            expried = 86400
            if time.time() - mtime > expried:
                print('cookies expired, re-login wordpress')
                self.__login_wp()
            else:
                print('use local session')
                self.__wp_session.cookies.update(json.loads(c))
                self.__session_resp = '1'
        else:
            print('No local cookies, login wordpress')
            self.__login_wp()
        # self.__login_wp()
        # print('login success!')
        try:
            self.get_nonce()
        except:
            pass
        if not self.__ajax_nonce:
            self.__login_wp()
            self.get_nonce()
        self.get_plugin_page()

    def __save_cookies(self):
        if not os.path.exists(self.wp_session_path):
            os.mkdir(self.wp_session_path)
        f = '{}/{}'.format(self.wp_session_path, self.__domain)
        return public.writeFile(f, json.dumps(self.__wp_session.cookies.get_dict()))

    def __login_wp(self):

        wp_login = 'http://{}/wp-login.php'.format(self.__domain)
        headers1 = {'Cookie': 'wordpress_test_cookie=WP Cookie check',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36',
                    # 'referer':"https://{}/wp-login.php?loggedout=true&wp_lang=en_US".format(self.__domain),
                    'Host': self.__domain
                    }
        datas = {
            'log': self.wp_user,
            'pwd': self.wp_passwd,
            'wp-submit': 'Log In',
            # 'redirect_to': 'https://{}/wp-admin'.format(self.__domain),
            'testcookie': '1'
        }
        # hosts = public.readFile('/etc/hosts')
        # if not hosts:
        #     return False
        # if not re.search(r'127.0.0.1\s+{}'.format(self.__domain),hosts):
        #     public.writeFile('/etc/hosts','\n127.0.0.1 {}'.format(self.__domain),'a+')

        self.__session_resp = retry(
            lambda: self.__wp_session.post(wp_login, headers=headers1, data=datas, verify=False))

        # cookies持久化
        self.__save_cookies()

    # 写输出日志
    def write_logs(self, log_msg, clean=None):
        if clean:
            fp = open(self.log_path, 'w')
            fp.write(log_msg)
            fp.close()
        fp = open(self.log_path, 'a+')
        fp.write(log_msg + '\n')
        fp.close()

    # 下载文件
    def download_file(self):
        try:
            path = os.path.dirname(self.package_zip)
            if not os.path.exists(path): os.makedirs(path)
            import urllib, socket, ssl
            ssl._create_default_https_context = ssl._create_unverified_context
            socket.setdefaulttimeout(10)
            self.pre = 0
            self.old_time = time.time()
            print("Download the installation package: {} --> {}".format(self.wp_package_url, self.package_zip))
            self.write_logs(
                "|-Download the installation package: {} --> {}".format(self.wp_package_url, self.package_zip))
            if sys.version_info[0] == 2:
                urllib.urlretrieve(self.wp_package_url, filename=self.package_zip, reporthook=self.download_hook)
            else:
                urllib.request.urlretrieve(self.wp_package_url, filename=self.package_zip,
                                           reporthook=self.download_hook)
            md5str = public.FileMd5(self.package_zip)
            public.writeFile(self.md5_file, str(md5str))
        except:
            print("Download error: {}".format(public.get_error_info()))
            if self.timeout_count > 5: return;
            self.timeout_count += 1
            time.sleep(5)
            self.download_file()

    # 下载文件进度回调
    def download_hook(self, count, blockSize, totalSize):
        used = count * blockSize
        pre1 = int((100.0 * used / totalSize))
        if self.pre != pre1:
            dspeed = used / (time.time() - self.old_time)
            self.pre = pre1

    def check_package(self):
        # 检查本地包
        download = False
        md5str = None
        if os.path.exists(self.package_zip):
            md5str = public.FileMd5(self.package_zip)
        if os.path.exists(self.md5_file) and md5str:
            if md5str != public.readFile(self.md5_file):
                download = True
        else:
            download = True
        return download

    def download_latest_package(self):
        print("Start downloading the installation package...")
        self.write_logs("|-Start downloading the installation package...")

        if os.path.exists(self.package_zip):
            # 获取文件的最后修改时间
            modified_time = os.path.getmtime(self.package_zip)
            # 计算当前时间与最后修改时间的差值
            time_diff = time.time() - modified_time
            time2 = 30 * 24 * 60 * 60

            if time_diff > time2:  # 如果超过30天，则删除文件
                os.remove(self.package_zip)
                os.remove(self.md5_file)
                self.write_logs("|-Del package...")

        if not self.check_package():
            print("|-MD5 consistent, no need to download...")
            return public.return_msg_gettext(True, public.lang("MD5 consistent!"))
        self.download_file()
        if not os.path.exists(self.package_zip):
            self.write_logs("|-Download failed...")
            print("Download failed...")
            return public.return_msg_gettext(False, public.lang("File download failed!"))
        return public.return_msg_gettext(True, public.lang("Download successfully"))

    def unzip_package(self, site_path):
        print("Start unzipping the installation package...")
        self.write_logs("|-Start unzipping the installation package...")
        public.ExecShell('unzip -o {} -d {}/'.format(self.package_zip, site_path))
        public.ExecShell('mv {}/wordpress/* {}'.format(site_path, site_path))
        os.removedirs("{}/wordpress/".format(site_path))
        print("Start setting up site permissions...")
        self.write_logs("|-Start setting up site permissions...")
        self.set_permission(site_path)

    def set_permission(self, site_path):
        os.system('chmod -R 755 ' + site_path)
        os.system('chown -R www.www ' + site_path)

    def set_urlrewrite(self, site_name, site_path):
        webserver = public.get_webserver()

        if webserver == 'openlitespeed':
            webserver = 'apache'

        swfile = '/www/server/panel/rewrite/{}/wordpress.conf'.format(webserver)
        if os.path.exists(swfile):
            rewriteConf = public.readFile(swfile)

            if webserver == 'nginx':
                dwfile = '{}/vhost/rewrite/{}.conf'.format(self.base_path, site_name)

            else:
                dwfile = '{}/.htaccess'.format(site_path)

            public.writeFile(dwfile, rewriteConf)

    def __write_db(self, s_id, d_id, prefix, user_name, admin_password):
        print("Inserting data...")
        pdata = {"s_id": s_id, "d_id": d_id, "prefix": prefix, "user": user_name, "pass": admin_password}
        public.M('wordpress_onekey').where('s_id=?', (s_id,)).field('s_id').find()
        if public.M('wordpress_onekey').where('s_id=?', (s_id,)).field('s_id').find():
            print("Data already exists, update data...")
            public.M('wordpress_onekey').where('s_id=?', (s_id,)).update(pdata)
            return
        print("Insert data...")
        print("Insert data:{}".format(pdata))
        print("Result:{}".format(public.M('wordpress_onekey').insert(pdata)))

    def create_wp_table(self):
        if not public.M('sqlite_master').where('type=? AND name=?', ('table', 'wordpress_onekey')).count():
            public.M('').execute('''CREATE TABLE "wordpress_onekey" (
                 "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                 "s_id" INTEGER DEFAULT '',
                 "d_id" INTEGER DEFAULT '',
                 "prefix" TEXT DEFAULT '',
                 "user" TEXT DEFAULT '',
                 "pass" TEXT DEFAULT '');''')

    def init_wp(self, values):
        hosts = public.readFile('/etc/hosts')
        if not hosts:
            return False
        if not re.search(r'127.0.0.1\s+{}'.format(values['site_name']), hosts):
            public.writeFile('/etc/hosts', '\n127.0.0.1 {}'.format(values['site_name']), 'a+')

        self.write_logs("|-Start initializing Wordpress...")

        from wp_toolkit import wpmgr

        # 初始化WP管理类
        wpmgr_obj = wpmgr(values['s_id'])

        # 初始化WP网站配置
        self.write_logs("|-Start setup configurations...")
        ok, msg = wpmgr_obj.setup_config(values['dbname'], values['db_user'], values['db_pwd'], 'localhost',
                                         values['prefix'])
        self.write_logs('|-Setup config >>> {} {}'.format('OK' if ok else 'FAIL', msg))

        if not ok:
            raise Exception(msg)

        # 初始化WP网站信息
        self.write_logs("|-Start installations...")
        ok, msg = wpmgr_obj.wp_install(values['weblog_title'], values['user_name'], values['admin_email'],
                                       values['admin_password'], values['language'])
        self.write_logs('|-Installation {} {}'.format('OK' if ok else 'FAIL', msg))

        if not ok:
            raise Exception(msg)

        # if self.__IS_PRO_MEMBER:
        #     from wp_toolkit import wpmgr
        #
        #     # 初始化WP管理类
        #     wpmgr_obj = wpmgr(values['s_id'])
        #
        #     # 初始化WP网站配置
        #     self.write_logs("|-Start setup configurations...")
        #     ok, msg = wpmgr_obj.setup_config(values['dbname'], values['db_user'], values['db_pwd'], 'localhost', values['prefix'])
        #     self.write_logs('|-Setup config >>> {} {}'.format('OK' if ok else 'FAIL', msg))
        #
        #     if not ok:
        #         raise Exception(msg)
        #
        #     # 初始化WP网站信息
        #     self.write_logs("|-Start installations...")
        #     ok, msg = wpmgr_obj.wp_install(values['weblog_title'], values['user_name'], values['admin_email'], values['admin_password'], values['language'])
        #     self.write_logs('|-Installation {} {}'.format('OK' if ok else 'FAIL', msg))
        #
        #     if not ok:
        #         raise Exception(msg)
        # else:
        #     self.request_setup_0(values)
        #     time.sleep(1)
        #     if not self.request_setup_2(values):
        #         return public.return_msg_gettext(False,
        #                                          "The database connection is abnormal. Please check whether the root user authority or database configuration parameters are correct.")
        #     time.sleep(1)
        #     self.request_setup_3(values)
        #     time.sleep(1)
        #     self.request_setup_4(values)
        #     time.sleep(1)

        # 配置伪静态规则
        self.set_urlrewrite(values['site_name'], values['site_path'])

    def request_setup_0(self, values):
        self.write_logs("|-Start initializing Wordpress language...")
        url = "http://{}/wp-admin/setup-config.php?step=0".format(values['site_name'])
        param = {
            "url": url,
            "data": {"language": values['language']},
            "headers": {"Host": values['domain']}
        }
        # result = self.request_wp_api(param)
        response = retry(lambda: self.request_wp_api(param))
        # public.print_log("开始检查--request_setup_0_result:{}".format(response))

    def request_setup_2(self, values):
        self.write_logs("|-Start initializing Wordpress config...")
        url = "http://{}/wp-admin/setup-config.php?step=2".format(values['site_name'])
        param = {
            "url": url,
            "headers": {"Host": values['domain']},
            "data": {
                "dbname": values['dbname'],
                "uname": values['db_user'],
                "pwd": values['db_pwd'],
                "dbhost": "localhost",
                "prefix": values['prefix'],
                "language": values['language'],
                "submit": "Submit",
            }
        }
        # result = self.request_wp_api(param)
        response = retry(lambda: self.request_wp_api(param))
        if "install.php?language=ja":
            return True

    def request_setup_3(self, values):
        self.write_logs("|-Start initializing Wordpress install language...")
        url = "http://{}/wp-admin/install.php?language={}".format(values['site_name'], values['language'])
        param = {
            "url": url,
            "headers": {"Host": values['domain']},
            "data": {
                "language": values['language']
            }
        }
        # self.request_wp_api(param)
        response = retry(lambda: self.request_wp_api(param))

    def request_setup_4(self, values):
        self.write_logs("|-Start installing the wordpress program...")
        url = "http://{}/wp-admin/install.php?step=2".format(values['site_name'])
        param = {
            "url": url,
            "headers": {"Host": values['domain']},
            "data": {
                "weblog_title": values['weblog_title'],
                "user_name": values['user_name'],
                "admin_password": values['admin_password'],
                "admin_password2": values['admin_password'],
                # "pw_weak": values['pw_weak'],  # on/off
                "admin_email": values['admin_email'],
                # "Submit": "Install WordPress",
                "language": values['language']
            }
        }
        # self.request_wp_api(param)
        response = retry(lambda: self.request_wp_api(param))

    def request_wp_api(self, param):
        """需要指定域名得host为本机IP"""
        resp = requests.post(param['url'], data=param['data'], headers=param['headers'])
        # public.print_log("开始检查--request_wp_api:{}".format(resp))
        # public.print_log("开始检查--request_wp_api_resp.text:{}".format(resp.text))
        return resp.text

    def get_update_wp_nonce(self):
        url = "http://{}/wp-admin/update-core.php".format(self.__domain)
        # res = self.action_plugin_get(url)
        _wp_nonce_rep = '"_wpnonce\\\"\\svalue=\\\"(\\w+)'
        # rex = re.search(_wp_nonce_rep,res)
        # if rex:
        #     self.__wp_nonce = rex.group(1)

        # return self.get_wp_nonce(self.action_plugin_get(url),_wp_nonce_rep)
        response = retry(lambda: self.get_wp_nonce(self.action_plugin_get(url), _wp_nonce_rep))
        return response

    def action_plugin_post(self, param):
        headers = self.get_headers()
        if 'upgrade' in param['data']:
            param['data']['_wpnonce'] = self.get_update_wp_nonce()
            headers['referer'] = 'http://{}/wp-admin/update-core.php'.format(param['domain'])

        response = retry(
            lambda: self.__wp_session.post(param['url'], data=param['data'], headers=headers, verify=False).text)
        return response
        # return self.__wp_session.post(param['url'],data=param['data'], headers=headers, verify=False).text

    def action_plugin_get(self, url, headers=None):
        if not headers:
            headers = self.get_headers()
        # headers['Referer'] = "http://{}/wp-admin".format(self.__domain)

        response = retry(lambda: self.__wp_session.get(url, headers=headers, verify=False).text)
        return response
        # return self.__wp_session.get(url, headers=headers, verify=False).text

    def install_plugin(self, values):
        self.write_logs("|-Start installing the [nginx-helper] plugin...")
        self.__load_cookies(values['s_id'])
        param = {
            "url": "http://{}/wp-admin/admin-ajax.php".format(self.__domain),
            "domain": values['domain'],
            "data": {
                "slug": values['slug'],  # 插件名称 nginx-helper
                "action": values['wp_action'],  # action已经被面板占用 install-plugin
                "_ajax_nonce": self.__ajax_nonce,
                "_fs_nonce": "",
                "username": "",
                "password": "",
                "connection_type": "",
                "public_key": "",
                "private_key": ""
            }
        }
        res = self.action_plugin_post(param)
        return res

    def get_smart_http_expire_form_nonce(self, url):
        public.writeFile('/tmp/2', str(self.action_plugin_get(url)))
        smart_http_expire_form_nonce = '"smart_http_expire_form_nonce\\\"\\svalue=\\\"(\\w+)'
        return self.get_wp_nonce(self.action_plugin_get(url), smart_http_expire_form_nonce)

    def set_nginx_helper(self, values):
        self.write_logs("|-Setting up [nginx-helper] plugin cache rules...")
        self.__load_cookies(values['s_id'])
        url = "http://{}/wp-admin/options-general.php?page=nginx".format(self.__domain)
        param = {
            "url": url,
            "domain": values['domain'],
            "data": {
                "enable_purge": "1",
                "is_submit": "1",
                "cache_method": "enable_fastcgi",
                "purge_method": "unlink_files",
                "redis_hostname": "127.0.0.1",
                "redis_port": "6379",
                "redis_prefix": "nginx-cache",
                "purge_homepage_on_edit": "1",
                "purge_homepage_on_del": "1",
                "purge_page_on_mod": "1",
                "purge_page_on_new_comment": "1",
                "purge_page_on_deleted_comment": "1",
                "purge_archive_on_edit": "1",
                "purge_archive_on_del": "1",
                "purge_archive_on_new_comment": "1",
                "purge_archive_on_deleted_comment": "1",
                "purge_url": "",
                "log_level": "INFO",
                "log_filesize": "5",
                "smart_http_expire_form_nonce": self.get_smart_http_expire_form_nonce(url),
                "smart_http_expire_save": "Save All Changes"
            }
        }
        return self.action_plugin_post(param)

    def act_nginx_helper_active(self, values):
        self.write_logs("|-activating [nginx-helper] plugin...")
        self.__load_cookies(values['s_id'])
        values['active_id'] = "activate-nginx-helper"
        self.get_plugin_page()
        res = self.get_plugin_url(values['active_id'], self.__plugin_page_content)
        url = 'http://{}/wp-admin/{data}'.format(self.__domain,
                                                 data=str(str(res[0]).split('"')[5]))
        url = url.replace('amp;', '')
        return self.action_plugin_get(url)

    def get_plugin_url(self, active_id, content):
        # soup = BeautifulSoup(content)
        soup = BeautifulSoup(content, features="html.parser")
        res = soup.find_all(id=active_id)
        return res

    def generate_wp_passwd(self, site_path, new_pass):
        hash_password_code = public.readFile("{}/wp-includes/class-phpass.php".format(site_path))
        extra_code = """
         $passwordValue = "%s";
         $wp_hasher = new PasswordHash(8, TRUE);
         $sigPassword = $wp_hasher->HashPassword($passwordValue);
         $data = $wp_hasher->CheckPassword($passwordValue,$sigPassword);
         if($data){
             echo 'True|'.$sigPassword;;
         }else{
         	echo 'False|'.$sigPassword;;
         }
         """ % new_pass
        php_code = hash_password_code + extra_code
        public.writeFile(self.__php_tmp_file, php_code)
        a, e = public.ExecShell("php -f {}".format(self.__php_tmp_file))
        os.remove(self.__php_tmp_file)
        res = a.split('|')
        if res[0] == "True":
            return public.return_message(0, 0, res[1])
        return public.return_message(-1, 0, public.lang("Generated password detection failed!"))

    def get_cache_status(self, s_id):
        """
        s_id 网站id
        """
        import data
        site_info = public.M('sites').where('id=?', (s_id,)).field('name').find()

        if not isinstance(site_info, dict):
            return False

        site_name = site_info['name']

        # 获取WP站点绑定的PHP可执行文件
        # from wp import websitemgr

        php_v = public.get_site_php_version(site_name).replace('.', '')

        return fast_cgi().get_fast_cgi_status(site_name, php_v)

    ##############################对外接口—BEGIN##############################
    def get_wp_username(self, get):
        """
        s_id 网站ID
        """
        # 校验参数
        try:
            get.validate([
                Param('s_id').Integer(),
            ], [
                public.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        values = self.check_param(get)
        if values['status'] == -1:
            return values
        values = values['msg']
        db_info = public.M('wordpress_onekey').where('s_id=?', (values['s_id'],)).find()
        db_name = public.M('databases').where('id=?', (db_info['d_id'],)).field('name').find()
        if "name" not in db_name:
            return public.return_message(-1, 0, public.lang("The database of this wordpress was not found, this may be caused by the fact that you have manually deleted the database"))
        db_name = db_name['name']
        mysql_obj = panelMysql.panelMysql()
        res = mysql_obj.query('select * from {}.{}users'.format(
            db_name, db_info['prefix']))
        if hasattr(res, '__iter__'):
            return public.return_message(0, 0, [i[1] for i in res])
        else:
            return public.return_message(-1, 0,
                                         "Site database [{}] failed to query users, try setting the database for this site. Error: {}".format(
                                             db_name, res))

    def reset_wp_password(self, get):
        """
        重置wordpress用户密码
        s_id 网站ID
        user 要重置的用户名
        new_pass
        """
        try:
            get.validate([
                Param('user').String(),
                Param('new_pass').String(),
                Param('s_id').Integer(),

            ], [
                public.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        values = self.check_param(get)
        if values['status'] == -1:
            return values
        values = values['msg']
        s_id = values['s_id']
        db_info = public.M('wordpress_onekey').where('s_id=?', (s_id,)).find()
        db_name = public.M('databases').where('id=?', (db_info['d_id'],)).field('name').find()['name']
        path = public.M('sites').where('id=?', (s_id,)).field('path').find()['path']
        new_pass = values['new_pass']
        passwd = self.generate_wp_passwd(path, new_pass)
        if passwd['status'] == -1:
            return passwd

        passwd = passwd['message']

        if isinstance(passwd, dict):
            passwd = passwd.get('result', None)

        if passwd is None:
            return public.fail_v2('Reset password failed')

        mysql_obj = panelMysql.panelMysql()
        sql = 'update {}.{}users set user_pass = "{}" where user_login = "{}"'.format(
            db_name, db_info['prefix'], passwd, values['user'])
        mysql_obj.execute(sql)
        return public.return_message(0, 0, public.lang("Password reset successful"))

    # 获取WP可用版本列表
    def get_wp_available_versions(self, args: public.dict_obj):
        # 校验参数
        try:
            args.validate([
                Param('php_version_short').Integer(),
            ], [
                public.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        from wp_toolkit import wp_version

        versions = list(map(lambda x: {
            'locale': x['locale'],
            'version': x['version'],
            'php_version': x['php_version'],
            'mysql_version': x['mysql_version'],
        }, wp_version().latest_versions()))

        if 'php_version_short' in args:
            versions = list(
                filter(lambda x: int(args.php_version_short) >= int(''.join(str(x['php_version']).split('.')[:2])),
                       versions))

        return public.success_v2(versions)

    # 获取WP网站本地版本号
    def get_wp_version(self, s_id):
        """获取wordpress本地版本
        s_id 网站id
        """
        path = public.M('sites').where('id=?', (s_id,)).field('path').find()['path']
        conf_file = "{}/wp-includes/version.php".format(path)
        conf = public.readFile(conf_file)
        try:
            version = re.search('\\$wp_version\\s*=\\s*[\'\"]{1}([\\d\\.]*)[\'\"]{1}', conf).groups(1)[0]
        except:
            version = "00"
        return version

    # 获取WP已发布的最新版本号
    def get_wp_version_online(self):
        """获取wordpress线上版本"""
        url = "http://wordpress.org/download/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36'
        }
        result = requests.get(url, headers=headers)
        result = re.search(r'Download\s+WordPress\s+([\d\.]+)', result.text)
        if result:
            return result.group(1)
        return "00"

    # 检查WP是否有新版本可以更新
    def is_update(self, get):
        """
        s_id 网站ID
        """
        values = self.check_param(get)
        if values['status'] == -1:
            return values
        values = values['msg']
        online_v = self.get_wp_version_online()
        local_v = self.get_wp_version(values['s_id'])
        update = False
        if str(online_v) != str(local_v):
            update = True
        data = {
            "online_v": online_v,
            "local_v": local_v,
            "update": update
        }
        return_message = public.return_msg_gettext(True, data)
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    def purge_all_cache(self, get):
        """
        清理所有缓存
        """
        # 校验参数
        try:
            get.validate([
                Param('s_id').Integer(),

            ], [
                public.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        if public.get_webserver() != "nginx":
            return public.return_message(-1, 0, public.lang("此功能目前仅支持Nginx"))

        from wp_toolkit import wpmgr
        wpmgr(get.s_id).purge_cache_with_nginx_helper()

        # if self.__IS_PRO_MEMBER:
        #     from wp_toolkit import wpmgr
        #     wpmgr(get.s_id).purge_cache_with_nginx_helper()
        # else:
        #     cache_dir = "/dev/shm/nginx-cache/wp"
        #     public.ExecShell("rm -rf {}/*".format(cache_dir))

        return public.return_message(0, 0, public.lang("清理成功！"))

    def set_fastcgi_cache(self, get):
        """
        设置缓存
        version php版本
        sitename 完整名
        act disable/enable 开启关闭缓存
        """
        # 校验参数
        try:
            get.validate([
                Param('version').String(),
                Param('sitename').String(),
                Param('act').String(),

            ], [
                public.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        if public.get_webserver() != "nginx":
            return public.return_message(-1, 0, public.lang("此功能目前只支持Nginx"))
        values = self.check_param(get)
        if values['status'] == -1:
            return values
        values = values['msg']
        if '.' in values['version']:
            values['version'] = values['version'].replace('.', '')

        from wp_toolkit import wpfastcgi_cache

        ok, msg = wpfastcgi_cache().set_website_conf(values['version'], values['sitename'], values['act'],
                                                     immediate=True)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2(msg)

        # if self.__IS_PRO_MEMBER:
        #     from wp_toolkit import wpfastcgi_cache
        #
        #     ok, msg = wpfastcgi_cache().set_website_conf(values['version'], values['sitename'], values['act'], immediate=True)
        #
        #     if not ok:
        #         return public.fail_v2(msg)
        #
        #     return public.success_v2(msg)
        # else:
        #     return fast_cgi().set_website_conf(values['version'], values['sitename'], values['act'])

    # 使用网站ID查询WP站点域名
    def get_wp_auth(self, s_id):
        domain = public.M('domain').where("pid=?", (s_id,)).field('name').find()['name']
        info = public.M('wordpress_onekey').where("s_id=?", (s_id,)).find()
        self.wp_user = info['user']
        self.wp_passwd = info['pass']
        return domain

    # 更新WP版本
    def update_wp(self, args):
        """更新wordpress版本
        s_id 网站ID
        version 需要更新的版本
        """
        from wp_toolkit import wpmgr

        # 校验参数
        try:
            args.validate([
                Param('s_id').Require().Integer('>', 0),
                Param('version').Require().Regexp(r'^\d+(?:\.\d+)+$'),
            ], [
                public.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        ok, msg = wpmgr(args.s_id).update_version(args.version)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2('成功更新到{}'.format(msg))

        # if self.__IS_PRO_MEMBER:
        #     from wp_toolkit import wpmgr
        #
        #     # 校验参数
        #     try:
        #         args.validate([
        #             Param('s_id').Require().Integer('>', 0),
        #             Param('version').Require().Regexp(r'^\d+(?:\.\d+)+$'),
        #         ], [
        #             public.trim_filter(),
        #         ])
        #     except Exception as ex:
        #         public.print_log("error info: {}".format(ex))
        #         return public.return_message(-1, 0, str(ex))
        #
        #     ok, msg = wpmgr(args.s_id).update_version(args.version)
        #
        #     if not ok:
        #         return public.fail_v2(msg)
        #
        #     return public.success_v2('Upgrade to {}'.format(msg))
        # else:
        #     self.__load_cookies(args.s_id)
        #     param = {
        #         "url": "http://{}/wp-admin/update-core.php?action=do-core-upgrade".format(self.__domain),
        #         "domain": self.__domain,
        #         "data": {
        #             # "_wpnonce":get._wpnonce,
        #             "_wp_http_referer": '/wp-admin/update-core.php',
        #             "version": args.version,
        #             "locale": "en_US",
        #             "upgrade": "Update to version {}".format(args.version)
        #         }
        #     }
        #     self.action_plugin_post(param)
        #     return_message=public.return_msg_gettext(True, 'Updated successfully!')
        #     del return_message['status']
        #     return public.return_message(0,0, return_message['msg'])

    # 获取可用的语言列表
    def get_language(self, get=None):
        language = {
            "zh_CN": "简体中文",
            "zh_TW": "繁體中文",
            "zh_HK": "香港中文版	",
            "en": "English (United States)",
            "af": "Afrikaans",
            "am": "አማርኛ",
            "ar": "العربية",
            "ary": "العربية المغربية",
            "as": "অসমীয়া",
            "az": "Azərbaycan dili",
            "azb": "گؤنئی آذربایجان",
            "bel": "Беларуская мова",
            "bg_BG": "Български",
            "bn_BD": "বাংলা",
            "bo": "བོད་ཡིག",
            "bs_BA": "Bosanski",
            "ca": "Català",
            "ceb": "Cebuano",
            "cs_CZ": "Čeština",
            "cy": "Cymraeg",
            "da_DK": "Dansk",
            "de_CH_informal": "Deutsch (Schweiz, Du)",
            "de_DE": "Deutsch",
            "de_DE_formal": "Deutsch (Sie)",
            "de_CH": "Deutsch (Schweiz)",
            "de_AT": "Deutsch (Österreich)",
            "dsb": "Dolnoserbšćina",
            "dzo": "རྫོང་ཁ",
            "el": "Ελληνικά",
            "en_US": "English (United States)",
            "en_NZ": "English (New Zealand)",
            "en_AU": "English (Australia)",
            "en_CA": "English (Canada)",
            "en_GB": "English (UK)",
            "en_ZA": "English (South Africa)",
            "eo": "Esperanto",
            "es_ES": "Español",
            "es_EC": "Español de Ecuador",
            "es_CO": "Español de Colombia",
            "es_AR": "Español de Argentina",
            "es_DO": "Español de República Dominicana",
            "es_PE": "Español de Perú",
            "es_CR": "Español de Costa Rica",
            "es_UY": "Español de Uruguay",
            "es_CL": "Español de Chile",
            "es_PR": "Español de Puerto Rico",
            "es_VE": "Español de Venezuela",
            "es_GT": "Español de Guatemala",
            "es_MX": "Español de México",
            "et": "Eesti",
            "eu": "Euskara",
            "fa_IR": "فارسی",
            "fa_AF": "(فارسی (افغانستان",
            "fi": "Suomi",
            "fr_FR": "Français",
            "fr_BE": "Français de Belgique",
            "fr_CA": "Français du Canada",
            "fur": "Friulian",
            "gd": "Gàidhlig",
            "gl_ES": "Galego",
            "gu": "ગુજરાતી",
            "haz": "هزاره گی",
            "he_IL": "עִבְרִית",
            "hi_IN": "हिन्दी",
            "hr": "Hrvatski",
            "hsb": "Hornjoserbšćina",
            "hu_HU": "Magyar",
            "hy": "Հայերեն",
            "id_ID": "Bahasa Indonesia",
            "is_IS": "Íslenska",
            "it_IT": "Italiano",
            "ja": "日本語",
            "jv_ID": "Basa Jawa",
            "ka_GE": "ქართული",
            "kab": "Taqbaylit",
            "kk": "Қазақ тілі",
            "km": "ភាសាខ្មែរ",
            "kn": "ಕನ್ನಡ",
            "ko_KR": "한국어",
            "ckb": "كوردی‎",
            "lo": "ພາສາລາວ",
            "lt_LT": "Lietuvių kalba",
            "lv": "Latviešu valoda",
            "mk_MK": "Македонски јазик",
            "ml_IN": "മലയാളം",
            "mn": "Монгол",
            "mr": "मराठी",
            "ms_MY": "Bahasa Melayu",
            "my_MM": "ဗမာစာ",
            "nb_NO": "Norsk bokmål",
            "ne_NP": "नेपाली",
            "nl_NL_formal": "Nederlands (Formeel)",
            "nl_NL": "Nederlands",
            "nl_BE": "Nederlands (België)",
            "nn_NO": "Norsk nynorsk",
            "oci": "Occitan",
            "pa_IN": "ਪੰਜਾਬੀ",
            "pl_PL": "Polski",
            "ps": "پښتو",
            "pt_BR": "Português do Brasil",
            "pt_AO": "Português de Angola",
            "pt_PT_ao90": "Português (AO90)",
            "pt_PT": "Português",
            "rhg": "Ruáinga",
            "ro_RO": "Română",
            "ru_RU": "Русский",
            "sah": "Сахалыы",
            "snd": "سنڌي",
            "si_LK": "සිංහල",
            "sk_SK": "Slovenčina",
            "skr": "سرائیکی",
            "sl_SI": "Slovenščina",
            "sq": "Shqip",
            "sr_RS": "Српски језик",
            "sv_SE": "Svenska",
            "sw": "Kiswahili",
            "szl": "Ślōnskŏ gŏdka",
            "ta_IN": "தமிழ்",
            "ta_LK": "தமிழ்",
            "te": "తెలుగు",
            "th": "ไทย",
            "tl": "Tagalog",
            "tr_TR": "Türkçe",
            "tt_RU": "Татар теле",
            "tah": "Reo Tahiti",
            "ug_CN": "ئۇيغۇرچە",
            "uk": "Українська",
            "ur": "اردو",
            "uz_UZ": "O‘zbekcha",
            "vi": "Tiếng Việt",
        }
        return_message = public.return_msg_gettext(True, language)
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    # 请求参数校验
    def check_param(self, args):
        """
        @name 检测传入参数
        @author zhwen<2022-03-10>
        """
        # 检查email格式
        rep_email = r"[\w!#$%&'*+/=?^_`{|}~-]+(?:\.[\w!#$%&'*+/=?^_`{|}~-]+)*@(?:[\w](?:[\w-]*[\w])?\.)+[\w](?:[\w-]*[\w])?"
        # 检查域名格式
        rep_domain = r"^(?=^.{3,255}$)[a-zA-Z0-9\_\-][a-zA-Z0-9\_\-]{0,62}(\.[a-zA-Z0-9\_\-][a-zA-Z0-9\_\-]{0,62})+$"
        values = {}
        # if hasattr(args, 'databaseName'):
        #     values['databaseName'] = public.xssencode2(args.databaseName)

        if hasattr(args, 'd_id'):
            if re.search(r'\d+', args.d_id):
                values["d_id"] = args.d_id
            else:
                return public.return_message(-1, 0, public.lang("Please check if the [{}] format is correct For example: {}", "d_id", "99"))
        if hasattr(args, 's_id'):
            if re.search(r'\d+', args.s_id):
                values["s_id"] = args.s_id
            else:
                return public.return_message(-1, 0, public.lang("Please check if the [{}] format is correct For example: {}", "s_id", "99"))
        if hasattr(args, 'language'):
            if args.language in self.get_language()['msg']:
                values['language'] = args.language
            else:
                return public.return_message(-1, 0, public.lang("Please check if the [{}] format is correct For example: {}", "language", "en"))
        if hasattr(args, 'domain'):
            if re.search(rep_domain, args.domain):
                values['domain'] = public.xssencode2(args.domain)
            else:
                return public.return_message(-1, 0, public.lang("Please check if the [{}] format is correct For example: {}", "domain", "aapanel.com"))
        if hasattr(args, 'weblog_title'):
            values['weblog_title'] = public.xssencode2(args.weblog_title)
        if hasattr(args, 'user_name'):
            values['user_name'] = public.xssencode2(args.user_name)
        if hasattr(args, 'admin_password'):
            values['admin_password'] = public.xssencode2(args.admin_password)
        if hasattr(args, 'pw_weak'):
            if args.pw_weak in ['on', 'off']:
                values['pw_weak'] = args.pw_weak
            else:
                return public.return_message(-1, 0, public.lang("Please check if the [{}] format is correct For example: {}", "pw_weak", "on/off"))
        if hasattr(args, 'admin_email'):
            if re.search(rep_email, args.admin_email):
                values['admin_email'] = public.xssencode2(args.admin_email)
            else:
                return public.return_message(-1, 0, public.lang("Please check if the [{}] format is correct For example: {}", "admin_email", "adimn@aapanel.com"))
        if hasattr(args, 'prefix'):
            values['prefix'] = public.xssencode2(args.prefix)
        if hasattr(args, 'php_version'):
            values['php_version'] = public.xssencode2(args.php_version)
        if hasattr(args, 'enable_cache'):
            values['enable_cache'] = public.xssencode2(args.enable_cache)
        if hasattr(args, 'wp_action'):
            values['slug'] = public.xssencode2(args.slug)
        if hasattr(args, 'slug'):
            values['wp_action'] = public.xssencode2(args.wp_action)
        if hasattr(args, 'active_id'):
            values['active_id'] = public.xssencode2(args.active_id)
        if hasattr(args, 'new_pass'):
            values['new_pass'] = public.xssencode2(args.new_pass)
        if hasattr(args, 'user'):
            values['user'] = public.xssencode2(args.user)
        if hasattr(args, 'sitename'):
            values['sitename'] = public.xssencode2(args.sitename)
        if hasattr(args, 'act'):
            values['act'] = public.xssencode2(args.act)
        if hasattr(args, 'version'):
            values['version'] = public.xssencode2(args.version)
        return public.return_message(0, 0, values)

    # 删除网站
    def del_site(self, get):
        import panelSite
        p = panelSite.panelSite()
        site_info = public.M('sites').where('id=?', (get.s_id,)).find()
        get.id = get.s_id
        get.webname = site_info['name']
        get.ftp = "1"
        get.database = "1"
        get.path = "1"
        p.DeleteSite(get)

    # 安装WP
    def deploy_wp(self, get):
        """
        d_id                    数据据库ID
        s_id                    网站ID
        language                部署wordpress后的语言
        weblog_title            wordpress博客名
        user_name               wordpress后台用户名
        admin_password          管理员密码
        admin_password2
        pw_weak                 允许弱密码
        admin_email             管理员邮箱
        prefix                  wordpress数据表前缀
        php_version             php版本
        enable_cache            开启缓存
        package_version         Wordpress版本
        @name 部署wordpress
        @author zhwen<2022-03-10>
        """
        # 校验参数
        try:
            get.validate([
                Param('domain').String().Host(),
                Param('weblog_title').String(),
                Param('language').String(),
                Param('php_version').String(),
                Param('user_name').String(),
                Param('admin_email').String().Email(),
                Param('prefix').String(),
                Param('pw_weak').String(),
                Param('admin_password').String(),
                Param('enable_cache').Integer(),
                Param('d_id').Integer(),
                Param('s_id').Integer(),
                Param('package_version').String(),
                # Param('databaseName').String(),

            ], [
                public.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        try:
            self.write_logs('', clean=True)
            values = self.check_param(get)
            if not values['status']:
                # 删除自动创建的空白网站
                self.del_site(get)
                return values
            values = values['msg']
            s_id = values['s_id']  # 网站ID
            d_id = values['d_id']  # 数据库ID
            prefix = values['prefix']  # 前缀
            site_info = public.M('sites').where('id=?', (s_id,)).find()
            print("Get site info:\n ID: {}\npath: {}\n".format(s_id, site_info['path']))
            self.write_logs("""
 |-获取网站信息:
     ID: {}
     Path: {}

 """.format(s_id, site_info['path']))
            db_info = public.M('databases').where('id=?', (d_id,)).find()
            if not db_info:
                db_info = public.M('databases').where('pid=?', (values['s_id'],)).find()

            print("Get database information: \nID: {}\nDBName: {}\nUser: {}\nPassWD: {}".format(
                d_id, db_info["name"], db_info["username"], db_info["password"]))
            self.write_logs("""
 |-获取数据库信息: 
     ID: {}
     DBName: {}
     User: {}
     PassWD: {}

 """.format(d_id, db_info["name"], db_info["username"], db_info["password"]))
            values['dbname'] = db_info["name"]
            self.wp_user = values['user_name']
            self.wp_passwd = values['admin_password']
            values['db_user'] = db_info["username"]
            values['db_pwd'] = db_info["password"]
            values['site_path'] = site_info['path']
            values['site_name'] = site_info['name']

            # 开始下载安装包
            from wp_toolkit import wp_version

            wp_version_obj = wp_version()

            if 'package_version' not in get or get.package_version is None:
                get.package_version = wp_version_obj.latest_version()['version']

            self.write_logs('|-Package version: {}'.format(get.package_version))

            # 下载特定版本的安装包
            one_key_wp.package_zip = wp_version_obj.download_package(get.package_version)


            self.unzip_package(site_info['path'])

            # 优化PHP
            res = optimize_php().optimize_php(get)
            if not res['status']:
                return public.return_message(-1, 0, res)

            # 初始化wp
            self.init_wp(values)
            self.__write_db(s_id, d_id, prefix, get.user_name, get.admin_password)

            # 优化mysql
            # optimize_db().self_db_cache(get)

            # 设置fastcgi缓存
            if int(get.enable_cache) == 1 and public.get_webserver() == 'nginx':
                from wp_toolkit import wpmgr, wpfastcgi_cache

                # 配置Nginx-fastcgi-cache

                wpfastcgi_cache().set_fastcgi(values['site_path'], values['site_name'], values['php_version'])

                self.write_logs('|-安装WP插件 nginx-helper ...')
                wpmgr(s_id).init_plugin_nginx_helper()
                self.write_logs('|-WP插件 nginx-helper 安装成功')

            # 设置登录入口保护
            if int(get.get('enable_whl', 0)) == 1:
                from wp_toolkit import wpmgr

                # 安装并启用wps-hide-login插件
                self.write_logs('|-安装WP插件 wps-hide-login ...')
                wpmgr(s_id).init_plugin_wps_hide_login(get.get('whl_page', 'login'),
                                                       get.get('whl_redirect_admin', '404'))
                self.write_logs('|-WP插件 wps-hide-login 安装成功')

            public.ServiceReload()

            self.write_logs("\n\n\n|-部署成功")

            return public.return_message(0, 0, public.lang("部署成功"))
        except:
            self.del_site(get)
            from traceback import format_exc
            public.print_log(format_exc())
            return public.return_message(-1, 0, public.lang("部署失败"))

    # 重新关联WP网站数据库
    def reset_wp_db(self, args):
        """
        :param args db_name 数据库名
        :param args site_id 网站ID
        """
        db_name = public.xssencode2(args.db_name)
        try:
            site_id = int(args.site_id)
        except:
            return public.return_message(-1, 0, public.lang("Site ID must be numeric"))
        db_info = public.M("databases").where("name=?", (db_name,)).field('id').find()
        if 'id' not in db_info:
            return public.return_message(-1, 0, public.lang("This database was not found!"))
        pdata = {
            "d_id": db_info['id']
        }
        public.M('wordpress_onekey').where("s_id=?", (site_id,)).update(pdata)
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 获取WP Toolkit配置信息
    def get_wp_configurations(self, args: public.dict_obj):
        # 校验参数
        try:
            args.validate([
                Param('s_id').Require().Integer('>', 0),
            ], [
                public.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        from wp_toolkit import wpmgr

        wpmgr_obj = wpmgr(args.s_id)

        wp_local_version = wpmgr_obj.get_local_version()
        wp_latest_version = wpmgr_obj.get_latest_version(available=True).get('version', '')
        can_upgrade = wp_latest_version > wp_local_version

        wp_toolkit_config_data = wpmgr_obj.get_wp_toolkit_config_data()
        if isinstance(wp_toolkit_config_data, str):
            return public.fail_v2(wp_toolkit_config_data)

        return public.success_v2({
            'local_version': wp_local_version,
            'latest_version': wp_latest_version,
            'can_upgrade': can_upgrade,
            'language': wp_toolkit_config_data['locale'],
            'login_url': wp_toolkit_config_data['login_url'],
            'home_url': wp_toolkit_config_data['site_url'],
            'cache_enabled': self.get_cache_status(args.s_id),
            'admin_user': wp_toolkit_config_data['admin_info']['user_login'],
            'admin_email': wp_toolkit_config_data['admin_info']['user_email'],
            'whl_enabled': wp_toolkit_config_data['whl_config'].get('activated', False),
            'whl_page': wp_toolkit_config_data['whl_config'].get('whl_page', 'login'),
            'whl_redirect_admin': wp_toolkit_config_data['whl_config'].get('whl_redirect_admin', '404'),
        })

    # 保存WP Toolkit配置
    def save_wp_configurations(self, args: public.dict_obj):
        # 校验参数
        try:
            args.validate([
                Param('s_id').Require().Integer('>', 0),
                Param('language').String('in', list(self.get_language(args)['msg'].keys())),
                Param('admin_password').String('>=', 8),
                Param('admin_email').Email(),
                Param('whl_enabled').Integer('in', [0, 1]),
                Param('whl_page').SafePath(),
                Param('whl_redirect_admin').SafePath(),
            ], [
                public.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        from wp_toolkit import wpmgr

        wpmgr_obj = wpmgr(args.s_id)

        # 更新语言
        if 'language' in args:
            locale = wpmgr_obj.get_local_language()
            if args.language != locale:
                wpmgr_obj.update_language(args.language)

                # 写操作日志
                wpmgr.log_opt('Change language from [{}] to [{}] successfully', (locale, args.language))

        # 更新管理员密码
        if 'admin_password' in args:
            wpmgr_obj.set_admin_password(args.admin_password)

            # 写操作日志
            wpmgr.log_opt('Reset admin password successfully')

        # 更新管理员邮箱
        if 'admin_email' in args:
            wpmgr_obj.set_admin_email(args.admin_email)

            # 写操作日志
            wpmgr.log_opt('Reset admin email to [{}] successfully', (args.admin_email,))

        # 更新WPS-Hide-Login插件配置
        if 'whl_enabled' in args:
            # 停用插件
            if int(args.whl_enabled) == 0:
                wpmgr_obj.deactivate_plugins('wps-hide-login/wps-hide-login.php')

                # 写操作日志
                wpmgr.log_opt('Deactivate plugin [{}] successfully', ('WPS Hide Login',))

            # 启用插件
            else:
                wpmgr_obj.config_plugin_wps_hide_login(args.get('whl_page', 'login'),
                                                       args.get('whl_redirect_admin', '404'))

                # 写操作日志
                wpmgr.log_opt('Activate plugin [{}] successfully', ('WPS Hide Login',))

        return public.success_v2('修改成功')

    def AddWPSite(self, args: public.dict_obj):
        # 参数验证
        try:
            args.validate([
                Param('webname').String(),
                Param('type').String(),
                Param('ps').String(),
                Param('path').String(),
                Param('version').String(),
                Param('sql').String(),
                Param('datauser').String(),
                Param('datapassword').String(),
                Param('codeing').String(),
                Param('port').Integer(),
                Param('type_id').Integer(),
                Param('set_ssl').Integer(),
                Param('force_ssl').Integer(),
                Param('ftp').Bool(),
                Param('weblog_title').Require().Xss(),
                Param('language').Require(),
                Param('user_name').Require().Xss(),
                Param('email').Require().Email(),
                Param('pw_weak').Require().String('in', ['on', 'off']),
                Param('password').Require(),
                Param('prefix').Require().Xss(),
                Param('enable_cache').Require().Integer(),
                Param('enable_whl').Integer(),
                Param('whl_page').SafePath(),
                Param('whl_redirect_admin').SafePath(),
                Param('package_version').String(),
            ], [
                public.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        if args.pw_weak == "off":
            if public.check_password(args.password) == 0:
                return public.returnMsg(False, "密码非常弱，如果确认使用此密码，请勾选【允许弱密码】选项！")

        from copy import deepcopy
        args_dup = public.to_dict_obj(deepcopy(args.get_items()))

        from panelSite import panelSite
        data = panelSite().AddSite(args_dup)

        if data.get('status') is False:
            return data
        if int(data.get('databaseStatus', 0)) != 1:
            self.del_site(public.to_dict_obj({'s_id': data.get('siteId', 0)}))
            return public.returnMsg(False, "数据库创建失败，请检查mysql运行状态并重试")

        return self.deploy_wp(public.to_dict_obj({
            'domain': json.loads(args.webname).get('domain', ''),
            'weblog_title': args.weblog_title,
            'language': args.get('language', ''),
            'php_version': args.version,
            'user_name': args.user_name,
            'admin_password': args.password,
            'pw_weak': args.pw_weak,
            'admin_email': args.email,
            'prefix': args.prefix,
            'enable_cache': args.enable_cache,
            'd_id': data.get('d_id', 0),
            's_id': data.get('siteId', 0),
            'enable_whl': args.get('enable_whl', 0),
            'whl_page': args.get('whl_page', 'login'),
            'whl_redirect_admin': args.get('whl_redirect_admin', '404'),
            'package_version': args.get('package_version', None),
        }))

##############################对外接口-END##############################

class optimize_php:

    def optimize_php(self, get):
        get.version = get.php_version
        # 安装缓存插件
        # self.install_ext(get)
        # 根据主机性能调整参数
        return self.php_fpm(get)

    def install_ext(self, get):
        exts = ['opcache']
        import files
        mfile = files.files()
        for ext in exts:
            # print("开始安装php扩展 [{}]...".format(ext))

            if ext == 'pathinfo':
                import config
                con = config.config()
                get.version = get.php_version
                get.type = 'on'
                con.setPathInfo(get)
            else:
                get.name = ext
                get.version = get.php_version
                get.type = '1'
                mfile.InstallSoft(get)

    # 优化phpfpm
    def php_fpm(self, get):
        one_key_wp().write_logs("|-Start tuning PHP FPM parameters...")
        mem_total = int(get_mem())
        if mem_total <= 1024:
            get.max_children = '30'
            get.start_servers = '5'
            get.min_spare_servers = '5'
            get.max_spare_servers = '20'
        elif 1024 < mem_total <= 2048:
            get.max_children = '50'
            get.start_servers = '5'
            get.min_spare_servers = '5'
            get.max_spare_servers = '30'
        elif 2048 < mem_total <= 4098:
            get.max_children = '80'
            get.start_servers = '10'
            get.min_spare_servers = '10'
            get.max_spare_servers = '30'
        elif 4098 < mem_total <= 8096:
            get.max_children = '120'
            get.start_servers = '10'
            get.min_spare_servers = '10'
            get.max_spare_servers = '30'
        elif 8096 < mem_total <= 16192:
            get.max_children = '200'
            get.start_servers = '15'
            get.min_spare_servers = '15'
            get.max_spare_servers = '50'
        elif 16192 < mem_total <= 32384:
            get.max_children = '300'
            get.start_servers = '20'
            get.min_spare_servers = '20'
            get.max_spare_servers = '50'
        elif 32384 < mem_total:
            get.max_children = '500'
            get.start_servers = '20'
            get.min_spare_servers = '20'
            get.max_spare_servers = '50'
        # get.version = self.version
        import config
        current_conf = config.config().getFpmConfig(get)
        get.pm = current_conf['pm']
        get.listen = current_conf['unix']
        one_key_wp().write_logs("""
 ===================PHP FPM parameters=======================

     max_children: {}
     start_servers: {}
     min_spare_servers: {}
     max_spare_servers: {}
     Running mode: {}
     Connection: {}

 ===================PHP FPM parameters=======================


 """.format(get.max_children, get.start_servers, get.min_spare_servers, get.max_spare_servers, get.pm, get.listen))
        # self.backup_conf('/www/server/php/{}/etc/php-fpm.conf'.format(self.version))
        result = config.config().setFpmConfig(get)
        if not result['status']:
            one_key_wp().write_logs("|-PHP FPM Optimization failed: {}".format(result))
            return public.return_msg_gettext(False, "PHP FPM Optimization failed: {}", (result,))
        one_key_wp().write_logs("|-PHP FPM optimization succeeded")
        return public.return_msg_gettext(True, public.lang("PHP FPM optimization succeeded"))


class optimize_db:

    def self_db_cache(self, get):
        one_key_wp().write_logs("|-Start optimizing Mysql")
        mem_total = int(get_mem())
        if mem_total <= 2048:
            get.key_buffer_size = '128'
            get.tmp_table_size = '64'
            get.innodb_buffer_pool_size = '256'
            get.innodb_log_buffer_size = '16'
            get.sort_buffer_size = '768'
            get.read_buffer_size = '768'
            get.read_rnd_buffer_size = '512'
            get.join_buffer_size = '1024'
            get.thread_stack = '256'
            get.binlog_cache_size = '64'
            get.thread_cache_size = '64'
            get.table_open_cache = '128'
            get.max_connections = '100'
            get.max_heap_table_size = '64'
        elif 2048 < mem_total <= 4096:
            get.key_buffer_size = '256'
            get.tmp_table_size = '384'
            get.innodb_buffer_pool_size = '384'
            get.innodb_log_buffer_size = '16'
            get.sort_buffer_size = '768'
            get.read_buffer_size = '768'
            get.read_rnd_buffer_size = '512'
            get.join_buffer_size = '2048'
            get.thread_stack = '256'
            get.binlog_cache_size = '64'
            get.thread_cache_size = '96'
            get.table_open_cache = '192'
            get.max_connections = '200'
            get.max_heap_table_size = '384'
        elif 4096 < mem_total <= 8192:
            get.key_buffer_size = '384'
            get.tmp_table_size = '512'
            get.innodb_buffer_pool_size = '512'
            get.innodb_log_buffer_size = '16'
            get.sort_buffer_size = '1024'
            get.read_buffer_size = '1024'
            get.read_rnd_buffer_size = '768'
            get.join_buffer_size = '2048'
            get.thread_stack = '256'
            get.binlog_cache_size = '128'
            get.thread_cache_size = '128'
            get.table_open_cache = '384'
            get.max_connections = '300'
            get.max_heap_table_size = '512'
        elif 8192 < mem_total <= 16384:
            get.key_buffer_size = '512'
            get.tmp_table_size = '1024'
            get.innodb_buffer_pool_size = '1024'
            get.innodb_log_buffer_size = '16'
            get.sort_buffer_size = '2048'
            get.read_buffer_size = '2048'
            get.read_rnd_buffer_size = '1024'
            get.join_buffer_size = '4096'
            get.thread_stack = '384'
            get.binlog_cache_size = '192'
            get.thread_cache_size = '192'
            get.table_open_cache = '1024'
            get.max_connections = '400'
            get.max_heap_table_size = '1024'
        elif 16384 < mem_total <= 32768:
            get.key_buffer_size = '1024'
            get.tmp_table_size = '2048'
            get.innodb_buffer_pool_size = '4096'
            get.innodb_log_buffer_size = '16'
            get.sort_buffer_size = '4096'
            get.read_buffer_size = '4096'
            get.read_rnd_buffer_size = '2048'
            get.join_buffer_size = '8192'
            get.thread_stack = '512'
            get.binlog_cache_size = '256'
            get.thread_cache_size = '256'
            get.table_open_cache = '2048'
            get.max_connections = '500'
            get.max_heap_table_size = '2048'
        elif 32768 < mem_total:
            get.key_buffer_size = '2048'
            get.tmp_table_size = '4096'
            get.innodb_buffer_pool_size = '8192'
            get.innodb_log_buffer_size = '16'
            get.sort_buffer_size = '8192'
            get.read_buffer_size = '8192'
            get.read_rnd_buffer_size = '4096'
            get.join_buffer_size = '16384'
            get.thread_stack = '1024'
            get.binlog_cache_size = '512'
            get.thread_cache_size = '512'
            get.table_open_cache = '2048'
            get.max_connections = '1000'
            get.max_heap_table_size = '4096'
        one_key_wp().write_logs("""
 =====================Mysql parameters=======================

     key_buffer_size: {}
     tmp_table_size: {}
     innodb_buffer_pool_size: {}
     innodb_log_buffer_size: {}
     sort_buffer_size: {}
     read_buffer_size: {}
     read_rnd_buffer_size: {}
     join_buffer_size: {}
     thread_stack: {}
     binlog_cache_size: {}
     thread_cache_size: {}
     table_open_cache: {}
     max_connections: {}
     max_heap_table_size: {}

 =====================Mysql parameters=======================

 """.format(get.key_buffer_size, get.tmp_table_size, get.innodb_buffer_pool_size,
            get.innodb_log_buffer_size, get.sort_buffer_size, get.read_buffer_size, get.read_rnd_buffer_size,
            get.join_buffer_size, get.thread_stack, get.binlog_cache_size, get.thread_cache_size, get.table_open_cache,
            get.max_connections, get.max_heap_table_size))
        import database
        result = database.database().SetDbConf(get)
        if not result['status']:
            one_key_wp().write_logs("|-Mysql optimization failed {}".format(result))
            return public.return_msg_gettext(False, "Mysql optimization failed {}", (result,))
        public.ExecShell("/etc/init.d/mysqld restart")
        one_key_wp().write_logs("|-Mysql optimization succeeded")
        return public.return_msg_gettext(True, public.lang("Mysql optimization succeeded"))


# Nginx缓存加速WP站点
class fast_cgi:

    def get_fastcgi_conf(self, version):
        conf = r"""
set $skip_cache 0;

if ($request_method = POST) {
    set $skip_cache 1;
}  

if ($query_string != "") {
    set $skip_cache 1;
} 

if ($request_uri ~* "/wp-admin/|/xmlrpc.php|wp-.*.php|/feed/|index.php|sitemap(_index)?.xml") {
    set $skip_cache 1;
}

if ($http_cookie ~* "comment_author|wordpress_[a-f0-9]+|wp-postpass|wordpress_no_cache|wordpress_logged_in") {
    set $skip_cache 1;
}

location ~ (/[^/]+\.php)(/|$) {
    if ( !-f $document_root$1 ) {
        return 404;
    }

    # try_files $uri =404;
    fastcgi_pass unix:/tmp/php-cgi-%s.sock;
    fastcgi_index index.php;
    include fastcgi.conf;  
    add_header Strict-Transport-Security "max-age=63072000; includeSubdomains; preload";
    fastcgi_cache_bypass $skip_cache;
    fastcgi_no_cache $skip_cache;
    add_header X-Cache "$upstream_cache_status From $host";
    fastcgi_cache WORDPRESS;
    add_header Cache-Control  max-age=0;
    add_header Nginx-Cache "$upstream_cache_status";
    add_header Last-Modified $date_gmt;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    etag  on;
    fastcgi_cache_valid 200 301 302 1d;
}

location ~ /purge(/.*) {
    allow 127.0.0.1;
    deny all;
    fastcgi_cache_purge WORDPRESS "$scheme$request_method$host$1";
}
""" % version
        return conf

    def get_fast_cgi_status(self, sitename, php_v):
        if public.get_webserver() != "nginx":
            return False
        conf_path = "/www/server/panel/vhost/nginx/{}.conf".format(sitename)
        content = public.readFile(conf_path)
        if not content:
            return False
        fastcgi_conf = "include enable-php-{}-wpfastcgi.conf;".format(php_v)
        # return conf_path,fastcgi_conf
        if fastcgi_conf in content:
            return True
        return False

    def set_nginx_conf(self):
        if not os.path.exists("/dev/shm/nginx-cache/wp"):
            os.makedirs("/dev/shm/nginx-cache/wp")
            one_key_wp().set_permission("/dev/shm/nginx-cache")
        conf = """
 #AAPANEL_FASTCGI_CONF_BEGIN
 fastcgi_cache_key "$scheme$request_method$host$request_uri";
 fastcgi_cache_path /dev/shm/nginx-cache/wp levels=1:2 keys_zone=WORDPRESS:100m inactive=60m max_size=1g;
 fastcgi_cache_use_stale error timeout invalid_header http_500;
 fastcgi_ignore_headers Cache-Control Expires Set-Cookie;
 #AAPANEL_FASTCGI_CONF_END
 """
        conf_path = "/www/server/nginx/conf/nginx.conf"
        public.back_file(conf_path)
        content = public.readFile(conf_path)
        if not content:
            return
        if "#AAPANEL_FASTCGI_CONF_BEGIN" in content:
            one_key_wp().write_logs("|-Nginx FastCgi cache configuration already exists")
            print("Nginx FastCgi cache configuration already exists")
            return public.return_msg_gettext(True, public.lang("Nginx FastCgi 缓存配置已存在"))
        rep = "http\\s*\n\\s*{"
        content = re.sub(rep, "http\n\t{" + conf, content)
        public.writeFile(conf_path, content)

        # 如果配置出错恢复
        conf_pass = public.checkWebConfig()
        if conf_pass != True:
            public.restore_file(conf_path)
            one_key_wp().write_logs("|-Nginx FastCgi configuration error! {}".format(conf_pass))
            print("Nginx FastCgi configuration error! {}".format(conf_pass))
            return public.return_msg_gettext(False, public.lang("Nginx FastCgi 配置失败!"))
        one_key_wp().write_logs("|-Nginx FastCgi cache configuration complete...")
        print("Nginx FastCgi cache configuration complete")
        return public.return_msg_gettext(True, public.lang("Nginx FastCgi 缓存配置已完成"))

    def set_nginx_init(self):
        # if not os.path.exists("/dev/shm/nginx-cache/wp"):
        #     os.makedirs("/dev/shm/nginx-cache/wp")
        #     one_key_wp().set_permission("/dev/shm/nginx-cache")
        conf2 = """
     #AAPANEL_FASTCGI_CONF_BEGIN
     mkdir -p /dev/shm/nginx-cache/wp
     #AAPANEL_FASTCGI_CONF_END
 """
        init_path = "/etc/init.d/nginx"
        public.back_file(init_path)
        content_init = public.readFile(init_path)
        if not content_init:
            return
        if "#AAPANEL_FASTCGI_CONF_BEGIN" in content_init:
            one_key_wp().write_logs("|-Nginx init FastCgi cache configuration already exists")
            print("Nginx init FastCgi cache configuration already exists")
            return public.return_msg_gettext(True, public.lang("Nginx init FastCgi 缓存配置已存在"))
        # content_init = re.sub(r"\$NGINX_BIN -c \$CONFIGFILE", + conf2, content_init)
        rep2 = r"\$NGINX_BIN -c \$CONFIGFILE"
        content_init = re.sub(rep2, conf2 + "        $NGINX_BIN -c $CONFIGFILE", content_init)
        public.writeFile(init_path, content_init)

        # 如果配置出错恢复
        public.ExecShell("/etc/init.d/nginx restart")
        conf_pass = public.is_nginx_process_exists()
        if conf_pass == False:
            public.restore_file(init_path)
            one_key_wp().write_logs("|-Nginx init FastCgi configuration error! {}".format(conf_pass))
            print("Nginx init FastCgi configuration error! {}".format(conf_pass))
            return public.return_msg_gettext(False, public.lang("Nginx init FastCgi 配置失败!"))
        one_key_wp().write_logs("|-Nginx init FastCgi cache configuration complete...")
        print("Nginx init FastCgi cache configuration complete")
        return public.return_msg_gettext(True, public.lang("Nginx init FastCgi 缓存配置完成"))

    def set_fastcgi_php_conf(self, version):
        conf_path = "/www/server/nginx/conf/enable-php-{}-wpfastcgi.conf".format(version)
        if os.path.exists(conf_path):
            one_key_wp().write_logs("|-Nginx FastCgi PHP configuration already exists...")
            print("Nginx FastCgi PHP configuration already exists")
            return True
        public.writeFile(conf_path, self.get_fastcgi_conf(version))

    def set_website_conf(self, version, sitename, act=None):
        conf_path = "/www/server/panel/vhost/nginx/{}.conf".format(sitename)
        public.back_file(conf_path)
        conf = public.readFile(conf_path)
        if not conf:
            print("Website configuration file does not exist {}".format(conf_path))
            one_key_wp().write_logs("|-Website configuration file does not exist: {}".format(conf_path))
            return public.return_message(-1, 0, False)
        if act == 'disable':
            fastcgi_conf = "include enable-php-{}-wpfastcgi.conf;".format(version)
            if fastcgi_conf not in conf:
                print("FastCgi configuration does not exist in website configuration")
                one_key_wp().write_logs("|-FastCgi configuration does not exist in website configuration, skip")
                return public.return_message(-1, 0, public.lang("FastCgi不在网站配置中"))
            rep = r"include\s+enable-php-{}-wpfastcgi.conf;".format(version)
            conf = re.sub(rep, "include enable-php-{}.conf;".format(version), conf)
        else:
            fastcgi_conf = "include enable-php-{}-wpfastcgi.conf;".format(version)
            if fastcgi_conf in conf:
                one_key_wp().write_logs(
                    "|-The FastCgi configuration already exists in the website configuration, skip it")
                return public.return_message(0, 0, public.lang("FastCgi已在网站配置中存在，跳过"))
            rep = r"include\s+enable-php-{}.conf;".format(version)

            one_key_wp().write_logs("|-Current configuration: {}".format(conf))
            one_key_wp().write_logs("|-Regular expression: {}".format(rep))

            conf = re.sub(rep, fastcgi_conf, conf)

            one_key_wp().write_logs("|-Modified configuration: {}".format(conf))
        public.writeFile(conf_path, conf)
        conf_pass = public.checkWebConfig()
        if conf_pass != True:
            public.restore_file(conf_path)
            print("Website FastCgi configuration error {}".format(conf_pass))
            one_key_wp().write_logs("|-Website FastCgi configuration error: {}", (conf_pass,))
            return public.return_message(-1, 0, public.lang("FastCgi配置失败"))
        print("Website FastCgi configuration complete")
        one_key_wp().write_logs("|-Website FastCgi configuration complete...")
        return public.return_message(0, 0, public.lang("FastCgi配置成功"))

    def set_fastcgi(self, values):
        """
        get.version
        get.name
        """
        # 设置nginx启动文件
        self.set_nginx_init()
        # 设置nginx全局配置
        self.set_nginx_conf()
        # 设置fastcgi location
        self.set_fastcgi_php_conf(values['php_version'])
        # 设置网站配置文件
        self.set_website_conf(values['php_version'], values['site_name'])
        # 设置wp的变量用于nginxhelper插件清理缓存
        self.set_wp_nginx_helper(values['site_path'])
        # 设置userini允许访问 /dev/shm/nginx-cache/wp 目录
        self.set_userini(values['site_path'])

    def set_wp_nginx_helper(self, site_path):
        cache_conf = """
 #AAPANEL_FASTCGICACHE_BEGIN
 define('RT_WP_NGINX_HELPER_CACHE_PATH','/dev/shm/nginx-cache/wp');
 #AAPANEL_FASTCGICACHE_END
 """
        conf_file = "{}/wp-config.php".format(site_path)
        conf = public.readFile(conf_file)
        if not conf:
            print("Wordpress configuration file does not exist: {}".format(conf_file))
            one_key_wp().write_logs("|-Wordpress configuration file does not exist: {}".format(conf_file))
            return public.return_msg_gettext(False, "Wordpress配置文件不存在: {}", (conf_file,))
        if re.search(r'''define\(\s*'RT_WP_NGINX_HELPER_CACHE_PATH'\s*,''', conf):
            # if "RT_WP_NGINX_HELPER_CACHE_PATH" in conf:
            one_key_wp().write_logs("|-Cache cleaning configuration already exists, skip")
            print("Cache cleaning configuration already exists")
            return
        conf = conf.replace("<?php", "<?php" + cache_conf)
        public.writeFile(conf_file, conf)

    def set_userini(self, site_path):
        conf_file = "{}/.user.ini".format(site_path)
        conf = public.readFile(conf_file)
        if not conf:
            print("Anti-cross-site configuration file does not exist: {}".format(conf_file))
            one_key_wp().write_logs("|-Anti-cross-site configuration file does not exist: {}".format(conf_file))
            return public.return_msg_gettext(False, "防跨站配置文件不存在: {}",
                                             (conf_file,))
        if "/dev/shm/nginx-cache/wp" in conf:
            print("Anti-cross-site configuration is successful")
            one_key_wp().write_logs("|-Anti-cross-site configuration is successful...")
            return
        public.ExecShell('chattr -i {}'.format(conf_file))
        conf += ":/dev/shm/nginx-cache/wp"
        public.writeFile(conf_file, conf)
        public.ExecShell('chattr +i {}'.format(conf_file))
        one_key_wp().write_logs("|-Anti-cross-site configuration is successful...")

# one_key_wp请求帮助函数
def retry(func, max_retries=10):
    retry_count = 0

    while retry_count < max_retries:
        try:

            return func()  # 调用传入的函数并返回结果
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                public.print_log("Access failed {} times：{}".format(retry_count, e))
                time.sleep(2)  # 添加适当的延迟
            else:
                public.print_log("The maximum number of retries has been reached.")
                return False

    return None
