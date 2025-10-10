import os
import re
import json
import hashlib
import time
from typing import Tuple, Optional, Union, Dict, List
from urllib import parse
from itertools import product

import public
from .base import BaseProjectCommon


class _RealRedirect:
    setup_path = "/www/server/panel"
    _redirect_conf_file = "{}/data/redirect.conf".format(setup_path)

    _ng_domain_format = """
if ($host ~ '^%s'){
    return %s %s%s;
}
"""
    _ng_path_format = """
rewrite ^%s(.*) %s%s %s;
"""
    _ap_domain_format = """
<IfModule mod_rewrite.c>
    RewriteEngine on
    RewriteCond %%{HTTP_HOST} ^%s [NC]
    RewriteRule ^(.*) %s%s [L,R=%s]
</IfModule>    
"""
    _ap_path_format = """
<IfModule mod_rewrite.c>
    RewriteEngine on
    RewriteRule ^%s(.*) %s%s [L,R=%s]
</IfModule>
"""

    def __init__(self, config_prefix: str):
        self._config: Optional[List[Dict[str, Union[str, int]]]] = None
        self.config_prefix = config_prefix
        self._webserver = None

    @property
    def webserver(self) -> str:
        if self._webserver is not None:
            return self._webserver
        self._webserver = public.get_webserver()
        return self._webserver

    @property
    def config(self) -> List[Dict[str, Union[str, int, List]]]:
        if self._config is not None:
            return self._config
        try:
            self._config = json.loads(public.readFile(self._redirect_conf_file))
        except (json.JSONDecodeError, TypeError, ValueError):
            self._config = []
        if not isinstance(self._config, list):
            self._config = []
        return self._config

    def save_config(self):
        if self._config is not None:
            return public.writeFile(self._redirect_conf_file, json.dumps(self._config))

    def _check_redirect_domain_exist(self, site_name,
                                     redirect_domain: list,
                                     redirect_name: str = None,
                                     is_modify=False) -> Optional[List[str]]:
        res = set()
        redirect_domain_set = set(redirect_domain)
        for c in self.config:
            if c["sitename"] != site_name:
                continue
            if is_modify:
                if c["redirectname"] != redirect_name:
                    res |= set(c["redirectdomain"]) & redirect_domain_set
            else:
                res |= set(c["redirectdomain"]) & redirect_domain_set
        return list(res) if res else None

    def _check_redirect_path_exist(self, site_name,
                                   redirect_path: str,
                                   redirect_name: str = None) -> bool:
        for c in self.config:
            if c["sitename"] == site_name:
                if c["redirectname"] != redirect_name and c["redirectpath"] == redirect_path:
                    return True
        return False

    @staticmethod
    def _parse_url_domain(url: str):
        return parse.urlparse(url).netloc

    @staticmethod
    def _parse_url_path(url: str):
        return parse.urlparse(url).path

    # 计算name md5
    @staticmethod
    def _calc_redirect_name_md5(redirect_name) -> str:
        md5 = hashlib.md5()
        md5.update(redirect_name.encode('utf-8'))
        return md5.hexdigest()

    def _check_redirect(self, site_name, redirect_name, is_error=False):
        for i in self.config:
            if i["sitename"] != site_name:
                continue
            if is_error and "errorpage" in i and i["errorpage"] in [1, '1']:
                return i
            if i["redirectname"] == redirect_name:
                return i
        return None

    # 创建修改配置检测
    def _check_redirect_args(self, get, is_modify=False) -> Union[str, Dict]:
        if public.checkWebConfig() is not True:
            return '配置文件出错请先排查配置'

        try:
            site_name = get.sitename.strip()
            redirect_path = get.redirectpath.strip()
            redirect_type = get.redirecttype.strip()
            domain_or_path = get.domainorpath.strip()
            hold_path = int(get.holdpath)

            to_url = ""
            to_path = ""
            error_page = 0
            redirect_domain = []
            redirect_name = ""
            status_type = 1

            if "redirectname" in get and get.redirectname.strip():
                redirect_name = get.redirectname.strip()
            if "tourl" in get:
                to_url = get.tourl.strip()
            if "topath" in get:
                to_path = get.topath.strip()
            if "redirectdomain" in get:
                redirect_domain = json.loads(get.redirectdomain.strip())
            if "type" in get:
                status_type = int(get.type)
            if "errorpage" in get:
                error_page = int(get.errorpage)
        except (AttributeError, ValueError):
            return '参数错误'

        if not is_modify:
            if not redirect_name:
                return "参数错误，配置名称不能为空"
            # 检测名称是否重复
            if not (3 < len(redirect_name) < 15):
                return '名称必须大于3小于15个字符串'

            if self._check_redirect(site_name, redirect_name, error_page == 1):
                return '指定重定向名称已存在'

        site_info = public.M('sites').where("name=?", (site_name,)).find()
        if not isinstance(site_info, dict):
            return "站点信息查询错误"
        else:
            site_name = site_info["name"]

        # 检测目标URL格式
        rep = r"http(s)?\:\/\/([a-zA-Z0-9][-a-zA-Z0-9]{0,62}\.)+([a-zA-Z0-9][a-zA-Z0-9]{0,62})+.?"
        if to_url and not re.match(rep, to_url):
            return '目标URL格式不对【%s】' % to_url

        # 非404页面de重定向检测项
        if error_page != 1:
            # 检测是否选择域名
            if domain_or_path == "domain":
                if not redirect_domain:
                    return '请选择重定向域名'
                # 检测域名是否已经存在配置文件
                repeat_domain = self._check_redirect_domain_exist(site_name, redirect_domain, redirect_name, is_modify)
                if repeat_domain:
                    return '重定向域名重复 %s' % repeat_domain

                # 检查目标URL的域名和被重定向的域名是否一样
                tu = self._parse_url_domain(to_url)
                for d in redirect_domain:
                    if d == tu:
                        return '域名 "%s" 和目标域名一致请取消选择' % d
            else:
                if not redirect_path:
                    return '请输入重定向路径'
                if redirect_path[0] != "/":
                    return "路径格式不正确，格式为/xxx"
                # 检测路径是否有存在配置文件
                if self._check_redirect_path_exist(site_name, redirect_path, redirect_name):
                    return '重定向路径重复 %s' % redirect_path

                to_url_path = self._parse_url_path(to_url)
                if to_url_path.startswith(redirect_path):
                    return '目标URL[%s]以被重定向的路径[%s]开头，会导致循环匹配' % (to_url_path, redirect_path)
        # 404页面重定向检测项
        else:
            if not to_url and not to_path:
                return '首页或自定义页面必须二选一'
            if to_path:
                to_path = "/"

        return {
            "tourl": to_url,
            "topath": to_path,
            "errorpage": error_page,
            "redirectdomain": redirect_domain,
            "redirectname": redirect_name if redirect_name else str(int(time.time())),
            "type": status_type,
            "sitename": site_name,
            "redirectpath": redirect_path,
            "redirecttype": redirect_type,
            "domainorpath": domain_or_path,
            "holdpath": hold_path,
        }

    def create_redirect(self, get):
        res_conf = self._check_redirect_args(get, is_modify=False)
        if isinstance(res_conf, str):
            return public.returnMsg(False, res_conf)

        res = self._set_include(res_conf)
        if res is not None:
            return public.returnMsg(False, res)
        res = self._write_config(res_conf)
        if res is not None:
            return public.returnMsg(False, res)
        self.config.append(res_conf)
        self.save_config()
        public.serviceReload()
        return public.returnMsg(True, '创建成功')

    def _set_include(self, res_conf) -> Optional[str]:
        flag, msg = self._set_nginx_redirect_include(res_conf)
        if not flag:
            return msg
        flag, msg = self._set_apache_redirect_include(res_conf)
        if not flag:
            return msg

    def _write_config(self, res_conf) -> Optional[str]:
        if res_conf["errorpage"] != 1:
            res = self.write_nginx_redirect_file(res_conf)
            if res is not None:
                return res
            res = self.write_apache_redirect_file(res_conf)
            if res is not None:
                return res
        else:
            self.unset_nginx_404_conf(res_conf["sitename"])
            res = self.write_nginx_404_redirect_file(res_conf)
            if res is not None:
                return res
            res = self.write_apache_404_redirect_file(res_conf)
            if res is not None:
                return res

    def modify_redirect(self, get):
        """
        @name 修改、启用、禁用重定向
        @author hezhihong
        @param get.sitename 站点名称
        @param get.redirectname 重定向名称
        @param get.tourl 目标URL
        @param get.redirectdomain 重定向域名
        @param get.redirectpath 重定向路径
        @param get.redirecttype 重定向类型
        @param get.type 重定向状态 0禁用 1启用
        @param get.domainorpath 重定向类型 domain 域名重定向 path 路径重定向
        @param get.holdpath 保留路径 0不保留 1保留
        @return json
        """
        # 基本信息检查
        res_conf = self._check_redirect_args(get, is_modify=True)
        if isinstance(res_conf, str):
            return public.returnMsg(False, res_conf)

        old_idx = None
        for i, conf in enumerate(self.config):
            if conf["redirectname"] == res_conf["redirectname"] and conf["sitename"] == res_conf["sitename"]:
                old_idx = i

        res = self._set_include(res_conf)
        if res is not None:
            return public.returnMsg(False, res)
        res = self._write_config(res_conf)
        if res is not None:
            return public.returnMsg(False, res)

        if old_idx is not None:
            self.config[old_idx].update(res_conf)
        else:
            self.config.append(res_conf)
        self.save_config()
        public.serviceReload()
        return public.returnMsg(True, '修改成功')

    def _set_nginx_redirect_include(self, redirect_conf: dict) -> Tuple[bool, str]:
        ng_redirect_dir = "%s/vhost/nginx/redirect/%s" % (self.setup_path, redirect_conf["sitename"])
        ng_file = "{}/vhost/nginx/{}{}.conf".format(self.setup_path, self.config_prefix, redirect_conf["sitename"])
        if not os.path.exists(ng_redirect_dir):
            os.makedirs(ng_redirect_dir, 0o600)
        ng_conf = public.readFile(ng_file)
        if not isinstance(ng_conf, str):
            return False, "nginx配置文件读取失败"

        rep_include = re.compile(r"\sinclude +.*/redirect/.*\*\.conf;", re.M)
        if rep_include.search(ng_conf):
            return True, ""
        redirect_include = (
            "#SSL-END\n"
            "    #引用重定向规则，注释后配置的重定向代理将无效\n"
            "    include {}/*.conf;"
        ).format(ng_redirect_dir)

        if "#SSL-END" not in ng_conf:
            return False, "添加配置失败，无法定位SSL相关配置的位置"

        new_conf = ng_conf.replace("#SSL-END", redirect_include)
        public.writeFile(ng_file, new_conf)
        if self.webserver == "nginx" and public.checkWebConfig() is not True:
            public.writeFile(ng_file, ng_conf)
            return False, "添加配置失败"

        return True, ""

    def _un_set_nginx_redirect_include(self, redirect_conf: dict) -> Tuple[bool, str]:
        ng_file = "{}/vhost/nginx/{}{}.conf".format(self.setup_path, self.config_prefix, redirect_conf["sitename"])
        ng_conf = public.readFile(ng_file)
        if not isinstance(ng_conf, str):
            return False, "nginx配置文件读取失败"

        rep_include = re.compile(r"(#(.*)\n)?\s*include +.*/redirect/.*\*\.conf;")
        if not rep_include.search(ng_conf):
            return True, ""

        new_conf = rep_include.sub("", ng_conf, 1)
        public.writeFile(ng_file, new_conf)
        if self.webserver == "nginx" and public.checkWebConfig() is not True:
            public.writeFile(ng_file, ng_conf)
            return False, "移除配置失败"

        return True, ""

    def _set_apache_redirect_include(self, redirect_conf: dict) -> Tuple[bool, str]:
        ap_redirect_dir = "%s/vhost/apache/redirect/%s" % (self.setup_path, redirect_conf["sitename"])
        ap_file = "{}/vhost/apache/{}{}.conf".format(self.setup_path, self.config_prefix, redirect_conf["sitename"])
        if not os.path.exists(ap_redirect_dir):
            os.makedirs(ap_redirect_dir, 0o600)

        ap_conf = public.readFile(ap_file)
        if not isinstance(ap_conf, str):
            return False, "apache配置文件读取失败"

        rep_include = re.compile(r"\sIncludeOptional +.*/redirect/.*\*\.conf", re.M)
        # public.print_log(list(rep_include.finditer(ap_conf)))
        include_count = len(list(rep_include.finditer(ap_conf)))
        if ap_conf.count("</VirtualHost>") == include_count:
            return True, ""

        if include_count > 0:
            # 先清除已有的配置
            self._un_set_apache_redirect_include(redirect_conf)

        rep_custom_log = re.compile(r"CustomLog .*\n")
        rep_deny_files = re.compile(r"\n\s*#DENY FILES")

        include_conf = (
            "\n    # 引用重定向规则，注释后配置的重定向代理将无效\n"
            "    IncludeOptional {}/*.conf\n"
        ).format(ap_redirect_dir)

        new_conf = None

        def set_by_rep_idx(rep: re.Pattern, use_start: bool) -> bool:
            new_conf_list = []
            last_idx = 0
            for tmp in rep.finditer(ap_conf):
                new_conf_list.append(ap_conf[last_idx:tmp.start()])
                if use_start:
                    new_conf_list.append(include_conf)
                    new_conf_list.append(tmp.group())
                else:
                    new_conf_list.append(tmp.group())
                    new_conf_list.append(include_conf)
                last_idx = tmp.end()

            new_conf_list.append(ap_conf[last_idx:])

            nonlocal new_conf
            new_conf = "".join(new_conf_list)
            public.writeFile(ap_file, new_conf)
            if self.webserver == "apache" and public.checkWebConfig() is not True:
                public.writeFile(ap_file, ap_conf)
                return False
            return True

        if set_by_rep_idx(rep_custom_log, False) and rep_include.search(new_conf):
            return True, ""

        if set_by_rep_idx(rep_deny_files, True) and rep_include.search(new_conf):
            return True, ""
        return False, "设置失败"

    def _un_set_apache_redirect_include(self, redirect_conf: dict) -> Tuple[bool, str]:
        ap_file = "{}/vhost/apache/{}{}.conf".format(self.setup_path, self.config_prefix, redirect_conf["sitename"])
        ap_conf = public.readFile(ap_file)
        if not isinstance(ap_conf, str):
            return False, "apache配置文件读取失败"

        rep_include = re.compile(r"(#(.*)\n)?\s*IncludeOptional +.*/redirect/.*\*\.conf")
        if not rep_include.search(ap_conf):
            return True, ""

        new_conf = rep_include.sub("", ap_conf)
        public.writeFile(ap_file, new_conf)
        if self.webserver == "apache" and public.checkWebConfig() is not True:
            public.writeFile(ap_file, ap_conf)
            return False, "移除配置失败"

        return True, ""

    def write_nginx_redirect_file(self, redirect_conf: dict) -> Optional[str]:
        conf_file = "{}/vhost/nginx/redirect/{}/{}_{}.conf".format(
            self.setup_path, redirect_conf["sitename"], self._calc_redirect_name_md5(redirect_conf["redirectname"]),
            redirect_conf["sitename"]
        )
        if redirect_conf["type"] == 1:
            to_url = redirect_conf["tourl"]
            conf_list = ["#REWRITE-START"]
            if redirect_conf["domainorpath"] == "domain":
                hold_path = "$request_uri" if redirect_conf["holdpath"] == 1 else ""
                for sd in redirect_conf["redirectdomain"]:
                    if sd.startswith("*."):
                        sd = r"[\w.]+\." + sd[2:]

                    conf_list.append(self._ng_domain_format % (
                        sd, redirect_conf["redirecttype"], to_url, hold_path
                    ))
            else:
                redirect_path = redirect_conf["redirectpath"]
                if redirect_conf["redirecttype"] == "301":
                    redirect_type = "permanent"
                else:
                    redirect_type = "redirect"
                hold_path = "$1" if redirect_conf["holdpath"] == 1 else ""
                conf_list.append(self._ng_path_format % (redirect_path, to_url, hold_path, redirect_type))

            conf_list.append("#REWRITE-END")

            conf_data = "\n".join(conf_list)
            public.writeFile(conf_file, conf_data)

            if self.webserver == "nginx":
                isError = public.checkWebConfig()
                if isError is not True:
                    if os.path.exists(conf_file):
                        os.remove(conf_file)
                    return 'ERROR: 配置出错<br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>'
        else:
            if os.path.exists(conf_file):
                os.remove(conf_file)

    def write_apache_redirect_file(self, redirect_conf: dict) -> Optional[str]:
        conf_file = "{}/vhost/apache/redirect/{}/{}_{}.conf".format(
            self.setup_path, redirect_conf["sitename"], self._calc_redirect_name_md5(redirect_conf["redirectname"]),
            redirect_conf["sitename"]
        )
        if redirect_conf["type"] != 1:
            if os.path.exists(conf_file):
                os.remove(conf_file)
            return

        to_url = redirect_conf["tourl"]
        conf_list = ["#REWRITE-START"]
        hold_path = "$1" if redirect_conf["holdpath"] == 1 else ""
        if redirect_conf["domainorpath"] == "domain":
            for sd in redirect_conf["redirectdomain"]:
                if sd.startswith("*."):
                    sd = r"[\w.]+\." + sd[2:]

                conf_list.append(self._ap_domain_format % (
                    sd, to_url, hold_path, redirect_conf["redirecttype"]
                ))
        else:
            redirect_path = redirect_conf["redirectpath"]
            conf_list.append(self._ap_path_format % (redirect_path, to_url, hold_path, redirect_conf["redirecttype"]))

        conf_list.append("#REWRITE-END")

        public.writeFile(conf_file, "\n".join(conf_list))
        if self.webserver == "apache":
            isError = public.checkWebConfig()
            if isError is not True:
                if os.path.exists(conf_file):
                    os.remove(conf_file)
                return 'ERROR: 配置出错<br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>'

    def unset_nginx_404_conf(self, site_name):
        """
        清理已有的 404 页面 配置
        """
        need_clear_files = [
            "{}/vhost/nginx/{}{}.conf".format(self.setup_path, self.config_prefix, site_name),
            "{}/vhost/nginx/rewrite/{}{}.conf".format(self.setup_path, self.config_prefix, site_name),
        ]
        rep_error_page = re.compile(r'(?P<prefix>.*)error_page +404 +/404\.html[^\n]*\n', re.M)
        rep_location_404 = re.compile(r'(?P<prefix>.*)location += +/404\.html[^}]*}')
        clear_files = [
            {
                "data": public.readFile(i),
                "path": i,
            } for i in need_clear_files
        ]
        for file_info, rep in product(clear_files, (rep_error_page, rep_location_404)):
            if not isinstance(file_info["data"], str):
                continue
            tmp_res = rep.search(file_info["data"])
            if not tmp_res or tmp_res.group("prefix").find("#") != -1:
                continue
            file_info["data"] = rep.sub("", file_info["data"])

        for i in clear_files:
            if not isinstance(i["data"], str):
                continue
            public.writeFile(i["path"], i["data"])

    def write_nginx_404_redirect_file(self, redirect_conf: dict) -> Optional[str]:
        """
        设置nginx 404重定向
        """
        r_name_md5 = self._calc_redirect_name_md5(redirect_conf["redirectname"])
        file_path = "{}/vhost/nginx/redirect/{}".format(self.setup_path, redirect_conf["sitename"])
        file_name = '%s_%s.conf' % (r_name_md5, redirect_conf["sitename"])
        conf_file = os.path.join(file_path, file_name)
        if redirect_conf["type"] != 1:
            if os.path.exists(conf_file):
                os.remove(conf_file)
            return

        _path = redirect_conf["tourl"] if redirect_conf["tourl"] else redirect_conf["topath"]
        conf_data = (
            '#REWRITE-START\n'
            'error_page 404 = @notfound;\n'
            'location @notfound {{\n'
            '    return {} {};\n'
            '}}\n#REWRITE-END'
        ).format(redirect_conf["redirecttype"], _path)

        public.writeFile(conf_file, conf_data)
        if self.webserver == "nginx":
            isError = public.checkWebConfig()
            if isError is not True:
                if os.path.exists(conf_file):
                    os.remove(conf_file)
                return 'ERROR: 配置出错<br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>'

    def write_apache_404_redirect_file(self, redirect_conf: dict) -> Optional[str]:
        """
        设置apache 404重定向
        """
        r_name_md5 = self._calc_redirect_name_md5(redirect_conf["redirectname"])
        conf_file = "{}/vhost/apache/redirect/{}/{}_{}.conf".format(
            self.setup_path, redirect_conf["sitename"], r_name_md5, redirect_conf["sitename"]
        )
        if redirect_conf["type"] != 1:
            if os.path.exists(conf_file):
                os.remove(conf_file)
            return

        _path = redirect_conf["tourl"] if redirect_conf["tourl"] else redirect_conf["topath"]
        conf_data = """
#REWRITE-START
<IfModule mod_rewrite.c>
    RewriteEngine on
        RewriteCond %{{REQUEST_FILENAME}} !-f
        RewriteCond %{{REQUEST_FILENAME}} !-d
        RewriteRule . {} [L,R={}]
</IfModule>
#REWRITE-END
""".format(_path, redirect_conf["redirecttype"])

        public.writeFile(conf_file, conf_data)
        if self.webserver == "apache":
            isError = public.checkWebConfig()
            if isError is not True:
                if os.path.exists(conf_file):
                    os.remove(conf_file)
                return 'ERROR: 配置出错<br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>'

    def remove_redirect(self, get, multiple=None):
        try:
            site_name = get.sitename.strip()
            redirect_name = get.redirectname.strip()
        except AttributeError:
            return public.returnMsg(False, "参数错误")
        target_idx = None
        have_other_redirect = False
        target_conf = None
        for i, conf in enumerate(self.config):
            if conf["redirectname"] != redirect_name and conf["sitename"] == site_name:
                have_other_redirect = True
            if conf["redirectname"] == redirect_name and conf["sitename"] == site_name:
                target_idx = i
                target_conf = conf

        if target_idx is None:
            return public.returnMsg(False, '没有指定的配置')

        r_md5_name = self._calc_redirect_name_md5(target_conf["redirectname"])
        public.ExecShell("rm -f %s/vhost/nginx/redirect/%s/%s_%s.conf" % (
            self.setup_path, site_name, r_md5_name, site_name))

        public.ExecShell("rm -f %s/vhost/apache/redirect/%s/%s_%s.conf" % (
            self.setup_path, site_name, r_md5_name, site_name))

        if not have_other_redirect:
            self._un_set_apache_redirect_include(target_conf)
            self._un_set_nginx_redirect_include(target_conf)

        del self.config[target_idx]
        self.save_config()
        if not multiple:
            public.serviceReload()

        return public.returnMsg(True, '删除成功')

    def mutil_remove_redirect(self, get):
        try:
            redirect_names = json.loads(get.redirectnames.strip())
            site_name = json.loads(get.sitename.strip())
        except (AttributeError, json.JSONDecodeError, TypeError):
            return public.returnMsg(False, "参数错误")
        del_successfully = []
        del_failed = {}
        get_obj = public.dict_obj()
        for redirect_name in redirect_names:
            get_obj.redirectname = redirect_name
            get_obj.sitename = site_name
            try:
                result = self.remove_redirect(get, multiple=1)
                if not result['status']:
                    del_failed[redirect_name] = result['msg']
                    continue
                del_successfully.append(redirect_name)
            except:
                del_failed[redirect_name] = '删除时出错了，请再试一次'

        public.serviceReload()
        return {
            'status': True,
            'msg': '删除重定向 [ {} ] 成功'.format(','.join(del_successfully)),
            'error': del_failed,
            'success': del_successfully
        }

    def get_redirect_list(self, get):
        try:
            error_page = None
            site_name = get.sitename.strip()
            if "errorpage" in get:
                error_page = int(get.errorpage)
        except (AttributeError, ValueError, TypeError):
            return public.returnMsg(False, "参数错误")
        redirect_list = []
        webserver = public.get_webserver()
        if webserver == 'openlitespeed':
            webserver = 'apache'
        for conf in self.config:
            if conf["sitename"] != site_name:
                continue
            if error_page is not None and error_page != int(conf['errorpage']):
                continue
            if 'errorpage' in conf and conf['errorpage'] in [1, '1']:
                conf['redirectdomain'] = ['404页面']

            md5_name = self._calc_redirect_name_md5(conf['redirectname'])
            conf["redirect_conf_file"] = "%s/vhost/%s/redirect/%s/%s_%s.conf" % (
                self.setup_path, webserver, site_name, md5_name, site_name)
            conf["type"] = 1 if os.path.isfile(conf["redirect_conf_file"]) else 0
            redirect_list.append(conf)
        return redirect_list

    def remove_redirect_by_project_name(self, project_name):
        for i in range(len(self.config) - 1, -1, -1):
            if self.config[i]["sitename"] == project_name:
                del self.config[i]
        self.save_config()
        m_path = self.setup_path + '/vhost/nginx/redirect/' + project_name
        if os.path.exists(m_path):
            public.ExecShell("rm -rf %s" % m_path)
        m_path = self.setup_path + '/vhost/apache/redirect/' + project_name
        if os.path.exists(m_path):
            public.ExecShell("rm -rf %s" % m_path)


