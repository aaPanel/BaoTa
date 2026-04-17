import copy
import json
import os.path
import sys
import time
import traceback
from typing import List, Tuple, Optional
from .bt_formater import _ConfileLink

_VHOST_PATH = "/www/server/panel/vhost"
_NGINX_PATH = "/www/server/nginx"

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
import public


class ConfigFileUtil:

    def __init__(self, tmp_config_path: str):
        site_data = []
        with open(os.path.join(tmp_config_path, "site_conf.json"), "r") as f:
            site_data = json.load(f)

        self.site_data = site_data
        self._tmp_path = tmp_config_path
        self.test_filter_file = []
        for site in site_data:
            for o_file in site["other_files"]:
                self.test_filter_file.append(o_file)
            self.test_filter_file.append(site["config_file"])

    def test_env(self) -> _ConfileLink:
        return _ConfileLink(
            (os.path.join(self._tmp_path, "conf"), _NGINX_PATH + "/conf"),
            (os.path.join(self._tmp_path, "vhost"), _VHOST_PATH),
            files_filter=self.test_filter_file
        )

    # 将除了网站之外的配置文件也应用上
    def use2panel(self):
        _ConfileLink(
            (os.path.join(self._tmp_path, "conf"), _NGINX_PATH + "/conf"),
            (os.path.join(self._tmp_path, "vhost"), _VHOST_PATH),
            files_filter=self.test_filter_file
        ).set_to()

    def unuse(self):
        _ConfileLink(
            (os.path.join(self._tmp_path, "conf"), _NGINX_PATH + "/conf"),
            (os.path.join(self._tmp_path, "vhost"), _VHOST_PATH),
            files_filter=self.test_filter_file
        ).reset_from()


class CreateSiteUtil:

    def __init__(self, tmp_config_path: str):
        self._proxy_main = None
        self.tmp_config_path = tmp_config_path

    def create_proxy_site(self, proxy_site: dict):
        site_id = 0
        site_nginx_config_file = "/www/server/panel/vhost/nginx/{}.conf".format(proxy_site["name"])

        def remove_site():
            if site_id:
                public.M("sites").where("id=?", [site_id]).delete()
                public.M("domain").where("pid=?", [site_id]).delete()

            try:
                for o_file in proxy_site["other_files"]:
                    _real_file = o_file.replace(os.path.join(self.tmp_config_path, "vhost"), _VHOST_PATH)
                    if os.path.exists(_real_file):
                        os.remove(_real_file)

                if os.path.exists(site_nginx_config_file):
                    os.remove(site_nginx_config_file)
            except:
                traceback.print_exc()

        try:
            init_proxy_conf = self._proxy_init_config()
            init_proxy_conf["subs_filter"] = False
            init_proxy_conf["site_name"] = proxy_site["name"]
            init_proxy_conf["domain_list"] = proxy_site["domains"]
            init_proxy_conf["site_port"] = [str(i) for i in proxy_site["ports"]]
            init_proxy_conf["site_path"] = proxy_site["site_path"]
            init_proxy_conf["proxy_log"]["log_conf"] = init_proxy_conf["proxy_log"]["log_conf"].format(
                log_path="/www/wwwlogs", site_name=proxy_site["name"]
            )
            init_proxy_conf["remark"] = ""
            init_proxy_conf["http_block"] = ""
            init_proxy_conf["proxy_info"] = []
            init_proxy_conf["proxy_cache"]["cache_zone"] = proxy_site["name"].replace(".", "_") + "_cache"
            if 80 in proxy_site["ports"]:
                init_proxy_conf["primary_port"] = "80"
            elif 443 in proxy_site["ports"]:
                init_proxy_conf["primary_port"] = "443"
            else:
                init_proxy_conf["primary_port"] = str(proxy_site["ports"][0])

            if 443 in proxy_site["ports"]:
                init_proxy_conf["https_port"] = "443"
                init_proxy_conf["ssl_info"]["ssl_status"] = True

            add_time = time.strftime('%Y-%m-%d %X', time.localtime())
            pdata = {
                'name': proxy_site["name"],
                'path': proxy_site["site_path"],
                'ps': "nginx配置解析并添加",
                'status': 1,
                'type_id': 0,
                'project_type': 'proxy',
                'project_config': json.dumps(init_proxy_conf),
                'addtime': add_time
            }

            site_id = public.M('sites').insert(pdata)
            if 443 in proxy_site["ports"]:
                proxy_site["ports"].remove(443)

            domain_len = max(len(proxy_site["domains"]), len(proxy_site["ports"]))
            proxy_site["domains"].extend([proxy_site["domains"][0]] * (domain_len - len(proxy_site["domains"])))
            proxy_site["ports"].extend([80] * (domain_len - len(proxy_site["ports"])))

            for i in range(domain_len):
                public.M('domain').insert({
                    'name': proxy_site["domains"][i], 'pid': str(site_id),
                    'port': str(proxy_site["ports"][i]), 'addtime': add_time
                })

            site_proxy_conf_path = "/www/server/proxy_project/sites/{n}/{n}.json".format(n=proxy_site["name"])
            if not os.path.exists(os.path.dirname(site_proxy_conf_path)):
                os.makedirs(os.path.dirname(site_proxy_conf_path), mode=0o755)
            public.writeFile(site_proxy_conf_path, json.dumps(init_proxy_conf))
            proxy_cache_dir = "/www/wwwroot/{}/proxy_cache_dir".format(proxy_site["name"])
            if not os.path.isdir(proxy_cache_dir):
                os.makedirs(proxy_cache_dir)

            config_data = public.readFile(proxy_site["config_file"])
            if "proxy_cache_path" not in config_data:
                proxy_cache = "proxy_cache_path {proxy_cache_dir} levels=1:2 keys_zone={cache_name}:20m inactive=1d max_size=5g;".format(
                    proxy_cache_dir=proxy_cache_dir, cache_name=init_proxy_conf["proxy_cache"]["cache_zone"])
                config_data = proxy_cache + "\n" + config_data

            public.writeFile(site_nginx_config_file, "")
            for file in proxy_site["other_files"]:
                real_file = file.replace(os.path.join(self.tmp_config_path, "vhost") , _VHOST_PATH)
                public.writeFile(real_file, public.readFile(file))

            proxy_main = self._get_proxy_main()
            res = proxy_main.save_nginx_config(public.to_dict_obj({
                "site_name": proxy_site["name"],
                "conf_data": config_data,
            }))
            if res["status"]:
                return None
            else:
                remove_site()
                return res["msg"]
        except Exception as e:
            traceback.print_exc()
            remove_site()
            return str(e)

    def _get_proxy_main(self):
        if self._proxy_main is not None:
            return self._proxy_main

        from mod.project.proxy.comMod import main as proxyMod
        self._proxy_main = proxyMod()
        return self._proxy_main

    def _proxy_init_config(self) -> dict:
        proxy_main = self._get_proxy_main()
        init_proxy_conf = getattr(proxy_main, "_init_proxy_conf")
        return copy.deepcopy(init_proxy_conf)

    def create_html_site(self, html_site: dict):
        site_id = 0
        site_nginx_config_file = "/www/server/panel/vhost/nginx/html_{}.conf".format(html_site["name"])
        ngx_open_basedir_path = _VHOST_PATH + '/open_basedir/nginx'
        if not os.path.exists(ngx_open_basedir_path):
            os.makedirs(ngx_open_basedir_path, 384)

        ngx_open_basedir_file = ngx_open_basedir_path + '/{}.conf'.format(html_site["name"])

        def remove_site():
            if site_id:
                public.M("sites").where("id=?", [site_id]).delete()
                public.M("domain").where("pid=?", [site_id]).delete()

            try:
                if os.path.exists(site_nginx_config_file):
                    os.remove(site_nginx_config_file)
                if os.path.exists(ngx_open_basedir_file):
                    os.remove(ngx_open_basedir_file)

                for o_file in html_site["other_files"]:
                    _real_file = o_file.replace(os.path.join(self.tmp_config_path, "vhost"), _VHOST_PATH)
                    if os.path.exists(_real_file):
                        os.remove(_real_file)
            except:
                traceback.print_exc()

        try:
            ngx_open_basedir_body = '''set $bt_safe_dir "open_basedir";\nset $bt_safe_open "{}/:/tmp/";'''.format(
                html_site["site_path"]
            )
            public.writeFile(ngx_open_basedir_file, ngx_open_basedir_body)
            user_ini_file = html_site["site_path"] + '/.user.ini'
            if not os.path.exists(user_ini_file):
                public.writeFile(user_ini_file, 'open_basedir=' + html_site["site_path"] + '/:/tmp/')
                public.ExecShell('chmod 644 ' + user_ini_file)
                public.ExecShell('chown root:root ' + user_ini_file)
                public.ExecShell('chattr +i ' + user_ini_file)

            add_time = time.strftime('%Y-%m-%d %X', time.localtime())
            pdata = {
                'name': html_site["name"],
                'path': html_site["site_path"],
                'ps': "nginx配置解析并添加",
                'status': 1,
                'type_id': 0,
                'project_type': 'html',
                'project_config': "{}",
                'addtime': add_time
            }
            site_id = public.M('sites').insert(pdata)

            if 443 in html_site["ports"]:
                html_site["ports"].remove(443)

            domain_len = max(len(html_site["domains"]), len(html_site["ports"]))
            html_site["ports"].extend([80] * (domain_len - len(html_site["ports"])))
            html_site["domains"].extend([html_site["domains"][0]] * (domain_len - len(html_site["domains"])))

            for i in range(domain_len):
                public.M('domain').insert({
                    'name': html_site["domains"][i], 'pid': str(site_id),
                    'port': str(html_site["ports"][i]), 'addtime': add_time
                })

            for file in html_site["other_files"]:
                real_file = file.replace(os.path.join(self.tmp_config_path, "vhost"), _VHOST_PATH)
                public.writeFile(real_file, public.readFile(file))

            config_data = public.readFile(html_site["config_file"])
            public.writeFile(site_nginx_config_file, "")
            ret = self.save_main_file(site_nginx_config_file, config_data)
            if ret:
                remove_site()
                return ret
            else:
                return None
        except Exception as e:
            traceback.print_exc()
            remove_site()
            return str(e)


    @staticmethod
    def save_main_file(path: str, data: str) -> Optional[str]:
        import files, public
        args = public.to_dict_obj({})
        args.data = data
        args.encoding = "utf-8"
        args.path = path

        f = files.files()
        save_result = f.SaveFileBody(args)
        if save_result["status"] is False:
            return save_result["msg"]
        return None


    def create_php_site(self, php_site: dict):
        site_id = 0
        site_nginx_config_file = "/www/server/panel/vhost/nginx/{}.conf".format(php_site["name"])
        ngx_open_basedir_path = _VHOST_PATH + '/open_basedir/nginx'
        if not os.path.exists(ngx_open_basedir_path):
            os.makedirs(ngx_open_basedir_path, 0o755)

        ngx_open_basedir_file = ngx_open_basedir_path + '/{}.conf'.format(php_site["name"])

        def remove_site():
            if site_id:
                public.M("sites").where("id=?", [site_id]).delete()
                public.M("domain").where("pid=?", [site_id]).delete()

            try:
                if os.path.exists(site_nginx_config_file):
                    os.remove(site_nginx_config_file)
                if os.path.exists(ngx_open_basedir_file):
                    os.remove(ngx_open_basedir_file)

                for o_file in php_site["other_files"]:
                    _real_file = o_file.replace(os.path.join(self.tmp_config_path, "vhost"), _VHOST_PATH)
                    if os.path.exists(_real_file):
                        os.remove(_real_file)
            except:
                traceback.print_exc()

        try:
            ngx_open_basedir_body = '''set $bt_safe_dir "open_basedir";\nset $bt_safe_open "{}/:/tmp/";'''.format(
                php_site["site_path"]
            )
            public.writeFile(ngx_open_basedir_file, ngx_open_basedir_body)
            user_ini_file = php_site["site_path"] + '/.user.ini'
            if not os.path.exists(user_ini_file):
                public.writeFile(user_ini_file, 'open_basedir=' + php_site["site_path"] + '/:/tmp/')
                public.ExecShell('chmod 644 ' + user_ini_file)
                public.ExecShell('chown root:root ' + user_ini_file)
                public.ExecShell('chattr +i ' + user_ini_file)

            add_time = time.strftime('%Y-%m-%d %X', time.localtime())
            pdata = {
                'name': php_site["name"],
                'path': php_site["site_path"],
                'ps': "nginx配置解析并添加",
                'status': 1,
                'type_id': 0,
                'project_type': 'PHP',
                'project_config': "{}",
                'addtime': add_time
            }
            site_id = public.M('sites').insert(pdata)

            if 443 in php_site["ports"]:
                php_site["ports"].remove(443)

            domain_len = max(len(php_site["domains"]), len(php_site["ports"]))
            php_site["ports"].extend([80] * (domain_len - len(php_site["ports"])))
            php_site["domains"].extend([php_site["domains"][0]] * (domain_len - len(php_site["domains"])))

            for i in range(domain_len):
                public.M('domain').insert({
                    'name': php_site["domains"][i], 'pid': str(site_id),
                    'port': str(php_site["ports"][i]), 'addtime': add_time
                })

            for file in php_site["other_files"]:
                real_file = file.replace(os.path.join(self.tmp_config_path, "vhost"), _VHOST_PATH)
                if not os.path.isdir(os.path.dirname(real_file)):
                    os.makedirs(os.path.dirname(real_file), 0o755)
                public.writeFile(real_file, public.readFile(file))

            config_data = public.readFile(php_site["config_file"])
            public.writeFile(site_nginx_config_file, "")
            ret = self.save_main_file(site_nginx_config_file, config_data)
            if ret:
                remove_site()
                return ret
            else:
                return None
        except Exception as e:
            traceback.print_exc()
            remove_site()
            return str(e)