def test_api_warp(fn):
    def inner(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except:
            public.print_log(public.get_error_info())

    return inner


class Redirect(BaseProjectCommon):
    # 匹配目标URL的域名并返回

    def remove_redirect_by_project_name(self, project_name):
        if not isinstance(self.config_prefix, str):
            return None
        return _RealRedirect(self.config_prefix).remove_redirect_by_project_name(project_name)

    def create_project_redirect(self, get):
        if not isinstance(self.config_prefix, str):
            return public.returnMsg(False, "不支持的网站类型")
        return _RealRedirect(self.config_prefix).create_redirect(get)

    def modify_project_redirect(self, get):
        if not isinstance(self.config_prefix, str):
            return public.returnMsg(False, "不支持的网站类型")

        return _RealRedirect(self.config_prefix).modify_redirect(get)

    def remove_project_redirect(self, get):
        if not isinstance(self.config_prefix, str):
            return public.returnMsg(False, "不支持的网站类型")
        return _RealRedirect(self.config_prefix).remove_redirect(get)

    def mutil_remove_project_redirect(self, get):
        if not isinstance(self.config_prefix, str):
            return public.returnMsg(False, "不支持的网站类型")

        return _RealRedirect(self.config_prefix).mutil_remove_redirect(get)

    def get_project_redirect_list(self, get):
        if not isinstance(self.config_prefix, str):
            return public.returnMsg(False, "不支持的网站类型")
        return _RealRedirect(self.config_prefix).get_redirect_list(get)
